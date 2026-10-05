"""Pre-plan probes: actual Telethon paging and SQLite writer serialization.

Synthetic replies and credentials only. No sockets or login.
"""
import asyncio
from concurrent.futures import ProcessPoolExecutor
import datetime
from pathlib import Path
import socket
import sqlite3
import tempfile
from unittest.mock import patch

from telethon import TelegramClient, errors
from telethon.sessions import MemorySession
from telethon.tl import types, functions


class Exhausted(Exception):
    pass


class Sender:
    def __init__(self):
        self.calls = []

    def send(self, request, ordered=False):
        self.calls.append((request.limit, request.add_offset, request.offset_id))
        messages = [types.Message(
            id=i, peer_id=types.PeerChannel(7), date=datetime.datetime.now(datetime.timezone.utc),
            message=str(i), from_id=types.PeerUser(8))
            for i in reversed(range(request.offset_id, request.offset_id + request.limit))]
        future = asyncio.get_running_loop().create_future()
        future.set_result(types.messages.ChannelMessages(
            pts=1, count=2000, messages=messages, topics=[], chats=[],
            users=[types.User(id=8, access_hash=8, first_name='Synthetic')]))
        return future


async def paging():
    client = TelegramClient(MemorySession(), 12345, '0123456789abcdef0123456789abcdef')
    client._sender = sender = Sender()
    iterator = client.iter_messages(types.InputPeerChannel(7, 7), limit=2000, min_id=100, reverse=True)
    load = iterator._load_next_chunk
    remaining = 37

    async def bounded_page():
        nonlocal remaining
        if remaining == 0:
            raise Exhausted
        original = iterator.left
        original_offset = iterator.request.add_offset
        iterator.left = min(original, remaining)
        try:
            done = await load()
            remaining -= len(iterator.buffer)
            return done
        finally:
            iterator.left = original
            iterator.request.add_offset = original_offset

    iterator._load_next_chunk = bounded_page
    seen = []
    try:
        async for message in iterator:
            seen.append(message.id)
    except Exhausted:
        pass
    assert sender.calls == [(37, -37, 101)], sender.calls
    assert seen == list(range(101, 138)), seen
    print('Paging: real iterator sent limit=37, add_offset=-37, offset_id=101; yielded 37 ordered messages')
    print('Paging: original 2,000-message limit retained; next page stopped before send')
    remaining = 100
    resumed = [(await iterator.__anext__()).id for _ in range(100)]
    assert sender.calls[-1] == (100, -100, 138), sender.calls
    assert resumed == list(range(138, 238)), resumed
    print('Paging: after renewed allowance, the same iterator sent 100/-100 from 138 without a gap')


def claim(path):
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    try:
        db.execute('BEGIN IMMEDIATE')
        used = db.execute('SELECT used FROM quota WHERE account = 1').fetchone()[0]
        if used + 7 > 100:
            db.rollback()
            return 0
        db.execute('UPDATE quota SET used = used + 7 WHERE account = 1')
        db.commit()
        return 7
    finally:
        db.close()


async def identity_and_dispatch():
    client = TelegramClient(MemorySession(), 12345, '0123456789abcdef0123456789abcdef')
    client._mb_entity_cache.set_self_user(111, False, 111)

    class SelfSender:
        def send(self, request, ordered=False):
            result = asyncio.get_running_loop().create_future()
            result.set_result([types.User(id=222, is_self=True, access_hash=222, first_name='Synthetic')])
            return result

    client._sender = SelfSender()
    me = await client.get_me()
    assert client._self_id == 111 and me.id == 222
    print('Identity: cached self ID=111; authenticated get_me response=222; cache alone is not authority')

    class GuardedSender:
        charged = 0
        sends = 0

        def send(self, request, ordered=False):
            async def admit_then_send():
                if self.charged + request.limit > 7:
                    raise Exhausted
                self.charged += request.limit
                self.sends += 1
                result = asyncio.get_running_loop().create_future()
                result.set_exception(errors.RpcCallFailError(request=request))
                return await result
            return admit_then_send()

    guard = GuardedSender()
    request = functions.messages.GetHistoryRequest(
        peer=types.InputPeerChannel(7, 7), offset_id=0, offset_date=None,
        add_offset=0, limit=5, max_id=0, min_id=0, hash=0)
    try:
        await client._call(guard, request)
    except Exhausted:
        pass
    else:
        raise AssertionError('a second send exceeded the allowance')
    assert guard.charged == 5 and guard.sends == 1
    print('Dispatch: real Telethon retry was denied before its second send; first failed attempt remains charged')


def concurrency():
    with tempfile.TemporaryDirectory(prefix='tgdata_budget_probe_') as tmp:
        path = str(Path(tmp) / 'budget.sqlite3')
        db = sqlite3.connect(path)
        db.execute('CREATE TABLE quota (account INTEGER PRIMARY KEY, used INTEGER NOT NULL)')
        db.execute('INSERT INTO quota VALUES (1, 0)')
        db.commit()
        db.close()
        with ProcessPoolExecutor(max_workers=4) as pool:
            accepted = sum(pool.map(claim, [path] * 40))
        db = sqlite3.connect(path)
        stored = db.execute('SELECT used FROM quota WHERE account = 1').fetchone()[0]
        db.close()
        assert accepted == stored == 98, (accepted, stored)
        print('SQLite: 40 competing claims across 4 processes charged 98/100, exactly matching accepted claims')
        print('SQLite: usage survived closing and reopening all connections')


if __name__ == '__main__':
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        asyncio.run(paging())
        asyncio.run(identity_and_dispatch())
    concurrency()
