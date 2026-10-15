# Decomposition — #44 (DV1)

## User Input
`_branch.md`, articulation, surfacing and stabilized `sensemaking.md`: bounded qualified measurement without changing existing progress or batch semantics.

## 1. Coupling topology
High coupling: page offsets/order/slot caps/end witnesses; row interpretation/unknowns/metric populations; owner/admission/heartbeat/cleanup (existing cluster). Moderate coupling: immutable observations connect source traversal to statistics. Weak coupling: publication documentation and caller-specific interpretation. No coupling: worker scheduling, synchronization acknowledgments, joining, album folding and discovery state.

## 2. Top-down boundaries
P1 observation meaning/value; P2 source traversal and evidence; P3 deterministic statistics; P4 composition with existing operational guarantees and public entry point. P4 is integration, not a replacement lifecycle. Evidence/provenance belongs in P1's interface and P2 produces it; it must not be manufactured by P3 from row count alone.

## 3. Bottom-up validation
Atoms: optional counter plus availability, sender kind plus ID, timestamp plus UTC meaning, source slot plus charge, offset plus progress, source-end plus response type, operation plus verified owner. None is split across contradictory authorities. P1 defines format, P2 obtains source evidence, P3 consumes it. All four boundaries HIGH confidence. The source collector is the largest piece but page evidence and offsets share mutable state and must remain together; splitting into separate end-detector and iterator would hide coupling.

## 4. Question tree and verification criteria
Root: How can a bounded invocation return useful statistics without overstating the visible history or counter evidence?

| Piece | Question | Done when |
|---|---|---|
| P1 | What precisely does each retained fact and result claim? | Fixed bounds/unit/timezone/version; portable immutable representation; count availability and author identities; coverage stop/evidence; no atomic-snapshot promise. |
| P2 | How does a bounded traversal establish what it saw and where it stopped? | Actual response types and placeholders retained; offsets progress; boundaries/equal seconds validated; short/empty/full pages distinguished; source work capped; malformed/repeated responses fail; cap never implies complete. |
| P3 | Which statistics follow from those facts without guessing? | Raw/service/unknown populations; known users/channels; daily edge exposure; metric missing/zero rules; denominator/rates; latest-observed label; pure expected-value tests. |
| P4 | How does the public call preserve operational behavior? | Validation before connection; expected account verified; source calls admitted/charged once; heartbeats reflect actual progress; errors retain partial evidence; cancellation/cleanup/health preserve original guarantees. |

## 5. Interfaces and assumptions
| Source → target | Flow | Assumptions, not just data |
|---|---|---|
| P1 → P2 | validated request and result schema | aware UTC normalized bounds, finite source budget; no business filters or folding |
| P2 → P1/P3 | dated immutable rows, source-slot counts, termination evidence, observation interval | no hidden unknown rows; response order checked; no metric can promote coverage |
| P1 → P3 | counter optionality, author kinds, day/window definitions | None is not zero; distinct IDs aren't distinct people; service rows excluded from ordinary metrics |
| P4 → P2 | verified client/identity, budget admission and liveness scope | no second client, fresh policy already set, raw RPC uses BudgetClientMixin |
| P2/P3 → P4 | final or validated partial observation | ordinary failures keep their type; partial data is observational, not durable delivery |
| P4 → caller | result or original exception with best-effort partial_result | explicit collection interval; no mutations to batch/progress state |
No circular runtime dependency: P1 is the contract, P2 evidence precedes P3 statistics. Error serialization must not invoke source or mask the original error.

## 6. Dependency order
Define P1 first. Establish P2's real SDK evidence and P4's combined operation behavior before committing implementation. P3 arithmetic can be specified independently once P1 is stable. Integrate P1→P2→P3 through P4, then verify adversarial composition. This is conceptual ordering, not an implementation task list; downstream plan chooses files/steps.

## 7. Self-evaluation
Independence PASS (each question uses explicit interfaces); completeness PASS (all issue dimensions mapped); reassembly PASS (request→owned source→evidence→math→caller). Runtime determination check PASS: P2 explicitly owns boundary/end/cap/order/unknown detection, P3 owns per-counter availability, P4 owns actual account admission. Tractability PASS; interface clarity PASS; balance PASS (collector appropriately cohesive); confidence PASS (top-down/bottom-up agree). Seven failure modes checked: no premature split, heavy crossing boundary, unstated snapshot assumption, missing detection, tiny fragments, dependency cycle or single opaque implementation bucket. Stop at DV1: four directly verifiable pieces. Manual structural check 7/7 steps, 7/7 evaluation dimensions. PROCEED to innovation.
