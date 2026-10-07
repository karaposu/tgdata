"""Stage 3 delivery: actual SQLite/SDK/media, synthetic transport, no network.

Seeded control/recovery snapshots test compatibility, not unimplemented operations.
Run: python -m tgdata.smoke_tests.test_25_backfill_delivery
"""
import asyncio
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta, timezone
import itertools
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import telethon
from telethon import errors, types
from tgdata import MessageBatch, SQLiteSyncStore, ReadBudgetExceeded, health
from tgdata.backfill import (
    BackfillRunRef, BackfillStartRequest, BackfillPrepareContext, BackfillDeliveryRef,
    BackfillTurn, BackfillError, BackfillConfigurationError, BackfillConflictError,
    BackfillUnknownRun, BackfillUnknownReceipt, BackfillRecoveryRequired,
    BackfillMediaError, BackfillClockError, BackfillStateError, BackfillStorageError,
)
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill_state import _BackfillState
from tgdata.history_window import _encode_date
from tgdata.message_batch import MAX_LONG
from tgdata.smoke_tests import test_19_message_batches as b

f=b.f
CHAT=-1000000000007
COLLECTION='delivery-tests'
NOW=b.NOW+timedelta(seconds=10)
START,END=b.NOW-timedelta(days=1),b.NOW+timedelta(seconds=1)
SECRET='PRIVATE_BACKEND_TEXT_MUST_NOT_ESCAPE'
TMP=None
NUMBERS=itertools.count(1)


def clock():return NOW
def forbidden_clock():raise AssertionError('local replay/retry must not read the clock')
async def forbidden_reader(*args,**kwargs):raise AssertionError('source must not be called')
def store():return SQLiteSyncStore(TMP/('delivery_{}.sqlite3'.format(next(NUMBERS))))


def request(run_id='run-1',**changes):
    args=dict(collection_id=COLLECTION,chat_id=CHAT,run_id=run_id,destination_id='archive',
              pause_seconds=0,expected_predecessor=None,origin='imported',after_id=100,
              batch_size=2,start_date=START,end_date=END)
    args.update(changes)
    return BackfillStartRequest(**args)


def engine(backend,reader=None,now=clock,collection=COLLECTION):
    return BackfillEngine(backend,collection,read_batch=reader,clock=now)


async def setup(budget=None,events=None,**changes):
    backend=store();tg,client,sender=b.instance(budget,events=events)
    req=request(**changes);eng=engine(backend,tg.get_message_batch)
    status=(await eng.start(req,submission='new')).status
    return backend,eng,tg,client,sender,req,BackfillPrepareContext.from_status(status)


async def prepared(**changes):
    values=await setup(**changes)
    turn=await values[1].prepare(values[-1])
    return values,turn


def sample(after=100,count=1,stop='limit',chat=CHAT,mode='references',date=None):
    record=json.loads(b.GOLDEN)['messages'][0]
    records=[]
    for mid in range(after+1,after+count+1):
        row=dict(record,id=str(mid),date=_encode_date(date or b.NOW),media=None)
        records.append(row)
    return MessageBatch._from_records(chat,after,records,mode,stop)


def finite_response(messages):
    # Unlike a short MessagesSlice, this wire type explicitly represents the
    # complete result. A short slice alone must not be treated as exhaustion.
    return types.messages.Messages(messages=list(messages),topics=[],chats=[f.room()],
        users=[types.User(id=88,access_hash=88,first_name='Author')])


async def until(predicate):
    for _ in range(2000):
        if predicate():return
        await asyncio.sleep(0.001)
    raise AssertionError('expected barrier was not reached')


class FaultStore:
    """Inject around actual SQLite; counters start after enrollment."""
    def __init__(self,actual):
        self.actual=actual;self.calls=0;self.fail={};self.after={};self.hook=None
        self.entered=asyncio.Event();self.release=asyncio.Event();self.hold=None
    async def load(self,chat):return await self.actual.load(chat)
    async def compare_and_swap(self,*args):
        self.calls+=1;n=self.calls
        if self.hook is not None:
            result=await self.hook(n,*args)
            if result is not None:return result
        if n in self.fail:
            value=self.fail[n]
            if isinstance(value,BaseException):raise value
            return value
        written=await self.actual.compare_and_swap(*args)
        if n==self.hold:
            self.entered.set();await self.release.wait()
        if n in self.after:raise self.after[n]
        return written


async def control_fixture(backend,action):
    """A valid future control write for a race; not a control API implementation."""
    raw=await backend.load(CHAT);value=json.loads(raw);row=value['current']
    assert row['terminal_outcome'] is None
    old=int(row['control_revision']);row['control_revision']=str(old+1)
    value['state_revision']=str(int(value['state_revision'])+1)
    row['operator_intent']={'pause':'paused','resume':'active','cancel':'cancelled'}[action]
    if action=='cancel':row['terminal_outcome']='cancelled'
    row['last_control']=dict(command_id='fixture-{}-{}'.format(action,old),action=action,
        expected_revision=str(old),accepted_revision=str(old+1),state_revision=value['state_revision'])
    assert await backend.compare_and_swap(CHAT,raw,_BackfillState(value).to_json())


async def test_values_are_exact_owned_and_not_public_facade():
    ref=BackfillRunRef('collection',-9007199254740993,9007199254740993,'run')
    context=BackfillPrepareContext(ref,101,9007199254740993)
    delivery=BackfillDeliveryRef(ref,'destination','a'*64)
    assert BackfillPrepareContext.from_dict(context.to_dict())==context
    assert BackfillDeliveryRef.from_dict(delivery.to_dict())==delivery
    assert context.to_dict()['expected_control_revision']=='9007199254740993'
    for call in [lambda:BackfillPrepareContext(ref,True,0),lambda:BackfillPrepareContext(ref,0,-1),
                 lambda:BackfillDeliveryRef(ref,'bad destination','a'*64),
                 lambda:BackfillDeliveryRef(ref,'archive','A'*64),
                 lambda:BackfillPrepareContext.from_dict(dict(context.to_dict(),extra=1))]:
        f.rejected(BackfillConfigurationError,call)
    f.rejected(FrozenInstanceError,lambda:setattr(delivery,'batch_id','b'*64))
    import tgdata
    assert not hasattr(tgdata,'BackfillTurn') and not hasattr(tgdata.TgData,'prepare_backfill')
    assert not hasattr(BackfillEngine,'control') and not hasattr(BackfillEngine,'recover')


async def test_confirmed_admission_precedes_actual_reader_without_db_lock():
    backend,eng,tg,_,sender,req,ctx=await setup()
    observed=[]
    async def reader(chat,**kwargs):
        value=json.loads(await backend.load(chat));row=value['current']
        assert value['state_revision']=='2' and row['attempt']['after_id']=='100'
        assert row['attempt']['control_revision']=='0' and row['pending'] is None
        assert kwargs==dict(after_id=100,limit=2,download_media_to=None,start_date=START,end_date=END)
        db=sqlite3.connect(backend.path,timeout=0);db.execute('BEGIN IMMEDIATE');db.rollback();db.close()
        result=await tg.get_message_batch(chat,**kwargs);observed.append(result.to_json());return result
    turn=await engine(backend,reader).prepare(ctx)
    assert turn.batch.to_json()==observed[0] and not turn.replayed
    assert turn.status.after_id==100 and turn.status.pending_next_after_id==102
    assert turn.status.attempt_id is None and turn.status.state_revision==3
    assert turn.delivery==BackfillDeliveryRef(ctx.run,req.destination_id,turn.batch.batch_id)
    assert len(sender.reads)==1
    changed=turn.to_dict();changed['batch']['messages'][0]['text']='changed'
    assert turn.batch.to_json()==observed[0]


async def test_restart_replay_is_offline_exact_and_has_no_clock():
    (backend,eng,tg,_,sender,req,ctx),turn=await prepared()
    before=await backend.load(CHAT);reads=len(sender.reads)
    local=engine(SQLiteSyncStore(backend.path,create=False),forbidden_reader,forbidden_clock)
    replay=await local.prepare(ctx)
    assert replay.replayed and replay.batch.to_json()==turn.batch.to_json()
    assert replay.delivery==turn.delivery and replay.status==turn.status
    assert await backend.load(CHAT)==before and len(sender.reads)==reads
    f.rejected(BackfillConfigurationError,lambda:BackfillTurn(turn.status))
    f.rejected(BackfillConfigurationError,lambda:BackfillTurn(turn.status,turn.batch,
        replace(turn.delivery,destination_id='wrong')))


async def test_fresh_relative_query_uses_original_window_after_clock_moves():
    backend,_,tg,_,sender,_,ctx=await setup(origin='fresh',after_id=0,
        start_date=None,end_date=None,last_days=30)
    original=await engine(backend).status(ctx.run)
    async def reader(chat,**options):
        assert options['after_id']==0 and options['start_date']==NOW-timedelta(days=30)
        assert options['end_date']==NOW
        return await tg.get_message_batch(chat,**options)
    eng=engine(backend,reader,lambda:NOW+timedelta(days=90))
    turn=await eng.prepare(ctx)
    assert turn.status.origin=='fresh' and turn.status.initial_after_id==0
    assert turn.status.start_date==original.start_date and turn.status.end_date==original.end_date
    assert turn.batch.after_id==0 and turn.batch.next_after_id==2
    assert (await eng.acknowledge(turn.delivery)).after_id==2 and len(sender.reads)==1


async def test_scoped_ack_duplicate_and_zero_pause_continuation():
    (backend,eng,tg,_,sender,req,ctx),first=await prepared()
    paced=first.status.pacing_not_before
    accepted=await engine(backend,forbidden_reader).acknowledge(first.delivery)
    assert accepted.after_id==102 and accepted.pending_batch_id is None
    assert accepted.state_revision==4 and accepted.pacing_not_before==paced
    before=await backend.load(CHAT)
    duplicate=await engine(backend,forbidden_reader,forbidden_clock).acknowledge(first.delivery)
    assert duplicate==accepted and await backend.load(CHAT)==before
    await f.expect(BackfillConflictError,eng.prepare(ctx))
    second=await eng.prepare(BackfillPrepareContext.from_status(accepted))
    assert second.batch.after_id==102 and second.batch.next_after_id==104
    newer=await backend.load(CHAT)
    repeated=await engine(backend,forbidden_reader,forbidden_clock).acknowledge(first.delivery)
    assert repeated.pending_batch_id==second.batch.batch_id and repeated.after_id==102
    assert await backend.load(CHAT)==newer and len(sender.reads)==2


async def test_wrong_and_unknown_receipts_preserve_pending():
    (backend,eng,_,_,sender,req,ctx),turn=await prepared()
    before=await backend.load(CHAT)
    for receipt,kind in [(replace(turn.delivery,destination_id='other'),BackfillConflictError),
                         (replace(turn.delivery,batch_id='0'*64),BackfillUnknownReceipt),
                         (replace(turn.delivery,run=replace(ctx.run,run_id='other')),BackfillUnknownRun),
                         (replace(turn.delivery,run=replace(ctx.run,generation=2)),BackfillUnknownRun),
                         (replace(turn.delivery,run=replace(ctx.run,collection_id='other')),BackfillConfigurationError)]:
        await f.expect(kind,engine(backend,forbidden_reader,forbidden_clock).acknowledge(receipt))
        assert await backend.load(CHAT)==before
    await f.expect(BackfillConfigurationError,eng.acknowledge(turn.batch.batch_id))
    assert len(sender.reads)==1


async def test_equal_hashes_in_distinct_runs_have_distinct_authority():
    one,first=await prepared(batch_size=1)
    two,second=await prepared(run_id='other-run',destination_id='other-destination',batch_size=1)
    assert first.batch.batch_id==second.batch.batch_id and first.delivery!=second.delivery
    before=await two[0].load(CHAT)
    await f.expect(BackfillUnknownRun,two[1].acknowledge(first.delivery))
    assert await two[0].load(CHAT)==before
    await two[1].acknowledge(second.delivery)
    assert (await one[1].status(first.status.run)).pending_batch_id==first.batch.batch_id


async def test_empty_and_final_end_obey_existing_codec_invariants():
    for count in (0,1):
        backend,eng,_,_,sender,_,ctx=await setup(batch_size=2)
        sender.script=[finite_response([f.message(101)] if count else [])]
        turn=await eng.prepare(ctx)
        assert turn.status.source_exhausted and turn.status.attempt_id is None
        if count:
            assert turn.batch.stop_reason=='end' and turn.status.terminal_outcome is None
            status=await eng.acknowledge(turn.delivery)
            assert status.after_id==101
        else:
            assert turn.batch is None and turn.delivery is None
            status=turn.status
        assert status.terminal_outcome=='completed'
        raw=await backend.load(CHAT)
        done=await engine(backend,forbidden_reader,forbidden_clock).prepare(BackfillPrepareContext.from_status(status))
        assert done.batch is None and done.status==status and await backend.load(CHAT)==raw


async def test_exact_full_batch_needs_real_end_not_length():
    backend,eng,_,_,sender,_,ctx=await setup(batch_size=1)
    first=await eng.prepare(ctx)
    status=await eng.acknowledge(first.delivery)
    assert not status.source_exhausted and status.terminal_outcome is None
    sender.script=[f.response([])]
    end=await eng.prepare(BackfillPrepareContext.from_status(status))
    assert end.status.terminal_outcome=='completed' and end.status.after_id==101
    assert len(sender.reads)==2


async def test_short_slice_is_not_itself_source_exhaustion():
    backend,eng,_,_,sender,_,ctx=await setup(batch_size=3)
    sender.script=[f.response([f.message(101)]),f.response([])]
    turn=await eng.prepare(ctx)
    assert len(sender.reads)==2 and len(turn.batch.messages)==1
    assert turn.batch.stop_reason=='end' and turn.status.source_exhausted
    assert turn.status.terminal_outcome is None


async def test_positive_pause_is_recorded_but_further_admission_stays_gated():
    (backend,eng,_,_,sender,_,ctx),turn=await prepared(pause_seconds=5)
    assert turn.status.pacing_not_before==NOW+timedelta(seconds=5)
    replay=await engine(backend,forbidden_reader,forbidden_clock).prepare(ctx)
    assert replay.replayed
    status=await eng.acknowledge(replay.delivery)
    before=await backend.load(CHAT)
    await f.expect(BackfillConfigurationError,engine(backend,forbidden_reader,
        lambda:NOW+timedelta(days=1)).prepare(BackfillPrepareContext.from_status(status)))
    assert await backend.load(CHAT)==before and len(sender.reads)==1


async def test_failed_or_unconfirmed_admission_never_calls_source():
    for fault in (False,1,OSError(SECRET),asyncio.CancelledError()):
        backend,_,tg,_,sender,_,ctx=await setup()
        wrapped=FaultStore(backend);wrapped.fail[1]=fault
        kind=(BackfillConflictError if fault is False else asyncio.CancelledError
              if isinstance(fault,asyncio.CancelledError) else BackfillStorageError)
        error=await f.expect(kind,engine(wrapped,tg.get_message_batch).prepare(ctx))
        assert SECRET not in str(error) and not sender.reads
        assert (await engine(backend).status(ctx.run)).attempt_id is None
    backend,_,tg,_,sender,_,ctx=await setup()
    wrapped=FaultStore(backend);wrapped.after[1]=OSError(SECRET)
    await f.expect(BackfillStorageError,engine(wrapped,tg.get_message_batch).prepare(ctx))
    assert not sender.reads and (await engine(backend).status(ctx.run)).attempt_id
    await f.expect(BackfillRecoveryRequired,engine(backend,forbidden_reader,forbidden_clock).prepare(ctx))


async def test_publication_failure_keeps_attempt_or_committed_pending():
    for committed in (False,True):
        backend,_,tg,_,sender,_,ctx=await setup()
        wrapped=FaultStore(backend)
        (wrapped.after if committed else wrapped.fail)[2]=OSError(SECRET)
        eng=engine(wrapped,tg.get_message_batch)
        if committed:
            confirmed=await eng.prepare(ctx)
            assert confirmed.batch.next_after_id==102 and not confirmed.replayed
            turn=await engine(backend,forbidden_reader,forbidden_clock).prepare(ctx)
            assert turn.replayed and turn.status.attempt_id is None and turn.batch.next_after_id==102
        else:
            error=await f.expect(BackfillStorageError,eng.prepare(ctx))
            assert SECRET not in str(error) and health.classify(error,True) is None
            await f.expect(BackfillRecoveryRequired,eng.prepare(ctx))
            assert (await engine(backend).status(ctx.run)).pending_batch_id is None
        assert len(sender.reads)==1


async def test_real_sqlite_post_commit_close_error_confirms_then_replays():
    backend,eng,_,_,sender,_,ctx=await setup()
    original=sqlite3.connect
    class BadClose(sqlite3.Connection):
        def close(self):
            pending=False
            if self.total_changes:
                pending=json.loads(self.execute('SELECT data FROM tgdata_sync_state').fetchone()[0])['current']['pending'] is not None
            super().close()
            if pending:raise sqlite3.OperationalError(SECRET)
    def connect(*args,**kwargs):kwargs['factory']=BadClose;return original(*args,**kwargs)
    with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
        confirmed=await eng.prepare(ctx)
    assert confirmed.batch.next_after_id==102 and len(sender.reads)==1
    replay=await engine(SQLiteSyncStore(backend.path,create=False),forbidden_reader,forbidden_clock).prepare(ctx)
    assert replay.replayed and replay.batch.next_after_id==102


async def test_same_engine_overlap_and_other_instance_unknown_attempt():
    backend,eng,tg,_,sender,_,ctx=await setup()
    sender.script=[f.PENDING]
    task=asyncio.create_task(eng.prepare(ctx));await until(lambda:bool(sender.pending))
    await f.expect(BackfillConflictError,eng.prepare(ctx))
    unknown=await f.expect(BackfillRecoveryRequired,engine(backend,forbidden_reader).prepare(ctx))
    assert unknown.status.attempt_id and len(sender.reads)==1
    task.cancel();await f.expect(asyncio.CancelledError,task)
    await f.expect(BackfillRecoveryRequired,eng.prepare(ctx))
    assert len(sender.reads)==1


async def test_two_instances_race_one_confirmed_admission():
    backend,_,tg,_,sender,_,ctx=await setup();ready=asyncio.Event()
    class Barrier:
        count=0
        async def load(self,chat):
            raw=await backend.load(chat);self.count+=1
            if self.count<=2:
                if self.count==2:ready.set()
                await ready.wait()
            return raw
        async def compare_and_swap(self,*args):return await backend.compare_and_swap(*args)
    barrier=Barrier()
    results=await asyncio.gather(engine(barrier,tg.get_message_batch).prepare(ctx),
        engine(barrier,tg.get_message_batch).prepare(ctx),return_exceptions=True)
    assert sum(isinstance(x,BackfillTurn) for x in results)==1
    assert sum(isinstance(x,BackfillConflictError) for x in results)==1
    assert len(sender.reads)==1


async def test_future_pause_or_cancel_during_read_preserves_result():
    for action in ('pause','cancel'):
        backend,eng,_,_,sender,_,ctx=await setup()
        sender.script=[f.PENDING]
        task=asyncio.create_task(eng.prepare(ctx));await until(lambda:bool(sender.pending))
        await control_fixture(backend,action)
        sender.pending[0].set_result(finite_response([f.message(101)]))
        turn=await task
        assert turn.status.control_revision==1 and turn.status.pending_message_count==1
        assert turn.status.operator_intent==('paused' if action=='pause' else 'cancelled')
        await f.expect(BackfillConflictError,eng.prepare(ctx))
        current=BackfillPrepareContext.from_status(turn.status)
        replay=await engine(backend,forbidden_reader,forbidden_clock).prepare(current)
        accepted=await eng.acknowledge(replay.delivery)
        assert accepted.terminal_outcome==('completed' if action=='pause' else 'cancelled')
        assert accepted.operator_intent==turn.status.operator_intent and len(sender.reads)==1


async def test_false_publication_cas_reloads_compatible_control_without_refetch():
    backend,_,tg,_,sender,_,ctx=await setup();wrapped=FaultStore(backend)
    async def change(n,*args):
        if n==2:
            await control_fixture(backend,'pause');return False
    wrapped.hook=change
    turn=await engine(wrapped,tg.get_message_batch).prepare(ctx)
    assert turn.status.operator_intent=='paused' and turn.status.control_revision==1
    assert wrapped.calls==3 and len(sender.reads)==1


async def test_bounded_conflicts_leave_source_result_unconfirmed():
    backend,_,tg,_,sender,_,ctx=await setup();wrapped=FaultStore(backend)
    async def conflict(n,*args):return False if n>1 else None
    wrapped.hook=conflict
    await f.expect(BackfillConflictError,engine(wrapped,tg.get_message_batch).prepare(ctx))
    assert wrapped.calls==5 and len(sender.reads)==1
    assert (await engine(backend).status(ctx.run)).attempt_id


async def test_budget_prefix_is_pending_with_verified_account_metadata():
    budget,_=f.ledger(3)
    backend,eng,_,client,sender,_,ctx=await setup(budget=budget,batch_size=5)
    client._mb_entity_cache.set_self_user(999,False,999)
    error=await f.expect(ReadBudgetExceeded,eng.prepare(ctx))
    assert len(error.partial_result.messages)==3 and error.partial_result.stop_reason=='interrupted'
    status=await eng.status(ctx.run)
    assert status.after_id==100 and status.pending_message_count==3 and not status.source_exhausted
    assert status.last_failure_kind=='budget' and status.last_failure_account_id==f.ACCOUNT
    assert status.last_failure_retry_at is not None and status.attempt_id is None
    before=budget.status(f.ACCOUNT).used
    replay=await engine(backend,forbidden_reader,forbidden_clock).prepare(ctx)
    assert replay.batch.to_json()==error.partial_result.to_json()
    assert (await eng.acknowledge(replay.delivery)).after_id==103
    assert budget.status(f.ACCOUNT).used==before==3 and len(sender.reads)==1


async def test_original_rpc_prefix_and_failed_save_keep_separate_provenance():
    for fail_save in (False,True):
        events=[];backend,_,tg,_,sender,_,ctx=await setup(events=events,batch_size=101)
        original=errors.ChannelPrivateError(None)
        sender.script=[f.response([f.message(i) for i in range(200,100,-1)]),original]
        wrapped=FaultStore(backend)
        if fail_save:wrapped.fail[2]=OSError(SECRET)
        eng=engine(wrapped,tg.get_message_batch)
        caught=await f.expect(BackfillStorageError if fail_save else type(original),eng.prepare(ctx))
        assert len(events)==1 and len(sender.reads)==2
        if fail_save:
            assert caught.read_error is original and caught.__cause__ is None
            assert health.classify(caught,True) is None and SECRET not in str(caught)
            assert (await eng.status(ctx.run)).attempt_id
        else:
            assert caught is original and len(original.partial_result.messages)==100
            replay=await engine(backend,forbidden_reader,forbidden_clock).prepare(ctx)
            assert replay.batch.to_json()==original.partial_result.to_json()
            assert replay.status.last_failure_account_id is None
            assert not replay.status.source_exhausted


async def test_no_prefix_failure_settles_without_end_or_cursor_advance():
    backend,eng,_,_,sender,_,ctx=await setup()
    original=ConnectionError('owned synthetic transport failure');sender.script=[original]
    assert await f.expect(ConnectionError,eng.prepare(ctx)) is original
    status=await eng.status(ctx.run)
    assert status.after_id==100 and status.pending_batch_id is None and status.attempt_id is None
    assert not status.source_exhausted and status.terminal_outcome is None
    assert status.last_failure_type=='ConnectionError'
    later=await eng.prepare(ctx)
    assert later.batch.after_id==100 and later.status.last_failure_type=='ConnectionError'


async def test_invalid_source_results_do_not_settle_or_advance():
    bad=[None,sample(chat=CHAT-1),sample(after=99),sample(count=3),
         sample(date=END),sample(stop='interrupted')]
    for result in bad:
        backend,_,_,_,_,_,ctx=await setup()
        async def reader(*args,**kwargs):return result
        eng=engine(backend,reader)
        await f.expect(BackfillStateError,eng.prepare(ctx))
        status=await eng.status(ctx.run)
        assert status.attempt_id and status.after_id==100 and status.pending_batch_id is None
        await f.expect(BackfillRecoveryRequired,eng.prepare(ctx))
    backend,_,_,_,_,_,ctx=await setup()
    original=ConnectionError('failure with invalid end prefix');original.partial_result=sample(stop='end')
    async def badprefix(*a,**k):raise original
    local=await f.expect(BackfillStateError,engine(backend,badprefix).prepare(ctx))
    assert local.read_error is original and health.classify(local,True) is None


async def test_media_replay_relocation_corruption_and_ack_after_removal():
    backend,eng,_,_,sender,_,ctx=await setup(media_mode='download',batch_size=1)
    sender.files[b.ASSET_ID]=b.PAYLOAD;b.script_messages(sender,[b.document()])
    first=b.directory();turn=await eng.prepare(ctx,download_media_to=first)
    second=b.directory()
    for path in first.iterdir():shutil.copyfile(path,second/path.name)
    local=engine(SQLiteSyncStore(backend.path,create=False),forbidden_reader,forbidden_clock)
    replay=await local.prepare(ctx,download_media_to=second)
    assert replay.batch.to_json()==turn.batch.to_json() and replay.delivery==turn.delivery
    blob=turn.batch.messages[0]['media']['blob'];path=second/blob['path'];before=await backend.load(CHAT)
    path.write_bytes(b'x'*blob['size'])
    await f.expect(BackfillMediaError,local.prepare(ctx,download_media_to=second))
    path.unlink();await f.expect(BackfillMediaError,local.prepare(ctx,download_media_to=second))
    path.symlink_to(first/blob['path'])
    await f.expect(BackfillMediaError,local.prepare(ctx,download_media_to=second))
    assert await backend.load(CHAT)==before
    path.unlink();(first/blob['path']).unlink()
    with patch('tgdata.backfill_engine._verify_existing',side_effect=AssertionError('ack must not inspect media')):
        status=await engine(backend,forbidden_reader).acknowledge(turn.delivery)
    assert status.after_id==101 and status.pending_batch_id is None and len(sender.reads)==1


async def test_media_failure_retains_only_actual_completed_prefix():
    backend,eng,_,_,sender,_,ctx=await setup(media_mode='download',batch_size=2)
    sender.files[b.ASSET_ID]=b.PAYLOAD
    b.script_messages(sender,[b.document(101),b.document(102,asset_id=b.ASSET_ID+1)])
    root=b.directory()
    original=await f.expect(KeyError,eng.prepare(ctx,download_media_to=root))
    assert len(original.partial_result.messages)==1
    replay=await engine(backend,forbidden_reader,forbidden_clock).prepare(ctx,download_media_to=root)
    assert replay.batch.to_json()==original.partial_result.to_json()
    assert replay.batch.stop_reason=='interrupted' and not replay.status.source_exhausted
    assert (await eng.acknowledge(replay.delivery)).after_id==101


async def test_directory_mismatch_is_pre_admission_local_refusal():
    backend,eng,_,_,sender,_,ctx=await setup()
    raw=await backend.load(CHAT)
    await f.expect(BackfillConfigurationError,eng.prepare(ctx,download_media_to=b.directory()))
    assert await backend.load(CHAT)==raw and not sender.reads
    backend,eng,_,_,sender,_,ctx=await setup(media_mode='download')
    raw=await backend.load(CHAT)
    for root in (None,True,''):
        await f.expect(BackfillConfigurationError,eng.prepare(ctx,download_media_to=root))
    file=TMP/'not_a_media_directory';file.write_bytes(b'x')
    await f.expect(BackfillMediaError,eng.prepare(ctx,download_media_to=file))
    assert await backend.load(CHAT)==raw and not sender.reads


async def test_cancellation_after_committed_publication_replays_exactly():
    backend,_,tg,_,sender,_,ctx=await setup();wrapped=FaultStore(backend);wrapped.hold=2
    eng=engine(wrapped,tg.get_message_batch)
    task=asyncio.create_task(eng.prepare(ctx));await asyncio.wait_for(wrapped.entered.wait(),5)
    raw=await backend.load(CHAT)
    assert json.loads(raw)['current']['pending'] is not None
    task.cancel();error=await f.expect(asyncio.CancelledError,task)
    assert health.classify(error,True) is None
    replay=await engine(backend,forbidden_reader,forbidden_clock).prepare(ctx)
    assert replay.replayed and replay.status.attempt_id is None
    assert await backend.load(CHAT)==raw and len(sender.reads)==1


async def test_cancellation_inside_rpc_prefix_save_is_not_rpc_health():
    backend,_,tg,_,sender,_,ctx=await setup(batch_size=101)
    original=errors.ChannelPrivateError(None)
    sender.script=[f.response([f.message(i) for i in range(200,100,-1)]),original]
    wrapped=FaultStore(backend);wrapped.hold=2
    task=asyncio.create_task(engine(wrapped,tg.get_message_batch).prepare(ctx))
    await asyncio.wait_for(wrapped.entered.wait(),5)
    task.cancel();cancel=await f.expect(asyncio.CancelledError,task)
    assert cancel.__cause__ is None and health.classify(cancel,True) is None
    replay=await engine(backend,forbidden_reader,forbidden_clock).prepare(ctx)
    assert replay.batch.stop_reason=='interrupted' and len(replay.batch.messages)==100
    assert replay.status.last_failure_type=='ChannelPrivateError'


async def test_cancelled_load_releases_guard_and_no_source_runs():
    backend,_,tg,_,sender,_,ctx=await setup()
    class Held:
        entered=asyncio.Event();release=asyncio.Event();holding=True
        async def load(self,chat):
            if self.holding:self.entered.set();await self.release.wait()
            return await backend.load(chat)
        async def compare_and_swap(self,*args):return await backend.compare_and_swap(*args)
    held=Held();eng=engine(held,tg.get_message_batch)
    task=asyncio.create_task(eng.prepare(ctx));await asyncio.wait_for(held.entered.wait(),5)
    task.cancel();await f.expect(asyncio.CancelledError,task)
    assert not sender.reads and (await engine(backend).status(ctx.run)).attempt_id is None
    held.holding=False
    assert (await eng.prepare(ctx)).batch is not None


async def test_clock_failures_leave_correct_uncertainty_and_ack_order():
    backend,_,tg,_,sender,_,ctx=await setup()
    def bad():raise RuntimeError(SECRET)
    error=await f.expect(BackfillClockError,engine(backend,tg.get_message_batch,bad).prepare(ctx))
    assert SECRET not in str(error) and not sender.reads
    assert (await engine(backend).status(ctx.run)).attempt_id is None
    moments=iter([NOW,NOW-timedelta(seconds=1)])
    await f.expect(BackfillClockError,engine(backend,tg.get_message_batch,lambda:next(moments)).prepare(ctx))
    assert len(sender.reads)==1 and (await engine(backend).status(ctx.run)).attempt_id
    await f.expect(BackfillRecoveryRequired,engine(backend,forbidden_reader,forbidden_clock).prepare(ctx))
    (other,eng,_,_,_,_,_),turn=await prepared()
    accepted=await engine(other,forbidden_reader,lambda:NOW-timedelta(days=1)).acknowledge(turn.delivery)
    assert accepted.after_id==102 and accepted.pacing_not_before==turn.status.pacing_not_before


async def test_revision_headroom_precedes_source_and_does_not_wrap():
    for revision,allowed in [(MAX_LONG-2,False),(MAX_LONG-3,True)]:
        backend,eng,_,_,sender,_,ctx=await setup()
        raw=await backend.load(CHAT);doc=json.loads(raw);doc['state_revision']=str(revision)
        assert await backend.compare_and_swap(CHAT,raw,_BackfillState(doc).to_json())
        if not allowed:
            await f.expect(BackfillConflictError,eng.prepare(ctx));assert not sender.reads
        else:
            turn=await eng.prepare(ctx)
            assert turn.status.state_revision==MAX_LONG-1
            ack=await eng.acknowledge(turn.delivery)
            assert ack.state_revision==MAX_LONG and ack.after_id==102
            await f.expect(BackfillConflictError,eng.prepare(BackfillPrepareContext.from_status(ack)))
            assert len(sender.reads)==1


async def test_invalid_saved_pending_bound_is_not_repaired():
    (backend,eng,_,_,sender,_,ctx),turn=await prepared()
    raw=await backend.load(CHAT);doc=json.loads(raw);doc['current']['request']['batch_size']=1
    bad=json.dumps(doc);assert await backend.compare_and_swap(CHAT,raw,bad)
    await f.expect(BackfillStateError,eng.prepare(ctx))
    await f.expect(BackfillStateError,eng.acknowledge(turn.delivery))
    assert await backend.load(CHAT)==bad and len(sender.reads)==1


async def test_ack_conflict_preserves_newer_cancel_and_duplicate_race():
    (backend,_,tg,_,sender,_,ctx),turn=await prepared()
    wrapped=FaultStore(backend)
    async def change(n,*args):
        if n==1:await control_fixture(backend,'cancel');return False
    wrapped.hook=change
    status=await engine(wrapped,forbidden_reader).acknowledge(turn.delivery)
    assert status.after_id==102 and status.terminal_outcome=='cancelled'
    assert status.control_revision==1 and wrapped.calls==2 and len(sender.reads)==1
    (backend,_,_,_,_,_,_),turn=await prepared()
    ready=asyncio.Event()
    class Barrier:
        count=0
        async def load(self,chat):
            raw=await backend.load(chat);self.count+=1
            if self.count<=2:
                if self.count==2:ready.set()
                await ready.wait()
            return raw
        async def compare_and_swap(self,*args):return await backend.compare_and_swap(*args)
    barrier=Barrier()
    statuses=await asyncio.gather(engine(barrier,forbidden_reader).acknowledge(turn.delivery),
        engine(barrier,forbidden_reader).acknowledge(turn.delivery))
    assert all(x.after_id==102 and x.state_revision==4 for x in statuses)


async def test_ack_uncertain_commit_retries_without_effect_or_clock():
    (backend,_,_,_,_,_,_),turn=await prepared()
    wrapped=FaultStore(backend);wrapped.after[1]=OSError(SECRET)
    confirmed=await engine(wrapped,forbidden_reader).acknowledge(turn.delivery)
    assert confirmed.after_id==102 and confirmed.pending_batch_id is None
    raw=await backend.load(CHAT)
    status=await engine(SQLiteSyncStore(backend.path,create=False),forbidden_reader,forbidden_clock).acknowledge(turn.delivery)
    assert status.after_id==102 and status.pending_batch_id is None
    assert await backend.load(CHAT)==raw


async def test_prior_run_receipt_cannot_ack_equal_hash_successor():
    backend,eng,_,_,sender,req,ctx=await setup(batch_size=2)
    sender.script=[finite_response([f.message(101)])]
    first=await eng.prepare(ctx);await eng.acknowledge(first.delivery)
    second_req=replace(req,run_id='run-2',expected_predecessor=ctx.run)
    second_status=(await eng.start(second_req,submission='new')).status
    sender.script=[finite_response([f.message(101)])]
    second=await eng.prepare(BackfillPrepareContext.from_status(second_status))
    assert first.batch.batch_id==second.batch.batch_id
    before=await backend.load(CHAT)
    old=await engine(backend,forbidden_reader,forbidden_clock).acknowledge(first.delivery)
    assert old.run==ctx.run and old.history_limited
    assert await backend.load(CHAT)==before
    await eng.acknowledge(second.delivery)
    third=(await eng.start(replace(req,run_id='run-3',expected_predecessor=second_status.run),submission='new')).status
    await f.expect(BackfillUnknownRun,eng.acknowledge(first.delivery))
    assert (await eng.status(third.run)).after_id==100


async def test_incompatible_late_source_context_is_not_overwritten():
    backend,eng,_,_,sender,_,ctx=await setup();sender.script=[f.PENDING]
    task=asyncio.create_task(eng.prepare(ctx));await until(lambda:bool(sender.pending))
    raw=await backend.load(CHAT);doc=json.loads(raw)
    # An intentionally incompatible but structurally valid external replacement.
    doc['current']['ref']['run_id']='replacement';doc['current']['request']['run_id']='replacement'
    replacement=_BackfillState(doc).to_json()
    assert await backend.compare_and_swap(CHAT,raw,replacement)
    sender.pending[0].set_result(f.response([f.message(102),f.message(101)]))
    await f.expect(BackfillUnknownRun,task)
    assert await backend.load(CHAT)==replacement and len(sender.reads)==1


async def test_local_operations_never_recover_source_health():
    events=[]
    (backend,eng,tg,_,sender,_,ctx),turn=await prepared(events=events)
    await tg._health._emit(health.Finding(health.NO_ACCESS,'group','CHANNEL_PRIVATE',None,None),None,'error',CHAT)
    before=tg._health.snapshot();reads=len(sender.reads)
    await eng.status(ctx.run);await eng.prepare(ctx);await eng.acknowledge(turn.delivery)
    await f.expect(BackfillUnknownReceipt,eng.acknowledge(replace(turn.delivery,batch_id='0'*64)))
    after=tg._health.snapshot()
    assert after['events']==before['events'] and after['no_access']==before['no_access']
    assert len(sender.reads)==reads


async def test_future_unknown_timing_blocks_source_but_not_pending_ack():
    (backend,eng,_,_,sender,_,ctx),turn=await prepared()
    raw=await backend.load(CHAT);doc=json.loads(raw)
    doc['current']['pacing'].update(clock_uncertain=True,ended_at=None,not_before=None)
    assert await backend.compare_and_swap(CHAT,raw,_BackfillState(doc).to_json())
    replay=await engine(backend,forbidden_reader,forbidden_clock).prepare(ctx)
    status=await eng.acknowledge(replay.delivery)
    await f.expect(BackfillRecoveryRequired,eng.prepare(BackfillPrepareContext.from_status(status)))
    assert len(sender.reads)==1 and status.clock_uncertain


async def test_real_receiver_commit_with_lost_reply_replays_without_duplication():
    (backend,eng,_,_,sender,_,ctx),turn=await prepared()
    target=TMP/('receiver_{}.sqlite3'.format(next(NUMBERS)))
    with sqlite3.connect(str(target)) as db:
        db.execute('CREATE TABLE receipts (context TEXT PRIMARY KEY)')
        db.execute('CREATE TABLE messages (chat TEXT,id TEXT,payload TEXT,PRIMARY KEY(chat,id))')
    def accept(value,lose=False):
        with sqlite3.connect(str(target)) as db:
            receipt=json.dumps(value.delivery.to_dict(),sort_keys=True)
            if db.execute('INSERT OR IGNORE INTO receipts VALUES (?)',(receipt,)).rowcount:
                for message in value.batch.messages:
                    db.execute('INSERT OR IGNORE INTO messages VALUES (?,?,?)',
                        (str(value.batch.chat_id),message['id'],json.dumps(message)))
        if lose:raise ConnectionError('owned lost receiver reply')
    f.rejected(ConnectionError,lambda:accept(turn,lose=True))
    assert (await eng.status(ctx.run)).after_id==100
    replay=await engine(SQLiteSyncStore(backend.path,create=False),forbidden_reader,forbidden_clock).prepare(ctx)
    accept(replay);await engine(backend,forbidden_reader).acknowledge(replay.delivery)
    with sqlite3.connect(str(target)) as db:
        assert db.execute('SELECT count(*) FROM receipts').fetchone()[0]==1
        assert db.execute('SELECT count(*) FROM messages').fetchone()[0]==2
    assert len(sender.reads)==1 and (await eng.status(ctx.run)).after_id==102


async def crash_transition(path,phase,mode,trace):
    backend=SQLiteSyncStore(path,create=False)
    value=json.loads(await backend.load(CHAT));row=value['current']
    ref=BackfillRunRef.from_dict(row['ref'])
    async def reader(chat,**options):
        with open(trace,'a') as output:output.write('reader\n')
        return sample(after=options['after_id'],count=1)
    eng=engine(backend,reader)
    original=sqlite3.connect
    class Crash(sqlite3.Connection):
        def commit(self):
            hit=False
            if self.total_changes:
                current=json.loads(self.execute('SELECT data FROM tgdata_sync_state').fetchone()[0])['current']
                hit=(current['pending'] is not None if phase=='publish' else
                     current['pending'] is None and current['last_ack'] is not None)
            if hit and mode=='before':os._exit(41)
            super().commit()
            if hit and mode=='after':os._exit(42)
    def connect(*args,**kwargs):kwargs['factory']=Crash;return original(*args,**kwargs)
    with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
        if phase=='publish':
            await eng.prepare(BackfillPrepareContext(ref,int(row['after_id']),int(row['control_revision'])))
        else:
            await eng.acknowledge(BackfillDeliveryRef(ref,row['request']['destination_id'],row['pending']['batch_id']))
    raise AssertionError('actual commit boundary was not reached')


async def run_child(backend,phase,mode,trace):
    args=[sys.executable,__file__,'--crash',backend.path,phase,mode,str(trace)]
    if hasattr(asyncio,'to_thread'):
        result=await asyncio.to_thread(subprocess.run,args,capture_output=True,text=True,timeout=25)
    else:result=subprocess.run(args,capture_output=True,text=True,timeout=25)
    assert result.returncode==(41 if mode=='before' else 42),(result.returncode,result.stderr)


async def test_process_exit_before_and_after_pending_commit():
    for mode in ('before','after'):
        backend,_,_,_,_,_,ctx=await setup(batch_size=1)
        trace=TMP/('source_{}.txt'.format(next(NUMBERS)))
        await run_child(backend,'publish',mode,trace)
        assert trace.read_text()=='reader\n'
        fresh=engine(SQLiteSyncStore(backend.path,create=False),forbidden_reader,forbidden_clock)
        status=await fresh.status(ctx.run)
        assert status.after_id==100
        if mode=='before':
            assert status.attempt_id and status.pending_batch_id is None
            await f.expect(BackfillRecoveryRequired,fresh.prepare(ctx))
        else:
            turn=await fresh.prepare(ctx)
            assert turn.replayed and turn.batch.to_json()==sample().to_json()
            assert status.attempt_id is None
        assert trace.read_text()=='reader\n'


async def test_process_exit_before_and_after_ack_commit():
    (backend,_,_,_,sender,_,ctx),turn=await prepared()
    trace=TMP/('no_source_{}.txt'.format(next(NUMBERS)))
    for mode in ('before','after'):
        await run_child(backend,'ack',mode,trace)
        local=engine(SQLiteSyncStore(backend.path,create=False),forbidden_reader,forbidden_clock)
        status=await local.status(ctx.run)
        assert status.after_id==(100 if mode=='before' else 102)
        assert (status.pending_batch_id is not None)==(mode=='before')
        if mode=='after':assert (await local.acknowledge(turn.delivery))==status
    assert not trace.exists() and len(sender.reads)==1


async def main():
    global TMP
    tests=[v for k,v in globals().items() if k.startswith('test_') and asyncio.iscoroutinefunction(v)]
    print('Backfill Delivery Tests — Telethon {}; LOCAL/INJECTED, actual SQLite/SDK'.format(telethon.__version__))
    assert telethon.__version__=='1.45.0'
    passed=0
    with tempfile.TemporaryDirectory(prefix='tgdata_backfill_delivery_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        TMP=Path(tmp);f.TMP=TMP
        try:
            for test in tests:
                print('\nTEST:',test.__name__,flush=True)
                try:await asyncio.wait_for(test(),60)
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
            asyncio.run(crash_transition(*sys.argv[2:]))
    else:sys.exit(asyncio.run(main()))
