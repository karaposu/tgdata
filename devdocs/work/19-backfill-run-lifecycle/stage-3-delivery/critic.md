---
model: gpt-6-astra
effort: max
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the actual SQLite/strict-codec/artifact composition cannot retain an exact
pending observation through reopen and an uncertain commit, or cannot settle metadata
without requiring an already-accepted local artifact. That would invalidate the chosen
custody boundary before the new delivery transitions are built.
Affordable now: yes — disposable local SQLite/files, existing code, seconds; no account
or network needed. The existing creation-only and separate artifact receipts are useful
but this exact primitive composition can be checked directly before implementation.

Experiment: run `prebuild_probe.py` in this folder. Use actual BackfillEngine.start,
_BackfillState, MessageBatch, download_blob/_verify_existing and SQLiteSyncStore;
publish a deliberately constructed valid pending fixture, reopen it, verify/relocate/
remove its real artifact, and commit accepted metadata with no file dependency. Exercise
an actual SQLite commit followed by close failure and the existing real process-exit
creation checks. Characterize cancellation causality under a real handled RPC exception
to verify the plan's explicit suppression requirement. No synthetic source behavior is
counted as live; fixture construction probes codec/storage capacity, not the unbuilt engine.
Cost: seconds of local CPU/disk, temporary files only.
Must precede: step 1 — new delivery values and transition implementation.
Disqualifying result: exact durable metadata/canonical payload or expected artifact
integrity is lost, failed CAS writes, or the real primitive cannot represent the planned
independent acknowledgment facts. Stop and replace the faulty foundation/premise.
Passing result: all stated primitive assertions hold, actual committed outcomes survive
their lost/error response, and the required error-boundary technique prevents a local
cancellation from acquiring the handled RPC verdict.

Result: PASS — 2026-10-07. All five actual-primitive assertions passed before any
implementation step. Exact pending data survived reopen; corruption refused without
state change; a committed write survived its close error; causal suppression removed
the observed inherited cancellation verdict; actual pre/post-commit process exits
matched expectations. Receipt: [prebuild-results.txt](prebuild-results.txt).

## High-Level Summary

The plan's structure survives review. No additional High/Medium/Low finding is left
unhandled in its content; the affordable primitive falsification must precede building
on that composition. The ordering verdict does not claim that existing tests prove the
new engine. Seven implementation steps remain after the experiment passes.

No open execution blocker is inherited for Stage 3. Gate A is PASS. The operational
receiver and later positive timing/recovery/control semantics remain their explicit
later stages, not prerequisites invented for this scoped internal delivery.

## Premise Inventory — ranked by waste if false

### P1 — Atomic metadata and artifact custody can share the existing boundary

- Premise: one strict opaque aggregate can preserve the prepared observation, while
  required artifacts are verified independently and acceptance is a metadata decision.
- First dependent step: 1; settlement/ack implementation follows in 2–4.
- Waste if false: the whole new delivery protocol and its tests would rest on a wrong
  persistence boundary, rather than needing one local branch fixed.
- Test scheduled at: step 5, beyond existing separate Stage 2/media receipts.
- Cheapest earlier test: the experiment above, using the actual local components and
  real files/commits. Cheap enough to run before step 1.
- Coverage: Gate A and test_24 cover real creation/CAS behavior; existing media and
  daily tests cover related paths. Seeded pending snapshots supply state and do not
  prove new prepare/ack transitions. The earlier primitive composition closes only
  the feasibility premise; step 5 must still run the actual new engine.

### P2 — The raw reader's query/end/prefix behavior is suitable

- Premise: the current callback returns bounded ordered MessageBatch v1 observations
  and real end evidence for saved dates/origin, with complete ordinary-failure prefixes.
- First dependent step: 3.
- Waste if false: publication/end handling would be built around false source semantics.
- Test scheduled at: Gate A before this stage; new composition in step 5; Gate B after 4.
- Cheapest earlier test: already executed Gate A comparisons, actual SDK pages/media
  and controlled raw-read interruption; re-run only if this work changes those paths.
- Coverage: real Telegram at `8023adf` for the reader foundations. Synthetic SDK replies
  in the new offline suite are non-covering for vendor behavior; they test composition.

### P3 — The new transition ordering and scoped receipts enforce the contract

- Premise: planned guards and exact-context comparisons prevent stale/foreign effects.
- First dependent step: 2; this is the implementation to build, not an external fact.
- Waste if false: incorrect implementation must be fixed/replanned before Gate B.
- Test scheduled at: step 5 with actual engine/CAS/receiver, including process exits.
- Cheapest earlier test: none for an implementation that does not yet exist. Source
  inspection confirms the required snapshot fields and examples; a handwritten transition
  fixture would supply the desired behavior and cannot substitute for executing the engine.
- Coverage: Stage 1 invariants and Stage 2 validator. These are constraints, not a claim
  that the future methods already work.

### P4 — Exception provenance survives the new nested failure path

- Premise: explicit cancellation/local-error suppression can prevent an enclosing RPC
  error from being classified as the local operation's verdict, preserving real read errors.
- First dependent step: 2, then partial settlement in 3.
- Waste if false: the required local/source distinction would need another mechanism.
- Test scheduled at: explicit step 2 implementation and step 5 negative classification.
- Cheapest earlier test: actual health.classify and Python cancellation/cause behavior
  in the prebuild experiment; no fabricated verdict or network needed.
- Coverage: source-confirmed cause-chain traversal and prior #6/#18 local-error tests.
  Existing `_backend` bare cancellation alone is not adequate under a handled source
  exception; the plan already explicitly requires suppressed context in this path.

### P5 — Receiver acceptance and later operations are not silently inferred

- Premise: the caller durably accepts before presenting a DeliveryRef; live integration
  and positive timing/recovery/control machinery need later evidence.
- First dependent step: 4 consumes the assertion, without claiming to prove it.
- Waste if false: the caller's integration can lose output despite correct library state.
- Test scheduled at: real local SQLite receiver in step 5; actual integration at Gate B/D.
- Cheapest earlier test: no local stand-in proves an unspecified production receiver's
  durability. Acknowledgment is explicitly an assertion, not an inferred vendor premise.
- Coverage: normative scope and earlier receiver demonstration only. New scoped receipt
  behavior still needs its own implementation tests. Later limitations fail closed.

## Restart Check

This stage is a new capability, not a replacement architecture justified by a failed
implementation. Its inherited failures are mapped without treating them as new incidents.

| Observed prior failure/boundary | Established mechanism | Addressed by |
|---|---|---|
| Local file failures inherited RPC health in #6 review | Exception cause/context traversal | Steps 2–3 suppression, step 5 real classifier checks |
| Cleanup/lost replies can follow a real commit | Existing actual SQLite probes and Gate A receipts | Confirmed admission, retained attempt, exact receipt retry; steps 2–5 |
| Synthetic checks missed SDK startup in Gate A | Real connect tried account-wide difference | Existing corrected instrument retained; step 7 repeats its ten checks |

## Inherited Lessons and ordering

| Lesson | Ordering that satisfies it |
|---|---|
| Read completion is not destination acceptance | Step 3 publishes pending before return; step 4 alone advances accepted position |
| Error is not proof of rollback | Primitive probe precedes step 1; admission/settlement uncertainty remains durable in steps 2–4 |
| Batch hash is not receipt authority | Step 1 defines full context before operations; steps 4–5 check equal-hash isolation |
| Local activity is not Telegram evidence | Step 2 error boundaries precede nested settlement; step 5 verifies actual classifier/monitor behavior |
| More synthetic tests do not prove source behavior | Gate A already precedes Stage 3; Gate B still follows Stage 4 |
| Missing owed artifacts do not permit replacement | Step 3 verifies/refuses replay; step 4 does not make accepted receipts depend on local bytes |

## Risk Review

No additional unhandled risk warrants a severity item after tracing the proposed paths.
Confirmed coverage includes exact-text CAS and strict booleans; revision headroom;
current/prior scope selection; invariant-preserving empty/final closure; bounded
same-attempt rebasing; malformed result/prefix refusal; no timer refresh on replay/ack;
positive-timing fail-closed staging; no generic transaction or scheduler expansion.

Resource cost remains proportional to one pending payload plus verified media bytes,
using the existing synchronous local SQLite/hash helpers. No constant-time or event-loop
latency promise is made. This does not justify widening the task into a storage framework.

## Phase 3 — Proposal Selection

No Medium/High mitigation proposals were needed, so no selected/elegant/last_resort
boxes are fabricated. There is no class-wide fix to split out. The one required action
is the affordable prebuild experiment; if it passes, execute the plan's existing
guards and tests as written. Do not call this primitive PASS a new-runtime or live PASS.
