from pathlib import Path
import ast
import json
import os
import py_compile
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import telethon

repo = Path('/private/tmp/tgdata-10-reading-jobs')
root = Path(tempfile.mkdtemp(prefix='tgdata10_r4_package_', dir='/private/tmp'))
export = root / 'export'
export.mkdir()
paths = list((repo / 'tgdata').rglob('*.py')) + list((repo / 'examples').glob('*.py')) + [repo / 'setup.py']
for path in paths:
    py_compile.compile(str(path), doraise=True)
    ast.parse(path.read_text(), filename=str(path.relative_to(repo)), feature_version=(3, 7))
print('PASS compile and Python3.7 grammar:', len(paths), flush=True)
print('Runtime:', sys.version.split()[0], 'Telethon', telethon.__version__, 'SQLite', sqlite3.sqlite_version, flush=True)

for name in ('tgdata', 'docs', 'examples'):
    shutil.copytree(repo / name, export / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
for name in ('setup.py', 'README.md', 'requirements.txt'):
    shutil.copy2(repo / name, export / name)
assert not (export / '.git').exists() and not (export / 'devdocs').exists()

def run(command, cwd=export, env=None):
    result = subprocess.run(command, cwd=str(cwd), env=env, capture_output=True, timeout=120)
    if result.returncode:
        print(result.stdout.decode(errors='replace'))
        print(result.stderr.decode(errors='replace'))
        raise AssertionError(command)
    return result

run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation',
     '--wheel-dir', str(root / 'wheel'), str(export)],
    env=dict(os.environ, PYTHONPATH='/Users/ns/miniconda3/lib/python3.11/site-packages',
             PIP_NO_CACHE_DIR='1', PIP_DISABLE_PIP_VERSION_CHECK='1'))
wheel = next((root / 'wheel').glob('*.whl'))
installed = root / 'installed'
run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-compile', '--target', str(installed), str(wheel)])
runroot = root / 'run'
runroot.mkdir()
env = dict(os.environ, PYTHONPATH=str(installed))
info = run([sys.executable, '-c', 'import tgdata; print(tgdata.__file__)'], cwd=runroot, env=env)
assert str(installed).encode() in info.stdout and str(repo).encode() not in info.stdout
run([sys.executable, '-c',
     "from tgdata import ReadBudget; ReadBudget('read.sqlite3')"], cwd=runroot, env=env)
manifest = runroot / 'worker.json'
manifest.write_text(json.dumps(dict(version=1, worker_id='installed-worker', read_budget='read.sqlite3', accounts=[])))
for command in ([sys.executable, '-m', 'tgdata.worker'], [str(installed / 'bin/tgdata-worker')]):
    result = subprocess.run(command + ['--config', str(manifest)], cwd=str(runroot), env=env,
                            input=b'', capture_output=True, timeout=15)
    assert result.returncode == 0 and not result.stderr
    ready = json.loads(result.stdout)
    assert ready['kind'] == 'ready' and ready['account_count'] == 0
    print('PASS installed entrypoint:', command, flush=True)

shutil.copytree(export / 'examples', runroot / 'examples')
for example in ('reading_worker.py', 'daily_continuation.py'):
    result = run([sys.executable, str(runroot / 'examples' / example), '--demo'], cwd=runroot, env=env)
    print('PASS isolated example:', example, result.stdout.decode().splitlines()[-1], flush=True)
backfill = [sys.executable, str(runroot / 'examples/backfill_runs.py'), '--demo',
            '--directory', str(runroot / 'backfill')]
for state in ('new', 'restart'):
    result = run(backfill + (['--new'] if state == 'new' else []), cwd=runroot, env=env)
    print('PASS isolated backfill:', state, result.stdout.decode().splitlines()[-1], flush=True)
print('Export/install evidence retained:', root, flush=True)
