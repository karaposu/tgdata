"""One complete P0 attempt, exact candidate hashes, explicit skips and watchdogs."""
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
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
OUT=HERE.parents[1]/'evidence/outcome'


def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()

def main():
    baseline=json.loads((OUT/'export-manifest.json').read_text())
    candidate=json.loads((OUT/'candidate-manifest.json').read_text());source=Path(candidate['source'])
    assert all(sha(source/p)==value for p,value in candidate['sha256'].items())
    script_hashes={p.name:sha(p) for p in HERE.glob('*.py')}
    attempt=1
    while (OUT/('attempt-'+str(attempt))).exists():attempt+=1
    output=OUT/('attempt-'+str(attempt));output.mkdir()
    modules=[]
    for file in sorted((source/'tgdata/smoke_tests').glob('test_*.py')):
        match=re.match(r'test_(\d+)_',file.name)
        if match and int(match[1]) in list(range(12,20))+list(range(22,40)):modules.append(file.stem)
    assert len(modules)==26
    jobs=[(m,[sys.executable,'-m','tgdata.smoke_tests.'+m],120) for m in modules]
    jobs += [('outcome_cases',[sys.executable,str(HERE/'cases.py'),'--source',str(source)],120),
             ('prior_review_controls',[sys.executable,str(HERE/'review_controls.py'),str(source)],60),
             ('baseline_negative_controls',[sys.executable,str(ROOT/'devdocs/inquiries/2026-10-13_11-46__17-public-outcome-ownership/evidence/sense_probe.py')],45)]
    jobs += [('example_'+name,[sys.executable,str(source/'examples'/(name+'.py')),'--demo'],120)
             for name in ('account_pool','daily_continuation','backfill_runs')]
    env=dict(os.environ,PYTHONPATH=str(source),PYTHONDONTWRITEBYTECODE='1')
    results=[]
    with tempfile.TemporaryDirectory(prefix='tgdata17-p0-no-live-') as temp:
        missing=str(Path(temp)/'NO_LIVE_CONFIG.ini');assert not Path(missing).exists()
        for name,cmd,limit in jobs:
            if name.startswith(('test_12_','test_13_')):cmd.append(missing)
        def run(job):
            name,cmd,limit=job;started=time.monotonic();killed=False;log=output/(name+'.txt')
            with log.open('w') as stream:
                try:r=subprocess.run(cmd,cwd=source,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=limit);code=r.returncode
                except subprocess.TimeoutExpired:code=None;killed=True
            text=log.read_text();pair=None
            counts=re.findall(r'Passed:\s*(\d+)\s*/\s*(\d+)',text)
            if counts:pair=tuple(map(int,counts[-1]))
            if pair is None:
                simple=re.findall(r'^(\d+) passed; (\d+) failed$',text,re.M)
                if simple:a,b=map(int,simple[-1]);pair=(a,a+b)
            if pair is None and re.search(r'^OK$',text,re.M):
                unit=re.findall(r'^Ran (\d+) tests? in ',text,re.M)
                if unit:pair=(int(unit[-1]),int(unit[-1]))
            if name=='prior_review_controls':
                for line in text.splitlines():
                    try:value=json.loads(line)
                    except ValueError:continue
                    if 'summary' in value:pair=(value['summary']['passed'],value['summary']['groups'])
            skip=sum('! skipped' in line for line in text.splitlines())
            passed=code==0 and not killed
            if name.startswith('test_') or name in ('outcome_cases','prior_review_controls'):
                passed=passed and pair is not None and pair[0]==pair[1]
            if name=='outcome_cases':passed=passed and pair==(14,14)
            if name=='prior_review_controls':passed=passed and pair==(8,8)
            if name=='baseline_negative_controls':passed=passed and 'PASS: observations match' in text
            return dict(name=name,passed=bool(passed),exit_code=code,watchdog_killed=killed,
                        counts=pair,live_skips=skip,duration_s=round(time.monotonic()-started,3),command=cmd,log=log.name)
        with ThreadPoolExecutor(max_workers=4) as workers:
            futures=[workers.submit(run,job) for job in jobs]
            for future in as_completed(futures):
                row=future.result();results.append(row);print(json.dumps(row),flush=True)
    stable=all(sha(source/p)==value for p,value in candidate['sha256'].items())
    scripts_stable=all(sha(HERE/p)==value for p,value in script_hashes.items())
    production_unchanged=not subprocess.check_output(['git','diff',baseline['baseline'],'--','tgdata','examples','README.md','docs'],cwd=ROOT)
    files=list(source.rglob('*.py'))
    grammar=[]
    for file in files:
        ast.parse(file.read_text(),feature_version=(3,7));compile(file.read_text(),str(file),'exec');grammar.append(str(file.relative_to(source)))
    total=sum(row['counts'][1] for row in results if row['counts'])
    skips=sum(row['live_skips'] for row in results)
    passed=all(row['passed'] for row in results) and stable and scripts_stable and production_unchanged
    summary=dict(result='PASS' if passed else 'FAIL',attempt=attempt,checks=sorted(results,key=lambda row:row['name']),
        candidate_groups_reported=total,candidate_groups_executed=total-skips,explicit_live_skips=skips,
        baseline_negative_control_groups_counted_in_candidate_total=False,
        candidate_unchanged=stable,probes_unchanged=scripts_stable,production_unchanged=production_unchanged,
        compile_and_python37_grammar_files=len(grammar),source=str(source),baseline=baseline,script_sha256=script_hashes)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(dict(result=summary['result'],executed=total-skips,live_skips=skips,
                         output=str(output),candidate_unchanged=stable,production_unchanged=production_unchanged)),flush=True)
    return 0 if passed else 1

if __name__=='__main__':raise SystemExit(main())
