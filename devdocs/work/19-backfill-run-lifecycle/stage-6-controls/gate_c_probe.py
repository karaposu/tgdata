"""Issue #19 Gate C audit driver. Default help is offline; --run uses approved reads.

Each network worker gets a durable, nonrefundable launch allocation. Owned processes
are sequential. Raw reports/state/media stay private. Local barriers are labeled;
no server wait/ban is manufactured, and no account policy is reset or increased.
"""
import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import time
from unittest.mock import patch

import gate_support as g
from telethon import functions, types, utils
from tgdata import ReadBudget, ReadBudgetExceeded, SQLiteSyncStore
from tgdata.backfill import (BackfillStartRequest, BackfillPrepareContext,
    BackfillConflictError, BackfillRecoveryRequired, BackfillUnknownReceipt,
    BackfillControlResult)
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill_state import _BackfillState
from tgdata.history_window import _encode_date, _decode_date

CODE='0d6bb26'
ctx=BackfillPrepareContext.from_status


def stamp():
    return dict(utc=_encode_date(datetime.now(timezone.utc)),monotonic_ns=time.monotonic_ns())


def args(status, action, ident):
    return dict(command_id=ident,expected_control_revision=status.control_revision,action=action)


async def refuse(kind, call):
    try:await call
    except kind:return
    raise AssertionError('expected '+kind.__name__)


def request(root,name,*,photo=False,media='references',batch=2,pause=8):
    oracle=g.read(root/'gate-oracle.json')
    if photo:
        start=_decode_date(oracle['selected_photo']['date']);end=start+timedelta(microseconds=1)
        after=int(oracle['selected_photo']['id'])-1;origin='imported'
    else:
        dates=[_decode_date(row['date']) for row in oracle['messages']]
        start=min(dates);end=max(dates)+timedelta(microseconds=1);after=0;origin='fresh'
    return BackfillStartRequest('gate-c-'+name,g.CHAT,'first','durable-receiver',pause,None,
        origin=origin,after_id=after,media_mode=media,batch_size=batch,start_date=start,end_date=end)


def expected(root,req,after,count=None):
    rows=[r for r in g.read(root/'gate-oracle.json')['messages']
          if int(r['id'])>after and req.start_date<=_decode_date(r['date'])<req.end_date]
    return rows if count is None else rows[:count]


def compare(turn,rows):
    assert [r['id'] for r in turn.batch.messages]==[r['id'] for r in rows]
    assert [r['date'] for r in turn.batch.messages]==[r['date'] for r in rows]


async def new_run(root,name,reader,**options):
    req=request(root,name,**options);store=SQLiteSyncStore(root/(name+'.sqlite3'))
    eng=BackfillEngine(store,req.collection_id,read_batch=reader)
    status=(await eng.start(req,submission='new')).status
    g.save(root/(name+'.case.json'),dict(request=req.to_dict(),run=status.run.to_dict()))
    return req,store,eng,status


async def reopen(root,name,reader=None,forbid_clock=False):
    req=BackfillStartRequest.from_dict(g.read(root/(name+'.case.json'))['request'])
    store=SQLiteSyncStore(root/(name+'.sqlite3'),create=False)
    kw=dict(clock=g.p.forbidden_clock,monotonic_ns=g.p.forbidden_clock) if forbid_clock else {}
    eng=BackfillEngine(store,req.collection_id,read_batch=reader,**kw)
    status=(await eng.start(req,submission='retry')).status
    return req,store,eng,status


def accept(root,name,turn,report,media=None):
    dest=root/(name+'-receiver');dest.mkdir(exist_ok=True)
    before=stamp();counts=g.base.accept(dest,turn,media)
    report['events'].append(dict(kind='receiver-commit',before=before,after=stamp(),
                                 receipt=turn.delivery.to_dict(),counts=counts))
    return counts


def observed_reader(tg,guard,report,after=None):
    async def reader(chat,**kw):
        guard.turn+=1
        event=dict(kind='source',turn=guard.turn,entry=stamp(),after_id=str(kw['after_id']))
        report['events'].append(event)
        try:
            result=await tg.get_message_batch(chat,**kw)
        except BaseException as error:
            event.update(end=stamp(),outcome=type(error).__name__)
            if after:await after(None,error,event)
            raise
        event.update(end=stamp(),outcome='result',ids=[r['id'] for r in result.messages],stop=result.stop_reason)
        if after:await after(result,None,event)
        return result
    return reader


def assert_spacing(report,prior_status,later_event,pause):
    assert _decode_date(later_event['entry']['utc'])>=prior_status.pacing_not_before
    earlier=[e for e in report['events'] if e['kind']=='source' and e is not later_event]
    if earlier:
        elapsed=(later_event['entry']['monotonic_ns']-earlier[-1]['end']['monotonic_ns'])/1e9
        assert elapsed>=pause
        report.setdefault('measured_intervals',[]).append(elapsed)


async def qualify(root,tg,client,guard,report):
    peer=await client.get_input_entity(g.CHAT);messages=[];offset=0
    for _ in range(2):
        reply=await client(functions.messages.GetHistoryRequest(peer,offset,None,0,100,0,0,0),flood_sleep_threshold=0)
        if not reply.messages:break
        assert all(isinstance(m,(types.Message,types.MessageService)) and utils.get_peer_id(m.peer_id)==g.CHAT for m in reply.messages)
        messages.extend(reply.messages);offset=min(m.id for m in reply.messages);await asyncio.sleep(5)
    else:raise AssertionError('independent bounded fixture has no observed end')
    rows=[dict(id=str(m.id),date=_encode_date(m.date),media_kind=type(m.media).__name__ if m.media else None)
          for m in sorted(messages,key=lambda m:m.id)]
    assert rows==g.read(root/'small-oracle.json')['messages'], 'source view changed; retain evidence and stop'
    photo=next(m for m in messages if m.id==14);assert isinstance(photo.media,types.MessageMediaPhoto)
    data=await client.download_media(photo,file=bytes)
    selected=dict(id=str(photo.id),date=_encode_date(photo.date),size=len(data),sha256=hashlib.sha256(data).hexdigest())
    historical=g.read(g.base.OLD.parent/'tgdata19-gate-b-live-20261007-prebuild'/'small-oracle.json')['selected_photo']
    assert all(selected[k]==historical[k] for k in ('id','size','sha256'))
    g.save(root/'gate-oracle.json',dict(messages=rows,selected_photo=selected,complete=True,
        method='independent direct descending history to explicit empty page; direct SDK photo bytes',captured_at=stamp()))
    report['checks']=['46 exact independent ID/date observations unchanged','independently downloaded photo digest unchanged']


async def budget_case(root,tg,client,guard,report,primary):
    test=ReadBudget(root/'gate-test-budget.sqlite3');ident=g.account();policy=test.configure(ident,3)
    client._tgdata_read_budget=tg.connection_engine.read_budget=g.RestrictiveBudget(primary,test)
    entered=asyncio.Event();release=asyncio.Event();errors=[]
    async def hold(result,error,event):
        if guard.turn==1:
            assert isinstance(error,ReadBudgetExceeded);errors.append(error);entered.set();await release.wait()
    reader=observed_reader(tg,guard,report,hold)
    req,store,eng,status=await new_run(root,'budget',reader,batch=5)
    task=asyncio.create_task(eng.prepare(ctx(status)));await asyncio.wait_for(entered.wait(),60)
    n=guard.history_count
    paused=await eng.control(status.run,**args(status,'pause','pause-before-error-settlement'))
    await refuse(BackfillConflictError,eng.control(status.run,**args(paused.status,'abandon','busy-abandon')))
    await refuse(BackfillConflictError,eng.recover(status.run,attempt_id=paused.status.attempt_id,
        command_id='busy-recovery',expected_control_revision=1,previous_reader_stopped=True))
    assert guard.history_count==n
    release.set()
    try:await task
    except ReadBudgetExceeded as error:assert error is errors[0]
    else:raise AssertionError('expected actual test-allowance failure')
    saved=await eng.status(status.run)
    assert saved.operator_intent=='paused' and saved.pending_message_count==3 and saved.last_failure_account_id==ident
    replay=await eng.prepare(ctx(saved));compare(replay,expected(root,req,0,3))
    assert replay.replayed and replay.batch.stop_reason=='interrupted' and test.status(ident).remaining==0
    accept(root,'budget',replay,report);ack=await eng.acknowledge(replay.delivery)
    assert datetime.now(timezone.utc)<saved.pacing_not_before
    assert (await eng.prepare(ctx(ack))).batch is None and guard.history_count==n
    new_policy=test.configure(ident,6)
    assert new_policy.started_at==policy.started_at and new_policy.used==3 and new_policy.remaining==3
    assert primary.status(ident).limit==5000
    resumed=await eng.control(status.run,**args(ack,'resume','resume-after-test-cap-increase'))
    assert resumed.status.pacing_not_before==saved.pacing_not_before
    early=await eng.prepare(ctx(resumed.status));assert early.wait_seconds>0 and guard.history_count==n
    report['early_wait_seconds']=early.wait_seconds
    await asyncio.sleep(early.wait_seconds+0.03)
    try:await eng.prepare(ctx(resumed.status))
    except ReadBudgetExceeded:pass
    else:raise AssertionError('expected cap 6 exhaustion after second prefix')
    assert_spacing(report,saved,[e for e in report['events'] if e['kind']=='source'][-1],req.pause_seconds)
    later=await eng.status(status.run);turn=await eng.prepare(ctx(later))
    compare(turn,expected(root,req,ack.after_id,3));counts=accept(root,'budget',turn,report)
    done=await eng.acknowledge(turn.delivery);await eng.control(status.run,**args(done,'cancel','finish'))
    assert counts==dict(receipts=2,messages=6) and test.status(ident).used==6
    assert guard.history_count==2
    report['checks']=['LIVE actual allowance 3 exhausted, usable prefix retained',
        'INJECTED pause during real error return preserves original exception/data',
        'busy recovery/abandon refused; replay/receiver/ack while paused and exhausted',
        'test-only cap increase to 6 retains charges/shared 5000 policy',
        'resume preserves wait; early call sends nothing; later real send rechecks both ledgers']
    report['test_budget']=dict(before_limit=3,after_limit=6,used=6,increase='explicit test policy; not natural expiry')


async def pause_case(root,tg,guard,report):
    entered=asyncio.Event();release=asyncio.Event()
    async def hold(result,error,event):
        assert error is None;entered.set();await release.wait()
    req,store,eng,status=await new_run(root,'pause',observed_reader(tg,guard,report,hold))
    task=asyncio.create_task(eng.prepare(ctx(status)));await asyncio.wait_for(entered.wait(),60)
    paused=await eng.control(status.run,**args(status,'pause','first-pause'))
    await refuse(BackfillConflictError,eng.control(status.run,**args(paused.status,'abandon','busy-abandon')))
    await refuse(BackfillConflictError,eng.recover(status.run,attempt_id=paused.status.attempt_id,
        command_id='busy-recover',expected_control_revision=1,previous_reader_stopped=True))
    release.set();turn=await task
    compare(turn,expected(root,req,0,2));assert turn.status.operator_intent=='paused'
    reads=guard.history_count;accept(root,'pause',turn,report);ack=await eng.acknowledge(turn.delivery)
    resume_args=args(ack,'resume','old-resume')
    resumed=await eng.control(status.run,**resume_args)
    again=await eng.control(status.run,**args(resumed.status,'pause','newer-pause'))
    await refuse(BackfillConflictError,eng.control(status.run,**resume_args))
    # Both loads see the same control revision; exactly one command can commit.
    ready=asyncio.Event()
    class Barrier:
        count=0
        async def load(self,chat):
            raw=await store.load(chat);self.count+=1
            if self.count<=2:
                if self.count==2:ready.set()
                await ready.wait()
            return raw
        async def compare_and_swap(self,*a):return await store.compare_and_swap(*a)
    barrier=Barrier()
    controls=[BackfillEngine(barrier,req.collection_id,clock=g.p.forbidden_clock) for _ in range(2)]
    outcomes=await asyncio.gather(controls[0].control(status.run,**args(again.status,'pause','opposing-pause')),
        controls[1].control(status.run,**args(again.status,'resume','opposing-resume')),return_exceptions=True)
    assert sum(isinstance(r,BackfillControlResult) and r.applied for r in outcomes)==1
    assert sum(isinstance(r,BackfillConflictError) for r in outcomes)==1
    # Hold a committed reply, accept a newer decision, then release the older reply.
    entered=asyncio.Event();release=asyncio.Event()
    class LateReply:
        async def load(self,chat):return await store.load(chat)
        async def compare_and_swap(self,*a):
            done=await store.compare_and_swap(*a);entered.set();await release.wait();return done
    current=await eng.status(status.run)
    local=BackfillEngine(LateReply(),req.collection_id,clock=g.p.forbidden_clock)
    old=asyncio.create_task(local.control(status.run,**args(current,'pause','delayed-pause')))
    await entered.wait();latest=await eng.status(status.run)
    newer=await eng.control(status.run,**args(latest,'resume','later-resume'))
    release.set();late=await old
    assert late.status.control_revision<newer.status.control_revision and (await eng.status(status.run))==newer.status
    assert late.status.operator_intent=='paused' and newer.status.operator_intent=='active'
    assert guard.history_count==reads
    await eng.control(status.run,**args(newer.status,'cancel','finish'))
    report['checks']=['INJECTED pause-before-real-result publication preserved',
        'active prepare refuses recovery/abandonment','real durable receiver accepts paused data',
        'stale resume refuses','opposing controls accept exactly one revision',
        'delayed older response does not replace newer intent','local decisions send no history requests']


async def terminal_case(root,tg,guard,report):
    for index,order in enumerate(('cancel-first','ack-first','empty-cancel-first')):
        if index:await asyncio.sleep(5)
        reader=observed_reader(tg,guard,report)
        req,store,eng,status=await new_run(root,order,reader,photo=True,pause=5)
        if order=='empty-cancel-first':
            # Fresh fixed intent starts beyond the last source ID; real EOF is held.
            highest=max(int(r['id']) for r in g.read(root/'gate-oracle.json')['messages'])
            # This is its own explicit imported successor after cancelling empty intent.
            cancelled=await eng.control(status.run,**args(status,'cancel','replace-empty-intent'))
            req=replace(req,run_id='empty-window-tail',after_id=highest,expected_predecessor=status.run)
            status=(await eng.start(req,submission='new')).status
            entered=asyncio.Event();release=asyncio.Event()
            async def hold(result,error,event):
                assert error is None and not result.messages and result.stop_reason=='end'
                entered.set();await release.wait()
            eng._read_batch=observed_reader(tg,guard,report,hold)
            task=asyncio.create_task(eng.prepare(ctx(status)));await asyncio.wait_for(entered.wait(),60)
            await eng.control(status.run,**args(status,'cancel','cancel-before-empty-publication'))
            release.set();turn=await task
            assert turn.status.terminal_outcome=='cancelled' and turn.status.source_exhausted
            report['events'].append(dict(kind='terminal',order=order,status=turn.status.to_dict()))
            continue
        turn=await eng.prepare(ctx(status));compare(turn,expected(root,req,req.after_id))
        assert turn.batch.stop_reason=='end' and turn.status.source_exhausted and turn.status.terminal_outcome is None
        accept(root,order,turn,report);n=guard.history_count
        if order=='cancel-first':
            cancelled=await eng.control(status.run,**args(turn.status,'cancel','cancel-after-receiver-before-ack'))
            done=await eng.acknowledge(turn.delivery);assert done.terminal_outcome=='cancelled'
        else:
            done=await eng.acknowledge(turn.delivery);raw=await store.load(g.CHAT)
            result=await eng.control(status.run,**args(done,'cancel','cancel-after-ack'))
            assert result.outcome=='terminal' and not result.applied and result.status==done
            assert done.terminal_outcome=='completed' and await store.load(g.CHAT)==raw
        assert guard.history_count==n
        report['events'].append(dict(kind='terminal',order=order,status=done.to_dict()))
    report['checks']=['LIVE final end with data; actual receiver committed',
        'INJECTED cancel-before-final-ack stays cancelled','ack-before-cancel stays completed',
        'cancel-before-real-empty-publication stays cancelled; no false completed outcome']


async def restart_seed(root,tg,guard,report):
    req,store,eng,status=await new_run(root,'restart',observed_reader(tg,guard,report))
    turn=await eng.prepare(ctx(status));compare(turn,expected(root,req,0,2))
    accept(root,'restart',turn,report);ack=await eng.acknowledge(turn.delivery)
    assert datetime.now(timezone.utc)<ack.pacing_not_before
    report['saved_status']=ack.to_dict()
    report['checks']=['LIVE result and early receiver acknowledgment preserve attempt-end deadline']


async def restart_early(root,report):
    req,store,eng,status=await reopen(root,'restart')
    raw=await store.load(g.CHAT);times=[]
    for _ in range(2):
        turn=await eng.prepare(ctx(status));assert turn.wait_seconds>0 and turn.batch is None
        times.append(turn.wait_seconds)
    assert times[1]<=times[0] and await store.load(g.CHAT)==raw
    report['wait_seconds']=times;report['saved_status']=status.to_dict()
    report['checks']=['actual fresh process returns decreasing wait without reader/network/write']


async def restart_next(root,tg,guard,report):
    req,store,eng,status=await reopen(root,'restart',observed_reader(tg,guard,report))
    turn=await eng.prepare(ctx(status));compare(turn,expected(root,req,status.after_id,2))
    assert_spacing(report,status,report['events'][-1],req.pause_seconds)
    first=g.read(root/'restart_seed.result.json')['events'][0]
    # Parent has independently qualified this host's cross-process monotonic domain.
    elapsed=(report['events'][0]['entry']['monotonic_ns']-first['end']['monotonic_ns'])/1e9
    assert elapsed>=req.pause_seconds;report['restart_elapsed_seconds']=elapsed
    wait=max(0,(turn.status.pacing_not_before-datetime.now(timezone.utc)).total_seconds())
    await asyncio.sleep(wait+0.03)
    before=stamp();accept(root,'restart',turn,report);ack=await eng.acknowledge(turn.delivery)
    assert datetime.now(timezone.utc)>ack.pacing_not_before
    next_turn=await eng.prepare(ctx(ack));compare(next_turn,expected(root,req,ack.after_id,2))
    event=[e for e in report['events'] if e['kind']=='source'][-1]
    assert_spacing(report,turn.status,event,req.pause_seconds)
    assert (event['entry']['monotonic_ns']-before['monotonic_ns'])/1e9<req.pause_seconds
    accept(root,'restart',next_turn,report);done=await eng.acknowledge(next_turn.delivery)
    await eng.control(status.run,**args(done,'cancel','finish'))
    report['checks']=['LIVE read after process reopen respects saved deadline',
        'same-host monotonic bracket supports diagnostic elapsed comparison',
        'late receiver ack does not start another wait; next read immediately eligible']


async def unknown_source(root,tg,guard,report,primary):
    holder={}
    async def die(result,error,event):
        assert error is None and len(result.messages)==2
        status=await holder['eng'].status(holder['run'])
        assert status.attempt_id and status.pending_batch_id is None and status.pacing_not_before is None
        recovery=dict(attempt_id=status.attempt_id,command_id='lost-recovery',
            expected_control_revision=status.control_revision,previous_reader_stopped=True)
        g.save(root/'unknown.recovery.json',dict(run=status.run.to_dict(),args=recovery,source_pid=os.getpid()))
        report.update(result='EXPECTED_EXIT',boundary='after actual source answer, before durable publication',
                      saved_status=status.to_dict(),rpc=guard.rpc,requested_slots=guard.slots,
                      budget_used=primary.status(g.account()).used)
        g.save(root/'unknown_source.result.json',report)
        os._exit(81)
    req,store,eng,status=await new_run(root,'unknown',observed_reader(tg,guard,report,die))
    holder.update(eng=eng,run=status.run)
    await eng.prepare(ctx(status))
    raise AssertionError('owned source exit boundary not reached')


async def recover_crash(root,report):
    from tgdata.backfill import BackfillRunRef
    proof=g.read(root/'unknown_source.exit.json');assert proof['returncode']==81
    req,store,eng,status=await reopen(root,'unknown')
    record=g.read(root/'unknown.recovery.json')
    assert status.attempt_id==record['args']['attempt_id'] and proof['pid']==record['source_pid']
    raw=await store.load(g.CHAT)
    await refuse(BackfillRecoveryRequired,eng.prepare(ctx(status)))
    assert await store.load(g.CHAT)==raw
    original=sqlite3.connect
    class Crash(sqlite3.Connection):
        def commit(self):
            candidate=None
            if self.total_changes:
                row=self.execute('SELECT data FROM tgdata_sync_state').fetchone()
                if row and json.loads(row[0])['current']['last_recovery'] is not None:
                    candidate=_BackfillState.from_json(row[0],req.collection_id,g.CHAT)
            super().commit()
            if candidate is not None:
                observed=candidate.status()
                assert observed.pacing_ended_at is None and observed.attempt_id is None
                assert (observed.pacing_not_before-observed.last_recovery_at).total_seconds()==req.pause_seconds
                report.update(result='EXPECTED_EXIT',boundary='after actual recovery commit, before reply',
                              saved_status=observed.to_dict())
                g.save(root/'recover_crash.result.json',report);os._exit(82)
    def connect(*a,**kw):kw['factory']=Crash;return original(*a,**kw)
    with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
        await eng.recover(BackfillRunRef.from_dict(record['run']),**record['args'])
    raise AssertionError('recovery commit exit boundary not reached')


async def recover_retry(root,report):
    from tgdata.backfill import BackfillRunRef
    assert g.read(root/'recover_crash.exit.json')['returncode']==82
    req,store,eng,status=await reopen(root,'unknown',forbid_clock=True)
    record=g.read(root/'unknown.recovery.json');raw=await store.load(g.CHAT)
    for _ in range(2):
        result=await eng.recover(BackfillRunRef.from_dict(record['run']),**record['args'])
        assert not result.applied and result.outcome=='recovered' and result.status==status
    assert await store.load(g.CHAT)==raw
    assert status.to_dict()==g.read(root/'recover_crash.result.json')['saved_status']
    local=BackfillEngine(store,req.collection_id)
    early=await local.prepare(ctx(status));assert early.wait_seconds>0
    assert await store.load(g.CHAT)==raw
    report.update(wait_seconds=early.wait_seconds,saved_status=status.to_dict())
    report['checks']=['confirmed owned source and recovery workers exited',
        'unknown source refused another read','recovery committed full unknown-end interval',
        'lost recovery reply recognized twice with forbidden clocks and identical deadline',
        'new process early prepare returns wait with no network/write']


async def unknown_next(root,tg,guard,report):
    req,store,eng,status=await reopen(root,'unknown',observed_reader(tg,guard,report))
    turn=await eng.prepare(ctx(status));compare(turn,expected(root,req,0,2))
    event=report['events'][0]
    assert _decode_date(event['entry']['utc'])>=status.pacing_not_before
    observed=_decode_date(g.read(root/'recover_crash.result.json')['saved_status']['last_recovery_at'])
    report['recovery_to_read_seconds']=(_decode_date(event['entry']['utc'])-observed).total_seconds()
    assert report['recovery_to_read_seconds']>=req.pause_seconds
    accept(root,'unknown',turn,report);done=await eng.acknowledge(turn.delivery)
    await eng.control(status.run,**args(done,'cancel','finish'))
    report['checks']=['LIVE read follows conservative recovery deadline',
        'unaccepted source position unchanged; reread exact expected prefix',
        'actual receiver accepts recovered delivery; no manufactured exhaustion']


async def successor_case(root,tg,guard,report):
    req,store,eng,status=await new_run(root,'succession',observed_reader(tg,guard,report),
        photo=True,media='download',pause=5)
    first_root=root/'retired-media'
    first=await eng.prepare(ctx(status),download_media_to=first_root)
    compare(first,expected(root,req,req.after_id));assert first.batch.stop_reason=='end'
    blob=first.batch.messages[0]['media']['blob'];oracle=g.read(root/'gate-oracle.json')['selected_photo']
    assert {k:blob[k] for k in ('size','sha256')}=={k:oracle[k] for k in ('size','sha256')}
    retired=await eng.control(status.run,**args(first.status,'abandon','retire-owed-photo'))
    assert retired.status.after_id==req.after_id and retired.status.abandoned_batch_id==first.batch.batch_id
    assert g.base.digest(first_root/blob['path'])==blob['sha256']
    await asyncio.sleep(5)
    second_req=replace(req,run_id='second',expected_predecessor=status.run)
    second_status=(await eng.start(second_req,submission='new')).status
    second_root=root/'second-media'
    second=await eng.prepare(ctx(second_status),download_media_to=second_root)
    assert second.batch.batch_id==first.batch.batch_id and second.delivery!=first.delivery
    raw=await store.load(g.CHAT);await refuse(BackfillUnknownReceipt,eng.acknowledge(first.delivery))
    assert await store.load(g.CHAT)==raw and (await eng.status(second_status.run)).after_id==req.after_id
    accept(root,'succession',second,report,second_root);done=await eng.acknowledge(second.delivery)
    assert done.terminal_outcome=='completed'
    await asyncio.sleep(5)
    third_req=replace(req,run_id='third',expected_predecessor=second_status.run)
    third_status=(await eng.start(third_req,submission='new')).status;third_root=root/'third-media'
    third=await eng.prepare(ctx(third_status),download_media_to=third_root)
    assert third.batch.batch_id==second.batch.batch_id and third.delivery!=second.delivery
    raw=await store.load(g.CHAT);old=await eng.acknowledge(second.delivery)
    assert old.history_limited and old.terminal_outcome=='completed' and await store.load(g.CHAT)==raw
    assert (await eng.status(third_status.run)).pending_batch_id==third.batch.batch_id
    counts=accept(root,'succession',third,report,third_root);last=await eng.acknowledge(third.delivery)
    assert counts==dict(receipts=2,messages=1) and last.terminal_outcome=='completed'
    assert g.base.digest(first_root/blob['path'])==blob['sha256']
    report['checks']=['LIVE photo digest matches independent download',
        'explicit abandonment records withdrawn obligation without accepted progress or blob deletion',
        'equal-hash successor has distinct receipt; retired receipt refuses',
        'retained accepted old receipt cannot settle equal-hash current pending',
        'actual receiver has 2 scoped receipts and one unique message']


NETWORK={'qualify','budget','pause','terminal','restart_seed','restart_next','unknown_source','unknown_next','succession'}


async def worker(root,name):
    report=dict(case=name,code_revision=CODE,pid=os.getpid(),events=[],checks=[],result='UNFINISHED',
                scope='LIVE source; INJECTED owned local barriers' if name in NETWORK else 'LOCAL actual live-origin state; sockets blocked')
    tg=guard=None;primary=None
    try:
        if name in NETWORK:
            primary=ReadBudget(g.base.OLD/'account-read-budget.sqlite3');before=primary.status(g.account())
            allocation=next(v['slots'] for v in map(json.loads,(root/'allocations.jsonl').read_text().splitlines()) if v['name']==name)
            assert before.limit==5000 and before.remaining>=allocation
            report['budget_before']=dict(limit=before.limit,used=before.used)
            tg,client,guard=await g.source(root,name,primary,media=name in ('qualify','succession'))
            if name=='qualify':await qualify(root,tg,client,guard,report)
            elif name=='budget':await budget_case(root,tg,client,guard,report,primary)
            elif name=='pause':await pause_case(root,tg,guard,report)
            elif name=='terminal':await terminal_case(root,tg,guard,report)
            elif name=='restart_seed':await restart_seed(root,tg,guard,report)
            elif name=='restart_next':await restart_next(root,tg,guard,report)
            elif name=='unknown_source':await unknown_source(root,tg,guard,report,primary)
            elif name=='unknown_next':await unknown_next(root,tg,guard,report)
            elif name=='succession':await successor_case(root,tg,guard,report)
        else:
            with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
                 patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
                if name=='restart_early':await restart_early(root,report)
                elif name=='recover_crash':await recover_crash(root,report)
                elif name=='recover_retry':await recover_retry(root,report)
                else:raise AssertionError('unknown worker')
        report['result']='PASS'
    except BaseException as error:
        report.update(result='FAIL',error_type=type(error).__name__)
        raise
    finally:
        if tg:await tg.close()
        if guard:
            report.update(rpc=guard.rpc,history_requests=guard.history_count,requested_slots=guard.slots,
                          requested_media_bytes=guard.media_bytes)
        if primary:
            after=primary.status(g.account());assert after.limit==5000
            report['budget_after']=dict(limit=after.limit,used=after.used)
        g.save(root/(name+'.result.json'),report)
        print(json.dumps(dict(case=name,result=report['result'],checks=len(report['checks']),
                             requested_slots=report.get('requested_slots',0)),sort_keys=True),flush=True)


def launch(root,name,slots=0,expected_code=0):
    if slots:g.allocate(root,name,slots)
    command=[sys.executable,str(Path(__file__).resolve()),'--worker',name,'--root',str(root)]
    with (root/(name+'.log')).open('x') as out:
        process=subprocess.Popen(command,cwd=g.base.CONFIG.parent,stdout=out,stderr=subprocess.STDOUT)
        try:code=process.wait(timeout=190)
        except subprocess.TimeoutExpired:
            process.kill();code=process.wait();g.save(root/(name+'.timeout.json'),dict(pid=process.pid,returncode=code))
            raise AssertionError('owned worker timeout; terminated and waited')
    proof=dict(pid=process.pid,returncode=code,expected_code=expected_code,waited=True,observed_at=stamp())
    g.save(root/(name+'.exit.json'),proof)
    assert code==expected_code, 'worker '+name+' failed; inspect private type/trace without changing expectations'
    print(json.dumps(dict(case=name,exit=code,expected=expected_code)),flush=True)


def wait_deadline(root,name):
    saved=g.read(root/(name+'.result.json'))['saved_status']
    seconds=(_decode_date(saved['pacing_not_before'])-datetime.now(timezone.utc)).total_seconds()
    if seconds>0:time.sleep(seconds+0.03)


def run(root):
    assert g.p.telethon.__version__=='1.45.0' and g.read(root/'prebuild-result.json')['result']=='PASS'
    # A diagnostic host-property measurement; never state-machine clock evidence.
    start=time.monotonic_ns()
    answer=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--clock'],capture_output=True,text=True,check=True)
    end=time.monotonic_ns();tick=int(answer.stdout)
    assert start<=tick<=end
    g.save(root/'clock-bracket.json',dict(parent_before=start,child=tick,parent_after=end,
        meaning='same-host diagnostics only; monotonic values are never persisted in run state'))
    launch(root,'qualify',200)
    time.sleep(5);launch(root,'budget',40)
    time.sleep(5);launch(root,'pause',40)
    time.sleep(5);launch(root,'terminal',40)
    time.sleep(5);launch(root,'restart_seed',30)
    launch(root,'restart_early')
    wait_deadline(root,'restart_seed');launch(root,'restart_next',40)
    time.sleep(5);launch(root,'unknown_source',20,81)
    launch(root,'recover_crash',expected_code=82)
    launch(root,'recover_retry')
    wait_deadline(root,'recover_retry');launch(root,'unknown_next',20)
    time.sleep(5);launch(root,'succession',50)
    names=['qualify','budget','pause','terminal','restart_seed','restart_early','restart_next',
           'unknown_source','recover_crash','recover_retry','unknown_next','succession']
    reports=[g.read(root/(name+'.result.json')) for name in names]
    assert all(r['result'] in ('PASS','EXPECTED_EXIT') for r in reports)
    allocations=[json.loads(line) for line in (root/'allocations.jsonl').read_text().splitlines()]
    assert sum(v['slots'] for v in allocations)<=1000
    summary=dict(result='PASS',gate='C',code_revision=CODE,workers=len(names),
        allocated_slots=sum(v['slots'] for v in allocations),
        observed_slots_including_prebuild=g.read(root/'prebuild-result.json')['requested_slots']+sum(r.get('requested_slots',0) for r in reports),
        checks=sum(len(r['checks']) for r in reports),cases=[dict(name=r['case'],result=r['result']) for r in reports],
        primary_policy='unchanged 5000/day; all source workers enforce it',
        expiry='test-only cap increase; natural rolling expiry is deterministic offline evidence')
    g.save(root/'summary.json',summary);print(json.dumps(summary,sort_keys=True),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true');parser.add_argument('--worker',choices=sorted(NETWORK|{'restart_early','recover_crash','recover_retry'}))
    parser.add_argument('--clock',action='store_true');parser.add_argument('--root',type=Path,default=g.ROOT)
    options=parser.parse_args();logging.disable(logging.CRITICAL)
    if options.clock:print(time.monotonic_ns())
    elif options.worker:asyncio.run(asyncio.wait_for(worker(options.root,options.worker),180))
    elif options.run:run(options.root)
    else:parser.print_help()
