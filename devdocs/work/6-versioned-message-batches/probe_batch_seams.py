"""Pre-build #6 probes: real filesystem and SDK behavior, synthetic transport.

Run: .venv/bin/python devdocs/work/6-versioned-message-batches/probe_batch_seams.py
No new batch implementation is supplied by these probes; Telegram is not contacted.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import telethon
from telethon.tl import functions, types
from tgdata.smoke_tests import test_18_read_budget as fixture

PAYLOAD = b'content-addressed-media\x00' * 4096


def filesystem(root):
    folder = root / 'publication'
    folder.mkdir()
    digest = hashlib.sha256(PAYLOAD).hexdigest()
    target = folder / digest

    def publish(_):
        with tempfile.NamedTemporaryFile(dir=folder, prefix='.pending-', delete=False) as output:
            temp = Path(output.name)
            output.write(PAYLOAD)
            output.flush()
            os.fsync(output.fileno())
        try:
            try:
                os.link(temp, target)
                created = True
            except FileExistsError:
                created = False
                assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
            return created
        finally:
            temp.unlink()

    with ThreadPoolExecutor(max_workers=8) as pool:
        created = sum(pool.map(publish, range(24)))
    assert created == 1 and target.read_bytes() == PAYLOAD
    assert list(folder.iterdir()) == [target]
    print('Publication: 24 competing writers, one complete digest-named file, no temporary leftovers')


class FileSender(fixture.Sender):
    def send(self, request, ordered=False):
        request = fixture.unwrap(request)
        if isinstance(request, functions.upload.GetFileRequest):
            future = asyncio.get_running_loop().create_future()
            data = PAYLOAD[request.offset:request.offset + request.limit]
            future.set_result(types.upload.File(types.storage.FileUnknown(), 0, data))
            return future
        return super().send(request, ordered=ordered)


async def sdk(root):
    tg, client, sender = fixture.instance()
    date = datetime.fromtimestamp(fixture.NOW, timezone.utc)
    plain = types.Message(id=101, peer_id=types.PeerChannel(7), date=date,
                          message='raw sender metadata may be absent', from_id=None)
    service = types.MessageService(id=102, peer_id=types.PeerChannel(7), date=date,
                                   action=types.MessageActionChatEditTitle('Synthetic'), from_id=None)
    reply = fixture.response([service, plain])
    reply.users = []
    sender.script = [reply]
    messages = [message async for message in client.iter_messages(
        types.InputPeerChannel(7, 7), min_id=100, reverse=True, limit=2)]
    assert [message.id for message in messages] == [101, 102]
    assert messages[0].sender_id is None and messages[1].action is not None
    shown = await tg.message_engine._process_message(messages[0], client, False)
    assert shown is None
    print('Raw iteration: IDs 101/102 and service action survive; presentation conversion omits senderless 101')
    try:
        json.dumps(messages[0].to_dict())
    except TypeError:
        print('SDK dictionary: ordinary JSON encoding rejects its datetime; an explicit wire projection is needed')
    else:
        raise AssertionError('SDK dictionary unexpectedly has no non-JSON value')

    client._sender = FileSender()
    client.session.set_dc(2, '149.154.167.51', 443)  # never connected
    document = types.Document(id=(1 << 60) + 9, access_hash=9, file_reference=b'synthetic',
                              date=date, mime_type='application/octet-stream', size=len(PAYLOAD), dc_id=2,
                              attributes=[types.DocumentAttributeFilename('../../untrusted-name.bin')])
    with tempfile.NamedTemporaryFile(dir=root, prefix='.sdk-', delete=False) as output:
        temp = Path(output.name)
        returned = await client.download_media(document, file=output)
        assert returned is output and not output.closed
        output.flush()
        os.fsync(output.fileno())
    try:
        assert temp.read_bytes() == PAYLOAD
        assert hashlib.sha256(temp.read_bytes()).digest() == hashlib.sha256(PAYLOAD).digest()
        print('SDK download: writes complete bytes to the supplied file object and returns it; media filename is unused')
    finally:
        temp.unlink()


async def main():
    print('Batch seam probes — Telethon', telethon.__version__)
    with tempfile.TemporaryDirectory(prefix='tgdata6_seams_') as name, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        root = Path(name)
        fixture.TMP = root
        try:
            filesystem(root)
            await sdk(root)
        finally:
            for client in fixture.CLIENTS:
                await client.disconnect()
            fixture.CLIENTS.clear()
    print('All pre-build seam probes passed; no live server behavior is claimed')


if __name__ == '__main__':
    asyncio.run(main())
