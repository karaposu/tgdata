---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

devdocs/work/4-account-health-events/traverse/_branch.md — inputs also in that folder: articulate_simple.md, surfacing.md (with ../triage.md as its prior artifact), articulate_warm.md (the settled re-anchored framing; use its committed MQ2 and refreshed considered articulations). SAVE the output as devdocs/work/4-account-health-events/traverse/sensemaking.md

---

# Sensemaking — what "account health events" mean in tgdata

## SV1 — Baseline

Map Telegram errors onto six labels (ok, waiting, logged out, banned, restricted, no access) and call a callback with an event whenever one occurs.

---

## Phase 1 — Cognitive anchors

### Constraints

- **C1 — Telethon's hierarchy is not a state map.**
  - A ban (`UserDeactivatedBanError`) and a logout (`AuthKeyUnregisteredError`, `SessionRevokedError`) share the `UnauthorizedError` base.
  - The frozen-account error shares the `FloodError` base with real waits and has no wait length.
- **C2 — How Telethon names errors (verified on 1.40, by converting sample Telegram responses).**
  - An error Telethon *knows* becomes its specific class, and its `.message` holds only the category (`UNAUTHORIZED`, `FLOOD`, `BAD_REQUEST`, `FORBIDDEN`).
  - An error it does *not* know becomes the bare category class, with Telegram's own name in `.message` (`FloodError` carrying `FROZEN_METHOD_INVALID` on 1.40).
  - Every error carries `.request`, the request that caused it.
  - `FloodWaitError` carries `.seconds`.
- **C3 — Waits under 60 s are slept inside Telethon and only logged:** `Sleeping[ early] for %ds (%s) on %s flood wait`, with the seconds and the request's class name as record arguments. Each client's logs can be routed to its own logger through `base_logger` (verified: `base_logger="tgdata.acct.demo"` gives `tgdata.acct.demo.client.users`).
- **C4 — tgdata has no notion of "the account".** It has a config path and a session name; a user id needs an authorised call.
- **C5 — events may leave the process** (#10), so an event must be plain data, never a Telethon object or an exception.
- **C6 — two callback conventions already exist:** exception-safe (heartbeat) and propagating (found and batch callbacks; propagation is tested).
- **C7 — the real-time path** learns of a logout inside Telethon's updates loop. tgdata sees it only when `run_until_disconnected` re-raises; a lost channel during catch-up is only logged.
- **C8 — "Could not find the input entity"** (`ValueError`) is a local cache-miss. It is a Telegram access verdict only after a dialog sync, and tgdata does that sync only in the fetch path.
- **C9 — this pass decides meaning only;** consumers #3, #8, #9 and #10 are not built.
- **C10 — public text carries no internal strategy.**

### Key insights

- **K1 — the six names are verdicts with different scopes, not one account state.**
  - "No access" is about one group: an account can read X while locked out of Y.
  - "Waiting" is about one *method*. Telethon remembers waits per request type, and the finder's account was blocked from username lookups for 21 h while it kept reading.
  - Only logged out, banned and restricted describe the account as a whole.
- **K2 — #4's own examples need every occurrence, not just changes.** "Waited 4 times, 210 s total" cannot be rebuilt from state transitions; "logged out after 9 days" can be rebuilt from occurrences.
- **K3 — truthful reporting on the persistent path requires detecting a logout before Telethon's interactive `start()`.** Without that, the logout surfaces as `ConnectionError("Failed to authenticate: EOF when reading a line")` after a login-code request — misclassified and harmful. Detecting it and then calling `start()` anyway would knowingly request a code. Reporting and not-requesting are coupled.
- **K4 — a version-robust mapping keys on Telegram's error identity:**
  - the specific class name when Telethon knows the error;
  - the raw `.message` when it does not;
  - never the category message alone.
- **K5 — observing must not change what is observed.** A dashboard bug must not end a scrape. The places events come from include a logging handler and Telethon's updates loop, where an exception has no meaningful place to go.
- **K6 — the commonest real failure (423× in one consumer's log) is not a verdict** until a dialog sync resolves it (C8).

### Structural points

- **S1 — signal sources:**
  - (a) exceptions from Telethon calls;
  - (b) silent sleeps — log records;
  - (c) the updates loop — a stored error re-raised;
  - (d) tgdata's own inferences — authorization checks, the dialog-sync result.
- **S2 — one classifier:** a signal goes in; a verdict, scope and detail come out.
- **S3 — one emitter per account.** The account lives as long as the `TgData` instance; liveness (the heartbeat) lives as long as one call.
- **S4 — the emission sites** listed in `triage.md`.
- **S5 — the event fields:** time, account, verdict, scope, group, call, wait seconds, Telegram error name, source.

### Foundational principles

- **P1 — report, and take no outward action the caller did not ask for.** Requesting a login code is an outward action.
- **P2 — additive:** no exception type a caller catches today changes, except where today's behaviour is a defect.
- **P3 — an observer never breaks the observed operation.**
- **P4 — key on the wire-level name**, Telegram's error identity, not on a library's class tree.
- **P5 — honesty over completeness:** what cannot be observed is declared unobservable, not guessed.

### Meaning-nodes

Signal vs. state · scope (account / method / group) · terminal vs. transient · observe vs. act · the login-code storm · cache-miss vs. verdict.

## SV2 — Anchor-informed

The task is not "label errors". It is a two-layer model:
- **classified occurrences** (signals), each carrying a scope;
- **per-scope verdicts** derived from them.

On the persistent path, the classification is only truthful if a logout is detected before Telethon's interactive login runs.

*Meta-inspection after SV2.*
- **H4, concept names:** "account health state" is the user's term, but "no access" and "waiting" are not account-wide. The names are kept; their scope is made explicit.
- **H5, motivating examples:** #4's two examples ("waited 4 times…", "banned at 14:02") are one case of a wider pattern — per-account aggregation over time — which the occurrence model serves generally.

---

## Phase 2 — Perspective checking

- **Technical / logical.** Classification has to handle known classes and unknown ones (C2).
  - Silent sleeps can be attributed per account by giving each client its own `base_logger` and reading the sleep record's arguments, with no change to Telethon's sleeping behaviour.
  - Forcing every wait to raise (threshold 0) would make every call site handle waits — a behaviour change everywhere.
  - *New anchors:* T1 per-client logger attribution; T2 the record's arguments give seconds and request type.
- **Human / user.**
  - An operator wants account-level verdicts, plus "no access to X" per group.
  - An integrator wants one callback, plain data, and a scrape that never dies because of it.
  - The account owner received 11 login codes in 70 minutes.
  - *New anchors:* U1 account and group views differ; U2 the owner is a stakeholder, not only the operator.
- **Strategic / long-term.**
  - #3 (proxy-check results), #9 (budget reached) and #8 (login steps) will want to put their own events into the same stream; #10 will serialise them.
  - An envelope with a `kind` lets later producers join without redefining the six verdicts. The heartbeat (scoped/9) stays separate because its lifetime is one call.
  - *New anchors:* L1 an extensible envelope; L2 two streams with different lifetimes.
- **Risk / failure.**
  - Reading a logout as a ban leads an operator to abandon a recoverable account.
  - Reading a frozen account as waiting keeps retrying a frozen account.
  - A propagating callback lets a monitor bug kill a scrape.
  - Per-occurrence emission inside a 3,000-message fetch could flood the stream if file errors are counted.
  - A global logging change could start printing Telethon INFO to users' consoles.
  - *New anchors:* R1 classify only Telegram verdicts; R2 attach the handler to per-client loggers without changing global log levels.
- **Resource / feasibility.**
  - Persistent-path detection costs nothing extra: `start()` already checks authorisation (`GetState`) before prompting.
  - The classifier is one table.
  - Per-client loggers are one constructor argument in the single client factory.
  - *New anchor:* F1 every mechanism hangs off existing seams — the factory, the facade, the two engines' wait handlers.
- **Ethical / systemic.** A library that silently spams verification codes can lock an owner out of their own account. Stopping that is a matter of harm, not polish.
  - *New anchor:* E1 the login-code storm is a defect with live harm, more urgent than events.
- **Definitional / internal consistency.**
  - #4 calls the six "account health states" while defining two of them per group or per method. The definition contradicts its own name.
  - Resolution direction: the six are verdict *types*; account health is the account-scope subset.
  - *New anchor:* D1.
- **Definitional / frame-exit completeness.** Gating fires: the six inherited terms are used across distinct values in this inquiry's taxonomy. The four meta-categories:
  - *Existence enumeration.* "Health" project-wide:
    - (1) Telegram's verdicts on an account;
    - (2) group access;
    - (3) connection health (`health_check`'s primary connection, the pool's rate limits);
    - (4) proxy health (#3);
    - (5) budget state (#9);
    - (6) operation liveness (heartbeat).

    The frame includes (1) and (2).
  - *Role assessment.* (3)–(6) are not needed for #4's operation to stay coherent. They are relocated, not excluded:
    - connection health stays in `health_check`;
    - proxy, budget and login become future `kind`s of the same envelope;
    - liveness stays the heartbeat.
  - *Verdict rigor.*
    - Counter: "a dashboard needs one stream with everything; splitting makes consumers merge streams."
    - Structural answer: the shared envelope with `kind` gives one callback stream without making "unreachable" a verdict about the account — a dead proxy says nothing about the account behind it.
    - Holds.
  - *Residual.* "Never logged in" — a throwaway session — vs. "logged out". A session with no auth key never had an account to lose. It is a configuration state, not a verdict; the persistent path's first-time interactive login stays as it is. Recursion terminates.
- **Phase / calibration-state** (required: these rules depend on evidence the project lacks).
  - No wait frequency is known: the consumer's log shows none, because of its level.
  - No banned or frozen account has been observed.
  - Early-stage default: report every wait with no threshold; mark the ban and frozen rows "by documentation, unobserved"; let the table grow from unclassified reports.
  - Frozen detection is version-phased: specific class on Telethon ≥ 1.42, raw name on 1.40.
  - *New anchor:* PH1 an "unclassified" report is the calibration channel.

## SV3 — Multi-perspective

The model now has:
1. **Verdicts at three scopes:** account (logged out, banned, restricted), method (waiting) and group (no access), plus "ok" as recovery.
2. **Plain-data events** in an envelope extensible by `kind`.
3. **One exception-safe callback per account.**
4. **A version-robust mapping** keyed on Telegram's error identity.
5. **Attribution of silent waits** through per-client loggers.
6. **Persistent-path truthfulness**, which requires detecting a logout before the interactive login — a defect with live harm.

*Meta-inspection after SV3.*
- **H1, candidate set:** the five considered articulations collapse onto two real axes — how much behaviour changes, and stream vs. state. Several differ only in callback semantics, which this model settles.
- **H2:** handled by frame-exit completeness above.
- **H3, question framing:** "whether fixing the headless-login bug belongs in #4" presupposes it is a #4 concern. Phase 3 tests that framing.
- **H7:** handled above.

---

## Phase 3 — Ambiguity collapse

### A1 — Decide or map?
**Counter:** lay out the space and let `desc.md` choose.
**Why it fails:** CONTRIBUTING's `desc.md` must state success criteria and scope boundaries, which cannot be written over an undecided space. What genuinely cannot be decided stays explicitly open (A9b, A13b).
**Confidence:** HIGH. **Resolution:** decide, and mark the residue open.
**Fixed:** the output is a decided meaning. **No longer allowed:** an options catalogue handed to `desc.md`. **Depends on it:** every entry below. **Model change:** commitments replace variants.

### A2 — The state-set boundary
**Counter (warm variant 3):** include "unreachable" (network or proxy down) as a seventh state so #3 and #10 read one set.
**Why it fails:** a transport failure carries no verdict about the account — the same healthy account is "unreachable" behind a dead proxy and fine behind a live one. Folding it in makes "account 7 unreachable" ambiguous between the account and the connection. The `kind` field already gives #3 and #10 the same stream (Phase 2, frame-exit).
**Confidence:** HIGH. **Resolution:** the six are Telegram's verdicts. Transport and proxy conditions are not health states; budget, proxy-check and login outcomes are future `kind`s.
**Fixed:** six verdict names. **No longer allowed:** transport errors emitted as health states. **Depends on it:** the classifier's input filter, and the envelope's `kind`. **Model change:** health means *Telegram's opinion*, not *can we connect*.

### A3 — One scope or three?
**Counter:** every verdict is about the account, for simplicity — the issue says "account health".
**Why it fails:** Telegram issues these verdicts at different scopes.
- `CHANNEL_PRIVATE` on group X says nothing about group Y.
- Telethon records flood waits per request type (`_flood_waited_requests` keyed by constructor id), and the finder kept reading for 21 h while username lookups were blocked.
- Marking the whole account "waiting" or "no access" would show a working account as broken.

**Confidence:** HIGH. **Resolution:** three scopes:
- *account* — logged out, banned, restricted, ok;
- *method* — waiting, keyed by the request type;
- *group* — no access, keyed by the group.

**Fixed:** every event carries a scope. **No longer allowed:** an account-wide "waiting" or "no access". **Depends on it:** the event schema; any current-state record. **Model change:** "account health" is the account-scope subset of a richer stream.

### A4 — When is "ok" emitted?
**Counter:** emit "ok" on every successful call, for liveness and success rates.
**Why it fails:**
- Liveness per call is the heartbeat's job; it already beats on every message, chunk and pause.
- A per-call "ok" from a 3,000-message fetch carries no verdict.
- Success counts are cheap for a consumer to keep on its own.

**Confidence:** HIGH. **Resolution:** "ok" is a recovery signal. It is emitted when a scope that was non-ok succeeds again:
- a waited method's retried call succeeds;
- a once logged-out account is authorised again;
- a group once without access reads.

**Fixed:** "ok" exists only as a transition back. **No longer allowed:** "ok" per call. **Depends on it:** emitters must remember which scopes are non-ok. **Model change:** "ok" marks an ending, not a pulse.

### A5 — Occurrences or transitions?
**Counter:** emit only on transitions — fewer events.
**Why it fails:** #4's "waited 4 times, 210 s total" needs each wait and its length; transitions alone collapse repeated waits on a method already "waiting" into one event and lose the durations.
**Confidence:** HIGH. **Resolution:** every non-ok occurrence is an event, plus "ok" on recovery. Transitions are derivable from the stream.
**Fixed:** occurrence-level events. **No longer allowed:** transition-only emission. **Depends on it:** the stream volume rules in A16. **Model change:** the stream is a ledger.

### A6 — A queryable current state?
**Counter:** tgdata stays stateless and consumers aggregate — simpler, and no disagreement between two `TgData` instances on one account.
**Why it fails:** the counter partly *holds*. Statelessness is a real virtue, and #4 asks for events. A last-known record in `health_check()` is a convenience for pollers, not part of the request.
**Confidence:** LOW. **Resolution (tentative):** events are the contract. A last-known account-scope verdict in `health_check()` is optional, for the description or plan to accept or drop.
**Fixed:** events are mandatory. **No longer allowed:** a design in which the record replaces the stream. **Depends on it:** nothing load-bearing. **Model change:** none at the core.

### A7 — Exception-safe or propagating?
**Counter (variant 5):** propagating, so a consumer can stop a run on a ban.
**Why it fails, structurally:**
- The operation that met a ban or logout already raises its own exception to the caller, so stopping is already possible on the exception path.
- Some places events come from have nowhere to propagate *to*:
  - a logging handler, whose exceptions `logging` swallows via `Handler.handleError`;
  - Telethon's updates loop.
- A propagating contract cannot be uniform there.
- A monitor bug ending a scrape breaks P3.

**Confidence:** HIGH. **Resolution:** exception-safe. Callback errors are logged and never propagate. Sync and async callables are both accepted. The event is delivered before the operation's own exception is re-raised.
**Fixed:** delivery semantics. **No longer allowed:** stopping a run through the health callback. **Depends on it:** every emission site uses one safe dispatcher. **Model change:** health is a side channel, not control flow.

### A8 — What the mapping keys on
**Counter:** key on Telethon classes — typed and simple.
**Why it fails (verified, C2):**
- On Telethon 1.40 a frozen-account response arrives as a bare `FloodError` whose `.message` is `FROZEN_METHOD_INVALID`. A class-keyed map either misses it or reads it as a flood.
- Known classes carry only the category in `.message`, so a name-keyed map alone misses them.

**Confidence:** HIGH. **Resolution:** Telegram's error identity, read two ways — the specific class (by name, so a class absent from an older Telethon costs nothing) when Telethon knows the error, else the raw `.message` of a category instance. A category fallback applies last:
- the unauthorised or auth-key family → logged out;
- `FloodError` → waiting only if it carries seconds.

Anything still unmapped is reported as **unclassified**, with its name — never forced into one of the six.
**Fixed:** the lookup order. **No longer allowed:** category-only mapping; a `FloodError` without seconds read as waiting. **Depends on it:** the restricted row (A9) and the calibration channel (PH1). **Model change:** the table is keyed on the wire, robust across Telethon versions.

### A9 — What "restricted" means for an account that only reads
**Counter:** drop it — unobservable for readers, so five states.
**Why it fails:** frozen accounts exist, and their error arrives in the flood family. Without a "restricted" row it would be read as "waiting" (A8), and a frozen account would be retried forever.
**Confidence:**
- (a) HIGH that the state stays, detected by name: `FROZEN_METHOD_INVALID`, `FROZEN_PARTICIPANT_MISSING`, `USER_RESTRICTED`, and `PEER_FLOOD` if it ever appears;
- (b) LOW on *which reads* a frozen account fails — behavioural and unobserved.

**Resolution:** keep "restricted"; document the row as "by documentation, unobserved".
**Fixed:** the row and its names. **No longer allowed:** inferring "restricted" from silence or from a category. **Depends on it:** documentation honesty. **Model change:** one state is admitted to be under-evidenced.

### A10 — Banned vs. logged out
**Counter:** fold a deactivated or deleted account (`USER_DEACTIVATED`) into "logged out" — it also "can't log in".
**Why it fails:** "logged out" promises recovery by logging in again; a deactivated account cannot. Mixing them sends an operator to re-login an account that is gone.
**Confidence:** HIGH. **Resolution:**
- *banned:* `USER_DEACTIVATED_BAN`, `USER_DEACTIVATED`, `PHONE_NUMBER_BANNED`.
- *logged out:* `AUTH_KEY_UNREGISTERED`, `SESSION_REVOKED`, `SESSION_EXPIRED`, `AUTH_KEY_INVALID`, `AUTH_KEY_DUPLICATED`, and tgdata's own detection of a revoked session.

The event always carries the exact error name, so a consumer can tell a ban from a deactivation.
**Fixed:** the two rows. **No longer allowed:** recoverable and terminal verdicts sharing a state. **Depends on it:** the classifier table. **Model change:** terminal and recoverable are distinguished.

### A11 — The cache-miss
**Counter:** report raw "Could not find the input entity" as "no access" — it is the commonest real failure (K6), and dashboards should see it.
**Why it fails:** tgdata added the dialog sync (0.0.5) precisely because fresh sessions raise this for groups they *can* read. Reporting it unresolved would show false "no access" on readable groups.
**Confidence:** HIGH. **Resolution:**
- "No access" comes only from confirmed verdicts: `GroupAccessError` after the sync, or `CHANNEL_PRIVATE`, `CHAT_FORBIDDEN`, `CHANNEL_INVALID`, `USER_BANNED_IN_CHANNEL`, `CHANNEL_PUBLIC_GROUP_NA` from Telegram.
- A raw cache-miss is not a health signal.
- Extending the sync to the count, search and download paths belongs to the entity-resolution follow-up already recorded in `scoped/10/critic.md` (R3 long-term).

**Fixed:** the source of "no access". **No longer allowed:** unresolved cache-misses as verdicts. **Depends on it:** the scope of the follow-up. **Model change:** the commonest signal is deliberately quiet until resolved.

### A12 — Seeing silent waits
**Counter:** set the flood threshold to 0 so every wait raises and tgdata handles it everywhere.
**Why it fails:** that changes behaviour at every call site — each would have to catch, sleep and retry — and breaks callers who rely on Telethon's transparent short sleeps (P2). The per-client logger observes the same sleeps without changing them (C3, verified).
**Confidence:** HIGH. **Resolution:** each client gets its own `base_logger` from the single factory. A handler on that client's logger turns each sleep record into a "waiting" event, with seconds and request type from the record's arguments. Global log levels and propagation are left as they are.
**Fixed:** the observation mechanism. **No longer allowed:** changing Telethon's sleeping behaviour for #4. **Depends on it:** the client factory. **Model change:** the invisible becomes reportable without changing a single wait.

### A13 — Account identity
**Counter:** the Telegram user id alone — the true identity.
**Why it fails:** the id is unknown until an authorised call succeeds, and a logged-out account cannot supply it — exactly when the event matters. The session name is always known.
**Confidence:** HIGH for the composition; LOW for the label's API name. **Resolution:** `account` = {an optional caller-given label, the resolved session name, the user id once known}.
- The label carries cross-machine identity (#10) without a network call.
- The config path stays out of events: it is a local path, meaningless on another machine.

**Fixed:** three identity fields. **No longer allowed:** requiring a network call to name the account. **Depends on it:** the envelope. **Model change:** identity survives a logout.

### A14 — The persistent path's logout (scope question 5)
**Counter (warm variant 1):** report only; file the fix separately; keep #4 small.
**Why it fails as stated:** report-only cannot report it. On the persistent path the only way to know a session is logged out, short of running `start()`, is to check authorisation first (K3). Having checked, calling `start()` anyway knowingly sends a login code.

**Second counter:** put the fix inside #4, since reporting depends on it.
**Why that is weaker:**
- The fix is smaller and more certain than #4, with live harm (11 codes observed). CONTRIBUTING §4.5 names exactly this case: a prerequisite smaller and more certain than what it unblocks.
- Bundling delays the harm fix behind a heavy feature.

**Confidence:** HIGH that a truthful authorisation check must exist before #4 can report logouts. MEDIUM that it ships as its own prerequisite bug rather than inside #4.

**Resolution:** a prerequisite bug — *authorisation checks tell a logout from a wait, and a headless process never requests a login code*. It covers:
- the persistent path: detect a revoked session before `start()`. Without a terminal, raise `AuthRequiredError` and send no code; with a human at a terminal, interactive re-login is allowed. A session with no auth key keeps today's first-login flow.
- the use-and-close check: classify `GetState`'s actual error instead of `is_user_authorized()`'s boolean.

#4 then emits "logged out" or "banned" at those detection points.

**Fixed:** the dependency direction (#4 is blocked by the bug). **No longer allowed:** #4 shipping with a persistent path that misreports a logout as a connection error; any code path requesting a login code without a terminal. **Depends on it:** #4's plan ordering; #8's step login builds on the same detection. **Model change:** scope question (5) is answered as a prerequisite, not as in-or-out.

### A15 — Where events come from
**Counter:** instrument each call site in the engines individually.
**Why it fails:** that means many sites and drift — the same lesson as the single client door. Escaping errors share one boundary, the public `TgData` calls. Only the places that *handle* or *swallow* a signal need their own emission, and those can be listed.
**Confidence:** HIGH. **Resolution:** five mechanisms.
1. **The facade boundary.** Any exception escaping a public `TgData` call is classified, emitted, and re-raised unchanged.
2. **Handled waits.** The fetch loop's flood handler, and discovery's request and post-reading waits.
3. **Silent sleeps.** Through the per-client logger (A12).
4. **Swallow points.** The poll loop (emit, then continue), discovery's seed and link skips (Telegram verdicts only), and the real-time path (`run_with_event_loop` re-raising the updates error).
5. **Authorisation checks.** Both paths, after the prerequisite (A14).

**Never emitted:** per-message file and media errors; user handler exceptions; raw cache-misses; transport errors; configuration errors.
**Fixed:** the emission inventory. **No longer allowed:** ad-hoc per-site emission. **Depends on it:** the plan's step structure. **Model change:** one boundary plus four enumerated internals.

### A16 — Stream volume
**Counter:** dedupe or rate-limit events to protect consumers.
**Why it fails:** with A15's filter, events come only from Telegram verdicts and waits. Within a fetch, a wait is handled once per interruption, and verdicts end the operation. Volume is bounded by Telegram's own rate of saying no. Dedupe would lose the counts A5 needs.
**Confidence:** HIGH. **Resolution:** no dedupe; the filter is the bound.
**Fixed:** no suppression. **No longer allowed:** dropping repeated waits. **Depends on it:** A15's filter. **Model change:** none.

### A17 — Load-bearing names (H4 / H9)
**Counter:** "health state" is a loop-coined frame; use "error classification".
**Why it fails:** "account health", "events" and the six state names are the user's and the issue's own words. Renaming would mismatch every consumer issue (#3, #9, #10 say "health events").
**Confidence:** HIGH. **Resolution:** keep "health event" and the six names. Add *scope*, *verdict* and *unclassified* as the minimum new vocabulary.
**Fixed:** vocabulary. **No longer allowed:** renaming the six. **Depends on it:** the docs and the event's field names. **Model change:** none.

### A18 — Specific vs. pattern: the storm (H5)
**Counter:** the login-code storm was one consumer on one old version on one day — a one-off.
**Why it fails:** the mechanism is general. Every persistent-path client with a configured phone runs `start()` on each connect; on a revoked session with no terminal it requests a code and fails, and any retry loop repeats it. tgdata 0.0.8 still has this path (triage #3, #55).
**Confidence:** HIGH. **Resolution:** a pattern, not an incident; it justifies A14's prerequisite.
**Fixed:** the bug's scope is every headless consumer. **No longer allowed:** treating it as a consumer misconfiguration. **Depends on it:** the bug's priority. **Model change:** none.

## SV4 — Clarified

**Clear now:**
- **Verdicts:** six, at three scopes, plus an "unclassified" report for unmapped Telegram errors.
- **Events:** plain-data occurrences, with "ok" only on recovery.
- **Mapping:** keyed on Telegram's error identity — class first, then raw name, then a careful category fallback.
- **Silent waits:** observed through per-client loggers.
- **Callback:** one exception-safe callback per account.
- **Emission:** five enumerated mechanisms.
- **Account identity:** label, session name, and user id when known.
- **Prerequisite:** a separate bug makes authorisation checks truthful and stops headless login-code requests.

**No longer viable:**
- an account-wide "waiting" or "no access";
- transport errors as health;
- a per-call "ok";
- transition-only events;
- a propagating health callback;
- class-only or category-only mapping;
- raw cache-misses as "no access";
- changing Telethon's sleep behaviour;
- report-only on the persistent path.

---

## Phase 4 — Degrees-of-freedom reduction

**Fixed:** A2, A3, A4, A5, A7, A8, A9a, A10, A11, A12, A13 (composition), A15, A16, A17, A18, and the prerequisite's existence (A14).

**Eliminated:**
- warm variants 1 (report-only on the persistent path), 3's seventh state, and 5 (propagating);
- variant 4's "no behaviour change" — it survives only for #4 itself, with the behaviour change moved into the prerequisite.

**Still open — for the description, plan or critique:**
- A6 — whether to keep a last-known record in `health_check()`;
- A9b — which reads a frozen account fails;
- A13b — the label's API name;
- A14 — prerequisite vs. bundled (MEDIUM).
- **Detail:** whether the prerequisite raises Telethon's floor — not required, by A8's name fallback.

## SV5 — Constrained

The solution space is a single shape with four small open parameters. #4 is a side channel:
- a classifier (verdict, scope, error identity);
- an envelope (plain data, extensible `kind`);
- one exception-safe dispatcher per `TgData` instance;
- five emission mechanisms.

It sits on top of a truthful authorisation layer that a prerequisite bug provides. Nothing a caller catches today changes because of #4.

---

## Phase 5 — Conceptual stabilization

**The coherent interpretation.** "Report account health states as events" means: tgdata tells its caller, through one safe side channel, every time Telegram says no — which verdict, about what scope, from which call, and for how long — and when that "no" ends. It never acts on those verdicts itself and never changes what callers catch today.

**The problem structure.**
1. **Verdict model** — six verdicts at three scopes, plus unclassified.
2. **Mapping** — specific class, then raw name, then a careful category fallback.
3. **Envelope** — `kind`, time, account {label, session, user id}, verdict, scope, group, call, wait seconds, error name, source.
4. **Delivery** — one exception-safe callback per `TgData`, sync or async, event before re-raise.
5. **Emission** — the facade boundary, handled waits, silent sleeps via per-client loggers, swallow points, authorisation checks.
6. **Prerequisite** — truthful authorisation checks, and no headless login-code requests.

**The stable action framework.**
1. File and fix the prerequisite bug first: authorisation truthfulness and the end of the login-code storm.
2. Then build #4 on top, as this model.
3. Leave A6, A9b and A13b open for the description and plan to settle with evidence.

*Accommodation check (H6).* Revisions across phases refined the model; none patched it. Every perspective added an anchor type (logger attribution, the owner as stakeholder, `kind` extensibility, version phases) without forcing a structural redo. No model misfit.

## SV6 — Stabilized model

**Account health events are a read-only side channel of Telegram's verdicts.**
- **Six verdicts at three scopes:**
  - *account* — logged out · banned · restricted · ok;
  - *method* — waiting;
  - *group* — no access.
- **Unclassified.** Telegram errors the table does not know are reported as unclassified with their name, so the table can grow from evidence.
- **Mapping.** Each occurrence is classified by Telegram's own error identity — Telethon's specific class when it knows the error, the raw name when it does not — never by category alone. A frozen account is therefore recognised even on Telethon 1.40, and never mistaken for a wait.
- **The event.** Each occurrence becomes a plain-data event carrying the account (label, session name, user id when known), the scope, the call, any wait length, and the exact error name. "ok" is sent when a non-ok scope recovers.
- **Delivery.** One exception-safe callback per account delivers them.
- **Sources.** Events come from the public-call boundary, the engines' handled waits, Telethon's otherwise invisible short sleeps (through each client's own logger), the poll loop and discovery skips, the real-time path, and the authorisation checks.
- **The prerequisite.** Those authorisation checks must first become truthful — a bug that also ends the observed login-code storm. It is its own prerequisite issue, smaller and more certain than #4.

**How it differs from SV1.**
- SV1 imagined labelling errors into one account state and calling a callback.
- SV6 separates *scope* (account / method / group) from *verdict*.
- It keys the mapping on the wire-level identity — verified against Telethon's conversion code — so frozen accounts and future errors are not misread.
- It makes the invisible waits reportable without changing them.
- It fixes the callback as a safe side channel.
- It discovers that the scope question (5) is really a dependency: correct reporting on the persistent path needs a smaller bug fixed first.

## Telemetry

- **Perspectives:** 10 checked; 9 produced new anchor types; Risk and Ethical were the most destabilising.
- **Ambiguities:** 18 identified; 14 resolved HIGH; 1 resolved MEDIUM (A14's packaging); 3 LOW or open (A6, A9b, A13b).
- **SV delta:** large — the scope split, wire-keyed mapping, logger attribution, and a prerequisite dependency.
- **Anchor diversity:** all five types, from eight perspectives.
- **Failure-mode scan:**
  - *anchor dominance* — no; the model stands on the hierarchy, the scopes, the callback precedent and observed harm, and removing any one leaves the others standing.
  - *clean-resolution trap* — every resolution states and tests its strongest counter.
  - *perspective blindness* — the uncomfortable perspective (the owner harmed; "keep #4 small") was run.
  - *self-reference* — not applicable.
