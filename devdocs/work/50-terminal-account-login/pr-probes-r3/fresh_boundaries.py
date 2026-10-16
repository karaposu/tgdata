"""Fresh actual-PTY/SDK/native-file review histories; no product edits or sockets."""
import contextlib, fcntl, json, os, pty, select, signal, socket, subprocess, sys, termios, time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from tgdata.smoke_tests import test_48_terminal_login as t
from tgdata import _terminal_input as ti
HERE=Path(__file__).resolve().parent
CASES=['custom_edit','custom_eof','swapped_erase_eof','noflsh_interrupt',
 'unicode128_password','unicode129_password','erase_unicode_limit','empty_phone',
 'bad_code_typeahead','password_retry','local_retry_two_factor','uncertain_yes',
 'uncertain_no','uncertain_overflow','uncertain_stop_final','uncertain_reinput',
 'unknown_control_phone','overflow_custom_clear','incomplete_utf8_erase','zero_byte',
 'restore_after_phone','intermediate_fail_password','final_flush_fail_code',
 'preprompt_stop_code','close_after_code','mode_change_code','post_return_replace',
 'source_wait','output_fail_discard']+['eof_close_'+p for p in ('phone','code','password','replace','retry','check')]
PROMPTS={'phone':'Phone number with country code (hidden):','code':'Telegram code (hidden):',
 'password':'Two-factor password (hidden):','replace':'Type REPLACE:',
 'retry':'Retry saving this completed login','check':'Check authorization without another code?'}

def password(mode):
 return '💬'*32 if mode=='unicode128_password' else '💬'*31+'abc' if mode=='erase_unicode_limit' else t.fx.PASSWORD

def child(mode):
 native={name:getattr(os,name) for name in ('open','close')};get=termios.tcgetattr;put=termios.tcsetattr;flush=termios.tcflush
 control=native['open']('/dev/tty',os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
 original=get(control);attrs=get(control);handler=signal.getsignal(signal.SIGINT)
 custom=mode in ('custom_edit','custom_eof','overflow_custom_clear')
 if custom:
  attrs[6][termios.VERASE]=b'\x02';attrs[6][termios.VKILL]=b'\x06';attrs[6][termios.VEOF]=b'\x05'
 if mode=='swapped_erase_eof':attrs[6][termios.VERASE]=b'\x04';attrs[6][termios.VEOF]=b'\x7f'
 if mode=='noflsh_interrupt':attrs[3]|=termios.NOFLSH
 put(control,termios.TCSANOW,attrs);baseline=get(control)
 phase={'name':None,'fd':None,'sets':0,'flushes':0,'fired':False,'before_calls':0,'settled':0,'close_attempts':0}
 eof_phase=mode[len('eof_close_'):] if mode.startswith('eof_close_') else None
 two=mode in ('unicode128_password','unicode129_password','erase_unicode_limit','password_retry','local_retry_two_factor','intermediate_fail_password') or eof_phase=='password'
 existing=mode=='post_return_replace' or eof_phase in ('replace','retry')
 check=mode.startswith('uncertain_') or eof_phase=='check'
 try:
  with patch.object(t.fx,'PASSWORD',password(mode)),t.fixture(two_factor=two,existing=existing) as (config,s,root,target,old):
   request_codes=[];prepare_calls=[0];native_prepare=t.publication._prepare_candidate
   def hook(w,r):
    if isinstance(r,t.functions.auth.SendCodeRequest):
     if mode=='mode_change_code':
      changed=get(control);changed[0]|=termios.IGNCR;put(control,termios.TCSANOW,changed)
     if mode=='source_wait':return t.errors.FloodWaitError(r,capture=12)
    if isinstance(r,t.functions.auth.SignInRequest):
     request_codes.append(r.phone_code)
     if check and len(request_codes)==1:
      if mode!='uncertain_reinput':s.answer(w,r)
      return OSError(t.fx.PASSWORD)
    return NotImplemented
   s.hook=hook
   def prepare(*args):
    prepare_calls[0]+=1
    if (mode=='local_retry_two_factor' or eof_phase=='retry') and prepare_calls[0]==1:raise OSError(t.fx.PASSWORD)
    return native_prepare(*args)
   native_read=t.cli.read_hidden
   def reading(prompt,stop_requested):
    phase['name']=next(p for p,marker in PROMPTS.items() if marker in prompt)
    phase.update(fd=None,sets=0,flushes=0,before_calls=len(s.calls))
    value=native_read(prompt,stop_requested)
    phase['settled']+=1
    assert get(control)==baseline,(mode,'returned before exact restoration')
    if mode=='post_return_replace' and phase['name']=='replace':
     phase['fired']=True;os.kill(os.getpid(),signal.SIGINT)
    phase['name']=None
    return value
   def opening(path,*a,**kw):
    fd=native['open'](path,*a,**kw)
    if path=='/dev/tty' and phase['name']:phase['fd']=fd
    return fd
   def setting(fd,when,value):
    owned=fd==phase['fd'] and phase['name'] is not None
    if owned:phase['sets']+=1
    if owned and phase['sets']==2 and mode=='intermediate_fail_password' and phase['name']=='password':
     phase['fired']=True;raise OSError(t.fx.PASSWORD)
    result=put(fd,when,value)
    if owned and phase['sets']==3:
     if mode=='restore_after_phone' and phase['name']=='phone':phase['fired']=True;raise OSError(t.fx.PASSWORD)
     if mode=='uncertain_stop_final' and phase['name']=='check':phase['fired']=True;os.kill(os.getpid(),signal.SIGINT)
    return result
   def flushing(fd,queue):
    owned=fd==phase['fd'] and phase['name'] is not None
    if owned:phase['flushes']+=1
    result=flush(fd,queue)
    if owned and mode=='final_flush_fail_code' and phase['name']=='code' and phase['flushes']==3:
     phase['fired']=True;raise OSError(t.fx.PASSWORD)
    if owned and mode=='preprompt_stop_code' and phase['name']=='code' and phase['flushes']==1:
     phase['fired']=True;os.kill(os.getpid(),signal.SIGINT)
    return result
   def closing(fd):
    owned=fd==phase['fd'] and phase['name'] is not None
    result=native['close'](fd)
    if owned:
     phase['close_attempts']+=1
     if (eof_phase and phase['name']==eof_phase) or (mode=='close_after_code' and phase['name']=='code'):
      phase['fired']=True;raise OSError(t.fx.PASSWORD)
    return result
   printing=print
   def output(*a,**kw):
    if mode=='output_fail_discard' and a and 'Input rejected' in str(a[0]):
     phase['fired']=True;raise OSError(t.fx.PASSWORD)
    return printing(*a,**kw)
   with contextlib.ExitStack() as stack:
    for name,fn in [('open',opening),('close',closing)]:stack.enter_context(patch.object(os,name,fn))
    stack.enter_context(patch.object(termios,'tcsetattr',setting));stack.enter_context(patch.object(termios,'tcflush',flushing))
    stack.enter_context(patch.object(t.cli,'read_hidden',reading));stack.enter_context(patch.object(t.publication,'_prepare_candidate',prepare))
    stack.enter_context(patch('builtins.print',output))
    status=t.cli.main(['--config',config]+(['--replace'] if existing else []))
   saved=mode in ('custom_edit','swapped_erase_eof','unicode128_password','erase_unicode_limit','empty_phone','bad_code_typeahead','password_retry','local_retry_two_factor','uncertain_yes','uncertain_reinput')
   stopped=bool(eof_phase) or mode in ('custom_eof','noflsh_interrupt','uncertain_stop_final','preprompt_stop_code','post_return_replace')
   expected=0 if saved else 130 if stopped else 3
   assert status==expected,(mode,status,expected)
   observed=get(control);restored=observed==baseline
   if mode=='mode_change_code':
    expected_modes=baseline[:];expected_modes[0]|=termios.IGNCR;assert observed==expected_modes
   elif mode!='intermediate_fail_password':assert restored,(mode,'terminal changed')
   assert signal.getsignal(signal.SIGINT)==handler
   assert all(not wire.up for wire in s.wires)
   if saved:
    assert target.exists();t.reopen(config,s)
   elif old is not None:assert target.read_bytes()==old
   else:assert not target.exists()
   codes=s.calls.count('SendCodeRequest');signins=s.calls.count('SignInRequest');proofs=s.calls.count('CheckPasswordRequest')
   no_codes=mode in ('custom_eof','noflsh_interrupt','unknown_control_phone','overflow_custom_clear','incomplete_utf8_erase','zero_byte','restore_after_phone','output_fail_discard') or eof_phase=='phone'
   assert codes==(0 if no_codes else 1),(mode,codes)
   if mode=='bad_code_typeahead':assert request_codes==['99999',t.fx.CODE]
   if mode=='password_retry':assert proofs==2 and s.srp_accepted==1
   if mode=='local_retry_two_factor':assert signins==proofs==1 and prepare_calls[0]==2
   if mode in ('unicode129_password','intermediate_fail_password') or eof_phase=='password':assert proofs==0
   if mode in ('final_flush_fail_code','preprompt_stop_code','close_after_code','mode_change_code') or eof_phase=='code':assert signins==0
   if check:assert signins==(2 if mode=='uncertain_reinput' else 1)
   if mode in ('uncertain_overflow','uncertain_stop_final') or eof_phase=='check':assert len(s.calls)==phase['before_calls']
   if eof_phase or mode in ('restore_after_phone','intermediate_fail_password','final_flush_fail_code','preprompt_stop_code','close_after_code','post_return_replace','uncertain_stop_final','output_fail_discard'):assert phase['fired']
   printing('\nFRESH_RESULT '+json.dumps(dict(mode=mode,exit=status,saved=saved,restored=restored,codes=codes,signins=signins,password_proofs=proofs,settled_inputs=phase['settled'],close_attempts=phase['close_attempts'],fault_or_stop_fired=phase['fired'])),flush=True)
 finally:
  put(control,termios.TCSAFLUSH,original);native['close'](control)
 return 0

def payload(mode,phase,count):
 if mode.startswith('eof_close_') and phase==mode[len('eof_close_'):]:return b'partial\x04'
 if phase=='phone':
  if mode=='custom_edit':return b'wrong\x06'+t.fx.PHONE.encode()+b'\n'
  if mode=='custom_eof':return b'partial\x05'
  if mode=='noflsh_interrupt':return b'private-partial\x03'
  if mode=='empty_phone' and count==1:return b'\n'
  if mode=='unknown_control_phone':return b'bad\x01\x15'+t.fx.PHONE.encode()+b'\n'
  if mode=='overflow_custom_clear':return b'x'*129+b'\x06'+t.fx.PHONE.encode()+b'\n'
  if mode=='incomplete_utf8_erase':return b'\xc3\x7f'+t.fx.PHONE.encode()+b'\n'
  if mode=='zero_byte':return b'private\x00value\n'
  if mode=='output_fail_discard':return b'x'*129+b'\n'
 if phase=='code':
  if mode=='custom_edit':return t.fx.CODE.encode()+b'9\x02\n'
  if mode=='swapped_erase_eof':return t.fx.CODE.encode()+b'9\x04\n'
  if mode=='bad_code_typeahead' and count==1:return b'99999\n'+t.fx.CODE.encode()+b'\n'
 if phase=='password':
  if mode=='unicode129_password':return ('💬'*32+'x\x15'+t.fx.PASSWORD+'\n').encode()
  if mode=='erase_unicode_limit':return ('💬'*32+'\x7fabc\n').encode()
  if mode=='password_retry' and count==1:return b'wrong-private-password\n'
  return (password(mode)+'\n').encode()
 if phase=='check':
  if mode=='uncertain_no':return b'no\n'
  if mode=='uncertain_overflow':return b'x'*129+b'\x15yes\n'
 return ({'phone':t.fx.PHONE,'code':t.fx.CODE,'replace':'REPLACE','retry':'yes','check':'yes'}[phase]+'\n').encode()

def parent(mode):
 master,slave=pty.openpty()
 def own():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
 proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',mode],stdin=slave,stdout=slave,stderr=slave,preexec_fn=own,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 os.close(slave);os.set_blocking(master,False)
 data=bytearray();pending=b'';seen={};wanted=written=0;deadline=time.monotonic()+20
 try:
  while time.monotonic()<deadline:
   r,w,_=select.select([master],[master] if pending else [],[],0.005)
   if r:
    try:block=os.read(master,65536)
    except OSError:block=b''
    if not block:break
    data.extend(block)
   text=data.decode(errors='replace')
   for phase,marker in PROMPTS.items():
    n=text.count(marker)
    if n>seen.get(phase,0):
     assert not pending;seen[phase]=n;pending=payload(mode,phase,n);wanted+=len(pending)
   if w and pending:
    size=1 if mode in ('unicode128_password','erase_unicode_limit','custom_edit') else 4096
    try:n=os.write(master,pending[:size])
    except BlockingIOError:n=0
    written+=n;pending=pending[n:]
   if proc.poll() is not None and not r:break
  proc.wait(timeout=max(.1,deadline-time.monotonic()))
  text=data.decode(errors='replace')
  (HERE/(mode+'.txt')).write_text(text)
  assert proc.returncode==0,(mode,text)
  assert wanted==written,(mode,wanted,written)
  t.no_secrets(text)
  for secret in ('private-partial','wrong-private-password','💬','x'*30):assert secret not in text,(mode,'echo')
  result=json.loads(next(s[13:] for s in text.splitlines() if s.startswith('FRESH_RESULT ')))
  if mode.startswith('eof_close_'):assert 'Input outcome: input_stopped' in text and 'terminal_close_failed' in text
  if mode=='final_flush_fail_code':assert 'terminal_restore_failed' in text
  result.update(producer_requested=wanted,producer_written=written)
  return result
 finally:
  if proc.poll() is None:proc.kill();proc.wait(timeout=2)
  os.close(master)

def main():
 rows=[];failed=[]
 for mode in CASES:
  try:row=parent(mode);rows.append(row);print('FRESH '+json.dumps(row),flush=True)
  except Exception as error:
   failed.append(dict(mode=mode,error=str(error)));print('FAIL',mode,str(error),flush=True)
 report=dict(result='FAIL' if failed else 'PASS',cases=rows,failures=failed,expected=len(CASES))
 (HERE/'fresh-result.json').write_text(json.dumps(report,indent=2)+'\n')
 return bool(failed)

if __name__=='__main__':
 with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
  raise SystemExit(child(sys.argv[2]) if len(sys.argv)>1 else main())
