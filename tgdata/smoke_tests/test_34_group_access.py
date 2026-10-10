"""Public group operations on Telethon 1.45.0, synthetic wire, sockets forbidden."""
import asyncio
from dataclasses import FrozenInstanceError
from datetime import timezone
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import telethon
from telethon import errors, utils
from telethon.network.mtprotosender import MTProtoSender
from telethon.tl import functions, types
from tgdata.smoke_tests import test_33_owned_health as h

fx = h.fx
DATE = fx.DATE
TRACE = []


class Reply:
    """Decode real TL bytes through the SDK sender/request state/result handler."""
    def __init__(self, value, *, entered=None, release=None):
        self.value, self.entered, self.release = value, entered, release

    def send(self, wire, request, ordered=False):
        sender = MTProtoSender(wire.auth_key, loggers=wire.client._log)
        sender._user_connected = True
        sender._send_queue = []
        future = sender.send(request, ordered=ordered)
        state = sender._send_queue.pop()
        state.msg_id = 123
        sender._pending_state[state.msg_id] = state

        async def deliver():
            if self.entered is not None:
                self.entered.set()
            if self.release is not None:
                await self.release.wait()
            message = SimpleNamespace(obj=SimpleNamespace(
                req_msg_id=state.msg_id, error=None, body=bytes(self.value)))
            await sender._handle_rpc_result(message)

        h.RPC_TASKS.append(asyncio.create_task(deliver()))
        return future


def send(wire, request, ordered=False):
    if isinstance(request, (list, tuple)):
        return [send(wire, item, ordered=ordered) for item in request]
    leaf = request
    while hasattr(leaf, 'query'):
        leaf = leaf.query
    assert not isinstance(leaf, (functions.channels.JoinChannelRequest,
                                functions.messages.ImportChatInviteRequest,
                                functions.messages.GetDialogsRequest)), 'mutation/dialog request'
    TRACE.append((wire, leaf))
    name = type(leaf).__name__
    queue = wire.script.get(name)
    reply = queue[0] if queue else wire.fixture.responses.get(name)
    if callable(reply):
        reply = reply(wire, leaf)
    if isinstance(reply, (Reply, h.RPCReply)):
        if queue:
            queue.pop(0)
        wire.calls.append(name)
        return reply.send(wire, request, ordered=ordered)
    return h.ORIGINAL_SEND(wire, request, ordered=ordered)


def channel(id=7, **kwargs):
    options = dict(megagroup=True, access_hash=0, username='synthetic_room')
    options.update(kwargs)
    return types.Channel(id, 'Synthetic group', types.ChatPhotoEmpty(), DATE, **options)


def chat(id=7, **kwargs):
    return types.Chat(id, 'Basic group', types.ChatPhotoEmpty(), 2, DATE, 1, **kwargs)


def resolved(entity=None, peer=None, chats=None):
    entity = channel() if entity is None else entity
    return Reply(types.contacts.ResolvedPeer(
        peer or (types.PeerChat(entity.id) if isinstance(entity, (types.Chat, types.ChatForbidden))
                 else types.PeerChannel(entity.id)),
        [entity] if chats is None else chats, []))


def history(peer=None, messages=None):
    if messages is None:
        messages = [types.MessageEmpty(1, peer_id=peer or types.PeerChannel(7))]
    return Reply(types.messages.Messages(messages=messages, topics=[], chats=[], users=[]))


def setup(*, entity=None, seeds=(), prepare=None, responses=None, callback=None, **kwargs):
    defaults = dict(ResolveUsernameRequest=resolved(entity), GetHistoryRequest=history())
    defaults.update(responses or {})
    tg, fixture = h.setup(callback, responses=defaults, **kwargs)
    original = fixture.engine._new_client

    def new_client(*args, **options):
        client = original(*args, **options)
        if seeds:
            client.session.process_entities(list(seeds))
        if prepare is not None:
            prepare(client)
        return client

    fixture.engine._new_client = new_client
    return tg, fixture


def requests(fixture, cls):
    return [request for wire, request in TRACE
            if wire.fixture is fixture and isinstance(request, cls)]


from tgdata import (TgData, GroupMetadata, GroupLookup, GroupAccess,
                    GroupReferenceError, GroupResponseError, AuthRequiredError,
                    ReadBudgetError, ReadBudgetExceeded, health)
from tgdata.account_operation import AccountIdentityError


async def test_reference_spellings_use_one_explicit_resolve():
    tg, f = setup()
    for value in ('synthetic_room', '@Synthetic_Room', ' Synthetic_Room ',
                  't.me/Synthetic_Room', 'https://t.me/Synthetic_Room/',
                  'http://telegram.me/Synthetic_Room', 'www.t.me/Synthetic_Room',
                  'https://www.telegram.me/Synthetic_Room'):
        lookup = await tg.lookup_group(value, account_id=222)
        assert lookup.target == 'synthetic_room' and lookup.account_id == 222
        assert f.wire.calls.count('ResolveUsernameRequest') == 1
        assert 'GetHistoryRequest' not in f.wire.calls and f.wire.closed
    assert all(r.username == 'synthetic_room' for r in requests(f, functions.contacts.ResolveUsernameRequest))


async def test_bad_references_never_open_config_or_client():
    tg = TgData('/missing/config.ini')
    values = (None, True, False, 0, 1.0, [], object(), types.PeerChannel(7), '', ' ',
              '@', '123abc', 'a' * 33, 'abc-def', 'a/b', 'me@example.com',
              'ftp://t.me/abc', 'tg://resolve?domain=abc', 'https://other.org/abc',
              'https://x@t.me/abc', 'https://t.me:443/abc', 'https://t.me/abc?',
              'https://t.me/abc#', 'https://t.me/abc/123', 'https://t.me/abc//',
              'https://t.me/+bad!', 'https://t.me/+', 'https://t.me/joinchat/',
              'https://t.me/+' + 'a' * 257, 'https://t.me/ab\nc',
              -2**63-1, 2**63, str(2**63), '0', '1' * 5000)
    with patch.object(tg.connection_engine, '_load_config', side_effect=AssertionError('config I/O')):
        for value in values:
            for method in (tg.lookup_group, tg.check_group_access):
                error = await fx.expect(GroupReferenceError, method(value, account_id=222))
                assert error.__suppress_context__
    assert not tg._account_health
    await tg.close()


async def test_literal_self_names_are_not_sdk_aliases():
    tg, f = setup(responses={'ResolveUsernameRequest': Reply(types.contacts.ResolvedPeer(
        types.PeerUser(222), [], [fx.user(222)]))})
    for name in ('me', 'self'):
        await fx.expect(GroupReferenceError, tg.lookup_group(name, account_id=222))
        assert requests(f, functions.contacts.ResolveUsernameRequest)[-1].username == name
    assert tg.get_account_health(222)['events'] == 0


async def test_expected_account_is_required_and_validated_before_client():
    tg, f = setup()
    for method in (tg.lookup_group, tg.check_group_access):
        fx.refuses(TypeError, lambda: method('synthetic_room'))
        for owner in (None, '222', 222.0, True, False, 0, -1):
            await fx.expect(ValueError, method('synthetic_room', account_id=owner))
    assert not f.clients


async def test_verified_owner_and_existing_factory_policy():
    tg, f = setup(cached=111, proxy=True, budget=True)
    result = await tg.check_group_access('@synthetic_room', account_id=222)
    assert result.account_id == result.lookup.account_id == 222
    assert f.clients[0]._self_id == 111
    assert tg.get_account_health(111) is None
    assert f.wire.policy_at_connect == dict(flood=0, requests=0, connections=0,
        delay=0, reconnect=False, last_error=True, updates=False)
    assert f.wire.proxy_at_connect == f.engine._load_config().proxy
    assert f.clients[0]._init_request.device_model == 'Stage 1 device'
    assert f.name in f.store and not list(f.root.glob('*.session'))


async def test_wrong_owner_prevents_every_group_request():
    tg, f = setup(cached=111)
    error = await fx.expect(AccountIdentityError,
                            tg.check_group_access('synthetic_room', account_id=111))
    assert error.actual_account_id == 222 and error.expected_account_id == 111
    assert not requests(f, functions.contacts.ResolveUsernameRequest)
    assert f.wire.closed and not tg._account_health


async def test_missing_authentication_never_logs_in():
    denial = h.RPCReply(401, 'AUTH_KEY_UNREGISTERED')
    tg, f = setup(logged_in=False, responses={'GetStateRequest': denial})
    error = await fx.expect(AuthRequiredError, tg.lookup_group('synthetic_room', account_id=222))
    assert error.first_login and f.wire.closed and not tg._account_health
    assert not requests(f, functions.contacts.ResolveUsernameRequest)


async def test_full_group_families_and_membership_hints():
    shapes = [(chat(), 'group', None),
              (channel(join_request=True), 'megagroup', True),
              (channel(megagroup=False, broadcast=True, left=True), 'channel', False),
              (channel(megagroup=False), 'unknown', False),
              (types.Community(7, 'Community', types.ChatPhotoEmpty(), DATE, access_hash=12),
               'community', None)]
    for entity, kind, approval in shapes:
        tg, f = setup(entity=entity)
        result = await tg.lookup_group('synthetic_room', account_id=222)
        assert result.group.kind == kind and result.group.id == 7
        assert result.group.peer_id == utils.get_peer_id(entity)
        assert result.member is (not bool(entity.left))
        assert result.request_needed is approval and result.requires_payment is None
        assert not requests(f, functions.messages.GetHistoryRequest)


async def test_resolved_user_wrong_missing_and_duplicate_entities():
    replies = [types.contacts.ResolvedPeer(types.PeerUser(7), [], [types.User(7)]),
               types.contacts.ResolvedPeer(types.PeerChannel(7), [], []),
               types.contacts.ResolvedPeer(types.PeerChannel(7), [channel(8)], []),
               types.contacts.ResolvedPeer(types.PeerChannel(7), [chat()], []),
               types.contacts.ResolvedPeer(types.PeerChannel(7), [channel(), channel()], [])]
    for index, reply in enumerate(replies):
        tg, f = setup(responses={'ResolveUsernameRequest': Reply(reply)})
        await fx.expect(GroupReferenceError if index == 0 else GroupResponseError,
                        tg.check_group_access('synthetic_room', account_id=222))
        assert not requests(f, functions.messages.GetHistoryRequest)
        assert f.wire.closed and tg.get_account_health(222)['events'] == 0


async def test_typed_match_ignores_other_group_namespace():
    tg, _ = setup(responses={'ResolveUsernameRequest': resolved(chats=[chat(), channel()])})
    lookup = await tg.lookup_group('synthetic_room', account_id=222)
    assert lookup.group.kind == 'megagroup' and lookup.group.peer_id == -1000000000007


async def test_empty_deactivated_and_migrated_groups_are_unavailable():
    for entity in (types.ChatEmpty(7), chat(deactivated=True),
                   chat(migrated_to=types.InputChannel(8, 9))):
        tg, f = setup(responses={'GetChatsRequest': Reply(types.messages.Chats([entity]))})
        await fx.expect(GroupReferenceError, tg.lookup_group(-7, account_id=222))
        assert f.wire.closed and not requests(f, functions.channels.GetChannelsRequest)


async def test_marked_basic_needs_no_cached_entity():
    tg, f = setup(responses={'GetChatsRequest': Reply(types.messages.Chats([chat()])),
                            'GetHistoryRequest': history(types.PeerChat(7))})
    for target in (-7, '-7'):
        value = await tg.check_group_access(target, account_id=222)
        assert value.readable and value.target == -7 and value.group.peer_id == -7
        assert requests(f, functions.messages.GetChatsRequest)[-1].id == [7]
        assert not requests(f, functions.contacts.ResolveUsernameRequest)


async def test_numeric_channels_preserve_large_and_zero_hashes():
    for access_hash in (0, 2**63-1, -2**63):
        for store in (None, fx.Store()):
            entity = channel(access_hash=access_hash)
            tg, f = setup(seeds=[entity], store=store,
                          responses={'GetChannelsRequest': Reply(types.messages.Chats([entity]))})
            result = await tg.check_group_access(-1000000000007, account_id=222)
            assert result.readable
            query = requests(f, functions.channels.GetChannelsRequest)[0]
            probe = requests(f, functions.messages.GetHistoryRequest)[0]
            assert query.id[0].access_hash == probe.peer.access_hash == access_hash
            assert bool(list(f.root.glob('*.session'))) == (store is None)


async def test_bare_numeric_ids_require_one_group_namespace():
    for seeds, accepted, basic in (([chat()], True, True), ([channel()], True, False),
                                   ([chat(), channel()], False, False),
                                   ([types.User(7, access_hash=4)], False, False),
                                   ([], False, False)):
        tg, f = setup(seeds=seeds, responses={
            'GetChatsRequest': Reply(types.messages.Chats([chat()])),
            'GetChannelsRequest': Reply(types.messages.Chats([channel()]))})
        if accepted:
            lookup = await tg.lookup_group('+7', account_id=222)
            assert lookup.target == 7 and lookup.group.peer_id == (-7 if basic else -1000000000007)
        else:
            await fx.expect(GroupReferenceError, tg.lookup_group(7, account_id=222))
            assert not requests(f, functions.channels.GetChannelsRequest)
            assert not requests(f, functions.messages.GetChatsRequest)


async def test_namespace_boundary_cannot_borrow_another_channel_row():
    for store in (None, fx.Store()):
        tg, f = setup(seeds=[channel()], store=store)
        await fx.expect(GroupReferenceError, tg.lookup_group(1000000000007, account_id=222))
        assert not requests(f, functions.messages.GetChatsRequest)
        assert not requests(f, functions.channels.GetChannelsRequest)
    edge = chat(10**12)
    tg, _ = setup(responses={'GetChatsRequest': Reply(types.messages.Chats([edge]))})
    assert (await tg.lookup_group(-10**12, account_id=222)).group.peer_id == -10**12
    large = channel(10**12+1)
    tg, _ = setup(seeds=[large], responses={'GetChannelsRequest': Reply(types.messages.Chats([large]))})
    assert (await tg.lookup_group(10**12+1, account_id=222)).group.id == 10**12+1


async def test_signed_extremes_are_bounded_and_bad_source_identity_refuses():
    tg, f = setup(store=None)
    for target in (-2**63, 2**63-1):
        await fx.expect(GroupReferenceError, tg.lookup_group(target, account_id=222))
    assert not requests(f, functions.channels.GetChannelsRequest)
    bad = chat(10**12+1)
    tg, _ = setup(responses={'ResolveUsernameRequest': Reply(types.contacts.ResolvedPeer(
        types.PeerChat(bad.id), [bad], []))})
    await fx.expect(GroupResponseError, tg.lookup_group('synthetic_room', account_id=222))


async def test_missing_hash_and_malformed_cache_rows_do_not_send():
    for row in (None, (-1000000000007, None), (-1000000000007, True),
                (-1000000000007, 2**63), (-1000000000008, 1), (1,), (True, 3)):
        def prepare(client):
            client.session.get_entity_rows_by_id = lambda *args, **kwargs: row
        tg, f = setup(prepare=prepare)
        await fx.expect(GroupReferenceError, tg.lookup_group(-1000000000007, account_id=222))
        assert not requests(f, functions.channels.GetChannelsRequest)


async def test_local_cache_exception_is_preserved_without_health():
    error = sqlite3.OperationalError('synthetic local cache failure')
    def prepare(client):
        original = client.session.get_entity_rows_by_id
        def broken(*args, **kwargs):
            if args[0] == -1000000000007 and kwargs.get('exact') is True:
                raise error
            return original(*args, **kwargs)
        client.session.get_entity_rows_by_id = broken
    tg, f = setup(prepare=prepare)
    assert await fx.expect(type(error), tg.check_group_access(-1000000000007, account_id=222)) is error
    assert tg.get_account_health(222)['events'] == 0 and f.wire.closed


async def test_invite_preview_is_not_a_peer_or_access_verdict():
    invite = types.ChatInvite('Preview', types.PhotoEmpty(0), 4, 0, channel=True,
                              megagroup=True, request_needed=True,
                              subscription_pricing=types.StarsSubscriptionPricing(2592000, 50))
    tg, f = setup(responses={'CheckChatInviteRequest': Reply(invite)})
    for target in ('https://t.me/+Case_sensitive', 'telegram.me/joinchat/Case_sensitive/'):
        result = await tg.check_group_access(target, account_id=222)
        assert result.status == 'unprobed' and result.readable is None and result.reason == 'NO_PEER'
        assert result.group.id is result.group.peer_id is result.group.username is None
        assert result.group.kind == 'megagroup' and result.member is False
        assert result.lookup.request_needed is result.lookup.requires_payment is True
        assert result.target.startswith('invite:') and len(result.target) == 71
        assert 'Case_sensitive' not in repr(result) + json.dumps(result.to_dict())
        assert requests(f, functions.messages.CheckChatInviteRequest)[-1].hash == 'Case_sensitive'
        assert not requests(f, functions.messages.GetHistoryRequest)


async def test_already_and_peek_invites_keep_membership_and_expiry():
    for wrapper, member, expires in ((types.ChatInviteAlready(channel(left=True)), True, None),
                                    (types.ChatInvitePeek(channel(left=False), DATE), False, DATE)):
        tg, f = setup(responses={'CheckChatInviteRequest': Reply(wrapper)})
        value = await tg.check_group_access('t.me/+invite_token', account_id=222)
        assert value.readable is True and value.member is member
        assert value.lookup.preview_expires_at == expires
        assert value.lookup.requires_payment is None
        converted = value.to_dict()['lookup']['preview_expires_at']
        assert converted == (expires.isoformat() if expires else None)
        assert len(requests(f, functions.messages.CheckChatInviteRequest)) == 1
        assert len(requests(f, functions.messages.GetHistoryRequest)) == 1


async def test_forbidden_min_and_missing_hash_are_qualified():
    cases = [(types.ChatForbidden(7, 'Forbidden'), None, True),
             (types.ChannelForbidden(7, 0, 'Forbidden', megagroup=True), None, True),
             (channel(min=True, left=True), None, False),
             (channel(access_hash=None), True, False),
             (types.CommunityForbidden(7, 'Forbidden', access_hash=0), None, True)]
    for entity, member, probe in cases:
        peer = types.PeerChat(7) if isinstance(entity, types.ChatForbidden) else types.PeerChannel(7)
        tg, f = setup(entity=entity, responses={'GetHistoryRequest': history(peer)})
        result = await tg.check_group_access('synthetic_room', account_id=222)
        assert result.member is member
        assert result.readable is (True if probe else None)
        assert bool(requests(f, functions.messages.GetHistoryRequest)) == probe
        assert result.lookup.requires_payment is None
        if isinstance(entity, (types.ChannelForbidden, types.CommunityForbidden)) or getattr(entity, 'min', False):
            assert result.lookup.request_needed is None


async def test_real_file_cache_hashless_community_error_stays_local():
    for store in (None, fx.Store()):
        tg, f = setup(store=store, entity=types.CommunityForbidden(7, 'Forbidden'))
        if store is None:
            await fx.expect(sqlite3.IntegrityError, tg.check_group_access('synthetic_room', account_id=222))
        else:
            result = await tg.check_group_access('synthetic_room', account_id=222)
            assert result.status == 'unprobed' and result.group.kind == 'community'
        assert f.wire.closed and tg.get_account_health(222)['events'] == 0
        assert not requests(f, functions.messages.GetHistoryRequest)


async def test_result_values_are_frozen_independent_and_json_ready():
    tg, _ = setup(responses={'CheckChatInviteRequest': Reply(types.ChatInvitePeek(channel(), DATE))})
    value = await tg.check_group_access('t.me/+private_token', account_id=222)
    assert isinstance(value, GroupAccess) and isinstance(value.lookup, GroupLookup)
    assert isinstance(value.group, GroupMetadata)
    for obj, name in ((value, 'status'), (value.lookup, 'member'), (value.group, 'title')):
        fx.refuses(FrozenInstanceError, lambda: setattr(obj, name, 'changed'))
    first = value.to_dict()
    first['lookup']['group']['title'] = 'changed'
    assert value.to_dict()['lookup']['group']['title'] == 'Synthetic group'
    assert 'access_hash' not in json.dumps(value.to_dict())
    assert set(value.to_dict()) == {'account_id', 'target', 'status', 'lookup', 'reason', 'readable'}
    assert value.lookup.preview_expires_at.tzinfo == timezone.utc


async def test_source_cache_self_sentinel_collision_preserves_setup_error():
    # The SDK's special self-row lookup for 0 also searches the marked channel-0
    # key, which equals Chat(10**12). This is a source setup error, not a denial.
    tg, f = setup(seeds=[chat(10**12)])
    await fx.expect(AttributeError, tg.lookup_group(10**12, account_id=222))
    assert tg.get_account_health(222) is None and f.wire.closed
    assert not requests(f, functions.messages.GetChatsRequest)


async def test_access_is_one_bounded_read_and_keeps_lookup():
    tg, f = setup(entity=channel(left=True, join_request=True))
    value = await tg.check_group_access('synthetic_room', account_id=222)
    assert value.status == 'readable' and value.readable is True and value.member is False
    assert value.lookup.request_needed is True
    assert len(requests(f, functions.contacts.ResolveUsernameRequest)) == 1
    probes = requests(f, functions.messages.GetHistoryRequest)
    assert len(probes) == 1
    req = probes[0]
    assert (req.offset_id, req.offset_date, req.add_offset, req.limit, req.max_id, req.min_id, req.hash) == (
        0, None, 0, 1, 0, 0, 0)
    assert isinstance(req.peer, types.InputPeerChannel) and req.peer.access_hash == 0


async def test_empty_history_and_supported_vectors_prove_access():
    variants = [types.messages.Messages([], [], [], []),
                types.messages.MessagesSlice(0, [], [], [], []),
                types.messages.ChannelMessages(1, 0, [], [], [], []),
                types.messages.Messages([types.MessageEmpty(1, None)], [], [], []),
                types.messages.Messages([types.Message(1, peer_id=types.PeerChannel(7),
                                            date=DATE, message='synthetic')], [], [], []),
                types.messages.Messages([types.MessageService(1, types.PeerChannel(7),
                                            DATE, action=types.MessageActionEmpty())], [], [], [])]
    for variant in variants:
        tg, _ = setup(responses={'GetHistoryRequest': Reply(variant)})
        result = await tg.check_group_access('synthetic_room', account_id=222)
        assert result.readable
        assert 'messages' not in result.to_dict()  # Probe content is not exposed.


async def test_bad_history_never_confirms_or_recovers():
    variants = [Reply(types.messages.MessagesNotModified(0)), Reply(types.User(9)),
                history(types.PeerChannel(8)), history(types.PeerChat(7)),
                history(types.PeerUser(7)), history(messages=[types.User(7)]),
                history(messages=[types.MessageEmpty(1, None), types.MessageEmpty(2, None)])]
    for variant in variants:
        tg, f = setup()
        f.responses['GetHistoryRequest'] = h.RPCReply(400, 'CHANNEL_PRIVATE')
        assert (await tg.check_group_access('synthetic_room', account_id=222)).status == 'denied'
        f.responses['GetHistoryRequest'] = variant
        await fx.expect(GroupResponseError, tg.check_group_access('synthetic_room', account_id=222))
        assert tg.get_account_health(222)['no_access']['synthetic_room']
        assert tg.get_account_health(222)['events'] == 1 and f.wire.closed


async def test_source_denial_during_resolution_has_no_invented_metadata():
    events = []
    denial = h.RPCReply(400, 'CHANNEL_PRIVATE')
    tg, f = setup(cached=111, callback=events.append, responses={'ResolveUsernameRequest': denial})
    result = await tg.check_group_access('@Synthetic_Room', account_id=222)
    assert result.status == 'denied' and result.readable is False
    assert result.lookup is result.group is result.member is None
    assert result.reason == 'CHANNEL_PRIVATE'
    assert not requests(f, functions.messages.GetHistoryRequest)
    await h.deliveries(tg)
    assert len(events) == 1 and events[0]['account']['user_id'] == 222
    assert events[0]['request'] == 'contacts.ResolveUsernameRequest'
    assert tg.get_account_health(111) is None and tg._health.snapshot()['events'] == 0


async def test_history_denial_keeps_complete_invite_lookup_and_safe_health_label():
    events = []
    tg, f = setup(callback=events.append, responses={
        'CheckChatInviteRequest': Reply(types.ChatInvitePeek(channel(), DATE)),
        'GetHistoryRequest': h.RPCReply(400, 'USER_BANNED_IN_CHANNEL')})
    result = await tg.check_group_access('t.me/+private_token', account_id=222)
    assert result.status == 'denied' and result.lookup.preview_expires_at == DATE
    assert result.member is False and result.group.id == 7
    await h.deliveries(tg)
    assert events[0]['group'] == result.target
    assert 'private_token' not in json.dumps(events) + json.dumps(result.to_dict())
    assert result.target in tg.get_account_health(222)['no_access']


async def test_lookup_source_denial_raises_original_and_records():
    denial = h.RPCReply(400, 'CHANNEL_PRIVATE')
    tg, f = setup(responses={'ResolveUsernameRequest': denial})
    error = await fx.expect(errors.ChannelPrivateError, tg.lookup_group('synthetic_room', account_id=222))
    assert error is denial.error and f.wire.closed
    assert tg.get_account_health(222)['no_access']['synthetic_room']


async def test_unclassified_wait_and_auth_rpcs_still_raise_original():
    cases = [(420, 'FLOOD_WAIT_120', errors.FloodWaitError, 'waiting'),
             (401, 'AUTH_KEY_UNREGISTERED', errors.AuthKeyUnregisteredError, 'logged out'),
             (400, 'USERNAME_NOT_OCCUPIED', errors.UsernameNotOccupiedError, 'ok'),
             (400, 'INVITE_HASH_EXPIRED', errors.InviteHashExpiredError, 'ok'),
             (403, 'CHAT_WRITE_FORBIDDEN', errors.ChatWriteForbiddenError, 'unclassified')]
    for code, text, kind, verdict in cases:
        reply = h.RPCReply(code, text)
        tg, f = setup(responses={'GetHistoryRequest': reply})
        error = await fx.expect(kind, tg.check_group_access('synthetic_room', account_id=222))
        assert error is reply.error and f.wire.closed
        snapshot = tg.get_account_health(222)
        if verdict == 'waiting':
            assert snapshot['waiting']['messages.GetHistoryRequest']['seconds'] == 120
            assert snapshot['verdict'] == 'ok'
        elif verdict == 'unclassified':
            assert snapshot['last_unclassified'] == text and snapshot['verdict'] == 'ok'
        else:
            assert snapshot['verdict'] == verdict


async def test_numeric_server_failure_preserves_sdk_error_and_policy():
    reply = h.RPCReply(500, 'RPC_CALL_FAIL')
    tg, f = setup(seeds=[channel()], responses={'GetChannelsRequest': reply})
    task, real_sleep, delays = asyncio.current_task(), asyncio.sleep, []
    async def sleep(seconds):
        if asyncio.current_task() is task:
            delays.append(seconds)
        else:
            await real_sleep(seconds)
    with patch('telethon.client.users.asyncio.sleep', sleep):
        error = await fx.expect(errors.RpcCallFailError,
                                tg.check_group_access(-1000000000007, account_id=222))
    assert error is reply.error and delays == [2]
    assert len(requests(f, functions.channels.GetChannelsRequest)) == 1
    assert f.wire.closed and tg.get_account_health(222)['events'] == 0


async def test_local_transport_and_native_errors_never_become_denials():
    for error in (OSError('synthetic transport'), TypeError('synthetic codec'),
                  ValueError('synthetic native'), KeyError('synthetic internal')):
        tg, f = setup(responses={'GetHistoryRequest': error})
        actual = await fx.expect(type(error), tg.check_group_access('synthetic_room', account_id=222))
        assert actual is error and f.wire.closed
        assert tg.get_account_health(222)['events'] == 0


async def test_nested_legacy_health_does_not_borrow_owned_errors_or_context():
    tg, _ = setup()
    async def bad_target():
        async with tg._health.call('legacy', 9):
            try:
                raise errors.ChannelPrivateError(fx.history())
            except errors.ChannelPrivateError:
                await tg.lookup_group('bad/input', account_id=222)
    await fx.expect(GroupReferenceError, bad_target())
    assert tg._health.snapshot()['events'] == 0
    async def wrong_owner():
        async with tg._health.call('legacy', 9):
            await tg.check_group_access('synthetic_room', account_id=111)
    await fx.expect(AccountIdentityError, wrong_owner())
    assert tg._health.snapshot()['events'] == 0


async def test_real_budget_metadata_cost_read_refund_and_pre_send_refusal():
    tg, f = setup(budget=True, cached=111)
    await tg.lookup_group('synthetic_room', account_id=222)
    assert f.budget.status(222).used == 0
    await tg.check_group_access('synthetic_room', account_id=222)
    assert f.budget.status(222).used == 1 and f.budget.status(111).used == 0
    f.responses['GetHistoryRequest'] = history(messages=[])
    assert (await tg.check_group_access('synthetic_room', account_id=222)).readable
    assert f.budget.status(222).used == 1
    f.budget.configure(222, 1)
    before = len(requests(f, functions.messages.GetHistoryRequest))
    await fx.expect(ReadBudgetExceeded, tg.check_group_access('synthetic_room', account_id=222))
    assert len(requests(f, functions.messages.GetHistoryRequest)) == before
    assert f.wire.closed and tg.get_account_health(222)['events'] == 0


async def test_budget_reverifies_owner_before_claim_or_send():
    for lost_auth in (False, True):
        def resolved_then_changed(wire, _):
            if lost_auth:
                wire.script['GetUsersRequest'] = [h.RPCReply(401, 'AUTH_KEY_UNREGISTERED')]
            else:
                wire.account = 333
            return resolved()
        tg, f = setup(budget=True, responses={'ResolveUsernameRequest': resolved_then_changed})
        await fx.expect(AuthRequiredError if lost_auth else AccountIdentityError,
                        tg.check_group_access('synthetic_room', account_id=222))
        assert f.budget.status(222).used == f.budget.status(333).used == 0
        assert not requests(f, functions.messages.GetHistoryRequest) and f.wire.closed
        assert not tg.get_account_health(222)['no_access']


async def test_failed_and_malformed_reads_keep_budget_error_semantics():
    for answer, kind in ((h.RPCReply(400, 'CHANNEL_PRIVATE'), None),
                         (Reply(types.User(7)), ReadBudgetError),
                         (history(messages=[types.MessageEmpty(1, None), types.MessageEmpty(2, None)]), ReadBudgetError),
                         (Reply(types.messages.MessagesNotModified(0)), GroupResponseError)):
        tg, f = setup(budget=True, responses={'GetHistoryRequest': answer})
        if kind is None:
            assert (await tg.check_group_access('synthetic_room', account_id=222)).status == 'denied'
        else:
            await fx.expect(kind, tg.check_group_access('synthetic_room', account_id=222))
        assert tg.get_account_health(222)['events'] == (1 if kind is None else 0)
        assert f.budget.status(222).used == (0 if isinstance(answer, Reply) and
            isinstance(answer.value, types.messages.MessagesNotModified) else
            2 if isinstance(answer, Reply) and hasattr(answer.value, 'messages') and
            len(answer.value.messages) == 2 else 1)


async def test_only_valid_history_recovers_prior_group_denial():
    tg, f = setup(responses={'GetHistoryRequest': h.RPCReply(400, 'CHANNEL_PRIVATE')})
    assert (await tg.check_group_access('synthetic_room', account_id=222)).status == 'denied'
    await tg.lookup_group('synthetic_room', account_id=222)
    assert tg.get_account_health(222)['no_access']['synthetic_room']
    f.responses['ResolveUsernameRequest'] = resolved(channel(min=True))
    assert (await tg.check_group_access('synthetic_room', account_id=222)).status == 'unprobed'
    assert tg.get_account_health(222)['no_access']['synthetic_room']
    f.responses['ResolveUsernameRequest'] = resolved()
    f.responses['GetHistoryRequest'] = history()
    assert (await tg.check_group_access('synthetic_room', account_id=222)).readable
    assert not tg.get_account_health(222)['no_access']
    assert tg.get_account_health(222)['events'] == 2


async def test_older_read_cannot_clear_a_newer_denial():
    entered, release = asyncio.Event(), asyncio.Event()
    tg, f = setup(responses={'GetHistoryRequest': Reply(history().value, entered=entered, release=release)})
    older = asyncio.create_task(tg.check_group_access('synthetic_room', account_id=222))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        f.responses['GetHistoryRequest'] = h.RPCReply(400, 'CHANNEL_PRIVATE')
        assert (await tg.check_group_access('synthetic_room', account_id=222)).status == 'denied'
        release.set()
        assert (await older).readable
        snapshot = tg.get_account_health(222)
        assert snapshot['no_access']['synthetic_room'] and snapshot['events'] == 1
    finally:
        release.set()
        await asyncio.gather(older, return_exceptions=True)


async def test_overlapping_accounts_keep_independent_source_health():
    entered, release = asyncio.Event(), asyncio.Event()
    tg, f = setup(accounts=[222, 333], cached=111,
                  responses={'GetHistoryRequest': Reply(history().value, entered=entered, release=release)})
    older = asyncio.create_task(tg.check_group_access('synthetic_room', account_id=222))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        f.responses['GetHistoryRequest'] = h.RPCReply(400, 'CHANNEL_PRIVATE')
        newer = await tg.check_group_access('synthetic_room', account_id=333)
        assert newer.account_id == 333 and newer.status == 'denied'
        release.set()
        assert (await older).account_id == 222
        assert not tg.get_account_health(222)['no_access']
        assert tg.get_account_health(333)['no_access']['synthetic_room']
        assert tg.get_account_health(111) is None
    finally:
        release.set()
        await asyncio.gather(older, return_exceptions=True)


async def test_cancelled_read_keeps_denial_and_reserved_budget():
    tg, f = setup(budget=True, responses={'GetHistoryRequest': h.RPCReply(400, 'CHANNEL_PRIVATE')})
    await tg.check_group_access('synthetic_room', account_id=222)
    entered, release = asyncio.Event(), asyncio.Event()
    f.responses['GetHistoryRequest'] = Reply(history().value, entered=entered, release=release)
    task = asyncio.create_task(tg.check_group_access('synthetic_room', account_id=222))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        task.cancel()
        await fx.expect(asyncio.CancelledError, task)
        assert f.wire.closed and tg.get_account_health(222)['no_access']['synthetic_room']
        assert f.budget.status(222).used == 2
        release.set()
        await fx.turns()
        assert tg.get_account_health(222)['events'] == 1
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)


async def test_notifications_wait_until_delayed_cleanup_settles():
    events, closing, release = [], asyncio.Event(), asyncio.Event()
    def prepare(client):
        client._sender.close_entered = closing
        client._sender.close_release = release
    tg, f = setup(callback=events.append, prepare=prepare,
                  responses={'GetHistoryRequest': h.RPCReply(400, 'CHANNEL_PRIVATE')})
    task = asyncio.create_task(tg.check_group_access('synthetic_room', account_id=222))
    try:
        await asyncio.wait_for(closing.wait(), 3)
        assert not task.done() and not events
        assert tg.get_account_health(222)['no_access']['synthetic_room']
        release.set()
        assert (await task).status == 'denied'
        await h.deliveries(tg)
        assert f.wire.closed and len(events) == 1
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)


async def test_cleanup_cancellation_preserves_completed_read_evidence():
    tg, f = setup(responses={'GetHistoryRequest': h.RPCReply(400, 'CHANNEL_PRIVATE')})
    await tg.check_group_access('synthetic_room', account_id=222)
    closing, release = asyncio.Event(), asyncio.Event()
    def good_then_hold_close(wire, _):
        wire.close_entered, wire.close_release = closing, release
        return history()
    f.responses['GetHistoryRequest'] = good_then_hold_close
    task = asyncio.create_task(tg.check_group_access('synthetic_room', account_id=222))
    try:
        await asyncio.wait_for(closing.wait(), 3)
        assert not tg.get_account_health(222)['no_access']
        task.cancel()
        await fx.turns()
        assert not task.done()
        task.cancel()
        release.set()
        await fx.expect(asyncio.CancelledError, task)
        assert f.wire.closed and not tg.get_account_health(222)['no_access']
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)


async def test_failed_cleanup_never_replaces_success_or_source_exception():
    for failed_work in (False, True):
        error = OSError('synthetic source failure')
        def prepare(client):
            client._sender.close_error = RuntimeError('synthetic cleanup secret')
        tg, f = setup(prepare=prepare, responses={'GetHistoryRequest': error if failed_work else history()})
        try:
            if failed_work:
                assert await fx.expect(OSError, tg.check_group_access('synthetic_room', account_id=222)) is error
            else:
                assert (await tg.check_group_access('synthetic_room', account_id=222)).readable
            assert f.wire.close_calls == 1 and tg.get_account_health(222)['events'] == 0
        finally:
            f.wire.close_error = None


async def test_callback_errors_and_callback_cancellation_preserve_result():
    for asynchronous in (False, True):
        for error_type in (ValueError, asyncio.CancelledError):
            events = []
            def callback(event):
                assert f.wire.closed
                events.append(event)
                raise error_type('synthetic callback')
            async def async_callback(event):
                callback(event)
            tg, f = setup(callback=async_callback if asynchronous else callback,
                          responses={'GetHistoryRequest': h.RPCReply(400, 'CHANNEL_PRIVATE')})
            assert (await tg.check_group_access('synthetic_room', account_id=222)).status == 'denied'
            await h.deliveries(tg)
            assert len(events) == 1 and tg.get_account_health(222)['events'] == 1


async def test_closed_handle_cannot_confirm_access():
    def invalidate(wire, _):
        # Fault injection of a terminal handle; does not supply a positive verdict.
        wire.client._tgdata_account_operation._close()
        return history()
    tg, f = setup(responses={'GetHistoryRequest': invalidate})
    await fx.expect(RuntimeError, tg.check_group_access('synthetic_room', account_id=222))
    assert f.wire.closed and tg.get_account_health(222)['events'] == 0


async def test_persistent_selection_and_legacy_health_are_unchanged():
    tg, f = setup()
    group = object()
    tg.current_group = group
    await tg.lookup_group('synthetic_room', account_id=222)
    await tg.check_group_access('synthetic_room', account_id=222)
    assert tg.current_group is group
    assert f.engine._primary_client is f.engine._pool is None
    assert tg._health.snapshot()['events'] == 0
    assert all(client._sender.closed for client in f.clients)


async def test_incomplete_and_wrong_metadata_never_recover():
    malformed = types.contacts.ResolvedPeer(types.PeerChannel(7), [channel()], [])
    malformed.chats = None
    for answer in (Reply(types.User(7)), malformed):
        tg, f = setup(responses={'GetHistoryRequest': h.RPCReply(400, 'CHANNEL_PRIVATE')})
        await tg.check_group_access('synthetic_room', account_id=222)
        f.responses['ResolveUsernameRequest'] = answer
        await fx.expect(GroupResponseError, tg.check_group_access('synthetic_room', account_id=222))
        assert tg.get_account_health(222)['no_access']['synthetic_room']
        assert tg.get_account_health(222)['events'] == 1


async def test_plain_invite_absent_flags_are_actual_negative_hints():
    tg, _ = setup(responses={'CheckChatInviteRequest': Reply(
        types.ChatInvite('Basic preview', types.PhotoEmpty(0), 0, 0))})
    result = await tg.lookup_group('t.me/+token', account_id=222)
    assert result.group.kind == 'group' and result.member is False
    assert result.request_needed is result.requires_payment is False
    assert result.preview_expires_at is None



async def fixture_probe():
    tg, fixture = setup(cached=111, budget=True)
    async with tg._account_health_operation(222, 'fixture_probe', 'synthetic_room') as (op, _):
        value = await op.client(functions.contacts.ResolveUsernameRequest('synthetic_room'))
        assert value.chats[0].access_hash == 0 and op.account_id == 222
        assert fixture.budget.status(222).used == 0
    assert fixture.wire.closed


async def main():
    assert telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='tgdata-group-access-') as root, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient, 'start', side_effect=AssertionError('login forbidden')), \
         patch.object(telethon.TelegramClient, 'send_code_request', side_effect=AssertionError('code forbidden')), \
         patch.object(fx.Wire, 'send', send):
        fx.TMP = Path(root)
        tests = sorted((name, value) for name, value in globals().items()
                       if name.startswith('test_') and callable(value))
        if not tests:
            tests = [('fixture_probe', fixture_probe)]
        failed = 0
        try:
            for name, test in tests:
                try:
                    await test()
                    print('PASS', name, flush=True)
                except Exception:
                    failed += 1
                    print('FAIL', name, flush=True)
                    traceback.print_exc()
        finally:
            for client in fx.CLIENTS:
                release = client._sender.close_release
                if release is not None:
                    release.set()
                await client.disconnect()
            for tg in h.FACADES:
                await tg.close()
            await asyncio.gather(*h.RPC_TASKS, return_exceptions=True)
        print('{} passed; {} failed'.format(len(tests) - failed, failed), flush=True)
        return bool(failed)


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
