"""Owned account routing over existing-access groups and guarded raw batches."""

import asyncio
import logging
import math
import os
import re
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

import telethon
from telethon import errors as rpc_errors

from . import health
from .batch_engine import _integer as _batch_integer
from .batch_files import BatchStorageError, prepare_directory
from .history_window import _HistoryWindow
from .message_batch import MessageBatch, BatchFormatError, MAX_BATCH_MESSAGES, MAX_MESSAGE_ID
from .read_budget import ReadBudget, ReadBudgetError, ReadBudgetExceeded
from .sync_engine import SyncEngine
from .progress_facade import ProgressFacade
from .pool_source import _OwnedSource
from . import pool_state as state
from .pool_state import (
    PoolError, PoolConfigurationError, PoolStateError, PoolStorageError,
    PoolConflictError, PoolClockError, PoolBusyError, PoolClosedError,
    PoolIdentityError, PoolTimeoutError, PoolUnavailable, SQLiteAccountPoolStore,
    _integer, _seconds, _chat, _UnresolvedGroup, _WarmupPending,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, init=False)
class PoolAccount:
    account_id: int
    config_path: str = field(repr=False)
    session_store: object = field(default=None, repr=False, compare=False)
    label: Optional[str] = None

    def __init__(self, account_id, config_path, *, session_store=None, label=None):
        account_id = _integer(account_id, 'account_id', 1)
        try:
            path = os.fspath(config_path)
            if not isinstance(path, str) or not path:
                raise ValueError
            path = str(Path(path).expanduser().resolve())
        except (TypeError, ValueError, OSError, RuntimeError):
            raise PoolConfigurationError('An explicit account config path is required') from None
        if label is not None and (not isinstance(label, str) or len(label) > 128):
            raise PoolConfigurationError('label must be a short string or None')
        object.__setattr__(self, 'account_id', account_id)
        object.__setattr__(self, 'config_path', path)
        object.__setattr__(self, 'session_store', session_store)
        object.__setattr__(self, 'label', label)


@dataclass(frozen=True)
class PoolGroup:
    chat_id: int
    reference: object = field(default=None, repr=False)

    def __post_init__(self):
        ident = _chat(self.chat_id)
        object.__setattr__(self, 'chat_id', ident)
        if self.reference is None:
            return
        if isinstance(self.reference, int) and not isinstance(self.reference, bool):
            if self.reference != ident:
                raise PoolConfigurationError('An integer group reference must equal its canonical chat ID')
            return
        if not isinstance(self.reference, str):
            raise PoolConfigurationError('Group reference must be a username/link or its canonical ID')
        match = re.fullmatch(r'(?:(?:https?://)?(?:t\.me|telegram\.me)/|@)?'
                             r'([A-Za-z][A-Za-z0-9_]{3,31})/?', self.reference.strip())
        if match is None:
            raise PoolConfigurationError('Group reference must be a public username/link, never an invite')
        object.__setattr__(self, 'reference', '@' + match.group(1))


@dataclass(frozen=True)
class PoolPolicy:
    strategy: str = 'drain'
    attempt_timeout: float = 30.0
    max_attempts: int = 3
    transient_retry_seconds: float = 30.0
    access_retry_seconds: float = 300.0
    min_warmup_days: int = 0

    def __post_init__(self):
        if self.strategy not in ('drain', 'spread'):
            raise PoolConfigurationError('strategy must be drain or spread')
        for name in ('attempt_timeout', 'transient_retry_seconds', 'access_retry_seconds'):
            object.__setattr__(self, name, _seconds(getattr(self, name), name, positive=True))
        object.__setattr__(self, 'max_attempts', _integer(self.max_attempts, 'max_attempts', 1))
        object.__setattr__(self, 'min_warmup_days', _integer(self.min_warmup_days, 'min_warmup_days', 0, 1000000))


@dataclass(frozen=True)
class PoolAttempt:
    account_id: int
    outcome: str
    error_type: Optional[str] = None

    def to_dict(self):
        return dict(account_id=str(self.account_id), outcome=self.outcome, error_type=self.error_type)


@dataclass(frozen=True)
class PoolAccountStatus:
    account_id: int
    reasons: Tuple[str, ...]
    retry_at: Optional[float]
    remaining: int
    attempt_id: Optional[str]
    error_type: Optional[str]
    verified_at: Optional[float]
    group_restrictions: tuple = ()

    @property
    def eligible(self):
        return not self.reasons

    def to_dict(self):
        return dict(account_id=str(self.account_id), eligible=self.eligible,
                    reasons=list(self.reasons), retry_at=self.retry_at,
                    remaining=self.remaining, attempt_id=self.attempt_id,
                    error_type=self.error_type, verified_at=self.verified_at,
                    group_restrictions=[dict(chat_id=str(g), not_before=t, reason=r)
                                        for g, t, r in self.group_restrictions])


@dataclass(frozen=True)
class PoolStatus:
    observed_at: float
    accounts: Tuple[PoolAccountStatus, ...]

    def to_dict(self):
        return dict(observed_at=self.observed_at, accounts=[row.to_dict() for row in self.accounts])


@dataclass(frozen=True)
class PoolReadResult:
    batch: MessageBatch
    account_id: int
    attempts: Tuple[PoolAttempt, ...]

    def to_dict(self):
        return dict(batch=self.batch.to_dict(), account_id=str(self.account_id),
                    attempts=[row.to_dict() for row in self.attempts])


class AccountPool(ProgressFacade):
    """One process's exclusively owned account inventory and bounded reader.

    Call initialize() deliberately when provisioning pool state or enrolling
    new accounts. Reopening known state needs no initialize call. One source
    or administrative mutation may run at a time; overlap raises PoolBusyError.
    The caller continues to schedule one reader per group, across all progress
    stores and instances. This is not a distributed lock or a login service.
    """

    def __init__(self, accounts, groups, *, read_budget, state_store, policy=None,
                 health_callback=None, sync_store=None, backfill_store=None):
        try:
            accounts, groups = tuple(accounts), tuple(groups)
        except TypeError:
            raise PoolConfigurationError('accounts and groups must be finite inventories') from None
        if (len(accounts) > 1000 or len(groups) > 10000
                or any(not isinstance(a, PoolAccount) for a in accounts)
                or any(not isinstance(g, PoolGroup) for g in groups)):
            raise PoolConfigurationError('Invalid or oversized account/group inventory')
        if len({a.account_id for a in accounts}) != len(accounts):
            raise PoolConfigurationError('Duplicate expected account ID')
        if len({a.config_path for a in accounts}) != len(accounts):
            raise PoolConfigurationError('Each account must have its own configuration')
        if len({g.chat_id for g in groups}) != len(groups):
            raise PoolConfigurationError('Duplicate canonical group ID')
        if not isinstance(read_budget, ReadBudget):
            raise PoolConfigurationError('An existing ReadBudget ledger is required')
        if (not callable(getattr(state_store, 'load', None))
                or not callable(getattr(state_store, 'compare_and_swap', None))):
            raise PoolConfigurationError('state_store requires async load and compare_and_swap')
        if policy is not None and not isinstance(policy, PoolPolicy):
            raise PoolConfigurationError('policy must be a PoolPolicy')
        if health_callback is not None and not callable(health_callback):
            raise PoolConfigurationError('health_callback must be callable or None')
        self.accounts = accounts
        self.groups = {g.chat_id: g for g in groups}
        self.policy = policy or PoolPolicy()
        self.read_budget = read_budget
        self._store = state_store
        self._sources = {a.account_id: _OwnedSource(a, read_budget, self.policy, self.groups, health_callback)
                         for a in accounts}
        self._active_task = None
        self._closed = False
        self._closing = False
        self._wall_clock = time.time
        self._monotonic = time.monotonic
        self._last_time = 0.0
        self._wait_ticks = {}
        self.sync_engine = SyncEngine(self.get_message_batch, sync_store)
        self._backfill_store = backfill_store
        self._backfill_engines = {}

    @contextmanager
    def _operation(self):
        if self._closed:
            raise PoolClosedError('Account pool is closed')
        if self._active_task is not None:
            raise PoolBusyError('Another account-pool operation is active')
        self._active_task = asyncio.current_task()
        try:
            yield
        finally:
            self._active_task = None

    def _now(self, document=None):
        try:
            now = _seconds(self._wall_clock(), 'pool clock')
        except (Exception, OverflowError):
            raise PoolClockError('Pool clock is unavailable or invalid') from None
        minimum = max(self._last_time, document['observed_at'] if document is not None else 0)
        if now < minimum:
            raise PoolClockError('Pool clock precedes previously observed state') from None
        self._last_time = now
        return now

    async def _backend(self, method, *args):
        try:
            return await getattr(self._store, method)(*args)
        except asyncio.CancelledError:
            raise
        except PoolError as error:
            raise error from None
        except Exception as error:
            raise PoolStorageError('Pool store {} failed ({})'.format(method, type(error).__name__)) from None

    async def _load(self, required=True):
        raw = await self._backend('load')
        if raw is None:
            if required:
                raise PoolStateError('Pool state is absent; do not recreate known state automatically')
            return None, None
        return raw, state._decode(raw)

    async def _write(self, expected, document):
        raw = state._encode(document)
        written = await self._backend('compare_and_swap', expected, raw)
        if type(written) is not bool:
            raise PoolStorageError('Pool store compare_and_swap must return a boolean')
        if not written:
            raise PoolConflictError('Pool state changed; no new source permission was granted')
        return raw

    def _account(self, account_id):
        account_id = _integer(account_id, 'account_id', 1)
        if account_id not in self._sources:
            raise PoolConfigurationError('Account is not in this pool inventory')
        return account_id

    def _group(self, chat_id):
        chat_id = _chat(chat_id)
        if chat_id not in self.groups:
            raise PoolConfigurationError('Register the canonical group before reading it')
        return chat_id

    @staticmethod
    def _require_row(document, account_id):
        row = document['accounts'].get(str(account_id))
        if row is None:
            raise PoolStateError('Account is not enrolled in this pool state')
        return row

    def _status(self, document, chat_id, now):
        rows = []
        ticks = self._monotonic()
        for account in self.accounts:
            aid = account.account_id
            row = self._require_row(document, aid)
            budget = self.read_budget.status(aid)
            reasons, deadlines = [], []
            indefinite = False
            if row['active'] is not None:
                reasons.append('unresolved_attempt')
                indefinite = True
            if row['repair'] is not None:
                reasons.append(row['repair'])
                indefinite = True
            deadline = max(row['not_before'], now + max(0, self._wait_ticks.get(aid, 0) - ticks))
            if deadline > now:
                reasons.append('waiting')
                deadlines.append(deadline)
            fact = row['groups'].get(str(chat_id)) if chat_id is not None else None
            if fact is not None and fact['until'] > now:
                reasons.append(fact['reason'])
                deadlines.append(fact['until'])
            if budget.warmup_day < self.policy.min_warmup_days:
                reasons.append('warmup')
                deadlines.append(budget.started_at + self.policy.min_warmup_days * 86400)
            if budget.remaining == 0:
                reasons.append('budget')
                if budget.next_available_at is None:
                    indefinite = True
                else:
                    deadlines.append(budget.next_available_at)
            retry_at = None if indefinite else (max(deadlines) if deadlines else now)
            rows.append(PoolAccountStatus(aid, tuple(reasons), retry_at, budget.remaining,
                        row['active']['id'] if row['active'] is not None else None,
                        row['last_error'], row['verified_at'],
                        tuple((int(g), value['until'], value['reason'])
                              for g, value in sorted(row['groups'].items()))))
        return PoolStatus(now, tuple(rows))

    async def initialize(self):
        """Explicitly provision state/enroll accounts; never reset existing facts."""
        with self._operation():
            raw, document = await self._load(required=False)
            now = self._now(document)
            if document is None:
                document = state._new(now)
            changed = raw is None
            for account in self.accounts:
                if str(account.account_id) not in document['accounts']:
                    document['accounts'][str(account.account_id)] = state._row()
                    changed = True
            # Check policy configuration before provisioning state.
            result = self._status(document, None, now)
            if changed:
                document['observed_at'] = now
                await self._write(raw, document)
            return result

    async def get_pool_status(self, chat_id=None):
        """Read pool facts and ledger allowance, with no client or credential I/O."""
        if chat_id is not None:
            chat_id = self._group(chat_id)
        _, document = await self._load()
        return self._status(document, chat_id, self._now(document))

    def _preflight(self):
        if telethon.__version__ != '1.45.0':
            raise PoolConfigurationError('AccountPool source operations require Telethon 1.45.0')
        sessions, credentials = set(), set()
        for source in self._sources.values():
            session, fingerprint = source.preflight()
            if session in sessions or (fingerprint is not None and fingerprint in credentials):
                raise PoolConfigurationError('Account inventory contains duplicate session credentials')
            sessions.add(session)
            if fingerprint is not None:
                credentials.add(fingerprint)

    async def _admit(self, raw, document, account_id, chat_id, kind):
        row = self._require_row(document, account_id)
        if row['active'] is not None:
            raise PoolConflictError('Account already has an unresolved attempt')
        now = self._now(document)
        ident = uuid4().hex
        if row['last_recovery'] is not None and row['last_recovery']['attempt_id'] == ident:
            raise PoolStateError('A fresh attempt identity could not be created')
        row['active'] = dict(id=ident, chat_id=str(chat_id) if chat_id is not None else None,
                             kind=kind, admitted_at=now)
        document['observed_at'] = now
        # A failed/ambiguous reply is never reconciled into permission to read.
        expected = await self._write(raw, document)
        return expected, ident

    def _failure(self, error, chat_id):
        if isinstance(error, PoolIdentityError):
            return 'identity_mismatch', False, None
        if isinstance(error, _UnresolvedGroup):
            return 'unresolved', True, self.policy.access_retry_seconds
        if isinstance(error, (ReadBudgetExceeded, _WarmupPending)):
            return 'budget' if isinstance(error, ReadBudgetExceeded) else 'warmup', True, None
        if isinstance(error, PoolTimeoutError):
            return 'transport', True, self.policy.transient_retry_seconds
        if isinstance(error, (PoolError, BatchStorageError, BatchFormatError, ReadBudgetError)):
            return 'local', False, None
        finding = health.classify(error, include_reported=True)
        if finding is not None:
            if finding.verdict == health.WAITING:
                if finding.wait_seconds is None or finding.wait_seconds < 0:
                    return 'unknown', False, None
                return 'waiting', True, max(1, finding.wait_seconds)
            if finding.verdict in (health.LOGGED_OUT, health.BANNED, health.RESTRICTED):
                return finding.verdict.replace(' ', '_'), True, None
            if finding.verdict == health.NO_ACCESS and chat_id is not None:
                return 'no_access', True, self.policy.access_retry_seconds
        # Owned local filesystem operations re-raise with suppressed context.
        # Do not mistake even a native ConnectionError from local I/O for a
        # reason to change accounts. Unknown provenance stops conservatively.
        if (isinstance(error, (ConnectionError, asyncio.TimeoutError))
                and not error.__suppress_context__):
            return 'transport', True, self.policy.transient_retry_seconds
        if isinstance(error, rpc_errors.ServerError):
            return 'transport', True, self.policy.transient_retry_seconds
        return 'unknown', False, None

    @staticmethod
    def _prefix(value):
        if not isinstance(value, MessageBatch) or not value.messages:
            return None
        if value.stop_reason == 'interrupted':
            return value
        wire = value.to_dict()
        return MessageBatch._from_records(int(wire['chat_id']), int(wire['after_id']),
                    wire['messages'], wire['media_mode'], 'interrupted')

    async def _settle(self, expected, document, account_id, attempt_id, chat_id,
                      source_error=None, batch=None, recheck=False):
        row = self._require_row(document, account_id)
        if row['active'] is None or row['active']['id'] != attempt_id:
            raise PoolConflictError('Source outcome no longer owns this account attempt')
        try:
            now = self._now(document)
            outcome, retry, delay = ('ok', False, None) if source_error is None else self._failure(source_error, chat_id)
            row['active'] = None
            row['last_error'] = type(source_error).__name__ if source_error is not None else None
            if self._sources[account_id].verified_id == account_id:
                row['verified_at'] = now
            if outcome in ('logged_out', 'banned', 'restricted', 'identity_mismatch'):
                row['repair'] = outcome
            if outcome in ('waiting', 'transport'):
                deadline = _seconds(now + delay, 'retry deadline')
                row['not_before'] = max(row['not_before'], deadline)
                self._wait_ticks[account_id] = max(self._wait_ticks.get(account_id, 0), self._monotonic() + delay)
            if outcome in ('no_access', 'unresolved') and chat_id is not None:
                old = row['groups'].get(str(chat_id), {}).get('until', 0)
                row['groups'][str(chat_id)] = dict(until=max(old, _seconds(now + delay, 'group deadline')),
                                                  reason=outcome, error_type=type(source_error).__name__)
            if source_error is None and recheck:
                row['repair'] = None
            document['observed_at'] = now
            raw = await self._write(expected, document)
            return raw, outcome, retry
        except asyncio.CancelledError:
            raise
        except Exception as error:
            local = error if isinstance(error, PoolError) else PoolStateError(
                'Account outcome could not settle ({})'.format(type(error).__name__))
            local.partial_result = self._prefix(batch if batch is not None else
                                                getattr(source_error, 'partial_result', None))
            if source_error is not None:
                local.read_error = source_error
            raise local from None

    async def read(self, chat_id, *, after_id=0, limit=200, download_media_to=None,
                   start_date=None, end_date=None):
        """Read once through the first successful eligible account, with provenance."""
        chat_id = self._group(chat_id)
        after_id = _batch_integer(after_id, 'after_id', 0, MAX_MESSAGE_ID)
        limit = _batch_integer(limit, 'limit', 1, MAX_BATCH_MESSAGES)
        _HistoryWindow.from_dates(start_date, end_date)
        root = prepare_directory(download_media_to) if download_media_to is not None else None
        options = dict(after_id=after_id, limit=limit, download_media_to=root,
                       start_date=start_date, end_date=end_date)
        with self._operation():
            raw, document = await self._load()
            attempts, tried = [], set()
            preflighted = False
            while len(tried) < self.policy.max_attempts:
                now = self._now(document)
                statuses = self._status(document, chat_id, now)
                available = [row for row in statuses.accounts if row.eligible and row.account_id not in tried]
                if not available:
                    break
                if self.policy.strategy == 'spread':
                    available.sort(key=lambda row: -row.remaining)  # stable inventory-order ties
                if not preflighted:
                    self._preflight()
                    preflighted = True
                aid = available[0].account_id
                tried.add(aid)
                expected, ident = await self._admit(raw, document, aid, chat_id, 'read')
                batch = source_error = None
                try:
                    batch = await self._sources[aid].run(chat_id, **options)
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    source_error = error
                raw, outcome, retry = await self._settle(expected, document, aid, ident, chat_id,
                                                        source_error, batch)
                attempts.append(PoolAttempt(aid, outcome, type(source_error).__name__ if source_error else None))
                if source_error is None:
                    return PoolReadResult(batch, aid, tuple(attempts))
                source_error.pool_account_id = aid
                source_error.pool_attempts = tuple(attempts)
                if self._prefix(getattr(source_error, 'partial_result', None)) is not None or not retry:
                    raise source_error
            now = self._now(document)
            statuses = self._status(document, chat_id, now)
            deadlines = [row.retry_at for row in statuses.accounts if row.retry_at is not None]
            retry_after = max(0, math.ceil(min(deadlines) - now)) if deadlines else None
            raise PoolUnavailable(statuses.accounts, attempts, retry_after) from None

    async def get_message_batch(self, group_id, *, after_id=0, limit=200,
                                download_media_to=None, start_date=None, end_date=None):
        """The existing bounded-reader signature, returning MessageBatch only."""
        result = await self.read(group_id, after_id=after_id, limit=limit,
                    download_media_to=download_media_to, start_date=start_date, end_date=end_date)
        return result.batch

    async def recover_account(self, account_id, *, attempt_id, previous_reader_stopped,
                              retry_not_before):
        """Retire one unknown attempt after explicit quiescence and retry policy.

        This never acknowledges data, grants allowance, shortens a known wait or
        asserts account health. Retain the exact arguments for a harmless retry.
        """
        account_id = self._account(account_id)
        try:
            state._token(attempt_id)
            if previous_reader_stopped is not True:
                raise ValueError
            if not isinstance(retry_not_before, datetime) or retry_not_before.utcoffset() is None:
                raise ValueError
            deadline = _seconds(retry_not_before.timestamp(), 'retry_not_before')
        except (ValueError, TypeError, OverflowError):
            raise PoolConfigurationError('Recovery requires an exact attempt, stopped-reader assertion and aware UTC bound') from None
        with self._operation():
            raw, document = await self._load()
            now = self._now(document)
            row = self._require_row(document, account_id)
            previous = row['last_recovery']
            if previous is not None and previous['attempt_id'] == attempt_id:
                if previous['retry_not_before'] != deadline:
                    raise PoolConflictError('A retained recovery retry changed its inputs')
                return self._status(document, None, now)
            if row['active'] is None or row['active']['id'] != attempt_id:
                raise PoolConflictError('Recovery does not name the active account attempt')
            row['active'] = None
            row['not_before'] = max(row['not_before'], deadline, now)
            row['last_recovery'] = dict(attempt_id=attempt_id, retry_not_before=deadline, recovered_at=now)
            document['observed_at'] = now
            await self._write(raw, document)
            return self._status(document, None, now)

    async def recheck_account(self, account_id):
        """Reload a repaired login and verify identity after known waits expire."""
        account_id = self._account(account_id)
        with self._operation():
            raw, document = await self._load()
            now = self._now(document)
            row = self._require_row(document, account_id)
            if row['active'] is not None:
                raise PoolConflictError('Recover the unresolved account attempt before rechecking')
            if row['not_before'] > now or self._wait_ticks.get(account_id, 0) > self._monotonic():
                raise PoolConflictError('A known account wait has not expired')
            await self._sources[account_id].retire()
            self._preflight()
            expected, ident = await self._admit(raw, document, account_id, None, 'recheck')
            error = None
            try:
                await self._sources[account_id].run()
            except asyncio.CancelledError:
                raise
            except Exception as caught:
                error = caught
            await self._settle(expected, document, account_id, ident, None, error, recheck=True)
            if error is not None:
                raise error
            return self._status(document, None, self._now(document))

    async def close(self):
        """Stop owned activity and retire clients; new source calls stay closed."""
        current = asyncio.current_task()
        if current is self._active_task or any(current is getattr(s, 'task', None) for s in self._sources.values()):
            raise PoolBusyError('Cannot close a pool from inside its own source operation or observer')
        if self._closing:
            raise PoolBusyError('Pool close is already in progress')
        self._closed = True
        self._closing = True
        try:
            active = self._active_task
            if active is not None and not active.done():
                active.cancel()
                try:
                    await active
                except asyncio.CancelledError:
                    if not active.done():
                        raise
                except Exception:
                    pass  # the source caller retains its own exception
            first = None
            for source in self._sources.values():
                try:
                    await source.retire()
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    first = first or error
            if first is not None:
                raise first
        finally:
            self._closing = False

    async def __aenter__(self):
        if self._closed:
            raise PoolClosedError('Account pool is closed')
        return self

    async def __aexit__(self, kind, error, traceback):
        try:
            await self.close()
        except BaseException as cleanup:
            if error is None:
                raise
            try:
                logger.warning('Account-pool cleanup failed (%s)', type(cleanup).__name__)
            except BaseException:
                pass
        return False
