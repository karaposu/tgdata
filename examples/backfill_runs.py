"""Offline public backfill/receiver example with a real process restart.

Fresh temporary demonstration (synthetic source, sockets blocked):
    python examples/backfill_runs.py --demo

Keep its application database; provisioning is an explicit decision:
    python examples/backfill_runs.py --demo --directory ./backfill-demo --new
    python examples/backfill_runs.py --demo --directory ./backfill-demo

One SQLite database holds separate daily/history progress namespaces and the
application's exact receiver observations. This is an offline reference-only
demonstration, not a Telegram worker or automatic arbitrary-crash recovery.
"""
import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch
from uuid import uuid4

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tgdata import TgData, BackfillStartRequest, BackfillRunRef, BackfillPrepareContext

from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3

from tgdata import MessageBatch
from tgdata import BackfillDeliveryRef


class ExampleStateError(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


class ApplicationDatabase:
    """Explicit provisioning; every later transaction opens known state with mode=rw."""
    def __init__(self, path, *, create=False):
        self.path = Path(path).resolve()
        if create:
            fd = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
            with self.transaction(write=True, initialize=True) as db:
                db.execute('CREATE TABLE example_meta (key TEXT PRIMARY KEY, data TEXT NOT NULL)')
                db.execute('CREATE TABLE example_progress (namespace TEXT NOT NULL, chat_id INTEGER NOT NULL, '
                           'data TEXT NOT NULL, PRIMARY KEY(namespace, chat_id))')
                db.execute('CREATE TABLE example_receipts (receipt TEXT PRIMARY KEY, batch TEXT NOT NULL)')
                db.execute('CREATE TABLE example_messages (chat_id TEXT NOT NULL, message_id TEXT NOT NULL, '
                           'record TEXT NOT NULL, PRIMARY KEY(chat_id, message_id))')
                db.execute("INSERT INTO example_meta VALUES ('schema-version', '1')")
        else:
            with self.transaction():
                pass

    @contextmanager
    def transaction(self, *, write=False, initialize=False):
        db = None
        primary = None
        try:
            db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True,
                                 isolation_level=None, timeout=5)
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            if not initialize:
                version = db.execute("SELECT data FROM example_meta WHERE key='schema-version'").fetchone()
                if version != ('1',):
                    raise ExampleStateError('Unsupported or missing application schema')
                db.execute('SELECT namespace, chat_id, data FROM example_progress LIMIT 0')
                db.execute('SELECT receipt, batch FROM example_receipts LIMIT 0')
                db.execute('SELECT chat_id, message_id, record FROM example_messages LIMIT 0')
            yield db
            db.commit()
        except BaseException as error:
            primary = error
            if db is not None:
                try:
                    db.rollback()
                except Exception:
                    pass  # Cleanup is not authority to replace the original failure.
            if isinstance(error, sqlite3.Error):
                raise ExampleStateError('Application storage failed ({})'.format(type(error).__name__)) from None
            raise
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception as error:
                    if primary is None:
                        raise ExampleStateError('Application storage close failed ({})'.format(type(error).__name__)) from None

    def get(self, key):
        with self.transaction() as db:
            row = db.execute('SELECT data FROM example_meta WHERE key=?', (key,)).fetchone()
        if row is None:
            return None
        try:
            return json.loads(row[0])
        except (ValueError, TypeError):
            raise ExampleStateError('Invalid application identity record') from None

    def remember(self, key, value):
        """Retain original intent before submission; never rewrite it on retry."""
        data = canonical(value)
        with self.transaction(write=True) as db:
            old = db.execute('SELECT data FROM example_meta WHERE key=?', (key,)).fetchone()
            if old is not None and old[0] != data:
                raise ExampleStateError('Application identity was retained with different input')
            if old is None:
                db.execute('INSERT INTO example_meta VALUES (?, ?)', (key, data))


class NamespaceStore:
    """Small caller-owned load/CAS adapter: namespace is configured, never inferred."""
    def __init__(self, database, namespace):
        if type(namespace) is not str or not namespace:
            raise ExampleStateError('An explicit namespace is required')
        self.database, self.namespace = database, namespace

    @staticmethod
    def _key(chat_id):
        if type(chat_id) is not int or not -(1 << 63) <= chat_id < 0:
            raise ExampleStateError('A canonical negative integer chat ID is required')

    async def load(self, chat_id):
        self._key(chat_id)
        with self.database.transaction() as db:
            row = db.execute('SELECT data FROM example_progress WHERE namespace=? AND chat_id=?',
                             (self.namespace, chat_id)).fetchone()
            if row is not None and type(row[0]) is not str:
                raise ExampleStateError('Stored progress must be text')
        return row[0] if row else None

    async def compare_and_swap(self, chat_id, expected, data):
        self._key(chat_id)
        if type(data) is not str or (expected is not None and type(expected) is not str):
            raise ExampleStateError('Progress values must be opaque text')
        data.encode('utf-8')
        if expected is not None:
            expected.encode('utf-8')
        with self.database.transaction(write=True) as db:
            row = db.execute('SELECT data FROM example_progress WHERE namespace=? AND chat_id=?',
                             (self.namespace, chat_id)).fetchone()
            if row is not None and type(row[0]) is not str:
                raise ExampleStateError('Stored progress must be text')
            current = row[0] if row else None
            if current != expected:
                return False
            if row is None:
                db.execute('INSERT INTO example_progress VALUES (?, ?, ?)', (self.namespace, chat_id, data))
            else:
                db.execute('UPDATE example_progress SET data=? WHERE namespace=? AND chat_id=?',
                           (data, self.namespace, chat_id))
        return True


class Receiver:
    """Retain exact observations plus a deduplicated first-observation message index."""
    def __init__(self, database, destination_id):
        self.database, self.destination_id = database, destination_id

    @staticmethod
    def backfill_key(delivery):
        return canonical(dict(kind='backfill', delivery=delivery.to_dict()))

    def accept_backfill(self, batch, delivery):
        if not isinstance(batch, MessageBatch) or not isinstance(delivery, BackfillDeliveryRef):
            raise ExampleStateError('Expected a batch and complete delivery reference')
        if (delivery.destination_id != self.destination_id or delivery.run.chat_id != batch.chat_id
                or delivery.batch_id != batch.batch_id):
            raise ExampleStateError('Delivery differs from this receiver or batch')
        return self._accept(self.backfill_key(delivery), batch)

    def accept_daily(self, namespace, batch):
        if type(namespace) is not str or not namespace or not isinstance(batch, MessageBatch):
            raise ExampleStateError('Daily acceptance requires its namespace and batch')
        key = canonical(dict(kind='daily', namespace=namespace, chat_id=str(batch.chat_id),
                             batch_id=batch.batch_id))
        return self._accept(key, batch)

    def _accept(self, receipt, batch):
        if batch.media_mode != 'references':
            raise ExampleStateError('This example receives references only; bytes need their own durable custody')
        data = batch.to_json()
        with self.database.transaction(write=True) as db:
            old = db.execute('SELECT batch FROM example_receipts WHERE receipt=?', (receipt,)).fetchone()
            if old is not None and old[0] != data:
                raise ExampleStateError('Retained receipt has a different observation')
            if old is None:
                db.execute('INSERT INTO example_receipts VALUES (?, ?)', (receipt, data))
                for row in batch.messages:
                    db.execute('INSERT OR IGNORE INTO example_messages VALUES (?, ?, ?)',
                               (str(batch.chat_id), row['id'], canonical(row)))
        return old is None

    def observation(self, delivery):
        with self.database.transaction() as db:
            row = db.execute('SELECT batch FROM example_receipts WHERE receipt=?',
                             (self.backfill_key(delivery),)).fetchone()
        return MessageBatch.from_json(row[0]) if row else None

    def summary(self):
        with self.database.transaction() as db:
            receipts = db.execute('SELECT count(*) FROM example_receipts').fetchone()[0]
            rows = db.execute('SELECT chat_id, message_id FROM example_messages').fetchall()
        return dict(receipts=receipts, messages=len(rows),
                    ids=sorted([row[1] for row in rows], key=int))


CHAT = -1000000000007
HISTORY_NAMESPACE = 'history'
DAILY_NAMESPACE = 'daily'
DESTINATION = 'demo-archive'
HISTORICAL_DATE = datetime(2023, 11, 14, 12, tzinfo=timezone.utc)
DAILY_DATE = datetime(2023, 11, 15, 12, tzinfo=timezone.utc)
EXPECTED_IDS = ['101', '102', '103', '104', '105']


def synthetic_batch(chat_id, after_id, limit, start_date=None, end_date=None):
    """Valid public values; deliberately no claim about SDK or Telegram behavior."""
    rows = []
    for mid in range(101, 106):
        date = HISTORICAL_DATE if mid <= 104 else DAILY_DATE
        if mid <= after_id or (start_date is not None and not start_date <= date < end_date):
            continue
        rows.append(dict(id=str(mid), kind='message', date=date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            edit_date=None, text='Synthetic example {}'.format(mid),
            sender=dict(id=None, name=None, username=None), post_author=None, reply_to_id=None,
            forward_from_id=None, grouped_id=None, service_action=None, media=None))
    rows = rows[:limit]
    value = dict(schema='tgdata.message-batch', version=1, chat_id=str(chat_id),
        after_id=str(after_id), next_after_id=rows[-1]['id'] if rows else str(after_id),
        media_mode='references', stop_reason='limit' if len(rows) == limit else 'end', messages=rows)
    value['batch_id'] = hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()
    return MessageBatch(value)


class DemoTgData(TgData):
    def __init__(self, database):
        self.source_reads = 0
        super().__init__('/unused-offline-backfill-config.ini', interactive_login=False,
            sync_store=NamespaceStore(database, DAILY_NAMESPACE),
            backfill_store=NamespaceStore(database, HISTORY_NAMESPACE))

    async def get_message_batch(self, group_id, *, after_id=0, limit=200,
                                download_media_to=None, start_date=None, end_date=None):
        if group_id != CHAT or download_media_to is not None:
            raise ExampleStateError('This synthetic example has one reference-only group')
        self.source_reads += 1
        return synthetic_batch(group_id, after_id, limit, start_date, end_date)


def required(database, key):
    value = database.get(key)
    if value is None:
        raise ExampleStateError('Known application identity is missing; do not enroll again')
    return value


async def retained_control(tg, database, run, action, key):
    """The app persists one deliberate command before sending it, including context."""
    name = 'command:' + key
    saved = database.get(name)
    if saved is None:
        status = await tg.get_backfill_status(run)
        saved = dict(run=run.to_dict(), command_id=uuid4().hex, action=action,
                     expected_control_revision=status.control_revision)
        database.remember(name, saved)
    if saved['run'] != run.to_dict() or saved['action'] != action:
        raise ExampleStateError('Retained command has a different scope/action')
    # No refreshing a retained command's expected revision when it conflicts.
    return await tg.control_backfill(run, command_id=saved['command_id'], action=saved['action'],
                                     expected_control_revision=saved['expected_control_revision'])


async def seed_worker(directory):
    database = ApplicationDatabase(directory/'application.sqlite3')
    request = BackfillStartRequest.from_dict(required(database, 'history-request'))
    tg = DemoTgData(database)
    await tg.initialize_sync(CHAT, after_id=104)
    database.remember('daily-enrolled', dict(chat_id=str(CHAT), after_id='104'))
    started = await tg.start_backfill(request, submission='new')
    database.remember('history-run', started.status.run.to_dict())
    turn = await tg.prepare_backfill(BackfillPrepareContext.from_status(started.status))
    database.remember('first-delivery', turn.delivery.to_dict())
    Receiver(database, DESTINATION).accept_backfill(turn.batch, turn.delivery)
    assert (await tg.get_backfill_status(started.status.run)).after_id == 0
    assert tg.source_reads == 1
    print('Receiver committed the first batch; simulating exit before acknowledgment.', flush=True)
    os._exit(73)  # Owned demonstration process only; parent waits for this exact exit.


async def cancel_successor(tg, database, request, completed):
    saved = database.get('cancel-request')
    submission = 'retry'
    if saved is None:
        if completed.history_limited:
            raise ExampleStateError('Successor identity is missing; do not invent another run')
        successor = replace(request, run_id=uuid4().hex, expected_predecessor=completed.run)
        saved = successor.to_dict()
        database.remember('cancel-request', saved)
        submission = 'new'
    successor = BackfillStartRequest.from_dict(saved)
    created = await tg.start_backfill(successor, submission=submission)
    database.remember('cancel-run', created.status.run.to_dict())
    cancelled = await retained_control(tg, database, created.status.run, 'cancel', 'cancel-successor')
    assert cancelled.status.terminal_outcome == 'cancelled'
    return cancelled.status


async def resume_worker(directory):
    database = ApplicationDatabase(directory/'application.sqlite3')
    request = BackfillStartRequest.from_dict(required(database, 'history-request'))
    reference = BackfillRunRef.from_dict(required(database, 'history-run'))
    required(database, 'daily-enrolled')
    receiver = Receiver(database, DESTINATION)
    tg = DemoTgData(database)
    replay_source_reads = 0
    try:
        recognized = await tg.start_backfill(request, submission='retry')
        if recognized.status.run != reference:
            raise ExampleStateError('Saved creation identity differs from the run reference')
        status = await tg.get_backfill_status(reference)
        daily = await tg.get_sync_status(CHAT)
        if daily is None or daily.initial_after_id != 104:
            raise ExampleStateError('Known daily progress is missing or differs; do not initialize again')
        if status.terminal_outcome is None:
            first = BackfillDeliveryRef.from_dict(required(database, 'first-delivery'))
            if status.pending_batch_id != first.batch_id or status.after_id != 0:
                raise ExampleStateError('Outside this demo\'s chosen lost-ack boundary; inspect state explicitly')
            replay = await tg.prepare_backfill(BackfillPrepareContext.from_status(status))
            original = receiver.observation(first)
            assert original is not None and replay.batch.to_json() == original.to_json()
            assert replay.delivery == first and replay.replayed and tg.source_reads == 0
            replay_source_reads = tg.source_reads
            paused = await retained_control(tg, database, reference, 'pause', 'pause-replay')
            replay = await tg.prepare_backfill(BackfillPrepareContext.from_status(paused.status))
            assert not receiver.accept_backfill(replay.batch, replay.delivery)
            status = await tg.acknowledge_backfill(replay.delivery)
            assert status.operator_intent == 'paused' and status.after_id == 102
            await retained_control(tg, database, reference, 'resume', 'resume-reading')

            # Application scheduling: one historical turn, then at most one daily
            # turn. No library-owned background loop or overlapping group reader.
            for _ in range(6):
                status = await tg.get_backfill_status(reference)
                if status.terminal_outcome is not None:
                    break
                daily_before = await tg.get_sync_status(CHAT)
                turn = await tg.prepare_backfill(BackfillPrepareContext.from_status(status))
                if turn.wait_seconds is not None:
                    raise ExampleStateError('This quick demo chose zero spacing; a real caller schedules the wait')
                if turn.batch is not None:
                    receiver.accept_backfill(turn.batch, turn.delivery)
                    status = await tg.acknowledge_backfill(turn.delivery)
                else:
                    status = turn.status
                assert await tg.get_sync_status(CHAT) == daily_before
                if daily_before.after_id < 105:
                    history_before = await tg.get_backfill_status(reference)
                    batch = await tg.sync_group(CHAT, limit=2)
                    assert batch is not None
                    receiver.accept_daily(DAILY_NAMESPACE, batch)
                    await tg.acknowledge_sync(CHAT, batch.batch_id)
                    assert await tg.get_backfill_status(reference) == history_before
            status = await tg.get_backfill_status(reference)
        if status.terminal_outcome != 'completed':
            raise ExampleStateError('History is not complete; do not silently create or resume a terminal run')
        reads_before_cancel = tg.source_reads
        cancelled = await cancel_successor(tg, database, request, status)
        assert tg.source_reads == reads_before_cancel
        history = await tg.get_backfill_status(reference)
        daily = await tg.get_sync_status(CHAT)
        summary = receiver.summary()
        assert history.terminal_outcome == 'completed' and history.after_id == 104
        assert daily.after_id == 105 and summary == dict(receipts=3, messages=5, ids=EXPECTED_IDS)
        result = dict(backfill=history.terminal_outcome, historical_after_id=history.after_id,
            daily_after_id=daily.after_id, cancelled_successor=cancelled.terminal_outcome,
            unique_messages=summary['messages'], receipts=summary['receipts'],
            source_reads=tg.source_reads, replay_source_reads=replay_source_reads)
        print(json.dumps(result, sort_keys=True), flush=True)
        return result
    finally:
        await tg.close()


def worker_process(directory, action, expected):
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', action,
                             '--directory', str(directory)], capture_output=True, text=True, timeout=30)
    if result.returncode != expected:
        raise ExampleStateError('Owned example worker stopped unexpectedly; inspect known state without resetting it')
    if result.stdout:
        print(result.stdout.strip())
    return result


def demo(directory, new):
    if new:
        directory.mkdir(parents=True, exist_ok=True)
        database = ApplicationDatabase(directory/'application.sqlite3', create=True)
        request = BackfillStartRequest(collection_id='demo-history', chat_id=CHAT,
            run_id=uuid4().hex, destination_id=DESTINATION, pause_seconds=0, expected_predecessor=None,
            batch_size=2, start_date=datetime(2023, 11, 14, tzinfo=timezone.utc),
            end_date=datetime(2023, 11, 15, tzinfo=timezone.utc))
        database.remember('history-request', request.to_dict())  # Before any library submission.
        worker_process(directory, 'seed', 73)
    else:
        ApplicationDatabase(directory/'application.sqlite3')  # mode=rw, never provisions lost state.
    result = worker_process(directory, 'resume', 0)
    return json.loads(result.stdout.strip().splitlines()[-1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--new', action='store_true', help='explicitly provision a new demo database')
    parser.add_argument('--worker', choices=('seed', 'resume'), help=argparse.SUPPRESS)
    options = parser.parse_args()
    if not options.demo and not options.worker:
        parser.print_help()
        return
    if options.worker and options.directory is None:
        parser.error('worker requires a known directory')
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('offline demo forbids network')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('offline demo forbids network')):
        if options.worker:
            asyncio.run(seed_worker(options.directory) if options.worker == 'seed' else resume_worker(options.directory))
        elif options.directory is None:
            with tempfile.TemporaryDirectory(prefix='tgdata_backfill_demo_') as tmp:
                demo(Path(tmp), True)
        else:
            demo(options.directory, options.new)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # No arbitrary backend or source text in CLI logs; no reset on failure.
        print('Stopped ({}); retained state was not reset.'.format(type(error).__name__), file=sys.stderr)
        sys.exit(1)
