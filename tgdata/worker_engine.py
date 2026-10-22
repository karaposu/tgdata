"""Explicit-account worker jobs over the accepted temporary-operation APIs."""

import asyncio
from contextlib import asynccontextmanager
import contextvars
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from uuid import uuid4

import telethon
from telethon import utils

from .batch_engine import BatchEngine
from .group_operations import _parse_target, _resolve, GroupReferenceError, GroupResponseError
from .join_budget import JoinBudget
from .message_batch import MessageBatch, MAX_LONG
from .read_budget import ReadBudget
from .tgdata import TgData
from . import worker_protocol as wire


_CURRENT_JOB = contextvars.ContextVar('tgdata_worker_job', default=None)


def _media_root(value):
    """Pin trusted configuration without creating output for reference-only jobs."""
    if value is None:
        return None
    try:
        text = os.fspath(value)
        if (type(text) is not str or not text or '\x00' in text
                or text == ':memory:' or text.lower().startswith('file:')):
            raise ValueError
        root = Path(text).expanduser().resolve()
        if root.exists() and not root.is_dir():
            raise ValueError
        return root
    except (TypeError, ValueError, OSError, RuntimeError):
        raise wire.WorkerError('invalid_config', field='media_directory') from None


@dataclass(frozen=True)
class WorkerAccount:
    account_id: int
    config_path: str = field(repr=False)
    session_store: object = field(default=None, repr=False, compare=False)
    label: str = None

    def __post_init__(self):
        if type(self.account_id) is not int or not 1 <= self.account_id <= MAX_LONG:
            raise wire.WorkerError('invalid_config', field='account_id')
        try:
            path = os.fspath(self.config_path)
            if type(path) is not str or not path:
                raise ValueError
            resolved = Path(path).expanduser().resolve()
            if not resolved.is_file():
                raise ValueError
        except (ValueError, TypeError, OSError, RuntimeError):
            raise wire.WorkerError('invalid_config', field='config_path') from None
        if self.label is not None:
            if type(self.label) is not str or len(self.label) > 128:
                raise wire.WorkerError('invalid_config', field='label')
            try:
                self.label.encode('utf-8')
            except UnicodeError:
                raise wire.WorkerError('invalid_config', field='label') from None
        if self.session_store is not None and not all(
                callable(getattr(self.session_store, name, None)) for name in ('load', 'save')):
            raise wire.WorkerError('invalid_config', field='session_store')
        object.__setattr__(self, 'config_path', str(resolved))


class _Collector:
    def __init__(self, owner):
        self.owner, self.events, self.dropped = owner, [], 0

    def append(self, event):
        if len(self.events) < wire.MAX_HEALTH_EVENTS:
            converted = wire.health_event(event)
            wire.encode_frame(converted, maximum=min(wire.MAX_HEALTH_EVENT_BYTES,
                                                    wire.MAX_RESPONSE_BYTES - 2048))
            self.events.append(converted)
        else:
            self.dropped += 1


class _BoundSession:
    def __init__(self, operation):
        self.operation = operation

    @asynccontextmanager
    async def session(self):
        yield self.operation.client


class Worker:
    """One dedicated process's explicit account inventory and serial executor.

    Construct with existing policies; the worker never logs in or configures an
    allowance. Use worker.serve as the process entry point. Sessions must be
    exclusively assigned for the lifetime of that process.
    """

    def __init__(self, accounts, *, worker_id, read_budget, join_budget=None,
                 media_directory=None):
        if telethon.__version__ != '1.45.0':
            raise wire.WorkerError('unsupported_sdk')
        if type(worker_id) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', worker_id):
            raise wire.WorkerError('invalid_config', field='worker_id')
        if not isinstance(read_budget, ReadBudget):
            raise wire.WorkerError('invalid_config', field='read_budget')
        if join_budget is not None and not isinstance(join_budget, JoinBudget):
            raise wire.WorkerError('invalid_config', field='join_budget')
        self._media_directory = _media_root(media_directory)
        try:
            accounts = tuple(accounts)
        except TypeError:
            raise wire.WorkerError('invalid_config', field='accounts') from None
        if len(accounts) > wire.MAX_ACCOUNTS or any(not isinstance(a, WorkerAccount) for a in accounts):
            raise wire.WorkerError('invalid_config', field='accounts')
        if (len({a.account_id for a in accounts}) != len(accounts)
                or len({a.config_path for a in accounts}) != len(accounts)):
            raise wire.WorkerError('invalid_config', field='accounts')
        self.worker_id, self.instance_id = worker_id, uuid4().hex
        self.accounts, self.read_budget, self.join_budget = accounts, read_budget, join_budget
        self.stopping = self._busy = False
        self._apps = {}
        addresses = set()
        for account in accounts:
            read_budget.status(account.account_id)  # Missing policy never means unlimited.
            app = TgData(account.config_path, connection_pool_size=1, interactive_login=False,
                         session_store=account.session_store, read_budget=read_budget,
                         join_budget=join_budget, health_callback=self._capture,
                         account_label=account.label)
            config = app.connection_engine._load_config()
            if account.session_store is None:
                name = str(Path(config.session_file).expanduser().resolve())
                config.session_file = name  # Pin the same library-relative file once.
                filename = name if name.endswith('.session') else name + '.session'
                address = ('file', str(Path(filename).resolve()))
            else:
                address = ('store', id(account.session_store), config.session_file)
            if address in addresses:
                raise wire.WorkerError('invalid_config', field='session')
            addresses.add(address)
            self._apps[account.account_id] = app

    def _capture(self, event):
        collector = _CURRENT_JOB.get()
        if collector is not None and collector.owner is self:
            try:
                collector.append(event)
            except BaseException:
                collector.dropped += 1  # Observation cannot replace the source result.

    def ready(self):
        return dict(version=wire.VERSION, kind='ready', worker_id=self.worker_id,
                    instance_id=self.instance_id, state='idle',
                    account_ids=[str(a.account_id) for a in self.accounts],
                    account_count=len(self.accounts),
                    limits=dict(request_bytes=wire.MAX_REQUEST_BYTES, response_bytes=wire.MAX_RESPONSE_BYTES,
                                read_messages=wire.MAX_READ_MESSAGES, request_id=wire.MAX_REQUEST_ID,
                                health_events=wire.MAX_HEALTH_EVENTS,
                                health_event_bytes=wire.MAX_HEALTH_EVENT_BYTES))

    def _base(self, job=None, error=None):
        ident = job.request_id if job is not None else getattr(error, 'request_id', None)
        account = job.account_id if job is not None else getattr(error, 'account_id', None)
        operation = job.operation if job is not None else getattr(error, 'operation', None)
        return dict(version=wire.VERSION, worker_id=self.worker_id, instance_id=self.instance_id,
                    request_id=ident, account_id=str(account) if account is not None else None,
                    operation=operation)

    def refusal(self, error, job=None):
        frame = self._base(job, error)
        frame.update(kind='result', ok=False, data=None, error=wire.describe_error(error),
                     partial_result=None, health_dropped=0,
                     worker_stopping=self.stopping or bool(getattr(error, 'fatal', False)))
        return frame

    async def _read(self, app, job, options):
        if options.pop('download_media', False):
            if self._media_directory is None:
                raise wire.WorkerError('media_disabled')
            options['download_media_to'] = self._media_directory
        target = _parse_target(options.pop('group_id'))
        async with app._account_health_operation(
                job.account_id, 'worker_read_batch', target.label) as (operation, observation):
            async def resolver(client, unused):
                if client is not operation.client:
                    raise RuntimeError('Worker source ownership changed')
                lookup, peer = await _resolve(operation, target)
                if peer is None or lookup.group.kind == 'community':
                    raise GroupReferenceError('No supported read peer')
                entity = await client.get_entity(peer)
                if utils.get_peer_id(entity) != lookup.group.peer_id:
                    raise GroupResponseError()
                return entity
            engine = BatchEngine(_BoundSession(operation), _resolve_entity=resolver)
            # BatchEngine's argument is only the original supported target; its
            # resolver receives the already parsed, bounded reference above.
            batch = await engine.fetch_batch(job.options()['group_id'], **options)
            if 'messages.GetHistoryRequest' in observation.requests:
                observation.confirm_group_access()
            return batch

    async def _perform(self, app, job):
        options = job.options()
        if job.operation == 'read_batch':
            return await self._read(app, job, options)
        if job.operation == 'lookup_group':
            return await app.lookup_group(options['target'], account_id=job.account_id)
        if job.operation == 'check_group_access':
            return await app.check_group_access(options['target'], account_id=job.account_id)
        if job.operation == 'join_group':
            if self.join_budget is None:
                raise wire.WorkerError('join_disabled')
            return await app.join_group(options['target'], account_id=job.account_id)
        raise wire.WorkerError('unknown_operation')

    def _frames(self, job, value, error, collector):
        result = self._base(job)
        result.update(kind='result', ok=error is None,
            data=(value.to_dict() if isinstance(value, MessageBatch) else wire.identifiers(value.to_dict()))
                 if error is None else None,
            error=wire.describe_error(error) if error is not None else None,
            partial_result=wire.partial_batch(error) if error is not None else None,
            health_dropped=collector.dropped, worker_stopping=self.stopping)
        frames = []
        for event in collector.events:
            frame = self._base(job)
            frame.update(kind='health', event=event)
            frames.append(frame)
        frames.append(result)
        # Check all frames before publishing any. This is bounded by one job,
        # not a queue of jobs or a durable result store.
        encoded = [wire.encode_frame(frame) for frame in frames]
        return encoded

    def _delivery_failure(self, job, value, error, dropped):
        self.stopping = True
        frame = self.refusal(wire.WorkerError('delivery_failed', fatal=True), job)
        frame.update(source_outcome='raised' if error is not None else 'returned',
                     source_error=wire.describe_error(error) if error is not None else None,
                     source_result_type=type(value).__name__ if value is not None else None,
                     partial_omitted=True, health_dropped=dropped)
        status = getattr(value, 'status', None)
        if status in ('readable', 'denied', 'unprobed', 'joined', 'already_joined',
                      'requested', 'payment_required', 'interaction_required'):
            frame['source_status'] = status
        return [wire.encode_frame(frame)]

    async def execute(self, job):
        if self.stopping:
            raise wire.WorkerError('worker_stopping', fatal=True)
        if self._busy:
            raise wire.WorkerError('worker_busy')
        if not isinstance(job, wire.Job):
            raise wire.WorkerError('invalid_parameters')
        self._busy = True
        collector = _Collector(self)
        token = _CURRENT_JOB.set(collector)
        app = self._apps.get(job.account_id)
        value = error = None
        try:
            try:
                if app is None:
                    raise wire.WorkerError('unknown_account')
                value = await self._perform(app, job)
            except asyncio.CancelledError:
                self.stopping = True
                raise
            except Exception as caught:
                error = caught
            finally:
                if app is not None and app.connection_engine._account_cleanup_failure is not None:
                    self.stopping = True
            if app is not None:
                deliveries = [task for monitor in app._account_health.values()
                              for task in monitor._tasks if task is not asyncio.current_task()]
                if deliveries:
                    await asyncio.gather(*deliveries, return_exceptions=True)
            try:
                return self._frames(job, value, error, collector)
            except Exception:
                return self._delivery_failure(job, value, error,
                                              collector.dropped + len(collector.events))
        except BaseException:
            self.stopping = True
            raise
        finally:
            _CURRENT_JOB.reset(token)
            self._busy = False

    async def close(self):
        if self._busy:
            raise wire.WorkerError('worker_busy')
        self.stopping = True
        for app in self._apps.values():
            await app.close()
