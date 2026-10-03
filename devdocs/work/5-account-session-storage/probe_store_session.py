"""Gate 1 probe for #5 (plan.md): a store-backed MemorySession through Telethon 1.45.0's real client.
Run from the repository root: .venv/bin/python devdocs/work/5-account-session-storage/probe_store_session.py"""
import asyncio, base64, datetime, hashlib, json, logging, os, sys, time
sys.path.insert(0, os.getcwd())
from telethon.crypto import AuthKey
from telethon.sessions import MemorySession
from telethon.sessions.memory import _SentFileType
from telethon.tl import types
import tgdata.connection_engine as ce

log = logging.getLogger('probe'); logging.basicConfig(level=logging.ERROR, format='%(levelname)s %(message)s')

class StoredSession(MemorySession):                          # the prototype
    def __init__(self, store, name):
        super().__init__()
        self._store, self._name, self._saved = store, name, None
        data = store.load(name)
        if data is not None:
            self._restore(data)
            self._saved = data
    def _dump(self):
        key = self._auth_key.key if self._auth_key is not None and self._auth_key.key else None
        return json.dumps({
            'version': 1, 'dc_id': self._dc_id, 'server_address': self._server_address, 'port': self._port,
            'auth_key': base64.b64encode(key).decode() if key else None, 'takeout_id': self._takeout_id,
            'entities': [list(e) for e in self._entities],
            'update_states': [[i, s.pts, s.qts, s.date.timestamp(), s.seq, s.unread_count]
                              for i, s in self._update_states.items()],
        }, separators=(',', ':'))
    def _restore(self, data):
        d = json.loads(data)
        if d.get('version') != 1:
            raise ValueError(f"unknown stored session version {d.get('version')!r}")
        self._dc_id, self._server_address, self._port = d['dc_id'], d['server_address'], d['port']
        self._auth_key = AuthKey(base64.b64decode(d['auth_key'])) if d['auth_key'] else None
        self._takeout_id = d['takeout_id']
        self._entities = {tuple(e) for e in d['entities']}
        self._update_states = {i: types.updates.State(pts=p, qts=q, date=datetime.datetime.fromtimestamp(t, datetime.timezone.utc),
                                                      seq=s, unread_count=u) for i, p, q, t, s, u in d['update_states']}
    def save(self):
        try:
            data = self._dump()
            if data != self._saved:
                self._store.save(self._name, data); self._saved = data
        except Exception:
            log.error("could not save session %r", self._name, exc_info=False)
    def close(self):
        self.save()
    def delete(self):
        if hasattr(self._store, 'delete'):
            self._store.delete(self._name)
    def clone(self, to_instance=None):
        return to_instance or MemorySession()

class Store:
    def __init__(self): self.data, self.saves, self.deletes = {}, 0, 0
    def load(self, name): return self.data.get(name)
    def save(self, name, data): self.data[name] = data; self.saves += 1
    def delete(self, name): self.data.pop(name, None); self.deletes += 1

def check(cond, msg):
    print(("✓ " if cond else "✗ ") + msg)

async def main():
    store = Store()
    fresh = StoredSession(store, 'acct')
    check(fresh.auth_key is None, "nothing stored: auth_key is None -> a brand-new session (first-login rules)")

    s = StoredSession(store, 'acct')
    key = os.urandom(256)
    s.set_dc(2, '149.154.167.51', 443); s.auth_key = AuthKey(key)
    room = types.Channel(id=1234567, title='Room', photo=types.ChatPhotoEmpty(), date=datetime.datetime.now(),
                         access_hash=987654321, username='SomeRoom', megagroup=True)
    s.process_entities(types.contacts.ResolvedPeer(None, [room], []))
    s.process_entities(types.contacts.ResolvedPeer(None, [types.InputPeerUser(0, 4242)], []))   # Telethon's self-id hack
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    s.set_update_state(0, types.updates.State(pts=10, qts=2, date=now, seq=3, unread_count=0))
    s.set_update_state(1234567, types.updates.State(pts=55, qts=0, date=now, seq=0, unread_count=0))
    s.save()

    r = StoredSession(store, 'acct')
    check((r.dc_id, r.server_address, r.port) == (2, '149.154.167.51', 443), "data centre restored")
    check(r.auth_key is not None and r.auth_key.key == key, "auth key restored")
    from telethon import utils as tu; peer = r.get_input_entity(tu.get_peer_id(types.PeerChannel(1234567)))
    check(isinstance(peer, types.InputPeerChannel) and peer.access_hash == 987654321, "group cache: the room's access hash by id")
    check(r.get_input_entity('@someroom').access_hash == 987654321, "group cache: the room by username")
    check(r.get_input_entity(0).access_hash == 4242, "the self-id row connect() reads")
    states = dict(r.get_update_states())
    check(states[0].pts == 10 and states[0].date == now and states[1234567].pts == 55, "update states restored, with dates")

    client = ce._client_class(ce.TelegramClient)(r, 12345, '0123456789abcdef0123456789abcdef')
    check(client.session is r, "Telethon's real constructor takes the store-backed session as-is")
    check(client._sender.auth_key.key == key, "its connection is built with the restored auth key")
    saves = store.saves
    r.process_entities(types.contacts.ResolvedPeer(None, [types.Channel(id=777, title='New', photo=types.ChatPhotoEmpty(),
                                                         date=datetime.datetime.now(), access_hash=1, username='newroom')], []))
    await client.disconnect()                                   # never connected: Telethon still flushes and closes
    check(store.saves == saves + 1 and '"newroom"' in store.data['acct'], "disconnect -> close() -> one save, with the new room")
    r.save()
    check(store.saves == saves + 1, "an unchanged session is not written again")

    store.data['broken'] = '{not json'
    try:
        StoredSession(store, 'broken'); check(False, "unreadable stored session raised")
    except ValueError:
        check(True, "unreadable stored session raises (never read as a new session)")
    class Down(Store):
        def load(self, name): raise ConnectionError("store down")
        def save(self, name, data): raise ConnectionError("store down")
    try:
        StoredSession(Down(), 'acct'); check(False, "a failed load raised")
    except ConnectionError:
        check(True, "a failed load raises the store's error")
    ok = StoredSession(Store(), 'x'); ok._store = Down(); ok.set_dc(1, '1.1.1.1', 443)
    ok.save(); check(True, "a failed save is logged and does not raise")

    copy = r.clone()
    check(type(copy) is MemorySession, "clone() is a plain in-memory session")
    before = store.saves; copy.set_dc(4, '2.2.2.2', 443); copy.save(); copy.close()
    check(store.saves == before, "the copy never writes to the store")

    r.delete(); check('acct' not in store.data and store.deletes == 1, "delete() removes it from the store")

    big = StoredSession(Store(), 'big'); big.set_dc(2, '149.154.167.51', 443); big.auth_key = AuthKey(os.urandom(256))
    for i in range(5000):
        big._entities.add((-1000000000000 - i, 10**17 + i, f'room{i}', None, f'Room number {i}'))
    t = time.perf_counter(); data = big._dump(); dt = (time.perf_counter() - t) * 1000
    t = time.perf_counter(); StoredSession.__new__(StoredSession)._restore.__func__(MemorySession.__new__(StoredSession), data); dr = (time.perf_counter() - t) * 1000
    print(f"   5,000 cached groups: {len(data)/1024:.0f} KB stored, dump {dt:.1f} ms, restore {dr:.1f} ms")

asyncio.run(main())
