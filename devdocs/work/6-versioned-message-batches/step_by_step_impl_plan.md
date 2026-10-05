---
model: unknown
effort: unknown
---

# Plan — stable, versioned message batches (issue #6)

**Revision 3 — first re-plan under CONTRIBUTING §7.4.** Replaces revision 1;
the original zero-finding critic needed no folded revision 2. Inputs: current
`desc.md`, complete original feature diff at `001f134`, and the rejected PR
critic at `670564e` (`history/round-1/pr-critic.md`, R1/R2, Robust selected).
All first-round artifacts remain intact under `history/round-1/` and in git.
Target: **Telethon 1.45.0 only**. Same warmed session; no subagent.

### What is the task

Deliver #6's portable raw message-batch contract with verifiable content files
and a completed-prefix cursor, while making local filesystem ownership and
failure provenance precise. The first implementation supplies the value and
reader but its publisher can misreport a local error as Telegram access denial
or replace a download failure during teardown. Regenerate the file lifecycle
around one error policy that applies to all its owned I/O, then verify the
whole public contract and repeat both PR gates on the same PR #15.

### Huge Hard Blockers

#### Planning Blockers

None OPEN. The two rejection mechanisms are established by source and the
public-API probes in `probe_pr_review.py`: FileExistsError produces a false
health event with zero requests when an unreported RPC is being handled;
permission-denied unlink replaces ChannelPrivateError after a safe prefix.
These are known inputs, not questions requiring a human decision.

The additional SDK/file seam was resolved before this plan by
`probe_replan_seams.py` on 1.45.0. The real SDK accepts a delegated file object,
writes exact photo/document bytes and returns that same object without closing
it. Guarding its local write/flush calls preserves the same OSError and prevents
incidental RPC classification; a transport exception's explicit RPC cause
remains intact. Python unwinding retains an RPC or CancelledError when secondary
cleanup exceptions are caught. Seven observations passed. This protocol probe
does not supply or test the proposed production publisher itself; that comes
after its implementation. Supplied server replies do not establish live behavior.

#### Execution Blockers

None for this local implementation/review cycle. The user has authorized the
re-plan, critique, implementation, verification and repeated PR reviews. Merge
requires the user's separate go-ahead under the existing session instruction.
Live Telegram, arbitrary deployment filesystems and a deployed receiver remain
outside this evidence. Exact model/effort metadata are unavailable; continue
recording `unknown` and explicitly flag CONTRIBUTING §9 at the merge gate.

### How this implementation moves toward desired state

Retain the explicit v1 value, raw reader and façade contract. Rework the leaf
file module's ownership rather than adding exception catches to the reader:
one narrow local-I/O invocation boundary, a file-object proxy that applies it
even when the SDK calls write/flush, and one owned-stream cleanup policy. The
SDK await is outside the local-I/O classifier; cleanup knows whether a primary
exception/cancellation is active. Both producers and existing-file verification
share this policy. No global health, budget, session or transport change is
needed, and no receiver, background collector or universal error framework is
introduced.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Preserve the v1 value and reader contract | Stable schema/API baseline and explicit retained invariants |
| 2 | Establish the local filesystem boundary | Native local errors keep type/identity without false Telegram provenance |
| 3 | Define owned-stream cleanup and error precedence | Primary failures/cancellation survive close/unlink/logging failures |
| 4 | Compose both publishers and verification with that policy | Complete files and exact errors through every file lifecycle exit |
| 5 | Extend behavioral regression coverage | Rejection cases plus SDK write/flush, double-failure and cancellation controls |
| 6 | Document operational failure semantics | Accurate best-effort cleanup and safe replay guidance |
| 7 | Verify, commit and repeat both review gates | Same PR updated with committed evidence and a fresh second PR verdict |

## Step 1 — Retain the complete public contract

### Proposed changes

Retain `MessageBatch` and its exact v1 envelope/record/media/blob schema from
`docs/message_batch_v1.md`, including canonical JSON, signed ID strings, UTC
dates, nullable fields, golden payload hash, strict ordering/cursors/modes and
immutable copies. No schema version or package/dependency change.

Retain `TgData.get_message_batch(group_id, *, after_id=0, limit=200,
download_media_to=None)`, its public exports and the shared guarded client.
Group resolution, explicit group, `after_id` range `0..2**31-1`, bounded
oldest-first iteration, senderless/service projection, no enrichment, media
selection, completed-record append and original-exception partial batches keep
their specified behavior. Preserve maximum-cursor handling and the distinctions
between limit/end/interrupted, saved replay versus fresh fetch, and caller
acknowledgment versus preparation. Existing DataFrame/media APIs keep their paths.

This step establishes what is intentionally retained while regenerating the
file lifecycle. Do not rewrite correct components to make the re-plan look new.
Any new contradiction affecting this contract must return to planning.

### Output
The current value/reader behavior remains the baseline for the revised publisher.

### Safe in nature
True — no runtime mutation in this step.

### Peripheral concepts
v1 schema, immutable snapshots, canonical hashes, SDK selection, continuation,
quota admission, health wrapper, backward compatibility

### Hardness Lvl
2

## Step 2 — Classify errors at owned local I/O [PR R1, robust]

### Proposed changes

In `tgdata/batch_files.py`, introduce one private invocation helper for an
owned synchronous filesystem action. Invoke the action; on an ordinary
Exception re-raise the **same object** `from None`, preventing incidental
context from masquerading as a Telegram cause. It must never enclose the
SDK/network await, writer coroutine, caller callback or arbitrary reader body.
BaseException control flow is not converted to a storage error.

Use this boundary for path resolution/creation/stat, temporary/open operations,
local reads/writes/flush/seek/fileno/fsync, close, link, verification and unlink.
Keep existing BatchStorageError validation and native filesystem types. Retain
TypeError-to-BatchStorageError behavior for invalid directory inputs.

Supply the SDK a private file-object proxy over the owned real file. Delegated
attributes are obtained through the same local boundary; callable stream
attributes are invoked through it. This covers real SDK write/flush calls,
including cached photos, without catching network failures merely because
ConnectionError is also an OSError. Telethon 1.45.0's real supplied-file return
identity is already observed. The proxy is private, not a new public stream API.

Do not alter health.classify or mark a complete batch operation local. A
current SDK exception, including a ConnectionError with an explicit RPC cause,
must retain its identity/cause and produce the existing appropriate health event.

### Output
A shared local-I/O boundary and a guarded owned file object; no global health
change or custom replacement for native file exceptions.

### Safe in nature
False — error context and file-object composition change in an existing API.

### Peripheral concepts
Python exception chaining, native OSError identity, SDK duck-typed file output,
local versus transport failures, existing health classification

### Hardness Lvl
4

## Step 3 — Own teardown and preserve the primary outcome [PR R2, robust]

### Proposed changes

Add a small shared owned-stream context in the leaf file module. It yields the
guarded stream and records an active **BaseException**, including cancellation,
without altering it. On exit it attempts close and, for a temporary file, unlink.
This is a resource/cleanup policy, not a new artifact-transaction framework.

Each cleanup action uses step 2's local boundary. Missing temporary files may
be ignored as already removed. Attempt unlink even if close fails. Choose errors
by precedence:

- Existing primary exception/cancellation: preserve that exact object and its
  meaningful cause. Secondary close/unlink failures are diagnostics only.
- No primary: retain the first cleanup failure as the operation's local error;
  attempt the remaining cleanup and report later failures as secondary. Do not
  silently return success when cleanup is the only failing operation.
- No failure: normal completion, no warning.

Log secondary cleanup failures at WARNING with operation and exception type
only, no exception text, paths, credentials or traceback. Guard diagnostic
delivery so a raising logging handler cannot replace the chosen outcome.
There is no promise that deletion succeeds when the filesystem refuses it.
Never publish incomplete contents or advance a cursor because cleanup failed.

Resource ownership starts immediately after a successful open. Prefer standard
`open(..., opener=...)` for existing-file reads, with O_NOFOLLOW where available,
so Python owns descriptor handoff; retain pre-open lstat and post-open fstat
identity/regular-file checks. Both read verification and output streams must
preserve an earlier failure if their close also fails. No awaited SDK work is
inside an exception-provenance wrapper, even though it is inside resource scope.

### Output
One explicit primary/secondary failure policy shared by output and verification
streams, including close/unlink and cancellation.

### Safe in nature
False — cleanup behavior and propagation are observable.

### Peripheral concepts
context managers, BaseException unwinding, file descriptors, cancellation,
logging handlers, residual private files, error precedence

### Hardness Lvl
4

## Step 4 — Compose complete publication with the ownership policy

### Proposed changes

Refactor `download_blob` and `save_manifest` to acquire their private temporary
files through the shared owner. Downloads await the SDK writer with the guarded
stream and still require that exact returned object and an open stream. Use
guarded local flush/fsync/hash/size-check and **close before publication**.
Manifests write the canonical bytes, flush/fsync and close before publication.
The owner still attempts teardown on every exit, including a failed close.

Keep SHA-256 names, bounded hashing, known-size verification, non-replacing
`os.link`, existing-file content checks and manifest full-byte verification.
Convert existing-file verification to the same owned read-stream policy and
guard its path/open/fstat/read/close operations. Preserve nonsymlink/regular-file
and inode checks, including O_NOFOLLOW where supported. Unsupported filesystem
operations remain errors rather than triggering an unsafe fallback.

Both publishers use the same cleanup decision; do not scatter ad-hoc exception
suppression into BatchEngine or TgData. Its existing catch attaches the valid
complete prefix to the original ordinary exception; cancellation remains outside
that ordinary partial-result promise. A completed blob may remain if later
preparation/cancellation fails; an undeletable private temp can also remain,
but no partially written public object may exist.

### Output
The existing media/manifest API with correct local error provenance and primary
exception identity, while keeping the complete-file and safe-cursor guarantees.

### Safe in nature
False — existing producers and file reuse are re-composed.

### Peripheral concepts
complete-file publication, streaming, deduplication, manifest identity, reader
partial results, existing cache integrity, cleanup ownership

### Hardness Lvl
4

## Step 5 — Test failures in the actual composition

### Proposed changes

Extend `tgdata/smoke_tests/test_19_message_batches.py` without weakening its
existing 25 groups/golden expectations. Preserve and rerun the unchanged
first-gate `probe_pr_review.py`; its two prior failures must turn into passes.
Use real 1.45.0 SDK flow, real temporary files and blocked sockets. Fault
injection supplies only external transport/filesystem/logging failures, not the
behavior being tested. Cover:

- Both original R1/R2 public reproductions with the same expectations.
- Local directory, create, write/flush (inside the SDK), fsync, publication,
  existing-file read/verification and cleanup-only errors under unrelated
  unreported RPC context: preserve the native object/type, no false health,
  correct empty/nonempty prefix and no incomplete public object.
- Genuine current RPC and transport errors with explicit RPC causes: same
  object/cause, correct health event and safe cursor; the local guard must not
  suppress the SDK await.
- A primary SDK error plus failed close/unlink, including real permission-denied
  unlink; cancellation during a pending SDK download plus denied cleanup;
  verify the chosen primary identity and that later cleanup still runs.
- No primary plus cleanup failure: raise the original first local cleanup
  error; with two teardown failures preserve first-error order. Include the
  manifest path, not only media downloads.
- Existing-file verification read failure plus close failure: preserve the read
  error and close the owned descriptor as far as storage permits.
- Secondary diagnostic content is limited to operation/type; a deliberately
  raising logging handler cannot replace the primary or cleanup-only error.
- Successful media/cached-photo/proxy return identity, dedup, corruption,
  symlink/directory rejection and saved replay remain covered by the retained
  suite and first-gate probes.

Restore probe-owned permissions/handles during test teardown, after assertions.
Do not pretend this recovery was done by production. Retain any real unresolved
failure as a gate result; only small nonarchitectural test/implementation errors
may be corrected under task-impl Verify, with every correction reported.

### Output
Executable evidence for provenance, primary/secondary precedence and original
feature compatibility through real SDK and filesystem boundaries.

### Safe in nature
True — synthetic tests only.

### Peripheral concepts
public API tests, SDK stream protocol, real permissions, fault injection,
logging isolation, cancellation, golden schema, regression evidence

### Hardness Lvl
4

## Step 6 — Document the accurate failure contract

### Proposed changes

Update `docs/message_batch_v1.md`, the batch README guidance and smoke inventory:
native local I/O keeps its class/object without unrelated Telegram attribution;
SDK errors retain their own causes; the active failure/cancellation takes
precedence over secondary close/removal failure. Secondary warnings reveal
only operation/type. A cleanup-only failure raises. Removal is best-effort when
storage refuses it and a private temporary file can remain; completed immutable
blobs may remain too. Preserve the guarantee that incomplete content is never
published and caller cursor state is never advanced by cleanup.

No wire-format, dependency, legacy-media or session behavior change. Keep the
separate guide checkpoint `b50561d` archived and exclude `duncan/` from every
commit. Retain first-round artifacts and record why the second cycle was needed.

### Output
Public documentation matching the filesystem's actual failure possibilities.

### Safe in nature
True — documentation only.

### Peripheral concepts
operational diagnostics, best-effort cleanup, replay/acknowledgment boundaries,
artifact history, explicit user exclusions

### Hardness Lvl
2

## Step 7 — Verify, commit and repeat both gates

### Proposed changes

Compile; run the expanded test_19, unchanged first-gate probes and the re-plan
seam probe. Then run the supported offline suites 12–18 and two no-network
test_11 helpers, with explicit nonexistent config for live 12/13 checks and
localhost-only permission for the proxy cases. No 1.33.1 run or live account.
Record exact counts, skips, corrections and limits in a new implementation.md.
Commit code/tests/public docs separately from work-folder notes and push the
same branch; tick issue checkpoints only from committed evidence.

Repeat merge-check.md against this complete live plan, original rejection,
new plan critic, actual diff and issue status. Then run a fresh in-session
critic-d on the updated PR #15 diff plus this plan, with new probes for any
remaining behavior question. Commit/post both reviews, preserve first-round
evidence and update the same PR/issue. Do not automatically merge. If this second
PR gate is rejected too, follow §7.4 back to the description/traverse rather
than starting a third patch/re-plan loop.

### Output
Verified revision, updated PR #15, and a truthful second set of merge/PR review
results, ready for the later authorized merge if accepted.

### Safe in nature
True — verification/publication on the existing feature branch only.

### Peripheral concepts
offline suite boundaries, separate commits, first-gate preservation, issue/PR
status, model flag, repeated review thresholds and user merge authorization

### Hardness Lvl
3
