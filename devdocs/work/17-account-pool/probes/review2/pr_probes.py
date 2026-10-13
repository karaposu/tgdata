"""Fresh PR soundness histories on actual SDK/SQLite; no product patches."""
import asyncio
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
from tgdata import SyncStorageError, BackfillStorageError, SyncConflictError, BackfillDeliveryRef, BackfillUnknownReceipt
from tgdata.pool_state import _SourceInterrupted
from tgdata.smoke_tests import test_31_account_pool as t
from tgdata.smoke_tests import pool_storage_cases as s

RESULTS=[]
async def own_cancel():
    future=asyncio.get_running_loop().create_future();future.cancel();await future

def prefix(error):return len(getattr(getattr(error,'partial_result',None),'messages',()))

def error_chain(error):
    result=[];seen=set()
    while error is not None and id(error) not in seen:
        seen.add(id(error));result.append(error);error=getattr(error,'read_error',None)
    return result

async def committed_reply_races_caller_stop():
    rows=[]
    for phase in ('admission','settlement'):
        for internal in (False,True):
            e,state,_,_=await s.setup('raw');s.source(e,False)
            actual=state.compare_and_swap; calls=[0];holder={}
            async def write(*args):
                calls[0]+=1
                result=await actual(*args)
                if calls[0]==(1 if phase=='admission' else 2):
                    holder['reader'].cancel()
                    if internal:await own_cancel()
                return result
            state.compare_and_swap=write
            reader=holder['reader']=asyncio.create_task(t.read(e))
            result=await s.capture(reader)
            assert isinstance(result,asyncio.CancelledError) and reader.cancelling()==1
            settled=phase=='settlement'
            row=json.loads(await state.actual.load())['accounts']['111']
            assert (row['active'] is None) is settled
            assert prefix(result)==int(settled) and e.budget.status(111).used==int(settled)
            assert len(e.senders[111].reads)==int(settled) and not e.senders[222].calls
            assert e.pool._active_task is None and all(task.done() for task in state.tasks)
            rows.append(dict(phase=phase,component_cancel=internal,caller_stop=True,records=prefix(result),source_reads=int(settled)))
    return rows

async def close_during_late_provider_commit():
    rows=[]
    for phase in ('admission','settlement'):
        e,state,_,_=await s.setup('raw');s.source(e,False)
        original=state.compare_and_swap;calls=[0];tasks=[]
        entered,finalizing,release=asyncio.Event(),asyncio.Event(),asyncio.Event()
        async def held(*args):
            calls[0]+=1
            if calls[0]!=(1 if phase=='admission' else 2):return await original(*args)
            tasks.append(asyncio.current_task());entered.set()
            try:await asyncio.Event().wait()
            finally:
                finalizing.set();await release.wait();await original(*args)
        state.compare_and_swap=held
        reader=asyncio.create_task(t.read(e));closer=None
        try:
            await entered.wait();closer=asyncio.create_task(e.pool.close());await finalizing.wait()
            closer.cancel();await t.turns();closer.cancel();await t.turns()
            assert not reader.done() and not closer.done() and not tasks[0].done()
            assert e.pool._closed and e.pool._closing and e.pool._active_task is reader
            release.set();read_error=await s.capture(reader);close_error=await s.capture(closer)
            assert isinstance(read_error,asyncio.CancelledError) and isinstance(close_error,asyncio.CancelledError)
            assert all(task.done() for task in tasks) and all(src._primary_client is None for src in e.pool._sources.values())
            row=json.loads(await state.actual.load())['accounts']['111']
            settled=phase=='settlement'
            print(json.dumps(dict(observation='late_close_result',phase=phase,
                stored_active=row['active'] is not None,read_error=type(read_error).__name__,
                read_prefix=prefix(read_error),read_error_attributes=sorted(vars(read_error)),
                reader_requests=reader.cancelling(),source_reads=len(e.senders[111].reads),
                charge=e.budget.status(111).used)),flush=True)
            assert (row['active'] is None) is settled and prefix(read_error)==int(settled)
            assert e.budget.status(111).used==int(settled) and not e.senders[222].reads
            rows.append(dict(phase=phase,actual_late_commit=True,close_waited=True,all_clients_retired=True,records=prefix(read_error)))
        finally:
            release.set();await asyncio.gather(reader,*([closer] if closer else []),return_exceptions=True)
    return rows

async def state_only_ack_owns_io_after_close():
    e,_,provider,context=await s.setup('daily');s.source(e,False)
    batch=await s.read(e,'daily',context,1);actual=provider.compare_and_swap
    entered,finalizing,release=asyncio.Event(),asyncio.Event(),asyncio.Event();tasks=[]
    async def held(*args):
        tasks.append(asyncio.current_task());entered.set()
        try:await asyncio.Event().wait()
        finally:
            finalizing.set();await release.wait();await actual(*args)
    provider.compare_and_swap=held
    task=asyncio.create_task(e.pool.acknowledge_sync(t.CHAT,batch.batch_id))
    try:
        await entered.wait();assert e.pool._active_task is None
        await e.pool.close()
        assert not task.done() and all(src._primary_client is None for src in e.pool._sources.values())
        task.cancel();await finalizing.wait();task.cancel();await t.turns()
        assert not task.done() and not tasks[0].done()
        release.set();assert isinstance(await s.capture(task),asyncio.CancelledError)
        status=await e.pool.get_sync_status(t.CHAT)
        assert status.after_id==101 and status.pending_batch_id is None and tasks[0].done()
        assert e.budget.status(111).used==1
        return dict(close_did_not_own_ack=True,caller_joined_write=True,actual_after_id=101,charge=1)
    finally:
        release.set();await asyncio.gather(task,return_exceptions=True)

async def independent_store_failures_compose():
    rows=[]
    for mode in ('daily','backfill'):
        for pool_after in (False,True):
            for progress_after in (False,True):
                e,state,provider,context=await s.setup(mode)
                original,size,charge=s.source(e,True)
                state.arm('compare_and_swap',2,pool_after)
                provider.arm('compare_and_swap',1 if mode=='daily' else 2,progress_after)
                task=asyncio.create_task(s.read(e,mode,context,200));result=await s.capture(task)
                chain=error_chain(result)
                assert isinstance(result,(t.PoolStorageError,SyncStorageError,BackfillStorageError))
                assert chain[-1] is original and prefix(result)==size==100 and task.cancelling()==0
                assert result.partial_result.messages==original.partial_result.messages
                row=json.loads(await state.actual.load())['accounts']['111']
                assert (row['active'] is None) is pool_after
                assert row['not_before']==(t.f.NOW+7200 if pool_after else 0)
                assert bool(await s.pending(e,mode,context)) is progress_after
                assert e.budget.status(111).used==charge==200 and not e.senders[222].reads
                assert t.health.classify(result) is None
                rows.append(dict(mode=mode,pool_commit=pool_after,progress_commit=progress_after,
                                 error_chain=[type(err).__name__ for err in chain],records=100,charge=200))
    return rows

async def error_prefix_is_not_the_stored_receipt():
    rows=[]
    for mode in ('daily','backfill'):
        e,_,provider,context=await s.setup(mode);s.source(e,False)
        write,load=provider.compare_and_swap,provider.load;calls=[0];uncertain=[False]
        async def after_write(*args):
            calls[0]+=1;result=await write(*args)
            if calls[0]==(1 if mode=='daily' else 2):
                uncertain[0]=True;await own_cancel()
            return result
        async def unavailable_readback(*args):
            if uncertain[0]:await own_cancel()
            return await load(*args)
        provider.compare_and_swap=after_write;provider.load=unavailable_readback
        error=await s.capture(s.read(e,mode,context,1));uncertain[0]=False
        assert isinstance(error,SyncStorageError if mode=='daily' else BackfillStorageError) and prefix(error)==1
        calls_before=len(e.senders[111].reads)
        await e.pool.close()
        replay=await s.read(e,mode,context,1)
        batch=replay if mode=='daily' else replay.batch
        assert batch.stop_reason in ('limit','end') and error.partial_result.stop_reason=='interrupted'
        assert batch.messages==error.partial_result.messages and batch.batch_id!=error.partial_result.batch_id
        before=await provider.actual.load(t.CHAT)
        if mode=='daily':
            refused=await s.capture(e.pool.acknowledge_sync(t.CHAT,error.partial_result.batch_id))
            assert isinstance(refused,SyncConflictError)
            assert await provider.actual.load(t.CHAT)==before
            accepted=await e.pool.acknowledge_sync(t.CHAT,batch.batch_id)
        else:
            wrong=BackfillDeliveryRef(replay.delivery.run,replay.delivery.destination_id,error.partial_result.batch_id)
            refused=await s.capture(e.pool.acknowledge_backfill(wrong))
            assert isinstance(refused,BackfillUnknownReceipt)
            assert await provider.actual.load(t.CHAT)==before
            accepted=await e.pool.acknowledge_backfill(replay.delivery)
        assert accepted.after_id==101 and len(e.senders[111].reads)==calls_before
        rows.append(dict(mode=mode,different_hashes=True,error_receipt_refused=True,real_receipt_accepted=True,after_id=101))
    return rows

async def invocation_and_preidentity_interruptions():
    rows=[]
    for mode in ('pool','daily','backfill'):
        e,state,provider,context=await s.setup('daily' if mode=='daily' else 'backfill')
        target=state if mode=='pool' else provider
        def interrupted(*args):raise asyncio.CancelledError(t.SECRET)
        target.load=interrupted  # The callable fails before returning an awaitable.
        work=(e.pool.get_pool_status() if mode=='pool' else e.pool.get_sync_status(t.CHAT) if mode=='daily'
              else e.pool.get_backfill_status(context.run))
        task=asyncio.create_task(work);error=await s.capture(task)
        assert isinstance(error,{'pool':t.PoolStorageError,'daily':SyncStorageError,'backfill':BackfillStorageError}[mode])
        assert task.cancelling()==0 and t.SECRET not in str(error) and t.health.classify(error) is None
        assert not any(sender.calls for sender in e.senders.values())
        rows.append(dict(mode=mode,local_error=type(error).__name__,caller_requests=0))
    e,_,_,_=await s.setup('raw');actual=e.senders[111].send;hits=[]
    def send(request,ordered=False):
        if isinstance(t.f.unwrap(request),t.functions.updates.GetStateRequest):
            hits.append(True);future=asyncio.get_running_loop().create_future();future.cancel();return future
        return actual(request,ordered=ordered)
    e.senders[111].send=send
    task=asyncio.create_task(t.read(e));error=await s.capture(task)
    assert isinstance(error,_SourceInterrupted) and task.cancelling()==0 and hits
    assert (await e.pool.get_pool_status()).accounts[0].attempt_id is not None
    assert e.budget.status(111).used==0 and not e.senders[222].calls
    assert e.pool.drain_health_events()==dict(events=[],dropped=0)
    rows.append(dict(mode='preidentity-source',unresolved=True,charge=0,caller_requests=0))
    return rows

async def caller_stop_after_source_before_reporting_end():
    rows=[]
    for failed in (False,True):
        e,_,_,_=await s.setup('raw');_,size,charge=s.source(e,failed)
        monitor=e.pool._sources[111].monitor;actual=monitor._safely;entered=asyncio.Event()
        async def delayed(*args):
            await actual(*args);entered.set();await asyncio.Event().wait()
        monitor._safely=delayed
        task=asyncio.create_task(t.read(e,limit=200 if failed else 1))
        await entered.wait();task.cancel();error=await s.capture(task)
        assert isinstance(error,asyncio.CancelledError) and prefix(error)==size
        assert (await e.pool.get_pool_status()).accounts[0].attempt_id is not None
        assert e.budget.status(111).used==charge and not e.senders[222].reads
        assert e.pool._sources[111].task is None
        rows.append(dict(source_failed=failed,caller_stop=True,known_records=size,unresolved=True,charge=charge))
    return rows

async def reporting_loss_does_not_change_wait_or_data():
    e,_,_,_=await s.setup('raw')
    monitor=e.pool._sources[111].monitor
    async with monitor.call('prior',group=t.CHAT):
        for _ in range(128):await t.health.report(t.errors.ChannelPrivateError(request=None),'handled')
    # HealthMonitor deduplicates one error instance, so each above is a fresh real report.
    assert len(e.pool._observations.events)==128
    original,size,charge=s.source(e,True)
    result=await s.capture(t.read(e,limit=200))
    assert result is original and prefix(result)==100
    status=(await e.pool.get_pool_status(t.CHAT)).accounts[0]
    assert status.retry_at==t.f.NOW+7200 and status.attempt_id is None
    snapshot=e.pool.drain_health_events()
    assert len(snapshot['events'])==128 and snapshot['dropped']==1
    assert e.budget.status(111).used==charge==200 and not e.senders[222].reads
    return dict(events=128,dropped=1,known_wait=7200,records=size,charge=charge)

CASES=[committed_reply_races_caller_stop,close_during_late_provider_commit,
       state_only_ack_owns_io_after_close,independent_store_failures_compose,
       error_prefix_is_not_the_stored_receipt,invocation_and_preidentity_interruptions,
       caller_stop_after_source_before_reporting_end,reporting_loss_does_not_change_wait_or_data]

async def main(directory):
    t.f.TMP=t.d.TMP=directory
    for case in CASES:
        print(json.dumps(dict(start=case.__name__)),flush=True)
        error=None;observation=None
        try:observation=await asyncio.wait_for(case(),10)
        except BaseException as caught:
            error=caught;traceback.print_exc()
        finally:
            for pool in t.POOLS:await pool.close()
            t.POOLS.clear()
        row=dict(case=case.__name__,result='PASS' if error is None else 'FAIL',observation=observation,
                 error_type=type(error).__name__ if error else None)
        RESULTS.append(row);print(json.dumps(row),flush=True)
    summary=dict(groups=len(RESULTS),passed=sum(r['result']=='PASS' for r in RESULTS),
                 failed=[r['case'] for r in RESULTS if r['result']!='PASS'])
    print(json.dumps(dict(summary=summary)),flush=True)
    return 0 if not summary['failed'] else 1

if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='tgdata17-review-') as directory, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        sys.exit(asyncio.run(main(Path(directory))))
