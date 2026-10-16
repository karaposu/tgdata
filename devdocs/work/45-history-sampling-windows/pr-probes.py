"""Fresh PR49 probes; actual product tree, no network or product edits."""
import ast
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import random
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from unittest.mock import patch

ROOT=Path('/private/tmp/tgdata-45-history-pr')
sys.path.insert(0,str(ROOT))
import telethon
from telethon import errors
from telethon.extensions import BinaryReader
from telethon.tl import functions,types
from tgdata import HistoryCapture,HistorySampleError,GroupResponseError
from tgdata import group_activity as activity
from tgdata.history_sample import _identity
from tgdata.history_window import _HistoryWindow,_decode_date
from tgdata.smoke_tests import test_34_group_access as g
from tgdata.smoke_tests.test_46_group_activity import setup,page
from tgdata.smoke_tests.test_47_history_sampling import message,capture

fx,h,D=g.fx,g.h,g.DATE
BASE='77f2f53eba8bdc6922127a3b9118bf17de4efabf'
HEAD='559638a3624bcdba7684beb286e9c619144be455'


class WireHistory:
    def __init__(self,rows,page_cap=100):
        self.rows=sorted(rows,key=lambda r:r.id,reverse=True)
        self.page_cap=page_cap
        self.calls=[]
        self.slots=0

    def __call__(self,wire,req):
        with BinaryReader(bytes(req)) as reader:
            decoded=reader.tgread_object()
        self.calls.append(decoded)
        assert decoded.min_id==decoded.max_id==decoded.add_offset==0
        available=[]
        for row in self.rows:
            if decoded.offset_id and row.id>=decoded.offset_id: continue
            if decoded.offset_date.timestamp() and row.date>=decoded.offset_date: continue
            available.append(row)
        rows=available[:min(decoded.limit,self.page_cap)]
        self.slots+=len(rows)
        return g.Reply(page(rows,'channel'))


def oracle(records,size,eligible):
    populations=[[r for r in b['records'] if r['kind']=='message' and r['id'] in eligible]
                 for b in records]
    allocations=[0 for _ in populations]
    left=min(size,sum(map(len,populations)))
    while left:
        active=[i for i,rows in enumerate(populations) if allocations[i]<len(rows)]
        if left>=len(active):
            for i in active: allocations[i]+=1
            left-=len(active)
        else:
            picks=([active[(len(active)-1)//2]] if left==1 else
                   [active[int(j*(len(active)-1)/(left-1))] for j in range(left)])
            for i in picks: allocations[i]+=1
            left=0
    result=[]
    for rows,count in zip(populations,allocations):
        if count==0: continue
        picks=[(len(rows)-1)//2] if count==1 else [int(i*(len(rows)-1)/(count-1)) for i in range(count)]
        result.extend(int(rows[i]['id']) for i in picks)
    return tuple(result)


async def cleanup():
    for client in fx.CLIENTS:
        client._sender.close_error=None
        if client._sender.close_release is not None: client._sender.close_release.set()
        await client.disconnect()
    for tg in h.FACADES: await tg.close()
    await asyncio.gather(*h.RPC_TASKS,return_exceptions=True)
    fx.CLIENTS.clear();h.FACADES.clear();h.RPC_TASKS.clear();g.TRACE.clear()


async def probe_randomized_source_and_independent_selection():
    rng=random.Random(450049)
    selections=0
    for case in range(36):
        days=rng.randrange(1,10)
        dates=sorted(D+timedelta(days=day,seconds=second) for day in range(days)
                     for second in [rng.choice((0,1,43200,86399)) for _ in range(rng.randrange(0,20))])
        rows=[message(i+2,date,text='sample '+str(i)) for i,date in enumerate(dates)]
        rows.insert(0,message(1,D-timedelta(days=1)))
        history=WireHistory(rows,page_cap=rng.choice((1,3,100)))
        tg,f=g.setup(budget=True,responses={'GetHistoryRequest':history})
        f.budget.configure(222,10000)
        slots,calls=(1000,1000) if case%3==0 else (rng.randrange(1,60),rng.randrange(1,25))
        value=await capture(tg,end_date=D+timedelta(days=days),max_messages=slots,max_requests=calls)
        assert value.coverage['scanned_messages']==history.slots<=slots
        assert value.coverage['requests']==len(history.calls)<=calls
        assert f.budget.status(222).used==history.slots and f.budget.status(111).used==0
        for bucket in value.buckets:
            if bucket['end_reason'] is not None:
                expected={str(r.id) for r in rows if _decode_date(bucket['start_date'])<=r.date<_decode_date(bucket['end_date'])}
                assert {r['id'] for r in bucket['records']}==expected
        if case%3==0:
            assert value.coverage_complete and len(value.messages)==len(dates)
        for size in (0,1,2,7,300,10000):
            eligible={r['id'] for r in value.messages if int(r['id'])%3!=0}
            sample=value.sample(size=size,eligible_ids=eligible)
            assert sample.selected_ids==oracle(value.buckets,size,eligible)
            assert sample.to_json()==HistoryCapture.from_json(value.to_json()).sample(
                size=size,eligible_ids=list(reversed(sorted(eligible)))).to_json()
            for b in sample.to_dict()['buckets']:
                assert b['selected_messages']+b['omitted_messages']==b['eligible_messages']
                assert b['eligible_messages']+b['excluded_messages']==b['ordinary_messages']
            selections+=1
        await cleanup()
    print('36 wire histories; {} independent selection/replay comparisons PASS'.format(selections))


async def probe_activity_extraction_parity():
    source=subprocess.check_output(['git','show',BASE+':tgdata/group_activity.py'],cwd=ROOT,text=True)
    nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in ('_date','_page')]
    namespace=dict(vars(activity))
    from tgdata.group_operations import _identity as peer_identity
    namespace['_identity']=peer_identity
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'base_activity','exec'),namespace)
    window=_HistoryWindow(D,D+timedelta(days=1))
    replies=[page(),page([message(8)]),page([message(8)],'slice'),page([message(8),message(8)]),
        page([message(8,peer=types.PeerChat(7))]),page([message(8,D-timedelta(seconds=1))]),
        page([types.MessageEmpty(8,peer_id=None)],'channel'),types.messages.MessagesNotModified(1)]
    rows=[]
    for reply in replies:
        for limit,last,last_date in ((1,None,None),(10,None,None),(10,8,D),(0,None,None)):
            results=[]
            for function in (namespace['_page'],activity._page):
                try: result=('value',function(reply,-1000000000007,limit,last,last_date,window,D))
                except Exception as exc: result=('error',type(exc).__name__,str(exc))
                results.append(result)
            assert results[0]==results[1]
            rows.append(results[0][0])
    print('32 base/current page results and exact exception texts match')


async def probe_last_request_end_and_partial_completion():
    # Finishing the last permitted call is complete, not automatically a cap stop.
    tg,f=setup(page([message(1)]),page([]))
    value=await capture(tg,end_date=D+timedelta(days=2),max_messages=2,max_requests=2)
    assert value.coverage_complete and value.stop_reason=='finished'
    assert value.coverage['requests']==2 and len(value.messages)==1
    await cleanup()
    # A completed earlier day survives unknown evidence on the later day.
    tg,f=setup(page([message(1)]),page([types.MessageEmpty(2,peer_id=None)]))
    value=await capture(tg,end_date=D+timedelta(days=2),max_messages=2,max_requests=2)
    sample=value.sample()
    assert value.stop_reason=='finished' and not sample.coverage_complete
    assert [b['coverage_complete'] for b in sample.to_dict()['buckets']]==[True,False]
    assert f.wire.closed
    print('last-call completion and per-day unknown evidence PASS')


async def probe_wide_window_and_sampling_cost():
    tg,f=setup(page())
    start=time.monotonic()
    value=await capture(tg,start_date=datetime(1970,1,1,tzinfo=timezone.utc),
                        end_date=D,max_messages=1,max_requests=1)
    sample=value.sample()
    elapsed=time.monotonic()-start
    assert len(value.buckets)==(D-datetime(1970,1,1,tzinfo=timezone.utc)).days
    assert value.coverage['requests']==1 and not value.coverage_complete and not sample.messages
    assert len(value.to_json().encode())<16*1024*1024
    assert HistoryCapture.from_json(value.to_json()).sample().to_json()==sample.to_json()
    print('wide window: {} buckets, {:.3f}s capture+selection, {} bytes'.format(
        len(value.buckets),elapsed,len(value.to_json().encode())))


async def probe_concurrent_owners_and_cleanup_error():
    events_a,events_b=[],[]
    def broken_close(client): client._sender.close_error=OSError('cleanup detail')
    a,fa=setup(page([message(7)]),accounts=(222,),cached=111,budget=True,callback=events_a.append)
    denial=h.RPCReply(400,'CHANNEL_PRIVATE')
    b,fb=setup(page([message(9)],'slice'),denial,accounts=(333,),cached=111,budget=True,
               callback=events_b.append,prepare=broken_close)
    av,bv=await asyncio.gather(capture(a,max_messages=2,max_requests=1),
                              capture(b,account_id=333,max_messages=3),return_exceptions=True)
    assert isinstance(av,HistoryCapture) and bv is denial.error
    assert bv.partial_result.account_id==333 and bv.partial_result.sample().selected_ids==(9,)
    await h.deliveries(a); await h.deliveries(b)
    assert not events_a and len(events_b)==1 and events_b[0]['account']['user_id']==333
    assert fa.budget.status(222).used==1 and fb.budget.status(333).used==3
    assert fa.wire.closed and fb.wire.close_calls==1
    print('concurrent222/333 outcome, allowance and event ownership PASS')


async def probe_capture_reload_adversarial_types():
    tg,_=setup(page([message(9),message(8)]))
    value=await capture(tg,max_requests=1)
    refused=0
    for path in (('version',),('account_id',),('limits','max_messages'),('buckets',0,'pages'),
                 ('buckets',0,'scanned_messages'),('buckets',0,'records',0,'id'),
                 ('buckets',0,'records',0,'date'),('group','peer_id')):
        for replacement in (None,True,{},[],1.5):
            doc=value.to_dict(); target=doc
            for segment in path[:-1]: target=target[segment]
            target[path[-1]]=replacement
            doc['capture_id']=_identity(doc,'capture_id')
            try: HistoryCapture.from_json(json.dumps(doc))
            except HistorySampleError: refused+=1
            else: raise AssertionError((path,replacement))
    assert refused==40
    print('40 rehashed malformed field variants refused with HistorySampleError')


async def probe_rehashed_impossible_page_counts():
    tg,_=setup(page())
    value=await capture(tg,max_requests=100)
    doc=value.to_dict()
    doc['buckets'][0]['pages']=100
    doc['buckets'][0]['requests']=100
    doc['capture_id']=_identity(doc,'capture_id')
    accepted=HistoryCapture.from_json(json.dumps(doc))
    assert accepted.coverage['pages']==100 and accepted.coverage['scanned_messages']==0
    assert accepted.coverage_complete
    print('OBSERVED loader accepts rehashed100 accepted pages/zero slots/history_end as complete')
    print('Native collector stops on first empty page; valid native capture had1 page')


async def probe_cancel_during_metadata_no_capture():
    entered,release=asyncio.Event(),asyncio.Event()
    tg,f=g.setup(responses={'ResolveUsernameRequest':g.Reply(
        types.contacts.ResolvedPeer(types.PeerChannel(7),[g.channel()],[]),entered=entered,release=release)})
    beats=[]
    task=asyncio.create_task(capture(tg,heartbeat=beats.append))
    try:
        await asyncio.wait_for(entered.wait(),3)
        before=list(beats); await fx.turns(20); assert beats==before
        task.cancel(); exc=await fx.expect(asyncio.CancelledError,task)
        assert not getattr(exc,'partial_result',None) and f.wire.closed
        assert not g.requests(f,functions.messages.GetHistoryRequest)
        release.set(); await fx.turns(10); assert beats==before
    finally:
        release.set(); await asyncio.gather(task,return_exceptions=True)
    print('metadata-stage cancellation: no invented capture or history send; cleanup PASS')


async def main():
    assert telethon.__version__=='1.45.0'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==HEAD
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ('tgdata','examples') for p in (ROOT/folder).rglob('*.py')}
    probes=sorted((n,f) for n,f in globals().items() if n.startswith('probe_'))
    failed=0
    with tempfile.TemporaryDirectory(prefix='sampling-pr-') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient,'start',side_effect=AssertionError('login forbidden')), \
         patch.object(telethon.TelegramClient,'send_code_request',side_effect=AssertionError('code forbidden')), \
         patch.object(fx.Wire,'send',g.send):
        fx.TMP=Path(tmp)
        for name,probe in probes:
            try:
                await asyncio.wait_for(probe(),45)
                print('PASS',name,flush=True)
            except (Exception,asyncio.CancelledError):
                failed+=1; print('FAIL',name,flush=True); traceback.print_exc()
            finally: await cleanup()
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest for p,digest in manifest.items())
    print('{} fresh probe groups; {} harness failures; one explicit loader observation'.format(len(probes),failed))
    return bool(failed)


if __name__=='__main__':
    sys.exit(asyncio.run(main()))
