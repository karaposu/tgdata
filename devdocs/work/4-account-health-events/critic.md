---
model: claude-opus-5-5[1m]
effort: max
---

**Verdict: IMPLEMENT AFTER FOLDING THESE IN**

Falsifier: a real Telegram flood wait of 60 s or less, during a live `TgData` call, that Telethon sleeps through without writing its sleep record on `telethon.client.users`. That would leave the capture design with nothing to read.
Affordable now: no — it needs a live account to be throttled, which spends its limits. Every offline equivalent has run and passes: `probe_health_145.py` S1–S11 drives Telethon 1.45.0's real request code.

# Critique — plan for issue #4, account health events

## High-level summary

**The plan's shape holds:**
- one classifier;
- a per-instance monitor with a ledger;
- a context variable for the call in progress;
- a filter on Telethon's own logger for silent sleeps;
- a decorator on public methods;
- one-line report calls at engine sites;
- the maintainer's two fixes.

Five Medium findings need folding before implementation. Probes show three of them, and the other two rest on lines of code and the plan's own text.

1. **The reporting path can change what the caller sees.** A bug in the health code inside the boundary replaces the caller's exception, or makes a successful call raise. Probe Q1b and Q1c.
2. **Calls that run for hours absorb other tasks' sleeps.** Under the real-time listener and polling, Telethon's updates loop and every event-handler task inherit the still-active call, so their waits are booked as the call's own. Probe Q2.
3. **"ok" can be false.** A call that swallowed a verdict and then returned normally would count as recovering from it — discovery's skips, for example. Handled and swallowed waits need different bookkeeping.
4. **Per-item verdicts lose their group.** Inside multi-item calls, discovery's seeds and links are reported with the call's group, which is none.
5. **`desc.md` now contradicts the plan.** It promises "reports and never acts", and the polling fix stops the loop on purpose.

Six Low findings are recorded.

## Premise Inventory

**What was checked:**
- the plan's and the desc's hedges, including the desc's `[ASSUMPTION]` on "restricted";
- every claim about Python's asyncio, contextvars, logging and contextlib behaviour, and about Telethon's request path.

**Confirmed by probe:**
- **Telethon's sleep record and the filter mechanics on 1.45.0** — `probe_health_145.py` S1–S11 in #4's work folder, run earlier. This covers the real Telethon request code.
- **An `asynccontextmanager` boundary re-raises the caller's exception unchanged**, the same object with its traceback, when the reporting code works:
  ```
  Q1a emit ok:     caller gets the same object: True; traceback kept: True
  ```
- **Telethon runs event handlers in tasks created by its updates loop**, which therefore inherit that loop's context (`telethon/client/updates.py:285-291`, `self.loop.create_task(self._dispatch_update(...))`).

**Open premises, ranked by waste if false:**
1. **Premise:** Telegram signals waits and verdicts with the error names the table lists.
   - **First dependent step:** Step 1.
   - **Waste if false:** Steps 1–8.
   - **Test scheduled at:** never live.
   - **Cheapest earlier test:** none affordable — a live account would have to be throttled, banned or frozen.
   - **Coverage:** **non-covering** in Step 6, where scripted errors supply the behaviour. The premise rests on Telethon's error tables and on real waits this project has seen before.
2. **Premise** (desc `[ASSUMPTION]`): "restricted" for a reader is "by documentation, unobserved".
   - **First dependent step:** Step 1 — one table row.
   - **Waste if false:** one row's wording.
   - **Test scheduled at:** never.
   - **Cheapest earlier test:** none affordable — it needs a frozen account.
   - **Coverage:** none.

**Rule check:** no affordable earlier test is scheduled after its first dependent step, so the verdict is not REORDER.

## Restart Check

| Observed failure (desc) | Established mechanism | Design element |
|---|---|---|
| Waits of 60 s or less are invisible | Telethon sleeps and logs only at INFO on `telethon.client.users` | Step 4 filter. Attribution in long calls is Medium Risk 2 |
| The poll loop swallows every error | one `except Exception` around fetch and callback (`tgdata.py`, `poll_for_messages`) | Step 2 fix and Step 5 decorator |
| Discovery's skips swallow seeds and links | `except (… RPCError)` skip sites in `discovery_engine.py` | Step 5 report sites. The group is Medium Risk 4 |
| Nothing aggregates per account | no ledger anywhere | Step 3 ledger and `snapshot()` |

Every failure has a design element; the plan works at the right layer.

## Inherited Lessons

| Lesson or prior conclusion (finding and desc) | Where the plan's sequence satisfies it |
|---|---|
| Verdicts only from Telegram's names, never from a category | Step 1 `classify()`, tested in Step 6 T1 |
| Counted once | Step 3 `_mark` and Step 5's report placement, tested in Step 6 T6 |
| **An observer never breaks the observed** | **Not yet.** Steps 3 and 5 have no guard around the reporting path — Risk 1 |
| A sleep outside a call is an occurrence only | Step 4's inactive-call rule. **Not for calls that never end** — Risk 2 |
| tgdata reports and never acts | **Contradicted on purpose** by Step 2, which the maintainer requested. The desc must say so — Risk 5 |
| A lookup wait is never slept through | unchanged; Step 5 only reports |

---

## Risk 1 — A bug in the health code can replace the caller's exception or break a successful call

### Risk

Every public tgdata call will pass through a new reporting layer. When the call fails, the layer records the failure and then lets the original error continue. When the call succeeds, it records any recovery.

If the reporting code itself has a bug — a missing field, an unexpected type — that bug's own error takes the place of the caller's. A caller catching "not logged in" or "flood wait" gets a different error, and a call that worked raises an error it never had. The same happens at the places where tgdata deliberately carries on after an error, such as polling and discovery's skips: a reporting bug there ends a loop that was designed to keep going.

**Precisely.** Plan Step 3's `HealthMonitor.call()` awaits `self._emit(...)` inside `except Exception as exc:` before `raise`, and awaits `self._recover(c)` in the `else` branch. Plan Step 5 adds `await health.report(e, …)` inside `except` blocks in `message_engine.py`, `discovery_engine.py` and `connection_engine.py`.

The probe, with an `asynccontextmanager` shaped like the plan's:

```
Q1b emit raises: caller gets KeyError('bug in the health code') — the caller's ValueError is replaced
Q1c success path: a call that succeeded now raises KeyError
```

The plan guards callback errors and `identity()`, but not `classify`, `_mark`, the ledger, event building, the log mirror or `_recover`.

### Severity

Medium

### Category

Breaking change, potential: observer side effects

### Impact

- A caller's exception handling is defeated by a reporting bug.
- A successful operation fails.
- A resilient loop — polling, discovery's skips — dies.

This is exactly the "observer never breaks the observed" rule #4 was designed around.

### NoobEng

Wrap the two entry points of the health module — the boundary and `report()` — so any exception from health code is caught and logged once, never propagated. The callback is already isolated, but the code around it is not.

### Affected areas

every decorated `TgData` method; every engine report site

### Mitigation

#### Mitigation — Quick

Wrap only the callback-free parts of `_emit` in `try/except Exception: pass`.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

Make the health module's two entry points fail-safe:
- **In `call()`:** put classify, mark and emit in the `except` branch inside their own `try/except Exception`, and the same for `_recover` in the `else` branch. A failure logs `health reporting failed` once at WARNING with its traceback, then DEBUG, and the original exception is re-raised or the result returned untouched.
- **In `report()`:** the same guard, so it never raises.
- **In Step 6:** add a test that patches `_emit` to raise and asserts the caller still gets its own exception and result.

**Why this is robust:** every reporting path funnels through these two functions, so two guards close every site, present and future.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Every reporting path funnels through call() and report(), so two guards close the whole class at almost no cost. The long-term observer wrapper is not one class: the heartbeat already swallows, and found_callback propagates by design.
*For future:* —

#### Mitigation — Long-term

A generic "observer" wrapper for all of tgdata's side channels — heartbeat, health, a future metrics stream — with one tested never-raise contract.

**Why this is long term effective:** the next side channel inherits the guarantee instead of re-implementing it.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

---

## Risk 2 — Calls that last for hours absorb other tasks' waits as their own

### Risk

tgdata remembers which public call is in progress, so it can say which call a wait belongs to. Background work Telegram's library starts during a call inherits that memory: the loop that receives live updates, and every handler that reacts to a new message. The plan treats a call as over once it returns, so later waits in that background work count only as account-level waits.

But some calls never return. The real-time listener runs until the program stops, and polling runs for hours. While such a call is running, every wait in the background update loop and in every message handler is booked as that call's own:
- the summary shows those waits as still open for hours or days;
- no "ok" ever ends them;
- events name the wrong call.

**Precisely.** Plan Step 3's `_Call.active` becomes False only in `call()`'s `finally`. Telethon creates its updates task inside `connect()` and runs event handlers with `self.loop.create_task(self._dispatch_update(...))` (`telethon/client/updates.py:285-291`). Both inherit `_CURRENT` from the call that triggered `connect()`, typically `run_with_event_loop` or `poll_for_messages`, which stays active. The probe:

```
Q2 a task started during a long call sees: {'call': 'run_with_event_loop', 'active': True, 'same task as the call': False}
```

Plan Step 4's filter would therefore add every catch-up wait (`GetDifferenceRequest`) and every handler's waits to `call.waited` and to the open-wait ledger.

### Severity

Medium

### Category

Correctness: attribution and stale state

### Impact

`health_check()["health"]` shows waits that ended long ago. Recovery never fires for them, and dashboards built on the summary mislead.

### NoobEng

Context variables follow tasks, not time. The reliable signal for "this sleep belongs to this call" is the same task, not "the call is still running". It is the same owner-task idea already used by the per-request flood threshold.

### Affected areas

`run_with_event_loop`, `poll_for_messages`, any user task created during a call; the ledger and snapshot

### Mitigation

#### Mitigation — Quick

Never decorate `run_with_event_loop` and `poll_for_messages`.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

`_Call` records `task = asyncio.current_task()` at entry. The filter attributes a sleep to the call only when `call.active and asyncio.current_task() is call.task`. Otherwise it is an account-level occurrence: `call=None`, no open-wait entry, no recovery. Add a Step 6 test in which a task started during a long call sleeps, and the event has `call=None` and no open wait.

**Why this is robust:** it is exact by construction for every long or short call, and is two lines in the filter plus one field.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Exact for every call length with one field and one comparison; the only site that reads another task's context is the filter, because report() always runs in the call's own task.
*For future:* —

#### Mitigation — Long-term

Give Telethon's background tasks their own explicit context: an account-only context set around `connect()` in the connection engine, so background tasks never see a call at all.

**Why this is long term effective:** attribution would no longer depend on where `connect()` happened to run.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* An account-only context around connect() would also stop background tasks from ever seeing a call. Worth it if a second background reader appears; today the filter is the only one.

---

## Risk 3 — "ok" can be sent for something that has not recovered

### Risk

"ok" is meant to say "this problem has ended". The plan sends it when a later call completes normally. But some calls report a problem and then carry on and complete normally anyway, because they deliberately skip the item that failed. Discovery skips a starting room it cannot read. A lookup that had to wait is skipped rather than slept through.

Under the plan's rules, such a call would report "logged out" or "no access" or "waiting" in the middle, then send "ok" for the very same thing at its end — a recovery that did not happen. Separately, waits that tgdata slept through and retried do recover when the call succeeds, but the plan only records sleeps from Telethon as recoverable, not the waits tgdata handled itself, so those never get their "ok".

**Precisely.** Plan Step 3's `_recover(c)` sends ok for:
- every request in `c.waited`;
- account `logged out` or `banned`;
- `restricted` when `restricted_by == c.method`;
- `c.group` in `no_access`.

It does this whenever the call ends without raising. `discover_groups`, `similar_groups` and `linked_groups` return normally after swallowing:
- `discovery_engine.py` `_similar`, `except (ValueError, TypeError, GroupAccessError, RPCError)` and the `_WAIT_ERRORS` seed skip;
- `_links`, the lookup-wait stop and the dead-name skip;
- `_search`'s `except RPCError`.

Step 5 reports these as `'swallowed'` inside the same call. Step 3 only says `_sleep` adds to `call.waited`, so the `'handled'` waits — the fetch loop, discovery's `_request` and `_mine_room` — never enter it.

### Severity

Medium

### Category

Correctness: false recovery events

### Impact

- A dashboard shows an account as recovered while it is still logged out or locked out.
- Waits tgdata handled stay open in the summary for good.

### NoobEng

Recovery needs to know which problems were seen by this call and how they ended:
- a wait that was slept and retried has ended;
- a wait or verdict that was skipped has not.

### Affected areas

`HealthMonitor._recover`, `_emit`, `report()`; discovery's skip sites; the fetch loop's waits

### Mitigation

#### Mitigation — Quick

Do not decorate the discovery methods with `recover=True`.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

Make the bookkeeping explicit in Step 3:
- a waiting finding with `source` in `{'sleep', 'handled'}` and an active same-task call adds its request to `c.waited`;
- `'swallowed'` waits do not;
- every account- or group-scope verdict reported during the call is added to `c.reported` as a scope key;
- `_recover(c)` skips any scope key in `c.reported`.

Add Step 6 tests:
- a `discover_groups` stand-in that swallows a logged-out seed error then returns: no ok;
- a fetch-loop stand-in that handles a wait then succeeds: ok for that request.

**Why this is robust:** "ok" then means exactly "a later, separate success", in the one function that sends it.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* It fixes recovery where it is decided, in one function and the call record. The long-term fix touches the client mixin in another module, so it fails the size gate, and robust survives it.
*For future:* —

#### Mitigation — Long-term

Track recovery per Telegram request rather than per tgdata call: record every request type that succeeds, through the per-request client mixin's `__call__`, and recover a scope only when the refused request type itself later succeeds.

**Why this is long term effective:** it is the finding's original intent for "restricted", at the granularity Telegram works at.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Per-request recovery, recording successful request types through the per-request client mixin, would make 'restricted' recover exactly as the finding intended. Do it if tgdata-method granularity proves too coarse in practice.

---

## Risk 4 — A verdict about one item inside a multi-item call loses its group

### Risk

Some calls work through many rooms at once. Discovery starts from several seed rooms and follows many links. When one of those rooms cannot be read, the event should name that room.

The plan fills the event's group from the call's single group argument. These calls have none, so the event names no group, and the summary has nothing to file the lost room under. A dashboard sees "no access" but not where, and a later successful read of that room cannot close it.

**Precisely.** Plan Step 3 builds events with `'group': call.group if call else None`, and `report(exc, source)` takes no group. Plan Step 5 decorates `search_groups`, `similar_groups` and `discover_groups` with no group parameter, and `linked_groups` with `'group_id'`, which `normalise_group` turns to `None` for a list. The per-item swallow sites in `discovery_engine.py` all know the item:
- `_similar` has `seed`;
- `_links` has `name`;
- a `GroupAccessError` from `MessageEngine._entity_after_dialog_sync` inside `_resolve` carries the integer `ref`.

### Severity

Medium

### Category

Correctness: missing attribution (desc criterion 2)

### Impact

No-access events from discovery are unattributable. The no-access part of the summary misses them, and their recovery cannot work.

### NoobEng

The boundary knows only the call's arguments, while the engine site knows the item. Pass the item explicitly where it is known.

### Affected areas

`health.report()`; discovery's seed and link skip sites; the event and ledger

### Mitigation

#### Mitigation — Quick

Put the item in the event's `error` text.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

Give `report(exc, source, group=None)` an explicit group, normalised with `normalise_group`. When given, it overrides `call.group` for that event and its ledger entry. Discovery passes `group=seed` at the seed skips, and `group=name` at the link skips. Add a Step 6 test: a swallowed `CHANNEL_PRIVATE` for seed `@roomname` gives an event with `group='roomname'` and a ledger entry.

**Why this is robust:** the site that knows the item says so, with one optional parameter.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Every per-item swallow site already knows its item; one optional parameter carries it.
*For future:* —

#### Mitigation — Long-term

Read the group from the Telegram error's own request — its `peer` or `channel` field — for every error, wherever it is reported.

**Why this is long term effective:** attribution would come from Telegram's own request, even at sites that do not know the item.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Reading the group from the Telegram error's request (peer or channel) would cover sites that do not know the item. None exists today.

---

## Risk 5 — The description promises "reports and never acts"; the polling fix acts

### Risk

The issue's description is the agreed promise of what #4 delivers. It states that tgdata only reports these states and never acts on them: nothing is paused, retried or stopped because of a verdict. The plan now includes the maintainer's fix that makes polling stop when the account is logged out, banned or locked out of the group.

That is a sound change, but it is an action, and the description does not mention it. The merge check compares the code to the description and plan, so it would find them disagreeing. A reader of the description alone would be surprised that polling can now raise.

**Precisely.** `desc.md` § User Value Proposition: "tgdata **reports and never acts**: no exception a caller catches today changes type or identity, and nothing is paused, retried or skipped because of a verdict." Plan Step 2 makes `poll_for_messages` re-raise terminal verdicts, `AuthRequiredError` and `ProxyConfigError`, and propagate callback errors. Today it never raises.

### Severity

Medium

### Category

Specification drift

### Impact

- The merge gate fails on desc–plan disagreement (CONTRIBUTING §7.1 question 2).
- Users are not told about a behaviour change in a public method.

### NoobEng

When the plan changes the promise, the promise document changes with it, before the code.

### Affected areas

`desc.md` (User Value, Scope Boundaries, Success Criteria); README polling text

### Mitigation

#### Mitigation — Quick

A note in the plan only.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

Amend `desc.md`, recording the maintainer's decision of 2026-10-03:
- **User Value:** "reports and never acts — except two fixes the maintainer added".
- **Success Criteria**, a new criterion 10:
  - polling stops with the real error on logged out, banned, restricted, no access, `AuthRequiredError` or `ProxyConfigError`;
  - it retries everything else;
  - callback errors propagate;
  - `validate_connection()` keeps its boolean, logs its reason, and never counts as a recovery.
- **Scope Boundaries:** acting on verdicts stays out *except* this polling stop.

**Why this is robust:** the promise, the plan and the code agree before implementation, which is what the merge gate checks.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The maintainer put the fixes in this issue; amending the desc keeps one promise in sync with the plan, which is what the merge gate checks.
*For future:* —

#### Mitigation — Long-term

Split the polling and `validate_connection` fixes into their own issue with their own description.

**Why this is long term effective:** each issue keeps one promise.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

---

## Risk 6 — Polling's callback errors propagate after the position has moved on

### Risk

Polling remembers the newest message it has handed over and asks only for newer ones next time. It moves that marker forward before calling the user's code. If the user's code now fails and the error reaches the user, they do not learn the new marker. Restarting from their own last value repeats some messages, which is better than today's silent loss, but not exact.

**Precisely.** `tgdata.py` `poll_for_messages` sets `current_after_id = max_id` before `await callback(truly_new_messages)`. The plan's Step 2 lets callback errors propagate without exposing `current_after_id`.

### Severity

Low

### Category

Behaviour change

### Impact

Duplicates on restart after a callback error.

### NoobEng

Advancing the marker after the callback succeeds, or attaching it to the error, would make a restart exact. That is optional polish.

### Affected areas

`poll_for_messages`

---

## Risk 7 — Argument binding in the decorator can fail before the method runs

### Risk

To find which group a call is about, the new wrapper matches the caller's arguments against the method's parameters. If a caller passes arguments the method does not accept, the wrapper's matching fails first. The caller still gets a "wrong arguments" error, but from inside the wrapper rather than the method.

**Precisely.** Plan Step 5 uses `inspect.signature(fn).bind_partial(self, *args, **kwargs)` before calling `fn`. `bind_partial` raises `TypeError` on unexpected keywords.

### Severity

Low

### Category

Compatibility

### Impact

The error's message and traceback origin differ.

### NoobEng

Guard the bind (`try … except TypeError: group = None`), and let the method raise its own error.

### Affected areas

the `_reported` decorator

---

## Risk 8 — Two calls waiting on the same request type close each other's wait

### Risk

If two calls wait on the same kind of Telegram request at the same time, the first to finish sends "ok" and clears the shared open-wait entry, while the second may still be waiting.

**Precisely.** The ledger's `waiting` is keyed by request type only. `_recover` deletes the key for any request in `c.waited`.

### Severity

Low

### Category

State accuracy

### Impact

The summary briefly under-reports open waits.

### NoobEng

Reference-count open waits per request type if it ever matters.

### Affected areas

ledger

---

## Risk 9 — Polling still retries a group name that does not exist

### Risk

If polling is given a username that does not exist, the lookup fails with a generic "not found" error that is not a Telegram verdict. Polling keeps retrying it at every interval, as it does today.

**Precisely.** Telethon raises `ValueError` for unknown usernames. Plan Step 2's `_polling_cannot_recover` treats `ValueError` as transient.

### Severity

Low

### Category

Behaviour, unchanged

### Impact

A misconfigured poll loops forever, as today.

### NoobEng

It is conservative on purpose; it could be revisited once real logs show which `ValueError`s polling meets.

### Affected areas

`poll_for_messages`

---

## Risk 10 — Capture stops under `logging.disable(INFO)` or a level change in the middle of a call

### Risk

The sleep capture depends on Telethon's sleep record being created. A program that silences INFO process-wide, or changes that logger's level in the middle of a call, stops capture until the next call begins.

**Precisely.** Carried from #4's design critique: `logging.disable` overrides logger levels, and the plan re-checks only at boundary entry.

### Severity

Low

### Category

Observability limit

### Impact

Missed sleep events in those setups.

### NoobEng

Document it.

### Affected areas

Step 4

---

## Risk 11 — An async callback scheduled from the filter needs a running loop

### Risk

When the callback is asynchronous and a wait is captured from inside Telegram's library, the callback is scheduled to run shortly afterwards. That needs a running event loop, which Telethon always has while it sleeps. A future change running the request code differently could break that assumption.

**Precisely.** Plan Step 3's `_deliver_now` uses `asyncio.ensure_future`.

### Severity

Low

### Category

Robustness

### Impact

A lost event plus a "coroutine never awaited" warning, in a setup that does not exist today.

### NoobEng

Guard with `asyncio.get_running_loop()` in a `try`, and close the coroutine if there is none.

### Affected areas

`_deliver_now`
