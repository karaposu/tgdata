"""Bound the fresh PR probes; preserve each attempt's exact source and observations."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
WORK = ROOT/'devdocs/work/17-account-pool'
OUT = WORK/'evidence/review3'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    audit = json.loads((OUT/'merge-audit.json').read_text())
    current = {name:sha(ROOT/name) for name in audit['product_paths']}
    assert current == audit['product_sha256']
    probe = Path(__file__).with_name('pr_probes.py')
    number = 1
    while (OUT/('pr-attempt-{}.json'.format(number))).exists(): number += 1
    stem = 'pr-attempt-{}'.format(number)
    (OUT/(stem+'-probe.py')).write_bytes(probe.read_bytes())
    command = [sys.executable,str(probe)]
    start = time.monotonic(); killed = False
    with (OUT/(stem+'.txt')).open('w') as log:
        try:
            result = subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1'),timeout=90)
            status = result.returncode
        except subprocess.TimeoutExpired:
            status,killed = None,True
    text = (OUT/(stem+'.txt')).read_text()
    summary = None
    for line in text.splitlines():
        if line.startswith('{'):
            value = json.loads(line)
            if 'summary' in value: summary=value['summary']
    unchanged = all(sha(ROOT/name) == digest for name,digest in current.items())
    report = dict(result='PASS' if status == 0 and not killed and unchanged and summary else 'FAIL',
                  exit_code=status,watchdog_killed=killed,summary=summary,command=command,
                  duration_s=round(time.monotonic()-start,3),product_sha256=current,
                  product_unchanged=unchanged,probe_sha256=sha(probe),runner_sha256=sha(Path(__file__)),
                  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    (OUT/(stem+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(text)
    print(json.dumps({key:value for key,value in report.items() if key!='product_sha256'}))
    return 0 if report['result']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
