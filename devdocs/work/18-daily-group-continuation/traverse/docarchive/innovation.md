---
model: gpt-6-astra
effort: max
---

# Innovation — daily continuation

## User Input
The four questions in decomposition.md, constrained by sensemaking.md SV6 and all
four _branch.md articulations. Produce a usable daily-continuation approach before
the implementation description/plan. Preserve all explicit user exclusions.

## Seed and mode

Seed type: gap/collision — immutable Telegram observations meet a durable consumer
checkpoint. Direction/valuation: reliable daily scraping after missed runs and
failed delivery, with little consumer bookkeeping.

Inherited mode: Standard default, production-task piece list Q1–Q4. Alternative:
Contrarian-rethink (Framer-weighted) could replace library state with a receiver-owned
cursor or make the destination drive reads. That may be useful when all consumers
share one database, but would rebuild each consumer's orchestration and requires
an unavailable destination integration. Run Standard default with all seven
mechanisms and explicit contrarian candidates at every meta-decision piece.

## Generation — before testing

### Q1 — identity/enrollment (meta-decision: framing and evaluation criteria)

Q1-G / generic, Combination: accept arbitrary group references at enrollment,
resolve them once, bind to a canonical chat ID and maintain alias lookup records.

Q1-F / focused, Constraint Manipulation ADD: require the canonical marked numeric
chat ID and explicit after_id for enrollment. One progress record per chat per
store; different destinations use different stores. Repeated matching enrollment
is idempotent, while a different initial cursor/mode refuses to reset progress.

Q1-C / contrarian, Inversion: reverse the canonical-source requirement and retain
only the account/session plus current username. Deeper inversion: let every new
account create its own fresh collection, with no identity link between runs.
Existence axis: zero persistent source identity. Identity axis: account inventory
becomes the dataset. These challenge P2 directly rather than merely renaming it.

### Q2 — persistence (meta-decision: durability criterion)

Q2-G / generic, Domain Transfer: use a transactional outbox pattern, with typed
backend initialize/load/stage/ack operations. Native source: database outboxes;
different-domain analogy: a dispatch ledger retains the parcel until a delivery
receipt arrives. The analogy suggests separation; SQLite behavior must prove it.

Q2-F / focused, Combination: store one validated versioned state document per chat,
containing initial/accepted cursors, media mode, optional pending MessageBatch and
last acknowledgment ID. Define only async load(chat_id) and
compare_and_swap(chat_id, expected_text_or_none, new_text) on the backend. The
library owns transition rules once; SQLite supplies the reference implementation.

Q2-C / contrarian, Inversion: remove atomic replacement and persist only a plain
cursor JSON file. Further system-level reversal: the reader always refetches and
the destination reconstructs progress, eliminating library pending state entirely.

### Q3 — batch composition (meta-decision: failure semantics)

Q3-G / generic, Lens Shifting: treat the library as a delivery executor. Invoke a
consumer callback after fetching and mark progress when it returns successfully.

Q3-F / focused, Absence Recognition: patch-level absence is durable partial output;
redesign-level absence is one place owning the read→pending transition. Compose
the existing public get_message_batch with state storage. Replay pending bytes
before any network call. Persist nonempty interrupted prefixes, then re-raise the
original read exception. A persistence failure raises a local storage error that
retains the read exception as inspectable data, not implicit Telegram health.

Q3-C / contrarian, Constraint Manipulation REMOVE: remove the requirement that
tgdata owns delivery state; return batches exactly as today and let every caller
persist the cursor and pending files. This challenges the inherited layer boundary.

Absence Recognition's reverse direction: serialization, immutable replay and
completed-prefix boundaries already exist in MessageBatch. Do not invent another
message envelope or rebuild the downloader to obtain them.

### Q4 — caller surface (meta-decision: ADD-CONTENT intervention shape)

Q4-G / generic, Domain Transfer: export an independent continuation controller
bound to a TgData and store, exposing enrollment, prepare, acknowledge and status.

Q4-F / focused, Constraint Manipulation ADD: additive optional sync_store on TgData
with asynchronous initialize_sync, sync_group, acknowledge_sync and get_sync_status.
Each sync_group prepares/replays at most one batch. None means no currently visible
new messages; a nonempty return is durable pending work. Store-only operations and
replay do not enter a Telegram health call; actual reads delegate to the existing
decorated get_message_batch method.

Q4-C / contrarian, Inversion on intervention-shape: reverse ADD-CONTENT to
REPAIR — change existing poll_for_messages into durable callback-driven polling.
The deeper zero-addition variant is DO-NOTHING in runtime plus a documentation
recipe. Both would make the old API the only entry point, rather than adding one.

### E1 — future extension, Extrapolation

If a consumer later adds backfill, keeping an explicit versioned daily-state
contract permits a separate backfill state without reversing today's cursor.
If sequential hosts use a custom backend, asynchronous storage methods allow real
remote I/O. No dormant backfill fields, leases or multi-reader scheduler are added.

### M1 — artifact retention, Lens Shifting + Combination

Under references-only collection, pending JSON is complete replay material. Under
download mode, the same JSON also requires its hash-named files. Persist media mode
at enrollment; receive the local media directory on each sync call so sequential
movement can use a different root after copying the blobs. Verify every referenced
blob before exposing a pending replay. Missing/corrupt files raise and preserve
pending state; a refetch cannot silently replace it. No automatic deletion on ack.

## Inherited Frame Audit

Seed assumptions: library-owned state (challenged by Q3-C); immutable replay
(challenged by Q2-C); explicit acceptance (challenged by Q3-G); single-reader scope
(E1 examines its later removal without undoing the user's current limit).
Q1 identity reversed by Q1-C; Q2 atomicity reversed by Q2-C; Q3 composition reversed
by Q3-C; Q4 ADD-CONTENT shape reversed by Q4-C's REPAIR/DO-NOTHING alternatives.
Every meta-decision has a generic/focused/contrarian set before testing. No audit
override or return-to-generation cycle is needed.

## Test cycle

Legend: N novelty in this repo; S scrutiny; F fertility; A actionability;
I independent grounding. A failure stops promotion, not its recording.

| Candidate | Five-test outcome and strongest objection | Disposition |
|---|---|---|
| Q1-G | N pass; S viable, but metadata resolution and alias migration add a second identity surface; F pass; A pass; I supported by existing canonical batch IDs and changing handles | DEFERRED: add alias enrollment when a consumer needs it |
| Q1-F | N pass; S canonical IDs are less convenient but unambiguous and already returned by MessageBatch; F leaves alias convenience possible; A current SDK probe accepts marked ID; I batch validation and consumer restart identity independently support it | ACTIONABLE |
| Q1-C | N variant; S fails: changing account/handle selects another cursor or applies old cursor to new history; remaining tests cannot repair that meaning | KILLED |
| Q2-G | N pass; S viable, but every custom backend reimplements domain transitions; F pass; A SQLite supports transactions; I outbox model plus lost-reply evidence | Alternative viable, not selected |
| Q2-F | N pass; S exact expected-value replacement rejects stale state and centralizes validation; F permits other stores without new domain logic; A real SQLite process/conditional-update probe passes; I lost-ack test and atomic commit observation are independent grounds | ACTIONABLE |
| Q2-C | N variant; S fails: no retained observation exists after uncertain delivery; cursor/write ordering cannot close both crash windows | KILLED |
| Q3-G | N pass; S callback success can mean queued rather than accepted; F explicit ack could wrap this later; A possible but forces receiver execution into library; I callback and batch APIs show convenience, not necessity | DEFERRED: explicit consumer demand for callback adapter |
| Q3-F | N pass; S partial persistence must report two failures accurately; F one pending path serves success/prefix/restart; A existing real SDK prefix test passes; I budget exhaustion and immutable replay independently require it | ACTIONABLE with explicit two-error contract |
| Q3-C | N fails: this is the current public batch recipe; S also leaves the user's requested continuation unimplemented | KILLED for this task |
| Q4-G | N pass; S coherent extra object, but another lifecycle-looking surface while TgData already exposes every public operation; F pass; A pass; I weak beyond generic layering preference | DEFERRED: independent reader abstraction becomes a real consumer requirement |
| Q4-F | N pass; S new methods preserve old behavior and do not fabricate network evidence on replay; F explicit acknowledgment supports local/remote sinks; A thin facade can delegate; I current facade pattern plus caller-owned scheduling | ACTIONABLE |
| Q4-C | N pass for REPAIR; S changes existing callback/polling semantics and still couples scheduling to persistence; DO-NOTHING fails requested runtime behavior | KILLED |
| E1 | N pass; S remote capability needs a backend contract, not concurrent-reader promises; F separate later backfill remains viable; A async protocol is local-code feasible; I user future storage need plus no held DB transaction | ACTIONABLE boundary; later implementations deferred |
| M1 | N pass; S verifying files costs I/O but returning absent data violates delivery contract; F root can change without changing manifest; A existing verifier handles nonsymlink/hash/size checks; I media schema and saved-replay contract | ACTIONABLE |

## Real-component observations

`../probe_components.py` ran against actual SQLite, subprocess termination, the
real Telethon 1.45.0 iterator/guard and existing MessageBatch/files. Output:

```text
PASS sqlite process exit abort 100 False
PASS sqlite process exit commit 101 True
PASS stale expected payload refuses replacement
PASS pending nested JSON preserves exact canonical batch
PASS real SDK canonical group and exclusive continuation
PASS real SDK/read-budget interrupted prefix and resume
PASS immutable replay after lost receiver acknowledgment
```

The SQLite probe observes actual commit/rollback after process exit; it is not a
stand-in returning the desired state. Scripted Telegram transport does not prove
live history visibility, only actual SDK/local composition. None of these probes
claims the not-yet-written SyncStore or SyncEngine is verified.

## Assembly check

Combine Q1-F, Q2-F, Q3-F, Q4-F, E1 and M1. The result is one optional continuation
engine around the unchanged public batch reader, a small opaque conditional-store
interface with SQLite backend, and four async facade operations. Canonical chat IDs
and an explicit initial cursor avoid resolution/default policy work. A saved
pending batch is authoritative until the caller acknowledges that exact batch.

State media mode is fixed at enrollment. A media root is supplied when needed,
validated on replay, and never affects batch identity. An empty read returns None
without inventing a new position. Repeated latest acknowledgment is idempotent;
an older/wrong acknowledgment must never clear newer work. All actual reads retain
the existing budget, session, proxy and health path; local storage/replay does not
claim Telegram recovery.

Two-error contract to detail in the plan: if a read yields a completed prefix but
its persistence fails, the new local error must name the persistence failure and
retain the original read error as an attribute for inspection. No successful pending
receipt or cursor advance is claimed. This is integral preparation failure, not
cleanup replacing a primary failure.

Axis coverage: identity (Q1-G/F/C); storage/atomicity (Q2-G/F/C); acceptance locus
(Q3-G/F/C); API/scheduling shape (Q4-G/F/C); artifact policy (M1); future scope (E1).
Each assembly element has a tested candidate. Shared-input convergence was challenged
by Q2-C/Q3-C; the saved-byte and SQL observations independently support retaining
pending state. No claim requires the paused #7 implementation.

## Telemetry

Generators 4/4; framers 3/3. Four meta-decision pieces, each with all three variants
and piece-level Inversion satisfied. Q4's inversion targets intervention-shape;
Q1–Q3 target identity/atomicity/layer respectively. ADD and REMOVE constraints
both produced tested candidates. Absence patch/redesign/reverse-present directions
all ran. Domain transfer includes native database and external dispatch analogies.
14 candidate entries tested; 6 assembly survivors fully tested. Convergence: four
mechanisms support retained observations plus explicit acceptance, with independent
component evidence. All six failure modes checked; no untested survivor promoted.
**Overall: PROCEED.**
