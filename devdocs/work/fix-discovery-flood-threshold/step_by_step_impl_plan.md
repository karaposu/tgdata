---
model: claude-opus-5-5[1m]
effort: max
---

# Step-by-step implementation plan — make Telethon's per-request flood-wait threshold work in tgdata

**Critic folded:** 2026-10-03 — 3 mitigations (5 steps changed, 1 added)

## What is the task

Telethon documents `client(request, flood_sleep_threshold=N)` as a per-request override of the client's flood-wait threshold. In every release from 1.33.1 to 1.45.0 it ignores the value, so every wait up to 60 s is slept silently inside Telethon.

tgdata's discovery relies on that override in two places:
- every raw discovery request (`DiscoveryEngine._request`);
- every username lookup (`DiscoveryEngine._resolve`).

As a result, three documented guarantees of discovery are false for short waits: waits are visible as heartbeat ticks, `max_flood_wait` is honoured, and a wait on a username lookup is never slept through.

The task is to make the override work for every client tgdata builds, inside tgdata's own client factory, without touching Telethon. Discovery's existing wait handling then runs as written, and docs and docstrings become true. Every call that does not pass the override keeps Telethon's normal behaviour exactly.

## Huge Hard Blockers

### Planning Blockers

None identified.

### Execution Blockers

None identified. Pushing the branch, opening a PR and merging are outside this plan and are the user's decisions.

## How this implementation moves toward desired state

**Today.** `ConnectionEngine._new_client()` returns a plain `TelegramClient`. Telethon's `UserMethods.__call__` drops `flood_sleep_threshold`, and `_call` decides whether to sleep by reading `self.flood_sleep_threshold`, the client-wide property, in both of its sleep checks (`users.py:37-38` and `:121`).

**The bridge** has three parts:
1. **A mixin overrides that property, so it returns a per-call value while one is set.** The value is held in a context variable together with the task that set it.
2. **The mixin overrides `__call__`, so a per-call value applies to exactly that request.**
   - It is also passed on to Telethon, so a future Telethon that honours it natively behaves the same.
   - A request sent without its own value clears any value inherited from an enclosing request in the same task. Requests Telethon makes internally — for example to resolve a name — therefore use the normal threshold.
3. **`_new_client()` builds its clients from the mixin plus whatever `connection_engine.TelegramClient` currently is.** Every client tgdata creates — persistent, pool, use-and-close — gets the behaviour. test_13's stand-in, which replaces that module name, keeps working.

Once the client honours the override, discovery's wait logic is unchanged. Its catch sites are widened to the whole family of wait errors Telethon used to sleep for it: ordinary, premium, slow-mode and test-server waits.
- `_request`'s existing handler sleeps short waits in heartbeat slices, and raises `DiscoveryInterrupted` above `max_flood_wait`.
- `_resolve`'s lookups raise, and the existing callers skip the seed, stop resolving, or interrupt, as documented.

The offline test proves both layers, then every documentation statement about discovery's waits is made exact and checked by a grep sweep.

**Settled during planning, by probe on Telethon 1.45.0** — none of these are blockers:
- **The property hooks exist everywhere.** The property, its setter, `_call` reading it, and the `__call__` signature are present in 1.33.1, 1.34.0, 1.40.0, 1.42.0, 1.44.0 and 1.45.0. The critic confirmed by a whole-function diff that 1.33.1's sleep decisions are identical to 1.45.0's.
- **A plain context variable leaks.** A task started during the call — for example the updates loop, which Telethon restarts inside `connect()` on a data-center switch — inherits the override.
  - Probe result: that task saw 0.
  - With the owner-task guard, it sees the normal 60, while the calling task still sees 0.
- **The build-time mixin works** against `TelegramClient` and against test_13's stand-in:
  - `isinstance` holds;
  - the stand-in's `__init__` recording and refusing `connect()` are preserved;
  - the setter keeps Telethon's 24 h cap;
  - per-call 0 raises.
- **Nothing in tgdata checks a client's exact class.**
- **tgdata never imports `telethon.sync`**, whose wrappers would not cover an overridden `__call__`.

## High-Level Summary

| Step | Description | Expected Output |
|------|-------------|-----------------|
| 1 | Add the per-call threshold mixin (owner-task guard; no inheritance into requests without their own value) and the class builder to `connection_engine.py`; `_new_client()` builds through it | Every client tgdata builds honours `flood_sleep_threshold=` for exactly that request; calls without it are unchanged |
| 2 | Discovery catches Telethon's whole wait family (`_WAIT_ERRORS`) at its five catch sites | A premium or other wait that Telethon used to sleep is handled by discovery as a wait, never as a generic error |
| 3 | New offline smoke test `test_14_flood_threshold.py`, Telethon level | TESTs 1–7 prove the override, independence, no side effects, the pending-wait pre-check, per-request scope, and every connection path |
| 4 | Same test file, discovery level | TESTs 8–11 prove short waits reach discovery's handlers: heartbeat and retry, interruption above `max_flood_wait`, lookups never slept, premium waits handled as waits |
| 5 | Make every documentation statement about discovery's waits exact | The engine docstrings, `DiscoveryInterrupted`, the `TgData` facade docstrings, README and guide (incl. §8) match the behaviour; the two still-silent paths are named |
| 6 | Grep sweep, run the offline suite, commit on `fix/discovery-flood-threshold` | No stale wait statement remains; test_14, test_13 and test_12 pass; one commit |

---

## Step 1 — The per-call threshold mixin and the class builder `[folded: Risk 3, robust]`

### Proposed changes

In `tgdata/connection_engine.py`:

1. **Imports.** Add `contextvars` and `functools`, and `from telethon.client.telegrambaseclient import TelegramBaseClient`. That is where the `flood_sleep_threshold` property lives in every 1.x release checked.
2. **A module-level context variable:**
   ```python
   _PER_CALL_FLOOD_THRESHOLD = contextvars.ContextVar('tgdata_per_call_flood_threshold', default=None)
   ```
   It holds `(owner_task, seconds)` while a per-call threshold is active.
3. **The mixin, `_PerCallFloodThreshold`**, with a docstring that states:
   - Telethon's defect: `__call__` drops the argument, and `_call` reads the property after a wait error;
   - the releases checked;
   - why the owner-task guard exists;
   - that a value applies to exactly the request it was passed with.

   ```python
   class _PerCallFloodThreshold:
       @property
       def flood_sleep_threshold(self):
           held = _PER_CALL_FLOOD_THRESHOLD.get()
           if held is not None:
               try:
                   if asyncio.current_task() is held[0]:
                       return held[1]
               except RuntimeError:          # read outside a running loop: no per-call value
                   pass
           return TelegramBaseClient.flood_sleep_threshold.fget(self)

       @flood_sleep_threshold.setter
       def flood_sleep_threshold(self, value):
           TelegramBaseClient.flood_sleep_threshold.fset(self, value)   # keeps Telethon's 24 h cap

       async def __call__(self, request, ordered=False, flood_sleep_threshold=None):
           if flood_sleep_threshold is None:
               if _PER_CALL_FLOOD_THRESHOLD.get() is None:          # the common path: nothing active
                   return await super().__call__(request, ordered=ordered)
               # [folded: Risk 3, robust] a request without its own value never inherits one
               # from an enclosing request in the same task (e.g. a name Telethon resolves
               # from inside that request) — exactly Telethon's documented "for this request"
               token = _PER_CALL_FLOOD_THRESHOLD.set(None)
               try:
                   return await super().__call__(request, ordered=ordered)
               finally:
                   _PER_CALL_FLOOD_THRESHOLD.reset(token)
           token = _PER_CALL_FLOOD_THRESHOLD.set((asyncio.current_task(), flood_sleep_threshold))
           try:
               return await super().__call__(request, ordered=ordered,
                                             flood_sleep_threshold=flood_sleep_threshold)
           finally:
               _PER_CALL_FLOOD_THRESHOLD.reset(token)
   ```
4. **The builder**, cached per base class:
   ```python
   @functools.lru_cache(maxsize=None)
   def _client_class(base):
       return type(f"Tgdata{base.__name__}", (_PerCallFloodThreshold, base), {})
   ```
5. **`_new_client()`.** Replace `return TelegramClient(...)` with:
   ```python
   return _client_class(TelegramClient)(...)
   ```
   - The arguments are unchanged: session, `api_id`, `api_hash`, `proxy`, identity.
   - `TelegramClient` is read from the module namespace at call time, so a test that replaces `connection_engine.TelegramClient` still controls what is built.
   - Extend `_new_client()`'s docstring with one sentence: every client also honours a per-request `flood_sleep_threshold`, which Telethon itself ignores.
   - Add the same note to the module docstring's "one door" paragraph.
6. **`device_identity()`'s probe client is not changed.** It is built without a connection and sends nothing.

### Output

`connection_engine.py` contains:
- the context variable;
- `_PerCallFloodThreshold`, whose `__call__` gives exact per-request scope;
- `_client_class()`;
- a `_new_client()` that returns a `TgdataTelegramClient`.

No public name is added, and `tgdata/__init__.py` is unchanged.

### Safe in nature

False. Every client tgdata creates changes class.
- Calls without a per-call value, with none active, take the identical path: `super().__call__(request, ordered=ordered)`, with the property returning Telethon's stored value.
- The only behavioural change is for calls that pass `flood_sleep_threshold`, and in tgdata those are exactly discovery's two call sites.

### Peripheral concepts

`ConnectionEngine._new_client` (the one door: persistent client, `ConnectionPool` connections, `ephemeral_client`), proxy and device-identity kwargs, Telethon `UserMethods.__call__` / `_call` and `TLRequest.resolve` (nested requests), `TelegramBaseClient.flood_sleep_threshold` property and its 24 h cap, `asyncio.current_task`, `contextvars`, Telethon's background tasks (updates loop, keepalive), test_13's `ce.TelegramClient` patch point, `isinstance(client, TelegramClient)`

### Hardness Lvl

2

---

## Step 2 — Discovery catches Telethon's whole wait family `[folded: Risk 1, robust]` *(new)*

### Proposed changes

In `tgdata/discovery_engine.py`:

1. **Define, next to the module's constants**, the tuple of every wait error Telethon's own sleep branch handles (`telethon/client/users.py`, `_call`). Discovery asks Telethon never to sleep, so it must handle all of them itself:
   ```python
   from telethon import errors as telethon_errors
   # Every wait Telethon's own sleep branch handles (users.py _call). Discovery
   # sends with a per-call threshold of 0, so it must handle all of them itself.
   # getattr: FloodPremiumWaitError is newer than the oldest supported Telethon.
   _WAIT_ERRORS = tuple(c for c in (FloodWaitError,
                                    getattr(telethon_errors, 'FloodPremiumWaitError', None),
                                    getattr(telethon_errors, 'SlowModeWaitError', None),
                                    getattr(telethon_errors, 'FloodTestPhoneWaitError', None))
                        if c is not None)
   ```
   Every member carries `.seconds`, so no handler body changes.
2. **Replace `except FloodWaitError as e:` with `except _WAIT_ERRORS as e:`** at the five discovery catch sites:
   - `_request`;
   - `_similar`'s seed loop — it stays before the generic `RPCError` clause;
   - `_mine_room`;
   - `_links`;
   - `linked_groups`' source resolution.
3. **Nothing else in discovery changes.** The log wording, `max_flood_wait`, `_sleep_beating` and `DiscoveryInterrupted` stay as they are.

### Output

All five discovery catch sites handle `FloodWaitError`, `FloodPremiumWaitError`, `SlowModeWaitError` and `FloodTestPhoneWaitError` as waits.
- A short premium wait on a raw request is slept with ticks and retried.
- On a `linked_groups` source it raises `DiscoveryInterrupted`.
- It is never a skipped query or a raw exception.

### Safe in nature

False. It changes how discovery treats premium, slow-mode and test-server waits.
- Today those over 60 s fall into the generic error clauses, or escape `linked_groups` raw.
- After this step they are handled as waits, which is the documented behaviour.

### Peripheral concepts

`DiscoveryEngine._request` / `_similar` / `_mine_room` / `_links` / `linked_groups`, Telethon's `FloodError` family and its `.seconds`, Telethon releases without `FloodPremiumWaitError` (1.33.x)

### Hardness Lvl

2

---

## Step 3 — Offline test, Telethon level (`tgdata/smoke_tests/test_14_flood_threshold.py`) `[folded: Risk 3, robust]`

### Proposed changes

Create `tgdata/smoke_tests/test_14_flood_threshold.py` in the style of `test_13_device_identity.py`: a module docstring listing the tests, numbered `TEST n` prints, `✓` and `✗` lines, `Passed: N/M`, and a non-zero exit on failure. Run it with `python -m tgdata.smoke_tests.test_14_flood_threshold`. The docstring also says to run it after any Telethon upgrade, because it is the canary for this workaround.

**Setup:**
- Write a throwaway config into a temp folder: dummy `api_id`, `api_hash` and `session_file` inside the temp folder; no phone; no network.
- Build clients only through `ConnectionEngine(config)._new_client()`.
- Drive Telethon's real request code by setting `client._sender` to a scripted fake connection, exactly as the probes did. Its `send()` returns futures that raise `FloodWaitError(request=None, capture=N)` or resolve to a result such as `types.updates.State(...)`.

**Tests:**
1. **The per-request option works.**
   - `await client(GetStateRequest(), flood_sleep_threshold=0)` against a 1 s wait raises `FloodWaitError` with `seconds == 1`, in under 0.5 s, after one send.
   - Print, without asserting, whether a plain `TelegramClient` honours the option. Today it does not: "Telethon ignores it — the known defect". If Telethon ever fixes it, the line reports that and the test still passes.
2. **Calls without the option are unchanged.** `await client(GetStateRequest())` against a 1 s wait sleeps at least 1 s, retries, and returns the `State`.
3. **Calls stay independent.** On one client, `asyncio.gather` runs a call with `flood_sleep_threshold=0` (`GetConfigRequest`), which raises, and a plain call (`GetStateRequest`), which sleeps and returns. A routing fake connection answers by request type.
4. **No side effects on the client:**
   - `client.flood_sleep_threshold == 60` after the calls;
   - the setter stores 5, and caps `10**9` at 86400;
   - a task started from inside the fake connection's `send()` during a call with the option reads 60, not 0 — the owner-task guard.
5. **A known pending wait is raised before sending.** After a call with the option records a 10 s wait, a second call with the option raises before anything is sent.
6. **Exact per-request scope** `[folded: Risk 3, robust]`. With a per-call value of 0 active in the current task — set through the module's context variable, standing in for an enclosing request — a plain `client(GetStateRequest())` against a 1 s wait sleeps and returns. It must not raise. Afterwards the enclosing value is intact.
7. **Every connection path builds the honouring class.** Reuse test_13's technique:
   - replace `ce.TelegramClient` with a recording stand-in that refuses `connect()`;
   - drive `ephemeral_client()`, `get_client()`, and a pool `_new_client(session + "_1")`;
   - assert three clients were built, each an instance of the stand-in and of `_PerCallFloodThreshold`, and each raising on the option;
   - restore `ce.TelegramClient` in `finally`.

### Output

A runnable offline test file with TESTs 1–7, all passing against Telethon 1.45.0. TEST 1 and TEST 5 assert behaviour, not internals, so a future Telethon that stops reading the property fails them: the upgrade canary.

### Safe in nature

True — a new test file only.

### Peripheral concepts

smoke-test conventions (test_12, test_13), `ConnectionEngine` config loading, Telethon `FloodWaitError(request, capture)`, `MTProtoSender.send` futures, `ConnectionPool` session naming (`<session>_1`), `ephemeral_client` / `get_client` / `AuthRequiredError` paths, the module context variable

### Hardness Lvl

3

---

## Step 4 — Offline test, discovery level (same file) `[folded: Risk 1, robust]`

### Proposed changes

Add TESTs 8–11 to `test_14_flood_threshold.py`. Each uses:
- a factory-built client with a scripted fake connection;
- a stand-in connection engine, an object whose `session()` is an `asynccontextmanager` yielding that client;
- `DiscoveryEngine(stand_in)` called with `pace=0`.

8. **Raw discovery requests: short waits reach discovery, which beats and retries.**
   - `search_groups("x", heartbeat=beats.append)`, with the fake connection answering `SearchRequest` first with a 2 s wait, then with `types.contacts.Found(my_results=[], results=[], chats=[], users=[])`.
   - Assert: two sends, `"flood-wait 2s"` among the beats, and an empty DataFrame returned.
   - Before the fix, Telethon slept silently and no `flood-wait` beat appeared.
9. **A wait above `max_flood_wait` interrupts.** The same call with `max_flood_wait=1` and a 2 s wait raises `DiscoveryInterrupted` with `retry_after == 2` in under 0.5 s.
10. **Lookup waits are never slept:**
    - (a) `similar_groups(["@seedname"])` with `ResolveUsernameRequest` answered by a 5 s wait returns in under 1 s, with the seed skipped and the `"Seed '@seedname' skipped"` warning logged (captured by a `logging` handler).
    - (b) `linked_groups("@source")` with the same wait raises `DiscoveryInterrupted` with `retry_after == 5` in under 1 s.
    - Link-resolution stopping (`_links` with `resolve=True`) goes through the same `_resolve`, which now raises. It is covered by (a)'s mechanism and not driven separately, because scripting `iter_messages` replies would double the test for no new path.
11. **Premium waits are handled as waits** `[folded: Risk 1, robust]`. Skipped with a printed note if the installed Telethon has no `FloodPremiumWaitError`.
    - (a) `search_groups("x")` answered first with `FloodPremiumWaitError(capture=2)`, then `Found`, beats `"flood-wait 2s"` and returns after two sends — not "Search … failed — skipped".
    - (b) `linked_groups("@source")` answered with `FloodPremiumWaitError(capture=5)` raises `DiscoveryInterrupted` with `retry_after == 5`, not the raw Telethon error.

### Output

TESTs 8–11 pass. They show that discovery's existing handlers now see every wait Telethon used to sleep for it, of every wait type, as written.

### Safe in nature

True — test code only.

### Peripheral concepts

`DiscoveryEngine._request` / `_resolve` / `_similar` / `linked_groups`, `_State` (`pace`, `max_flood_wait`, `beat`), `_sleep_beating` ticks, `DiscoveryInterrupted(found, retry_after)`, `_WAIT_ERRORS`, the session cache lookup in `_resolve` (an in-memory miss leads to a `ResolveUsernameRequest`), discovery's warning log lines

### Hardness Lvl

3

---

## Step 5 — Make every documentation statement about discovery's waits exact `[folded: Risk 2, robust]`

### Proposed changes

The complete list. Each statement is re-read against the behaviour after Steps 1–2.

1. **`tgdata/discovery_engine.py`:**
   - `_request`'s docstring: keep the per-call-threshold-0 sentence, and add that tgdata's clients honour it, while Telethon's own `__call__` ignores it (see `connection_engine._PerCallFloodThreshold`), and that every wait type is handled (`_WAIT_ERRORS`).
   - `_resolve`'s docstring and the `# NOT _request: a wait here is never slept` comment: now true; add a short pointer to the same mixin.
   - **`DiscoveryInterrupted`'s docstring:** add that it is also raised when looking up a `linked_groups` source name must wait — lookups are never slept through, so `retry_after` can be below `max_flood_wait`.
2. **`tgdata/tgdata.py`, the `TgData` facade:**
   - `search_groups`' `max_flood_wait` description — the one `similar_groups`, `linked_groups` and `discover_groups` refer to with "as in search_groups": "obeyed exactly, with heartbeat ticks" holds for search, recommendations and lookups. Add one clause: reading posts for links, and the dialog sync for numeric ids, keep Telethon's own handling of waits up to a minute, without ticks.
   - `linked_groups`' docstring: add a `Raises:` line — `DiscoveryInterrupted` when looking up a source name must wait, or as in `search_groups`.
3. **`README.md`, the "Pacing and waits" paragraph:**
   - Keep "obeyed exactly, with heartbeat ticks", made precise for search, recommendations and lookups.
   - Add one sentence naming the two still-silent paths: reading a room's posts for links, and the dialog sync for numeric ids. A wait of up to a minute there is slept without ticks.
4. **`devdocs/guides/group_discovery.md`:**
   - The "Waits are obeyed exactly, and you see them" paragraph: the same precision, in one sentence.
   - **§8 Troubleshooting, the row "`DiscoveryInterrupted` with `retry_after > 0`":** the cause becomes "Telegram demanded a wait above `max_flood_wait`, or a wait on looking up a `linked_groups` source".
5. **The stray edit in the guide.** The working tree holds an unrelated edit in this file: line 1 reads `claude # Group discovery …`. It predates this branch and is not ours. It must not be committed and must not be lost:
   - set it aside before editing, with a path-limited stash carrying a message — `git stash push -m "stray guide edit (not ours)" -- devdocs/guides/group_discovery.md` — after checking `git stash list` is empty;
   - make and stage this step's edits;
   - restore it after the commit in Step 6.

### Output

Every docstring, comment and README or guide sentence about discovery's waits matches the behaviour after Steps 1–2, including:
- the `DiscoveryInterrupted` docstring;
- the facade docstrings;
- the guide's §8 row;
- the two still-silent paths, named.

### Safe in nature

True — documentation only.

### Peripheral concepts

README discovery section, `devdocs/guides/group_discovery.md` (§ waits, § "Username resolution is the dangerous request", §8 troubleshooting, watchdog advice in §6), `TgData` discovery facade docstrings, `DiscoveryInterrupted`, `_mine_room` post reading via `iter_messages`, `MessageEngine._entity_after_dialog_sync`, the uncommitted stray edit in the guide

### Hardness Lvl

2

---

## Step 6 — Grep sweep, run the offline suite, and commit `[folded: Risk 2, robust]`

### Proposed changes

1. **Grep sweep** `[folded: Risk 2, robust]`. Run:
   ```
   grep -n -E "max_flood_wait|DiscoveryInterrupted|slept|heartbeat tick|lookup" README.md devdocs/guides/group_discovery.md tgdata/*.py
   ```
   Read every hit against the behaviour after Steps 1–2. Any statement still wrong is fixed in the Step 5 files before going on.
2. **Byte-compile the touched modules:** `python -m py_compile tgdata/connection_engine.py tgdata/discovery_engine.py tgdata/tgdata.py tgdata/smoke_tests/test_14_flood_threshold.py`.
3. **Run the offline tests with the repository's venv (Telethon 1.45.0):**
   - `test_14_flood_threshold`, all TESTs;
   - `test_13_device_identity`, 6 of 6, including its connection-path test, which now builds through `_client_class`;
   - `test_12_proxy`, 7 of 7.

   Do **not** run live tests (`test_11_discover_groups` and the other numbered smoke tests that log in). Their configured account session was logged out by Telegram, and the persistent path would request a login code.
4. **Commit on `fix/discovery-flood-threshold`.** Use explicit paths only:
   - `tgdata/connection_engine.py`;
   - `tgdata/discovery_engine.py`;
   - `tgdata/tgdata.py`;
   - `tgdata/smoke_tests/test_14_flood_threshold.py`;
   - `README.md`;
   - `devdocs/guides/group_discovery.md`, this step's hunks only — the stray edit is set aside;
   - `devdocs/work/fix-discovery-flood-threshold/`.

   The commit message states the Telethon defect, the workaround and the verification, and ends with the session's Co-Authored-By line.
5. **Restore the stray edit.** Run `git stash pop`, but only after `git stash list` shows the entry with the "stray guide edit (not ours)" message at `stash@{0}`. Then confirm with `git diff` that line 1 of the guide is the only modification left.
6. **Do not push, open a PR, or merge.**

### Output

- A grep sweep with no stale statement.
- A green offline run, reported.
- One local commit on `fix/discovery-flood-threshold`.
- The working tree as it was found, apart from the committed work.

### Safe in nature

True — verification and a local commit.

### Peripheral concepts

the CONTRIBUTING process guard (commits allowed on `fix/*`, blocked on `dev` / `main`), the logged-out live session (never run live tests), git stash for the stray edit

### Hardness Lvl

1
