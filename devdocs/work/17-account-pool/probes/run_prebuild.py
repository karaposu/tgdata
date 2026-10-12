"""Bounded parent runner: every required pool/worker result belongs to one attempt."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent / 'evidence/replan-r3'


def main():
    manifest = json.loads((EVIDENCE / 'export-manifest.json').read_text())
    source = Path(manifest['export'])
    attempt = 1
    while (EVIDENCE / ('attempt-{}-summary.json'.format(attempt))).exists():
        attempt += 1
    env = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
    tasks = [('combined', [sys.executable, str(HERE / 'prebuild_r3.py'), '--source', str(source)], 90),
             ('worker37', [sys.executable, '-m', 'tgdata.smoke_tests.test_37_worker'], 90),
             ('worker38', [sys.executable, '-m', 'tgdata.smoke_tests.test_38_worker_process'], 90)]
    results = []
    for name, command, limit in tasks:
        output = EVIDENCE / ('attempt-{}-{}.txt'.format(attempt, name))
        started = time.monotonic()
        timed_out = False
        with output.open('w') as stream:
            try:
                result = subprocess.run(command, cwd=source, env=env, stdout=stream,
                                        stderr=subprocess.STDOUT, timeout=limit)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code, timed_out = None, True
        data = output.read_text()
        detail = None
        if name == 'combined':
            for line in data.splitlines():
                try: value = json.loads(line)
                except ValueError: continue
                if 'summary' in value: detail = value['summary']
            passed = bool(code == 0 and detail and detail['passed'] == detail['combined_cases'] == 37
                          and not detail['failed'])
        else:
            match = re.findall(r'Passed: (\d+)/(\d+)', data)
            detail = dict(passed=int(match[-1][0]), total=int(match[-1][1])) if match else None
            passed = bool(code == 0 and detail and detail['passed'] == detail['total'] > 0)
        entry = dict(name=name, passed=passed, exit_code=code, watchdog_killed=timed_out,
                     duration_s=round(time.monotonic() - started, 3), detail=detail, output=output.name)
        results.append(entry)
        print(json.dumps(entry), flush=True)
    unchanged = all(hashlib.sha256((source / f).read_bytes()).hexdigest() == value
                    for f, value in manifest['runtime_sha256'].items())
    candidate = HERE / 'prebuild_candidate.py'
    ast.parse(candidate.read_text(), feature_version=(3, 7))
    candidate_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (candidate, HERE / 'prebuild_r3.py', Path(__file__))}
    summary = dict(attempt=attempt, result='PASS' if all(r['passed'] for r in results) and unchanged else 'FAIL',
                   checks=results, exported_runtime_unchanged=unchanged, candidate_sha256=candidate_hashes,
                   candidate_python37_grammar=True, source_tree=manifest['resolved_tree'])
    (EVIDENCE / ('attempt-{}-summary.json'.format(attempt))).write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(dict(gate=summary['result'], attempt=attempt, runtime_unchanged=unchanged)), flush=True)
    return 0 if summary['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
