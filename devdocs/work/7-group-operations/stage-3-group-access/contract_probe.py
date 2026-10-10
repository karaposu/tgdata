"""Ground Stage3 meaning in installed SDK/merged foundations, without sockets.

This is inquiry evidence, not an implementation of the proposed public APIs.
Synthetic server results cannot establish live Telegram permission behavior.
"""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path.cwd()))
import telethon
from telethon import errors, utils
from telethon.extensions import BinaryReader
from telethon.sessions import MemorySession
from telethon.tl import functions, types
from tgdata import ReadBudgetExceeded
from tgdata.smoke_tests import test_33_owned_health as fx


def decoded(value):
    with BinaryReader(bytes(value)) as reader:
        return reader.tgread_object()


def channel(**kwargs):
    return types.Channel(7, 'Synthetic group', types.ChatPhotoEmpty(), fx.fx.DATE,
                         megagroup=True, access_hash=0, **kwargs)


def schema_and_cache():
    preview = decoded(types.ChatInvite('Preview', types.PhotoEmpty(0), 4, 0,
                                      request_needed=True))
    peek = decoded(types.ChatInvitePeek(channel(left=True), fx.fx.DATE))
    already = decoded(types.ChatInviteAlready(channel(left=False)))
    facts = {'plain': type(preview).__name__, 'plain_has_id': hasattr(preview, 'id'),
             'plain_has_chat': hasattr(preview, 'chat'), 'approval_hint': preview.request_needed,
             'peek': type(peek).__name__, 'peek_expiry': peek.expires.isoformat(),
             'already': type(already).__name__}
    assert not facts['plain_has_id'] and not facts['plain_has_chat']
    assert isinstance(peek.expires, datetime) and peek.expires.tzinfo == timezone.utc
    ordinary = decoded(channel(left=False))
    peer = utils.get_input_peer(ordinary)
    assert isinstance(peer, types.InputPeerChannel) and peer.access_hash == 0
    memory = MemorySession()
    memory.process_entities([ordinary])
    assert memory.get_entity_rows_by_id(-1000000000007, exact=True) == (-1000000000007, 0)
    memory.process_entities([types.Chat(7, 'Basic', types.ChatPhotoEmpty(), 1, fx.fx.DATE, 1)])
    candidates = [memory.get_entity_rows_by_id(value, exact=True)
                  for value in (-7, -1000000000007)]
    assert all(candidates)
    minimal = decoded(channel(min=True))
    try:
        utils.get_input_peer(minimal)
    except TypeError:
        min_refused = True
    else:
        min_refused = False
    assert min_refused
    community = decoded(types.Community(9, 'Community', types.ChatPhotoEmpty(),
                                         fx.fx.DATE, access_hash=12))
    forbidden = decoded(types.CommunityForbidden(10, 'Community forbidden'))
    assert isinstance(utils.get_input_peer(community), types.InputPeerChannel)
    assert forbidden.access_hash is None
    return dict(facts, zero_hash=peer.access_hash, ambiguous_group_rows=candidates,
                min_refused=min_refused, community_peer=utils.get_peer_id(community),
                community_forbidden_hash=forbidden.access_hash)


async def budget_and_owned_evidence():
    tg, fixture = fx.setup(budget=True, cached=111)
    await fx.fail(tg, fixture)
    before = fixture.budget.status(222).used
    entity = decoded(channel(left=False))
    fixture.responses['ResolveUsernameRequest'] = decoded(types.contacts.ResolvedPeer(
        types.PeerChannel(7), [entity], []))
    async with tg._account_health_operation(222, 'lookup_group', 7) as (op, _):
        reply = await op.client(functions.contacts.ResolveUsernameRequest('synthetic_room'))
        assert reply.chats[0].id == 7
    metadata_used = fixture.budget.status(222).used
    metadata_kept_denial = bool(tg.get_account_health(222)['no_access'])
    async with tg._account_health_operation(222, 'check_group_access', 7) as (op, observed):
        result = await op.client(functions.messages.GetHistoryRequest(
            utils.get_input_peer(entity), 0, None, 0, 1, 0, 0, 0))
        assert isinstance(result, types.messages.Messages)
        observed.confirm_group_access()  # Supplied domain assertion; not new API logic.
    after = fixture.budget.status(222).used
    assert before == metadata_used == 1 and after == 2
    assert metadata_kept_denial and not tg.get_account_health(222)['no_access']
    assert tg._health.snapshot()['events'] == 0
    fixture.budget.configure(222, after)
    async with tg._account_health_operation(222, 'check_group_access', 7) as (op, _):
        await fx.fx.expect(ReadBudgetExceeded, op.client(fx.fx.history()))
        refused_before_send = 'GetHistoryRequest' not in fixture.wire.calls
    assert refused_before_send
    return {'owner': 222, 'cached': 111, 'metadata_cost': metadata_used - before,
            'history_cost': after - metadata_used, 'metadata_kept_denial': metadata_kept_denial,
            'explicit_read_assertion_recovers': True, 'budget_refused_before_history': refused_before_send}


async def direct_numeric_failure():
    tg, fixture = fx.setup()
    reply = fx.RPCReply(500, 'RPC_CALL_FAIL')
    sleeps = []
    sleep = asyncio.sleep
    request_task = asyncio.current_task()
    async def capture_sleep(seconds):
        if asyncio.current_task() is request_task:
            sleeps.append(seconds)
        else:
            await sleep(seconds)
    async with tg._account_health_operation(222, 'lookup_group', -1000000000007) as (op, _):
        fixture.wire.script['GetChannelsRequest'] = [reply]
        with patch('telethon.client.users.asyncio.sleep', capture_sleep):
            actual = await fx.fx.expect(errors.RpcCallFailError, op.client(
                functions.channels.GetChannelsRequest([types.InputChannel(7, 0)])))
        assert actual is reply.error
        sends = fixture.wire.calls.count('GetChannelsRequest')
    assert sends == 1 and sleeps == [2]
    assert tg.get_account_health(222)['events'] == 0 and fixture.wire.closed
    return {'same_final_rpc': True, 'group_sends': sends, 'sdk_backoff': sleeps,
            'closed': True, 'false_health_events': 0}


async def optional_hash_backends():
    outcomes = {}
    for name, store in (('file', None), ('stored', fx.fx.Store())):
        tg, fixture = fx.setup(store=store)
        fixture.responses['GetChannelsRequest'] = decoded(types.messages.Chats([
            types.CommunityForbidden(10, 'Synthetic unavailable community')]))
        try:
            async with tg._account_health_operation(222, 'lookup_group', -1000000000010) as (op, _):
                await op.client(functions.channels.GetChannelsRequest([types.InputChannel(10, 12)]))
        except Exception as exc:
            outcomes[name] = type(exc).__name__
        else:
            outcomes[name] = 'reply returned'
        assert fixture.wire.closed and tg.get_account_health(222)['events'] == 0
    return outcomes


async def main():
    assert telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='tgdata7-stage3-contract-') as temp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(fx.fx.Wire, 'send', fx.wire_send):
        fx.fx.TMP = Path(temp)
        try:
            print(json.dumps({'schema_cache': schema_and_cache()}), flush=True)
            print(json.dumps({'budget_health': await budget_and_owned_evidence()}), flush=True)
            print(json.dumps({'numeric_failure': await direct_numeric_failure()}), flush=True)
            print(json.dumps({'optional_hash_backends': await optional_hash_backends()}), flush=True)
        finally:
            await asyncio.gather(*fx.RPC_TASKS)
            for client in fx.fx.CLIENTS:
                await client.disconnect()
            for tg in fx.FACADES:
                await tg.close()


if __name__ == '__main__':
    asyncio.run(main())
