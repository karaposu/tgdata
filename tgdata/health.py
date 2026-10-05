"""
Account health events (issue #4).

Every time Telegram says no to an account — a wait, a logout, a ban, a
restriction, no access to a group — tgdata reports it: which verdict, about
what (the account, one kind of request, or one group), from which call, for how
long, and when it ended. It reports and never acts.

  classify()       Telegram's own error name -> verdict. Follows tgdata's
                   wrappers through the cause chain; never guesses from a
                   category.
  HealthMonitor    one per TgData: the ledger, "ok" on Telegram's evidence that
                   a condition ended, exception-safe delivery to the callback
                   (never back into a callback for its own calls' events), a
                   log line per event, a snapshot.
  call context     which public call — and which task — a report belongs to.
  report()         one line at every engine site that handles or swallows an
                   error.
  note_answer()    called by tgdata's client class for every request Telegram
                   answers: the evidence recovery needs.
  sleep capture    a filter on Telethon's own logger turns the waits it sleeps
                   through silently into events, without changing what anyone's
                   logging prints.

This module imports only the standard library and Telethon, so the engines and
the facade can all import it without a cycle. Nothing here may raise into the
code it observes.
"""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import inspect
import itertools
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from telethon import errors as tl_errors
from telethon.errors import RPCError, rpcerrorlist

logger = logging.getLogger(__name__)
_mirror = logging.getLogger('tgdata.tgdata.health')     # under the logger log_file= writes to

# ── vocabulary ──────────────────────────────────────────────────────────────

OK = 'ok'
WAITING = 'waiting'
LOGGED_OUT = 'logged out'
BANNED = 'banned'
RESTRICTED = 'restricted'
NO_ACCESS = 'no access'
UNCLASSIFIED = 'unclassified'

TERMINAL = frozenset({LOGGED_OUT, BANNED, RESTRICTED, NO_ACCESS})   # retrying cannot fix these
_LOUD = frozenset({LOGGED_OUT, BANNED, RESTRICTED, UNCLASSIFIED})    # WARNING in the log mirror

# Every wait Telethon's own sleep branch handles (UserMethods._call). getattr:
# FloodPremiumWaitError is newer than the oldest supported Telethon (1.33).
WAIT_ERRORS = tuple(c for c in (tl_errors.FloodWaitError,
                                getattr(tl_errors, 'FloodPremiumWaitError', None),
                                getattr(tl_errors, 'SlowModeWaitError', None),
                                getattr(tl_errors, 'FloodTestPhoneWaitError', None))
                    if c is not None)

# Telegram's own error name -> (verdict, scope). Verdicts come only from here,
# never from an error's category: on Telethon 1.45 the 401 and 406 families
# also hold errors that are not logouts.
_TABLE: Dict[str, Tuple[str, str]] = {}
for _name in ('AUTH_KEY_UNREGISTERED', 'SESSION_REVOKED', 'SESSION_EXPIRED', 'AUTH_KEY_INVALID',
              'AUTH_KEY_DUPLICATED'):
    _TABLE[_name] = (LOGGED_OUT, 'account')
for _name in ('USER_DEACTIVATED_BAN', 'USER_DEACTIVATED', 'PHONE_NUMBER_BANNED'):
    _TABLE[_name] = (BANNED, 'account')
for _name in ('FROZEN_METHOD_INVALID', 'FROZEN_PARTICIPANT_MISSING', 'USER_RESTRICTED', 'PEER_FLOOD'):
    _TABLE[_name] = (RESTRICTED, 'account')          # by documentation; frozen reads are unobserved
for _name in ('CHANNEL_PRIVATE', 'CHAT_FORBIDDEN', 'CHANNEL_INVALID', 'USER_BANNED_IN_CHANNEL',
              'CHANNEL_PUBLIC_GROUP_NA', 'CHANNEL_BANNED'):
    _TABLE[_name] = (NO_ACCESS, 'group')

# An unlisted error in these categories is reported as "unclassified", so the
# table can grow from evidence. 400s (bad input) and 5xx (server) never are.
_UNCLASSIFIED_CODES = frozenset({401, 403, 406, 420})

# tgdata's own exceptions that carry a verdict (registered by their modules)
_REGISTERED: Dict[type, Tuple[str, str]] = {}


def _wire_names() -> Dict[type, str]:
    names = {cls: name for name, cls in getattr(rpcerrorlist, 'rpc_errors_dict', {}).items()}
    for pattern, cls in getattr(rpcerrorlist, 'rpc_errors_re', ()):
        text = getattr(pattern, 'pattern', pattern)
        names.setdefault(cls, re.sub(r'\(\\d\+\)', 'X', str(text)))    # FLOOD_WAIT_(\d+) -> FLOOD_WAIT_X
    return names


_TELEGRAM_NAMES = _wire_names()
_REPORTED = '_tgdata_health_reported'


def register(exc_class: type, verdict: str, scope: str) -> None:
    """Give one of tgdata's own exception classes a verdict."""
    _REGISTERED[exc_class] = (verdict, scope)


def telegram_error_name(error: BaseException) -> str:
    """Telegram's own name for an error: from Telethon's tables for a class it
    knows, else the raw name Telethon keeps in .message for one it does not."""
    return _TELEGRAM_NAMES.get(type(error)) or getattr(error, 'message', None) or type(error).__name__


_TME = re.compile(r'^(?:https?://)?(?:t\.me|telegram\.me)/(?:s/|boost/)?(?!joinchat/)'
                  r'([A-Za-z][A-Za-z0-9_]{3,31})(?![A-Za-z0-9_])', re.I)


def normalise_group(value: Any):
    """The group as the caller named it: an int stays an int; a string of
    digits becomes an int; '@name' or a t.me link becomes the lowercase
    username, and any other string is lowercased; an entity becomes its id;
    anything else (a list included) None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r'-?\d+', text):
            return int(text)
        match = _TME.match(text)
        if match:
            return match.group(1).lower()
        return text.lstrip('@').lower() or None
    ident = getattr(value, 'id', None)
    return ident if isinstance(ident, int) and not isinstance(ident, bool) else None


# ── classification ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Finding:
    verdict: str
    scope: Optional[str]
    error: Optional[str]
    wait_seconds: Optional[int]
    request: Optional[str]
    source_exc: Optional[BaseException] = field(default=None, compare=False, repr=False)


def _chain(exc: BaseException):
    seen = set()
    current: Optional[BaseException] = exc
    while current is not None and id(current) not in seen and len(seen) < 10:
        yield current
        seen.add(id(current))
        if current.__cause__ is not None:
            current = current.__cause__
        elif current.__suppress_context__:
            current = None
        else:
            current = current.__context__


def _request_name(error: BaseException) -> Optional[str]:
    request = getattr(error, 'request', None)
    return type(request).__name__ if request is not None else None


def _file_reference(name: str) -> bool:
    return name.startswith('FILE_REFERENCE_') or name == 'FILEREF_UPGRADE_NEEDED'


def classify(exc: BaseException, include_reported: bool = False) -> Optional[Finding]:
    """The health verdict an exception carries, if any.

    Walks the exception and its cause chain (tgdata wraps Telegram's errors in
    RuntimeError, ConnectionError, AuthRequiredError, DiscoveryInterrupted).
    Returns None for anything that is not a health signal — a 400 or 5xx,
    a transport or configuration error, a never-logged-in session — and, unless
    include_reported, for an exception already reported once."""
    for error in _chain(exc):
        if not include_reported and getattr(error, _REPORTED, False):
            return None
        if getattr(error, 'first_login', False) is True:      # configuration, not a verdict
            return None
        reason = getattr(error, 'reason', None)               # AuthRequiredError: Telegram's name
        if hasattr(error, 'banned') and isinstance(reason, str) and _TABLE.get(reason, ('', ''))[1] == 'account':
            return Finding(_TABLE[reason][0], 'account', reason, None, None, error)
        for cls, (verdict, scope) in _REGISTERED.items():
            if isinstance(error, cls):
                return Finding(verdict, scope, type(error).__name__, None, None, error)
        if WAIT_ERRORS and isinstance(error, WAIT_ERRORS):
            seconds = getattr(error, 'seconds', None)
            return Finding(WAITING, 'request', telegram_error_name(error),
                           int(seconds) if seconds is not None else None, _request_name(error), error)
        if isinstance(error, RPCError):
            name = telegram_error_name(error)
            hit = _TABLE.get(name)
            if hit:
                return Finding(hit[0], hit[1], name, None, _request_name(error), error)
            if getattr(error, 'code', None) in _UNCLASSIFIED_CODES and not _file_reference(name):
                return Finding(UNCLASSIFIED, None, name, None, _request_name(error), error)
            return None                                       # an ordinary Telegram error
    return None


def _mark(exc: BaseException, finding: Finding) -> None:
    for error in (exc, finding.source_exc):
        if error is not None:
            try:
                setattr(error, _REPORTED, True)
            except Exception:  # noqa: BLE001 — an exception that refuses attributes stays unmarked
                pass


# ── the call context ────────────────────────────────────────────────────────

_CURRENT: contextvars.ContextVar = contextvars.ContextVar('tgdata_health_call', default=None)
_UNSET_ACCOUNT = object()
# Set while the health callback runs: events from tgdata calls the callback
# makes are recorded and logged, never delivered back to it (no re-entry).
_DELIVERING: contextvars.ContextVar = contextvars.ContextVar('tgdata_health_delivering', default=False)
# One order for verdicts and Telegram's answers: an answer recovers a verdict
# only when it came after it.
_TICKS = itertools.count(1)


def _current_task():
    try:
        return asyncio.current_task()
    except RuntimeError:
        return None


class _Call:
    """One public TgData call in progress. Tasks created during the call
    inherit it through the context variable, so a report is attributed to the
    call only from the call's own task while the call is active (owner task)."""
    __slots__ = ('monitor', 'method', 'group', 'task', 'parent', 'active', 'failed', 'waited', 'reported',
                 'answered', 'recover_group', 'account_id')

    def __init__(self, monitor: 'HealthMonitor', method: str, group):
        self.monitor = monitor
        self.method = method
        self.group = group
        self.recover_group = True
        self.account_id = _UNSET_ACCOUNT
        self.task = _current_task()
        self.parent: Optional[_Call] = _CURRENT.get()     # a public call made inside another one
        self.active = True
        self.failed = False
        self.waited: set = set()       # request types slept or handled during the call
        self.reported: set = set()     # account / group scopes reported during the call
        self.answered = 0              # tick of the last request Telegram answered for this call

    def owns_current_task(self) -> bool:
        return self.active and self.task is not None and _current_task() is self.task

    def note_reported(self, key: tuple) -> None:
        """This call — and every call still running around it — reported this
        scope, so none of them may claim to have recovered it."""
        call: Optional[_Call] = self
        while call is not None:
            if call.active:
                call.reported.add(key)
            call = call.parent


def _iso(epoch: Optional[float] = None) -> str:
    moment = datetime.fromtimestamp(epoch, timezone.utc) if epoch is not None else datetime.now(timezone.utc)
    return moment.isoformat()


# ── the monitor ─────────────────────────────────────────────────────────────

class HealthMonitor:
    """One per TgData: turns findings into plain-data events, keeps the
    per-instance ledger that "ok" recoveries and health_check()["health"]
    read, delivers to the callback without ever letting it break the caller,
    and mirrors each event to the 'tgdata.tgdata.health' logger."""

    def __init__(self, callback: Optional[Callable] = None, label: Optional[str] = None,
                 identity: Optional[Callable[[], Tuple[Optional[str], Optional[int]]]] = None):
        self.callback = callback
        self.label = label
        self._identity = identity
        self._account = OK
        self._account_tick = 0          # when the account verdict was recorded
        self._account_since: Optional[str] = None
        self._account_error: Optional[str] = None
        self._restricted_by: Optional[str] = None
        self._waiting: Dict[str, Dict[str, Any]] = {}
        self._waiting_until: Dict[str, float] = {}
        self._no_access: Dict[str, Dict[str, Any]] = {}
        self._no_access_tick: Dict[str, int] = {}
        self._waits = 0
        self._wait_seconds = 0
        self._events = 0
        self._last_unclassified: Optional[str] = None
        self._callback_failures = 0
        self._health_failures = 0
        self._tasks: set = set()

    # -- the boundary every public TgData call runs inside --------------------

    @contextlib.asynccontextmanager
    async def call(self, method: str, group=None, recover: bool = True,
                   recover_group: bool = True, account_id=_UNSET_ACCOUNT):
        try:
            ensure_sleep_capture()
        except Exception:  # noqa: BLE001
            self._health_failed()
        c = _Call(self, method, group)
        c.recover_group = recover_group
        c.account_id = account_id
        token = _CURRENT.set(c)
        try:
            yield c
        except Exception as exc:
            c.failed = True
            await self._safely(self._on_error, exc, c)
            raise                                          # the same object, unchanged
        else:
            if recover and not c.failed:
                await self._safely(self._recover, c)
        finally:
            c.active = False
            _CURRENT.reset(token)

    async def _safely(self, fn, *args) -> None:
        try:
            await fn(*args)
        except Exception:  # noqa: BLE001 — health code never breaks the observed call
            self._health_failed()

    async def _on_error(self, exc: BaseException, c: _Call) -> None:
        finding = classify(exc)
        if finding is not None:
            _mark(exc, finding)
            await self._emit(finding, c, 'error')

    # -- recording -----------------------------------------------------------

    async def _emit(self, finding: Finding, call: Optional[_Call], source: str, group=None) -> None:
        event = self._record(finding, call, source, group)
        await self._deliver(event)

    def _sleep(self, seconds: int, request: str, call: Optional[_Call], error: Optional[str] = None) -> None:
        """A wait Telethon slept through silently (from the logging filter)."""
        try:
            event = self._record(Finding(WAITING, 'request', error, seconds, request), call, 'sleep')
            self._deliver_now(event)
        except Exception:  # noqa: BLE001 — never raise into Telethon's request
            self._health_failed()

    def _record(self, finding: Finding, call: Optional[_Call], source: str, group=None) -> Dict[str, Any]:
        attributed = call if call is not None and call.owns_current_task() else None
        if group is None and attributed is not None:
            group = attributed.group
        now = time.time()
        when = _iso(now)
        verdict = finding.verdict
        if verdict == WAITING:
            self._waits += 1
            self._wait_seconds += int(finding.wait_seconds or 0)
            if attributed is not None and finding.request:
                if source in ('sleep', 'handled'):
                    attributed.waited.add(finding.request)       # slept and retried: recoverable
                self._waiting[finding.request] = {
                    'seconds': finding.wait_seconds, 'since': when,
                    'until': _iso(now + (finding.wait_seconds or 0))}
                self._waiting_until[finding.request] = now + (finding.wait_seconds or 0)
        elif verdict in (LOGGED_OUT, BANNED, RESTRICTED):
            self._account, self._account_since, self._account_error = verdict, when, finding.error
            self._account_tick = next(_TICKS)
            self._restricted_by = attributed.method if verdict == RESTRICTED and attributed else None
            if call is not None:
                call.note_reported(('account',))
        elif verdict == NO_ACCESS:
            if group is not None:
                key = str(group)
                self._no_access[key] = {'since': when, 'error': finding.error}
                self._no_access_tick[key] = next(_TICKS)
                if call is not None:
                    call.note_reported(('group', key))
        elif verdict == UNCLASSIFIED:
            self._last_unclassified = finding.error
        return self._event(verdict, finding.scope, group, attributed, finding.request,
                           finding.wait_seconds, finding.error, source, when)

    def _event(self, verdict, scope, group, call, request, wait_seconds, error, source, when) -> Dict[str, Any]:
        self._events += 1
        session, user_id = self._who()
        if call is not None and call.account_id is not _UNSET_ACCOUNT:
            user_id = call.account_id
        return {
            'kind': 'health',
            'time': when,
            'account': {'label': self.label, 'session': session, 'user_id': user_id},
            'verdict': verdict,
            'scope': scope,
            'group': group,
            'call': call.method if call is not None else None,
            'request': request,
            'wait_seconds': wait_seconds,
            'error': error,
            'source': source,
        }

    def _who(self) -> Tuple[Optional[str], Optional[int]]:
        try:
            session, user_id = self._identity() if self._identity else (None, None)
            return (str(session) if session is not None else None,
                    int(user_id) if isinstance(user_id, int) and not isinstance(user_id, bool) else None)
        except Exception:  # noqa: BLE001
            return None, None

    # -- recovery ------------------------------------------------------------

    async def _recover(self, c: _Call) -> None:
        """"ok" for what this call proves has ended. A wait: the call slept or
        handled it, and completed. A verdict about the account or a group:
        Telegram answered this call after the verdict was recorded. A
        completion alone proves nothing — a concurrent call answered before
        the verdict, or a call that sent no request — and a call never
        recovers what it reported itself (it may have skipped it and carried
        on)."""
        events = []
        for request in sorted(c.waited):
            if request in self._waiting:
                del self._waiting[request]
                self._waiting_until.pop(request, None)
                events.append(self._event(OK, 'request', None, c, request, None, None, 'recovery', _iso()))
        if ('account',) not in c.reported and c.answered > self._account_tick and (
                self._account in (LOGGED_OUT, BANNED)
                or (self._account == RESTRICTED and self._restricted_by == c.method)):
            self._account, self._account_since, self._account_error, self._restricted_by = OK, None, None, None
            self._account_tick = 0
            events.append(self._event(OK, 'account', None, c, None, None, None, 'recovery', _iso()))
        if c.recover_group and c.group is not None:
            key = str(c.group)
            if (key in self._no_access and ('group', key) not in c.reported
                    and c.answered > self._no_access_tick.get(key, 0)):
                del self._no_access[key]
                self._no_access_tick.pop(key, None)
                events.append(self._event(OK, 'group', c.group, c, None, None, None, 'recovery', _iso()))
        for event in events:
            await self._deliver(event)

    # -- delivery ------------------------------------------------------------

    async def _deliver(self, event: Dict[str, Any]) -> None:
        self._log(event)
        callback = self.callback
        if callback is None or _DELIVERING.get():     # caused by the callback's own call: no re-entry
            return
        token = _DELIVERING.set(True)
        try:
            result = callback(event)
            if inspect.isawaitable(result):
                await result
        except Exception:  # noqa: BLE001 — a broken callback never breaks the caller
            self._callback_failed()
        finally:
            _DELIVERING.reset(token)

    def _deliver_now(self, event: Dict[str, Any]) -> None:
        """Synchronous delivery from inside Telethon's request (the sleep
        filter): a plain callback runs inline, a coroutine is scheduled."""
        self._log(event)
        callback = self.callback
        if callback is None or _DELIVERING.get():     # caused by the callback's own call: no re-entry
            return
        token = _DELIVERING.set(True)
        try:
            result = callback(event)
            if inspect.isawaitable(result):
                try:
                    asyncio.get_running_loop()
                except RuntimeError:
                    if inspect.iscoroutine(result):
                        result.close()
                    return
                task = asyncio.ensure_future(_delivering(result))
                self._tasks.add(task)
                task.add_done_callback(self._task_done)
        except Exception:  # noqa: BLE001
            self._callback_failed()
        finally:
            _DELIVERING.reset(token)

    def _task_done(self, task) -> None:
        self._tasks.discard(task)
        if not task.cancelled() and task.exception() is not None:
            self._callback_failed(task.exception())

    def _callback_failed(self, exc: Optional[BaseException] = None) -> None:
        self._callback_failures += 1
        info = (type(exc), exc, exc.__traceback__) if exc is not None else True
        if self._callback_failures == 1:
            logger.warning("health_callback raised — events keep flowing; further failures are "
                           "logged at DEBUG", exc_info=info)
        else:
            logger.debug("health_callback raised", exc_info=info)

    def _health_failed(self) -> None:
        self._health_failures += 1
        if self._health_failures == 1:
            logger.warning("health reporting failed — the operation itself is unaffected; "
                           "further failures are logged at DEBUG", exc_info=True)
        else:
            logger.debug("health reporting failed", exc_info=True)

    def _log(self, event: Dict[str, Any]) -> None:
        try:
            level = logging.WARNING if event['verdict'] in _LOUD else logging.INFO
            if not _mirror.isEnabledFor(level):
                return
            scope = event['scope']
            key = event['request'] if scope == 'request' else event['group'] if scope == 'group' else None
            where = f"{scope}: {key}" if key is not None else (scope or '-')
            who = event['account']['label'] or event['account']['session'] or '?'
            detail = f" {event['error']}" if event['error'] else ''
            seconds = f" {event['wait_seconds']}s" if event['wait_seconds'] else ''
            _mirror.log(level, f"health: {event['verdict']} [{where}]{detail}{seconds} — "
                               f"call={event['call']} account={who}")
        except Exception:  # noqa: BLE001
            pass

    # -- the summary health_check() returns ----------------------------------

    def snapshot(self) -> Dict[str, Any]:
        now = time.time()
        session, user_id = self._who()
        return {
            'account': {'label': self.label, 'session': session, 'user_id': user_id},
            'verdict': self._account,
            'since': self._account_since,
            'error': self._account_error,
            'waiting': {request: dict(entry) for request, entry in self._waiting.items()
                        if self._waiting_until.get(request, 0) > now},
            'no_access': {group: dict(entry) for group, entry in self._no_access.items()},
            'waits': self._waits,
            'wait_seconds': self._wait_seconds,
            'events': self._events,
            'last_unclassified': self._last_unclassified,
        }


async def _delivering(awaitable) -> None:
    """Run a scheduled async callback with the delivery guard set in its own
    task, so the events of tgdata calls it makes are not delivered back."""
    _DELIVERING.set(True)
    await awaitable


def note_account(account_id: int) -> None:
    """Fresh identity for an opted-in operation, isolated to its owning task."""
    try:
        call = _CURRENT.get()
        if (call is not None and call.owns_current_task()
                and call.account_id is not _UNSET_ACCOUNT):
            call.account_id = account_id
    except Exception:  # noqa: BLE001 — observation never breaks the request
        pass


def note_answer() -> None:
    """Telegram answered a request. Called by tgdata's client class for every
    request that succeeds; the call whose own task sent it records when, which
    is the evidence an "ok" for the account or a group needs. Never raises."""
    try:
        call = _CURRENT.get()
        if call is not None and call.owns_current_task():
            call.answered = next(_TICKS)
    except Exception:  # noqa: BLE001 — never raise into Telethon's request
        pass


async def report(exc: BaseException, source: str = 'swallowed', group=None) -> Optional[Finding]:
    """Report an error an engine handled or swallowed. Does nothing outside a
    public TgData call, for errors that are not health signals, and for an
    error already reported. Never raises."""
    call = _CURRENT.get()
    if call is None:
        return None
    try:
        finding = classify(exc)
        if finding is None:
            return None
        _mark(exc, finding)
        await call.monitor._emit(finding, call, source, normalise_group(group) if group is not None else None)
        return finding
    except Exception:  # noqa: BLE001
        try:
            call.monitor._health_failed()
        except Exception:  # noqa: BLE001
            pass
        return None


# ── silent-sleep capture ────────────────────────────────────────────────────

_SLEEP_MSG = 'Sleeping%s for %ds (%s) on %s flood wait'     # identical in Telethon 1.33.1 … 1.45.0
_SENTINEL_LEVEL = logging.INFO - 1                           # 19: a level no user sets by name
_capture: Optional['_SleepCapture'] = None


class _SleepCapture(logging.Filter):
    """On Telethon's 'telethon.client.users' logger. Turns each silent sleep
    into a waiting event for the account (and call) it happened in, then lets
    through only what the user's own logging levels would have let through."""

    def __init__(self):
        super().__init__()
        self.user_level = logging.NOTSET
        self.user_disabled = False

    def _threshold(self, target: logging.Logger) -> int:
        if self.user_disabled:
            return logging.CRITICAL + 1
        if self.user_level != logging.NOTSET:
            return self.user_level
        parent = target.parent
        return parent.getEffectiveLevel() if parent is not None else logging.WARNING

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if record.msg == _SLEEP_MSG and isinstance(record.args, tuple) and len(record.args) == 4:
                call = _CURRENT.get()
                if call is not None:
                    _early, seconds, _delta, request = record.args
                    # Telethon logs this inside its `except <wait error> as e:`, so the
                    # wait being slept is the exception in flight (not for an early sleep)
                    handled = sys.exc_info()[1]
                    error = (telegram_error_name(handled)
                             if WAIT_ERRORS and isinstance(handled, WAIT_ERRORS)
                             and getattr(handled, 'seconds', None) == seconds else None)
                    call.monitor._sleep(int(seconds), str(request), call, error)
            return record.levelno >= self._threshold(logging.getLogger(record.name))
        except Exception:  # noqa: BLE001 — logging must never break Telethon's request
            return record.levelno >= logging.WARNING


def ensure_sleep_capture() -> None:
    """Install the filter once per process and keep it effective at every
    public call: re-attach it if it was removed, re-assert the sentinel level
    after a user changed it (remembering their level), and re-enable the
    logger after dictConfig disabled it (remembering that, so it still shows
    nothing)."""
    global _capture
    target = logging.getLogger('telethon.client.users')
    if _capture is None:
        _capture = _SleepCapture()
        _capture.user_level = target.level
        target.setLevel(_SENTINEL_LEVEL)
    elif target.level != _SENTINEL_LEVEL:
        _capture.user_level = target.level
        target.setLevel(_SENTINEL_LEVEL)
    if _capture not in target.filters:
        target.addFilter(_capture)
    if target.disabled:
        _capture.user_disabled = True
        target.disabled = False
