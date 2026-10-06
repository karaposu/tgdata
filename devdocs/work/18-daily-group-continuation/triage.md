---
model: gpt-6-astra
effort: max
---

# Triage — #18 daily group continuation

**Weight:** feature-heavy.
**Path:** feature, existing issue #18 (`enhancement`).
**Priority:** P2 — regular daily use makes reliable continuation current work;
the maintainer selected this first delivery from the previously parked backlog.
**Base:** dev `45bab7172621f576fa5e4b3265f87ec20da04fd5`.
**Branch:** `feat/18-daily-group-continuation`, created with `gh issue develop`
in `/private/tmp/tgdata-18-daily-group-continuation`.

**Session warmth:** retained from the same session's #5/#9/#6 implementation and
merged-code verification, #7 investigation and the #18 assessment. Full current
reads refreshed the facade, batch engine/value/files, message engine, read budget,
session store, connection and health paths, package exports, batch/budget tests,
README and public batch contract. The #7-to-dev differences were inspected; #7's
new operations are absent from this base. No repeat warming/archaeology rewrite
is claimed. This records the §4.1 retained-session provision.

**Surfaced:** public facade; MessageBatch preparation/serialization/publication;
durable cursor and pending output (absent today); read admission and exceptions;
session identity and group identity; health reporting of local failures; completed
prefixes; canonical group IDs; caller acknowledgment; media retention; daily
scheduling and future backfill boundary; offline SDK/SQLite testing. See the
companion thin `surfacing.md` trace for provenance and coverage.

**Why heavy:** batch data, durable progress and external acknowledgment meet at a
failure-sensitive boundary. Advancing early can silently omit records after a
restart; replay and progress have different lifetimes. Both laptop callers and a
future server consumer use it. Scope is moderate, but silent record loss makes
the contribution weight heavy independently of code size.

**Watch for:** confusing fetched with accepted; exposing an unsaved batch as
replayable; selecting progress by mutable username or account; acknowledging a
different/stale batch; treating a store outage as first use; re-fetching a pending
observation after Telegram changes; local errors inheriting RPC health; optional
media silently missing on replay; partial prefix handling hiding the failure;
reintroducing scheduler/failover/backfill work while implementing daily progress.

## Traverse decision

Required under CONTRIBUTING §5: this creates a durable state model and connects
the existing immutable batch contract to caller acceptance. Run the full traverse
pipeline in `traverse/` before description/plan. It must settle identity, first-use
position, pending/acknowledged transitions, storage boundaries and failure meaning.

## Prerequisite and adjacent-work check

All open/closed issue titles were refreshed. #6 supplies the merged batch contract;
#9 supplies optional read budgets; #5 supplies credential persistence. Their
outcomes were read in this session and are already on the base. #7's unmerged
lookup/join/health changes and #17's routing are not prerequisites for a caller
already able to read a group. #10 is a future consumer. No duplicate daily-state
task exists. Do not reopen or modify these other tasks.

The unresolved storage/API decisions are locally resolvable design work, not
human-only blockers. An explicit acknowledgment API can be delivered without
access to the user's downstream storage. The caller's eventual integration is
outside this library implementation and must not be claimed as tested.

## Model evidence

The current environment's CODEX thread/session ID matched the resumed rollout
file. Its latest turn_context at 2026-10-06T09:48:33.228Z records gpt-6-astra/max.
Only model/effort/time/cwd fields were read; no credentials were displayed.
§9 names Astra/xhigh; max is recorded exactly and treated as satisfying the
capability/effort intent, not relabeled as xhigh. Reviews run in this same session.
