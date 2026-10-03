---
status: active
model: claude-opus-5-5[1m]
effort: max
---
# Finding: account health events for tgdata (issue #4), on Telethon 1.45.0

## Question

tgdata is a Python library that wraps Telethon, the Telegram client library, to read groups and messages into tables. Issue #4 asks tgdata to "report account health states as events". It names six states: ok, waiting, logged out, banned, restricted and no access.

This inquiry asked what that should mean inside tgdata, concretely. Five facets were in question:
1. which Telegram signals map to which state, including the short waits Telethon sleeps through without telling anyone;
2. what one event looks like, and whether "ok" is sent on every call or only on recovery;
3. where in tgdata events must come from;
4. whether the callback that receives events may break the operation, or must be exception-safe;
5. whether fixing a known login bug belongs in #4 or elsewhere.

**Goal:** a stable, decided meaning from which #4's issue description can be written. That description is the five-section `desc.md` that CONTRIBUTING.md, the repository's contribution guide, requires: Problem Statement, User Value, Success Criteria, Scope Boundaries, Priority.

**Mid-inquiry direction from the user:** use the latest Telethon release, not the older version in the repository's environment.

## Finding Summary

- **What a health event is.** tgdata's report of each time Telegram says no to an account: which verdict, about what, from which call, for how long, and when it ended. tgdata reports and never acts on it.
- **The base is Telethon 1.45.0**, the latest release on PyPI (2026-09-10).
  - The repository's environment moved from 1.40.0 to it.
  - tgdata's offline proxy and device-identity tests pass on 1.45.0.
- **Six verdicts at three scopes.** About the whole account: logged out, banned, restricted, ok. About one kind of request: waiting. About one group: no access.
- **"Unclassified"** reports a Telegram error the list does not know, but only in the four error categories where account trouble lives.
- **Verdicts come only from a fixed list of Telegram's own error names**, never from an error's category. On 1.45.0 a category mixes real logouts with unrelated errors, such as one meaning a file reference needs refreshing.
- **Each event is plain data**, ready to serialize to JSON: time, account, verdict, scope, group, call, wait length, Telegram's error name, and where it was observed.
- **"ok" means recovery, not success.** It is sent only when something that was wrong recovers. A restricted account counts as recovered only when the very request it was refused later succeeds.
- **One callback per tgdata instance**, `health_callback=`. It may be a plain function or a coroutine, and it can never break the operation it observes.
- **Five sources of events:**
  - the boundary of every public tgdata call;
  - the waits tgdata handles itself;
  - the short waits Telethon sleeps through silently;
  - the places tgdata swallows errors;
  - the authorization checks.
- **Silent waits are caught by a filter on Telethon's own logger.** An offline probe on 1.45.0 shows the filter captures every such wait and changes nothing a user's logging prints.
- **Two more views of the same record:**
  - a log line per event — WARNING for the serious verdicts, INFO for the rest;
  - a per-instance summary in `health_check()`, tgdata's existing status call.
- **Prerequisite: a separate bug that #4 is blocked by.** tgdata's authorization checks must tell a ban, a logout and a wait apart. A session that was logged in before must never ask for a login code on its own. This also ends a login-code storm that hit a real account.
- **Found outside #4:** tgdata's group discovery relies on a per-call wait setting that Telethon ignores, in every release from 1.33.1 to 1.45.0.
- **Still open:**
  - what a frozen account can still read, which needs observation;
  - how a group is identified inside an event, which must be settled before the event shape is published;
  - a few details for the plan.

## Finding

Telegram limits and penalises accounts in several ways. It asks a client to wait, revokes a session, bans an account, freezes it, or locks it out of a group.

Today tgdata surfaces these as exceptions and log lines, or not at all. An operator running many accounts cannot see "account 7 waited 4 times, 210 seconds in total" or "account 3 was banned at 14:02" without reading logs. Issue #4 asks for that visibility as events.

This finding defines what those events are, precisely enough that #4's description can be written without leaving options open.

### 1. The baseline: Telethon 1.45.0

The inquiry began against Telethon 1.40.0, the version in the repository's virtual environment. Midway, the user directed: "Use the latest Telethon release, and … understand what we want to build based on the latest telethon."

- **The latest release is 1.45.0**, published to PyPI on 2026-09-10. No 2.x release exists on PyPI.
- **The environment moved to it.** It is inside tgdata's declared range, `Telethon>=1.33,<2.0`. Rolling back is `pip install telethon==1.40.0`.
- **tgdata still works on it.** The two offline smoke tests pass: proxy, 7 of 7, and device identity, 6 of 6.

Every Telethon fact below was re-checked on 1.45.0, in its source and by running it. Where older releases matter, six were compared: 1.33.1, 1.34.0, 1.40.0, 1.42.0, 1.44.0 and 1.45.0. Several conclusions reached on 1.40 changed as a result; they are listed in the Reasoning section.

### 2. What a health event is

A health event reports one occurrence of Telegram refusing or limiting an account. It also reports the moment such a condition ends.

- **It is a side channel.** Events go to whoever registered for them.
- **It changes nothing else.** The exception a caller receives today stays the same exception, of the same type. tgdata does not stop, retry, pause or skip anything because of a verdict.

The reason is that every operation that meets a ban or a logout already raises its own exception, so a caller can already stop on it. Making events carry control would let a bug in a monitoring dashboard end a scrape.

### 3. The six verdicts

The six names are the issue's own. They are kept because related issues use them: #3, proxy health checks; #9, per-account request budgets; #10, a worker that moves accounts between machines.

Each verdict has a **scope**, the thing it is about:

| Verdict | Scope | Meaning | Telegram error names (1.45.0) |
|---|---|---|---|
| waiting | one kind of request | Telegram asked the client to wait before repeating this request type | `FLOOD_WAIT_X`, `FLOOD_PREMIUM_WAIT_X`, `SLOWMODE_WAIT_X`, `FLOOD_TEST_PHONE_WAIT_X` — each carries the seconds |
| logged out | account | the session no longer works; logging in again recovers it | `AUTH_KEY_UNREGISTERED`, `SESSION_REVOKED`, `SESSION_EXPIRED`, `AUTH_KEY_INVALID`, `AUTH_KEY_DUPLICATED` |
| banned | account | the account is deactivated or banned; logging in does not help | `USER_DEACTIVATED_BAN`, `USER_DEACTIVATED`, `PHONE_NUMBER_BANNED` |
| restricted | account | the account is frozen or spam-limited | `FROZEN_METHOD_INVALID`, `FROZEN_PARTICIPANT_MISSING`, `USER_RESTRICTED`, `PEER_FLOOD` |
| no access | one group | this account cannot read this group | `CHANNEL_PRIVATE`, `CHAT_FORBIDDEN`, `CHANNEL_INVALID`, `USER_BANNED_IN_CHANNEL`, `CHANNEL_PUBLIC_GROUP_NA`, `CHANNEL_BANNED`, and tgdata's own `GroupAccessError` |
| ok | the scope that recovered | a condition above has ended | — |

Why three scopes and not one:
- **No access concerns one group.** An account locked out of group Y can still read group X, so marking the whole account would show a working account as broken.
- **Waiting concerns one kind of request.** Telethon remembers waits per request type. One observed account could not look up usernames for 21 hours while it kept reading normally.

Why banned and logged out are kept apart: "logged out" promises that logging in again will help, and "banned" does not. Mixing them would send an operator to re-login an account that is gone.

Why "no access" comes only from confirmed answers: the most common failure in practice is Telethon's local message "Could not find the input entity". It often means only that the session has not seen the group yet. tgdata confirms such cases with a dialog sync, its existing step that refreshes the account's list of chats, before treating them as no access. An unconfirmed lookup miss is not a health signal.

The **restricted** row is honest about its evidence. Telethon 1.45.0 describes `FROZEN_PARTICIPANT_MISSING` as "Your account is frozen and can't access the chat", and `PEER_FLOOD` as account-wide with no defined duration. But no frozen account has been observed, so which reads still work for one is unknown. The description must mark this row "by documentation, unobserved".

**Unclassified** is reported when Telegram returns an error that is not in the table, in one of four categories: authorization (code 401), forbidden (403), the auth-key family (406), or flood (420). These are the categories where account trouble lives, so an unknown name there is worth seeing. File-reference errors are excluded. Ordinary bad-input errors (400) and server errors (5xx) never produce a health event. `CHAT_RESTRICTED` ("The chat is restricted and cannot be used in that request") stays unclassified until someone observes what it means for a reader.

### 4. How an error becomes a verdict

Telethon turns each Telegram error into a Python exception. On 1.45.0 a known error becomes its own class, such as `AuthKeyUnregisteredError`, whose `.message` holds only a category word such as "UNAUTHORIZED". An error Telethon does not know becomes the bare category class, with Telegram's own name in `.message`.

The rule:
1. **Read Telegram's name for the error.** For a known class, take it from Telethon's own error tables (`rpc_errors_dict` and `rpc_errors_re`, both present on 1.45.0). For an unknown error, take it from `.message`.
2. **Look the name up in the table above.** That is the only way a verdict is given.
3. **If the name is not listed**, report "unclassified" when the error's category is one of the four above, and nothing otherwise.
4. **Look through wrappers.** tgdata sometimes raises its own exception around Telegram's: a `RuntimeError` after giving up on waits, a `ConnectionError` from authentication, an `AuthRequiredError`, or `DiscoveryInterrupted`. Follow the chain of causes to the Telegram error inside.

The earlier design had a fallback: "anything in the authorization or auth-key category means logged out". On 1.45.0 it is wrong.
- The 401 category also holds `SESSION_PASSWORD_NEEDED`, a two-step-verification prompt during login, and `AUTH_KEY_PERM_EMPTY`, about temporary keys.
- The 406 category is mostly unrelated: `FILEREF_UPGRADE_NEEDED` (a file reference needs refreshing), `STICKERSET_OWNER_ANONYMOUS`, `USERPIC_PRIVACY_REQUIRED` and others.
- With the fallback, a media download that needed a file refresh would have reported the account as logged out.

So the category may decide *whether* to report unclassified, and never *which* verdict.

Because the key is Telegram's name, the same table works on old Telethon releases, where some of these errors are not yet classes. It also works on future ones.

### 5. The event's shape

Each event is a plain dictionary of strings, numbers and `None`. It can be serialized to JSON and sent to another process, as #10's worker will need.

| Field | Content |
|---|---|
| `kind` | `"health"` — other producers (proxy checks, budgets, login steps) can add their own kinds later |
| `time` | UTC, ISO 8601 |
| `account` | `label` (optional, given by the caller), `session` (the session file's name without folder or extension), `user_id` (when Telethon already knows it; `None` otherwise) |
| `verdict` | one of the six, or `unclassified` |
| `scope` | `account`, `method` or `group` |
| `group` | the group the event concerns, when there is one |
| `call` | the Telegram request involved, such as `GetHistoryRequest` |
| `wait_seconds` | the wait length, for waiting |
| `error` | Telegram's error name |
| `source` | where it was observed: `error`, `sleep`, `auth` or `updates` |

Three rules about the account:
- **No local paths.** The config path and the session's folder never appear, because they mean nothing on another machine.
- **Name pooled connections by the configured session.** When tgdata runs several connections for one account, the extra session files are numbered (`<session>_1`, …). Using the numbered file's name would split one account into several.
- **Get the user id without a new network call.** On 1.45.0, Telethon restores the logged-in user's id from the session file when it connects. Reading it uses a private property (`_self_id`), so the plan must choose between that read and leaving the id empty until tgdata's own `get_me()` runs.

**One field is not decided yet: how `group` is identified.** It could be Telegram's numeric id, or whatever the caller passed in (an id, a username, or a link). Recovery (section 6) and per-group totals both depend on the choice, and changing a published field later breaks consumers. It must be settled in the description or the plan before anything is published.

A `severity` field was considered and dropped (see Reasoning).

### 6. When "ok" is sent

"ok" is not a heartbeat. tgdata already has a heartbeat callback for liveness. "ok" marks the end of a condition, one recovery per scope:
- **Waiting** ends when the call that waited completes successfully.
- **Restricted** ends only when the request type that was refused later succeeds. A frozen account that can still read would otherwise flip between restricted and ok on every mixed run.
- **Logged out** ends when the account is authorized again.
- **Banned** cannot end within one tgdata instance, because no call succeeds.
- **No access** ends when that group is read successfully.

Every non-ok occurrence is its own event, not only changes of state. #4's own example, "waited 4 times, 210 s total", needs each wait and its length. Reporting only changes would merge repeated waits into one.

A wait that Telethon sleeps through inside its own background task, with no tgdata call around it, is reported as an occurrence only. No "ok" follows it, because nothing marks its end.

### 7. Delivery: the callback contract

- **One callback per instance**, given when the instance is built: `TgData(..., health_callback=fn)`. The name follows tgdata's existing callbacks, which all end in `_callback`.
- **A plain function or a coroutine.** It is detected the way tgdata already detects `found_callback`: call it, and await the result if it is awaitable.
- **It can never break the operation.** If the callback raises, tgdata logs the error and carries on. Unlike the heartbeat, which swallows errors silently, the first error is logged at WARNING with its traceback, and repeats at DEBUG, so a broken callback cannot flood the log.
- **Async callbacks are awaited where tgdata runs async code**: the public-call boundary, the poll loop, the waits tgdata handles, and discovery's skips. An event that ends an operation, such as "logged out" or "banned", is therefore delivered before the operation's exception reaches the caller.
- **One place schedules instead:** the logging filter (section 9), which runs synchronously inside Telethon. There an async callback is scheduled as a task, with a reference kept and its errors contained. The probe showed it runs during the wait Telethon begins right after logging.
- **Why not schedule everywhere:** the probe also showed that a task scheduled just before a program finishes is cancelled by `asyncio.run`. The final "banned" event of a run would be lost.

### 8. Where events come from

Instrumenting call sites one by one would drift, so events come from one boundary plus four enumerated internal sources:
1. **The public-call boundary.** One wrapper around every public `TgData` method that talks to Telegram — reading groups and messages, counting, searching, downloading, the four discovery calls, connection checks, the real-time listener and the poll loop. It classifies any Telegram error that escapes, sends the event, and re-raises the exception unchanged.
2. **Waits tgdata handles itself:** the message fetch loop's wait handling, and discovery's request and post-reading loops. Discovery sees only waits longer than 60 seconds, because the per-call setting it relies on is ignored by Telethon (section 13). Shorter waits are caught by source 3.
3. **Telethon's silent sleeps** (section 9).
4. **Places tgdata swallows or re-raises errors:**
   - the poll loop, which sends an event and then continues as today;
   - discovery's skips, for Telegram verdicts only;
   - the real-time path, when Telethon re-raises the error that stopped its background updates loop.
5. **The authorization checks**, once the prerequisite bug (section 11) gives them truthful answers.

**Never reported:**
- per-message file and media errors;
- exceptions raised by the user's own event handlers;
- unconfirmed lookup misses;
- network and proxy failures with no Telegram error behind them;
- configuration errors.

A dead proxy says nothing about the account behind it, so connectivity is not a health verdict. It stays in `health_check()`, and #3 can report it later under its own `kind`.

**Counted once.** Each wait and each error is counted exactly once.
- Telethon either sleeps and logs, or raises — never both. The probe confirmed this on 1.45.0.
- On tgdata's side, an error already reported inside an engine is marked, so the public-call boundary does not report it again.
- Four waits followed by a give-up therefore produce four waiting events, not five.

**Not yet ruled on.** On 1.45.0 two more signals exist only as INFO log lines inside Telethon's background updates task:
- "Account is now banned in <channel id>", when a channel is lost during catch-up;
- waits while catching up, which carry the request type but no seconds.

The same filter technique can read them. Whether #4 includes them is the last open inventory decision; adding them later breaks nothing.

### 9. Seeing Telethon's silent sleeps

When Telegram asks for a wait of 60 seconds or less, Telethon sleeps inside the request and only writes an INFO log record: `Sleeping for 30s (0:00:30) on GetHistoryRequest flood wait`. The record lands on the logger `telethon.client.users`. With ordinary logging settings nobody sees it — the downstream service that suffered the login-code storm had no such line in its whole log. #4's wait totals need these waits.

The message and the logger name are identical in all six compared releases, 1.33.1 to 1.45.0. That logger only ever writes INFO and WARNING.

**The mechanism**, verified by an offline probe that runs Telethon 1.45.0's real request code with a fake connection:
- **A filter on `telethon.client.users`.** A logging filter sees each record before any handler does. It captures the sleep and then lets through only what the user's own logging levels would have let through.
- **A sentinel level.** tgdata sets that logger's level to 19, one below INFO, so the records are created at all. Since no user sets 19 by name, any later change by the user is noticed and respected.
- **A re-check at each public call.** It notices user changes, and re-enables capture if a logging reconfiguration disabled the logger (`dictConfig` does this by default). The logger stays silent for the user.
- **Context variables for attribution.** tgdata marks each public call with the account and the call.
  - Telethon starts its background updates task inside `connect()`, and the task inherits the context at that moment.
  - tgdata therefore keeps the account variable set, and clears the call variable, around `connect()`.
  - Background sleeps are then attributed to the right account and never to a call that has ended.

**What the probe showed**, 17 checks in all:
- The sleep is captured with the account, the call, the request type and the seconds.
- No INFO line reaches a console that showed none before.
- Telethon's warnings still reach both the root handler and a handler on `telethon`.
- A handler on `telethon.network` still matches.
- A user who asks for the sleep lines still gets them.
- Two accounts sleeping at the same time are told apart.

**Two limits remain**, both documented:
- A program-wide `logging.disable(INFO)` stops capture.
- A level change made in the middle of a call stops capture until the next call begins.

The probe is saved as `devdocs/work/4-account-health-events/probe_health_145.py`.

### 10. The other two views: log lines and `health_check()`

The callback, the log lines and the summary are fed from one record, so they cannot disagree.

**Log lines.** Each event is also written to a logger under `tgdata.tgdata` — the logger that tgdata's `log_file` option writes to — so file-logging users receive it.
- WARNING for logged out, banned, restricted and unclassified. These become visible with no setup: with no logging configured at all, Python prints warnings to the console, as it already does for tgdata's discovery warnings.
- INFO for waiting, no access and ok, one configuration line away.
- Attaching a JSON formatter to this logger gives a persistent event log with no new tgdata API.

**`health_check()["health"]`.** tgdata must already remember which scopes are not ok, to know when to send "ok". The summary exposes that memory read-only:
- the account's verdict and since when;
- the open waits, per request type;
- the groups without access;
- the wait count and total wait seconds;
- the last unclassified name.

It answers #4's example, "waited 4 times, 210 s total", without any consumer code. It is per instance and since the instance was built. It is kept in memory, and two instances on one account will differ.

### 11. The prerequisite bug

#4 cannot report a logout truthfully until tgdata's authorization checks tell the truth.

**What Telethon 1.45.0 does today:**
- On the long-lived connection tgdata keeps open, tgdata calls Telethon's `start()`. `start()` asks for the current user. Telethon's `get_me()` returns "nobody" for any authorization error, a ban included.
- `start()` then requests a login code from Telegram and waits for someone to type it.
- With no one at the keyboard, the read fails with "EOF when reading a line".
- On the short-lived connections tgdata opens per operation, Telethon's `is_user_authorized()` turns every Telegram error — including a long wait — into "not authorized".

**What happened.** A downstream scraping service, running an older tgdata, lost its session to a logout. Its loop asked Telegram for a login code 11 times in 70 minutes, until an operator stopped it, and each request reached the account owner. The error it logged was "Failed to authenticate: EOF when reading a line".

**The fix, as its own bug:**
- **Ask Telegram directly** (`GetUsers` or `GetState`) and classify the actual error. That tells a ban, a logout and a wait apart.
- **Never prompt implicitly for a previously logged-in session.** Raise `AuthRequiredError` with Telegram's error attached, and request no code.
- **Keep first login as it is.** A brand-new session still prompts when a terminal is attached.
- **Make re-login after a revocation explicit**, through an opt-in. Its exact API belongs to the bug's own plan.

Why the guard is not "prompt only when a terminal is attached": inside a pseudo-terminal nobody is typing into (tmux, screen, `script`), Python reports a terminal. The probe showed this. A revoked session would then request a code and hang. Under a watchdog that restarts the process, that becomes one code per restart.

Three local signals can tell "previously logged in" from "never logged in", all verified on 1.45.0:
- the session already had an encryption key before connecting;
- Telethon restored a user id from the session;
- the session holds saved update state.

The bug's plan picks one.

**Why it is a separate issue.** CONTRIBUTING.md §4.5 says: "A prerequisite is justified only when it is **smaller and more certain** than the thing it unblocks." This fix is both. It also stops a live harm that should not wait for a larger feature. Per §4.5, #4 is then marked "Blocked by" it and stops being open to implement until it merges.

### 12. What #4 does not include

- **Acting on verdicts.** No pausing, circuit-breaking or admission control. That belongs to #9's budgets and #10's worker, where it can be designed with them.
- **Building #3, #8, #9 or #10.** Their events can join later under their own `kind`.
- **Connectivity as a verdict.**
- **A pull-style event iterator**, or one shared sink for all instances. The per-instance callback is the primitive.
- **Exporting the verdict table** as a public constant. It stays internal: one data table drives the classifier and the tests, and the README lists it.
- **Merging health events with the heartbeat.** The heartbeat lives as long as one call; health lives as long as the instance.

### 13. Found along the way, outside #4

**tgdata's discovery has a pre-existing bug.** Telethon's request method accepts a per-call `flood_sleep_threshold` and never passes it on. This holds in every release from 1.33.1 to 1.45.0; the probe confirmed it on 1.45.0.
- Discovery sends its requests with that threshold set to 0, so that it can manage every wait itself.
- In fact Telethon sleeps through waits of 60 seconds or less. For those, discovery's `max_flood_wait` and its heartbeat during waits do not apply.
- Its docstrings claim otherwise.

This is its own bug. #4 only needs the correct statement in its inventory (section 8).

**The same defect exists upstream in Telethon.** Telethon's bug-report template says "Use your own words. **Do not use AI to write the issue.**" Any upstream report is the user's to write.

## Next Actions

### MUST

- **What:** File the prerequisite bug — truthful authorization checks, and no implicit login-code requests for previously logged-in sessions. Then mark #4 "Blocked by" it, per CONTRIBUTING.md §4.5.
  - **Who:** the maintainer, who approves filing a public issue. The assistant can draft a technical-only body.
  - **Gate:** before #4's implementation starts. #4's description may be written meanwhile.
  - **Why:** it ends a live harm to account owners, and #4's logout reporting depends on it.
- **What:** Write #4's `desc.md` from this finding, in technical terms only. The private sources this inquiry used — a downstream service's logs, a private proposal, local paths — stay out of the public text.
  - **Who:** the assistant, as the next CONTRIBUTING step for #4.
  - **Gate:** after this finding is committed on the `feat/4-account-health-events` branch.
  - **Why:** it is the deliverable this inquiry exists to enable.
- **What:** Decide how `group` is identified inside an event: Telegram's numeric id, or the caller's argument.
  - **Who:** the description or the plan for #4.
  - **Gate:** before the event shape appears in any published text or code.
  - **Why:** recovery matching and per-group totals depend on it, and changing a public field later breaks consumers.

### COULD

- **What:** File the discovery bug — the per-call threshold Telethon ignores — and correct discovery's docstrings.
  - **Who:** the maintainer approves; the assistant can draft it.
  - **Gate:** any time; it is independent of #4.
  - **Why:** discovery's documented wait handling is false for waits of 60 seconds or less.
- **What:** Report Telethon's `__call__` defect upstream.
  - **Who:** the maintainer, in their own words. Telethon forbids AI-written issues.
  - **Gate:** the maintainer's choice.
  - **Why:** a fix upstream would make per-call thresholds work for everyone.
- **What:** Grow the probe's fake connection into a reusable offline test stand-in.
  - **Who:** #4's plan.
  - **Gate:** when #4's plan is written.
  - **Why:** every success criterion becomes testable without Telegram, and a Telethon upgrade that changes the sleep record fails a test instead of silently breaking capture.
  - **Depends-on:** MUST item "File the prerequisite bug". OVERRIDE: the stand-in is useful to the prerequisite bug's own tests, so its value does not wait on that bug's resolution.
- **What:** Decide whether the background-task signals — channel lost during catch-up, catch-up waits — are part of #4.
  - **Who:** #4's description.
  - **Gate:** when #4's description is written.
  - **Why:** the real-time path would report lost groups, not only logouts.
- **What:** Run the classifier and capture tests on Telethon 1.33 as well as on 1.45.0.
  - **Who:** #4's plan.
  - **Gate:** before deciding whether to keep `Telethon>=1.33`.
  - **Why:** it confirms the declared floor, or shows it must rise.

### DEFERRED

- **What:** Admission control or a circuit breaker per account — tgdata withholding calls after a terminal verdict.
  - **Gate:** when #10's worker is designed, or when a retry storm on a terminal verdict other than login codes is observed.
  - **Why (if revived):** it protects accounts from callers that ignore verdicts.
- **What:** A pull-style event iterator and a process-wide sink.
  - **Gate:** when #10's worker needs to pull events instead of receiving callbacks.
  - **Why (if revived):** many accounts per process with one consumer loop.
- **What:** Letting callers add table rows at run time.
  - **Gate:** when a consumer needs a new verdict recognised before a tgdata release can ship it.
  - **Why (if revived):** faster reaction to new Telegram errors.
- **What:** Exporting the verdict table.
  - **Gate:** when a consumer asks for programmatic access to it.
  - **Why (if revived):** one source of truth outside tgdata.
- **What:** Fully explicit authentication, where no login ever happens implicitly.
  - **Gate:** when #8, step-by-step login, is designed.
  - **Why (if revived):** completes what the prerequisite starts.
- **What:** Pacing driven by health events, including a client-wide wait threshold of 0.
  - **Gate:** when #9's per-account budget is designed.
  - **Why (if revived):** waits become a policy tgdata controls.
- **What:** An `Account` object that gathers config, session, proxy, device identity and health.
  - **Gate:** when a second issue among #1, #2, #5, #9 and #10 needs per-account state that does not fit a config path.
  - **Why (if revived):** one home for per-account concerns.

## Reasoning

**Why a side channel and not control.**
- The considered alternatives were a propagating callback, which lets a consumer end a run by raising, and admission control, where tgdata withholds calls.
- A propagating callback fails twice. Two of the event sources — the logging filter, and Telethon's background task — have nowhere to propagate to. And it lets a monitoring bug end a scrape.
- Admission control was tested against the one harm actually observed. That harm, login codes, is removed by the prerequisite. The remaining retries on a dead account send nothing to its owner, so admission control is deferred, not rejected.

**Why three scopes.** A single account-wide state was proposed for simplicity. It was rejected because Telegram issues verdicts at three scopes: one lost group or one throttled request type would mark a working account as broken.

**Why every occurrence, and "ok" only on recovery.**
- Transition-only events were rejected: they lose the wait counts #4's own example needs.
- "ok" on every call was rejected: liveness is the heartbeat's job, and a per-call "ok" carries no verdict.

**Why the fallback by category was dropped.** It was part of the design built on 1.40. Checking 1.45.0's real error list showed both the 401 and the 406 categories hold errors that are not logouts, and the flood-category rule could never fire. The replacement — verdicts only from listed names, "unclassified" bounded by category — keeps every Telegram error visible without inventing verdicts.

**Why a logging filter and not a separate logger per client.** Telethon can route a client's logs to its own logger tree (`base_logger`). The probe showed what that costs:
- it renames every logger of that client, so a user's existing Telethon logging setup stops applying;
- capturing through it still requires enabling INFO, which then leaks the sleep lines to the user's console.

Its one real advantage, attributing signals from Telethon's background task, is reached instead by setting the account variable before `connect()`.

**Why not make every wait raise.** Setting Telethon's wait threshold to 0 would make tgdata handle every wait itself. Two reasons rule it out for #4:
- it changes behaviour at every call site;
- on every release up to 1.45.0 it can only be set client-wide, because the per-call setting is ignored.

It stays a candidate for #9's budgets.

**Why the `severity` field was dropped.** It proposed "terminal" and "degraded" so a dashboard could colour events without knowing the six names. Applied literally, it misdescribes two of six verdicts:
- *no access* does not pass by itself, yet it was "degraded";
- *restricted* may still allow reads, yet it was "terminal".

Corrected, it reduces to "is this a wait?", which the verdict already says. Who must act and how each verdict clears goes into the README's table instead.

**Why the label does not default to the config file's name.** Most users use the default `config.ini`, so the label would read "config" — no identity at all. The session name already identifies the account, and the label is an optional extra for callers who want their own names.

**Why the prerequisite is fail-closed for revoked sessions.** The first design allowed prompting whenever a terminal was attached. The probe showed a pseudo-terminal with nobody typing passes that test. Failing closed for previously logged-in sessions costs an interactive user one explicit step after a revocation, and it removes the remaining way to send codes no one can answer.

**Why a JSON-lines file sink was not added.** The log-line view with a JSON formatter gives the same persistence through standard logging, with no new tgdata API.

**Other directions considered and set aside:**
- one observer object combining heartbeat and health — rejected, because a call and an instance live for different lengths of time;
- pull-only health — rejected, because #4 asks for events;
- raising Telethon's minimum version for correctness — unnecessary, because keying on Telegram's names works on every release;
- an "unreachable" seventh verdict — rejected, because a dead proxy says nothing about the account.

**Earlier claims corrected by the move to 1.45.0:**
- **"The per-call wait threshold works."** It exists and is ignored.
- **"Silent waits can be seen through a per-client logger without side effects."** They cannot (see above).
- **"Restricted is unobservable before Telethon 1.42."** On the 1.45.0 base, the frozen-account errors are classes, and name-keying recognises them on older releases too.
- **"With the log view, the downstream service would have seen every wait with no integration."** False for waits, which are INFO. Serious verdicts are visible by default; waits need one configuration line.
- **"A lost channel during catch-up is only logged."** Still true, and now known to be capturable through the same filter.

## Open Questions

### Monitoring

- **Unclassified names.** After the first downstream service runs a tgdata version with health events, read its unclassified events. Any logout-like or ban-like name there becomes a table row.
- **How often waits happen.** After the first week of reported waits, check whether every wait is worth an event or whether volume needs a note in the docs. Today nothing is known, because no consumer logs INFO.

### Blocked

- **#4's implementation** is blocked until the prerequisite bug merges.
- **The restricted row's read behaviour** is blocked until someone has access to a frozen account, or reports what its reads return.

### Research Frontiers

- **What a frozen account can still read**, and whether continued calls worsen its standing.

### Refinement Triggers

- **The sleep record changes.** If a Telethon release changes `Sleeping%s for %ds (%s) on %s flood wait` or the `telethon.client.users` logger — the offline stand-in will fail — re-open the silent-sleep capture.
- **The per-call threshold starts working.** If a Telethon release forwards `flood_sleep_threshold` from `__call__`, re-open discovery's line in the inventory, and the client-wide-threshold question for #9.
- **A logout or ban arrives unclassified.** If an unclassified event carries a logout-like or ban-like name, add the row.
- **A frozen account is observed reading.** If one reads successfully, re-check that "restricted" recovers only on the refused request type and does not flip.
- **Telethon 2.x becomes the latest stable release.** Re-verify the whole fact base: the capture relies on 1.x internals (`_call`'s logging, `_log`, `rpc_errors_dict`).

## Source Input

<details>
<summary>Raw user input for this finding</summary>

```text
Issue #4 in karaposu/tgdata, branch feat/4-account-health-events. Write all output to devdocs/work/4-account-health-events/traverse/ (CONTRIBUTING.md §5: traverse output lives in traverse/ on the branch and becomes the raw material for desc.md). The question: what should "report account health states as events" mean inside tgdata, concretely — (1) the state set (ok, waiting, logged out, banned, restricted, no access): which Telegram signals map to each, including waits Telethon sleeps through silently (≤ flood_sleep_threshold, only logged on telethon.client.users) and what "restricted" can mean for an account that only reads, given Telethon 1.40 has no reading-side restriction error and lacks the frozen-account errors; (2) the event's shape — time, account (tgdata only knows a config path and session name), group, the call that caused it (RPCError.request), wait length — and whether "ok" is emitted per call or only on transitions; (3) where events must be emitted: the persistent connection path (which answers a logout with Telethon's interactive start() and a login-code request), the use-and-close client (whose is_user_authorized() turns any RPC error, flood waits included, into 'not authorized'), the fetch loop, discovery's per-item skips, the poll loop that swallows every error, and the real-time updates loop (which disconnects on a logout and re-raises it from run_until_disconnected); (4) callback semantics — exception-safe like heartbeat, or propagating like found_callback/batch_callback; (5) scope: whether fixing the headless-login bug belongs in #4 or only reporting it. Inputs already on the branch: devdocs/work/4-account-health-events/triage.md (the surfacing record). Consumers to keep in view: issues #3 (pause an account on a failed proxy check), #8 (step-by-step login), #9 (per-account budget), #10 (worker that emits health events). Goal for the onward route-field (_branch.md): a stable, decided meaning from which desc.md for #4 can be written.
```

Mid-inquiry direction (2026-10-03, during the critique):

```text
Use the latest Telethon release, and and like understand what we want to build based on the latest telethon.
```

</details>
