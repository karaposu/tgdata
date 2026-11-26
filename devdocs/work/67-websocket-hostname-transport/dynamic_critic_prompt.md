# Dynamic critic prompt — #67 WebSocket transport plan

**Subject.** Critique `plan.md` (14 steps) against `desc.md` (success criteria 1–14, scope, the settled `Origin` decision), `traverse/finding.md` (the decided design), and the code on `feat/67-websocket-hostname-transport`: tgdata 0.1.4 on Telethon 1.45.0 and Python 3.11+. Older Pythons and older Telethons are out of scope; do not raise them.

**What this feature is.** A per-account `transport = websocket` makes every connection reach Telegram's WebSocket endpoint by hostname — `wss://<planet>.web.telegram.org/apiws`, through the configured proxy or directly by name — and never by IP.

**How the plan achieves it:**
- a standard-library-only opener (`tgdata/ws_stream.py`), with a new `TransportConfigError`;
- a Telethon `ConnectionTcpObfuscated` subclass that hands Telethon the hostname in place of the DC's IP (`tgdata/websocket_transport.py`);
- small conditional edits: the config reader, the single client factory `ConnectionEngine._new_client`, two connect wrappers, the route log line, `health_check()`, and `LoginFlow`'s binding;
- an offline smoke test (`test_50`) with a Telethon-internals canary;
- docs;
- a live check gated on the maintainer's go (execution blocker E1 — a precondition, not a risk).

**The maintainer's overriding constraint:** the existing design must not be harmed. That covers:
- the single client factory;
- the request-level guards (the mixins above Telethon's sender);
- the strict client options of owned operations, the pool and login;
- `StoredSession`;
- the login checkpoint binding;
- `AccountPool._failure`;
- the exact Telethon pins.

The default path must be byte-identical.

---

**Ultrathink, read every file the plan touches in full, and probe anything behavioural with the real Telethon 1.45.0 in the venv, quoting the outputs. Never contact Telegram or use the real account.** Then answer these questions, specific to this codebase and feature.

1. **The guarantee: "never an IP".**
   - Follow every place a socket can be opened for a WebSocket account: Telethon's four construction sites, reconnect, exported senders, the CDN client, `_switch_dc` at login, the direct (no-proxy) path.
   - Does any path build a connection without the class, or hand it an IP it would dial?
   - Does Telethon's own proxy code (`Connection._proxy_connect`, python-socks or PySocks) send the *name* for HTTP CONNECT, SOCKS5 and SOCKS4 with tgdata's `rdns: True`? Probe it.
   - Does the socket it returns carry TLS with SNI?
2. **The classification contract, across every consumer, not only the pool.**
   - The plan expresses "stop immediately vs retry" through exception types. Find **every** place in tgdata that recognises configuration errors or connection errors by class: `AccountPool._failure`, `TgData`'s connect wrappers, the polling loop, the worker's wire protocol, discovery's reconnect wait, `health.classify`.
   - Does each one treat the new error as the plan intends?
   - Does a "stop immediately" error survive every wrapper between Telethon and the caller with its type intact?
   - Does keeping `ws_stream` free of Telethon constrain where the error class can live?
3. **The default-path invariance.**
   - Do any of the edits — the config field, the factory branch, the wrappers, the route line, `health_check`, the binding — change anything observable for an account without the key?
   - Is there an existing test or consumer that compares exact key sets, constructor arguments, log lines or hashes?
   - Is the baseline captured before any code changes?
4. **Telethon's connection lifecycle, as the class relies on it.**
   - The reader/writer contract `ObfuscatedIO` uses.
   - When `_init_conn` captures them.
   - Which errors the receive loop handles quietly.
   - What `disconnect()` does when `_connect` failed half-way.
   - Whether reconnect reuses the object.
   - What a failure inside `_connect` leaves behind.
5. **The offline proof's feasibility.** Does the test plan describe mechanics that will actually terminate and stay isolated?
   - Telethon's key exchange waits on the server with no timeout.
   - The retry delays.
   - Class-level caches such as `_get_dc`'s `cls._config`, and the plan's `_ssl_context` seam.
   - Building pool sources offline.
   - Whether any fake *supplies* the behaviour under test instead of observing it.
6. **The live parts and account safety.**
   - What the plan assumes about Telegram's treatment of this account over the web transport.
   - When that assumption is first tested.
   - Whether an earlier, cheaper test exists.
   - What could harm the real account during the live check — for example, one session used from two places at once.
7. **Elegance against the maintainer's criterion:** the fewest seams touched, the most reuse, no new concept Telethon already provides. Is there an edit the plan makes that a smaller one would make unnecessary, or a consumer edit a better class choice would avoid?
8. **Detail versus difficulty.** Flag any step whose description is too high-level for the complexity of the code it touches as a **Medium** risk.

---

## Output instructions

Create a `critic.md` file in the same directory as the implementation plan, and put a high level summary at the top of it.

**Order of contents:**
1. **A frontmatter block,** first:
   ```yaml
   ---
   model: [model id from session context; "unknown" if not derivable]
   effort: [effort setting from session context; "unknown" if not derivable]
   ---
   ```
2. **The document-level verdict,** directly after the frontmatter, and exactly one of:
   - **IMPLEMENT AS WRITTEN** — no changes needed;
   - **IMPLEMENT AFTER FOLDING THESE IN** — the shape survives, and the findings are absorbed;
   - **REORDER — TEST BEFORE BUILD** — the plan builds on an untested premise before testing it, and its sequence must change. Name the experiment, its cost, the step it must precede, and the result that converts this to verdict 4;
   - **DO NOT IMPLEMENT — MEANING GAP**, or **— WRONG LAYER** — the premise is wrong, or the plan does not address the failures it cites.

   The verdict judges shape and sequence, not the number of findings.
3. **The falsifier, directly under the verdict** (on verdicts 1–3):
   ```
   Falsifier: [the cheapest observation that would flip this verdict to DO NOT IMPLEMENT]
   Affordable now: yes | no — [cost: time, money, access]
   ```
   If it is affordable now and the verdict is 1 or 2, the verdict is REORDER.
4. **The high level summary.**
5. **The Premise Inventory,** computed before any risk item.
   - **What goes in:** every premise the plan hedges, plus every claim about how a vendor service (Telegram) behaves.
   - **Per premise:** the premise · the first dependent step · the waste if it is false · the step where it is tested · the cheapest earlier test, with its cost ("none" must be argued) · its coverage, flagging as **non-covering** any test that supplies the behaviour rather than observing it.
   - **Ranking:** by waste if false.
   - **The rule:** if any premise's cheapest earlier test is affordable now and is scheduled after its first dependent step, the verdict is REORDER.
6. **The Restart Check** — only if `desc.md` or the plan cites a prior failure.
7. **The Inherited Lessons check** — one row per settled conclusion `desc.md` carries, and the step whose ordering satisfies it.
8. **The risk items.**

## Output Format

For each risk found, document these fields:

**Risk** — written as TWO paragraphs, in this order. This is the field readers hit first, so it carries both registers itself rather than deferring the plain one to a box further down.

*Paragraph 1 — plain.* What goes wrong, for someone who has not read this plan and does not know this codebase's vocabulary.
- **Self-contained.** Every project-specific name — a module, class, config key, feature, table — is introduced with what it IS before it is used. Not "the resolver drops the trailing scope" but "the part that turns a login into a list of permissions drops the last permission on the list."
- **The consequence** is stated in terms someone would actually notice: what breaks, for whom, when.
- **No** file paths, symbol names or line numbers.

*Paragraph 2 — precise.* The same risk stated technically: file paths, function and class names, config keys, the call path or data flow involved, and the exact conditions under which it fires. This is the paragraph the implementer and the AI work from.

Both paragraphs describe the SAME risk at two resolutions. Paragraph 1 is not a summary of paragraph 2 — it is a genuine explanation of it.

**Test:** could someone who has never opened this repository read paragraph 1 alone and understand what would go wrong and why it matters? If not, it has failed, and the usual cause is internally-referential shorthand — phrasing that works for whoever has been living with this codebase's vocabulary and fails for everyone else.

**Severity** — Low / Medium / High
**Category** — Breaking change / Import error / Circular import / Package discovery / Stale cache / Missing file / Phase ordering / Consumer contract / Test isolation / Account safety (others as the codebase warrants)
**Impact** — possible effects if this risk materialises
**NoobEng** — for an engineer who reads code fine but does not know THIS system's dynamics. The middle register between the two Risk paragraphs: it assumes engineering literacy, and no familiarity with this project.
**Affected areas** — which existing features, modules, or endpoints are affected
**Mitigation** (Medium/High only) — three proposals: quick fix, robust fix, long-term fix. Keep the existing "why this is robust:" and "why this is long term effective:" subfields.

Under EACH of the three proposals — quick, robust and long-term alike — emit this scaffold, boxes unticked and both note sections empty. Do not fill them; a later pass does that.

    - [ ] selected   - [ ] elegant   - [ ] last_resort

    **Note**
    *Why chosen:* —
    *For future:* —

Dont use tabular format,  it should be sections with subsections and detailed enough.
