"""Opt-in real public facade/receiver falsifier; default help is offline."""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
from pathlib import Path
import socket
from unittest.mock import patch

import gate_d_support as g
from telethon import functions, types, utils
from tgdata import TgData, SQLiteSyncStore, BackfillStartRequest, BackfillPrepareContext
from tgdata.history_window import _encode_date


async def live(root):
    report=dict(result='UNFINISHED',revision=g.revision(),checks=[]);tg=guard=budget=None
    try:
        backend=SQLiteSyncStore(root/'prebuild-state.sqlite3')
        tg,client,guard,budget,before=await g.source(root,'prebuild',g.SMALL,backfill_store=backend,media=True)
        report['budget_before']=dict(limit=before.limit,used=before.used,reserved=before.reserved)
        peer=await g.operation(report,'independent-peer',client.get_input_entity(g.SMALL),guard)
        messages=[];offset=0
        for i in range(2):
            reply=await g.operation(report,'independent-descending-{}'.format(i),
                client(functions.messages.GetHistoryRequest(peer,offset,None,0,100,0,0,0)),guard)
            if not reply.messages:break
            assert all(isinstance(m,(types.Message,types.MessageService)) and utils.get_peer_id(m.peer_id)==g.SMALL for m in reply.messages)
            messages.extend(reply.messages);offset=min(m.id for m in reply.messages)
            await asyncio.sleep(5)
        else:raise AssertionError('small oracle cannot qualify explicit EOF within 200 slots')
        rows=[dict(id=str(m.id),date=_encode_date(m.date)) for m in sorted(messages,key=lambda m:m.id)]
        assert len({r['id'] for r in rows})==len(rows)
        photo=next(m for m in messages if m.id==14)
        assert isinstance(photo.media,types.MessageMediaPhoto)
        data=await g.operation(report,'independent-photo-bytes',client.download_media(photo,file=bytes),guard)
        oracle=dict(complete=True,chat_id=str(g.SMALL),captured=g.stamp(),messages=rows,
            photo=dict(id=str(photo.id),date=_encode_date(photo.date),size=len(data),sha256=hashlib.sha256(data).hexdigest()))
        g.save(root/'small-oracle.json',oracle)
        old=g.read(g.OLD/'../tgdata19-gate-b-live-20261007-prebuild/small-oracle.json')
        report['prior_oracle_count']=len(old['messages']);report['oracle_count']=len(rows)
        request=BackfillStartRequest('gate-d-prebuild',g.SMALL,'photo-run',g.DESTINATION,12,None,
            origin='imported',after_id=13,media_mode='download',batch_size=2,
            start_date=photo.date,end_date=photo.date+timedelta(microseconds=1))
        g.save(root/'prebuild-request.json',request.to_dict())
        status=(await g.operation(report,'public-start',tg.start_backfill(request,submission='new'),guard)).status
        media=root/'prebuild-media';media.mkdir()
        await asyncio.sleep(5)
        turn=await g.operation(report,'public-prepare-download',tg.prepare_backfill(
            BackfillPrepareContext.from_status(status),download_media_to=media),guard)
        assert [r['id'] for r in turn.batch.messages]==['14']
        assert turn.batch.messages[0]['date']==_encode_date(photo.date)
        blob=turn.batch.messages[0]['media']['blob']
        assert blob['size']==len(data) and blob['sha256']==oracle['photo']['sha256']
        assert turn.status.after_id==13 and turn.status.source_exhausted and turn.status.terminal_outcome is None
        g.save(root/'prebuild-pending.json',dict(batch=turn.batch.to_dict(),delivery=turn.delivery.to_dict(),status=turn.status.to_dict()))
        await tg.close();tg=None
        events=[];local=TgData('/missing-gate-d-config.ini',backfill_store=SQLiteSyncStore(backend.path,create=False),health_callback=events.append)
        with patch.object(socket.socket,'connect',side_effect=AssertionError('local network forbidden')), \
             patch.object(socket.socket,'connect_ex',side_effect=AssertionError('local network forbidden')), \
             patch.object(local.connection_engine,'_load_config',side_effect=AssertionError('local config forbidden')):
            count,snapshot=await g.seed_health(local,g.SMALL,events)
            retry=await g.operation(report,'local-original-start-retry',local.start_backfill(request,submission='retry'))
            assert not retry.applied and retry.status==turn.status
            reopened=await g.operation(report,'local-status',local.get_backfill_status(turn.status.run))
            replay=await g.operation(report,'local-replay',local.prepare_backfill(BackfillPrepareContext.from_status(reopened),download_media_to=media))
            assert replay.replayed and replay.batch.to_json()==turn.batch.to_json() and replay.delivery==turn.delivery
            paused=await g.operation(report,'local-pause',local.control_backfill(reopened.run,
                command_id='probe-pause',expected_control_revision=reopened.control_revision,action='pause'))
            replay=await g.operation(report,'local-paused-replay',local.prepare_backfill(BackfillPrepareContext.from_status(paused.status),download_media_to=media))
            assert replay.replayed and replay.batch.to_json()==turn.batch.to_json()
            receiver=g.Receiver(root/'prebuild-receiver',create=True)
            assert receiver.accept(replay.batch,replay.delivery,media)
            assert not receiver.accept(replay.batch,replay.delivery,media)
            done=await g.operation(report,'local-ack',local.acknowledge_backfill(replay.delivery))
            assert done.terminal_outcome=='completed' and done.after_id==14 and done.operator_intent=='paused'
            assert receiver.observation(replay.delivery).to_json()==turn.batch.to_json()
            assert g.digest(receiver.media/blob['path'])==oracle['photo']['sha256']
            assert len(events)==count and local._health.snapshot()==snapshot
            assert local.connection_engine._config is None and local.connection_engine._primary_client is None
            report['final_status']=done.to_dict();report['receiver']=receiver.summary()
            report['local_health_preserved']=True
            await local.close()
        report.update(result='PASS',checks=['independent full small-group EOF and photo digest',
            'real public source and saved pending match oracle','exact local replay after reopen',
            'paused full snapshot and verified byte custody before ack','completion only after receiver acceptance',
            'all local operations blocked config/sockets and preserved INJECTED prior health'])
    except BaseException as error:
        report.update(result='STOPPED',**g.safe_error(error));raise
    finally:
        if tg:await tg.close()
        if guard:report.update(guard.report())
        if budget:
            after=budget.status(g.account());report['budget_after']=dict(limit=after.limit,used=after.used,reserved=after.reserved)
        g.save(root/'prebuild-result.json',report)
        print(json.dumps({k:v for k,v in report.items() if k in ('result','checks','error_type','frames','budget_before','budget_after','sent_requested_slots','attempted_slots','history_requests')},sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',action='store_true')
    parser.add_argument('--root',type=Path,default=g.ROOT);args=parser.parse_args()
    logging.disable(logging.CRITICAL)
    if args.live:
        try:asyncio.run(asyncio.wait_for(live(args.root),180))
        except BaseException as error:
            print(json.dumps(g.safe_error(error)));raise SystemExit(1)
    else:parser.print_help()
