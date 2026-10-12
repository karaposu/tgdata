"""Read-only fidelity checks for the unchanged #10 implementation snapshot."""
import ast
import inspect
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata.worker_engine import WorkerAccount

BASE, PRODUCT = '68f6bbd', '6ee146c'

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
               '3da72ad', 'bee5b1f', PRODUCT, '6c60832', BASE)
for sha in checkpoints:
    subprocess.run(['git', 'merge-base', '--is-ancestor', sha, 'HEAD'], cwd=str(ROOT), check=True)
print('PASS10 warmth/pipeline/base ancestry checks')

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
print('NOTE optional store/label accept positional arguments; planned keyword-only restriction absent')
subprocess.run(['git', 'diff', BASE, 'HEAD', '--check'], cwd=str(ROOT), check=True)
print('PASS complete branch whitespace')
