"""Existing primitive composition, not an implementation of Stage 3 transitions."""
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sqlite3
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from telethon import errors
from tgdata import MessageBatch,SQLiteSyncStore,health
from tgdata.backfill import BackfillStartRequest,BackfillStorageError
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill_state import _BackfillState
from tgdata.batch_files import download_blob,_verify_existing,BatchStorageError
from tgdata.history_window import _encode_date
from tgdata.smoke_tests import test_24_backfill_state as state_tests

CHAT=-1000000000007
NOW=datetime(2026,10,7,12,tzinfo=timezone.utc)


async def main():
    with tempfile.TemporaryDirectory(prefix='tgdata19_prebuild_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        root=Path(tmp);backend=SQLiteSyncStore(root/'state.sqlite3')
        engine=BackfillEngine(backend,'primitive-probe',clock=lambda:NOW)
        req=BackfillStartRequest('primitive-probe',CHAT,'run','receiver',0,None,
            media_mode='download',batch_size=1,start_date=NOW-timedelta(days=2),end_date=NOW-timedelta(days=1))
        ref=(await engine.start(req,submission='new')).status.run
        payload=b'actual file bytes, synthetic message metadata\x00'
        async def writer(output):output.write(payload);return output
        blob=await download_blob(root/'media',writer,len(payload))
        assert blob['sha256']==hashlib.sha256(payload).hexdigest()
        record=dict(id='1',kind='message',date=_encode_date(req.start_date),edit_date=None,
            text='synthetic probe',sender=dict(id=None,name=None,username=None),post_author=None,
            reply_to_id=None,forward_from_id=None,grouped_id=None,service_action=None,
            media=dict(kind='document',id='7',mime_type='application/octet-stream',
                       file_name='probe.bin',size=len(payload),downloadable=True,blob=blob))
        batch=MessageBatch._from_records(CHAT,0,[record],'download','limit')
        raw=await backend.load(CHAT)
        pretty=json.dumps(json.loads(raw),indent=2)
        assert await backend.compare_and_swap(CHAT,raw,pretty)
        doc=json.loads(pretty);doc['state_revision']='3';row=doc['current']
        row['pending']=batch.to_dict()
        row['pacing']=dict(attempt_id='probe-attempt',ended_at=_encode_date(NOW),
                          not_before=_encode_date(NOW),clock_uncertain=False)
        pending=_BackfillState(doc).to_json()
        assert await backend.compare_and_swap(CHAT,raw,pending) is False
        assert await backend.load(CHAT)==pretty
        assert await backend.compare_and_swap(CHAT,pretty,pending)
        reopened=SQLiteSyncStore(backend.path,create=False)
        saved=await reopened.load(CHAT)
        restored=_BackfillState.from_json(saved,'primitive-probe',CHAT)
        assert restored.status().run==ref and restored.status().pending_batch_id==batch.batch_id
        assert MessageBatch(restored.to_dict()['current']['pending']).to_json()==batch.to_json()
        print('PASS real SQLite exact CAS, owned pending codec and reopen')

        moved=root/'moved';moved.mkdir();path=moved/blob['path']
        shutil.copyfile(root/'media'/blob['path'],path)
        _verify_existing(path,blob['sha256'],blob['size'])
        path.write_bytes(b'x'*len(payload))
        try:_verify_existing(path,blob['sha256'],blob['size'])
        except BatchStorageError:pass
        else:raise AssertionError('corruption accepted')
        path.unlink()
        assert await reopened.load(CHAT)==saved
        print('PASS actual artifact relocation/integrity refusal leaves pending metadata unchanged')

        accepted=restored.to_dict();accepted['state_revision']='4'
        accepted['current'].update(after_id='1',pending=None,
            last_ack=dict(batch_id=batch.batch_id,next_after_id='1',observed_at=_encode_date(NOW)))
        accepted=_BackfillState(accepted).to_json()
        original=sqlite3.connect
        class BadClose(sqlite3.Connection):
            def close(self):
                wrote=self.total_changes>0;super().close()
                if wrote:raise sqlite3.OperationalError('owned post-commit probe failure')
        def connect(*args,**kwargs):kwargs['factory']=BadClose;return original(*args,**kwargs)
        with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
            try:await engine._backend('compare_and_swap',CHAT,saved,accepted)
            except BackfillStorageError:pass
            else:raise AssertionError('lost commit reply not exposed')
        assert await SQLiteSyncStore(backend.path,create=False).load(CHAT)==accepted
        assert (await engine.status(ref)).after_id==1 and not path.exists()
        print('PASS actual committed metadata survives close failure; accepted state is independent of local media')

        class CancelAfterCommit:
            async def compare_and_swap(self,*args):
                assert await reopened.compare_and_swap(*args)
                asyncio.current_task().cancel()
                await asyncio.sleep(0)
        async def nested_cancellation():
            try:raise errors.FloodWaitError(None,capture=1)
            except Exception:
                try:await BackfillEngine(CancelAfterCommit(),'primitive-probe')._backend(
                    'compare_and_swap',CHAT,accepted,accepted)
                except asyncio.CancelledError as cancel:
                    # Characterize the existing unsuppressed path. A later run after
                    # the planned fix may already suppress it; both require final None.
                    inherited=health.classify(cancel,include_reported=True)
                    try:raise cancel from None
                    except asyncio.CancelledError as local:
                        assert health.classify(local,include_reported=True) is None
                    return inherited is not None
                raise AssertionError('cancellation did not arrive')
        inherited=await asyncio.create_task(nested_cancellation())
        assert await reopened.load(CHAT)==accepted
        print('PASS actual cancellation/commit and causal suppression; baseline inherited verdict:',inherited)

        state_tests.TMP=root
        await state_tests.test_process_exit_at_real_create_commit()
        print('PASS actual subprocess exits before/after SQLite create commit')
        print('Result: PASS — five existing-primitive checks; new Stage 3 engine and live gate not claimed')


if __name__=='__main__':asyncio.run(main())
