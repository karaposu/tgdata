---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

devdocs/work/4-account-health-events/traverse/_branch.md — inputs in that folder: innovation.md (the candidates, the assembled shape "one ledger, three views", and two RE-TEST TRIGGERS: C2's logging mechanics and sensemaking A6), sensemaking.md (SV6 and open items A6, A9b, A13b, A14), decomposition.md (P0–P4c, I1–I8, Q4b, Q3, Q0), articulate_warm.md, surfacing.md. Judge the candidates against the goal in _branch.md: a stable, decided meaning from which desc.md for #4 can be written. Settle what can be settled by evidence (Telethon 1.40 in this repo's .venv, Python logging behaviour) rather than by argument. SAVE the output as devdocs/work/4-account-health-events/traverse/critique.md

**User direction given during this critique (2026-10-03):**
> "Use the latest Telethon release, and and like understand what we want to build based on the latest telethon."

---

# Critique — account health events, on Telethon 1.45.0

## The baseline moved

The user redirected this pass from Telethon 1.40 to the latest release. That release is **Telethon 1.45.0**, published to PyPI on 2026-09-10. No 2.x release exists on PyPI.

- **The repository's venv moved from 1.40.0 to 1.45.0.** It stays inside `setup.py`'s range (`Telethon>=1.33,<2.0`). To roll back: `.venv/bin/pip install telethon==1.40.0`.
- **tgdata still works on it.** Both offline smoke tests pass: proxy (`test_12`, 7 of 7) and device identity (`test_13`, 6 of 6).
- **Every Telethon fact this critique relies on was re-verified on 1.45.0.** Where older versions matter, six releases were compared: 1.33.1, 1.34.0, 1.40.0, 1.42.0, 1.44.0 and 1.45.0.

The prompt above still names Telethon 1.40. The user's direction replaces that part, and the rest of the brief stands.

## Evidence base — external anchors

| # | Anchor | Result |
|---|---|---|
| E1 | PyPI release data | 1.45.0 is the latest stable release. 1.41 to 1.45 appeared between 2025-09 and 2026-09. |
| E2 | Telethon changelog, 1.41 to 1.45 (Codeberg, `v1` branch) | More error classes in 1.41 and 1.43. In 1.43: "Any RPC error should now be treated as a transient error while getting difference", a warning for a proxy without `python-socks`, and "The project now has a policy against AI." |
| E3 | Converting sample Telegram errors on 1.45.0 | Every candidate table row is a class. A known class's `.message` holds only its category. An unknown error becomes its category's base class with Telegram's raw name in `.message`. |
| E4 | The 401 and 406 families on 1.45.0 | Besides the logouts, the 401 family holds `SESSION_PASSWORD_NEEDED`, `AUTH_KEY_PERM_EMPTY` and `ACTIVE_USER_REQUIRED`. The 406 family holds `FILEREF_UPGRADE_NEEDED`, `STICKERSET_OWNER_ANONYMOUS`, `USERPIC_PRIVACY_REQUIRED`, `PHONE_PASSWORD_FLOOD` and others, with `AUTH_KEY_DUPLICATED` as its only logout. |
| E5 | `UserMethods.__call__` in all six releases | It accepts `flood_sleep_threshold` and never forwards it. The sleep after a flood error compares against the **client's** threshold. The runtime confirms it (probe S10, S11). |
| E6 | The sleep record in all six releases | The message is the same everywhere: `'Sleeping%s for %ds (%s) on %s flood wait'`, logged on `telethon.client.users`. That logger only ever writes INFO and WARNING. |
| E7 | `probe_health_145.py`, run offline on 1.45.0 | All 17 checks pass (S1–S11). It drives Telethon's real request path with a fake connection. |
| E8 | Login path on 1.45.0 | `get_me()` returns `None` on any `UnauthorizedError`, a ban included, after which `start()` calls `send_code_request()` and then `input()`. `is_user_authorized()` turns every `RPCError` into "not authorized". |
| E9 | Updates loop on 1.45.0 | A logout or ban stops the loop and is re-raised from `run_until_disconnected` — only for a session "once logged in". Two other signals are only INFO log lines: a wait while catching up, and "Account is now banned in %d". Telethon creates this task inside `connect()`. |
| E10 | Terminal test | `isatty()` is False under `</dev/null` and under a pipe. It is **True** inside a pseudo-terminal nobody is typing into. `input()` on `/dev/null` raises `EOF when reading a line` — the exact text of the observed login-code storm. |
| E11 | CONTRIBUTING.md §4.5 | "A prerequisite is justified only when it is **smaller and more certain** than the thing it unblocks." |
| E12 | tgdata conventions | **Heartbeat:** sync-only, and its errors are swallowed silently. **`found_callback`:** sync or async, detected with `inspect.isawaitable`. **Callback names** end in `_callback`. **`log_file`** attaches only to the `tgdata.tgdata` logger. tgdata installs no `NullHandler`. |
| E13 | Telethon's bug-report template (Codeberg) | "Use your own words. **Do not use AI to write the issue.**" |

---

## Phase 0 — Dimensions

| # | Dimension | Weight | What passing looks like | Substance or external-anchor criterion |
|---|---|---|---|---|
| D1 | **Truthful verdicts** | critical | Every event names the verdict Telegram actually gave. Nothing is invented, and nothing ordinary is promoted to a verdict. | *Substance:* apply the mapping literally to 1.45.0's real error list (E4). *Anchor:* 1.45.0's conversion (E3). |
| D2 | **Observer safety** | critical | Nothing a caller relies on changes: exceptions, control flow, timing, or what their logging prints. A broken callback breaks nothing. | *Anchor:* the probe (E7). |
| D3 | **No harm to the owner** | critical | No outward action on the account, such as a login-code request, without a human asking. | *Anchor:* the storm's EOF text and the terminal probe (E10). |
| D4 | **Complete capture** | high | Every verdict tgdata sees becomes an event attributed to the right account, including silent sleeps and background-task signals. | *Anchor:* E6, E9, probe S6–S7. |
| D5 | **Consumer fit** | high | Serves #4's per-account totals and #10's many accounts per process moving between machines. Leaves room for #3, #8 and #9. | *Substance:* run #4's two examples through the design. |
| D6 | **Fit with tgdata's conventions** | medium | Callback naming, sync/async handling, the one client door, logging habits. | *Anchor:* E12. |
| D7 | **Small public surface** | medium | Only additive API; nothing exported without a consumer. | — |
| D8 | **Version robustness** | medium | Correct on 1.45.0, the base, and not wrong on the declared floor (1.33). This weighed high on the 1.40 baseline, and the user's direction lowers it. | *Anchor:* the six-release comparison (E5, E6). |
| D9 | **Process fit** | medium | CONTRIBUTING §4.5 for prerequisites; public text stays technical. | *Anchor:* E11, E13. |

**Validation.**
- **Perspective cross-check.** Every sensemaking perspective has a dimension:
  - technical → D1, D4, D8;
  - human → D3, D5;
  - strategic → D5, D7;
  - risk → D2, D3;
  - resource → D7;
  - ethical → D3;
  - definitional → D1;
  - phase and calibration → D8.
- **Project-specific risk.** D2 carries the documented project risks: one client door, no logging side effects, additive change. D9 carries the process.
- **Axis absence.**
  - (i) *Upstream inheritance:* the logging axis came from decomposition's hidden coupling, and the background-task axis was found here (E9). Both are now covered by D4.
  - (ii) *Narrowest reading:* "observer safety" is taken in its broad reading — logging output and timing too, not only exceptions.
  - (iii) *Self-defeating wording:* none.
- **"If a candidate passed all nine, would it solve the problem?"** Yes. D1 and D4 make the events true and complete, D3 removes the live harm, D2 keeps today's callers whole, and D5 makes the result usable.

### Frame-premise test

The candidate space rests on SV6. Four load-bearing premises, each prosecuted on its own:

- **FP1 — health events are a read-only side channel; tgdata takes no action on verdicts.**
  - *If wrong:* consumers keep hammering terminal accounts.
  - *Evidence:* the one outward harm, login codes, is removed by the prerequisite. A retried call on a logged-out or banned account sends nothing to the owner.
  - *Residual:* frozen accounts. 1.45.0 documents `FROZEN_PARTICIPANT_MISSING` as "Your account is frozen and can't access the chat", so frozen accounts do lose chat access. Whether further calls worsen their standing is unknown.
  - **Holds.** Admission control stays deferred (see I1).
- **FP2 — Telethon's sleep record is a stable way to observe silent waits.**
  - *If wrong:* capture fails silently after an upgrade.
  - *Evidence:* the message and logger are identical in all six releases from 1.33.1 to 1.45.0 (E6).
  - **Holds**, with a canary test (A1) that fails if Telethon changes the record.
- **FP3 — mapping keys on Telegram's error identity, with a careful fallback by category.**
  - *If wrong:* ordinary errors become verdicts.
  - *Evidence (E4):* on 1.45.0 the 406 family is mostly not about authorization, and the 401 family holds a two-step-password prompt and a temporary-key error. A fallback by category reads `FILEREF_UPGRADE_NEEDED` during a media download as "logged out". The 420 fallback "waiting only with seconds" never fires, because an unknown 420 never carries seconds (E3).
  - **The identity half holds. The fallback half fails.** This is refined below as M1.
- **FP4 — Telethon 1.40 is the reference.**
  - *If wrong:* the design is tuned to an outdated library.
  - **Replaced by the user's direction:** 1.45.0 is the base. The consequences are listed under "Corrections to earlier claims".

---

## Phase 1 — Landscape

- **Viable.**
  - A side channel fed by one classifier keyed on Telegram's exact error names, with no verdict ever taken from a category.
  - Silent waits captured where Telethon logs them, without renaming loggers or changing what users see.
  - Delivery that never breaks the operation.
  - A prerequisite that fails closed for previously logged-in sessions.
- **Dead.**
  - Verdicts taken from a category (D1).
  - Anything that renames Telethon's loggers, or enables INFO where it reaches users' consoles (D2).
  - A login guard that depends only on a terminal test (D3, E10).
  - Fields derived from verdicts whose meaning cannot be checked (D1).
- **Boundary.**
  - Acting on verdicts. Valuable for #9 and #10, but it changes control flow.
  - Exporting the table. Useful, but a new surface without a consumer.
- **Unexplored.**
  - Behaviour of a frozen account on reads (A9b). It needs a frozen account, which no one has. No candidate can enter this region by argument.

---

## Phase 2 + 3 — Adversarial evaluation and verdicts

Full adversarial testing runs on the candidates that reached critique as actionable or as re-test triggers, and on three refinements this pass surfaced. Innovation's deferred and rejected candidates are screened afterwards.

### Q4b — how silent waits are captured

**C2 — a filter on Telethon's own `telethon.client.users` logger, plus context variables (RE-TEST TRIGGER 1).**
- **Prosecution.**
  - The sleep record only exists if that logger is enabled for INFO.
  - Enabling INFO lets the line reach a user's console handler.
  - Telethon's background updates task has no tgdata call around it.
  - A user can later re-configure logging and silently kill the capture.
- **Defense.** The probe settles every point (E7):
  - **S2.** A *filter*, not a handler, sees each record before any handler does. It captures the sleep and passes on only what the user's own levels would pass. The sleep is captured with account, call, request type and seconds. No INFO reaches the root handler. Telethon's warnings still reach both root and the user's `telethon` handler, and a handler on `telethon.network` still matches.
  - **S3, S4.** A user who wants the lines still gets them — whether they set INFO on `telethon.client.users` after tgdata, or on `telethon`.
  - **S6.** Two accounts sleeping at once are attributed correctly.
  - **S7.** Telethon creates its updates task inside `connect()`, so the task inherits the caller's context and would pin a finished call to later sleeps (S7a). Clearing the call variable around `connect()` keeps the account and drops the stale call (S7b).
  - **S8.** `dictConfig(disable_existing_loggers=True)` disables the logger. A check at each call boundary restores capture while keeping the logger silent for the user.
  - **Sentinel level.** tgdata sets level 19, one below INFO, which no user sets by name. Any user change is therefore detectable.
- **Collision.**
  - Only two limits remain: a process-wide `logging.disable(INFO)`, and a level change made in the middle of a call. Each stops capture until the next call boundary.
  - These are rare and can be documented. The defense wins on D2 and D4.
- **Verdict: SURVIVE** — validated by the probe. Caveat: the two limits above go into the docs.

**Per-client `base_logger`.**
- **Prosecution (E7, S5).**
  - The client's warnings land on `tgdata.acct.A.client.users`, which the user's `telethon` handler never sees.
  - Capturing still needs INFO enabled on that logger, which leaks the sleep line to root.
  - Making it safe needs a forwarding bridge that re-implements the user's level checks.
- **Defense.** Exact attribution of signals from Telethon's background tasks.
- **Collision.**
  - The defense's only advantage is reproduced by the account context variable, which `connect()` hands to the background task (S7b).
  - The prosecution wins on D2.
- **Verdict: KILL.**
  - *Seed:* per-client attribution was the real need, and the account context variable set before `connect()` meets it without renaming anything.

**K4 — flood threshold 0 everywhere.**
- **New evidence (E5).** On every release from 1.33.1 to 1.45.0, the per-call threshold is ignored. Only the client-wide attribute works (S10, S11), so K4 could only be client-wide — a behaviour change for every call.
- **Verdict:** stays a **RESEARCH FRONTIER for #9's budget**. It is dead for #4.

### Q3 — delivery from synchronous contexts

**The rule.** Call the callback. If the result is awaitable:
- **In async code** (the call boundary, the poll loop, the engines' wait handlers, discovery's skips), await it, with errors contained.
- **From the logging filter**, the only synchronous source, schedule it as a task. Keep a strong reference, and contain errors in a done-callback.

**Verdict on the rule.**
- **Prosecution.**
  - Awaiting a slow callback stalls the call.
  - Scheduling everything instead would lose events: a task scheduled just before `asyncio.run` returns is cancelled (S9b). That would drop exactly the terminal "logged out" or "banned" event a program exits on.
- **Defense.**
  - S9a: an async callback scheduled from the filter runs during Telethon's own sleep, which follows the log line immediately. Its error is contained.
  - Awaiting inline is what `found_callback` already does (E12).
- **Collision.** Await where possible, schedule only from the filter. Every event that ends an operation is delivered before the exception propagates.
- **Verdict: SURVIVE.**
- **Constructive notes.**
  - Detect sync versus async the way `_notify` does (`inspect.isawaitable`) (D6).
  - Unlike heartbeat's silent `pass`, log a callback error: the first at WARNING with its traceback, repeats at DEBUG, so a broken callback cannot flood the log.

**I3 — a pull iterator.**
- *Prosecution:* a second delivery API before any consumer needs pull.
- *Defense:* no sync/async problem.
- *Collision:* Q3's rule already solves dispatch.
- **Verdict: DEFERRED** (innovation's trigger stands: #10's worker).

### P0 / Q0 — the prerequisite

**I5 — package the authorization fix as its own bug.**
- **Prosecution.** #4 cannot report logouts truthfully without it, so splitting adds a dependency.
- **Defense.**
  - §4.5 (E11): the fix is smaller and more certain than #4.
  - It ends a live harm: 11 codes in 70 minutes.
  - Bundling would hold that harm fix back until a heavy feature ships.
- **Verdict: SURVIVE.** Shape: REFRAME-AS-BUG, with #4 **blocked by** it, per §4.5's rules.

**The terminal-only guard** (sensemaking A14 as written: with a terminal, re-login stays interactive).
- **Prosecution (E10).**
  - Inside a pseudo-terminal nobody types into (tmux, screen, `script`), `isatty()` is True.
  - A revoked session then requests a code and blocks on `input()`.
  - Under a watchdog that restarts the process, that becomes one code per restart.
- **Defense.**
  - In the observed storm stdin was at EOF, so this guard would have stopped it.
  - Interactive users keep today's prompt.
- **Collision.**
  - The guard's purpose — "never request a code no one can answer" — fails in a reachable headless setup.
  - Purpose-fitness: as the *only* guard, it does not do its job.
- **Verdict: REFINE.** Absorbed into L2.

**L2 — previously logged-in sessions never prompt implicitly.**
- **Prosecution.**
  - An interactive user whose session was revoked gets `AuthRequiredError` instead of today's prompt.
  - "Previously logged in" must be detected somehow.
- **Defense.**
  - It fails closed in every headless setup, the terminal false positive included.
  - It keeps first login unchanged where a terminal exists.
  - It is #8's first step.
- **Detection (verified on 1.45.0).**
  - Ask Telegram directly (`GetUsers` or `GetState`), not through `get_me()` or `is_user_authorized()`. That tells a ban from a logout from a wait (E8).
  - Three local signals distinguish "previously logged in":
    - (a) the session had an auth key before `connect()`;
    - (b) the self id Telethon restores at `connect()`;
    - (c) a saved update state, Telethon's own `was_once_logged_in`.
- **Verdict: SURVIVE** as P0's direction.
- **Constructive notes.**
  - P0's own plan picks the discriminator and an explicit opt-in for interactive re-login.
  - The cost to interactive users is one explicit step after a revocation.

### P1 — the mapping

**M1 — one key space, Telegram's own names, and no verdict from a category.** This is a refinement of sensemaking A8, surfaced by FP3.
- **Prosecution.** Dropping the fallback means a new logout error is reported as "unclassified", not "logged out".
- **Defense.** E4 shows the fallback would invent verdicts. "Unclassified" still fires, with the name, so nothing goes silent, and the table grows from evidence (sensemaking PH1).
- **Collision.**
  - D1 is critical, and D4 is still met because the unclassified event fires.
  - "Unclassified" itself needs a bound. 1.45.0 knows 515 error names, most of them ordinary bad input.
- **Verdict: SURVIVE**, with this shape:
  - **Key.** Telegram's wire name.
    - For known classes it is read from Telethon's own tables, `rpc_errors_dict` and `rpc_errors_re`, both present on 1.45.0.
    - For unknown errors it is read from `.message`.
    - This gives the same table on 1.33 and on 1.45.0 (D8).
  - **Verdicts only from listed names.** The 1.45.0 table:
    - *waiting* (method): `FLOOD_WAIT_X`, `FLOOD_PREMIUM_WAIT_X`, `SLOWMODE_WAIT_X`, `FLOOD_TEST_PHONE_WAIT_X`, with seconds.
    - *logged out* (account): `AUTH_KEY_UNREGISTERED`, `SESSION_REVOKED`, `SESSION_EXPIRED`, `AUTH_KEY_INVALID`, `AUTH_KEY_DUPLICATED`.
    - *banned* (account): `USER_DEACTIVATED_BAN`, `USER_DEACTIVATED`, `PHONE_NUMBER_BANNED`.
    - *restricted* (account): `FROZEN_METHOD_INVALID`, `FROZEN_PARTICIPANT_MISSING`, `USER_RESTRICTED`, `PEER_FLOOD`. 1.45.0's own text for `PEER_FLOOD`: "account-wide with no defined duration".
    - *no access* (group): `CHANNEL_PRIVATE`, `CHAT_FORBIDDEN`, `CHANNEL_INVALID`, `USER_BANNED_IN_CHANNEL`, `CHANNEL_PUBLIC_GROUP_NA`, **`CHANNEL_BANNED`** (new: "The channel is banned"), and tgdata's `GroupAccessError`.
  - **"Unclassified"** covers unlisted errors in the 401, 403, 406 and 420 categories, where account verdicts live. File-reference errors are excluded.
    - Unlisted 400s (bad input) and 5xx (server) produce no health event.
    - The category decides *whether* to report, never *which verdict*.
    - `CHAT_RESTRICTED` stays unclassified until it is observed: "cannot be used in that request" does not say what a reader loses.

**A2 + E1a — the table as an exported data constant.**
- *Prosecution:* exporting the table makes its row format a public contract with no consumer.
- *Defense:* one source for the classifier, the tests and the docs.
- *Collision:* the single source needs data, not export.
- **Verdict: REFINE.** Absorbed: an internal data table that drives the classifier and the tests, and is listed in the README. Export is deferred until a consumer asks.

**E1b — runtime table extension.** **DEFERRED**, confirmed. "Unclassified" plus a release covers it for now.

### P2 — the envelope and identity

**D3 — a `severity` field.**
- **Prosecution (substance, applied literally).** The proposed levels put *no access* under "degraded, will pass", but losing a group does not clear by itself. They put *restricted* under "terminal", yet a frozen account may still read (A9b). Two of six verdicts are misdescribed, and the field is a pure function of the verdict anyway.
- **Defense.** A dashboard could colour events without knowing the six names.
- **Collision.**
  - The field's purpose, acting without knowing the names, fails on two of six rows.
  - Fixing it gives "clears by itself", which is true only of *waiting*, so it reduces to `verdict == "waiting"`.
- **Verdict: KILL.**
  - *Seed:* the README's verdict table states, for each verdict, who has to act and how it clears. That is documentation, not a field.

**O6 — label defaults to the config file's stem (A13b).**
- **Prosecution.** The README's default config is `config.ini`, so the default label would be "config" for most users — no identity at all.
- **Defense.** The pool convention of one `<name>.ini` per account would give useful labels.
- **Collision.** The session stem already carries that identity.
- **Verdict: REFINE.** Absorbed:
  - **`account.session`** — the session file's **stem**, never a path. Always present.
  - **`account.label`** — an optional caller-given string, default `None`. Its constructor name follows E12's plain-noun style: **`account_label=`**.
  - **`account.user_id`** — the self id Telethon restores at `connect()`, when available.
  - *Spec gap for the plan:* the user id is read through a private property, or stays `None` until tgdata's own `get_me()` runs.
- **The callback's name** follows E12 too: **`health_callback=`**.

### P3 — recovery and the state view

**Recovery for *restricted*** — a substance-axis refinement of decomposition Q3.
- **Prosecution (applied literally).**
  - Q3 says the account scope recovers on the first successful authorized call.
  - A frozen account that can still read would then flap — restricted → ok → restricted — on every mixed run.
- **Verdict: REFINE.** Absorbed:
  - **restricted** recovers only when the refused request type later succeeds.
  - **logged out** recovers when authorized again.
  - **banned** cannot recover inside an instance, because no call succeeds.
  - **Waits slept in a background task**, with no call, are occurrences only: they open no scope that needs recovery.

**A6 / D1 + E2 + A4 — a state view in `health_check()` (RE-TEST TRIGGER 2).**
- **Prosecution.** #4 asks for events, not state. Two instances on one account will disagree. Memory grows with groups that errored.
- **Defense.**
  - P3 must already keep the non-ok scopes to send "ok" on recovery (sensemaking A4). Exposing them is one read-only copy.
  - The counters answer #4's own example ("waited 4 times, 210 s total") without consumer code.
  - Growth is bounded by the groups that ever returned a verdict.
- **Collision.** It is near-free and serves D5. The disagreement is resolved by saying "per instance, since construction, in memory".
- **Verdict: SURVIVE.** Sensemaking A6 moves from LOW to decided: `health_check()["health"]` holds:
  - the account verdict and since when;
  - the open method waits;
  - the groups without access;
  - wait count and total seconds;
  - the last unclassified name.

### The other views

**L3 — mirror each event on a logger.**
- **Prosecution.**
  - Innovation claimed the consumer "would now see every wait". At INFO, a WARNING-level consumer sees none of them.
  - `log_file` attaches only to `tgdata.tgdata` (E12), so a `tgdata.health` logger would miss `log_file` users.
- **Defense.**
  - Terminal verdicts become visible with zero integration, through tgdata's existing logging habit. With no logging configured at all, Python's last-resort handler prints them, as it already prints tgdata's discovery warnings.
  - One line of config turns on waits alone, without all of Telethon's INFO.
  - A JSON formatter on that logger gives persistence (K2) with no new API.
- **Verdict: SURVIVE**, corrected:
  - **Name:** under the logger `log_file` writes to (`tgdata.tgdata.health`).
  - **WARNING** for logged out, banned, restricted and unclassified.
  - **INFO** for waiting, no access and ok.
  - **The claim becomes:** terminal verdicts are visible by default, and waits are one opt-in line away.

**K2 — a built-in JSONL sink.** **KILL**, superseded by L3.
- *Seed:* persistence through standard logging handlers needs no tgdata API.

**A1 — fault-injection stand-in.**
- *Prosecution:* test code that could drift from Telethon.
- *Defense:* `probe_health_145.py` is the working prototype. It drives Telethon's **real** request path offline, so it fails when Telethon changes the sleep record or the threshold behaviour — the FP2 canary.
- **Verdict: SURVIVE.**

### Screened candidates

| Candidate | Screen verdict | Why |
|---|---|---|
| I1, I1b, D2 (admission control, circuit breaker) | DEFERRED, confirmed | FP1 holds. Revisit at #10's design or on a non-login retry storm. |
| C3 (never-implicit authentication) | DEFERRED to #8 | L2 is its first step. |
| A3 (Account object) | RESEARCH FRONTIER | Spans #1, #2, #5, #9 and #10. Purpose is ambiguous for #4. |
| E3 (closed-loop pacing) | RESEARCH FRONTIER | #9's scope. |
| C1 (one observer object) | rejected, confirmed | Call lifetime vs. instance lifetime. |
| I2 (pull only) | rejected, confirmed | #4 asks for every occurrence. |
| I4 (one scope) | rejected, confirmed | A lost group would mark a working account as broken. |
| K3 (raise the Telethon floor) | rejected for correctness | M1's wire-name key works on every release. Whether the *declared* floor moves to 1.45 is a packaging decision for the plan. Recommendation: build and test on 1.45.0, keep the floor. |
| L1 (process-wide sink) | DEFERRED | The C2 filter is already process-wide inside tgdata. The public API stays per instance. |

---

## Phase 3.5 — Assembly

**Candidate: one ledger, three views, on Telethon 1.45.0**, with every refinement above folded in.

- **Prosecution.**
  - Three views mean three surfaces: the callback parameter, the `health` key, and a logger name.
  - #4 asked for one.
- **Defense.**
  - They are one data flow: classifier → ledger → callback, log line and state. They cannot disagree.
  - The ledger has to exist for recovery anyway.
  - Each view serves a different reader: code, people reading logs, and pollers.
  - #4's two examples are answered with no consumer code. "Waited 4 times, 210 s total" comes from the state view. "Banned at 14:02" comes from the WARNING log line or the callback.
- **Collision.**
  - The surface is three names. None of them changes existing behaviour (D7 met).
  - The emergent value — consistency and zero-integration visibility — exists only in the assembly.
- **Verdict: SURVIVE** — clean on every critical dimension.

## What #4 builds, on Telethon 1.45.0

**Health events** are tgdata's report of every time Telegram says no to an account: which verdict, about what, from which call, for how long, and when it ended. tgdata reports and never acts.

1. **Verdicts.** Six verdicts at three scopes:
   - *account* — logged out, banned, restricted, ok;
   - *method* — waiting;
   - *group* — no access.

   Plus *unclassified* for unlisted errors in the 401, 403, 406 and 420 categories. Verdicts come only from M1's list of Telegram names, never from an error's category.
2. **Event.** Plain, JSON-ready data with these fields:
   - `kind` = `"health"` and `time`;
   - `account` — `label`, the session stem, and `user_id` when known;
   - `verdict`, `scope`, `group` and `call`;
   - `wait_seconds` and `error`, Telegram's name;
   - `source` — error, sleep, auth or updates.

   "ok" is sent when a scope recovers. *restricted* recovers only when the refused request type succeeds.
3. **Delivery.** `TgData(..., health_callback=fn, account_label=...)`. The callback may be sync or async and is exception-safe. It is awaited where tgdata is in async code, and scheduled only from the logging filter. Events that end an operation arrive before its exception.
4. **Capture.**
   - The public-call boundary classifies escaping errors and re-raises them unchanged.
   - The engines report the waits they handle themselves. Discovery's are only the waits above 60 s, since its per-call threshold of 0 is ignored (E5).
   - Telethon's silent sleeps are seen through a filter on `telethon.client.users`. The account comes from a context variable that Telethon's background tasks inherit at `connect()`, and the call variable is cleared there.
   - The poll loop, discovery's skips and the real-time path report what they swallow or re-raise.
   - The authorization checks report once the prerequisite lands.
   - Background signals that are only log lines can be added through the same filter on `telethon.client.updates`: "Account is now banned in <channel>", and waits while catching up.
5. **Views.**
   - the callback;
   - WARNING and INFO lines on `tgdata.tgdata.health`;
   - `health_check()["health"]` — current verdicts and counters, per instance.
6. **Prerequisite** — its own bug, which #4 is blocked by. tgdata asks Telegram directly whether a session is authorized, so it tells a ban, a logout and a wait apart. A session that was logged in before never prompts implicitly: it raises `AuthRequiredError` with Telegram's error attached. First login keeps the terminal prompt. Re-login after a revocation needs an explicit opt-in.
7. **Tests.** An offline stand-in drives Telethon's real request path, as the probe does, and doubles as an upgrade canary.

**Still open, for the plan:**
- **A9b** — which reads a frozen account fails. It can only be observed.
- **The user id's source** — a private property, or `None` until `get_me()`.
- **Group keys** — normalize them, so no-access recovery matches across an id and a username.
- **P0's choices** — its discriminator and its opt-in API.
- **The declared floor** — whether it moves.

## Corrections to earlier claims

| Earlier claim | Where | Correction |
|---|---|---|
| "The per-call `flood_sleep_threshold` parameter exists (verified)" | session 1 discovery work; sensemaking A12 relies on threshold behaviour | It exists and is **ignored**. `__call__` never forwards it, in every release from 1.33.1 to 1.45.0 (E5, S10). tgdata's discovery docstrings ("Telethon never sleeps silently", "a wait here is never slept") are wrong for waits of 60 s or less. |
| Fallback: "unauthorized or auth-key family → logged out; `FloodError` → waiting only with seconds" | sensemaking A8, decomposition Q1 | Wrong on 1.45.0: both families hold non-logout errors (E4), and the 420 rule never fires (E3). Replaced by M1. |
| Silent waits through a per-client `base_logger`; "global log levels and propagation are left as they are" | sensemaking A12, C3, SV6 | That approach renames every logger of the client and leaks INFO once it is enabled (S5). Replaced by the C2 filter. |
| "Restricted is unobservable on 1.40; the frozen classes exist only from 1.42" | articulate_warm, sensemaking A9 | On the base (1.45.0) the frozen errors are classes. The wire-name key also recognizes them on older releases. |
| "The consumer would see every wait with zero integration" | innovation, assembly | False for waits at INFO. Terminal verdicts are visible by default; waits need one opt-in line. |
| "With a terminal, interactive re-login stays available" as the headless guard | sensemaking A14, decomposition Q0 | A pseudo-terminal nobody types into passes the terminal test (E10). L2 replaces it for previously logged-in sessions. |
| Updates-loop logouts: "a lost channel during catch-up is only logged" | sensemaking C7 | Still true on 1.45.0, and capturable: the INFO record "Account is now banned in %d" carries the channel id, and a filter can attribute it (S7b). |

## Findings outside #4 — for the route-field

- **A bug in tgdata's discovery (pre-existing, from the discovery work).**
  - The per-call threshold of 0 does nothing, so waits of 60 s or less are slept silently inside Telethon.
  - In that case `max_flood_wait` and the heartbeat during waits do not apply, and the docstrings overstate the behaviour.
  - This is its own bug issue; the fix is not decided here.
- **The same Telethon bug, upstream.** `__call__` drops `flood_sleep_threshold`. Telethon's template says "Do not use AI to write the issue" (E13), so any upstream report is the user's to write in their own words.
- **Optional:** clients that never listen for updates could pass `receive_updates=False`, which avoids a background task per use-and-close client.

---

## Phase 4 — Coverage, convergence, signal

**Coverage map**

| Region | Candidates evaluated | Status |
|---|---|---|
| silent-wait capture | C2, per-client logger, K4 | settled by probe |
| dispatch | the Q3 rule, I3, C1, L1 | settled by probe |
| prerequisite | I5, terminal-only guard, L2, C3 | settled by E8, E10, E11 |
| mapping | M1, A2, E1b, K3 | settled by E3, E4 |
| envelope and identity | D3, O6, the callback name | settled by E12 |
| recovery and state | restricted recovery, A6, I2, I4 | settled |
| views | L3, K2, A1 | settled |
| acting on verdicts | I1, I1b, D2, E3, A3 | deferred or frontier, with triggers |
| frozen-account reads (A9b) | none possible | **unexplored — needs observation** |

**Accumulator**
- **Evaluation log:** 23 innovation candidates, plus three refinements surfaced here (M1, restricted recovery, the terminal-only guard), plus the assembly. 27 verdicts in all.
- **Kill record:**
  - per-client logger, killed on D2 (E7 S5);
  - severity, on D1 (substance);
  - JSONL sink, superseded by L3;
  - the fallback by category, on D1 (E4) — inherited from sensemaking, killed via FP3.
- **Refinement record:** all five REFINEs — the table, the label, restricted recovery, the terminal-only guard, the fallback — were fully specified by evidence and absorbed. None needs another innovation pass.
- **Mechanism independence:** **validated**. The survivors cite external anchors: Telethon 1.45.0 source and runtime, PyPI, the changelog, CONTRIBUTING §4.5, the storm's log text and the terminal probe.

**Signal: TERMINATE** for the meaning. Ranked survivors:
1. the assembly — one ledger, three views, on 1.45.0;
2. C2 filter capture;
3. P0 as L2, packaged by I5;
4. M1 mapping;
5. the Q3 dispatch rule;
6. the A6 state view;
7. L3 mirror;
8. A1 stand-in;
9. O6 identity, refined;
10. A2 internal table, refined.

**Convergence telemetry**
- **Dimension coverage:** 9 of 9, with every critical dimension tested against an external anchor.
- **Adversarial strength:** STRONG. Three kills and one inherited commitment overturned, all by evidence.
- **Landscape:** CHANGED this pass, by the baseline switch and the evidence. The changes are refinements inside the surviving frame; no viable region appeared outside it.
- **Clean SURVIVE:** yes — the assembly, with no caveat on a critical dimension.
- **Strict criterion not met:** "two consecutive iterations without new regions" cannot be met in a single pass. The residue is plan-level detail plus A9b, which no iteration can settle without a frozen account. A second loop would only re-confirm.
- **Failure modes:**
  - *External-grounding absence* was prevented: FP3 was overturned only because 1.45.0's real error list was checked.
  - *Rubber-stamping:* no — there are kills.
  - *Nitpicking:* no — every kill is on a critical dimension.
  - *Evaluation drift:* not applicable, as this is the first pass.
- **Output: PROCEED.**

## Appendix — the probe

`devdocs/work/4-account-health-events/probe_health_145.py`, run offline with the repository's venv (Telethon 1.45.0, Python 3.11.10):

```
[PASS] S1  a 1 s Telethon sleep is invisible under basicConfig (root WARNING)
[PASS] S2a sleep captured with account, call, request type and seconds
[PASS] S2b no INFO line reaches the root console handler
[PASS] S2c Telethon WARNINGs still reach root and the user's 'telethon' handler
[PASS] S2d a user's handler on 'telethon.network' still matches that client's network logs
[PASS] S3  user's own INFO on telethon.client.users still prints the sleep, and tgdata captures it
[PASS] S4  user's INFO on 'telethon' still prints the sleep, and tgdata captures it
[PASS] S5a with base_logger the client's warnings bypass the user's 'telethon' handler
[PASS] S5b enabling INFO on the per-client logger leaks the sleep line to root
[PASS] S6  concurrent sleeps on two accounts are attributed to the right account and call
[PASS] S7a hazard: a background task created during a call keeps that call's context after it ends
[PASS] S7b fix: clearing the call variable around connect() keeps the account, drops the stale call
[PASS] S8  dictConfig disables the logger (capture dies); the boundary check restores capture
[PASS] S9a an async callback scheduled from the filter runs during Telethon's own sleep; its error is contained
[PASS] S9b a callback scheduled just before the program ends is cancelled by asyncio.run (lost)
[PASS] S10 client(request, flood_sleep_threshold=0) still sleeps instead of raising (per-call threshold ignored)
[PASS] S11 a wait above the client threshold raises and writes no sleep record (no double count)
```
