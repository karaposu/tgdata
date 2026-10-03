---
model: claude-opus-5-5[1m]
effort: max
---

# Plan — report account health states as events (issue #4)

**Revision 2.**

**Critic folded:** 2026-10-03 — 5 mitigations from `critic.md`, all robust: 4 steps changed (3, 4, 5, 6), 0 added. Risk 5 was folded into `desc.md`, which now records the polling and `validate_connection` decision as criterion 10.

## What is the task

Make tgdata tell its caller every time Telegram says no to an account:
- which verdict;
- about what — the account, one kind of request, or one group;
- from which call;
- for how long;
- when it ended.

This arrives through one exception-safe callback, a log line per event, and a per-instance summary in `health_check()`. It covers waits Telethon sleeps through silently, the errors tgdata swallows, and those that escape public calls.

The maintainer added two fixes to this plan, so that failures stop being hidden:
- **The poll loop** stops swallowing failures that retrying cannot fix.
- **`validate_connection()`** stops hiding why it failed.

## Huge Hard Blockers

### Planning Blockers

None identified.

### Execution Blockers

None identified. Pushing, the PR and merging come after this plan, by the maintainer's decision.

## How this implementation moves toward desired state

**Today.** Telegram's verdicts surface as exceptions, as INFO log lines nobody sees, or not at all:
- the poll loop swallows everything;
- discovery's skips swallow seeds and links;
- `validate_connection()` turns every failure into `False`.

Nothing remembers per account what happened.

**The bridge** is one new module, `tgdata/health.py`. It holds four parts:
1. **A classifier.** It reads Telegram's own error name — through tgdata's wrappers — and returns a verdict, a scope, the wait length and the request type, or nothing when the error is not a health signal.
2. **A per-`TgData` monitor.** It turns findings into plain-data events, keeps the per-instance ledger that "ok" recoveries and `health_check()["health"]` read, delivers to the callback safely, and mirrors each event to a logger.
3. **A call context.** A context variable is set at every public call. It tells every reporting site which account and which call it is in, with no parameters threaded through the engines.
4. **Silent-sleep capture.** A filter on Telethon's own `telethon.client.users` logger, validated offline on Telethon 1.45.0, turns each silent sleep into a waiting event without changing what users' logging prints.

**The wiring** has three parts:
- **The facade.** A decorator on each public `TgData` method that talks to Telegram opens the call context, reports an escaping error, re-raises it unchanged, and sends "ok" on recovery.
- **The engines.** They report the waits they handle and the Telegram verdicts they swallow, through one function, `health.report()`, which does nothing outside a public call.
- **The two fixes.** The poll loop and `validate_connection()` use the same classifier to tell "retrying cannot help" from "temporary".

## High-Level Summary

| Step | Description | Expected Output |
|------|-------------|-----------------|
| 1 | `health.py`: vocabulary, wait family, error names, `classify()`, group normalisation. `AuthRequiredError.first_login`; `GroupAccessError` registered | One classifier for all sites; discovery and the connection engine import the shared pieces |
| 2 | **Fix**: polling stops on failures retrying cannot fix, and callback errors propagate. `validate_connection()` logs the classified reason | No more silent infinite retries of a logged-out, banned or locked-out account |
| 3 | `health.py`: the monitor, call context, events, ledger and recovery, safe delivery, log mirror, snapshot, `report()` | Events with the desc's fields; "ok" only on recovery |
| 4 | `health.py`: silent-sleep capture on Telethon's logger | Waits of 60 s or less become waiting events attributed to account and call |
| 5 | Wiring: `TgData(health_callback=, account_label=)`, the facade decorator, `health_check()["health"]`, engine report sites | Every source in the desc reports; counted once |
| 6 | Offline test `test_16_health_events.py` | Every success criterion checked offline |
| 7 | Docs: README section, docstrings, the polling change | Users can find and use it |
| 8 | Verify all offline suites, then commit | test_16 / 15 / 14 / 13 / 12 pass; commits on the branch |

---

## Step 1 — The classifier and shared vocabulary

### Proposed changes

New module `tgdata/health.py`. It imports only the standard library and Telethon, so it has no import cycle with the engines.

**Constants:**

```python
OK, WAITING, LOGGED_OUT, BANNED, RESTRICTED, NO_ACCESS, UNCLASSIFIED = (
    'ok', 'waiting', 'logged out', 'banned', 'restricted', 'no access', 'unclassified')
TERMINAL = {LOGGED_OUT, BANNED, RESTRICTED, NO_ACCESS}      # retrying cannot fix these

# Every wait Telethon's own sleep branch handles; getattr: FloodPremiumWaitError is newer than 1.33
WAIT_ERRORS = tuple(c for c in (tl_errors.FloodWaitError,
                                getattr(tl_errors, 'FloodPremiumWaitError', None),
                                getattr(tl_errors, 'SlowModeWaitError', None),
                                getattr(tl_errors, 'FloodTestPhoneWaitError', None)) if c is not None)

_TABLE = {   # Telegram's name -> (verdict, scope), as in desc.md criterion 1
    'AUTH_KEY_UNREGISTERED': (LOGGED_OUT, 'account'), 'SESSION_REVOKED': ..., 'SESSION_EXPIRED': ...,
    'AUTH_KEY_INVALID': ..., 'AUTH_KEY_DUPLICATED': ...,
    'USER_DEACTIVATED_BAN': (BANNED, 'account'), 'USER_DEACTIVATED': ..., 'PHONE_NUMBER_BANNED': ...,
    'FROZEN_METHOD_INVALID': (RESTRICTED, 'account'), 'FROZEN_PARTICIPANT_MISSING': ..., 'USER_RESTRICTED': ..., 'PEER_FLOOD': ...,
    'CHANNEL_PRIVATE': (NO_ACCESS, 'group'), 'CHAT_FORBIDDEN': ..., 'CHANNEL_INVALID': ..., 'USER_BANNED_IN_CHANNEL': ...,
    'CHANNEL_PUBLIC_GROUP_NA': ..., 'CHANNEL_BANNED': ...,
}
_UNCLASSIFIED_CODES = {401, 403, 406, 420}
# file-reference errors are ordinary, not health: FILE_REFERENCE_* and FILEREF_UPGRADE_NEEDED
```

**`telegram_error_name(e)`** moves here from `connection_engine`, where it is `_telegram_error_name`. The connection engine imports it. It returns the class's Telegram name from Telethon's `rpc_errors_dict`, else `.message`, else the class name.

**`register(exc_class, verdict, scope)`.** tgdata's own exceptions carry a verdict without an import cycle. `message_engine` registers `GroupAccessError` as no access, scope group.

**`Finding`** is a frozen dataclass with these fields:
- `verdict`, `scope`, `error`, `wait_seconds`, `request`;
- `source_exc` — the exception the finding was read from.

**`classify(exc, include_reported=False) -> Optional[Finding]`** walks `exc` and its cause chain — `__cause__`, else `__context__` unless suppressed — at most ten deep, with no cycles. At each link:
1. **Already reported** — the exception has `_tgdata_health_reported`, and `include_reported` is off: return `None`. This is the counted-once mark.
2. **A first login** — `getattr(e, 'first_login', False)`, an `AuthRequiredError` for a session that was never logged in: return `None`. It is configuration.
3. **A registered class:** return its verdict.
4. **One of `WAIT_ERRORS`:** return waiting, with `e.seconds` and the request type.
5. **An `RPCError`:**
   - a name in `_TABLE` gives that verdict;
   - otherwise a code in `_UNCLASSIFIED_CODES`, unless it is a file-reference name, gives unclassified with `scope=None`;
   - otherwise return `None`. A 400 or 5xx is an ordinary Telegram error, so the walk stops there.
6. **Anything else:** follow the chain.

**`request_name(e)`** is the class name of `getattr(e, 'request', None)`, or `None`.

**`normalise_group(value)`:**
- an int stays an int;
- a string of digits, with an optional leading `-`, becomes an int;
- `@name`, `t.me/name` and `telegram.me/name` become `name.lower()`;
- any other string is lowercased and stripped;
- anything else gives `None`. That includes lists, which have no single group.

**Changes elsewhere:**
- `connection_engine`: `AuthRequiredError.__init__` gains `first_login: bool = False`, stored as an attribute, and `_auth_required` passes it. Its local `_telegram_error_name` is replaced by the import.
- `discovery_engine`: the local `_WAIT_ERRORS` definition is replaced by `from .health import WAIT_ERRORS as _WAIT_ERRORS`, so there is one definition.
- `message_engine`: `health.register(GroupAccessError, health.NO_ACCESS, 'group')` at import.

### Output

`tgdata/health.py` with the vocabulary and the classifier. There is one wait tuple and one error-name function in the package.

### Safe in nature

True. Moving the two shared definitions is mechanical, and they behave identically. `AuthRequiredError` gains an optional attribute.

### Peripheral concepts

Telethon `rpc_errors_dict`, `RPCError.code/.request/.message`, exception `__cause__`/`__context__`/`__suppress_context__`, `AuthRequiredError`, `GroupAccessError`, discovery `_WAIT_ERRORS`, import order between engines

### Hardness Lvl

2

---

## Step 2 — Fix: stop polling on failures retrying cannot fix, and make `validate_connection()` say why

### Proposed changes

**`TgData.poll_for_messages`** (`tgdata/tgdata.py`). Today one `except Exception` around both the fetch and the callback logs and keeps polling forever, whatever the error. Restructure each iteration:

```python
try:
    new_messages = await self.get_messages(group_id=group_id, after_id=current_after_id)
except Exception as e:
    if _polling_cannot_recover(e):
        logger.error(f"Polling {group_id} stopped: {e}")
        raise
    logger.error(f"Error during polling: {e}")       # transient: as today
    iterations += 1
    if max_iterations is None or iterations < max_iterations:
        await asyncio.sleep(interval)
    continue
# … unchanged dedup / after_id bookkeeping …
if callback:
    await callback(truly_new_messages)                 # now OUTSIDE the except: its errors propagate
```

`_polling_cannot_recover(e)` returns True for:
- `AuthRequiredError` and `ProxyConfigError`;
- an error whose `health.classify(e, include_reported=True)` verdict is in `health.TERMINAL`: logged out, banned, restricted, or no access to the polled group — `GroupAccessError` included.

Everything else keeps today's behaviour, logged and retried at the next interval: network and connection errors, flood waits and the fetch loop's give-up, unclassified and 5xx Telegram errors. `include_reported=True` matters here because the inner `get_messages` boundary has already reported and marked the exception.

**Why callback errors propagate.** Today a callback that raises is swallowed after `current_after_id` has already moved past those messages, so they are lost without a trace. Propagation is also what tgdata's other data callbacks, `batch_callback` and `found_callback`, do.

**`ConnectionEngine.validate_connection`** keeps returning `True`/`False`; its callers branch on the boolean. On failure it now logs the classified reason. A Telegram verdict logs at WARNING, `Connection validation failed: logged out (AUTH_KEY_UNREGISTERED)`; anything else keeps the ERROR line. Step 5 makes it report the error to the health stream. The facade makes sure `False` never counts as a recovery.

### Output

- A polling loop that ends with the real error when the account or group cannot be read, and propagates callback errors.
- A `validate_connection()` that says why it returned `False`.

### Safe in nature

False. It is a deliberate behaviour change of a public method, which can now raise where it used to loop forever.

### Peripheral concepts

`TgData.poll_for_messages`, `TgData.get_messages`, `AuthRequiredError`, `ProxyConfigError`, `GroupAccessError`, `ConnectionEngine.validate_connection`, `health.classify`, the README polling section

### Hardness Lvl

2

---

## Step 3 — The monitor, call context, events, recovery and delivery `[folded: Risks 1, 2, 3, 4 — robust]`

### Proposed changes

**Folded from the critique** — these override the details below where they differ:
- **Risk 1 — the reporting path never raises.**
  - In `call()`, the classify, mark and emit work in the `except` branch runs inside its own `try/except Exception`, and so does `_recover` in the `else` branch.
  - `report()` carries the same guard.
  - A failure in health code logs `health reporting failed` once at WARNING with its traceback, then at DEBUG.
  - The caller's exception is re-raised untouched, and a successful call's result is returned untouched.
- **Risk 2 — owner-task attribution.** `_Call` records `task = asyncio.current_task()` at entry. A sleep, or a `report()`, coming from any other task — Telethon's updates loop, an event-handler task, a user task started during the call — is an account-level occurrence: `call=None`, no open-wait entry, no recovery. Only the call's own task is attributed to the call.
- **Risk 3 — recovery bookkeeping.**
  - A waiting finding whose source is `sleep` or `handled`, reported in the call's own active task, adds its request to `c.waited`. That wait was slept and the request retried.
  - A `swallowed` wait does not: the request was skipped, not retried.
  - Every account- or group-scope verdict reported during the call adds its scope key — `('account',)` or `('group', key)` — to `c.reported`.
  - `_recover(c)` skips any scope key in `c.reported`, so a call never recovers from what it reported itself.
- **Risk 4 — per-item groups.** `report(exc, source, group=None)` takes an explicit group, normalised. When given, it is the event's `group` and the no-access ledger key, instead of `call.group`.

The original design follows.

In `tgdata/health.py`:

**The call context:**

```python
_CURRENT = contextvars.ContextVar('tgdata_health_call', default=None)

class _Call:
    __slots__ = ('monitor', 'method', 'group', 'active', 'failed', 'waited')
    # monitor: HealthMonitor; method: TgData method name; group: normalised or None;
    # active: False once the call has returned (a task created during the call keeps a
    # stale reference — silent sleeps there are then account-level occurrences only);
    # failed: set when the call raised or its result means failure; waited: request types
```

**`HealthMonitor(callback=None, label=None, identity=callable)`.** `identity()` returns `(session, user_id)` lazily from the `TgData`. It must never raise; failures give `None`.

**The ledger**, per instance and in memory:
- `account` verdict, with `since` and `error`;
- `restricted_by`, the method;
- `waiting`: `{request: {seconds, since}}`;
- `no_access`: `{str(group): {since, error}}`;
- `waits`, `wait_seconds`, `events`;
- `last_unclassified`.

**The call boundary:**

```python
@contextlib.asynccontextmanager
async def call(self, method, group=None, recover=True):
    ensure_sleep_capture()                      # Step 4
    c = _Call(self, method, group)
    token = _CURRENT.set(c)
    try:
        yield c
    except Exception as exc:
        c.failed = True
        finding = classify(exc)
        if finding is not None:
            _mark(exc, finding)
            await self._emit(finding, c, 'error')
        raise                                    # unchanged, same object
    else:
        if recover and not c.failed:
            await self._recover(c)
    finally:
        c.active = False
        _CURRENT.reset(token)
```

`BaseException` that is not an `Exception`, such as cancellation, propagates without an event.

**`async report(exc, source='swallowed')`**, a module function used by every engine site:
- it reads `_CURRENT`, and does nothing without a call;
- it classifies, marks, and emits through the call's monitor;
- a stale call passes `call=None`.

**`_mark(exc, finding)`** sets `_tgdata_health_reported = True` on `exc` and on `finding.source_exc`, which makes "counted once" hold.

**`_emit(finding, call, source)`** updates the ledger, builds the event, logs it, then delivers it. **`_recover(c)`** emits "ok" events, with `source='recovery'` — a source the desc did not list, added here:
- for each request in `c.waited` still in `waiting`: scope `request`;
- account `logged out` or `banned`: scope `account`;
- account `restricted` and `restricted_by == c.method`: scope `account`;
- `c.group` in `no_access`: scope `group`.

**The event**, built by one function and JSON-ready:

```python
{'kind': 'health', 'time': datetime.now(timezone.utc).isoformat(),
 'account': {'label': ..., 'session': ..., 'user_id': ...},
 'verdict': ..., 'scope': ..., 'group': call.group if call else None,
 'call': call.method if call else None, 'request': ..., 'wait_seconds': ...,
 'error': ..., 'source': ...}
```

**Delivery:**
- `_deliver(event)`, async: log, then call the callback; if the result is awaitable, await it.
- `_deliver_now(event)`, sync, used only by the sleep filter: log, then call the callback; if the result is awaitable, `asyncio.ensure_future(result)`, kept in `self._tasks`, with a done-callback that removes it and logs its exception.
- A callback exception is caught in both. The first is logged at WARNING with its traceback, the rest at DEBUG.

**The log mirror:** `logging.getLogger('tgdata.tgdata.health')`. WARNING for logged out, banned, restricted and unclassified; INFO for waiting, no access and ok. One line:

```
health: <verdict> [<scope>: <key>] <error> — call=<method> account=<label or session>
```

**`snapshot()`** returns the ledger as a JSON-ready dict — times as ISO strings, group keys as strings — plus `account: {label, session, user_id}`.

### Output

`HealthMonitor`, `report()` and the call context.

### Safe in nature

True. A new module, not wired yet.

### Peripheral concepts

contextvars and task copying, `contextlib.asynccontextmanager` exception flow, `inspect.isawaitable`, `asyncio.ensure_future` from sync code inside a running loop, logging hierarchy (`tgdata.tgdata` and `log_file`)

### Hardness Lvl

4

---

## Step 4 — Silent-sleep capture `[folded: Risk 2 — robust]`

### Proposed changes

**Folded from the critique.** The filter attributes a sleep to the call only when `call.active and asyncio.current_task() is call.task`. Every other sleep — no call, an ended call, or another task during a long call such as `run_with_event_loop` or `poll_for_messages` — becomes an account-level waiting occurrence: `call=None`, counted, never opened in the ledger.

In `tgdata/health.py`, the mechanism validated in `probe_health_145.py` (S2–S8):

- **The filter.** A `logging.Filter` subclass `_SleepCapture` on `logging.getLogger('telethon.client.users')`. It recognises `record.msg == 'Sleeping%s for %ds (%s) on %s flood wait'` with four args — the format is identical in Telethon 1.33.1 to 1.45.0 — and reads `early`, `seconds` and the request type from them.
  - With `_CURRENT` set, it calls `call.monitor._sleep(seconds, request, call if call.active else None)`.
  - `_sleep` builds a waiting finding and uses `_deliver_now`. An active call records the request in `call.waited` and in `waiting`; a stale or absent call is an occurrence only.
- **The decision to show the record.** The filter returns `record.levelno >= threshold`, the user's own threshold:
  - `user_disabled` gives `CRITICAL + 1`, so nothing is shown;
  - otherwise the user's explicit level on that logger;
  - otherwise the parent `telethon.client` logger's effective level.
- **`ensure_sleep_capture()`**, run at every boundary entry:
  - install the filter once per process;
  - set the logger's level to the sentinel 19, unless the user set a different level since — then record it as `user_level` and set 19 again;
  - if `dictConfig` disabled the logger, record `user_disabled` and re-enable it for capture only.
- **The filter never raises.** Any internal error is swallowed, so logging cannot break Telethon's request.

### Output

Telethon's silent sleeps during public calls become waiting events with `source='sleep'`. A user's console shows exactly what it showed before.

### Safe in nature

False. It installs a process-wide filter and level on Telethon's logger; verified offline in Step 6.

### Peripheral concepts

Python `logging` filters vs handlers, effective levels, `dictConfig(disable_existing_loggers=True)`, Telethon `UserMethods._call` sleep record, context inheritance by tasks created during a call

### Hardness Lvl

3

---

## Step 5 — Wiring: the facade, the engines and the summary `[folded: Risk 4 — robust]`

### Proposed changes

**Folded from the critique.** Discovery's per-item report sites pass the item as the group:
- `_similar` seed skips pass `group=seed`;
- `_links` skips pass `group=name`.

The decorator also guards its argument binding (`try … except TypeError: group = None`), so the method raises its own argument errors (critic Risk 7, Low).

**`tgdata/tgdata.py`:**
- **`TgData.__init__`** gains `health_callback: Optional[Callable] = None` and `account_label: Optional[str] = None`, and creates `self._health = health.HealthMonitor(health_callback, account_label, self._health_identity)`.
- **`_health_identity()`** returns:
  - `session` — the basename of the engine's loaded config `session_file`, with `.session` stripped;
  - `user_id` — `getattr(primary_client, '_self_id', None)`.

  Both are guarded.
- **A decorator `_reported(group_param=None, recover=True, success_if=None)`.** Using `inspect.signature`, it finds the group argument, falling back to `self.current_group.id`, and normalises it. It then runs the method inside `self._health.call(name, group, recover)`, and sets `c.failed = True` when `success_if(result)` is false.

  | Method | Decorator arguments |
  |---|---|
  | `list_groups`, `search_groups`, `similar_groups`, `discover_groups`, `run_with_event_loop` | none |
  | `get_messages`, `get_message_count`, `search_messages`, `download_media_by_id`, `linked_groups` | `'group_id'` |
  | `poll_for_messages` | `'group_id', recover=False` — its inner `get_messages` calls do the recovering |
  | `validate_connection` | `success_if=bool` |
- **`health_check()`** adds `status['health'] = self._health.snapshot()`.

**Engine report sites.** Each is one awaited line, `await health.report(e, source)`:
- **`message_engine`, the fetch loop's `except FloodWaitError as e:`** — first statement, `'handled'`. All four waits are reported before the give-up raises `RuntimeError(...) from e`. The boundary then skips the marked cause.
- **`discovery_engine`:**
  - `_request` and `_mine_room` — in the within-`max_flood_wait` branch, before sleeping, `'handled'`. Above it, the raise `from e` lets the boundary report it.
  - `_similar` — the seed wait, the seed generic skip, and the round skip, `'swallowed'`.
  - `_search` skip, `'swallowed'`.
  - `_links` — the lookup wait and the dead-name skip, `'swallowed'`.

  `classify` drops non-verdicts such as `ValueError` and `USERNAME_NOT_OCCUPIED`.
- **`connection_engine`:**
  - the `FloodWaitError` handlers in `_authenticate` and `_ensure_connected`, `'handled'`;
  - `validate_connection`'s `except`, `'swallowed'`, after Step 2's log line.

### Output

Every source in desc criterion 4 reports; counted once (criterion 5); "ok" per criterion 6; `health_check()["health"]` (criterion 7).

### Safe in nature

False. Every public method gains a wrapper, though behaviour is unchanged when nothing is reported. The engines gain report lines.

### Peripheral concepts

`TgData` public API and `current_group`, `functools.wraps`, `inspect.signature`, nested public calls (poll → `get_messages`), `DiscoveryInterrupted`, `GroupAccessError`, `AuthRequiredError` from `get_client()`, `run_until_disconnected` re-raise, the message engine's flood loop, discovery's catch sites, `ConnectionEngine.health_check`

### Hardness Lvl

4

---

## Step 6 — Offline test `tgdata/smoke_tests/test_16_health_events.py` `[folded: Risks 1–4 — robust]`

### Proposed changes

The style of test_13 to test_15: numbered TESTs, `Passed: N/M`, exit code, no network and no login. The setup:
- `TgData` built on a temp config;
- engine methods replaced with small async stand-ins that raise or return;
- for sleeps, a factory-built client whose `_sender` is scripted, driving Telethon's real `_call`.

1. **The classifier table:**
   - every desc name, through `rpc_message_to_error`, gives the expected verdict and scope;
   - unknown 401, 403, 406 and 420 give unclassified;
   - 400, 500, `FILE_REFERENCE_EXPIRED` and `FILEREF_UPGRADE_NEEDED` give nothing;
   - `RuntimeError` from `FloodWaitError` gives waiting through the chain;
   - `AuthRequiredError(first_login=True)` gives nothing, and from `AuthKeyUnregisteredError` gives logged out;
   - `GroupAccessError` gives no access;
   - a bare `ConnectionError` gives nothing.
2. **The boundary:**
   - `get_message_count(123)` with the engine raising `ChannelPrivateError` re-raises the same object;
   - exactly one event: no access, scope group, `group=123`, `call='get_message_count'`;
   - `json.dumps(event)` works;
   - the event arrives before the caller sees the exception.
3. **Delivery:**
   - an async callback is awaited;
   - a raising callback breaks nothing, logs once at WARNING, then at DEBUG.
4. **Silent sleeps:**
   - a 1 s Telethon sleep inside a public call becomes waiting with `source='sleep'`, the request, `wait_seconds=1`, and the right call;
   - then "ok" for that request when the call succeeds;
   - a root console handler receives no INFO line.
5. **Two accounts.** Concurrent calls on two `TgData` with different labels and different callbacks each receive only their own sleeps.
6. **Counted once.** A stand-in engine reports four handled waits, then raises `RuntimeError(...) from` the last: four waiting events.
7. **Recovery:**
   - logged out, then a successful call, gives ok for the account;
   - restricted from `get_messages`, then `get_message_count` succeeding, gives no ok; then `get_messages` succeeding gives ok;
   - no access to 123, then a call on 456, gives no ok; then 123 gives ok.
8. **The summary.** `health_check()["health"]` after those shows the account verdict, open waits, groups without access, counters, last unclassified, and is JSON-ready.
9. **The log mirror** levels per verdict on `tgdata.tgdata.health`.
10. **Polling, the fix:**
    - `get_messages` raising `ChannelPrivateError` makes `poll_for_messages` raise after one iteration;
    - a `ConnectionError` is retried until `max_iterations` and returns normally;
    - a raising callback propagates.
11. **`validate_connection`, the fix.** `get_client` raising `AuthRequiredError` from `AuthKeyUnregisteredError` returns `False`, with a logged-out event, `source='swallowed'`, and no "ok".
12. **The real-time path.** `run_with_event_loop` with a stand-in client whose `run_until_disconnected` raises `AuthKeyUnregisteredError` gives a logged-out event, and the error propagates.
13. **No callback.** A `TgData` without `health_callback` behaves as before: same exceptions, same results.
14. **Fail-safe reporting** `[folded: Risk 1]`. With `HealthMonitor._emit` patched to raise, a failing call still raises its own exception, the same object, and a succeeding call still returns its result.
15. **Owner task** `[folded: Risk 2]`. A sleep in a task started during a still-active call gives `call=None` and no open wait.
16. **No self-recovery** `[folded: Risk 3]`:
    - a discovery-style stand-in that swallows a logged-out error, then returns, gives no ok;
    - a stand-in that handles a wait then succeeds gives ok for that request;
    - one that swallows a lookup wait gives no ok for it.
17. **Per-item group** `[folded: Risk 4]`. A swallowed `CHANNEL_PRIVATE` reported with `group='@RoomName'` gives an event with `group='roomname'` and a no-access ledger entry under that key.

### Output

`test_16_health_events.py`, all passing on Telethon 1.45.0.

### Safe in nature

True — a test file.

### Peripheral concepts

smoke-test conventions, Telethon `rpc_message_to_error`, the scripted-sender technique from test_14 and test_15, `logging` capture handlers

### Hardness Lvl

3

---

## Step 7 — Docs

### Proposed changes

**`README.md`** gains a section, "Account health events", with:
- the verdict table;
- one example event;
- `health_callback` and `account_label`;
- the delivery rules;
- the summary in `health_check()["health"]`;
- the log mirror and its levels;
- what is not covered — background-only signals, and restricted marked "by documentation, unobserved".

The README's polling text, if any, states the new stop rule and that callback errors propagate. The docstrings of `poll_for_messages`, `validate_connection` and `TgData.__init__` are updated.

### Output

The feature is documented where users look.

### Safe in nature

True.

### Peripheral concepts

README feature list, `TgData` docstrings

### Hardness Lvl

1

---

## Step 8 — Verify and commit

### Proposed changes

1. **Byte-compile** all touched modules.
2. **Run the offline suites:** `test_16_health_events`, `test_15_login_checks`, `test_14_flood_threshold`, `test_13_device_identity` and `test_12_proxy`. No live tests: their account is logged out.
3. **Commit on `feat/4-account-health-events`** with explicit paths. The working tree's unrelated guide edit stays out. Code, tests and docs go in one commit; this work folder's documents in their own commit (§7.6).

### Output

A green offline run and the commits on the branch. No push, no PR: the merge gate and the PR follow when the maintainer says so.

### Safe in nature

True.

### Peripheral concepts

the CONTRIBUTING process guard (commits allowed on `feat/*`), the unrelated working-tree guide edit

### Hardness Lvl

1

---

## Implementation notes — step 5, 2026-10-03

Implemented in `94560f0`, with all eight steps as written. These details differ from the plan or were added; none is structural.

1. **`validate_connection()` and a logout hidden by `get_me()`.** Telethon's `get_me()` answers a logout or a ban with `None`, so a session logged out after connecting validated `True`, and criterion 10 could not hold. When `get_me()` returns `None`, it now asks Telegram directly — `GetState`, as the login check does — and fails with the real error. Test 11 covers this.
2. **`classify()` reads `AuthRequiredError.reason`.** It applies to an exception with `.banned` and a `.reason` in the table, so one without a cause is still classified (desc criterion 4).
3. **A silent sleep's error name.** The plan left `error` unspecified for sleeps. It is Telegram's exact wait name, read from the exception Telethon is handling when it logs the sleep. It is `None` for an early sleep, a wait already known before sending.
4. **Open waits.** Every wait attributed to a call opens a ledger entry, a swallowed one included: a skipped lookup wait is still an open wait for that request type. Only a slept or handled wait is recoverable by the call, as folded from Risk 3.
5. **Nested calls.** `_Call.parent` records the enclosing call. A scope reported inside a nested public call — poll → `get_messages`, or a callback that makes a public call — is noted on every enclosing active call, so an outer call never recovers what an inner one reported.
6. **No report line in the poll loop's retry branch.** The inner `get_messages` boundary already reports and marks every verdict, so a report there would always be a no-op. Criterion 4's "the poll loop reports every Telegram verdict it swallows" holds through it, with `call=get_messages` and `source=error`.
7. **The fetch loop** reports each wait as its first statement, as Step 5 says. All four waits are `handled`, and the boundary skips the give-up's marked cause.
8. **Small hardening:**
   - the decorator runs the method unwrapped on an instance without a monitor;
   - `ensure_sleep_capture()` re-attaches its filter if it was removed, and handles a logger that `dictConfig` disabled before the first call;
   - `normalise_group` does not read `t.me/joinchat/...` as a username, and accepts `t.me/boost/name`.
9. **Docs** also gained a test_16 entry in `tgdata/smoke_tests/README.md`.

**Verify (step 8):** test_16 17/17, test_15 11/11, test_14 11/11, test_13 6/6, test_12 7/7, on Telethon 1.45.0.

One test-side correction was made during the run. The scripted connection now stamps every error with the request it answers, as Telegram's real answers do; a helper's default had stamped the wrong request name in test 16.
