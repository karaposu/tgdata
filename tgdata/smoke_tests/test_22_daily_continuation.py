"""Offline daily continuation through real Telethon and persistent SQLite.

Run: python -m tgdata.smoke_tests.test_22_daily_continuation
No real config/session is opened; socket connections are forbidden.
"""

import asyncio
from dataclasses import FrozenInstanceError
import json
import logging
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import telethon
from telethon import errors
from tgdata import (
    TgData, MessageBatch, SQLiteSyncStore, SyncStatus, SyncError,
    SyncConfigurationError, SyncNotInitializedError, SyncConflictError,
    SyncStorageError, ReadBudgetExceeded, BatchStorageError,
)
from tgdata import health
import tgdata.sync_store as sync_storage
from tgdata.smoke_tests import test_19_message_batches as b


CHAT = -1000000000007
OTHER = -1000000000008
f = b.f


def store():
    return SQLiteSyncStore(f.TMP / ('sync_{}.sqlite3'.format(next(f.NUMBERS))))


def instance(progress, budget=None, events=None):
    tg = TgData(f.config(), session_store=f.Store(), read_budget=budget,
                sync_store=progress, health_callback=events.append if events is not None else None)
    client = tg.connection_engine._new_client()
    client.session.process_entities([f.room()])
    client._mb_entity_cache.set_self_user(f.ACCOUNT, False, 1)
    client._sender = sender = b.Sender()
    tg.connection_engine._primary_client = client
    f.CLIENTS.append(client)
    return tg, client, sender


def offline(progress):
    return TgData('/intentionally-missing-no-Telegram-config.ini', sync_store=progress)


class MemoryStore:
    """Independent async contract example; not used as durability evidence."""

    def __init__(self):
        self.rows = {}

    async def load(self, chat_id):
        await asyncio.sleep(0)
        return self.rows.get(chat_id)

    async def compare_and_swap(self, chat_id, expected, data):
        await asyncio.sleep(0)
        if self.rows.get(chat_id) != expected:
            return False
        self.rows[chat_id] = data
        return True


class FaultStore:
    def __init__(self, actual):
        self.actual = actual
        self.load_error = None
        self.write_error = None
        self.raise_after_commit = None
        self.conflict = False
        self.bad_return = False
        self.hold_load = False
        self.hold_commit = False
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def load(self, chat_id):
        if self.load_error is not None:
            raise self.load_error
        if self.hold_load:
            self.entered.set()
            await self.release.wait()
        return await self.actual.load(chat_id)

    async def compare_and_swap(self, chat_id, expected, data):
        if self.write_error is not None:
            raise self.write_error
        if self.bad_return:
            return 1
        if self.conflict:
            return False
        written = await self.actual.compare_and_swap(chat_id, expected, data)
        if self.raise_after_commit is not None:
            raise self.raise_after_commit
        if self.hold_commit:
            self.entered.set()
            await self.release.wait()
        return written


async def pending(progress=None, count=2, budget=None, events=None, mode='references', root=None):
    progress = progress or store()
    tg, client, sender = instance(progress, budget, events)
    await tg.initialize_sync(CHAT, after_id=100, media_mode=mode)
    batch = await tg.sync_group(CHAT, limit=count, download_media_to=root)
    return progress, tg, client, sender, batch


async def contract(progress):
    assert await progress.load(CHAT) is None
    assert await progress.compare_and_swap(CHAT, None, 'first') is True
    assert await progress.compare_and_swap(CHAT, None, 'other') is False
    assert await progress.compare_and_swap(CHAT, 'wrong', 'other') is False
    assert await progress.load(CHAT) == 'first'
    assert await progress.compare_and_swap(CHAT, 'first', 'second') is True
    assert await progress.load(CHAT) == 'second' and await progress.load(OTHER) is None


async def test_store_protocol_and_no_store():
    await contract(MemoryStore())
    durable = store()
    await contract(durable)
    assert await SQLiteSyncStore(durable.path).load(CHAT) == 'second'
    tg = offline(None)
    for operation in (tg.get_sync_status(CHAT), tg.initialize_sync(CHAT, after_id=0),
                      tg.sync_group(CHAT), tg.acknowledge_sync(CHAT, 'a' * 64)):
        await f.expect(SyncConfigurationError, operation)
    assert tg.connection_engine._primary_client is None
    plain, _, _ = instance(None)
    assert (await plain.get_message_batch(CHAT, after_id=100, limit=1)).next_after_id == 101


async def test_enrollment_validation_and_idempotence():
    progress = store()
    tg = offline(progress)
    for value in (None, '', '@room', str(CHAT), True, False, 0, 7, 1.5, -(1 << 63) - 1):
        await f.expect(SyncConfigurationError, tg.initialize_sync(value, after_id=0))
    for value in (-1, True, 1.5, '0', 1 << 31):
        await f.expect(SyncConfigurationError, tg.initialize_sync(CHAT, after_id=value))
    for value in (None, True, 'other', []):
        await f.expect(SyncConfigurationError, tg.initialize_sync(CHAT, after_id=0, media_mode=value))
    assert await tg.get_sync_status(CHAT) is None
    await f.expect(SyncNotInitializedError, tg.sync_group(CHAT))
    status = await tg.initialize_sync(CHAT, after_id=100)
    assert isinstance(status, SyncStatus) and status.after_id == status.initial_after_id == 100
    assert await tg.initialize_sync(CHAT, after_id=100) == status
    await f.expect(SyncConflictError, tg.initialize_sync(CHAT, after_id=101))
    await f.expect(SyncConflictError, tg.initialize_sync(CHAT, after_id=100, media_mode='download'))
    large = await tg.initialize_sync(-(1 << 63), after_id=0)
    assert large.to_dict()['chat_id'] == str(-(1 << 63))
    assert tg.connection_engine._primary_client is None


async def test_prepare_ack_and_daily_continuation():
    progress, tg, _, sender, batch = await pending(count=2)
    before = await tg.get_sync_status(CHAT)
    assert before.after_id == 100 and before.pending_next_after_id == 102
    assert before.pending_message_count == 2 and batch.after_id == 100
    status = await tg.acknowledge_sync(CHAT, batch.batch_id)
    assert status.after_id == 102 and status.pending_batch_id is None
    assert (await tg.initialize_sync(CHAT, after_id=100)).after_id == 102
    # A skipped day is simply more unseen IDs; no machine-clock window is used.
    b.script_messages(sender, [f.message(103), f.message(107), f.message(140)])
    next_batch = await tg.sync_group(CHAT, limit=3)
    assert next_batch.after_id == 102
    assert [row['id'] for row in next_batch.messages] == ['103', '107', '140']
    assert (await tg.get_sync_status(CHAT)).after_id == 102
    assert (await tg.acknowledge_sync(CHAT, next_batch.batch_id)).after_id == 140


async def test_restarted_pending_is_offline_exact_replay():
    progress, tg, _, sender, batch = await pending()
    original_calls = list(sender.calls)
    restarted = offline(SQLiteSyncStore(progress.path))
    replay = await restarted.sync_group(CHAT, limit=1)
    assert replay.to_json() == batch.to_json() and replay.batch_id == batch.batch_id
    assert sender.calls == original_calls and restarted.connection_engine._primary_client is None
    assert (await restarted.get_sync_status(CHAT)).after_id == 100
    assert (await restarted.acknowledge_sync(CHAT, replay.batch_id)).after_id == 102


async def test_acknowledgment_identity_and_old_retries():
    _, tg, _, _, first = await pending(count=1)
    for value in (None, '', True, 'A' * 64, 'a' * 63):
        await f.expect(SyncConfigurationError, tg.acknowledge_sync(CHAT, value))
    await f.expect(SyncConflictError, tg.acknowledge_sync(CHAT, 'a' * 64))
    first_ack = await tg.acknowledge_sync(CHAT, first.batch_id)
    assert await tg.acknowledge_sync(CHAT, first.batch_id) == first_ack
    second = await tg.sync_group(CHAT, limit=1)
    status = await tg.acknowledge_sync(CHAT, first.batch_id)
    assert status.after_id == 101 and status.pending_batch_id == second.batch_id
    await tg.acknowledge_sync(CHAT, second.batch_id)
    third = await tg.sync_group(CHAT, limit=1)
    await f.expect(SyncConflictError, tg.acknowledge_sync(CHAT, first.batch_id))
    assert (await tg.get_sync_status(CHAT)).pending_batch_id == third.batch_id
    await tg.initialize_sync(OTHER, after_id=100)
    await f.expect(SyncConflictError, tg.acknowledge_sync(OTHER, third.batch_id))
    assert (await tg.get_sync_status(OTHER)).after_id == 100


async def test_empty_end_and_maximum_cursor():
    progress = store()
    tg, _, sender = instance(progress)
    await tg.initialize_sync(CHAT, after_id=100)
    sender.script = [f.response([])]
    assert await tg.sync_group(CHAT) is None
    status = await tg.get_sync_status(CHAT)
    assert status.after_id == 100 and status.pending_batch_id is None
    sender.script = [f.response([f.message(101)]), f.response([])]
    batch = await tg.sync_group(CHAT, limit=2)
    assert batch.stop_reason == 'end'
    await tg.acknowledge_sync(CHAT, batch.batch_id)
    sender.script = [f.response([])]
    assert await tg.sync_group(CHAT) is None
    other = store()
    high, _, high_sender = instance(other)
    await high.initialize_sync(CHAT, after_id=(1 << 31) - 1)
    assert await high.sync_group(CHAT) is None and not high_sender.reads
    assert (await high.get_sync_status(CHAT)).after_id == (1 << 31) - 1


async def test_read_budget_prefix_is_pending():
    progress = store()
    budget, _ = f.ledger(3)
    tg, _, sender = instance(progress, budget)
    await tg.initialize_sync(CHAT, after_id=100)
    error = await f.expect(ReadBudgetExceeded, tg.sync_group(CHAT, limit=10))
    assert len(error.partial_result.messages) == 3
    status = await tg.get_sync_status(CHAT)
    assert status.after_id == 100 and status.pending_batch_id == error.partial_result.batch_id
    replay = await offline(SQLiteSyncStore(progress.path)).sync_group(CHAT)
    assert replay.to_json() == error.partial_result.to_json()
    assert len(sender.reads) == 1 and budget.status(f.ACCOUNT).used == 3
    await tg.acknowledge_sync(CHAT, replay.batch_id)
    budget.configure(f.ACCOUNT, 6)
    following = await tg.sync_group(CHAT, limit=3)
    assert [row['id'] for row in following.messages] == ['104', '105', '106']


async def test_original_read_errors_and_no_prefix():
    for original in (ConnectionError('synthetic transport'), errors.ChannelPrivateError(request=None)):
        progress = store()
        events = []
        tg, _, sender = instance(progress, events=events)
        await tg.initialize_sync(CHAT, after_id=100)
        sender.script = [f.response([f.message(n) for n in range(200, 100, -1)]), original]
        caught = await f.expect(type(original), tg.sync_group(CHAT, limit=101))
        assert caught is original and caught.partial_result.next_after_id == 200
        assert (await tg.get_sync_status(CHAT)).pending_batch_id == caught.partial_result.batch_id
        assert (await tg.get_sync_status(CHAT)).after_id == 100
        assert len(events) == (1 if isinstance(original, errors.ChannelPrivateError) else 0)
    progress = store()
    tg, _, sender = instance(progress)
    await tg.initialize_sync(CHAT, after_id=100)
    original = ConnectionError('before any records')
    sender.script = [original]
    assert await f.expect(ConnectionError, tg.sync_group(CHAT)) is original
    assert (await tg.get_sync_status(CHAT)).pending_batch_id is None


async def test_failed_prefix_save_exposes_both_failures():
    actual = store()
    progress = FaultStore(actual)
    budget, _ = f.ledger(3)
    tg, _, _ = instance(progress, budget)
    await tg.initialize_sync(CHAT, after_id=100)
    progress.write_error = OSError('private persistence details')
    error = await f.expect(SyncStorageError, tg.sync_group(CHAT, limit=10))
    assert isinstance(error.read_error, ReadBudgetExceeded)
    assert len(error.read_error.partial_result.messages) == 3
    assert error.__cause__ is None and health.classify(error) is None
    assert 'private' not in str(error)
    status = await offline(actual).get_sync_status(CHAT)
    assert status.after_id == 100 and status.pending_batch_id is None


async def test_backend_failures_conflicts_and_uncertain_ack():
    actual = store()
    progress = FaultStore(actual)
    tg, _, sender = instance(progress)
    await tg.initialize_sync(CHAT, after_id=100)
    progress.load_error = OSError('private details')
    await f.expect(SyncStorageError, tg.sync_group(CHAT))
    assert not sender.calls
    progress.load_error = None
    progress.conflict = True
    await f.expect(SyncConflictError, tg.sync_group(CHAT, limit=1))
    assert (await offline(actual).get_sync_status(CHAT)).pending_batch_id is None
    progress.conflict = False
    progress.bad_return = True
    await f.expect(SyncStorageError, tg.sync_group(CHAT, limit=1))
    progress.bad_return = False
    batch = await tg.sync_group(CHAT, limit=1)
    progress.raise_after_commit = OSError('reply lost after commit')
    await f.expect(SyncStorageError, tg.acknowledge_sync(CHAT, batch.batch_id))
    restarted = offline(SQLiteSyncStore(actual.path))
    status = await restarted.get_sync_status(CHAT)
    assert status.after_id == 101 and status.pending_batch_id is None
    assert await restarted.acknowledge_sync(CHAT, batch.batch_id) == status


async def test_custom_async_store_and_local_health_isolation():
    memory = MemoryStore()
    events = []
    tg, _, _ = instance(memory, events=events)
    await tg.initialize_sync(CHAT, after_id=100)
    batch = await tg.sync_group(CHAT, limit=1)
    assert (await offline(memory).sync_group(CHAT)).to_json() == batch.to_json()
    await offline(memory).acknowledge_sync(CHAT, batch.batch_id)
    progress = FaultStore(memory)
    progress.load_error = ValueError('private backend data')
    local = offline(progress)
    try:
        raise errors.ChannelPrivateError(request=None)
    except errors.ChannelPrivateError:
        error = await f.expect(SyncStorageError, local.get_sync_status(CHAT))
    assert error.__cause__ is None and error.__suppress_context__
    assert health.classify(error) is None and not events


async def test_corrupt_state_refuses_without_network():
    actual, _, _, _, _ = await pending(count=1)
    original = await actual.load(CHAT)
    mutations = [
        lambda d: d.update(version=True), lambda d: d.update(version=2),
        lambda d: d.update(extra=1), lambda d: d.pop('after_id'),
        lambda d: d.update(chat_id=str(OTHER)), lambda d: d.update(after_id='99'),
        lambda d: d.update(after_id=100), lambda d: d.update(initial_after_id='0100'),
        lambda d: d.update(last_acked_batch_id='a' * 64),
        lambda d: d.update(media_mode='download'),
        lambda d: d['pending']['messages'][0].update(text='changed after hashing'),
    ]
    raw_values = ['', '{}', 'null', '[]', '{', original.replace('"version":1', '"version":1,"version":1')]
    for mutate in mutations:
        value = json.loads(original)
        mutate(value)
        raw_values.append(json.dumps(value))
    current = original
    local = offline(actual)
    for raw in raw_values:
        assert await actual.compare_and_swap(CHAT, current, raw)
        await f.expect(SyncStorageError, local.get_sync_status(CHAT))
        await f.expect(SyncStorageError, local.sync_group(CHAT))
        assert await actual.load(CHAT) == raw
        current = raw
    assert await actual.compare_and_swap(CHAT, current, original)
    assert (await local.get_sync_status(CHAT)).after_id == 100
    assert local.connection_engine._primary_client is None


async def test_sqlite_schema_path_and_missing_database():
    for path in (None, '', ':memory:', True, 'file:memory?mode=memory'):
        f.rejected(SyncConfigurationError, lambda path=path: SQLiteSyncStore(path))
    actual = store()
    tg = offline(actual)
    await tg.initialize_sync(CHAT, after_id=100)
    with sqlite3.connect(actual.path) as db:
        db.execute('CREATE TABLE unrelated (value TEXT)')
        db.execute('INSERT INTO unrelated VALUES (?)', ('keep',))
        db.execute('UPDATE tgdata_sync_meta SET version = 99')
    await f.expect(SyncStorageError, tg.get_sync_status(CHAT))
    f.rejected(SyncStorageError, lambda: SQLiteSyncStore(actual.path))
    with sqlite3.connect(actual.path) as db:
        assert db.execute('SELECT value FROM unrelated').fetchone()[0] == 'keep'
        db.execute('UPDATE tgdata_sync_meta SET version = 1')
        db.execute('DROP TABLE tgdata_sync_meta')
    f.rejected(SyncStorageError, lambda: SQLiteSyncStore(actual.path))
    with sqlite3.connect(actual.path) as db:
        assert db.execute('SELECT COUNT(*) FROM tgdata_sync_state').fetchone()[0] == 1
    other = store()
    Path(other.path).unlink()
    await f.expect(SyncStorageError, other.load(CHAT))
    assert not Path(other.path).exists()
    # A damaged/foreign schema may preserve the names but lose NOT NULL.
    # An existing invalid row must never be confused with an absent key.
    malformed = store()
    with sqlite3.connect(malformed.path) as db:
        db.execute('DROP TABLE tgdata_sync_state')
        db.execute('CREATE TABLE tgdata_sync_state (chat_id INTEGER PRIMARY KEY, data TEXT)')
        db.execute('INSERT INTO tgdata_sync_state VALUES (?, NULL)', (CHAT,))
    await f.expect(SyncStorageError, offline(malformed).get_sync_status(CHAT))
    await f.expect(SyncStorageError, offline(malformed).initialize_sync(CHAT, after_id=0))
    await f.expect(SyncStorageError, malformed.compare_and_swap(CHAT, None, 'replacement'))
    with sqlite3.connect(malformed.path) as db:
        assert db.execute('SELECT data FROM tgdata_sync_state').fetchone()[0] is None


async def test_status_and_current_group_are_independent():
    _, tg, _, _, batch = await pending()
    tg.set_group(999)
    current = tg.current_group
    status = await tg.get_sync_status(CHAT)
    f.rejected(FrozenInstanceError, lambda: setattr(status, 'after_id', 999))
    changed = status.to_dict()
    changed['after_id'] = '999'
    assert (await tg.get_sync_status(CHAT)).after_id == 100
    assert json.loads(json.dumps(status.to_dict()))['chat_id'] == str(CHAT)
    await tg.sync_group(CHAT)
    await tg.acknowledge_sync(CHAT, batch.batch_id)
    assert tg.current_group is current and current.id == 999


async def test_media_replay_relocation_and_refusal():
    actual = store()
    tg, _, sender = instance(actual)
    await tg.initialize_sync(CHAT, after_id=100, media_mode='download')
    sender.files[b.ASSET_ID] = b.PAYLOAD
    b.script_messages(sender, [b.document()])
    first = b.directory()
    batch = await tg.sync_group(CHAT, limit=1, download_media_to=first)
    second = b.directory()
    for item in first.iterdir():
        shutil.copyfile(item, second / item.name)
    local = offline(SQLiteSyncStore(actual.path))
    assert (await local.sync_group(CHAT, download_media_to=second)).to_json() == batch.to_json()
    await f.expect(SyncConfigurationError, local.sync_group(CHAT))
    blob = batch.messages[0]['media']['blob']
    path = second / blob['path']
    path.write_bytes(b'x' * blob['size'])
    await f.expect(BatchStorageError, local.sync_group(CHAT, download_media_to=second))
    path.unlink()
    await f.expect(FileNotFoundError, local.sync_group(CHAT, download_media_to=second))
    path.symlink_to(first / blob['path'])
    await f.expect(BatchStorageError, local.sync_group(CHAT, download_media_to=second))
    assert (await local.get_sync_status(CHAT)).pending_batch_id == batch.batch_id
    path.unlink()
    shutil.copyfile(first / blob['path'], path)
    await local.acknowledge_sync(CHAT, batch.batch_id)
    assert path.read_bytes() == b.PAYLOAD and (first / blob['path']).exists()
    assert local.connection_engine._primary_client is None


async def test_reference_options_and_invalid_limits():
    actual = store()
    tg, _, sender = instance(actual)
    await tg.initialize_sync(CHAT, after_id=100)
    for limit in (0, -1, True, 1.5, '1', 10001):
        await f.expect(SyncConfigurationError, tg.sync_group(CHAT, limit=limit))
    await f.expect(SyncConfigurationError, tg.sync_group(CHAT, download_media_to=b.directory()))
    assert not sender.calls


async def wait_for_sender(sender, task):
    while not sender.pending:
        if task.done():
            await task
            raise AssertionError('SDK request did not stay pending')
        await asyncio.sleep(0)


async def test_real_overlap_and_cancelled_read():
    actual = store()
    tg, _, sender = instance(actual)
    await tg.initialize_sync(CHAT, after_id=100)
    sender.script = [f.PENDING]
    task = asyncio.create_task(tg.sync_group(CHAT, limit=1))
    await wait_for_sender(sender, task)
    assert not task.done()
    await f.expect(SyncConflictError, tg.sync_group(CHAT, limit=1))
    assert len(sender.reads) == 1
    task.cancel()
    await f.expect(asyncio.CancelledError, task)
    status = await tg.get_sync_status(CHAT)
    assert status.after_id == 100 and status.pending_batch_id is None
    # The in-flight guard must be released, not merely the SDK future cancelled.
    assert (await tg.sync_group(CHAT, limit=1)).next_after_id == 101


async def test_cancelled_store_load_and_committed_stage():
    actual = store()
    progress = FaultStore(actual)
    tg, _, sender = instance(progress)
    await tg.initialize_sync(CHAT, after_id=100)
    progress.hold_load = True
    task = asyncio.create_task(tg.sync_group(CHAT, limit=1))
    await progress.entered.wait()
    task.cancel()
    await f.expect(asyncio.CancelledError, task)
    assert not sender.calls
    progress.hold_load = False
    progress.entered.clear()
    progress.hold_commit = True
    task = asyncio.create_task(tg.sync_group(CHAT, limit=1))
    await progress.entered.wait()
    task.cancel()
    await f.expect(asyncio.CancelledError, task)
    restarted = offline(SQLiteSyncStore(actual.path))
    status = await restarted.get_sync_status(CHAT)
    assert status.after_id == 100 and status.pending_message_count == 1
    batch = await restarted.sync_group(CHAT)
    assert batch.next_after_id == 101
    await restarted.acknowledge_sync(CHAT, batch.batch_id)


async def test_batch_source_cursor_and_mode_validation():
    for change in (lambda d: d.update(chat_id=str(OTHER)),
                   lambda d: d.update(after_id='99'),
                   lambda d: d.update(media_mode='download')):
        actual = store()
        tg, _, sender = instance(actual)
        await tg.initialize_sync(CHAT, after_id=100)
        document = json.loads(b.GOLDEN)
        change(document)
        wrong = MessageBatch.from_json(b.signed(document))

        async def wrong_batch(*args, **kwargs):
            return wrong

        # Deliberately invalid input at the reader/continuation boundary; normal
        # composition is tested elsewhere through the real SDK and batch engine.
        tg.batch_engine.fetch_batch = wrong_batch
        await f.expect(SyncStorageError, tg.sync_group(CHAT))
        state = await tg.get_sync_status(CHAT)
        assert state.after_id == 100 and state.pending_batch_id is None and not sender.calls


async def test_offline_operations_do_not_recover_health():
    actual, tg, _, sender, batch = await pending(count=1)
    events = []
    tg._health.callback = events.append
    async with tg._health.call('existing_denial', group=CHAT):
        await health.report(errors.ChannelPrivateError(request=None), 'handled')
    assert str(CHAT) in tg._health.snapshot()['no_access']
    calls = list(sender.calls)
    count = len(events)
    await tg.get_sync_status(CHAT)
    await tg.initialize_sync(CHAT, after_id=100)
    await tg.sync_group(CHAT)
    await tg.acknowledge_sync(CHAT, batch.batch_id)
    assert sender.calls == calls and len(events) == count
    assert str(CHAT) in tg._health.snapshot()['no_access']


async def crash_ack(path, batch_id, mode):
    original_connect = sqlite3.connect

    class CrashConnection(sqlite3.Connection):
        def commit(self):
            if self.total_changes and mode == 'before':
                os._exit(31)
            super().commit()
            if self.total_changes and mode == 'after':
                os._exit(32)

    def connect(*args, **kwargs):
        kwargs['factory'] = CrashConnection
        return original_connect(*args, **kwargs)

    actual = SQLiteSyncStore(path)
    with patch.object(sync_storage.sqlite3, 'connect', side_effect=connect):
        await offline(actual).acknowledge_sync(CHAT, batch_id)
    raise AssertionError('child did not exit at commit boundary')


async def test_process_exit_at_actual_ack_commit():
    actual, _, _, _, batch = await pending(count=1)
    for mode, code, expected_cursor, pending_id in (
            ('before', 31, 100, batch.batch_id), ('after', 32, 101, None)):
        result = subprocess.run(
            [sys.executable, __file__, '--crash-ack', actual.path, batch.batch_id, mode],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20,
        )
        assert result.returncode == code, result.stderr
        restarted = offline(SQLiteSyncStore(actual.path))
        status = await restarted.get_sync_status(CHAT)
        assert status.after_id == expected_cursor and status.pending_batch_id == pending_id
    await offline(actual).acknowledge_sync(CHAT, batch.batch_id)


async def test_real_receiver_lost_acknowledgment():
    actual, tg, _, _, batch = await pending(count=2)
    destination = f.TMP / 'destination.sqlite3'
    with sqlite3.connect(str(destination)) as db:
        db.execute('CREATE TABLE batches (batch_id TEXT PRIMARY KEY)')
        db.execute('CREATE TABLE records (chat_id TEXT, message_id TEXT, '
                   'payload TEXT, PRIMARY KEY(chat_id, message_id))')

    def accept(value, lose_reply=False):
        with sqlite3.connect(str(destination)) as db:
            inserted = db.execute('INSERT OR IGNORE INTO batches VALUES (?)', (value.batch_id,)).rowcount
            if inserted:
                for message in value.messages:
                    db.execute('INSERT OR IGNORE INTO records VALUES (?, ?, ?)',
                               (str(value.chat_id), message['id'], json.dumps(message)))
        if lose_reply:
            raise ConnectionError('acceptance response lost')

    f.rejected(ConnectionError, lambda: accept(batch, lose_reply=True))
    assert (await tg.get_sync_status(CHAT)).after_id == 100
    restarted = offline(SQLiteSyncStore(actual.path))
    replay = await restarted.sync_group(CHAT)
    accept(replay)
    await restarted.acknowledge_sync(CHAT, replay.batch_id)
    with sqlite3.connect(str(destination)) as db:
        assert db.execute('SELECT COUNT(*) FROM batches').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM records').fetchone()[0] == 2
    assert (await restarted.get_sync_status(CHAT)).after_id == 102


async def test_sqlite_cleanup_precedence_and_safe_logs():
    actual, tg, _, _, batch = await pending(count=1)
    original_connect = sqlite3.connect
    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    class BrokenConnection:
        def __init__(self, raw, write_failure):
            self.raw, self.write_failure = raw, write_failure

        def __getattr__(self, name):
            return getattr(self.raw, name)

        def execute(self, sql, *args):
            if self.write_failure and sql.startswith('UPDATE tgdata_sync_state'):
                raise sqlite3.OperationalError('secret primary write failure')
            return self.raw.execute(sql, *args)

        def rollback(self):
            self.raw.rollback()
            raise sqlite3.OperationalError('secret rollback failure')

        def close(self):
            self.raw.close()
            raise sqlite3.OperationalError('secret close failure')

    def broken_write(*args, **kwargs):
        # Reads close normally, so the fault reaches the actual update transaction.
        raw = original_connect(*args, **kwargs)
        return BrokenConnection(raw, True) if kwargs.get('isolation_level') is None else raw

    handler = Capture()
    log = logging.getLogger('tgdata.sync_store')
    old = log.level, log.propagate
    log.setLevel(logging.WARNING)
    log.propagate = False
    log.addHandler(handler)
    try:
        # Invoke CAS directly to isolate the primary UPDATE failure from an
        # earlier load's deliberately broken close.
        raw = await actual.load(CHAT)
        with patch.object(sync_storage.sqlite3, 'connect', side_effect=broken_write):
            error = await f.expect(SyncStorageError, actual.compare_and_swap(CHAT, raw, 'replacement'))
        assert 'storage failed (OperationalError)' in str(error)
        assert [r.getMessage() for r in records] == [
            'Sync storage cleanup failed during rollback (OperationalError)',
            'Sync storage cleanup failed during close (OperationalError)',
        ]
        assert all(r.exc_info is None and 'secret' not in r.getMessage() for r in records)
        assert await actual.load(CHAT) == raw
        records.clear()
        with patch.object(sync_storage.sqlite3, 'connect', side_effect=lambda *a, **k:
                          BrokenConnection(original_connect(*a, **k), False)):
            try:
                raise errors.ChannelPrivateError(request=None)
            except errors.ChannelPrivateError:
                error = await f.expect(SyncStorageError, tg.get_sync_status(CHAT))
        assert 'close failed' in str(error) and not records
        assert health.classify(error) is None
        assert (await tg.get_sync_status(CHAT)).pending_batch_id == batch.batch_id
    finally:
        log.removeHandler(handler)
        log.setLevel(old[0])
        log.propagate = old[1]


async def test_backend_return_and_empty_pending_validation():
    class BadLoad(MemoryStore):
        async def load(self, chat_id):
            return b'not text'

    await f.expect(SyncStorageError, offline(BadLoad()).get_sync_status(CHAT))
    actual, _, _, _, batch = await pending(count=1)
    raw = await actual.load(CHAT)
    value = json.loads(raw)
    empty = json.loads(b.GOLDEN)
    empty.update(messages=[], next_after_id='100', stop_reason='end')
    value['pending'] = json.loads(b.signed(empty))
    assert await actual.compare_and_swap(CHAT, raw, json.dumps(value))
    await f.expect(SyncStorageError, offline(actual).get_sync_status(CHAT))


async def test_offline_example():
    root = f.TMP / 'example'
    script = Path(__file__).resolve().parents[2] / 'examples' / 'daily_continuation.py'
    result = subprocess.run([sys.executable, str(script), '--demo', '--directory', str(root)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert 'Replay used the same batch' in result.stdout and 'Stored messages: 4' in result.stdout


async def main():
    tests = [
        test_store_protocol_and_no_store, test_enrollment_validation_and_idempotence,
        test_prepare_ack_and_daily_continuation, test_restarted_pending_is_offline_exact_replay,
        test_acknowledgment_identity_and_old_retries, test_empty_end_and_maximum_cursor,
        test_read_budget_prefix_is_pending, test_original_read_errors_and_no_prefix,
        test_failed_prefix_save_exposes_both_failures,
        test_backend_failures_conflicts_and_uncertain_ack,
        test_custom_async_store_and_local_health_isolation,
        test_corrupt_state_refuses_without_network, test_sqlite_schema_path_and_missing_database,
        test_status_and_current_group_are_independent, test_media_replay_relocation_and_refusal,
        test_reference_options_and_invalid_limits, test_real_overlap_and_cancelled_read,
        test_cancelled_store_load_and_committed_stage, test_batch_source_cursor_and_mode_validation,
        test_offline_operations_do_not_recover_health, test_process_exit_at_actual_ack_commit,
        test_real_receiver_lost_acknowledgment, test_sqlite_cleanup_precedence_and_safe_logs,
        test_backend_return_and_empty_pending_validation, test_offline_example,
    ]
    print('Daily Continuation Tests — Telethon {}; offline SDK/SQLite'.format(telethon.__version__))
    logging.getLogger('tgdata').addHandler(logging.NullHandler())
    passed = 0
    with tempfile.TemporaryDirectory(prefix='tgdata_sync_test_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        f.TMP = Path(tmp)
        try:
            for test in tests:
                print('\nTEST:', test.__name__[5:])
                try:
                    await asyncio.wait_for(test(), timeout=40)
                except Exception:
                    traceback.print_exc()
                    print('✗ Failed')
                else:
                    passed += 1
                    print('✓ Passed')
        finally:
            for client in f.CLIENTS:
                await client.disconnect()
            f.CLIENTS.clear()
    print('\nPassed: {}/{}'.format(passed, len(tests)))
    return 0 if passed == len(tests) else 1


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--crash-ack':
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
                patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
            asyncio.run(crash_ack(sys.argv[2], sys.argv[3], sys.argv[4]))
    else:
        sys.exit(asyncio.run(main()))
