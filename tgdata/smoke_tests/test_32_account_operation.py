"""Owned-operation contract on real Telethon 1.45, with synthetic wire replies.

No config/account from the project is read and sockets are forbidden. These
tests run actual connect, request dispatch, budget admission and disconnect.
"""
import asyncio
from datetime import datetime, timezone
import itertools
import logging
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import telethon
from telethon import TelegramClient, errors
from telethon.crypto import AuthKey
from telethon._updates import SessionState
from telethon.sessions import SQLiteSession
from telethon.tl import functions, types

from tgdata import AuthRequiredError, ReadBudget
from tgdata.account_operation import AccountIdentityError
from tgdata.connection_engine import ConnectionEngine
from tgdata.session_store import StoredSession
import tgdata.account_operation as owned


TMP = None
CLIENTS = []
NUMBERS = itertools.count(1)
DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)
KEY = bytes(range(256))
DEFAULT = object()


class Store(dict):
    def load(self, name):
        return self.get(name)

    def save(self, name, value):
        self[name] = value


def user(account):
    return types.User(id=account, is_self=True, access_hash=account)


def history():
    return functions.messages.GetHistoryRequest(types.InputPeerChannel(7, 7),
                                               0, None, 0, 1, 0, 0, 0)


class Wire:
    def __init__(self, client, fixture):
        self.client, self.fixture = client, fixture
        self.account = fixture.accounts.pop(0) if fixture.accounts else 222
        self.auth_key = AuthKey(KEY)
        self.disconnected = asyncio.get_running_loop().create_future()
        self.up = False
        self.calls = []
        self.script = {}
        self.close_calls = 0
        self.close_entered = asyncio.Event()
        self.close_release = None
        self.close_error = None
        self.closed = False

    async def connect(self, connection):
        c = self.client
        self.policy_at_connect = dict(
            flood=c.flood_sleep_threshold, requests=c._request_retries,
            connections=c._connection_retries, delay=c._retry_delay,
            reconnect=c._auto_reconnect, last_error=c._raise_last_call_error,
            updates=not c._no_updates)
        self.proxy_at_connect = connection._proxy
        if self.fixture.connect_error is not None:
            raise self.fixture.connect_error
        self.up = True
        return True

    def is_connected(self):
        return self.up

    async def disconnect(self):
        self.close_calls += 1
        self.close_entered.set()
        if self.close_release is not None:
            await self.close_release.wait()
        if self.close_error is not None:
            raise self.close_error
        self.up = False
        self.closed = True
        if not self.disconnected.done():
            self.disconnected.set_result(None)

    def send(self, request, ordered=False):
        while hasattr(request, 'query'):
            request = request.query
        name = type(request).__name__
        self.calls.append(name)
        if self.script.get(name):
            result = self.script[name].pop(0)
        elif name in self.fixture.responses:
            result = self.fixture.responses[name]
        elif isinstance(request, functions.help.GetConfigRequest):
            result = None
        elif isinstance(request, functions.users.GetUsersRequest):
            result = [user(self.account)]
        elif isinstance(request, functions.updates.GetStateRequest):
            result = types.updates.State(1, 1, DATE, 1, 0)
        elif isinstance(request, functions.updates.GetDifferenceRequest):
            result = types.updates.DifferenceEmpty(DATE, 1)
        elif isinstance(request, functions.messages.GetHistoryRequest):
            result = types.messages.Messages(
                messages=[types.MessageEmpty(id=1, peer_id=types.PeerChannel(7))],
                topics=[], chats=[], users=[])
        else:
            raise AssertionError('Unexpected request: ' + name)
        if isinstance(result, asyncio.Future):
            return result
        future = asyncio.get_running_loop().create_future()
        if isinstance(result, BaseException):
            future.set_exception(result)
        else:
            future.set_result(result)
        return future


class Fixture:
    def __init__(self, *, accounts=(), cached=None, logged_in=True, budget=False,
                 store=DEFAULT, proxy=False, connect_error=None, responses=None):
        self.root = TMP / str(next(NUMBERS))
        self.root.mkdir()
        self.accounts = list(accounts)
        self.cached = cached
        self.logged_in = logged_in
        self.connect_error = connect_error
        self.responses = responses or {}
        self.clients = []
        self.store = Store() if store is DEFAULT else store
        self.budget = ReadBudget(self.root / 'budget.sqlite3') if budget else None
        if self.budget is not None:
            for account in (111, 222, 333):
                self.budget.configure(account, 20)
        self.config = self.root / 'config.ini'
        self.name = str(self.root / 'synthetic_session')
        self.config.write_text(
            '[Telegram]\napi_id=12345\napi_hash=synthetic\n'
            'session_file={}\ndevice_model=Stage 1 device\n'
            'system_version=synthetic OS\napp_version=1.0\n'
            'lang_code=en\nsystem_lang_code=en-GB\n{}'.format(
                self.name, 'proxy=socks5://alice:synthetic-secret@127.0.0.1:9090\n'
                'require_proxy=true\n' if proxy else ''))
        fixture = self

        class Engine(ConnectionEngine):
            def _new_client(self, session_file=None, **options):
                client = super()._new_client(session_file, **options)
                if fixture.logged_in:
                    client.session.auth_key = AuthKey(KEY)
                    client.session.save()
                client._sender = Wire(client, fixture)
                if fixture.cached is not None:
                    # A previously populated message box avoids connect's
                    # own fresh _on_login. The actual self RPC must still win.
                    client._mb_entity_cache.set_self_user(fixture.cached, False, fixture.cached)
                    client._message_box.load(SessionState(
                        0, 0, False, 1, 1, int(DATE.timestamp()), 1, None), [])
                fixture.clients.append(client)
                CLIENTS.append(client)
                return client

        self.engine = Engine(str(self.config), pool_size=3, interactive_login=True,
                             session_store=self.store, read_budget=self.budget)

    @property
    def wire(self):
        return self.clients[-1]._sender


async def expect(kind, awaitable):
    try:
        await awaitable
    except kind as error:
        return error
    raise AssertionError('Expected ' + kind.__name__)


def refuses(kind, action):
    try:
        action()
    except kind as error:
        return error
    raise AssertionError('Expected ' + kind.__name__)


async def enter(fixture, expected=222):
    async with fixture.engine._account_operation(expected):
        raise AssertionError('Operation body should not run')


async def turns(count=3):
    for _ in range(count):
        await asyncio.sleep(0)


async def test_expected_b_cached_a_actual_b():
    f = Fixture(cached=111)
    async with f.engine._account_operation(222) as op:
        assert op.account_id == 222 and op.client._self_id == 111
        assert await op.verify_account() == 222
        refuses(AttributeError, lambda: setattr(op, 'account_id', 111))
        refuses(AttributeError, lambda: setattr(op, 'client', None))
        assert f.engine._primary_client is None and f.engine._pool is None
    assert f.wire.closed and f.wire.close_calls == 1


async def test_expected_a_actual_b_never_yields():
    f = Fixture(cached=111)
    error = await expect(AccountIdentityError, enter(f, 111))
    assert (error.expected_account_id, error.actual_account_id) == (111, 222)
    assert set(f.wire.calls) <= {'GetConfigRequest', 'GetStateRequest', 'GetUsersRequest'}
    assert f.wire.close_calls == 1 and f.wire.closed


async def test_invalid_expectations_precede_construction():
    f = Fixture()
    for value in (True, False, 0, -1, 222.0, '222', None, object()):
        await expect(ValueError, enter(f, value))
    assert not f.clients and not f.store


async def test_policy_and_configuration_precede_connect():
    f = Fixture(proxy=True, budget=True)
    async with f.engine._account_operation(222) as op:
        c = op.client
        assert f.wire.policy_at_connect == dict(flood=0, requests=0, connections=0,
            delay=0, reconnect=False, last_error=True, updates=False)
        assert f.wire.proxy_at_connect == c._proxy == f.engine._load_config().proxy
        assert c._init_request.device_model == 'Stage 1 device'
        assert c._init_request.system_version == 'synthetic OS'
        assert c._init_request.app_version == '1.0'
        assert c._init_request.lang_code == 'en'
        assert c._init_request.system_lang_code == 'en-GB'
        assert isinstance(c.session, StoredSession) and c._tgdata_read_budget is f.budget
    assert f.name in f.store and not list(f.root.glob('*.session'))


async def test_file_sessions_and_ordinary_defaults():
    f = Fixture(store=None)
    async with f.engine._account_operation(222) as op:
        assert isinstance(op.client.session, SQLiteSession)
    assert Path(f.name + '.session').exists()
    assert f.clients[0].session._conn is None
    ordinary = f.engine._new_client()
    assert ordinary._request_retries == ordinary._connection_retries == 5
    assert ordinary.flood_sleep_threshold == 60 and ordinary._auto_reconnect
    assert not ordinary._raise_last_call_error and not ordinary._no_updates
    assert not hasattr(ordinary, '_tgdata_account_operation')
    async with f.engine.ephemeral_client() as client:
        assert client._request_retries == 5 and client.flood_sleep_threshold == 60
        assert not hasattr(client, '_tgdata_account_operation')


async def test_empty_session_is_noninteractive():
    auth = errors.AuthKeyUnregisteredError(None)
    f = Fixture(logged_in=False, responses={'GetUsersRequest': auth, 'GetStateRequest': auth})
    with patch.object(TelegramClient, 'start', side_effect=AssertionError('start forbidden')), \
         patch.object(TelegramClient, 'send_code_request', side_effect=AssertionError('code forbidden')), \
         patch('builtins.input', side_effect=AssertionError('prompt forbidden')):
        error = await expect(AuthRequiredError, enter(f))
    assert error.first_login and error.reason == 'AUTH_KEY_UNREGISTERED'
    assert error.__cause__ is auth and 'separately' in str(error)
    assert f.wire.closed and f.wire.close_calls == 1


async def test_revoked_and_banned_sessions_keep_reason():
    for cls, banned in ((errors.SessionRevokedError, False), (errors.UserDeactivatedBanError, True)):
        auth = cls(None)
        f = Fixture(responses={'GetStateRequest': auth})
        error = await expect(AuthRequiredError, enter(f))
        assert error.__cause__ is auth and error.banned == banned and not error.first_login
        assert f.wire.closed


async def test_auth_failure_during_transport_connect():
    auth = errors.AuthKeyUnregisteredError(None)
    f = Fixture(connect_error=auth)
    error = await expect(AuthRequiredError, enter(f))
    assert error.__cause__ is auth and not f.wire.calls
    assert f.wire.closed and f.wire.close_calls == 1


async def test_connect_flood_wait_never_sleeps():
    wait = errors.FloodWaitError(None, capture=30)
    f = Fixture(responses={'GetStateRequest': wait})
    with patch('telethon.client.users.asyncio.sleep', side_effect=AssertionError('sleep forbidden')):
        assert await expect(errors.FloodWaitError, enter(f)) is wait
    assert f.wire.calls.count('GetStateRequest') == 1 and f.wire.closed


async def test_server_failure_is_original_and_not_retried():
    failure = errors.ServerError(None, 'synthetic server failure', 500)
    f = Fixture(responses={'GetStateRequest': failure})
    sleeps = []
    original_sleep = asyncio.sleep

    async def record(seconds):
        sleeps.append(seconds)
        await original_sleep(0)

    with patch('telethon.client.users.asyncio.sleep', record):
        assert await expect(errors.ServerError, enter(f)) is failure
    assert sleeps == [2]  # SDK backoff still occurs even after its final attempt.
    assert f.wire.calls.count('GetStateRequest') == 1 and f.wire.closed


async def test_transport_error_keeps_identity_and_closes():
    failure = OSError('synthetic transport failed')
    f = Fixture(connect_error=failure)
    assert await expect(OSError, enter(f)) is failure
    assert f.wire.closed and f.wire.close_calls == 1


async def test_missing_self_is_explicit_auth_failure():
    for reply in (None, [], [types.UserEmpty(222)]):
        f = Fixture(cached=111, responses={'GetUsersRequest': reply})
        error = await expect(AuthRequiredError, enter(f))
        assert error.reason is None and f.wire.closed


async def test_malformed_self_is_unverifiable_not_a_new_owner():
    for reply in ({'id': 222}, [user(222), user(333)], [types.ChatEmpty(222)],
                  [user(True)], [user(0)], [user('222')]):
        f = Fixture(cached=111, responses={'GetUsersRequest': reply})
        error = await expect(AccountIdentityError, enter(f))
        assert error.actual_account_id is None and f.wire.closed


async def test_budget_charges_verified_b_despite_cache_a():
    f = Fixture(cached=111, budget=True)
    async with f.engine._account_operation(222) as op:
        await op.client(history())
        assert op.client._self_id == 111
    assert f.budget.status(222).used == 1 and f.budget.status(111).used == 0


async def test_late_mismatch_is_terminal_before_claim_send():
    f = Fixture(budget=True)
    async with f.engine._account_operation(222) as op:
        client = op.client
        f.wire.account = 333
        error = await expect(AccountIdentityError, client(history()))
        assert error.actual_account_id == 333
        f.wire.account = 222
        refuses(RuntimeError, lambda: op.client)
        await expect(RuntimeError, op.verify_account())
        await expect(RuntimeError, client(history()))
    assert 'GetHistoryRequest' not in f.wire.calls
    assert all(f.budget.status(a).used == 0 for a in (111, 222, 333))
    assert f.wire.close_calls == 1


async def test_late_auth_loss_and_missing_proof_are_terminal():
    for reply in (errors.SessionRevokedError(None), [], [user(0)]):
        f = Fixture(budget=True)
        async with f.engine._account_operation(222) as op:
            client = op.client
            f.wire.script['GetUsersRequest'] = [reply]
            expected = AuthRequiredError
            if isinstance(reply, list) and reply and reply[0].id == 0:
                expected = AccountIdentityError
            await expect(expected, client(history()))
            await expect(RuntimeError, client(history()))
            refuses(RuntimeError, lambda: op.client)
        assert f.budget.status(222).used == 0 and 'GetHistoryRequest' not in f.wire.calls


async def test_iterator_admission_refuses_changed_account():
    f = Fixture(budget=True)
    async with f.engine._account_operation(222) as op:
        f.wire.account = 333
        await expect(AccountIdentityError, op.client.get_messages(types.InputPeerChannel(7, 7), limit=1))
    assert 'GetHistoryRequest' not in f.wire.calls
    assert f.budget.status(222).used == f.budget.status(333).used == 0


async def test_transient_proof_error_does_not_rebind_owner():
    f = Fixture(budget=True)
    async with f.engine._account_operation(222) as op:
        wait = errors.FloodWaitError(None, capture=30)
        f.wire.script['GetUsersRequest'] = [wait]
        assert await expect(errors.FloodWaitError, op.client(history())) is wait
        assert op.account_id == 222
    assert f.budget.status(222).used == 0 and 'GetHistoryRequest' not in f.wire.calls


async def test_closed_and_foreign_task_handles_refuse():
    f = Fixture(budget=True)
    async with f.engine._account_operation(222) as op:
        client = op.client
        before = len(f.wire.calls)
        task = asyncio.create_task(op.verify_account())
        error = await expect(RuntimeError, task)
        assert 'opening task' in str(error) and len(f.wire.calls) == before
        assert await op.verify_account() == 222
    refuses(RuntimeError, lambda: op.client)
    await expect(RuntimeError, op.verify_account())
    await expect(RuntimeError, client(history()))
    assert op.account_id == 222 and f.budget.status(222).used == 0


async def test_active_check_repeats_after_proof_await():
    f = Fixture()
    held = {}
    ready = asyncio.Event()

    async def worker():
        async with f.engine._account_operation(222) as op:
            held['op'] = op
            pending = asyncio.get_running_loop().create_future()
            held['pending'] = pending
            f.wire.script['GetUsersRequest'] = [pending]
            ready.set()
            await expect(RuntimeError, op.verify_account())

    task = asyncio.create_task(worker())
    await asyncio.wait_for(ready.wait(), 2)
    held['op']._close()
    held['pending'].set_result([user(222)])
    await asyncio.wait_for(task, 2)
    assert f.wire.closed


async def test_two_operations_really_overlap_without_owner_leak():
    f = Fixture(accounts=(222, 333), budget=True)
    ready = [asyncio.Event(), asyncio.Event()]
    release = asyncio.Event()
    ids = []

    async def worker(index, account):
        async with f.engine._account_operation(account) as op:
            ready[index].set()
            await release.wait()
            assert op.account_id == await op.verify_account() == account
            await op.client(history())
            ids.append((account, id(op.client)))

    tasks = [asyncio.create_task(worker(0, 222)), asyncio.create_task(worker(1, 333))]
    await asyncio.wait_for(asyncio.gather(*(e.wait() for e in ready)), 2)
    assert len(f.clients) == 2 and all(c.is_connected() for c in f.clients)
    assert all(not t.done() for t in tasks)
    release.set()
    await asyncio.wait_for(asyncio.gather(*tasks), 2)
    assert len({client for _, client in ids}) == 2
    assert f.budget.status(222).used == f.budget.status(333).used == 1
    assert all(c._sender.closed and c._sender.close_calls == 1 for c in f.clients)


async def test_primary_body_exception_is_unchanged():
    f = Fixture()
    failure = errors.ChannelPrivateError(None)

    async def worker():
        async with f.engine._account_operation(222):
            raise failure

    assert await expect(errors.ChannelPrivateError, worker()) is failure
    assert f.wire.closed and f.wire.close_calls == 1


async def test_cleanup_error_preserves_success_and_primary_error():
    secret = 'synthetic-login-key-must-never-appear'
    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = Capture()
    owned.logger.addHandler(handler)
    try:
        for failure in (None, ValueError('primary work failure')):
            f = Fixture()

            async def worker():
                async with f.engine._account_operation(222):
                    f.wire.close_error = OSError(secret)
                    if failure is not None:
                        raise failure
                    return 42

            if failure is None:
                assert await worker() == 42
            else:
                assert await expect(ValueError, worker()) is failure
            assert f.wire.close_calls == 1
        assert len(records) == 2
        assert all(r.levelno == logging.ERROR and r.exc_info is None for r in records)
        assert all('OSError' in r.getMessage() and secret not in r.getMessage() for r in records)
    finally:
        owned.logger.removeHandler(handler)


async def test_cleanup_internal_cancel_and_broken_logger_preserve_success():
    f = Fixture()
    with patch.object(owned.logger, 'error', side_effect=RuntimeError('logger broke')):
        async with f.engine._account_operation(222):
            f.wire.close_error = asyncio.CancelledError('internal teardown cancelled')
    assert f.wire.close_calls == 1


async def test_cancelled_body_waits_for_actual_sdk_disconnect():
    f = Fixture()
    ready = asyncio.Event()

    async def worker():
        async with f.engine._account_operation(222):
            f.wire.close_release = asyncio.Event()
            ready.set()
            await asyncio.Event().wait()

    task = asyncio.create_task(worker())
    await asyncio.wait_for(ready.wait(), 2)
    task.cancel()
    await asyncio.wait_for(f.wire.close_entered.wait(), 2)
    task.cancel()
    await turns()
    assert not task.done() and not f.wire.closed
    f.wire.close_release.set()
    await expect(asyncio.CancelledError, asyncio.wait_for(task, 2))
    assert f.wire.closed and f.wire.close_calls == 1
    assert f.clients[0]._updates_handle.done() and f.clients[0]._keepalive_handle.done()


async def test_cancellation_during_authentication_closes_client():
    pending = asyncio.get_running_loop().create_future()
    f = Fixture(responses={'GetStateRequest': pending})
    task = asyncio.create_task(enter(f))
    while not f.clients or 'GetStateRequest' not in f.wire.calls:
        await asyncio.sleep(0)
    task.cancel()
    await expect(asyncio.CancelledError, asyncio.wait_for(task, 2))
    assert f.wire.closed and f.wire.close_calls == 1


async def test_cancellation_during_successful_cleanup_is_preserved():
    f = Fixture()

    async def worker():
        async with f.engine._account_operation(222):
            f.wire.close_release = asyncio.Event()
            return 42

    task = asyncio.create_task(worker())
    while not f.clients:
        await asyncio.sleep(0)
    await asyncio.wait_for(f.wire.close_entered.wait(), 2)
    for _ in range(2):
        task.cancel()
        await turns()
        assert not task.done()
    f.wire.close_release.set()
    await expect(asyncio.CancelledError, asyncio.wait_for(task, 2))
    assert f.wire.closed and f.wire.close_calls == 1


async def test_cancelled_body_survives_failed_cleanup():
    f = Fixture()
    ready = asyncio.Event()

    async def worker():
        async with f.engine._account_operation(222):
            f.wire.close_error = OSError('secondary close failure')
            ready.set()
            await asyncio.Event().wait()

    task = asyncio.create_task(worker())
    await asyncio.wait_for(ready.wait(), 2)
    task.cancel()
    await expect(asyncio.CancelledError, asyncio.wait_for(task, 2))
    assert f.wire.close_calls == 1


async def main():
    assert telethon.__version__ == '1.45.0'
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    passed = 0
    with tempfile.TemporaryDirectory(prefix='tgdata_account_operation_') as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        global TMP
        TMP = Path(tmp)
        for test in tests:
            print('TEST:', test.__name__, flush=True)
            try:
                await asyncio.wait_for(test(), 15)
            except (Exception, asyncio.CancelledError):
                traceback.print_exc()
            else:
                passed += 1
            finally:
                # Fault-injected failed disconnects deliberately leave SDK
                # resources; retire those fixtures after asserting the outcome.
                for client in CLIENTS:
                    client._sender.close_error = None
                    if client._sender.close_release is not None:
                        client._sender.close_release.set()
                    await client.disconnect()
                CLIENTS.clear()
    print('Passed: {}/{}'.format(passed, len(tests)))
    return 0 if passed == len(tests) else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
