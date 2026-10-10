# Dynamic plan critic — #7 Stage5 joining

Subject: committed revision1 plan.md with desc.md, inquiry finding/probes, current
group domain, factory/MRO, account operation, owned health, read/join budgets and
SDK1.45 sources. Run in this warmed session. The old broad PR16 is historical;
merged prerequisites are current code, not a reason to trust new composition blindly.

First read declared blockers. Compute Premise Inventory before risks: each premise,
first dependent step, waste if false, scheduled test, cheapest earlier actual-component
test/cost and current coverage. Rank by waste. Synthetic replies may select source
inputs but cannot stand in for the SDK/ledger/lifecycle behavior being qualified.
Test any affordable unsettled behavior before building on it. In particular trace
caller cancellation while fresh identity is pending and after a claim/actual enqueue,
through real SDK futures and owned cleanup; prior identity-error tests are not the
same observation as cancellation at these suspension points.

Question architecture and detail. Does the facade-configured, operation-local guard
solve the requested ownership/admission problem without a new raw-client policy or
quota framework? Is every mutation attempt preceded by fresh same-owner proof and
a completed synchronous claim, with no intervening await? Are packet retransmission
and application attempts clearly distinguished? Do no-op membership/payment paths
still require explicit policy, without charging metadata or the read allowance?

Check request classifiers, supported auto wrappers, batches, depth/cycles, MRO
cooperation, inactive ordinary clients and marker teardown. Check exact RPC request
identity, not names alone, and typed nested Ok/WebView payloads. Verify metadata is
preflight data and no optional enrichment can erase acknowledgment. Check source
errors, cancellation/cleanup, health recovery and all public import/doc contracts.
Identify concrete missing predicates as Medium if complexity requires inventing
semantics during implementation. Avoid speculative extra backends or packet guards.

Create critic.md with actual model/effort frontmatter (unknown if unavailable), then
one critic-d verdict: IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN;
REORDER — TEST BEFORE BUILD; or DO NOT IMPLEMENT — MEANING GAP/WRONG LAYER.
Include falsifier/affordability directly below, then high-level summary, Premise
Inventory, Restart Check and Inherited Lessons. An affordable untested premise
requires REORDER with experiment/cost/first dependent step/disqualifying and passing
results. A wrong premise invokes deprecation/blocker handling, not mitigation patches.

Restart Check covers the original source-error/owner failures, table/timestamp reset
pitfalls already addressed by Stage4, and the newly observed wrong-origin/malformed
reply cases. Lessons must point to actual ordering or structural enforcement.

For each real risk use two paragraphs: plain user consequence without code names,
then precise file/symbol/trigger/flow. Include Severity, Category, Impact, NoobEng
and Affected areas. Medium/High needs Quick, Robust and Long-term proposals with
why robust/long-term is effective. Every proposal initially has:

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

Run selection separately: only tick boxes/notes, name real other instances before
generalizing, compare reach/extent and apply the size gate. No actual finding means
no fabricated mitigation. Preserve plan/inquiry history; the orchestrator folds
selected changes after any required experiment passes. No re-critique after fold.
