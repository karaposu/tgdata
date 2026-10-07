"""Offline AccountPool demo: python examples/account_pool.py --demo.

No real config or Telegram sockets. The private wire replacement is only test
instrumentation; see docs/account_pool.md for ordinary account configuration.
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from telethon import errors, functions, types
from telethon.crypto import AuthKey
from tgdata import (AccountPool, PoolAccount, PoolGroup, ReadBudget,
                    SQLiteAccountPoolStore, SQLiteSyncStore)

CHAT = -1000000000007


class SessionStore(dict):
    def load(self, name): return self.get(name)
    def save(self, name, data): self[name] = data


def room():
    return types.Channel(id=7, title='Offline example', photo=types.ChatPhotoEmpty(),
                         date=datetime.now(timezone.utc), access_hash=7, megagroup=True)


class SyntheticWire:
    def __init__(self, account_id, deny=False):
        self.account_id, self.deny = account_id, deny
        self.up, self.reads = True, 0

    def is_connected(self): return self.up

    async def disconnect(self): self.up = False

    def send(self, request, ordered=False):
        if isinstance(request, (list, tuple)):
            return [self.send(item, ordered) for item in request]
        bytes(request)
        while hasattr(request, 'query'):
            request = request.query
        if isinstance(request, functions.updates.GetStateRequest):
            result = types.updates.State(1, 1, datetime.now(timezone.utc), 1, 0)
        elif isinstance(request, functions.users.GetUsersRequest):
            result = [types.User(id=self.account_id, is_self=True, access_hash=self.account_id,
                                 first_name='Synthetic account')]
        elif isinstance(request, functions.channels.GetChannelsRequest):
            result = types.messages.Chats(chats=[room()])
        elif isinstance(request, functions.messages.GetHistoryRequest):
            self.reads += 1
            if self.deny:
                result = errors.FloodWaitError(request=request, capture=30)
            else:
                selected = [mid for mid in range(101, 105) if mid >= request.offset_id][:request.limit]
                messages = [types.Message(id=mid, peer_id=types.PeerChannel(7),
                    from_id=types.PeerUser(77), date=datetime.now(timezone.utc),
                    message='Synthetic message {}'.format(mid)) for mid in reversed(selected)]
                result = types.messages.Messages(messages=messages, topics=[], chats=[room()],
                    users=[types.User(id=77, first_name='Synthetic author')])
        else:
            raise AssertionError('Unexpected demo request: ' + type(request).__name__)
        future = asyncio.get_running_loop().create_future()
        if isinstance(result, Exception): future.set_exception(result)
        else: future.set_result(result)
        return future


class Receiver:
    """First-observation archive and batch receipts, committed together."""
    def __init__(self, path):
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE batches (id TEXT PRIMARY KEY)')
            db.execute('CREATE TABLE messages (chat TEXT, id TEXT, data TEXT, PRIMARY KEY(chat,id))')

    def accept(self, batch):
        with sqlite3.connect(self.path) as db:
            if db.execute('INSERT OR IGNORE INTO batches VALUES (?)', (batch.batch_id,)).rowcount:
                for message in batch.messages:
                    db.execute('INSERT OR IGNORE INTO messages VALUES (?,?,?)',
                               (str(batch.chat_id), message['id'], json.dumps(message)))

    def count(self):
        with sqlite3.connect(self.path) as db:
            return db.execute('SELECT COUNT(*) FROM messages').fetchone()[0]


async def demo(directory):
    budget = ReadBudget(directory / 'budget.sqlite3')
    accounts = []
    for aid in (111, 222):
        budget.configure(aid, 20)  # Deliberate policy for fresh synthetic accounts only.
        config = directory / ('account-{}.ini'.format(aid))
        config.write_text('[Telegram]\napi_id=12345\napi_hash=0123456789abcdef0123456789abcdef\n'
                          'session_file=synthetic-{}\n'.format(aid))
        accounts.append(PoolAccount(aid, config, session_store=SessionStore()))
    pool = AccountPool(accounts, [PoolGroup(CHAT)], read_budget=budget,
                       state_store=SQLiteAccountPoolStore(directory / 'pool.sqlite3'),
                       sync_store=SQLiteSyncStore(directory / 'daily.sqlite3'))
    await pool.initialize()
    wires = {}
    for aid, source in pool._sources.items():
        source.preflight()
        client = source._primary_client
        client.session.auth_key = AuthKey(bytes([aid % 251 + 1]) * 256)
        client.session.process_entities([room()])
        client._mb_entity_cache.set_self_user(aid, False, aid)
        client._sender = wires[aid] = SyntheticWire(aid, deny=aid == 111)
    receiver = Receiver(directory / 'receiver.sqlite3')
    try:
        result = await pool.read(CHAT, after_id=100, limit=2)
        receiver.accept(result.batch)
        print('Selected account:', result.account_id)
        print('Attempts:', ', '.join(a.outcome for a in result.attempts))
        # Import only the position the receiver just durably accepted.
        await pool.initialize_sync(CHAT, after_id=result.batch.next_after_id)
        pending = await pool.sync_group(CHAT, limit=2)
        before = sum(w.reads for w in wires.values())
        replay = await pool.sync_group(CHAT, limit=1)
        assert replay.batch_id == pending.batch_id
        assert sum(w.reads for w in wires.values()) == before
        receiver.accept(replay)
        await pool.acknowledge_sync(CHAT, replay.batch_id)
        print('Replay source reads: 0')
        print('Stored messages:', receiver.count())
        print('Acknowledged through:', (await pool.get_sync_status(CHAT)).after_id)
        print('Allowance charged:', {aid: budget.status(aid).used for aid in (111, 222)})
    finally:
        await pool.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='run an offline synthetic demonstration')
    args = parser.parse_args()
    if not args.demo:
        parser.print_help()
        return
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='tgdata-pool-demo-') as directory, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        asyncio.run(demo(Path(directory)))


if __name__ == '__main__':
    main()
