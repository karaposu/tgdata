"""Offline v1 batch contract, real Telethon 1.45.0 flows and local files.

Run: python -m tgdata.smoke_tests.test_19_message_batches
Synthetic replies replace the transport; iterators, downloads, budget admission
and batch preparation are real. No account config or Telegram socket is used.
"""

import asyncio
import builtins
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, ExitStack
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import telethon
from telethon import errors
from telethon.tl import functions, types

from tgdata import TgData, MessageBatch, BatchFormatError, BatchStorageError, ReadBudgetExceeded
from tgdata import health
from tgdata.batch_files import download_blob
import tgdata.batch_files as batch_files
from tgdata.message_engine import GroupAccessError
from tgdata.smoke_tests import test_18_read_budget as f


# Fixed independently with stdlib JSON/SHA-256 before running the implementation.
GOLDEN_ID = '0080da8c922378798db91cd36476d57bc4ea02f5cadb140fb23e650b77e9e614'
GOLDEN = r'{"after_id":"100","batch_id":"0080da8c922378798db91cd36476d57bc4ea02f5cadb140fb23e650b77e9e614","chat_id":"-1000000000007","media_mode":"references","messages":[{"date":"2023-11-14T22:13:20.000000Z","edit_date":null,"forward_from_id":"-1000000000009","grouped_id":"1152921504606847099","id":"101","kind":"message","media":null,"post_author":null,"reply_to_id":"99","sender":{"id":"88","name":"Author","username":null},"service_action":null,"text":"Hello 🌍\nline 2"}],"next_after_id":"101","schema":"tgdata.message-batch","stop_reason":"limit","version":1}'
NOW = datetime.fromtimestamp(f.NOW, timezone.utc)
PAYLOAD = b'content-addressed-media\x00' * 97
ASSET_ID = (1 << 60) + 91


class Sender(f.Sender):
    def __init__(self):
        super().__init__()
        self.files = {}
        self.file_calls = []
        self.file_script = []
        self.entity = None
        self.entity_error = None

    def send(self, request, ordered=False):
        if isinstance(request, (list, tuple)):
            return [self.send(item, ordered=ordered) for item in request]
        # Exercise the real wire-width constraints as well as SDK control flow.
        bytes(request)
        r = f.unwrap(request)
        result = None
        handled = False
        if isinstance(r, functions.upload.GetFileRequest):
            handled = True
            self.file_calls.append((r.location.id, r.offset, r.limit))
            if self.file_script:
                result = self.file_script.pop(0)
                if callable(result):
                    result = result(r)
            else:
                data = self.files[r.location.id]
                result = types.upload.File(types.storage.FileUnknown(), 0, data[r.offset:r.offset + r.limit])
        elif isinstance(r, functions.channels.GetChannelsRequest) and (self.entity or self.entity_error):
            handled = True
            result = self.entity_error or types.messages.Chats(chats=[self.entity])
        if not handled:
            return super().send(request, ordered=ordered)
        self.calls.append(type(r).__name__)
        future = asyncio.get_running_loop().create_future()
        if result is f.PENDING:
            self.pending.append(future)
        elif isinstance(result, BaseException):
            future.set_exception(result)
        else:
            future.set_result(result)
        return future


def instance(budget=None, events=None):
    tg, client, _ = f.instance(budget, events=events)
    client._sender = sender = Sender()
    return tg, client, sender


def directory():
    return Path(tempfile.mkdtemp(dir=str(f.TMP))).resolve()


def document(mid=101, *, asset_id=ASSET_ID, data=PAYLOAD, size=None, mime='application/octet-stream'):
    msg = f.message(mid)
    msg.media = types.MessageMediaDocument(document=types.Document(
        id=asset_id, access_hash=987654321987654321, file_reference=b'synthetic-file-reference',
        date=NOW, mime_type=mime, size=len(data) if size is None else size, dc_id=0,
        attributes=[types.DocumentAttributeFilename('../../metadata-only.bin')]))
    return msg


def photo(mid=101, *, sizes=None):
    msg = f.message(mid)
    msg.media = types.MessageMediaPhoto(photo=types.Photo(
        id=ASSET_ID, access_hash=987654321987654321, file_reference=b'synthetic-photo-reference',
        date=NOW, sizes=sizes if sizes is not None else [types.PhotoSize('w', 100, 100, len(PAYLOAD))],
        dc_id=0))
    return msg


def script_messages(sender, messages):
    sender.script = [f.response(list(reversed(messages)))]


def signed(document):
    """Independent re-signing ensures malformed tests reach field validation."""
    payload = {key: value for key, value in document.items() if key != 'batch_id'}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    document['batch_id'] = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    return json.dumps(document, ensure_ascii=False)


def malformed(change):
    value = json.loads(GOLDEN)
    change(value)
    f.rejected(BatchFormatError, lambda: MessageBatch.from_json(signed(value)))


async def test_golden_wire_and_no_enrichment():
    tg, _, sender = instance()
    msg = f.message(101, 'Hello 🌍\nline 2')
    msg.reply_to = types.MessageReplyHeader(reply_to_msg_id=99)
    msg.fwd_from = types.MessageFwdHeader(date=NOW, from_id=types.PeerChannel(9))
    msg.grouped_id = (1 << 60) + 123
    script_messages(sender, [msg])
    batch = await tg.get_message_batch('@synthetic_room', after_id=100, limit=1)
    assert batch.to_json() == GOLDEN and batch.batch_id == GOLDEN_ID
    assert batch.chat_id == -1000000000007 and batch.after_id == 100 and batch.next_after_id == 101
    assert sender.calls == ['ResolveUsernameRequest', 'GetHistoryRequest']
    assert not sender.file_calls


async def test_immutable_value_and_save_reload():
    raw = json.loads(GOLDEN)
    batch = MessageBatch(raw)
    raw['messages'][0]['text'] = 'mutated source'
    batch.to_dict()['messages'][0]['text'] = 'mutated copy'
    batch.messages[0]['sender']['name'] = 'mutated nested copy'
    f.rejected(FrozenInstanceError, lambda: setattr(batch, '_encoded', 'different'))
    assert batch.to_json() == GOLDEN
    for root in (directory(), directory()):
        path = batch.save(root)
        assert path.name == GOLDEN_ID + '.json'
        assert path.read_bytes() == GOLDEN.encode('utf-8')
        assert MessageBatch.from_json(path.read_bytes()).to_json() == GOLDEN
        assert batch.save(root) == path and list(root.iterdir()) == [path]


async def test_senderless_and_service_records():
    tg, _, sender = instance()
    missing = f.message(101, '')
    missing.from_id = None
    missing.out = True  # Telethon may infer self; the raw wire did not name an author.
    service = types.MessageService(id=102, peer_id=types.PeerChannel(7), date=NOW,
                                   action=types.MessageActionChatEditTitle('Renamed'))
    script_messages(sender, [missing, service])
    batch = await tg.get_message_batch(7, after_id=100, limit=2)
    assert [r['id'] for r in batch.messages] == ['101', '102']
    assert all(r['sender'] == {'id': None, 'name': None, 'username': None} for r in batch.messages)
    assert batch.messages[0]['text'] == '' and batch.messages[0]['kind'] == 'message'
    assert batch.messages[1]['kind'] == 'service'
    assert batch.messages[1]['service_action'] == 'MessageActionChatEditTitle'
    assert 'GetUsersRequest' not in sender.calls


async def test_dates_nulls_and_large_signed_ids():
    tg, _, sender = instance()
    msg = document(asset_id=-(1 << 60) + 9)
    msg.date = datetime(2024, 1, 2, 6, 4, 5, 123456, timezone(timedelta(hours=3)))
    msg.edit_date = datetime(2024, 1, 2, 3, 4, 6)  # naive SDK values are interpreted as UTC
    msg.from_id = types.PeerUser((1 << 60) + 3)
    msg.grouped_id = -(1 << 63)
    msg.post_author = '署名'
    script_messages(sender, [msg])
    batch = await tg.get_message_batch(7, after_id=100, limit=1)
    record = batch.messages[0]
    assert record['date'] == '2024-01-02T03:04:05.123456Z'
    assert record['edit_date'] == '2024-01-02T03:04:06.000000Z'
    assert record['sender'] == {'id': str((1 << 60) + 3), 'name': None, 'username': None}
    assert record['grouped_id'] == '-9223372036854775808' and record['post_author'] == '署名'
    assert record['media']['id'] == str(-(1 << 60) + 9) and record['media']['blob'] is None
    assert record['reply_to_id'] is None and record['forward_from_id'] is None
    assert MessageBatch.from_json(batch.to_json()).to_dict() == batch.to_dict()


async def test_strict_json_and_schema():
    for data in (b'\xff', '', '{}', '[]', 'null', 1, None, bytearray(b'{}')):
        f.rejected(BatchFormatError, lambda data=data: MessageBatch.from_json(data))
    for fragment in ('"version":true', '"version":2', '"version":1.0', '"version":NaN',
                     '"version":Infinity', '"version":1,"version":1'):
        f.rejected(BatchFormatError, lambda fragment=fragment: MessageBatch.from_json(
            GOLDEN.replace('"version":1', fragment)))
    f.rejected(BatchFormatError, lambda: MessageBatch.from_json(GOLDEN.replace('Hello', 'Changed')))
    f.rejected(BatchFormatError, lambda: MessageBatch.from_json(GOLDEN.replace('Hello', r'\ud800')))
    f.rejected(BatchFormatError, lambda: MessageBatch.from_json(GOLDEN.replace('"id":"101"', '"id":"101","id":"101"')))
    for key, value in [('schema', 'another'), ('version', 9), ('batch_id', 'A' * 64),
                       ('chat_id', '7'), ('chat_id', '-0'), ('chat_id', '-9223372036854775809'),
                       ('after_id', 100), ('after_id', '0100'), ('after_id', '-1'),
                       ('after_id', '2147483648'), ('next_after_id', '102'),
                       ('messages', {}), ('media_mode', 'future'), ('stop_reason', 'done')]:
        if key == 'batch_id':
            value_dict = json.loads(GOLDEN)
            value_dict[key] = value
            f.rejected(BatchFormatError, lambda: MessageBatch(value_dict))
        else:
            malformed(lambda doc, key=key, value=value: doc.__setitem__(key, value))
    malformed(lambda doc: doc.__setitem__('extra', None))
    malformed(lambda doc: doc.pop('media_mode'))
    malformed(lambda doc: doc['messages'][0].__setitem__('extra', None))
    malformed(lambda doc: doc['messages'][0].pop('sender'))
    value = json.loads(GOLDEN)
    value['messages'][0]['text'] = object()
    f.rejected(BatchFormatError, lambda: MessageBatch(value))


async def test_record_cursor_and_blob_constraints():
    for key, value in [('id', '100'), ('id', '0'), ('id', '+101'), ('id', '2147483648'),
                       ('date', '2024-01-01T00:00:00Z'), ('date', '2024-13-01T00:00:00.000000Z'),
                       ('edit_date', 123), ('reply_to_id', '0'), ('grouped_id', '0'),
                       ('forward_from_id', '9223372036854775808'), ('kind', 'future'),
                       ('service_action', 'unexpected'), ('text', {}), ('post_author', False)]:
        malformed(lambda doc, key=key, value=value: doc['messages'][0].__setitem__(key, value))
    malformed(lambda doc: doc['messages'][0]['sender'].__setitem__('id', '0'))
    malformed(lambda doc: doc['messages'][0]['sender'].__setitem__('name', []))
    malformed(lambda doc: doc['messages'].append(doc['messages'][0].copy()))
    malformed(lambda doc: doc.update(messages=[], next_after_id='100'))  # empty limit
    malformed(lambda doc: doc['messages'][0].__setitem__('kind', 'service'))
    tg, _, sender = instance()
    sender.files[ASSET_ID] = PAYLOAD
    script_messages(sender, [document()])
    batch = await tg.get_message_batch(7, after_id=100, limit=1, download_media_to=directory())
    for key, value in [('size', True), ('size', -1), ('downloadable', 1), ('kind', 'future'),
                       ('kind', 'poll'), ('id', None), ('blob', None)]:
        doc = batch.to_dict()
        doc['messages'][0]['media'][key] = value
        f.rejected(BatchFormatError, lambda doc=doc: MessageBatch.from_json(signed(doc)))
    for key, value in [('path', '../escape'), ('sha256', 'f' * 63), ('size', len(PAYLOAD) + 1)]:
        doc = batch.to_dict()
        doc['messages'][0]['media']['blob'][key] = value
        f.rejected(BatchFormatError, lambda doc=doc: MessageBatch.from_json(signed(doc)))
    doc = batch.to_dict()
    doc['media_mode'] = 'references'
    f.rejected(BatchFormatError, lambda: MessageBatch.from_json(signed(doc)))


async def test_ordered_pages_and_explicit_group():
    tg, _, sender = instance()
    tg.set_group(999)
    original = tg.current_group
    batch = await tg.get_message_batch(7, after_id=100, limit=205)
    assert [int(r['id']) for r in batch.messages] == list(range(101, 306))
    assert batch.next_after_id == 305 and batch.stop_reason == 'limit'
    assert [r[1] for r in sender.reads] == [100, 100, 5]
    assert tg.current_group is original and tg.current_group.id == 999
    assert all(r[3] < 0 for r in sender.reads)


async def test_end_empty_and_max_cursor():
    tg, _, sender = instance()
    sender.script = [f.response([f.message(102), f.message(101)]), f.response([])]
    batch = await tg.get_message_batch(7, after_id=100, limit=3)
    assert batch.stop_reason == 'end' and batch.next_after_id == 102 and len(batch.messages) == 2
    sender.script = [f.response([])]
    empty = await tg.get_message_batch(7, after_id=102, limit=3)
    assert empty.stop_reason == 'end' and empty.next_after_id == empty.after_id == 102 and not empty.messages
    count = len(sender.reads)
    terminal = await tg.get_message_batch(7, after_id=2147483647, limit=1)
    assert terminal.stop_reason == 'end' and terminal.next_after_id == 2147483647
    assert len(sender.reads) == count
    exact = await tg.get_message_batch(7, after_id=100, limit=1)
    assert exact.stop_reason == 'limit' and len(sender.reads) == count + 1


async def test_invalid_input_before_connection():
    tg = TgData(f.config(), session_store=f.Store())
    for group in (None, '', '   ', 0, False, 2.5, [], 1 << 63):
        error = await f.expect(BatchFormatError, tg.get_message_batch(group))
        assert error.partial_result is None
    for key, values in [('after_id', [-1, True, '1', 2.5, 1 << 31]),
                         ('limit', [0, -1, True, '1', 2.5, 10001]),
                         ('download_media_to', ['', False, b'path', 123])]:
        for value in values:
            await f.expect(BatchFormatError, tg.get_message_batch(7, **{key: value}))
    file = directory() / 'file'
    file.write_text('existing')
    await f.expect(FileExistsError, tg.get_message_batch(7, download_media_to=file))
    assert tg.connection_engine._primary_client is None


async def test_source_and_peer_validation():
    tg, _, sender = instance()
    error = await f.expect(BatchFormatError, tg.get_message_batch(f.ACCOUNT))
    assert error.partial_result is None and not sender.reads
    sender.entity = types.ChannelForbidden(7, 7, 'Forbidden', megagroup=True)
    error = await f.expect(GroupAccessError, tg.get_message_batch(7))
    assert getattr(error, 'partial_result', None) is None and not sender.reads
    sender.entity = None
    sender.entity_error = ConnectionError('resolution failed')
    error = await f.expect(ConnectionError, tg.get_message_batch(7))
    assert error is sender.entity_error and getattr(error, 'partial_result', None) is None
    sender.entity_error = None
    bad = f.message(102)
    bad.peer_id = types.PeerChannel(8)
    script_messages(sender, [f.message(101), bad])
    error = await f.expect(BatchFormatError, tg.get_message_batch(7, after_id=100, limit=2))
    assert error.partial_result.next_after_id == 101 and len(error.partial_result.messages) == 1


async def test_budget_prefix_empty_and_resume():
    events = []
    budget, _ = f.ledger(3)
    tg, _, sender = instance(budget, events)
    error = await f.expect(ReadBudgetExceeded, tg.get_message_batch(7, after_id=100, limit=10))
    partial = error.partial_result
    assert isinstance(partial, MessageBatch) and partial.stop_reason == 'interrupted'
    assert [r['id'] for r in partial.messages] == ['101', '102', '103']
    assert partial.next_after_id == 103 and budget.status(f.ACCOUNT).used == 3
    assert len(sender.reads) == 1 and not events
    empty = await f.expect(ReadBudgetExceeded, tg.get_message_batch(7, after_id=103, limit=3))
    assert empty.partial_result.messages == [] and empty.partial_result.next_after_id == 103
    budget.configure(f.ACCOUNT, 6)
    resumed = await tg.get_message_batch(7, after_id=partial.next_after_id, limit=3)
    assert [r['id'] for r in resumed.messages] == ['104', '105', '106']
    assert budget.status(f.ACCOUNT).used == 6 and not events


async def test_original_network_and_rpc_errors():
    for original in (ConnectionError('transport failed'), errors.ChannelPrivateError(request=f.history())):
        events = []
        tg, _, sender = instance(events=events)
        sender.script = [f.response([f.message(n) for n in range(200, 100, -1)]), original]
        error = await f.expect(type(original), tg.get_message_batch(7, after_id=100, limit=101))
        assert error is original and error.partial_result.next_after_id == 200
        assert len(error.partial_result.messages) == 100 and error.partial_result.stop_reason == 'interrupted'
        assert len(sender.reads) == 2
        if isinstance(original, errors.ChannelPrivateError):
            assert len(events) == 1 and events[0]['verdict'] == 'no access'
            assert events[0]['call'] == 'get_message_batch'
        else:
            assert not events


async def test_bad_record_preserves_prefix():
    events = []
    tg, _, sender = instance(events=events)
    bad = f.message(102)
    bad.message = object()
    script_messages(sender, [f.message(101), bad])
    error = await f.expect(BatchFormatError, tg.get_message_batch(7, after_id=100, limit=2))
    assert error.partial_result.next_after_id == 101 and len(error.partial_result.messages) == 1
    assert not events and health.classify(error) is None


async def test_document_bytes_dedup_and_root_independence():
    roots = [directory(), directory()]
    batches = []
    digest = hashlib.sha256(PAYLOAD).hexdigest()
    for root in roots:
        tg, _, sender = instance()
        sender.files = {ASSET_ID: PAYLOAD, ASSET_ID + 1: PAYLOAD}
        script_messages(sender, [document(), document(102, asset_id=ASSET_ID + 1)])
        batch = await tg.get_message_batch(7, after_id=100, limit=2, download_media_to=root)
        batches.append(batch)
        assert sorted(p.name for p in root.iterdir()) == [digest]
        assert (root / digest).read_bytes() == PAYLOAD and len(sender.file_calls) == 2
        for record in batch.messages:
            assert record['media']['blob'] == {'sha256': digest, 'size': len(PAYLOAD), 'path': digest}
            assert record['media']['file_name'] == '../../metadata-only.bin'
        assert 'access_hash' not in batch.to_json() and 'file_reference' not in batch.to_json()
        assert str(root) not in batch.to_json()
    assert batches[0].batch_id == batches[1].batch_id


async def test_photo_variants_and_unsupported_media():
    variants = [None, [types.PhotoCachedSize('w', 100, 100, PAYLOAD)],
                [types.PhotoSizeProgressive('w', 100, 100, [1, len(PAYLOAD)])]]
    for sizes in variants:
        tg, _, sender = instance()
        sender.files[ASSET_ID] = PAYLOAD
        script_messages(sender, [photo(sizes=sizes)])
        root = directory()
        batch = await tg.get_message_batch(7, after_id=100, limit=1, download_media_to=root)
        media = batch.messages[0]['media']
        assert media['kind'] == 'photo' and media['mime_type'] is None
        assert media['size'] == len(PAYLOAD) and (root / media['blob']['path']).read_bytes() == PAYLOAD
        assert len(sender.file_calls) == (0 if sizes and isinstance(sizes[0], types.PhotoCachedSize) else 1)
    tg, _, sender = instance()
    unsupported = f.message(101)
    unsupported.media = types.MessageMediaWebPage(types.WebPageEmpty(123))
    script_messages(sender, [unsupported, f.message(102, media=True)])
    root = directory()
    batch = await tg.get_message_batch(7, after_id=100, limit=2, download_media_to=root)
    assert [r['media']['kind'] for r in batch.messages] == ['webpage', 'photo']
    assert all(not r['media']['downloadable'] and r['media']['blob'] is None for r in batch.messages)
    assert not sender.file_calls and not list(root.iterdir())


async def test_changed_bytes_change_identity():
    tg, _, sender = instance()
    root = directory()
    batches = []
    for data in (PAYLOAD, b'changed contents'):
        sender.files[ASSET_ID] = data
        script_messages(sender, [document(data=data)])
        batches.append(await tg.get_message_batch(7, after_id=100, limit=1, download_media_to=root))
    assert batches[0].batch_id != batches[1].batch_id
    paths = [batch.messages[0]['media']['blob']['path'] for batch in batches]
    assert paths[0] != paths[1] and len(list(root.iterdir())) == 2 and len(sender.file_calls) == 2
    assert (root / paths[0]).read_bytes() == PAYLOAD


async def test_missing_and_truncated_media():
    for prefix_count in (0, 1):
        for msg in (photo(sizes=[]), document(size=len(PAYLOAD) + 10)):
            events = []
            tg, _, sender = instance(events=events)
            sender.files[ASSET_ID] = PAYLOAD
            msg.id = 101 + prefix_count
            prefix = [f.message(101)] if prefix_count else []
            script_messages(sender, prefix + [msg])
            root = directory()
            error = await f.expect(BatchStorageError, tg.get_message_batch(
                7, after_id=100, limit=1 + prefix_count, download_media_to=root))
            assert len(error.partial_result.messages) == prefix_count
            assert error.partial_result.next_after_id == 100 + prefix_count
            assert not list(root.iterdir()) and not events


async def test_existing_blob_integrity():
    digest = hashlib.sha256(PAYLOAD).hexdigest()
    for kind in ('corrupt', 'symlink', 'directory'):
        root = directory()
        destination = root / digest
        if kind == 'corrupt':
            destination.write_bytes(b'x' * len(PAYLOAD))
        elif kind == 'symlink':
            target = directory() / 'target'
            target.write_bytes(PAYLOAD)
            destination.symlink_to(target)
        else:
            destination.mkdir()
        tg, _, sender = instance()
        sender.files[ASSET_ID] = PAYLOAD
        script_messages(sender, [document()])
        error = await f.expect(BatchStorageError, tg.get_message_batch(
            7, after_id=100, limit=1, download_media_to=root))
        assert error.partial_result.next_after_id == 100 and list(root.iterdir()) == [destination]
        if kind == 'corrupt':
            assert destination.read_bytes() == b'x' * len(PAYLOAD)
        elif kind == 'symlink':
            assert destination.is_symlink() and target.read_bytes() == PAYLOAD
        else:
            assert destination.is_dir()


async def test_manifest_integrity():
    batch = MessageBatch.from_json(GOLDEN)
    root = directory()
    path = batch.save(root)
    path.write_bytes(b'x' * len(GOLDEN.encode('utf-8')))
    f.rejected(BatchStorageError, lambda: batch.save(root))
    assert path.read_bytes() == b'x' * len(GOLDEN.encode('utf-8')) and list(root.iterdir()) == [path]
    f.rejected(BatchFormatError, lambda: MessageBatch.from_json(path.read_bytes()))
    f.rejected(BatchStorageError, lambda: batch.save(None))


async def test_concurrent_complete_publication():
    root = directory()

    async def writer(output):
        output.write(PAYLOAD[:100])
        await asyncio.sleep(0)
        output.write(PAYLOAD[100:])
        return output

    def work(_):
        return asyncio.run(download_blob(root, writer, expected_size=len(PAYLOAD)))

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(work, range(24)))
    assert all(result == results[0] for result in results)
    assert [p.name for p in root.iterdir()] == [hashlib.sha256(PAYLOAD).hexdigest()]
    assert (root / results[0]['path']).read_bytes() == PAYLOAD


async def test_cancelled_download_cleanup():
    tg, _, sender = instance()
    data = b'x' * (256 * 1024)
    sender.files[ASSET_ID] = data
    sender.file_script = [lambda r: types.upload.File(types.storage.FileUnknown(), 0, data[:r.limit]), f.PENDING]
    script_messages(sender, [document(data=data)])
    root = directory()
    task = asyncio.create_task(tg.get_message_batch(7, after_id=100, limit=1, download_media_to=root))
    while not sender.pending:
        if task.done():
            await task
            raise AssertionError('download finished before its pending second chunk')
        await asyncio.sleep(0)
    assert len(sender.file_calls) == 2 and any(p.name.startswith('.tgdata-media-') for p in root.iterdir())
    task.cancel()
    await f.expect(asyncio.CancelledError, task)
    assert not list(root.iterdir())


async def test_media_refresh_obeys_budget():
    for error_type in (errors.FileReferenceExpiredError, errors.FilerefUpgradeNeededError):
        budget, _ = f.ledger(1)
        events = []
        tg, _, sender = instance(budget, events)
        script_messages(sender, [document()])
        sender.file_script = [error_type(request=None)]
        root = directory()
        error = await f.expect(ReadBudgetExceeded, tg.get_message_batch(
            7, after_id=100, limit=1, download_media_to=root))
        assert error.partial_result.messages == [] and error.partial_result.next_after_id == 100
        assert budget.status(f.ACCOUNT).used == 1 and len(sender.reads) == 1
        assert len(sender.file_calls) == 1 and not list(root.iterdir()) and not events


async def test_local_errors_do_not_inherit_health_verdicts():
    try:
        raise errors.ChannelPrivateError(request=None)
    except errors.ChannelPrivateError:
        format_error = f.rejected(BatchFormatError, lambda: MessageBatch.from_json('{}'))
        storage_error = f.rejected(BatchStorageError, lambda: MessageBatch.from_json(GOLDEN).save(None))
    assert health.classify(format_error) is None and health.classify(storage_error) is None


async def test_saved_replay_and_ack_order():
    # A receiver stand-in illustrates the caller protocol; no deployed receiver is claimed.
    accepted = set()
    writes = []

    def receive(data, lose_ack=False):
        batch = MessageBatch.from_json(data)
        if batch.batch_id not in accepted:
            accepted.add(batch.batch_id)
            writes.extend(batch.messages)
        if lose_ack:
            raise ConnectionError('acknowledgment lost after acceptance')
        return batch.batch_id

    batch = MessageBatch.from_json(GOLDEN)
    cursor = batch.after_id
    saved = batch.save(directory())
    f.rejected(ConnectionError, lambda: receive(saved.read_bytes(), lose_ack=True))
    assert cursor == 100 and len(writes) == 1
    replay = MessageBatch.from_json(saved.read_bytes())
    ack = receive(replay.to_json())
    assert ack == replay.batch_id
    cursor = replay.next_after_id
    assert cursor == 101 and accepted == {GOLDEN_ID} and len(writes) == 1


async def test_legacy_dataframe_and_media_contracts():
    tg, _, sender = instance()
    frame = await tg.get_messages(7, after_id=100, limit=2)
    assert isinstance(frame, pd.DataFrame) and frame['MessageId'].tolist() == [101, 102]
    sender.files[ASSET_ID] = PAYLOAD
    script_messages(sender, [document(mime='image/png')])
    root = directory()
    result = await tg.download_media_by_id(7, [101], output_dir=str(root))
    assert Path(result[101]).name == '7_101.png' and Path(result[101]).read_bytes() == PAYLOAD


class FileFault:
    """Real file with a supplied I/O failure; SDK and publisher stay real."""

    def __init__(self, raw, faults):
        self.raw, self.faults = raw, faults

    def __getattr__(self, name):
        value = getattr(self.raw, name)
        if name not in self.faults:
            return value

        def fail(*args, **kwargs):
            if name == 'close':
                self.raw.close()
            raise self.faults[name]
        return fail


@contextmanager
def temporary_faults(faults):
    original = batch_files.tempfile.NamedTemporaryFile
    opened = []

    def create(*args, **kwargs):
        raw = original(*args, **kwargs)
        opened.append(raw)
        return FileFault(raw, faults)

    with patch.object(batch_files.tempfile, 'NamedTemporaryFile', side_effect=create):
        try:
            yield opened
        finally:
            for raw in opened:
                raw.close()


@contextmanager
def verification_faults(faults):
    opened = []

    def open_file(*args, **kwargs):
        raw = builtins.open(*args, **kwargs)
        opened.append(raw)
        return FileFault(raw, faults)

    with patch.object(batch_files, 'open', side_effect=open_file, create=True):
        try:
            yield opened
        finally:
            for raw in opened:
                raw.close()


@contextmanager
def cleanup_logs(explode=None):
    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record)
            if explode is not None:
                raise explode

    records = []
    handler = Capture()
    logger = logging.getLogger('tgdata.batch_files')
    previous = logger.level, logger.propagate
    logger.setLevel(logging.WARNING)
    logger.propagate = False
    logger.addHandler(handler)
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous[0])
        logger.propagate = previous[1]


async def test_native_path_error_under_handled_rpc():
    events = []
    tg, _, sender = instance(events=events)
    root = directory()
    ordinary_file = root / 'not-a-directory'
    ordinary_file.write_bytes(b'keep me')
    try:
        raise errors.ChannelPrivateError(request=None)
    except errors.ChannelPrivateError:
        caught = await f.expect(FileExistsError, tg.get_message_batch(7, download_media_to=ordinary_file))
    assert caught.__suppress_context__ and caught.__cause__ is None
    assert health.classify(caught) is None and not events and not sender.calls
    assert getattr(caught, 'partial_result', None) is None and ordinary_file.read_bytes() == b'keep me'


async def test_local_io_provenance_matrix():
    cases = ('resolve', 'mkdir', 'create', 'write', 'flush', 'fsync', 'link',
             'lstat', 'verify_open', 'fstat', 'verify_read', 'close')
    for operation in cases:
        events = []
        tg, _, sender = instance(events=events)
        root = directory()
        existing = operation in ('lstat', 'verify_open', 'fstat', 'verify_read')
        digest = hashlib.sha256(PAYLOAD).hexdigest()
        if existing:
            (root / digest).write_bytes(PAYLOAD)
        sender.files[ASSET_ID] = PAYLOAD
        script_messages(sender, [f.message(101), document(102)])
        fault = OSError('secret local fault: ' + operation)
        with ExitStack() as stack:
            if operation in ('resolve', 'mkdir', 'lstat'):
                stack.enter_context(patch.object(Path, operation, side_effect=fault))
            elif operation == 'create':
                stack.enter_context(patch.object(batch_files.tempfile, 'NamedTemporaryFile', side_effect=fault))
            elif operation in ('write', 'flush', 'close'):
                stack.enter_context(temporary_faults({operation: fault}))
            elif operation == 'verify_open':
                stack.enter_context(patch.object(batch_files, 'open', side_effect=fault, create=True))
            elif operation == 'verify_read':
                stack.enter_context(verification_faults({'read': fault}))
            else:
                stack.enter_context(patch.object(batch_files.os, operation, side_effect=fault))
            try:
                raise errors.ChannelPrivateError(request=None)
            except errors.ChannelPrivateError:
                caught = await f.expect(OSError, tg.get_message_batch(
                    7, after_id=100, limit=2, download_media_to=root))
        assert caught is fault, operation
        assert caught.__suppress_context__ and caught.__cause__ is None, operation
        assert health.classify(caught) is None and not events, operation
        if operation in ('resolve', 'mkdir'):
            assert not sender.calls and getattr(caught, 'partial_result', None) is None
        else:
            assert caught.partial_result.next_after_id == 101 and len(caught.partial_result.messages) == 1
        assert not any(path.name.startswith('.tgdata-') for path in root.iterdir()), operation
        if existing:
            assert (root / digest).read_bytes() == PAYLOAD
        else:
            assert not list(root.iterdir()), operation


async def test_sdk_transport_cause_is_preserved():
    events = []
    tg, _, sender = instance(events=events)
    reason = errors.ChannelPrivateError(request=None)
    original = ConnectionError('current SDK transport wrapper')
    original.__cause__ = reason
    sender.file_script = [original]
    script_messages(sender, [f.message(101), document(102)])
    root = directory()
    caught = await f.expect(ConnectionError, tg.get_message_batch(
        7, after_id=100, limit=2, download_media_to=root))
    assert caught is original and caught.__cause__ is reason
    assert caught.partial_result.next_after_id == 101 and not list(root.iterdir())
    assert len(events) == 1 and events[0]['verdict'] == 'no access'
    assert events[0]['error'] == 'CHANNEL_PRIVATE' and events[0]['call'] == 'get_message_batch'


async def test_primary_rpc_survives_real_cleanup_denial():
    events = []
    tg, _, sender = instance(events=events)
    root = directory()
    original = errors.ChannelPrivateError(request=None)
    script_messages(sender, [f.message(101), document(102)])

    def refuse_file(request):
        root.chmod(0o500)
        return original

    sender.file_script = [refuse_file]
    try:
        with cleanup_logs() as records:
            caught = await f.expect(errors.ChannelPrivateError, tg.get_message_batch(
                7, after_id=100, limit=2, download_media_to=root))
        assert caught is original and caught.partial_result.next_after_id == 101
        assert len(events) == 1 and events[0]['verdict'] == 'no access'
        assert len(records) == 1 and records[0].getMessage() == 'Batch artifact cleanup failed during unlink (PermissionError)'
        assert all(path.name.startswith('.tgdata-media-') for path in root.iterdir())
        assert len(list(root.iterdir())) == 1
    finally:
        # Test teardown restores access; production cannot promise removal
        # when the filesystem refuses it.
        root.chmod(0o700)


async def test_secondary_failures_and_logging_cannot_mask_primary():
    for logger_error in (None, RuntimeError('secret handler error'), asyncio.CancelledError('secret handler cancellation')):
        events = []
        tg, _, sender = instance(events=events)
        root = directory()
        original = errors.ChannelPrivateError(request=None)
        close_error = PermissionError('secret close details')
        unlink_error = PermissionError('secret unlink details')
        sender.file_script = [original]
        script_messages(sender, [f.message(101), document(102)])
        with temporary_faults({'close': close_error}) as opened, \
                patch.object(batch_files.os, 'unlink', side_effect=unlink_error) as unlink, \
                cleanup_logs(logger_error) as records:
            caught = await f.expect(errors.ChannelPrivateError, tg.get_message_batch(
                7, after_id=100, limit=2, download_media_to=root))
        assert caught is original and caught.partial_result.next_after_id == 101
        assert unlink.call_count == 1 and all(raw.closed for raw in opened)
        assert len(events) == 1 and events[0]['verdict'] == 'no access'
        assert [r.getMessage() for r in records] == [
            'Batch artifact cleanup failed during close (PermissionError)',
            'Batch artifact cleanup failed during unlink (PermissionError)',
        ]
        assert all(r.exc_info is None and 'secret' not in r.getMessage() and str(root) not in r.getMessage() for r in records)


async def test_cancellation_survives_cleanup_denial():
    events = []
    tg, client, sender = instance(events=events)
    root = directory()
    script_messages(sender, [f.message(101), document(102)])
    original_download = client.download_media
    observed = []

    async def observe_cancellation(*args, **kwargs):
        try:
            return await original_download(*args, **kwargs)
        except BaseException as error:
            observed.append(error)
            raise

    def pending_file(request):
        root.chmod(0o500)
        return f.PENDING

    client.download_media = observe_cancellation
    sender.file_script = [pending_file]
    try:
        with cleanup_logs() as records:
            task = asyncio.create_task(tg.get_message_batch(7, after_id=100, limit=2, download_media_to=root))
            while not sender.pending:
                if task.done():
                    await task
                    raise AssertionError('SDK download did not block')
                await asyncio.sleep(0)
            task.cancel('secret cancellation details')
            caught = await f.expect(asyncio.CancelledError, task)
        assert len(observed) == 1 and caught is observed[0]
        assert not events and len(list(root.iterdir())) == 1
        assert [r.getMessage() for r in records] == ['Batch artifact cleanup failed during unlink (PermissionError)']
    finally:
        root.chmod(0o700)


async def test_cleanup_only_media_and_manifest_errors():
    for mode in ('media', 'manifest'):
        root = directory()
        fault = PermissionError('secret cleanup-only details')
        events = []
        tg, _, sender = instance(events=events)
        sender.files[ASSET_ID] = PAYLOAD
        script_messages(sender, [document()])
        with patch.object(batch_files.os, 'unlink', side_effect=fault), cleanup_logs() as records:
            try:
                raise errors.ChannelPrivateError(request=None)
            except errors.ChannelPrivateError:
                if mode == 'media':
                    caught = await f.expect(PermissionError, tg.get_message_batch(
                        7, after_id=100, limit=1, download_media_to=root))
                else:
                    caught = f.rejected(PermissionError, lambda: MessageBatch.from_json(GOLDEN).save(root))
        assert caught is fault and health.classify(caught) is None and not events and not records
        if mode == 'media':
            assert caught.partial_result.next_after_id == 100 and not caught.partial_result.messages
            assert (root / hashlib.sha256(PAYLOAD).hexdigest()).read_bytes() == PAYLOAD
        else:
            assert (root / (GOLDEN_ID + '.json')).read_bytes() == GOLDEN.encode('utf-8')
        assert len(list(root.iterdir())) == 2  # complete public object and the undeletable private temp


async def test_verification_error_and_cleanup_precedence():
    for first_failure in ('read', 'close'):
        events = []
        tg, _, sender = instance(events=events)
        root = directory()
        digest = hashlib.sha256(PAYLOAD).hexdigest()
        (root / digest).write_bytes(PAYLOAD)
        sender.files[ASSET_ID] = PAYLOAD
        script_messages(sender, [f.message(101), document(102)])
        read_error = OSError('secret verification read error')
        close_error = PermissionError('secret verification close error')
        faults = {'close': close_error}
        if first_failure == 'read':
            faults['read'] = read_error
        with ExitStack() as stack:
            opened = stack.enter_context(verification_faults(faults))
            records = stack.enter_context(cleanup_logs())
            if first_failure == 'close':
                stack.enter_context(patch.object(batch_files.os, 'unlink', side_effect=PermissionError('secret unlink error')))
            try:
                raise errors.ChannelPrivateError(request=None)
            except errors.ChannelPrivateError:
                caught = await f.expect(OSError, tg.get_message_batch(
                    7, after_id=100, limit=2, download_media_to=root))
        assert caught is (read_error if first_failure == 'read' else close_error)
        assert caught.partial_result.next_after_id == 101 and not events and health.classify(caught) is None
        assert opened and all(raw.closed for raw in opened)
        operation = 'close' if first_failure == 'read' else 'unlink'
        assert [r.getMessage() for r in records] == ['Batch artifact cleanup failed during {} (PermissionError)'.format(operation)]
        assert (root / digest).read_bytes() == PAYLOAD


async def main():
    tests = [test_golden_wire_and_no_enrichment, test_immutable_value_and_save_reload,
             test_senderless_and_service_records, test_dates_nulls_and_large_signed_ids,
             test_strict_json_and_schema, test_record_cursor_and_blob_constraints,
             test_ordered_pages_and_explicit_group, test_end_empty_and_max_cursor,
             test_invalid_input_before_connection, test_source_and_peer_validation,
             test_budget_prefix_empty_and_resume, test_original_network_and_rpc_errors,
             test_bad_record_preserves_prefix, test_document_bytes_dedup_and_root_independence,
             test_photo_variants_and_unsupported_media, test_changed_bytes_change_identity,
             test_missing_and_truncated_media, test_existing_blob_integrity,
             test_manifest_integrity, test_concurrent_complete_publication,
             test_cancelled_download_cleanup, test_media_refresh_obeys_budget,
             test_local_errors_do_not_inherit_health_verdicts, test_saved_replay_and_ack_order,
             test_legacy_dataframe_and_media_contracts,
             test_native_path_error_under_handled_rpc, test_local_io_provenance_matrix,
             test_sdk_transport_cause_is_preserved, test_primary_rpc_survives_real_cleanup_denial,
             test_secondary_failures_and_logging_cannot_mask_primary,
             test_cancellation_survives_cleanup_denial, test_cleanup_only_media_and_manifest_errors,
             test_verification_error_and_cleanup_precedence]
    print('Message Batch Tests — Telethon {}; synthetic credentials; no Telegram sockets'.format(telethon.__version__))
    logging.getLogger('tgdata').addHandler(logging.NullHandler())
    results = []
    with tempfile.TemporaryDirectory(prefix='tgdata_batch_test_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        f.TMP = Path(tmp)
        try:
            for number, test in enumerate(tests, 1):
                print('\nTEST {}: {}'.format(number, test.__name__[5:]))
                try:
                    await asyncio.wait_for(test(), timeout=40)
                    results.append(True)
                    print('✓ Passed')
                except Exception:
                    results.append(False)
                    traceback.print_exc()
                    print('✗ Failed')
        finally:
            for client in f.CLIENTS:
                await client.disconnect()
            f.CLIENTS.clear()
    print('\nPassed: {}/{}'.format(sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
