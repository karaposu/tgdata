# Existing-access account routing and recovery — #17

> Session warmed at `95ed4c76c4d2aba7800d8793b16eb5d54cfba4ec` (2026-10-07),
> retained from this session's #18/#19 implementation and merge verification;
> connection, health, budget, raw batch and progress interfaces refreshed for #17.
> Existing architecture summaries retained; no second warm-up skill run claimed.

**Path/weight:** feature-heavy. **Model:** GPT-6 Astra / max.
**Source:** issue17 and confirmed scope in `source-input.md`.
**Design basis:** `traverse/finding.md`, completed in `d1daa84` after two iterations.

## Problem Statement

An application currently chooses the account for every group read and implements
its own reaction to account logout, ban, cooldown, lost group access and exhausted
allowance. Tgdata's ConnectionPool only supplies several sessions of one account.
It is not a distinct-account router.

Simply wrapping TgData instances is unsafe: actual-account budget admission and
cached-identity health can disagree, and ordinary authentication can sleep through
long flood waits. Restart and partial reads also require explicit stopping rules.

## User Value Proposition

An application supplies accounts, their existing configuration/session sources,
known groups, a shared ReadBudget and persistent pool state. It asks the pool for
a bounded group batch or uses the existing daily/backfill operations. The library
selects eligible accounts and moves past recoverable source failures, preserving
the existing delivery and allowance contracts.

The application retains scheduling, receiver storage, account login/repair and
explicit recovery of unknown source attempts. Adding this library capability does
not turn tgdata into an application worker or scheduler.

## Success Criteria

1. Separate AccountPool/PoolAccount/PoolGroup API; existing TgData construction,
   connection_pool_size and MessageBatch v1 behavior unchanged.
2. Canonical group IDs and fixed expected account IDs; fresh actual identity checked
   before history and at actual quota admission. Duplicate inventory/known session
   credentials refuse. Unknown identity is reported honestly.
3. Deterministic drain/spread selection uses the existing ledger and explicit
   optional minimum warm-up age. No local budget reset, refund or unlimited fallback.
4. No terminal login, joining, dialog sweep or hidden long flood sleep. Cooperative
   timeout awaits source-task termination before any failover.
5. Account attempts are durably admitted before source calls. Token-specific
   settlement records scoped failures; uncertain attempts remain blocked across
   restart. Explicit initialization/recovery cannot erase known prohibitions.
6. No more than one active pool operation; each candidate attempted at most once
   per read. Structured unavailable/busy outcomes never masquerade as empty history.
7. Nonempty prefixes stop failover. Timeout and local settlement errors preserve
   complete records; ordinary source exceptions retain their type and prefix.
   Caller cancellation propagates and never starts another account.
8. Daily/backfill use their current engines and acknowledgment rules. Pending
   replay/ack need no account configuration, selection, authentication or quota.
9. Local input/store/media faults never become Telegram health or failover reasons.
   Errors/status/logs contain no credentials or stored message content.
10. Actual Telethon1.45/SQLite offline histories cover stale identity, waits, quota,
    no access, partial reads, cancellation, uncertain writes, restart and concurrency;
    existing supported offline suites pass. A separate bounded live gate qualifies
    two real accounts when resources are available.

## Scope Boundaries

- The user explicitly selected existing-access routing/failover. Automatic joining
  is deferred and #7 remains paused; no rejected #7 implementation is adopted.
- No global retrofit of all existing health ownership, login wizard, account repair
  automation, background scheduler, distributed pool or competing group reader.
- No union-history guarantee, old edit/deletion reconciliation, new message schema,
  copied quota ledger or copied cursor/receipt lifecycle.
- No merge or deployment in this request; merge-check/PR/fresh critique remain later.
- [ASSUMPTION] One owning process/event loop, exclusive client/session ownership,
  trustworthy UTC and caller-enforced single reader per group. Clock regression
  and unresolved attempt state refuse new source permission.
- [ASSUMPTION] Offline implementation proceeds while the optional two-account live
  setup question is unanswered; synthetic account tests are never called live proof.

## Priority Level

**Medium / P2**, selected now by the maintainer. This removes duplicated routing
from scraping consumers while preserving already-built daily/backfill delivery.

## Known Blockers

No open planning blocker. Execution-only: two already logged-in, distinct accounts
and an approved shared group plus bounded allowance are needed for the live gate.
That does not gate code, documentation or deterministic offline verification.
