---
model: claude-opus-5-5[1m]
effort: max
---

**Verdict: IMPLEMENT AFTER FOLDING THESE IN**

Falsifier: a live Telegram connection that refuses a session restored from a store, while it accepts the same session from its `.session` file. The restored auth key and data centre would then not be enough to resume a login.
Affordable now: no. The configured account is logged out, and the check needs a logged-in account and a live connection. Offline, the Gate 1 probe shows Telethon's real client builds its connection with the restored key — the same bytes the file would give it.

# Critique — plan for issue #5, a pluggable session store

## High-level summary

**The plan's shape holds:**
- one store-backed session class, which is Telethon's in-memory session with load, save, close, delete and copy added;
- one decision point in the function every client passes through;
- one constructor argument;
- the default path byte-identical.

The probes and a search of Telethon 1.45.0 confirm it. No code path in Telethon or tgdata assumes a SQLite session: outside its sessions package, Telethon touches `SQLiteSession` only to build one from a name.

**Four Medium findings, all inside Step 1's store-backed session.** Each is small to fix and each stands on a probe:
1. **It stores and keeps far more than a restart needs.** The in-memory session caches every entity a response carries, message senders included. For an account that scrapes, 96% of the stored string is senders: 3.4 MB rewritten on each changed minute, and about 14 MB held in memory per account. tgdata needs only the groups and channels — which is all `desc.md` promises.
2. **A failed save can write the account's credential into the error log.** The plan logs the store's exception with its traceback. Database toolkits quote their statement parameters in their errors, and that includes the session string.
3. **A newer login can be overwritten.** A client that started before a login finished saves its own fresh key over it. The desc's "the login is never lost" is not true.
4. **A plain sort makes saving fail for good.** "Rows are sorted" fails as soon as one room is cached both with a username and without one. Every save after that fails, a new auth key included.

**Three Lows:**
- a synchronous store blocks the event loop;
- the string's raw 64-bit integers do not survive a store that parses JSON as floats;
- the connect-time saves are not exercised by an offline test.

## Premise Inventory

**What was checked:**
- the plan's Gate 1 list;
- the desc's claims;
- every Telethon behaviour the plan builds on — save, close, delete, `connect()`'s restore, and the constructor;
- whether anything assumes a SQLite session.

The behavioural premises are about deterministic code: Telethon's and Python's. Only the first involves Telegram itself.

**Premises, ranked by waste if false:**

1. **Premise:** Telegram resumes a login from a restored auth key and data centre exactly as it does from a `.session` file.
   - **First dependent step:** Step 1.
   - **Waste if false:** Steps 1–6.
   - **Test scheduled at:** never live.
   - **Cheapest earlier test:** a live connection on a logged-in account with a store. Not affordable now: the configured account is logged out.
   - **Coverage:** **non-covering** for Telegram's side, because the scripted connection supplies Telegram. The client side is covered: the Gate 1 probe shows `client._sender.auth_key.key` equals the restored bytes.
2. **Premise:** Telethon saves on connect and on a new auth key, and on every disconnect it flushes and then calls `close()`. That is `telegrambaseclient.py` lines 558, 572, 754–756 and 792, and `updates.py` 552–554.
   - **First dependent step:** Step 1.
   - **Waste if false:** the saving design.
   - **Test scheduled at:** Step 4, test 4 — the disconnect path and `_auth_key_callback`.
   - **Coverage:** covering for disconnect, through the real client in the Gate 1 probe. The two `connect()` saves are covered by reading only — see Risk 7.
3. **Premise:** the in-memory session's whole entity set is what a restart needs.
   - **First dependent step:** Step 1.
   - **Result:** **refuted for size by P1** — Risk 1. The probe was affordable, and has now run.
4. **Premise:** two clients of one stored session never lose the login (desc criterion 7).
   - **Result:** **refuted by P3** — Risk 3.
5. **Premise, given by the maintainer:** Telethon copies a session for side connections with `clone()` and no arguments.
   - **First dependent step:** Step 1's override.
   - **Waste if false:** one method.
   - **Test:** Step 4, test 8. That tests the override's behaviour, not Telethon's call site, which is not re-verified, by direction.

**Rule check:** no affordable earlier test is scheduled after its first dependent step. The affordable ones, P1 and P3, ran in this critique and produced Risks 1 and 3.

## Restart Check

Not applicable. `desc.md` gives a missing capability as the reason for this work, not a prior failure or incident. The constraint it inherits from `c72eab4` — a failed load must never look like a first login — is covered under Inherited Lessons.

## Inherited Lessons

| Lesson (triage's watch-for items, the desc, `c72eab4`) | Where the plan satisfies it |
|---|---|
| 1. Save at close | Step 1's `close()` → `save()`; the Gate 1 probe through the real client |
| 2. The whole session, not the string format | Step 1 stores the session's state. **But "whole" overshoots the group cache** — Risk 1 |
| 3. A failed load raises, and never looks like a new session | Step 1's `__init__`, Step 2's load inside `_new_client()`, Step 4 test 5 |
| 4. Two clients, one stored session | **Not satisfied.** No guard, and the desc claims the login is never lost — Risk 3 |
| 5. Log-out → `delete()` | Step 1's `delete()`; Step 4 test 7 |
| 6. Sync or async | Sync, by decision. **The event-loop consequence is undocumented** — Risk 5 |
| 7. The default is byte-identical | Step 2 passes the same string; Step 4 test 3 |
| `c72eab4`'s first-login rule | unchanged: an empty store gives `auth_key is None`; Step 4 test 6 |
| The maintainer's "keep it simple" | every Medium's selected fix stays within Step 1 |

---

## Risk 1 — The stored session holds every message sender, so it grows without bound

### Risk

To save an account's session, the plan saves everything Telethon's in-memory session holds. That includes Telethon's cache of every user whose message the account ever read, not only the groups and channels tgdata needs to reopen after a restart.

An account that scrapes busy groups meets tens of thousands of message authors. Its saved session then becomes mostly authors: megabytes rewritten in full on every changed minute, and many megabytes held in memory per account. For a server holding many accounts — the reason this feature exists — that is memory and storage traffic spent on data nothing reads back. The description only promises the cache of groups and channels.

**Precisely.** The plan's `StoredSession` extends `telethon.sessions.MemorySession`. Its `process_entities()` adds a row for every user and chat in each response (`memory.py`, `_entities_to_rows`), and Telethon calls it after every request (`client/users.py`, `_call`). Step 1 dumps the whole `_entities` set on every changed `save()`.

P1, on the plan's own prototype:

```
        0 senders + 2000 groups: string 0.15 MB, dump 1 ms, in memory ≈0.7 MB; zlib 0.03 MB in 3 ms
    50000 senders + 2000 groups: string 3.39 MB, dump 56 ms, in memory ≈14.4 MB; zlib 0.94 MB in 103 ms
   rows a restart needs for groups (channels, chats, the self row): 2001 of 52001
```

tgdata reads the session's cache only through:
- discovery's `client.session.get_input_entity(ref)`, which resolves groups and channels;
- Telethon's `connect()`, which reads the id-0 self row and the account's own user row.

Message senders come with their messages. `msg.get_sender()` and `download_profile_photo(sender)` use the response's own entities, never the session cache.

Telethon's file session keeps users too, but on disk with incremental inserts. The store-backed session keeps them in memory, and rewrites all of them each time.

### Severity

Medium

### Category

Performance: memory and write amplification

### Impact

- About 14 MB of memory per scraping account, growing without bound.
- A multi-megabyte rewrite of the store on each changed minute, plus about 56 ms of event-loop time to build it.
- Multiplied by every account in a process.

### NoobEng

Persist what a restart reads. For tgdata that is groups, channels and the account's own rows, not every user a response mentioned. The in-memory session offers a hook, `_entity_values_to_row`, documented as overridable, where a row can be declined.

### Affected areas

`tgdata/session_store.py` (Step 1); the desc's criterion 3 wording; the README section

### Mitigation

#### Mitigation — Quick

Compress the stored string with zlib. The write shrinks from 3.4 MB to about 0.94 MB, but memory and dump time stay, and compression adds about 100 ms.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

Keep only the group cache. `StoredSession` overrides `_entity_values_to_row` to decline user rows — marked id above 0 — except the account's own:
- **Kept:** groups, channels, the id-0 self row, and the user row whose id equals the self id that the id-0 row carries. The self id is tracked when the id-0 row is processed or restored.
- **Never stored:** message senders, which never enter memory either.
- **Size:** bounded by the groups the account knows — 0.15 MB and 1 ms for 2,000 groups.
- **Docs:** desc criterion 3 and the README say "groups and channels".
- **Test:** a session fed a response with many users keeps none of them, keeps its own row, and still restores the self id at `connect()`.

**Why this is robust:** it removes the growth where it starts, at insert, so memory and the stored string are both bounded. It is the cache the desc promised and the only one tgdata reads.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* No class: only the stored session persists, so long-term collapses to robust. Robust bounds memory, size and CPU at insert, in a few lines, and matches the desc's group cache. The quick fix only shrinks the write, and adds CPU.
*For future:* —

#### Mitigation — Long-term

Incremental persistence: a store interface with per-row upserts, so only changed rows are written, like Telethon's file session. That means a richer interface and more store methods.

**Why this is long term effective:** writes become proportional to change, not to size, for any future cache tgdata decides to keep.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Per-row upserts would make writes proportional to change. Worth it only if tgdata ever needs to keep users across restarts, or if groups alone grow large.

---

## Risk 2 — A failed save can write the account's credential into the error log

### Risk

The saved session contains the account's secret login key: whoever has it has the account. When the application's storage refuses a save, the plan logs the storage's error message and its traceback. Common database toolkits put the values they tried to write into that message, truncated or not. So part or all of the secret key lands in the application's error log, and from there in log files, log shippers and error trackers.

**Precisely.** Plan Step 1: "Any exception … is logged on `tgdata.session_store` at ERROR every time, with its traceback and the session name". SQLAlchemy's `StatementError`, for example, appends `[parameters: …]` with each long value cut to its first and last 150 characters. In the plan's JSON the auth key starts about 70 characters in.

P2 used a store that raises like such a driver. The probe supplies the driver's text; the logging is the plan's:

```
P2 — what the plan logs when a store's save fails the way DB toolkits fail
   the ERROR record contains 70 of the auth key's 344 base64 characters
```

A toolkit that does not truncate leaks the whole key. `TgData(log_file=…)` writes ERROR records to a file.

### Severity

Medium

### Category

Security: credential exposure in logs

### Impact

The account's auth key — fragments, or all of it — is written to log files and anything that collects them.

### NoobEng

When the payload is a credential, log that the operation failed and the error's type, never the error's text. Driver messages are not under your control.

### Affected areas

`StoredSession.save()` and `delete()` logging; the README's failure section

### Mitigation

#### Mitigation — Quick

Drop the traceback from the ERROR record. The message would still include the error's text, so this only narrows the leak.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

Log a failed save, or a failed delete, with the session name and the exception's *type* only, never its text and never a traceback. For example: `Could not save session 'acct' to the session store (OperationalError) — retried at the next save point`.

The store owner can wrap their own store to see more. A Step 4 test runs a store whose error quotes its arguments, and checks that no part of the auth key appears in any captured record.

**Why this is robust:** tgdata's own logging never carries the credential, whatever any store's error contains, and a test holds it.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* No class: the session string exists only inside StoredSession, and a failed load carries only the name. One line plus a test keeps the credential out of every log tgdata writes.
*For future:* —

#### Mitigation — Long-term

A redaction filter on tgdata's loggers that masks the session string and the auth key in any record, from any path.

**Why this is long term effective:** a future log line elsewhere cannot leak it either.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* A redaction filter would guard paths that do not exist today. Revisit if another code path ever handles the session string.

---

## Risk 3 — A client that started before a login can overwrite it

### Risk

Several connections can share one stored session: the main one, a short-lived lookup connection, or a second program. The plan lets whichever saves last win, and the description promises that this never loses the login, because both connections carry the same one.

That holds only if both started after the login existed. If a connection starts before a login is made — or keeps running while someone logs the account in again by hand — it holds a different key. Its next save replaces the fresh login. Nothing reports it. The next start finds a key Telegram does not recognise, and the account owner has to log in again, with a code.

**Precisely.** Step 1's `save()` writes whenever its own dump changed, with no regard to what the store now holds. Desc criterion 7 says "Both carry the same login, so the login is never lost". P3 runs two `StoredSession`s on one name, both loaded while nothing was stored:

```
P3 — a client that started before a login, saving after it
   stored key is the login's (k1): False; the other client's fresh key (k2): True
```

In tgdata this arises when:
- `ConnectionEngine.ephemeral_client()` — a use-and-close client applications call — is built while a first login is in progress;
- a second process uses the same store and name;
- or Telethon regenerates a key that the server forgot, and saves it, after a login was made elsewhere.

Telethon's file session writes the auth key only when it changes in that process, so the file is less exposed.

### Severity

Medium

### Category

Correctness: credential overwrite; specification drift (desc criterion 7)

### Impact

A fresh login is silently replaced by a dead key. The next start raises "logged out", and the owner must log in again.

### NoobEng

A whole-record store needs the read-before-write check that row-level files get for free: do not overwrite a login you did not load or make.

### Affected areas

`StoredSession.save()`; desc criterion 7; the README's "two clients" paragraph

### Mitigation

#### Mitigation — Quick

Correct the words only. Desc criterion 7 and the README drop "the login is never lost" and say: "make a login with no other client of that session running; a client started before the login can overwrite it".

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

Check before writing:
- Each `StoredSession` remembers the auth key it last loaded or wrote.
- Before a write, it calls `store.load(name)`.
- If the stored auth key differs from the one it last synced, it skips the write and logs a WARNING once: the session was logged in elsewhere, and is not overwritten.
- Otherwise it writes, and records the new key.

The cost is one extra load per actual write — small once Risk 1 bounds the string. Desc criterion 7 is restated to match. Step 4 tests both P3's race and a stale client after a login made elsewhere.

**Why this is robust:** a newer login can never be replaced by a client that did not see it. The two-clients-same-login case is unchanged: the later save still wins for the cache.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* It closes the realistic overwrites — a client started before a login, a stale process — with one load per write, keeping the two-method store interface. Long-term would grow the interface, against the maintainer's "keep it simple".
*For future:* —

#### Mitigation — Long-term

A compare-and-set in the store interface — `save(name, data, expected=…)`, atomic in the store — which also closes the window between the load and the save.

**Why this is long term effective:** it is exact under true concurrency, enforced where the data lives.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* A store-level compare-and-set would also close the millisecond window between load and save. Revisit if two processes writing one session at once proves to be real use.

---

## Risk 4 — "Rows are sorted" breaks every later save once a room loses its username

### Risk

To avoid re-writing an unchanged session, the plan builds the saved text the same way every time, by sorting the cached rows. But a room cached once while public, with a username, and again after going private, without one, leaves two rows that a plain sort cannot order: Python refuses to compare text with nothing.

The save then fails. Because a failed save is logged and swallowed, every save after it fails too, for as long as the program runs. That includes the one that would store a new login key.

**Precisely.** Plan Step 1 says "Rows are sorted, so the same state always gives the same string", with no key. `MemorySession.process_entities()` unions rows, so one entity can hold `(id, hash, 'publicroom', None, 'Room')` and `(id, hash, None, None, 'Room')`. The probe, through Telethon's own `MemorySession`:

```
rows for one room: [(-1000000000055, 777, 'publicroom', None, 'Room'), (-1000000000055, 777, None, None, 'Room')]
plain sorted() raises: '<' not supported between instances of 'str' and 'NoneType'
```

`sorted(self._entities)` inside `save()` would raise `TypeError` at every save point from then on, logged at ERROR, and the session would never be stored again.

### Severity

Medium

### Category

Plan detail too high-level for a delicate step; silent persistence failure

### Impact

Saving stops for good after a common event — a group going private, a user dropping a username. A later auth-key change is then never stored, and the login is lost at the next start.

### NoobEng

Rows mix `None` and strings. Sort them with a key that orders any row, such as the row's JSON or `repr`, never with the rows themselves.

### Affected areas

`StoredSession._dump()` (Step 1); Step 4

### Mitigation

#### Mitigation — Quick

Sort with `key=repr`.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

Sort rows by their JSON text — `sorted(rows, key=json.dumps)`, the same form they are stored in. The same applies to the update-state rows. Step 4 adds a test: a room seen public, then private, saves and restores both rows, and the string is identical across two dumps.

**Why this is robust:** any row is orderable, the order is stable across processes, and a test pins the exact case.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Any row becomes orderable with a stable key, in one line, and a test pins the exact case. The update-state rows use the same key. There is no other mixed-type sort to generalise over.
*For future:* —

#### Mitigation — Long-term

Keep one row per entity, the latest replacing the earlier, as Telethon's file session does. Mixed rows never arise and a renamed room stops adding rows. It needs a `process_entities` override keyed by id.

**Why this is long term effective:** the cache stays one row per entity, which also removes the duplicate-row growth.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* One row per entity would also stop renamed rooms from adding rows. Risk 1's fix already bounds the cache, so this matters only if duplicates ever cause trouble.

---

## Risk 5 — A slow store blocks every account in the process

### Risk

The store's methods are plain, by the maintainer's decision, and they run inside the program's event loop. While a save is in progress, nothing else in that program runs: other accounts, Telegram's keepalive, update handlers.

**Precisely.** Telethon calls `session.save()` in `connect()`, in the updates loop and at close, all on the event loop. P5, with a store that takes 0.5 s:

```
   longest gap between 10 ms ticks: 507 ms
```

### Severity

Low

### Category

Performance: event-loop blocking — a documented consequence of a decision

### Impact

Stalls equal to the store's latency, once per changed minute per account.

### NoobEng

The README must say the methods run on the event loop and should return quickly — a local database, or an in-memory write-behind cache.

### Affected areas

README; the `TgData` docstring

---

## Risk 6 — The string's large numbers break in a store that parses JSON as floats

### Risk

The saved text is JSON with 64-bit access hashes written as plain numbers. A store that reads it as JSON instead of keeping it as text — some ORMs, JavaScript layers, query tools — turns those numbers into floating point and silently changes them. The restored session then holds wrong access hashes, and those rooms fail with "no access" after a restart.

**Precisely.** P4: of 1,000 realistic access hashes read back with `parse_int=float`, 991 changed; for example `-2255621593168970683` became `-2255621593168970752`.

### Severity

Low

### Category

Data contract

### Impact

Rooms unreadable after a restart, in setups whose store parses the string.

### NoobEng

Make the string opaque — base64 of the JSON, the way Telethon's own `StringSession` is — or say plainly: store it as text, never parse it.

### Affected areas

`StoredSession._dump()` and `_restore()`; the README

---

## Risk 7 — The connect-time saves are covered by reading only

### Risk

The description promises a save when the client connects. The planned tests run the save at disconnect and at a new auth key through Telegram's library itself, but not the two saves inside connecting, which the plan has only read.

**Precisely.** Step 4 test 4 covers `_disconnect_coro` → `close()` and `_auth_key_callback`. The `connect()` saves at `telegrambaseclient.py` 558 and 572 need a scripted sender with a `connect()` method.

### Severity

Low

### Category

Test coverage

### Impact

A future Telethon that changes `connect()`'s saving would pass the suite.

### NoobEng

A scripted sender whose `connect()` returns `True` lets the real `connect()` run its two saves offline.

### Affected areas

Step 4
