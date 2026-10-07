import asyncio,logging,socket,tempfile,types as pytypes,json
from pathlib import Path
from unittest.mock import patch
from telethon import errors
from tgdata import ReadBudgetConfigError
from tgdata.smoke_tests import test_18_read_budget as f

async def run():
 with tempfile.TemporaryDirectory(prefix='tgdata17-plan-critic-') as directory:
  f.TMP=Path(directory)
  budget,_=f.ledger(account=111);budget.configure(222,100)
  class Bound:
   def status(self,account):
    if account!=111:raise ReadBudgetConfigError('identity mismatch')
    return budget.status(account)
   def _reserve(self,account,amount):
    self.status(account);return budget._reserve(account,amount)
   def _settle(self,*args):return budget._settle(*args)
  tg,client,sender=f.instance(Bound(),account=222,cached=111)
  await f.expect(ReadBudgetConfigError,tg.get_message_batch(-1000000000007,limit=1))
  assert not sender.reads and budget.status(111).used==budget.status(222).used==0
  print(json.dumps(dict(probe='bound_real_budget_admission',source_reads=0,wrong_owner_refused=True)))
  # Actual reader and HealthMonitor; only the proposed cancellation tuple is extended.
  source=Path('tgdata/batch_engine.py').read_text();source='import asyncio\n'+source.replace('except Exception as error:', 'except (Exception, asyncio.CancelledError) as error:')
  module=pytypes.ModuleType('tgdata._critic_probe');module.__package__='tgdata';exec(compile(source,'<batch cancellation seam>','exec'),module.__dict__)
  async def blocked_callback(event):await asyncio.Event().wait()
  for retained in (False,True):
   tg,c,s=f.instance();tg._health.callback=blocked_callback
   # HealthMonitor stores callback on .callback (assert source attribute below).
   tg._health=f.health.HealthMonitor(blocked_callback,None,tg._health_identity)
   s.script=[f.response([f.message(n) for n in reversed(range(101,201))]),errors.FloodWaitError(request=None,capture=7200)]
   c.flood_sleep_threshold=0;c._request_retries=0;c._raise_last_call_error=True
   body=module.BatchEngine(tg.connection_engine);outcome={}
   async def observed():
    async with tg._health.call('pool-probe',group=-1000000000007):
     try:
      result=await body.fetch_batch(-1000000000007,after_id=100,limit=200)
     except BaseException as error:
      outcome['error']=error;outcome['finished']=True;raise
     else:outcome['batch']=result;outcome['finished']=True;return result
   try:await asyncio.wait_for(observed(),0.03)
   except asyncio.TimeoutError as error:
    primary=outcome['error'] if retained and outcome.get('finished') else error
    count=len(getattr(primary,'partial_result',None).messages) if getattr(primary,'partial_result',None) else 0
    print(json.dumps(dict(probe='timeout_during_health_callback',retain_outcome=retained,error=type(primary).__name__,prefix=count,wait=getattr(primary,'seconds',None))))
    if retained:assert isinstance(primary,errors.FloodWaitError) and count==100 and primary.seconds==7200
    else:assert count==0
  for client in f.CLIENTS:client.session.close()
logging.disable(logging.CRITICAL)
with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')):asyncio.run(run())
