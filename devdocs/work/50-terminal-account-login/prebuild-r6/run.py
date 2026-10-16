"""One complete candidate run; any product change or failed case fails the gate."""
import ast,hashlib,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
number=1
while (HERE/('attempt-%d.txt'%number)).exists():number+=1
paths=list(HERE.glob('*.py'))+list((ROOT/'tgdata').rglob('*.py'))
def digest():return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=digest()
for p in HERE.glob('candidate_*.py'):compile(p.read_text(),str(p),'exec');ast.parse(p.read_text(),feature_version=(3,7))
start=time.monotonic();codes=[]
with (HERE/('attempt-%d.txt'%number)).open('w') as out:
    for script in ('combined_suite.py','terminal_matrix.py'):
        out.write('RUN '+script+'\n');out.flush()
        try:
            result=subprocess.run([sys.executable,str(HERE/script)],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=150)
            codes.append(result.returncode)
        except subprocess.TimeoutExpired:codes.append(None)
text=(HERE/('attempt-%d.txt'%number)).read_text()
after=digest()
report=dict(result='PASS' if codes==[0,0] and before==after else 'FAIL',attempt=number,exit_codes=codes,seconds=round(time.monotonic()-start,3),source_unchanged=before==after,sha256=before,
 retained_pty=text.count('PTY_PHASE ')+text.count('PTY '),review_histories=text.count('REVIEW_HISTORY '),stop_phases=text.count('STOP_PHASE '),publication_phases=text.count('PUBLICATION_STOP '),owned_terminal=text.count('OWNED_TERMINAL '))
(HERE/('result-attempt-%d.json'%number)).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='sha256'}),flush=True)
print('\n'.join(text.splitlines()[-12:]),flush=True)
raise SystemExit(0 if report['result']=='PASS' else 1)
