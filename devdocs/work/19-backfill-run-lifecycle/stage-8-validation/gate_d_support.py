"""Gate D's bounded, operation-attributed source and actual local receiver primitives."""
import asyncio
import contextvars
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
sys.path.insert(0,str(REPO))


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return value


p=module('gate_d_original_guard',HERE.parent/'live_probe.py')
app=module('gate_d_application_receiver',REPO/'examples/backfill_runs.py')
from telethon import functions,errors
from tgdata import TgData,ReadBudget,MessageBatch,BackfillDeliveryRef,health
from tgdata.history_window import _encode_date

ROOT=Path('/private/tmp/tgdata19-gate-d-live-20261007')
OLD=Path('/private/tmp/tgdata19-gate-a-live-20261007')
CONFIG=Path('/Users/ns/Desktop/projects/telegram-group-scraper/config.ini')
BUDGET=OLD/'account-read-budget.sqlite3'
SMALL=-1004478311025
LARGE=-1001139574198
DESTINATION='gate-d-receiver'
STAGE_CAP=1500
OP=contextvars.ContextVar('gate_d_operation',default='outside-public-call')


def stamp():return dict(utc=_encode_date(datetime.now(timezone.utc)),monotonic_ns=time.monotonic_ns())
def read(path):return json.loads(Path(path).read_text())
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def account():return int(read(OLD/'login-status.json')['verified_account_id'])
def revision():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()


def save(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def append(path,value):
    with Path(path).open('a') as stream:
        stream.write(canonical(value)+'\n');stream.flush();os.fsync(stream.fileno())


def allocate(root,name,slots):
    """Single sequential owner; failed/uncertain launches never regain their cap."""
    root=Path(root);root.mkdir(mode=0o700,exist_ok=True)
    assert root.stat().st_mode & 0o077==0
    assert type(slots) is int and 0<slots<=STAGE_CAP
    path=root/'allocations.jsonl'
    prior=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    assert name not in [r['name'] for r in prior], 'launch allocation already exists'
    assert sum(r['slots'] for r in prior)+slots<=STAGE_CAP, 'stage ceiling exhausted'
    append(path,dict(name=name,slots=slots,created=stamp()))
    fd=os.open(str(root),os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def begin(root,name):
    rows=[json.loads(line) for line in (root/'allocations.jsonl').read_text().splitlines()]
    row=next(r for r in rows if r['name']==name)
    save(root/(name+'.started.json'),dict(pid=os.getpid(),allocation=row,started=stamp()))
    return row['slots']


class Guard(p.ReadOnlyGuard):
    def __init__(self,root,name,chat,slots,media=False):
        super().__init__(chat,dict(max_rpc_requests=220,max_history_requests=24,
            max_requested_slots=slots,max_media_bytes=4*1024*1024 if media else 0),media)
        self.path=root/(name+'.sends.jsonl');self.blocked=[];self.block_after=None

    def before_send(self,request):
        raw=request
        for _ in range(9):
            if not isinstance(raw,p._WRAPPERS):break
            raw=raw.query
        if isinstance(raw,functions.messages.GetHistoryRequest):
            amount=p.number(raw.limit,'history bound',1,10000)
            p.require(p.peer_id(raw.peer)==self.chat_id,'wrong_history_group')
            p.require(self.slots+sum(r['limit'] for r in self.blocked)+amount<=self.limits['max_requested_slots'],
                      'allocated_slot_cap_reached')
            if self.block_after is not None and self.history_count>=self.block_after:
                entry=dict(kind=type(raw).__name__,limit=amount,operation=OP.get(),
                    observed=stamp(),outcome='INJECTED local refusal before underlying sender')
                self.blocked.append(entry);append(self.path,entry)
                raise p.ProbeStop('injected_local_send_refusal')
        entry=super().before_send(request);entry['operation']=OP.get();append(self.path,entry)
        return entry

    def report(self):
        return dict(rpc=self.rpc,blocked=self.blocked,history_requests=self.history_count,
            sent_requested_slots=self.slots,attempted_slots=self.slots+sum(r['limit'] for r in self.blocked),
            requested_media_bytes=self.media_bytes)


async def operation(report,label,awaitable,guard=None):
    before=stamp();token=OP.set(label);event=dict(operation=label,entry=before)
    if guard:event['rpc_before']=len(guard.rpc)
    report.setdefault('operations',[]).append(event)
    try:
        result=await awaitable;event['outcome']=type(result).__name__;return result
    except BaseException as error:
        event['outcome']=type(error).__name__;raise
    finally:
        event['end']=stamp()
        if guard:event['rpc_after']=len(guard.rpc)
        OP.reset(token)


async def source(root,name,chat,*,backfill_store=None,sync_store=None,media=False,events=None):
    assert p.telethon.__version__=='1.45.0' and BUDGET.is_file()
    slots=begin(root,name);ident=account();budget=ReadBudget(BUDGET)
    status=budget.status(ident)
    assert status.limit==5000 and status.remaining>=slots, 'authoritative capacity unavailable'
    guard=Guard(root,name,chat,slots,media)
    tg=TgData(str(CONFIG),connection_pool_size=1,interactive_login=False,read_budget=budget,
        backfill_store=backfill_store,sync_store=sync_store,
        health_callback=events.append if events is not None else None)
    factory=tg.connection_engine._new_client
    def instrumented(*a,**kw):
        client=factory(*a,**kw);guard.instrument(client)
        client.flood_sleep_threshold=0;client._request_retries=0;client._connection_retries=1
        return client
    tg.connection_engine._new_client=instrumented
    token=OP.set('connect-and-verify-selected-account')
    try:
        client=await tg.connection_engine.get_client()
        me=await client.get_me(input_peer=False)
        assert me is not None and me.id==ident, 'selected authenticated identity changed'
        assert client._self_id==ident, 'cached identity differs; do not repair it in this gate'
        return tg,client,guard,budget,status
    except BaseException:
        await tg.close();raise
    finally:OP.reset(token)


async def seed_health(tg,chat,events):
    """INJECTED prior group-health fixture, explicitly not a Telegram observation."""
    async with tg._health.call('gate-d-injected-prior-denial',group=chat):
        await health.report(errors.ChannelPrivateError(request=None),'INJECTED-local-fixture')
    assert str(chat) in tg._health.snapshot()['no_access']
    return len(events),tg._health.snapshot()


class Receiver:
    """Actual file custody before one full snapshot/receipt/message transaction."""
    def __init__(self,root,*,create=False):
        self.root=Path(root)
        if create:self.root.mkdir(mode=0o700,exist_ok=False)
        self.media=self.root/'media'
        if create:self.media.mkdir()
        assert self.root.is_dir() and self.media.is_dir()
        self.db=app.ApplicationDatabase(self.root/'receiver.sqlite3',create=create)

    def _bytes(self,batch,source):
        for record in batch.messages:
            blob=record['media']['blob'] if record['media'] is not None else None
            if blob is None:continue
            assert source is not None
            data=(Path(source)/blob['path']).read_bytes()
            assert len(data)==blob['size'] and hashlib.sha256(data).hexdigest()==blob['sha256']
            target=self.media/blob['path']
            assert target.parent.resolve()==self.media.resolve() and not target.is_symlink()
            if not target.exists():
                with target.open('xb') as stream:
                    stream.write(data);stream.flush();os.fsync(stream.fileno())
            assert target.stat().st_size==blob['size'] and digest(target)==blob['sha256']
        fd=os.open(str(self.media),os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)

    def _accept(self,key,batch,source):
        self._bytes(batch,source)
        data=batch.to_json()
        with self.db.transaction(write=True) as db:
            old=db.execute('SELECT batch FROM example_receipts WHERE receipt=?',(key,)).fetchone()
            assert old is None or old[0]==data, 'duplicate receipt changed observation'
            if old is None:
                db.execute('INSERT INTO example_receipts VALUES (?, ?)',(key,data))
                for row in batch.messages:
                    db.execute('INSERT OR IGNORE INTO example_messages VALUES (?, ?, ?)',
                        (str(batch.chat_id),row['id'],canonical(row)))
        return old is None

    def accept(self,batch,delivery,source=None):
        assert isinstance(batch,MessageBatch) and isinstance(delivery,BackfillDeliveryRef)
        assert delivery.destination_id==DESTINATION and delivery.run.chat_id==batch.chat_id
        assert delivery.batch_id==batch.batch_id
        return self._accept(app.Receiver.backfill_key(delivery),batch,source)

    def daily(self,namespace,batch):
        assert batch.media_mode=='references' and type(namespace) is str and namespace
        return self._accept(canonical(dict(kind='daily',namespace=namespace,
            chat_id=str(batch.chat_id),batch_id=batch.batch_id)),batch,None)

    def summary(self):return app.Receiver(self.db,DESTINATION).summary()
    def observation(self,delivery):return app.Receiver(self.db,DESTINATION).observation(delivery)


def safe_error(error):
    import traceback
    return dict(error_type=type(error).__name__,frames=[dict(file=Path(f.filename).name,line=f.lineno,
        function=f.name) for f in traceback.extract_tb(error.__traceback__)])
