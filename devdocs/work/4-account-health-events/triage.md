---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

Triage for GitHub issue #4 in karaposu/tgdata (branch feat/4-account-health-events): "Report account health states as events" — every Telegram signal maps to one small set (ok, waiting, logged out, banned, restricted, no access) and is emitted as an event through a callback, with the time, the account, the group, the call that caused it, and any wait length. Territory: the tgdata package at /Users/ns/Desktop/projects/telegram-group-scraper (connection_engine.py, message_engine.py, discovery_engine.py, tgdata.py, models.py, the smoke tests) plus the installed Telethon 1.40 error and flood-wait paths. Purpose: answer "what parts of this system does this issue actually touch?" so the work can be weighed light or heavy per CONTRIBUTING.md §4.3–4.4, and record it in devdocs/work/4-account-health-events/triage.md.

---

# Triage — issue #4

**Weight:** feature-heavy

**Surfaced:**
- **Connection engine** — the persistent path's authentication through Telethon's interactive `start()`, the use-and-close authorization check, reconnects, the health check, and the rate-limit helpers.
- **Message engine** — the fetch loop's flood-wait retries and give-up, the error re-raise, the dialog-sync fallback that raises `GroupAccessError`, and the per-message failures it swallows.
- **Discovery engine** — the raw-request wait and reconnect loop, the unslept username resolution, and the per-seed and per-link skips.
- **Facade** — where a health callback would be registered; every public call as the event's "call"; the poll loop that swallows every error; the real-time handler wrapper; and `run_with_event_loop`.
- **Config model** — the only notion of "which account" tgdata has: the config path and session name.
- **Telethon 1.40** — the error classes per state and their HTTP-like base classes; the request carried on every error; waits it sleeps through silently; an authorization check that turns any error into "not authorized"; `start()` sending login codes; and an updates loop that disconnects on a logout and re-raises it from `run_until_disconnected`.
- **Smoke tests** — where the new tests go, and the stand-in-client pattern that can drive real paths without a network.

**Why heavy:** it fails the light test on three axes at once (§4.4).
- *Blast radius:* every engine, the facade, and the real-time path. Telegram signals surface in all of them, plus in Telethon code tgdata does not own.
- *Observability:* a misclassified state fails silently, and the misclassification already happens today. A flood wait answers "not authorized"; this morning a real logout surfaced as an interactive login prompt in a consumer's log.
- *Consumers:* test-run tables, dashboards, and the open issues that act on these states (#3 pauses an account on a failed check, #9 reports a reached budget, #10 emits these events).

Model contact: none. Reversibility: no money or records — but these events will drive decisions to pause or reassign accounts.

**Watch for:**
1. **A rate limit reported as a logout.** Telethon's `is_user_authorized()` catches every `RPCError`, flood waits included, and `ephemeral_client` turns that into `AuthRequiredError`. The real error has to be classified, not the boolean.
2. **Waits nobody sees.** Telethon sleeps through waits up to `flood_sleep_threshold` (60 s) inside its own call, including "early" waits it remembers per request type, and only logs them on `telethon.client.users`. Unless those are observed, "waiting" is undercounted on every path except discovery, which already sends with threshold 0.
3. **Logout on the persistent path calls `start()`**, which requests a login code and then waits on the console. Emitting "logged out" there means checking authorization before `start()` — the headless-login bug. Whether that fix is in scope is a decision for the description.
4. **Signals swallowed on purpose** — per-message media failures, discovery's seed and link skips, the poll loop, the handler wrapper. They must still emit events without changing control flow.
5. **"restricted" has no clean reading-side signal** in Telethon 1.40. `UserRestrictedError` and `PeerFloodError` are sending-side; the newer frozen-account errors (`FROZEN_METHOD_INVALID`) are not in 1.40's error list. What "restricted" means for a reader is an open question, not a mapping.
6. **"the account" is undefined in tgdata.** There is a config path and a session name; a stable user id needs a `get_me()` call.
7. **Callback safety must be decided.** The heartbeat never lets a broken callback kill a run, while `found_callback` / `batch_callback` propagate exceptions on purpose. A health event stream has to pick one.
8. **The real-time path changes state with no call in flight.** A logout ends `run_until_disconnected` with Telethon's stored error; a lost channel during update catch-up is only logged.

**Traverse (§5):** called. The state set and the event shape are a structure that later issues stand on (#3, #8, #9, #10), and item 5 above is a meaning gap, not a detail.

---

# Surfacing record

Mode: **artifact** · entry point: **signal-first** · territory: **explicit-bounded** (boundary-discovery sub-phase not fired).

## Traversal Trace

Recency is filesystem mtime in UTC, as a signal only — never used to weigh relevance. Telethon files are from the installed 1.40.0 package.

| # | Region | Item | Verdict | Conf. | Note | Recency |
|---|---|---|---|---|---|---|
| 1 | `tgdata/connection_engine.py` | `AuthRequiredError` | core | HIGH | existing "needs login" state | 2026-10-03T07:54:30Z |
| 2 | ″ | `ConnectionEngine.ephemeral_client` | core | HIGH | authorization check via `is_user_authorized()` — misreports waits | ″ |
| 3 | ″ | `ConnectionEngine._authenticate` | core | HIGH | `start(phone)`; one flood-wait sleep then retry; anything else → `ConnectionError` | ″ |
| 4 | ″ | `ConnectionEngine._ensure_connected` | core | HIGH | flood wait on connect; `ConnectionError` | ″ |
| 5 | ″ | unused import `AuthKeyUnregisteredError` | core | HIGH | named in the issue | ″ |
| 6 | ″ | `ConnectionEngine._load_config` / account identity (config path, session name, username) | core | MEDIUM | the only "account" tgdata knows | ″ |
| 7 | ″ | `ConnectionEngine.get_client`, `session()` | sub | MEDIUM | entry to the persistent path | ″ |
| 8 | ″ | `ConnectionEngine.health_check` | sub | HIGH | natural place to report current state | ″ |
| 9 | ″ | `ConnectionEngine.validate_connection` | sub | MEDIUM | collapses every error to `False` | ″ |
| 10 | ″ | `ConnectionEngine.handle_rate_limit` | sub | HIGH | the "exponential" wait strategy | ″ |
| 11 | ″ | `ConnectionPool.mark_rate_limited`, `rate_limits` | sub | MEDIUM | per-connection wait bookkeeping | ″ |
| 12 | ″ | `ConnectionEngine._new_client` | sub | MEDIUM | the single client factory — a place to attach per-client observation | ″ |
| 13 | ″ | `ProxyConfigError`, `parse_proxy_url` | side | MEDIUM | config errors, not Telegram signals; a dead proxy is "no connection", outside the six states | ″ |
| 14 | ″ | `device_identity` | side | HIGH | not an error path | ″ |
| 15 | `tgdata/message_engine.py` | `fetch_messages` flood loop, `MAX_FLOOD_RETRIES`, give-up `RuntimeError` | core | HIGH | the one handled "wait" today | 2026-08-05T12:02:07Z |
| 16 | ″ | `fetch_messages` broad `except Exception` → log + raise | core | HIGH | every other signal leaves here unclassified | ″ |
| 17 | ″ | `_entity_after_dialog_sync` | core | HIGH | turns a cache miss into "no access" after one dialog sync | ″ |
| 18 | ″ | `GroupAccessError` | core | HIGH | existing "no access" state | ″ |
| 19 | ″ | `_process_message` per-message `except` (profile photo, media, bytes) | sub | HIGH | swallowed failures that may be flood or access signals | ″ |
| 20 | ″ | `download_media_by_id`, `get_message_count`, `search_messages` | sub | HIGH | error sites without the dialog-sync fallback | ″ |
| 21 | ″ | `_beat` heartbeat closure | sub | HIGH | exception-safe callback convention | ″ |
| 22 | ″ | `batch_callback`, `progress_callback` | side | MEDIUM | propagate / swallow conventions for comparison | ″ |
| 23 | `tgdata/discovery_engine.py` | `DiscoveryEngine._request` | core | HIGH | per-call threshold 0; waits slept visibly or raised; network waits | 2026-09-30T07:21:30Z |
| 24 | ″ | `DiscoveryEngine._resolve` | core | HIGH | unslept `ResolveUsername` wait; dialog-sync fallback | ″ |
| 25 | ″ | `_similar` / `_links` per-item skip handlers | core | HIGH | flood, access and RPC signals swallowed per seed or link | ″ |
| 26 | ″ | `DiscoveryInterrupted` | sub | HIGH | carries `retry_after` — a wait length already in hand | ″ |
| 27 | ″ | `_wait_for_network` | sub | MEDIUM | connectivity loss — not one of the six states, but a "waiting"-like condition | ″ |
| 28 | ″ | `_notify` / `found_callback` | sub | HIGH | propagating-callback convention | ″ |
| 29 | ″ | `_mine_room` | sub | MEDIUM | its own wait and reconnect loop | ″ |
| 30 | `tgdata/tgdata.py` | `TgData.__init__` | core | HIGH | where a health callback would be registered | 2026-10-03T07:55:04Z |
| 31 | ″ | public calls: `get_messages`, `get_message_count`, `search_messages`, `list_groups`, `download_media_by_id`, the four discovery calls | core | HIGH | the event's "call" and "group" fields | ″ |
| 32 | ″ | `poll_for_messages` | core | HIGH | swallows every error, logs, continues — a logout here loops silently | ″ |
| 33 | ″ | `run_with_event_loop` | core | HIGH | `run_until_disconnected` re-raises the updates loop's stored logout | ″ |
| 34 | ″ | `_register_pending_handlers` safe wrapper | sub | MEDIUM | swallows handler exceptions | ″ |
| 35 | ″ | `validate_connection`, `health_check` facades | sub | MEDIUM | | ″ |
| 36 | ″ | `get_metrics`, `export_metrics` | side | MEDIUM | could carry the last known state | ″ |
| 37 | `tgdata/models.py` | `ConnectionConfig` | core | MEDIUM | account identity fields | 2026-10-03T07:54:30Z |
| 38 | ″ | `RateLimitInfo` | side | MEDIUM | `requests_made` never counted | ″ |
| 39 | ″ | `GroupInfo`, `MessageData` | — | HIGH | rejected (HIGH-confidence): no bearing | ″ |
| 40 | `tgdata/__init__.py` | `__all__` and error exports | sub | HIGH | new public types land here | 2026-10-03T07:29:10Z |
| 41 | `tgdata/smoke_tests/` | `test_13_device_identity.py` stand-in client | sub | HIGH | drives real paths with no network — fits error injection | 2026-10-03T07:55:04Z |
| 42 | ″ | `test_12_proxy.py` local relay | sub | MEDIUM | a refusing proxy produces real transport errors | 2026-10-03T07:30:09Z |
| 43 | ″ | `test_08_batch_callback.py` | side | MEDIUM | callback-exception propagation precedent | 2025-08-16T21:47:22Z |
| 44 | ″ | `test_11_discover_groups.py` | side | MEDIUM | discovery paths that would emit events | 2026-09-30T07:14:30Z |
| 45 | ″ | `test_00_connection.py` | side | LOW | connection basics | 2025-08-16T19:57:19Z |
| 46 | Telethon `errors/rpcerrorlist.py` | waiting: `FloodWaitError`, `FloodPremiumWaitError`, `SlowModeWaitError`, `FloodTestPhoneWaitError` | core | HIGH | present in 1.40 | 2025-08-15T07:22:55Z |
| 47 | ″ | logged out: `AuthKeyUnregisteredError`, `SessionRevokedError`, `SessionExpiredError`, `AuthKeyInvalidError`, `AuthKeyDuplicatedError`; `SessionPasswordNeededError` | core | HIGH | present; the last is a login step, not a logout | ″ |
| 48 | ″ | banned: `UserDeactivatedBanError`, `UserDeactivatedError`, `PhoneNumberBannedError` | core | HIGH | present | ″ |
| 49 | ″ | restricted: `UserRestrictedError`, `PeerFloodError` | core | MEDIUM | present but sending-side; `FrozenMethodInvalidError` / `FrozenParticipantMissingError` absent | ″ |
| 50 | ″ | no access: `ChannelPrivateError`, `ChatForbiddenError`, `ChannelInvalidError`, `UserBannedInChannelError`, `ChannelPublicGroupNaError`, `InviteHashExpiredError` | core | HIGH | present | ″ |
| 51 | Telethon `errors/rpcbaseerrors.py` | `RPCError.request` | core | HIGH | every error carries the request that caused it — the "call" field | 2025-08-15T07:22:55Z |
| 52 | ″ | base classes: `UnauthorizedError`, `AuthKeyError`, `ForbiddenError`, `FloodError`, `BadRequestError`, `ServerError`, `TimedOutError` | core | HIGH | a category fallback for unlisted errors | ″ |
| 53 | Telethon `client/users.py` | `_call` auto-sleep ≤ `flood_sleep_threshold`, INFO log on `telethon.client.users`; "early" sleep from `_flood_waited_requests` | core | HIGH | waits tgdata never sees | 2025-08-15T07:22:55Z |
| 54 | ″ | `is_user_authorized` catches `RPCError` | core | HIGH | the wait-as-logout misreport | ″ |
| 55 | Telethon `client/auth.py` | `start()` → `send_code_request` → `input()` | core | HIGH | the persistent path's response to a logout | 2025-08-15T07:22:55Z |
| 56 | Telethon `client/updates.py` | updates loop: on `UnauthorizedError` / `AuthKeyError` stores the error and disconnects; `run_until_disconnected` re-raises it | core | HIGH | logout with no call in flight | 2025-08-15T07:22:55Z |
| 57 | ″ | channel catch-up: `ChannelPrivateError` / `ChannelInvalidError` logged only | sub | HIGH | "no access" visible only in logs | ″ |
| 58 | Telethon `network/mtprotosender.py` | connection retries; "Connection to Telegram failed N time(s)" | sub | MEDIUM | transport loss, not a Telegram verdict | 2025-08-15T07:22:55Z |
| 59 | `tgdata/progress.py` | `ProgressTracker.update` swallows callback errors | side | LOW | another callback-safety precedent | 2025-08-15T16:03:26Z |
| 60 | `tgdata/utils.py` | export and filter helpers | — | HIGH | rejected (HIGH-confidence): file I/O only, no Telegram signal | 2026-09-30T07:14:29Z |

## State Summary

**Territory:** the tgdata package (`connection_engine.py`, `message_engine.py`, `discovery_engine.py`, `tgdata.py`, `models.py`, `__init__.py`, `progress.py`, `utils.py`, the smoke tests) plus Telethon 1.40's error, flood-wait, auth and updates paths.

**Purpose:** what parts of the system issue #4 touches, so it can be weighed light or heavy.

**Coverage map**

| Region | Coverage | Aggregate verdict |
|---|---|---|
| `connection_engine.py` | confirmed (read in full on this branch) | core |
| `message_engine.py` | confirmed (read in full this session; unchanged since) | core |
| `discovery_engine.py` | confirmed (read in full on this branch) | core |
| `tgdata.py` | confirmed (read in full on this branch) | core |
| `models.py`, `__init__.py` | confirmed | core / sub |
| smoke tests | scanned-but-shallow (patterns, not every assertion) | sub |
| Telethon errors and base classes | confirmed (classes probed by import) | core |
| Telethon `users.py`, `auth.py`, `updates.py` | confirmed for the error, sleep, auth and updates paths only | core |
| Telethon `mtprotosender.py` | scanned-but-shallow | sub |
| `progress.py` | confirmed | side |
| `utils.py` | confirmed | absent |

**Confirmed-absent:**
- `utils.py` holds no Telegram signal.
- No health or state type exists anywhere in tgdata.
- No test exercises error-to-state classification.

**Concept names**

| Name | Type | Provenance | Gloss |
|---|---|---|---|
| account health state | vocabulary | issue | ok · waiting · logged out · banned · restricted · no access |
| health event | vocabulary | issue | time, account, group, call, wait length |
| `flood_sleep_threshold` | structural-reference | #53 | Telethon sleeps waits up to it, silently |
| early flood wait | structural-reference | #53 | a remembered wait applied before sending |
| `RPCError.request` | structural-reference | #51 | the request behind an error |
| `UnauthorizedError` / `AuthKeyError` / `ForbiddenError` / `FloodError` | structural-reference | #52 | category base classes |
| `_updates_error` | structural-reference | #56 | Telethon's stored real-time logout |
| `AuthRequiredError` | structural-reference | #1 | tgdata's "needs login" |
| `GroupAccessError` | structural-reference | #18 | tgdata's "no access" |
| `DiscoveryInterrupted.retry_after` | structural-reference | #26 | a wait length tgdata already holds |
| exception-safe callback | coined-term | #21 | heartbeat style: a broken callback never ends a run |
| propagating callback | coined-term | #28 | found / batch style: an exception ends the run |
| account identity | coined-term | #6 | config path + session name; user id needs `get_me()` |
| reading-side restriction | coined-term | #49 | what "restricted" means for an account that only reads |

**Recency distribution**

| Region | Newest | Oldest | No mtime | Items |
|---|---|---|---|---|
| tgdata engines + facade + models | 2026-10-03T07:55:04Z | 2026-08-05T12:02:07Z | 0 | 40 |
| smoke tests | 2026-10-03T07:55:04Z | 2025-08-16T19:57:19Z | 0 | 5 |
| Telethon 1.40 | 2025-08-15T07:22:55Z | 2025-08-15T07:22:55Z | 0 | 13 |
| progress.py, utils.py | 2026-09-30T07:14:29Z | 2025-08-15T16:03:26Z | 0 | 2 |

**Workspace-populated status:** `{populated: true, populated-at: 2026-10-03, extent: every core region read in full in this session; smoke tests and mtprotosender scanned}`.

## Telemetry

- Mode `artifact`, entry `signal-first`, boundary-discovery not fired.
- Regions traversed: 12. Items enumerated: 60 — core 32, sub 19, side 7, rejected 2. No umbrella tags; nothing was uncertain enough to need one.
- Convergence: territory exhausted at module and function resolution; no item filtered at uncertain relevance; only two HIGH-confidence rejections.
- Workspace-overload trigger: not fired.
- Failure modes checked: missed-relevance, territory-mis-binding (consumer issues kept to the Frontier, outside the stated territory), recency-bias-filter, interpretive-overstep.
- `items_with_mtime` 60 / `items_without_mtime` 0.

## Frontier — for downstream

- **"restricted" for a reader** — no reading-side signal surfaced in 1.40 (item 49). Needs a decision, or evidence from a restricted account.
- **Newer Telethon** — whether 1.41–1.44 add the frozen-account errors; a consumer of tgdata runs 1.44.
- **Consumers outside the territory** — #3 (pause on a failed check), #8 (login steps), #9 (budget reached), #10 (worker emits these events). They shape what the event must carry, and are not part of this traversal.
- **The headless-login bug** — item 55 seen from the persistent path; whether #4 fixes it or only reports it.

## Self-assessment

**FLAG.** The output is complete for the stated territory. Two flags are for the next steps, not a re-run: the "restricted" state has no surfaced signal, and the issue's consumers lie outside the territory.
