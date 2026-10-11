---
model: gpt-6-astra
effort: max
---
# Retirement rework — surfacing

## User Input

Surface the existing#17 retirement/repair boundary and its integration with dev68f6bbd, using the retained same-session assessment workspace. Save here beside source-input.md. Purpose: determine what the authorized focused rework touches before planning.

## Traversal Trace

| # | Region | Item | Relevance | Confidence | Recency annotation |
|---|---|---|---|---|---|
| 1 | scope | source-input.md | core | HIGH | {"source": "filesystem", "value": "2026-10-11T07:37:17.228030+00:00"} |
| 2 | baseline | ../desc.md | core | HIGH | {"source": "filesystem", "value": "2026-10-07T21:19:40.376169+00:00"} |
| 3 | baseline | ../step_by_step_impl_plan.md revision2 | core | HIGH | {"source": "filesystem", "value": "2026-10-07T21:20:29.390494+00:00"} |
| 4 | baseline | ../critic.md, selected outcome/credential mitigations | core | HIGH | {"source": "filesystem", "value": "2026-10-07T21:19:40.375718+00:00"} |
| 5 | source | tgdata/pool_source.py (whole module) | core | HIGH | {"source": "filesystem", "value": "2026-10-07T21:33:38.828358+00:00"} |
| 6 | controller | tgdata/account_pool.py (whole module) | core | HIGH | {"source": "filesystem", "value": "2026-10-07T21:34:46.762529+00:00"} |
| 7 | state | tgdata/pool_state.py (whole module) | sub | HIGH | {"source": "filesystem", "value": "2026-10-07T21:24:26.626054+00:00"} |
| 8 | progress | tgdata/progress_facade.py (whole module) | sub | HIGH | {"source": "filesystem", "value": "2026-10-07T22:04:24.568164+00:00"} |
| 9 | reader | tgdata/batch_engine.py: BatchEngine (complete class) | sub | HIGH | {"source": "filesystem", "value": "2026-10-07T21:26:22.528398+00:00"} |
| 10 | SDK | Telethon1.45 TelegramBaseClient.disconnect/_disconnect_coro (complete) | core | HIGH | {"source": "filesystem", "value": "2026-10-03T09:09:32.892326+00:00"} |
| 11 | cleanup precedent | dev68f6bbd:tgdata/account_operation.py (whole module) | core | HIGH | {"source": "filesystem", "value": "2026-10-11T04:54:38.221750+00:00"} |
| 12 | factory | dev68f6bbd:ConnectionEngine._new_client/_account_operation; branch diff | core | HIGH | {"source": "filesystem", "value": "2026-10-11T04:55:05.471254+00:00"} |
| 13 | proof | probes/retirement_race.py and original reproduction output | core | HIGH | {"source": "filesystem", "value": "2026-10-11T07:37:17.229231+00:00"} |
| 14 | integration | evidence/prior-compatibility.json and trial merge conflicts | core | HIGH | {"source": "filesystem", "value": "2026-10-11T07:37:17.229878+00:00"} |
| 15 | tests | tgdata/smoke_tests/test_31_account_pool.py (whole suite/fixtures) | core | HIGH | {"source": "filesystem", "value": "2026-10-07T21:47:08.667597+00:00"} |
| 16 | public contract | docs/account_pool.md (whole file) | core | HIGH | {"source": "filesystem", "value": "2026-10-07T21:55:33.825699+00:00"} |
| 17 | public integration | README/__init__/TgData changes in original17 and dev diff | sub | HIGH | {"source": "filesystem", "value": "2026-10-07T21:34:46.761917+00:00"} |
| 18 | process | CONTRIBUTING §§4–7/9/12; existing issue17/native branch | umbrella | HIGH | {"source": "filesystem", "value": "2026-10-07T20:04:36.499934+00:00"} |

## State Summary

Artifact case; signal-first; explicit-bounded territory. Re-invocation from retained same-session context, retagged for retirement/integration rather than a new account-routing design. Three cycles: reproduced lifetime/SDK boundary; factory and public-controller integration; durable/progress/test/process edges. All listed regions confirmed at the stated full module/function/diff resolution. No architecture refresh is claimed.

Concept names/provenance: caller cancellation(5,6,10); SDK disconnect task(10,11); pool operation exclusion(6); retired-client reuse(5,13); source outcome retention(4,5); credential reload(4,5); explicit factory options(12); opaque source-permission state(7); replay/ack reader substitution(8,9); constructor compatibility(14,17). These are navigation names, not implementation selections.

Confirmed absent: no PARKED marker or rejecting PR critic for#17; no applicable AGENTS.md/project card; no supplied second-account live resources; no runtime fix in the assessment; no automatic joining in this selected delivery. Existing issue/native branch and heavy label are confirmed. Current dev merge evidence is retained in the same session.

Frontier for planning: wait for actual cleanup under repeated caller cancellation; failed/internal-cancel cleanup and client reuse; factory option precedence using the now-existing API. No uncovered territory or overloaded region; these are bounded choices inside the existing lifetime contract. No uncertain relevance item was excluded.

Workspace populated:true, assembled 2026-10-11T07:38:48.617188+00:00. Eighteen items,3 cycles;13 core,4 sub,1 umbrella; all18 have filesystem metadata,0 without. Boundary discovery did not fire. Tags derive from content/purpose; mtimes do not filter them.

Self-check: obvious scope/SDK/caller/storage/test edges included; confirmed absences checked; no item content copied. LAYER1 missed relevance, irrelevance, over-coverage, mis-binding, overload, under-specification, desync and both recency failures checked; LAYER2 interpretive overstep, purpose loss and downstream-only coupling checked. Convergence reached. Verdict: PROCEED.

### Recency distribution

```json
{
  "scope": {
    "newest": "2026-10-11T07:37:17.228030+00:00",
    "oldest": "2026-10-11T07:37:17.228030+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "baseline": {
    "newest": "2026-10-07T21:20:29.390494+00:00",
    "oldest": "2026-10-07T21:19:40.375718+00:00",
    "no_mtime_count": 0,
    "total_items": 3
  },
  "source": {
    "newest": "2026-10-07T21:33:38.828358+00:00",
    "oldest": "2026-10-07T21:33:38.828358+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "controller": {
    "newest": "2026-10-07T21:34:46.762529+00:00",
    "oldest": "2026-10-07T21:34:46.762529+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "state": {
    "newest": "2026-10-07T21:24:26.626054+00:00",
    "oldest": "2026-10-07T21:24:26.626054+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "progress": {
    "newest": "2026-10-07T22:04:24.568164+00:00",
    "oldest": "2026-10-07T22:04:24.568164+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "reader": {
    "newest": "2026-10-07T21:26:22.528398+00:00",
    "oldest": "2026-10-07T21:26:22.528398+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "SDK": {
    "newest": "2026-10-03T09:09:32.892326+00:00",
    "oldest": "2026-10-03T09:09:32.892326+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "cleanup precedent": {
    "newest": "2026-10-11T04:54:38.221750+00:00",
    "oldest": "2026-10-11T04:54:38.221750+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "factory": {
    "newest": "2026-10-11T04:55:05.471254+00:00",
    "oldest": "2026-10-11T04:55:05.471254+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "proof": {
    "newest": "2026-10-11T07:37:17.229231+00:00",
    "oldest": "2026-10-11T07:37:17.229231+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "integration": {
    "newest": "2026-10-11T07:37:17.229878+00:00",
    "oldest": "2026-10-11T07:37:17.229878+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "tests": {
    "newest": "2026-10-07T21:47:08.667597+00:00",
    "oldest": "2026-10-07T21:47:08.667597+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "public contract": {
    "newest": "2026-10-07T21:55:33.825699+00:00",
    "oldest": "2026-10-07T21:55:33.825699+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "public integration": {
    "newest": "2026-10-07T21:34:46.761917+00:00",
    "oldest": "2026-10-07T21:34:46.761917+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "process": {
    "newest": "2026-10-07T20:04:36.499934+00:00",
    "oldest": "2026-10-07T20:04:36.499934+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  }
}
```
