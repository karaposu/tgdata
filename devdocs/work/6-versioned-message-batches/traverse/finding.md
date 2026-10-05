---
status: active
model: unknown
effort: unknown
---

# Finding: a replayable message-batch contract

## Question

How should tgdata answer “read group X after message N” with a stable, versioned
batch containing messages, the next continuation point and content-hashed media?
The result must support a reader and a processor evolving independently, and
make a repeated upload recognizable without building the future worker now.

## Finding Summary

- Add a separate raw-batch API. Keep existing DataFrame and media APIs compatible.
- Define the message fields and JSON rules explicitly instead of inheriting the
  entire Telethon object format or the presentation table's filtering.
- Advance the cursor only after a message and any requested media are prepared.
  A failure exposes the completed prefix and leaves the failed message resumable.
- Name completed media bytes by their content hash. Write to private temporary
  files and verify existing hash-named files before reusing them.
- Persist and replay the same batch after an upload failure. Reading Telegram
  again is a new observation and may produce different content.
- Target implementation and tests at Telethon **1.45.0**, as the user specified.

## Finding

tgdata already reads incrementally and returns DataFrames, but the table is a
presentation result. It can omit a message when sender metadata is unavailable.
The batch contract needs to preserve the requested raw fields without depending
on that conversion, or a caller could advance past data it never received.

The new public operation should perform one bounded oldest-first read for one
resolved group or channel. It should use the same client factory as existing
calls, preserving proxy/session behavior, account-budget admission and Telegram
health reporting. A separate operation can do this without refactoring every
date-filter/callback option in the existing reader.

The returned value should own its schema and deterministic JSON representation.
Identifiers need an exact representation for consumers whose numeric types cannot
preserve all Telegram IDs. Dates and absent values also need explicit rules.
The batch identity should be derived from the finalized payload, and reload should
verify the version, structure and identity. Returning a mutable dictionary must
not silently change the identity of the original value.

Media preparation needs two explicit modes. A references-only read can remain
cheap. When the caller requests downloaded files, a message joins the completed
prefix only after its supported asset has been fully written and published.
The format must say which media kinds can produce files, rather than treating
every attachment as downloadable.

The media publisher should use a private temporary file in the destination
directory, compute the digest of the completed bytes, and publish without
overwriting another writer's object. It should verify a pre-existing digest
path before reusing it. Only portable relative names and byte metadata belong
in the record; absolute machine paths and transport access details do not.

The next cursor belongs to a particular chat and means “continue after the last
fully prepared message in this value”. It does not mean that the receiver has
stored the value. Quota or media failures may occur after the SDK has fetched
more messages than the application completed; a retry can therefore spend quota
again without implying that the first attempt was free.

The batch must distinguish reaching the requested count from observing the end
of available history. A full batch alone does not prove another message exists.
There should be no extra read merely to manufacture a `has_more` answer, and a
batch should not exceed its bound just to finish an album. Preserve grouping
identity so consumers can associate album members across batches.

For delivery recovery, the caller stores the batch and its completed files,
uploads those same artifacts, and persists the next cursor only after its
receiver acknowledges durable storage. A content hash supplies a deduplication
key; it does not execute the receiver's database transaction. A fresh fetch
may observe edits or deletions and is not a substitute for replaying saved output.

The local feasibility checks are concrete. The actual Telethon 1.45.0 iterator
preserved senderless message 101 and a service message; the existing presentation
converter omitted 101. Telethon wrote the complete scripted media payload into
the supplied file object, ignoring the media's unsafe filename. Twenty-four
concurrent local publishers produced one complete digest-named object with no
temporary leftovers. These observations are recorded in
`../probe_batch_seams.py`; they do not claim live Telegram or receiver behavior.

## Next Actions

### MUST

- **What:** fix the v1 field/type rules, public API, limits, media eligibility and
  error/partial-result contract in the description and implementation plan.
  **Who:** the #6 task-impl run.
  **Gate:** before runtime changes.
  **Why:** the code and consumer fixtures need one concrete contract.
- **What:** implement the value, file publisher, bounded reader and additive
  façade using the existing guarded client.
  **Who:** the #6 implementation.
  **Gate:** after the plan and its critic/fold pass.
  **Why:** realize the selected design without bypassing account safeguards.
- **What:** test the actual composition on Telethon 1.45.0, including partial
  failure, exact identifiers, identity/reload, file races/corruption and old APIs.
  **Who:** the #6 verification suite.
  **Gate:** before the implementation checkpoint is reported complete.
  **Why:** the new API must meet the contract rather than merely emit JSON.

### COULD

- **What:** include a small receiving-side deduplication example.
  **Who:** user documentation.
  **Gate:** after the normative v1 format is fixed.
  **Why:** make saved-output replay and acknowledgment concrete for consumers.
  **Depends-on:** MUST “fix the v1 field/type rules”. This COULD is GATED until
  those rules are fixed; it does not introduce a receiving service.

### DEFERRED

- **What:** generalize the legacy and raw readers into a shared scanner.
  **Gate:** another real reader requires the same generalized state machine.
  **Why if revived:** reduce demonstrated duplication without speculative API risk.
- **What:** add an acknowledgment/backpressure stream.
  **Gate:** #10 defines actual receiver/job ownership and persistence.
  **Why if revived:** coordinate delivery around this value contract.

## Reasoning

A versioned wrapper around the entire SDK payload preserves many fields, but
leaves their meaning and representation tied to generated Telegram types. It
does not establish a producer-owned field contract. The selected explicit
projection gives a processor a small defined surface while preserving the
requested unprocessed data.

Standardizing only the current DataFrame JSON export would retain its omissions.
Both the “reuse the table as the value” alternative and the “add version/cursor
fields to export” alternative fail the observed senderless-message case. The
selected reader starts from the SDK messages instead.

Keeping existing message-based media filenames and postponing hashing to a
receiver leaves the requested content-named output absent. Downloading all media
into memory and replacing files by rename does create hashes, but the focused
temporary-file design avoids whole-asset memory use and verifies reuse rather
than concealing destination corruption.

A universal scanner and a new acknowledgment stream could be useful later.
They introduce broader state and migration obligations without being necessary
for one bounded producer operation. Replacing existing successful returns would
break current callers for the sake of a cleaner-looking API. The additive method
meets the task while retaining those contracts.

The surviving design combines four independently grounded parts: an explicit
value, verified file publication, a complete-prefix reader and a public replay
contract. Their joining rule is completion: bytes exist before their record is
counted complete, and the record exists before its cursor advances. This resolves
the tension between a network page, a displayed row and a delivered batch.

## Open Questions

### Monitoring

Observe filesystem contention and media-processing latency on deployment
volumes. The local probe establishes the tested filesystem behavior, not every
remote or unusual storage mount.

### Refinement Triggers

Revisit schema depth if an actual processor needs Telegram fields beyond the
documented v1 surface. Revisit the shared-scanner choice when a second reader
needs identical filtering/resume semantics. Neither condition blocks the current
description and plan.

## Source Input

The original #6 request is preserved verbatim in `source-input.md`. Subsequent
user steering: “we will be using 1.45.0 , no need for 1.33.1”.
