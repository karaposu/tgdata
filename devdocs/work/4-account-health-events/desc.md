# Report account health states as events (issue #4)

> Session warmed at `c72eab4` (2026-10-03) — already warm, so `/arch-small-summary` and `/arch-intro` were not run. This session wrote tgdata's discovery, proxy, device-identity, flood-threshold and login code, and read `connection_engine.py`, `message_engine.py`, `discovery_engine.py`, `tgdata.py` and Telethon 1.45.0's request, login, updates and error paths in full. `devdocs/archaeology/` is unchanged.

**Sources:**
- `traverse/finding.md` — the decided meaning, on Telethon 1.45.0;
- `triage.md` — feature-heavy.

**Since the finding was written, `dev` gained:**
- **The login prerequisite, `c72eab4`.**
  - Every login asks Telegram directly whether the session is logged in, and never requests a code nobody can type.
  - A session that is not logged in raises `AuthRequiredError` with `.reason` and `.banned`.
- **PR #11, `040100b`.**
  - tgdata's clients honour the per-request flood threshold.
  - Discovery handles every kind of wait itself.

## Problem Statement

Telegram limits and penalises accounts in several ways. It asks a client to wait, logs a session out, bans an account, freezes or spam-limits it, or locks it out of one group.

Today tgdata surfaces these only as exceptions, log lines, or not at all:
- **Short waits are invisible.** Waits of 60 s or less are slept inside Telethon and logged only at INFO on `telethon.client.users`, which almost no setup shows. This affects message fetching and iteration, counting, search, downloads, discovery's post reading, the dialog sync, and discovery's reconnect check.
- **Swallowed errors leave no trace.** The poll loop swallows every error, and discovery skips seeds and links, so a ban or a lost group there disappears.
- **Nothing aggregates per account.** An operator running many accounts cannot see "account 7 waited 4 times, 210 s in total" or "account 3 was banned at 14:02" without reading logs. Nothing in tgdata remembers which account is in which state.

## User Value Proposition

Every time Telegram says no to an account, tgdata tells the caller:
- which verdict;
- about what — the account, one kind of request, or one group;
- from which call;
- for how long;
- when it ended.

This arrives through one exception-safe callback, one log line per event, and a per-instance summary in `health_check()`.

That gives dashboards and test runs per-account totals, gives a future worker (#10) events it can forward, and gives operators a ban or logout without reading logs.

tgdata **reports and never acts**: no exception a caller catches today changes type or identity, and nothing is paused, retried or skipped because of a verdict.

## Success Criteria

Every criterion below is verified offline, by tests that drive Telethon 1.45.0's real request code with a scripted stand-in for the connection.

### 1. Verdicts come only from Telegram's own error names

The key is the class Telethon maps to that name, or the raw name in `.message` for an error Telethon does not know.

| Verdict | Scope | Telegram names |
|---|---|---|
| waiting | the request type | `FLOOD_WAIT_X`, `FLOOD_PREMIUM_WAIT_X`, `SLOWMODE_WAIT_X`, `FLOOD_TEST_PHONE_WAIT_X`, each with its seconds |
| logged out | account | `AUTH_KEY_UNREGISTERED`, `SESSION_REVOKED`, `SESSION_EXPIRED`, `AUTH_KEY_INVALID`, `AUTH_KEY_DUPLICATED` |
| banned | account | `USER_DEACTIVATED_BAN`, `USER_DEACTIVATED`, `PHONE_NUMBER_BANNED` |
| restricted | account | `FROZEN_METHOD_INVALID`, `FROZEN_PARTICIPANT_MISSING`, `USER_RESTRICTED`, `PEER_FLOOD` |
| no access | group | `CHANNEL_PRIVATE`, `CHAT_FORBIDDEN`, `CHANNEL_INVALID`, `USER_BANNED_IN_CHANNEL`, `CHANNEL_PUBLIC_GROUP_NA`, `CHANNEL_BANNED`, and tgdata's own `GroupAccessError` |
| ok | the scope that recovered | — |

**Unclassified.** Any other Telegram error in the 401, 403, 406 or 420 categories is reported as **unclassified**, with its name. File-reference errors are the exception.

**No event at all** for any of these:
- 400 and 5xx errors;
- transport errors, proxy errors and configuration errors;
- an unconfirmed lookup miss;
- per-message file and media errors;
- exceptions from user handlers;
- the `AuthRequiredError` of a session that was never logged in. That is configuration, not a verdict.

**Wrapped errors are unwrapped.** A Telegram error wrapped by tgdata — the fetch loop's `RuntimeError`, `AuthRequiredError`, `DiscoveryInterrupted`, `ConnectionError` — is found through the cause chain.

### 2. Each event is a plain dictionary

It must survive `json.dumps` unchanged. Its fields:

| Field | Content |
|---|---|
| `kind` | `"health"` |
| `time` | UTC, ISO 8601 |
| `account` | `label`, `session`, `user_id` |
| `verdict`, `scope` | as in the table above |
| `group` | the group as the caller named it: an int stays an int; a `@username` or t.me link becomes the lowercase username without `@`; `None` otherwise |
| `call` | the `TgData` method in progress, e.g. `get_messages` |
| `request` | the Telegram request type when known, e.g. `GetHistoryRequest` |
| `wait_seconds` | the wait length, for waiting |
| `error` | Telegram's name |
| `source` | `error`, `sleep`, `handled` or `swallowed` |

The `account` values:
- **`label`** — the optional `account_label=`;
- **`session`** — the session file's name, without folder or `.session`;
- **`user_id`** — the id Telethon restored for the client, else `None`.

### 3. Delivery

- **Registration.** `TgData(..., health_callback=fn, account_label=None)`. `fn` may be a function or a coroutine function.
- **Never breaks the operation.** A callback that raises is logged: the first time at WARNING with its traceback, after that at DEBUG.
- **Ordering.** An event that ends an operation is delivered before that operation's exception reaches the caller.

### 4. Sources

- **Public calls.** Every public `TgData` method that talks to Telegram reports a Telegram error that escapes it, then re-raises it unchanged. That includes `run_with_event_loop`, so a logout from the real-time listener is reported.
- **Waits tgdata handles itself:**
  - the fetch loop's waits;
  - discovery's waits;
  - discovery's skips that are Telegram verdicts — a seed or a link it can no longer see, a lookup wait.
- **Telethon's silent sleeps.** Each one during a public call becomes a waiting event attributed to the right account and call. This holds with several accounts in one process.
- **The poll loop.** It reports every Telegram verdict it swallows, then carries on as today.
- **Login.** An `AuthRequiredError` escaping a public call becomes logged out or banned, from its `.reason`.

### 5. Counted once

The fetch loop waiting four times, then giving up, produces four waiting events, not five.

### 6. Recovery — "ok" only when a condition ends

| Scope | Recovers when |
|---|---|
| waiting (a request type) | the call that waited completes successfully |
| logged out, banned | any later call completes successfully |
| restricted | only the same `TgData` method that was refused later completes successfully |
| no access (a group) | a later call naming the same group completes successfully |

A sleep that happens outside any public call is an occurrence only, with no "ok" after it.

### 7. A per-instance summary in `health_check()["health"]`

It holds:
- the account's verdict and since when;
- the open waits per request type;
- the groups without access and since when;
- the wait count and total wait seconds;
- the event count;
- the last unclassified name.

It covers events since this `TgData` was created, kept in memory.

### 8. A log line per event

Each event is also written to the logger `tgdata.tgdata.health`, so `log_file` users receive it:
- **WARNING** for logged out, banned, restricted and unclassified;
- **INFO** for waiting, no access and ok.

### 9. No side effects

- **Logging output is unchanged.** A console that showed no Telethon INFO lines still shows none. Telethon's warnings still reach a user's handlers, and a user who asked for the sleep lines still gets them.
- **Without a `health_callback`,** tgdata behaves as before, apart from the new log lines and summary.
- **Nothing regresses.** The offline suites — proxy, device identity, flood threshold and login checks — still pass.

## Scope Boundaries

- **No acting on verdicts:** no pausing, retrying, circuit-breaking or admission control. That belongs to #9 and #10.
- **No building #3, #8, #9 or #10.** The `kind` field lets their events join the stream later.
- **Transport is not a verdict.** Connectivity, proxies and configuration are not verdicts about the account.
- **Background-only signals are a follow-up.** Telethon's updates loop logs two signals only at INFO: "Account is now banned in <channel>", and catch-up waits. They can be added through the same mechanism later.
- **The verdict table stays internal.** The README lists it. No persistence: a JSON formatter on the `tgdata.tgdata.health` logger gives a persistent record.
- **No change to Telethon,** and no change to how waits are slept.
- **The callback stays separate from the heartbeat.** The heartbeat stays as it is.
- **[ASSUMPTION] "restricted" for a reader is documented as "by documentation, unobserved".** No frozen account has been observed, so which reads still work for one is unknown.

## Priority Level

**High** — P1 on the issue.
- It is the measurement layer the proxy work (#1) and the account tests depend on: every rate limit, logout and ban needs to be visible per account.
- #3, #9 and #10 build on its event shape.
- The login prerequisite has landed, so nothing blocks it.
