---
model: gpt-6-astra
effort: max
---
# Critique — Stage4 allowance contract

## User Input

Evaluate all17 candidates from innovation.md plus their proposed assembly against
sensemaking.md, decomposition.md and _branch.md. The user's exact boundary is “Stage 4
only; review and merge before Stage 5 (Recommended)”. This is the inquiry critique,
not task-plan's later critic-d or an implemented PR review.

## Phase0 — Dimensions, weights and success criteria

| Dimension | Weight | Source / substance-level passing criterion |
|---|---|---|
| D1 Admission meaning | Critical | S.A1/A2/A5: one durable consumed unit before permission; no guessed refunds or status grants |
| D2 State custody/integrity | Critical | S.A4/Q2: explicit creation versus known-state open; absent/malformed history cannot become free capacity |
| D3 Time/policy coherence | Critical | S.A3/A6/A7: one transactional policy/time/count view; updates preserve claims; expiry and rollback are explicit |
| D4 Staged ownership/coherence | Critical | User boundary and merged handle: no Stage5 guard now; ledger claims are local and do not invent verified identity/health |
| D5 Extent and usability | Important | User concern about overengineering: smallest sufficient surface; no token/workflow/general quota machinery without current need |
| D6 Feasibility/compatibility | Important | Current Python/SQLite/runtime: ordinary local transactions and existing public conventions; no unqualified backend dependency |
| D7 External evidence | Critical for empirical claims | Actual source/probe outcome must support component claims; no supplied success or borrowed test total as new qualification |

Failure on D1–4 prevents an allowance doing its job. A naming/convenience issue on D5/6
alone does not justify killing a sound bounded design. D2 is the project-specific risk
axis exposed by silent schema repair; it includes record validity, not just table names.
All sensemaking perspectives map to these dimensions. No metric rewards new abstractions.

### Inherited-frame prosecution

- If admitted attempts were the wrong unit, a membership-success counter could serve
  the task better. Test independently: timeout/cancellation lacks proof of remote effect;
  Stage4 has no source observation. No mechanism makes outcome-only accounting a bound.
- If durability were unnecessary, a process counter would be sufficient. Test independently:
  separate processes and restart create independent counters; the actual process probe
  demonstrates the durable before/after-commit distinction that a memory-only design lacks.
- If a new implementation were unnecessary, ReadBudget wrapping should win on extent.
  Test actual code: its initialization/refund/warmup contract differs, and making strict
  known-state opening safe would require changing that accepted module or bypassing it.

These prosecutions challenge the frame separately from whether a particular candidate
is well presented. The user's staged boundary is directly applied to4G, not paraphrased
into generic caution. No scope change is needed to resolve the conceptual question.

## Phase1 — Fitness landscape

**Viable:** small local typed surface + explicit provisioning/existing-state access +
atomic nonrefundable unit claims + narrow documented Stage5 seam + real storage evidence.
**Dead:** grants from status, source-success-only accounting, automatic restoration of
missing history, reusable claim tokens without source lifecycle, process-only counters,
and borrowed/fake evidence as complete qualification.
**Boundary:** auto-init with only partial-schema detection; shared quota framework;
external backend protocol; immediate client wiring; pure helper tests as a supplement.
**Unexplored:** distributed storage implementations and live joining outcomes/rate safety.
They are outside this stated delivery and cannot be silently promoted into its guarantees.

## Phases2–3 — Candidate prosecution, defense, collision and output

### 1G — Generic quota facade
**Prosecution:** D4/D5 fail: joins inherit read settlement and warmup or add branches to
an already accepted read subsystem. **Defense:** a common API could reduce future drift.
**Collision:** no present common lifecycle or second new consumer justifies the rewrite.
**KILL for this stage.** Seed: seek shared primitives only after actual consumers exhibit
identical transitions. The broader idea remains a research frontier, not a dependency.

### 1F — Small standalone ledger/status/errors
**Prosecution:** D5 duplication could grow two subtly different accounting implementations.
**Defense:** the local unit, error and nonrefundability contract is independently clear;
source identity and dispatch are elsewhere. **Collision:** shared patterns, focused tests
and no inherited refund surface keep extent bounded. **SURVIVE**, strong D1/D4/D5/D6;
D7 grounds its feasibility, while actual new methods still need implementation tests.

### 1C — Wrap ReadBudget
**Prosecution:** D2/D4 fail: actual ReadBudget initializes missing tables and owns message
reservation/settlement; a wrapper cannot atomically preflight around that constructor.
**Defense:** reuse avoids duplicated SQL and preserves existing competition machinery.
**Collision:** repairing all required seams expands into excluded existing behavior or
private-state construction. **KILL.** Seed: reuse transaction knowledge, not an incompatible
public lifetime. Code evidence, not preference for new classes, breaks the tie with1F.

### 2G — Auto-init with partial-table guard
**Prosecution:** D2 still admits whole-file recreation as an ordinary startup path.
**Defense:** explicit account configure prevents an entirely unconfigured grant and is
convenient on first use. **Collision:** repeated startup configure makes missing known
state indistinguishable from fresh setup. **REFINE →2F**, by requiring creation intent;
no remaining independent role for default auto-init in the selected assembly.

### 2F — Explicit provisioning/existing-state opens
**Prosecution:** checking only tables/version still lets malformed claim timestamps be
pruned into free capacity or treated as legitimate future usage. Missing schema is not
all detectable damage. **Defense:** Q2 already requires stored-value validation before
mutation/pruning; the proposed custody boundary can contain it without another component.
**Collision:** **REFINE2F-R**, making Q2's predicate concrete: validate current account's
stored cap/clock and attempt time types/ranges/coherence **against its prior stored clock**
before advancing time or pruning. Validate required schema/version/columns and refuse
partial state even during explicit create. No automatic repair. Second pass below accepts
this refinement within the existing small module; no new lifecycle or backend is added.

### 2C — External backend only
**Prosecution:** D6/D7: a protocol alone supplies neither the local durable result nor a
qualified backend. **Defense:** a future web app may need central shared storage.
**Collision:** **KILL as this delivery**, preserving research seed: when a concrete second
backend is required, specify its atomic/error contract and qualify it rather than adding
an unused protocol now. A local first delivery can survive later backend extraction.

### 3G — Reservation/settlement/recovery lifecycle
**Prosecution:** D1/D4: a reused local grant can authorize another source attempt unless
source lifecycle is also tracked; that is Stage5-or-beyond work. **Defense:** named receipts
can recover a committed claim whose return was lost. **Collision:** avoiding occasional
stranded allowance does not justify new mutable states and uncertain source coupling.
**KILL.** Seed: keep lost-return evidence and conservative charges, without token replay.

### 3F — One synchronous nonrefundable admission
**Prosecution:** a storage error after a real commit may make the caller believe nothing
was consumed; delayed commit/cleanup could accidentally return permission early.
**Defense:** the contract explicitly grants nothing on errors and waits until the local
operation completes; the durable unit may remain. No source behavior is inferred.
**Collision:** **SURVIVE**, D1–4/D6 strong, with D5's deliberate under-utilization tradeoff.
D7 actual commits/process exits ground the mechanics; tests must exercise the new wrapper.

### 3C — Charge successful membership after acting
**Prosecution:** D1 fails on lost/cancelled replies, and source outcome lives outsideStage4.
**Defense:** accurate retrospective success analytics avoids charging harmless failures.
**Collision:** that is a different product promise. **KILL.** Seed: successful-membership
metrics may be useful separately; they cannot replace an admission cap.

### 4G — Add factory guard now
**Prosecution:** D4 violates the user's exact Stage4-only/staged-merge boundary; partial
wiring can also falsely suggest existing clients are protected. **Defense:** it anticipates
a real next consumer and could save later wiring work. **Collision:** **KILL in this run**,
with explicit revival seed for Stage5 after review/merge. A valid next step is not a valid
current scope expansion.

### 4F — Document verified consumer obligations
**Prosecution:** docs cannot enforce future sends or prevent a caller abusing a private API.
**Defense:** it correctly locates authority: supplied account key here, fresh proof and
per-attempt dispatch in Stage5. Current code supplies that handle mechanism already.
**Collision:** **SURVIVE**, D4/D5 strong, without claiming enforcement that is not yet built.
The consume-once, no-status-grant and no-refund obligations are substantive interface facts.

### 4C — Defer all consumption meaning
**Prosecution:** D1/D4: future work would have to guess identity, retry and permission rules,
reintroducing the hidden prerequisite the user wanted eliminated. **Defense:** fewer docs
could leave flexibility. **Collision:** undefined authority is not useful flexibility.
**KILL.** Seed: retain a short explicit boundary rather than build the sender prematurely.

### 5G — Fakes plus existing regressions
**Prosecution:** D7 fails if supplied persistence/claim success is called backend proof;
old tests did not expose the missing-table repair. **Defense:** pure tests cheaply cover
validation and portable values. **Collision:** **REFINE**, retaining helper tests inside5F
but requiring actual SQLite/process/fault paths for storage and admission claims.

### 5F — Actual storage/process/fault qualification
**Prosecution:** process exits and injected errors could be misrepresented as disk power
failure or all vendor behavior. **Defense:** those limits are explicitly stated; actual
rows, locks, source-method effects and caller exceptions are observed. **Collision:**
**SURVIVE**, D7/D6 strong, with evidence scoped to what runs. This is a test requirement,
not a claim the unbuilt Stage4 public API has already passed.

### 5C — Repackage old evidence only
**Prosecution:** D7 fails: code/contract changed and no new method was exercised.
**Defense:** reusing old coverage can avoid redundant tests. **Collision:** reuse fixtures
and stable baselines, not their verdict for a new component. **KILL.** Seed: measure the
new composition while keeping prior results labeled historical.

### 6D — Ticket analogy
**Prosecution:** it contributes no implementation primitive beyond3F. **Defense:** useful
for explaining lost-return charges. **Collision:** **KILL as a design component**, retain
only the explanatory seed. This is a noncritical novelty/extent decision, not a safety claim.

### 7I — No durable state
**Prosecution:** D1/D2 fail across competing processes or restart. **Defense:** very simple
for a single process's lifetime. **Collision:** wrong accounting domain for this task.
**KILL.** Seed: an optional in-memory preview/simulation could be separate, never the grant.

## Empirical challenge of the integrity predicate

The additional old-ledger probe updated real temporary rows, then invoked its status API:

```json
{"historical_corrupt_time": [{"stored_admitted_at": -100000.0, "stored_clock": 1000.0, "status_used": 0, "remaining": 1, "next_available_at": null}, {"stored_admitted_at": 2000.0, "stored_clock": 1000.0, "status_used": 1, "remaining": 0, "next_available_at": 88400.0}]}
```

A negative invalid timestamp vanished under ordinary pruning; a timestamp beyond the
recorded observation horizon produced a plausible retry time. This substantiates2F-R's
need to validate before normalizing time/pruning. It does not imply the new implementation
already has this bug or that arbitrary valid-looking external edits are detectable.

The reproducible contract_probe.py now loads historical source by git object8a43d23,
removing dependence on a particular old worktree path. Its4 probe groups exited0; the
first3 repeated their prior results. Output is in ../evidence/critique-probe.txt. This
is actual SQLite/historical code plus intentional damage/fault injection, not a mocked
new ledger. No runtime implementation file changed during the inquiry.

## Phase3.5 — Assembly A and second evaluation pass

**A:**1F+2F-R+3F+4F+5F, with5G's pure checks as supplements. A small separate SQLite
ledger with explicit create=False default and deliberate create=True provisioning;
no repair of partial/malformed known state; configured rolling24-hour unit admission;
nonrefundable claims, local typed values/errors and future verified-consumer obligations.

**Prosecution:** partial schema or invalid rows could still be normalized into valid-looking
capacity; transaction cleanup could turn an uncertain grant into success; a general helper
might accidentally claim current Telegram enforcement. These are D2, D1 and D4 respectively.
**Defense:**2F-R fixes validation ordering inside the same transaction and reuses the current
store's open semantics;3F waits for complete local success and errors grant nothing;
4F explicitly leaves source integration with Stage5. Actual primitive behavior is measured.
**Collision:** **SURVIVE A**, with no unresolved critical-dimension caveat at contract level.
Implementation precision belongs in the ensuing plan/critic and actual public-method tests.

Second pass used unchanged dimensions to reapply the concrete negative/future timestamp,
missing namespace, lost-commit-return, simultaneous claim and Stage5-scope counterexamples.
2F-R and A remain viable; the rejected models remain in the same dead/boundary regions.
The refinement specifies an already-required integrity check, not a new architectural
candidate or another full traverse iteration. No new region emerged on the second pass.

## Phase4 — Accumulator, coverage and convergence

**Evaluation log:**17 incoming candidates and assemblyA; all faced prosecution/defense/
collision at their critical axes. First pass identified one concrete integrity refinement;
second pass confirmed it without shifting weights. Four clean focused components survive,
2F survives as2F-R, and A is the complete survivor.2G/5G refinements are absorbed; all
kills include a seed and out-of-scope frontier candidates retain their revival conditions.

**Coverage map:** unit and uncertainty(1/3), custody/validity(2), time/policy(2/3), scope/
identity(4), evidence/compatibility(5), existence of persistence(7), explanatory-only(6)
all examined. Distributed backends/live mutation qualification are outsideStage4, not
unexplored regions needed for this candidate to stand. Current model contains no need
for a hidden new health or source-routing subsystem.

**Mechanism-independence status:** validated for surviving component premises using source
code, user scope and actual SQLite/process results; the new implementation's correctness
is still to be established by its tests. No external-grounding quarantine applies to the
contract decision. Hardware/clock custody remains an explicit operating assumption.

**Convergence:** two consecutive internal evaluation passes place the same final assembly
in the viable region; new information dropped from the specific validation-order refinement
to confirmation. This does not fabricate two traverse runs. Dimension coverage7/7,
adversarial strength STRONG, final landscape STABLE, clean assembly survivor exists.
All9 failure modes checked; no drift, scope substitution or source-evidence overclaim.

**Signal: TERMINATE — ranked survivors:** A first; focused1F/2F-R/3F/4F/5F as its coherent
parts. **Telemetry verdict: PROCEED.** Proceed to Routelister, then compile the contract
finding for task-desc/task-plan. This is not an implementation or merge approval.
