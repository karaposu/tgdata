"""Supported offline suites and examples, each in a watchdog-bounded process."""
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / 'verification'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    sys.path.insert(0, str(ROOT))
    from tgdata import LoginFlow, LoginStatus, LoginError
    from tgdata.connection_engine import ConnectionEngine
    from telethon import __version__ as sdk_version
    assert sdk_version == '1.45.0', sdk_version
    candidate = HERE / 'prebuild'
    manifest = json.loads((candidate / 'manifest.json').read_text())
    assert all(sha(candidate / name) == digest for name, digest in manifest['sha256'].items())
    assert (ROOT / 'tgdata/login.py').read_bytes() == (candidate / 'candidate.py').read_bytes()
    assert (ROOT / 'tgdata/smoke_tests/test_41_stepwise_login.py').read_bytes() == (candidate / 'test_login.py').read_bytes()
    # The factory's only behavioral changes are the qualified private seam.
    old = subprocess.check_output(['git', 'show', 'c4e6eac:tgdata/connection_engine.py'], cwd=ROOT, text=True)
    old_tree = ast.parse(old)
    engine = next(n for n in old_tree.body if isinstance(n, ast.ClassDef) and n.name == 'ConnectionEngine')
    factory = next(n for n in engine.body if isinstance(n, ast.FunctionDef) and n.name == '_new_client')
    old_source = '\n'.join(old.splitlines()[factory.lineno-1:factory.end_lineno])
    old_source = textwrap.dedent(old_source).replace('session_file: Optional[str] = None, **client_options',
                   'session_file: Optional[str] = None, *, _client_base=None, **client_options')
    old_source = old_source.replace('_client_class(TelegramClient)', '_client_class(_client_base or TelegramClient)')
    actual = ast.parse(textwrap.dedent(inspect.getsource(ConnectionEngine._new_client)))
    expected = ast.parse(old_source)
    actual.body[0].body.pop(0)
    expected.body[0].body.pop(0)
    assert ast.dump(actual) == ast.dump(expected)
    files = list((ROOT / 'tgdata').rglob('*.py')) + list((ROOT / 'examples').glob('*.py')) + [ROOT / 'setup.py']
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in files}
    for path in files:
        ast.parse(path.read_text(), feature_version=(3, 7))
        compile(path.read_text(), str(path), 'exec')
    modules = [p.stem for p in sorted((ROOT / 'tgdata/smoke_tests').glob('test_*.py'))
               if p.name.split('_')[1].isdigit()
               and int(p.name.split('_')[1]) in list(range(12,20)) + list(range(22,42))]
    assert len(modules) == 28
    jobs = [(name, [sys.executable, '-m', 'tgdata.smoke_tests.' + name]) for name in modules]
    for name in ('account_pool','daily_continuation','backfill_runs','reading_worker','stepwise_login'):
        jobs.append(('example_' + name, [sys.executable, str(ROOT/'examples'/(name+'.py')), '--demo']))
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
    results = []
    with tempfile.TemporaryDirectory(prefix='tgdata8-no-live-') as tmp:
        missing = str(Path(tmp) / 'MISSING_CONFIG.ini')
        for name, command in jobs:
            if name.startswith(('test_12_', 'test_13_')):
                command.append(missing)
        def run(job):
            name, command = job
            start = time.monotonic()
            killed = False
            log = OUT / (name+'.txt')
            with log.open('w') as stream:
                try:
                    result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                            stderr=subprocess.STDOUT, timeout=120)
                    status = result.returncode
                except subprocess.TimeoutExpired:
                    status, killed = None, True
            value = log.read_text()
            counts = re.findall(r'Passed:\s*(\d+)\s*/\s*(\d+)', value)
            pair = tuple(map(int, counts[-1])) if counts else None
            if pair is None:
                simple = re.findall(r'^(\d+) passed; (\d+) failed$', value, re.M)
                if simple:
                    good, bad = map(int, simple[-1]); pair = (good, good+bad)
            if pair is None and re.search(r'^OK$', value, re.M):
                unit = re.findall(r'^Ran (\d+) tests? in ', value, re.M)
                if unit: pair = (int(unit[-1]), int(unit[-1]))
            passed = status == 0 and not killed
            if name.startswith('test_'):
                passed = passed and pair is not None and pair[0] == pair[1]
            return dict(name=name, passed=bool(passed), exit_code=status, watchdog_killed=killed,
                        counts=pair, live_skips=sum('! skipped' in line for line in value.splitlines()),
                        duration_s=round(time.monotonic()-start,3), log=log.name)
        with ThreadPoolExecutor(max_workers=4) as workers:
            for future in as_completed([workers.submit(run, job) for job in jobs]):
                row = future.result()
                results.append(row)
                print(json.dumps(row), flush=True)
    assert all(sha(ROOT/name) == digest for name, digest in hashes.items()), 'Source changed during verification'
    passed = all(r['passed'] for r in results)
    report = dict(result='PASS' if passed else 'FAIL', runtime=sys.version.split()[0], telethon=sdk_version,
                  candidate_parity=True, factory_parity=True, compile=True, python37_grammar=True,
                  native_python37=False, source_sha256=hashes, results=sorted(results,key=lambda r:r['name']))
    (OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT ' + report['result'], flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
