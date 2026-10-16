"""Actual getpass/PTY: first SIGINT during restoration after input/EOF versus read stop."""
import json,os,select,signal,socket,subprocess,sys,tempfile,termios,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path('/private/tmp/tgdata-50-terminal-login-pr');sys.path.insert(0,str(ROOT))
from tgdata.smoke_tests import test_48_terminal_login as t
HERE=Path(__file__).resolve().parent

def child(mode):
 with t.fixture() as (config,s,root,target,old):
  before=termios.tcgetattr(0);native=termios.tcsetattr;fired=[False]
  def restoring(fd,when,attrs):
   if attrs[3]&termios.ECHO and not fired[0]:
    fired[0]=True
    print('SIGNAL_AT_RESTORE',flush=True)
    os.kill(os.getpid(),signal.SIGINT)
   return native(fd,when,attrs)
  try:
   with patch('builtins.input',t.ORIGINAL_INPUT),patch.object(t.cli.getpass,'getpass',t.ORIGINAL_GETPASS),patch.object(termios,'tcsetattr',restoring):
    status=t.cli.main(['--config',config])
   after=termios.tcgetattr(0)
   result=dict(case=mode,exit=status,signal_at_restore=fired[0],terminal_restored=before==after,
      echo_enabled=bool(after[3]&termios.ECHO),saved=target.exists(),codes=s.calls.count('SendCodeRequest'))
   print('RESULT '+json.dumps(result),flush=True)
   assert status==130 and fired[0] and not target.exists() and not s.calls
  finally:native(0,termios.TCSANOW,before)

def parent(mode):
 import pty,fcntl
 with tempfile.TemporaryDirectory(prefix='pr51-input-restore-') as tmp:
  master,slave=pty.openpty()
  def terminal():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
  process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',mode],stdin=slave,stdout=slave,stderr=slave,
    cwd=ROOT,env=dict(os.environ,TMPDIR=tmp,PYTHONDONTWRITEBYTECODE='1'),preexec_fn=terminal)
  os.close(slave);data=bytearray();sent=False;deadline=time.monotonic()+8
  try:
   while time.monotonic()<deadline:
    ready,_,_=select.select([master],[],[],0.05)
    if ready:
     try:block=os.read(master,65536)
     except OSError:block=b''
     if not block:break
     data.extend(block)
    if b'Phone number with country code (hidden):' in data and not sent:
     sent=True
     if mode=='normal_input':os.write(master,(t.fx.PHONE+'\n').encode())
     elif mode=='eof':os.write(master,b'\x04')
     else:os.kill(process.pid,signal.SIGINT)
    if process.poll() is not None and not ready:break
   if process.poll() is None:raise AssertionError('child failed to finish')
   text=data.decode(errors='replace');t.no_secrets(text)
   result=json.loads(next(line[7:] for line in text.splitlines() if line.startswith('RESULT ')))
   assert process.returncode==0
   result['child_exit']=process.returncode
   return result
  finally:
   if process.poll() is None:process.kill();process.wait(timeout=3)
   os.close(master)

if __name__=='__main__':
 with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
  if len(sys.argv)>1:child(sys.argv[2])
  else:
   rows=[parent(mode) for mode in ('normal_input','eof','read_stop_control')]
   (HERE/'input-restore-result.json').write_text(json.dumps(rows,indent=2)+'\n')
   for row in rows:print(json.dumps(row),flush=True)
