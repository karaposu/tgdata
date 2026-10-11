# Surfacing — #10 worker contract

## User Input

Surface the bounded current-dev/source/process territory relevant to all W1 variants
in `_branch.md`, retaining the same-session triage workspace as prior input.

## Traversal Trace

Artifact, signal-first, explicit-bounded. Three cycles: current library contracts;
process I/O and lifecycle references; caller/service/durable-runner edge inventory.
Prior warm reads retained at named implementations; newly loaded ownership/health/
group/facade methods confirmed in full at this scope. Mtime captured now after reads,
not used as relevance. Primary docs are references; live process behavior needs probes.

| # | Region | Identifier | Relevance | Confidence | Recency |
|---|---|---|---|---|---|
| 1 | framing | `_branch.md; articulate_simple.md` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:33:29.554413+00:00"}` |
| 2 | request | `issue10 + source-input.md; one-session-per-account constraint` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:30:57.236603+00:00"}` |
| 3 | process | `CONTRIBUTING.md §§5/6/9/12` | umbrella | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.364422+00:00"}` |
| 4 | source | `tgdata/batch_engine.py [complete retained read]; MessageBatch v1` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.383026+00:00"}` |
| 5 | ownership | `tgdata/account_operation.py [complete]; _disconnect_owned` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.382239+00:00"}` |
| 6 | ownership | `tgdata/connection_engine.py::_account_operation/_new_client/session [complete methods]` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.383931+00:00"}` |
| 7 | health | `tgdata/owned_health.py [complete]; HealthMonitor [complete retained]` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.386371+00:00"}` |
| 8 | facade | `tgdata/tgdata.py::__init__/_account_health_operation/group methods` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.400244+00:00"}` |
| 9 | groups | `tgdata/group_operations.py [complete]` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.384440+00:00"}` |
| 10 | allowance | `read_budget.py/budget_client.py; join_budget.py/join_client.py [retained reviewed]` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.386810+00:00"}` |
| 11 | sessions | `session_store.py; config/session factory [retained reviewed]` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.386967+00:00"}` |
| 12 | delivery | `sync_engine.py/sync_store.py; backfill engines [retained reviewed]` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.399622+00:00"}` |
| 13 | package | `setup.py; runtime inventory; no current worker entry point` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.381238+00:00"}` |
| 14 | tests | `test19,32–36 actual SDK/SQLite test fixtures` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.395821+00:00"}` |
| 15 | prior | `PR26 observer-cancel and descendant-close evidence at71502e5; no runtime adoption` | side | HIGH | `{"source": "none", "value": null}` |
| 16 | stdio | `https://docs.python.org/3.11/library/asyncio-subprocess.html` | core | HIGH | `{"source": "none", "value": null}` |
| 17 | loop | `https://docs.python.org/3.11/library/asyncio-eventloop.html` | core | HIGH | `{"source": "none", "value": null}` |
| 18 | signals | `https://docs.python.org/3.11/library/asyncio-runner.html` | core | HIGH | `{"source": "none", "value": null}` |
| 19 | consumer | `V1 caller subprocess / V2 service / V3 durable runner; no supplied consumer wire contract` | umbrella | MEDIUM | `{"source": "none", "value": null}` |

## State Summary

Territory: dev68f6bbd library/package and current issue context, official Python3.11
process/loop/runner references, and the explicit V1/V2/V3 alternatives. Purpose:
identify material for worker account/job/reply ownership, without choosing a design.

Coverage by region: framing/request/process/source/ownership/health/facade/groups/
allowance/sessions/package confirmed at named scope; delivery/tests retained reviewed
interfaces; prior confirmed only for named findings; stdio/loop/signals documentary
APIs confirmed, actual composition unprobed; consumer expectations remain unknown.
All aggregate relevance follows the rows; no uncertain item was excluded.

Confirmed absent in current runtime/package inventory: worker entry point, job
transport schema, HTTP authentication layer, worker-specific durable job receipts.
Existing group progress is surfaced separately, not treated as proof of a job queue.

Concept names (flat): bounded batch (structural-reference,4); account operation
(structural-reference,5); cleanup (vocabulary,5); notification (vocabulary,7);
join outcome (vocabulary,9); allowance (vocabulary,10); pending delivery (vocabulary,12);
pipe/backpressure (vocabulary,16); signal (vocabulary,18); job acceptance (vocabulary,19).

Recency distribution:

```json
{
  "framing": {
    "newest": "2026-10-11T11:33:29.554413+00:00",
    "oldest": "2026-10-11T11:33:29.554413+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "request": {
    "newest": "2026-10-11T11:30:57.236603+00:00",
    "oldest": "2026-10-11T11:30:57.236603+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "process": {
    "newest": "2026-10-11T11:26:38.364422+00:00",
    "oldest": "2026-10-11T11:26:38.364422+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "source": {
    "newest": "2026-10-11T11:26:38.383026+00:00",
    "oldest": "2026-10-11T11:26:38.383026+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "ownership": {
    "newest": "2026-10-11T11:26:38.383931+00:00",
    "oldest": "2026-10-11T11:26:38.382239+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "health": {
    "newest": "2026-10-11T11:26:38.386371+00:00",
    "oldest": "2026-10-11T11:26:38.386371+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "facade": {
    "newest": "2026-10-11T11:26:38.400244+00:00",
    "oldest": "2026-10-11T11:26:38.400244+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "groups": {
    "newest": "2026-10-11T11:26:38.384440+00:00",
    "oldest": "2026-10-11T11:26:38.384440+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "allowance": {
    "newest": "2026-10-11T11:26:38.386810+00:00",
    "oldest": "2026-10-11T11:26:38.386810+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "sessions": {
    "newest": "2026-10-11T11:26:38.386967+00:00",
    "oldest": "2026-10-11T11:26:38.386967+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "delivery": {
    "newest": "2026-10-11T11:26:38.399622+00:00",
    "oldest": "2026-10-11T11:26:38.399622+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "package": {
    "newest": "2026-10-11T11:26:38.381238+00:00",
    "oldest": "2026-10-11T11:26:38.381238+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "tests": {
    "newest": "2026-10-11T11:26:38.395821+00:00",
    "oldest": "2026-10-11T11:26:38.395821+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "prior": {
    "newest": null,
    "oldest": null,
    "no-mtime-count": 1,
    "total-items": 1
  },
  "stdio": {
    "newest": null,
    "oldest": null,
    "no-mtime-count": 1,
    "total-items": 1
  },
  "loop": {
    "newest": null,
    "oldest": null,
    "no-mtime-count": 1,
    "total-items": 1
  },
  "signals": {
    "newest": null,
    "oldest": null,
    "no-mtime-count": 1,
    "total-items": 1
  },
  "consumer": {
    "newest": null,
    "oldest": null,
    "no-mtime-count": 1,
    "total-items": 1
  }
}
```

Frontier: actual pipe EOF/framing/backpressure and signal behavior; post-cleanup
notification scheduling; the meaning of a completed cleanup attempt; lost reply
versus job admission; transport choice and strict JSON projection. These are named
questions for subsequent disciplines/probes, not conclusions disguised as inventory.

Workspace-populated: {"populated": true, "populated-at": "2026-10-11T11:38:31.001741+00:00", "extent": "named interfaces, retained reviewed contracts, new official process references"}

## Telemetry

Three cycles; 19 items; tags {'core': 14, 'sub': 2, 'side': 1, 'umbrella': 2}; 14 filesystem mtimes, five without.
Boundary discovery not fired. Current-resolution traversal complete; behavioral
frontiers explicit, no overload/filtering. Checked territory/purpose binding,
missed relevance, irrelevant overcoverage, artifact/workspace desync, underspecification,
recency bias and interpretive overstep. No hidden variant pruning.

**Verdict: FLAG.** Structural output complete; process and lifecycle behavior must
be probed before the inquiry chooses a contract. This is not an implementation plan.
