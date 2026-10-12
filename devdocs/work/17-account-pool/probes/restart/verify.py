"""Run supported offline suites with real per-process logs and outer deadlines."""
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

ROOT = Path(__file__).resolve().parents[5]
BASE = Path(__file__).resolve().parents[2] / 'evidence/restart'


def main():
    attempt = 1
    while (BASE / ('final-attempt-' + str(attempt))).exists(): attempt += 1
    output = BASE / ('final-attempt-' + str(attempt)); output.mkdir()
    modules=[]
    for file in sorted((ROOT/'tgdata/smoke_tests').glob('test_*.py')):
        match=re.match(r'test_(\d+)_',file.name)
        if match and int(match[1]) in list(range(12,20))+list(range(22,40)):
            modules.append(file.stem)
    if len(sys.argv)>1: modules=[m for m in modules if any(key in m for key in sys.argv[1:])]
    assert modules
    jobs=[(m,[sys.executable,'-m','tgdata.smoke_tests.'+m],120) for m in modules]
    if len(sys.argv)==1:
        jobs += [('example_'+m,[sys.executable,str(ROOT/'examples'/ (m+'.py')),'--demo'],120)
                 for m in ('account_pool','daily_continuation','backfill_runs')]
    env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1')
    results=[]
    with tempfile.TemporaryDirectory(prefix='tgdata17-offline-only-') as temp:
        missing=str(Path(temp)/'NO_LIVE_CONFIG.ini'); assert not Path(missing).exists()
        for name,cmd,limit in jobs:
            if name.startswith(('test_12_','test_13_')): cmd.append(missing)
        def run(job):
            name,cmd,limit=job; started=time.monotonic(); killed=False
            log=output/(name+'.txt')
            with log.open('w') as stream:
                try:
                    result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=limit)
                    code=result.returncode
                except subprocess.TimeoutExpired:
                    code=None; killed=True
            text=log.read_text(); counts=re.findall(r'Passed:\s*(\d+)\s*/\s*(\d+)',text)
            pair=tuple(map(int,counts[-1])) if counts else None
            if pair is None:
                plain=re.findall(r'^(\d+) passed; (\d+) failed$',text,re.M)
                if plain:
                    good,bad=map(int,plain[-1]); pair=(good,good+bad)
            if pair is None and re.search(r'^OK$',text,re.M):
                unit=re.findall(r'^Ran (\d+) tests? in ',text,re.M)
                if unit: pair=(int(unit[-1]),int(unit[-1]))
            skipped=sum('! skipped' in line for line in text.splitlines())
            passed=code==0 and (not name.startswith('test_') or bool(pair and pair[0]==pair[1]))
            return dict(name=name,passed=passed,exit_code=code,watchdog_killed=killed,
                count=pair,skipped=skipped,duration_s=round(time.monotonic()-started,3),command=cmd)
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures=[pool.submit(run,j) for j in jobs]
            for future in as_completed(futures):
                row=future.result();results.append(row);print(json.dumps(row),flush=True)
    files=list((ROOT/'tgdata').rglob('*.py'))+list((ROOT/'examples').glob('*.py'))+[ROOT/'setup.py']
    for file in files: ast.parse(file.read_text(),feature_version=(3,7))
    candidate=json.loads((BASE/'candidate-manifest.json').read_text())
    parity={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==candidate['runtime_sha256'][p]
            for p in candidate['changed']}
    passed=all(r['passed'] for r in results) and all(parity.values())
    total=sum(r['count'][1] for r in results if r['count']); skips=sum(r['skipped'] for r in results)
    summary=dict(result='PASS' if passed else 'FAIL',checks=sorted(results,key=lambda r:r['name']),
        reported_groups=total,explicit_live_skips=skips,executed_groups=total-skips,
        python37_grammar_files=len(files),production_candidate_parity=parity,
        working_runtime_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(dict(result=summary['result'],reported_groups=total,executed_groups=total-skips,
                        live_skips=skips,evidence=str(output))),flush=True)
    return 0 if passed else 1

if __name__=='__main__': raise SystemExit(main())
