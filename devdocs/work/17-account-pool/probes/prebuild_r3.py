"""Full P0 candidate composition. Run via run_prebuild.py for an outer watchdog."""
import argparse
import asyncio
from contextlib import asynccontextmanager
import hashlib
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.source))
from tgdata.smoke_tests import test_31_account_pool as t
from tgdata import health
import prebuild_candidate as c

assert Path(t.__file__).resolve().is_relative_to(args.source.resolve())
RESULTS = []

async def capture(work):
    try:
        return await work
    except BaseException as error:
        return error

async def seed_report(e):
    async with e.pool._sources[111].monitor.call('prior', group=t.CHAT):
        await health.report(t.errors.ChannelPrivateError(request=None), 'handled')

async def source_call(e, mode, limit=200):
    if mode == 'raw':
        return t.read(e, limit=limit), None
    if mode == 'daily':
        await e.pool.initialize_sync(t.CHAT, after_id=100)
        return e.pool.sync_group(t.CHAT, limit=limit), None
    started = await e.pool.start_backfill(t.d.request(batch_size=limit), submission='new')
    context = t.BackfillPrepareContext.from_status(started.status)
    return e.pool.prepare_backfill(context), context

async def replay_after_close(e, mode, context, error):
    count = sum(len(s.reads) for s in e.senders.values())
    await e.pool.close()
    class NoPoolStore:
        async def load(self): raise AssertionError('replay accessed pool state')
        async def compare_and_swap(self, *a): raise AssertionError('replay wrote pool state')
    e.pool._store = NoPoolStore()
    for account in e.pool.accounts:
        Path(account.config_path).unlink()
    with patch.object(e.budget, 'status', side_effect=AssertionError('replay accessed source budget')):
        if mode == 'daily':
            batch = await e.pool.sync_group(t.CHAT, limit=200)
            assert batch.to_json() == error.partial_result.to_json()
            await e.pool.acknowledge_sync(t.CHAT, batch.batch_id)
            assert (await e.pool.get_sync_status(t.CHAT)).after_id == 200
        elif mode == 'backfill':
            status = await e.pool.get_backfill_status(context.run)
            replay = await e.pool.prepare_backfill(t.BackfillPrepareContext.from_status(status))
            assert replay.replayed and replay.batch.to_json() == error.partial_result.to_json()
            status = await e.pool.acknowledge_backfill(replay.delivery)
            assert status.after_id == 200
    assert sum(len(s.reads) for s in e.senders.values()) == count
    return mode != 'raw'

async def completed_prefix(mode, cancel_observer):
    trigger, holder = asyncio.Event(), {}
    async def controller():
        await trigger.wait()
        await holder['pool'].close()
    actor = asyncio.create_task(controller())  # Created before any operation context.
    e = await t.setup(daily=t.SQLiteSyncStore(t.path('daily')), history=t.SQLiteSyncStore(t.path('history')))
    holder['pool'] = e.pool
    error = t.errors.FloodWaitError(request=None, capture=7200)
    e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101, 201))]), error]
    work, context = await source_call(e, mode)
    result = await capture(work)
    assert result is error and len(error.partial_result.messages) == 100
    snapshot = e.pool.drain_health_events()
    assert snapshot['events'] and snapshot['dropped'] == 0
    assert snapshot['events'][-1]['account']['user_id'] == 111
    row = json.loads(await e.store.load())['accounts']['111']
    assert row['active'] is None and row['not_before'] == t.f.NOW + 7200
    assert e.budget.status(111).used == 200 and not e.senders[222].reads
    before = await e.store.load()
    if cancel_observer:
        async def observer():
            future = asyncio.get_running_loop().create_future()
            future.cancel()
            await future
        assert isinstance(await capture(observer()), asyncio.CancelledError)
        assert asyncio.current_task().cancelling() == 0
    trigger.set()
    await actor
    assert await e.store.load() == before and all(s._primary_client is None for s in e.pool._sources.values())
    replayed = await replay_after_close(e, mode, context, error)
    return dict(mode=mode, app_observer_cancel=cancel_observer, same_error=True,
                prefix=100, wait=7200, charge=200, external_actor_closed=True, replay_ack=replayed)

async def success_and_migration():
    e = await t.setup()
    for value in (lambda event: None, object()):
        try:
            c.CandidatePool(e.pool.accounts, tuple(e.pool.groups.values()), read_budget=e.budget,
                            state_store=e.store, health_callback=value)
        except t.PoolConfigurationError as error:
            assert 'drain_health_events' in str(error)
        else:
            raise AssertionError('application callback accepted')
    await seed_report(e)
    e.pool.drain_health_events()
    result = await t.read(e)
    reports = e.pool.drain_health_events()
    assert len(result.batch.messages) == 1 and reports['events'][-1]['source'] == 'recovery'
    assert reports['events'][-1]['account']['user_id'] == 111
    async def observer():
        future = asyncio.get_running_loop().create_future(); future.cancel(); await future
    assert isinstance(await capture(observer()), asyncio.CancelledError)
    assert (await e.pool.get_pool_status(t.CHAT)).accounts[0].attempt_id is None
    assert e.budget.status(111).used == 1
    await e.pool.close()
    return dict(batch=1, charge=1, caller_cancel_requests=0, recovery_report=True, callbacks_refused=2)

async def internal_cancel(mode):
    e = await t.setup(daily=t.SQLiteSyncStore(t.path('daily')), history=t.SQLiteSyncStore(t.path('history')))
    e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101, 201))]), t.f.PENDING]
    work, context = await source_call(e, mode)
    reader = asyncio.create_task(work)
    await t.d.until(lambda: bool(e.senders[111].pending))
    e.senders[111].pending[0].cancel()
    error = await capture(reader)
    assert isinstance(error, c._SourceInterrupted) and reader.cancelling() == 0 and not reader.cancelled()
    assert len(error.partial_result.messages) == 100 and health.classify(error) is None
    assert (await e.pool.get_pool_status(t.CHAT)).accounts[0].attempt_id is not None
    assert e.budget.status(111).used == 200 and not e.senders[222].reads
    if mode == 'daily': assert (await e.pool.get_sync_status(t.CHAT)).pending_batch_id == error.partial_result.batch_id
    if mode == 'backfill': assert (await e.pool.get_backfill_status(context.run)).pending_batch_id == error.partial_result.batch_id
    replayed = await replay_after_close(e, mode, context, error)
    return dict(mode=mode, caller_cancel_requests=0, local_interruption=True, unresolved=True,
                prefix=100, charge=200, replay_ack=replayed)

async def secondary_finalization():
    observations = []
    for source_error in (False, True):
        for finalizer in ('error', 'cancel', 'timeout'):
            e = await t.setup(policy=t.PoolPolicy(attempt_timeout=0.04))
            await seed_report(e); e.pool.drain_health_events()
            original = e.pool._sources[111].monitor._safely
            async def afterward(fn, *arguments):
                await original(fn, *arguments)  # Actual health observation first.
                if finalizer == 'timeout': await asyncio.Event().wait()
                if finalizer == 'cancel': raise asyncio.CancelledError('secondary-only')
                raise RuntimeError('secondary-only')
            e.pool._sources[111].monitor._safely = afterward
            error = t.errors.FloodWaitError(request=None, capture=7200)
            if source_error:
                e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101, 201))]), error]
            result = await capture(t.read(e, limit=200 if source_error else 1))
            if source_error:
                assert result is error and len(error.partial_result.messages) == 100
                assert (await e.pool.get_pool_status(t.CHAT)).accounts[0].retry_at == t.f.NOW + 7200
            else:
                assert len(result.batch.messages) == 1
            assert asyncio.current_task().cancelling() == 0
            assert e.pool._sources[111].task is None
            assert (await e.pool.get_pool_status(t.CHAT)).accounts[0].attempt_id is None
            observations.append(dict(source='error' if source_error else 'success', secondary=finalizer))
    return dict(combinations=observations, original_outcomes_retained=True)

async def passive_drain_during_close():
    e = await t.setup()
    await seed_report(e)
    e.senders[111].script = [t.f.PENDING]
    saved = {}
    async def reader():
        try:
            return await t.read(e)
        finally:
            saved['closing'] = e.pool._closing
            saved['reports'] = e.pool.drain_health_events()
    task = asyncio.create_task(reader())
    await t.d.until(lambda: bool(e.senders[111].pending))
    active = e.pool.drain_health_events()
    assert active['events'] and not task.done()
    await e.pool._sources[111].monitor._deliver(active['events'][0])  # New capture after active drain.
    await e.pool.close()
    assert isinstance(await capture(task), asyncio.CancelledError)
    assert saved['closing'] and saved['reports']['events']
    assert e.pool.drain_health_events() == {'events': [], 'dropped': 0}
    class NoStore:
        async def load(self): raise AssertionError('drain called backend')
        async def compare_and_swap(self, *a): raise AssertionError('drain called backend')
    e.pool._store = NoStore()
    assert e.pool.drain_health_events() == {'events': [], 'dropped': 0}
    assert all(s._primary_client is None for s in e.pool._sources.values())
    return dict(active_access=True, closing_finally_preserves_cancel=True, closed_backend_free=True)

async def provider_reentry():
    observations = []
    for phase in ('load_read', 'load_status', 'cas_admit', 'cas_settle'):
        for mode in ('direct', 'task', 'wait_for'):
            e = await t.setup()
            actual = e.store
            seen, calls = [], [0]
            async def trigger():
                before = (e.pool._closed, e.pool._closing)
                close = e.pool.close()
                work = close if mode == 'direct' else asyncio.create_task(close) if mode == 'task' else asyncio.wait_for(close, 1)
                error = await capture(work)
                assert isinstance(error, t.PoolBusyError)
                assert (e.pool._closed, e.pool._closing) == before == (False, False)
                seen.append(True)
            class Backend:
                async def load(self):
                    if phase.startswith('load') and not seen: await trigger()
                    return await actual.load()
                async def compare_and_swap(self, *arguments):
                    calls[0] += 1
                    if calls[0] == (1 if phase == 'cas_admit' else 2) and phase.startswith('cas'):
                        await trigger()
                    return await actual.compare_and_swap(*arguments)
            e.pool._store = Backend()
            if phase == 'load_status':
                await e.pool.get_pool_status()
                assert not any(s.calls for s in e.senders.values())
            else:
                assert (await t.read(e)).account_id == 111
            assert seen == [True] and not e.pool._closed
            observations.append(phase + ':' + mode)
    return dict(refusals=observations, flags_unchanged=True, actual_sqlite_forwarded=True)

async def scope_positive_controls():
    e, foreign = await t.setup(), await t.setup()
    actual, trigger, state = e.store, asyncio.Event(), {}
    class Backend:
        async def load(self):
            if 'actor' not in state:
                state['scopes'] = tuple(c._SCOPES.get())
                await foreign.pool.close()
                async def later():
                    await trigger.wait()
                    await e.pool.close()
                state['actor'] = asyncio.create_task(later())
            return await actual.load()
        async def compare_and_swap(self, *arguments): return await actual.compare_and_swap(*arguments)
    e.pool._store = Backend()
    assert (await t.read(e)).account_id == 111 and foreign.pool._closed and not e.pool._closed
    assert all(not item['active'] and item['pool'] is None for item in state['scopes'])
    trigger.set(); await state['actor']
    assert e.pool._closed and all(s._primary_client is None for s in e.pool._sources.values())
    return dict(foreign_allowed=True, expired_allowed=True, scope_references_released=True)

async def observation_bounds():
    e = await t.setup()
    await seed_report(e)
    event = e.pool.drain_health_events()['events'][0]
    producer = json.loads(json.dumps(event))
    e.pool._observations.capture(producer)
    old_label = producer['account']['label']
    producer['account']['label'] = 'changed by producer'
    owned = e.pool.drain_health_events()
    assert owned['events'][0]['account']['label'] == old_label
    owned['events'][0]['account']['label'] = 'changed by receiver'
    e.pool._observations.capture(event)
    assert e.pool.drain_health_events()['events'][0]['account']['label'] == old_label
    buffer = e.pool._observations
    for _ in range(c.MAX_EVENTS + 2): buffer.capture(event)
    snapshot = buffer.drain()
    assert len(snapshot['events']) == c.MAX_EVENTS and snapshot['dropped'] == 2
    large = dict(event, error='e' * 2500)
    for _ in range(c.MAX_EVENTS): buffer.capture(large)
    assert buffer.byte_count <= c.MAX_TOTAL_BYTES
    snapshot = buffer.drain()
    assert 0 < len(snapshot['events']) < c.MAX_EVENTS and snapshot['dropped'] > 0
    byte_retained = len(snapshot['events'])
    touched = []
    class NotPlain:
        def __str__(self): touched.append(True); raise AssertionError('arbitrary conversion')
    malformed = [dict(event, error='x' * (c.MAX_EVENT_BYTES + 1)),
                 dict(event, error='😀' * 1000), dict(event, group=True),
                 dict(event, group=NotPlain()), dict(event, unexpected='not allowed')]
    for value in malformed: buffer.capture(value)
    snapshot = buffer.drain()
    assert not snapshot['events'] and snapshot['dropped'] == len(malformed) and not touched
    buffer.dropped = c.MAX_DROPPED; buffer.lose(); assert buffer.dropped == c.MAX_DROPPED
    buffer.drain()
    token = health._DELIVERING.set(True)
    try:
        e.senders[111].script = [t.errors.ChannelPrivateError(request=None)]
        assert (await t.read(e)).account_id == 222
    finally:
        health._DELIVERING.reset(token)
    assert e.pool.drain_health_events()['events']  # Internal capture ignores ambient callback guard.
    assert not any(s.monitor._tasks for s in e.pool._sources.values())
    legacy_events = []
    legacy = health.HealthMonitor(legacy_events.append, 'legacy', lambda: ('legacy', 999))
    async with legacy.call('legacy', group=t.CHAT):
        await health.report(t.errors.ChannelPrivateError(request=None), 'handled')
    assert legacy_events and legacy_events[0]['account']['user_id'] == 999
    return dict(count_cap=c.MAX_EVENTS, byte_cap=c.MAX_TOTAL_BYTES, byte_limited_events=byte_retained,
                malformed_dropped=len(malformed), nested_values_owned=True,
                ambient_capture=True, legacy_callback_preserved=True, observer_tasks=0)

async def failed_capture_preserves_facts():
    for failure in (RuntimeError('private-capture-detail'), asyncio.CancelledError('secondary-cancel')):
        e = await t.setup()
        error = t.errors.FloodWaitError(request=None, capture=7200)
        e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101, 201))]), error]
        with patch.object(e.pool._observations, 'own', side_effect=failure):
            assert await capture(t.read(e, limit=200)) is error
        assert len(error.partial_result.messages) == 100
        assert (await e.pool.get_pool_status(t.CHAT)).accounts[0].retry_at == t.f.NOW + 7200
        assert e.budget.status(111).used == 200 and not e.senders[222].reads
        assert e.pool.drain_health_events() == {'events': [], 'dropped': 1}
        assert asyncio.current_task().cancelling() == 0
    return dict(capture_fault_types=2, original_prefix=100, wait=7200, charge=200)

async def native_failed_retirement():
    combinations = []
    for internal in ('error', 'cancel'):
        for caller_cancel in (False, True):
            e = await t.setup()
            source, old = e.pool._sources[111], e.pool._sources[111]._primary_client
            before = await e.store.load()
            failure = OSError(t.SECRET) if internal == 'error' else asyncio.CancelledError(t.SECRET)
            gate = t.CleanupGate(e.senders[111], failure)
            task = asyncio.create_task(e.pool.recheck_account(111))
            try:
                await gate.entered.wait()
                if caller_cancel:
                    task.cancel(); await t.turns(); assert not task.done()
                gate.release.set()
                error = await capture(task)
                assert isinstance(error, asyncio.CancelledError if caller_cancel else t.PoolStateError)
                assert t.SECRET not in str(error) and source._retirement_blocked
                assert source._primary_client is old and all(work.done() for work in gate.tasks)
                assert isinstance(await capture(t.read(e)), t.PoolStateError)
                assert await e.store.load() == before
                assert not any(s.calls for s in e.senders.values()) and e.budget.status(111).used == 0
                assert e.pool.drain_health_events() == {'events': [], 'dropped': 0}
                await gate.restore()
                factory = source._new_client
                def rebuilt(*a, **kw):
                    client = factory(*a, **kw); client._sender = t.b.Sender(); client._sender.account = 111
                    return client
                with patch.object(source, '_new_client', side_effect=rebuilt):
                    await e.pool.recheck_account(111)
                assert source._primary_client is not old and not source._retirement_blocked
                combinations.append(internal + ':' + str(caller_cancel))
            finally:
                await gate.restore(); await asyncio.gather(task, return_exceptions=True)
    return dict(native_failure_retry=combinations, failed_client_never_reused=True)

async def actual_caller_cancel_at_admission():
    outcomes = []
    for after in (False, True):
        e = await t.setup()
        actual, entered, release = e.store, asyncio.Event(), asyncio.Event()
        class Backend:
            async def load(self): return await actual.load()
            async def compare_and_swap(self, *arguments):
                if after: result = await actual.compare_and_swap(*arguments)
                entered.set()
                await release.wait()
                return result if after else await actual.compare_and_swap(*arguments)
        e.pool._store = Backend()
        reader = asyncio.create_task(t.read(e))
        try:
            await entered.wait(); reader.cancel()
            assert isinstance(await capture(reader), asyncio.CancelledError)
            row = json.loads(await actual.load())['accounts']['111']
            assert (row['active'] is not None) is after
            assert not any(sender.calls for sender in e.senders.values()) and e.budget.status(111).used == 0
            outcomes.append(dict(committed=after, unresolved=after, source_requests=0, caller_requests=reader.cancelling()))
        finally:
            release.set(); await asyncio.gather(reader, return_exceptions=True)
    return dict(admission_cancellation=outcomes)

async def backend_internal_cancel_after_source():
    """Challenge cancellation origin at the remaining awaited authoritative stage."""
    observations = []
    for after in (False, True):
        actual = t.SQLiteAccountPoolStore(t.path('backend-cancel'))
        e = await t.setup(store=actual, daily=t.SQLiteSyncStore(t.path('daily')))
        await e.pool.initialize_sync(t.CHAT, after_id=100)
        calls = [0]
        class Backend:
            async def load(self): return await actual.load()
            async def compare_and_swap(self, *arguments):
                calls[0] += 1
                if calls[0] != 2: return await actual.compare_and_swap(*arguments)
                if after: await actual.compare_and_swap(*arguments)
                own = asyncio.get_running_loop().create_future()
                own.cancel()
                return await own  # Provider's awaited I/O failed; caller was not cancelled.
        e.pool._store = Backend()
        failure = t.errors.FloodWaitError(request=None, capture=7200)
        e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101, 201))]), failure]
        reader = asyncio.create_task(e.pool.sync_group(t.CHAT, limit=200))
        result = await capture(reader)
        row = json.loads(await actual.load())['accounts']['111']
        pending = (await e.pool.get_sync_status(t.CHAT)).pending_batch_id
        observation = dict(commit_happened=after, caller_requests=reader.cancelling(),
            returned=type(result).__name__, returned_prefix=len(getattr(getattr(result, 'partial_result', None), 'messages', ())),
            actual_prefix=len(failure.partial_result.messages), pending=bool(pending),
            unresolved=row['active'] is not None, stored_wait=row['not_before'] - t.f.NOW if row['not_before'] else 0,
            charge=e.budget.status(111).used, second_source_reads=len(e.senders[222].reads))
        observations.append(observation)
        print(json.dumps(dict(observation='backend_internal_cancel', **observation)), flush=True)
    assert all(o['caller_requests'] == 0 and o['returned'] != 'CancelledError' and o['pending']
               and o['returned_prefix'] == 100 for o in observations), 'provider cancellation hid completed source facts'
    return dict(provider_internal_cancellation=observations)

async def run_case(name, function):
    print(json.dumps(dict(start=name)), flush=True)
    error = None
    observation = None
    try:
        observation = await asyncio.wait_for(function(), 15)
    except BaseException as caught:
        error = caught
        traceback.print_exc()
    finally:
        for pool in t.POOLS:
            await pool.close()
        t.POOLS.clear()
    value = dict(case=name, result='PASS' if error is None else 'FAIL', observation=observation,
                 error_type=type(error).__name__ if error is not None else None)
    RESULTS.append(value)
    print(json.dumps(value), flush=True)

async def main(directory):
    t.f.TMP = t.d.TMP = directory
    cases = [('successful_source_and_callback_migration', success_and_migration)]
    for mode in ('raw', 'daily', 'backfill'):
        for cancelled in (False, True):
            cases.append(('prefix_{}_observer_{}'.format(mode, 'cancel' if cancelled else 'close'),
                          lambda mode=mode, cancelled=cancelled: completed_prefix(mode, cancelled)))
    for mode in ('raw', 'daily', 'backfill'):
        cases.append(('source_internal_cancel_' + mode, lambda mode=mode: internal_cancel(mode)))
    cases += [('secondary_finalization', secondary_finalization),
              ('passive_drain_during_close', passive_drain_during_close),
              ('provider_reentry', provider_reentry), ('scope_positive_controls', scope_positive_controls),
              ('observation_bounds', observation_bounds), ('capture_failure', failed_capture_preserves_facts),
              ('native_failed_retirement', native_failed_retirement),
              ('caller_cancel_at_admission', actual_caller_cancel_at_admission)]
    controls = [
        t.test_real_pagination_and_drain_budget,
        t.test_spread_uses_remaining_and_stable_ties,
        t.test_flood_failover_and_restart_wait,
        t.test_changed_identity_at_admission_never_sends_history,
        t.test_timeout_retains_completed_page_and_awaits_cancel,
        t.test_empty_timeout_fails_over_after_quiescence,
        t.test_external_cancel_remains_unresolved_and_no_failover,
        t.test_uncertain_admission_opens_no_source_and_survives_restart,
        t.test_settlement_failure_preserves_data_and_daily_replay,
        t.test_stale_settlement_cannot_erase_newer_stored_facts,
        t.test_recheck_reloads_repaired_stored_credential,
        t.test_recheck_cancellation_holds_ownership_until_sdk_disconnect,
        t.test_cancelled_retirement_cannot_overwrite_repaired_credential_later,
        t.test_repeated_read_cancellation_retains_the_actual_child,
        t.test_cancelled_close_waits_for_actual_source_child,
        t.test_close_cancellation_settles_all_sdk_cleanup_and_stays_closed,
        t.test_actual_cleanup_failure_keeps_body_error_and_can_be_retried,
        t.test_context_exit_preserves_caller_cancellation_after_cleanup,
    ]
    cases += [(test.__name__, test) for test in controls]
    cases.append(('backend_internal_cancel_after_source', backend_internal_cancel_after_source))
    with c.install(t):
        for name, function in cases:
            await run_case(name, function)
    summary = dict(combined_cases=len(cases), passed=sum(r['result'] == 'PASS' for r in RESULTS),
                   failed=[r['case'] for r in RESULTS if r['result'] != 'PASS'])
    print(json.dumps(dict(summary=summary)), flush=True)
    return 0 if not summary['failed'] else 1

if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='tgdata17-p0-state-') as directory, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        sys.exit(asyncio.run(main(Path(directory))))
