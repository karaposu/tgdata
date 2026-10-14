"""Bounded daily collection with durable local acceptance before acknowledgment.

Offline demonstration (no Telegram):
    python examples/daily_continuation.py --demo

Real use (an already logged-in account and canonical negative group ID):
    python examples/daily_continuation.py --config config.ini \
        --directory ./daily-archive --group=-1001234567890 --after-id 48213

Later daily runs omit --after-id. This example stores references, not media bytes.
It deliberately keeps destination records and progress in one portable SQLite file.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tgdata import TgData, MessageBatch, SQLiteSyncStore


class Destination:
    """Commit batch acceptance and message deduplication in one transaction."""

    def __init__(self, path):
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS example_received_batches '
                       '(batch_id TEXT PRIMARY KEY)')
            db.execute('CREATE TABLE IF NOT EXISTS example_messages '
                       '(chat_id TEXT, message_id TEXT, record TEXT NOT NULL, '
                       'PRIMARY KEY (chat_id, message_id))')

    def accept(self, batch):
        if batch.media_mode != 'references':
            raise ValueError('This example accepts reference-only batches')
        with sqlite3.connect(self.path) as db:
            fresh = db.execute('INSERT OR IGNORE INTO example_received_batches VALUES (?)',
                               (batch.batch_id,)).rowcount
            if fresh:
                for message in batch.messages:
                    db.execute('INSERT OR IGNORE INTO example_messages VALUES (?, ?, ?)',
                               (str(batch.chat_id), message['id'],
                                json.dumps(message, ensure_ascii=False)))
        # Exiting the transaction commits both records and the duplicate marker.

    def count(self):
        with sqlite3.connect(self.path) as db:
            return db.execute('SELECT COUNT(*) FROM example_messages').fetchone()[0]


async def collect(tg, chat_id, destination, *, max_batches=10, batch_size=200):
    """Run a bounded amount of work; the caller schedules tomorrow's invocation."""
    for _ in range(max_batches):
        try:
            batch = await tg.sync_group(chat_id, limit=batch_size)
        except Exception as error:
            partial = getattr(error, 'partial_result', None)
            # sync_group only re-raises a read error with a nonempty prefix after
            # saving that prefix. A failed save raises SyncError instead, with
            # read_error rather than a deliverable partial_result.
            if isinstance(partial, MessageBatch) and partial.messages:
                destination.accept(partial)
                await tg.acknowledge_sync(chat_id, partial.batch_id)
            raise
        if batch is None:
            break
        destination.accept(batch)
        await tg.acknowledge_sync(chat_id, batch.batch_id)
        if batch.stop_reason == 'end':
            break


def demo_batch(chat_id, after_id, limit):
    """Synthetic, valid public batch values; this does not simulate SDK behavior."""
    messages = []
    for number in [n for n in (101, 102, 103, 104) if n > after_id][:limit]:
        messages.append({
            'id': str(number), 'kind': 'message',
            'date': '2026-10-06T00:00:00.000000Z', 'edit_date': None,
            'text': 'Synthetic message {}'.format(number),
            'sender': {'id': None, 'name': None, 'username': None},
            'post_author': None, 'reply_to_id': None, 'forward_from_id': None,
            'grouped_id': None, 'service_action': None, 'media': None,
        })
    payload = {
        'schema': 'tgdata.message-batch', 'version': 1, 'chat_id': str(chat_id),
        'after_id': str(after_id),
        'next_after_id': messages[-1]['id'] if messages else str(after_id),
        'media_mode': 'references', 'messages': messages,
        'stop_reason': 'limit' if len(messages) == limit else 'end',
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False)
    payload['batch_id'] = hashlib.sha256(encoded.encode('utf-8')).hexdigest()
    return MessageBatch(payload)


class DemoReader(TgData):
    def __init__(self, progress):
        self.reads = 0
        super().__init__('/unused-in-offline-demo.ini', sync_store=progress)

    async def get_message_batch(self, group_id, *, after_id=0, limit=200, download_media_to=None):
        self.reads += 1
        return demo_batch(group_id, after_id, limit)


async def demo(directory):
    chat_id = -1000000000007
    path = directory / 'demo.sqlite3'
    destination = Destination(path)
    first = DemoReader(SQLiteSyncStore(path))
    await first.initialize_sync(chat_id, after_id=100)
    batch = await first.sync_group(chat_id, limit=2)
    if batch is None:
        print('Demo already complete. Stored messages:', destination.count())
        await first.close()
        return
    destination.accept(batch)
    # Simulate the process disappearing after acceptance, before acknowledgment.
    assert (await first.get_sync_status(chat_id)).after_id == 100
    print('Destination accepted the batch; acknowledgment was lost.')
    await first.close()
    restarted = DemoReader(SQLiteSyncStore(path))
    try:
        replay = await restarted.sync_group(chat_id, limit=2)
        assert replay.to_json() == batch.to_json() and restarted.reads == 0
        print('Replay used the same batch without reading Telegram.')
        destination.accept(replay)
        await restarted.acknowledge_sync(chat_id, replay.batch_id)
        await collect(restarted, chat_id, destination, batch_size=2)
        print('Stored messages:', destination.count())
        print('Acknowledged through:', (await restarted.get_sync_status(chat_id)).after_id)
    finally:
        await restarted.close()


async def run(args, directory):
    if args.demo:
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('demo forbids network')), \
                patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('demo forbids network')):
            await demo(directory)
        return
    path = directory / 'collection.sqlite3'
    destination = Destination(path)
    tg = TgData(args.config, interactive_login=False, sync_store=SQLiteSyncStore(path))
    try:
        if args.after_id is not None:
            await tg.initialize_sync(args.group, after_id=args.after_id)
        elif await tg.get_sync_status(args.group) is None:
            raise ValueError('First run requires --after-id (0 explicitly starts from visible history)')
        await collect(tg, args.group, destination, max_batches=args.max_batches,
                      batch_size=args.batch_size)
        print('Stored messages:', destination.count())
        print((await tg.get_sync_status(args.group)).to_dict())
    finally:
        await tg.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--config', default='config.ini')
    parser.add_argument('--group', type=int)
    parser.add_argument('--after-id', type=int)
    parser.add_argument('--batch-size', type=int, default=200)
    parser.add_argument('--max-batches', type=int, default=10)
    args = parser.parse_args()
    if not args.demo and (args.group is None or args.group >= 0 or args.directory is None):
        parser.error('normal use requires --directory and a canonical negative --group')
    if not 1 <= args.batch_size <= 10000 or args.max_batches < 1:
        parser.error('batch-size must be 1..10000 and max-batches must be positive')
    if args.directory is None:
        with tempfile.TemporaryDirectory(prefix='tgdata_daily_demo_') as tmp:
            asyncio.run(run(args, Path(tmp)))
    else:
        args.directory.mkdir(parents=True, exist_ok=True)
        asyncio.run(run(args, args.directory))


if __name__ == '__main__':
    main()
