"""Account-owned health on real Telethon 1.45.0; no network or project login."""
import asyncio
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import telethon
from telethon import errors
from telethon.tl import functions
from tgdata import TgData, AuthRequiredError, health
from tgdata.account_operation import AccountIdentityError
from tgdata.smoke_tests import test_32_account_operation as fx


FACADES = []


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
    error = kind(request, capture=seconds) if seconds is not None else kind(request)
    try:
        async with tg._account_health_operation(owner, method, group) as (op, observation):
            f.wire.script['GetHistoryRequest'] = [error]
            if caught:
                assert await fx.expect(kind, op.client(request)) is error
            else:
                await op.client(request)
    except kind as actual:
        assert not caught and actual is error
    else:
        assert caught
    return error


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
    snap['waiting']['GetHistoryRequest']['seconds'] = 999
    actual = tg.get_account_health(222)
    assert actual['account']['user_id'] == 222
    assert actual['no_access']['7']['error'] == 'CHANNEL_PRIVATE'
    assert actual['waiting']['GetHistoryRequest']['seconds'] == 120


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
    assert events[0]['request'] == 'GetHistoryRequest'


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
    assert len(events) == 1 and events[0]['request'] == 'GetUsersRequest'


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
    assert 'GetHistoryRequest' in tg._account_health[222]._waiting


async def test_wait_recovery_requires_matching_request():
    tg, f = setup()
    await fail(tg, f, errors.FloodWaitError, seconds=120)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.client(functions.updates.GetStateRequest())
    assert tg.get_account_health(222)['waiting']['GetHistoryRequest']
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
    assert snap['waiting']['GetHistoryRequest']['seconds'] == 120 and snap['events'] == 1


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


async def main():
    assert telethon.__version__ == '1.45.0'
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    original_send = fx.Wire.send
    def send(wire, request, **kwargs):
        if isinstance(request, (list, tuple)):
            return [original_send(wire, item, **kwargs) for item in request]
        return original_send(wire, request, **kwargs)
    passed = 0
    with tempfile.TemporaryDirectory(prefix='tgdata_owned_health_') as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(fx.Wire, 'send', send):
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
