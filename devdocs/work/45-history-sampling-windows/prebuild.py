"""Combined #45 feasibility probe: real SDK/admission/cleanup, synthetic packets."""
import ast
import asyncio
from datetime import datetime, timedelta, timezone
import inspect
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import telethon
from telethon import errors
from telethon.tl import functions, types
from tgdata import ReadBudgetExceeded
from tgdata import group_activity as activity
from tgdata.account_operation import AccountIdentityError
from tgdata.batch_engine import _record
from tgdata.batch_heartbeat import heartbeat_scope
from tgdata.group_operations import _parse_target, _resolve
from tgdata.history_window import _HistoryWindow
from tgdata.message_batch import _canonical, _validate_record
from tgdata.smoke_tests import test_34_group_access as g

fx, h = g.fx, g.h
D = datetime(2025, 1, 1, tzinfo=timezone.utc)

# Prototype the exact proposed narrow extraction from current activity source.
# It keeps real validation, replacing only the internal projection call.
tree = ast.parse(inspect.getsource(activity._page))
tree.body[0].name = 'shared_page'
tree.body[0].args.args.append(ast.arg(arg='project'))
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_message':
        node.func.id = 'project'
namespace = dict(vars(activity))
exec(compile(ast.fix_missing_locations(tree), '<proposed shared page>', 'exec'), namespace)
shared_page = namespace['shared_page']


def ranks(n, k):
    return [] if not k else [(n-1)//2] if k == 1 else [j*(n-1)//(k-1) for j in range(k)]


def quotas(capacities, size):
    target = min(size, sum(capacities))
    if not target:
        return [0]*len(capacities)
    if target == sum(capacities):
        return list(capacities)
    lo, hi = 0, max(capacities)
    while lo < hi:
        mid = (lo+hi+1)//2
        if sum(min(c,mid) for c in capacities) <= target:
            lo = mid
        else:
            hi = mid-1
    result = [min(c,lo) for c in capacities]
    available = [i for i,c in enumerate(capacities) if c > result[i]]
    for index in ranks(len(available), target-sum(result)):
        result[available[index]] += 1
    return result


def row(id, date=D, **kwargs):
    return types.Message(id, types.PeerChannel(7), date=date, message='text '+str(id), **kwargs)


def page(rows):
    return types.messages.ChannelMessages(1, 99999, list(rows), [], [], [])


def source(corpus):
    def response(wire, req):
        values = [m for m in corpus if (not req.offset_id or m.id < req.offset_id)
                  and (req.offset_date is None or m.date < req.offset_date)]
        return g.Reply(page(values[:req.limit]))
    return response


async def collect(tg, start, end, cap=3000, calls=100, account=222, heartbeat=None):
    buckets, current = [], start.replace(hour=0,minute=0,second=0,microsecond=0)
    while current < end:
        following = current+timedelta(days=1)
        buckets.append(dict(window=_HistoryWindow(max(start,current),min(end,following)),
                            requests=0,pages=0,scanned=0,unknown=0,records=[],
                            last_id=None,last_date=None,end_reason=None))
        current = following
    scanned = requests = 0
    seen = set()
    def snapshot(reason):
        result = dict(account_id=account,stop_reason=reason,scanned=scanned,requests=requests,
            buckets=[dict(window=b['window'].to_dict(),requests=b['requests'],pages=b['pages'],
                scanned=b['scanned'],unknown=b['unknown'],end_reason=b['end_reason'],
                records=sorted(b['records'],key=lambda r:int(r['id']))) for b in buckets])
        return json.loads(_canonical(result))
    with heartbeat_scope(heartbeat) as beat:
        async with tg._account_health_operation(account,'sampling prebuild','synthetic_room') as (op,_):
            lookup, peer = await _resolve(op,_parse_target('synthetic_room'))
            def project(message,date,observed):
                result = _record(message,op.client)
                _validate_record(result,'references')
                return result
            try:
                while True:
                    active = [b for b in buckets if b['end_reason'] is None]
                    if not active:
                        return snapshot('finished')
                    if scanned >= cap:
                        return snapshot('message_limit')
                    if requests >= calls:
                        return snapshot('request_limit')
                    chosen = [active[i] for i in ranks(len(active),min(len(active),cap-scanned,calls-requests))]
                    for position,b in enumerate(chosen):
                        remaining_visits = len(chosen)-position
                        limit = min(100,max(1,(cap-scanned)//remaining_visits))
                        if b['requests'] == 0 and calls-requests > remaining_visits:
                            limit = 1
                        upper = b['window'].end_date.replace(microsecond=0)
                        if b['window'].end_date.microsecond:
                            upper += timedelta(seconds=1)
                        requests += 1; b['requests'] += 1
                        response = await op.client(functions.messages.GetHistoryRequest(
                            peer,b['last_id'] or 0,upper if b['last_id'] is None else None,
                            0,limit,0,0,0))
                        accepted,dates,unknown,count,next_id,next_date,reason = shared_page(
                            response,lookup.group.peer_id,limit,b['last_id'],b['last_date'],
                            b['window'],D,project)
                        assert not seen.intersection(r['id'] for r in accepted)
                        seen.update(r['id'] for r in accepted)
                        b['records'].extend(accepted); b['pages'] += 1
                        b['scanned'] += count; b['unknown'] += unknown
                        b['last_id'],b['last_date'],b['end_reason']=next_id,next_date,reason
                        scanned += count
                        if beat is not None:
                            beat('history page done')
            except (Exception,asyncio.CancelledError) as error:
                error.partial_capture = snapshot('cancelled' if isinstance(error,asyncio.CancelledError) else 'error')
                raise


async def shared_parity_and_real_projection():
    photo=types.Photo(91,22,b'ref',D,[types.PhotoSize('x',1,1,5)],2)
    document=types.Document(92,23,b'ref',D,'application/pdf',6,2,[types.DocumentAttributeFilename('file.pdf')])
    rows=[row(9,views=0,forwards=0,grouped_id=2**62+17),
          row(8,media=types.MessageMediaPhoto(photo=photo)),
          row(7,media=types.MessageMediaDocument(document=document)),
          types.MessageService(6,types.PeerChannel(7),date=D,action=types.MessageActionEmpty()),
          types.MessageEmpty(5,peer_id=None)]
    tg,f=g.setup(responses={'GetHistoryRequest':g.Reply(page(rows))})
    async with tg._account_health_operation(222,'projection prebuild',7) as (op,_):
        reply=await op.client(functions.messages.GetHistoryRequest(types.InputPeerChannel(7,0),0,None,0,5,0,0,0))
        args=(reply,-1000000000007,5,None,None,_HistoryWindow(D-timedelta(days=1),D+timedelta(days=1)),D)
        assert activity._page(*args)==shared_page(*args,activity._message)
        values=shared_page(*args,lambda m,d,t:_record(m,op.client))[0]
        for value in values:_validate_record(value,'references')
        assert values[0]['grouped_id']==str(2**62+17)
        assert values[1]['media']['kind']=='photo' and values[2]['media']['file_name']=='file.pdf'
        assert values[3]['kind']=='service'
        assert json.loads(_canonical(values))==values
        # Independent projections: sampling does not depend on engagement counts.
        reply.messages[0].views=-1
        fx.refuses(activity.GroupResponseError,lambda:activity._page(*args))
        assert shared_page(*args,lambda m,d,t:_record(m,op.client))[0][0]['id']=='9'
    assert f.wire.closed


async def sparse_busy_days_and_replay():
    corpus=[row(i,D+timedelta(days=59,seconds=i-1000)) for i in range(1598,999,-1)]
    corpus += [row(i,D-timedelta(days=2)+timedelta(seconds=i)) for i in range(200,0,-1)]
    tg,f=g.setup(budget=True,cached=111,proxy=True,responses={'GetHistoryRequest':source(corpus)})
    f.budget.configure(222,10000)
    beats=[]
    value=await collect(tg,D,D+timedelta(days=60),heartbeat=beats.append)
    records=[r for b in value['buckets'] for r in b['records']]
    assert len(records)==599 and value['stop_reason']=='finished'
    assert value['scanned']<1000 and value['requests']<=100
    assert f.budget.status(222).used==value['scanned'] and f.budget.status(111).used==0
    loaded=json.loads(_canonical(value))
    candidates=[b['records'] for b in loaded['buckets']]
    allocation=quotas([len(c) for c in candidates],300)
    selected=[c[i]['id'] for c,k in zip(candidates,allocation) for i in ranks(len(c),k)]
    assert len(selected)==len(set(selected))==300 and selected[0]=='1000' and selected[-1]=='1598'
    assert beats.count('history page done')==value['requests']
    assert f.wire.policy_at_connect['flood']==f.wire.policy_at_connect['requests']==0
    assert f.wire.closed
    print('sparse source:',value['requests'],'calls',value['scanned'],'slots',len(records),'captured',len(selected),'selected',flush=True)


async def request_and_slot_bounds():
    corpus=[row(100,D+timedelta(days=59)),row(1,D-timedelta(days=1))]
    for cap,calls,expected_limit in ((3000,1,100),(2,100,1)):
        tg,f=g.setup(responses={'GetHistoryRequest':source(corpus)})
        value=await collect(tg,D,D+timedelta(days=60),cap,calls)
        assert value['scanned']<=cap and value['requests']<=calls
        assert g.requests(f,functions.messages.GetHistoryRequest)[0].limit==expected_limit
        assert sum(b['requests']==0 for b in value['buckets'])>0
    tg,f=g.setup(responses={'GetHistoryRequest':g.Reply(page([]))})
    value=await collect(tg,D,D+timedelta(days=60),3000,3)
    assert value['requests']==3 and value['scanned']==0 and value['stop_reason']=='request_limit'


async def date_ties_and_unknowns():
    rows=[row(30,D+timedelta(seconds=2)),row(29,D+timedelta(seconds=1)),
          row(28,D+timedelta(seconds=1)),row(1,D)]
    tg,f=g.setup(responses={'GetHistoryRequest':source(rows)})
    value=await collect(tg,D+timedelta(microseconds=1),D+timedelta(seconds=2,microseconds=1),20,10)
    assert [r['id'] for r in value['buckets'][0]['records']]==['28','29','30']
    assert value['buckets'][0]['end_reason']=='window_start'
    replies=[page([types.MessageEmpty(9,peer_id=None)]),page([row(8,D-timedelta(days=1))])]
    tg,f=g.setup(responses={'GetHistoryRequest':lambda wire,req:g.Reply(replies.pop(0))})
    value=await collect(tg,D,D+timedelta(days=1),10,10)
    assert value['buckets'][0]['unknown']==1 and value['buckets'][0]['end_reason']=='window_start'


async def owner_and_budget_refuse():
    tg,f=g.setup(budget=True,cached=111)
    await fx.expect(AccountIdentityError,collect(tg,D,D+timedelta(days=1),10,10,account=111))
    assert not g.requests(f,functions.messages.GetHistoryRequest)
    f.budget.configure(222,0)
    error=await fx.expect(ReadBudgetExceeded,collect(tg,D,D+timedelta(days=1),10,10))
    assert error.partial_capture['scanned']==0 and not g.requests(f,functions.messages.GetHistoryRequest)


async def later_failures_keep_capture():
    for kind in ('rpc','settle','local'):
        denial=h.RPCReply(400,'CHANNEL_PRIVATE')
        failure=OSError('synthetic local fault')
        n=0
        def response(wire,req):
            nonlocal n
            n+=1
            if n==2 and kind=='rpc':return denial
            if n==2 and kind=='local':raise failure
            return g.Reply(page([row(10,D)]))
        tg,f=g.setup(budget=True,responses={'GetHistoryRequest':response})
        original=f.budget._settle
        def settle(*args):
            if n==2 and kind=='settle':raise failure
            return original(*args)
        with patch.object(f.budget,'_settle',side_effect=settle):
            error=await fx.expect(errors.ChannelPrivateError if kind=='rpc' else OSError,
                collect(tg,D,D+timedelta(days=2),10,10))
        assert error is (denial.error if kind=='rpc' else failure)
        assert len(error.partial_capture['buckets'][0]['records'])==1
        assert error.partial_capture['buckets'][1]['records']==[] and f.wire.closed
        assert tg.get_account_health(222)['events']==(1 if kind=='rpc' else 0)


async def cancellation_and_cleanup():
    entered,release=asyncio.Event(),asyncio.Event()
    n=0
    def response(wire,req):
        nonlocal n
        n+=1
        return g.Reply(page([row(10,D)])) if n==1 else g.Reply(page([]),entered=entered,release=release)
    tg,f=g.setup(budget=True,responses={'GetHistoryRequest':response})
    beats=[]; task=asyncio.create_task(collect(tg,D,D+timedelta(days=2),10,10,heartbeat=beats.append))
    try:
        await asyncio.wait_for(entered.wait(),3)
        prior=list(beats);await fx.turns(20);assert beats==prior
        task.cancel();error=await fx.expect(asyncio.CancelledError,task)
        assert len(error.partial_capture['buckets'][0]['records'])==1 and f.wire.closed
        assert f.budget.status(222).reserved==1
    finally:
        release.set();await asyncio.gather(task,return_exceptions=True)
    closing,closed=asyncio.Event(),asyncio.Event()
    def prepare(client):client._sender.close_entered,client._sender.close_release=closing,closed
    tg,f=g.setup(prepare=prepare,responses={'GetHistoryRequest':g.Reply(page([]))})
    task=asyncio.create_task(collect(tg,D,D+timedelta(days=1),10,10))
    try:
        await asyncio.wait_for(closing.wait(),3)
        task.cancel();await fx.turns();task.cancel();await fx.turns()
        assert not task.done() and not f.wire.closed
        closed.set();await fx.expect(asyncio.CancelledError,task);assert f.wire.closed
    finally:
        closed.set();await asyncio.gather(task,return_exceptions=True)


async def quota_totality():
    import itertools
    checked=0
    for capacities in itertools.product(range(5),repeat=4):
        for size in range(sum(capacities)+3):
            q=quotas(capacities,size)
            assert sum(q)==min(size,sum(capacities))
            assert all(0<=a<=b for a,b in zip(q,capacities))
            assert q==quotas(capacities,size)
            checked+=1
    assert quotas([1,100,2],10)==[1,7,2]
    print('quota combinations:',checked,flush=True)


async def main():
    assert telethon.__version__=='1.45.0'
    groups=(shared_parity_and_real_projection,sparse_busy_days_and_replay,request_and_slot_bounds,
            date_ties_and_unknowns,owner_and_budget_refuse,later_failures_keep_capture,
            cancellation_and_cleanup,quota_totality)
    with tempfile.TemporaryDirectory(prefix='sampling-prebuild-') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient,'start',side_effect=AssertionError('login forbidden')), \
         patch.object(fx.Wire,'send',g.send):
        fx.TMP=Path(tmp)
        for test in groups:
            try:
                await asyncio.wait_for(test(),20)
                print('PASS',test.__name__,flush=True)
            finally:
                for client in fx.CLIENTS:
                    client._sender.close_error=None
                    if client._sender.close_release is not None:client._sender.close_release.set()
                    await client.disconnect()
                for tg in h.FACADES:await tg.close()
                await asyncio.gather(*h.RPC_TASKS,return_exceptions=True)
                fx.CLIENTS.clear();h.FACADES.clear();h.RPC_TASKS.clear();g.TRACE.clear()
    print('8 combined prebuild groups PASS; synthetic source, no live Telegram',flush=True)


if __name__=='__main__':asyncio.run(main())
