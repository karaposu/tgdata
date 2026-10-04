# Load and save sessions through a pluggable session store (issue #5)

> Session warmed at `110996c` (2026-10-03) — already warm, carried from #4 in this session, so `/arch-small-summary` and `/arch-intro` were not run. This session read `connection_engine.py`, `tgdata.py`, `message_engine.py`, `discovery_engine.py` and `health.py` in full, and Telethon 1.45.0's request, login and updates code. For this issue it also read Telethon's sessions package and every session save, close and delete call site. `devdocs/archaeology/` is unchanged.

> Implementation resumed at `0162acd` (2026-10-05). This Codex session was already warm from `/arch-small-summary`: all 41 Python source files, including the unfinished `session_store.py`, were read, along with the process hook and publishing workflow. For continuation it read the issue, the full issue-title list, CONTRIBUTING, this work folder, and Telethon 1.45.0's in-memory session, disconnect, auth-key-save and log-out implementations. No repeat architecture pass was needed under §4.1. The project card is not yet written, as the issue records. The refreshed small summary is kept in the documentation commit.

**Sources:**
- issue #5's body;
- `triage.md` — feature-heavy, traverse not needed;
- the maintainer's decisions of 2026-10-03:
  - no encryption in tgdata;
  - no helper to migrate existing `.session` files;
  - keep it simple — store the sessions;
  - today's files stay the default.

> Amended at step 2 (2026-10-05), by the maintainer's decisions: criterion 9 targets Telethon 1.45.0 only, and criterion 7 adds that Telethon's own copies of a session never write to the store. Amended again at step 2 (2026-10-05) for four risks the maintainer flagged before the plan: criterion 3 (only groups, channels and the account itself are kept), criterion 5 (no credential in logs) and criterion 7 (a login is never overwritten by a client that did not see it).
>
> Amended at the fold (2026-10-05). Criterion 3: the sent-file cache is not stored, because Telethon 1.45.0's client never uses it, and the stored string is opaque — critic Risk 6. Criterion 2: a store's methods run on the event loop and should be quick — critic Risk 5.

**Where this departs from the issue text:**
- **No encryption.** tgdata hands the store the session. A store may encrypt it on its own.
- **No migration helper.** Existing `.session` files are not converted.
- **`StringSession` is not unused.** The issue says it is imported but unused; it serves `device_identity()`'s probe. It is also not the format a store should keep — see criterion 3.

## Problem Statement

tgdata can keep an account's session only as a `.session` file. Every client tgdata builds — the persistent one, each pool connection, and the use-and-close client applications call for short lookups — is built by one function, `ConnectionEngine._new_client()`. That function always hands Telethon the configured session *name*, and Telethon turns a name into its SQLite file.

Telethon itself accepts any session object; tgdata never lets one through.

So an application that keeps its data elsewhere — a database row, a key-value store, a secrets service — cannot run tgdata without a `.session` file on disk. A server holding many accounts must manage a folder of files, each of which is full access to its account.

## User Value Proposition

An application passes one object to `TgData`, and each account's session lives where the application keeps its data. The object has two methods: load a session by name, and save it. The code that uses the account does not change. No `.session` file is written.

A restart keeps the whole session — the login, and the cache of groups and channels with the access hashes needed to read them. So it does not re-sync chat lists, re-look-up usernames (the request Telegram punishes hardest), or lose the rooms discovery found.

Without a store, nothing changes.

## Success Criteria

Each criterion is verified offline, with a store backed by a plain dictionary and Telethon 1.45.0's real client code on a scripted connection.

### 1. The default is unchanged
Without `session_store`, the same session name reaches Telethon as today. Existing `.session` files keep working. The offline suites — proxy, device identity, flood threshold, login checks and health events — pass unchanged.

### 2. A store, passed once, serves every client
`TgData(..., session_store=store)` is passed through to `ConnectionEngine`. A store is any object with:
- `load(name) -> str | None` — the saved session, or `None` when there is none yet;
- `save(name, data: str)`;
- optionally `delete(name)`, called when Telethon logs the account out.

The methods are plain functions, not coroutines. Telethon reads a session's login and data centre from synchronous code, and treats async session methods as experimental. A store over an async database wraps its own call. The methods run on the event loop, so they should return quickly: a local database, or an in-memory cache that writes behind.

Every client of the account uses the store under its name:
- the persistent client and a use-and-close client use the configured session name — `session_file`, then `username`, then the default, as today;
- pool connections use `<name>_1` … `<name>_n`, as their files do today.

No `.session` file is created.

### 3. What a restart needs is stored, and nothing more
What is saved is one opaque, versioned string — store it as text. It carries:
- the auth key and the data centre;
- the update states;
- the group cache — groups and channels with their access hashes — and the account's own rows.

The sent-file cache is not stored: Telethon 1.45.0's client never uses it.

It is not Telethon's `StringSession`, which keeps only the auth key and the data centre. A session saved by one client and loaded by a new one reads a discovered room straight from its cache, with no lookup.

Message senders are not kept. tgdata reads them from the messages they arrive with, never from the session's cache. Keeping every author a scraping account meets would grow the session without bound, so they never enter the stored session at all. The stored string is therefore bounded by the groups the account knows.

### 4. It is saved whenever Telethon saves, and at close
That means:
- on connect;
- on a data-centre switch;
- when a new auth key is made;
- once a minute while connected;
- on disconnect, where Telethon flushes its last state into the session.

### 5. Failures are loud
- **A failed load raises before anything connects.** That covers a store error, and a saved string that cannot be read. It is never mistaken for a session that was never logged in: that is what decides whether a login code may be requested (`c72eab4`).
- **A failed save is logged at ERROR every time.** It never breaks Telethon's own loops, and the next save point tries again.
- **No credential in logs.** A failed save or delete is logged with the session name and the error's type only — never the error's text, never a traceback. Store and database errors often quote the values they tried to write, and the session holds the account's login key.

### 6. Logins behave as today
- **Nothing saved yet.** When a store has nothing under the name, the session is brand-new, and today's first-login rules apply unchanged.
- **A login is stored.** A login made by hand (`interactive_login=True`, at a terminal) is saved to the store.
- **A logout still raises.** A saved session that Telegram has logged out raises `AuthRequiredError` as before.

### 7. Two clients of one session
The persistent client and a use-and-close client save independently. While both hold the same login, the later save wins for the cache, and at worst a few cache entries are learned again.

A client never overwrites or removes a login it did not load or save. Before a changed save or a delete it reads what the store holds. If the stored login key is not the one it last loaded or wrote, it skips the mutation and warns once: the account was logged in or removed elsewhere. Examples are a client that started before a login, or a second process. This applies to logout too: an older client's successful logout must not delete a newer stored login. The read and mutation are separate operations, not an atomic cross-process guarantee.

This lifecycle clarification follows PR #13's first critique (`a6deab7`): the
real logout probe preserved a replacement login during disconnect, then
deleted it through the unguarded delete path. Plan revision 3 is regenerated
around one ownership check for both mutations.

Telethon sometimes copies a session for a side connection, such as media from its CDN. That copy lives in memory only and never writes to the store, so it can never replace the account's stored login.

### 8. Health events keep their names
Events and `health_check()["health"]` name the session by the configured name, as today.

### 9. Telethon version
It is designed and verified on Telethon 1.45.0, the latest release. Older versions are not compared — the maintainer's decision, 2026-10-05.

### 10. Documented
The README says how to pass a store, what it receives, and that the default is unchanged.

## Scope Boundaries

- **No encryption.** The store receives the session as a string; encrypting it is the store's business.
- **No migration** of existing `.session` files into a store.
- **No async stores** (criterion 2).
- **No store backends.** tgdata ships the interface and the session that uses it. The application supplies the store: a dictionary in the tests, its own database in production.
- **No change to the login rules** from `c72eab4`. The store changes where a session lives, not when tgdata may ask for a code.
- **No new dependency.**
- **Not #8 or #10.** Step-by-step login (#8) and the worker (#10) may use the store; neither is built here.

## Priority Level

**Low** — P3 on the issue. By importance it is backlog: it matters once accounts are logged in and held on a server. It is being built now at the maintainer's request; the priority records importance, not order.
