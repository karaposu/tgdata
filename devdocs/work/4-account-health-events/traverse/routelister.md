---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

Territory: this inquiry's own artifacts in devdocs/work/4-account-health-events/traverse/ — _branch.md, articulate_simple.md, surfacing.md, articulate_warm.md, sensemaking.md, decomposition.md, innovation.md, critique.md (critique.md carries the user's mid-pass direction to base everything on the latest Telethon release, 1.45.0, and supersedes the 1.40-era claims it lists under "Corrections to earlier claims"). Goal (received from _branch.md's Goal): a stable, decided meaning-definition for issue #4 from which desc.md can be written — state taxonomy, signal-to-state mapping, event schema, emission-site inventory, callback contract, scope ruling. Enumerate the onward route-field (typed, prescriptive, never choosing). Write routelister.md (the per-run route-map) and _route.md (the persistent cross-run concept-map index), both in devdocs/work/4-account-health-events/traverse/ (the inquiry root).

---

# Route-Map — account health events (#4), on Telethon 1.45.0

## Map Header

- **Identities:** 21
- **High priority:** 9
- **Essential (`core`):** 10 · supporting 9 · peripheral 2
- **Goal, shared by every route:** #4's decided meaning, ready for `desc.md` — state taxonomy, signal-to-state mapping, event schema, emission-site inventory, callback contract, scope ruling.
- **Grain:** project-space throughout. A route's `kind` follows from its engagement-type.

## Route Index

| # | Direction | Engagement | Priority | Essentiality | ✓ |
|---|---|---|---|---|---|
| R1 | #4's issue description in its five-section shape | CONSOLIDATE | HIGH | core | |
| R2 | The Telethon 1.45.0 fact base #4 rests on | CONSOLIDATE | HIGH | core | |
| R3 | The verdict taxonomy — six verdicts at three scopes, plus unclassified | CONSOLIDATE | HIGH | core | |
| R4 | The rule that turns a Telegram error into a verdict | CONSOLIDATE | HIGH | core | |
| R5 | The health event's fields and plain-data shape | CONSOLIDATE | HIGH | core | |
| R6 | How an account is named inside an event | REFINE | MED | supporting | |
| R7 | When "ok" is sent — recovery per scope | REFINE | MED | core | |
| R8 | The health callback's contract | CONSOLIDATE | HIGH | core | |
| R9 | The inventory of places events come from | CONSOLIDATE | HIGH | core | |
| R10 | Capturing Telethon's silent sleeps through its own logger | DEEPEN | MED | supporting | |
| R11 | Signals that exist only inside Telethon's background updates task | PURSUE-SEED | MED | supporting | |
| R12 | Counting each wait and each error exactly once | TEST | MED | supporting | |
| R13 | The authorization-truthfulness prerequisite, as its own bug | PURSUE-SEED | HIGH | core | |
| R14 | #4's scope ruling — in, out, and named follow-ups | CONSOLIDATE | HIGH | core | |
| R15 | The per-instance health view in `health_check()` | DEVELOP | MED | supporting | |
| R16 | The log-line mirror of health events | DEVELOP | MED | supporting | |
| R17 | The offline fault-injection harness, doubling as an upgrade canary | DEVELOP | MED | supporting | |
| R18 | What a frozen account can still read | INVESTIGATE-FRONTIER | LOW | supporting | |
| R19 | tgdata's declared Telethon dependency floor | TEST | LOW | peripheral | |
| R20 | Discovery's per-call flood threshold, which Telethon ignores | PURSUE-SEED | MED | peripheral | |
| R21 | The public-text boundary for everything #4 posts | REFINE | MED | supporting | |

## Routes

### R1 — #4's issue description in its five-section shape

- **Direction:** #4's issue description in its five-section shape
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** CONSOLIDATE
- **Move:** gather the decided meaning (R3–R9, R14) into the description's five sections, with the prerequisite named as a blocker.
- **Lands:** a `desc.md` whose sections — Problem Statement, User Value, Success Criteria, Scope Boundaries, Priority — each draw from settled material, with no option left open.
- **Basis:** surfacing.md Trace #25 — "`desc.md`'s five sections (Problem Statement, User Value, Success Criteria, Scope Boundaries, Priority)" (defines the target shape)
- **WHY:** the goal *is* a meaning from which `desc.md` can be written. This route is where that becomes literally true, so the goal gains its finished form.
- **Priority:** HIGH · **Confidence:** MED · **Essentiality:** core
- **Guidance Mode:** compact
  - "state Success Criteria as checks the offline harness can run" (bc R17 makes every criterion testable without Telegram)
  - "carry the observed harm into User Value, in technical words" (bc the description is public — R21)
  - Meaning-gaps:
    - which items become Scope Boundaries and which become follow-up issues — mid — the boundary between #4 and its neighbours is public once posted
    - how strongly Success Criteria name Telethon 1.45.0 — low — the design is version-robust by its key (R4)
- **Depth-link:** none (not yet drilled)

### R2 — The Telethon 1.45.0 fact base #4 rests on

- **Direction:** The Telethon 1.45.0 fact base #4 rests on
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** CONSOLIDATE
- **Move:** carry critique's verified facts (E1–E13) and its corrections table forward as the only Telethon facts the description may cite.
- **Lands:** one fact list, re-verified on 1.45.0, which replaces the 1.40-era claims spread through sensemaking, decomposition and innovation.
- **Basis:** critique.md § User Input — "Use the latest Telethon release, and and like understand what we want to build based on the latest telethon." (records the user's direction that sets the base)
- **Basis:** critique.md § Corrections to earlier claims — paraphrase: seven earlier claims superseded, among them the ignored per-call threshold and the wrong fallback by category (corrects the upstream artifacts) — as-of Telethon 1.45.0
- **WHY:** a description that cites a superseded fact would plant a wrong behaviour into the plan. The goal gains a meaning that is true for the release the user chose.
- **Priority:** HIGH · **Confidence:** MED · **Essentiality:** core
- **Guidance Mode:** compact
  - "treat sensemaking A8 and A12 as superseded wherever they disagree with critique" (bc critique re-tested them against 1.45.0 source and runtime)
  - Meaning-gaps:
    - whether every 1.40-only claim in the upstream artifacts was caught by the corrections table — mid — a missed one would surface as a wrong sentence in the description
- **Depth-link:** none (not yet drilled)

### R3 — The verdict taxonomy

- **Direction:** The verdict taxonomy — six verdicts at three scopes, plus unclassified
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** CONSOLIDATE
- **Move:** state the six verdicts, their scopes and their meanings in one place, merging sensemaking's rulings with critique's table changes.
- **Lands:** each verdict defined once:
  - *account* — logged out (recoverable by login), banned (not recoverable), restricted, ok;
  - *method* — waiting;
  - *group* — no access, from confirmed verdicts only;
  - *unclassified* — the calibration channel.
- **Basis:** sensemaking.md §§ A2, A3, A9, A10, A11 — paraphrase: Telegram's verdicts only, three scopes, "restricted" kept and marked unobserved, banned kept apart from logged out, no access only once confirmed (defines the taxonomy)
- **Basis:** critique.md § P1 — the mapping, M1 — paraphrase: adds `CHANNEL_BANNED` to no access and leaves `CHAT_RESTRICTED` unclassified (refines the rows)
- **WHY:** every other piece carries a verdict name, so the goal gains the vocabulary every section of the description is written in.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "keep the user's six names; add only scope, verdict and unclassified" (bc sensemaking A17 ties the names to issues #3, #9 and #10)
  - Meaning-gaps:
    - whether a slow-mode wait is a method or a group scope — low — chat-specific per Telethon, and unlikely for a reader
    - what `CHAT_RESTRICTED` means for a reader — low — safely unclassified until observed
- **Depth-link:** none (not yet drilled)

### R4 — The rule that turns a Telegram error into a verdict

- **Direction:** The rule that turns a Telegram error into a verdict
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** CONSOLIDATE
- **Move:** write the single rule:
  - key every error by Telegram's wire name, read from Telethon's tables or from `.message`;
  - take verdicts only from listed names;
  - report unclassified only in the 401, 403, 406 and 420 categories;
  - walk wrapped causes.
- **Lands:** one lookup rule that gives the same verdict on Telethon 1.33 and 1.45.0, and that never invents a verdict from an error's family.
- **Basis:** critique.md § Evidence base E4 — paraphrase: 1.45.0's 401 and 406 families hold non-logout errors such as `FILEREF_UPGRADE_NEEDED` and `SESSION_PASSWORD_NEEDED` (establishes why the fallback was removed) — as-of Telethon 1.45.0
- **WHY:** a wrong verdict is worse than none, because an operator would abandon a recoverable account or retry a frozen one. So the goal gains truthful verdicts.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "the category decides whether to report, never which verdict" (bc that is the line critique drew between bounding noise and inventing verdicts)
  - Meaning-gaps:
    - walking wrapped causes — `RuntimeError`, `ConnectionError`, `AuthRequiredError`, `DiscoveryInterrupted` — to reach the Telegram error — mid — a missed wrap loses the verdict on tgdata's most common escape paths
    - which ordinary errors besides file-reference ones stay out of "unclassified" — low — the list can grow safely after building
    - where scope comes from: the request type from `.request`, the group from the call — low — decomposition I7 already names it
- **Depth-link:** none (not yet drilled)

### R5 — The health event's fields and plain-data shape

- **Direction:** The health event's fields and plain-data shape
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** CONSOLIDATE
- **Move:** fix the field list, the types and the JSON-ready rule, dropping the killed `severity` field.
- **Lands:** a published event shape — `kind`, `time`, `account`, `verdict`, `scope`, `group`, `call`, `wait_seconds`, `error`, `source` — that crosses a process boundary unchanged.
- **Touches:** `kind` (`"health"`, extensible for later producers) · `source` (error · sleep · auth · updates) · `error` (Telegram's wire name, never a category)
- **WHY:** consumers and #10's worker will serialize this shape, so it is the public contract the goal must state exactly.
- **Priority:** HIGH · **Confidence:** MED · **Essentiality:** core
- **Guidance Mode:** compact
  - "describe what each action needs in the README's verdict table, not in a field" (bc critique killed `severity` for misdescribing two verdicts)
  - Meaning-gaps:
    - what identifies a group in the event — a resolved id or the caller's argument — high — recovery keys (R7) and per-group totals depend on it, readings differ, and a public field is costly to change
    - how `call` is rendered (request class name vs. tgdata method) — low — both can be carried later
- **Depth-link:** none (not yet drilled)

### R6 — How an account is named inside an event

- **Direction:** How an account is named inside an event
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** REFINE
- **Move:** pin each of the three identity fields to one source:
  - **session** — the configured session's stem;
  - **label** — an optional `account_label=`;
  - **user id** — from what Telethon already knows, without a new call.
- **Lands:** an account identity that survives a logout and a move between machines, and stays one identity across pooled connections.
- **Basis:** articulate_simple.md MQ2 verdict sub-axis — "Whether 'the account' is 1:1 with a config file. True for the account pool described in the consumer's docs; unverified for pooled sessions (`<session>_1`, …)." (establishes the pooled-session risk)
- **Basis:** critique.md § P2 — O6 — paraphrase: no stem default for the label; the user id comes from Telethon's restored self id or stays empty until `get_me()` (refines the identity)
- **WHY:** #4's own examples aggregate per account. Two names for one account would split its totals, so the goal gains totals that add up.
- **Priority:** MED · **Confidence:** MED · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "name pooled connections by the configured session, not the pooled file" (bc connection pooling creates `<session>_1`-style files for one account)
  - "decide private `_self_id` vs. empty-until-`get_me()` by what Telethon 1.45.0 restores at connect" (bc critique verified the restore on 1.45.0)
- **Depth-link:** none (not yet drilled)

### R7 — When "ok" is sent

- **Direction:** When "ok" is sent — recovery per scope
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** REFINE
- **Move:** state recovery per verdict:
  - waiting ends when the call that waited succeeds;
  - restricted ends only when the refused request type succeeds;
  - logged out ends on re-authorization;
  - banned never ends within an instance;
  - waits in a background task are occurrences only.
- **Lands:** "ok" events that never flap and never claim a recovery that did not happen.
- **Basis:** critique.md § P3 — "Recovery for *restricted*" — paraphrase: the first-success rule would flap restricted → ok → restricted on a frozen account that can still read (corrects decomposition Q3)
- **WHY:** a false "ok" tells an operator a frozen account is healthy again. The goal gains an "ok" that can be trusted, and the state view (R15) inherits it.
- **Priority:** MED · **Confidence:** MED · **Essentiality:** core
- **Guidance Mode:** compact
  - "key group recovery on the same group identity R5 settles" (bc an id-vs-username mismatch leaves a stale "no access")
- **Depth-link:** none (not yet drilled)

### R8 — The health callback's contract

- **Direction:** The health callback's contract
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** CONSOLIDATE
- **Move:** state the contract:
  - one `health_callback=` per instance, sync or async;
  - exception-safe — errors are logged, never propagated;
  - awaited where tgdata runs async code, scheduled only from the logging filter;
  - an event that ends an operation is delivered before its exception propagates.
- **Lands:** a callback a consumer can write without reading tgdata's source, and that can never break a scrape.
- **Basis:** devdocs/work/4-account-health-events/probe_health_145.py S9a, S9b — paraphrase: a scheduled async callback runs during Telethon's sleep; a task scheduled as `asyncio.run` ends is cancelled (establishes await-where-possible)
- **WHY:** a callback that propagates or loses terminal events would turn the observer into a hazard. The goal gains a delivery rule that keeps P3 — an observer never breaks the observed.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "reuse `_notify`'s `inspect.isawaitable` detection" (bc it matches the existing `found_callback` convention)
  - Meaning-gaps:
    - how repeated callback errors are logged — first at WARNING, repeats at DEBUG — low — easily tuned later
    - how strongly the docs warn against slow callbacks — low — documentation only
- **Depth-link:** none (not yet drilled)

### R9 — The inventory of places events come from

- **Direction:** The inventory of places events come from
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** CONSOLIDATE
- **Move:** list every source with what it observes:
  - the public-call boundary;
  - engine-handled waits (discovery's only above 60 s);
  - Telethon's silent sleeps;
  - the poll loop, discovery's skips and the real-time path;
  - the authorization checks, after the prerequisite;
  - the never-emitted list.
- **Lands:** an inventory the plan can turn into steps one-to-one, with each site's signal and verdict stated.
- **Basis:** sensemaking.md § A15 — paraphrase: one boundary plus four enumerated internals, and a never-emitted list (defines the inventory's structure)
- **Basis:** critique.md § What #4 builds, item 4 — paraphrase: discovery's engine waits are only those above 60 s, because the per-call threshold is ignored (refines the inventory) — as-of Telethon 1.45.0
- **WHY:** a source missing from the inventory becomes a silent gap in the event stream, so the goal gains a stream that is complete by construction.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "list the wrapped public methods by name" (bc decomposition Q4a names twelve, and the description should too)
  - Meaning-gaps:
    - whether the background-task signals (R11) enter #4's inventory or a follow-up — low — they can be added through the same filter later
- **Depth-link:** none (not yet drilled)

### R10 — Capturing Telethon's silent sleeps through its own logger

- **Direction:** Capturing Telethon's silent sleeps through its own logger
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** DEEPEN
- **Move:** carry the validated mechanism into specification:
  - a filter on `telethon.client.users` with sentinel level 19;
  - an account context variable inherited at `connect()`, with the call variable cleared there;
  - a re-check at every call boundary;
  - two documented limits.
- **Lands:** a specified capture whose side effects are nil by test, ready for the plan.
- **Basis:** devdocs/work/4-account-health-events/probe_health_145.py S2–S8 — paraphrase: capture with no INFO leak, warnings and sub-logger matches preserved, correct attribution across accounts and background tasks (establishes the mechanism) — as-of Telethon 1.45.0
- **WHY:** waits of 60 s or less are invisible today (S1), and #4's "waited 4 times" needs them. The goal gains the waits without changing what users see.
- **Priority:** MED · **Confidence:** HIGH · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "document `logging.disable(INFO)` and a mid-call level change as the two limits" (bc critique left only these)
- **Depth-link:** none (not yet drilled)

### R11 — Signals that exist only inside Telethon's background updates task

- **Direction:** Signals that exist only inside Telethon's background updates task
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** PURSUE-SEED
- **Move:** decide whether to read two INFO records through the same filter on `telethon.client.updates`, attributed by the inherited account variable:
  - "Account is now banned in %d", with the channel id;
  - a wait while catching up, with the request type only.
- **Lands:** a ruling on whether a lost channel and catch-up waits during real-time listening become events in #4.
- **Basis:** critique.md § Evidence base E9 — paraphrase: on 1.45.0 a logout or ban re-raises only for sessions once logged in; channel loss and catch-up waits are only log lines (establishes the seed) — as-of Telethon 1.45.0
- **WHY:** without it the real-time path reports logouts but not lost groups. The goal gains a scope ruling that says so explicitly either way.
- **Priority:** MED · **Confidence:** MED · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "a catch-up wait carries no seconds in its record" (bc the event would have `wait_seconds` empty)
- **Depth-link:** none (not yet drilled)

### R12 — Counting each wait and each error exactly once

- **Direction:** Counting each wait and each error exactly once
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** TEST
- **Move:** check exactly-once delivery against evidence, in two layers:
  - Telethon's side — it either sleeps and logs, or raises, never both (S11);
  - tgdata's side — the "already emitted" mark at the boundary after an engine gave up.
- **Lands:** a success criterion that is shown to hold, such as "four waits then a give-up give four waiting events, not five".
- **Basis:** devdocs/work/4-account-health-events/probe_health_145.py S11 — paraphrase: a wait above the client threshold raises and writes no sleep record (supports Telethon's side)
- **WHY:** #4's totals are only right if nothing is counted twice, so the goal gains totals a consumer can trust.
- **Priority:** MED · **Confidence:** MED · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "test tgdata's side with the stand-in client of R17" (bc the mark crosses the engine/boundary seam decomposition found)
- **Depth-link:** none (not yet drilled)

### R13 — The authorization-truthfulness prerequisite, as its own bug

- **Direction:** The authorization-truthfulness prerequisite, as its own bug
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** PURSUE-SEED
- **Move:** take up the prerequisite as its own bug:
  - tgdata asks Telegram directly, so it tells a ban, a logout and a wait apart;
  - a previously logged-in session never prompts implicitly — it raises `AuthRequiredError` with Telegram's error attached;
  - first login keeps the terminal prompt;
  - re-login after a revocation needs an explicit opt-in.
- **Lands:** a filed bug that #4 is blocked by, whose fix ends the login-code storm.
- **Basis:** surfacing.md Trace #12 — paraphrase: a logged-out session on the persistent path asked for a login code 11 times in 70 minutes until stopped (records the harm)
- **Basis:** critique.md § Evidence base E10, E11 — paraphrase: a pseudo-terminal with no one typing passes `isatty()`; §4.5's "smaller and more certain" rule (establishes the fail-closed design and the packaging)
- **WHY:** #4 cannot report a logout truthfully on the persistent path until this exists. The owner stops receiving codes, so the goal gains both its scope ruling and the end of a live harm.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "choose among the three 'previously logged in' signals critique verified" (bc each fails differently: auth key before connect, restored self id, saved update state)
  - "classify the actual error from `GetUsers` or `GetState`, never through `get_me()` or `is_user_authorized()`" (bc both hide the difference — E8)
- **Depth-link:** none (not yet drilled)

### R14 — #4's scope ruling

- **Direction:** #4's scope ruling — in, out, and named follow-ups
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** CONSOLIDATE
- **Move:** state the ruling:
  - **in:** the side channel and its three views;
  - **blocked by:** the prerequisite (R13);
  - **out:** transport errors, the six excluded signal kinds, and building #3, #8, #9 or #10;
  - **later:** the deferred directions, each named with its issue.
- **Lands:** a Scope Boundaries section with no unnamed edge.
- **Basis:** critique.md § Screened candidates — paraphrase: admission control, pull iteration, a process-wide sink, the Account object, closed-loop pacing and threshold 0 deferred beyond #4 (records the follow-ups)
- **WHY:** a scope without named edges invites the plan to build a neighbour's feature. The goal gains the boundary CONTRIBUTING's description requires.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "keep heartbeat and health as two streams" (bc sensemaking L2: their lifetimes differ)
  - "say that health events report and never act" (bc frame-premise FP1 held under critique)
  - Meaning-gaps:
    - whether the discovery threshold bug (R20) is listed as a neighbour or a blocker — low — it changes one inventory line, not the ruling
- **Depth-link:** none (not yet drilled)

### R15 — The per-instance health view in `health_check()`

- **Direction:** The per-instance health view in `health_check()`
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** DEVELOP
- **Move:** expose recovery's own state read-only as `health_check()["health"]`:
  - the account verdict and since when;
  - open method waits;
  - groups without access;
  - wait count and total seconds;
  - the last unclassified name.
- **Lands:** #4's example ("waited 4 times, 210 s total") answered with no consumer code.
- **Basis:** critique.md § P3 — A6 — paraphrase: SURVIVE; the ledger already exists for recovery; per instance, since construction, in memory (establishes the view)
- **WHY:** pollers and dashboards get state without wiring a callback, so the goal gains #4's aggregate examples at almost no cost.
- **Priority:** MED · **Confidence:** MED · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "say 'per instance, since construction' in the docs" (bc two instances on one account will differ)
  - Meaning-gaps:
    - the exact field set of the view — mid — it becomes a public shape, and adding later is safe but removing is not
    - how the group list stays bounded in long runs — low — bounded by groups that ever returned a verdict
- **Depth-link:** none (not yet drilled)

### R16 — The log-line mirror of health events

- **Direction:** The log-line mirror of health events
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** DEVELOP
- **Move:** mirror each event on a logger under `tgdata.tgdata`:
  - WARNING for logged out, banned, restricted and unclassified;
  - INFO for waiting, no access and ok.
- **Lands:** terminal verdicts visible by default to anyone reading tgdata's logs, and waits one configuration line away.
- **Basis:** critique.md § The other views — L3 — paraphrase: corrects innovation's claim that waits would be visible with zero integration; `log_file` attaches only to `tgdata.tgdata` (refines the mirror)
- **WHY:** the consumer whose log showed nothing would have seen the logout. The goal gains visibility for people, not only for code.
- **Priority:** MED · **Confidence:** MED · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "a JSON formatter on this logger is the persistence story" (bc critique killed the separate JSONL sink in its favour)
  - Meaning-gaps:
    - the logger's name, and whether `log_file` users receive it — low — a small rename if wrong
    - the level for "no access" — low — one line to change
- **Depth-link:** none (not yet drilled)

### R17 — The offline fault-injection harness

- **Direction:** The offline fault-injection harness, doubling as an upgrade canary
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** DEVELOP
- **Move:** grow the probe's fake connection into a reusable stand-in. It drives Telethon's real request path with each verdict, a sleep and a give-up.
- **Lands:** every success criterion checkable offline. A Telethon upgrade that changes the sleep record or the threshold behaviour fails a test instead of silently breaking capture.
- **Touches:** `probe_health_145.py` (the working prototype, 17 checks) · the smoke-test folder (where the stand-in would live)
- **WHY:** no live account can be banned or frozen on demand, so the goal gains success criteria that can actually be verified.
- **Priority:** MED · **Confidence:** HIGH · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "keep it in the smoke tests, not the package" (bc critique judged it test code)
  - Meaning-gaps:
    - covering the background-task path offline — low — the probe's S7 shows how
- **Depth-link:** none (not yet drilled)

### R18 — What a frozen account can still read

- **Direction:** What a frozen account can still read
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** INVESTIGATE-FRONTIER
- **Move:** observe a frozen account's reads, or collect a credible report of them, to learn which calls fail with which error.
- **Lands:** the restricted row marked observed or still unobserved, with evidence.
- **Basis:** critique.md § Frame-premise test FP1 — paraphrase: 1.45.0 documents `FROZEN_PARTICIPANT_MISSING` as "Your account is frozen and can't access the chat"; read behaviour is otherwise unobserved (establishes the frontier) — as-of Telethon 1.45.0
- **WHY:** the description must say honestly what "restricted" covers for a reader. The goal gains that honesty even if the answer stays "unobserved".
- **Priority:** LOW · **Confidence:** LOW · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "an unclassified report from a consumer is the likeliest first evidence" (bc the calibration channel was designed for this)
- **Depth-link:** none (not yet drilled)

### R19 — tgdata's declared Telethon dependency floor

- **Direction:** tgdata's declared Telethon dependency floor
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** TEST
- **Move:** run the offline classifier and capture tests on the floor version (1.33) as well as on 1.45.0.
- **Lands:** evidence for keeping `Telethon>=1.33` or for raising it.
- **Basis:** critique.md § Screened candidates — K3 — paraphrase: build and test on 1.45.0 and keep the floor, because the wire-name key works on every release (supports the test)
- **WHY:** indirect — the meaning is version-robust by design, so this settles packaging rather than meaning. It is a nice-to-have for the description's compatibility line.
- **Priority:** LOW · **Confidence:** MED · **Essentiality:** peripheral
- **Guidance Mode:** compact
  - "the six archives critique compared are a ready matrix" (bc the sleep record and `__call__` were identical across them)
- **Depth-link:** none (not yet drilled)

### R20 — Discovery's per-call flood threshold, which Telethon ignores

- **Direction:** Discovery's per-call flood threshold, which Telethon ignores
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** PURSUE-SEED
- **Move:** take up the pre-existing discovery defect as its own bug. `client(request, flood_sleep_threshold=0)` sleeps through waits of 60 s or less, so `max_flood_wait` and the waiting heartbeat do not apply to them.
- **Lands:** a filed bug, with discovery's docstrings corrected and a fix chosen.
- **Basis:** critique.md § Evidence base E5 — paraphrase: `__call__` never forwards the per-call threshold in any release from 1.33.1 to 1.45.0 (establishes the defect) — as-of Telethon 1.45.0
- **WHY:** indirect for #4 — it only changes one line of R9's inventory. Its own value lies outside this goal.
- **Priority:** MED · **Confidence:** HIGH · **Essentiality:** peripheral
- **Guidance Mode:** compact
  - "the client-wide threshold is the only one Telethon honours" (bc S11 shows it raising while the per-call one does not)
- **Depth-link:** none (not yet drilled)

### R21 — The public-text boundary for everything #4 posts

- **Direction:** The public-text boundary for everything #4 posts
- **Goal:** #4's decided meaning, ready for `desc.md`
- **engagement-type:** REFINE
- **Move:** sharpen what counts as internal before the description is posted. Internal means:
  - the private proposal and its strategy;
  - consumer project names and local paths;
  - the observed account.
- **Lands:** a description and a prerequisite bug written only in technical terms, with the harm told without naming its owner.
- **Basis:** sensemaking.md § C10 — "public text carries no internal strategy." (defines the boundary)
- **Basis:** surfacing.md Trace #24 — paraphrase: the private proposal is a requirement source, never quoted into public text (supports the boundary)
- **WHY:** the issue tracker is public, so the goal gains a description that can be posted as written.
- **Priority:** MED · **Confidence:** MED · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "these traverse artifacts name private sources; treat them as raw material, not as text to quote" (bc surfacing and critique cite internal logs and paths by name)
- **Depth-link:** none (not yet drilled)

## Sources

The routes cite these artifacts directly; all were in view during this run:
- critique.md
- sensemaking.md
- decomposition.md
- surfacing.md
- articulate_simple.md
- `devdocs/work/4-account-health-events/probe_health_145.py`

## Excluded

**Not goal-relevant:**
- **An upstream report of Telethon's `__call__` defect.** It does nothing toward #4's meaning. It is the user's own outward act, and Telethon's template says "Do not use AI to write the issue" (critique E13).
- **`receive_updates=False` for clients without listeners.** An optimisation with no bearing on what health events mean.
- **The entity-resolution follow-up**, which extends the dialog sync to count, search and download. #4's rule — an unresolved cache-miss is not a signal — stands without it (sensemaking A11).

**Killed under critique, by evidence:**
- per-client `base_logger` capture — it renames loggers and leaks INFO;
- the `severity` field — it misdescribes two verdicts and adds nothing;
- a built-in JSONL sink — superseded by the log mirror;
- the verdict fallback by category — it invents logouts on 1.45.0;
- the terminal-only login guard — the pseudo-terminal false positive, absorbed into R13.

**Ruled out in sensemaking, re-confirmed under critique:**
- a propagating callback;
- "ok" per call;
- transition-only events;
- "unreachable" as a seventh verdict;
- a single scope;
- pull-only health;
- one observer object;
- raising Telethon's floor *for correctness*. The packaging question survives as R19.

**Deferred beyond #4,** named in R14's follow-ups, so no route here:
- admission control or a circuit breaker;
- never-implicit authentication (#8);
- a pull iterator and a process-wide sink (#10);
- runtime table extension;
- an Account object;
- closed-loop pacing and threshold 0 (#9).

## Telemetry

- **Mode:** root / project-space. **Entry point:** fresh (no prior `_route.md`).
- **Identities:** 21.
  - By kind: epistemic 13 (CONSOLIDATE 8, REFINE 3, TEST 2); teleological 8 (DEVELOP 3, PURSUE-SEED 3, DEEPEN 1, INVESTIGATE-FRONTIER 1).
  - High priority: 9.
  - Essentiality: core 10, supporting 9, peripheral 2.
- **Individuations made:** 21. Three splits are flagged as uncertain, each kept split under lean-to-split:
  - taxonomy (R3) vs. mapping rule (R4) — the goal names them separately;
  - event shape (R5) vs. account naming (R6) — R6 carries its own open facets;
  - inventory (R9) vs. silent-sleep capture (R10), background-task signals (R11) and exactly-once counting (R12) — distinct engagements.
- **Stale entries:** 0.
- **Convergence:** reached — a second sweep of the eight artifacts produced no new identity. **Frontier flags:** none for sub-territory; R18 is a frontier route.
- **Basis entries:** 25 — pointer with a verbatim quote 4 (R1, R2, R6, R21), paraphrase 21, excerpt 0, not recovered 0. Routes needing none: R5 and R17, whose sources are in Touches.
- **Failure modes checked:**
  - LAYER 1: over-merge (splits leaned), under-coverage (all eight artifacts swept, including the cold articulation's pooled-session facet), wrong-grain (identities only), goal-loss, type-misassignment (each verb tested against its kind), index-drift (fresh), basis-unrecoverable (none).
  - LAYER 2: selection-creep (no route chosen or ordered as "next"), process-coupling (no control-flow route), description-collapse (every route is a move), manifestation-dump.
- **Self-assessment: PROCEED.**
