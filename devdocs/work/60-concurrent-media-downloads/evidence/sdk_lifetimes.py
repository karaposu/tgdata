"""Observe real Telethon download ownership after file migration; sockets forbidden."""
import asyncio,json,socket,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from telethon import errors
from tgdata.smoke_tests import test_19_message_batches as b

async def case(cancel):
    tg,client,sender=b.instance();other=b.Sender();borrowed=[];returned=[]
    sender.file_script=[errors.FileMigrateError(request=None,capture=2)]
    other.files[b.ASSET_ID]=b.PAYLOAD
    if cancel:other.file_script=[b.f.PENDING]
    async def borrow(dc):borrowed.append(dc);return other
    async def release(value):assert value is other;returned.append(True)
    with patch.object(client,'_borrow_exported_sender',borrow),patch.object(client,'_return_exported_sender',release):
        task=asyncio.create_task(client.download_media(b.document(),file=bytes))
        if cancel:
            while not other.pending:await asyncio.sleep(0)
            task.cancel()
            try:await task
            except asyncio.CancelledError:pass
        else:assert await task==b.PAYLOAD
    return dict(case='cancel' if cancel else 'success',borrowed=len(borrowed),returned=len(returned),cancelled=task.cancelled(),pending_cancelled=all(p.cancelled() for p in other.pending))

async def main():
    try:
        rows=[await case(False),await case(True)]
        Path(__file__).with_suffix('.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
    finally:
        for client in b.f.CLIENTS:client.session.close()

with tempfile.TemporaryDirectory() as tmp,patch.object(socket.socket,'connect',side_effect=AssertionError('no network')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('no network')):
    b.f.TMP=Path(tmp);asyncio.run(main())
