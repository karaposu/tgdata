"""Fresh worker lifetime falsifiers: real OS signals, SDK and selector, no network."""
import asyncio
import json
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
from tgdata import ReadBudget, JoinBudget
from tgdata.worker import main as worker_main
from tgdata.smoke_tests import test_37_worker as f
from tgdata.smoke_tests import test_38_worker_process as p


def child(root, mode):
    root = Path(root)
    item = f.fixture(root, 111)
    def trace(kind, detail):
        with (root / 'trace.jsonl').open('a') as stream:
            stream.write(json.dumps([kind, detail]) + '\n')
    async def ticker():
        while True:
            await asyncio.sleep(.01)
    def hook(client, sender):
        loop = asyncio.get_running_loop()
        sender.script['GetHistoryRequest'] = [loop.create_future()]
        original = loop._selector.select
        def observed(timeout=None):
            # Observe the real selector without introducing an asyncio timer.
            trace('select', timeout)
            return original(timeout)
        loop._selector.select = observed
        signal.signal(signal.SIGUSR1, lambda sig, frame: loop.call_soon_threadsafe(lambda: None))
        if mode == 'polling':
            asyncio.create_task(ticker())
        trace('client', 111)
    item.trace, item.hook = trace, hook
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         f.install_factory({111: item}):
        return worker_main(['--config', str(root / 'worker.json')])


def signal_case(sig, mode):
    with tempfile.TemporaryDirectory(prefix='tgdata10_pr_signal_') as directory:
        root = Path(directory)
        budget = ReadBudget(root / 'read.sqlite3');budget.configure(111, 20)
        f.fixture(root, 111)
        (root / 'worker.json').write_text(json.dumps(dict(version=1, worker_id='probe',
            read_budget='read.sqlite3', accounts=[dict(account_id='111', config_path='account-111.ini')])))
        process = p.Process.__new__(p.Process)
        process.root, process.buffer, process.stderr = root, bytearray(), b''
        process.p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
            '--child', str(root), mode], cwd=str(ROOT), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        try:
            assert process.line()['kind'] == 'ready'
            process.send(p.request())
            process.until(lambda rows: ['request', 'GetHistoryRequest'] in rows
                          and any(row[0] == 'select' and row[1] is not None and row[1] > 1 for row in rows)
                          if mode == 'quiet' else ['request', 'GetHistoryRequest'] in rows)
            time.sleep(.1)  # Parent only; child has no helper timer in quiet mode.
            before_signal = process.trace()
            selector_timeout = [row[1] for row in before_signal if row[0] == 'select'][-1]
            started = time.monotonic()
            process.p.send_signal(sig)
            try:
                process.p.wait(timeout=.7)
                late = False
            except subprocess.TimeoutExpired:
                late = True
            before_wake = process.trace()
            if late:
                # Repeat does not supply a loop wake-up either. Diagnostic control:
                # a separate explicit self-pipe wake lets the already-cancelled job run.
                process.p.send_signal(sig)
                time.sleep(.15)
                still_waiting = process.p.poll() is None
                process.p.send_signal(signal.SIGUSR1)
            else:
                still_waiting = False
            process.wait(128 + sig, timeout=5)
            after = process.trace()
            result = dict(case='signal_without_helper', signal=sig.name, mode=mode,
                selector_timeout_before_signal=round(selector_timeout, 3),
                stalled_before_explicit_wake=late,
                cleanup_started_before_wake=['cleanup', 'entered'] in before_wake,
                repeated_signal_still_waiting=still_waiting,
                cleanup_finished=['cleanup', 'finished'] in after,
                exit=process.p.returncode, charge=budget.status(111).used,
                elapsed=round(time.monotonic()-started, 3))
            assert result['cleanup_finished'] and result['charge'] == 2
            print(json.dumps(result), flush=True)
            return result
        finally:
            process.dispose()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--child':
        raise SystemExit(child(sys.argv[2], sys.argv[3]))
    for sig in (signal.SIGINT, signal.SIGTERM):
        for mode in ('quiet', 'polling'):
            signal_case(sig, mode)
