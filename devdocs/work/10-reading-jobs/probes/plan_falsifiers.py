"""Pre-implementation worker plan probes: actual SDK resolution and OS stdout."""
import asyncio
from contextlib import asynccontextmanager
import json
import logging
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
from tgdata.batch_engine import BatchEngine
from tgdata.smoke_tests import test_32_account_operation as f
from telethon import errors, types


class Bound:
    def __init__(self, op): self.op = op
    @asynccontextmanager
    async def session(self): yield self.op.client


async def resolution():
    with tempfile.TemporaryDirectory(prefix='tgdata10-resolution-') as directory:
        f.TMP = Path(directory)
        fx = f.Fixture(accounts=(222,), cached=111, budget=True, responses={
            'GetChannelsRequest': errors.ChannelInvalidError(request=None),
            'GetDialogsRequest': types.messages.Dialogs([], [], [], []),
        })
        try:
            async with fx.engine._account_operation(222) as op:
                try:
                    await BatchEngine(Bound(op)).fetch_batch(-1000000000007, limit=1)
                except Exception as error:
                    kind = type(error).__name__
                else:
                    raise AssertionError('An uncached private peer unexpectedly resolved')
            assert 'GetDialogsRequest' in fx.wire.calls
            print(json.dumps(dict(case='legacy_raw_resolution', error=kind,
                attempted_dialog_scan=True, history_requests=fx.wire.calls.count('GetHistoryRequest'),
                actual_requests=fx.wire.calls)), flush=True)
        finally:
            for client in fx.clients: await client.disconnect()


CHILD = '''import os,signal,sys
def stop(*args): raise SystemExit(143)
signal.signal(signal.SIGTERM,stop)
mode,scenario=sys.argv[1:]
sys.stderr.write('ready\\n');sys.stderr.flush()
sys.stdin.buffer.readline()
try:
    if scenario=='broken':
        if mode=='buffered':
            sys.stdout.buffer.write(b'x'*64);sys.stdout.buffer.flush()
        else: os.write(sys.stdout.fileno(),b'x'*64)
    else:
        sys.stderr.write('writing\\n');sys.stderr.flush()
        for n in range(2048):
            if mode=='buffered':sys.stdout.buffer.write(b'x'*1024)
            else:os.write(sys.stdout.fileno(),b'x'*1024)
        if mode=='buffered':sys.stdout.buffer.flush()
except BrokenPipeError:
    raise SystemExit(3)
'''


def output_cases():
    for scenario in ('broken', 'pressure'):
        for mode in ('buffered', 'raw'):
            p = subprocess.Popen([sys.executable, '-c', CHILD, mode, scenario],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                assert p.stderr.readline() == b'ready\n'
                if scenario == 'broken':
                    p.stdout.close()
                    p.stdout = None
                p.stdin.write(b'go\n');p.stdin.close();p.stdin = None
                if scenario == 'pressure':
                    assert p.stderr.readline() == b'writing\n'
                    time.sleep(.1)
                    assert p.poll() is None
                    p.send_signal(signal.SIGTERM)
                stuck = False
                try:p.wait(timeout=.5)
                except subprocess.TimeoutExpired:stuck = True
                # Drain only after observing whether signal termination completed.
                out, err = p.communicate(timeout=3)
                print(json.dumps(dict(case='stdout_'+scenario, mode=mode, exit=p.returncode,
                    stuck_until_drain=stuck, shutdown_warning=bool(err),
                    bytes=len(out or b''))), flush=True)
            finally:
                if p.poll() is None:
                    p.kill();p.communicate()


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        asyncio.run(resolution())
    output_cases()
