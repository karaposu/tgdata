"""Prosecute the concept's public-progress/lifetime boundary; no product patch."""
import asyncio
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import concept_probe as c
from tgdata.smoke_tests import test_31_account_pool as t
from tgdata.smoke_tests import pool_storage_cases as s

async def publication_after_close(mode):
    e,state,provider,context=await s.setup(mode)
    c.candidate(e.pool);s.source(e,False)
    entered,release=asyncio.Event(),asyncio.Event();calls=[0]
    actual=provider.compare_and_swap
    async def held(*args):
        calls[0]+=1
        if calls[0] == (1 if mode=='daily' else 2):
            entered.set();await release.wait()
        return await actual(*args)
    provider.compare_and_swap=held
    recipient=c.Recipient()
    reader=asyncio.create_task(recipient.run(lambda:s.read(e,mode,context,1)))
    try:
        await entered.wait()
        assert e.pool._active_task is None and recipient.phase=='running'
        await e.pool.close()
        assert not reader.done() and recipient.phase=='running' and recipient.batch is None
        assert all(source._primary_client is None for source in e.pool._sources.values())
        assert not any(task.done() is False for task in state.tasks)
        release.set();result=await reader
        assert c.count(recipient)==1 and recipient.signal=='returned'
        assert await s.pending(e,mode,context) is not None
        charge=e.budget.status(111).used
        assert charge==1
        return dict(mode=mode,close_done_before_publication=True,recipient_running_before_release=True,
                    provisional_data_visible=False,final_records=c.count(recipient),pending=True,charge=charge)
    finally:
        release.set();await asyncio.gather(reader,return_exceptions=True)

async def prestart():
    e,state,_,_=await s.setup('raw');c.candidate(e.pool)
    recipient=c.Recipient()
    calls=dict(state.counts)
    task=asyncio.create_task(recipient.run(lambda:t.read(e)))
    task.cancel();result=await s.capture(task)
    assert isinstance(result,asyncio.CancelledError) and recipient.phase=='new'
    assert state.counts==calls and not any(sender.calls for sender in e.senders.values())
    await e.pool.close()
    return dict(task_cancelled=True,recipient_state='new',io=False,
                inference='no started invocation; not a finished read with an empty batch')

async def main(directory):
    t.f.TMP=t.d.TMP=directory
    rows=[await publication_after_close(mode) for mode in ('daily','backfill')]
    rows.append(await prestart())
    for pool in t.POOLS:await pool.close()
    print(json.dumps(rows,indent=2))
    print('PASS: three adversarial concept observations; early-data publication not implemented by the adapter.')

if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='tgdata17-critique-') as directory, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        asyncio.run(main(Path(directory)))
