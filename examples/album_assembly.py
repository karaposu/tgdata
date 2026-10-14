"""Caller-owned album storage with commit-before-ack acceptance.

Offline demo: python examples/album_assembly.py --demo
This receiver accepts reference-only batches. It does not own Telegram progress,
downloaded bytes, source leases or downstream processing of post revisions.
"""

import argparse
import asyncio
from contextlib import contextmanager
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tgdata import MessageBatch, SQLiteSyncStore
from tgdata.album import (
    TelegramPost, AlbumAssemblyError, album_post_ids, assemble_albums,
    DEFAULT_MAX_MEMBERS, DEFAULT_MAX_BYTES, _limits,
)
from tgdata.sync_engine import SyncEngine


class ReceiverError(ValueError):
    """Local receiver state is unavailable or inconsistent; do not acknowledge."""


_SCHEMA = {
    'album_meta': 'name TEXT PRIMARY KEY NOT NULL, version INTEGER NOT NULL',
    'album_collections': 'collection TEXT PRIMARY KEY NOT NULL',
    'album_posts': 'collection TEXT NOT NULL, post_id TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(collection, post_id)',
    'album_receipts': 'collection TEXT NOT NULL, batch_id TEXT NOT NULL, PRIMARY KEY(collection, batch_id)',
}
_COLUMNS = {
    'album_meta': [('name', 'TEXT', 1, 1), ('version', 'INTEGER', 1, 0)],
    'album_collections': [('collection', 'TEXT', 1, 1)],
    'album_posts': [('collection', 'TEXT', 1, 1), ('post_id', 'TEXT', 1, 2), ('value', 'TEXT', 1, 0)],
    'album_receipts': [('collection', 'TEXT', 1, 1), ('batch_id', 'TEXT', 1, 2)],
}


class AlbumReceiver:
    """Small SQLite example, with an explicit new-collection operation.

    Reopen with create=False (the default) and the same collection and adequate
    limits. Restore known lost state from a backup/archive; never reset it merely
    because source progress has advanced. No asynchronous work runs under a lock.
    """

    def __init__(self, path, collection, *, create=False,
                 max_members=DEFAULT_MAX_MEMBERS, max_bytes=DEFAULT_MAX_BYTES):
        _limits(max_members, max_bytes)
        if (not isinstance(path, (str, Path)) or str(path) in ('', ':memory:')
                or str(path).startswith('file:')):
            raise ReceiverError('an explicit filesystem database path is required')
        if type(create) is not bool or type(collection) is not str or not collection:
            raise ReceiverError('explicit boolean create and nonempty collection are required')
        try:
            if len(collection.encode('utf-8')) > 256:
                raise ReceiverError('collection is too long')
        except UnicodeError:
            raise ReceiverError('collection must be UTF-8') from None
        self.path = Path(path).resolve()
        self.collection = collection
        self.max_members, self.max_bytes = max_members, max_bytes
        created = False
        if create:
            try:
                with self.path.open('xb'):
                    pass
                created = True
            except FileExistsError:
                pass
        with self._open() as db:
            db.execute('BEGIN IMMEDIATE')
            if created:
                for table, columns in _SCHEMA.items():
                    db.execute('CREATE TABLE {} ({})'.format(table, columns))
                db.execute('INSERT INTO album_meta VALUES (?, ?)', ('album-receiver', 1))
            self._validate_schema(db)
            found = db.execute('SELECT 1 FROM album_collections WHERE collection=?', (collection,)).fetchone()
            if create:
                if found:
                    raise ReceiverError('collection already exists; reopen it explicitly')
                db.execute('INSERT INTO album_collections VALUES (?)', (collection,))
            elif found is None:
                raise ReceiverError('known collection is missing')
            db.commit()

    @contextmanager
    def _open(self):
        try:
            db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True, isolation_level=None, timeout=0)
        except sqlite3.Error as error:
            raise ReceiverError('receiver open failed ({})'.format(type(error).__name__)) from None
        try:
            yield db
        except BaseException:
            # A cleanup failure must not replace the reason acceptance failed.
            try:
                db.rollback()
            except BaseException:
                pass
            try:
                db.close()
            except BaseException:
                pass
            raise
        else:
            db.close()

    @staticmethod
    def _validate_schema(db):
        for table, expected in _COLUMNS.items():
            actual = [(row[1], row[2].upper(), row[3], row[5])
                      for row in db.execute('PRAGMA table_info({})'.format(table))]
            if actual != expected:
                raise ReceiverError('receiver schema is missing or unsupported')
        if db.execute('SELECT name, version FROM album_meta').fetchall() != [('album-receiver', 1)]:
            raise ReceiverError('receiver version is missing or unsupported')

    def _validate(self, db):
        self._validate_schema(db)
        if db.execute('SELECT 1 FROM album_collections WHERE collection=?', (self.collection,)).fetchone() is None:
            raise ReceiverError('known collection is missing')

    def _load(self, db, key):
        row = db.execute('SELECT value FROM album_posts WHERE collection=? AND post_id=?',
                         (self.collection, key)).fetchone()
        if row is None:
            return None
        post = TelegramPost.from_json(row[0], max_members=self.max_members, max_bytes=self.max_bytes)
        if post.post_id != key:
            raise ReceiverError('stored post does not match its key')
        return post

    def load(self, key):
        """Read one post; None means this key is absent in the known collection."""
        with self._open() as db:
            self._validate(db)
            return self._load(db, key)

    def accept(self, batch):
        """Atomically store observed posts and input recognition; never source ack."""
        keys = album_post_ids(batch, max_bytes=self.max_bytes)
        if batch.media_mode != 'references':
            raise AlbumAssemblyError('this receiver example accepts references only')
        with self._open() as db:
            db.execute('BEGIN IMMEDIATE')
            self._validate(db)
            received = db.execute('SELECT 1 FROM album_receipts WHERE collection=? AND batch_id=?',
                                  (self.collection, batch.batch_id)).fetchone() is not None
            previous = {key: self._load(db, key) for key in keys}
            posts = assemble_albums(batch, previous=previous,
                                    max_members=self.max_members, max_bytes=self.max_bytes)
            if received:
                if any(previous[post.post_id] != post for post in posts):
                    raise ReceiverError('accepted input is missing from stored posts')
            else:
                for post in posts:
                    if previous[post.post_id] != post:
                        db.execute('INSERT OR REPLACE INTO album_posts VALUES (?, ?, ?)',
                                   (self.collection, post.post_id, post.to_json()))
                db.execute('INSERT INTO album_receipts VALUES (?, ?)', (self.collection, batch.batch_id))
            db.commit()
        return posts


async def collect(tg, chat_id, receiver, *, max_batches=10, batch_size=200):
    """Accept only normal confirmed deliveries; errors/cancellation propagate.

    Do not acknowledge an arbitrary exception's partial_result. Recover using the
    source's documented pending-delivery APIs and offer its normal replay instead.
    """
    if type(max_batches) is not int or max_batches <= 0:
        raise ValueError('max_batches must be a positive integer')
    for _ in range(max_batches):
        batch = await tg.sync_group(chat_id, limit=batch_size)
        if batch is None:
            break
        receiver.accept(batch)
        await tg.acknowledge_sync(chat_id, batch.batch_id)
        if batch.stop_reason == 'end':
            break


def _demo_batch(after_id, limit):
    records = []
    for ident in [i for i in (101, 102, 103) if i > after_id][:limit]:
        records.append(dict(id=str(ident), kind='message', date='2026-10-14T00:00:00.000000Z',
                            edit_date=None, text={101: 'First caption', 102: '', 103: 'Second caption'}[ident],
                            sender=dict(id=None, name=None, username=None), post_author=None,
                            reply_to_id=None, forward_from_id=None, grouped_id='4611686018427387921',
                            service_action=None, media=None))
    return MessageBatch._from_records(-1000000000007, after_id, records, 'references',
                                      'limit' if len(records) == limit else 'end')


async def demo(directory):
    chat = -1000000000007
    receiver = AlbumReceiver(directory / 'posts.sqlite3', 'demo', create=True)
    store = SQLiteSyncStore(directory / 'progress.sqlite3')
    reads = []

    async def reader(chat_id, **options):
        reads.append(options)
        return _demo_batch(options['after_id'], options['limit'])

    first = SyncEngine(reader, store)
    await first.initialize(chat, after_id=100)
    batch = await first.prepare(chat, limit=1)
    receiver.accept(batch)
    restarted = SyncEngine(reader, SQLiteSyncStore(store.path, create=False))
    receiver = AlbumReceiver(receiver.path, 'demo')
    replay = await restarted.prepare(chat, limit=1)
    assert replay.to_json() == batch.to_json() and len(reads) == 1
    receiver.accept(replay)
    await restarted.acknowledge(chat, replay.batch_id)
    remaining = await restarted.prepare(chat, limit=3)
    post, = receiver.accept(remaining)
    await restarted.acknowledge(chat, remaining.batch_id)
    assert post.member_ids == (101, 102, 103) and post.membership == 'unconfirmed'
    print('Lost acknowledgment replayed without another source read.')
    print('One album; 3 members; 2 captions; membership unconfirmed.')
    print('Acknowledged through:', (await restarted.status(chat)).after_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', required=True)
    parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='tgdata_album_demo_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('demo forbids network')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('demo forbids network')):
        asyncio.run(demo(Path(tmp)))


if __name__ == '__main__':
    main()
