"""Caller-owned album storage with commit-before-ack acceptance.

Offline demo: python examples/album_assembly.py --demo
This receiver accepts reference-only batches. It does not own Telegram progress,
downloaded bytes, source leases or downstream processing of post revisions.
"""

import argparse
import asyncio
from contextlib import contextmanager
import hashlib
import json
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
    _identity, _revision,
)
from tgdata.message_batch import (
    MIN_LONG, MAX_MESSAGE_ID, _canonical, _identifier,
    _json_pairs, _invalid_constant, _validate_record,
)
from tgdata.sync_engine import SyncEngine


class ReceiverError(ValueError):
    """Local receiver state is unavailable or inconsistent; do not acknowledge."""


_SCHEMA = {
    'album_meta': 'name TEXT PRIMARY KEY NOT NULL, version INTEGER NOT NULL',
    'album_collections': 'collection TEXT PRIMARY KEY NOT NULL',
    'album_members': 'collection TEXT NOT NULL, chat_id INTEGER NOT NULL, message_id INTEGER NOT NULL, '
                     'post_id TEXT NOT NULL, record TEXT NOT NULL, record_sha256 TEXT NOT NULL, '
                     'PRIMARY KEY(collection, chat_id, message_id)',
    'album_receipts': 'collection TEXT NOT NULL, batch_id TEXT NOT NULL, PRIMARY KEY(collection, batch_id)',
}
_COLUMNS = {
    'album_meta': [('name', 'TEXT', 1, 1), ('version', 'INTEGER', 1, 0)],
    'album_collections': [('collection', 'TEXT', 1, 1)],
    'album_members': [('collection', 'TEXT', 1, 1), ('chat_id', 'INTEGER', 1, 2),
                      ('message_id', 'INTEGER', 1, 3), ('post_id', 'TEXT', 1, 0),
                      ('record', 'TEXT', 1, 0), ('record_sha256', 'TEXT', 1, 0)],
    'album_receipts': [('collection', 'TEXT', 1, 1), ('batch_id', 'TEXT', 1, 2)],
}


class AlbumReceiver:
    """Store immutable accepted records; construct current post views separately.

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
                db.execute('CREATE INDEX album_members_by_post ON album_members(collection, post_id, message_id)')
                db.execute('INSERT INTO album_meta VALUES (?, ?)', ('album-receiver', 2))
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
            primary = [row for row in db.execute('PRAGMA index_list({})'.format(table)) if row[3] == 'pk']
            expected_pk = [item[0] for item in sorted(expected, key=lambda item: item[3]) if item[3]]
            if len(primary) != 1:
                raise ReceiverError('receiver primary key is unsupported')
            indexed = [(row[2], row[4]) for row in db.execute('PRAGMA index_xinfo({})'.format(primary[0][1])) if row[5]]
            if indexed != [(name, 'BINARY') for name in expected_pk]:
                raise ReceiverError('receiver key comparison is unsupported')
        index = [row for row in db.execute('PRAGMA index_list(album_members)') if row[1] == 'album_members_by_post']
        columns = [(row[2], row[4]) for row in db.execute('PRAGMA index_xinfo(album_members_by_post)') if row[5]]
        if (len(index) != 1 or index[0][2] != 0 or index[0][4] != 0 or
                columns != [('collection', 'BINARY'), ('post_id', 'BINARY'), ('message_id', 'BINARY')]):
            raise ReceiverError('receiver post index is missing or unsupported')
        if db.execute('SELECT name, version FROM album_meta').fetchall() != [('album-receiver', 2)]:
            raise ReceiverError('receiver version is missing or unsupported')

    def _validate(self, db):
        self._validate_schema(db)
        if db.execute('SELECT 1 FROM album_collections WHERE collection=?', (self.collection,)).fetchone() is None:
            raise ReceiverError('known collection is missing')

    def _stats(self, db, key):
        count, amount, invalid = db.execute(
            'SELECT COUNT(*), COALESCE(SUM(length(CAST(record AS BLOB))),0), '
            "COALESCE(SUM(typeof(record)!='text' OR typeof(record_sha256)!='text' "
            "OR typeof(chat_id)!='integer' OR typeof(message_id)!='integer'),0) "
            'FROM album_members WHERE collection=? AND post_id=?', (self.collection, key)).fetchone()
        if invalid:
            raise ReceiverError('stored member has invalid field types')
        return count, amount

    def _read_members(self, db, key):
        return db.execute('SELECT chat_id, message_id, record, record_sha256 FROM album_members '
                          'WHERE collection=? AND post_id=? ORDER BY message_id', (self.collection, key))

    def _load(self, db, key, *, max_bytes=None, stats=None):
        maximum = self.max_bytes if max_bytes is None else max_bytes
        count, amount = self._stats(db, key) if stats is None else stats
        if not count:
            return None
        if count > self.max_members or amount > maximum or maximum <= 0:
            raise AlbumAssemblyError('post view exceeds member or byte limit')
        members, chat = [], None
        try:
            for stored_chat, ident, encoded, digest in self._read_members(db, key):
                _identifier(str(stored_chat), 'stored chat_id', MIN_LONG, -1)
                _identifier(str(ident), 'stored message_id', 1, MAX_MESSAGE_ID)
                if hashlib.sha256(encoded.encode('utf-8')).hexdigest() != digest:
                    raise ReceiverError('stored member digest mismatch')
                member = json.loads(encoded, object_pairs_hook=_json_pairs, parse_constant=_invalid_constant)
                _validate_record(member, 'references')
                if (_canonical(member) != encoded or member['id'] != str(ident) or
                        _identity(str(stored_chat), member) != key or
                        (chat is not None and chat != stored_chat)):
                    raise ReceiverError('stored member metadata mismatch')
                chat = stored_chat
                members.append(member)
        except (ValueError, TypeError, RecursionError):
            raise ReceiverError('stored member is invalid') from None
        document = dict(schema='tgdata.telegram-post', version=1, post_id=key,
                        chat_id=str(chat), grouped_id=members[0]['grouped_id'], media_mode='references',
                        membership='single' if members[0]['grouped_id'] is None else 'unconfirmed', members=members)
        document['revision'] = _revision(document)
        return TelegramPost(document, max_members=self.max_members, max_bytes=maximum)

    def load(self, key):
        """Construct a bounded current view; None means no members for this key."""
        with self._open() as db:
            db.execute('BEGIN')
            self._validate(db)
            return self._load(db, key)

    def _match(self, db, chat, ident, key, encoded, digest):
        # SQL returns flags, not growing projections or corrupt payloads. Keys
        # and content use byte-exact comparisons; schema validation checks indexes.
        return db.execute(
            "SELECT typeof(record)='text' AND CAST(record AS BLOB)=?, "
            "typeof(post_id)='text' AND post_id COLLATE BINARY=?, "
            "typeof(record_sha256)='text' AND record_sha256 COLLATE BINARY=? "
            'FROM album_members WHERE collection=? AND chat_id=? AND message_id=?',
            (encoded.encode('utf-8'), key, digest, self.collection, chat, ident)).fetchone()

    def _previous(self, db, keys, input_bytes):
        stats, count, lower_bytes = {}, 0, input_bytes
        for key in keys:
            stats[key] = self._stats(db, key)
            count += stats[key][0]
            lower_bytes += stats[key][1]
            if count > self.max_members or lower_bytes > self.max_bytes:
                raise AlbumAssemblyError('prior views exceed member or byte limit')
        previous, used = {}, input_bytes
        for key in keys:
            post = self._load(db, key, max_bytes=self.max_bytes-used, stats=stats[key])
            previous[key] = post
            if post is not None:
                used += len(post.to_json().encode('utf-8'))
        return previous

    def accept(self, batch):
        """Commit new records or confirm accepted ones; return None, never a receipt.

        Confirmation checks only the immutable original input. A current post view
        is a separate load(), which can legitimately need a different view policy.
        """
        _limits(self.max_members, self.max_bytes)
        keys = album_post_ids(batch, max_bytes=self.max_bytes)
        value = batch.to_dict()
        if value['media_mode'] != 'references':
            raise AlbumAssemblyError('this receiver example accepts references only')
        if len(value['messages']) > self.max_members:
            raise AlbumAssemblyError('input exceeds max_members')
        chat, batch_id = int(value['chat_id']), value['batch_id']
        prepared = []
        for member in value['messages']:
            encoded = _canonical(member)
            prepared.append((chat, int(member['id']), _identity(value['chat_id'], member),
                             encoded, hashlib.sha256(encoded.encode('utf-8')).hexdigest()))
        with self._open() as db:
            db.execute('BEGIN IMMEDIATE')
            self._validate(db)
            received = db.execute('SELECT 1 FROM album_receipts WHERE collection=? AND batch_id=?',
                                  (self.collection, batch_id)).fetchone() is not None
            if received:
                for member in prepared:
                    if self._match(db, *member) != (1, 1, 1):
                        raise ReceiverError('accepted member is missing or inconsistent')
            else:
                absent = []
                for member in prepared:
                    match = self._match(db, *member)
                    if match is None:
                        absent.append(member)
                    elif match != (1, 1, 1):
                        raise ReceiverError('conflicting stored member')
                previous = self._previous(db, keys, len(batch.to_json().encode('utf-8')))
                assemble_albums(batch, previous=previous, max_members=self.max_members, max_bytes=self.max_bytes)
                for member in absent:
                    written = db.execute('INSERT INTO album_members VALUES (?, ?, ?, ?, ?, ?)',
                                         (self.collection,) + member).rowcount
                    if written != 1:
                        raise ReceiverError('member insert was not confirmed')
                written = db.execute('INSERT INTO album_receipts VALUES (?, ?)',
                                     (self.collection, batch_id)).rowcount
                if written != 1:
                    raise ReceiverError('receipt insert was not confirmed')
            db.commit()
        return None


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
    receiver.accept(remaining)
    await restarted.acknowledge(chat, remaining.batch_id)
    post = receiver.load(album_post_ids(remaining)[0])
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
