"""Fresh round2 review histories. Run with the product checkout as argv[1].

Actual SDK-derived values, SQLite and existing source engines; no Telegram I/O.
Faults cause failures/observe paths; no substitute supplies receiver success.
"""
import asyncio
from contextlib import contextmanager
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import random
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
from unittest.mock import patch

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT))
from tgdata.smoke_tests.test_42_album_assembly import record, batch, assemble, CHAT, GROUP, NOW
from tgdata import MessageBatch, SQLiteSyncStore
from tgdata.album import album_post_ids, AlbumAssemblyError
from tgdata.sync_engine import SyncEngine
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill import BackfillStartRequest, BackfillPrepareContext
import examples.album_assembly as module
from examples.album_assembly import AlbumReceiver, ReceiverError, collect


def refusal(kind, fn):
    try:
        fn()
    except kind:
        return
    raise AssertionError('expected {}'.format(kind.__name__))


def rows(receiver):
    with sqlite3.connect(str(receiver.path)) as db:
        return (db.execute('SELECT * FROM album_members ORDER BY collection,chat_id,message_id').fetchall(),
                db.execute('SELECT * FROM album_receipts ORDER BY collection,batch_id').fetchall())


def confirm(receiver, raw):
    original = receiver._open
    @contextmanager
    def guarded():
        with original() as db:
            db.set_authorizer(lambda op, *args: sqlite3.SQLITE_DENY if op in
                              (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE)
                              else sqlite3.SQLITE_OK)
            yield db
            assert db.total_changes == 0
    with patch.object(receiver, '_open', side_effect=guarded), \
         patch.object(receiver, '_load', side_effect=AssertionError('view read')), \
         patch.object(receiver, '_stats', side_effect=AssertionError('post stats')), \
         patch.object(module, 'assemble_albums', side_effect=AssertionError('assembly')):
        assert receiver.accept(raw) is None


def mixed_histories(root):
    accepts = confirms = 0
    for seed in range(18):
        rng = random.Random(seed)
        database = root/('mixed-{}.db'.format(seed))
        expected = {}
        receivers = [AlbumReceiver(database, name, create=True) for name in ('a', 'A')]
        jobs = []
        for dest, receiver in enumerate(receivers):
            for chat in (CHAT, CHAT-1):
                records = [record(i, 'caption-{}-{}-{}🙂'.format(dest, chat, i),
                                  grouped=None if i % 4 == 0 else GROUP + i % 3)
                           for i in range(1, 13)]
                for post in assemble(batch(*records, chat=chat)):
                    expected[(dest,post.post_id)] = post.to_json()
                shuffled = records[:]; rng.shuffle(shuffled)
                parts = [shuffled[n:n+2] for n in range(0,12,2)]
                # A differently partitioned overlap is new admission, not replay.
                parts += [rng.sample(records, 3), rng.sample(records, 4)]
                jobs.extend((dest,batch(*part,chat=chat)) for part in parts)
        rng.shuffle(jobs)
        for dest, raw in jobs:
            before = raw.to_json()
            receivers[dest].accept(raw); accepts += 1
            assert raw.to_json() == before
        rng.shuffle(jobs)
        for dest, raw in jobs:
            confirm(AlbumReceiver(database, receivers[dest].collection), raw); confirms += 1
        for (dest,key), expected_wire in expected.items():
            assert receivers[dest].load(key).to_json() == expected_wire
        stored, markers = rows(receivers[0])
        assert len(stored) == 48
        assert len(markers) == len({(dest,raw.batch_id) for dest,raw in jobs})
    return dict(seeds=18, accept_calls=accepts, zero_write_confirmations=confirms,
                distinct_members_per_database=48, oracle='one-shot core plus independent row/marker counts')


def new_hash_boundary(root):
    raw = batch(record(1,'🙂'*500)); post, = assemble(raw)
    cap = len(raw.to_json().encode()) + len(post.to_json().encode())
    receiver = AlbumReceiver(root/'boundary.db','one',create=True,max_bytes=cap,max_members=1)
    receiver.accept(raw); before = rows(receiver)
    other = batch(*raw.messages,stop='end')
    assert other.batch_id != raw.batch_id and other.messages == raw.messages
    refusal(AlbumAssemblyError, lambda: receiver.accept(other))
    assert rows(receiver) == before
    confirm(AlbumReceiver(receiver.path,'one',max_bytes=cap,max_members=1),raw)
    return dict(cap=cap,new_hash_refused=True,original_confirmed=True,markers=1)


def namespace_matrix(root):
    names = ['Tenant','tenant','é','e\u0301','x','x\x00tail']
    raw = batch(record(1,'common')); key = album_post_ids(raw)[0]
    receivers = [AlbumReceiver(root/'names.db',name,create=True) for name in names]
    for index, receiver in enumerate(receivers):
        assert receiver.load(key) is None
        receiver.accept(raw)
        receiver.accept(batch(record(2,'private-'+str(index)),after=1))
    for index, receiver in enumerate(receivers):
        confirm(receiver,raw)
        assert receiver.load(key).members[1]['text'] == 'private-'+str(index)
    stored, markers = rows(receivers[0])
    assert len(stored) == len(markers) == 12
    return dict(collections=len(names),members=12,markers=12,normalization_or_prefix_alias=False)


def confirmation_scope(root):
    receiver = AlbumReceiver(root/'scope.db','one',create=True)
    first, later = batch(record(1)), batch(record(2),after=1)
    receiver.accept(first); receiver.accept(later)
    with sqlite3.connect(str(receiver.path)) as db:
        db.execute('UPDATE album_members SET record_sha256=? WHERE message_id=2',('0'*64,))
    before = rows(receiver)
    confirm(receiver,first)
    refusal(ReceiverError,lambda: confirm(receiver,later))
    refusal(ReceiverError,lambda: receiver.load(album_post_ids(first)[0]))
    assert rows(receiver) == before
    return dict(original_confirmation=True,changed_original_refused=True,grown_view_refused=True,no_repair=True)


def commit_response_lost(root):
    async def run():
        raw=batch(record(1,'saved'),after=0,stop='end'); reads=[]
        async def read(*args,**kwargs): reads.append(kwargs); return raw
        store=SQLiteSyncStore(root/'source.db'); engine=SyncEngine(read,store)
        await engine.initialize(CHAT,after_id=0)
        owed=await engine.prepare(CHAT,limit=1)
        receiver=AlbumReceiver(root/'lost.db','one',create=True)
        real_connect=sqlite3.connect
        class LostReply(sqlite3.Connection):
            def commit(self):
                super().commit()
                if self.total_changes: raise OSError('receiver commit succeeded; response lost')
        def connect(*args,**kwargs): return real_connect(*args,factory=LostReply,**kwargs)
        with patch.object(module.sqlite3,'connect',side_effect=connect):
            refusal(OSError,lambda:receiver.accept(owed))
        state=await engine.status(CHAT)
        assert state.after_id==0 and state.pending_batch_id==raw.batch_id
        restarted=SyncEngine(read,SQLiteSyncStore(store.path,create=False))
        replay=await restarted.prepare(CHAT,limit=1)
        assert replay.to_json()==raw.to_json()
        confirm(AlbumReceiver(receiver.path,'one'),replay)
        await restarted.acknowledge(CHAT,replay.batch_id)
        assert (await restarted.status(CHAT)).after_id==1 and len(reads)==1
        return dict(source_reads=1,receiver_members=1,receiver_markers=1,settled_after_restart=1)
    return asyncio.run(run())


def equal_content_two_sources(root):
    async def run():
        raw=batch(record(1,'shared'),record(2),after=0,stop='end'); calls=[]
        async def read(*args,**kwargs): calls.append(kwargs); return raw
        daily=SyncEngine(read,SQLiteSyncStore(root/'daily.db')); await daily.initialize(CHAT,after_id=0)
        history=BackfillEngine(SQLiteSyncStore(root/'history.db'),'jobs',read_batch=read,
                               clock=lambda:NOW+timedelta(hours=2))
        request=BackfillStartRequest(collection_id='jobs',chat_id=CHAT,run_id='history',destination_id='one',
                   origin='fresh',after_id=0,expected_predecessor=None,start_date=NOW-timedelta(hours=1),
                   end_date=NOW+timedelta(hours=1),batch_size=2,pause_seconds=0)
        status=(await history.start(request,submission='new')).status
        one=await daily.prepare(CHAT,limit=2)
        two=await history.prepare(BackfillPrepareContext.from_status(status))
        assert one.batch_id==two.batch.batch_id
        receiver=AlbumReceiver(root/'shared.db','one',create=True); receiver.accept(one)
        await daily.acknowledge(CHAT,one.batch_id)
        assert (await history.status(CHAT)).after_id==0
        confirm(receiver,two.batch)
        done=await history.acknowledge(two.delivery)
        assert done.after_id==2 and done.terminal_outcome=='completed'
        stored,markers=rows(receiver); assert len(stored)==2 and len(markers)==1
        return dict(source_reads=len(calls),independent_original_receipts=2,members=2,receiver_markers=1)
    return asyncio.run(run())


def actual_busy_commit(root):
    receiver=AlbumReceiver(root/'busy.db','one',create=True)
    first,second=batch(record(1)),batch(record(2),after=1)
    receiver.accept(first); before=rows(receiver)
    reader=sqlite3.connect(str(receiver.path),isolation_level=None)
    try:
        reader.execute('BEGIN'); reader.execute('SELECT * FROM album_members').fetchall()
        refusal(sqlite3.OperationalError,lambda:receiver.accept(second))
        assert rows(receiver)==before
    finally:
        reader.rollback();reader.close()
    receiver.accept(second);confirm(receiver,second)
    assert receiver.load(album_post_ids(first)[0]).member_ids==(1,2)
    return dict(real_commit_contention=True,partial_data_or_marker=False,retry_succeeds=True)


def snapshot_integrity(root):
    receiver=AlbumReceiver(root/'snapshot.db','one',create=True);raw=batch(record(1))
    receiver.accept(raw);key=album_post_ids(raw)[0]
    with sqlite3.connect(str(receiver.path)) as db: db.execute('PRAGMA journal_mode=WAL')
    original=receiver._read_members
    def mutate(db,key):
        with sqlite3.connect(str(receiver.path)) as writer:
            writer.execute('UPDATE album_members SET record=?',('BROKEN',))
        return original(db,key)
    with patch.object(receiver,'_read_members',side_effect=mutate):
        post=receiver.load(key)
    assert post.member_ids==(1,)
    refusal(ReceiverError,lambda:receiver.load(key))
    refusal(ReceiverError,lambda:confirm(receiver,raw))
    return dict(first_view_snapshot='valid',next_view='refused',next_confirmation='refused')


def child_accept(database,wire,gate):
    receiver=AlbumReceiver(database,'one');raw=MessageBatch.from_json(Path(wire).read_text())
    start=time.monotonic()
    while not Path(gate).exists():
        assert time.monotonic()-start<10;time.sleep(.005)
    original=receiver._open; changes=[]
    @contextmanager
    def observed():
        with original() as db:
            yield db
            changes.append(db.total_changes)
    with patch.object(receiver,'_open',side_effect=observed):
        for _ in range(1000):
            try: receiver.accept(raw); break
            except sqlite3.OperationalError as error:
                assert 'locked' in str(error);time.sleep(.005)
        else: raise AssertionError('writer never settled')
    print(json.dumps(dict(changes=changes)))


def process_competition(root):
    receiver=AlbumReceiver(root/'race.db','one',create=True)
    raw=batch(*(record(i,'caption' if i==1 else '') for i in range(1,51)))
    wire=root/'raw.json';wire.write_text(raw.to_json());gate=root/'go'
    children=[subprocess.Popen([sys.executable,__file__,str(ROOT),'--child',str(receiver.path),str(wire),str(gate)],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(3)]
    gate.touch()
    results=[]
    try:
        for child in children:
            out,err=child.communicate(timeout=20)
            assert child.returncode==0,(child.returncode,err)
            results.append(json.loads(out))
    finally:
        for child in children:
            if child.poll() is None: child.kill();child.wait()
    changes=sorted(sum(item['changes']) for item in results)
    assert changes==[0,0,51],changes
    stored,markers=rows(receiver);assert len(stored)==50 and len(markers)==1
    confirm(receiver,raw)
    return dict(processes=3,actual_changes=changes,members=50,markers=1)


def mixed_conflict_rollback(root):
    receiver=AlbumReceiver(root/'conflict.db','one',create=True)
    raw=batch(record(1,'stable'),record(2,'other',grouped=None))
    receiver.accept(raw);before=rows(receiver)
    changed=batch(record(1,'changed'),record(3,'new',grouped=GROUP+1))
    refusal(ReceiverError,lambda:receiver.accept(changed))
    assert rows(receiver)==before
    absent=album_post_ids(batch(record(3,grouped=GROUP+1)))[0]
    assert receiver.load(absent) is None
    confirm(receiver,raw)
    return dict(conflict_refused=True,new_member_absent=True,marker_count=1)


def exact_query_plans(root):
    receiver=AlbumReceiver(root/'index.db','one',create=True)
    raw=batch(record(1));receiver.accept(raw);key=album_post_ids(raw)[0]
    queries=[('SELECT record FROM album_members WHERE collection COLLATE BINARY=? AND chat_id=? AND message_id=?',
              ('one',CHAT,1)),
             ('SELECT record FROM album_members WHERE collection COLLATE BINARY=? AND post_id COLLATE BINARY=? ORDER BY message_id',
              ('one',key)),
             ('SELECT 1 FROM album_receipts WHERE collection COLLATE BINARY=? AND batch_id COLLATE BINARY=?',
              ('one',raw.batch_id))]
    with sqlite3.connect(str(receiver.path)) as db:
        plans=[db.execute('EXPLAIN QUERY PLAN '+query,args).fetchall() for query,args in queries]
    assert all(any('SEARCH' in row[-1] for row in plan) and all('SCAN ' not in row[-1] for row in plan) for plan in plans)
    return dict(plans=plans)


def cancellation_after_commit(root):
    async def run():
        raw=batch(record(1),after=0);calls=[]
        async def read(*args,**kwargs):calls.append(kwargs);return raw
        source=SyncEngine(read,SQLiteSyncStore(root/'cancel-source.db'));await source.initialize(CHAT,after_id=0)
        receiver=AlbumReceiver(root/'cancel.db','one',create=True)
        original=receiver.accept
        def accept_then_cancel(value):
            original(value);asyncio.current_task().cancel()
        class Facade:
            async def sync_group(self,chat,**kwargs):return await source.prepare(chat,**kwargs)
            async def acknowledge_sync(self,chat,ident):
                await asyncio.sleep(0) # the consumer can be cancelled before its ack request
                return await source.acknowledge(chat,ident)
        with patch.object(receiver,'accept',side_effect=accept_then_cancel):
            task=asyncio.create_task(collect(Facade(),CHAT,receiver,max_batches=1,batch_size=1))
            try:await task
            except asyncio.CancelledError:pass
            else:raise AssertionError('cancellation was swallowed')
        state=await source.status(CHAT)
        assert state.after_id==0 and state.pending_batch_id==raw.batch_id
        replay=await source.prepare(CHAT,limit=1);confirm(receiver,replay)
        await source.acknowledge(CHAT,replay.batch_id)
        assert len(calls)==1 and (await source.status(CHAT)).after_id==1
        return dict(cancellation_preserved=True,data_retained=True,source_reads=1,recovery_cursor=1)
    return asyncio.run(run())


def main():
    if len(sys.argv)>2 and sys.argv[2]=='--child':
        child_accept(*sys.argv[3:]);return
    probes=[mixed_histories,new_hash_boundary,namespace_matrix,confirmation_scope,commit_response_lost,
            equal_content_two_sources,actual_busy_commit,snapshot_integrity,process_competition,
            mixed_conflict_rollback,exact_query_plans,cancellation_after_commit]
    output=dict(product_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                python=sys.version.split()[0],histories=[],no_live_telegram=True)
    manifest=Path(__file__).with_name('merge-parity-r2.json')
    expected=json.loads(manifest.read_text())['source_sha256']
    assert all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==digest for f,digest in expected.items())
    with tempfile.TemporaryDirectory(prefix='tgdata29-review2-') as directory, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        for probe in probes:
            root=Path(directory)/probe.__name__;root.mkdir();start=time.monotonic()
            try:
                result=probe(root);entry=dict(name=probe.__name__,result='PASS',detail=result)
            except BaseException:
                entry=dict(name=probe.__name__,result='FAIL',error=traceback.format_exc())
            entry['seconds']=round(time.monotonic()-start,3);output['histories'].append(entry)
            print(json.dumps(entry,ensure_ascii=True),flush=True)
    assert all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==digest for f,digest in expected.items())
    output.update(result='PASS' if all(x['result']=='PASS' for x in output['histories']) else 'FAIL',
                  unchanged_sources=len(expected))
    Path(__file__).with_suffix('.json').write_text(json.dumps(output,indent=2)+'\n')
    raise SystemExit(0 if output['result']=='PASS' else 1)


if __name__=='__main__':main()
