# Surfacing — album contract inquiry

## User Input
`_branch.md`: I1 and variants V1–V4; scope, closure evidence, retention and raw-ack compatibility. Prior artifact: ../surfacing.md. Prior workspace: same-session source reads, refreshed in the regions below.

Mode: artifact; signal-first. Explicit bounded territory: existing batch/progress/receiver/capture/budget paths, supplied consumer helper/fixtures and primary grouping/album evidence. No boundary-discovery subphase.

## Traversal Trace

| Seq | Item identifiers | Relevance | Confidence | Recency annotation |
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
| 12 | `tgdata/budget_client.py` | sub | HIGH | filesystem: 2026-10-14T10:49:01.223279+00:00 |
| 13 | `examples/daily_continuation.py` | core | HIGH | filesystem: 2026-10-14T10:49:01.214614+00:00 |
| 14 | `/Users/ns/Desktop/projects/flatmir-scrapeops/scrapeOps/engine/collapse.py` | core | HIGH | filesystem: 2026-08-13T19:11:54.659864+00:00 |
| 15 | `/Users/ns/Desktop/projects/flatmir-scrapeops/scrapeOps/tests/test_engine_smoke.py` | sub | HIGH | filesystem: 2026-10-02T09:15:43.082247+00:00 |
| 16 | `https://core.telegram.org/constructor/message` | core | HIGH | none: null |
| 17 | `https://core.telegram.org/api/files#albums-grouped-media` | core | HIGH | none: null |
| 18 | `https://core.telegram.org/constructor/inputSingleMedia` | core | HIGH | none: null |
| 19 | `https://core.telegram.org/method/messages.getWebPage` | side | HIGH | none: null |
| 20 | `Telethon1.45.0 Message constructor signature; AlbumHack and Album.build introspection` | sub | HIGH | none: null |

## State Summary

Coverage map: batch, progress and receiver confirmed by full implementation reads; facade confirmed; pool capture confirmed, unrelated pool policy not re-read; source budget seam confirmed; consumer helper confirmed and relevant test region scanned through line165; primary album documentation/signatures confirmed at the indicated sections. The introspection result is an observed API artifact without a separately materialized file, hence no mtime is assigned to that result. No relevance decision uses timestamps.

Confirmed absent in the examined wire/batch interfaces: an expected album member-count field, a batch-carried time-window identity and an authoritative global album-completion marker. No whole-vendor-API absence is claimed. Scripted fixtures remain fixtures; the current pass has made no live Telegram request.

Concept names: grouped_id [1,2,16], canonical chat ID [1], album/per-file caption [17,18], immutable observation [1], source cursor [2,4], durable pending delivery [4,9], source admission [9,12], fixed window [6,10], receiver acceptance [13], completed capture [11], logical post/caption carrier [14], bounded history [2], delayed update collection [20], album preview [19]. These are vocabulary/structural-reference identifiers only, not a selected decomposition.

Recency distribution (mechanically derived):

```json
{
  "batch": {
    "oldest": "2026-10-14T10:49:01.221770+00:00",
    "newest": "2026-10-14T10:49:01.227966+00:00",
    "total-items": 3,
    "no-mtime-count": 0
  },
  "progress": {
    "oldest": "2026-10-14T10:49:01.220605+00:00",
    "newest": "2026-10-14T10:49:01.259820+00:00",
    "total-items": 6,
    "no-mtime-count": 0
  },
  "facade": {
    "oldest": "2026-10-14T10:49:01.260288+00:00",
    "newest": "2026-10-14T10:49:01.260288+00:00",
    "total-items": 1,
    "no-mtime-count": 0
  },
  "pool": {
    "oldest": "2026-10-14T10:49:01.231148+00:00",
    "newest": "2026-10-14T10:49:01.231148+00:00",
    "total-items": 1,
    "no-mtime-count": 0
  },
  "source": {
    "oldest": "2026-10-14T10:49:01.223279+00:00",
    "newest": "2026-10-14T10:49:01.223279+00:00",
    "total-items": 1,
    "no-mtime-count": 0
  },
  "receiver": {
    "oldest": "2026-10-14T10:49:01.214614+00:00",
    "newest": "2026-10-14T10:49:01.214614+00:00",
    "total-items": 1,
    "no-mtime-count": 0
  },
  "consumer": {
    "oldest": "2026-08-13T19:11:54.659864+00:00",
    "newest": "2026-10-02T09:15:43.082247+00:00",
    "total-items": 2,
    "no-mtime-count": 0
  },
  "vendor": {
    "oldest": null,
    "newest": null,
    "total-items": 5,
    "no-mtime-count": 5
  }
}
```

Frontier: closure versus completeness, no implicit contiguity proof, retention ownership and resource bounds, replay/public-output shape, and real-source evidence for any chosen closure premise. Live source availability and shared allowance are unestablished; no account budget is reset. API preference and model/effort factual questions remain pending.

Workspace populated:true; extent:20 trace items at the recorded depth. Four variants remained in scope; no output shape was selected by this pass.

## Telemetry
Three traversal cycles (reuse core, inspect delivery edges, inspect vendor/consumer frontier);20 included items. Tags: {"core": 13, "sub": 6, "side": 1, "umbrella": 0}. File mtime15, observation/remote no-mtime5. All current-resolution regions covered; unknown live/vendor guarantees explicitly surfaced. Failure checks: missed relevance, out-of-territory expansion, lost context, thin-artifact completeness, tag desync and recency bias; none fired. No silent sampling. **PROCEED** to Sensemaking.
