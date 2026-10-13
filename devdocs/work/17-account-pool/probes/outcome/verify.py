"""Verify plan7 on the actual branch: supported offline suites, demos and parity."""
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
ROOT = HERE.parents[4]
OUT = HERE.parents[1] / 'evidence/outcome-implementation'


class CodeOnly(ast.NodeTransformer):
    def generic_visit(self, node):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body = node.body[1:]
        return super().generic_visit(node)


def code(file):
    return ast.dump(CodeOnly().visit(ast.parse(file.read_text())), include_attributes=False)


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    attempt = 1
    while (OUT / ('attempt-' + str(attempt))).exists():
        attempt += 1
    output = OUT / ('attempt-' + str(attempt))
    output.mkdir()
    manifest = json.loads((HERE.parents[1] / 'evidence/outcome/candidate-manifest.json').read_text())
    candidate = Path(manifest['source'])
    runtime_names = [name for name in manifest['changed']
                     if name.startswith('tgdata/') and not name.startswith('tgdata/smoke_tests/')]
    assert len(runtime_names) == 8
    assert all(sha(candidate / name) == manifest['sha256'][name] for name in manifest['sha256'])
    parity = {name: code(ROOT / name) == code(candidate / name) for name in runtime_names}
    assert all(parity.values()), parity
    modules = []
    for file in sorted((ROOT / 'tgdata/smoke_tests').glob('test_*.py')):
        match = re.match(r'test_(\d+)_', file.name)
        if match and int(match[1]) in list(range(12, 20)) + list(range(22, 41)):
            modules.append(file.stem)
    assert len(modules) == 27
    # The directly changed suites start first, without duplicating them later.
    focused = ('test_40_pool_outcomes', 'test_31_account_pool', 'test_39_pool_lifecycle')
    modules = list(focused) + [name for name in modules if name not in focused]
    jobs = [(name, [sys.executable, '-m', 'tgdata.smoke_tests.' + name], 120) for name in modules]
    jobs += [('example_' + name, [sys.executable, str(ROOT / 'examples' / (name + '.py')), '--demo'], 120)
             for name in ('account_pool', 'daily_continuation', 'backfill_runs')]
    files = list((ROOT / 'tgdata').rglob('*.py')) + list((ROOT / 'examples').glob('*.py')) + [ROOT / 'setup.py']
    initial_hashes = {str(file.relative_to(ROOT)): sha(file) for file in files}
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
    results = []
    with tempfile.TemporaryDirectory(prefix='tgdata17-no-live-verification-') as temp:
        missing = str(Path(temp) / 'NO_LIVE_CONFIG.ini')
        assert not Path(missing).exists()
        for name, command, limit in jobs:
            if name.startswith(('test_12_', 'test_13_')):
                command.append(missing)

        def run(job):
            name, command, limit = job
            started = time.monotonic()
            killed = False
            log = output / (name + '.txt')
            with log.open('w') as stream:
                try:
                    result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                            stderr=subprocess.STDOUT, timeout=limit)
                    status = result.returncode
                except subprocess.TimeoutExpired:
                    status, killed = None, True
            text = log.read_text()
            pair = None
            counts = re.findall(r'Passed:\s*(\d+)\s*/\s*(\d+)', text)
            if counts:
                pair = tuple(map(int, counts[-1]))
            if pair is None:
                simple = re.findall(r'^(\d+) passed; (\d+) failed$', text, re.M)
                if simple:
                    good, bad = map(int, simple[-1])
                    pair = (good, good + bad)
            if pair is None and re.search(r'^OK$', text, re.M):
                unit = re.findall(r'^Ran (\d+) tests? in ', text, re.M)
                if unit:
                    pair = (int(unit[-1]), int(unit[-1]))
            skips = sum('! skipped' in line for line in text.splitlines())
            passed = status == 0 and not killed
            if name.startswith('test_'):
                passed = passed and pair is not None and pair[0] == pair[1]
            if name == 'test_40_pool_outcomes':
                passed = passed and pair == (25, 25)
            return dict(name=name, passed=bool(passed), exit_code=status, watchdog_killed=killed,
                        counts=pair, live_skips=skips, duration_s=round(time.monotonic() - started, 3),
                        command=command, log=log.name)

        with ThreadPoolExecutor(max_workers=4) as workers:
            futures = [workers.submit(run, job) for job in jobs]
            for future in as_completed(futures):
                row = future.result()
                results.append(row)
                print(json.dumps(row), flush=True)
    stable = all(sha(ROOT / name) == digest for name, digest in initial_hashes.items())
    for file in files:
        ast.parse(file.read_text(), feature_version=(3, 7))
        compile(file.read_text(), str(file), 'exec')
    # Permanent qualification functions are exactly those exercised by P0.
    permanent = ast.parse((ROOT / 'tgdata/smoke_tests/test_40_pool_outcomes.py').read_text())
    functions = {node.name: ast.dump(node, include_attributes=False) for node in permanent.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    function_count = 0
    for name in ('cases.py', 'review_controls.py'):
        for node in ast.parse((HERE / name).read_text()).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name != 'main':
                assert functions[node.name] == ast.dump(node, include_attributes=False), node.name
                function_count += 1
    total = sum(row['counts'][1] for row in results if row['counts'])
    skips = sum(row['live_skips'] for row in results)
    passed = all(row['passed'] for row in results) and stable and all(parity.values())
    summary = dict(result='PASS' if passed else 'FAIL', attempt=attempt,
                   checks=sorted(results, key=lambda row: row['name']), reported_groups=total,
                   executed_groups=total-skips, explicit_live_skips=skips,
                   runtime_and_tests_stable=stable, code_parity_with_prebuild=parity,
                   byte_parity_with_prebuild={name: sha(ROOT/name) == manifest['sha256'][name]
                                             for name in runtime_names},
                   unchanged_promoted_function_bodies=function_count,
                   compile_and_python37_grammar_files=len(files), working_runtime_sha256=initial_hashes,
                   head_before_product_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(dict(result=summary['result'], executed_groups=total-skips, live_skips=skips,
                         evidence=str(output), runtime_stable=stable)), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
