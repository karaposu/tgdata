"""Private, opt-in bounded media ownership; the readers still own acceptance."""

import asyncio
from contextlib import asynccontextmanager, contextmanager
import contextvars
import logging
import math
import operator
import time

from telethon import errors, utils

from . import health
from .batch_heartbeat import _current as _heartbeat_current, _media_child_heartbeat

logger = logging.getLogger(__name__)
_SCOPE = contextvars.ContextVar('tgdata_media_scope', default=None)
_RESOURCES = contextvars.ContextVar('tgdata_media_resources', default=None)
_WAIT_ERRORS = (errors.FloodWaitError, errors.FloodPremiumWaitError,
                errors.SlowModeWaitError, errors.FloodTestPhoneWaitError)
_WAIT_SLICE = 10.0


def download_options(value):
    try:
        if isinstance(value, bool):
            raise TypeError
        number = operator.index(value)
        if not 1 <= number <= 16:
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        raise ValueError('download_concurrency must be an integer from 1 to 16') from None
    return {} if number == 1 else {'download_concurrency': int(number)}


@contextmanager
def media_boundary():
    token = _SCOPE.set(None)
    resources = _RESOURCES.set(None)
    try:
        yield
    finally:
        _RESOURCES.reset(resources)
        _SCOPE.reset(token)


def _current(client):
    scope = _SCOPE.get()
    return (scope if scope is not None and scope.active
            and scope.task is asyncio.current_task() and client in scope.clients else None)


def _warn(error):
    try:
        logger.warning('Media cleanup failed (%s)', type(error).__name__)
    except BaseException:
        pass


async def _settled(work):
    """Retain physical work through repeated cancellation of its waiter."""
    async def finish():
        try:
            return await work, None
        except (Exception, asyncio.CancelledError) as error:
            return None, error
    task = asyncio.ensure_future(finish())
    cancelled = None
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError as error:
            if cancelled is None:
                cancelled = error
    value, error = task.result()
    return value, error, cancelled


class _Control:
    def __init__(self):
        self.active = None
        self.deadline = 0.0
        self.error = None

    def observe(self, error):
        until = time.monotonic() + max(1, error.seconds)
        if until > self.deadline:
            self.deadline, self.error = until, error

    async def admit(self, scope, client, request):
        # A callback may have queued cancellation without yielding to the loop.
        # Observe it before a new request can reserve budget or reach the wire.
        await asyncio.sleep(0)
        while True:
            if scope.owner.failure is not None:
                raise scope.owner.failure
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                return
            if remaining > client.flood_sleep_threshold:
                kind = type(self.error) if isinstance(self.error, _WAIT_ERRORS) else errors.FloodWaitError
                raise kind(request=request, capture=max(1, math.ceil(remaining))) from None
            scope.owner.beat('flood-wait')
            await asyncio.sleep(min(_WAIT_SLICE, remaining))


class _SourceScope:
    def __init__(self, owner, client, worker=False):
        self.owner, self.client = owner, client
        self.worker = worker
        self.task = asyncio.current_task()
        self.clients = {client}
        self.active = True


class MediaRead:
    """One opted-in operation on an engine; finite windows of owned children."""
    def __init__(self, engine, count, beat=None):
        self.engine, self.count = engine, count
        self.beat = beat or (lambda phase: None)
        self.failure = None
        self.client = None
        self.control = None

    def __enter__(self):
        primary = getattr(self.engine, '_primary_client', None)
        if getattr(primary, '_tgdata_media_cleanup_failed', False):
            raise RuntimeError('Media cleanup failed; close and replace the client before another opt-in read') from None
        control = getattr(self.engine, '_tgdata_media_control', None)
        if control is None:
            control = self.engine._tgdata_media_control = _Control()
        if control.active is not None:
            raise RuntimeError('An opt-in media read is already active on this connection engine') from None
        control.active = self
        self.control = control
        return self

    def __exit__(self, *unused):
        self.control.active = None

    @contextmanager
    def bind(self, client):
        if getattr(client, '_tgdata_media_cleanup_failed', False):
            raise RuntimeError('Media cleanup failed; close and replace the client before another opt-in read') from None
        self.client, self.failure = client, None
        scope = _SourceScope(self, client)
        token = _SCOPE.set(scope)
        try:
            yield
        finally:
            scope.active = False
            _SCOPE.reset(token)
            self.client = None

    async def window(self, items, work, accept):
        if not items:
            return
        if len(items) > self.count:
            raise RuntimeError('media window exceeds its bound')
        await asyncio.sleep(0)  # A queued caller stop must not start new work.
        self.failure = None
        call = health._capture_media_call()
        observer = _heartbeat_current()
        client = self.client
        outcomes = [None] * len(items)

        async def run(index, item):
            scope = _SourceScope(self, client, worker=True)
            token = _SCOPE.set(scope)
            try:
                with health._media_child_call(call), _media_child_heartbeat(observer):
                    try:
                        value = await work(item)
                    except (Exception, asyncio.CancelledError) as error:
                        if self.failure is None:
                            self.failure = error
                        outcomes[index] = (None, error)
                    else:
                        outcomes[index] = (value, None)
            finally:
                scope.active = False
                _SCOPE.reset(token)

        tasks = [asyncio.ensure_future(run(i, item)) for i, item in enumerate(items)]
        primary = None
        try:
            pending = set(tasks)
            while pending:
                _, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                if self.failure is not None:
                    primary = self.failure
                    break
        except asyncio.CancelledError as error:
            primary = error
        finally:
            async def finish():
                if primary is not None:
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
            _, cleanup_error, cancelled = await _settled(finish())
            if cancelled is not None:
                primary = cancelled
            if cleanup_error is not None:
                if primary is None:
                    primary = cleanup_error
                else:
                    _warn(cleanup_error)
        if primary is None:
            for task, outcome in zip(tasks, outcomes):
                if task.cancelled():
                    primary = asyncio.CancelledError()
                    break
                if task.exception() is not None:
                    primary = task.exception()
                    break
                if outcome is None:
                    primary = RuntimeError('Media worker ended without an outcome')
                    break
        for outcome in outcomes:
            if outcome is None or outcome[1] is not None:
                break
            accept(outcome[0])
        if primary is not None:
            raise primary


class _Resources:
    def __init__(self, scope):
        self.scope = scope
        self.iterators, self.clients = [], []

    async def __aenter__(self):
        self.token = _RESOURCES.set(self)
        return self

    async def __aexit__(self, kind, primary, traceback):
        if primary is not None and self.scope.worker and self.scope.owner.failure is None:
            self.scope.owner.failure = primary
        async def close():
            failures = []
            for iterator in self.iterators:
                if getattr(iterator, '_sender', None) is not None:
                    try:
                        await iterator.close()
                    except (Exception, asyncio.CancelledError) as error:
                        failures.append(error)
            for client in self.clients:
                try:
                    await client.disconnect()
                except (Exception, asyncio.CancelledError) as error:
                    failures.append(error)
            return failures
        try:
            failures, failure, cancelled = await _settled(close())
            failures = failures or []
            if failure is not None:
                failures.append(failure)
            if failures:
                self.scope.client._tgdata_media_cleanup_failed = True
                for error in failures:
                    _warn(error)
                if primary is None and cancelled is None:
                    raise RuntimeError('Media resource cleanup failed') from None
            if cancelled is not None:
                raise cancelled
        finally:
            for client in self.clients:
                self.scope.clients.discard(client)
            _RESOURCES.reset(self.token)


class _MediaSender:
    def __init__(self, sender, scope, client):
        self.sender, self.scope, self.client = sender, scope, client

    def __getattr__(self, name):
        return getattr(self.sender, name)

    def send(self, request, ordered=False):
        if utils.is_list_like(request):
            return [self.send(item, ordered=ordered) for item in request]
        async def admitted():
            await self.scope.owner.control.admit(self.scope, self.client, request)
            try:
                # No await between gate admission and the existing sender seam.
                return await self.sender.send(request, ordered=ordered)
            except _WAIT_ERRORS as error:
                self.scope.owner.control.observe(error)
                raise
        return admitted()


class MediaClientMixin:
    async def _call(self, sender, request, ordered=False, flood_sleep_threshold=None):
        scope = _current(self)
        if scope is not None:
            for item in list(request) if utils.is_list_like(request) else [request]:
                due = self._flood_waited_requests.get(item.CONSTRUCTOR_ID)
                remaining = round(due - time.time()) if due is not None else 0
                if remaining > 3:
                    scope.owner.control.observe(errors.FloodWaitError(request=item, capture=remaining))
            await scope.owner.control.admit(scope, self, request)
            sender = _MediaSender(sender, scope, self)
        return await super()._call(sender, request, ordered=ordered,
                                   flood_sleep_threshold=flood_sleep_threshold)

    async def download_media(self, *args, **kwargs):
        scope = _current(self)
        if scope is None:
            return await super().download_media(*args, **kwargs)
        async with _Resources(scope):
            return await super().download_media(*args, **kwargs)

    async def download_profile_photo(self, *args, **kwargs):
        scope = _current(self)
        if scope is None:
            return await super().download_profile_photo(*args, **kwargs)
        async with _Resources(scope):
            return await super().download_profile_photo(*args, **kwargs)

    def _iter_download(self, *args, **kwargs):
        iterator = super()._iter_download(*args, **kwargs)
        resources = _RESOURCES.get()
        if resources is not None and _current(self) is resources.scope:
            native_close = iterator.close
            async def close_owned():
                # The SDK calls close internally at end-of-file too. Both call
                # sites obey the same retained/local cleanup boundary.
                _, error, cancelled = await _settled(native_close())
                if error is not None:
                    resources.scope.client._tgdata_media_cleanup_failed = True
                    _warn(error)
                if cancelled is not None:
                    raise cancelled
                if error is not None:
                    raise RuntimeError('Media resource cleanup failed') from None
            iterator.close = close_owned
            resources.iterators.append(iterator)
        return iterator

    async def _get_cdn_client(self, redirect):
        scope, resources = _current(self), _RESOURCES.get()
        if scope is None or resources is None or resources.scope is not scope:
            return await super()._get_cdn_client(redirect)
        # Telethon 1.45's helper factory, with ownership before connect and the
        # source's request policy on the NEW helper, never a shared mutation.
        session = self._exported_sessions.get(redirect.dc_id)
        if session is None:
            dc = await self._get_dc(redirect.dc_id, cdn=True)
            session = await utils.maybe_async(self.session.clone())
            await utils.maybe_async(session.set_dc(dc.id, dc.ip_address, dc.port))
            self._exported_sessions[redirect.dc_id] = session
        client = self.__class__(session, self.api_id, self.api_hash,
            proxy=self._proxy, timeout=self._timeout, loop=self.loop,
            request_retries=self._request_retries,
            flood_sleep_threshold=self.flood_sleep_threshold,
            raise_last_call_error=self._raise_last_call_error,
            connection_retries=self._connection_retries, retry_delay=self._retry_delay,
            auto_reconnect=self._auto_reconnect)
        resources.clients.append(client)
        scope.clients.add(client)
        session.auth_key = self._sender.auth_key
        await client._sender.connect(client._connection(session.server_address,
            session.port, session.dc_id, loggers=client._log, proxy=client._proxy,
            local_addr=client._local_addr))
        return client


async def download_named(client, message, directory, stem, beat):
    """Keep legacy names/reuse, but publish new opted-in files only on success."""
    import os
    from pathlib import Path
    import tempfile
    from .batch_files import _local_io, _owned_stream, _hash_stream, _publish
    root = Path(directory)
    extension = utils.get_extension(message.media) or ''
    target = root / (stem + extension)
    if extension and _local_io(target.exists):
        return str(target)
    raw = _local_io(tempfile.NamedTemporaryFile, mode='w+b', dir=str(root),
                    prefix='.tgdata-media-', delete=False)
    with _owned_stream(raw, raw.name) as output:
        result = await client.download_media(message, file=output,
            progress_callback=lambda current, total: beat('media'))
        if result is None:
            return None
        if result is not output or output.closed:
            raise RuntimeError('Media download did not complete its owned output') from None
        output.flush()
        _local_io(os.fsync, output.fileno())
        output.seek(0)
        digest, size = _hash_stream(output)
        output.close()
        _publish(raw.name, target, digest, size)
        return str(target)
