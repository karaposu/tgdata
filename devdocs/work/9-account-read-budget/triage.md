---
model: unknown
effort: unknown
---

# Triage — issue #9

## User Input

Use task-impl on GitHub #9, "Enforce a per-account read budget inside tgdata".
The previous discussion selected it because its enforcement can be verified
offline while live proxy testing for #3 is unavailable. Scope: tgdata's reading
paths, shared client factory, account identity, persistence and existing tests,
plus Telethon 1.45.0's actual pagination/request behavior.

**Weight:** feature-heavy. Multiple readers and pooled/short-lived clients share
an account; lost accounting can be silent; persistent usage and concurrency
cross the request and storage boundary.

**Warmth:** carried from this session's full source read and #5 implementation /
review / merged-tree verification at `af593fc`. Relevant Telethon request,
message-iterator and dialog-iterator code was read for this issue. No repeated
archaeology refresh is needed under CONTRIBUTING §4.1.

**Traverse:** not needed at this scope. The feature extends the existing shared
client/request interception structure and conventional SQLite transactions;
it does not introduce the future worker or change the engines' boundaries.
Product choices about accounting units, window and persistence are explicit
in the following description and will be attacked by the plan critic. A
meaning gap discovered there must stop the task-impl run.

**Watch for:** network-page reads versus output rows; oldest-first offsets when
reducing page size; account identity versus session/pool names; simultaneous
claims; restart and clock behavior; exceptional/cancelled requests; pending
partial results; message pulls hidden in search, discovery or media lookup;
local budget exhaustion being confused with Telegram account health.

## Traversal Trace

Mode: artifact. Entry: signal-first. Territory: explicit-bounded. The earlier
full-source workspace is retained in this session; new vendor behavior was
read and probed. Tags below concern relevance, never file age or correctness.

| # | Region | Item | Tag | Confidence | Recency (UTC filesystem; none for remote) |
|---|---|---|---|---|---|
| 1 | `tgdata/message_engine.py` | fetch_messages / search_messages | core | HIGH | 2026-10-03T19:35:48.953194+00:00 |
| 2 | `tgdata/message_engine.py` | get_message_count / download_media_by_id / _process_message | core | HIGH | 2026-10-03T19:35:48.953194+00:00 |
| 3 | `tgdata/discovery_engine.py` | _mine_room / _links / public discovery calls | core | HIGH | 2026-10-03T19:35:48.952415+00:00 |
| 4 | `tgdata/connection_engine.py` | _client_class / _new_client / primary, pool and ephemeral paths | core | HIGH | 2026-10-04T22:13:00.749304+00:00 |
| 5 | `tgdata/tgdata.py` | constructor / poll_for_messages / message and discovery delegates | core | HIGH | 2026-10-04T22:13:00.785959+00:00 |
| 6 | `tgdata/tgdata.py` | on_new_message / run_with_event_loop | sub | HIGH | 2026-10-04T22:13:00.785959+00:00 |
| 7 | `tgdata/session_store.py` | StoredSession / own-account cache / synchronous store interface | sub | HIGH | 2026-10-04T22:44:49.875322+00:00 |
| 8 | `tgdata/health.py` | classify / reporting / recovery evidence | sub | HIGH | 2026-10-03T19:35:48.952728+00:00 |
| 9 | `tgdata/models.py` | RateLimitInfo / MessageData | sub | HIGH | 2026-10-03T07:54:30.530271+00:00 |
| 10 | `tgdata/progress.py` | ProgressTracker | side | HIGH | 2025-08-15T16:03:26.793552+00:00 |
| 11 | `tgdata/utils.py` | exports and DataFrame utilities | side | HIGH | 2026-09-30T07:14:29.956982+00:00 |
| 12 | `tgdata/smoke_tests/test_17_session_store.py` | offline factory and session fixtures | sub | HIGH | 2026-10-04T22:44:03.271036+00:00 |
| 13 | `tgdata/smoke_tests/test_16_health_events.py` | scripted sender / polling error handling | sub | HIGH | 2026-10-03T19:35:48.954162+00:00 |
| 14 | `tgdata/smoke_tests/test_15_login_checks.py` | login stand-ins | sub | HIGH | 2026-10-03T17:12:34.339740+00:00 |
| 15 | `tgdata/smoke_tests/test_14_flood_threshold.py` | real Telethon request loop with scripted transport | sub | HIGH | 2026-10-03T17:12:34.339288+00:00 |
| 16 | `tgdata/smoke_tests/test_13_device_identity.py` | client factory patch point | sub | HIGH | 2026-10-03T07:55:04.355906+00:00 |
| 17 | `tgdata/smoke_tests/test_12_proxy.py` | offline/loopback versus live checks | sub | HIGH | 2026-10-03T07:30:09.708599+00:00 |
| 18 | `.venv/lib/python3.11/site-packages/telethon/client/messages.py` | _MessagesIter / _IDsIter | core | HIGH | 2026-10-03T09:09:32.892107+00:00 |
| 19 | `.venv/lib/python3.11/site-packages/telethon/client/users.py` | __call__ / _call | core | HIGH | 2026-10-03T09:09:32.893062+00:00 |
| 20 | `.venv/lib/python3.11/site-packages/telethon/client/dialogs.py` | _DialogsIter | sub | HIGH | 2026-10-03T09:09:32.891295+00:00 |
| 21 | `.venv/lib/python3.11/site-packages/telethon/requestiter.py` | RequestIter state and collect | core | HIGH | 2026-10-03T09:09:32.887635+00:00 |
| 22 | `devdocs/work/9-account-read-budget/probe_budget_seams.py` | paging and process-level transaction probes | core | HIGH | 2026-10-05T07:59:32.357265+00:00 |
| 23 | `README.md` | message limits / incremental reads / polling / account configuration | sub | HIGH | 2026-10-04T22:44:49.900018+00:00 |
| 24 | `setup.py` | dependency bounds and package discovery | side | HIGH | 2026-10-03T07:29:10.872688+00:00 |
| 25 | `devdocs/scoped/9/desc.md` | unrelated historical heartbeat task | side | HIGH | 2026-08-23T12:01:11.414332+00:00 |
| 26 | `GitHub` | GitHub #9 request and status | core | HIGH | no mtime available |
| 27 | `GitHub` | GitHub #6 batch contract; #5 completed session storage | sub | HIGH | no mtime available |

## State Summary

Coverage: the listed runtime modules and request/pagination implementations
are confirmed at function resolution. Existing test_12–17 were read in full
in this session. README is confirmed for the affected public surfaces; the
older smoke scripts remain manual/live demonstrations, not an offline runner.

Confirmed absent: a persistent per-account quota, an atomic usage ledger,
warm-up policy, a budget stop signal, and a single full-suite command that
safely runs every historical smoke script offline. RateLimitInfo's request
counter does not implement these. The existing session store offers only
load/save and supplies no atomic claim operation.

Concepts (name → provenance): message page → 18/21; per-request interception →
4/19; account identity → 4/7; atomic claim → 22; partial result → 1/3;
local stop versus Telegram verdict → 5/8; passive updates → 6;
metadata previews → 20; separate message-batch contract → 27.

Recency distribution is descriptive only: runtime/test files have filesystem
mtimes as listed; two remote entries have none. No item was filtered by age.
Workspace populated: true, 2026-10-05; source/request behavior and explicit tags
are present in this session. No uncovered core region remains.

## Frontier

Define what counts before planning: output rows and fetched protocol messages
are different. Decide whether metadata previews and unsolicited updates are
part of this allowance. Decide rolling versus fixed windows, persistent policy
and warm-up origin, and partial-result reporting. The request names none of
these implementation details; choices must be explicit, not accidental.

## Telemetry and self-assessment

27 items: {'core': 10, 'sub': 13, 'side': 4, 'umbrella': 0}. Filesystem mtime: 25; no mtime: 2.
Three region passes: readers, shared/account state, then vendor/persistence
behavior. Boundary discovery and workspace-overload triggers did not fire.
Checked missed relevance, territory binding, workspace/artifact consistency,
interpretive overstep and recency filtering. **PROCEED** to task-desc.
