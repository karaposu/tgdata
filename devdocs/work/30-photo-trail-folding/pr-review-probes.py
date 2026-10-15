"""Fresh PR36 review: actual product checkout, independent expected histories.

The existing suite's SDK fixture constructors supply valid observations only;
no product inference/selection implementation is copied as an expected oracle.
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
from unittest.mock import patch

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(ROOT))
from tgdata import PhotoTrailPolicy, PhotoTrailView, PhotoTrailError, fold_photo_trails, SQLiteSyncStore
from tgdata.sync_engine import SyncEngine
from tgdata.backfill_engine import BackfillEngine
from tgdata.backfill import BackfillStartRequest, BackfillPrepareContext
from tgdata.smoke_tests.test_43_photo_trails import record, batch, posts, member_groups, resign, stored, CHAT, GROUP, NOW, ON
from examples.album_assembly import AlbumReceiver, ReceiverError
import examples.album_assembly as receiver_module
from examples.photo_trails import load_photo_trails

RESULTS=[]

def run(name, fn):
    before=time.monotonic()
    try:
        details=fn()
    except BaseException as exc:
        RESULTS.append(dict(name=name,status='FAIL',error=type(exc).__name__,message=str(exc)))
        write()
        raise
    RESULTS.append(dict(name=name,status='PASS',seconds=round(time.monotonic()-before,4),details=details))
    print(name+': PASS',flush=True)

def write():
    OUT.write_text(json.dumps(dict(
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        root=str(ROOT),results=RESULTS,passed=sum(x['status']=='PASS' for x in RESULTS),
        product_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                        ('tgdata/photo_trails.py','examples/photo_trails.py','tgdata/smoke_tests/test_43_photo_trails.py')}
    ),indent=2)+'\n')

def expect(rows, expected, *, policy=ON):
    original=posts(*rows)
    before=tuple(x.to_json() for x in original)
    value=fold_photo_trails(original,policy=policy)
    assert member_groups(value)==expected, (member_groups(value),expected)
    assert tuple(x.to_json() for x in original)==before
    assert PhotoTrailView.from_json(value.to_json())==value
    assert fold_photo_trails(tuple(reversed(original)),policy=policy)==value
    return {'groups':expected,'counts':[value.folded_posts,value.folded_photos]}

def interleaved():
    return expect([record(1,'A'),record(2,'B',sender=99),record(3,group=GROUP,reply=1),
                   record(4,sender=99,reply=2),record(5,group=GROUP,reply=3),record(6,reply=5)],
                  ((1,3,5,6),(2,4)))

def interrupted_follower():
    return expect([record(1,'A'),record(2,group=GROUP),record(3,sender=None),
                   record(4,group=GROUP),record(5,reply=2)],((1,),(2,4,5),(3,)))

def other_unsafe():
    service=record(3,sender=99);service.update(kind='service',text=None,service_action='MessageActionChatEditTitle',date=None)
    return expect([record(1,'A'),record(2,group=GROUP),service,record(4,group=GROUP),record(5)],
                  ((1,2,4,5),(3,)))

def overlap_cluster():
    return expect([record(1,'one',group=GROUP),record(2,'other',sender=99),
                   record(3,'two',group=GROUP+1),record(4,group=GROUP),record(5,sender=99),
                   record(6,group=GROUP+1),record(7),record(8,'fresh'),record(9)],
                  ((1,4),(2,5),(3,6),(7,),(8,9)))

def mixed_late_barrier():
    return expect([record(1,sender=99,group=GROUP),record(2,'A'),record(3),record(4,group=GROUP),
                   record(5),record(6,'fresh'),record(7)],((1,4),(2,3),(5,),(6,7)))

def foreign_reply_ends():
    return expect([record(1,'A'),record(2),record(3,'B',sender=99),record(4,group=GROUP,reply=3),
                   record(5,group=GROUP),record(6,reply=4)],((1,2),(3,),(4,5,6)))

def atomic_cap():
    return expect([record(1,'A'),record(2),record(3,group=GROUP),record(4,group=GROUP),record(5),record(6)],
                  ((1,2),(3,4,5,6)),policy=PhotoTrailPolicy(enabled=True,max_photos=2))

def midnight_and_large_span():
    rows=[record(1,'A'),record(2)]
    rows[0]['date']='9999-12-31T23:59:29.999999Z';rows[1]['date']='9999-12-31T23:59:59.999999Z'
    exact=expect(rows,((1,2),))
    rows[0]['date']='0001-01-01T00:00:00.000000Z'
    far=expect(rows,((1,),(2,)),policy=PhotoTrailPolicy(enabled=True,gap_seconds=2147483647,max_span_seconds=2147483647))
    return {'exact':exact,'far':far}

def chat_independence():
    a=posts(record(1,'A',seconds=100),record(2,seconds=101))
    b=posts(record(1,'B',seconds=0),record(2,seconds=1),chat=CHAT-1)
    together=fold_photo_trails(a+b,policy=ON)
    singles=[fold_photo_trails(x,policy=ON) for x in (b,a)]
    assert together.groups==sum((x.groups for x in singles),())
    return {'groups':together.groups,'folded_photos':together.folded_photos}

def late_evidence(kind):
    with tempfile.TemporaryDirectory() as temp:
        receiver=AlbumReceiver(Path(temp)/'db','one',create=True)
        initial=batch(record(10,'A'),record(12,group=GROUP),record(14,group=GROUP),record(16))
        receiver.accept(initial)
        old=load_photo_trails(receiver,CHAT,after_id=0,through_id=16,policy=ON);wire=old.to_json()
        assert member_groups(old)==((10,12,14,16),)
        if kind=='unknown':
            receiver.accept(batch(record(13,sender=None)))
            expected=((10,),(12,14,16),(13,))
        else:
            receiver.accept(batch(record(8,group=GROUP)))
            expected=((8,12,14),(10,),(16,))
        current=load_photo_trails(receiver,CHAT,after_id=0,through_id=16,policy=ON)
        assert member_groups(current)==expected,(member_groups(current),expected)
        receiver.accept(initial)
        assert old.to_json()==wire
        assert len(stored(receiver)[0])==5
        return {'old':member_groups(old),'new':member_groups(current),'original_replay':'confirmed'}

def future_reply_never_becomes_earlier():
    return expect([record(1,'A'),record(2,reply=4),record(3),record(4)],((1,),(2,),(3,),(4,)))

def disabled_invalid_original():
    original=posts(record(1,'A'))+posts(record(1,'A',group=GROUP))
    try:fold_photo_trails(original)
    except PhotoTrailError:return {'refusal':'identity collision even when disabled'}
    raise AssertionError('disabled policy allowed conflicting original identity')

def saved_policy_and_nested_mutations():
    original=posts(record(1,'A'),record(2),record(3))
    good=fold_photo_trails(original,policy=ON)
    changes=[lambda d:d.update(groups=[]),lambda d:d['groups'][0]['post_ids'].reverse(),
             lambda d:d['groups'].append(d['groups'][0]),lambda d:d['groups'][0].update(anchor_post_id=d['groups'][0]['post_ids'][-1]),
             lambda d:d.update(folded_photos=2.0),lambda d:d.update(folded_posts=False),
             lambda d:d['policy'].update(enabled=False),lambda d:d['policy'].update(max_photos=1),
             lambda d:d['posts'][0].update(version=True),lambda d:d['posts'][0].update(membership='complete')]
    for change in changes:
        doc=good.to_dict();change(doc);resign(doc)
        try:PhotoTrailView.from_json(json.dumps(doc))
        except PhotoTrailError:pass
        else:raise AssertionError('rehashed invalid view accepted')
    fresh=fold_photo_trails(original,policy=PhotoTrailPolicy(enabled=True,max_photos=1))
    assert member_groups(fresh)==((1,2),(3,)) and fresh.revision!=good.revision
    return {'rehashed_refusals':len(changes),'fresh_policy_groups':member_groups(fresh)}

def random_observation_properties():
    rng=random.Random(30_36);histories=128
    for trial in range(histories):
        rows=[]
        for ident in range(1,13):
            sender=rng.choice([88,99,None,-7]);group=rng.choice([None,None,GROUP,GROUP+1])
            row=record(ident,rng.choice(['','','text']),sender=sender,group=group,
                       seconds=rng.choice([ident,ident+20]),photo=rng.choice([True,True,False]),
                       reply=rng.choice([None,None,max(1,ident-1),ident+1]))
            if rng.randrange(16)==0:row['date']=None
            rows.append(row)
        original=list(posts(*rows));expected=fold_photo_trails(original,policy=ON)
        shuffled=original[:];rng.shuffle(shuffled)
        assert fold_photo_trails(shuffled+shuffled,policy=ON)==expected
        assert PhotoTrailView.from_json(expected.to_json())==expected
        assert {x.to_json() for x in expected.posts}=={x.to_json() for x in original}
        keys=[k for group in expected.groups for k in group]
        assert len(keys)==len(set(keys))==len(original)
        assert expected.folded_posts==len(original)-len(expected.groups)
        by_key={p.post_id:p for p in expected.posts}
        count=0
        for group in expected.groups:
            ids=set();sender=None;previous=None;origin=None;attached=0
            for n,key in enumerate(group):
                p=by_key[key];members=p.members
                if len(group)==1:continue
                users={r['sender']['id'] for r in members}
                assert len(users)==1 and next(iter(users)) is not None and int(next(iter(users)))>0
                user=next(iter(users));assert sender in (None,user);sender=user
                if n:
                    assert all(r['kind']=='message' and not (r['text'] or '').strip() and r['media'] and r['media']['kind']=='photo' for r in members)
                    for row in members:
                        assert row['reply_to_id'] is None or int(row['reply_to_id']) in ids
                        assert int(row['id'])>max(ids)
                        ids.add(int(row['id']))
                    attached+=len(members);count+=len(members)
                else:ids.update(p.member_ids)
            assert attached<=ON.max_photos
        assert count==expected.folded_photos
        # Feed the same facts to the real receiver in random individual batches.
        if trial<16:
            with tempfile.TemporaryDirectory() as temp:
                receiver=AlbumReceiver(Path(temp)/'db','one',create=True)
                arrival=rows[:];rng.shuffle(arrival)
                for row in arrival:receiver.accept(batch(row))
                assert load_photo_trails(receiver,CHAT,after_id=0,through_id=12,policy=ON)==expected
    return {'fixed_seed':3036,'observation_sets':histories,'random_SQLite_arrival_histories':16}

def snapshot_before_extent():
    with tempfile.TemporaryDirectory() as temp:
        receiver=AlbumReceiver(Path(temp)/'db','one',create=True)
        receiver.accept(batch(record(2,'A'),record(4,group=GROUP)))
        with sqlite3.connect(str(receiver.path)) as db:db.execute('PRAGMA journal_mode=WAL')
        writer=AlbumReceiver(receiver.path,'one');real=receiver._stats;did=[]
        def stats(db,key):
            result=real(db,key)
            if not did:writer.accept(batch(record(1,group=GROUP)));did.append(True)
            return result
        with patch.object(receiver,'_stats',side_effect=stats):
            before=load_photo_trails(receiver,CHAT,after_id=1,through_id=4,policy=ON)
        assert member_groups(before)==((2,4),)
        try:load_photo_trails(receiver,CHAT,after_id=1,through_id=4,policy=ON)
        except PhotoTrailError:pass
        else:raise AssertionError('later split was hidden')
        return {'snapshot_groups':member_groups(before),'subsequent_split':'refused'}

def exact_unicode_collection():
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'db';names=['é','e\u0301','tenant\x00A','tenant\x00B']
        for name in names:
            receiver=AlbumReceiver(path,name,create=True);receiver.accept(batch(record(1,name),record(2)))
        for name in names:
            receiver=AlbumReceiver(path,name)
            got=load_photo_trails(receiver,CHAT,after_id=0,through_id=2,policy=ON)
            assert got.posts[0].members[0]['text']==name and got.folded_photos==1
        return {'distinct_namespaces':len(names)}

def cancel_primary_cleanup():
    with tempfile.TemporaryDirectory() as temp:
        receiver=AlbumReceiver(Path(temp)/'db','one',create=True);receiver.accept(batch(record(1,'A')))
        before=stored(receiver);real=sqlite3.connect;error=asyncio.CancelledError('cancelled read')
        class BadClose(sqlite3.Connection):
            def close(self):super().close();raise OSError('close failed')
        def connect(*args,**kw):return real(*args,factory=BadClose,**kw)
        with patch.object(receiver_module.sqlite3,'connect',side_effect=connect),patch.object(receiver,'_stats',side_effect=error):
            try:load_photo_trails(receiver,CHAT,after_id=0,through_id=1,policy=ON)
            except asyncio.CancelledError as got:assert got is error
            else:raise AssertionError('cancellation replaced or swallowed')
        assert stored(receiver)==before
        return {'primary':'same CancelledError','originals':'unchanged'}

def daily_view_failure():
    async def scenario():
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=batch(record(1,'A'),record(2),after=0);calls=[]
            async def read(*a,**k):calls.append(1);return raw
            store=SQLiteSyncStore(root/'progress');source=SyncEngine(read,store)
            await source.initialize(CHAT,after_id=0);delivery=await source.prepare(CHAT,limit=2)
            receiver=AlbumReceiver(root/'db','one',create=True);receiver.accept(delivery)
            reader=AlbumReceiver(receiver.path,'one',max_members=1)
            try:load_photo_trails(reader,CHAT,after_id=0,through_id=2,policy=ON)
            except PhotoTrailError:pass
            else:raise AssertionError('cap ignored')
            source=SyncEngine(read,SQLiteSyncStore(store.path,create=False))
            replay=await source.prepare(CHAT,limit=2);assert replay.to_json()==delivery.to_json()
            receiver.accept(replay);await source.acknowledge(CHAT,replay.batch_id)
            assert (await source.status(CHAT)).after_id==2 and len(calls)==1
            return {'reads':1,'cursor':2,'view_limit':'did not block original replay/ack'}
    return asyncio.run(scenario())

def backfill_view_failure():
    async def scenario():
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=batch(record(1,'A'),record(2),after=0,stop='end');calls=[]
            async def read(*a,**k):calls.append(k);return raw
            store=SQLiteSyncStore(root/'progress')
            source=BackfillEngine(store,'jobs',read_batch=read,clock=lambda:NOW+timedelta(hours=2))
            req=BackfillStartRequest(collection_id='jobs',chat_id=CHAT,run_id='one',destination_id='one',origin='fresh',after_id=0,expected_predecessor=None,start_date=NOW-timedelta(hours=1),end_date=NOW+timedelta(hours=1),batch_size=2,pause_seconds=0)
            initial=(await source.start(req,submission='new')).status
            turn=await source.prepare(BackfillPrepareContext.from_status(initial))
            receiver=AlbumReceiver(root/'db','one',create=True);receiver.accept(turn.batch)
            try:load_photo_trails(receiver,CHAT,after_id=0,through_id=2,policy={})
            except PhotoTrailError:pass
            else:raise AssertionError('invalid policy accepted')
            source=BackfillEngine(SQLiteSyncStore(store.path,create=False),'jobs',read_batch=read,clock=lambda:NOW+timedelta(hours=2))
            replay=await source.prepare(BackfillPrepareContext.from_status(turn.status))
            assert replay.delivery==turn.delivery;receiver.accept(replay.batch)
            end=await source.acknowledge(replay.delivery)
            assert end.terminal_outcome=='completed' and end.after_id==2 and len(calls)==1
            return {'reads':1,'cursor':2,'terminal':'completed','receipt':'exact original delivery'}
    return asyncio.run(scenario())

with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
    for name,fn in [('interleaved whole followers and reply chains',interleaved),
                    ('unknown member inside follower album',interrupted_follower),
                    ('other known user unsafe activity remains independent',other_unsafe),
                    ('connected overlap cluster and recovery',overlap_cluster),
                    ('mixed post late barrier',mixed_late_barrier),
                    ('foreign reply refusal and independent new album anchor',foreign_reply_ends),
                    ('atomic count failure then new album trail',atomic_cap),
                    ('datetime extremes and exact boundary',midnight_and_large_span),
                    ('chat chronology independence',chat_independence),
                    ('backfilled unknown evidence withdraws old link',lambda:late_evidence('unknown')),
                    ('backfilled earlier album member poisons overlap',lambda:late_evidence('earlier')),
                    ('future reply remains ineligible',future_reply_never_becomes_earlier),
                    ('disabled policy still rejects identity conflict',disabled_invalid_original),
                    ('rehash attacks and explicit policy replacement',saved_policy_and_nested_mutations),
                    ('seeded observation properties and random receiver arrival',random_observation_properties),
                    ('WAL growth between preflight and extent query',snapshot_before_extent),
                    ('Unicode and embedded-NUL exact collection identity',exact_unicode_collection),
                    ('cancellation survives cleanup failure',cancel_primary_cleanup),
                    ('daily receipt survives view limit failure',daily_view_failure),
                    ('backfill receipt survives invalid view policy',backfill_view_failure)]:
        run(name,fn)
write()
print('All {} fresh review cases passed.'.format(len(RESULTS)))
