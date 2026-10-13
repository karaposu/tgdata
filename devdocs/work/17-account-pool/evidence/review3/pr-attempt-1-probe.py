"""Fresh PR26 round3 falsifiers; real SDK/stores/ledger, no network or product edits."""
import asyncio
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from tgdata import PoolReadCapture, BackfillClockError, BackfillMediaError
from tgdata.smoke_tests import test_31_account_pool as t
from tgdata.smoke_tests import pool_storage_cases as s
from tgdata.smoke_tests import test_40_pool_outcomes as p


async def shield_waiter_stops_inner_read_survives():
    rows = []
    for mode in p.MODES:
        e, state, provider, ctx = await p.setup(mode)
        e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101, 201))]), t.f.PENDING]
        capture = PoolReadCapture()
        reader = asyncio.create_task(p.call(e, mode, ctx, capture, 200))
        async def wait():
            return await asyncio.shield(reader)
        outer = asyncio.create_task(wait())
        try:
            await p.until(lambda: bool(e.senders[111].pending), reader)
            first = capture.snapshot()
            assert first.state == 'running' and p.count(first) == 100
            outer.cancel()
            assert isinstance(await p.observed(outer), asyncio.CancelledError)
            assert reader.cancelling() == 0 and not reader.done() and capture.snapshot() == first
            e.senders[111].pending[0].set_result(t.d.finite_response([t.f.message(201)]))
            result = await reader
            final = capture.snapshot()
            assert final.state == 'succeeded' and p.count(final) == 101 and final.batch.stop_reason == 'end'
            assert final.account_id == 111 and final.error_type is final.read_error_type is None
            assert first.state == 'running' and p.count(first) == 100 and first.batch.stop_reason == 'interrupted'
            assert e.budget.status(111).used == 101 and not e.senders[222].calls
            if mode in ('daily', 'backfill'):
                assert await p.pending(e, mode, ctx) == final.batch.batch_id
            await e.pool.close()
            assert capture.snapshot() == final
            rows.append(dict(mode=mode,outer_cancelled=True,inner_cancel_requests=reader.cancelling(),
                             early_records=100,final_records=101,charge=101,final=final.state))
        finally:
            reader.cancel(); outer.cancel()
            await asyncio.gather(reader, outer, return_exceptions=True)
    return rows


async def publishing_group_and_other_source_close():
    rows = []
    for mode in ('daily', 'backfill'):
        for publication in ('success', 'failure', 'cancel_late_commit'):
            daily = s.Fault(t.SQLiteSyncStore(t.path('overlap-daily')))
            history = s.Fault(t.SQLiteSyncStore(t.path('overlap-history')))
            e = await t.setup(policy=t.PoolPolicy(strategy='spread'), daily=daily, history=history)
            if mode == 'daily':
                await e.pool.initialize_sync(t.CHAT, after_id=100)
                ctx, provider = None, daily
            else:
                started = await e.pool.start_backfill(t.d.request(batch_size=1), submission='new')
                ctx, provider = t.BackfillPrepareContext.from_status(started.status), history
            s.source(e, False)
            entered, release, finalizing = asyncio.Event(), asyncio.Event(), asyncio.Event()
            actual, calls, provider_tasks = provider.compare_and_swap, [0], []
            async def held(*args):
                calls[0] += 1
                if calls[0] != (1 if mode == 'daily' else 2):
                    return await actual(*args)
                provider_tasks.append(asyncio.current_task()); entered.set()
                try:
                    await release.wait()
                except asyncio.CancelledError:
                    finalizing.set(); await release.wait()
                    await actual(*args)
                    raise
                if publication == 'failure':
                    raise OSError(t.SECRET)
                return await actual(*args)
            provider.compare_and_swap = held
            cap_a, cap_b = PoolReadCapture(), PoolReadCapture()
            a = asyncio.create_task(p.call(e, mode, ctx, cap_a))
            b = None
            try:
                await entered.wait()
                before = cap_a.snapshot()
                assert before.state == 'running' and p.count(before) == 1 and before.account_id == 111
                assert e.pool._active_task is None
                e.senders[222].entity = t.room8()
                messages = [t.f.message(n) for n in reversed(range(501, 601))]
                for message in messages:
                    message.peer_id = t.types.PeerChannel(8)
                reply = t.f.response(messages); reply.chats = [t.room8()]
                e.senders[222].script = [reply, t.f.PENDING]
                b = asyncio.create_task(e.pool.read(t.OTHER, capture=cap_b, after_id=500, limit=200))
                await p.until(lambda: bool(e.senders[222].pending), b)
                b_before = cap_b.snapshot()
                assert p.count(b_before) == 100 and b_before.account_id == 222
                assert b_before.batch.chat_id == t.OTHER and cap_a.snapshot() == before
                await e.pool.close()
                assert isinstance(await p.observed(b), asyncio.CancelledError)
                assert cap_b.snapshot().state == 'cancelled' and p.count(cap_b) == 100
                assert not a.done() and cap_a.snapshot() == before
                assert all(source._primary_client is None for source in e.pool._sources.values())
                if publication == 'cancel_late_commit':
                    a.cancel(); await finalizing.wait(); a.cancel(); await t.turns()
                    assert not a.done() and not provider_tasks[0].done()
                release.set()
                result = await p.observed(a)
                expected = {'success':'succeeded','failure':'failed','cancel_late_commit':'cancelled'}[publication]
                assert cap_a.snapshot().state == expected and p.count(cap_a) == 1
                assert cap_a.snapshot().account_id == 111 and cap_a.snapshot().read_error_type is None
                assert cap_a.snapshot().batch.chat_id == t.CHAT and cap_a.snapshot().batch.messages[0]['id'] == '101'
                assert p.count(cap_b) == 100 and cap_b.snapshot().account_id == 222
                if publication == 'cancel_late_commit':
                    assert isinstance(result, asyncio.CancelledError) and a.cancelled()
                elif publication == 'failure':
                    assert isinstance(result, Exception) and not a.cancelled() and t.SECRET not in str(result)
                else:
                    assert not isinstance(result, BaseException)
                stored = await p.pending(e, mode, ctx)
                assert bool(stored) is (publication != 'failure')
                document = json.loads(await e.store.load())
                assert document['accounts']['111']['active'] is None
                assert document['accounts']['222']['active'] is not None
                assert e.budget.status(111).used == 1 and e.budget.status(222).used == 200
                assert all(task.done() for task in provider_tasks)
                counts = [len(sender.reads) for sender in e.senders.values()]
                if stored:
                    local = PoolReadCapture()
                    replay = await p.call(e, mode, ctx, local)
                    assert local.snapshot().account_id is None and local.snapshot().batch.batch_id == stored
                    local.snapshot().batch.save(t.path('receiver'))
                    accepted = (await e.pool.acknowledge_sync(t.CHAT, replay.batch_id) if mode == 'daily'
                                else await e.pool.acknowledge_backfill(replay.delivery))
                    assert accepted.after_id == 101
                assert counts == [len(sender.reads) for sender in e.senders.values()]
                rows.append(dict(mode=mode,publication=publication,first_records=1,first_owner=111,
                                 second_records=100,second_owner=222,close_preceded_publication=True,
                                 pending_committed=bool(stored),charges=[1,200],first_final=expected))
            finally:
                release.set(); a.cancel()
                if b is not None: b.cancel()
                await asyncio.gather(a, *([b] if b is not None else []), return_exceptions=True)
    return rows


async def app_moves_to_foreign_pool():
    rows = []
    for first_cancel in (False, True):
        e, _, _, _ = await p.setup('raw')
        foreign, _, _, _ = await p.setup('raw')
        first, second = PoolReadCapture(), PoolReadCapture()
        if first_cancel:
            e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101,201))]),t.f.PENDING]
        else:
            s.source(e, False)
        foreign.senders[111].script = [t.f.PENDING]
        stage = asyncio.Event()
        async def app():
            try:
                await p.call(e,'raw',None,first,200 if first_cancel else 1)
            except asyncio.CancelledError:
                assert first_cancel
            stage.set()
            return await p.call(foreign,'raw',None,second)
        task = asyncio.create_task(app())
        try:
            if first_cancel:
                await p.until(lambda:bool(e.senders[111].pending),task)
                old = e.pool._active_invocation
                task.cancel()
            await stage.wait()
            await p.until(lambda:bool(foreign.senders[111].pending),task)
            before = task.cancelling(); initial = first.snapshot()
            assert e.pool._active_invocation is None and foreign.pool._active_task is task
            if first_cancel:
                old.stop(e.pool._active_invocation)
                assert old.done.done() and old.caller is None
            await e.pool.close()
            assert not task.done() and task.cancelling() == before
            assert not foreign.pool._closed and all(src._primary_client is None for src in e.pool._sources.values())
            foreign.senders[111].pending[0].set_result(t.d.finite_response([t.f.message(101)]))
            await task
            assert first.snapshot() == initial and p.count(first) == (100 if first_cancel else 1)
            assert second.snapshot().state == 'succeeded' and p.count(second) == 1
            rows.append(dict(first_cancelled=first_cancel,caller_requests=before,foreign_read_survived=True,
                             first_records=p.count(first),second_records=1))
        finally:
            task.cancel(); await p.observed(task)
    return rows


async def source_data_survives_postsource_failure():
    rows = []
    for failure in ('clock', 'media'):
        if failure == 'clock':
            e, state, provider, ctx = await p.setup('backfill')
            s.source(e, False)
            engine = e.pool._backfill_engines[ctx.run.collection_id]
            clock, count = engine._clock, [0]
            def bad_clock():
                count[0] += 1
                if count[0] == 2: raise OSError(t.SECRET)
                return clock()
            engine._clock = bad_clock
            cap = PoolReadCapture()
            result = await p.observed(p.call(e,'backfill',ctx,cap))
            assert isinstance(result, BackfillClockError)
        else:
            state = s.Fault(t.SQLiteAccountPoolStore(t.path('media-state')))
            provider = s.Fault(t.SQLiteSyncStore(t.path('media-history')))
            e = await t.setup(store=state,history=provider)
            started = await e.pool.start_backfill(t.d.request(batch_size=1,media_mode='download'),submission='new')
            ctx = t.BackfillPrepareContext.from_status(started.status)
            e.senders[111].script = [t.d.finite_response([t.b.document(101)])]
            e.senders[111].files[t.b.ASSET_ID] = t.b.PAYLOAD
            entered, release = asyncio.Event(), asyncio.Event()
            actual, calls = state.compare_and_swap, [0]
            async def held(*args):
                calls[0] += 1
                if calls[0] == 2:
                    entered.set(); await release.wait()
                return await actual(*args)
            state.compare_and_swap = held
            cap, root = PoolReadCapture(), t.path('postsource-media')
            task = asyncio.create_task(p.call(e,'backfill',ctx,cap,download_media_to=root))
            try:
                await entered.wait()
                early = cap.snapshot()
                blob = early.batch.messages[0]['media']['blob']
                assert (root/blob['path']).read_bytes() == t.b.PAYLOAD
                (root/blob['path']).unlink()  # Independent local artifact loss, after actual download.
                release.set(); result = await p.observed(task)
                assert isinstance(result, BackfillMediaError)
            finally:
                release.set(); task.cancel(); await p.observed(task)
        snap = cap.snapshot()
        assert snap.state == 'failed' and p.count(snap) == 1 and snap.batch.stop_reason == 'interrupted'
        assert snap.account_id == 111 and snap.read_error_type is None
        assert snap.error_type == type(result).__name__ and t.SECRET not in repr(snap)
        row = json.loads(await state.actual.load())['accounts']['111']
        assert row['active'] is None and row['last_error'] is None
        status = await e.pool.get_backfill_status(ctx.run)
        assert status.attempt_id is not None and status.pending_batch_id is None and status.after_id == 100
        assert e.budget.status(111).used == 1 and not e.senders[222].reads
        assert not e.pool.drain_health_events()['events']
        await e.pool.close(); assert cap.snapshot() == snap
        rows.append(dict(failure=failure,error=type(result).__name__,retained=1,charge=1,
                         source_completed=True,group_attempt_unresolved=True,no_false_health=True))
    return rows


async def failover_second_admission_or_identity():
    rows = []
    for mode in p.MODES:
        for failure in ('admission_before','admission_after','identity'):
            e, state, provider, ctx = await p.setup(mode)
            e.senders[111].script = [t.errors.FloodWaitError(request=None,capture=7200)]
            if failure == 'identity':
                e.senders[222].identities = [999]
            else:
                state.arm('compare_and_swap',3,failure == 'admission_after')
            cap = PoolReadCapture()
            result = await p.observed(p.call(e,mode,ctx,cap))
            snap = cap.snapshot()
            assert snap.state == 'failed' and snap.batch is None and snap.account_id is None
            if failure == 'identity':
                assert isinstance(result,t.PoolIdentityError) and snap.read_error_type == 'PoolIdentityError'
            else:
                assert isinstance(result,t.PoolStorageError) and snap.read_error_type == 'FloodWaitError'
            assert snap.error_type == type(result).__name__
            rows_by_id = json.loads(await state.actual.load())['accounts']
            assert rows_by_id['111']['not_before'] == t.f.NOW + 7200
            assert (rows_by_id['222']['active'] is not None) is (failure == 'admission_after')
            assert not e.senders[222].reads and e.budget.status(222).used == 0
            assert await p.pending(e,mode,ctx) is None
            rows.append(dict(mode=mode,failure=failure,error=snap.error_type,
                             latest_actual_source_error=snap.read_error_type,retained=0,account=None,
                             second_source_reads=0,second_charge=0))
    return rows


CASES = [shield_waiter_stops_inner_read_survives,publishing_group_and_other_source_close,
         app_moves_to_foreign_pool,source_data_survives_postsource_failure,
         failover_second_admission_or_identity]


async def main(directory):
    t.f.TMP = t.d.TMP = directory
    results = []
    for function in CASES:
        print(json.dumps(dict(start=function.__name__)),flush=True)
        try:
            details = await asyncio.wait_for(function(),25)
        except BaseException as error:
            traceback.print_exc()
            results.append(dict(name=function.__name__,passed=False,error=type(error).__name__))
        else:
            results.append(dict(name=function.__name__,passed=True,details=details))
        finally:
            for pool in t.POOLS: await pool.close()
            t.POOLS.clear()
        print(json.dumps(results[-1]),flush=True)
    summary = dict(passed=sum(row['passed'] for row in results),total=len(results),
                   histories=sum(len(row.get('details',[])) for row in results))
    print(json.dumps(dict(summary=summary)),flush=True)
    return 0 if summary['passed'] == summary['total'] else 1


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='tgdata17-review3-') as directory, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        raise SystemExit(asyncio.run(main(Path(directory))))
