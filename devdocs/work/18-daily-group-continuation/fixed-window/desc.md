---
model: gpt-6-astra
effort: max
---
# #18 — fixed historical windows

> Session warm at 0a9f82445c45ea64320b873da7b453147a15d2a1 through retained #18
> implementation context and refreshed complete facade/batch/progress/budget/test
> and contract reads; triage checkpoint cd111dd records the §4.1 provision.

## Problem Statement

The batch reader and acknowledged continuation can resume by message ID, but cannot
limit that work to a fixed historical interval. Recomputing "last 30 days" after
restart shifts the query and can omit unfinished history. Filtering whole-history
exports in the application wastes reads and bypasses the reusable batch protocol.

## User Value Proposition

A caller supplies explicit dates or a number of days once, in its chosen progress
store. Later calls reuse the saved interval and either replay an unfinished batch
or read the next portion. Archive/upload ownership and scheduling stay with the
application. Daily and historical collections keep independent bookmarks by using
the existing separate-store collection boundary.

## Success Criteria

1. Callers can read batches within explicit timezone-aware start/end dates. Bounds
   normalize to UTC; start is inclusive and end exclusive. IDs remain the resume
   cursor, including when many messages share a timestamp.
2. Continuation enrollment can save explicit bounds or resolve a positive integer
   last_days once as N*24 hours ending at enrollment time. Repeating the same
   enrollment request after a clock change preserves the original dates and state.
   A different query cannot reset an existing collection.
3. Resume, pending replay and acknowledgment use the persisted window. A replay
   makes no Telegram request. Progress advances only for a completely prepared,
   acknowledged batch. Every persisted pending message must belong to its window.
4. Date positioning avoids walking all older history on an initial zero-cursor
   read. Filtering occurs before media download. A filtered SDK page is not
   mistaken for end-of-window; requested batch size counts included records.
5. Empty windows produce no pending batch. Reaching the end bound or exhausting
   currently visible history returns the existing end result. Read-budget and
   transport failures remain failures with complete in-window prefixes retained.
6. Existing daily records, pending bytes, no-window calls, batch v1 and custom
   load/compare_and_swap backends retain their contracts. Status exposes saved
   bounds without exposing message contents. Unsupported/corrupt state refuses.
7. Offline tests exercise the actual Telethon1.45 iterator and budget adapter,
   real SQLite restart/acknowledgment, boundary ties and absent/failing storage.
   Relevant regressions and the complete supported offline suite pass.

## Scope Boundaries

This is an extension inside the established reader/progress architecture, not a
new planned-job system. No pacing, scheduler, named jobs, reset/re-arm, permanent
completion marker, multi-reader coordination or automatic daily/backfill routing.
Use separate stores for simultaneous daily and historical collections of one group;
the same group/store cannot be initialized with conflicting query settings.
The existing explicit initial after_id remains available; dates intersect that
exclusive position. No arbitrary output-folder scanning or archive inference.

No edits/deletions, group joining, account routing, #7 health changes, ScrapeOps
edits, duncan commits, live account testing, PR publication or merge in this run.
The earlier daily delivery's description remains its historical scope record;
this subfolder records the newly authorized extension. #18 stays open for the
remaining planned-backfill work and subsequent review gates.

## Priority Level

**Medium (P2).** The user selected this concrete prerequisite for routine historical
reads alongside daily collection; it removes repeated window bookkeeping.

## Known Blockers

None identified for implementation and offline verification. probe_sdk.py confirms
actual SDK date-offset construction, equal-timestamp ID continuation and real
budget resizing/prefix behavior. Its synthetic transport does not validate live
Telegram date selection; the documented API is the vendor contract. Server history
visibility and destination durability remain the existing external boundaries.

Implementation choices to document in the plan: date/wire representability limits,
strict naive-time rejection, query identity on repeated initialization, and additive
versioned progress state. No unchosen business policy blocks those decisions.
