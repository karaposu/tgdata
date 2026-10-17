"""Fresh PENDIN context and actual queued-input composition probes."""
import fcntl,hashlib,json,os,pty,select,signal,socket,subprocess,sys,termios,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from tgdata.smoke_tests import _terminal_login_modes as modes
from tgdata.smoke_tests import test_48_terminal_login as t
HERE=Path(__file__).resolve().parent
VARIANTS=('two_terminals','echo_off','stop_acquire','stop_snapshot','stop_hidden',
 'fault_apply_after','fault_output','fault_restore','fault_restore_after','fault_close',
 'istrip','bad_intr','quit_intermediate','suspend_intermediate','intr_intermediate',
 'invalid_utf8','partial_eof','limit128')
QUEUES={'partial':b'queued-private-partial','lines':b'+15550009999\n99999\n',
 'unicode':'queued-éπ💬'.encode(),'stop':b'queued-private-cancel\n'}

def queued_child(mode,ready_fd):
 fd=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY);original=termios.tcgetattr(fd)
 setup=termios.tcgetattr(fd);setup[3]&=~(termios.ECHO|termios.ECHONL)
 termios.tcsetattr(fd,termios.TCSAFLUSH,setup)
 try:
  print('QUEUE_READY',flush=True)
  assert os.read(ready_fd,1)==b'1';os.close(ready_fd)
  setup=termios.tcgetattr(fd);setup[3]|=termios.PENDIN
  termios.tcsetattr(fd,termios.TCSANOW,setup);before=termios.tcgetattr(fd)
  assert before[3]&termios.PENDIN
  returned=[];reader=t.cli.read_hidden
  def observed(prompt,stop_requested):
   value=reader(prompt,stop_requested)
   assert termios.tcgetattr(fd)==before
   expected=t.fx.PHONE if not returned else t.fx.CODE
   assert value==expected,'queued input crossed prompt invitation'
   returned.append(True);return value
  with t.fixture() as (config,s,root,target,old):
   def requests(w,r):
    if isinstance(r,t.functions.auth.SendCodeRequest):assert r.phone_number==t.fx.PHONE.lstrip('+')
    if isinstance(r,t.functions.auth.SignInRequest):assert r.phone_code==t.fx.CODE
    return NotImplemented
   s.hook=requests
   with patch.object(t.cli,'read_hidden',observed):status=t.cli.main(['--config',config])
   stopped=mode=='stop';assert status==(130 if stopped else 0)
   assert termios.tcgetattr(fd)==before
   assert all(not wire.up for wire in s.wires)
   assert s.calls.count('SendCodeRequest')==(0 if stopped else 1)
   assert len(returned)==(0 if stopped else 2)
   if stopped:assert not target.exists()
   else:t.reopen(config,s)
   print('\nQUEUE_RESULT '+json.dumps(dict(mode=mode,initial_pendin=True,restored=True,exit=status,inputs=len(returned),codes=s.calls.count('SendCodeRequest'),queued_admitted=False)),flush=True)
 finally:termios.tcsetattr(fd,termios.TCSAFLUSH,original);os.close(fd)
 return 0

def queued_parent(mode):
 master,slave=pty.openpty();ready_r,ready_w=os.pipe()
 def own():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
 p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--queued-child',mode,str(ready_r)],stdin=slave,stdout=slave,stderr=slave,pass_fds=(ready_r,),preexec_fn=own,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 os.close(slave);os.close(ready_r);os.set_blocking(master,False)
 data=bytearray();pending=b'';stage=0;seen={};requested=written=0;deadline=time.monotonic()+15
 try:
  while time.monotonic()<deadline:
   r,w,_=select.select([master],[master] if pending else [],[],.005)
   if r:
    try:b=os.read(master,65536)
    except OSError:b=b''
    if not b:break
    data.extend(b)
   text=data.decode(errors='replace')
   if 'QUEUE_READY' in text and stage==0:pending=QUEUES[mode];requested+=len(pending);stage=1
   if w and pending:
    try:n=os.write(master,pending)
    except BlockingIOError:n=0
    written+=n;pending=pending[n:]
    if not pending and stage==1:os.write(ready_w,b'1');stage=2
   for phase,marker in [('phone','Phone number with country code (hidden):'),('code','Telegram code (hidden):')]:
    count=text.count(marker)
    if count>seen.get(phase,0):
     assert count==1 and not pending
     seen[phase]=count
     pending=b'\x03' if mode=='stop' else (t.fx.PHONE+'\n').encode() if phase=='phone' else (t.fx.CODE+'\n').encode()
     requested+=len(pending)
   if p.poll() is not None and not r:break
  p.wait(timeout=max(.1,deadline-time.monotonic()))
  text=data.decode(errors='replace');assert p.returncode==0,(mode,text)
  assert requested==written and stage==2
  t.no_secrets(text)
  for secret in ('queued-private','+15550009999','99999','éπ💬'):assert secret not in text
  result=json.loads(next(line[13:] for line in text.splitlines() if line.startswith('QUEUE_RESULT ')))
  result.update(producer_requested=requested,producer_written=written)
  return result,text
 finally:
  if p.poll() is None:p.kill();p.wait(timeout=2)
  os.close(master);os.close(ready_w)

def main():
 manifest=json.loads((HERE.parent/'verification/evidence/full/result.json').read_text())['source_sha256']
 for name,h in manifest.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
 rows=[];raw={}
 for variant in VARIANTS:
  row=modes.parent('pendin_'+variant);assert row['initial_pendin'];rows.append(row);print('CONTEXT '+json.dumps(row),flush=True)
 for mode in QUEUES:
  row,text=queued_parent(mode);rows.append(row);raw[mode]=text;print('QUEUED '+json.dumps(row),flush=True)
 for name,h in manifest.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
 (HERE/'result.json').write_text(json.dumps(dict(result='PASS',contexts=len(VARIANTS),queued=len(QUEUES),total=len(rows),cases=rows,source_files_unchanged=len(manifest)),indent=2)+'\n')
 (HERE/'raw-transcripts.json').write_text(json.dumps(raw,indent=2)+'\n')
 return 0

if __name__=='__main__':
 with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
  raise SystemExit(queued_child(sys.argv[2],int(sys.argv[3])) if len(sys.argv)>1 else main())
