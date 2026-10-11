# Route map — worker contract concepts

## User Input

Territory: this inquiry's _branch.md and six saved discipline outputs.
Goal: an actionable worker-boundary decision covering the four jobs, account/job
ownership, failure semantics and empirical premises for laptop/server use.

## Map Header

Root/project-space breadth; fresh index. 14 identities; 9 high-priority;
10 core (including one deployment-phase core). Attributes describe the
routes; ordinals are identifiers, not a ranking or a selection.

## Route Index

| # | Direction | Engagement | Priority | Essentiality | ✓ |
|---|---|---|---|---|---|
| 1 | Request framing and correlation | DEVELOP | HIGH | core | |
| 2 | Verified account inventory | DEVELOP | HIGH | core | |
| 3 | Existing allowance authority | DEEPEN | HIGH | core | |
| 4 | Cleanup failure knowledge | DEVELOP | HIGH | core | |
| 5 | Process I/O and termination | TEST | HIGH | core | |
| 6 | Exact result projection | DEVELOP | HIGH | core | |
| 7 | Correlated health collection | DEVELOP | HIGH | core | |
| 8 | Unknown completion and join retries | REFINE | HIGH | core | |
| 9 | Caller integration example | DEVELOP | MEDIUM | supporting | |
| 10 | Compatibility of existing library paths | TEST | HIGH | core | |
| 11 | Network service transport | INVESTIGATE-FRONTIER | LOW | peripheral | |
| 12 | Durable worker receipts | INVESTIGATE-FRONTIER | LOW | peripheral | |
| 13 | Per-job process isolation | TEST | LOW | peripheral | |
| 14 | Live account qualification | TEST | MEDIUM | core · @deployment | |

## W01 — Request framing and correlation

Type: project-space × teleological × DEVELOP.
Goal: the worker-boundary decision stated above.
Move: Specify strict versioned bounded jobs and process-local request identities.
Lands: A caller can correlate outcomes and distinguish invalid input from executed work.
WHY: The worker goal needs an unambiguous boundary rather than an implicit queue.
Priority: HIGH. Confidence: HIGH. Essentiality: core.
Guidance Mode: compact.
- Use Q1 and F1 (bc they separate correlation from durable acceptance).
Meaning-gaps:
- Exact field limits and invalid-frame handling — [mid] — the protocol must be reproducible.
Depth-link: none; no separate depth run.

## W02 — Verified account inventory

Type: project-space × teleological × DEVELOP.
Goal: the worker-boundary decision stated above.
Move: Bind each declared account to trusted configuration and fresh authenticated proof.
Lands: Every job has one accountable owner and one session lifetime.
WHY: The goal fails if the named account differs from the one that acts.
Priority: HIGH. Confidence: HIGH. Essentiality: core.
Guidance Mode: compact.
- Use the source composition probe (bc cached111/actual222 is already tested).
Meaning-gaps:
- Startup alias detection and external exclusive assignment wording — [mid] — ownership must not be implicit.
Depth-link: none; no separate depth run.

## W03 — Existing allowance authority

Type: project-space × teleological × DEEPEN.
Goal: the worker-boundary decision stated above.
Move: Carry read and join allowance rules into the worker configuration contract.
Lands: Jobs use existing ledgers without reset or an unlimited fallback.
WHY: Reusable worker execution must retain account protections.
Priority: HIGH. Confidence: HIGH. Essentiality: core.
Guidance Mode: compact.
- Use current ReadBudget/JoinBudget contracts (bc their admission semantics are already authoritative).
Depth-link: none; no separate depth run.

## W04 — Cleanup failure knowledge

Type: project-space × teleological × DEVELOP.
Goal: the worker-boundary decision stated above.
Move: Expose the settled cleanup failure fact to successor admission.
Lands: Unsafe cleanup stops further worker source work while preserving the source result.
WHY: The goal needs safe reuse rather than a misleading normal return.
Priority: HIGH. Confidence: HIGH. Essentiality: core.
Guidance Mode: compact.
- Use cleanup_candidate.py (bc it includes setup, SDK cancellation, caller cancellation and broken diagnostics).
Meaning-gaps:
- Final worker consumption of the private fact — [mid] — a produced fact alone does not enforce admission.
Depth-link: none; no separate depth run.

## W05 — Process I/O and termination

Type: project-space × epistemic × TEST.
Goal: the worker-boundary decision stated above.
Move: Exercise EOF, bounded frames, blocked output and signals across idle and active work.
Lands: The chosen process contract is supported by real pipe/task behavior.
WHY: The goal includes a worker that can stop without silently detaching reads.
Priority: HIGH. Confidence: HIGH. Essentiality: core.
Guidance Mode: compact.
- Use process_boundaries.py and the proposed serial driver (bc a cancelled executor await did not end stdin ownership).
Depth-link: none; no separate depth run.

## W06 — Exact result projection

Type: project-space × teleological × DEVELOP.
Goal: the worker-boundary decision stated above.
Move: Project identifiers as decimal strings and preserve raw batches and group statuses.
Lands: The consumer receives exact source meaning across JSON.
WHY: A working worker must not round large query IDs or flatten denied/requested outcomes.
Priority: HIGH. Confidence: HIGH. Essentiality: core.
Guidance Mode: compact.
- Use wire_ids.py and source to_dict contracts (bc actual Node parsing demonstrated numeric loss).
Meaning-gaps:
- Complete identifier-field inventory — [mid] — projection must cover health, group and error metadata consistently.
Depth-link: none; no separate depth run.

## W07 — Correlated health collection

Type: project-space × teleological × DEVELOP.
Goal: the worker-boundary decision stated above.
Move: Collect bounded plain health facts against their originating job before publication.
Lands: Notifications remain separate from source outcomes and cannot acquire the next job label.
WHY: The goal requires health events without reintroducing the reviewed ownership failures.
Priority: HIGH. Confidence: HIGH. Essentiality: core.
Guidance Mode: compact.
- Use the owned-health post-cleanup probe (bc notification dispatch is deferred).
Meaning-gaps:
- Exact drain and signal behavior — [mid] — cancellation must not relabel or fabricate facts.
Depth-link: none; no separate depth run.

## W08 — Unknown completion and join retries

Type: project-space × epistemic × REFINE.
Goal: the worker-boundary decision stated above.
Move: State what a missing reply means for a read and for a potentially completed join.
Lands: Callers make explicit recovery decisions without automatic mutation replay.
WHY: The worker goal depends on honest uncertainty at irreversible source boundaries.
Priority: HIGH. Confidence: HIGH. Essentiality: core.
Guidance Mode: compact.
- Use Q1/A2 and qualified GroupJoin outcomes (bc a pipe has no transaction with Telegram).
Depth-link: none; no separate depth run.

## W09 — Caller integration example

Type: project-space × teleological × DEVELOP.
Goal: the worker-boundary decision stated above.
Move: Demonstrate startup, account inventory, one request, health frames and terminal result handling.
Lands: A consuming app can use the protocol without hidden scheduling assumptions.
WHY: The goal becomes easier to adopt with a concrete caller pattern.
Priority: MEDIUM. Confidence: HIGH. Essentiality: supporting.
Guidance Mode: compact.
- Use F1/F3 caller-managed transport (bc readers must drain output as well as send input).
Meaning-gaps:
- Example verbosity and packaging form — [low] — these are reversible presentation choices.
Depth-link: none; no separate depth run.

## W10 — Compatibility of existing library paths

Type: project-space × epistemic × TEST.
Goal: the worker-boundary decision stated above.
Move: Run existing account/group/batch/budget checks with the additive worker hooks.
Lands: Ordinary callers retain their documented results and cleanup precedence.
WHY: The general-library goal cannot be met by breaking existing consumers.
Priority: HIGH. Confidence: HIGH. Essentiality: core.
Guidance Mode: compact.
- Use suites12–19,22–30,32–36 (bc these are the supported offline current-dev boundaries).
Depth-link: none; no separate depth run.

## W11 — Network service transport

Type: project-space × teleological × INVESTIGATE-FRONTIER.
Goal: the worker-boundary decision stated above.
Move: Examine an authenticated remote transport when a network consumer is specified.
Lands: The additional service duties are explicit instead of silently bundled into execution.
WHY: Indirect: a later remote interface can help deployment without changing source ownership.
Priority: LOW. Confidence: MEDIUM. Essentiality: peripheral.
Guidance Mode: compact.
- Use G1/V2 (bc the consumer/authentication contract is currently unspecified).
Depth-link: none; no separate depth run.

## W12 — Durable worker receipts

Type: project-space × teleological × INVESTIGATE-FRONTIER.
Goal: the worker-boundary decision stated above.
Move: Examine whether an explicitly requested durable job/output store has a distinct caller benefit.
Lands: Any added acceptance/retention authority is justified and bounded.
WHY: Indirect: persistence may help a future consumer but is not required by the selected small worker.
Priority: LOW. Confidence: MEDIUM. Essentiality: peripheral.
Guidance Mode: compact.
- Use C1/C4/V3 (bc they add an owner the current orchestration already supplies).
Depth-link: none; no separate depth run.

## W13 — Per-job process isolation

Type: project-space × epistemic × TEST.
Goal: the worker-boundary decision stated above.
Move: Test OS child isolation if uncooperative task/plugin lifetime becomes a real requirement.
Lands: Isolation costs and result custody are measured for that stronger boundary.
WHY: Indirect: stronger isolation can matter later without burdening the current cooperative worker.
Priority: LOW. Confidence: MEDIUM. Essentiality: peripheral.
Guidance Mode: compact.
- Use C2 (bc its strength is process-owned resource termination, not a smaller protocol).
Depth-link: none; no separate depth run.

## W14 — Live account qualification

Type: project-space × epistemic × TEST.
Goal: the worker-boundary decision stated above.
Move: Exercise the final worker with explicitly approved live account/group and bounded allowance.
Lands: Deployment claims have live evidence distinct from synthetic SDK/process tests.
WHY: The deployed-worker goal requires real source qualification, even though offline implementation can proceed.
Priority: MEDIUM. Confidence: MEDIUM. Essentiality: core · @deployment.
Guidance Mode: compact.
- Use the explicit authorization/ledger boundary (bc old live permissions do not silently authorize new tests).
Depth-link: none; no separate depth run.

## Excluded

Merge gates and iteration control are process decisions, not concept directions.
Editing/deletion reconciliation does not advance the selected raw-job worker goal.
No generic credential-rotation framework is listed: this territory supplies no
shared-owner requirement that would justify that separate concept here.

## Telemetry

14 identities; 9 teleological and 5 epistemic;
9 high-priority; 10 core, one supporting, three peripheral.
Two sweeps: the second found no new identity. No stale entries, uncertain merges
or omitted frontier region. Six operational modes and four identity modes checked:
no over-merge, undercoverage, wrong grain, goal loss, type error, index drift,
selection/process creep, descriptive collapse or manifestation dump.
Both route map and within-concept index saved. **Verdict: PROCEED.**
