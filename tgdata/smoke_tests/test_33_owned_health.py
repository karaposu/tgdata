"""Account-owned health on real Telethon 1.45.0; no network or project login."""
import asyncio
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import telethon
from telethon import errors
from telethon.network.mtprotosender import MTProtoSender
from telethon.tl import functions, types
from tgdata import TgData, AuthRequiredError, health
from tgdata.account_operation import AccountIdentityError
from tgdata.smoke_tests import test_32_account_operation as fx


FACADES = []
RPC_TASKS = []
ORIGINAL_SEND = fx.Wire.send


class RPCReply:
    """A decoded server failure; the actual SDK constructs its Python exception."""
    def __init__(self, code, message):
        self.code, self.message = code, message
        self.error = None

    @classmethod
    def from_error(cls, error):
        name = health.telegram_error_name(error)
        if hasattr(error, 'seconds'):
            name = name.replace('_X', '_' + str(error.seconds))
        return cls(error.code, name)

    def send(self, wire, request, ordered=False):
        sender = MTProtoSender(wire.auth_key, loggers=wire.client._log)
        sender._user_connected = True
        sender._send_queue = []
        future = sender.send(request, ordered=ordered)
        state = sender._send_queue.pop()
        state.msg_id = 123
        sender._pending_state[state.msg_id] = state
        message = SimpleNamespace(obj=SimpleNamespace(req_msg_id=state.msg_id,
            error=types.RpcError(self.code, self.message), body=None))

        async def deliver():
            await sender._handle_rpc_result(message)
            self.error = future.exception()

        RPC_TASKS.append(asyncio.create_task(deliver()))
        return future


def wire_send(wire, request, ordered=False):
    if isinstance(request, (list, tuple)):
        return [wire_send(wire, item, ordered=ordered) for item in request]
    inner = request
    while hasattr(inner, 'query'):
        inner = inner.query
    name = type(inner).__name__
    queue = wire.script.get(name)
    reply = queue[0] if queue else wire.fixture.responses.get(name)
    if isinstance(reply, RPCReply):
        if queue:
            queue.pop(0)
        wire.calls.append(name)
        return reply.send(wire, request, ordered=ordered)
    return ORIGINAL_SEND(wire, request, ordered=ordered)


def setup(callback=None, **kwargs):
    f = fx.Fixture(**kwargs)
    tg = TgData(str(f.config), health_callback=callback, account_label='test account')
    tg.connection_engine = f.engine
    FACADES.append(tg)
    return tg, f


async def deliveries(tg):
    # Callback re-entry may schedule a suppressed log-only delivery.
    for _ in range(20):
        tasks = {task for m in tg._account_health.values() for task in m._tasks}
        if not tasks:
            return
        await asyncio.gather(*tasks)
        await fx.turns()
    raise AssertionError('Notifications did not retire')


async def fail(tg, f, kind=errors.ChannelPrivateError, *, owner=222, group=7,
               method='read', caught=False, seconds=None):
    request = fx.history()
    descriptor = kind(request, capture=seconds) if seconds is not None else kind(request)
    reply = RPCReply.from_error(descriptor)
    try:
        async with tg._account_health_operation(owner, method, group) as (op, observation):
            f.wire.script['GetHistoryRequest'] = [reply]
            if caught:
                assert await fx.expect(kind, op.client(request)) is reply.error
            else:
                await op.client(request)
    except kind as actual:
        assert not caught and actual is reply.error
    else:
        assert caught
    return reply.error


async def read(tg, f, *, owner=222, group=7, confirm=False, method='read'):
    async with tg._account_health_operation(owner, method, group) as (op, observation):
        await op.client(fx.history())
        if confirm:
            observation.confirm_group_access()


async def test_fixed_owner_event_and_snapshot_survive_stale_cache():
    events = []
    tg, f = setup(events.append, cached=111)
    await fail(tg, f)
    client = f.clients[0]
    f.engine._primary_client = client
    client._mb_entity_cache.set_self_user(333, False, 333)
    await deliveries(tg)
    snap = tg.get_account_health(222)
    assert events[0]['account'] == snap['account'] == dict(
        label='test account', session='synthetic_session', user_id=222)
    assert events[0]['source'] == 'rpc' and snap['no_access']['7']
    assert tg.get_account_health(111) is tg.get_account_health(333) is None
    assert tg._health.snapshot()['account']['user_id'] == 333
    assert tg._health.snapshot()['events'] == 0


async def test_query_unknown_validation_and_no_io():
    tg = TgData('/does/not/exist/config.ini')
    FACADES.append(tg)
    with patch.object(tg.connection_engine, '_load_config', side_effect=AssertionError('I/O')):
        assert tg.get_account_health(222) is None
        for value in (None, True, False, '222', 222.0, 0, -1, object()):
            fx.refuses(ValueError, lambda: tg.get_account_health(value))
    assert tg.connection_engine._primary_client is None


async def test_snapshot_nested_values_are_independent():
    tg, f = setup()
    await fail(tg, f)
    await fail(tg, f, errors.FloodWaitError, seconds=120)
    snap = tg.get_account_health(222)
    snap['account']['user_id'] = 111
    snap['no_access']['7']['error'] = 'changed'
    snap['waiting']['messages.GetHistoryRequest']['seconds'] = 999
    actual = tg.get_account_health(222)
    assert actual['account']['user_id'] == 222
    assert actual['no_access']['7']['error'] == 'CHANNEL_PRIVATE'
    assert actual['waiting']['messages.GetHistoryRequest']['seconds'] == 120


async def test_two_accounts_keep_independent_conditions():
    tg, f = setup(accounts=[222, 333, 333])
    await fail(tg, f, errors.UserDeactivatedBanError)
    await fail(tg, f, owner=333, group=8)
    await read(tg, f, owner=333, group=8, confirm=True)
    assert tg.get_account_health(222)['verdict'] == 'banned'
    assert tg.get_account_health(333)['verdict'] == 'ok'
    assert not tg.get_account_health(333)['no_access']


async def test_instances_do_not_share_even_the_same_owner():
    a, fa = setup()
    b, fb = setup()
    await fail(a, fa)
    await read(b, fb, confirm=True)
    assert a.get_account_health(222)['no_access']['7']
    assert not b.get_account_health(222)['no_access']


async def test_mismatch_inside_legacy_call_has_no_owner():
    tg, f = setup(cached=111)
    async def work():
        async with tg._health.call('outer', 7):
            async with tg._account_health_operation(111, 'read', 7):
                raise AssertionError('Must refuse')
    await fx.expect(AccountIdentityError, work())
    assert tg.get_account_health(111) is tg.get_account_health(222) is None
    assert tg._health.snapshot()['events'] == 0 and f.wire.closed
    assert 'GetHistoryRequest' not in f.wire.calls


async def test_unverified_auth_error_and_wrappers_are_excluded():
    error = errors.AuthKeyUnregisteredError(functions.updates.GetStateRequest())
    tg, f = setup(cached=111, responses={'GetStateRequest': error})
    async def work():
        async with tg._health.call('outer', 7):
            try:
                async with tg._account_health_operation(222, 'read', 7):
                    raise AssertionError('Must refuse')
            except AuthRequiredError as exc:
                assert exc.__cause__ is error
                await health.report(exc)
                raise RuntimeError('wrapper') from exc
    await fx.expect(RuntimeError, work())
    assert tg.get_account_health(222) is None
    assert tg._health.snapshot()['events'] == 0 and f.wire.closed


async def test_setup_rpc_is_not_an_owned_or_legacy_condition():
    error = errors.ChannelPrivateError(fx.history())
    tg, f = setup(connect_error=error)
    async def work():
        async with tg._health.call('outer', 7):
            async with tg._account_health_operation(222, 'read', 7):
                raise AssertionError('Must refuse')
    assert await fx.expect(type(error), work()) is error
    assert tg._health.snapshot()['events'] == 0 and not tg._account_health


async def test_other_legacy_error_after_isolation_still_reports():
    tg, f = setup()
    error = errors.ChannelPrivateError(fx.history())
    async def work():
        async with tg._health.call('outer', 8):
            async with tg._account_health_operation(222, 'read', 7):
                pass
            raise error
    assert await fx.expect(type(error), work()) is error
    assert tg._health.snapshot()['no_access']['8']
    assert tg.get_account_health(222)['events'] == 0


async def test_owned_success_cannot_recover_enclosing_legacy_group():
    tg, f = setup()
    async with tg._health.call('old', 7):
        await health.report(errors.ChannelPrivateError(fx.history()))
    async with tg._health.call('outer', 7):
        health.note_answer()  # Even earlier ambient evidence must not be mixed.
        await read(tg, f, confirm=True)
    assert tg._health.snapshot()['no_access']['7']


async def test_local_exception_with_rpc_cause_does_not_manufacture_health():
    tg, f = setup()
    error = OSError('local output failed')
    async def work():
        async with tg._health.call('outer', 7):
            async with tg._account_health_operation(222, 'read', 7):
                raise error from errors.ChannelPrivateError(fx.history())
    assert await fx.expect(OSError, work()) is error
    assert tg.get_account_health(222)['events'] == tg._health.snapshot()['events'] == 0


async def test_caught_rpc_stays_recorded_after_earlier_success():
    events = []
    tg, f = setup(events.append)
    await fail(tg, f, errors.AuthKeyUnregisteredError, caught=True)
    assert tg.get_account_health(222)['verdict'] == 'logged out'
    await deliveries(tg)
    assert [e['verdict'] for e in events] == ['logged out']
    assert events[0]['request'] == 'messages.GetHistoryRequest'


async def test_nested_budget_verification_reports_once():
    events = []
    tg, f = setup(events.append, budget=True)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        error = errors.AuthKeyUnregisteredError(functions.users.GetUsersRequest([]))
        f.wire.script['GetUsersRequest'] = [error]
        raised = await fx.expect(AuthRequiredError, op.client(fx.history()))
        assert raised.__cause__ is error
        await health.report(raised, 'handled')
    assert f.budget.status(222).remaining == 20  # proof refused before reservation
    assert tg.get_account_health(222)['verdict'] == 'logged out'
    await deliveries(tg)
    assert len(events) == 1 and events[0]['request'] == 'users.GetUsersRequest'


async def test_ambient_report_and_sleep_do_not_create_owned_facts():
    tg, f = setup()
    async with tg._account_health_operation(222, 'read', 7):
        assert await health.report(errors.ChannelPrivateError(fx.history())) is None
        capture = health._SleepCapture()
        import logging
        capture.filter(logging.LogRecord('telethon.client.users', logging.INFO, '', 0,
            health._SLEEP_MSG, ('', 12, 'delta', 'GetHistoryRequest'), None))
    assert tg.get_account_health(222)['events'] == 0


async def test_real_multi_error_leaves_record_even_when_caught():
    events = []
    tg, f = setup(events.append)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        denied = errors.ChannelPrivateError(fx.history())
        f.wire.script['GetHistoryRequest'] = [denied]
        error = await fx.expect(errors.MultiError,
            op.client([fx.history(), fx.history()]))
        assert error.exceptions == [denied, None]
        assert not observation.requests  # Partial successes do not recover.
    assert tg.get_account_health(222)['no_access']['7']
    await deliveries(tg)
    assert len(events) == 1 and events[0]['source'] == 'rpc'


async def test_successful_list_recovers_matching_request_wait():
    tg, f = setup()
    await fail(tg, f, errors.FloodWaitError, seconds=120)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.client([fx.history(), functions.updates.GetStateRequest()])
    assert not tg.get_account_health(222)['waiting']


async def test_foreign_client_cannot_supply_evidence_or_errors():
    tg, f = setup()
    other = fx.Fixture(accounts=[333])
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        async with other.engine._account_operation(333) as foreign:
            denied = errors.ChannelPrivateError(fx.history())
            other.wire.script['GetHistoryRequest'] = [denied]
            assert await fx.expect(type(denied), foreign.client(fx.history())) is denied
        assert not observation.requests
    assert tg.get_account_health(222)['events'] == 0


async def test_inherited_child_task_cannot_record_or_confirm():
    tg, f = setup()
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        client = op.client
        denied = errors.ChannelPrivateError(fx.history())
        f.wire.script['GetHistoryRequest'] = [denied]
        async def child():
            assert await fx.expect(type(denied), client(fx.history())) is denied
            fx.refuses(RuntimeError, observation.confirm_group_access)
        await asyncio.create_task(child())
        assert not observation.requests
    assert tg.get_account_health(222)['events'] == 0


async def test_inactive_inherited_context_cannot_record():
    tg, f = setup()
    release = asyncio.Event()
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        client = op.client
        async def child():
            await release.wait()
            health.note_rpc_error(client, errors.ChannelPrivateError(fx.history()))
            health.note_answer(client, fx.history())
            fx.refuses(RuntimeError, observation.confirm_group_access)
        task = asyncio.create_task(child())
    release.set()
    await task
    assert not observation.requests and tg.get_account_health(222)['events'] == 0


async def test_self_proof_and_metadata_alone_never_recover_group():
    tg, f = setup()
    await fail(tg, f)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.verify_account()
        await op.client(functions.updates.GetStateRequest())
    assert tg.get_account_health(222)['no_access']['7']
    await read(tg, f, confirm=True)
    assert not tg.get_account_health(222)['no_access']


async def test_confirmation_requires_current_lifetime_and_request_evidence():
    tg, f = setup()
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        fx.refuses(RuntimeError, observation.confirm_group_access)
        await op.client(fx.history())
        observation.confirm_group_access()
    fx.refuses(RuntimeError, observation.confirm_group_access)


async def test_caught_identity_loss_vetoes_prior_group_and_account_recovery():
    tg, f = setup()
    await fail(tg, f)
    await fail(tg, f, errors.UserDeactivatedBanError)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.client(fx.history())
        observation.confirm_group_access()
        f.wire.account = 333
        await fx.expect(AccountIdentityError, op.verify_account())
    snap = tg.get_account_health(222)
    assert snap['verdict'] == 'banned' and snap['no_access']['7']
    assert snap['events'] == 2


async def test_caught_auth_loss_vetoes_prior_group_recovery():
    tg, f = setup()
    await fail(tg, f)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.client(fx.history())
        observation.confirm_group_access()
        f.wire.script['GetUsersRequest'] = [errors.AuthKeyUnregisteredError(
            functions.users.GetUsersRequest([]))]
        await fx.expect(AuthRequiredError, op.verify_account())
    snap = tg.get_account_health(222)
    assert snap['verdict'] == 'logged out' and snap['no_access']['7']
    assert snap['events'] == 2


async def test_restriction_needs_matching_method_and_post_proof_work():
    tg, f = setup()
    await fail(tg, f, errors.PeerFloodError)
    async with tg._account_health_operation(222, 'read', 7):
        pass
    assert tg.get_account_health(222)['verdict'] == 'restricted'
    await read(tg, f, method='different')
    assert tg.get_account_health(222)['verdict'] == 'restricted'
    await read(tg, f)
    assert tg.get_account_health(222)['verdict'] == 'ok'


async def test_same_call_cannot_recover_its_own_wait():
    tg, f = setup()
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        f.wire.script['GetHistoryRequest'] = [errors.FloodWaitError(fx.history(), capture=1)]
        await fx.expect(errors.FloodWaitError, op.client(fx.history()))
        # SDK ignores a cached wait <= 3 seconds; the real second request succeeds.
        await op.client(fx.history())
    assert tg.get_account_health(222)['events'] == 1
    assert 'messages.GetHistoryRequest' in tg._account_health[222]._waiting


async def test_wait_recovery_requires_matching_request():
    tg, f = setup()
    await fail(tg, f, errors.FloodWaitError, seconds=120)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.client(functions.updates.GetStateRequest())
    assert tg.get_account_health(222)['waiting']['messages.GetHistoryRequest']
    await read(tg, f)
    assert not tg.get_account_health(222)['waiting']


async def overlap(kind, **kwargs):
    tg, f = setup()
    opened, release = asyncio.Event(), asyncio.Event()
    async def older():
        async with tg._account_health_operation(222, 'read', 7) as (op, observation):
            opened.set()
            await release.wait()
            await op.client(fx.history())
            observation.confirm_group_access()
    task = asyncio.create_task(older())
    await opened.wait()
    await fail(tg, f, kind, **kwargs)
    release.set()
    await task
    return tg.get_account_health(222)


async def test_older_work_cannot_clear_newer_account_condition():
    snap = await overlap(errors.UserDeactivatedBanError)
    assert snap['verdict'] == 'banned' and snap['events'] == 1


async def test_older_work_cannot_clear_newer_group_condition():
    snap = await overlap(errors.ChannelPrivateError)
    assert snap['no_access']['7'] and snap['events'] == 1


async def test_older_work_cannot_clear_newer_request_wait():
    snap = await overlap(errors.FloodWaitError, seconds=120)
    assert snap['waiting']['messages.GetHistoryRequest']['seconds'] == 120 and snap['events'] == 1


async def test_operation_order_starts_before_authentication():
    proof = asyncio.get_running_loop().create_future()
    tg, f = setup(cached=111, responses={'GetUsersRequest': proof})
    async def older():
        async with tg._account_health_operation(222, 'read', 7):
            pass
    task = asyncio.create_task(older())
    while not f.clients or 'GetUsersRequest' not in f.clients[0]._sender.calls:
        await asyncio.sleep(0)
    f.responses.clear()
    await fail(tg, f, errors.UserDeactivatedBanError)
    proof.set_result([fx.user(222)])
    await task
    assert tg.get_account_health(222)['verdict'] == 'banned'


async def test_later_proof_can_recover_account_condition():
    tg, f = setup()
    await fail(tg, f, errors.UserDeactivatedBanError)
    async with tg._account_health_operation(222, 'read', 7):
        pass
    assert tg.get_account_health(222)['verdict'] == 'ok'
    assert tg.get_account_health(222)['events'] == 2


async def test_parent_reported_flags_stay_in_same_monitor_and_task():
    a, b = health.HealthMonitor(), health.HealthMonitor()
    async with a.call('outer') as outer:
        async with b.call('inner'):
            await health.report(errors.UserDeactivatedBanError(fx.history()))
        assert not outer.reported
        async with a.call('same'):
            await health.report(errors.UserDeactivatedBanError(fx.history()))
        assert ('account',) in outer.reported


async def test_sync_async_and_cancelled_callbacks_preserve_original_error():
    for asynchronous in (False, True):
        for kind in (ValueError, asyncio.CancelledError):
            observed = []
            def body(event):
                assert f.wire.closed
                observed.append(event)
                raise kind('observer')
            async def async_callback(event):
                body(event)
            tg, f = setup(async_callback if asynchronous else body)
            await fail(tg, f)
            assert tg.get_account_health(222)['events'] == 1
            await deliveries(tg)
            assert len(observed) == 1


async def test_callback_failure_does_not_replace_successful_result():
    def callback(event):
        raise ValueError('observer')
    tg, f = setup(callback)
    async def work():
        async with tg._account_health_operation(222, 'read', 7) as (op, observation):
            f.wire.script['GetHistoryRequest'] = [errors.ChannelPrivateError(fx.history())]
            await fx.expect(errors.ChannelPrivateError, op.client(fx.history()))
            return 42
    assert await work() == 42
    await deliveries(tg)


async def test_notifications_wait_for_source_disconnect():
    events = []
    tg, f = setup(events.append)
    release = asyncio.Event()
    async def work():
        async with tg._account_health_operation(222, 'read', 7) as (op, observation):
            f.wire.close_release = release
            f.wire.script['GetHistoryRequest'] = [errors.ChannelPrivateError(fx.history())]
            await op.client(fx.history())
    task = asyncio.create_task(work())
    while not f.clients:
        await asyncio.sleep(0)
    await f.wire.close_entered.wait()
    assert not events and not task.done()
    assert tg.get_account_health(222)['no_access']['7']
    release.set()
    await fx.expect(errors.ChannelPrivateError, task)
    await deliveries(tg)
    assert len(events) == 1 and f.wire.closed


async def test_cleanup_failure_keeps_primary_and_no_extra_health():
    events = []
    tg, f = setup(events.append)
    primary = errors.ChannelPrivateError(fx.history())
    async def work():
        async with tg._account_health_operation(222, 'read', 7) as (op, observation):
            f.wire.close_error = errors.AuthKeyUnregisteredError(None)
            f.wire.script['GetHistoryRequest'] = [primary]
            await op.client(fx.history())
    assert await fx.expect(type(primary), work()) is primary
    assert f.wire.close_calls == 1
    assert tg.get_account_health(222)['verdict'] == 'ok'
    await deliveries(tg)
    assert len(events) == 1


async def test_cancellation_waits_for_cleanup_and_preserves_observation():
    events = []
    tg, f = setup(events.append)
    ready, release = asyncio.Event(), asyncio.Event()
    async def work():
        async with tg._account_health_operation(222, 'read', 7) as (op, observation):
            f.wire.close_release = release
            f.wire.script['GetHistoryRequest'] = [errors.ChannelPrivateError(fx.history())]
            await fx.expect(errors.ChannelPrivateError, op.client(fx.history()))
            ready.set()
            await asyncio.Event().wait()
    task = asyncio.create_task(work())
    await ready.wait()
    task.cancel()
    await f.wire.close_entered.wait()
    task.cancel()
    await fx.turns()
    assert not task.done() and not events
    release.set()
    await fx.expect(asyncio.CancelledError, task)
    await deliveries(tg)
    assert len(events) == 1 and f.wire.closed


async def test_callback_reentry_records_without_recursive_delivery():
    seen = []
    async def callback(event):
        seen.append(event)
        await fail(tg, f, group=8)
    tg, f = setup(callback)
    await fail(tg, f)
    await deliveries(tg)
    assert len(seen) == 1
    assert set(tg.get_account_health(222)['no_access']) == {'7', '8'}


async def test_close_retires_pending_notifications():
    entered = asyncio.Event()
    async def callback(event):
        entered.set()
        await asyncio.Event().wait()
    tg, f = setup(callback)
    await fail(tg, f)
    await entered.wait()
    await tg.close()
    await fx.turns()
    assert not tg._account_health[222]._tasks


async def test_callback_can_close_without_awaiting_itself():
    finished = asyncio.Event()
    async def callback(event):
        await tg.close()
        finished.set()
    tg, f = setup(callback)
    await fail(tg, f)
    await finished.wait()
    await deliveries(tg)


async def test_reporting_failure_does_not_replace_rpc():
    tg, f = setup()
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        error = errors.ChannelPrivateError(fx.history())
        f.wire.script['GetHistoryRequest'] = [error]
        with patch.object(observation.monitor, '_record', side_effect=ValueError('observer bug')):
            assert await fx.expect(type(error), op.client(fx.history())) is error
        assert observation.failed


async def test_r4_wrapped_wait_recovers_on_matching_request():
    events = []
    tg, f = setup(events.append)
    error = await fail(tg, f, errors.FloodWaitError, seconds=120)
    assert isinstance(error.request, functions.InvokeWithoutUpdatesRequest)
    assert tg.get_account_health(222)['waiting']['messages.GetHistoryRequest']['seconds'] == 120
    await read(tg, f)
    assert not tg.get_account_health(222)['waiting']
    await deliveries(tg)
    assert [(e['verdict'], e['request']) for e in events] == [
        ('waiting', 'messages.GetHistoryRequest'), ('ok', 'messages.GetHistoryRequest')]


async def test_r4_distinct_waits_and_namespaces():
    tg, f = setup()
    cases = [(fx.history(), 'messages.GetHistoryRequest', 120),
             (functions.updates.GetStateRequest(), 'updates.GetStateRequest', 15),
             (functions.messages.GetMessagesRequest([]), 'messages.GetMessagesRequest', 20),
             (functions.channels.GetMessagesRequest(types.InputChannel(7, 7), []),
              'channels.GetMessagesRequest', 30)]
    for request, key, seconds in cases:
        async with tg._account_health_operation(222, 'read', 7) as (op, observation):
            reply = RPCReply(420, 'FLOOD_WAIT_' + str(seconds))
            f.wire.script[type(request).__name__] = [reply]
            assert await fx.expect(errors.FloodWaitError, op.client(request)) is reply.error
    waiting = tg.get_account_health(222)['waiting']
    assert {key: item['seconds'] for key, item in waiting.items()} == {
        key: seconds for _, key, seconds in cases}
    await read(tg, f)
    assert set(tg.get_account_health(222)['waiting']) == {key for _, key, _ in cases[1:]}


async def test_r4_nested_envelopes_match_leaf():
    tg, f = setup()
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        reply = RPCReply(420, 'FLOOD_WAIT_120')
        f.wire.script['GetHistoryRequest'] = [reply]
        request = functions.InvokeWithTakeoutRequest(123, fx.history())
        await fx.expect(errors.FloodWaitError, op.client(request))
        assert reply.error.request.query is request
    assert 'messages.GetHistoryRequest' in tg.get_account_health(222)['waiting']
    await read(tg, f)
    assert not tg.get_account_health(222)['waiting']


async def test_r4_repeated_identity_is_not_refused_action_success():
    tg, f = setup()
    await fail(tg, f, errors.PeerFloodError)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.verify_account()
        await op.client(functions.updates.GetStateRequest())
    assert tg.get_account_health(222)['verdict'] == 'restricted'
    assert 'GetHistoryRequest' not in f.wire.calls
    await read(tg, f)
    assert tg.get_account_health(222)['verdict'] == 'ok'


async def test_r4_fresh_legacy_rpc_precedes_old_neutral_context():
    for handled in (False, True):
        for wrapped in (False, True):
            tg, f = setup(accounts=[111, 222], cached=111)
            legacy = f.engine._new_client()
            f.engine._primary_client = legacy
            await legacy.connect()
            reply = RPCReply(400, 'CHANNEL_PRIVATE')
            try:
                async with tg._health.call('legacy_outer', 7):
                    try:
                        async with tg._account_health_operation(111, 'read', 7):
                            raise AssertionError('Must refuse')
                    except AccountIdentityError:
                        legacy._sender.script['GetHistoryRequest'] = [reply]
                        try:
                            await legacy(fx.history())
                        except errors.ChannelPrivateError as error:
                            if handled:
                                assert (await health.report(error)).verdict == 'no access'
                            if wrapped:
                                raise RuntimeError('forwarded new RPC') from error
                            raise
            except (errors.ChannelPrivateError, RuntimeError) as error:
                assert (error.__cause__ if wrapped else error) is reply.error
            else:
                raise AssertionError('RPC must propagate')
            snap = tg._health.snapshot()
            assert snap['account']['user_id'] == 111
            assert snap['events'] == 1 and snap['no_access']['7']


async def test_r4_unverified_child_error_is_not_parent_health():
    reply = RPCReply(401, 'AUTH_KEY_UNREGISTERED')
    tg, f = setup(accounts=[111, 222], cached=111, responses={'GetStateRequest': reply})
    legacy = f.engine._new_client()
    f.engine._primary_client = legacy
    await legacy.connect()
    async def child():
        async with tg._account_health_operation(222, 'read', 7):
            raise AssertionError('Must refuse')
    try:
        async with tg._health.call('parent', 7):
            await asyncio.create_task(child())
    except AuthRequiredError as error:
        assert error.__cause__ is reply.error
        assert health.classify(error, include_reported=True).verdict == 'logged out'
        from tgdata.tgdata import _polling_cannot_recover
        assert _polling_cannot_recover(reply.error)
    else:
        raise AssertionError('Must propagate')
    assert tg._health.snapshot()['events'] == 0
    assert tg.get_account_health(222) is None


async def test_r4_unwrapped_explicit_source_stays_neutral():
    reply = RPCReply(401, 'AUTH_KEY_UNREGISTERED')
    tg, f = setup(cached=111, responses={'GetStateRequest': reply})
    try:
        async with tg._health.call('parent', 7):
            try:
                async with tg._account_health_operation(222, 'read', 7):
                    raise AssertionError('Must refuse')
            except AuthRequiredError as error:
                original_source = error.__cause__
            # Outside the handler: no implicit link back to the excluded wrapper.
            raise original_source
    except errors.AuthKeyUnregisteredError as error:
        assert error is reply.error
        assert health.classify(error, include_reported=True).verdict == 'logged out'
    assert tg._health.snapshot()['events'] == 0


async def test_r4_changed_batch_input_cannot_invent_recovery():
    tg, f = setup(cached=111)
    await fail(tg, f, errors.FloodWaitError, seconds=120)
    requests = [functions.updates.GetStateRequest()]
    held = asyncio.get_running_loop().create_future()
    async def worker():
        async with tg._account_health_operation(222, 'read', 7) as (op, observation):
            f.wire.script['GetStateRequest'] = [held]
            await op.client(requests)
            assert observation.requests == {'updates.GetStateRequest'}
    task = asyncio.create_task(worker())
    while len(f.clients) < 2 or f.wire.calls.count('GetStateRequest') < 2:
        await asyncio.sleep(0)
    requests[:] = [fx.history()]
    held.set_result(types.updates.State(1, 1, fx.DATE, 1, 0))
    await task
    assert tg.get_account_health(222)['waiting']['messages.GetHistoryRequest']


async def test_r4_request_keys_bound_envelopes_and_keep_unknown_types():
    from telethon.tl.tlobject import TLRequest
    from tgdata.owned_health import _request_key
    leaf = fx.history()
    envelopes = [functions.InvokeAfterMsgRequest(1, leaf),
                 functions.InvokeAfterMsgsRequest([1], leaf),
                 functions.InitConnectionRequest(1, 'test', 'test', '1', 'en', '', 'en', leaf),
                 functions.InvokeWithLayerRequest(229, leaf),
                 functions.InvokeWithoutUpdatesRequest(leaf),
                 functions.InvokeWithMessagesRangeRequest(types.MessageRange(1, 2), leaf),
                 functions.InvokeWithTakeoutRequest(123, leaf)]
    assert all(_request_key(item) == 'messages.GetHistoryRequest' for item in envelopes)
    assert _request_key(functions.PingRequest(1)) == 'PingRequest'
    class Unknown(TLRequest):
        query = leaf
    assert _request_key(Unknown()) == __name__ + '.Unknown'
    cyclic = functions.InvokeWithoutUpdatesRequest(leaf)
    cyclic.query = cyclic
    assert _request_key(cyclic) is None
    assert _request_key(functions.InvokeWithoutUpdatesRequest(None)) is None
    for value in (None, True, object(), [leaf]):
        assert _request_key(value) is None
    nested = leaf
    for _ in range(8):
        nested = functions.InvokeWithoutUpdatesRequest(nested)
    assert _request_key(nested) == 'messages.GetHistoryRequest'
    assert _request_key(functions.InvokeWithoutUpdatesRequest(nested)) is None


async def test_r4_capture_does_not_consume_lazy_input_or_reuse_old_binding():
    tg, f = setup()
    consumed = []
    def lazy():
        consumed.append(True)
        yield fx.history()
    class CustomList(list):
        def __iter__(self):
            raise AssertionError('Observer must not iterate a custom container')
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        for request in (lazy(), CustomList([fx.history()])):
            evidence = health.capture_request_evidence(op.client, request)
            health.note_answer(op.client, request, evidence)
        assert not consumed and not observation.requests
        fx.refuses(RuntimeError, observation.confirm_group_access)
        old_evidence = health.capture_request_evidence(op.client, fx.history())
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        health.note_answer(op.client, fx.history(), old_evidence)
        assert not observation.requests


async def test_r4_restriction_replacement_uses_the_new_refused_request():
    tg, f = setup()
    await fail(tg, f, errors.PeerFloodError)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        f.wire.script['GetStateRequest'] = [RPCReply(400, 'PEER_FLOOD')]
        await fx.expect(errors.PeerFloodError, op.client(functions.updates.GetStateRequest()))
    await read(tg, f)
    assert tg.get_account_health(222)['verdict'] == 'restricted'
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.client(functions.updates.GetStateRequest())
    assert tg.get_account_health(222)['verdict'] == 'ok'


async def test_r4_unknown_refusal_key_never_reuses_an_old_key():
    tg, f = setup()
    await fail(tg, f, errors.PeerFloodError)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        # Explicit malformed-metadata case, not a claim about sender-built errors.
        f.wire.script['GetHistoryRequest'] = [errors.PeerFloodError(None)]
        await fx.expect(errors.PeerFloodError, op.client(fx.history()))
    await read(tg, f)
    assert tg.get_account_health(222)['verdict'] == 'restricted'


async def test_r4_restriction_does_not_recover_in_its_own_call():
    tg, f = setup()
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        f.wire.script['GetHistoryRequest'] = [RPCReply(400, 'PEER_FLOOD')]
        await fx.expect(errors.PeerFloodError, op.client(fx.history()))
        await op.client(fx.history())
    assert tg.get_account_health(222)['verdict'] == 'restricted'
    await read(tg, f)
    assert tg.get_account_health(222)['verdict'] == 'ok'


async def test_r4_older_action_success_does_not_clear_newer_restriction():
    snapshot = await overlap(errors.PeerFloodError)
    assert snapshot['verdict'] == 'restricted' and snapshot['events'] == 1


async def test_r4_identity_request_refusal_has_its_own_positive_recovery():
    tg, f = setup(budget=True)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        f.wire.script['GetUsersRequest'] = [RPCReply(400, 'PEER_FLOOD')]
        await fx.expect(errors.PeerFloodError, op.client(fx.history()))
    assert tg.get_account_health(222)['verdict'] == 'restricted'
    assert 'GetHistoryRequest' not in f.wire.calls and f.budget.status(222).used == 0
    async with tg._account_health_operation(222, 'read', 7):
        pass  # Initial proof is outside owned request observation.
    assert tg.get_account_health(222)['verdict'] == 'restricted'
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.verify_account()
    assert tg.get_account_health(222)['verdict'] == 'ok'


async def test_r4_budget_proof_without_admitted_read_cannot_recover_read():
    from tgdata import ReadBudgetExceeded
    tg, f = setup(budget=True)
    await fail(tg, f, errors.PeerFloodError)
    assert f.budget.status(222).used == 1
    f.budget.configure(222, 1)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await fx.expect(ReadBudgetExceeded, op.client(fx.history()))
        assert observation.requests == {'users.GetUsersRequest'}
    assert 'GetHistoryRequest' not in f.wire.calls
    assert tg.get_account_health(222)['verdict'] == 'restricted'


async def test_r4_implicit_context_before_isolation_is_not_adopted():
    tg, f = setup(cached=111)
    legacy = f.engine._new_client()
    f.engine._primary_client = legacy
    await legacy.connect()
    reply = RPCReply(400, 'CHANNEL_PRIVATE')
    legacy._sender.script['GetHistoryRequest'] = [reply]
    async with tg._health.call('legacy', 7):
        try:
            await legacy(fx.history())
        except errors.ChannelPrivateError as prior:
            with patch.object(f.store, 'load', side_effect=ValueError('local store unavailable')):
                try:
                    async with tg._account_health_operation(222, 'read', 7):
                        raise AssertionError('Must refuse')
                except ValueError as setup_error:
                    assert setup_error.__context__ is prior
            assert (await health.report(prior)).verdict == 'no access'
    assert tg._health.snapshot()['events'] == 1
    assert tg.get_account_health(222) is None


async def test_r4_forwarded_preproof_wrappers_remain_neutral():
    for explicit in (False, True):
        reply = RPCReply(401, 'AUTH_KEY_UNREGISTERED')
        tg, f = setup(cached=111, responses={'GetStateRequest': reply})
        async def child():
            try:
                async with tg._account_health_operation(222, 'read', 7):
                    raise AssertionError('Must refuse')
            except AuthRequiredError as source:
                if explicit:
                    raise RuntimeError('forwarded') from source
                raise RuntimeError('forwarded')
        try:
            async with tg._health.call('parent', 7):
                await asyncio.create_task(child())
        except RuntimeError as error:
            assert health.classify(error, include_reported=True).verdict == 'logged out'
        assert tg._health.snapshot()['events'] == 0


async def test_r4_isolated_sdk_multierror_leaves_remain_neutral():
    tg, f = setup()
    async with tg._health.call('parent', 7):
        try:
            with health.isolate_call():
                async with f.engine._account_operation(222) as op:
                    f.wire.script['GetHistoryRequest'] = [RPCReply(400, 'CHANNEL_PRIVATE'),
                                                        RPCReply(401, 'AUTH_KEY_UNREGISTERED')]
                    await op.client([fx.history(), fx.history()])
        except errors.MultiError as error:
            leaves = error.exceptions
        else:
            raise AssertionError('Expected SDK MultiError')
        for leaf in leaves:
            assert await health.report(leaf) is None
        assert [health.classify(leaf, include_reported=True).verdict for leaf in leaves] == [
            'no access', 'logged out']
    assert tg._health.snapshot()['events'] == 0


async def test_r4_neutral_metadata_failures_and_cycles_preserve_outcomes():
    for failure in (RuntimeError, asyncio.CancelledError):
        class RefusingMarker(AuthRequiredError):
            def __setattr__(self, name, value):
                if name == health._LEGACY_NEUTRAL:
                    raise failure('metadata unavailable')
                super().__setattr__(name, value)
        tg, f = setup()
        primary = RefusingMarker('primary', reason='AUTH_KEY_UNREGISTERED')
        cause = errors.AuthKeyUnregisteredError(functions.updates.GetStateRequest())
        try:
            async with tg._health.call('parent'):
                with health.isolate_call():
                    raise primary from cause
        except RefusingMarker as error:
            assert error is primary and error.__cause__ is cause
        assert tg._health.snapshot()['events'] == 0
    left, right = RuntimeError('left'), RuntimeError('right')
    left.__cause__, right.__cause__ = right, left
    try:
        with health.isolate_call():
            raise left
    except RuntimeError as error:
        assert error is left
    assert health._legacy_neutral(left) and health._legacy_neutral(right)


async def test_r4_real_multierror_partial_success_is_not_recovery_evidence():
    tg, f = setup()
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        reply = RPCReply(400, 'CHANNEL_PRIVATE')
        f.wire.script['GetHistoryRequest'] = [reply]
        result = await fx.expect(errors.MultiError, op.client([fx.history(), fx.history()]))
        assert result.exceptions == [reply.error, None]
        assert not observation.requests
        fx.refuses(RuntimeError, observation.confirm_group_access)
    assert tg.get_account_health(222)['no_access']['7']


async def main():
    assert telethon.__version__ == '1.45.0'
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    if '--revision4' in sys.argv:
        tests = [test for test in tests if test.__name__.startswith('test_r4_')]
    passed = 0
    with tempfile.TemporaryDirectory(prefix='tgdata_owned_health_') as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(fx.Wire, 'send', wire_send):
        fx.TMP = Path(tmp)
        for test in tests:
            print('TEST:', test.__name__, flush=True)
            try:
                await asyncio.wait_for(test(), 15)
            except (Exception, asyncio.CancelledError):
                traceback.print_exc()
            else:
                passed += 1
            finally:
                await asyncio.gather(*RPC_TASKS)
                RPC_TASKS.clear()
                for client in fx.CLIENTS:
                    client._sender.close_error = None
                    if client._sender.close_release is not None:
                        client._sender.close_release.set()
                    await client.disconnect()
                fx.CLIENTS.clear()
                for tg in FACADES:
                    await tg.close()
                FACADES.clear()
    print('Passed: {}/{}'.format(passed, len(tests)))
    return 0 if passed == len(tests) else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
