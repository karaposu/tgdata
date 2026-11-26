---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

/Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/_branch.md — inputs also in that folder: articulate_simple.md, surfacing.md, articulate_warm.md, sensemaking.md (SV6 stabilized model), decomposition.md (pieces P0–P7 with interfaces and three hidden couplings). Generate ideas that could make the #67 WebSocket transport design MORE elegant or SAFER without harming the existing design — alternatives to the SV6 choices (shape, map home, taxonomy, binding, observability, tests, canary) and unrealised concerns — for Critique to evaluate. SAVE the output as /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/innovation.md

---

# Innovation — making the #67 transport more elegant or safer

## Seed

**Seed type:** dissatisfaction plus question. SV6 is a good design, so where is it still weaker than it could be, and what has nobody asked yet?

**Direction (valuation).** The maintainer's priority is that the existing design stays elegant, and that a single by-IP connection, which fails silently, can never happen. Ideas that strengthen "never an IP" or reduce what the transport touches are worth more than ideas that add features.

**Methodology mode.**
- **Inherited:** Standard default — the seed asks to "generate ideas … alternatives … for Critique".
- **Alternative:** Contrarian-rethink, which is Framer-weighted. Under it, the candidate space would centre on overturning SV6's in-process subclass and its fixed map, producing mostly frame-rejections.
- **Decision:** Standard default. Each mechanism still carries one contrarian variation, so the contrarian direction is covered without letting it dominate a design that sensemaking tested on structural grounds (A1–A14).

**Facts re-checked in Telethon 1.45.0 and tgdata for this run:**
- **F1 — Telethon's connect log already names the host.** `Connection.__str__` is `'{}:{}/{}'.format(self._ip, self._port, <class name minus "Connection">)`, and `MTProtoSender` logs `Connecting to %s...` and `Connection to %s complete!` at INFO (`mtprotosender.py:245`, `:296`). With `_ip` set to the host name, Telethon's own log reads `Connecting to vesta.web.telegram.org:443/<Name>...`.
- **F2 — Telethon maps python-socks' errors inside its own proxy code.** `_proxy_connect` replaces python-socks' `ProxyError`, `ProxyConnectionError` and `ProxyTimeoutError` with `ConnectionError` subclasses (`connection.py:114–126`). That is what makes proxy failures retryable `IOError`s.
- **F3 — tgdata's health module classifies transport and configuration errors as "not a health signal".** `health.classify` returns `None` for them; only RPC errors, waits, registered classes and `AuthRequiredError` reasons carry verdicts. The account-level codes are 401, 403, 406 and 420, and an *RPC* error with one of those codes is reported as `unclassified` (`health.py:88–90`, `:180–220`).
- **F4 — Both name families worked for the main DCs.** The probe record on issue #67: `kwsN` for DC 1–5 worked, as did every `<planet>` name. Only the `-1` media names `kws2-1` and `kws4-1` failed — names the design never uses.
- **F5 — The `proxy` extra is `python-socks[asyncio]>=2.0`,** and it is the only optional dependency.

---

## Phase 2 — Generation (7 mechanisms × generic / focused / contrarian)

### 1. Lens shifting (framer)

**L-G (generic) — the "fewest private writes" lens.**
- **Idea:** under the lens "elegance = the smallest private surface", the class should not assign `self._ip` / `self._port` after construction. `__init__` should call `super().__init__(host, 443, dc_id, loggers=…, proxy=…, local_addr=…)`, so Telethon's own constructor stores the name.
- **Result:** the class writes no private attributes. It overrides `__init__` only to swap arguments, and `_connect` only to open the stream.

**L-F (focused) — the "operator checking at runtime" lens.**
- **Idea:** by F1, Telethon already logs every connection's host and port at INFO. So runtime evidence of "by name" exists without new code. tgdata's additions shrink to:
  - the route-line suffix, logged once per instance;
  - optionally, `health_check()["transport"]`.
- **Result:** an operator verifies "never an IP" by grepping Telethon's log for `Connecting to` lines with no IP literal.

**L-C (contrarian) — the "most users never enable it" lens.**
- **Idea:** import the transport module lazily, inside `_new_client`'s `websocket` branch. The default path then never imports it at all, so no import-time side effects or import cost reach TCP users.
- **Result:** "byte-identical" extends from constructor arguments to the set of imported modules.

### 2. Combination (generator)

**C-G (generic) — the no-IP guarantee × the lowest layer.**
- **Idea:** combine the guarantee with P1's stream opener. `open_websocket` refuses a host that parses as an IP literal (`ipaddress.ip_address(host)` succeeds) with P0's fail-fast class.
- **Result:** even a future caller misusing P1 cannot dial an IP through it. The guarantee then holds at two layers: the object (P2) and the opener (P1).

**C-F (focused) — the binding × the proxy precedent.**
- **Idea:** factor "network-identity settings, included only when non-default" into one helper, used by `LoginFlow`'s binding. A future setting would join with one line.

**C-C (contrarian) — the transport × the web clients' codec.**
- **Idea:** carry whichever codec Telegram's own web clients use (possibly padded intermediate rather than abridged), so the connection looks like a browser's. This would reduce the account-fingerprint concern (R6).

### 3. Inversion (framer)

**I-G (generic) — "a DC→name map is needed", inverted: "the DC number *is* the name."**
- **Idea:** `kws{dc_id}.web.telegram.org` is a formula, so no table is needed (F4: all five worked).
- **Depth check, existence axis:** the map's existence count goes from 5 entries to 0. A range check (1–5) replaces it, keeping fail-fast for unknown DCs.
- **Second-order finding:** sensemaking chose planets as "the superset that worked" (A3/A14). By F4, that superset is about the `-1` names, which the design never dials. **For the names actually used, the two families are evidence-equal.** The planet choice needs a different justification, or it is a coin toss.

**I-F (focused) — "one name per DC", inverted: "two names per DC, both Telegram's."**
- **Idea:** on each `_connect` attempt — Telethon reuses the same connection object on reconnect — alternate between `<planet>` and `kws<N>`.
- **Result:** if Telegram renames or retires one family, the account keeps working. It is still never an IP: a *name* fallback inside the door, not a transport fallback.

**I-C (contrarian) — "send `Origin: https://web.telegram.org`", inverted: "send no `Origin`."**
- **Idea:** a non-browser client honestly sends no `Origin`. If the door accepts that, the transport stops imitating the web app's header.
- **Status:** the probe has `--no-origin`, but its results were recorded with `Origin` on. Whether the door requires it is untested.

**I-D (depth, on P0's commitment) — "taxonomy by base class", inverted: "taxonomy by an attribute" (`error.retryable`).**
- **Idea:** classify failures by an attribute instead of by base class.
- **Depth:** Telethon's `_try_connect` reads only `isinstance(e, (IOError, TimeoutError))`, and `AccountPool._failure` reads only types. An attribute is invisible to both, so the base class is the only lever the existing machinery reads.

**I-E (frame audit, on the central shape) — "reuse `ConnectionTcpObfuscated`", inverted: "subclass bare `Connection` with tgdata's own obfuscation."**
- **Idea:** do not reuse Telethon's obfuscation; write tgdata's own.

### 4. Constraint manipulation (framer — ADD and REMOVE)

**CM-G (ADD) — "the class holds no class-level or shared mutable state."**
- **The fact:** one class object is shared by every account in a process. A pool can mix `tcp` and `websocket` accounts, because each engine passes `connection=` per call.
- **Under this constraint:**
  - any per-connection record (C-G, L-F) must live on the instance;
  - the map is an immutable module constant;
  - **P5 gains a mixed-pool test:** one `tcp` and one `websocket` account in one `AccountPool`, each dialling only its own kind of destination.

**CM-F (REMOVE) — "reuse Telethon's `_proxy_connect`", removed: own the tunnel via python-socks' public API** (`Proxy.from_url(..., rdns=True).connect(dest_host=host, dest_port=443)`), as the probe did for SOCKS.
- **Gain:** one private Telethon method fewer.

**CM-C (REMOVE, contrarian) — "no per-account host override", removed, but constrained.**
- **Idea:** allow `websocket_host = <label>`, which expands only to `<label>.web.telegram.org`. Operators can then follow a renamed door without a release, and no arbitrary host is possible.
- **Cost (K-I7):** it requires a class built per config, cached like `_client_class`, because Telethon accepts only a class.

### 5. Absence recognition (generator — patch and redesign, both directions)

**AR-P1 (patch) — a missing runtime record of where each connection went.**
- **Already present in a different form:** by F1, Telethon's INFO line is that record.
- **The real absence:** nothing *asserts* it. P5's recording proxy is the only assertion, and it runs offline.
- **Patch:** none at runtime. In the docs (P6), name the log line as the operator's evidence.

**AR-P2 (patch) — a missing interface in the decomposition: the transport × #4's health events.**
- **The question:** a WebSocket failure escapes a public call, so does the health layer emit anything?
- **By F3, no.** Transport and configuration errors are not health signals, and the fail-fast classes are `ValueError`s, not RPC errors.
- **Patch:** P5 gains a test that each P0 class yields `classify(...) is None` and no health event. This pins the non-interaction so a later health change cannot start emitting "unclassified" events for a door outage.

**AR-R (redesign) — "designed from scratch, the network route would be one object":** `proxy`, `require_proxy` and `transport`, consumed together by the door, the binding, the route line and `health_check`.
- **Already present in a different form:** `ConnectionConfig` *is* that object, a frozen record read by all four. The redesign collapses to "put `transport` in `ConnectionConfig`", which is SV6.
- No new object is needed.

### 6. Domain transfer (generator)

**DT-G (native: HTTP clients' pluggable transports — httpx `transport=`, requests `HTTPAdapter`).**
- **Confirms the shape:** the transport is injected per client, and the client is unaware of it.
- **Imported lesson:** those libraries test most behaviour through a *mock transport at the seam*, and keep one real-socket test.
- **Applied to P5:** most tests inject a fake `open_websocket` (P1's interface) into P2. One test runs real TLS against the local server. That makes the harness cheaper and keeps proof of the real wire.

**DT-F (native: censorship-circumvention pluggable transports — the Tor PT model).**
- **The source domain:** the transport name is part of the configured route ("bridge line"). A PT never falls back to direct, and logs name the transport.
- **Imported:**
  - P0 messages carry the transport's name, e.g. "WebSocket transport: …";
  - the binding includes the transport. This confirms A8 from a field with the same threat model: a route change is an identity change.

**DT-C (different domain: keyed connectors in electrical and medical-gas fittings — a plug that physically cannot go in the wrong socket).**
- **The safety comes from the shape, not from a check.** Imported:
  - the constructor *ignores* its `ip` argument entirely, rather than validating it;
  - the opener cannot accept an IP (C-G).
- A wrong path cannot be expressed at all.

### 7. Extrapolation (generator)

**E-G — the Telethon 2.x trend (its network layer is rewritten).**
- The subclass dies in 2.x, but P1 has zero Telethon imports. A port therefore rewrites only P2's roughly 40 lines of glue.
- **Implication:** keep P1 strictly Telethon-free, which decomposition already states. Don't let framing code import Telethon "for convenience".

**E-F — the "more accounts per process, more providers refusing IP targets" trend.**
- WebSocket becomes the common path in mixed pools.
- **Implication:** the WebSocket path must not be second-class in tests or logs. This converges with CM-G's mixed-pool test.

**E-C (contrarian) — the "Telegram tightens the web door" trend:** origin checks, rate limits, a web-only `api_id` policy.
- **The risk:** refusals may arrive as *RPC errors on `initConnection`*, not transport errors. By F3, an RPC error with code 401, 403, 406 or 420 that is not in the table becomes a health **`unclassified`** event. A door-policy refusal could therefore look like an account problem.
- **Implication:**
  - P7 records any RPC error seen only under `websocket`;
  - P6 tells operators to compare against `tcp` before reading a health event as an account verdict.

---

## Inherited Frame Audit

**Seed-level central assumptions:**

**(a) "The transport is an in-process `ConnectionTcpObfuscated` subclass."** Challenged by I-E (bare `Connection`) and CM-F (own tunnel). For the shape itself, the relay, monkeypatch and SOCKS shim were tested in sensemaking A1.
- `Inherited-Frame-Audit-marked-inapplicable` for any *further* shape: Telethon 1.45.0 exposes exactly one in-process transport seam. `TelegramBaseClient.__init__` asserts `isinstance(connection, type)` (`telegrambaseclient.py:351`), and `_proxy_connect` accepts only a dict or tuple proxy, raising `TypeError` otherwise (`connection.py:107–112`). So no socket-factory injection point exists.
- **Structural reason:** a single seam.
- **Contextual reason:** sensemaking A1 tested the three out-of-seam shapes and killed them on that seam.

**(b) "The default path is byte-identical."** Challenged by nothing, and strengthened by L-C.
- `Inherited-Frame-Audit-marked-inapplicable`: the maintainer's explicit requirement ("without harming … keep it that way", `_branch.md` Source Input; MQ4's first exclusion). It is a constraint the user set, not an inference the loop made, and challenging it would leave the brief.

**Piece-level commitments (decomposition):**

| Piece | Load-bearing commitment | Challenged by |
|---|---|---|
| P0 | the taxonomy by base class | I-D (an attribute) |
| P1 | hand-written, Telethon-free | E-G (confirms); a library alternative killed in A9 |
| P2 | the fixed planet map, no override | I-G (a formula), I-F (rotation), CM-C (a constrained override) |
| P3 | the observability additions | L-F (Telethon already logs it) |
| P4 | the binding entry only when non-default | C-F (a helper), DT-F (confirms) |
| P5 | a real TLS server harness | DT-G (inject at the seam) |
| P6, P7 | docs; a live run | E-C (door-policy errors) |

**The audit does not fire:** every commitment has at least one explicit challenge.

---

## Phase 3 — Test (novelty · scrutiny · fertility · actionability · mechanism-independence)

Test columns, in order: N = novelty, S = scrutiny, F = fertility, A = actionability, MI = mechanism independence.

| ID | N | S | F | A | MI | Disposition |
|---|---|---|---|---|---|---|
| **L-G** naming via `super().__init__` | med | **passes** — the base stores `_ip`/`_port` from its arguments; nothing else differs | low | high | DT-C reaches the same "constructor decides" point | **ACTIONABLE** |
| **L-F** Telethon's log is the runtime record | high | **passes** — F1 verified in the source | med | high | AR-P1 converges | **ACTIONABLE** (docs, plus a reduced P3) |
| **L-C** lazy import | med | **passes** — at most one import line in the branch; no cycle, since the module imports Telethon, not `connection_engine` | low | high | single | **DEFERRED → ACTIONABLE if** P3's module layout puts the class outside `connection_engine.py`. Revival: plan-time layout choice. |
| **C-G** opener refuses IP literals | med | **passes** — one `ipaddress` call; Telegram's door names are never IPs | med | high | DT-C converges | **ACTIONABLE** |
| **C-F** network-identity helper | low | **fails** — one field today; a helper for one entry is speculative generality | — | — | — | **KILL**, becomes a seed: revisit when a second network setting joins the binding |
| **C-C** web clients' codec | med | **fails** — which codec the web clients use is unverified, and the fingerprint (R6) is dominated by `api_id` and device fields in `initConnection`, not the codec | — | — | — | **RESEARCH FRONTIER** — only a live comparison could show any effect |
| **I-G** the formula `kws{N}` / evidence-equal families | high | **partly passes** — the formula works for DC 1–5 (F4). Which family Telegram keeps is unknown either way. The second-order finding (A3/A14's justification doesn't apply to the names used) **survives**. | high | med | I-F leans on the same fact | **RE-TEST TRIGGER** on A3/A14: the planet choice must be re-justified, or the formula considered |
| **I-F** name rotation on reconnect | high | **contested** — "never an IP" is kept. But on strict clients (no reconnect, `connection_retries=0`) rotation never happens. On ordinary clients it turns one name's outage into retries that look healthy. Telethon's `connection_retries` loop calls `connect()` on the same object, so rotation does work there. | med | med | single | **DEFERRED** — revival trigger: one family fails while the other works (P7, or the probe later) |
| **I-C** no `Origin` | med | **untested** — cheap to settle with the existing probe (`--no-origin`, no account). Sending `Origin` is harmless if needed; omitting it is more honest if not. | low | high | single | **ACTIONABLE as an experiment** (probe run before P1's header list is final) |
| **I-D** taxonomy by attribute | low | **fails structurally** — invisible to `_try_connect` and `_failure` | — | — | — | **KILL** (confirms P0) |
| **I-E** bare `Connection` plus own obfuscation | low | **fails** — duplicates `ObfuscatedIO`, about 60 lines of AES-CTR setup, for no gain | — | — | — | **KILL** (confirms reuse) |
| **CM-G** stateless class, mixed-pool test | high | **passes** — one class per process, per-call `connection=`, `_client_class` cached only by base (verified in the warm reading) | med | high | E-F converges | **ACTIONABLE** |
| **CM-F** own the tunnel via python-socks | med | **fails** — by F2, Telethon's `_proxy_connect` converts python-socks' errors to `ConnectionError`, which is what makes them retryable `IOError`s. Owning the tunnel would either re-implement that mapping or depend on Telethon having patched python-socks *globally, earlier* (order-dependent). Reusing the private method is the smaller dependency. | — | — | — | **KILL**, and **strengthens** P2's reuse; add `_proxy_connect`'s error mapping to the P5 canary |
| **CM-C** constrained host override | med | **fails on cost** — a per-config class factory (K-I7) for an unobserved event; the constrained form removes the arbitrary-host risk, but not the machinery | — | — | — | **DEFERRED** — revival trigger: the door renames a host, or one family fails (shared with I-F) |
| **AR-P1** a runtime record of destinations | — | absorbed by L-F | — | — | — | merged into L-F |
| **AR-P2** health non-interaction test | high | **passes** — F3 verified; the test pins today's behaviour | med | high | E-C touches the same seam from the other side | **ACTIONABLE** |
| **AR-R** a `NetworkRoute` object | — | collapses to `ConnectionConfig`, which is SV6 | — | — | — | **KILL** (confirms SV6) |
| **DT-G** inject at the seam in tests | med | **passes** — P1's interface is a natural fake point; one real-TLS test is kept | med | high | single | **ACTIONABLE** |
| **DT-F** the transport's name in messages | low | **passes**, trivially | low | high | confirms A8 | **ACTIONABLE** (minor) |
| **DT-C** the constructor ignores `ip` | med | **passes** — the same as L-G, viewed as safety | — | — | — | merged into L-G |
| **E-G** keep P1 Telethon-free | low | **passes** — already in decomposition; promoted to a rule | low | high | — | **ACTIONABLE** (a rule in the plan) |
| **E-F** WebSocket as first-class | — | merges into CM-G | — | — | — | merged |
| **E-C** door-policy refusals look like account problems | high | **passes as a concern** — F3 shows the path. Not observable offline. | high | med | single | **DEFERRED** — revival trigger: P7 sees any RPC error only under `websocket`. Docs note now (P6). |

---

## Assembly check

**What emerges when the survivors are combined: a four-layer "never an IP", where each layer is one line or one test.**
1. **The object** (L-G + DT-C): the constructor passes the host name to Telethon's own `__init__`, and ignores the IP it was handed. The object never holds an IP.
2. **The opener** (C-G): `open_websocket` refuses an IP literal. The lowest layer cannot dial one.
3. **The proof** (P5 + CM-G + DT-G): recording-proxy tests on every construction path, including a mixed `tcp`/`websocket` pool, with most cases at the injected seam and one real-TLS case.
4. **The runtime evidence** (L-F): Telethon's own INFO line, `Connecting to <host>:443/…`, which the docs name as the operator's check. No new runtime code is needed.

No single survivor gives this. Together they move the guarantee from "a property we tested" to **"a property the code cannot violate, with a test and a log line that show it"**. It costs about three lines of production code beyond SV6.

**A second emergent point: SV6 gets *smaller*, not bigger.**
- L-F reduces P3's observability work.
- CM-F's kill confirms the private-surface choice.
- L-G removes private attribute writes.
- AR-R and I-E confirm that no new object or codec is needed.

The innovations harden the design without adding a concept, which is the maintainer's elegance criterion.

**Axis-coverage check:**

| Axis | Candidates |
|---|---|
| shape | I-E, CM-F, audit (a) |
| naming source | I-G, I-F, CM-C |
| taxonomy | I-D, DT-F |
| binding | C-F, DT-F |
| observability | L-F, AR-P1 |
| tests | DT-G, CM-G, AR-P2 |
| packaging | L-C, E-G |
| wire headers | I-C, C-C |
| cross-feature (#4 health) | AR-P2, E-C |

Every axis has a variant.

**Per-element mechanism trace (P0–P7):**

| Piece | Candidates |
|---|---|
| P0 | I-D, DT-F |
| P1 | C-G, I-C, E-G |
| P2 | L-G, I-G, I-F, CM-C, CM-F, I-E |
| P3 | L-F, L-C |
| P4 | C-F, DT-F |
| P5 | DT-G, CM-G, AR-P2 |
| P6 | L-F, E-C |
| P7 | I-C, I-F, E-C |

None is untouched.

**RE-TEST TRIGGER, raised for Critique:** sensemaking's A3/A14 justified planet names as "the superset that worked". By F4, both families worked for every name the design dials. The choice between `<planet>` (a map) and `kws{N}` (a formula) is therefore evidence-equal, and must be decided on other grounds:
- readability of logs;
- which family is more likely to persist — unknown;
- zero table vs five-entry table.

**For Critique — the candidates carried forward:**
- **ACTIONABLE:** L-G, L-F, C-G, CM-G, AR-P2, DT-G, DT-F, E-G.
- **Experiment:** I-C.
- **RE-TEST:** I-G (on A3/A14).
- **DEFERRED:** L-C, I-F, CM-C, E-C.
- **RESEARCH FRONTIER:** C-C.
- **KILLED** (each confirming an SV6 choice): C-F, I-D, I-E, CM-F, AR-R.

---

## Telemetry

- Generators applied: **4 / 4** — Combination, Absence Recognition, Domain Transfer, Extrapolation.
- Framers applied: **3 / 3** — Lens Shifting, Inversion (depth- and existence-axis checked), Constraint Manipulation (ADD: CM-G; REMOVE: CM-F, CM-C).
- Convergence: **YES.**
  - "never an IP by construction" — L-G, DT-C, C-G: 3 mechanisms;
  - "mixed pool / WebSocket first-class" — CM-G, E-F;
  - "observability already exists" — L-F, AR-P1.
  - **Shared-input check:** L-G and C-G rest on different grounds — Telethon's constructor vs the `ipaddress` module — so the convergence is independent, not spurious.
- Survivors tested: **23 / 23** (5 merged into other candidates).
- Failure modes observed: none.
  - **Survival bias** was checked: the most uncomfortable candidates — I-G (it undercuts a sensemaking justification) and E-C (the door could misfire #4's health) — were kept, not killed.
  - **Early frame lock** was checked: the central shape was challenged twice.
- **Overall: PROCEED.**
