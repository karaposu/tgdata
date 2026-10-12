"""Actual SQLite/SDK histories at every pool-owned provider boundary."""
import asyncio
from datetime import datetime, timezone
import json
from unittest.mock import patch
from tgdata import SyncStorageError, BackfillStorageError, BackfillPrepareContext
from tgdata.pool_lifecycle import _StoreBoundary
from tgdata.smoke_tests import test_31_account_pool as t

async def capture(work):
    try:
        return await work
    except BaseException as error:
        return error

class Fault:
    """Cancel a provider's own I/O, before/after actual delegate completion."""
    def __init__(self, actual):
        self.actual = actual
        self.armed = None
        self.counts = {}
        self.tasks = []
    def arm(self, method, number=1, after=False):
        self.counts = {}
        self.armed = method, number, after
    async def _call(self, method, args):
        self.tasks.append(asyncio.current_task())
        self.counts[method] = self.counts.get(method, 0) + 1
        hit = self.armed and (method, self.counts[method]) == self.armed[:2]
        if not hit or self.armed[2]:
            result = await getattr(self.actual, method)(*args)
        if hit:
            own = asyncio.get_running_loop().create_future()
            own.cancel()
            await own
        return result
    async def load(self, *args): return await self._call('load', args)
    async def compare_and_swap(self, *args): return await self._call('compare_and_swap', args)

async def setup(mode):
    daily = Fault(t.SQLiteSyncStore(t.path('daily-owned')))
    history = Fault(t.SQLiteSyncStore(t.path('history-owned')))
    state = Fault(t.SQLiteAccountPoolStore(t.path('pool-owned')))
    e = await t.setup(store=state, daily=daily, history=history)
    if mode == 'daily':
        await e.pool.initialize_sync(t.CHAT, after_id=100)
        context = None
    elif mode == 'backfill':
        started = await e.pool.start_backfill(t.d.request(batch_size=200), submission='new')
        context = BackfillPrepareContext.from_status(started.status)
    else:
        context = None
    return e, state, daily if mode == 'daily' else history, context

async def read(e, mode, context, limit):
    if mode == 'raw': return await t.read(e, limit=limit)
    if mode == 'daily': return await e.pool.sync_group(t.CHAT, limit=limit)
    return await e.pool.prepare_backfill(context)

def source(e, failed):
    if failed:
        error = t.errors.FloodWaitError(request=None, capture=7200)
        e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101, 201))]), error]
        return error, 100, 200
    e.senders[111].script = [t.d.finite_response([t.f.message(101)])]
    return None, 1, 1

async def pending(e, mode, context):
    if mode == 'daily': return (await e.pool.get_sync_status(t.CHAT)).pending_batch_id
    if mode == 'backfill': return (await e.pool.get_backfill_status(context.run)).pending_batch_id
    return None

async def pool_load_admission():
    observations = []
    for method in ('load', 'compare_and_swap'):
        for after in (False, True):
            e, state, _, _ = await setup('raw')
            state.arm(method, after=after)
            task = asyncio.create_task(t.read(e))
            result = await capture(task)
            assert isinstance(result, t.PoolStorageError) and task.cancelling() == 0
            row = json.loads(await state.actual.load())['accounts']['111']
            assert (row['active'] is not None) is (method == 'compare_and_swap' and after)
            assert not any(s.calls for s in e.senders.values()) and e.budget.status(111).used == 0
            assert all(p.done() for p in state.tasks)
            assert t.SECRET not in str(result) and t.health.classify(result) is None
            observations.append(dict(method=method, after=after, source_requests=0))
    return observations

async def pool_settlement():
    observations = []
    for mode in ('raw', 'daily', 'backfill'):
        for failed in (False, True):
            for after in (False, True):
                e, state, _, context = await setup(mode)
                original, size, charge = source(e, failed)
                state.arm('compare_and_swap', 2, after)
                task = asyncio.create_task(read(e, mode, context, 200 if failed else 1))
                result = await capture(task)
                assert isinstance(result, t.PoolStorageError) and task.cancelling() == 0
                assert len(result.partial_result.messages) == size
                assert result.partial_result.stop_reason == 'interrupted'
                if failed: assert result.read_error is original
                row = json.loads(await state.actual.load())['accounts']['111']
                assert (row['active'] is None) is after
                assert row['not_before'] == (t.f.NOW + 7200 if failed and after else 0)
                assert e.budget.status(111).used == charge and not e.senders[222].reads
                if mode != 'raw':
                    assert await pending(e, mode, context) == result.partial_result.batch_id
                observations.append(dict(mode=mode, source_failed=failed, committed=after, prefix=size))
    return observations

async def progress_load_start_admission():
    observations = []
    for mode in ('daily', 'backfill'):
        for after in (False, True):
            e, _, provider, context = await setup(mode)
            provider.arm('load', after=after)
            work = e.pool.get_sync_status(t.CHAT) if mode == 'daily' else e.pool.get_backfill_status(context.run)
            task = asyncio.create_task(work)
            result = await capture(task)
            assert isinstance(result, SyncStorageError if mode == 'daily' else BackfillStorageError)
            assert task.cancelling() == 0 and not any(s.calls for s in e.senders.values())
            observations.append(mode + ':load:' + str(after))
    for after in (False, True):
        e, _, provider, context = await setup('backfill')
        provider.arm('compare_and_swap', 1, after)
        result = await capture(e.pool.prepare_backfill(context))
        assert isinstance(result, BackfillStorageError)
        row = json.loads(await provider.actual.load(t.CHAT))['current']
        assert (row['attempt'] is not None) is after
        assert not any(s.calls for s in e.senders.values()) and e.budget.status(111).used == 0
        observations.append('backfill:admission:' + str(after))
    for mode in ('daily', 'backfill'):
        for after in (False, True):
            provider = Fault(t.SQLiteSyncStore(t.path('start')))
            e = await t.setup(daily=provider if mode == 'daily' else None,
                              history=provider if mode == 'backfill' else None)
            provider.arm('compare_and_swap', after=after)
            work = (e.pool.initialize_sync(t.CHAT, after_id=100) if mode == 'daily' else
                    e.pool.start_backfill(t.d.request(), submission='new'))
            result = await capture(work)
            confirmed = mode == 'backfill' and after
            assert (not isinstance(result, BaseException)) is confirmed
            if not confirmed:
                assert isinstance(result, SyncStorageError if mode == 'daily' else BackfillStorageError)
            assert (await provider.actual.load(t.CHAT) is not None) is after
            assert provider.counts['compare_and_swap'] == 1 and not any(s.calls for s in e.senders.values())
            observations.append(mode + ':start:' + str(after))
    return observations

async def progress_publication():
    observations = []
    for mode in ('daily', 'backfill'):
        for failed in (False, True):
            for after in (False, True):
                e, _, provider, context = await setup(mode)
                original, size, charge = source(e, failed)
                provider.arm('compare_and_swap', 1 if mode == 'daily' else 2, after)
                task = asyncio.create_task(read(e, mode, context, 200 if failed else 1))
                result = await capture(task)
                assert task.cancelling() == 0
                reconciled = mode == 'backfill' and after
                if reconciled:
                    if failed: assert result is original
                    else: assert len(result.batch.messages) == size
                else:
                    assert isinstance(result, SyncStorageError if mode == 'daily' else BackfillStorageError)
                    assert len(result.partial_result.messages) == size and result.partial_result.stop_reason == 'interrupted'
                    if failed: assert result.read_error is original
                    assert t.health.classify(result) is None
                assert bool(await pending(e, mode, context)) is after
                assert e.budget.status(111).used == charge and not e.senders[222].reads
                provider.armed = None
                if after:
                    await e.pool.close()
                    replay = await read(e, mode, context, 1)
                    batch = replay if mode == 'daily' else replay.batch
                    assert len(batch.messages) == size
                    if mode == 'daily': await e.pool.acknowledge_sync(t.CHAT, batch.batch_id)
                    else: await e.pool.acknowledge_backfill(replay.delivery)
                    assert await pending(e, mode, context) is None
                observations.append(dict(mode=mode, failed=failed, committed=after, records=size, reconciled=reconciled))
    return observations

async def progress_ack_control():
    observations = []
    for mode in ('daily', 'backfill'):
        for after in (False, True):
            e, _, provider, context = await setup(mode)
            source(e, False)
            prepared = await read(e, mode, context, 1)
            provider.arm('compare_and_swap', after=after)
            def ack():
                return (e.pool.acknowledge_sync(t.CHAT, prepared.batch_id) if mode == 'daily'
                        else e.pool.acknowledge_backfill(prepared.delivery))
            result = await capture(ack())
            confirmed = mode == 'backfill' and after
            assert (not isinstance(result, BaseException)) is confirmed
            assert bool(await pending(e, mode, context)) is (not after)
            provider.armed = None
            accepted = await ack()
            assert accepted.after_id == 101 and e.budget.status(111).used == 1
            observations.append(mode + ':ack:' + str(after))
    for after in (False, True):
        e, _, provider, context = await setup('backfill')
        provider.arm('compare_and_swap', after=after)
        args = dict(command_id='pause-known', expected_control_revision=context.expected_control_revision, action='pause')
        result = await capture(e.pool.control_backfill(context.run, **args))
        assert (not isinstance(result, BaseException)) is after
        status = await e.pool.get_backfill_status(context.run)
        assert (status.operator_intent == 'paused') is after
        provider.armed = None
        await e.pool.control_backfill(context.run, **args)
        assert not any(s.calls for s in e.senders.values())
        observations.append('backfill:control:' + str(after))
    return observations

async def pool_recovery():
    observations = []
    for after in (False, True):
        e, state, _, _ = await setup('raw')
        e.senders[111].script = [t.f.PENDING]
        reader = asyncio.create_task(t.read(e))
        await t.d.until(lambda: bool(e.senders[111].pending))
        reader.cancel(); assert isinstance(await capture(reader), asyncio.CancelledError)
        token = (await e.pool.get_pool_status()).accounts[0].attempt_id
        args = dict(attempt_id=token, previous_reader_stopped=True,
                    retry_not_before=datetime.fromtimestamp(t.f.NOW + 90, timezone.utc))
        state.arm('compare_and_swap', after=after)
        result = await capture(e.pool.recover_account(111, **args))
        assert isinstance(result, t.PoolStorageError)
        row = json.loads(await state.actual.load())['accounts']['111']
        assert (row['active'] is None) is after
        state.armed = None
        await e.pool.recover_account(111, **args)
        assert (await e.pool.get_pool_status()).accounts[0].retry_at == t.f.NOW + 90
        assert e.budget.status(111).used == 1
        observations.append(dict(committed=after, exact_retry=True))
    return observations

async def retained_provider_stop():
    observations = []
    for mode in ('raw', 'daily', 'backfill'):
        e, state, provider, context = await setup(mode)
        source(e, False)
        target = state if mode == 'raw' else provider
        number = 1 if mode != 'backfill' else 2
        original = target.compare_and_swap
        entered, finalizing, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
        calls, tasks = [0], []
        async def held(*args):
            calls[0] += 1
            if calls[0] != number: return await original(*args)
            tasks.append(asyncio.current_task()); entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                finalizing.set(); await release.wait()
                await original(*args)  # Real late commit after the caller's stop.
        target.compare_and_swap = held
        reader = asyncio.create_task(read(e, mode, context, 1))
        await entered.wait(); reader.cancel(); await finalizing.wait()
        try:
            for _ in range(3): reader.cancel(); await t.turns()
            assert not reader.done() and not tasks[0].done()
            if mode == 'raw':
                assert e.pool._active_task is reader
                assert isinstance(await capture(t.read(e)), t.PoolBusyError)
                assert not any(s.calls for s in e.senders.values())
            else:
                engine = e.pool.sync_engine if mode == 'daily' else e.pool._backfill_engines[context.run.collection_id]
                assert t.CHAT in engine._preparing
            release.set()
            result = await capture(reader)
            assert isinstance(result, asyncio.CancelledError) and tasks[0].done()
            if mode == 'raw':
                row = json.loads(await state.actual.load())['accounts']['111']
                assert row['active'] is not None and e.budget.status(111).used == 0
            else:
                assert len(result.partial_result.messages) == 1
                assert await pending(e, mode, context) is not None
                assert e.budget.status(111).used == 1
            observations.append(dict(mode=mode, caller_requests=reader.cancelling(), late_commit=True))
        finally:
            release.set(); await asyncio.gather(reader, return_exceptions=True)
    return observations

async def provider_control_refusal():
    observations = []
    for domain in ('pool', 'daily', 'backfill'):
        for operation in ('close', 'initialize', 'read', 'recheck', 'recover'):
            for via in ('direct', 'task', 'wait_for'):
                e, state, provider, context = await setup('daily' if domain == 'daily' else 'backfill')
                target = state if domain == 'pool' else provider
                actual_load, seen = target.load, []
                before = await state.actual.load()
                clients = [s._primary_client for s in e.pool._sources.values()]
                async def load(*args):
                    if not seen:
                        seen.append(True)
                        work = {'close': lambda:e.pool.close(), 'initialize':lambda:e.pool.initialize(),
                            'read':lambda:t.read(e), 'recheck':lambda:e.pool.recheck_account(111),
                            'recover':lambda:e.pool.recover_account(111, attempt_id='0'*32,
                                previous_reader_stopped=True, retry_not_before=datetime.fromtimestamp(t.f.NOW,timezone.utc))}[operation]()
                        if via == 'task': work = asyncio.create_task(work)
                        if via == 'wait_for': work = asyncio.wait_for(work, 1)
                        result = await capture(work)
                        assert isinstance(result, t.PoolBusyError), (domain, operation, via, result)
                        assert not e.pool._closed and e.pool._active_task is None
                    return await actual_load(*args)
                target.load = load
                if domain == 'pool': await e.pool.get_pool_status()
                elif domain == 'daily': await e.pool.get_sync_status(t.CHAT)
                else: await e.pool.get_backfill_status(context.run)
                assert seen and await state.actual.load() == before
                assert clients == [s._primary_client for s in e.pool._sources.values()]
                assert not any(s.calls for s in e.senders.values()) and e.budget.status(111).used == 0
                observations.append(domain+':'+operation+':'+via)
    return dict(refusals=observations)

async def prestart_and_sync_session():
    e, state, _, _ = await setup('raw')
    calls = dict(state.counts)
    task = asyncio.create_task(t.read(e)); task.cancel()
    assert isinstance(await capture(task), asyncio.CancelledError)
    assert state.counts == calls and not any(s.calls for s in e.senders.values())
    # Cancellation queued on an already-running caller must stop at the checkpoint.
    async def queued():
        asyncio.current_task().cancel()
        return await t.read(e)
    task = asyncio.create_task(queued())
    assert isinstance(await capture(task), asyncio.CancelledError)
    assert state.counts == calls and e.pool._active_task is None
    source = e.pool._sources[111]
    await source.retire()
    with patch.object(source.session_store, 'load', side_effect=asyncio.CancelledError(t.SECRET)):
        task = asyncio.create_task(t.read(e))
        result = await capture(task)
    assert isinstance(result, t.PoolConfigurationError) and task.cancelling() == 0
    assert t.SECRET not in str(result) and e.budget.status(111).used == 0
    assert not any(s.calls for s in e.senders.values())
    return dict(prestart_no_io=True, queued_stop_no_io=True, session_internal_cancel_local=True)

CASES = [('storage_pool_load_admission', pool_load_admission),
         ('storage_pool_settlement', pool_settlement),
         ('storage_progress_load_start_admission', progress_load_start_admission),
         ('storage_progress_publication', progress_publication),
         ('storage_progress_ack_control', progress_ack_control),
         ('storage_pool_recovery', pool_recovery),
         ('storage_retained_caller_stop', retained_provider_stop),
         ('storage_provider_controls', provider_control_refusal),
         ('storage_prestart_session', prestart_and_sync_session)]

async def backfill_recovery():
    observations = []
    for after in (False, True):
        e, state, provider, context = await setup('backfill')
        e.senders[111].script = [t.f.PENDING]
        reader = asyncio.create_task(e.pool.prepare_backfill(context))
        await t.d.until(lambda: bool(e.senders[111].pending))
        reader.cancel(); assert isinstance(await capture(reader), asyncio.CancelledError)
        saved = await e.pool.get_backfill_status(context.run)
        args = dict(attempt_id=saved.attempt_id, command_id='recover-exact',
                    expected_control_revision=saved.control_revision, previous_reader_stopped=True)
        before_pool = await state.actual.load()
        provider.arm('compare_and_swap', after=after)
        result = await capture(e.pool.recover_backfill(context.run, **args))
        assert (not isinstance(result, BaseException)) is after
        if not after: assert isinstance(result, BackfillStorageError)
        status = await e.pool.get_backfill_status(context.run)
        assert (status.attempt_id is None) is after
        provider.armed = None
        confirmed = await e.pool.recover_backfill(context.run, **args)
        assert confirmed.status.attempt_id is None and confirmed.status.after_id == 100
        assert await state.actual.load() == before_pool and e.budget.status(111).used == 200
        observations.append(dict(committed=after, exact_recovery=True, pool_attempt_unchanged=True))
    return observations

async def cancelled_completed_raw_settlement():
    observations = []
    for failed in (False, True):
        for after in (False, True):
            e, state, _, _ = await setup('raw')
            original_error, size, charge = source(e, failed)
            original = state.compare_and_swap
            entered, finalizing, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
            calls, tasks = [0], []
            async def held(*args):
                calls[0] += 1
                if calls[0] != 2: return await original(*args)
                tasks.append(asyncio.current_task()); entered.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    finalizing.set(); await release.wait()
                    if after: await original(*args)
            state.compare_and_swap = held
            task = asyncio.create_task(t.read(e, limit=200 if failed else 1))
            try:
                await entered.wait(); task.cancel(); await finalizing.wait()
                task.cancel(); await t.turns()
                assert not task.done() and e.pool._active_task is task and not tasks[0].done()
                release.set(); result = await capture(task)
                assert isinstance(result, asyncio.CancelledError) and len(result.partial_result.messages) == size
                assert result.partial_result.stop_reason == 'interrupted'
                if failed: assert result.read_error is original_error
                row = json.loads(await state.actual.load())['accounts']['111']
                assert (row['active'] is None) is after
                assert row['not_before'] == (t.f.NOW + 7200 if failed and after else 0)
                assert e.budget.status(111).used == charge and not e.senders[222].reads
                assert tasks[0].done() and e.pool._active_task is None
                observations.append(dict(source_failed=failed, committed=after, records=size))
            finally:
                release.set(); await asyncio.gather(task, return_exceptions=True)
    return observations

CASES += [('storage_backfill_recovery', backfill_recovery),
          ('storage_cancelled_completed_raw_settlement', cancelled_completed_raw_settlement)]
