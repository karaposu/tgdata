"""Public lifecycle failure histories: actual SQLite/SDK, synthetic wire, no network.

Owned children exit before/after real commits. This proves process recovery, not
filesystem power-loss behavior or distributed reader ownership.
"""
import asyncio
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import telethon
from telethon import errors
from tgdata import (SQLiteSyncStore, BackfillStartRequest, BackfillRunRef,
    BackfillDeliveryRef, BackfillControlResult, BackfillConflictError,
    BackfillUnknownCommand, BackfillUnknownRun, BackfillUnknownReceipt,
    BackfillRecoveryRequired, BackfillStorageError, BackfillStateError,
    BackfillMediaError, SyncStorageError, health)
from tgdata.smoke_tests import test_29_backfill_public as u

d,f,b,q=u.d,u.f,u.b,u.q
CHAT=d.CHAT
ctx=u.ctx
spec=importlib.util.spec_from_file_location('integration_example',Path(__file__).resolve().parents[2]/'examples/backfill_runs.py')
example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)


def save(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream);stream.flush();os.fsync(stream.fileno())


def receiver():
    root=b.directory()
    return example.Receiver(example.ApplicationDatabase(root/'receiver.sqlite3',create=True),'archive')


def local(store):return u.instance(store,offline=True)[0]


async def finite(e,empty=False):
    e.sender.script=[d.finite_response([] if empty else [f.message(101)])]
    return await e.tg.prepare_backfill(ctx(e.initial))


async def unknown(e):
    e.sender.script=[f.PENDING]
    task=asyncio.create_task(e.tg.prepare_backfill(ctx(e.initial)))
    await d.until(lambda:bool(e.sender.pending));task.cancel()
    await f.expect(asyncio.CancelledError,task)
    return await e.tg.get_backfill_status(e.initial.run)


async def crash_child(manifest,phase,mode,trace):
    m=json.loads(Path(manifest).read_text());backend=SQLiteSyncStore(m['path'],create=False)
    req=BackfillStartRequest.from_dict(m['request'])
    source=phase in ('admission','publication','empty')
    tg,client,sender=u.instance(backend,offline=not source)
    if sender:sender.script=[d.finite_response([] if phase=='empty' else [f.message(101)])]
    clocks=q.Clocks()
    def factory(store,collection,**kw):return u.BackfillEngine(store,collection,clock=clocks.wall,monotonic_ns=clocks.nano,**kw)
    original=sqlite3.connect
    class Crash(sqlite3.Connection):
        def commit(self):
            hit=False
            if self.total_changes:
                row=json.loads(self.execute('SELECT data FROM tgdata_sync_state').fetchone()[0])['current']
                hit={
                    'create':row['ref']['run_id']==req.run_id,
                    'successor':row['ref']['run_id']==req.run_id,
                    'admission':row['attempt'] is not None,
                    'publication':row['pending'] is not None,
                    'empty':row['terminal_outcome']=='completed' and row['pending'] is None,
                    'ack':row['last_ack'] is not None and row['pending'] is None,
                    'control':row['last_control'] is not None and row['last_control']['command_id']=='matrix-pause',
                    'recovery':row['last_recovery'] is not None,
                    'abandon':row['abandoned'] is not None,
                }[phase]
            if hit:
                save(trace,dict(phase=phase,mode=mode,source_reads=len(sender.reads) if sender else 0,
                    candidate_after=row['after_id'],candidate_run=row['ref'],candidate_pending=row['pending'] is not None))
                if mode=='before':os._exit(41)
            super().commit()
            if hit:os._exit(42)
    def connect(*a,**kw):kw['factory']=Crash;return original(*a,**kw)
    with patch('tgdata.tgdata.BackfillEngine',side_effect=factory),patch.object(sqlite3,'connect',side_effect=connect):
        if phase in ('create','successor'):await tg.start_backfill(req,submission='new')
        else:
            ref=BackfillRunRef.from_dict(m['run']);status=await tg.get_backfill_status(ref)
            if source:await tg.prepare_backfill(ctx(status))
            elif phase=='ack':await tg.acknowledge_backfill(BackfillDeliveryRef.from_dict(m['delivery']))
            elif phase in ('control','abandon'):
                await tg.control_backfill(ref,command_id='matrix-pause' if phase=='control' else 'matrix-abandon',
                    expected_control_revision=status.control_revision,action='pause' if phase=='control' else 'abandon')
            elif phase=='recovery':await tg.recover_backfill(ref,**m['recovery'])
    raise AssertionError('actual commit boundary was not reached')


async def launch(e,phase,mode,**extra):
    root=b.directory();manifest=root/'intent.json';trace=root/'boundary.json'
    save(manifest,dict(path=e.store.path,request=e.req.to_dict(),run=e.initial.run.to_dict(),**extra))
    args=[sys.executable,__file__,'--crash',str(manifest),phase,mode,str(trace)]
    loop=asyncio.get_running_loop()
    def run():return subprocess.run(args,cwd=str(root),capture_output=True,text=True,timeout=25)
    result=await loop.run_in_executor(None,run)
    assert result.returncode==(41 if mode=='before' else 42),(phase,mode,result.returncode,result.stderr)
    observed=json.loads(trace.read_text())
    assert observed['source_reads']==(1 if phase in ('publication','empty') else 0)
    return local(SQLiteSyncStore(e.store.path,create=False)),observed


async def test_creation_real_commit_exit_pair():
    for mode in ('before','after'):
        e=await u.setup()
        # Use a separately provisioned empty actual store, retaining original request.
        e.store=d.store()
        fresh,_=await launch(e,'create',mode)
        if mode=='before':
            await f.expect(BackfillUnknownCommand,fresh.start_backfill(e.req,submission='retry'))
            assert await e.store.load(CHAT) is None
        else:
            retry=await fresh.start_backfill(e.req,submission='retry')
            assert not retry.applied and retry.status.run==e.initial.run
            assert retry.status.start_date==e.req.start_date and retry.status.end_date==e.req.end_date
        assert fresh.connection_engine._config is None


async def test_admission_real_commit_exit_pair_never_sends():
    for mode in ('before','after'):
        e=await u.setup();fresh,_=await launch(e,'admission',mode)
        status=await fresh.get_backfill_status(e.initial.run)
        assert status.after_id==100 and status.pending_batch_id is None
        if mode=='before':assert status==e.initial
        else:
            assert status.attempt_id
            await f.expect(BackfillRecoveryRequired,fresh.prepare_backfill(ctx(status)))
            recovered=await fresh.recover_backfill(status.run,attempt_id=status.attempt_id,
                command_id='stopped-child',expected_control_revision=0,previous_reader_stopped=True)
            assert recovered.status.attempt_id is None and recovered.status.after_id==100


async def test_publication_real_commit_exit_pair():
    for mode in ('before','after'):
        e=await u.setup();fresh,_=await launch(e,'publication',mode)
        status=await fresh.get_backfill_status(e.initial.run)
        assert status.after_id==100 and status.terminal_outcome is None
        if mode=='before':
            assert status.attempt_id and status.pending_batch_id is None
            await f.expect(BackfillRecoveryRequired,fresh.prepare_backfill(ctx(status)))
        else:
            replay=await fresh.prepare_backfill(ctx(status));assert replay.replayed
            assert [r['id'] for r in replay.batch.messages]==['101'] and status.source_exhausted
            r=receiver();assert r.accept_backfill(replay.batch,replay.delivery)
            assert r.observation(replay.delivery).to_json()==replay.batch.to_json()
            assert (await fresh.acknowledge_backfill(replay.delivery)).terminal_outcome=='completed'


async def test_empty_end_real_commit_exit_pair():
    for mode in ('before','after'):
        e=await u.setup();fresh,_=await launch(e,'empty',mode)
        status=await fresh.get_backfill_status(e.initial.run)
        assert status.after_id==100 and status.pending_batch_id is None and status.last_acked_batch_id is None
        if mode=='before':
            assert status.attempt_id and status.terminal_outcome is None
            await f.expect(BackfillRecoveryRequired,fresh.prepare_backfill(ctx(status)))
        else:
            assert status.source_exhausted and status.terminal_outcome=='completed'
            assert (await fresh.prepare_backfill(ctx(status))).batch is None


async def test_ack_real_commit_exit_pair_follows_receiver():
    for mode in ('before','after'):
        e=await u.setup();turn=await finite(e);r=receiver()
        assert r.accept_backfill(turn.batch,turn.delivery)
        fresh,_=await launch(e,'ack',mode,delivery=turn.delivery.to_dict())
        status=await fresh.get_backfill_status(e.initial.run)
        assert status.after_id==(100 if mode=='before' else 101)
        if mode=='before':
            replay=await fresh.prepare_backfill(ctx(status))
            assert replay.batch.to_json()==r.observation(turn.delivery).to_json()
            assert not r.accept_backfill(replay.batch,replay.delivery)
        done=await fresh.acknowledge_backfill(turn.delivery)
        assert done.terminal_outcome=='completed' and done.after_id==101
        assert await fresh.acknowledge_backfill(turn.delivery)==done and len(e.sender.reads)==1


async def test_control_real_commit_exit_pair_preserves_delivery():
    for mode in ('before','after'):
        e=await u.setup();turn=await finite(e);fresh,_=await launch(e,'control',mode)
        status=await fresh.get_backfill_status(e.initial.run)
        assert status.control_revision==(0 if mode=='before' else 1)
        result=await fresh.control_backfill(status.run,command_id='matrix-pause',expected_control_revision=0,action='pause')
        assert result.applied==(mode=='before') and result.status.operator_intent=='paused'
        replay=await fresh.prepare_backfill(ctx(result.status));assert replay.batch.to_json()==turn.batch.to_json()
        r=receiver();r.accept_backfill(replay.batch,replay.delivery)
        assert (await fresh.acknowledge_backfill(replay.delivery)).terminal_outcome=='completed'


async def test_recovery_real_commit_exit_pair_preserves_original_command():
    for mode in ('before','after'):
        e=await u.setup(pause=12);status=await unknown(e)
        args=dict(attempt_id=status.attempt_id,command_id='matrix-recovery',expected_control_revision=0,previous_reader_stopped=True)
        fresh,_=await launch(e,'recovery',mode,recovery=args)
        observed=await fresh.get_backfill_status(status.run)
        assert bool(observed.attempt_id)==(mode=='before')
        result=await fresh.recover_backfill(status.run,**args)
        assert result.applied==(mode=='before') and result.status.after_id==100
        if mode=='after':assert result.status.pacing_not_before==observed.pacing_not_before
        assert not (await fresh.recover_backfill(status.run,**args)).applied
        assert len(e.sender.reads)==1


async def test_abandon_real_commit_exit_pair_retires_receipt():
    for mode in ('before','after'):
        e=await u.setup();turn=await finite(e);await u.decide(e,turn.status,'cancel','cancel')
        fresh,_=await launch(e,'abandon',mode)
        status=await fresh.get_backfill_status(e.initial.run)
        assert status.terminal_outcome=='cancelled' and status.after_id==100
        assert status.delivery_abandoned==(mode=='after')
        result=await fresh.control_backfill(status.run,command_id='matrix-abandon',expected_control_revision=1,action='abandon')
        assert result.applied==(mode=='before') and result.status.delivery_abandoned
        await f.expect(BackfillUnknownReceipt,fresh.acknowledge_backfill(turn.delivery))
        assert len(e.sender.reads)==1


async def test_successor_real_commit_exit_pair_keeps_old_receipt_read_only():
    for mode in ('before','after'):
        e=await u.setup();turn=await finite(e);r=receiver();r.accept_backfill(turn.batch,turn.delivery)
        old=await e.tg.acknowledge_backfill(turn.delivery)
        e.req=replace(e.req,run_id='successor',expected_predecessor=old.run)
        fresh,_=await launch(e,'successor',mode)
        if mode=='before':await f.expect(BackfillUnknownCommand,fresh.start_backfill(e.req,submission='retry'))
        else:
            result=await fresh.start_backfill(e.req,submission='retry');assert not result.applied
            assert result.status.run.generation==2 and result.status.after_id==100
        raw=await e.store.load(CHAT)
        ack=await fresh.acknowledge_backfill(turn.delivery)
        assert ack.after_id==101 and await e.store.load(CHAT)==raw


async def test_failed_prefix_and_publication_keep_source_provenance_then_recover():
    events=[];e=await u.setup(pause=12,batch_size=101,events=events)
    original=errors.ChannelPrivateError(None)
    e.sender.script=[f.response([f.message(i) for i in range(200,100,-1)]),original]
    fault=u.AmbiguousStore(e.store,target=2,committed=False,readback='outage');e.engine._store=fault
    error=await f.expect(BackfillStorageError,e.tg.prepare_backfill(ctx(e.initial)))
    assert error.read_error is original and health.classify(error,True) is None
    assert len(events)==1 and events[0]['verdict']==health.NO_ACCESS
    snapshot=e.tg._health.snapshot();status=await e.tg.get_backfill_status(e.initial.run)
    assert status.attempt_id and status.after_id==100 and status.pending_batch_id is None
    recovered=await e.tg.recover_backfill(status.run,attempt_id=status.attempt_id,command_id='recover',
        expected_control_revision=0,previous_reader_stopped=True)
    wait=await e.tg.prepare_backfill(ctx(recovered.status));assert wait.wait_seconds==12
    assert e.tg._health.snapshot()==snapshot and len(events)==1 and len(e.sender.reads)==2
    e.clocks.advance(12);e.sender.script=[d.finite_response([f.message(101)])]
    turn=await e.tg.prepare_backfill(ctx(wait.status))
    assert [r['id'] for r in turn.batch.messages]==['101'] and len(e.sender.reads)==3
    assert str(CHAT) not in e.tg._health.snapshot()['no_access']


async def test_cancelled_publication_and_ack_reply_reopen_actual_effect():
    for phase in ('publication','ack'):
        e=await u.setup();turn=None
        if phase=='ack':
            turn=await finite(e);r=receiver();r.accept_backfill(turn.batch,turn.delivery)
        else:e.sender.script=[d.finite_response([f.message(101)])]
        fault=u.AmbiguousStore(e.store,target=2 if phase=='publication' else 1,readback='hold');e.engine._store=fault
        call=e.tg.prepare_backfill(ctx(e.initial)) if phase=='publication' else e.tg.acknowledge_backfill(turn.delivery)
        task=asyncio.create_task(call);await asyncio.wait_for(fault.entered.wait(),5)
        task.cancel();await f.expect(asyncio.CancelledError,task)
        fresh=local(e.store);status=await fresh.get_backfill_status(e.initial.run)
        assert status.attempt_id is None and len(e.sender.reads)==1
        if phase=='publication':
            replay=await fresh.prepare_backfill(ctx(status));assert replay.replayed and len(replay.batch.messages)==1
        else:assert status.terminal_outcome=='completed' and await fresh.acknowledge_backfill(turn.delivery)==status


async def test_late_final_result_cancel_order_and_equal_hash_successor():
    e=await u.setup();e.sender.script=[f.PENDING]
    task=asyncio.create_task(e.tg.prepare_backfill(ctx(e.initial)));await d.until(lambda:bool(e.sender.pending))
    cancelled=await u.decide(e,e.initial,'cancel','cancel')
    await f.expect(BackfillConflictError,u.decide(e,cancelled.status,'abandon','premature-abandon'))
    e.sender.pending[0].set_result(d.finite_response([f.message(101)]));turn=await task
    assert turn.status.terminal_outcome=='cancelled' and turn.status.source_exhausted
    r=receiver();r.accept_backfill(turn.batch,turn.delivery)
    settled=await e.tg.acknowledge_backfill(turn.delivery);assert settled.terminal_outcome=='cancelled'
    second=(await e.tg.start_backfill(replace(e.req,run_id='second',expected_predecessor=settled.run),submission='new')).status
    e.sender.script=[d.finite_response([f.message(101)])]
    later=await e.tg.prepare_backfill(ctx(second));assert later.batch.batch_id==turn.batch.batch_id
    raw=await e.store.load(CHAT);old=await e.tg.acknowledge_backfill(turn.delivery)
    assert old.history_limited and await e.store.load(CHAT)==raw
    r.accept_backfill(later.batch,later.delivery);done=await e.tg.acknowledge_backfill(later.delivery)
    terminal=await u.decide(e,done,'cancel','after-completion');assert terminal.outcome=='terminal'
    third=(await e.tg.start_backfill(replace(e.req,run_id='third',expected_predecessor=done.run),submission='new')).status
    await f.expect(BackfillUnknownRun,e.tg.acknowledge_backfill(turn.delivery))
    assert third.after_id==100 and r.summary()['receipts']==2 and r.summary()['messages']==1


async def test_opposing_controls_and_delayed_resume_are_revision_ordered():
    e=await u.setup();ready=asyncio.Event()
    class Barrier:
        count=0
        async def load(self,chat):
            raw=await e.store.load(chat);self.count+=1
            if self.count<=2:
                if self.count==2:ready.set()
                await ready.wait()
            return raw
        async def compare_and_swap(self,*a):return await e.store.compare_and_swap(*a)
    one=local(Barrier());two=local(one._backfill_store)
    results=await asyncio.gather(one.control_backfill(e.initial.run,command_id='one',expected_control_revision=0,action='pause'),
        two.control_backfill(e.initial.run,command_id='two',expected_control_revision=0,action='cancel'),return_exceptions=True)
    assert sum(isinstance(x,BackfillControlResult) and x.applied for x in results)==1
    assert sum(isinstance(x,BackfillConflictError) for x in results)==1 and not e.sender.reads
    e=await u.setup();paused=await u.decide(e,e.initial,'pause','initial-pause')
    fault=d.FaultStore(e.store);fault.hold=1;slow=local(fault)
    task=asyncio.create_task(slow.control_backfill(paused.status.run,command_id='resume',expected_control_revision=1,action='resume'))
    await asyncio.wait_for(fault.entered.wait(),5)
    status=await e.tg.get_backfill_status(e.initial.run);newer=await u.decide(e,status,'pause','newer-pause')
    fault.release.set();late=await task
    assert late.status.control_revision==2 and late.status.operator_intent=='active'
    assert (await e.tg.get_backfill_status(e.initial.run))==newer.status and newer.status.control_revision==3
    await f.expect(BackfillConflictError,e.tg.prepare_backfill(ctx(late.status)))
    await f.expect(BackfillConflictError,e.tg.control_backfill(e.initial.run,command_id='resume',expected_control_revision=1,action='resume'))


async def test_media_receipt_custody_ack_without_source_bytes_and_health():
    events=[];e=await u.setup(media_mode='download',batch_size=1,events=events)
    e.sender.files[b.ASSET_ID]=b.PAYLOAD;b.script_messages(e.sender,[b.document()]);media=b.directory()
    turn=await e.tg.prepare_backfill(ctx(e.initial),download_media_to=media)
    blob=turn.batch.messages[0]['media']['blob'];source=media/blob['path'];custody=b.directory()/blob['path']
    custody.write_bytes(source.read_bytes())
    with custody.open('rb') as stream:os.fsync(stream.fileno())
    # Actual snapshot transaction retained with the scoped ref; the example's
    # reference-only receiver intentionally does not pretend to own download bytes.
    db=example.ApplicationDatabase(b.directory()/'receiver.sqlite3',create=True)
    with db.transaction(write=True) as sql:
        sql.execute('INSERT INTO example_receipts VALUES (?,?)',(example.Receiver.backfill_key(turn.delivery),turn.batch.to_json()))
    count,snapshot=await u.prior_denial(e.tg,events);raw=await e.store.load(CHAT);calls=list(e.sender.calls)
    source.write_bytes(b'corrupt');await f.expect(BackfillMediaError,e.tg.prepare_backfill(ctx(turn.status),download_media_to=media))
    source.unlink();await f.expect(BackfillMediaError,e.tg.prepare_backfill(ctx(turn.status),download_media_to=media))
    assert await e.store.load(CHAT)==raw and e.tg._health.snapshot()==snapshot and len(events)==count
    status=await e.tg.acknowledge_backfill(turn.delivery)
    assert status.after_id==101 and status.terminal_outcome is None and e.sender.calls==calls
    assert example.Receiver(db,'archive').observation(turn.delivery).to_json()==turn.batch.to_json()
    assert custody.read_bytes()==b.PAYLOAD and await e.tg.acknowledge_backfill(turn.delivery)==status


async def test_missing_malformed_known_state_and_cleanup_preserve_uncertainty():
    e=await u.setup();raw=await e.store.load(CHAT);fresh=local(e.store)
    with sqlite3.connect(e.store.path) as db:db.execute('UPDATE tgdata_sync_state SET data=?',('{bad',))
    await f.expect(BackfillStateError,fresh.get_backfill_status(e.initial.run))
    await f.expect(BackfillStateError,fresh.start_backfill(e.req,submission='retry'))
    with sqlite3.connect(e.store.path) as db:db.execute('DELETE FROM tgdata_sync_state')
    await f.expect(BackfillUnknownRun,fresh.get_backfill_status(e.initial.run))
    await f.expect(BackfillUnknownCommand,fresh.start_backfill(e.req,submission='retry'))
    assert await e.store.load(CHAT) is None and not e.sender.calls
    Path(e.store.path).unlink();f.rejected(SyncStorageError,lambda:SQLiteSyncStore(e.store.path,create=False))
    assert not Path(e.store.path).exists()
    e=await u.setup();original=sqlite3.connect
    class Failure(sqlite3.Connection):
        def execute(self,sql,*a,**kw):
            if sql.startswith('SELECT data FROM tgdata_sync_state'):raise sqlite3.OperationalError('primary read failed')
            return super().execute(sql,*a,**kw)
        def rollback(self):raise RuntimeError('secondary rollback failed')
        def close(self):super().close();raise RuntimeError('secondary close failed')
    def connect(*a,**kw):kw['factory']=Failure;return original(*a,**kw)
    with patch.object(sqlite3,'connect',side_effect=connect):
        error=await f.expect(BackfillStorageError,e.tg.get_backfill_status(e.initial.run))
    assert 'RuntimeError' not in str(error) and not e.sender.calls and await e.store.load(CHAT)


async def main(args):
    with tempfile.TemporaryDirectory(prefix='tgdata_public_integration_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        f.TMP=d.TMP=Path(tmp)
        if args and args[0]=='--crash':return await crash_child(*args[1:])
        assert telethon.__version__=='1.45.0';tests=[v for k,v in globals().items() if k.startswith('test_')]
        print('Public Integration Tests — actual SQLite/SDK; synthetic wire; sockets forbidden');passed=0
        try:
            for test in tests:
                print('\nTEST:',test.__name__,flush=True)
                try:await asyncio.wait_for(test(),90)
                except Exception:traceback.print_exc();print('✗ Failed')
                else:passed+=1;print('✓ Passed')
        finally:
            for client in f.CLIENTS:await client.disconnect()
            f.CLIENTS.clear()
        print('\nPassed: {}/{}'.format(passed,len(tests)))
        return 0 if passed==len(tests) else 1


if __name__=='__main__':sys.exit(asyncio.run(main(sys.argv[1:])))
