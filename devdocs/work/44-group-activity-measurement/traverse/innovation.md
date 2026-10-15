# Innovation — #44

## User Input / seed
Sensemaking's qualified-observation contract and decomposition P1–P4. Gap: the source reader hides evidence needed to explain bounded statistics. Value: reusable truthful measurements without an analytics platform.
Inherited methodology: Standard default, production-task seed. Alternative: Contrarian-rethink would focus on eliminating collection or arithmetic from tgdata. Decision: Standard default with all seven mechanisms and explicit inversions of every meta-decision. Full coverage retained.

## Generate before testing
All four pieces are meta-decisions (contract/evaluation criteria). No piece commits to a methodology intervention-shape vocabulary; property(v) does not fire.

| Piece | Generic candidate | Focused candidate | Contrarian / inversion candidate |
|---|---|---|---|
| P1 | G1 general analytics observation schema with configurable units/timezones | F1 separate v1 immutable raw-message measurement, UTC, optional counters and explicit coverage | C1 no new value: extend Batch v1 and derive all evidence from existing records |
| P2 | G2 generic paginated history stream exposing every TL page | F2 small direct GetHistory loop inside the existing owned operation, bounded slots and checked decreasing offsets | C2 no collector: only summarize caller-supplied messages; alternatively use iter_messages exhaustion as end |
| P3 | G3 configurable distribution/ratio/aggregation DSL | F3 fixed descriptive statistics from retained rows, known-value populations, UTC buckets and explicitly qualified rates | C3 no aggregate API: ship raw observations only, apps decide all arithmetic |
| P4 | G4 measurement job engine with resumable snapshots and storage | F4 one public async call using existing verified operation, budget, heartbeat and cleanup | C4 shared persistent client for lower startup cost, no expected-account requirement |

Seven mechanism outputs:
- Lens L1: evaluate partial results as useful observations rather than failed censuses; return capped data with coverage false, reserve exceptions for actual failures.
- Combination B1: join raw source evidence with immutable descriptive statistics; self-explanatory output without exposing mutable SDK objects. Generic-scope sources include service messages, broadcast channels and anonymous group posts, not only real-estate chats.
- Inversion V1: instead of “read until enough useful messages”, cap all source slots. Further inversion: not “statistics must be complete”, but “the output must explain incomplete evidence”. Existence axis C2/C3 eliminates collector/arithmetic; identity axis F1 treats result as observation rather than snapshot.
- Constraint ADD A1: only UTC buckets, raw messages and a closed publication window; remove ambiguous user-configurable modes.
- Constraint REMOVE R1: remove immutable historical-snapshot expectation; permit observation during an interval. Removing the source cap instead yields R2 unlimited census.
- Absence N1 patch: add availability populations and source stop evidence. Redesign N2: explicit independent coverage and metric completeness. Already-present inverse: owner/admission/progress mechanics exist; don't build another engine.
- Domain D1: import missing-value populations from descriptive statistics; native computing source: pagination cursor/progress invariants and immutable value serialization. Adapt by making source visibility explicit; no statistical random-sample confidence intervals.
- Extrapolation E1: future sampling/repeated audits benefit from IDs, publication/observation times and raw counters; keep these now, defer archive/trend machinery until requested.

Inherited-frame audit: separate schema challenged C1; bounded collection challenged C2/R2; qualified arithmetic challenged C3; owned call challenged C4. Seed assumption “native collection is needed” challenged C2. No unchallenged commitment; no override needed.

## Five-test log
N=novelty relative to this project, S=scrutiny, F=fertility, A=actionability, I=independent grounding. A failure ends candidacy; later cells are recorded where informative.
| Candidate | N | S: strongest objection and result | F | A | I / disposition |
|---|---|---|---|---|---|
| G1 | yes | modes multiply unresolved denominators; too broad now | yes | weak | no / reject scope |
| F1 | yes | another schema costs maintenance; strict batch keys and missing counters justify separation | yes | yes | batch validation + source facts / ACTIONABLE |
| C1 | no compatible route | strict v1 keys/hash reject extension; v2 migration is unnecessary | yes | costly | reject |
| G2 | yes | public stream exposes lifetime/cleanup and paging protocol callers don't need | yes | costly | defer until another collector needs it |
| F2 | yes | duplicate iterator behavior; limited raw paging preserves exactly the evidence iterator discards | yes | yes after prebuild | SDK source + vendor pagination + cap requirement / ACTIONABLE conditional |
| C2 | partly | caller messages cannot establish source completeness; iterator cannot reveal placeholders | useful helper | yes | reject as full #44 delivery |
| G3 | yes | configurable formula language adds unsupported semantics | yes | costly | reject scope |
| F3 | yes | incomplete rates may mislead; expose observed counts always, full-window rates only when complete | yes | yes | missingness math + consumer defects / ACTIONABLE |
| C3 | no | omits requested reusable counts/daily statistics; pure internal arithmetic gives small surface | low | yes | reject |
| G4 | yes | resumability doesn't create a snapshot and duplicates existing progress | yes | costly | reject |
| F4 | partly reuse | startup overhead is real but known owner/admission semantics avoid stale identity | yes | yes | verified-operation and budget fixtures / ACTIONABLE |
| C4 | no | stale cached ownership and policy mutation reintroduce #7 failure class | low | yes | reject |
| L1 | yes | users may ignore flags; names/docs and null full-window rates prevent silent promotion | yes | yes | cap requirement + counter observations / ACTIONABLE |
| B1 | yes | duplicate aggregates could drift; derive solely from immutable rows | yes | yes | independent serialization and deterministic arithmetic / ACTIONABLE |
| V1 | yes | sparse windows may hit cap early; that is honest charged work, not an error | yes | yes | budget admission + raw placeholders / ACTIONABLE |
| A1 | useful focus | UTC-only excludes local days; explicit current scope permits caller re-bucketing portable rows | yes | yes | dates/order and consumer ambiguity / ACTIONABLE |
| R1 | yes | observation weaker than snapshot; source offers no freeze, disclose interval | yes | yes | RPC behavior + counter clocks / ACTIONABLE |
| R2 | no useful change | unlimited scan violates bounded request and budget contract | low | no | reject |
| N1/N2 | yes | several flags can confuse; one coverage_complete plus stop_reason/unknown count, per-metric known count | yes | yes | source evidence + missing-value math / ACTIONABLE |
| D1 | adaptation | implies sampling inference? explicitly descriptive only; null when population empty | yes | yes | mathematical denominator and wire optionality / ACTIONABLE |
| E1 | yes | overdesign for #45? IDs/dates/counters already requested; no persistent archive | yes | yes | issue44 + audit consumer / ACTIONABLE limited to raw facts |

Artifact grounding: v1 strict keys in message_batch.py, raw source rows in TL/SDK, verified temp lifecycle in account_operation.py, budget_client actual-send interception and heartbeat_scope support reuse. No invented missing orchestration. Shared-input check: ownership arguments arise from #7 tests; evidence arguments arise independently from iterator and vendor response contracts; arithmetic arises from optional counters and denominator math. Invert shared assumption “one result should contain everything”: caller can reanalyze to_dict; no public analysis framework is necessary.

## Assembly and remaining choices
Select F1+F2+F3+F4 with L1/V1/A1/R1/N1/D1/E1. Public `measure_group_activity(target, *, account_id, start_date, end_date, max_messages=3000, heartbeat=None)` returns a versioned immutable GroupActivity. `max_messages` explicitly means examined raw source slots, including service/empty/out-of-window rows; each request limit is remaining capacity capped at100. No downloads/joins/stores/full-profile dependency. Raw ordered pages preserve unknown slots and validate monotone IDs/dates; a below-start witness or genuine source-end can establish coverage only without unknowns. Half-open bounds apply locally after conservative upper seek. Ordinary failures preserve their type and attach validated partial observations best effort.

Statistics: count ordinary/service separately; distinct visible user IDs and channel-author IDs separately; unknown sender count; latest observed ordinary message; per-UTC-date ordinary counts/authors with exact intersected exposure; per-counter known/missing counts, sum/mean/median/min/max. No engagement ratio (undefined denominator and business assumptions). A complete-window message rate per24h may be supplied with exposure denominator; no ambiguous mean daily unique-users value. All current counters concern publications in window, not reactions accrued in window.

Axes covered: capture shape (G2/F2/C2), representation (G1/F1/C1), interpretation breadth (G3/F3/C3), lifetime (G4/F4/C4), completeness ambition (L1/R1/R2), denominator/unit (A1/D1). Emergent value: bounded data is useful without asserting that its partial summary describes a whole group. No survivor contradicts a committed choice without re-test; C1/C2/C3/C4 explicitly retest the inherited form. Four piece logs: P1 combination/absence/inversion/domain; P2 lens/constraint/inversion/domain; P3 combination/inversion/domain; P4 absence/inversion/extrapolation. All four inversion requirements satisfied. Every assembled element traces to a tested candidate.

Telemetry:4/4 generators,3/3 framers; full three-variation set for each meta-decision; both constraint directions and absence levels; native and different-domain transfer; all survivors five-tested. Six failure modes checked, no omitted contrarian. Convergence YES on qualified bounded observations, with multiple artifact grounds. Manual structural check seed/generate/test/assembly/telemetry PASS. PROCEED to critique; real-component feasibility remains unproven until prebuild.
