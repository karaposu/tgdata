---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

/Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/_branch.md — inputs also in that folder: articulate_simple.md, surfacing.md, articulate_warm.md, sensemaking.md (SV6), decomposition.md (P0–P7), innovation.md (candidates: ACTIONABLE L-G, L-F, C-G, CM-G, AR-P2, DT-G, DT-F, E-G; experiment I-C; RE-TEST I-G on A3/A14; DEFERRED L-C, I-F, CM-C, E-C; RESEARCH C-C; killed C-F, I-D, I-E, CM-F, AR-R). Evaluate the SV6 design plus these candidates against the maintainer's elegance criterion (fewest seams touched, most reuse, no harm to the existing design) and the fail-closed guarantee; produce SURVIVE / REFINE / KILL verdicts and the final assembled design for desc.md/plan.md. SAVE the output as /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/critique.md

---

# Critique — the #67 WebSocket transport: SV6 and the innovation candidates

**External anchors gathered for this pass:**
- **X1 — Telethon 1.45.0 source, read directly.** Every Telethon claim below cites a file and line.
- **X2 — the CDN client builds its connection with the parent's class.** `_get_cdn_client` calls `client._sender.connect(self._connection(session.server_address, session.port, session.dc_id, …))` (`telegrambaseclient.py:931–938`), so a CDN DC number would reach the transport's `__init__`. Nothing in `telethon/client/` sets `cdn_supported` (grep: no hits), so the path is not reachable today. If it ever became reachable, an unmapped CDN DC would fail fast, not dial an IP.
- **X3 — an independent client library (gotd/td, `telegram/dcs/prod.go`)** hard-codes the same five planet names for DC 1–5 over `wss://…/apiws` (web search, 2026-11-26). Telegram's own docs say `help.getConfig` returns DC **IPs** that may change, and publish no WebSocket names.
- **X4 — the probe record on issue #67:**
  - every `<planet>` and `kwsN` name for DC 1–5 worked;
  - `kws2-1` and `kws4-1` failed MTProto;
  - idle connections were alive at 150 s and cut by 300 s;
  - `Origin` was sent on every recorded run.

---

## Phase 0 — Dimensions

| # | Dimension | Weight | Success criterion — substance-level where it is load-bearing |
|---|---|---|---|
| D1 | **Fail-closed** — never an IP, no fallback | **critical** | Following the code literally on every construction path (main, exported, reconnect, CDN), no IP literal can reach a socket call. Any unknown DC is an error. |
| D2 | **No harm to the existing design** — the user's anchor, "keep it that way" | **critical** | With `tcp` or no key, the `TelegramClient` kwargs, log text, binding hash and consumer code are unchanged. No change to the mixins, the strict options, `StoredSession` or `_failure`. |
| D3 | **Correct against Telethon 1.45.0** | **critical** | Every behaviour the candidate relies on is shown in Telethon's source (X1), not inferred. |
| D4 | **Elegance** — fewest seams, most reuse | high | The number of existing functions edited, and no new concept Telethon already provides. |
| D5 | **Cross-feature and account safety** — project-specific risk: #4 health, `LoginFlow` binding, pool classification | high | No new health verdicts from transport faults, the binding is correct, and pool outcomes follow the existing types. |
| D6 | **Evidence grounding** | high | Live facts cite X3 or X4. Facts not yet observed are routed to P7, not assumed. |
| D7 | **Robustness to change** — Telethon patch releases, the door changing | medium | Breakage is loud, local to WebSocket users, and caught by the canary. |
| D8 | **Diagnosability** | medium | The operator can tell which transport is in use and why it failed, without credentials in the text. |
| D9 | **Testability** | medium | It can be proven offline, except for the calibration (P7). |

**Validation:**
- Every sensemaking perspective has a dimension:
  - Technical → D1, D3;
  - Human → D8;
  - Strategic → D7;
  - Risk → D1, D5;
  - Resource → D4, D9;
  - Definitional → D2;
  - Calibration → D6.
- The axis-absence sub-checks:
  - (i) every hidden coupling found by decomposition and innovation — the receive-loop exception rule, the reader/writer ordering, the SSL seam, health, the mixed pool — sits under D3, D5 or D9;
  - (ii) "no harm" takes its broadest sensible reading: behaviour, *and* structure, *and* the consumers;
  - (iii) no dimension's wording performs the violation it tests.

**Frame-premise test** — the inherited premises of SV6, each with a what-if-wrong prosecution:
- **FP1 — "a `ConnectionTcpObfuscated` subclass is the only in-process shape."**
  - *If wrong:* some lighter seam exists.
  - *Evidence against wrongness:* `isinstance(connection, type)` (`telegrambaseclient.py:351`); a proxy may only be a dict or tuple, and anything else raises `TypeError` (`connection.py:107–112`).
  - **Holds.**
- **FP2 — "the planet map is the right naming source."**
  - *If wrong:* the formula `kwsN` is better, or names should come from Telegram.
  - Telegram publishes only IPs (X3: `help.getConfig`), so "names from Telegram" is impossible. Planet vs `kws` is evidence-equal on the probe (X4). The tie-breaker is X3: an independent client uses planets.
  - **Holds, with a corrected justification** — see I-G.
- **FP3 — "Telethon's keep-alive covers the idle cut."**
  - *If wrong:* connections die at 150–300 s.
  - Source: `_keepalive_loop` pings every 60 s on every connected client (`updates.py:516–545`). Exported senders get no ping but are closed after 60–120 s idle (`_DISCONNECT_EXPORTED_AFTER = 60`, checked each tick).
  - **Holds.** The live confirmation is in P7.

---

## Phase 1 — Fitness landscape

**Viable region** — D1, D2 and D3 all pass:
- in-process, inside Telethon's seam;
- the IP discarded at construction;
- names only from a fixed set that external clients use too;
- taxonomy by base class;
- consumers untouched.

**Dead region** — any of:
- **a fallback of any kind to TCP or an IP** (D1 fatal);
- **any change on the TCP path's kwargs or binding** (D2 fatal);
- **anything Telethon's readers cannot see**, such as attributes instead of types (D3 fatal);
- **out-of-process relays** — they need the excluded MTProto-proxy protocol (D2 fatal, and out of scope).

**Boundary region:**
- configurability of names: an override, or rotation;
- header choices: `Origin`;
- observability scope: the health field vs logs only.

Viability here trades D4 and D7 against D1 and D6.

**Unexplored region:** the transport's behaviour under Telegram's *policy*, as opposed to its protocol — rate limits, `api_id` checks over the web door. It cannot be explored offline, so it goes to P7.

---

## Phase 2–3 — Adversarial evaluation and verdicts

### S0 — The SV6 core: subclass, named at construction, one key, one door branch, conditional binding, taxonomy by base class

**Prosecution.**
- **User-perspective:** "without harming" — the change still edits `_load_config`, `_new_client`, the route log line, `health_check()` and `LoginFlow`'s binding. That is five places in three modules, plus a new module. Is that minimal?
- **Failure case:** the door is renamed. Every WebSocket account then fails at the proxy's DNS. That is a `ConnectionError`, so it is transient: the pool cools sources down and retries indefinitely rather than stopping.
- **Specification gap:** what does `_new_client` do if a caller already passes `connection=` in its client options? A duplicate keyword gives a `TypeError`.

**Defense.**
- **Each of the five edits is the narrowest possible at its site,** and four of the five are one or two lines. No consumer, mixin, strict option or `_failure` line changes. No call site passes `connection=` today: tgdata never sets it (grep), and `_OwnedSource` adds only the strict options.
- **The renamed-door case is loud, not silent:** WARNING lines name the host on every attempt (X1: `mtprotosender.py:245`). It is also not a safety failure, because nothing goes by IP. "Retry while the door is down" is the right behaviour for an outage, and a rename is indistinguishable from an outage at first.

**Collision.** The defense holds on D1–D3. The renamed-door case is a D8 caveat: an outage and a rename look alike, so the docs must tell operators what a door change looks like.

**Verdict: SURVIVE.** Caveat: D8 docs (P6).

### L-G — Pass the host name to Telethon's own `Connection.__init__`, and ignore the IP

**Prosecution.**
- Overriding `__init__` with Telethon's exact keyword set (`loggers`, `proxy`, `local_addr`) couples the class to that signature. A 1.x patch adding a keyword would break construction.

**Defense.**
- Forward with `*args`/`**kwargs` and replace only the first two positionals. The base then stores `_ip` and `_port` itself (`connection.py:36–38`, verified), and the class writes no private attribute.
- This is the structural form of "never an IP": the object never holds one.

**Collision.** Forwarding `**kwargs` removes the coupling.

**Verdict: SURVIVE**, refined: `__init__(self, ip, port, dc_id, **kwargs)` calls `super().__init__(host_for(dc_id), 443, dc_id, **kwargs)`.

### L-F — Telethon's own INFO line, `Connecting to <host>:443/…`, is the runtime evidence

**Prosecution.**
- It is evidence only where logging is on. `Worker` disables logging, and operators may silence Telethon.
- So L-F cannot *replace* `health_check()["transport"]`, as innovation half-suggested.

**Defense.**
- It costs nothing, and it shows each connection's actual target, which no tgdata field can.

**Collision.** Both stand. The log line is per-connection evidence; the health field is a per-instance statement that works without logging.

**Verdict: SURVIVE, scoped to the docs (P6).** The README names the log line as the operator's check, and P3 keeps the `transport` field in `health_check()`.

### C-G — `open_websocket` refuses an IP-literal host (fail-fast)

**Prosecution.**
- It is redundant with L-G — the class already never passes an IP — and it is extra code for a case that cannot happen.

**Defense.**
- It is two lines. It protects P1 as an independently usable unit, including the tests and any future caller.
- It makes the guarantee hold at the lowest layer that opens a socket. That matters precisely because the failure it guards against is *silent* (triage).

**Collision.** Low stakes, so the burden is on the prosecution, which shows only redundancy, not harm.

**Verdict: SURVIVE.**

### CM-G — The class holds no shared state; add a mixed `tcp` + `websocket` pool test

**Prosecution.**
- Every test is cost, and per-engine configuration already guarantees separation.

**Defense.**
- The guarantee is per *call* (`connection=` passed in `_new_client`), and `_client_class` is cached by base only. That is correct today, but nothing *tests* it.
- A future refactor that caches clients by base plus options, or that sets `connection` on a class, would mix transports silently. The mixed pool is the realistic deployment.

**Verdict: SURVIVE.**

### AR-P2 — Pin that the P0 classes yield no health verdict (`classify(...) is None`)

**Prosecution.**
- It tests today's `health.classify`, which already returns `None` for these errors (`health.py:180–220`). So the test is a tautology.

**Defense.**
- It pins a cross-feature *interface* that decomposition missed. A future health change, for example "unclassified for unknown exceptions", would otherwise start emitting account-level noise during a door outage.

**Verdict: SURVIVE.**

### DT-G — Test mostly through the seam (a fake `open_websocket`), plus one real-TLS test

**Prosecution (specific failure case).**
- If the fake is injected *below* `_proxy_connect`, the no-IP tests stop exercising the proxy tunnel, and so stop proving the guarantee.

**Defense.**
- P2 calls `_proxy_connect` *before* `open_websocket`. A fake at P1's interface still sends every tunnel request through the recording proxy, so the destination record stays real.

**Verdict: SURVIVE**, with a constraint for P5: fakes replace only `open_websocket` (TLS plus WebSocket), never the tunnel. At least one test runs the real TLS server end to end through the recording proxy.

### DT-F — Name the transport in P0's messages

**Prosecution:** cosmetic.
**Defense:** it removes ambiguity in logs where TCP and WebSocket accounts share a process (CM-G).
**Verdict: SURVIVE** (minor).

### E-G — Keep P1 free of Telethon imports, as a rule in the plan

**Prosecution:** decomposition already says so.
**Defense:** it turns a description into a rule the critic and reviewer can check, and it bounds a Telethon 2.x port to P2's glue.
**Verdict: SURVIVE.**

### L-C — Import the transport module lazily, in `_new_client`'s `websocket` branch

**Prosecution.**
- Import cost and side effects are nil, since the module imports only the standard library and Telethon's own public connection classes. "Byte-identical" is about behaviour, which an import does not change.
- A lazy import also hides import errors until first use.

**Defense** — robustness, D7, not byte-identity.
- Plain `TgData` accepts Telethon `>=1.45,<2.0` (warm conflict C1). If a 1.x release moved or renamed something the module imports at the top level, a *top-level* import would break **every** tgdata user, TCP included.
- A lazy import confines any such breakage to WebSocket users: the existing design stays unharmed even when the new transport is broken.
- The prosecution's "hidden errors" are caught by the canary and the WebSocket tests anyway.

**Collision.** The defense wins on the user's own anchor: "without harming … the existing design".

**Verdict: SURVIVE**, promoted from DEFERRED. The reason is blast-radius isolation, not import cost.

### I-C — Is `Origin: https://web.telegram.org` needed? (an experiment)

**Prosecution against dropping it.**
- Every browser sends `Origin` on a WebSocket. A client without one is *more* anomalous at the door, not less.
- The recorded runs all used it (X4).

**Prosecution against keeping it.**
- It asserts that the request comes from a page on web.telegram.org, which it does not.

**Defense of the experiment.**
- One no-account probe run (`--no-origin`) settles whether the door *requires* it. Either answer is cheap to act on.

**Collision.** This is a low-stakes boundary choice. Keep the tested configuration as the default, and settle "required?" empirically.

**Verdict: REFINE** — as a P7 / pre-P1 observation, not a design change.
- **Target:** one header constant in P1.
- **Rule:** if all five DCs work without `Origin`, the plan may drop it. Otherwise keep it, and record why in the code comment.
- **Who:** the run uses the network and the proxy, so it happens on the maintainer's go.

### I-G — The formula `kws{N}` vs the planet map (RE-TEST of A3/A14)

**Re-test result.**
- Sensemaking's justification ("the superset that worked") is **void** for the names used (X4).
- A new justification exists: an independent library uses the same planet map (X3), and planet names read clearly in logs. A five-entry immutable constant costs nothing over a formula.
- The formula's only gain, "zero table", is not worth trading away the external convergence.

**Prosecution against the planet map.**
- X3 is one third-party library, not Telegram. Both families could be retired.

**Defense.**
- Both families are unpublished either way. The one with outside corroboration is the better bet.
- A change is one constant edit, plus the canary or live test.

**Verdicts:**
- the **planet map: SURVIVE**, with its justification corrected (X3 + X4, not "superset");
- the **formula: KILL.**
  - **Seed:** if Telegram ever publishes WebSocket names, through docs or config, derive names from that source instead of either family.

### I-F — Rotate between `<planet>` and `kwsN` on reconnect

**Prosecution (failure case).**
- Strict clients — owned operations, the pool, login — never reconnect (`connection_retries=0`, `auto_reconnect=False`), so for them rotation never happens.
- On ordinary clients it hides a family outage behind retries that look healthy.
- It doubles the names the guarantee and the tests must cover.

**Defense.**
- It gives resilience against one family's retirement, and it is still never an IP.

**Collision.** The prosecution wins on D4 and D8: it adds silent behaviour for a hypothetical event, and is ineffective on half the clients.

**Verdict: KILL.**
- **Seed:** if P7 or a later probe shows one family failing while the other works, the response is a one-constant change in a release, made visible, not silent rotation.

### CM-C — A constrained host override (`<label>.web.telegram.org` only)

**Prosecution.**
- It needs a class built per config (Telethon accepts only a class, `telegrambaseclient.py:351`) and a cache, for an unobserved event.

**Defense.**
- It lets operators follow a renamed door without waiting for a release.

**Collision.** tgdata is maintained in-repo, so a release is the override. The machinery cost is permanent; the benefit is hypothetical.

**Verdict: KILL.**
- **Seed:** the same revival trigger as I-F. If renames turn out to be frequent, revisit with evidence.

### E-C — Door-policy refusals could look like account problems in #4's health events

**Prosecution.**
- It is speculative, and nothing observed suggests it.

**Defense.**
- The mechanism is real. An RPC error with code 401, 403, 406 or 420 not in the table becomes `unclassified` (`health.py:88–90`). A door that refused, say, a desktop `api_id` with such an error would surface as an account-level WARNING.

**Collision.** It is not designable offline (an unexplored region), but it is cheap to *watch*.

**Verdict: SURVIVE, as a registered concern, not code:**
- the P6 docs say "compare against `tcp` before reading a health event under `websocket` as an account verdict";
- P7 records any RPC error seen only under `websocket`.

### C-C — Match the web clients' codec

**Prosecution.**
- There is no evidence of which codec the web clients use, nor that the codec contributes to the fingerprint. The `initConnection` fields dominate.

**Verdict: KILL.**
- **Seed:** if P7 shows web-door-specific refusals (E-C), the codec becomes one variable to test among several.

### Innovation's kills — re-checked for the accumulator

| Kill | Confirmed by |
|---|---|
| **CM-F** (own the tunnel) | `connection.py:114–126`: Telethon converts python-socks' errors to `ConnectionError` inside `_proxy_connect`. Owning the tunnel loses that conversion, or depends on its global, order-dependent side effect. **Add the conversion to the P5 canary.** |
| **I-D** (taxonomy by attribute) | `_try_connect` and `_failure` read only types. |
| **I-E** (own obfuscation) | It duplicates `ObfuscatedIO`. |
| **AR-R** (`NetworkRoute`) | It is `ConnectionConfig`. |
| **C-F** (identity helper) | One field needs no helper. |

---

## Phase 3.5 — Assembly check

**Assembly A* — SV6, hardened** (S0 + L-G + C-G + L-C + CM-G + AR-P2 + DT-G + DT-F + E-G, with L-F and E-C in the docs and I-C as an observation).

**Prosecution.**
- Does the hardening add up to more than the maintainer wants — eight additions on top of SV6?

**Defense** — count what actually lands in production code beyond SV6:
- the `**kwargs` forwarding in `__init__` (L-G);
- two lines refusing IP literals (C-G);
- one import moved into the branch (L-C);
- the transport's name in messages (DT-F).

Everything else is tests (CM-G, AR-P2, DT-G), a rule (E-G), or docs (L-F, E-C). The assembly's emergent property: **"never an IP" holds by construction at two layers and is proven on every path, and a broken transport can only ever affect WebSocket users.** No single candidate gives this.

**Collision.** The production delta is roughly six lines, so D4 is preserved, while D1, D7 and D2 strengthen.

**Verdict: SURVIVE** — ranked first.

---

## The assembled design (for desc.md / plan.md)

1. **Config (P3).**
   - `transport = tcp | websocket` in `[Telegram]`; absent means `tcp`.
   - It is normalised once in `_load_config` into `ConnectionConfig.transport`.
   - An unknown value raises a config-family `ValueError` before any socket opens.
   - It is independent of `proxy` / `require_proxy`; `websocket` without a proxy goes direct by name.
2. **The door (P3).** `_new_client` imports the transport class **inside** the `websocket` branch and adds `connection=<class>`. Nothing changes for `tcp`.
3. **The class (P2)** — a `ConnectionTcpObfuscated` subclass.
   - `__init__(ip, port, dc_id, **kw)` calls `super().__init__(<planet>.web.telegram.org, 443, dc_id, **kw)` using the fixed DC 1–5 map, which is corroborated externally. An unmapped DC (CDN, test or unknown) raises fail-fast.
   - `_connect(timeout, ssl)` gets a socket from `_proxy_connect` (Telethon's own; the name; errors already converted) or `None` for direct.
   - It then calls `open_websocket(host, sock=…, timeout=…)`, assigns `_reader` / `_writer`, and runs the base sequence: `_codec`, `_init_conn`, `drain`.
   - No other override.
4. **The stream (P1)** — `open_websocket`.
   - Telethon-free (a rule); the standard library only.
   - Refuses IP-literal hosts.
   - TLS uses `create_default_context()`, which can be injected for tests, with SNI set to the host. A certificate failure is fail-fast.
   - `GET /apiws`, `Sec-WebSocket-Protocol: binary`, and `Origin` — kept pending the I-C observation. A `101` and the accept hash are required; anything else is a transient `ConnectionError`.
   - Framing: masked binary frames out; binary and continuation frames joined into the stream; ping→pong; close or EOF becomes `IncompleteReadError`.
   - **After connect, it never raises anything except an `IOError` or `IncompleteReadError`.**
5. **The taxonomy (P0).**
   - **Fail-fast (`ValueError` family, tgdata's own class):** an unknown value, an unmapped DC, a certificate failure, an IP-literal host.
   - **Transient (`ConnectionError`):** a bad upgrade, resets, protocol violations, a server close. Proxy errors stay Telethon's own.
   - Messages carry the transport's name and the host, and no credentials.
   - No changes to `_failure` or `health`.
6. **The binding (P4).** `transport` is added to `LoginFlow`'s settings only when it is not `tcp`; the TCP hash is pinned by a test.
7. **Observability (P3, P6).**
   - The route line gains "over WebSocket by name" for `websocket` only.
   - `health_check()["transport"]`.
   - The README names Telethon's `Connecting to <host>:443` INFO line as per-connection evidence.
8. **Tests (P5).**
   - recording-proxy no-IP tests on every path, including the strict-option paths, plus a mixed `tcp` + `websocket` pool;
   - fakes only at `open_websocket`, plus one real-TLS end-to-end test;
   - one test per taxonomy class, through the real `_try_connect` and `_failure`;
   - the default byte-identical: kwargs, binding hash, log text;
   - the health non-interaction test;
   - **the canary:** the `Connection.__init__` signature, `_connect(timeout, ssl)`, `_proxy_connect` using `_ip` and converting python-socks' errors, `_init_conn` reading `_reader` / `_writer`, the four construction sites passing `dc_id`, `cdn_supported` never set.
9. **Docs (P6).**
   - the "remote DNS is moot" fix;
   - the docstrings;
   - the README section;
   - `stepwise_login.md`;
   - the risk register: the unpublished door; the desktop `api_id` over the web door; the relays' rate limits; one day's calibration; TCP-made keys proven only live; the trust store; a renamed door looks like an outage; door-policy errors may read as `unclassified` health events.
10. **Live (P7), on the maintainer's go.**
    - login, a read, and a download from another DC;
    - an existing session reused;
    - more than 300 s idle;
    - the `--no-origin` probe (I-C);
    - any RPC error seen only under `websocket` (E-C).

---

## Phase 4 — Coverage and convergence

**Coverage map.**
- **Viable — evaluated thoroughly:** the shape; naming; the taxonomy; the binding; observability; tests; packaging.
- **Boundary — settled:** the override (killed); rotation (killed); `Origin` (an observation).
- **Dead — confirmed:** fallbacks; relays; attributes as taxonomy; own obfuscation; own tunnel.
- **Unexplored — routed to P7:** the door's *policy* behaviour (rate limits, `api_id`).

**Accumulator (this loop's single iteration).**

| Verdict | Candidates |
|---|---|
| **SURVIVE** (12) | A*, S0, L-G, L-F (scoped), C-G, CM-G, AR-P2, DT-G, DT-F, E-G, L-C, E-C (as a concern) |
| **SURVIVE** with corrected justification | the planet map |
| **REFINE** (1) | I-C (an observation) |
| **KILL** (9) | I-G's formula, I-F, CM-C, C-C, plus innovation's C-F, I-D, I-E, CM-F, AR-R — confirmed with seeds |

**Mechanism-independence status: validated.** The survivors' evidence cites external anchors:
- Telethon's source (X1, X2);
- an independent client (X3);
- the live probe record (X4).

**Signal: TERMINATE.**
- A clean SURVIVE (A*) passes every critical dimension without caveats on them.
- New candidates landed in mapped regions: the innovation kills re-confirmed SV6's choices.
- The one unexplored region cannot be explored offline and is routed to P7.

**Ranked survivors:**
1. A*
2. S0 + L-G + C-G — the guarantee's core
3. L-C — blast-radius isolation
4. the tests: CM-G, AR-P2, DT-G
5. DT-F, E-G, L-F — docs and rules

---

## Convergence telemetry

- **Dimension coverage:** 9 dimensions — 3 critical, 3 high, 3 medium. All sensemaking perspectives are mapped, and the frame-premise test ran FP1–FP3.
- **Adversarial strength: STRONG.**
  - Prosecutions included the user-perspective case ("five edits"), concrete failure cases (a renamed door, strict clients never rotating, fakes below the tunnel) and a specification-gap probe (a duplicate `connection=`).
  - Two candidates changed disposition under collision: L-C was promoted on robustness, and I-G reversed sensemaking's justification.
- **Landscape stability: CHANGED once.** I-G corrected A3's grounds, but not its choice. It is stable otherwise.
- **Clean SURVIVE: yes** (A*).
- **Failure modes:**
  - **rubber-stamping:** no — four kills, and one premise justification reversed;
  - **nitpicking:** no — the caveats are scoped to docs;
  - **dimension blindness / axis absence:** health and the mixed pool were checked explicitly;
  - **external-grounding absence:** no — X1–X4 are cited;
  - **self-reference:** not applicable.
- **Output: PROCEED.**

Sources: [gotd/td `telegram/dcs/prod.go`](https://github-redirect.dependabot.com/gotd/td/blob/f1af1992aca6e6b92562892fb8a37316ddae4d8b/telegram/dcs/prod.go) · [Telegram — Working with Different Data Centers](https://core.telegram.org/api/datacenter) · [Telegram — Client configuration](https://core.telegram.org/api/config)
