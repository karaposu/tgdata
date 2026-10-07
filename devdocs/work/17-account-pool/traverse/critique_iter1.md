# Critique — account pool candidate assembly, iteration 1

## User Input

Evaluate `innovation.md` against `_branch.md`, Sensemaking anchors and actual
dev95 probes. User scope: “Routing and failover for groups accounts can already
read; keep #7 paused (recommended).”

## Phase 0 — dimensions and premise prosecutions

| Dimension | Weight | Substance-level success criterion / external anchor |
|---|---|---|
| D1 Account ownership | Critical | The actual ID at a history send is the expected ID; the 222/111 probe must not recur in pool reporting. |
| D2 Durable restrictions / uncertainty | Critical | A crash or failed store write cannot make an unsettled account immediately eligible. Inspect actual CAS/admission history, not the word persistent. |
| D3 Delivery preservation | Critical | Completed prefixes and saved receipts survive source changes; actual current engines must replay without source selection. |
| D4 Bounded routing and scope | Critical | No joining, prompts, hidden unlimited retries, or local errors classified as account health. |
| D5 Coherence and feasibility | High | Existing factory/ledger/progress behavior stays intact; required seams exist in actual source. |
| D6 Operational clarity | High | No-eligible/busy/repair/visibility outcomes actionable; live evidence bounded. |
| D7 Parsimony | Noncritical | Minimum additional source-state authority; no second quota or cursor implementation. |

Premise prosecutions independent of candidate choice:
- If identity were already trustworthy, P1 ownership might be redundant. Actual
  probe fresh222/cached111 disproves that premise; user_id reporting and billing
  have different authorities today.
- If durable delivery required a stable account, P4 integration would be wrong.
  Actual SQLite replay probes changed the source identity and made zero new reads;
  current docs say “Progress belongs to the canonical group, independently of the
  account that reads it.” Visibility remains a separate qualified claim.
- If a known failure were always durably recorded, P2's minimal facts would be
  enough. SQLite write failures and process death can occur after the server
  answers but before a new fact commits. The candidate must handle that interval.

Axis audit spans failures inside and between operations, not merely valid state
shapes. The broad reading of ownership includes cancellation and pre-identity
failures. No test manufactures a ban or spends a real account's allowance.

## Phase 1 — landscape

Viable: owned bounded readers + guarded ledger + original progress authority.
Dead: shared legacy summaries, duplicate acknowledgment, hedged source calls,
forgetting known waits, source-format migration for routing metadata.
Boundary: durable observations around uncertain source/store transitions;
timeout prefix transfer; facade extraction with strict behavior parity.
Unexplored: distributed ownership/union visibility (outside selected scope), real
two-account transport and visibility (qualification resource, not synthetic proof).

## Phases 2–3 — candidate adversarial log

| Candidate | Prosecution | Defense | Collision / verdict / constructive output |
|---|---|---|---|
| P1G | Real cache mismatch labels the wrong account. | Reuses public API cheaply. | KILL D1; seed: own identity at the attempted client. |
| P1F | Timeout cancellation currently drops BatchEngine's completed records; duplicate config/credential aliases may bypass slot assumptions. | Private policy and fresh admission checks contain source ownership. | REFINE D1/D3: prove cancellation-prefix transfer; reject duplicate expected IDs and known duplicate credentials before reads; pre-verification failures must say identity unknown. |
| P1C | Reopens broad #7 ownership work and still leaves waits unbounded. | Could improve all existing callers. | KILL D4/D7 for this delivery; seed: isolate the account owner now, retain a separate global repair task. |
| P2G | Restart forgets a recorded wait. | Small and fast. | KILL D2; seed: preserve prohibitions, not merely ranking. |
| P2F | Process dies after receiving FloodWait but before its fact commits; old clear state is reloaded. | CAS facts prevent ordinary forgotten waits without another scheduler. | REFINE D2: persist account-attempt admission before source and refuse unresolved attempts after restart; define recovery/failed-settlement behavior. Facts alone are insufficient. |
| P2C | Repeatedly asking Telegram bypasses known prohibitions. | Fresh evidence avoids stale caches. | KILL D2/D4; seed: expiry grants a probe, never deletes evidence retroactively. |
| P3G | Hedges produce two paid observations and uncertain loser cleanup. | Low latency under slow sources. | KILL D3/D4; seed: single quiescent attempt at a time. |
| P3F | Serial pool can reject useful concurrent work. | Clear ownership, finite inventory, no prefix arbitration. | SURVIVE D1–D7; throughput is an explicit noncritical tradeoff, not a missing correctness guarantee. |
| P3C | Caller still implements failover. | Strong library boundary. | KILL D4 outcome; seed: keep scheduling external while selecting internally. |
| P4G | A second cursor can diverge after an uncertain acknowledgment. | Unified API. | KILL D3/D7; seed: unify facade, not state authority. |
| P4F | Extraction could decorate local storage errors as health or call pool selection during replay. | Existing reader injection and replay probes show a narrow reusable seam. | SURVIVE as behavior-preserving composition, D1–D7; implementation tests must exercise actual facade methods with unavailable inventory. |
| P4C | Raw-only requires callers to access private progress engines. | Smaller independently useful unit. | REFINE D6: retain as fallback only if user deliberately narrows delivery; do not silently substitute it. |
| P5G | Stand-ins supply the very identity/error behavior under dispute. | Cheap broad scenario testing. | KILL D5; seed: synthetic wire, actual SDK/client/SQLite. |
| P5F | Two live accounts do not safely reproduce bans. | Deterministic offline faults plus bounded live composition establish complementary claims. | SURVIVE D1–D7; evidence must explicitly separate those claims. |
| P5C | Happy live replies cannot establish failure histories. | Captures real Telegram behavior. | KILL D2/D3 qualification; seed: combine actual wire success with controlled offline failures. |
| X1 | Changing batch hashes breaks unchanged receipt users. | Intrinsic source provenance. | KILL D5/D7; seed: provenance outside canonical observation. |
| X2 | Distributed leases exceed the selected single-owner problem. | Future scalability. | KILL as current delivery; retain future seed when competing readers are requested. |

## Phase 3.5 — assembly A

Prosecution: a “minimal persistent health cache” cannot safely restart after a
source reply whose restriction never reached disk. Timeout is also not a plain
transport failure: asyncio.wait_for raises TimeoutError after cancelling the
inner coroutine, and BatchEngine currently catches Exception, excluding that
cancellation. Its previously completed records become unavailable to the router.
Both fail the user's daily-continuation concern, not just implementation neatness.

Defense: identity/ledger/delivery ownership is sound, and existing CAS plus
exception-prefix contracts are suitable primitives. The defects lie at source
admission/settlement and cancellation boundaries, not the whole library layer.

**Assembly verdict: REFINE.** Two required targets:
1. Treat an admitted account attempt as durable permission with a unique identity.
   Settlement clears it only together with the outcome/restriction. Unknown state
   remains ineligible; recovery requires quiescence and an explicit restriction
   decision. This is account source ownership, distinct from a group's owed batch.
2. Establish a real-component timeout-prefix path before planning source failover.
   Preserve external cancellation semantics and do not retry when a prefix exists.

The critique specifies the necessary semantics, not a chosen new storage API.
Return these targets to the next iteration's Innovation through the pipeline.

## Phase 4 — accumulator / coverage / signal

Evaluation log and kill seeds: table above. Refinement record: P1F (timeout/alias),
P2F (admission uncertainty), P4C (scope fallback). Mechanism-independence status:
validated for P3F/P4F/P5F by actual SDK/SQLite observations and current source;
P2's proposed restart safety has no empirical proof and is not a survivor.
All17 candidates screened across critical axes; survivors considered on all7.
Landscape: boundary risks sharpened, viable source/delivery region unchanged.
No clean whole-assembly survivor yet. **Signal: ITERATE** with a narrow focus on
account admission/settlement and cancellation-prefix ownership; keep resolved
identity, budget, scope and delivery constraints.

Convergence telemetry: dimension coverage7/7; adversarial strength STRONG;
landscape CHANGED within boundary region; clean component survivors yes, complete
assembly no. No rubber stamp, nitpicking, drift or external-grounding absence.
No two-iteration convergence claim. **Overall: FLAG** — refinement required before
description; no product code has been changed.
