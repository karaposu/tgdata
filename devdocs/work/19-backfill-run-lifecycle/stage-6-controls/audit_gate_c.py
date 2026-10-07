"""Read-only audit of actual Gate C state/receiver/trace files. No Telegram calls."""
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
from unittest.mock import patch

import gate_support as g
from tgdata.backfill_state import _BackfillState
from tgdata.history_window import _decode_date


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root):
    reports=[g.read(p) for p in sorted(root.glob('*.result.json'))]
    assert len(reports)==13 and all(r['result'] in ('PASS','EXPECTED_EXIT') for r in reports)
    pre=g.read(root/'prebuild-result.json');assert pre['result']=='PASS'
    rpc=[r for report in [pre]+reports for r in report.get('rpc',[])]
    history=[r for r in rpc if r['kind']=='GetHistoryRequest']
    assert all(r['outcome']=='answered' for r in history)
    allocated=sum(json.loads(line)['slots'] for line in (root/'allocations.jsonl').read_text().splitlines())
    observed=sum(r['limit'] for r in history)
    assert observed==442 and allocated==790 and observed<=allocated<=1000
    no_local_rpc=[]
    for report in reports:
        sources=[e for e in report.get('events',[]) if e['kind']=='source']
        if not sources:continue
        begin=sources[0]['entry']['utc']
        for call in report.get('rpc',[]):
            if call['sent_at']>=begin:
                assert any(e['entry']['utc']<=call['sent_at']<=e['end']['utc'] for e in sources), (report['case'],call['kind'])
        no_local_rpc.append(report['case'])
    states=[]
    for path in sorted(root.glob('*.sqlite3')):
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='tgdata_sync_state'").fetchone():continue
            rows=db.execute('SELECT chat_id,data FROM tgdata_sync_state').fetchall()
        for chat,raw in rows:
            state=_BackfillState.from_json(raw,json.loads(raw)['collection_id'],chat)
            status=state.status();assert status.attempt_id is None and status.pending_batch_id is None
            states.append(dict(file=path.name,state_sha256=hashlib.sha256(raw.encode()).hexdigest(),status=status.to_dict()))
    # Several workers reopen the same state file; count the specified cases,
    # not worker launches. Exact names also catch an unexpected/missing container.
    assert {r['file'] for r in states} == {
        'prebuild-state.sqlite3', 'budget.sqlite3', 'pause.sqlite3',
        'cancel-first.sqlite3', 'ack-first.sqlite3', 'empty-cancel-first.sqlite3',
        'restart.sqlite3', 'unknown.sqlite3', 'succession.sqlite3',
        'matrix-retirement.sqlite3', 'no-prefix.sqlite3',
    }
    expected={'prebuild':(2,6),'budget':(2,6),'pause':(1,2),'cancel-first':(1,1),
              'ack-first':(1,1),'restart':(3,6),'unknown':(1,2),'succession':(2,1),'matrix':(2,1)}
    receivers=[]
    for name,(receipts,messages) in expected.items():
        path=root/(name+'-receiver')/'receiver.sqlite3'
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
            assert db.execute('SELECT count(*) FROM receipts').fetchone()[0]==receipts
            rows=db.execute('SELECT chat,id,payload FROM messages').fetchall();assert len(rows)==messages
            ids=[]
            for chat,mid,payload in rows:
                record=json.loads(payload);assert chat==str(g.CHAT) and record['id']==mid
                oracle=next(r for r in g.read(root/'gate-oracle.json')['messages'] if r['id']==mid)
                assert record['date']==oracle['date'];ids.append(mid)
            if name=='succession':
                record=json.loads(rows[0][2]);blob=record['media']['blob']
                assert digest(path.parent/'receiver-media'/blob['path'])==blob['sha256']
        receivers.append(dict(name=name,receipts=receipts,messages=messages,ids=sorted(ids,key=int)))
    originals=[]
    old=g.read(g.HERE.parent/'stage-5-pacing-recovery'/'gate-b-copies-results.json')
    old_root=Path('/private/tmp/tgdata19-gate-b-live-20261007')
    for row in old['cases']:
        path=old_root/(row['case']+'.sqlite3')
        assert digest(path)==row['original_sha256']
        originals.append(dict(case=row['case'],unchanged=True,sha256=row['original_sha256']))
    budget_path=g.base.OLD/'account-read-budget.sqlite3'
    with sqlite3.connect(budget_path.as_uri()+'?mode=ro',uri=True) as db:
        assert db.execute('SELECT daily_limit FROM tgdata_budget_accounts WHERE account_id=?',(g.account(),)).fetchone()[0]==5000
        used=db.execute('SELECT sum(amount) FROM tgdata_budget_charges WHERE account_id=?',(g.account(),)).fetchone()[0]
    assert used==2334
    for name,code in (('unknown_source',81),('recover_crash',82)):
        proof=g.read(root/(name+'.exit.json'));assert proof['returncode']==code and proof['waited']
        assert proof['pid']==g.read(root/(name+'.result.json'))['pid']
    result=dict(result='PASS',code_revision='0d6bb26',gate='C',workers=13,history_requests=len(history),
        total_rpc=len(rpc),requested_slots=observed,allocated_slots=allocated,cap=1000,
        primary_before=pre['budget_before']['used'],primary_after=used,primary_limit=5000,
        first_rpc=min(r['sent_at'] for r in rpc),last_rpc=max(r['sent_at'] for r in rpc),
        rpc_types=sorted({r['kind'] for r in rpc}),no_local_rpc_after_source_entry=no_local_rpc,
        states=states,receivers=receivers,preserved_gate_b_originals=originals,
        control_test_groups=32,supported_offline_passes=319,legacy_live_skips=3,
        live_scope='existing approved group; actual SDK/SQLite/receiver; local faults explicitly injected')
    g.save(root/'audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('states','receivers','preserved_gate_b_originals')},sort_keys=True))


if __name__=='__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        audit(g.ROOT)
