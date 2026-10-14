"""Fresh PR35 probes: real published components, no production edits/network."""
import asyncio
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT))
from telethon import TelegramClient, types, errors
from telethon.extensions import BinaryReader
import telethon
from tgdata import MessageBatch, TelegramPost, AlbumAssemblyError, album_post_ids, assemble_albums, SQLiteSyncStore
from tgdata import health
from tgdata.batch_engine import _record
from tgdata.sync_engine import SyncEngine
from examples.album_assembly import AlbumReceiver, ReceiverError, collect

CHAT = -1000000000007
GROUP = 4611686018427387921
NOW = datetime(2026, 10, 14, tzinfo=timezone.utc)
RESULTS = []


def row(mid, text='', grouped=GROUP):
    value = types.Message(id=mid, peer_id=types.PeerChannel(7), date=NOW,
                          from_id=types.PeerUser(88), message=text, grouped_id=grouped)
    return _record(BinaryReader(bytes(value)).tgread_object(), TelegramClient)


def batch(records, after=0, stop='limit'):
    return MessageBatch._from_records(CHAT, after, records, 'references', stop)


def size(value):
    return len(value.to_json().encode('utf-8'))


def fresh(raw):
    return assemble_albums(raw, previous={key: None for key in album_post_ids(raw)})


def save_result(name, kind, **evidence):
    item = dict(name=name, result=kind, **evidence)
    RESULTS.append(item)
    print(json.dumps(item), flush=True)


def refused(call, kind=AlbumAssemblyError):
    try:
        call()
    except kind as error:
        return type(error).__name__ + ': ' + str(error)
    raise AssertionError('expected explicit refusal')


def mixed_permutations(root):
    records = [row(1, 'caption A'), row(2, 'singleton', None), row(3, 'caption B', GROUP+1),
               row(4, '', GROUP), row(5, '', GROUP+1), row(6, 'another', None)]
    expected = {post.post_id: post.to_json() for post in fresh(batch(records))}
    order_count = 0
    for order in itertools.permutations(range(3)):
        known = {}
        for index in order:
            raw = batch(records[index*2:index*2+2], after=index*2)
            posts = assemble_albums(raw, previous={key: known.get(key) for key in album_post_ids(raw)})
            known.update({post.post_id: post for post in posts})
        assert {key: post.to_json() for key, post in known.items()} == expected
        order_count += 1
    save_result('mixed_post_partition_order', 'CONTROL_PASS', orders=order_count, posts=len(expected), members=6)


def byte_replay_with_actual_source(root):
    async def run():
        raw = batch([row(1, 'caption '*100), row(2, 'second '*100)])
        expected, = fresh(raw)
        cap = size(raw) + size(expected)
        receiver = AlbumReceiver(root/'posts.sqlite3', 'daily', create=True, max_bytes=cap)
        source = SQLiteSyncStore(root/'source.sqlite3')
        reads = []
        async def read(chat, **options):
            reads.append(options)
            return raw
        engine = SyncEngine(read, source)
        await engine.initialize(CHAT, after_id=0)
        owed = await engine.prepare(CHAT, limit=2)
        accepted = receiver.accept(owed)
        assert accepted == (expected,)
        resumed = SyncEngine(read, SQLiteSyncStore(source.path, create=False))
        reopened = AlbumReceiver(receiver.path, 'daily', max_bytes=cap)
        assert reopened.load(expected.post_id) == expected
        replay = await resumed.prepare(CHAT, limit=2)
        assert replay.to_json() == owed.to_json() and len(reads) == 1
        error = refused(lambda: reopened.accept(replay))
        state = await resumed.status(CHAT)
        assert state.after_id == 0 and state.pending_batch_id == raw.batch_id
        assert reopened.load(expected.post_id) == expected
        with sqlite3.connect(str(receiver.path)) as db:
            receipts = db.execute('SELECT COUNT(*) FROM album_receipts').fetchone()[0]
        assert receipts == 1
        raised = AlbumReceiver(receiver.path, 'daily', max_bytes=cap+size(expected))
        assert raised.accept(replay) == (expected,)
        await resumed.acknowledge(CHAT, replay.batch_id)
        assert (await resumed.status(CHAT)).after_id == 2
        save_result('same_policy_lost_ack_byte_replay', 'COUNTEREXAMPLE_REPRODUCED', cap=cap,
                    initial_cost=cap, replay_cost=cap+size(expected), error=error,
                    source_reads=len(reads), before_manual_policy_increase=dict(cursor=state.after_id,
                    pending=True, saved_post_loadable=True, receipt_rows=receipts), raised_policy_control='PASS')
    asyncio.run(run())


def default_byte_replay(root):
    raw = batch([row(mid, 'x'*4096, None) for mid in range(1, 1301)])
    expected = fresh(raw)
    before = size(raw)+sum(size(post) for post in expected)
    repeat = before+sum(size(post) for post in expected)
    cap = 16*1024*1024
    assert before <= cap < repeat
    receiver = AlbumReceiver(root/'default.sqlite3', 'default', create=True)
    assert receiver.accept(raw) == expected
    reopened = AlbumReceiver(receiver.path, 'default')
    error = refused(lambda: reopened.accept(raw))
    with sqlite3.connect(str(receiver.path)) as db:
        counts = (db.execute('SELECT COUNT(*) FROM album_posts').fetchone()[0],
                  db.execute('SELECT COUNT(*) FROM album_receipts').fetchone()[0])
    assert counts == (1300, 1)
    save_result('default_16mib_accepted_input_replay', 'COUNTEREXAMPLE_REPRODUCED', raw_messages=1300,
                text_chars_each=4096, cap=cap, initial_cost=before, replay_cost=repeat,
                stored_posts=counts[0], stored_receipts=counts[1], error=error)


def grown_member_replay(root):
    raw = batch([row(1, 'caption'), row(2), row(3, 'separate', None)])
    added = batch([row(4)], after=3)
    receiver = AlbumReceiver(root/'members.sqlite3', 'one', create=True, max_members=3)
    receiver.accept(raw)
    grown, = receiver.accept(added)
    assert grown.member_ids == (1, 2, 4)
    reopened = AlbumReceiver(receiver.path, 'one', max_members=3)
    error = refused(lambda: reopened.accept(raw))
    assert reopened.load(grown.post_id) == grown
    widened = AlbumReceiver(receiver.path, 'one', max_members=4)
    assert sum(len(post.member_ids) for post in widened.accept(raw)) == 4
    save_result('old_accepted_input_after_other_post_growth', 'COUNTEREXAMPLE_REPRODUCED',
                unchanged_member_cap=3, initially_returned=3, later_call_returned=3,
                old_replay_wants=4, error=error, raised_policy_control='PASS')


def malformed_values(root):
    post, = fresh(batch([row(1, 'PRIVATE_CONTENT')]))
    changed = post.to_dict(); changed['members'][0]['text'] = 'tampered'
    cases = [post.to_json().replace('"version":1', '"version":1,"version":1'),
             json.dumps(changed), b'\xff', '{"n":Infinity}', 'null']
    for value in cases:
        error = refused(lambda value=value: TelegramPost.from_json(value))
        assert 'PRIVATE_CONTENT' not in error and 'tampered' not in error
    caught = None
    try:
        raise errors.ChannelPrivateError(request=None)
    except errors.ChannelPrivateError:
        try:
            TelegramPost.from_json('{}')
        except AlbumAssemblyError as error:
            caught = error
    assert caught is not None and health.classify(caught) is None and caught.__suppress_context__
    save_result('malformed_saved_values_and_rpc_context', 'CONTROL_PASS', malformed_cases=len(cases),
                local_error_health=None, content_not_exposed=True)


def committed_close_failure(root):
    receiver = AlbumReceiver(root/'close.sqlite3', 'one', create=True)
    raw = batch([row(1)])
    original = sqlite3.connect
    class BadClose(sqlite3.Connection):
        def close(self):
            super().close()
            raise OSError('lost close response')
    def connect(*args, **kwargs):
        kwargs['factory'] = BadClose
        return original(*args, **kwargs)
    with patch('examples.album_assembly.sqlite3.connect', side_effect=connect):
        refused(lambda: receiver.accept(raw), OSError)
    reopened = AlbumReceiver(receiver.path, 'one')
    assert reopened.accept(raw) == fresh(raw)
    save_result('successful_commit_failed_close', 'CONTROL_PASS', saved_data_recovered=True, replay='same revision')


def identity_modes_and_scope(root):
    raw = batch([row(1, 'one')])
    first, = fresh(raw)
    ended = batch(raw.messages, stop='end')
    assert ended.batch_id != raw.batch_id and fresh(ended) == (first,)
    other = MessageBatch._from_records(CHAT-1, 0, raw.messages, 'references', 'limit')
    alien, = fresh(other)
    refused(lambda: assemble_albums(raw, previous={first.post_id: alien}))
    a = AlbumReceiver(root/'scopes.sqlite3', 'a', create=True)
    b = AlbumReceiver(a.path, 'b', create=True)
    assert a.accept(raw) == b.accept(raw) == (first,)
    with sqlite3.connect(str(a.path)) as db:
        assert db.execute('SELECT COUNT(*) FROM album_receipts').fetchone()[0] == 2
    save_result('raw_stop_reason_chat_and_collection_scope', 'CONTROL_PASS', membership=first.membership,
                same_records_same_post=True, separate_receipts=2)


def strict_reopen_and_atomicity(root):
    absent = root/'absent.sqlite3'
    refused(lambda: AlbumReceiver(absent, 'known'), ReceiverError)
    assert not absent.exists()
    receiver = AlbumReceiver(root/'schema.sqlite3', 'known', create=True)
    refused(lambda: AlbumReceiver(receiver.path, 'typo'), ReceiverError)
    raw = batch([row(1), row(2, 'text', None)])
    with sqlite3.connect(str(receiver.path)) as db:
        db.execute("CREATE TRIGGER fail_after_post BEFORE INSERT ON album_receipts BEGIN SELECT RAISE(ABORT,'injected'); END")
    refused(lambda: receiver.accept(raw), sqlite3.IntegrityError)
    with sqlite3.connect(str(receiver.path)) as db:
        assert db.execute('SELECT COUNT(*) FROM album_posts').fetchone()[0] == 0
        assert db.execute('SELECT COUNT(*) FROM album_receipts').fetchone()[0] == 0
        db.execute('DROP TABLE album_posts')
    refused(lambda: AlbumReceiver(receiver.path, 'known'), ReceiverError)
    save_result('known_state_refusal_and_atomic_rollback', 'CONTROL_PASS', absent_file_created=False,
                typo_refused=True, post_rows_after_failure=0, receipt_rows_after_failure=0, damaged_schema_refused=True)


def main():
    head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    assert head == '19d421f1465961f90ab8a1036bd285425c2b90ad'
    with tempfile.TemporaryDirectory(prefix='tgdata-pr35-probes-') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        for function in (mixed_permutations, byte_replay_with_actual_source, default_byte_replay,
                         grown_member_replay, malformed_values, committed_close_failure,
                         identity_modes_and_scope, strict_reopen_and_atomicity):
            path = Path(tmp)/function.__name__; path.mkdir(); function(path)
    report = dict(head=head, runtime=sys.version.split()[0], telethon=telethon.__version__,
                  network='forbidden', histories=len(RESULTS),
                  counterexamples=sum(row['result']=='COUNTEREXAMPLE_REPRODUCED' for row in RESULTS),
                  source_sha256={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                                 for name in ('tgdata/album.py','examples/album_assembly.py')}, results=RESULTS)
    Path(__file__).with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Completed',report['histories'],'fresh histories;',report['counterexamples'],'counterexamples reproduced')


if __name__ == '__main__':
    main()
