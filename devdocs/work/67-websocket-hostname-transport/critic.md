---
model: claude-opus-5-5[1m]
effort: unknown
---

# Critic — #67 plan (`plan.md`, 14 steps)

## Verdict: REORDER — TEST BEFORE BUILD

```
Falsifier: the real account's authorized requests are refused over Telegram's WebSocket
           door while the same session still works over the ordinary connection.
Affordable now: yes — about 1 h to write a prototype check and about 15 min for the
                operator to run it; needs the maintainer's go and the operator's
                environment (the account's session and the proxy), both available.
```

```
Experiment:          a prototype live check on the real account, run before step 2. A real Telethon
                     1.45.0 TelegramClient on a copy of the account's existing session file (made over
                     TCP), with the account's api_id/api_hash and pinned device identity, through the
                     real proxy, using a connection class that does exactly what step 3 specifies
                     (DC → planet name at construction; Telethon's own _proxy_connect; TLS with SNI and
                     verification; GET /apiws, binary, no Origin; Telethon's obfuscation over the probe's
                     frame adapters). In order:
                       1. connect and GetState;
                       2. get_me;
                       3. one small read;
                       4. one media download that needs a connection to another DC;
                       5. 330 s idle;
                       6. a second read.
                     It records Telethon's "Connecting to …" lines and any Telegram error. Then the same
                     GetState/get_me over the ordinary connection, as a same-hour control.
Cost:                about 1 h to write (the assistant, offline) + about 15 min to run (the operator);
                     the maintainer's go. Nothing new is sent to the account beyond what step 14 would.
                     No login code is requested.
Must precede:        step 2 — the first step whose work is wasted if Telegram will not serve this
                     account over the door.
Disqualifying result: any of the following that the same session does not produce over the
                     ordinary connection in the same hour: GetState, get_me or a read fails with an
                     account or authorization error (AUTH_KEY_UNREGISTERED, SESSION_REVOKED,
                     API_ID_INVALID, a 406/420-class refusal, a freeze or restriction); or the door
                     completes TLS and the handshake but never answers authorized MTProto for the
                     account's DCs. Either converts this verdict to DO NOT IMPLEMENT — MEANING GAP: the
                     feature's premise for this account is false.
Passing result:      steps 1–6 succeed; every "Connecting to" line names a *.web.telegram.org host and
                     none names an IP; the second read works after the idle. The plan then proceeds as
                     critiqued, with the selected mitigations folded in; step 14 becomes confirmation of
                     the built code.
```

## High level summary

**The plan's shape is right.** It is the traverse's design, ordered bottom-up, with the default-path values captured first. The code reading and probes behind this critique confirm its mechanical premises:
- Telethon 1.45.0's own proxy code sends the **hostname** over both HTTP CONNECT (`CONNECT venus.web.telegram.org:443 HTTP/1.1`) and SOCKS5 (domain name `venus.web.telegram.org`, with tgdata's `rdns: True`).
- It returns a non-blocking socket that carries TLS with SNI to a verified certificate.
- A dead proxy raises `ConnectionError`.
- Reconnect reuses the same connection object.
- `retry_range(2)` makes three attempts.
- No test compares `health_check()`'s exact keys.
- `LoginFlow.export_state()` works offline at the first step, so the "restore under a different transport" test is feasible.

**What is wrong is the order.** The premise every step depends on — that Telegram will serve *this account's* authorized session over the web door — is a claim about a vendor service, and it is tested only at step 14, after all the building. The no-account probe proved the transport, not the account. A one-hour prototype check settles it first. Hence **REORDER**.

**Three Medium findings to fold in once the experiment passes:**
1. **Two consumers recognise configuration errors by the existing `ProxyConfigError` class** — the polling loop's "cannot recover" test and the worker's error description. A new sibling class would be retried by polling every interval, and reported by the worker as a plain operation error. Making the new class a **subclass** of `ProxyConfigError` closes both, and any user code, with no consumer edits.
2. **The offline test plan omits the mechanics that make it terminate and stay isolated.** Telethon's key exchange waits on the server with no timeout. The default retry delay is 1 s. `_get_dc` caches its config on the shared client class. Pool sources need scaffolding.
3. **The live checks** (this experiment, and step 14) **could get the account's session revoked** if the same session is used from two places at once. The brief must make "nothing else is using this session" a hard precondition.

**Two Low findings:**
- a stream left open when `_connect` fails half-way;
- the `_ssl_context` seam is process-wide.

**Execution blocker E1** (the maintainer's go for the live run) carries over unchanged as a precondition of step 14. It also governs the experiment above.

---

## Premise Inventory

Ranked by waste if false.

### P1 — Telegram serves this account's existing authorized session over the WebSocket door, including the authorization export to another DC for downloads
- **Kind:** behavioural — a vendor service, Telegram.
- **First dependent step:** step 2. Steps 2–13 build and prove a transport whose only purpose, for the maintainer, is this account.
- **Waste if false:** steps 2–13 — roughly 1–2 days of implementation and tests.
- **Test scheduled at:** step 14, the last step.
- **Cheapest earlier test:** the prototype live check above — about 1 h to write and about 15 min to run, given the maintainer's go. "None" cannot be argued: the account, the proxy and an operator who already ran the no-account probe are all available.
- **Coverage:** **none covering.**
  - The 2026-11-26 probes created throwaway, unauthenticated keys. They prove TLS, the WebSocket handshake and MTProto framing, not account-level acceptance.
  - Telegram's MTProto documentation treating transports as interchangeable is documentary, and does not close a behavioural premise.
- **Consequence:** this premise sets the verdict.

### P2 — Telethon's 60 s keep-alive keeps a held connection alive past the relay's 150–300 s idle cut
- **Kind:** behavioural — the relay.
- **First dependent step:** step 2 (no transport-level pings).
- **Waste if false:** small and local — add a ping in the writer. The plan's shape is unchanged.
- **Test scheduled at:** step 14.
- **Cheapest earlier test:** the same experiment, which holds 330 s at its step 5.
- **Coverage:** partial — a connection answered after 150 s idle in the probe, and the keep-alive loop was read in Telethon's source.

### P3 — The plain obfuscated header, with no DC number in bytes 60–61, works for authorized traffic
- **Kind:** behavioural — the relay.
- **First dependent step:** step 3.
- **Waste if false:** small and local — swap in the probe's header variant.
- **Test scheduled at:** step 14.
- **Cheapest earlier test:** the same experiment.
- **Coverage:** strong — every DC created an auth key over the plain header (2026-11-26), which is the same framing authorized traffic uses.

### P4 — Telethon's proxy code reaches the door by hostname and yields a TLS-capable socket
- **Kind:** documentary / local behaviour.
- **Status:** closed by this critique's probe. A local HTTP CONNECT proxy and a SOCKS5 proxy recorded `('http', 'CONNECT venus.web.telegram.org:443 HTTP/1.1')` and `('socks5', 'venus.web.telegram.org')`. The socket was non-blocking, and a TLS round trip with SNI `venus.web.telegram.org` against a test-CA certificate returned `b'hello12345'`. A closed proxy port raised `ConnectionError`.

### P5 — The system trust store verifies Telegram's certificate in the operator's environment; `Origin` is not required
- **Kind:** environment.
- **Status:** covered by the operator's no-account run on 2026-11-26: "TLS verified, certificate CN=*.web.telegram.org", all five DCs, no `Origin`.

**Rule applied.** P1's cheapest earlier test is affordable now and is scheduled after its first dependent step, so the verdict is REORDER. P2 and P3 ride on the same experiment.

---

## Restart Check

Not applicable. Neither `desc.md` nor the plan cites a prior failure, incident or abandoned attempt.

## Inherited Lessons

`desc.md` carries settled conclusions. How the plan's ordering satisfies each:
- **"The `Origin` header is not required; the transport does not send one."** Satisfied: step 2 specifies the handshake without `Origin`, and step 7's item 1 asserts its absence.
- **"Planet names, chosen because an independent client uses the same map; the media names never used."** Satisfied: step 3's `DC_HOSTS`, and step 7's item 3.
- **"The name map and the plain header are calibrated on one day's no-account probe; the live run is where disagreement would show."** **Not satisfied by the current order:** the live run is step 14, after the build. The REORDER experiment satisfies it: the account-level calibration runs before step 2.

---

## Risk items

### Risk 1 — The new "stop immediately" error is invisible to the consumers that recognise configuration errors

**Risk**

Paragraph 1 (plain). The library already has one error type for "the network settings in this account's config cannot be used" — today raised for a bad proxy setting. Two parts of the library check for exactly that type:
- the background loop that keeps fetching new messages, which stops for good when it sees it, instead of trying again every few minutes;
- the long-running worker process, which reports it to its caller as a configuration problem.

The plan introduces a second, separate error type for the WebSocket door's equivalent problems: an unknown setting value, a data centre with no known hostname, a certificate that does not verify. Neither of those two parts knows the new type. A WebSocket account behind a proxy that intercepts TLS would therefore have its polling loop retry forever, logging an error each time, and the worker would report the problem as a generic operation failure rather than a configuration problem.

Paragraph 2 (precise).
- **The two checks:** `tgdata/tgdata.py:93–100` `_polling_cannot_recover` tests `isinstance(error, (AuthRequiredError, ProxyConfigError, ReadBudgetError))`, and `tgdata/worker_protocol.py:262` `describe_error` maps `ProxyConfigError` → `category: 'configuration_error'`.
- **Why the plan misses them:** steps 2 and 4 define `TransportConfigError(ValueError)` as a **sibling** in `ws_stream.py`. It falls through polling (→ logged, `iterations += 1`, retried at the next interval) and through the worker (→ `operation_error`).
- **What already works:** `AccountPool._failure` (`account_pool.py:395–424`) is unaffected — any `ValueError` → `('unknown', False, None)` — and `health.classify` returns `None`.
- **The wrappers:** the plan's step 5 pass-through clauses in `_authenticate` / `_ensure_connected` name only `TransportConfigError`.
- **The placement problem:** `ws_stream.py` must stay Telethon-free (step 10's rule), so it cannot import `ProxyConfigError` from `connection_engine.py`, which imports Telethon.
- **Fires when:** a `websocket` account hits a certificate failure, an unmapped DC or a bad `transport` value, under `TgData.poll_for_messages`-style polling or in a `Worker` job.

**Severity** — Medium
**Category** — Consumer contract
**Impact**
- polling keeps retrying a failure that can only be fixed by the operator, filling logs;
- worker callers see `operation_error` where the documented category is `configuration_error` (`docs/worker.md:233–236`);
- user code that catches `ProxyConfigError` to detect "the configured route is unusable" misses the new cases;
- the `desc.md` claim "no consumer's code changes" is either broken, by editing the two checks, or the behaviour is wrong.

**NoobEng.** The library signals "this cannot work until a human fixes the config" by raising one specific exception class, and several loops and adapters decide stop-vs-retry by checking for that class, not for its parent `ValueError`. A brand-new class that only shares the `ValueError` parent passes the pool's check, which looks at `ValueError`, but fails the two checks that look at the specific class.

**Affected areas** — `TgData` polling (`_polling_cannot_recover`), the `Worker` wire protocol (`describe_error`), `ConnectionEngine._authenticate` / `_ensure_connected` (step 5), user code catching `ProxyConfigError`, `docs/worker.md`.

**Mitigation**

#### Mitigation — Quick
Add `TransportConfigError` to the two `isinstance` tuples (`tgdata.py:97`, `worker_protocol.py:262`), and keep the step-5 clauses as written.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust
Define `class TransportConfigError(ProxyConfigError)` in `connection_engine.py`, directly after `ProxyConfigError`, with a docstring naming its cases. Then:
- **The opener stays standard-library only and raises standard types.** `ws_stream.py` raises a plain `ValueError` for an IP-literal host, and lets `ssl.SSLCertVerificationError` propagate.
- **The class converts.** `ConnectionWebSocket._connect` in `websocket_transport.py` turns the certificate error into `TransportConfigError(...)`, raised from the original. `host_for` raises `TransportConfigError` for an unmapped DC. `websocket_transport.py` imports the class from `connection_engine`; that module is fully loaded before the lazy import runs, so there is no cycle.
- **The wrappers.** The step-5 clauses become `except ProxyConfigError: raise`, which covers both classes.
- **Export.** `tgdata/__init__.py` exports `TransportConfigError`.

Every existing `ProxyConfigError` check — polling, the worker, user code — handles the new cases with **no consumer edit**.

**Why this is robust:** it closes the gap at the type itself, so every present and future check written against the established configuration-error class covers the WebSocket cases automatically. It keeps the plan's "no consumer changes" promise and the opener's standard-library-only rule.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* A class exists: polling's `_polling_cannot_recover`, the worker's `describe_error`, and any user code catching `ProxyConfigError`. Subclassing serves all of them with one mechanism and no special-casing, so the robust fix already has class-wide reach, inside files the plan touches anyway (`connection_engine.py`, `websocket_transport.py`, `ws_stream.py`). The quick fix covers two of the three instances and edits consumers the plan promised not to touch.
*For future:* —

#### Mitigation — Long-term
Introduce a neutral base, `RouteConfigError(ValueError)`, for "the configured network route cannot be used". Re-parent both `ProxyConfigError` and `TransportConfigError` under it, export it, and change the polling, worker, docs and pool checks to test the base.

**Why this is long term effective:** the hierarchy says what it means — proxy and transport are siblings under one "route" concept — and future route settings get the right handling by subclassing the base.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* The same reach as the robust fix, at larger extent: it re-parents a public class and edits every consumer. Worth it only if a third kind of route setting appears; until then, `ProxyConfigError` is the route-error base in practice.

---

### Risk 2 — The offline proof's mechanics are under-specified for Telethon's behaviour: tests can hang, leak state, or stall on scaffolding

**Risk**

Paragraph 1 (plain). Most of the plan's tests make the real Telegram library talk to a fake local server that understands the web-socket handshake but not Telegram's own protocol. They do it to prove where connections go. But when the library opens a brand-new connection, it first runs an encryption handshake with the server and waits for an answer **with no time limit**. Against a fake server that never answers, such a test simply never finishes. Several other details also lack an owner:
- the library pauses one second between retries by default;
- it remembers the list of Telegram's servers in a place shared by every client in the process, which one test can poison for the next;
- building a stand-in member of the multi-account pool needs pool machinery the plan does not mention.

The result would be a test suite that hangs, runs slowly, or passes and fails depending on test order.

Paragraph 2 (precise).
- **The unbounded wait:** `MTProtoSender._connect` → `_try_gen_auth_key` → `authenticator.do_authentication(MTProtoPlainSender)` → `MTProtoPlainSender.send` awaits `self._connection.recv()` with **no timeout** (`telethon/network/mtprotoplainsender.py:36`). `connect_timeout` bounds only the transport open. So plan step 8's items 4–6 (`client.connect()` on a key-less session, `_create_exported_sender(4)`, `_account_operation`, `LoginFlow`) hang unless each call is wrapped in `asyncio.wait_for`, or `FakeDoor` closes after the first MTProto message.
- **The retry delay:** `retry_delay` defaults to 1 s (`_try_connect` sleeps between attempts). Step 9's item 7 (403 × 3 attempts) must pass `delay=0`.
- **The shared cache:** `_get_dc` reads and writes `cls._config` on `self.__class__` (`telegrambaseclient.py:798–802`). For clients built by `_client_class(TelegramClient)`, that is the cached `TgdataTelegramClient` class, shared by every client in the process. Step 8's item 5 must set and **delete** it in `finally`. The plan's `ConnectionWebSocket._ssl_context` seam needs the same restore discipline.
- **Pool scaffolding:** step 8's item 6 needs `AccountPool` sources built offline. The plan names no builder; `tgdata/smoke_tests/pool_storage_cases.py` and test_31's helpers exist for this.
- **Non-covering fakes:** none found. `FakeDoor` observes; the recording proxy records. The plan's fakes do not supply the behaviour under test.

**Severity** — Medium
**Category** — Test isolation / Phase ordering (detail vs difficulty)
**Impact** — steps 7–9 balloon in time; a hanging suite gets "fixed" by loosening assertions; order-dependent failures in other smoke tests that share the client class.
**NoobEng.** Telethon's connect has two phases: open the transport, which is bounded by `connect_timeout`, then create an auth key if the session has none, which is unbounded. Its server-config cache is a class attribute of whatever client class you built, and tgdata builds one cached subclass for the whole process. Any test that touches either must bound it or clean it up explicitly.
**Affected areas** — `test_50` (steps 7–9), other smoke tests run in the same process, the runtime of step 12's regression run.

**Mitigation**

#### Mitigation — Quick
Wrap every connect-type call in steps 7–9 in `asyncio.wait_for(…, 5)`, and accept the timeouts as the end of each path.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust
Specify the harness mechanics in steps 7–9:
- **`FakeDoor` modes:** `mtproto="close_after_first"` (decode and record the first message, then close, so key generation fails fast and deterministically) and `mtproto="silent"` (for the timeout item only).
- **One `bounded(coro, seconds=5)` helper** used by every path item.
- **`delay=0` / `retry_delay=0`** wherever retries are counted.
- **A `restoring()` context manager** that sets and then deletes `type(client)._config` and restores `ConnectionWebSocket._ssl_context`.
- **Pool sources** built with the existing offline pool builders (`pool_storage_cases.py`, test_31). Name them in step 8.

**Why this is robust:** every path item then terminates for a structural reason — the server closes — not a timing one, and no item can leave process-wide state behind for the next test.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* It closes this instance permanently — termination by structure, and isolation by explicit restore — entirely inside `test_50`, a file the plan creates. The quick fix leaves timing-based endings and the leaked class cache in place.
*For future:* —

#### Mitigation — Long-term
Extract a shared offline "Telegram door" harness module — a recording proxy for SOCKS5 and HTTP, a TLS test PKI, a scripted MTProto peer, and state-restoring fixtures — for all network-touching smoke tests (test_12, test_16, test_50), replacing their per-file relays.

**Why this is long term effective:** one maintained harness instead of several drifting copies; every future transport or proxy test inherits termination and isolation.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Real class: test_12 (`Socks5Relay`), test_16 and test_50 each carry their own network fakes. It fails the size gate: it touches files this plan does not otherwise touch. Future improvement, not a prerequisite: the robust harness survives it by moving into the shared module, not by being discarded.

---

### Risk 3 — The live checks can get the real account's session revoked if it is used from two places at once

**Risk**

Paragraph 1 (plain). Both live checks — the experiment this critique asks for first, and the plan's final step — connect the real account using a copy of its existing login file. Telegram treats one login as one device. If the copy connects while the account's normal application is also running on the same login, from another machine or process, Telegram can see the same login key active from two places at once and invalidate it. The account would then be logged out, and the operator would need to log in again with a code. The plan's brief mentions backing up the file, which does not prevent this.

Paragraph 2 (precise).
- **The symptom:** Telegram answers concurrent use of one `auth_key` with `AUTH_KEY_DUPLICATED`. Telethon 1.45.0's `AuthKeyDuplicatedError` (an `AuthKeyError`, code 406) reads: *"The authorization key (session file) was used under two different IP addresses simultaneously, and can no longer be used."*
- **Why the WebSocket checks are exposed:** their connections leave from the proxy's assigned address, which by design differs from wherever the account's normal application connects.
- **Where the gap is:** plan step 13's `live_check.py` "reads a tgdata config path, plus a backup check" and runs `TgData(config)` on the existing session. Nothing requires that no other client uses that session during the run. The REORDER experiment has the same exposure.
- **Fires when:** the operator's normal service — for example the downstream app using this account — is running during the check.

**Severity** — Medium
**Category** — Account safety
**Impact** — the account is logged out mid-check, and it needs an interactive re-login with a code sent to the owner. It confounds the experiment too: a duplicated-key error would look like the door refusing the account, which is a false disqualifying result.
**NoobEng.** An MTProto session file holds a long-lived key that Telegram binds to one logical device. Copying the file does not create a new device; it clones the key. Two simultaneous connections with one key are a protocol violation that Telegram punishes by revoking the key.
**Affected areas** — the REORDER experiment, plan step 13 (`live_check.py`, `live_check.md`), step 14.

**Mitigation**

#### Mitigation — Quick
Add a bold line to the brief: "stop every application using this account's session before running".
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust
Make exclusivity a hard precondition in both the experiment script and `live_check.py`:
- the script refuses to start without `--exclusive-confirmed`, which the brief tells the operator to pass only after stopping every process that uses the session;
- it runs on a copy of the session file, leaving the original untouched;
- it treats `AUTH_KEY_DUPLICATED` as "**invalid run** — another client was active", **not** as a disqualifying result;
- the brief's first step lists how to confirm the account's normal service is stopped.

**Why this is robust:** the failure needs an operator who explicitly asserted exclusivity, and a duplicated key can never be misread as the door refusing the account.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* It closes the exposure for both live checks — the experiment and step 14 — inside the scripts this work writes anyway. It also stops a duplicated key being misread as a disqualifying result, which matters more under REORDER. The quick fix relies on the operator remembering.
*For future:* —

#### Mitigation — Long-term
A tgdata-level session lease: the session store records an exclusive holder with a heartbeat, and every client refuses a session leased elsewhere.

**Why this is long term effective:** it prevents duplicated-key revocation for every tgdata deployment, not just live checks.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* A session lease would protect every deployment from duplicated-key revocation. It is a feature of its own: a new session-store contract and every client path. It fails the size gate, so it becomes a future improvement with its own issue if wanted.

---

### Risk 4 — A connect that fails half-way leaves its stream open (Low)

**Risk**

Paragraph 1 (plain). If the new connection gets as far as opening the encrypted web-socket stream and then fails on its very last setup step, nothing closes that stream. The library only closes connections it considers fully open. Each such failure leaks one network connection until garbage collection.

Paragraph 2 (precise). Telethon's `Connection.disconnect()` returns at once when `self._connected` is False (`connection.py:262–263`), and `connect()` sets `_connected` only after `_connect` returns. If `ConnectionWebSocket._connect` fails after `open_websocket` succeeded — in `self._codec = …`, `_init_conn()` or `await self._writer.drain()` — the stream stays open. The plan closes the socket only "on any failure after `_proxy_connect` returned". Wrap the post-open sequence in `try/except BaseException: self._writer.close(); raise`.

**Severity** — Low
**Category** — Resource leak
**Impact** — leaked sockets on repeated failures: transient-error retries, pool cooldown cycles.
**NoobEng** — Telethon's cleanup is gated on a flag set only after a successful connect, so partial connects must clean up after themselves.
**Affected areas** — `websocket_transport.ConnectionWebSocket._connect` (step 3).

### Risk 5 — `_ssl_context` is a process-wide switch (Low)

**Risk**

Paragraph 1 (plain). For testing, the plan gives the new connection type a setting that replaces which certificates are trusted. It is shared by every account in the process. A test that crashes before restoring it, or any code that sets it, silently changes certificate trust for every WebSocket account in that process.

Paragraph 2 (precise). Plan step 3 declares `ConnectionWebSocket._ssl_context = None` as a class attribute, used by `_connect` → `open_websocket(..., ssl_context=self._ssl_context)`. It is private and set only by `test_50`, which restores it per Risk 2's robust fix. Document in its comment that production code never sets it, and have step 10's canary assert it is `None` at import.

**Severity** — Low
**Category** — Security hygiene
**Impact** — certificate verification weakened process-wide if it is misused.
**NoobEng** — class attributes are shared by all instances. A trust seam on a class is effectively global.
**Affected areas** — `websocket_transport.ConnectionWebSocket` (step 3), `test_50`.

---

## Execution blockers (carried over, preconditions — not risks)

- **E1 — the maintainer's explicit go for the live run on the real account.** It gates step 14, and with this verdict, the experiment above.
