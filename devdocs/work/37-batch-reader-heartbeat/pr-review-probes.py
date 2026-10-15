"""Fresh PR38 histories against the product checkout; synthetic wire, real SDK."""
import asyncio
import hashlib
import inspect
import json
import logging
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve();sys.path.insert(0,str(ROOT))
from telethon import errors,functions,types
from telethon.client import users as sdk_users
from tgdata import SQLiteSyncStore,PoolReadCapture,SyncStorageError,BatchFormatError
from tgdata.sync_engine import SyncEngine
from tgdata.batch_heartbeat import heartbeat_scope
import tgdata.batch_heartbeat as hb
from tgdata.smoke_tests import test_19_message_batches as b
from tgdata.smoke_tests import test_25_backfill_delivery as d
from tgdata.smoke_tests import test_31_account_pool as p
from tgdata.smoke_tests import pool_storage_cases as ps
f=b.f;CHAT=d.CHAT;RESULTS=[]

async def until(predicate):
    for _ in range(10000):
        if predicate():return
        await asyncio.sleep(.001)
    raise AssertionError('expected boundary not reached')

async def quiet_watchdog(factory,timeout=.08):
    beats=[];last=[time.monotonic()]
    def beat(phase):beats.append(phase);last[0]=time.monotonic()
    task=asyncio.create_task(factory(beat))
    while not task.done():
        await asyncio.sleep(.005)
        if time.monotonic()-last[0]>timeout:
            task.cancel()
            try:await task
            except asyncio.CancelledError:pass
            return 'stalled',beats
    return await task,beats


def media_then_stall(sender):
    original=sender.send;chunks=[0]
    def send(request,ordered=False):
        if isinstance(f.unwrap(request),functions.upload.GetFileRequest):
            chunks[0]+=1
            if chunks[0]==3:
                pending=asyncio.get_running_loop().create_future();sender.pending.append(pending);return pending
            value=original(request,ordered=ordered);pending=asyncio.get_running_loop().create_future()
            def complete():
                if not pending.done():pending.set_result(value.result())
            asyncio.get_running_loop().call_later(.02,complete);return pending
        return original(request,ordered=ordered)
    sender.send=send
    return chunks

async def daily_error_after_media_progress():
    tg,client,sender=b.instance();store=SQLiteSyncStore(f.TMP/'daily');tg.sync_engine=SyncEngine(tg.get_message_batch,store)
    await tg.initialize_sync(CHAT,after_id=100,media_mode='download')
    data=b'z'*(1024*1024);b.script_messages(sender,[f.message(101),b.document(102,data=data)])
    sender.files[b.ASSET_ID]=data
    first=types.upload.File(types.storage.FileUnknown(),0,data[:131072]);original=RuntimeError('SOURCE_ERROR')
    sender.file_script=[first,original]
    phases=[]
    def callback(phase):phases.append(phase);raise errors.ChannelPrivateError(request=None)
    try:await tg.sync_group(CHAT,limit=2,download_media_to=f.TMP/'media',heartbeat=callback)
    except RuntimeError as got:assert got is original
    else:raise AssertionError('source failure lost')
    assert 'media' in phases and original.partial_result.next_after_id==101
    before=list(sender.calls);replay=await tg.sync_group(CHAT,limit=2,download_media_to=f.TMP/'media')
    assert replay.to_json()==original.partial_result.to_json() and list(sender.calls)==before
    assert list((f.TMP/'media').iterdir())==[]
    return dict(prefix=101,pending_replay=True,media_before_error=phases.count('media'),same_error=True)

async def pool_progress_then_stall():
    e=await p.setup();data=b'x'*(1024*1024);s=e.senders[111]
    b.script_messages(s,[f.message(101),b.document(102,data=data)]);s.files[b.ASSET_ID]=data
    chunks=media_then_stall(s);cap=PoolReadCapture()
    result,beats=await quiet_watchdog(lambda beat:e.pool.read(CHAT,capture=cap,after_id=100,limit=2,download_media_to=f.TMP/'media',heartbeat=beat))
    assert result=='stalled' and beats.count('media')==2 and chunks[0]==3
    snap=cap.snapshot();assert snap.state=='cancelled' and snap.batch.next_after_id==101
    assert not e.senders[222].reads and e.budget.status(111).used==2
    count=len(beats);await e.pool.close();await asyncio.sleep(.01);assert len(beats)==count
    assert list((f.TMP/'media').iterdir())==[]
    return dict(media_beats=2,stalled=True,captured_prefix=101,budget_used=2,no_failover=True)

async def sdk_retry_parity():
    outcomes=[]
    for mode in ('none','normal','broken'):
        ledger,_=f.ledger(10);tg,client,sender=b.instance(ledger);beats=[];sleeps=[]
        sender.script=[errors.FloodPremiumWaitError(request=None,capture=1),errors.ServerError(request=None,message='RPC_FAIL',code=500),f.response([f.message(101)])]
        async def sleep(seconds):sleeps.append(seconds);await asyncio.sleep(0)
        def beat(phase):
            beats.append(phase)
            if mode=='broken':raise asyncio.CancelledError('callback only')
        with patch.object(sdk_users,'asyncio',SimpleNamespace(sleep=sleep)):
            batch=await tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=None if mode=='none' else beat)
        status=ledger.status(111);outcomes.append([batch.to_json(),sleeps,len(sender.reads),status.used,status.reserved,client.flood_sleep_threshold])
        if mode!='none':assert 'flood-wait' in beats and 'request-error' in beats
    assert outcomes[0]==outcomes[1]==outcomes[2]
    return dict(sleeps=outcomes[0][1],requests=outcomes[0][2],used=outcomes[0][3],reserved=outcomes[0][4],threshold=outcomes[0][-1])

async def pool_bad_callback_read_failure():
    e=await p.setup();error=errors.ChannelPrivateError(request=None)
    e.senders[111].script=[f.response([f.message(n) for n in reversed(range(101,201))]),error]
    cap=PoolReadCapture();beats=[]
    def callback(phase):beats.append(phase);raise ValueError('PRIVATE_CALLBACK')
    try:await e.pool.read(CHAT,capture=cap,after_id=100,limit=200,heartbeat=callback)
    except errors.ChannelPrivateError as got:assert got is error
    else:raise AssertionError('real source error disappeared')
    snap=cap.snapshot();assert snap.batch.next_after_id==200 and snap.state=='failed'
    assert not e.senders[222].reads and e.budget.status(111).used==200
    return dict(prefix=100,source_error=type(error).__name__,capture_state=snap.state,budget=200)

async def concurrent_cancel_budgeted():
    ledger,_=f.ledger(10);tg,client,sender=b.instance(ledger);sender.script=[f.PENDING,f.PENDING]
    a=[];z=[]
    ta=asyncio.create_task(tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=a.append))
    tz=asyncio.create_task(tg.get_message_batch(CHAT,after_id=200,limit=1,heartbeat=z.append))
    await until(lambda:len(sender.pending)==2);ta.cancel()
    try:await ta
    except asyncio.CancelledError:pass
    na=len(a);sender.pending[1].set_result(f.response([f.message(201)]));result=await tz
    await asyncio.sleep(0);assert len(a)==na and result.next_after_id==201
    assert sender.pending[0].cancelled() and ledger.status(111).used==2
    return dict(cancelled_beat_count=na,other_cursor=201,budget=2)

async def delayed_future_after_scope():
    beats=[];loop=asyncio.get_running_loop();pending=loop.create_future()
    class Sender:
        def send(self,*a,**k):return pending
    with heartbeat_scope(beats.append) as observer:
        result=hb._ObservedSender(Sender(),observer).send(object());assert result is pending
    pending.set_exception(RuntimeError('late failure'));await asyncio.sleep(0)
    assert beats==[] and result.exception() is not None
    return dict(future_identity=True,late_beats=0)

async def nested_scopes_restore():
    _,client,_=b.instance();a=[];z=[]
    with heartbeat_scope(a.append):
        await client(functions.updates.GetStateRequest());await asyncio.sleep(0)
        before=len(a)
        with heartbeat_scope(z.append):
            await client(functions.updates.GetStateRequest());await asyncio.sleep(0)
        assert len(a)==before and z
        await client(functions.updates.GetStateRequest());await asyncio.sleep(0)
    assert a.count('request')==2 and z.count('request')==1
    return dict(outer_requests=2,inner_requests=1)

async def list_future_failure_is_unchanged():
    results=[]
    for enabled in (False,True):
        _,client,sender=b.instance();original=sender.send;error=errors.ChannelPrivateError(request=None);beats=[]
        def send(request,ordered=False):
            if isinstance(request,list):
                good=original(request[0],ordered=ordered);bad=asyncio.get_running_loop().create_future();bad.set_exception(error)
                return [good,bad]
            return original(request,ordered=ordered)
        sender.send=send
        with heartbeat_scope(beats.append if enabled else None):
            try:await client([functions.updates.GetStateRequest(),functions.updates.GetStateRequest()])
            except errors.MultiError as got:
                assert got.exceptions[1] is error and got.exceptions[0] is None
                results.append((len(got.results),type(got.results[0]).__name__,type(got.exceptions[1]).__name__))
            else:raise AssertionError('multi-error not propagated')
            await asyncio.sleep(0)
        if enabled:assert 'request-error' in beats
    assert results[0]==results[1]
    return dict(results=results[0],same_original_error=True)

async def source_publication_does_not_keep_observer_alive():
    tg,client,sender=b.instance();store=SQLiteSyncStore(f.TMP/'daily');tg.sync_engine=SyncEngine(tg.get_message_batch,store)
    await tg.initialize_sync(CHAT,after_id=100);actual=store.compare_and_swap;entered=asyncio.Event();release=asyncio.Event()
    async def held(*args):entered.set();await release.wait();return await actual(*args)
    store.compare_and_swap=held;beats=[]
    task=asyncio.create_task(tg.sync_group(CHAT,limit=1,heartbeat=beats.append));await entered.wait();n=len(beats)
    await client(functions.updates.GetStateRequest());await asyncio.sleep(0);assert len(beats)==n
    task.cancel()
    try:await task
    except asyncio.CancelledError as got:assert got.partial_result.next_after_id==101
    else:raise AssertionError('cancelled publication succeeded')
    assert (await tg.get_sync_status(CHAT)).pending_batch_id is None and len(beats)==n
    return dict(source_complete=True,cancelled_publication=True,no_saved_receipt=True,late_beats=0)

async def real_connect_wait_is_alive():
    tg,client,sender=b.instance();sender.up=False;calls=[0]
    async def connect():
        calls[0]+=1
        if calls[0]==1:raise errors.FloodWaitError(request=None,capture=1)
        sender.up=True
    with patch.object(client,'connect',side_effect=connect),patch.object(hb,'_WAIT_SLICE',.02):
        result,beats=await quiet_watchdog(lambda beat:tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=beat),timeout=.15)
    assert result.next_after_id==101 and calls[0]==2 and beats.count('flood-wait')>=20
    return dict(connect_attempts=2,wait_beats=beats.count('flood-wait'),cursor=101)

async def invalid_pool_callbacks_do_not_admit():
    observations=[]
    for mode in ('raw','batch','daily','backfill'):
        e,state,provider,context=await ps.setup('raw' if mode=='batch' else mode);before=dict(state.counts);cap=PoolReadCapture()
        async def callback(phase):pass
        try:
            if mode=='raw':await e.pool.read(CHAT,capture=cap,after_id=100,heartbeat=callback)
            elif mode=='batch':await e.pool.get_message_batch(CHAT,capture=cap,after_id=100,heartbeat=callback)
            elif mode=='daily':await e.pool.sync_group(CHAT,capture=cap,heartbeat=callback)
            else:await e.pool.prepare_backfill(context,capture=cap,heartbeat=callback)
        except BatchFormatError:pass
        else:raise AssertionError('invalid callback accepted')
        assert state.counts==before and all(not s.calls for s in e.senders.values())
        observations.append(mode)
    return dict(no_admission=observations)

async def failing_callback_releases_reference():
    import weakref,gc
    tg,_,_=b.instance();events=[]
    class Callback:
        def __call__(self,phase):raise ValueError('PRIVATE')
    cb=Callback();ref=weakref.ref(cb)
    await tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=cb)
    del cb;await asyncio.sleep(0);gc.collect();assert ref() is None
    return dict(callback_released=True)

async def main():
    cases=[('daily media error preserves prefix and original exception',daily_error_after_media_progress),
           ('pool progresses then genuinely stalls',pool_progress_then_stall),
           ('premium and server retry parity under failing callback',sdk_retry_parity),
           ('pool source error with broken callback keeps capture',pool_bad_callback_read_failure),
           ('one concurrent budgeted read cancels independently',concurrent_cancel_budgeted),
           ('deferred Future completion after scope emits nothing',delayed_future_after_scope),
           ('nested scopes restore exact observer',nested_scopes_restore),
           ('batched SDK MultiError identity survives observation',list_future_failure_is_unchanged),
           ('cancelled publication cannot retain source heartbeat',source_publication_does_not_keep_observer_alive),
           ('actual connection recovery wait stays alive',real_connect_wait_is_alive),
           ('invalid callback refuses all pool entry points before admission',invalid_pool_callbacks_do_not_admit),
           ('failed callback object is released after scope',failing_callback_releases_reference)]
    for name,call in cases:
        with tempfile.TemporaryDirectory(prefix='tgdata37-pr-review-') as temp:
            f.TMP=d.TMP=Path(temp);f.CLIENTS.clear();p.POOLS.clear();start=time.monotonic()
            try:
                details=await asyncio.wait_for(call(),10)
                RESULTS.append(dict(name=name,status='PASS',seconds=round(time.monotonic()-start,4),details=details));print(name+': PASS',flush=True)
            except BaseException as error:
                RESULTS.append(dict(name=name,status='FAIL',error=type(error).__name__,message=str(error)));raise
            finally:
                for pool in p.POOLS:await pool.close()
                for client in f.CLIENTS:
                    for pending in getattr(client._sender,'pending',[]):
                        if not pending.done():pending.cancel()
                    client.session.close()

def save():
    OUT.write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        results=RESULTS,passed=sum(r['status']=='PASS' for r in RESULTS),
        helper_sha256=hashlib.sha256((ROOT/'tgdata/batch_heartbeat.py').read_bytes()).hexdigest()),indent=2)+'\n')

logging.disable(logging.CRITICAL)
try:
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        asyncio.run(main())
finally:save()
print('All {} fresh PR review histories passed.'.format(len(RESULTS)))
