---
model: unknown
effort: unknown
---

# Merge check — #6, second cycle / revision 3

**Fidelity verdict: PASS. Proceed to the fresh second PR critique on PR #15.**
This is not a merge authorization or a certification of CONTRIBUTING §9 model
metadata. The first merge check and rejected PR critique remain in
`history/round-1/` and their original PR comments.

Reviewed in the same warmed session on 2026-10-05, without subagents. Refreshed
`origin/dev`: `d39a4df275bacf51f814b6a0b281c227d4d17f93`. Reviewed head:
`96389f144e8b431fc64c0f0993165c706e17c103`; current runtime implementation:
`ce938a1fd0290cf590469800ce8541f4a9723e17`. Read current description, triage,
replacement plan, plan critic, original rejection and actual full feature diff,
including the new file lifecycle and expanded regression suite.

## 0 — Warmth and weight

The original full-source #5/#9 context, merged-tree verification at `d39a4df`
and #6 traverse at `c7f7e1e` remain valid warmth records. The file/SDK/health/
budget boundaries were refreshed during this cycle, including actual protocol
probes before implementation. Both warmth anchors, triage `7fe270c`, rejected
gate `670564e`, re-plan `e391cd6`, critic `d82c663` and code/report commits are
verified ancestors. GitHub labels remain enhancement/heavy/open to implement;
feature-heavy still fits the data, cursor, filesystem and consumer boundaries.

## 0b — Scope versus triage

The whole feature stays in the surfaced record/reader/media/client/error/test/
documentation territory. Revision 3 changes only `tgdata/batch_files.py` in
runtime code, plus its tests and public docs. Shared health, budget, session,
connection, façade and v1 codec/reader code are unchanged from `001f134`.
The local stream proxy and owner are mechanisms for the existing file boundary,
not an added global service or new feature weight.

The separately checkpointed guide edit `b50561d` was explicitly authorized by
the user, remains unrelated to #6 and is excluded from eventual integration.
`duncan/` is excluded from commits per the user's explicit instruction; no files
there are tracked. The first-round work documents were preserved without content
changes under `history/round-1/`, not overwritten by this new cycle.

## 1 — Does the diff match the replacement plan?

- Step 1's complete v1 schema, golden identity, raw reader, safe cursor, shared
  controls and legacy contracts are retained. Source comparison confirms this.
- Step 2's `_local_io` invocation and `_LocalFile` proxy cover owned filesystem
  and SDK stream calls while the SDK await stays outside the local guard.
  Native exception type/object remains intact; unrelated cause/context is
  suppressed at the owning action, not by weakening global health classification.
- Step 3's shared `_owned_stream`/`_cleanup` tracks a primary BaseException,
  attempts close and unlink, preserves the first cleanup-only error and logs
  secondary operation/type safely. Logging failure cannot mask the result.
- Step 4 composes both publishers and existing-file verification with that
  owner. Standard open/opener takes descriptor ownership; lstat, nofollow,
  fstat/inode and byte-integrity checks remain. Output closes before publication.
- Step 5 retains the original 25 test groups and adds eight failure groups,
  including a 12-point local-I/O matrix, actual cancellation/permissions,
  explicit SDK causes and verifier read/close/outer-cleanup precedence. The
  unchanged first-gate probes also pass on the revised implementation.
- Step 6 documents primary precedence, cleanup-only errors, guarded warnings
  and filesystem-refusal limits without changing the wire format or promising
  impossible deletion.
- Step 7 has compilation/diff checks and **128 actual offline/loopback passing
  groups, three live skips**, plus eight re-plan seam observations and eight
  first-gate probes. Code and work notes are separate commits; the repeated
  reviews are now being performed against that exact code.

No architectural deviation. Revision 3 remains live because the new plan critic
selected no additional mitigations; task-impl explicitly skips Fold for its
IMPLEMENT AS WRITTEN verdict. Original R1/R2 Robust choices were incorporated
by the re-plan itself, not left for ad-hoc runtime patching. The absence of a
fabricated revision 4 is explained in critic.md.

## 2 — Does the plan still make sense?

Yes. The original failure mechanisms are owned by the file layer, so correcting
error provenance and resource teardown there avoids coupling global health or
budget logic to arbitrary filesystem exception types. The original raw value
and reader remain the right layer for the feature. Real SDK protocol probes
confirmed the private file object before dependent runtime work.

The implementation respects the plan's limits: local I/O remains synchronous,
server replies are synthetic in tests, deployment volumes/receiver transactions
are not certified, and filesystem refusal can leave a private temporary file.
No incomplete public blob or automatic durable-cursor advancement is introduced.

## 3 — Are every critic's findings answered?

Original PR **R1 (Medium)** is answered by `_local_io` at batch_files.py:26,
the SDK file proxy at line 38, directory handling at line 89 and guarded
verification/publication operations. The original zero-request false-health
probe now emits no event. The new matrix and genuine-transport-cause control
verify both sides of that boundary.

Original PR **R2 (Medium)** is answered by `_cleanup` at line 58 and
`_owned_stream` at line 78, used by download, manifest and verification paths.
The real permission-change reproduction now raises the same ChannelPrivateError
with cursor 101. Cancellation, close/read double failure, cleanup-only error and
raising-log-handler cases pass. Private leftovers are documented accurately.

The replacement plan critic (`d82c663`) has **0 High / 0 Medium / 0 Low**; there
are no new selected mitigations or deferred Lows. This is fidelity evidence,
not a substitute for the fresh second PR soundness check.

## 4 — Is issue #6's status accurate?

Current T/0/1/2/3/4/5 checkpoints are backed by committed artifacts, including
the description clarification/re-plan `e391cd6`, plan critique `d82c663`, code
`ce938a1` and evidence `96389f1`. The issue states the first rejection historically
and the passing unchanged reproductions now. Steps 6/7 of the second cycle stay
pending until the new review artifacts are committed and posted. The original
request and target Telethon 1.45.0 are preserved.

## Integration boundary and model flag

At a later user-authorized merge, exclude `devdocs/work/6-versioned-message-batches/`,
any archaeology refresh and the unrelated guide delta from `b50561d`; retain
the public docs/README changes and the branch archive. Run the merged-code
checks before pushing and handle issue closure on dev as with #5/#9.

CONTRIBUTING §9's requested exact model/effort cannot be verified from this
session; artifacts retain `unknown`. This remains an explicit merger flag,
separate from the now-addressed runtime findings. PR #15 stays a draft pending
the fresh critique. Nothing in this fidelity result merges or closes the issue.
