---
model: gpt-6-astra
effort: max
---

# Surfacing — #18 daily continuation

## User Input
Implement the daily-continuation first delivery of #18, using the source-input.md constraints.

## Traversal Trace
Artifact mode; signal-first; explicit bounded territory: merged tgdata source/interfaces, their batch/budget tests, current user constraints, and contribution procedure. Same-session retained workspace supplied. Relevance is content-based; mtimes are descriptive only.

| # | Region | Item | Tag | Confidence | Recency annotation |
|---|---|---|---|---|---|
| 1 | facade | `tgdata/tgdata.py` | core | HIGH | filesystem: 2026-10-06T09:51:24.355342+00:00 |
| 2 | batch | `tgdata/batch_engine.py` | core | HIGH | filesystem: 2026-10-06T09:51:24.341723+00:00 |
| 3 | batch | `tgdata/message_batch.py` | core | HIGH | filesystem: 2026-10-06T09:51:24.344687+00:00 |
| 4 | artifacts | `tgdata/batch_files.py` | core | HIGH | filesystem: 2026-10-06T09:51:24.342085+00:00 |
| 5 | budget | `tgdata/read_budget.py` | sub | HIGH | filesystem: 2026-10-06T09:51:24.345879+00:00 |
| 6 | budget | `tgdata/budget_client.py` | sub | HIGH | filesystem: 2026-10-06T09:51:24.342772+00:00 |
| 7 | lifecycle | `tgdata/connection_engine.py` | sub | HIGH | filesystem: 2026-10-06T09:51:24.343231+00:00 |
| 8 | storage precedent | `tgdata/session_store.py` | sub | HIGH | filesystem: 2026-10-06T09:51:24.346626+00:00 |
| 9 | health | `tgdata/health.py` | sub | HIGH | filesystem: 2026-10-06T09:51:24.344221+00:00 |
| 10 | legacy reader | `tgdata/message_engine.py` | sub | HIGH | filesystem: 2026-10-06T09:51:24.344990+00:00 |
| 11 | public surface | `tgdata/__init__.py` | core | HIGH | filesystem: 2026-10-06T09:51:24.341208+00:00 |
| 12 | tests | `tgdata/smoke_tests/test_18_read_budget.py` | sub | HIGH | filesystem: 2026-10-06T09:51:24.353885+00:00 |
| 13 | tests | `tgdata/smoke_tests/test_19_message_batches.py` | core | HIGH | filesystem: 2026-10-06T09:51:24.354210+00:00 |
| 14 | docs | `README.md` | core | HIGH | filesystem: 2026-10-06T09:51:24.317306+00:00 |
| 15 | docs | `docs/message_batch_v1.md` | core | HIGH | filesystem: 2026-10-06T09:51:24.337935+00:00 |
| 16 | docs | `tgdata/smoke_tests/README.md` | sub | HIGH | filesystem: 2026-10-06T09:51:24.347166+00:00 |
| 17 | process | `CONTRIBUTING.md` | umbrella | HIGH | filesystem: 2026-10-06T09:51:24.316701+00:00 |
| 18 | packaging | `setup.py` | side | HIGH | filesystem: 2026-10-06T09:51:24.340474+00:00 |
| 19 | packaging | `requirements.txt` | side | HIGH | filesystem: 2026-10-06T09:51:24.339849+00:00 |
| 20 | requirements | current user request and supplied ScrapeOps handoff, preserved in source-input.md | core | HIGH | source: none; value: null |

## State Summary
Purpose: expose all surfaces touched by durable, acknowledged daily continuation without scheduling or backfill.
Coverage: all listed regions confirmed at full-file/interface resolution, using retained full reads plus current refreshes. The external ScrapeOps implementation is represented only by the supplied handoff; no independent coverage claimed.
Confirmed absent: durable daily progress/pending-batch owner in merged tgdata; implementation of backfill scheduling in this repository; PROJECT_SPECIFICS.md/AGENTS.md in the checkout.
Concept names with provenance: public batch (1–3); immutable replay (3–4); account admission (5–6); client lifecycle (7); store precedent (8); local failure classification (9); date-window reader (10); API export (11); synthetic transport (12–13); acknowledgment contract (14–15); test inventory (16); contribution boundaries (17); supported runtime (18–19); daily versus backfill scope (20).

Recency distribution:
- facade: oldest=2026-10-06T09:51:24.355342+00:00, newest=2026-10-06T09:51:24.355342+00:00, no-mtime-count=0, total-items=1
- batch: oldest=2026-10-06T09:51:24.341723+00:00, newest=2026-10-06T09:51:24.344687+00:00, no-mtime-count=0, total-items=2
- artifacts: oldest=2026-10-06T09:51:24.342085+00:00, newest=2026-10-06T09:51:24.342085+00:00, no-mtime-count=0, total-items=1
- budget: oldest=2026-10-06T09:51:24.342772+00:00, newest=2026-10-06T09:51:24.345879+00:00, no-mtime-count=0, total-items=2
- lifecycle: oldest=2026-10-06T09:51:24.343231+00:00, newest=2026-10-06T09:51:24.343231+00:00, no-mtime-count=0, total-items=1
- storage precedent: oldest=2026-10-06T09:51:24.346626+00:00, newest=2026-10-06T09:51:24.346626+00:00, no-mtime-count=0, total-items=1
- health: oldest=2026-10-06T09:51:24.344221+00:00, newest=2026-10-06T09:51:24.344221+00:00, no-mtime-count=0, total-items=1
- legacy reader: oldest=2026-10-06T09:51:24.344990+00:00, newest=2026-10-06T09:51:24.344990+00:00, no-mtime-count=0, total-items=1
- public surface: oldest=2026-10-06T09:51:24.341208+00:00, newest=2026-10-06T09:51:24.341208+00:00, no-mtime-count=0, total-items=1
- tests: oldest=2026-10-06T09:51:24.353885+00:00, newest=2026-10-06T09:51:24.354210+00:00, no-mtime-count=0, total-items=2
- docs: oldest=2026-10-06T09:51:24.317306+00:00, newest=2026-10-06T09:51:24.347166+00:00, no-mtime-count=0, total-items=3
- process: oldest=2026-10-06T09:51:24.316701+00:00, newest=2026-10-06T09:51:24.316701+00:00, no-mtime-count=0, total-items=1
- packaging: oldest=2026-10-06T09:51:24.339849+00:00, newest=2026-10-06T09:51:24.340474+00:00, no-mtime-count=0, total-items=2
- requirements: newest=null, oldest=null, no-mtime-count=1, total-items=1
Frontier: group/source identity, initial position, atomic acknowledgment, pending artifacts and partial-failure contract are for downstream interpretation. No unread blocking code region is hidden.
Workspace-populated: true; populated-at: 2026-10-06T09:56:32.269738+00:00; extent: 20 trace items.

## Telemetry
Cycles: 4 (requirements/public batch; storage/lifecycle; tests; docs/process). Items: 20; core=9, sub=8, side=2, umbrella=1. Filesystem mtimes=19; without mtime=1. Boundary discovery: not fired. Convergence: bounded territory covered, uncertain relevance retained. Workspace-overload: not fired.
Checked: missed-relevance, surfaced-irrelevance, over-coverage, territory-mis-binding, workspace overload, artifact under-specification, workspace/artifact desync, recency-equates-idleness, recency-bias-filter, interpretive-overstep, purpose-loss and downstream coupling.
**Self-assessment: PROCEED.** Interpretation/selection deliberately deferred to traverse.
