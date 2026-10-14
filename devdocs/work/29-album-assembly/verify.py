"""Issue29 offline verification, with bounded subprocesses and source manifests."""
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
ROOT = HERE.parents[2]
OUT = HERE / 'verification'
BASE = 'e5cdad77ff6af41f21503fc43fe3180d5213a41e'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    sys.path.insert(0, str(ROOT))
    import tgdata, telethon
    assert Path(tgdata.__file__).resolve() == ROOT / 'tgdata/__init__.py'
    assert tgdata.__version__ == '0.1' and telethon.__version__ == '1.45.0'
    original = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, 'tgdata', 'examples'], cwd=ROOT, text=True).splitlines()
    original = [name for name in original if name.endswith('.py')]
    for name in original:
        prior = subprocess.check_output(['git', 'show', '{}:{}'.format(BASE, name)], cwd=ROOT)
        if name == 'tgdata/__init__.py':
            prior += (b'\nfrom .album import TelegramPost, AlbumAssemblyError, album_post_ids, assemble_albums\n'
                      b'__all__ += ["TelegramPost", "AlbumAssemblyError", "album_post_ids", "assemble_albums"]\n')
        assert (ROOT / name).read_bytes() == prior, 'unexpected existing Python change: ' + name
    names = sorted(str(p.relative_to(ROOT)) for folder in ('tgdata', 'examples') for p in (ROOT / folder).rglob('*.py'))
    manifest = {name: digest(ROOT / name) for name in names}
    for name in names:
        text = (ROOT / name).read_text()
        compile(text, name, 'exec')
        ast.parse(text, feature_version=(3, 7))
    modules = [p.stem for p in sorted((ROOT / 'tgdata/smoke_tests').glob('test_*.py'))
               if p.name.split('_')[1].isdigit() and int(p.name.split('_')[1]) in list(range(12, 20)) + list(range(22, 43))]
    assert len(modules) == 29
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
    all_results = []
    with tempfile.TemporaryDirectory(prefix='tgdata29-no-live-') as tmp:
        missing = str(Path(tmp) / 'MISSING_CONFIG.ini')
        def run(job):
            phase, name, command = job
            start = time.monotonic(); killed = False
            log = OUT / (phase + '_' + name + '.txt')
            with log.open('w') as stream:
                try:
                    code = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                          stderr=subprocess.STDOUT, timeout=120).returncode
                except subprocess.TimeoutExpired:
                    code, killed = None, True
            value = log.read_text()
            counts = re.findall(r'Passed:\s*(\d+)\s*/\s*(\d+)', value)
            pair = tuple(map(int, counts[-1])) if counts else None
            if pair is None:
                simple = re.findall(r'^(\d+) passed; (\d+) failed$', value, re.M)
                if simple:
                    good, bad = map(int, simple[-1]); pair = (good, good+bad)
            if pair is None and re.search(r'^OK$', value, re.M):
                unit = re.findall(r'^Ran (\d+) tests? in ', value, re.M)
                if unit:
                    pair = (int(unit[-1]), int(unit[-1]))
            passed = code == 0 and not killed
            if name.startswith('test_'):
                passed = passed and pair is not None and pair[0] == pair[1]
            row = dict(phase=phase, name=name, passed=bool(passed), exit_code=code, watchdog_killed=killed,
                       counts=pair, live_skips=sum('! skipped' in line for line in value.splitlines()),
                       duration_s=round(time.monotonic()-start, 3), log=log.name)
            print(json.dumps(row), flush=True)
            return row
        for phase in ('focused', 'full'):
            selected = modules if phase == 'full' else [name for name in modules if int(name.split('_')[1]) in [19, 22, 23] + list(range(24, 32)) + [39, 40, 42]]
            jobs = []
            for name in selected:
                command = [sys.executable, '-m', 'tgdata.smoke_tests.'+name]
                if name.startswith(('test_12_', 'test_13_')):
                    command.append(missing)
                jobs.append((phase, name, command))
            if phase == 'full':
                for name in ('account_pool', 'daily_continuation', 'backfill_runs', 'reading_worker', 'stepwise_login', 'album_assembly'):
                    jobs.append((phase, 'example_'+name, [sys.executable, str(ROOT/'examples'/(name+'.py')), '--demo']))
            with ThreadPoolExecutor(max_workers=4) as workers:
                results = [future.result() for future in as_completed([workers.submit(run, job) for job in jobs])]
            all_results.extend(results)
            if not all(row['passed'] for row in results):
                break
    assert all(digest(ROOT/name) == value for name, value in manifest.items()), 'sources changed during verification'
    full = [row for row in all_results if row['phase'] == 'full']
    skips = sum(row['live_skips'] for row in full)
    success = len(full) == 35 and all(row['passed'] for row in all_results)
    report = dict(result='PASS' if success else 'FAIL', version=tgdata.__version__, runtime=sys.version.split()[0],
                  telethon=telethon.__version__, source_base=BASE, source_sha256=manifest,
                  unchanged_existing_python=len(original)-1, compile=len(names), python37_grammar=len(names), native_python37=False,
                  suite_count=sum(row['name'].startswith('test_') for row in full),
                  executed_offline=sum(row['counts'][0] for row in full if row['counts'])-skips,
                  live_skips=skips, demos=sum(row['name'].startswith('example_') and row['passed'] for row in full),
                  results=sorted(all_results, key=lambda row:(row['phase'], row['name'])))
    (OUT/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('RESULT', report['result'], 'offline', report['executed_offline'], 'live-skips', skips, flush=True)
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
