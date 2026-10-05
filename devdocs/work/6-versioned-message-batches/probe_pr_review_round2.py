"""Independent second PR #15 probes on the implemented revision 3.

The actual SDK, budget and files run. Telegram replies/storage faults are
supplied; no real account or network connection is used.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

import telethon
from telethon import errors
from tgdata import BatchStorageError, MessageBatch, ReadBudgetExceeded, health
import tgdata.batch_files as files
from tgdata.smoke_tests import test_19_message_batches as t


async def budget_refusal_and_cleanup():
    budget, _ = t.f.ledger(2)
    events = []
    tg, client, sender = t.instance(budget, events)
    root = t.directory()
    t.script_messages(sender, [t.f.message(101), t.document(102)])
    observed = []
    download = client.download_media

    async def observe(*args, **kwargs):
        try:
            return await download(*args, **kwargs)
        except BaseException as error:
            observed.append(error)
            raise

    def expire_reference(request):
        root.chmod(0o500)
        return errors.FileReferenceExpiredError(request=request)

    client.download_media = observe
    sender.file_script = [expire_reference]
    try:
        with t.cleanup_logs() as records:
            caught = await t.f.expect(ReadBudgetExceeded, tg.get_message_batch(
                7, after_id=100, limit=2, download_media_to=root))
        assert caught is observed[0] and caught.partial_result.next_after_id == 101
        assert budget.status(t.f.ACCOUNT).used == 2 and len(sender.reads) == 1
        assert not events and len(records) == 1 and len(list(root.iterdir())) == 1
        print('PASS budget + cleanup: original ReadBudgetExceeded, cursor 101, two charged messages, no false health')
    finally:
        root.chmod(0o700)


async def invalid_path_non_oserror():
    events = []
    tg, _, sender = t.instance(events=events)
    path = str(t.directory() / ('bad' + chr(0) + 'path'))
    try:
        raise errors.ChannelPrivateError(request=None)
    except errors.ChannelPrivateError:
        caught = await t.f.expect(ValueError, tg.get_message_batch(7, download_media_to=path))
    assert not isinstance(caught, OSError)
    assert health.classify(caught) is None and not events and not sender.calls
    print('PASS non-OSError path failure: ValueError stays local; zero requests and zero health events')


async def verification_symlink_race():
    events = []
    tg, _, sender = t.instance(events=events)
    root = t.directory()
    destination = root / hashlib.sha256(t.PAYLOAD).hexdigest()
    destination.write_bytes(t.PAYLOAD)
    outside = t.directory() / 'outside'
    outside.write_bytes(b'unchanged external contents')
    sender.files[t.ASSET_ID] = t.PAYLOAD
    t.script_messages(sender, [t.document()])
    real_lstat = Path.lstat
    swapped = []

    def swap_after_stat(path, *args, **kwargs):
        before = real_lstat(path, *args, **kwargs)
        if path == destination and not swapped:
            destination.unlink()
            destination.symlink_to(outside)
            swapped.append(True)
        return before

    with patch.object(Path, 'lstat', swap_after_stat):
        caught = await t.f.expect((OSError, BatchStorageError), tg.get_message_batch(
            7, after_id=100, limit=1, download_media_to=root))
    assert swapped and caught.partial_result.next_after_id == 100
    assert not events and destination.is_symlink() and list(root.iterdir()) == [destination]
    assert outside.read_bytes() == b'unchanged external contents'
    print('PASS verification race: post-lstat symlink replacement rejected; cursor and outside contents unchanged')


async def retry_after_published_cleanup_failure():
    budget, _ = t.f.ledger(2)
    events = []
    tg, _, sender = t.instance(budget, events)
    root = t.directory()
    real_link = files.os.link
    sender.files[t.ASSET_ID] = t.PAYLOAD
    t.script_messages(sender, [t.document()])

    def publish_then_deny_removal(source, destination):
        real_link(source, destination)
        root.chmod(0o500)

    try:
        with patch.object(files.os, 'link', side_effect=publish_then_deny_removal):
            caught = await t.f.expect(PermissionError, tg.get_message_batch(
                7, after_id=100, limit=1, download_media_to=root))
        assert caught.partial_result.next_after_id == 100 and not caught.partial_result.messages
        assert budget.status(t.f.ACCOUNT).used == 1 and not events
    finally:
        root.chmod(0o700)
    digest = hashlib.sha256(t.PAYLOAD).hexdigest()
    assert (root / digest).read_bytes() == t.PAYLOAD
    t.script_messages(sender, [t.document()])
    batch = await tg.get_message_batch(7, after_id=100, limit=1, download_media_to=root)
    assert batch.next_after_id == 101 and budget.status(t.f.ACCOUNT).used == 2
    assert batch.messages[0]['media']['blob']['sha256'] == digest and not events
    assert len([p for p in root.iterdir() if not p.name.startswith('.tgdata-')]) == 1
    assert len([p for p in root.iterdir() if p.name.startswith('.tgdata-')]) == 1
    saved = batch.save(t.directory())
    assert MessageBatch.from_json(saved.read_bytes()).batch_id == batch.batch_id
    print('PASS retry after publication: failed cleanup keeps cursor 100; retry verifies blob and returns 101, charged again')


async def independent_process_publishers():
    root = t.directory()
    child = '''import asyncio, json, sys
from tgdata import MessageBatch
from tgdata.batch_files import download_blob
payload = b'round-two-concurrent-bytes'
async def writer(stream):
    stream.write(payload)
    return stream
blob = asyncio.run(download_blob(sys.argv[1], writer, expected_size=len(payload)))
manifest = MessageBatch.from_json(sys.stdin.read()).save(sys.argv[2])
print(json.dumps({'blob': blob, 'manifest': manifest.name}, sort_keys=True))
'''

    def publish(_):
        result = subprocess.run([sys.executable, '-c', child, str(root / 'media'), str(root / 'manifests')],
                                input=t.GOLDEN, text=True, capture_output=True, check=True, cwd=str(REPO))
        return json.loads(result.stdout)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(publish, range(4)))
    assert all(result == results[0] for result in results)
    assert len(list((root / 'media').iterdir())) == len(list((root / 'manifests').iterdir())) == 1
    assert (root / 'media' / results[0]['blob']['path']).read_bytes() == b'round-two-concurrent-bytes'
    assert (root / 'manifests' / results[0]['manifest']).read_bytes() == t.GOLDEN.encode('utf-8')
    print('PASS multiprocess publication: four independent processes, one complete blob/manifest each, no temp leftovers')


async def main():
    print('Second PR #15 probes — Telethon {}'.format(telethon.__version__))
    probes = [budget_refusal_and_cleanup, invalid_path_non_oserror, verification_symlink_race,
              retry_after_published_cleanup_failure, independent_process_publishers]
    with tempfile.TemporaryDirectory(prefix='tgdata6_pr_round2_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        t.f.TMP = Path(tmp)
        try:
            for probe in probes:
                await asyncio.wait_for(probe(), timeout=40)
        finally:
            for client in t.f.CLIENTS:
                await client.disconnect()
            t.f.CLIENTS.clear()
    print('Result: 5/5 fresh probes passed; no live-server/receiver claim')


if __name__ == '__main__':
    asyncio.run(main())
