"""Stage 5 clocks/recovery: actual SQLite/SDK/budget, synthetic transport, no network."""
import asyncio
from dataclasses import FrozenInstanceError,replace
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import telethon
from telethon import errors
from tgdata import SQLiteSyncStore,ReadBudgetExceeded,ReadBudgetError,health
from tgdata.backfill import (BackfillPrepareContext,BackfillTurn,BackfillRecoveryResult,
    BackfillConfigurationError,BackfillConflictError,BackfillStorageError,BackfillStateError,
    BackfillClockError,BackfillRecoveryRequired,BackfillUnknownRun)
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill_state import _BackfillState
from tgdata.history_window import _encode_date
from tgdata.message_batch import MAX_LONG
from tgdata.smoke_tests import test_25_backfill_delivery as d
from tgdata.smoke_tests.test_26_backfill_completion import AmbiguousStore

f=d.f
CHAT=d.CHAT


class Clocks:
    def __init__(self,utc=d.NOW,ticks=50_000_000_000):
        self.utc,self.ticks=utc,ticks;self.utc_calls=self.ns_calls=0
    def wall(self):self.utc_calls+=1;return self.utc
    def nano(self):self.ns_calls+=1;return self.ticks
    def advance(self,seconds):
        self.utc+=timedelta(seconds=seconds);self.ticks+=round(seconds*1_000_000_000)


def context(status):return BackfillPrepareContext.from_status(status)


def engine(e,*,store=None,reader=None,clocks=None,forbid=False):
    clocks=clocks or e.clocks
    return BackfillEngine(store or e.store,e.req.collection_id,read_batch=reader,
        clock=d.forbidden_clock if forbid else clocks.wall,
        monotonic_ns=d.forbidden_clock if forbid else clocks.nano)


async def setup(pause=240,*,budget=None,events=None,clocks=None,**changes):
    store=d.store();tg,client,sender=d.b.instance(budget,events=events)
    req=d.request(pause_seconds=pause,**changes);clocks=clocks or Clocks()
    e=SimpleNamespace(store=store,tg=tg,client=client,sender=sender,req=req,clocks=clocks)
    e.eng=engine(e,reader=tg.get_message_batch)
    e.initial=(await e.eng.start(req,submission='new')).status;e.ctx=context(e.initial)
    return e


def command(status,ident='recover-1'):
    assert status.attempt_id
    return dict(attempt_id=status.attempt_id,command_id=ident,
                expected_control_revision=status.control_revision,previous_reader_stopped=True)


async def unknown(pause=240,**changes):
    e=await setup(pause,**changes);e.sender.script=[f.PENDING]
    task=asyncio.create_task(e.eng.prepare(e.ctx));await d.until(lambda:bool(e.sender.pending))
    task.cancel();await f.expect(asyncio.CancelledError,task)
    status=await e.eng.status(e.ctx.run);e.command=command(status)
    return e


async def test_wait_values_and_recovery_status_are_owned():
    e=await setup();turn=await e.eng.prepare(e.ctx);status=await e.eng.acknowledge(turn.delivery)
    waiting=await e.eng.prepare(context(status))
    assert waiting.wait_seconds==240 and waiting.batch is None and waiting.delivery is None
    assert waiting.to_dict()['wait_seconds']==240 and waiting.status.pacing_attempt_id
    assert waiting.status.pacing_ended_at==d.NOW and waiting.status.last_recovery_id is None
    f.rejected(FrozenInstanceError,lambda:setattr(waiting,'wait_seconds',0))
    for seconds in (True,0,-1,float('nan'),float('inf')):
        f.rejected(BackfillConfigurationError,lambda:BackfillTurn(status,wait_seconds=seconds))
    f.rejected(BackfillConfigurationError,lambda:BackfillTurn(turn.status,turn.batch,turn.delivery,wait_seconds=1))
    u=await unknown();u.clocks.advance(10)
    result=await engine(u).recover(u.ctx.run,**u.command)
    assert result.applied and result.outcome=='recovered'
    assert result.status.last_recovery_id==u.command['command_id']
    assert result.status.last_recovered_attempt_id==u.command['attempt_id']
    assert result.status.last_recovery_at==u.clocks.utc
    changed=result.to_dict();changed['status']['run']['run_id']='different'
    assert result.status.run==u.ctx.run
    f.rejected(FrozenInstanceError,lambda:setattr(result,'applied',False))


async def test_early_late_ack_and_repeated_observation_do_not_move_deadline():
    for ack_at in (60,600):
        e=await setup();turn=await e.eng.prepare(e.ctx);deadline=d.NOW+timedelta(seconds=240)
        assert turn.status.pacing_not_before==deadline
        e.clocks.advance(ack_at)
        local=engine(e,forbid=True)
        assert (await local.prepare(e.ctx)).batch.to_json()==turn.batch.to_json()
        assert (await local.status(e.ctx.run)).pacing_not_before==deadline
        accepted=await e.eng.acknowledge(turn.delivery);saved=await e.store.load(CHAT)
        assert accepted.pacing_not_before==deadline
        assert await local.acknowledge(turn.delivery)==accepted
        if ack_at==60:
            for _ in range(3):
                wait=await e.eng.prepare(context(accepted));assert wait.wait_seconds==180
                assert await e.store.load(CHAT)==saved
            e.clocks.advance(179);assert (await e.eng.prepare(context(accepted))).wait_seconds==1
            e.clocks.advance(1)
        next_turn=await e.eng.prepare(context(accepted))
        assert next_turn.batch.after_id==102 and len(e.sender.reads)==2


async def test_early_wait_needs_no_reader_media_root_or_sleep():
    e=await setup(media_mode='download',batch_size=1)
    e.sender.files[d.b.ASSET_ID]=d.b.PAYLOAD;d.b.script_messages(e.sender,[d.b.document()])
    turn=await e.eng.prepare(e.ctx,download_media_to=d.b.directory())
    accepted=await e.eng.acknowledge(turn.delivery);before=await e.store.load(CHAT)
    missing=d.TMP/'waiting-must-not-create'
    with patch('tgdata.backfill_engine.prepare_directory',side_effect=AssertionError('no directory work')):
        local=engine(e)
        for directory in (None,missing):
            waiting=await local.prepare(context(accepted),download_media_to=directory)
            assert waiting.wait_seconds==240
    assert not missing.exists() and await e.store.load(CHAT)==before and len(e.sender.reads)==1


async def test_reopen_remaining_wait_uses_utc_once_then_monotonic():
    e=await setup();turn=await e.eng.prepare(e.ctx);accepted=await e.eng.acknowledge(turn.delivery)
    e.clocks.advance(60)
    moved=Clocks(e.clocks.utc,0);local=engine(e,reader=e.tg.get_message_batch,clocks=moved)
    assert (await local.prepare(context(accepted))).wait_seconds==180
    moved.utc+=timedelta(hours=1);moved.ticks+=1_000_000_000
    assert (await local.prepare(context(accepted))).wait_seconds==179
    assert len(e.sender.reads)==1
    moved.ticks+=179_000_000_000
    assert (await local.prepare(context(accepted))).batch.after_id==102
    raw=await e.store.load(CHAT)
    assert all(k not in raw for k in ('monotonic','deadline_ns','ticks'))


async def test_forward_wall_step_cannot_beat_known_elapsed_minimum():
    e=await setup();turn=await e.eng.prepare(e.ctx);accepted=await e.eng.acknowledge(turn.delivery)
    e.clocks.utc+=timedelta(hours=2);e.clocks.ticks+=10_000_000_000
    assert (await e.eng.prepare(context(accepted))).wait_seconds==230
    e.clocks.ticks+=230_000_000_000
    assert (await e.eng.prepare(context(accepted))).batch.after_id==102


async def test_clock_regression_and_invalid_ns_refuse_without_admission():
    for which in ('utc','ns','bool','float','negative','raising'):
        e=await setup();turn=await e.eng.prepare(e.ctx);accepted=await e.eng.acknowledge(turn.delivery)
        before=await e.store.load(CHAT)
        if which=='utc':e.clocks.utc-=timedelta(microseconds=1)
        elif which=='ns':e.clocks.ticks-=1
        elif which=='bool':e.clocks.ticks=True
        elif which=='float':e.clocks.ticks=1.5
        elif which=='negative':e.clocks.ticks=-1
        else:
            def fail():raise OSError(d.SECRET)
            e.eng._monotonic_ns=fail
        error=await f.expect(BackfillClockError,e.eng.prepare(context(accepted)))
        assert d.SECRET not in str(error) and health.classify(error,True) is None
        assert await e.store.load(CHAT)==before and len(e.sender.reads)==1
    e=await setup();turn=await e.eng.prepare(e.ctx)
    await e.eng.acknowledge(turn.delivery)
    old=Clocks(d.NOW-timedelta(seconds=1),0)
    await f.expect(BackfillClockError,engine(e,reader=d.forbidden_reader,clocks=old).prepare(
        context(await e.eng.status(e.ctx.run))))


async def test_exact_submicrosecond_pause_and_explicit_zero():
    for pause in (0,0.0000004):
        e=await setup(pause);turn=await e.eng.prepare(e.ctx);accepted=await e.eng.acknowledge(turn.delivery)
        if pause:
            assert accepted.pacing_not_before==d.NOW+timedelta(microseconds=1)
            e.clocks.utc+=timedelta(microseconds=1);e.clocks.ticks+=999
            assert (await e.eng.prepare(context(accepted))).wait_seconds==1e-9
            e.clocks.ticks+=1
        assert (await e.eng.prepare(context(accepted))).batch.after_id==102
        assert len(e.sender.reads)==2


async def test_unknown_recovery_and_retry_preserve_one_full_wait():
    e=await unknown();e.clocks.advance(60);fresh=engine(e)
    before=await e.store.load(CHAT)
    result=await fresh.recover(e.ctx.run,**e.command)
    assert result.applied and result.status.after_id==100 and result.status.pacing_ended_at is None
    assert result.status.pacing_not_before==d.NOW+timedelta(seconds=300)
    assert result.status.attempt_id is None and result.status.pending_batch_id is None
    assert not result.status.source_exhausted and result.status.terminal_outcome is None
    saved=await e.store.load(CHAT);assert saved!=before
    for _ in range(3):
        retry=await engine(e,forbid=True).recover(e.ctx.run,**e.command)
        assert not retry.applied and retry.status==result.status
        assert await e.store.load(CHAT)==saved
    assert (await fresh.prepare(context(result.status))).wait_seconds==240
    e.clocks.advance(240)
    assert (await engine(e,reader=e.tg.get_message_batch).prepare(context(result.status))).batch.after_id==100


async def test_known_cancelled_end_keeps_original_deadline():
    e=await unknown();e.clocks.advance(60)
    result=await e.eng.recover(e.ctx.run,**e.command)
    assert result.status.pacing_ended_at==d.NOW
    assert result.status.pacing_not_before==d.NOW+timedelta(seconds=240)
    assert (await e.eng.prepare(context(result.status))).wait_seconds==180
    e.clocks.advance(180)
    assert (await e.eng.prepare(context(result.status))).batch.after_id==100


async def test_known_end_survives_failed_publication_and_long_storage_await():
    e=await setup();fault=d.FaultStore(e.store);fault.fail[2]=OSError(d.SECRET);e.eng._store=fault
    await f.expect(BackfillStorageError,e.eng.prepare(e.ctx))
    command_args=command(await e.eng.status(e.ctx.run));e.clocks.advance(60)
    result=await e.eng.recover(e.ctx.run,**command_args)
    assert result.status.pacing_not_before==d.NOW+timedelta(seconds=240)
    # A new engine has no end evidence; time spent awaiting its CAS is real quiet
    # time after quiescence, not a reason to restart the interval on reply.
    u=await unknown();fresh=engine(u);slow=d.FaultStore(u.store)
    async def delay(n,*a):u.clocks.advance(300)
    slow.hook=delay;fresh._store=slow
    recovered=await fresh.recover(u.ctx.run,**u.command)
    assert recovered.status.last_recovery_at==d.NOW
    assert recovered.status.pacing_not_before==d.NOW+timedelta(seconds=240)
    assert (await engine(u,reader=u.tg.get_message_batch).prepare(context(recovered.status))).batch


async def test_recovery_quiescence_input_scope_and_capacity_refusals():
    e=await unknown();saved=await e.store.load(CHAT);fresh=engine(e,forbid=True)
    for changes,kind in [(dict(previous_reader_stopped=False),BackfillConflictError),
                         (dict(previous_reader_stopped=1),BackfillConfigurationError),
                         (dict(expected_control_revision=True),BackfillConfigurationError),
                         (dict(expected_control_revision=1),BackfillConflictError),
                         (dict(attempt_id='other'),BackfillConflictError),
                         (dict(command_id='bad command'),BackfillConfigurationError)]:
        args=dict(e.command,**changes)
        await f.expect(kind,fresh.recover(e.ctx.run,**args));assert await e.store.load(CHAT)==saved
    f.rejected(TypeError,lambda:fresh.recover(e.ctx.run,attempt_id=e.command['attempt_id'],
        command_id='r',expected_control_revision=0))
    await f.expect(BackfillUnknownRun,fresh.recover(replace(e.ctx.run,run_id='other'),**e.command))
    await f.expect(BackfillConfigurationError,fresh.recover(replace(e.ctx.run,collection_id='other'),**e.command))
    doc=json.loads(saved);doc['state_revision']=str(MAX_LONG)
    assert await e.store.compare_and_swap(CHAT,saved,_BackfillState(doc).to_json())
    await f.expect(BackfillConflictError,fresh.recover(e.ctx.run,**e.command))


async def test_local_active_read_admission_and_publication_all_refuse_recovery():
    for phase in ('read','admit','publish'):
        e=await setup();fault=d.FaultStore(e.store);e.eng._store=fault
        if phase=='read':e.sender.script=[f.PENDING]
        else:fault.hold=1 if phase=='admit' else 2
        task=asyncio.create_task(e.eng.prepare(e.ctx))
        if phase=='read':await d.until(lambda:bool(e.sender.pending))
        else:await asyncio.wait_for(fault.entered.wait(),5)
        status=await e.eng.status(e.ctx.run)
        args=dict(attempt_id=status.attempt_id or status.pacing_attempt_id,command_id='r',
                  expected_control_revision=0,previous_reader_stopped=True)
        raw=await e.store.load(CHAT)
        await f.expect(BackfillConflictError,e.eng.recover(e.ctx.run,**args))
        assert await e.store.load(CHAT)==raw
        task.cancel();await f.expect(asyncio.CancelledError,task)
        assert len(e.sender.reads)==(0 if phase=='admit' else 1)
        if phase=='publish':
            result=await engine(e,forbid=True).recover(e.ctx.run,**args)
            assert result.outcome=='settled' and not result.applied and result.status.pending_message_count==2


async def test_recovery_recognizes_original_input_across_controls():
    e=await unknown();result=await engine(e).recover(e.ctx.run,**e.command)
    await d.control_fixture(e.store,'pause');saved=await e.store.load(CHAT)
    local=engine(e,forbid=True)
    retry=await local.recover(e.ctx.run,**e.command)
    assert not retry.applied and retry.status.operator_intent=='paused'
    for changes in (dict(attempt_id='other'),dict(expected_control_revision=1)):
        await f.expect(BackfillConflictError,local.recover(e.ctx.run,**dict(e.command,**changes)))
    await f.expect(BackfillConflictError,local.recover(e.ctx.run,**dict(e.command,command_id='new')))
    latest=json.loads(saved)['current']['last_control']['command_id']
    await f.expect(BackfillConflictError,local.recover(e.ctx.run,**dict(e.command,command_id=latest,expected_control_revision=1)))
    assert await e.store.load(CHAT)==saved


async def test_recovery_preserves_paused_cancelled_and_stronger_saved_deadline():
    for action in ('pause','cancel'):
        e=await unknown();await d.control_fixture(e.store,action)
        args=dict(e.command,expected_control_revision=1)
        result=await engine(e).recover(e.ctx.run,**args)
        assert result.status.operator_intent==('paused' if action=='pause' else 'cancelled')
        assert result.status.terminal_outcome==(None if action=='pause' else 'cancelled')
        assert (await engine(e,forbid=True).prepare(context(result.status))).wait_seconds is None
    e=await unknown();raw=await e.store.load(CHAT);doc=json.loads(raw)
    deadline=d.NOW+timedelta(seconds=600)
    doc['current']['pacing']=dict(attempt_id='older-settled-attempt',ended_at=_encode_date(d.NOW),
        not_before=_encode_date(deadline),clock_uncertain=False)
    assert await e.store.compare_and_swap(CHAT,raw,_BackfillState(doc).to_json())
    result=await engine(e).recover(e.ctx.run,**e.command)
    assert result.status.pacing_not_before==deadline
    assert (await engine(e).prepare(context(result.status))).wait_seconds==600


async def test_reconcile_pending_completed_and_failure_without_clock_or_artifacts():
    for outcome in ('pending','completed','failure'):
        e=await setup()
        if outcome=='failure':e.sender.script=[ConnectionError('owned source failure')]
        else:e.sender.script=[d.finite_response([f.message(101)])]
        if outcome=='failure':await f.expect(ConnectionError,e.eng.prepare(e.ctx))
        else:
            turn=await e.eng.prepare(e.ctx)
            if outcome=='completed':await e.eng.acknowledge(turn.delivery)
        status=await e.eng.status(e.ctx.run);saved=await e.store.load(CHAT)
        args=dict(attempt_id=status.pacing_attempt_id,command_id='inspect-result',
                  expected_control_revision=0,previous_reader_stopped=True)
        with patch('tgdata.backfill_engine._verify_existing',side_effect=AssertionError('recovery is not replay')):
            result=await engine(e,forbid=True).recover(e.ctx.run,**args)
        assert result.outcome=='settled' and not result.applied and result.status==status
        assert await e.store.load(CHAT)==saved
    # Actual download pending is still reconcilable after local bytes disappear.
    e=await setup(media_mode='download',batch_size=1)
    e.sender.files[d.b.ASSET_ID]=d.b.PAYLOAD;d.b.script_messages(e.sender,[d.b.document()])
    media=d.b.directory();turn=await e.eng.prepare(e.ctx,download_media_to=media)
    for file in media.iterdir():file.unlink()
    status=turn.status
    result=await engine(e,forbid=True).recover(e.ctx.run,attempt_id=status.pacing_attempt_id,
        command_id='inspect-download',expected_control_revision=0,previous_reader_stopped=True)
    assert result.status.pending_batch_id==turn.batch.batch_id and len(e.sender.reads)==1


async def test_old_recovery_never_clears_newer_attempt_or_pending():
    e=await unknown(0);recovered=await engine(e).recover(e.ctx.run,**e.command)
    e.sender.script=[f.PENDING]
    worker=engine(e,reader=e.tg.get_message_batch)
    task=asyncio.create_task(worker.prepare(context(recovered.status)))
    await d.until(lambda:len(e.sender.pending)==2)
    before=await e.store.load(CHAT)
    status=await worker.status(e.ctx.run);assert status.attempt_id!=e.command['attempt_id']
    await f.expect(BackfillConflictError,worker.recover(e.ctx.run,**e.command))
    retry=await engine(e,forbid=True).recover(e.ctx.run,**e.command)
    assert not retry.applied and retry.status.attempt_id==status.attempt_id
    await f.expect(BackfillConflictError,engine(e,forbid=True).recover(e.ctx.run,**dict(e.command,command_id='unknown')))
    assert await e.store.load(CHAT)==before
    e.sender.pending[-1].set_result(d.finite_response([f.message(101)]));turn=await task
    saved=await e.store.load(CHAT)
    await f.expect(BackfillConflictError,engine(e,forbid=True).recover(e.ctx.run,**e.command))
    assert await e.store.load(CHAT)==saved and turn.status.pending_message_count==1


async def test_recovery_actual_commit_error_nonbool_and_unreadable_reply():
    for committed in (False,True):
        for nonbool in (False,True):
            e=await unknown();e.clocks.advance(10)
            fault=AmbiguousStore(e.store,committed=committed,nonbool=nonbool)
            call=engine(e,store=fault).recover(e.ctx.run,**e.command)
            if committed:
                result=await call;assert result.applied and result.status.attempt_id is None
            else:
                await f.expect(BackfillStorageError,call)
                assert (await e.eng.status(e.ctx.run)).attempt_id==e.command['attempt_id']
            assert fault.writes==1 and fault.readbacks==1
    for readback in ('outage','corrupt','missing'):
        e=await unknown();fault=AmbiguousStore(e.store,readback=readback)
        await f.expect(BackfillStateError if readback=='corrupt' else BackfillStorageError,
            engine(e,store=fault).recover(e.ctx.run,**e.command))
        saved=await e.store.load(CHAT)
        retry=await engine(e,forbid=True).recover(e.ctx.run,**e.command)
        assert not retry.applied and retry.status.attempt_id is None and await e.store.load(CHAT)==saved


async def test_cancelled_recovery_commit_or_readback_stays_reconcilable():
    for where in ('commit','readback'):
        e=await unknown()
        if where=='commit':fault=d.FaultStore(e.store);fault.hold=1
        else:fault=AmbiguousStore(e.store,readback='hold')
        task=asyncio.create_task(engine(e,store=fault).recover(e.ctx.run,**e.command))
        await asyncio.wait_for(fault.entered.wait(),5);task.cancel()
        error=await f.expect(asyncio.CancelledError,task)
        assert health.classify(error,True) is None and error.__cause__ is None
        saved=await e.store.load(CHAT)
        result=await engine(e,forbid=True).recover(e.ctx.run,**e.command)
        assert not result.applied and result.status.attempt_id is None and await e.store.load(CHAT)==saved


async def test_concurrent_recoveries_have_one_durable_effect():
    for same_command in (True,False):
        e=await unknown();ready=asyncio.Event()
        class Barrier:
            count=0
            async def load(self,chat):
                raw=await e.store.load(chat);self.count+=1
                if self.count<=2:
                    if self.count==2:ready.set()
                    await ready.wait()
                return raw
            async def compare_and_swap(self,*a):return await e.store.compare_and_swap(*a)
        store=Barrier()
        args=e.command if same_command else dict(e.command,command_id='recover-2')
        results=await asyncio.gather(engine(e,store=store).recover(e.ctx.run,**e.command),
            engine(e,store=store).recover(e.ctx.run,**args))
        assert sum(result.applied for result in results)==1
        assert results[0].status==results[1].status
        assert {r.outcome for r in results}==({'recovered'} if same_command else {'recovered','settled'})
        assert results[0].status.state_revision==3


async def test_recovery_false_cas_does_not_rebase_control_or_loop_forever():
    e=await unknown();fault=d.FaultStore(e.store)
    async def pause(n,*a):
        if n==1:await d.control_fixture(e.store,'pause');return False
    fault.hook=pause
    await f.expect(BackfillConflictError,engine(e,store=fault).recover(e.ctx.run,**e.command))
    current=await e.eng.status(e.ctx.run)
    assert current.attempt_id==e.command['attempt_id'] and current.control_revision==1 and fault.calls==1
    e=await unknown();fault=d.FaultStore(e.store)
    async def conflicts(*a):return False
    fault.hook=conflicts
    await f.expect(BackfillConflictError,engine(e,store=fault).recover(e.ctx.run,**e.command))
    assert fault.calls==4 and (await e.eng.status(e.ctx.run)).attempt_id==e.command['attempt_id']


async def test_invalid_recovery_clock_missing_or_corrupt_state_never_repairs():
    for fault in ('past','raising','corrupt','absent'):
        e=await unknown();before=await e.store.load(CHAT);local=engine(e)
        if fault=='past':e.clocks.utc-=timedelta(seconds=1);kind=BackfillClockError
        elif fault=='raising':
            def broken():raise OSError(d.SECRET)
            local._clock=broken;kind=BackfillClockError
        elif fault=='corrupt':
            assert await e.store.compare_and_swap(CHAT,before,'{bad');kind=BackfillStateError
        else:
            with sqlite3.connect(e.store.path) as db:db.execute('DELETE FROM tgdata_sync_state')
            kind=BackfillUnknownRun
        saved=await e.store.load(CHAT)
        error=await f.expect(kind,local.recover(e.ctx.run,**e.command))
        assert d.SECRET not in str(error) and await e.store.load(CHAT)==saved


async def test_budget_prefix_expired_hint_and_account_switch_recheck_actual_guard():
    budget,budget_clock=f.ledger(3)
    e=await setup(budget=budget,batch_size=5);e.client._mb_entity_cache.set_self_user(999,False,999)
    original=await f.expect(ReadBudgetExceeded,e.eng.prepare(e.ctx))
    status=await e.eng.status(e.ctx.run)
    assert status.pending_message_count==3 and status.last_failure_account_id==f.ACCOUNT
    assert status.last_failure_retry_at==datetime.fromtimestamp(budget_clock.value+86400,timezone.utc)
    replay=await engine(e,forbid=True).prepare(e.ctx)
    assert replay.batch.to_json()==original.partial_result.to_json()
    accepted=await e.eng.acknowledge(replay.delivery)
    assert (await e.eng.prepare(context(accepted))).wait_seconds==240
    # Lifecycle UTC says the hint expired; the independent actual quota clock has
    # not expired its charges. Saved hints therefore cannot grant capacity.
    e.clocks.advance(86400)
    await f.expect(ReadBudgetExceeded,e.eng.prepare(context(accepted)))
    assert len(e.sender.reads)==1 and budget.status(f.ACCOUNT).used==3
    current=await e.eng.status(e.ctx.run);assert current.pending_batch_id is None
    e.clocks.advance(240)
    budget.configure(222,5);e.sender.account=222
    turn=await e.eng.prepare(context(current))
    assert turn.batch.after_id==103 and len(turn.batch.messages)==5
    assert budget.status(222).used==5 and budget.status(f.ACCOUNT).used==3
    assert turn.status.last_failure_account_id==f.ACCOUNT  # explicitly historical


async def test_indefinite_budget_stop_is_not_zero_wait_or_completion():
    budget,_=f.ledger(0);e=await setup(5,budget=budget)
    await f.expect(ReadBudgetExceeded,e.eng.prepare(e.ctx))
    status=await e.eng.status(e.ctx.run)
    assert status.last_failure_retry_at is None and status.last_failure_kind=='budget'
    assert status.pending_batch_id is None and not status.source_exhausted and status.terminal_outcome is None
    assert (await e.eng.prepare(e.ctx)).wait_seconds==5 and not e.sender.reads
    e.clocks.advance(5)
    await f.expect(ReadBudgetExceeded,e.eng.prepare(e.ctx));assert not e.sender.reads
    budget.configure(f.ACCOUNT,2);e.clocks.advance(5)
    assert (await e.eng.prepare(e.ctx)).batch.next_after_id==102


async def test_recovery_never_refunds_cancelled_budget_claims():
    budget,_=f.ledger(5);e=await unknown(5,budget=budget)
    before=budget.status(f.ACCOUNT);assert before.used==before.reserved==2
    recovered=await engine(e).recover(e.ctx.run,**e.command)
    assert budget.status(f.ACCOUNT).used==before.used
    budget.configure(f.ACCOUNT,6)  # disposable offline policy; existing charges survive
    assert budget.status(f.ACCOUNT).used==2
    e.clocks.advance(5)
    assert (await e.eng.prepare(context(recovered.status))).batch.next_after_id==102
    assert budget.status(f.ACCOUNT).used==4 and budget.status(f.ACCOUNT).reserved==2


async def test_direct_sdk_wait_hint_keeps_original_error_without_cached_account():
    e=await setup();e.client.flood_sleep_threshold=0
    original=errors.FloodWaitError(None,capture=120);e.sender.script=[original]
    caught=await f.expect(errors.FloodWaitError,e.eng.prepare(e.ctx))
    assert caught is original
    status=await e.eng.status(e.ctx.run)
    assert status.last_failure_retry_at==d.NOW+timedelta(seconds=120)
    assert status.last_failure_account_id is None and status.last_failure_type=='FloodWaitError'
    assert status.pacing_not_before==d.NOW+timedelta(seconds=240) and not status.source_exhausted
    raw=await e.store.load(CHAT)
    assert (await e.eng.prepare(e.ctx)).wait_seconds==240 and await e.store.load(CHAT)==raw
    for hint in (None,True,-1,1.5,10**30):
        value=errors.FloodWaitError(None,capture=1);value.seconds=hint
        async def invalid(*a,**kw):raise value
        other=await setup();other.eng._read_batch=invalid
        assert await f.expect(errors.FloodWaitError,other.eng.prepare(other.ctx)) is value
        assert (await other.eng.status(other.ctx.run)).last_failure_retry_at is None


async def test_local_error_context_does_not_supply_source_hint_or_health():
    e=await setup(events=[])
    async def local_failure(*a,**kw):
        try:raise errors.FloodWaitError(None,capture=120)
        except Exception:raise ReadBudgetError('local refusal under incidental RPC context')
    e.eng._read_batch=local_failure
    original=await f.expect(ReadBudgetError,e.eng.prepare(e.ctx))
    status=await e.eng.status(e.ctx.run)
    assert status.last_failure_retry_at is None and status.last_failure_account_id is None
    assert health.classify(original,True) is None and not status.source_exhausted
    # Local pacing/recovery never clear a recorded Telegram group failure.
    await e.tg._health._emit(health.Finding(health.NO_ACCESS,'group','CHANNEL_PRIVATE',None,None),None,'error',CHAT)
    before=e.tg._health.snapshot()
    await e.eng.prepare(e.ctx)
    await e.eng.recover(e.ctx.run,attempt_id=status.pacing_attempt_id,command_id='inspect',
        expected_control_revision=0,previous_reader_stopped=True)
    after=e.tg._health.snapshot()
    assert before['events']==after['events'] and before['no_access']==after['no_access']


async def test_cancelled_end_clock_failure_does_not_replace_cancellation():
    e=await setup();e.sender.script=[f.PENDING]
    task=asyncio.create_task(e.eng.prepare(e.ctx));await d.until(lambda:bool(e.sender.pending))
    def fail():raise OSError(d.SECRET)
    e.eng._monotonic_ns=fail;task.cancel()
    error=await f.expect(asyncio.CancelledError,task)
    assert error.__cause__ is None and health.classify(error,True) is None
    status=await e.eng.status(e.ctx.run);e.clocks.advance(60)
    result=await engine(e).recover(e.ctx.run,**command(status))
    assert result.status.pacing_ended_at is None
    assert result.status.pacing_not_before==d.NOW+timedelta(seconds=300)


async def test_unrepresentable_end_and_recovery_deadlines_leave_attempt_unknown():
    maximum=datetime.max.replace(tzinfo=timezone.utc)
    clocks=Clocks(maximum-timedelta(seconds=600));e=await setup(clocks=clocks)
    async def reader(*a,**kw):
        result=await e.tg.get_message_batch(*a,**kw);clocks.advance(590);return result
    e.eng._read_batch=reader
    await f.expect(BackfillClockError,e.eng.prepare(e.ctx))
    status=await e.eng.status(e.ctx.run);assert status.attempt_id
    saved=await e.store.load(CHAT)
    await f.expect(BackfillClockError,engine(e).recover(e.ctx.run,**command(status)))
    assert await e.store.load(CHAT)==saved and len(e.sender.reads)==1


async def test_real_elapsed_wait_does_not_sleep_inside_engine():
    e=await setup(0.04);observed=[]
    async def reader(*a,**kw):
        observed.append(time.monotonic_ns());return await e.tg.get_message_batch(*a,**kw)
    real=BackfillEngine(e.store,e.req.collection_id,read_batch=reader)
    turn=await real.prepare(e.ctx);accepted=await real.acknowledge(turn.delivery)
    for _ in range(5):
        later=await real.prepare(context(accepted))
        if later.batch:break
        assert later.wait_seconds>0
        await asyncio.sleep(later.wait_seconds+0.003)
    else:raise AssertionError('measured wait did not elapse')
    assert len(observed)==2 and observed[1]-observed[0]>=40_000_000


async def test_generation_change_does_not_reuse_an_old_wait_anchor():
    e=await setup();e.sender.script=[d.finite_response([f.message(101)])]
    turn=await e.eng.prepare(e.ctx);complete=await e.eng.acknowledge(turn.delivery)
    req=replace(e.req,run_id='successor',expected_predecessor=e.ctx.run)
    created=await e.eng.start(req,submission='new')
    assert created.status.run.generation==2 and created.status.pacing_not_before is None
    next_turn=await e.eng.prepare(context(created.status))
    assert next_turn.batch is not None and len(e.sender.reads)==2
    # Retained prior-run source outcome is read-only reconciliation.
    result=await engine(e,forbid=True).recover(e.ctx.run,attempt_id=complete.pacing_attempt_id,
        command_id='old-inspection',expected_control_revision=0,previous_reader_stopped=True)
    assert result.status.history_limited and result.status.run==e.ctx.run and not result.applied


async def test_recovery_cas_race_cannot_clear_a_replacement_attempt():
    e=await unknown(0);fault=d.FaultStore(e.store);tasks=[];other=engine(e,reader=e.tg.get_message_batch)
    async def change(n,*a):
        if n==1:
            recovered=await other.recover(e.ctx.run,**dict(e.command,command_id='other-recovery'))
            e.sender.script=[f.PENDING]
            tasks.append(asyncio.create_task(other.prepare(context(recovered.status))))
            await d.until(lambda:len(e.sender.pending)==2)
            return False
    fault.hook=change
    try:
        await f.expect(BackfillConflictError,engine(e,store=fault).recover(e.ctx.run,**e.command))
        status=await other.status(e.ctx.run)
        assert status.attempt_id!=e.command['attempt_id'] and status.last_recovery_id=='other-recovery'
        assert fault.calls==1 and len(e.sender.reads)==2
    finally:
        for task in tasks:task.cancel();await f.expect(asyncio.CancelledError,task)


async def crash(path,phase,boundary):
    store=SQLiteSyncStore(path,create=False)
    e=SimpleNamespace(store=store,req=d.request(pause_seconds=240),clocks=Clocks())
    async def exit_source(*a,**kw):os._exit(80)
    eng=engine(e,reader=exit_source)
    status=(await eng.start(e.req,submission='retry')).status
    if phase=='source':await eng.prepare(context(status));raise AssertionError('expected source exit')
    original=sqlite3.connect
    class Crash(sqlite3.Connection):
        def commit(self):
            hit=False
            if self.total_changes:
                row=json.loads(self.execute('SELECT data FROM tgdata_sync_state').fetchone()[0])['current']
                hit=row['last_recovery'] is not None
            if hit and boundary=='before':os._exit(81)
            super().commit()
            if hit and boundary=='after':os._exit(82)
    def connect(*a,**kw):kw['factory']=Crash;return original(*a,**kw)
    with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
        await eng.recover(status.run,**command(status))
    raise AssertionError('actual recovery commit boundary not reached')


async def run_child(path,phase,boundary,expected):
    args=[sys.executable,__file__,'--crash',path,phase,boundary]
    if hasattr(asyncio,'to_thread'):
        result=await asyncio.to_thread(subprocess.run,args,capture_output=True,text=True,timeout=25)
    else:result=subprocess.run(args,capture_output=True,text=True,timeout=25)
    assert result.returncode==expected,(result.returncode,result.stderr)


async def test_process_exit_recovery_before_after_commit_keeps_exact_deadline():
    for boundary in ('before','after'):
        e=await setup()
        await run_child(e.store.path,'source','unused',80)  # child really exited after durable admission
        status=await e.eng.status(e.ctx.run);args=command(status);raw=await e.store.load(CHAT)
        await run_child(e.store.path,'recovery',boundary,81 if boundary=='before' else 82)
        saved=await e.store.load(CHAT)
        if boundary=='before':
            assert saved==raw
            await f.expect(BackfillRecoveryRequired,engine(e,forbid=True).prepare(e.ctx))
        else:
            local=engine(e,store=SQLiteSyncStore(e.store.path,create=False),forbid=True)
            recovered=await local.recover(e.ctx.run,**args)
            assert not recovered.applied and recovered.status.pacing_ended_at is None
            assert recovered.status.pacing_not_before==d.NOW+timedelta(seconds=240)
            assert recovered.status.after_id==100 and not recovered.status.source_exhausted
            assert recovered.status.pending_batch_id is None and await e.store.load(CHAT)==saved
            assert (await engine(e).prepare(context(recovered.status))).wait_seconds==240


async def main():
    tests=[v for k,v in globals().items() if k.startswith('test_') and asyncio.iscoroutinefunction(v)]
    print('Backfill Pacing/Recovery Tests — Telethon {}; LOCAL/INJECTED actual SQLite/SDK'.format(telethon.__version__))
    assert telethon.__version__=='1.45.0';passed=0
    with tempfile.TemporaryDirectory(prefix='tgdata_backfill_pacing_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        d.TMP=Path(tmp);f.TMP=d.TMP
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


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--crash':
        with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
             patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
            asyncio.run(crash(*sys.argv[2:]))
    else:sys.exit(asyncio.run(main()))
