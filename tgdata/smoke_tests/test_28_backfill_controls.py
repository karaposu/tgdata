"""Stage 6 controls: actual SQLite/SDK, injected orderings, sockets forbidden."""
import asyncio
from dataclasses import FrozenInstanceError, replace
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import telethon
from tgdata import SQLiteSyncStore, ReadBudgetExceeded, health
from tgdata.backfill import (BackfillControlResult, BackfillConfigurationError,
    BackfillConflictError, BackfillStorageError, BackfillStateError, BackfillClockError,
    BackfillUnknownRun, BackfillUnknownReceipt, BackfillRecoveryRequired,
    BackfillStartRequest, BackfillRunRef)
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill_state import _BackfillState
from tgdata.message_batch import MAX_LONG
from tgdata.smoke_tests import test_27_backfill_pacing as q
from tgdata.smoke_tests.test_26_backfill_completion import AmbiguousStore

d = q.d
f = d.f
CHAT = d.CHAT
context = q.context


def command(status, action, ident='command'):
    return dict(command_id=ident, expected_control_revision=status.control_revision, action=action)


async def decide(e, action, ident='command', status=None, engine=None):
    status = status or await e.eng.status(e.ctx.run)
    return await (engine or e.eng).control(status.run, **command(status, action, ident))


async def pending(**options):
    e = await q.setup(**options)
    return e, await e.eng.prepare(e.ctx)


async def test_values_status_projection_and_scope_validation():
    e = await q.setup()
    assert e.initial.last_control_action is None and e.initial.abandoned_at is None
    result = await decide(e, 'pause', engine=q.engine(e, forbid=True))
    status = result.status
    assert result.applied and result.outcome == 'accepted'
    assert status.last_control_action == 'pause' and status.last_control_expected_revision == 0
    assert status.last_control_state_revision == status.state_revision == 2
    assert result.to_dict()['status']['last_control_expected_revision'] == '0'
    large = replace(status, last_control_state_revision=9007199254740993)
    assert large.to_dict()['last_control_state_revision'] == '9007199254740993'
    f.rejected(FrozenInstanceError, lambda:setattr(result, 'applied', False))
    for make in (
        lambda:BackfillControlResult('different','pause',True,'accepted',status),
        lambda:BackfillControlResult('command','resume',True,'accepted',status),
        lambda:BackfillControlResult('command','pause',False,'terminal',status),
        lambda:BackfillControlResult('command','pause',1,'accepted',status),
        lambda:BackfillControlResult('command','pause',False,'other',status),
    ):
        f.rejected(BackfillConfigurationError, make)
    import tgdata
    assert not hasattr(tgdata, 'BackfillControlResult') and not hasattr(tgdata.TgData, 'control_backfill')
    before = await e.store.load(CHAT)
    for key, value in (('command_id','bad id'),('command_id',None),('action','stop'),
                       ('expected_control_revision',True),('expected_control_revision','1'),
                       ('expected_control_revision',-1)):
        args = command(status,'pause'); args[key] = value
        await f.expect(BackfillConfigurationError,e.eng.control(status.run,**args))
    await f.expect(BackfillConfigurationError,e.eng.control('run',**command(status,'pause')))
    await f.expect(BackfillConfigurationError,e.eng.control(replace(status.run,collection_id='foreign'),
                                                          **command(status,'pause')))
    assert await e.store.load(CHAT) == before and not e.sender.calls


async def test_new_matching_no_change_decisions_increment_once_without_clocks():
    e = await q.setup()
    before = json.loads(await e.store.load(CHAT))['current']
    for revision, action in enumerate(('resume','pause','pause','resume','resume'),1):
        result = await decide(e,action,'decision-'+str(revision),engine=q.engine(e,forbid=True))
        assert result.applied and result.status.control_revision == revision
        assert result.status.operator_intent == ('paused' if action=='pause' else 'active')
    after = json.loads(await e.store.load(CHAT))['current']
    for key in ('operator_intent','control_revision','last_control'):
        before.pop(key); after.pop(key)
    assert after == before and not e.sender.calls


async def test_exact_retry_and_changed_input_do_not_write_or_observe_time():
    e, turn = await pending()
    args = command(turn.status,'pause')
    accepted = await e.eng.control(e.ctx.run,**args)
    acknowledged = await e.eng.acknowledge(turn.delivery)
    raw = await e.store.load(CHAT)
    result = await q.engine(e,forbid=True).control(e.ctx.run,**args)
    assert not result.applied and result.status == acknowledged and result.outcome=='accepted'
    for changed in (dict(args,action='resume'),dict(args,expected_control_revision=1)):
        await f.expect(BackfillConflictError,q.engine(e,forbid=True).control(e.ctx.run,**changed))
    assert await e.store.load(CHAT)==raw and len(e.sender.reads)==1


async def test_stale_resume_prepare_and_forgotten_command_refuse():
    e = await q.setup()
    pause = await decide(e,'pause','pause')
    await f.expect(BackfillConflictError,e.eng.prepare(e.ctx))
    resume = await decide(e,'resume','resume')
    await decide(e,'pause','later-pause')
    raw = await e.store.load(CHAT)
    await f.expect(BackfillConflictError,e.eng.control(e.ctx.run,**command(pause.status,'resume','resume')))
    await f.expect(BackfillConflictError,e.eng.control(e.ctx.run,**command(e.initial,'pause','pause')))
    await f.expect(BackfillConflictError,e.eng.prepare(context(resume.status)))
    assert await e.store.load(CHAT)==raw and not e.sender.reads


async def test_cross_recovery_command_collision_in_both_directions():
    e = await q.unknown()
    recovered = await e.eng.recover(e.ctx.run,**e.command)
    await f.expect(BackfillConflictError,e.eng.control(e.ctx.run,**command(recovered.status,'pause','recover-1')))
    pause = await decide(e,'pause','pause')
    await f.expect(BackfillConflictError,e.eng.recover(e.ctx.run,**dict(e.command,
        command_id='pause',expected_control_revision=pause.status.control_revision)))
    old = await q.engine(e,forbid=True).recover(e.ctx.run,**e.command)
    assert not old.applied and old.status.operator_intent=='paused'


async def test_two_opposing_controls_have_one_accepted_order():
    for same in (False,True):
        e = await q.setup(); ready = asyncio.Event()
        class Barrier:
            count=0
            async def load(self,chat):
                raw=await e.store.load(chat);self.count+=1
                if self.count<=2:
                    if self.count==2:ready.set()
                    await ready.wait()
                return raw
            async def compare_and_swap(self,*args):return await e.store.compare_and_swap(*args)
        barrier=Barrier();one=command(e.initial,'pause','one')
        two=one if same else command(e.initial,'cancel','two')
        results=await asyncio.gather(q.engine(e,store=barrier,forbid=True).control(e.ctx.run,**one),
            q.engine(e,store=barrier,forbid=True).control(e.ctx.run,**two),return_exceptions=True)
        successful=[r for r in results if isinstance(r,BackfillControlResult)]
        assert sum(r.applied for r in successful)==1
        if same:assert len(successful)==2 and successful[0].status==successful[1].status
        else:assert len(successful)==1 and sum(isinstance(r,BackfillConflictError) for r in results)==1
        assert (await e.eng.status(e.ctx.run)).control_revision==1 and not e.sender.reads


async def test_delayed_control_reply_is_historical_not_authority():
    e=await q.setup();fault=d.FaultStore(e.store);fault.hold=1
    first=asyncio.create_task(decide(e,'pause','first',status=e.initial,engine=q.engine(e,store=fault,forbid=True)))
    await asyncio.wait_for(fault.entered.wait(),5)
    resumed=await decide(e,'resume','second')
    fault.release.set();late=await first
    assert late.status.operator_intent=='paused' and late.status.control_revision==1
    now=await e.eng.status(e.ctx.run)
    assert now==resumed.status and now.control_revision==2 and now.operator_intent=='active'
    await f.expect(BackfillConflictError,e.eng.control(e.ctx.run,**command(e.initial,'pause','first')))


async def test_data_only_cas_conflict_reloads_but_new_control_refuses():
    e,turn=await pending();fault=d.FaultStore(e.store)
    async def ack(n,*args):
        if n==1:await e.eng.acknowledge(turn.delivery);return False
    fault.hook=ack
    result=await decide(e,'pause',status=turn.status,engine=q.engine(e,store=fault,forbid=True))
    assert result.status.after_id==102 and result.status.control_revision==1 and fault.calls==2
    e=await q.setup();fault=d.FaultStore(e.store)
    async def newer(n,*args):
        if n==1:await decide(e,'pause','newer');return False
    fault.hook=newer
    await f.expect(BackfillConflictError,decide(e,'resume','older',status=e.initial,
        engine=q.engine(e,store=fault,forbid=True)))
    assert fault.calls==1 and (await e.eng.status(e.ctx.run)).operator_intent=='paused'


async def test_perpetual_conflicts_are_bounded():
    e=await q.setup();fault=d.FaultStore(e.store)
    async def conflict(*args):return False
    fault.hook=conflict
    await f.expect(BackfillConflictError,decide(e,'pause',engine=q.engine(e,store=fault,forbid=True)))
    assert fault.calls==4 and await e.eng.status(e.ctx.run)==e.initial


async def test_pause_and_cancel_during_real_sdk_wait_preserve_late_data():
    for action in ('pause','cancel'):
        e=await q.setup();e.sender.script=[f.PENDING]
        task=asyncio.create_task(e.eng.prepare(e.ctx));await d.until(lambda:bool(e.sender.pending))
        accepted=await decide(e,action,engine=q.engine(e,forbid=True))
        assert accepted.status.attempt_id and accepted.status.pending_batch_id is None
        await f.expect(BackfillConflictError,decide(e,'abandon','bad'))
        await f.expect(BackfillConflictError,e.eng.recover(e.ctx.run,**q.command(accepted.status)))
        e.sender.pending[0].set_result(f.response([f.message(102),f.message(101)]))
        turn=await task
        assert turn.status.operator_intent==accepted.status.operator_intent
        assert turn.status.control_revision==1 and turn.status.pending_message_count==2
        replay=await q.engine(e,forbid=True).prepare(context(turn.status))
        assert replay.batch.to_json()==turn.batch.to_json()
        done=await e.eng.acknowledge(replay.delivery)
        local=await q.engine(e,forbid=True).prepare(context(done))
        assert local.batch is None and len(e.sender.reads)==1
        assert done.terminal_outcome==('cancelled' if action=='cancel' else None)


async def test_control_after_admission_commit_before_reply_allows_that_read():
    for action in ('pause','cancel'):
        e=await q.setup();fault=d.FaultStore(e.store);fault.hold=1
        eng=q.engine(e,store=fault,reader=e.tg.get_message_batch)
        task=asyncio.create_task(eng.prepare(e.ctx));await asyncio.wait_for(fault.entered.wait(),5)
        accepted=await decide(e,action)
        assert not e.sender.reads and accepted.status.attempt_id
        fault.release.set();turn=await task
        assert turn.status.control_revision==1 and turn.status.operator_intent==accepted.status.operator_intent
        assert len(e.sender.reads)==1 and turn.batch is not None


async def test_pause_during_publication_reloads_only_same_attempt():
    e=await q.setup();fault=d.FaultStore(e.store)
    async def pause(n,*args):
        if n==2:await decide(e,'pause');return False
    fault.hook=pause
    turn=await q.engine(e,store=fault,reader=e.tg.get_message_batch).prepare(e.ctx)
    assert turn.status.operator_intent=='paused' and turn.status.pending_message_count==2
    assert fault.calls==3 and len(e.sender.reads)==1


async def test_final_ack_cancel_orders_keep_first_terminal_outcome():
    for first in ('ack','cancel'):
        e=await q.setup();e.sender.script=[d.finite_response([f.message(101)])]
        turn=await e.eng.prepare(e.ctx)
        if first=='cancel':
            cancelled=await decide(e,'cancel',status=turn.status)
            done=await e.eng.acknowledge(turn.delivery)
            assert done.terminal_outcome=='cancelled' and done.control_revision==1
        else:
            done=await e.eng.acknowledge(turn.delivery);raw=await e.store.load(CHAT)
            result=await decide(e,'cancel',status=done,engine=q.engine(e,forbid=True))
            assert result.outcome=='terminal' and not result.applied and result.status==done
            assert done.terminal_outcome=='completed' and await e.store.load(CHAT)==raw
        assert done.after_id==101 and done.pending_batch_id is None


async def test_cancel_empty_end_orders_and_terminal_reports():
    for cancel_first in (True,False):
        e=await q.setup();entered=asyncio.Event();release=asyncio.Event()
        e.sender.script=[d.finite_response([])]
        async def read(chat,**kw):
            result=await e.tg.get_message_batch(chat,**kw);entered.set();await release.wait();return result
        eng=q.engine(e,reader=read);task=asyncio.create_task(eng.prepare(e.ctx));await entered.wait()
        if cancel_first:await decide(e,'cancel')
        release.set();turn=await task
        expected='cancelled' if cancel_first else 'completed'
        assert turn.status.terminal_outcome==expected and turn.status.source_exhausted
        raw=await e.store.load(CHAT)
        for action in ('pause','resume','cancel'):
            result=await decide(e,action,'fresh-'+action,engine=q.engine(e,forbid=True))
            assert result.outcome=='terminal' and not result.applied and result.status.terminal_outcome==expected
        assert await e.store.load(CHAT)==raw


async def test_pause_final_ack_completes_without_resuming_source():
    e=await q.setup();e.sender.script=[d.finite_response([f.message(101)])]
    turn=await e.eng.prepare(e.ctx);await decide(e,'pause')
    done=await e.eng.acknowledge(turn.delivery)
    assert done.terminal_outcome=='completed' and done.operator_intent=='paused'
    terminal=await decide(e,'resume','late',engine=q.engine(e,forbid=True))
    assert terminal.outcome=='terminal' and terminal.status==done and len(e.sender.reads)==1


async def test_abandonment_records_owed_scope_without_accepting_or_deleting():
    e=await q.setup(media_mode='download',batch_size=1)
    e.sender.files[d.b.ASSET_ID]=d.b.PAYLOAD;d.b.script_messages(e.sender,[d.b.document()])
    root=d.b.directory();turn=await e.eng.prepare(e.ctx,download_media_to=root)
    blob=turn.batch.messages[0]['media']['blob'];path=root/blob['path'];before=path.read_bytes()
    retired=await decide(e,'abandon',status=turn.status)
    status=retired.status
    assert status.terminal_outcome=='abandoned' and status.delivery_abandoned
    assert status.after_id==100 and status.abandoned_batch_id==turn.batch.batch_id
    assert status.abandoned_next_after_id==turn.batch.next_after_id and status.abandoned_at==d.NOW
    assert path.read_bytes()==before and status.pending_batch_id is None
    raw=await e.store.load(CHAT)
    await f.expect(BackfillUnknownReceipt,e.eng.acknowledge(turn.delivery))
    retry=await q.engine(e,forbid=True).control(e.ctx.run,**command(turn.status,'abandon'))
    assert not retry.applied and retry.status==status and await e.store.load(CHAT)==raw
    wire=status.to_dict();assert wire['abandoned_next_after_id']==str(turn.batch.next_after_id)
    assert wire['abandoned_at'].endswith('Z') and len(e.sender.reads)==1


async def test_cancel_then_abandon_and_empty_retirement_preserve_meaning():
    for with_pending in (True,False):
        e=await q.setup()
        turn=await e.eng.prepare(e.ctx) if with_pending else None
        cancelled=await decide(e,'cancel','cancel')
        retired=await decide(e,'abandon','abandon')
        assert retired.status.terminal_outcome=='cancelled' and retired.status.operator_intent=='cancelled'
        assert retired.status.after_id==100 and retired.status.control_revision==2
        assert retired.status.abandoned_batch_id==(turn.batch.batch_id if turn else None)
        assert retired.status.abandoned_next_after_id==(102 if turn else 100)
        raw=await e.store.load(CHAT)
        result=await decide(e,'abandon','fresh',engine=q.engine(e,forbid=True))
        assert result.outcome=='terminal' and await e.store.load(CHAT)==raw
    e=await q.setup();retired=await decide(e,'abandon')
    assert retired.status.terminal_outcome=='abandoned' and retired.status.abandoned_batch_id is None
    assert not e.sender.calls


async def test_abandon_clock_failure_and_unknown_source_preserve_obligation():
    e,turn=await pending();raw=await e.store.load(CHAT)
    await f.expect(BackfillClockError,decide(e,'abandon',engine=q.engine(e,forbid=True)))
    assert await e.store.load(CHAT)==raw
    e=await q.unknown();cancelled=await decide(e,'cancel','cancel')
    raw=await e.store.load(CHAT)
    await f.expect(BackfillConflictError,decide(e,'abandon','abandon'))
    assert await e.store.load(CHAT)==raw
    recovered=await e.eng.recover(e.ctx.run,**dict(e.command,
        expected_control_revision=cancelled.status.control_revision))
    assert recovered.status.terminal_outcome=='cancelled' and recovered.status.pacing_not_before
    retired=await decide(e,'abandon','abandon')
    assert retired.status.pacing_not_before==recovered.status.pacing_not_before
    assert retired.status.terminal_outcome=='cancelled' and retired.status.after_id==100


async def test_busy_local_replay_refuses_abandon_and_successor_but_recognizes_start():
    e,turn=await pending();fault=d.FaultStore(e.store)
    entered=asyncio.Event();release=asyncio.Event()
    class LoadBarrier:
        async def load(self,chat):
            raw=await e.store.load(chat);entered.set();await release.wait();return raw
        async def compare_and_swap(self,*args):return await e.store.compare_and_swap(*args)
    eng=q.engine(e,store=LoadBarrier())
    task=asyncio.create_task(eng.prepare(e.ctx));await entered.wait()
    # The separate wrapper lets control/status load without releasing that replay.
    eng._store=e.store
    await f.expect(BackfillConflictError,decide(e,'abandon',engine=eng))
    await decide(e,'cancel','cancel');await e.eng.acknowledge(turn.delivery)
    successor=replace(e.req,run_id='successor',expected_predecessor=e.ctx.run)
    await f.expect(BackfillConflictError,eng.start(successor,submission='new'))
    assert not (await eng.start(e.req,submission='retry')).applied
    release.set();replayed=await task
    assert replayed.delivery==turn.delivery
    assert (await eng.start(successor,submission='new')).applied


async def test_successor_requires_terminal_settled_exact_predecessor():
    e,turn=await pending();req=replace(e.req,run_id='next',expected_predecessor=e.ctx.run)
    await f.expect(BackfillConflictError,e.eng.start(req,submission='new'))
    await decide(e,'cancel')
    await f.expect(BackfillConflictError,e.eng.start(req,submission='new'))
    await e.eng.acknowledge(turn.delivery)
    await f.expect(BackfillConflictError,e.eng.start(replace(req,expected_predecessor=None),submission='new'))
    new=await e.eng.start(req,submission='new')
    assert new.status.run.generation==2 and new.status.control_revision==0


async def test_retired_equal_hash_receipt_never_accepts_successor():
    e,turn=await pending(pause=0)
    retired=await decide(e,'abandon')
    next_request=replace(e.req,run_id='second',expected_predecessor=e.ctx.run)
    next_status=(await e.eng.start(next_request,submission='new')).status
    second=await e.eng.prepare(context(next_status))
    assert second.batch.batch_id==turn.batch.batch_id and second.delivery!=turn.delivery
    raw=await e.store.load(CHAT)
    await f.expect(BackfillUnknownReceipt,e.eng.acknowledge(turn.delivery))
    recognized=await e.eng.control(e.ctx.run,**command(turn.status,'abandon'))
    assert recognized.status.history_limited and not recognized.applied
    terminal=await e.eng.control(e.ctx.run,**command(retired.status,'resume','old-new'))
    assert terminal.outcome=='terminal' and terminal.status.history_limited
    assert await e.store.load(CHAT)==raw and (await e.eng.status(next_status.run)).after_id==100


async def test_retained_accepted_receipt_and_previous_cancel_are_read_only_then_pruned():
    e,turn=await pending(pause=0);cancelled=await decide(e,'cancel','cancel')
    accepted=await e.eng.acknowledge(turn.delivery)
    second_req=replace(e.req,run_id='second',expected_predecessor=e.ctx.run)
    second=(await e.eng.start(second_req,submission='new')).status
    raw=await e.store.load(CHAT)
    old=await q.engine(e,forbid=True).acknowledge(turn.delivery)
    assert old.history_limited and old.after_id==102
    terminal=await e.eng.control(e.ctx.run,**command(accepted,'abandon','late-abandon'))
    assert terminal.outcome=='terminal' and not terminal.status.delivery_abandoned
    assert await e.store.load(CHAT)==raw
    await e.eng.control(second.run,**command(second,'abandon','second-abandon'))
    third_req=replace(e.req,run_id='third',expected_predecessor=second.run)
    await e.eng.start(third_req,submission='new')
    await f.expect(BackfillUnknownRun,e.eng.acknowledge(turn.delivery))
    await f.expect(BackfillUnknownRun,e.eng.control(e.ctx.run,**command(turn.status,'cancel','cancel')))


async def test_paused_failed_budget_prefix_replays_and_ack_preserves_wait_and_failure():
    budget,_=f.ledger(3);events=[]
    e=await q.setup(budget=budget,events=events,batch_size=5)
    entered=asyncio.Event();release=asyncio.Event();caught=[]
    async def read(chat,**kw):
        try:return await e.tg.get_message_batch(chat,**kw)
        except ReadBudgetExceeded as error:
            caught.append(error);entered.set();await release.wait();raise
    eng=q.engine(e,reader=read);task=asyncio.create_task(eng.prepare(e.ctx));await entered.wait()
    await decide(e,'pause');release.set()
    error=await f.expect(ReadBudgetExceeded,task);assert error is caught[0]
    paused=await eng.status(e.ctx.run);assert paused.operator_intent=='paused' and paused.pending_message_count==3
    replay=await q.engine(e,forbid=True).prepare(context(paused))
    assert replay.batch.to_json()==error.partial_result.to_json()
    ack=await eng.acknowledge(replay.delivery)
    resumed=await decide(e,'resume','resume')
    assert resumed.status.pacing_not_before==paused.pacing_not_before
    assert resumed.status.last_failure_account_id==f.ACCOUNT and resumed.status.last_failure_kind=='budget'
    assert (await e.eng.prepare(context(resumed.status))).wait_seconds==240
    assert budget.status(f.ACCOUNT).used==3 and len(e.sender.reads)==1 and not events


async def test_early_and_late_controls_neither_extend_nor_shorten_pacing():
    e,turn=await pending();deadline=turn.status.pacing_not_before
    await decide(e,'pause','pause');e.clocks.advance(100)
    ack=await e.eng.acknowledge(turn.delivery);resumed=await decide(e,'resume','resume')
    assert ack.pacing_not_before==resumed.status.pacing_not_before==deadline
    assert (await e.eng.prepare(context(resumed.status))).wait_seconds==140
    e.clocks.advance(200)
    await decide(e,'pause','late-pause');active=await decide(e,'resume','late-resume')
    later=await e.eng.prepare(context(active.status))
    assert later.batch.after_id==102 and len(e.sender.reads)==2


async def set_revision(e, value):
    raw=await e.store.load(CHAT);doc=json.loads(raw);doc['state_revision']=str(value)
    assert await e.store.compare_and_swap(CHAT,raw,_BackfillState(doc).to_json())


async def test_control_reserves_revisions_for_pending_ack_and_unknown_settlement():
    e,turn=await pending();await set_revision(e,MAX_LONG-2)
    paused=await decide(e,'pause','last-control')
    assert paused.status.state_revision==MAX_LONG-1
    raw=await e.store.load(CHAT)
    await f.expect(BackfillConflictError,decide(e,'resume','too-far'))
    assert await e.store.load(CHAT)==raw
    ack=await e.eng.acknowledge(turn.delivery);assert ack.state_revision==MAX_LONG
    retry=await q.engine(e,forbid=True).control(e.ctx.run,**command(turn.status,'pause','last-control'))
    assert not retry.applied
    e=await q.setup();e.sender.script=[f.PENDING]
    task=asyncio.create_task(e.eng.prepare(e.ctx));await d.until(lambda:bool(e.sender.pending))
    await set_revision(e,MAX_LONG-3)
    await decide(e,'cancel','cancel')
    await f.expect(BackfillConflictError,decide(e,'abandon','bad'))
    e.sender.pending[0].set_result(f.response([f.message(102),f.message(101)]))
    turn=await task;assert turn.status.state_revision==MAX_LONG-1
    ack=await e.eng.acknowledge(turn.delivery)
    assert ack.state_revision==MAX_LONG and ack.terminal_outcome=='cancelled'


async def test_insufficient_attempt_capacity_refuses_and_abandon_can_retire_last_revision():
    e=await q.unknown();await set_revision(e,MAX_LONG-2);raw=await e.store.load(CHAT)
    await f.expect(BackfillConflictError,decide(e,'pause'))
    assert await e.store.load(CHAT)==raw
    e,turn=await pending();await set_revision(e,MAX_LONG-1)
    result=await decide(e,'abandon')
    assert result.status.state_revision==MAX_LONG and result.status.after_id==100
    assert result.status.abandoned_batch_id==turn.batch.batch_id


async def test_control_write_confirmation_matrix_and_safe_error():
    for committed in (False,True):
        for nonbool in (False,True):
            e=await q.setup();fault=AmbiguousStore(e.store,committed=committed,nonbool=nonbool)
            call=decide(e,'pause',engine=q.engine(e,store=fault,forbid=True))
            if committed:
                result=await call;assert result.applied and result.status.operator_intent=='paused'
            else:
                error=await f.expect(BackfillStorageError,call)
                assert d.SECRET not in str(error) and health.classify(error,True) is None
                assert await e.eng.status(e.ctx.run)==e.initial
            assert fault.writes==fault.readbacks==1 and not e.sender.calls


async def test_ambiguous_readback_never_overwrites_later_control():
    e=await q.setup()
    async def later():await decide(e,'resume','newer')
    fault=AmbiguousStore(e.store,hook=later)
    await f.expect(BackfillStorageError,decide(e,'pause','older',status=e.initial,
        engine=q.engine(e,store=fault,forbid=True)))
    assert fault.writes==1 and (await e.eng.status(e.ctx.run)).operator_intent=='active'
    await f.expect(BackfillConflictError,e.eng.control(e.ctx.run,**command(e.initial,'pause','older')))
    for view,kind in (('corrupt',BackfillStateError),('wrong_scope',BackfillStateError),
                      ('old',BackfillStorageError),('missing',BackfillStorageError),('outage',BackfillStorageError)):
        e=await q.setup();fault=AmbiguousStore(e.store,readback=view)
        await f.expect(kind,decide(e,'pause',engine=q.engine(e,store=fault,forbid=True)))
        retry=await q.engine(e,forbid=True).control(e.ctx.run,**command(e.initial,'pause'))
        assert not retry.applied and retry.status.operator_intent=='paused'


async def test_cancelled_control_reply_reconciles_without_resetting_wait():
    for where in ('commit','readback'):
        e,turn=await pending()
        if where=='commit':fault=d.FaultStore(e.store);fault.hold=1
        else:fault=AmbiguousStore(e.store,readback='hold')
        task=asyncio.create_task(decide(e,'pause',status=turn.status,engine=q.engine(e,store=fault,forbid=True)))
        await asyncio.wait_for(fault.entered.wait(),5);task.cancel()
        await f.expect(asyncio.CancelledError,task)
        raw=await e.store.load(CHAT)
        result=await q.engine(e,forbid=True).control(e.ctx.run,**command(turn.status,'pause'))
        assert not result.applied and result.status.pacing_not_before==turn.status.pacing_not_before
        assert await e.store.load(CHAT)==raw


async def test_real_post_commit_close_failure_confirms_control():
    e=await q.setup();original=sqlite3.connect
    class BadClose(sqlite3.Connection):
        def close(self):
            hit=False
            if self.total_changes:
                row=self.execute('SELECT data FROM tgdata_sync_state').fetchone()
                hit=row and json.loads(row[0])['current']['last_control'] is not None
            super().close()
            if hit:raise sqlite3.OperationalError(d.SECRET)
    def connect(*args,**kw):kw['factory']=BadClose;return original(*args,**kw)
    with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
        result=await decide(e,'pause',engine=q.engine(e,forbid=True))
    assert result.applied and result.status.control_revision==1
    assert not (await q.engine(e,forbid=True).control(e.ctx.run,**command(e.initial,'pause'))).applied


async def test_corrupt_missing_or_foreign_state_is_not_repaired():
    for mode in ('corrupt','missing','foreign'):
        e=await q.setup();raw=await e.store.load(CHAT)
        if mode=='missing':
            with sqlite3.connect(e.store.path) as db:db.execute('DELETE FROM tgdata_sync_state')
            kind=BackfillUnknownRun
        else:
            changed='{bad' if mode=='corrupt' else raw.replace('delivery-tests','different-scope')
            assert await e.store.compare_and_swap(CHAT,raw,changed);kind=BackfillStateError
        before=await e.store.load(CHAT)
        await f.expect(kind,decide(e,'pause',status=e.initial,engine=q.engine(e,forbid=True)))
        assert await e.store.load(CHAT)==before


async def crash(path,boundary):
    store=SQLiteSyncStore(path,create=False);raw=await store.load(CHAT)
    state=_BackfillState.from_json(raw,d.COLLECTION,CHAT);status=state.status();original=sqlite3.connect
    class Crash(sqlite3.Connection):
        def commit(self):
            hit=False
            if self.total_changes:
                row=self.execute('SELECT data FROM tgdata_sync_state').fetchone()
                hit=row and json.loads(row[0])['current']['last_control'] is not None
            if hit and boundary=='before':os._exit(90)
            super().commit()
            if hit and boundary=='after':os._exit(91)
    def connect(*args,**kw):kw['factory']=Crash;return original(*args,**kw)
    with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
        await BackfillEngine(store,d.COLLECTION,clock=d.forbidden_clock).control(
            status.run,**command(status,'pause','crash-pause'))
    raise AssertionError('crash boundary not reached')


async def test_process_exit_before_and_after_real_control_commit():
    for boundary in ('before','after'):
        e,turn=await pending();raw=await e.store.load(CHAT)
        args=[sys.executable,__file__,'--crash',str(e.store.path),boundary]
        loop=asyncio.get_running_loop()
        result=await loop.run_in_executor(None,lambda:subprocess.run(args,capture_output=True,text=True,timeout=25))
        assert result.returncode==(90 if boundary=='before' else 91),(result.returncode,result.stderr)
        if boundary=='before':assert await e.store.load(CHAT)==raw
        outcome=await q.engine(e,forbid=True).control(e.ctx.run,**command(turn.status,'pause','crash-pause'))
        assert outcome.applied==(boundary=='before') and outcome.status.control_revision==1
        assert outcome.status.pending_batch_id==turn.batch.batch_id
        assert outcome.status.pacing_not_before==turn.status.pacing_not_before


async def main():
    tests=[v for k,v in globals().items() if k.startswith('test_') and asyncio.iscoroutinefunction(v)]
    print('Backfill Controls Tests — Telethon {}; LOCAL/INJECTED actual SQLite/SDK'.format(telethon.__version__))
    assert telethon.__version__=='1.45.0';passed=0
    with tempfile.TemporaryDirectory(prefix='tgdata_backfill_controls_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        f.TMP=d.TMP=Path(tmp)
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
