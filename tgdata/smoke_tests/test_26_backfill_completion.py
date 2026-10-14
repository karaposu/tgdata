"""Completion/read-back: actual engine/SQLite/SDK, synthetic source, no network.

Process exits use actual SQLite commits; they do not simulate filesystem power loss.
Seeded controls test preservation only. Run as a module, like the other smoke suites.
"""
import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import telethon
from telethon import errors
from tgdata import SQLiteSyncStore, ReadBudgetExceeded, health
from tgdata.backfill import (
    BackfillPrepareContext, BackfillDeliveryRef, BackfillRunRef, BackfillStorageError,
    BackfillStateError, BackfillRecoveryRequired, BackfillUnknownCommand,
    BackfillUnknownReceipt, BackfillConflictError,
)
from tgdata.backfill_state import _BackfillState
from tgdata.history_window import _encode_date
from tgdata.smoke_tests import test_25_backfill_delivery as d

f = d.f
CHAT = d.CHAT


class AmbiguousStore:
    """One failed reply around a real CAS; read-back faults never fabricate success."""
    def __init__(self, actual, target=1, committed=True, nonbool=False, readback=None, hook=None):
        self.actual, self.target, self.committed = actual, target, committed
        self.nonbool, self.readback, self.hook = nonbool, readback, hook
        self.writes = self.readbacks = 0
        self.failed = False
        self.old = self.candidate = None
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def load(self, chat):
        if self.failed:
            self.failed = False
            self.readbacks += 1
            if self.readback == 'old': return self.old
            if self.readback == 'missing': return None
            if self.readback == 'outage': raise OSError(d.SECRET)
            if self.readback == 'corrupt': return '{bad'
            if self.readback == 'wrong_scope':
                value = json.loads(await self.actual.load(chat))
                value['collection_id'] = 'foreign'
                return json.dumps(value)
            if self.readback == 'noncanonical':
                return json.dumps(json.loads(await self.actual.load(chat)), indent=2)
            if self.readback == 'hold':
                self.entered.set(); await self.release.wait()
        return await self.actual.load(chat)

    async def compare_and_swap(self, chat, expected, candidate):
        self.writes += 1
        if self.writes != self.target:
            return await self.actual.compare_and_swap(chat, expected, candidate)
        self.old, self.candidate = expected, candidate
        if self.committed:
            assert await self.actual.compare_and_swap(chat, expected, candidate)
        if self.hook: await self.hook()
        self.failed = True
        if self.nonbool: return 'unconfirmed'
        raise OSError(d.SECRET)


async def operation(kind, **faults):
    if kind == 'create':
        actual = d.store(); req = d.request(); sender = None
        wrapped = AmbiguousStore(actual, **faults)
        return actual, wrapped, d.engine(wrapped).start(req, submission='new'), req, sender
    actual, eng, tg, _, sender, req, ctx = await d.setup(batch_size=2)
    sender.script = [d.finite_response([f.message(101)] if kind != 'empty' else [])]
    if kind == 'ack':
        pending = await eng.prepare(ctx)
        wrapped = AmbiguousStore(actual, **faults)
        return actual, wrapped, d.engine(wrapped).acknowledge(pending.delivery), pending, sender
    wrapped = AmbiguousStore(actual, target=2, **faults)
    return actual, wrapped, d.engine(wrapped, tg.get_message_batch).prepare(ctx), ctx, sender


async def test_pre_and_post_commit_reply_matrix():
    for kind in ('create', 'publish', 'empty', 'ack'):
        for committed in (False, True):
            for nonbool in (False, True):
                actual, fault, call, address, sender = await operation(
                    kind, committed=committed, nonbool=nonbool)
                if committed:
                    result = await call
                    status = result.status if hasattr(result, 'status') else result
                    assert status.terminal_outcome == ('completed' if kind in ('empty','ack') else None)
                    assert status.after_id == (101 if kind == 'ack' else 100)
                    if kind == 'create': assert result.applied
                    if kind == 'publish':
                        assert status.source_exhausted and result.batch.stop_reason == 'end'
                        assert status.pending_message_count == 1
                else:
                    error = await f.expect(BackfillStorageError, call)
                    assert d.SECRET not in str(error) and health.classify(error, True) is None
                    raw = await actual.load(CHAT)
                    if kind == 'create':
                        assert raw is None
                        await f.expect(BackfillUnknownCommand,d.engine(actual).start(address,submission='retry'))
                    else:
                        row = json.loads(raw)['current']
                        assert row['terminal_outcome'] is None and row['after_id'] == '100'
                        if kind == 'ack': assert row['pending'] is not None
                        else:
                            assert row['attempt'] is not None and row['pending'] is None
                            await f.expect(BackfillRecoveryRequired,d.engine(actual,d.forbidden_reader).prepare(address))
                assert fault.readbacks == 1 and fault.writes == fault.target
                if sender: assert len(sender.reads) == 1


async def test_exact_readback_has_no_second_clock_source_or_write():
    actual, _, tg, _, sender, _, ctx = await d.setup(batch_size=2)
    sender.script = [d.finite_response([f.message(101)])]
    fault = AmbiguousStore(actual, target=2)
    times = iter((d.NOW,d.NOW))
    turn = await d.engine(fault,tg.get_message_batch,lambda:next(times)).prepare(ctx)
    assert turn.status.pending_message_count == 1 and fault.writes == 2 and fault.readbacks == 1
    fault = AmbiguousStore(actual)
    times = iter((d.NOW,))
    status = await d.engine(fault,d.forbidden_reader,lambda:next(times)).acknowledge(turn.delivery)
    assert status.terminal_outcome == 'completed' and fault.writes == 1 and fault.readbacks == 1
    assert len(sender.reads) == 1


async def test_readback_noncanonical_text_must_validate_same_full_state():
    actual, fault, call, _, _ = await operation('create', readback='noncanonical')
    result = await call
    assert result.applied and fault.writes == fault.readbacks == 1
    assert result.status == (await d.engine(actual,now=d.forbidden_clock).status(result.status.run))


async def test_unreadable_absent_stale_or_foreign_readback_never_confirms():
    for kind in ('create', 'publish', 'empty', 'ack'):
        for readback in ('old','missing','outage','corrupt','wrong_scope'):
            actual, fault, call, address, sender = await operation(kind, readback=readback)
            error = await f.expect(BackfillStateError if readback in ('corrupt','wrong_scope')
                                   else BackfillStorageError,call)
            assert d.SECRET not in str(error) and error.__cause__ is None
            assert health.classify(error,True) is None and fault.readbacks == 1
            assert fault.writes == fault.target  # uncertainty never rewrites the candidate
            row = json.loads(await actual.load(CHAT))['current']
            assert row['attempt'] is None
            if kind in ('empty','ack'): assert row['terminal_outcome'] == 'completed'
            if sender: assert len(sender.reads) == 1


async def test_newer_control_snapshot_requires_inspection_not_stale_success():
    actual, _, tg, _, sender, _, ctx = await d.setup(batch_size=2)
    sender.script = [d.finite_response([f.message(101)])]
    fault = AmbiguousStore(actual, target=2, hook=lambda:d.control_fixture(actual,'pause'))
    await f.expect(BackfillStorageError,d.engine(fault,tg.get_message_batch).prepare(ctx))
    current = await d.engine(actual).status(ctx.run)
    assert current.operator_intent == 'paused' and current.pending_message_count == 1
    assert current.control_revision == 1 and fault.writes == 2
    await f.expect(BackfillConflictError,d.engine(actual,d.forbidden_reader).prepare(ctx))
    turn = await d.engine(actual,d.forbidden_reader,d.forbidden_clock).prepare(
        BackfillPrepareContext.from_status(current))
    assert turn.replayed and len(sender.reads) == 1
    assert (await d.engine(actual).acknowledge(turn.delivery)).terminal_outcome == 'completed'


async def test_ack_readback_moved_on_keeps_newer_pending_and_retained_receipt():
    (actual, eng, tg, _, sender, _, ctx), turn = await d.prepared()
    async def newer():
        status = await eng.status(ctx.run)
        await eng.prepare(BackfillPrepareContext.from_status(status))
    fault = AmbiguousStore(actual, hook=newer)
    await f.expect(BackfillStorageError,d.engine(fault).acknowledge(turn.delivery))
    before = await actual.load(CHAT)
    repeated = await d.engine(actual,d.forbidden_reader,d.forbidden_clock).acknowledge(turn.delivery)
    assert repeated.after_id == 102 and repeated.pending_next_after_id == 104
    assert await actual.load(CHAT) == before and fault.writes == 1 and len(sender.reads) == 2


async def test_admission_error_cannot_gain_permission_from_committed_marker():
    for nonbool in (False,True):
        actual, _, tg, _, sender, _, ctx = await d.setup()
        fault = AmbiguousStore(actual, nonbool=nonbool)
        await f.expect(BackfillStorageError,d.engine(fault,tg.get_message_batch).prepare(ctx))
        assert fault.readbacks == 0 and fault.writes == 1 and not sender.reads
        assert (await d.engine(actual).status(ctx.run)).attempt_id
        await f.expect(BackfillRecoveryRequired,d.engine(actual,d.forbidden_reader).prepare(ctx))


async def test_cancel_during_readback_is_not_success_or_rollback():
    for kind in ('create','publish','empty','ack'):
        actual, fault, call, _, sender = await operation(kind,readback='hold')
        task = asyncio.create_task(call)
        await asyncio.wait_for(fault.entered.wait(),5)
        task.cancel(); error = await f.expect(asyncio.CancelledError,task)
        assert error.__cause__ is None and health.classify(error,True) is None
        row = json.loads(await actual.load(CHAT))['current']
        assert row['attempt'] is None and fault.writes == fault.target
        if kind in ('empty','ack'): assert row['terminal_outcome'] == 'completed'
        if sender: assert len(sender.reads) == 1


async def test_prefix_commit_confirmation_preserves_original_rpc_exception():
    for unreadable in (False,True):
        actual, _, tg, _, sender, _, ctx = await d.setup(batch_size=101)
        original = errors.ChannelPrivateError(None)
        sender.script = [f.response([f.message(i) for i in range(200,100,-1)]),original]
        fault = AmbiguousStore(actual,target=2,readback='outage' if unreadable else None)
        caught = await f.expect(BackfillStorageError if unreadable else type(original),
                               d.engine(fault,tg.get_message_batch).prepare(ctx))
        if unreadable:
            assert caught.read_error is original and health.classify(caught,True) is None
        else: assert caught is original
        replay = await d.engine(actual,d.forbidden_reader,d.forbidden_clock).prepare(ctx)
        assert len(replay.batch.messages) == 100 and replay.batch.stop_reason == 'interrupted'
        assert replay.status.terminal_outcome is None and not replay.status.source_exhausted
        assert len(sender.reads) == 2 and fault.writes == 2 and fault.readbacks == 1


async def test_cancellation_in_prefix_readback_has_no_rpc_health():
    actual, _, tg, _, sender, _, ctx = await d.setup(batch_size=101)
    sender.script = [f.response([f.message(i) for i in range(200,100,-1)]),errors.ChannelPrivateError(None)]
    fault = AmbiguousStore(actual,target=2,readback='hold')
    task = asyncio.create_task(d.engine(fault,tg.get_message_batch).prepare(ctx))
    await asyncio.wait_for(fault.entered.wait(),5)
    task.cancel(); error = await f.expect(asyncio.CancelledError,task)
    assert health.classify(error,True) is None and error.__cause__ is None
    assert (await d.engine(actual).status(ctx.run)).pending_message_count == 100


async def test_completion_preserves_declared_origin_window_and_cursor():
    for origin,after in (('fresh',0),('imported',0),('imported',100)):
        for count in (0,1):
            actual, eng, _, _, sender, req, ctx = await d.setup(origin=origin,after_id=after)
            sender.script = [d.finite_response([f.message(after+1)] if count else [])]
            turn = await eng.prepare(ctx)
            assert turn.status.source_exhausted and turn.status.after_id == after
            if count:
                assert turn.status.terminal_outcome is None and turn.delivery
                status = await eng.acknowledge(turn.delivery)
            else:
                assert turn.batch is None and turn.delivery is None
                status = turn.status
            assert status.terminal_outcome == 'completed' and status.after_id == after+count
            assert status.origin == origin and status.initial_after_id == after
            assert (status.start_date,status.end_date) == (req.start_date,req.end_date)
            raw = await actual.load(CHAT)
            local = d.engine(SQLiteSyncStore(actual.path,create=False),d.forbidden_reader,d.forbidden_clock)
            assert (await local.prepare(BackfillPrepareContext.from_status(status))).status == status
            assert (await local.start(req,submission='retry')).status == status
            assert await actual.load(CHAT) == raw and len(sender.reads) == 1


async def test_full_batch_followup_budget_or_auth_failure_is_not_end():
    for fail in ('budget','auth'):
        budget = f.ledger(2)[0] if fail == 'budget' else None
        actual, eng, _, _, sender, _, ctx = await d.setup(budget=budget)
        turn = await eng.prepare(ctx); status = await eng.acknowledge(turn.delivery)
        assert turn.batch.stop_reason == 'limit' and status.after_id == 102
        if fail == 'auth': sender.script = [errors.AuthKeyUnregisteredError(None)]
        await f.expect(ReadBudgetExceeded if fail == 'budget' else errors.AuthKeyUnregisteredError,
                       eng.prepare(BackfillPrepareContext.from_status(status)))
        failed = await eng.status(ctx.run)
        assert failed.after_id == 102 and not failed.source_exhausted and failed.terminal_outcome is None
        assert failed.pending_batch_id is None and failed.attempt_id is None
        assert failed.last_failure_kind == ('budget' if fail == 'budget' else 'source')
        assert len(sender.reads) == (1 if fail == 'budget' else 2)


async def test_empty_end_preserves_pause_or_cancel_fixture():
    for action in ('pause','cancel'):
        actual, eng, _, _, sender, _, ctx = await d.setup()
        sender.script = [f.PENDING]
        task = asyncio.create_task(eng.prepare(ctx)); await d.until(lambda:bool(sender.pending))
        await d.control_fixture(actual,action)
        sender.pending[0].set_result(d.finite_response([]))
        turn = await task
        assert turn.status.source_exhausted and turn.batch is None
        assert turn.status.terminal_outcome == ('completed' if action == 'pause' else 'cancelled')
        assert turn.status.operator_intent == ('paused' if action == 'pause' else 'cancelled')


async def test_abandoned_final_fixture_never_accepts_or_completes():
    actual, eng, _, _, sender, _, ctx = await d.setup()
    sender.script = [d.finite_response([f.message(101)])]
    turn = await eng.prepare(ctx)
    raw = await actual.load(CHAT); value = json.loads(raw); row = value['current']
    value['state_revision'] = str(int(value['state_revision'])+1)
    row.update(operator_intent='abandoned',terminal_outcome='abandoned',control_revision='1',pending=None,
        abandoned=dict(batch_id=turn.delivery.batch_id,next_after_id='101',observed_at=_encode_date(d.NOW)),
        last_control=dict(command_id='fixture-abandon',action='abandon',expected_revision='0',
                          accepted_revision='1',state_revision=value['state_revision']))
    saved = _BackfillState(value).to_json(); assert await actual.compare_and_swap(CHAT,raw,saved)
    status = await eng.status(ctx.run)
    assert status.after_id == 100 and status.delivery_abandoned and status.source_exhausted
    await f.expect(BackfillUnknownReceipt,eng.acknowledge(turn.delivery))
    assert (await d.engine(actual,d.forbidden_reader,d.forbidden_clock).prepare(
        BackfillPrepareContext.from_status(status))).status.terminal_outcome == 'abandoned'
    assert await actual.load(CHAT) == saved and len(sender.reads) == 1


async def test_actual_final_sqlite_close_errors_confirm_immediately():
    for count in (0,1):
        actual, eng, _, _, sender, _, ctx = await d.setup()
        sender.script = [d.finite_response([f.message(101)] if count else [])]
        turn = await eng.prepare(ctx) if count else None
        original = sqlite3.connect
        class BadClose(sqlite3.Connection):
            def close(self):
                hit = False
                if self.total_changes:
                    hit = json.loads(self.execute('SELECT data FROM tgdata_sync_state').fetchone()[0])['current']['terminal_outcome']=='completed'
                super().close()
                if hit: raise sqlite3.OperationalError(d.SECRET)
        def connect(*a,**kw): kw['factory']=BadClose; return original(*a,**kw)
        with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
            if count: status = await eng.acknowledge(turn.delivery)
            else: status = (await eng.prepare(ctx)).status
        assert status.terminal_outcome == 'completed' and status.after_id == 100+count
        assert await d.engine(SQLiteSyncStore(actual.path,create=False)).status(ctx.run) == status


async def crash(path, phase, boundary, trace):
    actual = SQLiteSyncStore(path,create=False)
    async def reader(chat,**options):
        with open(trace,'a') as stream:
            stream.write('reader\n'); stream.flush(); os.fsync(stream.fileno())
        return d.sample(after=options['after_id'],count=0 if phase=='empty' else 1,stop='end')
    eng = d.engine(actual,reader)
    row = json.loads(await actual.load(CHAT))['current'] if phase!='create' else None
    original = sqlite3.connect
    class Crash(sqlite3.Connection):
        def commit(self):
            hit = False
            if self.total_changes:
                value = json.loads(self.execute('SELECT data FROM tgdata_sync_state').fetchone()[0])
                current = value['current']
                hit = (value['state_revision']=='1' if phase=='create' else
                       current['pending'] is not None if phase=='publish' else
                       current['terminal_outcome']=='completed' and (current['last_ack'] is not None)==(phase=='ack'))
            if hit and boundary=='before': os._exit(51)
            super().commit()
            if hit and boundary=='after': os._exit(52)
    def connect(*a,**kw): kw['factory']=Crash; return original(*a,**kw)
    with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
        if phase=='create': await eng.start(d.request(),submission='new')
        elif phase=='ack':
            await eng.acknowledge(BackfillDeliveryRef(BackfillRunRef.from_dict(row['ref']),
                row['request']['destination_id'],row['pending']['batch_id']))
        else:
            status = await eng.status(BackfillRunRef.from_dict(row['ref']))
            await eng.prepare(BackfillPrepareContext.from_status(status))
    raise AssertionError('commit crash boundary not reached')


async def test_subprocess_exit_at_all_final_commit_boundaries():
    for phase in ('create','publish','empty','ack'):
        for boundary in ('before','after'):
            actual = d.store(); eng = d.engine(actual); req = d.request()
            address = None
            if phase != 'create':
                status = (await eng.start(req,submission='new')).status
                address = BackfillPrepareContext.from_status(status)
            if phase == 'ack':
                async def reader(*a,**kw): return d.sample(stop='end')
                turn = await d.engine(actual,reader).prepare(address)
            trace = Path(actual.path).with_suffix('.trace')
            args = [sys.executable,__file__,'--crash',actual.path,phase,boundary,str(trace)]
            if hasattr(asyncio,'to_thread'):
                result = await asyncio.to_thread(subprocess.run,args,capture_output=True,text=True,timeout=25)
            else: result = subprocess.run(args,capture_output=True,text=True,timeout=25)
            assert result.returncode == (51 if boundary=='before' else 52),(phase,result.stderr)
            local = d.engine(SQLiteSyncStore(actual.path,create=False),d.forbidden_reader,d.forbidden_clock)
            if phase == 'create':
                if boundary == 'before':
                    assert await actual.load(CHAT) is None
                    await f.expect(BackfillUnknownCommand,local.start(req,submission='retry'))
                else: assert not (await local.start(req,submission='retry')).applied
            else:
                current = await local.status(address.run)
                if phase == 'ack':
                    assert current.after_id == (100 if boundary=='before' else 101)
                    if boundary=='after': assert await local.acknowledge(turn.delivery) == current
                    else: assert (await local.prepare(address)).batch.to_json() == turn.batch.to_json()
                elif boundary=='before':
                    assert current.attempt_id and current.pending_batch_id is None
                    await f.expect(BackfillRecoveryRequired,local.prepare(address))
                elif phase=='publish':
                    replay=await local.prepare(address)
                    assert replay.replayed and replay.batch.to_json()==d.sample(stop='end').to_json()
                    assert replay.status.source_exhausted
                if phase in ('empty','ack') and boundary=='after':
                    assert current.terminal_outcome=='completed' and current.pending_batch_id is None
                    assert (await local.prepare(BackfillPrepareContext.from_status(current))).status==current
                else: assert current.terminal_outcome is None
            assert (trace.read_text() if trace.exists() else '') == ('reader\n' if phase in ('publish','empty') else '')


async def main():
    tests=[v for k,v in globals().items() if k.startswith('test_') and asyncio.iscoroutinefunction(v)]
    print('Backfill Completion Tests — Telethon {}; LOCAL/INJECTED, actual SQLite/SDK'.format(telethon.__version__))
    assert telethon.__version__=='1.45.0'
    passed=0
    with tempfile.TemporaryDirectory(prefix='tgdata_backfill_completion_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        d.TMP=Path(tmp); f.TMP=d.TMP
        try:
            for test in tests:
                print('\nTEST:',test.__name__,flush=True)
                try: await asyncio.wait_for(test(),90)
                except Exception: traceback.print_exc(); print('✗ Failed')
                else: passed+=1; print('✓ Passed')
        finally:
            for client in f.CLIENTS: await client.disconnect()
            f.CLIENTS.clear()
    print('\nPassed: {}/{}'.format(passed,len(tests)))
    return 0 if passed==len(tests) else 1


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--crash':
        with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
             patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
            asyncio.run(crash(*sys.argv[2:]))
    else: sys.exit(asyncio.run(main()))
