# Verify — #67 WebSocket transport

**The run:** 2026-11-26, at `2133d7e` (plan steps 1–11 implemented), Python 3.11.10, Telethon 1.45.0.

**Conditions:** every suite was run offline, from the worktree root, with no `config.ini` present, so nothing that needs an account or Telegram could run.

## Plan step 12 — the offline regression run

| Suite | Result | Notes |
|---|---|---|
| `test_50_websocket_transport` (new) | **71/71** | All items ran, using `openssl` for the throwaway test CA. Nothing was skipped. |
| `test_12_proxy` | 7/7 | **Items 6–7 skipped by design:** "config.ini not found". Item 6 would send a throwaway session to Telegram through a local relay, and item 7 would use a real proxy from the config. Items 1–5 (loopback only) ran. |
| `test_13_device_identity` | 6/6 | |
| `test_14_flood_threshold` | 11/11 | |
| `test_15_login_checks` | 11/11 | |
| `test_16_health_events` | 21/21 | |
| `test_17_session_store` | 12/12 | |
| `test_31_account_pool` | 46/46 | |
| `test_32_account_operation` | 28/28 | |
| `test_33_owned_health` | 62/62 | |
| `test_37_worker` | 33/33 | |
| `test_39_pool_lifecycle` | 48/48 | |
| `test_40_pool_outcomes` | 25/25 | |
| `test_41_stepwise_login` | 23/23 | |
| `test_48_terminal_login` | 26 passed, 0 failed | 102 s, with real PTY children |

**Fixes made during the run** — all in `test_50` itself; none to production code:
- **The reconnect item compared the connection object after `disconnect()`.** Telethon clears `MTProtoSender._connection` on disconnect, so the item now records the comparison before disconnecting.
- **The mixed-pool item assumed `AccountPool.initialize()` builds the sources' clients.** It does not, so the item calls `source.preflight()`, as test_31 does.
- **The pool configs repeated `session_file`.** `write_ini` gained a `session` parameter, so each pool account has its own session. The pool refuses two accounts sharing one session.
- **A bare `MTProtoSender` left the error that ended it on its `_disconnected` future,** and asyncio reported it as "never retrieved". A `collect(sender)` helper now retrieves it. A `TelegramClient` awaits that future itself.

## Success criteria — offline status

| # | Criterion | Shown by |
|---|---|---|
| 1 | the key is read and checked | test_50 items 7 and 9 (bad value; default) |
| 2 | one switch covers every client | test_50 items 4–6 (factory, owned, LoginFlow, pool) |
| 3 | never an IP, on every path | test_50 items 3–6 (recording proxy, SOCKS5 and HTTP CONNECT, reconnect, exported sender, strict paths, mixed pool) |
| 4 | no IP held or accepted | test_50 items 1 and 3 |
| 5 | failures classified correctly | test_50 item 7 (through `_try_connect` and `AccountPool._failure`, plus polling and the worker) |
| 6 | no health noise | test_50 item 8 |
| 7 | the login checkpoint stays correct | test_50 items 9–10 |
| 8 | the default path is unchanged | test_50 item 9 (against the pre-#67 baseline), plus the 14 regression suites above |
| 9 | observability | test_50 item 10 |
| 10 | the version canary | test_50 item 11 |
| 11 | no new runtime dependency | `ws_stream` imports only the standard library (item 11); `setup.py` is unchanged |
| 12–13 | documentation | `2133d7e`: the corrected comment and docstrings, the README section, `docs/stepwise_login.md` |
| 14 | the live run on the built code | **waived before the merge by the maintainer (2026-11-26); observed after the release.** The pre-build prototype check on the same account PASSED (`critic.md`). |
