---
model: claude-opus-5-5[1m]
effort: max
---

# Plan — load and save sessions through a pluggable session store (issue #5)

**Revision 2.**

**Critic folded:** 2026-10-05.
- **What the critic reviewed.** `critic.md` (`cf7a745`) reviewed revision 1, the 6-step plan at `391ddde`. Its findings were applied in rewriting it into these 5 steps (`2f09596`), and this revision tags them.
- **The four Medium mitigations,** all robust (Risks 1–4), changed Steps 1, 3 and 4. No step was added.
- **Two Lows were taken,** because each costs a line:
  - Risk 5 — the README says a store runs on the event loop;
  - Risk 6 — the stored string is opaque.
- **One Low is consciously left:** Risk 7 — the two connect-time saves are covered by reading Telethon's code, not by an offline test.
- **The sent-file cache is not stored.** Telethon 1.45.0's client never calls `cache_file` or `get_file`.

## What is the task

Let an application keep each account's Telegram session wherever it keeps its data, instead of in a `.session` file. It passes one object, the store, with `load(name)` and `save(name, data)`, plus an optional `delete(name)`. tgdata then builds every client of the account on a session that loads from that store and saves back to it. The code that uses the account does not change, and without a store nothing changes at all.

The maintainer asked for it simple: store the sessions; no encryption, no migration, sync methods. Before the plan was written, the maintainer also flagged four risks, which the plan designs in:
1. an unbounded cache of message senders;
2. the credential leaking into logs;
3. a stale client overwriting a login;
4. a sort that breaks on rows mixing text and `None`.

## Huge Hard Blockers

### Planning Blockers

None open. Two questions were closed before any step was written:

- **Question:** Does the oldest Telethon tgdata supports, 1.33, keep the same session state and save at the same points?
  - **Why the steps can't survive it:** a different state or different save points would change Step 1's whole format and save logic.
  - **Status:** CLOSED — dropped by the maintainer on 2026-10-05: design and verify on Telethon 1.45.0 only. Desc criterion 9 now says so.
  - **Source:** inherited from `desc.md` (its `[ASSUMPTION]`).
  - **Who can close it:** the maintainer — closed.
- **Question:** Does Telethon copy a session for a side connection, and how?
  - **Why the steps can't survive it:** if a copy were store-backed, a side connection would save its own login over the account's.
  - **Status:** CLOSED — taken as given by the maintainer on 2026-10-05. For side connections such as media from its CDN, Telethon builds a copy with `clone()`, which constructs the session class with no arguments. The stored session's `clone()` therefore returns a fresh in-memory session that never touches the store. That is what the file session's own copy is: `SQLiteSession()` with no name lives in memory.
  - **Source:** found in Telethon's code by an earlier run; confirmed by the maintainer.
  - **Who can close it:** the maintainer — closed.

### Execution Blockers

None identified. Pushing, the PR and merging follow the process: the merge waits for the maintainer.

## How this implementation moves toward desired state

**Today.** `ConnectionEngine._new_client()` always hands Telethon the configured session *name*, and Telethon turns a name into its SQLite `.session` file. That one function builds every client tgdata opens: the persistent client, each pool connection and the use-and-close client.

**The bridge** is one new session class, `StoredSession`, in `tgdata/session_store.py`. It is Telethon's own in-memory session, which already does all the session work, plus four things:
1. **It loads its state from the store when built.**
2. **It saves that state back** whenever Telethon saves, and at close.
3. **It keeps only what a restart needs.**
4. **It never overwrites a login it did not load or make.**

`_new_client()` passes a `StoredSession` instead of the name when a store is configured; otherwise it passes the name exactly as today.

**Evidence on 1.45.0** comes from this step's probe, `probe_store_session.py` in the session scratchpad, run through Telethon's real client:
- **P1, the row shape.** A cache row is `(marked_id, access_hash, username, phone, name)`, e.g. `(-1000001234567, 987654321, 'someroom', None, 'Room')`.
- **P2, the login.** The client's sender took the stored auth key, and the data centre came back.
- **P3, the cache.** A discovered room is read from the restored cache, by username and by id, with no lookup.
- **P4, update states.** They come back intact.
- **P5, disconnect.** It saves, through `close()`, even on a client that never connected.
- **P6, a failed save.** It raises nothing.
- **P7, the copy.** `clone()` returns a plain `MemorySession`, and its saves never reach the store.
- **P8, an empty store.** It gives a brand-new session, with `auth_key` `None`.
- **The other shapes.**
  - The sent-file cache maps `(md5, size, kind)` to `(id, access_hash)`, but Telethon 1.45.0's client never calls `cache_file` or `get_file`, so it is not stored.
  - Update states are Telethon `State` objects.
  - `connect()` reads the account's own id from the id-0 row and then its user row.
  - Log-out disconnects (and so saves) before `delete()`.

## High-Level Summary

| Step | Description | Expected Output |
|------|-------------|-----------------|
| 1 | `tgdata/session_store.py`: `StoredSession` — load, a bounded cache, a deterministic opaque dump, check-then-save, loud but credential-free failures, `delete`, `clone` | A session class Telethon accepts, which keeps everything a restart needs in any store |
| 2 | Wiring: `TgData(session_store=)` → `ConnectionEngine(session_store=)` → `_new_client()` | Every client of the account uses the store; the default is unchanged |
| 3 | Docs: a README section, the docstrings, the smoke-test README | Users can pass a store and know what it receives |
| 4 | Offline test `test_17_session_store.py` | Every desc criterion checked on Telethon 1.45.0 |
| 5 | Verify the offline suites, then commit | test_17, 16, 15, 14, 13 and 12 pass; commits on the branch |

---

## Step 1 — The store-backed session `[folded: Risks 1–4, robust; Risk 6, Low]`

### Proposed changes

New module `tgdata/session_store.py`. It imports only the standard library and Telethon.

**The store, documented in the module docstring and the README.** Any object with:
- `load(name) -> str | None` — the saved session, or `None` when there is none yet;
- `save(name, data: str)`;
- optionally `delete(name)`, called when Telethon logs the account out.

The methods are plain functions; tgdata never awaits them.

**`StoredSession(MemorySession)`:**

```python
class StoredSession(MemorySession):
    def __init__(self, store, name: str):
        super().__init__()
        self._store, self._name = store, name
        self._synced = None            # the string last loaded from or written to the store
        self._synced_key = None        # the login key in it (bytes) — [folded: Risk 3]
        self._warned = False
        data = store.load(name)        # a store error propagates as itself, before anything connects
        if data is not None:
            self._restore(data)        # unreadable → ValueError naming only the session, `from None`
            self._synced, self._synced_key = data, self._key_bytes()
```

- **Loading.**
  - **Nothing stored.** `None` means a brand-new session, with `auth_key` `None`, so today's first-login rules apply unchanged.
  - **A store error** propagates as itself.
  - **An unreadable string** — bad JSON or base64, a missing field, an unknown format — raises `ValueError(f"stored session {name!r} cannot be read ({type(e).__name__})") from None`. The data is never quoted, and the parse error is never chained. A failed load can never look like a new session (`c72eab4`'s guarantee).
- **The bounded cache** `[folded: Risk 1, robust]`. It overrides `_entity_to_row(e)`: a `types.User` is declined unless `e.is_self`. Kept are:
  - groups and channels;
  - the account's own user row;
  - the id-0 row Telethon writes to remember the account's id. It arrives as an `InputPeerUser`, not a `User`, so it is kept.

  Message senders never enter memory, so memory, the stored string and the dump time are all bounded by the groups the account knows. `is_self` is used rather than tracking the id from the id-0 row: on a first login the account's own row arrives before that id-0 row exists, and `is_self` keeps it anyway.
- **A deterministic, opaque dump** `[folded: Risk 4, robust; Risk 6, Low]`. `dump()` builds compact JSON with sorted keys:

  ```
  {"format": 1, "dc_id", "server_address", "port", "auth_key": base64 or null, "takeout_id",
   "entities":      [[marked_id, access_hash, username, phone, name], …],
   "update_states": [[entity_id, pts, qts, date_ts, seq, unread_count], …]}
  ```

  - **Sorting.** Every row list is sorted with `key=json.dumps`. Rows mix text and `None` — a room cached once with its username and once without — and plain `sorted()` raises on those.
  - **The stored string is opaque.** It is `"1:"` followed by the URL-safe base64 of that JSON, the way Telethon's own `StringSession` is opaque. A store that parses JSON could otherwise turn the 64-bit access hashes into floats and change them.
  - **What is not stored.**
    - The temporary auth key, as Telethon's own file does not store it by default.
    - The sent-file cache, which Telethon 1.45.0 never uses.
- **Check, then save** `[folded: Risk 3, robust]`. Telethon calls `save()` at its save points.
  1. Build the dump. If it equals `self._synced`, return: nothing changed, so nothing is written.
  2. Read the stored string, and the login key in it.
  3. If that key is not `self._synced_key` — someone else logged in, or deleted the session — do not write. Log a WARNING once: `session 'acct' was logged in or removed elsewhere — not overwritten`.
  4. Otherwise `store.save(name, data)`, and record `self._synced` and `self._synced_key`.

  This costs one extra load per real write, and none when nothing changed. Two clients on the same login keep writing, and the later save still wins for the cache.
- **Credential-free failures** `[folded: Risk 2, robust]`. Any exception while saving — the dump, the check load or the save — is caught and logged on `tgdata.session_store` at ERROR, every time. The record carries the session name and the exception's *type* only: no text, no traceback. For example: `Could not save session 'acct' to the session store (OperationalError) — retried at the next save point`. `save()` never raises into Telethon's loops.
- **`close()`** calls `save()`. Telethon flushes its last state into the session and then closes it.
- **`delete()`** calls `store.delete(name)` when the store has one, and logs a failure the same credential-free way. Telethon's `log_out()` disconnects, which saves, and then deletes.
- **`clone(to_instance=None)`** returns `to_instance or MemorySession()`: a fresh in-memory session for a side connection, which never touches the store. This is the maintainer-confirmed finding.

### Output

`tgdata/session_store.py` with `StoredSession`. It is not wired in yet.

### Safe in nature

True. A new module that nothing imports yet.

### Peripheral concepts

Telethon `MemorySession` and `_entity_to_row`, `AuthKey`, `types.updates.State`, `_SentFileType`; the save, close, delete and clone call sites; `c72eab4`'s first-login guarantee; JSON determinism; logging on `tgdata.session_store`

### Hardness Lvl

3

---

## Step 2 — Wiring

### Proposed changes

- **`ConnectionEngine.__init__(…, session_store=None)`** stores it.
- **`_new_client(session_file=None)`:**

  ```python
  name = session_file or config.session_file
  session = StoredSession(self.session_store, name) if self.session_store is not None else name
  return _client_class(TelegramClient)(session, config.api_id, config.api_hash, proxy=…, **identity)
  ```

  Without a store, the same name reaches Telethon as today. With one, the persistent client and the use-and-close client load under the configured name, and pool connections under `<name>_<i>`, as `_init_pool` already names them.
- **`TgData.__init__(…, session_store=None)`** passes it to `ConnectionEngine`. The docstrings of both constructors, and `_new_client`'s, say what a store is.
- **Unchanged:**
  - first-login detection (`client.session.auth_key is None`);
  - the login checks;
  - `device_identity()`'s in-memory probe;
  - the health identity, which names the session by the configured name;
  - `tgdata/__init__.py` — `StoredSession` stays importable from `tgdata.session_store`, and a store needs no import.

### Output

`TgData(…, session_store=store)` works end to end; the default path is byte-identical.

### Safe in nature

False. It changes the function every client goes through, although without a store it passes exactly what it passes today.

### Peripheral concepts

`ConnectionEngine._new_client`, `_init_pool` naming, `ephemeral_client`, `_init_primary_client`, `TgData.__init__`, test_13's `ce.TelegramClient` patch point

### Hardness Lvl

2

---

## Step 3 — Docs `[folded: Risks 1–3, robust; Risks 5 and 6, Low]`

### Proposed changes

- **`README.md`**, under "Authentication", gets a section, "Keeping sessions out of files". It covers:
  - the three store methods;
  - a short example store backed by a small SQLite table (clarified by the maintainer during PR preparation);
  - what is stored — the login, the data centre, update states, groups and channels with their access hashes, and the account's own rows; never message senders;
  - that the string is opaque: store it as text;
  - that a store's methods run on the event loop, so they should return quickly — a local database, or an in-memory cache that writes behind;
  - when a session is saved;
  - failures — a load error raises, and a save error is logged with its type only;
  - the two-clients rule;
  - that encrypting the string is the store's business;
  - that without a store, `.session` files work exactly as before.
- **`tgdata/smoke_tests/README.md`** gets an entry for test_17.

### Output

The option is documented where users look.

### Safe in nature

True.

### Peripheral concepts

README "Authentication" and "Logging in", smoke-test README

### Hardness Lvl

1

---

## Step 4 — Offline test `tgdata/smoke_tests/test_17_session_store.py` `[folded: Risks 1–4, robust; Risk 6, Low]`

### Proposed changes

In the style of test_14 to test_16: numbered TESTs, `Passed: N/M`, an exit code, no network and no login. The setup:
- a dictionary store that counts its calls, and can be made to fail with an error that quotes its arguments;
- clients from tgdata's own factory, so Telethon's real client code runs;
- for the login checks, test_15's stand-in client, which never opens a socket and refuses to request a code.

1. **The default is unchanged.** Without a store, `_new_client()` builds Telethon's `SQLiteSession` on `<name>.session`, as today.
2. **A store serves every client.** `TgData(…, session_store=store)` makes the engine's clients `StoredSession`s under the configured name, and pool connections under `<name>_<i>`. No `.session` file is created.
3. **The round trip, through Telethon's real client.** The auth key reaches the sender; the data centre and the update states come back; a discovered room is read from the restored cache by username and by id. The stored string is opaque: it starts with `1:` and is not JSON, and a 64-bit access hash survives it exactly.
4. **The bounded cache** `[folded: Risk 1]`. A response with 500 message senders, one channel and the account's own user stores the channel, the account's row and the id-0 row, and no sender. After a restart, the id-0 row and the own row give back the account's id the way `connect()` reads them.
5. **The save points.** `client.disconnect()` on a never-connected client saves through `close()`; an unchanged state is not written again.
6. **Failures** `[folded: Risk 2]`:
   - a store whose `load` raises makes building the client raise that error;
   - an unreadable string raises a `ValueError` that names the session only;
   - a failing `save` is logged at ERROR every time, with the error's type, and `save()` returns normally;
   - with a store error that quotes its arguments, no fragment of the auth key's base64 appears in any captured log record.
7. **Logins, with the stand-in client:**
   - an empty store with no terminal raises `AuthRequiredError(first_login=True)`, and no code is requested;
   - an empty store at a terminal runs the interactive login, and after `close()` the store holds the login;
   - a stored logged-out session raises `AuthRequiredError` (logged out), and no code is requested.
8. **Log-out**, through Telethon's real `log_out()` on a scripted connection, calls `store.delete(name)`. A store without `delete` raises nothing.
9. **Two clients** `[folded: Risk 3]`:
   - on the same login, the later save wins for the cache;
   - a client that started before a login — both loaded empty, one logged in and saved — does not overwrite it: it skips and warns once, and the stored key stays the login's;
   - a stale client after a login made elsewhere skips the same way.
10. **Mixed rows** `[folded: Risk 4]`. A room cached public, then private, saves and restores both rows, and two dumps of the same state are identical.
11. **`clone()`.** It returns a plain `MemorySession`, not a `StoredSession`. Saving or closing it never reaches the store, and `to_instance` is honoured.
12. **The health identity** names the session by the configured name when a store is used.

### Output

`test_17_session_store.py`, all passing on Telethon 1.45.0.

### Safe in nature

True — a test file.

### Peripheral concepts

the scripted-sender technique (test_14, test_16), test_15's stand-in client and terminal patch, `logging` capture, Telethon's `log_out()`

### Hardness Lvl

3

---

## Step 5 — Verify and commit

### Proposed changes

1. **Byte-compile** the touched modules.
2. **Run the offline suites:** test_17 (new), test_16, test_15, test_14, test_13 and test_12. No live tests: the configured account is logged out.
3. **Commit on `feat/5-account-session-storage`** with explicit paths:
   - code, tests and docs in one commit;
   - this work folder's documents in their own commit (§7.6);
   - the unrelated working-tree guide edit stays out.

### Output

A green offline run and the commits on the branch.

### Safe in nature

True.

### Peripheral concepts

the CONTRIBUTING process guard (commits allowed on `feat/*`), the unrelated guide edit

### Hardness Lvl

1
