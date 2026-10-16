---
model: gpt-6-astra
effort: xhigh
---
# Surfacing — #45 contract alternatives

## User Input
_branch.md: all four considered articulations of bounded, replayable history sampling across days.

## Traversal Trace
Prior-workspace/trace: triage.md plus current session's source/owner/SDK context. Relevance refreshed for all four variants; no mtime-based filtering. Additional assembly documentation, raw-record fixture helpers and SDK iterator inspected in this discipline.

| # | Region | Item | Tag/confidence | Recency annotation |
|---|---|---|---|---|
| 1 | source | `tgdata/group_activity.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.777443+00:00} |
| 2 | source | `tgdata/batch_engine.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.775374+00:00} |
| 3 | source | `tgdata/message_batch.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.780934+00:00} |
| 4 | source | `tgdata/history_window.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.779094+00:00} |
| 5 | assembly | `tgdata/album.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.773809+00:00} |
| 6 | assembly | `tgdata/photo_trails.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.782863+00:00} |
| 7 | ownership | `tgdata/group_operations.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.777795+00:00} |
| 8 | ownership | `tgdata/account_operation.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.772933+00:00} |
| 9 | ownership | `tgdata/owned_health.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.782511+00:00} |
| 10 | ownership | `tgdata/connection_engine.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.776928+00:00} |
| 11 | ownership | `tgdata/tgdata.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.808341+00:00} |
| 12 | admission | `tgdata/budget_client.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.776453+00:00} |
| 13 | admission | `tgdata/read_budget.py` | sub/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.786330+00:00} |
| 14 | admission | `tgdata/batch_heartbeat.py` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.776057+00:00} |
| 15 | compatibility | `tgdata/progress_facade.py` | sub/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.785666+00:00} |
| 16 | compatibility | `tgdata/__init__.py` | sub/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.772597+00:00} |
| 17 | fixtures | `tgdata/smoke_tests/test_34_group_access.py` | sub/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.801737+00:00} |
| 18 | fixtures | `tgdata/smoke_tests/test_46_group_activity.py` | sub/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.806461+00:00} |
| 19 | consumer | `/Users/ns/Desktop/projects/flatmir-growth/work/tg/tg_group_discovery/measure.py` | core/HIGH | {source: filesystem, value: 2026-09-30T07:44:03.629252+00:00} |
| 20 | consumer | `/Users/ns/Desktop/projects/flatmir-growth/work/tg/tg_groups_audit/how_to_search.md` | sub/HIGH | {source: filesystem, value: 2026-09-27T20:16:52+00:00} |

| 21 | assembly docs | `docs/album_assembly.md` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.760461+00:00} |
| 22 | assembly docs | `docs/photo_trails.md` | core/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.765109+00:00} |
| 23 | fixture helpers | `tgdata/smoke_tests/test_42_album_assembly.py` | sub/HIGH | {source: filesystem, value: 2026-10-16T06:49:48.804419+00:00} |
| 24 | SDK | `/Users/ns/Desktop/projects/telegram-group-scraper/.venv/lib/python3.11/site-packages/telethon/client/messages.py` | core/HIGH | {source: filesystem, value: 2026-10-03T09:09:32.892107+00:00} |
| 25 | vendor | `https://core.telegram.org/method/messages.getHistory` | core/HIGH | {source: none, value: null} |
| 26 | vendor | `https://core.telegram.org/api/offsets` | core/HIGH | {source: none, value: null} |
| 27 | vendor | `https://core.telegram.org/constructor/message` | core/HIGH | {source: none, value: null} |

## State Summary
Territory: explicit bounded source/values, album/trail units, owner/admission/liveness, source/progress compatibility and motivating consumer. Purpose: supply facts for all four sampling articulations without choosing one.
Coverage: source/assembly modules and public assembly docs confirmed at full-file resolution; ownership/admission retained from complete current-session reads; facade/factory/compatibility at relevant interface resolution; fixture34/46 complete public paths retained, fixture42 helper interface inspected only (not entire suite); SDK _MessagesIter completely read, not whole SDK distribution. Vendor history/offset/message contracts retained from same-session primary-source reads at #44; no live behavior implied. Consumer measure.py and how_to_search.md completely read.
Confirmed absent: no existing public replayable period-sampling result or algorithm. No current sampler accepting saved MessageBatch/TelegramPost observations. This is absence within the bounded territory, not a claim about all possible downstream consumers.
Concept provenance: source/window/coverage1–4, observed units5–6/21–22, ownership7–11, admission/liveness12–14, compatibility15–16, fixtures17–18/23, consumer19–20, SDK/page mechanics24–27.
Recency distribution:
- source: newest=2026-10-16T06:49:48.780934+00:00, oldest=2026-10-16T06:49:48.775374+00:00, no-mtime-count=0, total-items=4
- assembly: newest=2026-10-16T06:49:48.782863+00:00, oldest=2026-10-16T06:49:48.773809+00:00, no-mtime-count=0, total-items=2
- ownership: newest=2026-10-16T06:49:48.808341+00:00, oldest=2026-10-16T06:49:48.772933+00:00, no-mtime-count=0, total-items=5
- admission: newest=2026-10-16T06:49:48.786330+00:00, oldest=2026-10-16T06:49:48.776057+00:00, no-mtime-count=0, total-items=3
- compatibility: newest=2026-10-16T06:49:48.785666+00:00, oldest=2026-10-16T06:49:48.772597+00:00, no-mtime-count=0, total-items=2
- fixtures: newest=2026-10-16T06:49:48.806461+00:00, oldest=2026-10-16T06:49:48.801737+00:00, no-mtime-count=0, total-items=2
- consumer: newest=2026-09-30T07:44:03.629252+00:00, oldest=2026-09-27T20:16:52+00:00, no-mtime-count=0, total-items=2
- assembly docs: newest=2026-10-16T06:49:48.765109+00:00, oldest=2026-10-16T06:49:48.760461+00:00, no-mtime-count=0, total-items=2
- fixture helpers: newest=2026-10-16T06:49:48.804419+00:00, oldest=2026-10-16T06:49:48.804419+00:00, no-mtime-count=0, total-items=1
- SDK: newest=2026-10-03T09:09:32.892107+00:00, oldest=2026-10-03T09:09:32.892107+00:00, no-mtime-count=0, total-items=1
- vendor: newest=None, oldest=None, no-mtime-count=3, total-items=3

Frontiers: algorithm/distribution and shared-source abstraction are unsettled contract questions for downstream reasoning; full fixture42 test-body refresh is unnecessary for contract facts, inspect relevant tests during implementation qualification. Exclusive current live session and authoritative allowance remain unqualified; no network call to Telegram made. All uncertain relevance included.
Workspace-populated:true,2026-10-16; bounded extent above. Telemetry: artifact/signal-first, three cycles (reconfirm, assembly semantics, SDK/source evidence);27 items,20 core/7 sub;24 filesystem mtimes/3 without. No boundary-discovery or workspace-overload trigger. All named operational and identity failures checked, no interpretive output in this thin artifact. Manual structural8/8. PROCEED to Sensemaking.
