import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

REPO=Path('/private/tmp/tgdata-19-backfill-run-lifecycle')
ROOT=Path('/private/tmp/tgdata19-gate-a-live-20261007')
sys.path.insert(0,str(REPO))
from tgdata import SQLiteSyncStore
from tgdata.backfill import BackfillStartRequest
from tgdata.backfill_engine import BackfillEngine
from tgdata.history_window import _decode_date,_encode_date


async def main():
    original=json.loads((ROOT/'qualification-6.json').read_text())
    rows={int(row['id']):row for row in original['messages']}
    chat=int(original['chat_id'])
    date=lambda ident:_decode_date(rows[ident]['date'])
    cases=[
        ('boundaries_and_gaps',dict(start_date=date(1),end_date=date(51),batch_size=10)),
        ('exact_full_followup',dict(start_date=date(1),end_date=date(15),batch_size=9)),
        ('empty_window',dict(start_date=datetime(2026,9,29,tzinfo=timezone.utc),
                            end_date=datetime(2026,10,1,tzinfo=timezone.utc),batch_size=10)),
        ('imported_tail',dict(start_date=date(1),end_date=date(51),after_id=34,origin='imported',batch_size=7)),
        ('relative_restart',dict(last_days=10,batch_size=10)),
        ('media_imported',dict(start_date=date(14),end_date=date(14)+timedelta(microseconds=1),
                              after_id=13,origin='imported',media_mode='download',batch_size=5)),
    ]
    for name,options in cases:
        state=ROOT/(name+'.sqlite3')
        if state.exists():raise RuntimeError('refusing to overwrite '+name)
        request=BackfillStartRequest(collection_id='gate-a-'+name,chat_id=chat,
            run_id='20261007-'+name,destination_id='gate-a-diagnostic',pause_seconds=5,
            expected_predecessor=None,**options)
        store=SQLiteSyncStore(state)
        status=(await BackfillEngine(store,request.collection_id).start(request,submission='new')).status
        manifest=dict(schema='tgdata.backfill-probe',version=1,run=status.run.to_dict(),
            start_request=request.to_dict(),window=dict(start_date=_encode_date(status.start_date),
                end_date=_encode_date(status.end_date)),expected_account_id=original['account_id'],
            oracle=dict(method='independent_client',reference='UNQUALIFIED until the post-enrollment snapshot',
                captured_at=original['captured_at'],complete=False,messages=[]),
            limits=dict(max_rpc_requests=100,max_history_requests=10,max_requested_slots=1000,
                max_media_bytes=4*1024*1024 if status.media_mode=='download' else 0,
                timeout_seconds=180,spacing_seconds=5))
        (ROOT/(name+'.manifest.json')).write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
        print('Created',name,status.start_date,status.end_date,flush=True)


if __name__=='__main__':asyncio.run(main())
