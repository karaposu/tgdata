"""Native hidden canonical transition: does the quit key regain signal behavior?"""
import fcntl,json,os,pty,select,signal,subprocess,sys,termios,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def child(mode):
 fd=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
 old=termios.tcgetattr(fd);seen=[];previous=signal.getsignal(signal.SIGQUIT)
 signal.signal(signal.SIGQUIT,lambda *args:seen.append('SIGQUIT'))
 try:
  hidden=old[:];hidden[6]=old[6][:]
  hidden[3]&=~(termios.ECHO|termios.ECHONL|termios.ICANON|termios.IEXTEN)
  hidden[0]&=~(termios.IXON|termios.IXOFF|getattr(termios,'IXANY',0))
  disabled=bytes([os.fpathconf(fd,'PC_VDISABLE')])
  hidden[6][termios.VQUIT]=disabled;hidden[6][termios.VSUSP]=disabled
  hidden[6][termios.VMIN]=1;hidden[6][termios.VTIME]=0
  termios.tcsetattr(fd,termios.TCSANOW,hidden)
  stage=(old if mode=='original_based' else hidden)[:]
  stage[6]=(old if mode=='original_based' else hidden)[6][:]
  stage[3]=(stage[3]&~(termios.ECHO|termios.ECHONL))|termios.ICANON
  termios.tcsetattr(fd,termios.TCSANOW,stage)
  print('STAGE_READY',flush=True)
  time.sleep(0.2)
  echo=bool(termios.tcgetattr(fd)[3]&termios.ECHO)
  assert not echo
  assert bool(seen)==(mode=='original_based')
  termios.tcflush(fd,termios.TCIFLUSH)
  termios.tcsetattr(fd,termios.TCSANOW,old)
  assert termios.tcgetattr(fd)==old
  print('RESULT '+json.dumps(dict(mode=mode,quit_signal_while_hidden=bool(seen),echo_during_stage=echo,restored=True)),flush=True)
 finally:
  termios.tcsetattr(fd,termios.TCSAFLUSH,old);os.close(fd);signal.signal(signal.SIGQUIT,previous)

def parent(mode):
 m,s=pty.openpty()
 def control():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
 proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',mode],stdin=s,stdout=s,stderr=s,preexec_fn=control)
 os.close(s);data=bytearray();sent=False;deadline=time.monotonic()+4
 try:
  while time.monotonic()<deadline:
   if select.select([m],[],[],0.01)[0]:
    try:b=os.read(m,65536)
    except OSError:b=b''
    if not b:break
    data.extend(b)
   if b'STAGE_READY' in data and not sent:os.write(m,b'\x1c');sent=True
   if proc.poll() is not None:break
  proc.wait(timeout=max(.1,deadline-time.monotonic()))
  text=data.decode();assert proc.returncode==0,text
  return json.loads(next(x[7:] for x in text.splitlines() if x.startswith('RESULT ')))
 finally:
  if proc.poll() is None:proc.kill();proc.wait(timeout=2)
  os.close(m)

if __name__=='__main__':
 if len(sys.argv)>1:child(sys.argv[2])
 else:
  rows=[parent(m) for m in ('original_based','protected_based')]
  (HERE/'retirement-control-result.json').write_text(json.dumps(rows,indent=2)+'\n')
  print(json.dumps(rows,indent=2))
