# Decomposition — source attempt refinement, iteration 2

## User Input

`_branch.md`, current Sensemaking SV6 and `decomposition_iter1.md`. Preserve the
five established pieces; expose the attempt boundary within P1/P2/P3.

## 1. Coupling map

Admission token, account row, known deadlines and settlement form one strongly
coupled state transition. Timeout timer, child task termination and completed
records form a second cluster. Their only necessary cross-boundary object is an
owned outcome: token, account, source result/error and optional prefix. Existing
group pending/receipt remains outside both clusters.

## 2. Top-down boundaries

Q1: durable account permission; Q2: bounded source outcome; Q3: router settlement
and delivery handoff. Q1 does not perform network work. Q2 does not persist quotas
or progress beyond the existing SDK guards. Q3 does not infer what an unresolved
task did. These are focused subquestions of P2, P1 and P3/P4 respectively.

## 3. Bottom-up check

Atoms: exact raw CAS expectation, attempt UUID, known deadline, source task,
CancelledError, complete MessageBatch, saved receipt. The first three fit Q1,
next three fit Q2, receipt remains existing P4. The token/outcome crosses to Q3
without splitting any atomic budget reservation or message record. HIGH confidence.

## 4. Question tree

Root: how is a source attempt safe across timeout, store failure and restart?

**Q1 — What grants and retires an account attempt?**
- [ ] Confirmed durable admission precedes any source call.
- [ ] Exact token-specific settlement; no expiry-based clearance.
- [ ] Missing/corrupt known state refuses; explicit first initialization.
- [ ] Recovery names the exact token, quiescence assertion and retry-not-before;
  retained prohibitions cannot be shortened.

**Q2 — What does a bounded source operation return at each exit?**
- [ ] Success batch; original ordinary error with prefix; owned timeout with
  completed prefix; caller cancellation unchanged.
- [ ] Child ended before timeout is treated as failover-eligible.
- [ ] Unknown identity and duplicate declared/known credential aliases cannot
  yield a history read attributed to another slot.

**Q3 — How do state and output settle together without pretending atomicity?**
- [ ] Store failure stops the call and leaves durable uncertainty when unsettled.
- [ ] Complete records survive in local pool error.partial_result with interrupted
  semantics; original source failure is separate read_error.
- [ ] Existing progress engines own publication and ack; pool state never has
  an accepted group cursor or receiver receipt.

## 5. Interfaces and assumptions

Caller→Q1: explicit initialization/recovery intent, exact token, truthful quiescence;
not a promise that Telegram was healthy. Q1→Q2: confirmed permission plus immutable
account/group request. Q2→Q3: quiescent outcome and complete records. Q3→Q1: one
CAS transition settling that permission and preserving all stronger prohibitions.
Q3→existing P4: ordinary MessageBatch/exception-prefix contract. A failed response
from any store write is not a rollback assertion. Returning data and recording
restrictions are not claimed to be one distributed transaction.

## 6. Dependency order

Define Q1/Q2 outcome contracts, establish both mechanisms, then Q3 composition.
They refine P1/P2 before the original P3 router; P4/P5 follow the unchanged
decomposition order. No circular construction dependency or new global scheduler.

## 7. Self-evaluation

Independence PASS (state vs source mechanisms); completeness PASS (all two prior
refinement targets plus alias/unknown identity); reassembly PASS (token/output joins
are explicit); tractability PASS (two small mechanisms and one composition);
interface clarity PASS (uncertainty not hidden); balance PASS; boundary confidence
PASS (atoms agree). Determination mechanisms: active=validated stored token,
quiescent=awaited task or explicit caller assertion, prefix=complete records from
actual reader, settlement=exact CAS success. No missing predicate. Seven failure
modes checked; no arbitrary extra pieces. Next: Innovation of the concrete state shape.
