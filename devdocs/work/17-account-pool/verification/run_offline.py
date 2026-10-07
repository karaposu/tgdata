import concurrent.futures, json, os, re, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[4]
logs=root/'devdocs/work/17-account-pool/verification';logs.mkdir(exist_ok=True)
python=sys.executable
missing=str(logs/'__intentionally_missing_live_config__.ini')
assert not Path(missing).exists()
modules=['test_31_account_pool','test_30_backfill_integration','test_29_backfill_public',
 'test_28_backfill_controls','test_27_backfill_pacing','test_26_backfill_completion',
 'test_25_backfill_delivery','test_24_backfill_state','test_23_fixed_windows',
 'test_22_daily_continuation','test_19_message_batches','test_18_read_budget',
 'test_17_session_store','test_16_health_events','test_15_login_checks',
 'test_14_flood_threshold','test_13_device_identity','test_12_proxy']
jobs=[(m,[python,'-m','tgdata.smoke_tests.'+m]+([missing] if m.startswith(('test_12_','test_13_')) else [])) for m in modules]
helper='''import asyncio
from tgdata.smoke_tests import test_11_discover_groups as t
async def run():
    assert await t.test_query_builder()
    assert await t.test_empty_frame()
    print('Passed: 2/2 explicitly awaited offline helpers')
asyncio.run(run())
'''
jobs.append(('test11_helpers',[python,'-c',helper]))
for name in ('daily_continuation','backfill_runs','account_pool'):
 jobs.append((name+'_example',[python,'examples/'+name+'.py','--demo']))
def run(job):
 name,args=job
 try:
  result=subprocess.run(args,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
  output=result.stdout;code=result.returncode
 except subprocess.TimeoutExpired as e:
  output=(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else (e.stdout or '')
  output+='\nRUNNER TIMEOUT';code=124
 (logs/(name+'.txt')).write_text(output)
 summaries=re.findall(r'^Passed:.*$',output,re.M)
 skipped=len(re.findall(r'^! skipped',output,re.M))
 record=dict(name=name,returncode=code,summary=summaries,live_skips=skipped)
 print(json.dumps(record),flush=True)
 return record
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
 results=list(executor.map(run,jobs))
(logs/'offline-results.json').write_text(json.dumps(results,indent=2)+'\n')
print('All subprocesses successful:',all(r['returncode']==0 for r in results),flush=True)
sys.exit(0 if all(r['returncode']==0 for r in results) else 1)
