"""Bounded planning experiment: cancel/settle a real LoginFlow without injecting KI.

This is only a phase-local viability probe, not the proposed command lifetime or
its required full prebuild. Product CLI and publisher are never patched.
"""
import asyncio,json,os,signal,socket,sys,threading,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path('/private/tmp/tgdata-50-terminal-account-login');sys.path.insert(0,str(ROOT))
from tgdata import login
from tgdata.smoke_tests import test_41_stepwise_login as fx

class Stop(Exception):pass

def drive(loop,action,*,retire=False):
 task=asyncio.ensure_future(action,loop=loop);requested=[False];queued=[False];sent=[0]
 prior=signal.getsignal(signal.SIGINT)
 def cancel():
  if not task.done():sent[0]+=1;task.cancel()
 def request(signum,frame):
  requested[0]=True
  if not retire and not queued[0]:
   queued[0]=True;loop.call_soon_threadsafe(cancel)
 signal.signal(signal.SIGINT,request)
 try:
  while not task.done():
   try:loop.run_until_complete(task)
   except (KeyboardInterrupt,asyncio.CancelledError):
    requested[0]=True
    if not retire and not task.done() and not queued[0]:queued[0]=True;loop.call_soon_threadsafe(cancel)
   except BaseException:
    if task.done():break
    raise
  try:result=task.result()
  except (KeyboardInterrupt,asyncio.CancelledError):raise Stop() from None
  if requested[0] and not retire:raise Stop()
  return result
 finally:
  signal.signal(signal.SIGINT,prior)
  assert sent[0]<=1

def one(mode):
 with fx.fixture(two_factor=mode=='srp') as (config,s):
  loop=asyncio.new_event_loop();asyncio.set_event_loop(loop);flow=login.LoginFlow(config);timers=[];active=[False];retired=[False]
  async def close(w):
   if mode=='cleanup' and 'SendCodeRequest' in s.calls:
    os.kill(os.getpid(),signal.SIGINT)
    await asyncio.sleep(0.01)
    os.kill(os.getpid(),signal.SIGINT)
   retired[0]=True
  s.close_hook=close
  try:
   try:
    if mode=='validation':
     original=login._phone
     def phone(value):os.kill(os.getpid(),signal.SIGINT);return original(value)
     with patch.object(login,'_phone',phone):drive(loop,flow.start(fx.PHONE))
    elif mode=='srp':
     drive(loop,flow.start(fx.PHONE));drive(loop,flow.submit_code(fx.CODE))
     original=login.srp.compute_check
     def compute(*args):
      running=[True]
      def stop():
       active[0]=running[0];os.kill(os.getpid(),signal.SIGINT)
      timer=threading.Timer(0.002,stop);timers.append(timer);timer.start()
      try:return original(*args)
      finally:running[0]=False
     with patch.object(login.srp,'compute_check',compute):drive(loop,flow.submit_password(fx.PASSWORD))
    elif mode=='cleanup':drive(loop,flow.start(fx.PHONE))
    elif mode=='wait':
     async def held(w,r):
      from telethon import functions
      if isinstance(r,functions.auth.SendCodeRequest):
       loop.call_later(0.002,os.kill,os.getpid(),signal.SIGINT)
       loop.call_later(0.003,os.kill,os.getpid(),signal.SIGINT)
       await asyncio.Future()
      return NotImplemented
     s.hook=held;drive(loop,flow.start(fx.PHONE))
    elif mode=='done_interrupt':
     task=loop.create_future();task.set_exception(KeyboardInterrupt())
     drive(loop,task)
    elif mode=='retirement':
     async def retiring():
      os.kill(os.getpid(),signal.SIGINT);await asyncio.sleep(0.003)
      os.kill(os.getpid(),signal.SIGINT);return 'settled'
     assert drive(loop,retiring(),retire=True)=='settled'
     return dict(case=mode,settled=True,cancelled=False)
    raise AssertionError('stop lost')
   except Stop:pass
   if flow.status.cleanup_pending:drive(loop,flow.close(),retire=True)
   assert all(not w.up for w in s.wires)
   assert not [task for task in asyncio.all_tasks(loop) if not task.done()]
   if mode=='validation':assert not s.calls
   if mode=='srp':assert active[0]
   return dict(case=mode,stopped=True,all_wires_closed=True,native_srp_signal_active=active[0],
       auth_step=flow.status.step,codes=s.calls.count('SendCodeRequest'),password_requests=s.calls.count('CheckPasswordRequest'))
  finally:
   for timer in timers:timer.join()
   loop.run_until_complete(loop.shutdown_asyncgens());loop.close();asyncio.set_event_loop(None)

if __name__=='__main__':
 rows=[]
 with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
  for mode in ('validation','srp','cleanup','wait','done_interrupt','retirement'):
   value=one(mode);rows.append(value);print(json.dumps(value),flush=True)
 Path(__file__).with_name('interrupt-probe-result.json').write_text(json.dumps(dict(result='PASS',cases=rows),indent=2)+'\n')
