"""Full PR38 merge-candidate verification, preserving earlier evidence."""
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
REPOSITORY=HERE.parents[2]
BASE='38dee0bbde3259cd2d34a91206afe483132eca59'
PRODUCT=['tgdata/batch_heartbeat.py','tgdata/connection_engine.py','tgdata/batch_engine.py',
 'tgdata/tgdata.py','tgdata/progress_facade.py','tgdata/sync_engine.py',
 'tgdata/backfill_engine.py','tgdata/account_pool.py','tgdata/smoke_tests/test_44_batch_heartbeat.py',
 'docs/batch_heartbeat.md','README.md','tgdata/smoke_tests/README.md']


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(sys.argv[1]).resolve();phase='verification'
    out=HERE/'verification-merge';out.mkdir(exist_ok=True)
    parents=subprocess.check_output(['git','show','-s','--format=%P','HEAD'],cwd=root,text=True).strip().split()
    assert parents==[BASE,'15241bf9a91883137cf154700f6e26fbd64ed085'],parents
    changed=subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=root,text=True).splitlines()
    assert sorted(changed)==sorted(PRODUCT),changed
    sys.path.insert(0,str(root))
    import tgdata,telethon
    assert Path(tgdata.__file__).resolve()==root/'tgdata/__init__.py'
    assert tgdata.__version__=='0.1' and telethon.__version__=='1.45.0'
    original=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'tgdata','examples'],cwd=REPOSITORY,text=True).splitlines()
    original=[name for name in original if name.endswith('.py')]
    for name in original:
        if name in PRODUCT:continue
        prior=subprocess.check_output(['git','show',BASE+':'+name],cwd=REPOSITORY)
        assert (root/name).read_bytes()==prior,'unexpected existing Python change: '+name
    names=sorted(str(p.relative_to(root)) for folder in ('tgdata','examples') for p in (root/folder).rglob('*.py'))
    hashes={name:digest(root/name) for name in names};product={name:digest(root/name) for name in PRODUCT}
    for name in names:
        source=(root/name).read_text();compile(source,name,'exec');ast.parse(source,feature_version=(3,7))
    modules=[p.stem for p in sorted((root/'tgdata/smoke_tests').glob('test_*.py'))
             if p.name.split('_')[1].isdigit() and int(p.name.split('_')[1]) in list(range(12,20))+list(range(22,45))]
    assert len(modules)==31
    selected=modules if phase=='verification' else [name for name in modules
                 if int(name.split('_')[1]) in [14,16,18,19]+list(range(22,32))+[39,40,44]]
    examples=['account_pool','daily_continuation','backfill_runs','reading_worker','stepwise_login','album_assembly','photo_trails'] if phase=='verification' else ['daily_continuation','backfill_runs','account_pool']
    env=dict(os.environ,PYTHONPATH=str(root),PYTHONDONTWRITEBYTECODE='1')
    results=[]
    with tempfile.TemporaryDirectory(prefix='tgdata37-no-live-') as tmp:
        missing=str(Path(tmp)/'MISSING_CONFIG.ini')
        jobs=[]
        for name in selected:
            command=[sys.executable,'-m','tgdata.smoke_tests.'+name]
            if name.startswith(('test_12_','test_13_')):command.append(missing)
            jobs.append((name,command))
        jobs += [('example_'+name,[sys.executable,str(root/'examples'/(name+'.py')),'--demo']) for name in examples]
        def run(job):
            name,command=job;log=out/(name+'.txt');started=time.monotonic();killed=False
            with log.open('w') as stream:
                try:code=subprocess.run(command,cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
                except subprocess.TimeoutExpired:code=None;killed=True
            value=log.read_text();counts=None
            pairs=re.findall(r'Passed:\s*(\d+)\s*/\s*(\d+)',value)
            if pairs:counts=tuple(map(int,pairs[-1]))
            if counts is None:
                pairs=re.findall(r'^(\d+) passed; (\d+) failed$',value,re.M)
                if pairs:
                    good,bad=map(int,pairs[-1]);counts=(good,good+bad)
            if counts is None and re.search(r'^OK$',value,re.M):
                pairs=re.findall(r'^Ran (\d+) tests? in ',value,re.M)
                if pairs:counts=(int(pairs[-1]),int(pairs[-1]))
            passed=code==0 and not killed and (not name.startswith('test_') or counts is not None and counts[0]==counts[1] and counts[0]>0)
            row=dict(name=name,passed=bool(passed),exit_code=code,watchdog_killed=killed,counts=counts,
                     live_skips=sum('! skipped' in line for line in value.splitlines()),
                     duration_s=round(time.monotonic()-started,3),log=log.name)
            print(json.dumps(row),flush=True);return row
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=[future.result() for future in as_completed([pool.submit(run,job) for job in jobs])]
    assert all(digest(root/name)==value for name,value in hashes.items()),'sources changed during verification'
    assert all(digest(root/name)==value for name,value in product.items()),'product files changed during verification'
    skips=sum(r['live_skips'] for r in results)
    report=dict(result='PASS' if all(r['passed'] for r in results) else 'FAIL',phase=phase,path=str(root),
                base=BASE,merged_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
                merged_tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=root,text=True).strip(),
                merged_parents=parents,version=tgdata.__version__,runtime=sys.version.split()[0],telethon=telethon.__version__,
                source_sha256=hashes,product_sha256=product,compile=len(names),python37_grammar=len(names),native_python37=False,
                unchanged_existing_python=sum(name not in PRODUCT for name in original),suite_count=len(selected),demos=len(examples),
                executed_offline=sum(r['counts'][0] for r in results if r['counts'])-skips,live_skips=skips,
                results=sorted(results,key=lambda r:r['name']))
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',report['result'],'suites',len(selected),'offline',report['executed_offline'],'demos',len(examples),'live skips',skips,flush=True)
    return 0 if report['result']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
