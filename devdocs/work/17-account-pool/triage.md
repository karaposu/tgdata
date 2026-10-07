# Triage — issue #17

**Weight:** feature-heavy
**Base:** `95ed4c76c4d2aba7800d8793b16eb5d54cfba4ec` (dev, 2026-10-07).
**Surfaced:** distinct-account ownership; ConnectionEngine and its same-account
session pool; HealthMonitor; real-identity budget admission; raw batches; daily
and backfill delivery state; Telethon 1.45 request/authentication behavior;
ScrapeOps selection policy; paused #7 review evidence. See `surfacing.md`.
**Why heavy:** selection combines separate contracts for authentication,
account-wide failures, group visibility, quotas, waits and owed deliveries.
Successful source failover must not falsely mean complete group history.
**Watch for:** cached identity being used as operation ownership, flood waits
hidden inside SDK/authentication paths, changing the quota authority, discarding
a partial batch, treating inaccessible history as empty, or adopting paused #7.

## Authorization and selected boundary

The user selected #17 with task-impl and then explicitly chose: “Routing and
failover for groups accounts can already read; keep #7 paused (recommended).”
This first delivery excludes joining and leaves #7 paused. The original issue
remains the umbrella for that later capability. No protected branch merge or
live account operation is part of this preparation checkpoint.

## Session warmth

Already warm in this same session through #18/#19 implementation, review and
dev merge verification. Refreshed against dev `95ed4c7`: connection_engine,
tgdata facade, health, read_budget, budget_client, batch_engine, message_engine
resolution fallback and sync_engine. Backfill engines/state and receipts remain
unchanged from the just-reviewed merge. Existing architecture summaries retained;
this checkpoint does not claim a second architecture-skill run.

## Traverse decision

Required by CONTRIBUTING §5: a new account ownership structure and a delicate
join between source attempts, budgets and acknowledged progress. Execute the full
same-session traverse in `traverse/` before description/planning. Its purpose is
to establish whether a bounded account reader can safely compose with those
existing contracts, and which decisions belong to the caller. It must not adopt
the rejected #7 implementation or begin its broader health redesign by accident.

## Known evidence and unresolved questions

- ConnectionPool expands sessions of one account; this cannot silently become
  a pool of distinct accounts.
- BudgetClient obtains the authenticated identity from get_me; TgData health
  uses cached primary-client `_self_id`. These are different identity sources.
- SDK waits and connection-engine waits can delay failover. Probe the actual
  installed 1.45 composition before committing to timing/error guarantees.
- Daily/backfill persistence owns pending batches and acknowledgments. Account
  selection must not introduce a second cursor or pretend failover has equal
  historical visibility.
- ScrapeOps `state/accounts.py` at `dc49db8` is policy context, not a budget
  backend to copy: tgdata already reserves allowances before source requests.
- Selection, fairness, affinity, retry scope, warm-up eligibility and restart
  behavior remain design questions for traverse. No runtime implementation yet.

## Model and verification boundary

Feature path: this session reports GPT-6 Astra / max (higher than §9 xhigh).
No delegation; the required critiques remain in this warmed session.
Python 3.11.10, installed Telethon 1.45.0. No 1.33 compatibility work.
Only offline analysis/probes are presently scheduled; real multi-account
qualification will need a concrete bounded gate, not assumed prior results.
