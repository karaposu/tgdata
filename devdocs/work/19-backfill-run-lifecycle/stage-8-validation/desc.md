---
model: gpt-6-astra
effort: max
---
# Stage 8 — complete public validation and Gate D

> Warm at `cb1297a` (2026-10-07): same-session lifecycle/facade/source/health model
> and prior gates retained; public tests, durable boundaries and live instruments
> refreshed. See [triage](triage.md). Verified gpt-6-astra/max.

## Problem Statement

The public lifecycle and its parts pass scoped tests, but the full feature still
needs combined failure/process histories and real public-flow validation. Existing
internal/live receipts do not prove that the facade, caller, source, backend and
receiver cooperate correctly through restart, delayed acceptance and source restrictions.
Review also needs a complete link from the original intent and critic findings to
observable evidence, including honest remaining deployment assumptions.

## User Value Proposition

Applications can adopt a reviewable lifecycle with evidence that saved progress,
operator intent and exact delivery survive the specified failures. The daily scraper
can give historical and daily work separate turns without mixing their progress.
The maintainer can review one scoped delivery rather than infer readiness from many
individually successful stages.

## Success Criteria

1. A combined public-API suite exercises real SQLite/process boundaries before/after
   creation, admission, publication, ack, empty completion, controls, recovery and
   succession, plus error/cancellation/cleanup, media/state loss and retention histories.
   Observe actual data, requests, state and receiver effects; do not mirror helpers.
2. Relevant supported regressions, examples, compile and declared syntax checks pass
   on Telethon 1.45.0. Count actual passes separately from explicit legacy live skips
   and distinguish syntax checks from the interpreter runtime actually executed.
3. Gate D completes a bounded real backfill through TgData across processes, a real
   pacing wait, delayed delivery and receiver-commit/lost-ack restart. Accepted IDs/
   dates/media and qualified completion agree with an independent frozen oracle.
4. Actual daily and historical public operations use isolated state and sequential
   source turns; each can progress without advancing the other's cursor or deadlines.
5. Representative B/C fault histories run through the actual facade, including local
   health isolation, late controls/results, stale context/receipts, owned stopped-worker
   recovery, lost replies and media custody. Injected local orderings/health fixtures
   are labeled; no synthetic response is presented as Telegram evidence.
6. Source work remains read-only on the approved groups/account, with the unchanged
   authoritative ledger and at most 1,500 allocated requested history slots for this
   stage, including prebuild/reruns. Earlier gate originals stay intact. Secret/account/
   message content remains private; publish only sanitized evidence.
7. Final source/contract/plan/critic traceability and an independent saved-record audit
   explain the complete diff and every required case. Gate D and any invalidated earlier
   gate must pass before review readiness; unresolved failure stops advancement.
8. Commit tests/public documentation separately from work evidence, push the issue
   branch and update #19 accurately. Formal merge-check/PR/fresh PR critic and protected
   merge remain the next requested review stages, not implied by test completion.

## Scope Boundaries

Validate the existing lifecycle rather than introduce another design. No new runtime
behavior is anticipated. Small nonarchitectural corrections may be made and recorded;
larger failures follow task-impl's stop/re-plan rule. The selected validation backend is
actual SQLiteSyncStore, with test-only fault wrappers; the local durable receiver keeps
full scoped snapshots and verified media before acceptance. Other deployment backends/
receivers need equivalent evidence, not a claim extrapolated from this fixture.

No source writes/joins, deliberate server flood/ban generation, competing readers,
automatic account routing, edits/deletions, archive-folder scanning, ScrapeOps changes,
#7 resumption, duncan changes, package release, PR or merge in this scoped run.
Real clock qualification is separate from injected clock edge cases; do not alter
the host clock or reset account allowance to finish a gate.

## Priority Level

**Medium (existing P2).** This is the last required implementation/validation stage
before feature review; missing composition evidence can invalidate otherwise polished APIs.

## Known Blockers

None open for planning. Stage 7 is verified and the approved resources exist locally.
Actual identity/access/oracle/capacity must be requalified. A missing live capability
gates its execution and review readiness; it is never replaced with an assumed PASS.
The public source/selected receiver composition has a cheap real early probe before
the larger matrix/harness depends on it.

## Inherited lessons

Local or internal evidence is not public/live evidence. Error is not rollback;
source end is not receiver acceptance; a hash is not run authority. Confirm process
exit rather than infer death. Preserve original request/control context and waits.
Receiver markers must retain the exact observation and required bytes. A worker's
local counter is not a stage-wide resource bound. A declared limitation is not proof
that an untested critical condition passed.
