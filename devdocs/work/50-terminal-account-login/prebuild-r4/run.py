"""One complete prebuild, with source manifests and unchanged product enforcement."""
import ast,hashlib,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
files=[HERE/'candidate_login_cli.py',HERE/'combined_suite.py']
product=[ROOT/'tgdata'/name for name in ('login_cli.py','login_file.py','login.py','session_store.py','account_operation.py','connection_engine.py')]
def digest(paths):return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=digest(files+product)
for p in files:compile(p.read_text(),str(p),'exec');ast.parse(p.read_text(),feature_version=(3,7))
start=time.monotonic()
with (HERE/'attempt-1.txt').open('w') as out:
 try:r=subprocess.run([sys.executable,str(HERE/'combined_suite.py')],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=120);code=r.returncode
 except subprocess.TimeoutExpired:code=None
text=(HERE/'attempt-1.txt').read_text()
unchanged=before==digest(files+product)
report=dict(result='PASS' if code==0 and unchanged else 'FAIL',exit=code,seconds=round(time.monotonic()-start,3),source_unchanged=unchanged,sha256=before,
 phase_cases=text.count('PTY_PHASE '),baseline_pty=text.count('PTY '),review_histories=text.count('REVIEW_HISTORY '),stop_phases=text.count('STOP_PHASE '),publication_phases=text.count('PUBLICATION_STOP '))
(HERE/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
print('\n'.join(text.splitlines()[-12:]),flush=True)
raise SystemExit(0 if report['result']=='PASS' else 1)
