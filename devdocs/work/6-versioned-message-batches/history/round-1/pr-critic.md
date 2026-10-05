---
model: unknown
effort: unknown
---

**Verdict: IMPLEMENT AFTER FOLDING THESE IN**

Falsifier: an authorized live history read demonstrates that the selected SDK
interface cannot produce an ordered, visible-message prefix with a usable
exclusive cursor. Affordable now: no — a live account/server observation is
outside this offline review. All affordable local checks below were executed.

**PR disposition: REJECTED — 0 High / 2 Medium / 0 Low.** CONTRIBUTING §7.3
rejects any Medium. The critic-d content verdict says the design can survive;
it does **not** authorize patching or merging this PR. Under §7.4, return to
step 2 and re-plan with these findings, then repeat both merge gates.

# Fresh PR critique — #6 / PR #15

Reviewed 2026-10-05 in the same warmed session, without subagents. Subject:
the actual published PR #15 diff at `81e3cfddd4d6c55db75cd403011163ccfe8f8c7d`
against `dev` at `d39a4df275bacf51f814b6a0b281c227d4d17f93`, together with
`step_by_step_impl_plan.md` revision 1. Runtime is `001f134`; later commits are
the user's guide checkpoint and review records. The tailored prompt is
`dynamic_pr_critic_prompt.md` (`e398958`). Pre-build `critic.md` is preserved.

## High-level summary

The raw value, cursor discipline, file identity and shared budget integration
hold in the exercised normal/interruption paths. Fresh probes also confirm
basic groups, channel authors, cross-process JSON identity, less common SDK
photo representations, a successful budgeted reference refresh and cancellation
after one already completed file.

Two filesystem failure paths violate the promised diagnostic contract. An
ordinary local path error can inherit an unrelated, unreported Telegram error
and produce a false group-health event. A cleanup failure can replace the
original SDK error, defeating callers that act on that exception's type. Both
were reproduced through the public batch API; no production code was changed.
The existing 25-group suite still passes, so these are missing failure cases,
not a claim that the earlier 120-group verification was misreported.

## Premise Inventory

### 1 — Visible-history ordering permits complete-prefix continuation

First dependent step: 3. Waste if false: reader/continuation and consumer-facing
contract work from step 3 onward. Planned test: pre-build actual SDK iterator
probe, then step 5. Cheapest earlier observation: the already performed SDK
probe; a definitive live-server test needs an authorized account/server run.
Coverage: real 1.45.0 iterator exercised with controlled replies, including
paging, gaps, basic groups and cursor bounds. Supplied replies are **non-covering
for live history selection**. No affordable local prerequisite test remains
unrun, and no live completeness claim is made.

### 2 — Completed SDK downloads can be represented as verified files

First dependent step: 2. Waste if false: publisher/reader media composition.
Planned test: real SDK file-object seam before build; step-5 actual download
tests. Cheapest earlier test: the pre-build probe, already passed. Fresh
coverage adds stripped-photo/video-size selection and successful reference
refresh, while the original suite covers normal/cached/progressive output,
missing/truncated bytes and denied refresh. These run actual SDK selection,
streaming and request flow; server content is supplied, so they do not prove
what a live server would return. Findings below concern local failure handling,
not a false SDK output premise.

### 3 — Non-replacing publication is supported on the target filesystem

First dependent step: 2. Waste if false: all local artifact publication.
Planned test: 24-writer real filesystem probe before build, then implemented
publisher tests. Cheapest earlier observation: that pre-build test; already
performed. Coverage: real local hard links, flush/fsync, concurrent writers,
existing-object integrity and cleanup. The fresh permission-change probe runs
the actual filesystem and disproves error precedence, not hard-link atomicity.
Deployment volumes/power-loss behavior remain **uncovered** and explicitly
outside this review. Unsupported operations must continue to raise.

### 4 — Replay identity is separate from receiver effects

First dependent step: 1 for identity, step 5 for the caller protocol. Waste if
false: codec/save/delivery contract. Planned test: independent golden fixture,
immutable copies, save/reload and a receiver stand-in. Cheapest earlier test:
stdlib canonicalization/SHA observation, followed by tests of the new value.
Coverage: exact golden bytes also survive reordered/escaped JSON and two fresh
Python processes with different hash seeds. The receiver stand-in is
**non-covering for a deployed receiver's atomic deduplication**; the docs assign
that responsibility to the receiver and never promise exactly-once effects.

### 5 — Existing admission and diagnostics remain authoritative

First dependent steps: 3–4. Waste if false: guarded-reader integration and error
contract. Planned test: existing #9/#4 source/probes plus step-5 integration.
Cheapest earlier test: existing real-client fixtures; those were used. Coverage:
quota denial, resume, blocked/successful implicit refresh and original normal
RPC errors are exercised through the actual guard/wrapper. The local error
provenance/cleanup cases below were missing and fail now. They are observable
defects in newly implemented failure paths, not stochastic vendor premises or
a reason to deprecate the whole data-contract design.

No OPEN planning/execution blocker is declared in the description/plan. The
affordable local behavior questions were tested during this critique. There is
no REORDER experiment pending and no meaning-gap/wrong-layer verdict.

## Restart Check

The description cites three existing limitations, not an abandoned #6 build.
Their mechanisms are established in the source and earlier seam probe:

- Presentation conversion can drop a senderless record because
  `MessageEngine._process_message` returns None without a sender. BatchEngine
  projects raw messages directly, and senderless/service cases pass.
- Existing JSON export lacks a normative schema/identity. MessageBatch owns an
  exact v1 codec/hash and rejects malformed values; golden/replay checks pass.
- Existing media filenames identify origin rather than bytes. The new publisher
  hashes complete downloaded contents; equal-content/different-root and changed
  content checks pass without changing legacy filenames.

The feature is operating at the right layer. The new findings concern diagnostic
guarantees around the file layer, not an unaddressed original problem.

## Inherited Lessons

Saved observation versus fresh query is respected by steps 1/5 and cross-process
replay checks. Raw records versus presentation rows is respected by step 3 and
actual SDK message probes. Network admission versus application progress is
respected by the step-3 append boundary and budgeted refresh probes. Filename
versus content identity is respected by step 2 and byte verification. Actual SDK
behavior versus documentation assumptions was tested before implementation and
extended on 1.45.0 here. The weak spot is the promised preservation of diagnostic
meaning: step 2 handles its custom errors but misses native filesystem errors
and a secondary cleanup failure.

## Evidence

Read the full changed runtime/test/public-doc implementations and the plan;
refreshed the relevant factory/session, health classification/reporting, budget
adapter, legacy media/entity helpers and SDK iterator/download/sender-init flow.
The actual PR diff was saved locally via `gh pr diff 15` before critique.

Reproduce with:

```bash
.venv/bin/python devdocs/work/6-versioned-message-batches/probe_pr_review.py
```

Actual output (exit 1 intentionally reports the two observed violations):

```text
Fresh PR #15 probes — Telethon 1.45.0
PASS identity: reordered/escaped JSON and two independent processes preserve exact golden bytes
PASS basic group: marked chat -17, gap 101->104 and cached channel author; no enrichment
PASS photo selection: real SDK stripped-photo and video-size paths match prepared bytes/size/hash
PASS reference refresh: SDK retries with the refreshed reference; history + refresh charge exactly two reads
PASS publication fault: same local exception, one completed record, cursor 101 and no public/temp file
PASS cancellation: second download temp removed; only the first complete immutable blob remains
FAIL local error context: error=FileExistsError, Telegram requests=0, health=[('no access', 7, 'CHANNEL_PRIVATE')]
FAIL cleanup error precedence: original=ChannelPrivateError, raised=PermissionError, same_object=False, cursor=101, temp_left=1
Result: 6 passed; 2 contract violations
```

The control run of `test_19_message_batches` still returns **25/25**. Runtime,
tests and public docs remain unchanged from the earlier 120-group verification.
The probe file compiles and diff checks pass. No live account/socket is used.

One probe-fixture correction preceded the final output: changing `from_id` after
a Message was constructed left Telethon's cached `sender_id` at 88. Source and
a recording check showed that inconsistency. The basic-group fixture now
constructs the Message with its channel author initially, as deserialization
would. Its expectations were retained; production code was not changed.

## R1 — Local filesystem errors can inherit a false Telegram verdict

**Risk**

An application handling an earlier Telegram access error may attempt another
batch read using an unusable media directory. The library can then report that
the new group is inaccessible, even though it sent no Telegram request for that
read and only encountered a local path error. An operator or worker consuming
health events receives the wrong reason to stop or investigate that group.

In `tgdata/batch_files.py:29`, `prepare_directory` lets native OSError subclasses
escape unchanged but without suppressing incidental exception context. The
public call reaches it at `tgdata/batch_engine.py:157`, inside the façade's health
wrapper. If the caller is currently handling an **unreported** ChannelPrivateError,
the FileExistsError inherits it through `__context__`. `health._chain` at
`tgdata/health.py:155` follows that context and `classify` reports CHANNEL_PRIVATE
for the current group. The fresh probe records FileExistsError, **zero Telegram
requests**, and a `no access` event for group 7. The custom BatchStorageError
suppression at `batch_files.py:19` does not apply to native filesystem errors.

**Severity:** Medium

**Category:** Error provenance / account-health contract

**Impact:** False health events and summary state can attribute a local storage
failure to Telegram access. This violates description criterion 6 and the plan's
local-versus-Telegram error boundary. An ordinary path failure without an active
unreported RPC context does not trigger this finding.

**NoobEng:** Python implicitly links exceptions raised inside an `except` block
to the exception being handled, even across called functions. tgdata follows
these links to find Telegram reasons through genuine wrappers. Local exceptions
must prevent unrelated links from being interpreted as their cause while
retaining the promised exception class/object. Merely using a different
top-level exception type does not stop the health classifier.

**Affected areas:** Batch output-directory preparation and native local I/O
failures in the artifact publisher; the existing health wrapper consumes them.
The shared health module itself is unchanged by this PR.

### Mitigation — Quick

Have callers suppress health delivery while handling storage failures, or avoid
calling the batch API from an exception handler. This hides the symptom and
risks hiding real Telegram failures in the same operation.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Give the batch-owned filesystem operations a narrow local-error boundary that
retains each OSError's identity/type while suppressing incidental RPC context.
Cover directory creation, local reads/writes/fsync, verification/publication and
cleanup. Keep awaited SDK/network exceptions outside that local boundary, so
real explicit Telegram causes retain their existing health meaning. Add public
API probes for pre-resolution and post-prefix filesystem failures under a stale
RPC context, alongside a real current RPC error control.

**Why this is robust:** fixes the actual provenance at its owned source instead
of weakening the shared classifier or replacing native filesystem types.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* It covers the native local I/O paths that are actually broken
while retaining the existing network/classification contract. A shared local
provenance class exists in three modules, but those custom exceptions already
work. Migrating them and the classifier adds extent without closing another
observed defect. This repair also survives any later shared convention.
*For future:* —

### Mitigation — Long-term

Introduce a shared local-error provenance convention understood by health
classification and migrate the current suppression conventions in
`message_batch.BatchFormatError`, `batch_files.BatchStorageError` and
`read_budget.ReadBudgetError` to it.

**Why this is long term effective:** one explicit local-error signal could
serve future modules without relying on each constructor's context flag.
Those existing custom classes already handle their own context correctly;
this wider migration is not required to repair the new native I/O paths.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit if multiple new modules need native-error provenance.
The same local marker could serve them without per-module special cases, but
changing the already-correct format/budget errors now would enlarge this task.
This is future work, not a prerequisite; the selected repair would survive it.

## R2 — Cleanup can replace the original download exception

**Risk**

If a media download fails after the output directory becomes unwritable, the
attempt to remove its temporary file can fail too. The library then raises the
cleanup error instead of the download error. A caller that handles a specific
Telegram refusal no longer receives that exception, even though the completed
message prefix is still recoverable. Loss of write permission can prevent
cleanup; it should not change which error caused the operation to fail.

`download_blob` calls `_remove_temp` unconditionally in its finally block at
`tgdata/batch_files.py:104`; `_remove_temp` at line 73 suppresses only
FileNotFoundError. Any other unlink error replaces the active exception from
the awaited SDK writer. `save_manifest` has the same finalizer at line 120.
The public-API probe completes message 101, opens media for 102, changes the
real temporary directory to mode 0500 and supplies a ChannelPrivateError from
the SDK transport. The caller receives **PermissionError**, not the original
object, with cursor 101 and one private temporary file left. Permission is
restored only by the probe's teardown, after the observation.

**Severity:** Medium

**Category:** Error precedence / cleanup / public exception contract

**Impact:** Exception-type-based retry/stop handling no longer sees the actual
download failure, contradicting the documented same-object re-raise contract.
The cursor remains safe and no partial digest-named file is published; those
facts do not repair the exception contract. A private temporary file may remain
while storage permissions prevent removal.

**NoobEng:** An exception raised in `finally` takes precedence over an exception
already being propagated. Cleanup needs an explicit primary/secondary error
policy. Making deletion best-effort when a primary exception exists does not
mean pretending a cleanup-only failure was successful. Cancellation is another
primary outcome whose identity must survive secondary cleanup errors.

**Affected areas:** `batch_files.download_blob`, `save_manifest`, `_remove_temp`,
and the exception that `BatchEngine.fetch_batch` attaches `partial_result` to.

### Mitigation — Quick

Ignore every unlink OSError. This preserves a primary error accidentally but
also hides cleanup-only failures and can accumulate private temporary files
without any diagnostic.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Give both publishers an explicit shared cleanup-error policy: when an exception
or cancellation is already active, preserve that exact primary outcome and
report the secondary cleanup failure safely; when cleanup is the only failure,
raise it as a local error. Document that removal is best-effort when the
filesystem refuses it. Exercise a real permission-denied cleanup after an SDK
error and cancellation, plus a cleanup-only failure, without changing cursor
or complete-publication guarantees.

**Why this is robust:** handles precedence in the two actual finalizers while
preserving primary identity, cancellation and useful cleanup-only errors. It
does not need a background collector or broader client lifecycle changes.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The two genuine instances are download_blob and save_manifest;
both already call the same removal helper. One explicit cleanup policy can
serve both without content-specific branches. It closes the current class with
less rewrite than a new publication context manager, so it has greater reach
per unit of extent. It must include cancellation and cleanup-only controls.
*For future:* —

### Mitigation — Long-term

Consolidate both artifact producers into one publication context manager that
owns temporary creation, completion, publication and exception precedence.
Future artifact producers would use that lifecycle instead of writing another
finally block.

**Why this is long term effective:** the existing download and manifest
publishers are two real instances of the same temporary-file lifecycle. One
mechanism can own both; file content production stays in their callers. Its
additional rewrite buys little extra reach over a shared cleanup policy for
the two current paths.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Consider a common publication lifecycle only if more producers
make the open/write/publish duplication itself a maintenance problem. The
selected cleanup policy remains valid inside that later abstraction; no
prerequisite or extra artifact service is justified now.

## Phase 3 — Mitigation selection

Executed separately after Phase 2. Both Robust proposals are selected and
elegant; neither is a last resort. The two class/extent comparisons are recorded
in their notes. Quick fixes hide failures and have no external constraint to
justify them. Long-term alternatives remain unselected future considerations.
No risk, severity or proposal was rewritten during selection, and no runtime
fix or plan rewrite was made. The PR remains rejected; the selected mitigations
are inputs to the required re-plan, not permission to patch past that gate.

## Other review outcomes and process boundaries

No additional High/Medium/Low finding is established in the other exercised
contracts. Imports/package discovery and Python-compatible syntax introduce no
observed break; existing successful DataFrame/media paths are unchanged. Full
batch copies/canonicalization and synchronous local hashing are bounded by the
documented count/local-I/O choices, with no claim of nonblocking arbitrary
storage. The guide checkpoint is excluded from #6 integration and duncan is
excluded from commits by user instruction.

CONTRIBUTING §9 model/effort metadata remain unavailable and unverified as
flagged by the merge check. This is separate from the two concrete runtime
findings; it is not counted as a fabricated code risk. No merge is authorized
or performed. Return to planning with R1/R2, preserve both original artifacts
and this failed gate as history, then repeat verification and both PR checks.
