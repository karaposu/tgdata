"""Native exported-sender creation cancellation, before the borrow is returned."""
import asyncio,json,socket,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path('/private/tmp/tgdata-60-media-prebuild/candidate')
sys.path.insert(0,str(ROOT))
from telethon import errors,functions
from telethon.crypto import AuthKey
from telethon.network.mtprotosender import MTProtoSender
from tgdata.smoke_tests import test_19_message_batches as b

class Wire:
    def __init__(self,*args,**kwargs):self.up=False
    async def connect(self,timeout=None):self.up=True
    async def disconnect(self):self.up=False
    def is_connected(self):return self.up
    async def send(self,data):pass
    async def recv(self):return await asyncio.Future()

async def main(root):
    tg,client,sender=b.instance();b.script_messages(sender,[b.document()])
    sender.file_script=[errors.FileMigrateError(request=None,capture=2)]
    native_init=MTProtoSender.__init__;created=[];auth=[];original=sender.send
    def initialize(new,auth_key,**kwargs):
        # Credentials are a fixture; connect, native sender loops and SDK export
        # ownership execute unchanged. No key negotiation/network is needed.
        native_init(new,AuthKey(b's'*256),**kwargs);created.append(new)
    def send(request,ordered=False):
        if isinstance(b.f.unwrap(request),functions.auth.ExportAuthorizationRequest):
            future=asyncio.get_running_loop().create_future();auth.append(future);return future
        return original(request,ordered=ordered)
    sender.send=send
    async def dc(*args,**kwargs):return SimpleNamespace(id=2,ip_address='127.0.0.1',port=443)
    try:
        with patch.object(MTProtoSender,'__init__',initialize),patch.object(client,'_get_dc',dc),patch.object(client,'_connection',Wire):
            task=asyncio.create_task(tg.get_message_batch(-1000000000007,after_id=100,limit=1,
                download_media_to=root/'media',download_concurrency=3))
            for _ in range(2000):
                if auth:break
                await asyncio.sleep(.001)
            assert len(created)==1 and len(auth)==1
            assert created[0].is_connected()
            task.cancel()
            try:await task
            except asyncio.CancelledError:pass
            new=created[0]
            observed=dict(public_task_cancelled=task.cancelled(),export_auth_cancelled=auth[0].cancelled(),
                exported_sender_connected=new.is_connected(),wire_connected=new._connection is not None and new._connection.is_connected(),
                send_loop_running=new._send_loop_handle is not None and not new._send_loop_handle.done(),
                receive_loop_running=new._recv_loop_handle is not None and not new._recv_loop_handle.done(),
                reachable_in_client_cache=any(pair[1] is new for pair in client._borrowed_senders.values()),
                temporary_files=len(list((root/'media').glob('.tgdata-media-*'))))
            passed=not any(observed[k] for k in ('exported_sender_connected','wire_connected','send_loop_running','receive_loop_running'))
            report=dict(result='PASS' if passed else 'FAIL',observation=observed,fixture_cleanup_after_observation=True)
            Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    finally:
        for new in created:await new.disconnect()
        for c in b.f.CLIENTS:c.session.close()
    assert passed,'exported sender creation escaped media ownership after cancellation'

with tempfile.TemporaryDirectory() as tmp,patch.object(socket.socket,'connect',side_effect=AssertionError('no network')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('no network')):
    b.f.TMP=Path(tmp);asyncio.run(main(Path(tmp)))
