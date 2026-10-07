"""Real local SQLite/receiver falsifier on unchanged Stage 6 production code."""
import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from prebuild_store import ApplicationDatabase, NamespaceStore, Receiver, ExampleStateError
from tgdata import TgData, MessageBatch
from tgdata.backfill import BackfillStartRequest, BackfillRunRef, BackfillPrepareContext, BackfillDeliveryRef
from tgdata.backfill_engine import BackfillEngine
from tgdata.smoke_tests.test_25_backfill_delivery import sample, request, CHAT, NOW, forbidden_reader


class SyntheticReader(TgData):
    async def get_message_batch(self, chat_id, *, after_id=0, limit=200,
                                download_media_to=None, start_date=None, end_date=None):
        return sample(chat=chat_id,after=after_id,count=min(limit,2),stop='end')


async def child(path,action,value=None):
    database=ApplicationDatabase(path);backend=NamespaceStore(database,'history')
    if action=='claim':
        print(json.dumps(await NamespaceStore(database,'race').compare_and_swap(CHAT,None,value)))
        return
    req=BackfillStartRequest.from_dict(database.get('request'))
    eng=BackfillEngine(backend,req.collection_id,read_batch=lambda chat,**kw:async_batch(chat,kw))
    started=await eng.start(req,submission='new')
    database.remember('run',started.status.run.to_dict())
    turn=await eng.prepare(BackfillPrepareContext.from_status(started.status))
    Receiver(database,'archive').accept_backfill(turn.batch,turn.delivery)
    os._exit(73)  # Real receiver commit occurred, no library ack was made.


async def async_batch(chat,kw):
    return sample(chat=chat,after=kw['after_id'],count=2,stop='end')


async def checks():
    results=[]
    with tempfile.TemporaryDirectory(prefix='tgdata_stage7_prebuild_') as tmp:
        path=Path(tmp)/'application.sqlite3';database=ApplicationDatabase(path,create=True)
        one,two=NamespaceStore(database,'one'),NamespaceStore(database,'two')
        assert await one.compare_and_swap(CHAT,None,'first')
        assert not await one.compare_and_swap(CHAT,None,'other')
        assert await two.load(CHAT) is None and await two.compare_and_swap(CHAT,None,'independent')
        assert await one.compare_and_swap(CHAT,'first','second')
        assert await one.load(CHAT)=='second' and await two.load(CHAT)=='independent'
        results.append('actual isolated namespaces and exact CAS')
        processes=[subprocess.Popen([sys.executable,__file__,'--child',str(path),'claim',v],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for v in ('left','right')]
        outcomes=[]
        for process in processes:
            out,err=process.communicate(timeout=20);assert process.returncode==0,err
            outcomes.append(json.loads(out))
        assert sorted(outcomes)==[False,True]
        results.append('actual competing process CAS: exactly one winner')
        receiver=Receiver(database,'archive');batch=sample(count=1)
        ref=BackfillRunRef('probe',CHAT,1,'run')
        first=BackfillDeliveryRef(ref,'archive',batch.batch_id)
        assert receiver.accept_backfill(batch,first) and not receiver.accept_backfill(batch,first)
        changed=batch.messages[0];changed['text']='different-valid-observation'
        other=MessageBatch._from_records(CHAT,batch.after_id,[changed],'references','limit')
        second=BackfillDeliveryRef(ref,'archive',other.batch_id)
        assert receiver.accept_backfill(other,second)
        assert receiver.observation(first).to_json()==batch.to_json()
        assert receiver.observation(second).to_json()==other.to_json()
        assert receiver.summary()['receipts']==2 and receiver.summary()['messages']==1
        for wrong in (replace(first,destination_id='foreign'),replace(first,batch_id='0'*64),
                      replace(first,run=replace(ref,chat_id=CHAT-1))):
            try:receiver.accept_backfill(batch,wrong)
            except ExampleStateError:pass
            else:raise AssertionError('receiver accepted wrong scope')
        results.append('full observations retained across same-ID dedup; wrong scope refuses')
        missing=Path(tmp)/'missing.sqlite3'
        try:ApplicationDatabase(missing)
        except ExampleStateError:pass
        else:raise AssertionError('missing known database silently created')
        assert not missing.exists()
        empty=Path(tmp)/'empty.sqlite3';empty.touch()
        try:ApplicationDatabase(empty)
        except ExampleStateError:pass
        else:raise AssertionError('missing known schema silently created')
        results.append('known missing file/schema refuses without provisioning')
        # A distinct actual application database keeps the crash observation count independent.
        crash_path=Path(tmp)/'crash.sqlite3';app=ApplicationDatabase(crash_path,create=True)
        req=request(batch_size=3);app.remember('request',req.to_dict())
        daily=NamespaceStore(app,'daily');tg=SyntheticReader('/unused.ini',sync_store=daily)
        await tg.initialize_sync(CHAT,after_id=100);daily_before=await daily.load(CHAT)
        result=subprocess.run([sys.executable,__file__,'--child',str(crash_path),'receive'],
                              capture_output=True,text=True,timeout=20)
        assert result.returncode==73,(result.returncode,result.stderr)
        reopened=ApplicationDatabase(crash_path);saved_ref=BackfillRunRef.from_dict(reopened.get('run'))
        engine=BackfillEngine(NamespaceStore(reopened,'history'),req.collection_id,read_batch=forbidden_reader)
        started=await engine.start(req,submission='retry');assert not started.applied and started.status.run==saved_ref
        turn=await engine.prepare(BackfillPrepareContext.from_status(started.status))
        destination=Receiver(reopened,'archive')
        assert turn.replayed and destination.observation(turn.delivery).to_json()==turn.batch.to_json()
        assert not destination.accept_backfill(turn.batch,turn.delivery)
        done=await engine.acknowledge(turn.delivery)
        assert done.after_id==102 and done.terminal_outcome=='completed'
        assert await daily.load(CHAT)==daily_before
        daily_batch=await tg.sync_group(CHAT,limit=2)
        destination.accept_daily('daily',daily_batch);await tg.acknowledge_sync(CHAT,daily_batch.batch_id)
        assert (await engine.status(saved_ref))==done and destination.summary()['messages']==2
        await tg.close()
        results.append('owned receiver-commit exit/reopen: exact replay, one effect, independent daily/history')
        successor=replace(req,run_id='second',expected_predecessor=saved_ref)
        status=(await engine.start(successor,submission='new')).status
        original=sqlite3.connect
        class BadClose(sqlite3.Connection):
            def close(self):
                hit=self.total_changes>0
                super().close()
                if hit:raise sqlite3.OperationalError('injected lost reply')
        def connect(*a,**kw):kw['factory']=BadClose;return original(*a,**kw)
        args=dict(command_id='pause',expected_control_revision=0,action='pause')
        with patch('prebuild_store.sqlite3.connect',side_effect=connect):
            paused=await engine.control(status.run,**args)
        assert paused.applied and not (await engine.control(status.run,**args)).applied
        results.append('actual committed-then-close-error reconciles existing lifecycle command')
        class BadCleanup(sqlite3.Connection):
            def rollback(self):raise sqlite3.OperationalError('injected rollback')
            def close(self):super().close();raise sqlite3.OperationalError('injected close')
        def connect(*a,**kw):kw['factory']=BadCleanup;return original(*a,**kw)
        primary=ValueError('chosen primary failure')
        with patch('prebuild_store.sqlite3.connect',side_effect=connect):
            try:
                with app.transaction():raise primary
            except ValueError as error:assert error is primary
            else:raise AssertionError('primary error disappeared')
        results.append('actual cleanup failures do not replace primary error')
    print(json.dumps(dict(result='PASS',checks=results,count=len(results),
        product='unchanged 0d6bb26',evidence='LOCAL real SQLite/process/receiver; synthetic batch inputs, no Telegram'),indent=2))


if __name__=='__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        if len(sys.argv)>1 and sys.argv[1]=='--child':asyncio.run(child(*sys.argv[2:]))
        else:asyncio.run(checks())
