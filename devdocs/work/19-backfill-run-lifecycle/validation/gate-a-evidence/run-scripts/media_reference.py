"""Independent hash of one selected in-window photo; no batch-reader/download wrapper."""
import asyncio
import hashlib
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
from telethon import functions,types
from tgdata import TgData,ReadBudget


async def main():
    manifest=json.loads((ROOT/'media_imported.manifest.json').read_text())
    expected=manifest['oracle']['messages']
    assert len(expected)==1 and expected[0]['id']=='14'
    chat=int(manifest['run']['chat_id']);account=int(manifest['expected_account_id'])
    budget=ReadBudget(ROOT/'account-read-budget.sqlite3')
    guard=p.ReadOnlyGuard(chat,dict(max_rpc_requests=40,max_history_requests=1,
        max_requested_slots=1,max_media_bytes=4*1024*1024),allow_media=True)
    tg=TgData('/Users/ns/Desktop/projects/telegram-group-scraper/config.ini',
              interactive_login=False,connection_pool_size=1,read_budget=budget)
    factory=tg.connection_engine._new_client
    def instrumented(*a,**kw):
        client=factory(*a,**kw);guard.instrument(client);client.flood_sleep_threshold=0
        client._request_retries=0;return client
    tg.connection_engine._new_client=instrumented
    report=dict(method='direct GetHistory then SDK download_media(bytes), separate from batch/blob engine',
                budget_used_before=budget.status(account).used)
    try:
        async def capture():
            client=await tg.connection_engine.get_client()
            p.require((await client.get_me(input_peer=False)).id==account,'wrong_account')
            peer=await client.get_input_entity(chat)
            result=await client(functions.messages.GetHistoryRequest(peer,15,None,0,1,0,0,0),flood_sleep_threshold=0)
            p.require(len(result.messages)==1 and result.messages[0].id==14,'unexpected_media_message')
            message=result.messages[0]
            p.require(p._encode_date(message.date)==expected[0]['date'],'media_date_drift')
            p.require(isinstance(message.media,types.MessageMediaPhoto),'not_selected_photo')
            data=await client.download_media(message,file=bytes)
            p.require(isinstance(data,bytes) and bool(data),'missing_photo_bytes')
            report['blob']=dict(sha256=hashlib.sha256(data).hexdigest(),size=len(data))
            report['message_id']='14'
        await asyncio.wait_for(capture(),120)
    except Exception as e:
        report['error_type']=type(e).__name__
        if isinstance(e,p.ProbeStop):report['stop_code']=str(e)
    finally:
        await asyncio.wait_for(tg.close(),10)
        report['rpc']=guard.rpc;report['requested_media_bytes']=guard.media_bytes
        report['budget_used_after']=budget.status(account).used
        with (ROOT/'media-reference.json').open('x') as f:json.dump(report,f,sort_keys=True,indent=2)
    if 'blob' in report and 'error_type' not in report:
        expected[0]['blob']=report['blob'];manifest['oracle']['complete']=True
        manifest['oracle']['reference']+='; media-reference.json direct SDK bytes hash'
        (ROOT/'media_imported.manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rpc'},sort_keys=True))
    return 0 if 'blob' in report and 'error_type' not in report else 2


if __name__=='__main__':
    os.umask(0o077);os.chdir('/Users/ns/Desktop/projects/telegram-group-scraper')
    logging.disable(logging.CRITICAL)
    sys.exit(asyncio.run(main()))
