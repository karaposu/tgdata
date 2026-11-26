---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

/Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/_branch.md + /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/surfacing.md + /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/articulate_simple.md — SAVE the output as /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/articulate_warm.md

---

# Warm articulation — issue #67 (round 0)

**Inputs:**
- the task statement;
- the cold bundle, `articulate_simple.md` — its answers are constraints;
- the surfaced material, `surfacing.md` with `../triage.md` as its prior artifact — information.

**Substrate:** received, not fetched.

## Carried unchanged — class (a)

- **Itemize:** count 1, item `I1`.
- **Deconstruct:**
  - **deliverable:** a decided meaning-and-shape for `transport = websocket`;
  - **kinds:** decisions on the ten open points, a concern register, a test strategy, doc corrections;
  - **bounds:** tgdata 0.1.4 on Telethon 1.45.0; the connection seam and its consumers; the default unchanged; no implementation.
- **MultiDepth literal:** as in the cold bundle.

## MQ2 — re-anchored (the committed context-need)

The task bears on these project facets, and only these:
1. **Telethon 1.45.0's connection lifecycle**, the layer the transport lives in:
   - the `connection=` constructor argument, special-cased only for `TcpMTProxy`;
   - `Connection.__init__(ip, port, dc_id, …)` and `_connect` / `_proxy_connect` (`dest_host = _ip`);
   - `ConnectionTcpObfuscated` / `ObfuscatedIO`, which need only a reader and writer pair;
   - `MTProtoSender._try_connect`, which retries `IOError` / `TimeoutError` only and then raises a fresh, unchained `ConnectionError`;
   - `_reconnect`, which reuses the same connection object and does zero attempts when `auto_reconnect=False`;
   - the four construction sites, all passing `dc_id` through the class;
   - `_keepalive_loop`, started on every connected client, strict clients included.
2. **tgdata's single door and its config:**
   - `_load_config` → `ConnectionConfig`, with `ProxyConfigError(ValueError)` raised at config time;
   - `parse_proxy_url` with `rdns: True`;
   - `_new_client` and its `**client_options` seam, used by `ephemeral_client`, `_account_operation`, `LoginFlow` (`_client_base=_LoginClient`) and `_OwnedSource`.
3. **The consumer contracts** that read connection behaviour:
   - the strict options — `connection_retries=0`, `auto_reconnect=False`, `receive_updates=False`;
   - `LoginFlow`'s binding SHA-256 over api id, api hash, proxy, `require_proxy` and identity, with `docs/stepwise_login.md:90`;
   - `AccountPool._failure`: `ValueError` → unknown (stop), `ConnectionError` → transport (retry);
   - the exact Telethon 1.45.0 pin in `AccountPool` and `Worker` only.
4. **The prototype and its evidence:** `ws_door_probe.py`'s `WsReader`, `WsWriter`, `open_tunnel`, `open_websocket` and `WsConnection`, plus the live results — the planet names, the idle cut between 150 and 300 s.
5. **What must stay true or be corrected:**
   - the README's proxy section;
   - `connection_engine.py:154`, "remote DNS is moot";
   - `test_14`'s internals-canary convention;
   - `test_12`'s recording relay;
   - `test_13`'s stand-in patch point;
   - `setup.py`'s single `proxy` extra.

**Material-change judgment.** The committed anchor names exactly the territory `surfacing.md` and `triage.md` covered. RFC 6455 and Telegram's transport page are external, and already embodied in the tested prototype. **Unchanged, so this is a fixpoint. No re-surface.**

## Re-runs — class (b), trigger-gated

**MQ4 (boundary) — re-run; the context moved it.** Identified-ambiguities-list — the exclusions the surfaced reality adds to the cold NOT-list:
- **[default byte-identical extends to the login binding]** — adding `transport` to `LoginFlow`'s hash unconditionally would invalidate every existing checkpoint. Whether "default unchanged" covers the binding hash is now an identified boundary.
- **[the relay alternative meets the MTProto-proxy exclusion]** — an out-of-process relay of the kind the brief cites speaks the MTProto proxy protocol, which `parse_proxy_url` refuses and #67 excludes. Whether that rules the shape out entirely, or only that protocol, is identified, not decided.
- **[reliance on Telethon internals]** — the prototype overrides `_connect` and reads `_ip`, `_reader` and `_writer`. Whether relying on internals is allowed without a canary is an identified boundary.
- **Carried from the cold pass:** no default-TCP change; no fallback; no MTProxy; no secrets; latest Telethon only; no implementation here.

**MQ1 (verdict) — re-run; the context moved it.** Identified-ambiguities-list:
- **[settled by the code vs still a choice]** — surfacing settled facts behind points 3 and 4: the keep-alive runs on strict clients, strict clients never reconnect, and only `IOError` is retried. Whether the inquiry should restate those as decisions, or treat them as given and decide only what remains, is open.
- **["elegant", narrowed]** — the joint elegance criterion now has concrete measures: how many existing seams are touched (`_load_config`, `_new_client`, the binding, docs), whether consumers change at all, and whether the existing fail-fast-by-type pattern is reused.
- **Carried:** decision vs map; "concerns not yet realised" — register, constraints or blockers.

**MQ3 (intent, WHAT) — re-run; the context moved it.** Identified-ambiguities-list:
- **[where the generality lives]** — Telethon's `connection=` argument is already a general seam. "A minimal addition vs a general seam" becomes: a config value mapped to one class, or a small registry of transports.
- **[the error taxonomy as an end point]** — express it through exception types, which Telethon's retry and the pool's classification already read; or through new tgdata error classes; or both.
- **Carried:** the end point (decide vs evaluate whether to build); the action end points; concern handling.

**MultiDepth-WHY — not re-run.** The surfaced material did not move the motivations: operational, stewardship, safety, vendor, process, discovery are carried as in the cold bundle.

**MQA — re-run (three operations re-ran).**
- **Reconcile.** MQ1's "elegant, narrowed" and MQ3's "where the generality lives" fold into the joint **elegance criterion**, now concrete: the seams touched, consumer change, pattern reuse, and generality via Telethon's own `connection=`.
- **Reconcile.** MQ3's "error taxonomy via exception types" and MQ4's "reliance on Telethon internals" share an axis: **how much of Telethon's behaviour the design leans on** — its retry types, its private connection hooks.
- **Surface.** MQ1's "settled by the code vs still a choice" and the carried "decide vs evaluate whether to build" remain an irreducible overlap.

## Conflict-detection — class (c)

Identified-conflicts-list:
- **C1 — "the Telethon==1.45.0 pins" vs reality.** The request lists the pins among elements to keep, as if all of tgdata were pinned. In reality only `AccountPool._preflight` and `Worker.__init__` refuse a Telethon other than 1.45.0. `setup.py` and plain `TgData` accept `>=1.45,<2.0`. A transport that leans on Telethon internals would therefore run unpinned under plain `TgData`.
  - **Severity: resolvable by re-anchoring.** Re-anchor onto the reality: the pin is partial. The design must decide how a transport relying on internals is guarded under plain `TgData` — an exact-version guard, a canary test, or both. Which side is right is not decided here.

No other conflicts. The surfaced reality supports every other premise:
- the connection-class shape;
- by-name proxying through `rdns`;
- planet names for every DC;
- no change needed to Telethon's DC switching;
- the request-seam mixins above the transport.

The binding-hash point is a gap the design fills, not a contradiction.

**Flag:** `content-conflict` — **resolvable (MED-FLAG)**. No clarifying question is formulated, because it is not severe.

## Rephrase — refreshed considered articulations (in project vocabulary)

Bounded by:
- Deconstruct's shape — a decided meaning-and-shape;
- the identified ambiguities — the elegance criterion, the settled-vs-choice overlap, the taxonomy and internals reliance, the WHY set;
- MQ4 — no default change including the binding hash, no MTProxy, no fallback, no implementation;
- the warm substrate.

The articulations:
1. **The minimal-change design.** One `transport` key in `[Telegram]` read by `_load_config`, and one `connection=` value passed by `_new_client`, pointing at a `ConnectionTcpObfuscated` subclass that maps `dc_id` to a planet name. Nothing else changes: not the consumers, not the mixins, not the strict options. Settle the remaining open points against that.
2. **The pattern-fit design.** Reuse tgdata's existing patterns end to end:
   - fail-fast by exception type — configuration errors as `ValueError` subclasses at config time, transport errors as `ConnectionError` for Telethon's retry and the pool's `transport` class;
   - one door;
   - credential-free messages;
   - a canary test in the style of `test_14`.

   Decide the DC map's home, the binding and the docs by the same rule.
3. **Concern-first.** Enumerate what the transport could break or hide:
   - Telethon replacing the transport's error with an unchained `ConnectionError`;
   - the login binding hash;
   - plain `TgData` running unpinned on internals;
   - the trust store's availability;
   - the false "remote DNS is moot" comment;
   - the `-1` names;
   - the outside-world risks.

   Decide a design that closes or routes each one.
4. **Map, then choose.** Compare a `Connection` subclass inside the client with an out-of-process relay — now known to require the excluded MTProto-proxy protocol or a tunnel tgdata does not own — and with any other shape, against the elegance criterion. Choose, and record the trade-offs.
5. **Specific vs general.** Decide whether `transport` takes exactly two values (`tcp`, `websocket`) mapped to Telethon connection classes, or a small registry of transports — given that Telethon's `connection=` already supplies the general seam.
6. **Build or not.** Decide the design, and whether its residual outside-world risks justify building it against a provider that allows IP targets. The code-side risks are now shown to be small.

## Self-assessment

**Inherited LAYER 1 self-check (light pass):** no fires.
- 2-shape held at every re-run;
- the WHAT/WHY axes are kept apart;
- every variant stays in bounds;
- no required field is missing.

**Warm-specific modes:**
- **false-positive conflict:** no — C1 is a real premise-vs-reality mismatch, not a gap;
- **crying-wolf:** no — graded resolvable, not severe;
- **adjudicate-instead-of-identify:** no — C1 names the mismatch without deciding;
- **ignore-the-trigger:** no — WHY was not re-run, because it did not move.

**Loop:** round 0 → fixpoint (unchanged anchor); 0 re-surfaces.

**Verdict: MED-FLAG** — `content-conflict`, resolvable (C1: the Telethon pin is partial, not universal).
