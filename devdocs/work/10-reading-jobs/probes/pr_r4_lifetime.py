"""Fresh second PR review: real source/cleanup/loop boundaries, no child timer."""
import asyncio
from contextlib import ExitStack
import json
import logging
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata import worker
from tgdata.smoke_tests import test_37_worker as core
from tgdata.smoke_tests import test_38_worker_process as process


def child(root, mode, first):
    root = Path(root)
    items = {aid: core.fixture(root, aid) for aid in (111, 222)}
    old_handlers = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    old_logging = logging.root.manager.disable

    def trace(kind, value):
        name = 'trace.jsonl' if kind in ('client', 'request', 'cleanup') else 'evidence.jsonl'
        with (root / name).open('a') as stream:
            stream.write(json.dumps([kind, value]) + '\n')

    def hook(client, sender):
        trace('client', sender.account)
        loop = asyncio.get_running_loop()
        if mode in ('quiet_mixed', 'held_success', 'held_failure'):
            sender.close_release = asyncio.Event()
            signal.signal(signal.SIGUSR1, lambda s, f: loop.call_soon_threadsafe(sender.close_release.set))
        if mode == 'quiet_mixed':
            sender.script['GetHistoryRequest'] = [loop.create_future()]
        if mode == 'held_failure':
            sender.close_error = OSError(core.SECRET)
        select = loop._selector.select
        def observed(timeout=None):
            trace('select', timeout)
            return select(timeout)
        loop._selector.select = observed

    for item in items.values():
        item.trace, item.hook = trace, hook

    real_signal = signal.signal
    def install(sig, handler):
        if sig in old_handlers and getattr(handler, '__name__', '') == 'stop':
            def observed(signum, frame):
                try:
                    return handler(signum, frame)
                finally:
                    # Observe the actual latch; nested handlers can finish out of order.
                    state = dict(zip(handler.__code__.co_freevars,
                                     (cell.cell_contents for cell in handler.__closure__)))
                    trace('signal_handled', dict(signum=signum, owner=state['stopping_signal']))
            return real_signal(sig, observed)
        return real_signal(sig, handler)

    real_write = worker._write_all
    def write(stream, data):
        if mode == 'before_reply' and b'"kind":"result"' in data:
            trace('boundary', 'before_result_write')
            os.kill(os.getpid(), first)
        return real_write(stream, data)

    real_close = asyncio.BaseEventLoop.close
    def close(loop):
        pending = sum(not task.done() for task in asyncio.all_tasks(loop))
        real_close(loop)
        trace('loop', dict(pending=pending, closed=loop.is_closed()))
        if mode == 'closed_loop':
            trace('boundary', 'after_loop_close')
            os.kill(os.getpid(), first)

    with ExitStack() as stack:
        stack.enter_context(patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')))
        stack.enter_context(patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')))
        stack.enter_context(core.install_factory(items))
        stack.enter_context(patch.object(signal, 'signal', install))
        stack.enter_context(patch.object(worker, '_write_all', write))
        stack.enter_context(patch.object(asyncio.BaseEventLoop, 'close', close))
        result = worker.main(['--config', str(root / 'worker.json')])
    trace('final', [dict(account=aid, closed=c._sender.closed, attempts=c._sender.close_calls)
                    for aid, item in items.items() for c in item.clients])
    trace('restored', old_logging == logging.root.manager.disable and all(
        signal.getsignal(s) == h for s, h in old_handlers.items()))
    return result


class Process(process.Process):
    def __init__(self, root, scenario='normal', stock=False):
        mode, first = scenario.split(':')
        self.root, self.buffer, self.stderr = root, bytearray(), b''
        self.p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--child',
            str(root), mode, first], cwd=str(ROOT), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)


def history(mode, first):
    repeat = signal.SIGTERM if first == signal.SIGINT else signal.SIGINT
    with process.setup(mode + ':' + str(int(first))) as (p, budget, join):
        assert p.line()['kind'] == 'ready'
        if mode == 'closed_loop':
            p.send(process.request())
            assert p.result()[0]['ok']
            p.eof()
        else:
            p.send(process.request() + process.request(2, 222))
        if mode == 'quiet_mixed':
            p.until(lambda rows: ['request', 'GetHistoryRequest'] in rows and any(
                row[0] == 'select' and row[1] is not None and row[1] > 1 for row in rows))
            p.p.send_signal(first)
            p.until(lambda rows: ['cleanup', 'entered'] in rows)
        elif mode in ('held_success', 'held_failure'):
            p.until(lambda rows: ['cleanup', 'entered'] in rows)
            assert budget.status(111).used == 2  # Source finished before first stop.
            p.p.send_signal(first)
        if mode in ('quiet_mixed', 'held_success', 'held_failure'):
            p.until(lambda rows: ['signal_handled', dict(signum=int(first), owner=int(first))] in rows)
            p.p.send_signal(repeat)
            time.sleep(.15)  # Parent observation only; no child progress task.
            assert p.p.poll() is None and ['cleanup', 'finished'] not in p.trace()
            p.p.send_signal(signal.SIGUSR1)
        p.wait(128 + first, timeout=5)
        rows = p.observations()
        assert budget.status(111).used == 2 and budget.status(222).used == join.status(111).used == 0
        final = next(row[1] for row in rows if row[0] == 'final')
        assert final == [dict(account=111, closed=mode != 'held_failure', attempts=1)]
        assert not p.p.stdout.read()  # No successor or interrupted terminal reply.
        return dict(mode=mode, first=first.name, repeat=repeat.name if mode.startswith(('quiet','held')) else None,
                    exit=p.p.returncode, charge=2, successor=False, cleanup_attempts=1,
                    disconnected=final[0]['closed'], restored=True, pending_tasks=0)


def coalescing_control():
    # Sending order is not dispatch order when different signals are pending.
    with process.setup('held_success:' + str(int(signal.SIGTERM))) as (p, budget, join):
        p.line(); p.send(process.request())
        p.until(lambda rows: ['cleanup', 'entered'] in rows)
        p.p.send_signal(signal.SIGTERM)
        p.p.send_signal(signal.SIGINT)
        p.until(lambda rows: len([r for r in rows if r[0] == 'signal_handled']) == 2)
        handled = [r[1] for r in p.observations() if r[0] == 'signal_handled']
        p.p.send_signal(signal.SIGUSR1)
        owners = {row['owner'] for row in handled}
        assert len(owners) == 1
        owner = owners.pop()
        code = p.p.wait(timeout=5)
        print(json.dumps(dict(observation='mixed_pending', completed_handlers=handled, exit=code)), flush=True)
        p.wait(128 + owner, timeout=5)
        assert budget.status(111).used == 2
        return dict(control='back_to_back_dispatch', sent=[15, 2], handled=handled,
                    exit=p.p.returncode, first_dispatched_wins=True)


def main():
    results = []
    with patch.object(process, 'Process', Process):
        for _ in range(3):
            print(json.dumps(coalescing_control()), flush=True)
        for mode in ('quiet_mixed', 'held_success', 'held_failure', 'before_reply', 'closed_loop'):
            for first in (signal.SIGINT, signal.SIGTERM):
                result = history(mode, first)
                results.append(result)
                print(json.dumps(result), flush=True)
    print('PASS fresh lifetime histories:', len(results), flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--child':
        raise SystemExit(child(sys.argv[2], sys.argv[3], int(sys.argv[4])))
    main()
