# Decomposition — receiver refinement

## User Input

_branch.md and current sensemaking.md SV6, with the fixed first-pass whole and critique dimensions. Refine the receiver's creation/reopen and acceptance contract, preserving the smaller pure assembly architecture.

## 1. Coupling Map

The four clusters remain: post identity/representation; deterministic combination/refusal; receiver acceptance; qualification. The new inspection shows creation/open validation is strongly coupled to authoritative prior lookup, which is strongly coupled to the receiver write transaction. Source acknowledgment remains a separate assertion after acceptance. No new source-state dependency appears.

## 2. Top-down Boundaries

Keep the value/combiner boundary and pure-operation/receiver boundary. Put explicit creation, require-existing reopen, logical collection selection, schema validation, prior lookup, post persistence and raw input recognition inside the receiver contract. Do not split these into independently bootstrapping stores. Keep media-byte custody explicit at the caller boundary.

## 3. Bottom-up Validation

Indivisible facts: an opened authoritative collection, an individual-key lookup result, a prior immutable post, a new input batch, a commit and the existing source receipt. An absent collection is not the same atom as an absent post key. Actual SQLite probes establish the distinction and transaction behavior. All three prior boundaries still agree with this atom grouping; confidence HIGH. No additional generic engine is needed.

## 4. Question Tree

**Q1 — What value is stored?** Stable chat/group or chat/message identity; lossless original members/captions/media; canonical immutable serialization/revision; explicit unconfirmed global membership for albums. Verification: big IDs, cross-chat separation, multiple captions, immutable round-trip and no false complete flag.

**Q2 — How is new input combined?** Require an explicit prior-state mapping for every affected post identity; validate prior values and media-mode compatibility; merge identical records idempotently and refuse incompatible observations/bounds without mutation. Verification: arbitrary batch splits, nonadjacent members, exact replay, changed-record conflict, missing/extra/wrong prior entries, byte/count refusal. This operation performs no I/O and does not own a source cursor.

**Q3 — When is it safe to acknowledge?** Explicitly create a chosen receiver collection or reopen a known one; reject missing file/schema/collection and failed/corrupt prior lookup on reopen. Load prior values inside the transaction, persist all accepted post snapshots with a collection-scoped input marker, commit, then acknowledge with the original source receipt. Verification: missing known state, partial schema, collection typo, failed write, lost commit reply, lost source ack, duplicate input after later membership grew, and two collections with equal batch IDs. A data capture/partial_result alone is not proof of an owed durable source receipt; examples must obtain normal delivery or confirmed pending replay before acknowledging.

**Q4 — What proves the integration?** Keep the existing component evidence as baseline, then run the actual candidate value/combiner and real receiver storage together with MessageBatch/SDK serialization and daily/backfill prepare/replay/ack before production adoption. Verification: named deterministic expectations, source bounds/cursors unchanged, complete focused failure histories, full baseline suite. Vendor completeness is not inferred from fake replies or local storage; the first API promises only observed membership.

## 5. Interface Map

1. Reader→Q1/Q2: immutable raw values; no completeness or collection certificate is invented.
2. Q1→Q2: validated post identity/member representation; original captions remain data.
3. Authoritative receiver lookup→Q2: exact required key mapping; None only means observed key absence after successful validated open.
4. Q2→receiver: new immutable observed posts; original raw input/receipt remains available separately.
5. Receiver→raw acknowledgment: durable acceptance assertion in the selected logical collection, using the original batch ID/full delivery reference.
6. Receiver reopen→retry: saved post observations and collection-scoped duplicate marker; missing known state is an error.
7. Q1–Q3→Q4: concrete obligations and failure points; actual evidence feeds the later task description/plan.

Assumptions-not-data: backend lookup failure must raise; current-prior lookup and writes are transactional or conditionally consistent; source partial data is not automatically an acknowledgment credential; media bytes need independent durable custody; externally corrupt/rolled-back storage is not repaired by inventing an empty state.

## 6. Dependency Order

Fix Q1/Q2 value interfaces, then build the concrete Q3 receiver integration against them. Q3 opening/lookup semantics are specified before implementation, not discovered afterward. Q4's existing-component checks are complete; the new combined candidate remains a mandatory prebuild before product code. Runtime lookup→combine→write is a single receiver operation, not a circular design dependency.

## 7. Self-Evaluation

Independence PASS: each question uses defined inputs. Completeness PASS: the previous missing opening lifecycle is now included. Reassembly PASS: authoritative prior-state determination and accepted-data ownership have named mechanisms. Tractability PASS: four focused pieces; no new engine. Interface clarity PASS: failures/absence/namespace are explicit. Balance PASS: combination and acceptance carry the real complexity. Confidence PASS: existing probe results agree with the boundaries. No premature or excessive splitting, hidden lookup assumption, missing determination, dependency inversion or unbounded integration remainder. **PROCEED** to Innovation.
