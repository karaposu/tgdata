"""Application-owned SQLite prototype for Stage 7's offline example.

Real storage/receiver primitive, not a production tgdata backend framework.
The final example carries this qualified design; no library state schema changes.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3

from tgdata import MessageBatch
from tgdata.backfill import BackfillDeliveryRef


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
