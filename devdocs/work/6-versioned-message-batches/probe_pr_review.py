"""Fresh PR #15 probes; exit 1 means a documented contract violation.

Run from the repository: .venv/bin/python devdocs/work/6-versioned-message-batches/probe_pr_review.py
The SDK and filesystem behavior are real; Telegram replies/faults are supplied.
No account/session file or network connection is used.
"""

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

import telethon
from telethon import errors, utils
from telethon.tl import functions, types
from tgdata import MessageBatch
from tgdata.smoke_tests import test_19_message_batches as t
import tgdata.batch_files as files


def digest(data):
    return hashlib.sha256(data).hexdigest()


class ReviewSender(t.Sender):
    def __init__(self):
        super().__init__()
        self.basic_group = None
        self.file_refs = []

    def send(self, request, ordered=False):
        if isinstance(request, (list, tuple)):
            return [self.send(item, ordered=ordered) for item in request]
        r = t.f.unwrap(request)
        if isinstance(r, functions.messages.GetChatsRequest):
            bytes(request)
            self.calls.append(type(r).__name__)
            result = asyncio.get_running_loop().create_future()
            result.set_result(types.messages.Chats([self.basic_group]))
            return result
        if isinstance(r, functions.upload.GetFileRequest):
            self.file_refs.append((r.location.file_reference, r.location.thumb_size))
        return super().send(request, ordered=ordered)


def instance(budget=None, events=None):
    tg, client, _ = t.instance(budget, events)
    client._sender = sender = ReviewSender()
    return tg, client, sender


async def cross_process_identity():
    shuffled = dict(reversed(list(json.loads(t.GOLDEN).items())))
    ordinary = json.dumps(shuffled, ensure_ascii=True, indent=2)
    assert MessageBatch.from_json(ordinary).to_json() == t.GOLDEN
    for seed in ('1', '37'):
        environment = dict(os.environ, PYTHONHASHSEED=seed)
        result = subprocess.run(
            [sys.executable, '-c', 'import sys; from tgdata import MessageBatch; '
             'sys.stdout.write(MessageBatch.from_json(sys.stdin.read()).to_json())'],
            input=ordinary, text=True, capture_output=True, check=True,
            cwd=str(REPO), env=environment,
        )
        assert result.stdout == t.GOLDEN
    print('PASS identity: reordered/escaped JSON and two independent processes preserve exact golden bytes')
    return True


async def basic_group_and_gap():
    tg, client, sender = instance()
    basic = types.Chat(id=17, title='Basic room', photo=types.ChatPhotoEmpty(),
                       participants_count=2, date=t.NOW, version=1)
    sender.basic_group = basic
    client.session.process_entities([basic])
    messages = [types.Message(id=mid, peer_id=types.PeerChat(17), from_id=types.PeerChannel(7),
                              date=t.NOW, message='message {}'.format(mid)) for mid in (101, 104)]
    page = t.f.response(list(reversed(messages)))
    page.chats.append(basic)
    sender.script = [page]
    batch = await tg.get_message_batch(-17, after_id=100, limit=2)
    assert batch.chat_id == -17 and batch.next_after_id == 104
    assert [message['id'] for message in batch.messages] == ['101', '104']
    assert all(message['sender'] == {'id': '-1000000000007', 'name': 'Synthetic Room',
                                  'username': 'synthetic_room'} for message in batch.messages)
    assert sender.calls == ['GetChatsRequest', 'GetHistoryRequest']
    print('PASS basic group: marked chat -17, gap 101->104 and cached channel author; no enrichment')
    return True


async def sdk_photo_selection():
    stripped = types.PhotoStrippedSize('i', b'\x01\x01\x01synthetic-stripped-payload')
    for variant in ('stripped', 'video'):
        tg, _, sender = instance()
        message = t.photo(sizes=[stripped] if variant == 'stripped' else [types.PhotoSize('w', 2, 2, 99)])
        if variant == 'stripped':
            expected = utils.stripped_photo_to_jpg(stripped.bytes)
        else:
            expected = b'selected video bytes'
            message.media.photo.video_sizes = [types.VideoSize('u', 2, 2, len(expected))]
        sender.files[t.ASSET_ID] = expected
        t.script_messages(sender, [message])
        root = t.directory()
        batch = await tg.get_message_batch(7, after_id=100, limit=1, download_media_to=root)
        media = batch.messages[0]['media']
        assert media['size'] == len(expected)
        assert media['blob'] == {'sha256': digest(expected), 'path': digest(expected), 'size': len(expected)}
        assert (root / digest(expected)).read_bytes() == expected
        assert len(sender.file_calls) == (0 if variant == 'stripped' else 1)
        if variant == 'video':
            assert sender.file_refs[0][1] == 'u'
    print('PASS photo selection: real SDK stripped-photo and video-size paths match prepared bytes/size/hash')
    return True


async def successful_media_refresh():
    budget, _ = t.f.ledger(2)
    events = []
    tg, _, sender = instance(budget, events)
    initial, refreshed = t.document(), t.document()
    refreshed.media.document.file_reference = b'refreshed-synthetic-reference'
    sender.script = [t.f.response([initial]), t.f.response([refreshed])]
    sender.files[t.ASSET_ID] = t.PAYLOAD
    sender.file_script = [errors.FileReferenceExpiredError(request=None)]
    root = t.directory()
    batch = await tg.get_message_batch(7, after_id=100, limit=1, download_media_to=root)
    assert batch.next_after_id == 101 and batch.messages[0]['media']['blob']['sha256'] == digest(t.PAYLOAD)
    assert budget.status(t.f.ACCOUNT).used == 2 and len(sender.reads) == 2
    assert sender.file_refs == [(b'synthetic-file-reference', ''), (b'refreshed-synthetic-reference', '')]
    assert not events and (root / digest(t.PAYLOAD)).read_bytes() == t.PAYLOAD
    print('PASS reference refresh: SDK retries with the refreshed reference; history + refresh charge exactly two reads')
    return True


async def publication_fault_prefix():
    events = []
    tg, _, sender = instance(events=events)
    t.script_messages(sender, [t.f.message(101), t.document(102)])
    sender.files[t.ASSET_ID] = t.PAYLOAD
    root = t.directory()
    original = PermissionError('synthetic hard-link denial')
    with patch.object(files.os, 'link', side_effect=original):
        caught = await t.f.expect(PermissionError, tg.get_message_batch(
            7, after_id=100, limit=2, download_media_to=root))
    assert caught is original and caught.partial_result.next_after_id == 101
    assert len(caught.partial_result.messages) == 1 and not list(root.iterdir()) and not events
    print('PASS publication fault: same local exception, one completed record, cursor 101 and no public/temp file')
    return True


async def cancellation_after_completed_blob():
    tg, _, sender = instance()
    sender.files[t.ASSET_ID] = t.PAYLOAD
    sender.file_script = [types.upload.File(types.storage.FileUnknown(), 0, t.PAYLOAD), t.f.PENDING]
    t.script_messages(sender, [t.document(), t.document(102, asset_id=t.ASSET_ID + 1)])
    root = t.directory()
    task = asyncio.create_task(tg.get_message_batch(7, after_id=100, limit=2, download_media_to=root))
    while not sender.pending:
        if task.done():
            await task
            raise AssertionError('second download did not block')
        await asyncio.sleep(0)
    task.cancel()
    await t.f.expect(asyncio.CancelledError, task)
    assert [entry.name for entry in root.iterdir()] == [digest(t.PAYLOAD)]
    assert (root / digest(t.PAYLOAD)).read_bytes() == t.PAYLOAD
    print('PASS cancellation: second download temp removed; only the first complete immutable blob remains')
    return True


async def incidental_rpc_does_not_label_local_path_failure():
    events = []
    tg, _, sender = instance(events=events)
    path = t.directory() / 'ordinary-file'
    path.write_bytes(b'not a directory')
    try:
        # Models a caller handling a raw/unreported SDK access error, then
        # attempting a different batch operation. No server behavior is inferred.
        raise errors.ChannelPrivateError(request=None)
    except errors.ChannelPrivateError:
        caught = await t.f.expect(FileExistsError, tg.get_message_batch(7, download_media_to=path))
    observation = [(event['verdict'], event['group'], event['error']) for event in events]
    passed = not events and not sender.calls
    print('{} local error context: error={}, Telegram requests={}, health={}'.format(
        'PASS' if passed else 'FAIL', type(caught).__name__, len(sender.calls), observation))
    return passed


async def cleanup_does_not_mask_sdk_error():
    events = []
    tg, _, sender = instance(events=events)
    root = t.directory()
    original = errors.ChannelPrivateError(request=None)
    t.script_messages(sender, [t.f.message(101), t.document(102)])

    def denied_after_download_starts(request):
        # Real filesystem permission change after the temporary file opened.
        # Downloading would still surface its original exception if cleanup
        # were prevented from replacing an already active failure.
        root.chmod(0o500)
        return original

    sender.file_script = [denied_after_download_starts]
    try:
        caught = await t.f.expect(Exception, tg.get_message_batch(
            7, after_id=100, limit=2, download_media_to=root))
        leftovers = len(list(root.iterdir()))
        assert caught.partial_result.next_after_id == 101 and len(caught.partial_result.messages) == 1
        passed = caught is original
        print('{} cleanup error precedence: original={}, raised={}, same_object={}, cursor={}, temp_left={}'.format(
            'PASS' if passed else 'FAIL', type(original).__name__, type(caught).__name__, passed,
            caught.partial_result.next_after_id, leftovers))
        return passed
    finally:
        # Restore only this probe-owned temporary directory so its fixture can
        # be removed. The production implementation never receives this help.
        root.chmod(0o700)


async def main():
    logging.getLogger('tgdata').addHandler(logging.NullHandler())
    probes = [cross_process_identity, basic_group_and_gap, sdk_photo_selection,
              successful_media_refresh, publication_fault_prefix, cancellation_after_completed_blob,
              incidental_rpc_does_not_label_local_path_failure, cleanup_does_not_mask_sdk_error]
    results = []
    print('Fresh PR #15 probes — Telethon {}'.format(telethon.__version__))
    with tempfile.TemporaryDirectory(prefix='tgdata6_pr_review_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        t.f.TMP = Path(tmp)
        try:
            for probe in probes:
                results.append(await asyncio.wait_for(probe(), timeout=40))
        finally:
            for client in t.f.CLIENTS:
                await client.disconnect()
            t.f.CLIENTS.clear()
    print('Result: {} passed; {} contract violations'.format(sum(results), len(results) - sum(results)))
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
