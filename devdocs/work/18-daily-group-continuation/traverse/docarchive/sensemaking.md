---
model: gpt-6-astra
effort: max
---

# Sensemaking — daily continuation

## User Input
_branch.md, all four considered articulations, with surfacing.md and the populated
source workspace. Scope: the authorized daily-continuation first delivery of #18.

## SV1 — baseline
The apparent task is to remember the last read message between daily jobs. The
existing reader already accepts after_id, so a persisted integer seems sufficient.

## Phase 1 — anchors

- Constraint C1: one active reader per group; no distributed scheduling, old
  edits/deletions, backfill implementation or account failover in this delivery.
- Constraint C2: an upload/storage failure must not advance acknowledged progress.
- Insight I1: a freshly fetched batch can differ from an earlier observation;
  a cursor alone cannot reproduce an unacknowledged delivery (batch v1 contract).
- Insight I2: a read-budget error can carry a nonempty completed prefix. Ignoring
  it can repeatedly spend a small allowance re-reading the same prefix.
- Structural S1: MessageBatch already validates, hashes and retains exact JSON.
  Its media references use basenames; file bytes have a separate lifetime.
- Structural S2: get_message_batch owns the network/health/read-budget path.
  Local continuation state does not need to own a second Telegram client.
- Principle P1: successfully fetched, durably prepared and acknowledged are
  different states. Only the last authorizes progress advancement.
- Principle P2: an account authorizes a read; group/collection identity identifies
  the progress. A session name or mutable handle is not durable source identity.
- Meaning M1: “daily” describes caller scheduling, not a midnight cutoff. Catch-up
  begins at accepted progress after arbitrarily many missed days.
- Meaning M2: “acknowledged” is a caller assertion about its destination's durable
  acceptance; the library cannot observe that destination by itself.

H4/H5 check: pending and acknowledged are distinct because the receiver may commit
while its response is lost. This is a storage/delivery state distinction, not a
renaming of the current in-memory polling cursor.

## SV2 — anchor-informed
The deliverable is a small durable delivery state machine around immutable batches.
It owns both the accepted position and any prepared observation awaiting acceptance.

## Phase 2 — perspectives

Technical: no state update may pass records absent from the accepted batch. A
bookmark plus pending manifest must transition atomically; the network cannot be
part of a local database transaction. New anchor T1: conditional state replacement
can protect transitions without a distributed scheduling system.

User: a daily job should reopen progress and continue without re-supplying its
latest cursor. Enrollment still needs an explicit initial position; silently
starting at the current head can discard wanted history. New anchor U1: beginning
is a caller choice, while subsequent positions are library-owned.

Failure: crash after destination acceptance but before local acknowledgment is
indistinguishable from failure before acceptance. New anchor F1: repeat delivery is
necessary; receiver deduplication remains an explicit integration obligation.

Resource: keeping one pending batch per collection bounds unfinished work, and
limits are inherited from the existing batch API. Files and messages can be large;
the store must avoid copying media bytes into a cursor row. New anchor R1: retain
the actual artifact location and verify replay artifacts rather than silently
switching mode or fetching replacements.

Strategic: later backfill needs separate progress, not a backward mutation of the
daily bookmark. This delivery can leave that namespace absent. A custom store can
move state sequentially between machines; it does not itself move local media.

Systemic: stored pending JSON contains message content, unlike budget/session
metadata. Access controls belong to the chosen storage. Errors/logs must not dump
stored content, invite tokens or login credentials.

Internal consistency: the old polling callback is not an acknowledgment boundary:
its in-memory cursor advances before calling the callback. Reusing it would not
produce the requested durable semantics. Session save failures are logged and
retried; progress-store failures must instead be visible before further delivery.

Frame-exit completeness fires for “state”: session credentials, read allowance,
daily accepted position, pending output, backfill progress and receiver records
are project-wide referents. Session and allowance stay in their existing owners;
receiver acceptance is an external precondition; backfill stays deferred. Strongest
counter: one universal state store would simplify integration. Structurally these
records have different commit/failure guarantees, so shared infrastructure does
not justify sharing their transition rules. No additional referent remains hidden.

Phase/calibration: no current reader-coordination requirement justifies leases or
automatic ownership takeover. Single-reader support still needs to reject stale
acknowledgments and avoid last-writer cursor replacement. Live Telegram acceptance
is outside the evidence; current visible history is the only scope of an end batch.

H1/H2/H3/H7 check: explicit-ack and helper composition can coexist; callback is an
alternative convenience boundary, not a prerequisite. “daily” is not a date filter,
and “shared” does not authorize concurrent workers after the user's clarification.

## SV3 — expanded
The main boundary is durable preparation versus external acceptance. Identity,
initial enrollment, interrupted prefixes and artifact availability also determine
whether resumption means continuing the same work.

## Phase 3 — ambiguity collapse

### A1 — progress versus fetched position
Strongest counter-interpretation: persisting the highest fetched ID is enough;
the receiver can request a missing batch later.
Why it fails: after advancing and crashing before delivery, the new run queries
only higher IDs; no pending bytes exist from which to satisfy that request.
Confidence: HIGH. Resolution: accepted position and pending observation are
separate. Fixed: only acknowledgment advances. No longer allowed: save-on-fetch
as the authoritative bookmark. Depends: state transitions, examples and tests.
Change: replace integer-only resumption with preparation/acceptance semantics.

### A2 — acknowledgment versus callback return
Strongest counter-interpretation: a callback's successful return is a sufficient
universal acceptance signal.
Why it narrows poorly: a callback may enqueue asynchronous work or run an upload
whose eventual acceptance arrives elsewhere. Explicit acknowledgment supports
both those flows and a synchronous callback adapter without owning the transport.
Confidence: HIGH for explicit acceptance meaning; callback convenience is not
technically invalid. Resolution: acknowledgment is an explicit caller assertion;
endpoint shape remains for Innovation. Fixed: caller owns destination transaction.
No longer allowed: interpreting mere fetch/queue completion as durable acceptance.
Depends: public API and receiver example. Change: no external receiver blocker.

### A3 — where a new reader begins
Strongest counter-interpretation: “daily” implies start at now-minus-one-day or
the current head, and a zero default is convenient for everything else.
Why it fails: those defaults choose data omission or an unexpected full catch-up
without knowing what the consumer already stored. An explicit initial message ID
can represent zero or an imported prior checkpoint without guessing.
Confidence: HIGH. Resolution: first-use position must be explicit; resume never
resets it. Fixed: enrollment and continuing are distinguishable. No longer allowed:
repeated configuration overwriting accepted progress. Depends: initialization API.
Change: migration is a supplied checkpoint, not ScrapeOps-specific file parsing.

### A4 — group identity versus account/handle label
Strongest counter-interpretation: key progress by account plus username so each
reader can reopen it from its familiar config.
Why it fails: account changes would create new progress, while a renamed/reassigned
handle can route an old cursor to another group. Existing MessageBatch.chat_id
provides a canonical marked peer ID that can be checked without new health state.
Confidence: HIGH. Resolution: bind a collection to its canonical group and reject
unexpected returned groups. Fixed: identity survives labels/accounts. No longer
allowed: unverified relabeling of a progress record. Depends: group enrollment and
pending validation. Change: #7 health ownership is not imported into this design.

### A5 — one reader versus atomic storage
Strongest counter-interpretation: without competing readers, an ordinary JSON
overwrite is enough and transaction semantics can be deferred.
Why it fails: a single process can crash between removing pending data and saving
the new cursor. Single-writer reduces coordination needs, not atomicity needs.
Confidence: HIGH. Resolution: publish/acknowledge each logical state atomically;
detect stale/mismatched transitions. Fixed: backend contract includes durability
and transition preconditions. No longer allowed: write-behind success or clearing
pending before the cursor commit. Depends: pluggable store and offline probes.
Change: storage is a correctness boundary, not a session-store clone.

### A6 — errors with completed prefixes
Strongest counter-interpretation: discard partial batches and retry everything
from accepted progress; this avoids a special error path.
Why it fails operationally: with allowance smaller than requested batch size, the
same completed prefix can be fetched every day without ever becoming deliverable.
Confidence: HIGH. Resolution: valid nonempty prefixes must enter the same durable
pending/ack path while the read failure remains visible. Fixed: no auto-ack on
failure. No longer allowed: unbounded re-fetch of an unchanged interrupted prefix.
Depends: error precedence and restart tests. Change: prepared work can coexist
with a failed read; completion and operation success are not synonyms.

### A7 — replay versus another fetch
Strongest counter-interpretation: re-fetching the same ID range recreates the
batch, so only its bounds need storage.
Why it fails: batch identity includes mutable observed fields and stop reason;
the actual saved-replay test uses the same serialized observation. Re-fetch can
produce new bytes even though old-edit reconciliation is excluded.
Confidence: HIGH. Resolution: replay saved validated bytes; preserve downloaded
artifacts if requested. Fixed: pending replay requires no Telegram call. No longer
allowed: silently replacing a missing/corrupt pending batch or file. Depends:
artifact checks, failure reporting, receiver idempotency. Change: a missing pending
artifact is an error, not permission to move progress.

Specific-versus-pattern test: lost acknowledgment is one instance of process
failure between preparation, delivery and commit. The same state rules must cover
store failure, cancellation, wrong acknowledgment and restart. Restricting tests
to the example receiver would miss the general boundary.

## SV4 — clarified
Daily continuation is bounded preparation/replay followed by an explicit atomic
acknowledgment. The initial position is chosen once; canonical source identity and
prepared bytes persist. Partial read failures can leave pending output, never an
advanced accepted cursor.

## Phase 4 — degrees of freedom
Fixed: single-reader scope; no scheduler; acknowledged progress; canonical source
binding; pending exact bytes; explicit first-use position; local errors stay local;
budget enforcement remains in existing client code; backfill stays separate.
Eliminated: cursor-only overwrite, fresh-query replay, implicit now/24h cutoff,
automatic completion of backfill, distributed coordination and global health changes.
Viable: a standalone helper or additive facade backed by a small atomic store;
SQLite reference backend; explicit acknowledgment with optional caller-written
callback glue; references and verified optional artifacts. API names and schema
layout remain design choices, not unresolved human-only meaning gaps.

## SV5 — constrained
Two durable states suffice at the core: ready at accepted position, or holding one
pending observation at that position. Acknowledgment transitions the latter to
the former with a higher accepted position. No progress transition depends on
health labels, wall-clock midnight, account routing or the UI plan.

## Phase 5 / SV6 — stabilized
Add an acknowledgment-driven continuation layer around the existing batch reader,
with a precise pluggable persistence boundary and a usable local backend. Keep
caller scheduling and destination effects outside it. Unlike SV1, resumption is
defined by both a committed position and exact unfinished delivery, with explicit
group identity and first-use semantics.

Telemetry: all 5 anchor types; 8 perspectives; 7 collapse pairs resolved; no open
meaning blocker. Three perspectives introduced distinct surprising constraints
(lost reply, interrupted prefix, separate media lifetime); later perspectives
confirmed their scope. H4/H5 terminology tests passed for accepted/pending/daily;
H6 found refinement rather than exception accumulation. All six failure patterns
were checked; no self-referential framework evaluation occurs.

Existing-component probe on Telethon 1.45.0, real batch/SDK/files with sockets
blocked: saved replay/ack ordering, budget prefix/resume and end/empty/max-cursor
tests ran. These establish current components, not the new store's correctness.
