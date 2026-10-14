"""Full revision4 candidate qualification before production adoption."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def main():
    candidate=Path(tempfile.mkdtemp(prefix='tgdata29-r4-candidate-',dir='/private/tmp'))
    for folder in ('tgdata','examples'):
        shutil.copytree(ROOT/folder,candidate/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    targets={'album_assembly.py':'examples/album_assembly.py',
             'test_42_album_assembly.py':'tgdata/smoke_tests/test_42_album_assembly.py'}
    for name,target in targets.items():shutil.copyfile(HERE/name,candidate/target)
    env=dict(os.environ,PYTHONPATH=str(candidate),PYTHONDONTWRITEBYTECODE='1')
    results=[]
    def run(name,command):
        log=HERE/(name+'.txt')
        with log.open('w') as stream:
            try:code=subprocess.run(command,cwd=candidate,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
            except subprocess.TimeoutExpired:code=-1
        value=log.read_text();counts=re.findall(r'Ran (\d+) tests? in ',value)
        passed=code==0
        item=dict(name=name,passed=passed,exit_code=code,log=log.name,
                  cases=int(counts[-1]) if counts else None)
        print(json.dumps(item),flush=True)
        return item
    results.append(run('combined',[sys.executable,'-m','tgdata.smoke_tests.test_42_album_assembly','-v']))
    if results[-1]['passed']:
        numbers={19,22,23,24,25,26,27,28,29,30,31,39,40}
        modules=[p.stem for p in sorted((candidate/'tgdata/smoke_tests').glob('test_*.py'))
                 if p.name.split('_')[1].isdigit() and int(p.name.split('_')[1]) in numbers]
        jobs=[(name,[sys.executable,'-m','tgdata.smoke_tests.'+name]) for name in modules]
        jobs.append(('demo',[sys.executable,str(candidate/'examples/album_assembly.py'),'--demo']))
        with ThreadPoolExecutor(max_workers=4) as executor:
            results.extend(executor.map(lambda job:run(*job),jobs))
    report=dict(result='PASS' if all(r['passed'] for r in results) and len(results)==15 else 'FAIL',
                runtime=sys.version.split()[0],candidate=str(candidate),results=results,
                sha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in targets},
                unchanged_core_sha256=hashlib.sha256((candidate/'tgdata/album.py').read_bytes()).hexdigest())
    (HERE/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FULL COMBINED PREBUILD',report['result'],flush=True)
    return 0 if report['result']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
