"""Fresh PR probes against actual #7 code; synthetic transport, no Telegram sockets."""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from telethon import errors
from tgdata import GroupReferenceError
from tgdata.smoke_tests import test_20_group_operations as g


async def immediate(_):
    pass


async def retry_exhaustion():
    sender = g.Sender()
    server_error = errors.ServerError(None, 'synthetic temporary server fault')
    sender.channels_reply = server_error
    with g.rig(senders=[sender], seed=[g.room()]) as r, patch(
            'telethon.client.users.asyncio.sleep', immediate):
        caught = await g.expect(GroupReferenceError, r.tg.lookup_group(-1000000000007))
        requests = [x for x in sender.requests if type(x).__name__ == 'GetChannelsRequest']
        assert len(requests) == 6
        assert isinstance(caught.__context__, ValueError) and caught.__cause__ is None
        assert caught.__suppress_context__ and not r.events
        print('REPRO numeric retry exhaustion:', json.dumps({
            'rpc_attempts': len(requests), 'actual_error': type(server_error).__name__,
            'public_error': type(caught).__name__, 'suppressed_context': str(caught.__context__)}))

    budget, _ = g.ledger(10)
    sender = g.Sender()
    sender.join_script = [server_error] * 6
    with g.rig(budget, senders=[sender]) as r, patch('telethon.client.users.asyncio.sleep', immediate):
        caught = await g.expect(ValueError, r.tg.join_group(g.LINK))
        assert type(caught) is ValueError and len(sender.join_requests) == 6
        assert budget.status(g.f.ACCOUNT).used == 6
        print('REPRO join retry exhaustion:', json.dumps({
            'rpc_attempts': len(sender.join_requests), 'public_error': type(caught).__name__,
            'used': budget.status(g.f.ACCOUNT).used}))


async def overlapping_identity():
    trace = []
    a, b = g.Sender(222), g.Sender(333)
    a.script, b.script = [errors.ChannelPrivateError(None)], [errors.ChannelPrivateError(None)]
    with g.rig(senders=[a, b]) as r:
        async def traced(name, target):
            trace.append(name + ':start')
            try:
                return await r.tg.check_group_access(target)
            finally:
                trace.append(name + ':end')
        await asyncio.gather(traced('A', 'synthetic_aaa'), traced('B', 'synthetic_bbb'))
    assert trace == ['A:start', 'A:end', 'B:start', 'B:end']
    print('OBSERVED original immediate-response concurrency fixture:', trace)

    a, b = g.Sender(222), g.Sender(333)
    a.resolve_reply = b.resolve_reply = g.f.PENDING
    with g.rig(senders=[a, b]) as r:
        first = asyncio.create_task(r.tg.check_group_access('synthetic_aaa'))
        second = asyncio.create_task(r.tg.check_group_access('synthetic_bbb'))
        for _ in range(100):
            if a.pending and b.pending:
                break
            await asyncio.sleep(0)
        assert a.pending and b.pending and not first.done() and not second.done()
        b.pending[0].set_exception(errors.ChannelPrivateError(None))
        a.pending[0].set_exception(errors.ChannelPrivateError(None))
        values = await asyncio.gather(first, second)
        assert all(value.status == 'denied' for value in values)
        pairs = {(e['group'], e['account']['user_id']) for e in r.events}
        assert pairs == {('synthetic_aaa', 222), ('synthetic_bbb', 333)}
        print('PASS genuinely overlapping calls retain their own account identities')


async def snapshot_identity():
    primary, ephemeral = g.Sender(222), g.Sender(222)
    ephemeral.script = [errors.ChannelPrivateError(None)]
    with g.rig(senders=[primary, ephemeral], cached=111) as r:
        r.tg.connection_engine._primary_client = r.tg.connection_engine._new_client()
        await r.tg.check_group_access('synthetic_room')
        event_id = r.events[-1]['account']['user_id']
        summary = await r.tg.health_check()
        snapshot_id = summary['health']['account']['user_id']
        assert event_id == 222 and snapshot_id == 111
        assert 'synthetic_room' in summary['health']['no_access']
        print('REPRO public summary identity:', json.dumps({'event': event_id, 'summary': snapshot_id,
                                                          'contains_ephemeral_denial': True}))


async def main():
    await retry_exhaustion()
    await overlapping_identity()
    await snapshot_identity()


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp, patch.object(
            socket.socket, 'connect', side_effect=AssertionError('network forbidden')):
        g.TMP = g.f.TMP = Path(tmp)
        asyncio.run(main())
