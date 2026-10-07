---
model: gpt-6-astra
effort: max
---
# Surfacing — Stage 3 exact delivery

## User Input
Implement Stage 3 of #19 in this folder; surface the settled lifecycle, source, storage, media and failure boundaries before describing it.

## Reception
Artifact; signal-first; explicitly bounded territory: the listed #19 contracts, existing runtime interfaces and their tests at 8023adf. Retained same-session full-source/Gate A workspace, with fresh whole-file reads of lifecycle, CAS, raw batch/media, health and budget code. Boundary discovery not needed.

## Traversal Trace
| # | Region | Item | Tag | Confidence | Recency annotation |
|---|---|---|---|---|---|
| 1 | Authority | issue #19 / user Stage 3 request | core | HIGH | `{"source": "none", "value": null}` |
| 2 | Authority | contract.md | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T06:30:39.353145+00:00"}` |
| 3 | Authority | staged-plan.md (Stages 3–5 / gates) | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T06:30:39.460521+00:00"}` |
| 4 | Authority | assumptions.md | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T06:31:48.490217+00:00"}` |
| 5 | Authority | acceptance-matrix.md | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T06:31:48.465816+00:00"}` |
| 6 | Authority | validation/gate-a.md | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T06:27:26.338369+00:00"}` |
| 7 | Lifecycle | backfill.py | core | HIGH | `{"source": "filesystem", "value": "2026-10-06T21:49:25.278462+00:00"}` |
| 8 | Lifecycle | backfill_state.py | core | HIGH | `{"source": "filesystem", "value": "2026-10-06T21:35:24.398043+00:00"}` |
| 9 | Lifecycle | backfill_engine.py | core | HIGH | `{"source": "filesystem", "value": "2026-10-06T21:37:59.844423+00:00"}` |
| 10 | Storage | sync_store.py | core | HIGH | `{"source": "filesystem", "value": "2026-10-06T21:48:10.031723+00:00"}` |
| 11 | Storage | sync_engine.py | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T21:00:55.057913+00:00"}` |
| 12 | Observation | message_batch.py | core | HIGH | `{"source": "filesystem", "value": "2026-10-06T20:06:01.801156+00:00"}` |
| 13 | Observation | batch_engine.py | core | HIGH | `{"source": "filesystem", "value": "2026-10-06T21:00:55.055420+00:00"}` |
| 14 | Observation | batch_files.py | core | HIGH | `{"source": "filesystem", "value": "2026-10-06T20:06:01.799735+00:00"}` |
| 15 | Observation | history_window.py | core | HIGH | `{"source": "filesystem", "value": "2026-10-06T21:00:55.055816+00:00"}` |
| 16 | Provenance | health.py | core | HIGH | `{"source": "filesystem", "value": "2026-10-06T20:06:01.800950+00:00"}` |
| 17 | Provenance | read_budget.py | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T20:06:01.802255+00:00"}` |
| 18 | Provenance | budget_client.py | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T20:06:01.800022+00:00"}` |
| 19 | Provenance | tgdata.py (retained whole-file context / source entry refresh) | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T21:00:55.059357+00:00"}` |
| 20 | Evidence | test_24_backfill_state.py | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T22:20:36.301630+00:00"}` |
| 21 | Evidence | test_22_daily_continuation.py | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T21:00:55.057118+00:00"}` |
| 22 | Evidence | test_19_message_batches.py | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T20:06:01.811618+00:00"}` |
| 23 | Boundary | CONTRIBUTING.md | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T20:06:01.779665+00:00"}` |
| 24 | Boundary | docs/backfill_state.md | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T22:10:01.866535+00:00"}` |

## State Summary
Purpose: draw the items bearing on durable one-batch preparation/replay/ack into current attention. Territory echo: the 24 identifiers above. Six cycles (authority, lifecycle/storage, observation, provenance, evidence, boundary); all listed regions confirmed at required implementation/interface resolution. No uncertain relevance was excluded.

Confirmed absent: Stage 3 runtime prepare/ack methods, Stage 3 artifacts/rejection history, public backfill facade, controls/recovery operations. Future timing/control operations remain an explicit boundary, not missing coverage disguised as absence.

Concept/provenance index: fixed intent / scoped authority (1–9); conditional durable mutation (10–11); canonical observation / artifact integrity (12–15); error causality / verified source accounting (16–19); actual state, media and regression receipts (20–22); formal scope / supported staged interface (23–24).

Workspace-populated: true; populated-at 2026-10-07T07:21:16.147714+00:00; extent: complete listed runtime sources plus retained facade and full contract/evidence context. Frontier: implementation ordering across already-defined end/timing invariants goes to planning; no uncovered dependency region.

## Recency Distribution
- Authority: newest=2026-10-07T06:31:48.490217+00:00; oldest=2026-10-07T06:27:26.338369+00:00; no-mtime-count=1; total-items=6.
- Lifecycle: newest=2026-10-06T21:49:25.278462+00:00; oldest=2026-10-06T21:35:24.398043+00:00; no-mtime-count=0; total-items=3.
- Storage: newest=2026-10-06T21:48:10.031723+00:00; oldest=2026-10-06T21:00:55.057913+00:00; no-mtime-count=0; total-items=2.
- Observation: newest=2026-10-06T21:00:55.055816+00:00; oldest=2026-10-06T20:06:01.799735+00:00; no-mtime-count=0; total-items=4.
- Provenance: newest=2026-10-06T21:00:55.059357+00:00; oldest=2026-10-06T20:06:01.800022+00:00; no-mtime-count=0; total-items=4.
- Evidence: newest=2026-10-06T22:20:36.301630+00:00; oldest=2026-10-06T20:06:01.811618+00:00; no-mtime-count=0; total-items=3.
- Boundary: newest=2026-10-06T22:10:01.866535+00:00; oldest=2026-10-06T20:06:01.779665+00:00; no-mtime-count=0; total-items=2.

## Telemetry and Verdict
24 items: 15 core and 9 sub; 23 filesystem annotations and one external sentinel. Six cycles, no discovery sub-phase, no workspace-overload exclusion. Coverage, confidence/tag consistency, edge items, absence claims, recency neutrality and operational/identity failure modes checked. **PROCEED**.
