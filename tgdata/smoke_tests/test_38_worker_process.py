"""Actual worker subprocesses, pipes and signals; synthetic SDK transport only.

All files and policies belong to temporary test directories. No real accounts,
network, login, joins or allowance reset outside those directories.
"""
import asyncio
from contextlib import contextmanager, ExitStack
import json
import logging
import os
from pathlib import Path
import selectors
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from unittest.mock import patch

from telethon import errors, types
from tgdata import MessageBatch, ReadBudget, JoinBudget
from tgdata import worker, worker_protocol as protocol
from tgdata.connection_engine import ConnectionEngine
from tgdata.smoke_tests import test_37_worker as f

ROOT = Path(__file__).resolve().parents[2]
PROCESS_COUNT = 0


def child(root, scenario, stock=False):
    """Real driver/SDK; synthetic transport and named boundary observations only."""
    parts = scenario.split(':')
    mode = parts[0]
    stop_signal = int(parts[1]) if len(parts) > 1 else int(signal.SIGTERM)
    root = Path(root)
    items = {} if stock else {aid: f.fixture(root, aid) for aid in (111, 222)}
    old_handlers = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    old_logging = logging.root.manager.disable

    def trace(kind, detail):
        # Keep source activity separate from test-only lifecycle observations.
        name = 'trace.jsonl' if kind in ('client', 'request', 'cleanup') else 'evidence.jsonl'
        with (root / name).open('a') as stream:
            stream.write(json.dumps([kind, detail]) + '\n')

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
            sender.close_error = OSError(f.SECRET)
        elif mode == 'internal_cleanup_cancel':
            sender.close_error = asyncio.CancelledError(f.SECRET)
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
                f.b.f.response([f.b.f.message(n) for n in reversed(range(101, 201))]),
                errors.FloodWaitError(request=None, capture=7200)]
        elif mode == 'pressure':
            message = f.b.f.message(101)
            message.message = 'x' * (2 * 1024 * 1024)
            item.scripts['GetHistoryRequest'] = [f.b.f.response([message])]
        elif mode == 'wrong_owner':
            item.actual = 333
        elif mode == 'unauthenticated':
            item.logged_in = False
            item.responses['GetStateRequest'] = errors.AuthKeyUnregisteredError(request=None)
        elif mode == 'webview':
            item.join_result = types.messages.ChatInviteJoinResultWebView(111, 1152921504606847099, [])
        elif mode == 'body_cleanup':
            item.scripts['GetHistoryRequest'] = [errors.ChannelPrivateError(request=None)]
        elif mode == 'setup_cleanup':
            item.connect_error = LookupError(f.SECRET)
        elif mode.startswith('auth_') or mode == 'delivery_projection':
            code, text = (401, f.SECRET) if mode == 'delivery_projection' else f.AUTH_CASES[mode][:2]
            item.scripts['GetUsersRequest'] = [f.sdk_error(code, text)]

    real_create = asyncio.BaseEventLoop.create_task
    def create(loop, coro, *args, **kwargs):
        if mode == 'before_task' and getattr(coro, '__qualname__', '') == 'Worker.execute':
            trace('publication', 'before-create')
            os.kill(os.getpid(), stop_signal)
        task = real_create(loop, coro, *args, **kwargs)
        if mode == 'publication' and getattr(coro, '__qualname__', '') == 'Worker.execute':
            trace('publication', 'created-before-return')
            os.kill(os.getpid(), stop_signal)
        return task

    real_close = worker.Worker.close
    async def close(instance):
        if mode == 'finalize':
            event = asyncio.Event()
            release_on_command(event)
            trace('finalize', 'entered')
            await event.wait()  # Named pause, then actual facade close.
        await real_close(instance)
        trace('finalize', 'finished')

    real_loop_close = asyncio.BaseEventLoop.close
    def loop_close(loop):
        pending = len([t for t in asyncio.all_tasks(loop) if not t.done()])
        real_loop_close(loop)
        trace('loop', dict(pending=pending, closed=loop.is_closed()))

    real_encoder = protocol.encode_frame
    def encoder(value, **options):
        if mode == 'delivery_projection' and value.get('kind') == 'result' and (
                value.get('error') or {}).get('category') == 'authentication_required':
            raise protocol.WorkerError('delivery_failed')  # Explicit post-source serializer fault.
        return real_encoder(value, **options)

    with ExitStack() as stack:
        stack.enter_context(patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')))
        stack.enter_context(patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')))
        stack.enter_context(patch.object(asyncio.BaseEventLoop, 'create_task', create))
        stack.enter_context(patch.object(asyncio.BaseEventLoop, 'close', loop_close))
        stack.enter_context(patch.object(worker.Worker, 'close', close))
        stack.enter_context(patch.object(protocol, 'encode_frame', encoder))
        if items:
            stack.enter_context(f.install_factory(items))
        if mode.startswith('fatal_'):
            # Shared encoder control, not source/startup authentication.
            code, text = f.AUTH_CASES[mode.replace('fatal_', 'auth_', 1)][:2]
            wrapped = ConnectionEngine._auth_required('private', f.sdk_error(code, text), False)
            worker._fatal(wrapped, worker._raw_output(None))
            result = 2
        elif mode == 'store':
            options = worker.load_inventory(root / 'worker.json')
            options['accounts'] = [worker.WorkerAccount(aid, item.config, session_store=item.store)
                                   for aid, item in items.items()]
            result = worker.serve(**options)
        else:
            result = worker.main(['--config', str(root / 'worker.json')])
    trace('clients_final', [dict(account=item.actual, closed=c._sender.closed,
          disconnect_attempts=c._sender.close_calls) for item in items.values() for c in item.clients])
    trace('restored', all(signal.getsignal(s) == h for s, h in old_handlers.items())
          and logging.root.manager.disable == old_logging)
    return result


def request(ident=1, account=111, operation='read_batch', **params):
    if not params:
        params = dict(group_id='@synthetic_room', after_id='100', limit=2) \
            if operation == 'read_batch' else dict(target='@synthetic_room')
    return (json.dumps(dict(version=1, request_id=ident, account_id=str(account),
                           operation=operation, params=params)) + '\n').encode()


class Process:
    def __init__(self, root, scenario='normal', stock=False):
        global PROCESS_COUNT
        PROCESS_COUNT += 1
        self.root, self.buffer = root, bytearray()
        command = [sys.executable, '-m', 'tgdata.smoke_tests.test_38_worker_process',
                   '--child', str(root), scenario, str(int(stock))]
        self.p = subprocess.Popen(command, cwd=str(ROOT), stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        self.stderr = b''

    def send(self, value):
        view = memoryview(value)
        while view:
            count = self.p.stdin.write(view)
            assert count and count > 0
            view = view[count:]

    def eof(self):
        self.p.stdin.close()
        self.p.stdin = None

    def line(self, timeout=15):
        deadline = time.monotonic() + timeout
        with selectors.DefaultSelector() as selector:
            selector.register(self.p.stdout, selectors.EVENT_READ)
            while b'\n' not in self.buffer:
                remaining = deadline - time.monotonic()
                assert remaining > 0 and selector.select(remaining), 'worker reply timed out'
                data = os.read(self.p.stdout.fileno(), 65536)
                assert data, 'worker exited before complete reply'
                self.buffer.extend(data)
        raw, _, tail = self.buffer.partition(b'\n')
        self.buffer = bytearray(tail)
        assert f.SECRET.encode() not in raw
        return json.loads(raw)

    def result(self):
        events = []
        while True:
            value = self.line()
            if value['kind'] != 'health':
                assert value['kind'] == 'result'
                return value, events
            events.append(value)

    def wait(self, code=0, timeout=15):
        assert self.p.wait(timeout=timeout) == code, 'unexpected worker exit code'
        self.stderr += self.p.stderr.read()
        assert not self.stderr, self.stderr.decode(errors='replace')
        rows = self.observations()
        assert ['restored', True] in rows
        assert all(row[1]['pending'] == 0 and row[1]['closed'] for row in rows if row[0] == 'loop')
        assert f.SECRET.encode() not in self.buffer

    def trace(self):
        return self._rows('trace.jsonl')

    def observations(self):
        return self.trace() + self._rows('evidence.jsonl')

    def _rows(self, name):
        path = self.root / name
        if not path.exists():
            return []
        data = path.read_bytes()
        return [json.loads(line) for line in data.split(b'\n')[:-1]]

    def until(self, predicate, timeout=15):
        deadline = time.monotonic() + timeout
        while not predicate(self.observations()):
            assert self.p.poll() is None and time.monotonic() < deadline, 'trace timed out'
            time.sleep(.01)

    def dispose(self):
        if self.p.poll() is None:
            self.p.kill()
        self.p.wait(timeout=5)
        for stream in (self.p.stdin, self.p.stdout, self.p.stderr):
            if stream is not None:
                stream.close()


@contextmanager
def setup(scenario='normal', stock=False, edit=None):
    with tempfile.TemporaryDirectory(prefix='tgdata_worker_process_') as directory:
        root = Path(directory)
        budget = ReadBudget(root / 'read.sqlite3')
        join = JoinBudget(root / 'join.sqlite3', create=True)
        for aid in (111, 222):
            f.fixture(root, aid)
            budget.configure(aid, 1000)
            join.configure(aid, 5)
        manifest = dict(version=1, worker_id='process-test', read_budget='read.sqlite3',
                        join_budget='join.sqlite3', accounts=[
            dict(account_id=str(aid), config_path='account-{}.ini'.format(aid)) for aid in (111, 222)])
        if edit:
            edit(root, manifest)
        (root / 'worker.json').write_text(json.dumps(manifest))
        process = Process(root, scenario, stock)
        try:
            yield process, budget, join
        finally:
            process.dispose()


def test_stock_empty_inventory_ready_eof_and_module_help():
    with setup(stock=True, edit=lambda root, m: m.update(accounts=[])) as (p, budget, join):
        ready = p.line()
        assert ready['kind'] == 'ready' and ready['account_count'] == 0
        assert ready['limits']['request_bytes'] == 16384 and not p.trace()
        p.eof()
        p.wait()
        module = subprocess.run([sys.executable, '-m', 'tgdata.worker', '--config',
                                 str(p.root / 'worker.json')], cwd=str(ROOT), input=b'',
                                capture_output=True, timeout=15)
        assert module.returncode == 0 and not module.stderr
        assert json.loads(module.stdout)['account_count'] == 0
    help_run = subprocess.run([sys.executable, '-m', 'tgdata.worker', '--help'],
                              cwd=str(ROOT), capture_output=True, timeout=15)
    assert help_run.returncode == 0 and b'--config' in help_run.stdout and not help_run.stderr


def test_all_four_operations_two_accounts_and_eof():
    with setup() as (p, budget, join):
        ready = p.line()
        assert ready['account_ids'] == ['111', '222'] and not p.trace()
        p.send(request() + request(2, 222, 'lookup_group') +
               request(3, 111, 'check_group_access') + request(4, 111, 'join_group'))
        p.eof()
        results = [p.result()[0] for _ in range(4)]
        assert all(r['ok'] for r in results), results
        assert [r['request_id'] for r in results] == [1, 2, 3, 4]
        assert len(MessageBatch(results[0]['data']).messages) == 2
        assert results[1]['account_id'] == '222'
        assert results[2]['data']['status'] == 'readable'
        assert results[3]['data']['status'] == 'joined'
        p.wait()
        assert budget.status(111).used == 3 and budget.status(222).used == 0
        assert join.status(111).used == 1
        assert p.trace().count(['cleanup', 'finished']) == 4
        assert len([row for row in p.trace() if row[0] == 'client']) == 4


def test_partial_batch_health_correlation_and_charge_survive_json():
    with setup('partial') as (p, budget, join):
        ready = p.line()
        p.send(request(group_id='@synthetic_room', after_id='100', limit=200))
        p.eof()
        value, events = p.result()
        assert value['error']['wait_seconds'] == 7200
        batch = MessageBatch(value['partial_result'])
        assert len(batch.messages) == 100 and budget.status(111).used == 200
        assert len(events) == 1 and events[0]['request_id'] == value['request_id'] == 1
        assert events[0]['account_id'] == '111'
        assert events[0]['instance_id'] == value['instance_id'] == ready['instance_id']
        p.wait()


def test_webview_identifiers_survive_javascript_exactly():
    with setup('webview') as (p, budget, join):
        p.line()
        p.send(request(operation='join_group'))
        p.eof()
        value, _ = p.result()
        assert value['ok'] and value['data']['status'] == 'interaction_required'
        assert value['data']['query_id'] == '1152921504606847099'
        assert value['data']['bot_id'] == '111'
        if shutil.which('node'):
            check = subprocess.run(['node', '-e',
                "let s='';process.stdin.on('data',x=>s+=x).on('end',()=>{"
                "const q=JSON.parse(s).data.query_id;process.exit(typeof q==='string' && "
                "BigInt(q)===1152921504606847099n ? 0 : 1)})"],
                input=json.dumps(value).encode(), capture_output=True, timeout=10)
            assert check.returncode == 0
        p.wait()
        assert join.status(111).used == 1


def test_wrong_identity_and_missing_auth_never_read_or_login():
    for scenario, category in [('wrong_owner', 'identity_mismatch'),
                                ('unauthenticated', 'authentication_required')]:
        with setup(scenario) as (p, budget, join):
            p.line()
            p.send(request())
            p.eof()
            value, _ = p.result()
            assert not value['ok'] and value['error']['category'] == category, value
            p.wait()
            assert budget.status(111).used == 0 and join.status(111).used == 0
            assert not any(row[1] in ('GetHistoryRequest', 'JoinChannelRequest',
                                     'ImportChatInviteRequest', 'SendCodeRequest') for row in p.trace())


def test_bad_complete_frames_and_reused_ids_are_local():
    with setup() as (p, budget, join):
        p.line()
        malformed = [b'\xff\n', b'[]\n', b'{"version":1,"version":1}\n',
                     request(limit=True, group_id='@room'), request(),
                     request(2, operation='arbitrary'), request(3, 333),
                     request(4, group_id='@room', output_path=f.SECRET)]
        for raw in malformed:
            p.send(raw)
            result, events = p.result()
            assert not result['ok'] and not events and not result['worker_stopping']
        assert not p.trace() and budget.status(111).used == 0
        p.send(request(5))
        p.eof()
        assert p.result()[0]['ok']
        p.wait()


def test_truncated_and_oversized_frames_never_execute():
    for raw, error in [(request()[:-1], 'incomplete_frame'),
                       (b'x' * (protocol.MAX_REQUEST_BYTES + 1) + b'\n', 'frame_too_large')]:
        with setup() as (p, budget, join):
            p.line()
            p.send(raw)
            p.eof()
            value, _ = p.result()
            assert value['error']['code'] == error and value['worker_stopping']
            p.wait(2)
            assert not p.trace() and budget.status(111).used == 0


def test_invalid_startup_is_safe_and_source_free():
    def missing_policy(root, manifest):
        manifest['accounts'][0]['account_id'] = '333'
    def alias(root, manifest):
        text = (root / 'account-111.ini').read_text()
        (root / 'account-222.ini').write_text(text)
    cases = [lambda root, m: m.update(version=2),
             lambda root, m: m.update(read_budget=f.SECRET),
             lambda root, m: m.update(worker_id=f.SECRET + '\n'),
             lambda root, m: m['accounts'][0].update(config_path=f.SECRET),
             lambda root, m: m['accounts'].append(m['accounts'][0]),
             missing_policy, alias]
    for edit in cases:
        with setup(stock=True, edit=edit) as (p, budget, join):
            value = p.line()
            assert value['kind'] == 'fatal' and value['worker_stopping']
            p.wait(2)
            assert not p.trace() and not list(p.root.glob('*.session'))
            assert budget.status(111).used == 0
    result = subprocess.run([sys.executable, '-m', 'tgdata.worker', '--unknown', f.SECRET],
                            cwd=str(ROOT), capture_output=True, timeout=15)
    assert result.returncode == 2 and not result.stderr and f.SECRET.encode() not in result.stdout


def test_session_store_bootstrap_does_not_create_session_files():
    with setup('store') as (p, budget, join):
        p.line()
        p.send(request() + request(2, 222))
        p.eof()
        assert p.result()[0]['ok'] and p.result()[0]['ok']
        p.wait()
        assert not list(p.root.glob('*.session'))
        assert budget.status(111).used == budget.status(222).used == 2


def test_cleanup_failure_keeps_result_then_exits_without_successor():
    for mode in ('cleanup_failure', 'body_cleanup', 'setup_cleanup',
                 'internal_cleanup_cancel', 'partial_cleanup'):
        with setup(mode) as (p, budget, join):
            p.line()
            first = request(group_id='@room', after_id='100', limit=200) \
                if mode == 'partial_cleanup' else request()
            p.send(first + request(2, 222))
            p.eof()
            value, _ = p.result()
            assert value['worker_stopping']
            assert value['ok'] is (mode in ('cleanup_failure', 'internal_cleanup_cancel'))
            if value['ok']:
                assert len(value['data']['messages']) == 2
            if mode == 'body_cleanup':
                assert value['error']['type'] == 'ChannelPrivateError'
            if mode == 'setup_cleanup':
                assert value['error']['type'] == 'LookupError'
            if mode == 'partial_cleanup':
                assert value['error']['wait_seconds'] == 7200
                assert len(MessageBatch(value['partial_result']).messages) == 100
            p.wait(3)
            final = next(row[1] for row in p.observations() if row[0] == 'clients_final')
            assert len(final) == 1 and final[0]['disconnect_attempts'] == 1 and not final[0]['closed']
            assert budget.status(111).used == (0 if mode == 'setup_cleanup' else
                                             200 if mode == 'partial_cleanup' else 2)
            assert budget.status(222).used == join.status(111).used == 0
            assert [row for row in p.trace() if row[0] == 'client'] == [['client', 111]]


def test_broken_stdout_stops_without_retry_flush_or_next_job():
    with setup() as (p, budget, join):
        p.line()
        p.p.stdout.close()
        p.send(request() + request(2, 222))
        p.eof()
        p.wait(3)
        assert budget.status(111).used == 2 and budget.status(222).used == 0
        assert p.trace().count(['cleanup', 'finished']) == 1


def test_signals_while_idle_do_not_need_stdin_eof():
    for sig in (signal.SIGINT, signal.SIGTERM):
        with setup() as (p, budget, join):
            p.line()
            p.p.send_signal(sig)
            p.wait(128 + sig)
            assert not p.trace() and budget.status(111).used == 0


def test_signal_under_output_pressure_does_not_need_reader_drain():
    for sig in (signal.SIGINT, signal.SIGTERM):
        with setup('pressure') as (p, budget, join):
            p.line()
            p.send(request(group_id='@room', after_id='100', limit=1) + request(2, 222))
            p.until(lambda rows: ['cleanup', 'finished'] in rows)
            # The encoded frame exceeds the pipe capacity. Do not read or close
            # stdout: exit must interrupt the raw write, including finalization.
            time.sleep(.1)
            assert p.p.poll() is None and budget.status(222).used == 0
            p.p.send_signal(sig)
            p.wait(128 + sig, timeout=5)
            assert budget.status(111).used == 1 and budget.status(222).used == 0
            assert len([row for row in p.trace() if row[0] == 'client']) == 1
            tail = p.p.stdout.read()
            assert tail and not tail.endswith(b'\n')  # No terminal acknowledgment.


def test_repeated_active_signals_wait_for_native_cleanup():
    for sig in (signal.SIGINT, signal.SIGTERM):
        lifecycle('held', sig)


def lifecycle(mode, sig):
    with setup(mode + ':' + str(int(sig))) as (p, budget, join):
        assert p.line()['kind'] == 'ready'
        p.send(request() + (b'' if mode == 'finalize' else request(2, 222)))
        if mode == 'finalize':
            assert p.result()[0]['ok']
            p.eof()
            p.until(lambda rows: ['finalize', 'entered'] in rows)
        elif mode not in ('before_task', 'publication'):
            p.until(lambda rows: ['request', 'GetHistoryRequest'] in rows and
                    any(r[0] == 'select' and r[1] is not None and r[1] > 1 for r in rows))
        cancel_signal = signal.SIGUSR2 if mode == 'caller_cancel' else sig
        if mode not in ('before_task', 'publication'):
            p.p.send_signal(cancel_signal)
        if mode in ('held', 'finalize', 'caller_cancel'):
            if mode != 'finalize':
                p.until(lambda rows: ['cleanup', 'entered'] in rows)
            p.p.send_signal(cancel_signal)
            time.sleep(.15)  # Parent observation only; no child polling timer.
            assert p.p.poll() is None
            assert ['finalize' if mode == 'finalize' else 'cleanup', 'finished'] not in p.observations()
            p.p.send_signal(signal.SIGUSR1)  # Explicit release of the held SDK/event boundary.
        p.wait(3 if mode == 'caller_cancel' else 128 + sig, timeout=5)
        rows = p.observations()
        expected = 0 if mode in ('before_task', 'publication') else 1
        assert len([r for r in rows if r[0] == 'client']) == expected
        assert budget.status(111).used == 2 * expected
        assert budget.status(222).used == join.status(111).used == 0
        assert rows.count(['cleanup', 'finished']) == expected
        assert ['finalize', 'finished'] in rows
        assert not p.p.stdout.read()  # Interrupted jobs never become success replies.


def test_active_signal_wakes_quiet_selector():
    for sig in (signal.SIGINT, signal.SIGTERM):
        lifecycle('quiet', sig)


def test_stop_before_task_creation_never_starts_source():
    for sig in (signal.SIGINT, signal.SIGTERM):
        lifecycle('before_task', sig)


def test_stop_before_task_publication_never_starts_source():
    for sig in (signal.SIGINT, signal.SIGTERM):
        lifecycle('publication', sig)


def test_repeated_signals_during_finalization_preserve_cleanup():
    for sig in (signal.SIGINT, signal.SIGTERM):
        lifecycle('finalize', sig)


def test_repeated_direct_cancellation_waits_for_native_cleanup():
    lifecycle('caller_cancel', signal.SIGTERM)


def authentication_cases(operation):
    for mode in f.AUTH_CASES:
        with setup(mode) as (p, budget, join):
            p.line()
            p.send(request(operation=operation))
            p.eof()
            value, events = p.result()
            assert not value['ok'] and not events
            f.assert_auth_error(value['error'], mode)
            p.wait()
            rows = p.trace()
            assert rows.count(['cleanup', 'finished']) == 1
            f.assert_auth_source_free([r[1] for r in rows if r[0] == 'request'])
            assert budget.status(111).used == join.status(111).used == 0


def test_sdk_authentication_read_batch():
    authentication_cases('read_batch')


def test_sdk_authentication_lookup_group():
    authentication_cases('lookup_group')


def test_sdk_authentication_check_group_access():
    authentication_cases('check_group_access')


def test_sdk_authentication_join_group():
    authentication_cases('join_group')


def test_delivery_failure_omits_unknown_authentication_text():
    with setup('delivery_projection') as (p, budget, join):
        p.line()
        p.send(request() + request(2, 222))
        p.eof()
        value, events = p.result()
        assert value['partial_omitted'] and value['worker_stopping'] and not events
        assert value['error']['code'] == 'delivery_failed'
        f.assert_auth_error(value['source_error'], 'auth_unknown401')
        p.wait(3)
        assert p.trace().count(['cleanup', 'finished']) == 1
        f.assert_auth_source_free([r[1] for r in p.trace() if r[0] == 'request'])
        assert budget.status(111).used == budget.status(222).used == join.status(111).used == 0


def test_fatal_authentication_projection():
    for mode in ('fatal_unknown401', 'fatal_unknown406', 'fatal_unregistered', 'fatal_banned'):
        with setup(mode, stock=True) as (p, budget, join):
            value = p.line()
            assert value['kind'] == 'fatal' and value['worker_stopping']
            assert value['error']['category'] == 'configuration_error'
            detail = dict(value['error'], category='authentication_required')
            f.assert_auth_error(detail, mode.replace('fatal_', 'auth_', 1))
            p.wait(2)
            assert not p.trace()
            assert budget.status(111).used == budget.status(222).used == join.status(111).used == 0


def main():
    tests = [value for name, value in globals().items() if name.startswith('test_')]
    results = []
    for test in tests:
        try:
            test()
            print('PASS', test.__name__, flush=True)
            results.append(True)
        except Exception:
            traceback.print_exc()
            print('FAIL', test.__name__, flush=True)
            results.append(False)
    print('Passed: {}/{}'.format(sum(results), len(results)), flush=True)
    print('Controlled worker subprocesses:', PROCESS_COUNT, flush=True)
    return 0 if all(results) else 1


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--child':
        raise SystemExit(child(sys.argv[2], sys.argv[3], bool(int(sys.argv[4]))))
    raise SystemExit(main())
