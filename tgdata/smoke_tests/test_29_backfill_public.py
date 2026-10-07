"""Public lifecycle composition: real SQLite/SDK, synthetic transport, no network."""
import asyncio
from dataclasses import FrozenInstanceError, replace
import importlib
import inspect
import io
import json
import logging
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import telethon
from telethon import errors
import tgdata
from tgdata import (
    TgData, SQLiteSyncStore, MessageBatch, ReadBudgetExceeded, SyncStorageError,
    BackfillRunRef, BackfillStartRequest, BackfillPrepareContext, BackfillDeliveryRef,
    BackfillStatus, BackfillStartResult, BackfillTurn, BackfillControlResult, BackfillRecoveryResult,
    BackfillError, BackfillConfigurationError, BackfillConflictError, BackfillUnknownRun,
    BackfillUnknownCommand, BackfillStateError, BackfillStorageError, BackfillUnknownReceipt,
    BackfillRecoveryRequired, BackfillMediaError, BackfillClockError, health,
)
from tgdata.backfill_engine import BackfillEngine
from tgdata.smoke_tests import test_27_backfill_pacing as q
from tgdata.smoke_tests.test_26_backfill_completion import AmbiguousStore

d, f, b = q.d, q.f, q.d.b
CHAT=d.CHAT
ctx=BackfillPrepareContext.from_status


def instance(backend=None, *, daily=None, budget=None, events=None, offline=False):
    tg=TgData('/intentionally-missing-public-demo.ini' if offline else f.config(),
        session_store=f.Store(),read_budget=budget,sync_store=daily,backfill_store=backend,
        health_callback=events.append if events is not None else None)
    if offline:return tg,None,None
    client=tg.connection_engine._new_client();client.session.process_entities([f.room()])
    client._mb_entity_cache.set_self_user(f.ACCOUNT,False,1);client._sender=sender=b.Sender()
    tg.connection_engine._primary_client=client;f.CLIENTS.append(client)
    return tg,client,sender


async def setup(*,pause=0,budget=None,events=None,daily=None,backend=None,**changes):
    backend=backend or d.store();tg,client,sender=instance(backend,daily=daily,budget=budget,events=events)
    clocks=q.Clocks();req=d.request(pause_seconds=pause,**changes)
    def engine(store,collection,**kw):
        return BackfillEngine(store,collection,clock=clocks.wall,monotonic_ns=clocks.nano,**kw)
    # Only clock injection: each constructed object is the actual engine.
    with patch('tgdata.tgdata.BackfillEngine',side_effect=engine):
        initial=(await tg.start_backfill(req,submission='new')).status
    return SimpleNamespace(tg=tg,client=client,sender=sender,store=backend,req=req,
        initial=initial,clocks=clocks,engine=tg._backfill_engines[req.collection_id])


async def decide(e,status,action,ident):
    return await e.tg.control_backfill(status.run,command_id=ident,
        expected_control_revision=status.control_revision,action=action)


async def prior_denial(tg,events):
    async with tg._health.call('existing-denial',group=CHAT):
        await health.report(errors.ChannelPrivateError(request=None),'handled')
    assert str(CHAT) in tg._health.snapshot()['no_access']
    return len(events),tg._health.snapshot()


async def test_exports_and_immutable_portable_values():
    names=('BackfillRunRef BackfillStartRequest BackfillPrepareContext BackfillDeliveryRef BackfillStatus '
        'BackfillStartResult BackfillTurn BackfillControlResult BackfillRecoveryResult BackfillError '
        'BackfillConfigurationError BackfillConflictError BackfillUnknownRun BackfillUnknownCommand '
        'BackfillStateError BackfillStorageError BackfillUnknownReceipt BackfillRecoveryRequired '
        'BackfillMediaError BackfillClockError').split()
    module=importlib.import_module('tgdata.backfill')
    assert all(name in tgdata.__all__ and getattr(tgdata,name) is getattr(module,name) for name in names)
    assert not any(hasattr(tgdata,name) for name in ('BackfillEngine','_BackfillState','NamespaceStore'))
    ref=BackfillRunRef('collection',-9007199254740993,9007199254740993,'run')
    assert BackfillRunRef.from_dict(ref.to_dict())==ref
    assert ref.to_dict()['generation']=='9007199254740993'
    f.rejected(FrozenInstanceError,lambda:setattr(ref,'run_id','changed'))
    e=await setup();result=await e.tg.start_backfill(e.req,submission='retry')
    assert isinstance(result,BackfillStartResult) and not result.applied
    assert isinstance(result.status,BackfillStatus)
    wire=result.status.to_dict();wire['run']['run_id']='changed'
    assert result.status.run.run_id==e.req.run_id


async def test_constructor_is_additive_and_disabled_calls_are_local():
    names=list(inspect.signature(TgData.__init__).parameters)
    assert names==['self','config_path','connection_pool_size','log_file','interactive_login',
        'health_callback','account_label','session_store','read_budget','sync_store','backfill_store']
    assert inspect.signature(TgData.__init__).parameters['backfill_store'].default is None
    backend=d.store();tg=TgData('/unused.ini',1,None,False,None,None,f.Store(),None,None,backend)
    assert tg._backfill_store is backend and tg.connection_engine._config is None
    local,_,_=instance(offline=True);req=d.request();ref=BackfillRunRef(req.collection_id,CHAT,1,req.run_id)
    context=BackfillPrepareContext(ref,100,0);delivery=BackfillDeliveryRef(ref,'archive','a'*64)
    calls=[local.start_backfill(req,submission='new'),local.get_backfill_status(ref),
        local.prepare_backfill(context),local.acknowledge_backfill(delivery),
        local.control_backfill(ref,command_id='pause',expected_control_revision=0,action='pause'),
        local.recover_backfill(ref,attempt_id='attempt',command_id='recover',expected_control_revision=0,previous_reader_stopped=True)]
    with patch.object(local.connection_engine,'_load_config',side_effect=AssertionError('config forbidden')):
        for call in calls:await f.expect(BackfillConfigurationError,call)
    assert local.connection_engine._primary_client is None and not local._backfill_engines
    plain,_,sender=instance()
    assert (await plain.get_message_batch(CHAT,after_id=100,limit=1)).next_after_id==101
    assert len(sender.reads)==1


async def test_bad_addresses_and_backend_do_not_open_config_or_source():
    class NoIO:
        async def load(self,*a):raise AssertionError('bad address reached store')
        async def compare_and_swap(self,*a):raise AssertionError('bad address reached store')
    tg,_,_=instance(NoIO(),offline=True)
    for call in (tg.start_backfill({},submission='new'),tg.get_backfill_status({}),
                 tg.prepare_backfill('hash'),tg.acknowledge_backfill('hash'),
                 tg.control_backfill(None,command_id='pause',expected_control_revision=0,action='pause'),
                 tg.recover_backfill(None,attempt_id='x',command_id='r',expected_control_revision=0,previous_reader_stopped=True)):
        await f.expect(BackfillConfigurationError,call)
    assert not tg._backfill_engines and tg.connection_engine._config is None
    local,_,_=instance(object(),offline=True)
    await f.expect(BackfillConfigurationError,local.start_backfill(d.request(),submission='new'))
    assert local.connection_engine._config is None


async def test_required_context_arguments_have_no_implicit_defaults():
    e=await setup()
    for call in (
        lambda:e.tg.start_backfill(e.req),
        lambda:e.tg.control_backfill(e.initial.run,command_id='c',expected_control_revision=0),
        lambda:e.tg.control_backfill(e.initial.run,command_id='c',action='pause'),
        lambda:e.tg.recover_backfill(e.initial.run,attempt_id='a',command_id='r',expected_control_revision=0),
    ):f.rejected(TypeError,call)
    await f.expect(BackfillConfigurationError,e.tg.start_backfill(e.req,submission='automatic'))
    assert not e.sender.calls


async def test_public_delivery_reopen_exact_receipt_and_completion():
    e=await setup();e.sender.script=[d.finite_response([f.message(101)])]
    turn=await e.tg.prepare_backfill(ctx(e.initial))
    assert isinstance(turn,BackfillTurn) and turn.status.source_exhausted and turn.status.terminal_outcome is None
    local,_,_=instance(SQLiteSyncStore(e.store.path,create=False),offline=True)
    status=await local.get_backfill_status(BackfillRunRef.from_dict(turn.status.run.to_dict()))
    replay=await local.prepare_backfill(BackfillPrepareContext.from_dict(ctx(status).to_dict()))
    assert replay.replayed and replay.batch.to_json()==turn.batch.to_json()
    assert replay.delivery==turn.delivery and local.connection_engine._config is None
    wrong=replace(replay.delivery,destination_id='foreign')
    await f.expect(BackfillConflictError,local.acknowledge_backfill(wrong))
    done=await local.acknowledge_backfill(BackfillDeliveryRef.from_dict(replay.delivery.to_dict()))
    assert done.terminal_outcome=='completed' and done.after_id==101
    assert (await local.acknowledge_backfill(replay.delivery))==done and len(e.sender.reads)==1
    assert (await local.prepare_backfill(ctx(done))).batch is None


async def test_unknown_start_and_run_never_bootstrap():
    backend=d.store();tg,_,_=instance(backend,offline=True);req=d.request()
    await f.expect(BackfillUnknownCommand,tg.start_backfill(req,submission='retry'))
    ref=BackfillRunRef(req.collection_id,CHAT,1,req.run_id)
    await f.expect(BackfillUnknownRun,tg.get_backfill_status(ref))
    assert await backend.load(CHAT) is None and tg.connection_engine._config is None


async def test_public_controls_terminal_orders_and_scoped_successor():
    for cancel_first in (True,False):
        e=await setup();e.sender.script=[d.finite_response([f.message(101)])]
        turn=await e.tg.prepare_backfill(ctx(e.initial))
        if cancel_first:
            cancelled=await decide(e,turn.status,'cancel','cancel')
            assert isinstance(cancelled,BackfillControlResult) and cancelled.applied
            done=await e.tg.acknowledge_backfill(turn.delivery);assert done.terminal_outcome=='cancelled'
        else:
            done=await e.tg.acknowledge_backfill(turn.delivery)
            result=await decide(e,done,'cancel','cancel')
            assert result.outcome=='terminal' and not result.applied and done.terminal_outcome=='completed'
        new=await e.tg.start_backfill(replace(e.req,run_id='second',expected_predecessor=done.run),submission='new')
        raw=await e.store.load(CHAT);old=await e.tg.acknowledge_backfill(turn.delivery)
        assert old.history_limited and await e.store.load(CHAT)==raw and new.status.after_id==100


async def test_one_cached_engine_preserves_busy_source_and_late_control():
    e=await setup();e.sender.script=[f.PENDING]
    task=asyncio.create_task(e.tg.prepare_backfill(ctx(e.initial)))
    await d.until(lambda:bool(e.sender.pending))
    with patch('tgdata.tgdata.BackfillEngine',side_effect=AssertionError('must retain the existing engine')):
        await f.expect(BackfillConflictError,e.tg.prepare_backfill(ctx(e.initial)))
        pause=await decide(e,e.initial,'pause','pause')
        assert pause.status.attempt_id
        await f.expect(BackfillConflictError,e.tg.recover_backfill(pause.status.run,
            attempt_id=pause.status.attempt_id,command_id='recover',expected_control_revision=1,previous_reader_stopped=True))
        await f.expect(BackfillConflictError,decide(e,pause.status,'abandon','abandon'))
        e.sender.pending[0].set_result(f.response([f.message(102),f.message(101)]))
        turn=await task
        assert turn.status.operator_intent=='paused' and turn.status.pending_message_count==2
        await f.expect(BackfillConflictError,e.tg.prepare_backfill(ctx(e.initial)))
        replay=await e.tg.prepare_backfill(ctx(turn.status));assert replay.replayed
    assert len(e.sender.reads)==1


async def test_clock_minimum_survives_public_calls_and_close():
    e=await setup(pause=240);turn=await e.tg.prepare_backfill(ctx(e.initial))
    pause=await decide(e,turn.status,'pause','pause')
    accepted=await e.tg.acknowledge_backfill(turn.delivery)
    resumed=await decide(e,accepted,'resume','resume')
    deadline=resumed.status.pacing_not_before
    e.clocks.utc+=q.timedelta(days=1)  # Forward UTC cannot erase this engine's local minimum.
    with patch('tgdata.tgdata.BackfillEngine',side_effect=AssertionError('cache lost')):
        assert (await e.tg.prepare_backfill(ctx(resumed.status))).wait_seconds==240
        await e.tg.close()
        assert (await e.tg.get_backfill_status(resumed.status.run)).pacing_not_before==deadline
        assert (await e.tg.prepare_backfill(ctx(resumed.status))).wait_seconds==240
    assert len(e.sender.reads)==1


async def test_cancelled_attempt_recovery_is_public_exact_and_local():
    e=await setup(pause=240);e.sender.script=[f.PENDING]
    task=asyncio.create_task(e.tg.prepare_backfill(ctx(e.initial)));await d.until(lambda:bool(e.sender.pending))
    task.cancel();await f.expect(asyncio.CancelledError,task)
    saved=await e.tg.get_backfill_status(e.initial.run)
    args=dict(attempt_id=saved.attempt_id,command_id='recover',expected_control_revision=0,previous_reader_stopped=True)
    calls=list(e.sender.calls);result=await e.tg.recover_backfill(saved.run,**args)
    assert isinstance(result,BackfillRecoveryResult) and result.applied and result.status.attempt_id is None
    assert result.status.pacing_ended_at==e.clocks.utc
    retry=await e.tg.recover_backfill(saved.run,**args)
    assert not retry.applied and retry.status==result.status and e.sender.calls==calls
    assert (await e.tg.prepare_backfill(ctx(result.status))).wait_seconds==240


async def test_local_operations_preserve_prior_health_and_make_no_calls():
    events=[];e=await setup(events=events)
    turn=await e.tg.prepare_backfill(ctx(e.initial))
    count,snapshot=await prior_denial(e.tg,events);calls=list(e.sender.calls)
    await e.tg.start_backfill(e.req,submission='retry')
    await e.tg.get_backfill_status(e.initial.run)
    pause=await decide(e,turn.status,'pause','pause')
    replay=await e.tg.prepare_backfill(ctx(pause.status));assert replay.replayed
    ack=await e.tg.acknowledge_backfill(replay.delivery)
    resumed=await decide(e,ack,'resume','resume')
    retired=await decide(e,resumed.status,'abandon','abandon')
    assert retired.status.delivery_abandoned
    await e.tg.start_backfill(replace(e.req,run_id='second',expected_predecessor=retired.status.run),submission='new')
    assert e.sender.calls==calls and len(events)==count and e.tg._health.snapshot()==snapshot


async def test_actual_source_error_is_reported_once_without_facade_recovery():
    events=[];e=await setup(events=events)
    original=errors.ChannelPrivateError(request=None);e.sender.script=[original]
    observed=await f.expect(errors.ChannelPrivateError,e.tg.prepare_backfill(ctx(e.initial)))
    assert observed is original and len(events)==1
    assert events[0]['call']=='get_message_batch' and events[0]['verdict']==health.NO_ACCESS
    before=e.tg._health.snapshot();calls=list(e.sender.calls)
    status=await e.tg.get_backfill_status(e.initial.run)
    assert status.last_failure_type=='ChannelPrivateError' and status.pending_batch_id is None
    await decide(e,status,'pause','pause')
    assert e.tg._health.snapshot()==before and e.sender.calls==calls and len(events)==1


async def test_status_and_local_logs_exclude_payload_and_backend_error_text():
    buffer=io.StringIO();handler=logging.StreamHandler(buffer);log=logging.getLogger('tgdata')
    old_level=log.level;log.setLevel(logging.DEBUG);log.addHandler(handler)
    try:
        e=await setup();e.sender.text=lambda mid:d.SECRET
        turn=await e.tg.prepare_backfill(ctx(e.initial));assert d.SECRET in turn.batch.to_json()
        status=await e.tg.get_backfill_status(e.initial.run)
        result=await decide(e,status,'pause','pause')
        assert d.SECRET not in json.dumps(status.to_dict()) and d.SECRET not in json.dumps(result.to_dict())
        assert e.client.api_hash not in json.dumps(status.to_dict())
        assert 'messages' not in status.to_dict() and 'sender' not in status.to_dict()
        fault=d.FaultStore(e.store);fault.fail[1]=OSError(d.SECRET);e.engine._store=fault
        error=await f.expect(BackfillStorageError,decide(e,result.status,'resume','resume'))
        assert d.SECRET not in str(error) and health.classify(error,True) is None
        assert d.SECRET not in buffer.getvalue()
        assert e.client.api_hash not in buffer.getvalue()
    finally:log.removeHandler(handler);log.setLevel(old_level)


async def test_public_budget_prefix_and_failed_prefix_save_keep_provenance():
    budget,_=f.ledger(3);e=await setup(budget=budget,batch_size=5)
    original=await f.expect(ReadBudgetExceeded,e.tg.prepare_backfill(ctx(e.initial)))
    status=await e.tg.get_backfill_status(e.initial.run)
    assert status.pending_message_count==3 and status.last_failure_account_id==f.ACCOUNT
    calls=list(e.sender.calls);replay=await e.tg.prepare_backfill(ctx(status))
    assert replay.replayed and replay.batch.to_json()==original.partial_result.to_json()
    await e.tg.acknowledge_backfill(replay.delivery)
    assert e.sender.calls==calls and budget.status(f.ACCOUNT).used==3
    budget,_=f.ledger(3);e=await setup(budget=budget,batch_size=5)
    fault=d.FaultStore(e.store);fault.fail[2]=OSError(d.SECRET);e.engine._store=fault
    local=await f.expect(BackfillStorageError,e.tg.prepare_backfill(ctx(e.initial)))
    assert isinstance(local.read_error,ReadBudgetExceeded) and local.__cause__ is None
    assert health.classify(local,True) is None
    status=await e.tg.get_backfill_status(e.initial.run)
    assert status.attempt_id and status.pending_batch_id is None


async def test_local_media_failure_does_not_clear_health_or_refetch():
    events=[];e=await setup(media_mode='download',batch_size=1,events=events)
    e.sender.files[b.ASSET_ID]=b.PAYLOAD;b.script_messages(e.sender,[b.document()]);root=b.directory()
    turn=await e.tg.prepare_backfill(ctx(e.initial),download_media_to=root)
    count,snapshot=await prior_denial(e.tg,events);calls=list(e.sender.calls)
    blob=turn.batch.messages[0]['media']['blob'];(root/blob['path']).unlink()
    await f.expect(BackfillMediaError,e.tg.prepare_backfill(ctx(turn.status),download_media_to=root))
    assert e.sender.calls==calls and len(events)==count and e.tg._health.snapshot()==snapshot
    await e.tg.acknowledge_backfill(turn.delivery)
    assert e.sender.calls==calls and e.tg._health.snapshot()==snapshot


async def test_ambiguous_admission_is_no_send_and_public_recovery_is_explicit():
    e=await setup();fault=AmbiguousStore(e.store);e.engine._store=fault
    await f.expect(BackfillStorageError,e.tg.prepare_backfill(ctx(e.initial)))
    assert not e.sender.calls
    status=await e.tg.get_backfill_status(e.initial.run);assert status.attempt_id
    await f.expect(BackfillRecoveryRequired,e.tg.prepare_backfill(ctx(status)))
    args=dict(attempt_id=status.attempt_id,command_id='recover',expected_control_revision=0,previous_reader_stopped=False)
    await f.expect(BackfillConflictError,e.tg.recover_backfill(status.run,**args))
    result=await e.tg.recover_backfill(status.run,**dict(args,previous_reader_stopped=True))
    assert result.applied and result.status.after_id==100 and not e.sender.calls


async def test_public_lost_control_reply_recognizes_one_decision():
    e=await setup();fault=AmbiguousStore(e.store);e.engine._store=fault
    first=await decide(e,e.initial,'pause','pause')
    assert first.applied and fault.writes==fault.readbacks==1
    second=await decide(e,e.initial,'pause','pause')
    assert not second.applied and second.status==first.status and fault.writes==1


async def test_daily_and_backfill_progress_are_separate_and_no_auto_namespace_exists():
    daily=d.store();e=await setup(daily=daily)
    await e.tg.initialize_sync(CHAT,after_id=100)
    daily_before=await daily.load(CHAT);turn=await e.tg.prepare_backfill(ctx(e.initial))
    await e.tg.acknowledge_backfill(turn.delivery)
    assert await daily.load(CHAT)==daily_before
    history_before=await e.store.load(CHAT);batch=await e.tg.sync_group(CHAT,limit=1)
    await e.tg.acknowledge_sync(CHAT,batch.batch_id)
    assert await e.store.load(CHAT)==history_before
    wrong=replace(e.req,collection_id='foreign',run_id='different')
    await f.expect(BackfillStateError,e.tg.start_backfill(wrong,submission='new'))
    assert await e.store.load(CHAT)==history_before
    shared=d.store();tg,_,_=instance(shared,daily=shared,offline=True)
    await tg.initialize_sync(CHAT,after_id=100);before=await shared.load(CHAT)
    await f.expect(BackfillStateError,tg.start_backfill(d.request(),submission='new'))
    assert await shared.load(CHAT)==before
    shared=d.store();tg,_,_=instance(shared,daily=shared,offline=True)
    await tg.start_backfill(d.request(),submission='new');before=await shared.load(CHAT)
    await f.expect(SyncStorageError,tg.initialize_sync(CHAT,after_id=100))
    assert await shared.load(CHAT)==before and tg.connection_engine._config is None


def example_module():
    name='example_backfill_runs'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,Path(__file__).resolve().parents[2]/'examples/backfill_runs.py')
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return sys.modules[name]


async def example_process(directory,new=False):
    path=Path(__file__).resolve().parents[2]/'examples/backfill_runs.py'
    args=[sys.executable,str(path),'--demo','--directory',str(directory)]
    if new:args.append('--new')
    return await asyncio.get_running_loop().run_in_executor(None,
        lambda:subprocess.run(args,capture_output=True,text=True,timeout=40))


async def test_example_actual_restart_exact_replay_and_completed_repeat():
    directory=f.TMP/'public-example'
    result=await example_process(directory,new=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    summary=json.loads(result.stdout.strip().splitlines()[-1])
    assert summary==dict(backfill='completed',cancelled_successor='cancelled',historical_after_id=104,
        daily_after_id=105,receipts=3,replay_source_reads=0,source_reads=3,unique_messages=5)
    repeated=await example_process(directory)
    assert repeated.returncode==0,(repeated.stdout,repeated.stderr)
    again=json.loads(repeated.stdout.strip().splitlines()[-1])
    assert again==dict(summary,source_reads=0)
    with sqlite3.connect(directory/'application.sqlite3') as db:
        ids=[r[0] for r in db.execute('SELECT message_id FROM example_messages ORDER BY message_id')]
        assert ids==['101','102','103','104','105']
        snapshots=[MessageBatch.from_json(r[0]) for r in db.execute('SELECT batch FROM example_receipts')]
        assert sorted(len(batch.messages) for batch in snapshots)==[1,2,2]
        namespaces={r[0] for r in db.execute('SELECT namespace FROM example_progress')}
        assert namespaces=={'daily','history'}


async def test_example_missing_known_state_and_repeated_new_do_not_reset():
    directory=f.TMP/'example-refusal';result=await example_process(directory,new=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    path=directory/'application.sqlite3';before=path.read_bytes()
    duplicate=await example_process(directory,new=True)
    assert duplicate.returncode==1 and path.read_bytes()==before
    with sqlite3.connect(path) as db:
        db.execute("DELETE FROM example_meta WHERE key='history-run'")
    before=path.read_bytes();missing_identity=await example_process(directory)
    assert missing_identity.returncode==1 and path.read_bytes()==before
    path.rename(directory/'retained-backup.sqlite3')
    missing_file=await example_process(directory)
    assert missing_file.returncode==1 and not path.exists()


async def test_example_receiver_keeps_full_snapshots_and_refuses_wrong_scope():
    m=example_module();db=m.ApplicationDatabase(f.TMP/'receiver-example.sqlite3',create=True)
    receiver=m.Receiver(db,'archive');first=d.sample(count=1)
    ref=BackfillRunRef('example',CHAT,1,'run');delivery=BackfillDeliveryRef(ref,'archive',first.batch_id)
    assert receiver.accept_backfill(first,delivery) and not receiver.accept_backfill(first,delivery)
    row=first.messages[0];row['text']='different observation'
    second=MessageBatch._from_records(CHAT,100,[row],'references','limit')
    other=replace(delivery,batch_id=second.batch_id)
    assert receiver.accept_backfill(second,other)
    assert receiver.summary()==dict(receipts=2,messages=1,ids=['101'])
    assert receiver.observation(delivery).to_json()==first.to_json()
    assert receiver.observation(other).to_json()==second.to_json()
    for wrong in (replace(delivery,destination_id='other'),replace(delivery,batch_id='0'*64),
                  replace(delivery,run=replace(ref,chat_id=CHAT-1))):
        f.rejected(m.ExampleStateError,lambda:receiver.accept_backfill(first,wrong))
    with db.transaction(write=True) as connection:
        connection.execute('UPDATE example_receipts SET batch=? WHERE receipt=?',
                           ('corrupt saved observation',receiver.backfill_key(delivery)))
    f.rejected(m.ExampleStateError,lambda:receiver.accept_backfill(first,delivery))


async def test_example_namespace_adapter_uses_actual_atomic_conditional_storage():
    m=example_module();db=m.ApplicationDatabase(f.TMP/'namespaced-example.sqlite3',create=True)
    one=m.NamespaceStore(db,'daily');two=m.NamespaceStore(db,'history')
    assert await one.compare_and_swap(CHAT,None,'one') is True
    assert await one.compare_and_swap(CHAT,None,'lost') is False
    assert await two.load(CHAT) is None and await two.compare_and_swap(CHAT,None,'two') is True
    assert await one.load(CHAT)=='one' and await two.load(CHAT)=='two'
    assert await one.compare_and_swap(CHAT,'one','later') is True
    assert await two.load(CHAT)=='two'
    db.remember('request',{'id':'original'})
    f.rejected(m.ExampleStateError,lambda:db.remember('request',{'id':'replacement'}))
    assert db.get('request')=={'id':'original'}


async def test_example_receiver_commit_failure_is_atomic_and_lost_reply_retries_exactly():
    m=example_module();db=m.ApplicationDatabase(f.TMP/'receiver-boundary.sqlite3',create=True)
    receiver=m.Receiver(db,'archive');batch=d.sample(count=2)
    delivery=BackfillDeliveryRef(BackfillRunRef('example',CHAT,1,'run'),'archive',batch.batch_id)
    original=sqlite3.connect
    class BeforeCommit(sqlite3.Connection):
        def commit(self):
            if self.total_changes:raise sqlite3.OperationalError('injected pre-commit failure')
            super().commit()
    def connect(*a,**kw):kw['factory']=BeforeCommit;return original(*a,**kw)
    with patch.object(m.sqlite3,'connect',side_effect=connect):
        f.rejected(m.ExampleStateError,lambda:receiver.accept_backfill(batch,delivery))
    assert receiver.summary()==dict(receipts=0,messages=0,ids=[])
    class AfterCommit(sqlite3.Connection):
        def close(self):
            changed=self.total_changes;super().close()
            if changed:raise sqlite3.OperationalError('injected lost receiver reply')
    def connect(*a,**kw):kw['factory']=AfterCommit;return original(*a,**kw)
    with patch.object(m.sqlite3,'connect',side_effect=connect):
        f.rejected(m.ExampleStateError,lambda:receiver.accept_backfill(batch,delivery))
    assert receiver.observation(delivery).to_json()==batch.to_json()
    assert not receiver.accept_backfill(batch,delivery)
    assert receiver.summary()==dict(receipts=1,messages=2,ids=['101','102'])


async def main():
    tests=[v for k,v in globals().items() if k.startswith('test_') and asyncio.iscoroutinefunction(v)]
    print('Public Backfill Tests — Telethon {}; LOCAL actual SQLite/SDK, synthetic transport'.format(telethon.__version__))
    assert telethon.__version__=='1.45.0';passed=0
    with tempfile.TemporaryDirectory(prefix='tgdata_backfill_public_') as tmp, \
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


if __name__=='__main__':sys.exit(asyncio.run(main()))
