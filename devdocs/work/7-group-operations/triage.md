---
model: unknown
effort: unknown
---

# Triage — issue #7

## User Input

Use task-impl on #7 — group lookup, access checks and joining. The issue requests
three short-lived operations through ephemeral_client, with an account join limit.

**Weight:** feature-heavy. This adds a public account-membership operation,
its quota/admission behavior and results for callers and future worker #10.
Network retries, pending outcomes, account identity, persistent state and health
reporting cross boundaries; a mistake can change external membership.

**Warmth:** full-source context retained from #5/#9/#6, including #6's two
review cycles and merged-tree verification at `45bab71`. Refreshed group models,
ephemeral lifecycle, shared budget/health/request paths and the installed 1.45.0
join/invite constructors. The warmth anchor is the tested merge on this branch's
ancestry; no cold-session archaeology re-run is needed.

**Branch:** `feat/7-group-operations`, natively linked with gh issue develop,
based on dev at `45bab7172621f576fa5e4b3265f87ec20da04fd5`. The working tree
was clean. `duncan/` remains excluded from commits. No AGENTS.md or project card
is present. Model/effort metadata remain unknown; §9 is not certified.

**Traverse:** required by CONTRIBUTING §5. The membership transition/result
contract and shared admission policy are structures future #10 will depend on.
Use the full sequential pass in this task's `traverse/` folder before desc/plan.

**Related issue sweep:** all ten open/closed titles read; no duplicate. #9
#6, #5 and #4 are integrated. #10 consumes group operations; #8 is a separate
login workflow; #3 stays deferred by user preference. #7 has no discussion
decisions. Historical `devdocs/scoped/7` is an unrelated, already implemented
real-time handler fix.

## Traversal Trace

Mode: artifact; entry: signal-first; territory: explicit-bounded. Three cycles:
current public/lifecycle/record behavior, limits/health/storage interactions,
then SDK/protocol/tests/docs and related consumers. Relevance is content-based;
mtime is descriptive only. Existing full reads are retained in this session.

| # | Region | Item identifier | Relevance | Confidence | Recency (UTC) |
|---|---|---|---|---|---|
| 1 | request | GitHub #7 body and empty discussion | core | HIGH | none / null |
| 2 | history | `devdocs/scoped/7/desc.md` — devdocs/scoped/7/desc.md — unrelated real-time handler fix | side | HIGH | filesystem / 2026-07-19T20:40:52.470191+00:00 |
| 3 | records | `tgdata/models.py` — GroupInfo / ConnectionConfig | core | HIGH | filesystem / 2026-10-03T07:54:30.530271+00:00 |
| 4 | public API | `tgdata/tgdata.py` — TgData constructor / _reported / group and discovery delegates | core | HIGH | filesystem / 2026-10-05T12:11:43.199766+00:00 |
| 5 | connections | `tgdata/connection_engine.py` — ConnectionEngine factory / ephemeral_client / authorization | core | HIGH | filesystem / 2026-10-05T09:40:30.662542+00:00 |
| 6 | health | `tgdata/health.py` — classification / group normalization / call and recovery scope | core | HIGH | filesystem / 2026-10-03T19:35:48.952728+00:00 |
| 7 | limits | `tgdata/read_budget.py` — ReadBudget persistence / account identity / reservations | core | HIGH | filesystem / 2026-10-05T09:02:33.056613+00:00 |
| 8 | limits | `tgdata/budget_client.py` — BudgetClientMixin / actual send and hidden retry admission | core | HIGH | filesystem / 2026-10-05T09:07:29.764286+00:00 |
| 9 | sessions | `tgdata/session_store.py` — StoredSession / entity policy / concurrent client persistence | sub | HIGH | filesystem / 2026-10-04T22:44:49.875322+00:00 |
| 10 | access | `tgdata/message_engine.py` — GroupAccessError / entity-after-dialog-sync / history reads | core | HIGH | filesystem / 2026-10-05T09:14:38.468091+00:00 |
| 11 | discovery | `tgdata/discovery_engine.py` — candidate group shape / no-join discovery boundary | sub | HIGH | filesystem / 2026-10-05T09:14:38.491188+00:00 |
| 12 | reader | `tgdata/batch_engine.py` — BatchEngine explicit source / shared guarded session | sub | HIGH | filesystem / 2026-10-05T12:11:43.174743+00:00 |
| 13 | errors | `tgdata/batch_files.py` — local error provenance and primary outcome ownership | sub | HIGH | filesystem / 2026-10-05T14:05:21.293796+00:00 |
| 14 | package | `tgdata/__init__.py` — public export inventory | sub | HIGH | filesystem / 2026-10-05T12:11:43.225617+00:00 |
| 15 | docs | `README.md` — message/budget/session/discovery public contracts | sub | HIGH | filesystem / 2026-10-05T14:12:56.669022+00:00 |
| 16 | package | `setup.py` — Python/dependency bounds | side | HIGH | filesystem / 2026-10-05T12:11:43.257750+00:00 |
| 17 | tests | `tgdata/smoke_tests/README.md` — offline/live test inventory | sub | HIGH | filesystem / 2026-10-05T14:11:17.422411+00:00 |
| 18 | tests | `tgdata/smoke_tests/test_15_login_checks.py` — ephemeral auth / no-prompt fixtures | core | HIGH | filesystem / 2026-10-03T17:12:34.339740+00:00 |
| 19 | tests | `tgdata/smoke_tests/test_16_health_events.py` — actual SDK request and health fixtures | core | HIGH | filesystem / 2026-10-03T19:35:48.954162+00:00 |
| 20 | tests | `tgdata/smoke_tests/test_18_read_budget.py` — SQLite/process budgets and scripted real SDK senders | core | HIGH | filesystem / 2026-10-05T09:40:30.639272+00:00 |
| 21 | SDK call | `.venv/lib/python3.11/site-packages/telethon/client/users.py` — UserMethods _call / get_me / entity resolution | core | HIGH | filesystem / 2026-10-03T09:09:32.893062+00:00 |
| 22 | SDK joins | `.venv/lib/python3.11/site-packages/telethon/tl/functions/channels.py` — JoinChannelRequest | core | HIGH | filesystem / 2026-10-03T09:09:32.909319+00:00 |
| 23 | SDK joins | `.venv/lib/python3.11/site-packages/telethon/tl/functions/messages.py` — CheckChatInviteRequest / ImportChatInviteRequest | core | HIGH | filesystem / 2026-10-03T09:09:32.911895+00:00 |
| 24 | SDK invites | `.venv/lib/python3.11/site-packages/telethon/tl/types/__init__.py` — ChatInvite / ChatInviteAlready / ChatInvitePeek | core | HIGH | filesystem / 2026-10-03T09:09:32.917819+00:00 |
| 25 | SDK results | `.venv/lib/python3.11/site-packages/telethon/tl/types/messages.py` — ChatInviteJoinResultOk / ChatInviteJoinResultWebView | core | HIGH | filesystem / 2026-10-03T09:09:32.922117+00:00 |
| 26 | vendor docs | core.telegram.org methods checkChatInvite / importChatInvite / joinChannel | sub | HIGH | none / null |
| 27 | related issues | all ten open/closed titles; worker #10 and login #8 boundaries | core | HIGH | none / null |

## State Summary

Territory: current group/data/public/client/session/health/budget paths, installed
Telethon 1.45.0 join/invite/request behavior, package/tests/docs and related GitHub
work. Purpose: expose what #7 touches before choosing an API/result/admission
design. All listed source regions are confirmed at relevant function/class
resolution; vendor generated types were read as complete classes, not an
unbounded generated module.

Confirmed absent: public group lookup/access/join operations and a join-specific
allowance. Existing metadata models, read budgets, ephemeral clients and health
reporting are present; this pass does not choose whether/how to reuse them.

The installed SDK reports Telethon 1.45.0, TL layer 229. Its two join requests
return ChatInviteJoinResultOk or ChatInviteJoinResultWebView, not simply Updates.
The retrieved core method pages describe an earlier result shape, so installed
types and executable SDK probes must ground the selected-version contract.
The tl.telethon.dev fetch returned unrelated text/unavailable pages and is not
accepted as evidence. No live account or membership mutation was performed.

Concept names with provenance: group metadata → 3; ephemeral lifecycle → 5;
health/error provenance → 6/13; account allowance → 7/8; session persistence → 9;
read access → 10; discovery non-mutation → 11; mutation attempt/retry → 21/22/23;
invite preview/peek/already → 24; acknowledged/web-view result → 25; worker
consumer → 27. These are surfaced names, not an adjudicated architecture.

Coverage map: confirmed core for request/records/public API/connections/health/
limits/access/tests/SDK call/joins/invites/results; confirmed sub for sessions/
discovery/reader/errors/package/docs/vendor docs; confirmed side for historical
scope/dependency bounds. No uncertain-relevance item was filtered.

Recency distribution by region (oldest / newest / no-mtime / total):
- request: null / null / 1 / 1
- history: 2026-07-19T20:40:52.470191+00:00 / 2026-07-19T20:40:52.470191+00:00 / 0 / 1
- records: 2026-10-03T07:54:30.530271+00:00 / 2026-10-03T07:54:30.530271+00:00 / 0 / 1
- public API: 2026-10-05T12:11:43.199766+00:00 / 2026-10-05T12:11:43.199766+00:00 / 0 / 1
- connections: 2026-10-05T09:40:30.662542+00:00 / 2026-10-05T09:40:30.662542+00:00 / 0 / 1
- health: 2026-10-03T19:35:48.952728+00:00 / 2026-10-03T19:35:48.952728+00:00 / 0 / 1
- limits: 2026-10-05T09:02:33.056613+00:00 / 2026-10-05T09:07:29.764286+00:00 / 0 / 2
- sessions: 2026-10-04T22:44:49.875322+00:00 / 2026-10-04T22:44:49.875322+00:00 / 0 / 1
- access: 2026-10-05T09:14:38.468091+00:00 / 2026-10-05T09:14:38.468091+00:00 / 0 / 1
- discovery: 2026-10-05T09:14:38.491188+00:00 / 2026-10-05T09:14:38.491188+00:00 / 0 / 1
- reader: 2026-10-05T12:11:43.174743+00:00 / 2026-10-05T12:11:43.174743+00:00 / 0 / 1
- errors: 2026-10-05T14:05:21.293796+00:00 / 2026-10-05T14:05:21.293796+00:00 / 0 / 1
- package: 2026-10-05T12:11:43.225617+00:00 / 2026-10-05T12:11:43.257750+00:00 / 0 / 2
- docs: 2026-10-05T14:12:56.669022+00:00 / 2026-10-05T14:12:56.669022+00:00 / 0 / 1
- tests: 2026-10-03T17:12:34.339740+00:00 / 2026-10-05T14:11:17.422411+00:00 / 0 / 4
- SDK call: 2026-10-03T09:09:32.893062+00:00 / 2026-10-03T09:09:32.893062+00:00 / 0 / 1
- SDK joins: 2026-10-03T09:09:32.909319+00:00 / 2026-10-03T09:09:32.911895+00:00 / 0 / 2
- SDK invites: 2026-10-03T09:09:32.917819+00:00 / 2026-10-03T09:09:32.917819+00:00 / 0 / 1
- SDK results: 2026-10-03T09:09:32.922117+00:00 / 2026-10-03T09:09:32.922117+00:00 / 0 / 1
- vendor docs: null / null / 1 / 1
- related issues: null / null / 1 / 1

Workspace: populated=true; populated-at=2026-10-05T16:18:27.868652+00:00; extent=all surfaced core
regions at function/class resolution, with retained whole-codebase context.

## Frontier

Resolve the distinction between readability and membership; invite previews and
temporary peeks; requested versus completed versus web-view outcomes; join-limit
units/window/persistence; retry/cancellation admission; fresh account authority;
and redaction/recovery scopes. These are questions for the traverse and plan,
not conclusions of this surfacing pass.

## Telemetry and self-assessment

Three cycles; 27 items; tags {'core': 17, 'side': 2, 'sub': 8}.
24 filesystem-backed items and 3 external items without mtime.
Boundary discovery not needed. Coverage converged; no overload frontier. Checked
missed relevance, irrelevant/over-coverage, territory binding, artifact sufficiency,
workspace consistency, both recency biases, interpretive overstep, purpose loss
and downstream self-coupling. **PROCEED** to the required traverse.
