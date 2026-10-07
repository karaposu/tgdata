"""Controlled local interruptions around actual raw reads; no lifecycle transitions."""
import asyncio
import importlib.util
import json
import logging
import os
from pathlib import Path
import sys

ROOT=Path('/private/tmp/tgdata19-gate-a-live-20261007')
REPO=Path('/private/tmp/tgdata-19-backfill-run-lifecycle')
sys.path.insert(0,str(REPO))
spec=importlib.util.spec_from_file_location('probe',REPO/'devdocs/work/19-backfill-run-lifecycle/live_probe.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
from telethon import functions
from tgdata import TgData,ReadBudget


def unwrap(request):
    while isinstance(request,p._WRAPPERS):request=request.query
    return request


async def main():
    manifest=p.manifest_from_text((ROOT/'exact_full_followup.manifest.json').read_text())
    store,status,original=await p.preflight(manifest,ROOT/'exact_full_followup.sqlite3')
    account=int(manifest['expected_account_id'])
    budget=ReadBudget(ROOT/'account-read-budget.sqlite3')
    guard=p.ReadOnlyGuard(status.run.chat_id,dict(max_rpc_requests=60,max_history_requests=3,
        max_requested_slots=30,max_media_bytes=0))
    tg=TgData('/Users/ns/Desktop/projects/telegram-group-scraper/config.ini',interactive_login=False,
              connection_pool_size=1,read_budget=budget)
    factory=tg.connection_engine._new_client
    def instrumented(*a,**kw):
        client=factory(*a,**kw);guard.instrument(client);client.flood_sleep_threshold=0
        return client
    tg.connection_engine._new_client=instrumented
    report=dict(kind='LIVE source with INJECTED local cancellation/refusal',gate_verdict='INCONCLUSIVE',
                budget_used_before=budget.status(account).used)
    try:
        client=await tg.connection_engine.get_client()
        p.require((await client.get_me(input_peer=False)).id==account,'wrong_account')
        guarded_call=client._call
        answered=asyncio.Event()
        release=asyncio.Event()
        async def hold_answer(sender,request,ordered=False,flood_sleep_threshold=None):
            result=await guarded_call(sender,request,ordered=ordered,flood_sleep_threshold=flood_sleep_threshold)
            if isinstance(unwrap(request),functions.messages.GetHistoryRequest):
                report['answered_before_cancellation']=len(result.messages)
                answered.set()
                await release.wait()
            return result
        client._call=hold_answer
        before_cancel=budget.status(account).used
        task=asyncio.create_task(tg.get_message_batch(status.run.chat_id,after_id=0,limit=5,
            start_date=status.start_date,end_date=status.end_date))
        try:
            await asyncio.wait_for(answered.wait(),20)
            task.cancel()
            try:await task
            except asyncio.CancelledError:report['cancellation_propagated']=True
            else:raise p.ProbeStop('cancelled_read_returned_normally')
        finally:
            task.cancel()
            try:await task
            except asyncio.CancelledError:pass
            client._call=guarded_call
        report['cancelled_read_charge']=budget.status(account).used-before_cancel
        p.require(report['cancelled_read_charge']==report['answered_before_cancellation'],'cancelled_read_charge_lost')
        await asyncio.sleep(5)
        full=await tg.get_message_batch(status.run.chat_id,after_id=0,limit=9,
            start_date=status.start_date,end_date=status.end_date)
        p.require(full.stop_reason=='limit' and len(full.messages)==9,'expected_full_prefix')
        guard.limits['max_history_requests']=guard.history_count  # refuse next actual send
        before_refusal=len(guard.rpc)
        before_refused_charge=budget.status(account).used
        try:
            await tg.get_message_batch(status.run.chat_id,after_id=full.next_after_id,limit=9,
                start_date=status.start_date,end_date=status.end_date)
        except p.ProbeStop as error:
            part=getattr(error,'partial_result',None)
            p.require(str(error)=='history_cap_reached' and part is not None,'wrong_refusal')
            p.require(part.stop_reason=='interrupted' and len(part.messages)==0,'refusal_faked_end')
            report['full_batch_then_refusal']=dict(first_stop=full.stop_reason,
                refused_stop=part.stop_reason,refused_records=len(part.messages),
                additional_history_sends=sum(x['kind']=='GetHistoryRequest' for x in guard.rpc[before_refusal:]),
                conservative_charge=budget.status(account).used-before_refused_charge)
        else:raise p.ProbeStop('expected_refusal_not_observed')
        report['checks_passed']=True
    except Exception as e:
        report['error_type']=type(e).__name__
        if isinstance(e,p.ProbeStop):report['stop_code']=str(e)
    finally:
        await asyncio.wait_for(tg.close(),10)
        report['lifecycle_state_unchanged']=await store.load(status.run.chat_id)==original
        report['budget_used_after']=budget.status(account).used
        report['rpc']=guard.rpc
        with (ROOT/'interruption.live.json').open('x') as f:json.dump(report,f,sort_keys=True,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='rpc'},sort_keys=True))
    return 0 if report.get('checks_passed') and report['lifecycle_state_unchanged'] else 2


if __name__=='__main__':
    os.umask(0o077);os.chdir('/Users/ns/Desktop/projects/telegram-group-scraper')
    logging.disable(logging.CRITICAL)
    sys.exit(asyncio.run(asyncio.wait_for(main(),120)))
