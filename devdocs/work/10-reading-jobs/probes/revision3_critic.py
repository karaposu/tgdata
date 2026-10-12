"""Targeted r3 review candidates; actual processes/SDK, no production file edits.

This is not the full Step1 prebuild. It probes publication/finalization edges and
diagnostic call sites; raw-pipe/startup/source-fault matrix remains mandatory.
"""
import asyncio
import inspect
import io
import json
import logging
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision3_feasibility as feasibility
from tgdata import worker, ReadBudget
from tgdata import worker_protocol as protocol
from tgdata.connection_engine import ConnectionEngine, AuthRequiredError
from tgdata.smoke_tests import test_37_worker as f
from tgdata.smoke_tests import test_38_worker_process as p
from telethon import errors, types, functions
from telethon.extensions import BinaryReader


def candidate():
    source = inspect.getsource(worker.serve)
    replacements = [
        ('    code = 0\n', '    code = 0\n    creating = finalizing = False\n'),
        ('        stopping_signal = signum\n',
         '        stopping_signal = signum\n'
         '        if worker is not None:\n            worker.stopping = True\n'
         '        if creating or finalizing:\n'
         '            if loop is not None and not loop.is_closed():\n'
         '                loop.call_soon_threadsafe(lambda: None)\n'
         '            return\n'),
        ('            # Do not interrupt a retained cleanup waiter with repeated cancels.\n            active.cancel()\n',
         '            active.cancel()\n            loop.call_soon_threadsafe(lambda: None)\n'),
        ('            active = loop.create_task(worker.execute(job))\n',
         '            creating = True\n'
         '            try:\n                active = loop.create_task(worker.execute(job))\n'
         '            finally:\n                creating = False\n'
         '            if stopping_signal is not None:\n                active.cancel()\n'),
        ('    finally:\n        if loop is not None:\n',
         '    finally:\n        finalizing = True\n'
         '        if worker is not None:\n            worker.stopping = True\n'
         '        if loop is not None:\n')]
    for old, new in replacements:
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    namespace = dict(worker.__dict__)
    exec(compile(source, '<r3-boundary-candidate>', 'exec'), namespace)
    return namespace['serve']


def child(root, mode, stop_signal):
    root = Path(root)
    item = f.fixture(root, 111)
    old_handlers = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    old_logging = logging.root.manager.disable
    def trace(kind, detail):
        with (root/'trace.jsonl').open('a') as stream:
            stream.write(json.dumps([kind, detail])+'\n')
    def release_on_command(event):
        loop = asyncio.get_running_loop()
        signal.signal(signal.SIGUSR1, lambda s, frame: loop.call_soon_threadsafe(event.set))
    def hook(client, sender):
        trace('client', 111)
        loop = asyncio.get_running_loop()
        if mode in ('quiet', 'held'):
            sender.script['GetHistoryRequest'] = [loop.create_future()]
        if mode == 'held':
            sender.close_release = asyncio.Event()
            release_on_command(sender.close_release)
        original = loop._selector.select
        def selected(timeout=None):
            trace('select', timeout)
            return original(timeout)
        loop._selector.select = selected
    item.trace, item.hook = trace, hook
    original_create = asyncio.BaseEventLoop.create_task
    def create(loop, coro, *args, **kwargs):
        result = original_create(loop, coro, *args, **kwargs)
        if mode == 'publication' and getattr(coro, '__qualname__', '') == 'Worker.execute':
            trace('publication', 'task-created-reference-not-returned')
            os.kill(os.getpid(), stop_signal)
        return result
    original_close = worker.Worker.close
    async def close(instance):
        if mode == 'finalize':
            event = asyncio.Event()
            release_on_command(event)
            trace('finalize', 'entered')
            await event.wait()  # Named boundary pause, then the real close below.
        await original_close(instance)
        trace('finalize', 'finished')
    with patch.object(worker, 'serve', candidate()), \
         patch.object(asyncio.BaseEventLoop, 'create_task', create), \
         patch.object(worker.Worker, 'close', close), f.install_factory({111:item}), \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        code = worker.main(['--config', str(root/'worker.json')])
    trace('restored', all(signal.getsignal(s) == h for s,h in old_handlers.items())
          and logging.root.manager.disable == old_logging)
    return code


def process_case(mode, sig):
    with tempfile.TemporaryDirectory(prefix='tgdata_r3_critic_') as directory:
        root = Path(directory)
        budget = ReadBudget(root/'read.sqlite3');budget.configure(111, 20)
        f.fixture(root, 111)
        (root/'worker.json').write_text(json.dumps(dict(version=1, worker_id='critic',
            read_budget='read.sqlite3', accounts=[dict(account_id='111',config_path='account-111.ini')])))
        process = p.Process.__new__(p.Process)
        process.root, process.buffer, process.stderr = root, bytearray(), b''
        process.p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--child',
            str(root), mode, str(int(sig))], cwd=str(ROOT), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        try:
            assert process.line()['kind'] == 'ready'
            process.send(p.request() + (b'' if mode == 'finalize' else p.request(2)))
            if mode == 'finalize':
                assert process.result()[0]['ok']
                process.eof()
                process.until(lambda rows:['finalize','entered'] in rows)
            elif mode != 'publication':
                process.until(lambda rows:['request','GetHistoryRequest'] in rows
                    and any(row[0]=='select' and row[1] is not None and row[1]>1 for row in rows))
            if mode != 'publication':
                process.p.send_signal(sig)
            if mode in ('held', 'finalize'):
                if mode == 'held':
                    process.until(lambda rows:['cleanup','entered'] in rows)
                process.p.send_signal(sig)
                time.sleep(.15)  # Parent only; no polling helper in child.
                assert process.p.poll() is None
                if mode == 'held':assert ['cleanup','finished'] not in process.trace()
                else:assert ['finalize','finished'] not in process.trace()
                process.p.send_signal(signal.SIGUSR1)  # Explicit release, after proving retention.
            process.wait(128+sig, timeout=5)
            rows=process.trace()
            clients=sum(row[0]=='client' for row in rows)
            assert clients == (0 if mode=='publication' else 1)
            assert budget.status(111).used == (0 if mode=='publication' else 2)
            assert ['restored',True] in rows and ['finalize','finished'] in rows
            if clients:assert ['cleanup','finished'] in rows
            print(json.dumps(dict(case=mode,signal=sig.name,exit=process.p.returncode,
                clients=clients,charge=budget.status(111).used,restored=True,
                cleanup_finished=bool(clients),stderr_empty=True)),flush=True)
        finally:
            process.dispose()


def sdk_error(code, text):
    with BinaryReader(bytes(types.RpcError(code, text))) as reader:
        reply=reader.tgread_object()
    return errors.rpc_message_to_error(reply, functions.users.GetUsersRequest([types.InputUserSelf()]))


async def diagnostics():
    sentinel='R3_CRITIC_PRIVATE_DIAGNOSTIC'
    projected, known=feasibility.diagnostic_candidate()
    with patch.object(protocol,'describe_error',projected), \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        for op in protocol.OPERATIONS:
            for code,text in ((401,sentinel),(406,sentinel),(401,'SESSION_REVOKED')):
                async with f.Setup() as setup:
                    setup.items[111].scripts['GetUsersRequest']=[sdk_error(code,text)]
                    result,events=await setup.call(op)
                    assert sentinel not in json.dumps(result) and not result['ok']
                    assert result['error'].get('reason')==(text if text in known else None)
                    assert not events and setup.budget.status(111).used==setup.join.status(111).used==0
                    assert setup.items[111].clients[-1]._sender.closed
        original=protocol.encode_frame
        def refuse_terminal(value,**kwargs):
            if value.get('kind')=='result' and (value.get('error') or {}).get('category')=='authentication_required':
                raise protocol.WorkerError('delivery_failed')
            return original(value,**kwargs)
        async with f.Setup() as setup:
            setup.items[111].scripts['GetUsersRequest']=[sdk_error(401,sentinel)]
            with patch.object(protocol,'encode_frame',refuse_terminal):
                value,_=await setup.call()
            assert value['partial_omitted'] and value['worker_stopping']
            assert 'reason' not in value['source_error'] and sentinel not in json.dumps(value)
        output=io.BytesIO()
        worker._fatal(ConnectionEngine._auth_required('private',sdk_error(406,sentinel),False),output)
        value=json.loads(output.getvalue())
        assert value['kind']=='fatal' and 'reason' not in value['error'] and sentinel.encode() not in output.getvalue()
    print('PASS12 SDK/Worker auth routes + delivery-error projection + fatal projection; no raw sentinel',flush=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':
        raise SystemExit(child(sys.argv[2],sys.argv[3],int(sys.argv[4])))
    for mode in ('quiet','held','publication','finalize'):
        for sig in (signal.SIGINT,signal.SIGTERM):
            process_case(mode,sig)
    logging.disable(logging.CRITICAL)
    asyncio.run(diagnostics())
    print('PASS8 targeted process histories and14 diagnostic histories; full prebuild still pending',flush=True)
