# Surfacing — unresolved source boundaries

## User Input

_branch.md, iteration2 focus from _state.md: account admission/settlement and timeout-prefix ownership.

## Traversal Trace

Artifact, signal-first, explicit-bounded; prior workspace and surfacing_iter1.md retained. Two cycles: admission/CAS, then cancellation/delivery. Recency captured at enumeration; not used as relevance.

| # | Region | Identifier | Tag | Confidence | Recency source | UTC value |
|---|---|---|---|---|---|---|
| 1 | critique | `critique_iter1.md` | core | HIGH | filesystem | 2026-10-07T20:53:08.682598+00:00 |
| 2 | admission | `BackfillEngine._admit/_settle` | core | HIGH | filesystem | 2026-10-07T20:04:36.524907+00:00 |
| 3 | storage | `SQLiteSyncStore.load/CAS` | core | HIGH | filesystem | 2026-10-07T20:04:36.547707+00:00 |
| 4 | cancellation | `BatchEngine.fetch_batch exception boundary` | core | HIGH | filesystem | 2026-10-07T20:04:36.525950+00:00 |
| 5 | cancellation | `asyncio.wait_for Python3.11` | core | HIGH | filesystem | 2024-10-03T07:33:18.791598+00:00 |
| 6 | delivery | `SyncEngine.prepare prefix publication` | sub | HIGH | filesystem | 2026-10-07T20:04:36.547149+00:00 |

## State Summary

Territory/purpose as above. Coverage: all named methods and prior critique confirmed; no claim about the rest of asyncio. Confirmed-absent: an account attempt journal in current pool code (no pool code exists); cancellation branch retaining records in current BatchEngine.

Concept names: unsettled attempt/vocabulary/2; exact CAS/structural-reference/3; CancelledError/vocabulary/4; timeout cause/vocabulary/5; pending prefix/vocabulary/6.

Recency distribution:
```json
{
  "critique": {
    "oldest": "2026-10-07T20:53:08.682598+00:00",
    "newest": "2026-10-07T20:53:08.682598+00:00",
    "total_items": 1,
    "no_mtime_count": 0
  },
  "admission": {
    "oldest": "2026-10-07T20:04:36.524907+00:00",
    "newest": "2026-10-07T20:04:36.524907+00:00",
    "total_items": 1,
    "no_mtime_count": 0
  },
  "storage": {
    "oldest": "2026-10-07T20:04:36.547707+00:00",
    "newest": "2026-10-07T20:04:36.547707+00:00",
    "total_items": 1,
    "no_mtime_count": 0
  },
  "cancellation": {
    "oldest": "2024-10-03T07:33:18.791598+00:00",
    "newest": "2026-10-07T20:04:36.525950+00:00",
    "total_items": 2,
    "no_mtime_count": 0
  },
  "delivery": {
    "oldest": "2026-10-07T20:04:36.547149+00:00",
    "newest": "2026-10-07T20:04:36.547149+00:00",
    "total_items": 1,
    "no_mtime_count": 0
  }
}
```

Frontier: exercise prefix retention at the exact real BatchEngine exception seam and SQLite admission across reconstruction; no further unrelated source territory required. Workspace-populated: true at 2026-10-07T20:55:30.369183+00:00, six named interfaces.

## Telemetry

6 items, core5/sub1, filesystem6/none0; two cycles; boundary discovery/overload no. Current resolution exhausted; no uncertain item excluded. Failure modes1–9 and identity modes checked; no content copied into trace, interpretation or metadata-driven filtering. **Verdict: PROCEED**.
