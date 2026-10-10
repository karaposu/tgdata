"""Stage5 inquiry: actual Telethon1.45 composition, synthetic wire, no network.

The temporary probe mixin tests a candidate admission seam; it is not product code.
"""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import telethon
from telethon import errors
from telethon.network.mtprotosender import MTProtoSender
from telethon.tl import functions, types
from tgdata import JoinBudget
from tgdata import connection_engine as connection
from tgdata.account_operation import AccountIdentityError
from tgdata.group_operations import _parse_target, _resolve
from tgdata.smoke_tests import test_34_group_access as g

h, fx = g.h, g.fx
JOINS = (functions.channels.JoinChannelRequest, functions.messages.ImportChatInviteRequest)
TRACE = []
ORIGINAL_CLASS = connection._client_class


def wire_send(wire, request, ordered=False):
    leaf = request
    while hasattr(leaf, 'query'):
        leaf = leaf.query
    name = type(leaf).__name__
    TRACE.append(('send', name))
    queue = wire.script.get(name)
    value = queue[0] if queue else wire.fixture.responses.get(name)
    if isinstance(value, (g.Reply, h.RPCReply)):
        if queue:
            queue.pop(0)
        wire.calls.append(name)
        return value.send(wire, request, ordered=ordered)
    return h.ORIGINAL_SEND(wire, request, ordered=ordered)


class ProbeSender:
    def __init__(self, sender, client, budget):
        self.sender, self.client, self.budget = sender, client, budget

    def __getattr__(self, name):
        return getattr(self.sender, name)

    def send(self, request, ordered=False):
        async def admitted():
            owner = await self.client._tgdata_account_operation.verify_account()
            TRACE.append(('verified', owner))
            self.budget._claim(owner)
            TRACE.append(('claimed', owner))
            pending = self.sender.send(request, ordered=ordered)
            return await pending
        return admitted()


class ProbeMixin:
    async def _call(self, sender, request, ordered=False, flood_sleep_threshold=None):
        budget = getattr(self, '_stage5_probe_budget', None)
        if budget is not None and isinstance(request, JOINS):
            sender = ProbeSender(sender, self, budget)
        return await super()._call(sender, request, ordered=ordered,
                                   flood_sleep_threshold=flood_sleep_threshold)


def setup():
    tg, fixture = h.setup(cached=111, budget=True)
    budget = JoinBudget(fixture.root / 'join.sqlite3', create=True, clock=lambda: 1000)
    budget.configure(111, 5)
    budget.configure(222, 5)
    return tg, fixture, budget


def ok_reply(chat_id=9):
    return g.Reply(types.messages.ChatInviteJoinResultOk(types.Updates(
        [], [], [g.channel(chat_id, access_hash=19)], fx.DATE, 1)))


async def result_and_cache():
    tg, fixture, budget = setup()
    async with tg._account_health_operation(222, 'join_probe', 'synthetic') as (op, _):
        client = op.client
        client._stage5_probe_budget = budget
        fixture.wire.script['JoinChannelRequest'] = [ok_reply()]
        TRACE.clear()
        result = await client(functions.channels.JoinChannelRequest(types.InputChannel(9, 19)))
        assert isinstance(result, types.messages.ChatInviteJoinResultOk)
        # The actual SDK processes the outer wrapper, not its nested Updates.
        before = client.session.get_entity_rows_by_id(-1000000000009, exact=True)
        assert before is None
        client.session.process_entities(result.updates)
        after = client.session.get_entity_rows_by_id(-1000000000009, exact=True)
        assert after == (-1000000000009, 19)
        assert TRACE[-3:] == [('verified', 222), ('claimed', 222), ('send', 'JoinChannelRequest')]
        output = dict(result=type(result).__name__, outer_cached_room=before,
                      explicit_nested_cache=list(after), admission_order=TRACE[-3:])
    assert fixture.wire.closed
    assert budget.status(111).used == 0 and budget.status(222).used == 1
    output.update(owner=222, cached_identity=111, join_used=1, read_used=fixture.budget.status(222).used)
    return output


async def source_outcomes():
    output = []
    for payload in (g.Reply(types.messages.ChatInviteJoinResultWebView(44, -7, [])),
                    h.RPCReply(400, 'INVITE_REQUEST_SENT'),
                    h.RPCReply(400, 'USER_ALREADY_PARTICIPANT'),
                    h.RPCReply(400, 'STARS_PAYMENT_REQUIRED')):
        tg, fixture, budget = setup()
        async with tg._account_health_operation(222, 'join_probe', 'synthetic') as (op, _):
            op.client._stage5_probe_budget = budget
            fixture.wire.script['ImportChatInviteRequest'] = [payload]
            try:
                result = await op.client(functions.messages.ImportChatInviteRequest('synthetic_token'))
            except errors.RPCError as error:
                assert error is payload.error
                name = h.health.telegram_error_name(error)
                kind = type(error).__name__
            else:
                name, kind = 'interaction', type(result).__name__
                assert (result.bot_id, result.query_id) == (44, -7)
        assert budget.status(222).used == 1
        output.append(dict(outcome=name, type=kind, charged=1))
    return output


async def identity_change():
    tg, fixture, budget = setup()
    async with tg._account_health_operation(222, 'join_probe', 'synthetic') as (op, _):
        op.client._stage5_probe_budget = budget
        fixture.wire.account = 333
        TRACE.clear()
        error = await fx.expect(AccountIdentityError, op.client(
            functions.messages.ImportChatInviteRequest('synthetic_token')))
        assert error.actual_account_id == 333
        assert ('send', 'ImportChatInviteRequest') not in TRACE
    assert budget.status(222).used == 0
    return dict(expected=222, actual=333, join_sends=0, charged=0, closed=fixture.wire.closed)


async def cached_wait_and_retry():
    tg, fixture, budget = setup()
    async with tg._account_health_operation(222, 'join_probe', 'synthetic') as (op, _):
        client = op.client
        client._stage5_probe_budget = budget
        import time
        client._flood_waited_requests[functions.channels.JoinChannelRequest.CONSTRUCTOR_ID] = time.time() + 300
        await fx.expect(errors.FloodWaitError, client(
            functions.channels.JoinChannelRequest(types.InputChannel(9, 19))))
        assert budget.status(222).used == 0
        client._flood_waited_requests.clear()
        # Probe-only stress: production owned-operation policy remains zero retries.
        client._request_retries = 1
        fixture.wire.script['JoinChannelRequest'] = [h.RPCReply(500, 'INTERNAL'), ok_reply()]
        result = await client(functions.channels.JoinChannelRequest(types.InputChannel(9, 19)))
        assert isinstance(result, types.messages.ChatInviteJoinResultOk)
        client._request_retries = 0
    assert budget.status(222).used == 2
    return dict(cached_wait_charged=0, probe_retry_sends=2, charged=2,
                production_retry_policy=0)


async def exhausted_rpc():
    tg, fixture, budget = setup()
    reply = h.RPCReply(500, 'INTERNAL')
    try:
        async with tg._account_health_operation(222, 'join_probe', 'synthetic') as (op, _):
            op.client._stage5_probe_budget = budget
            fixture.wire.script['ImportChatInviteRequest'] = [reply]
            await op.client(functions.messages.ImportChatInviteRequest('synthetic_token'))
    except errors.ServerError as error:
        assert error is reply.error
        result = type(error).__name__
    else:
        raise AssertionError('Expected original server error')
    assert budget.status(222).used == 1 and fixture.wire.closed
    return dict(error=result, original_identity=True, charged=1, closed=True)


async def transport_requeue():
    tg, fixture, _ = setup()
    async with tg._account_health_operation(222, 'join_probe') as (op, _):
        sender = MTProtoSender(fixture.wire.auth_key, loggers=op.client._log)
        sender._user_connected = True
        sender._send_queue = []
        future = sender.send(functions.channels.JoinChannelRequest(types.InputChannel(9, 19)))
        state = sender._send_queue.pop()
        state.msg_id = 123
        sender._pending_state[123] = state
        bad = SimpleNamespace(obj=types.BadServerSalt(123, 1, 48, 999))
        await sender._handle_bad_server_salt(bad)
        assert sender._send_queue == [state] and state.future is future
        future.cancel()
    return dict(protocol_correction='bad_server_salt', same_request_state=True,
                additional_application_send=0)


async def numeric_route():
    tg, fixture, budget = setup()
    async with tg._account_health_operation(222, 'join_probe', -1000000000009) as (op, _):
        op.client._stage5_probe_budget = budget
        op.client.session.process_entities([g.channel(9, access_hash=19, left=True)])
        fixture.wire.script['GetChannelsRequest'] = [g.Reply(types.messages.Chats(
            [g.channel(9, access_hash=0, left=True)]))]
        lookup, peer = await _resolve(op, _parse_target(-1000000000009))
        assert lookup.group.peer_id == -1000000000009 and lookup.member is False
        assert (peer.channel_id, peer.access_hash) == (9, 0)
        fixture.wire.script['JoinChannelRequest'] = [ok_reply()]
        reply = await op.client(functions.channels.JoinChannelRequest(
            types.InputChannel(peer.channel_id, peer.access_hash)))
        assert isinstance(reply, types.messages.ChatInviteJoinResultOk)
    return dict(peer=-1000000000009, source_hash=0, charged=budget.status(222).used)


async def proof_rpc_origin():
    tg, fixture, budget = setup()
    descriptor = h.RPCReply(400, 'INVITE_REQUEST_SENT')
    async with tg._account_health_operation(222, 'join_probe', 'synthetic') as (op, _):
        op.client._stage5_probe_budget = budget
        fixture.wire.script['GetUsersRequest'] = [descriptor]
        TRACE.clear()
        # Deliberately unexpected source code for self proof: the SDK constructs
        # its class from the error name, without asserting which method emitted it.
        error = await fx.expect(errors.InviteRequestSentError, op.client(
            functions.messages.ImportChatInviteRequest('synthetic_token')))
        leaf = error.request
        while hasattr(leaf, 'query'):
            leaf = leaf.query
        assert isinstance(leaf, functions.users.GetUsersRequest)
        assert ('send', 'ImportChatInviteRequest') not in TRACE
    assert budget.status(222).used == 0
    return dict(error=type(error).__name__, actual_origin=type(leaf).__name__,
                join_sends=0, charged=0, synthetic_unexpected_code=True)


async def malformed_ok_payload():
    tg, fixture, budget = setup()
    async with tg._account_health_operation(222, 'join_probe', 'synthetic') as (op, _):
        op.client._stage5_probe_budget = budget
        fixture.wire.script['JoinChannelRequest'] = [g.Reply(
            types.messages.ChatInviteJoinResultOk(types.User(999)))]
        reply = await op.client(functions.channels.JoinChannelRequest(types.InputChannel(9, 19)))
        assert isinstance(reply, types.messages.ChatInviteJoinResultOk)
        assert isinstance(reply.updates, types.User)
    return dict(outer=type(reply).__name__, nested=type(reply.updates).__name__,
                decoded_by_actual_sdk=True, charged=budget.status(222).used)


async def exact_rpc_request_identity():
    tg, fixture, budget = setup()
    descriptor = h.RPCReply(400, 'INVITE_REQUEST_SENT')
    async with tg._account_health_operation(222, 'join_probe', 'synthetic') as (op, _):
        op.client._stage5_probe_budget = budget
        fixture.wire.script['ImportChatInviteRequest'] = [descriptor]
        request = functions.messages.ImportChatInviteRequest('synthetic_token')
        error = await fx.expect(errors.InviteRequestSentError, op.client(request))
        leaf = error.request
        envelopes = []
        while isinstance(leaf, functions.InvokeWithoutUpdatesRequest):
            envelopes.append(type(leaf).__name__)
            leaf = leaf.query
        assert leaf is request and error is descriptor.error
    return dict(exact_request_identity=True, envelopes=envelopes,
                charged=budget.status(222).used)


async def main():
    assert telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='tgdata-stage5-contract-') as temp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient, 'start', side_effect=AssertionError('login forbidden')), \
         patch.object(telethon.TelegramClient, 'send_code_request', side_effect=AssertionError('code forbidden')), \
         patch.object(fx.Wire, 'send', wire_send), \
         patch.object(connection, '_client_class', lambda base: type('ProbeClient', (ProbeMixin, ORIGINAL_CLASS(base)), {})):
        fx.TMP = Path(temp)
        try:
            probes = ((exact_rpc_request_identity,) if '--identity' in sys.argv else
                      (numeric_route, proof_rpc_origin, malformed_ok_payload) if '--extra' in sys.argv
                      else (result_and_cache, source_outcomes, identity_change,
                            cached_wait_and_retry, exhausted_rpc, transport_requeue))
            for function in probes:
                print(json.dumps(dict(probe=function.__name__, result=await function())), flush=True)
        finally:
            for client in fx.CLIENTS:
                await client.disconnect()
            for tg in h.FACADES:
                await tg.close()
            await asyncio.gather(*h.RPC_TASKS, return_exceptions=True)


if __name__ == '__main__':
    asyncio.run(main())
