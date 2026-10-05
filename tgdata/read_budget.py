"""Durable admission-time accounting for explicit Telegram message pulls.

One SQLite file coordinates callers on the same host. A claim is committed
before sending; failed/cancelled attempts retain their maximum charge for 24
hours. Successful replies refund unused capacity. No credentials or messages
are stored, and no database transaction crosses network I/O.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import operator
from pathlib import Path
import sqlite3
import time
from typing import Optional
import uuid


WINDOW_SECONDS = 24 * 60 * 60
_MAX_INT = (1 << 63) - 1


class ReadBudgetError(RuntimeError):
    """A local budget/configuration/storage stop, not a Telegram verdict."""

    def __init__(self, message):
        super().__init__(message)
        self.partial_result = None
        # A local stop raised during a Telegram-error handler must not inherit
        # that error's account-health classification through implicit context.
        self.__suppress_context__ = True


class ReadBudgetConfigError(ReadBudgetError):
    pass


class ReadBudgetStorageError(ReadBudgetError):
    pass


class UnsupportedBudgetRequest(ReadBudgetError):
    pass


def _integer(value, name, minimum=0):
    try:
        if isinstance(value, bool):
            raise TypeError
        number = operator.index(value)
        if not minimum <= number <= _MAX_INT:
            raise ValueError
        return int(number)
    except (TypeError, ValueError, OverflowError):
        raise ReadBudgetConfigError(f'{name} must be an integer between {minimum} and {_MAX_INT}') from None


def _epoch(value):
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ReadBudgetConfigError('started_at must include a timezone')
        value = value.timestamp()
    try:
        if isinstance(value, bool):
            raise ValueError
        result = float(value)
        if not math.isfinite(result) or not 0 <= result <= 253402214399:
            raise ValueError
        return result
    except (TypeError, ValueError, OverflowError):
        raise ReadBudgetConfigError('time must be a finite, nonnegative UTC timestamp') from None


def _warmup(value, maximum):
    if value is None:
        return []
    try:
        rows = value.items() if hasattr(value, 'items') else value
        curve = sorted((_integer(day, 'warm-up day'), _integer(cap, 'warm-up cap'))
                       for day, cap in rows)
    except (TypeError, ValueError):
        raise ReadBudgetConfigError('warmup must contain (day, cap) pairs') from None
    if curve and curve[0][0] != 0:
        raise ReadBudgetConfigError('warmup must start at day zero')
    previous_day, previous_cap = -1, -1
    for day, cap in curve:
        if day <= previous_day or cap < previous_cap or cap > maximum:
            raise ReadBudgetConfigError('warmup days must be unique and caps nondecreasing, at most daily_limit')
        previous_day, previous_cap = day, cap
    return curve


def _iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


@dataclass(frozen=True)
class ReadBudgetStatus:
    account_id: int
    limit: int
    used: int
    reserved: int
    remaining: int
    warmup_day: int
    started_at: float
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
        return {
            'account_id': self.account_id, 'limit': self.limit,
            'used': self.used, 'reserved': self.reserved, 'remaining': self.remaining,
            'warmup_day': self.warmup_day, 'started_at': _iso(self.started_at),
            'observed_at': _iso(self.observed_at),
            'next_available_at': _iso(self.next_available_at), 'retry_after': self.retry_after,
            'window_seconds': WINDOW_SECONDS,
        }


class ReadBudgetExceeded(ReadBudgetError):
    """Capacity was refused before send; partial_result belongs to the caller's operation."""

    def __init__(self, status, requested, next_available_at):
        self.status = status
        self.account_id = status.account_id
        self.requested = requested
        self.next_available_at = next_available_at
        self.retry_after = (max(0, math.ceil(next_available_at - status.observed_at))
                            if next_available_at is not None else None)
        advice = (f'retry in {self.retry_after}s' if self.retry_after is not None
                  else 'a smaller request or policy change is required')
        super().__init__(f'Read budget for account {status.account_id} cannot admit {requested} messages: '
                         f'{status.remaining} remaining of {status.limit}; {advice}')


@dataclass(frozen=True)
class _Reservation:
    token: str
    account_id: int
    amount: int


class ReadBudget:
    """A shared rolling 24-hour ledger, keyed by verified Telegram account ID.

    configure() explicitly replaces the daily limit and warm-up curve. It
    preserves existing usage and, unless supplied, the existing start time.
    All instances/processes that should coordinate must use the same file.
    clock is injectable for offline tests; production callers use UTC wall time.
    SQLite connections are short-lived, so this object needs no close method.
    """

    def __init__(self, path, *, clock=time.time):
        if not path or str(path) == ':memory:':
            raise ReadBudgetConfigError('ReadBudget requires a persistent SQLite file path')
        self.path = str(Path(path).expanduser().resolve())
        self._clock = clock
        with self._transaction(initialize=True) as db:
            db.execute('CREATE TABLE IF NOT EXISTS tgdata_budget_meta '
                       '(id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL)')
            row = db.execute('SELECT version FROM tgdata_budget_meta WHERE id = 1').fetchone()
            if row is None:
                db.execute('INSERT INTO tgdata_budget_meta VALUES (1, 1)')
            elif row[0] != 1:
                raise ReadBudgetStorageError('Unsupported read-budget schema version')
            db.execute('CREATE TABLE IF NOT EXISTS tgdata_budget_accounts '
                       '(account_id INTEGER PRIMARY KEY, daily_limit INTEGER NOT NULL CHECK (daily_limit >= 0), '
                       'warmup TEXT NOT NULL, started_at REAL NOT NULL, last_clock REAL NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS tgdata_budget_charges '
                       '(token TEXT PRIMARY KEY, account_id INTEGER NOT NULL, admitted_at REAL NOT NULL, '
                       'amount INTEGER NOT NULL CHECK (amount >= 0), settled INTEGER NOT NULL CHECK (settled IN (0, 1)), '
                       'FOREIGN KEY (account_id) REFERENCES tgdata_budget_accounts(account_id))')
            db.execute('CREATE INDEX IF NOT EXISTS tgdata_budget_charges_time '
                       'ON tgdata_budget_charges(account_id, admitted_at)')

    @contextmanager
    def _transaction(self, initialize=False):
        db = None
        try:
            db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA foreign_keys = ON')
            db.execute('BEGIN IMMEDIATE')
            if not initialize:
                row = db.execute('SELECT version FROM tgdata_budget_meta WHERE id = 1').fetchone()
                if row is None or row[0] != 1:
                    raise ReadBudgetStorageError('Unsupported or missing read-budget schema')
            yield db
            db.commit()
        except sqlite3.Error as error:
            raise ReadBudgetStorageError(f'Read-budget storage failed ({type(error).__name__})') from None
        finally:
            if db is not None:
                # Closing rolls back on any exception; no lock survives an await.
                db.close()

    def configure(self, account_id, daily_limit, warmup=None, started_at=None):
        account_id = _integer(account_id, 'account_id', 1)
        daily_limit = _integer(daily_limit, 'daily_limit')
        curve = _warmup(warmup, daily_limit)
        now = _epoch(self._clock())
        with self._transaction() as db:
            old = db.execute('SELECT * FROM tgdata_budget_accounts WHERE account_id = ?', (account_id,)).fetchone()
            if old is not None:
                now = max(now, _epoch(old['last_clock']))
            start = (_epoch(started_at) if started_at is not None
                     else _epoch(old['started_at']) if old is not None else now)
            if start > now:
                raise ReadBudgetConfigError('started_at cannot be in the future')
            encoded = json.dumps(curve, separators=(',', ':'))
            if old is None:
                db.execute('INSERT INTO tgdata_budget_accounts VALUES (?, ?, ?, ?, ?)',
                           (account_id, daily_limit, encoded, start, now))
            else:
                # REPLACE would delete the parent row and can destroy quota history.
                db.execute('UPDATE tgdata_budget_accounts SET daily_limit = ?, warmup = ?, '
                           'started_at = ?, last_clock = ? WHERE account_id = ?',
                           (daily_limit, encoded, start, now, account_id))
            status, _ = self._snapshot(db, account_id, now)
        return status

    @staticmethod
    def _limit(policy, now):
        maximum, curve, start = policy
        day = max(0, int((now - start) // WINDOW_SECONDS))
        cap = maximum
        if curve:
            cap = curve[0][1]
            for threshold, value in curve:
                if threshold > day:
                    break
                cap = value
        return cap, day

    def _snapshot(self, db, account_id, raw_now=None):
        row = db.execute('SELECT * FROM tgdata_budget_accounts WHERE account_id = ?', (account_id,)).fetchone()
        if row is None:
            raise ReadBudgetConfigError(f'No read-budget policy for Telegram account {account_id}; configure it first')
        try:
            policy = (_integer(row['daily_limit'], 'stored daily_limit'),
                      _warmup(json.loads(row['warmup']), row['daily_limit']), _epoch(row['started_at']))
            now = max(_epoch(self._clock()) if raw_now is None else raw_now, _epoch(row['last_clock']))
        except (ReadBudgetConfigError, TypeError, ValueError):
            raise ReadBudgetStorageError('Invalid stored read-budget policy or clock') from None
        db.execute('UPDATE tgdata_budget_accounts SET last_clock = ? WHERE account_id = ?', (now, account_id))
        db.execute('DELETE FROM tgdata_budget_charges WHERE account_id = ? AND admitted_at <= ?',
                   (account_id, now - WINDOW_SECONDS))
        sums = db.execute('SELECT COALESCE(SUM(amount), 0), '
                          'COALESCE(SUM(CASE WHEN settled = 0 THEN amount ELSE 0 END), 0) '
                          'FROM tgdata_budget_charges WHERE account_id = ?', (account_id,)).fetchone()
        used, reserved = int(sums[0]), int(sums[1])
        cap, day = self._limit(policy, now)
        remaining = max(0, cap - used)
        next_at = self._retry_at(db, account_id, policy, now, used, 1) if remaining == 0 else None
        return ReadBudgetStatus(account_id, cap, used, reserved, remaining, day, policy[2], now, next_at), policy

    def _retry_at(self, db, account_id, policy, now, used, requested):
        if requested > policy[0]:
            return None
        changes = {}
        for row in db.execute('SELECT admitted_at, amount FROM tgdata_budget_charges WHERE account_id = ?',
                              (account_id,)):
            at = row['admitted_at'] + WINDOW_SECONDS
            changes[at] = changes.get(at, 0) + row['amount']
        for day, _ in policy[1]:
            at = policy[2] + day * WINDOW_SECONDS
            if now < at <= 253402300799:
                changes.setdefault(at, 0)
        for at in sorted(changes):
            used -= changes[at]
            if self._limit(policy, at)[0] - used >= requested:
                return at
        return None

    def status(self, account_id):
        account_id = _integer(account_id, 'account_id', 1)
        with self._transaction() as db:
            status, _ = self._snapshot(db, account_id)
        return status

    def _reserve(self, account_id, amount):
        account_id = _integer(account_id, 'account_id', 1)
        amount = _integer(amount, 'requested messages', 1)
        denied = None
        with self._transaction() as db:
            status, policy = self._snapshot(db, account_id)
            if amount > status.remaining:
                denied = ReadBudgetExceeded(status, amount, self._retry_at(
                    db, account_id, policy, status.observed_at, status.used, amount))
            else:
                token = uuid.uuid4().hex
                db.execute('INSERT INTO tgdata_budget_charges VALUES (?, ?, ?, ?, 0)',
                           (token, account_id, status.observed_at, amount))
        if denied is not None:
            raise denied from None
        return _Reservation(token, account_id, amount)

    def _settle(self, reservation, actual):
        actual = _integer(actual, 'returned message count')
        with self._transaction() as db:
            # Prune/observe time first. An old response must never refund a new window.
            self._snapshot(db, reservation.account_id)
            row = db.execute('SELECT settled FROM tgdata_budget_charges WHERE token = ? AND account_id = ?',
                             (reservation.token, reservation.account_id)).fetchone()
            if row is None or row['settled']:
                return
            if actual:
                db.execute('UPDATE tgdata_budget_charges SET amount = ?, settled = 1 WHERE token = ?',
                           (actual, reservation.token))
            else:
                db.execute('DELETE FROM tgdata_budget_charges WHERE token = ?', (reservation.token,))
