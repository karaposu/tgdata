---
model: gpt-6-astra
effort: max
---
# #19 Stage 2 — durable backfill state and creation

> Session warm at `5d0789e7aec9af9884fc0e8479a14f0cec57ea86`: same-session contract
> work plus refreshed storage/window/batch/SDK boundaries. This feature-only merge
> contains #18 prerequisites; it is not a merge/approval of them into dev. Triage
> records the exact source scope. Active model/effort: gpt-6-astra/max.

## Problem Statement

The reviewed contract describes saved runs, but no runtime record or start/status
operation implements it. Building preparation or controls first would make their
progress, intent and recovery authority depend on missing persistence semantics.
Current daily state also cannot distinguish a new historical intention from an old
creation retry, and it must retain its existing independent behavior.

## User Value Proposition

A caller can explicitly create one historical run, keep its stable reference, reopen
it after process restart and recover a recognized creation result without recalculating
its dates. Unknown retries and stale/conflicting context refuse safely. A strict
versioned record provides the foundation for later delivery/control stages. An opt-in
real-source probe can test the saved query at Gate A without waiting for the full API.

## Success Criteria

1. Immutable validated run/start/status/result types represent exact identity, canonical
   group/cursor values, declared origin/destination, media/batch/pacing policy and original
   window request. Portable IDs/revisions preserve precision. Status is content-free.
2. A strict versioned opaque-text lifecycle record stores current run and bounded prior
   recognition, plus the contract's independent facts for later pending/output/end/
   attempt/control/pacing states. Validate nested values and cross-field invariants;
   reject corrupt/unsupported/wrong-kind state without repair or mutation.
3. Storage-only creation distinguishes explicit `new` versus `retry`, recognizes retained
   matching input before observing a clock, refuses changed input/stale predecessors,
   and never converts unknown/missing-known context into fresh creation. Relative dates
   freeze once. A successor requires a matching quiescent, terminal, settled predecessor.
4. Known-reference status works after restart, can report retained prior terminal state,
   and refuses unknown or missing runs. The engine uses the existing async load/CAS
   backend atomically and preserves uncertainty/cancellation without exposing raw errors.
5. Tests use actual SQLite and process/commit boundaries, independent custom backend
   faults and no Telegram. Cover fresh/retried/changed/new-identical requests, invalid
   state, state-kind compatibility, generation/receipt retention, lost commit responses
   and unchanged legacy daily/window records.
6. An explicitly opt-in Gate A probe loads the actual saved dates/origin, reads through
   the existing real batch API, compares with an independent existing-history manifest,
   measures actual request/page boundaries and enforces bounded read-only scope. No
   connection on import/help/preflight, no login code requests, no automatic fixture
   writes or production budget changes. Incomplete evidence cannot produce Gate A PASS.
7. Compile and supported offline suites pass on Telethon 1.45.0. Product code/tests/docs
   and work evidence are separately checkpointed. Stage 2 build status and Gate A result
   are recorded independently; Stage 3 remains blocked without a real Gate A pass.

## Scope Boundaries

This is Stage 2 and Gate A preparation/execution only. No new source preparation,
acknowledgment, lifecycle completion transition, pacing enforcement, controls or recovery
operation is implemented; the codec can represent/test their valid snapshots without
claiming their transitions work. No new TgData constructor/facade wiring or root exports
before Stage 7; use the scoped modules/engine internally for Stage 2 and its probe.

Reuse SQLiteSyncStore's opaque backend in a dedicated collection namespace; do not alter
its schema/protocol or migrate daily/window rows. One active reader per group remains
required. No worker/account pool, group joining, edit/deletion reconciliation, ScrapeOps,
duncan, #7, dev/main merge or deployment. Actual live tests use the chosen existing-group,
read-only approach and require explicit target/fixture inputs.

## Priority Level

**Medium (P2).** The user selected this foundation next. It enables the first mandatory
live check before further lifecycle work depends on its assumptions.

## Known Blockers

No planning blocker identified for Stage 2 implementation and offline verification.
The #18 runtime-base dependency is satisfied on this feature branch by `5d0789e`;
its separate protected-branch review/merge remains outstanding.

**Gate A live resources — CLOSED on 2026-10-07.** This condition was initially OPEN.
The user later selected the account and two existing sources and confirmed exclusive
test-budget context. Independent intervals/media were qualified and
[Gate A passed](../validation/gate-a.md). No arbitrary account, fabricated oracle or
synthetic-only substitute closed it. Stage 3 is unblocked but remains unimplemented.

## Inherited Lessons

- An unknown start retry cannot mean new intent; affirmative new submission and exact
  predecessor context are required. A recognized retry reads stored input before a clock.
- A state record and durable success are different from a received success response;
  actual conditional storage and before/after-commit observations are required.
- A supplied initial checkpoint does not verify its preceding archive. Status keeps
  imported origin explicit and no creation invents accepted delivery or exhaustion.
- Stage 2 should stand on existing mechanisms, not rebuild them. A future snapshot fixture
  tests its codec, not an unimplemented transition. Existing APIs remain unchanged.
- Live source selection needs an independent complete bounded oracle and actual SDK page
  evidence. Synthetic replies and local tests cannot fulfill Gate A.
