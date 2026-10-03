---
model: claude-opus-5-5[1m]
effort: max
---

# Plan — load and save sessions through a pluggable session store (issue #5)

## What is the task

Let an application keep each account's Telegram session in its own storage. Today a session can live only in a `.session` file.

The application passes one object, a **session store**, to `TgData`. The store has two plain methods, `load(name)` and `save(name, data)`, plus an optional `delete(name)`. tgdata then keeps every client's session there: the whole session — login, data centre, update states and the group cache — as one string. It loads the session when a client is built, and saves it whenever Telethon saves and at close. Failures are loud.

Without a store, nothing changes. This follows the maintainer's decisions: just store the sessions — no encryption, no migration, plain synchronous methods (`desc.md`).

## Huge Hard Blockers

### Planning Blockers

None identified. Every question Gate 1 raised was settled by reading Telethon 1.45.0 and by running `probe_store_session.py` in this folder. Its 17 checks pass through Telethon's real client:

1. **Telethon takes a session object as-is.** `TelegramBaseClient.__init__` builds a `SQLiteSession` from a name or path, uses a `Session` instance unchanged, and builds a `MemorySession` from `None`.
2. **The shape of the in-memory state** (`MemorySession`):
   - `_dc_id`, `_server_address` and `_port`;
   - `_auth_key`, an `AuthKey` holding 256 bytes in `.key`;
   - `_takeout_id`;
   - `_entities`, a set of `(marked_id, access_hash, username, phone, name)` rows;
   - `_update_states`, a dict from entity id to `types.updates.State`;
   - `_files`.
3. **A restored session drives the real client.** The connection is built with the restored auth key. `connect()` reads the self-id row (id 0) and each update state's `pts`, `qts`, `date` and `seq`, and all of these round-trip.
4. **The save points, and close.** Telethon saves on connect, on a data-centre switch, on a new auth key, and once a minute from the updates loop. On disconnect it flushes into the session and calls `close()`. The probe shows a disconnect saving through `close()`, even for a client that never connected.
5. **The sent-file cache is not used.** Telethon 1.45.0 never calls `cache_file()` or `get_file()` outside the sessions package, so it is not stored (`desc.md`, amended in `fc2ca1b`).
6. **Log-out** disconnects, which closes and saves the session, then calls `delete()` and drops the session.
7. **The copy for a side connection** — taken as given, at the maintainer's direction (2026-10-03). Telethon copies a session for a side connection, such as CDN media, with `clone()`. The base `clone()` returns `to_instance or self.__class__()`: a fresh instance with no arguments. A store-backed session cannot be built that way. If its copy were store-backed, it would write the side connection's login over the account's. So the stored session's copy is a plain `MemorySession`.

### Execution Blockers

None identified. Everything runs offline.

## How this implementation moves toward desired state

Today every client tgdata builds passes through one function, `ConnectionEngine._new_client()`, which hands Telethon the session *name*.

After this plan, that function hands Telethon a **store-backed session** whenever a store is configured, and the same name as today when one is not.

The store-backed session is a new class, `StoredSession`, in a new module, `tgdata/session_store.py`. It is Telethon's own in-memory session — which already implements every session method — with four additions:
- it loads its whole state from the store when built;
- it saves that state to the store whenever Telethon saves, and at close;
- it deletes it on log-out;
- its copy for a side connection never touches the store.

Because the change sits in the one function every client passes through, the persistent client, each pool connection and every use-and-close client all get it with no other change. The login rules from `c72eab4` keep working unchanged, because they read `session.auth_key`, and an empty store answers `None` exactly as a brand-new file does.

## High-Level Summary

| Step | Description | Expected Output |
|------|-------------|-----------------|
| 1 | `tgdata/session_store.py` — `StoredSession`: load when built, save at Telethon's save points and at close, delete on log-out, a plain copy for side connections; loud failures | The store-backed session, unused yet |
| 2 | `ConnectionEngine(session_store=)` — check the store's two methods; `_new_client()` hands Telethon a `StoredSession` when a store is set, the same name otherwise | Every client of the account uses the store; the default unchanged |
| 3 | `TgData(session_store=)` passed through, with its docstring | The public option |
| 4 | Offline test `test_17_session_store.py` | Every success criterion checked offline |
| 5 | Docs: a README section, the smoke-test README, docstrings | Users can find and use it |
| 6 | Verify every offline suite, then commit | test_17 / 16 / 15 / 14 / 13 / 12 pass; commits on the branch |

---

## Step 1 — `StoredSession`, the store-backed session

### Proposed changes

A new module, `tgdata/session_store.py`. It imports only the standard library and Telethon.

Its docstring documents the store interface:

```
load(name) -> str | None     the saved session, or None when there is none yet
save(name, data: str)        keep this string under this name
delete(name)                 optional: called when Telethon logs the account out
```

The methods are plain, not coroutines (`desc.md` criterion 2).

```python
class StoredSession(MemorySession):
    """A Telethon session that keeps its state in memory, like MemorySession,
    and keeps a copy in the application's store."""

    def __init__(self, store, name: str):
        super().__init__()
        self._store, self._name, self._saved = store, name, None
        data = store.load(name)              # a store error propagates as itself
        if data is not None:
            self._restore(data)              # an unreadable string raises ValueError
            self._saved = data
```

**The stored string** is compact JSON, `{"version": 1, …}`, carrying:
- `dc_id`, `server_address` and `port`;
- `auth_key`, base64 of `AuthKey.key`, or `null`;
- `takeout_id`;
- `entities`, as rows `[marked_id, access_hash, username, phone, name]`;
- `update_states`, as rows `[entity_id, pts, qts, date_timestamp, seq, unread_count]`.

Rows are sorted, so the same state always gives the same string, even across processes where Python's hash order differs. Without that, an unchanged session would be re-written once after every restart.

**`_restore`** is the inverse:
- the auth key is rebuilt with `AuthKey(bytes)`;
- update states are rebuilt with `types.updates.State(...)`, dates in UTC;
- entity rows become tuples again;
- a missing field, a wrong type, bad base64, or an unknown `version` raises `ValueError(f"stored session {name!r} cannot be read: …")` from the original error.

**`save()`** is called by Telethon at every save point.
- It builds the string, and writes only when it differs from the last one written or loaded. The minutely save then costs a store write only when something changed. The probe measured 5,000 cached groups at 345 KB, built in about 2.6 ms.
- Any exception, from building or from the store, is logged on `tgdata.session_store` at ERROR **every time**, with its traceback and the session name, and is never raised. Telethon calls `save()` from its updates loop and from `connect()`, and a raise there would end the loop or the connection. The next save point tries again, because the last-written string did not change.

**`close()`** calls `save()`. Telethon flushes its last state into the session and then calls `close()`; `MemorySession.close()` does nothing.

**`delete()`** calls `store.delete(name)` when the store has a callable `delete`. A failure there is logged at ERROR, not raised: Telegram has already logged the session out. It also forgets the last-written string.

**`clone(to_instance=None)`** returns `to_instance or MemorySession()`. A side connection gets a plain in-memory session that never writes to the store.

**The group cache** keeps `MemorySession`'s own rules. A room that changes its username adds a second row with the same id, where `SQLiteSession` would replace the row. Both rows carry the same id and access hash, so lookups stay correct. This is rare, and the cost is a little growth.

### Output

`tgdata/session_store.py` with `StoredSession`. Nothing uses it yet.

### Safe in nature

True — a new module, not wired in yet.

### Peripheral concepts

Telethon `MemorySession` and `Session.clone`, `AuthKey`, `types.updates.State`, the save points (`connect`, `_switch_dc`, `_auth_key_callback`, the updates loop, `_disconnect_coro` → `close`), `log_out` → `delete`, `connect()`'s self-id row and update-state restore, JSON determinism

### Hardness Lvl

3

---

## Step 2 — The connection engine hands Telethon the store-backed session

### Proposed changes

**`ConnectionEngine.__init__(..., session_store=None)`.**
- When a store is given, check that `load` and `save` are callable. If not, raise `TypeError("session_store needs load(name) and save(name, data) methods")` at construction, long before anything connects.
- Keep the store as `self.session_store`.

**`_new_client(session_file=None)`:**

```python
name = session_file or config.session_file
session = StoredSession(self.session_store, name) if self.session_store is not None else name
return _client_class(TelegramClient)(session, config.api_id, config.api_hash, proxy=..., **identity)
```

**Without a store,** `name` is exactly the string that reaches Telethon today, so the default is byte-identical (criterion 1).

**With a store,** every client path gets its session from it, with no other change:
- `_init_primary_client` → `_new_client(config.session_file)`;
- `_init_pool` → `_new_client(f"{name}_{i}")`;
- `ephemeral_client` → `_new_client()`.

The load runs inside `_new_client()`, before any `connect()`. A failed load therefore raises before anything connects, and:
- `_primary_client` is never assigned;
- the pool's existing teardown, `_discard_clients`, runs as it already does for a failed pool client.

**`device_identity()`** keeps its own `StringSession` probe, unchanged.

The docstrings of `ConnectionEngine.__init__` and `_new_client()` gain one paragraph each.

### Output

Every client of the account loads from and saves to the store, under its name, when a store is configured. No `.session` file is created. The default is unchanged.

### Safe in nature

False. It changes the one function every client passes through, although the default path passes the same value as today.

### Peripheral concepts

`_new_client` and its callers (persistent, pool, use-and-close), `_client_class` and its mixins, `first_login = client.session.auth_key is None`, `_discard_clients`, session-name precedence in `_load_config`

### Hardness Lvl

2

---

## Step 3 — `TgData(session_store=)`

### Proposed changes

`TgData.__init__` gains `session_store=None`, passed to `ConnectionEngine`. The docstring states:
- the interface;
- what is stored;
- when it is saved;
- that failures are loud;
- that the default is unchanged.

Nothing is exported from `tgdata/__init__.py`. The store is any object with the two methods, and `StoredSession` is internal.

`_health_identity()` needs no change: it already names the session by the configured name (criterion 8).

### Output

The public option.

### Safe in nature

True. A keyword argument with a default of `None`.

### Peripheral concepts

`TgData.__init__`, the `ConnectionEngine` constructor, `_health_identity`

### Hardness Lvl

1

---

## Step 4 — Offline test `tgdata/smoke_tests/test_17_session_store.py`

### Proposed changes

The style of test_14 to test_16: numbered TESTs, `Passed: N/M`, an exit code, and no network or login.

Two techniques:
- **Telethon's real client from tgdata's factory, with a scripted connection.** This is test_16's `Scripted` sender. It covers save points, log-out and disconnect.
- **test_15's no-network `StandIn` client patched in for `TelegramClient`.** This covers the persistent, pool and use-and-close paths through `get_client()` and `ephemeral_client()`, with the status check scripted.

The store is a dict with `load`, `save` and `delete`, and it counts its calls.

The tests:
1. **Round trip.** Everything is restored: the data centre, the auth key, the group cache by id and by username, the self-id row, and the update states with their dates.
2. **Every client path uses the store, under its name.** The persistent client uses `<name>`, a pool of two uses `<name>` and `<name>_1`, and the use-and-close client uses `<name>`. No `.session` file appears in the temporary folder.
3. **The default is unchanged.** Without a store, the client's session is Telethon's `SQLiteSession` on `<name>.session`, the same string as today.
4. **Saved at disconnect.**
   - A new cache entry, then `await client.disconnect()` on the real client: one save, containing it.
   - Disconnecting again unchanged writes nothing.
   - Telethon's own `_auth_key_callback` saves a new auth key.
5. **Failures are loud:**
   - a store whose `load` raises makes `get_client()` raise that error, with no connect and no code requested;
   - an unreadable string raises `ValueError` naming the session;
   - a store whose `save` raises is logged at ERROR on each attempt, never raises, and the next save after the store recovers writes.
6. **Logins:**
   - an empty store with no terminal gives `AuthRequiredError` with `first_login=True`, and no code;
   - a stored, logged-in session connects with its stored auth key;
   - a stored session that Telegram logged out gives `AuthRequiredError` with `.reason` `AUTH_KEY_UNREGISTERED`.
7. **Log-out.** The real `client.log_out()`, with `LogOutRequest` answered `True`, calls `store.delete(name)`, and the entry is gone. With a store that has no `delete`, it completes without an error.
8. **The copy.** `clone()` is a plain `MemorySession`, and its `save()` and `close()` never write to the store.
9. **Two clients of one session.** Both save, the later save wins, and the stored auth key is the one both carried.
10. **Health identity.** `TgData(..., session_store=…)` names the session by the configured name.
11. **The interface check.** `TgData(..., session_store=object())` raises `TypeError` naming `load` and `save`.

### Output

`test_17_session_store.py`, all passing on Telethon 1.45.0.

### Safe in nature

True — a test file.

### Peripheral concepts

smoke-test conventions, test_15's `StandIn` and scripted status replies, test_16's `Scripted` sender, Telethon `log_out`, `_auth_key_callback`, `logging` capture

### Hardness Lvl

3

---

## Step 5 — Docs

### Proposed changes

**`README.md`** gains a section after "Logging in": "Keeping sessions somewhere else (optional)". It covers:
- the interface, and that the methods are plain;
- a short dict-backed example;
- what is stored, and that it is the whole session;
- when it is saved;
- that failures are loud;
- that two clients of one session overwrite each other harmlessly;
- that encryption, if wanted, is the store's business;
- that without a store nothing changes and `.session` files keep working.

**`tgdata/smoke_tests/README.md`** gains a test_17 entry. Step 2's and Step 3's docstrings are part of those steps.

### Output

The option is documented where users look.

### Safe in nature

True.

### Peripheral concepts

the README "Authentication" section, the smoke-test README

### Hardness Lvl

1

---

## Step 6 — Verify and commit

### Proposed changes

1. **Byte-compile** the touched modules.
2. **Run the offline suites:** test_17, test_16, test_15, test_14, test_13 and test_12, on Telethon 1.45.0. No live tests: the configured account is logged out.
3. **Commit on `feat/5-account-session-storage`** with explicit paths, keeping the unrelated working-tree guide edit out:
   - code, tests and docs in one commit;
   - the work folder's documents in their own commits (§7.6).

   Push the branch.

### Output

A green offline run and the commits on the branch, pushed.

### Safe in nature

True.

### Peripheral concepts

the CONTRIBUTING process guard (commits allowed on `feat/*`), the unrelated working-tree guide edit

### Hardness Lvl

1
