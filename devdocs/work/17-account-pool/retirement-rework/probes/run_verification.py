from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import subprocess
import sys

cwd=Path('/private/tmp/tgdata-17-account-pool')
logs=Path('/private/tmp/tgdata17-rework-verification')
logs.mkdir(exist_ok=True)
missing=logs/'intentionally-missing-config.ini'
assert not missing.exists()
ids=set(range(12,20))|set(range(22,31))|{31,32,33,34,35,36}
files=sorted(p for p in (cwd/'tgdata/smoke_tests').glob('test_*.py') if p.name[5:7].isdigit() and int(p.name[5:7]) in ids)
assert len(files)==23

def run(path):
    command=[sys.executable,'-m','tgdata.smoke_tests.'+path.stem]
    if path.name[5:7] in ('12','13'):
        command.append(str(missing))
    log=logs/(path.stem+'.log')
    with log.open('w') as output:
        result=subprocess.run(command,cwd=str(cwd),stdout=output,stderr=subprocess.STDOUT,timeout=300)
    return dict(suite=path.stem,exit=result.returncode,log=str(log),tail=log.read_text()[-350:])
results=[]
with ThreadPoolExecutor(max_workers=4) as executor:
    futures=[executor.submit(run,p) for p in files]
    for future in as_completed(futures):
        result=future.result()
        results.append(result)
        print(json.dumps(result),flush=True)
(logs/'results.json').write_text(json.dumps(sorted(results,key=lambda x:x['suite']),indent=2))
sys.exit(any(row['exit'] for row in results))
