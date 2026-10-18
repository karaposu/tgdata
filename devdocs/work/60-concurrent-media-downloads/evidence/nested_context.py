"""Observe public callback reentry sharing its task/context and changing clients."""
import asyncio,contextvars,json,socket,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from tgdata.smoke_tests import test_19_message_batches as b
marker=contextvars.ContextVar('probe_media_owner',default=None)
async def main():
    tg,client,sender=b.instance();other,other_client,other_sender=b.instance();parent=asyncio.current_task();seen=[]
    original=other_sender.send
    def send(request,ordered=False):
        seen.append(dict(same_task=asyncio.current_task() is parent,marker=marker.get(),different_client=other_client is not client))
        return original(request,ordered=ordered)
    other_sender.send=send
    async def callback(frame,info):await other.get_message_batch(7,after_id=100,limit=1)
    token=marker.set('outer_read')
    try:
        frame=await tg.get_messages(7,after_id=100,limit=1,batch_size=1,batch_callback=callback)
        assert len(frame)==1 and seen and all(x['same_task'] and x['marker']=='outer_read' and x['different_client'] for x in seen)
        report=dict(result='OBSERVED',nested_sends=len(seen),same_task=True,inherited_outer_context=True,different_client=True)
        Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    finally:
        marker.reset(token)
        for c in b.f.CLIENTS:c.session.close()
with tempfile.TemporaryDirectory() as tmp,patch.object(socket.socket,'connect',side_effect=AssertionError('no network')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('no network')):
    b.f.TMP=Path(tmp);asyncio.run(main())
