# Decomposition — account routing contract

## User Input

`_branch.md` and saved `sensemaking.md` SV6. Partition the source-owner problem
without splitting identity from admission or moving progress into the pool.

## 1. Coupling map

| Cluster | Strong internal coupling | Boundary traffic |
|---|---|---|
| P1 Account reader | Credential, actual principal, guarded client, proxy, request behavior, error attribution, close/quiescence | Bounded request in; batch or original error/prefix out |
| P2 Eligibility facts | Account/group scope, deadlines, retention, clock and restart semantics | Facts in; candidate eligibility/reason out |
| P3 Router | Inventory, policy, exclusion set, one attempt per candidate, cancellation, partial output | Eligibility queries; P1 attempts; observed facts |
| P4 Delivery adapter | Existing progress engines, reader injection, saved pending/ack contract | MessageBatch and original exception only |
| P5 Qualification | Real SDK composition, persisted state, overlapping tasks, deployment evidence | Observable invariants and explicit evidence limits |

P1↔P2 moderate contract coupling (typed scoped facts); P2↔P3 strong temporal
coupling at admission, but a narrow eligibility interface can contain it.
P1↔P3 moderate asynchronous outcome contract. P3↔P4 weak format coupling through
the existing reader signature. P5 crosses all pieces through public behavior,
not by taking ownership of their state. Application scheduling/receivers remain
external resources, not pieces hidden inside P3.

## 2. Top-down boundary candidates

Keep actual identity checks and the client that makes the request together.
Cut between a source observation and delivery acknowledgment; the current batch
contract already supplies that cut. Separate eligibility history from selection
ranking so changing fairness cannot clear a restriction. Keep close/cancel with
the owner of the in-flight task rather than delegating cleanup to an application
that cannot see it. Persistence mechanism stays inside P2's question.

## 3. Bottom-up validation

Atoms: one credential session, one fresh authenticated identity answer, one quota
reservation, one SDK send, one complete record, one batch, one saved receipt, one
restriction expiry, one active task. Credential/identity/send cluster in P1;
reservation authority remains the existing ledger consumed by P1/P2. Deadline
and restriction scope cluster in P2. Batch crosses P1/P3/P4 intact. Receipt and
cursor stay together in P4's existing engines. Task is owned by P3, with P1 awaited
to completion. Top-down/bottom-up agree: HIGH boundary confidence.

The potential wrong cut was “health reporting separate from source identity.”
That is rejected: operation attribution belongs inside P1 even if existing
HealthMonitor classification helpers are reused. No broad #7 redesign follows.

## 4. Question tree and verification criteria

**Root: How can existing-access reads route and recover without changing the
meaning of identity, allowance or acknowledged progress?**

**P1 — How does a bounded reader prove and retain the attempted account?**
- [ ] A fresh authenticated ID must equal the configured expected ID before any history send.
- [ ] Every budgeted retry keeps that invariant; duplicate expected IDs refuse.
- [ ] Proxy/device/session settings use the existing factory; no terminal login.
- [ ] SDK and authentication errors retain actionable types; no hidden long wait.
- [ ] Cleanup and cancellation cannot replace a prefix/error or leave an attempt running before failover.

**P2 — How is eligibility determined and retained?**
- [ ] Account-wide failures, per-group denials, request/account waits and local errors have explicit scopes.
- [ ] Actual ledger status and explicit maturity policy determine allowance, never a second quota ledger.
- [ ] Clock, restart and unreadable-state behavior are specified; observed waits are not silently forgotten.
- [ ] Recovery/recheck has an evidence rule; unrelated success cannot clear a denial.
- [ ] No-eligible output includes actionable reasons and conditional retry times without credential/error text.

**P3 — How does selection terminate and preserve observations?**
- [ ] Deterministic policy and affinity meaning; candidate attempted at most once per call.
- [ ] Retryable failures with no prefix may fail over; local/unknown errors and owed prefixes stop.
- [ ] Concurrent callers cannot use the same owned client unsafely; group/progress ownership is explicit.
- [ ] Close/cancellation settle tasks, and subsequent use has a defined result.

**P4 — How does the router compose with existing durable delivery?**
- [ ] Canonical group validated before message reads; changed username cannot change the source.
- [ ] Daily/backfill use their current pending/ack logic through the reader contract.
- [ ] Pending replay/ack require no account selection, authentication, quota or routing-state access.
- [ ] Empty/end is qualified by source visibility; pool cannot claim union-history coverage.

**P5 — Which observations qualify the composition?**
- [ ] Actual 1.45 factory, SDK sender and SQLite tests cover fresh/stale identity, retries and prefix failure.
- [ ] Deterministic overlapping calls, cancellation, lost writes and restart have external assertions.
- [ ] Existing supported offline suite stays green; standalone usage/build paths have no work-folder dependency.
- [ ] A bounded live gate states accounts, groups, costs, failure method and exactly what it proves; missing live resources remain a visible limit.

## 5. Interface map and assumptions-not-data check

| From → to | Flow / direction | Required assumption made explicit |
|---|---|---|
| Caller → P1 | Immutable inventory and expected numeric IDs; one-way configuration | Session ownership exclusive; replacing credentials is explicit, never relabel an active slot |
| Ledger → P1/P2 | Status and reservation authority; request/response | Status is advisory; actual send independently reserves and rechecks identity |
| P2 → P3 | Eligibility/reason/deadline | A eligible snapshot does not guarantee later send; update failure facts before another intentional call |
| P3 → P1 | Canonical group, bounded cursor/window/limit | Previous attempt ended; no implicit join or hidden account change |
| P1 → P3/P2 | Verified identity, source outcome and scoped facts | A local exception is not Telegram evidence; original prefix stays attached |
| P3 → P4 | MessageBatch or exception carrying partial_result | No internal acknowledgment, cursor advance, prefix discard or synthetic empty success |
| P4 → caller | Pending observation/receipt/status | Destination acceptance belongs to caller; one source reader per group remains required |
| P5 → all | Evidence plus qualification boundary | Synthetic transport proves client composition, not equal account visibility or real proxy behavior |

## 6. Dependency order

P1/P2 contracts precede P3; P3's reader contract precedes P4 integration. P5's
acceptance definitions apply from the start; combined qualification follows P4.
P1 and P2 can be reasoned about independently once fact types are agreed; no
parallel agents are used. The runtime P1→P2→P3→P1 cycle is an observation loop,
not a construction dependency: the interfaces define ownership before policy.

## 7. Self-evaluation

| Dimension | Result | Reason |
|---|---|---|
| Independence | PASS | Each question has a coherent answer with explicit upstream contracts. |
| Completeness | PASS | All nine Sensemaking anchors map to P1–P5; persistence stays an explicit question. |
| Reassembly | PASS | Owned source + eligibility + bounded routing + existing delivery fulfils the selected scope. |
| Tractability | PASS | P1 is the hardest; its actual seams have already been probed. |
| Interface clarity | PASS | Timing, ownership, prefixes and evidence assumptions named alongside data. |
| Balance | PASS | P1/P2/P3 carry separate substantial risks; P4 reuses rather than duplicates state. |
| Confidence | PASS | Bottom-up atoms agree with top-down cuts. |

Determination mechanisms are covered: identity=P1 fresh answer; eligibility=P2
scoped facts plus ledger; retryability=P3 typed outcome/prefix; owed work=P4 stored
pending. No predicate is assumed already decided. Failure modes checked: no
premature split, hidden health ownership, missing cleanup, arbitrary atom splitting,
unmapped dependency or single catch-all piece. Stop at this level: each question
has directly verifiable criteria. Next: Innovation, including P2 durability options.
