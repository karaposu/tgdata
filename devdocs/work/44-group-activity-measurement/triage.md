---
model: gpt-6-astra
effort: xhigh
---
# Triage — #44 activity and engagement measurement

## User Input
`$task-impl #44 — Activity and engagement measurement (P2)`.

## Intake and warmth
Base dev490cf5f4aaf682a1ed9fcf8c680be56f2ec14c92 includes merged #43.
Branch feat/44-group-activity-measurement was linked using gh issue develop;
an isolated /private/tmp worktree preserves the original checkout/version edit.
No #44 artifacts, PARKED block or rejected PR critics existed at intake.
All open/closed issue titles were read; #43/#6/#7/#18/#19 are delivered foundations,
#45 sampling and #46 discovery resume remain separate. No duplicate.

Same session as the complete #43 implementation/review/merge; ownership, factory,
health, budget, heartbeat and profile code remain in context. Newly refreshed
batch reader, history-window constraint, raw-batch schema, progress facade and
actual1.45 SDK message iterator/counter types, plus downstream measure.py.
No new all-tree archaeology sweep is claimed. PROJECT_SPECIFICS.md is absent.
Current turn metadata2026-10-15T19:46:59.404Z verifies gpt-6-astra/xhigh.

## Surfacing — bounded territory
Artifact/signal-first. Purpose: determine what #44 reaches before selecting its
measurement/coverage contract. The workspace contains:
- CORE: batch_engine/history_window/message_batch — source scanning, date boundaries
  and compatibility; current get_message_batch drops engagement counters.
- CORE: group_operations/account_operation/tgdata — explicit owner/reference/facade.
- CORE: budget_client/read_budget and owned_health/health — per-send claims, original
  failures and conservative recovery.
- CORE: batch_heartbeat and group_profile — observational liveness and prior bounded
  value/partial-error conventions.
- CORE: Telethon1.45 _MessagesIter and Message/MessageReplies/MessageReactions —
  wire data, page handling, unknown placeholders and counter meaning.
- SUB: progress_facade, album and public batch/window contracts — existing consumers
  that must not silently change format/cursor or counting unit.
- SUB: downstream measure.py and the audit guide — motivating gaps, not the spec.
- SUB: SDK/TL/SQLite fixtures32/33/34/45 and fixed-window tests23 — composition probes.
- SIDE: existing get_statistics(df) — simple supplied-row summary, not source coverage.
- UMBRELLA: live source visibility/history order — offline replies alone cannot
  establish it; keep as an inquiry/validation frontier rather than assume it away.

New behavior must not change #6 v1, sync/backfill progress, album views, worker/pool
routing or stored sessions. Read budgets and source ownership are reused, not rebuilt.
Recency provenance and detailed traversal are retained by the subsequent inquiry
surfacing pass; relevance here is from content, not mtimes.

## Weight
**feature-heavy.** A new observation model and scan/coverage semantics support
several consumers and can fail silently. Count precision, raw wire availability,
author identity, period denominators, paging and cancellation meet.

## Traverse decision
**Required under §5.** The window-observation contract is a new structure later
measurement/sampling work can stand on. Its most important ambiguity is what
source evidence establishes coverage/completion under explicit cost limits.
Also settle raw message versus logical post, absent versus zero counters,
observed counts versus accrued activity, and original-failure/partial custody.
Run full A→Su→S→D→I→C→R sequentially in traverse/ per the issue work-folder rule.
Do not write the implementation plan until those meanings are settled.

## Early source findings (no design selected)
The real SDK iterator omits MessageEmpty rows and may stop on full-vector,
empty-page or iterator conditions. It does not expose every source page fact
needed for a new independent completeness claim. A short page alone is not
source end (SDK itself documents this). Existing historical batches enforce an
ID cursor and half-open date filter but their fixed v1 omits engagement fields.
The downstream reader excludes zero views, merges missing senders and hides
cap exhaustion. These require a qualified new contract, not copying the script.
