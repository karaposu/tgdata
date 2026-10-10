"""Fresh PR23 review probes; actual SDK composition, synthetic server data only."""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import telethon
from telethon.tl import functions, types
from tgdata import GroupResponseError
from tgdata.smoke_tests import test_34_group_access as f


async def cache_vs_current_reply():
    rows = []
    for store in (None, f.fx.Store()):
        tg, fixture = f.setup(store=store, seeds=[f.channel(access_hash=11)],
                              entity=f.channel(access_hash=22))
        result = await tg.check_group_access('synthetic_room', account_id=222)
        peer = f.requests(fixture, functions.messages.GetHistoryRequest)[0].peer
        assert result.readable is True and peer.access_hash == 22
        fixture.responses['GetHistoryRequest'] = f.h.RPCReply(400, 'CHANNEL_PRIVATE')
        assert (await tg.check_group_access('synthetic_room', account_id=222)).status == 'denied'
        fixture.responses['ResolveUsernameRequest'] = f.resolved(f.channel(min=True, access_hash=33))
        before = len(f.requests(fixture, functions.messages.GetHistoryRequest))
        result = await tg.check_group_access('synthetic_room', account_id=222)
        assert result.status == 'unprobed' and result.member is None
        assert len(f.requests(fixture, functions.messages.GetHistoryRequest)) == before
        assert tg.get_account_health(222)['no_access']['synthetic_room']
        rows.append(dict(backend='file' if store is None else 'stored', fresh_hash=peer.access_hash,
                         minimal=result.status, extra_history=0, denial_retained=True))
    return rows


async def malformed_nested_invite():
    observed = []
    for leaf in (types.PeerChat(7), types.PeerChannel(7), types.User(7)):
        tg, fixture = f.setup(responses={'CheckChatInviteRequest': f.Reply(types.ChatInviteAlready(leaf))})
        try:
            await tg.check_group_access('t.me/+probe_token', account_id=222)
        except Exception as exc:
            outcome = type(exc).__name__
        else:
            outcome = 'unexpected success'
        assert outcome != 'unexpected success'
        snapshot = tg.get_account_health(222)
        assert snapshot['events'] == 0 and fixture.wire.closed
        assert not f.requests(fixture, functions.messages.GetHistoryRequest)
        observed.append(dict(nested=type(leaf).__name__, outcome=outcome,
                             expected='GroupResponseError', health_events=0, closed=True))
    return observed


class DelayedRPC(f.h.RPCReply):
    def __init__(self, entered, release):
        super().__init__(400, 'CHANNEL_PRIVATE')
        self.entered, self.release = entered, release

    def send(self, wire, request, ordered=False):
        async def deliver():
            self.entered.set()
            await self.release.wait()
            return await super(DelayedRPC, self).send(wire, request, ordered=ordered)
        return asyncio.create_task(deliver())


async def late_old_failure():
    entered, release = asyncio.Event(), asyncio.Event()
    denial = DelayedRPC(entered, release)
    tg, fixture = f.setup(budget=True, cached=111, responses={'GetHistoryRequest': denial})
    older = asyncio.create_task(tg.check_group_access('synthetic_room', account_id=222))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        fixture.responses['GetHistoryRequest'] = f.history()
        newer = await tg.check_group_access('synthetic_room', account_id=222)
        assert newer.readable and not tg.get_account_health(222)['no_access']
        release.set()
        later = await older
        assert later.status == 'denied' and later.account_id == 222
        assert tg.get_account_health(222)['no_access']['synthetic_room']
        assert fixture.budget.status(222).used == 2
        assert tg.get_account_health(111) is None
        return dict(newer=newer.status, older_completed_later=later.status, denial_retained=True,
                    owner=222, budget_used=2, cached_owner_has_health=False)
    finally:
        release.set()
        await asyncio.gather(older, return_exceptions=True)


async def budget_denial_never_changes_group_state():
    tg, fixture = f.setup(budget=True, responses={'GetHistoryRequest': f.h.RPCReply(400,'CHANNEL_PRIVATE')})
    await tg.check_group_access('synthetic_room', account_id=222)
    fixture.budget.configure(222, 1)
    fixture.responses['GetHistoryRequest'] = f.history()
    await f.fx.expect(f.ReadBudgetExceeded, tg.check_group_access('synthetic_room', account_id=222))
    snapshot = tg.get_account_health(222)
    assert snapshot['events'] == 1 and snapshot['no_access']['synthetic_room']
    assert not f.requests(fixture, functions.messages.GetHistoryRequest)[1:]
    assert fixture.wire.closed
    return dict(events=1, denial_retained=True, history_sends=1, second_call='ReadBudgetExceeded')


async def numeric_rejection_is_qualified_source_reason():
    tg, fixture = f.setup(seeds=[f.channel()], responses={
        'GetChannelsRequest': f.h.RPCReply(400, 'CHANNEL_INVALID')})
    result = await tg.check_group_access(-1000000000007, account_id=222)
    assert result.status == 'denied' and result.reason == 'CHANNEL_INVALID' and result.lookup is None
    assert not f.requests(fixture, functions.messages.GetHistoryRequest)
    return dict(status=result.status, reason=result.reason, lookup=result.lookup,
                events=tg.get_account_health(222)['events'])


async def service_message_peer_validation():
    tg, fixture = f.setup(responses={'GetHistoryRequest': f.history(messages=[types.MessageService(
        5, types.PeerChannel(8), f.DATE, action=types.MessageActionEmpty())])})
    await f.fx.expect(GroupResponseError, tg.check_group_access('synthetic_room', account_id=222))
    assert tg.get_account_health(222)['events'] == 0 and fixture.wire.closed
    return dict(outcome='GroupResponseError', wrong_peer=8, health_events=0)


async def main():
    assert telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='tgdata-pr23-review-') as root, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient, 'start', side_effect=AssertionError('login forbidden')), \
         patch.object(telethon.TelegramClient, 'send_code_request', side_effect=AssertionError('code forbidden')), \
         patch.object(f.fx.Wire, 'send', f.send):
        f.fx.TMP = Path(root)
        try:
            for probe in (cache_vs_current_reply, malformed_nested_invite, late_old_failure,
                          budget_denial_never_changes_group_state,
                          numeric_rejection_is_qualified_source_reason, service_message_peer_validation):
                print(json.dumps({probe.__name__: await probe()}), flush=True)
        finally:
            for client in f.fx.CLIENTS:
                await client.disconnect()
            for tg in f.h.FACADES:
                await tg.close()
            await asyncio.gather(*f.h.RPC_TASKS, return_exceptions=True)


if __name__ == '__main__':
    asyncio.run(main())
