"""Run the supported offline suites with bounded subprocesses and saved evidence."""
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
ROOT = Path('/private/tmp/tgdata-50-terminal-login-pr')
DEMO_NAMES = ('account_pool', 'daily_continuation', 'backfill_runs', 'reading_worker',
              'stepwise_login', 'album_assembly', 'photo_trails')


def main():
    phase = sys.argv[1]
    assert phase in ('targeted', 'full')
    out = HERE / 'evidence' / phase
    out.mkdir(parents=True, exist_ok=True)
    names = sorted(p for folder in ('tgdata', 'examples') for p in (ROOT/folder).rglob('*.py')) + [ROOT/'setup.py']
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in names}
    for p in names:
        source = p.read_text()
        compile(source, str(p), 'exec')
        ast.parse(source, feature_version=(3, 7))
    ids = ({15, 17, 32, 41, 48} if phase == 'targeted' else
           set(range(12, 20)) | set(range(22, 47)) | {48})
    tests = [p.stem for p in sorted((ROOT/'tgdata/smoke_tests').glob('test_*.py'))
             if p.name.split('_')[1].isdigit() and int(p.name.split('_')[1]) in ids]
    assert len(tests) == (5 if phase == 'targeted' else 34)
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
    results = []
    with tempfile.TemporaryDirectory(prefix='terminal-login-no-live-') as tmp:
        jobs = []
        for name in tests:
            command = [sys.executable, '-m', 'tgdata.smoke_tests.'+name]
            if name.startswith(('test_12_', 'test_13_')):
                command.append(str(Path(tmp)/'MISSING_CONFIG.ini'))
            jobs.append((name, command))
        if phase == 'full':
            jobs.extend(('example_'+n, [sys.executable, str(ROOT/'examples'/(n+'.py')), '--demo'])
                        for n in DEMO_NAMES)

        def run(job):
            name, command = job
            log = out/(name+'.txt')
            start = time.monotonic()
            with log.open('w') as stream:
                try:
                    code = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                        stderr=subprocess.STDOUT, timeout=120).returncode
                except subprocess.TimeoutExpired:
                    code = None
            text = log.read_text()
            counts = None
            pairs = re.findall(r'Passed:\s*(\d+)\s*/\s*(\d+)', text)
            if pairs:
                counts = tuple(map(int, pairs[-1]))
            if counts is None:
                pairs = re.findall(r'^(\d+) passed; (\d+) failed$', text, re.M)
                if pairs:
                    good, bad = map(int, pairs[-1])
                    counts = (good, good+bad)
            if counts is None and re.search(r'^OK$', text, re.M):
                pairs = re.findall(r'^Ran (\d+) tests? in ', text, re.M)
                if pairs:
                    counts = (int(pairs[-1]), int(pairs[-1]))
            passed = code == 0 and (not name.startswith('test_') or
                counts is not None and counts[0] == counts[1] and counts[0] > 0)
            row = dict(name=name, passed=bool(passed), exit_code=code, counts=counts,
                live_skips=sum('! skipped' in line for line in text.splitlines()),
                duration_s=round(time.monotonic()-start, 3))
            print(json.dumps(row), flush=True)
            return row

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = [f.result() for f in as_completed([pool.submit(run, j) for j in jobs])]
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == digest
               for p, digest in hashes.items()), 'source changed during verification'
    skips = sum(r['live_skips'] for r in results)
    report = dict(result='PASS' if all(r['passed'] for r in results) else 'FAIL',
        phase=phase, runtime=sys.version.split()[0], source_sha256=hashes,
        compiled=len(names), python37_grammar=len(names), native_python37=False,
        suites=len(tests), demos=7 if phase=='full' else 0,
        offline_checks=sum(r['counts'][0] for r in results if r['counts'])-skips,
        live_skips=skips, results=sorted(results, key=lambda r:r['name']))
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('RESULT', report['result'], 'offline', report['offline_checks'],
          'suites', report['suites'], 'demos', report['demos'], 'live skips', skips, flush=True)
    return 0 if report['result']=='PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
