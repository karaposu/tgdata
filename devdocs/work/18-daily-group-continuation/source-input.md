---
model: gpt-6-astra
effort: max
---

# #18 — authorized first delivery

On 2026-10-06 the user accepted: “I would implement daily continuation first”
and instructed: “okay do it”. The prior discussion established these boundaries:

- tgdata is used to scrape Telegram groups daily; missed runs must resume from
  acknowledged progress, not a newly calculated last-24-hours window.
- One active reader per group is sufficient now. Competing readers across
  machines are not needed.
- Reconciliation of old edits and deletions is never required for this feature.
- First delivery: durable daily continuation, saved pending batches, explicit
  acknowledgment, and restart recovery. Planned backfill is a later delivery.
- The caller stores/uploads/processes the data, then acknowledges durable
  acceptance. No concrete ScrapeOps receiver is available in this repository.
- #7 remains paused, with its local handoff in the original checkout and PR16
  draft. This branch starts from merged dev, not the rejected #7 implementation.
- Do not commit duncan; use Telethon 1.45.0, without 1.33.1 work. No live Telegram
  calls or group mutations are authorized by this implementation run.

The original request is https://github.com/karaposu/tgdata/issues/18. Its original
body also requests shared progress and backfill; the issue must remain open for
the undelivered backfill scope after this first delivery. #17 is a separate future
account-routing proposal; #10 is a separate worker proposal.

## Supplied ScrapeOps context

The user supplied a read-only handoff checked in that other repository at dev
6f2b978. This is user-provided evidence; its files were not independently read here.

Manual `scrape --last 30d` is an ordinary explicit-window scrape. Planned backfill
is enabled per group in the dashboard, with window_days, batch_size, pause_s and
done_at stored in the roster/center plan. Idle loop wakes select an enabled plan;
one long run holds a job lock, invokes tgdata with date bounds and chunk pacing,
and marks done on success. Failure leaves the plan armed. Backfill neither reads
nor advances the daily group cursor. Chunk callbacks report pacing/progress, not
a demonstrated durable per-chunk acknowledgment checkpoint. The supplied handoff
also notes that an active walk blocks daily work, keyed mode can start it during
center cooldown, and defaults are duplicated.

This future integration should preserve separate daily/backfill progress, freeze
a backfill run's date window, and return to the scheduler between acknowledged
chunks. UI settings, scheduling priorities, cooldowns and account allocation stay
with the consumer. None of that scheduler/backfill work is in this first delivery.

## Grounding retained from the preceding assessment

The merged MessageBatch API prepares ascending, bounded raw snapshots, gives
partial completed prefixes on ordinary failures, and serializes immutable replay
bytes. It owns no durable cursor. The existing DataFrame reader supports bounded
date windows and forward walks; that is future backfill groundwork, not a reason
to add reverse cursors now. The session-store interface has different failure and
atomicity semantics and cannot silently become a progress store.
