"""Run existing release checks on the candidate, with exact baseline parity."""
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'candidate'
OUT = HERE / 'verification'
BASELINE = Path('/private/tmp/tgdata-8-stepwise-login/devdocs/work/8-stepwise-login/merged-verification/result.json')
BASE_INIT = Path('/private/tmp/tgdata-28-merge-verification/tgdata/__init__.py')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True)
    expected = json.loads(BASELINE.read_text())['source_sha256']
    expected_init = BASE_INIT.read_bytes().replace(b'__version__ = "0.0.8"', b'__version__ = "0.1"')
    assert (ROOT / 'tgdata/__init__.py').read_bytes() == expected_init
    expected['tgdata/__init__.py'] = hashlib.sha256(expected_init).hexdigest()
    assert all(sha(ROOT / name) == digest for name, digest in expected.items())
    sys.path.insert(0, str(ROOT))
    import tgdata, telethon
    assert tgdata.__version__ == '0.1'
    assert telethon.__version__ == '1.45.0'
    assert Path(tgdata.__file__).resolve() == ROOT / 'tgdata/__init__.py'
    for name in expected:
        if name.endswith('.py'):
            text = (ROOT / name).read_text()
            ast.parse(text, feature_version=(3, 7))
            compile(text, name, 'exec')
    modules = [p.stem for p in sorted((ROOT / 'tgdata/smoke_tests').glob('test_*.py'))
               if p.name.split('_')[1].isdigit()
               and int(p.name.split('_')[1]) in list(range(12, 20)) + list(range(22, 42))]
    assert len(modules) == 28
    jobs = [(name, [sys.executable, '-m', 'tgdata.smoke_tests.' + name]) for name in modules]
    for name in ('account_pool', 'daily_continuation', 'backfill_runs', 'reading_worker', 'stepwise_login'):
        jobs.append(('example_' + name, [sys.executable, str(ROOT / 'examples' / (name + '.py')), '--demo']))
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
    results = []
    with tempfile.TemporaryDirectory(prefix='tgdata01-no-live-') as tmp:
        missing = str(Path(tmp) / 'MISSING_CONFIG.ini')
        for name, command in jobs:
            if name.startswith(('test_12_', 'test_13_')):
                command.append(missing)
        def run(job):
            name, command = job
            started = time.monotonic()
            log = OUT / (name + '.txt')
            killed = False
            with log.open('w') as stream:
                try:
                    status = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                        stderr=subprocess.STDOUT, timeout=120).returncode
                except subprocess.TimeoutExpired:
                    status, killed = None, True
            value = log.read_text()
            counts = re.findall(r'Passed:\s*(\d+)\s*/\s*(\d+)', value)
            pair = tuple(map(int, counts[-1])) if counts else None
            if pair is None:
                simple = re.findall(r'^(\d+) passed; (\d+) failed$', value, re.M)
                if simple:
                    good, bad = map(int, simple[-1]); pair = (good, good + bad)
            if pair is None and re.search(r'^OK$', value, re.M):
                unit = re.findall(r'^Ran (\d+) tests? in ', value, re.M)
                if unit:
                    pair = (int(unit[-1]), int(unit[-1]))
            passed = status == 0 and not killed
            if name.startswith('test_'):
                passed = passed and pair is not None and pair[0] == pair[1]
            return dict(name=name, passed=bool(passed), exit_code=status, watchdog_killed=killed,
                        counts=pair, live_skips=sum('! skipped' in line for line in value.splitlines()),
                        duration_s=round(time.monotonic() - started, 3), log=log.name)
        with ThreadPoolExecutor(max_workers=4) as workers:
            for future in as_completed([workers.submit(run, job) for job in jobs]):
                row = future.result(); results.append(row)
                print(json.dumps(row), flush=True)
    assert all(sha(ROOT / name) == digest for name, digest in expected.items()), 'Candidate changed during verification'
    passed = all(row['passed'] for row in results)
    skips = sum(row['live_skips'] for row in results)
    executed = sum(row['counts'][0] for row in results if row['counts']) - skips
    report = dict(result='PASS' if passed else 'FAIL', version=tgdata.__version__,
        runtime=sys.version.split()[0], telethon=telethon.__version__, source_base='f927496',
        source_sha256=expected, compile=True, python37_grammar=True, native_python37=False,
        suite_count=len(modules), executed_offline=executed, live_skips=skips,
        demos=sum(row['name'].startswith('example_') and row['passed'] for row in results),
        results=sorted(results, key=lambda row: row['name']))
    (OUT / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('RESULT', report['result'], 'executed', executed, 'skipped', skips, flush=True)
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
