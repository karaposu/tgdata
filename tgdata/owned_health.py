"""Private, fixed-owner observations for verified account operations.

Reuses the health ledger and event format, but not legacy ambient attribution,
recovery evidence or inline callback timing. No credentials or clients are kept
in notifications. Future group code must explicitly assert proven access.
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
import inspect

from telethon.errors import MultiError, RPCError
from telethon.tl import functions
from telethon.tl.tlobject import TLRequest

from . import health


_ENVELOPES = (
    functions.InvokeAfterMsgRequest, functions.InvokeAfterMsgsRequest,
    functions.InitConnectionRequest, functions.InvokeWithLayerRequest,
    functions.InvokeWithoutUpdatesRequest, functions.InvokeWithMessagesRangeRequest,
    functions.InvokeWithTakeoutRequest,
)


def _request_key(request):
    """One namespaced action key; never keep arguments or guess through .query."""
    seen = set()
    try:
        for depth in range(9):
            if not isinstance(request, TLRequest) or id(request) in seen:
                return None
            seen.add(id(request))
            if isinstance(request, _ENVELOPES):
                if depth == 8:
                    return None
                request = request.query
                continue
            cls = type(request)
            namespace = cls.__module__
            prefix = 'telethon.tl.functions'
            if namespace == prefix:
                return cls.__name__
            if namespace.startswith(prefix + '.'):
                namespace = namespace[len(prefix) + 1:]
            return namespace + '.' + cls.__name__
    except (Exception, asyncio.CancelledError):  # Metadata cannot change the RPC outcome.
        return None
    return None


class _OwnedCall(health._Call):
    accepts_ambient_reports = False

    def __init__(self, monitor, operation, method, group, started):
        super().__init__(monitor, method, group)
        self.operation = operation
        self.client = operation.client
        self.started = started
        self.requests = set()
        self.group_confirmed = False
        self.events = []
        self.notify = not health._DELIVERING.get()

    def valid(self):
        if not self.owns_current_task():
            return False
        try:
            return self.operation.client is self.client
        except RuntimeError:  # A caught auth/identity failure invalidates the handle.
            return False

    def capture_request_evidence(self, client, request):
        if client is not self.client or not self.valid():
            return None
        if type(request) in (list, tuple, set, dict):
            requests = request
        elif isinstance(request, TLRequest):
            requests = (request,)
        else:
            requests = ()  # Do not consume custom/lazy input for observer evidence.
        keys = frozenset(key for key in map(_request_key, requests) if key is not None)
        return self, client, keys

    def note_answer(self, client=None, request=None, evidence=None):
        if client is not self.client or not self.valid() or evidence is None:
            return
        call, source, keys = evidence
        if call is self and source is client:
            self.requests.update(keys)

    def note_rpc_error(self, client, exc):
        if client is not self.client or not self.valid():
            return
        errors = exc.exceptions if isinstance(exc, MultiError) else (exc,)
        for error in errors:
            if not isinstance(error, RPCError):
                continue
            # A raw RPCError is classified itself, never an arbitrary local cause.
            finding = health.classify(error)
            if finding is None:
                continue
            finding = replace(finding, request=_request_key(getattr(error, 'request', None)))
            health._mark(error, finding)
            event = self.monitor._record(finding, self, 'rpc')
            if finding.verdict == health.WAITING and finding.request:
                self.monitor._waiting_tick[finding.request] = next(health._TICKS)
                self.note_reported(('request', finding.request))
            self.events.append(event)

    def confirm_group_access(self):
        """Assert that a successful owned result proved access to this group.

        Internal semantic contract: the caller must interpret a real group result,
        never self/metadata alone. Stage 2 cannot infer Telegram permissions from
        a request name. It only enforces lifetime and successful source evidence.
        """
        if not self.valid() or self.group is None or not self.requests:
            raise RuntimeError('Group access requires successful work in the owned operation')
        self.group_confirmed = True


class _OwnedHealthMonitor(health.HealthMonitor):
    def __init__(self, account_id, session, callback=None, label=None):
        super().__init__(callback, label)
        self._owner = (session, account_id)
        self._waiting_tick = {}
        self._restricted_request = None

    def _who(self):
        return self._owner

    def _record(self, finding, call, source, group=None):
        event = super()._record(finding, call, source, group)
        if finding.verdict in (health.LOGGED_OUT, health.BANNED, health.RESTRICTED):
            self._restricted_request = finding.request if finding.verdict == health.RESTRICTED else None
        return event

    @asynccontextmanager
    async def observe(self, operation, method, group, started):
        call = _OwnedCall(self, operation, method, group, started)
        token = health._CURRENT.set(call)
        try:
            yield call
        except BaseException:
            call.failed = True
            raise
        else:
            if not call.failed and call.valid():
                await self._safely(self._recover, call)
        finally:
            call.active = False
            health._CURRENT.reset(token)

    async def _recover(self, call):
        def older(tick, scope):
            return 0 < tick < call.started and scope not in call.reported

        for request in sorted(call.requests):
            if older(self._waiting_tick.get(request, 0), ('request', request)):
                self._waiting.pop(request, None)
                self._waiting_until.pop(request, None)
                self._waiting_tick.pop(request, None)
                call.events.append(self._event(health.OK, 'request', None, call, request,
                                               None, None, 'recovery', health._iso()))
        if older(self._account_tick, ('account',)) and (
                self._account in (health.LOGGED_OUT, health.BANNED)
                or (self._account == health.RESTRICTED and self._restricted_request in call.requests
                    and self._restricted_by == call.method)):
            self._account, self._account_since, self._account_error = health.OK, None, None
            self._account_tick, self._restricted_by = 0, None
            self._restricted_request = None
            call.events.append(self._event(health.OK, 'account', None, call, None,
                                           None, None, 'recovery', health._iso()))
        key = str(call.group)
        if call.group_confirmed and older(self._no_access_tick.get(key, 0), ('group', key)):
            self._no_access.pop(key, None)
            self._no_access_tick.pop(key, None)
            call.events.append(self._event(health.OK, 'group', call.group, call, None,
                                           None, None, 'recovery', health._iso()))

    def dispatch(self, call):
        """Called only after source cleanup. The task receives plain data only."""
        if not call.events:
            return
        pending = self._notify(call.events, call.notify)
        try:
            task = asyncio.create_task(pending)
            self._tasks.add(task)
            task.add_done_callback(self._task_done)
        except Exception:  # noqa: BLE001
            pending.close()
            self._health_failed()

    async def _notify(self, events, notify):
        source = health._CURRENT.set(None)
        token = health._DELIVERING.set(True)
        try:
            for event in events:
                self._log(event)
                if not notify or self.callback is None:
                    continue
                try:
                    result = self.callback(event)
                    if inspect.isawaitable(result):
                        await result
                except asyncio.CancelledError as exc:
                    self._callback_failed(exc)
                    return
                except Exception as exc:  # noqa: BLE001
                    self._callback_failed(exc)
        finally:
            health._DELIVERING.reset(token)
            health._CURRENT.reset(source)

    def _callback_failed(self, exc=None):
        try:
            super()._callback_failed(exc)
        except Exception:  # noqa: BLE001 — even a broken logging handler is secondary
            pass

    def _health_failed(self):
        try:
            super()._health_failed()
        except Exception:  # noqa: BLE001
            pass


async def _retire_notifications(monitors):
    """Cooperatively retire existing deliveries; a callback never awaits itself."""
    current = asyncio.current_task()
    tasks = {task for monitor in monitors for task in monitor._tasks
             if task is not current and not task.done()}
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
