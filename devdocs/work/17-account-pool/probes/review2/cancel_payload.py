"""Isolate cancellation-payload consumption using actual pool and C asyncio Tasks."""
import asyncio
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
from tgdata.smoke_tests import test_31_account_pool as t
from tgdata.smoke_tests import pool_storage_cases as s

async def history(mode,waiting,stop_closer):
    e,state,_,context=await s.setup(mode);s.source(e,False)
    original=state.compare_and_swap;calls=[0];inner={}
    entered,finalizing,release=asyncio.Event(),asyncio.Event(),asyncio.Event()
    async def held(*args):
        calls[0]+=1
        if calls[0]!=2:return await original(*args)
        entered.set()
        try:await asyncio.Event().wait()
        finally:
            finalizing.set();await release.wait();await original(*args)
    state.compare_and_swap=held
    async def read():
        try:return await s.read(e,mode,context,1)
        except asyncio.CancelledError as error:
            inner['prefix']=len(error.partial_result.messages)
            inner['exception_id']=id(error)
            raise
    reader=asyncio.create_task(read());receiver=None;closer=None
    try:
        await entered.wait()
        if waiting:
            receiver=asyncio.create_task(s.capture(reader))
            await t.turns()  # Register the public receiver before close's own await.
        closer=asyncio.create_task(e.pool.close());await finalizing.wait()
        if stop_closer:
            closer.cancel();await t.turns();closer.cancel();await t.turns()
        assert not reader.done() and not closer.done()
        release.set()
        error=await receiver if receiver else await s.capture(reader)
        close_result=await s.capture(closer)
        public=len(getattr(getattr(error,'partial_result',None),'messages',()))
        assert isinstance(error,asyncio.CancelledError) and inner['prefix']==1
        assert public==(1 if waiting else 0), (mode,waiting,public)
        assert all(src._primary_client is None for src in e.pool._sources.values())
        if mode!='raw':assert await s.pending(e,mode,context) is None
        row=json.loads(await state.actual.load())['accounts']['111']
        assert row['active'] is None and e.budget.status(111).used==1
        return dict(mode=mode,public_waiter_registered_first=waiting,repeated_close_cancel=stop_closer,
            before_task_termination_prefix=inner['prefix'],public_prefix=public,
            same_exception=id(error)==inner['exception_id'],pool_settled=True,
            pending_delivery=False,charge=1,all_clients_retired=True,
            close_result=type(close_result).__name__)
    finally:
        release.set();await asyncio.gather(reader,*([closer] if closer else []),return_exceptions=True)
        if receiver is not None:await asyncio.gather(receiver,return_exceptions=True)

async def task_control():
    entered=asyncio.Event()
    async def body():
        try:entered.set();await asyncio.Event().wait()
        except asyncio.CancelledError as error:error.payload='owned-value';raise
    task=asyncio.create_task(body());await entered.wait();task.cancel()
    first=await s.capture(task);second=await s.capture(task)
    assert getattr(first,'payload',None)=='owned-value' and not hasattr(second,'payload')
    return dict(task_type=type(task).__module__+'.'+type(task).__name__,first_has_payload=True,
                second_has_payload=False,same_exception=first is second)

async def main(directory):
    t.f.TMP=t.d.TMP=directory
    print(json.dumps(dict(control=await task_control())),flush=True)
    for mode in ('raw','daily','backfill'):
        for waiting in (False,True):
            for stop in (False,True):
                print(json.dumps(await history(mode,waiting,stop)),flush=True)
                for pool in t.POOLS:await pool.close()
                t.POOLS.clear()
    print('Mechanism reproduced in 12 actual pool histories; no production patch.',flush=True)

if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='tgdata17-payload-') as directory, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        asyncio.run(main(Path(directory)))
