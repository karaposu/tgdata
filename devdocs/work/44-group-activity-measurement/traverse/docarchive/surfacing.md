---
model: gpt-6-astra
effort: xhigh
---
# Surfacing — #44 contract

## User Input
_branch.md: all three considered articulations of bounded window measurement.

## Traversal Trace
| # | Region | Item | Tag/confidence | Recency annotation |
|---|---|---|---|---|
| 1 | source | `tgdata/batch_engine.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.365537+00:00} |
| 2 | source | `tgdata/history_window.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.371133+00:00} |
| 3 | source | `tgdata/message_batch.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.372860+00:00} |
| 4 | ownership | `tgdata/tgdata.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.399647+00:00} |
| 5 | ownership | `tgdata/group_operations.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.370087+00:00} |
| 6 | ownership | `tgdata/account_operation.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.363148+00:00} |
| 7 | ownership | `tgdata/connection_engine.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.369221+00:00} |
| 8 | ownership | `tgdata/owned_health.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.373933+00:00} |
| 9 | ownership | `tgdata/health.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.370886+00:00} |
| 10 | admission | `tgdata/budget_client.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.368536+00:00} |
| 11 | admission | `tgdata/read_budget.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.377270+00:00} |
| 12 | admission | `tgdata/batch_heartbeat.py` | core/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.368011+00:00} |
| 13 | compatibility | `tgdata/group_profile.py` | sub/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.370497+00:00} |
| 14 | compatibility | `tgdata/album.py` | sub/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.363897+00:00} |
| 15 | compatibility | `tgdata/progress_facade.py` | sub/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.376927+00:00} |
| 16 | compatibility | `tgdata/utils.py` | sub/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.399923+00:00} |
| 17 | compatibility | `tgdata/__init__.py` | sub/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.362884+00:00} |
| 18 | fixtures | `tgdata/smoke_tests/test_23_fixed_windows.py` | sub/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.387225+00:00} |
| 19 | fixtures | `tgdata/smoke_tests/test_32_account_operation.py` | sub/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.391020+00:00} |
| 20 | fixtures | `tgdata/smoke_tests/test_33_owned_health.py` | sub/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.391345+00:00} |
| 21 | fixtures | `tgdata/smoke_tests/test_34_group_access.py` | sub/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.391744+00:00} |
| 22 | fixtures | `tgdata/smoke_tests/test_45_group_profile.py` | sub/HIGH | {source: filesystem, value: 2026-10-15T19:49:10.397179+00:00} |
| 23 | SDK | `telethon/client/messages.py` | core/HIGH | {source: filesystem, value: 2026-10-03T09:09:32.892107+00:00} |
| 24 | SDK | `telethon/tl/types/__init__.py` | sub/HIGH | {source: filesystem, value: 2026-10-03T09:09:32.917819+00:00} |
| 25 | vendor | `https://core.telegram.org/method/messages.getHistory` | core/HIGH | {source: none, value: null} |
| 26 | vendor | `https://core.telegram.org/api/offsets` | core/HIGH | {source: none, value: null} |
| 27 | vendor | `https://core.telegram.org/constructor/messageReactions` | core/HIGH | {source: none, value: null} |
| 28 | vendor | `https://core.telegram.org/constructor/message` | core/HIGH | {source: none, value: null} |
| 29 | consumer | `/Users/ns/Desktop/projects/flatmir-growth/work/tg/tg_group_discovery/measure.py` | sub/HIGH | {source: filesystem, value: 2026-09-30T07:44:03.629252+00:00} |

## State Summary
Purpose: expose evidence-bearing source/value/admission/counter boundaries for every articulation, without selecting a design. Territory: bounded source and owned-operation contracts, compatibility interfaces, actual SDK message iterator/counter types, direct vendor contracts and motivating consumer.
Coverage: source/ownership/admission confirmed at complete module resolution; compatibility confirmed at value/facade resolution; fixtures23/32/33/34/45 confirmed at public-path suite resolution; SDK iterator and relevant constructors confirmed (not the entire generated TL types file); four vendor pages confirmed at relevant contract fields; consumer measure.py confirmed.
Confirmed absent: no existing versioned engagement observation or explicit per-page measurement coverage in this bounded surface. No UI/business classifier/store migration is part of the requested library change.
Concept provenance: bounded records/date-window (1–3); account ownership and semantic health (4–9); charged source slots/liveness (10–12); reusable raw values versus views/progress (13–17); real SDK evidence (18–24); source order and optional counters (25–28); consumer assumptions (29).
Recency distributions (descriptive only):
- source: newest=2026-10-15T19:49:10.372860+00:00, oldest=2026-10-15T19:49:10.365537+00:00, no-mtime-count=0, total-items=3
- ownership: newest=2026-10-15T19:49:10.399647+00:00, oldest=2026-10-15T19:49:10.363148+00:00, no-mtime-count=0, total-items=6
- admission: newest=2026-10-15T19:49:10.377270+00:00, oldest=2026-10-15T19:49:10.368011+00:00, no-mtime-count=0, total-items=3
- compatibility: newest=2026-10-15T19:49:10.399923+00:00, oldest=2026-10-15T19:49:10.362884+00:00, no-mtime-count=0, total-items=5
- fixtures: newest=2026-10-15T19:49:10.397179+00:00, oldest=2026-10-15T19:49:10.387225+00:00, no-mtime-count=0, total-items=5
- SDK: newest=2026-10-03T09:09:32.917819+00:00, oldest=2026-10-03T09:09:32.892107+00:00, no-mtime-count=0, total-items=2
- vendor: newest=None, oldest=None, no-mtime-count=4, total-items=4
- consumer: newest=2026-09-30T07:44:03.629252+00:00, oldest=2026-09-30T07:44:03.629252+00:00, no-mtime-count=0, total-items=1

Frontier: actual live account/session exclusivity and authoritative allowance are not yet qualified. Local session filenames exist but do not themselves authorize or establish a live run. No live request was made. Source ordering/counter types have vendor documentation and local codec evidence, not universal empirical coverage.
Workspace populated:true,2026-10-15, runtime contracts/SDK iterator and relevant packet types retained/refreshed in this session. No source content is copied into this thin artifact.
Telemetry: artifact/signal-first;3 cycles (source, composition, external/consumer);29 items,17 core/12 sub/0 side/0 umbrella;25 with filesystem mtime/4 without. Explicit bounded territory; no boundary-discovery subphase.
Failure modes checked: missing/irrelevant/overcoverage, territory binding, workspace overload, artifact underspecification/desync, recency conflation/filtering and interpretive overstep. No uncertain item excluded. Substantive live frontier preserved; downstream must not convert it into a live PASS.
Manual structural check: trace, per-item tags/confidence/mtime, coverage, concept provenance, recency aggregation, frontier, populated status and telemetry present (8/8). tools/structural_check.sh absent.
Self-assessment: PROCEED for contract inquiry; live qualification remains a named frontier.
