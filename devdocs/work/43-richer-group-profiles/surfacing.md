---
model: gpt-6-astra
effort: xhigh
---
# Surfacing — #43

## User Input
Implement #43 richer group profiles; surface the existing observation composition.

## Traversal Trace
| Sequence | Region/item | Relevance | Confidence | Recency annotation (filesystem UTC) |
|---|---|---|---|---|
| 1 | `tgdata/tgdata.py` | core | HIGH | 2026-10-15T15:08:24.883659+00:00 |
| 2 | `tgdata/group_operations.py` | core | HIGH | 2026-10-15T15:08:24.849306+00:00 |
| 3 | `tgdata/account_operation.py` | core | HIGH | 2026-10-15T15:08:24.842915+00:00 |
| 4 | `tgdata/connection_engine.py` | core | HIGH | 2026-10-15T15:08:24.848263+00:00 |
| 5 | `tgdata/owned_health.py` | core | HIGH | 2026-10-15T15:08:24.853068+00:00 |
| 6 | `tgdata/health.py` | core | HIGH | 2026-10-15T15:08:24.850022+00:00 |
| 7 | `tgdata/budget_client.py` | core | HIGH | 2026-10-15T15:08:24.847807+00:00 |
| 8 | `tgdata/read_budget.py` | core | HIGH | 2026-10-15T15:08:24.855775+00:00 |
| 9 | `tgdata/batch_heartbeat.py` | core | HIGH | 2026-10-15T15:08:24.847332+00:00 |
| 10 | `tgdata/__init__.py` | sub | HIGH | 2026-10-15T15:08:24.842640+00:00 |
| 11 | `tgdata/models.py` | sub | HIGH | 2026-10-15T15:08:24.852780+00:00 |
| 12 | `tgdata/message_batch.py` | sub | HIGH | 2026-10-15T15:08:24.852155+00:00 |
| 13 | `docs/account_operations.md` | sub | HIGH | 2026-10-15T15:08:24.819006+00:00 |
| 14 | `docs/group_operations.md` | sub | HIGH | 2026-10-15T15:08:24.832024+00:00 |
| 15 | `tgdata/smoke_tests/test_32_account_operation.py` | sub | HIGH | 2026-10-15T15:08:24.875678+00:00 |
| 16 | `tgdata/smoke_tests/test_33_owned_health.py` | sub | HIGH | 2026-10-15T15:08:24.876102+00:00 |
| 17 | `tgdata/smoke_tests/test_34_group_access.py` | sub | HIGH | 2026-10-15T15:08:24.876848+00:00 |
| 18 | `setup.py` | sub | HIGH | 2026-10-15T15:08:24.839745+00:00 |

## State Summary
Territory: verified profile source path and directly supporting interfaces/fixtures. Purpose: qualify #43 without changing established ownership or budget rules.
Coverage: core runtime, value contracts, public documentation and three foundational fixture suites confirmed; source history/discovery/lifecycle are unchanged adjacent regions.
Confirmed absent: profile persistence, migrations, runtime LLM and UI implementation are not present in this bounded change. PROJECT_SPECIFICS.md is absent.
Concept provenance: expected account (3–4); source evidence (5–6); message allowance (7–8); observational heartbeat (9); portable observation (2,10,12); real SDK fixture (15–17).
Cycles: 3 (public API, dependencies, fixture/protocol boundary). Items: 18; core 9/sub 9/side 0/umbrella 0. 18 with mtime/0 without. Recency recorded as signal only; all items in this checkout share creation-time vicinity, not relevance.
Workspace populated: true, 2026-10-15; source/interfaces listed above read in this session. Frontier: real Telegram permission/visibility is not qualified by synthetic responses; runtime contract preserves refusal/unknown. No unvisited core implementation frontier.
Failure-mode audit: missed/irrelevant/overcoverage, territory binding, workspace/artifact synchronization, recency bias and interpretive overstep considered. No uncertain item excluded.
Verdict: PROCEED. Revisit scope if prebuild contradicts existing composition.
