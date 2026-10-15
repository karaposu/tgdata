"""Actual existing SDK/factory composition; synthetic server packets, no network."""
import asyncio
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import telethon
from telethon import errors
from telethon.tl import functions, types
from tgdata import ReadBudgetExceeded
from tgdata.account_operation import AccountIdentityError
from tgdata.batch_heartbeat import heartbeat_scope
from tgdata.group_operations import _resolve, _parse_target
from tgdata.smoke_tests import test_34_group_access as g

fx, h = g.fx, g.h


def full(basic=False, count=None, online=None):
    entity = g.chat() if basic else g.channel()
    if basic:
        detail = types.ChatFull(7, '', types.ChatParticipantsForbidden(7),
                                types.PeerNotifySettings())
    else:
        detail = types.ChannelFull(7, '', 0, 0, 0, types.PhotoEmpty(0),
            types.PeerNotifySettings(), [], 0, participants_count=count,
            online_count=online)
    return types.messages.ChatFull(detail, [entity], [])


def search(peer, limit=3):
    return functions.messages.SearchRequest(peer, '', types.InputMessagesFilterPinned(),
                                           None, None, 0, 0, limit, 0, 0, 0)


async def composition():
    for basic in (False, True):
        for store in (None, fx.Store()):
            beats = []
            tg, f = g.setup(entity=g.chat() if basic else g.channel(), store=store,
                cached=111, budget=True, responses={
                'GetFullChatRequest' if basic else 'GetFullChannelRequest':
                    g.Reply(full(basic, 0, 0)),
                'SearchRequest': g.Reply(types.messages.Messages([], [], [], []))})
            with heartbeat_scope(beats.append):
                async with tg._account_health_operation(222, 'probe', 'synthetic_room') as (op, _):
                    lookup, peer = await _resolve(op, _parse_target('synthetic_room'))
                    request = (functions.messages.GetFullChatRequest(7) if basic else
                        functions.channels.GetFullChannelRequest(types.InputChannel(7, 0)))
                    reply = await op.client(request)
                    assert isinstance(reply, types.messages.ChatFull) and reply.full_chat.about == ''
                    assert reply.full_chat.id == lookup.group.id == 7
                    if not basic:
                        assert reply.full_chat.online_count == reply.full_chat.participants_count == 0
                    assert f.budget.status(222).used == 0
                    pins = await op.client(search(peer))
                    assert pins.messages == [] and f.budget.status(222).used == 0
                    assert op.client._self_id == 111
            assert f.wire.closed and beats.count('request') == beats.count('request done')
            requests = g.requests(f, functions.messages.SearchRequest)
            assert len(requests) == 1 and requests[0].limit == 3
            assert f.budget.status(111).used == 0


async def optional_and_inexact():
    pins = [types.Message(9, types.PeerChannel(7), date=fx.DATE,
                          message='', pinned=True), types.MessageEmpty(8, peer_id=None)]
    for inexact in (False, True):
        tg, f = g.setup(responses={
            'GetFullChannelRequest': g.Reply(full()),
            'SearchRequest': g.Reply(types.messages.ChannelMessages(1, 2, pins, [], [], [],
                                                                    inexact=inexact))})
        async with tg._account_health_operation(222, 'probe', 7) as (op, _):
            metadata = await op.client(functions.channels.GetFullChannelRequest(types.InputChannel(7, 0)))
            assert metadata.full_chat.participants_count is metadata.full_chat.online_count is None
            reply = await op.client(search(types.InputPeerChannel(7, 0)))
            assert bool(reply.inexact) == inexact and reply.count == 2
            assert reply.messages[0].date == fx.DATE and reply.messages[0].message == ''
            assert isinstance(reply.messages[1], types.MessageEmpty)
        assert f.wire.closed


async def allowance_and_owner():
    tg, f = g.setup(budget=True, cached=111)
    async with tg._account_health_operation(222, 'probe', 7) as (op, _):
        f.budget.configure(222, 0)
        await fx.expect(ReadBudgetExceeded, op.client(search(types.InputPeerChannel(7, 0))))
        assert not g.requests(f, functions.messages.SearchRequest)
        f.budget.configure(222, 10)
        f.wire.account = 333
        await fx.expect(AccountIdentityError, op.client(search(types.InputPeerChannel(7, 0))))
        assert not g.requests(f, functions.messages.SearchRequest)
        assert f.budget.status(222).used == f.budget.status(333).used == 0
    assert f.wire.closed


async def errors_and_health():
    refusal = h.RPCReply(400, 'CHANNEL_PRIVATE')
    tg, f = g.setup(budget=True, responses={'SearchRequest': refusal})
    async def attempt():
        async with tg._account_health_operation(222, 'probe', 7) as (op, _):
            await op.client(search(types.InputPeerChannel(7, 0)))
    error = await fx.expect(errors.ChannelPrivateError, attempt())
    assert error is refusal.error
    assert f.budget.status(222).used == f.budget.status(222).reserved == 3
    assert tg.get_account_health(222)['no_access']['7']
    assert f.wire.closed
    f.responses['SearchRequest'] = g.Reply(types.messages.Messages([], [], [], []))
    f.responses['GetFullChannelRequest'] = g.Reply(full())
    async with tg._account_health_operation(222, 'probe', 7) as (op, _):
        await op.client(functions.channels.GetFullChannelRequest(types.InputChannel(7, 0)))
        await op.client(search(types.InputPeerChannel(7, 0)))
    assert tg.get_account_health(222)['no_access']['7']
    assert tg._health.snapshot()['events'] == 0
    await h.deliveries(tg)


async def heartbeat_failure():
    def bad(_):
        raise errors.ChannelPrivateError(None)
    tg, f = g.setup(responses={'SearchRequest': g.Reply(types.messages.Messages([], [], [], []))})
    with heartbeat_scope(bad):
        async with tg._account_health_operation(222, 'probe', 7) as (op, _):
            assert (await op.client(search(types.InputPeerChannel(7, 0)))).messages == []
    assert f.wire.closed and tg.get_account_health(222)['events'] == 0


async def cleanup_cancellation():
    tg, f = g.setup()
    closing, release = asyncio.Event(), asyncio.Event()
    async def work():
        async with tg._account_health_operation(222, 'probe', 7):
            f.wire.close_entered, f.wire.close_release = closing, release
            return 42
    task = asyncio.create_task(work())
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


async def main():
    assert telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='profile-prebuild-') as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient, 'start', side_effect=AssertionError('login forbidden')), \
         patch.object(fx.Wire, 'send', g.send):
        fx.TMP = Path(tmp)
        for test in (composition, optional_and_inexact, allowance_and_owner,
                     errors_and_health, heartbeat_failure, cleanup_cancellation):
            try:
                await asyncio.wait_for(test(), 15)
                print('PASS', test.__name__, flush=True)
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
    print('6 prebuild groups passed', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
