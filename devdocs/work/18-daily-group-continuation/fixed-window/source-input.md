---
model: gpt-6-astra
effort: max
---
# Fixed historical windows — selected slice of #18

The maintainer asked whether fixed historical windows were well-defined, then:
"okay $task-impl that part". This follows acceptance of tgdata owning progress and
pending observations in caller-selected storage, with archive/upload ownership
remaining in the application.

Selected contract from the discussion: explicit start/end dates or last N days;
resolve a duration once, save UTC bounds, preserve them across restart; start is
included, end excluded; days are 24-hour durations; paginate/resume by message ID
so equal timestamps do not skip messages. The batch/acknowledgment mechanism is
already implemented on this same #18 branch at d096442 and verified at 0a9f824.

This is the fixed-window slice, not the remaining planned-backfill scheduler.
Reuse existing collection-scoped progress stores; daily and historical collections
of the same group use different stores. No named-job registry, pacing, background
loop, reset/re-arm, persistent completion lifecycle, shared-machine competition,
account routing, joining or health redesign. Edits/deletions remain excluded.
ScrapeOps at 6f2b978 guides date-window intent; its UI, cursor writer and whole-walk
completion mechanism are not dependencies. No changes in ScrapeOps, #7 or duncan.
No live Telegram tests or merge. Target SDK remains Telethon 1.45.0.

Keep the previous delivery's documents intact. Formal artifacts for this slice
live in this subfolder of the existing #18 work folder, on its linked branch.
