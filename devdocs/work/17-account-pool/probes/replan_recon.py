"""Fresh revision3 reconnaissance on the unchanged product, with no network."""
import asyncio
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata.smoke_tests import test_31_account_pool as t

async def capture(work):
    try:
        return await work
    except BaseException as error:
        return error

async def source_internal_cancel(mode):
    e = await t.setup(daily=t.SQLiteSyncStore(t.path('daily')))
    await e.pool.initialize_sync(t.CHAT, after_id=100)
    e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101, 201))]), t.f.PENDING]
    reader = asyncio.create_task(t.read(e, limit=200) if mode == 'raw' else e.pool.sync_group(t.CHAT, limit=200))
    await t.d.until(lambda: bool(e.senders[111].pending))
    e.senders[111].pending[0].cancel()  # Actual SDK-awaited transport future; not reader.cancel().
    result = await capture(reader)
    status = (await e.pool.get_pool_status(t.CHAT)).accounts[0]
    pending = (await e.pool.get_sync_status(t.CHAT)).pending_batch_id
    assert isinstance(result, asyncio.CancelledError) and reader.cancelling() == 0
    assert status.attempt_id is not None and not e.senders[222].reads
    assert e.budget.status(111).used == 200
    assert len(result.partial_result.messages) == 100 and pending is None
    print(json.dumps(dict(case='source_internal_cancel', mode=mode,
        caller_cancel_requests=reader.cancelling(), public_error=type(result).__name__,
        partial_records=100, pending_delivery=False, unresolved=True, charge=200,
        second_source_reads=0)), flush=True)

async def main(directory):
    t.f.TMP = t.d.TMP = directory
    try:
        for mode in ('raw', 'daily'):
            await asyncio.wait_for(source_internal_cancel(mode), 5)
    finally:
        for pool in t.POOLS:
            await pool.close()
        t.POOLS.clear()

if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        with tempfile.TemporaryDirectory(prefix='tgdata17-replan-recon-') as directory:
            asyncio.run(main(Path(directory)))
