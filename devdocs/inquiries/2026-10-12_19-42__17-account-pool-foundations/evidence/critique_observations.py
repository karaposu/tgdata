"""Adversarial data-boundary checks on original pool/SDK/progress implementations."""
import asyncio
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from tgdata.smoke_tests import test_31_account_pool as t


async def capture(work):
    try:return await work
    except BaseException as error:return error


async def history(kind,observer_failure):
    events=[];trigger=asyncio.Event();holder={}
    async def external_controller():
        await trigger.wait();await holder['pool'].close()
    controller=asyncio.create_task(external_controller())
    e=await t.setup(callback=events.append,daily=t.SQLiteSyncStore(t.path('daily')),
                    history=t.SQLiteSyncStore(t.path('history')))
    holder['pool']=e.pool
    failure=t.errors.FloodWaitError(request=None,capture=7200)
    e.senders[111].script=[t.f.response([t.f.message(n) for n in reversed(range(101,201))]),failure]
    if kind=='raw':
        call=t.read(e,limit=200);context=None
    elif kind=='daily':
        await e.pool.initialize_sync(t.CHAT,after_id=100)
        call=e.pool.sync_group(t.CHAT,limit=200);context=None
    else:
        started=await e.pool.start_backfill(t.d.request(batch_size=200),submission='new')
        context=t.BackfillPrepareContext.from_status(started.status)
        call=e.pool.prepare_backfill(context)
    result=await capture(call)
    assert result is failure and len(result.partial_result.messages)==100 and events
    row=json.loads(await e.store.load())['accounts']['111']
    assert row['active'] is None and row['not_before']==t.f.NOW+7200
    assert e.budget.status(111).used==200 and not e.senders[222].reads
    if kind=='daily':
        assert (await e.pool.get_sync_status(t.CHAT)).pending_batch_id==failure.partial_result.batch_id
    if kind=='backfill':
        assert (await e.pool.get_backfill_status(context.run)).pending_batch_id==failure.partial_result.batch_id
    before=await e.store.load()
    # Application code receives observations only after the source/progress call
    # has returned. No pool/source/outcome method is patched to manufacture this.
    if observer_failure:
        async def observer():
            own=asyncio.get_running_loop().create_future();own.cancel();await own
        assert isinstance(await capture(observer()),asyncio.CancelledError)
        assert asyncio.current_task().cancelling()==0
        trigger.set();await asyncio.wait_for(controller,2)
    else:
        trigger.set();await asyncio.wait_for(controller,2)
    assert await e.store.load()==before and all(s._primary_client is None for s in e.pool._sources.values())
    count=len(e.senders[111].reads)
    if kind=='daily':
        replay=await e.pool.sync_group(t.CHAT,limit=200)
        assert replay.to_json()==failure.partial_result.to_json()
        await e.pool.acknowledge_sync(t.CHAT,replay.batch_id)
    if kind=='backfill':
        status=await e.pool.get_backfill_status(context.run)
        replay=await e.pool.prepare_backfill(t.BackfillPrepareContext.from_status(status))
        assert replay.replayed and replay.batch.to_json()==failure.partial_result.to_json()
        await e.pool.acknowledge_backfill(replay.delivery)
    assert len(e.senders[111].reads)==count and not e.senders[222].reads
    print(json.dumps(dict(case=kind,observer_own_cancel=observer_failure,prefix=100,stored_wait=7200,
        charge=200,controller_close_completed=True,replay_source_free=True)),flush=True)


async def main(directory):
    t.f.TMP=t.d.TMP=directory
    try:
        for kind in ('raw','daily','backfill'):
            for observer_failure in (False,True):await history(kind,observer_failure)
    finally:
        for pool in t.POOLS:await pool.close()
        t.POOLS.clear()
    print('PASS6 observation-boundary histories on original runtime; event API unimplemented.',flush=True)


if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        with tempfile.TemporaryDirectory(prefix='tgdata17-critique-') as directory:
            asyncio.run(main(Path(directory)))
