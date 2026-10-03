---
model: claude-opus-5-5[1m]
effort: max
---

**Verdict: IMPLEMENT AFTER FOLDING THESE IN**

Falsifier: a real Telegram flood wait of 60 s or less, during a live `TgData` call, that Telethon sleeps through without writing its sleep record on `telethon.client.users`. The silent-sleep capture would then have nothing to read.
Affordable now: no — it needs a live account throttled on purpose, which spends its limits. The offline equivalents pass: tests 4, 5, 14 and 15 drive Telethon 1.45.0's real request code.

# PR critic — PR #12, `feat/4-account-health-events` into `dev`

CONTRIBUTING.md §7.2.
- **Subject:** the implemented diff `dev...feat/4-account-health-events` — code, tests and product docs, with `devdocs/` excluded.
- **Read with:** `plan.md`, revision 2, and its implementation notes 1–10.
- **Judged against:** the codebase on Telethon 1.45.0.
- **Prompt:** `pr_dynamic_critic_prompt.md`, beside this file.

It ran in the same AI session as the implementation, never in a subagent, which is the process §7.5 prescribes. Independence comes from the rules instead:
- every changed file was read in full;
- behaviour was probed, and the output is quoted below;
- each Medium stands on a probe and the lines of code it exercises.

The probes are P1–P6, run from this session's scratchpad against the branch.

## High-level summary

**Outcome under §7.3: rejected — two Medium findings.** Per §7.4, the branch returns to step 2. `plan.md` revision 3 takes this file as its input; then the critic, the fold and the implementation run again, PR #12 is updated, and both gates run again.

**The shape survives,** so the verdict is IMPLEMENT AFTER FOLDING THESE IN, not a meaning gap. These parts hold in the code, and probes or tests show it:
- the classifier;
- the per-instance monitor and its ledger;
- the call context with owner-task attribution;
- the silent-sleep capture;
- the decorator, and the engine report sites;
- the two maintainer fixes, and the `health_check()` fix.

**What is wrong is narrower, and both findings sit in the delivery and recovery core.**
1. **"ok" can be sent while the condition persists.** Recovery is inferred from a tgdata call *completing*, not from Telegram *answering* after the verdict. P1: a concurrent call whose only request was answered before a logout finishes after it, and sends "ok". P2: `download_media_by_id(123, [])` sends no request, yet recovers both the logout and group 123.
2. **A callback that calls tgdata re-enters itself without bound.** The event that ends a call is delivered *inside* that call. A natural callback — "on a logout, re-check with `validate_connection()`" — re-triggers itself. P6: one call became 141 nested calls before Python's recursion limit stopped it, and the error was swallowed.

**Three Lows:**
- a finished call's result is kept alive for the connection's lifetime when that call opened the connection from its own task (P3);
- `log_file=` receives only the WARNING health lines by default, though the docs say every event (P4);
- `get_metrics()` runs the same connection check without reporting what it finds.

## Premise Inventory

**What was checked:**
- the plan's and the desc's hedges, including the desc's `[ASSUMPTION]` on "restricted";
- every behavioural claim the diff relies on: Telethon's sleep record, task and context inheritance, logging thresholds, the request counts on the happy path, and the recovery rule.

**Premises, ranked by waste if false:**

1. **Premise:** a tgdata call that completes successfully proves a recorded verdict has ended. This is desc criterion 6's recovery rule, built in plan Step 3's `_recover`.
   - **First dependent step:** Step 3.
   - **Waste if false:** the recovery half of Step 3, and the recovery assertions of tests 7, 11, 16 and 18.
   - **Test scheduled at:** never. The tests supply "success" with stand-ins that never reach Telegram.
   - **Cheapest earlier test:** P1 and P2, a few minutes, offline.
   - **Result:** **false.** Both probes ran at this gate, and the premise is refuted — Risk 1. This is not a REORDER: the code exists, and the test has now run.
   - **Coverage:** **non-covering.** Every recovery test hands the call a success that involves no Telegram answer, so the tests encode the premise rather than observe it.
2. **Premise:** Telegram signals these states with the error names the table lists.
   - **First dependent step:** Step 1.
   - **Waste if false:** Steps 1–8.
   - **Test scheduled at:** never live.
   - **Cheapest earlier test:** none affordable — it needs an account that is throttled, banned or frozen.
   - **Coverage:** **non-covering.** The errors are scripted. The premise rests on Telethon's own error tables.
3. **Premise:** Telethon 1.45.0 writes its sleep record for every silent sleep. That is `users.py:122` inside its `except` block, and `users.py:53` before an early sleep.
   - **First dependent step:** Step 4.
   - **Waste if false:** the capture.
   - **Test scheduled at:** Step 6.
   - **Coverage:** covering for this Telethon version. Tests 4, 5, 14 and 15 run Telethon's real `_call`. A future Telethon that changes the record silently stops capture, and test_16 then fails, which makes it the canary.
4. **Premise** (desc `[ASSUMPTION]`): "restricted" is, for a reader, by documentation and unobserved.
   - **Waste if false:** one table row's wording.
   - **Test:** never.
   - **Coverage:** none.

**Rule check:** no affordable earlier test is scheduled after its first dependent step. The one that was affordable has now run, and it produced Risk 1.

## Restart Check

| Observed failure (desc) | Established mechanism | Design element in the diff |
|---|---|---|
| Waits of 60 s or less are invisible | Telethon sleeps and logs only at INFO on `telethon.client.users` | `_SleepCapture` and `ensure_sleep_capture()` in `health.py`; tests 4 and 5 |
| The poll loop swallows every error | one `except Exception` around the fetch and the callback | `poll_for_messages` restructured, with `_polling_cannot_recover`; test 10 |
| Discovery's skips swallow seeds and links | `except (… RPCError)` skip sites in `discovery_engine.py` | `health.report(..., group=)` at each site; tests 16 and 17 |
| Nothing aggregates per account | no ledger existed | `HealthMonitor`'s ledger and `snapshot()`; test 8 |

Every cited failure has a design element in the diff.

## Inherited Lessons

| Lesson (desc and step 3's critic) | Where the diff satisfies it |
|---|---|
| Verdicts only from Telegram's names, never from a category | `classify()`, `_TABLE`, `_UNCLASSIFIED_CODES`; test 1 |
| Counted once | `_mark()` and the report placement; tests 6 and 10 |
| An observer never breaks the observed | `_safely`, and the guards in `report()`, `_sleep()` and the filter; test 14. **Not for a callback that re-enters tgdata** — Risk 2 |
| A sleep outside a call is an occurrence only | the owner-task rule in `_record`; test 15 |
| tgdata reports and never acts, except criterion 10 | only `poll_for_messages` stops; everything else re-raises unchanged |
| A lookup wait is never slept | unchanged; test 16 |
| Step 3's Risk 3: "ok" means a later, separate success | **Not satisfied.** A concurrent call, or one that sends nothing, counts as that success — Risk 1 |

---

## Risk 1 — "ok" can be sent while the account is still logged out, banned or locked out

### Risk

The feature promises to say "ok" only when a problem has ended, such as a logout. It decides that a problem ended when some later operation completes without an error. But an operation can complete without an error and still tell us nothing about the account now:
- **Concurrent operations.** It may have run alongside the one that hit the logout, with all its own conversation with Telegram finished just before the logout.
- **Operations that never contact Telegram.** It may have contacted Telegram not at all — for example, "download the media for this empty list of messages", which returns at once.

In both cases the account is reported recovered while it is not. A dashboard shows it as healthy. A tool that pauses accounts on a logout and resumes them on "ok" resumes a logged-out account, which fails again. The stream then flaps: logged out, ok, logged out.

**Precisely.** `tgdata/health.py`, `HealthMonitor._recover(c)`, runs from `call()`'s `else` branch whenever the call returns without raising, unless `c.failed` is set. It recovers:
- `logged out` or `banned` unconditionally;
- `restricted` when `restricted_by == c.method`;
- `c.group` when it is in `_no_access`.

Nothing relates the call to *when* the verdict was recorded, or to whether Telegram answered the call at all.

P1 runs real discovery code. `search_groups(..., pace=0.3)` has its one `SearchRequest` answered, then paces. A concurrent `get_message_count` hits `AUTH_KEY_UNREGISTERED`. The search then completes:

```
P1 — a call whose Telegram work predates a logout completes after it
   B's requests: ['SearchRequest']
   events: [('logged out', 'get_message_count'), ('ok', 'search_groups')]
   summary verdict now: ok — the last Telegram answer said AUTH_KEY_UNREGISTERED
```

P2 calls the real, unpatched `download_media_by_id`. It returns `{}` for an empty list before any client exists (`message_engine.py`, `if not ids: return {}`):

```
P2 — a call that sends no request at all
   download_media_by_id(123, []) -> {} | a client was ever built: False
   events: [('no access', 'group', 123, 'get_message_count'), ('logged out', 'account', 123, 'get_message_count'), ('ok', 'account', None, 'download_media_by_id'), ('ok', 'group', 123, 'download_media_by_id')]
   summary: {'verdict': 'ok', 'no_access': {}}
```

The same holds for the following, on an already-connected client:
- `discover_groups()` with nothing to do;
- `similar_groups([])`;
- `linked_groups([])`.

Tests 7, 11 and 18 assert "ok" after stand-in successes that never reach Telegram. They encode the flaw rather than catch it.

### Severity

Medium

### Category

Correctness: false recovery events. This is the failure class step 3 rated Medium as Risk 3.

### Impact

- `health_check()["health"]` and dashboards show a logged-out, banned or locked-out account as `ok`.
- Consumers that act on `ok` — pausing and resuming accounts (#3, #10) — resume an account that cannot work.
- The event stream flaps, which undermines the stream's purpose: a recovery you can trust.

### NoobEng

"The call returned" and "Telegram said yes after the problem began" are different facts. Recovery needs the second one. Every request tgdata sends passes through one place: its client class's `__call__`, the per-request mixin. That is where "Telegram said yes" can be observed, and it can be ordered against when the verdict was recorded.

### Affected areas

`HealthMonitor._recover`, the ledger, `_CURRENT`, and the client mixin `_PerCallFloodThreshold.__call__` in `connection_engine.py`. Tests 7, 11, 16 and 18, the README's "ok only when a condition ended", and desc criterion 6.

### Mitigation

#### Mitigation — Quick

Order recovery by sequence. Give each recorded verdict the ledger's sequence number, and record the number at call entry. `_recover` recovers only verdicts recorded before the call began. This closes P1, not P2.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

Make recovery evidence-based:
- **The ledger.** It keeps a sequence number, and each verdict records the number current when it was recorded.
- **The client mixin's `__call__`.** After a request *succeeds* there, it calls `health.note_answer()`. When the current call owns the task, that stores the ledger's current sequence on the call as `c.answered_seq`.
- **`_recover`.** It recovers an account or group verdict only when `c.answered_seq` is later than that verdict's sequence: Telegram answered this call after the verdict was recorded.
  - Restricted additionally keeps the same-method rule.
  - Waits keep their rule: the call's own slept or handled waits.
- **What does not count.** Requests that bypass `__call__`, such as Telethon's exported senders for media on other data centres, count as no evidence. That can miss an "ok", and never sends a false one.
- **Tests.**
  - P1 and P2 become regression tests.
  - The recovery tests give their stand-ins a scripted Telegram answer instead of a bare return value.

**Why this is robust:** "ok" then rests on Telegram's own answer, received after the verdict. It is decided in the one function that sends it, and it closes both paths: concurrency, and calls that send nothing. `health_check()` and `validate_connection()` need no special case, because their `get_me()` is an answer.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* One evidence check, in the one function that sends "ok", serves all three verdict scopes (account, restricted, group) and closes both refuted paths (P1, P2). Quick closes only P1. Long-term fails the similarity test: GroupAccessError and a reason-only AuthRequiredError carry no request type, so per-type recovery would need special cases.
*For future:* —

#### Mitigation — Long-term

Track recovery per Telegram request type. Record which request types succeed for the account. Recover a scope only when the request type that was refused — from the verdict's `error.request` — later succeeds.

**Why this is long term effective:** it is the finding's original intent for "restricted", where a frozen account may still read while it cannot write, at the granularity Telegram itself works at.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Per-request-type recovery would make 'restricted' exact — a frozen account that can still read — once every verdict carries the request it refused. Revisit if method-level granularity proves too coarse in practice.

---

## Risk 2 — A health callback that calls tgdata re-enters itself, and can fire a burst of requests at Telegram

### Risk

The feature calls the application's own function — its "health callback" — whenever Telegram refuses the account. It calls it *during* the operation that saw the refusal, so the event arrives before the error does. An application that reacts by asking tgdata something — for example, double-checking the connection when it hears "logged out" — starts a new operation from inside the callback. That operation hits the same logout, which calls the callback again, which starts another operation, and so on.

The chain stops only when Python's recursion limit breaks it. Each step is a real request, or a new connection, to Telegram from an account that is already logged out: a burst that can earn rate limits. The failure is silent. The recursion error is caught as "a broken callback", and the original operation returns as if nothing happened.

**Precisely.** `HealthMonitor._deliver` awaits the callback:
- from `call()`'s `except` branch, through `_on_error` and `_emit`;
- from `report()`.

A tgdata call made inside the callback opens a nested `call()`. Its error re-enters `_deliver` with no guard. The scheduled path has the same shape one hop removed: `_deliver_now` turns an async callback into a task that inherits the sleeping call's context, and that task's tgdata calls produce new events.

P6: a callback that runs `validate_connection()` on every `logged out`, with `get_client` raising `AUTH_KEY_UNREGISTERED`:

```
validate_connection() -> False
connection attempts: 141, callback runs: 141, deepest nesting: 141, events counted: 141
```

In the real code, each level is one of two things:
- `get_me()` plus `GetState`, on an existing client — two requests;
- a fresh `connect()` and `GetState`, on first use.

The `RecursionError` that ends the chain is swallowed by `_deliver`'s `except Exception`, and is logged only as a callback failure.

### Severity

Medium

### Category

Observer side effects: re-entrant delivery

### Impact

- A burst of up to about 140 requests or connections from a logged-out account, invisible to the caller.
- Possible rate limits, or a flagged account or IP.
- The same shape, at lower intensity, for async callbacks that call tgdata on `waiting` events while the account is being throttled.

### NoobEng

Synchronous, in-band delivery needs a re-entrancy guard. While the callback runs, events produced by calls the callback itself makes should be recorded and logged, but not delivered to the same callback again. Plain recursion protection — a context flag — is enough, because context variables follow the callback into the calls it makes.

### Affected areas

`HealthMonitor._deliver` and `_deliver_now`, `report()`, `call()`; every application whose callback uses tgdata.

### Mitigation

#### Mitigation — Quick

Document it: "Do not call tgdata from `health_callback`." Add it to the README and the `TgData.__init__` docstring.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

A delivery guard. A context variable, `_DELIVERING`, is set while the callback runs:
- around the awaited call in `_deliver`;
- inside a small wrapper coroutine for the task `_deliver_now` schedules.

While it is set, events from tgdata calls made inside the callback still update the ledger and the log line. They are not delivered to the callback again.

Test: a callback that calls `validate_connection()` on `logged out` produces exactly one nested call, and one callback run for that event.

**Why this is robust:** it breaks the loop where it forms, on both delivery paths, with one flag. The ledger and the log stay complete, and the ordering promise — the event before the exception — is untouched.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* One context flag covers both delivery paths (awaited and scheduled) and keeps desc criterion 3's ordering promise. The long-term queue would break that promise — a contract change — for little extra reach.
*For future:* —

#### Mitigation — Long-term

Decouple delivery from operations. Each monitor gets a queue, drained by one consumer task, so the callback never runs inside a tgdata call and can call tgdata freely.

**Why this is long term effective:** re-entrancy becomes impossible by construction, for every future event kind.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* A delivery queue drained by one consumer task would let callbacks receive the events their own calls produce. It needs desc criterion 3 changed (events after, not before, the exception); revisit if a consumer needs those events.

---

## Risk 3 — A finished call can keep its result in memory until the connection closes

### Risk

When one operation happens to be the one that opens the connection, the library starts long-running background work, such as the loop that receives updates. That background work inherits a reference to the operation's record, and the record holds the operation's task. The task keeps the operation's result alive — for example a large table of messages with media — until the connection closes. This happens only when the application ran that operation in its own task, for example through `asyncio.gather`. It is bounded: one result per connection.

**Precisely.** `_Call.task` holds the task, and `_CURRENT` holds the `_Call`. Telethon creates its long-lived tasks inside `connect()`:
- `telegrambaseclient.py:618-619`, the updates and keepalive loops;
- `mtprotosender.py:285,288`, the send and receive loops.

Those tasks copy the context, and so keep the `_Call` and its task, with the task's `_result`. P3, with the loop settled:

```
   engine directly (control)    : result alive while the background task runs: False; after it ends: False
   through TgData (health layer): result alive while the background task runs: True; after it ends: False
```

### Severity

Low

### Category

Resource lifetime

### Impact

Memory held until `close()` — material only when the connecting call returned something large.

### NoobEng

Release `c.task` (and `c.parent`) in `call()`'s `finally`. `owns_current_task()` is already False by then, so nothing reads them afterwards.

### Affected areas

`_Call`, `HealthMonitor.call()`

---

## Risk 4 — `log_file=` receives only the WARNING health lines by default

### Risk

The README says each health event is written to the library's log, "so `log_file=` receives it". By default, only the serious ones — logged out, banned, restricted, unclassified — reach the file. Waits, lost groups and recoveries are logged at a level the default configuration filters out before any file sees them.

**Precisely.** `TgData(log_file=…)` adds a handler to `tgdata.tgdata` without setting a level, so the effective level is the root's WARNING. P4:

```
   health lines in the file: 1
      tgdata.tgdata.health - WARNING - health: logged out [account] AUTH_KEY_UNREGISTERED — call=get_message_count account=?
   effective level of tgdata.tgdata.health: WARNING
```

### Severity

Low

### Category

Documentation accuracy

### Impact

A `log_file` user sees no waits or recoveries, and may conclude there were none.

### NoobEng

Say so: the INFO lines need `logging.getLogger('tgdata').setLevel(logging.INFO)`. Update the README and desc criterion 8.

### Affected areas

README "Log lines"; desc criterion 8

---

## Risk 5 — `get_metrics()` runs the same connection check, but reports nothing

### Risk

A second method, which exports metrics, runs the same connection check `health_check()` now runs. It finds a logout the same way, but outside the reporting layer, so the logout appears in its output and never in the event stream or the summary.

**Precisely.** `TgData.get_metrics()` calls `self.connection_engine.health_check()` directly. `_confirm_logged_in` raises, and the engine calls `health.report(e, 'swallowed')`, but `_CURRENT` is `None`, so nothing is recorded. `TgData.health_check()` opens a health call; `get_metrics()` does not.

### Severity

Low

### Category

Consistency

### Impact

A logout seen only through `get_metrics()` or `export_metrics()` is missing from the event stream.

### NoobEng

Have `get_metrics()` call `self.health_check()`, or open the same health call around its check.

### Affected areas

`TgData.get_metrics`, `TgData.export_metrics`

---

## After this critique — the maintainer's patch (`dd45f6c`)

The maintainer chose a patch over §7.4's re-plan. The robust mitigation selected for each Medium was implemented as written above:
- **Risk 1:** `_AnswerEvidence` and `health.note_answer()`, and the evidence check in `_recover`.
- **Risk 2:** the `_DELIVERING` guard, on both delivery paths.

**The probes that found them, re-run on the patched branch:**

```
P1 — a call whose Telegram work predates a logout completes after it
   B's requests: ['SearchRequest']
   events: [('logged out', 'get_message_count')]
   summary verdict now: logged out — the last Telegram answer said AUTH_KEY_UNREGISTERED
P2 — a call that sends no request at all
   download_media_by_id(123, []) -> {} | a client was ever built: False
   events: [('no access', 'group', 123, 'get_message_count'), ('logged out', 'account', 123, 'get_message_count')]
P6:
validate_connection() -> False
connection attempts: 2, callback runs: 1, deepest nesting: 1, events counted: 2
```

**Regression tests.** test_16's tests 19–21 now carry P1, P2 and P6. A mutation check shows each catches its defect:
- with the evidence rule removed, tests 19 and 20 fail — test_16 19/21;
- with the guard removed, test 21 fails with 140 nested attempts — 20/21;
- restored, 21/21.

**The other suites:** test_15 11/11, test_14 11/11, test_13 6/6, test_12 7/7.

**The three Lows stand as recorded,** consciously left: Risks 3, 4 and 5.
