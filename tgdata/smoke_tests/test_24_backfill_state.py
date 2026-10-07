"""Stage 2 state/start/status: real SQLite, crash boundaries, no Telegram.

Future run snapshots below test only codec/successor validation, not unimplemented
prepare/ack/control/recovery transitions. Run: python -m tgdata.smoke_tests.test_24_backfill_state
"""

import asyncio
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from decimal import localcontext
import json
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
from telethon import errors
from tgdata import health, MessageBatch, SQLiteSyncStore, SyncStorageError, SyncConfigurationError
from tgdata.backfill import (
    BackfillRunRef, BackfillStartRequest, BackfillError, BackfillConfigurationError,
    BackfillConflictError, BackfillUnknownRun, BackfillUnknownCommand,
    BackfillStateError, BackfillStorageError, _pause_delta,
)
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill_state import _BackfillState
from tgdata.history_window import _encode_date
from tgdata.message_batch import MAX_LONG, MAX_MESSAGE_ID
from tgdata.sync_store import _decode as decode_daily


UTC = timezone.utc
NOW = datetime(2026, 10, 7, 12, tzinfo=UTC)
START, END = NOW - timedelta(days=2), NOW - timedelta(days=1)
CHAT = -1000000000007
COLLECTION = 'test-history'
SECRET = 'DO_NOT_LOG_BACKEND_CREDENTIAL'
TMP = None
COUNT = 0


def request(run_id='run-1', **changes):
    values = dict(collection_id=COLLECTION, chat_id=CHAT, run_id=run_id,
                  destination_id='archive', pause_seconds=240, expected_predecessor=None,
                  start_date=START, end_date=END)
    values.update(changes)
    return BackfillStartRequest(**values)


def store():
    global COUNT
    COUNT += 1
    return SQLiteSyncStore(TMP / ('backfill_{}.sqlite3'.format(COUNT)))


def engine(backend, clock=lambda: NOW):
    return BackfillEngine(backend, COLLECTION, clock=clock)


def forbid_clock():
    raise AssertionError('recognized/reopen paths must not observe a clock')


def raises(kind, call):
    try:
        call()
    except kind as error:
        return error
    raise AssertionError('expected '+kind.__name__)


async def rejects(kind, call):
    try:
        await call
    except kind as error:
        return error
    raise AssertionError('expected '+kind.__name__)


async def enrolled(**changes):
    backend = store()
    req = request(**changes)
    result = await engine(backend).start(req, submission='new')
    return backend, req, result.status.run


def complete_empty_fixture(value):
    """Valid snapshot fixture, deliberately not a lifecycle transition implementation."""
    value = json.loads(json.dumps(value))
    row = value['current']
    row['terminal_outcome'] = 'completed'
    row['exhaustion'] = dict(attempt_id='attempt-final', after_id=row['after_id'],
                             next_after_id=row['after_id'], observed_at=_encode_date(NOW))
    row['pacing'] = dict(attempt_id='attempt-final', ended_at=_encode_date(NOW),
                        not_before=_encode_date(NOW + _pause_delta(row['request']['pause_seconds'])),
                        clock_uncertain=False)
    value['state_revision'] = str(int(value['state_revision']) + 2)
    return value


async def install_fixture(backend, edit):
    raw = await backend.load(CHAT)
    changed = edit(json.loads(raw))
    validated = _BackfillState(changed).to_json()
    assert await backend.compare_and_swap(CHAT, raw, validated)
    return changed


def pending_fixture(value, stop='limit'):
    value = json.loads(json.dumps(value))
    row = value['current']
    mid = int(row['after_id']) + 1
    record = dict(id=str(mid), kind='message', date=_encode_date(START), edit_date=None,
                  text='PRIVATE_MESSAGE_CONTENT', sender=dict(id=None, name=None, username=None),
                  post_author=None, reply_to_id=None, forward_from_id=None, grouped_id=None,
                  service_action=None, media=None)
    batch = MessageBatch._from_records(CHAT, int(row['after_id']), [record], 'references', stop)
    row['pending'] = batch.to_dict()
    row['pacing'] = dict(attempt_id='attempt-one', ended_at=_encode_date(NOW),
                        not_before=_encode_date(NOW + timedelta(seconds=240)), clock_uncertain=False)
    if stop == 'end':
        row['exhaustion'] = dict(attempt_id='attempt-one', after_id=row['after_id'],
                                 next_after_id=str(mid), observed_at=_encode_date(NOW))
    value['state_revision'] = '3'
    return value


async def test_input_and_portable_identity():
    req = request(chat_id=-9007199254740993)
    assert BackfillStartRequest.from_dict(req.to_dict()) == req
    ref = BackfillRunRef(COLLECTION, req.chat_id, 9007199254740993, 'opaque-run')
    assert BackfillRunRef.from_dict(ref.to_dict()) == ref
    assert ref.to_dict()['chat_id'] == '-9007199254740993'
    assert ref.to_dict()['generation'] == '9007199254740993'
    raises(FrozenInstanceError, lambda: setattr(ref, 'run_id', 'changed'))
    for kw in [dict(chat_id=True), dict(chat_id=0), dict(chat_id='-7'), dict(after_id=-1),
               dict(after_id=MAX_MESSAGE_ID+1), dict(batch_size=True), dict(batch_size=10001),
               dict(origin='fresh', after_id=2), dict(media_mode='bad'), dict(run_id=''),
               dict(run_id='has space'), dict(run_id='bad\x00id'), dict(run_id='x'*257),
               dict(destination_id='\ud800'), dict(pause_seconds=True), dict(pause_seconds='2')]:
        raises(BackfillConfigurationError, lambda kw=kw: request(**kw))
    data = ref.to_dict();data['generation'] = 1.0
    raises(BackfillConfigurationError, lambda: BackfillRunRef.from_dict(data))
    import tgdata
    assert not hasattr(tgdata.TgData, 'start_backfill')
    # Stage 3 adds these internal operations; later controls/facade remain absent.
    assert callable(BackfillEngine.prepare) and callable(BackfillEngine.acknowledge)
    assert not hasattr(BackfillEngine, 'control') and not hasattr(BackfillEngine, 'recover')


async def test_duration_precision_and_bounds():
    assert _pause_delta(request(pause_seconds=0.0000004).pause_seconds) == timedelta(microseconds=1)
    assert _pause_delta(request(pause_seconds=0.0000014).pause_seconds) == timedelta(microseconds=2)
    assert _pause_delta(request(pause_seconds=0).pause_seconds) == timedelta(0)
    for value in [float('nan'), float('inf'), -1, 1e300]:
        raises(BackfillConfigurationError, lambda value=value: request(pause_seconds=value))
    assert request(pause_seconds=-0.0).pause_seconds == 0.0
    with localcontext() as context:
        context.prec = 2
        context.Emax = 2
        assert _pause_delta(123.4567891) == timedelta(seconds=123, microseconds=456790)
        assert context.prec == 2 and context.Emax == 2


async def test_explicit_creation_and_reopen():
    backend, req, ref = await enrolled()
    result = await engine(backend, forbid_clock).start(req, submission='retry')
    assert not result.applied and result.status.run == ref
    fresh = engine(SQLiteSyncStore(backend.path, create=False), forbid_clock)
    status = await fresh.status(ref)
    assert status.start_date == START and status.end_date == END
    assert status.after_id == 0 and not status.source_exhausted
    assert status.terminal_outcome is None and status.attempt_id is None
    assert status.pending_batch_id is None and status.last_acked_batch_id is None
    assert not status.clock_uncertain and status.state_revision == 1
    assert status.to_dict()['run'] == ref.to_dict()
    data = status.to_dict();data['run']['run_id'] = 'changed'
    assert status.run == ref
    raises(FrozenInstanceError, lambda: setattr(status, 'after_id', 42))


async def test_relative_window_freezes_before_retry_clock():
    backend, req, ref = await enrolled(last_days=30, start_date=None, end_date=None)
    before = await backend.load(CHAT)
    assert (await engine(backend, forbid_clock).status(ref)).end_date == NOW
    for mode in ['new','retry']:
        result = await engine(backend, forbid_clock).start(req, submission=mode)
        assert not result.applied and result.status.start_date == NOW-timedelta(days=30)
    assert await backend.load(CHAT) == before


async def test_imported_origin_is_not_acceptance_or_exhaustion():
    backend, req, ref = await enrolled(origin='imported', after_id=MAX_MESSAGE_ID)
    status = await engine(backend, forbid_clock).status(ref)
    assert status.origin == 'imported' and status.initial_after_id == MAX_MESSAGE_ID
    assert status.after_id == MAX_MESSAGE_ID and status.last_acked_batch_id is None
    assert not status.source_exhausted and status.terminal_outcome is None
    assert status.pending_batch_id is None and status.attempt_id is None
    assert not (await engine(backend, forbid_clock).start(req, submission='retry')).applied


async def test_changed_input_and_active_successor_conflict():
    backend, req, ref = await enrolled()
    before = await backend.load(CHAT)
    for changed in [replace(req,destination_id='elsewhere'),replace(req,pause_seconds=241),
                    replace(req,origin='imported'),replace(req,batch_size=2),
                    replace(req,end_date=END-timedelta(seconds=1))]:
        await rejects(BackfillConflictError, engine(backend,forbid_clock).start(changed,submission='retry'))
    await rejects(BackfillConflictError, engine(backend,forbid_clock).start(
        request('next',expected_predecessor=ref),submission='new'))
    await rejects(BackfillConflictError, engine(backend,forbid_clock).start(request('next'),submission='new'))
    assert await backend.load(CHAT) == before


async def test_unknown_retry_and_missing_known_run():
    backend=store();req=request();eng=engine(backend,forbid_clock)
    await rejects(BackfillUnknownCommand,eng.start(req,submission='retry'))
    await rejects(BackfillUnknownRun,eng.status(BackfillRunRef(COLLECTION,CHAT,1,req.run_id)))
    assert await backend.load(CHAT) is None
    missing=BackfillRunRef(COLLECTION,CHAT,1,'lost')
    await rejects(BackfillConflictError,eng.start(request('next',expected_predecessor=missing),submission='new'))
    await rejects(BackfillConfigurationError,eng.start(req,submission='automatic'))
    assert await backend.load(CHAT) is None


async def test_namespace_and_legacy_state_isolation():
    backend,req,ref=await enrolled()
    raw=await backend.load(CHAT)
    await rejects(BackfillConfigurationError,BackfillEngine(backend,'other').status(ref))
    other_ref=BackfillRunRef('other',CHAT,1,ref.run_id)
    await rejects(BackfillStateError,BackfillEngine(backend,'other').status(other_ref))
    raises(SyncStorageError,lambda:decode_daily(raw,CHAT))
    from tgdata.sync_engine import SyncEngine
    async def never(*args,**kwargs): raise AssertionError('source forbidden')
    for dates in [{},dict(start_date=START,end_date=END)]:
        legacy=store();sync=SyncEngine(never,legacy)
        await sync.initialize(CHAT,after_id=0,**dates)
        saved=await legacy.load(CHAT)
        await rejects(BackfillStateError,engine(legacy).start(request(),submission='new'))
        assert await legacy.load(CHAT)==saved
    assert await backend.load(CHAT)==raw


async def test_successor_recognition_and_bounded_retention():
    backend,first,ref1=await enrolled()
    await install_fixture(backend,complete_empty_fixture)
    second=request('run-2',expected_predecessor=ref1)
    ref2=(await engine(backend).start(second,submission='new')).status.run
    assert ref2.generation==2
    old=await engine(backend,forbid_clock).start(first,submission='retry')
    assert not old.applied and old.status.run==ref1 and old.status.history_limited
    assert (await engine(backend).status(ref1)).terminal_outcome=='completed'
    await install_fixture(backend,complete_empty_fixture)
    third=request('run-3',expected_predecessor=ref2)
    ref3=(await engine(backend).start(third,submission='new')).status.run
    assert ref3.generation==3
    await rejects(BackfillUnknownCommand,engine(backend,forbid_clock).start(first,submission='retry'))
    await rejects(BackfillUnknownRun,engine(backend).status(ref1))
    assert (await engine(backend).start(second,submission='retry')).status.run==ref2
    await rejects(BackfillConflictError,engine(backend).start(request('stale',expected_predecessor=ref1),submission='new'))
    assert (await engine(backend).status(ref3)).after_id==0


async def test_exact_loaded_text_is_cas_expectation():
    backend,req,ref=await enrolled()
    raw=await backend.load(CHAT)
    noncanonical=json.dumps(complete_empty_fixture(json.loads(raw)),indent=2)
    assert await backend.compare_and_swap(CHAT,raw,noncanonical)
    result=await engine(backend).start(request('second',expected_predecessor=ref),submission='new')
    assert result.applied and result.status.run.generation==2


async def test_concurrent_creation_has_one_effect():
    actual=store();ready=asyncio.Event()
    class Barrier:
        count=0
        async def load(self,chat):
            raw=await actual.load(chat);self.count+=1
            if self.count==2:ready.set()
            await ready.wait();return raw
        async def compare_and_swap(self,*args):return await actual.compare_and_swap(*args)
    backend=Barrier()
    values=await asyncio.gather(engine(backend).start(request('a'),submission='new'),
                                engine(backend).start(request('b'),submission='new'),return_exceptions=True)
    assert sum(isinstance(v,BackfillConflictError) for v in values)==1
    assert sum(not isinstance(v,BaseException) and v.applied for v in values)==1
    assert json.loads(await actual.load(CHAT))['current']['ref']['run_id'] in ('a','b')


async def test_backend_failures_return_types_and_privacy():
    actual=store()
    class Fault:
        async def load(self,chat):
            try:raise errors.AuthKeyUnregisteredError(None)
            except Exception:raise RuntimeError(SECRET)
    error=await rejects(BackfillStorageError,engine(Fault()).start(request(),submission='new'))
    assert SECRET not in str(error) and health.classify(error) is None
    class Wrong:
        async def load(self,chat):return None
        async def compare_and_swap(self,*args):return 'true'
    await rejects(BackfillStorageError,engine(Wrong()).start(request(),submission='new'))
    await rejects(BackfillConfigurationError,engine(None).start(request(),submission='new'))
    class BadLoad:
        async def load(self,chat):return {}
    await rejects(BackfillStateError,engine(BadLoad()).start(request(),submission='new'))
    class LostReply:
        async def load(self,chat):return await actual.load(chat)
        async def compare_and_swap(self,*args):
            assert await actual.compare_and_swap(*args)
            raise RuntimeError(SECRET)
    await rejects(BackfillStorageError,engine(LostReply()).start(request(),submission='new'))
    assert not (await engine(actual,forbid_clock).start(request(),submission='retry')).applied


async def test_actual_sqlite_commit_then_close_error():
    backend=store();original=sqlite3.connect
    class BadClose(sqlite3.Connection):
        def close(self):
            wrote=self.total_changes>0
            super().close()
            if wrote:raise sqlite3.OperationalError(SECRET)
    def connect(*args,**kwargs):
        kwargs['factory']=BadClose
        return original(*args,**kwargs)
    with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
        error=await rejects(BackfillStorageError,engine(backend).start(request(),submission='new'))
        assert SECRET not in str(error)
    assert not (await engine(SQLiteSyncStore(backend.path,create=False),forbid_clock).start(
        request(),submission='retry')).applied


async def test_cancellation_after_commit_is_not_rollback():
    actual=store()
    class Cancel:
        async def load(self,chat):return await actual.load(chat)
        async def compare_and_swap(self,*args):
            assert await actual.compare_and_swap(*args)
            raise asyncio.CancelledError()
    await rejects(asyncio.CancelledError,engine(Cancel()).start(request(),submission='new'))
    assert not (await engine(actual,forbid_clock).start(request(),submission='retry')).applied


async def test_process_exit_at_real_create_commit():
    for mode,code in [('before',23),('after',24)]:
        backend=store()
        result=await asyncio.to_thread(subprocess.run,[sys.executable,__file__,'--crash-create',backend.path,mode],
                                       capture_output=True,text=True,timeout=25) if hasattr(asyncio,'to_thread') else subprocess.run(
                                           [sys.executable,__file__,'--crash-create',backend.path,mode],capture_output=True,text=True,timeout=25)
        assert result.returncode==code,(result.returncode,result.stderr)
        if mode=='before':
            assert await backend.load(CHAT) is None
            await rejects(BackfillUnknownCommand,engine(backend,forbid_clock).start(request(),submission='retry'))
        else:
            result=await engine(backend,forbid_clock).start(request(),submission='retry')
            assert not result.applied and result.status.run.generation==1


async def test_existing_only_open_never_bootstraps():
    absent=TMP/'must-stay-absent.sqlite3'
    raises(SyncStorageError,lambda:SQLiteSyncStore(absent,create=False))
    assert not absent.exists()
    empty=TMP/'empty.sqlite3';empty.touch();before=empty.read_bytes()
    raises(SyncStorageError,lambda:SQLiteSyncStore(empty,create=False))
    assert empty.read_bytes()==before
    backend=store();known=SQLiteSyncStore(backend.path,create=False)
    Path(backend.path).unlink()
    await rejects(SyncStorageError,known.load(CHAT))
    assert not Path(backend.path).exists()
    raises(SyncConfigurationError,lambda:SQLiteSyncStore(absent,create=1))
    created=SQLiteSyncStore(absent)
    assert Path(created.path).exists()


async def test_malformed_outer_and_request_refused():
    backend,req,ref=await enrolled();raw=await backend.load(CHAT);base=json.loads(raw)
    mutations=[lambda d:d.update(version=True),lambda d:d.update(version=2),lambda d:d.update(extra=None),
               lambda d:d.update(schema='daily'),lambda d:d.update(chat_id=str(CHAT-1)),
               lambda d:d.update(state_revision='01'),lambda d:d.update(state_revision='0'),
               lambda d:d['current']['request'].update(pause_seconds=True),
               lambda d:d['current']['request'].update(after_id='-0'),
               lambda d:d['current']['request'].update(batch_size=1.0),
               lambda d:d['current']['ref'].update(generation='2'),
               lambda d:d['current'].update(window=dict(start_date=_encode_date(START),end_date=_encode_date(END+timedelta(seconds=1))))]
    for change in mutations:
        doc=json.loads(raw);change(doc)
        raises(BackfillStateError,lambda doc=doc:_BackfillState.from_json(json.dumps(doc),COLLECTION,CHAT))
    for bad in [raw[:-1]+',"version":1}',raw.replace('240.0','NaN'), '\ud800', {}, '[]', 'null']:
        raises(BackfillStateError,lambda bad=bad:_BackfillState.from_json(bad,COLLECTION,CHAT))
    assert await backend.load(CHAT)==raw


async def test_pending_validation_and_ownership():
    backend,req,ref=await enrolled();base=json.loads(await backend.load(CHAT))
    value=pending_fixture(base);state=_BackfillState(value)
    status=state.status()
    assert status.pending_message_count==1 and status.after_id==0
    assert 'PRIVATE_MESSAGE_CONTENT' not in json.dumps(status.to_dict())
    value['current']['pending']['messages'][0]['text']='changed'
    assert state.to_dict()['current']['pending']['messages'][0]['text']=='PRIVATE_MESSAGE_CONTENT'
    for edit in [lambda r:r.update(after_id='1'),lambda r:r.update(terminal_outcome='completed'),
                 lambda r:r.update(pending=MessageBatch._from_records(CHAT,0,[],'references','end').to_dict()),
                 lambda r:r.update(pacing=None)]:
        doc=state.to_dict();edit(doc['current'])
        raises(BackfillStateError,lambda doc=doc:_BackfillState(doc))
    bad=state.to_dict();batch=bad['current']['pending'];batch['messages'][0]['date']=_encode_date(START-timedelta(seconds=1))
    bad['current']['pending']=MessageBatch._from_records(CHAT,0,batch['messages'],'references','limit').to_dict()
    raises(BackfillStateError,lambda:_BackfillState(bad))


async def test_exhaustion_and_attempt_cross_invariants():
    backend,req,ref=await enrolled();base=json.loads(await backend.load(CHAT))
    end=pending_fixture(base,'end');assert _BackfillState(end).status().source_exhausted
    complete=complete_empty_fixture(base);assert _BackfillState(complete).status().terminal_outcome=='completed'
    for edit in [lambda r:r.update(exhaustion=None),lambda r:r.update(terminal_outcome=None),
                 lambda r:r['pacing'].update(attempt_id='other'),
                 lambda r:r['exhaustion'].update(next_after_id='5'),
                 lambda r:r['pacing'].update(not_before=_encode_date(NOW))]:
        doc=json.loads(json.dumps(complete));edit(doc['current'])
        raises(BackfillStateError,lambda doc=doc:_BackfillState(doc))
    active=json.loads(json.dumps(base));active['state_revision']='2'
    active['current']['attempt']=dict(attempt_id='inflight',after_id='0',control_revision='0',admitted_at=_encode_date(NOW))
    assert _BackfillState(active).status().attempt_id=='inflight'
    active['current']['pending']=end['current']['pending']
    raises(BackfillStateError,lambda:_BackfillState(active))


async def test_control_recovery_and_failure_snapshot_validation():
    backend,req,ref=await enrolled();base=json.loads(await backend.load(CHAT))
    row=base['current'];base['state_revision']='4';row['control_revision']='1';row['operator_intent']='paused'
    row['last_control']=dict(command_id='pause-1',action='pause',expected_revision='0',accepted_revision='1',state_revision='2')
    row['pacing']=dict(attempt_id='lost-attempt',ended_at=None,not_before=_encode_date(NOW+timedelta(seconds=240)),clock_uncertain=False)
    row['last_recovery']=dict(command_id='recover-1',attempt_id='lost-attempt',expected_control_revision='1',state_revision='4',recovered_at=_encode_date(NOW))
    row['last_failure']=dict(category='budget',error_type='ReadBudgetExceeded',observed_at=_encode_date(NOW),retry_at=None,account_id='9007199254740993')
    status=_BackfillState(base).status()
    assert status.operator_intent=='paused' and status.last_failure_account_id==9007199254740993
    assert status.to_dict()['last_failure_account_id']=='9007199254740993'
    mutations=[lambda r:r['last_control'].update(accepted_revision='2'),lambda r:r['last_control'].update(action='resume'),
               lambda r:r['last_recovery'].update(attempt_id='wrong'),lambda r:r['last_failure'].update(error_type='raw secret error'),
               lambda r:r['last_failure'].update(account_id='0'),lambda r:r['pacing'].update(clock_uncertain=1)]
    for edit in mutations:
        d=json.loads(json.dumps(base));edit(d['current'])
        raises(BackfillStateError,lambda d=d:_BackfillState(d))


async def test_abandonment_and_pending_predecessor_refused():
    backend,req,ref=await enrolled();base=pending_fixture(json.loads(await backend.load(CHAT)))
    row=base['current'];row['terminal_outcome']='cancelled';row['operator_intent']='cancelled';row['control_revision']='1'
    row['last_control']=dict(command_id='cancel',action='cancel',expected_revision='0',accepted_revision='1',state_revision='3')
    raw=await backend.load(CHAT)
    assert await backend.compare_and_swap(CHAT,raw,_BackfillState(base).to_json())
    await rejects(BackfillConflictError,engine(backend).start(request('next',expected_predecessor=ref),submission='new'))
    row['abandoned']=dict(batch_id=row['pending']['batch_id'],next_after_id='1',observed_at=_encode_date(NOW))
    row['pending']=None;row['control_revision']='2';base['state_revision']='4'
    row['last_control']=dict(command_id='abandon',action='abandon',expected_revision='1',accepted_revision='2',state_revision='4')
    assert _BackfillState(base).status().terminal_outcome=='cancelled'
    assert _BackfillState(base).status().after_id==0
    raw=await backend.load(CHAT);assert await backend.compare_and_swap(CHAT,raw,_BackfillState(base).to_json())
    assert (await engine(backend).start(request('next',expected_predecessor=ref),submission='new')).applied


async def test_counter_limits_and_stale_reference():
    backend,req,ref=await enrolled()
    done=await install_fixture(backend,complete_empty_fixture)
    raw=await backend.load(CHAT);done['state_revision']=str(MAX_LONG)
    assert await backend.compare_and_swap(CHAT,raw,_BackfillState(done).to_json())
    await rejects(BackfillConflictError,engine(backend,forbid_clock).start(request('next',expected_predecessor=ref),submission='new'))
    await rejects(BackfillUnknownRun,engine(backend).status(replace(ref,generation=2)))
    raises(BackfillConfigurationError,lambda:replace(ref,generation=MAX_LONG+1))


async def test_window_and_clock_failures_are_local():
    backend=store()
    for kw in [dict(start_date=START.replace(tzinfo=None)),dict(end_date=None),dict(last_days=1),
               dict(start_date=END,end_date=START),dict(start_date=None,end_date=None,last_days=0)]:
        raises(BackfillConfigurationError,lambda kw=kw:request(**kw))
    await rejects(BackfillConfigurationError,engine(backend).start(request(end_date=NOW+timedelta(seconds=1)),submission='new'))
    await rejects(BackfillConfigurationError,engine(backend).start(request(start_date=None,end_date=None,last_days=MAX_MESSAGE_ID),submission='new'))
    def badclock():raise RuntimeError(SECRET)
    error=await rejects(BackfillConfigurationError,engine(backend,badclock).start(request(),submission='new'))
    assert SECRET not in str(error) and health.classify(error) is None
    assert await backend.load(CHAT) is None
    equivalent=request(start_date=START.astimezone(timezone(timedelta(hours=3))),end_date=END.astimezone(timezone(timedelta(hours=3))))
    await engine(backend).start(request(),submission='new')
    assert not (await engine(backend,forbid_clock).start(equivalent,submission='retry')).applied


async def crash_create(path,mode):
    import os
    backend=SQLiteSyncStore(path,create=False)
    original=sqlite3.connect
    class Crash(sqlite3.Connection):
        def commit(self):
            if self.total_changes:
                if mode=='before':os._exit(23)
                super().commit();os._exit(24)
            return super().commit()
    def connect(*args,**kwargs):
        kwargs['factory']=Crash
        return original(*args,**kwargs)
    with patch('tgdata.sync_store.sqlite3.connect',side_effect=connect):
        await engine(backend).start(request(),submission='new')
    raise AssertionError('crash boundary not reached')


async def main():
    global TMP
    tests=[value for name,value in globals().items() if name.startswith('test_') and asyncio.iscoroutinefunction(value)]
    print('Backfill State Tests — Telethon {}; offline actual SQLite'.format(telethon.__version__))
    assert telethon.__version__=='1.45.0'
    passed=0
    with tempfile.TemporaryDirectory(prefix='tgdata_backfill_state_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        TMP=Path(tmp)
        for test in tests:
            print('\nTEST:',test.__name__)
            try:await asyncio.wait_for(test(),timeout=60)
            except Exception:traceback.print_exc();print('✗ Failed')
            else:passed+=1;print('✓ Passed')
    print('\nPassed: {}/{}'.format(passed,len(tests)))
    return 0 if passed==len(tests) else 1


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--crash-create':
        with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
             patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
            asyncio.run(crash_create(sys.argv[2],sys.argv[3]))
    else:
        sys.exit(asyncio.run(main()))
