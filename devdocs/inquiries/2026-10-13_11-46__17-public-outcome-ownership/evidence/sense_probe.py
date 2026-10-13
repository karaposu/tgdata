"""Observe current pool operation and public-task boundaries; no candidate patch."""
import asyncio
import hashlib
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from tgdata.smoke_tests import test_31_account_pool as t
from tgdata.smoke_tests import pool_storage_cases as s

async def capture(work):
    try:return await work
    except BaseException as error:return error

def count(value):return len(getattr(getattr(value,'partial_result',None),'messages',()))

async def prepared_wait():
    e,state,_,_=await s.setup('raw');s.source(e,False)
    entered=asyncio.Event();calls=[0];actual=state.compare_and_swap
    async def held(*args):
        calls[0]+=1
        if calls[0]!=2:return await actual(*args)
        entered.set()
        try:await asyncio.Event().wait()
        finally:await actual(*args)
    state.compare_and_swap=held
    return e,entered

async def public_composition():
    rows=[]
    for kind in ('direct','wait','gather_raise','gather_values','shield','wait_for'):
        e,entered=await prepared_wait();seen={}
        async def call():
            try:return await t.read(e)
            except asyncio.CancelledError as error:
                seen['inside']=count(error)
                raise
        reader=asyncio.create_task(call());await entered.wait()
        async def observe():
            if kind=='wait':
                await asyncio.wait((reader,));return reader.result()
            if kind=='gather_raise':return (await asyncio.gather(reader))[0]
            if kind=='gather_values':return (await asyncio.gather(reader,return_exceptions=True))[0]
            if kind=='shield':return await asyncio.shield(reader)
            if kind=='wait_for':return await asyncio.wait_for(reader,0.02)
            return await reader
        observer=asyncio.create_task(capture(observe()));await t.turns()
        if kind!='wait_for':reader.cancel()
        result=await observer
        row=dict(kind=kind,inside_records=seen['inside'],public_type=type(result).__name__,
                 public_records=count(result),cause_records=count(getattr(result,'__cause__',None)),
                 task_cancelled=reader.cancelled(),charge=e.budget.status(111).used,
                 close_was_called=False)
        assert seen['inside']==1 and e.budget.status(111).used==1 and reader.cancelled()
        assert count(result)==(1 if kind in ('direct','wait','gather_raise') else 0)
        if kind=='wait_for':assert isinstance(result,TimeoutError) and count(result.__cause__)==1
        rows.append(row)
        await e.pool.close()
    return rows

async def application_continuation(mode):
    e,state,_,context=await s.setup(mode);s.source(e,False)
    entered,handler,release=asyncio.Event(),asyncio.Event(),asyncio.Event();calls=[0];seen={}
    actual=state.compare_and_swap
    async def held(*args):
        calls[0]+=1
        if calls[0]!=2:return await actual(*args)
        entered.set()
        try:await asyncio.Event().wait()
        finally:await actual(*args)
    state.compare_and_swap=held
    async def application():
        try:return await s.read(e,mode,context,1)
        except asyncio.CancelledError as error:
            seen['records']=count(error);handler.set()
            # Ordinary application cleanup after tgdata has already raised.
            # It need not use Telegram or any pool/provider API.
            await release.wait()
            raise
    caller=asyncio.create_task(application());closer=None
    try:
        await entered.wait();closer=asyncio.create_task(e.pool.close());await handler.wait();await t.turns()
        record=dict(mode=mode,read_coroutine_already_raised=True,records_at_application=seen['records'],
            pool_slot_released=e.pool._active_task is None,
            source_children_ended=all(src.task is None for src in e.pool._sources.values()),
            provider_tasks_ended=all(task.done() for task in state.tasks),
            close_still_waiting=not closer.done(),clients_retired=all(src._primary_client is None for src in e.pool._sources.values()))
        assert record['pool_slot_released'] and record['source_children_ended'] and record['provider_tasks_ended']
        assert record['close_still_waiting'] and not record['clients_retired'] and seen['records']==1
        release.set();await capture(caller);await closer
        record['close_finishes_after_app_release']=closer.done()
        return record
    finally:
        release.set();await asyncio.gather(caller,*([closer] if closer else []),return_exceptions=True)

async def inherited_controls():
    tests=[t.test_real_pagination_and_drain_budget,t.test_changed_identity_at_admission_never_sends_history,
           t.test_uncertain_admission_opens_no_source_and_survives_restart,
           t.test_settlement_failure_preserves_data_and_daily_replay,
           t.test_recheck_cancellation_holds_ownership_until_sdk_disconnect,
           t.test_actual_cleanup_failure_keeps_body_error_and_can_be_retried]
    for test in tests:
        await test()
        for pool in t.POOLS:await pool.close()
        t.POOLS.clear()
    return [test.__name__ for test in tests]

async def main(directory):
    t.f.TMP=t.d.TMP=directory
    print(json.dumps(dict(runtime=sys.version.split()[0],task_type=asyncio.Task.__module__+'.'+asyncio.Task.__name__)),flush=True)
    print(json.dumps(dict(public_composition=await public_composition())),flush=True)
    for mode in ('raw','daily','backfill'):
        print(json.dumps(dict(application_continuation=await application_continuation(mode))),flush=True)
    print(json.dumps(dict(inherited_controls=await inherited_controls())),flush=True)
    for pool in t.POOLS:await pool.close()
    print('PASS: observations match actual source/store/task histories.',flush=True)

if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='tgdata17-sense-') as directory, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        asyncio.run(main(Path(directory)))
