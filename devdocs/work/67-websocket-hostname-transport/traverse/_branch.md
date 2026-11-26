# Branch: issue #67 — the most elegant WebSocket transport design for tgdata

## Source Input

The raw request, verbatim. It also lives in `articulate_simple.md`'s `## User Input`, and both copies are authoritative.

```text
Issue #67 in karaposu/tgdata, branch feat/67-websocket-hostname-transport, worktree /Users/ns/Desktop/projects/telegram-group-scraper/.worktrees/67 (all paths below are relative to it). Write all output to devdocs/work/67-websocket-hostname-transport/traverse/ (CONTRIBUTING.md §5: traverse output lives in traverse/ on the branch and becomes the raw material for desc.md). Inputs already on the branch: devdocs/work/67-websocket-hostname-transport/triage.md (feature-heavy; watch-for 1–8; frontier items), devdocs/work/67-websocket-hostname-transport/ws_door_probe.py (the no-account probe), devdocs/archaeology/intro2codebase.md and small_summary.md (warmed at 240a208), and issue #67's body + comments (probe results 2026-11-26: all five DCs work by planet name pluto/venus/aurora/vesta/flora incl. -1 names except kws2-1/kws4-1; every connection left from the proxy's assigned address with IP targets refused; idle tunnels survive 150 s, cut by 300 s; Telethon's full client pings its main connection every 60 s). The question: what is the most ELEGANT design for a per-account `transport = websocket` in tgdata — connect to Telegram's WebSocket door by hostname through the configured proxy (HTTP CONNECT / SOCKS remote DNS), TLS with SNI + verified certificate, GET /apiws with Sec-WebSocket-Protocol: binary, Telethon 1.45.0's obfuscated transport carried as a byte stream in binary frames, every DC by name, fail-closed (never an IP, no fallback to TCP), session files and device identity unchanged, the default transport byte-identical — WITHOUT harming or breaking the existing design, which the maintainer considers elegant and wants kept that way (the single client factory ConnectionEngine._new_client; the request-seam mixin stack _AnswerEvidence/JoinClientMixin/BudgetClientMixin/BatchHeartbeatMixin/_PerCallFloodThreshold; the fail-closed proxy guarantees; owned account operations with strict client options; StoredSession; LoginFlow's checkpoint binding; AccountPool's failure classification; the Telethon==1.45.0 pins). Also surface concerns not yet realised. Open points to settle or route: (1) the transport as a Telethon Connection subclass (ConnectionTcpObfuscated reused over a byte-stream adapter) vs other shapes; (2) where the DC→hostname map lives and whether it is configurable; (3) whether Telethon's 60 s _keepalive_loop runs on strict clients (receive_updates=False, auto_reconnect=False) and so covers the 150–300 s idle cut, or the transport must ping; (4) the error taxonomy — configuration vs transient transport failures, Telethon's connection_retries and AccountPool's 'transport' retry; (5) require_proxy × websocket and a websocket transport with no proxy; (6) whether the transport joins LoginFlow's binding; (7) a hand-written WebSocket client vs an optional dependency; (8) docs/comments that become false (connection_engine's 'remote DNS is moot'); (9) testing: offline fake TLS WebSocket server, a no-IP guarantee across every connect path including reconnect / exported senders / CDN, test_12's recording SOCKS relay; (10) the remaining outside-world risks (unpublished door, desktop api_id via the web door, relay rate limits, existing TCP-made login keys over the door). Telethon baseline: 1.45.0 (latest on PyPI; do not compare older versions). Consumers to keep in view: TgData, AccountPool, Worker, LoginFlow. Goal for the onward route-field (_branch.md): a stable, decided meaning-and-shape from which desc.md and plan.md for #67 can be written.
```

## Articulation Reference

- **File:** `devdocs/work/67-websocket-hostname-transport/traverse/articulate_simple.md`
- **Itemize count:** 1
- **Per-item identifiers:** `I1`
- **Verdict:** HIGH-PROCEED
- **Flagged conditions:** none

## Question

**The literal statement:** *"What is the most elegant design for a per-account `transport = websocket` in tgdata — connecting to Telegram's WebSocket door by hostname through the configured proxy, TLS with SNI and a verified certificate, `GET /apiws` with `Sec-WebSocket-Protocol: binary`, Telethon 1.45.0's obfuscated transport as a byte stream in binary frames, every DC by name, fail-closed, sessions and device identity unchanged, the default byte-identical — without harming or breaking the existing design; also surface concerns not yet realised, and settle or route the ten open points."*

**What kinds of ask this carries** — MQ1, kept as ambiguities:
- **decision vs map** — one chosen design, a map of options with trade-offs, or a map that ends in a choice;
- **"elegant" — by which measure** — the smallest change, the fewest new concepts, the closest fit to existing patterns, the strongest guarantees, or a reusable seam. MQA folds this with MQ3 into one **elegance-criterion** dimension;
- **settle vs route** — whether each of the ten points is decided here, or routed to `desc.md` / `plan.md` or a live test;
- **"concerns not yet realised"** — a risk register, design constraints, open blockers, or all three;
- **the scope of "without harming"** — no behaviour change on the default path, no structural change to the listed elements, or no change visible to their consumers.

**What it may be trying to accomplish** — MQ3, kept as ambiguities:
- **the end point** — a decided design for `desc.md` / `plan.md`, an evaluation of whether to build at all, or both. Irreducible overlap with settle-vs-route, per MQA;
- **the action end points** — choose the transport's shape, the config surface, the failure taxonomy and retries, the test strategy, and the doc corrections;
- **the kind of change** — a minimal addition beside the existing door, or a new general transport seam;
- **concern handling** — design it out, document it, or route it to a live test.

## Goal

**Deconstruct:**
- **deliverable:** a decided meaning-and-shape for `transport = websocket`, the stable framing for `desc.md` and `plan.md`;
- **kinds:** decisions on the ten open points, a concern register, a test strategy, and doc corrections;
- **bounds:** tgdata 0.1.4 on Telethon 1.45.0; the connection seam and its consumers (`TgData`, `AccountPool`, `Worker`, `LoginFlow`); the default path unchanged; no implementation here.

**Motivations a good answer might serve** — MultiDepth WHY, kept open:
- **operational** — one assigned exit address through a hostname-only proxy;
- **codebase stewardship** — keep an elegant design elegant;
- **account safety** — no leak by IP, no odd fingerprint;
- **vendor / cost** — building vs switching proxy provider;
- **process** — a premise CONTRIBUTING's chain can stand on;
- **discovery** — find concerns before they become defects.

**Context the answer needs** — MQ2:
- **verdict:**
  - whether code reading settles the behavioural points, or Telethon 1.45.0 probes are needed;
  - whether more live evidence is needed — only on the maintainer's go.
- **kinds:**
  - Telethon 1.45.0's network layer and connection-construction sites;
  - tgdata's consumer contracts: `_new_client`'s option seam, the strict options, `LoginFlow`'s binding, `AccountPool._failure`, the pins, `StoredSession`;
  - RFC 6455 and Telegram's transport page;
  - the probe and its results;
  - CONTRIBUTING;
  - the tests' patch points.
- **stance:**
  - the maintainer's notion of elegance;
  - the appetite for an unpublished endpoint;
  - whether a new dependency is acceptable;
  - fail-closed at config time vs at connect time.

**What would explicitly fail** — MQ4, the negative spec:
- any change to the default TCP behaviour;
- harming the listed design elements — and whether that means not touching them at all, or not changing their behaviour, is itself an open reading;
- any fallback to TCP or to an IP;
- MTProxy;
- secrets in the repo;
- designing for older Telethon;
- drafting upstream Telethon issues;
- implementing in this step.

## Considered Articulations

- **Item I1 — the WebSocket transport design:**
  1. **The minimal-change design.** The smallest design that adds `transport = websocket` beside the existing single client factory — one new connection class and one config key — leaving every consumer and the request-seam mixins untouched. Settle each of the ten open points or route it to the plan.
  2. **The pattern-fit design.** The design that fits tgdata's existing patterns most closely — one door, interception at a seam, fail-closed at config time, credential-free errors — used to decide the transport's shape, the DC-name map's home, the error taxonomy and the tests.
  3. **Concern-first.** Enumerate everything the WebSocket transport could break or leave unguarded — strict clients' keep-alive, retry loops, the login checkpoint's binding, docs that become false, a second way to dial an IP, the outside-world risks — and decide a design that closes each one, or explicitly routes it.
  4. **Map, then choose.** Map the shapes the transport could take — a Telethon connection class over a byte-stream adapter, or a local relay process like the third-party tools the brief cites — against the existing design's elegance and the fail-closed guarantee. Then choose one, with its trade-offs recorded.
  5. **Specific vs general.** Decide whether the design is specific to Telegram's WebSocket door, or a small general transport choice in the config that the WebSocket door is the first user of — judged by what keeps the existing design elegant.
  6. **Build or not.** Decide the design and, alongside it, whether its residual outside-world risks justify building it at all, against a proxy provider that allows IP targets.

## Scope Check

**Question covers goal.** The question asks for the design and for its concerns, with the ten points settled or routed. That is the goal's deliverable, a decided meaning-and-shape with its kinds. The bounds — Telethon 1.45.0, the connection seam and its consumers, the default unchanged, no implementation — come from Deconstruct. The exclusions come from MQ4.

**Specific vs pattern.** The ten open points are specific prompts, not the whole field. The inquiry addresses the broader pattern — every way the transport meets the existing design — and treats the ten as a checklist the answer must cover. "Concerns not yet realised" explicitly asks for beyond the ten.
