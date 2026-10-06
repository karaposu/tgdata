---
model: gpt-6-astra
effort: max
revision: 1
---
# Stage 1 contract delivery — implementation plan

Input: [desc.md](desc.md), [source record](source-input.md),
[overall staged plan](../staged-plan.md), published issue #19 and prior lifecycle inquiry.
This plan implements only Stage 1. Its steps are document-delivery steps, not the
subsequent runtime stages. Explicit folder: `devdocs/work/19-backfill-run-lifecycle/stage-1-contract/`.

### What is the task

Produce an operationally precise lifecycle contract and a connected assumption,
acceptance and live-validation specification. Give the next implementer one meaning
for every operation, with checks that can invalidate its premises before dependent
work is built. Preserve the whole eight-stage plan and its four mandatory gates.

### Huge Hard Blockers

#### Planning Blockers

None identified for this document delivery. The user selected the finding as its
basis, then explicitly requested Stage 1 via task-impl. Current interfaces and prior
observations are available; normative choices can be made within that scope. No
runtime/vendor success is presumed by writing a proposed behavioral contract.

#### Execution Blockers

None gates Steps 1–5 below. Carry these later conditions into the deliverables:
- #18 daily/window code must be present on an integrated/authorized runtime base
  before Stage 2 code work. Current #19 branch is from dev `45bab71`; sources at
  #18 `e9b5154` are inspected separately. Do not merge or copy product code here.
- Live resources/fixture and independent expected results gate Gate A and Stage 3;
  receipt semantics for the chosen receiver and actual gate results gate later work.
  No live resources are selected or validated by this plan.
- PR/merge remain outside this request. Implementation of Stages 2–8 is not selected.

### How this implementation moves toward desired state

Write the public behavioral contract first, using stable requirement identifiers.
Record which premises are policy, source-supported or still untested. Map each
operation and failure history to observable outcomes and evidence requirements.
Specify the first executable live experiment without implementing its harness.
Then verify the documents against the source/finding and run the supported offline
baseline suite, with a scoped issue update and committed artifacts.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Define identities, operations and transitions | `../contract.md` |
| 2 | Record assumptions and dependencies | `../assumptions.md` |
| 3 | Specify adverse histories and coverage | `../acceptance-matrix.md` |
| 4 | Specify live fixtures, harness and gate protocol | `../live-validation.md`; reconciled `../staged-plan.md` |
| 5 | Verify and checkpoint Stage 1 only | `verification.md`, `implementation.md`, scoped #19 status |

## Step 1 — Write the operation and state contract

### Proposed changes

Create `contract.md` in the #19 task root. Mark it as a normative Stage 1 specification,
not an implemented API. Name the source baseline and reference the existing finding
through the preserved source record. Keep the text usable without the prior discussion.

Define collection/destination identity, canonical chat ID, immutable run intent,
command identity/accepted ordering, one source attempt and one pending delivery.
Give JSON-friendly data sketches for run reference, start/control request, delivery
reference and status. Retain exact IDs and stable batch v1 payloads; no credentials
or message content in status. Distinguish state, progress and control revisions if
needed so unrelated acknowledgment does not accidentally supersede operator intent.

Specify create/new versus repeated start, prepare/replay, acknowledge, status,
pause/resume/cancel/abandon through a control operation, and explicit recovery.
For each: inputs and validation, preconditions, local versus source effects, durable
commit point, returned status/data, unchanged facts on refusal, retry handling and
conflicts/unknown outcomes. Equal payloads or equal parameters are not intent identity.
Known missing state cannot silently initialize. Caller-owned request identities and
receiver acceptance must be explicit; do not imply a distributed source/store/destination
transaction or indefinite command recognition.

Define independent state facts, accepted-position advancement, empty/final exhaustion,
imported-origin coverage, attempt admission, durable timing, unknown-attempt recovery,
terminal race precedence and merging late results with newer controls. Validate source
results against their exact attempt/run; source failures remain failures with useful
prefixes where persisted. Pause stops new reads, cancel stays terminal, abandon withdraws
delivery with an honest incomplete outcome. Store failure is not source exhaustion.

Give allowed/forbidden transition examples, invariant identifiers and observable
error categories. Preserve local error/health isolation, one active source reader,
caller scheduling and budget admission by fresh authenticated identity. Specify
clock/visibility/receiver limits without inventing numeric operational guarantees.
No wire codec, runtime dataclass, migration, scheduler or test-only lifecycle engine.

### Output

Self-contained contract with public operation sketches, consistent state/transition
rules, durable success and refusal meanings, and cross-referenceable invariants.

### Safe in nature

False — runtime is untouched, but this document governs later records and external
source activity. An incorrect contract is not harmless merely because it is prose.

### Peripheral concepts

Batch v1, #18 sync/window state, caller receiver, source ownership, budgets, health.

### Hardness Lvl

5/5 — resolve temporal identity and settlement precisely.

## Step 2 — Make assumptions falsifiable and dependencies visible

### Proposed changes

Create `assumptions.md`. For each critical premise record its kind (chosen policy,
documentary/component fact or behavioral premise), actual evidence, falsifying
observation, cheapest earlier check, first dependent stage, earliest gate, owner,
status and scope of confirmation. Distinguish existing source behavior from the
new lifecycle implementation that remains unbuilt.

Include source identity/bounds/ID pagination/exhaustion, real SDK attempt boundaries,
one-record CAS, persisted observation/media availability, receiver acceptance,
clock trust, single-reader recovery, command/receipt context, imported progress and
independent daily/backfill state. Link each to contract requirements and matrix cases.
Current component receipts can be inherited with named revision; none prove a live
account/group or a new lifecycle state machine. Conditional mechanisms remain conditional.

Carry explicit `UNSET` inputs for live test account/group/fixture and chosen destination.
The user selected an existing group with read-only tests: no source writes, fixture
creation or membership changes. That choice does not supply an actual fixture or
independent oracle. An unavailable future gate is recorded
as a future execution condition and does not prevent this Stage 1 document delivery.

### Output

An auditable register showing what is decided, what has evidence, and what can invalidate
later work. No critical untested premise silently receives a confirmed status.

### Safe in nature

False — false confirmation could allow subsequent implementation past its gate.

### Peripheral concepts

Evidence provenance, source visibility, account configuration, receiver guarantees.

### Hardness Lvl

4/5 — make the dependence and evidence level match.

## Step 3 — Specify failure cases and coverage

### Proposed changes

Create `acceptance-matrix.md`. Carry all 22 final inquiry histories individually,
then add the explicit implementation boundaries in the staged plan. Assign case IDs.
Each case contains setup/initial state, ordered stimulus, required and forbidden
observable effects, evidence class (LIVE/INJECTED/LOCAL), earliest stage/gate and
initial `UNRUN` status. A scenario written in Markdown is not a runtime pass.

Cover lost creation/control/ack/recovery replies, changed start parameters, new identical
intent, retired/unknown requests, known missing state, reordered controls, final ack
versus cancel in both orders, pause/final settlement, imported origin, full/empty/end,
missing artifacts, pending identity beyond historical retention, budget prefixes,
possible-send crashes, known waits, untrusted clocks and commit-then-error.

Add refusal before source send on uncertain admission, local persistence failure after
a read failure, mid-read control CAS changes, active earlier reader, public-operation
health isolation and unchanged daily behavior. Include coverage tables from every
public operation and invariant to one or more named cases; inspect success, retry,
conflict and failure coverage rather than counting cases alone.

### Output

A traceable specification of how to tell correct from incorrect behavior at each
boundary, ready to drive real runtime tests in the appropriate future stage.

### Safe in nature

False — a matrix that omits or weakens a required outcome can certify the wrong behavior.

### Peripheral concepts

Fault boundaries, actual persistence, receiver deduplication, invariant traceability.

### Hardness Lvl

4/5 — check composition, not just isolated happy paths.

## Step 4 — Specify the early live experiment and later gates

### Proposed changes

Create `live-validation.md` with an input template and a procedure executable once
Stage 2 and its live resources exist. Define independent fixture establishment,
canonical IDs/dates and selected media hashes, expected included/excluded message sets,
actual SDK page crossing and caller-batch crossing, empty and exact-full cases.
The procedure must record its oracle before fetching; a second call to the same
implementation is not independent evidence. Use existing visible history, with a
separate client/export/manual enumeration for a complete bounded interval. A sample
of a few messages cannot prove whole-interval completeness. Missing critical cases
remain unverified; do not seed messages to obtain them. Declare account-dependent
visibility and mark source drift inconclusive rather than changing expectations.

Gate A uses the existing real batch reader and dates loaded from the Stage 2 saved
record; it does not depend on new Stage 3 preparation or Stage 7 public facade.
Specify allowed probe actions, request/time accounting and a bounded test allowance;
no unrelated account discovery, writes, group joining or induced Telegram bans/floods.
Stage 1 writes the specification, not an executable live_probe.py or test messages.

For Gates B/C/D, specify the real source/store/receiver composition and exact locally
injected failure boundaries. Separate live observation, injected interruption and
synthetic clock/state checks. Require reports naming code revision, premise, expected
and actual outcome, limits and next-stage decision. No skipped critical case passes;
contradicted premises stop dependent work, re-plan and re-open affected earlier gates.

Reconcile `staged-plan.md` with the produced contract only where a concrete clarification
requires it. Add a Stage 1 handoff rather than pretending all future stages are approved
or implemented. Keep detailed draft history/source references and four gate order intact.

### Output

A concrete opt-in validation specification, independent fixture requirements, gate
report templates and a consistent overall plan ready for later authorized execution.

### Safe in nature

False — it defines which external tests may be treated as sufficient evidence.

### Peripheral concepts

Live access, bounded source traffic, oracle independence, fault injection, gate authority.

### Hardness Lvl

4/5 — real evidence must arrive before dependent work and be distinguished from simulation.

## Step 5 — Verify, commit and report Stage 1

### Proposed changes

Perform a literal cross-document audit: operations and invariants are defined exactly
once, identifiers/links resolve, every required history is covered, repeated/unknown
commands and terminal orders agree, and stage/gate dependencies do not require future
code to pass an earlier gate. Inspect each declaration of evidence and readiness.
Temporary check scripts may check structure/coverage; do not ship a toy lifecycle model
or call a heading/count check a behavioral proof.

Run the full supported offline baseline suite on this #19 branch with Telethon 1.45.0:
tests 19, 18, 17, 16, 15, 14, 13 and 12, plus explicitly awaited offline test11 helpers.
Use absent config arguments to skip test12/13 live sections; proxy testing uses only
local sockets. Do not run other legacy live entry points. The #18 test22/23 receipts
are source evidence, not suites present on dev; any targeted #18 mechanism probes must
name their separate baseline. Count actual passes/skips and record test limitations.

Confirm the diff contains only this issue's devdocs and no staged unrelated work.
Write implementation/verification records, commit the completed contract documents,
push the issue branch and publish the scoped Stage 1 completion/evidence on #19.
Keep Stage 2 onward and all live gate boxes unchecked. No PR or merge; no push to
#18, dev or main. Stage 1 completion means the specification is produced/reviewed,
not that any future lifecycle guarantee has passed runtime/live validation.

### Output

Verified and committed Stage 1 deliverables, a reproducible offline test receipt,
accurate issue progress, and a clear next-stage handoff.

### Safe in nature

True for document verification and scoped branch/issue updates. Existing runtime is
not edited. Tests use temporary data and controlled/local transport only.

### Peripheral concepts

Smoke-test entry points, baseline separation, GitHub status, scoped commits/publication.

### Hardness Lvl

3/5 — distinguish document completeness from implementation correctness.
