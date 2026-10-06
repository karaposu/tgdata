---
model: gpt-6-astra
effort: max
---
# Triage — #18 fixed historical windows

**Weight:** feature-heavy. Date selection, prepared batches, durable state and
acknowledgment meet at a boundary where omissions would be silent.
**Priority:** P2. **Branch:** feat/18-daily-group-continuation.
**Starting commit:** 0a9f82445c45ea64320b873da7b453147a15d2a1.

**Session warmth:** retained same-session #18 implementation and full source reads;
refreshed complete facade, batch engine/value/files, sync engine/store, budget
adapter/ledger, tests19/22 and public contracts. Prior lifecycle/health reads remain
applicable; neither subsystem is redesigned. CONTRIBUTING was re-read to the end.
PROJECT_SPECIFICS.md and AGENTS.md are absent from both tgdata checkouts; actual
README, setup.py and smoke-test runners supply the project commands. No redundant
archaeology refresh is claimed under §4.1. The process hook files are present.

**Surfaced:** API input and timestamp validation; SDK date/ID pagination; record
filtering before media; read budget and complete prefixes; strict saved state;
conditional updates; repeat initialization; offline pending replay; status; batch
v1 compatibility; independent collection stores; docs and offline regressions.
See surfacing.md for item provenance/coverage.

**Watch for:** rolling the window on restart; timestamp ties; SDK-exclusive offsets;
counting filtered messages as delivered; an empty filtered page mistaken for end;
requesting or downloading an entire history to filter later; dropping date filters
after an ID resume; interpreting a budget/error as completion; foreign/out-of-window
pending batches; old state rewritten on load; introducing automatic resets/jobs.

## Traverse decision

Not needed for this selected slice under §5: it extends the settled batch reader
and versioned progress record with an immutable query constraint. It retains the
existing ready/pending/ack transitions, store interface, collection identity and
caller delivery boundary established by the parent's completed traverse. No second
progress lane, scheduler or job lifecycle is being designed here. Those would need
their own analysis when selected. Date-boundary behavior is probed before planning.
Heavy weight does not itself require another traverse.

## Adjacent work and prerequisites

All 12 open/closed issue titles were refreshed and #18's full body/comments read.
#6/#9/#5 are closed and supply the baseline; #7/#17 are independent and untouched.
Reuse #18 and its linked branch. The existing daily implementation is available on
this branch, not merged: later merge gates must assess the combined diff. Its
pending review is not a missing implementation prerequisite for this in-branch
extension. No duplicate issue or new branch is required.

## Model evidence

Matched CODEX_THREAD_ID 01a108f3-12f8-7ef2-bc82-745d4feb2a25 to the current rollout;
latest turn metadata at 2026-10-06T13:14:56.497Z records gpt-6-astra/max. Only model,
effort, cwd and timestamp were inspected. §9's Astra/xhigh row is satisfied in its
higher-effort intent; max is recorded exactly. Skills and reviews run in-session.
