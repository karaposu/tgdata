"""Real SIGINT inside an actual LoginFlow action; bounded by an outer process."""
import os
import asyncio
from pathlib import Path
import signal
import socket
import sys
from unittest.mock import patch
ROOT=Path('/private/tmp/tgdata-50-terminal-login-pr')
sys.path.insert(0,str(ROOT))
from tgdata import login
from tgdata.smoke_tests import test_48_terminal_login as t
kind=sys.argv[1]
if '--diagnostic' in sys.argv:
 original_new=asyncio.new_event_loop
 def new_loop():
  loop=original_new();run=loop.run_until_complete;repeats=[0]
  def inspect_run(task):
   if hasattr(task,'done') and task.done() and not task.cancelled():
    if isinstance(task.exception(),KeyboardInterrupt):
     repeats[0]+=1
     if repeats[0]<=3:print('DONE_TASK_KEYBOARD_INTERRUPT_REENTER '+str(repeats[0]),file=sys.__stderr__,flush=True)
   return run(task)
  loop.run_until_complete=inspect_run
  return loop
 asyncio.new_event_loop=new_loop
with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
     patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
 with t.fixture(two_factor=kind=='password') as (config,s,root,target,old):
  if kind=='phone':
   original=login._phone
   def stopped(value):
    print('SIGNAL_INSIDE_PHONE',flush=True)
    os.kill(os.getpid(),signal.SIGINT)
    return original(value)
   scope=patch.object(login,'_phone',stopped)
  else:
   original=login.srp.compute_check
   def stopped(*args):
    print('SIGNAL_INSIDE_SRP',flush=True)
    os.kill(os.getpid(),signal.SIGINT)
    return original(*args)
   scope=patch.object(login.srp,'compute_check',stopped)
  # invoke captures output; report after return only. Outer timeout proves hangs.
  with scope:
   code,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE]+([t.fx.PASSWORD] if kind=='password' else []))
  t.no_secrets(text)
  print('RESULT',kind,'exit',code,'saved',target.exists(),'codes',s.calls.count('SendCodeRequest'),flush=True)
