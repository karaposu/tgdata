---
model: gpt-6-astra
effort: max
---
# Decomposition — the joining contract

## User Input

_branch.md and saved sensemaking.md: separate the remaining Stage5 questions at
their natural boundaries, preserving all6 articulated alternatives and the
measured SDK/ledger constraints. This is a question partition, not an implementation plan.

## 1 — Coupling map

The irreducible high-coupling cluster is **fresh owner proof → committed claim →
synchronous enqueue**. Moving one across an await changes the meaning of all three.
Keep that cluster together. Likewise source response classification and what the
public result asserts must remain together: separating them would invite a generic
“success” value that loses pending/payment/interaction meaning.

| Cluster | Strong internal coupling | Weaker external connection |
|---|---|---|
| Entry/eligibility | expected account, supplied allowance, supported reference, preflight observation | passes a verified operation and qualified target into admission/dispatch |
| Admission | active task/lifetime, fresh self, ledger claim, exact enqueue | receives budget/handle; returns source future or refusal |
| Source outcome | request kind, actual response/RPC name, acknowledgment versus incomplete state | produces immutable result facts for caller; no storage settlement |
| Aftermath | optional enrichment, primary-result/error precedence, health proof, teardown | consumes source facts and the existing owned lifecycle |
| Qualification | real SDK paths, failure injection, overlapping operations, public docs | checks each interface; no production mechanism of its own |

Changing a public target grammar changes entry tests, not quota SQL. Changing a
result's evidence threshold changes projection/docs/health expectations, not the
owner proof implementation. Changing admission placement changes identity and
charge timing together. Existing ledger, lifecycle and health are prerequisites,
not pieces to rebuild merely because this partition names their interfaces.

## 2 — Top-down boundaries

B1: caller policy/reference → an owned operation plus target observation.
B2: group resolution → join request identity; never re-resolve a public handle
inside a later mutation after a concrete channel peer has been observed.
B3: pre-admission work → the coupled proof/claim/enqueue cluster.
B4: source answer → qualified outcome, before optional cache/metadata work.
B5: source outcome → caller/health/cleanup effects, whose proof requirements differ.

These are conceptual seams, not instructions to create five classes or modules.
The new behavior can remain a small consumer of existing structures.

## 3 — Bottom-up boundary check

Atoms: one supplied account ID; one resolved input peer/invite token; one fresh
self result; one synchronous claim transaction; one SDK enqueue; one decoded answer
or original error; one immutable returned observation; one owned disconnect attempt.

Self/claim/enqueue group naturally under B3, not three separately callable stages.
An invite token cannot be replaced by an unrelated chat from an updates vector;
that target/outcome association crosses B2/B4 explicitly. Optional entity processing
does not belong inside the definition of source acknowledgment. Existing owned
cleanup is coherent independently of the chosen target grammar. Top-down and
bottom-up agree on all5 boundaries: HIGH confidence. No extra split is justified.

## 4 — Question tree and completion criteria

### Q1 — What may a caller ask this operation to do, with which policy?

Decide facade versus per-call configuration and supported references using existing
contracts. Determine missing budget/policy, zero allowance, already-member and
known payment-required preflight behavior. Verification: explicit entry contract;
no guessed default; no mutation from unsupported inputs; read-only preflight is not
charged as a join; a result never invents an unknown peer. Independent once the
existing expected-account and target-parser interfaces are given.

### Q2 — How is every new join attempt admitted for the right account?

Determine the actual SDK boundary and its ownership/lifetime preconditions. Runtime
determination is explicit: recognize the supported join request/wrapper, use the
current operation handle, run fresh proof, commit claim, call the real sender with
no intervening await. Verification: mismatch/missing auth sends0/charges0, cached
waits charge0, each SDK retry gets a new claim, post-claim failures retain charge,
and no broad raw-client guard is claimed without an ownership contract.

### Q3 — What does each source answer establish?

Determine valid Ok/WebView payloads and named RPC outcomes using selected1.45
classes and real decoding. Verification: joined/already-member are distinguishable
from requested/payment/interaction; malformed or unsupported replies cannot become
joined; ordinary RPC/transport errors retain type/object; result values are frozen,
qualified by owner/target and contain no transport secrets. Unknown IDs stay unknown.

### Q4 — What happens after acknowledgment or failure?

Determine whether cache/metadata enrichment is needed, and how it can remain optional.
Verification: optional failure cannot erase a validated acknowledgment; cancellation
remains cancellation; no mandatory post-ack network request changes an outcome; read
denial clears only through actual read proof, not join metadata. Existing cleanup
settles before return and callbacks remain separate. No new recovery journal or
refund path is hidden behind “reliable joining”.

### Q5 — What evidence and public explanation qualify that contract?

Define adversarial offline cases against real SDK dispatch and ledger storage,
including stale-cache/actual-owner mismatch, changed identity before enqueue,
wrapped responses, interrupted joins, source-error exhaustion and forced overlap.
Verification: component prototypes are distinguished from delivered code; public
tests cover the actual facade/factory composition; existing suites remain compatible;
docs state live/packet-count/raw-client limits. No proof is borrowed from mock-supplied
success or from an older rejected implementation.

## 5 — Interfaces, including assumptions

| From → to | Flow / direction | Assumptions that must be explicit |
|---|---|---|
| Q1 → Q2 | verified handle + configured ledger + immutable request intent, one-way | shared current task; no credential replacement or detached request mutation |
| Q1 → Q3 | preflight lookup and pinned peer/token, one-way | prior metadata is not a newer membership/read observation |
| Q2 → Q3 | actual source response or original exception, one-way | one claim already consumed; failure may follow a real remote mutation |
| Q2 → Q4 | charge/attempt uncertainty fact, one-way | no refund/settlement or reusable permit |
| Q3 → Q4 | qualified result/evidence category, one-way | acknowledgment, membership and read access are distinct |
| Q4 → caller | primary outcome after owned cleanup, one-way | cleanup diagnostics cannot replace it; caller cancellation is preserved |
| Q1–Q4 → Q5 | interface contracts and runtime determination mechanisms, one-way | tests must drive real mechanisms, not manufacture their desired decisions |
| Q5 → Q1–Q4 | observed counterexamples, feedback | a failed premise reopens its question; it is not patched away in a test |

The feedback is evaluation, not a circular runtime dependency. Shared mutable
health state, hidden account inference, transport packet retries and source-time
target identity have all been named rather than assumed absent.

## 6 — Dependency order

Define Q1's ownership/policy interface first. Q2's admission mechanism and Q3's
response contract can be reasoned about independently against that interface.
Q4 consumes the outcome boundary. Q5's criteria are established alongside each
question and applied to the assembled behavior before implementation acceptance.
The cognitive runner still executes sequentially; no subagents are implied.

## 7 — Self-evaluation

| Dimension | Result / reason |
|---|---|
| Independence | PASS — each question has explicit prerequisites, no sibling internals |
| Completeness | PASS — all6 variants, failure/ownership and source/afterward boundaries covered |
| Reassembly | PASS — entry → admission → source outcome → aftermath → qualification forms the whole |
| Tractability | PASS — five bounded questions; no generic platform or transport rewrite |
| Interface clarity | PASS —8 flows include temporal/evidence assumptions, not only data |
| Balance | PASS — admission and interpretation carry comparable complexity; neither hidden in “wire it up” |
| Confidence | PASS —5 boundaries agree with the atom check |

Determination-mechanism check: Q1 decides eligibility from actual parsed input and
policy; Q2 identifies requests and verifies owner; Q3 classifies actual SDK shapes
and error names; Q4 decides evidence/secondary work. No load-bearing “is valid” or
“is joined” predicate is assumed to arrive by magic. All7 failure modes checked;
no recursive decomposition or DV2 is needed. Stop: pieces are directly verifiable.
