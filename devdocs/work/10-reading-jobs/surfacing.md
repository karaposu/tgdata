---
model: gpt-6-astra
effort: max
---
# Surfacing — #10 triage

## User Input

What current-dev interfaces and process boundaries does issue10's small reading-job
worker touch? Save this triage pass to devdocs/work/10-reading-jobs/surfacing.md.

## Traversal Trace

Artifact case, signal-first, explicit-bounded: dev68f6bbd, issue10, merged operation
contracts and adjacent interpreter process-I/O behavior. Same-session prior source
workspace is retained where indicated; no content is reproduced in this thin trace.
Recency captured at this assembly after the warm refresh, not used as relevance.

| # | Region | Identifier | Relevance | Confidence | Recency |
|---|---|---|---|---|---|
| 1 | request | `#10 original request / current user authorization` | core | HIGH | `{"source": "none", "value": null}` |
| 2 | process | `CONTRIBUTING.md §§4–7/9/12` | umbrella | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.364422+00:00"}` |
| 3 | prerequisites | `#4/#6/#7 CLOSED; dev68f6bbd; no #10 linked branch at intake` | core | HIGH | `{"source": "none", "value": null}` |
| 4 | inventory | `tgdata/ runtime inventory; setup.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.381238+00:00"}` |
| 5 | facade | `tgdata/tgdata.py::__init__,_account_health_operation,lookup_group,check_group_access,join_group` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.400244+00:00"}` |
| 6 | ownership | `tgdata/account_operation.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.382239+00:00"}` |
| 7 | ownership | `tgdata/connection_engine.py::_new_client,_account_operation,session` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.383931+00:00"}` |
| 8 | health | `tgdata/owned_health.py; tgdata/health.py [same-session full read]` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.386371+00:00"}` |
| 9 | source | `tgdata/batch_engine.py; tgdata/message_batch.py [retained reviewed format]` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.383026+00:00"}` |
| 10 | groups | `tgdata/group_operations.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.384440+00:00"}` |
| 11 | budgets | `tgdata/budget_client.py; read_budget.py; join_budget.py; join_client.py [retained reviewed contracts]` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.383501+00:00"}` |
| 12 | storage | `tgdata/session_store.py; sync_store.py [retained reviewed contracts]` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.386967+00:00"}` |
| 13 | contracts | `docs/account_operations.md; docs/group_operations.md; docs/group_joining.md` | core | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.377307+00:00"}` |
| 14 | tests | `tgdata/smoke_tests/test_19_message_batches.py and test_32–36; fixtures and offline boundaries` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-11T11:26:38.395821+00:00"}` |
| 15 | prior | `#17 PR26 fresh observer/cleanup findings; explicit excluded runtime dependency` | side | HIGH | `{"source": "none", "value": null}` |
| 16 | process_io | `CPython asyncio subprocess, pipe framing, signals and output backpressure` | core | MEDIUM | `{"source": "none", "value": null}` |
| 17 | consumer | `Laptop/server worker integration; no downstream consumer protocol supplied` | umbrella | MEDIUM | `{"source": "none", "value": null}` |

## State Summary

Purpose: weigh and locate the worker's integration/ownership contract before design.
Coverage: request/process/prerequisites/inventory confirmed; facade at named methods,
ownership, health and group module confirmed; source/budgets/storage retain reviewed
interfaces from the same session; consumer unspecified; process-I/O scanned-but-shallow
and requires execution probes. Tests identified, full new-worker coverage absent.

Confirmed absent: no worker module/entrypoint or task10 artifacts in current dev's
runtime/work inventory; no existing #10 linked branch at intake. These are bounded
inventory claims, not claims that no downstream application implements a worker.

Concept names: account operation (structural-reference,6); ownership (vocabulary,7);
health notification (vocabulary,8); raw batch (vocabulary,9); group join (vocabulary,10);
allowance (vocabulary,11); job (vocabulary,1); framing (vocabulary,16).

Recency distribution (descriptive only):

```json
{
  "request": {
    "newest": null,
    "oldest": null,
    "no-mtime-count": 1,
    "total-items": 1
  },
  "process": {
    "newest": "2026-10-11T11:26:38.364422+00:00",
    "oldest": "2026-10-11T11:26:38.364422+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "prerequisites": {
    "newest": null,
    "oldest": null,
    "no-mtime-count": 1,
    "total-items": 1
  },
  "inventory": {
    "newest": "2026-10-11T11:26:38.381238+00:00",
    "oldest": "2026-10-11T11:26:38.381238+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "facade": {
    "newest": "2026-10-11T11:26:38.400244+00:00",
    "oldest": "2026-10-11T11:26:38.400244+00:00",
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
  "source": {
    "newest": "2026-10-11T11:26:38.383026+00:00",
    "oldest": "2026-10-11T11:26:38.383026+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "groups": {
    "newest": "2026-10-11T11:26:38.384440+00:00",
    "oldest": "2026-10-11T11:26:38.384440+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "budgets": {
    "newest": "2026-10-11T11:26:38.383501+00:00",
    "oldest": "2026-10-11T11:26:38.383501+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "storage": {
    "newest": "2026-10-11T11:26:38.386967+00:00",
    "oldest": "2026-10-11T11:26:38.386967+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "contracts": {
    "newest": "2026-10-11T11:26:38.377307+00:00",
    "oldest": "2026-10-11T11:26:38.377307+00:00",
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
  "process_io": {
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

Frontier: process transport/framing, response-loss and join retry meaning, account
configuration/one-session ownership, cleanup failure and worker continuation,
notification collection, real pipe/EOF/backpressure/signal behavior. These are
questions for traverse, not selected designs or invented execution blockers.

Workspace-populated: {"populated": true, "populated-at": "2026-10-11T11:29:38.489480+00:00", "extent": "named interfaces plus retained same-session reviewed boundaries"}

## Telemetry

Three cycles (request/process; runtime contracts; external/process edge inventory),
17 items: core12, sub2, side1, umbrella2; 12 with filesystem mtime, five without.
Boundary discovery not fired. No uncertain
item excluded; no recency filtering. Workspace overload not fired. At current
triage resolution the territory is exhausted; process behavior remains explicit
frontier. Layer1 checked: missed relevance, irrelevant/overcoverage, territory binding,
workspace overload, artifact underspecification/desync and both recency failures.
Layer2 checked: interpretive overstep, purpose loss, downstream self-coupling.

**Verdict: FLAG** — enough coverage to weigh heavy; actual process and source lifetime
composition must be established before a plan. This pass does not choose a transport
or claim receipt durability.
