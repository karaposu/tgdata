"""Inquiry experiment, not production implementation or mandatory prebuild.
Only instance-local lifetime seams and a caller-retained capture adapter change.
All batches, budget charges and persistent outcomes come from real components.
"""
import asyncio
from contextlib import contextmanager
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
from types import MethodType, SimpleNamespace
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata.pool_lifecycle import _inside, _scope, _await_cleanup
from tgdata.smoke_tests import test_31_account_pool as t
from tgdata.smoke_tests import pool_storage_cases as s

class Recipient:
    """Single-use caller-owned data destination, no exception/Task retention."""
    def __init__(self):
        self.phase = 'new'
        self.batch = None
        self.signal = None
        self.error_type = None
        self.read_error_type = None
    async def run(self, work):
        assert self.phase == 'new'
        self.phase = 'running'
        try:
            result = await work()
        except BaseException as error:
            self.batch = getattr(error, 'partial_result', None)
            self.signal = 'cancelled' if isinstance(error, asyncio.CancelledError) else 'failed'
            self.error_type = type(error).__name__
            self.read_error_type = type(error.read_error).__name__ if hasattr(error, 'read_error') else None
            self.phase = 'ended'
            raise
        else:
            self.batch = getattr(result, 'batch', result)
            self.signal = 'returned'
            self.phase = 'ended'
            return result

@contextmanager
def operation(self):
    if _inside(self): raise t.PoolBusyError('live provider scope')
    if self._closed: raise t.PoolClosedError('closed')
    if self._active_task is not None: raise t.PoolBusyError('busy')
    record = SimpleNamespace(caller=asyncio.current_task(), done=asyncio.get_running_loop().create_future())
    self._concept_invocation = record
    self._active_task = record.caller
    try:
        with _scope(self): yield
    finally:
        self._active_task = None
        self._concept_invocation = None
        record.done.set_result(None)

async def close(self):
    if _inside(self): raise t.PoolBusyError('live provider scope')
    current = asyncio.current_task()
    if current is self._active_task or any(current is source.task for source in self._sources.values()):
        raise t.PoolBusyError('owned work cannot close itself')
    if self._closing: raise t.PoolBusyError('already closing')
    self._closed = self._closing = True
    async def finish():
        record = self._concept_invocation
        if record is not None and not record.done.done():
            record.caller.cancel()
            # Compare non-consuming caller join with the library's own witness.
            target = record.caller if self._concept_join == 'caller' else record.done
            await asyncio.wait((target,))
        first = None
        for source in self._sources.values():
            try: await source.retire()
            except asyncio.CancelledError: raise
            except Exception as error: first = first or error
        if first is not None: raise first
    try: await _await_cleanup(finish())
    finally: self._closing = False

def candidate(pool, join='invocation'):
    pool._concept_invocation = None
    pool._concept_join = join
    pool._operation = MethodType(operation, pool)
    pool.close = MethodType(close, pool)

def count(obj):
    batch = obj.batch if isinstance(obj, Recipient) else getattr(obj, 'partial_result', None)
    return len(getattr(batch, 'messages', ()))

async def delayed_settlement(mode, failed=False, after=True):
    e, state, provider, context = await s.setup(mode)
    candidate(e.pool)
    error, size, charge = s.source(e, failed)
    entered, ending, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
    calls, actual = [0], state.compare_and_swap
    async def held(*args):
        calls[0] += 1
        if calls[0] != 2: return await actual(*args)
        entered.set()
        try: await asyncio.Event().wait()
        finally:
            ending.set()
            await release.wait()
            if after: await actual(*args)
    state.compare_and_swap = held
    return e, state, context, entered, ending, release, size, charge

async def lifetime(mode, join):
    e, state, context, entered, ending, release, size, charge = await delayed_settlement(mode)
    e.pool._concept_join = join
    handled, app_release = asyncio.Event(), asyncio.Event()
    recipient = Recipient()
    async def application():
        try: return await recipient.run(lambda: s.read(e, mode, context, 1))
        except asyncio.CancelledError:
            handled.set()
            await app_release.wait()  # application-owned cleanup, outside tgdata
            raise
    caller = asyncio.create_task(application())
    closer = None
    try:
        await entered.wait()
        closer = asyncio.create_task(e.pool.close())
        await ending.wait()
        release.set()
        await handled.wait()
        # Native SDK retirement spans more than eight loop turns. Give the
        # operation-witness candidate a bounded completion observation window.
        for _ in range(500):
            if closer.done(): break
            await asyncio.sleep(0)
        await t.turns()
        finished = closer.done()
        retired = all(source._primary_client is None for source in e.pool._sources.values())
        assert finished is (join == 'invocation') and retired is finished, (mode, join, finished, retired)
        assert e.pool._active_task is None and not caller.done()
        assert all(task.done() for task in state.tasks)
        assert all(source.task is None for source in e.pool._sources.values())
        assert count(recipient) == 1 and e.budget.status(111).used == 1
        return dict(mode=mode, join=join, app_still_running=True, close_done=finished,
                    clients_retired=retired, actual_records=count(recipient))
    finally:
        release.set(); app_release.set()
        await asyncio.gather(caller, *([closer] if closer else []), return_exceptions=True)

async def delivery(mode, wrapper, close_first, failed=False, after=True):
    e, state, context, entered, ending, release, size, charge = await delayed_settlement(mode, failed, after)
    recipient = Recipient()
    caller = asyncio.create_task(recipient.run(lambda: s.read(e, mode, context, 200 if failed else 1)))
    closer = None
    try:
        await entered.wait()
        if close_first: closer = asyncio.create_task(e.pool.close())
        else: caller.cancel()
        await ending.wait()
        caller.cancel(); caller.cancel()
        if closer is not None: closer.cancel(); closer.cancel()
        await t.turns()
        assert not caller.done() and e.pool._active_task is caller
        assert all(source.task is None for source in e.pool._sources.values())
        assert recipient.phase == 'running' and recipient.batch is None
        release.set()
        if closer is not None: await s.capture(closer)
        async def observe():
            if wrapper == 'shield': return await asyncio.shield(caller)
            if wrapper == 'gather_values': return (await asyncio.gather(caller, return_exceptions=True))[0]
            return await caller
        public = await s.capture(observe())
        assert isinstance(public, asyncio.CancelledError) and caller.cancelled()
        assert recipient.phase == 'ended' and recipient.signal == 'cancelled'
        assert count(recipient) == size and recipient.batch.stop_reason == 'interrupted'
        assert e.budget.status(111).used == charge and not e.senders[222].reads
        row = json.loads(await state.actual.load())['accounts']['111']
        assert (row['active'] is None) is after
        assert row['not_before'] == (t.f.NOW + 7200 if failed and after else 0)
        if mode != 'raw': assert await s.pending(e, mode, context) is None
        if failed: assert recipient.read_error_type == 'FloodWaitError'
        await e.pool.close()
        assert all(source._primary_client is None for source in e.pool._sources.values())
        # Independent retrieval is nondestructive and does not resume I/O.
        assert recipient.batch is recipient.batch and count(recipient) == size
        return dict(mode=mode, wrapper=wrapper, close_first=close_first,
            source_failed=failed, committed=after, task_cancelled=caller.cancelled(),
            signal_records=count(public), retained_records=count(recipient), charge=charge,
            pending=False, clients_retired=True)
    finally:
        release.set()
        await asyncio.gather(caller, *([closer] if closer else []), return_exceptions=True)

async def storage(mode, failed, after, progress=False):
    e, state, provider, context = await s.setup(mode)
    candidate(e.pool)
    original, size, charge = s.source(e, failed)
    if progress: provider.arm('compare_and_swap', 1 if mode == 'daily' else 2, after)
    else: state.arm('compare_and_swap', 2, after)
    recipient = Recipient()
    caller = asyncio.create_task(recipient.run(lambda: s.read(e, mode, context, 200 if failed else 1)))
    public = await s.capture(caller)
    assert caller.cancelling() == 0 and recipient.phase == 'ended'
    assert count(recipient) == size and e.budget.status(111).used == charge
    assert not e.senders[222].reads and all(task.done() for task in state.tasks + provider.tasks)
    row = json.loads(await state.actual.load())['accounts']['111']
    if not progress:
        assert isinstance(public, t.PoolStorageError)
        assert (row['active'] is None) is after
        assert row['not_before'] == (t.f.NOW + 7200 if failed and after else 0)
    if mode != 'raw': assert bool(await s.pending(e, mode, context)) is (after if progress else True)
    provider.armed = None
    await e.pool.close()
    return dict(mode=mode, progress=progress, source_failed=failed, committed=after,
        signal=recipient.signal, retained_records=count(recipient), charge=charge,
        pending=bool(await s.pending(e, mode, context)) if mode != 'raw' else False)

async def main(directory):
    t.f.TMP = t.d.TMP = directory
    rows = []
    for mode in ('raw', 'daily', 'backfill'):
        for join in ('caller', 'invocation'):
            rows.append(dict(lifetime=await lifetime(mode, join)))
        for wrapper in ('direct', 'shield', 'gather_values'):
            for close_first in (False, True):
                rows.append(dict(delivery=await delivery(mode, wrapper, close_first)))
        for after in (False, True):
            rows.append(dict(delivery=await delivery(mode, 'gather_values', True, True, after)))
        for failed in (False, True):
            for after in (False, True):
                rows.append(dict(storage=await storage(mode, failed, after)))
    for mode in ('daily', 'backfill'):
        for after in (False, True):
            rows.append(dict(storage=await storage(mode, True, after, progress=True)))
    for pool in t.POOLS: await pool.close()
    print(json.dumps(dict(runtime=sys.version.split()[0], experiments=rows), indent=2))
    print('PASS: 46 concept histories; observations only, no production implementation.')

if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='tgdata17-concept-') as directory, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        asyncio.run(main(Path(directory)))
