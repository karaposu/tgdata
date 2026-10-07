"""Opt-in Gate D public integration; default --help is offline.

--run starts bounded sequential owned workers on the previously approved sources.
Raw snapshots, account state and payloads remain in the private root. Local faults
are explicitly injected; no source writes, joins, policy increases or quota resets.
"""
import argparse
import asyncio
from contextlib import ExitStack, contextmanager
from dataclasses import replace
from datetime import timedelta
import json
import logging
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
from unittest.mock import patch

import gate_d_support as g
from telethon import functions, types, utils
from tgdata import (TgData, SQLiteSyncStore, BackfillStartRequest, BackfillRunRef,
    BackfillPrepareContext, BackfillDeliveryRef, BackfillControlResult,
    BackfillConflictError, BackfillUnknownRun, BackfillUnknownReceipt,
    BackfillRecoveryRequired, BackfillMediaError)
from tgdata.history_window import _decode_date, _encode_date

ctx=BackfillPrepareContext.from_status
ALLOCATIONS={'qualify':450,'main-seed':150,'main-continue':260,'controls':40,
    'prefix':130,'unknown-source':10,'unknown-follow':10,'photo-source':10,'photo-follow':20}


class Inconclusive(RuntimeError):pass


async def refuse(kind,awaitable):
    try:await awaitable
    except kind:return
    raise AssertionError('expected '+kind.__name__)


@contextmanager
def offline(tg):
    with ExitStack() as stack:
        for method in ('connect','connect_ex'):
            stack.enter_context(patch.object(socket.socket,method,side_effect=AssertionError('local sockets forbidden')))
        stack.enter_context(patch.object(tg.connection_engine,'_load_config',side_effect=AssertionError('local config forbidden')))
        yield
        assert tg.connection_engine._config is None and tg.connection_engine._primary_client is None


def request(root,name,*,photo=False,batch=120,media='references'):
    oracle=g.read(root/('small-oracle.json' if photo else 'large-oracle.json'))
    if photo:
        start=_decode_date(oracle['photo']['date']);end=start+timedelta(microseconds=1);after=int(oracle['photo']['id'])-1
    else:start=_decode_date(oracle['window']['start_date']);end=_decode_date(oracle['window']['end_date']);after=0
    return BackfillStartRequest('gate-d-'+name,g.SMALL if photo else g.LARGE,'first',g.DESTINATION,12,None,
        origin='imported' if photo else 'fresh',after_id=after,media_mode=media,batch_size=batch,start_date=start,end_date=end)


def originals(root,name):return BackfillStartRequest.from_dict(g.read(root/(name+'-request.json')))
def backend(root,name,create=False):return SQLiteSyncStore(root/(name+'.sqlite3'),create=create)


async def new(tg,root,name,report,guard=None,**options):
    req=request(root,name,**options);g.save(root/(name+'-request.json'),req.to_dict())
    status=(await g.operation(report,'start-'+name,tg.start_backfill(req,submission='new'),guard)).status
    g.save(root/(name+'-run.json'),status.run.to_dict());return req,status


async def reopen(tg,root,name,report,guard=None):
    req=originals(root,name)
    result=await g.operation(report,'original-start-retry-'+name,tg.start_backfill(req,submission='retry'),guard)
    assert not result.applied;return req,result.status


def compare(batch,rows):
    actual=[dict(id=r['id'],date=r['date']) for r in batch.messages]
    if actual!=rows:raise Inconclusive('qualified source set drift or reader mismatch; preserve actual result for audit')


def save_turn(root,name,turn):
    g.save(root/(name+'-turn.json'),dict(batch=turn.batch.to_dict() if turn.batch else None,
        delivery=turn.delivery.to_dict() if turn.delivery else None,status=turn.status.to_dict(),replayed=turn.replayed))


def receive(receiver,turn,report,media=None):
    before=g.stamp();fresh=receiver.accept(turn.batch,turn.delivery,media)
    report.setdefault('receipts',[]).append(dict(delivery=turn.delivery.to_dict(),fresh=fresh,
        entry=before,end=g.stamp(),snapshot_sha256=__import__('hashlib').sha256(turn.batch.to_json().encode()).hexdigest()))
    assert receiver.observation(turn.delivery).to_json()==turn.batch.to_json();return fresh


async def wait_turn(tg,status,report,label,guard=None,*,must_wait=False):
    turn=await g.operation(report,label,tg.prepare_backfill(ctx(status)),guard)
    if must_wait and not (turn.wait_seconds is not None and turn.wait_seconds>0):
        raise Inconclusive('host/connection delay expired required early-wait observation')
    if turn.wait_seconds is not None and turn.wait_seconds>0:
        report.setdefault('waits',[]).append(dict(label=label,seconds=turn.wait_seconds,observed=g.stamp(),status=turn.status.to_dict()))
        await asyncio.sleep(turn.wait_seconds+0.03)
        return None
    return turn


def report_exit(root,name,report,code,guard=None,budget=None):
    report.update(result='EXPECTED_OWNED_EXIT',exit_code=code,exited=g.stamp())
    if guard:report.update(guard.report())
    if budget:
        v=budget.status(g.account());report['budget_after']=dict(limit=v.limit,used=v.used,reserved=v.reserved)
    g.save(root/(name+'-result.json'),report);os._exit(code)


async def qualify(root,report,tg,client,guard):
    old=g.read(g.OLD/'real_sdk_pages.manifest.json');start=_decode_date(old['window']['start_date']);end=_decode_date(old['window']['end_date'])
    peer=await g.operation(report,'independent-large-peer',client.get_input_entity(g.LARGE),guard)
    rows=[];offset=0;witness=False
    for page in range(4):
        reply=await g.operation(report,'independent-large-descending-'+str(page),client(functions.messages.GetHistoryRequest(
            peer,offset,end if page==0 else None,0,100,0,0,0)),guard)
        if not reply.messages:witness=True;break
        assert all(isinstance(m,(types.Message,types.MessageService)) and utils.get_peer_id(m.peer_id)==g.LARGE for m in reply.messages)
        rows.extend(dict(id=str(m.id),date=_encode_date(m.date)) for m in reply.messages if start<=m.date<end)
        if any(m.date<start for m in reply.messages):witness=True;break
        offset=min(m.id for m in reply.messages);await asyncio.sleep(5)
    if not witness:raise Inconclusive('bounded independent older-than-start witness unavailable')
    rows.sort(key=lambda r:int(r['id']));assert len({r['id'] for r in rows})==len(rows)
    if len(rows)<250:raise Inconclusive('large source no longer qualifies 250-message scope')
    cut=_decode_date(rows[249]['date'])+timedelta(microseconds=1)
    selected=[r for r in rows if _decode_date(r['date'])<cut]
    if not 240<len(selected)<360:raise Inconclusive('date-tied closed prefix cannot qualify bounded three turns')
    await asyncio.sleep(5)
    newest=await g.operation(report,'independent-latest-three',client(functions.messages.GetHistoryRequest(peer,0,None,0,3,0,0,0)),guard)
    assert len(newest.messages)==3
    daily=sorted([dict(id=str(m.id),date=_encode_date(m.date)) for m in newest.messages],key=lambda r:int(r['id']))
    assert int(daily[0]['id'])>int(selected[-1]['id'])
    oracle=dict(captured=g.stamp(),method='independent descending raw SDK to older-than-start witness; closed prefix fixed before tested reader',
        search_window=old['window'],search_count=len(rows),window=dict(start_date=_encode_date(start),end_date=_encode_date(cut)),
        messages=selected,daily_after=daily[0]['id'],daily_expected=daily[1:],prior_count=350,
        search_difference_from_prior_count=len(rows)-350)
    g.save(root/'large-oracle.json',oracle);report.update(expected_count=len(selected),source_qualified=True)


async def main_seed(root,report,tg,guard,budget):
    req,status=await new(tg,root,'main',report,guard)
    turn=await g.operation(report,'history-first-prepare',tg.prepare_backfill(ctx(status)),guard)
    compare(turn.batch,g.read(root/'large-oracle.json')['messages'][:120]);assert not turn.status.source_exhausted
    save_turn(root,'main-first',turn);report['receiver_delay_started']=g.stamp();await asyncio.sleep(2)
    receiver=g.Receiver(root/'main-receiver',create=True);assert receive(receiver,turn,report)
    report_exit(root,'main-seed',report,73,guard,budget)


async def main_local(root,report):
    events=[];store=backend(root,'main');tg=TgData('/missing-gate-d.ini',backfill_store=store,health_callback=events.append)
    with offline(tg):
        count,snapshot=await g.seed_health(tg,g.LARGE,events)
        req,status=await reopen(tg,root,'main',report)
        expected=g.read(root/'main-first-turn.json');assert status.to_dict()==expected['status']
        paused=await g.operation(report,'local-pause',tg.control_backfill(status.run,command_id='pause',expected_control_revision=0,action='pause'))
        replay=await g.operation(report,'local-paused-replay',tg.prepare_backfill(ctx(paused.status)))
        assert replay.replayed and replay.batch.to_dict()==expected['batch']
        receiver=g.Receiver(root/'main-receiver');assert not receive(receiver,replay,report)
        accepted=await g.operation(report,'local-ack',tg.acknowledge_backfill(replay.delivery))
        await refuse(BackfillConflictError,tg.prepare_backfill(ctx(paused.status)))
        resumed=await g.operation(report,'local-resume',tg.control_backfill(status.run,command_id='resume',expected_control_revision=1,action='resume'))
        early=await g.operation(report,'local-early-prepare',tg.prepare_backfill(ctx(resumed.status)))
        if early.wait_seconds is None or early.wait_seconds<=0:raise Inconclusive('main restart did not observe early deadline')
        assert early.status.pacing_not_before==status.pacing_not_before and accepted.after_id==int(replay.batch.next_after_id)
        assert len(events)==count and tg._health.snapshot()==snapshot
        report.update(early_wait=early.wait_seconds,final_status=resumed.status.to_dict(),local_health_preserved=True)
        await tg.close()


async def main_continue(root,report,tg,guard):
    req,status=await reopen(tg,root,'main',report,guard)
    oracle=g.read(root/'large-oracle.json');receiver=g.Receiver(root/'main-receiver')
    turn=await wait_turn(tg,status,report,'history-restart-wait',guard)
    if turn is None:turn=await g.operation(report,'history-second-prepare',tg.prepare_backfill(ctx(status)),guard)
    compare(turn.batch,oracle['messages'][120:240]);save_turn(root,'main-second',turn)
    assert not turn.status.source_exhausted;receive(receiver,turn,report)
    status=await g.operation(report,'history-second-ack',tg.acknowledge_backfill(turn.delivery),guard)
    history_before=await backend(root,'main').load(g.LARGE)
    daily_status=await g.operation(report,'daily-enroll',tg.initialize_sync(g.LARGE,after_id=int(oracle['daily_after'])),guard)
    daily_before=await backend(root,'daily').load(g.LARGE)
    assert status.after_id!=daily_status.after_id and req.after_id==0
    early=await g.operation(report,'history-wait-before-daily',tg.prepare_backfill(ctx(status)),guard)
    if early.wait_seconds is None or early.wait_seconds<=0:raise Inconclusive('daily interleave began after history wait')
    batch=await g.operation(report,'daily-source-turn',tg.sync_group(g.LARGE,limit=2),guard)
    compare(batch,oracle['daily_expected']);g.save(root/'daily-batch.json',batch.to_dict())
    assert receiver.daily('gate-d-daily',batch)
    daily_done=await g.operation(report,'daily-ack',tg.acknowledge_sync(g.LARGE,batch.batch_id),guard)
    assert await backend(root,'main').load(g.LARGE)==history_before
    assert await backend(root,'daily').load(g.LARGE)!=daily_before
    report['daily_status']=daily_done.to_dict();report['history_unchanged_by_daily']=True
    daily_after=await backend(root,'daily').load(g.LARGE)
    turn=await wait_turn(tg,status,report,'history-wait-after-daily',guard)
    if turn is None:turn=await g.operation(report,'history-final-prepare',tg.prepare_backfill(ctx(status)),guard)
    compare(turn.batch,oracle['messages'][240:]);save_turn(root,'main-final',turn)
    assert turn.status.source_exhausted and turn.status.terminal_outcome is None
    receive(receiver,turn,report);done=await g.operation(report,'history-final-ack',tg.acknowledge_backfill(turn.delivery),guard)
    assert done.terminal_outcome=='completed' and await backend(root,'daily').load(g.LARGE)==daily_after
    report.update(final_status=done.to_dict(),receiver=receiver.summary(),daily_unchanged_by_history=True)


async def controls(root,report,tg,guard):
    from tgdata.smoke_tests.test_25_backfill_delivery import FaultStore
    store=backend(root,'controls');entered=asyncio.Event();release=asyncio.Event();original=tg.get_message_batch;hold=True
    async def read(*a,**kw):
        result=await original(*a,**kw)
        if hold:entered.set();await release.wait()
        return result
    tg.get_message_batch=read
    req,status=await new(tg,root,'controls',report,guard,photo=True,batch=2)
    task=asyncio.create_task(g.operation(report,'real-result-held-before-publication',tg.prepare_backfill(ctx(status)),guard))
    await asyncio.wait_for(entered.wait(),60)
    paused=await g.operation(report,'pause-in-flight',tg.control_backfill(status.run,command_id='pause',expected_control_revision=0,action='pause'),guard)
    await refuse(BackfillConflictError,tg.recover_backfill(status.run,attempt_id=paused.status.attempt_id,
        command_id='busy-recovery',expected_control_revision=1,previous_reader_stopped=True))
    await refuse(BackfillConflictError,tg.control_backfill(status.run,command_id='busy-abandon',expected_control_revision=1,action='abandon'))
    release.set();first=await task;hold=False
    assert first.status.operator_intent=='paused' and first.status.source_exhausted
    save_turn(root,'controls-first',first)
    events=tg._gate_d_events;count,snapshot=await g.seed_health(tg,g.SMALL,events);n=len(guard.rpc)
    replay=await g.operation(report,'paused-replay',tg.prepare_backfill(ctx(first.status)),guard)
    assert replay.replayed and replay.batch.to_json()==first.batch.to_json()
    receiver=g.Receiver(root/'controls-receiver',create=True);receive(receiver,replay,report)
    done=await g.operation(report,'paused-final-ack',tg.acknowledge_backfill(replay.delivery),guard)
    assert done.terminal_outcome=='completed'
    terminal=await g.operation(report,'cancel-after-completion',tg.control_backfill(done.run,
        command_id='late-cancel',expected_control_revision=done.control_revision,action='cancel'),guard)
    assert terminal.outcome=='terminal' and not terminal.applied
    assert len(guard.rpc)==n and len(events)==count and tg._health.snapshot()==snapshot
    previous=done;turns=[first]
    for num in (2,3,4):
        newreq=replace(req,run_id='run-'+str(num),expected_predecessor=previous.run)
        g.save(root/('controls-request-'+str(num)+'.json'),newreq.to_dict())
        status=(await g.operation(report,'successor-'+str(num),tg.start_backfill(newreq,submission='new'),guard)).status
        await asyncio.sleep(5)
        turn=await g.operation(report,'controls-prepare-'+str(num),tg.prepare_backfill(ctx(status)),guard)
        assert turn.batch.to_json()==first.batch.to_json();save_turn(root,'controls-'+str(num),turn);turns.append(turn)
        if num==2:
            raw=await store.load(g.SMALL);old=await tg.acknowledge_backfill(first.delivery)
            assert old.history_limited and await store.load(g.SMALL)==raw
            cancelled=await tg.control_backfill(status.run,command_id='cancel-second',expected_control_revision=0,action='cancel')
            receive(receiver,turn,report);previous=await tg.acknowledge_backfill(turn.delivery)
            assert previous.terminal_outcome=='cancelled' and cancelled.status.pending_batch_id==turn.batch.batch_id
        elif num==3:
            paused=await tg.control_backfill(status.run,command_id='third-pause',expected_control_revision=0,action='pause')
            fault=FaultStore(store);fault.hold=1;slow=TgData('/missing-gate-d.ini',backfill_store=fault)
            with offline(slow):
                delayed=asyncio.create_task(slow.control_backfill(status.run,command_id='third-resume',expected_control_revision=1,action='resume'))
                await asyncio.wait_for(fault.entered.wait(),5)
                now=await tg.get_backfill_status(status.run)
                newer=await tg.control_backfill(status.run,command_id='third-newer-pause',expected_control_revision=now.control_revision,action='pause')
                fault.release.set();late=await delayed
                assert late.status.control_revision==2 and newer.status.control_revision==3
                await refuse(BackfillConflictError,tg.prepare_backfill(ctx(late.status)))
                await refuse(BackfillConflictError,slow.control_backfill(status.run,command_id='third-resume',expected_control_revision=1,action='resume'))
                await slow.close()
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
            shared=Barrier();one=TgData('/missing-one.ini',backfill_store=shared);two=TgData('/missing-two.ini',backfill_store=shared)
            with offline(one),offline(two):
                outcomes=await asyncio.gather(one.control_backfill(status.run,command_id='opposing-one',expected_control_revision=3,action='resume'),
                    two.control_backfill(status.run,command_id='opposing-two',expected_control_revision=3,action='pause'),return_exceptions=True)
                assert sum(isinstance(x,BackfillControlResult) and x.applied for x in outcomes)==1
                assert sum(isinstance(x,BackfillConflictError) for x in outcomes)==1
                await one.close();await two.close()
            now=await tg.get_backfill_status(status.run)
            cancelled=await tg.control_backfill(status.run,command_id='third-cancel',expected_control_revision=now.control_revision,action='cancel')
            abandoned=await tg.control_backfill(status.run,command_id='third-abandon',expected_control_revision=cancelled.status.control_revision,action='abandon')
            previous=abandoned.status;assert previous.after_id==13 and previous.terminal_outcome=='cancelled' and previous.delivery_abandoned
            await refuse(BackfillUnknownReceipt,tg.acknowledge_backfill(turn.delivery))
        else:
            raw=await store.load(g.SMALL)
            await refuse(BackfillUnknownRun,tg.acknowledge_backfill(first.delivery))
            await refuse(BackfillUnknownReceipt,tg.acknowledge_backfill(turns[2].delivery))
            assert await store.load(g.SMALL)==raw
            pending=await tg.prepare_backfill(ctx(turn.status));assert pending.replayed and pending.batch.to_json()==first.batch.to_json()
            cancelled=await tg.control_backfill(status.run,command_id='fourth-cancel',expected_control_revision=0,action='cancel')
            previous=(await tg.control_backfill(status.run,command_id='fourth-abandon',expected_control_revision=1,action='abandon')).status
    report.update(final_status=previous.to_dict(),local_health_preserved=True,
        control_checks=['busy recover/abandon refuse','paused final ack completes','first terminal wins both orders',
            'old accepted same-hash receipt leaves newer pending intact','late resume cannot supersede pause',
            'opposing CAS has one accepted decision','stale prepare/resume refuse','cancel then abandon preserves cursor',
            'retired and pruned receipts cannot accept same-hash successor'])


async def prefix(root,report,tg,guard,budget):
    req,status=await new(tg,root,'prefix',report,guard)
    guard.block_after=1
    await refuse(g.p.ProbeStop,g.operation(report,'prefix-second-send-INJECTED-refusal',tg.prepare_backfill(ctx(status)),guard))
    status=await tg.get_backfill_status(status.run)
    assert status.pending_message_count==100 and not status.source_exhausted and status.last_failure_type=='ProbeStop'
    n=len(guard.rpc);turn=await g.operation(report,'prefix-local-replay',tg.prepare_backfill(ctx(status)),guard)
    compare(turn.batch,g.read(root/'large-oracle.json')['messages'][:100]);assert turn.replayed and turn.batch.stop_reason=='interrupted'
    save_turn(root,'prefix',turn);receiver=g.Receiver(root/'prefix-receiver',create=True);receive(receiver,turn,report)
    done=await g.operation(report,'prefix-local-ack',tg.acknowledge_backfill(turn.delivery),guard)
    assert done.terminal_outcome is None and done.last_failure_type=='ProbeStop' and len(guard.rpc)==n
    assert guard.slots==100 and sum(x['limit'] for x in guard.blocked)==20
    report.update(final_status=done.to_dict(),injected_fault='local second SDK send refusal; no Telegram denial manufactured')


async def unknown_source(root,report,tg,guard,budget):
    original=tg.get_message_batch
    async def exit_after_raw(*a,**kw):
        result=await original(*a,**kw);g.save(root/'unknown-raw-result.json',result.to_dict())
        report['actual_raw_return']=g.stamp();report_exit(root,'unknown-source',report,81,guard,budget)
    tg.get_message_batch=exit_after_raw
    req,status=await new(tg,root,'unknown',report,guard,photo=True,batch=2)
    await g.operation(report,'unknown-real-source-before-publication',tg.prepare_backfill(ctx(status)),guard)
    raise AssertionError('owned source exit not reached')


async def recovery_exit(root,report):
    store=backend(root,'unknown');events=[];tg=TgData('/missing-recover.ini',backfill_store=store,health_callback=events.append)
    with offline(tg):
        count,snapshot=await g.seed_health(tg,g.SMALL,events)
        req,status=await reopen(tg,root,'unknown',report)
        assert status.attempt_id and status.pending_batch_id is None
        await refuse(BackfillRecoveryRequired,tg.prepare_backfill(ctx(status)))
        command=dict(attempt_id=status.attempt_id,command_id='exact-stopped-attempt',expected_control_revision=status.control_revision,previous_reader_stopped=True)
        g.save(root/'recovery-command.json',command);original=sqlite3.connect
        class Exit(sqlite3.Connection):
            def commit(self):
                hit=False
                if self.total_changes:
                    row=json.loads(self.execute('SELECT data FROM tgdata_sync_state').fetchone()[0])['current']
                    hit=row['last_recovery'] is not None
                super().commit()
                if hit:
                    assert len(events)==count and tg._health.snapshot()==snapshot
                    report['committed_pacing']=row['pacing'];report['local_health_preserved']=True
                    report_exit(root,'recovery-exit',report,82)
        def connect(*a,**kw):kw['factory']=Exit;return original(*a,**kw)
        with patch.object(sqlite3,'connect',side_effect=connect):
            await g.operation(report,'recover-actual-commit-before-reply',tg.recover_backfill(status.run,**command))


async def recovery_retry(root,report):
    events=[];tg=TgData('/missing-retry.ini',backfill_store=backend(root,'unknown'),health_callback=events.append)
    with offline(tg):
        count,snapshot=await g.seed_health(tg,g.SMALL,events);req,status=await reopen(tg,root,'unknown',report)
        command=g.read(root/'recovery-command.json');raw=await backend(root,'unknown').load(g.SMALL)
        result=await g.operation(report,'original-recovery-retry',tg.recover_backfill(status.run,**command))
        assert not result.applied and result.status==status
        assert _encode_date(status.pacing_not_before)==g.read(root/'recovery-exit-result.json')['committed_pacing']['not_before']
        early=await g.operation(report,'recovery-local-early-wait',tg.prepare_backfill(ctx(status)))
        if early.wait_seconds is None or early.wait_seconds<=0:raise Inconclusive('recovery restart missed early wait')
        assert await backend(root,'unknown').load(g.SMALL)==raw and len(events)==count and tg._health.snapshot()==snapshot
        report.update(final_status=status.to_dict(),early_wait=early.wait_seconds,local_health_preserved=True);await tg.close()


async def unknown_follow(root,report,tg,guard):
    req,status=await reopen(tg,root,'unknown',report,guard)
    turn=await wait_turn(tg,status,report,'recovered-source-wait',guard)
    if turn is None:turn=await g.operation(report,'recovered-real-source',tg.prepare_backfill(ctx(status)),guard)
    compare(turn.batch,[{k:v for k,v in g.read(root/'small-oracle.json')['photo'].items() if k in ('id','date')}])
    save_turn(root,'unknown-final',turn);receiver=g.Receiver(root/'unknown-receiver',create=True);receive(receiver,turn,report)
    done=await g.operation(report,'recovered-final-ack',tg.acknowledge_backfill(turn.delivery),guard)
    assert done.terminal_outcome=='completed' and done.after_id==14;report['final_status']=done.to_dict()


async def photo_source(root,report,tg,guard,budget):
    req,status=await new(tg,root,'photo',report,guard,photo=True,batch=1,media='download')
    media=root/'photo-media';media.mkdir()
    turn=await g.operation(report,'photo-real-download-full-batch',tg.prepare_backfill(ctx(status),download_media_to=media),guard)
    oracle=g.read(root/'small-oracle.json')['photo'];assert [r['id'] for r in turn.batch.messages]==[oracle['id']]
    blob=turn.batch.messages[0]['media']['blob'];assert blob['size']==oracle['size'] and blob['sha256']==oracle['sha256']
    assert turn.batch.stop_reason=='limit' and not turn.status.source_exhausted and turn.status.terminal_outcome is None
    save_turn(root,'photo',turn);report_exit(root,'photo-source',report,83,guard,budget)


async def photo_ack_exit(root,report):
    store=backend(root,'photo');events=[];tg=TgData('/missing-photo.ini',backfill_store=store,health_callback=events.append)
    with offline(tg):
        count,snapshot=await g.seed_health(tg,g.SMALL,events);req,status=await reopen(tg,root,'photo',report)
        media=root/'photo-media';expected=g.read(root/'photo-turn.json')
        turn=await g.operation(report,'photo-local-replay',tg.prepare_backfill(ctx(status),download_media_to=media))
        assert turn.replayed and turn.batch.to_dict()==expected['batch'];blob=turn.batch.messages[0]['media']['blob']
        copied=root/'photo-corrupt-copy';shutil.copytree(media,copied);(copied/blob['path']).write_bytes(b'INJECTED corrupt disposable copy')
        raw=await store.load(g.SMALL)
        await refuse(BackfillMediaError,g.operation(report,'photo-corrupt-copy-refusal',tg.prepare_backfill(ctx(status),download_media_to=copied)))
        assert await store.load(g.SMALL)==raw and len(events)==count and tg._health.snapshot()==snapshot
        receiver=g.Receiver(root/'photo-receiver',create=True);assert receive(receiver,turn,report,media)
        assert g.digest(receiver.media/blob['path'])==g.read(root/'small-oracle.json')['photo']['sha256']
        (media/blob['path']).unlink()
        await refuse(BackfillMediaError,g.operation(report,'photo-missing-source-refusal',tg.prepare_backfill(ctx(status),download_media_to=media)))
        original=sqlite3.connect
        class Exit(sqlite3.Connection):
            def commit(self):
                hit=False
                if self.total_changes:
                    row=json.loads(self.execute('SELECT data FROM tgdata_sync_state').fetchone()[0])['current']
                    hit=row['last_ack'] is not None and row['pending'] is None
                super().commit()
                if hit:
                    assert row['terminal_outcome'] is None and row['after_id']=='14'
                    assert len(events)==count and tg._health.snapshot()==snapshot
                    report['local_health_preserved']=True;report_exit(root,'photo-ack-exit',report,84)
        def connect(*a,**kw):kw['factory']=Exit;return original(*a,**kw)
        with patch.object(sqlite3,'connect',side_effect=connect):
            await g.operation(report,'photo-ack-actual-commit-before-reply',tg.acknowledge_backfill(turn.delivery))


async def photo_retry(root,report):
    events=[];tg=TgData('/missing-photo-retry.ini',backfill_store=backend(root,'photo'),health_callback=events.append)
    with offline(tg):
        count,snapshot=await g.seed_health(tg,g.SMALL,events);req,status=await reopen(tg,root,'photo',report)
        delivery=BackfillDeliveryRef.from_dict(g.read(root/'photo-turn.json')['delivery']);raw=await backend(root,'photo').load(g.SMALL)
        duplicate=await g.operation(report,'photo-duplicate-ack-without-source-bytes',tg.acknowledge_backfill(delivery))
        assert duplicate==status and status.after_id==14 and status.terminal_outcome is None and not status.source_exhausted
        assert await backend(root,'photo').load(g.SMALL)==raw and len(events)==count and tg._health.snapshot()==snapshot
        report.update(final_status=status.to_dict(),local_health_preserved=True);await tg.close()


async def photo_follow(root,report,tg,guard):
    req,status=await reopen(tg,root,'photo',report,guard);guard.block_after=0;media=root/'photo-media'
    # The first post-restart call may be early. It must supply the required root,
    # even though an admitted empty follow-up will not download another blob.
    remaining=max(0,(status.pacing_not_before-_decode_date(g.stamp()['utc'])).total_seconds())
    if remaining:await asyncio.sleep(remaining+0.03)
    await refuse(g.p.ProbeStop,g.operation(report,'photo-follow-INJECTED-local-refusal',tg.prepare_backfill(ctx(status),download_media_to=media),guard))
    failed=await tg.get_backfill_status(status.run)
    assert failed.after_id==14 and not failed.source_exhausted and failed.terminal_outcome is None and failed.pending_batch_id is None
    g.save(root/'photo-failed-status.json',failed.to_dict());guard.block_after=None
    early=await g.operation(report,'photo-failed-early-wait',tg.prepare_backfill(ctx(failed),download_media_to=media),guard)
    assert early.wait_seconds>0 and early.batch is None
    await asyncio.sleep(early.wait_seconds+0.03)
    final=await g.operation(report,'photo-real-empty-end',tg.prepare_backfill(ctx(failed),download_media_to=media),guard)
    assert final.batch is None and final.status.source_exhausted and final.status.terminal_outcome=='completed'
    assert g.Receiver(root/'photo-receiver').summary()['receipts']==1
    report.update(final_status=final.status.to_dict(),failure_then_wait=early.wait_seconds)


async def worker(root,name):
    report=dict(result='UNFINISHED',worker=name,revision=g.revision(),started=g.stamp(),pid=os.getpid());tg=guard=budget=None
    try:
        if name in ALLOCATIONS:
            case={'main-seed':'main','main-continue':'main','unknown-source':'unknown','unknown-follow':'unknown',
                'photo-source':'photo','photo-follow':'photo'}.get(name,name)
            create=name not in ('main-continue','unknown-follow','photo-follow')
            store=None if name=='qualify' else backend(root,case,create=create)
            daily=backend(root,'daily',create=True) if name=='main-continue' else None
            chat=g.LARGE if name in ('qualify','main-seed','main-continue','prefix') else g.SMALL
            events=[]
            tg,client,guard,budget,before=await g.source(root,name,chat,backfill_store=store,sync_store=daily,
                media=name.startswith('photo-'),events=events)
            tg._gate_d_events=events
            report['budget_before']=dict(limit=before.limit,used=before.used,reserved=before.reserved)
            if name=='qualify':await qualify(root,report,tg,client,guard)
            elif name=='main-seed':await main_seed(root,report,tg,guard,budget)
            elif name=='main-continue':await main_continue(root,report,tg,guard)
            elif name=='controls':await controls(root,report,tg,guard)
            elif name=='prefix':await prefix(root,report,tg,guard,budget)
            elif name=='unknown-source':await unknown_source(root,report,tg,guard,budget)
            elif name=='unknown-follow':await unknown_follow(root,report,tg,guard)
            elif name=='photo-source':await photo_source(root,report,tg,guard,budget)
            elif name=='photo-follow':await photo_follow(root,report,tg,guard)
        else:
            await {'main-local':main_local,'recovery-exit':recovery_exit,'recovery-retry':recovery_retry,
                'photo-ack-exit':photo_ack_exit,'photo-retry':photo_retry}[name](root,report)
        report['result']='PASS'
    except BaseException as error:
        report.update(result='INCONCLUSIVE' if isinstance(error,Inconclusive) else 'STOPPED',**g.safe_error(error));raise
    finally:
        if tg:await tg.close()
        if guard:report.update(guard.report())
        if budget:
            after=budget.status(g.account());report['budget_after']=dict(limit=after.limit,used=after.used,reserved=after.reserved)
        report['finished']=g.stamp();g.save(root/(name+'-result.json'),report)
        print(json.dumps({k:v for k,v in report.items() if k in ('result','worker','error_type','frames','budget_before','budget_after','sent_requested_slots','attempted_slots')},sort_keys=True),flush=True)


def run(root):
    assert g.read(root/'prebuild-result.json')['result']=='PASS'
    sequence=[('qualify',0),('main-seed',73),('main-local',0),('main-continue',0),('controls',0),('prefix',0),
        ('unknown-source',81),('recovery-exit',82),('recovery-retry',0),('unknown-follow',0),
        ('photo-source',83),('photo-ack-exit',84),('photo-retry',0),('photo-follow',0)]
    previous_source_end=None;observations=[]
    for name,expected in sequence:
        if name in ALLOCATIONS:
            if previous_source_end is not None:time.sleep(max(0,5-(time.monotonic()-previous_source_end)))
            g.allocate(root,name,ALLOCATIONS[name])
        args=[sys.executable,str(Path(__file__).resolve()),'--worker',name,'--root',str(root)]
        start=g.stamp()
        with (root/(name+'.worker.log')).open('x') as log:
            process=subprocess.Popen(args,cwd=str(g.CONFIG.parent),stdout=log,stderr=subprocess.STDOUT)
            try:code=process.wait(timeout=195)
            except subprocess.TimeoutExpired:
                process.kill();process.wait();code=124
        end=g.stamp();row=dict(worker=name,pid=process.pid,code=code,expected=expected,entry=start,end=end,
            monotonic_order_qualified=end['monotonic_ns']>=start['monotonic_ns'])
        observations.append(row);g.append(root/'owned-workers.jsonl',row)
        if name in ALLOCATIONS:previous_source_end=time.monotonic()
        print(json.dumps(row),flush=True)
        if code!=expected:raise RuntimeError('worker did not reach expected result; inspect private report '+name)
        report=g.read(root/(name+'-result.json'))
        assert report['result']==('PASS' if code==0 else 'EXPECTED_OWNED_EXIT')
        assert start['monotonic_ns']<=report['started']['monotonic_ns']<=end['monotonic_ns']
    g.save(root/'driver-result.json',dict(result='EXECUTION_COMPLETE_AUDIT_PENDING',revision=g.revision(),workers=observations,finished=g.stamp()))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    parser.add_argument('--worker',choices=list(ALLOCATIONS)+['main-local','recovery-exit','recovery-retry','photo-ack-exit','photo-retry'])
    parser.add_argument('--root',type=Path,default=g.ROOT);args=parser.parse_args();logging.disable(logging.CRITICAL)
    try:
        if args.worker:asyncio.run(asyncio.wait_for(worker(args.root,args.worker),180))
        elif args.run:run(args.root)
        else:parser.print_help()
    except BaseException as error:
        print(json.dumps(g.safe_error(error)),flush=True);raise SystemExit(1)
