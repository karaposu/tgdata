---
model: gpt-6-astra
effort: max
---
# Stage5 triage surfacing

## User Input

Surface the existing Stage5 joining territory to weigh the work and identify the
contract inquiry frontier, using merged devf15f1a8. Do not choose an implementation here.

## Traversal Trace

| # | Region | Item | Relevance | Confidence | Recency annotation |
|---|---|---|---|---|---|
| 1 | scope | source-input.md | core | HIGH | {"source":"filesystem","value":"2026-10-10T20:00:06.194547+00:00"} |
| 2 | public contract | docs/group_operations.md | core | HIGH | {"source":"filesystem","value":"2026-10-10T19:59:05.458329+00:00"} |
| 3 | ownership contract | docs/account_operations.md | core | HIGH | {"source":"filesystem","value":"2026-10-10T19:59:05.456080+00:00"} |
| 4 | identity/lifetime | tgdata/account_operation.py | core | HIGH | {"source":"filesystem","value":"2026-10-10T19:59:05.463099+00:00"} |
| 5 | admission seam | tgdata/budget_client.py | core | HIGH | {"source":"filesystem","value":"2026-10-10T19:59:05.465615+00:00"} |
| 6 | group domain | tgdata/group_operations.py | core | HIGH | {"source":"filesystem","value":"2026-10-10T19:59:05.467221+00:00"} |
| 7 | public facade | tgdata/tgdata.py:1–282 (constructor/owned context/group methods) | core | HIGH | {"source":"filesystem","value":"2026-10-10T19:59:05.488567+00:00"} |
| 8 | join allowance | tgdata/join_budget.py (retained Stage4 full source) | core | HIGH | {"source":"filesystem","value":"2026-10-10T19:59:05.470860+00:00"} |

| 9 | factory | tgdata/connection_engine.py: _client_class, constructors, _new_client, _account_operation | core | HIGH | {"source": "filesystem", "value": "2026-10-10T19:59:05.466337+00:00"} |
| 10 | health | tgdata/owned_health.py (whole module) | core | HIGH | {"source": "filesystem", "value": "2026-10-10T19:59:05.473893+00:00"} |
| 11 | health | tgdata/health.py: classify/request evidence, retained Stage2 source | core | HIGH | {"source": "filesystem", "value": "2026-10-10T19:59:05.467694+00:00"} |
| 12 | SDK dispatch | Telethon1.45 client/users.py: UserMethods._call | core | HIGH | {"source": "filesystem", "value": "2026-10-03T09:09:32.893062+00:00"} |
| 13 | SDK join | Telethon1.45 functions/channels.py: JoinChannelRequest | core | HIGH | {"source": "filesystem", "value": "2026-10-03T09:09:32.909319+00:00"} |
| 14 | SDK join | Telethon1.45 functions/messages.py: ImportChatInviteRequest | core | HIGH | {"source": "filesystem", "value": "2026-10-03T09:09:32.911895+00:00"} |
| 15 | SDK result | Telethon1.45 types/messages.py: ChatInviteJoinResultOk/WebView | core | HIGH | {"source": "filesystem", "value": "2026-10-03T09:09:32.922117+00:00"} |
| 16 | SDK cache | Telethon1.45 sessions/memory.py: process_entities/_entities_to_rows | sub | HIGH | {"source": "filesystem", "value": "2026-10-03T09:09:32.902128+00:00"} |
| 17 | historical | 8a43d23:tgdata/join_client.py and group_operations.py | core | HIGH | {"source": "none", "value": null} |
| 18 | historical review | 8a43d23:devdocs/work/7-group-operations/pr-critic.md | core | HIGH | {"source": "none", "value": null} |
| 19 | test foundations | tgdata/smoke_tests/test_32_account_operation.py: Fixture/Wire | core | HIGH | {"source": "filesystem", "value": "2026-10-10T19:59:05.485483+00:00"} |
| 20 | test foundations | tgdata/smoke_tests/test_33_owned_health.py: RPCReply/setup | core | HIGH | {"source": "filesystem", "value": "2026-10-10T19:59:05.485802+00:00"} |
| 21 | test foundations | tgdata/smoke_tests/test_34_group_access.py: Reply/send/setup | core | HIGH | {"source": "filesystem", "value": "2026-10-10T19:59:05.486252+00:00"} |
| 22 | allowance tests | tgdata/smoke_tests/test_35_join_budget.py, retained full Stage4 tests | sub | HIGH | {"source": "filesystem", "value": "2026-10-10T19:59:05.486580+00:00"} |
| 23 | public/package | tgdata/__init__.py and setup.py, retained full sources | sub | HIGH | {"source": "filesystem", "value": "2026-10-10T19:59:05.462672+00:00"} |
| 24 | vendor docs | https://core.telegram.org/method/channels.joinChannel (page layer225) | sub | HIGH | {"source": "none", "value": null} |
| 25 | vendor docs | https://core.telegram.org/method/messages.importChatInvite (page layer225) | sub | HIGH | {"source": "none", "value": null} |
| 26 | process | CONTRIBUTING.md §§4–7,9,12 | umbrella | HIGH | {"source": "filesystem", "value": "2026-10-10T19:59:05.434735+00:00"} |

## State Summary

Artifact case; signal-first; explicit-bounded territory: #7 Stage5 joining against
merged devf15f1a8. Purpose is breadth/weight and inquiry-frontier discovery, not
selection. Three cycles: current contracts and domain; actual SDK/old attempt;
health/test/public/vendor/process edges. Content consumed in-session at each
listed whole-module or complete named-function resolution. Existing Stage4 budget
source/tests and prior ownership context remain available; fixture regions are
not claimed to be all possible source behavior.

Confirmed absent: no current join_group, join sender admission or Stage5 pipeline
artifacts/PARKED/rejecting PR critic. Open issue titles read; #7 owns joining,
#17 routing remains separate and is not a prerequisite. No AGENTS.md or project
card was found in the applicable worktree/ancestor paths. Original broad PR16
is historical; its single unique rejection is not a Stage5 rejection.

Concept names/provenance: target grammar(2,6), verified owner/lifetime(3–4,9),
actual send admission(5,8,12–14), joined/requested/interaction outcomes(15,17,24–25),
local cache enrichment(16), owned source health(10–11), real SDK fixture boundary(19–21),
file custody(8,22), public package contract(23), staged merge archive(26).

Frontier: actual SDK result dispatch/cache behavior, per-attempt proof/claim order,
post-ack failure meaning, join-versus-read health recovery, supported target/outcome
scope, and whether broader raw-client guarding belongs in this stage. Method pages
observed at layer225 do not replace installed1.45/layer229 constructor evidence.
The newer constructor URLs were unreachable; local SDK source is available instead.
No live acceptance or speculative framework choice is inferred from these reads.

Workspace populated:true. No uncertain item omitted; metadata is descriptive,
never a relevance filter. No overload or boundary-discovery subphase fired.
Telemetry:26 entries,3 cycles; all HIGH relevance confidence at named resolution.
Self-checks: obvious paths covered, absences checked, tags consistent, frontier
explicit, no source content copied into this thin artifact. LAYER1 operational
and LAYER2 identity checks passed. Verdict: PROCEED to triage/inquiry.

### Recency distribution (derived, not relevance evidence)

```json
{
  "scope": {
    "newest": "2026-10-10T20:00:06.194547+00:00",
    "oldest": "2026-10-10T20:00:06.194547+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "public contract": {
    "newest": "2026-10-10T19:59:05.458329+00:00",
    "oldest": "2026-10-10T19:59:05.458329+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "ownership contract": {
    "newest": "2026-10-10T19:59:05.456080+00:00",
    "oldest": "2026-10-10T19:59:05.456080+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "identity/lifetime": {
    "newest": "2026-10-10T19:59:05.463099+00:00",
    "oldest": "2026-10-10T19:59:05.463099+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "admission seam": {
    "newest": "2026-10-10T19:59:05.465615+00:00",
    "oldest": "2026-10-10T19:59:05.465615+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "group domain": {
    "newest": "2026-10-10T19:59:05.467221+00:00",
    "oldest": "2026-10-10T19:59:05.467221+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "public facade": {
    "newest": "2026-10-10T19:59:05.488567+00:00",
    "oldest": "2026-10-10T19:59:05.488567+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "join allowance": {
    "newest": "2026-10-10T19:59:05.470860+00:00",
    "oldest": "2026-10-10T19:59:05.470860+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "factory": {
    "newest": "2026-10-10T19:59:05.466337+00:00",
    "oldest": "2026-10-10T19:59:05.466337+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "health": {
    "newest": "2026-10-10T19:59:05.473893+00:00",
    "oldest": "2026-10-10T19:59:05.467694+00:00",
    "no_mtime_count": 0,
    "total_items": 2
  },
  "SDK dispatch": {
    "newest": "2026-10-03T09:09:32.893062+00:00",
    "oldest": "2026-10-03T09:09:32.893062+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "SDK join": {
    "newest": "2026-10-03T09:09:32.911895+00:00",
    "oldest": "2026-10-03T09:09:32.909319+00:00",
    "no_mtime_count": 0,
    "total_items": 2
  },
  "SDK result": {
    "newest": "2026-10-03T09:09:32.922117+00:00",
    "oldest": "2026-10-03T09:09:32.922117+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "SDK cache": {
    "newest": "2026-10-03T09:09:32.902128+00:00",
    "oldest": "2026-10-03T09:09:32.902128+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "historical": {
    "newest": null,
    "oldest": null,
    "no_mtime_count": 1,
    "total_items": 1
  },
  "historical review": {
    "newest": null,
    "oldest": null,
    "no_mtime_count": 1,
    "total_items": 1
  },
  "test foundations": {
    "newest": "2026-10-10T19:59:05.486252+00:00",
    "oldest": "2026-10-10T19:59:05.485483+00:00",
    "no_mtime_count": 0,
    "total_items": 3
  },
  "allowance tests": {
    "newest": "2026-10-10T19:59:05.486580+00:00",
    "oldest": "2026-10-10T19:59:05.486580+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "public/package": {
    "newest": "2026-10-10T19:59:05.462672+00:00",
    "oldest": "2026-10-10T19:59:05.462672+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  },
  "vendor docs": {
    "newest": null,
    "oldest": null,
    "no_mtime_count": 2,
    "total_items": 2
  },
  "process": {
    "newest": "2026-10-10T19:59:05.434735+00:00",
    "oldest": "2026-10-10T19:59:05.434735+00:00",
    "no_mtime_count": 0,
    "total_items": 1
  }
}
```
