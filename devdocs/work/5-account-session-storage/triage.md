---
model: claude-opus-5-5[1m]
effort: max
---

## User Input

Triage for GitHub issue #5 in karaposu/tgdata (branch feat/5-account-session-storage, cut from dev at 110996c): "Load and save sessions through a pluggable session store" — tgdata asks a session store to load and save each account's Telegram session, so sessions can live somewhere other than a .session file; today's file behaviour stays the default. Maintainer decisions already taken (2026-10-03): no encryption in tgdata (a store may encrypt on its own), no helper to migrate existing .session files. Territory (explicit-bounded, artifact case): the tgdata package at /Users/ns/Desktop/projects/telegram-group-scraper — connection_engine.py (the client factory _new_client and every path that builds a client: persistent, pool, use-and-close, device_identity's probe; login and first-login detection; close/disconnect), tgdata.py (constructor, health identity, close), discovery_engine.py and message_engine.py (their reliance on Telethon's session entity cache), health.py, models.py (ConnectionConfig), __init__.py, the smoke tests — plus Telethon 1.45.0's sessions package (abstract Session, MemorySession, SQLiteSession, StringSession) and where the client calls session.save()/close()/delete(). Purpose: answer "what parts of this system does this issue actually touch?" so the work can be weighed light or heavy per CONTRIBUTING.md §4.3–4.4 (blast radius, observability, consumers, model contact, reversibility). SAVE the artifact as devdocs/work/5-account-session-storage/triage.md, in triage.md form: Weight, Surfaced, Why light/heavy, Watch for, then the surfacing record (Traversal Trace with verdicts, State Summary, Telemetry, Frontier, Self-assessment).

---

# Triage — issue #5

**Weight:** feature-heavy

**Surfaced:**
- **The client factory** — `ConnectionEngine._new_client()`, the one place that hands Telethon a session. Today it always passes a file name, and Telethon turns that into a SQLite `.session` file. Through it run the persistent client, each pool connection (`<name>_1 … <name>_n`) and every use-and-close client. `device_identity()` builds its own in-memory probe and is unaffected.
- **Login state read from the session** — `first_login = client.session.auth_key is None`, at two sites. The login checks from `c72eab4` decide on it whether a login code may ever be requested.
- **The facade** — `TgData.__init__`, where a store would be passed in; `_health_identity()`, whose `account.session` is the configured session name; `close()`, which disconnects and so ends the session.
- **Consumers of the session's group cache** — discovery's cache-only lookup (`client.session.get_input_entity`), whose promise that "every room found is readable by `get_messages`" lasts only as long as the cache does; and the message engine's dialog-sync fallback for ids the cache does not know.
- **Telethon 1.45.0's session model:**
  - **What the client accepts.** A name or path becomes `SQLiteSession`, a `Session` instance is used as-is, and `None` becomes `MemorySession`.
  - **`MemorySession`.** It already holds everything — data centre, auth key, update states, the group cache, sent files — and its `save`, `close` and `delete` do nothing.
  - **`StringSession`.** Its saved string holds only the data centre and the auth key.
  - **The save points.** `connect()` (two), a data-centre switch, a new auth key, the updates loop once a minute, and one download path.
  - **On disconnect.** It writes its last state into the session, then calls `close()`.
  - **On log-out.** `delete()`.
  - **Async session methods.** Accepted only as "experimental", with a warning.
- **Config and model** — the session name's precedence (`session_file` > `username` > default, quotes stripped), and `ConnectionConfig.session_file`.
- **Smoke tests** — test_13, test_14, test_15 and test_16 build clients through `_new_client()`, on session files in temporary folders. test_15's stand-in client reads `session.auth_key` and closes the session on disconnect.

**Why heavy — it is small in code, but it fails the light test on three axes (§4.4):**
- **Observability.** A session that is not saved, or saved incompletely, fails silently and late: the login is gone at the *next* start, and a lost group cache shows only as extra chat-list syncs and username lookups. No test or screen shows it at the time it happens.
- **Consumers.** Telethon reads and writes the session, and the application's storage keeps it — two parties with different needs. Issues #8 (step-by-step login) and #10 (a worker holding many accounts) will build on the same store.
- **Reversibility.** The session *is* the account's login. Losing one forces a by-hand re-login with a code from the owner, and a store that writes it to the wrong place exposes the account.

Blast radius is borderline: one seam in code, but every connection path goes through it. Model contact: none.

**Watch for:**
1. **A save at close.** Telethon writes its last state into the session and then calls `close()`, which does nothing on an in-memory session. A store-backed session that does not save there loses everything since the last minutely save.
2. **The whole session, not the string format.** `StringSession` keeps only the auth key and data centre. Storing that alone means every start re-syncs chat lists, re-looks-up usernames — the request Telegram punishes hardest — and cannot read rooms discovery found but the account never joined.
3. **A store that fails must not look like a new session.** If loading fails and tgdata carries on with an empty session, `first_login` becomes true. At a terminal that runs the interactive login and requests a code — the exact failure `c72eab4` fixed. A failed load has to raise.
4. **Two clients, one stored session.** The persistent client and a use-and-close client share one session name and run at the same time. Each loads when built and saves on its own schedule, so the last write wins. Pool connections use their own names.
5. **Log-out.** Telethon calls `delete()`, and a store has to know what deleting a stored session means.
6. **Sync or async.** Telethon treats async session methods as experimental, and the oldest Telethon tgdata supports (1.33) may not await them at all.
7. **The default stays byte-identical.** Without a store, the same file name goes to Telethon as today, so every existing `.session` file keeps working.

**Traverse (§5):** not needed.
- The work sits inside a structure that already exists: Telethon's session design, where the client takes any session object.
- The meaning of the store was settled by the maintainer on 2026-10-03: load and save each account's session through a store; no encryption in tgdata; today's files stay the default; no migration helper.
- What is left — when to save, what to keep, two clients on one session — is within reach of the description and the plan.
- Issues #8 and #10 will use the store, but its interface is two methods over Telethon's existing session model, so it is not a new structure they stand on.

---

# Surfacing record

Mode: **artifact** · entry point: **signal-first** · territory: **explicit-bounded** (boundary-discovery sub-phase not fired).

## Traversal Trace

Recency is the filesystem mtime in UTC, used as a signal only and never to weigh relevance. The Telethon files are from the installed 1.45.0 package.

| # | Region | Item | Verdict | Conf. | Note | Recency |
|---|---|---|---|---|---|---|
| 1 | `tgdata/connection_engine.py` | `ConnectionEngine._new_client` | core | HIGH | the one seam: passes the session name to Telethon | 2026-10-03T19:35:48Z |
| 2 | ″ | `_init_primary_client` / `get_client` | core | HIGH | the persistent client on `config.session_file` | ″ |
| 3 | ″ | `_init_pool` (`<name>_<i>`) | core | HIGH | several stored sessions per account | ″ |
| 4 | ″ | `ephemeral_client` | core | HIGH | a second client on the same session, at the same time as the persistent one | ″ |
| 5 | ″ | `first_login = client.session.auth_key is None` (two sites) | core | HIGH | an empty store answer reads as "never logged in" | ″ |
| 6 | ″ | `_log_in` → `client.start()`; `_auth_required` messages | sub | HIGH | an interactive login must persist through the store; messages name the session | ″ |
| 7 | ″ | `_load_config` session-name precedence | sub | HIGH | the name a store would key on | ″ |
| 8 | ″ | `close` / `_discard_clients` → `disconnect()` | sub | HIGH | disconnect is the session's last save point | ″ |
| 9 | ″ | `device_identity` — `TelegramClient(StringSession(), …)` | side | HIGH | already an in-memory probe; never saved | ″ |
| 10 | ″ | `_client_class` mixins | side | MEDIUM | pass the session through unchanged | ″ |
| 11 | `tgdata/tgdata.py` | `TgData.__init__` | core | HIGH | where a store would be passed in | 2026-10-03T19:35:48Z |
| 12 | ″ | `_health_identity` | sub | MEDIUM | events name the session by the config's name | ″ |
| 13 | ″ | `close` / `__aexit__` | sub | MEDIUM | ends the session | ″ |
| 14 | `tgdata/discovery_engine.py` | `_resolve` — `client.session.get_input_entity(ref)` | sub | HIGH | reads the stored group cache; discovery's "readable by `get_messages`" rests on it | 2026-10-03T19:35:48Z |
| 15 | `tgdata/message_engine.py` | `_entity_after_dialog_sync`, `get_entity` | sub | HIGH | a lost cache means a chat-list sync on every unknown id | 2026-10-03T19:35:48Z |
| 16 | `tgdata/health.py` | — | side | HIGH | no session use beyond the identity in item 12 | 2026-10-03T19:35:48Z |
| 17 | `tgdata/models.py` | `ConnectionConfig.session_file` | sub | MEDIUM | the configured name | 2026-10-03T07:54:30Z |
| 18 | `tgdata/__init__.py` | exports | sub | MEDIUM | a store type may be exported | 2026-10-03T07:29:10Z |
| 19 | `tgdata/smoke_tests/` | `test_15_login_checks.py` | sub | HIGH | the stand-in reads `session.auth_key` and closes the session; the login-code guarantees | 2026-10-03T17:12:34Z |
| 20 | ″ | `test_13_device_identity.py`, `test_14_flood_threshold.py`, `test_16_health_events.py` | sub | HIGH | build clients through `_new_client()` on temporary session files | 2026-10-03T07:55:04Z / 2026-10-03T17:12:34Z / 2026-10-03T19:35:48Z |
| 21 | ″ | `test_12_proxy.py` | side | MEDIUM | a throwaway session | 2026-10-03T07:30:09Z |
| 22 | ″ | `test_00_connection.py` … `test_11` | side | LOW | live tests on the configured session file | 2025-08-16T19:57:19Z (test_00) |
| 23 | `README.md` | "Authentication" — `session_file` | sub | MEDIUM | where the store option is documented | 2026-10-03T19:35:48Z |
| 24 | `setup.py` | `Telethon>=1.33,<2.0` | sub | MEDIUM | the floor bounds which session hooks can be relied on | 2026-10-03T07:29:10Z |
| 25 | `.gitignore` | `*.session` | side | HIGH | file sessions are kept out of git today | 2026-08-05T12:03:08Z |
| 26 | repo root | `'karaposu'.session`, `karaposu.session`, `test_session.session` | side | HIGH | existing file sessions; the quoted name is the old quoting bug. Not migrated, by the maintainer's decision | 2026-07-21T05:32:16Z / 2026-08-02T07:17:12Z / 2025-08-17T07:50:19Z |
| 27 | Telethon `client/telegrambaseclient.py` | `__init__` session argument | core | HIGH | a name or path becomes `SQLiteSession`, a `Session` is used as-is, `None` becomes `MemorySession` | 2026-10-03T09:09:32Z |
| 28 | ″ | `connect()` save points (two); `_switch_dc`; `_auth_key_callback` | core | HIGH | when the login and data centre are written | ″ |
| 29 | ″ | `_disconnect_coro` → `_save_states_and_entities()` → `session.close()` | core | HIGH | the last flush, into `close()` | ″ |
| 30 | ″ | `_save_states_and_entities` | sub | HIGH | writes the update states and the self id; the group cache enters per request | ″ |
| 31 | Telethon `client/updates.py` | the updates loop: once a minute, flush and `save()` | core | HIGH | the regular save cadence while connected | 2026-10-03T09:09:32Z |
| 32 | Telethon `client/auth.py` | `log_out()` → `session.delete()` | sub | HIGH | what a stored session does on log-out | 2026-10-03T09:09:32Z |
| 33 | Telethon `client/downloads.py` | the exported-sender data-centre fix → `save()` | side | MEDIUM | a rare save point | 2026-10-03T09:09:32Z |
| 34 | Telethon `client/users.py` | `_call` → `session.process_entities(result)` | sub | HIGH | the group cache fills per request | 2026-10-03T09:09:32Z |
| 35 | Telethon `utils.py` | `maybe_async` | sub | HIGH | async session methods are "experimental" and warn | 2026-10-03T09:09:32Z |
| 36 | Telethon `sessions/abstract.py` | `Session` — 17 abstract members | sub | HIGH | the interface a stored session satisfies | 2026-10-03T09:09:32Z |
| 37 | Telethon `sessions/memory.py` | `MemorySession` | core | HIGH | holds the whole state; `save`, `close` and `delete` do nothing | 2026-10-03T09:09:32Z |
| 38 | Telethon `sessions/sqlite.py` | `SQLiteSession` | core | HIGH | today's default: `.session` appended, commit on save, `delete` removes the file | 2026-10-03T09:09:32Z |
| 39 | Telethon `sessions/string.py` | `StringSession` | sub | HIGH | saves only the data centre and auth key | 2026-10-03T09:09:32Z |

## State Summary

**Territory:** the tgdata package — the engines, the facade, `health.py`, `models.py`, `__init__.py`, the smoke tests, `README.md`, `setup.py`, `.gitignore` and the repo root's session files — plus Telethon 1.45.0's sessions package and the client's session save, close and delete points.

**Purpose:** what issue #5 touches, so it can be weighed light or heavy.

**Coverage map**

| Region | Coverage | Aggregate verdict |
|---|---|---|
| `connection_engine.py` | confirmed (read in full this session) | core |
| `tgdata.py` | confirmed | core |
| `discovery_engine.py`, `message_engine.py` | confirmed, for session and cache use | sub |
| `health.py` | confirmed | side |
| `models.py`, `__init__.py`, `setup.py`, `.gitignore` | confirmed | sub / side |
| smoke tests | confirmed for session use (test_12–16); live tests scanned | sub / side |
| `README.md` | confirmed | sub |
| Telethon `sessions/` | confirmed (all four modules) | core |
| Telethon client save, close and delete points | confirmed, every call site found by search and read | core |

**Confirmed-absent:**
- No other place in tgdata builds a client or hands Telethon a session.
- tgdata never calls `session.save()`, `close()` or `delete()` itself.
- No store, or any alternative to file sessions, exists in tgdata today. The `StringSession` import serves only `device_identity()`'s probe.

**Concept names**

| Name | Type | Provenance | Gloss |
|---|---|---|---|
| session store | vocabulary | issue | where a session is loaded from and saved to |
| `SQLiteSession` | structural-reference | #38 | today's `.session` file |
| `MemorySession` | structural-reference | #37 | holds everything, saves nothing |
| `StringSession` | structural-reference | #39 | login key and data centre only |
| save point | coined-term | #28, #29, #31 | where Telethon calls `save()` or `close()` |
| group cache | coined-term | #14, #34 | the session's entities and their access hashes |
| first login | structural-reference | #5 | `auth_key is None` |
| last write wins | coined-term | #4 | two clients saving one stored session |

**Recency distribution**

| Region | Newest | Oldest | No mtime | Items |
|---|---|---|---|---|
| tgdata package | 2026-10-03T19:35:48Z | 2025-08-16T19:57:19Z | 0 | 23 |
| repo root and config files | 2026-10-03T07:29:10Z | 2025-08-17T07:50:19Z | 0 | 3 |
| Telethon 1.45.0 | 2026-10-03T09:09:32Z | 2026-10-03T09:09:32Z | 0 | 13 |

**Workspace-populated status:** `{populated: true, populated-at: 2026-10-03, extent: every core region read in full this session; live smoke tests scanned}`.

## Telemetry

- Mode `artifact`, entry `signal-first`, boundary discovery not fired.
- Regions traversed: 14. Items enumerated: 39 — 14 core, 18 sub, 7 side, none rejected. No umbrella tags.
- Convergence: the territory was traversed at module and function resolution, with no item filtered at uncertain relevance.
- Workspace-overload trigger: not fired.
- Failure modes checked: missed-relevance, territory-mis-binding, recency-bias-filter, interpretive-overstep.
- `items_with_mtime` 39 / `items_without_mtime` 0.

## Frontier — for downstream

- **The floor version.** Whether Telethon 1.33, the oldest tgdata supports, calls the same save points and accepts a `MemorySession` subclass the same way. A probe against 1.33.1 settles it.
- **Async stores.** Telethon accepts async session methods only as "experimental". Whether tgdata's store interface is sync only is for the description.
- **The serialised form.** What a stored session must carry — auth key, data centre, update states, group cache, sent-file cache — and how it is versioned.

## Self-assessment

**PROCEED.** The output is complete for the stated territory. The three frontier items are for the description and the plan, not a re-run.
