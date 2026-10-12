"""Full combined offline prebuild. One frozen stop/projector pair in every worker.

No product files are edited. Actual Worker, Telethon, SQLite, loops and OS pipes
execute behind synthetic transport. Only named observation/fault boundaries vary.
"""
import asyncio
from contextlib import contextmanager, ExitStack
import hashlib
import inspect
import json
import logging
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tgdata import worker, MessageBatch
from tgdata import worker_protocol as protocol
from tgdata.connection_engine import ConnectionEngine
from tgdata.smoke_tests import test_37_worker as core
from tgdata.smoke_tests import test_38_worker_process as original
from telethon import errors, types, functions
from telethon.extensions import BinaryReader

FINGERPRINT = json.loads((FOLDER/'revision4_fingerprint.json').read_text())
SENTINEL = 'COMBINED_PREBUILD_PRIVATE_TEXT'
RESULTS = []
PROCESS_COUNT = 0


def check_fingerprint():
    for name, expected in FINGERPRINT['sources'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
    for name, expected in FINGERPRINT['candidates'].items():
        assert hashlib.sha256((FOLDER/name).read_bytes()).hexdigest() == expected, name
    assert __import__('telethon').__version__ == FINGERPRINT['telethon'] == '1.45.0'


@contextmanager
def combined_candidate():
    check_fingerprint()
    driver = dict(worker.__dict__)
    projector = dict(protocol.__dict__,
        _CANONICAL_AUTH_REASONS=frozenset(FINGERPRINT['canonical_auth_reasons']))
    exec(compile((FOLDER/'revision4_candidate_serve.py').read_text(),
                 '<frozen-combined-serve>', 'exec'), driver)
    exec(compile((FOLDER/'revision4_candidate_diagnostics.py').read_text(),
                 '<frozen-combined-diagnostics>', 'exec'), projector)
    with patch.object(worker, 'serve', driver['serve']), \
         patch.object(protocol, 'describe_error', projector['describe_error']):
        yield


def sdk_error(code, text):
    with BinaryReader(bytes(types.RpcError(code, text))) as reader:
        decoded = reader.tgread_object()
    return errors.rpc_message_to_error(decoded,
        functions.users.GetUsersRequest([types.InputUserSelf()]))


def child(root, mode, stock, stop_signal):
    root = Path(root)
    items = {} if stock else {aid: core.fixture(root, aid) for aid in (111, 222)}
    old_handlers = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    old_logging = logging.root.manager.disable
    def trace(kind, detail):
        # Legacy source assertions must keep seeing only actual transport work.
        # Provenance/lifecycle observations are separate, never discarded.
        name = 'trace.jsonl' if kind in ('client','request','cleanup') else 'evidence.jsonl'
        with (root/name).open('a') as stream:
            stream.write(json.dumps([kind, detail])+'\n')
    trace('candidate', FINGERPRINT['candidates'])
    def release_on_command(event):
        loop = asyncio.get_running_loop()
        signal.signal(signal.SIGUSR1, lambda s, frame: loop.call_soon_threadsafe(event.set))
    def hook(client, sender):
        loop = asyncio.get_running_loop()
        trace('client', sender.account)
        if mode in ('quiet', 'held', 'caller_cancel'):
            sender.script['GetHistoryRequest'] = [loop.create_future()]
        if mode in ('held', 'caller_cancel'):
            sender.close_release = asyncio.Event()
            release_on_command(sender.close_release)
        if mode == 'caller_cancel':
            owner = asyncio.current_task()
            signal.signal(signal.SIGUSR2, lambda s, frame: loop.call_soon_threadsafe(owner.cancel))
        if mode in ('cleanup_failure', 'body_cleanup', 'setup_cleanup', 'partial_cleanup'):
            sender.close_error = OSError(SENTINEL)
        elif mode == 'internal_cleanup_cancel':
            sender.close_error = asyncio.CancelledError(SENTINEL)
        if mode in ('quiet', 'held', 'caller_cancel'):
            select = loop._selector.select
            def observed(timeout=None):
                trace('select', timeout)
                return select(timeout)
            loop._selector.select = observed
    for item in items.values():
        item.trace, item.hook = trace, hook
        item.room.left = True
    if items:
        item = items[111]
        if mode in ('partial', 'partial_cleanup'):
            item.scripts['GetHistoryRequest'] = [
                core.b.f.response([core.b.f.message(n) for n in reversed(range(101,201))]),
                errors.FloodWaitError(request=None, capture=7200)]
        elif mode == 'pressure':
            message = core.b.f.message(101)
            message.message = 'x'*(2*1024*1024)
            item.scripts['GetHistoryRequest'] = [core.b.f.response([message])]
        elif mode == 'wrong_owner':
            item.actual = 333
        elif mode == 'unauthenticated':
            item.logged_in = False
            item.responses['GetStateRequest'] = errors.AuthKeyUnregisteredError(request=None)
        elif mode == 'webview':
            item.join_result = types.messages.ChatInviteJoinResultWebView(111,1152921504606847099,[])
        elif mode == 'body_cleanup':
            item.scripts['GetHistoryRequest'] = [errors.ChannelPrivateError(request=None)]
        elif mode == 'setup_cleanup':
            item.connect_error = LookupError(SENTINEL)
        elif mode.startswith('auth_') or mode == 'delivery_projection':
            code, text = (401,SENTINEL) if mode == 'delivery_projection' else auth_spec(mode)
            item.scripts['GetUsersRequest'] = [sdk_error(code,text)]
    real_create = asyncio.BaseEventLoop.create_task
    def create(loop, coro, *args, **kwargs):
        if mode == 'before_task' and getattr(coro,'__qualname__','') == 'Worker.execute':
            trace('publication','before-create')
            os.kill(os.getpid(), stop_signal)
        task = real_create(loop,coro,*args,**kwargs)
        if mode == 'publication' and getattr(coro,'__qualname__','') == 'Worker.execute':
            trace('publication','created-before-return')
            os.kill(os.getpid(),stop_signal)
        return task
    real_close = worker.Worker.close
    async def close(instance):
        if mode == 'finalize':
            event = asyncio.Event()
            release_on_command(event)
            trace('finalize','entered')
            await event.wait()  # Named pause, then actual facade close.
        await real_close(instance)
        trace('finalize','finished')
    real_loop_close = asyncio.BaseEventLoop.close
    def loop_close(loop):
        pending = len([t for t in asyncio.all_tasks(loop) if not t.done()])
        real_loop_close(loop)
        trace('loop',dict(pending=pending,closed=loop.is_closed()))
    real_encoder = protocol.encode_frame
    def encoder(value,**options):
        if mode == 'delivery_projection' and value.get('kind')=='result' and (
                value.get('error') or {}).get('category')=='authentication_required':
            raise protocol.WorkerError('delivery_failed')  # Explicit post-source serializer fault.
        return real_encoder(value,**options)
    with ExitStack() as stack:
        stack.enter_context(combined_candidate())
        stack.enter_context(patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')))
        stack.enter_context(patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')))
        stack.enter_context(patch.object(asyncio.BaseEventLoop,'create_task',create))
        stack.enter_context(patch.object(asyncio.BaseEventLoop,'close',loop_close))
        stack.enter_context(patch.object(worker.Worker,'close',close))
        stack.enter_context(patch.object(protocol,'encode_frame',encoder))
        if items:
            stack.enter_context(core.install_factory(items))
        if mode.startswith('fatal_'):
            code, text = auth_spec(mode.replace('fatal_','auth_',1))
            worker._fatal(ConnectionEngine._auth_required('private',sdk_error(code,text),False),worker._raw_output(None))
            result = 2
        elif mode == 'store':
            options = worker.load_inventory(root/'worker.json')
            options['accounts'] = [worker.WorkerAccount(aid,item.config,session_store=item.store)
                                   for aid,item in items.items()]
            result = worker.serve(**options)
        else:
            result = worker.main(['--config',str(root/'worker.json')])
    trace('clients_final', [dict(account=item.actual, closed=c._sender.closed,
          disconnect_attempts=c._sender.close_calls) for item in items.values() for c in item.clients])
    trace('restored',all(signal.getsignal(s)==h for s,h in old_handlers.items())
          and logging.root.manager.disable==old_logging)
    return result


class Process(original.Process):
    def __init__(self,root,scenario='normal',stock=False):
        global PROCESS_COUNT
        PROCESS_COUNT += 1
        self.root,self.buffer,self.stderr = root,bytearray(),b''
        parts=scenario.split(':')
        mode,stop_signal=parts[0],int(parts[1]) if len(parts)>1 else int(signal.SIGTERM)
        self.p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',
            str(root),mode,str(int(stock)),str(stop_signal)],cwd=str(ROOT),stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)

    def wait(self,code=0,timeout=15):
        super().wait(code,timeout)
        rows=self.observations()
        assert ['candidate',FINGERPRINT['candidates']] in rows
        assert ['restored',True] in rows
        assert all(row[1]['pending']==0 and row[1]['closed'] for row in rows if row[0]=='loop')
        assert not self.stderr and SENTINEL.encode() not in self.buffer

    def observations(self):
        path=self.root/'evidence.jsonl'
        metadata=[] if not path.exists() else [json.loads(line) for line in path.read_bytes().split(b'\n')[:-1]]
        return self.trace()+metadata

    def until(self,predicate,timeout=15):
        deadline=time.monotonic()+timeout
        while not predicate(self.observations()):
            assert self.p.poll() is None and time.monotonic()<deadline, 'trace timed out'
            time.sleep(.01)


AUTH = {
    'auth_unknown401': (401,SENTINEL), 'auth_unknown406': (406,SENTINEL),
    'auth_generic403': (403,SENTINEL), 'auth_unregistered': (401,'AUTH_KEY_UNREGISTERED'),
    'auth_revoked': (401,'SESSION_REVOKED'), 'auth_banned': (401,'USER_DEACTIVATED_BAN')}


def auth_spec(mode):
    return AUTH[mode]


def lifecycle(mode,sig):
    with original.setup(mode+':'+str(int(sig))) as (process,budget,join):
        assert process.line()['kind']=='ready'
        process.send(original.request() + (b'' if mode=='finalize' else original.request(2,222)))
        if mode=='finalize':
            assert process.result()[0]['ok']
            process.eof()
            process.until(lambda rows:['finalize','entered'] in rows)
        elif mode not in ('before_task','publication'):
            process.until(lambda rows:['request','GetHistoryRequest'] in rows and
                any(r[0]=='select' and r[1] is not None and r[1]>1 for r in rows))
        if mode not in ('before_task','publication'):
            process.p.send_signal(signal.SIGUSR2 if mode=='caller_cancel' else sig)
        if mode in ('held','finalize','caller_cancel'):
            if mode!='finalize':process.until(lambda rows:['cleanup','entered'] in rows)
            process.p.send_signal(signal.SIGUSR2 if mode=='caller_cancel' else sig)
            time.sleep(.15)  # Parent observation only; no child polling timer.
            assert process.p.poll() is None
            assert [ 'finalize' if mode=='finalize' else 'cleanup','finished'] not in process.observations()
            process.p.send_signal(signal.SIGUSR1)  # Release held native/event boundary only now.
        process.wait(3 if mode=='caller_cancel' else 128+sig,timeout=5)
        rows=process.observations();clients=[r[1] for r in rows if r[0]=='client']
        expected=0 if mode in ('before_task','publication') else 1
        assert len(clients)==expected and budget.status(111).used==2*expected
        assert budget.status(222).used==join.status(111).used==0
        if expected:
            assert rows.count(['cleanup','finished'])==1
        assert ['finalize','finished'] in rows
        return dict(mode=mode,signal=sig.name,clients=len(clients),charge=budget.status(111).used,
                    exit=process.p.returncode,settled=True,restored=True)


def empty_inventory():
    with original.setup(stock=True,edit=lambda root,m:m.update(accounts=[])) as (p,budget,join):
        assert p.line()['account_count']==0
        p.eof();p.wait()
        assert not any(r[0]=='client' for r in p.trace())


def startup_refusals():
    def alias(root,m):
        (root/'account-222.ini').write_text((root/'account-111.ini').read_text())
    cases=[lambda root,m:m.update(version=2), lambda root,m:m.update(read_budget=core.SECRET),
           lambda root,m:m.update(worker_id=core.SECRET+'\n'),
           lambda root,m:m['accounts'][0].update(config_path=core.SECRET),
           lambda root,m:m['accounts'].append(m['accounts'][0]),
           lambda root,m:m['accounts'][0].update(account_id='333'), alias]
    for edit in cases:
        with original.setup(stock=True,edit=edit) as (p,budget,join):
            value=p.line();assert value['kind']=='fatal' and value['worker_stopping']
            p.wait(2)
            assert not any(r[0]=='client' for r in p.trace())
            assert not list(p.root.glob('*.session')) and budget.status(111).used==0
    return dict(refusals=len(cases),clients=0)


def cleanup(mode):
    with original.setup(mode) as (p,budget,join):
        p.line()
        first=original.request(group_id='@room',after_id='100',limit=200) if mode=='partial_cleanup' else original.request()
        p.send(first+original.request(2,222));p.eof()
        value,events=p.result()
        assert value['worker_stopping'] and SENTINEL not in json.dumps(value)
        assert value['ok'] is (mode in ('cleanup_failure','internal_cleanup_cancel'))
        if mode=='body_cleanup':assert value['error']['type']=='ChannelPrivateError'
        if mode=='setup_cleanup':assert value['error']['type']=='LookupError'
        if mode=='partial_cleanup':
            assert value['error']['wait_seconds']==7200
            assert len(MessageBatch(value['partial_result']).messages)==100
        p.wait(3)
        rows=p.observations();final=next(r[1] for r in rows if r[0]=='clients_final')
        assert len(final)==1 and final[0]['disconnect_attempts']==1 and not final[0]['closed']
        assert budget.status(222).used==0
        assert budget.status(111).used==(0 if mode=='setup_cleanup' else 200 if mode=='partial_cleanup' else 2)
        return dict(mode=mode,outcome='returned' if value['ok'] else value['error']['type'],
                    charge=budget.status(111).used,cleanup_failed=True,next_client=False,exit=3)


def authentication(mode,op):
    code,text=auth_spec(mode)
    with original.setup(mode) as (p,budget,join):
        p.line();p.send(original.request(operation=op));p.eof()
        value,events=p.result();assert not value['ok'] and not events
        assert SENTINEL not in json.dumps(value)
        expected=text if text in FINGERPRINT['canonical_auth_reasons'] else None
        assert value['error'].get('reason')==expected
        if code==403:assert value['error']['category']=='telegram_error' and value['error']['code']==403
        else:assert value['error']['category']=='authentication_required'
        if mode=='auth_banned':assert value['error']['banned'] is True
        p.wait()
        rows=p.trace()
        assert rows.count(['cleanup','finished'])==1
        assert not any(r[0]=='request' and r[1] in ('GetHistoryRequest','JoinChannelRequest',
            'ImportChatInviteRequest','ResolveUsernameRequest','SendCodeRequest') for r in rows)
        assert budget.status(111).used==join.status(111).used==0
        return dict(operation=op,error=value['error']['type'],reason=expected,charge=0,closed=True)


def secondary_projection(mode):
    with original.setup(mode,stock=mode.startswith('fatal_')) as (p,budget,join):
        if mode.startswith('fatal_'):
            value=p.line();assert value['kind']=='fatal'
            code,text=auth_spec(mode.replace('fatal_','auth_',1))
            assert value['error'].get('reason')==(text if text in FINGERPRINT['canonical_auth_reasons'] else None)
            p.wait(2)
        else:
            p.line();p.send(original.request()+original.request(2,222));p.eof()
            value,_=p.result()
            assert value['partial_omitted'] and value['worker_stopping']
            assert 'reason' not in value['source_error'] and value['error']['code']=='delivery_failed'
            p.wait(3)
        assert SENTINEL not in json.dumps(value)
        assert budget.status(111).used==budget.status(222).used==join.status(111).used==0
        return dict(mode=mode,raw_text=False,exit=p.p.returncode)


def record(name,action):
    detail=action()
    value=dict(case=name,status='PASS',detail=detail)
    RESULTS.append(value)
    print(json.dumps(value),flush=True)


def run_core_controls():
    async def run():
        with combined_candidate(), \
             patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
             patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
            tests=[test for name,test in vars(core).items() if name.startswith('test_') and inspect.iscoroutinefunction(test)]
            for test in tests:
                await asyncio.wait_for(test(),30)
                record('core.'+test.__name__,lambda:dict(actual_sdk=True))
    previous=logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:asyncio.run(run())
    finally:logging.disable(previous)


def main():
    check_fingerprint()
    try:
        with patch.object(original,'Process',Process):
            for mode in ('quiet','held','before_task','publication','finalize'):
                for sig in (signal.SIGINT,signal.SIGTERM):
                    record(mode+'.'+sig.name,lambda mode=mode,sig=sig:lifecycle(mode,sig))
            record('caller_cancel.repeated',lambda:lifecycle('caller_cancel',signal.SIGTERM))
            record('empty_inventory.eof',empty_inventory)
            record('startup.refusals',startup_refusals)
            for name in ('test_all_four_operations_two_accounts_and_eof',
                         'test_partial_batch_health_correlation_and_charge_survive_json',
                         'test_webview_identifiers_survive_javascript_exactly',
                         'test_wrong_identity_and_missing_auth_never_read_or_login',
                         'test_bad_complete_frames_and_reused_ids_are_local',
                         'test_truncated_and_oversized_frames_never_execute',
                         'test_session_store_bootstrap_does_not_create_session_files',
                         'test_broken_stdout_stops_without_retry_flush_or_next_job',
                         'test_signals_while_idle_do_not_need_stdin_eof',
                         'test_signal_under_output_pressure_does_not_need_reader_drain'):
                record(name,getattr(original,name))
            for mode in ('cleanup_failure','body_cleanup','setup_cleanup','internal_cleanup_cancel','partial_cleanup'):
                record(mode,lambda mode=mode:cleanup(mode))
            for op in protocol.OPERATIONS:
                for mode in AUTH:
                    record(mode+'.'+op,lambda mode=mode,op=op:authentication(mode,op))
            for mode in ('delivery_projection','fatal_unknown401','fatal_unknown406','fatal_unregistered','fatal_banned'):
                record(mode,lambda mode=mode:secondary_projection(mode))
        run_core_controls()
        check_fingerprint()
    except BaseException as error:
        traceback.print_exc()
        print(json.dumps(dict(status='FAIL',error_type=type(error).__name__,completed=len(RESULTS))),flush=True)
        (FOLDER/'revision4_prebuild_result.json').write_text(json.dumps(dict(status='FAIL',
            completed=RESULTS,processes=PROCESS_COUNT,error_type=type(error).__name__),indent=2)+'\n')
        return 1
    summary=dict(status='PASS',groups=len(RESULTS),processes=PROCESS_COUNT,
                 candidate_sha256=FINGERPRINT['candidates'],results=RESULTS)
    (FOLDER/'revision4_prebuild_result.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',groups=len(RESULTS),processes=PROCESS_COUNT,
                         all_sources_unchanged=True,both_candidates_installed=True)),flush=True)
    return 0


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':
        raise SystemExit(child(Path(sys.argv[2]),sys.argv[3],bool(int(sys.argv[4])),int(sys.argv[5])))
    raise SystemExit(main())
