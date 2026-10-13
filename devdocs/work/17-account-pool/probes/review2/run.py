"""Outer watchdog and exact subject/probe hashes for fresh PR review."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
OUT=HERE.parents[1]/'evidence/review2'

def main():
    n=1
    while (OUT/('pr-attempt-'+str(n)+'.json')).exists():n+=1
    log=OUT/('pr-attempt-'+str(n)+'.txt');started=time.monotonic();killed=False
    with log.open('w') as stream:
        try:
            result=subprocess.run([sys.executable,str(HERE/'pr_probes.py')],cwd=ROOT,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stream,stderr=subprocess.STDOUT,timeout=35)
            code=result.returncode
        except subprocess.TimeoutExpired:code=None;killed=True
    detail=None
    for line in log.read_text().splitlines():
        try:value=json.loads(line)
        except ValueError:continue
        if 'summary' in value:detail=value['summary']
    result=dict(result='PASS' if code==0 and detail and detail['groups']==detail['passed']==8 else 'FAIL',
        exit_code=code,watchdog_killed=killed,elapsed=round(time.monotonic()-started,3),summary=detail,
        product='a63099e',base='2ddb852',head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        probe_sha256=hashlib.sha256((HERE/'pr_probes.py').read_bytes()).hexdigest(),log=log.name)
    (OUT/('pr-attempt-'+str(n)+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return 0 if result['result']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
