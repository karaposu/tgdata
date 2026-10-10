---
model: gpt-6-astra
effort: max
---
# Sensemaking — Stage4 allowance contract

## User Input

_branch.md's I1 question and all6 considered articulations, using the committed
surfacing.md inventory. The user confirmed Stage4 only, review/merge before Stage5.
This pass stabilizes meaning; decomposition/innovation still choose the bounded design.

## SV1 — Baseline understanding

A per-account counter might appear to be enough: save a limit, count joins over a day,
refuse when full. Existing ReadBudget and the old unmerged JoinBudget offer code patterns.
That baseline leaves “join”, “day”, “saved” and “refused” underspecified.

## Phase1 — Cognitive anchors

**Constraints:** C1 user scoped Stage4 only; C2 verified ownership is already merged;
C3 Stage5 is the later source-send consumer; C4 allowance must survive local process
restart to serve that consumer; C5 current library supports SQLite locally and Python3.7
syntax; C6 no safe Telegram rate or global control of arbitrary other clients is known.

**Insights:** K1 a missing reply does not say whether the remote action happened;
K2 even a local error after commit can coexist with a durable charge; K3 auto-repair of
partial ledger schema can erase usage while retaining policy.

**Structural points:** S1 policy/status and atomic consumption are distinct operations;
S2 state initialization/reopen and ordinary operations have different authority;
S3 account/clock/claims need one transactional view before any later source send.

**Principles:** P1 later work may proceed only after successful admission return;
P2 policy changes must not rewrite already admitted history; P3 storage/hardware and
clock trust are explicit operating assumptions, not things a counter can manufacture.

**Meaning nodes:** M1 allowance (local authority to attempt), M2 claim (consumed unit),
M3 usage (unexpired admitted units), M4 observation (status snapshot, not permission).
These nodes are tested below rather than inherited solely because the old code names them.

## SV2 — Anchor-informed understanding

The unit and the point at which permission exists matter more than the count formula.
A successful membership counter cannot alone bound requests whose outcomes are unknown.
A database file existing is not evidence that its historical usage remains intact.
H4/H5 checks: “claim” denotes an actual committed row, not a label for an anticipated
success; missing-table reproduction is one case of a wider missing-state responsibility.

## Phase2 — Perspectives and new anchors

- **Technical/logical:** a separate status read and later write race. Real SQLite
  BEGIN IMMEDIATE can serialize the combined decision and charge; no new lock service
  is implied. New anchor: admission is atomic, status remains advisory.
- **Human/user:** a limit unexpectedly reset by configure/restart would look like valid
  remaining capacity. Explicit provisioning and policy updates need different meanings.
  New anchor: convenience must not silently grant new history.
- **Risk/failure:** process exit after commit but before return leaves usage, while no
  consumer can safely assume permission from the missing return. New anchor: an error
  may strand allowance conservatively; it never creates permission or a refund right.
- **Resource/feasibility:** bounded local synchronous transactions fit current conventions;
  a five-second busy wait is possible and must be described. No transaction spans await.
  New anchor: source-independent Stage4 has no need for an SDK mixin yet.
- **Strategic:** reuse can mean the proven transaction pattern, not inheritance from a
  message-specific refund/warmup class. New anchor: separate units can share one file
  while preserving separate schema and public semantics.
- **Ethical/systemic:** configured allowance is a caller policy, not assurance against
  account restrictions or permission to join private spaces. No rate recommendation.
- **Definitional/internal consistency:** “used” must include uncertain/abandoned admitted
  attempts if it promises conservative admission; “remaining” cannot promise future
  availability against other writers. Authentication proof stays outside this ledger.
- **Frame-exit completeness:** the inherited word “budget” has message-read and join
  referents with different unit/refund propositions. Enumerate read sums/reservations,
  join unit claims, caller policy and source outcomes. Read settlement and remote action
  are outside Stage4 but load-bearing: locate read behavior in ReadBudget and actual-send
  integration in Stage5. Counter: combine them in one generic quota engine; different
  refund/consumer semantics require branches and add coupling. Residual: uncoordinated
  external clients remain a custody assumption, not another enforcement surface here.
- **Phase/calibration:** Stage4 has no joining API; it can qualify ledger behavior, not
  claim already-enforced Telegram mutation limits. Stage5 must prove per-send placement
  under the verified operation. Live server semantics/rate safety are not calibrated.

H1/H2/H3/H7: variants1/4/5 can compose but are not yet a selected implementation;
variant2 changes the enforceable unit,3 requires an additional lifecycle,6 changes
provisioning authority. Scope cannot be expanded into Stage5 to make Stage4 look complete.

## Executed component evidence

`../contract_probe.py` ran against Python3.11.10/SQLite3.45.3, temporary files and actual
spawned processes. It implements small SQLite experiments and loads only the historical
standard-library ledger; it is **not** a prototype of the new JoinBudget API.

```
sqlite_processes:6 workers,3 admitted at cap3; exits before commit->0 rows, after commit->1 row
open_commit_boundaries:mode=rw did not create a missing file; injected error after real commit left1 row
historical_ledger:lowered cap next=87420; backwards clock observed=1020/used3; exact boundary remaining1
dropped_attempt_table:before1, after old constructor reopen0, another claim admitted
```

Exit0; complete JSON output in ../evidence/contract-probe.txt. The post-commit exception
is deliberately injected after an actual SQLite commit: the observed persistence is
real, not a claim that this particular driver error normally occurs. Process exits are
real; disk power-loss behavior was not tested. The old missing-table case demonstrates
silent repair in that code, not a failure of SQLite atomicity.

Documentary support: [SQLite transaction rules](https://www.sqlite.org/lang_transaction.html)
explain writer serialization and commit errors; [Python's SQLite URI interface](https://docs.python.org/3.11/library/sqlite3.html#how-to-work-with-sqlite-uris)
supports opening without creating; [SQLite's atomicity assumptions](https://www.sqlite.org/atomiccommit.html)
make filesystem/hardware cooperation explicit. Component execution closes the affordable
local premise; documentation does not certify arbitrary deployment storage.

## SV3 — Multi-perspective understanding

This is a durable admission ledger with explicit custody, not merely a retrospective
membership total. A few conservative local rules can avoid a remote-outcome lifecycle.
The important new distinction is fresh provisioning versus reopening known allowance.

## Phase3 — Ambiguity collapse

### A1 — What does an allowance count?

**Counter:** count only confirmed new memberships to avoid wasting allowance on errors.
**Structural test:** neither Stage4 nor a failed/absent source reply proves that no
mutation occurred; Stage4 has no source result at all. Success-only counting admits
unbounded uncertain attempts. **Confidence:** HIGH.
**Resolution/fixed:** one consumed unit per admitted mutation attempt; all admitted
units remain charged through their window. **Excluded:** success-only automatic refunds.
**Dependencies:** future per-send integration and user-facing usage terminology.
**Model change:** policy bounds controllable local admissions rather than remote membership.

### A2 — Can status authorize a later send?

**Counter:** a caller can read remaining and decrement afterwards.
**Structural test:** six processes competing for cap3 need decision+charge in the same
transaction; a snapshot is not exclusive ownership. **Confidence:** HIGH.
**Resolution/fixed:** atomic claim is the authority; status is advisory and may be stale.
**Excluded:** a cached remaining count as a grant. **Dependencies:** ledger API and Stage5.
**Model change:** observation and authorization are separate even if they show the same fields.

### A3 — What is a “day”?

**Counter:** a UTC midnight reset is simpler and familiar.
**Structural test:** it permits two full caps around midnight; a rolling24-hour interval
matches the already-established admission pattern without timezone boundaries. Calendar
limits remain structurally possible, so this is an explicit library policy choice, not
a Telegram fact. **Confidence:** HIGH for the scoped chosen contract, LOW as a universal
necessity. **Resolution/fixed:** carry rolling24 hours forward for design evaluation.
**Excluded here:** calendar reset/warmup policy expansion. **Dependencies:** expiry/status.
**Model change:** “daily” labels a rolling interval rather than a calendar partition.

### A4 — Is automatic schema/file creation harmless?

**Counter:** initialize on every startup so consumers do not manage provisioning.
**Structural test:** the actual historical constructor rebuilt a missing attempts table,
retaining its policy but returning zero usage. Reopening known state must not silently
supply absent history. Whole-file reinitialization has the same custody problem.
**Confidence:** HIGH for distinguishing lifecycle intents; initialization syntax remains
an implementation choice. **Resolution/fixed:** explicit provisioning; ordinary/reopen
operations refuse missing/incomplete known state. **Excluded:** transparent schema repair.
**Dependencies:** constructor/open behavior and fault tests. **Model change:** file creation
is a grant of state authority, not a harmless convenience inside any operation.

### A5 — What does an error after writing mean?

**Counter:** failed claim call means nothing was charged, so retry/refund it automatically.
**Structural test:** process death and the post-real-commit injected error leave a durable
row without successful return. **Confidence:** HIGH.
**Resolution/fixed:** only successful return permits the later attempt; errors grant no
permission and may have consumed usage. A new call is a fresh attempted admission.
**Excluded:** refund/receipt replay based only on error or guessed source non-execution.
**Dependencies:** caller contract, transaction cleanup and Stage5. **Model change:** safe
under-utilization is acceptable; the ledger does not promise exactly-once source effects.

### A6 — Can a counter handle arbitrary clock changes?

**Counter:** wall time always moves forward, or a per-process monotonic clock suffices.
**Structural test:** restart/processes do not share monotonic origins; current code and
probe demonstrate per-account persisted max time under rollback. A trusted clock is
still needed to distinguish elapsed time from a forward jump across restarts.
**Confidence:** HIGH. **Resolution/fixed:** finite UTC wall time, persisted nondecreasing
observation, ordinary rolling expiry. Forward-clock correctness is an operating assumption.
**Excluded:** claiming protection from arbitrary clock tampering or instant-retry guarantees.
**Dependencies:** expiry and retry hints. **Model change:** clock trust is named, not inferred.

### A7 — Can configure reset usage, or does zero mean unlimited?

**Counter:** replacing policy should provision a fresh allowance; zero could disable limits.
**Structural test:** repeated configuration would circumvent a rolling cap; a missing/
zero policy cannot safely be an implicit permit for a future mutation. Old lowered-cap
probe already retains all3 claims and computes the third required expiry.
**Confidence:** HIGH. **Resolution/fixed:** policy update preserves claims, zero blocks,
absent policy errors; lowering affects new admission without revoking earlier claims.
**Excluded:** reset-as-configure or zero-as-unlimited. **Dependencies:** config/status/claim.
**Model change:** policy controls future decisions, not rewriting historical usage.

### A8 — Does cleanup redefine the main outcome?

**Counter:** always report the last close/rollback error, or ignore all storage trouble.
**Structural test:** replacing a primary failure loses its meaning; ignoring commit trouble
can let Stage5 proceed without a durable claim. Current SyncStore distinguishes primary
and cleanup-only errors. **Confidence:** HIGH.
**Resolution/fixed:** preserve a primary failure/cancellation; storage/cleanup-only failures
refuse permission and retain any already committed usage. Sanitize diagnostics. Precise
exception typing is a plan detail. **Excluded:** cleanup overriding a primary or refunding.
**Dependencies:** transaction/error implementation. **Model change:** failure precedence is
part of admission safety, not just logging quality.

### A9 — Is this a universal Telegram-account limit?

**Counter:** an account ID identifies one account globally, so any local counter suffices.
**Structural test:** two independent files/process domains can each grant their full cap;
a local class also cannot authenticate the caller-supplied ID. **Confidence:** HIGH.
**Resolution/fixed:** cooperative same-host callers share the same persistent ledger;
Stage5 supplies freshly verified numeric owner and uses every claim once before enqueue.
**Excluded:** cross-machine coordination, custody-violation detection and claimed source
protection before Stage5. **Dependencies:** docs and later consumer tests.
**Model change:** this stage owns the allowance fact, not all Telegram behavior.

H4/H5: the old stabilized admission unit, shared durability and ownership notions were
retested against process/SQLite behavior and the merged handle contract. Missing-table
repair is one representative failure of a broader state-custody invariant, not the whole
problem. User language stays “join allowance/budget”; no new workflow vocabulary needed.

## SV4 — Clarified understanding

The allowance consumes durable, nonrefundable admissions under explicit policy and shared
state. Restart cannot reset usage through ordinary operations. A snapshot, a failed call
or a filename cannot prove an available permission. Stage5's proof/send composition remains
a distinct next stage; no lifecycle machinery for remote acknowledgments is required here.

## Phase4 — Degrees of freedom reduced

Fixed: Stage4-only local ledger, supplied numeric account key, atomic unit claims,
rolling24-hour accounting, explicit policy, history-preserving updates, nondecreasing
observed clock, no refund/replay, no implicit repair and original-error precedence.
Eliminated: success-only/calendar-reset variants for this delivery; generic read-quota
refactor; process-memory-only enforcement; new persistence service; source join guard now.
Viable representation/API options: a small separate SQLite class following current store
patterns, or a narrow wrapper around existing quota machinery if it can preserve these
semantics without leaking read settlement/configuration. Explicit-create syntax and
exact status/error fields remain engineering choices for decomposition/innovation.

## SV5 — Constrained understanding

The design space is a local durable policy+claims primitive with three actions: configure,
observe, atomically consume one unit. Its outputs convey local facts; its future consumer
must still prove the account and place the consumption at the send boundary. No current
feature's ownership or message-read state needs to change to deliver that primitive.

## SV6 — Stabilized model

Stage4 grants a bounded right to make one later join attempt by committing one unit of
usage for a configured account, or returns a local refusal/error. Remaining capacity is
an observation. Lost returns, failed sends and cancellation never justify restoring it.
Known-state custody, clock assumptions and policy changes are explicit. This differs
from SV1 by replacing “count joins each day” with a verifiable admission fact and clearly
separating initialization, observation, consumption and the later source action.

**Telemetry:**19 initial anchors across5 types;9 perspectives, at least5 new anchor
kinds;9 ambiguity entries resolved/narrowed with counters and structural tests; all6
articulation variants evaluated (1/4/5 viable/composable,2/3 rejected here,6 narrowed to
explicit provisioning). Two implementation choices remain open without external blockers:
API syntax and reuse form. Late perspectives confirmed existing anchor types. H6 model
fit stabilized without repeated exception patches; H8 self-reference not applicable to
SQLite behavior; H9 terminology aligns with the repository/user. No architectural or
vendor-rate claim was inferred from passing synthetic data.
