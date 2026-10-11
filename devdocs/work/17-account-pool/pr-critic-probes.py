"""Fresh PR #26 falsifiers: actual pool/SDK/SQLite with synthetic wire only."""
import asyncio
import json
import logging
import os
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tgdata.smoke_tests import test_31_account_pool as t


def emit(case, **values):
    print(json.dumps(dict(case=case, **values), sort_keys=True), flush=True)


async def capture(work):
    try:
        return await work
    except BaseException as error:
        return error


async def identity_after_page():
    e = await t.setup()
    # Initial proof, page allowance, first send, then a different actual account
    # at the second page's admission. The actual SDK and budget mixin do the work.
    e.senders[111].identities = [111, 111, 111, 222]
    error = await capture(t.read(e, limit=200))
    assert isinstance(error, t.PoolIdentityError)
    assert len(error.partial_result.messages) == 100
    assert len(e.senders[111].reads) == 1 and not e.senders[222].reads
    assert e.budget.status(111).used == 100 and e.budget.status(222).used == 0
    assert 'identity_mismatch' in (await e.pool.get_pool_status(t.CHAT)).accounts[0].reasons
    emit('identity_after_page', prefix=100, history_requests=1, charges=[100, 0], wrong_owner_requests=0)


async def preproof_logout():
    events = []
    e = await t.setup(callback=events.append)
    e.clients[111]._mb_entity_cache.set_self_user(999, False, 1)
    e.senders[111].auth_error = True
    result = await t.read(e)
    assert result.account_id == 222
    assert events[0]['account']['user_id'] is None
    assert 'logged_out' in (await e.pool.get_pool_status()).accounts[0].reasons
    assert not e.senders[111].reads
    emit('preproof_logout', selected=222, health_user_id=None, stale_cached_id=999, wrong_account_reads=0)


class DelayedStore:
    def __init__(self, actual, phase, committed):
        self.actual, self.phase, self.committed = actual, phase, committed
        self.entered, self.release = asyncio.Event(), asyncio.Event()
        self.hit = False

    async def load(self):
        return await self.actual.load()

    async def compare_and_swap(self, old, new):
        row = json.loads(new)['accounts']['111']
        active = row['active'] is not None
        target = active if self.phase == 'admission' else not active
        if self.hit or not target:
            return await self.actual.compare_and_swap(old, new)
        self.hit = True
        if self.committed:
            result = await self.actual.compare_and_swap(old, new)
        self.entered.set()
        await self.release.wait()
        return result if self.committed else await self.actual.compare_and_swap(old, new)


async def cancelled_remote_responses():
    for committed in (False, True):
        e = await t.setup()
        backend = DelayedStore(e.store, 'admission', committed)
        e.pool._store = backend
        task = asyncio.create_task(t.read(e))
        await backend.entered.wait()
        task.cancel()
        assert isinstance(await capture(task), asyncio.CancelledError)
        backend.release.set()
        assert not any(sender.calls for sender in e.senders.values())
        row = (await e.pool.get_pool_status()).accounts[0]
        assert (row.attempt_id is not None) is committed
        emit('cancelled_admission_response', commit_happened=committed,
             unresolved=row.attempt_id is not None, source_requests=0)
    e = await t.setup()
    backend = DelayedStore(e.store, 'settlement', True)
    e.pool._store = backend
    e.senders[111].script = [t.errors.FloodWaitError(request=None, capture=7200)]
    task = asyncio.create_task(t.read(e))
    await backend.entered.wait()
    task.cancel()
    assert isinstance(await capture(task), asyncio.CancelledError)
    backend.release.set()
    row = (await e.pool.get_pool_status()).accounts[0]
    assert row.retry_at == t.f.NOW + 7200 and row.attempt_id is None
    assert not e.senders[222].reads
    emit('cancelled_settlement_response', stored_wait=7200, unresolved=False, next_source_reads=0)


async def close_during_recheck():
    e = await t.setup()
    gate = t.CleanupGate(e.senders[111])
    reader = asyncio.create_task(e.pool.recheck_account(111))
    closer = None
    try:
        await gate.entered.wait()
        closer = asyncio.create_task(e.pool.close())
        await t.turns()
        closer.cancel()
        await t.turns()
        closer.cancel()
        await t.turns()
        assert not reader.done() and not closer.done()
        assert e.pool._active_task is reader and e.pool._closing
        gate.release.set()
        assert isinstance(await capture(reader), asyncio.CancelledError)
        assert isinstance(await capture(closer), asyncio.CancelledError)
        assert len(gate.tasks) == 1 and gate.tasks[0].done()
        assert all(s._primary_client is None for s in e.pool._sources.values())
        emit('close_during_recheck', sdk_retirements_first_client=1, all_clients_cleared=True,
             repeated_cancel_preserved=True, charges=0)
    finally:
        await gate.restore()
        if closer is not None:
            await asyncio.gather(closer, return_exceptions=True)
        await asyncio.gather(reader, return_exceptions=True)


async def local_transport_shaped_media_error():
    events = []
    e = await t.setup(callback=events.append)
    e.senders[111].files[t.b.ASSET_ID] = t.b.PAYLOAD
    e.senders[111].script = [t.d.finite_response([t.b.document()])]
    original = ConnectionResetError('synthetic local filesystem boundary')
    # Fail the real filesystem call, retaining _publish/_local_io provenance.
    with patch('tgdata.batch_files.os.link', side_effect=original):
        error = await capture(t.read(e, download_media_to=t.path('media')))
    assert error is original and not events and not e.senders[222].calls
    assert (await e.pool.get_pool_status(t.CHAT)).accounts[0].eligible
    emit('local_transport_shaped_media_error', original_error=True, health_events=0,
         next_source_requests=0, invented_restrictions=0)


async def pending_progress_without_source_resources():
    e = await t.setup(daily=t.SQLiteSyncStore(t.path('daily.sqlite3')),
                      history=t.SQLiteSyncStore(t.path('history.sqlite3')))
    await e.pool.initialize_sync(t.CHAT, after_id=100)
    daily = await e.pool.sync_group(t.CHAT, limit=1)
    start = await e.pool.start_backfill(t.d.request(), submission='new')
    e.senders[111].script = [t.d.finite_response([t.f.message(102), t.f.message(101)])]
    history = await e.pool.prepare_backfill(t.BackfillPrepareContext.from_status(start.status))
    await e.pool.close()
    for account in e.pool.accounts:
        Path(account.config_path).unlink()
    class Unavailable:
        async def load(self):
            raise AssertionError('source pool state touched during replay')
        async def compare_and_swap(self, *args):
            raise AssertionError('source pool state touched during replay')
    e.pool._store = Unavailable()
    with patch.object(e.budget, 'status', side_effect=AssertionError('budget touched during replay')):
        replay = await e.pool.sync_group(t.CHAT, limit=1)
        assert replay.batch_id == daily.batch_id
        await e.pool.acknowledge_sync(t.CHAT, replay.batch_id)
        turn = await e.pool.prepare_backfill(t.BackfillPrepareContext.from_status(history.status))
        assert turn.replayed and turn.delivery == history.delivery
        accepted = await e.pool.acknowledge_backfill(turn.delivery)
        assert accepted.after_id == 102
    emit('pending_progress_without_source_resources', closed_pool=True, configs_removed=True,
         pool_state_unavailable=True, budget_forbidden=True, daily_ack=101, historical_ack=102)


async def cancelled_observer_result():
    async def callback(event):
        response = asyncio.get_running_loop().create_future()
        response.cancel()  # Observer's own awaited resource, not caller cancellation.
        await response
    for mode in ('raw', 'daily'):
        e = await t.setup(callback=callback, daily=t.SQLiteSyncStore(t.path('daily.sqlite3')))
        await e.pool.initialize_sync(t.CHAT, after_id=100)
        original = t.errors.FloodWaitError(request=None, capture=7200)
        e.senders[111].script = [t.f.response([t.f.message(n) for n in reversed(range(101, 201))]), original]
        call = t.read(e, limit=200) if mode == 'raw' else e.pool.sync_group(t.CHAT, limit=200)
        error = await capture(call)
        row = json.loads(await e.store.load())['accounts']['111']
        pending = (await e.pool.get_sync_status(t.CHAT)).pending_batch_id
        assert isinstance(error, asyncio.CancelledError)
        assert asyncio.current_task().cancelling() == 0 and error is not original
        assert len(original.partial_result.messages) == 100
        assert getattr(error, 'partial_result', None) is None and pending is None
        assert row['active'] is not None and row['not_before'] == 0
        emit('REPRODUCED_observer_cancel_masks_source', mode=mode, caller_cancel_requests=0,
             returned_error=type(error).__name__, actual_source_error=type(original).__name__,
             completed_prefix=100, returned_prefix=0, daily_pending=False,
             actual_wait=7200, stored_wait=0, unresolved=True)


async def callback_close_child(directory):
    t.f.TMP = t.d.TMP = directory
    holder = {}
    async def callback(event):
        # Creating and awaiting a task (also what wait_for does) remains a
        # callback-initiated close. No pool/source/cleanup method is replaced.
        holder['close'] = asyncio.create_task(holder['pool'].close())
        await holder['close']
    e = await t.setup(callback=callback)
    holder['pool'] = e.pool
    e.senders[111].script = [t.errors.ChannelPrivateError(request=None)]
    reader = asyncio.create_task(t.read(e))
    await t.d.until(lambda: 'close' in holder)
    await t.turns(30)
    close = holder['close']
    child = e.pool._sources[111].task
    cycle = (not reader.done() and not close.done() and child is not None and not child.done()
             and getattr(child, '_fut_waiter', None) is close
             and any(getattr(work, '_fut_waiter', None) is reader for work in asyncio.all_tasks()))
    assert cycle and e.pool._closing and e.pool._closed
    emit('REPRODUCED_callback_close_wait_cycle', reader_done=False, source_child_done=False,
         close_done=False, child_waits_for_close=True, cleanup_waits_for_reader=True,
         reader_cancel_requests=reader.cancelling(), close_cancel_requests=close.cancelling(),
         sdk_disconnects_started=sum(not sender.up for sender in e.senders.values()))
    # The reproduced ownership cycle cannot be unwound by cancelling these tasks.
    # This probe owns the whole offline subprocess; terminate it after evidence.
    os._exit(42)


async def callback_close_cycle(directory):
    process = await asyncio.create_subprocess_exec(sys.executable, __file__, '--callback-close-child',
        str(directory), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), 10)
        assert process.returncode == 42, stderr.decode()
        result = json.loads(stdout.decode())
        assert result['child_waits_for_close'] and result['cleanup_waits_for_reader']
        print(stdout.decode().strip(), flush=True)
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


async def main(directory):
    t.f.TMP = t.d.TMP = directory
    tests = [identity_after_page, preproof_logout, cancelled_remote_responses,
             close_during_recheck, local_transport_shaped_media_error,
             pending_progress_without_source_resources, cancelled_observer_result]
    try:
        for test in tests:
            await asyncio.wait_for(test(), 25)
        child_directory = directory / 'child'
        child_directory.mkdir()
        await callback_close_cycle(child_directory)
    finally:
        for pool in t.POOLS:
            await pool.close()
        t.POOLS.clear()
    print('Completed 8 fresh probe groups: 6 held; 2 defects reproduced.', flush=True)


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        if len(sys.argv) > 1:
            asyncio.run(callback_close_child(Path(sys.argv[2])))
        else:
            with tempfile.TemporaryDirectory(prefix='tgdata17-pr-critic-') as directory:
                asyncio.run(main(Path(directory)))
