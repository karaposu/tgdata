---
model: gpt-6-astra
effort: max
---
# Innovation — Stage4 allowance design alternatives

## User Input / seed

_branch.md I1 and decomposition.md Q1–Q5, grounded in sensemaking SV6 and the actual
SQLite/process/old-ledger probes. Produce alternatives for the Stage4 contract and
bounded implementation shape; Stage5 joining remains outside the user-confirmed scope.

**Seed:** a durable admission primitive is missing on merged dev, while both useful
patterns and a silent historical schema-repair loophole are visible. The user's valuation
is reliable staged progress and a design that does not grow another broad health system.

**Mode consideration:** inherited Standard default, applied in Production-task mode to
Q1–Q5. Alternative Contrarian-rethink would emphasize deleting the separate ledger or
moving authority to a caller backend; it might expose reuse but could underdevelop the
required concrete delivery. Decision: retain Standard default, with all7 mechanisms,
generic/focused/contrarian candidates at each meta-decision piece, and explicit inversions.
No user instruction narrows mechanism coverage.

## Phase2 — Generate before evaluating

### Q1 — Policy, observation and consumed unit

Q1 commits frame/criteria (properties ii/iv): meta-decision.

**1G — generic; Combination:** combine read-budget concepts into a generic multi-resource
quota facade with configurable windows, warmup, reservation and settlement. Publish a
join-flavored view of that common object. Shape: ADD-CONTENT plus shared REPAIR.

**1F — focused; Lens Shifting:** from caller planning rather than quota-platform design,
provide JoinBudget, frozen JoinBudgetStatus and local errors. Status contains only account,
limit, used, remaining, observation time, next availability and derived retry delay.
A private synchronous claim consumes one unit; no source reply or token crosses it.

**1C — contrarian; Inversion:** reverse “a new allowance needs a new ledger”. Build no
new persistence implementation; wrap ReadBudget and reserve one message-shaped unit,
never settle it. Depth: remove a class → reuse the entire existing accounting system.
Existence-axis: zero new ledger implementations. Identity-axis: allowance is an adapted
read reservation rather than a distinct domain record. This challenges1G/1F directly.

### Q2 — Provisioning and storage custody

Q2 commits validity criteria and REPAIR of old initialization semantics (iv/v): meta-decision.

**2G — generic; Absence Recognition, patch level:** keep default auto-initialization but
add detection of partially missing namespaced tables. It addresses the concrete old
missing-attempts reproduction while preserving familiar first-run convenience.

**2F — focused; Domain Transfer, computing-native:** apply SQLiteSyncStore's explicit-open
pattern to this new surface. `JoinBudget(path, *, create=False, clock=time.time)` reopens
known state; explicit create=True may create the file/absent join namespace. Any existing
partial/unsupported join schema fails. Ordinary methods always use mode=rw. Separate join
tables may share a file with ReadBudget. Shape: REPAIR of custody semantics in new code.

**2C — contrarian; Constraint Manipulation REMOVE / Inversion on intervention shape:**
remove the built-in persistence requirement. Instead of REPAIRing a local schema contract,
use CONTRARIAN-RETHINK: accept an external atomic allowance backend and make the library
only a typed contract. State creation/durability is entirely the consumer backend's job.
System level: storage authority belongs to the application rather than tgdata's local file.

### Q3 — Atomic claim and outcome

Q3 commits admission/safety criteria (iv): meta-decision.

**3G — generic; Combination:** combine backfill-like durable receipt identity with allowance.
Create an idempotent reservation token, then settle, refund or recover uncertain claims.
An operation may reuse a token after a lost return and distinguish pending from consumed.

**3F — focused; Constraint Manipulation ADD:** add “no refunds, no reusable grant token,
no connection beyond the synchronous call”. One BEGIN IMMEDIATE transaction observes
policy/time/usage and consumes one unit; return only after successful commit/cleanup.
Any error grants no permission and may have retained usage. A later call is a new claim.

**3C — contrarian; Inversion:** reverse pre-admission charging: let the future caller act
first and record only its confirmed membership outcome. Component reversal of charge
ordering becomes the system rule that the allowance is a retrospective activity report.
Identity-axis changes what the system regulates; it is not just a different SQL order.

### Q4 — Future consumer boundary

Q4 commits the stage boundary/frame (ii): meta-decision.

**4G — generic; Extrapolation:** as pool/worker consumers grow, install a shared factory
join-budget option and guard middleware now, so every client path can later inherit it.
The candidate pulls the future integration seam forward even without a public join method.

**4F — focused; Absence Recognition, redesign level:** add the missing explicit consumption
contract: Stage5 must freshly verify the owner, claim once per source attempt/retry and
never turn a status read or exception into permission. What already exists in another
form is the verified operation handle and its read-budget re-verification seam; reuse
those later. Stage4 exposes a standalone ledger only, with no misleading TgData option.

**4C — contrarian; Inversion:** reverse “future integration obligations belong here”. Ship
only bare local counter methods and postpone all identity/send/claim semantics until
Stage5. System level: each consumer invents its own relationship between allowance and
source work. This removes the documented boundary rather than adding another mechanism.

### Q5 — Verification evidence

Q5 commits evidence criteria and ADD-TEST shape (iv/v): meta-decision.

**5G — generic; Lens Shifting:** optimize for fast domain-unit feedback: pure fake storage
and deterministic counters test all value and error paths, with existing broad suites
standing in for actual backend qualification.

**5F — focused; Domain Transfer, computing-native:** use crash-consistency testing: public
ledger calls against actual SQLite, spawned processes with barriers, exits before/after
real commits and injected faults around real connection actions. Preserve evidence limits;
no synthetic claim-success helper supplies the result. Shape: ADD-TEST.

**5C — contrarian; Inversion on intervention shape:** reverse ADD-TEST into
REORGANIZE-WITHOUT-ADDING: reorganize existing ReadBudget/old-join evidence as sufficient
coverage, with no new ledger fault suite. The system would rely on a shared pattern's
history rather than measuring the new implementation's actual composition.

### Additional domain and frame alternatives

**6D — Domain Transfer, deliberately different field:** model allowance as a consumed
physical ticket: a lost ticket does not imply it is safe to issue another free one.
This offers a useful analogy for nonrefundability without creating a token API.

**7I — Inversion, persistence existence-axis:** challenge the central persistence premise
with zero durable state: use only a process-memory counter and require consumers to keep
that process alive. This would remove all schema/commit handling from Stage4.

## Inherited Frame Audit (before tests)

Central assumptions: enforceable admissions rather than remote outcomes (challenged3C),
durable state (challenged7I), and a separate local implementation (challenged1C/2C).
Every Q1–Q5 meta-decision has an explicit contrarian:1C/2C/3C/4C/5C. Property-v shape
inversions occur at Q2 (REPAIR→CONTRARIAN-RETHINK) and Q5
(ADD-TEST→REORGANIZE-WITHOUT-ADDING). No generic inapplicability override is needed.

The initial piece variants lacked a direct challenge to persistence itself; audit fired
once and generated7I before testing. User-confirmed Stage4-only scope is not inverted
into permission to implement Stage5:4G is a candidate to evaluate and may be rejected.
No later output or criterion was pre-authored to protect the inherited choice.

## Phase3 — Five-test log

N=novelty relative to this delivery; S=strongest-objection survival; F=fertility;
A=actionability in authorized scope; M=independence of grounds. All generated candidates
enter testing; killed candidates remain visible. Project-state claims receive the
conditional artifact-grounding check as well.

### 1G — Generic quota facade

N: a common abstraction is new. S: read reservations/refunds/warmup and unit join claims
have different semantics; sharing forces per-resource branches and touches accepted code.
F: useful if several future quotas truly share transitions. A: expands this stage and
its regression surface without a present consumer need. M: combination alone favors it;
actual distinct unit/refund contracts push against it. **RESEARCH FRONTIER**, revive only
when another concrete quota consumer demonstrates common lifecycle, not merely common SQL.

### 1F — Dedicated small values and ledger surface

N: new public join allowance, with fewer facts than ReadBudgetStatus. S: separate code
could duplicate storage patterns, but avoids exposing settlement/warmup that joins do not
use. F: enough for Stage5 admission and caller status. A: one small module plus exports,
tests/docs. M: user boundary and irreversible-admission argument independently support it.
**ACTIONABLE**, with simple local errors and no generic policy engine.

### 1C — ReadBudget wrapper, zero new persistence

N: adapting the existing unit is a real alternative. S: its initializer auto-creates
partial tables; fixing custody would require private-constructor bypass, preflight races
or changing ReadBudget. Its reservation/warmup/schema promises also leak into the wrapper.
F: broad reuse possible after a separate shared-store refactor. A: cannot meet this bounded
stage's custody contract without unwanted existing-behavior changes. M: code inspection
and the independent missing-table probe defeat simple reuse. **KILLED for this delivery**.

### 2G — Auto-init with partial-table guard

N: directly closes the reproduced table loss. S: a completely missing known file still
looks like first-use and can receive a newly configured policy, restoring free capacity.
F: familiar consumer startup. A: easy, but weaker custody remains default. M: code and
restart reasoning distinguish it from2F. **REFINED into2F**: convenience only under explicit
provisioning intent, never ordinary reopen. The patch-level absence alone was too narrow.

### 2F — Explicit provisioning and existing-state opens

N: applies the current store's safer lifecycle to a new policy surface. S: an extra flag
costs one-time setup clarity; it blocks accidental missing-state recreation and supports
coexisting table namespaces. F: later callers can reopen without granting fresh usage.
A: direct URI/table validation in a bounded module. M: actual mode=rw refusal, old schema
failure and current SyncStore pattern are distinct evidence. **ACTIONABLE**.

### 2C — External backend only

N: moves ownership of durability out of this library. S: an abstract contract cannot
supply a concrete verified local backend; present users still need implementation and
qualification. F: useful if distributed inventory later demands shared server storage.
A: postpones the asked local delivery and adds backend-contract scope. M: application
separation favors it; current same-host consumers do not require it. **RESEARCH FRONTIER**,
revive for a concrete additional backend with atomic failure semantics and tests.

### 3G — Named reservations and reconciliation

N: introduces lifecycle state/replay. S: replaying a grant is not replaying a network
attempt; after an uncertain source send, reuse could authorize another send for one unit.
Avoiding that requires the source lifecycle that Stage4 excludes. F: richer orchestration
only if such a consumer exists. A: needless receipt/control state for conservative counts.
M: distributed-write analogy suggests it, while the enforced unit and stage boundary
contradict it. **KILLED here**; preserve the lost-return test, not the lifecycle design.

### 3F — Synchronous nonrefundable unit admission

N: a deliberately small contract with no settlement surfaces. S: unused admissions can
be stranded after faults, but this conservatively denies extra work instead of guessing
at source execution. F: clean future per-send composition. A: supported by actual writer
transactions/process evidence. M: failure observability, concurrency evidence and user
staging converge from separate grounds. **ACTIONABLE**. Clock is sampled under the writer
transaction; a refused claim may commit clock/pruning before its local refusal is raised.

### 3C — Act first, charge confirmed memberships

N: reframes allowance as an activity report. S: missing source outcome cannot bound
admitted attempts; it violates the stabilized safeguard the user expects this stage to
provide. F: could be a separate analytics counter. A: requires Stage5 outcome coupling;
not this allowance. M: source-observability and actual post-commit lost-return evidence
reject the inference from failure to “unused”. **KILLED as allowance design**.

### 4G — Pull factory guard forward

N: prepares a future integration. S: a constructor option without a qualified source
boundary can advertise protection prematurely; actually implementing it is Stage5 work.
F: useful next stage. A: outside the user's explicit Stage4-only selection. M: future
consumer trend alone cannot override scope. **DEFERRED**, revival after Stage4 review/merge
when Stage5 is explicitly requested; no Stage4 constructor changes.

### 4F — Explicit consumer obligations, standalone ledger

N: the missing boundary becomes a testable contract. S: docs do not enforce future code;
state exactly that Stage5 must implement/prove it rather than implying protection now.
F: later guard has an unambiguous seam. A: small API/docs surface, no foundation mutation.
M: current verified handle and the independent ledger guarantee fit without new identity
storage. **ACTIONABLE**; old get_me/health.note_account guard is not copied.

### 4C — Omit future obligations

N: saves current documentation/integration thinking. S: leaves the meaning of successful
claim, verified owner and retries to be reinvented, recreating hidden prerequisites.
F: weak; consumers cannot rely on a stable contract. A: easy omission but not completion.
M: no independent requirement supports the ambiguity. **KILLED**.

### 5G — Fake storage plus old regressions

N: enables fast expected-path coverage. S: supplies the persistence/atomicity behavior
being tested; it misses the demonstrated auto-repair loophole. F: useful supplement for
pure validation helpers. A: insufficient as the whole acceptance suite. M: speed alone
supports it. **REFINED** into supplementary pure checks inside5F, not backend evidence.

### 5F — Actual SQLite/process/fault acceptance

N: new component composition tested rather than assumed. S: process exits do not prove
power-loss behavior; injected faults do not prove a vendor will emit them. Those limits
are explicit while actual rows/locks/commit effects remain observed. F: protects later
Stage5 reuse. A: existing project tests and inquiry probe show the environment supports it.
M: real state plus independent caller/error assertions support it. **ACTIONABLE**.

### 5C — Reorganize prior evidence only

N: presentation changes are not new qualification. S: old evidence predates the new
custody API/schema/logic and did not catch old silent repair. F: useful provenance only.
A: cannot validate unimplemented behavior. M: artifact-grounding defeats the sufficiency
claim. **KILLED**; retain prior evidence as reference rather than relabel it as a pass.

### 6D — Physical ticket analogy

N: explains the already-established nonrefundability but adds no new mechanism or
contract beyond3F. **KILLED at novelty** as an implementation candidate. Other tests are
not needed after this kill; its teaching analogy does not justify a token subsystem.

### 7I — Process-memory-only allowance

N: removes persistent machinery. S: process restart/parallel independent processes
restore separate full counters; there is no24-hour shared admission bound. F: only a
single-lifetime convenience limiter. A: violates Stage4's durable future consumer need.
M: actual process-exit persistence evidence demonstrates why shared state matters.
**KILLED**. Persistence survives an explicit existence-axis challenge.

## Artifact-grounding, independence and re-test disposition

Current ReadBudget's actual constructor/reservation/settlement code grounds1C's failure;
current SQLiteSyncStore grounds2F, without claiming its runtime itself enforces joins.
Merged account_operation supplies verified identity only to its caller, supporting4F.
No current JoinBudget/export/guard exists on dev. All proposed additions remain proposals.

Convergence on1F+2F+3F+4F+5F is not five repetitions of one upstream assertion: it rests
on a user scope decision, actual source state, actual SQLite/process observations and
independent inability to infer source outcomes from missing replies. Shared inherited
“durability is needed” was challenged7I; “a new ledger is needed” was challenged1C/2C.
No survivor requires silently revising a committed fact.2G's refinement is an explicit
re-test of the narrower missing-table-only fix; the lifecycle selection remains2F.

## Assembly check

Assemble a small dedicated SQLite JoinBudget with explicit provisioning and conservative
unit admission, exported with frozen status/local errors. Reuse current patterns, not
ReadBudget internals. Use separate tables and one transaction helper; no backend protocol,
new engine, SDK mixin, facade option, receipt/recovery state machine or new health ownership.
Status includes configured account ID/limit, unexpired usage/remaining and advisory times.
Success-return from private _claim is the only local permit; it is consumed already.

The assembly's emergent value is that a known-state open, coherent policy/time snapshot,
durable claim and fail-closed outcome form one comprehensible promise, while still
leaving authentication and actual sending with the already-established future boundary.
It is smaller than combining “convenient” automatic initialization with ad-hoc repair
and recovery logic after the fact.

Axes covered: counted unit(1/3), persistence ownership(1/2/7), lifecycle(2), uncertainty/
cleanup(3/5), source-integration scope(4), evidence method(5), user observation(1).
All5 assembly elements have variation/test trace. No axis is silently inherited.

## Telemetry / verdict

- Generators4/4: Combination1G/3G; Absence2G/4F (patch+redesign and already-present check);
  Domain Transfer2F/5F/6D (native+different field); Extrapolation4G.
- Framers3/3: Lens1F/5G; ConstraintADD3F/REMOVE2C; Inversion1C/2C/3C/4C/5C/7I.
- Five meta-decision pieces; each generated generic/focused/contrarian before testing.
  Piece mechanism logs are explicit above. Q2/Q5 property-v shape-axis inversions satisfied;
  Q1/Q3/Q4 framing/criteria inversions satisfied. No inapplicability shortcut.
- 17 candidates entered tests:16 full five-test entries,1 novelty kill. Five actionable
  assembly components; two research frontiers, one deferred consumer candidate, two
  refinements and seven kills. All survivors tested; no promised full-scale reduction.
- Inherited frame audit fired once for persistence;7I closed the gap. No unchallenged
  central assumption remains. Three-plus mechanisms converge with different grounds.
- Six failure modes checked: no premature evaluation/single mechanism/early lock/
  ungrounded generation/exhaustion/comfort-only survival. The smallest surviving design
  was selected after testing zero-ledger, external-backend and outcome-accounting alternatives.

**Overall: PROCEED.** Assembly is a candidate for critique, not yet an approved implementation plan.
