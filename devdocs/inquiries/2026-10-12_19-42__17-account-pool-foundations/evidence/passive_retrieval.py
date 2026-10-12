"""Concept-access comparison composed with unchanged AccountPool close/source code.

Only local retrieval functions are hypothetical. No product method is patched.
Actual SDK/SQLite fixtures, owned temporary files, sockets blocked.
"""
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
from tgdata.pool_state import PoolBusyError

async def capture(work):
    try:
        return await work
    except BaseException as error:
        return error

async def compare(busy_guard):
    reports = []
    e = await t.setup(callback=reports.append)
    monitor = e.pool._sources[111].monitor
    async with monitor.call('prior', group=t.CHAT):
        await t.health.report(t.errors.ChannelPrivateError(request=None), 'handled')
    assert reports
    retrieved = []
    observations = {}

    def drain():
        # This is the proposed contract seam, not a method in the product.
        if busy_guard and (e.pool._active_task is not None or e.pool._closing):
            raise PoolBusyError('hypothetical busy-sensitive reporting')
        result = json.loads(json.dumps(reports))
        reports.clear()
        return result

    async def read_with_application_cleanup():
        try:
            return await t.read(e)
        finally:
            observations['closing_when_drained'] = e.pool._closing
            retrieved.extend(drain())

    e.senders[111].script = [t.f.PENDING]
    reader = asyncio.create_task(read_with_application_cleanup())
    await t.d.until(lambda: bool(e.senders[111].pending))
    closer = asyncio.create_task(e.pool.close())
    await asyncio.wait_for(closer, 2)
    result = await capture(reader)
    assert observations['closing_when_drained']
    assert isinstance(result, PoolBusyError if busy_guard else asyncio.CancelledError)
    assert all(source._primary_client is None for source in e.pool._sources.values())
    if not busy_guard:
        assert retrieved and not reports and drain() == []
    print(json.dumps(dict(contract='busy_refusal' if busy_guard else 'always_local',
        caller_result=type(result).__name__, closing_when_drained=True,
        reports_retrieved=bool(retrieved), close_completed=True,
        all_clients_retired=True)), flush=True)

async def main(directory):
    t.f.TMP = t.d.TMP = directory
    try:
        await compare(True)
        await compare(False)
    finally:
        for pool in t.POOLS:
            await pool.close()
        t.POOLS.clear()
    print('PASS2 access-contract comparisons; source/close runtime unchanged.', flush=True)

if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        with tempfile.TemporaryDirectory(prefix='tgdata17-access-') as directory:
            asyncio.run(main(Path(directory)))
