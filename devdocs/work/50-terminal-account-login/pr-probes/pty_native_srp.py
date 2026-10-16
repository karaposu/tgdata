"""Real hidden-input terminal and real SRP interrupted by SIGINT during computation."""
import json,os,sys,socket,signal,threading,subprocess,tempfile,time,select
from pathlib import Path
from unittest.mock import patch
ROOT=Path('/private/tmp/tgdata-50-terminal-login-pr');sys.path.insert(0,str(ROOT))
from tgdata import login
from tgdata.smoke_tests import test_48_terminal_login as t
HERE=Path(__file__).resolve().parent

def child():
 with t.fixture(two_factor=True) as (config,s,root,target,previous):
  compute=login.srp.compute_check
  def timed(*args):
   active=[True]
   def interrupt():
    print('SIGINT_NATIVE_SRP_ACTIVE='+str(active[0]),flush=True)
    os.kill(os.getpid(),signal.SIGINT)
   timer=threading.Timer(0.002,interrupt);timer.start()
   try:return compute(*args)
   finally:active[0]=False;timer.join()
  with patch('builtins.input',t.ORIGINAL_INPUT),patch.object(t.cli.getpass,'getpass',t.ORIGINAL_GETPASS),patch.object(login.srp,'compute_check',timed):
   result=t.cli.main(['--config',config])
  print('CHILD_RESULT',result,'saved',target.exists(),flush=True)

def parent():
 import pty,fcntl,termios
 with tempfile.TemporaryDirectory(prefix='pr51-pty-owned-') as tmp:
  master,slave=pty.openpty()
  def terminal():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
  process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'child'],stdin=slave,stdout=slave,stderr=slave,
      env=dict(os.environ,TMPDIR=tmp,PYTHONDONTWRITEBYTECODE='1'),cwd=ROOT,preexec_fn=terminal)
  os.close(slave);data=bytearray();sent=0;extra=False;start=time.monotonic();effect_at=None
  prompts=[('Phone number with country code (hidden):',t.fx.PHONE),('Telegram code (hidden):',t.fx.CODE),('Two-factor password (hidden):',t.fx.PASSWORD)]
  try:
   while time.monotonic()-start<7:
    ready,_,_=select.select([master],[],[],0.05)
    if ready:
     try:block=os.read(master,65536)
     except OSError:block=b''
     if not block:break
     data.extend(block)
    text=data.decode(errors='replace')
    if sent<len(prompts) and prompts[sent][0] in text:
     os.write(master,(prompts[sent][1]+'\n').encode());sent+=1
    if 'SIGINT_NATIVE_SRP_ACTIVE=True' in text and effect_at is None:effect_at=time.monotonic()
    if effect_at and not extra and time.monotonic()-effect_at>0.25:
     os.kill(process.pid,signal.SIGINT);extra=True
    if process.poll() is not None:break
   timed_out=process.poll() is None
   if timed_out:process.kill()
   process.wait(timeout=3)
   text=data.decode(errors='replace');t.no_secrets(text)
   report=dict(native_srp_interrupted='SIGINT_NATIVE_SRP_ACTIVE=True' in text,all_hidden_inputs_sent=sent==3,
      additional_sigint_sent=extra,timed_out=timed_out,exit=process.returncode,child_result='CHILD_RESULT' in text,secret_echo=False,
      transcript=text)
   (HERE/'pty-native-srp-result.json').write_text(json.dumps(report,indent=2)+'\n')
   print(json.dumps({k:v for k,v in report.items() if k!='transcript'}),flush=True)
   assert report['native_srp_interrupted'] and report['all_hidden_inputs_sent'] and report['timed_out'] and not report['child_result']
  finally:
   if process.poll() is None:process.kill();process.wait(timeout=3)
   os.close(master)

if __name__=='__main__':
 with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
  if len(sys.argv)>1:child()
  else:parent()
