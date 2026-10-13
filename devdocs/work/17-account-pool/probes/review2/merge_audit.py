"""Fidelity audit of the exact renewed PR product and committed verification."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[5]
BASE='2ddb852d917998d003f9db863fce09a92e9c5712'
HEAD='379a94953f3f4c5b6899657afbffa7fc88cb4594'
W=ROOT/'devdocs/work/17-account-pool'

def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True)
def methods(text,cls):
    return {n.name:n for c in ast.parse(text).body if isinstance(c,ast.ClassDef) and c.name==cls
            for n in c.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def normalized(node):
    if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str):
        node.body=node.body[1:]
    return ast.dump(node,include_attributes=False)

def main():
    commits=['09e0277','5ebd59f','e660c52','7872998','91c612f','6c81299','52f31c9','3f535d1','ceda2bf','a63099e',BASE]
    for commit in commits: subprocess.run(['git','merge-base','--is-ancestor',commit,HEAD],cwd=ROOT,check=True)
    paths=git('diff','--name-only',BASE+'...'+HEAD,'--','.',':!devdocs').splitlines()
    assert len(paths)==21 and not any('duncan' in p for p in paths)
    stable=['connection_engine','account_operation','owned_health','group_operations','join_budget',
            'join_client','budget_client','worker','worker_engine','worker_protocol','read_budget','sync_store','backfill_state','backfill','health']
    for name in stable:
        file='tgdata/'+name+'.py'
        assert git('show',BASE+':'+file)==(ROOT/file).read_text(),file
    candidate=json.loads((W/'evidence/restart/candidate-manifest.json').read_text())
    for file in candidate['changed']:
        assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==candidate['runtime_sha256'][file]
    verification=json.loads((W/'evidence/restart/final-attempt-2/summary.json').read_text())
    for file,value in verification['working_runtime_sha256'].items():
        assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==value,file
    summary=json.loads((W/'evidence/restart/final-summary.json').read_text())
    assert summary['result']=='PASS' and summary['executed_groups']==725 and summary['live_skips']==3
    assert len(summary['checks'])==29 and all(r['passed'] for r in summary['checks'].values())
    old=methods(git('show',BASE+':tgdata/tgdata.py'),'TgData')
    new=methods((ROOT/'tgdata/progress_facade.py').read_text(),'ProgressFacade')
    moved=[]
    for name,node in new.items():
        if name.startswith('_'):continue
        assert normalized(node)==normalized(old[name]),name
        moved.append(name)
    all_names=git('diff','--name-only',BASE+'...'+HEAD).splitlines()
    extra=[p for p in all_names if p not in paths]
    assert all(p.startswith('devdocs/') for p in extra)
    for file in [ROOT/'tgdata/pool_lifecycle.py',ROOT/'tgdata/pool_source.py']:
        assert '.cancelling(' not in file.read_text() and '.uncancel(' not in file.read_text()
    result=dict(result='PASS',base=BASE,subject=HEAD,product='a63099e',product_paths=paths,
        ancestry_commits=len(commits),unchanged_adjacent_modules=stable,
        production_candidate_parity=len(candidate['changed']),verified_python_file_hashes=len(verification['working_runtime_sha256']),
        unchanged_public_progress_methods=moved,executed_offline_groups=725,explicit_live_skips=3,
        examples=3,work_docs_excluded_from_later_merge=extra)
    (W/'evidence/review2/merge-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='work_docs_excluded_from_later_merge'}))

if __name__=='__main__':main()
