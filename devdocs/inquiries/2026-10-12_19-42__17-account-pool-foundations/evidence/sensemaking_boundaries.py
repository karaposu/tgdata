"""Current-code counterchecks for the #17 conceptual inquiry; no candidate patch."""
import asyncio
import json
import logging
import os
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata.smoke_tests import test_31_account_pool as t


def emit(case, **values):
    print(json.dumps(dict(case=case, **values), sort_keys=True), flush=True)


async def capture(work):
    try:
        return await work
    except BaseException as error:
        return error


async def success_observer_cancel():
    async def observer(event):
        owned = asyncio.get_running_loop().create_future()
        owned.cancel()
        await owned
    e = await t.setup(callback=observer)
    monitor = e.pool._sources[111].monitor
    # Seed a known prior health fact to request recovery notification after a
    # real successful SDK read. This fixture does not supply the source result.
    monitor.callback = None
    async with monitor.call('prior', group=t.CHAT):
        await t.health.report(t.errors.ChannelPrivateError(request=None), 'handled')
    monitor.callback = observer
    result = await capture(t.read(e))
    row = json.loads(await e.store.load())['accounts']['111']
    assert isinstance(result, asyncio.CancelledError)
    assert asyncio.current_task().cancelling() == 0
    assert len(e.senders[111].reads) == 1 and not e.senders[222].reads
    assert e.budget.status(111).used == 1 and row['active'] is not None
    emit('success_hidden_by_observer_cancel', actual_source_reads=1, actual_charge=1,
         caller_cancel_requests=0, returned=type(result).__name__, unresolved=True)


async def independent_close_control():
    e = await t.setup()
    e.senders[111].script = [t.f.PENDING]
    reader = asyncio.create_task(t.read(e))
    await t.d.until(lambda: bool(e.senders[111].pending))
    closer = asyncio.create_task(e.pool.close())
    await asyncio.wait_for(closer, 2)
    result = await capture(reader)
    assert isinstance(result, asyncio.CancelledError)
    assert all(s._primary_client is None for s in e.pool._sources.values())
    emit('independent_close_control', external_close_completed=True,
         reader_cancelled=True, all_clients_retired=True)


async def store_descendant_child(directory):
    t.f.TMP = t.d.TMP = directory
    e = await t.setup()
    actual = e.store
    holder = {}
    class Backend:
        async def load(self):
            # Instrumentation/observer code inside an allowed asynchronous
            # backend initiates and awaits close; source has not started.
            holder['close'] = asyncio.create_task(e.pool.close())
            return await holder['close']
        async def compare_and_swap(self, *args):
            return await actual.compare_and_swap(*args)
    e.pool._store = Backend()
    reader = asyncio.create_task(t.read(e))
    await t.d.until(lambda: 'close' in holder)
    await t.turns(30)
    closer = holder['close']
    assert not reader.done() and not closer.done() and e.pool._closing
    assert getattr(reader, '_fut_waiter', None) is closer
    assert any(getattr(task, '_fut_waiter', None) is reader for task in asyncio.all_tasks())
    assert all(source.task is None for source in e.pool._sources.values())
    assert not any(sender.calls for sender in e.senders.values())
    emit('backend_descendant_close_cycle', source_started=False,
         reader_waits_for_close=True, cleanup_waits_for_reader=True,
         reader_done=False, close_done=False, sdk_disconnects_started=0)
    os._exit(42)  # Only this owned diagnostic subprocess; loop has a proven cycle.


async def main(directory):
    t.f.TMP = t.d.TMP = directory
    try:
        await success_observer_cancel()
        await independent_close_control()
        child_path = directory / 'child'
        child_path.mkdir()
        child = await asyncio.create_subprocess_exec(sys.executable, __file__, '--store-child',
            str(child_path), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(child.communicate(), 10)
            assert child.returncode == 42, stderr.decode()
            result = json.loads(stdout)
            assert result['source_started'] is False
            print(stdout.decode().strip(), flush=True)
        finally:
            if child.returncode is None:
                child.kill()
                await child.wait()
    finally:
        for pool in t.POOLS:
            await pool.close()
        t.POOLS.clear()
    print('PASS3 current-code conceptual counterchecks; no runtime edits.', flush=True)


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        if len(sys.argv)>1:
            asyncio.run(store_descendant_child(Path(sys.argv[2])))
        else:
            with tempfile.TemporaryDirectory(prefix='tgdata17-sense-') as directory:
                asyncio.run(main(Path(directory)))
