"""Actual public batch -> SDK CDN redirect -> helper -> native blob publication."""
import asyncio,hashlib,json,socket,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path('/private/tmp/tgdata-60-media-prebuild/candidate')
sys.path.insert(0,str(ROOT))
from telethon import functions,types
from telethon.crypto import AES,AuthKey
from telethon.network.mtprotosender import MTProtoSender
from tgdata.smoke_tests import test_19_message_batches as b

async def main(root):
    data=b'cdn-media-bytes!!'*16
    assert len(data)%16==0
    key=b'k'*32;iv=b'i'*32;encoded=AES.encrypt_ige(data,key,iv)
    tg,client,sender=b.instance();sender.auth_key=AuthKey(b'a'*256)
    client.flood_sleep_threshold=0;client._request_retries=0;client._raise_last_call_error=True
    b.script_messages(sender,[b.document(data=data)])
    sender.file_script=[types.upload.FileCdnRedirect(dc_id=2,file_token=b'token',
        encryption_key=key,encryption_iv=iv,file_hashes=[])]
    original=sender.send;calls=[];helpers=[];native_init=type(client).__init__
    def send(request,ordered=False):
        raw=b.f.unwrap(request)
        if isinstance(raw,functions.upload.GetCdnFileRequest):
            bytes(raw);calls.append(type(raw).__name__)
            result=asyncio.get_running_loop().create_future()
            result.set_result(types.upload.CdnFile(encoded[raw.offset:raw.offset+raw.limit]))
            return result
        return original(request,ordered=ordered)
    sender.send=send
    def initialize(helper,*args,**kwargs):
        native_init(helper,*args,**kwargs);helpers.append(helper)
    async def connect(sender,connection):return True
    async def dc(*args,**kwargs):return SimpleNamespace(id=2,ip_address='127.0.0.1',port=443)
    with patch.object(type(client),'__init__',initialize),patch.object(MTProtoSender,'connect',connect),patch.object(client,'_get_dc',dc):
        batch=await tg.get_message_batch(-1000000000007,after_id=100,limit=1,
            download_media_to=root/'media',download_concurrency=3)
    blob=batch.messages[0]['media']['blob'];assert (root/'media'/blob['path']).read_bytes()==data
    assert len(helpers)==1 and helpers[0].flood_sleep_threshold==0 and helpers[0]._request_retries==0
    assert not helpers[0].is_connected() and client.is_connected()
    assert calls==['GetCdnFileRequest']
    report=dict(result='PASS',public_batch=True,actual_sdk_cdn_request=calls,plaintext_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),helpers_created=1,helper_closed=True,
        parent_connected=True,wait_threshold=helpers[0].flood_sleep_threshold,request_retries=helpers[0]._request_retries)
    Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    for c in b.f.CLIENTS:c.session.close()
with tempfile.TemporaryDirectory() as tmp,patch.object(socket.socket,'connect',side_effect=AssertionError('no network')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('no network')):
    b.f.TMP=Path(tmp);asyncio.run(main(Path(tmp)))
