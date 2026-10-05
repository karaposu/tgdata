---
model: unknown
effort: unknown
---

# Surfacing — group-operation meaning and boundaries

## User Input

Traverse `_branch.md` for G1 across all A1–A4 readings. Purpose: draw the
evidence relevant to metadata, read access, membership outcomes and account
admission into context before stabilizing their meaning. Prior triage is
navigation; retained source context plus refreshed functions/classes is the
workspace. No implementation architecture is selected in this artifact.

## Traversal Trace

Mode: artifact. Entry: signal-first. Territory: explicit-bounded. Four cycles:
framing/lifecycle, invite/join protocol and cache, admission/health/error flow,
then testing/documentation/consumer boundaries. The surfacing framework was
loaded in full and reused from triage. No boundary-discovery sub-phase.

| # | Region | Item identifier | Tag | Confidence | Recency (UTC) |
|---|---|---|---|---|---|
| 1 | framing | `devdocs/work/7-group-operations/traverse/articulate_simple.md` — articulate_simple.md — G1, W1–W5, B1–B4, Y1–Y3, A1–A4 | core | HIGH | filesystem / 2026-10-05T16:23:54.119505+00:00 |
| 2 | framing | `devdocs/work/7-group-operations/traverse/_branch.md` — _branch.md — question, goal and unresolved readings | core | HIGH | filesystem / 2026-10-05T16:25:02.991442+00:00 |
| 3 | navigation | `devdocs/work/7-group-operations/triage.md` — triage.md — prior territory coverage | sub | HIGH | filesystem / 2026-10-05T16:18:27.868930+00:00 |
| 4 | metadata | `tgdata/models.py` — GroupInfo.from_entity / to_dict | core | HIGH | filesystem / 2026-10-03T07:54:30.530271+00:00 |
| 5 | lifecycle | `tgdata/connection_engine.py` — ConnectionEngine.ephemeral_client / _authorization_problem | core | HIGH | filesystem / 2026-10-05T09:40:30.662542+00:00 |
| 6 | public surface | `tgdata/tgdata.py` — TgData._reported / constructor / group delegates | core | HIGH | filesystem / 2026-10-05T12:11:43.199766+00:00 |
| 7 | access | `tgdata/message_engine.py` — MessageEngine._entity_after_dialog_sync / GroupAccessError / fetch | core | HIGH | filesystem / 2026-10-05T09:14:38.468091+00:00 |
| 8 | mutation protocol | `.venv/lib/python3.11/site-packages/telethon/tl/functions/channels.py` — JoinChannelRequest | core | HIGH | filesystem / 2026-10-03T09:09:32.909319+00:00 |
| 9 | mutation protocol | `.venv/lib/python3.11/site-packages/telethon/tl/functions/messages.py` — CheckChatInviteRequest / ImportChatInviteRequest | core | HIGH | filesystem / 2026-10-03T09:09:32.911895+00:00 |
| 10 | invite outcomes | `.venv/lib/python3.11/site-packages/telethon/tl/types/__init__.py` — ChatInvite / ChatInviteAlready / ChatInvitePeek | core | HIGH | filesystem / 2026-10-03T09:09:32.917819+00:00 |
| 11 | join outcomes | `.venv/lib/python3.11/site-packages/telethon/tl/types/messages.py` — ChatInviteJoinResultOk / ChatInviteJoinResultWebView | core | HIGH | filesystem / 2026-10-03T09:09:32.922117+00:00 |
| 12 | SDK control | `.venv/lib/python3.11/site-packages/telethon/client/users.py` — UserMethods._call / get_me / _get_entity_from_string | core | HIGH | filesystem / 2026-10-03T09:09:32.893062+00:00 |
| 13 | session cache | `.venv/lib/python3.11/site-packages/telethon/sessions/memory.py` — MemorySession._entities_to_rows / get_input_entity | core | HIGH | filesystem / 2026-10-03T09:09:32.902128+00:00 |
| 14 | session cache | `tgdata/session_store.py` — StoredSession._entity_to_row / save / disconnect | sub | HIGH | filesystem / 2026-10-04T22:44:49.875322+00:00 |
| 15 | read allowance | `tgdata/read_budget.py` — ReadBudget._reserve / _snapshot / _settle / _transaction | core | HIGH | filesystem / 2026-10-05T09:02:33.056613+00:00 |
| 16 | admission | `tgdata/budget_client.py` — BudgetClientMixin / _BudgetSender / request classification | core | HIGH | filesystem / 2026-10-05T09:07:29.764286+00:00 |
| 17 | health scope | `tgdata/health.py` — normalise_group / HealthMonitor.call / _recover / classify | core | HIGH | filesystem / 2026-10-03T19:35:48.952728+00:00 |
| 18 | local failures | `tgdata/batch_files.py` — batch_files error ownership and cleanup boundary | sub | HIGH | filesystem / 2026-10-05T14:05:21.293796+00:00 |
| 19 | discovery boundary | `tgdata/discovery_engine.py` — DiscoveryEngine group rows / non-joining behavior | sub | HIGH | filesystem / 2026-10-05T09:14:38.491188+00:00 |
| 20 | tests | `tgdata/smoke_tests/test_15_login_checks.py` — test_15 ephemeral lifecycle / auth / no-prompt fixtures | core | HIGH | filesystem / 2026-10-03T17:12:34.339740+00:00 |
| 21 | tests | `tgdata/smoke_tests/test_16_health_events.py` — test_16 callback / recovery / real-request fixtures | core | HIGH | filesystem / 2026-10-03T19:35:48.954162+00:00 |
| 22 | tests | `tgdata/smoke_tests/test_18_read_budget.py` — test_18 concurrency / clocks / retries / real SDK fixtures | core | HIGH | filesystem / 2026-10-05T09:40:30.639272+00:00 |
| 23 | tests | `tgdata/smoke_tests/test_19_message_batches.py` — test_19 local-context / primary-outcome failures | sub | HIGH | filesystem / 2026-10-05T14:10:11.042569+00:00 |
| 24 | docs | `README.md` — README account controls / discovery / batch contract | sub | HIGH | filesystem / 2026-10-05T14:12:56.669022+00:00 |
| 25 | vendor reference | core.telegram.org methods/checkChatInvite, importChatInvite, joinChannel | sub | HIGH | none / null |
| 26 | future consumer | GitHub #10 worker jobs / account pool semantics | core | HIGH | none / null |
| 27 | adjacent work | GitHub #8 login and #3 deferred proxy checks | side | HIGH | none / null |

## State Summary

**Territory:** G1's existing public/group/client/session/health/admission surfaces,
installed Telethon 1.45.0 protocol/control/cache classes, tests and related
consumer requests. **Purpose:** support all four considered readings before
interpreting what each operation can prove and what account limit means.

**Coverage:** framing, metadata, lifecycle, public surface, access, mutation/
invite/join protocol, SDK control, session cache, read allowance, admission and
health are confirmed at relevant function/class resolution (core). Local-failure,
discovery and docs regions are confirmed sub; tests confirmed core/sub; adjacent
work is confirmed side. Related source implementations are held from this warm
session; refreshed SDK classes are held in full.

**Confirmed absent:** a public join operation, join-specific policy/ledger,
membership result contract, join-web-view completion workflow and worker service.
Absence concerns these requested/new concepts, not existing metadata, session,
read-limit or health functionality.

**Concept names with provenance:** metadata identity → 4; ephemeral ownership → 5;
read-capability probe → 7; join request → 8/9; preview/already/peek → 10; wrapped
join acknowledgment/web-view fields → 11; actual send/retry and fresh self → 12;
entity caching → 13/14; quota claim/time window → 15/16; safe operation scope/
recovery/context → 17/18; non-joining discovery → 19; offline composition → 20–23;
future consumer → 26. These names identify items rather than choose relations.

**Recency distribution** (oldest / newest / no-mtime / total):
- framing: 2026-10-05T16:23:54.119505+00:00 / 2026-10-05T16:25:02.991442+00:00 / 0 / 2
- navigation: 2026-10-05T16:18:27.868930+00:00 / 2026-10-05T16:18:27.868930+00:00 / 0 / 1
- metadata: 2026-10-03T07:54:30.530271+00:00 / 2026-10-03T07:54:30.530271+00:00 / 0 / 1
- lifecycle: 2026-10-05T09:40:30.662542+00:00 / 2026-10-05T09:40:30.662542+00:00 / 0 / 1
- public surface: 2026-10-05T12:11:43.199766+00:00 / 2026-10-05T12:11:43.199766+00:00 / 0 / 1
- access: 2026-10-05T09:14:38.468091+00:00 / 2026-10-05T09:14:38.468091+00:00 / 0 / 1
- mutation protocol: 2026-10-03T09:09:32.909319+00:00 / 2026-10-03T09:09:32.911895+00:00 / 0 / 2
- invite outcomes: 2026-10-03T09:09:32.917819+00:00 / 2026-10-03T09:09:32.917819+00:00 / 0 / 1
- join outcomes: 2026-10-03T09:09:32.922117+00:00 / 2026-10-03T09:09:32.922117+00:00 / 0 / 1
- SDK control: 2026-10-03T09:09:32.893062+00:00 / 2026-10-03T09:09:32.893062+00:00 / 0 / 1
- session cache: 2026-10-03T09:09:32.902128+00:00 / 2026-10-04T22:44:49.875322+00:00 / 0 / 2
- read allowance: 2026-10-05T09:02:33.056613+00:00 / 2026-10-05T09:02:33.056613+00:00 / 0 / 1
- admission: 2026-10-05T09:07:29.764286+00:00 / 2026-10-05T09:07:29.764286+00:00 / 0 / 1
- health scope: 2026-10-03T19:35:48.952728+00:00 / 2026-10-03T19:35:48.952728+00:00 / 0 / 1
- local failures: 2026-10-05T14:05:21.293796+00:00 / 2026-10-05T14:05:21.293796+00:00 / 0 / 1
- discovery boundary: 2026-10-05T09:14:38.491188+00:00 / 2026-10-05T09:14:38.491188+00:00 / 0 / 1
- tests: 2026-10-03T17:12:34.339740+00:00 / 2026-10-05T14:10:11.042569+00:00 / 0 / 4
- docs: 2026-10-05T14:12:56.669022+00:00 / 2026-10-05T14:12:56.669022+00:00 / 0 / 1
- vendor reference: null / null / 1 / 1
- future consumer: null / null / 1 / 1
- adjacent work: null / null / 1 / 1

Workspace: populated=true; populated-at=2026-10-05T16:33:33.307504+00:00;
extent=all surfaced core regions with relevance tags and retained current-code
context. Metadata signals did not affect relevance. No uncovered core-region
overload flag; live server behavior is deliberately not claimed by source reads.

## Frontier

The next discipline must relate W1–W5 to the evidence: metadata/membership/read
proof, installed wrapped join outcomes, pending/interaction and unknown states,
nested update caching, actual-send versus successful-membership limits, process
persistence and current account authority. It must also address operation identity
for private invites, health recovery meaning, error provenance and primary cleanup
without assuming that a successful metadata reply proves history access.

The retrieved core method pages and installed join signatures have different
return shapes. Installed 1.45.0 types (layer 229) and later real-SDK probes are
the selected-version evidence; the unrelated tl.telethon.dev response is not
used. How much an interaction result should expose/complete remains B4 openness.

## Telemetry and self-assessment

Four cycles; 27 items; tags {'core': 19, 'sub': 7, 'side': 1};
24 with filesystem mtime, 3 without.
All bounded regions covered; uncertain relevance would be included rather than
filtered. Checked missed relevance, over/irrelevant coverage, territory binding,
overload, artifact sufficiency, workspace sync, recency biases, interpretive
overstep, purpose loss and downstream self-coupling. **PROCEED.**
