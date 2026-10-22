"""Public profiles on real Telethon1.45 dispatch/TL/SQLite; sockets forbidden."""
import asyncio
from dataclasses import FrozenInstanceError
from datetime import timedelta, timezone
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
from tgdata import (
    TgData, GroupProfile, GroupPinnedMessage, GroupReferenceError, GroupResponseError,
    BatchFormatError, AuthRequiredError, ReadBudgetExceeded,
)
from tgdata.account_operation import AccountIdentityError
from tgdata.smoke_tests import test_34_group_access as g

fx, h, DATE = g.fx, g.h, g.DATE


def full(entity=None, count=10, online=2, about='Description'):
    entity = g.channel() if entity is None else entity
    if isinstance(entity, (types.Chat, types.ChatForbidden)):
        detail = types.ChatFull(entity.id, about, types.ChatParticipantsForbidden(entity.id),
                                types.PeerNotifySettings())
    else:
        detail = types.ChannelFull(entity.id, about, 0, 0, 0, types.PhotoEmpty(0),
            types.PeerNotifySettings(), [], 0, participants_count=count, online_count=online)
    return types.messages.ChatFull(detail, [entity], [])


def message(id=9, peer=None, text='Pinned text', date=DATE):
    return types.Message(id, peer or types.PeerChannel(7), date=date, message=text, pinned=True)


def pins(rows=(), count=None, inexact=None, channel=False):
    if count is None:
        return types.messages.Messages(list(rows), [], [], [])
    if channel:
        return types.messages.ChannelMessages(1, count, list(rows), [], [], [], inexact=inexact)
    return types.messages.MessagesSlice(count, list(rows), [], [], [], inexact=inexact)


def setup(entity=None, response=None, pin_response=None, responses=None, **kwargs):
    entity = g.channel() if entity is None else entity
    values = {
        'GetFullChannelRequest': g.Reply(full(entity) if response is None else response),
        'GetFullChatRequest': g.Reply(full(entity) if response is None else response),
        'SearchRequest': g.Reply(pins() if pin_response is None else pin_response),
    }
    values.update(responses or {})
    return g.setup(entity=entity, responses=values, **kwargs)


async def profile(tg, limit=0, **kwargs):
    return await tg.get_group_profile('synthetic_room', account_id=222,
                                     pinned_limit=limit, **kwargs)


async def test_defaults_and_full_metadata():
    tg, f = setup()
    value = await profile(tg)
    assert isinstance(value, GroupProfile) and value.account_id == 222
    assert value.target == 'synthetic_room' and value.group.peer_id == -1000000000007
    assert value.about == 'Description' and value.group.participants_count == 10
    assert value.online_count == 2 and value.observed_at.tzinfo == timezone.utc
    assert value.pins_status == 'not_requested' and value.pinned_messages == ()
    assert value.pins_total is value.pins_total_exact is value.pins_observed_at is None
    assert not g.requests(f, functions.messages.SearchRequest) and f.wire.closed


async def test_public_exports_and_detached_immutable_values():
    import tgdata
    assert {'GroupProfile', 'GroupPinnedMessage'} <= set(tgdata.__all__)
    assert tgdata.__version__ == '0.1.4'
    assert len(tgdata.__all__) == len(set(tgdata.__all__))
    tg, _ = setup(pin_response=pins([message()]))
    value = await profile(tg, 3)
    assert isinstance(value.pinned_messages[0], GroupPinnedMessage)
    for obj, name in ((value, 'about'), (value.group, 'title'), (value.pinned_messages[0], 'text')):
        fx.refuses(FrozenInstanceError, lambda: setattr(obj, name, 'changed'))
    payload = value.to_dict()
    payload['group']['title'] = 'changed'
    payload['pinned_messages'][0]['text'] = 'changed'
    assert value.group.title == 'Synthetic group'
    assert value.pinned_messages[0].text == 'Pinned text'
    assert 'access_hash' not in json.dumps(value.to_dict())
    assert 'Pinned text' not in repr(value) and 'Description' not in repr(value)


async def test_invalid_limits_and_callbacks_precede_io():
    tg = TgData('/missing/config.ini')
    async def async_beat(_):
        pass
    with patch.object(tg.connection_engine, '_load_config', side_effect=AssertionError('config read')):
        for limit in (True, False, None, -1, 101, 1.0, '1', [], 2**63):
            await fx.expect(ValueError, profile(tg, limit))
        for beat in (1, [], async_beat):
            await fx.expect(BatchFormatError, profile(tg, heartbeat=beat))
        await fx.expect(GroupReferenceError, tg.get_group_profile('bad/input', account_id=222))
    assert not tg._account_health


async def test_account_required_and_invalid_before_client():
    tg, f = setup()
    fx.refuses(TypeError, lambda: tg.get_group_profile('synthetic_room'))
    for account in (True, None, 0, -1, '222', 222.0):
        await fx.expect(ValueError, tg.get_group_profile('synthetic_room', account_id=account))
    assert not f.clients


async def test_verified_b_cached_a_and_factory_policy():
    tg, f = setup(cached=111, proxy=True, budget=True)
    value = await profile(tg, 3)
    assert value.account_id == 222 and f.clients[0]._self_id == 111
    assert f.wire.policy_at_connect == dict(flood=0, requests=0, connections=0,
        delay=0, reconnect=False, last_error=True, updates=False)
    assert f.wire.proxy_at_connect == f.engine._load_config().proxy
    assert f.clients[0]._init_request.device_model == 'Stage 1 device'
    assert tg.get_account_health(111) is None and f.budget.status(111).used == 0
    assert f.name in f.store and not list(f.root.glob('*.session'))


async def test_wrong_owner_prevents_every_group_request():
    tg, f = setup(cached=111)
    await fx.expect(AccountIdentityError,
                    tg.get_group_profile('synthetic_room', account_id=111, pinned_limit=3))
    assert not g.requests(f, functions.contacts.ResolveUsernameRequest)
    assert not g.requests(f, functions.channels.GetFullChannelRequest)
    assert f.wire.closed and not tg._account_health


async def test_absent_auth_never_requests_login():
    tg, f = setup(logged_in=False, responses={'GetStateRequest': h.RPCReply(401, 'AUTH_KEY_UNREGISTERED')})
    value = await fx.expect(AuthRequiredError, profile(tg, 3))
    assert value.first_login and f.wire.closed
    assert not g.requests(f, functions.contacts.ResolveUsernameRequest)


async def test_supported_families_use_expected_full_request():
    for entity, kind in ((g.chat(), 'group'), (g.channel(), 'megagroup'),
                          (g.channel(megagroup=False, broadcast=True), 'channel')):
        tg, f = setup(entity=entity)
        value = await profile(tg)
        assert value.group.kind == kind
        assert len(g.requests(f, functions.messages.GetFullChatRequest)) == (kind == 'group')
        assert len(g.requests(f, functions.channels.GetFullChannelRequest)) == (kind != 'group')
        assert value.online_count == (None if kind == 'group' else 2)
        assert value.group.participants_count == (2 if kind == 'group' else 10)


async def test_zero_unknown_and_full_description_preserved():
    for count, online in ((None, None), (0, 0), (0, 4)):
        text = '' if count is None else 'Привет 🌍\n' * 200
        tg, _ = setup(response=full(count=count, online=online, about=text))
        value = await profile(tg)
        assert value.group.participants_count == count and value.online_count == online
        assert value.about == text


async def test_channel_count_never_falls_back_to_entity():
    entity = g.channel(participants_count=999)
    tg, _ = setup(entity=entity, response=full(entity, count=None))
    assert (await profile(tg)).group.participants_count is None


async def test_basic_count_comes_from_matching_entity_not_users():
    reply = full(g.chat())
    reply.users = [fx.user(222)]
    reply.chats.insert(0, g.channel(participants_count=999))
    tg, _ = setup(entity=g.chat(), response=reply)
    value = await profile(tg)
    assert value.group.peer_id == -7 and value.group.participants_count == 2
    assert value.online_count is None


async def test_wrong_full_shapes_ids_and_namespace_refuse():
    variants = [types.User(7), full(g.chat()), full(g.channel(8))]
    duplicate = full()
    duplicate.chats.append(g.channel())
    variants.append(duplicate)
    missing = full()
    missing.chats = []
    variants.append(missing)
    wrong = full()
    wrong.chats = [g.chat()]
    variants.append(wrong)
    for reply in variants:
        tg, f = setup(response=reply)
        error = await fx.expect(GroupResponseError, profile(tg, 3))
        assert getattr(error, 'partial_result', None) is None
        assert not g.requests(f, functions.messages.SearchRequest)
        assert tg.get_account_health(222)['events'] == 0 and f.wire.closed


async def test_negative_full_counts_refuse_without_health():
    for count, online in ((-1, 0), (0, -1)):
        tg, _ = setup(response=full(count=count, online=online))
        await fx.expect(GroupResponseError, profile(tg))
        assert tg.get_account_health(222)['events'] == 0


async def test_unusable_and_unsupported_peers_refuse():
    for entity in (g.channel(min=True), g.channel(access_hash=None),
                   g.channel(megagroup=False, broadcast=False),
                   types.Community(7, 'Community', types.ChatPhotoEmpty(), DATE, access_hash=0)):
        tg, f = setup(entity=entity)
        await fx.expect(GroupReferenceError, profile(tg, 3))
        assert not g.requests(f, functions.channels.GetFullChannelRequest)
        assert not g.requests(f, functions.messages.SearchRequest) and f.wire.closed


async def test_invite_preview_refuses_without_join_or_full_read():
    tg, f = setup(responses={'CheckChatInviteRequest': g.Reply(
        types.ChatInvite('Preview', types.PhotoEmpty(0), 4, 0))})
    await fx.expect(GroupReferenceError,
                    tg.get_group_profile('t.me/+private_token', account_id=222, pinned_limit=3))
    assert not g.requests(f, functions.channels.GetFullChannelRequest)
    assert not g.requests(f, functions.messages.SearchRequest)


async def test_invite_already_and_peek_use_safe_labels():
    for reply in (types.ChatInviteAlready(g.channel()), types.ChatInvitePeek(g.channel(), DATE)):
        tg, _ = setup(responses={'CheckChatInviteRequest': g.Reply(reply)})
        value = await tg.get_group_profile('t.me/+private_token', account_id=222)
        assert value.target.startswith('invite:') and len(value.target) == 71
        assert 'private_token' not in json.dumps(value.to_dict())


async def test_numeric_namespace_and_hash_extremes_with_both_stores():
    for store in (None, fx.Store()):
        for access_hash in (0, 2**63-1, -2**63):
            entity = g.channel(access_hash=access_hash)
            tg, f = setup(entity=entity, seeds=[entity], store=store, responses={
                'GetChannelsRequest': g.Reply(types.messages.Chats([entity]))})
            value = await tg.get_group_profile(-1000000000007, account_id=222, pinned_limit=1)
            assert value.group.peer_id == -1000000000007
            assert g.requests(f, functions.channels.GetFullChannelRequest)[0].channel.access_hash == access_hash
            assert g.requests(f, functions.messages.SearchRequest)[0].peer.access_hash == access_hash


async def test_one_exact_filtered_request_and_separate_times():
    tg, f = setup(pin_response=pins([message()]))
    value = await profile(tg, 3)
    requests = g.requests(f, functions.messages.SearchRequest)
    assert len(requests) == 1
    request = requests[0]
    assert isinstance(request.filter, types.InputMessagesFilterPinned)
    assert (request.q, request.limit, request.hash, request.offset_id,
            request.add_offset, request.max_id, request.min_id) == ('', 3, 0, 0, 0, 0, 0)
    assert request.min_date is request.max_date is request.from_id is request.top_msg_id is None
    assert value.pins_observed_at >= value.observed_at
    assert value.pins_total == 1 and value.pins_total_exact is True
    assert value.pins_status == 'complete'


async def test_empty_exact_is_complete_not_omitted():
    for reply in (pins(), pins(count=0), pins(count=0, channel=True)):
        tg, _ = setup(pin_response=reply)
        value = await profile(tg, 1)
        assert value.pinned_messages == () and value.pins_status == 'complete'
        assert value.pins_total == 0 and value.pins_total_exact is True
        assert value.pins_observed_at is not None


async def test_limit_and_short_slice_coverage():
    for limit, rows, count, status in ((2, [message(9), message(8)], 4, 'limited'),
                                     (3, [message(9)], 4, 'incomplete'),
                                     (2, [message(9), message(8)], 2, 'complete')):
        tg, f = setup(pin_response=pins(rows, count=count, channel=True))
        value = await profile(tg, limit)
        assert value.pins_status == status and value.pins_total == count
        assert value.pins_total_exact is True
        assert len(g.requests(f, functions.messages.SearchRequest)) == 1


async def test_inexact_and_unavailable_are_independent():
    cases = [(pins([message()], count=1, inexact=True), False, 1, 'message'),
             (pins([types.MessageEmpty(9, None)], count=1), True, 1, 'unavailable'),
             (pins(count=0, inexact=True), False, 0, None),
             (pins([message()], count=0, inexact=True), False, 0, 'message')]
    for reply, exact, total, kind in cases:
        tg, _ = setup(pin_response=reply)
        value = await profile(tg, 3)
        assert value.pins_status == 'incomplete'
        assert value.pins_total_exact is exact and value.pins_total == total
        if kind:
            assert value.pinned_messages[0].kind == kind


async def test_content_and_service_pins_retain_ids_dates_and_empty_text():
    shifted = DATE.astimezone(timezone(timedelta(hours=3)))
    rows = [message(9, text='Кириллица\n' * 200, date=shifted), message(8, text=''),
            types.MessageService(7, types.PeerChannel(7), DATE, action=types.MessageActionEmpty())]
    tg, _ = setup(pin_response=pins(rows))
    value = await profile(tg, 3)
    assert [m.id for m in value.pinned_messages] == [9, 8, 7]
    assert [m.kind for m in value.pinned_messages] == ['message', 'message', 'service']
    assert value.pinned_messages[0].text == rows[0].message
    assert value.pinned_messages[1].text == '' and value.pinned_messages[2].text is None
    assert all(m.date == DATE and m.date.tzinfo == timezone.utc for m in value.pinned_messages)


async def test_bad_pin_responses_keep_metadata_and_raise():
    variants = [types.messages.MessagesNotModified(0), types.User(7),
                pins([message(peer=types.PeerChat(7))]),
                pins([message(peer=types.PeerChannel(8))]),
                pins([message(9), message(9)]), pins([message(0)]),
                pins([message()], count=-1), pins([message()], count=0),
                pins([message(9), message(8), message(7), message(6)])]
    for reply in variants:
        tg, f = setup(pin_response=reply)
        error = await fx.expect(GroupResponseError, profile(tg, 3))
        value = error.partial_result
        assert isinstance(value, GroupProfile) and value.about == 'Description'
        assert value.pins_status == 'failed' and value.pinned_messages == ()
        assert value.pins_total is value.pins_total_exact is value.pins_observed_at is None
        assert tg.get_account_health(222)['events'] == 0 and f.wire.closed


async def test_metadata_is_available_with_zero_budget():
    tg, f = setup(budget=True)
    f.budget.configure(222, 0)
    assert (await profile(tg)).about == 'Description'
    assert f.budget.status(222).used == 0


async def test_budget_charges_returned_slots_and_refuses_before_send():
    tg, f = setup(budget=True, pin_response=pins([message()]))
    assert (await profile(tg, 3)).pins_total == 1
    assert f.budget.status(222).used == 1 and f.budget.status(222).reserved == 0
    f.budget.configure(222, 2)
    before = len(g.requests(f, functions.messages.SearchRequest))
    error = await fx.expect(ReadBudgetExceeded, profile(tg, 3))
    assert error.partial_result.pins_status == 'failed'
    assert len(g.requests(f, functions.messages.SearchRequest)) == before
    assert f.budget.status(222).used == 1 and f.wire.closed


async def test_changed_owner_or_auth_blocks_pin_admission():
    for logged_out in (False, True):
        def change(wire, _):
            if logged_out:
                wire.script['GetUsersRequest'] = [h.RPCReply(401, 'AUTH_KEY_UNREGISTERED')]
            else:
                wire.account = 333
            return g.Reply(full())
        tg, f = setup(budget=True, responses={'GetFullChannelRequest': change})
        error = await fx.expect(AuthRequiredError if logged_out else AccountIdentityError, profile(tg, 3))
        assert error.partial_result.account_id == 222
        assert not g.requests(f, functions.messages.SearchRequest)
        assert f.budget.status(222).used == f.budget.status(333).used == 0


async def test_pin_source_denial_keeps_original_and_owned_event():
    events = []
    denial = h.RPCReply(400, 'CHANNEL_PRIVATE')
    tg, f = setup(cached=111, budget=True, callback=events.append,
                  responses={'SearchRequest': denial})
    error = await fx.expect(errors.ChannelPrivateError, profile(tg, 3))
    assert error is denial.error and error.partial_result.account_id == 222
    assert error.partial_result.about == 'Description' and f.budget.status(222).reserved == 3
    await h.deliveries(tg)
    assert len(events) == 1 and events[0]['request'] == 'messages.SearchRequest'
    assert events[0]['account']['user_id'] == 222 and events[0]['call'] == 'get_group_profile'
    assert tg.get_account_health(111) is None and tg._health.snapshot()['events'] == 0


async def test_pin_wait_propagates_without_sleep_or_retry():
    refusal = h.RPCReply(420, 'FLOOD_WAIT_30')
    tg, f = setup(responses={'SearchRequest': refusal})
    error = await fx.expect(errors.FloodWaitError, profile(tg, 3))
    assert error is refusal.error and error.seconds == 30
    assert error.partial_result.pins_status == 'failed'
    assert len(g.requests(f, functions.messages.SearchRequest)) == 1


async def test_local_pin_errors_stay_local_and_original():
    for error in (OSError('local/source transport'), ValueError('codec local'), TypeError('codec local')):
        tg, f = setup(responses={'SearchRequest': error})
        assert await fx.expect(type(error), profile(tg, 3)) is error
        assert error.partial_result.about == 'Description'
        assert tg.get_account_health(222)['events'] == 0 and f.wire.closed


async def test_full_read_failure_has_no_fabricated_profile():
    for error in (OSError('metadata transport'), h.RPCReply(400, 'CHANNEL_PRIVATE')):
        tg, f = setup(responses={'GetFullChannelRequest': error})
        kind = errors.ChannelPrivateError if isinstance(error, h.RPCReply) else OSError
        actual = await fx.expect(kind, profile(tg, 3))
        assert actual is (error.error if isinstance(error, h.RPCReply) else error)
        assert getattr(actual, 'partial_result', None) is None
        assert not g.requests(f, functions.messages.SearchRequest) and f.wire.closed


async def test_profile_and_pins_never_clear_history_denial():
    tg, f = setup(responses={'GetHistoryRequest': h.RPCReply(400, 'CHANNEL_PRIVATE')})
    assert (await tg.check_group_access('synthetic_room', account_id=222)).status == 'denied'
    await profile(tg)
    await profile(tg, 3)
    assert tg.get_account_health(222)['no_access']['synthetic_room']
    assert tg.get_account_health(222)['events'] == 1


async def test_heartbeat_progress_and_callback_failure_isolation():
    phases = []
    tg, _ = setup()
    await profile(tg, 1, heartbeat=phases.append)
    assert 'profile done' in phases and 'pins done' in phases
    assert phases.count('request') == phases.count('request done')
    for exception in (RuntimeError, asyncio.CancelledError, errors.ChannelPrivateError):
        def callback(_):
            raise exception('callback secret')
        value = await profile(tg, 1, heartbeat=callback)
        assert value.pins_status == 'complete' and tg.get_account_health(222)['events'] == 0
    async def later():
        pass
    assert (await profile(tg, heartbeat=lambda _: later())).pins_status == 'not_requested'


async def test_held_pin_has_no_fake_beats_and_cancellation_retains_profile():
    entered, release, beats = asyncio.Event(), asyncio.Event(), []
    tg, f = setup(budget=True, responses={'SearchRequest': g.Reply(
        pins([message()]), entered=entered, release=release)})
    task = asyncio.create_task(profile(tg, 3, heartbeat=beats.append))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        before = list(beats)
        await fx.turns(20)
        assert beats == before and not task.done()
        task.cancel()
        error = await fx.expect(asyncio.CancelledError, task)
        assert error.partial_result.about == 'Description'
        assert error.partial_result.pins_status == 'failed'
        assert f.wire.closed and f.budget.status(222).reserved == 3
        release.set()
        await fx.turns(10)
        assert beats == before and tg.get_account_health(222)['events'] == 0
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)


async def test_cleanup_cancellation_waits_for_sdk_and_stays_cancellation():
    closing, release = asyncio.Event(), asyncio.Event()
    def prepare(client):
        client._sender.close_entered, client._sender.close_release = closing, release
    tg, f = setup(prepare=prepare)
    task = asyncio.create_task(profile(tg, 3))
    try:
        await asyncio.wait_for(closing.wait(), 3)
        task.cancel()
        await fx.turns()
        task.cancel()
        await fx.turns()
        assert not task.done() and not f.wire.closed
        release.set()
        await fx.expect(asyncio.CancelledError, task)
        assert f.wire.closed
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)


async def test_cleanup_failure_preserves_result_and_original_failure():
    for failing in (False, True):
        source = OSError('source')
        def prepare(client):
            client._sender.close_error = RuntimeError('cleanup secret')
        tg, f = setup(prepare=prepare,
                      responses={'SearchRequest': source} if failing else None)
        if failing:
            error = await fx.expect(OSError, profile(tg, 3))
            assert error is source and error.partial_result.about == 'Description'
        else:
            assert (await profile(tg, 3)).pins_status == 'complete'
        assert f.wire.close_calls == 1 and tg.get_account_health(222)['events'] == 0


async def test_persistent_selection_and_legacy_state_do_not_change():
    tg, f = setup()
    selected = object()
    tg.current_group = selected
    await profile(tg, 3)
    assert tg.current_group is selected
    assert f.engine._primary_client is f.engine._pool is None
    assert tg._health.snapshot()['events'] == 0 and f.wire.closed


async def test_basic_pins_and_maximum_limit_are_bounded():
    tg, f = setup(entity=g.chat(), pin_response=pins([
        message(9, peer=types.PeerChat(7))], count=1))
    value = await profile(tg, 100)
    assert value.group.peer_id == -7 and value.pinned_messages[0].id == 9
    requests = g.requests(f, functions.messages.SearchRequest)
    assert len(requests) == 1 and requests[0].limit == 100
    assert isinstance(requests[0].peer, types.InputPeerChat)


async def test_refusing_exception_annotation_preserves_primary_error():
    class RefusingError(OSError):
        def __setattr__(self, name, value):
            if name == 'partial_result':
                raise RuntimeError('annotation refused')
            super().__setattr__(name, value)
    source = RefusingError('source failure')
    tg, f = setup(responses={'SearchRequest': source})
    assert await fx.expect(RefusingError, profile(tg, 3)) is source
    assert getattr(source, 'partial_result', None) is None
    assert tg.get_account_health(222)['events'] == 0 and f.wire.closed


async def main():
    assert telethon.__version__ == '1.45.0'
    tests = sorted((name, value) for name, value in globals().items()
                   if name.startswith('test_') and callable(value))
    failed = 0
    with tempfile.TemporaryDirectory(prefix='tgdata-profile-') as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient, 'start', side_effect=AssertionError('login forbidden')), \
         patch.object(telethon.TelegramClient, 'send_code_request', side_effect=AssertionError('code forbidden')), \
         patch.object(fx.Wire, 'send', g.send):
        fx.TMP = Path(tmp)
        for name, test in tests:
            try:
                await asyncio.wait_for(test(), 15)
                print('PASS', name, flush=True)
            except (Exception, asyncio.CancelledError):
                failed += 1
                print('FAIL', name, flush=True)
                traceback.print_exc()
            finally:
                for client in fx.CLIENTS:
                    client._sender.close_error = None
                    if client._sender.close_release is not None:
                        client._sender.close_release.set()
                    await client.disconnect()
                for tg in h.FACADES:
                    await tg.close()
                await asyncio.gather(*h.RPC_TASKS, return_exceptions=True)
                fx.CLIENTS.clear()
                h.FACADES.clear()
                h.RPC_TASKS.clear()
                g.TRACE.clear()
    print('{} passed; {} failed'.format(len(tests)-failed, failed), flush=True)
    return bool(failed)


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
