"""Real local SDK composition; server packets synthetic, sockets forbidden."""
import asyncio
from datetime import timedelta
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import telethon
from telethon import errors
from telethon.extensions import BinaryReader
from telethon.tl import functions, types
from tgdata import ReadBudgetExceeded
from tgdata.account_operation import AccountIdentityError
from tgdata.batch_heartbeat import heartbeat_scope
from tgdata.group_operations import _resolve, _parse_target
from tgdata.smoke_tests import test_34_group_access as g

fx, h, DATE = g.fx, g.h, g.DATE


def message(id, date=DATE, **kwargs):
    return types.Message(id, types.PeerChannel(7), date=date, message='', **kwargs)


def page(rows, full=False):
    return (types.messages.Messages(rows, [], [], []) if full else
            types.messages.ChannelMessages(1, 9999, rows, [], [], []))


async def collect(tg, cap=200, start=None, end=None, beats=None, account=222):
    start = start or DATE - timedelta(days=1)
    end = end or DATE + timedelta(seconds=1)
    upper = end.replace(microsecond=0) + (timedelta(seconds=1) if end.microsecond else timedelta())
    rows, pages, scanned, stop = [], [], 0, None
    with heartbeat_scope(beats):
        async with tg._account_health_operation(account, 'prebuild', 'synthetic_room') as (op, _):
            _, peer = await _resolve(op, _parse_target('synthetic_room'))
            offset = 0
            try:
                while scanned < cap:
                    req = functions.messages.GetHistoryRequest(
                        peer, offset, upper if not offset else None, 0,
                        min(100, cap-scanned), 0, 0, 0)
                    with BinaryReader(bytes(req)) as reader:
                        decoded = reader.tgread_object()
                    assert (decoded.offset_date == upper if not offset else
                            decoded.offset_date.timestamp() == 0)  # None encodes wire date0.
                    assert decoded.offset_id == offset and decoded.limit == req.limit
                    reply = await op.client(req)
                    pages.append(reply)
                    scanned += len(reply.messages)
                    rows.extend(reply.messages)
                    if any(getattr(m, 'date', None) is not None and m.date < start
                           for m in reply.messages):
                        stop = 'window_start'
                        break
                    if not reply.messages or isinstance(reply, types.messages.Messages):
                        stop = 'history_end'
                        break
                    offset = reply.messages[-1].id
                return rows, pages, scanned, stop or 'message_limit'
            except (Exception, asyncio.CancelledError) as error:
                error.partial_rows = tuple(rows)
                raise


async def paging_precision_and_slots():
    rows = [message(i, DATE + timedelta(seconds=(i//100))) for i in range(205, 0, -1)]
    # Packets deliberately supply pages; local component evidence only.
    packets = [page(rows[:100]), page(rows[100:140]), page(rows[140:]), page([])]
    def response(wire, req):
        return g.Reply(packets.pop(0))
    tg, f = g.setup(cached=111, budget=True, proxy=True, responses={'GetHistoryRequest': response})
    f.budget.configure(222, 1000)
    beats = []
    observed, replies, scanned, stop = await collect(
        tg, 300, end=DATE + timedelta(seconds=2, microseconds=1), beats=beats.append)
    assert [m.id for m in observed] == list(range(205, 0, -1))
    assert scanned == 205 and stop == 'history_end' and len(replies) == 4
    reqs = g.requests(f, functions.messages.GetHistoryRequest)
    assert [r.offset_id for r in reqs] == [0,106,66,1]
    assert [r.limit for r in reqs] == [100,100,100,95]
    assert f.budget.status(222).used == 205 and f.budget.status(111).used == 0
    assert f.clients[0]._self_id == 111 and f.wire.closed
    assert beats.count('request') == beats.count('request done')
    assert f.wire.policy_at_connect['flood'] == f.wire.policy_at_connect['requests'] == 0


async def counter_and_placeholder_codec():
    m = message(9, from_id=types.PeerChannel(88), grouped_id=2**62+17,
        views=0, forwards=0, replies=types.MessageReplies(0, 1, comments=True, channel_id=7),
        reactions=types.MessageReactions([types.ReactionCount(types.ReactionEmoji('x'), 0)], min=True))
    tg, f = g.setup(budget=True, responses={'GetHistoryRequest': g.Reply(page([
        m, types.MessageEmpty(8, peer_id=None), message(7)], full=True))})
    rows, replies, scanned, stop = await collect(tg, 3)
    assert scanned == 3 and stop == 'history_end'
    assert isinstance(replies[0], types.messages.Messages)
    assert isinstance(rows[1], types.MessageEmpty) and rows[1].peer_id is None
    assert rows[0].grouped_id == 2**62+17 and rows[0].views == rows[0].forwards == 0
    assert rows[0].reactions.results[0].count == rows[0].replies.replies == 0
    assert rows[0].replies.comments and rows[0].reactions.min
    assert rows[2].views is rows[2].reactions is rows[2].replies is None
    assert f.budget.status(222).used == 3


async def cap_and_boundary():
    tg, f = g.setup(responses={'GetHistoryRequest': g.Reply(page([message(3),message(2)]))})
    rows, _, scanned, stop = await collect(tg, 2)
    assert scanned == 2 and stop == 'message_limit'
    assert len(g.requests(f, functions.messages.GetHistoryRequest)) == 1
    f.responses['GetHistoryRequest'] = g.Reply(page([message(3),message(2, DATE-timedelta(days=2))]))
    rows, _, scanned, stop = await collect(tg, 2)
    assert scanned == 2 and stop == 'window_start'


async def wrong_owner_and_allowance():
    tg, f = g.setup(cached=111, budget=True)
    await fx.expect(AccountIdentityError, collect(tg, 2, account=111))
    assert not g.requests(f, functions.messages.GetHistoryRequest)
    f.budget.configure(222, 1)
    await fx.expect(ReadBudgetExceeded, collect(tg, 2))
    assert not g.requests(f, functions.messages.GetHistoryRequest)
    assert f.budget.status(222).used == 0


async def second_page_source_failure():
    denial = h.RPCReply(400, 'CHANNEL_PRIVATE')
    values = [g.Reply(page([message(3)])), denial]
    tg, f = g.setup(cached=111, budget=True,
        responses={'GetHistoryRequest': lambda wire, req: values.pop(0)})
    error = await fx.expect(errors.ChannelPrivateError, collect(tg, 3))
    assert error is denial.error and [r.id for r in error.partial_rows] == [3]
    assert f.budget.status(222).used == 3 and f.budget.status(222).reserved == 2
    assert f.wire.closed and tg.get_account_health(111) is None
    assert tg.get_account_health(222)['no_access']['synthetic_room']


async def stalled_cancellation_and_cleanup():
    entered, release, closing, close_release = (asyncio.Event() for _ in range(4))
    values = [g.Reply(page([message(3)])), g.Reply(page([message(2)]), entered=entered, release=release)]
    def prepare(client):
        client._sender.close_entered, client._sender.close_release = closing, close_release
    tg, f = g.setup(budget=True, prepare=prepare,
        responses={'GetHistoryRequest': lambda wire, req: values.pop(0)})
    beats = []
    task = asyncio.create_task(collect(tg, 3, beats=beats.append))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        saved = list(beats)
        await fx.turns(20)
        assert saved == beats
        task.cancel()
        await asyncio.wait_for(closing.wait(), 3)
        task.cancel()
        await fx.turns(20)
        assert not task.done() and not f.wire.closed
        close_release.set()
        error = await fx.expect(asyncio.CancelledError, task)
        assert f.wire.closed and f.budget.status(222).reserved == 2
        # Repeated cleanup cancellation may carry a new cancellation object.
        assert tg.get_account_health(222)['events'] == 0
        release.set()
        await fx.turns(10)
        assert beats == saved
    finally:
        release.set(); close_release.set()
        await asyncio.gather(task, return_exceptions=True)


async def cleanup_error_and_callback_isolation():
    source = OSError('source')
    def prepare(client):
        client._sender.close_error = ValueError('cleanup')
    def bad(_):
        raise errors.ChannelPrivateError(None)
    tg, f = g.setup(prepare=prepare, responses={'GetHistoryRequest': source})
    assert await fx.expect(OSError, collect(tg, 3, beats=bad)) is source
    assert source.partial_rows == () and f.wire.close_calls == 1
    assert tg.get_account_health(222)['events'] == 0


async def main():
    assert telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='activity-prebuild-') as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient, 'start', side_effect=AssertionError('login forbidden')), \
         patch.object(fx.Wire, 'send', g.send):
        fx.TMP = Path(tmp)
        tests = (paging_precision_and_slots, counter_and_placeholder_codec, cap_and_boundary,
                 wrong_owner_and_allowance, second_page_source_failure,
                 stalled_cancellation_and_cleanup, cleanup_error_and_callback_isolation)
        for test in tests:
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
                fx.CLIENTS.clear(); h.FACADES.clear(); h.RPC_TASKS.clear(); g.TRACE.clear()
    print('7 combined prebuild groups passed; no live Telegram evidence', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
