"""Stage 6 falsifier: real current engine, codec, SDK and two real ledgers.

Default --help is offline. --checks blocks sockets. --live uses the approved setup,
an existing parent allocation, and the original 5,000/day ledger unchanged.
"""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import socket
import tempfile
import traceback
from unittest.mock import patch

import gate_support as g
from telethon import functions, types, utils
from tgdata import ReadBudget, ReadBudgetExceeded, ReadBudgetError, SQLiteSyncStore
from tgdata.backfill import BackfillStartRequest, BackfillPrepareContext, BackfillStateError
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill_state import _BackfillState
from tgdata.history_window import _encode_date


async def checks():
    from tgdata.smoke_tests import test_18_read_budget as f
    from tgdata.smoke_tests import test_25_backfill_delivery as d
    from tgdata.smoke_tests import test_27_backfill_pacing as q
    count = 0
    with tempfile.TemporaryDirectory(prefix='stage6_prebuild_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        f.TMP = d.TMP = Path(tmp)
        try:
            for limits in ((3,10),(10,3)):
                primary,_ = f.ledger(limits[0]); test,_ = f.ledger(limits[1])
                budget = g.RestrictiveBudget(primary,test)
                tg,client,sender = f.instance(budget)
                assert budget.status(f.ACCOUNT).remaining == 3
                result = await client(f.history(3))
                assert len(result.messages)==3 and len(sender.reads)==1
                assert primary.status(f.ACCOUNT).used==test.status(f.ACCOUNT).used==3
                await f.expect(ReadBudgetExceeded, client(f.history(1)))
                assert len(sender.reads)==1
                count += 1
            primary,_=f.ledger(10); test,_=f.ledger(0)
            tg,client,sender=f.instance(g.RestrictiveBudget(primary,test))
            await f.expect(ReadBudgetExceeded,client(f.history(2)))
            assert not sender.reads and primary.status(f.ACCOUNT).reserved==2
            count += 1
            primary,_=f.ledger(10); test,_=f.ledger(10)
            tg,client,sender=f.instance(g.RestrictiveBudget(primary,test))
            sender.script=[f.response([f.message(1),f.message(2)])]
            await f.expect(ReadBudgetError,client(f.history(1)))
            assert primary.status(f.ACCOUNT).used==test.status(f.ACCOUNT).used==2
            count += 1
            primary,_=f.ledger(10); test,_=f.ledger(10)
            budget=g.RestrictiveBudget(primary,test); claim=budget._reserve(f.ACCOUNT,3)
            with patch.object(test,'_settle',side_effect=OSError('injected')):
                f.rejected(OSError,lambda:budget._settle(claim,1))
            assert primary.status(f.ACCOUNT).used==1 and test.status(f.ACCOUNT).reserved==3
            count += 1
            # Actual codec candidates, deliberately not a replacement control API.
            initial=await d.setup(); pending,turn=await d.prepared()
            final=await d.setup();final[4].script=[d.finite_response([f.message(101)])]
            await final[1].prepare(final[-1])
            unknown=await q.unknown(pause=5)
            snapshots=[json.loads(await x.load(d.CHAT)) for x in (initial[0],pending[0],final[0],unknown.store)]
            for base in snapshots:
                for action in ('pause','resume','cancel','abandon'):
                    value=json.loads(json.dumps(base));row=value['current']
                    old=int(row['control_revision']);rev=int(value['state_revision'])+1
                    row['control_revision']=str(old+1);value['state_revision']=str(rev)
                    row['last_control']=dict(command_id='probe',action=action,expected_revision=str(old),
                        accepted_revision=str(old+1),state_revision=str(rev))
                    row['operator_intent']={'pause':'paused','resume':'active','cancel':'cancelled','abandon':'abandoned'}[action]
                    if action in ('cancel','abandon'):row['terminal_outcome']=row['operator_intent']
                    if action=='abandon':
                        p=row['pending'];row['pending']=None
                        row['abandoned']=dict(batch_id=p['batch_id'] if p else None,
                            next_after_id=p['next_after_id'] if p else row['after_id'],observed_at=_encode_date(d.NOW))
                    if action=='abandon' and row['attempt'] is not None:
                        f.rejected(BackfillStateError,lambda:_BackfillState(value));continue
                    state=_BackfillState(value);store=d.store()
                    assert await store.compare_and_swap(d.CHAT,None,state.to_json())
                    assert _BackfillState.from_json(await store.load(d.CHAT),d.COLLECTION,d.CHAT).to_json()==state.to_json()
                    if action=='abandon':
                        value['current']['terminal_outcome']='cancelled';value['current']['operator_intent']='cancelled'
                        _BackfillState(value)
            count += 1
            # Single-parent launch accounting: no uncertain allocation is reclaimed.
            allocations=Path(tmp)/'allocations';g.allocate(allocations,'one',700)
            f.rejected(AssertionError,lambda:g.allocate(allocations,'two',301))
            g.allocate(allocations,'two',300)
            f.rejected(AssertionError,lambda:g.allocate(allocations,'one',1))
            count += 1
        finally:
            for client in f.CLIENTS:await client.disconnect()
            f.CLIENTS.clear()
    print('Passed: {}/{} prebuild instrument/codec checks'.format(count,count))


async def live(root):
    assert g.p.telethon.__version__=='1.45.0'
    report=dict(result='UNFINISHED',code_revision='5382f78; unchanged Stage 5 product',checks=[])
    primary=ReadBudget(g.base.OLD/'account-read-budget.sqlite3');ident=g.account()
    before=primary.status(ident);assert before.limit==5000 and before.remaining>=250
    report['budget_before']=dict(limit=before.limit,used=before.used)
    tg=guard=None
    try:
        tg,client,guard=await g.source(root,'prebuild',primary)
        peer=await client.get_input_entity(g.CHAT)
        messages=[];offset=0
        for _ in range(2):
            reply=await client(functions.messages.GetHistoryRequest(peer,offset,None,0,100,0,0,0),flood_sleep_threshold=0)
            if not reply.messages:break
            assert all(isinstance(m,(types.Message,types.MessageService)) and utils.get_peer_id(m.peer_id)==g.CHAT for m in reply.messages)
            messages.extend(reply.messages);offset=min(m.id for m in reply.messages)
            await asyncio.sleep(5)
        else:raise AssertionError('small fixture no longer has bounded independent end')
        rows=[dict(id=str(m.id),date=_encode_date(m.date),media_kind=type(m.media).__name__ if m.media else None)
              for m in sorted(messages,key=lambda m:m.id)]
        assert len({m['id'] for m in rows})==len(rows) and len(rows)>8
        g.save(root/'small-oracle.json',dict(complete=True,messages=rows,chat_id=str(g.CHAT),
            captured_at=_encode_date(datetime.now(timezone.utc)),method='independent descending history to explicit empty page'))
        report['oracle_count']=len(rows)
        test=ReadBudget(root/'prebuild-test-budget.sqlite3');first=test.configure(ident,3)
        client._tgdata_read_budget=tg.connection_engine.read_budget=g.RestrictiveBudget(primary,test)
        req=BackfillStartRequest('stage6-prebuild',g.CHAT,'run','receiver',5,None,
            batch_size=5,start_date=min(m.date for m in messages),end_date=max(m.date for m in messages)+timedelta(microseconds=1))
        store=SQLiteSyncStore(root/'prebuild-state.sqlite3')
        eng=BackfillEngine(store,req.collection_id,read_batch=tg.get_message_batch)
        status=(await eng.start(req,submission='new')).status
        await asyncio.sleep(5);guard.turn=1
        try:await eng.prepare(BackfillPrepareContext.from_status(status))
        except ReadBudgetExceeded:pass
        else:raise AssertionError('expected actual restrictive allowance exhaustion')
        saved=await eng.status(status.run);assert saved.pending_message_count==3 and saved.last_failure_kind=='budget'
        prefix=await eng.prepare(BackfillPrepareContext.from_status(saved))
        assert prefix.replayed and prefix.batch.stop_reason=='interrupted'
        assert [r['id'] for r in prefix.batch.messages]==[r['id'] for r in rows[:3]]
        assert [r['date'] for r in prefix.batch.messages]==[r['date'] for r in rows[:3]]
        assert test.status(ident).used==3 and test.status(ident).remaining==0
        receiver=root/'prebuild-receiver';receiver.mkdir()
        g.base.accept(receiver,prefix,None)
        acknowledged=await eng.acknowledge(prefix.delivery)
        n=guard.history_count
        early=await eng.prepare(BackfillPrepareContext.from_status(acknowledged))
        assert early.wait_seconds>0 and guard.history_count==n
        increased=test.configure(ident,6)
        assert increased.started_at==first.started_at and increased.used==3 and increased.remaining==3
        assert primary.status(ident).limit==5000
        early2=await eng.prepare(BackfillPrepareContext.from_status(acknowledged))
        assert early2.wait_seconds>0 and early2.status.pacing_not_before==saved.pacing_not_before
        await asyncio.sleep(early2.wait_seconds+0.02);guard.turn=2
        try:await eng.prepare(BackfillPrepareContext.from_status(acknowledged))
        except ReadBudgetExceeded:pass
        else:raise AssertionError('second bounded prefix should exhaust cap 6')
        later=await eng.status(saved.run);replay=await eng.prepare(BackfillPrepareContext.from_status(later))
        assert [r['id'] for r in replay.batch.messages]==[r['id'] for r in rows[3:6]]
        assert test.status(ident).used==6 and len([r for r in guard.rpc if r['kind']=='GetHistoryRequest' and r['turn']>0])==2
        g.base.accept(receiver,replay,None);await eng.acknowledge(replay.delivery)
        histories=[r for r in guard.rpc if r['kind']=='GetHistoryRequest' and r['turn']>0]
        assert histories[1]['monotonic']-histories[0]['monotonic']>=5
        report.update(result='PASS',checks=['independent exact live IDs/dates','two real ledgers at actual SDK send',
            'error prefix persisted/replayed/receiver committed/acknowledged','early wait has no send',
            'test-only cap 3 to 6 preserves charges and shared policy','later real request respects pacing'],
            requested_slots=guard.slots,history_requests=guard.history_count,
            measured_send_spacing=histories[1]['monotonic']-histories[0]['monotonic'],test_used=6)
    except BaseException as error:
        report['error_type']=type(error).__name__
        raise
    finally:
        if tg:await tg.close()
        after=primary.status(ident);report['budget_after']=dict(limit=after.limit,used=after.used)
        if guard:report.update(rpc=guard.rpc,requested_slots=guard.slots,history_requests=guard.history_count)
        g.save(root/'prebuild-result.json',report)
        print(json.dumps({k:v for k,v in report.items() if k!='rpc'},sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checks',action='store_true');parser.add_argument('--live',action='store_true')
    parser.add_argument('--root',type=Path,default=g.ROOT);args=parser.parse_args()
    logging.disable(logging.CRITICAL)
    if args.checks:asyncio.run(checks())
    elif args.live:asyncio.run(asyncio.wait_for(live(args.root),180))
    else:parser.print_help()
