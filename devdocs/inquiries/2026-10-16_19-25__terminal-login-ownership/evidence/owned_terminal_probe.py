"""Inquiry-only terminal-boundary feasibility, not a product candidate or login flow."""
import errno,fcntl,json,os,pty,select,signal,subprocess,sys,termios,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
MODES=('normal','unicode','editing','eof','invalid_encoding','long_input',
 'stop_acquired','stop_snapshot','stop_hidden','stop_wait','stop_read_complete',
 'stop_restore_normal','stop_restored_normal','stop_close_normal','stop_restore_eof',
 'stop_restored_eof','repeated_stop','apply_fail_before','apply_fail_after','restore_fail',
 'restore_fail_stop','snapshot_fail')

class Stopped(Exception):pass

def observe(mode):
 stopped=[False];signals=[0];events=[];original=None;fd=None;value=None;outcome='error';failure=None;restored=False
 previous=signal.getsignal(signal.SIGINT)
 def signal_stop(*args):stopped[0]=True;signals[0]+=1
 signal.signal(signal.SIGINT,signal_stop)
 def point(stage):
  events.append(stage)
  target={'stop_acquired':'acquired','stop_snapshot':'snapshot','stop_hidden':'hidden',
   'stop_read_complete':'read_complete','stop_restore_normal':'restore','stop_restored_normal':'restored',
   'stop_close_normal':'close','stop_restore_eof':'restore','stop_restored_eof':'restored',
   'restore_fail_stop':'restore'}.get(mode)
  if stage==target or mode=='repeated_stop' and stage in ('restore','restored'):os.kill(os.getpid(),signal.SIGINT)
 try:
  try:
   fd=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK);point('acquired')
   if mode=='snapshot_fail':raise OSError(errno.EIO,'synthetic snapshot fault')
   original=termios.tcgetattr(fd);point('snapshot')
   if stopped[0]:raise Stopped()
   assert original[3]&termios.ICANON,'probe qualifies canonical input only'
   hidden=original[:];hidden[3]&=~termios.ECHO
   if mode=='apply_fail_before':raise OSError(errno.EIO,'synthetic apply fault')
   termios.tcsetattr(fd,termios.TCSANOW,hidden)
   if mode=='apply_fail_after':raise OSError(errno.EIO,'synthetic post-apply fault')
   assert not termios.tcgetattr(fd)[3]&termios.ECHO
   point('hidden')
   if stopped[0]:raise Stopped()
   print('OWNED_PROMPT',flush=True)
   data=bytearray()
   while True:
    if stopped[0]:raise Stopped()
    ready,_,_=select.select([fd],[],[],0.02)
    if stopped[0]:raise Stopped()
    if not ready:continue
    try:chunk=os.read(fd,129)
    except BlockingIOError:continue
    if not chunk:outcome='eof';break
    data.extend(chunk)
    if len(data)>128:raise ValueError('input_limit')
    if b'\n' in data:
     value=bytes(data).split(b'\n',1)[0].decode('utf-8');outcome='value';break
   point('read_complete')
  except Stopped:outcome='stop'
  except Exception as error:failure=type(error).__name__;outcome='error'
  finally:
   if fd is not None:
    if original is not None:
     try:
      point('restore')
      if mode in ('restore_fail','restore_fail_stop'):raise OSError(errno.EIO,'synthetic restore fault')
      termios.tcsetattr(fd,termios.TCSAFLUSH,original)
      restored=termios.tcgetattr(fd)==original
      point('restored')
      if not restored:failure='restore_mismatch'
     except Exception:failure='restore_failed';restored=False
    point('close');os.close(fd)
   if stopped[0]:outcome='stop'
   if not restored and original is not None:outcome='error'
   if outcome!='value' or failure is not None:value=None
  return dict(mode=mode,outcome=outcome,failure=failure,stop=stopped[0],signals=signals[0],
    restored=restored,value_present=value is not None,value_correct=None if value is None else value=={'normal':'abc','unicode':'éπ💬','editing':'ac'}.get(mode),
    fd_closed=fd is None or is_closed(fd),events=events)
 finally:signal.signal(signal.SIGINT,previous)

def is_closed(fd):
 try:os.fstat(fd)
 except OSError as e:return e.errno==errno.EBADF
 return False

def child(mode):
 before=termios.tcgetattr(0)
 try:
  result=observe(mode);result['observed_restored']=termios.tcgetattr(0)==before
  if mode in ('restore_fail','restore_fail_stop'):
   assert not result['restored'] and not result['observed_restored'] and result['failure']=='restore_failed' and not result['value_present']
  else:assert result['observed_restored'],result
  assert result['fd_closed']
  if mode in ('normal','unicode','editing'):assert result['outcome']=='value' and result['value_correct']
  elif mode=='eof':assert result['outcome']=='eof'
  elif mode.startswith('stop_') or mode=='repeated_stop':assert result['stop'] and not result['value_present']
  else:assert result['failure'] and not result['value_present']
  print('RESULT '+json.dumps(result),flush=True)
 finally:termios.tcsetattr(0,termios.TCSANOW,before)

def parent(mode):
 master,slave=pty.openpty()
 def control():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
 proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',mode],stdin=slave,stdout=slave,stderr=slave,preexec_fn=control)
 os.close(slave);data=bytearray();sent=False;deadline=time.monotonic()+5
 try:
  while time.monotonic()<deadline:
   ready,_,_=select.select([master],[],[],0.03)
   if ready:
    try:block=os.read(master,65536)
    except OSError:block=b''
    if not block:break
    data.extend(block)
   if b'OWNED_PROMPT' in data and not sent:
    sent=True
    if mode in ('stop_wait','repeated_stop'):os.kill(proc.pid,signal.SIGINT)
    elif mode in ('eof','stop_restore_eof','stop_restored_eof'):os.write(master,b'\x04')
    else:
     payload={'unicode':'éπ💬\n'.encode(),'editing':b'ab\x7fc\n','invalid_encoding':b'\xff\n','long_input':b'x'*256+b'\n'}.get(mode,b'abc\n')
     os.write(master,payload)
   if proc.poll() is not None and not ready:break
  try:proc.wait(timeout=max(0.1,deadline-time.monotonic()))
  except subprocess.TimeoutExpired:raise AssertionError('probe timeout '+mode)
  text=data.decode(errors='replace')
  assert proc.returncode==0,(mode,text)
  result=json.loads(next(line[7:] for line in text.splitlines() if line.startswith('RESULT ')))
  # Raw payloads are never printed; RESULT contains only observations/booleans.
  assert 'éπ💬' not in text and 'abc\r\n' not in text and 'x'*20 not in text
  return result
 finally:
  if proc.poll() is None:proc.kill();proc.wait(timeout=2)
  os.close(master)

if __name__=='__main__':
 if len(sys.argv)>1:child(sys.argv[2])
 else:
  rows=[]
  for mode in MODES:
   result=parent(mode);rows.append(result);print(json.dumps({k:v for k,v in result.items() if k!='events'}),flush=True)
  (HERE/'owned-terminal-result.json').write_text(json.dumps(dict(result='PASS',cases=rows),indent=2)+'\n')
