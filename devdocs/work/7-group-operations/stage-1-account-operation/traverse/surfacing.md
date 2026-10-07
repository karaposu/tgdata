# Surfacing — Stage 1 ownership inquiry

## User Input

_branch.md: span the internal context, public context and dispatch-supervisor readings; preserve Stage 1 exclusions.

## Traversal Trace

Artifact; signal-first; explicit-bounded. Same-session source workspace retained and current-dev named seams refreshed; two cycles: rehydrate source/admission plus constructor/authentication, then SDK disconnect/lifetime and compatibility. Factory, budget mixin, SDK get_me and disconnect read again; remaining named artifacts retained from the same-session intake. All three articulation variants share these seams; no additional relevant region appeared. Recency captured during enumeration, never used to choose relevance.

| # | Region | Identifier | Tag | Confidence | Recency |
|---|---|---|---|---|---|
| 1 | lifecycle | `tgdata/connection_engine.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T22:44:01.569840+00:00"}` |
| 2 | admission | `tgdata/budget_client.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T22:44:01.569339+00:00"}` |
| 3 | admission | `tgdata/read_budget.py` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-07T22:44:01.573993+00:00"}` |
| 4 | sessions | `tgdata/session_store.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T22:44:01.574396+00:00"}` |
| 5 | health | `tgdata/health.py` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-07T22:44:01.570612+00:00"}` |
| 6 | facade | `tgdata/tgdata.py` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-07T22:44:01.588616+00:00"}` |
| 7 | tests | `tgdata/smoke_tests/test_15_login_checks.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T22:44:01.580656+00:00"}` |
| 8 | tests | `tgdata/smoke_tests/test_18_read_budget.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-07T22:44:01.581542+00:00"}` |
| 9 | sdk | `Telethon1.45 telegrambaseclient.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-03T09:09:32.892326+00:00"}` |
| 10 | sdk | `Telethon1.45 users.py` | core | HIGH | `{"source": "filesystem", "value": "2026-10-03T09:09:32.893062+00:00"}` |
| 11 | history | `#7 rejected PR critique @8a43d23` | sub | HIGH | `{"source": "filesystem", "value": "2026-10-05T19:28:42.376926+00:00"}` |
| 12 | reference | `#17 pool_source.py @964d082` | side | HIGH | `{"source": "filesystem", "value": "2026-10-07T21:33:38.828358+00:00"}` |
| 13 | contract | `user selected Stage1 only` | umbrella | HIGH | `{"source": "none", "value": null}` |

## State Summary

Territory: named files/interfaces on dev95, actual installed SDK1.45, and explicit historical/reference items. Purpose: establish evidence for the three preserved API/lifetime variants. Lifecycle/admission/sessions/SDK core seams confirmed; health/facade confirmed at relevant boundaries with retained full reads; test fixtures confirmed; prior/reference source read but not adopted.

Confirmed-absent: expected-account operation API on dev; existing owned-operation handle or owner-aware admission helper. No claim about an absent pool on an unmerged branch.

Concept names: ephemeral_client/structural-reference/1; fresh identity/vocabulary/2; StoredSession/structural-reference/4; diagnostic ownership/vocabulary/5; cancellation shielding/vocabulary/9; error exhaustion/vocabulary/10.

Recency distribution:
```json
{
  "lifecycle": {
    "newest": "2026-10-07T22:44:01.569840+00:00",
    "oldest": "2026-10-07T22:44:01.569840+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "admission": {
    "newest": "2026-10-07T22:44:01.573993+00:00",
    "oldest": "2026-10-07T22:44:01.569339+00:00",
    "no_mtime_count": 0,
    "total_items": 2
  },
  "sessions": {
    "newest": "2026-10-07T22:44:01.574396+00:00",
    "oldest": "2026-10-07T22:44:01.574396+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "health": {
    "newest": "2026-10-07T22:44:01.570612+00:00",
    "oldest": "2026-10-07T22:44:01.570612+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "facade": {
    "newest": "2026-10-07T22:44:01.588616+00:00",
    "oldest": "2026-10-07T22:44:01.588616+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "tests": {
    "newest": "2026-10-07T22:44:01.581542+00:00",
    "oldest": "2026-10-07T22:44:01.580656+00:00",
    "no_mtime_count": 0,
    "total_items": 2
  },
  "sdk": {
    "newest": "2026-10-03T09:09:32.893062+00:00",
    "oldest": "2026-10-03T09:09:32.892326+00:00",
    "no_mtime_count": 0,
    "total_items": 2
  },
  "history": {
    "newest": "2026-10-05T19:28:42.376926+00:00",
    "oldest": "2026-10-05T19:28:42.376926+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "reference": {
    "newest": "2026-10-07T21:33:38.828358+00:00",
    "oldest": "2026-10-07T21:33:38.828358+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "contract": {
    "newest": null,
    "oldest": null,
    "no_mtime_count": 1,
    "total_items": 1
  }
}
```

Frontier: bounded inquiry for handle lifetime and cleanup precedence; actual disconnect cancellation probe. Workspace populated=true at 2026-10-07T22:46:21.660891+00:00; extent=named current interfaces plus retained history.

## Telemetry

13 items; tags {'core': 7, 'sub': 4, 'side': 1, 'umbrella': 1}; filesystem12/none1. Two cycles; no boundary discovery or overload. No uncertain item excluded; territory exhausted at declared resolution. Checked missed/irrelevant coverage, territory, artifact sufficiency, desync, recency bias and interpretive/selection drift. **Verdict: PROCEED** to Sensemaking. Thin artifact contains trace and state only; analysis is downstream.
