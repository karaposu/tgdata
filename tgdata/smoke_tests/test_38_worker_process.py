"""Actual worker subprocesses, pipes and signals; synthetic SDK transport only.

All files and policies belong to temporary test directories. No real accounts,
network, login, joins or allowance reset outside those directories.
"""
import asyncio
from contextlib import contextmanager
import json
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
from tgdata import worker_protocol as protocol
from tgdata.smoke_tests import test_37_worker as f

ROOT = Path(__file__).resolve().parents[2]


def child(root, scenario):
    """Test-only bootstrap: replace transport, never execution or process I/O."""
    from tgdata.worker import main, load_inventory, serve, WorkerAccount
    root = Path(root)
    items = {aid: f.fixture(root, aid) for aid in (111, 222)}

    def trace(kind, detail):
        with (root / 'trace.jsonl').open('a') as stream:
            stream.write(json.dumps([kind, detail]) + '\n')

    async def release(wire):
        while not (root / 'release').exists():
            await asyncio.sleep(.01)
        wire.close_release.set()

    def hook(client, wire):
        trace('client', wire.account)
        if scenario == 'held':
            wire.script['GetHistoryRequest'] = [asyncio.get_running_loop().create_future()]
            wire.close_release = asyncio.Event()
            asyncio.create_task(release(wire))
        elif scenario == 'cleanup_failure':
            wire.close_error = OSError(f.SECRET)

    for item in items.values():
        item.trace, item.hook = trace, hook
        item.room.left = True
    item = items[111]
    if scenario == 'partial':
        item.scripts['GetHistoryRequest'] = [
            f.b.f.response([f.b.f.message(n) for n in reversed(range(101, 201))]),
            errors.FloodWaitError(request=None, capture=7200)]
    elif scenario == 'pressure':
        message = f.b.f.message(101)
        message.message = 'x' * (2 * 1024 * 1024)
        item.scripts['GetHistoryRequest'] = [f.b.f.response([message])]
    elif scenario == 'wrong_owner':
        item.actual = 333
    elif scenario == 'unauthenticated':
        item.logged_in = False
        item.responses['GetStateRequest'] = errors.AuthKeyUnregisteredError(request=None)
    elif scenario == 'webview':
        item.join_result = types.messages.ChatInviteJoinResultWebView(
            111, 1152921504606847099, [])

    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         f.install_factory(items):
        if scenario == 'store':
            options = load_inventory(root / 'worker.json')
            options['accounts'] = [WorkerAccount(aid, item.config, session_store=item.store)
                                   for aid, item in items.items()]
            return serve(**options)
        return main(['--config', str(root / 'worker.json')])


def request(ident=1, account=111, operation='read_batch', **params):
    if not params:
        params = dict(group_id='@synthetic_room', after_id='100', limit=2) \
            if operation == 'read_batch' else dict(target='@synthetic_room')
    return (json.dumps(dict(version=1, request_id=ident, account_id=str(account),
                           operation=operation, params=params)) + '\n').encode()


class Process:
    def __init__(self, root, scenario='normal', stock=False):
        self.root, self.buffer = root, bytearray()
        command = [sys.executable, '-m', 'tgdata.worker', '--config', str(root / 'worker.json')] \
            if stock else [sys.executable, '-m', 'tgdata.smoke_tests.test_38_worker_process',
                           '--child', str(root), scenario]
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

    def trace(self):
        path = self.root / 'trace.jsonl'
        if not path.exists():
            return []
        data = path.read_bytes()
        return [json.loads(line) for line in data.split(b'\n')[:-1]]

    def until(self, predicate, timeout=15):
        deadline = time.monotonic() + timeout
        while not predicate(self.trace()):
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
    with setup('cleanup_failure') as (p, budget, join):
        p.line()
        p.send(request() + request(2, 222))
        p.eof()
        value, _ = p.result()
        assert value['ok'] and value['worker_stopping'] and len(value['data']['messages']) == 2
        p.wait(3)
        assert budget.status(111).used == 2 and budget.status(222).used == 0
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
        with setup('held') as (p, budget, join):
            p.line()
            p.send(request() + request(2, 222))
            p.until(lambda rows: ['request', 'GetHistoryRequest'] in rows)
            assert budget.status(111).used == 2
            p.p.send_signal(sig)
            p.until(lambda rows: ['cleanup', 'entered'] in rows)
            p.p.send_signal(sig)
            time.sleep(.1)
            assert p.p.poll() is None and ['cleanup', 'finished'] not in p.trace()
            (p.root / 'release').touch()
            p.wait(128 + sig)
            assert p.trace().count(['cleanup', 'finished']) == 1
            assert budget.status(111).used == 2 and budget.status(222).used == 0
            assert not p.p.stdout.read()  # Cancellation is not a success reply.


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
    return 0 if all(results) else 1


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--child':
        raise SystemExit(child(sys.argv[2], sys.argv[3]))
    raise SystemExit(main())
