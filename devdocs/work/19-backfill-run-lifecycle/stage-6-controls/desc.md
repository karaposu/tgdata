---
model: gpt-6-astra
effort: max
---
# Stage 6 — operator controls, concurrent settlement and safe retirement

> Session warmed at `1896820` (2026-10-07) — same-session Stage 5/Gates A/B context
> retained; lifecycle/state/store and actual source-budget/facade interfaces refreshed.
> Prior source/media/health full-file context retained, archaeology unchanged.
> See [triage](triage.md). Session model/effort: GPT 6 Astra/max.

## Problem Statement

The internal engine has durable delivery, completion, pacing and explicit recovery,
but operator controls exist only as a contract and seeded preservation fixtures.
Callers cannot yet pause/cancel a run or explicitly retire its owed data. A late result,
acknowledgment or repeated command must not overwrite newer operator intent, revive
terminal work or settle another generation's obligation.

Stages 5–6 also need real Gate C evidence: timing across restart/ack/failure, current
budget enforcement, actual stopped-worker recovery and forced operator/receipt races.
Local tests alone cannot establish that source/store/receiver composition.

## User Value Proposition

An application can stop new backfill reads while delivering what it already owes,
resume without resetting pacing/quota, cancel terminally and deliberately abandon an
obligation before creating a successor. Exact command context makes delayed requests
harmless. The app retains scheduling, account/receiver ownership and source-worker
quiescence; tgdata provides the reusable lifecycle rules.

## Success Criteria

1. Pause/resume decisions use full run/command/expected-control identity. New matching
   decisions, including already-paused/active decisions, advance control revision once;
   identical retained retries have no second effect. Changed/stale commands refuse.
2. Pause/cancel deny new admissions but preserve an already admitted bounded attempt,
   pending delivery, accepted position, pacing and failure observations. Resume restores
   only operator permission, never quota or terminal activity.
3. First committed terminal outcome wins. Final ack after cancellation remains cancelled;
   cancel after completed exhaustion reports the existing completion without rewriting it.
4. Abandonment requires quiescence and explicitly records the withdrawn obligation,
   with no accepted-cursor advancement or physical blob deletion. Cancelled stays
   cancelled. A successor requires exact predecessor, terminal/quiescent/settled state;
   late old/retired receipts never change it.
5. Existing late settlement reloads and preserves compatible controls using the same
   admitted run/attempt/cursor. Ordinary data writes cannot consume or overwrite a newer
   control decision. Controls leave revision capacity for still-owed settlement/ack.
6. Lost replies, concurrent controls, stale resume/prepare, retention, clocks, corrupted
   state and actual SQLite/process boundaries pass the supported offline tests on
   Telethon 1.45.0. Local operations create no source traffic or health evidence.
7. Gate C passes real bounded reads and measured timing, actual restrictive test-budget
   exhaustion/re-admission, owned-worker exit/recovery and controlled operator/receipt
   orderings with an actual durable receiver. Preserve exact expectations/evidence and
   stop before Stage 7 if a required case cannot pass.

## Scope Boundaries

Keep the existing strict aggregate and raw reader/budget/health contracts. Add internal
control/results and needed status evidence; no public facade (Stage 7), scheduler,
account routing, distributed leases, edits/deletions, blob garbage collection, PR/merge,
or #7/duncan work. Retained terminal histories support read-only recognition, not new
mutations of old generations. A new command on already terminal work can report that
outcome without becoming an accepted new decision; current cancelled abandonment is
the explicit exception allowed by the contract.

Gate C uses the approved existing groups/account, unchanged authoritative ledger and
new private test state. A dedicated smaller real allowance may be increased only as
specified for the test, preserving charges and never bypassing the shared ledger.
No Telegram writes or manufactured server bans/floods. Natural expiry is separately
labeled deterministic evidence, not confused with a test-policy increase.

## Priority Level

**Medium (issue P2 retained)** — the next planned prerequisite for the public lifecycle.
The work is heavy because failures cross temporal ownership and can silently lose data.

## Known Blockers

None open for planning. Gate B passed and Stage 5 is verified. The real test allowance
composition is a cheaply testable premise; validate it before relying on Gate C.
Live session/view/capacity must be requalified. If unavailable, that gates the live
step and Stage 7, not independent local implementation, and is never an assumed PASS.

## Inherited lessons

Error is not rollback; source end is not destination acceptance; hashes are not run
or command authority; timeout does not prove worker death; local activity is not
Telegram health. Neither ack/control nor restart may reset a source wait or quota.
Late response arrival is not accepted command order. Prior A/B originals remain evidence.
