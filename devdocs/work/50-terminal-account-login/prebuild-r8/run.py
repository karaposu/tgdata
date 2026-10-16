"""Complete experiment: every matrix must pass and all source hashes stay fixed."""
import ast,hashlib,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
number=1
while (HERE/('attempt-%d.txt'%number)).exists():number+=1
paths=list(HERE.glob('*.py'))+list((ROOT/'tgdata').rglob('*.py'))
def digest():return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=digest()
for p in HERE.glob('candidate_*.py'):compile(p.read_text(),str(p),'exec');ast.parse(p.read_text(),feature_version=(3,7))
scripts=('combined_suite.py','terminal_matrix.py','framing_matrix.py','handoff_matrix.py','verify_install.py')
start=time.monotonic();codes={}
with (HERE/('attempt-%d.txt'%number)).open('w') as out:
    for script in scripts:
        out.write('RUN '+script+'\n');out.flush()
        try:
            result=subprocess.run([sys.executable,str(HERE/script)],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PIP_NO_INDEX='1'),stdout=out,stderr=subprocess.STDOUT,timeout=180)
            codes[script]=result.returncode
        except subprocess.TimeoutExpired:codes[script]=None
text=(HERE/('attempt-%d.txt'%number)).read_text();after=digest()
counts=dict(retained_pty=text.count('PTY_PHASE ')+text.count('PTY '),review_histories=text.count('REVIEW_HISTORY '),stop_phases=text.count('STOP_PHASE '),publication_phases=text.count('PUBLICATION_STOP '),terminal_cases=text.count('OWNED_TERMINAL '),profile_control=text.count('PROFILE_CONTROL '),framing_cases=text.count('FRAMING '),handoff_cases=text.count('HANDOFF_CASE '))
expected=dict(retained_pty=25,review_histories=17,stop_phases=8,publication_phases=14,terminal_cases=50,profile_control=20,framing_cases=46,handoff_cases=7)
passed=all(v==0 for v in codes.values()) and before==after and counts==expected and '23 passed; 0 failed' in text
report=dict(result='PASS' if passed else 'FAIL',attempt=number,exit_codes=codes,seconds=round(time.monotonic()-start,3),source_unchanged=before==after,counts=counts,expected=expected,sha256=before)
(HERE/('result-attempt-%d.json'%number)).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='sha256'}),flush=True)
print('\n'.join(text.splitlines()[-15:]),flush=True)
raise SystemExit(0 if passed else 1)
