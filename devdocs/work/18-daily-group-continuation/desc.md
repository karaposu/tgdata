---
model: gpt-6-astra
effort: max
---

# #18 — daily group continuation, first delivery

> Session warm at `45bab7172621f576fa5e4b3265f87ec20da04fd5` through retained
> same-session #5/#9/#6 source/implementation/merge context and refreshed full
> facade, batch, storage, lifecycle, budget, health, reader and test reads. The
> source inventory and branch isolation are recorded in triage.md (`b721216`).
> No redundant archaeology rewrite is claimed under CONTRIBUTING §4.1.

## Problem Statement

tgdata prepares stable MessageBatch values, but daily callers still own the cursor,
pending delivery and acknowledgment ordering. A cursor saved too early can skip
data after a crash; a fresh fetch cannot reliably recreate an uncertain delivery.
The current polling cursor is only in memory. The user selected daily continuation
first from #18; planned backfill remains a later delivery of that issue.

## User Value Proposition

A caller enrolls a group once, asks for its next bounded batch, durably stores or
uploads it, and acknowledges it. A later run reopens the same progress and either
replays unfinished delivery or reads after the last accepted message. Missing a
daily run does not create an implicit date gap. The application keeps its existing
scheduler and destination; tgdata supplies the reusable continuation protocol.

## Success Criteria

1. Optional pluggable progress storage and a bundled persistent SQLite backend
   expose asynchronous load and atomic conditional-replacement semantics. Store
   failures remain visible and cannot masquerade as new/empty progress.
2. Enrollment requires a canonical marked numeric group ID and explicit initial
   after_id. Matching repeated enrollment is harmless; conflicting initialization
   refuses to reset state. Group identity is independent of account/session labels.
3. sync_group returns at most one nonempty, durably pending MessageBatch, or None
   when no new messages are currently visible. It uses accepted progress, not a
   rolling date window, and never changes current_group.
4. Pending output is reloaded as the same canonical batch without Telegram calls
   or read-budget use. No subsequent batch is prepared until pending work is
   acknowledged. Status and acknowledgment work without an authenticated client.
5. Acknowledgment takes the pending batch ID, never a supplied replacement cursor.
   It atomically advances to that batch's next_after_id and clears pending output.
   Repeating the latest accepted acknowledgment is harmless even while newer work
   is pending; stale/wrong IDs cannot clear that work.
6. Existing get_message_batch performs all actual reads, retaining proxy, session,
   read-budget and health behavior. New local store/replay operations do not emit
   synthetic Telegram recovery or inherit an unrelated RPC error's classification.
7. A valid nonempty completed prefix from an ordinary read failure is persisted
   as pending before the same read exception is re-raised. If retaining it fails,
   a local SyncError reports that failure and retains the original read exception
   in read_error. No acknowledged progress changes. Cancellation never acknowledges.
8. Optional download mode retains MessageBatch's artifact contract. A pending
   replay verifies referenced blobs under the current caller-supplied directory;
   missing/corrupt files raise without replacing pending bytes. Media mode is fixed
   at enrollment. No automatic artifact deletion or transfer is introduced.
9. The single-reader contract is explicit; duplicate in-flight preparation through
   one instance is rejected and conditional store updates prevent stale overwrite.
   No distributed scheduling, lease or failover service is claimed.
10. A runnable offline example demonstrates destination acceptance and duplicate
    handling before acknowledgment. Tests exercise actual Telethon 1.45.0 code,
    SQLite transactions, process restarts, lost acknowledgments, partial budgets,
    store failures, invalid state and optional media. Existing supported offline
    suites pass; live checks are explicitly skipped.

## Scope Boundaries

Daily continuation only. Backfill, date-window batch extension and ScrapeOps UI/
center/scheduling integration remain outside this delivery. Edits and deletions
are permanently excluded by the user. No concurrent-machine ownership, automatic
joining, account routing, remote database implementation, implicit first-use
current-head policy or group-alias registry. Existing batch v1, polling, DataFrame
and session/budget contracts remain unchanged. No live Telegram operations, duncan
commits or merge without separate go-ahead. Tests target Telethon 1.45.0 only.

The caller's acknowledgment means its chosen destination durably accepted the
batch and requested media. The library cannot verify that external assertion or
promise exactly-once downstream effects. The example/tests demonstrate a local
destination contract, not the user's deployed receiver. Visible history is not a
promise of Telegram archive completeness across accounts or access changes.

## Priority Level

**Medium (P2).** The user runs daily scrapes and selected this work now. Reliable
continuation is directly useful before the future account pool or worker. #18
must remain open for planned backfill after this slice is implemented.

## Known Blockers

None for this library implementation and its offline verification. Explicit caller
acknowledgment avoids a dependency on an unavailable ScrapeOps destination. Real
SQLite process-exit and current SDK/batch probes passed in probe_components.py.
The new implementation's correctness still requires its own tests and reviews.

Active-session metadata confirms gpt-6-astra/max; triage.md records the exact §9
higher-effort interpretation. No lower-model or subagent review is used.
