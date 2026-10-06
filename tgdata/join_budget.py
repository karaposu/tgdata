"""Durable rolling 24-hour admission for join attempts, independent of reads."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import operator
from pathlib import Path
import sqlite3
import sys
import time
from typing import Optional

WINDOW_SECONDS = 86400


class JoinBudgetError(RuntimeError):
    """Local policy/storage failure, not a Telegram health verdict."""

    def __init__(self, message):
        super().__init__(message)
        self.__suppress_context__ = True


class JoinBudgetConfigError(JoinBudgetError):
    pass


class JoinBudgetStorageError(JoinBudgetError):
    pass


class UnsupportedJoinRequest(JoinBudgetError):
    pass


def _integer(value, name, minimum=0):
    try:
        if isinstance(value, bool):
            raise TypeError
        value = operator.index(value)
        if not minimum <= value < 2 ** 63:
            raise ValueError
        return int(value)
    except (TypeError, ValueError, OverflowError):
        raise JoinBudgetConfigError('{} must be an integer in {}..2**63-1'.format(name, minimum)) from None


def _epoch(value):
    try:
        if isinstance(value, bool):
            raise ValueError
        value = float(value)
        if not math.isfinite(value) or not 0 <= value <= 253402214399:
            raise ValueError
        return value
    except (TypeError, ValueError, OverflowError):
        raise JoinBudgetConfigError('Clock must return a finite nonnegative UTC timestamp') from None


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
        super().__init__('Join budget for account {} exhausted: {} of {} attempts used'.format(
            status.account_id, status.used, status.limit))


class JoinBudget:
    """Atomic attempt claims across processes sharing this persistent SQLite file.

    configure() replaces the limit while preserving usage. All admitted attempts
    remain charged for 24 hours, regardless of reply or cancellation. Synchronous
    operations run on the event loop; local storage should be quick. No connection
    or transaction is retained between calls, and no close() is needed.
    """

    def __init__(self, path, *, clock=time.time):
        if not path or str(path) == ':memory:':
            raise JoinBudgetConfigError('JoinBudget requires a persistent SQLite file')
        try:
            self.path = str(Path(path).expanduser().resolve())
        except (OSError, ValueError, TypeError, RuntimeError) as error:
            raise JoinBudgetStorageError('Invalid join-budget path ({})'.format(type(error).__name__)) from None
        self._clock = clock
        with self._transaction(initialize=True) as db:
            db.execute('CREATE TABLE IF NOT EXISTS tgdata_join_meta '
                       '(id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL)')
            row = db.execute('SELECT version FROM tgdata_join_meta WHERE id=1').fetchone()
            if row is None:
                db.execute('INSERT INTO tgdata_join_meta VALUES (1,1)')
            elif row[0] != 1:
                raise JoinBudgetStorageError('Unsupported join-budget schema version')
            db.execute('CREATE TABLE IF NOT EXISTS tgdata_join_accounts '
                       '(account_id INTEGER PRIMARY KEY, daily_limit INTEGER NOT NULL CHECK(daily_limit>=0), '
                       'last_clock REAL NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS tgdata_join_attempts '
                       '(id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL, admitted_at REAL NOT NULL, '
                       'FOREIGN KEY(account_id) REFERENCES tgdata_join_accounts(account_id))')
            db.execute('CREATE INDEX IF NOT EXISTS tgdata_join_attempts_time '
                       'ON tgdata_join_attempts(account_id, admitted_at)')

    @contextmanager
    def _transaction(self, initialize=False):
        db = None
        try:
            db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            if not initialize:
                row = db.execute('SELECT version FROM tgdata_join_meta WHERE id=1').fetchone()
                if row is None or row[0] != 1:
                    raise JoinBudgetStorageError('Unsupported or missing join-budget schema')
            yield db
            db.commit()
        except sqlite3.Error as error:
            raise JoinBudgetStorageError('Join-budget storage failed ({})'.format(type(error).__name__)) from None
        finally:
            if db is not None:
                primary = sys.exc_info()[0] is not None
                try:
                    db.close()  # Rolls back uncommitted work, including cancellation.
                except sqlite3.Error as error:
                    if not primary:
                        raise JoinBudgetStorageError('Join-budget cleanup failed ({})'.format(
                            type(error).__name__)) from None

    def configure(self, account_id, daily_limit):
        account_id = _integer(account_id, 'account_id', 1)
        daily_limit = _integer(daily_limit, 'daily_limit')
        now = _epoch(self._clock())
        with self._transaction() as db:
            old = db.execute('SELECT last_clock FROM tgdata_join_accounts WHERE account_id=?',
                             (account_id,)).fetchone()
            if old is None:
                db.execute('INSERT INTO tgdata_join_accounts VALUES (?,?,?)', (account_id, daily_limit, now))
            else:
                try:
                    now = max(now, _epoch(old[0]))
                except JoinBudgetConfigError:
                    raise JoinBudgetStorageError('Invalid stored join-budget clock') from None
                db.execute('UPDATE tgdata_join_accounts SET daily_limit=?, last_clock=? WHERE account_id=?',
                           (daily_limit, now, account_id))
            result = self._snapshot(db, account_id, now)
        return result

    def _snapshot(self, db, account_id, now=None):
        row = db.execute('SELECT * FROM tgdata_join_accounts WHERE account_id=?', (account_id,)).fetchone()
        if row is None:
            raise JoinBudgetConfigError('No join-budget policy for Telegram account {}; configure it first'.format(account_id))
        try:
            limit = _integer(row['daily_limit'], 'stored daily_limit')
            last = _epoch(row['last_clock'])
        except JoinBudgetConfigError:
            raise JoinBudgetStorageError('Invalid stored join-budget policy or clock') from None
        now = max(_epoch(self._clock()) if now is None else now, last)
        db.execute('UPDATE tgdata_join_accounts SET last_clock=? WHERE account_id=?', (now, account_id))
        db.execute('DELETE FROM tgdata_join_attempts WHERE account_id=? AND admitted_at<=?',
                   (account_id, now - WINDOW_SECONDS))
        used = db.execute('SELECT COUNT(*) FROM tgdata_join_attempts WHERE account_id=?', (account_id,)).fetchone()[0]
        remaining = max(0, limit - used)
        next_at = None
        if not remaining and limit:
            expiry = db.execute('SELECT admitted_at FROM tgdata_join_attempts WHERE account_id=? '
                                'ORDER BY admitted_at LIMIT 1 OFFSET ?', (account_id, used - limit)).fetchone()
            next_at = expiry[0] + WINDOW_SECONDS if expiry else None
        return JoinBudgetStatus(account_id, limit, used, remaining, now, next_at)

    def status(self, account_id):
        account_id = _integer(account_id, 'account_id', 1)
        with self._transaction() as db:
            return self._snapshot(db, account_id)

    def _claim(self, account_id):
        account_id = _integer(account_id, 'account_id', 1)
        with self._transaction() as db:
            status = self._snapshot(db, account_id)
            if status.remaining:
                db.execute('INSERT INTO tgdata_join_attempts(account_id,admitted_at) VALUES (?,?)',
                           (account_id, status.observed_at))
        if not status.remaining:
            raise JoinBudgetExceeded(status) from None
