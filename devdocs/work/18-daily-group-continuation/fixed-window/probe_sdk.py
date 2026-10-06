"""Probe the real 1.45.0 iterator/guard; transport is synthetic, not server evidence."""
import asyncio
from datetime import timedelta
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tgdata import ReadBudgetExceeded
from tgdata.smoke_tests import test_19_message_batches as b

f = b.f

async def main():
    start = b.NOW
    tg, client, sender = b.instance()
    requests = []
    def page(ids):
        def respond(r):
            requests.append((r.offset_id, r.offset_date, r.add_offset, r.limit))
            return f.response([f.message(i) for i in reversed(ids)])
        return respond
    sender.script = [page([101, 102]), page([103, 104])]
    first = [m.id async for m in client.iter_messages(f.room(), offset_date=start-timedelta(seconds=1), reverse=True, limit=2)]
    later = [m.id async for m in client.iter_messages(f.room(), min_id=102, reverse=True, limit=2)]
    assert first == [101, 102] and later == [103, 104]
    assert requests[0] == (0, start-timedelta(seconds=1), -2, 2)
    assert requests[1] == (103, None, -2, 2)
    print('PASS date positioning is preserved on first SDK request; resume uses exclusive ID')
    print('PASS messages sharing a timestamp survive an ID-based page boundary')
    budget, _ = f.ledger(2)
    _, guarded, transport = b.instance(budget)
    transport.script = [page([101,102])]
    seen=[]
    try:
        async for m in guarded.iter_messages(f.room(), offset_date=start-timedelta(seconds=1), reverse=True, limit=3):
            seen.append(m.id)
    except ReadBudgetExceeded:
        pass
    else:
        raise AssertionError('quota exhaustion became end-of-history')
    assert seen == [101,102] and budget.status(f.ACCOUNT).used == 2
    assert requests[-1] == (0, start-timedelta(seconds=1), -2, 2)
    print('PASS real budget page resizing retains date seek and raises after completed prefix')

if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='tgdata_window_probe_') as root, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        f.TMP=Path(root)
        async def run():
            try:
                await main()
            finally:
                for client in f.CLIENTS:
                    await client.disconnect()
                f.CLIENTS.clear()
        asyncio.run(run())
