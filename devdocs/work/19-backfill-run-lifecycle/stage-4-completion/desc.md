---
model: gpt-6-astra
effort: max
---
# Stage 4 — truthful completion and uncertain writes

> Session warmed at `62d5f60` (2026-10-07) — retained same-session Gate A/Stage 3
> architecture, raw reader, SDK, budget, media and health context; refreshed the
> complete lifecycle engine, values, state codec, SQLite store, suites and live
> instrument. Archaeology unchanged. See [triage](triage.md).

## Problem Statement

The Stage 3 internal engine already records actual exhaustion and closes a run when
its last obligation is fulfilled. Those minimal transitions preserve the strict
saved-state invariant, but their dedicated completion/crash audit is unfinished.
An exceptional storage reply currently always propagates, even when a real durable
commit can be confirmed by reading the identical state back. The new engine has not
yet passed its real-source delivery/receiver gate.

An empty successful end and a final nonempty delivery have different obligations.
A full batch, interrupted prefix, missing account or unavailable store cannot certify
completion. A commit error cannot certify rollback, and ambiguous source admission
cannot authorize another source read.

## User Value Proposition

A daily scraping application can distinguish finished historical work from data
still owed to its archive, restart without losing that data, and recover a confirmed
write result without fetching Telegram again. Completion remains qualified by the
original window and declared fresh/imported origin. Live evidence tests that the
actual reader, durable state and repeat-safe receiver agree before later stages build
on this behavior.

## Success Criteria

1. Empty real exhaustion completes in its settlement commit; final nonempty output
   completes only with its matching acknowledgment. Full/interrupted/failed reads
   remain incomplete. Reopening complete work performs no source read.
2. Origin and window survive completion/restart; imported progress never becomes a
   claim to have scanned its skipped prefix. Prior cancellation/abandonment cannot
   be relabelled completion.
3. Ambiguous create, publication, empty-completion and acknowledgment writes perform
   bounded authoritative read-back. Exact committed state can confirm success; absent,
   moved-on, unreadable or incompatible state never implies rollback or a new write.
   Admission uncertainty still performs zero source calls; cancellation propagates.
4. Actual SQLite commit-boundary process exits preserve either owed work/unresolved
   attempt or durable completion, including final ack and empty settlement. Repeated
   and wrong-context receipts have no unintended effect.
5. New fault/completion tests and the supported offline suite pass on Telethon 1.45.0.
   Existing contracts keep their regression coverage; changed post-commit reply
   behavior is explicitly documented and its assertions intentionally updated.
6. Gate B uses requalified independent source fixtures from authorized existing
   groups, the same account/ledger, actual engine and durable local receiver. It
   verifies message IDs/media, replay, deduplication, completion and interruption
   without source writes or resetting unknown attempts. Record a conclusive gate
   verdict; Stage 5 remains gated unless PASS.

## Scope Boundaries

Reuse one aggregate and the existing shared closure; no new schema or generic
transaction framework. No timer eligibility/recovery (Stage 5), operator control API
(Stage 6), public facade (Stage 7), scheduler, account routing, multi-reader ownership,
edits/deletions or permanent archive inside tgdata. A seeded control fixture checks
preservation only; it does not implement or live-validate controls.

The disposable receiver is test infrastructure, not the production archive. It makes
its acceptance repeat-safe and durably commits payload/blob custody before ack.
Exact read-back is conservative: a newer snapshot may require the existing explicit
status/same-request retry rather than an inferred partial match. Backend durability
and truthful authoritative reads remain the caller's store contract.

No PR, merge, #7/duncan changes, or unrelated worktree edits.

## Priority Level

**Medium (issue P2 retained)** — false completion can silently skip required history. This is
the next planned prerequisite for durable pacing/recovery, not a separate backlog item.

## Known Blockers

None open for planning. Gate A passed; selected account, two existing read-only
groups and the authoritative budget remain available from this session. Actual
current source visibility and budget capacity must still be checked by bounded live
qualification. An unavailable live prerequisite gates Gate B, not independent local
implementation, and must be reported without weakening the gate.

## Inherited lessons

An error is not rollback; read completion is not delivery acceptance; payload hash
is not run authority; local failure is not Telegram health; synthetic tests do not
establish vendor behavior. Stage 3's short-slice fixture correction demonstrated why
only actual end evidence, never response length alone, may close a scan. The contract
and prior lifecycle traverse settle the intended ownership; this stage stays within it.
