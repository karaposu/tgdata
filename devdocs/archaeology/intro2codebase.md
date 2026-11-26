# tgdata — an architecture introduction (from the code at `784d851`, 2026-11-26, version 0.1.4)

This is the walk-through I'd give a new engineer on day one. tgdata is a Python library over Telethon 1.45.0 (a Telegram client library) that reads Telegram groups through user accounts. It has grown in two layers:
- an original, convenience-first interface that returns pandas tables;
- a newer, strict layer built for unattended, multi-account collection.

Both are live, and they share one connection core.

## 1. The shape in one picture

```
 Entry points                 Orchestration                       Telegram boundary
 ───────────                  ─────────────                       ─────────────────
 TgData (facade) ───────┬──> MessageEngine / DiscoveryEngine ─┐
   + ProgressFacade     ├──> BatchEngine ──> MessageBatch      │
                        ├──> SyncEngine / BackfillEngine        ├──> ConnectionEngine._new_client()
                        └──> group_* (verified operations)     │        │
 AccountPool ──> _OwnedSource (a ConnectionEngine) ────────────┤        ▼
 Worker (tgdata-worker) ──> one TgData per account ────────────┤   client class = mixins + TelegramClient
 LoginFlow (tgdata-login) ──> _new_client(_client_base=…) ─────┘        │
                                                                         ▼
 Local state: ReadBudget / JoinBudget (SQLite), sync/backfill/pool    Telethon: MTProtoSender ─> Connection
 stores (async load + compare_and_swap), session store (load/save)    (TCP to the DC's IP, via the proxy)
```

There is no server or UI. Callers are Python programs, plus two console commands.

## 2. The connection core — read this first

**`ConnectionEngine` (`connection_engine.py`)** owns everything about reaching Telegram for one account config (`config.ini`, section `[Telegram]`):
- **It reads the config once** (`_load_config`): api id and hash, the session name, an optional proxy with `require_proxy`, and an optional pinned device identity. A bad proxy setting raises `ProxyConfigError` before any socket opens.
- **`_new_client()` is the only factory.** Every Telethon client tgdata builds is made here:
  - the persistent client;
  - the legacy pool's extra connections;
  - the use-and-close `ephemeral_client()`;
  - the verified `_account_operation()`;
  - `LoginFlow`'s auth-only client;
  - `AccountPool`'s owned sources, which subclass the engine and tighten `_new_client`'s options.

  It passes the session — a file name, or a `StoredSession` when a session store is configured — the proxy and the device identity to the client constructor.
- **The client class is a stack of mixins** in front of `TelegramClient`, built and cached by `_client_class()`:
  - `_AnswerEvidence` — notes every request Telegram answers, for health "ok" evidence;
  - `JoinClientMixin` — join admission against the join budget, only inside a verified operation;
  - `BudgetClientMixin` — read-budget reservation at Telethon's send seam;
  - `BatchHeartbeatMixin` — liveness callbacks per request;
  - `_PerCallFloodThreshold` — makes Telethon's per-request flood threshold actually work.

  All of them intercept at Telethon's request layer (`__call__`, `_call(sender, …)`, and wrapping the sender's `send`). None touch the network transport below it: that is still Telethon's own `Connection` class, opened by `MTProtoSender`.
- **Login safety.** tgdata asks Telegram directly whether a session is logged in, with `GetState`. It never runs Telethon's interactive `start()` unless a human can type the code. Otherwise it raises `AuthRequiredError`, with `.reason`, `.banned` and `.first_login`.
- **The legacy `health_check()` / `validate_connection()`** confirm the login with Telegram before calling a connection healthy.

**Sessions** (`session_store.py`). `StoredSession` is Telethon's `MemorySession` that loads from and saves to an application-supplied store:
- it keeps only groups, channels and the account's own rows;
- it never overwrites a login it didn't load;
- it logs failures without the error's text;
- its copies (`clone()`) stay in memory.

Without a store, Telethon's SQLite `.session` file is used, as originally.

## 3. Data flows, end to end

1. **The legacy table read** (`TgData.get_messages`). `@_reported` opens a health call, then `MessageEngine.fetch_messages` runs:
   - it calls `engine.session()`, which is the persistent client, and `get_entity`, falling back to a dialog sync then `GroupAccessError`;
   - it iterates `iter_messages`, waiting out flood waits and resuming from a cursor;
   - the rows become `MessageData`, then a pandas `DataFrame`.

   Media is downloaded inline or later through `download_media_by_id`.
2. **The strict batch read** (`get_message_batch` → `BatchEngine.fetch_batch`):
   - it pages oldest-first after an exclusive message id, within an optional UTC window (`history_window`);
   - it builds validated records and, optionally, content-addressed media blobs (`batch_files`);
   - it returns an immutable, versioned `MessageBatch` (canonical JSON, `batch_id`, `next_after_id`).

   On failure, the completed prefix rides on `error.partial_result`.
3. **Durable progress** (`ProgressFacade`, mixed into both `TgData` and `AccountPool`):
   - `SyncEngine` keeps one pending batch per group in a store with async `load` / `compare_and_swap`. `sync_group` prepares or replays it; only `acknowledge_sync(batch_id)` advances the cursor.
   - `BackfillEngine` does the same for historical runs, with explicit start and control requests, pacing, recovery and receipts.

   Both call back into an injected batch reader. Replaying a pending batch never contacts Telegram.
4. **Verified group operations** — `lookup_group`, `check_group_access`, `get_group_profile`, `measure_group_activity` and `join_group`:
   - `TgData._account_health_operation` opens `ConnectionEngine._account_operation(expected_account_id)`. That is a fresh client with strict options (no retries, no auto-reconnect, no updates) that proves the expected account with a self request before any work.
   - The work runs in `group_operations` / `group_profile` / `group_activity` on that handle.
   - Health is recorded by an owned, fixed-account monitor (`owned_health`), and notifications run after the client is cleaned up.
5. **The pool read** (`AccountPool.read` / `get_message_batch`). A pool-state document (async `load` / CAS, `pool_state`) records each account's waits, repairs and per-group restrictions. A read then:
   - preflights the sessions, refusing duplicates;
   - admits one attempt per account in that document;
   - runs `_OwnedSource.run`, which verifies identity and uses its `BatchEngine`;
   - settles the outcome — ok, waiting, transport, no access, logged out and so on, classified by `health` — then tries the next eligible account.

   Results come with provenance (`PoolReadResult`) and a caller-retained capture.
6. **The worker** (`tgdata-worker`, `worker.py` / `worker_engine.py` / `worker_protocol.py`):
   - JSON-line jobs come in on stdin, from a trusted local inventory of accounts and budgets;
   - each job runs serially on one `TgData` per account, through the verified-operation path;
   - result and health frames go out, size-bounded.
7. **Login** (`LoginFlow`, `tgdata-login`):
   - each step (phone, code, password) builds a short-lived auth-only client through `_new_client`;
   - its progress is an exportable secret checkpoint, bound to the config (api id, proxy, identity);
   - the result is session text, which `login_file` publishes atomically as a native `.session` file.

## 4. Cross-cutting abstractions

- **Health** (`health.py`). `classify()` maps Telegram's own error names to verdicts: waiting, logged out, banned, restricted, no access, unclassified. Two attribution styles coexist:
  - **legacy ambient calls** — a context variable for "which public call, in which task"; engines call `report()` at handled or swallowed errors; a logging filter captures Telethon's silent sleeps;
  - **owned calls** — `_OwnedCall`, which records evidence at the client boundary.

  Observers never raise into the observed work.
- **Budgets.** `ReadBudget` and `JoinBudget` are SQLite ledgers keyed by verified account id. A request is reserved before it is sent and settled after, at Telethon's sender seam.
- **Stores are opaque-text, compare-and-swap.** Sync, backfill and pool state all use the same contract, so the caller owns persistence and tgdata owns correctness.
- **Context variables** carry scoping that must follow tasks: health calls, heartbeat scopes, the per-call flood threshold, pool scopes, the worker's current job. Several are owner-task checked.

## 5. Patterns, and how consistently they're applied

- **A facade over engines** (`TgData` → engines), with the connection engine as a single gateway. This is consistent.
- **Interception by mixins at Telethon's request seam**, rather than wrapping every call site. Consistent, and the reason features compose: budget, join, heartbeat, evidence and flood all work on every path.
- **Explicit ownership and lifetimes** in the newer code: owned tasks, shielded cleanup, "never detach work", credential-free errors, fail-closed defaults. It is thorough, dense and heavily commented. The older modules (`message_engine`, `discovery_engine`, the legacy `ConnectionPool`) are looser and older in style.
- **In transition:**
  - Two health models: legacy ambient vs owned.
  - Two read stacks: DataFrame vs `MessageBatch`.
  - Two multi-account mechanisms: the old in-engine `ConnectionPool` round-robin vs `AccountPool`.
  - The newer code pins Telethon 1.45.0 exactly (`AccountPool`, `Worker`), while package metadata says `>=1.45,<2.0` and lists old Python versions.

  New work should follow the newer layer's conventions.

## 6. Where to look first

`connection_engine.py`, then `tgdata.py`, `session_store.py`, `health.py`, `batch_engine.py` / `message_batch.py`, `account_pool.py` / `pool_source.py`, and `login.py`. Tests live in `tgdata/smoke_tests/`, numbered by feature. Most run offline against Telethon's real request code with a scripted connection.
