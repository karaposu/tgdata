"""History sampling with real SDK/TL/SQLite components and synthetic source packets."""
import asyncio
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import itertools
import json
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import telethon
from telethon import errors
from telethon.tl import functions, types
from tgdata import (TgData, HistoryCapture, HistorySample, HistorySampleError,
                    GroupResponseError, GroupReferenceError, BatchFormatError,
                    ReadBudgetExceeded, ReadBudgetError, AuthRequiredError)
from tgdata.account_operation import AccountIdentityError
from tgdata.history_sample import _quotas, _identity
from tgdata.smoke_tests import test_34_group_access as g
from tgdata.smoke_tests.test_46_group_activity import page, service, setup

fx, h, DATE = g.fx, g.h, g.DATE


def message(id=9, date=DATE, text='Retained text', peer=None, **kwargs):
    return types.Message(id, peer or types.PeerChannel(7), date=date, message=text, **kwargs)


class Source:
    """Small source-side GetHistory offset model; never substitutes the SDK client."""
    def __init__(self, rows):
        self.rows = sorted(rows, key=lambda r: r.id, reverse=True)
        self.calls = []

    def __call__(self, wire, request):
        assert request.add_offset == request.min_id == request.max_id == request.hash == 0
        self.calls.append(request)
        rows = [r for r in self.rows if
                (not request.offset_id or r.id < request.offset_id) and
                (not request.offset_date or r.date < request.offset_date)]
        # A slice deliberately does not promise end-of-history, even when short.
        return g.Reply(page(rows[:request.limit], 'slice'))


def source_setup(rows, **kwargs):
    source = Source(rows)
    tg, f = g.setup(responses={'GetHistoryRequest': source}, **kwargs)
    return tg, f, source


async def capture(tg, **kwargs):
    options = dict(account_id=222, start_date=DATE, end_date=DATE+timedelta(days=1),
                   max_messages=1000, max_requests=100)
    options.update(kwargs)
    return await tg.capture_group_history('synthetic_room', **options)


async def small_capture(rows=None):
    tg, f = setup(page(rows if rows is not None else [message(9), message(8), service(7)]))
    return await capture(tg, max_requests=1), tg, f


async def test_599_to_300_spans_retained_input_and_replays():
    tg, f, source = source_setup([message(i, DATE+timedelta(seconds=i)) for i in range(1,600)])
    value = await capture(tg)
    assert value.coverage_complete and len(value.messages) == 599
    sample = value.sample()
    assert isinstance(value, HistoryCapture) and isinstance(sample, HistorySample)
    assert sample.selected_ids == tuple(1+j*598//299 for j in range(300))
    assert sample.selected_ids[0] == 1 and sample.selected_ids[-1] == 599
    calls = len(source.calls)
    assert HistoryCapture.from_json(value.to_json()).sample().to_json() == sample.to_json()
    assert HistoryCapture.from_json(value.to_json().encode()).to_json() == value.to_json()
    assert len(source.calls) == calls and f.wire.closed
    assert sample.coverage_complete and sample.to_dict()['buckets'][0]['omitted_messages'] == 299
    assert len(sample.messages) == 300 and 'next_after_id' not in sample.to_dict()


async def test_sparse_60_days_preserve_capacity_for_busy_day():
    busy = DATE+timedelta(days=29)
    rows = [message(1, DATE-timedelta(days=1))]
    rows += [message(i+1, busy+timedelta(seconds=i)) for i in range(1,600)]
    tg, f, source = source_setup(rows, budget=True)
    f.budget.configure(222,10000)
    value = await capture(tg,end_date=DATE+timedelta(days=60),max_messages=3000)
    assert value.coverage_complete and len(value.messages) == 599
    assert value.coverage['scanned_messages'] < 1000 and len(source.calls) <= 100
    assert value.coverage['requests'] == len(source.calls)
    assert f.budget.status(222).used == value.coverage['scanned_messages']
    assert len(value.sample().messages) == 300
    assert value.sample().selected_ids[0] == 2 and value.sample().selected_ids[-1] == 600
    assert len(value.buckets) == 60 and all(b['requests'] >= 1 for b in value.buckets)


async def test_busy_day_does_not_starve_quiet_days():
    rows = [message(1,DATE),message(2,DATE+timedelta(days=1))]
    rows += [message(i,DATE+timedelta(days=2,seconds=i)) for i in range(3,103)]
    rows += [message(103,DATE+timedelta(days=3)),message(104,DATE+timedelta(days=4))]
    tg, _, source = source_setup(rows)
    value = await capture(tg,end_date=DATE+timedelta(days=5),max_messages=30,max_requests=20)
    sample = value.sample(size=8)
    assert {1,2,103,104} <= set(sample.selected_ids)
    assert sum(b['selected_messages'] for b in sample.to_dict()['buckets']) == 8
    assert value.stop_reason == 'message_limit' and not value.coverage_complete
    assert [r.limit for r in source.calls[:5]] == [1]*5


async def test_no_spare_requests_use_available_page_capacity():
    tg, _, source = source_setup([message(i) for i in range(1,21)])
    value = await capture(tg,max_messages=20,max_requests=1)
    assert len(value.messages) == 20 and source.calls[0].limit == 20
    assert value.stop_reason == 'message_limit' and not value.coverage_complete
    tg, _, source = source_setup([message(i) for i in range(1,21)])
    value = await capture(tg,max_messages=30,max_requests=1)
    assert len(value.messages) == 20 and value.stop_reason == 'request_limit'
    assert len(source.calls) == 1


async def test_tiny_caps_distribute_visits_and_keep_unvisited_buckets():
    rows = [message(i+1,DATE+timedelta(days=i)) for i in range(7)]
    for slots, calls in ((2,10),(10,2),(1,1)):
        tg, _, source = source_setup(rows)
        value = await capture(tg,end_date=DATE+timedelta(days=7),max_messages=slots,max_requests=calls)
        visited = [i for i,b in enumerate(value.buckets) if b['requests']]
        assert visited == ([3] if slots == 1 else [0,6])
        assert len(value.buckets) == 7 and not value.coverage_complete
        assert len(source.calls) <= calls and value.coverage['scanned_messages'] <= slots
        assert all(b['end_reason'] is None and not b['records'] for b in value.buckets if not b['requests'])


async def test_empty_days_have_finite_requests_and_complete_evidence():
    tg, _, source = source_setup([])
    value = await capture(tg,end_date=DATE+timedelta(days=5))
    assert len(source.calls) == 5 and value.coverage['scanned_messages'] == 0
    assert value.coverage_complete and value.stop_reason == 'finished'
    assert value.sample().selected_ids == ()
    tg, _, source = source_setup([])
    value = await capture(tg,end_date=DATE+timedelta(days=5),max_requests=2)
    assert value.stop_reason == 'request_limit' and not value.coverage_complete
    assert len(source.calls) == 2


async def test_fractional_bounds_timezone_and_equal_timestamp_pagination():
    rows = [message(5,DATE+timedelta(seconds=3)),message(4,DATE+timedelta(seconds=2)),
            message(3,DATE+timedelta(seconds=2)),message(2,DATE+timedelta(seconds=1)),message(1,DATE)]
    tg, _, source = source_setup(rows)
    zone = timezone(timedelta(hours=3))
    value = await capture(tg,start_date=(DATE+timedelta(microseconds=1)).astimezone(zone),
        end_date=(DATE+timedelta(seconds=2,microseconds=1)).astimezone(zone))
    assert value.sample(size=10).selected_ids == (2,3,4)
    assert source.calls[0].offset_date == DATE+timedelta(seconds=3)
    assert source.calls[1].offset_id == 4 and source.calls[1].offset_date is None
    assert value.buckets[0]['end_reason'] == 'window_start' and value.coverage_complete
    tg, _, _ = source_setup(rows)
    exact = await capture(tg,start_date=DATE,end_date=DATE+timedelta(seconds=2))
    assert exact.sample(size=10).selected_ids == (1,2)


async def test_midnight_intersections_order_and_no_duplicate_boundary():
    rows = [message(1,DATE-timedelta(hours=1)),message(2,DATE),
            message(3,DATE+timedelta(days=1)),message(4,DATE+timedelta(days=1,hours=12))]
    tg, _, _ = source_setup(rows)
    value = await capture(tg,start_date=DATE-timedelta(hours=12),end_date=DATE+timedelta(days=1,hours=12))
    assert value.sample(size=10).selected_ids == (1,2,3)
    assert [len(b['records']) for b in value.buckets] == [1,1,1]
    assert value.coverage_complete


async def test_unknown_slots_are_bounded_but_never_complete():
    tg, _ = setup(page([types.MessageEmpty(9,peer_id=None)],'slice'),
                  page([message(8,DATE-timedelta(days=1))],'slice'))
    value = await capture(tg)
    assert value.stop_reason == 'finished' and not value.coverage_complete
    assert value.coverage['unavailable_messages'] == 1 and value.coverage['scanned_messages'] == 2
    assert not value.messages and not value.sample().to_dict()['buckets'][0]['coverage_complete']


async def test_raw_services_album_omissions_and_media_references():
    album = 2**62+17
    photo = types.Photo(91,22,b'ref',DATE,[types.PhotoSize('x',1,1,5)],2)
    document = types.Document(92,23,b'ref',DATE,'application/pdf',6,2,[types.DocumentAttributeFilename('file.pdf')])
    rows = [message(9,grouped_id=album,media=types.MessageMediaPhoto(photo=photo)),
            message(8,grouped_id=album,media=types.MessageMediaDocument(document=document)),service(7)]
    value, _, _ = await small_capture(rows)
    sample = value.sample(size=1)
    assert sample.selected_ids == (8,) and sample.to_dict()['sampling_unit'] == 'raw_message'
    assert sample.to_dict()['albums'] == [dict(grouped_id=str(album),membership='unconfirmed',
        captured_member_ids=['8','9'],selected_member_ids=['8'],omitted_member_ids=['9'])]
    assert value.sample(size=10).selected_ids == (8,9)
    assert sample.to_dict()['buckets'][0]['service_messages'] == 1
    assert all(r['media']['blob'] is None for r in value.messages if r['media'])
    assert value.messages[-1]['media']['size'] == 5 and value.messages[-2]['media']['size'] == 6
    fx.refuses(HistorySampleError,lambda:value.sample(eligible_ids=[7]))
    assert not hasattr(sample,'ack') and not hasattr(sample,'next_after_id')


async def test_full_text_and_detached_immutable_exports():
    import tgdata
    content = 'Привет 🏡\n'*10000
    value, _, _ = await small_capture([message(text=content)])
    sample = value.sample()
    assert value.messages[0]['text'] == sample.messages[0]['text'] == content
    assert {'HistoryCapture','HistorySample','HistorySampleError'} <= set(tgdata.__all__)
    assert tgdata.__version__ == '0.1.1'
    for obj in (value,sample):
        fx.refuses(FrozenInstanceError,lambda:setattr(obj,'_encoded','changed'))
        obj.messages[0]['text'] = 'changed'
        obj.to_dict()['group']['title'] = 'changed'
        assert obj.messages[0]['text'] == content
        assert content not in repr(obj)
    value.buckets[0]['records'].clear()
    assert len(value.messages) == 1
    assert len(value.capture_id) == len(sample.sample_id) == 64


async def test_eligibility_normalizes_and_is_pure_after_cleanup():
    value, _, f = await small_capture([message(9),message(8),message(7)])
    assert f.wire.closed
    calls = len(f.wire.calls)
    a = value.sample(size=2,eligible_ids=[9,'7',7,'9'])
    assert a.to_json() == value.sample(size=2,eligible_ids={7,9}).to_json()
    assert value.sample().to_json() == value.sample(eligible_ids=[9,8,7]).to_json()
    assert value.sample(eligible_ids=[]).selected_ids == () and value.sample(size=0).selected_ids == ()
    assert len(f.wire.calls) == calls
    for invalid in ([True],['07'],['0'],[0],[2**31],[100],(x for x in [7]),'7',{'id':7},[7]*10001):
        fx.refuses(HistorySampleError,lambda:value.sample(eligible_ids=invalid))
    for size in (-1,True,1.0,'1',None,10001):
        fx.refuses(HistorySampleError,lambda:value.sample(size=size))
    original = value.to_json()
    def topic(record):
        raise RuntimeError('caller predicate failed')
    fx.refuses(RuntimeError,lambda:[r['id'] for r in value.messages if topic(r)])
    assert value.to_json() == original and len(f.wire.calls) == calls


async def test_waterfill_totality_conservation_and_sparse_redistribution():
    for n in range(5):
        for capacities in itertools.product(range(4),repeat=n):
            for size in range(0,sum(capacities)+3):
                quota = _quotas(capacities,size)
                assert sum(quota) == min(size,sum(capacities))
                assert all(0 <= q <= c for q,c in zip(quota,capacities))
                active = [q for q,c in zip(quota,capacities) if q < c]
                assert not active or max(active)-min(active) <= 1
                assert quota == _quotas(capacities,size)
    rows = [message(1,DATE),message(2,DATE+timedelta(days=1))]
    rows += [message(i,DATE+timedelta(days=2,seconds=i)) for i in range(3,23)]
    tg, _, _ = source_setup(rows)
    value = await capture(tg,end_date=DATE+timedelta(days=3))
    assert [b['selected_messages'] for b in value.sample(size=8).to_dict()['buckets']] == [1,1,6]
    assert value.sample(size=1).selected_ids == (2,)
    assert value.sample(size=2).selected_ids == (1,12)
    assert len(value.sample(size=100).messages) == 22


async def test_loader_rejects_malformed_json_and_byte_overflow():
    value, _, _ = await small_capture()
    text = value.to_json()
    for bad in ('{','null','[]','{"schema":1,"schema":2}','NaN',b'\xff',text[:-1]+',"extra":0}'):
        fx.refuses(HistorySampleError,lambda:HistoryCapture.from_json(bad))
    for data in (None,1,{},bytearray(text.encode())):
        fx.refuses(HistorySampleError,lambda:HistoryCapture.from_json(data))
    fx.refuses(HistorySampleError,lambda:HistoryCapture.from_json(text,max_bytes=len(text.encode())-1))
    assert HistoryCapture.from_json(text,max_bytes=len(text.encode())).capture_id == value.capture_id
    changed = value.to_dict(); changed['buckets'][0]['records'][0]['text'] = 'changed'
    fx.refuses(HistorySampleError,lambda:HistoryCapture.from_json(json.dumps(changed)))
    fx.refuses(HistorySampleError,lambda:HistoryCapture.from_json(value.sample().to_json()))
    for bound in (0,True,1.0,'1'):
        fx.refuses(HistorySampleError,lambda:HistoryCapture.from_json(text,max_bytes=bound))


async def test_loader_rejects_rehashed_contradictory_source_evidence():
    value, _, _ = await small_capture()
    def refuse(change):
        data=value.to_dict(); change(data); data['capture_id']=_identity(data,'capture_id')
        fx.refuses(HistorySampleError,lambda:HistoryCapture.from_json(json.dumps(data)))
    for key,bad in [('requests',0),('pages',0),('scanned_messages',0),('unavailable_messages',4),
                    ('end_reason',None),('end_reason','window_start'),('pages',True)]:
        refuse(lambda d,key=key,bad=bad:d['buckets'][0].__setitem__(key,bad))
    for key,bad in [('account_id',True),('stop_reason','request_limit'),('algorithm','other'),
                    ('version',True),('target','@UNNORMALIZED')]:
        refuse(lambda d,key=key,bad=bad:d.__setitem__(key,bad))
    refuse(lambda d:d['group'].__setitem__('peer_id',-7))
    refuse(lambda d:d['buckets'][0].__setitem__('start_date',d['end_date']))
    refuse(lambda d:d['buckets'][0]['records'][0].__setitem__('date',d['end_date']))
    refuse(lambda d:d['buckets'][0]['records'][0].__setitem__('id','9'))
    refuse(lambda d:d['buckets'][0]['records'].reverse())
    refuse(lambda d:d['limits'].__setitem__('max_messages',1))


async def test_invalid_public_inputs_precede_configuration_io():
    tg=TgData('/missing/config.ini')
    async def bad_beat(_):
        pass
    with patch.object(tg.connection_engine,'_load_config',side_effect=AssertionError('config I/O')):
        for name in ('max_messages','max_requests'):
            for bad in (0,-1,True,None,1.0,'1',[],10001):
                await fx.expect(HistorySampleError,capture(tg,**{name:bad}))
        for owner in (0,-1,True,None,222.0,'222'):
            await fx.expect(ValueError,capture(tg,account_id=owner))
        for start,end in ((None,DATE),(DATE,DATE),(DATE.replace(tzinfo=None),DATE),
                          (datetime(1960,1,1,tzinfo=timezone.utc),DATE)):
            await fx.expect(BatchFormatError,capture(tg,start_date=start,end_date=end))
        await fx.expect(ValueError,capture(tg,end_date=datetime.now(timezone.utc)+timedelta(days=1)))
        for beat in (1,[],bad_beat):
            await fx.expect(BatchFormatError,capture(tg,heartbeat=beat))
        await fx.expect(GroupReferenceError,tg.capture_group_history('bad/ref',account_id=222,
            start_date=DATE,end_date=DATE+timedelta(days=1)))
    assert not tg._account_health
    await tg.close()


async def test_bad_page_is_atomic_and_earlier_day_survives():
    tg,f=setup(page([message(9)]),page([message(10,DATE+timedelta(days=1)),
                                      message(10,DATE+timedelta(days=1))]))
    error=await fx.expect(GroupResponseError,capture(tg,end_date=DATE+timedelta(days=2),max_requests=2))
    partial=error.partial_result
    assert partial.sample().selected_ids==(9,) and partial.stop_reason=='error'
    assert partial.coverage['requests']==2 and partial.coverage['pages']==1
    assert partial.buckets[0]['end_reason']=='history_end' and partial.buckets[1]['records']==[]
    assert partial.sample().to_dict()['buckets'][0]['coverage_complete'] and not partial.coverage_complete
    assert tg.get_account_health(222)['events']==0 and f.wire.closed


async def test_cross_bucket_conflicting_id_refuses_whole_page():
    tg,_=setup(page([message(9)]),page([message(9,DATE+timedelta(days=1))]))
    error=await fx.expect(GroupResponseError,capture(tg,end_date=DATE+timedelta(days=2),max_requests=2))
    assert error.partial_result.sample().selected_ids==(9,) and error.partial_result.coverage['pages']==1


async def test_nonprogress_dates_peers_and_oversized_pages_refuse():
    for row in (message(10),message(11),message(9,DATE+timedelta(seconds=1)),
                message(9,peer=types.PeerChat(7))):
        tg,_=setup(page([message(10)],'slice'),page([row]))
        error=await fx.expect(GroupResponseError,capture(tg))
        assert error.partial_result.sample().selected_ids==(10,)
    for budget,kind in ((False,GroupResponseError),(True,ReadBudgetError)):
        tg,_=setup(page([message(9),message(8)]),budget=budget)
        error=await fx.expect(kind,capture(tg,max_messages=1))
        assert not error.partial_result.messages
    tg,_=setup(types.messages.MessagesNotModified(1))
    error=await fx.expect(GroupResponseError,capture(tg))
    assert error.partial_result.coverage['pages']==0


async def test_supported_peer_families_and_numeric_references():
    for entity,peer in ((g.chat(),types.PeerChat(7)),(g.channel(),types.PeerChannel(7)),
                       (g.channel(megagroup=False,broadcast=True),types.PeerChannel(7))):
        tg,f=setup(page([message(peer=peer)]),entity=entity,seeds=(entity,),responses={
            'GetChatsRequest':g.Reply(types.messages.Chats([entity])),
            'GetChannelsRequest':g.Reply(types.messages.Chats([entity]))})
        target=-7 if isinstance(peer,types.PeerChat) else -1000000000007
        value=await tg.capture_group_history(target,account_id=222,start_date=DATE,
            end_date=DATE+timedelta(days=1),max_requests=1)
        assert value.group.peer_id==target and value.coverage_complete
        assert not g.requests(f,functions.contacts.ResolveUsernameRequest)


async def test_unusable_target_metadata_refuses_before_history():
    for reply in (types.contacts.ResolvedPeer(types.PeerUser(222),[],[fx.user(222)]),
                  types.contacts.ResolvedPeer(types.PeerChannel(7),[g.channel(min=True)],[])):
        tg,f=setup(responses={'ResolveUsernameRequest':g.Reply(reply)})
        error=await fx.expect(GroupReferenceError,capture(tg))
        assert not g.requests(f,functions.messages.GetHistoryRequest)
        assert not hasattr(error,'partial_result')


async def test_cached_owner_policy_and_actual_budget_owner():
    tg,f=setup(page([message()]),cached=111,budget=True,proxy=True)
    value=await capture(tg,max_messages=3,max_requests=1)
    assert value.account_id==222 and f.clients[0]._self_id==111
    assert f.budget.status(222).used==1 and f.budget.status(111).used==0
    assert f.wire.policy_at_connect==dict(flood=0,requests=0,connections=0,delay=0,
        reconnect=False,last_error=True,updates=False)
    assert f.wire.proxy_at_connect==f.engine._load_config().proxy
    assert f.clients[0]._init_request.device_model=='Stage 1 device'
    assert f.name in f.store and not list(f.root.glob('*.session'))


async def test_wrong_owner_and_missing_auth_prevent_group_work():
    tg,f=setup(cached=111)
    await fx.expect(AccountIdentityError,capture(tg,account_id=111))
    assert not g.requests(f,functions.contacts.ResolveUsernameRequest) and f.wire.closed
    tg,f=setup(logged_in=False,responses={'GetStateRequest':h.RPCReply(401,'AUTH_KEY_UNREGISTERED')})
    error=await fx.expect(AuthRequiredError,capture(tg))
    assert error.first_login and not g.requests(f,functions.messages.GetHistoryRequest)


async def test_budget_all_slots_and_refusal_preserve_prior_day():
    tg,f=setup(page([service(9),types.MessageEmpty(8,peer_id=None),message(7,DATE-timedelta(days=1))]),budget=True)
    value=await capture(tg,max_messages=3,max_requests=1)
    assert f.budget.status(222).used==value.coverage['scanned_messages']==3
    assert not value.sample().messages and not value.coverage_complete
    tg,f=setup(page([message(9)]),budget=True)
    f.budget.configure(222,1)
    error=await fx.expect(ReadBudgetExceeded,capture(tg,end_date=DATE+timedelta(days=2),max_messages=4))
    assert error.partial_result.sample().selected_ids==(9,)
    assert error.partial_result.coverage['requests']==2 and len(g.requests(f,functions.messages.GetHistoryRequest))==1
    assert f.budget.status(222).used==1


async def test_owner_change_at_later_admission_refuses():
    def first(wire,req):
        wire.account=333
        return g.Reply(page([message(9)],'slice'))
    tg,f=setup(budget=True,responses={'GetHistoryRequest':first})
    error=await fx.expect(AccountIdentityError,capture(tg,max_messages=3))
    assert error.partial_result.sample().selected_ids==(9,)
    assert len(g.requests(f,functions.messages.GetHistoryRequest))==1
    assert f.budget.status(222).used==1 and f.budget.status(333).used==0


async def test_source_local_and_settlement_errors_preserve_original_and_prefix():
    for kind in ('rpc','local','settle'):
        denial=h.RPCReply(400,'CHANNEL_PRIVATE'); failure=OSError('local failure'); count=0
        def response(wire,req):
            nonlocal count
            count+=1
            if count==2 and kind=='rpc': return denial
            if count==2 and kind=='local': raise failure
            return g.Reply(page([message(9)]))
        events=[]
        tg,f=g.setup(budget=True,callback=events.append,responses={'GetHistoryRequest':response})
        original=f.budget._settle
        def settle(*args):
            if count==2 and kind=='settle': raise failure
            return original(*args)
        with patch.object(f.budget,'_settle',side_effect=settle):
            error=await fx.expect(errors.ChannelPrivateError if kind=='rpc' else OSError,
                capture(tg,end_date=DATE+timedelta(days=2),max_messages=10))
        assert error is (denial.error if kind=='rpc' else failure)
        assert error.partial_result.sample().selected_ids==(9,) and f.wire.closed
        assert error.partial_result.coverage['pages']==1 and error.partial_result.coverage['requests']==2
        await h.deliveries(tg)
        assert len(events)==(1 if kind=='rpc' else 0)
        if events:
            assert events[0]['account']['user_id']==222 and events[0]['call']=='capture_group_history'
        assert tg.get_account_health(111) is None


async def test_wait_no_retry_and_annotation_refusal_preserves_error():
    wait=h.RPCReply(420,'FLOOD_WAIT_30')
    tg,f=setup(wait)
    assert await fx.expect(errors.FloodWaitError,capture(tg)) is wait.error
    assert len(g.requests(f,functions.messages.GetHistoryRequest))==1
    class Refusing(OSError):
        def __setattr__(self,name,value):
            if name=='partial_result': raise RuntimeError('annotation refused')
            super().__setattr__(name,value)
    original=Refusing('original')
    tg,f=setup(page([message(9)],'slice'),original)
    assert await fx.expect(Refusing,capture(tg)) is original
    assert f.wire.closed and tg.get_account_health(222)['events']==0


async def test_heartbeat_is_observational_and_success_does_not_clear_access_failure():
    tg,f=g.setup(responses={'GetHistoryRequest':h.RPCReply(400,'CHANNEL_PRIVATE')})
    assert (await tg.check_group_access('synthetic_room',account_id=222)).status=='denied'
    f.responses['GetHistoryRequest']=g.Reply(page())
    beats=[]; selected=object(); tg.current_group=selected
    value=await capture(tg,heartbeat=beats.append)
    assert value.coverage_complete and tg.get_account_health(222)['no_access']['synthetic_room']
    assert beats.count('history page done')==1 and beats.count('request')==beats.count('request done')
    assert tg.current_group is selected and f.engine._primary_client is f.engine._pool is None
    for kind in (RuntimeError,asyncio.CancelledError,errors.ChannelPrivateError):
        def bad(_): raise kind('callback')
        tg,f=setup(page())
        assert (await capture(tg,heartbeat=bad)).coverage_complete
        assert tg.get_account_health(222)['events']==0


async def test_stalled_later_day_cancels_with_prior_capture_and_no_fake_beats():
    entered,release=asyncio.Event(),asyncio.Event()
    tg,f=setup(page([message(9)]),g.Reply(page(),entered=entered,release=release),budget=True)
    beats=[]
    task=asyncio.create_task(capture(tg,end_date=DATE+timedelta(days=2),max_messages=4,heartbeat=beats.append))
    try:
        await asyncio.wait_for(entered.wait(),3)
        before=list(beats); await fx.turns(20); assert beats==before
        task.cancel(); error=await fx.expect(asyncio.CancelledError,task)
        assert error.partial_result.sample().selected_ids==(9,)
        assert error.partial_result.stop_reason=='cancelled' and not error.partial_result.coverage_complete
        assert f.wire.closed and f.budget.status(222).reserved==1
        release.set(); await fx.turns(10)
        assert beats==before and tg.get_account_health(222)['events']==0
    finally:
        release.set(); await asyncio.gather(task,return_exceptions=True)


async def test_repeated_cleanup_cancellation_waits_for_disconnect():
    closing,release=asyncio.Event(),asyncio.Event()
    def prepare(client):
        client._sender.close_entered,client._sender.close_release=closing,release
    tg,f=setup(page(),prepare=prepare)
    task=asyncio.create_task(capture(tg))
    try:
        await asyncio.wait_for(closing.wait(),3)
        task.cancel(); await fx.turns(); task.cancel(); await fx.turns()
        assert not task.done() and not f.wire.closed
        release.set(); await fx.expect(asyncio.CancelledError,task)
        assert f.wire.closed
    finally:
        release.set(); await asyncio.gather(task,return_exceptions=True)


async def test_cleanup_failure_preserves_result_and_original_error():
    def prepare(client): client._sender.close_error=RuntimeError('cleanup')
    tg,f=setup(page(),prepare=prepare)
    assert (await capture(tg)).coverage_complete and f.wire.close_calls==1
    original=OSError('source')
    tg,f=setup(page([message(9)],'slice'),original,prepare=prepare)
    assert await fx.expect(OSError,capture(tg)) is original
    assert original.partial_result.sample().selected_ids==(9,) and f.wire.close_calls==1


async def main():
    assert telethon.__version__=='1.45.0'
    tests=sorted((name,value) for name,value in globals().items() if name.startswith('test_') and callable(value))
    failed=0
    with tempfile.TemporaryDirectory(prefix='tgdata-sampling-') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient,'start',side_effect=AssertionError('login forbidden')), \
         patch.object(telethon.TelegramClient,'send_code_request',side_effect=AssertionError('code forbidden')), \
         patch.object(fx.Wire,'send',g.send):
        fx.TMP=Path(tmp)
        for name,test in tests:
            try:
                await asyncio.wait_for(test(),20)
                print('PASS',name,flush=True)
            except (Exception,asyncio.CancelledError):
                failed+=1; print('FAIL',name,flush=True); traceback.print_exc()
            finally:
                for client in fx.CLIENTS:
                    client._sender.close_error=None
                    if client._sender.close_release is not None: client._sender.close_release.set()
                    await client.disconnect()
                for tg in h.FACADES: await tg.close()
                await asyncio.gather(*h.RPC_TASKS,return_exceptions=True)
                fx.CLIENTS.clear(); h.FACADES.clear(); h.RPC_TASKS.clear(); g.TRACE.clear()
    print('{} passed; {} failed'.format(len(tests)-failed,failed),flush=True)
    return bool(failed)


if __name__=='__main__':
    sys.exit(asyncio.run(main()))
