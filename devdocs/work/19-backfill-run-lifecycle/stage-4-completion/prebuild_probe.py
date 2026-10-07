"""Prebuild only: unchanged Stage 3, actual live source and real SQLite receiver.

Private output root must be new. No policy configure/reset, source writes or login.
"""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import socket
import sqlite3
import sys
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
spec = importlib.util.spec_from_file_location('gate_a_probe', Path(__file__).parents[1]/'live_probe.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
from telethon import functions, types, utils
from tgdata import TgData, ReadBudget, SQLiteSyncStore, MessageBatch
from tgdata.backfill import BackfillStartRequest, BackfillPrepareContext, BackfillStorageError
from tgdata.backfill_engine import BackfillEngine
from tgdata.history_window import _encode_date, _decode_date

CHAT = -1004478311025
OLD = Path('/private/tmp/tgdata19-gate-a-live-20261007')
CONFIG = Path('/Users/ns/Desktop/projects/telegram-group-scraper/config.ini')


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accept(root, turn, media):
    """Real local durable bytes, transaction and repeat-safe receipt/effect keys."""
    target = root/'receiver-media'; target.mkdir(exist_ok=True)
    for row in turn.batch.messages:
        blob = row['media']['blob'] if row['media'] else None
        if blob:
            data = (media/blob['path']).read_bytes()
            assert len(data) == blob['size'] and hashlib.sha256(data).hexdigest() == blob['sha256']
            dest = target/blob['path']
            if not dest.exists():
                with dest.open('xb') as stream:
                    stream.write(data); stream.flush(); os.fsync(stream.fileno())
            assert dest.stat().st_size == blob['size'] and digest(dest) == blob['sha256']
    fd = os.open(str(target), os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)
    with sqlite3.connect(str(root/'receiver.sqlite3')) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS receipts (ref TEXT PRIMARY KEY)')
        db.execute('CREATE TABLE IF NOT EXISTS messages (chat TEXT,id TEXT,payload TEXT,PRIMARY KEY(chat,id))')
        ref = json.dumps(turn.delivery.to_dict(), sort_keys=True)
        fresh = db.execute('INSERT OR IGNORE INTO receipts VALUES (?)', (ref,)).rowcount
        if fresh:
            for row in turn.batch.messages:
                db.execute('INSERT OR IGNORE INTO messages VALUES (?,?,?)',
                           (str(turn.batch.chat_id), row['id'], json.dumps(row, sort_keys=True)))
    with sqlite3.connect(str(root/'receiver.sqlite3')) as db:
        return dict(receipts=db.execute('SELECT count(*) FROM receipts').fetchone()[0],
                    messages=db.execute('SELECT count(*) FROM messages').fetchone()[0])


async def local_boundaries(root, report):
    for count in (0, 1):
        path = root/('local-final-{}.sqlite3'.format(count)); backend = SQLiteSyncStore(path)
        now = datetime.now(timezone.utc)
        req = BackfillStartRequest('prebuild-local', CHAT, 'run', 'receiver', 0, None,
                                  start_date=now-timedelta(days=1), end_date=now)
        async def reader(chat, **options):
            rows = []
            if count:
                rows = [dict(id='1',kind='message',date=_encode_date(now-timedelta(seconds=1)),
                    edit_date=None,text='local fixture',sender=dict(id=None,name=None,username=None),
                    post_author=None,reply_to_id=None,forward_from_id=None,grouped_id=None,
                    service_action=None,media=None)]
            return MessageBatch._from_records(chat, 0, rows, 'references', 'end')
        eng = BackfillEngine(backend, req.collection_id, read_batch=reader)
        status = (await eng.start(req, submission='new')).status
        turn = await eng.prepare(BackfillPrepareContext.from_status(status)) if count else None
        original = sqlite3.connect
        class BadClose(sqlite3.Connection):
            def close(self):
                hit = False
                if self.total_changes:
                    row = self.execute('SELECT data FROM tgdata_sync_state').fetchone()
                    hit = row and json.loads(row[0])['current']['terminal_outcome'] == 'completed'
                super().close()
                if hit: raise sqlite3.OperationalError('owned lost completion reply')
        def connect(*a, **kw): kw['factory'] = BadClose; return original(*a, **kw)
        with patch('tgdata.sync_store.sqlite3.connect', side_effect=connect):
            try:
                if count: await eng.acknowledge(turn.delivery)
                else: await eng.prepare(BackfillPrepareContext.from_status(status))
            except BackfillStorageError: pass  # Stage 3 behavior, before confirmation is built.
            else: raise AssertionError('expected original Stage 3 storage uncertainty')
        reopened = BackfillEngine(SQLiteSyncStore(path, create=False), req.collection_id)
        raw = await backend.load(CHAT)
        done = await reopened.status(status.run)
        assert done.terminal_outcome == 'completed' and done.after_id == count
        assert done.pending_batch_id is None and done.attempt_id is None
        if turn: assert (await reopened.acknowledge(turn.delivery)) == done
        assert await backend.load(CHAT) == raw
        report['checks'].append('actual post-commit close error: '+('final ack' if count else 'empty completion'))


async def main(root):
    assert p.telethon.__version__ == '1.45.0'
    root.mkdir(mode=0o700, exist_ok=False)
    account = int(json.loads((OLD/'login-status.json').read_text())['verified_account_id'])
    budget = ReadBudget(OLD/'account-read-budget.sqlite3')
    before = budget.status(account); assert before.limit == 5000 and before.remaining >= 250
    guard = p.ReadOnlyGuard(CHAT, dict(max_rpc_requests=80, max_history_requests=8,
        max_requested_slots=250, max_media_bytes=4*1024*1024), allow_media=True)
    tg = TgData(str(CONFIG), connection_pool_size=1, interactive_login=False, read_budget=budget)
    factory = tg.connection_engine._new_client
    def instrumented(*a, **kw):
        client = factory(*a, **kw); guard.instrument(client)
        client.flood_sleep_threshold = 0; client._request_retries = 0; client._connection_retries = 1
        return client
    tg.connection_engine._new_client = instrumented
    report = dict(checks=[], budget_used_before=before.used, result='UNFINISHED',
                  code_revision='3140dcd (unchanged Stage 3 product)', gate_verdict='INCONCLUSIVE')
    try:
        client = await tg.connection_engine.get_client()
        assert (await client.get_me(input_peer=False)).id == account
        peer = await client.get_input_entity(CHAT)
        messages = []; offset = 0
        for page in range(2):
            answer = await client(functions.messages.GetHistoryRequest(peer,offset,None,0,100,0,0,0),flood_sleep_threshold=0)
            if not answer.messages: break
            assert all(isinstance(m,(types.Message,types.MessageService)) and utils.get_peer_id(m.peer_id)==CHAT for m in answer.messages)
            messages.extend(answer.messages); offset = min(m.id for m in answer.messages)
            await asyncio.sleep(5)
        else: raise AssertionError('fixture requires explicit empty second descending page')
        assert len({m.id for m in messages}) == len(messages)
        photo = next(m for m in messages if m.id == 14)
        assert isinstance(photo.media, types.MessageMediaPhoto)
        data = await client.download_media(photo, file=bytes)
        blob = dict(sha256=hashlib.sha256(data).hexdigest(),size=len(data))
        rows = [dict(id=str(m.id),date=_encode_date(m.date),media_kind=type(m.media).__name__ if m.media else None) for m in sorted(messages,key=lambda m:m.id)]
        oracle = dict(method='direct descending GetHistory to explicit empty page; direct SDK media bytes',
                      chat_id=str(CHAT), captured_at=_encode_date(datetime.now(timezone.utc)),
                      complete=True, messages=rows, selected_photo=dict(id='14',**blob))
        save(root/'small-oracle.json', oracle)
        start=photo.date; end=start+timedelta(microseconds=1)
        wanted = [r for r in rows if start <= _decode_date(r['date']) < end and int(r['id']) > 13]
        assert [r['id'] for r in wanted] == ['14']
        req = BackfillStartRequest('stage4-prebuild',CHAT,'photo-run','receiver',0,None,
            origin='imported',after_id=13,media_mode='download',batch_size=2,start_date=start,end_date=end)
        backend = SQLiteSyncStore(root/'prebuild.sqlite3')
        eng = BackfillEngine(backend,req.collection_id,read_batch=tg.get_message_batch)
        status = (await eng.start(req,submission='new')).status
        ctx = BackfillPrepareContext.from_status(status); media = root/'media'
        await asyncio.sleep(5)
        turn = await eng.prepare(ctx,download_media_to=media)
        assert [r['id'] for r in turn.batch.messages] == ['14'] and turn.batch.stop_reason == 'end'
        actual = turn.batch.messages[0]['media']['blob']
        assert {k:actual[k] for k in ('sha256','size')} == blob
        assert turn.status.source_exhausted and turn.status.terminal_outcome is None
        saved = turn.batch.to_json(); report['pending_sha256']=hashlib.sha256(saved.encode()).hexdigest()
        report['checks'].append('real prepared photo matches independent ID/date/media oracle')
        await tg.close()
        with patch.object(socket.socket,'connect',side_effect=AssertionError('offline reopen')):
            reopened=BackfillEngine(SQLiteSyncStore(backend.path,create=False),req.collection_id,clock=p.forbidden_clock)
            replay=await reopened.prepare(ctx,download_media_to=media)
            assert replay.replayed and replay.batch.to_json() == saved and replay.delivery == turn.delivery
            assert accept(root,replay,media) == accept(root,replay,media) == dict(receipts=1,messages=1)
            done=await BackfillEngine(backend,req.collection_id).acknowledge(replay.delivery)
            assert done.terminal_outcome=='completed' and done.after_id==14 and done.origin=='imported'
            assert (await reopened.prepare(BackfillPrepareContext.from_status(done))).status==done
            report['checks'].append('offline exact replay, real durable receiver/dedup, final ack and complete reopen')
            await local_boundaries(root,report)
        report['result']='PASS'
    except Exception as error:
        report['error_type']=type(error).__name__
        if isinstance(error,p.ProbeStop): report['stop_code']=str(error)
        raise
    finally:
        await asyncio.wait_for(tg.close(),10)
        report.update(rpc=guard.rpc,requested_slots=guard.slots,requested_media_bytes=guard.media_bytes,
                      budget_used_after=budget.status(account).used)
        save(root/'prebuild-results.json',report)
        print(json.dumps({k:v for k,v in report.items() if k!='rpc'},sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-root',required=True,type=Path)
    args=parser.parse_args();os.umask(0o077);os.chdir(CONFIG.parent);logging.disable(logging.CRITICAL)
    asyncio.run(asyncio.wait_for(main(args.output_root),180))
