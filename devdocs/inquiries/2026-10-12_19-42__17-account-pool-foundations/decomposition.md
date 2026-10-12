---
model: gpt-6-astra
effort: max
---
# Decomposition — questions beneath the pool lifecycle

## User Input

`_branch.md` and saved Sensemaking SV6: explain #17's incomplete operation boundary
and compare simplifying concepts. Preserve all five articulations. This decomposes
the conceptual problem; the current product/plans remain unchanged.

## 1. Coupling map

| Elements | Coupling / propagation | Boundary consequence |
|---|---|---|
| Operation admission, descendant provenance, external close and guard release | Strong: each decides whether one control path may wait on another | Keep control admission and provenance together; identity-only checks cannot be an independent utility |
| Source result holder, timer cancellation, child completion, caller cancellation | Strong: a change in one changes which result/error may be delivered | One complete outcome rule; do not add independent exception-specific fixes |
| Client retirement, retained SDK task, quarantine and credential reload | Strong: replacement before retirement can reuse/write stale credentials | One client-lifetime contract, including failed attempts |
| Source outcomes and account-attempt settlement | Moderate: exact data/error and identity flow across one boundary | Keep a clear outcome-to-settlement interface; no callback outcome may enter it as source truth |
| Observer delivery and source completion | Currently strong through awaiting; semantically limited to data notification | Candidate boundary: source facts flow out; observer outcome does not flow back as source permission/result |
| Pool state and budget | Weak/moderate: eligibility snapshot plus actual guarded send | Preserve ledger authority; pool status grants no quota |
| Pool reader and daily/backfill receipts | Moderate, stable batch/error interface | Preserve existing reader injection; pending replay/ack stays independent |
| Persistent pool versus #7 temporary clients / #10 process | Shared settlement mechanism, different owner/reuse policies | Compare contracts; no assumed universal lifecycle abstraction |

The strongest concentration is lifecycle/control/outcome, not drain/spread selection.
The backend-close probe crosses control admission even before a source child exists;
therefore cutting at “health callback” would split the wrong region.

## 2. Top-down boundaries

B1. Live operation authority: who can enter/wait/stop, including descendants and the
lifetime of their authority. B2. Source outcome: what the body accomplished and how
public cancellation/timeout affects delivery. B3. Client lifetime: whether actual
SDK work ended and the client may be reused/replaced. B4. Durable settlement/routing:
which source facts change future eligibility or produce a batch. B5. Notifications:
plain observations and their independent delivery outcomes. B6. Qualification:
observations required to establish the combined contract and later live limits.

These are semantic boundaries, not six mandatory modules or public APIs. B1/B2/B3
are the foundation requiring clearer rules; B4 mostly preserves an existing one;
B5 must lose implicit authority over the others; B6 checks their real composition.

## 3. Bottom-up validation

Atoms checked against those boundaries:

- A single terminal source observation (value OR original error/prefix) stays in B2.
- A real pending task and the proof of its end belong to B1/B3; a stored attempt ID
  is B4 and cannot substitute for that proof.
- An account-ID proof stays at the actual source/budget admission seam and crosses
  B2→B4 as attribution, not as a claim made from a configured label.
- A descendants' live operation identity and its expiry stay together in B1;
  splitting propagation from invalidation would falsely reject stale work later.
- One native disconnect attempt and its success/failure receipt stay in B3;
  cancellation of the waiting caller does not erase that receipt.
- An event's plain account/request data may cross to B5; a live client, operation
  mutation right or right to await its own owner must not be implied by that data.
- Existing account token, quota reservation and group delivery receipt remain three
  separate state authorities in B4's interfaces, not one merged record.

Top-down and bottom-up agree on B1–B4/B6 (HIGH). B5's exact dispatch placement is an
open design choice, but its no-source-authority interface is HIGH confidence. The
boundary is retained as a question rather than an assumed background queue.

## 4. Question tree and verification criteria

### Q1 — Who owns a live pool operation, and which controls may wait for it?

Q1.1 How is the operation identified across awaited source, observer and backend
descendants? Q1.2 When does that identity stop authorizing/restricting descendants?
Q1.3 How is external shutdown distinguished from self-dependent shutdown before
changing closed/busy state?

Verification: direct/create_task/wait_for reentry is refused before mutation;
backend descendants are covered; unrelated external close still cancels/joins;
stale context after operation completion is not permanently forbidden; another
pool's independent operation is not blocked by a global observer flag. Required
runtime determination is explicit here, not delegated to “somehow know the owner.”

### Q2 — Which outcome belongs to the source, caller and observer respectively?

Q2.1 What facts capture body completion exactly once? Q2.2 How do ordinary child
completion, observer failure/cancellation, owned timeout and genuine caller stop
combine without losing the original batch/error/prefix? Q2.3 How is stop origin
established without relying solely on CancelledError's type or a runtime-specific
cancellation counter?

Verification: the same successful and failed bodies preserve their exact outcome
under ordinary return, blocked observer timeout and observer-owned cancellation;
actual caller cancellation remains cancellation after child settlement; unfinished
source timeout retains available complete records; no next account runs past a
nonempty prefix. The source result is not inferred from a composite task's state.

### Q3 — What proves a persistent client's retirement or safe reuse?

Q3.1 Who retains and observes source/SDK tasks? Q3.2 Which result quarantines the old
client? Q3.3 When may recheck load a repaired credential or close report completion?

Verification: repeated read/recheck/close cancellation never frees a live child;
failed/internal-cancelled disconnect is distinct from caller cancellation;
quarantined clients cannot be reused/replaced; successful explicit retry clears
the old client before cancellation escapes; credential replacement survives;
accepted temporary-client policies are not silently substituted.

### Q4 — How does a finished attempt affect durable eligibility and delivery?

Q4.1 Which definite admission permits source? Q4.2 Which exact outcome retires the
token and records waits/repair/group denial? Q4.3 How are uncertain commits, real
charges and group receipts preserved without duplicated authority?

Verification: no source after ambiguous admission; exact token/CAS prevents stale
settlement; known waits do not become short generic cooldowns; cancellation remains
conservative; stored/replayed prefixes remain exact; source-free replay/ack works
with pool/credentials unavailable. Router strategy changes are unnecessary unless
a new counterexample implicates them.

### Q5 — What may notifications do, and when do they stop being part of a read?

Q5.1 Which events are plain observations of established source facts? Q5.2 Is
callback completion part of public-call latency or independent delivery? Q5.3 Who
bounds/retires that work, and what authority follows it?

Verification: callback success/failure/own cancellation cannot rewrite source facts
or bypass Q1; slow delivery cannot silently change a known wait; delivery is bounded
or explicitly awaited under a defined policy; there are no detached unowned tasks,
implicit unbounded queue or shutdown cycle. Exact timing/API compatibility is an
Innovation choice, not presumed here.

### Q6 — What evidence closes the prerequisites before integrating another fix?

Q6.1 Which cross-role matrix exercises the whole contract? Q6.2 Which currently
passing source/state/progress behaviors must remain unchanged? Q6.3 What can only
be demonstrated later with real accounts?

Verification: actual SDK/SQLite/task tests cover the Cartesian fault boundaries
that matter, with real outcome/charge/token/waiter evidence; the existing46 pool
groups and preserved core probes remain useful controls; no timer/fake creates the
property under test. Two-account E1 stays separate and requires supplied resources.

## 5. Interfaces, including assumptions

| Source → consumer | What flows / direction | Assumption that must become explicit |
|---|---|---|
| Q1 → Q2/Q3/Q5 | live operation provenance and control role; one-way | authority belongs to this pool and this live operation, not merely the current task or a global callback bit |
| Q2 → Q4 | completed source value/error/prefix plus authenticated attribution; one-way | completion is stable before secondary delivery; original exception identity/provenance retained |
| Q1 ↔ Q3 | stop request, retained ownership and quiescence receipt | waiting cannot be admitted if it closes a dependency cycle; end means actual task settlement |
| Q3 → Q4 | usable/quarantined/retired local client fact | local cleanup is not a Telegram health verdict or durable quota refund |
| Q4 → Q2 | definite durable permission and chosen account/group | a lost CAS response supplies no permission; status is advisory, send guard remains authoritative |
| Q2/Q4 → Q5 | plain events/results suitable for observation | no live-client/control capability is implied; observer response grants nothing back |
| Q5 → Q1/Q2 | delivery completion/fault where the selected API waits | secondary event, never an implicit source error or external stop request |
| Q4 ↔ existing progress engines | MessageBatch/error-prefix input; exact ack/replay protocols | source-attempt recovery cannot settle a group receipt; replay performs no source admission |
| Q1–Q5 → Q6 | declared invariants and actual boundary hooks | tests observe the implementation, not a helper supplying the desired ownership |

Apparent Q1/Q2/Q3 cycles are resolved by agreeing their contract before choosing
mechanisms: stop intent, retained task and resulting fact are separate directions.
They are not permission for cyclic awaited execution. Source→observer→close→source
must be refused or structurally removed, not implemented as an interface loop.

## 6. Dependency order

1. Establish Q1 and Q2's shared operation contract first: provenance, terminal source
   fact and stop precedence. Each is independently explainable through the other’s
   declared interface, but their cheap composition proof must be joint.
2. Q3's retirement policy already has implementation/evidence; qualify it against
   that contract. Q5 can compare dispatch choices once Q1/Q2 fix authority rules.
   These analyses may be independent after interface agreement; this traverse still
   runs disciplines sequentially as required.
3. Q4 integrates those results into the retained router/state/receipt contracts.
   It should not be a rewrite of selection or storage absent contrary evidence.
4. Q6 probes each boundary early, then their assembled composition before product
   implementation; the real two-account gate follows only when its prerequisites
   exist. Qualification is not postponed until all downstream work has been rebuilt.

This is a conceptual dependency order, not a new implementation plan or authorization
to write production code. Further splitting is stopped because each question has
explicit inputs/outputs and directly verifiable criteria; splitting by exception or
callback implementation would reintroduce the hidden coupling being removed.

## 7. Self-evaluation and reassembly

| Dimension | Result / evidence |
|---|---|
| Independence | PASS through the named interfaces; no claim that unknown Q1/Q2 semantics can be coded independently |
| Completeness | PASS: revision diagnosis, live/durable ownership, source/observer result, retirement, preservation, reuse alternatives and evidence boundaries all covered |
| Reassembly | PASS: Q1 controls entry; Q2 supplies true result; Q3 settles lifetime; Q4 records/routes/delivers; Q5 reports; Q6 demonstrates their composition |
| Tractability | PASS: six bounded questions, with Q1/Q2 subquestions exposing the hard distinctions |
| Interface clarity | PASS: data, authority, stop intent, facts and assumptions are stated separately |
| Balance | PASS: control/provenance, result precedence and retirement are separate substantive burdens; other pieces preserve/integrate rather than conceal one giant task |
| Confidence | PASS: top-down/bottom-up agree; dispatch timing remains an explicit option rather than a false certainty |

Determination-mechanism check: Q1 explicitly owns recognition of live/stale/foreign
operation provenance; Q2 owns recognition of source completion and stop origin;
Q3 owns actual cleanup success/failure; Q4 owns definite/uncertain CAS. No load-bearing
runtime predicate is assumed already available.

The original two defects and the backend/success counterchecks all map to Q1/Q2,
with Q3 required to retain the fixes' safety. The six current control groups map to
Q3/Q4. New abstractions must justify themselves inside these boundaries; reuse of
existing routing/state/progress remains a live candidate for Innovation.

Checker unavailable; manual structure7/7 and full quality7/7 PASS. No premature
partition, hidden coupling, missing determination piece, over-decomposition, ignored
dependency or imbalanced residual identified. **Verdict: PROCEED.** Next: Innovation.
