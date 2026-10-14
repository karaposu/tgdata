---
model: gpt-6-astra
effort: xhigh
---
# Decomposition — photo-trail contract

## User Input
_branch.md's four readings, refined by the committed sensemaking.md SV6: optional conservative, revisable inference over bounded current observations; original records and source acceptance remain separate authorities.

## 1. Coupling Map

The whole contains observation selection, current album/member identity, sender/photo/time/reply checks, relation construction, resource policy, versioned provenance, downstream replacement, persistence/restart and source ack. Strong clusters are (a) selected evidence plus temporal/member ordering, (b) eligibility/barriers/chain limits plus inferred relation semantics, (c) the relation plus preserved originals/validation/revision, and (d) strict retained-data loading plus transaction/snapshot integrity. These are conceptual clusters, not instructions to create four frameworks or packages.

Changing observation scope can change inferred relationships: moderate, explicit input-contract coupling between a and b. Changing heuristic rules changes result provenance and validation: moderate contract coupling between b and c. Within b, time/reply/author/barrier decisions must stay together; splitting each predicate into an independently governed subsystem would cut strong semantic bonds. Within c, a result and its validator must agree exactly. Original-record acceptance and optional projection have weak one-way coupling through durable data; forcing them into one transaction outcome would introduce unnecessary strong coupling. Source receipt acknowledgment consumes original acceptance, not the inferred relation: no new runtime dependency on the heuristic.

## 2. Top-Down Boundaries

B1: a validated, explicit observation set separates collection/storage from inference. B2: a deterministic relation computed from that set and policy separates inference from serialization/presentation. B3: an immutable full-view result separates library facts/inference from application replacement and downstream processing. B4: original-record acceptance remains separate from bounded view construction. Boundaries B1–B3 require explicit assumptions; B4 is already implemented and qualified by #29.

## 3. Bottom-Up Validation

Atoms: original raw member with ID/content; TelegramPost stable ID/revision; sender peer identity; member time/reply/photo fields; policy parameters; association edge; complete inferred view; original source receipt; committed member/marker transaction. No atom is split. One member cannot be partially rewritten to fit a heuristic, and an inferred edge cannot exist without its source and target evidence. Top-down and bottom-up agree at all four boundaries: HIGH confidence. B2's result-wire validation may call the same deterministic rule, but that is a one-way dependency, not a second policy authority.

## 4. Question Tree

### Q1 — What exact current observations and ordering can a fold claim to cover?

Answer independently from the inference algorithm using MessageBatch/TelegramPost and the caller's intended observation scope.

Verification criteria: [ ] explicit finite input/scope and required prior-context contract; [ ] same-chat/member identity and mixed-mode/duplicate/conflict handling; [ ] source ordering and interleaved/overlapping album intervals; [ ] no absent-context/completeness claim; [ ] bounded input materialization; [ ] late observations and snapshot replacement semantics stated. This is the determination mechanism for “current context”, not an assumption that a caller already made it true.

### Q2 — Which observable relation is safe to infer under a selected policy?

Verification criteria: [ ] opt-in identity/photo/text/reply/time rules; [ ] determination of eligible anchor versus follower and uncertain barriers; [ ] chained gap plus whole-trail count/duration limits with exact units; [ ] no reverse text merging; [ ] deterministic treatment of interleaved users and unknown authors; [ ] partition/order/replay properties within Q1's contract; [ ] unsupported evidence remains separate or explicitly refuses, never silently disappears.

### Q3 — How does the result preserve facts and expose replaceable inference?

Verification criteria: [ ] original post IDs/revisions/members unchanged and inspectable; [ ] relation provenance, policy/version and unambiguous counts; [ ] canonical immutable value and malformed saved-state refusal; [ ] revision covers interpretation dependencies; [ ] a changed observation set can withdraw an old relation; [ ] whole-operation member/byte bounds; [ ] application replacement/undo examples. “Replaceable” is a concrete full result contract, not a promise that the library updates a remote consumer itself.

### Q4 — How does one caller retain enough evidence across batches and restarts without changing source authority?

Verification criteria: [ ] reuse or justify a new retention boundary explicitly; [ ] missing known state refuses; [ ] consistent bounded reconstruction with no silent eviction or arbitrary default tail; [ ] exact accepted-input confirmation survives larger views; [ ] real SQLite/source-engine commit-before-ack, lost replies and restart; [ ] projection failure does not invalidate accepted original data; [ ] downloaded media custody remains explicit; [ ] example spans calls/restart and actual late observation/replacement. These criteria make A/C's storage composition or B's retained-state obligations reviewable.

## 5. Interface Map and Assumptions

Q1→Q2: data = validated current original posts and a declared observation scope/order. Assumptions = caller has supplied the intended evidence, not a globally complete Telegram history; no inference across silently omitted relevant context. Q2 must not pretend it can detect unseen messages.

Q2→Q3: data = deterministic associations and the exact policy/decision basis. Assumptions = one home for rule semantics; result validation cannot accept invented edges merely because a caller recomputed a hash.

Q1→Q3: data = canonical original observations. Assumptions = all originals remain recoverable and represented exactly once in a view, whether attached or separate.

Q4→Q1: data/resource = a consistent bounded snapshot of retained original facts, or explicit serialized context if that alternative is selected. Assumptions = lookup failure is not absence; policy refusal is not permission to reset; persistent growth does not force unbounded loading.

Q3→application: full replacement view and explicit provenance. Assumptions = application owns scope identity, atomic replacement and any external work. Irreversible upsert-only handling cannot silently consume retractable guesses.

Existing acceptance→source ack: original batch/full backfill receipt only. Q4 may demonstrate this interface but Q2/Q3 cannot create or broaden it. Changes to inference policy do not force new Telegram calls or rewrite raw receipt identity.

## 6. Dependency Order

Set Q1's interface first; then Q2; then Q3's validated output; finally Q4's complete composition. Retained existing acceptance is available now, but the bounded-view adapter cannot be designed before Q1 is settled. Q2's semantic predicate can serve Q3 validation without importing a public output class, avoiding a cycle. Offline behavioral evidence accompanies each question; the complete composition must run before adopting implementation. No parallel agents are used in this inquiry.

## 7. Self-Evaluation

Independence PASS: each question is answerable through declared input contracts. Completeness PASS: all requested safety, retention, provenance, replay and opt-in dimensions appear, including runtime determination of context/eligibility. Reassembly PASS: durable original facts→bounded observations→deterministic relation→replaceable view, while the unchanged original receipt settles source progress. Tractability PASS: each question is one focused design decision; no new source coordinator or scheduler. Interface clarity PASS: data, assumptions and resources named. Balance PASS: ordering/eligibility and retention carry most work, but are separately bounded rather than hidden in one enormous “integration” piece. Confidence PASS: all four top-down cuts agree with irreducible atoms.

Seven failure modes checked: prior sensemaking prevents premature cuts; predicates stay together; hidden ordering/absence/replacement assumptions are explicit; all runtime determinations have a question; no predicate-level over-decomposition; dependency order is acyclic; hard retention work has its own bounded question. Structural manual check7/7; no further decomposition needed at this depth. The next discipline chooses a coherent answer to Q1–Q4 from the preserved alternatives, not a file-per-question implementation plan.
