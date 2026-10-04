"""PR #13 lifecycle probes. Synthetic credentials, no sockets or live account."""
import asyncio
import datetime
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from telethon.crypto import AuthKey
from telethon.tl import types
from tgdata.connection_engine import ConnectionEngine
from tgdata.session_store import StoredSession

KEY = bytes(range(256))
NEW_KEY = bytes(reversed(range(256)))
DATE = datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc)


class Store:
    def __init__(self):
        self.data = {}
        self.writes = []
        self.deletes = []

    def load(self, name):
        return self.data.get(name)

    def save(self, name, data):
        self.data[name] = data
        self.writes.append(data)

    def delete(self, name):
        self.deletes.append(name)
        self.data.pop(name, None)


class Sender:
    def __init__(self, key=KEY):
        self.auth_key = AuthKey(key)
        self.up = False
        self.sent = []

    async def connect(self, connection):
        self.up = True
        return True

    async def disconnect(self):
        self.up = False

    def is_connected(self):
        return self.up

    def send(self, request, ordered=False):
        self.sent.append(type(request).__name__)
        future = asyncio.get_running_loop().create_future()
        future.set_result(types.auth.LoggedOut() if type(request).__name__ == 'LogOutRequest' else True)
        return future


def seed(store, key=KEY):
    session = StoredSession(store, 'account')
    session.set_dc(2, '149.154.167.51', 443)
    session.auth_key = AuthKey(key)
    session.process_entities([
        types.User(id=4242, is_self=True, access_hash=123456789, first_name='Me'),
        types.InputPeerUser(0, 4242),
        types.InputPeerChannel(1234567, -2255621593168970683),
    ])
    session.set_update_state(0, types.updates.State(10, 2, DATE, 3, 0))
    session.set_update_state(1234567, types.updates.State(20, 0, DATE, 0, 0))
    session.save()
    return session


async def parked_loop():
    await asyncio.Event().wait()


async def nobody():
    return None


def client(ini, store, key=KEY):
    result = ConnectionEngine(str(ini), session_store=store)._new_client()
    result._sender = Sender(key)
    result._update_loop = parked_loop
    result._keepalive_loop = parked_loop
    return result


async def main():
    with tempfile.TemporaryDirectory(prefix='tgdata_pr_lifecycle_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        ini = Path(tmp) / 'config.ini'
        ini.write_text('[Telegram]\napi_id = 12345\n'
                       'api_hash = 0123456789abcdef0123456789abcdef\nsession_file = account\n')

        # Run the actual connect method. Only transport/server answers and
        # background loops are supplied; the session save calls are real.
        store = Store()
        fresh = client(ini, store)
        fresh.get_me = nobody
        await fresh.connect()
        snapshots = [fresh.session._parse(data) for data in store.writes]
        assert len(snapshots) == 2
        assert snapshots[0]['auth_key'] is None and snapshots[1]['auth_key'] == KEY
        print('P1 real connect: data-centre save, then auth-key save — passed')
        await fresh.disconnect()

        store = Store()
        seed(store)
        restored = client(ini, store)
        restored._catch_up = True
        await restored.connect()
        account, channels = restored._message_box.session_state()
        assert restored._self_id == 4242
        assert restored._mb_entity_cache.get(4242).hash == 123456789
        assert (account['pts'], account['qts'], account['seq']) == (10, 2, 3)
        assert channels[1234567] == 20
        print('P2 real connect: self identity and stored update positions restored — passed')
        await restored.disconnect()

        store = Store()
        seed(store)
        stale = client(ini, store)
        seed(store, NEW_KEY)
        await stale.disconnect()
        assert StoredSession(store, 'account').auth_key.key == NEW_KEY
        print('P3 stale real disconnect: newer stored login preserved — passed')

        store = Store()
        seed(store)
        stale = client(ini, store)
        seed(store, NEW_KEY)
        newer = store.load('account')
        assert await stale.log_out() is True
        print('P4 stale real log_out: newer stored login removed:', store.load('account') is None)
        print('P4 store.delete calls:', len(store.deletes))
        print('P4 newer stored login preserved:', store.load('account') == newer)


if __name__ == '__main__':
    asyncio.run(main())
