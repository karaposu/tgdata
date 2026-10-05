---
model: unknown
effort: unknown
---

**Verdict: IMPLEMENT AS WRITTEN**

Falsifier: a live Telegram history observation shows that the SDK interface
cannot produce the ordered visible-message prefix required by this contract.
Affordable now: no — an authorized live account/server run is outside this
offline review. All affordable local behavioral questions identified here were
probed on the actual implementation before this verdict.

**PR disposition: ACCEPT — 0 High / 0 Medium / 0 Low findings.** This is the
second technical soundness check for PR #15. It resolves the first rejection's
runtime findings; it does not authorize merge or certify unavailable §9
model/effort metadata.

# Fresh second PR critique — #6, revision 3

Reviewed 2026-10-05 in the same warmed session, without subagents. Subject:
the actual published PR #15 diff at `196f9ce` against `dev` at
`d39a4df275bacf51f814b6a0b281c227d4d17f93`, plus the complete revision-3 plan.
Runtime is `ce938a1fd0290cf590469800ce8541f4a9723e17`. The tailored second
review prompt is committed at `66231bc`. First-round reports remain under
`history/round-1/` and in the original PR comments.

## High-level summary

The revised file layer applies one local-I/O boundary at the operations it
owns, including writes/flushes invoked by the actual SDK. SDK awaits remain
outside that boundary, so genuine transport/RPC causes keep their meaning.
The shared owner chooses primary versus cleanup-only errors, attempts remaining
teardown and prevents secondary logging failures from replacing the result.

Both first-gate failures are reproduced by unchanged probes and now pass.
The expanded regression suite passes 33 groups, with 128 actual groups across
the supported offline set and three live skips. Independent second-gate probes
also pass: budget refusal plus denied cleanup, native non-OSError path failure,
a symlink replacement between stat/open, retry after publication plus cleanup
failure, and four independent processes publishing identical blobs/manifests.

No new High, Medium or Low finding is established. No runtime patch or test
expectation change was made during this second PR critique.

## Premise Inventory

### 1 — Raw ordered history supports a complete-prefix cursor

First dependent step: retained reader (revision-3 step 1). Waste if false:
the wire continuation contract and reader/consumer boundary need redesign.
Original planned test: pre-build real SDK seam and behavioral suite; current
plan retains them at steps 1/5/7. Cheapest earlier local observation was already
run. Actual SDK ordering, basic groups, gaps, bounded pages, senderless/service
records and quota prefixes are exercised with supplied replies. Those are
**non-covering for live server history selection**. No new server assumption
was introduced by the file-layer revision.

### 2 — SDK stream calls can be guarded without misclassifying transport

First dependent step: 2. Waste if false: file-object and diagnostic boundaries
must change. Planned test: real SDK protocol before implementation, then public
API failure cases. Cheapest earlier observation: the pre-plan probe, expanded
by the plan critic to eight passing observations. Actual Photo/Document/cached
Photo paths accept the proxy and retain return identity. SDK write/flush faults
are local; an actual SDK transport wrapper retains its explicit RPC cause.
The 12-point implemented I/O matrix and second-gate non-OSError path probe
confirm the deployed code's boundary. Transport replies/faults are supplied;
no live Telegram verdict is inferred from them.

### 3 — Resource failure precedence is stable during interruption

First dependent step: 3. Waste if false: both publishers and reader interruption
semantics must change. Planned test: Python-unwind observation before build,
then actual owner/SDK/permission/cancellation/logging cases. Cheapest earlier
observation was already run. The implemented policy preserves RPC identity,
task cancellation, a genuine explicit cause, first cleanup-only failure and
read/close precedence. The independent budget-plus-denied-cleanup probe confirms
the same policy also preserves ReadBudgetExceeded, its safe prefix and its
conservative charge. Known storage refusal leaves a private file and is not
claimed to be fixed by catching an exception.

### 4 — Complete publication and verified reuse remain sound

First dependent step: 4. Waste if false: media/manifest identity and replay
artifacts need redesign. Planned test: original hard-link/SDK probes and step-5
integrity/concurrency cases. Cheapest earlier primitive tests preceded the
first implementation. Current evidence adds a real post-lstat symlink swap and
four independent publisher processes using the actual revised helpers.
In this filesystem, no incomplete final object or leftover temporary from
successful publication is observed. Standard open/opener owns the verification
descriptor, and fstat/inode/type/content checks remain. Arbitrary deployment
filesystems and power loss remain **uncovered**, with unsupported operations
surfacing as errors rather than an unsafe fallback.

### 5 — Preparation, replay and durable acceptance are separate

First dependent step: retained codec/reader (step 1), caller documentation at
step 6. Waste if false: receiver/cursor contract. Planned test: golden identity,
save/reload/defensive copies and receiver stand-in. The second-gate retry probe
adds the case where a complete blob exists but cleanup failed: the interrupted
cursor stays 100; the repaired retry verifies that blob, is charged again, then
returns 101 and saves/reloads the same returned batch. No durable caller cursor
is mutated. A receiving-service transaction is **not covered by the stand-in**
and remains explicitly outside tgdata's implementation.

No OPEN local blocker or affordable unrun prerequisite requires REORDER. Tests
of the new owner occur after its construction; the existing SDK/Python seams
were observed before dependent implementation. The model-metadata flag is
separate from code/premise findings.

## Restart Check — first rejection

**R1, false health attribution:** originally a FileExistsError under an
unreported ChannelPrivateError inherited the latter as context, and the health
wrapper reported no access despite zero requests. `batch_files._local_io` now
re-raises the same owned-local error from None; `_LocalFile` extends that
boundary to SDK stream calls without catching the SDK await. The unchanged
original public probe and new non-OSError path probe produce zero false events;
the genuine explicit-RPC-cause regression still reports the real event.

**R2, cleanup masks primary failure:** originally `_remove_temp` raised out of
finally and replaced a primary SDK error. `_owned_stream` and `_cleanup` now
track the primary BaseException, attempt close/unlink and retain the first
cleanup-only failure. The original real permission-change probe preserves the
same ChannelPrivateError and cursor. Added tests cover close/unlink doubles,
task cancellation, verification read/close and failing logging handlers; the
fresh budget probe adds another primary error class. Secondary warnings carry
only operation/type. The documented best-effort deletion limit is accurate.

Both established mechanisms are addressed at their owning layer. Neither was
hidden by altering health classification globally or treating all OSErrors,
including network errors, as local storage errors.

## Inherited Lessons

The original separation of raw records from presentation, saved observations
from re-fetches, quota charges from progress, and filenames from verified bytes
still holds. The rejection's additional lesson is now structural: error meaning
is assigned at an owned synchronous operation, and secondary teardown has an
explicit precedence policy before either producer uses it. Protocol probes
preceded implementation; public failure tests preceded the repeated gates.
The two Mediums were inputs to a committed replacement plan, not unrecorded
patches applied during review.

## Fresh second-gate evidence

Read the actual full feature diff and retained value/reader/public contracts
together with the complete revised file module, added tests/docs and the SDK,
budget and health interfaces. The published diff was retrieved after the
repeated merge check. Runtime/tests/public docs compare unchanged from `ce938a1`.

Reproduce the new observations with:

```bash
.venv/bin/python devdocs/work/6-versioned-message-batches/probe_pr_review_round2.py
```

Actual output:

```text
Second PR #15 probes — Telethon 1.45.0
PASS budget + cleanup: original ReadBudgetExceeded, cursor 101, two charged messages, no false health
PASS non-OSError path failure: ValueError stays local; zero requests and zero health events
PASS verification race: post-lstat symlink replacement rejected; cursor and outside contents unchanged
PASS retry after publication: failed cleanup keeps cursor 100; retry verifies blob and returns 101, charged again
PASS multiprocess publication: four independent processes, one complete blob/manifest each, no temp leftovers
Result: 5/5 fresh probes passed; no live-server/receiver claim
```

The new probe compiles and exits zero. Its parent blocks sockets; child publisher
processes instantiate no Telegram client and only serialize/write synthetic
data. Real SDK request/iterator/file dispatch and real filesystem operations are
exercised; scripted replies/faults supply only the external condition.

Retained evidence: **128 offline/loopback groups pass, three live checks skip**;
original PR probe **8/8**, re-plan protocol probe **8/8**. No broad rerun was
needed during this final review because runtime/tests/public docs did not change
after the full verification. The five new probes directly answer the remaining
composition questions rather than treating the old green suite as proof.

## Findings and Phase 3

**0 High / 0 Medium / 0 Low.** Phase 3 ran after the findings pass. No new
proposals require selection, and no risk was hidden, reclassified or patched
to obtain acceptance. Original R1/R2 Robust mitigations are implemented and
verified as mapped above. No further local re-plan or description/traverse
restart is indicated by this second gate.

## Remaining integration boundaries

The technical PR critique accepts this revision. Keep the feature branch as
the archive and exclude work-folder/archaeology documents plus the unrelated
guide checkpoint `b50561d` from a later authorized merge; public docs remain.
`duncan/` is not committed. Merge still requires the user's go-ahead, with
merged-code verification before pushing and manual issue closure if needed.

Exact model/effort metadata remain unavailable (`unknown`), so CONTRIBUTING §9
is explicitly **unverified** as in both merge checks. This is not counted as
a fabricated runtime finding or silently certified by the passing probes.
Live Telegram, deployed receiver transactions and deployment storage behavior
also remain outside the offline evidence stated above.
