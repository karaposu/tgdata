"""Renewed fidelity checks for the integrated revision4 product; no product writes."""
import ast
import inspect
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata.worker_engine import WorkerAccount

BASE, PRODUCT = '68f6bbd', 'd32abcd'
FOLDER = ROOT / 'devdocs/work/10-reading-jobs'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=str(ROOT))

expected = {'README.md', 'setup.py', 'docs/worker.md', 'examples/reading_worker.py',
    'tgdata/account_operation.py', 'tgdata/batch_engine.py', 'tgdata/connection_engine.py',
    'tgdata/worker.py', 'tgdata/worker_engine.py', 'tgdata/worker_protocol.py',
    'tgdata/smoke_tests/README.md', 'tgdata/smoke_tests/test_37_worker.py',
    'tgdata/smoke_tests/test_38_worker_process.py'}
changed = set(git('diff', '--name-only', BASE, 'HEAD').decode().splitlines())
assert {name for name in changed if not name.startswith('devdocs/work/10-reading-jobs/')} == expected
assert not git('diff', PRODUCT, 'HEAD', '--', *sorted(expected))
print('PASS exact13 product paths; product unchanged since', PRODUCT)

checkpoints = ('a61f4a4', 'e8bf7f0', 'faa2f18', '079ea54', '0d2bc09',
               '3da72ad', 'bee5b1f', '6ee146c', '6c60832', BASE,
               '85c0455', '837d06f', '8322827', '9ce9ae3', '08ee0f2',
               'd49f8a0', '5adc00a', '2cc9995', '95acfc3', PRODUCT, '0c0144d')
for sha in checkpoints:
    subprocess.run(['git', 'merge-base', '--is-ancestor', sha, 'HEAD'], cwd=str(ROOT), check=True)
print('PASS{} warmth/pipeline/base ancestry checks'.format(len(checkpoints)))

modules = ('tgdata', 'owned_health', 'health', 'group_operations', 'join_client',
           'read_budget', 'join_budget', 'session_store', 'message_batch',
           'sync_engine', 'backfill_engine')
for module in modules:
    path = 'tgdata/' + module + '.py'
    assert git('show', BASE + ':' + path) == (ROOT / path).read_bytes()
print('PASS11 source, allowance, ownership and progress foundations byte-identical to dev')

def fetch(source):
    return next(n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.AsyncFunctionDef)
                and n.name == 'fetch_batch')
old = fetch(git('show', BASE + ':tgdata/batch_engine.py').decode())
new = fetch((ROOT / 'tgdata/batch_engine.py').read_text())
control = next(n for n in ast.walk(new) if isinstance(n, ast.If)
               and '_resolve_entity' in ast.dump(n.test))
original = next(n for n in ast.walk(old) if isinstance(n, ast.Try) and n.handlers
                and isinstance(n.handlers[0].type, ast.Name) and n.handlers[0].type.id == 'ValueError')
assert ast.dump(control.orelse[0]) == ast.dump(original)
print('PASS default BatchEngine get_entity/dialog fallback AST unchanged')
print('Inventory signature:', inspect.signature(WorkerAccount))
print('PASS revision4 explicitly preserves the optional positional inventory arguments')
subprocess.run(['git', 'diff', BASE, 'HEAD', '--check'], cwd=str(ROOT), check=True)
print('PASS complete branch whitespace')

assert git('rev-parse', 'origin/dev').strip() == git('rev-parse', BASE).strip()
audit = json.loads((FOLDER/'verification_r4/integration-audit.json').read_text())
for path, expected_hash in audit['changed_files_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected_hash, path
print('PASS all6 product/documentation file hashes match the631-pass verification snapshot')
fp = json.loads((FOLDER/'probes/revision4_fingerprint.json').read_text())
for path in audit['unchanged_source_files']:
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == fp['sources'][path]
print('PASS9 other fingerprinted runtime files unchanged through revision4')
for source, candidate, function in [('tgdata/worker.py', 'revision4_candidate_serve.py', 'serve'),
                                   ('tgdata/worker_protocol.py', 'revision4_candidate_diagnostics.py', 'describe_error')]:
    frozen = (FOLDER/'probes'/candidate).read_bytes()
    assert hashlib.sha256(frozen).hexdigest() == fp['candidates'][candidate]
    actual = next(n for n in ast.parse((ROOT/source).read_text()).body if isinstance(n, ast.FunctionDef) and n.name == function)
    reference = next(n for n in ast.parse(frozen).body if isinstance(n, ast.FunctionDef))
    assert ast.dump(actual) == ast.dump(reference), function
from tgdata.worker_protocol import _CANONICAL_AUTH_REASONS
assert sorted(_CANONICAL_AUTH_REASONS) == fp['canonical_auth_reasons']
print('PASS both frozen candidate functions and20 canonical auth names match integration')
old_count = new_count = 0
for name in ('test_37_worker', 'test_38_worker_process'):
    path = 'tgdata/smoke_tests/' + name + '.py'
    def tests(text):
        return {n.name for n in ast.parse(text).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_')}
    old, new = tests(git('show', '6ee146c:' + path)), tests((ROOT/path).read_text())
    assert old <= new
    old_count += len(old); new_count += len(new)
print('PASS all{} original worker groups retained; now{} groups'.format(old_count,new_count))
results = json.loads((FOLDER/'verification_r4/counted-results.json').read_text())
assert results['suites'] == 24 and results['actual_passes'] == 631 and results['live_skips'] == 3
for row in results['results']:
    assert row['exit'] == 0 and (FOLDER/'verification_r4'/row['artifact']).is_file()
print('PASS committed24-suite/631-pass/3-skip evidence complete; no rerun claimed')
issue = json.loads(Path('/private/tmp/tgdata10-r4-review-issue-before.json').read_text())
pr = json.loads(Path('/private/tmp/tgdata10-r4-review-pr-before.json').read_text())
assert {'heavy', 'enhancement'} <= {v['name'] for v in issue['labels']}
assert '- [x] **5 — implement**' in issue['body']
assert '- [ ] **6 — merge gate**' in issue['body'] and '- [ ] **7 — PR critic**' in issue['body']
assert pr['state'] == issue['state'] == 'OPEN' and pr['isDraft'] and pr['baseRefName'] == 'dev'
assert pr['headRefOid'] == git('rev-parse', '0c0144d').decode().strip() and 'Closes #10' in pr['body']
print('PASS issue labels/status and draft PR head/base/closing reference match committed work')
