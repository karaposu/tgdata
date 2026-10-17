"""Qualify the corrected native oracle and exact PENDIN candidate before adoption."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
files=list((ROOT/'tgdata').rglob('*.py'))+list((ROOT/'examples').rglob('*.py'))+[ROOT/'setup.py']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
candidates={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}
env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1')
code="import runpy; d=runpy.run_path("+repr(str(HERE/'modes_candidate.py'))+"); d['parent']('pendin')"
red=subprocess.run([sys.executable,'-c',code],env=dict(env,PENDIN_PROBE_RELEASED='1'),cwd=ROOT,capture_output=True,text=True,timeout=25)
text=red.stdout+red.stderr;(HERE/'red-baseline.txt').write_text(text)
assert red.returncode==1 and 'terminal_mode_unsupported' in text and '2, 0)' in text,'corrected oracle must fail on released preflight refusal'
started=time.monotonic()
with (HERE/'green-attempt-1.txt').open('w') as log:
 green=subprocess.run([sys.executable,str(HERE/'modes_candidate.py')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=150)
rows=[]
for line in (HERE/'green-attempt-1.txt').read_text().splitlines():
 for prefix in ('OWNED_TERMINAL ','PROFILE_CONTROL ','PENDIN_CONTEXT '):
  if line.startswith(prefix):rows.append((prefix.strip(),json.loads(line[len(prefix):])))
counts={p:sum(a==p for a,r in rows) for p in ('OWNED_TERMINAL','PROFILE_CONTROL','PENDIN_CONTEXT')}
assert green.returncode==0 and counts=={'OWNED_TERMINAL':50,'PROFILE_CONTROL':19,'PENDIN_CONTEXT':11},(green.returncode,counts)
assert all(r['initial_pendin'] for p,r in rows if p=='PENDIN_CONTEXT')
assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in hashes.items())
assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==h for n,h in candidates.items())
report=dict(result='PASS',red_exit=red.returncode,green_exit=green.returncode,counts=counts,cases=[r for p,r in rows],seconds=round(time.monotonic()-started,3),candidate_sha256=candidates,product_sha256=hashes,source_unchanged=True)
(HERE/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(result='PASS',counts=counts,seconds=report['seconds'],source_unchanged=True)))
