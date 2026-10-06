"""Independent pre-build checks of uncertain commits and existing blob replay."""
import asyncio
import hashlib
from pathlib import Path
import shutil
import socket
import sqlite3
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tgdata.batch_files import _verify_existing, BatchStorageError
from tgdata import MessageBatch
from tgdata.smoke_tests import test_19_message_batches as b


async def uncertain_commit(root):
    path = root / 'uncertain.sqlite3'
    with sqlite3.connect(str(path)) as db:
        db.execute('CREATE TABLE payload (value TEXT)')
        db.execute('INSERT INTO payload VALUES (?)', ('old',))
    committed = asyncio.Event()
    wait = asyncio.Future()

    async def write_then_wait():
        with sqlite3.connect(str(path)) as db:
            db.execute('UPDATE payload SET value = ?', ('new',))
        committed.set()
        await wait

    task = asyncio.create_task(write_then_wait())
    await committed.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    else:
        raise AssertionError('cancellation did not propagate')
    with sqlite3.connect(str(path)) as db:
        assert db.execute('SELECT value FROM payload').fetchone()[0] == 'new'
    print('PASS cancellation after commit does not imply rollback')


async def relocated_blob(root):
    b.f.TMP = root
    first, second = root / 'media-a', root / 'media-b'
    second.mkdir()
    try:
        tg, _, sender = b.instance()
        sender.files[b.ASSET_ID] = b.PAYLOAD
        b.script_messages(sender, [b.document()])
        batch = await tg.get_message_batch(-1000000000007, after_id=100, limit=1,
                                           download_media_to=first)
        blob = batch.messages[0]['media']['blob']
        shutil.copyfile(first / blob['path'], second / blob['path'])
        before = list(sender.calls)
        replay = MessageBatch.from_json(batch.to_json())
        _verify_existing(second / blob['path'], blob['sha256'], blob['size'])
        assert replay.to_json() == batch.to_json() and sender.calls == before
        print('PASS real downloaded batch replays from relocated verified blob')
        (second / blob['path']).write_bytes(b'x' * blob['size'])
        try:
            _verify_existing(second / blob['path'], blob['sha256'], blob['size'])
        except BatchStorageError:
            pass
        else:
            raise AssertionError('corrupt blob accepted')
        assert sender.calls == before
        print('PASS same-size corrupt blob refused without Telegram')
    finally:
        for client in b.f.CLIENTS:
            await client.disconnect()
        b.f.CLIENTS.clear()


async def main(root):
    await uncertain_commit(root)
    await relocated_blob(root)


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='tgdata18_plan_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        asyncio.run(main(Path(tmp)))
