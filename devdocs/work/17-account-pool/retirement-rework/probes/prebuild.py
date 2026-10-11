"""Required candidate experiment; actual pool/SDK/SQLite, synthetic network.

Only the planned private lifetime functions are prototyped here. This is not
delivered-product verification. Held cooperative finalizers are explicit faults.
"""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from tgdata import AccountPool, PoolBusyError, PoolClosedError, PoolStateError, PoolTimeoutError
from tgdata.pool_source import _OwnedSource
from tgdata.smoke_tests import test_31_account_pool as t

OLD_PREFLIGHT, OLD_VERIFY = _OwnedSource.preflight, _OwnedSource._verify


async def wait_cleanup(work):
    async def finish():
        try:
            return await work, None
        except (Exception, asyncio.CancelledError) as error:
            return None, error
    completion = asyncio.ensure_future(finish())
    cancelled = None
    while not completion.done():
        try:
            await asyncio.shield(completion)
        except asyncio.CancelledError as error:
            cancelled = error
    value, error = completion.result()
    if cancelled is not None:
        raise cancelled
    if error is not None:
        raise error
    return value


def preflight(self):
    if getattr(self, '_retirement_blocked', False):
        raise PoolStateError('Client retirement has not completed successfully')
    return OLD_PREFLIGHT(self)


async def verify(self):
    if getattr(self, '_retirement_blocked', False):
        raise PoolStateError('Client retirement has not completed successfully')
    return await OLD_VERIFY(self)


async def retire(self):
    client = self._primary_client
    if client is None:
        return
    self._retirement_blocked = True
    async def finish():
        try:
            await client.disconnect()
        except (Exception, asyncio.CancelledError) as error:
            raise PoolStateError('Account client could not be retired ({})'.format(type(error).__name__)) from None
        self._primary_client = self.verified_id = self._config = None
        self._retirement_blocked = False
    await wait_cleanup(finish())


async def run(self, chat_id=None, **options):
    outcome = {}
    async def observed():
        async with self.monitor.call('account_pool_read' if chat_id is not None else 'account_pool_recheck', group=chat_id):
            try:
                value = (await self.batch_reader.fetch_batch(chat_id, **options)
                         if chat_id is not None else await self._verify())
            except BaseException as error:
                outcome['error'], outcome['done'] = error, not isinstance(error, asyncio.CancelledError)
                raise
            else:
                outcome['value'], outcome['done'] = value, True
                return value
    child = self.task = asyncio.ensure_future(observed())
    async def stop():
        if not child.done():
            child.cancel()
        try:
            await child
        except (Exception, asyncio.CancelledError):
            pass
    try:
        try:
            done, _ = await asyncio.wait((child,), timeout=self.policy.attempt_timeout)
            if done:
                return child.result()
            await wait_cleanup(stop())
        except asyncio.CancelledError:
            await wait_cleanup(stop())
            raise
    finally:
        self.task = None
    if outcome.get('done'):
        if 'error' in outcome:
            raise outcome['error']
        return outcome['value']
    error = PoolTimeoutError('The account source attempt timed out')
    error.partial_result = getattr(outcome.get('error'), 'partial_result', None)
    raise error from None


async def close(self):
    current = asyncio.current_task()
    if current is self._active_task or any(current is getattr(s, 'task', None) for s in self._sources.values()):
        raise PoolBusyError('Cannot close a pool from its source operation')
    if self._closing:
        raise PoolBusyError('Pool close is already in progress')
    self._closed, self._closing = True, True
    async def finish():
        active = self._active_task
        if active is not None and not active.done():
            active.cancel()
            try:
                await active
            except (Exception, asyncio.CancelledError):
                pass
        first = None
        for source in self._sources.values():
            try:
                await source.retire()
            except Exception as error:
                first = first or error
        if first is not None:
            raise first
    try:
        await wait_cleanup(finish())
    finally:
        self._closing = False


async def held_retirement():
    e = await t.setup()
    source = e.pool._sources[111]
    original = e.senders[111].disconnect
    entered, release, finished = asyncio.Event(), asyncio.Event(), asyncio.Event()
    attempts = []
    async def held():
        attempts.append(True)
        entered.set()
        await release.wait()
        await original()
        finished.set()
    e.senders[111].disconnect = held
    task = asyncio.create_task(e.pool.recheck_account(111))
    try:
        await entered.wait()
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        await t.f.expect(PoolBusyError, t.read(e))
        assert not e.senders[111].reads and e.budget.status(111).used == 0
        release.set()
        await t.f.expect(asyncio.CancelledError, task)
        assert finished.is_set() and len(attempts) == 1 and source._primary_client is None
        assert not source._retirement_blocked
        e.clients[111], e.senders[111] = t.wire(source)
        assert (await t.read(e)).account_id == 111
        return dict(caller='CancelledError', disconnects=1, busy_until_finished=True, fresh_read=True)
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)
        await e.pool.close()


async def failed_retirement():
    results = []
    for internal, caller_cancel in [('OSError', False), ('CancelledError', False), ('OSError', True)]:
        e = await t.setup()
        source = e.pool._sources[111]
        old_sender = e.senders[111]
        original = old_sender.disconnect
        entered, release = asyncio.Event(), asyncio.Event()
        async def fail():
            entered.set()
            await release.wait()
            error = asyncio.CancelledError if internal == 'CancelledError' else OSError
            raise error('private-detail')
        e.senders[111].disconnect = fail
        task = asyncio.create_task(e.pool.recheck_account(111))
        try:
            await entered.wait()
            if caller_cancel:
                task.cancel()
            release.set()
            error = await t.f.expect(asyncio.CancelledError if caller_cancel else PoolStateError, task)
            assert 'private-detail' not in str(error) and source._retirement_blocked
            await t.f.expect(PoolStateError, t.read(e))
            assert e.budget.status(111).used == 0 and not e.senders[111].reads
            e.senders[111].disconnect = original
            await source.retire()
            assert source._primary_client is None and not source._retirement_blocked
            e.clients[111], e.senders[111] = t.wire(source)
            assert (await t.read(e)).account_id == 111
            results.append(dict(internal=internal, caller_cancel=caller_cancel,
                                outcome=type(error).__name__, blocked_until_retry=True))
        finally:
            release.set()
            old_sender.disconnect = original
            await asyncio.gather(task, return_exceptions=True)
            await e.pool.close()
    return results


async def held_child(closing=False):
    e = await t.setup()
    source = e.pool._sources[111]
    original = source.batch_reader.fetch_batch
    entered, release = asyncio.Event(), asyncio.Event()
    async def finalizer(*args, **kwargs):
        try:
            return await original(*args, **kwargs)
        finally:
            entered.set()
            await release.wait()
    source.batch_reader.fetch_batch = finalizer
    e.senders[111].script = [t.f.PENDING]
    reader = asyncio.create_task(t.read(e))
    closer = None
    try:
        await t.d.until(lambda: bool(e.senders[111].pending))
        child = source.task
        if closing:
            closer = asyncio.create_task(e.pool.close())
        else:
            reader.cancel()
        await entered.wait()
        target = closer if closing else reader
        target.cancel()
        await asyncio.sleep(0)
        target.cancel()
        for _ in range(8):
            await asyncio.sleep(0)
        assert not target.done() and not child.done() and source.task is child
        await t.f.expect(PoolClosedError if closing else PoolBusyError, t.read(e))
        release.set()
        await t.f.expect(asyncio.CancelledError, target)
        await t.f.expect(asyncio.CancelledError, reader)
        assert child.done() and source.task is None
        if closing:
            assert all(s._primary_client is None for s in e.pool._sources.values())
        return dict(case='close' if closing else 'read', caller='CancelledError',
                    child_awaited=True, no_next_source_before_settlement=True)
    finally:
        release.set()
        await asyncio.gather(reader, child, *([closer] if closer else []), return_exceptions=True)
        await e.pool.close()


async def main():
    with tempfile.TemporaryDirectory(prefix='pool-prebuild-') as root, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(_OwnedSource, 'preflight', preflight), patch.object(_OwnedSource, '_verify', verify), \
         patch.object(_OwnedSource, 'retire', retire), patch.object(_OwnedSource, 'run', run), \
         patch.object(AccountPool, 'close', close):
        t.f.TMP = t.d.TMP = Path(root)
        try:
            cases = [('retirement', held_retirement), ('failure_retry', failed_retirement),
                     ('read_child', held_child), ('close_child', lambda: held_child(True)),
                     ('completed_flood_prefix', t.test_observer_timeout_preserves_original_flood_and_prefix),
                     ('completed_success', t.test_success_observer_timeout_keeps_successful_batch)]
            for name, case in cases:
                result = await asyncio.wait_for(case(), 15)
                print(json.dumps(dict(case=name, result='PASS', observation=result)), flush=True)
        finally:
            for pool in t.POOLS:
                await pool.close()
            t.POOLS.clear()


asyncio.run(main())
