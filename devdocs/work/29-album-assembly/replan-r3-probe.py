"""Planning feasibility only: immutable accepted records, separate post views.

Actual SQLite, MessageBatch/TelegramPost and SyncEngine are used. This is not the
production receiver, migration tooling or the required full combined prebuild.
"""
import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tgdata import MessageBatch, TelegramPost, AlbumAssemblyError, SQLiteSyncStore
from tgdata.album import album_post_ids, assemble_albums, _identity, _revision, _limits
from tgdata.message_batch import _canonical, _json_pairs, _invalid_constant
from tgdata.sync_engine import SyncEngine
from telethon import TelegramClient, types
from telethon.extensions import BinaryReader
from tgdata.batch_engine import _record

CHAT = -1000000000007
GROUP = 4611686018427387921
RESULTS = []


class ProbeReceiver:
    """The proposed acceptance shape, deliberately confined to this work file."""
    def __init__(self, path, collection='one', *, create=False, max_members=10000, max_bytes=16777216):
        _limits(max_members, max_bytes)
        self.path, self.collection = Path(path), collection
        self.max_members, self.max_bytes = max_members, max_bytes
        self.last_changes = None
        if create:
            with self.path.open('xb'):
                pass
            with self.db() as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('CREATE TABLE meta (version INTEGER NOT NULL)')
                db.execute('INSERT INTO meta VALUES (2)')
                db.execute('CREATE TABLE collections (name TEXT PRIMARY KEY NOT NULL)')
                db.execute('CREATE TABLE members (collection TEXT NOT NULL, chat INTEGER NOT NULL, '
                           'id INTEGER NOT NULL, post TEXT NOT NULL, record TEXT NOT NULL, digest TEXT NOT NULL, '
                           'PRIMARY KEY(collection,chat,id))')
                db.execute('CREATE INDEX post_lookup ON members(collection,post,id)')
                db.execute('CREATE TABLE receipts (collection TEXT NOT NULL, batch TEXT NOT NULL, PRIMARY KEY(collection,batch))')
                db.execute('INSERT INTO collections VALUES (?)', (collection,))
                db.commit()
        with self.db() as db:
            self.validate(db)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path.resolve().as_uri()+'?mode=rw', uri=True, isolation_level=None, timeout=0)
        try:
            yield db
        finally:
            db.close()

    def validate(self, db):
        if db.execute('SELECT version FROM meta').fetchall() != [(2,)]:
            raise ValueError('unsupported receiver schema')
        if db.execute('SELECT 1 FROM collections WHERE name=?', (self.collection,)).fetchone() is None:
            raise ValueError('missing collection')

    def _load(self, db, key):
        n, amount = db.execute('SELECT COUNT(*),COALESCE(SUM(length(CAST(record AS BLOB))),0) '
                              'FROM members WHERE collection=? AND post=?', (self.collection,key)).fetchone()
        if not n:
            return None
        if n > self.max_members or amount > self.max_bytes:
            raise AlbumAssemblyError('post view exceeds policy')
        records, chat = [], None
        for stored_chat, ident, encoded, digest in db.execute(
                'SELECT chat,id,record,digest FROM members WHERE collection=? AND post=? ORDER BY id',
                (self.collection,key)):
            if hashlib.sha256(encoded.encode()).hexdigest() != digest:
                raise ValueError('stored member digest mismatch')
            record = json.loads(encoded, object_pairs_hook=_json_pairs, parse_constant=_invalid_constant)
            if _canonical(record) != encoded or record['id'] != str(ident):
                raise ValueError('stored member metadata mismatch')
            if _identity(str(stored_chat),record) != key or (chat is not None and chat != stored_chat):
                raise ValueError('stored member owner mismatch')
            chat = stored_chat; records.append(record)
        document = dict(schema='tgdata.telegram-post',version=1,post_id=key,chat_id=str(chat),
                        grouped_id=records[0]['grouped_id'],media_mode='references',
                        membership='single' if records[0]['grouped_id'] is None else 'unconfirmed',members=records)
        document['revision'] = _revision(document)
        return TelegramPost(document,max_members=self.max_members,max_bytes=self.max_bytes)

    def load(self, key):
        with self.db() as db:
            db.execute('BEGIN')
            self.validate(db)
            return self._load(db,key)

    def _matches(self, db, chat, member):
        encoded = _canonical(member)
        expected = (encoded, _identity(str(chat),member), hashlib.sha256(encoded.encode()).hexdigest(),
                    self.collection,chat,int(member['id']))
        # Return only equality flags, never the potentially grown projection or
        # an unbounded corrupt record. Force byte comparison, not text collation.
        return db.execute('SELECT CAST(record AS BLOB)=CAST(? AS BLOB),post COLLATE BINARY=?,digest COLLATE BINARY=? '
                          'FROM members WHERE collection=? AND chat=? AND id=?', expected).fetchone()

    def accept(self, raw):
        keys = album_post_ids(raw,max_bytes=self.max_bytes)
        document = raw.to_dict()
        chat, batch_id, rows = int(document['chat_id']), document['batch_id'], document['messages']
        if document['media_mode'] != 'references' or len(rows) > self.max_members:
            raise AlbumAssemblyError('input mode or count exceeds policy')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            self.validate(db)
            received = db.execute('SELECT 1 FROM receipts WHERE collection=? AND batch=?',
                                  (self.collection,batch_id)).fetchone() is not None
            if received:
                for member in rows:
                    if self._matches(db,chat,member) != (1,1,1):
                        raise ValueError('accepted member missing or inconsistent')
            else:
                for member in rows:
                    match = self._matches(db,chat,member)
                    if match is not None and match != (1,1,1):
                        raise ValueError('conflicting stored member')
                previous = {key:self._load(db,key) for key in keys}
                # Real new-work admission. Output is validated, not stored as a
                # second authoritative copy of the same member records.
                assemble_albums(raw,previous=previous,max_members=self.max_members,max_bytes=self.max_bytes)
                for member in rows:
                    encoded = _canonical(member)
                    db.execute('INSERT OR IGNORE INTO members VALUES (?,?,?,?,?,?)',
                               (self.collection,chat,int(member['id']),_identity(str(chat),member),
                                encoded,hashlib.sha256(encoded.encode()).hexdigest()))
                db.execute('INSERT INTO receipts VALUES (?,?)',(self.collection,batch_id))
            db.commit()
            self.last_changes = db.total_changes
        return None


def row(mid,text='',group=GROUP):
    value=types.Message(id=mid,peer_id=types.PeerChannel(7),date=datetime(2026,10,14,tzinfo=timezone.utc),
                        from_id=types.PeerUser(88),message=text,grouped_id=group)
    return _record(BinaryReader(bytes(value)).tgread_object(),TelegramClient)


def batch(rows,after=0):
    return MessageBatch._from_records(CHAT,after,rows,'references','limit')


def post_values(raw):
    return assemble_albums(raw,previous={key:None for key in album_post_ids(raw)})


def size(value):
    return len(value.to_json().encode())


def record_result(name,**fields):
    RESULTS.append(dict(name=name,result='PASS',**fields));print(json.dumps(RESULTS[-1]),flush=True)


def no_projection_replay(receiver,raw):
    with patch.object(receiver,'_load',side_effect=AssertionError('replay must not load a post view')), \
            patch(__name__+'.assemble_albums',side_effect=AssertionError('replay must not assemble')):
        assert receiver.accept(raw) is None
        assert receiver.last_changes==0


async def lost_ack(root):
    raw=batch([row(1,'caption '*100),row(2,'second '*100)])
    post,=post_values(raw);cap=size(raw)+size(post)
    receiver=ProbeReceiver(root/'receiver.db',create=True,max_bytes=cap)
    store=SQLiteSyncStore(root/'progress.db');reads=[]
    async def read(*args,**options):reads.append(options);return raw
    engine=SyncEngine(read,store);await engine.initialize(CHAT,after_id=0)
    owed=await engine.prepare(CHAT,limit=2);assert receiver.accept(owed) is None
    resumed=SyncEngine(read,SQLiteSyncStore(store.path,create=False))
    receiver=ProbeReceiver(receiver.path,max_bytes=cap)
    replay=await resumed.prepare(CHAT,limit=2);assert replay.to_json()==owed.to_json()
    no_projection_replay(receiver,replay);await resumed.acknowledge(CHAT,replay.batch_id)
    assert len(reads)==1 and (await resumed.status(CHAT)).after_id==2
    assert receiver.load(post.post_id)==post
    record_result('small_byte_boundary_lost_ack',unchanged_cap=cap,source_reads=1,cursor=2,replay_writes=0)


def defaults(root):
    raw=batch([row(i,'x'*4096,None) for i in range(1,1301)])
    posts=post_values(raw)
    receiver=ProbeReceiver(root/'default.db',create=True);receiver.accept(raw)
    no_projection_replay(ProbeReceiver(receiver.path),raw)
    assert receiver.load(posts[-1].post_id)==posts[-1]
    record_result('default_16mib_replay',messages=1300,cap=16777216,replay_writes=0)


def growth(root):
    old=batch([row(1,'caption'),row(2),row(3,'single',None)]);new=batch([row(4)],after=3)
    receiver=ProbeReceiver(root/'growth.db',create=True,max_members=3)
    receiver.accept(old);receiver.accept(new)
    no_projection_replay(ProbeReceiver(receiver.path,max_members=3),old)
    assert receiver.load(album_post_ids(new)[0]).member_ids==(1,2,4)
    # Confirmation is tied to accepted input, even if another authorized writer
    # later increases policy and makes the complete post too big for this view.
    bigger=ProbeReceiver(receiver.path,max_members=4);bigger.accept(batch([row(5)],after=4))
    no_projection_replay(receiver,old)
    try:receiver.load(album_post_ids(new)[0])
    except AlbumAssemblyError:pass
    else:raise AssertionError('small view policy should refuse larger current view')
    record_result('later_growth_member_boundary',original_cap=3,current_album_members=4,
                  replay_writes=0,separate_view_refusal=True)


def integrity(root):
    raw=batch([row(1,'original')]);key=album_post_ids(raw)[0]
    cases={
        'missing':('DELETE FROM members',()),
        'content':('UPDATE members SET record=?',('changed',)),
        'digest':('UPDATE members SET digest=?',('0'*64,)),
        'post_key':('UPDATE members SET post=?',('wrong',)),
    }
    for name,(sql,args) in cases.items():
        receiver=ProbeReceiver(root/(name+'.db'),create=True);receiver.accept(raw)
        with receiver.db() as db:db.execute(sql,args)
        try:no_projection_replay(receiver,raw)
        except ValueError:pass
        else:raise AssertionError('must refuse inconsistent accepted data')
        with receiver.db() as db:assert db.execute('SELECT COUNT(*) FROM receipts').fetchone()[0]==1
    record_result('recognized_input_integrity',refused_cases=list(cases),repair_attempted=False)


def atomicity(root):
    receiver=ProbeReceiver(root/'atomic.db',create=True)
    with receiver.db() as db:
        db.execute("CREATE TRIGGER refuse_receipt BEFORE INSERT ON receipts BEGIN SELECT RAISE(ABORT,'fault'); END")
    try:receiver.accept(batch([row(1),row(2,'',None)]))
    except sqlite3.IntegrityError:pass
    else:raise AssertionError('write fault expected')
    with receiver.db() as db:
        assert db.execute('SELECT COUNT(*) FROM members').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM receipts').fetchone()[0]==0
    record_result('atomic_member_and_receipt_write',members=0,receipts=0)


def fresh_limits_and_conflicts(root):
    raw=batch([row(1,'caption'),row(2)])
    receiver=ProbeReceiver(root/'new.db',create=True,max_members=1)
    try:receiver.accept(raw)
    except AlbumAssemblyError:pass
    else:raise AssertionError('new oversized input must refuse')
    receiver=ProbeReceiver(receiver.path,max_members=3);receiver.accept(raw)
    for changed in (batch([row(1,'changed')]),batch([row(1,'caption',GROUP+1)])):
        try:receiver.accept(changed)
        except ValueError:pass
        else:raise AssertionError('existing immutable member cannot change or move posts')
    assert receiver.load(album_post_ids(raw)[0]).member_ids==(1,2)
    record_result('new_work_limits_and_record_identity',fresh_limit_refused=True,conflicts_refused=2)


def main():
    start=time.monotonic()
    before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in ('tgdata/album.py','examples/album_assembly.py','tgdata/smoke_tests/test_42_album_assembly.py')}
    with tempfile.TemporaryDirectory(prefix='tgdata29-r3-design-') as tmp, \
            patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        root=Path(tmp)
        asyncio.run(lost_ack(root));defaults(root);growth(root);integrity(root)
        atomicity(root);fresh_limits_and_conflicts(root)
    assert before=={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in before}
    report=dict(scope='planning feasibility; full candidate/prebuild pending',runtime=sys.version.split()[0],
                source_sha256=before,histories=RESULTS,product_files_changed=False,
                elapsed_seconds=round(time.monotonic()-start,3))
    Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Planning feasibility: six histories pass; production files unchanged.')


if __name__=='__main__':main()
