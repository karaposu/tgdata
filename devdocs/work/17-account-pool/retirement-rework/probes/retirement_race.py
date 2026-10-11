"""Diagnostic only: actual pool/SDK cleanup with a delayed transport close."""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[5]))
from tgdata.smoke_tests import test_31_account_pool as t


async def main():
    with tempfile.TemporaryDirectory(prefix='tgdata17-retire-') as directory, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        t.f.TMP = t.d.TMP = Path(directory)
        e = await t.setup()
        source = e.pool._sources[111]
        original = e.senders[111].disconnect
        entered, release, finished = asyncio.Event(), asyncio.Event(), asyncio.Event()
        sdk_tasks = []
        async def delayed_transport_close():
            sdk_tasks.append(asyncio.current_task())
            entered.set()
            await release.wait()
            await original()
            finished.set()
        e.senders[111].disconnect = delayed_transport_close
        task = asyncio.create_task(e.pool.recheck_account(111))
        try:
            await asyncio.wait_for(entered.wait(), 5)
            task.cancel()
            await t.f.expect(asyncio.CancelledError, task)
            observation = dict(recheck_cancelled=task.cancelled(),
                sdk_disconnect_still_running=not finished.is_set(),
                pool_operation_slot_released=e.pool._active_task is None,
                old_client_retained=source._primary_client is e.clients[111])
            result = await asyncio.wait_for(t.read(e), 5)
            observation.update(next_read_account=result.account_id,
                next_read_count=len(result.batch.messages),
                next_read_completed_before_old_disconnect=not finished.is_set(),
                read_budget_charged=e.budget.status(111).used)
            print(json.dumps(observation), flush=True)
            assert observation['sdk_disconnect_still_running']
            assert observation['next_read_completed_before_old_disconnect']
        finally:
            release.set()
            await asyncio.gather(*sdk_tasks, return_exceptions=True)
            e.senders[111].disconnect = original
            for pool in t.POOLS:
                await pool.close()
            t.POOLS.clear()


asyncio.run(main())
