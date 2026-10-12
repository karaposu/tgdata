"""Run two permanent regressions against an isolated copy of the rejected runtime."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

repo = Path('/private/tmp/tgdata-10-reading-jobs')
root = Path(tempfile.mkdtemp(prefix='tgdata10_r4_negative_', dir='/private/tmp'))
shutil.copytree(repo / 'tgdata', root / 'tgdata', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
for relative in ('tgdata/worker.py', 'tgdata/worker_protocol.py'):
    old = subprocess.check_output(['git', 'show', '6ee146c:' + relative], cwd=str(repo))
    (root / relative).write_bytes(old)
control = '''import asyncio
import logging
import signal
import socket
import subprocess
import sys
from unittest.mock import patch
from tgdata.smoke_tests import test_37_worker as core
from tgdata.smoke_tests import test_38_worker_process as process
logging.disable(logging.CRITICAL)
with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \\
     patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
    if sys.argv[1] == 'authentication':
        try:
            asyncio.run(core.test_sdk_authentication_read_batch())
        except AssertionError:
            print('PASS sensitivity: rejected auth projector fails permanent SDK regression')
        else:
            raise AssertionError('Rejected authentication code unexpectedly passed')
    else:
        try:
            process.lifecycle('quiet', signal.SIGTERM)
        except subprocess.TimeoutExpired:
            print('PASS sensitivity: rejected stop handler fails permanent quiet-selector regression')
        else:
            raise AssertionError('Rejected stop handler unexpectedly passed')
'''
(root / 'negative_control.py').write_text(control)
for case in ('authentication', 'stop'):
    result = subprocess.run([sys.executable, str(root / 'negative_control.py'), case], cwd=str(root),
                            env=dict(os.environ, PYTHONPATH=str(root)), capture_output=True, timeout=30)
    print(result.stdout.decode(), end='', flush=True)
    assert result.returncode == 0 and not result.stderr, result.stderr.decode()
print('Retained isolated rejected-code controls:', root)
