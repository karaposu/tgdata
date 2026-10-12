---
model: gpt-6-astra
effort: max
status: FAIL
plan: DEPRECATED_step_by_step_impl_plan.md
---
# #17 revision-3 prebuild — storage cancellation remains unresolved

**Gate P0: FAIL. Do not implement revision 3.**

The proposed source/observation/control changes passed36 of37 pool case groups.
Both current-dev worker suites passed:33/33 and25/25. The failed group exercises an
allowed asynchronous storage adapter whose own awaited future is cancelled after
a real read has completed. The pool mistakes that for caller cancellation and
withholds the completed message prefix from the caller and daily delivery.

This is the purpose of the prebuild: it found an unhandled ownership boundary before
working-branch runtime changes. No runtime implementation or revision4 fold followed.
The failed plan is preserved under its DEPRECATED filename. This is one failed
prebuild, not another PR rejection or a signal that the retained router must be rebuilt.

## What ran

- Plan17ead79; tailored critic prompt4410f5a; fresh critic5ce2527; selectionc96115a.
- Product71502e5/4854464, combined with current dev2ddb852 in an isolated export.
- Merge preview had exactly one conflict: batch_engine.py. Its explicit union kept
  the existing resolver and pool-only opt-in cancellation-prefix behavior. Worker
  cleanup-failure receipts and all other dev changes remained.
- Combined tree:`7d2dc2393c473cf6cdf9642c60f7c40618b21404`.
- Python3.11.10, Telethon1.45.0, actual SDK request/pagination/native disconnect,
  actual ReadBudget and SQLite pool/daily/backfill stores. Synthetic wire supplied
  server replies; no fake reader supplied results, charges, tokens or receipts.
- Candidate changes existed only in `probes/prebuild_candidate.py`, installed over
  the real exported classes in memory. All76 exported runtime Python file hashes
  remained unchanged. Working-branch runtime files also match71502e5.
- A parent process bounded each command. No watchdog fired or task was abandoned
  as a supposed fix. Socket connect/connect_ex were forbidden in the candidate.
  Existing worker suites use their controlled offline fixtures/processes.

## Observed failure

The actual reader produced100 complete messages followed by FloodWait7200. The real
ledger retained200 units: the completed page and reservation for the failed request.
The pool then awaited its state backend's compare-and-swap during settlement.

The provider adapter awaited a separately cancelled Future. It never cancelled the
reader task and never called pool.close or another lifecycle method. One case failed
before committing; the other performed the actual SQLite CAS and then lost its reply
through that cancellation. This is a controlled I/O fault around real storage, not
fabricated permission or a synthetic source result.

| Observation | Before settlement commit | After actual settlement commit |
|---|---|---|
| Caller cancellation requests | 0 | 0 |
| Public outcome | CancelledError | CancelledError |
| Actual complete records | 100 | 100 |
| Records on public error | 0 | 0 |
| Daily pending delivery | absent | absent |
| Account attempt | unresolved | settled |
| Saved wait | none observed | 7200 seconds |
| Actual charge | 200 | 200 |
| Second source reads in the call | 0 | 0 |

The unresolved token prevents automatic reuse in the first case. The second case
preserves the known wait. Those safeguards held; neither supplies the missing
message delivery. A later account need not see the same history, so withholding the
already-read prefix is a real outcome defect.

## Why revision 3 did not close it

`AccountPool._backend` still propagates every CancelledError. `_settle` also lets it
escape as cancellation, bypassing its ordinary local-storage-error/prefix path.
`SyncEngine.prepare` consequently takes its caller-cancellation path rather than
publishing the actual source-error prefix. The candidate wrapped _backend in a
control scope, but did not give the awaited provider's completion its own cancellation
meaning. The source holder cannot control what happens during the later state await.

The critic's original Phase2 recorded no new content defect and required this combined
experiment. The experiment falsified the overall outcome promise. Its result is now
recorded in critic.md without rewriting that earlier review into a fictitious prior
finding. Do not claim the plan passed merely because its headline callback cases did.

## What the other cases established

The same candidate passed real raw/daily/backfill prefix+wait histories, source-free
replay/ack after closure/backend/config/budget removal, successful recovery reporting,
application observer cancellation and outside-created close, secondary health-finalizer
error/cancellation/timeout, and distinct source-internal cancellation with unresolved
account permission and retained group prefix.

It also passed twelve provider reentry combinations (load/status/admission/settlement
with direct/task/wait_for close), foreign/expired-scope controls, drain during read/
close/caller cleanup, event count/byte/oversize/type/drop behavior, ambient legacy
callback-flag independence, and unchanged legacy health callbacks. Reporting created
no observer tasks.

Native held/failed disconnect and explicit retry, actual caller cancellation before/
after admission, repeated source/close cancellation, credential reload, both routing
strategies, identity mismatch, timeouts and ordinary uncertain-write/prefix cases
also passed. Those results remain useful. They do not waive the failed37th group.

The worker33+25 checks validate its actual source/process behavior on the combined
batch seam. They do not constitute a full revised pool regression or live qualification.

## Required next design work

Distinguish the caller's stop request from cancellation inside an awaited storage
provider. Preserve completed source data through the latter as a local storage
failure, while retaining uncertain-write semantics and genuine caller cancellation.
Any provider-task ownership solution must also specify what is awaited/cancelled
before releasing an operation; it cannot simply detach a live state write.

Do not blanket-catch cancellation as an ordinary error, assume a cancelled response
means rollback, retry CAS into fresh permission, or change the failed test to expect
lost data. Resolve this contract first, write a replacement plan, run a fresh critic
and rerun the entire combined gate. The observation/reporting and source-control
candidate can remain evidence; it is not installed product code.

## Reproduction and evidence

Run in a fresh Python process from the issue branch:

```bash
python devdocs/work/17-account-pool/probes/export_prebuild.py
python devdocs/work/17-account-pool/probes/run_prebuild.py
```

Use the project's existing Telethon1.45.0 environment. The export command writes only
an isolated Git index/export and its manifest, without moving branch refs or changing
working-tree runtime files. The parent runner records a fresh numbered attempt and
expects the combined gate to fail until a new accepted candidate addresses the gap.

- [Complete pool output](evidence/replan-r3/attempt-1-combined.txt)
- [Machine-readable gate result and candidate hashes](evidence/replan-r3/attempt-1-summary.json)
- [Export manifest and source hashes](evidence/replan-r3/export-manifest.json)
- [Worker source suite](evidence/replan-r3/attempt-1-worker37.txt)
- [Worker process suite](evidence/replan-r3/attempt-1-worker38.txt)

No Telegram account/session/login/read/join or live budget was used. Two-account E1,
production implementation, full regression, renewed merge check/PR critique and merge
remain pending. Main checkout, duncan and unrelated work are unchanged.
