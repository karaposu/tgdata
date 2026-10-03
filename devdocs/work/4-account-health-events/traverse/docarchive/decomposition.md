---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

devdocs/work/4-account-health-events/traverse/_branch.md — inputs in that folder: sensemaking.md (the stabilized model SV6 to decompose), articulate_warm.md, surfacing.md, articulate_simple.md. SAVE the output as devdocs/work/4-account-health-events/traverse/decomposition.md

---

# Decomposition — account health events (DV1)

**The whole, in one paragraph** (the prerequisite check — sensemaking SV6). Account health events are a read-only side channel of Telegram's verdicts:
- six verdicts at three scopes, plus "unclassified";
- classified by Telegram's error identity;
- delivered as plain-data events through one exception-safe callback per `TgData`;
- emitted from five mechanisms;
- built on a prerequisite that makes authorization checks truthful and stops headless login-code requests.

## Step 1 — Coupling topology

**Elements:**
- **E1** verdict taxonomy, scopes, and "ok" as recovery;
- **E2** the mapping table;
- **E3** error-identity extraction;
- **E4** the event envelope;
- **E5** account identity;
- **E6** the dispatcher;
- **E7** recovery tracking;
- **E8** the facade boundary;
- **E9** engine-handled waits;
- **E10** silent sleeps via per-client loggers;
- **E11** swallow points (poll loop, discovery skips, real-time path);
- **E12** authorization-check emission;
- **E13** the prerequisite (truthful authorization checks, no headless login codes);
- **E14** the "never emitted" filter;
- **E15** honesty annotations (unobserved rows, the unclassified report).

**Pairs, by the test "change A → must B change?"**

| Pair | Coupling | Why |
|---|---|---|
| E1–E2, E2–E3, E2–E14, E2–E15 | strong | the table *is* the taxonomy applied to identities; the filter and annotations are rows of it |
| E3 – wrapped exceptions | strong | found bottom-up: errors reach the boundary wrapped — `RuntimeError` from a give-up, `ConnectionError` from authentication, `DiscoveryInterrupted` — so extraction must walk the cause chain |
| E4–E5 | strong | identity is a field of the envelope |
| E1–E4 | moderate | the envelope carries verdict and scope names |
| E6–E7 | strong | recovery is stateful emission logic inside delivery |
| E7–E8, E7–E9, E7–E10 | moderate, **hidden** | found bottom-up: "ok" after a silent sleep is knowable only because the *public call* that contained it completed. Recovery needs a per-call context the boundary opens and the wait sites write into |
| E8–E9 | moderate, **hidden** | a wait handled in the fetch loop and later re-raised from its give-up must not be counted twice — an "already emitted" mark crosses the boundary |
| E10 – logging config | strong, **hidden** | found bottom-up. Seeing sleep records needs INFO records on the per-client logger. Raising that logger's level leaks INFO to a user's root console handler; cutting propagation hides Telethon's warnings. Renaming loggers away from `telethon.*` breaks users' existing logging config |
| E10 – client factory | strong | `base_logger` is a constructor argument |
| E12–E13 | strong | E12 emits at detection points E13 creates |
| E13 – everything else | weak | E13 hands over detection points plus the original error as the cause; it uses none of the taxonomy |
| E8, E9, E10, E11, E12 – E2/E3 | moderate | every site calls one classifier |
| E8, E9, E10, E11, E12 – E6 | moderate | every site calls one dispatcher |

**Clusters (peaks):**
1. *Classification* — E1, E2, E3, E14, E15.
2. *Envelope* — E4, E5.
3. *Delivery* — E6, E7, plus the call context.
4. *Signal capture*, three sub-peaks by signal source (sensemaking S1):
   - exceptions — E8, E11;
   - waits — E9, E10;
   - authorization — E12.
5. *Prerequisite* — E13.

**Valleys (boundaries):**
- classifier ↔ sites: one pure function;
- envelope ↔ delivery: one data type;
- delivery ↔ sites: the dispatch and call-context API;
- prerequisite ↔ authorization capture: detection points plus the cause.

## Step 2 — Boundaries, top-down

The weakest coupling sits at the four valleys above. That gives seven pieces:
- **P0** prerequisite;
- **P1** classification;
- **P2** envelope and identity;
- **P3** delivery and recovery;
- **P4a** exception capture;
- **P4b** wait capture;
- **P4c** authorization capture.

The boundary between P4a and P4b is a narrow single point: the "already emitted" mark. The boundary between P3 and P4 is diffuse: the call context is shared by all capture pieces, so it is defined in P3 and only consumed by P4.

## Step 3 — Validation, bottom-up

| Atom | Lands in | Agrees? |
|---|---|---|
| a `FrozenMethodInvalidError` raised out of `get_messages` on Telethon 1.42 | P4a captures → P1 classifies (restricted) → P2 envelope → P3 delivers | yes |
| the same response on Telethon 1.40 — a bare `FloodError` carrying `FROZEN_METHOD_INVALID` | same path; P1's raw-name lookup | yes |
| a 30 s sleep Telethon takes inside `GetHistory` | P4b via the per-client logger → P1 → P3; recovery when the public call completes | **initially no** — recovery needed the public call. Fixed by giving the call context to P3 (Step 2) |
| fetch gives up after its fourth wait: `RuntimeError` raised from `FloodWaitError` | P4b emitted each wait; P4a sees the `RuntimeError` | **initially no** — double count, and a wrapped cause. Fixed by the mark contract (P3) and cause-chain walking (P1) |
| `AUTH_KEY_UNREGISTERED` at persistent connect | P0 detects → `AuthRequiredError` from the original → P4c → P1 (logged out) | yes |
| `USER_DEACTIVATED_BAN` at connect | same; P1 tells a ban from a logout through the cause | yes |
| a throwaway session (never logged in) | P0 keeps the first-login flow; P4c emits nothing | yes |
| "Could not find the input entity" in `get_message_count` | P1's filter: not a signal | yes |
| a user's `@on_new_message` handler raising | not captured (E14) | yes |
| a user who configured `logging.getLogger('telethon')` | P4b must keep their visibility | **initially no** — no piece owned it. Moved into Q4b's criteria |

**Confidence:** top-down and bottom-up agree after the three corrections, all absorbed into existing pieces with no new boundary. High.

## Step 4 — Question tree

### Q0 — P0, prerequisite (its own bug issue, outside #4)
**How do tgdata's authorization checks tell a logged-out session from a waiting or never-logged-in one, and never request a login code from a process with no one to type it?**
- [ ] The persistent path checks authorization before Telethon's interactive `start()`.
- [ ] A session holding an auth key that Telegram rejects (the unauthorized or auth-key families) raises `AuthRequiredError` with the original Telegram error as its cause. No login code is requested when stdin is not a terminal; with a terminal, interactive re-login stays available.
- [ ] A session with no auth key keeps today's first-login flow.
- [ ] A wait at any authorization check raises the wait (`FloodWaitError`), never "not authorized". This fixes `ephemeral_client`'s use of `is_user_authorized()`.
- [ ] Tests with a stand-in client returning a logout, a ban, a wait and an authorized answer give the expected exceptions, with `send_code_request` never called headlessly.
- [ ] Filed as a `bug`, priority set from the observed storm (11 code requests in 70 minutes).

### Q1 — P1, classification
**Given any signal tgdata observes — an exception (possibly wrapped), a Telethon sleep record, an authorization verdict, or the updates loop's stored error — what verdict, scope and Telegram error identity does it carry, if any?**
- [ ] **Identity.** The specific Telethon class name when Telethon knows the error. The raw `.message` when the instance is a bare category class. The cause chain (`__cause__`, `__context__`) is walked to reach a Telegram error inside `RuntimeError`, `ConnectionError`, `AuthRequiredError` and `DiscoveryInterrupted`.
- [ ] **Table:**
  - *waiting* — the flood-wait family, with seconds;
  - *logged out* — `AUTH_KEY_UNREGISTERED`, `SESSION_REVOKED`, `SESSION_EXPIRED`, `AUTH_KEY_INVALID`, `AUTH_KEY_DUPLICATED`;
  - *banned* — `USER_DEACTIVATED_BAN`, `USER_DEACTIVATED`, `PHONE_NUMBER_BANNED`;
  - *restricted* — `FROZEN_METHOD_INVALID`, `FROZEN_PARTICIPANT_MISSING`, `USER_RESTRICTED`, `PEER_FLOOD`;
  - *no access* — `CHANNEL_PRIVATE`, `CHAT_FORBIDDEN`, `CHANNEL_INVALID`, `USER_BANNED_IN_CHANNEL`, `CHANNEL_PUBLIC_GROUP_NA`, and `GroupAccessError`.

  Each row is marked *observed* or *by documentation, unobserved*.
- [ ] **Fallback.** The unauthorized or auth-key category → logged out. `FloodError` → waiting only when it carries seconds. Anything else → **unclassified**, carrying its name.
- [ ] **Filter.** No signal from: transport errors with no Telegram cause, configuration errors, raw cache-misses, file or media errors, or user-handler errors.
- [ ] **Scope.** Account; method, keyed by the request type from `.request` or the sleep record; or group, from the call context or the error's request.
- [ ] **Offline tests.** Every row through `rpc_message_to_error` on Telethon 1.40, including `FROZEN_METHOD_INVALID` as a bare `FloodError`. Wrapped-exception cases. A sleep-record fixture.
- [ ] **A9b recorded.** Which reads a frozen account fails is unobserved.

### Q2 — P2, envelope and identity
**What does one health event look like as plain data, and how is the account named in it?**
- [ ] **Fields:**
  - `kind` (`"health"`);
  - `time` (UTC ISO 8601);
  - `account` {`label`, `session`, `user_id`};
  - `verdict`, `scope`, `group`, `call`;
  - `wait_seconds`;
  - `error` — Telegram's name;
  - `source` — `error` | `sleep` | `auth` | `updates`.
- [ ] **Plain data only** — strings, numbers, `None`, dicts; JSON-serializable; no Telethon objects or exceptions.
- [ ] **Account.** An optional caller-given `label` (its API name is open — A13b). `session` is the resolved session name. `user_id` is filled only from what Telethon already knows, never by a new network call. The config path is never included.
- [ ] **`kind` is documented as extensible** for future producers (#3, #8, #9), none defined here.
- [ ] **README:** one example event per verdict.

### Q3 — P3, delivery and recovery
**How does an event reach the caller safely, and how does tgdata know a non-ok scope has recovered?**
- [ ] **Registration.** One callback per `TgData`, given at construction (API name decided in the description). Sync and async callables are accepted.
- [ ] **Exception-safe.** Callback errors are logged and never propagate. Dispatch works both from coroutines and from synchronous logging handlers; an async callback reached from a synchronous context is scheduled, not awaited.
- [ ] **Ordering.** The event is dispatched before the operation's own exception is re-raised.
- [ ] **Call context.** The facade boundary opens one per public call (a context variable, so concurrent calls stay separate). Capture sites record the non-ok scopes they saw, and the group or call the event concerns.
- [ ] **Recovery:**
  - *method* scopes that waited during a call recover when that call completes successfully;
  - the *account* scope recovers on the first successful authorized call after logged out, banned or restricted;
  - a *group* scope recovers on a successful read of that group.
- [ ] **No double emission.** An exception already emitted is marked, and the boundary does not emit it again.
- [ ] **A6 decided** in the description: a last-known account verdict in `health_check()`, or none.
- [ ] **Tests:**
  - a raising callback does not break a fetch;
  - an async callback receives events;
  - recovery events follow a simulated wait;
  - a give-up after four waits gives four waiting events, not five.

### Q4a — P4a, exception capture
**Where do escaping and swallowed Telegram errors become events?**
- [ ] One wrapper mechanism covers every public `TgData` method that talks to Telegram — not per-method code:
  - `list_groups`, `get_messages`, `get_message_count`, `search_messages`, `download_media_by_id`;
  - the four discovery calls;
  - `validate_connection`, `run_with_event_loop`, `poll_for_messages`.
- [ ] Exceptions are re-raised unchanged, in type and identity.
- [ ] The poll loop classifies and emits each swallowed error before it continues.
- [ ] Discovery's seed and link skips emit Telegram verdicts only — not budget exhaustion, not lookup `ValueError`s.
- [ ] The real-time path emits the updates loop's stored error when `run_until_disconnected` re-raises it. User-handler exceptions are not emitted.
- [ ] Tests: a stand-in raises each verdict through `get_messages` and the poll loop, giving one event each, with the exception unchanged.

### Q4b — P4b, wait capture
**How does every wait — whether tgdata handles it or Telethon sleeps through it silently — become exactly one waiting event attributed to its account, method and call?**
- [ ] **Engine-handled waits** emit with seconds and request type: the fetch loop's flood handler, discovery's request loop, and its post-reading loop.
- [ ] **Silent sleeps.** Each `Sleeping[ early] for %ds (%s) on %s flood wait` record becomes a waiting event, using the record's arguments, **attributed to its account**. Two candidate mechanisms, for Innovation and Critique to judge — this piece fixes the requirement, not the solution:
  - *a per-client logger.* `base_logger` from the client factory. Exact, but it renames **every** Telethon logger of that client, not only `client.users`.
  - *the call context*, read by a handler on Telethon's own `telethon.client.users` logger. No renaming, but sleeps outside a tgdata call stay unattributed.
- [ ] **No logging side effects:**
  - INFO sleep records reach tgdata's handler even when the user's `telethon` level is WARNING;
  - they do not newly appear on a user's console;
  - Telethon's WARNING and above still reach the user's handlers exactly as before;
  - users who configured a specific Telethon sub-logger (for example `telethon.network`) keep their match.
- [ ] **No double count.** Telethon logs only the sleeps it performs. A wait above its threshold is raised, not logged, and is counted once by the engine handler.
- [ ] **Tests:**
  - a log-record fixture gives one waiting event;
  - a user's `telethon` handler still receives a Telethon warning;
  - a root console handler receives no new INFO lines.

### Q4c — P4c, authorization capture
**How do the authorization checks emit logged out, banned or waiting at the detection points P0 creates?**
- [ ] At the persistent-path and use-and-close detections, the event is classified from the cause (a ban vs. a logout) and emitted before `AuthRequiredError` propagates.
- [ ] A never-logged-in session emits nothing; it is configuration, not a verdict.
- [ ] Tests through stand-in clients, one per verdict.

## Step 5 — Interface map

| # | Source → target | What flows | Direction | Assumption made explicit |
|---|---|---|---|---|
| I1 | P0 → P4c | the detection points, and `AuthRequiredError` with the Telegram error as `__cause__` | one-way | P4c assumes the cause is always attached; P0 guarantees it |
| I2 | P1 → P4a, P4b, P4c | `classify(signal, context) → verdict \| unclassified \| none` | one-way | sites assume classification is pure and never raises |
| I3 | P2 → P1, P3 | the verdict and scope vocabulary; the envelope builder | one-way | P1 emits only names P2 defines |
| I4 | P3 → P4a, P4b, P4c | the dispatch API; the call-context API (open, record, close); the "emitted" mark | one-way | every site runs inside a call context opened by the boundary — except silent sleeps and the updates loop, which read it when present and tolerate its absence |
| I5 | P4b → P3 | waits recorded in the call context, for recovery | one-way | recovery assumes the sleeping task is the calling task (true: Telethon logs from inside the caller's coroutine) |
| I6 | client factory (connection engine) → P4b | the per-client logger and handler attachment — only if P4b takes the per-client-logger candidate | one-way | one factory builds every client — true since #1 |
| I7 | P3 → P1 | the call context's group and call, for scope | one-way | groups are known at the boundary from the call's arguments |
| I8 | P2 ← the `TgData` constructor | the account label, the session name, and the user id when known | one-way | no network call to fill it |

**Assumptions checked** (hidden coupling lives here):
- **wrapped errors** — owned by P1;
- **double emission** — the I4 mark;
- **logging side effects** — owned by Q4b;
- **sync-context dispatch of async callbacks** — owned by Q3;
- **the terminal check standing for "a human can answer"** — owned by Q0, with the caveat that IDE consoles and notebooks must be checked in the plan.

## Step 6 — Dependency order

1. **P0** can start immediately and runs in parallel with everything else, but must land before **P4c**.
2. **P2** (vocabulary first, then the envelope), then **P1**. P1 consumes P2's names; the vocabulary is small and goes first.
3. **P3**, which consumes P2's envelope and provides the call context.
4. **P4a ∥ P4b**, both consuming P1, P2 and P3. They are coupled only through the mark contract, which P3 owns.
5. **P4c**, after P0 and P3.

There is no circular dependency.

## Step 7 — Self-evaluation (full, 7 dimensions)

| Dimension | Score | Why |
|---|---|---|
| Independence | pass | each question is answerable through I1–I8 alone; P1 is a pure function, P2 data, P3 delivery, P4 capture sites |
| Completeness | pass | every SV6 element maps to a piece: the taxonomy, table, identity, filter and annotations (P1); envelope and identity (P2); delivery, recovery and call context (P3); five mechanisms (P4a, P4b, P4c); prerequisite (P0). Consumer behaviour (#3, #8, #9, #10) is excluded by design |
| Reassembly | pass | every piece answered plus every interface satisfied gives SV6. **Determination-mechanism check:** "ok" depends on a runtime determination of recovery, and Q3 specifies how (the call context). Scope depends on the request type and the group, and Q1 with I7 specifies how. The account depends on identity, and Q2 with I8 specifies how |
| Tractability | pass | each piece is one focused pass. P4a is one wrapper mechanism, not twelve edits |
| Interface clarity | pass | eight explicit interfaces, five assumptions named with owners |
| Balance | pass, with a note | P1 and P4b are the heaviest — the table and wire identity; the logging subtleties. P2 and P4c are light. No piece holds most of the work |
| Confidence | high | top-down and bottom-up agree after three corrections absorbed into existing pieces |

**Failure-mode scan:**
- *premature decomposition* — no; SV6 is one clear paragraph.
- *wrong boundaries* — no heavy interfaces.
- *hidden coupling* — three found and owned.
- *missing pieces* — the determination checks pass.
- *over-decomposition* — seven pieces for a heavy feature; none trivial except P4c, kept because it is the only piece gated by P0.
- *ignoring dependencies* — Step 6 is explicit.
- *imbalance* — none dominant.
