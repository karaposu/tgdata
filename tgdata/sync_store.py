"""Durable daily progress and its small asynchronous storage contract.

A backend implements ``await load(chat_id) -> str | None`` and
``await compare_and_swap(chat_id, expected, data) -> bool``. The latter must
compare and commit atomically; success means durable storage, not write-behind.
The text is opaque to the backend. Tgdata owns its validation and transitions.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
import operator
from pathlib import Path
import re
import sqlite3
from typing import Optional

from .message_batch import MessageBatch, MAX_MESSAGE_ID, MIN_LONG
from .history_window import _HistoryWindow, _encode_date, _decode_date


logger = logging.getLogger(__name__)
_STATE_KEYS = frozenset({
    'version', 'chat_id', 'initial_after_id', 'after_id', 'media_mode',
    'pending', 'last_acked_batch_id',
})
_TABLES = {'tgdata_sync_meta', 'tgdata_sync_state'}


class SyncError(RuntimeError):
    """A local continuation failure, never an inferred Telegram verdict.

    read_error retains a read failure when its completed prefix could not be
    persisted. It is data, not an exception cause used for health classification.
    """

    def __init__(self, message):
        super().__init__(message)
        self.read_error = None
        self.__suppress_context__ = True


class SyncConfigurationError(SyncError):
    pass


class SyncNotInitializedError(SyncConfigurationError):
    pass


class SyncConflictError(SyncError):
    pass


class SyncStorageError(SyncError):
    pass


def _integer(value, name, minimum, maximum):
    try:
        if isinstance(value, bool):
            raise TypeError
        number = operator.index(value)
        if not minimum <= number <= maximum:
            raise ValueError
        return int(number)
    except (TypeError, ValueError, OverflowError):
        raise SyncConfigurationError('{} must be an integer in {}..{}'.format(
            name, minimum, maximum)) from None


def _chat_id(value):
    return _integer(value, 'canonical chat_id', MIN_LONG, -1)


def _mode(value):
    if type(value) is not str or value not in ('references', 'download'):
        raise SyncConfigurationError('media_mode must be references or download')
    return value


def _batch_id(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise SyncConfigurationError('batch_id must be a lowercase SHA-256 identifier')
    return value


def _stored_id(value, minimum, maximum):
    if type(value) is not str or re.fullmatch(r'-?(?:0|[1-9][0-9]*)', value) is None:
        raise ValueError('invalid stored identifier')
    if len(value) > 20:
        raise ValueError('stored identifier outside range')
    number = int(value)
    if str(number) != value or not minimum <= number <= maximum:
        raise ValueError('stored identifier outside range')
    return number


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate stored field')
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError('nonfinite stored value')


@dataclass(frozen=True)
class SyncStatus:
    """One consistent, content-free view of a group's continuation."""

    chat_id: int
    initial_after_id: int
    after_id: int
    media_mode: str
    pending_batch_id: Optional[str]
    pending_message_count: int
    pending_next_after_id: Optional[int]
    last_acked_batch_id: Optional[str]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    last_days: Optional[int] = None

    def to_dict(self):
        value = {
            'chat_id': str(self.chat_id),
            'initial_after_id': str(self.initial_after_id),
            'after_id': str(self.after_id),
            'media_mode': self.media_mode,
            'pending_batch_id': self.pending_batch_id,
            'pending_message_count': self.pending_message_count,
            'pending_next_after_id': (str(self.pending_next_after_id)
                                      if self.pending_next_after_id is not None else None),
            'last_acked_batch_id': self.last_acked_batch_id,
        }
        if self.start_date is not None:
            value.update(start_date=_encode_date(self.start_date),
                         end_date=_encode_date(self.end_date), last_days=self.last_days)
        return value


@dataclass(frozen=True)
class _State:
    chat_id: int
    initial_after_id: int
    after_id: int
    media_mode: str
    pending: Optional[MessageBatch] = None
    last_acked_batch_id: Optional[str] = None
    window: Optional[_HistoryWindow] = None
    window_days: Optional[int] = None

    def status(self):
        pending = self.pending.to_dict() if self.pending is not None else None
        return SyncStatus(
            self.chat_id, self.initial_after_id, self.after_id, self.media_mode,
            pending['batch_id'] if pending else None,
            len(pending['messages']) if pending else 0,
            int(pending['next_after_id']) if pending else None,
            self.last_acked_batch_id,
            self.window.start_date if self.window is not None else None,
            self.window.end_date if self.window is not None else None,
            self.window_days,
        )

    def encode(self):
        value = {
            'version': 1, 'chat_id': str(self.chat_id),
            'initial_after_id': str(self.initial_after_id), 'after_id': str(self.after_id),
            'media_mode': self.media_mode,
            'pending': self.pending.to_dict() if self.pending is not None else None,
            'last_acked_batch_id': self.last_acked_batch_id,
        }
        if self.window is not None:
            value['version'] = 2
            value['window'] = dict(self.window.to_dict(), last_days=self.window_days)
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False)


def _decode(data, chat_id):
    try:
        if type(data) is not str:
            raise TypeError('state must be text')
        data.encode('utf-8')
        value = json.loads(data, object_pairs_hook=_unique_pairs, parse_constant=_nonfinite)
        if type(value) is not dict:
            raise ValueError('state must be an object')
        version = value.get('version')
        if type(version) is not int or version not in (1, 2):
            raise ValueError('unsupported state version')
        expected_keys = _STATE_KEYS if version == 1 else _STATE_KEYS | {'window'}
        if value.keys() != expected_keys:
            raise ValueError('unsupported stored fields')
        window = window_days = None
        if version == 2:
            saved = value['window']
            if type(saved) is not dict or saved.keys() != {'start_date', 'end_date', 'last_days'}:
                raise ValueError('invalid stored window fields')
            window = _HistoryWindow(_decode_date(saved['start_date']), _decode_date(saved['end_date']))
            if saved['last_days'] is not None:
                window_days = _integer(saved['last_days'], 'last_days', 1, MAX_MESSAGE_ID)
                if window.end_date - window.start_date != timedelta(days=window_days):
                    raise ValueError('stored window differs from last_days')
        source = _stored_id(value['chat_id'], MIN_LONG, -1)
        initial = _stored_id(value['initial_after_id'], 0, MAX_MESSAGE_ID)
        after = _stored_id(value['after_id'], initial, MAX_MESSAGE_ID)
        mode = _mode(value['media_mode'])
        if source != chat_id:
            raise ValueError('stored source does not match key')
        last_ack = value['last_acked_batch_id']
        if last_ack is not None:
            _batch_id(last_ack)
        if (after > initial) != (last_ack is not None):
            raise ValueError('acknowledgment and position disagree')
        pending = None
        if value['pending'] is not None:
            pending = MessageBatch(value['pending'])
            _validate_batch(pending, source, after, mode, nonempty=True, window=window)
            if pending.batch_id == last_ack:
                raise ValueError('pending batch was already acknowledged')
        return _State(source, initial, after, mode, pending, last_ack, window, window_days)
    except (TypeError, ValueError, OverflowError, RecursionError, SyncError) as error:
        raise SyncStorageError('Invalid saved sync state ({})'.format(type(error).__name__)) from None


def _validate_batch(batch, chat_id, after_id, media_mode, nonempty=False, window=None):
    if not isinstance(batch, MessageBatch):
        raise SyncStorageError('Reader did not return a MessageBatch')
    value = batch.to_dict()
    if (value['chat_id'] != str(chat_id) or value['after_id'] != str(after_id)
            or value['media_mode'] != media_mode):
        raise SyncStorageError('Batch does not match the enrolled source, cursor or media mode')
    if not value['messages']:
        if nonempty or value['stop_reason'] != 'end':
            raise SyncStorageError('An empty batch cannot be pending work')
    if window is not None:
        for record in value['messages']:
            if record['date'] is None or not window.contains(_decode_date(record['date'])):
                raise SyncStorageError('Batch contains a message outside the saved window')
    return value


def _cleanup_warning(operation, error):
    try:
        logger.warning('Sync storage cleanup failed during %s (%s)', operation, type(error).__name__)
    except BaseException:
        pass


class SQLiteSyncStore:
    """Persistent opaque sync state in a local SQLite file.

    The async methods do short synchronous local I/O, with a five-second busy
    timeout. They hold no connection across an await. Remote backends may await
    their own I/O while implementing the same load/compare_and_swap contract.
    Parent directories must exist. Use a separate store for each destination's
    logical collection; share the state and pending artifacts for a sequential move.
    """

    def __init__(self, path):
        try:
            if (path is None or isinstance(path, bool) or str(path) in ('', ':memory:')
                    or str(path).lower().startswith('file:')):
                raise ValueError
            self.path = str(Path(path).expanduser().resolve())
        except (TypeError, ValueError, OSError, RuntimeError):
            raise SyncConfigurationError('SQLiteSyncStore requires a persistent filesystem path') from None
        with self._transaction(initialize=True, write=True):
            pass

    @staticmethod
    def _schema(db, initialize):
        names = {row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name IN ('tgdata_sync_meta', 'tgdata_sync_state')")}
        if not names and initialize:
            db.execute('CREATE TABLE tgdata_sync_meta '
                       '(id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL)')
            db.execute('INSERT INTO tgdata_sync_meta VALUES (1, 1)')
            db.execute('CREATE TABLE tgdata_sync_state '
                       '(chat_id INTEGER PRIMARY KEY, data TEXT NOT NULL)')
        elif names != _TABLES:
            raise SyncStorageError('Missing or incomplete sync schema')
        row = db.execute('SELECT version FROM tgdata_sync_meta WHERE id = 1').fetchone()
        if row is None or type(row[0]) is not int or row[0] != 1:
            raise SyncStorageError('Unsupported or missing sync schema version')
        # A version marker is not sufficient if an existing table lost its columns.
        db.execute('SELECT chat_id, data FROM tgdata_sync_state LIMIT 0')

    @contextmanager
    def _transaction(self, initialize=False, write=False):
        db = None
        primary = None
        try:
            uri = Path(self.path).as_uri() + ('?mode=rwc' if initialize else '?mode=rw')
            db = sqlite3.connect(uri, uri=True, timeout=5, isolation_level=None)
            db.execute('PRAGMA synchronous = FULL')
            db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            self._schema(db, initialize)
            yield db
            db.commit()
        except BaseException as error:
            primary = error
            if db is not None:
                try:
                    db.rollback()
                except Exception as secondary:
                    _cleanup_warning('rollback', secondary)
            if isinstance(error, sqlite3.Error):
                raise SyncStorageError('Sync storage failed ({})'.format(type(error).__name__)) from None
            raise
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception as error:
                    if primary is not None:
                        _cleanup_warning('close', error)
                    else:
                        raise SyncStorageError('Sync storage close failed ({})'.format(
                            type(error).__name__)) from None

    async def load(self, chat_id):
        chat_id = _chat_id(chat_id)
        with self._transaction() as db:
            row = db.execute('SELECT data FROM tgdata_sync_state WHERE chat_id = ?', (chat_id,)).fetchone()
            if row is not None and type(row[0]) is not str:
                raise SyncStorageError('Stored sync value is not text')
        return row[0] if row is not None else None

    async def compare_and_swap(self, chat_id, expected, data):
        chat_id = _chat_id(chat_id)
        if type(data) is not str or (expected is not None and type(expected) is not str):
            raise SyncConfigurationError('Sync store values must be text (or None for an absent expectation)')
        try:
            data.encode('utf-8')
            if expected is not None:
                expected.encode('utf-8')
        except UnicodeError:
            raise SyncConfigurationError('Sync store values must be valid UTF-8') from None
        with self._transaction(write=True) as db:
            row = db.execute('SELECT data FROM tgdata_sync_state WHERE chat_id = ?', (chat_id,)).fetchone()
            if row is not None and type(row[0]) is not str:
                raise SyncStorageError('Stored sync value is not text')
            current = row[0] if row is not None else None
            if current != expected:
                return False
            if row is None:
                db.execute('INSERT INTO tgdata_sync_state (chat_id, data) VALUES (?, ?)', (chat_id, data))
            else:
                db.execute('UPDATE tgdata_sync_state SET data = ? WHERE chat_id = ?', (data, chat_id))
        return True
