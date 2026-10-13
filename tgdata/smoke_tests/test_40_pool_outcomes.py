"""Public pool data ownership: real SDK/SQLite/budgets, controlled wire, no sockets.

Run: python -m tgdata.smoke_tests.test_40_pool_outcomes
The 25 groups preserve the complete ownership prebuild and earlier review controls.
"""
import asyncio
from dataclasses import FrozenInstanceError
import gc
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tgdata import (
    PoolReadCapture, PoolReadSnapshot, BackfillDeliveryRef,
    SyncStorageError, BackfillStorageError, SyncConflictError, BackfillUnknownReceipt,
)
from tgdata.pool_state import _SourceInterrupted
from tgdata.smoke_tests import test_31_account_pool as t
from tgdata.smoke_tests import pool_storage_cases as s
from tgdata.smoke_tests import test_39_pool_lifecycle as old
from tgdata.pool_lifecycle import _Invocation
assert Path(t.__file__).resolve().parents[2] == ROOT
MODES=('raw','batch','daily','backfill');MISSING=object();RESULTS=[]

async def observed(work):
    try:return await work
    except BaseException as error:return error

def count(cap):
    snap=cap.snapshot() if isinstance(cap,PoolReadCapture) else cap
    return len(snap.batch.messages) if snap.batch is not None else 0

async def until(predicate,task=None):
    for _ in range(2000):
        if predicate():return
        if task is not None and task.done():
            raise AssertionError(('call ended before expected boundary',await observed(task)))
        await asyncio.sleep(0)
    raise AssertionError('expected boundary was not reached in bounded loop turns')

async def setup(mode):return await s.setup('raw' if mode=='batch' else mode)

def call(e,mode,context,cap,limit=1,**kwargs):
    options={} if cap is MISSING else {'capture':cap}
    options.update(kwargs)
    if mode=='raw':return e.pool.read(t.CHAT,after_id=100,limit=limit,**options)
    if mode=='batch':return e.pool.get_message_batch(t.CHAT,after_id=100,limit=limit,**options)
    if mode=='daily':return e.pool.sync_group(t.CHAT,limit=limit,**options)
    return e.pool.prepare_backfill(context,**options)

async def pending(e,mode,context):
    return await s.pending(e,mode,context) if mode in ('daily','backfill') else None

async def held_settlement(mode,failed=False,after=True):
    e,state,provider,context=await setup(mode);original,size,charge=s.source(e,failed)
    entered,ending,release=asyncio.Event(),asyncio.Event(),asyncio.Event()
    calls,tasks=[0],[];actual=state.compare_and_swap
    async def held(*arguments):
        calls[0]+=1
        if calls[0]!=2:return await actual(*arguments)
        tasks.append(asyncio.current_task());entered.set()
        try:await asyncio.Event().wait()
        finally:
            ending.set();await release.wait()
            if after:await actual(*arguments)
    state.compare_and_swap=held
    return e,state,context,entered,ending,release,tasks,size,charge

async def binding_states():
    rows=[]
    for mode in MODES:
        e,state,_,context=await setup(mode)
        before=dict(state.counts)
        for bad in (MISSING,None,object()):
            try:work=call(e,mode,context,bad)
            except TypeError:assert bad is MISSING
            else:
                error=await observed(work)
                assert isinstance(error,t.PoolConfigurationError),(mode,bad,error)
        assert state.counts==before and not any(sender.calls for sender in e.senders.values())
        cap=PoolReadCapture();assert cap.snapshot().state=='unbound'
        s.source(e,False);result=await call(e,mode,context,cap)
        snap=cap.snapshot();assert snap.state=='succeeded' and count(snap)==1 and snap.error_type is None
        assert snap.account_id==111 and snap.batch.stop_reason in ('end','limit')
        try:snap.state='changed'
        except FrozenInstanceError:pass
        else:raise AssertionError('mutable snapshot')
        try:cap.state='changed'
        except AttributeError:pass
        else:raise AssertionError('mutable public capture')
        altered=snap.batch.messages;altered[0]['text']='altered';assert snap.batch.messages!=altered
        total=sum(len(sender.reads) for sender in e.senders.values())
        assert isinstance(await observed(call(e,mode,context,cap)),t.PoolConfigurationError)
        foreign,_,_,fc=await setup(mode)
        assert isinstance(await observed(call(foreign,mode,fc,cap)),t.PoolConfigurationError)
        assert cap.snapshot()==snap and not any(sender.calls for sender in foreign.senders.values())
        await e.pool.close();assert cap.snapshot()==snap
        assert sum(len(sender.reads) for sender in e.senders.values())==total
        rows.append(dict(mode=mode,state=snap.state,records=count(snap),single_use=True))
    e,state,_,_=await setup('raw');cap=PoolReadCapture();before=dict(state.counts)
    error=await observed(e.pool.read(t.CHAT,capture=cap,limit=0))
    assert isinstance(error,t.BatchFormatError) and cap.snapshot().state=='failed' and state.counts==before
    return rows

async def prestart_and_concurrent_binding():
    rows=[]
    for mode in MODES:
        e,state,_,ctx=await setup(mode);before=dict(state.counts);cap=PoolReadCapture()
        task=asyncio.create_task(call(e,mode,ctx,cap));task.cancel()
        assert isinstance(await observed(task),asyncio.CancelledError)
        assert cap.snapshot().state=='unbound' and state.counts==before
        async def queued():
            asyncio.current_task().cancel();return await call(e,mode,ctx,cap)
        task=asyncio.create_task(queued());assert isinstance(await observed(task),asyncio.CancelledError)
        assert cap.snapshot().state=='cancelled' and count(cap)==0 and state.counts==before
        assert not any(sender.calls for sender in e.senders.values())
        e,state,_,ctx=await setup(mode);e.senders[111].script=[t.f.PENDING];cap=PoolReadCapture()
        reader=asyncio.create_task(call(e,mode,ctx,cap))
        try:
            await until(lambda:bool(e.senders[111].pending),reader)
            assert isinstance(await observed(call(e,mode,ctx,cap)),t.PoolConfigurationError)
            assert cap.snapshot().state=='running' and not reader.done()
            reader.cancel();await observed(reader);assert cap.snapshot().state=='cancelled'
        finally:
            reader.cancel();await observed(reader)
        rows.append(dict(mode=mode,prestart_no_io=True,queued_stop=True,one_writer=True))
    return rows

async def early_page():
    rows=[]
    for mode in MODES:
        e,state,_,ctx=await setup(mode)
        e.senders[111].script=[t.f.response([t.f.message(n) for n in reversed(range(101,201))]),t.f.PENDING]
        cap=PoolReadCapture();reader=asyncio.create_task(call(e,mode,ctx,cap,limit=200))
        try:
            await until(lambda:bool(e.senders[111].pending),reader)
            first=cap.snapshot();assert first.state=='running' and count(first)==100
            assert first.batch.stop_reason=='interrupted' and first.account_id==111
            reader.cancel();reader.cancel();signal=await observed(reader)
            assert isinstance(signal,asyncio.CancelledError) and reader.cancelled()
            final=cap.snapshot();assert final.state=='cancelled' and count(final)==100
            assert final.batch.to_json()==first.batch.to_json() and first.state=='running'
            assert e.budget.status(111).used==200 and not e.senders[222].reads
            assert (await e.pool.get_pool_status()).accounts[0].attempt_id is not None
            assert await pending(e,mode,ctx) is None
            rows.append(dict(mode=mode,early_records=100,final_records=100,charge=200))
        finally:
            reader.cancel();await observed(reader)
    return rows

async def settlement_stops():
    rows=[]
    for mode in MODES:
        for failed in (False,True):
            for after in (False,True):
                for external in (False,True):
                    e,state,ctx,entered,ending,release,tasks,size,charge=await held_settlement(mode,failed,after)
                    cap=PoolReadCapture();reader=asyncio.create_task(call(e,mode,ctx,cap,200 if failed else 1));closer=None
                    try:
                        await entered.wait();initial=cap.snapshot()
                        assert initial.state=='running' and count(initial)==size and initial.batch.stop_reason=='interrupted'
                        if external:closer=asyncio.create_task(e.pool.close())
                        else:reader.cancel()
                        await ending.wait()
                        reader.cancel();reader.cancel()
                        if closer is not None:closer.cancel();closer.cancel()
                        await t.turns();assert not reader.done() and not tasks[0].done()
                        assert e.pool._active_task is reader and cap.snapshot().state=='running'
                        release.set()
                        if closer is not None:await observed(closer)
                        signal=await observed(reader)
                        assert isinstance(signal,asyncio.CancelledError) and reader.cancelled()
                        final=cap.snapshot();assert final.state=='cancelled' and count(final)==size
                        assert final.batch.to_json()==initial.batch.to_json()
                        if failed:assert final.read_error_type=='FloodWaitError'
                        row=json.loads(await state.actual.load())['accounts']['111']
                        assert (row['active'] is None) is after
                        assert row['not_before']==(t.f.NOW+7200 if failed and after else 0)
                        assert e.budget.status(111).used==charge and not e.senders[222].reads
                        assert await pending(e,mode,ctx) is None
                        assert tasks[0].done() and e.pool._active_task is None
                        await e.pool.close();await observed(reader)
                        assert cap.snapshot()==final and all(src._primary_client is None for src in e.pool._sources.values())
                        rows.append(dict(mode=mode,failed_source=failed,committed=after,external_close=external,records=size,charge=charge))
                    finally:
                        release.set();reader.cancel()
                        await asyncio.gather(reader,*([closer] if closer else []),return_exceptions=True)
    return rows

async def wrapper_retrieval():
    rows=[]
    for mode in MODES:
        for wrapper in ('direct','shield','gather_values','wait_for'):
            e,state,ctx,entered,ending,release,tasks,size,charge=await held_settlement(mode)
            cap=PoolReadCapture();reader=asyncio.create_task(call(e,mode,ctx,cap))
            async def observe():
                if wrapper=='shield':return await asyncio.shield(reader)
                if wrapper=='gather_values':return (await asyncio.gather(reader,return_exceptions=True))[0]
                if wrapper=='wait_for':return await asyncio.wait_for(reader,0.01)
                return await reader
            waiter=None
            try:
                await entered.wait();waiter=asyncio.create_task(observed(observe()))
                await t.turns()
                if wrapper!='wait_for':reader.cancel()
                await ending.wait();release.set();signal=await waiter
                assert isinstance(signal,TimeoutError if wrapper=='wait_for' else asyncio.CancelledError)
                assert reader.cancelled() and cap.snapshot().state=='cancelled' and count(cap)==1
                await observed(reader);await observed(reader);await e.pool.close()
                assert count(cap)==1 and e.budget.status(111).used==1 and tasks[0].done()
                rows.append(dict(mode=mode,wrapper=wrapper,signal=type(signal).__name__,retained=1))
            finally:
                release.set();reader.cancel()
                await asyncio.gather(reader,*([waiter] if waiter else []),return_exceptions=True)
    return rows

async def application_continuation():
    rows=[]
    for mode in MODES:
        e,state,ctx,entered,ending,release,tasks,_,_=await held_settlement(mode)
        cap=PoolReadCapture();handled,app_release=asyncio.Event(),asyncio.Event();holder={}
        async def application():
            try:return await call(e,mode,ctx,cap)
            except asyncio.CancelledError:
                handled.set()
                await holder['closer']  # This would cycle with a whole-Task join.
                await app_release.wait()
                raise
        reader=asyncio.create_task(application());closer=None
        try:
            await entered.wait();closer=holder['closer']=asyncio.create_task(e.pool.close())
            await ending.wait();release.set();await handled.wait()
            await until(closer.done);await closer
            assert not reader.done() and tasks[0].done() and e.pool._active_task is None
            assert all(src._primary_client is None for src in e.pool._sources.values())
            assert cap.snapshot().state=='cancelled' and count(cap)==1
            app_release.set();assert isinstance(await observed(reader),asyncio.CancelledError)
            rows.append(dict(mode=mode,close_done=True,unrelated_app_work_not_joined=True))
        finally:
            release.set();app_release.set()
            await asyncio.gather(reader,*([closer] if closer else []),return_exceptions=True)
    return rows

async def stale_completion():
    e,_,_,_=await setup('raw')
    with e.pool._operation():old_record=e.pool._active_invocation
    assert old_record.done.done() and old_record.caller is None
    requests=asyncio.current_task().cancelling()
    with e.pool._operation():
        new=e.pool._active_invocation;old_record.stop(new)
        assert asyncio.current_task().cancelling()==requests and not new.done.done()
    old_record.stop(None);assert asyncio.current_task().cancelling()==requests
    cap=PoolReadCapture();s.source(e,False);await call(e,'raw',None,cap)
    final=cap.snapshot();await e.pool.close();assert cap.snapshot()==final
    return dict(stale_stop_harmless=True,success_not_downgraded=True)

async def progress_publication():
    rows=[]
    for mode in ('daily','backfill'):
        for cancel in (False,True):
            e,state,provider,ctx=await setup(mode);s.source(e,False)
            entered,ending,release=asyncio.Event(),asyncio.Event(),asyncio.Event();calls=[0];tasks=[]
            actual=provider.compare_and_swap
            async def held(*arguments):
                calls[0]+=1
                if calls[0]!=(1 if mode=='daily' else 2):return await actual(*arguments)
                tasks.append(asyncio.current_task());entered.set()
                try:await release.wait()
                finally:
                    ending.set();await release.wait();result=await actual(*arguments)
                return result
            provider.compare_and_swap=held
            cap=PoolReadCapture();reader=asyncio.create_task(call(e,mode,ctx,cap))
            try:
                await entered.wait();assert e.pool._active_task is None
                early=cap.snapshot();assert early.state=='running' and count(early)==1 and early.batch.stop_reason=='interrupted'
                await e.pool.close();assert not reader.done() and cap.snapshot()==early
                assert all(src._primary_client is None for src in e.pool._sources.values())
                if cancel:
                    reader.cancel();await ending.wait();reader.cancel();await t.turns()
                    assert not reader.done() and not tasks[0].done()
                release.set();result=await observed(reader)
                assert cap.snapshot().state==('cancelled' if cancel else 'succeeded') and count(cap)==1
                if cancel:assert isinstance(result,asyncio.CancelledError) and reader.cancelled()
                assert await pending(e,mode,ctx) is not None and tasks[0].done() and e.budget.status(111).used==1
                assert early.state=='running' and early.batch.stop_reason=='interrupted'
                rows.append(dict(mode=mode,cancelled=cancel,early=1,pending=True,close_preceded_public_end=True))
            finally:
                release.set();reader.cancel();await observed(reader)
    return rows

async def paired_faults():
    rows=[]
    for mode in ('daily','backfill'):
        for account_commit in (False,True):
            for progress_commit in (False,True):
                e,state,provider,ctx=await setup(mode);s.source(e,True)
                state.arm('compare_and_swap',2,account_commit)
                provider.arm('compare_and_swap',1 if mode=='daily' else 2,progress_commit)
                cap=PoolReadCapture();reader=asyncio.create_task(call(e,mode,ctx,cap,200))
                error=await observed(reader);snap=cap.snapshot()
                assert isinstance(error,Exception) and not reader.cancelled() and reader.cancelling()==0
                assert snap.state=='failed' and count(snap)==100 and snap.read_error_type=='FloodWaitError'
                assert snap.batch.stop_reason=='interrupted'
                row=json.loads(await state.actual.load())['accounts']['111']
                assert (row['active'] is None) is account_commit
                assert row['not_before']==(t.f.NOW+7200 if account_commit else 0)
                assert bool(await pending(e,mode,ctx)) is progress_commit
                assert e.budget.status(111).used==200 and not e.senders[222].reads
                provider.armed=None
                rows.append(dict(mode=mode,account_commit=account_commit,progress_commit=progress_commit,records=100))
    return rows

async def exact_receipts_and_local_replay():
    rows=[]
    for mode in ('daily','backfill'):
        e,state,provider,ctx=await setup(mode);s.source(e,False)
        actual_write,actual_load=provider.compare_and_swap,provider.load
        calls=[0];unknown=[False]
        async def write(*arguments):
            calls[0]+=1;result=await actual_write(*arguments)
            if calls[0]==(1 if mode=='daily' else 2):
                unknown[0]=True;own=asyncio.get_running_loop().create_future();own.cancel();await own
            return result
        async def load(*arguments):
            if unknown[0]:raise OSError(t.SECRET)
            return await actual_load(*arguments)
        provider.compare_and_swap=write;provider.load=load
        cap=PoolReadCapture();error=await observed(call(e,mode,ctx,cap));unknown[0]=False
        assert isinstance(error,Exception) and cap.snapshot().state=='failed' and count(cap)==1
        stored=await pending(e,mode,ctx);assert stored is not None and stored!=cap.snapshot().batch.batch_id
        if mode=='daily':wrong=e.pool.acknowledge_sync(t.CHAT,cap.snapshot().batch.batch_id)
        else:wrong=e.pool.acknowledge_backfill(BackfillDeliveryRef(ctx.run,(await e.pool.get_backfill_status(ctx.run)).destination_id,cap.snapshot().batch.batch_id))
        assert isinstance(await observed(wrong),Exception) and await pending(e,mode,ctx)==stored
        await e.pool.close()
        class NoStore:
            async def load(self):raise AssertionError('local replay accessed account state')
            async def compare_and_swap(self,*arguments):raise AssertionError('local replay wrote account state')
        e.pool._store=NoStore()
        for account in e.pool.accounts:Path(account.config_path).unlink()
        replay_cap=PoolReadCapture()
        with patch.object(e.budget,'status',side_effect=AssertionError('local replay accessed budget')):
            replay=await call(e,mode,ctx,replay_cap)
            snap=replay_cap.snapshot();assert snap.state=='succeeded' and count(snap)==1 and snap.account_id is None
            assert snap.batch.batch_id==stored
            snap.batch.save(t.path('delivered'))  # actual receiver artifact before ack
            if mode=='daily':await e.pool.acknowledge_sync(t.CHAT,replay.batch_id)
            else:await e.pool.acknowledge_backfill(replay.delivery)
            assert await pending(e,mode,ctx) is None
        rows.append(dict(mode=mode,wrong_hash_refused=True,local_replay_records=1,acknowledged=True))
    return rows

async def attempt_provenance():
    rows=[]
    for mode in MODES:
        e,state,_,ctx=await setup(mode)
        e.senders[111].script=[t.errors.FloodWaitError(request=None,capture=7200)]
        e.senders[222].script=[t.d.finite_response([t.f.message(101)])]
        actual=state.compare_and_swap;calls=[0];entered,release=asyncio.Event(),asyncio.Event()
        async def held(*arguments):
            calls[0]+=1
            if calls[0]==4:entered.set();await release.wait()
            return await actual(*arguments)
        state.compare_and_swap=held
        cap=PoolReadCapture();reader=asyncio.create_task(call(e,mode,ctx,cap))
        try:
            await entered.wait();snap=cap.snapshot()
            assert snap.state=='running' and snap.account_id==222 and snap.read_error_type is None and count(snap)==1
            release.set();await reader;assert cap.snapshot().read_error_type is None and cap.snapshot().account_id==222
            rows.append(dict(mode=mode,first_failure='FloodWaitError',batch_account=222,stale_error_cleared=True))
        finally:release.set();await observed(reader)
        e,_,_,ctx=await setup(mode)
        e.senders[111].script=[t.errors.FloodWaitError(request=None,capture=7200)]
        e.senders[222].script=[t.errors.ChannelPrivateError(request=None)]
        cap=PoolReadCapture();error=await observed(call(e,mode,ctx,cap))
        assert isinstance(error,t.PoolUnavailable) and count(cap)==0
        assert cap.snapshot().read_error_type=='ChannelPrivateError' and cap.snapshot().account_id is None
        e,_,_,ctx=await setup(mode);e.senders[111].identities=[222];cap=PoolReadCapture()
        error=await observed(call(e,mode,ctx,cap))
        assert isinstance(error,t.PoolIdentityError) and count(cap)==0 and cap.snapshot().account_id is None
        assert not any(sender.reads for sender in e.senders.values())
    return rows

async def monitor_finalization():
    rows=[]
    for failed in (False,True):
        e,_,_,ctx=await setup('raw');await old.seed_report(e);e.pool.drain_health_events();s.source(e,failed)
        entered=asyncio.Event();actual=e.pool._sources[111].monitor._safely
        async def held(*arguments):
            await actual(*arguments);entered.set();await asyncio.Event().wait()
        e.pool._sources[111].monitor._safely=held
        cap=PoolReadCapture();reader=asyncio.create_task(call(e,'raw',ctx,cap,200 if failed else 1))
        try:
            await entered.wait();early=cap.snapshot();assert early.state=='running' and count(early)==(100 if failed else 1)
            reader.cancel();signal=await observed(reader)
            assert isinstance(signal,asyncio.CancelledError) and count(cap)==count(early)
            if failed:assert cap.snapshot().read_error_type=='FloodWaitError'
            rows.append(dict(source_failed=failed,early_records=count(early),terminal=cap.snapshot().state))
        finally:reader.cancel();await observed(reader)
    return rows

async def media_early():
    e,_,_,ctx=await setup('raw')
    first=t.b.document(101);second=t.b.document(102,asset_id=t.b.ASSET_ID+1)
    e.senders[111].script=[t.d.finite_response([second,first])]
    e.senders[111].file_script=[t.b.types.upload.File(t.b.types.storage.FileUnknown(),0,t.b.PAYLOAD),t.f.PENDING]
    cap=PoolReadCapture();root=t.path('media-capture')
    reader=asyncio.create_task(call(e,'raw',ctx,cap,2,download_media_to=root))
    try:
        await until(lambda:bool(e.senders[111].pending),reader)
        snap=cap.snapshot();assert snap.state=='running' and count(snap)==1
        assert snap.batch.messages[0]['id']=='101' and snap.batch.media_mode=='download'
        blob=snap.batch.messages[0]['media']['blob']
        assert blob is not None and (root/blob['path']).read_bytes()==t.b.PAYLOAD
        reader.cancel();await observed(reader)
        assert cap.snapshot().state=='cancelled' and count(cap)==1 and not e.senders[222].reads
        assert not list(root.glob('.tgdata-*.tmp'))
        return dict(complete_records=1,incomplete_media_record_excluded=True)
    finally:reader.cancel();await observed(reader)

async def retention_and_empty_results():
    rows=[]
    for mode in MODES:
        e,_,_,ctx=await setup(mode);e.senders[111].script=[t.d.finite_response([])]
        cap=PoolReadCapture();await call(e,mode,ctx,cap)
        assert cap.snapshot().state=='succeeded' and count(cap)==0
        await e.pool.close()
        rows.append(dict(mode=mode,state=cap.snapshot().state,records=0))
    e,state,_,ctx=await setup('raw');s.source(e,True);cap=PoolReadCapture()
    error=await observed(call(e,'raw',ctx,cap,200));snap=cap.snapshot()
    assert snap.read_error_type=='FloodWaitError' and snap.error_type=='FloodWaitError'
    saved=snap.batch.to_json();del error;await e.pool.close();gc.collect()
    assert cap.snapshot().batch.to_json()==saved
    private=object.__getattribute__(cap,'_PoolReadCapture__state')
    assert private.records is None and private.address is None and private.expected_account is None
    for value in vars(private).values():
        assert value is None or isinstance(value,(str,int,t.MessageBatch)),type(value)
    assert t.SECRET not in repr(snap) and t.SECRET not in repr(cap)
    # New data/diagnostic acquisition on another call cannot mutate this capture.
    foreign,_,_,_=await setup('raw');await call(foreign,'raw',None,PoolReadCapture())
    assert cap.snapshot()==snap
    return dict(empty=rows,terminal_state_plain=True,retained_records=100)

async def provider_refusals_capture():
    rows=[]
    for mode in MODES:
        for method in ('load','compare_and_swap'):
            for after in (False,True):
                e,state,_,ctx=await setup(mode);state.arm(method,1,after)
                cap=PoolReadCapture();reader=asyncio.create_task(call(e,mode,ctx,cap))
                error=await observed(reader);snap=cap.snapshot()
                assert isinstance(error,t.PoolStorageError) and not reader.cancelled() and reader.cancelling()==0
                assert snap.state=='failed' and snap.batch is None and snap.account_id is None
                assert snap.read_error_type is None and snap.error_type=='PoolStorageError'
                assert not any(sender.calls for sender in e.senders.values()) and e.budget.status(111).used==0
                row=json.loads(await state.actual.load())['accounts']['111']
                assert (row['active'] is not None) is (method=='compare_and_swap' and after)
                assert all(task.done() for task in state.tasks)
                rows.append(dict(mode=mode,method=method,after=after,state=snap.state,records=0))
    return rows

async def local_wait_capture():
    e=await t.setup(history=t.SQLiteSyncStore(t.path('capture-wait')))
    started=await e.pool.start_backfill(t.d.request(pause_seconds=30,batch_size=1),submission='new')
    ctx=t.BackfillPrepareContext.from_status(started.status)
    s.source(e,False)
    turn=await call(e,'backfill',ctx,PoolReadCapture())
    status=await e.pool.acknowledge_backfill(turn.delivery)
    ctx=t.BackfillPrepareContext.from_status(status)
    reads=sum(len(sender.reads) for sender in e.senders.values())
    cap=PoolReadCapture();wait=await call(e,'backfill',ctx,cap)
    assert wait.wait_seconds>0 and cap.snapshot().state=='succeeded' and cap.snapshot().batch is None
    changed=await e.pool.control_backfill(ctx.run,command_id='pause-capture',
        expected_control_revision=ctx.expected_control_revision,action='pause')
    ctx=t.BackfillPrepareContext.from_status(changed.status)
    await e.pool.close();paused=PoolReadCapture();await call(e,'backfill',ctx,paused)
    assert paused.snapshot().state=='succeeded' and paused.snapshot().batch is None
    assert sum(len(sender.reads) for sender in e.senders.values())==reads
    return dict(wait_without_source=True,paused_after_close=True,records=0)

async def diagnostic_bounds():
    e,_,_,_=await setup('raw')
    error_type=type('X'*129,(RuntimeError,),{})
    original=error_type(t.SECRET)
    e.senders[111].script=[t.f.response([t.f.message(n) for n in reversed(range(101,201))]),original]
    cap=PoolReadCapture();error=await observed(call(e,'raw',None,cap,200));snap=cap.snapshot()
    assert isinstance(error,t.PoolStateError) and snap.state=='failed' and count(cap)==100
    assert snap.read_error_type=='Exception' and snap.error_type=='PoolStateError'
    assert t.SECRET not in repr(snap) and len(snap.read_error_type)<=128
    assert e.budget.status(111).used==200 and not e.senders[222].reads
    return dict(actual_prefix=100,safe_type_fallback=True,private_message_not_retained=True)

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

REVIEW_CASES=[committed_reply_races_caller_stop,close_during_late_provider_commit,
       state_only_ack_owns_io_after_close,independent_store_failures_compose,
       error_prefix_is_not_the_stored_receipt,invocation_and_preidentity_interruptions,
       caller_stop_after_source_before_reporting_end,reporting_loss_does_not_change_wait_or_data]


CASES=[('binding_states',binding_states),('prestart_concurrent_binding',prestart_and_concurrent_binding),
       ('early_pagination',early_page),('settlement_stops',settlement_stops),
       ('public_wrappers',wrapper_retrieval),('application_continuation',application_continuation),
       ('stale_completion',stale_completion),('progress_publication',progress_publication),
       ('paired_faults',paired_faults),('receipts_local_replay',exact_receipts_and_local_replay),
       ('attempt_provenance',attempt_provenance),('monitor_finalization',monitor_finalization),
       ('early_media',media_early),('retention_empty',retention_and_empty_results),
       ('provider_refusals_capture',provider_refusals_capture),('local_wait_capture',local_wait_capture),
       ('diagnostic_bounds',diagnostic_bounds)]

CASES += [(function.__name__, function) for function in REVIEW_CASES]

async def main(directory):
    t.f.TMP=t.d.TMP=directory
    for name,fn in CASES:
        print(json.dumps(dict(start=name)),flush=True)
        try:details=await asyncio.wait_for(fn(),25)
        except BaseException as error:
            traceback.print_exc();RESULTS.append(dict(name=name,passed=False,error=type(error).__name__))
        else:RESULTS.append(dict(name=name,passed=True,details=details))
        finally:
            for pool in t.POOLS:await pool.close()
            t.POOLS.clear()
        print(json.dumps(RESULTS[-1]),flush=True)
    total=sum(row['passed'] for row in RESULTS)
    print(json.dumps(dict(summary=dict(passed=total,total=len(CASES)))),flush=True)
    print('Passed: {}/{}'.format(total,len(CASES)),flush=True)
    return 0 if total==len(CASES) else 1

if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='tgdata17-outcome-case-') as directory, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        sys.exit(asyncio.run(main(Path(directory))))
