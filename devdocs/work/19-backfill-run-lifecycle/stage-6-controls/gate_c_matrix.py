"""Gate C matrix-specific orderings omitted by the core driver; same live cap/owner.

Expected outcomes are unchanged C03/04/06/11/16/21/32/36/38 from the committed matrix.
The core driver's PASS covers its cases, not this remaining formal gate audit.
"""
import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from unittest.mock import patch

import gate_c_probe as c
g=c.g
from tgdata import ReadBudget, ReadBudgetExceeded
from tgdata.backfill import BackfillConflictError, BackfillUnknownCommand, BackfillUnknownRun, BackfillUnknownReceipt
from tgdata.backfill_engine import BackfillEngine


async def run(root):
    report=dict(case='matrix_extra',code_revision=c.CODE,result='UNFINISHED',events=[],checks=[])
    primary=ReadBudget(g.base.OLD/'account-read-budget.sqlite3');ident=g.account()
    before=primary.status(ident);assert before.limit==5000 and before.remaining>=60
    report['budget_before']=dict(limit=before.limit,used=before.used)
    tg=guard=None
    try:
        tg,client,guard=await g.source(root,'matrix_extra',primary)
        entered=asyncio.Event();release=asyncio.Event()
        async def hold(result,error,event):
            assert error is None;entered.set();await release.wait()
        req,store,eng,status=await c.new_run(root,'matrix-retirement',c.observed_reader(tg,guard,report,hold),photo=True,pause=5)
        task=asyncio.create_task(eng.prepare(c.ctx(status)));await asyncio.wait_for(entered.wait(),60)
        cancelled=await eng.control(status.run,**c.args(status,'cancel','cancel-in-flight'))
        n=len(guard.rpc)
        await c.refuse(BackfillConflictError,eng.control(status.run,**c.args(cancelled.status,'abandon','too-early')))
        next_req=replace(req,run_id='second',expected_predecessor=status.run)
        await c.refuse(BackfillConflictError,eng.start(next_req,submission='new'))
        assert len(guard.rpc)==n
        release.set();first=await task;c.compare(first,c.expected(root,req,req.after_id))
        assert first.status.terminal_outcome=='cancelled' and first.status.pending_batch_id
        retired=await eng.control(status.run,**c.args(first.status,'abandon','retire-cancelled'))
        assert retired.status.terminal_outcome=='cancelled' and retired.status.after_id==req.after_id
        assert retired.status.abandoned_batch_id==first.batch.batch_id
        report['retired_status']=retired.status.to_dict()
        report['checks'].append('C32: cancel actual admitted read; busy abandon/successor refuse; late data saved; explicit retirement preserves cancelled/cursor')

        await asyncio.sleep(5)
        second_status=(await eng.start(next_req,submission='new')).status
        eng._read_batch=c.observed_reader(tg,guard,report)
        second=await eng.prepare(c.ctx(second_status));c.compare(second,c.expected(root,req,req.after_id))
        assert second.batch.batch_id==first.batch.batch_id and second.batch.stop_reason=='end'
        n=len(guard.rpc);old_raw=await store.load(g.CHAT)
        await c.refuse(BackfillUnknownReceipt,eng.acknowledge(first.delivery))
        assert await store.load(g.CHAT)==old_raw
        paused=await eng.control(second_status.run,**c.args(second.status,'pause','initial-pause'))
        entered=asyncio.Event();release=asyncio.Event()
        class LostOrder:
            async def load(self,chat):return await store.load(chat)
            async def compare_and_swap(self,*a):
                done=await store.compare_and_swap(*a);entered.set();await release.wait();return done
        delayed=BackfillEngine(LostOrder(),req.collection_id,clock=g.p.forbidden_clock)
        resume_args=c.args(paused.status,'resume','old-resume-reply')
        task=asyncio.create_task(delayed.control(second_status.run,**resume_args));await entered.wait()
        resumed=await eng.status(second_status.run)
        newer=await eng.control(second_status.run,**c.args(resumed,'pause','newer-pause'))
        release.set();old=await task
        assert old.status.operator_intent=='active' and old.status.control_revision<newer.status.control_revision
        assert await eng.status(second_status.run)==newer.status and newer.status.operator_intent=='paused'
        report['command_order']=[old.to_dict(),newer.to_dict()]
        before_stale=await store.load(g.CHAT)
        await c.refuse(BackfillConflictError,eng.prepare(c.ctx(second.status)))
        await c.refuse(BackfillConflictError,eng.control(second_status.run,**resume_args))
        assert await store.load(g.CHAT)==before_stale
        local=BackfillEngine(store,req.collection_id,clock=g.p.forbidden_clock)
        replay=await local.prepare(c.ctx(newer.status))
        assert replay.replayed and replay.status.source_exhausted and replay.status.operator_intent=='paused'
        c.accept(root,'matrix',replay,report)
        done=await eng.acknowledge(replay.delivery)
        assert done.terminal_outcome=='completed' and done.operator_intent=='paused'
        assert len(guard.rpc)==n
        report['checks']+=['C06: older accepted resume reply arrives after newer pause; stored pause stays authoritative',
            'C36/C07: stale prepare/resume refuse without any RPC or state change',
            'C11: actual final batch replay/receiver/ack while paused completes without resume or RPC']

        await asyncio.sleep(5)
        third_req=replace(req,run_id='third',expected_predecessor=second_status.run)
        third_status=(await eng.start(third_req,submission='new')).status
        third=await eng.prepare(c.ctx(third_status));c.compare(third,c.expected(root,req,req.after_id))
        raw=await store.load(g.CHAT);n=len(guard.rpc)
        retained=await local.start(next_req,submission='retry')
        assert not retained.applied and retained.status.history_limited
        assert not (await local.start(third_req,submission='retry')).applied
        await c.refuse(BackfillUnknownCommand,eng.start(req,submission='retry'))
        await c.refuse(BackfillConflictError,eng.start(req,submission='new'))
        await c.refuse(BackfillUnknownRun,eng.acknowledge(first.delivery))
        prior=await local.acknowledge(second.delivery)
        assert prior.history_limited and await store.load(g.CHAT)==raw
        await c.refuse(BackfillConflictError,eng.start(replace(req,run_id='fourth',expected_predecessor=third_status.run),submission='new'))
        replay=await local.prepare(c.ctx(third.status));assert replay.batch.to_json()==third.batch.to_json()
        assert (await eng.status(third_status.run)).pending_batch_id==third.batch.batch_id
        # Lost control reply after a real commit, on real pending data; exact readback confirms.
        original=sqlite3.connect
        class BadClose(sqlite3.Connection):
            def close(self):
                hit=False
                if self.total_changes:
                    row=self.execute('SELECT data FROM tgdata_sync_state').fetchone()
                    ctl=json.loads(row[0])['current']['last_control'] if row else None
                    hit=ctl and ctl['command_id']=='lost-pause'
                super().close()
                if hit:raise sqlite3.OperationalError('injected post-commit reply loss')
        def connect(*a,**kw):kw['factory']=BadClose;return original(*a,**kw)
        command=c.args(third.status,'pause','lost-pause')
        with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
            accepted=await local.control(third_status.run,**command)
        assert accepted.applied
        raw=await store.load(g.CHAT);duplicate=await local.control(third_status.run,**command)
        assert not duplicate.applied and duplicate.status==accepted.status and await store.load(g.CHAT)==raw
        c.accept(root,'matrix',third,report);done=await eng.acknowledge(third.delivery)
        assert done.terminal_outcome=='completed' and len(guard.rpc)==n
        report['checks']+=['C03/C04: retained creation recognized; pruned creation retry/new refuse',
            'C16: historical metadata pruned; active pending still replays and cannot be replaced',
            'C21: actual post-commit control close failure confirms; retry has no second effect or RPC']

        await asyncio.sleep(5)
        test=ReadBudget(root/'gate-test-budget.sqlite3')
        assert test.status(ident).used==6 and test.status(ident).remaining==0
        client._tgdata_read_budget=tg.connection_engine.read_budget=g.RestrictiveBudget(primary,test)
        req,store,eng,status=await c.new_run(root,'no-prefix',c.observed_reader(tg,guard,report),pause=5)
        history=guard.history_count
        await c.refuse(ReadBudgetExceeded,eng.prepare(c.ctx(status)))
        failed=await eng.status(status.run)
        assert failed.after_id==0 and failed.pending_batch_id is None and not failed.source_exhausted
        assert failed.attempt_id is None and failed.last_failure_kind=='budget'
        rpc=len(guard.rpc);early=await eng.prepare(c.ctx(failed))
        assert early.wait_seconds>0 and len(guard.rpc)==rpc and guard.history_count==history
        await asyncio.sleep(early.wait_seconds+0.03)
        await c.refuse(ReadBudgetExceeded,eng.prepare(c.ctx(failed)))
        later=await eng.status(status.run)
        assert later.pacing_attempt_id!=failed.pacing_attempt_id and later.state_revision==failed.state_revision+2
        assert later.pending_batch_id is None and not later.source_exhausted and later.after_id==0
        assert guard.history_count==history and len(guard.rpc)>rpc and test.status(ident).used==6
        last=[e for e in report['events'] if e['kind']=='source'][-1]
        c.assert_spacing(report,failed,last,req.pause_seconds)
        await eng.control(status.run,**c.args(later,'cancel','finish'))
        report['checks'].append('C38: settled zero-prefix budget failure; early no RPC; later distinct attempt rechecks real account/allowance and sends no disallowed history')
        report['result']='PASS'
    except BaseException as error:
        report.update(result='FAIL',error_type=type(error).__name__);raise
    finally:
        if tg:await tg.close()
        if guard:report.update(rpc=guard.rpc,history_requests=guard.history_count,requested_slots=guard.slots)
        after=primary.status(ident);assert after.limit==5000
        report['budget_after']=dict(limit=after.limit,used=after.used)
        g.save(root/'matrix_extra.result.json',report)
        print(json.dumps({k:v for k,v in report.items() if k in ('case','result','checks','requested_slots','history_requests','measured_intervals')},sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    parser.add_argument('--root',type=Path,default=g.ROOT);options=parser.parse_args()
    logging.disable(logging.CRITICAL)
    if options.run:asyncio.run(asyncio.wait_for(run(options.root),180))
    else:parser.print_help()
