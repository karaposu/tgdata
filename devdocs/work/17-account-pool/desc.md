---
model: gpt-6-astra
effort: max
revision: 3
---
# Existing-access account routing — explicit operation ownership

> Session warm at ancestor `ebbaaac` (2026-10-12), carried from the full foundation
> traverse and complete source/controller/health/state/batch/progress-facade/test31
> reads. Current-dev2ddb852 differences inspected; see `triage.md`. No new
> archaeology-skill run claimed. Model/effort verified from current turn metadata.

**Path/weight:** feature-heavy. **Issue:**17; same draft PR26.
**Basis:** first rejected `pr-critic.md`, original/scoped plans and
[completed foundation finding](../../inquiries/2026-10-12_19-42__17-account-pool-foundations/finding.md).
The initial description remains in `desc_r2.md`; the accepted retirement guarantees
remain in `retirement-rework/`. This replaces their incomplete observer/control
assumptions, not the original routing and delivery goals.

## Problem Statement

The pool already selects accounts and composes with quotas and acknowledged group
progress. Its enclosing source task also runs arbitrary application health callbacks.
That mixes a Telegram read's result with the result of reporting it. A cancelled
callback can hide completed messages and a known wait even when the caller did not
cancel. Shutdown can also wait for an operation that is itself waiting for shutdown.
Exact task identity, and even inherited task context alone, do not identify every
such dependency.

The complete traverse reproduced both rejected findings, extended them to successful
reads and asynchronous storage, and rejected a scope-only callback fix. The useful
change is to define source outcome, true caller stop, permitted lifecycle control,
physical retirement and diagnostic data separately. The account router and durable
stores should continue to serve their existing purposes.

## User Value Proposition

An application can still ask for a bounded group read and let tgdata choose an
eligible preconfigured account. A reporting failure cannot erase the read's useful
outcome or weaken account restrictions. Shutdown has a defined ownership boundary.
The application retrieves plain health observations and owns their processing.

Daily/backfill delivery remains durable and acknowledged by the existing progress
engines. The application still owns receiver storage, scheduling, account login/
repair and explicit recovery of uncertain attempts.

## Success Criteria

1. Preserve numeric identity verification, deterministic drain/spread, actual ledger
   admission, stored restrictions, unknown-attempt recovery and the current no-prefix
   failover rules. MessageBatch v1 and group receipt formats stay unchanged.
2. Preserve the exact completed source value/error and complete prefix regardless
   of secondary health/reporting termination. The rule applies on normal completion
   and pool-owned timeout, not just one branch of the wrapper.
3. Distinguish actual caller cancellation, internal attempt timeout and unexpected
   source-internal cancellation. Caller stop retains owned cleanup and propagates
   cancellation. An interrupted source with no completed result must not become
   successful settlement or fresh permission; any complete prefix remains usable.
4. Retain actual SDK/source cleanup through repeated cancellation. Failed retirement
   quarantines the persistent client until successful explicit retry. Cleanup cannot
   replace the primary source/body outcome; no deadline is proof of quiescence.
5. Pool reporting is bounded passive data. The pool executes no application health
   callback, owns no observer task and does not await observation consumers. Capture
   limits and losses are explicit; diagnostics never authorize source work or ack data.
6. A synchronous local `drain_health_events()` returns captured-so-far independent
   event values and a loss indication, then clears them. It works during reads,
   failures and close and after closure, with no source/state I/O or busy predicate.
   Later captures belong to a later drain; reporting is not durable or complete.
7. Direct/detectable descendant lifecycle reentry refuses before mutation. Ordinary
   external close still stops/awaits source work and retires clients. Scope records
   expire and belong to one pool. Storage adapters serve I/O and cannot depend on
   controlling the pool they serve; arbitrary external wait-graph detection is not
   promised. State-only reports do not gain source-operation ownership.
8. Explicitly reject application callback configuration on the unmerged pool API;
   explain migration to passive data. Ordinary TgData/#7/#10 health behavior remains
   as merged. Local faults and credentials/message bodies do not become health data.
9. Preserve both current-dev worker resolver support and the pool's opt-in interrupted
   prefix support at the shared batch seam. The combined composition is tested before
   runtime implementation, rather than assumed safe from each branch separately.
10. A bounded prebuild uses real Telethon1.45.0 methods, native disconnect, ReadBudget,
    SQLite pool/progress stores and real task scheduling with controlled wire replies.
    The combined candidate must preserve source results, saved waits/charges, replay,
    ownership and cleanup in the stated counterexamples and controls.

## Scope Boundaries

This is the selected existing-access first delivery. #7 and #10 are now merged;
that does not add automatic joining, a worker protocol change, affinity, scheduling,
a login wizard, distributed ownership or union-history guarantees to #17.

Retain exclusive persistent account clients; do not replace them with temporary
clients or a global lifecycle supervisor. Keep quota, account permission and group
progress separate. No general health-system retrofit or durable telemetry service.

[ASSUMPTION] One owning process/event loop, exclusive session ownership, trustworthy
UTC and one source reader per group remain the established deployment contract.
Custom providers are not permitted to coordinate the same pool's lifecycle while
serving it. This is an explicit extension contract, not a hidden dependency detector.

**Requested endpoint:** revision-3 re-plan, fresh critic, selected fold and a small
combined real-component prebuild. Application/runtime changes are prototyped only
inside an isolated candidate/export for evidence. The working branch's runtime files
remain unchanged in this run. Implementation, full regression and renewed PR gates
are later work; merge still needs the user's go-ahead. Preserve unrelated files.

## Priority Level

**Medium/P2 feature; blocking correctness work for its continuation.** Another plan
must establish this boundary before further pool implementation can be trusted.

## Known Blockers

### Awaited storage can cancel independently of the caller — CLOSED (measured)

**What was tested:** whether the revised source/observation boundary preserves a
completed source result through real pool-state settlement when the storage adapter
awaits its own cancelled future. The adapter performs storage only and does not call
pool lifecycle; this is inside the supported provider role.

**Result:** NO. The full P0 candidate returned CancelledError with caller requests0,
actual prefix100 but returned prefix0/daily pending=false, and charge200. Before the
SQLite settlement commit the account token remained unresolved; after commit the
wait7200 was saved and the token cleared. Neither case delivered the completed prefix.

**Source/evidence:** `prebuild.md`, `probes/prebuild_r3.py:backend_internal_cancel_after_source`,
`evidence/replan-r3/attempt-1-combined.txt`, recorded by the mandatory real-component
experiment on 2026-10-12. The design premise is known false, not an unanswered vendor
question. Revision3 is `DEPRECATED_step_by_step_impl_plan.md`; do not implement it.

**What must change next:** define cancellation ownership for awaited state-provider
work, preserving source data on local storage interruption while genuine caller
cancellation and uncertain commits remain conservative. Replace the plan, freshly
critique it and rerun the entire combined prebuild. Converting every CancelledError
into an ordinary storage error would also violate the caller-stop contract.
No new account access or human product decision is needed to study this boundary.

Execution-only E1 remains unchanged: two approved logged-in accounts, a shared group
and bounded existing allowance are required for the later live gate. No live work
or budget reset ran. PROJECT_SPECIFICS.md remains absent; no process file was created.

## Inherited lessons the plan must satisfy

- A task finishing does not prove which enclosed activity supplied its result.
- A different task or inherited context is not a complete dependency graph.
- Retaining cleanup cannot make a circular wait valid.
- Reports are observations, not account permission or group acknowledgments.
- Detectable reentry guards supplement explicit provider roles; they do not replace them.
- Real-component prebuild comes before production steps; targeted demonstrations
  alone do not replace the combined gate or final regression/live qualification.
