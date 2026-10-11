"""Rework-critic reconnaissance on actual pool/reader/SDK/asyncio.

Network is synthetic and blocked. A cooperative finalizer is explicitly injected
AFTER the real batch read exits; this tests task ownership, not a live SDK delay.
"""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from tgdata.smoke_tests import test_31_account_pool as t


async def child_case(close=False):
    e = await t.setup()
    source = e.pool._sources[111]
    fetch = source.batch_reader.fetch_batch
    entered, release = asyncio.Event(), asyncio.Event()
    async def cooperative_finalizer(*args, **kwargs):
        try:
            return await fetch(*args, **kwargs)
        finally:
            entered.set()
            await release.wait()
    source.batch_reader.fetch_batch = cooperative_finalizer
    e.senders[111].script = [t.f.PENDING]
    reader = asyncio.create_task(t.read(e))
    closer = None
    try:
        await t.d.until(lambda: bool(e.senders[111].pending))
        child = source.task
        if close:
            closer = asyncio.create_task(e.pool.close())
        else:
            reader.cancel()
        await entered.wait()
        (closer if close else reader).cancel()
        for _ in range(12):
            await asyncio.sleep(0)
        outcome = dict(case='close_cancel' if close else 'repeated_read_cancel',
            reader_ended=reader.done(), source_child_ended=child.done(),
            source_reference_cleared=source.task is None)
        if close:
            await asyncio.wait_for(asyncio.shield(closer), 3)
            outcome['close_cancelled'] = closer.cancelled()
            outcome['child_pending_after_close'] = not child.done()
        else:
            await t.f.expect(asyncio.CancelledError, reader)
            result = await t.read(e)
            outcome['next_read_account'] = result.account_id
            outcome['child_pending_after_next_read'] = not child.done()
        print(json.dumps(outcome), flush=True)
        assert not child.done() and reader.done()
    finally:
        release.set()
        await asyncio.gather(reader, child, *([closer] if closer is not None else []), return_exceptions=True)
        source.batch_reader.fetch_batch = fetch
        await e.pool.close()


async def main():
    with tempfile.TemporaryDirectory(prefix='pool-child-edges-') as root, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        t.f.TMP = t.d.TMP = Path(root)
        try:
            await child_case()
            await child_case(close=True)
        finally:
            for pool in t.POOLS:
                await pool.close()
            t.POOLS.clear()


asyncio.run(main())
