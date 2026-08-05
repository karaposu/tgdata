# Trace 1 — Telegram Client Lifecycle

**Category:** Lifecycle
**One-liner:** How the underlying Telethon `TelegramClient` is born, connected, used, torn down, and closed — and why "torn down" happens far more often than the design intends.

---

## Entry Point

Any operation that needs Telegram. The first call to `ConnectionEngine.get_client()` (`connection_engine.py:133`) is the birth event. In practice it's reached the first time `TgData.list_groups()`, `get_messages()`, `get_message_count()`, or `search_messages()` runs, because each of those opens with `client = await self.connection_engine.get_client()`.

The terminal event is `ConnectionEngine.close()` (`connection_engine.py:323`), normally reached via `TgData.close()` (`tgdata.py:398`) or the async context manager `__aexit__` (`tgdata.py:572`).

## Execution Path

1. **Lazy creation.** `get_client()` checks whether a health check is due (see trace 8), then — for the default `pool_size == 1` — falls through to `_init_primary_client()` (`connection_engine.py:157`) on first call.
2. **Config load.** `_load_config()` parses `config.ini` once and memoizes a `ConnectionConfig` (`connection_engine.py:102`).
3. **Client construction.** A `TelegramClient` is built with the session name = `config.username` if set, else `config.session_file` (`connection_engine.py:161-167`). Note the comment: *"Use username as session name for compatibility with original code."*
4. **Connect + authenticate.** `_connect_with_retry()` calls `client.start(phone=...)` (`connection_engine.py:204`). Telethon either resumes from the `.session` file or performs interactive login.
5. **Use.** The client is returned. **Every call site immediately wraps it in `async with client:`** (`tgdata.py:84`; `message_engine.py:86,279,314`).
6. **Teardown per operation.** Telethon's `TelegramClient.__aexit__` calls `disconnect()`. So the moment an operation finishes, `_primary_client.is_connected()` becomes `False`.
7. **Reconnect on next call.** The next `get_client()` sees `not self._primary_client.is_connected()` (`connection_engine.py:152`) and runs `_connect_with_retry()` again — re-calling `start()`.
8. **Final close.** `close()` disconnects the primary client (or the pool) and nulls the references.

The object graph therefore has a long-lived **client instance** (created once, cached in `self._primary_client`) but a short-lived **connection** (opened and closed on every single operation).

## Resource Management

- **Session file** (`<username>.session`, a SQLite DB) is the durable resource; it survives process death and is Telethon's job to manage.
- **The socket/connection** is the volatile resource, and it is explicitly opened and closed by the `async with` blocks — not held.
- **The client object** is cached but never re-created; only reconnected.
- `close()` is the only explicit teardown; if a caller forgets it and doesn't use `async with TgData(...)`, the client is dropped at GC with the connection already closed (usually harmless, since each op already disconnected).

## Error Path

- Connect failures raise `ConnectionError` from `_connect_with_retry` (`connection_engine.py:220`) — except `FloodWaitError`, which is slept off and retried once inline (`connection_engine.py:207-216`).
- If `start()` needs interactive input in a non-interactive run, it blocks on stdin — a latent hang, not an error.

## Performance Characteristics

- **Reconnect-per-operation cost.** Because every op tears down the connection, every op pays a fresh `start()` — an authorization round-trip to Telegram — before doing any real work. For a workload of many small calls (e.g. a polling loop calling `get_messages` every interval, trace 10), this is pure overhead repeated forever.
- The health-check gate (trace 8) adds a `get_me()` round-trip at most every 5 minutes.
- Single connection means no parallelism across operations by default.

## Observable Effects

- A `.session` file appears/updates on disk.
- Repeated "Successfully connected and authenticated!" log lines (`connection_engine.py:205`) — one per operation, which is itself a tell that reconnection is happening constantly.
- Network: a connect/handshake/disconnect cycle per call.

## Why This Design

The intent is clearly a **long-lived, reusable client** — that's why it's cached in `self._primary_client`, why `is_connected()` is checked, why there's a pool and a periodic health check. The `async with client:` blocks appear to have been copied from Telethon's own quick-start examples (where a script opens a client, does one thing, and exits) into a library context where the client is meant to persist. The two idioms were never reconciled after the refactor from the older multi-class design.

---

## What feels incomplete

**The issue.** The persistence machinery is only half-wired: the client is cached and reconnect logic exists, but the per-call `async with client:` teardown means the connection is never actually reused. The lifecycle "birth-to-death arc" the design implies (connect once, use many times, close once) is never realized — it's really "connect, use once, disconnect" repeated N times.

**ELI15.** Imagine renting an office, and every time you want to do one task you unlock the door, do the task, then lock up and hand back the key — then rent the *same* office again five seconds later for the next task. You kept the lease (the client object), but you never actually stayed inside (the connection). All the "keep the office ready" effort is wasted.

**Impact.** Every operation pays reconnect latency; the connection pool and health-check cadence are rendered pointless; log noise; and in a tight polling loop the overhead is continuous. No correctness bug — just wasted work and a design that doesn't do what it looks like it does.

**Robust Fixes / Best Practices.** Pick one idiom and commit. Either (a) make the client genuinely persistent: connect once in `get_client()`, drop all the `async with client:` blocks at call sites, and rely on `close()`/`__aexit__` for teardown; or (b) make it genuinely per-call: stop caching `_primary_client`, and create+`async with` a fresh client each op (simpler, but slower). Option (a) matches the existing design intent and is the right call.

**Architectural Fix.** Introduce a single `async with self.connection_engine.session() as client:` context manager owned by `ConnectionEngine` that yields the *already-connected persistent* client and does **not** disconnect on exit (only `close()` disconnects). All call sites use that instead of `async with client:`. This centralizes the lifecycle in one place and removes the teardown from the message layer entirely. *Not overkill* — it's a small, high-leverage change that also fixes traces 8 and 12.

**Speculative defence.** The `async with client:` pattern is the single most-copied snippet in Telethon tutorials, and it *works* (tests pass, messages come back) — so nothing screamed "bug." Under `pool_size == 1` and light manual testing, the reconnect cost is invisible. The refactor notes ("delegating to specialized engines") suggest the author was focused on structure, not connection semantics, and the two layers were written/copied at different times without a joined-up view of the socket lifecycle.

**Is this worth fixing?** Yes — medium-high priority. It's the root cause behind traces 8 and 12 and the cheapest single change with the widest benefit.

## What feels vulnerable

**The issue.** Interactive `client.start(phone=...)` in `_connect_with_retry` (`connection_engine.py:204`) can block on stdin for a login code. In any non-interactive context (cron, server, the "smoke tests" run headless) the first connection with no valid session will hang indefinitely rather than fail fast.

**ELI15.** The program sometimes stops and waits for a human to type a text-message code. If nobody's sitting at the keyboard — like when it's running on a server at 3am — it just waits forever instead of saying "I can't log in."

**Impact.** A missing/expired session turns a startup into a silent hang. Combined with the reconnect-per-op behavior, a session that expires mid-run could convert every subsequent operation into a hang.

**Robust Fixes / Best Practices.** Pre-check authorization with `client.is_user_authorized()` and, if false in a non-interactive context, raise immediately with a clear message. Support session-string auth (already researched in `expansion_auth_features.md`) so headless deploys never need stdin. Add a connect timeout.

**Architectural Fix.** Split "authenticate" (one-time, may be interactive) from "connect" (runtime, must be non-interactive and fail-fast) into two methods; runtime paths only ever call the latter. *Slightly more than this codebase needs today*, but the `is_user_authorized()` guard is a two-line must-have.

**Speculative defence.** For the author's own use — a personal account with a long-lived `.session` file already committed to the repo — `start()` never actually prompts, so the hang is never observed. The design implicitly assumes "a valid session already exists," which is true on the author's machine.

**Is this worth fixing?** Yes for any headless/production use; low priority for personal interactive use.

## What feels like bad design

**The issue.** Session identity is derived from `config.username` ("for compatibility with original code", `connection_engine.py:161-163`), falling back to `session_file`. Using a human username as the durable session key couples the auth artifact to a display-name field and makes multi-account or renamed-account setups fragile.

**ELI15.** The program names your "keep me logged in" file after your nickname. If you change your nickname, or two people share config, the login files collide or get lost — because a nickname was used as an ID, and nicknames aren't good IDs.

**Impact.** Mostly latent: surprising `.session` filenames, potential collisions, and a config field (`username`) doing double duty as an auth key. It's a maintainability smell inherited from the pre-refactor code, not an active bug.

**Robust Fixes / Best Practices.** Use an explicit, stable `session_file` as the single source of session identity; keep `username` purely informational. Document that the session file is sensitive (it currently gets committed — see the repo hygiene note in `small_summary.md`).

**Architectural Fix.** A small `SessionResolver` that maps (account) → session path deterministically. *Overkill for a single-account library* — just standardize on `session_file`.

**Speculative defence.** The comment says it outright: backward compatibility. An earlier version keyed sessions by username, and existing `.session` files on the author's disk would stop resolving if the key changed — so the compatibility shim was kept to avoid re-authenticating. It's a deliberate, if unfortunate, migration compromise.

**Is this worth fixing?** Low priority — a cleanup, not a correctness issue.
