---
model: unknown
effort: unknown
---

**Verdict: IMPLEMENT AS WRITTEN**

Falsifier: a live Telegram history read using the selected chat/after-ID settings
fails to provide the ordered visible-message sequence the SDK iterator relies on,
so that a complete-prefix cursor cannot be produced through that interface.
Affordable now: no — that requires an authorized live account and server
observation outside this offline run. The actual 1.45.0 iterator and download
control flow have been probed with supplied replies; those replies do not
establish live server behavior.

# Plan critique — issue #6, revision 1

Reviewed in this warmed session against `f19299f`, its description, traverse
finding, existing reader/factory/health/budget code and Telethon 1.45.0. No
subagent. The user's explicit 1.45.0 target is retained.

## High-level summary

The plan specifies the needed contract before code: exact fields, canonical
types/encoding, identity, mode/stop meanings, validation and continuation.
It separates raw records from presentation, uses completed-file publication,
and advances only a fully prepared prefix. Existing public behavior stays on
its original path, while every new read uses the shared client guard.

No High, Medium or Low finding was established against the plan. The complex
parts have concrete mechanisms and tests, rather than being deferred behind
phrases such as “serialize safely” or “handle errors”. The architecture and
six-step order can proceed unchanged.

## Premise Inventory

### 1. The SDK provides the ordered messages needed for continuation

First dependent step: 3. Waste if false: reader/cursor and integration/test work
would need redesign. Test scheduled: actual SDK seam probe before planning,
then implementation behavior in step 5. Cheapest earlier observation: run the
installed iterator with controlled message replies; already done. Coverage:
real 1.45.0 iterator ordering, min-ID behavior and senderless/service preservation,
plus the earlier #9 paging/admission evidence. Scripted replies are **non-covering
for live server selection**, which remains the falsifier above.

### 2. Completed media can be produced without whole-file memory buffering

First dependent step: 2. Waste if false: publisher/reader media composition and
its resource promises would change. Test scheduled: pre-build SDK download probe,
expanded in this critique to both full Document and Photo paths; step 5 tests
the implemented helper. Cheapest earlier test: real SDK download code with a
supplied file object and recording transport, already run on 1.45.0. Coverage:
the SDK writes the supplied bytes into that object and returns it; metadata
filenames do not control the destination. Server file content/completeness is
supplied, not observed. Known-size checking and missing-output errors remain
required in the implemented helper.

### 3. Local publication can avoid partial objects and replacement races

First dependent step: 2. Waste if false: the file publisher's central mechanism
would need replacing before reader composition. Test scheduled: real filesystem
probe before build, then implementation corruption/cancellation/concurrency tests.
Cheapest earlier test: competing complete temporary-file writers on the real
filesystem. Observed 24 writers produce one complete digest-named file and no
temporary leftovers. This covers the local `fsync`/`os.link` composition, not
arbitrary deployment filesystems or power-loss behavior. Unsupported operations
raise instead of silently weakening publication.

### 4. Canonical bytes and an exact schema provide a stable producer identity

First dependent step: 1. Waste if false: value/replay/file naming and receiving
examples would have a false foundation. Test scheduled: explicit golden payload,
mutation, version/type and save/reload cases in step 5. The serializer and SHA-256
are deterministic standard-library primitives; the new implementation still needs
those tests. No existing vendor behavior is being assumed without a prior test.
The contract intentionally makes batch identity different from message identity
and the manifest file's own digest. Re-fetch equality and receiver exactly-once
processing are explicitly not inferred from a payload hash.

### 5. Existing account controls and return contracts can be retained

First dependent steps: 3–4. Waste if false: façade/client integration would need
changing. Test scheduled: existing real-client probes and #9 regression evidence,
then the new engine tests and supported full offline suite. Source evidence:
`ConnectionEngine.session()` supplies the same factory-built client; its `_call`
guard covers history and media message re-fetches. The new module dependency
direction is leaf file helper → value consumer → engine consumer → façade,
with no import back into the façade. Existing MessageEngine methods need no
behavior change. No new transport, session or quota store is planned.

No affordable decisive check on an existing prerequisite component is postponed
behind implementation. Tests of the new code naturally follow its construction;
that does not make them untested vendor premises.

## Restart Check

This adds a missing contract rather than repairing a failed earlier #6 attempt.
The concrete existing mismatch cited by the description is the presentation
converter dropping a senderless message. The real probe reproduces it; step 3
reads/project messages directly rather than routing through `_process_message`.
The unversioned export and origin-based media filenames are observed source
behavior; steps 1 and 2 address those mechanisms directly.

## Inherited Lessons

- Saved-output replay differs from a fresh query: step 1 binds identity to
  payload bytes, and step 5 documents receiver/cursor acknowledgment order.
- Presentation rows are not complete raw records: the real counterexample was
  tested before build; step 3 does not use the DataFrame converter or enrich
  missing senders.
- Network admission and application progress differ: step 3 retains the original
  quota exception and exposes only the completely prepared prefix.
- File names do not prove contents: step 2 hashes completed bytes and verifies
  existing destinations before reuse, with a prior actual filesystem probe.
- SDK details must be observed on the selected version: the probes run 1.45.0;
  no further 1.33.1 work is required or included in the plan.

## Targeted Checks and Evidence

The review attacked the serialization and cursor rules with malformed types,
duplicate keys, mutated dictionaries, empty/invalid progress, and media-mode
inconsistency. The plan has explicit validation/identity rules and tests for
each. It does not use a digest as authentication or a timestamp as identity.

The filesystem review covered missing/truncated output, corrupt/symlink paths,
concurrent equal writers, cancellation and output-root independence. The specified
completion and verification boundaries are sufficient for the scoped local
publisher; source size is checked when known. Synchronous local I/O latency is
disclosed, with bounded hashing memory, rather than claimed to be nonblocking.

The interruption review traced a failure on a second record, a budget stop
during media refresh, a bad projected value and failure before chat resolution.
The cursor follows appended validated records; unresolved sources do not fabricate
partial batches. Original exceptions and health classification are preserved.

Exact current `probe_batch_seams.py` output:

```text
Batch seam probes — Telethon 1.45.0
Publication: 24 competing writers, one complete digest-named file, no temporary leftovers
Raw iteration: IDs 101/102 and service action survive; presentation conversion omits senderless 101
SDK dictionary: ordinary JSON encoding rejects its datetime; an explicit wire projection is needed
SDK download: writes complete bytes to the supplied file object and returns it; media filename is unused
SDK photo download: the supplied file object also receives the complete photo payload
All pre-build seam probes passed; no live server behavior is claimed
```

## Findings

None. **0 High / 0 Medium / 0 Low.** No selected mitigations are required and
no plan change is justified by this review. The implementation must still satisfy
the normative fixture and behavior suite; this is not an implementation verdict.

## Known Execution Boundaries

Live Telegram, deployment-volume/receiver validation and merge/deployment remain
outside this implementation run. The selected SDK is 1.45.0. Exact model/effort
are unavailable and remain `unknown`; CONTRIBUTING §9 compliance is not certified.

## Phase 3 — Mitigation Selection

Executed after the findings pass. No Medium/High risk or mitigation proposal was
produced, so there is nothing to rank or select. No speculative generalization,
last-resort choice or new prerequisite was added. The verdict remains IMPLEMENT
AS WRITTEN; task-impl skips Fold and proceeds to implementation.
