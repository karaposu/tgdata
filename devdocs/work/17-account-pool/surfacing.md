# Surfacing — #17 triage

## User Input

What parts of dev95ed4c7 does account routing/failover for existing-access groups reach? #7 stays paused.

## Traversal Trace

Artifact case; signal-first; explicit-bounded. Same-session reads/retained unchanged reviewed source, followed by recency capture at this assembly; recency is descriptive, never relevance.

| # | Region | Identifier | Relevance | Confidence | Recency |
|---|---|---|---|---|---|
| 1 | request | `#17 + confirmed scope` | core | HIGH | `{"source": "none", "value": null}` |
| 2 | process | `CONTRIBUTING.md` | umbrella | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.499934+00:00"}` |
| 3 | connection | `tgdata/connection_engine.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.527963+00:00"}` |
| 4 | facade | `tgdata/tgdata.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.548317+00:00"}` |
| 5 | health | `tgdata/health.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.529290+00:00"}` |
| 6 | budget | `tgdata/read_budget.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.532324+00:00"}` |
| 7 | budget | `tgdata/budget_client.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.527420+00:00"}` |
| 8 | source | `tgdata/batch_engine.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.525950+00:00"}` |
| 9 | source | `tgdata/message_engine.py::_entity_after_dialog_sync` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.530936+00:00"}` |
| 10 | delivery | `tgdata/sync_engine.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.547149+00:00"}` |
| 11 | delivery | `tgdata/backfill_engine.py [retained dev95]` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.524907+00:00"}` |
| 12 | delivery | `tgdata/backfill_state.py [retained dev95]` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.525642+00:00"}` |
| 13 | prior | `paused #7 HANDOFF.md` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-06T09:10:20.487171+00:00"}` |
| 14 | consumer | `ScrapeOps state/accounts.py @dc49db8` | side | HIGH | `{"source": "filesystem", "value": "2026-07-29T14:13:00.998746+00:00"}` |
| 15 | sdk | `Telethon 1.45 users.py::_call/get_me` | core | HIGH | `{"source": "filesystem", "value": "2026-10-03T09:09:32.893062+00:00"}` |
| 16 | tests | `tgdata/smoke_tests/README.md [through #18]` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-07T20:04:36.533471+00:00"}` |

## State Summary

Territory: identifiers above, dev95 plus installed SDK and explicitly named prior/consumer sources. Purpose: weigh touched contracts before design.

Coverage: request/process/connection/health/budget/source confirmed at named interfaces; facade scanned-but-shallow outside pool/health/source entry points; delivery confirmed with same-session retained reviewed code; prior/consumer confirmed for named files only; tests scanned-but-shallow. Tags aggregate directly from the trace.

Confirmed-absent: no distinct-account pool implementation in the enumerated runtime inventory; no accepted group-operation API on dev; no task-17 runtime or prior pipeline artifacts at intake. This is a bounded absence claim, not a repository-wide claim about undocumented behavior.

Concept names: ConnectionPool (structural-reference,3); HealthMonitor (structural-reference,5); authenticated identity (vocabulary,7); source prefix (vocabulary,8); acknowledgment (vocabulary,10); source attempt (vocabulary,11); drain/spread (vocabulary,14).

Recency distribution:

```json
{
  "request": {
    "newest": null,
    "oldest": null,
    "no-mtime-count": 1,
    "total-items": 1
  },
  "process": {
    "newest": "2026-10-07T20:04:36.499934+00:00",
    "oldest": "2026-10-07T20:04:36.499934+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "connection": {
    "newest": "2026-10-07T20:04:36.527963+00:00",
    "oldest": "2026-10-07T20:04:36.527963+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "facade": {
    "newest": "2026-10-07T20:04:36.548317+00:00",
    "oldest": "2026-10-07T20:04:36.548317+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "health": {
    "newest": "2026-10-07T20:04:36.529290+00:00",
    "oldest": "2026-10-07T20:04:36.529290+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "budget": {
    "newest": "2026-10-07T20:04:36.532324+00:00",
    "oldest": "2026-10-07T20:04:36.527420+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "source": {
    "newest": "2026-10-07T20:04:36.530936+00:00",
    "oldest": "2026-10-07T20:04:36.525950+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "delivery": {
    "newest": "2026-10-07T20:04:36.547149+00:00",
    "oldest": "2026-10-07T20:04:36.524907+00:00",
    "no-mtime-count": 0,
    "total-items": 3
  },
  "prior": {
    "newest": "2026-10-06T09:10:20.487171+00:00",
    "oldest": "2026-10-06T09:10:20.487171+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "consumer": {
    "newest": "2026-07-29T14:13:00.998746+00:00",
    "oldest": "2026-07-29T14:13:00.998746+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "sdk": {
    "newest": "2026-10-03T09:09:32.893062+00:00",
    "oldest": "2026-10-03T09:09:32.893062+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "tests": {
    "newest": "2026-10-07T20:04:36.533471+00:00",
    "oldest": "2026-10-07T20:04:36.533471+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  }
}
```

Frontier: same-session traverse needs actual composition probes for identity, SDK error/wait behavior, and source-reader delivery integration. Live two-account behavior remains unqualified.

Workspace-populated: {"populated": true, "populated-at": "2026-10-07T20:32:37.503513+00:00", "extent": "named interfaces plus retained unchanged delivery contracts"}

## Telemetry

Cycles: 3 (runtime, dependencies, consumer/prior boundaries). Items: 16; tags: {'core': 11, 'umbrella': 1, 'sub': 3, 'side': 1}. Boundary discovery: no (explicit). Filesystem recency: 15; none: 1. No overload or uncertain-relevance filtering. Current-resolution territory exhausted; deeper execution evidence is the named frontier. Operational and identity failure modes checked: no territory mismatch, relevance overfiltering, premature closure, content-in-artifact, or substitution of description for workspace.

**Verdict: FLAG** — sufficiently covered to weigh feature-heavy; execution guarantees need probes during traverse. Recency was captured after earlier reads, a telemetry timing limitation explicitly retained rather than fabricated.
