"""Activity measurements on real Telethon1.45 dispatch/TL/SQLite; sockets forbidden."""
import asyncio
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
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
from telethon.extensions import BinaryReader
from telethon.tl import functions, types
from tgdata import (
    TgData, GroupActivity, ActivityMessage, GroupResponseError, GroupReferenceError,
    BatchFormatError, ReadBudgetExceeded, ReadBudgetError, AuthRequiredError,
)
from tgdata.account_operation import AccountIdentityError
from tgdata.smoke_tests import test_34_group_access as g

fx, h, DATE = g.fx, g.h, g.DATE


def message(id=9, date=DATE, peer=None, **kwargs):
    # The real TL schema stores views and forwards under the same presence flag.
    if 'views' in kwargs:
        kwargs.setdefault('forwards', 0)
    if 'forwards' in kwargs:
        kwargs.setdefault('views', 0)
    return types.Message(id, peer or types.PeerChannel(7), date=date,
                         message='private text must not enter result', **kwargs)


def service(id=8, date=DATE, peer=None):
    return types.MessageService(id, peer or types.PeerChannel(7), date=date,
                                action=types.MessageActionEmpty())


def page(rows=(), mode='full', count=999):
    if mode == 'full':
        return types.messages.Messages(list(rows), [], [], [])
    if mode == 'slice':
        return types.messages.MessagesSlice(count, list(rows), [], [], [])
    return types.messages.ChannelMessages(1, count, list(rows), [], [], [])


def setup(*replies, **kwargs):
    values = [r if isinstance(r, (g.Reply, h.RPCReply, Exception)) else g.Reply(r)
              for r in (replies or (page(),))]
    def response(wire, req):
        assert values, 'unexpected extra history request'
        value = values.pop(0)
        if isinstance(value, Exception):
            raise value
        return value
    responses = kwargs.pop('responses', {})
    responses.setdefault('GetHistoryRequest', response)
    return g.setup(responses=responses, **kwargs)


async def measure(tg, cap=10, **kwargs):
    options = dict(account_id=222, start_date=DATE-timedelta(days=1),
                   end_date=DATE+timedelta(days=1), max_messages=cap)
    options.update(kwargs)
    return await tg.measure_group_activity('synthetic_room', **options)


async def test_exports_frozen_values_and_json():
    import tgdata
    tg, f = setup(page([message(grouped_id=2**62+17, views=0, forwards=0)]))
    value = await measure(tg)
    assert isinstance(value, GroupActivity) and isinstance(value.messages[0], ActivityMessage)
    assert value.schema_version == 1 and value.account_id == 222
    assert {'GroupActivity', 'ActivityMessage'} <= set(tgdata.__all__)
    assert tgdata.__version__ == '0.1.4' and len(set(tgdata.__all__)) == len(tgdata.__all__)
    for obj, key in ((value, 'coverage_complete'), (value.messages[0], 'views'), (value.group, 'title')):
        fx.refuses(FrozenInstanceError, lambda: setattr(obj, key, 42))
    data = value.to_dict()
    assert json.loads(json.dumps(data)) == data
    assert data['messages'][0]['grouped_id'] == str(2**62+17)
    data['messages'][0]['views'] = 99
    data['group']['title'] = 'changed'
    data['statistics']['message_count'] = 99
    assert value.messages[0].views == 0 and value.statistics['message_count'] == 1
    assert value.group.title == 'Synthetic group'
    assert 'access_hash' not in json.dumps(value.to_dict())
    assert 'private text' not in repr(value) + json.dumps(value.to_dict())
    assert value.collection_started_at <= value.messages[0].observed_at <= value.collection_finished_at
    assert f.wire.closed


async def test_invalid_inputs_precede_all_io():
    tg = TgData('/missing/config.ini')
    async def bad_beat(_):
        pass
    with patch.object(tg.connection_engine, '_load_config', side_effect=AssertionError('config I/O')):
        for cap in (0,-1,True,False,None,1.0,'1',[],2**31):
            await fx.expect(ValueError, measure(tg, cap))
        for owner in (0,-1,True,None,222.0,'222'):
            await fx.expect(ValueError, measure(tg, account_id=owner))
        for start, end in ((None,DATE), (DATE,None), (DATE,DATE),
                           (DATE+timedelta(days=1),DATE), (DATE.replace(tzinfo=None),DATE),
                           (DATE,DATE.replace(tzinfo=None)),
                           (datetime(1960,1,1,tzinfo=timezone.utc),DATE)):
            await fx.expect(BatchFormatError, measure(tg, start_date=start,end_date=end))
        await fx.expect(ValueError, measure(tg, end_date=datetime.now(timezone.utc)+timedelta(days=1)))
        for callback in (1,[],bad_beat):
            await fx.expect(BatchFormatError, measure(tg, heartbeat=callback))
        await fx.expect(GroupReferenceError, tg.measure_group_activity('bad/ref',
            account_id=222,start_date=DATE-timedelta(days=1),end_date=DATE))
    fx.refuses(TypeError, lambda: tg.measure_group_activity('synthetic_room'))
    assert not tg._account_health
    await tg.close()


async def test_half_open_fractional_bounds_and_wire_seek():
    start, end = DATE+timedelta(microseconds=1), DATE+timedelta(seconds=2,microseconds=1)
    rows = [message(9,DATE+timedelta(seconds=3)),message(8,DATE+timedelta(seconds=2)),
            message(7,DATE+timedelta(seconds=1)),message(6,DATE)]
    tg, f = setup(page(rows,'channel'))
    value = await measure(tg,4,start_date=start,end_date=end)
    assert [m.id for m in value.messages] == [8,7]
    assert value.coverage_complete and value.stop_reason == 'window_start'
    req = g.requests(f,functions.messages.GetHistoryRequest)[0]
    with BinaryReader(bytes(req)) as reader:
        decoded = reader.tgread_object()
    assert decoded.offset_date == DATE+timedelta(seconds=3)
    assert req.min_id == req.max_id == req.add_offset == 0
    assert value.oldest_observed_message_date == DATE
    assert value.newest_observed_message_date == DATE+timedelta(seconds=3)


async def test_exact_end_and_equal_timestamp_page_boundary():
    tg, f = setup(page([message(9,DATE+timedelta(seconds=1)),message(8)],'slice'),
                  page([message(7),message(6,DATE-timedelta(seconds=1))],'slice'))
    value = await measure(tg,5,start_date=DATE,end_date=DATE+timedelta(seconds=1))
    assert [m.id for m in value.messages] == [8,7] and value.coverage_complete
    requests = g.requests(f,functions.messages.GetHistoryRequest)
    assert [r.offset_id for r in requests] == [0,8]
    assert requests[1].offset_date is None and requests[0].offset_date == value.end_date


async def test_timezone_normalization():
    zone = timezone(timedelta(hours=3))
    tg, _ = setup(page([message()]))
    value = await measure(tg,start_date=(DATE-timedelta(days=1)).astimezone(zone),
                          end_date=(DATE+timedelta(days=1)).astimezone(zone))
    assert value.start_date == DATE-timedelta(days=1)
    assert value.start_date.tzinfo == timezone.utc and len(value.statistics['daily']) == 2


async def test_empty_history_complete_and_no_unknown_zero_counters():
    for mode in ('full','slice','channel'):
        tg, _ = setup(page(mode=mode,count=500))
        v = await measure(tg)
        assert v.stop_reason == 'history_end' and v.coverage_complete and v.scanned_messages == 0
        assert v.pages == 1 and v.oldest_observed_message_date is None
        s = v.statistics
        assert s['message_count'] == s['known_user_count'] == s['messages_per_24h'] == 0
        assert s['latest_observed_message_date'] is None
        assert s['counters']['views']['sum'] is None


async def test_short_page_is_not_history_end():
    tg, f = setup(page([message(9)],'channel',count=1),page([message(7)],'channel',count=1),page())
    value = await measure(tg,10)
    assert value.pages == 3 and value.scanned_messages == 2 and value.coverage_complete
    assert [m.id for m in value.messages] == [9,7]
    assert [r.limit for r in g.requests(f,functions.messages.GetHistoryRequest)] == [10,9,8]


async def test_dense_pagination_and_exact_cap():
    rows = [message(i) for i in range(150,0,-1)]
    tg, f = setup(page(rows[:100],'channel'),page(rows[100:],'channel'),page())
    value = await measure(tg,200)
    assert [m.id for m in value.messages] == list(range(150,0,-1))
    assert value.coverage_complete and value.scanned_messages == 150
    assert [r.offset_id for r in g.requests(f,functions.messages.GetHistoryRequest)] == [0,51,1]
    tg, f = setup(page(rows[:100],'channel',count=100))
    limited = await measure(tg,100)
    assert limited.stop_reason == 'message_limit' and not limited.coverage_complete
    assert limited.statistics['messages_per_24h'] is None
    assert len(g.requests(f,functions.messages.GetHistoryRequest)) == 1
    tg, _ = setup(page(rows[:100]))
    assert (await measure(tg,100)).coverage_complete


async def test_empty_placeholders_are_not_lost_or_complete():
    tg, f = setup(page([types.MessageEmpty(9,peer_id=None),types.MessageEmpty(8,peer_id=None)],'slice'),page())
    value = await measure(tg,3)
    assert value.pages == 2 and value.scanned_messages == value.unavailable_messages == 2
    assert value.messages == () and not value.coverage_complete and value.stop_reason == 'history_end'
    assert g.requests(f,functions.messages.GetHistoryRequest)[1].offset_id == 8


async def test_unknown_slot_prevents_boundary_completion():
    tg, _ = setup(page([message(9),types.MessageEmpty(8,peer_id=None),
                       message(7,DATE-timedelta(days=2))],'channel'))
    value = await measure(tg,3)
    assert value.stop_reason == 'window_start' and not value.coverage_complete
    assert value.unavailable_messages == 1 and value.statistics['message_count'] == 1


async def test_raw_albums_services_and_identity_populations():
    rows = [message(9,from_id=types.PeerUser(10),grouped_id=100),
            message(8,from_id=types.PeerUser(10),grouped_id=100),
            message(7,from_id=types.PeerChannel(10)),message(6),
            message(5,from_id=types.PeerChat(7)),service(4)]
    tg, _ = setup(page(rows))
    v = await measure(tg)
    s = v.statistics
    assert s['message_count'] == 5 and s['service_message_count'] == 1
    assert s['known_user_count'] == s['channel_sender_count'] == 1
    assert s['unknown_author_messages'] == 2 and len(v.messages) == 6
    assert [m.grouped_id for m in v.messages[:2]] == [100,100]
    assert s['counters']['views']['missing_count'] == 5


async def test_zero_missing_and_counter_distribution_population():
    rows = [message(9,views=0,forwards=0),message(8),message(7,views=10,forwards=4)]
    tg, _ = setup(page(rows))
    value = await measure(tg)
    stats = value.statistics
    assert stats['counters']['views'] == dict(known_count=2,missing_count=1,sum=10,mean=5,median=5,min=0,max=10)
    assert stats['counters']['forwards']['mean'] == 2
    assert stats['counters']['reactions'] == dict(known_count=0,missing_count=3,sum=None,mean=None,median=None,min=None,max=None)
    assert value.coverage_complete and stats['messages_per_24h'] == 1.5


async def test_reaction_totals_and_reply_counter_meaning():
    rows = [message(9,reactions=types.MessageReactions([
        types.ReactionCount(types.ReactionEmoji('👍'),0),
        types.ReactionCount(types.ReactionCustomEmoji(33),4)],min=True),
        replies=types.MessageReplies(2,1,comments=True,channel_id=7)),
        message(8,reactions=types.MessageReactions([]),replies=types.MessageReplies(0,1)),message(7)]
    tg, _ = setup(page(rows))
    v = await measure(tg)
    assert [m.reactions for m in v.messages] == [4,0,None]
    assert [m.replies for m in v.messages] == [2,0,None]
    assert [m.replies_are_comments for m in v.messages] == [True,False,None]
    assert v.statistics['counters']['reactions']['mean'] == 2


async def test_forward_origin_does_not_invent_forward_count():
    tg, _ = setup(page([message(fwd_from=types.MessageFwdHeader(DATE,from_id=types.PeerUser(8)))]))
    assert (await measure(tg)).messages[0].forwards is None


async def test_counter_changes_do_not_mutate_prior_observations():
    tg, f = setup(page([message(9,views=0)]),page([message(9,views=12)]))
    first, second = await measure(tg), await measure(tg)
    assert first.messages[0].id == second.messages[0].id == 9
    assert first.messages[0].views == 0 and second.messages[0].views == 12
    assert first.messages[0].observed_at <= second.messages[0].observed_at


async def test_daily_boundaries_and_unique_author_denominators():
    start, end = DATE-timedelta(hours=12), DATE+timedelta(days=1,hours=12)
    rows = [service(10,DATE+timedelta(days=1,hours=2)),
            message(9,DATE+timedelta(days=1),from_id=types.PeerUser(10)),
            message(8,DATE,from_id=types.PeerUser(10)),
            message(7,DATE-timedelta(hours=1),from_id=types.PeerUser(10))]
    tg, _ = setup(page(rows))
    s = (await measure(tg,start_date=start,end_date=end)).statistics
    assert [d['window_seconds'] for d in s['daily']] == [43200,86400,43200]
    assert [d['message_count'] for d in s['daily']] == [1,1,1]
    assert s['known_user_count'] == 1 and s['messages_per_24h'] == 1.5
    assert s['latest_observed_message_date'] == (DATE+timedelta(days=1)).isoformat()


async def test_wide_sparse_window_has_all_days_without_row_cross_product():
    start, end = datetime(1970,1,1,tzinfo=timezone.utc), DATE+timedelta(days=1)
    tg, _ = setup(page([message()]))
    s = (await measure(tg,start_date=start,end_date=end)).statistics
    assert len(s['daily']) == (end-start).days
    assert sum(row['message_count'] for row in s['daily']) == 1
    assert s['daily'][0]['message_count'] == 0 and s['daily'][-1]['message_count'] == 1


async def test_bad_page_is_atomic_and_previous_page_survives():
    tg, f = setup(page([message(10,views=4)],'channel'),page([message(9),message(8,views=-1)]))
    error = await fx.expect(GroupResponseError,measure(tg))
    partial = error.partial_result
    assert [m.id for m in partial.messages] == [10] and partial.scanned_messages == partial.pages == 1
    assert partial.stop_reason == 'error' and not partial.coverage_complete
    assert partial.statistics['counters']['views']['mean'] == 4
    assert tg.get_account_health(222)['events'] == 0 and f.wire.closed


async def test_nonprogress_and_date_order_refuse():
    for row in (message(10),message(11),message(9,DATE+timedelta(seconds=1))):
        tg, _ = setup(page([message(10)],'slice'),page([row]))
        error = await fx.expect(GroupResponseError,measure(tg))
        assert [m.id for m in error.partial_result.messages] == [10]


async def test_malformed_vectors_counters_and_peers_refuse():
    cases = [page([message(9),message(9)]),page([message(peer=types.PeerChat(7))]),
             page([message(peer=types.PeerChannel(8))]),page([message(forwards=-1)]),
             page([message(replies=types.MessageReplies(-1,1))]),
             page([message(reactions=types.MessageReactions([types.ReactionCount(types.ReactionEmoji('x'),-1)]))]),
             page([message(from_id=types.PeerUser(0))]),types.messages.MessagesNotModified(3)]
    for reply in cases:
        tg, f = setup(reply)
        error = await fx.expect(GroupResponseError,measure(tg))
        assert error.partial_result.messages == () and error.partial_result.pages == 0
        assert tg.get_account_health(222)['events'] == 0 and f.wire.closed


async def test_oversized_response_is_not_accepted():
    for budget, kind in ((False,GroupResponseError),(True,ReadBudgetError)):
        tg, f = setup(page([message(9),message(8)]),budget=budget)
        error = await fx.expect(kind,measure(tg,1))
        assert not error.partial_result.messages and not error.partial_result.coverage_complete
        assert len(g.requests(f,functions.messages.GetHistoryRequest)) == 1


async def test_supported_peer_families_and_numeric_cached_reference():
    for entity,peer in ((g.chat(),types.PeerChat(7)),(g.channel(),types.PeerChannel(7)),
                         (g.channel(megagroup=False,broadcast=True),types.PeerChannel(7))):
        tg, f = setup(page([message(peer=peer)]),entity=entity,seeds=(entity,),responses={
            'GetChatsRequest':g.Reply(types.messages.Chats([entity])),
            'GetChannelsRequest':g.Reply(types.messages.Chats([entity]))})
        v = await tg.measure_group_activity(-7 if isinstance(peer,types.PeerChat) else -1000000000007,
            account_id=222,start_date=DATE-timedelta(days=1),end_date=DATE+timedelta(days=1),max_messages=2)
        assert v.coverage_complete and v.statistics['message_count'] == 1
        assert not g.requests(f,functions.contacts.ResolveUsernameRequest)


async def test_user_target_refuses_before_history():
    tg, f = setup(responses={'ResolveUsernameRequest':g.Reply(types.contacts.ResolvedPeer(
        types.PeerUser(222),[],[fx.user(222)]))})
    error = await fx.expect(GroupReferenceError,measure(tg))
    assert not g.requests(f,functions.messages.GetHistoryRequest)
    assert getattr(error,'partial_result',None) is None


async def test_cached_owner_policy_and_actual_budget_owner():
    tg, f = setup(page([message()]),cached=111,budget=True,proxy=True)
    v = await measure(tg,3)
    assert v.account_id == 222 and f.clients[0]._self_id == 111
    assert f.budget.status(222).used == 1 and f.budget.status(111).used == 0
    assert f.wire.policy_at_connect == dict(flood=0,requests=0,connections=0,delay=0,
        reconnect=False,last_error=True,updates=False)
    assert f.wire.proxy_at_connect == f.engine._load_config().proxy
    assert f.clients[0]._init_request.device_model == 'Stage 1 device'
    assert f.name in f.store and not list(f.root.glob('*.session'))


async def test_wrong_owner_and_missing_auth_prevent_group_work():
    tg, f = setup(cached=111)
    await fx.expect(AccountIdentityError,measure(tg,account_id=111))
    assert not g.requests(f,functions.contacts.ResolveUsernameRequest) and f.wire.closed
    tg, f = setup(logged_in=False,responses={'GetStateRequest':h.RPCReply(401,'AUTH_KEY_UNREGISTERED')})
    error = await fx.expect(AuthRequiredError,measure(tg))
    assert error.first_login and not g.requests(f,functions.messages.GetHistoryRequest)


async def test_budget_counts_all_raw_slots_and_reserves_full_request():
    tg, f = setup(page([service(9),types.MessageEmpty(8,peer_id=None),
                        message(7,DATE-timedelta(days=2))]),budget=True)
    v = await measure(tg,3)
    assert f.budget.status(222).used == v.scanned_messages == 3
    assert v.statistics['message_count'] == 0
    tg, f = setup(page(),budget=True)
    error = await fx.expect(ReadBudgetExceeded,measure(tg,100))
    assert error.partial_result.scanned_messages == 0
    assert not g.requests(f,functions.messages.GetHistoryRequest) and f.budget.status(222).used == 0


async def test_owner_change_at_later_admission_refuses():
    def first(wire,req):
        wire.account = 333
        return g.Reply(page([message(9)],'channel'))
    tg, f = setup(budget=True,responses={'GetHistoryRequest':first})
    error = await fx.expect(AccountIdentityError,measure(tg,3))
    assert [m.id for m in error.partial_result.messages] == [9]
    assert len(g.requests(f,functions.messages.GetHistoryRequest)) == 1
    assert f.budget.status(222).used == 1 and f.budget.status(333).used == 0


async def test_later_source_error_and_owned_health_preserve_prefix():
    events=[]
    denial=h.RPCReply(400,'CHANNEL_PRIVATE')
    tg,f=setup(page([message(9)],'channel'),denial,budget=True,cached=111,callback=events.append)
    error=await fx.expect(errors.ChannelPrivateError,measure(tg,3))
    assert error is denial.error and [m.id for m in error.partial_result.messages] == [9]
    assert f.budget.status(222).used == 3 and f.budget.status(222).reserved == 2
    await h.deliveries(tg)
    assert len(events)==1 and events[0]['account']['user_id']==222
    assert events[0]['call']=='measure_group_activity' and events[0]['request']=='messages.GetHistoryRequest'
    assert tg.get_account_health(111) is None and f.wire.closed


async def test_wait_has_no_retry_or_sleep():
    wait=h.RPCReply(420,'FLOOD_WAIT_30')
    tg,f=setup(wait)
    error=await fx.expect(errors.FloodWaitError,measure(tg))
    assert error is wait.error and error.seconds==30
    assert error.partial_result.stop_reason=='error' and len(g.requests(f,functions.messages.GetHistoryRequest))==1


async def test_local_errors_and_refused_annotation_remain_original():
    class Refusing(OSError):
        def __setattr__(self,name,value):
            if name=='partial_result':
                raise RuntimeError('annotation refused')
            super().__setattr__(name,value)
    for error in (OSError('source'),ValueError('decode'),Refusing('original')):
        tg,f=setup(page([message(9)],'channel'),error)
        assert await fx.expect(type(error),measure(tg)) is error
        assert tg.get_account_health(222)['events']==0 and f.wire.closed
        if not isinstance(error,Refusing):
            assert len(error.partial_result.messages)==1


async def test_history_success_does_not_clear_access_restriction():
    tg,f=g.setup(responses={'GetHistoryRequest':h.RPCReply(400,'CHANNEL_PRIVATE')})
    assert (await tg.check_group_access('synthetic_room',account_id=222)).status=='denied'
    f.responses['GetHistoryRequest']=g.Reply(page([message()]))
    await measure(tg)
    assert tg.get_account_health(222)['no_access']['synthetic_room']


async def test_heartbeat_progress_callback_failures_and_no_legacy_mutation():
    beats=[]
    tg,f=setup(page([message()]))
    selected=object(); tg.current_group=selected
    await measure(tg,heartbeat=beats.append)
    assert beats.count('request')==beats.count('request done') and beats.count('activity page done')==1
    assert tg.current_group is selected and f.engine._primary_client is f.engine._pool is None
    assert tg._health.snapshot()['events']==0
    for kind in (RuntimeError,asyncio.CancelledError,errors.ChannelPrivateError):
        def bad(_):
            raise kind('callback secret')
        tg,f=setup(page())
        assert (await measure(tg,heartbeat=bad)).coverage_complete
        assert tg.get_account_health(222)['events']==0


async def test_stalled_later_page_cancels_with_partial_evidence():
    entered,release=asyncio.Event(),asyncio.Event()
    tg,f=setup(page([message(9)],'channel'),g.Reply(page([message(8)]),entered=entered,release=release),budget=True)
    beats=[]
    task=asyncio.create_task(measure(tg,3,heartbeat=beats.append))
    try:
        await asyncio.wait_for(entered.wait(),3)
        before=list(beats); await fx.turns(20)
        assert beats==before
        task.cancel(); error=await fx.expect(asyncio.CancelledError,task)
        assert [m.id for m in error.partial_result.messages]==[9]
        assert error.partial_result.stop_reason=='cancelled' and not error.partial_result.coverage_complete
        assert f.wire.closed and f.budget.status(222).reserved==2
        release.set(); await fx.turns(10)
        assert beats==before and tg.get_account_health(222)['events']==0
    finally:
        release.set(); await asyncio.gather(task,return_exceptions=True)


async def test_repeated_cleanup_cancellation_still_waits_for_disconnect():
    closing,release=asyncio.Event(),asyncio.Event()
    def prepare(client):
        client._sender.close_entered,client._sender.close_release=closing,release
    tg,f=setup(page(),prepare=prepare)
    task=asyncio.create_task(measure(tg))
    try:
        await asyncio.wait_for(closing.wait(),3)
        task.cancel(); await fx.turns(); task.cancel(); await fx.turns()
        assert not task.done() and not f.wire.closed
        release.set(); await fx.expect(asyncio.CancelledError,task)
        assert f.wire.closed
    finally:
        release.set(); await asyncio.gather(task,return_exceptions=True)


async def test_cleanup_errors_preserve_return_and_original_failure():
    def prepare(client):
        client._sender.close_error=RuntimeError('cleanup')
    tg,f=setup(page(),prepare=prepare)
    assert (await measure(tg)).coverage_complete and f.wire.close_calls==1
    original=OSError('source')
    tg,f=setup(page([message(9)],'channel'),original,prepare=prepare)
    assert await fx.expect(OSError,measure(tg)) is original
    assert len(original.partial_result.messages)==1 and f.wire.close_calls==1


async def main():
    assert telethon.__version__=='1.45.0'
    tests=sorted((name,value) for name,value in globals().items() if name.startswith('test_') and callable(value))
    failed=0
    with tempfile.TemporaryDirectory(prefix='tgdata-activity-') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient,'start',side_effect=AssertionError('login forbidden')), \
         patch.object(telethon.TelegramClient,'send_code_request',side_effect=AssertionError('code forbidden')), \
         patch.object(fx.Wire,'send',g.send):
        fx.TMP=Path(tmp)
        for name,test in tests:
            try:
                await asyncio.wait_for(test(),15)
                print('PASS',name,flush=True)
            except (Exception,asyncio.CancelledError):
                failed+=1; print('FAIL',name,flush=True); traceback.print_exc()
            finally:
                for client in fx.CLIENTS:
                    client._sender.close_error=None
                    if client._sender.close_release is not None:
                        client._sender.close_release.set()
                    await client.disconnect()
                for tg in h.FACADES:
                    await tg.close()
                await asyncio.gather(*h.RPC_TASKS,return_exceptions=True)
                fx.CLIENTS.clear(); h.FACADES.clear(); h.RPC_TASKS.clear(); g.TRACE.clear()
    print('{} passed; {} failed'.format(len(tests)-failed,failed),flush=True)
    return bool(failed)


if __name__=='__main__':
    sys.exit(asyncio.run(main()))
