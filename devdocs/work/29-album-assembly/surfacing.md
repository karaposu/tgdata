# Surfacing — album task triage

## User Input
What parts of the current tgdata codebase and supplied ScrapeOps behavior does issue #29 actually touch? Input request is preserved in source-input.md.

Mode: artifact. Entry: signal-first. Territory: the current raw-batch/receiver/progress paths, supplied collapse reference, relevant SDK grouping evidence and adjacent backlog boundaries. Explicit bounded; no boundary-discovery subphase.

## Traversal Trace

| Seq | Item identifier | Relevance | Confidence | Recency annotation |
|---|---|---|---|---|
| 1 | `tgdata/message_batch.py` | core | HIGH | filesystem: 2026-10-14T10:49:01.227966+00:00 |
| 2 | `tgdata/batch_engine.py` | core | HIGH | filesystem: 2026-10-14T10:49:01.221770+00:00 |
| 3 | `tgdata/batch_files.py` | sub | HIGH | filesystem: 2026-10-14T10:49:01.222303+00:00 |
| 4 | `tgdata/sync_engine.py` | core | HIGH | filesystem: 2026-10-14T10:49:01.259426+00:00 |
| 5 | `tgdata/sync_store.py` | core | HIGH | filesystem: 2026-10-14T10:49:01.259820+00:00 |
| 6 | `tgdata/history_window.py` | core | HIGH | filesystem: 2026-10-14T10:49:01.226004+00:00 |
| 7 | `tgdata/progress_facade.py` | core | HIGH | filesystem: 2026-10-14T10:49:01.232941+00:00 |
| 8 | `tgdata/tgdata.py` | sub | HIGH | filesystem: 2026-10-14T10:49:01.260288+00:00 |
| 9 | `tgdata/backfill_engine.py` | core | HIGH | filesystem: 2026-10-14T10:49:01.220605+00:00 |
| 10 | `tgdata/backfill_state.py` | core | HIGH | filesystem: 2026-10-14T10:49:01.221229+00:00 |
| 11 | `tgdata/pool_result.py` | sub | HIGH | filesystem: 2026-10-14T10:49:01.231148+00:00 |
| 12 | `tgdata/pool_observation.py` | side | HIGH | filesystem: 2026-10-14T10:49:01.230645+00:00 |
| 13 | `examples/daily_continuation.py` | core | HIGH | filesystem: 2026-10-14T10:49:01.214614+00:00 |
| 14 | `/Users/ns/Desktop/projects/flatmir-scrapeops/scrapeOps/engine/collapse.py` | core | HIGH | filesystem: 2026-08-13T19:11:54.659864+00:00 |
| 15 | `/Users/ns/Desktop/projects/flatmir-scrapeops/scrapeOps/tests/test_engine_smoke.py` | sub | HIGH | filesystem: 2026-10-02T09:15:43.082247+00:00 |
| 16 | `/Users/ns/Desktop/projects/telegram-group-scraper/.venv/lib/python3.11/site-packages/telethon/events/album.py`: AlbumHack, Album.build | sub | HIGH | filesystem: 2026-10-03T09:09:32.896134+00:00 |
| 17 | https://core.telegram.org/constructor/message | core | HIGH | none: null |
| 18 | Issue #30 photo-trail scope | side | HIGH | none: null |
| 19 | Issue #31 lease scope | side | HIGH | none: null |

## State Summary

Purpose: surface the scope and delicacy before choosing a design. Coverage: core batch/progress/receiver implementations confirmed; facade and pool capture confirmed; ScrapeOps helper confirmed and relevant tests read through line165; live Telegram membership completeness unknown. Remote docs/current SDK inspected at the grouping-field/event boundary. Confirmed absent in the traversed batch schema: expected album-member count and authoritative album-complete field. No global claim about the whole vendor API is made.

Concept names with provenance: raw observation/hash [1], grouped_id [1,2,17], completed prefix [2,11], blob custody [3], pending delivery [4,5,9,10], fixed window [6], explicit acknowledgment [7,13], caller data capture [11], logical post/caption carrier [14], delayed album event [16]. Types: vocabulary for platform/library names; structural-reference for receiver/retention seams. No invented output API is selected here.

Recency distribution: filesystem annotations cover 16 items; three items use none/null. Source checkout files share the new-worktree materialization time; annotations are provenance only and were not used for relevance. Min/max timestamps are available directly in the trace. All 19 items were included; no uncertain item was filtered out.

Frontier: source-completeness guarantees, assembly closure policy, bounded retention, output/replay contract, and the real existing-account fixture for later qualification. These are inquiry work, not completed evidence. Workspace populated: true at 2026-10-14T10:58:36.557338+00:00; relevant implementations loaded. No unseen file is claimed read.

## Telemetry and self-assessment
Three regions traversed (tgdata core/consumer reference/source evidence); 19 items: 11 core, 5 sub, 3 side, 0 umbrella. Filesystem-backed 16, no-mtime 3. Current-resolution scope converged; live completeness remains explicitly unknown. Checked missed relevance, territory misbinding, workspace overload, artifact under-specification, tag drift and recency bias. No silent sampling or metadata relevance filter. **PROCEED** to triage/traverse; no implementation decision follows from this relevance inventory.
