---
model: claude-opus-5-5[1m]
effort: unknown
---

# Plan — #67 WebSocket transport by hostname

**Revision 2.** **Critic folded:** 2026-11-26 — 3 mitigations (9 steps changed, 0 added): Risk 1 → steps 2, 3, 4, 5, 9; Risk 2 → steps 7, 8, 9; Risk 3 → steps 13, 14. Each change is tagged `[folded: Risk N, robust]`. The REORDER experiment ran first and PASSED (`critic.md`, `002fd9c`).

### What is the task

Add a per-account `transport = websocket` setting. With it, every connection tgdata opens for that account reaches Telegram's WebSocket endpoint (`wss://<planet>.web.telegram.org/apiws`) **by hostname**, through the configured proxy or directly by name, and never by IP address.

**Why.** A proxy that routes only hostnames can then carry the account's traffic from its assigned address, which today's IP-only connections make impossible.

**Constraints:**
- The existing design must stay exactly as it is: the single client factory, the request-level guards, the strict options, `StoredSession`, the login binding, the pool's failure classification and the pins.
- The default path stays byte-identical.

The design is decided in `traverse/finding.md`. The success criteria are 1–14 in `desc.md`, including the settled decision not to send `Origin`. This plan only orders the work and names exactly what changes.

### Huge Hard Blockers

#### Planning Blockers

None open. Four questions that could have rewritten steps were closed during planning, by reading the code and probing Telethon 1.45.0:

- **Does tgdata's own connect path keep a "stop immediately" error's type?**
  - **Why the steps can't survive it:** if every path rewrapped it, the classification would need a different mechanism.
  - **Status:** CLOSED.
    - Owned account operations (`_account_operation`), the pool source (`_OwnedSource._verify`) and `LoginFlow` call Telethon's `client.connect()` directly, so the error reaches `AccountPool._failure` unchanged, which maps a `ValueError` to `unknown`, stop.
    - Only `TgData`'s persistent-client path — `ConnectionEngine._authenticate` (`connection_engine.py:817`) and `_ensure_connected` (`:913`) — rewraps every exception as `ConnectionError("Failed to …")`.
    - Step 5 adds a one-line pass-through there, exactly like the existing one for `AuthRequiredError`.
    - Confirmed by reading `connection_engine.py`, `pool_source.py:110–125`, `login.py:382` and `account_pool.py:395–424`.
  - **Source:** found in code.
  - **Who can close it:** closed.
- **Discovery's reconnect wait loop catches every exception.**
  - **The fact:** `discovery_engine._wait_for_network`, `:228–254`, treats any connect error as "still down" until `max_offline`.
  - **Status:** CLOSED — kept as is.
  - **Why:** it is that loop's documented contract ("past max_offline the run gives up with everything it has found"), and it already treats `AuthRequiredError` the same way. A certificate failure in the middle of a discovery run will therefore wait out `max_offline`. That is documented in step 11, not changed.
  - **Source:** found in code.
- **Does Telethon 1.45.0 accept the subclass, and does construction-time naming work?**
  - **Status:** CLOSED. Confirmed by a probe:
    - `TelegramClient(…, connection=WS)` stores `WS`;
    - `WS('<an IP>', 443, 2, loggers=…)` yields `_ip == 'venus.web.telegram.org'` and `str(conn) == 'venus.web.telegram.org:443/WS'`;
    - an unmapped DC raises;
    - `_try_connect` catches only `(IOError, asyncio.TimeoutError)`.
  - **Source:** found in code, confirmed by probe.
- **Can the offline tests reach every construction path without Telegram?**
  - **Status:** CLOSED. The probe confirmed:
    - `_get_dc` reads the client class's cached `_config`, so a test can preset a config with DC options;
    - `_create_exported_sender` builds `self._connection(dc.ip_address, dc.port, dc.id, …)`;
    - `MTProtoSender` takes an `auth_key` and `auto_reconnect`, so its real reconnect can be driven against a local server.
    - The probe's earlier end-to-end test (7/7) showed Telethon's real `MTProtoSender` running over the WebSocket adapters against a local TLS server.
  - **Source:** found in code, confirmed by probe.

#### Execution Blockers

- **E1 — the maintainer's explicit go for the live run on the real account.**
  - **What must happen:** the maintainer says go.
  - **Who:** the maintainer. The run happens in the operator's environment, from the brief written in step 13.
  - **Blocks:** step 14.
  - **Status:** **WAIVED by the maintainer, 2026-11-26** — "No need for live run. Live run will be kind of tested … after the release, and when we test it, we will understand." Step 14 is not run before the merge. The pre-build prototype check on the account PASSED (`critic.md`), and the built code is observed in use after the release.

### How this implementation moves toward desired state

**Today:** `ConnectionEngine._new_client` builds every client with Telethon's default connection class, which dials a data centre's IP.

**The change:**
1. **Two new modules:**
   - a standard-library-only WebSocket opener (`tgdata/ws_stream.py`) that raises only standard-library errors;
   - a Telethon connection class that hands Telethon the DC's hostname in place of the IP it was given (`tgdata/websocket_transport.py`).
2. **Small, conditional edits to existing code:**
   - the config reader learns `transport`;
   - the factory passes `connection=` only for `websocket`, importing the class on demand;
   - two connect wrappers let the new error through, like `AuthRequiredError`;
   - the route line and `health_check()` name the transport;
   - the login binding includes `transport` only when it is not `tcp`.

Because every consumer builds clients through the factory, `TgData`, `AccountPool`, `Worker` and `LoginFlow` gain the transport without edits.

**Proof:**
- an offline smoke test, `test_50`, proves no IP on every path, the classification, the unchanged default, and the absence of health noise;
- a canary in the same test guards the Telethon internals the class relies on;
- the docs are corrected.

The live run then confirms the remaining account-level unknowns.

**Order.** The default-path values are captured *first*, before any code changes, so "unchanged" is measured against reality, not memory. Production code then lands bottom-up — stream, class, config, factory, binding — so each step only adds to something that already exists and is tested. A missing piece would show as a failing test, not a silent fallback.

### High-Level Summary

| Step | Description | Expected Output |
|------|-------------|-----------------|
| 1 | Capture today's default-path values | `test_50` skeleton holding today's constructor kwargs, route text and binding hash as literals |
| 2 | WebSocket opener | `tgdata/ws_stream.py` (standard library only) |
| 3 | The connection class and the DC map | `tgdata/websocket_transport.py` (`ConnectionWebSocket`) |
| 4 | The `transport` config key, and `TransportConfigError(ProxyConfigError)` | `ConnectionConfig.transport`, validation, the error class defined and exported |
| 5 | Factory branch, wrappers, route line, `health_check` | the transport wired through the one door |
| 6 | Conditional login-binding entry | `LoginFlow` binding includes `transport` only when it is not `tcp` |
| 7 | Test harness, plus stream and class items | test PKI, fake door, recording proxy; items 1–3 |
| 8 | No-IP proof on every construction path | items 4–6, including the mixed pool |
| 9 | Classification, health, default, binding | items 7–10 |
| 10 | Telethon-internals canary, plus the test README entry | item 11; `smoke_tests/README.md` |
| 11 | Docs | comment fix, docstrings, README section, `stepwise_login.md` |
| 12 | Regression run | the offline suites green, results recorded |
| 13 | Live-check script and operator brief | `live_check.py` and `live_check.md` in the work folder — written, not run |
| 14 | Live run on the real account | criterion 14 recorded — **gated by E1** |

---

## Steps

### Step 1 — Capture today's default-path values

#### Proposed changes

Create `tgdata/smoke_tests/test_50_websocket_transport.py` holding only a module docstring, a scratch-config helper and a `BASELINE` dict. The dict's values are computed **now**, on the unchanged code, by a throwaway script, then pasted into the dict as literals.

**What it captures, for one fixed TCP config** (`api_id = 12345`, a fixed `api_hash`, a temp `session_file`, `proxy = socks5://u:p@127.0.0.1:1080`, two pinned identity fields), and again for the same config without a proxy:

- **The constructor keyword arguments** `_new_client` passes to `TelegramClient`. Use test_13's method: stand in for `connection_engine.TelegramClient` with a recorder, so its arguments are seen without building a real client. Capture three call shapes:
  - `_new_client()`;
  - `_new_client(**<the account-operation options>)`;
  - `LoginFlow`'s `_make_client` options.

  Record the keyword arguments except the session object, plus the positional `api_id` / `api_hash`.
- **The route log lines** `_new_client` emits once: the INFO records on the `tgdata.connection_engine` logger.
- **`LoginFlow(<ini>)._binding`** — constructor only: no socket, no login.

#### Output

`test_50_websocket_transport.py` exists with `BASELINE = {...}` literals and a comment saying they were captured at `a199c0c` before any #67 change. Nothing else changes.

#### Safe in nature
True — a new test file; no production code touched.

#### Peripheral concepts
test_13's stand-in `TelegramClient` patch point, `_new_client` client options, `LoginFlow` binding, `_route_logged`

#### Hardness Lvl
2

---

### Step 2 — The WebSocket opener (`tgdata/ws_stream.py`) [folded: Risk 1, robust]

#### Proposed changes

A new module that imports **only the standard library**. It is a rule, checked in step 10, that it never imports Telethon or tgdata. It is adapted from the probe — `client_frame` / `_xor` / `WsReader` / `WsWriter` / `open_websocket`, at `ws_door_probe.py:115–300` — and **drops the probe's `Origin` header**.

**No tgdata error class lives here** [folded: Risk 1, robust]. The module stays standard-library only, so it cannot import `ProxyConfigError`, which lives in `connection_engine.py` beside Telethon.
- Its "stop immediately" cases raise **standard** types: a plain `ValueError` for an IP-literal host, and an unconverted `ssl.SSLCertVerificationError` for a certificate failure.
- Step 3 converts the certificate error into `TransportConfigError`.
- Messages start with `WebSocket transport:`, name the host, and never carry a credential.

**`async def open_websocket(host, *, sock=None, port=443, timeout=None, ssl_context=None) -> (WsReader, WsWriter)`**
- **Refuses an IP literal.** `ipaddress.ip_address(host.strip('[]'))` succeeding raises `ValueError("WebSocket transport: refusing an IP address as the host …")` [folded: Risk 1, robust].
- **TLS.** `ctx = ssl_context or ssl.create_default_context()`. Then either:
  - `asyncio.open_connection(sock=sock, ssl=ctx, server_hostname=host)` when a tunnelled socket is given;
  - or `asyncio.open_connection(host, port, ssl=ctx, server_hostname=host)` for the direct case, where the OS resolves the name.
- **A certificate failure propagates unchanged** as `ssl.SSLCertVerificationError`; step 3 converts it [folded: Risk 1, robust]. Any other TLS or socket error stays an `OSError`, which Telethon retries.
- **The handshake:**
  - **Request:** `GET /apiws HTTP/1.1` with `Host`, `Upgrade: websocket`, `Connection: Upgrade`, a random 16-byte `Sec-WebSocket-Key`, `Sec-WebSocket-Version: 13` and `Sec-WebSocket-Protocol: binary`. **No `Origin`.**
  - **Response reading:** read the status and header block with a 16 KiB cap.
  - **Required:** status `101` and `Sec-WebSocket-Accept == base64(sha1(key + GUID))`. A `Sec-WebSocket-Protocol` that is present must equal `binary`.
  - **Anything else** raises `ConnectionError("WebSocket transport: upgrade to <host> refused (<status line>)")`.
- **One `asyncio.wait_for(…, timeout)`** bounds TLS and the handshake together. On any failure after the TLS stream opened, close it.

**`WsReader.readexactly(n)`** — a byte stream over frames:
- binary (`0x2`) and continuation (`0x0`) payloads are appended to one buffer;
- ping (`0x9`) is answered with a masked pong through the shared writer; pong (`0xA`) is ignored;
- close (`0x8`) is answered with one close frame, then the reader is marked closed and raises `asyncio.IncompleteReadError(partial, n)`, as does a transport end-of-file;
- **raised as `ConnectionError`:**
  - a text frame (`0x1`), an unknown opcode, or reserved bits set;
  - a masked server frame;
  - a control frame over 125 bytes, or a fragmented one;
  - a data frame over 16 MiB.
- **After connect, the reader raises nothing but `ConnectionError` / `IncompleteReadError`.** These are the only types Telethon's receive loop handles quietly.

**`WsWriter`:**
- `write(data)` sends one masked, FIN, binary frame per call, which is how the probe ran live;
- `drain()` delegates;
- `close()` sends a close frame (best effort, errors ignored), then closes the transport;
- `wait_closed()` delegates.

#### Output

`tgdata/ws_stream.py` with `open_websocket`, `WsReader` and `WsWriter`, importable with only the standard library.

#### Safe in nature
True — a new module; nothing imports it yet.

#### Peripheral concepts
RFC 6455 client framing, `ssl.create_default_context` / SNI, `asyncio.open_connection(sock=…)`, Telethon's receive-loop exception contract (`connection.py` `_recv_loop`), the probe's tested framing

#### Hardness Lvl
4

---

### Step 3 — The connection class and the DC map (`tgdata/websocket_transport.py`) [folded: Risk 1, robust]

#### Proposed changes

```python
DC_HOSTS = {1: 'pluto', 2: 'venus', 3: 'aurora', 4: 'vesta', 5: 'flora'}   # wss://<name>.web.telegram.org/apiws
DOMAIN, PORT = 'web.telegram.org', 443

from .connection_engine import TransportConfigError   # fully loaded before this lazy import runs: no cycle

def host_for(dc_id) -> str:            # unmapped (CDN, test, unknown) -> TransportConfigError

class ConnectionWebSocket(ConnectionTcpObfuscated):
    _ssl_context = None                # test seam: None = the system trust store

    def __init__(self, ip, port, dc_id, **kwargs):
        super().__init__(host_for(dc_id), PORT, dc_id, **kwargs)   # the IP is dropped here

    async def _connect(self, timeout=None, ssl=None):
        sock = await self._proxy_connect(timeout=timeout) if self._proxy else None
        try:
            self._reader, self._writer = await open_websocket(
                self._ip, sock=sock, port=self._port, timeout=timeout, ssl_context=self._ssl_context)
        except ssl_module.SSLCertVerificationError as e:          # [folded: Risk 1, robust]
            ...close sock...
            raise TransportConfigError(f"WebSocket transport: the certificate of {self._ip} did not verify ({e.verify_message})") from e
        except BaseException:
            ...close sock...
            raise
        try:
            self._codec = self.packet_codec(self)
            self._init_conn()          # ObfuscatedIO captures _reader/_writer here
            await self._writer.drain()
        except BaseException:
            self._writer.close()       # Telethon's disconnect() skips a connect that never completed
            raise
```
The connect argument named `ssl` shadows the module, so the module is imported as `ssl_module`. This exact shape ran live in the REORDER experiment (`experiment_account_check.py`).

- **The provenance comment on `DC_HOSTS`:**
  - an independent client (gotd/td `telegram/dcs/prod.go`, `b4bf604`) uses the same map;
  - the probe of 2026-11-26 verified it;
  - the `-1` media names are never used.
- **The `ssl` argument** — Telethon's TLS-to-IP option — is ignored: TLS is always on. tgdata never passes it.
- **`_proxy_connect` is Telethon's own.** It dials `dest_host=self._ip`, which is the name, and converts python-socks' errors to `ConnectionError`.
- **On any failure after `_proxy_connect` returned a socket,** close the socket before re-raising.
- **The class name.** It is `ConnectionWebSocket`, so Telethon's own INFO line reads `Connecting to venus.web.telegram.org:443/WebSocket...`.
- **Shared state.** There is no mutable class-level state besides the test seam. The class is shared by every account in a process.

#### Output

`tgdata/websocket_transport.py` with `DC_HOSTS`, `host_for` and `ConnectionWebSocket`. Not yet wired to anything.

#### Safe in nature
True — new and unwired.

#### Peripheral concepts
`ConnectionTcpObfuscated` / `ObfuscatedIO`, `Connection.__init__` storing `_ip` / `_port`, `_proxy_connect` with python-socks error conversion, Telethon's four construction sites, `Connection.__str__`

#### Hardness Lvl
3

---

### Step 4 — The `transport` config key, and `TransportConfigError` [folded: Risk 1, robust]

#### Proposed changes

- **`tgdata/models.py` `ConnectionConfig`.** Append `transport: str = 'tcp'` as the **last** field, with a comment ("'tcp' or 'websocket'; how connections reach Telegram"). Appending keeps every existing positional construction valid.
- **`tgdata/connection_engine.py`:**
  - **define** `class TransportConfigError(ProxyConfigError)` directly after `ProxyConfigError` [folded: Risk 1, robust].
    - **Its docstring:** "The WebSocket transport cannot be used as configured or reached: an unknown `transport` value, a data centre with no WebSocket hostname, or a certificate that does not verify. Never retried."
    - **Why a subclass:** every existing check for `ProxyConfigError` also covers it — `TgData`'s polling (`_polling_cannot_recover`, `tgdata.py:97`, which stops for good), the worker (`describe_error`, `worker_protocol.py:262`, which reports `configuration_error`), and user code — with no consumer edit. `AccountPool._failure` still reads it as a `ValueError`, so it stops (`unknown`).
  - In `_load_config`, beside the proxy keys, read `transport` raw with `_first_token(...)`, lowercased:
    - `''` or `'tcp'` → `'tcp'`;
    - `'websocket'` → `'websocket'`;
    - anything else → `TransportConfigError(f"transport = {raw!r} in {self.config_path} — use tcp or websocket")`.
  - Pass `transport=` to `ConnectionConfig(...)`.
- **`tgdata/__init__.py`.** Export `TransportConfigError` next to `ProxyConfigError`, in both the import line and `__all__`.

#### Output

`_load_config()` returns `transport`. A bad value fails before any client is built, `from tgdata import TransportConfigError` works, and `isinstance(TransportConfigError(...), ProxyConfigError)` holds.

#### Safe in nature
False — it touches `_load_config` and `ConnectionConfig`, which every client depends on. With no key, the record is equal to today's apart from the new field holding its default.

#### Peripheral concepts
`ConnectionConfig` dataclass field order, `_first_token` inline-comment handling, the `ProxyConfigError` hierarchy and its consumers (polling, worker, pool), the public exports in `tgdata/__init__.py`

#### Hardness Lvl
2

---

### Step 5 — The factory branch, the connect wrappers, the route line and `health_check` [folded: Risk 1, robust]

#### Proposed changes

In `tgdata/connection_engine.py`:

- **`_new_client`.** After the route-log block, and before the `_client_class(...)` call:
  ```python
  if config.transport == 'websocket':
      from .websocket_transport import ConnectionWebSocket      # only accounts that chose it load it
      client_options = dict(client_options, connection=ConnectionWebSocket)
  ```
  For `tcp`, `client_options` is untouched, so the call is byte-identical. No caller passes `connection=` today (grep: none).
- **The route log line.** Inside the existing once-per-engine block, append `", over Telegram's WebSocket transport by hostname"` to the proxy line and to the direct line, **only** when `config.transport == 'websocket'`. The TCP text is unchanged.
- **`_authenticate`.** Add `except ProxyConfigError: logger.error(...); raise` before `except Exception`, mirroring the existing `AuthRequiredError` clause. It covers `TransportConfigError`, a subclass [folded: Risk 1, robust].
- **`_ensure_connected`.** Add `except ProxyConfigError: raise` before `except Exception` [folded: Risk 1, robust]. Today both wrappers turn every connect error into `ConnectionError`; the configuration error must keep its type, so callers and the pool stop rather than retry.
- **`health_check()`.** Add `'transport': self._config.transport if self._config else None` beside `'proxy'`.

#### Output

`transport = websocket` makes every client built by the factory use `ConnectionWebSocket`: the persistent client, the legacy pool, `ephemeral_client`, owned operations, `_OwnedSource` (whose `_new_client` override calls `super()`), and `LoginFlow` (`_client_base=_LoginClient`). The configuration error passes through `TgData`'s connect wrappers, and the transport is visible in the log and in `health_check()`.

#### Safe in nature
False — it edits the single client factory and two connect wrappers. The new branch and the new clauses are reached only by `websocket` accounts or by the new error, and step 9 proves the TCP path is unchanged.

#### Peripheral concepts
`_new_client` options seam, `_client_class` cache (keyed by base only, unaffected), `_OwnedSource._new_client` override, `LoginFlow._make_client`, `_route_logged`, `AuthRequiredError` pass-through precedent, `health_check` status dict

#### Hardness Lvl
3

---

### Step 6 — The conditional login-binding entry

#### Proposed changes

In `tgdata/login.py`, where `settings` is built (`:156–158`):
```python
if config.transport != 'tcp':
    settings['transport'] = config.transport
```
The binding hash for every TCP config is therefore unchanged. A checkpoint saved under one transport and restored under another fails the existing `hmac.compare_digest` check as `invalid_state`, as a changed proxy does today.

#### Output

The `LoginFlow` checkpoint binding covers a non-default transport. TCP checkpoints restore exactly as before.

#### Safe in nature
False — it edits a security-relevant hash input. It is conditional, and step 9 pins the TCP hash to step 1's literal.

#### Peripheral concepts
`LoginFlow` checkpoint binding (`sha256` of sorted JSON), `hmac.compare_digest` restore check, `invalid_state`

#### Hardness Lvl
2

---

### Step 7 — Test harness, stream items and class items (`test_50` part 1) [folded: Risk 2, robust]

#### Proposed changes

Extend `test_50_websocket_transport.py`, following the smoke-test conventions: async `test_*` functions printing ✓ / ✗, a `main()` summary, and `# To run: python -m tgdata.smoke_tests.test_50_websocket_transport`. It is **fully offline**: loopback sockets only, never Telegram.

**The harness:**
- **`make_pki(tmp)`** runs the `openssl` command to generate a throwaway test certificate authority and a leaf certificate for `*.web.telegram.org`, signed by that authority, in a temp folder. No key is committed. If `openssl` is missing, the TLS items print **SKIPPED (openssl not found)** and the summary counts them as not run.
- **`FakeDoor`** — a local TLS server using the leaf certificate, speaking server-side WebSocket:
  - it records each upgrade request's headers;
  - it answers `101` with the correct accept key and `protocol: binary`, or a scripted status (403);
  - it unmasks client frames into a byte log;
  - scripted actions: send binary, ping, close or text frames; drop the connection; decode Telethon's obfuscated header and first MTProto message (`req_pq_multi`). The decoding logic comes from the probe's end-to-end test.
  - **Modes** [folded: Risk 2, robust]:
    - `mtproto="close_after_first"`, the default: record the first MTProto message, then send a close frame. Telethon's key exchange then fails at once and deterministically, instead of waiting forever — `MTProtoPlainSender.send` awaits `recv()` with no timeout.
    - `mtproto="silent"`, used only by the timeout item.
- **`RecordingProxy`** — a loopback proxy speaking both **HTTP CONNECT** and **SOCKS5** (both no-auth and user / password; the RFC 1928/1929 code follows test_12's `Socks5Relay`). It records every requested `(host, port)`, and forwards every tunnel to `FakeDoor`, whatever host was asked for. That is how a hostname target reaches a local server.
- **Trust.** Tests set `ConnectionWebSocket._ssl_context` to a context trusting the test authority, and restore it afterwards. Calls straight to `open_websocket` pass `ssl_context`.
- **Termination and isolation helpers** [folded: Risk 2, robust]:
  - **`bounded(coro, seconds=5)`** wraps every connect-type call;
  - **`restoring(client)`** is a context manager that, in `finally`, deletes the `_config` (and `_cdn_config`) attribute set on `type(client)` and restores `ConnectionWebSocket._ssl_context`. `_get_dc` caches its config on the client's class, and every client built by `_client_class(TelegramClient)` in the process shares one class;
  - **`delay=0` / `retry_delay=0`** wherever retries are counted. Telethon's default sleeps 1 s between attempts.

**Items:**
1. **The opener's handshake:**
   - the request carries `Sec-WebSocket-Protocol: binary`, a valid key and version 13, and **no `Origin`**;
   - `101` with the right accept key succeeds;
   - a wrong accept key, and a 403, each raise `ConnectionError`;
   - an IP-literal host raises `TransportConfigError` before any socket opens;
   - the default trust store, which does not trust the test authority, raises `TransportConfigError`;
   - a door that never answers times out within `timeout`.
2. **The opener's framing:**
   - bytes round-trip across fragmented and continuation frames and across `readexactly` boundaries (1, 4, 63, 64, 125, 126, 65535, 65536 bytes);
   - a ping is answered with a masked pong;
   - close and end-of-file each raise `IncompleteReadError`;
   - a text frame, a masked server frame, an oversized control frame and a reserved bit each raise `ConnectionError`.
3. **The class:**
   - `ConnectionWebSocket('<an IP>', 443, 2, loggers=…)` holds `venus.web.telegram.org:443`, and no IP anywhere among its attributes;
   - DC 1–5 map to the five planet names;
   - DC 203 and DC 0 raise `TransportConfigError`;
   - `str(conn)` ends with `/WebSocket`;
   - over `RecordingProxy` plus `FakeDoor`, Telethon's real `MTProtoSender` (no key) delivers `req_pq_multi` through the class, and the proxy recorded only `venus.web.telegram.org:443`.

#### Output

Harness classes plus items 1–3 passing.

#### Safe in nature
True — test code only.

#### Peripheral concepts
test_12's `Socks5Relay`, the probe's end-to-end obfuscated-header decoding, `MTProtoSender`, the `openssl` command, smoke-test conventions

#### Hardness Lvl
4

---

### Step 8 — No IP on every construction path (`test_50` part 2) [folded: Risk 2, robust]

#### Proposed changes

Each item builds clients **through the real factory**, from a scratch ini with `transport = websocket` and `proxy = socks5://…` or `http://…` pointing at `RecordingProxy`. Every connect runs inside `bounded(…)`, against a `FakeDoor` in `close_after_first` mode, so a key-less connect ends when the door closes; the assertion is on the proxy's record [folded: Risk 2, robust].

**Items:**

4. **Main connect and reconnect:**
   - `engine._new_client()`, then `client.connect()` with `connection_retries=0` and a short timeout. The record holds only DC 2's name, `venus.web.telegram.org:443` — the default DC of a fresh session.
   - A reconnect through Telethon's real `MTProtoSender`, built with a random `AuthKey` and `auto_reconnect=True`: `FakeDoor` drops the connection after the handshake. The second recorded destination is the same name, so the same connection object was reused.
   - Both runs are done over SOCKS5 and over HTTP CONNECT.
5. **A connection to another DC.**
   - Preset `type(client)._config` with DC options holding IP literals for DC 4, inside `restoring(client)` [folded: Risk 2, robust].
   - Call `await client._create_exported_sender(4)` with a short timeout.
   - The record holds `vesta.web.telegram.org:443` and **no IP**.
6. **The strict paths, the mixed pool and the direct case:**
   - **Strict paths.** For `ConnectionEngine._account_operation`, an `AccountPool` source (`_OwnedSource._new_client`) and `LoginFlow._make_client`: the built client's `_connection is ConnectionWebSocket`, and one connect attempt records only planet names. Build pool sources with the existing offline pool builders (`tgdata/smoke_tests/pool_storage_cases.py`, as test_31 does), not hand-assembled internals [folded: Risk 2, robust].
   - **The mixed pool.** Two sources in one pool, one `tcp` and one `websocket`. The TCP client keeps Telethon's default connection class, and its tunnel request is the DC's IP, as today. The WebSocket client's requests are names only. Neither changes the other.
   - **The direct case** (`websocket` with no proxy). Spy on `ws_stream.open_websocket`: it is called with the hostname and `sock=None`, and nothing passes an IP.

#### Output

Items 4–6 passing: criteria 2, 3 and 4 shown on every path.

#### Safe in nature
True — test code only.

#### Peripheral concepts
`_get_dc` / client-class `_config` cache, `_create_exported_sender`, `MTProtoSender` reconnect, `_account_operation` strict options, `_OwnedSource`, `LoginFlow._make_client`, `AccountPool` sources

#### Hardness Lvl
4

---

### Step 9 — Classification, health, the default path and the binding (`test_50` part 3) [folded: Risk 1, robust; Risk 2, robust]

#### Proposed changes

7. **Classification through Telethon's real retry loop:**
   - **A refused upgrade is retried, then classified as `transport`.** `FakeDoor` returns 403 on every attempt. `MTProtoSender` with `retries=2, delay=0` makes three attempts (`retry_range(2)` yields 3), counted at the door, then raises Telethon's `ConnectionError` [folded: Risk 2, robust]. `AccountPool._failure(error, None)` — called on a minimal stand-in carrying the pool's default policy — returns `('transport', True, …)`.
   - **A certificate failure stops at once, classified as `unknown`.** With the default trust store: exactly **one** attempt, the `TransportConfigError` escapes unchanged, and `_failure` returns `('unknown', False, None)`.
   - **Configuration errors stop before any connection.** An unknown `transport` value raises at `_load_config`, and an unmapped DC raises at construction.
   - **`TgData`'s wrappers pass the error through.** With a stub client whose `connect()` raises `TransportConfigError`, `_authenticate` and `_ensure_connected` re-raise it as itself. A plain `OSError` is still wrapped as `ConnectionError("Failed to …")`, as today.
   - **The consumers that key on `ProxyConfigError` recognise it** [folded: Risk 1, robust]: `tgdata.tgdata._polling_cannot_recover(TransportConfigError(...))` is `True`, and `worker_protocol.describe_error(...)['category'] == 'configuration_error'`.
8. **No health noise, and quiet mid-session closes:**
   - `health.classify(e)` is `None` for every transport error above;
   - a mid-session close from `FakeDoor` is logged by Telethon at WARNING ("Server closed the connection"), with **no** "Unexpected exception" record, checked by capturing the `telethon` loggers.
9. **The default path is byte-identical.** Re-run step 1's captures and compare them to `BASELINE`:
   - the constructor kwargs for all three call shapes, with and without a proxy;
   - the route log lines;
   - the TCP binding hash;
   - `'tgdata.websocket_transport' not in sys.modules` after building and using a TCP client, checked in a fresh subprocess.
10. **The binding and observability:**
    - a `websocket` config's binding hash differs from the TCP one;
    - a checkpoint exported under `websocket` and restored with a `tcp` config raises `invalid_state`;
    - `health_check()['transport']` reports `'websocket'` / `'tcp'`;
    - the WebSocket route line contains "over Telegram's WebSocket transport by hostname".

#### Output

Items 7–10 passing: criteria 1, 5, 6, 7, 8 and 9.

#### Safe in nature
True — test code only.

#### Peripheral concepts
`MTProtoSender._try_connect`, `AccountPool._failure`, `health.classify`, Telethon logger names, `LoginFlow.export_state` / restore (`invalid_state`), subprocess import check

#### Hardness Lvl
4

---

### Step 10 — The Telethon-internals canary and the test README entry

#### Proposed changes

**Item 11** in `test_50`, headed **"RUN AFTER ANY TELETHON UPGRADE"** in the style of test_14. It checks behaviour wherever behaviour is observable:
- **The connection constructor:** `Connection.__init__` accepts `(ip, port, dc_id, *, loggers, proxy, local_addr)` and stores the first argument as `_ip`. Behavioural: construct it and read the attribute back.
- **The connect method:** `Connection.connect` calls `self._connect(timeout=…, ssl=…)`, observed by subclassing with a recorder.
- **The proxy code:** `_proxy_connect` dials `self._ip` and raises a `ConnectionError` subclass when the proxy port is closed. Observed against a closed loopback port, and through `RecordingProxy`.
- **The obfuscation layer:** `ObfuscatedConnection._init_conn` reads `_reader` / `_writer` at the moment the header is written, and `_try_connect` retries only `IOError` / `asyncio.TimeoutError`. Both are observed through items 3 and 7.
- **The source-text checks** — used only where no behaviour can be observed offline:
  - `telegrambaseclient` builds connections in exactly four places, each passing a DC id (`self._connection(` occurs four times);
  - `cdn_supported` appears nowhere under `telethon/client/`.
- **The stream module stays Telethon-free:** `ws_stream` imports only the standard library, checked by parsing its `import` statements.

Add a `test_50_websocket_transport.py` entry to `tgdata/smoke_tests/README.md`: what it covers, that it is offline, that it needs the `openssl` command, and that the canary part must run after any Telethon upgrade.

#### Output

Item 11 passing, and the README entry.

#### Safe in nature
True — test code and docs.

#### Peripheral concepts
test_14's canary convention, Telethon 1.45.0 internals, `ast` import parsing

#### Hardness Lvl
3

---

### Step 11 — The documentation

#### Proposed changes

- **`connection_engine.py`, the comment above `_PROXY_SCHEMES` (`:153–154`).** Replace "Telegram's servers are addressed by IP, so remote DNS is moot" with: remote DNS is always on, and it is what carries the WebSocket transport's hostname to the proxy. `socks5h` / `socks4a` remain accepted spellings.
- **The docstrings:**
  - `_new_client` gains one paragraph: with `transport = websocket` the client carries `ConnectionWebSocket`, and every connection reaches Telegram by hostname, never by IP;
  - `parse_proxy_url`'s docstring notes that remote DNS is always requested.
- **`README.md`.** A new subsection after "Connecting through a proxy", titled "Connecting through Telegram's WebSocket door (optional)". It covers:
  - the key and an example;
  - what the proxy must allow: a tunnel to `*.web.telegram.org:443`, by HTTP CONNECT or SOCKS with remote DNS;
  - never an IP and no fallback, with the five names;
  - direct by name when no proxy is set, with `require_proxy` unchanged;
  - the failures — `TransportConfigError` stops (unknown value, unknown DC, certificate), anything else is a retryable `ConnectionError`;
  - how to confirm it is active: the route line, `health_check()['transport']`, and Telethon's `Connecting to <host>:443/WebSocket` INFO line;
  - that discovery waits out connect errors until `max_offline`;
  - the verified Telethon version, and the canary;
  - the accepted risks from `desc.md`.

  New text says "network transport", and the existing "transport envelopes" wording is untouched.
- **`docs/stepwise_login.md` (`:90`).** "Restoration checks the API, proxy, proxy requirement, a non-default network transport and explicitly configured device settings."

#### Output

No statement in the repository is false once the key exists, and the README documents the feature (criteria 12–13).

#### Safe in nature
True — comments and docs only.

#### Peripheral concepts
README proxy and device-identity sections, `docs/stepwise_login.md`, the "transport envelopes" wording in `README.md` / `docs/account_operations.md`

#### Hardness Lvl
2

---

### Step 12 — Regression run

#### Proposed changes

Run `python -m tgdata.smoke_tests.test_50_websocket_transport`, then every **offline** suite whose subject the change touches:
- test_12, items 1–5 — the loopback-only items; item 6 talks to Telegram and is **not** run;
- test_13, test_14, test_15, test_16, test_17;
- test_31, test_32, test_33;
- test_37, test_39, test_40, test_41;
- test_48.

Before running any suite, read its header, and skip any item that would reach Telegram or need an account config. Record the pass counts and every skip, with its reason, in `devdocs/work/67-websocket-hostname-transport/verify.md`.

#### Output

The offline suites green, and `verify.md` with results and skips.

#### Safe in nature
True — runs only.

#### Peripheral concepts
the smoke-test suites' network requirements

#### Hardness Lvl
2

---

### Step 13 — The live-check script and the operator brief (written, not run) [folded: Risk 3, robust]

#### Proposed changes

- **`devdocs/work/67-websocket-hostname-transport/live_check.py`**, for the operator's environment:
  - it reads a tgdata config path. It **refuses to run without `--exclusive-confirmed`**, and works on a copy of the session file, leaving the original untouched [folded: Risk 3, robust]. Telegram revokes a key used from two addresses at once (`AUTH_KEY_DUPLICATED`, Telethon's `AuthKeyDuplicatedError`: "used under two different IP addresses simultaneously, and can no longer be used");
  - it reports `AUTH_KEY_DUPLICATED` as **INVALID RUN**, never as a failure of the transport;
  - it is modelled on `experiment_account_check.py`, which already ran live with these safeguards, but drives tgdata's own built code through its public API;
  - it requires `transport = websocket` and a proxy in that config;
  - it runs, through tgdata's public API:
    1. `TgData(config)` connects with the existing session — no new login;
    2. one read of a small known group;
    3. a media download that needs a connection to another DC, located by the script, which lists the DCs it touched;
    4. an idle wait of 330 s, then a second read on the same client.
  - it prints each step's result, `health_check()`, and every `Connecting to …` line Telethon logged, which must all be hostnames;
  - it records any Telegram error, with the call that produced it.
- **`live_check.md`** — the brief, written like `experiment_account_check.md`: background; safety — the first step is stopping every application that uses the session, on every machine [folded: Risk 3, robust]; setup, with `python-socks[asyncio]` required for every proxy kind; the command; how to read the output, where a cut followed by a reconnect by name is expected; and what to send back, privately.

#### Output

The two files, committed. **Nothing is run.**

#### Safe in nature
True — new files in the work folder; no network.

#### Peripheral concepts
`TgData` public API, `health_check`, Telethon INFO logging, session backup

#### Hardness Lvl
2

---

### Step 14 — The live run on the real account — **gated by E1** [folded: Risk 3, robust]

#### Proposed changes

After the maintainer's explicit go — and with every other user of the session stopped (`--exclusive-confirmed`) — the operator runs `live_check.py` per `live_check.md` and returns the output privately. Record the result for criterion 14 in `verify.md`:
- login;
- read;
- the other-DC download;
- the 330 s idle;
- hostname-only `Connecting to` lines;
- any errors seen only under WebSocket.

A failure in the name map or the obfuscation header is handled locally in `ConnectionWebSocket`, per the finding's refinement triggers.

#### Output

Criterion 14 recorded.

#### Safe in nature
False — it touches the real account and Telegram.

#### Peripheral concepts
the real account's session, the proxy, Telegram's treatment of the web transport

#### Hardness Lvl
2
