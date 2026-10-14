"""Private pool task outcomes and I/O-only provider boundaries."""

import asyncio
from contextlib import contextmanager
import contextvars

from .pool_state import PoolConfigurationError

_SCOPES = contextvars.ContextVar('tgdata_pool_scopes', default=())


@contextmanager
def _scope(pool):
    item = {'pool': pool, 'active': True}
    token = _SCOPES.set(tuple(s for s in _SCOPES.get() if s['active']) + (item,))
    try:
        yield
    finally:
        item['active'], item['pool'] = False, None
        _SCOPES.reset(token)


def _inside(pool):
    return any(s['active'] and s['pool'] is pool for s in _SCOPES.get())


async def _await_cleanup(work):
    """Retain cleanup; cancellation of its waiter never cancels physical work."""
    async def finish():
        try:
            return await work, None
        except (Exception, asyncio.CancelledError) as error:
            return None, error

    completion = asyncio.ensure_future(finish())
    cancelled = None
    while not completion.done():
        try:
            await asyncio.shield(completion)
        except asyncio.CancelledError as error:
            cancelled = error
    value, error = completion.result()
    if cancelled is not None:
        raise cancelled
    if error is not None:
        raise error
    return value


def _start_owned(call):
    """Capture component termination as data, including its own cancellation.

    Callers checkpoint before this synchronous start, then immediately wait_owned.
    Invocation itself belongs to the child, not to the public caller.
    """
    async def finish():
        try:
            return await call(), None
        except (Exception, asyncio.CancelledError) as error:
            return None, error
    return asyncio.ensure_future(finish())


async def _wait_owned(child, timeout=None):
    """Caller stop cancels once and joins; component interruption is returned."""
    async def stop():
        if not child.done():
            child.cancel()
        try:
            await child
        except (Exception, asyncio.CancelledError):
            pass

    try:
        done, _ = await asyncio.wait((child,), timeout=timeout)
        timed_out = not done
        if timed_out:
            await _await_cleanup(stop())
    except asyncio.CancelledError:
        await _await_cleanup(stop())
        raise
    # Outside the caller-cancellation handler, with no intervening await.
    try:
        value, error = child.result()
    except asyncio.CancelledError as error:
        # The child may have been cancelled before its capture body ever ran.
        return None, error, timed_out
    return value, error, timed_out


async def _call_store(pool, store, method, args, error_type, label):
    with _scope(pool):
        await asyncio.sleep(0)  # A queued caller stop must not start new I/O.
        async def invoke():
            return await getattr(store, method)(*args)
        value, error, _ = await _wait_owned(_start_owned(invoke))
        if isinstance(error, asyncio.CancelledError):
            raise error_type('{} store {} failed (CancelledError); outcome may be unknown'.format(
                label, method)) from None
        if error is not None:
            raise error
        return value


class _StoreBoundary:
    """Pool-only wrapper. State-only callers own their I/O even after pool close."""
    def __init__(self, pool, store, error_type, label):
        try:
            valid = (callable(getattr(store, 'load', None))
                     and callable(getattr(store, 'compare_and_swap', None)))
        except (Exception, asyncio.CancelledError):
            valid = False
        if not valid:
            raise PoolConfigurationError('{} store requires async load and compare_and_swap'.format(label)) from None
        self.pool, self.store = pool, store
        self.error_type, self.label = error_type, label

    async def load(self, *args):
        return await _call_store(self.pool, self.store, 'load', args, self.error_type, self.label)

    async def compare_and_swap(self, *args):
        return await _call_store(self.pool, self.store, 'compare_and_swap', args, self.error_type, self.label)


class _Invocation:
    """Completion of one library-owned span, not its containing caller Task."""
    def __init__(self):
        self.caller = asyncio.current_task()
        self.done = asyncio.get_running_loop().create_future()

    def stop(self, active):
        if active is self and not self.done.done() and self.caller is not None:
            self.caller.cancel()

    def finish(self):
        self.caller = None
        self.done.set_result(None)
