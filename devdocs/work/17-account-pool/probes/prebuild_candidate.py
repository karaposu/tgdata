"""Revision3 inquiry-only candidate: private seams over the real exported runtime.

No routing, budget, CAS, batch production or progress engine is replaced.
"""
import asyncio
from contextlib import contextmanager
import contextvars
import json
from types import MethodType
from unittest.mock import patch

from tgdata.account_pool import AccountPool as OriginalPool
from tgdata.pool_source import _await_cleanup
from tgdata.pool_state import PoolStateError, PoolBusyError, PoolConfigurationError, PoolTimeoutError
from tgdata.health import HealthMonitor

MAX_EVENTS = 128
MAX_EVENT_BYTES = 4096
MAX_TOTAL_BYTES = 65536
MAX_DROPPED = (1 << 63) - 1
_EVENT_KEYS = frozenset('kind time account verdict scope group call request wait_seconds error source'.split())
_ACCOUNT_KEYS = frozenset('label session user_id'.split())
_SCOPES = contextvars.ContextVar('tgdata17_prebuild_scopes', default=())


class _SourceInterrupted(PoolStateError):
    """No caller stop or owned timeout, but the source ended without a result."""


class ObservationBuffer:
    def __init__(self):
        self.events, self.byte_count, self.dropped = [], 0, 0

    def lose(self):
        self.dropped = min(self.dropped + 1, MAX_DROPPED)

    @staticmethod
    def scalar(value):
        if value is None:
            return value
        if type(value) is str and len(value) <= MAX_EVENT_BYTES:
            return value
        if type(value) is int and -(1 << 63) <= value < (1 << 63):
            return value
        raise ValueError('not a bounded plain health scalar')

    @staticmethod
    def keys(value, expected):
        return (type(value) is dict and len(value) == len(expected)
                and all(type(key) is str for key in value) and value.keys() == expected)

    def own(self, event):
        if not self.keys(event, _EVENT_KEYS) or not self.keys(event['account'], _ACCOUNT_KEYS):
            raise ValueError('not a health event shape')
        result = {key: self.scalar(event[key]) for key in _EVENT_KEYS if key != 'account'}
        result['account'] = {key: self.scalar(event['account'][key]) for key in _ACCOUNT_KEYS}
        if result['kind'] != 'health':
            raise ValueError('not health')
        payload = json.dumps(result, ensure_ascii=True, allow_nan=False,
                             sort_keys=True, separators=(',', ':')).encode('ascii')
        return result, len(payload)

    def capture(self, event):
        try:
            if len(self.events) >= MAX_EVENTS:
                self.lose()
                return
            owned, size = self.own(event)
            if size > MAX_EVENT_BYTES or self.byte_count + size > MAX_TOTAL_BYTES:
                self.lose()
                return
            self.events.append(owned)
            self.byte_count += size
        except (Exception, asyncio.CancelledError):
            self.lose()

    def drain(self):
        events, dropped = self.events, self.dropped
        self.events, self.byte_count, self.dropped = [], 0, 0
        return {'events': events, 'dropped': dropped}


class PoolMonitor(HealthMonitor):
    def __init__(self, buffer, label, identity):
        super().__init__(None, label, identity)
        self.buffer = buffer

    async def _deliver(self, event):
        self.buffer.capture(event)

    def _deliver_now(self, event):
        self.buffer.capture(event)

    def _health_failed(self):
        self.buffer.lose()


@contextmanager
def scope(pool):
    item = {'pool': pool, 'active': True}
    alive = tuple(s for s in _SCOPES.get() if s['active'])
    token = _SCOPES.set(alive + (item,))
    try:
        yield
    finally:
        item['active'], item['pool'] = False, None
        _SCOPES.reset(token)


def refuses_close(pool):
    return any(s['active'] and s['pool'] is pool for s in _SCOPES.get())


async def source_run(self, chat_id=None, **options):
    outcome = {}

    async def observed():
        async with self.monitor.call('account_pool_read' if chat_id is not None else 'account_pool_recheck',
                                     group=chat_id):
            try:
                value = (await self.batch_reader.fetch_batch(chat_id, **options)
                         if chat_id is not None else await self._verify())
            except BaseException as error:
                outcome['error'] = error
                outcome['done'] = not isinstance(error, asyncio.CancelledError)
                raise
            else:
                outcome['value'], outcome['done'] = value, True
                return value

    child = self.task = asyncio.ensure_future(observed())

    async def stop():
        if not child.done():
            child.cancel()
        try:
            await child
        except (Exception, asyncio.CancelledError):
            pass

    terminal = None
    try:
        try:
            done, _ = await asyncio.wait((child,), timeout=self.policy.attempt_timeout)
        except asyncio.CancelledError:
            await _await_cleanup(stop())
            raise
        timed_out = not done
        if timed_out:
            await _await_cleanup(stop())
        # Reading child termination is deliberately outside the parent-cancel handler.
        try:
            child.result()
        except (Exception, asyncio.CancelledError) as error:
            terminal = error
    finally:
        self.task = None
    if outcome.get('done'):
        if 'error' in outcome:
            raise outcome['error']
        return outcome['value']
    if timed_out:
        error = PoolTimeoutError('The account source attempt timed out')
    elif isinstance(terminal, asyncio.CancelledError):
        error = _SourceInterrupted('Account source was interrupted; recover its unresolved attempt')
    elif terminal is not None:
        raise terminal
    else:
        error = _SourceInterrupted('Account source ended without an outcome; recover its unresolved attempt')
    error.partial_result = getattr(outcome.get('error'), 'partial_result', None)
    raise error from None


class CandidatePool(OriginalPool):
    def __init__(self, *args, **kwargs):
        if kwargs.get('health_callback') is not None:
            raise PoolConfigurationError('AccountPool does not run health callbacks; use drain_health_events()')
        self._observations = ObservationBuffer()
        super().__init__(*args, **kwargs)
        for source in self._sources.values():
            source.monitor = PoolMonitor(self._observations, source.account.label, source._identity)
            source.run = MethodType(source_run, source)

    @contextmanager
    def _operation(self):
        with super()._operation():
            with scope(self):
                yield

    async def _backend(self, method, *args):
        with scope(self):
            return await super()._backend(method, *args)

    async def _settle(self, expected, document, account_id, attempt_id, chat_id,
                      source_error=None, batch=None, recheck=False):
        if isinstance(source_error, _SourceInterrupted):
            # No transition: the real prior admission remains in SQLite.
            raise source_error
        return await super()._settle(expected, document, account_id, attempt_id, chat_id,
                                     source_error, batch, recheck)

    async def close(self):
        if refuses_close(self):
            raise PoolBusyError('Cannot close this pool from its live operation/provider scope')
        return await super().close()

    def drain_health_events(self):
        return self._observations.drain()


@contextmanager
def install(test_module):
    # Only the fixture's constructor is routed to the candidate. All real engines,
    # SDK requests, CAS/ledger implementations and source clients are retained.
    with patch.object(test_module, 'AccountPool', CandidatePool):
        yield
