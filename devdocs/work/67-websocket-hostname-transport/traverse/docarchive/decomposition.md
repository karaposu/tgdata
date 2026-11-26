---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

/Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/_branch.md — inputs also in that folder: articulate_simple.md, surfacing.md, articulate_warm.md, sensemaking.md (its SV6 stabilized model is the whole to decompose: the WebSocket transport design for tgdata #67 — config key, door branch, the connection class, the WebSocket adapters, the error taxonomy, the login binding entry, observability, docs, tests — with the open MEDIUM/LOW items A3, A6, A10, A14). SAVE the output as /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/decomposition.md

---

# Decomposition — the WebSocket transport for tgdata (issue #67)

**The whole, in one paragraph** — sensemaking's SV6, the prerequisite. `transport = websocket` is a Telethon connection class chosen per account by one config key and passed through tgdata's one door (`_new_client`).
- **At construction** the class names the DC: `<planet>.web.telegram.org:443`.
- **On connect** it opens a socket by name, through Telethon's own `_proxy_connect` or directly. It then does TLS with SNI and verification and the `/apiws` binary WebSocket handshake, and hands Telethon's own obfuscated codec a byte stream over binary frames.
- **Everything else is reuse.** Failures are classified by base class. `LoginFlow`'s binding gains `transport` only when it is not `tcp`. The default path is byte-identical.

**Re-checked in Telethon 1.45.0 for this step:**
- **Construction happens outside the retry.** The connection object is built *inside* `client.connect()` and `_create_exported_sender`, outside `MTProtoSender._try_connect` (`telegrambaseclient.py:560`, `:842`). An exception from the class's `__init__` therefore escapes immediately and is never retried.
- **The receive loop handles only two error families.** It treats `IOError` / `IncompleteReadError` as "server closed the connection": a WARNING, then disconnect. Any other exception is logged as "Unexpected exception in the receive loop" with a traceback (`connection.py:340–356`).
- **`ObfuscatedIO` captures the reader and writer at `_init_conn` time.** `ObfuscatedIO.__init__` reads `connection._reader` / `_writer` then (`tcpobfuscated.py:13–14`), so the adapters must be installed before `_init_conn()`.
- **`ssl.SSLCertVerificationError` is an `OSError`.** Left alone, Telethon would retry a certificate failure as a transient `IOError`.
- **tgdata never passes `local_addr`.** There are zero hits in `tgdata/`.

---

## Step 1 — Coupling map

**Elements.**
- **E1** — the config key `transport`, with `ConnectionConfig.transport` and the config-time check of its value.
- **E2** — the door branch: `_new_client` adds `connection=` only for `websocket`.
- **E3** — the DC→hostname map: a fixed constant, and an error for unmapped DCs.
- **E4** — the connection class:
  - `__init__` does the naming;
  - `_connect` does the socket by name, then calls the stream opener, installs the adapters, and runs `_codec`, `_init_conn` and `drain`.
- **E5** — the WebSocket stream:
  - TLS with SNI and verification;
  - the HTTP upgrade (`/apiws`, `binary`, `Origin`, the accept check);
  - the frame reader and writer: masking, fragmentation, ping→pong, close.
- **E6** — the error taxonomy: the fail-fast class family, the transient family, and which failure maps to which.
- **E7** — the login binding entry, present only when the value is not `tcp`.
- **E8** — observability: the route log line names the transport; `health_check()` gains a `transport` field.
- **E9** — the docs:
  - the `connection_engine.py:154` comment;
  - the `parse_proxy_url` and `_new_client` docstrings;
  - the README subsection;
  - `docs/stepwise_login.md:90`;
  - the outside-world risk register.
- **E10** — the offline integration guarantees: no IP on any construction path, the default byte-identical, and the Telethon-internals canary.
- **E11** — the live calibration on the real account (A14).

**Propagation ("if I change A, must B change?"):**

| Pair | Coupling | Why |
|---|---|---|
| E4 ↔ E5 | **strong** | E4 consumes E5's stream object, and Telethon's codec reads it through `readexactly` and `write`/`drain`/`close`/`wait_closed`. A change to E5's object breaks E4. |
| E4 ↔ E3 | strong | Naming at construction *is* the map lookup. The map's exhaustiveness decides E4's error. |
| E5 ↔ E6 | moderate | E5 must raise mid-session faults as `IOError` / `IncompleteReadError`, or Telethon logs tracebacks. Connect-time faults raise the taxonomy's classes. |
| E4 ↔ E6 | moderate | E4 converts `SSLCertVerificationError` to fail-fast, and raises the unmapped-DC error at `__init__`. |
| E1 ↔ E6 | moderate | An unknown `transport` value raises the taxonomy's config-family class. |
| E1 → E2 | moderate | The door reads `config.transport`. |
| E2 → E4 | weak | The door references the class; the signature is Telethon's own. |
| E1 → E7 | moderate | The binding reads `config.transport` and includes it conditionally. Its invariant (the TCP hash is unchanged) is separate. |
| E1 → E8 | weak | Reads `config.transport`. |
| E2, E8 | weak | Both live in `connection_engine.py`, and both read the same value. |
| E10 → E2, E4, E5, E6, E7 | moderate (contract) | The tests pin each contract. They share one harness: a local TLS WebSocket server plus a recording proxy. |
| E9 → all | weak (one-way) | The docs describe the decisions; nothing reads the docs. |
| E11 → all | weak (one-way, after build) | It runs the finished build. |

**Clusters (peaks):**
- **The wire** — E3, E4, E5, the high-coupling core.
- **Selection** — E1, E2, E8.
- **Identity** — E7.
- **The contract** — E6, consumed by the wire and by selection.
- **Proof** — E10, E11.
- **Description** — E9.

**Valleys (boundaries):**
- **B1, inside the wire, between E5 and E3+E4.** One narrow interface crosses it: a stream object made from a host name and an optional connected socket. This is the boundary the probe already drew: `open_websocket` and `WsReader` / `WsWriter` on one side, `WsConnection` on the other.
- **B2, between the wire and selection:** the class object.
- **B3, between selection and identity:** one string field.
- **B4, between the contract and everything else:** class names plus a mapping table.
- **B5, between proof and the rest:** contracts only.
- **B6, description:** one-way.

## Step 2 — Boundaries (top-down)

The initial partition:
- **P0** — the contract (E6);
- **P1** — the WebSocket stream (E5);
- **P2** — the Telethon connection class with the DC map (E3, E4);
- **P3** — selection and visibility (E1, E2, E8);
- **P4** — the login binding (E7);
- **P5** — the offline guarantees (E10);
- **P6** — the docs and risk register (E9);
- **P7** — the live calibration (E11).

B1 is a **single-point boundary**: one interface, used once in `_connect`. B3 and B4 are single-point too. B5 is **diffuse**: tests touch every piece, but only through contracts.

## Step 3 — Bottom-up validation

**The atoms:**
- the map constant;
- the naming lookup;
- the socket-by-name call (`_proxy_connect` or direct);
- the TLS context;
- the upgrade request and accept check;
- the frame encoder (masked);
- the frame decoder (fragments, control frames);
- the adapter's `readexactly` buffer;
- the codec plug-in sequence;
- the cert-error conversion;
- the config parse;
- the door branch;
- the log-line text;
- the health field;
- the binding insert;
- each doc edit;
- each test.

**Do the atoms group into the Step 2 clusters?**
- **Yes, for the encoder, decoder, buffer, TLS and upgrade.** All sit in P1, matching the probe's tested split. Nothing in them knows Telethon, DCs or tgdata config.
- **The cert-error conversion is a split atom.** The SSL error surfaces inside P1's TLS step, but *classifying* it belongs to P0's table. Where does the `raise` live?
  - **Resolution:** P1 raises a P0 class directly — the contract is defined first. P2 does not need to wrap P1's errors. **Confidence: high**, once P0 exists before P1.
- **The socket-by-name call stays in P2, not P1.** It needs Telethon's `_proxy_connect` and `self._proxy`. P1 receives an already-connected socket, or none, for the direct path.
- **The direct path (no proxy) is the one place P1 opens its own connection,** via `asyncio.open_connection(host, port, ssl=…, server_hostname=host)`. P1 then never resolves names itself; asyncio's resolver does. That is not a split: P1's interface accepts `sock=None`.
- **The log line and the health field** group with the door: same module, same input. There is no missing boundary.

**Confidence:** top-down and bottom-up agree on every boundary. One atom (the cert-error conversion) needs P0 first, which is an ordering fact, not a boundary error.

---

## Step 4 — Question tree

### P0 — Which failures fail fast and which are retried, and as what classes?

The contract. Defined first, consumed by P1, P2 and P3.

- [ ] **The fail-fast family is defined** (`ValueError` subclasses, credential-free messages). Its members:
  - an unknown `transport` value, at config time;
  - an unmapped DC, at connection construction;
  - certificate verification failure, at connect.
- [ ] **Its relation to the existing `ProxyConfigError(ValueError)`** is decided: a subclass, or a sibling under one config-family name. Either way, `AccountPool._failure` classifies it as `unknown` (stop) with no change to `_failure`.
- [ ] **The transient family** is `ConnectionError` (an `IOError`). Its members:
  - a non-`101` upgrade, or a bad `Sec-WebSocket-Accept`;
  - a TLS or TCP reset;
  - a WebSocket protocol violation (a text frame, a bad opcode, an oversized control frame);
  - a server close frame or EOF.

  Proxy errors stay Telethon's / python-socks' own, unchanged.
- [ ] **The mid-session rule:** after connect, every fault P1 raises is an `IOError` or `IncompleteReadError`. Never a `ValueError`, which would produce a traceback in Telethon's receive loop.
- [ ] **Each class's message names the host and the step,** never a credential. Example: "WebSocket upgrade to vesta.web.telegram.org refused: HTTP 403".
- [ ] **A6 is ruled:** no cause-chaining mechanism. Transparency is the same as TCP's; transient causes appear in Telethon's connect warnings.

### P1 — Given a host name, and optionally an already-connected socket to it, how is a verified binary WebSocket byte stream opened?

- [ ] **The interface is fixed:** `open_websocket(host, *, sock=None, port=443, timeout) -> (reader, writer)`.
  - `reader.readexactly(n)`;
  - `writer.write(b)`, `await writer.drain()`, `writer.close()`, `await writer.wait_closed()`.
- [ ] **TLS:**
  - `ssl.create_default_context()`, so verification is on;
  - `server_hostname=host`, so SNI is the name;
  - `asyncio.open_connection(sock=…)` when a socket is given; `asyncio.open_connection(host, port, …)` when not;
  - no use of Telethon's `ssl.wrap_socket` helper;
  - a cert failure raises P0's fail-fast class.
- [ ] **The upgrade:**
  - `GET /apiws HTTP/1.1`, `Host`, `Upgrade: websocket`, `Connection: Upgrade`, a random `Sec-WebSocket-Key`, `Sec-WebSocket-Version: 13`, `Sec-WebSocket-Protocol: binary`, `Origin: https://web.telegram.org`;
  - a `101` is required, and the accept hash is checked;
  - any other answer raises P0's transient class.
- [ ] **Framing (RFC 6455, client side):**
  - every frame sent is masked and binary;
  - received binary and continuation frames are joined into one byte stream behind `readexactly`;
  - ping is answered with pong;
  - close (or EOF) is answered with close, and further reads raise `IncompleteReadError`;
  - text frames or unknown opcodes raise `ConnectionError`.
- [ ] **No extensions,** no compression, and no dependency outside the standard library. **A9 is ruled:** hand-written, adapted from the probe.
- [ ] **One `timeout` bounds TLS plus upgrade together.**
- [ ] **Self-contained:** nothing in P1 imports Telethon or tgdata config.

### P2 — How does a Telethon 1.45.0 connection reach DC *n* only by name and carry its obfuscated transport over P1's stream?

- [ ] **The class subclasses `ConnectionTcpObfuscated`:** abridged codec, Telethon's own `ObfuscatedIO`, and the plain header the probe used. No DC bytes in the header.
- [ ] **A3 is ruled:** the map is one module constant, `{1: 'pluto', 2: 'venus', 3: 'aurora', 4: 'vesta', 5: 'flora'}` with `.web.telegram.org`. There is no override, and the `-1` names are never used.
- [ ] **`__init__(ip, port, dc_id, …)`:**
  - looks up `dc_id`; any unmapped id, a test-server DC included, raises P0's fail-fast class;
  - sets `self._ip = host` and `self._port = 443`;
  - **discards the IP Telethon passed.** From then on the object holds no IP at all.
- [ ] **`_connect(timeout, ssl)`:**
  - with a proxy: `sock = await self._proxy_connect(timeout)`. Telethon's code, `dest_host = self._ip`, the name; `rdns` is already true;
  - with no proxy: `sock = None`;
  - then `self._reader, self._writer = await open_websocket(self._ip, sock=sock, timeout=…)`;
  - then exactly the base sequence: `self._codec = self.packet_codec(self)`, `self._init_conn()`, `await self._writer.drain()`.
- [ ] **The `ssl` argument** (Telethon's TLS-to-IP option) is refused or ignored. tgdata never passes it.
- [ ] **All four Telethon construction sites** — main connect, exported sender, its reconnect, CDN client — dial only the mapped name. This needs no Telethon change, because `dc_id` already reaches `__init__`.
- [ ] **No other Telethon method is overridden.**

### P3 — How does an account select the transport, and how does the operator see that it is active?

- [ ] `_load_config` reads `transport` from `[Telegram]` into `ConnectionConfig.transport`.
  - It is absent or `tcp` by default; `websocket` is the other value.
  - Matching is case-insensitive, and whitespace is trimmed.
  - Any other value raises P0's config class before a socket opens.
- [ ] **Transport and proxy are independent** (A7). `require_proxy` is unchanged, and `websocket` without a proxy is allowed and goes direct by name.
- [ ] **`_new_client`** adds `connection=<P2 class>` to the `TelegramClient(...)` call only when `transport == 'websocket'`.
  - For `tcp` the call's arguments are byte-identical to today's.
  - `_client_base`, `_client_class`, the mixins and the strict options are untouched.
- [ ] **The one-time route log line** gains "over WebSocket by name" only for `websocket`. The TCP text is unchanged.
- [ ] **`health_check()`** reports `transport` (A6, recommended). Whether the TCP output gains the key is decided here; adding a key to a dict is additive.
- [ ] **No consumer changes.** `TgData`, `AccountPool` (`_OwnedSource._new_client` adds its strict options to the same call), `Worker` and `LoginFlow` inherit the transport through the door.

### P4 — Does the transport change the login checkpoint's binding, and without breaking existing checkpoints?

- [ ] **`transport` is added to `LoginFlow`'s binding settings only when it is not `tcp`** (A8).
- [ ] **A TCP account's binding hash is bit-identical to today's**, proven by a test that pins the current hash for a fixed config.
- [ ] **Changing the transport between `start` and `submit` invalidates the checkpoint,** as changing the proxy does today.
- [ ] **`docs/stepwise_login.md:90`** lists the field and its conditional presence.

### P5 — How is it proven offline that no IP is ever dialled, that the default is unchanged, and that drift in Telethon's internals is caught?

- [ ] **The harness:**
  - a local TLS WebSocket server with a test CA, serving `/apiws` and echoing or speaking enough MTProto for Telethon to connect;
  - a recording proxy (HTTP CONNECT and SOCKS5) that logs every requested destination. It extends `test_12`'s relay.
- [ ] **No IP, on every path.** Main connect, reconnect (non-strict client), exported sender to another DC, and the strict-options path (`_account_operation`, `_OwnedSource`, `LoginFlow`): every recorded destination is a mapped name, and never an IP literal.
- [ ] **Construction-time naming.** A connection constructed with an IP and `dc_id=2` holds `venus.web.telegram.org` and no IP.
- [ ] **The taxonomy,** each tested through Telethon's real `_try_connect` and `AccountPool._failure`:
  - an unknown value and an unmapped DC fail fast with no retry;
  - a cert failure fails fast;
  - a 403 upgrade is retried as transient;
  - a server close mid-session gives a WARNING with no traceback.
- [ ] **The default is byte-identical:**
  - the `TelegramClient` constructor kwargs for `tcp` match today's;
  - the TCP binding hash is pinned;
  - the TCP log text is unchanged.
- [ ] **A10 is ruled:** no runtime version refusal for this transport. A canary in the `test_14` style, "run after any Telethon upgrade", asserts the internals P2 relies on:
  - the `Connection.__init__` signature;
  - `_connect(timeout, ssl)`;
  - `_proxy_connect` using `self._ip`;
  - `ObfuscatedConnection._init_conn` reading `_reader` / `_writer`;
  - the four construction sites passing `dc_id`.
- [ ] **The keep-alive under the transport:** Telethon's ping is sent over the WebSocket stream on a held connection (using a short loop interval, or by driving `_keepalive_ping` directly).

### P6 — What must the docs say so that nothing is false and an operator can use the transport safely?

- [ ] **`connection_engine.py:154`'s "remote DNS is moot"** is corrected. Remote DNS is what carries the WebSocket host name to the proxy.
- [ ] **The `parse_proxy_url` and `_new_client` docstrings** mention the transport.
- [ ] **A README subsection, "Connecting through Telegram's WebSocket door":**
  - the key;
  - the proxy requirement (tunnel to `*.web.telegram.org:443`, by CONNECT or SOCKS with remote DNS);
  - "never an IP, no fallback";
  - the direct-by-name case;
  - what failures look like (P0);
  - how to confirm it is active (P3);
  - the verified Telethon version and the canary.
- [ ] **"Transport" in the new text means the network transport.** The request-"envelope" wording elsewhere is untouched.
- [ ] **The outside-world register:**
  - the door is unpublished;
  - a desktop-app account arrives through the web door;
  - the relays' rate limits;
  - the planet map is calibrated on one day's probe;
  - login keys made over TCP are expected to work (keys belong to a DC) but are proven only live;
  - the trust store must be present on servers.

### P7 — Does the finished transport hold for the real account, through the real proxy, beyond the one-day probe?

**Execution-gated:** it runs only on the maintainer's go.
- [ ] **Login, a read, and a download from another DC** run over `transport = websocket` on the real account, with every exit from the assigned address and none by IP.
- [ ] **An existing TCP-made session file keeps working** over the door.
- [ ] **A held connection survives more than 300 s idle** thanks to Telethon's keep-alive.
- [ ] **Any failure is recorded** against the A14 calibration. A map failure is a blocker for `desc.md` / `plan.md`, not a redesign.

---

## Step 5 — Interface map (data and assumptions)

**P0 → P1** (contract, one-way).
- *Flows:* the class names and the fault→class table.
- *Assumptions:*
  - P1 assumes the fail-fast class exists for the cert failure, and that `ConnectionError` is the transient base;
  - P0 assumes P1 never raises a `ValueError` after connect — the mid-session rule;
  - hidden-coupling check: Telethon's `_recv_loop` handles only `IOError` / `IncompleteReadError` quietly, so the rule is load-bearing, not stylistic.

**P0 → P2** (contract, one-way).
- *Flows:* the unmapped-DC class.
- *Assumption:* raising from `__init__` escapes Telethon unretried. Verified: construction happens outside `_try_connect`.

**P0 → P3** (contract, one-way).
- *Flows:* the config-family class for an unknown `transport`.
- *Assumption:* it is a `ValueError`, so `AccountPool._failure` maps it to `unknown`.

**P1 → P2** (interface, one-way).
- *Flows:* `open_websocket(host, *, sock, port, timeout) -> (reader, writer)`.
- *Assumptions:*
  - P2 assumes `reader` / `writer` satisfy every method Telethon calls: `readexactly`, `write`, `drain`, `close`, `wait_closed`;
  - P1 assumes `host` is a DNS name, never an IP, and that a given `sock` is already connected to that name. P2 guarantees both.
  - Hidden-coupling check: `ObfuscatedIO` captures `connection._reader` / `_writer` at `_init_conn`. P2 must assign them *before* calling `_init_conn` — an ordering assumption, stated in P2's criteria.

**P2 → P3** (artifact, one-way).
- *Flows:* the class object.
- *Assumption:* its constructor signature is Telethon's `Connection` signature. Telethon asserts `isinstance(connection, type)`, so no factory or partial is allowed. This is why the map has no per-account override (A3).

**P3 → P4** (data, one-way).
- *Flows:* the `ConnectionConfig.transport` string.
- *Assumption:* P4 sees the normalised value (`tcp` / `websocket`). Normalisation therefore happens once, in `_load_config`, or else the binding could differ for `WebSocket` vs `websocket`.

**P1, P2, P3, P4 → P5** (contracts, one-way).
- *Flows:* each piece's verification criteria become tests.
- *Assumption:* P5's harness can stand in for Telegram's door locally, with TLS to a test CA. P1 therefore needs a seam for the trust store or SSL context in tests (for example, the context passed as a parameter defaulting to `create_default_context()`). That is a small interface addition, captured here so it does not surface late.

**P0–P5 → P6** (information, one-way). Decisions become text.

**P5 → P7** (prerequisite, one-way). The offline suite is green before any live run.

**Removed by design:** P2 ↔ Telethon's DC switching has no flow, because `dc_id` already reaches the class. P3 ↔ the mixins has no flow, because they work above the sender.

## Step 6 — Dependency order

1. **P0** — the contract. Must precede P1, P2 and P3, since they raise its classes.
2. **P1 and P2, in parallel,** once P1's signature (Step 5) is fixed at contract level. P2 can be written against the signature, and P1's framing can be tested alone.
3. **P3** — needs P2's class to exist (an import), and P0's config class.
4. **P4** — needs P3's `ConnectionConfig.transport`. It can run in parallel with P3 once that field's name is fixed.
5. **P5** — needs P1–P4.
6. **P6** — drafted from this decomposition in parallel; finalised after P5, so the docs state what was tested.
7. **P7** — last, gated on the maintainer's go (an execution blocker, not a planning blocker).

There are no cycles.

## Step 7 — Self-evaluation (full, seven dimensions)

| Dimension | Result | Note |
|---|---|---|
| **Independence** | PASS | Each question answers without reading siblings, except through the Step 5 interfaces. P1 is fully standalone (no Telethon), and P4 needs one field. |
| **Completeness** | PASS | Every SV6 element is covered: the meaning (P2, P3), the shape (P1, P2), the boundaries (P3, P4), the taxonomy (P0), what is not built (rulings A3, A6, A9, A10 inside P0, P1, P2, P5), and the concerns (P6, P7). The ten open points map to P2, P2, P5 keep-alive, P0, P3, P4, P1, P6, P5 and P6/P7. |
| **Reassembly** | PASS | P0–P4 built and P5 green give the transport. P6 makes it usable and honest, and P7 closes the calibration. The determination-mechanism check: the runtime determination "which host for this DC?" has its own piece (P2's map and the `__init__` lookup), and "which transport for this client?" has P3's door branch. |
| **Tractability** | PASS | Each piece is one focused pass. P1 (about 120–150 lines) and P5 (the harness) are the largest. |
| **Interface clarity** | PASS | Every flow is named, with its assumptions. Two hidden couplings were found and captured: the receive-loop exception rule (P0/P1), and the reader/writer assignment before `_init_conn` (P1/P2). A third was added: the SSL-context seam P5 needs in P1. |
| **Balance** | PARTIAL | P1 and P5 carry most of the work; P4 is small. The imbalance is accepted, not hidden. Splitting P1 further (TLS+upgrade vs framing) passes the stopping criteria: it is tractable as one pass, and the probe already implements it as one unit. P4 stays separate because its invariant (TCP hash) and module (`login.py`) are distinct. |
| **Confidence** | PASS | Top-down and bottom-up agree. The one split atom (the cert-error conversion) resolves by ordering P0 first. |

**Failure modes checked:**
- **premature decomposition:** no — sensemaking's SV6 states the whole in one paragraph;
- **wrong boundaries:** no — B1 matches the probe's tested split;
- **hidden coupling:** three found and captured;
- **missing pieces:** the keep-alive and the trust store were checked — the keep-alive is in P5 and P7, the trust store in P1's seam and P6;
- **over-decomposition:** eight pieces for this whole is proportionate;
- **ignoring dependencies:** ordered above;
- **imbalance:** noted, and accepted on the stopping criteria.

**One open assumption carried forward** (not a boundary issue). The plain Telethon obfuscation header (no DC bytes) is what the probe recorded working on 2026-11-26. P7 is where a different result would show. If it does, the remedy is local to P2: override `obfuscated_io` with the probe's header variant.
