"""Offline session-store checks against Telethon 1.45.0.

Run: python -m tgdata.smoke_tests.test_17_session_store

All credentials are synthetic. Telethon's constructor, request handling,
disconnect and log-out run for real; login responses use a stand-in, and socket
connections are forbidden. No existing config or session file is opened.
"""

import asyncio
import base64
import datetime
import json
import logging
import os
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from contextlib import contextmanager
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import telethon
from telethon import TelegramClient, errors
from telethon.crypto import AuthKey
from telethon.sessions import MemorySession, SQLiteSession
from telethon.tl import types
from telethon.tl.functions.updates import GetStateRequest

import tgdata.connection_engine as ce
from tgdata import AuthRequiredError, TgData
from tgdata.session_store import StoredSession


KEY = bytes(range(256))
OTHER_KEY = bytes(reversed(range(256)))
DATE = datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc)
SELF_ID = 4242
ACCESS_HASH = -2255621593168970683  # deliberately outside exact float precision
TMP = None
CLIENTS = []
_ini_no = 0


class Store(dict):
    """Also falsey when empty: an empty store is still a configured store."""

    def __init__(self):
        super().__init__()
        self.loads, self.saves, self.deletes = [], [], []
        self.load_error = self.save_error = self.delete_error = None

    def load(self, name):
        self.loads.append(name)
        if self.load_error is not None:
            raise self.load_error
        return self.get(name)

    def save(self, name, data):
        self.saves.append((name, data))
        if self.save_error is not None:
            raise self.save_error
        self[name] = data

    def delete(self, name):
        self.deletes.append(name)
        if self.delete_error is not None:
            raise self.delete_error
        self.pop(name, None)


class Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@contextmanager
def captured():
    logger = logging.getLogger('tgdata.session_store')
    handler, before = Capture(), logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield handler.records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(before)


def config(name=None):
    global _ini_no
    _ini_no += 1
    name = name or str(TMP / f'account_{_ini_no}')
    path = TMP / f'c{_ini_no}.ini'
    path.write_text(
        '[Telegram]\napi_id = 12345\n'
        'api_hash = 0123456789abcdef0123456789abcdef\n'
        f'session_file = {name}\n', encoding='utf-8')
    return str(path), name


def client_for(store=None, name=None):
    ini, name = config(name)
    client = ce.ConnectionEngine(ini, session_store=store)._new_client()
    CLIENTS.append(client)
    return client, name


def room(ident=1234567, username='SomeRoom'):
    return types.Channel(id=ident, title='Room', photo=types.ChatPhotoEmpty(),
                         date=DATE, access_hash=ACCESS_HASH, username=username,
                         megagroup=True)


def add_room(session, ident=1234567, username='SomeRoom'):
    session.process_entities(types.contacts.ResolvedPeer(None, [room(ident, username)], []))


def seed(store, name, key=KEY):
    session = StoredSession(store, name)
    session.set_dc(2, '149.154.167.51', 443)
    session.auth_key = AuthKey(key)
    session.save()
    return session


class Scripted:
    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []

    def send(self, request, ordered=False):
        self.sent.append(type(request).__name__)
        reply = self.replies.pop(0)
        future = asyncio.get_running_loop().create_future()
        if isinstance(reply, BaseException):
            future.set_exception(reply)
        else:
            future.set_result(reply)
        return future

    async def disconnect(self):
        pass

    def is_connected(self):
        return False


def state():
    return types.updates.State(pts=10, qts=2, date=DATE, seq=3, unread_count=4)


@contextmanager
def login_clients(replies, terminal=False):
    """Exercise tgdata's login decisions without contacting Telegram."""
    built = []
    pending = iter(replies)

    class LoginClient(TelegramClient):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.starts = self.codes = 0
            self.up = False
            self._sender = Scripted(next(pending))
            built.append(self)
            CLIENTS.append(self)

        async def connect(self):
            if self.session.auth_key is None:
                self.session.auth_key = AuthKey(KEY)
            self.up = True

        def is_connected(self):
            return self.up

        async def disconnect(self):
            self.up = False
            await super().disconnect()

        async def start(self, *args, **kwargs):
            self.starts += 1
            self.session.auth_key = AuthKey(OTHER_KEY)
            return self

        async def send_code_request(self, *args, **kwargs):
            self.codes += 1
            raise AssertionError('a login code was requested')

    with patch.object(ce, 'TelegramClient', LoginClient), \
            patch.object(ce, '_human_at_terminal', return_value=terminal):
        yield built


async def test_file_default():
    client, name = client_for()
    assert type(client.session) is SQLiteSession
    assert client.session.filename == name + '.session'
    assert Path(name + '.session').is_file()
    await client.disconnect()


async def test_every_connection_path():
    store = Store()
    ini, name = config()
    files_before = set(TMP.rglob('*.session'))
    with login_clients([[state()] for _ in range(4)]) as built:
        tg = TgData(ini, connection_pool_size=3, session_store=store)
        assert tg.connection_engine.session_store is store
        await tg.connection_engine.get_client()
        async with tg.connection_engine.ephemeral_client() as ephemeral:
            assert type(ephemeral.session) is StoredSession
        assert len(built) == 4
        assert all(type(client.session) is StoredSession for client in built)
        assert [client.session._name for client in built] == [name, name + '_1', name + '_2', name]
        assert store.loads[:4] == [name, name + '_1', name + '_2', name]
        await tg.close()
        assert all(client.codes == client.starts == 0 for client in built)
    assert set(store) == {name, name + '_1', name + '_2'}
    assert set(TMP.rglob('*.session')) == files_before


async def test_round_trip():
    store = Store()
    client, name = client_for(store)
    session = client.session
    session.set_dc(2, '149.154.167.51', 443)
    session.auth_key = AuthKey(KEY)
    session.takeout_id = 987654321
    add_room(session)
    session.process_entities([types.InputPeerChat(77)])
    session.set_update_state(0, state())
    session.set_update_state(1234567, state())
    session.save()
    assert store[name].startswith('1:')
    try:
        json.loads(store[name])
    except ValueError:
        pass
    else:
        raise AssertionError('the stored string is raw JSON')
    restarted, _ = client_for(store, name)
    restored = restarted.session
    assert restarted._sender.auth_key.key == KEY
    assert (restored.dc_id, restored.server_address, restored.port) == (2, '149.154.167.51', 443)
    assert restored.takeout_id == 987654321
    assert restored.get_input_entity('@someroom').access_hash == ACCESS_HASH
    assert restored.get_input_entity(1234567).access_hash == ACCESS_HASH
    assert restored.get_input_entity(-77).chat_id == 77
    assert {k: s.to_dict() for k, s in restored.get_update_states()} == {
        0: state().to_dict(), 1234567: state().to_dict()}


async def test_bounded_cache():
    store = Store()
    client, name = client_for(store)
    me = types.User(id=SELF_ID, is_self=True, access_hash=123456789, first_name='Me')
    senders = [types.User(id=i, access_hash=i + 100, first_name=f'Sender {i}') for i in range(1, 501)]
    client.session.process_entities(types.contacts.ResolvedPeer(None, [room()], senders + [me]))
    # The real disconnect flush writes the id-0 row used by connect().
    client._mb_entity_cache.set_self_user(SELF_ID, False, me.access_hash)
    await client.disconnect()
    restored, _ = client_for(store, name)
    session = restored.session
    assert len(session._entities) == 3
    assert session.get_input_entity(0).access_hash == SELF_ID
    assert session.get_input_entity(SELF_ID).access_hash == me.access_hash
    assert session.get_input_entity('@someroom').access_hash == ACCESS_HASH
    assert not any(row[0] in range(1, 501) for row in session._entities)
    try:
        session.get_input_entity(1)
    except ValueError:
        pass
    else:
        raise AssertionError('a message sender survived the restart')


async def test_save_points():
    store = Store()
    client, name = client_for(store)
    add_room(client.session)
    assert not store.saves
    await client.disconnect()
    assert len(store.saves) == 1
    assert StoredSession(store, name).get_input_entity('@someroom').access_hash == ACCESS_HASH
    calls = (len(store.loads), len(store.saves))
    client.session.save()
    client.session.close()
    assert (len(store.loads), len(store.saves)) == calls
    await client._auth_key_callback(AuthKey(OTHER_KEY))
    assert len(store.saves) == 2
    assert StoredSession(store, name).auth_key.key == OTHER_KEY


async def test_failures():
    store = Store()
    ini, name = config()
    engine = ce.ConnectionEngine(ini, session_store=store)
    error = ConnectionError('store unavailable')
    store.load_error = error
    with login_clients([]) as built:
        try:
            await engine.get_client()
        except ConnectionError as raised:
            assert raised is error
        else:
            raise AssertionError('a failed load built a client')
        assert not built
    store.load_error = None
    secret = base64.b64encode(KEY).decode()
    malformed = '1:' + base64.urlsafe_b64encode(('bad JSON ' + secret).encode()).decode()
    valid = StoredSession(store, name).dump()
    damaged_keys = []
    for key in ('!!!!', '', base64.b64encode(b'short').decode()):
        payload = json.loads(base64.urlsafe_b64decode(valid[2:]))
        payload['auth_key'] = key
        damaged_keys.append('1:' + base64.urlsafe_b64encode(json.dumps(payload).encode()).decode())
    for data in ['2:unknown', '1:!', '1:e30=', malformed, valid[:2] + '!' + valid[2:]] + damaged_keys:
        store[name] = data
        try:
            engine._new_client()
        except ValueError as raised:
            rendered = ''.join(traceback.format_exception(type(raised), raised, raised.__traceback__))
            assert name in str(raised)
            assert raised.__cause__ is None and raised.__suppress_context__
            assert data not in str(raised) and secret not in rendered
        else:
            raise AssertionError('an unreadable session was accepted')
    store.clear()
    session = seed(store, name)
    session.takeout_id = 5
    original = store[name]
    store.save_error = RuntimeError(f'failed with parameters: {original} {secret}')
    with captured() as records:
        session.save()
        session.save()
        store.save_error = None
        store.load_error = RuntimeError(secret)
        session.save()
        store.load_error = None
        store.delete_error = RuntimeError(secret)
        session.delete()
        store.delete_error = None
    assert len(records) == 4 and all(r.levelno == logging.ERROR for r in records)
    for record in records:
        assert name in record.getMessage() and 'RuntimeError' in record.getMessage()
        assert original not in record.getMessage()
        assert all(secret[i:i + 24] not in record.getMessage() for i in range(0, len(secret) - 23, 24))
        assert record.exc_info is None and record.exc_text is None and record.stack_info is None
    assert store[name] == original
    session.save()
    assert StoredSession(store, name).takeout_id == 5


async def test_login_rules():
    for terminal, interactive in ((False, None), (True, False)):
        store = Store()
        ini, _ = config()
        with login_clients([[errors.AuthKeyUnregisteredError(None)]], terminal=terminal) as built:
            tg = TgData(ini, session_store=store, interactive_login=interactive)
            try:
                await tg.connection_engine.get_client()
            except AuthRequiredError as error:
                assert error.first_login
            else:
                raise AssertionError('a fresh session was silently accepted')
            assert len(built) == 1 and built[0].starts == built[0].codes == 0

    for existing, interactive in ((False, None), (True, True)):
        store = Store()
        ini, name = config()
        if existing:
            seed(store, name)
        with login_clients([[errors.AuthKeyUnregisteredError(None)]], terminal=True) as built:
            tg = TgData(ini, session_store=store, interactive_login=interactive)
            await tg.connection_engine.get_client()
            assert built[0].starts == 1 and built[0].codes == 0
            await tg.close()
        assert StoredSession(store, name).auth_key.key == OTHER_KEY

    store = Store()
    ini, name = config()
    seed(store, name)
    with login_clients([[errors.AuthKeyUnregisteredError(None)]], terminal=True) as built:
        tg = TgData(ini, session_store=store)
        try:
            await tg.connection_engine.get_client()
        except AuthRequiredError as error:
            assert not error.first_login and error.reason == 'AUTH_KEY_UNREGISTERED'
        else:
            raise AssertionError('a stored logout was silently accepted')
        assert built[0].starts == built[0].codes == 0


async def test_log_out():
    store = Store()
    client, name = client_for(store)
    client.session.auth_key = AuthKey(KEY)
    client.session.save()
    sender = Scripted([types.auth.LoggedOut()])
    client._sender = sender
    assert await client.log_out() is True
    assert sender.sent == ['LogOutRequest']
    assert store.deletes == [name] and name not in store
    assert client.session is None

    class NoDelete:
        def __init__(self):
            self.data = {}

        def load(self, name):
            return self.data.get(name)

        def save(self, name, data):
            self.data[name] = data

    store = NoDelete()
    client, name = client_for(store)
    client._sender = Scripted([types.auth.LoggedOut()])
    assert await client.log_out() is True
    assert name in store.data


async def test_two_clients():
    store, name = Store(), 'shared'
    seed(store, name)
    first, second = StoredSession(store, name), StoredSession(store, name)
    add_room(first, 101, 'FirstRoom')
    add_room(second, 202, 'SecondRoom')
    first.save()
    second.save()
    restored = StoredSession(store, name)
    assert restored.auth_key.key == KEY
    assert restored._entities == second._entities

    for initially_empty in (True, False):
        store = Store()
        if not initially_empty:
            seed(store, name)
        stale = StoredSession(store, name)
        seed(store, name, OTHER_KEY)
        original = store[name]
        stale.auth_key = AuthKey(KEY)
        add_room(stale)
        with captured() as records:
            stale.save()
            stale.save()
            stale.close()
        assert store[name] == original
        assert len(records) == 1 and records[0].levelno == logging.WARNING
        assert 'not overwritten' in records[0].getMessage()
        assert StoredSession(store, name).auth_key.key == OTHER_KEY

    stale = StoredSession(store, name)
    del store[name]
    add_room(stale, 303)
    with captured() as records:
        stale.save()
    assert name not in store and len(records) == 1


async def test_mixed_rows():
    store, name = Store(), 'mixed'
    session = seed(store, name)
    add_room(session)
    add_room(session, username=None)
    assert len(session._entities) == 2
    before = session.dump()
    assert session.dump() == before
    session.save()
    restored = StoredSession(store, name)
    assert restored._entities == session._entities
    assert restored.dump() == before
    assert {row[2] for row in restored._entities} == {'someroom', None}


async def test_clone():
    store = Store()
    session = seed(store, 'clone')
    before = (len(store.loads), len(store.saves), len(store.deletes))
    clone = session.clone()
    assert type(clone) is MemorySession and clone.auth_key is None
    clone.auth_key = AuthKey(OTHER_KEY)
    clone.set_dc(4, '149.154.167.91', 443)
    clone.save()
    clone.close()
    clone.delete()
    target = MemorySession()
    assert session.clone(target) is target
    assert (len(store.loads), len(store.saves), len(store.deletes)) == before


async def test_health_identity():
    store, events = Store(), []
    ini, name = config(str(TMP / 'health_account.session'))
    tg = TgData(ini, session_store=store, health_callback=events.append, account_label='account-17')
    client = tg.connection_engine._new_client()
    CLIENTS.append(client)
    client._mb_entity_cache.set_self_user(SELF_ID, False, 123)
    client._sender = Scripted([errors.AuthKeyUnregisteredError(None)])
    tg.connection_engine._primary_client = client

    async def count(group_id):
        return await client(GetStateRequest())

    tg.message_engine.get_message_count = count
    try:
        await tg.get_message_count(123)
    except errors.AuthKeyUnregisteredError:
        pass
    else:
        raise AssertionError('the scripted logout was not raised')
    expected = {'label': 'account-17', 'session': 'health_account', 'user_id': SELF_ID}
    assert len(events) == 1 and events[0]['account'] == expected
    before = list(store.loads)
    tg.device_identity()
    status = await tg.health_check()
    assert store.loads == before  # device identity is still a separate in-memory probe
    assert status['health']['account'] == expected
    assert name in store.loads


async def main():
    global TMP
    print('Session Store Tests')
    print('=' * 60)
    print(f'Telethon {telethon.__version__}; offline, synthetic credentials, sockets blocked')
    tests = [test_file_default, test_every_connection_path, test_round_trip,
             test_bounded_cache, test_save_points, test_failures, test_login_rules,
             test_log_out, test_two_clients, test_mixed_rows, test_clone, test_health_identity]
    results = []
    with tempfile.TemporaryDirectory(prefix='tgdata_store_test_') as directory, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        TMP = Path(directory)
        try:
            for number, test in enumerate(tests, 1):
                print(f'\nTEST {number}: {test.__name__[5:]}')
                try:
                    await asyncio.wait_for(test(), timeout=30)
                    results.append(True)
                    print('✓ Passed')
                except Exception:
                    results.append(False)
                    traceback.print_exc()
                    print('✗ Failed')
        finally:
            for client in CLIENTS:
                await client.disconnect()
            CLIENTS.clear()
    print(f'\nPassed: {sum(results)}/{len(results)}')
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
