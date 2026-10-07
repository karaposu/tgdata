"""Opaque account-pool permission state; no credentials, messages or quotas."""

import asyncio
import json
import math
import operator
import re

from .sync_store import SQLiteSyncStore


class PoolError(RuntimeError):
    def __init__(self, message):
        super().__init__(message)
        self.partial_result = None
        self.__suppress_context__ = True


class PoolConfigurationError(PoolError):
    pass


class PoolStateError(PoolError):
    pass


class PoolStorageError(PoolStateError):
    pass


class PoolConflictError(PoolStateError):
    pass


class PoolClockError(PoolStateError):
    pass


class PoolBusyError(PoolError):
    pass


class PoolClosedError(PoolError):
    pass


class PoolIdentityError(PoolError):
    pass


class PoolTimeoutError(PoolError):
    pass


class PoolUnavailable(PoolError):
    def __init__(self, accounts, attempts=(), retry_after=None):
        super().__init__('No eligible account can read this group now')
        self.accounts = tuple(accounts)
        self.attempts = tuple(attempts)
        self.retry_after = retry_after


class _UnresolvedGroup(PoolError):
    pass


class _WarmupPending(PoolError):
    pass


def _integer(value, name, low=0, high=(1 << 63) - 1):
    try:
        if isinstance(value, bool):
            raise ValueError
        result = int(operator.index(value))
        if not low <= result <= high:
            raise ValueError
        return result
    except (TypeError, ValueError, OverflowError):
        raise PoolConfigurationError('{} is outside its integer range'.format(name)) from None


def _seconds(value, name, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 or value > 253402214399
            or (positive and value == 0)):
        raise PoolConfigurationError('{} must be a finite {}number'.format(
            name, 'positive ' if positive else 'nonnegative ')) from None
    return float(value)


def _chat(value):
    return _integer(value, 'chat_id', -(1 << 63), -1)


def _row():
    return dict(active=None, repair=None, not_before=0.0, groups={},
                last_error=None, verified_at=None, last_recovery=None)


def _new(now):
    return dict(format='tgdata-account-pool', version=1, observed_at=now, accounts={})


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def _keys(value, names):
    if type(value) is not dict or set(value) != set(names.split()):
        raise ValueError('fields')


def _id(value, chat=False):
    if type(value) is not str:
        raise ValueError('id')
    number = int(value)
    if str(number) != value:
        raise ValueError('id')
    return _chat(number) if chat else _integer(number, 'account_id', 1)


def _token(value):
    if type(value) is not str or re.fullmatch(r'[0-9a-f]{32}', value) is None:
        raise ValueError('attempt id')


def _error_name(value):
    if value is not None and (type(value) is not str or len(value) > 128
                             or re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', value) is None):
        raise ValueError('error type')


def _decode(raw):
    try:
        if type(raw) is not str or len(raw.encode('utf-8')) > 4 * 1024 * 1024:
            raise ValueError('state text')
        value = json.loads(raw, object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError('number')))
        _keys(value, 'format version observed_at accounts')
        if value['format'] != 'tgdata-account-pool' or type(value['version']) is not int or value['version'] != 1:
            raise ValueError('version')
        observed = _seconds(value['observed_at'], 'observed_at')
        if type(value['accounts']) is not dict or len(value['accounts']) > 10000:
            raise ValueError('accounts')
        for account, row in value['accounts'].items():
            _id(account)
            _keys(row, 'active repair not_before groups last_error verified_at last_recovery')
            if row['repair'] not in (None, 'logged_out', 'banned', 'restricted', 'identity_mismatch'):
                raise ValueError('repair')
            _seconds(row['not_before'], 'not_before')
            _error_name(row['last_error'])
            if row['verified_at'] is not None and _seconds(row['verified_at'], 'verified_at') > observed:
                raise ValueError('verified time')
            if type(row['groups']) is not dict or len(row['groups']) > 10000:
                raise ValueError('groups')
            for group, fact in row['groups'].items():
                _id(group, chat=True)
                _keys(fact, 'until reason error_type')
                _seconds(fact['until'], 'until')
                if fact['reason'] not in ('no_access', 'unresolved'):
                    raise ValueError('group reason')
                _error_name(fact['error_type'])
            active = row['active']
            if active is not None:
                _keys(active, 'id chat_id kind admitted_at')
                _token(active['id'])
                if _seconds(active['admitted_at'], 'admitted_at') > observed:
                    raise ValueError('admission time')
                if active['kind'] == 'read':
                    _id(active['chat_id'], chat=True)
                elif active['kind'] != 'recheck' or active['chat_id'] is not None:
                    raise ValueError('attempt kind')
            recovery = row['last_recovery']
            if recovery is not None:
                _keys(recovery, 'attempt_id retry_not_before recovered_at')
                _token(recovery['attempt_id'])
                _seconds(recovery['retry_not_before'], 'retry_not_before')
                if _seconds(recovery['recovered_at'], 'recovered_at') > observed:
                    raise ValueError('recovery time')
                if active is not None and active['id'] == recovery['attempt_id']:
                    raise ValueError('recovered active attempt')
        return value
    except (ValueError, TypeError, OverflowError, RecursionError, PoolError):
        raise PoolStateError('Invalid or unsupported saved account-pool state') from None


def _encode(value):
    try:
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
        _decode(raw)
        return raw
    except (ValueError, TypeError, OverflowError, RecursionError):
        raise PoolStateError('Account-pool state cannot be encoded') from None


class SQLiteAccountPoolStore:
    """One logical pool's opaque state in a dedicated SQLite file.

    load() and compare_and_swap(expected, data) run short synchronous local
    transactions on the event loop. A custom backend may await remote I/O.
    Use create=False when reopening known state. Do not share this file with
    daily/history progress; the pool document has its own format discriminator.
    """

    def __init__(self, path, *, create=True):
        try:
            self._backend = SQLiteSyncStore(path, create=create)
        except Exception as error:
            raise PoolStorageError('Pool store open failed ({})'.format(type(error).__name__)) from None
        self.path = self._backend.path

    async def load(self):
        try:
            return await self._backend.load(-1)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            raise PoolStorageError('Pool store load failed ({})'.format(type(error).__name__)) from None

    async def compare_and_swap(self, expected, data):
        try:
            return await self._backend.compare_and_swap(-1, expected, data)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            raise PoolStorageError('Pool store write failed ({})'.format(type(error).__name__)) from None
