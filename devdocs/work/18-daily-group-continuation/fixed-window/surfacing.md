---
model: gpt-6-astra
effort: max
---
# Surfacing — fixed windows

## User Input
Implement the fixed historical-window slice of #18, as recorded in source-input.md.

## Traversal Trace
Artifact; signal-first; explicit bounded territory: existing batch/progress paths,
their SDK/budget interfaces, tests and public contracts. Same-session parent
workspace retained. The tags below are content-based, not mtime-based.

| # | Region | Item | Tag | Confidence | Recency annotation |
|---|---|---|---|---|---|
| 1 | facade | `tgdata/tgdata.py` | core | HIGH | filesystem: 2026-10-06T10:49:27.177003+00:00 |
| 2 | batch | `tgdata/batch_engine.py` | core | HIGH | filesystem: 2026-10-06T09:51:24.341723+00:00 |
| 3 | batch | `tgdata/message_batch.py` | core | HIGH | filesystem: 2026-10-06T09:51:24.344687+00:00 |
| 4 | batch | `tgdata/batch_files.py` | sub | HIGH | filesystem: 2026-10-06T09:51:24.342085+00:00 |
| 5 | progress | `tgdata/sync_engine.py` | core | HIGH | filesystem: 2026-10-06T10:49:27.154864+00:00 |
| 6 | progress | `tgdata/sync_store.py` | core | HIGH | filesystem: 2026-10-06T11:08:14.994040+00:00 |
| 7 | budget | `tgdata/budget_client.py` | sub | HIGH | filesystem: 2026-10-06T09:51:24.342772+00:00 |
| 8 | budget | `tgdata/read_budget.py` | sub | HIGH | filesystem: 2026-10-06T09:51:24.345879+00:00 |
| 9 | tests | `tgdata/smoke_tests/test_19_message_batches.py` | core | HIGH | filesystem: 2026-10-06T09:51:24.354210+00:00 |
| 10 | tests | `tgdata/smoke_tests/test_22_daily_continuation.py` | core | HIGH | filesystem: 2026-10-06T11:08:15.016261+00:00 |
| 11 | contract | `docs/daily_continuation.md` | core | HIGH | filesystem: 2026-10-06T11:00:21.342435+00:00 |
| 12 | contract | `docs/message_batch_v1.md` | core | HIGH | filesystem: 2026-10-06T09:51:24.337935+00:00 |
| 13 | docs | `README.md` | sub | HIGH | filesystem: 2026-10-06T11:00:21.365275+00:00 |
| 14 | docs | `tgdata/smoke_tests/README.md` | sub | HIGH | filesystem: 2026-10-06T11:00:21.392486+00:00 |
| 15 | packaging | `setup.py` | side | HIGH | filesystem: 2026-10-06T09:51:24.340474+00:00 |
| 16 | process | `CONTRIBUTING.md` | umbrella | HIGH | filesystem: 2026-10-06T09:51:24.316701+00:00 |
| 17 | parent | `devdocs/work/18-daily-group-continuation/traverse/finding.md` | sub | HIGH | filesystem: 2026-10-06T10:24:53.222987+00:00 |
| 18 | SDK | Telethon 1.45.0 client/messages.py iterator and public iter_messages documentation | core | HIGH | source: none; value: null |
| 19 | requirements | current fixed-window discussion | core | HIGH | source: none; value: null |

## State Summary
Coverage confirmed through complete current reads for the listed project files;
SDK coverage is the relevant complete iterator plus public parameter contract.
Parent's complete lifecycle/health context is retained; neither is edited.
Confirmed absent: fixed-window support in the batch/progress APIs; project card and
AGENTS files in the tgdata checkouts. Proposed new module/test names are plan outputs,
not existing items. Four cycles: contract, runtime, SDK/budget/tests, docs/process.
Concepts/provenance: date constraints(1–2,18–19); immutable observations(3–4);
state/replay/acknowledgment(5–6,11,17); guarded admission(7–8); behavioral regression
(9–10); public wire contract(12); usage/test inventory(13–14); compatibility(15);
workflow(16). Side/umbrella items retained; no uncertain-relevance exclusions.
Recency distribution (descriptive only):
- facade: oldest=2026-10-06T10:49:27.177003+00:00, newest=2026-10-06T10:49:27.177003+00:00, no-mtime-count=0, total-items=1
- batch: oldest=2026-10-06T09:51:24.341723+00:00, newest=2026-10-06T09:51:24.344687+00:00, no-mtime-count=0, total-items=3
- progress: oldest=2026-10-06T10:49:27.154864+00:00, newest=2026-10-06T11:08:14.994040+00:00, no-mtime-count=0, total-items=2
- budget: oldest=2026-10-06T09:51:24.342772+00:00, newest=2026-10-06T09:51:24.345879+00:00, no-mtime-count=0, total-items=2
- tests: oldest=2026-10-06T09:51:24.354210+00:00, newest=2026-10-06T11:08:15.016261+00:00, no-mtime-count=0, total-items=2
- contract: oldest=2026-10-06T09:51:24.337935+00:00, newest=2026-10-06T11:00:21.342435+00:00, no-mtime-count=0, total-items=2
- docs: oldest=2026-10-06T11:00:21.365275+00:00, newest=2026-10-06T11:00:21.392486+00:00, no-mtime-count=0, total-items=2
- packaging: oldest=2026-10-06T09:51:24.340474+00:00, newest=2026-10-06T09:51:24.340474+00:00, no-mtime-count=0, total-items=1
- process: oldest=2026-10-06T09:51:24.316701+00:00, newest=2026-10-06T09:51:24.316701+00:00, no-mtime-count=0, total-items=1
- parent: oldest=2026-10-06T10:24:53.222987+00:00, newest=2026-10-06T10:24:53.222987+00:00, no-mtime-count=0, total-items=1
- SDK/requirements: no-mtime-count=2, total-items=2.
Frontier: SDK request construction must be exercised, and exact state/API decisions
belong to desc/plan. No blocking unread source region identified.
Workspace-populated: true; extent: 19 items; retained session plus current full reads.

## Telemetry and self-assessment
19 items: core=11, sub=6, side=1, umbrella=1. 17 with mtime, 2 without. Boundary
discovery not fired; bounded traversal converged; no overload. Checked missed
relevance, irrelevance, overcoverage, territory binding, overload, artifact detail,
workspace/trace sync, both recency errors, interpretive overstep, purpose loss and
downstream coupling. **PROCEED.** No implementation verdict is supplied by surfacing.
