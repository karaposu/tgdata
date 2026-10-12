"""In-memory concept experiments, not an implementation proposal or runtime edit."""
import asyncio
from contextlib import contextmanager
import contextvars
import json
import logging
import os
from pathlib import Path
import socket
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata.smoke_tests import test_31_account_pool as t
from tgdata.pool_source import _OwnedSource, _await_cleanup
from tgdata.account_pool import AccountPool

_SCOPES = contextvars.ContextVar('inquiry_pool_operations', default=())


def emit(case, **values):
    print(json.dumps(dict(case=case, **values), sort_keys=True), flush=True)


async def capture(work):
    try:
        return await work
    except BaseException as error:
        return error


async def retained_outcome(self, chat_id=None, **options):
    outcome = {}
    async def observed():
        async with self.monitor.call('account_pool_read' if chat_id is not None else 'account_pool_recheck', group=chat_id):
            try:
                value = await self.batch_reader.fetch_batch(chat_id, **options) if chat_id is not None else await self._verify()
            except BaseException as error:
                outcome.update(error=error, done=not isinstance(error, asyncio.CancelledError))
                raise
            else:
                outcome.update(value=value, done=True)
                return value
    child = self.task = asyncio.ensure_future(observed())
    async def stop():
        if not child.done():
            child.cancel()
        try:
            await child
        except (Exception, asyncio.CancelledError):
            pass
    terminal = None
    timed_out = False
    try:
        try:
            done, _ = await asyncio.wait((child,), timeout=self.policy.attempt_timeout)
        except asyncio.CancelledError:
            await _await_cleanup(stop())
            raise
        timed_out = not done
        if timed_out:
            await _await_cleanup(stop())
        try:
            child.result()  # Observe task termination; it is not the body's outcome.
        except (Exception, asyncio.CancelledError) as error:
            terminal = error
    finally:
        self.task = None
    if outcome.get('done'):
        if 'error' in outcome:
            raise outcome['error']
        return outcome['value']
    if not timed_out and terminal is not None:
        raise terminal  # Incomplete, unattributed source cancellation stays conservative.
    error = t.PoolTimeoutError('The account source attempt timed out')
    error.partial_result = getattr(outcome.get('error'), 'partial_result', None)
    raise error from None


@contextmanager
def candidate():
    original_operation, original_close = AccountPool._operation, AccountPool.close
    @contextmanager
    def operation(pool):
        with original_operation(pool):
            scope = SimpleNamespace(pool=pool, active=True)
            token = _SCOPES.set(_SCOPES.get() + (scope,))
            try:
                yield
            finally:
                scope.active = False
                _SCOPES.reset(token)
    async def close(pool):
        if any(scope.active and scope.pool is pool for scope in _SCOPES.get()):
            raise t.PoolBusyError('Cannot close from this live operation lineage')
        return await original_close(pool)
    with patch.object(AccountPool, '_operation', operation), \
         patch.object(AccountPool, 'close', close), \
         patch.object(_OwnedSource, 'run', retained_outcome):
        yield


async def own_cancel(mode):
    async def observer(event):
        future = asyncio.get_running_loop().create_future(); future.cancel(); await future
    e = await t.setup(callback=observer, daily=t.SQLiteSyncStore(t.path('daily')))
    if mode == 'success':
        monitor = e.pool._sources[111].monitor
        monitor.callback = None
        async with monitor.call('prior', group=t.CHAT):
            await t.health.report(t.errors.ChannelPrivateError(request=None), 'handled')
        monitor.callback = observer
        result = await t.read(e)
        assert len(result.batch.messages) == 1
        pending = None
    else:
        await e.pool.initialize_sync(t.CHAT, after_id=100)
        failure = t.errors.FloodWaitError(request=None, capture=7200)
        e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101,201))]), failure]
        result = await capture(t.read(e,limit=200) if mode=='raw' else e.pool.sync_group(t.CHAT,limit=200))
        assert result is failure and len(result.partial_result.messages) == 100
        assert (await e.pool.get_pool_status(t.CHAT)).accounts[0].retry_at == t.f.NOW+7200
        pending = (await e.pool.get_sync_status(t.CHAT)).pending_batch_id
        assert (pending is not None) is (mode=='daily')
    assert asyncio.current_task().cancelling() == 0
    assert (await e.pool.get_pool_status()).accounts[0].attempt_id is None
    emit('candidate_observer_cancel', mode=mode, preserved=True, pending=bool(pending), caller_cancel_requests=0)


async def descendants(kind):
    holder, observed = {}, []
    async def call_close():
        work = holder['pool'].close()
        result = await capture(asyncio.wait_for(work,1) if kind=='wait_for' else asyncio.create_task(work))
        assert isinstance(result,t.PoolBusyError)
        observed.append('refused')
    e = await t.setup(callback=(lambda event:call_close()) if kind!='backend' else None)
    holder['pool'] = e.pool
    if kind=='backend':
        actual = e.pool._store
        class Backend:
            async def load(self):
                if not observed:await call_close()
                return await actual.load()
            async def compare_and_swap(self,*args):return await actual.compare_and_swap(*args)
        e.pool._store = Backend()
    else:
        e.senders[111].script=[t.errors.ChannelPrivateError(request=None)]
    result = await t.read(e)
    assert observed and not e.pool._closed
    emit('candidate_descendant', kind=kind, refused=True, selected=result.account_id)


async def stale_context():
    holder={}; release=asyncio.Event()
    async def later():
        await release.wait()
        await holder['pool'].close()
    async def observer(event):holder['task']=asyncio.create_task(later())
    e=await t.setup(callback=observer);holder['pool']=e.pool
    e.senders[111].script=[t.errors.ChannelPrivateError(request=None)]
    assert (await t.read(e)).account_id==222
    release.set();await asyncio.wait_for(holder['task'],2)
    assert e.pool._closed
    emit('candidate_stale_scope', no_permanent_false_refusal=True)


async def foreign_pool():
    target=await t.setup()
    async def observer(event):await target.pool.close()
    e=await t.setup(callback=observer)
    e.senders[111].script=[t.errors.ChannelPrivateError(request=None)]
    assert (await t.read(e)).account_id==222 and target.pool._closed and not e.pool._closed
    emit('candidate_foreign_pool', unrelated_close_permitted=True)


async def predating_actor(directory, passive):
    t.f.TMP=t.d.TMP=directory
    trigger=asyncio.Event(); holder={}; events=[]
    async def actor():
        await trigger.wait(); await holder['pool'].close()
    actor_task=asyncio.create_task(actor())  # Born outside any operation context.
    async def observer(event):
        trigger.set(); await actor_task
    e=await t.setup(callback=events.append if passive else observer);holder['pool']=e.pool
    e.senders[111].script=[t.errors.ChannelPrivateError(request=None)]
    reader=asyncio.create_task(t.read(e))
    if passive:
        result=await asyncio.wait_for(reader,2)
        assert result.account_id==222 and events
        # App-owned observer processing after the source call/settlement ended.
        await observer(events[0])
        assert actor_task.done() and e.pool._closed
        assert all(s._primary_client is None for s in e.pool._sources.values())
        emit('passive_events_predating_actor', source_settled_before_observer=True, close_completed=True)
        await e.pool.close()
        return
    await t.d.until(lambda:trigger.is_set());await t.turns(30)
    child=e.pool._sources[111].task
    assert not reader.done() and not actor_task.done() and child is not None and not child.done()
    assert getattr(child,'_fut_waiter',None) is actor_task
    assert any(getattr(task,'_fut_waiter',None) is reader for task in asyncio.all_tasks())
    emit('LIMIT_scope_only_predating_actor', actual_cycle=True, actor_inherits_scope=False,
         reader_done=False, sdk_disconnects_started=0)
    os._exit(42)


async def child_case(directory,passive):
    with candidate():await predating_actor(directory,passive)


async def main(directory):
    t.f.TMP=t.d.TMP=directory
    with candidate():
        try:
            for mode in ('raw','daily','success'):await own_cancel(mode)
            for kind in ('create_task','wait_for','backend'):await descendants(kind)
            await stale_context();await foreign_pool()
            for test in (t.test_external_cancel_remains_unresolved_and_no_failover,
                         t.test_repeated_read_cancellation_retains_the_actual_child,
                         t.test_close_cancellation_settles_all_sdk_cleanup_and_stays_closed,
                         t.test_observer_timeout_preserves_original_flood_and_prefix):
                await asyncio.wait_for(test(),10)
                emit('candidate_control', test=test.__name__, passed=True)
            for passive in (False,True):
                child_path=directory/('passive' if passive else 'inline');child_path.mkdir()
                process=await asyncio.create_subprocess_exec(sys.executable,__file__,'--child',str(child_path),str(int(passive)),
                    stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
                try:
                    stdout,stderr=await asyncio.wait_for(process.communicate(),10)
                    assert process.returncode==(0 if passive else 42),stderr.decode()
                    print(stdout.decode().strip(),flush=True)
                finally:
                    if process.returncode is None:process.kill();await process.wait()
        finally:
            for pool in t.POOLS:await pool.close()
            t.POOLS.clear()
    print('PASS14 concept histories:12 narrow controls,1 scope limitation,1 passive-observer alternative.',flush=True)


if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        if len(sys.argv)>1:
            asyncio.run(child_case(Path(sys.argv[2]),bool(int(sys.argv[3]))))
        else:
            with tempfile.TemporaryDirectory(prefix='tgdata17-innovation-') as directory:
                asyncio.run(main(Path(directory)))
