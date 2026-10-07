---
model: gpt-6-astra
effort: max
---
# Stage 5 — durable pacing and explicit interrupted-attempt recovery

> Session warmed at `246a187` (2026-10-07) — same-session Stage 4/Gate B architecture
> and live evidence retained; complete lifecycle, budget adapter/ledger and health
> paths refreshed. Store/media/batch context retained. Archaeology unchanged.
> See [triage](triage.md). Model/effort confirmed GPT 6 Astra/max.

## Problem Statement

The internal engine records source-end timing and durable admission, but currently
refuses further positive-pause reads as an unfinished stage. It cannot explicitly
resolve an attempt left uncertain by cancellation, process exit or failed publication.
Restart must not grant a free retry, and acknowledging an already delivered batch
must not move its source pacing deadline.

The chosen account's read allowance and Telegram restrictions remain separate from
per-run pacing. A stored failure/retry estimate is an observation, not current account
health or permission to spend. Recovery must resolve the named attempt under the
caller's single-reader ownership, without inferring worker death or modifying a newer
attempt merely because it now occupies the same run.

## User Value Proposition

Callers can schedule short backfill turns around daily scraping, receive a local wait
instead of sleeping inside tgdata, resume the same deadline after restart and explicitly
recover a stopped worker. Pending delivery remains replayable and acknowledgeable
throughout. The application retains scheduling/account/receiver/worker ownership.

## Success Criteria

1. A known source end plus the immutable pause defines the earliest next admission.
   Early preparation returns a content-free wait without source I/O, sleeping or a
   state mutation. Early/late ack, replay, status and retries do not restart the wait.
2. Positive, zero and sub-microsecond pauses work across success, ordinary failure,
   cancellation and process restart. Known UTC evidence is durable; monotonic evidence
   protects elapsed waits within an engine lifetime. Backward/inconsistent evidence
   refuses safely, with the trusted-UTC limitation explicit across lost local context.
3. Recovery validates full run/attempt/command/control context and a required true
   caller assertion that the previous reader stopped. Active local preparation, stale
   or wrong context, missing/corrupt state and unavailable storage never enable reading.
4. A committed source outcome is reconciled without another effect. Otherwise recover
   the exact quiescent attempt once: preserve known end/deadline where available, or
   save a conservative full interval from recovery when the end is unknown. Preserve
   stronger known timing and source observations, pending/cursor and pause/cancel facts.
5. Matching recovery retries, including after an ambiguous commit/restart, retain the
   original result/deadline without new clock/network work. Changed recognized input
   conflicts. Bounded recognition cannot accidentally recover a replacement attempt.
6. Original source exceptions and valid prefixes retain their provenance; known budget/
   SDK wait hints are preserved without raw error text or cached account inference.
   Local eligibility never substitutes for the adapter's actual-send account/allowance
   check. Unknown/indefinite source hints remain unknown, not zero waits.
7. Deterministic clock/actual-budget/SQLite tests, real process commit boundaries and
   the supported offline regressions pass on Telethon 1.45.0. Any copied live-data
   fixture is labeled local validation; mandatory Gate C remains after Stage 6.

## Scope Boundaries

Implement Stage 5 internal operations using the existing strict aggregate. No timer
loop, automatic retry/wake-up, distributed lease, account routing, health redesign,
operator controls (Stage 6), public facade (Stage 7), edits/deletions, permanent archive,
or PR/merge. No live quota policy reset, increase or account read is needed here.

Source restriction metadata is not a second admission authority: the reader/SDK/budget
adapter re-evaluates actual restrictions when an intentional, locally eligible turn
runs. A wait result describes local pacing only, never unconditional account readiness.
Known end time may be retained locally after an unconfirmed save; losing that evidence
requires conservative recovery. Arbitrary undetectable clock jumps remain outside proof.

## Priority Level

**Medium (issue P2 retained)** — next planned prerequisite for operator controls and
Gate C. Incorrect recovery can silently weaken read admission, so the work is heavy
even though the externally visible surface is small.

## Known Blockers

None open. Gate B passed at the entry revision. Clock and strict-record primitives
can be probed locally before implementation; no external account/login is required.
Full live elapsed-time/budget/control validation is an explicit later gate, not a
claim made by offline tests or a reason to implement Stage 6 in this run.

## Inherited lessons

An error is not rollback; source end is not receiver acceptance; operation identity
is more than payload equality; local activity is not Telegram health; saved status
is not fresh account evidence. A timeout is not proof that the previous worker stopped.
An acknowledgment time is not a pacing anchor. Preserve Gate B's unresolved original
records; do not clear them merely to make a later test look finished.
