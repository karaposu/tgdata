import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/private/tmp/tgdata19-gate-a-live-20261007')
PROBE='/private/tmp/tgdata-19-backfill-run-lifecycle/devdocs/work/19-backfill-run-lifecycle/live_probe.py'
for name in ('exact_full_followup','empty_window','imported_tail','relative_restart'):
    output=ROOT/(name+'.live.json')
    assert not output.exists()
    time.sleep(5)
    print('Running',name,flush=True)
    args=[sys.executable,PROBE,'--live','--manifest',str(ROOT/(name+'.manifest.json')),
          '--state',str(ROOT/(name+'.sqlite3')),'--config','/Users/ns/Desktop/projects/telegram-group-scraper/config.ini',
          '--budget',str(ROOT/'account-read-budget.sqlite3'),'--output',str(output)]
    with (ROOT/(name+'.live.log')).open('x') as log:
        result=subprocess.run(args,cwd='/Users/ns/Desktop/projects/telegram-group-scraper',
                              stdout=log,stderr=subprocess.STDOUT,timeout=210)
    report=json.loads(output.read_text())
    print(json.dumps(dict(case=name,exit_code=result.returncode,comparison=report.get('comparison'),
        observed=report.get('observed_count'),expected=report.get('expected_count'),
        stop_reasons=report.get('stop_reasons'),unchanged=report.get('lifecycle_state_unchanged'),
        error_type=report.get('error_type'),stop_code=report.get('stop_code'))),flush=True)
    if result.returncode:sys.exit(result.returncode)
