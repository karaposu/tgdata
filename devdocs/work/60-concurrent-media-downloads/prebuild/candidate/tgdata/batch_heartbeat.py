"""Private, observational batch liveness; no retries, tasks or receipt state."""

import asyncio
from contextlib import contextmanager
import contextvars
import inspect
import logging

from telethon import errors
from .message_batch import BatchFormatError

logger = logging.getLogger(__name__)
_SCOPE = contextvars.ContextVar('tgdata_batch_heartbeat', default=None)
def _sleep(seconds):
    return asyncio.sleep(seconds)

_WAIT_SLICE = 10.0
_FLOOD_ERRORS = (errors.FloodWaitError, errors.FloodPremiumWaitError,
                 errors.SlowModeWaitError, errors.FloodTestPhoneWaitError)


def heartbeat_kwargs(callback):
    """Omit None for compatibility with existing injected readers."""
    if callback is None:
        return {}
    if (not callable(callback) or inspect.iscoroutinefunction(callback)
            or inspect.isasyncgenfunction(callback)
            or inspect.iscoroutinefunction(getattr(type(callback), '__call__', None))
            or inspect.isasyncgenfunction(getattr(type(callback), '__call__', None))):
        raise BatchFormatError('heartbeat must be a synchronous callable or None')
    return {'heartbeat': callback}


def _warn(error):
    try:
        logger.warning('Batch heartbeat callback failed (%s)', type(error).__name__)
    except BaseException:
        pass


class _Observer:
    def __init__(self, callback):
        self.callback = callback
        self.owner = asyncio.current_task()
        self.active = True
        self.media_children = set()

    def __call__(self, phase):
        # Captured Future observers run outside a Task, but must stop on exit.
        if not self.active:
            return
        try:
            result = self.callback(phase)
            if inspect.isawaitable(result):
                if inspect.iscoroutine(result):
                    result.close()
                raise TypeError('heartbeat must return synchronously')
        except (Exception, asyncio.CancelledError) as error:
            _warn(error)


def _current():
    observer = _SCOPE.get()
    return (observer if observer is not None and observer.active
            and (observer.owner is asyncio.current_task()
                 or asyncio.current_task() in observer.media_children) else None)


@contextmanager
def _media_child_heartbeat(observer):
    task = asyncio.current_task()
    if observer is not None and not observer.active:
        observer = None
    token = _SCOPE.set(observer)
    if observer is not None:
        observer.media_children.add(task)
    try:
        yield
    finally:
        if observer is not None:
            observer.media_children.discard(task)
        _SCOPE.reset(token)


@contextmanager
def heartbeat_scope(callback):
    heartbeat_kwargs(callback)
    observer = _Observer(callback) if callback is not None else None
    token = _SCOPE.set(observer)  # None masks any enclosing operation as well.
    try:
        yield observer
    finally:
        if observer is not None:
            observer.active = False
            observer.callback = observer.owner = None
        _SCOPE.reset(token)


def _answered(observer, error=None):
    observer('flood-wait' if isinstance(error, _FLOOD_ERRORS) else
             'request-error' if error is not None else 'request done')


class _ObservedSender:
    def __init__(self, sender, observer):
        self.sender, self.observer = sender, observer

    def __getattr__(self, name):
        return getattr(self.sender, name)

    def _observe(self, pending):
        observer = self.observer
        if asyncio.isfuture(pending):
            def done(future):
                if not future.cancelled():
                    _answered(observer, future.exception())
            pending.add_done_callback(done)
            return pending  # Do not move enqueue or replace Future ownership.
        async def observed():
            try:
                value = await pending  # Budget admission stays in the SDK task.
            except asyncio.CancelledError:
                raise
            except Exception as error:
                _answered(observer, error)
                raise
            else:
                _answered(observer)
                return value
        return observed()

    def send(self, request, ordered=False):
        # Synchronous enqueue happens at exactly the original SDK call site.
        pending = self.sender.send(request, ordered=ordered)
        if isinstance(pending, list):
            return [self._observe(item) for item in pending]
        return self._observe(pending)


class BatchHeartbeatMixin:
    async def _call(self, sender, request, ordered=False, flood_sleep_threshold=None):
        observer = _current()
        if observer is not None:
            observer('request')
            sender = _ObservedSender(sender, observer)
        return await super()._call(sender, request, ordered=ordered,
                                   flood_sleep_threshold=flood_sleep_threshold)


async def heartbeat_sleep(seconds):
    """Only for waits tgdata already chose; never wrap an unanswered request."""
    observer = _current()
    if observer is None:
        return await _sleep(seconds)
    if seconds <= 0:
        observer('flood-wait')
        await _sleep(seconds)
        observer('flood-wait done')
        return
    loop = asyncio.get_running_loop()
    deadline = loop.time() + seconds
    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            break
        observer('flood-wait')
        await _sleep(min(_WAIT_SLICE, remaining))
    observer('flood-wait done')
