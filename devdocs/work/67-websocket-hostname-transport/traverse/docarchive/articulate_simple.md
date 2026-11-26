---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

Issue #67 in karaposu/tgdata, branch feat/67-websocket-hostname-transport, worktree /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67 (all paths below are relative to it). Write all output to devdocs/work/67-websocket-hostname-transport/traverse/ (CONTRIBUTING.md §5: traverse output lives in traverse/ on the branch and becomes the raw material for desc.md). Inputs already on the branch: devdocs/work/67-websocket-hostname-transport/triage.md (feature-heavy; watch-for 1–8; frontier items), devdocs/work/67-websocket-hostname-transport/ws_door_probe.py (the no-account probe), devdocs/archaeology/intro2codebase.md and small_summary.md (warmed at 240a208), and issue #67's body + comments (probe results 2026-11-26: all five DCs work by planet name pluto/venus/aurora/vesta/flora incl. -1 names except kws2-1/kws4-1; every connection left from the proxy's assigned address with IP targets refused; idle tunnels survive 150 s, cut by 300 s; Telethon's full client pings its main connection every 60 s). The question: what is the most ELEGANT design for a per-account `transport = websocket` in tgdata — connect to Telegram's WebSocket door by hostname through the configured proxy (HTTP CONNECT / SOCKS remote DNS), TLS with SNI + verified certificate, GET /apiws with Sec-WebSocket-Protocol: binary, Telethon 1.45.0's obfuscated transport carried as a byte stream in binary frames, every DC by name, fail-closed (never an IP, no fallback to TCP), session files and device identity unchanged, the default transport byte-identical — WITHOUT harming or breaking the existing design, which the maintainer considers elegant and wants kept that way (the single client factory ConnectionEngine._new_client; the request-seam mixin stack _AnswerEvidence/JoinClientMixin/BudgetClientMixin/BatchHeartbeatMixin/_PerCallFloodThreshold; the fail-closed proxy guarantees; owned account operations with strict client options; StoredSession; LoginFlow's checkpoint binding; AccountPool's failure classification; the Telethon==1.45.0 pins). Also surface concerns not yet realised. Open points to settle or route: (1) the transport as a Telethon Connection subclass (ConnectionTcpObfuscated reused over a byte-stream adapter) vs other shapes; (2) where the DC→hostname map lives and whether it is configurable; (3) whether Telethon's 60 s _keepalive_loop runs on strict clients (receive_updates=False, auto_reconnect=False) and so covers the 150–300 s idle cut, or the transport must ping; (4) the error taxonomy — configuration vs transient transport failures, Telethon's connection_retries and AccountPool's 'transport' retry; (5) require_proxy × websocket and a websocket transport with no proxy; (6) whether the transport joins LoginFlow's binding; (7) a hand-written WebSocket client vs an optional dependency; (8) docs/comments that become false (connection_engine's 'remote DNS is moot'); (9) testing: offline fake TLS WebSocket server, a no-IP guarantee across every connect path including reconnect / exported senders / CDN, test_12's recording SOCKS relay; (10) the remaining outside-world risks (unpublished door, desktop api_id via the web door, relay rate limits, existing TCP-made login keys over the door). Telethon baseline: 1.45.0 (latest on PyPI; do not compare older versions). Consumers to keep in view: TgData, AccountPool, Worker, LoginFlow. Goal for the onward route-field (_branch.md): a stable, decided meaning-and-shape from which desc.md and plan.md for #67 can be written.

---
SAVE OUTPUT TO: /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67/devdocs/work/67-websocket-hostname-transport/traverse/articulate_simple.md

---

# Articulation (simple) — issue #67, the WebSocket transport

**Substrate:** warm. This session read tgdata 0.1.4's connection core and every client consumer in full while warming at `240a208`, and Telethon 1.45.0's network layer. That context is used to name the readings; it does not choose among them.

## Itemize

- **Count:** 1.
- **Item `I1`:** *"What is the most elegant design for a per-account `transport = websocket` in tgdata … without harming or breaking the existing design … Also surface concerns not yet realised. Open points to settle or route: (1)–(10)."*

**Why keep-together.** The ten open points and "surface concerns not yet realised" are facets of one design question: they settle or route parts of the same shape. Splitting them would produce bundles that cannot be read without cross-item interpretation (Mode 1 risk). Deconstruct confirms one deliverable — no late-split signal.

## Item I1

### Stage 2 — Meta-questions

**MQ1 — verdict-axis.** *What is the user asking for?*

Identified-ambiguities-list:
- **[decision vs map]** — one chosen design, or a map of design options with trade-offs, or both (a map that ends in a choice).
- **["elegant" — by which measure]** — the smallest change to the existing code; the fewest new concepts; the closest fit to existing patterns (one door, interception at a seam, fail-closed); the strongest guarantees; or a reusable seam for future transports.
- **[settle vs route, per open point]** — whether each of the ten points must be decided here, or may be routed to `desc.md` / `plan.md` or to a live test.
- **["concerns not yet realised"]** — a risk register, design constraints, open blockers, or all three.
- **[the scope of "without harming"]** — no behaviour change on the default path only, or no structural change to the listed elements at all, or no change visible to their consumers.

**MQ2 — context-need axis.** *What context does the response need that is not in the statement?*

Identified-ambiguities-list:
- **verdict sub-axis:**
  - whether code reading settles the open behavioural points (keep-alive on strict clients, reconnect paths, retry loops), or probes against Telethon 1.45.0 are needed;
  - whether further live evidence beyond the 2026-11-26 probe is needed — and it can only be run on the maintainer's go.
- **kinds sub-axis:**
  - Telethon 1.45.0's internals: `Connection`, `ObfuscatedIO`, `MTProtoSender` connect / reconnect / keep-alive, the exported-sender and CDN construction sites, `_switch_dc`;
  - tgdata's consumer contracts: `_new_client` and its option seam, the strict client options, `LoginFlow`'s binding, `AccountPool._failure`, the `Worker` pins, `StoredSession`;
  - the WebSocket protocol, RFC 6455 (framing, masking, close, ping);
  - Telegram's published transport page;
  - the probe and its results;
  - CONTRIBUTING's conventions;
  - the existing tests' patch points (`test_12` relay, `test_13` stand-in).
- **stance sub-axis:**
  - the maintainer's notion of elegance;
  - the appetite for depending on an unpublished endpoint;
  - whether adding a dependency is acceptable;
  - how strict fail-closed must be: refuse at config time vs at connect time.

**MQ3 — intent-axis (WHAT).** *What is the user trying to accomplish?*

Identified-ambiguities-list:
- **[the end point of this inquiry]** — a decided design to write `desc.md` and `plan.md` from; or an evaluation of whether to build at all; or both.
- **[the action end points]** — choose the transport's shape; define the config surface; define the failure taxonomy and retry behaviour; define the test strategy; correct the docs that become false.
- **[the kind of change]** — a minimal addition beside the existing door, or a new general seam (a transport choice that is not WebSocket-specific).
- **[concern handling]** — design each concern out, document it, or route it to a live test.

**MQ4 — boundary-axis.** *What is the user explicitly excluding?*

Identified-ambiguities-list. These are exclusions stated in the input (intrinsic) or recorded in session context (extrinsic); where the source is unclear, they are routed to both MQ3 and MQ4:
- **[intrinsic]**
  - any change to the default TCP behaviour ("the default transport byte-identical");
  - harming the listed existing design elements;
  - comparing older Telethon versions;
  - any fallback to TCP or to an IP.
- **[extrinsic — #67 and its brief]**
  - MTProxy;
  - secrets in the repo;
  - implementing in this step: traverse precedes `desc.md`.
- **[extrinsic — the maintainer's memory note]**
  - designing for Telethon versions other than the latest;
  - drafting upstream Telethon issues.
- **[unclear source — routed to both MQ3 and MQ4]**
  - whether "do not harm" excludes touching those elements at all, or only changing their behaviour.

### MQA

- **Reconcile.** MQ1's "elegant — by which measure" and MQ3's "minimal addition vs new general seam" share one joint axis, the **elegance criterion**: what makes a design elegant here — minimal diff, pattern fit, guarantee strength, or generality. The joint axis is folded; downstream should treat it as one dimension.
- **Surface.** MQ1's "settle vs route" and MQ3's "decided design vs evaluation of whether to build" overlap: whether the inquiry may conclude "build" or "do not build" is partly a routing question. The joint axis is unclear, so this is an irreducible overlap.
- **Surface.** MQ2's stance on the appetite for an unpublished endpoint overlaps MQ3's evaluation end point: risk appetite partly decides whether the design exists at all. Irreducible.

### Stage 3 — Deconstruct + MultiDepth

**Deconstruct:**
- **deliverable:** a decided meaning-and-shape for `transport = websocket`, the stable framing that `desc.md` and `plan.md` are written from;
- **kinds:** design decisions on the ten open points, a register of concerns, a test strategy, and corrections to docs that become false;
- **bounds:** tgdata 0.1.4 on Telethon 1.45.0 only; the connection seam and its consumers (`TgData`, `AccountPool`, `Worker`, `LoginFlow`); the default path unchanged; no implementation in this step.

**Late-split check:** none. The kinds are facets of one decided shape, not separate deliverables.

**MultiDepth — literal statement:** *"What is the most elegant design for a per-account `transport = websocket` in tgdata — connecting to Telegram's WebSocket door by hostname through the configured proxy, TLS with SNI and a verified certificate, `GET /apiws` with `Sec-WebSocket-Protocol: binary`, Telethon 1.45.0's obfuscated transport as a byte stream in binary frames, every DC by name, fail-closed, sessions and device identity unchanged, the default byte-identical — without harming or breaking the existing design; also surface concerns not yet realised, and settle or route the ten open points."*

**MultiDepth — purpose and motivation ambiguities (WHY-axis):** identified-ambiguities-list. Why does the maintainer want this?
- **[operational]** — so an account's traffic leaves from one assigned address through a hostname-only proxy, and Telegram never sees the server's own;
- **[codebase stewardship]** — to keep a design the maintainer considers elegant from degrading as features accrete;
- **[account safety]** — to avoid behaviour that could get accounts restricted: a leak by IP, an odd transport fingerprint;
- **[vendor / cost]** — to decide between building this and changing proxy provider;
- **[process]** — to give CONTRIBUTING's `desc` → `plan` → `critic` chain a premise it can stand on, avoiding a re-plan later;
- **[discovery]** — to learn concerns nobody has thought of yet, before they become defects.

### Stage 4 — Rephrase: considered articulations

Composition sources:
- **Deliverable shape:** a decided meaning-and-shape.
- **Ambiguity dimensions:** the elegance criterion; decision vs map; settle vs route; the end point; minimal vs general; the concern-handling mode; WHY — operational, stewardship, safety, vendor, process, discovery.
- **NOT-list:** default TCP changes; MTProxy; secrets; older Telethon; fallback; implementing now.
- **Substrate:** warm.

The considered articulations:
1. **The minimal-change design.** *"Decide the smallest design that adds `transport = websocket` beside the existing single client factory — one new connection class and one config key — leaving every consumer and the request-seam mixins untouched. Settle each of the ten open points or route it to the plan."*
2. **The pattern-fit design.** *"Decide the design that fits tgdata's existing patterns most closely: one door, interception at a seam, fail-closed at config time, credential-free errors. Use it to decide the transport's shape, the DC-name map's home, the error taxonomy and the tests."*
3. **Concern-first.** *"Enumerate everything the WebSocket transport could break or leave unguarded — strict clients' keep-alive, retry loops, the login checkpoint's binding, docs that become false, a second way to dial an IP, the outside-world risks — and decide a design that closes each one, or explicitly routes it."*
4. **Map, then choose.** *"Map the shapes the transport could take — a Telethon connection class over a byte-stream adapter, or a local relay process like the third-party tools the brief cites — against the existing design's elegance and the fail-closed guarantee. Then choose one, with its trade-offs recorded."*
5. **Specific vs general.** *"Decide whether the design should be specific to Telegram's WebSocket door, or a small general transport choice in the config that the WebSocket door is the first user of — judged by what keeps the existing design elegant."*
6. **Build or not.** *"Decide the design and, alongside it, whether its residual outside-world risks justify building it at all, against the alternative of a proxy provider that allows IP targets."*

Bounds check: every variant keeps the deliverable shape (a decided design), spans at least one identified dimension, avoids the NOT-list (no default-path change, no MTProxy, no fallback, no implementation), and uses only substrate terms. The local relay in variant 4 is in substrate, through the brief's reference implementations.

## Self-assessment

**LAYER 1 self-check (single LIGHT pass):**

| Mode | Fire? |
|---|---|
| 1 Premature Itemize split | no — count 1 |
| 2 Late-detected multi-item | no — Deconstruct gives one deliverable |
| 3 MQ extension beyond four axes | no |
| 4 Operation missed | no — every field present |
| 5 MQ2 missing preparation content | no — verdict, kinds and stance present |
| 6 MQ2 missing kinds or stance | no |
| 7 2-shape violation | no — every MQ and MultiDepth output is an identified-ambiguities list |
| 8 AMBIGUITY-NATURE conflation | no — WHAT-axis content in MQ3, WHY-axis in MultiDepth |
| 9 Variants outside composition bounds | no |

**Friction:** moderate. The statement is long and carries ten open points, but they fold cleanly under one item.

**Verdict: HIGH-PROCEED**
