---
model: gpt-6-astra
effort: max
---
**Verdict: IMPLEMENT AFTER FOLDING THESE IN**

**Falsifier:** an independently enumerated real-group interval contradicts the
source reader's ID/date/end interpretation so the declared scan cannot be supplied
without changing the proposed contract.
**Affordable now:** no — the user selected an existing read-only group as the
approach, but no actual account/group/independent oracle is configured for this run.
Gate A is before new source/delivery implementation. Stage 1 defines the conditional
contract and the test, not a verified live behavior. Affordable existing-component
checks below were run during this critique, before document implementation.

## High-level summary

The five-step document delivery is the correct layer and preserves the user's
mandatory gates. Two Medium omissions need explicit decisions before the contract
is written: first-use versus unknown creation retry, and a stale prepare call after
accepted progress/control changes. Both are refinements inside Step 1 and its cases,
not reasons to build another subsystem. No High/Low findings; no deprecation/reorder.

This is the in-session three-phase critic-d pass against plan revision 1 at e39f8a5,
including the full staged plan as dependency context. It is not a PR critique or
proof of the unbuilt lifecycle.

## Premise Inventory

### P1 — Live selection and source-attempt behavior

**Premise:** the selected real source can supply the declared fixed-window/ID scan,
and its actual request/retry/cancellation boundaries fit the proposed attempt.
**First dependent step:** document Step 1 records a conditional contract; runtime
Stage 3 is the first new source/delivery implementation relying on it. Stage 2 can
supply the saved query and reuse the current raw reader for Gate A.
**Waste if false:** document revision and the source-facing design, then runtime
Stages 3–8 if the mandatory gate were bypassed.
**Test scheduled at:** Gate A; subsequent composition at Gates B/C/D.
**Cheapest earlier test:** same existing read-only fixture probe as soon as access,
identity and independently recorded expected results exist. None can be substituted
from local fixtures to establish server behavior.
**Coverage:** current batch/window source and offline SDK tests; explicitly
non-covering for the real account/group. No live claim is inherited as confirmed.

### P2 — Durable state and exact pending observations are usable foundations

**Premise:** current #18 store/continuation mechanisms expose actual conditional
storage, uncertainty and frozen query behavior that the documents can reference.
**First dependent step:** document Step 1's compatibility/current-state descriptions;
future Stage 2's reuse of the backend.
**Waste if false:** change the proposed storage boundary before runtime reuse.
**Test scheduled at:** existing receipts and four focused existing-component checks
run now; further new-state durability at Stage 2/Gate A.
**Cheapest earlier test:** real current SQLite/SDK composition; performed below.
**Coverage:** source + actual SQLite + synthetic transport. Covers the named current
mechanisms only, not a new state codec or a deployed remote backend.

### P3 — Receiver, clock and ownership preconditions

**Premise:** a caller can attest its chosen receiver's durable acceptance, preserve
request context, provide one source reader and use sufficiently trustworthy time.
**First dependent step:** contract Step 1 defines these obligations rather than
asserting a deployed instance satisfies them; runtime delivery/recovery depend on them.
**Waste if false:** revise that integration or weaken an advertised guarantee explicitly;
never claim exactly-once effects or safe elapsed time without their prerequisites.
**Test scheduled at:** receiver Gate B/D; request/order/clock/recovery Gate C with
cheap local cases specified before implementation.
**Cheapest earlier test:** an identified receiver/worker/time environment. None is
selected now; logical adverse histories are required here but do not certify one.
**Coverage:** existing local receiver examples and budget code; non-covering for an
unselected deployment. The single-reader boundary is chosen scope, not a proven lease.

### P4 — The selected task is Stage 1 only

**Premise:** the user requested contract definition rather than the whole lifecycle.
**First dependent step:** all five document-delivery steps.
**Waste if false:** work would target the wrong output layer.
**Test scheduled at:** raw request, published Stage 1 and supplied task-impl skill
read at intake. **Cheapest earlier test:** direct request comparison, completed.
**Coverage:** explicit user selection and asynchronous existing-group/read-only answer.
No runtime or live execution is necessary to satisfy the selected deliverable.

## Existing-component observations

Telethon 1.45.0; #18 product baseline e9b5154; actual SQLite and real library/SDK paths
with synthetic replies and both socket connect functions forbidden. Four tests passed:
- `test_store_protocol_and_no_store`;
- `test_backend_failures_conflicts_and_uncertain_ack`;
- `test_relative_enrollment_freezes_once`;
- `test_initialization_conflicts_and_bad_durations`.

The first temporary driver omitted the tests' shared temporary-directory setup and
failed before the first store could be created (`f.TMP` was None). It is not a product
failure or passing evidence. The corrected driver followed the suites' fixture setup
and client cleanup, then passed all four without source/test changes. No live gate passed.

## Restart Check

- **Observed:** current empty/end sync does not retain a durable completed-run fact.
  **Established mechanism:** `SyncEngine._publish` returns None for empty data; ack
  records a cursor, not lifecycle exhaustion. **Planned remedy:** Step 1 separates
  exhaustion/delivery; Step 3 supplies empty/final/limit cases; Gate B tests them.
- **Observed:** equal observed batches can belong to different windows.
  **Established mechanism:** MessageBatch v1 hashes payload, not a run/query.
  **Planned remedy:** Step 1 scoped run/delivery references and Step 3 wrong-run cases.
- **Observed:** nonzero initialization can store caller progress with no receiver
  proof. **Established mechanism:** `SyncEngine.initialize(after_id=...)` is local
  enrollment. **Planned remedy:** Step 1 explicit imported origin; Step 3 coverage claims.
- **Observed:** an acknowledgment can commit before its response fails.
  **Established mechanism:** real durable backend write followed by injected lost
  response in the existing test. **Planned remedy:** Step 1 reload/unknown semantics;
  Steps 3/4 define actual before/after-commit interruptions for future gates.

## Inherited Lessons check

- More implementation does not prove Telegram behavior: Step 2 names the unverified
  source premise; Step 4 specifies Gate A before runtime Stage 3. No late-only test.
- Function return is not completion: Step 1's invariants and Step 3's explicit cases.
- Payload equality is not ownership: Step 1 contexts and Step 3 cross-run refusal.
- Supplied cursor is not archive proof: Step 1 origin and Step 3 imported-tail case.
- Local error is not Telegram health: Step 1 boundary; Steps 3/5 existing regressions.
- Snapshot is not capacity; timer is not scheduler; error is not rollback: Step 1
  authority/time/uncertainty rules and Steps 2–4 evidence requirements.
The two risks below make retry behavior more specific without relaxing these lessons.

## Risk 1 — An unknown creation retry can look like first use

**Risk**

A caller can lose the answer to “start this job” and try again after the library
can no longer recognize that request. If the contract treats every missing job as
first use, retrying can create a fresh job with new dates. A request label alone
does not tell the library whether the caller intended new work or is recovering
an uncertain earlier result.

Step 1 of `step_by_step_impl_plan.md` requires retry/new distinctions and refusal of
known missing state, but does not require a creation-submission rule for an absent
slot versus an unknown/pruned request. Existing `SyncEngine.initialize` treats a
missing row as enrollment; reusing that convention at `start_backfill` would violate
#19's unknown-retry rule. Step 3 lists retired requests without pinning this first-use
counterexample. This is a specification omission, not a demonstrated new runtime bug.

**Severity:** Medium.
**Category:** API contract / identity / recovery.
**Impact:** a lost or forgotten request can be reinterpreted as new source work.
**NoobEng:** remembering a token helps only while it is recognized. Starting a new
job and asking whether an old start succeeded need distinct permission when it isn't.
**Affected areas:** future start API, new/known-run recovery, command retention;
contract, assumptions and acceptance-matrix documents in the #19 task folder.

### Mitigation — Quick

Warn callers not to retry start after uncertainty and require manual inspection.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Require an explicit new-submission versus recovery/retry mode, caller-retained intent
identity and expected predecessor context. Recognized same requests return recorded
effect/current state; unknown retry refuses without creation. Unknown fresh creation
requires affirmative first-use/successor preconditions, never automatic promotion
from a failed resume. Record the limit after catastrophic loss of authoritative
history; known-run recovery stays a failure. Add the absent/retired counterexamples.
**Why this is robust:** defines the missing permission locally, without indefinite
history or pretending total storage loss can be inferred from equal parameters.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The only current analogous entry point is SyncEngine.initialize, whose daily enrollment contract intentionally differs. No single existing command-service mechanism closes a demonstrated cross-module class. Explicit submission authority closes this lifecycle instance with contract/case changes only; robust has the best reach per extent.
*For future:* —

### Mitigation — Long-term

Specify an indefinitely retained command journal and a generalized submission service.
**Why this is long term effective:** if all commands were routed through it with
retained history, recognition could span many operations and arbitrarily old requests.
This still cannot repair catastrophic loss of that authority.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit a general command journal only if a separately selected service needs longer historical recognition. It must retain these explicit authority rules; it is future work, not a prerequisite.

## Risk 2 — Retrying a stale prepare can request another source turn

**Risk**

An earlier request to fetch data can arrive again after that data has already been
accepted, or after the operator paused and resumed the job. Returning the currently
pending batch is safe while it exists. Once it is gone, the same old call can instead
start a different read unless the contract ties it to the progress and permission
that the caller actually observed.

Step 1 promises retry/conflict semantics for prepare/replay but the overall plan
only scopes preparation to a run and current eligibility. Current `SyncEngine.prepare`
intentionally reads after the latest cursor once pending is cleared; that existing
behavior is not proof of retry identity for the proposed `prepare_backfill` API.
Steps 1/3 need an explicit stale-progress/control case. Future runtime admission must
check that context atomically, rather than silently rebasing the old call to new state.

**Severity:** Medium.
**Category:** API contract / stale operation / source admission.
**Impact:** unnecessary source reads/quota use or work authorized by an older view,
without a wrong batch acknowledgment being necessary to trigger it.
**NoobEng:** “fetch next” is a new instruction after progress advances. An old request
should not quietly acquire that new meaning because the receiver finished first.
**Affected areas:** future prepare API, admission guard and status tokens; contract
and acceptance cases. Existing daily sync semantics must remain unchanged.

### Mitigation — Quick

Document prepare as always a new attempt and advise callers never to retry it.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Require the expected accepted position and control revision with the run reference
on preparation. Replayed pending output must match that context; a stale position
or control revision refuses before a new source request. A new intentional turn
uses fresh status. Explicitly state that a retry at unchanged progress after a known
failed attempt may be a new attempt once eligible; an unresolved attempt still
requires recovery. Add after-ack and pause/resume delayed-call cases.
**Why this is robust:** uses the already-required status/control facts to prevent
silent rebasing; it does not promise to remember every source call forever.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The issue is the new prepare operation under changed progress/control context; existing daily sync is not contracted as the same operation. Reusing its required status facts closes both delayed-call histories without new storage history. Robust wins on reach per extent; the broader journal adds an unrequested service.
*For future:* —

### Mitigation — Long-term

Add an indefinitely retained preparation-command journal and replayable turn receipts.
**Why this is long term effective:** it could identify old preparation invocations
regardless of current cursor/control state and generalize to a future worker queue.
It adds storage/retention and command-service semantics outside the selected library scope.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit turn journaling only if a selected worker contract needs replay of arbitrarily old prepare invocations. Expected progress/control preconditions still survive that extension; it is not prerequisite work.

## Carried execution conditions

Unchanged: #18 integration/authorized runtime base before Stage 2; selected existing
read-only account/group and independent fixture before Gate A; actual receiver/time/
ownership evidence at later gates; no Stage 2, live test, PR or merge in this run.
These are not newly scored findings and do not block Stage 1 document implementation.

## Selection pass

Phase 2 produced the above three proposals per Medium risk with empty boxes/notes.
Phase 3 will compare reach/extent without editing their wording or severity.
