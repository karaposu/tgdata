---
model: gpt-6-astra
effort: max
---
**Verdict: REORDER — TEST BEFORE BUILD**

Falsifier: caller cancellation while fresh proof is pending still spends/sends a
join, or cancellation after committed enqueue refunds the claim or loses owned cleanup.
Affordable now: yes — two real-SDK/SQLite/owned-context cases with synthetic wire
and blocked sockets, seconds locally, no account or money.

Experiment: exercise the existing candidate sender adapter with caller cancellation
at (a) pending fresh GetUsers proof and (b) pending join reply after actual sender
enqueue. Use real SDK RequestState futures, the actual JoinBudget and actual
_account_health_operation/disconnect. Verify stored usage and original cancellation.
Cost: seconds offline; no credentials/network.
Must precede: step2's admission adapter; task-impl runs it before any step1 code.
Disqualifying result: before-proof cancellation sends/spends a join, after-enqueue
cancellation loses its committed claim, or the composition cannot settle owned
cleanup and propagate caller cancellation.
Passing result: before proof:0 join sends/0 charge; after enqueue:1 send/1 retained
charge; in both cases caller receives CancelledError and actual owned disconnect settles.

## High-level summary

Revision1's bounded consumer fits the staged #7 scope. The plan explicitly addresses
the observed wrong-origin and malformed-payload cases, keeps existing ownership/
health/ledger behavior, and avoids mandatory post-ack enrichment. It is detailed
enough to implement without inventing a new workflow or backend contract.

No High, Medium or Low plan defect was established. One affordable behavioral
premise is tested too late: the new asynchronous sender adapter's cancellation
composition. Identity mismatch and ordinary RPC failure probes do not exercise
both cancellation suspension points. Move that experiment before building. This
is a plan-order verdict, not a product rejection or request for a broader design.

## Premise Inventory

### P1 — Cancellation across proof/admission/source await

**First dependent step:**2. **Waste if false:** adapter, facade and public tests2–5.
**Scheduled test:**4. **Cheapest earlier test:** the experiment above, seconds.
**Coverage:** Stage1 separately verifies owned cleanup; inquiry exercises the new
candidate on identity errors and RPC errors. Neither establishes cancellation on
the candidate's new await-before-claim and await-after-enqueue paths. A mock that
returns a prewritten cancellation result would be non-covering. This sets REORDER.

### P2 — SDK enqueue and original request correlation

**First dependent steps:**1/2. **Waste if false:** source interpretation and guard1–4.
**Scheduled test:** inquiry/planning before this plan, repeated through product4.
**Cheapest earlier test:** already performed actual SDK dispatch, TL decoding and
SDK-built RPC errors. **Coverage:** source order verified222→claim222→enqueue;
cached wait0, two retry sends/two charges, final error object preserved. Extra
planning probe shows the exact mutation request survives InvokeWithoutUpdates in
error.request. The local helper still needs implementation tests, but no untested
vendor object-identity convention is being assumed.

### P3 — Existing reference/ledger/health composition

**First dependent steps:**1–3. **Waste if false:** public outcome/integration design.
**Scheduled test:** existing staged tests, current real component probes, final4/6.
**Cheapest earlier test:** already performed real numeric peer/hash0 join and
read/join budget coexistence with the current owned context. **Coverage:** source
code plus ten probe groups and merged529-test baseline. No raw-client expected-owner
contract is assumed; the marker is confined to the public owned operation.

### P4 — Live Telegram semantics and operating conditions

**First dependent step:** public contract. **Waste if false:** any overstated live
acceptance/rate guarantee. **Scheduled test:** no live joining in this authorized
delivery. **Cheapest earlier test:** needs explicit account/group mutation permission,
not supplied by prior read-only authorization. **Coverage:** installed1.45 schema,
documented RPC meanings and offline mapping; synthetic replies are non-covering for
live acceptance. The description/public-doc plan explicitly limit that claim.
Accurate forward clock/cooperative file custody remain the merged ledger's stated
assumptions, not newly claimed protections.

## Restart Check

| Prior observation | Established mechanism | Plan response |
|---|---|---|
| Temporary source error relabeled as bad reference | Generic SDK retry ValueError caught by old resolver | Existing Stage1 policy retains last error; steps1/3 preserve current resolver/errors; test4 exhaustion checks |
| Fresh event owner differed from stored health summary | New event identity fed legacy cache-owned state | Existing fixed-owner context consumed in3; no legacy note_account fallback or health store change |
| Missing/invalid ledger state restored capacity | Old auto-repair and prune-before-validation | Stage4 ledger already fixes it; step2 calls it directly and step4 verifies failure before send |
| Success-like RPC name came from GetUsers, with0 join sends | SDK error class is independent of operation origin | Step1 requires exact mutation request identity, not names alone |
| Ok wrapper contained a User payload | TL decoder does not enforce field annotation | Step1 lists allowed Updates roots and validates used WebView fields |
| Weak original overlap fixture | Completed futures did not force interleaving | Step4 requires held pending replies/forced overlap, not gather alone |

## Inherited Lessons

- Owner proof is structural: step2 uses the same verified handle at the actual
  enqueue boundary; step3 activates it only on that temporary operation.
- Helper calls are not request admissions: sender wrapping lies inside SDK retry
  dispatch and after cached-wait handling, proven before build.
- Source acknowledgment is not fresh metadata/read proof: step1 returns preflight
  metadata without post-ack enrichment; step3 never confirms group read recovery.
- Local failures stay local: guard errors inherit JoinBudgetError; exact RPC origin
  prevents proof errors being interpreted as membership outcomes.
- Existing tests are not new qualification: candidate probes establish components;
  step4 tests the delivered facade and step6 the full current offline suite.
- Cancellation cannot be inferred from ordinary-error coverage: the required
  prebuild experiment closes that gap before adapter/facade work.

## Findings and scope assessment

No mitigation finding. Request classifiers, envelope/batch/depth bounds, accepted
ledger/status/claim returns, result fields, ownership, error correlation, teardown
and documentation are concrete enough. The source module/helper dependency in
step1 is introduced before step2's file exists, but no intermediate import/run is
required; final integration/tests occur after both, so it is not a pipeline blocker.

Compatibility risk is concentrated in the shared client MRO, explicitly marked
not safe-in-nature in step3 and covered by the full existing suite. The new mixin
is inactive when the operation marker is None. No changed constructor positional
slot, ledger schema, source wait/retry policy, global registry or read settlement.

Overengineering check: one result/helper, one bounded send adapter and a facade
method are sufficient. General raw-client guarding would require another authority
policy; quota unification would alter accepted read behavior. Neither is needed to
deliver this scope. The schema/rate limits and two known prior-stage Lows are not
silently “fixed” as part of this feature.

## Selection pass

No High/Medium proposals exist to select; no fabricated risk or mitigation tiers.
Run the experiment first. PASS proceeds with this plan's behavior unchanged and a
zero-mitigation fold record; FAIL follows task-impl's experiment/deprecation gate.
