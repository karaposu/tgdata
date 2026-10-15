---
model: gpt-6-astra
effort: xhigh
---
# Batch-reader heartbeat — #37

Session warmed at8ee0a73 (2026-10-15), continuing #30 with refreshed SDK/client/source/consumer reads recorded in warm.md and surfacing-trace.json. Model/effort verified from the current turn. Use existing feat/30-photo-trail-folding, as explicitly requested; no new branch and no change to PR36's reviewed head.

## Problem Statement

ScrapeOps cancels a Telegram fetch after120 seconds without progress. Its old row reader emits heartbeat phases, but get_message_batch and daily continuation do not. A healthy large-media batch can repeatedly be cancelled before a pending delivery exists. The request in source-request.md asks for real batch progress and callback isolation without changing the data/acknowledgment contract.

## User Value Proposition

The caller can keep a slow, active download running while still cancelling a silent request. The same optional callback works for direct batches, daily continuation and pool reads; historical preparations use the same reader and should expose it consistently.

## Success Criteria

1. Optional synchronous heartbeat(phase) defaults to None on batch reads, daily continuation and corresponding pool methods. Backfill preparation exposes it consistently. It is transient, never serialized or part of batch hashes, enrollment, receipts or policy.
2. Real observed progress emits phases: records scanned/prepared (including window-excluded observations), media chunks, entity-resolution/dialog synchronization and actual SDK request activity. No perpetual timer claims an unanswered RPC is alive.
3. Preserve Telethon retry counts, flood thresholds, budget charging and pool's no-auto-wait policy. Request starts/results/flood-wait responses separate consecutive waits. tgdata-owned intentional sleeps can emit periodic phase ticks while actually sleeping. Telethon's internal sleeps remain under its existing threshold: the watchdog must exceed the longest single allowed SDK wait plus ordinary latency (default SDK60s, consumer120s). This is progress notification, not a universal maximum-silence guarantee or a change to SDK policy.
4. A callback exception is logged by type only and ignored. It cannot become an RPC/health failure or change the result, completed-prefix, pending data or cleanup. Real task cancellation remains cancellation. Callbacks are quick synchronous observers; async callbacks are unsupported and must not create unawaited-coroutine leaks.
5. No callback leaks into concurrent/background requests or later operations. Default-None paths preserve compatibility with injected readers lacking the new keyword. Pending replay opens no client and requires no beats; existing local media verification remains unchanged.
6. Actual Telethon1.45 download/request loops, real batch values, SQLite continuation and pool ownership are exercised offline. A download lasting longer than a scaled silence threshold completes when chunks progress; a stalled chunk still cancels. Repeated SDK waits, cached waits, callback failures, cancellation, replay, budget accounting and no-heartbeat behavior have direct tests.

## Scope Boundaries

No MessageBatch version/schema or author/chat metadata change; no automatic acknowledgment, retry redesign, new health success evidence or read-budget refunds. No client-wide mutation of wait thresholds, global SDK/asyncio monkeypatch or generic keepalive timer. The old row reader remains compatible. No ScrapeOps source/deployment edit, live account read, version bump, release or merge in this implementation.

## Priority Level

High: this unblocks the consumer's selected download-mode daily-continuation integration. The implementation remains bounded despite feature-heavy verification across existing consumers.

## Known Blockers

None OPEN. The remaining SDK notification/composition behavior is locally testable and must be exercised before product adoption. If observing waits requires replacing SDK retry semantics or pool lifecycle, stop and return to the contract rather than widening this task silently.
