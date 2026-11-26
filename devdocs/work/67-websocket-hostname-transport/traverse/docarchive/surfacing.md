---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

/Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/_branch.md — SAVE the artifact as /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/surfacing.md. This is a re-invocation over the same codebase territory as devdocs/work/67-websocket-hostname-transport/triage.md, which is the prior-artifact (its Traversal Trace is the exclusion filter for items whose relevance does not change). Purpose, from _branch.md: surface what bears on deciding the most elegant design for `transport = websocket` without harming the existing design — the transport's possible shapes (Telethon Connection subclass over a byte-stream adapter, a local relay process, others), the config surface and the DC→hostname map, the strict clients' keep-alive / reconnect / retry behaviour under the transport, the error taxonomy, require_proxy × websocket, LoginFlow's binding, the WebSocket client implementation choice, docs that become false, the test seams, and the outside-world risks — and concerns not yet realised. Driven by the cold MQ2 (verdict: code reading vs probes; kinds: Telethon 1.45.0 network internals, tgdata consumer contracts, RFC 6455, Telegram's transport page, the probe, tests' patch points; stance: elegance, endpoint appetite, dependency, fail-closed timing) and MQ4 (no default-path change, no fallback, no MTProxy, no secrets, latest Telethon only, no implementation).

---

# Surfacing — what bears on the WebSocket transport's design

**Mode:** artifact · **entry:** signal-first · **territory:** explicit-bounded (the boundary-discovery sub-phase did not fire).

**Prior artifact:** `../triage.md`. Its 30 trace items are the exclusion filter. They are not re-listed unless this purpose changes their relevance or what they reveal.

**Workspace:** this session read every item below in full, now or while warming at `240a208`.

## What this pass found that triage did not

These are facts drawn into view. Interpreting them is for later disciplines.

1. **The keep-alive runs on every connected client.** `TelegramBaseClient.connect()` creates `_updates_handle` and `_keepalive_handle` with no condition, after `InitConnection` and `get_me` (`telegrambaseclient.py:617-618`). With `receive_updates=False` the only difference is that the init request is wrapped in `InvokeWithoutUpdatesRequest` (608-609). So strict clients — owned operations, `AccountPool` sources, `LoginFlow` — ping every 60 s too.
2. **Strict clients never reconnect.** With `auto_reconnect=False`, `MTProtoSender._reconnect` sets `retries = 0` and loops `retry_range(0, force_retry=False)`, which yields nothing. The `for … else` sets `ok = False`, and the sender disconnects. A cut ends a strict client's operation with a transport error. No other route is tried.
3. **Telethon's connect retry catches only `IOError` and `asyncio.TimeoutError`** (`_try_connect`). Any other exception from `Connection.connect()` propagates at once, with no retries. An `IOError` is retried `connection_retries` times (0 on strict clients). When it gives up, Telethon raises a **fresh, unchained** `ConnectionError('Connection to Telegram failed N time(s)')`. The original error survives only in a WARNING log line.
4. **Reconnects reuse the same connection object** (`self._connection.connect()` inside `_reconnect`). Its class, and so its hostname, is fixed for the client's life.
5. **The connection class is a constructor argument.** `TelegramBaseClient.__init__(connection=…)` asserts it is a type, and special-cases only `TcpMTProxy` subclasses (`init_proxy`). A subclass of `ConnectionTcpObfuscated` is not one, so the client's `proxy` is passed straight to each connection, as for TCP.
6. **The connection instance carries the DC number and a display name.** `Connection.__init__(ip, port, dc_id, *, loggers, proxy, local_addr)` stores `_ip`, `_port` and `_dc_id`. Telethon's log lines print the connection with `_ip`, so a hostname set there appears in its logs.
7. **The login checkpoint's binding is a SHA-256 hash** of `{api_id, api_hash, proxy, require_proxy, identity}` (`login.py:156-160`), compared on restore (225). `docs/stepwise_login.md:90-92` documents those exact fields. Adding a field to the hash changes it for every existing checkpoint, unless the field is included only when it differs from the default.
8. **The ordinary clients' retry options** are Telethon's defaults, since tgdata sets none for them: `connection_retries=5`, `auto_reconnect=True`. The persistent client and `ephemeral_client` reconnect through the same class.
9. **Fail-fast already exists by exception type.** `ProxyConfigError(ValueError)` is raised while reading the config, before any socket. A `ValueError` from inside `Connection.connect()` would also escape Telethon unretried. In `AccountPool._failure`, a `ValueError` is `unknown`, which stops; an unsuppressed `ConnectionError` is `transport`, which retries after `transient_retry_seconds`.
10. **TLS certificates come from Python's default trust store.** `ssl.create_default_context()` uses the system bundle; on this machine, conda's `cert.pem` with 151 CAs. A server or container without one fails verification — loudly, never by skipping. The probe verified fine inside a container on the maintainer's server.
11. **Telethon's own TLS helper is unusable here.** `Connection._wrap_socket_ssl` calls `ssl.wrap_socket`, which Python 3.12 removed, and it sets no SNI. A WebSocket connection must do its own TLS: `asyncio.open_connection(sock=…, ssl=ctx, server_hostname=host)` does both SNI and verification.
12. **The `PySocks` fallback** (`_proxy_library_available` accepts `socks`) also connects with `(self._ip, port)` and `rdns` set. A hostname in `_ip` reaches PySocks as a name too.
13. **The probe is a working prototype.** `ws_door_probe.py` (496 lines, in the work folder) contains:
    - `WsReader` and `WsWriter` — the byte stream over frames, with masking, ping/pong and close;
    - `open_tunnel` — HTTP CONNECT by hand, and SOCKS5 through python-socks with remote DNS;
    - `open_websocket` — TLS, SNI, certificate verification, and the RFC 6455 accept check;
    - `WsConnection(ConnectionTcpObfuscated)` — overrides only `_connect`.

    It passed 18 offline checks and an end-to-end local TLS check, then live: all five DCs, and holds of 75, 150 and 300 s.
14. **The docs that state related facts:**
    - `connection_engine.py:154`: "Telegram's servers are addressed by IP, so remote DNS is moot."
    - `README.md`'s proxy section: "A proxy that is down or refuses the tunnel makes the connection fail with `ConnectionError`" and "a session file is not tied to an IP".
    - `docs/stepwise_login.md:90`: the restore binding's fields.
    - `docs/account_operations.md:38`: "Transport failures … remain their original errors" — though Telethon's connect wrapper replaces them, per item 3.
15. **The test layout:**
    - `test_14`'s docstring makes it the canary to "RUN AFTER ANY TELETHON UPGRADE", for code relying on Telethon internals;
    - `test_12`'s `Socks5Relay` records the destinations it was asked for;
    - `test_13` patches `ce.TelegramClient` with a stand-in;
    - test numbers run to 29, with suite 18 and up being newer features.
16. **The dependencies:**
    - neither `websockets` nor `aiohttp` is installed or declared;
    - `setup.py` declares one extra, `proxy` (python-socks);
    - `install_requires` is Telethon `>=1.45,<2.0` and pandas;
    - `AccountPool` and `Worker` refuse any Telethon other than 1.45.0 at runtime;
    - plain `TgData` does not.
17. **Third-party relays are in the territory as the brief's references.** tg-ws-proxy-rs and similar tools run a local MTProto proxy that relays to the door. tgdata excludes MTProto proxies (`parse_proxy_url` refuses `tg://proxy`), so a relay would also need a tunnel to the proxy that tgdata does not own.

## Traversal Trace

Recency is the filesystem mtime in UTC. tgdata files carry the worktree's checkout time; Telethon's are the installed 1.45.0.

| # | Region | Item | Verdict | Conf. | Note | Recency |
|---|---|---|---|---|---|---|
| 1 | Telethon `client/telegrambaseclient.py` | `connect()` 600-618: `_no_updates` wraps the init; the keep-alive task is unconditional | core | HIGH | settles open point 3 for strict clients | 2026-10-03T09:09:32Z |
| 2 | Telethon `network/mtprotosender.py` | `_reconnect` with `auto_reconnect=False` → zero attempts → disconnect | core | HIGH | a cut fails strict clients; no fallback | ″ |
| 3 | ″ | `_try_connect` catches `IOError` / `TimeoutError` only; a fresh unchained `ConnectionError` after the retries | core | HIGH | error taxonomy by exception type; the cause is lost | ″ |
| 4 | ″ | `_connect` auth-key loop; `_reconnect` reuses `self._connection` | sub | HIGH | the class is fixed per client | ″ |
| 5 | Telethon `client/telegrambaseclient.py` | `__init__`: `assert isinstance(connection, type)`; only `TcpMTProxy` special-cased | core | HIGH | the obfuscated subclass gets the normal proxy path | ″ |
| 6 | Telethon `network/connection/connection.py` | `__init__` fields; `__str__` shows `_ip` | sub | HIGH | the hostname appears in Telethon's logs | ″ |
| 7 | ″ | `_wrap_socket_ssl` (`ssl.wrap_socket`, no SNI) | sub | HIGH | unusable; own TLS required | ″ |
| 8 | `tgdata/login.py` | binding hash 156-160, restore compare 225 | core | HIGH | adding a field breaks existing checkpoints unless only non-default | 2026-11-26T12:36:44Z |
| 9 | `tgdata/connection_engine.py` | `ProxyConfigError(ValueError)` at config time | core | HIGH | the existing fail-fast pattern | ″ |
| 10 | `tgdata/account_pool.py` | `_failure`: `ValueError` → unknown (stop); `ConnectionError` → transport (retry) | core | HIGH | the taxonomy maps onto exception types | ″ |
| 11 | `tgdata/login.py`, `pool_source.py`, `connection_engine._account_operation` | strict options: `connection_retries=0`, `auto_reconnect=False`, `receive_updates=False` | sub | HIGH | one connect attempt; keep-alive runs; no reconnect | ″ |
| 12 | Python `ssl` | default verify paths; 151 CAs here | sub | MEDIUM | trust store availability on servers | none |
| 13 | `devdocs/work/67-…/ws_door_probe.py` | `WsReader`/`WsWriter`, `open_tunnel`, `open_websocket`, `WsConnection` | core | HIGH | a tested prototype of the transport's parts | 2026-11-26T15:30Z (commit `1ab45e7`) |
| 14 | `docs/stepwise_login.md` | 90-92 binding fields; 102 (Telegram's auth key, unrelated) | sub | HIGH | docs to update if the binding changes | 2026-11-26T12:36:44Z |
| 15 | `docs/account_operations.md` | 38 "transport failures remain their original errors" | sub | MEDIUM | true of tgdata; Telethon replaces connect errors | ″ |
| 16 | `README.md` | proxy section claims | sub | HIGH | to extend for a by-name transport | ″ |
| 17 | `tgdata/smoke_tests/test_14_flood_threshold.py` | the "run after any Telethon upgrade" canary convention | sub | HIGH | a precedent for an internals canary | ″ |
| 18 | `setup.py` | one extra (`proxy`); no WebSocket library | sub | HIGH | the dependency choice | ″ |
| 19 | `docs/worker.md`, `docs/account_pool.md` | config-driven proxy and identity; no job may supply a proxy | side | MEDIUM | a transport key inherits the same config-only rule | ″ |
| 20 | issue #67 (brief's references) | tg-ws-proxy-rs, GramJS, gotd/td | side | MEDIUM | the alternative shape: an out-of-process relay | none |

## State Summary

**Territory:**
- what triage covered, re-filtered;
- Telethon 1.45.0's connect, reconnect, keep-alive and construction paths, at line level;
- the login binding;
- the docs under `docs/`;
- the probe;
- Python's `ssl` defaults.

**Purpose:** what bears on the elegant design for `transport = websocket`, and unrealised concerns.

**Coverage map**

| Region | Coverage | Aggregate verdict |
|---|---|---|
| Telethon connect, retry, reconnect and keep-alive | confirmed (line-level read) | core |
| tgdata strict-client options, binding, failure classification | confirmed | core |
| the probe | confirmed (it wrote, tested and ran) | core |
| `docs/` | scanned for transport, proxy, IP and binding claims | sub |
| dependencies and the trust store | confirmed | sub |

**Confirmed-absent:**
- no code path in tgdata or Telethon opens a socket outside the connection class;
- no WebSocket library is present;
- no existing doc describes a by-name transport.

**Concept names**

| Name | Type | Provenance | Gloss |
|---|---|---|---|
| fail-fast by type | coined-term | #3, #9, #10 | a non-`IOError` escapes Telethon's retries |
| unchained connect error | coined-term | #3 | Telethon replaces the cause |
| strict client | structural-reference | #11 | no retries, no reconnect, no updates |
| binding hash | structural-reference | #8 | the login checkpoint's config fingerprint |
| default-only-if-absent | coined-term | #8 | add a field to a hash only when non-default |
| internals canary | structural-reference | #17 | a test run after a Telethon upgrade |
| out-of-process relay | coined-term | #20 | the alternative shape |

**Recency distribution**

| Region | Newest | Oldest | No mtime | Items |
|---|---|---|---|---|
| Telethon 1.45.0 | 2026-10-03T09:09:32Z | same | 0 | 7 |
| tgdata, docs and setup | 2026-11-26T15:30Z | 2026-11-26T12:36:44Z | 0 | 11 |
| external (Python `ssl`, references) | — | — | 2 | 2 |

**Workspace-populated status:** `{populated: true, populated-at: 2026-11-26, extent: all core regions read in full in this session}`.

## Telemetry

- Mode `artifact`, entry `signal-first`, boundary discovery not fired. Prior artifact `triage.md`, used as the exclusion filter.
- Regions traversed: 9 new or refined. Items: 20 — 9 core, 9 sub, 2 side, none rejected. No umbrella tags.
- Convergence: the territory was traversed at line level for the behavioural paths, with no item filtered at uncertain relevance.
- Failure modes checked: missed-relevance, territory-mis-binding, recency-bias-filter, interpretive-overstep (the facts stay uninterpreted here).
- `items_with_mtime` 18 / `items_without_mtime` 2.

## Frontier — for downstream

- **Error transparency.** Telethon's connect wrapper drops the transport's own reason. Whether, and how, the transport makes it visible is open.
- **The taxonomy by exception type.** Which WebSocket failures should be fail-fast (non-`IOError`) and which retried (`IOError`): an unknown DC, a missing dependency, a refused upgrade, a certificate failure, a proxy refusal.
- **The binding.** Whether `transport` joins `LoginFlow`'s hash, and how without invalidating existing checkpoints.
- **The DC map.** A fixed set of planet names, or a configurable override against an unpublished door changing.
- **The relay alternative.** Out-of-process, through an excluded proxy type — to be weighed, not assumed away.

## Self-assessment

**PROCEED.** All frontier items are design questions; none is a coverage gap.
