"""Observed albums: real SDK values, SQLite and source engines; no network.

Run: python -m tgdata.smoke_tests.test_42_album_assembly
Scripted source replies qualify local composition, not Telegram completeness.
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from telethon import TelegramClient, types
from telethon.extensions import BinaryReader
from telethon.sessions import MemorySession

import tgdata
from tgdata import MessageBatch, SQLiteSyncStore, ReadBudget, ReadBudgetExceeded, health
from tgdata.album import TelegramPost, AlbumAssemblyError, album_post_ids, assemble_albums
from tgdata.batch_engine import _record, BatchEngine
from tgdata.backfill import BackfillStartRequest, BackfillPrepareContext
from tgdata.backfill_engine import BackfillEngine
from tgdata.sync_engine import SyncEngine
from tgdata.sync_store import SyncConflictError
from examples.album_assembly import AlbumReceiver, ReceiverError, collect, demo


CHAT = -1000000000007
GROUP = (1 << 62) + 17
NOW = datetime(2026, 10, 14, tzinfo=timezone.utc)


def record(ident, text='', grouped=GROUP, media=None):
    message = types.Message(id=ident, peer_id=types.PeerChannel(7), date=NOW,
                            message=text, grouped_id=grouped, from_id=types.PeerUser(88), media=media)
    decoded = BinaryReader(bytes(message)).tgread_object()
    return _record(decoded, TelegramClient)


def batch(*records, chat=CHAT, stop='limit', mode='references', after=None):
    if after is None:
        after = min(int(row['id']) for row in records) - 1 if records else 0
    return MessageBatch._from_records(chat, after, sorted(records, key=lambda row: int(row['id'])), mode,
                                      stop if records else 'end')


def assemble(value, old=(), **options):
    by_key = {post.post_id: post for post in old}
    prior = {key: by_key.get(key) for key in album_post_ids(value, max_bytes=options.get('max_bytes', 16777216))}
    return assemble_albums(value, previous=prior, **options)


def resign(document):
    data = {key: value for key, value in document.items() if key != 'revision'}
    document['revision'] = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                          separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return document


class Facade:
    def __init__(self, engine):
        self.engine, self.acks = engine, []

    async def sync_group(self, chat, **options):
        return await self.engine.prepare(chat, **options)

    async def acknowledge_sync(self, chat, receipt):
        self.acks.append(receipt)
        return await self.engine.acknowledge(chat, receipt)


class AlbumTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='tgdata_album_test_')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for name in ('connect', 'connect_ex'):
            guard = patch.object(socket.socket, name, side_effect=AssertionError('network forbidden'))
            guard.start()
            self.addCleanup(guard.stop)

    def receiver(self, collection='one', **options):
        return AlbumReceiver(self.root / 'posts.sqlite3', collection, create=True, **options)

    def test_public_exports(self):
        for name in ('TelegramPost', 'AlbumAssemblyError', 'album_post_ids', 'assemble_albums'):
            self.assertIs(getattr(tgdata, name), globals()[name])
            self.assertIn(name, tgdata.__all__)
        self.assertEqual(tgdata.__version__, '0.1')

    def test_sdk_large_ids_captions_and_cross_chat(self):
        rows = (record(1, 'first'), record(2, 'second'))
        one, = assemble(batch(*rows))
        two, = assemble(batch(*rows, chat=CHAT - 1))
        self.assertNotEqual(one.post_id, two.post_id)
        self.assertEqual(one.grouped_id, GROUP)
        self.assertEqual(one.members, list(rows))
        self.assertEqual(one.membership, 'unconfirmed')
        self.assertEqual(one.to_dict()['grouped_id'], str(GROUP))
        self.assertEqual(one.member_ids, (1, 2))

    def test_every_partition_and_reverse_arrival_has_identical_bytes(self):
        rows = [record(i, 'caption' if i == 4 else '') for i in range(1, 5)]
        expected, = assemble(batch(*rows))
        for mask in range(8):
            parts, part = [], []
            for index, row in enumerate(rows):
                part.append(row)
                if index == 3 or mask & (1 << index):
                    parts.append(batch(*part)); part = []
            for order in (parts, list(reversed(parts))):
                old = ()
                for value in order:
                    old = assemble(value, old)
                self.assertEqual(old[0].to_json(), expected.to_json())

    def test_nonadjacent_album_singleton_and_service(self):
        service = record(4, '', grouped=None)
        service.update(kind='service', text=None, service_action='MessageActionChatEditTitle')
        raw = batch(record(1, 'caption'), record(2, 'separate', grouped=None), record(3), service)
        posts = assemble(raw)
        self.assertEqual([post.member_ids for post in posts], [(1, 3), (2,), (4,)])
        self.assertEqual([post.membership for post in posts], ['unconfirmed', 'single', 'single'])
        self.assertEqual(posts[-1].members[0], service)
        self.assertEqual(album_post_ids(raw), tuple(post.post_id for post in posts))

    def test_frozen_copying_and_json_roundtrip(self):
        post, = assemble(batch(record(1, 'private-caption')))
        wire = post.to_json()
        post.members[0]['text'] = 'mutated'
        post.to_dict()['members'].clear()
        with self.assertRaises(FrozenInstanceError):
            post._encoded = '{}'
        self.assertEqual(post.to_json(), wire)
        self.assertEqual(TelegramPost.from_json(wire.encode()), post)
        self.assertNotIn('private-caption', repr(post))

    def test_duplicate_input_keeps_revision_and_raw_bytes(self):
        raw = batch(record(1, 'one'))
        before = raw.to_json()
        first = assemble(raw)
        replay = assemble(raw, first)
        self.assertEqual(first, replay)
        self.assertEqual(raw.to_json(), before)
        self.assertEqual(raw.next_after_id, 1)

    def test_empty_batch_and_invalid_input(self):
        self.assertEqual(assemble_albums(batch(), previous={}), ())
        self.assertEqual(album_post_ids(batch()), ())
        for value in (None, {}, 'batch', True):
            with self.assertRaises(AlbumAssemblyError):
                album_post_ids(value)
        with self.assertRaises(TypeError):
            assemble_albums(batch(record(1)))

    def test_prior_mapping_is_required_exact_and_identity_checked(self):
        raw = batch(record(1)); key, = album_post_ids(raw)
        wrong, = assemble(batch(record(1), chat=CHAT - 1))
        for previous in (None, [], {}, {key: None, 'extra': None}, {'wrong': None}, {key: {}}, {key: wrong}):
            with self.assertRaises(AlbumAssemblyError):
                assemble_albums(raw, previous=previous)
        post, = assemble_albums(raw, previous={key: None})
        self.assertEqual(post.member_ids, (1,))

    def test_conflicting_record_refuses_without_mutation_or_content_leak(self):
        old = assemble(batch(record(1, 'first')))
        newer = batch(record(1, 'PRIVATE_CONFLICT'))
        before = (old[0].to_json(), newer.to_json())
        with self.assertRaises(AlbumAssemblyError) as caught:
            assemble(newer, old)
        self.assertEqual(before, (old[0].to_json(), newer.to_json()))
        self.assertNotIn('PRIVATE_CONFLICT', str(caught.exception))
        self.assertIsNone(health.classify(caught.exception))

    def test_mode_conflict_and_reference_receiver_refusal(self):
        reference = batch(record(1))
        downloaded = batch(record(2), mode='download')
        with self.assertRaises(AlbumAssemblyError):
            assemble(downloaded, assemble(reference))
        receiver = self.receiver()
        with self.assertRaises(AlbumAssemblyError):
            receiver.accept(downloaded)

    def test_json_malformed_duplicate_nonfinite_and_utf8(self):
        post, = assemble(batch(record(1)))
        for raw in ('', '{', 'null', '[]', '{"a":1,"a":1}', '{"a":NaN}', b'\xff', '\ud800', 1):
            with self.assertRaises(AlbumAssemblyError):
                TelegramPost.from_json(raw)
        duplicate = post.to_json().replace('"version":1', '"version":1,"version":1')
        with self.assertRaises(AlbumAssemblyError):
            TelegramPost.from_json(duplicate)

    def test_schema_identity_member_and_revision_corruption(self):
        post, = assemble(batch(record(1), record(2)))
        changes = [lambda d: d.update(version=True), lambda d: d.update(version=2),
                   lambda d: d.update(schema='other'), lambda d: d.update(extra=1),
                   lambda d: d.update(chat_id=CHAT), lambda d: d.update(grouped_id='01'),
                   lambda d: d.update(membership='complete'), lambda d: d.update(post_id='wrong'),
                   lambda d: d.update(media_mode='other'), lambda d: d.update(members=[]),
                   lambda d: d['members'].reverse(), lambda d: d['members'][0].update(grouped_id=None),
                   lambda d: d['members'][0].update(id=True), lambda d: d['members'][0].pop('sender')]
        for change in changes:
            value = post.to_dict(); change(value)
            with self.assertRaises(AlbumAssemblyError):
                TelegramPost(resign(value))
        changed = post.to_dict(); changed['members'][0]['text'] = 'tampered'
        with self.assertRaises(AlbumAssemblyError):
            TelegramPost(changed)

    def test_singleton_cannot_claim_multiple_members(self):
        post, = assemble(batch(record(1, grouped=None)))
        wire = post.to_dict(); wire['members'].append(record(2, grouped=None))
        with self.assertRaises(AlbumAssemblyError):
            TelegramPost(resign(wire))

    def test_member_limits_aggregate_and_no_partial_mutation(self):
        raw = batch(record(1), record(2, grouped=None))
        before = raw.to_json()
        with self.assertRaises(AlbumAssemblyError):
            assemble(raw, max_members=1)
        self.assertEqual(raw.to_json(), before)
        self.assertEqual(len(assemble(raw, max_members=2)), 2)

    def test_exact_utf8_byte_accounting_includes_prior_and_output(self):
        first = batch(record(1, 'ğ🙂'))
        old = assemble(first)
        raw = batch(record(2, 'é'))
        post, = assemble(raw, old)
        cost = sum(len(item.to_json().encode()) for item in (raw, old[0], post))
        self.assertEqual(assemble(raw, old, max_bytes=cost), (post,))
        with self.assertRaises(AlbumAssemblyError):
            assemble(raw, old, max_bytes=cost - 1)
        encoded = post.to_json().encode()
        self.assertEqual(TelegramPost.from_json(encoded, max_bytes=len(encoded)), post)
        with self.assertRaises(AlbumAssemblyError):
            TelegramPost.from_json(encoded, max_bytes=len(encoded)-1)

    def test_limit_configuration_validation(self):
        raw = batch(record(1))
        for invalid in (True, False, 0, -1, 1.5, '3', None):
            for name in ('max_members', 'max_bytes'):
                with self.assertRaises(AlbumAssemblyError):
                    assemble(raw, **{name: invalid})

    def test_stop_reason_and_window_do_not_certify_complete_membership(self):
        for reason in ('limit', 'end', 'interrupted'):
            raw = batch(record(101), stop=reason, after=100)
            post, = assemble(raw)
            self.assertEqual(post.membership, 'unconfirmed')
            self.assertEqual(post.member_ids, (101,))
            self.assertEqual(raw.after_id, 100)

    def test_real_cached_photo_download_and_blob_preservation(self):
        async def run():
            payload = b'actual cached photo bytes'
            photo = types.Photo(id=(1 << 62)+3, access_hash=(1 << 62)+7, file_reference=b'opaque',
                                date=NOW, sizes=[types.PhotoCachedSize(type='x', w=2, h=2, bytes=payload)], dc_id=2)
            message = types.Message(id=1, peer_id=types.PeerChannel(7), date=NOW, message='caption',
                                    grouped_id=GROUP, media=types.MessageMediaPhoto(photo=photo))
            message = BinaryReader(bytes(message)).tgread_object()
            client = TelegramClient(MemorySession(), 123, 'a'*32)
            try:
                target = io.BytesIO()
                await client.download_media(message, file=target)
                self.assertEqual(target.getvalue(), payload)
                row = _record(message, client)
                digest = hashlib.sha256(payload).hexdigest()
                (self.root / digest).write_bytes(target.getvalue())
                row['media']['blob'] = dict(sha256=digest, size=len(payload), path=digest)
                post, = assemble(batch(row, mode='download'))
                self.assertEqual(post.members[0]['media'], row['media'])
                self.assertEqual((self.root / post.members[0]['media']['blob']['path']).read_bytes(), payload)
                self.assertEqual(TelegramPost.from_json(post.to_json()), post)
            finally:
                await client.disconnect()
        asyncio.run(run())

    def test_actual_sdk_iterator_and_reader_clip_an_album_without_lookahead(self):
        async def run():
            room = types.Channel(id=7, title='Fixture', photo=types.ChatPhotoEmpty(), date=NOW,
                                 access_hash=7, megagroup=True)
            client = TelegramClient(MemorySession(), 123, 'a'*32)
            messages = [types.Message(id=i, peer_id=types.PeerChannel(7),
                       date=NOW+timedelta(seconds=i), message='caption' if i == 1 else '',
                       grouped_id=GROUP) for i in (1, 2, 3)]
            requests = []
            async def transport(sender, request, **options):
                requests.append(request)
                return types.messages.Messages(messages=list(reversed(messages)), topics=[], chats=[room], users=[])
            class Connection:
                @asynccontextmanager
                async def session(self):
                    yield client
            async def resolve(*args):
                return room
            try:
                with patch.object(client, '_call', side_effect=transport):
                    raw = await BatchEngine(Connection(), _resolve_entity=resolve).fetch_batch(CHAT,
                            limit=5, start_date=NOW+timedelta(seconds=2), end_date=NOW+timedelta(seconds=3))
                    before = raw.to_json(); calls = len(requests)
                    post, = assemble(raw)
                    self.assertEqual(post.member_ids, (2,))
                    self.assertEqual(post.membership, 'unconfirmed')
                    self.assertEqual(raw.stop_reason, 'end')
                    self.assertEqual(raw.next_after_id, 2)
                    self.assertEqual(raw.to_json(), before)
                    self.assertEqual(len(requests), calls)
                    self.assertEqual(calls, 1)
            finally:
                await client.disconnect()
        asyncio.run(run())

    def test_explicit_creation_reopen_and_collection_absence(self):
        path = self.root / 'posts.sqlite3'
        with self.assertRaises(ReceiverError):
            AlbumReceiver(path, 'one')
        self.assertFalse(path.exists())
        receiver = self.receiver()
        self.assertIsNone(receiver.load('absent'))
        with self.assertRaises(ReceiverError):
            AlbumReceiver(path, 'typo')
        with self.assertRaises(ReceiverError):
            AlbumReceiver(path, 'one', create=True)
        AlbumReceiver(path, 'two', create=True)
        path.unlink()
        with self.assertRaises(ReceiverError):
            receiver.accept(batch(record(1)))
        self.assertFalse(path.exists())

    def test_partial_schema_is_not_repaired(self):
        receiver = self.receiver()
        with sqlite3.connect(str(receiver.path)) as db:
            db.execute('DROP TABLE album_posts')
        for create in (False, True):
            with self.assertRaises(ReceiverError):
                AlbumReceiver(receiver.path, 'other', create=create)
        with sqlite3.connect(str(receiver.path)) as db:
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='album_posts'").fetchone())

    def test_schema_shape_version_and_corrupt_post_refuse(self):
        receiver = self.receiver(); raw = batch(record(1)); post, = receiver.accept(raw)
        with sqlite3.connect(str(receiver.path)) as db:
            db.execute('UPDATE album_posts SET value=?', ('{}',))
        with self.assertRaises(AlbumAssemblyError):
            receiver.accept(batch(record(2)))
        with sqlite3.connect(str(receiver.path)) as db:
            db.execute('UPDATE album_meta SET version=2')
        with self.assertRaises(ReceiverError):
            AlbumReceiver(receiver.path, 'one')

    def test_failed_lookup_does_not_mean_new_post(self):
        receiver = self.receiver(); first, = receiver.accept(batch(record(1)))
        with patch.object(receiver, '_load', side_effect=OSError('lookup unavailable')):
            with self.assertRaises(OSError):
                receiver.accept(batch(record(2)))
        self.assertEqual(receiver.load(first.post_id), first)

    def test_receipts_are_scoped_and_replay_keeps_later_growth(self):
        a = self.receiver('a'); b = AlbumReceiver(a.path, 'b', create=True)
        first = batch(record(1, 'caption')); second = batch(record(2))
        old, = a.accept(first); grown, = a.accept(second)
        self.assertEqual(a.accept(first), (grown,))
        other, = b.accept(first)
        self.assertEqual(other, old)
        with sqlite3.connect(str(a.path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM album_receipts').fetchone()[0], 3)

    def test_receipt_with_missing_accepted_member_refuses_repair(self):
        receiver = self.receiver(); raw = batch(record(1)); post, = receiver.accept(raw)
        with sqlite3.connect(str(receiver.path)) as db:
            db.execute('DELETE FROM album_posts')
        with self.assertRaises(ReceiverError):
            receiver.accept(raw)
        self.assertIsNone(receiver.load(post.post_id))

    def test_transaction_rolls_back_all_posts_and_marker(self):
        receiver = self.receiver()
        with sqlite3.connect(str(receiver.path)) as db:
            db.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON album_receipts BEGIN SELECT RAISE(ABORT, 'fault'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            receiver.accept(batch(record(1), record(2, grouped=None)))
        with sqlite3.connect(str(receiver.path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM album_posts').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM album_receipts').fetchone()[0], 0)

    def test_cleanup_preserves_original_failure(self):
        receiver = self.receiver()
        original = sqlite3.connect
        class Broken(sqlite3.Connection):
            def commit(self):
                raise RuntimeError('primary commit failure')
            def rollback(self):
                super().rollback()
                raise OSError('rollback failure')
            def close(self):
                super().close()
                raise OSError('close failure')
        def connect(*args, **kwargs):
            kwargs['factory'] = Broken
            return original(*args, **kwargs)
        with patch('examples.album_assembly.sqlite3.connect', side_effect=connect):
            with self.assertRaisesRegex(RuntimeError, 'primary commit failure'):
                receiver.accept(batch(record(1)))
        self.assertIsNone(receiver.load(album_post_ids(batch(record(1)))[0]))

    def test_real_process_loss_before_and_after_commit(self):
        receiver = self.receiver(); raw = batch(record(1, 'persist'))
        path = self.root / 'batch.json'; path.write_text(raw.to_json())
        for mode, code in (('before', 41), ('after', 42)):
            done = subprocess.run([sys.executable, __file__, '--crash', str(receiver.path), str(path), mode],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            self.assertEqual(done.returncode, code, done.stderr.decode())
            reopened = AlbumReceiver(receiver.path, 'one')
            stored = reopened.load(album_post_ids(raw)[0])
            if mode == 'before':
                self.assertIsNone(stored)
            else:
                self.assertEqual(stored.member_ids, (1,))
                self.assertEqual(reopened.accept(raw), (stored,))

    def test_competing_writer_refuses_then_reads_current_prior(self):
        a = self.receiver(); b = AlbumReceiver(a.path, 'one')
        original = a._load; attempted = []
        def load(db, key):
            with self.assertRaises(sqlite3.OperationalError):
                b.accept(batch(record(2)))
            attempted.append(True)
            return original(db, key)
        with patch.object(a, '_load', side_effect=load):
            a.accept(batch(record(1)))
        post, = b.accept(batch(record(2)))
        self.assertEqual(post.member_ids, (1, 2))
        self.assertEqual(attempted, [True])

    def test_raised_member_limit_survives_restart_and_replay(self):
        # More than one raw batch's maximum; no invented Telegram-size assertion.
        template = record(1)
        rows = [dict(template, id=str(i)) for i in range(1, 10002)]
        first, last = batch(*rows[:10000]), batch(rows[-1])
        receiver = self.receiver(max_members=10001)
        receiver.accept(first); post, = receiver.accept(last)
        reopened = AlbumReceiver(receiver.path, 'one', max_members=10001)
        self.assertEqual(reopened.load(post.post_id).member_ids, tuple(range(1, 10002)))
        self.assertEqual(reopened.accept(last), (post,))
        lower = AlbumReceiver(receiver.path, 'one')
        with self.assertRaises(AlbumAssemblyError):
            lower.accept(last)
        self.assertEqual(reopened.load(post.post_id), post)

    def test_daily_lost_ack_replay_and_continuation(self):
        async def run():
            reads = []
            async def reader(chat, **options):
                reads.append(options)
                ident = options['after_id'] + 1
                return batch(record(ident, 'caption' if ident == 1 else ''), after=options['after_id'])
            store = SQLiteSyncStore(self.root / 'source.sqlite3')
            engine = SyncEngine(reader, store); await engine.initialize(CHAT, after_id=0)
            receiver = self.receiver()
            first = await engine.prepare(CHAT, limit=1); receiver.accept(first)
            resumed = SyncEngine(reader, SQLiteSyncStore(store.path, create=False))
            receiver = AlbumReceiver(receiver.path, 'one')
            replay = await resumed.prepare(CHAT, limit=1)
            self.assertEqual(replay.to_json(), first.to_json()); self.assertEqual(len(reads), 1)
            receiver.accept(replay); await resumed.acknowledge(CHAT, replay.batch_id)
            second = await resumed.prepare(CHAT, limit=1); post, = receiver.accept(second)
            self.assertEqual((await resumed.status(CHAT)).after_id, 1)
            await resumed.acknowledge(CHAT, second.batch_id)
            self.assertEqual(post.member_ids, (1, 2)); self.assertEqual(len(reads), 2)
            self.assertEqual((await resumed.status(CHAT)).after_id, 2)
        asyncio.run(run())

    def test_backfill_fixed_window_replay_keeps_original_receipt(self):
        async def run():
            reads = []
            start, end = NOW - timedelta(hours=1), NOW + timedelta(hours=1)
            async def reader(chat, **options):
                reads.append(options)
                self.assertEqual((options['start_date'], options['end_date']), (start, end))
                ident = options['after_id'] + 1
                return batch(record(ident), after=options['after_id'], stop='limit' if ident == 1 else 'end')
            store = SQLiteSyncStore(self.root / 'backfill.sqlite3')
            engine = BackfillEngine(store, 'jobs', read_batch=reader, clock=lambda: NOW+timedelta(hours=2))
            request = BackfillStartRequest(collection_id='jobs', chat_id=CHAT, run_id='r1',
                        destination_id='one', origin='fresh', after_id=0, expected_predecessor=None,
                        start_date=start, end_date=end, batch_size=1, pause_seconds=0)
            status = (await engine.start(request, submission='new')).status
            turn = await engine.prepare(BackfillPrepareContext.from_status(status))
            receiver = self.receiver(); receiver.accept(turn.batch)
            resumed = BackfillEngine(SQLiteSyncStore(store.path, create=False), 'jobs', read_batch=reader, clock=lambda: NOW+timedelta(hours=2))
            replay = await resumed.prepare(BackfillPrepareContext.from_status(turn.status))
            self.assertEqual(replay.delivery, turn.delivery); self.assertEqual(len(reads), 1)
            receiver = AlbumReceiver(receiver.path, 'one'); receiver.accept(replay.batch)
            accepted = await resumed.acknowledge(replay.delivery)
            last = await resumed.prepare(BackfillPrepareContext.from_status(accepted))
            post, = receiver.accept(last.batch)
            finished = await resumed.acknowledge(last.delivery)
            self.assertEqual(finished.after_id, 2)
            self.assertEqual(finished.terminal_outcome, 'completed')
            self.assertEqual(post.membership, 'unconfirmed')
            self.assertEqual(post.member_ids, (1, 2))
        asyncio.run(run())

    def test_failed_publication_partial_data_is_not_acknowledged(self):
        async def run():
            actual = SQLiteSyncStore(self.root / 'source.sqlite3')
            raw = batch(record(1), after=0)
            async def reader(*args, **options):
                return raw
            engine = SyncEngine(reader, actual); await engine.initialize(CHAT, after_id=0)
            class Refuse:
                async def load(self, chat):
                    return await actual.load(chat)
                async def compare_and_swap(self, *args):
                    return False
            facade = Facade(SyncEngine(reader, Refuse()))
            receiver = self.receiver()
            with self.assertRaises(SyncConflictError) as error:
                await collect(facade, CHAT, receiver, max_batches=1)
            self.assertEqual([r['id'] for r in error.exception.partial_result.messages], ['1'])
            self.assertEqual(facade.acks, [])
            self.assertIsNone(receiver.load(album_post_ids(raw)[0]))
            self.assertIsNone((await engine.status(CHAT)).pending_batch_id)
        asyncio.run(run())

    def test_read_error_pending_replay_is_accepted_only_on_normal_return(self):
        async def run():
            raw = batch(record(1), after=0, stop='interrupted')
            failure = RuntimeError('source failed'); failure.partial_result = raw
            async def reader(*args, **options):
                raise failure
            store = SQLiteSyncStore(self.root / 'source.sqlite3')
            engine = SyncEngine(reader, store); await engine.initialize(CHAT, after_id=0)
            facade = Facade(engine); receiver = self.receiver()
            with self.assertRaises(RuntimeError):
                await collect(facade, CHAT, receiver, max_batches=1)
            self.assertEqual(facade.acks, [])
            self.assertEqual((await engine.status(CHAT)).pending_batch_id, raw.batch_id)
            await collect(facade, CHAT, receiver, max_batches=1)
            self.assertEqual(facade.acks, [raw.batch_id])
            self.assertEqual(receiver.load(album_post_ids(raw)[0]).membership, 'unconfirmed')
        asyncio.run(run())

    def test_cancellation_preserves_saved_receiver_and_source_cursor(self):
        async def run():
            receiver = self.receiver(); prior, = receiver.accept(batch(record(1)))
            async def reader(*args, **options):
                raise asyncio.CancelledError()
            store = SQLiteSyncStore(self.root / 'source.sqlite3')
            engine = SyncEngine(reader, store); await engine.initialize(CHAT, after_id=1)
            facade = Facade(engine)
            with self.assertRaises(asyncio.CancelledError):
                await collect(facade, CHAT, receiver, max_batches=1)
            self.assertEqual(receiver.load(prior.post_id), prior)
            self.assertEqual((await engine.status(CHAT)).after_id, 1)
            self.assertEqual(facade.acks, [])
        asyncio.run(run())

    def test_actual_exhausted_budget_preserves_prior_and_does_not_ack(self):
        async def run():
            budget = ReadBudget(self.root / 'budget.sqlite3', clock=lambda: 1000)
            budget.configure(88, daily_limit=1)
            budget._reserve(88, 1)
            receiver = self.receiver(); prior, = receiver.accept(batch(record(1)))
            async def reader(*args, **options):
                budget._reserve(88, 1)
                raise AssertionError('exhausted allowance must refuse')
            store = SQLiteSyncStore(self.root / 'source.sqlite3')
            engine = SyncEngine(reader, store); await engine.initialize(CHAT, after_id=1)
            facade = Facade(engine)
            with self.assertRaises(ReadBudgetExceeded):
                await collect(facade, CHAT, receiver, max_batches=1)
            self.assertEqual(budget.status(88).used, 1)
            self.assertEqual(receiver.load(prior.post_id), prior)
            self.assertEqual((await engine.status(CHAT)).after_id, 1)
            self.assertEqual(facade.acks, [])
        asyncio.run(run())

    def test_offline_demo_uses_actual_receiver_and_source_engine(self):
        asyncio.run(demo(self.root))


def crash(path, batch_path, mode):
    original = sqlite3.connect
    class Connection(sqlite3.Connection):
        def commit(self):
            if self.total_changes and mode == 'before':
                os._exit(41)
            super().commit()
            if self.total_changes and mode == 'after':
                os._exit(42)
    def connect(*args, **options):
        options['factory'] = Connection
        return original(*args, **options)
    with patch('examples.album_assembly.sqlite3.connect', side_effect=connect):
        AlbumReceiver(path, 'one').accept(MessageBatch.from_json(Path(batch_path).read_text()))
    raise AssertionError('commit fault did not fire')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--crash':
        crash(*sys.argv[2:])
    else:
        unittest.main()
