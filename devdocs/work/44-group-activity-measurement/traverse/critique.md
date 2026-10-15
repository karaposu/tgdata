# Structural critique — #44

## User Input
Evaluate innovation candidates against sensemaking's qualified-observation contract, including rejected alternatives. This is contract inquiry, not the later critic-d implementation-plan review.

## Phase 0 — dimensions and inherited premises
Critical: E evidence correctness (actual boundary/end proof; unknown rows cannot disappear), O operational ownership/admission (verified owner, actual source budget and original failure), T temporal/population meaning (publication versus observation, raw versus assembled, known versus missing). High: C compatibility and scope (strict v1/progress unchanged), F feasible source composition (actual SDK/TL/fixtures, not invented APIs). Medium: U useful/easy interface and D deterministic portability. Low: cosmetic economy.
Purpose fitness: E/O/T failures defeat trustworthy measurement; cosmetic preferences do not. External-anchor criterion: verify SDK source, current exact-key serializer and actual owned-call path. Failure-plane check includes local/protocol failures as well as Telegram errors; “safe requests” alone would miss lost partial evidence.

Independent frame prosecutions:
1. If separate schema is unnecessary, a real batch record should already carry counters and source completion witnesses. Current `_RECORD_KEYS` and `_record` lack those; v1 mutation fails strict validation. Premise supported independently of F1's elegance.
2. If direct source paging offers no stronger evidence, the iterator should yield placeholders/response types. Actual SDK line193 filters MessageEmpty; line216 says `it's not safe to rely on len(r.messages) < req.limit`. Premise supported, but direct paging itself still needs prebuild.
3. If bounded observations are not useful, user would need only exact census or no result. The audit consumer already uses bounded histories; the defect is silent completeness, not boundedness. Returning qualified data meets user intent without requiring a source snapshot.

## Phase 1 — landscape
Viable: narrow immutable observations with explicit evidence and existing owned lifecycle. Dead: hidden truncation, guessed counters/authors, shared unverified owner or incompatible v1 extension. Boundary: generic stream/analytics framework or archive; potentially useful but excessive for44. Unexplored: live visibility across actual Telegram groups and concurrent source mutation; these constrain evidence claims, not grounds for inventing a store.

## Phases 2–3 — prosecution / defense / collision accumulator
| Candidate | Prosecution | Defense | Collision / constructive verdict |
|---|---|---|---|
| G1 | Unit/timezone/mode matrix grows ambiguous definitions | Broad reuse | KILL scope: seed a later explicitly requested mode instead |
| F1 | A coverage boolean alone hides why evidence failed | Separate raw facts and stop/unknown fields explain it | SURVIVE E/T/C/D; require described fields in schema |
| C1 | Exact v1 keys reject counters | Reuses consumer format | KILL C: seed separate value without migration |
| G2 | Streaming lifetime and raw SDK types expose heavy caller obligations | Reusable page abstraction | KILL U for this delivery: seed internal collector only |
| F2 | Rounded end can skip same-second messages; short pages or order anomalies can falsely finish | Direct page evidence permits precise filters/checks | SURVIVE E/F at contract level: conservative upper seek, local half-open selection, exclusive ID continuation, actual end evidence; combined prebuild must prove mechanism |
| C2 | Supplied rows lack source provenance; iterator erases empty rows | Small pure helper | KILL completeness: seed internal pure summarizer fed by qualified capture |
| G3 | DSL permits undefined ratios/populations | Flexibility | KILL U/scope: seed fixed documented metrics |
| F3 | Seven rolling days can touch eight UTC dates; missing counters skew sums | Named buckets and known populations permit honest arithmetic | SURVIVE T/D: no average daily unique-users scalar, exact exposure, separate counter known/missing counts |
| C3 | Omits native reusable aggregate functionality | Eliminates assumptions | KILL issue completeness: seed raw rows retained alongside math |
| G4 | Resume cannot freeze history; creates new failure/lifecycle system | Handles long scans | KILL scope/O: seed finite one-call observation |
| F4 | Cancellation during cleanup may erase a successful return | Existing operation deliberately preserves cancellation; no durable receipt promised | SURVIVE O/C with same contract and documented best-effort partial attachment |
| C4 | Expected B/cached A attribution regression | Low startup overhead | KILL O: keep verified operation |
| L1 | Caller may treat partial count as census | Explicit coverage and null complete-window rates | SURVIVE E/U; capped output remains useful |
| B1 | Stored summary drifts from records | Derive on demand from immutable facts | SURVIVE D; no duplicate mutable authority |
| V1 | Most cap can be spent on service/empty rows | That's actual work and prevents unbounded request loops | SURVIVE E/O; document cap unit clearly |
| A1 | UTC-only insufficient for local businesses | Raw dates permit consumer bucketing | SURVIVE U/C; explicit initial boundary |
| R1 | Cannot audit a historical snapshot | Source provides no transactional freeze | SURVIVE E/T; observed visible-history claim only |
| R2 | Unbounded cost defeats stated scope | Complete scan simpler to interpret | KILL O: seed explicit finite cap plus completion witness |
| N1/N2 | Many flags could contradict | One coverage flag, independent missing counts, explicit stop reason | SURVIVE E/D with fixed meanings |
| D1 | Median of available counters is biased if called whole-window median | Availability population named | SURVIVE T; label observed-counter distribution |
| E1 | Future-proofing can bloat current work | IDs/timestamps/counters already in issue | SURVIVE C/U only for requested raw facts; archive remains frontier |

User-level objection: “I want comparable group activity, not a complicated packet dump.” The selected result includes straightforward counts, daily rows and counter summaries; raw evidence supports them. It withholds only claims unsupported by a capped/unknown scan.
Literal edge case: cap100, response100 dated in-window, reported count100. No boundary/end witness from a sliced/channel result: coverage false even if the count says100. An extra request is not allowed after cap. Literal unknown case: a MessageEmpty slot between valid rows prevents complete coverage even if traversal later reaches the start. Literal denominator case: views [0,None,10] → known2/missing1/sum10/mean5, never mean(10) or10/3.
Specification-gap probe: source response types, monotone offset IDs and local timestamp predicate determine end/boundary; optional fields determine metric availability; known PeerUser/PeerChannel determine identity categories. Runtime decisions have named mechanisms, not just labels.

## Phase 3.5 — assembly
Selected assembly F1+F2+F3+F4 and refinements. Prosecution: source validation might fail mid-page after some rows, and aggregate construction in the exception path could mask the original error. Defense: page validation is atomic before accepting its observations; retain prior accepted pages, validate primitive values before aggregation, attach partial evidence defensively. Collision: SURVIVE contract with page-atomic acceptance and explicit errors; plan must cover malformed pages, budget/transport failure and cancellation after a valid page. No independent lifecycle/store machinery is necessary.

## Phase 4 — coverage / second adversarial iteration
Iteration1 mapped all candidates above. Iteration2 retested the surviving assembly against source-end versus cap, placeholder versus missing counter, UTC exposure versus unique users, caller cancellation versus result publication, and existing Batch v1 versus separate schema. No new landscape region: these land respectively on E,T,T,O,C already mapped; no new candidate needed. The assembly's page-atomic condition resolves the only composition weakness without changing the frame. This is contract convergence, not runtime qualification.
Coverage map: collection/representation/population/ownership/portability axes covered; live source visibility and cross-version SDK behavior remain explicit external qualification frontiers. All candidates checked on critical axes; survivors additionally checked U/D/F/C. Accumulator: kill seeds and reasons in table; no pending contract refinement; mechanism_independence_status=validated against SDK/source/consumer artifacts. Two evaluation iterations stable; decreasing new information (composition detail then none), clean contract survivor present. Ranked survivors: (1) selected assembly; (2) its reusable immutable value/pure arithmetic pieces. TERMINATE contract inquiry and proceed to required route exhaust. Runtime implementation remains blocked until the later plan prebuild succeeds.
Telemetry: all dimensions covered, adversarial strength STRONG, landscape STABLE after second iteration, clean contract SURVIVE yes. Nine listed failure modes checked, no self-reference evaluation. Manual structural check phases0/1/2/3/3.5/4 and telemetry PASS. PROCEED.
