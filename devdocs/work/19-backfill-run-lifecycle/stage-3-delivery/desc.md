---
model: gpt-6-astra
effort: max
---
# #19 Stage 3 — durable preparation, replay and acknowledgment

> Session warm at `8023adf507457b9b3b553090c7fc3ab56b24625f` (2026-10-07):
> retained same-session architecture/full facade and Gate A work, refreshed complete
> lifecycle/state, CAS, raw batch/media, health and budget sources, and state-test code.

Inputs: [source record](source-input.md), [surfacing](surfacing.md), [triage](triage.md),
[contract](../contract.md), overall [Stage 3](../staged-plan.md#stage-3--prepare-retain-and-acknowledge-one-batch),
and [Gate A PASS](../validation/gate-a.md). The orchestrator supplied this explicit
target folder; the user's task-impl invocation authorizes the complete scoped chain.

## Problem Statement

A saved historical run currently has identity, a fixed window and status, but cannot
durably hand a caller its next batch. A raw fetch alone cannot tell whether a later
retry should replay the same observation or contact Telegram again, and a bare batch
hash does not identify which run/destination may advance. A process exit or an ambiguous
write can otherwise replace an owed observation, skip progress or acknowledge another run.

## User Value Proposition

The caller can prepare one bounded batch, restart and obtain that exact batch locally,
then acknowledge only after its destination has durably accepted it. The engine retains
unaccepted work and required media identity. The caller continues to own scheduling,
the permanent archive, external acceptance and repeat-safe processing.

## Success Criteria

1. A complete run/cursor/control context is required. Stale context refuses before
   source work. A confirmed atomic attempt record precedes every new raw read;
   failed or ambiguous admission produces no read, and unresolved work cannot overlap.
2. A valid nonempty batch is published atomically with its attempt outcome before
   it is returned. Reopen/replay preserves canonical bytes, batch hash and full delivery
   context, with no reader/config/budget call or timer refresh.
3. Download replay verifies the saved bytes under the supplied root. Missing, corrupt,
   truncated or substituted artifacts refuse without refetching or clearing pending.
   Relocation of intact content-addressed artifacts preserves the observation.
4. Acknowledgment matches run, generation, collection, group, destination and batch.
   One atomic transition advances only to the saved next ID. Latest recognized retries
   are effect-free, including while newer work exists. Wrong/retired contexts cannot
   mutate current work; accepted media need not still exist locally at acknowledgment.
5. Ordinary source failures retain their completely prepared valid prefix before the
   same exception is re-raised. Local publication failure exposes the original separately
   in `read_error`. Cancellation propagates without inherited Telegram classification
   or any claim that a prefix/rollback was confirmed.
6. Publication preserves newer compatible control facts and refuses incompatible
   run/attempt/cursor changes. Real storage/failure tests, actual SDK/batch/media
   composition tests and the supported offline regression suite pass.

## Scope Boundaries

This is the internal engine/type delivery, imported directly. No new root exports or
TgData facade until Stage 7. Existing daily/window APIs, state v1/v2, MessageBatch v1,
session/proxy/budget paths and health semantics retain their behavior.

The existing codec requires end/pacing evidence alongside final pending work and a
terminal fact for fulfilled exhaustion. Include that minimal invariant-preserving
closure when publishing/acknowledging actual `end`; do not weaken the codec or discard
end evidence. Stage 4's dedicated completion/uncertain-write audit and fault matrix
remain pending, and Gate B still follows Stage 4.

Stage 5 owns positive timing eligibility and explicit recovery. Stage 3 records the
settled attempt's UTC pacing evidence but fails closed on another source turn when
a prior positive-pause/uncertain timing record requires that unimplemented machinery.
First turns, zero-pause continuation, replay and valid acknowledgment are supported;
no stored pacing setting is rewritten or silently ignored. Unsettled attempts remain
recovery-required. Controls themselves remain Stage 6; valid seeded control snapshots
can test late-result/receipt preservation without claiming those operations exist.

No permanent archive, automatic receiver acceptance, competing readers/leases, source
edits/deletion reconciliation, group joining, account pool, worker/scheduler, #7/duncan,
PR or merge. The next mandatory real-source gate is B; offline transport is not live proof.

## Priority Level

**High correctness priority within issue #19's P2 roadmap.** This is the first
transition boundary at which source work could be repeated or acknowledged incorrectly.

## Known Blockers

No open planning or Stage 3 execution blocker identified. Gate A is PASS and the
required #18/#5/#6/#9 components are present on this feature branch. Their separate
review/merge history is not changed by this task. Later timing, recovery, controls
and live receiver acceptance retain their named stages/gates and are not guessed here.

## Inherited Lessons

- A completed read is not destination acceptance; pending publication precedes return.
- An error after commit does not mean rollback; durable attempt/pending facts outrank memory.
- A batch hash is observation identity, not run or destination authority.
- Local files/storage/cancellation must not acquire a Telegram verdict through exception context.
- Test real primitives before depending on them; synthetic transport does not pass a live gate.
- Retain owed data; never repair corruption by silently fetching a replacement observation.
