# Innovation — mechanisms for the account pool

## User Input and seed

Saved `_branch.md`, Sensemaking SV6 and Decomposition P1–P5. Seed: a gap between
per-account guarded reads and account-independent durable delivery. The user values
daily continuity and reusable orchestration without resuming joining work.

Inherited mode: **Standard default**, production-task piece list P1–P5. Alternative:
**Contrarian-rethink**, prioritizing whether to add a pool at all. That would consider
leaving routing in an application and repairing only identity. Run Standard default
with all seven mechanisms and explicit contrarian variants per piece; the alternative
is tested rather than silently discarded. No coverage-reducing instruction supplied.

## Generate — full variation set before testing

P1–P5 all contain evaluation/frame commitments and are meta-decision pieces. Each
receives generic G, focused F and contrarian C variants. Intervention-shape names
are not the seed's commitments; inversions below target the ownership/frame axes.

| ID | Mechanism(s) | Generated variation |
|---|---|---|
| P1G | Combination | Accept arbitrary TgData objects and combine their batch APIs with health summaries. |
| P1F | Absence recognition, constraint ADD | Own immutable expected-account configurations; make a private pool connection policy through the existing factory, verify identity, bound SDK attempts, refuse prompts, and retain cancellation prefixes for pool-owned timeouts. |
| P1C | Inversion | Reverse “a new owner is necessary”: repair every health identity path first and use shared clients unchanged. System-depth: make all TgData activity account-bound globally. |
| P2G | Domain transfer (native circuit breaker) | Keep in-memory account/group circuit breakers; recreate them after restart. |
| P2F | Combination, domain transfer (ledger/bookkeeping) | Persist only known restriction facts per numeric account in an opaque CAS store; keep quota in ReadBudget and progress in current engines. No durable job scheduler. |
| P2C | Inversion, constraint REMOVE | Reverse “remember restrictions”: forget all routing observations and ask Telegram again on every call; source answers are the whole health system. |
| P3G | Extrapolation | As inventory grows, add parallel hedged reads and choose whichever account returns first. |
| P3F | Lens shifting, constraint ADD | Evaluate success as one attributable bounded observation. One active pool operation, deterministic drain or remaining-budget spread, one attempt per candidate, failover only with no owed prefix. |
| P3C | Inversion | Reverse “the pool chooses”: expose eligibility only and require the application to choose each account. Existence-axis: zero internal failover. |
| P4G | Combination | Duplicate cursor/ack behavior inside an all-in-one pool scheduler. |
| P4F | Combination, absence recognition | Expose the same raw-reader signature and share a narrow progress facade backed by the current SyncEngine/BackfillEngine. Static canonical group registry supplies bounded resolution hints. |
| P4C | Inversion, constraint REMOVE | Reverse “integrate progress now”: ship only raw batch routing; users manually compose private engines or rebuild public wrappers. Identity-axis: pool is only a selector, not a reader. |
| P5G | Domain transfer (native unit testing) | Script account outcomes in a fake reader and declare failover qualified. |
| P5F | Lens shifting, combination | Qualify invariants with actual factory/SDK/SQLite adversarial histories, then a bounded two-account live gate; report missing live resources separately. |
| P5C | Inversion | Reverse “offline tests establish the core”: run only live tests and trust successful accounts to demonstrate failure correctness. |

Additional variation X1 (constraint REMOVE): remove the existing batch-format
constraint and add account identity to MessageBatch v2. It could make provenance
intrinsic, but changes every receipt/hash consumer. X2 (extrapolation): if the
account inventory and scheduling become distributed, evolve to leased workers and
an explicit visibility policy; a separate future controller rather than hidden v1 scope.

Absence recognition ran both levels: patch-level missing preserved SDK error type;
redesign-level missing source ownership/eligibility contract. Reverse direction:
quota, CAS durability and acknowledgment already exist and are not newly invented
pool capabilities. Domain transfer includes native circuit-breaker/structured-task
patterns and the distinct bookkeeping distinction between an observation and a
settled obligation; neither analogy substitutes for SDK probes.

Inversion depth: shared client → explicit owner → permission/identity travels with
the attempted source operation. Other axes checked: zero pool (P3C), no persistent
observations (P2C), batch format as owner (X1). All produce tested candidates.

## Inherited frame audit

Central assumptions: a pool belongs in the library (challenged P3C); a new owner is
needed (P1C); durable facts are necessary (P2C); progress integration should reuse
existing engines (P4G/P4C); offline evidence matters (P5C). Every piece commitment
has an explicit reversal. No audit override or return cycle needed. User exclusions
remain authorization bounds; generating an automatic-join candidate cannot satisfy
the selected delivery, so no scope extension is smuggled in through an inversion.

## Test cycle

N=novel relative to this codebase, S=scrutiny survival, F=fertility, A=actionability,
M=mechanism independence. A dash means killed at an earlier test, not untested survival.

| Candidate | N | S (strongest objection and result) | F | A | M / disposition |
|---|---|---|---|---|---|
| P1G | yes | FAIL: probe proves health can belong to cached111 while actual222 spends budget | — | — | killed |
| P1F | yes | survives if actual identity checked again at each send and attempts await cancellation | yes | private policy/factory seams exist | source probe + explicit ownership independently support it; ACTIONABLE |
| P1C | yes | FAIL for this delivery: making all existing facade health account-bound expands into the paused #7 problem without bounding its connection sleeps | — | — | defer global repair separately |
| P2G | yes | FAIL: restart erases a known two-hour wait and makes it immediately selectable | — | — | killed as sole authority |
| P2F | yes | survives if failed/ambiguous state writes stop routing and do not discard a prefix | yes | existing CAS backend can be adapted with separate state discriminator | wait probe + restart thought experiment; ACTIONABLE |
| P2C | yes | FAIL: an RPC retry is not evidence that an observed prohibition has expired | — | — | killed |
| P3G | yes | FAIL: concurrent hedges spend multiple allowances and create multiple owed observations without a winner/loser delivery contract | — | — | distributed/hedged work is RESEARCH FRONTIER |
| P3F | yes | survives: serial operations limit throughput but caller owns scheduling; finite inventory bounds retries | yes | narrow router over owned readers | identity and prefix constraints independently converge; ACTIONABLE |
| P3C | no | unchanged burden from current public APIs; fails selected automatic routing outcome | — | — | killed at novelty/outcome |
| P4G | yes | FAIL: second cursor/receipt authority can acknowledge unseen work and diverge after uncertain writes | — | — | killed |
| P4F | yes | survives if facade extraction is behavior-preserving and local replay bypasses pool admission | yes | actual replay probes already show seam | source signature + persisted replay independently support it; ACTIONABLE |
| P4C | yes | survives as a smaller API but daily callers would need private internals or duplicate wrappers | limited | possible | DEFERRED alternative if facade extraction cannot preserve existing behavior |
| P5G | no | fake outcomes miss actual stale-cache/retry seams shown by probes | — | — | killed |
| P5F | yes | survives: live test cannot safely manufacture bans, so actual SDK scripted errors remain necessary | yes | existing transport seam and explicit live gate | SDK probes + receiver invariants; ACTIONABLE |
| P5C | yes | FAIL: happy-path live accounts cannot establish bans, uncertain writes or cancellation deterministically | — | — | killed |
| X1 | yes | FAIL: source identity in canonical batch hash changes equality/receipt behavior and mixes source provenance with observation content | — | — | killed for v1; separate routing outcome can carry provenance |
| X2 | yes | survives as future territory | yes | not within single-owner scope | RESEARCH FRONTIER; revive when competing readers are requested |

Artifact grounding: ConnectionEngine._new_client carries proxy/session/device;
SDK `_call` has the observed retry controls; BudgetClient refreshes identity at
send; SyncEngine and BackfillEngine already take a reader callable. None of the
survivors assumes a missing capability exists. Shared-input check: P1F and P3F
both inherit ownership; their apparent agreement is not independent proof. Their
extra grounding is the actual cache/ledger mismatch and the independent partial
delivery mechanism. P2F still needs state-failure probes during implementation.

## Assembly candidate A — owned reader with persistent restrictions

Proposed public `AccountPool` owns `PoolAccount` configurations with positive
expected IDs; callers supply a canonical `PoolGroup` registry with optional
username resolution hints. Existing private groups need resolvable cached entities;
no unbounded dialog enumeration or automatic joining. A resolved hint must match
the canonical ID before reading; stale/reassigned hints cannot change progress source.

The pool requires the existing ReadBudget ledger and a persistent account-state
store. A small `SQLiteAccountPoolStore` may reuse the existing SQLite CAS primitive
through composition, with a distinct document kind and dedicated file. Its public
keys are account IDs, not group IDs; custom stores implement async load/CAS.
Restrictions are keyed by expected account and optional canonical group. This
stores no credentials, messages, accepted cursors or duplicate quotas. Corrupt,
missing-known or ambiguous state refuses rather than treating facts as clear.

Known flood waits survive restart; ordinary transport failures and group denials
have explicit retry deadlines. Ban/logout/identity mismatch require deliberate
operator recheck after repair; recheck does not erase future waits or budgets and
does not claim group access. Eligibility defaults to the ledger's warm-up caps;
optional minimum warm-up age adds a gate. Trustworthy UTC is an explicit deployment
assumption; regressions refuse. One owning process and one active pool operation,
with independent progress stores retaining their existing single-reader rule.

Selection: `drain` uses inventory order; `spread` uses current remaining allowance,
ties inventory order. No implicit unlimited allowance or hidden affinity policy.
Account/group facts record observed readability/restrictions; they do not certify
membership forever. Each call attempts each eligible account at most once. Typed
unavailability without a prefix permits failover; local/unknown errors stop.
No candidates yields a structured refusal with per-account reasons and conditional
retry information, never an empty MessageBatch.

Pool readers use a private connection policy: one session per account, no prompts,
zero SDK request retries, preserved last error, flood threshold0, no automatic
reconnect/update processing, finite attempt timeout. The SDK's final two-second
server-error sleep is allowed within that bound, not falsely promised absent.
Fresh identity is checked on entry and at budget admission through a bound ledger
adapter; expected mismatch stops before history send. Pool-owned health has fixed
ownership with user_id unknown until verified; it never imports legacy summaries.

On a timeout, cancellation is awaited and a completed prefix is retained if one
exists. External cancellation propagates without failover. Once any prefix exists,
no further account is tried. If recording the failure itself fails, a local pool
storage exception carries the interrupted prefix and separately retains the source
error; no exception cause can falsely classify the storage error as Telegram health.

Raw `get_message_batch` keeps the current MessageBatch contract. A richer `read`
operation may return batch plus account/attempt metadata without changing its hash.
Daily/backfill methods share the current progress facade and use that same reader;
replay/ack bypass account inventory and routing-state I/O. Completion continues to
mean history visible to the selected account, never union history across accounts.

## Assembly tests and dispositions

The assembly adds value: the source seam can change accounts while durable delivery
continues to replay the exact already-observed data. Strongest emergent objection:
state persistence failure after source data arrives could lose the result. The
candidate explicitly preserves the completed prefix on that local error and must
test it through the actual progress engines. Another: global serialization costs
throughput. It is an explicit first-version contract, not hidden queueing; callers
receive a busy outcome and can schedule later.

Axes covered: ownership (P1), persistence (P2), routing/fairness (P3), delivery
integration (P4), qualification (P5), source-format identity (X1), scaling (X2).
Every assembly row has a generated/tested candidate. P4C is retained as a named
fallback requiring an explicit scope decision, not an implementation escape hatch.
Re-test triggers passed to Critique: timeout-prefix composition; ambiguous restriction
write; duplicate credential aliases; recheck while a cooldown remains; facade replay
without configured accounts. The full durable scheduler and visibility union are
not ACTIONABLE components of this delivery.

## Telemetry

Generators 4/4; framers 3/3; all fired and entered tests. Generic/focused/contrarian
sets: 5/5. P1: absence+ADD+combination+inversion (ownership); P2:
domain-transfer+combination+REMOVE+inversion (durability); P3:
extrapolation+lens+ADD+inversion (routing); P4: combination+absence+REMOVE+inversion
(integration); P5: domain-transfer+lens+combination+inversion (evidence).
Meta-decision: all five; inversion compliance satisfied5/5; property(v) does not
fire (no named intervention-shape commitment). Both constraint directions and both
absence levels exercised; native and distinct source domains included.
Five actionable survivors tested5/5, two retained future/alternative survivors
tested2/2; ten killed candidates retained. Convergence from ≥3 mechanisms is
qualified by independent SDK/delivery evidence rather than mechanism count alone.
No premature evaluation, single-mechanism trap, early frame lock, ungrounded survivor,
exhaustion or ungenerated contrarian. **Overall: PROCEED** to adversarial Critique;
this candidate is not yet the implementation plan.
