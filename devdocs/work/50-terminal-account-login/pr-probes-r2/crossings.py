"""Fresh source/stop/storage crossings on the exact PR product, with real components."""
import asyncio,hashlib,json,os,signal,socket,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path('/private/tmp/tgdata-50-terminal-login-pr');sys.path.insert(0,str(ROOT))
from telethon import functions,errors
from tgdata.smoke_tests import test_48_terminal_login as t
HERE=Path(__file__).resolve().parent
rows=[]

def record(name,**value):
 rows.append(dict(case=name,**value));print(json.dumps(rows[-1]),flush=True)

def source_crossings():
 for mode in ('invalid_phone_stop','wait_and_stop','source_error_and_stop','recovery_complete_stop','recovery_error_stop','known_auth_close_failure_stop'):
  with t.fixture(existing=True) as (config,s,root,target,previous):
   values=[t.fx.PHONE,t.fx.CODE];confirmations=[];fired=[False]
   def stop():
    if not fired[0]:fired[0]=True;os.kill(os.getpid(),signal.SIGINT)
   stack=__import__('contextlib').ExitStack()
   if mode=='invalid_phone_stop':
    values=['invalid phone'];say=t.cli._say
    def output(text):
     say(text)
     if text=='Login: invalid_phone':stop()
    stack.enter_context(patch.object(t.cli,'_say',output))
   elif mode in ('wait_and_stop','source_error_and_stop'):
    values=[t.fx.PHONE]
    def hook(w,r):
     if isinstance(r,functions.auth.SendCodeRequest):
      stop()
      return errors.FloodWaitError(r,capture=12) if mode=='wait_and_stop' else OSError(t.fx.PASSWORD)
     return NotImplemented
    s.hook=hook
   elif mode.startswith('recovery_'):
    confirmations=[True];after_loss=[False]
    def hook(w,r):
     if isinstance(r,functions.auth.SignInRequest):
      s.answer(w,r);after_loss[0]=True;return OSError('lost synthetic authorization reply')
     if isinstance(r,functions.users.GetUsersRequest) and after_loss[0]:
      stop()
      return OSError(t.fx.PASSWORD) if mode=='recovery_error_stop' else NotImplemented
     return NotImplemented
    s.hook=hook
   else:
    faults=[0]
    async def close(w):
     if 'SignInRequest' in s.calls and faults[0]==0:
      faults[0]+=1;stop();raise OSError(t.fx.PASSWORD)
    s.close_hook=close
   with stack:status,text=t.invoke(config,values,confirmations,replace=True)
   assert fired[0] and status==130,(mode,status,text)
   assert target.read_bytes()==previous and all(not w.up for w in s.wires)
   assert s.calls.count('SendCodeRequest')==(0 if mode=='invalid_phone_stop' else 1)
   assert s.calls.count('SignInRequest')<=1
   t.no_secrets(text)
   record(mode,exit=status,old_bytes=True,closed=True,codes=s.calls.count('SendCodeRequest'))


def storage_crossings():
 for mode in ('backup_bytes_stop_error','backup_directory_stop_error','retry_answer_stop','uncertain_then_shutdown_stop','two_local_retries'):
  with t.fixture(existing=True) as (config,s,root,target,previous):
   stack=__import__('contextlib').ExitStack();fired=[False];attempts=[0]
   def stop():
    fired[0]=True;os.kill(os.getpid(),signal.SIGINT)
   answers=[True]
   if mode=='backup_bytes_stop_error':
    sync=t.publication._sync_file
    def file(path):
     if Path(path).name=='previous.session':stop();raise OSError(t.fx.PASSWORD)
     return sync(path)
    stack.enter_context(patch.object(t.publication,'_sync_file',file))
   elif mode=='backup_directory_stop_error':
    sync=t.publication._sync_directory
    def directory(path):
     if (Path(path)/'previous.session').exists():stop();raise OSError(t.fx.PASSWORD)
     return sync(path)
    stack.enter_context(patch.object(t.publication,'_sync_directory',directory))
   elif mode in ('retry_answer_stop','two_local_retries'):
    prepare=t.publication._prepare_candidate
    def prepared(*args):
     attempts[0]+=1
     if attempts[0]<=(2 if mode=='two_local_retries' else 1):raise OSError(t.fx.PASSWORD)
     return prepare(*args)
    stack.enter_context(patch.object(t.publication,'_prepare_candidate',prepared))
    if mode=='two_local_retries':answers=[True,True,True]
    else:
     class Answers:
      def __iter__(self):self.n=0;return self
      def __next__(self):
       self.n+=1
       if self.n==2:stop()
       return True
     answers=Answers()
   else:
    rename=os.replace;sync=t.publication._sync_directory;switched=[False];retire=t.cli._retire
    def replace(src,dst,*args,**kw):
     result=rename(src,dst,*args,**kw)
     if Path(dst)==target:switched[0]=True
     return result
    def directory(path):
     if switched[0] and Path(path)==root:raise OSError(t.fx.PASSWORD)
     return sync(path)
    def finishing(*args):stop();return retire(*args)
    stack.enter_context(patch.object(t.publication.os,'replace',replace))
    stack.enter_context(patch.object(t.publication,'_sync_directory',directory))
    stack.enter_context(patch.object(t.cli,'_retire',finishing))
   with stack:status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],answers,replace=True)
   assert status==(0 if mode=='two_local_retries' else 130),(mode,status,text)
   assert fired[0]==(mode!='two_local_retries')
   if mode=='two_local_retries':assert attempts[0]==3;t.reopen(config,s)
   elif mode=='uncertain_then_shutdown_stop':
    recovery=list(root.glob('.tgdata-login-*'));assert len(recovery)==1
    assert (recovery[0]/'previous.session').read_bytes()==previous
    assert 'publication is uncertain' in text and target.read_bytes()!=previous
   else:assert target.read_bytes()==previous
   assert s.calls.count('SendCodeRequest')==s.calls.count('SignInRequest')==1
   t.no_secrets(text)
   record(mode,exit=status,codes=1,signins=1,local_attempts=attempts[0])


def pending_task_shutdown():
 # Observe real pending task/async-generator cleanup through the whole command,
 # with repeated real signals from within retirement, after confirmed publication.
 for resource in ('task','async_generator'):
  with t.fixture() as (config,s,root,target,previous):
   initialized=[False];settled=[False];retained=[]
   async def completion():
    try:await asyncio.Future()
    finally:
     os.kill(os.getpid(),signal.SIGINT);await asyncio.sleep(0)
     os.kill(os.getpid(),signal.SIGINT);settled[0]=True
   async def generator():
    try:yield 1
    finally:
     os.kill(os.getpid(),signal.SIGINT);await asyncio.sleep(0)
     os.kill(os.getpid(),signal.SIGINT);settled[0]=True
   async def hook(w,r):
    if not initialized[0] and isinstance(r,functions.auth.SignInRequest):
     initialized[0]=True
     if resource=='task':retained.append(asyncio.create_task(completion()))
     else:
      value=generator();retained.append(value);assert await value.__anext__()==1
    return NotImplemented
   s.hook=hook
   status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE])
   assert status==130 and settled[0] and target.exists(),(resource,status,text)
   assert 'Saved session' in text;t.reopen(config,s);t.no_secrets(text)
   record('late_'+resource+'_retirement',exit=status,saved=True,settled=True)

if __name__=='__main__':
 manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tgdata').rglob('*.py')}
 try:
  with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
   source_crossings();storage_crossings();pending_task_shutdown()
 finally:
  assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in manifest.items())
  (HERE/'crossings-result.json').write_text(json.dumps(dict(cases=rows,source_sha256=manifest),indent=2)+'\n')
 print('FRESH_CROSSINGS',len(rows),'PASS',flush=True)
