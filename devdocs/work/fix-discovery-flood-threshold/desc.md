# Make Telethon's per-request flood-wait threshold work in tgdata

> Session warmed at `f411c9c` (2026-10-03) — already warm, so `/arch-small-summary` and `/arch-intro` were not run. This session wrote tgdata's discovery engine, and read `connection_engine.py`, `discovery_engine.py`, `tgdata.py` and Telethon 1.45.0's request path (`telethon/client/users.py`, `telegrambaseclient.py`) in full. `devdocs/archaeology/` is unchanged.
>
> **Branch:** `fix/discovery-flood-threshold`, cut from `dev` at `f411c9c`. There is no GitHub issue: the maintainer waived it for this fix on 2026-10-03.

## Problem Statement

Telethon documents a per-request override on every client call:

> `flood_sleep_threshold` — "The flood sleep threshold to use for this request. This overrides the default value stored in `client.flood_sleep_threshold`" (the docstring of `TelegramBaseClient.__call__`).

**It does not work**, in any release checked: 1.33.1, 1.34.0, 1.40.0, 1.42.0, 1.44.0 and 1.45.0, the latest. Telethon ignores the value in two places:
- `UserMethods.__call__` (`users.py:29-30`) accepts the argument and calls `_call(...)` without it.
- Inside `_call`, the decision after a `FloodWaitError` (`users.py:121`) compares against `self.flood_sleep_threshold` — the client-wide property — not the per-call value.

Run offline through Telethon 1.45.0's real request code with a fake connection, a 1 s `FLOOD_WAIT` sent with `flood_sleep_threshold=0` is slept and retried instead of raised. Every wait up to the client-wide threshold, 60 s by default, is slept silently inside Telethon, whatever the caller passes.

**tgdata relies on the override in exactly two places, both in discovery:**
- `DiscoveryEngine._request` (`discovery_engine.py:252`) sends every raw discovery request with `flood_sleep_threshold=0`. The intent is that discovery handles each wait itself: it sleeps a wait within `max_flood_wait` in ten-second heartbeat slices and retries, and raises `DiscoveryInterrupted(found, retry_after)` for a longer one.
- `DiscoveryEngine._resolve` (`discovery_engine.py:301`) sends `ResolveUsernameRequest` with `flood_sleep_threshold=0`, so that a lookup wait "propagates unslept for the caller to skip or stop on".

**What goes wrong today, for waits of 60 s or less:**
1. **Discovery goes silent.** Its heartbeat stops for up to a minute, although the guide promises "Waits are obeyed exactly, and you see them".
2. **`max_flood_wait` below 60 s is not honoured.**
3. **Lookup waits are slept through.** The guide (§ "Username resolution is the dangerous request") and the README promise that "a wait on a lookup is **never slept through**: a seed that would wait is skipped with a warning, and link resolution stops at the first wait". In fact Telethon sleeps and retries the lookup — the pattern the design avoids, because lookup blocks escalate (a reference account lost 8 h and then 21 h of lookups).
4. **The docstrings say the opposite of what happens** (`_request`, `_resolve`, and the `# NOT _request: a wait here is never slept` comment).

Telethon will not be asked to fix this. That is the user's decision, and Telethon's issue template forbids AI-written reports. tgdata has to overcome it on its own side.

## User Value Proposition

- **Discovery does what its docs say.** Every wait on a raw discovery request shows up as heartbeat ticks and respects `max_flood_wait`. Every wait on a username lookup is skipped or stopped, never slept through.
- **The option means what Telethon documents.** Any tgdata code can pass `client(request, flood_sleep_threshold=N)` and rely on it.
- **Nothing else changes.** Calls that do not pass the option keep Telethon's normal behaviour: a wait of 60 s or less is slept and retried.
- **No dependency on Telethon.** The fix lives in tgdata and works across the declared range, `Telethon>=1.33,<2.0`.

## Success Criteria

Verified offline: Telethon's real request code, a fake connection, no network and no login.

1. **The option works.** For a client built by tgdata's factory, `await client(request, flood_sleep_threshold=0)` raises `FloodWaitError` at once for a 1 s wait, with one request sent and no sleep.
2. **Calls without the option are unchanged.** A 1 s wait is slept and the request retried, returning the result.
3. **Calls stay independent.** On one client, a call with `flood_sleep_threshold=0` and a call without it, running concurrently, each keep their own behaviour.
4. **No side effects on the client.**
   - The override never outlives its call: `client.flood_sleep_threshold` reads 60 afterwards.
   - The client-wide setter behaves exactly as Telethon's, including its 24 h cap.
5. **Known pending waits are covered.** With a wait already pending for that request type, a call with `flood_sleep_threshold=0` raises before anything is sent.
6. **Every client gets it.** Every client tgdata builds — persistent, pool connection, use-and-close — comes from `ConnectionEngine._new_client()` and has this behaviour. A test checks each path.
7. **Discovery handles short waits itself.** A short wait on a raw discovery request reaches discovery's handler: it is slept in heartbeat slices (`"flood-wait …"` ticks) and the same request retried. A wait above `max_flood_wait` raises `DiscoveryInterrupted` with `retry_after`.
8. **Lookup waits are never slept.** A short wait on a username lookup:
   - skips the seed (`similar_groups` / `discover_groups`);
   - stops link resolution (`linked_groups` with `resolve_links=True`);
   - or raises `DiscoveryInterrupted` when the lookup is `linked_groups`' own source;

   exactly as the code and the docs describe.
9. **It cannot fail silently.** The new test asserts behaviour, not internals, so a future Telethon that stops reading the property fails it.
10. **Nothing regresses, and the docs are true.**
    - `test_12_proxy` and `test_13_device_identity` still pass.
    - Every docstring, comment and README or guide sentence about discovery's waits matches what now happens.

## Scope Boundaries

- **Telethon is not changed.** No vendoring, no global monkeypatch of `TelegramClient`, no upstream report. The change lives in tgdata's client factory.
- **Waits elsewhere are not changed.** The default threshold stays 60 s. The message fetch loop, counting, searching, downloads, the poll loop and the real-time path keep Telethon's normal waits.
- **Discovery's post reading is not changed.** Link mining (`_mine_room` via `iter_messages`) never passes a per-call threshold, so its short waits stay Telethon's silent sleeps.
  - [ASSUMPTION] This is out of scope: it is not caused by this defect. A follow-up can opt it in with the same mechanism.
  - Where the README or guide promise visible waits for *all* discovery requests, the wording becomes precise instead.
- **No retry policy, pacing or `max_resolve` changes.** Discovery's handlers are used exactly as written.
- **No new public API.** [ASSUMPTION] The client class stays internal to `connection_engine.py`, and `__init__.py` exports nothing new.
- **The `device_identity()` probe client is not required to change.** It is built without a connection and sends nothing. [ASSUMPTION] Building it with the new class is acceptable but not required.
- **Out of this task:**
  - Issue #4 (account health events). Its finding notes that discovery's short waits are invisible today; after this fix discovery handles them itself, and #4's description should say so.
  - Any GitHub issue or PR. Merging is the user's decision.

## Priority Level

**Medium.**
- Two documented guarantees of a shipped feature are false: visible waits, and lookups never slept through. One of them is a safety rule against lookup-block escalation.
- The exposure is limited to waits of 60 s or less, and no harm has been observed from it yet.
- The fix is small and contained to one factory.
