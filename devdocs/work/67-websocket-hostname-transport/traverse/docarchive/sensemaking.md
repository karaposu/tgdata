---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

/Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/_branch.md — inputs also in that folder: articulate_simple.md, surfacing.md (with ../triage.md as its prior artifact), articulate_warm.md (the settled re-anchored framing; use its committed MQ2, its refreshed considered articulations, and its content-conflict C1). SAVE the output as /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/sensemaking.md

---

# Sensemaking — the elegant WebSocket transport for tgdata (issue #67)

## SV1 — Baseline understanding

Add a "WebSocket" connection type that tgdata can choose per account, so connections to Telegram go to its web endpoint by hostname through the configured proxy instead of to an IP address. It presumably needs:
- a new class;
- a config switch;
- some way to send other data centres to the right hostname;
- care that nothing else changes.

The open questions look numerous (ten), and a few look like they could need new machinery: keep-alive pings, an error taxonomy, a version guard.

---

## Phase 1 — Cognitive anchor extraction

### Constraints

- **K-C1 The default is byte-identical.** No `transport` key means the same `TelegramClient` constructor arguments, the same log lines, and the same login-checkpoint binding hash as today.
- **K-C2 Never an IP when the WebSocket transport is chosen.** Every socket for such a client is opened by **name**:
  - through the proxy with remote DNS — `parse_proxy_url` always sets `rdns: True`, so HTTP CONNECT, SOCKS5 and SOCKS4a all send the name;
  - or, with no proxy, through the OS resolver to the name.

  It never falls back to TCP or to an IP.
- **K-C3 Telethon 1.45.0 is the baseline.** `AccountPool` and `Worker` pin it exactly. Plain `TgData` accepts `>=1.45,<2.0` — warm conflict C1.
- **K-C4 The listed existing elements stay unharmed:**
  - the one door, `_new_client`;
  - the request-seam mixins;
  - the fail-closed proxy;
  - the strict options;
  - `StoredSession`;
  - `LoginFlow`'s binding;
  - `AccountPool._failure`;
  - the pins.
- **K-C5 Excluded:** MTProxy, secrets, older Telethon, implementing in this step.
- **K-C6 Hostnames, from the probe (2026-11-26):** `pluto`, `venus`, `aurora`, `vesta`, `flora` (`.web.telegram.org`) for DC 1–5 work. `kws2-1` and `kws4-1` fail.
- **K-C7 Idle tunnels:** alive at 150 s, cut by 300 s.

### Key insights

- **K-I1 Telethon already provides the general seam.** `TelegramClient(connection=<class>)` is honoured on every one of its four connection-construction sites, each of which passes `dc_id`. So the whole transport is one `Connection` subclass, and no Telethon DC-switching code is touched.
- **K-I2 Fail-fast vs retry is already decided by exception type, on both sides.**
  - Telethon's `_try_connect` retries only `IOError` / `TimeoutError`; anything else escapes at once.
  - tgdata's `ProxyConfigError(ValueError)` is raised at config time.
  - `AccountPool._failure` maps a `ValueError` to `unknown`, which stops, and an unsuppressed `ConnectionError` to `transport`, which retries.

  An error taxonomy needs no new machinery: only choosing the right base class.
- **K-I3 The keep-alive runs on every connected client**, strict ones included, every 60 s. Strict clients never reconnect, and are short-lived. All of these sit inside the ≥ 150 s idle margin, so **the transport needs no pings**.
  - Exported senders — connections to other DCs — get no pings. Telethon does close them once they have been idle for more than 60 s, checked on each 60 s keep-alive tick, so after at most about 120 s.
  - Re-checked against Telethon 1.45.0: `_DISCONNECT_EXPORTED_AFTER = 60`, and `_clean_exported_senders()` is called from `_keepalive_loop`.
- **K-I4 Telethon's own proxy code can be reused unchanged.** `Connection._proxy_connect` connects to `dest_host = self._ip`. If the subclass's `_ip` is the hostname, Telethon's python-socks or PySocks code tunnels by name, with the same masking, errors and library selection as TCP today.
- **K-I5 Telethon's TLS helper is unusable**: `ssl.wrap_socket` was removed in Python 3.12, and it sets no SNI. The subclass does its own TLS with `asyncio.open_connection(sock=…, ssl=ctx, server_hostname=host)`.
- **K-I6 Setting the hostname at construction makes the transport fail closed by construction.** If the subclass's `__init__` replaces the IP Telethon passes in with the DC's hostname, then even a future Telethon that skipped the `_connect` override could only ever dial a **name**. That name would fail its handshake; it could not leak an IP.
- **K-I7 The connection class cannot carry per-account parameters.** Telethon asserts `isinstance(connection, type)`, so a `functools.partial` or an instance is rejected. Any per-account setting — a hostname override, a TLS context — would need a dynamically built subclass per config. A static class needs none.
- **K-I8 Telethon replaces a transport `IOError` with a fresh, unchained `ConnectionError`.** The original reason survives only in Telethon's WARNING log. That is the same as TCP failures today, so it is not a regression. Fail-fast errors (`ValueError` family) escape intact.

### Structural points

- **K-S1 config:** `_load_config` reads `transport` into `ConnectionConfig.transport`: `tcp` by default, or `websocket`.
- **K-S2 the door:** `_new_client` adds `connection=<WebSocket class>` **only** when the transport is `websocket`. Otherwise it adds nothing.
- **K-S3 the class:** a subclass of `ConnectionTcpObfuscated`.
  - `__init__` maps `dc_id` to the hostname, and sets `_ip` and the port 443.
  - `_connect` opens a socket by name — through Telethon's `_proxy_connect`, or directly — then TLS with SNI and verification, then the WebSocket handshake. It installs reader and writer adapters, and then does exactly what the base does: `_codec`, `_init_conn`, `drain`.
- **K-S4 the adapters:** the probe's `WsReader` / `WsWriter` — the byte stream over binary frames, client masking, ping/pong and close.
- **K-S5 the consumers:** `TgData`, `AccountPool`, `Worker` and `LoginFlow` all build through `_new_client` and inherit the transport with zero code changes. That is exactly how the proxy was added.
- **K-S6 the login binding:** a `transport` entry is added to `LoginFlow`'s settings **only when it is not `tcp`**.

### Foundational principles

- **K-P1 One door.** Every client is built by `_new_client`.
- **K-P2 Fail closed, as early as possible.** Fail at config time where possible, at connect time otherwise, and never by fallback.
- **K-P3 Layers stay orthogonal.** The request-seam mixins act above `MTProtoSender`; the transport lives below it.
- **K-P4 Credential-free diagnostics.** Proxy passwords are masked, and no secrets go into messages.
- **K-P5 The default is byte-identical.**
- **K-P6 Reuse the mechanisms that already exist:** Telethon's `connection=` seam, its retry-by-type, its proxy code; tgdata's `ValueError` / `ConnectionError` split.

### Meaning-nodes

- **K-M1 "By name"** — the transport's essence: never resolve locally when a proxy is configured, never dial an IP.
- **K-M2 "The door"** — Telegram's WebSocket endpoint, `wss://<planet>.web.telegram.org/apiws`.
- **K-M3 Transport ⟂ proxy** — two independent axes in the same config section.
- **K-M4 Elegance** — the fewest seams touched, the most existing mechanism reused, and nothing new that Telethon already provides.

**Meta-inspection after SV2.**
- **H4 (concept names):** "transport" is load-bearing and tested at Phase 2's Frame-exit perspective below.
- **H5 (motivating examples):** the planet-name map rests on one day's probe, from one server and one proxy. It is tested in Phase 3 (A14).

### SV2 — Anchor-informed understanding

The design is smaller than SV1 assumed. Telethon already provides:
- the general seam (`connection=`);
- the DC routing (every construction site passes `dc_id`);
- the proxy tunnel by name (`_proxy_connect` with `rdns`);
- the retry-vs-fail-fast split (by exception type).

tgdata already provides:
- the one door;
- the config-time `ValueError` pattern;
- the pool's classification by type.

What remains genuinely new:
- one connection class: a TLS and WebSocket wrapper around Telethon's own obfuscation;
- one config key;
- one conditional binding entry;
- docs.

Three of the ten open points — keep-alive, retries, shape — are already settled by the code, not by design.

---

## Phase 2 — Perspective checking

**Technical / Logical.**
- Telethon's `ConnectionTcpObfuscated` needs only `_reader.readexactly` and `_writer.write`/`drain`/`close`/`wait_closed`. The probe showed the adapters satisfying this end to end, offline and live.
- New anchor **T1**: the overridden `_connect` must honour `timeout` across tunnel, TLS and handshake together, as Telethon's base `_connect` uses it for the open.
- New anchor **T2**: Telethon's `_proxy_connect` also handles `local_addr`. Reusing it keeps that behaviour for free.

**Human / User — the operator.**
- An operator adds one line, `transport = websocket`, beside `proxy`.
- They need to know four things:
  - it requires a proxy that can tunnel to `*.web.telegram.org:443`, by HTTP CONNECT or SOCKS with remote DNS;
  - nothing ever goes by IP;
  - a failure looks like what: a config error at start-up, or a `ConnectionError` with Telethon's warning in the logs;
  - how to see that it is active.
- New anchor **U1**: the one-time route log line and `health_check()` should name the transport, so the operator can confirm "via proxy X, over WebSocket by name".

**Strategic / Long-term.**
- The door is unpublished, so its hostnames and path could change.
- Telethon 2.x is out of scope (`<2.0`).
- Future transports (HTTP, or Telethon's others) would reuse the same seam: a value mapped to a class.
- New anchor **St1**: a canary test in the style of `test_14` — "run after any Telethon upgrade" — protects the reliance on Telethon internals (`_connect`, `_proxy_connect`, `_init_conn`, `packet_codec`, `_reader` / `_writer`).

**Risk / Failure** — the uncomfortable perspective, deliberately checked:
- **R1 A silent IP leak.** Closed by K-I6, construction-time naming, and by a test that records every destination on every construction path, including reconnect and the exported sender.
- **R2 A DNS leak.** Telegram names are resolved locally only when no proxy is configured. That is a direct connection anyway, by the operator's choice, so it is not a leak of the proxy's purpose.
- **R3 A refused upgrade is retried.** An HTTP 403 or 404 at `/apiws` could be persistent (the door moved) or transient. Retrying is bounded on ordinary clients (`connection_retries=5`), immediate failure on strict ones, and timed by the pool's `transient_retry_seconds`. That is acceptable, and visible.
- **R4 Certificate failure:** a missing CA bundle on a server, or a man-in-the-middle proxy. It must fail, never skip verification. **New anchor R4a**: a certificate failure is persistent and configuration-like, so make it fail-fast, not retried.
- **R5 Telethon drift under plain `TgData`** (C1). Mitigated by R1's construction-time naming — drift can break the handshake, never leak — plus St1's canary.
- **R6 An account fingerprint.** A desktop-app account (its api id and pinned identity) arriving through the browser's door. tgdata cannot fix this; document it, and watch it in the live test.
- **R7 The relays' rate limits** — unknown. Document them.
- **R8 Diagnosability in `Worker`.** It disables logging, so Telethon's warning carrying the transport's reason is not visible there. The `Worker` reports error types only. That is the same as TCP today, not a regression.

**Resource / Feasibility.**
- Size: the class plus adapters is about 150–250 lines, adapted from the probe; the config key and door branch about 15; the binding about 3; docs and tests on top.
- No new dependency: neither `websockets` nor `aiohttp` is needed for a client-only, binary-only, no-extension WebSocket. The probe's framing is about 100 lines and tested.
- New anchor **F1**: a library's message-oriented API would need a pump task to present a byte stream, which adds machinery the hand-written adapter avoids.

**Ethical / Systemic.**
- tgdata stays a neutral transport. Choosing to present a dedicated address is the operator's decision, and the account-safety risks (R6, R7) are the operator's to accept.
- tgdata's systemic duty is the guarantee itself — "never an IP" — and honest docs.

**Definitional / Internal consistency.**
- "Fail closed" today means "never connect without the configured proxy". The WebSocket transport adds "never dial an IP when by-name was chosen". Direct-by-name with no proxy is consistent with both: it is the operator's explicit choice, and `require_proxy` still governs it.
- "Default byte-identical" must explicitly cover the binding hash and the log text (K-C1), or a TCP user's saved login checkpoints would silently stop restoring after an upgrade.

**Definitional / Frame-exit completeness.** The gating fires. "transport" will be used across several values in this inquiry's committed structures: the config values `tcp` / `websocket`; the pool's `transport` outcome; and "transport failures" in docs.
- **Existence enumeration.** "transport" already refers to several distinct things project-wide:
  - (a) the network layer: Telethon's `Connection` classes, and `LoginError('transport_error')`;
  - (b) `AccountPool`'s `transport` *failure outcome* — connection errors, timeouts, server errors;
  - (c) "transport envelopes" — TL request wrappers such as `InvokeWithLayer` and `InitConnection`, in `owned_health._ENVELOPES`, `budget_client._WRAPPERS`, `README.md:1278` and `docs/account_operations.md:107`;
  - (d) "transport failures" in `docs/account_operations.md:38`, `docs/group_activity.md:209` and `docs/message_batch_v1.md:219`.
- **Role assessment.** The config key belongs to meaning (a). (b) and (d) are consequences of (a), consistent. (c) is a different layer, request wrapping. If the docs say "transport" bare, a reader could conflate the config key with (c).
- **Verdict rigour.**
  - *Counter:* name the key `connection = websocket` to match Telethon's argument.
  - *Fails structurally:* "connection" already means something else in tgdata's config (`connection_pool_size`), and `TgData`'s API exposes `connection_engine`. Telegram's own documentation calls TCP, WebSocket and HTTP "MTProto **transports**".
  - So `transport` is the domain term. The README must say "network transport", and must not touch the envelope wording.
- **Residual.** None beyond this.

**Phase / Calibration-State.**
- The DC→hostname map is calibrated on a single measurement: 2026-11-26, one server, one proxy, one region.
- The `-1` failures (`kws2-1`, `kws4-1`) show the relays are not uniform.
- Is the planet-name rule correct beyond that calibration? Unknown. The early-stage default is the verified map, plus a live check at the end of the work (A14).

**Meta-inspection after SV3.**
- **H1 (candidate set):** the shapes considered — connection subclass, out-of-process relay, a monkeypatch of `Connection._connect`, a local in-process SOCKS shim. The shim and the subclass are not the same thing: the shim keeps TCP framing and would need its own WebSocket conversion. Collapsed in A1.
- **H2 (frame scope):** done above.
- **H3 (question framing):** "the most elegant design" presupposes that one shape is clearly best. Tested in A1 and A13.
- **H7 (calibration):** done above.

### SV3 — Multi-perspective understanding

The model holds, and gains four things:
- **Construction-time naming** (K-I6) turns "never an IP" from a property of one method into a property of the class's identity. That is the strongest guard against Telethon drift (C1).
- **Fail-fast belongs to certificate failures as well as configuration errors** (R4a).
- **Observability needs the transport named** in the route log line and in `health_check()` (U1).
- **"transport" is overloaded project-wide.** The docs must disambiguate it from request envelopes.

The uncomfortable perspective (Risk) produced no structural break. Its residuals are outside-world risks tgdata documents and cannot remove: R6, R7, and the door's stability.

---

## Phase 3 — Ambiguity collapse

### A1 — The transport's shape

**Ambiguity:** a `Connection` subclass inside the client, an out-of-process relay, a monkeypatch of Telethon's `Connection._connect`, or a local in-process SOCKS shim that rewrites IPs to names.

**Strongest counter-interpretation:** an out-of-process relay (tg-ws-proxy-style) keeps tgdata untouched entirely: zero code, no Telethon internals.

**Why it fails (structural):**
- Those relays speak the MTProto **proxy** protocol, which `parse_proxy_url` refuses and #67 excludes.
- Telethon's MTProxy connection is special-cased in `TelegramBaseClient.__init__` (`TcpMTProxy` → `init_proxy`), which changes the init request.
- The relay would also need its own upstream tunnel through the configured proxy, which tgdata does not own. The fail-closed guarantee would then live outside tgdata.
- The monkeypatch fails K-C1/K-P5: it would change every client, the default included.
- The SOCKS shim would still need full WebSocket framing on the IP→name side, plus a mapping of DC IPs back to DC numbers that the `dc_id` already passed to the class makes unnecessary.

**Confidence:** HIGH.

**Resolution:** a subclass of Telethon's `ConnectionTcpObfuscated` that overrides `__init__` (naming) and `_connect` (the socket, TLS and WebSocket), passed through `connection=`.

**Now fixed:** the transport is in-process, per client, selected at the one door.

**No longer allowed:** relays, monkeypatching, IP→name rewriting.

**Depends on this:** A2, A3, A5, A10, A13.

**Model change:** the shape is decided by Telethon's own seam rather than designed.

### A2 — The config surface

**Ambiguity:** an ini key per account, a `TgData(...)` argument, or both.

**Strongest counter:** a `TgData(transport=...)` argument is more discoverable in code.

**Why it fails:**
- `AccountPool` and `Worker` build their engines from `config_path` only.
- `docs/worker.md:22`: "No job may supply credentials, a proxy …".
- `LoginFlow` binds to config values.

A constructor argument would have to be threaded through four constructors and would bypass the binding. The proxy precedent is the ini file.

**Confidence:** HIGH.

**Resolution:** `transport = tcp | websocket` in the account's `[Telegram]` section. The default is `tcp`, and an absent key means `tcp`. An unknown value raises a config-time error (`ProxyConfigError` family, or a sibling `ValueError`) before any socket opens.

**Fixed:** it is per account and per config file, read once by `_load_config`.

**Not allowed:** a per-call transport; a transport supplied by a job.

**Depends on this:** A8, the docs.

**Model change:** the transport becomes a proxy-sibling setting.

### A3 — The DC→hostname map: its home, and whether it is configurable

**Ambiguity:** a fixed map in code, or an ini override per DC.

**Strongest counter:** the door is unpublished, and two naming families exist (`kwsN`, planets). A per-DC override would let operators react to a renamed host without a release.

**Why it fails (structural):**
- Telethon requires a **class** (K-I7). A per-account override means building a class per config — another `lru_cache` factory like `_client_class` — for a hypothetical change.
- A renamed host is unlikely to change alone; the path or protocol may move with it, which needs code anyway.
- An override pointing at an arbitrary host weakens the "Telegram's door" meaning. It would still be TLS-verified for that name, but would no longer be known to be Telegram's.
- A tgdata release is cheap: the maintainer owns the repo.

**Confidence:** MEDIUM. The counter has merit if the door changes often; there is no evidence either way.

**Resolution:**
- One module-level constant, `{1: 'pluto', 2: 'venus', 3: 'aurora', 4: 'vesta', 5: 'flora'}`, with `.web.telegram.org`, port 443 and `/apiws`. No override.
- Any other DC number raises a fail-fast error naming the DC.
- The `-1` names are never used.

**Fixed:** the map's single home, and its exhaustiveness.

**Not allowed:** dialling any non-mapped DC; a TCP fallback for it.

**Depends on this:** the error taxonomy (A5) and the tests.

**Model change:** "every DC by name" becomes "every *mapped* DC by name, and an error otherwise". Telethon never uses CDN DCs (`GetFileRequest` without `cdn_supported`).

### A4 — Keep-alive

**Ambiguity:** whether the transport must send its own pings.

**Strongest counter:** Telethon's keep-alive is a 60 s loop whose missed-pong detection takes up to about 120 s. If the relay's real cut is near 150 s, the margin is thin.

**Why it fails:** the loop *sends a ping every 60 s* regardless of detection, and any ping is traffic that resets an idle timer. The idle gap therefore never exceeds about 60 s, and 150 s survived in the probe. Detection latency matters only after a cut, and a cut is handled by reconnecting (ordinary clients) or failing (strict ones).

**Confidence:** HIGH — from the code (`_keepalive_loop`, unconditional start) and the probe (75 s and 150 s answered).

**Resolution:** no transport-level pings. The adapter answers *server* pings with pongs, as RFC 6455 requires.

**Fixed:** keep-alive belongs to Telethon.

**Not allowed:** a second keep-alive mechanism.

**Model change:** open point 3 is closed by evidence.

### A5 — The error taxonomy

**Ambiguity:** which WebSocket failures are configuration (fail fast) and which transient (retried).

**Strongest counter:** make every transport failure a `ConnectionError` — one class, simplest — and let retries and the pool sort it out.

**Why it fails:**
- Telethon retries every `IOError` `connection_retries` times with delays, and `AccountPool` would cool down and retry it as `transport`.
- For an unmapped DC, or a certificate that cannot verify, every retry is guaranteed to fail the same way. Retrying hides a configuration fault behind "Connection to Telegram failed 5 time(s)" (K-I8), with no cause chained.
- A `ValueError`-family error escapes Telethon immediately and intact (K-I2). The pool classifies it as `unknown`, which stops it, exactly as `ProxyConfigError` behaves today.

**Confidence:** HIGH.

**Resolution:**
- **Fail fast (`ValueError` family, tgdata's own class):**
  - an unknown `transport` value, at config time;
  - an unmapped DC, at construction or connect;
  - a certificate verification failure, at connect.
- **Transient (`ConnectionError` family):**
  - proxy refusal or unreachability — Telethon's existing errors, unchanged;
  - a TCP or TLS reset;
  - a WebSocket handshake that is not `101`, or a bad accept key;
  - a server close or end of stream mid-session, which becomes `IncompleteReadError` / `ConnectionError` in Telethon's receive loop.

**Fixed:** the taxonomy is the choice of base class, and nothing else.

**Not allowed:** new retry logic; new pool outcomes.

**Depends on this:** the tests (one per class), the docs.

**Model change:** open point 4 reduces to "pick the base class correctly".

### A6 — Error transparency

**Ambiguity:** whether the transport must preserve its reason beyond Telethon's WARNING log, given Telethon replaces transient errors (K-I8).

**Strongest counter:** attach the last transport error to the client, and surface it in `health_check()` or in the raised error.

**Why it fails:**
- Telethon constructs the final `ConnectionError` itself. tgdata cannot chain it without patching Telethon or wrapping every connect site.
- TCP failures have exactly the same transparency today.
- The fail-fast errors — the ones that need operator action — escape intact by A5.
- Telethon already logs each attempt's cause, through tgdata's credential-free messages.

**Confidence:** MEDIUM. A `health_check` field remains possible later.

**Resolution:** no new mechanism. The transport's error messages are specific and credential-free, for example "WebSocket handshake to vesta.web.telegram.org refused: HTTP 403". The docs say transient causes appear in Telethon's connect warnings.

**Fixed:** messages are informative and contain no secrets.

**Not allowed:** patching Telethon's sender.

**Model change:** transparency equals TCP's, with clearer messages.

### A7 — `require_proxy` × WebSocket

**Ambiguity:** whether a WebSocket transport without a proxy is allowed.

**Strongest counter:** the WebSocket transport exists for hostname-only proxies, so require a proxy with it.

**Why it fails:**
- Transport and proxy are independent axes (K-M3). Coupling them adds a special case to `_load_config`.
- Direct-by-name has real uses: networks that block Telegram's IP ranges but allow `web.telegram.org`, and local testing.
- `require_proxy = true` already expresses "never without a proxy" for operators who need it.

**Confidence:** HIGH.

**Resolution:** allowed. With no proxy, the name is resolved by the OS. `require_proxy` keeps its meaning, unchanged.

**Fixed:** the axes are independent.

**Not allowed:** transport-specific proxy rules.

**Model change:** open point 5 is closed.

### A8 — `LoginFlow`'s binding

**Ambiguity:** whether `transport` joins the checkpoint binding.

**Strongest counter:** leave it out. A login conversation is tied to an auth key and a DC, not a transport, and adding it touches a security-sensitive hash.

**Why it fails:**
- The binding already includes `proxy` and `require_proxy`: settings that change *where the conversation's traffic exits from*. The transport changes the exit address the same way: via the proxy's gateway by IP under TCP, via the assigned address by name under WebSocket. A code requested from one address and submitted from another is the fingerprint the binding exists to prevent.

**Confidence:** HIGH.

**Resolution:** add `transport` to the binding settings **only when it is not `tcp`**. TCP checkpoints keep their exact hash (K-C1), and `docs/stepwise_login.md:90` lists the field.

**Fixed:** the binding semantics: "the settings that decide the conversation's network identity".

**Depends on this:** the login tests and docs.

**Model change:** open point 6 is closed.

### A9 — The WebSocket client

**Ambiguity:** hand-written, or an optional dependency (`websockets` / `aiohttp`).

**Strongest counter:** a library is battle-tested on RFC 6455 edge cases — fragmentation, control frames, close handshakes.

**Why it fails:**
- The need is a strict subset: a client; binary frames; no extensions, compression or subprotocol negotiation beyond `binary`; a byte stream.
- Libraries are message-oriented. Presenting `readexactly` requires a pump task and a buffer, which is more machinery than the framing itself (F1).
- A library also owns its socket and TLS, which conflicts with reusing Telethon's `_proxy_connect` (K-I4).
- The probe's framing handles fragmentation (continuation frames), ping, pong and close, and is tested offline at every size boundary, and live.

**Confidence:** HIGH.

**Resolution:** a hand-written, minimal client adapted from the probe. No new dependency. The `proxy` extra stays the only optional dependency.

**Fixed:** zero new dependencies.

**Not allowed:** WebSocket extensions; text frames (they are a protocol error, raised as a `ConnectionError`).

**Model change:** open point 7 is closed.

### A10 — Reliance on Telethon internals, under plain `TgData` (warm C1)

**Ambiguity:**
- a runtime exact-version refusal, as in `AccountPool` / `Worker`;
- a structural check;
- a canary test only.

**Strongest counter:** refuse `transport = websocket` at config time on any Telethon other than 1.45.0. That is fail-closed and consistent with the pool and worker.

**Why it fails, mostly:**
- With construction-time naming (K-I6), Telethon drift cannot produce the failure that matters, an IP connection. At worst it breaks the handshake, loudly.
- A hard version refusal would block plain `TgData` users on a harmless Telethon patch release until tgdata re-verifies.
- The pool and worker already pin for their own reasons, and keep doing so.

**Confidence:** MEDIUM. A hard pin is defensible, if the maintainer prefers uniformity.

**Resolution:**
- no runtime version refusal;
- construction-time naming;
- a canary test in the `test_14` style, run after any Telethon upgrade, that drives Telethon's real client through every construction path with the transport;
- the docs name the verified Telethon version.

**Fixed:** the safety argument rests on naming at construction, not on the version.

**Model change:** C1 is resolved by design, not by policy.

### A11 — Docs that become false

**Ambiguity:** which statements change, and how.

**Strongest counter:** none of them are strictly false until the transport ships, so update them later.

**Why it fails:** they are false the moment the key exists. "remote DNS is moot" becomes wrong for `websocket`, and the binding doc would omit a field.

**Confidence:** HIGH.

**Resolution:** change these in the same change:
- the `connection_engine.py:154` comment;
- the `parse_proxy_url` and `_new_client` docstrings;
- the README proxy section, plus a new "Connecting through Telegram's WebSocket door" subsection;
- `docs/stepwise_login.md:90`.

Envelope wording (A-frame (c)) stays untouched.

**Fixed:** the docs list.

### A12 — Build or not

**Ambiguity:** whether this inquiry decides to build.

**Strongest counter:** the residual outside-world risks (R6, R7, an unpublished door) may argue for the alternative provider.

**Why it fails (as a question for this inquiry):** the maintainer opened #67 to build it, after the probe and the cost comparison. The code-side risk this inquiry can assess is small and contained. The outside-world risks are accept-or-avoid decisions this inquiry cannot change.

**Confidence:** HIGH.

**Resolution:** the inquiry delivers the design. The residual risks are recorded for `desc.md`'s scope and risks, and for the live test.

### A13 — Load-bearing concept test: "elegance" = fewest seams touched + reuse

**Counter:** elegance could mean *generality*: a transport registry or plugin system ready for HTTP and others.

**Why it fails:** Telethon's `connection=` *is* the registry. A tgdata registry would duplicate it. Adding a value is one more `name → class` entry in the same place the WebSocket entry lives.

**Confidence:** HIGH.

**Resolution:**
- elegance here means the fewest existing seams touched — two: `_load_config` and `_new_client`, plus a conditional binding entry;
- the most Telethon mechanism reused: `connection=`, `ConnectionTcpObfuscated`, `_proxy_connect`, retry-by-type, the keep-alive;
- no new concept that Telethon already has.

### A14 — Specific vs pattern: one probe day

**Ambiguity:** does "planet names work for all DCs" hold generally, or only for 2026-11-26, from one server through one proxy?

**Counter:** relays are anycast or regional; other regions or days may differ, as the `-1` failures show the fleet is not uniform.

**Why that doesn't overturn A3:** it is not disproven. Rather, nothing better exists. Both naming families were measured, and planet names were the superset that worked.

**Confidence:** LOW for generality, HIGH for "the best-evidenced choice now".

**Resolution:** the planet-name map stays. Its calibration is stated in the docs, and the live test on the real account is the next measurement. A failure there is a desc-level blocker, not a design change.

### SV4 — Clarified understanding

What is now clear:
- the shape: a `ConnectionTcpObfuscated` subclass, named at construction;
- the config surface: one `transport` key;
- the fixed planet map: an error for unmapped DCs;
- keep-alive: Telethon's;
- the error taxonomy: by base class — `ValueError` for configuration and certificates, `ConnectionError` for transient faults;
- transparency: as for TCP;
- the axes: independent of `require_proxy`;
- the binding: `transport` only when non-default;
- the WebSocket client: hand-written;
- the version guard: none at runtime; safety from construction-time naming plus a canary;
- the docs list.

What is no longer viable:
- a relay;
- monkeypatching;
- a SOCKS shim;
- a `TgData` argument;
- a host override;
- transport pings;
- one error class for everything;
- a WebSocket library;
- a runtime version pin for this transport;
- `-1` names;
- any fallback.

Open with MEDIUM or LOW confidence:
- A3's override question (MEDIUM);
- A6's `health_check` field (MEDIUM);
- A10's hard-pin preference (MEDIUM);
- A14's calibration (LOW).

---

## Phase 4 — Degrees-of-freedom reduction

**Fixed variables:**
1. **The seam:** `TelegramClient(connection=WebSocketClass)` from `_new_client`, only when `transport = websocket`.
2. **The class:** subclasses `ConnectionTcpObfuscated` (abridged codec). It overrides `__init__` (the DC→host map, `_ip = host`, `_port = 443`) and `_connect`:
   - the socket by name — Telethon's `_proxy_connect` when proxied, `asyncio` by name otherwise;
   - TLS with `ssl.create_default_context()` and `server_hostname`;
   - `GET /apiws` with `Sec-WebSocket-Protocol: binary`, `Origin: https://web.telegram.org`, and the accept check;
   - the adapters;
   - then `_codec`, `_init_conn` and `drain`, as in the base.
3. **The config:** `transport` in `[Telegram]` → `ConnectionConfig.transport`, with values `tcp` (default) and `websocket`.
4. **The errors:** one new local exception family. For example, `TransportConfigError(ProxyConfigError)` or a `ValueError` sibling for the fail-fast cases; transient cases raise `ConnectionError` subclasses.
5. **The binding:** `settings['transport']` is present only when not `tcp`.
6. **Observability:** the route log line names "over WebSocket (by name)" for `websocket` only; `health_check()` gains a `transport` field.

**Eliminated:**
- relays, monkeypatching and IP→name shims;
- a constructor argument;
- host overrides;
- the `-1` names;
- transport pings;
- a WebSocket library;
- a runtime version pin for this transport;
- any IP or TCP fallback.

**Remaining viable choices — small, for the description or plan:**
- the exact error class names, and whether the fail-fast class subclasses `ProxyConfigError` (both are config-family) or is a sibling `ValueError`;
- whether `Origin` is sent: it was sent in every probe run; keep it;
- whether `health_check()` reports `transport` — recommended, being cheap;
- the module name, e.g. `tgdata/websocket_transport.py`.

### SV5 — Constrained understanding

The solution space has collapsed to one design. Its open parameters are naming-level only. The problem's structure is:

**Config** (`transport`) → **the door** (`_new_client` adds `connection=` conditionally) → **the class** (naming at construction; a by-name socket through Telethon's own proxy code; TLS; WebSocket; Telethon's own obfuscation) → **Telethon's unchanged machinery**: the four construction sites, reconnect, keep-alive, retry-by-type.

**Around it:** the binding entry, the docs, the observability line, and the tests:
- **offline:**
  - a local TLS WebSocket server;
  - destinations recorded on every construction path — main, exported sender, reconnect;
  - the taxonomy per base class;
  - the default byte-identical, including the binding hash;
- **a canary** after Telethon upgrades;
- **a live run** on the real account, on the maintainer's go.

---

## Phase 5 — Conceptual stabilization

**Accommodation check (H6):** every perspective added anchors that refined the model; none forced a revision of its structure. The model was refined, not patched. No accommodation trigger.

### SV6 — Stabilized model

**The WebSocket transport is a Telethon connection class, chosen per account by one config key, and passed through tgdata's one door. Everything else is reuse.**

1. **The meaning.**
   - `transport = websocket` means every connection the account's clients open goes to Telegram's WebSocket door by **name**. That holds for logins, reads, verified operations, the pool, the worker, reconnects and downloads from other DCs.
   - It goes through the configured proxy with remote DNS, or directly by name when no proxy is configured.
   - It never goes to an IP, and never falls back.
   - `tcp`, the default, is exactly today's behaviour: the same constructor arguments, log lines and binding hash.
2. **The shape.** A `ConnectionTcpObfuscated` subclass:
   - **at construction** it maps the DC number to `<planet>.web.telegram.org:443`, so even Telethon drift can only fail a handshake, never dial an IP;
   - **on connect** it opens a socket by name through Telethon's own `_proxy_connect`, does TLS with SNI and verification, and performs the `/apiws` binary WebSocket handshake;
   - **once connected** it hands Telethon's own obfuscation a byte-stream adapter over binary frames.

   Telethon's four construction sites, reconnect and keep-alive are untouched. They already route by `dc_id`, reuse the connection object, and ping every 60 s inside the 150 s idle margin.
3. **The boundaries with existing design:**
   - the request-seam mixins sit above, unchanged;
   - the strict options apply unchanged: one attempt, no reconnect, and the keep-alive still runs;
   - `StoredSession` and the session files are unchanged; the stored IP is never dialled;
   - `AccountPool._failure` is unchanged, because the taxonomy is expressed through base classes it already reads;
   - the pins are unchanged.

   `LoginFlow`'s binding gains `transport` only when it is not `tcp`.
4. **The error taxonomy is a base-class choice:**
   - `ValueError` family, failing fast at config time or connect time: an unknown transport, an unmapped DC, a certificate failure;
   - `ConnectionError` family, retried by Telethon on ordinary clients and by the pool's `transport` cooldown: proxy refusal, resets, a non-101 handshake, a server close;
   - all messages are credential-free.
5. **What is deliberately not built:** relays, a host override, transport pings, a WebSocket dependency, a runtime version pin, the `-1` names.
6. **Concerns registered — the ones not yet realised in the brief:**
   - a TCP user's saved login checkpoints would break if the binding changed unconditionally (closed by the conditional entry);
   - "transport" is overloaded with request envelopes (the docs disambiguate);
   - Telethon replaces transient causes (accepted: the same as TCP, the cause logged, fail-fast errors intact);
   - certificate failures should not be retried (they fail fast);
   - plain `TgData` is unpinned (closed by construction-time naming plus a canary);
   - the trust store's availability on servers (fails loudly, documented);
   - one day's calibration of the map (the live test).
   - **Outside-world, documented, not fixable in code:** the door is unpublished; a desktop-app account arrives through the web door; the relays' rate limits.

**How SV6 differs from SV1.** SV1 expected a new transport *subsystem* with several open mechanisms: pings, a taxonomy, a version guard, DC routing. SV6 finds almost all of those already exist in Telethon or tgdata. The design is a class plus a key. Its distinctive moves:
- **naming at construction**, which makes "never an IP" structural;
- **taxonomy by base class**;
- **a binding entry that exists only when it is not the default**.

The ten open points are closed, except four parameters routed with MEDIUM or LOW confidence:
- A3, a host override — no;
- A6, a `health_check` field — recommended;
- A10, a hard pin — no;
- A14, the calibration — a live test.

---

## Telemetry

- **Perspective saturation:** Technical, Human, Strategic, Risk, Resource, Ethical, Definitional (both) and Calibration were checked. Risk, Definitional/Frame-exit and Calibration produced new anchor *types* (R4a, the overloaded term, the calibration limit). The last two confirmed existing types, so saturation is approaching.
- **Ambiguity resolution ratio:** 14 collapsed — 10 HIGH, 3 MEDIUM, 1 LOW/HIGH split. None was dropped silently.
- **SV delta:** large. A subsystem with open mechanisms became one class plus a key, with mechanisms reused.
- **Anchor diversity:** all five types, from nine perspectives.
- **Failure modes checked:**
  - **status-quo bias:** the existing design was protected on evidence (K-I2, K-I7), not by default — it was explicitly asked "would I keep it if it were undocumented?";
  - **premature stabilization:** five perspectives produced new anchors;
  - **anchor dominance:** remove K-I1 and the model still stands on K-I2, K-I4 and K-I6;
  - **perspective blindness:** Risk was checked deliberately;
  - **clean resolution:** every resolution has a structural counter;
  - **self-reference:** not applicable.
