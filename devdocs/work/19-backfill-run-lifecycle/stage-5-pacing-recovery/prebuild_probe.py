"""Stage 5 primitive probe on unchanged Stage 4; no new recover implementation.

Candidate recovery fixtures prove codec/store capacity only. Sockets are blocked;
Gate B originals are opened read-only and only disposable copies are mutated.
"""
import asyncio
from datetime import datetime,timedelta,timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from tgdata import SQLiteSyncStore,SyncStorageError
from tgdata.backfill import BackfillStartRequest,BackfillPrepareContext,_pause_delta
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill_state import _BackfillState
from tgdata.history_window import _encode_date

CHAT=-1000000000007


def candidate(raw,*,known_end=None):
    value=json.loads(raw);row=value['current'];attempt=row['attempt'];assert attempt
    at=datetime.now(timezone.utc);pause=_pause_delta(row['request']['pause_seconds'])
    value['state_revision']=str(int(value['state_revision'])+1)
    row['attempt']=None
    row['pacing']=dict(attempt_id=attempt['attempt_id'],ended_at=_encode_date(known_end) if known_end else None,
                      not_before=_encode_date((known_end or at)+pause),clock_uncertain=False)
    row['last_recovery']=dict(command_id='primitive-recovery',attempt_id=attempt['attempt_id'],
        expected_control_revision=row['control_revision'],state_revision=value['state_revision'],
        recovered_at=_encode_date(at))
    return _BackfillState(value)


async def unknown(path):
    store=SQLiteSyncStore(path);now=datetime.now(timezone.utc)
    request=BackfillStartRequest('primitive',CHAT,'run','archive',0.025,None,
        start_date=now-timedelta(days=1),end_date=now)
    async def cancelled(*a,**kw):raise asyncio.CancelledError()
    eng=BackfillEngine(store,request.collection_id,read_batch=cancelled)
    status=(await eng.start(request,submission='new')).status
    try:await eng.prepare(BackfillPrepareContext.from_status(status))
    except asyncio.CancelledError:pass
    else:raise AssertionError('expected cancelled callback')
    raw=await store.load(CHAT);assert json.loads(raw)['current']['attempt']
    return store,raw


async def crash(path,mode):
    store=SQLiteSyncStore(path,create=False);raw=await store.load(CHAT)
    next_state=candidate(raw);original=sqlite3.connect
    class Crash(sqlite3.Connection):
        def commit(self):
            if self.total_changes:
                if mode=='before':os._exit(81)
                super().commit();os._exit(82)
            super().commit()
    def connect(*a,**kw):kw['factory']=Crash;return original(*a,**kw)
    with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
        await store.compare_and_swap(CHAT,raw,next_state.to_json())
    raise AssertionError('actual commit boundary not reached')


async def main():
    with tempfile.TemporaryDirectory(prefix='tgdata19_stage5_primitive_') as tmp:
        root=Path(tmp)
        start=datetime.now(timezone.utc);ticks=time.monotonic_ns()
        await asyncio.sleep(0.03)
        elapsed=time.monotonic_ns()-ticks;utc_elapsed=datetime.now(timezone.utc)-start
        assert type(ticks) is int and ticks>=0 and elapsed>=30_000_000 and utc_elapsed>timedelta(0)
        print('PASS actual UTC and integer monotonic_ns observe a positive elapsed interval')
        for known in (False,True):
            store,raw=await unknown(root/('known-{}.sqlite3'.format(known)))
            next_state=candidate(raw,known_end=datetime.now(timezone.utc) if known else None)
            assert await store.compare_and_swap(CHAT,raw,next_state.to_json())
            reopened=SQLiteSyncStore(store.path,create=False)
            assert await reopened.load(CHAT)==next_state.to_json()
            status=_BackfillState.from_json(await reopened.load(CHAT),'primitive',CHAT).status()
            assert status.after_id==0 and status.attempt_id is None and not status.source_exhausted
            assert status.pending_batch_id is None and status.terminal_outcome is None
        print('PASS strict v1 known/unknown-end recovery candidates reopen exactly without invented data')
        store,raw=await unknown(root/'close-error.sqlite3');next_state=candidate(raw)
        original=sqlite3.connect
        class BadClose(sqlite3.Connection):
            def close(self):
                changed=self.total_changes;super().close()
                if changed:raise sqlite3.OperationalError('owned post-commit failure')
        def connect(*a,**kw):kw['factory']=BadClose;return original(*a,**kw)
        with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
            try:await store.compare_and_swap(CHAT,raw,next_state.to_json())
            except SyncStorageError:pass
            else:raise AssertionError('expected post-commit close error')
        assert await SQLiteSyncStore(store.path,create=False).load(CHAT)==next_state.to_json()
        print('PASS actual post-commit close error retains the exact recovery identity/deadline')
        for mode in ('before','after'):
            store,raw=await unknown(root/('crash-'+mode+'.sqlite3'))
            result=await asyncio.to_thread(subprocess.run,[sys.executable,__file__,'--crash',store.path,mode],
                                          capture_output=True,text=True,timeout=25)
            assert result.returncode==(81 if mode=='before' else 82),(result.returncode,result.stderr)
            saved=await SQLiteSyncStore(store.path,create=False).load(CHAT)
            if mode=='before':assert saved==raw
            else:
                row=_BackfillState.from_json(saved,'primitive',CHAT).to_dict()['current']
                assert row['attempt'] is None and row['last_recovery']['command_id']=='primitive-recovery'
                assert row['pacing']['ended_at'] is None and row['after_id']=='0' and row['exhaustion'] is None
        print('PASS actual subprocess exits before/after recovery-candidate commits preserve the correct side')
        gates=Path('/private/tmp/tgdata19-gate-b-live-20261007')
        for name in ('empty_uncommitted','unknown_source'):
            source=gates/(name+'.sqlite3');before=hashlib.sha256(source.read_bytes()).hexdigest()
            dest=root/(name+'.sqlite3')
            with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as original_db,sqlite3.connect(str(dest)) as copy_db:
                original_db.backup(copy_db)
            store=SQLiteSyncStore(dest,create=False)
            with sqlite3.connect(str(dest)) as db:chat,raw=db.execute('SELECT chat_id,data FROM tgdata_sync_state').fetchone()
            state=candidate(raw);assert await store.compare_and_swap(chat,raw,state.to_json())
            assert await store.load(chat)==state.to_json()
            assert before==hashlib.sha256(source.read_bytes()).hexdigest()
        print('PASS actual Gate B stopped-worker rows support the candidate in disposable copies; originals unchanged')
        print('Passed: 5/5 primitive checks; LOCAL only, not new recovery behavior or Gate C')


if __name__=='__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        if len(sys.argv)>1 and sys.argv[1]=='--crash':asyncio.run(crash(sys.argv[2],sys.argv[3]))
        else:asyncio.run(main())
