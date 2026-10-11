"""Public joining on actual Telethon1.45/SQLite, with synthetic wire and no network.

Normal cases use real TL decoding/error construction. Malformed Python values,
foreign error origins and local faults are explicitly injected validation cases.
"""
import asyncio
from dataclasses import FrozenInstanceError
import hashlib
import inspect
import json
from pathlib import Path
import socket
import sqlite3
import struct
import sys
import tempfile
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import telethon
from telethon import errors
from telethon.network.mtprotosender import MTProtoSender
from telethon.tl import functions, types
from telethon.tl.tlobject import TLRequest

from tgdata import TgData, JoinBudget, JoinBudgetConfigError, JoinBudgetStorageError, JoinBudgetExceeded
from tgdata import AuthRequiredError, GroupReferenceError, GroupResponseError
from tgdata.account_operation import AccountIdentityError
from tgdata.group_operations import GroupJoin
from tgdata.join_client import UnsupportedJoinRequest, _join_error_matches
from tgdata.smoke_tests import test_34_group_access as g

h, fx, DATE = g.h, g.fx, g.DATE
TRACE, TASKS = [], []
MUTATIONS = (functions.channels.JoinChannelRequest, functions.messages.ImportChatInviteRequest)


class Raw:
    """Explicit malformed/local-result injection; not a TL source qualification."""
    def __init__(self, value):
        self.value = value


class UserVector:
    def __bytes__(self):
        return struct.pack('<Ii', 0x1cb5c415, 1) + bytes(fx.user(222))


class DelayedRPC(h.RPCReply):
    def __init__(self, code, message, entered, release):
        super().__init__(code, message)
        self.entered, self.release = entered, release

    def send(self, wire, request, ordered=False):
        sender = MTProtoSender(wire.auth_key, loggers=wire.client._log)
        sender._user_connected = True
        sender._send_queue = []
        future = sender.send(request, ordered=ordered)
        state = sender._send_queue.pop()
        state.msg_id = 123
        sender._pending_state[123] = state

        async def deliver():
            self.entered.set()
            await self.release.wait()
            message = SimpleNamespace(obj=SimpleNamespace(req_msg_id=123,
                error=types.RpcError(self.code, self.message), body=None))
            await sender._handle_rpc_result(message)
            if not future.cancelled():
                self.error = future.exception()

        h.RPC_TASKS.append(asyncio.create_task(deliver()))
        return future


def send(wire, request, ordered=False):
    if isinstance(request, (list, tuple)):
        return [send(wire, item, ordered=ordered) for item in request]
    leaf = request
    while hasattr(leaf, 'query'):
        leaf = leaf.query
    name = type(leaf).__name__
    assert not isinstance(leaf, (functions.messages.GetDialogsRequest,
                                functions.messages.RequestChatJoinWebViewRequest)), 'unexpected follow-up'
    TRACE.append((wire, leaf))
    queue = wire.script.get(name)
    value = queue[0] if queue else wire.fixture.responses.get(name)
    if callable(value):
        value = value(wire, leaf)
    if isinstance(value, (g.Reply, h.RPCReply)):
        if queue:
            queue.pop(0)
        wire.calls.append(name)
        return value.send(wire, request, ordered=ordered)
    if isinstance(value, Raw):
        if queue:
            queue.pop(0)
        wire.calls.append(name)
        future = asyncio.get_running_loop().create_future()
        if isinstance(value.value, BaseException):
            future.set_exception(value.value)
        else:
            future.set_result(value.value)
        return future
    return h.ORIGINAL_SEND(wire, request, ordered=ordered)


def preview(**kwargs):
    return types.ChatInvite('Invite preview', types.PhotoEmpty(0), 2, 0,
                            channel=True, megagroup=True, **kwargs)


def acknowledged(updates=None, **kwargs):
    if updates is None:
        updates = types.Updates([], [], [], DATE, 1)
    return g.Reply(types.messages.ChatInviteJoinResultOk(updates), **kwargs)


def setup(*, limit=3, configured=True, enabled=True, entity=None, responses=None,
          prepare=None, seeds=(), callback=None, read_budget=True, **kwargs):
    entity = g.channel(left=True) if entity is None else entity
    defaults = dict(ResolveUsernameRequest=g.resolved(entity),
                    CheckChatInviteRequest=g.Reply(preview()),
                    JoinChannelRequest=acknowledged(), ImportChatInviteRequest=acknowledged())
    defaults.update(responses or {})
    kwargs.setdefault('cached', 111)
    f = fx.Fixture(budget=read_budget, responses=defaults, **kwargs)
    budget = JoinBudget(f.root / 'join.sqlite3', create=True, clock=lambda: 1000) if enabled else None
    if budget is not None and configured:
        for account in (111, 222, 333):
            budget.configure(account, limit)
    tg = TgData(str(f.config), health_callback=callback, account_label='joining account', join_budget=budget)
    tg.connection_engine = f.engine
    h.FACADES.append(tg)
    f.join_budget = budget
    original = f.engine._new_client

    def new_client(*args, **options):
        client = original(*args, **options)
        if seeds:
            client.session.process_entities(list(seeds))
        if prepare is not None:
            prepare(client)
        return client

    f.engine._new_client = new_client
    return tg, f, budget


def requests(f, cls=MUTATIONS):
    return [req for wire, req in TRACE if wire.fixture is f and isinstance(req, cls)]


def start(awaitable):
    task = asyncio.create_task(awaitable)
    TASKS.append(task)
    return task


async def test_public_signature_exports_and_constructor():
    import tgdata
    assert inspect.signature(TgData.join_group).parameters['account_id'].kind is inspect.Parameter.KEYWORD_ONLY
    for name in ('GroupJoin', 'UnsupportedJoinRequest'):
        assert name in tgdata.__all__ and getattr(tgdata, name) is globals()[name]
    tg, f, budget = setup()
    assert tg._join_budget is budget
    fx.refuses(TypeError, lambda: tg.join_group('synthetic_room'))
    value = await tg.join_group('synthetic_room', account_id=222)
    assert isinstance(value, GroupJoin) and value.status == 'joined'
    assert f.engine._primary_client is None and f.engine._pool is None


async def test_argument_and_budget_errors_precede_client_creation():
    tg, f, _ = setup()
    for target in (None, True, 0, 1.5, [], 't.me/+bad!', 'https://other.org/room', 2**63):
        await fx.expect(GroupReferenceError, tg.join_group(target, account_id=222))
    for owner in (None, True, False, 0, -1, '222', 222.0):
        await fx.expect(ValueError, tg.join_group('synthetic_room', account_id=owner))
    for budget in (None, object(), False, f.budget):
        tg._join_budget = budget
        await fx.expect(JoinBudgetConfigError, tg.join_group('synthetic_room', account_id=222))
    assert not f.clients


async def test_policy_is_required_before_group_work():
    tg, f, _ = setup(configured=False, entity=g.channel(left=False))
    await fx.expect(JoinBudgetConfigError, tg.join_group('synthetic_room', account_id=222))
    assert not requests(f, (functions.contacts.ResolveUsernameRequest,) + MUTATIONS)
    assert f.wire.closed and tg.get_account_health(222)['events'] == 0


async def test_invalid_and_async_policy_returns_fail_closed():
    for mode in ('value', 'foreign', 'async'):
        tg, f, budget = setup()
        foreign = budget.status(333)
        async def async_status(owner):
            return foreign
        replacement = async_status if mode == 'async' else lambda owner: foreign if mode == 'foreign' else None
        with patch.object(budget, 'status', replacement):
            await fx.expect(JoinBudgetConfigError, tg.join_group('synthetic_room', account_id=222))
        assert not requests(f, (functions.contacts.ResolveUsernameRequest,) + MUTATIONS)
        assert budget.status(222).used == 0


async def test_invalid_and_async_claim_returns_never_send():
    for value in (False, 0, object(), 'async'):
        tg, f, budget = setup()
        async def async_claim(owner):
            raise AssertionError('Invalid provider must not be awaited')
        replacement = async_claim if value == 'async' else lambda owner: value
        with patch.object(budget, '_claim', replacement):
            await fx.expect(JoinBudgetConfigError, tg.join_group('synthetic_room', account_id=222))
        assert not requests(f) and budget.status(222).used == 0


async def test_stale_cached_identity_does_not_own_claim_or_result():
    tg, f, budget = setup(cached=111)
    result = await tg.join_group('synthetic_room', account_id=222)
    assert result.account_id == 222 and f.clients[0]._self_id == 111
    assert (budget.status(111).used, budget.status(222).used) == (0, 1)
    assert tg.get_account_health(111) is None
    assert tg.get_account_health(222)['account']['user_id'] == 222


async def test_wrong_expected_account_prevents_all_group_requests():
    tg, f, budget = setup()
    error = await fx.expect(AccountIdentityError, tg.join_group('synthetic_room', account_id=111))
    assert error.actual_account_id == 222
    assert not requests(f, (functions.contacts.ResolveUsernameRequest,) + MUTATIONS)
    assert budget.status(111).used == budget.status(222).used == 0
    assert f.wire.closed


async def test_identity_change_after_lookup_prevents_claim_and_send():
    def changed(wire, request):
        wire.account = 333
        return g.resolved(g.channel(left=True))
    tg, f, budget = setup(responses={'ResolveUsernameRequest': changed})
    await fx.expect(AccountIdentityError, tg.join_group('synthetic_room', account_id=222))
    assert not requests(f) and budget.status(222).used == budget.status(333).used == 0
    assert f.wire.closed


async def test_missing_and_revoked_authentication_never_prompt():
    for logged_in in (False, True):
        tg, f, budget = setup(logged_in=logged_in,
            responses={'GetStateRequest': h.RPCReply(401, 'AUTH_KEY_UNREGISTERED')})
        error = await fx.expect(AuthRequiredError, tg.join_group('synthetic_room', account_id=222))
        assert error.first_login is (not logged_in)
        assert not requests(f) and budget.status(222).used == 0
        assert f.wire.closed


async def test_zero_cap_observes_membership_but_refuses_mutation():
    tg, f, budget = setup(limit=0, entity=g.channel(left=False))
    value = await tg.join_group('synthetic_room', account_id=222)
    assert value.status == 'already_joined' and value.member is True and not requests(f)
    f.responses['ResolveUsernameRequest'] = g.resolved(g.channel(left=True))
    await fx.expect(JoinBudgetExceeded, tg.join_group('synthetic_room', account_id=222))
    assert not requests(f) and budget.status(222).used == 0


async def test_known_payment_is_a_nonmutating_observation():
    tg, f, budget = setup(limit=0, responses={'CheckChatInviteRequest': g.Reply(preview(
        subscription_pricing=types.StarsSubscriptionPricing(2592000, 99)))})
    value = await tg.join_group('t.me/+Token', account_id=222)
    assert value.status == 'payment_required' and value.member is None
    assert not requests(f) and budget.status(222).used == 0


async def test_handle_join_uses_the_resolved_peer_and_zero_hash():
    tg, f, budget = setup(entity=g.channel(9, left=True, access_hash=0))
    result = await tg.join_group('HTTPS://T.ME/Synthetic_Room/', account_id=222)
    request = requests(f)[0]
    assert isinstance(request, functions.channels.JoinChannelRequest)
    assert (request.channel.channel_id, request.channel.access_hash) == (9, 0)
    assert result.target == 'synthetic_room' and result.group.peer_id == -1000000000009
    assert len(requests(f, functions.contacts.ResolveUsernameRequest)) == 1
    assert budget.status(222).used == 1 and f.budget.status(222).used == 0


async def test_invite_import_preserves_token_and_hides_it_from_result():
    token = 'CASE_sensitive_token'
    tg, f, budget = setup()
    result = await tg.join_group('https://t.me/+' + token, account_id=222)
    assert requests(f)[0].hash == token
    assert result.target == 'invite:' + hashlib.sha256(token.encode()).hexdigest()
    assert result.status == 'joined' and result.member is True
    assert result.group.id is None and result.group.peer_id is None
    assert token not in repr(result) and token not in json.dumps(result.to_dict())
    assert budget.status(222).used == 1 and f.budget.status(222).used == 0


async def test_invite_already_member_and_peek_routes():
    tg, f, budget = setup(limit=1, responses={'CheckChatInviteRequest': g.Reply(
        types.ChatInviteAlready(g.channel(9)))})
    assert (await tg.join_group('t.me/joinchat/Token', account_id=222)).status == 'already_joined'
    assert not requests(f) and budget.status(222).used == 0
    f.responses['CheckChatInviteRequest'] = g.Reply(types.ChatInvitePeek(g.channel(9, left=True), DATE))
    result = await tg.join_group('t.me/joinchat/Token', account_id=222)
    assert result.status == 'joined' and result.group.id == 9
    assert isinstance(requests(f)[0], functions.messages.ImportChatInviteRequest)


async def test_numeric_join_reuses_exact_cached_namespace():
    for target in (9, -1000000000009, '-1000000000009'):
        tg, f, budget = setup(seeds=[g.channel(9, access_hash=19)], responses={
            'GetChannelsRequest': g.Reply(types.messages.Chats([g.channel(9, left=True, access_hash=0)]))})
        result = await tg.join_group(target, account_id=222)
        assert result.group.peer_id == -1000000000009
        assert requests(f)[0].channel.access_hash == 0
        assert budget.status(222).used == 1


async def test_numeric_cache_absence_and_collision_do_not_guess():
    for seeds in ((), (g.chat(9), g.channel(9))):
        tg, f, budget = setup(seeds=seeds)
        await fx.expect(GroupReferenceError, tg.join_group(9, account_id=222))
        assert not requests(f) and budget.status(222).used == 0


async def test_basic_and_community_direct_mutations_require_invites():
    for entity in (g.chat(9, left=True), types.Community(9, 'Community', types.ChatPhotoEmpty(),
                                                       DATE, left=True, access_hash=0)):
        tg, f, budget = setup(entity=entity)
        await fx.expect(GroupReferenceError, tg.join_group('synthetic_room', account_id=222))
        assert not requests(f) and budget.status(222).used == 0


async def test_all_declared_updates_roots_are_acknowledgments():
    values = [types.Updates([], [], [], DATE, 1), types.UpdatesCombined([], [], [], DATE, 1, 1),
              types.UpdatesTooLong(), types.UpdateShort(types.UpdateConfig(), DATE),
              types.UpdateShortMessage(1, 222, 'synthetic', 1, 1, DATE),
              types.UpdateShortChatMessage(1, 222, 7, 'synthetic', 1, 1, DATE),
              types.UpdateShortSentMessage(1, 1, 1, DATE)]
    for value in values:
        tg, _, budget = setup(responses={'JoinChannelRequest': acknowledged(value)})
        result = await tg.join_group('synthetic_room', account_id=222)
        assert result.status == 'joined' and budget.status(222).used == 1


async def test_webview_is_portable_incomplete_data():
    bot = 2**53 + 99
    tg, f, budget = setup(responses={'JoinChannelRequest': g.Reply(
        types.messages.ChatInviteJoinResultWebView(bot, -2**63, []))})
    result = await tg.join_group('synthetic_room', account_id=222)
    assert result.status == 'interaction_required' and result.member is None
    value = json.loads(json.dumps(result.to_dict()))
    assert value['bot_id'] == bot and value['query_id'] == -2**63 and 'users' not in value
    assert len(requests(f)) == 1 and budget.status(222).used == 1


async def test_result_immutability_and_large_ids():
    ident, access_hash = 2**53 + 33, 2**63 - 1
    tg, f, _ = setup(entity=g.channel(ident, left=True, access_hash=access_hash))
    result = await tg.join_group('synthetic_room', account_id=222)
    fx.refuses(FrozenInstanceError, lambda: setattr(result, 'status', 'changed'))
    fx.refuses(FrozenInstanceError, lambda: setattr(result.group, 'id', 0))
    value = result.to_dict()
    assert json.loads(json.dumps(value))['group']['id'] == ident
    value['group']['id'] = 0
    assert result.to_dict()['group']['id'] == ident
    assert requests(f)[0].channel.access_hash == access_hash and 'access_hash' not in result.to_dict()['group']


async def test_source_outcomes_require_the_exact_mutation_on_both_paths():
    for target, method in [('synthetic_room', 'JoinChannelRequest'),
                           ('t.me/+token', 'ImportChatInviteRequest')]:
        for name, status in [('USER_ALREADY_PARTICIPANT', 'already_joined'),
                             ('INVITE_REQUEST_SENT', 'requested'),
                             ('STARS_PAYMENT_REQUIRED', 'payment_required')]:
            reply = h.RPCReply(400, name)
            tg, f, budget = setup(responses={method: reply})
            result = await tg.join_group(target, account_id=222)
            assert result.status == status
            assert result.member is (True if status == 'already_joined' else None)
            assert _join_error_matches(reply.error, requests(f)[0])
            assert budget.status(222).used == 1 and f.budget.status(222).used == 0


async def test_proof_and_metadata_rpc_names_are_not_join_outcomes():
    for phase in ('proof', 'metadata'):
        for name in ('USER_ALREADY_PARTICIPANT', 'INVITE_REQUEST_SENT', 'STARS_PAYMENT_REQUIRED'):
            reply = h.RPCReply(400, name)
            def resolved(wire, request):
                wire.script['GetUsersRequest'] = [reply]
                return g.resolved(g.channel(left=True))
            tg, f, budget = setup(responses={
                'ResolveUsernameRequest': resolved if phase == 'proof' else reply})
            error = await fx.expect(errors.RPCError, tg.join_group('synthetic_room', account_id=222))
            assert error is reply.error and not requests(f) and budget.status(222).used == 0


async def test_foreign_request_and_unreadable_origins_preserve_errors():
    for target, request in [('synthetic_room', functions.channels.JoinChannelRequest(types.InputChannel(7, 0))),
                            ('t.me/+token', functions.messages.ImportChatInviteRequest('token'))]:
        error = errors.InviteRequestSentError(request)
        tg, f, budget = setup(responses={type(request).__name__: Raw(error)})
        assert await fx.expect(type(error), tg.join_group(target, account_id=222)) is error
        assert not _join_error_matches(error, requests(f)[0]) and budget.status(222).used == 1
    class Broken:
        @property
        def request(self):
            raise ValueError('unreadable origin')
    assert not _join_error_matches(Broken(), request)
    class OldCancellation(Exception):
        pass
    class Cancelled:
        @property
        def request(self):
            raise OldCancellation()
    # Compatibility fixture only, not a native Python3.7 execution.
    with patch('tgdata.join_client.asyncio.CancelledError', OldCancellation):
        fx.refuses(OldCancellation, lambda: _join_error_matches(Cancelled(), request))


async def test_malformed_join_replies_remain_charged():
    for reply in (Raw(None), g.Reply(types.Updates([], [], [], DATE, 1)),
                  acknowledged(types.User(222)), Raw(object.__new__(types.messages.ChatInviteJoinResultOk))):
        tg, f, budget = setup(responses={'JoinChannelRequest': reply})
        await fx.expect(GroupResponseError, tg.join_group('synthetic_room', account_id=222))
        assert len(requests(f)) == budget.status(222).used == 1 and f.wire.closed
    for bot, query in [(False, 1), (0, 1), (-1, 1), (2**63, 1), (1, True),
                       (1, None), (1, 2**63), (1, -2**63 - 1)]:
        tg, f, budget = setup(responses={'JoinChannelRequest': Raw(
            types.messages.ChatInviteJoinResultWebView(bot, query, []))})
        await fx.expect(GroupResponseError, tg.join_group('synthetic_room', account_id=222))
        assert budget.status(222).used == 1
    tg, _, _ = setup(responses={'JoinChannelRequest': g.Reply(
        types.messages.ChatInviteJoinResultWebView(1, 0, []))})
    assert (await tg.join_group('synthetic_room', account_id=222)).query_id == 0


async def test_no_post_acknowledgment_enrichment_or_nested_cache_work():
    observed = []
    def prepare(client):
        original = client.session.process_entities
        def cache(value):
            observed.append(type(value).__name__)
            assert not isinstance(value, types.Updates), 'nested result explicitly cached'
            return original(value)
        client.session.process_entities = cache
    later = g.channel(9)
    later.title = 'Later title'
    nested = types.Updates([], [], [later], DATE, 1)
    tg, f, budget = setup(prepare=prepare, responses={'JoinChannelRequest': acknowledged(nested)})
    result = await tg.join_group('synthetic_room', account_id=222)
    assert result.group.id == 7 and result.group.title == 'Synthetic group'
    assert 'ChatInviteJoinResultOk' in observed
    assert not requests(f, functions.messages.GetHistoryRequest)
    assert len(requests(f, functions.contacts.ResolveUsernameRequest)) == 1
    assert budget.status(222).used == 1


async def test_unusable_and_malformed_lookup_never_mutates():
    answers = [g.resolved(g.channel(left=True, access_hash=None)),
               g.resolved(g.channel(left=True, min=True)),
               g.Reply(types.contacts.ResolvedPeer(types.PeerUser(222), [], [fx.user(222)])),
               g.Reply(types.User(222))]
    for reply in answers:
        tg, f, budget = setup(responses={'ResolveUsernameRequest': reply})
        await fx.expect((GroupReferenceError, GroupResponseError),
                        tg.join_group('synthetic_room', account_id=222))
        assert not requests(f) and budget.status(222).used == 0
    # Inherited Stage3 Low: malformed nested invite still fails before any join.
    tg, f, budget = setup(responses={'CheckChatInviteRequest': g.Reply(
        types.ChatInviteAlready(types.PeerChannel(7)))})
    await fx.expect((AttributeError, GroupResponseError), tg.join_group('t.me/+token', account_id=222))
    assert not requests(f) and budget.status(222).used == 0


async def test_original_source_failures_keep_identity_and_usage():
    for code, name in [(500, 'INTERNAL'), (420, 'FLOOD_WAIT_300'),
                        (401, 'AUTH_KEY_UNREGISTERED'), (400, 'CHANNEL_PRIVATE')]:
        reply = h.RPCReply(code, name)
        tg, f, budget = setup(responses={'JoinChannelRequest': reply})
        error = await fx.expect(errors.RPCError, tg.join_group('synthetic_room', account_id=222))
        assert error is reply.error and len(requests(f)) == budget.status(222).used == 1
        assert f.wire.closed and f.wire.policy_at_connect['requests'] == 0
    for error in (ConnectionError('wire failure'), OSError('local failure')):
        tg, f, budget = setup(responses={'JoinChannelRequest': Raw(error)})
        assert await fx.expect(type(error), tg.join_group('synthetic_room', account_id=222)) is error
        assert budget.status(222).used == 1 and f.wire.closed


async def test_cached_wait_and_controlled_retry_charge_only_actual_sends():
    def wait(client):
        client._flood_waited_requests[functions.channels.JoinChannelRequest.CONSTRUCTOR_ID] = time.time() + 300
    tg, f, budget = setup(prepare=wait)
    await fx.expect(errors.FloodWaitError, tg.join_group('synthetic_room', account_id=222))
    assert not requests(f) and budget.status(222).used == 0
    for cap in (1, 2):
        def retry(wire, request):
            # Probe-only override AFTER production connect policy has been observed.
            wire.client._request_retries = 1
            wire.script['JoinChannelRequest'] = [h.RPCReply(500, 'INTERNAL'), acknowledged()]
            return g.resolved(g.channel(left=True))
        tg, f, budget = setup(limit=cap, responses={'ResolveUsernameRequest': retry})
        if cap == 1:
            await fx.expect(JoinBudgetExceeded, tg.join_group('synthetic_room', account_id=222))
        else:
            assert (await tg.join_group('synthetic_room', account_id=222)).status == 'joined'
        assert len(requests(f)) == budget.status(222).used == cap
        assert f.wire.policy_at_connect['requests'] == 0


async def test_fresh_proof_committed_claim_and_enqueue_have_no_await_gap():
    events, yielded = [], []
    def reply(wire, request):
        assert events == ['verified', 'claimed'] and not yielded
        assert budget.status(222).used == 1  # separate real SQLite transaction
        events.append('enqueued')
        return acknowledged()
    def preflight(wire, request):
        def proof(wire, request):
            events.append('verified')
            return Raw([fx.user(wire.account)])
        wire.fixture.responses['GetUsersRequest'] = proof
        return g.resolved(g.channel(left=True))
    tg, f, budget = setup(responses={'ResolveUsernameRequest': preflight, 'JoinChannelRequest': reply})
    original = budget._claim
    def claim(owner):
        assert owner == 222 and events == ['verified']
        original(owner)
        events.append('claimed')
        asyncio.get_running_loop().call_soon(yielded.append, True)
    with patch.object(budget, '_claim', claim):
        await tg.join_group('synthetic_room', account_id=222)
    assert events == ['verified', 'claimed', 'enqueued'] and f.budget.status(222).used == 0


async def test_missing_corrupt_and_failing_ledger_never_send_or_report_rpc():
    for phase in ('before', 'after'):
        for damage in ('missing', 'corrupt', 'clock'):
            tg, f, budget = setup()
            def break_ledger():
                if damage == 'missing':
                    (f.root / 'join.sqlite3').unlink()
                elif damage == 'corrupt':
                    with sqlite3.connect(str(f.root / 'join.sqlite3')) as db:
                        db.execute('UPDATE tgdata_join_accounts SET last_clock=-1 WHERE account_id=222')
                else:
                    def bad_clock():
                        raise errors.ChannelPrivateError(functions.channels.JoinChannelRequest(types.InputChannel(7, 0)))
                    budget._clock = bad_clock
            if phase == 'before':
                break_ledger()
            else:
                def resolve(wire, request):
                    break_ledger()
                    return g.resolved(g.channel(left=True))
                f.responses['ResolveUsernameRequest'] = resolve
            kind = JoinBudgetConfigError if damage == 'clock' else JoinBudgetStorageError
            await fx.expect(kind, tg.join_group('synthetic_room', account_id=222))
            assert not requests(f) and tg.get_account_health(222)['events'] == 0
            if damage == 'missing':
                assert not (f.root / 'join.sqlite3').exists()


async def test_committed_claim_failure_does_not_refund_or_send():
    tg, f, budget = setup()
    original = budget._claim
    def invalid(owner):
        original(owner)
        return False
    with patch.object(budget, '_claim', invalid):
        await fx.expect(JoinBudgetConfigError, tg.join_group('synthetic_room', account_id=222))
    assert not requests(f) and budget.status(222).used == 1


async def test_sessions_proxy_and_device_settings_survive_composition():
    for use_store in (False, True):
        tg, f, budget = setup(store=fx.Store() if use_store else None, proxy=True)
        await tg.join_group('synthetic_room', account_id=222)
        client = f.clients[0]
        assert f.wire.proxy_at_connect and client._init_request.device_model == 'Stage 1 device'
        assert client._init_request.system_version == 'synthetic OS'
        assert f.wire.policy_at_connect == dict(flood=0, requests=0, connections=0,
            delay=0, reconnect=False, last_error=True, updates=False)
        assert bool(list(f.root.glob('*.session'))) is (not use_store)
        assert client._tgdata_join_budget is None and f.wire.closed
        assert budget.status(222).used == 1 and f.budget.status(222).used == 0


async def test_ordinary_clients_remain_unmarked_and_unguarded():
    _, f, budget = setup()
    client = f.engine._new_client()
    assert client._tgdata_join_budget is None
    await client.connect()
    request = functions.channels.JoinChannelRequest(types.InputChannel(7, 0))
    assert isinstance(await client(request), types.messages.ChatInviteJoinResultOk)
    values = await client([functions.users.GetUsersRequest([types.InputUserSelf()]),
                           functions.users.GetUsersRequest([types.InputUserSelf()])])
    assert len(values) == 2 and budget.status(222).used == 0
    await client.disconnect()


async def test_active_guard_rejects_batches_unknown_wrappers_and_families():
    tg, f, budget = setup(limit=4)
    async with tg._account_health_operation(222, 'guard_probe', 'synthetic_room') as (op, _):
        client = op.client
        client._tgdata_join_budget = budget
        request = functions.channels.JoinChannelRequest(types.InputChannel(7, 0))
        def generator():
            raise AssertionError('Batch must not be consumed')
            yield request
        class Unknown(TLRequest):
            SUBCLASS_OF_ID = types.messages.ChatInviteJoinResultOk.SUBCLASS_OF_ID
        depth = request
        for _ in range(9):
            depth = functions.InvokeWithoutUpdatesRequest(depth)
        cycle = functions.InvokeWithoutUpdatesRequest(request)
        cycle.query = cycle
        for value in ([request], (request,), generator(), Unknown(), depth, cycle,
                      functions.InvokeWithLayerRequest(229, request)):
            await fx.expect(UnsupportedJoinRequest, client(value))
        assert not requests(f) and budget.status(222).used == 0
        assert (await client(functions.users.GetUsersRequest([types.InputUserSelf()])))[0].id == 222
        await client(request)
        await client(functions.InvokeWithoutUpdatesRequest(
            functions.messages.ImportChatInviteRequest('token')))
        assert len(requests(f)) == budget.status(222).used == 2
        client._tgdata_join_budget = None


async def test_foreign_task_closed_and_foreign_client_cannot_claim():
    tg, f, budget = setup()
    request = functions.channels.JoinChannelRequest(types.InputChannel(7, 0))
    async with tg._account_health_operation(222, 'guard_probe', 'synthetic_room') as (op, _):
        client = op.client
        client._tgdata_join_budget = budget
        await fx.expect(RuntimeError, start(client(request)))
        other = f.engine._new_client()
        other._tgdata_join_budget, other._tgdata_account_operation = budget, op
        await fx.expect(UnsupportedJoinRequest, other(request))
    await fx.expect(RuntimeError, client(request))
    assert not requests(f) and budget.status(222).used == 0


async def test_cancellation_before_proof_and_after_enqueue():
    for phase, usage in [('proof', 0), ('enqueue', 1)]:
        entered, release = asyncio.Event(), asyncio.Event()
        def resolve(wire, request):
            wire.script['GetUsersRequest'] = [g.Reply(UserVector(), entered=entered, release=release)]
            return g.resolved(g.channel(left=True))
        responses = {'ResolveUsernameRequest': resolve} if phase == 'proof' else {
            'JoinChannelRequest': acknowledged(entered=entered, release=release)}
        tg, f, budget = setup(responses=responses)
        task = start(tg.join_group('synthetic_room', account_id=222))
        try:
            await entered.wait()
            task.cancel()
            await fx.expect(asyncio.CancelledError, task)
            assert len(requests(f)) == budget.status(222).used == usage
            assert f.wire.closed and f.wire.close_calls == 1
            assert f.clients[0]._tgdata_join_budget is None
        finally:
            release.set()


async def test_repeated_cancellation_waits_for_actual_cleanup():
    release = asyncio.Event()
    tg, f, budget = setup(prepare=lambda c: setattr(c._sender, 'close_release', release))
    task = start(tg.join_group('synthetic_room', account_id=222))
    try:
        while not f.clients:
            await asyncio.sleep(0)
        await f.wire.close_entered.wait()
        task.cancel()
        await fx.turns()
        task.cancel()
        await fx.turns()
        assert not task.done() and not f.wire.closed
        release.set()
        await fx.expect(asyncio.CancelledError, task)
        assert f.wire.closed and f.wire.close_calls == 1 and budget.status(222).used == 1
    finally:
        release.set()


async def test_cleanup_failure_preserves_primary_and_logs_only_type():
    for failed in (False, True):
        reply = h.RPCReply(400, 'CHANNEL_PRIVATE') if failed else acknowledged()
        tg, f, budget = setup(prepare=lambda c: setattr(c._sender, 'close_error', OSError('private-token')),
                              responses={'JoinChannelRequest': reply})
        with patch('tgdata.account_operation.logger.error') as log:
            if failed:
                assert await fx.expect(errors.ChannelPrivateError,
                    tg.join_group('synthetic_room', account_id=222)) is reply.error
            else:
                assert (await tg.join_group('synthetic_room', account_id=222)).status == 'joined'
        assert log.call_count == 1 and 'OSError' in str(log.call_args)
        assert 'private-token' not in str(log.call_args)
        assert f.wire.close_calls == 1 and not f.wire.closed  # attempt settled; closure failed
        assert budget.status(222).used == 1 and f.clients[0]._tgdata_join_budget is None


async def test_callback_failure_and_reentry_preserve_outcome_after_cleanup():
    received = []
    async def callback(event):
        assert f.clients[0]._sender.closed
        received.append(event)
        f.responses['JoinChannelRequest'] = acknowledged()
        result = await tg.join_group('synthetic_room', account_id=222)
        assert result.status == 'joined'
        raise RuntimeError('callback failed')
    reply = h.RPCReply(400, 'CHANNEL_PRIVATE')
    tg, f, budget = setup(callback=callback, responses={'JoinChannelRequest': reply})
    assert await fx.expect(errors.ChannelPrivateError,
        tg.join_group('synthetic_room', account_id=222)) is reply.error
    await h.deliveries(tg)
    assert len(received) == 1 and received[0]['account']['user_id'] == 222
    assert budget.status(222).used == 2 and all(c._sender.closed for c in f.clients)
    assert tg.get_account_health(222)['no_access']['synthetic_room']


async def test_join_results_never_confirm_history_readability():
    replies = [acknowledged(), h.RPCReply(400, 'USER_ALREADY_PARTICIPANT'),
               h.RPCReply(400, 'INVITE_REQUEST_SENT'), h.RPCReply(400, 'STARS_PAYMENT_REQUIRED'),
               g.Reply(types.messages.ChatInviteJoinResultWebView(1, 0, []))]
    for reply in replies:
        tg, f, budget = setup(responses={'JoinChannelRequest': reply})
        await h.fail(tg, f, group='synthetic_room', method='check_group_access')
        previous = tg.get_account_health(222)['no_access']['synthetic_room']
        await tg.join_group('synthetic_room', account_id=222)
        assert tg.get_account_health(222)['no_access']['synthetic_room'] == previous
        assert tg.get_account_health(111) is None and tg._health.snapshot()['events'] == 0
        assert budget.status(222).used == 1


async def test_source_request_and_account_recovery_keep_existing_rules():
    tg, f, budget = setup(limit=6, responses={'JoinChannelRequest': h.RPCReply(420, 'FLOOD_WAIT_300')})
    await fx.expect(errors.FloodWaitError, tg.join_group('synthetic_room', account_id=222))
    assert 'channels.JoinChannelRequest' in tg.get_account_health(222)['waiting']
    f.responses['ResolveUsernameRequest'] = g.resolved(g.channel(left=False))
    assert (await tg.join_group('synthetic_room', account_id=222)).status == 'already_joined'
    assert 'channels.JoinChannelRequest' in tg.get_account_health(222)['waiting']
    f.responses['ResolveUsernameRequest'] = g.resolved(g.channel(left=True))
    f.responses['JoinChannelRequest'] = acknowledged()
    await tg.join_group('synthetic_room', account_id=222)
    assert not tg.get_account_health(222)['waiting']
    f.responses['JoinChannelRequest'] = h.RPCReply(401, 'AUTH_KEY_UNREGISTERED')
    await fx.expect(errors.AuthKeyUnregisteredError, tg.join_group('synthetic_room', account_id=222))
    assert tg.get_account_health(222)['verdict'] == 'logged out'
    f.responses['JoinChannelRequest'] = acknowledged()
    await tg.join_group('synthetic_room', account_id=222)
    assert tg.get_account_health(222)['verdict'] == 'ok' and budget.status(222).used == 4


async def test_sdk_processing_failure_after_reply_is_preserved_and_charged():
    error = OSError('session processing failed')
    def prepare(client):
        original = client.session.process_entities
        def cache(value):
            if isinstance(value, types.messages.ChatInviteJoinResultOk):
                raise error
            return original(value)
        client.session.process_entities = cache
    tg, f, budget = setup(prepare=prepare)
    assert await fx.expect(OSError, tg.join_group('synthetic_room', account_id=222)) is error
    assert budget.status(222).used == 1 and len(requests(f)) == 1
    assert tg.get_account_health(222)['events'] == 0 and f.wire.closed


async def test_same_owner_overlap_competes_for_one_shared_slot():
    gates = [asyncio.Event(), asyncio.Event()]
    release = asyncio.Event()
    def resolve(wire, request):
        return g.resolved(g.channel(left=True)) if not gates else g.Reply(
            types.contacts.ResolvedPeer(types.PeerChannel(7), [g.channel(left=True)], []),
            entered=gates.pop(0), release=release)
    entered = list(gates)
    tg, f, budget = setup(limit=1, responses={'ResolveUsernameRequest': resolve})
    tasks = [start(tg.join_group('synthetic_room', account_id=222)) for _ in range(2)]
    try:
        await asyncio.gather(*(gate.wait() for gate in entered))
        release.set()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert sum(isinstance(x, GroupJoin) for x in results) == 1
        assert sum(isinstance(x, JoinBudgetExceeded) for x in results) == 1
        assert len(requests(f)) == budget.status(222).used == 1
        assert all(c._sender.closed for c in f.clients)
    finally:
        release.set()


async def test_different_owners_overlap_without_health_or_budget_leakage():
    a_entered, b_entered, a_release, b_release = (asyncio.Event() for _ in range(4))
    failure = DelayedRPC(400, 'CHANNEL_PRIVATE', b_entered, b_release)
    def reply(wire, request):
        return acknowledged(entered=a_entered, release=a_release) if wire.account == 222 else failure
    tg, f, budget = setup(accounts=[222, 333], responses={'JoinChannelRequest': reply})
    first = start(tg.join_group('synthetic_room', account_id=222))
    try:
        await a_entered.wait()
        second = start(tg.join_group('synthetic_room', account_id=333))
        await b_entered.wait()
        b_release.set()
        assert await fx.expect(errors.ChannelPrivateError, second) is failure.error
        assert not first.done()
        a_release.set()
        assert (await first).account_id == 222
        assert not tg.get_account_health(222)['no_access']
        assert tg.get_account_health(333)['no_access']['synthetic_room']
        assert budget.status(222).used == budget.status(333).used == 1
        assert budget.status(111).used == 0 and tg._health.snapshot()['events'] == 0
    finally:
        a_release.set()
        b_release.set()


async def cleanup():
    for client in fx.CLIENTS:
        if client._sender.close_release is not None:
            client._sender.close_release.set()
        client._sender.close_error = None
    for task in TASKS + h.RPC_TASKS:
        if not task.done():
            task.cancel()
    await asyncio.gather(*(TASKS + h.RPC_TASKS), return_exceptions=True)
    TASKS.clear()
    h.RPC_TASKS.clear()
    for client in fx.CLIENTS:
        await client.disconnect()
    fx.CLIENTS.clear()
    for tg in h.FACADES:
        await tg.close()
    h.FACADES.clear()
    TRACE.clear()


async def main():
    assert telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='tgdata-group-join-') as root, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient, 'start', side_effect=AssertionError('login forbidden')), \
         patch.object(telethon.TelegramClient, 'send_code_request', side_effect=AssertionError('code forbidden')), \
         patch.object(fx.Wire, 'send', send):
        fx.TMP = Path(root)
        tests = sorted((name, value) for name, value in globals().items()
                       if name.startswith('test_') and callable(value))
        if len(sys.argv) == 3 and sys.argv[1] == '--only':
            tests = [(name, test) for name, test in tests if sys.argv[2] in name]
        assert tests, 'No tests selected'
        failed = 0
        for name, test in tests:
            try:
                await asyncio.wait_for(test(), 30)
                print('PASS', name, flush=True)
            except Exception:
                failed += 1
                print('FAIL', name, flush=True)
                traceback.print_exc()
            finally:
                await cleanup()
        print('{} passed; {} failed'.format(len(tests) - failed, failed), flush=True)
        return bool(failed)


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
