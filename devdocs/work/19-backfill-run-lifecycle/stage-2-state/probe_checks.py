"""Offline checks of the Gate A instrument; synthetic transport is not LIVE evidence."""

import asyncio
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
PROBE = Path(__file__).resolve().parents[1] / 'live_probe.py'
spec = importlib.util.spec_from_file_location('backfill_gate_a_probe', str(PROBE))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

from telethon import errors, functions, types
from tgdata import SQLiteSyncStore
from tgdata.backfill import BackfillStartRequest
from tgdata.backfill_engine import BackfillEngine
from tgdata.history_window import _encode_date
from tgdata.smoke_tests import test_19_message_batches as b

CHAT = -1000000000007
NOW = datetime(2026,10,7,12,tzinfo=timezone.utc)


def limits(**changes):
    result=dict(max_rpc_requests=100,max_history_requests=10,max_requested_slots=1000,
                max_media_bytes=0,timeout_seconds=10,spacing_seconds=0)
    result.update(changes)
    return result


def expect(kind, call):
    try:call()
    except kind:return
    raise AssertionError('expected '+kind.__name__)


async def reject(kind, call):
    try:await call
    except kind:return
    raise AssertionError('expected '+kind.__name__)


async def fixture(root):
    req=BackfillStartRequest('probe',CHAT,'probe-run','test-receiver',0,None,
                             start_date=NOW-timedelta(days=2),end_date=NOW-timedelta(days=1))
    store=SQLiteSyncStore(root/'probe-state.sqlite3')
    status=(await BackfillEngine(store,'probe',clock=lambda:NOW).start(req,submission='new')).status
    manifest=dict(schema='tgdata.backfill-probe',version=1,run=status.run.to_dict(),
                  start_request=req.to_dict(),window=dict(start_date=_encode_date(status.start_date),
                  end_date=_encode_date(status.end_date)),expected_account_id='111',
                  oracle=dict(method='manual',reference='synthetic-offline-fixture-only',
                  captured_at=_encode_date(NOW),complete=True,messages=[]),limits=limits())
    return store,manifest


async def main():
    passed=0
    with tempfile.TemporaryDirectory(prefix='tgdata19_probe_checks_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        root=Path(tmp);b.f.TMP=root
        try:
            store,manifest=await fixture(root)
            parsed=p.manifest_from_text(json.dumps(manifest))
            raw=await store.load(CHAT)
            with patch.object(p,'TgData',side_effect=AssertionError('preflight must not create a Telegram client')):
                _,status,_=await p.preflight(parsed,store.path)
                assert status.run.run_id=='probe-run' and await store.load(CHAT)==raw
                absent=root/'missing.sqlite3'
                await reject(Exception,p.preflight(parsed,absent))
                assert not absent.exists()
            passed+=1;print('PASS existing-only offline preflight and unchanged state')

            for change in [lambda d:d['oracle'].update(complete=False),
                           lambda d:d['oracle'].update(method='tgdata'),
                           lambda d:d['limits'].update(max_rpc_requests=True),
                           lambda d:d['limits'].update(timeout_seconds=float('inf')),
                           lambda d:d.update(extra='unsupported')]:
                bad=json.loads(json.dumps(manifest));change(bad)
                expect(Exception,lambda bad=bad:p.manifest_from_text(json.dumps(bad)))
            passed+=1;print('PASS independent oracle/limit/shape preflight refusals')

            guard=p.ReadOnlyGuard(CHAT,limits())
            expect(p.ProbeStop,lambda:guard.before_send(functions.messages.SendMessageRequest(
                types.InputPeerChannel(7,7),'do not send',random_id=1)))
            expect(p.ProbeStop,lambda:guard.before_send(functions.channels.JoinChannelRequest(types.InputChannel(7,7))))
            expect(p.ProbeStop,lambda:guard.before_send(functions.messages.GetHistoryRequest(
                types.InputPeerChannel(8,8),0,None,0,1,0,0,0)))
            expect(p.ProbeStop,lambda:guard.before_send(functions.users.GetUsersRequest([types.InputUser(123,456)])))
            assert guard.rpc==[]
            passed+=1;print('PASS actual write/join/wrong-target RPCs refused before send')

            one=p.ReadOnlyGuard(CHAT,limits(max_history_requests=1,max_requested_slots=1))
            one.before_send(b.f.history(1))
            expect(p.ProbeStop,lambda:one.before_send(b.f.history(1)))
            assert one.history_count==1 and one.slots==1
            passed+=1;print('PASS actual request-type caps')

            budget,_=b.f.ledger(1000)
            tg,client,sender=b.instance(budget)
            measured=p.ReadOnlyGuard(CHAT,limits())
            measured.instrument(client)
            sender.script=[b.f.response([b.f.message(i) for i in range(100,0,-1)]),
                           b.f.response([b.f.message(i) for i in range(120,100,-1)])]
            batch=await tg.get_message_batch(CHAT,after_id=0,limit=120)
            assert len(batch.messages)==120 and batch.next_after_id==120
            history=[r for r in measured.rpc if r['kind']=='GetHistoryRequest']
            assert len(history)==2 and history[0]['page'][0]==history[1]['page'][0]
            assert [r['page'][1] for r in history]==[1,2]
            assert measured.slots==120 and budget.status(b.f.ACCOUNT).used==120
            await tg.close()
            passed+=1;print('PASS actual Telethon iterator/page and budget composition with synthetic transport')

            budget,_=b.f.ledger(100)
            tg,client,sender=b.instance(budget)
            measured=p.ReadOnlyGuard(CHAT,limits(max_history_requests=1))
            measured.instrument(client)
            sender.script=[errors.ServerError(None,'injected test failure',500),b.f.response([b.f.message(1)])]
            await reject(p.ProbeStop,tg.get_message_batch(CHAT,after_id=0,limit=1))
            assert len(sender.reads)==1 and measured.history_count==1
            assert measured.rpc[-1]['kind'] in ('GetUsersRequest','GetHistoryRequest')
            await tg.close()
            passed+=1;print('PASS SDK retry cannot bypass actual-send history cap')

            rows=[dict(id='1',date=_encode_date(NOW-timedelta(days=2)),blob=None)]
            sample=json.loads(json.dumps(manifest));sample['oracle']['messages']=rows
            assert p.compare_observations(sample,rows)['exact_match']
            assert not p.compare_observations(sample,[])['exact_match']
            changed=[dict(rows[0],date=_encode_date(NOW-timedelta(days=2,seconds=-1)))]
            assert p.compare_observations(sample,changed)['date_mismatches']==['1']
            unknown_media=[dict(rows[0],blob=dict(sha256='0'*64,size=1))]
            assert p.compare_observations(sample,unknown_media)['media_mismatches']==['1']
            passed+=1;print('PASS independent comparison distinguishes match, omission and date mismatch')

            live_manifest=json.loads(json.dumps(manifest))
            date=NOW-timedelta(days=2)
            live_manifest['oracle']['messages']=[dict(id=str(i),date=_encode_date(date),blob=None) for i in range(1,121)]
            budget,_=b.f.ledger(1000)
            config=root/'selected-synthetic.ini';config.write_text('# only used by the patched test factory\n')
            def actual_library_with_synthetic_transport(*args,**kwargs):
                assert kwargs['interactive_login'] is False and kwargs['connection_pool_size']==1
                tg,client,sender=b.instance(kwargs['read_budget'])
                tg.connection_engine._primary_client=None
                tg.connection_engine._new_client=lambda *a,**k:client
                messages=[b.f.message(i) for i in range(1,121)]
                for message in messages:message.date=date
                sender.script=[b.f.response(list(reversed(messages[:100]))),
                               b.f.response(list(reversed(messages[100:]))),b.f.response([])]
                return tg
            with patch.object(p,'TgData',side_effect=actual_library_with_synthetic_transport):
                report=await p.live_scan(live_manifest,store.path,config,budget.path)
            assert report['comparison']=='MATCH' and report['account_verified'] is True,report
            assert report['sdk_page_boundary_observed'] is True
            assert report['lifecycle_state_unchanged'] is True and report['gate_verdict']=='INCONCLUSIVE'
            assert await store.load(CHAT)==raw
            passed+=1;print('PASS full instrument composition with real state/reader/budget and synthetic transport; not LIVE')

            path=root/'manifest.json';path.write_text(json.dumps(manifest))
            output=root/'preflight.json'
            result=subprocess.run([sys.executable,str(PROBE),'--manifest',str(path),'--state',store.path,
                                   '--output',str(output)],capture_output=True,text=True,timeout=15)
            assert result.returncode==0,result.stderr
            saved=json.loads(output.read_text())
            assert saved['live_started'] is False and saved['gate_verdict']=='INCONCLUSIVE'
            again=subprocess.run([sys.executable,str(PROBE),'--manifest',str(path),'--state',store.path,
                                  '--output',str(output)],capture_output=True,text=True,timeout=15)
            assert again.returncode==2 and json.loads(output.read_text())==saved
            help_result=subprocess.run([sys.executable,str(PROBE),'--help'],capture_output=True,text=True,timeout=15)
            assert help_result.returncode==0
            passed+=1;print('PASS CLI defaults offline, never overwrites evidence, and never emits gate PASS')
        finally:
            for client in b.f.CLIENTS:await client.disconnect()
            b.f.CLIENTS.clear()
    print('Passed: {}/9; LOCAL/INJECTED only, no live gate'.format(passed))
    return 0 if passed==9 else 1


if __name__=='__main__':sys.exit(asyncio.run(main()))
