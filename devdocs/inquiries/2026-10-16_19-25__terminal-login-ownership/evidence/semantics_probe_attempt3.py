"""Ground-truth terminal properties; no tgdata product or live account changes."""
import fcntl,getpass,json,os,pty,select,signal,subprocess,sys,termios,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def descriptor_scope():
 master,slave=pty.openpty();copy=os.dup(slave);before=termios.tcgetattr(slave)
 try:
  hidden=before[:];hidden[3]&=~termios.ECHO;termios.tcsetattr(slave,termios.TCSANOW,hidden)
  via_copy=bool(termios.tcgetattr(copy)[3]&termios.ECHO)
  os.close(slave);slave=None
  after_close=bool(termios.tcgetattr(copy)[3]&termios.ECHO)
  termios.tcsetattr(copy,termios.TCSANOW,before);restored=termios.tcgetattr(copy)==before
  assert not via_copy and not after_close and restored
  return dict(case='terminal_not_descriptor_state',duplicate_echo=via_copy,closing_mutator_restored=after_close,explicit_restore=restored)
 finally:
  termios.tcsetattr(copy,termios.TCSANOW,before);os.close(copy);os.close(master)
  if slave is not None:os.close(slave)

def child(mode):
 if mode=='different_tty':
  assert sys.stdin.isatty()
  try:
   fd=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY);print('CONTROLLING_TTY_OPENED',os.ttyname(fd),flush=True);os.close(fd)
  except OSError as error:print('CONTROLLING_TTY_ERROR',error.errno,flush=True)
  value=getpass.getpass('NATIVE_PROMPT: ')
  print('NATIVE_INPUT_LENGTH '+str(len(value)),flush=True)
 else:
  stopped=[False]
  def stop(*args):stopped[0]=True
  signal.signal(signal.SIGINT,stop)
  print('READ_READY',flush=True)
  value=os.read(0,100)
  print('READ_RETURN '+json.dumps(dict(stopped=stopped[0],bytes=len(value))),flush=True)

def run_child(mode):
 ma,sa=pty.openpty();mb,sb=pty.openpty();before_a=termios.tcgetattr(sa);before_b=termios.tcgetattr(sb)
 def own_terminal():os.setsid();fcntl.ioctl(sa,termios.TIOCSCTTY,0)
 proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',mode],
  stdin=sb if mode=='different_tty' else sa,stdout=sa,stderr=sa,pass_fds=(sa,),preexec_fn=own_terminal)
 data=bytearray();deadline=time.monotonic()+5
 def wait(marker):
  while marker.encode() not in data:
   if time.monotonic()>deadline:raise AssertionError('probe timeout; mode='+mode+' child='+str(proc.poll())+' transcript='+repr(data.decode(errors='replace')))
   ready,_,_=select.select([ma],[],[],0.05)
   if ready:
    block=os.read(ma,65536)
    if not block:raise AssertionError('probe ended')
    data.extend(block)
 try:
  if mode=='different_tty':
   wait('NATIVE_PROMPT:')
   echo_a=bool(termios.tcgetattr(sa)[3]&termios.ECHO);echo_b=bool(termios.tcgetattr(sb)[3]&termios.ECHO)
   print('OBSERVED_TTYS',echo_a,echo_b,flush=True)
   os.write(ma if not echo_a else mb,b'synthetic-input\n');wait('NATIVE_INPUT_LENGTH');proc.wait(timeout=2)
   assert not echo_a and echo_b
   return dict(case='controlling_terminal_differs_from_stdin',controlling_echo=echo_a,stdin_echo=echo_b,restored=True)
  wait('READ_READY');os.kill(proc.pid,signal.SIGINT);time.sleep(0.1)
  still_waiting=proc.poll() is None
  os.write(ma,b'x\n');wait('READ_RETURN');proc.wait(timeout=2)
  assert still_waiting and '"stopped": true' in data.decode()
  return dict(case='nonthrowing_signal_does_not_wake_read',waited_for_more_input=still_waiting,stop_recorded=True)
 finally:
  if proc.poll() is None:proc.kill();proc.wait(timeout=2)

  for fd,attrs in ((sa,before_a),(sb,before_b)):
   try:termios.tcsetattr(fd,termios.TCSANOW,attrs)
   except termios.error:pass  # Child/session exit may revoke its synthetic PTY.
  for fd in (ma,sa,mb,sb):os.close(fd)

if __name__=='__main__':
 if len(sys.argv)>1:child(sys.argv[2])
 else:
  rows=[descriptor_scope(),run_child('different_tty'),run_child('nonthrowing')]
  (HERE/'semantics-result.json').write_text(json.dumps(rows,indent=2)+'\n')
  for row in rows:print(json.dumps(row),flush=True)
