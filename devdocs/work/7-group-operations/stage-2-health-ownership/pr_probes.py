"""Fresh revision4 PR probes; actual SDK/asyncio composition, no sockets.

Run from the repository root with its Telethon1.45.0 interpreter. Synthetic
decoded server failures use suite33's inspected real sender/result adapter.
These are independent review scenarios, not a replay of the smoke runner.
"""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path.cwd()))
from telethon import errors
from telethon.tl import functions, types
from tgdata import AuthRequiredError, health
from tgdata.smoke_tests import test_33_owned_health as f


def messages():
    return types.messages.Messages(messages=[], topics=[], chats=[], users=[])


async def namespace_restriction():
    tg, fixture = f.setup()
    fixture.responses['GetMessagesRequest'] = messages()
    by_message = functions.messages.GetMessagesRequest([])
    by_channel = functions.channels.GetMessagesRequest(types.InputChannel(7, 7), [])
    async with tg._account_health_operation(222, 'read', 7) as (op, _):
        reply = f.RPCReply(400, 'PEER_FLOOD')
        fixture.wire.script['GetMessagesRequest'] = [reply]
        await f.fx.expect(errors.PeerFloodError, op.client(by_message))
    async with tg._account_health_operation(222, 'read', 7) as (op, _):
        await op.client(by_channel)
    unrelated = tg.get_account_health(222)['verdict']
    async with tg._account_health_operation(222, 'read', 7) as (op, _):
        await op.client(by_message)
    matching = tg.get_account_health(222)['verdict']
    assert (unrelated, matching) == ('restricted', 'ok')
    return {'other_namespace': unrelated, 'same_namespace': matching}


async def concrete_batches():
    result = {}
    for kind in (tuple,):
        tg, fixture = f.setup()
        await f.fail(tg, fixture, errors.FloodWaitError, seconds=120)
        async with tg._account_health_operation(222, 'read', 7) as (op, observed):
            requests = [f.fx.history(), functions.updates.GetStateRequest()]
            batch = kind(requests)
            answers = await op.client(batch)
            assert len(answers) == 2
            keys = sorted(observed.requests)
        assert not tg.get_account_health(222)['waiting']
        assert keys == ['messages.GetHistoryRequest', 'updates.GetStateRequest']
        result[kind.__name__] = keys
    # Generated requests are unhashable: a normal nonempty set/dict of them
    # cannot be built. Check the actual invalid-input boundary, not subclasses
    # invented solely to make the observer's accepted container shapes useful.
    for batch in ({'not-a-request'}, {'not-a-request': None}):
        tg, fixture = f.setup()
        await f.fail(tg, fixture, errors.FloodWaitError, seconds=120)
        async with tg._account_health_operation(222, 'read', 7) as (op, observed):
            await f.fx.expect(TypeError, op.client(batch))
            assert not observed.requests
        assert tg.get_account_health(222)['waiting']['messages.GetHistoryRequest']
        result[type(batch).__name__] = 'invalid SDK input; no recovery evidence'
    return result


async def nested_resolution():
    tg, fixture = f.setup()
    reply = f.RPCReply(420, 'FLOOD_WAIT_120')
    fixture.responses['ResolveUsernameRequest'] = reply
    async with tg._account_health_operation(222, 'read', 7) as (op, observed):
        request = f.fx.history()
        request.peer = '@review_probe'
        actual = await f.fx.expect(errors.FloodWaitError, op.client(request))
        assert actual is reply.error
        assert not observed.requests
    first = tg.get_account_health(222)
    assert first['events'] == 1
    assert set(first['waiting']) == {'contacts.ResolveUsernameRequest'}
    assert 'GetHistoryRequest' not in fixture.wire.calls
    fixture.responses.clear()
    await f.read(tg, fixture)
    assert set(tg.get_account_health(222)['waiting']) == {'contacts.ResolveUsernameRequest'}
    fixture.responses['ResolveUsernameRequest'] = types.contacts.ResolvedPeer(
        peer=types.PeerChannel(7), chats=[], users=[])
    async with tg._account_health_operation(222, 'read', 7) as (op, _):
        await op.client(functions.contacts.ResolveUsernameRequest('review_probe'))
    assert not tg.get_account_health(222)['waiting']
    return {'failure_key': list(first['waiting']), 'initial_events': first['events'],
            'history_success_clears_resolver_wait': False, 'resolver_success_clears': True}


async def unsuccessful_body():
    tg, fixture = f.setup()
    await f.fail(tg, fixture)
    await f.fail(tg, fixture, errors.FloodWaitError, seconds=120)
    await f.fail(tg, fixture, errors.PeerFloodError)
    primary = OSError('local consumer failure')
    try:
        async with tg._account_health_operation(222, 'read', 7) as (op, observed):
            await op.client(f.fx.history())
            observed.confirm_group_access()
            raise primary
    except OSError as actual:
        assert actual is primary
    snapshot = tg.get_account_health(222)
    assert snapshot['verdict'] == 'restricted'
    assert snapshot['waiting']['messages.GetHistoryRequest']
    assert snapshot['no_access']['7'] and snapshot['events'] == 3
    return {'account': snapshot['verdict'], 'wait': list(snapshot['waiting']),
            'group': list(snapshot['no_access']), 'events': snapshot['events']}


async def account_overlap():
    events = []
    tg, fixture = f.setup(events.append, accounts=[222, 333], cached=111)
    blocked = asyncio.Event()
    release = asyncio.Event()
    async def account_b():
        async with tg._account_health_operation(222, 'read', 7) as (op, _):
            fixture.wire.close_release = release
            blocked.set()
            fixture.wire.script['GetHistoryRequest'] = [f.RPCReply(400, 'CHANNEL_PRIVATE')]
            await op.client(f.fx.history())
    task = asyncio.create_task(account_b())
    await blocked.wait()
    source = fixture.clients[0]._sender
    await source.close_entered.wait()
    await f.fail(tg, fixture, errors.PeerFloodError, owner=333, group=8)
    # Wait only for the finished source's notification, leaving B's cleanup held.
    await f.deliveries(tg)
    assert [event['account']['user_id'] for event in events] == [333]
    fixture.engine._primary_client = fixture.clients[-1]
    fixture.clients[-1]._mb_entity_cache.set_self_user(999, False, 999)
    release.set()
    await f.fx.expect(errors.ChannelPrivateError, task)
    await f.deliveries(tg)
    owners = [event['account']['user_id'] for event in events]
    assert owners == [333, 222]
    assert tg.get_account_health(222)['no_access']['7']
    assert tg.get_account_health(333)['verdict'] == 'restricted'
    assert tg.get_account_health(999) is None
    assert events[1]['time'] <= events[0]['time']
    return {'arrival_owners': owners, 'observation_order': [222, 333],
            'cached_owner': 999, 'cached_owner_has_ledger': False}


async def cancellation_recovery():
    tg, fixture = f.setup()
    await f.fail(tg, fixture, errors.FloodWaitError, seconds=120)
    ready = asyncio.Event()
    async def worker():
        async with tg._account_health_operation(222, 'read', 7) as (op, _):
            await op.client(f.fx.history())
            ready.set()
            await asyncio.Event().wait()
    task = asyncio.create_task(worker())
    await ready.wait()
    task.cancel()
    await f.fx.expect(asyncio.CancelledError, task)
    assert fixture.wire.closed
    assert tg.get_account_health(222)['waiting']['messages.GetHistoryRequest']
    await f.read(tg, fixture)
    assert not tg.get_account_health(222)['waiting']
    return {'cancelled_body_keeps_wait': True, 'source_closed': True,
            'later_success_recovers': True}


async def forwarding_then_fresh():
    events = []
    tg, fixture = f.setup(events.append, accounts=[111, 222], cached=111)
    legacy = fixture.engine._new_client()
    fixture.engine._primary_client = legacy
    await legacy.connect()
    auth_reply = f.RPCReply(401, 'SESSION_REVOKED')
    fixture.responses['GetStateRequest'] = auth_reply
    async def child():
        async with tg._account_health_operation(222, 'read', 7):
            raise AssertionError('Must refuse')
    async with tg._health.call('legacy', 8):
        try:
            await asyncio.create_task(child())
        except AuthRequiredError as isolated:
            assert health.classify(isolated, include_reported=True).verdict == 'logged out'
            assert await health.report(isolated) is None
            fixture.responses.clear()
            fresh = f.RPCReply(420, 'FLOOD_WAIT_120')
            legacy._sender.script['GetHistoryRequest'] = [fresh]
            error = await f.fx.expect(errors.FloodWaitError, legacy(f.fx.history()))
            assert error is fresh.error
            finding = await health.report(error)
            assert finding.verdict == 'waiting'
    assert tg.get_account_health(222) is None
    assert tg._health.snapshot()['events'] == 1
    assert events[0]['account']['user_id'] == 111
    assert events[0]['request'] == 'GetHistoryRequest'  # Ordinary client / legacy spelling.
    return {'isolated_diagnostic': 'logged out', 'owned_ledger': None,
            'legacy_owner': 111, 'legacy_events': 1, 'legacy_request': events[0]['request']}


async def cleanup():
    await asyncio.gather(*f.RPC_TASKS)
    f.RPC_TASKS.clear()
    for client in f.fx.CLIENTS:
        client._sender.close_error = None
        if client._sender.close_release is not None:
            client._sender.close_release.set()
        await client.disconnect()
    f.fx.CLIENTS.clear()
    for tg in f.FACADES:
        await tg.close()
    f.FACADES.clear()


async def main():
    probes = (namespace_restriction, concrete_batches, nested_resolution,
              unsuccessful_body, account_overlap, cancellation_recovery,
              forwarding_then_fresh)
    with tempfile.TemporaryDirectory(prefix='tgdata-pr22-r4-') as temporary, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(f.fx.Wire, 'send', f.wire_send):
        f.fx.TMP = Path(temporary)
        for probe in probes:
            try:
                result = await asyncio.wait_for(probe(), timeout=20)
                print(json.dumps({'probe': probe.__name__, 'observed': result}), flush=True)
            finally:
                await cleanup()


if __name__ == '__main__':
    asyncio.run(main())
