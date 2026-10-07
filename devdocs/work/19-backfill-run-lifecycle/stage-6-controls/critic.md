---
model: gpt-6-astra
effort: max
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the actual SDK/page adapter cannot enforce both real ledgers while
returning an exact usable prefix, or the unchanged strict state codec rejects the
specified control/retirement states without an invariant/schema change.
Affordable now: yes — local primitive checks plus roughly 210 requested history
slots, existing approved account/group, several seconds of real pacing; no writes
to Telegram or authoritative policy changes.

Experiment: before product edits, run current Stage 5 with a test-only two-ledger
adapter satisfying the complete reservation interface. Independently requalify
the small group, exhaust cap 3 in a bounded real read, persist/replay/accept its
prefix, increase only test cap to 6 preserving usage, enforce saved wait and make
another bounded real read. Assert both actual ledgers and actual send bounds.
Locally run actual codec candidates for pause/resume/cancel/abandon and headroom;
run both stricter-ledger orders, partial-claim failure and real SDK consumer checks.
Cost: under 250 requested history slots allocated within the total 1,000 Stage 6
ceiling; no media needed; under a few minutes excluding setup. Source account ID,
credentials and message content stay private.
Must precede: step 1 — task-impl's experiment gate; first composition-dependent
product cost is steps 2–3 and the required live evidence is step 6.
Disqualifying result: actual composition bypasses either budget, loses/changes a
valid prefix, needs a production budget/health redesign, or requires relaxing the
strict lifecycle schema to represent a contracted transition. Deprecate and stop.
Passing result: real prefix and later admission match independent IDs/dates, both
ledgers stay authoritative, test-only increase retains charges, premature prepare
does no source work, and real codec accepts all legal candidates/refuses invalid
retirement. Controlled fault boundaries retain conservative charges.

Result: PASS — 2026-10-07. Seven local actual-codec/SDK/ledger checks passed.
The real 46-message oracle matched both three-message prefixes; 206 requested slots
in four history calls, 5.3253478338 seconds between budgeted source sends, no early
send, and test cap 3 → 6 retained all charges. Shared policy stayed 5,000; actual
usage 2,202 → 2,254. No product code changed. See `prebuild-results.json`.

## High-level summary

The transition design fits the existing aggregate and reuses the appropriate
settlement owner. No meaning gap or product-layer redesign found. Two Medium risks
concern the live instrument's interface and cumulative ceiling. Test the actual
composition before building controls; fold selected instrument corrections if it
passes. Local fake source responses alone cannot establish this premise.

## Premise Inventory — ranked by waste if false

### 1. Budget/source composition remains the actual authority

**Premise:** adding a restrictive test ledger preserves actual SDK admission and
usable error prefixes without bypassing the existing account allowance.
**First dependent step:** product controls/settlement integration, steps 2–3, whose
mandatory Gate C proof is unavailable if this composition needs another design.
**Waste if false:** steps 1–5 built before discovery at step 6; several hours plus
unusable gate evidence. **Test scheduled at:** step 6, with possible earlier critic
falsifier acknowledged but not yet executed. **Cheapest earlier test:** the experiment
above using unchanged Stage 5, actual SDK, real ledgers and real source; <250 slots.
**Coverage:** test18 proves one ledger with real SDK/fake transport; Gate A/B prove
one ledger with real source; neither covers two-ledger return shape/composition.
The documented consumer in `budget_client._BudgetSender.send` reads `.amount` after
settlement. A tuple alone is non-covering/incompatible.

### 2. Existing strict aggregate expresses controls without migration

**Premise:** selected mutations satisfy codec cross-field invariants for pending,
exhaustion, terminal outcome, last control and abandonment, including cancelled-end
and accepted no-change commands. **First dependent step:** 1–2.
**Waste if false:** result/transition implementation and tests need redesign.
**Test scheduled at:** step 4; **Cheapest earlier test:** actual `_BackfillState`
construction/SQLite round trips before step 1, milliseconds.
**Coverage:** Stage 2 state tests and Stage 3–5 seeded preservation fixtures cover
many states, but not the complete proposed command matrix. Handwritten input is
appropriate here only because the real component under test is the strict codec;
it is not a substitute for later actual `control` concurrency tests.

### 3. Current session, source view and capacity remain usable

**Premise:** approved existing resource still permits bounded read-only observation.
**First dependent step:** live experiment and step 6. **Waste if false:** live case
is blocked, not a different control design. **Test scheduled at:** requalification.
**Cheapest earlier test:** same requalification before build; no additional source.
**Coverage:** prior A/B historical evidence only, so current availability unproven.
Carry as execution condition, not a severity-rated design risk or assumed PASS.

### 4. Implemented controls preserve real result/delivery ordering

**Premise:** Stage 6 implementation meets its contract at actual awaits.
**First dependent step:** public Stage 7 (outside this run).
**Waste if false:** no public API built; gate blocks before dependent stage.
**Test scheduled at:** offline step 4 then real step 6 before Stage 7.
**Cheapest earlier test:** cannot run unimplemented controls; unchanged settlement
has actual A/B and Stage 5 primitive evidence. Seeded controls are explicitly
non-covering for the new method. Ordering is already correct for this premise.

## Restart Check

This is an unfinished planned stage, not a repair of paused #7. Relevant established
failure mechanisms from the inherited gates are addressed as follows:

| Observed failure | Established mechanism | Design element |
|---|---|---|
| Store can commit and lose its reply | Actual SQLite close/process probes | Shared exact readback; retained command recognition, steps 2/4/6 |
| Worker can stop after source but before publication | Gate B unknown attempt retained | No implicit abandon/recovery; confirmed exit and exact recovery, steps 3/6 |
| Received data may still be unaccepted | Actual receiver-before-ack interruption | Cancel preserves pending; only explicit abandonment withdraws, steps 2/4/6 |
| Local failures must not become Telegram health | Prior raw-batch local-error probes | No new health owner/classification, steps 2/3 |

## Inherited Lessons

| Lesson | Ordering that satisfies it |
|---|---|
| Error is not rollback | Shared confirmation/recognition before live controls, steps 2/4 |
| Source end is not acceptance | Reuse closure and both terminal-order tests, steps 3/4 before 6 |
| Hash is not authority | Full context/ref checks, steps 1–4 before equal-hash live case |
| Timeout is not worker death | Local unknown/busy refusal then actual exited-worker Gate C before public API |
| Local work is not Telegram health | Keep health untouched, local no-network checks in step 4 |
| Ack/control/restart cannot reset wait/quota | Existing pacing reused; actual two-ledger experiment moves before build |
| Response arrival is not accepted order | Atomic revisions and delayed-response cases before public API |
| Existing evidence remains evidence | New private state, separate traffic allocations; A/B originals untouched |

## Risk 1 — Incomplete test reservation interface

**Risk**

The extra allowance used for the live test could approve a request and then fail
after Telegram has answered. The test would appear to find a scraping failure even
though it was caused by its own adapter, and might lose the evidence needed to
decide whether the lifecycle works.

Step 6 specifies returning both real reservation objects, but the real
`tgdata/budget_client.py::_BudgetSender.send` also reads `reservation.amount` after
`_settle`. A plain pair has no such attribute. The complete test-only reservation
must retain both actual claims and expose their identical admitted amount; local
interface checks must execute the real consumer, not only call ledger methods.

**Severity:** Medium. **Category:** API contract / verification validity.
**Impact:** false source failure, unverified prefix/gate and charged live requests.
**NoobEng:** the budget callback's result is not opaque to its SDK consumer; another
field is used to detect an overlarge source response after the budget settles.
**Affected areas:** Stage 6 probe wrapper and Gate C evidence; production adapter unchanged.

### Mitigation — Quick

Catch the attribute error and treat the already received response as success.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Use an immutable test-only composite reservation exposing `amount` and both real
claims; assert equal amounts. Run the complete actual consumer locally and live,
including oversized response and partial claim/settlement failure.
**Why this is robust:** preserves every consumed interface without changing production
budget code or weakening its oversize check.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Chosen: no second genuine production intersection consumer exists; the long-term class collapses to this instance. A small instrument value preserves the real adapter with less extent and complete reach.
*For future:* —

### Mitigation — Long-term

Introduce a production budget-intersection abstraction and documented protocol.
**Why this is long term effective:** would support multiple application policy layers
if real consumers need them; currently this test helper is the only instance.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Risk 2 — A per-worker ceiling does not bound the whole gate

**Risk**

Restarting a crashed live test can give it a new local allowance even though earlier
requests already happened. Several individually small tests could then exceed the
total read limit promised for this stage, especially when a worker dies before it
writes its final counter.

Step 6 names a 1,000 requested-slot total, but `ReadOnlyGuard` counters are per
process. The prebuild, crash worker, recovery worker and retries require a parent
allocation record that survives process failure. Inferring total usage only from
successful worker reports misses sends immediately preceding `os._exit`.

**Severity:** Medium. **Category:** Resource bound / verification validity.
**Impact:** extra account traffic and incorrect reported source ceilings.
**NoobEng:** the shared 5,000/day ledger still protects the account, but it measures
returned messages/conservative reservations, not the test's total requested-slot cap.
**Affected areas:** prebuild/Gate C orchestration, actual-send diagnostics.

### Mitigation — Quick

Sum successful worker reports at the end and mention missing crash counts.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Persist fixed per-launch slot allocations before starting any network worker; their
sum, including prebuild and retries, must stay within 1,000. A crash consumes its full
allocation for the ceiling. Each worker's guard enforces its allocation; diagnostics
persist send admission before awaiting responses. Do not reclaim uncertain allocations.
**Why this is robust:** a lost final report cannot grant more traffic, without building
a second distributed budget system. Actual observed counters can still be lower.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Chosen: the prebuild and crash/restart workers share one sequential launch mechanism, so a single allocation record covers them. A service adds coordination absent from this task; fixed reservations close the whole present gate without product changes.
*For future:* —

### Mitigation — Long-term

Build a shared durable test-request quota service for all future live gates.
**Why this is long term effective:** would coordinate independently scheduled workers
if that becomes a requirement. Current gate has one sequential parent and fixed bounds.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Preconditions and scope audit

Existing session/view/capacity are unchanged execution conditions. No OPEN planning
blocker was declared or found. New status fields are additive internal API; persisted
schema remains v1. Four bounded CAS attempts and one retained predecessor keep work/
storage bounded by existing policy. No new secret logging, package discovery, import
cycle or source-health path is proposed. The affordable experiment, not a claimed
proof from source reading, closes the live-composition premise before build.
