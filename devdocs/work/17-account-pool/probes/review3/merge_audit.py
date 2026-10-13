"""Renewed fidelity audit for plan7's exact implemented product, not a PR verdict."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
WORK = ROOT / 'devdocs/work/17-account-pool'
BASE = '2ddb852d917998d003f9db863fce09a92e9c5712'
SUBJECT = 'b62189cf5945bcd901194a532cbba0353a9ed283'
PRODUCT = '007c2e4'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True)


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


class CodeOnly(ast.NodeTransformer):
    def generic_visit(self, node):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body = node.body[1:]
        return super().generic_visit(node)


def code(text):
    return ast.dump(CodeOnly().visit(ast.parse(text)), include_attributes=False)


def methods(text, name):
    return {n.name: n for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == name
            for n in c.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main():
    commits = ['09e0277', 'a63099e', '234563e', 'f1cae2c', '41a6c59',
               'e7fdafc', 'b5d26e0', '25a55f0', '9772541', PRODUCT, BASE]
    for commit in commits:
        subprocess.run(['git', 'merge-base', '--is-ancestor', commit, SUBJECT], cwd=ROOT, check=True)
    paths = git('diff', '--name-only', BASE + '...' + SUBJECT, '--', '.', ':!devdocs').splitlines()
    assert len(paths) == 23 and not any('duncan' in p.lower() for p in paths)
    assert not git('diff', PRODUCT, SUBJECT, '--', '.', ':!devdocs')
    stable = ['connection_engine', 'account_operation', 'owned_health', 'group_operations',
              'join_budget', 'join_client', 'budget_client', 'worker', 'worker_engine',
              'worker_protocol', 'read_budget', 'sync_store', 'backfill_state', 'backfill', 'health']
    for name in stable:
        file = 'tgdata/' + name + '.py'
        assert git('show', BASE + ':' + file) == (ROOT / file).read_text(), file
    manifest = json.loads((WORK / 'evidence/outcome/candidate-manifest.json').read_text())
    candidate = Path(manifest['source'])
    runtime = [f for f in manifest['changed'] if f.startswith('tgdata/') and not f.startswith('tgdata/smoke_tests/')]
    assert len(runtime) == 8
    parity = {}
    for file in runtime:
        assert sha(candidate / file) == manifest['sha256'][file]
        assert code((ROOT / file).read_text()) == code((candidate / file).read_text()), file
        parity[file] = {'executable_ast': True, 'bytes': sha(ROOT / file) == sha(candidate / file)}
    verification_dir = WORK / 'evidence/outcome-implementation/attempt-1'
    verified = json.loads((verification_dir / 'summary.json').read_text())
    assert verified['result'] == 'PASS' and verified['executed_groups'] == 750
    assert verified['explicit_live_skips'] == 3 and len(verified['checks']) == 30
    for file, digest in verified['working_runtime_sha256'].items():
        assert sha(ROOT / file) == digest, file
        text = (ROOT / file).read_text()
        ast.parse(text, feature_version=(3, 7))
        compile(text, file, 'exec')
    logs = {}
    for check in verified['checks']:
        assert check['passed'] and check['exit_code'] == 0 and not check['watchdog_killed']
        log = verification_dir / check['log']
        text = log.read_text()
        assert sum('! skipped' in line for line in text.splitlines()) == check['live_skips']
        if check['name'].startswith('test_'):
            pairs = re.findall(r'Passed:\s*(\d+)\s*/\s*(\d+)', text)
            if pairs:
                observed = list(map(int, pairs[-1]))
            else:
                simple = re.findall(r'^(\d+) passed; (\d+) failed$', text, re.M)
                if simple:
                    good, bad = map(int, simple[-1]); observed = [good, good + bad]
                else:
                    count = int(re.findall(r'^Ran (\d+) tests? in ', text, re.M)[-1])
                    assert re.search(r'^OK$', text, re.M)
                    observed = [count, count]
            assert observed == check['counts'] and observed[0] == observed[1]
        logs[check['log']] = sha(log)
    old = methods(git('show', BASE + ':tgdata/tgdata.py'), 'TgData')
    new = methods((ROOT / 'tgdata/progress_facade.py').read_text(), 'ProgressFacade')
    moved = []
    for name, node in new.items():
        if not name.startswith('_'):
            assert ast.dump(CodeOnly().visit(node), include_attributes=False) == ast.dump(CodeOnly().visit(old[name]), include_attributes=False)
            moved.append(name)
    permanent = {n.name: ast.dump(n, include_attributes=False)
                 for n in ast.parse((ROOT / 'tgdata/smoke_tests/test_40_pool_outcomes.py').read_text()).body
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    functions = []
    for file in ['cases.py', 'review_controls.py']:
        for node in ast.parse((WORK / 'probes/outcome' / file).read_text()).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name != 'main':
                assert permanent[node.name] == ast.dump(node, include_attributes=False)
                functions.append(node.name)
    assert len(functions) == 35 and len(moved) == 10
    extra = [p for p in git('diff', '--name-only', BASE + '...' + SUBJECT).splitlines() if p not in paths]
    assert all(p.startswith('devdocs/') for p in extra)
    result = dict(result='PASS', base=BASE, subject=SUBJECT, product=PRODUCT, product_paths=paths,
                  ancestry_commits=commits, adjacent_modules_unchanged=stable, prebuild_parity=parity,
                  tested_file_hashes=len(verified['working_runtime_sha256']), moved_public_methods=moved,
                  identical_promoted_functions=functions, executed_groups=750, live_skips=3, demos=3,
                  verified_log_sha256=logs, product_sha256={p: sha(ROOT / p) for p in paths},
                  archive_only_paths=extra)
    out = WORK / 'evidence/review3'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'merge-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(result='PASS', product_files=len(paths), ancestry=len(commits),
                         adjacent_unchanged=len(stable), prebuild_runtime_ast=len(parity),
                         tested_hashes=result['tested_file_hashes'], promoted_functions=len(functions),
                         moved_methods=len(moved), executed_groups=750, live_skips=3, demos=3)))


if __name__ == '__main__':
    main()
