---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

Territory: this inquiry's own artifacts in /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/ — _branch.md, articulate_simple.md, surfacing.md, articulate_warm.md, sensemaking.md, decomposition.md, innovation.md, critique.md (critique.md carries the assembled design A* and the routed items: I-C Origin observation, E-C door-policy concern, P7 live calibration). Goal (received from _branch.md's Goal): a stable, decided meaning-and-shape for `transport = websocket` from which desc.md and plan.md for #67 can be written — decisions on the ten open points, a concern register, a test strategy, doc corrections. Enumerate the onward route-field (typed, prescriptive, never choosing). Write routelister.md (the per-run route-map) and _route.md (the persistent cross-run concept-map index), both in that traverse/ folder (the inquiry root).

---

# Route-Map — #67 WebSocket transport (root / project-space, fresh)

**Goal (received):** a stable, decided meaning-and-shape for `transport = websocket`, from which `desc.md` and `plan.md` can be written. It covers decisions on the ten open points, a concern register, a test strategy, and doc corrections.

**Territory:** the eight inquiry artifacts listed above. All routes are `project-space` grain.

## Map Header

- **Identities:** 19
- **High priority:** 9
- **Essential (core):** 12, of which 2 are `@post-build`

## Route Index

| # | Direction | Engagement | Priority | Essentiality | ✓ |
|---|---|---|---|---|---|
| R1 | the decision record for the ten open points | CONSOLIDATE | HIGH | core | |
| R2 | the fail-fast / transient error contract | DEVELOP | HIGH | core | |
| R3 | the verified binary WebSocket stream opener | DEVELOP | HIGH | core | |
| R4 | the connection class that names each DC at construction | DEVELOP | HIGH | core | |
| R5 | the DC→planet-name map and its corrected grounds | REFINE | MED | supporting | |
| R6 | the `transport` key and the door's branch | DEVELOP | HIGH | core | |
| R7 | transport observability: the route line, the health field, Telethon's connect line | DEVELOP | MED | supporting | |
| R8 | the login checkpoint's conditional `transport` entry | DEVELOP | HIGH | core | |
| R9 | the no-IP proof across every construction path | DEVELOP | HIGH | core | |
| R10 | the default-path byte-identity invariant | TEST | HIGH | core | |
| R11 | the Telethon-internals canary | DEVELOP | MED | core | |
| R12 | the transport × health-events non-interaction | TEST | LOW | supporting | |
| R13 | the docs that become false, and the new README section | DEVELOP | MED | core | |
| R14 | the outside-world risk register | CONSOLIDATE | MED | supporting | |
| R15 | the live calibration on the real account | TEST | HIGH | core · @post-build | |
| R16 | idle survival under Telethon's keep-alive | TEST | LOW | core · @post-build | |
| R17 | whether the door requires the `Origin` header | TEST | LOW | peripheral | |
| R18 | door-policy refusals that would read as account verdicts | INVESTIGATE-FRONTIER | MED | supporting | |
| R19 | a renamed door's failure semantics under pool retry | DIAGNOSE | LOW | supporting | |

## Sources

- **[S1]** `critique.md` § The assembled design (for desc.md / plan.md)
- **[S2]** issue #67 body § "What a probe found" (as-of 2026-11-26)
- **[S3]** Telethon 1.45.0 package source, `telethon/client/` and `telethon/network/connection/`, read during this inquiry

---

## Routes

### R1 — the decision record for the ten open points
- **Goal:** a decided meaning-and-shape for `desc.md` and `plan.md`
- **Engagement-type:** CONSOLIDATE
- **Move:** gather each of the ten open points from `_branch.md`, and the concerns found beyond them, into one table.
  - **Each row:** the point, its decision, its grounds, and where it was decided (the sensemaking A-number, the critique verdict).
- **Lands:** one place where every open point reads as decided, or as routed to the live run, with no point left implicit.
- **Touches:**
  - `_branch.md` § Source Input (the ten points, verbatim);
  - `sensemaking.md` A1–A14;
  - `critique.md` verdicts, including the corrected A3 grounds and the L-C promotion.
- **WHY:** the decisions are spread over four artifacts, and two were changed in critique, so the end goal gains a single, current premise that `desc.md` can be written from without re-reading the traverse.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "take critique's version wherever it differs from sensemaking" (bc critique corrected A3's grounds and promoted L-C)
  - "mark the live-only items as routed, not decided" (bc the Origin question, door policy and calibration cannot be settled offline)
  - **Meaning-gaps:**
    - whether the `health_check()["transport"]` key also appears for `tcp` — low — additive either way; decide at plan time
    - whether the fail-fast class subclasses `ProxyConfigError` or is a sibling `ValueError` — low — `_failure` treats both the same

### R2 — the fail-fast / transient error contract
- **Goal:** the same
- **Engagement-type:** DEVELOP
- **Move:** define tgdata's fail-fast `ValueError`-family class and the fault→class table.
  - **Fail fast:** an unknown value, an unmapped DC, a certificate failure, an IP-literal host.
  - **Transient (`ConnectionError`):** a bad upgrade, resets, protocol violations, a server close.
  - **Mid-session rule:** only `IOError` / `IncompleteReadError` after connect.
- **Lands:** a contract the stream, the class and the config parse all raise against. `AccountPool._failure` and `health.classify` need no change.
- **Touches:**
  - `AccountPool._failure` (`ValueError` → unknown, `ConnectionError` → transport; unchanged);
  - `ProxyConfigError(ValueError)` (the existing precedent).
- **Basis:** [S3] `telethon/network/connection/connection.py` `_recv_loop` — only `IOError` / `IncompleteReadError` are handled quietly; anything else is logged as "Unexpected exception in the receive loop" (establishes the mid-session rule)
- **Basis:** [S3] `telethon/client/telegrambaseclient.py:560`, `:842` — connections are built outside `_try_connect` (establishes that an `__init__` error is never retried)
- **WHY:** expressed through base classes the existing machinery already reads, so neither the pool nor the health layer is touched. The end goal gains a taxonomy with zero new mechanism.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "define it before the stream and the class" (bc both raise its classes)
  - "convert `ssl.SSLCertVerificationError` explicitly" (bc it is an `OSError`, which Telethon would otherwise retry)
  - **Meaning-gaps:**
    - the exact class names — low — naming only

### R3 — the verified binary WebSocket stream opener
- **Goal:** the same
- **Engagement-type:** DEVELOP
- **Move:** build `open_websocket(host, *, sock=None, port=443, timeout, ssl_context=None) -> (reader, writer)`, adapted from the probe.
  - **TLS:** the default context, SNI set to the host.
  - **Upgrade:** `/apiws`, `binary`, a `101` plus the accept check.
  - **Framing:** masked binary frames, continuation joined, ping→pong, close or EOF → `IncompleteReadError`.
  - **Guard:** it refuses IP literals.
  - **Rule:** no Telethon imports.
- **Lands:** a Telethon-free unit that turns "a name, and maybe a tunnelled socket" into a verified byte stream with exactly the five methods Telethon calls.
- **Touches:**
  - `ws_door_probe.py` `WsReader` / `WsWriter` / `open_websocket` (the tested origin);
  - `ObfuscatedIO`, which captures `_reader` / `_writer` at `_init_conn`.
- **WHY:**
  - **neighbourhood:** it isolates all WebSocket code from Telethon, bounding a future Telethon port to the glue class;
  - **goal:** the end goal gains the transport's whole new wire behaviour in one testable piece.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "keep the SSL context injectable" (bc the offline proof needs a test CA)
  - "one timeout bounds TLS plus upgrade" (bc Telethon passes a single connect timeout)
  - **Meaning-gaps:**
    - whether `Origin` stays in the header set — low — a single constant, settled by R17
    - the maximum frame size to accept — low — a protocol-violation bound; any sane cap is safe

### R4 — the connection class that names each DC at construction
- **Goal:** the same
- **Engagement-type:** DEVELOP
- **Move:** subclass `ConnectionTcpObfuscated`.
  - `__init__(ip, port, dc_id, **kw)` calls `super().__init__(<name for dc_id>, 443, dc_id, **kw)`, discarding the IP.
  - `_connect` gets the socket from `_proxy_connect` (or `None` for direct), then `open_websocket`, assigns `_reader` / `_writer`, then `_codec` / `_init_conn` / `drain`.
- **Lands:** a class that cannot hold or dial an IP. Telethon's four construction sites — main, exported, reconnect, CDN — reach only mapped names, or a fail-fast error.
- **Touches:**
  - `Connection.__init__` (stores `_ip` / `_port` from its arguments);
  - `_proxy_connect` (`dest_host = self._ip`; converts python-socks' errors to `ConnectionError`).
- **Basis:** [S3] `telethon/network/connection/connection.py:36–42`, `:114–126` (establishes that the base stores the name, and that the proxy path's errors are already retryable)
- **Basis:** [S3] `telethon/client/telegrambaseclient.py:931–938` — the CDN client uses the parent's connection class (establishes that an unmapped CDN DC fails fast)
- **WHY:** "never an IP" becomes a property of the object rather than of a code path, so the end goal's fail-closed requirement holds by construction.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "forward `**kwargs`" (bc a Telethon patch adding a keyword must not break construction)
  - "override nothing else" (bc every extra override is canary surface)
  - **Meaning-gaps:**
    - whether the plain obfuscation header works for every DC on the real account — mid — the probe used it without DC bytes; if live disagrees, the probe's header variant is the local fix

### R5 — the DC→planet-name map and its corrected grounds
- **Goal:** the same
- **Engagement-type:** REFINE
- **Move:** restate the map's justification in the decision record.
  - It is **not** "the superset that worked" — both families worked for every name the design dials.
  - It **is** an independent client's use of the same five names, plus readability.
- **Lands:** `{1: pluto, 2: venus, 3: aurora, 4: vesta, 5: flora}` with grounds that survive scrutiny. The formula and the override are recorded as rejected.
- **Basis:** [S2] "Every other `kwsN`, `kwsN-1` and `<planet>-1` name worked" (establishes that the families are equal for the names used)
- **Basis:** paraphrase: a web search this run summarised gotd/td's `telegram/dcs/prod.go` as mapping DC 1–5 to the same planet names over `wss://…/apiws`; the file itself was not opened (supports the external corroboration)
- **WHY:** sensemaking's original grounds were void, so the end goal gains a map choice a reviewer can check.
- **Priority:** MED · **Confidence:** MED · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "open the cited library file before quoting it in `desc.md`" (bc only a search summary was seen)

### R6 — the `transport` key and the door's branch
- **Goal:** the same
- **Engagement-type:** DEVELOP
- **Move:**
  - `_load_config` normalises `transport` into `ConnectionConfig.transport` (`tcp` default, or `websocket`). An unknown value raises a config error.
  - `_new_client` imports the class **inside** the `websocket` branch and adds `connection=`.
  - It is independent of `proxy` / `require_proxy`; `websocket` without a proxy goes direct by name.
- **Lands:** a per-account switch that every consumer (`TgData`, `AccountPool`, `Worker`, `LoginFlow`) inherits through the one door, with no consumer edits.
- **Touches:**
  - `ConnectionConfig` (the frozen config record);
  - `_new_client` (the single client factory);
  - `_OwnedSource._new_client` (adds strict options to the same call).
- **WHY:**
  - **neighbourhood:** the lazy import confines any transport breakage to WebSocket users, because plain `TgData` is not pinned;
  - **goal:** the end goal gains the selection seam at the narrowest point.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "normalise once, in `_load_config`" (bc the binding must see the same value)

### R7 — transport observability: the route line, the health field, Telethon's connect line
- **Goal:** the same
- **Engagement-type:** DEVELOP
- **Move:**
  - add "over WebSocket by name" to the one-time route log line, for `websocket` only;
  - add `health_check()["transport"]`;
  - name Telethon's INFO line, `Connecting to <host>:443/…`, as the per-connection evidence.
- **Lands:** an operator can confirm the transport per instance (even with logging off) and per connection (with logging on).
- **Basis:** [S3] `telethon/network/mtprotosender.py:245`, `:296` and `Connection.__str__` (establishes that Telethon's own log prints the host)
- **WHY:** the triage named the silent failure as the one that matters, so the end goal gains a visible confirmation at no new mechanism cost.
- **Priority:** MED · **Confidence:** HIGH · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "TCP text unchanged" (bc the default must be byte-identical)
  - **Meaning-gaps:**
    - whether `tcp` also reports the key — low — additive

### R8 — the login checkpoint's conditional `transport` entry
- **Goal:** the same
- **Engagement-type:** DEVELOP
- **Move:** add `transport` to `LoginFlow`'s binding settings only when it is not `tcp`, and list it in the login doc.
- **Lands:** a transport change between `start` and `submit` invalidates the checkpoint, as a proxy change does, while every TCP checkpoint's hash stays bit-identical.
- **Touches:**
  - `LoginFlow`'s binding (a SHA-256 over the network-identity settings);
  - `docs/stepwise_login.md:90`.
- **WHY:** the transport changes the exit address the way the proxy does, so the end goal gains a binding that still means "the same network identity", without invalidating existing logins.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "pin today's hash in a test first" (bc that is the invariant)

### R9 — the no-IP proof across every construction path
- **Goal:** the same
- **Engagement-type:** DEVELOP
- **Move:** build the offline harness — a local TLS WebSocket server with a test CA, plus a recording HTTP-CONNECT/SOCKS5 proxy extending `test_12`'s relay. Assert that every recorded destination is a mapped name on:
  - main connect, reconnect and exported senders;
  - the strict-option paths;
  - a mixed `tcp` + `websocket` pool.

  Fakes replace only `open_websocket`, and one test runs the real TLS server end to end.
- **Lands:** the guarantee proven on every path, with a test that would fail on any single by-IP connection.
- **Touches:**
  - `test_12`'s recording relay;
  - `AccountPool` (the mixed pool).
- **WHY:**
  - **neighbourhood:** it protects against future refactors mixing transports by caching;
  - **goal:** the end goal gains proof, not just argument, for its central requirement.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "never fake below `_proxy_connect`" (bc then the tunnel, and so the proof, is bypassed)
  - **Meaning-gaps:**
    - how much MTProto the local server must speak for Telethon to complete `connect()` — mid — it decides whether the harness echoes, or replays a recorded auth exchange
    - driving reconnect and an exported sender offline — mid — these need a way to force a DC switch or a drop

### R10 — the default-path byte-identity invariant
- **Goal:** the same
- **Engagement-type:** TEST
- **Move:** assert, for `tcp` and for no key:
  - the `TelegramClient` constructor kwargs;
  - the route log text;
  - the binding hash;

  each against today's values.
- **Lands:** the maintainer's "keep it that way" as a passing check, not a promise.
- **Basis:** `_branch.md` § Source Input — "WITHOUT harming or breaking the existing design … wants kept that way" (establishes the constraint)
- **WHY:** the end goal gains the user's anchor turned into evidence.
- **Priority:** HIGH · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "capture today's values before any change" (bc afterwards there is nothing to compare against)

### R11 — the Telethon-internals canary
- **Goal:** the same
- **Engagement-type:** DEVELOP
- **Move:** a `test_14`-style canary, "run after any Telethon upgrade", asserting:
  - the `Connection.__init__` signature;
  - `_connect(timeout, ssl)`;
  - `_proxy_connect` using `_ip` and converting python-socks' errors;
  - `ObfuscatedConnection._init_conn` reading `_reader` / `_writer`;
  - the four construction sites passing `dc_id`;
  - `cdn_supported` never set.
- **Lands:** the reliance on private internals is guarded without a runtime version pin.
- **Touches:** `test_14` (the canary convention).
- **WHY:** plain `TgData` accepts `>=1.45,<2.0` (warm conflict C1), so the end goal gains drift detection where no pin exists.
- **Priority:** MED · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "assert behaviour, not source text" (bc formatting changes must not trip it)

### R12 — the transport × health-events non-interaction
- **Goal:** the same
- **Engagement-type:** TEST
- **Move:** assert that each class in the error contract yields `health.classify(...) is None`, and that no health event is emitted.
- **Lands:** a door outage cannot become account-level noise in #4's health events.
- **Touches:** `health.classify` (returns `None` for transport and configuration errors).
- **WHY:** it pins a cross-feature interface the decomposition missed, so the end goal gains a guard against a later health change.
- **Priority:** LOW · **Confidence:** HIGH · **Essentiality:** supporting
- **Guidance Mode:** none

### R13 — the docs that become false, and the new README section
- **Goal:** the same
- **Engagement-type:** DEVELOP
- **Move:**
  - correct the `connection_engine.py:154` comment, "remote DNS is moot";
  - update the `parse_proxy_url` and `_new_client` docstrings;
  - add the README section "Connecting through Telegram's WebSocket door" (the key, the proxy requirement, never-an-IP, direct-by-name, what failures look like, how to confirm it is active, the verified Telethon version);
  - update `stepwise_login.md`.
- **Lands:** no statement in the repository is false once the key exists, and operators have one place to read.
- **WHY:** sensemaking A11 found they are false the moment the key ships, so the end goal gains doc corrections as part of the change, not after it.
- **Priority:** MED · **Confidence:** HIGH · **Essentiality:** core
- **Guidance Mode:** compact
  - "say 'network transport'" (bc 'transport' already names request envelopes elsewhere)

### R14 — the outside-world risk register
- **Goal:** the same
- **Engagement-type:** CONSOLIDATE
- **Move:** collect the risks tgdata cannot remove into one register for `desc.md` and the README:
  - the unpublished door;
  - a desktop-app `api_id` through the web door;
  - the relays' rate limits;
  - one day's calibration of the map;
  - TCP-made login keys proven only live;
  - the trust store on servers;
  - a renamed door looks like an outage;
  - door-policy errors may read as health `unclassified`.
- **Lands:** each accepted risk is stated once, with what would show it.
- **WHY:** the end goal's concern register is incomplete without the risks that live outside the code.
- **Priority:** MED · **Confidence:** MED · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "pair each risk with its observation point" (bc most resolve only in the live run)
  - **Meaning-gaps:**
    - whether the relays rate-limit per address — mid — unobserved; it changes operator advice
    - how Telegram treats a desktop `api_id` over the web door — mid — unobserved; it is the main account-safety unknown

### R15 — the live calibration on the real account
- **Goal:** the same
- **Engagement-type:** TEST
- **Move:** on the maintainer's go, with `transport = websocket` on the real account:
  - log in;
  - read;
  - download from another DC;
  - reuse an existing TCP-made session;

  recording every exit, with none by IP.
- **Lands:** the one-day probe calibration is confirmed, or contradicted, for the real account, the real `api_id` and the real proxy.
- **Basis:** [S2] "TLS verified; WebSocket `101` …; an MTProto auth key created …; a ping answered" (records the no-account calibration this run would extend)
- **WHY:** the offline proof cannot show Telegram's policy toward the account, so the end goal's test strategy gains its only real-world check.
- **Priority:** HIGH · **Confidence:** MED · **Essentiality:** core · @post-build
- **Guidance Mode:** compact
  - "run only after the offline suite is green" (bc a live failure should be the door's, not the code's)

### R16 — idle survival under Telethon's keep-alive
- **Goal:** the same
- **Engagement-type:** TEST
- **Move:** hold a WebSocket client idle for more than 300 s on the real path, and confirm it is still alive.
- **Lands:** the source-verified reading — 60 s pings on every client; exported senders closed after at most about 120 s idle — confirmed against the relay's real cut.
- **Basis:** [S2] "One survived 150 s idle and was cut by 300 s" (establishes the cut window)
- **WHY:** the end goal's decision of "no transport pings" gains live confirmation.
- **Priority:** LOW · **Confidence:** HIGH · **Essentiality:** core · @post-build
- **Guidance Mode:** none

### R17 — whether the door requires the `Origin` header
- **Goal:** the same
- **Engagement-type:** TEST
- **Move:** run the no-account probe with `--no-origin` across DC 1–5, on the maintainer's go.
- **Lands:** a recorded answer:
  - if all five DCs work without it, the header can be dropped;
  - otherwise it stays, with the reason in a code comment.
- **Touches:** `ws_door_probe.py` `--no-origin`
- **WHY:** indirect — it trims one header or documents why it stays. A small honesty and fingerprint nicety for the end goal.
- **Priority:** LOW · **Confidence:** HIGH · **Essentiality:** peripheral
- **Guidance Mode:** none

### R18 — door-policy refusals that would read as account verdicts
- **Goal:** the same
- **Engagement-type:** INVESTIGATE-FRONTIER
- **Move:** in the live run, record any RPC error that appears only under `websocket`, and compare it with `tcp`. Check whether its code (401, 403, 406, 420) would make #4's health layer emit `unclassified`.
- **Lands:** the boundary between "the door refused" and "the account is in trouble" is known, or recorded as not yet seen.
- **Touches:** `health.py` `_UNCLASSIFIED_CODES` (the codes that turn an unlisted RPC error into `unclassified`)
- **WHY:** a false account verdict could lead an operator to retire a healthy account, so the end goal's concern register gains its least-explored region.
- **Priority:** MED · **Confidence:** LOW · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "compare the same call over both transports" (bc only the difference isolates the door)

### R19 — a renamed door's failure semantics under pool retry
- **Goal:** the same
- **Engagement-type:** DIAGNOSE
- **Move:** examine what the pool does when every WebSocket attempt fails at the proxy's DNS — transient, so cooled down and retried indefinitely. Decide whether that needs only documentation, or a visible marker.
- **Lands:** the operator-facing description of "the door moved" vs "an outage".
- **WHY:** the critique's only caveat on the core design (D8), so the end goal gains an honest failure story.
- **Priority:** LOW · **Confidence:** MED · **Essentiality:** supporting
- **Guidance Mode:** compact
  - "prefer docs over mechanism" (bc an outage and a rename are indistinguishable at first)

---

## Excluded

| Candidate | Reason |
|---|---|
| a formula `kws{N}` instead of the map | Killed in critique. The external corroboration favours planets; the formula's only gain is no table. |
| name rotation between families | Killed in critique. Ineffective on strict clients, and it hides a family outage. |
| a constrained per-account host override | Killed in critique. It needs a class factory for an unobserved event; a release is the override. |
| matching the web clients' codec | Killed in critique. No evidence of an effect; it lives on only as a variable if R18 finds door-specific refusals. |
| an out-of-process relay, a monkeypatch, a SOCKS shim | Killed in sensemaking A1. They need the excluded MTProto-proxy protocol, change the default, or duplicate the seam. |
| owning the tunnel via python-socks | Killed. Telethon's `_proxy_connect` already converts its errors to retryable `ConnectionError`s. |
| taxonomy by attribute | Killed. Telethon and the pool read only types. |
| tgdata's own obfuscation | Killed. It duplicates `ObfuscatedIO`. |
| a `NetworkRoute` object, or a network-identity helper | Killed. `ConnectionConfig` already is that object; one field needs no helper. |
| transport-level pings | Decided against in sensemaking A4. Telethon's 60 s keep-alive covers the cut; live confirmation is R16. |
| a WebSocket library dependency | Decided against in sensemaking A9. It is message-oriented, and conflicts with reusing `_proxy_connect`. |
| a runtime Telethon version pin for this transport | Decided against in A10 and critique. Construction-time naming plus the canary (R11) guard it instead. |
| writing `desc.md` / `plan.md` | A process step, not a concept-direction. |

---

## Telemetry

- **Mode:** root / project-space (breadth). **Entry point:** fresh (no prior `_route.md`).
- **Identities:** 19.
  - **Kinds:** teleological 10 (DEVELOP ×9, INVESTIGATE-FRONTIER ×1); epistemic 9 (CONSOLIDATE ×2, REFINE ×1, TEST ×5, DIAGNOSE ×1).
- **High priority:** 9. **Essentiality:** core 12 (2 `@post-build`), supporting 6, peripheral 1.
- **Individuations:** 19 identities. One split under lean-to-split: R16 (idle survival) was split from R15 (live calibration), because the keep-alive decision is independent of the account-policy questions. No uncertain merges. Stale entries: 0 (fresh).
- **Convergence:** a second sweep over the critique's assembled design and the Excluded candidates yielded no new identities. No frontier flags.
- **Basis entries:** 10, on 7 routes.
  - **Pointers:** 9 — S3 ×5, S2 ×3, `_branch.md` ×1.
  - **Paraphrase:** 1 (R5, the library file — seen as a search summary only).
  - **Not recovered:** 0.
  - **Routes needing none:** 12.
- **Failure modes checked:**
  - **LAYER 1:** over-merge (R15 and R16 split, R2 kept apart from R3 and R4); wrong-grain (identities, not files); goal-loss; type-misassignment (TEST on the epistemic checks, DEVELOP on builds); basis — no invention: R5's source is marked as a paraphrase.
  - **LAYER 2:**
    - **selection-creep:** no ranking — the index order follows the decomposition;
    - **process-coupling:** "write desc/plan" is excluded as a process step;
    - **description-collapse:** every record is Move / Lands;
    - **manifestation-dump:** none.
- **Verdict: PROCEED.**
