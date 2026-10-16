def test_review_source_and_storage_histories():
 from datetime import datetime, timezone
 from types import SimpleNamespace
 t=sys.modules[__name__]
 f=publication
 def record(name,details):print('REVIEW_HISTORY',name,json.dumps(details),flush=True)
 def unchanged(target,previous):
  assert target.read_bytes()==previous if previous is not None else not target.exists()
 # Source results and actual SRP, independent of the implementation's test list.
 for mode in ('expired','phone_reply_lost','code_retry','code_loss_twice','wrong_password','migration'):
  with t.fixture(two_factor=mode=='wrong_password') as (config,s,root,target,previous):
   seen=[0]
   def hook(w,r):
    if mode=='expired' and isinstance(r,functions.auth.SignInRequest):return errors.PhoneCodeExpiredError(r)
    if mode=='phone_reply_lost' and isinstance(r,functions.auth.SendCodeRequest):
     s.answer(w,r);return OSError(t.fx.PASSWORD)
    if mode in ('code_retry','code_loss_twice') and isinstance(r,functions.auth.SignInRequest):
     seen[0]+=1
     if seen[0]==1 or mode=='code_loss_twice':return OSError(t.fx.PASSWORD)
    if mode=='migration' and isinstance(r,functions.auth.SendCodeRequest) and w.client.session.dc_id!=3:
     return errors.PhoneMigrateError(r,capture=3)
    return NotImplemented
   s.hook=hook
   values=[t.fx.PHONE,t.fx.CODE]
   if mode=='phone_reply_lost':values=[t.fx.PHONE]
   if mode in ('code_retry','code_loss_twice'):values.append(t.fx.CODE)
   if mode=='wrong_password':values.extend(['incorrect-private-password',t.fx.PASSWORD])
   confirms=[True] if mode in ('phone_reply_lost','code_retry','code_loss_twice') else []
   status,text=t.invoke(config,values,confirms)
   expected=3 if mode in ('expired','phone_reply_lost','code_loss_twice') else 0
   assert status==expected,(mode,status,text)
   assert target.exists()==(expected==0)
   assert s.calls.count('SendCodeRequest')==(2 if mode=='migration' else 1)
   if mode=='wrong_password':assert s.calls.count('CheckPasswordRequest')==2 and s.srp_accepted==1
   if mode=='code_loss_twice':assert s.calls.count('SignInRequest')==2
   if mode=='migration':
    native=SQLiteSession(str(target));assert native.dc_id==3 and native.auth_key.key==t.fx.OTHER;native.close()
    async def reader():
     engine=ConnectionEngine(config,interactive_login=False);original=engine._new_client
     def make(*args,**kwargs):
      client=original(*args,**kwargs);client._sender=t.fx.Wire(client,s);s.clients.append(client);s.wires.append(client._sender);return client
     engine._new_client=make
     async with engine._account_operation(4242) as op:assert op.client.session.auth_key.key==t.fx.OTHER
    asyncio.run(reader())
   elif expected==0:t.reopen(config,s)
   t.no_secrets(text)
   record(mode,dict(exit=status,saved=target.exists(),codes=s.calls.count('SendCodeRequest'),signins=s.calls.count('SignInRequest')))

 # Sidecars appearing after actual native candidate preparation, including dangling links.
 for suffix in ('-wal','-shm','-journal'):
  with t.fixture(existing=True) as (config,s,root,target,previous):
   prepare=f._prepare_candidate
   def late(*args):
    prepare(*args);Path(str(target)+suffix).symlink_to(root/'absent-sidecar')
   with patch.object(f,'_prepare_candidate',late):status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],[True],replace=True)
   assert status==4 and 'sqlite_sidecar_present' in text
   unchanged(target,previous);assert Path(str(target)+suffix).is_symlink();t.no_secrets(text)
   record('late_'+suffix,dict(exit=status,old_bytes_preserved=True))

 # Real syscall effects followed by failures; no implicit retry/rollback.
 for existing in (False,True):
  for effect in (False,True):
   with t.fixture(existing=existing) as (config,s,root,target,previous):
    operation='replace' if existing else 'link';original=getattr(os,operation)
    def fault(source,dest,*args,**kwargs):
     if Path(dest)==target:
      if effect:original(source,dest,*args,**kwargs)
      raise OSError(t.fx.PASSWORD)
     return original(source,dest,*args,**kwargs)
    with patch.object(f.os,operation,fault):status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],[True] if existing else [],replace=existing)
    assert status==5 and 'publication is uncertain' in text
    recovery=list(root.glob('.tgdata-login-*'));assert len(recovery)==1
    if existing:assert (recovery[0]/'previous.session').read_bytes()==previous
    if not effect:unchanged(target,previous)
    else:
     native=SQLiteSession(str(target));assert native.auth_key.key==t.fx.KEY;native.close()
    assert s.calls.count('SendCodeRequest')==s.calls.count('SignInRequest')==1
    t.no_secrets(text)
    record(operation+('_after_effect' if effect else '_before_effect'),dict(exit=status,recovery_retained=True,effect=effect))

 # A second local attempt does not authorize a replacement of a changed target.
 with t.fixture(existing=True) as (config,s,root,target,previous):
  prepare=f._prepare_candidate;count=[0]
  def first(*args):
   count[0]+=1
   if count[0]==1:raise OSError(t.fx.PASSWORD)
   return prepare(*args)
  confirmations=[0]
  def confirm(prompt,expected='yes'):
   confirmations[0]+=1
   if confirmations[0]==2:target.write_bytes(b'new independent destination')
   return True
  with patch.object(f,'_prepare_candidate',first),patch.object(t.cli,'_confirm',confirm):
   # invoke patches confirm itself; use a local iterator with side effect instead.
   class Answers:
    def __iter__(self):return self
    def __next__(self):return confirm('')
   status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],Answers(),replace=True)
  assert status==4 and target.read_bytes()==b'new independent destination' and count[0]==1
  assert s.calls.count('SendCodeRequest')==s.calls.count('SignInRequest')==1
  record('retry_refuses_changed_target',dict(exit=status,candidate_attempts=count[0],codes=1))

 # Real native constructor opens a connection and fails; it must be retired.
 with t.fixture(existing=True) as (config,s,root,target,previous):
  original=SQLiteSession.__init__;connections=[]
  def broken(value,*args,**kwargs):
   original(value,*args,**kwargs)
   if 'candidate-' in value.filename:
    connections.append(value._conn);raise OSError(t.fx.PASSWORD)
  with patch.object(SQLiteSession,'__init__',broken):status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],[True,False],replace=True)
  assert status==4;unchanged(target,previous);assert connections
  for conn in connections:
   try:conn.execute('select 1')
   except Exception as e:assert type(e).__name__=='ProgrammingError'
   else:raise AssertionError('constructor connection remains open')
  t.no_secrets(text);record('constructor_failure_retired',dict(exit=status,connections=len(connections)))

 # LoginFlow naturally completes without own hash; add available native state at the source boundary.
 with t.fixture(no_hash=True) as (config,s,root,target,previous):
  def state(w,r):
   if isinstance(r,functions.auth.SignInRequest):
    w.client._message_box.load(SimpleNamespace(pts=123,qts=456,date=datetime(2026,10,16,1,2,3,123456,tzinfo=timezone.utc).timestamp(),seq=789),[])
    w.client.session.takeout_id=2**62+19
   return NotImplemented
  s.hook=state
  status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE]);assert status==0
  native=SQLiteSession(str(target));v=native.get_update_state(0)
  # Native disconnect exports the real message-box state into the completed credential.
  assert native.takeout_id==2**62+19 and native.get_entity_rows_by_id(4242) is None
  assert v is not None and v.pts==123 and v.date.microsecond==123456
  native.close();t.reopen(config,s);t.no_secrets(text)
  record('available_state_and_optional_hash',dict(exit=status,fractional_date=True,takeout_exact=True))

 # Failed retirement after known authorization blocks publication even on repeated failures.
 with t.fixture(existing=True) as (config,s,root,target,previous):
  async def bad_close(w):
   if 'SignInRequest' in s.calls:raise OSError(t.fx.PASSWORD)
  s.close_hook=bad_close
  try:
   status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],replace=True)
   assert status==3;unchanged(target,previous);assert s.calls.count('SignInRequest')==1
   t.no_secrets(text);record('unsettled_auth_not_published',dict(exit=status,old_bytes_preserved=True,signins=1))
  finally:
   s.close_hook=None
   async def cleanup():
    for wire in s.wires:
     if wire.up:await wire.disconnect()
   asyncio.run(cleanup())
