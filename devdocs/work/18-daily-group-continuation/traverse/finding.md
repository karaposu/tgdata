---
status: active
model: gpt-6-astra
effort: max
---

# Finding: durable daily continuation

## Question

How should tgdata implement the daily-continuation first delivery of #18, using
its existing versioned batches, so daily scrapes resume after failed delivery or
process restart? The user needs one reader per group, has deferred backfill, and
has permanently excluded old-edit and deletion reconciliation.

## Finding Summary

- Persist both the acknowledged message position and one pending batch per group.
- Enroll each canonical group ID with an explicit initial position. Reopening
  progress must never silently reset it.
- Prepare or replay one batch per call; the caller controls daily scheduling.
- Advance the position only after an explicit acknowledgment naming the pending
  batch. Keep receiver acceptance and duplicate handling with the application.
- Define an asynchronous load/conditional-replacement store contract and provide
  a SQLite implementation. Keep transition rules in tgdata rather than each backend.
- Reuse MessageBatch and the existing guarded reader, including partial prefixes.
- Optional downloaded media must remain available and valid for pending replay.
- Keep planned backfill, account routing, joining and health redesign outside this
  delivery. Issue #18 remains open for its later backfill work.

## Finding

Daily scraping must continue from what the destination accepted. Merely remembering
what Telegram returned is insufficient: the process may stop before those messages
reach storage. The existing MessageBatch API already prepares bounded observations
and preserves their exact bytes; it intentionally leaves this delivery state to
the caller. The new feature takes ownership of that reusable state.

### 1. Give each collection an explicit source and starting position

The first version should use a canonical marked Telegram group ID, the same
chat_id already exposed by MessageBatch. This avoids storing progress under a
mutable username or a session/account label. A returned batch must match that ID.

Enrollment requires an explicit after_id. Zero deliberately starts at the oldest
currently visible messages; an imported checkpoint resumes an existing archive.
An existing collection keeps its current accepted position. A conflicting attempt
to reinitialize it must raise rather than skip or reread data silently.

### 2. Retain unfinished delivery as one durable record

A group is either ready at an accepted position or has a pending observation
prepared from that position. The pending observation includes the full validated
MessageBatch value, not only a query range or hash. Replaying it makes no Telegram
request and spends no read allowance.

Acknowledgment names the batch the caller durably accepted. The library obtains
the next position from that stored batch and commits the cursor update together
with removal of the pending value. Repeating the latest acknowledgment is harmless;
a mismatched or older acknowledgment cannot clear newer work.

The receiver still needs duplicate handling. A successful upload can be followed
by a lost reply, in which case the reader must send the same pending observation
again. Different batches can also overlap on message IDs. The application must
commit its effects and duplicate markers together before acknowledging.

### 3. Keep persistence replaceable without duplicating transition rules

An asynchronous store loads the saved text for a chat and conditionally replaces
it only when it still equals an expected previous value. The comparison and write
must be one durable atomic operation. A missing record differs from a failed load.

The library validates and constructs the versioned state, so a custom database
backend implements storage rather than daily-continuation logic. A bundled SQLite
backend makes the feature usable immediately. Its transactions are short and never
span network waits. This is not a distributed reader-coordination service.

### 4. Preserve errors without losing already prepared work

A read can exhaust the account budget after preparing a valid prefix. Save that
prefix as pending and preserve the original read failure. The caller can deliver
and acknowledge the prefix, then stop or retry according to the error.

If retaining that prefix itself fails, raise an explicit local persistence error
and retain the original read exception for inspection. Do not claim the partial
batch is durable. In either case the accepted position stays unchanged.

An empty result means nothing new is currently visible after the bookmark. It
does not manufacture a later cursor or a permanent completed state. Cancellation
never acknowledges work; committed pending state remains discoverable on restart.

### 5. Keep optional files attached to the replay promise

Reference-only batches need their saved JSON. Download-mode batches additionally
need the hash-named blobs from the existing downloader. Fix media mode at enrollment
and allow the caller to supply the local media root when preparing/replaying.
Verify pending blobs before returning them. Missing or corrupt files raise while
leaving pending state intact; a fresh fetch is not a substitute for those bytes.

Moving a collection sequentially between machines requires the state and those
artifacts to be available at the new location. The feature does not implement
file transfer or delete accepted media automatically.

### 6. Expose bounded library operations

Use an optional sync_store on TgData with enrollment, one-batch sync, acknowledgment
and status methods. Delegate actual fetching to the existing get_message_batch
path so proxy, session, read-budget and existing health behavior remain authoritative.
Store-only operations and offline replay must not pretend Telegram answered a request.

The caller's existing loop decides when to run and how much work to do. A future
backfill implementation can use separate progress without moving this daily cursor.

## Next Actions

### MUST
- **What:** turn the selected contract into a description, implementation plan and
  adversarial plan review. **Who:** task implementation agent in this work folder.
  **Gate:** this finding is committed. **Why:** make storage and error details
  reviewable before writing runtime code.
- **What:** implement and test the store, continuation layer and public API.
  **Who:** tgdata modules and offline regression suite. **Gate:** plan critic/fold
  complete. **Why:** deliver real daily continuation and verify crash boundaries.
- **What:** document an end-to-end local destination example with repeated-delivery
  handling. **Who:** public docs/example. **Gate:** API fixed by the plan.
  **Why:** callers can supply a real acceptance signal without copying unsafe cursor
  bookkeeping.

### COULD
- **What:** validate a designated live group's first daily run with the actual
  destination. **Who:** account owner and implementation agent. **Gate:** explicit
  authorization and destination access. **Why:** supplement offline evidence.
  **Depends-on:** MUST item “implement and test the store, continuation layer and
  public API”; GATED until it completes.

### DEFERRED
- **What:** planned backfill. **Gate:** user selects the second #18 delivery.
  **Why (if revived):** retain independent fixed-window progress between chunks.
- **What:** alias enrollment or callback convenience. **Gate:** a concrete consumer
  needs those interfaces. **Why (if revived):** reduce integration boilerplate
  without changing durable acceptance rules.
- **What:** additional remote store backend. **Gate:** a deployment names its
  database and transaction requirements. **Why (if revived):** host the same state
  contract in application storage.

## Reasoning

Canonical numeric enrollment was selected over an alias registry because it uses
the identity already carried by batches and avoids adding a second resolution
contract. Alias enrollment remains viable when convenience becomes necessary.
Account/username keying was rejected because changing those labels can change the
meaning of an old cursor.

An opaque conditional store was selected over backend-specific stage/acknowledge
methods because the library can own the transition rules once. Both can be correct,
but the latter asks every backend to repeat more domain logic. A plain cursor file
was rejected because it cannot retain an uncertain delivery, whichever write order
it chooses.

Explicit acknowledgment was selected over integrated callbacks because consumers
may receive acceptance asynchronously or in another process. A durable callback
can be an adapter later. Returning today's batch API with only a recipe was rejected
because the user explicitly asked tgdata to own daily continuation.

An additive facade was selected over changing poll_for_messages because that method
already has callback and scheduling semantics. A separate public controller is
viable but adds an unnecessary entry point; its internal separation can remain
behind the existing facade. Documentation-only and polling replacement alternatives
fail the requested behavior or existing compatibility respectively.

Replay verifies optional files because a valid manifest alone cannot deliver absent
bytes. Replacing missing artifacts by re-fetching would create a new observation.
Retaining explicit format/version and an async backend boundary supports the already
requested pluggable storage without implementing future workers or backfill now.

## Open Questions

### Monitoring
Measure local SQLite and media-verification latency with actual daily batch sizes.
The backend methods are asynchronous interfaces, but the reference implementation
can do short synchronous local I/O; documentation must state that accurately.

### Blocked
No planning blocker. Actual receiver integration and live Telegram acceptance need
their own access/authorization and are outside this implementation's evidence.

### Refinement Triggers
Add alias enrollment when a consumer cannot supply canonical IDs conveniently.
Revisit coordination only if the user requests overlapping readers. Revisit media
transport when a named deployment needs to relocate pending blobs automatically.
Edit/deletion reconciliation remains permanently excluded by the user.

## Evidence

Seven observations in ../probe_components.py passed: process exit before/after
SQLite commit, stale replacement refusal, exact nested batch serialization, real
SDK canonical-ID reading, interrupted budget prefixes and saved replay after lost
acceptance acknowledgment. Source code and component behavior ground the selected
shape; no new continuation implementation or deployed receiver has yet been tested.
