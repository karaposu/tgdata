"""Issue #19 Gate B audit driver, pinned to the authorized test setup.

Private artifacts only. Default --help is offline. --run creates a new private root;
workers run sequentially, source requests use Gate A's unchanged read-only guard.
"""
import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
sys.path.insert(0,str(REPO))
spec=importlib.util.spec_from_file_location('stage4_prebuild',HERE/'prebuild_probe.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
p=base.p
from telethon import functions,types,utils
from tgdata import TgData,ReadBudget,SQLiteSyncStore,MessageBatch
from tgdata.backfill import (BackfillStartRequest,BackfillPrepareContext,BackfillDeliveryRef,
    BackfillConflictError,BackfillConfigurationError,BackfillUnknownRun,BackfillUnknownReceipt,
    BackfillRecoveryRequired,BackfillMediaError)
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill_state import _BackfillState
from tgdata.history_window import _decode_date,_encode_date

OLD=base.OLD
PRE=Path('/private/tmp/tgdata19-gate-b-live-20261007-prebuild')
SMALL=base.CHAT
LARGE=-1001139574198
CODE='b1f6495'


def save(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def read(path):return json.loads(path.read_text())
def sha(text):return hashlib.sha256(text.encode()).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)


def selected_account():return int(read(OLD/'login-status.json')['verified_account_id'])


def snapshot(path,chat):
    with sqlite3.connect(str(path)) as db:
        raw=db.execute('SELECT data FROM tgdata_sync_state WHERE chat_id=?',(chat,)).fetchone()[0]
    state=_BackfillState.from_json(raw,json.loads(raw)['collection_id'],chat)
    row=state.to_dict()['current']
    return dict(status=state.status().to_dict(),state_sha256=sha(raw),
                pending_sha256=sha(MessageBatch(row['pending']).to_json()) if row['pending'] else None)


def receiver_view(root,chat):
    with sqlite3.connect(str(root/'receiver.sqlite3')) as db:
        rows=db.execute('SELECT id,payload FROM messages WHERE chat=?',(str(chat),)).fetchall()
        return dict(ids=sorted((row[0] for row in rows),key=int),
                    dates={row[0]:json.loads(row[1])['date'] for row in rows},
                    receipts=db.execute('SELECT count(*) FROM receipts').fetchone()[0])


async def refusal(kind,call):
    try:await call
    except kind:return
    raise AssertionError('expected '+kind.__name__)


async def local_engine(root,case):
    req=BackfillStartRequest.from_dict(case['request'])
    store=SQLiteSyncStore(root/case['state'],create=False)
    eng=BackfillEngine(store,req.collection_id,clock=p.forbidden_clock)
    status=(await eng.start(req,submission='retry')).status
    return req,store,eng,status


async def local_worker(root,name,action):
    case=read(root/(name+'.case.json'))
    req,store,eng,status=await local_engine(root,case)
    media=root/case['media'] if req.media_mode=='download' else None
    target=root/case['receiver'];target.mkdir(exist_ok=True)
    report=dict(case=name,action=action,evidence='INJECTED actual live-data/store/receiver; offline process',
                pid=os.getpid(),code_revision=CODE,history_requests=0,requested_slots=0)
    before=await store.load(req.chat_id)
    ctx=BackfillPrepareContext.from_status(status)
    if action=='recovery_check':
        assert status.attempt_id and not status.source_exhausted and status.terminal_outcome is None
        await refusal(BackfillRecoveryRequired,eng.prepare(ctx,download_media_to=media))
        assert await store.load(req.chat_id)==before
    elif action=='complete_check':
        assert status.terminal_outcome=='completed' and status.pending_batch_id is None
        assert (await eng.prepare(ctx,download_media_to=media)).status==status
        assert await store.load(req.chat_id)==before
    else:
        row=json.loads(before)['current'];assert row['pending'] is not None
        delivery=BackfillDeliveryRef(status.run,status.destination_id,row['pending']['batch_id'])
        if action in ('ack_before','ack_after'):
            original=sqlite3.connect
            class Crash(sqlite3.Connection):
                def commit(self):
                    hit=False;candidate=None
                    if self.total_changes:
                        row=self.execute('SELECT data FROM tgdata_sync_state').fetchone()
                        if row:
                            candidate=json.loads(row[0]);hit=candidate['current']['last_ack'] is not None
                    if hit and action=='ack_before':
                        report.update(boundary='before actual final ack commit',candidate_status=_BackfillState(candidate).status().to_dict())
                        save(root/(name+'.'+action+'.json'),report);os._exit(71)
                    super().commit()
                    if hit and action=='ack_after':
                        report.update(boundary='after actual final ack commit',candidate_status=_BackfillState(candidate).status().to_dict())
                        save(root/(name+'.'+action+'.json'),report);os._exit(72)
            def connect(*a,**kw):kw['factory']=Crash;return original(*a,**kw)
            with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
                await BackfillEngine(store,req.collection_id).acknowledge(delivery)
            raise AssertionError('ack commit boundary not reached')
        turn=await eng.prepare(ctx,download_media_to=media)
        assert turn.replayed and turn.batch.to_json()==MessageBatch(row['pending']).to_json()
        report['pending_sha256']=sha(turn.batch.to_json())
        if action=='receiver_crash':
            report.update(receiver=base.accept(target,turn,media),boundary='after actual receiver transaction commit, before ack')
            save(root/(name+'.'+action+'.json'),report);os._exit(74)
        if action=='replay_checks':
            report['receiver_before']=receiver_view(target,req.chat_id)
            base.accept(target,turn,media)
            report['receiver_after']=receiver_view(target,req.chat_id)
            assert report['receiver_before']==report['receiver_after']
            for changed,kind in (
                (replace(delivery,run=replace(delivery.run,generation=delivery.run.generation+1)),BackfillUnknownRun),
                (replace(delivery,destination_id='different'),BackfillConflictError),
                (replace(delivery,run=replace(delivery.run,collection_id='different')),BackfillConfigurationError)):
                await refusal(kind,eng.acknowledge(changed))
            if media:
                relocated=root/(name+'-relocated');shutil.copytree(media,relocated)
                assert (await eng.prepare(ctx,download_media_to=relocated)).batch.to_json()==turn.batch.to_json()
                blob=turn.batch.messages[0]['media']['blob'];file=relocated/blob['path']
                file.write_bytes(b'x'*blob['size'])
                await refusal(BackfillMediaError,eng.prepare(ctx,download_media_to=relocated))
                file.unlink()
                await refusal(BackfillMediaError,eng.prepare(ctx,download_media_to=relocated))
                # Receiver owns the verified bytes; final ack must survive loss of all source copies.
                shutil.rmtree(media);shutil.rmtree(relocated)
                assert base.digest(target/'receiver-media'/blob['path'])==blob['sha256']
            assert await store.load(req.chat_id)==before
        else:raise AssertionError('unknown local action')
    report.update(after=snapshot(root/case['state'],req.chat_id),result='PASS')
    save(root/(name+'.'+action+'.json'),report)


async def connection(chat,limits,allow_media=False):
    account=selected_account();budget=ReadBudget(OLD/'account-read-budget.sqlite3')
    policy=budget.status(account);assert policy.limit==5000 and policy.remaining>0
    guard=p.ReadOnlyGuard(chat,limits,allow_media)
    tg=TgData(str(base.CONFIG),connection_pool_size=1,interactive_login=False,read_budget=budget)
    factory=tg.connection_engine._new_client
    def instrumented(*a,**kw):
        client=factory(*a,**kw);guard.instrument(client)
        client.flood_sleep_threshold=0;client._request_retries=0;client._connection_retries=1
        return client
    tg.connection_engine._new_client=instrumented
    return tg,guard,budget,account


async def qualify(root,name,remaining):
    large=name=='large_oracle'
    chat=LARGE if large else SMALL
    old=read(OLD/'real_sdk_pages.manifest.json') if large else read(PRE/'small-oracle.json')
    start=_decode_date(old['window']['start_date']) if large else None
    end=_decode_date(old['window']['end_date']) if large else None
    limits=dict(max_rpc_requests=80,max_history_requests=5 if large else 2,
                max_requested_slots=min(500 if large else 200,remaining),max_media_bytes=0)
    tg,guard,budget,account=await connection(chat,limits)
    report=dict(kind='independent direct descending GetHistory, not batch reader',
                code_revision=CODE,chat_id=str(chat),messages=[],budget_used_before=budget.status(account).used)
    try:
        client=await tg.connection_engine.get_client();assert (await client.get_me(input_peer=False)).id==account
        peer=await client.get_input_entity(chat);offset=0;seen=set();complete=False
        for page in range(limits['max_history_requests']):
            answer=await client(functions.messages.GetHistoryRequest(peer,offset,end if not offset else None,0,100,0,0,0),flood_sleep_threshold=0)
            msgs=answer.messages
            if not msgs:complete=True;report['boundary']='explicit empty reply';break
            assert all(isinstance(m,(types.Message,types.MessageService)) and utils.get_peer_id(m.peer_id)==chat for m in msgs)
            for message in msgs:
                assert message.id not in seen;seen.add(message.id)
                report['messages'].append(dict(id=str(message.id),date=_encode_date(message.date)))
            next_offset=min(m.id for m in msgs);assert not offset or next_offset<offset;offset=next_offset
            if large and min(m.date for m in msgs)<start:
                complete=True;report['boundary']='observed older-than-start witness';break
            await asyncio.sleep(5)
        assert complete
        rows=sorted(report['messages'],key=lambda r:int(r['id']))
        assert all(_decode_date(a['date'])<=_decode_date(b['date']) for a,b in zip(rows,rows[1:]))
        selected=[r for r in rows if not large or start<=_decode_date(r['date'])<end]
        expected=old['oracle']['messages'] if large else old['messages']
        expected=[dict(id=r['id'],date=r['date']) for r in expected]
        assert selected==expected,'source fixture drift'
        report.update(selected=selected,expected_sha256=sha(canonical(expected)),complete=True,
                      captured_at=_encode_date(datetime.now(timezone.utc)),result='PASS')
    finally:
        await asyncio.wait_for(tg.close(),10)
        report.update(rpc=guard.rpc,requested_slots=guard.slots,budget_used_after=budget.status(account).used)
        save(root/(name+'.json'),report)


async def live_worker(root,name,action,remaining):
    case=read(root/(name+'.case.json'));req=BackfillStartRequest.from_dict(case['request'])
    store=SQLiteSyncStore(root/case['state'],create=False)
    limits=dict(max_rpc_requests=100,max_history_requests=12,
                max_requested_slots=min(1000,remaining),max_media_bytes=4*1024*1024 if req.media_mode=='download' else 0)
    tg,guard,budget,account=await connection(req.chat_id,limits,req.media_mode=='download')
    eng=BackfillEngine(store,req.collection_id,read_batch=tg.get_message_batch)
    media=root/case['media'] if req.media_mode=='download' else None
    target=root/case['receiver'];target.mkdir(exist_ok=True)
    report=dict(case=name,action=action,evidence='LIVE with named INJECTED local boundaries',
                code_revision=CODE,pid=os.getpid(),turns=[],budget_used_before=budget.status(account).used)
    def emit_exit(code,boundary,candidate=None):
        report.update(boundary=boundary,rpc=guard.rpc,requested_slots=guard.slots,
            requested_media_bytes=guard.media_bytes,budget_used_after=budget.status(account).used)
        if candidate:
            row=candidate['current'];report['candidate_status']=_BackfillState(candidate).status().to_dict()
            report['pending_sha256']=sha(MessageBatch(row['pending']).to_json()) if row['pending'] else None
        save(root/(name+'.'+action+'.json'),report);os._exit(code)
    try:
        client=await tg.connection_engine.get_client();assert (await client.get_me(input_peer=False)).id==account
        report['account_verified']=True
        original_call=client._call
        if action=='source_crash':
            async def crash_answer(sender,request,ordered=False,flood_sleep_threshold=None):
                result=await original_call(sender,request,ordered=ordered,flood_sleep_threshold=flood_sleep_threshold)
                raw=request
                while isinstance(raw,p._WRAPPERS):raw=raw.query
                if isinstance(raw,functions.messages.GetHistoryRequest):
                    emit_exit(76,'after actual history answer, before raw-reader delivery')
                return result
            client._call=crash_answer
        if action=='prefix':guard.limits['max_history_requests']=1
        original_connect=sqlite3.connect
        class Crash(sqlite3.Connection):
            def commit(self):
                candidate=None;hit=False
                if (self.total_changes and action in ('publish_crash','empty_before','empty_after')
                        and self.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='tgdata_sync_state'").fetchone()):
                    row=self.execute('SELECT data FROM tgdata_sync_state').fetchone()
                    if row:
                        candidate=json.loads(row[0]);current=candidate['current']
                        hit=(current['pending'] is not None if action=='publish_crash' else
                             current['terminal_outcome']=='completed' if action in ('empty_before','empty_after') else False)
                if hit and action=='empty_before':emit_exit(71,'before actual empty completion commit',candidate)
                super().commit()
                if hit:emit_exit(73 if action=='publish_crash' else 72,'after actual '+('pending publication' if action=='publish_crash' else 'empty completion')+' commit',candidate)
        def connect(*a,**kw):kw['factory']=Crash;return original_connect(*a,**kw)
        accepted=[];latest=None;older=None;wrong_checks=0
        with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
            for iteration in range(12):
                status=(await eng.start(req,submission='retry')).status
                ctx=BackfillPrepareContext.from_status(status);guard.turn+=1
                await asyncio.sleep(5)
                try:turn=await eng.prepare(ctx,download_media_to=media)
                except p.ProbeStop as error:
                    assert action in ('prefix','refuse_followup') and str(error)=='history_cap_reached'
                    status=await eng.status(status.run)
                    assert not status.source_exhausted and status.terminal_outcome is None and status.attempt_id is None
                    if action=='prefix':
                        assert status.pending_message_count==100
                        replay=await BackfillEngine(store,req.collection_id,clock=p.forbidden_clock).prepare(ctx)
                        assert replay.batch.stop_reason=='interrupted'
                        assert [r['id'] for r in replay.batch.messages]==[r['id'] for r in case['expected'][:100]]
                        base.accept(target,replay,None)
                        status=await eng.acknowledge(replay.delivery)
                        report['prefix_ids']=[r['id'] for r in replay.batch.messages]
                    else:
                        assert status.pending_batch_id is None and accepted==[r['id'] for r in case['expected']]
                    report.update(refusal='injected guard refusal before second history send',
                                  status=status.to_dict(),accepted_ids=accepted,result='PASS')
                    break
                if action in ('prefix','source_crash','publish_crash','empty_before','empty_after'):
                    raise AssertionError('expected controlled boundary was not reached')
                obs=dict(status=turn.status.to_dict(),stop_reason=turn.batch.stop_reason if turn.batch else 'empty-end',
                         pending_sha256=sha(turn.batch.to_json()) if turn.batch else None)
                report['turns'].append(obs)
                if turn.batch:
                    assert turn.status.terminal_outcome is None
                    ids=[r['id'] for r in turn.batch.messages]
                    wanted=case['expected'][len(accepted):len(accepted)+len(ids)]
                    assert [dict(id=r['id'],date=r['date']) for r in turn.batch.messages]==[dict(id=r['id'],date=r['date']) for r in wanted]
                    accepted.extend(ids)
                    raw=await store.load(req.chat_id)
                    if latest:
                        repeated=await eng.acknowledge(latest)
                        assert repeated.pending_batch_id==turn.batch.batch_id and await store.load(req.chat_id)==raw
                    if older:
                        await refusal(BackfillUnknownReceipt,eng.acknowledge(older));assert await store.load(req.chat_id)==raw
                    await refusal(BackfillUnknownRun,eng.acknowledge(replace(turn.delivery,run=replace(turn.delivery.run,generation=2))))
                    assert await store.load(req.chat_id)==raw;wrong_checks+=1
                    if action=='refuse_followup':
                        other=read(root/'exact_full.scan.json')['first_delivery']
                        foreign=BackfillDeliveryRef.from_dict(other)
                        assert foreign.batch_id==turn.delivery.batch_id
                        await refusal(BackfillConfigurationError,eng.acknowledge(foreign))
                        assert await store.load(req.chat_id)==raw
                        report['equal_hash_wrong_context_refused']=True
                    base.accept(target,turn,media)
                    if latest is not None:older=latest
                    latest=turn.delivery
                    report.setdefault('first_delivery',latest.to_dict())
                    after=await eng.acknowledge(latest)
                    reads=guard.history_count
                    await refusal(BackfillConflictError,eng.prepare(ctx,download_media_to=media))
                    assert guard.history_count==reads
                    if turn.batch.stop_reason=='limit':assert not after.source_exhausted and after.terminal_outcome is None
                else:after=turn.status
                if after.terminal_outcome=='completed':
                    assert accepted==[r['id'] for r in case['expected']]
                    raw=await store.load(req.chat_id)
                    local=BackfillEngine(store,req.collection_id,clock=p.forbidden_clock)
                    assert (await local.prepare(BackfillPrepareContext.from_status(after),download_media_to=media)).status==after
                    if latest:assert await local.acknowledge(latest)==after
                    assert await store.load(req.chat_id)==raw
                    report.update(result='PASS',accepted_ids=accepted,status=after.to_dict(),wrong_receipt_checks=wrong_checks)
                    break
                if action=='refuse_followup':guard.limits['max_history_requests']=guard.history_count
            else:raise AssertionError('turn cap reached')
        report['after']=snapshot(root/case['state'],req.chat_id)
    finally:
        await asyncio.wait_for(tg.close(),10)
        report.update(rpc=guard.rpc,requested_slots=guard.slots,requested_media_bytes=guard.media_bytes,
                      history_requests=guard.history_count,budget_used_after=budget.status(account).used)
        save(root/(name+'.'+action+'.json'),report)


async def initialize_case(root,name,chat,expected,start,end,*,batch=17,after=0,download=False,receiver='reference-receiver'):
    request=BackfillStartRequest('gate-b-'+name,chat,'run-1',receiver,0,None,
        origin='imported' if after else 'fresh',after_id=after,batch_size=batch,
        start_date=start,end_date=end,media_mode='download' if download else 'references')
    case=dict(request=request.to_dict(),state=name+'.sqlite3',media=name+'-media',receiver=receiver,expected=expected)
    save(root/(name+'.case.json'),case)  # identity/oracle durable before first submission
    await BackfillEngine(SQLiteSyncStore(root/case['state']),request.collection_id).start(request,submission='new')


async def run(root):
    root.mkdir(mode=0o700,exist_ok=False)
    assert p.telethon.__version__=='1.45.0'
    summary=dict(code_revision=CODE,telethon=p.telethon.__version__,python=sys.version.split()[0],
                 results=[],gate_verdict='UNFINISHED',requested_slots=int(read(PRE/'prebuild-results.json')['requested_slots']))
    budget=ReadBudget(OLD/'account-read-budget.sqlite3');account=selected_account()
    summary['budget_used_before']=budget.status(account).used
    assert budget.status(account).limit==5000
    async def child(name,action,expected=0,live=False):
        remaining=1500-summary['requested_slots'];assert remaining>0
        args=[sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--case',name,
              '--action',action,'--remaining',str(remaining)]
        with (root/(name+'.'+action+'.log')).open('x') as log:
            proc=await asyncio.to_thread(subprocess.run,args,stdout=log,stderr=subprocess.STDOUT,timeout=200)
        path=root/(name+'.json' if action=='qualify' else name+'.'+action+'.json')
        if path.exists():
            report=read(path);summary['requested_slots']+=report.get('requested_slots',0)
        else:report={}
        summary['results'].append(dict(case=name,action=action,exit_code=proc.returncode,
            expected_exit=expected,report=path.name,requested_slots=report.get('requested_slots',0)))
        assert proc.returncode==expected,(name,action,'worker exit mismatch; see private log')
        if expected==0:assert report.get('result')=='PASS'
        assert summary['requested_slots']<=1500
        print(json.dumps(dict(case=name,action=action,exit_code=proc.returncode,
                              requested_slots_total=summary['requested_slots'])),flush=True)
        if live:await asyncio.sleep(5)
        return report
    try:
        # Prebuild independently requalified the small source and photo immediately
        # before this product change. Freeze that oracle here before any Gate B scan.
        small=read(PRE/'small-oracle.json');save(root/'small-oracle.json',small)
        rows=small['messages'];start=_decode_date(rows[0]['date']);end=_decode_date(rows[-1]['date'])+timedelta(microseconds=1)
        await child('large_oracle','qualify',live=True)
        large=read(root/'large_oracle.json')['selected'];old=read(OLD/'real_sdk_pages.manifest.json')
        await initialize_case(root,'small_complete',SMALL,rows,start,end,batch=17)
        await child('small_complete','scan',live=True)
        tail=[r for r in rows if int(r['id'])>13]
        await initialize_case(root,'overlap_imported',SMALL,tail,start,end,batch=20,after=13)
        await child('overlap_imported','scan',live=True)
        view=receiver_view(root/'reference-receiver',SMALL)
        assert view['ids']==[r['id'] for r in rows] and view['dates']=={r['id']:r['date'] for r in rows}
        summary['overlap_receiver']=view
        exact=read(OLD/'exact_full_followup.manifest.json')
        exstart=_decode_date(exact['window']['start_date']);exend=_decode_date(exact['window']['end_date'])
        expected=[r for r in rows if exstart<=_decode_date(r['date'])<exend]
        assert [r['id'] for r in expected]==[r['id'] for r in exact['oracle']['messages']] and len(expected)==9
        for name,action in (('exact_full','scan'),('full_then_refused','refuse_followup')):
            await initialize_case(root,name,SMALL,expected,exstart,exend,batch=9)
            await child(name,action,live=True)
        photo=next(r for r in rows if r['id']=='14');ps=_decode_date(photo['date']);pe=ps+timedelta(microseconds=1)
        await initialize_case(root,'photo_crashes',SMALL,[photo],ps,pe,batch=2,after=13,download=True,receiver='photo-receiver')
        pub=await child('photo_crashes','publish_crash',73,live=True)
        received=await child('photo_crashes','receiver_crash',74)
        replay=await child('photo_crashes','replay_checks')
        assert pub['pending_sha256']==received['pending_sha256']==replay['pending_sha256']
        await child('photo_crashes','ack_before',71)
        owed=snapshot(root/'photo_crashes.sqlite3',SMALL)
        assert owed['status']['pending_message_count']==1 and owed['status']['terminal_outcome'] is None
        await child('photo_crashes','ack_after',72)
        await child('photo_crashes','complete_check')
        summary['photo_receiver']=receiver_view(root/'photo-receiver',SMALL)
        blob=small['selected_photo']
        files=list((root/'photo-receiver'/'receiver-media').iterdir())
        assert len(files)==1 and base.digest(files[0])==blob['sha256'] and files[0].stat().st_size==blob['size']
        summary['selected_blob']={k:blob[k] for k in ('id','sha256','size')}
        # Empty interval strictly after the independently enumerated latest message,
        # still historical. Separate records preserve the unresolved before-commit case.
        es=end+timedelta(seconds=1);ee=es+timedelta(seconds=1)
        for name,action,code in (('empty_uncommitted','empty_before',71),('empty_committed','empty_after',72)):
            await initialize_case(root,name,SMALL,[],es,ee,batch=2)
            await child(name,action,code,live=True)
            await child(name,'recovery_check' if action=='empty_before' else 'complete_check')
        await initialize_case(root,'unknown_source',SMALL,expected,exstart,exend,batch=5)
        await child('unknown_source','source_crash',76,live=True)
        await child('unknown_source','recovery_check')
        ls=_decode_date(old['window']['start_date']);le=_decode_date(old['window']['end_date'])
        await initialize_case(root,'sdk_pages',LARGE,large,ls,le,batch=120)
        pages=await child('sdk_pages','scan',live=True)
        assert len(pages['accepted_ids'])==350
        assert any(r.get('page') and r['page'][1]>1 for r in pages['rpc'])
        await initialize_case(root,'saved_prefix',LARGE,large,ls,le,batch=101)
        await child('saved_prefix','prefix',live=True)
        summary['large_receiver']=receiver_view(root/'reference-receiver',LARGE)
        assert summary['large_receiver']['ids']==[r['id'] for r in large]
        await child('small_postcheck','qualify',live=True)
        summary['gate_verdict']='PASS'
    finally:
        summary['budget_used_after']=budget.status(account).used
        save(root/'summary.json',summary)
        print(json.dumps({k:v for k,v in summary.items() if k not in ('results','overlap_receiver','large_receiver')},sort_keys=True))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--run',action='store_true')
    parser.add_argument('--case');parser.add_argument('--action');parser.add_argument('--remaining',type=int)
    args=parser.parse_args();os.umask(0o077);os.chdir(base.CONFIG.parent);logging.disable(logging.CRITICAL)
    try:
        if args.run:asyncio.run(run(args.root))
        elif args.action=='qualify':asyncio.run(asyncio.wait_for(qualify(args.root,args.case,args.remaining),180))
        elif args.action in ('scan','prefix','refuse_followup','source_crash','publish_crash','empty_before','empty_after'):
            asyncio.run(asyncio.wait_for(live_worker(args.root,args.case,args.action,args.remaining),180))
        else:
            with patch.object(socket.socket,'connect',side_effect=AssertionError('offline worker')), \
                 patch.object(socket.socket,'connect_ex',side_effect=AssertionError('offline worker')), \
                 patch.object(base,'TgData',side_effect=AssertionError('offline worker cannot construct client')):
                asyncio.run(local_worker(args.root,args.case,args.action))
    except Exception as error:
        import traceback
        print(json.dumps(dict(error_type=type(error).__name__,frames=[dict(file=Path(f.filename).name,
            function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)])),flush=True)
        return 2
    return 0


if __name__=='__main__':sys.exit(main())
