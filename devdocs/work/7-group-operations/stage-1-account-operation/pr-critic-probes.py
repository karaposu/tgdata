"""PR21 adversarial probes: actual SDK/SQLite, synthetic transport, no sockets."""
import asyncio
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from telethon import errors
from telethon.tl import functions, types
from tgdata import AuthRequiredError
from tgdata.account_operation import AccountIdentityError
from tgdata.connection_engine import ConnectionEngine, ProxyConfigError
import tgdata.account_operation as owned
from tgdata.smoke_tests import test_32_account_operation as f


async def until(predicate):
    async def wait():
        while not predicate():
            await asyncio.sleep(0)
    await asyncio.wait_for(wait(), 3)


async def delayed_resolution():
    fixture = f.Fixture(budget=True)
    entered, release = asyncio.Event(), asyncio.Event()
    observed = {}

    class PausedHistory(functions.messages.GetHistoryRequest):
        async def resolve(self, client, utils):
            entered.set()
            await release.wait()
            return await super().resolve(client, utils)

    async def worker():
        async with fixture.engine._account_operation(222) as op:
            request = PausedHistory(types.InputPeerChannel(7, 7), 0, None, 0, 1, 0, 0, 0)
            error = await f.expect(AccountIdentityError, op.client(request))
            observed['refused_actual'] = error.actual_account_id
    task = asyncio.create_task(worker())
    await asyncio.wait_for(entered.wait(), 3)
    fixture.wire.account = 333
    release.set()
    await asyncio.wait_for(task, 3)
    assert observed['refused_actual'] == 333
    assert not {'GetHistoryRequest', 'PausedHistory'}.intersection(fixture.wire.calls)
    assert fixture.budget.status(222).used == fixture.budget.status(333).used == 0
    return dict(actual=333, claims=0, history_sends=0, closed=fixture.wire.closed)


async def cancel_admission():
    fixture = f.Fixture(budget=True)
    ready = asyncio.Event()
    pending = asyncio.get_running_loop().create_future()

    async def worker():
        async with fixture.engine._account_operation(222) as op:
            fixture.wire.script['GetUsersRequest'] = [pending]
            ready.set()
            await op.client(f.history())
    task = asyncio.create_task(worker())
    await asyncio.wait_for(ready.wait(), 3)
    task.cancel()
    await f.expect(asyncio.CancelledError, asyncio.wait_for(task, 3))
    assert pending.cancelled() and fixture.wire.closed
    assert fixture.budget.status(222).used == 0
    assert 'GetHistoryRequest' not in fixture.wire.calls
    return dict(cancelled=True, claims=0, history_sends=0, close_attempts=fixture.wire.close_calls)


async def reversed_initial_proofs():
    fixture = f.Fixture(accounts=(222, 333), cached=111)
    pending = [asyncio.get_running_loop().create_future() for _ in range(2)]
    body = [asyncio.Event(), asyncio.Event()]
    release = asyncio.Event()
    order = []
    original = fixture.engine._new_client

    def factory(*args, **kwargs):
        client = original(*args, **kwargs)
        client._sender.script['GetUsersRequest'] = [pending[len(fixture.clients)-1]]
        return client
    fixture.engine._new_client = factory

    async def worker(index, account):
        async with fixture.engine._account_operation(account) as op:
            assert op.account_id == account and op.client._self_id == 111
            order.append(account)
            body[index].set()
            await release.wait()
    tasks = [asyncio.create_task(worker(0, 222)), asyncio.create_task(worker(1, 333))]
    await until(lambda: len(fixture.clients) == 2 and all(
        'GetUsersRequest' in c._sender.calls for c in fixture.clients))
    assert not any(t.done() for t in tasks)
    pending[1].set_result([f.user(333)])
    await asyncio.wait_for(body[1].wait(), 3)
    assert not body[0].is_set()
    pending[0].set_result([f.user(222)])
    await asyncio.wait_for(body[0].wait(), 3)
    release.set()
    await asyncio.wait_for(asyncio.gather(*tasks), 3)
    assert order == [333, 222] and all(c._sender.closed for c in fixture.clients)
    return dict(opened=[222, 333], verified_order=order, owners_correct=True, closed_clients=2)


async def session_close_failures():
    records = []
    outcomes = []
    marker = 'synthetic-credential-marker-never-log'

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record)
    capture = Capture()
    owned.logger.addHandler(capture)
    try:
        for cleanup_type in (OSError, asyncio.CancelledError):
            for fail_work in (False, True):
                fixture = f.Fixture(store=None)
                original_close = None
                primary = errors.ChannelPrivateError(None)
                closes = []

                async def worker():
                    nonlocal original_close
                    async with fixture.engine._account_operation(222) as op:
                        original_close = op.client.session.close

                        async def failed_close():
                            assert fixture.wire.closed
                            original_close()
                            closes.append('session closed')
                            raise cleanup_type(marker)
                        op.client.session.close = failed_close
                        if fail_work:
                            raise primary
                        return 'work-result'
                try:
                    if fail_work:
                        assert await f.expect(errors.ChannelPrivateError, worker()) is primary
                    else:
                        assert await worker() == 'work-result'
                    assert closes == ['session closed'] and fixture.wire.close_calls == 1
                    assert fixture.clients[0].session._conn is None
                    assert fixture.clients[0]._updates_handle.done()
                    assert fixture.clients[0]._keepalive_handle.done()
                    outcomes.append([cleanup_type.__name__, 'primary error' if fail_work else 'success'])
                finally:
                    if original_close is not None:
                        fixture.clients[0].session.close = original_close
        assert len(records) == 4
        assert all(marker not in r.getMessage() and r.exc_info is None for r in records)
        return dict(preserved=outcomes, sanitized_error_logs=4, sdk_background_tasks_finished=True)
    finally:
        owned.logger.removeHandler(capture)


async def cancel_over_primary_and_failed_close():
    fixture = f.Fixture()

    async def worker():
        async with fixture.engine._account_operation(222):
            fixture.wire.close_release = asyncio.Event()
            fixture.wire.close_error = OSError('synthetic secondary close failure')
            raise ValueError('synthetic primary work failure')
    task = asyncio.create_task(worker())
    await until(lambda: fixture.clients and fixture.wire.close_entered.is_set())
    for _ in range(2):
        task.cancel()
        await f.turns()
        assert not task.done()
    fixture.wire.close_release.set()
    await f.expect(asyncio.CancelledError, asyncio.wait_for(task, 3))
    assert task.cancelled() and fixture.wire.close_calls == 1
    return dict(outcome='CancelledError', close_attempts=1, detached_close=False)


async def preconstruction_failures():
    class BrokenStore:
        def load(self, name):
            raise OSError('synthetic store unavailable')
    missing = f.Fixture(store=BrokenStore())
    error = await f.expect(OSError, f.enter(missing))
    assert str(error) == 'synthetic store unavailable' and not missing.clients
    corrupt = f.Fixture()
    corrupt.store[corrupt.name] = 'synthetic corrupt snapshot'
    await f.expect(ValueError, f.enter(corrupt))
    assert not corrupt.clients
    proxy = f.Fixture()
    proxy.config.write_text(proxy.config.read_text() + 'require_proxy=true\n')
    await f.expect(ProxyConfigError, f.enter(proxy))
    assert not proxy.clients
    return dict(store_load='OSError', corrupt_snapshot='ValueError', proxy='ProxyConfigError', built_clients=0)


async def successful_iterator():
    fixture = f.Fixture(cached=111, budget=True)
    fixture.responses['GetHistoryRequest'] = types.messages.Messages(
        messages=[types.Message(id=101, peer_id=types.PeerChannel(7), date=f.DATE, message='synthetic')],
        topics=[], chats=[], users=[])
    async with fixture.engine._account_operation(222) as op:
        result = await op.client.get_messages(types.InputPeerChannel(7, 7), limit=1)
        assert [m.id for m in result] == [101]
    assert fixture.budget.status(111).used == 0 and fixture.budget.status(222).used == 1
    return dict(message_ids=[101], billed_account=222, billed=1, cached_account=111)


async def bootstrap_self_shapes():
    observed = []
    for label, reply in (('None', None), ('empty list', []), ('UserEmpty', [types.UserEmpty(222)])):
        fixture = f.Fixture(responses={'GetUsersRequest': reply})
        reached = False
        try:
            async with fixture.engine._account_operation(222):
                reached = True
        except Exception as error:
            result = type(error).__name__
        else:
            result = 'no exception'
        assert not reached and fixture.wire.closed and fixture.wire.close_calls == 1
        observed.append(dict(reply=label, exception=result, body_entered=False, closed=True))
    return observed


async def main():
    probes = [delayed_resolution, cancel_admission, reversed_initial_proofs,
              session_close_failures, cancel_over_primary_and_failed_close,
              preconstruction_failures, successful_iterator, bootstrap_self_shapes]
    with tempfile.TemporaryDirectory(prefix='tgdata_pr21_') as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        f.TMP = Path(tmp)
        for probe in probes:
            try:
                result = await asyncio.wait_for(probe(), 15)
                print(json.dumps(dict(probe=probe.__name__, observed=result)), flush=True)
            finally:
                for client in f.CLIENTS:
                    client._sender.close_error = None
                    if client._sender.close_release is not None:
                        client._sender.close_release.set()
                    await client.disconnect()
                f.CLIENTS.clear()


if __name__ == '__main__':
    asyncio.run(main())
