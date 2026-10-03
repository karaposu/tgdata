---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

devdocs/work/4-account-health-events/traverse/_branch.md — inputs in that folder: sensemaking.md (SV6 and its open items A6, A9b, A13b, A14 packaging), decomposition.md (the question tree; Q4b left open between two candidate mechanisms; Q3 dispatch from sync contexts; Q0 terminal check), articulate_warm.md, surfacing.md. Generate candidates for the open design points and for the shape of the whole, to be judged by critique. SAVE the output as devdocs/work/4-account-health-events/traverse/innovation.md

---

# Innovation — account health events

## Seed

**Type:** gap plus constraint. SV6 settled the core; seven points stay open:

| # | Open point | Source |
|---|---|---|
| O1 | how the authorization fix is packaged | A14, MEDIUM |
| O2 | how a silent sleep is attributed to its account | Q4b |
| O3 | how async callbacks are dispatched from synchronous contexts | Q3 |
| O4 | how tgdata knows "a human can answer" | Q0 |
| O5 | a last-known state view | A6, LOW |
| O6 | the account label's API | A13b |
| O7 | which reads a frozen account fails | A9b — behavioural, so innovation can only route around it |

Beyond those seven, the shape of the whole is itself open.

**Direction (valuation).**
- the observed login-code storm — real harm to an account owner;
- events that are trustworthy rather than merely present;
- the smallest new public surface;
- a consumer that will run 20 accounts in one process (#10).

**Methodology mode.**
- **Inherited:** Standard default — balanced coverage. The framing says "generate candidates … to be judged by critique".
- **Alternative:** Contrarian-rethink (Framer-weighted). Under it, the candidate space would centre on whether SV6's side-channel frame is right at all: whether tgdata should act on verdicts, or whether events need a new API at all.
- **Decision:** default. The Inherited Frame Audit below forces that contrarian territory into the set anyway, so a mode switch would add nothing the audit does not.

**Production-task mode** applies: the seed includes decomposition's piece list. Meta-decision pieces (per the criterion):
- **P0** — relationship plus intervention shape (i, v);
- **P1** — new vocabulary: scope, unclassified (iii);
- **P2** — the `kind` framing (ii);
- **P3** — the side-channel framing (ii).

P4b and Q0 are content-production.

---

## Phase 2 — Generate (seven mechanisms × generic / focused / contrarian)

### 1. Lens Shifting (Framer)

- **L1 — generic — under many accounts.**
  - Re-evaluate "one callback per `TgData`" when one process runs 20 instances (#10).
  - Per-instance callbacks become 20 registrations of the same function.
  - *Candidate:* the per-instance callback stays, and a process-wide sink is allowed as well, since every event already carries `account`.
- **L2 — focused — on O4: who decides that a human can answer?**
  - Under the lens of "most tgdata processes are unattended loops", inferring a human from `stdin.isatty()` is the wrong owner for the decision. IDE consoles, notebooks and `nohup` all blur it.
  - *Candidate:* a **revoked** session never prompts implicitly. Re-login is an explicit act — a call or flag the caller makes.
  - A first login on a session with no auth key keeps today's documented interactive path only when a terminal is present.
- **L3 — contrarian — events are for machines, logs are for humans.**
  - Under the lens of "whoever reads the stream", a log line is the channel ops already use. The consumer whose log showed zero waits (surfacing #15) would have seen them.
  - *Candidate:* every health event is also written as a structured record on a `tgdata.health` logger (`extra={"health": event}`).
  - Logging is exception-safe and works from synchronous contexts by design.

### 2. Combination (Generator)

- **C1 — generic — heartbeat + health → one observer object** (`on_beat`, `on_health`), replacing separate parameters.
- **C2 — focused — on O2: call context + Telethon's own logger.**
  - Combine P3's per-call context variable with a handler on Telethon's `telethon.client.users` logger.
  - The handler reads the active call context — which `TgData`, which public call — so a sleep is attributed without renaming any logger.
  - Sleeps outside a tgdata call stay unattributed, which is out of scope.
- **C3 — contrarian — fold P0 into #8.**
  - Authentication becomes never implicit: the persistent path stops calling `start()` at all, and every login goes through #8's step API or an explicit `login_interactive()`.

### 3. Inversion (Framer)

- **I1 — generic — invert "tgdata reports, never acts".**
  - *Level 1, component:* after a terminal verdict, the `TgData` instance refuses further calls until reset — a per-account circuit breaker.
  - *Level 2, system:* health is not reported *after* calls; it is the **admission control before each call*. The account's lifecycle is a state machine tgdata owns.
  - *Existence axis:* **I2** — zero push mechanisms. Pull-only: `health_check()` returns state, with no events.
- **I3 — focused, piece-level on P3 (side channel) — invert push to pull.**
  - An async iterator, `async for event in tg.health_events()`, backed by a bounded queue.
  - `put_nowait` is synchronous-safe, which answers O3 by construction.
- **I4 — contrarian, piece-level on P1 (three scopes) — one scope.**
  - Every verdict is about the account; group and call are detail fields.
  - "No access" and "waiting" are marked non-terminal instead of being scoped.
- **I5 — piece-level on P0, intervention-shape axis.**
  - *Committed shape:* **REFRAME-AS-BUG** — its own bug issue, a prerequisite.
  - *Alternatives:* **REPAIR** inside #4, which bundles it; and **DO-NOTHING**, which documents "do not run headless with a phone configured".
  - *What follows:* REPAIR ships the harm fix only when the heavy #4 ships. DO-NOTHING leaves every headless consumer exposed.

### 4. Constraint Manipulation (Framer) — both directions

- **K1 — ADD, generic — "no new public surface beyond one constructor parameter."** Forces delivery through `on_health=` only; everything else stays internal.
- **K2 — ADD, focused — "events must survive a restart."**
  - #4's "logged out after 9 days" cannot be computed by a callback in a process that restarted.
  - *Candidate:* an optional built-in JSONL sink, `health_log=path`, as one consumer of the callback.
- **K3 — REMOVE, generic — drop Telethon 1.40 compatibility** (floor ≥ 1.42) so the frozen-account errors are classes.
- **K4 — REMOVE, contrarian — drop "don't change Telethon's sleeping".**
  - Threshold 0 everywhere: every wait raises and is handled by tgdata, so waiting becomes a policy tgdata controls — the bridge to #9's budget.

### 5. Absence Recognition (Generator) — patch level and redesign level, both directions

- **A1 — patch, generic — no fault-injection harness.**
  - Every piece's tests need Telegram errors without Telegram.
  - *Candidate:* a test stand-in client that raises configured errors through Telethon's own `rpc_message_to_error`, usable by tgdata's smoke tests and by consumers.
- **A2 — patch, focused — no machine-readable verdict table.**
  - *Candidate:* the table as an exported data constant, the single source for the classifier, docs and consumers.
- **A3 — redesign, missing — no Account.**
  - Designed today, an `Account` would be first-class (label, config, session, proxy, identity, health). #1, #2, #5, #9 and #10 all attach to it, yet tgdata has only a config path.
  - *Candidate:* an `Account` value object.
- **A4 — redesign, already present in another form.**
  - `health_check()` already reports per-instance condition: proxy, device identity, primary connection, the pool's rate limits.
  - `DiscoveryInterrupted.retry_after`, `GroupAccessError` and `RateLimitInfo` already carry fragments of health.
  - *Candidate:* the pull form exists — add the push form, and let `health_check()` read from the same ledger.

### 6. Domain Transfer (Generator) — native and different

- **D1 — native, generic — Kubernetes conditions.**
  - Each object carries conditions (type, status, reason, message, last-transition time), plus a separate event stream.
  - *Candidate:* per-scope conditions — Authorized, NotBanned, NotRestricted, Throttled[method], GroupAccessible[group] — with last-transition times, alongside the events.
- **D2 — native, focused — circuit breakers and Retry-After.**
  - A wait is `Retry-After`; a terminal verdict is an open circuit; "ok" closes it after a half-open success.
  - *Candidate:* a per-method breaker state — the same shape as I1.
- **D3 — different, contrarian — medical triage, aviation alert levels.**
  - Readers act on severity, not on the diagnosis's name.
  - *Candidate:* a `severity` field — `terminal` (logged out, banned, restricted), `degraded` (waiting, no access) or `ok` — so a dashboard needs no knowledge of the six names.

### 7. Extrapolation (Generator)

- **E1 — generic — more verdicts will come.**
  - Telegram added frozen accounts and Telethon followed in 1.42, so new restriction kinds will keep appearing.
  - *Candidate:* the table as data (A2), the unclassified report as the calibration channel, and runtime extension (`extra_verdicts={…}`) so a consumer need not wait for a release.
- **E2 — focused — accounts per process grow (1 → 20).**
  - *Candidate:* tgdata keeps per-account counters — waits, total wait seconds, last verdict, since — so #4's example table is computed by tgdata.
- **E3 — contrarian — detection grows behavioural, so reporting stops protecting.**
  - *Candidate:* health events feed an optional pacing policy that slows down after waits, closing the loop.

---

## Inherited Frame Audit

**Seed's central assumption** (SV6): *#4 is a read-only side channel delivered by a push callback.*
Challenged by:
- I1 / I1b — tgdata acts, via admission control;
- I2 — no push at all;
- I3 — pull instead of push;
- L3 — logging as the channel;
- D2 — circuit breaker.

**Piece-level commitments:**

| Piece | Commitment | Challenged by |
|---|---|---|
| P0 | a separate prerequisite bug (shape REFRAME-AS-BUG) | I5 (REPAIR, DO-NOTHING), C3 (fold into #8) |
| P1 | three scopes, plus "unclassified" | I4 (one scope), D3 (severity instead of scope) |
| P2 | a flat event with an extensible `kind` | D1 (conditions plus events) |
| P3 | an exception-safe push callback | I3, L3, C1 |
| P4b | the per-client logger, or the call context | C2, K4 |
| Q0 | `isatty()` decides interactivity | L2 |

**Firing condition:** every assumption has at least one explicit challenge. **The audit does not fire.**

---

## Phase 3 — Test

Tests: **N**ovelty · **S**crutiny survival · **F**ertility · **A**ctionability · **M**echanism independence.

| Candidate | N | S — strongest objection, and the verdict | F | A | M | Disposition |
|---|---|---|---|---|---|---|
| **L2** revoked sessions never prompt implicitly; first login keeps the terminal path | ✓ | *Breaks scripts that rely on the first-run prompt.* No: only revoked sessions change, and first login is untouched. Survives | ✓ (#8 builds on it) | ✓ | ✓ L2 + C3 + I5 (shared input: the storm — a verified observation, not an assumption) | **ACTIONABLE** |
| **I5** P0 as its own bug (REFRAME-AS-BUG) vs. REPAIR vs. DO-NOTHING | — | DO-NOTHING fails (live harm). REPAIR delays the harm fix behind a heavy feature and breaks §4.5's "smaller and more certain first". REFRAME-AS-BUG survives | ✓ | ✓ | ✓ | **ACTIONABLE** — the principal shape holds |
| **C2** call-context attribution on Telethon's own logger | ✓ | *INFO records are not created unless `telethon.client.users` is at INFO — a global level change that leaks INFO to root handlers.* That applies equally to the per-client-logger option. Survivable only if the handler stops propagation and re-dispatches non-sleep records to the parent chain at the user's original effective level. Unproven | ✓ | ✓ | ✓ C2 + A4 | **RE-TEST TRIGGER** — the logging behaviour needs a probe before commitment; preferred over the per-client logger because it renames nothing |
| **L3** mirror every event to a `tgdata.health` logger | ✓ | *Users get logs they did not ask for.* No: INFO on a dedicated tgdata logger follows the user's own logging config, as all tgdata logging does today. Survives | ✓ | ✓ | ✓ L3 + A4 + surfacing #15 | **ACTIONABLE** |
| **D1 + E2 + A4** a state view in `health_check()`: per-scope verdict, since, counters | ✓ | *Statelessness is simpler, and two instances may disagree (A6's counter).* The view is derived from the same ledger the events come from, scoped to one instance and documented as in-memory; persistence stays the consumer's job. Survives | ✓ (#3, #9 add conditions) | ✓ | ✓ three mechanisms, independent inputs | **ACTIONABLE** — **RE-TEST TRIGGER** on A6 (LOW → proposed yes) |
| **D3** `severity` field | ✓ | *Redundant with the verdict.* No: a dashboard can colour by severity without knowing the six names, and future `kind`s get one too. Survives | ✓ | ✓ | ✓ D3 + L1 | **ACTIONABLE** |
| **A1** fault-injection stand-in client | ~ | *Test code shipped in the package.* It can live in `smoke_tests` first. Survives | ✓ | ✓ | ✓ every piece needs it | **ACTIONABLE** |
| **A2 + E1a** the verdict table as data | ✓ | *A constant is just code.* Its value is one source for the classifier, docs and consumers. Survives | ✓ | ✓ | ✓ A2 + E1 | **ACTIONABLE** |
| **E1b** runtime table extension | ✓ | No consumer has asked; it adds API | ✓ | ✓ | single | **DEFERRED** — revive when a verdict arrives that a consumer needs before a release |
| **O6** label defaults to the config file's stem, with an override parameter | ✓ | *A stem collides across folders.* The override exists for that. Matches the account-pool convention of one `<name>.ini` per account | ✓ | ✓ | ✓ L1 + A3-lite | **ACTIONABLE** |
| **I3** pull iterator | ✓ | *An undrained queue grows.* Bounded with drop-oldest plus a counter. But the callback is the primitive, and a queue is an adapter over it | ✓ | ✓ | single | **DEFERRED** — revive when #10's worker needs pull |
| **I1 / I1b / D2** admission control, circuit breaker | ✓ | *Changes control flow, against P2.* But it takes no outward action — it *withholds* calls, and a loop retrying a terminal account is exactly what the consumer did. The prerequisite already stops the harmful part (codes); what remains is harmless retries | ✓✓ (bridges #9, #10) | ~ | ✓ I1 + D2 | **DEFERRED** — revive on a retry storm of terminal verdicts other than login codes, or at #10's design |
| **K2** JSONL health log | ~ | Persistence is the consumer's job; a callback can write it | ~ | ✓ | single | **DEFERRED** — revive when a second consumer re-implements the same sink |
| **C3** never-implicit authentication | ✓ | #8 does not exist yet, so #4 cannot depend on it | ✓ | ✗ now | ✓ (L2) | **DEFERRED** — revive when #8 lands |
| **A3** Account value object | ✓ | Spans #1, #2, #5, #9 and #10; out of #4's scope | ✓✓ | ✗ in #4 | ✓ | **RESEARCH FRONTIER** |
| **E3** closed-loop pacing | ✓ | It is #9's scope | ✓ | ✗ in #4 | single | **RESEARCH FRONTIER** |
| **K4** threshold 0 everywhere | — | Re-tests sensemaking A12; still changes every call site | ✓ for #9 | ✗ | single | **RESEARCH FRONTIER** — for #9 |
| **C1** one observer object | ~ | Merges call and instance lifetimes (sensemaking L2) | ✗ | ✓ | single | **rejected** → seed: lifetimes decide the API boundary |
| **I2** pull-only | — | #4 asks for events; A5 needs every occurrence | ✗ | ✓ | — | **rejected** → seed absorbed into A4 |
| **I4** one scope | — | Sensemaking A3: one group's loss would mark a working account as broken. D3 gives the account-level summary without collapsing scopes | ✗ | ✓ | — | **rejected** |
| **K3** raise Telethon's floor | — | The raw-name fallback already covers 1.40, and future errors still need the fallback | ✗ | ✓ | — | **rejected** |
| **L1** process-wide sink | ~ | One function registered 20 times is fine; a global sink invites hidden state | ~ | ✓ | single | **DEFERRED** — revive at #10 |

**O7** (which reads a frozen account fails) has no candidate; innovation cannot produce behavioural evidence. It stays open.

### Assembly check

**Combining the survivors:** health is **one ledger, three views**.

1. **Push to code** — one exception-safe callback per `TgData`. Synchronous callables are called inline; async ones are scheduled. This answers O3.
2. **Push to humans** — the same event mirrored on a `tgdata.health` logger (L3).
3. **Pull** — `health_check()["health"]`: per-scope conditions with verdict, since, wait counters, and last error (D1, E2, A4). This answers A6 / O5.

All three are fed from one classifier whose table is exported data (A2). Each event carries a **severity** (D3) and an **account label** that defaults to the config file's stem (O6). Silent sleeps reach the ledger through **call-context attribution on Telethon's own logger** (C2), pending the logging probe. Underneath sits the **prerequisite bug**: revoked sessions never prompt implicitly, and first login keeps its terminal path (L2, I5). Every piece is verified with a **fault-injection stand-in** (A1).

**Emergent value no single piece has:**
- The callback, the log mirror and the state view **cannot disagree**: they are views of one ledger.
- The consumer whose log showed nothing would now see every wait and verdict **with zero integration code** — the log mirror plus the attributed sleeps.
- A dashboard can be built **from severity and since alone**.

### Axis coverage

| Axis | Variants |
|---|---|
| delivery shape | callback · iterator · logging · state view |
| how much behaviour changes | report-only · prerequisite fix · admission control |
| scope model | three scopes · one scope · conditions · severity |
| sleep attribution | per-client logger · call context · threshold 0 |
| persistence | memory · JSONL |
| P0 packaging | bug · bundle · do-nothing · fold into #8 |
| identity | label parameter · config stem · user id |
| table extensibility | static · data · runtime |

No axis is left without a variant.

**Per-row trace for the six verdicts:**
- *waiting* — C2, K4, D2.
- *logged out* — L2, I5, C3.
- *banned* — I1.
- *restricted* — K3, E1.
- *no access* — I4.
- *ok* — D1 recovery as a condition transition, D2 closing the circuit.

### RE-TEST TRIGGERS (carried to Critique)

1. **C2's logging mechanics:**
   - INFO sleep records must reach tgdata;
   - a root console handler must see no new INFO;
   - the user's `telethon` warnings must still flow;
   - the user's sub-logger configuration must still match.

   This is Python `logging` behaviour, settleable by a probe.
2. **Sensemaking A6** (LOW) — the state view is now proposed as yes, with a concrete shape (D1 + E2).

---

## Telemetry

- Generators applied: 4 / 4. Framers applied: 3 / 3.
- **Convergence: YES**, on three cores:
  - (a) implicit re-login is the hazard, so a prerequisite bug and explicit interactivity — L2, C3, I5;
  - (b) one ledger feeds a pull state view — D1, A4, E2;
  - (c) logging is already the channel people read — L3, A4, surfacing #15.
- **Survivors tested:** 23 of 23.
- **Failure modes observed:** none.
  - Survival-bias check: the most uncomfortable candidate, I1 (tgdata acts), was tested with extra care and **deferred with a trigger**, not killed.
  - Early frame lock: avoided — Q4b got three mechanisms.
- **Production-task telemetry:**
  - *Per-piece log:*
    - P0: [Inversion:intervention-shape (I5), Combination (C3), Lens (L2)]
    - P1: [Inversion:content (I4), Domain Transfer (D3), Extrapolation (E1)]
    - P2: [Domain Transfer (D1), Absence (A3), Lens (L1)]
    - P3: [Inversion:content (I3, I2), Lens (L3), Combination (C1)]
    - P4b: [Combination (C2), Constraint REMOVE (K4)]
    - Q0: [Lens (L2)]
  - *Meta-decision pieces:* P0, P1, P2, P3. *Content-production:* P4b, Q0.
  - *Piece-level Inversion compliance:*
    - P0 — **satisfied** on the intervention-shape axis (REFRAME-AS-BUG vs. REPAIR / DO-NOTHING);
    - P1 — satisfied (I4);
    - P3 — satisfied (I3, I2);
    - P2 — satisfied (D1 reshapes the envelope into conditions plus events; scored as Inversion-equivalent, since it reverses "flat events only").
- **Overall: PROCEED.**
