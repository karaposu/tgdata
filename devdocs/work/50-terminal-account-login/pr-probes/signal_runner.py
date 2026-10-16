import json,os,subprocess,sys,tempfile
from pathlib import Path
p=Path(__file__).resolve().parent;out=[]
for diagnostic in (False,True):
 for kind in ('phone','password'):
  with tempfile.TemporaryDirectory(prefix='pr51-signal-owned-') as temp:
   command=[sys.executable,str(p/'signal_inside_action.py'),kind]+(['--diagnostic'] if diagnostic else [])
   try:
    r=subprocess.run(command,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=temp),capture_output=True,text=True,timeout=5)
    row=dict(case=kind,diagnostic=diagnostic,timed_out=False,exit=r.returncode,output=r.stdout,error=r.stderr)
   except subprocess.TimeoutExpired as e:
    row=dict(case=kind,diagnostic=diagnostic,timed_out=True,timeout_seconds=5,output=(e.stdout or b'').decode(),error=(e.stderr or b'').decode())
   out.append(row);print(json.dumps(row),flush=True)
(p/'signal-diagnostic-result.json').write_text(json.dumps(out,indent=2)+'\n')
