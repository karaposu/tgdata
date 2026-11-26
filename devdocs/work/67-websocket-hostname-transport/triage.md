---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

Triage for GitHub issue #67 in karaposu/tgdata (branch feat/67-websocket-hostname-transport, worktree /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67, cut from dev at 784d851, warmed at 240a208): "Connect to Telegram over its WebSocket transport by hostname, for proxies that route only hostnames" — a per-account `transport = websocket` choice; connect by hostname through the configured proxy (HTTP CONNECT / SOCKS5 remote DNS), TLS with SNI and a verified certificate, GET /apiws with Sec-WebSocket-Protocol: binary, Telethon's obfuscated transport carried as a byte stream in binary frames; every DC by name (planet names: pluto/venus/aurora/vesta/flora for DC1-5, probe-verified 2026-11-26); fail-closed (never an IP, no TCP fallback); session files and device identity unchanged; the default transport exactly as today. Territory (explicit-bounded, artifact case): the tgdata package — connection_engine.py (_load_config, _new_client, _client_class mixins, _account_operation, ephemeral_client, _authenticate/_ensure_connected, health_check, ConnectionConfig in models.py), every consumer that builds clients through _new_client (login.py LoginFlow and its config binding, pool_source.py _OwnedSource, worker_engine.py, account_pool.py's failure classification of transport errors), discovery_engine.py's reconnect loop, health.py's classification (transport is not a verdict), session_store.py / login_file.py (stored server_address), setup.py extras and the Telethon pin, README proxy/device-identity docs, the smoke tests (test_12 proxy relay, test_13 identity, test_14 flood, test_17 session store) — plus Telethon 1.45.0's network layer (telethon/network/connection/connection.py Connection._connect/_proxy_connect, tcpobfuscated.py ObfuscatedIO/ConnectionTcpObfuscated, MTProtoSender connect/reconnect/auto_reconnect) and the client's connection-construction sites (telegrambaseclient.py connect, _get_dc, _create_exported_sender, _borrow_exported_sender, _get_cdn_client, _switch_dc, the 60 s _keepalive_loop), and the probe evidence (ws_door_probe.py and its 2026-11-26 results in issue #67). Purpose: answer "what parts of this system does this issue actually touch?" so the work can be weighed light or heavy per CONTRIBUTING.md §4.3–4.4 (blast radius, observability, consumers, model contact, reversibility). SAVE the artifact as devdocs/work/67-websocket-hostname-transport/triage.md, in triage.md form: Weight, Surfaced, Why light/heavy, Watch for, Traverse call, then the surfacing record (Traversal Trace with verdicts, State Summary, Telemetry, Frontier, Self-assessment).

---

# Triage — issue #67

**Weight:** feature-heavy

**Surfaced:**
- **The one door.** `ConnectionEngine._new_client()` builds every client tgdata opens:
  - the persistent client;
  - the legacy pool's extra connections;
  - `ephemeral_client()`;
  - the verified `_account_operation()`;
  - `LoginFlow`'s auth-only client (`_client_base=_LoginClient`);
  - `AccountPool`'s owned sources, which override `_new_client` and tighten its options.

  The Telethon constructor already takes a `connection=` class, and nothing passes one today, so every client uses `ConnectionTcpFull` by IP.
- **The config.**
  - `_load_config` reads `[Telegram]` into `ConnectionConfig`, which holds the proxy dict plus `proxy_display` and `require_proxy`, and the pinned identity.
  - `parse_proxy_url` always sets `rdns: True`. Its comment says remote DNS is "moot" because Telegram is addressed by IP; that stops being true here.
- **The mixin stack.** `_AnswerEvidence`, `JoinClientMixin`, `BudgetClientMixin`, `BatchHeartbeatMixin` and `_PerCallFloodThreshold` all intercept at Telethon's request seam, `__call__` and `_call(sender…)` / `sender.send`. That is above `MTProtoSender`, so a transport choice sits below all of them.
- **The consumers that read connection behaviour:**
  - `LoginFlow` hashes api id, api hash, proxy, `require_proxy` and identity into its checkpoint `binding`. A transport setting is not in it.
  - `AccountPool._failure` treats an unsuppressed `ConnectionError` or `TimeoutError` as `transport`, a timed retry.
  - `Worker` and `AccountPool` both require Telethon == 1.45.0 exactly.
  - `discovery_engine._wait_for_network` reconnects the same client.
  - `health.classify` treats transport errors as not a verdict.
- **The session.** Telethon records the DC's IP in the session (`server_address`), whatever transport is used. `login_file` validates that it is present. Under a hostname transport it is carried along but never dialled.
- **Telethon 1.45.0's network layer:**
  - **How a connection opens.** `Connection._connect` and `_proxy_connect` dial `self._ip`. Python-socks receives `dest_host=self._ip` with tgdata's `rdns=True`, and for a name: SOCKS5 sends the name; SOCKS4 sends it as SOCKS4a; HTTP CONNECT always sends it.
  - **The obfuscation.** `ConnectionTcpObfuscated` / `ObfuscatedIO` need only `reader.readexactly()` and `writer.write/drain/close/wait_closed`.
  - **Reconnects.** `MTProtoSender` reuses the same connection object on reconnect.
  - **Every connection carries its DC number.** All four places that build one pass `dc_id` through `self._connection(...)`: the main connect, exported senders, their reconnect, and the CDN client.
  - **Keep-alive.** `_keepalive_loop` pings every 60 s. A ping still unanswered at the next tick triggers a reconnect.
- **Docs and tests:**
  - the README's "Connecting through a proxy" and "A fixed device identity" sections;
  - `test_12`'s local SOCKS5 relay, which records the destinations it was asked for;
  - `test_13`'s stand-in `TelegramClient` patch point;
  - `test_14` and `test_17` build clients through the factory.
- **Evidence** (issue #67, 2026-11-26):
  - all five DCs work by planet name, from the proxy's assigned address;
  - `kws2-1` and `kws4-1` fail;
  - an idle connection is cut between 150 and 300 s.

**Why heavy.** One seam in code, but it fails the light test on four axes (§4.4):
- **Blast radius.** Every connection path — login, reads, verified operations, the pool, the worker, reconnects, downloads from other DCs — rides the transport. It joins tgdata's single-door proxy guarantee to Telethon's connection lifecycle, and both to an outside endpoint.
- **Observability.** The failure that matters is silent: one connection that still goes by IP gives the account away, and nothing in tgdata or Telethon shows it. Only the proxy's own exit-address header would.
- **Consumers.** `TgData`, `AccountPool`, `Worker` and `LoginFlow` all depend on it, with different policies: retries, the checkpoint binding, exact version pins.
- **Reversibility.** The outside world: it changes how Telegram sees the account. An unpublished door, a desktop-app account arriving through the web transport, and the relays' rate limits are all unverified.

Model contact: none.

**Watch for:**
1. **A second way in.** Any connection built outside `_new_client`, or any Telethon path that opens a socket without the connection class, would leak by IP. All four of Telethon's construction sites pass `dc_id` through the class today. Keep it that way, and test it.
2. **Fallback by accident.** An unknown DC, a missing dependency, a failed handshake: each must raise, never quietly use `ConnectionTcpFull`. That also covers `require_proxy`: is a WebSocket transport without a proxy allowed?
3. **Retries that make it worse.** A configuration-class transport error, such as an unknown DC or a refused upgrade, would be retried by `AccountPool` as `transport`. Telethon's own `connection_retries` loops on it too.
4. **The checkpoint binding.** A `LoginFlow` checkpoint made under one transport could be restored under another unless the transport joins the binding.
5. **Docs that become false:**
   - "remote DNS is moot" in `connection_engine.py`;
   - "every connection goes through it" now needs "by name";
   - the README's proxy section.
6. **The `-1` names** must not be used: `kws2-1` and `kws4-1` fail.
7. **Idle connections are cut by 300 s** at the latest. Telethon's 60 s keep-alive covers it on the main connection, but only while the client's keep-alive loop runs. Owned operations set `receive_updates=False`, so check whether the keep-alive still runs there.
8. **The default stays byte-identical.** No `transport` key means the same constructor arguments as today.

**Traverse (§5): called.**
- It joins two existing structures delicately: Telethon's connection lifecycle, and tgdata's single-door, fail-closed proxy guarantees. Each side has rules the other must not break.
- The maintainer asked for a full traverse, so that the most elegant design is found without harming the existing one.

---

# Surfacing record

Mode: **artifact** · entry point: **signal-first** · territory: **explicit-bounded** (boundary-discovery sub-phase not fired). Most regions were read in full while warming at `240a208`. This pass read the rest: the tests, the README sections, the discovery reconnect, and Python-socks' remote-DNS behaviour.

## Traversal Trace

Recency is the filesystem mtime in UTC, used as a signal only. The worktree was checked out on 2026-11-26, so every tgdata file carries that checkout time. Telethon's files are from the installed 1.45.0 package.

| # | Region | Item | Verdict | Conf. | Note | Recency |
|---|---|---|---|---|---|---|
| 1 | `tgdata/connection_engine.py` | `ConnectionEngine._new_client` | core | HIGH | the one door; `connection=` is not passed today | 2026-11-26T12:36:44Z |
| 2 | ″ | `_load_config`, `ConnectionConfig` (`models.py`) | core | HIGH | where a `transport` key would be read and validated | ″ |
| 3 | ″ | `parse_proxy_url` (`rdns: True`), `_PROXY_SCHEMES` comment | core | HIGH | names reach the proxy; the comment "remote DNS is moot" becomes false | ″ |
| 4 | ″ | `_client_class` mixin stack | sub | HIGH | above the transport; unaffected, but must stay above it | ″ |
| 5 | ″ | `_account_operation` (`auto_reconnect=False`, `receive_updates=False`) | core | HIGH | strict client options; does the keep-alive run? | ″ |
| 6 | ″ | `ephemeral_client`, `_init_primary_client`, `_init_pool` | core | HIGH | all build through `_new_client` | ″ |
| 7 | ″ | `_authenticate`, `_ensure_connected`, `_log_in` | sub | HIGH | connect and reconnect; `ConnectionError` wrapping | ″ |
| 8 | ″ | `health_check`, `validate_connection`, `_route_logged` log line | sub | MEDIUM | where the transport would be reported | ″ |
| 9 | ″ | `device_identity` (plain `TelegramClient` probe) | side | HIGH | never connects; unaffected | ″ |
| 10 | `tgdata/login.py` | `LoginFlow` binding, `_LoginClient.connect/_disconnect`, `_make_client` | core | HIGH | the checkpoint binding omits the transport; the auth client builds through the door | ″ |
| 11 | `tgdata/pool_source.py` | `_OwnedSource._new_client` override, `_verify` | core | HIGH | strict options; reconnect by `connect()` | ″ |
| 12 | `tgdata/account_pool.py` | `_failure` transport classification; `_preflight` version pin | sub | HIGH | a configuration error retried as `transport` | ″ |
| 13 | `tgdata/worker_engine.py` | one `TgData` per account; version pin | sub | MEDIUM | inherits the config | ″ |
| 14 | `tgdata/discovery_engine.py` | `_wait_for_network` reconnect loop | sub | MEDIUM | reconnects the same client | ″ |
| 15 | `tgdata/health.py` | `classify` (transport is not a verdict) | sub | MEDIUM | WebSocket failures stay non-verdicts | ″ |
| 16 | `tgdata/session_store.py`, `tgdata/login_file.py` | stored `server_address` / `dc_id` | sub | MEDIUM | an IP stored, never dialled | ″ |
| 17 | `tgdata/budget_client.py`, `join_client.py`, `batch_heartbeat.py`, `owned_health.py` | request-seam interception | side | HIGH | unaffected | ″ |
| 18 | `setup.py` | `extras_require['proxy']`, Telethon `>=1.45,<2.0` | sub | HIGH | a possible new extra for a WebSocket library | ″ |
| 19 | `README.md` | "Connecting through a proxy", "A fixed device identity" | sub | HIGH | docs to extend; "a session file is not tied to an IP" | ″ |
| 20 | `tgdata/smoke_tests/test_12_proxy.py` | `Socks5Relay` with recorded destinations | sub | HIGH | reusable to prove names only, never IPs | ″ |
| 21 | ″ `test_13_device_identity.py` | the `ce.TelegramClient` stand-in patch point | sub | MEDIUM | the stand-in must accept `connection=` | ″ |
| 22 | ″ `test_14_flood_threshold.py`, `test_17_session_store.py` | factory-built clients | side | MEDIUM | regression coverage | ″ |
| 23 | Telethon `network/connection/connection.py` | `Connection._connect`, `_proxy_connect` (`dest_host=self._ip`), `_wrap_socket_ssl` (`ssl.wrap_socket`) | core | HIGH | the hook point; Telethon's own TLS helper is unusable on 3.12+ | 2026-10-03T09:09:32Z |
| 24 | Telethon `network/connection/tcpobfuscated.py` | `ObfuscatedIO`, `ConnectionTcpObfuscated` | core | HIGH | reusable unchanged over a byte-stream adapter | ″ |
| 25 | Telethon `network/mtprotosender.py` | `connect`, `_try_connect`, `_reconnect` (same connection object), `_keepalive_ping` | core | HIGH | reconnects reuse the class | ″ |
| 26 | Telethon `client/telegrambaseclient.py` | `__init__(connection=…)`; `connect` (line 560); `_create_exported_sender` (842); `_borrow_exported_sender` (877); `_get_cdn_client` (931); `_get_dc`; `_switch_dc` | core | HIGH | every construction site passes `dc_id` through the class | ″ |
| 27 | Telethon `client/updates.py` | `_keepalive_loop` (60 s) | sub | HIGH | covers the 150–300 s idle cut, while it runs | ″ |
| 28 | Telethon `client/downloads.py` | `GetFileRequest` without `cdn_supported` | side | HIGH | no CDN redirects from Telethon's own downloads | ″ |
| 29 | Python-socks `_connectors/socks4_async.py`, `socks5_async.py` | `rdns` handling | sub | HIGH | names pass through with `rdns=True`; SOCKS4 becomes SOCKS4a | ″ |
| 30 | issue #67 | probe results (2026-11-26) | core | HIGH | planet names for all 5 DCs; `kws2-1` / `kws4-1` fail; cut by 300 s | none (no file) |

## State Summary

**Territory:**
- the tgdata package's connection core and every client consumer;
- docs and tests;
- Telethon 1.45.0's network layer and client connection sites;
- Python-socks' remote-DNS handling;
- the #67 probe evidence.

**Purpose:** what #67 touches, so it can be weighed light or heavy.

**Coverage map**

| Region | Coverage | Aggregate verdict |
|---|---|---|
| `connection_engine.py`, `models.py` | confirmed (read in full at `240a208`) | core |
| `login.py`, `pool_source.py`, `account_pool.py`, `worker_engine.py` | confirmed | core / sub |
| `discovery_engine.py`, `health.py`, `session_store.py`, `login_file.py` | confirmed (`discovery_engine` for its reconnect path) | sub |
| request-seam mixins | confirmed | side |
| `setup.py`, `README.md` | confirmed | sub |
| smoke tests 12, 13, 14, 17 | confirmed for structure; relay and patch points read | sub / side |
| Telethon network and client sites | confirmed (read in full this session) | core |
| Python-socks connectors | confirmed for `rdns` | sub |

**Confirmed-absent:**
- tgdata never passes `connection=`.
- No WebSocket library is installed: neither `websockets` nor `aiohttp`.
- No code outside `_new_client` builds a connecting client. `device_identity`'s probe never connects.

**Concept names**

| Name | Type | Provenance | Gloss |
|---|---|---|---|
| the one door | coined-term | #1 | `_new_client`, the only client factory |
| connection class | structural-reference | #23, #26 | Telethon's per-client transport class |
| dc_id routing | coined-term | #26 | every connection carries its DC number |
| byte-stream adapter | coined-term | #24 | the reader/writer pair the obfuscation needs |
| planet names | vocabulary | #30 | pluto…flora = DC 1–5 |
| remote DNS (`rdns`) | structural-reference | #3, #29 | the proxy resolves the name |
| checkpoint binding | structural-reference | #10 | `LoginFlow`'s config hash |
| idle cut | coined-term | #27, #30 | quiet tunnels die by 300 s |

**Recency distribution**

| Region | Newest | Oldest | No mtime | Items |
|---|---|---|---|---|
| tgdata package and docs | 2026-11-26T12:36:44Z | 2026-11-26T12:36:44Z (checkout time) | 0 | 22 |
| Telethon 1.45.0 | 2026-10-03T09:09:32Z | 2026-10-03T09:09:32Z | 0 | 6 |
| Python-socks | — | — | 0 | 1 |
| issue #67 evidence | — | — | 1 | 1 |

**Workspace-populated status:** `{populated: true, populated-at: 2026-11-26, extent: every core region read in full this session}`.

## Telemetry

- Mode `artifact`, entry `signal-first`, boundary discovery not fired.
- Regions traversed: 15. Items enumerated: 30 — 13 core, 13 sub, 4 side, none rejected. No umbrella tags.
- Convergence: the territory was traversed at module and function resolution, with no item filtered at uncertain relevance.
- Workspace-overload trigger: not fired.
- Failure modes checked: missed-relevance, territory-mis-binding, recency-bias-filter (a uniform checkout mtime, recorded but not used), interpretive-overstep.
- `items_with_mtime` 28 / `items_without_mtime` 2.

## Frontier — for downstream

- **The keep-alive under strict options.** Does `_keepalive_loop` run when `receive_updates=False`, as in owned operations, the pool and login? It decides whether those clients survive a 150–300 s quiet period.
- **Error taxonomy.** Which transport failures are configuration — unknown DC, refused upgrade, certificate — and which are transient? That decides `AccountPool` retries and Telethon's `connection_retries`.
- **The checkpoint binding.** Whether the transport joins `LoginFlow`'s binding.
- **`require_proxy` × websocket.** Is a WebSocket transport without a proxy allowed?
- **Dependencies.** A hand-written WebSocket client, or an optional extra.

## Self-assessment

**PROCEED.** The output is complete for the stated territory. The five frontier items are design questions for the traverse, not gaps in coverage.
