"""Fresh composition probes for the iteration2 contract sketch."""
import asyncio
from datetime import timedelta
import json
from pathlib import Path
import socket
import sqlite3
import tempfile
from unittest.mock import patch
import contract_probe as sketch
from foundation_probe import AlbumReceiver,raw_record,batch,CHAT,NOW
from tgdata import MessageBatch,SQLiteSyncStore
from tgdata.backfill import BackfillStartRequest,BackfillPrepareContext
from tgdata.backfill_engine import BackfillEngine


def main():
    results={}
    with tempfile.TemporaryDirectory(prefix='tgdata30-critic-') as directory, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        root=Path(directory)
        async def backfill():
            calls=[]
            async def read(chat,**options):
                calls.append(options);ident=options['after_id']+1
                row=raw_record(ident,seconds=ident,text='anchor' if ident==1 else '')
                return MessageBatch._from_records(CHAT,options['after_id'],[row],'references','limit' if ident==1 else 'end')
            store=SQLiteSyncStore(root/'source.db')
            source=BackfillEngine(store,'jobs',read_batch=read,clock=lambda:NOW+timedelta(hours=2))
            request=BackfillStartRequest(collection_id='jobs',chat_id=CHAT,run_id='one',destination_id='one',
                origin='fresh',after_id=0,expected_predecessor=None,start_date=NOW-timedelta(hours=1),
                end_date=NOW+timedelta(hours=1),batch_size=1,pause_seconds=0)
            state=(await source.start(request,submission='new')).status
            first=await source.prepare(BackfillPrepareContext.from_status(state))
            receiver=AlbumReceiver(root/'posts.db','one',create=True);receiver.accept(first.batch)
            source=BackfillEngine(SQLiteSyncStore(store.path,create=False),'jobs',read_batch=read,
                                  clock=lambda:NOW+timedelta(hours=2))
            replay=await source.prepare(BackfillPrepareContext.from_status(first.status))
            assert replay.delivery==first.delivery and len(calls)==1
            with patch.object(sketch,'infer',side_effect=AssertionError('receipt depends on inference')):
                receiver.accept(replay.batch);accepted=await source.acknowledge(replay.delivery)
            second=await source.prepare(BackfillPrepareContext.from_status(accepted));receiver.accept(second.batch)
            assert sketch.infer(sketch.load_closed(receiver,0,2))==((1,2),)
            done=await source.acknowledge(second.delivery)
            assert done.after_id==2 and done.terminal_outcome=='completed' and len(calls)==2
            return dict(reads=2,original_delivery_replayed=True,completed_after_id=2)
        results['backfill']=asyncio.run(backfill())
        receiver=AlbumReceiver(root/'snapshot.db','one',create=True)
        original=batch(raw_record(1,text='anchor'),raw_record(2,seconds=1,group=7));receiver.accept(original)
        with sqlite3.connect(str(receiver.path)) as db:db.execute('PRAGMA journal_mode=WAL')
        writer=AlbumReceiver(receiver.path,'one');actual=receiver._load;wrote=[]
        def load(db,key,**options):
            if not wrote:
                writer.accept(batch(raw_record(3,seconds=2,text='later caption',group=7)));wrote.append(True)
            return actual(db,key,**options)
        with patch.object(receiver,'_load',side_effect=load):
            old=sketch.load_closed(receiver,0,2)
        assert sketch.infer(old)==((1,2),)
        try:sketch.load_closed(receiver,0,2)
        except sketch.ScopeRefusal:pass
        else:raise AssertionError('new split scope accepted')
        assert sketch.infer(sketch.load_closed(receiver,0,3))==((1,),(2,3))
        receiver.accept(original)
        results['snapshot']=dict(old_view_consistent=True,new_split_refused=True,
                  widened_view_withdraws_link=True,original_receipt_confirmable=True)
    report=dict(result='PASS',histories=results,scope='contract sketch composition, not the complete public prebuild')
    Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
