# State: issue #67 — WebSocket transport design
## Flow-type
articulated-surfacing-routed
## Pipeline
A → Su → W → S → D → I → C → R (always)
## Progress
- [x] Articulate-Simple
- [x] Surfacing
- [x] Warm
- [x] Sensemaking
- [x] Decomposition
- [x] Innovation
- [x] Critique
- [x] Routelister
## Warm Loop
round: 0/2 | last-anchor: Telethon connection lifecycle + tgdata single door + consumer contracts + prototype | status: settled (fixpoint)
## Iteration
1
## Status
COMPLETE
## Next Discipline
—
## Relationships
- CONTINUES FROM: devdocs/work/67-websocket-hostname-transport/triage.md (the triage surfacing record — its trace is the prior artifact for this inquiry's surfacing)
## History
- 2026-11-26_15-45: Created. Question: the most elegant design for a per-account `transport = websocket` in tgdata, without harming the existing design; surface unrealised concerns; settle or route ten open points. Articulation: HIGH-PROCEED (Itemize count = 1; flagged: none).
- 2026-11-26_15-49: Surfacing complete — 20 items (9 core / 9 sub / 2 side), triage.md used as the exclusion filter; key finds: the keep-alive runs on strict clients, strict clients never reconnect, Telethon retries only IOError and replaces it unchained, the login binding hash. Structural check: manual, 6/6 (no structural_check.sh available). Next: Warm.
- 2026-11-26_15-50: Warm complete — fixpoint at round 0 (0 re-surfaces; the anchor did not move). Re-ran MQ2, MQ4, MQ1, MQ3, MQA, Rephrase; WHY carried. content-conflict C1 resolvable (MED-FLAG): the Telethon pin is partial — only AccountPool and Worker pin 1.45.0; plain TgData accepts >=1.45,<2.0. Conflict gate: non-severe, proceed. Structural check: manual 4/4. Next: Sensemaking.
- 2026-11-26_15-55: Sensemaking complete — SV1→SV6. The model is one ConnectionTcpObfuscated subclass, named at construction, selected by one `transport` key at the one door; everything else is reuse of Telethon or tgdata. 14 ambiguities collapsed (10 HIGH, 3 MEDIUM: A3 host override, A6 health field, A10 hard pin; A14 calibration LOW). New concerns: certificate failures fail fast; 'transport' is overloaded with request envelopes; the binding entry only when non-default; exported senders get no pings but are closed after ≤120 s idle (re-checked in 1.45.0 source). Structural check: manual — SV1–SV6 and Phases 1–5 present, A1–A10 full entry fields, A11–A14 abbreviated. Next: Decomposition.
- 2026-11-26_15-58: Decomposition complete — 8 pieces: P0 error contract → P1 WebSocket stream ∥ P2 Telethon connection class + DC map → P3 selection/visibility → P4 login binding → P5 offline guarantees (no-IP on every path, default byte-identical, canary) → P6 docs + risk register → P7 live calibration (maintainer's go). Three hidden couplings captured: Telethon's receive loop treats only IOError/IncompleteReadError quietly (mid-session faults must be IOError); ObfuscatedIO captures _reader/_writer at _init_conn; P5 needs an SSL-context seam in P1. Re-checked in 1.45.0: connection construction is outside _try_connect (an __init__ error is never retried); SSLCertVerificationError is an OSError; tgdata never passes local_addr. Structural check: manual — Steps 1–7, 8 questions with criteria, interface map, order, 7-dimension self-eval (Balance PARTIAL, accepted). Next: Innovation.
- 2026-11-26_16-02: Innovation complete — 7/7 mechanisms, 23 candidates tested. Emergent: a four-layer 'never an IP' (constructor passes the name to Telethon's own __init__; the opener refuses IP literals; recording-proxy tests incl. a mixed tcp/websocket pool; Telethon's own INFO 'Connecting to <host>:443' line as runtime evidence). Actionable: L-G, L-F, C-G, CM-G, AR-P2 (health non-interaction test), DT-G, DT-F, E-G; experiment I-C (is Origin needed? probe --no-origin); RE-TEST I-G: both name families worked for every name used, so A3/A14's planet justification does not apply; deferred L-C, I-F, CM-C, E-C (door-policy RPC errors could read as health 'unclassified'). Killed, each confirming SV6: C-F, I-D, I-E, CM-F (Telethon's _proxy_connect maps python-socks errors to ConnectionError), AR-R. Structural check: manual — seed + mode, 7 mechanisms × 3, frame audit, test table, assembly, telemetry PROCEED. Next: Critique.
- 2026-11-26_16-05: Critique complete — 9 dimensions (D1 fail-closed, D2 no harm, D3 Telethon-correct critical); frame-premise test FP1–FP3 hold. Assembly A* (SV6 hardened) SURVIVES first: production delta ≈ 6 lines beyond SV6 (super().__init__ with the name, opener refuses IP literals, lazy import confines breakage to websocket users, transport named in messages). L-C promoted on blast-radius isolation (plain TgData is unpinned). Planet map SURVIVES with corrected justification (external: an independent client library uses the same five names; the probe shows both families equal) — formula KILLED. Killed: rotation, host override, codec match. I-C (Origin) REFINE as a P7 observation. E-C a registered concern (door-policy RPC errors could read as health 'unclassified'). External anchors X1–X4; mechanism independence validated. Signal TERMINATE; telemetry PROCEED. Structural check: manual — Phases 0–4, verdicts with seeds, assembly, coverage, telemetry. Next: Routelister.
- 2026-11-26_16-08: Routelister complete — root/project-space, fresh; 19 routes (12 core incl. 2 @post-build, 6 supporting, 1 peripheral; 9 HIGH). Wrote routelister.md + _route.md in the inquiry root. Basis: 9 pointers, 1 paraphrase (R5: the external library seen only as a search summary), 0 not-recovered. Verdict PROCEED. Structural check: manual — header, index, 19 records with Move/Lands/WHY/attribution/guidance, Sources, Excluded, telemetry; _route.md identity table + log, no process state. Next: CONCLUDE.
- 2026-11-26_16-10: CONCLUDE — finding.md written; the seven upstream discipline outputs archived to docarchive/; routelister.md and _route.md kept in root. Answer: the WebSocket transport is one Telethon connection class (a ConnectionTcpObfuscated subclass that hands Telethon the DC's hostname in place of its IP), chosen per account by one `transport` key at the one client factory; everything else is reuse, the default is byte-identical, and the login binding gains `transport` only when not tcp. Status COMPLETE.
