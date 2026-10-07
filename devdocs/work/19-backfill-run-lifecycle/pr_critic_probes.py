"""Fresh PR20 probes against the exact product checkout; LOCAL, no network.

These are adversarial observations, not alternate lifecycle implementations.
Actual SQLite commits, actual public facade and actual SDK execute. Only wire
responses and identified storage reply timing are synthetic/injected.
"""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--checkout',type=Path,required=True)
args=parser.parse_args();ROOT=args.checkout.resolve();sys.path.insert(0,str(ROOT))
import tgdata
from tgdata import (TgData,SQLiteSyncStore,BackfillStorageError,BackfillStateError,
    BackfillConflictError,SyncStorageError,BackfillRunRef,BackfillDeliveryRef,health)
from telethon import errors
from tgdata.smoke_tests import test_29_backfill_public as u
d,f,b=u.d,u.f,u.b
ctx=u.ctx
CHAT=d.CHAT


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


app=module('pr20_receiver',ROOT/'examples/backfill_runs.py')
daily=module('pr20_daily_receiver',ROOT/'examples/daily_continuation.py')


async def setup(batch_size=2):
    actual=d.store();fault=d.FaultStore(actual);events=[]
    tg,client,sender=u.instance(fault,events=events);req=d.request(batch_size=batch_size)
    initial=(await tg.start_backfill(req,submission='new')).status;fault.calls=0
    return SimpleNamespace(tg=tg,store=actual,fault=fault,sender=sender,events=events,req=req,status=initial)


def local(store,events=None):return u.instance(store,offline=True,events=events)[0]


def receiver():return app.Receiver(app.ApplicationDatabase(b.directory()/'receiver.sqlite3',create=True),'archive')


async def publication_reply_after_receiver_and_ack():
    e=await setup();e.sender.script=[d.finite_response([f.message(101)])]
    e.fault.hold=2;e.fault.after[2]=OSError('INJECTED reply loss after real publication')
    task=asyncio.create_task(e.tg.prepare_backfill(ctx(e.status)))
    await asyncio.wait_for(e.fault.entered.wait(),5)
    # A second actor does local replay/acceptance while the original RPC has ended
    # but its publication reply remains unresolved. No second source reader.
    other=local(SQLiteSyncStore(e.store.path,create=False))
    with patch.object(other.connection_engine,'_load_config',side_effect=AssertionError('local config forbidden')):
        pending=await other.get_backfill_status(e.status.run)
        turn=await other.prepare_backfill(ctx(pending));assert turn.replayed
        dest=receiver();dest.accept_backfill(turn.batch,turn.delivery)
        done=await other.acknowledge_backfill(turn.delivery)
        assert done.terminal_outcome=='completed' and done.after_id==101
    before=await e.store.load(CHAT);count,snapshot=await u.prior_denial(e.tg,e.events)
    e.fault.release.set();error=await f.expect(BackfillStorageError,task)
    assert error.read_error is None and await e.store.load(CHAT)==before
    assert (await e.tg.get_backfill_status(done.run))==done and len(e.sender.reads)==1
    assert len(e.events)==count and e.tg._health.snapshot()==snapshot
    assert (await e.tg.prepare_backfill(ctx(done))).batch is None
    assert dest.observation(turn.delivery).to_json()==turn.batch.to_json()
    return dict(source_reads=1,after_id=101,terminal='completed',local_health_preserved=True)


async def ack_reply_after_newer_pending():
    e=await setup(batch_size=1);e.sender.script=[d.finite_response([f.message(101)])]
    first=await e.tg.prepare_backfill(ctx(e.status));dest=receiver();dest.accept_backfill(first.batch,first.delivery)
    assert not first.status.source_exhausted
    e.fault.calls=0;e.fault.hold=1;e.fault.after[1]=OSError('INJECTED old ack reply loss')
    task=asyncio.create_task(e.tg.acknowledge_backfill(first.delivery))
    await asyncio.wait_for(e.fault.entered.wait(),5)
    other,client,sender=u.instance(SQLiteSyncStore(e.store.path,create=False))
    current=await other.get_backfill_status(first.status.run);assert current.after_id==101
    sender.script=[d.finite_response([f.message(102)])]
    second=await other.prepare_backfill(ctx(current));assert second.status.pending_message_count==1
    before=await e.store.load(CHAT);e.fault.release.set();await f.expect(BackfillStorageError,task)
    duplicate=await e.tg.acknowledge_backfill(first.delivery)
    assert duplicate.after_id==101 and duplicate.pending_batch_id==second.batch.batch_id
    assert await e.store.load(CHAT)==before and len(e.sender.reads)==len(sender.reads)==1
    await f.expect(BackfillConflictError,e.tg.prepare_backfill(ctx(first.status)))
    replay=await e.tg.prepare_backfill(ctx(duplicate));assert replay.replayed
    assert replay.batch.to_json()==second.batch.to_json()
    return dict(total_source_reads=2,accepted=101,pending_next=102,duplicate_left_newer_pending=True)


async def namespace_isolation_both_directions():
    history=d.store();backfill=local(history);req=d.request()
    await backfill.start_backfill(req,submission='new');before=await history.load(CHAT)
    daily_tg=TgData('/forbidden.ini',sync_store=history)
    await f.expect(SyncStorageError,daily_tg.get_sync_status(CHAT))
    await f.expect(SyncStorageError,daily_tg.initialize_sync(CHAT,after_id=100))
    assert await history.load(CHAT)==before
    progress=d.store();daily_tg=TgData('/forbidden.ini',sync_store=progress)
    await daily_tg.initialize_sync(CHAT,after_id=100);before=await progress.load(CHAT)
    backfill=local(progress)
    await f.expect(BackfillStateError,backfill.start_backfill(req,submission='new'))
    assert await progress.load(CHAT)==before
    assert backfill.connection_engine._config is None and daily_tg.connection_engine._config is None
    return dict(wrong_kind_refusals=3,mutations=0,client_config_loads=0)


async def malformed_state_inside_unrelated_rpc_context():
    e=await setup();count,snapshot=await u.prior_denial(e.tg,e.events)
    with sqlite3.connect(e.store.path) as db:db.execute('UPDATE tgdata_sync_state SET data=?',('{broken',))
    raw=await e.store.load(CHAT)
    try:raise errors.AuthKeyUnregisteredError(None)
    except errors.AuthKeyUnregisteredError:
        for call in (e.tg.get_backfill_status(e.status.run),e.tg.start_backfill(e.req,submission='retry'),
                     e.tg.prepare_backfill(ctx(e.status))):
            error=await f.expect(BackfillStateError,call)
            assert health.classify(error,True) is None and error.__suppress_context__
    assert await e.store.load(CHAT)==raw and not e.sender.calls
    assert len(e.events)==count and e.tg._health.snapshot()==snapshot
    return dict(local_refusals=3,source_reads=0,local_health_preserved=True)


async def receiver_contracts_and_failed_reply():
    e=await setup(batch_size=1)
    observed=[]
    for text in ('first observed record','different observed record'):
        e.sender.script=[d.finite_response([f.message(101,text)])]
        observed.append(await e.tg.get_message_batch(CHAT,after_id=100,limit=1))
    assert observed[0].batch_id!=observed[1].batch_id
    dest=receiver();deliveries=[BackfillDeliveryRef(BackfillRunRef('scope-'+str(i),CHAT,1,'run'),'archive',x.batch_id)
        for i,x in enumerate(observed)]
    assert dest.accept_backfill(observed[0],deliveries[0])
    original=sqlite3.connect
    class LostReply(sqlite3.Connection):
        def close(self):
            changed=self.total_changes;super().close()
            if changed:raise sqlite3.OperationalError('INJECTED receiver reply loss after commit')
    def connect(*a,**kw):kw['factory']=LostReply;return original(*a,**kw)
    with patch.object(sqlite3,'connect',side_effect=connect):
        f.rejected(app.ExampleStateError,lambda:dest.accept_backfill(observed[1],deliveries[1]))
    assert not dest.accept_backfill(observed[1],deliveries[1])
    assert all(dest.observation(ref).to_json()==batch.to_json() for ref,batch in zip(deliveries,observed))
    assert dest.summary()['receipts']==2 and dest.summary()['messages']==1
    # This helper has a different, explicitly documented first-observation policy.
    old=daily.Destination(b.directory()/'daily.sqlite3')
    for batch in observed:old.accept(batch)
    with sqlite3.connect(old.path) as db:
        kept=json.loads(db.execute('SELECT record FROM example_messages').fetchone()[0])
        markers=db.execute('SELECT COUNT(*) FROM example_received_batches').fetchone()[0]
    assert kept==observed[0].messages[0] and markers==2
    return dict(scoped_snapshots=2,message_index_rows=1,lost_receiver_reply_recognized=True,
        daily_policy='explicit first-observation archive; not the full-snapshot backfill receiver')


async def main():
    assert Path(tgdata.__file__).resolve().is_relative_to(ROOT)
    cases=[publication_reply_after_receiver_and_ack,ack_reply_after_newer_pending,
        namespace_isolation_both_directions,malformed_state_inside_unrelated_rpc_context,
        receiver_contracts_and_failed_reply]
    with tempfile.TemporaryDirectory(prefix='tgdata_pr20_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        f.TMP=d.TMP=Path(tmp)
        try:
            for case in cases:
                result=await asyncio.wait_for(case(),20)
                print(json.dumps(dict(case=case.__name__,result='PASS',observed=result),sort_keys=True),flush=True)
        finally:
            for client in f.CLIENTS:await client.disconnect()
            f.CLIENTS.clear()
    print('Passed: 5/5 fresh public/SQLite/SDK/receiver probes; LOCAL, sockets forbidden')


if __name__=='__main__':asyncio.run(main())
