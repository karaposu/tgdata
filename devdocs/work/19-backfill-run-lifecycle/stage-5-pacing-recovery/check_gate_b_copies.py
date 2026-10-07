"""LOCAL recovery of LIVE-origin Gate B state copies; never a Gate C result."""
import asyncio
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from tgdata import SQLiteSyncStore
from tgdata.backfill import BackfillStartRequest
from tgdata.backfill_engine import BackfillEngine
from tgdata.read_budget import ReadBudget

ROOT=Path('/private/tmp/tgdata19-gate-b-live-20261007')
BUDGET=Path('/private/tmp/tgdata19-gate-a-live-20261007/account-read-budget.sqlite3')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def forbidden():raise AssertionError('recognized recovery must not sample clocks')


async def main():
    before_budget=digest(BUDGET);observations=[]
    with tempfile.TemporaryDirectory(prefix='tgdata19_stage5_gate_b_copies_') as tmp:
        for name in ('empty_uncommitted','unknown_source'):
            original=ROOT/(name+'.sqlite3');before=digest(original)
            copy=Path(tmp)/(name+'.sqlite3')
            with sqlite3.connect(original.as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(str(copy)) as target:
                source.backup(target)
            case=json.loads((ROOT/(name+'.case.json')).read_text())
            request=BackfillStartRequest.from_dict(case['request'])
            store=SQLiteSyncStore(copy,create=False);engine=BackfillEngine(store,request.collection_id)
            old=(await engine.start(request,submission='retry')).status
            assert old.attempt_id and not old.source_exhausted and old.pending_batch_id is None
            args=dict(attempt_id=old.attempt_id,command_id='stage5-copy-check',
                      expected_control_revision=old.control_revision,previous_reader_stopped=True)
            # Gate B's recorded subprocess exit codes establish original worker exit;
            # no source reader is started here and no actual original row is cleared.
            result=await engine.recover(old.run,**args)
            assert result.applied and result.status.after_id==old.after_id
            assert result.status.attempt_id is None and not result.status.source_exhausted
            assert result.status.terminal_outcome is None and result.status.pending_batch_id is None
            raw=await store.load(request.chat_id)
            reopened=BackfillEngine(SQLiteSyncStore(copy,create=False),request.collection_id,
                                   clock=forbidden,monotonic_ns=forbidden)
            retry=await reopened.recover(old.run,**args)
            assert not retry.applied and retry.status==result.status
            assert await store.load(request.chat_id)==raw and digest(original)==before
            observations.append(dict(case=name,applied=result.applied,after_id=str(result.status.after_id),
                source_exhausted=result.status.source_exhausted,terminal=result.status.terminal_outcome,
                retry_applied=retry.applied,original_unchanged=True,
                pause_seconds=result.status.pause_seconds,ended_at=result.status.pacing_ended_at,
                original_sha256=before))
    assert digest(BUDGET)==before_budget
    print(json.dumps(dict(result='PASS',evidence='LOCAL actual recovery of LIVE-origin copies',
        cases=observations,source_calls=0,original_budget_unchanged=True,
        recorded_at=datetime.now(timezone.utc).isoformat(),gate_c='PENDING after Stage 6'),sort_keys=True,indent=2))


if __name__=='__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')), \
         patch.object(ReadBudget,'__init__',side_effect=AssertionError('recovery must not access budget')):
        asyncio.run(main())
