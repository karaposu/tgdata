# Surfacing — ownership and delivery territory

## User Input

_branch.md, all four considered articulations. Draw evidence relevant to distinct-account ownership, bounded attempts, routing state and daily/backfill integration.

## Traversal Trace

Artifact; signal-first; explicitly bounded to current dev interfaces, their contracts/tests, installed Telethon1.45 and named historical/consumer inputs. Re-invocation uses ../surfacing.md plus same-session workspace; this pass changes the purpose from weight to meaning.

| # | Region | Item identifier | Tag | Confidence | Recency |
|---|---|---|---|---|---|
| 1 | ownership | `tgdata/connection_engine.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.527963+00:00"}` |
| 2 | ownership | `tgdata/tgdata.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.548317+00:00"}` |
| 3 | ownership | `tgdata/health.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.529290+00:00"}` |
| 4 | admission | `tgdata/read_budget.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.532324+00:00"}` |
| 5 | admission | `tgdata/budget_client.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.527420+00:00"}` |
| 6 | source | `tgdata/batch_engine.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.525950+00:00"}` |
| 7 | source | `tgdata/message_engine.py` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.530936+00:00"}` |
| 8 | delivery | `tgdata/sync_engine.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.547149+00:00"}` |
| 9 | delivery | `tgdata/backfill_engine.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.524907+00:00"}` |
| 10 | delivery | `docs/backfill_runs.md` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.518067+00:00"}` |
| 11 | delivery | `docs/daily_continuation.md` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.519347+00:00"}` |
| 12 | verification | `tgdata/smoke_tests/test_18_read_budget.py` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.540731+00:00"}` |
| 13 | verification | `tgdata/smoke_tests/test_16_health_events.py` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.540150+00:00"}` |
| 14 | verification | `tgdata/smoke_tests/test_30_backfill_integration.py` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.545803+00:00"}` |
| 15 | prior | `paused7/HANDOFF.md` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T09:10:20.487171+00:00"}` |
| 16 | consumer | `ScrapeOps/accounts.py@dc49db8` | side | HIGH | `{"source": "filesystem", "value": "2026-07-29T14:13:00.998746+00:00"}` |
| 17 | sdk | `Telethon1.45/users.py::_call,get_me` | core | HIGH | `{"source": "filesystem", "value": "2026-10-03T09:09:32.893062+00:00"}` |
| 18 | request | `confirmed existing-access scope + branch variants` | umbrella | HIGH | `{"source": "none", "value": null}` |

## State Summary

Purpose/territory: as above; openness: bounded reader, integrated reader, durable controller, process-scoped learned access.

Coverage map: ownership/admission/source/delivery core interfaces confirmed (same-session code reads; current budget and batch paths re-read); verification sub, scanned-but-shallow helpers and summaries; prior sub confirmed HANDOFF only; consumer side confirmed accounts.py only; SDK core confirmed named methods only; request umbrella confirmed. Wider docs/test bodies intentionally not claimed fully read.

Confirmed-absent: pool-of-distinct-accounts API in current runtime inventory; accepted #7 implementation on dev; multi-account qualification in #19 live evidence. No absence asserted for unread consumer code.

Concept names (name/type/provenance): authenticated principal/vocabulary/1; HealthMonitor/structural-reference/3; reservation/vocabulary/5; partial_result/vocabulary/6; SyncEngine/structural-reference/8; BackfillEngine/structural-reference/9; account-visible history/vocabulary/11; scripted sender/vocabulary/12; cached self identity/vocabulary/17; persistent routing/vocabulary/18.

Recency distribution (derived; never a relevance filter):

```json
{
  "ownership": {
    "newest": "2026-10-07T20:04:36.548317+00:00",
    "oldest": "2026-10-07T20:04:36.527963+00:00",
    "total_items": 3,
    "no_mtime_count": 0
  },
  "admission": {
    "newest": "2026-10-07T20:04:36.532324+00:00",
    "oldest": "2026-10-07T20:04:36.527420+00:00",
    "total_items": 2,
    "no_mtime_count": 0
  },
  "source": {
    "newest": "2026-10-07T20:04:36.530936+00:00",
    "oldest": "2026-10-07T20:04:36.525950+00:00",
    "total_items": 2,
    "no_mtime_count": 0
  },
  "delivery": {
    "newest": "2026-10-07T20:04:36.547149+00:00",
    "oldest": "2026-10-07T20:04:36.518067+00:00",
    "total_items": 4,
    "no_mtime_count": 0
  },
  "verification": {
    "newest": "2026-10-07T20:04:36.545803+00:00",
    "oldest": "2026-10-07T20:04:36.540150+00:00",
    "total_items": 3,
    "no_mtime_count": 0
  },
  "prior": {
    "newest": "2026-10-06T09:10:20.487171+00:00",
    "oldest": "2026-10-06T09:10:20.487171+00:00",
    "total_items": 1,
    "no_mtime_count": 0
  },
  "consumer": {
    "newest": "2026-07-29T14:13:00.998746+00:00",
    "oldest": "2026-07-29T14:13:00.998746+00:00",
    "total_items": 1,
    "no_mtime_count": 0
  },
  "sdk": {
    "newest": "2026-10-03T09:09:32.893062+00:00",
    "oldest": "2026-10-03T09:09:32.893062+00:00",
    "total_items": 1,
    "no_mtime_count": 0
  },
  "request": {
    "newest": null,
    "oldest": null,
    "total_items": 1,
    "no_mtime_count": 1
  }
}
```

Frontier: actual dev composition probes for stale cached identity, exhausted SDK failures, authentication waits, and a changing reader underneath durable replay. Coverage qualification across real accounts remains unknown.

Workspace-populated: {"populated": true, "populated_at": "2026-10-07T20:35:48.767957+00:00", "extent": "named contracts/interfaces and explicitly shallow verification helpers"}

## Telemetry

Cycles: 3 (source ownership/admission, durable delivery, evidence limits). Enumerated 18; relevance {'core': 11, 'sub': 5, 'side': 1, 'umbrella': 1}; filesystem17/none1. Boundary discovery: no. No overload, metadata filter or uncertain rejection. All bounded regions reached at declared resolution. Failure modes 1–9 plus identity modes checked; no interpretation/selection in this thin trace.

**Verdict: PROCEED** — surfaced frontier is passed to Sensemaking; the trace makes no runtime guarantee.
