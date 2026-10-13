---
model: gpt-6-astra
effort: max
---
# Decomposition — independent facts and owners

## User Input

_branch.md/A1 and all four articulations, with saved sensemaking.md SV6. The output
is a partition of the contract questions, not a stage-by-stage implementation plan.

## 1 — Coupling Map

The whole: a pool may stop a read while data, storage, caller code and cleanup are at
different stages. It must finish only its owned work, retain known data for its owner,
and leave permission/ack/allowance decisions with their existing authorities.

| Elements | Coupling | Why changes propagate |
|---|---|---|
| Active invocation, stop address, busy release, owned children, close barrier | Strong | Each determines when cancellation/retirement/reuse can occur |
| Completed message data, retained recipient, exposure/finalization, retrieval lifetime | Strong | A handoff guarantee is meaningless without who retains and retrieves it |
| Account CAS, exact attempt recovery | Strong internally | Both address the same durable permission token |
| Group pending/receipt/ack | Strong internally | Receiver acceptance advances the saved group position |
| Source/operation and account CAS | Moderate | Source admission/settlement order, no shared definition of “done” |
| Available data and group receipt | Moderate | Same observations may be stored, but only stored context authorizes ack |
| Stop signal and data recipient | Moderate | Stop changes control status; it cannot own/delete completed data |
| Caller Task and operation | Moderate | The Task is a cancellation address; application continuation is separate |
| Passive health observations and authorities | Weak | Diagnostic data can be lost without granting permission or progress |
| Pool boundary and scheduler/distributed ownership | No required coupling | Those are excluded product responsibilities |

High-coupling clusters stay together: lifetime/control, data/handoff, each durable
authority. There is no natural boundary that splits “cancel then finish cleanup” into
independent policies or combines every result into one completion bit.

## 2 — Top-down boundaries

B1: library-owned invocation versus application continuation. Stop may be addressed
to its caller, but completion concerns only work admitted under this invocation.
B2: control signals versus retained data. A data owner must exist before a wrapper can
replace the signal; a particular CancelledError instance is not that owner.
B3: available data versus authoritative state. Account permission, quota and delivery
ack remain separate; retrieval does not create state success.
B4: operational guarantee versus calling form/runtime. Public forms must state what is
retained and where, without promising all cancellation-exception identities.
B5: described contract versus qualification. Proof must compose these pieces; individual
happy paths do not establish their interaction.

## 3 — Bottom-up validation

Atoms: one actual send/reservation; one source value/error; one provider invocation and
its reply; one write commit; one stop request; one owned-child termination; one complete
record; one scoped group receipt; one application continuation after the call; one native
client retirement. These atoms group into B1–B5 without splitting a required causal link.

B1/B2 are independently falsified by the new probes, so neither can be omitted. B3 is
supported by the inherited actual CAS/ledger/replay controls. B4 remains a contract choice
constrained by runtime evidence, not a reason to collapse B2 into a chosen implementation.
B5 prevents a wrapper-level pass hiding an owner-level failure. Top-down/bottom-up agree:
HIGH confidence for all five boundaries. No module-per-piece or exception-type-per-piece
split is justified; that would reproduce the previous boundary omissions.

## 4 — Question Tree and verification criteria

### Q0 — Which contract makes #17 reliable and small enough to understand?

Answered when Q1–Q5 and their interfaces reconstruct a bounded operation with correct
stop, completion, handoff, durable authority and caller behavior.

### Q1 — What is the owned invocation, and who may stop or finish it?

Keep stop addressing and owned completion in one lifetime piece.
- [ ] Define admission/start/end of the invocation independently of application Task end.
- [ ] Determine completion from actual source/provider cleanup and guard release, not a
  timeout or public-task result retrieval; give it a concrete runtime witness.
- [ ] Identify the exact current operation before a stop request; a stale stop must not
  cancel later application work or a successor operation.
- [ ] Preserve cancellation provenance, repeated-stop joins, reentry refusal, all-source
  retirement and failed-cleanup quarantine.
- [ ] Close can finish while the application continues its own post-call cleanup.
- [ ] Source-free progress/status I/O retains its already-defined separate caller ownership.

### Q2 — Who owns completed data, and what is the handoff?

Keep retention, finality and retrieval together.
- [ ] Identify a bounded recipient that exists before data can be lost through cancellation.
- [ ] Capture only actual validated records; define no-data, provisional/available-data and
  final success/error/cancellation observations distinctly.
- [ ] No new await or arbitrary application callback is required merely to retain local data.
- [ ] Late callers and documented wrapper compositions can retrieve data from that recipient
  without depending on the original cancellation exception object.
- [ ] Later operations, close and diagnostic draining cannot overwrite/consume another
  invocation's retained data; caller discard/process death are explicit limits.
- [ ] Interrupted data does not supply history-end evidence or a saved delivery receipt.
- [ ] Storage and source failure metadata remain distinct, safe and bounded; retention must
  not accidentally keep an unbounded graph of live tasks/tracebacks/providers.

### Q3 — Which authority can certify permission, allowance or accepted progress?

Existing durable components are independent pieces internally; this question defines the
fence the revised invocation must respect, not a replacement unified journal.
- [ ] Only definite account admission permits source work; unknown replies never mean rollback.
- [ ] A stopped invocation cannot refund sends, shorten waits or clear an unresolved token.
- [ ] Only real group pending/receipt state and explicit acceptance may advance progress.
- [ ] Keep existing backfill exact non-admission reconciliation, exact recovery arguments,
  and source-free replay/ack after close.
- [ ] State availability and data availability may disagree without one being fabricated.

### Q4 — What can an application rely on at each public calling boundary?

This piece consumes Q1/Q2/Q3 contracts rather than silently selecting a representation.
- [ ] State the contract for direct await, a public Task, timeout/cancellation wrappers,
  and deliberate application abandonment.
- [ ] Preserve genuine cancellation and normal result/error behavior, or make any new
  required calling form/API choice explicit as an unmerged interface change.
- [ ] A convenient facade must not claim retrieval that its caller cannot address.
- [ ] Old Python syntax support must not become an untested payload-retention claim.
- [ ] Keep ordinary TgData/#7/#10 policies independent unless a demonstrated interface
  dependency requires touching them; no new scheduler/worker protocol by implication.

### Q5 — What evidence distinguishes a contract from another promising example?

- [ ] Reproduce both PR rounds and the storage prebuild failure mechanisms.
- [ ] Include caller continuation, first-consumer order and wrapper-induced signal replacement.
- [ ] Cross those with real source results/prefixes, source/provider interruption, before/
  after commits, true/repeated caller stop, cleanup failure and post-close access.
- [ ] Observe actual data, source sends/charges, durable rows, child completion and recipient
  availability separately; no stand-in supplies the expected batch/token/receipt.
- [ ] Bound experiments externally; forced kill is failure, not quiescence.
- [ ] Mark inherited-without-retest and live E1 honestly; concept evidence is not a merged
  implementation or whole-feature acceptance.

## 5 — Interface Map (including assumptions)

| From → to | What flows / direction | Assumption explicitly rejected |
|---|---|---|
| Q3 → Q1 | Existing admission/recovery constraints; one-way | “Cancelled response means the write did not happen” |
| Q1 → Q2 | Invocation identity, actual source completion and final owned end; one-way | “Task done describes the source and every owner” |
| Q2 → Q1 | Local handoff-complete condition if required before release; one-way contract | “Writing to a recipient may await arbitrary user work” |
| Q3 → Q2 | Receipt/durability boundaries; one-way | “Available batch means pending/acknowledged” |
| Q1/Q2/Q3 → Q4 | Named guarantees, stop authority and retrieval address; one-way | “A useful wrapper will preserve arbitrary exception fields” |
| Q4 → Q1/Q2 | Calling-lifetime/retention requirements; contract-level feedback | “The entire application Task belongs to tgdata” |
| Q1–Q4 → Q5 | Independently observable invariants; one-way | “Separate passing tests prove the composition” |
| Q5 → Q1–Q4 | Counterexample/refinement evidence; inquiry feedback | “Failure is a reason to weaken the requirement” |

The apparent Q1↔Q2 and Q4 feedback is resolved by defining the handoff contract before
any mechanism is built. It is not a runtime await cycle. Q1 must never wait for user
consumption, only any specified local retention; Q2 retrieval must not start source,
control the pool or certify a write. No hidden shared cancellation counter is an interface.

## 6 — Dependency Order

Reasoning order, **not an implementation plan**: retain Q3's established constraints;
settle Q1 and Q2 as independent-but-interfaced obligations; reconcile Q4 with both; use
Q5 to test the resulting composition before accepting it. Q1/Q2 can be considered
independently once their identity/handoff terms are fixed; this traverse still runs
sequentially and uses no subagents. Any failed determination sends the inquiry back
to that contract, not to compensating code elsewhere.

## 7 — Self-evaluation / reassembly

| Dimension | Result | Reason |
|---|---|---|
| Independence | PASS | Five purposeful questions with explicit input contracts |
| Completeness | PASS | Stop, owned end, data, durable authority, caller surface and evidence covered |
| Reassembly | PASS at contract level | Q1–Q4 plus Q5's observations reconstruct Q0; representation remains open |
| Tractability | PASS | Each question fits one focused pass; existing authorities are preserved, not rebuilt |
| Interface clarity | PASS | Data and assumptions/timing are both listed; runtime wait cycle forbidden |
| Balance | PASS | Q1/Q2 are the two measured hard boundaries; Q4 qualifies their public meaning |
| Confidence | HIGH | Top-down clusters match independent runtime counterexamples and atoms |

Determination-mechanism check: source/body completion belongs to Q1's actual producer;
provider cancellation provenance to owned invocation; owned end to a completion witness;
data availability/finality to Q2's recipient; commit/receipt to Q3. No piece presupposes
these determinations from an unexamined Task.done or exception type. All7 failure modes
checked. No DV2 needed: boundaries are not yet a chosen architecture and none disagree
with the bottom-up atoms. Stop decomposition here; smaller pieces would separate the
strongly coupled lifetime or handoff rules. **PROCEED to Innovation.**
