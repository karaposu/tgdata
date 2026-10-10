"""Local rolling-day allowance for admitted join attempts.

Claims are synchronous, durable and never refunded. This standalone ledger does
not authenticate an account or guard Telegram calls; the future joining consumer
must claim once immediately before each actual attempt using verified identity.
"""

import asyncio
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import math
import operator
import os
from pathlib import Path
import sqlite3
import time
from typing import Optional


WINDOW_SECONDS = 86400
_MAX_INT = (1 << 63) - 1
_MAX_EPOCH = 253402214399  # Leave one day for an ISO-formattable expiry.
logger = logging.getLogger(__name__)


class JoinBudgetError(RuntimeError):
    """A local allowance failure, never a Telegram health verdict."""

    def __init__(self, message):
        super().__init__(message)
        self.__suppress_context__ = True


class JoinBudgetConfigError(JoinBudgetError):
    pass


class JoinBudgetStorageError(JoinBudgetError):
    pass


def _integer(value, name, minimum=0):
    try:
        if isinstance(value, bool):
            raise ValueError
        result = operator.index(value)
        if not minimum <= result <= _MAX_INT:
            raise ValueError
        return int(result)
    except asyncio.CancelledError:
        raise
    except Exception:
        raise JoinBudgetConfigError('{} must be an integer between {} and {}'.format(
            name, minimum, _MAX_INT)) from None


def _epoch(value):
    try:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError
        result = float(value)
        if not math.isfinite(result) or not 0 <= result <= _MAX_EPOCH:
            raise ValueError
        return result
    except asyncio.CancelledError:
        raise
    except Exception:
        raise JoinBudgetConfigError('Clock must return a finite UTC timestamp between 0 and {}'.format(
            _MAX_EPOCH)) from None


def _iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


@dataclass(frozen=True)
class JoinBudgetStatus:
    account_id: int
    limit: int
    used: int
    remaining: int
    observed_at: float
    next_available_at: Optional[float]

    @property
    def retry_after(self):
        if self.remaining:
            return 0
        if self.next_available_at is None:
            return None
        return max(0, math.ceil(self.next_available_at - self.observed_at))

    def to_dict(self):
        return dict(account_id=self.account_id, limit=self.limit, used=self.used,
                    remaining=self.remaining, observed_at=_iso(self.observed_at),
                    next_available_at=_iso(self.next_available_at),
                    retry_after=self.retry_after, window_seconds=WINDOW_SECONDS)


class JoinBudgetExceeded(JoinBudgetError):
    def __init__(self, status):
        self.status = status
        self.account_id = status.account_id
        self.retry_after = status.retry_after
        self.next_available_at = status.next_available_at
        super().__init__('Join allowance exhausted for Telegram account {}'.format(self.account_id))


def _cleanup_warning(operation, error):
    try:
        logger.warning('Join-budget cleanup failed during %s (%s)', operation, type(error).__name__)
    except BaseException:
        pass


# Exact owned columns prevent a schema marker from blessing an incompatible table.
_COLUMNS = {
    'tgdata_join_meta': [('id', 'INTEGER', 0, None, 1), ('version', 'INTEGER', 1, None, 0)],
    'tgdata_join_accounts': [('account_id', 'INTEGER', 0, None, 1),
                             ('daily_limit', 'INTEGER', 1, None, 0),
                             ('last_clock', 'REAL', 1, None, 0)],
    'tgdata_join_attempts': [('id', 'INTEGER', 0, None, 1),
                             ('account_id', 'INTEGER', 1, None, 0),
                             ('admitted_at', 'REAL', 1, None, 0)],
}
_INDEX = 'tgdata_join_attempts_time'
_OBJECTS = {name: ('table', name) for name in _COLUMNS}
_OBJECTS[_INDEX] = ('index', 'tgdata_join_attempts')


class JoinBudget:
    """Persistent admitted-attempt allowance, shared through one local SQLite file.

    Explicit create=True provisions a fresh file/namespace; default reopening
    refuses missing state. Parent directories must exist. Each call uses short
    synchronous I/O with a five-second SQLite busy timeout; no close is needed.
    Retain the file and use an accurate host clock. Separate files do not share
    usage, and arbitrary external edits/backup rollback cannot be detected.
    """

    def __init__(self, path, *, create=False, clock=time.time):
        if type(create) is not bool or not callable(clock):
            raise JoinBudgetConfigError('create must be boolean and clock must be callable')
        try:
            raw = os.fspath(path)
            if not isinstance(raw, str) or raw in ('', ':memory:') or raw.lower().startswith('file:'):
                raise ValueError
            self.path = str(Path(raw).expanduser().resolve())
        except asyncio.CancelledError:
            raise
        except Exception:
            raise JoinBudgetConfigError('JoinBudget requires a persistent filesystem path') from None
        self._clock = clock
        with self._transaction(initialize=create):
            pass

    @staticmethod
    def _schema(db, initialize):
        names = tuple(_OBJECTS)
        found = {name: (kind, table) for name, kind, table in db.execute(
            'SELECT name, type, tbl_name FROM sqlite_master WHERE name IN (?,?,?,?)', names)}
        if not found and initialize:
            db.execute('CREATE TABLE tgdata_join_meta '
                       '(id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL)')
            db.execute('INSERT INTO tgdata_join_meta VALUES(1,1)')
            db.execute('CREATE TABLE tgdata_join_accounts '
                       '(account_id INTEGER PRIMARY KEY, daily_limit INTEGER NOT NULL CHECK(daily_limit>=0), '
                       'last_clock REAL NOT NULL)')
            db.execute('CREATE TABLE tgdata_join_attempts '
                       '(id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL, admitted_at REAL NOT NULL, '
                       'FOREIGN KEY(account_id) REFERENCES tgdata_join_accounts(account_id))')
            db.execute('CREATE INDEX tgdata_join_attempts_time '
                       'ON tgdata_join_attempts(account_id, admitted_at)')
        elif found != _OBJECTS:
            raise JoinBudgetStorageError('Missing or incomplete join-budget schema')
        for name, expected in _COLUMNS.items():
            columns = [tuple(row[1:]) for row in db.execute('PRAGMA table_info({})'.format(name))]
            if columns != expected:
                raise JoinBudgetStorageError('Incompatible join-budget columns')
        meta = db.execute('SELECT id, version FROM tgdata_join_meta').fetchall()
        if meta != [(1, 1)] or any(type(value) is not int for value in meta[0]):
            raise JoinBudgetStorageError('Unsupported or missing join-budget schema version')
        fk = db.execute('PRAGMA foreign_key_list(tgdata_join_attempts)').fetchall()
        if fk != [(0, 0, 'tgdata_join_accounts', 'account_id', 'account_id', 'NO ACTION', 'NO ACTION', 'NONE')]:
            raise JoinBudgetStorageError('Incompatible join-budget account relationship')
        indexes = [row for row in db.execute('PRAGMA index_list(tgdata_join_attempts)') if row[1] == _INDEX]
        columns = db.execute('PRAGMA index_info(tgdata_join_attempts_time)').fetchall()
        if (len(indexes) != 1 or indexes[0][2:] != (0, 'c', 0)
                or columns != [(0, 1, 'account_id'), (1, 2, 'admitted_at')]):
            raise JoinBudgetStorageError('Incompatible join-budget time index')
        orphan = db.execute(
            'SELECT 1 FROM tgdata_join_attempts t LEFT JOIN tgdata_join_accounts a '
            "ON a.account_id=t.account_id WHERE typeof(t.account_id)!='integer' "
            'OR t.account_id<1 OR a.account_id IS NULL LIMIT 1').fetchone()
        if orphan:
            raise JoinBudgetStorageError('Invalid stored join-budget account relationship')

    @contextmanager
    def _transaction(self, initialize=False):
        db, primary = None, None
        try:
            uri = Path(self.path).as_uri() + ('?mode=rwc' if initialize else '?mode=rw')
            db = sqlite3.connect(uri, uri=True, timeout=5, isolation_level=None)
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE')
            self._schema(db, initialize)
            yield db
            db.commit()
        except BaseException as error:
            primary = error
            if db is not None:
                try:
                    db.rollback()
                except BaseException as secondary:
                    _cleanup_warning('rollback', secondary)
            if isinstance(error, sqlite3.Error):
                raise JoinBudgetStorageError('Join-budget storage failed ({})'.format(type(error).__name__)) from None
            raise
        finally:
            if db is not None:
                try:
                    db.close()
                except BaseException as error:
                    if primary is not None:
                        _cleanup_warning('close', error)
                    elif isinstance(error, asyncio.CancelledError) or not isinstance(error, Exception):
                        raise
                    else:
                        raise JoinBudgetStorageError('Join-budget close failed ({})'.format(
                            type(error).__name__)) from None

    def _now(self):
        try:
            value = self._clock()
        except asyncio.CancelledError:
            raise
        except Exception as error:
            raise JoinBudgetConfigError('Join-budget clock failed ({})'.format(type(error).__name__)) from None
        return _epoch(value)

    def _observe(self, db, account_id, new_limit=None):
        row = db.execute('SELECT daily_limit, last_clock FROM tgdata_join_accounts WHERE account_id=?',
                         (account_id,)).fetchone()
        if row is None:
            if new_limit is None:
                raise JoinBudgetConfigError('No join-budget policy for Telegram account {}; configure it first'.format(
                    account_id))
            cap, previous = new_limit, 0.0
        else:
            cap, previous = row
            if (type(cap) is not int or not 0 <= cap <= _MAX_INT
                    or type(previous) not in (int, float) or not math.isfinite(previous)
                    or not 0 <= previous <= _MAX_EPOCH):
                raise JoinBudgetStorageError('Invalid stored join-budget policy or clock')
            invalid = db.execute(
                'SELECT 1 FROM tgdata_join_attempts WHERE account_id=? AND '
                "(typeof(id)!='integer' OR id<1 OR typeof(admitted_at) NOT IN ('integer','real') "
                'OR admitted_at<0 OR admitted_at>?) LIMIT 1', (account_id, previous)).fetchone()
            if invalid:
                raise JoinBudgetStorageError('Invalid stored join-budget attempt')
        # Validate against the prior horizon BEFORE a forward clock can hide damage.
        now = max(self._now(), previous)
        cap = cap if new_limit is None else new_limit
        if row is None:
            db.execute('INSERT INTO tgdata_join_accounts VALUES(?,?,?)', (account_id, cap, now))
        else:
            db.execute('UPDATE tgdata_join_accounts SET daily_limit=?, last_clock=? WHERE account_id=?',
                       (cap, now, account_id))
        db.execute('DELETE FROM tgdata_join_attempts WHERE account_id=? AND admitted_at<=?',
                   (account_id, now - WINDOW_SECONDS))
        used = db.execute('SELECT count(*) FROM tgdata_join_attempts WHERE account_id=?', (account_id,)).fetchone()[0]
        remaining = max(0, cap - used)
        next_at = None
        if remaining == 0 and cap > 0:
            stamp = db.execute('SELECT admitted_at FROM tgdata_join_attempts WHERE account_id=? '
                               'ORDER BY admitted_at LIMIT 1 OFFSET ?', (account_id, used - cap)).fetchone()[0]
            next_at = stamp + WINDOW_SECONDS
        return JoinBudgetStatus(account_id, cap, used, remaining, now, next_at)

    def configure(self, account_id, daily_limit):
        """Set a policy without discarding usage; zero blocks new claims."""
        account_id = _integer(account_id, 'account_id', 1)
        daily_limit = _integer(daily_limit, 'daily_limit')
        with self._transaction() as db:
            status = self._observe(db, account_id, daily_limit)
        return status

    def status(self, account_id):
        """Observe local usage; this snapshot reserves no allowance."""
        account_id = _integer(account_id, 'account_id', 1)
        with self._transaction() as db:
            status = self._observe(db, account_id)
        return status

    def _claim(self, account_id):
        """Consume one attempt, with no refund. Only successful return permits use."""
        account_id = _integer(account_id, 'account_id', 1)
        denied = None
        with self._transaction() as db:
            status = self._observe(db, account_id)
            if status.remaining == 0:
                denied = JoinBudgetExceeded(status)
            else:
                db.execute('INSERT INTO tgdata_join_attempts(account_id,admitted_at) VALUES(?,?)',
                           (account_id, status.observed_at))
        # Refusal still commits the clock/expiry observation before surfacing.
        if denied is not None:
            raise denied from None
