"""Real Telethon 1.45 composition; synthetic replies, forbidden sockets."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import socket
import sys
import tempfile
from types import MethodType
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from telethon import TelegramClient, errors
from telethon.crypto import AuthKey
from telethon.tl import functions, types
from tgdata.connection_engine import ConnectionEngine
from tgdata import ReadBudget
import tgdata.connection_engine as ce

POLICY = dict(flood_sleep_threshold=0, request_retries=0, connection_retries=0,
              retry_delay=0, auto_reconnect=False, raise_last_call_error=True,
              receive_updates=False)
DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)


class Store(dict):
    def load(self, name):
        return self.get(name)

    def save(self, name, value):
        self[name] = value


class PolicyClient(TelegramClient):
    def __init__(self, *args, **kwargs):
        kwargs.update(POLICY)
        super().__init__(*args, **kwargs)


class Wire:
    def __init__(self, auth_error=None):
        self.auth_key = AuthKey(bytes(range(256)))
        self.disconnected = asyncio.get_running_loop().create_future()
        self.up = False
        self.calls = []
        self.auth_error = auth_error
        self.entered = asyncio.Event()
        self.release = None
        self.closed = False

    async def connect(self, connection):
        self.up = True
        return True

    def is_connected(self):
        return self.up

    async def disconnect(self):
        self.entered.set()
        if self.release is not None:
            await self.release.wait()
        self.up = False
        self.closed = True
        if not self.disconnected.done():
            self.disconnected.set_result(None)

    def send(self, request, ordered=False):
        while hasattr(request, 'query'):
            request = request.query
        self.calls.append(type(request).__name__)
        if isinstance(request, functions.help.GetConfigRequest):
            result = None
        elif isinstance(request, functions.users.GetUsersRequest):
            result = [types.User(id=222, is_self=True, access_hash=222)]
        elif isinstance(request, functions.updates.GetStateRequest):
            result = self.auth_error or types.updates.State(1, 1, DATE, 1, 0)
        elif isinstance(request, functions.updates.GetDifferenceRequest):
            result = types.updates.DifferenceEmpty(DATE, 1)
        else:
            raise AssertionError('Unexpected send: ' + type(request).__name__)
        future = asyncio.get_running_loop().create_future()
        if isinstance(result, BaseException):
            future.set_exception(result)
        else:
            future.set_result(result)
        return future


async def main(root):
    config = root / 'config.ini'
    config.write_text('[Telegram]\napi_id=1\napi_hash=synthetic\n'
                      'session_file=probe\ndevice_model=Stage1Probe\n')
    engine = ConnectionEngine(str(config), session_store=Store())
    budget = ReadBudget(root / 'budget.sqlite3')
    budget.configure(111, 20)
    budget.configure(222, 20)
    engine.read_budget = budget
    original_sleep = asyncio.sleep
    sleeps = []

    async def record_sleep(seconds):
        sleeps.append(seconds)
        await original_sleep(0)

    def client(error=None):
        with patch.object(ce, 'TelegramClient', PolicyClient):
            result = engine._new_client()
        result._sender = Wire(error)
        assert result._request_retries == 0
        assert result.flood_sleep_threshold == 0
        assert result._init_request.device_model == 'Stage1Probe'
        return result

    c = client()
    try:
        await c.connect()
        assert await engine._authorization_problem(c) is None
        c._mb_entity_cache.set_self_user(111, False, 111)
        actual = (await c(functions.users.GetUsersRequest([types.InputUserSelf()])))[0].id
        assert actual == 222 and c._self_id == 111
        print('PASS real connect + fresh self: actual222, cache111')

        async def owned_identity(self):
            actual = (await self(functions.users.GetUsersRequest([types.InputUserSelf()])))[0].id
            if actual != 111:
                raise RuntimeError('owned account mismatch')
            return actual

        c._read_budget_account = MethodType(owned_identity, c)
        request = functions.messages.GetHistoryRequest(types.InputPeerChannel(7, 7),
                                                       0, None, 0, 1, 0, 0, 0)
        try:
            await c(request)
        except RuntimeError as exc:
            assert str(exc) == 'owned account mismatch'
        else:
            raise AssertionError('read admitted')
        assert 'GetHistoryRequest' not in c._sender.calls
        assert budget.status(111).used == budget.status(222).used == 0
        print('PASS real SDK + SQLite admission: no claim or history send')
    finally:
        await c.disconnect()

    for error in (errors.FloodWaitError(None, capture=30),
                  errors.ServerError(None, 'synthetic server failure', 500)):
        c = client(error)
        sleeps.clear()
        try:
            with patch('telethon.client.users.asyncio.sleep', record_sleep):
                try:
                    await c.connect()
                except type(error) as observed:
                    assert observed is error
                else:
                    raise AssertionError('auth failure hidden')
            assert c._sender.calls.count('GetStateRequest') == 1
            assert sleeps == ([] if isinstance(error, errors.FloodWaitError) else [2])
            print('PASS constructor policy during connect:', type(error).__name__, 'sleeps', sleeps)
        finally:
            await c.disconnect()

    c = client()
    await c.connect()
    c._sender.release = asyncio.Event()

    async def close_owner():
        async def close():
            try:
                await c.disconnect()
            except (Exception, asyncio.CancelledError) as exc:
                return type(exc).__name__
        completion = asyncio.ensure_future(close())
        cancelled = None
        while not completion.done():
            try:
                await asyncio.shield(completion)
            except asyncio.CancelledError as exc:
                cancelled = exc
        assert completion.result() is None
        if cancelled is not None:
            raise cancelled

    task = asyncio.create_task(close_owner())
    await asyncio.wait_for(c._sender.entered.wait(), 2)
    for _ in range(2):
        task.cancel()
        for _ in range(3):
            await original_sleep(0)
        assert not task.done() and not c._sender.closed
    c._sender.release.set()
    try:
        await asyncio.wait_for(task, 2)
    except asyncio.CancelledError:
        pass
    else:
        raise AssertionError('cancellation lost')
    assert c._sender.closed
    assert c._updates_handle.done() and c._keepalive_handle.done()
    print('PASS actual SDK disconnect: repeated cancellation retained until close completed')


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp, patch.object(
            socket.socket, 'connect', side_effect=AssertionError('network forbidden')):
        asyncio.run(main(Path(tmp)))
