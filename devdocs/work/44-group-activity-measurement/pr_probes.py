"""Fresh PR48 probes. Actual public path/SDK/SQLite; modeled server packets only."""
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path('/private/tmp/tgdata-44-activity-pr')
sys.path.insert(0, str(ROOT))
import telethon
from telethon.tl import functions, types
from tgdata import GroupReferenceError, GroupResponseError, ReadBudgetExceeded
from tgdata.smoke_tests import test_34_group_access as g

fx, h = g.fx, g.h
D = datetime(2025, 4, 1, tzinfo=timezone.utc)
CASES = []


def row(id, date=D, **kwargs):
    return types.Message(id, types.PeerChannel(7), date=date, message='', **kwargs)


def packet(rows, full=False):
    return (types.messages.Messages(list(rows), [], [], []) if full else
            types.messages.ChannelMessages(1, 99999, list(rows), [], [], [], inexact=True))


async def call(tg, cap=300, start=None, end=None, account=222, target='synthetic_room', beat=None):
    return await tg.measure_group_activity(target, account_id=account,
        start_date=start or D-timedelta(days=1), end_date=end or D+timedelta(days=2),
        max_messages=cap, heartbeat=beat)


def passed(name, **evidence):
    CASES.append(dict(name=name, **evidence))
    print('PASS', name, json.dumps(evidence, sort_keys=True), flush=True)


async def source_offset_oracles():
    # This source-side model does not call the product collector/filter/helpers.
    # It obeys the documented exclusive date/ID offsets and permits short pages.
    corpus = [row(3*i+2, D+timedelta(seconds=i//4), from_id=types.PeerUser(i%3+1))
              for i in range(399, -1, -1)]
    for fractional in (0, 500000):
        for cap in (1, 99, 164, 200):
            start, end = D+timedelta(seconds=20), D+timedelta(seconds=60,microseconds=fractional)
            expected = [m.id for m in corpus if start <= m.date < end]
            sizes, seen, requests = [7,53,2,89], [], []
            def response(wire, req):
                candidates = [m for m in corpus if
                    (not req.offset_id or m.id < req.offset_id) and
                    (req.offset_date is None or m.date < req.offset_date)]
                part = candidates[:min(req.limit,sizes[len(requests)%len(sizes)])]
                seen.extend(part); requests.append(req)
                return g.Reply(packet(part))
            tg, f = g.setup(budget=True,cached=111,responses={'GetHistoryRequest':response})
            f.budget.configure(222,1000)
            value = await call(tg,cap,start,end)
            actual = [m.id for m in value.messages]
            assert actual == [m.id for m in seen if start <= m.date < end]
            assert len(set(actual)) == len(actual) and len(seen) <= cap
            assert f.budget.status(222).used == len(seen) and f.budget.status(111).used == 0
            if value.coverage_complete:
                assert actual == expected and value.stop_reason == 'window_start'
            else:
                assert value.stop_reason == 'message_limit' and len(seen) == cap
                assert value.statistics['messages_per_24h'] is None
            if cap==200:
                assert value.coverage_complete
            if cap in (1,99):
                assert not value.coverage_complete
            assert all(r.min_id==r.max_id==r.add_offset==r.hash==0 for r in requests)
            assert f.wire.closed
            passed('offset_oracle_{}_{}'.format(fractional,cap),
                messages=len(actual), expected_full=len(expected), scanned=len(seen),
                requests=len(requests), complete=value.coverage_complete)


async def independent_aggregate_oracle():
    rows = [row(99,D+timedelta(hours=24),from_id=types.PeerUser(5),
                views=0,forwards=0,grouped_id=-2**63,
                reactions=types.MessageReactions([types.ReactionCount(types.ReactionPaid(),2**31-1),
                    types.ReactionCount(types.ReactionEmoji('👍'),3)],min=True)),
            row(81,D+timedelta(hours=12),from_id=types.PeerChannel(5),views=4,forwards=2),
            row(60,D,from_id=types.PeerUser(5),views=10,forwards=8),
            row(25,D-timedelta(hours=6)),
            types.MessageService(1,types.PeerChannel(7),date=D-timedelta(hours=8),
                                 action=types.MessageActionEmpty())]
    tg, f = g.setup(responses={'GetHistoryRequest':g.Reply(packet(rows,full=True))})
    value = await call(tg,10,D-timedelta(hours=12),D+timedelta(hours=36))
    s=value.statistics
    assert s['message_count']==4 and s['service_message_count']==1
    assert s['known_user_count']==s['channel_sender_count']==s['unknown_author_messages']==1
    assert s['counters']['views']==dict(known_count=3,missing_count=1,sum=14,mean=14/3,median=4,min=0,max=10)
    assert s['counters']['reactions']['sum']==2**31+2
    assert s['counters']['reactions']['missing_count']==3
    assert [x['message_count'] for x in s['daily']]==[1,2,1]
    assert [x['window_seconds'] for x in s['daily']]==[43200,86400,43200]
    assert s['messages_per_24h']==2 and s['window_seconds']==172800
    assert value.to_dict()['messages'][0]['grouped_id']==str(-2**63)
    passed('aggregate_oracle', ordinary=4, services=1, views_sum=14, reactions_sum=2**31+2)


async def invite_and_preview_boundaries():
    token='FreshReviewInvite'
    for kind in ('preview','already','peek'):
        invite = (types.ChatInvite('Preview',types.PhotoEmpty(0),2,0,channel=True,megagroup=True)
                  if kind=='preview' else types.ChatInviteAlready(g.channel()) if kind=='already'
                  else types.ChatInvitePeek(g.channel(),D+timedelta(days=1)))
        tg,f=g.setup(responses={'CheckChatInviteRequest':g.Reply(invite),
                               'GetHistoryRequest':g.Reply(packet([row(9)],full=True))})
        if kind=='preview':
            await fx.expect(GroupReferenceError,call(tg,10,target='https://t.me/+'+token))
            assert not g.requests(f,functions.messages.GetHistoryRequest)
        else:
            v=await call(tg,10,target='https://t.me/+'+token)
            assert v.target=='invite:'+hashlib.sha256(token.encode()).hexdigest()
            assert token not in json.dumps(v.to_dict()) and len(v.messages)==1
        assert f.wire.closed
        passed('invite_'+kind, history_requests=len(g.requests(f,functions.messages.GetHistoryRequest)))


async def malformed_unknown_peer_after_prefix():
    count=0
    def response(wire,req):
        nonlocal count
        count+=1
        return g.Reply(packet([row(9)] if count==1 else [
            types.MessageEmpty(8,peer_id=types.PeerChannel(80)),row(7)]))
    tg,f=g.setup(budget=True,responses={'GetHistoryRequest':response})
    error=await fx.expect(GroupResponseError,call(tg,4))
    assert [m.id for m in error.partial_result.messages]==[9]
    assert error.partial_result.scanned_messages==1 and error.partial_result.unavailable_messages==0
    assert error.partial_result.pages==1 and not error.partial_result.coverage_complete
    assert f.budget.status(222).used==3 and tg.get_account_health(222)['events']==0
    passed('foreign_unknown_page_atomic', accepted=1,charged=3)


async def budget_refusal_after_validated_prefix():
    def response(wire,req):
        wire.fixture.budget.configure(222,2)
        return g.Reply(packet([row(9),row(8)]))
    tg,f=g.setup(budget=True,responses={'GetHistoryRequest':response})
    error=await fx.expect(ReadBudgetExceeded,call(tg,4))
    assert [m.id for m in error.partial_result.messages]==[9,8]
    assert error.partial_result.stop_reason=='error' and error.partial_result.pages==1
    assert len(g.requests(f,functions.messages.GetHistoryRequest))==1
    assert f.budget.status(222).used==2 and tg.get_account_health(222)['events']==0
    passed('budget_late_refusal', accepted=2,source_requests=1)


async def settlement_failure_preserves_prior_evidence():
    n=0
    def response(wire,req):
        nonlocal n
        n+=1
        return g.Reply(packet([row(10-n)]))
    tg,f=g.setup(budget=True,responses={'GetHistoryRequest':response})
    original=f.budget._settle
    fault=OSError('synthetic settlement failure')
    calls=0
    def settle(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==2:
            raise fault
        return original(*args,**kwargs)
    with patch.object(f.budget,'_settle',side_effect=settle):
        error=await fx.expect(OSError,call(tg,3))
    assert error is fault and [m.id for m in error.partial_result.messages]==[9]
    assert f.budget.status(222).reserved==2 and tg.get_account_health(222)['events']==0
    assert f.wire.closed
    passed('settlement_fault', accepted=1,reserved=2)


async def parallel_owners_and_callbacks():
    def response(wire,req):
        return g.Reply(packet([row(wire.account,from_id=types.PeerUser(wire.account))],full=True))
    tg,f=g.setup(accounts=(222,333),cached=111,budget=True,responses={'GetHistoryRequest':response})
    beats={222:[],333:[]}
    a,b=await asyncio.gather(call(tg,3,account=222,beat=beats[222].append),
                             call(tg,3,account=333,beat=beats[333].append))
    assert (a.account_id,a.messages[0].sender_id)==(222,222)
    assert (b.account_id,b.messages[0].sender_id)==(333,333)
    assert f.budget.status(222).used==f.budget.status(333).used==1
    assert f.budget.status(111).used==0
    assert all(c._sender.closed for c in f.clients)
    assert all(v.count('activity page done')==1 for v in beats.values())
    assert all(v.count('request')==v.count('request done') for v in beats.values())
    passed('parallel_owners', owners=[a.account_id,b.account_id],charges=[1,1])


async def cancel_from_final_page_progress():
    tg,f=g.setup(budget=True,responses={'GetHistoryRequest':g.Reply(packet([row(9)],full=True))})
    def beat(phase):
        if phase=='activity page done':
            asyncio.current_task().cancel()
    task=asyncio.create_task(call(tg,3,beat=beat))
    await fx.expect(asyncio.CancelledError,task)
    assert f.wire.closed and f.budget.status(222).used==1
    assert tg.get_account_health(222)['events']==0
    passed('cancel_at_final_progress', result_delivered=False,charged=1,disconnected=True)


async def unavailable_then_boundary():
    packets=[packet([types.MessageEmpty(91,peer_id=None)]),
             packet([row(90),row(1,D-timedelta(days=2))])]
    tg,f=g.setup(responses={'GetHistoryRequest':lambda wire,req:g.Reply(packets.pop(0))})
    v=await call(tg,3)
    assert v.stop_reason=='window_start' and not v.coverage_complete
    assert v.unavailable_messages==1 and v.scanned_messages==3 and len(v.messages)==1
    assert v.statistics['messages_per_24h'] is None
    passed('unknown_then_boundary',complete=False,observed=1,unknown=1)


async def main():
    assert telethon.__version__=='1.45.0'
    groups=(source_offset_oracles,independent_aggregate_oracle,invite_and_preview_boundaries,
            malformed_unknown_peer_after_prefix,budget_refusal_after_validated_prefix,
            settlement_failure_preserves_prior_evidence,parallel_owners_and_callbacks,
            cancel_from_final_page_progress,unavailable_then_boundary)
    with tempfile.TemporaryDirectory(prefix='pr48-critic-') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient,'start',side_effect=AssertionError('login forbidden')), \
         patch.object(fx.Wire,'send',g.send):
        fx.TMP=Path(tmp)
        for test in groups:
            try:
                await asyncio.wait_for(test(),20)
            finally:
                for client in fx.CLIENTS:
                    client._sender.close_error=None
                    if client._sender.close_release is not None:
                        client._sender.close_release.set()
                    await client.disconnect()
                for tg in h.FACADES:
                    await tg.close()
                await asyncio.gather(*h.RPC_TASKS,return_exceptions=True)
                fx.CLIENTS.clear();h.FACADES.clear();h.RPC_TASKS.clear();g.TRACE.clear()
    report=dict(result='PASS',groups=len(groups),cases=len(CASES),histories=CASES,
                source_head='b479e5f3cf0304865b055ebd271f187cf60848b3',
                runtime=sys.version.split()[0],telethon=telethon.__version__,live=False)
    Path(__file__).with_name('pr-probe-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('{} groups / {} fresh histories PASS; no live Telegram'.format(len(groups),len(CASES)))


if __name__=='__main__':
    asyncio.run(main())
