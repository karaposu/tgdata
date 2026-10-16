# Structural critique — #45

## User Input
Evaluate innovation.md's candidates against sensemaking.md and the four-articulation _branch.md. Contract inquiry only; the later implementation plan still requires critic-d and real-component prebuild.

## Phase 0 — dimensions, weights and frame premises
Critical: T temporal usefulness (older days have deliberate acquisition opportunity), E truthful evidence (source gaps versus selection omissions), R reproducibility (same captured input/decisions select same original IDs), O owner/admission/outcome preservation. High: C existing batch/post/progress compatibility; B finite source/output/reload work; F feasible implementation on actual SDK. Medium: U caller usability and narrow API. Cosmetic preferences low. Each critical failure defeats the requested feature; lack of a speculative strategy registry does not.

External-anchor criteria require actual consumer behavior, SDK/source interfaces and current library contracts, not internal agreement. Source documents preserve unknown album membership and raw receipts. Substance checks must apply the chosen formulas and budgets literally, including empty days and a sample smaller than its album.

Independent inherited-premise prosecutions:
1. What if newest-first capture already suffices? With a recent day exceeding the source cap, no later selector can expose an earlier day. Consumer requirement “spread evenly across the days” and a constructed busy-day case independently reject this premise.
2. What if selected rows suffice for replay? A different eligibility decision over omitted text cannot be evaluated from selected rows. The requested same-captured-input domain needs the input retained somewhere, but not a library database.
3. What if raw-message selection violates post preservation? Existing TelegramPost explicitly says `membership="unconfirmed"`; its raw originals are independent IDs. Raw selection can meet #45 only by identifying its unit and reporting known omitted members, never calling the result whole posts. Atomic-post mode remains a distinct possible future contract, not silently supplied now.
Failure-plane check: resource accounting includes zero-result calls; replay validation includes metadata consistency, not only a content hash; preserved account policy covers cleanup/failure as well as successful source sends.

## Phase 1 — landscape
Viable: bounded day-distributed capture plus local deterministic raw selection with explicit omissions and retained input. Dead: newest-only acquisition marketed as period spread, output-only replay claims, hidden predicates/LLMs, unbounded empty-day loops, cursor/ack reuse. Boundary: atomic post sampling, randomized/proportional registries and persistent archives; useful under different explicit requirements but not necessary here. External qualification frontier: actual live visibility and SDK composition before product work.

## Phases 2–3 — adversarial candidate log
| Candidate | Prosecution | Defense | Collision / verdict with constructive direction |
|---|---|---|---|
| G1 archive | Introduces durable ownership and recovery outside scope | Makes replay persistent | KILL C/U; seed caller-saved portable capture |
| F1 capture + local sample | Two actions cost caller effort; reload could accept internally contradictory metadata | Retained evidence is the only way to change local selection without rereading | SURVIVE R/E/U with strict bounded value validation; derive counts/coverage from consistent facts rather than trusting duplicate flags |
| C1 selected-only | Cannot re-evaluate omitted content | Smallest return | KILL R; retain input separately from bounded sample output |
| G2 strategy engine | Generic scheduling adds new policy authority | Flexible future allocation | KILL scope/U; seed one named deterministic policy |
| F2 day rounds | A tiny cap cannot visit every day; sparse days could strand capacity | Even-spaced subset/explicit unvisited states and repeated rounds give bounded opportunity | SURVIVE T/B; no promise every day contributes when caps cannot support it |
| C2 newest-only | Busy newest day starves the rest | Reuses current window walk | KILL T; source breadth must precede deeper scanning |
| G3 registry | Many units/distributions expand proof obligations | More choices | KILL U for now; revive with a concrete alternate-policy caller |
| F3 raw equal-day/rank | Can split known albums and overrepresent quiet days | Explicit raw units/album omissions and descriptive-only claims make exact behavior reviewable | SURVIVE E/R/C; label bias and keep originals unchanged |
| C3 atomic albums | One ten-member album cannot satisfy a one-message cap; a partial capture still lacks global members | Strong observed-unit preservation | KILL as default C/B; seed later separate unit/member limits and explicit underfill |
| G4 whole-reader refactor | Unrelated batch/progress callers acquire migration risk | One theoretical engine | KILL C/F; extract only truly common raw page validation |
| F4 narrow shared validation | Sampling may accidentally inherit activity-only counter rules | Shared structure plus separate projection preserves both semantics | SURVIVE C/F; preserve #44 behavior with full parity and mixed-projection prebuild |
| C4 pure batch helper only | Does not acquire across days or expose honest source coverage | Small pure functionality | KILL task completeness; retain pure selection without pretending it solves source work |
| L1 reading heuristic | “Balanced” could be read as representative | Explicit descriptive contract | SURVIVE E/U; never supply a statistical inference claim |
| B1 captured eligibility | Caller could pass IDs from another capture | IDs must be existing ordinary captured members; validate and normalize before selection | SURVIVE R; no side-effectful callback in the live operation |
| V1 opportunity policy | Round truncation creates unequal observations | Inequality is bounded and visible at each bucket | SURVIVE T/E; document exact subset/tie rules |
| A1 two actions/UTC/raw | Extra action less convenient than one call | Clear lifecycle and local failure boundary | SURVIVE U/O; concise public example keeps it usable |
| R1 no archive | Discarding input loses replay | Caller controls retention explicitly | SURVIVE C/R; no replay claim after discard |
| R2 no request cap | Empty days allow many calls without consuming message cap | Fewer knobs | KILL B; preserve separate finite logical history-call bound |
| N1/N2 evidence split | Redundant summary fields could contradict saved facts | Separate authorities make validation possible | SURVIVE E; loader recomputes derived totals/coverage and rejects conflicts |
| D1 equal opportunity | Uniform days distort traffic frequency | This is a reading set, not a frequency estimate | SURVIVE T/E with explicit bias |
| E1 future local analysis | Could expand into an analytics framework | Text/IDs/policy already required for replay | SURVIVE R/C only for present portable facts |

User-perspective objection: “I asked for300 useful messages, not an archive API.” The capture is a bounded immutable value, not a service; one local sample method returns at most300 bodies. Caller topic rules can filter that retained content without extra Telegram work. A short capture may legitimately produce fewer than300; the result explains why.

Literal arithmetic probe executed during this pass:
```text
{'case': '599/300', 'old_first_last': [0, 299], 'new_first_last': [0, 598], 'unique': 300}
3160 n/k rank-spacing combinations satisfy size, uniqueness and bounds
This is arithmetic evidence only; SDK/day acquisition is reserved for combined prebuild
```
The probe applies the candidate's integer formula directly. It is not evidence of live Telegram or complete acquisition. Source anchor: actual SDK `_MessagesIter` drops MessageEmpty before yielding and warns that `len(r.messages) < req.limit` is unsafe as a stop rule. Current batch raw-record validation supplies content structure; current activity page validation supplies structural source checks. Raw receipt and post membership meanings are independently documented in docs/album_assembly.md and docs/photo_trails.md.

## Phase 3.5 — assembly collision
Assembly: portable capture + bounded day rounds + pure equal-day/rank selection + existing owned lifecycle. Prosecution: a later day may repeat an ID already captured with a changed publication date; a failed load could silently invent empty input; invalid metadata could label unvisited days complete. Defense: exact fixed day membership, cross-capture unique IDs, page-atomic acceptance, strict reload and derived coverage/count consistency are part of the evidence contract, not a new state machine. Collision: SURVIVE with those explicit consistency obligations carried into the description/plan. No implicit deduplication of conflicting observations or replacement of missing input is permitted.

## Phase 4 — coverage and convergence
First evaluation iteration screened every candidate, then applied E/R/B/O/C/F/U to the survivors and identified saved-evidence consistency obligations. Second evaluation iteration attacks the assembly with: zero-result days under max_requests; size0/small size; more days than work slots; same album across day boundaries; repeated IDs with changed dates; eligibility excluding all rows; late source failure after earlier completed days. These remain in the already mapped resource/evidence/unit/replay/outcome regions and are handled by the same explicit contract, not additional architecture. No new candidate region or unresolved conceptual refinement remains. Real SDK composition remains the required prebuild, not an asserted runtime PASS.

Accumulator: all verdicts/kill seeds in table; consistency obligations resolved within the surviving contract; mechanism_independence_status=validated by consumer source, SDK source, current value/assembly contracts and arithmetic output. Coverage spans acquisition, retention, selection, units, eligibility, bounds and lifecycle. The first articulation supplies native source breadth; second supplies replay separation; third is explicitly declined as initial unit; fourth contributes raw record reuse but its envelope-only architecture is rejected. No variant silently dropped.

Signal: TERMINATE contract inquiry, ranked survivor1 the selected assembly; survivor2 its independently useful local selector. Two evaluation iterations stable, new-information rate reduced, no unexplored in-scope region likely to replace the survivor. Fresh critic-d/prebuild still required before implementation. Telemetry: all dimensions covered, adversarial strengthSTRONG, landscapeSTABLE, clean contractSURVIVE. All nine documented failure modes checked. Manual phases0/1/2/3/3.5/4 and telemetry PASS. PROCEED to Routelister.
