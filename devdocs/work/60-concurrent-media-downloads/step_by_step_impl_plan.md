---
model: gpt-6-astra
effort: xhigh
---
# Concurrent media downloads — revision 1

### What is the task
Implement issue60's optional `download_concurrency=1` on both readers and their
runtime daily/backfill/pool consumers. Preserve the current inline path at one;
overlap only attachment preparation above one, keeping source order, truthful
partial progress, configured wait policy and fully owned cancellation. Inputs:
description4821a7b, triaged06021a and traverse finding159f642.

### Huge Hard Blockers
#### Planning Blockers
None identified. Actual Telethon1.45 source confirms direct/exported download calls,
internal/cached waits and CDN creation seams. Native cancellation probe proves a
borrowed iterator needs explicit closing. These are concrete implementation seams,
not missing account/identity architecture. The live speed estimate is not a premise
for correctness or a promised outcome.
#### Execution Blockers
- Complete combined real-component prebuild PASS is required before step1 adoption.
  Agent runs it in a git-free candidate, using actual Telethon, files, budgets and
  public consumers. Status: pending experiment, no external dependency.
- Live throughput comparison requires a suitable account/group/shared allowance and
  explicit bounded read-only authorization. Not part of product adoption steps;
  record unqualified performance and provide an opt-in procedure, no deployment.

### How this implementation moves toward desired state
Add one private owner for optional media windows, connect it to existing source/file
seams, and let each reader retain result acceptance. Forward a nondefault runtime
option without changing stored batches/receipts. Qualify the complete combination
before copying product bytes, then run affected/full regression suites.

### High-Level Summary
| Step | Change | Expected output |
|---|---|---|
|1|Private media owner, raw admission and explicit observers|Bounded tasks/resources with coordinated source waits|
|2|Batch reader windows|Ordered validated records and correct partial prefixes|
|3|Legacy reader windows and complete named files|Same default path; strict opted-in media outcomes|
|4|Runtime consumer forwarding|Daily/backfill/pool options without receipt changes|
|5|Tests and user documentation|Actual SDK/public-path coverage and bounded benchmark procedure|
|6|Verification and separate commits|Qualified feature implementation and honest issue handoff|

## Step 1 — owned media work and request policy
### Proposed changes
Add private `tgdata/media_downloads.py` with strict integer1–16 validation and a
kwargs helper omitting1. Do not accept bool/coercible strings/floats. Use ValueError
with suppressed incidental context before source/storage I/O. An opt-in owner marks
its ConnectionEngine synchronously before connecting; reject a second active opt-in
media operation before I/O. Release only after its tasks/resources settle. References-
only reads need no owner, but still validate options. Independent engines and ordinary
N1 calls remain outside this local gate, explicitly documented.

The owner accepts a finite ordered list of at mostN items, creates at mostN children,
and records outcomes as values. On the first observed child failure, stop remaining
children once, retain a cleanup task and shield/join it through repeated caller stops.
Select the triggering error; a real caller cancellation dominates observed child
outcomes. After all children settle, publish only the longest successful prefix in
input order through a synchronous reader-owned acceptance callback, then re-raise the
same primary object. No detached work, no first-completed cursor, no refill before
window settlement. Cleanup errors are logged by type only; preserve primary failure.
If cleanup alone fails, raise a local context-suppressed RuntimeError. Mark the affected
client unusable for further opt-in work until replaced, rather than claim clean reuse.

Create an explicit task-owned source context for parent source setup/pagination and
children's media requests. Context inheritance alone never authorizes SDK background
tasks. Add narrow private child-membership contexts to ambient health._Call and batch
heartbeat observer; existing owner checks remain the default, and only an enrolled
child can attribute observations. Membership is removed on child settlement; parent
scope deactivation suppresses late callbacks. Do not relax verified account-operation
handles or owned-health task authority.

Add a client mixin in the common ConnectionEngine client MRO, bypassing unchanged
when no media context is active. Wrap the sender at `_call` so every actual enqueue
(including SDK retries and message-reference refresh) first checks the operation's
monotonic wait deadline. Observe wait exceptions while awaiting the actual send,
before the SDK handles them; extend the deadline, never shorten it. Include the SDK's
four wait-error types and zero-second→one-second normalization. Observe applicable
cached waits before entering the SDK so siblings share their deadline too. A caller
whose configured threshold disallows the remaining wait receives a wait exception;
a permitted gate wait emits sliced heartbeat and resumes at the deadline. Preserve
SDK bounded retries, original wait/error types where directly observed, and existing
legacy outer retry behavior; no new worker retry loop or shared property mutation.
Budget reservation must still occur immediately before the actual underlying enqueue,
after the gate; never reserve quota and then sleep at this new gate.

Track actual SDK iterators returned by `_iter_download` within the explicitly owned
media child. Close every tracked iterator in the child's finalization, including
cancel/error paths the SDK does not close itself. Normal SDK double-close is harmless
when sender is already cleared. Close only initialized iterators with resources.
For SDK-created CDN clients, the scoped `_get_cdn_client` path must register the new
helper before its asynchronous connect can suspend and pass the source client's
configured request/wait policy at construction. Mirror the small existing Telethon1.45
helper factory using the same clone/DC/proxy/connection behavior; no global monkeypatch.
Keep this scoped override inactive on default reads. Retain and settle created helper
clients on any result/error/stop. Actual private SDK seams are a pinned-version proof
obligation; document that1.45 is the qualified version.
### Output
Private bounded owner/source mixin; exact enrollment in existing observers; no public
scheduler abstraction, account registry or durable state.
### Safe in nature
False
### Peripheral concepts
Context ownership, SDK retry/send order, budgets, exported/CDN lifetime, health, heartbeat.
### Hardness Lvl
5

## Step 2 — bounded batch attachment preparation
### Proposed changes
Extend BatchEngine.fetch_batch and TgData.get_message_batch with the default option.
Validate before directories/source work. N1 calls the existing preparation loop with
no new media owner or download callback keywords. For download mode above one, hold
the owner around the complete source session and bind its client context before
resolution/pagination. Keep history reads/date filtering and `_record` in the parent.
Accumulate at mostN eligible records, with a bound also respecting remaining requested
limit; each work item binds its own message/record (no closure over the moving loop
variable). Workers call real download_blob and existing complete-file validation.
Accept records in input order only after settlement; append into the existing records
list so pool capture sees the same prefix. Flush a final short window before success.
On source/metadata failure while collecting a window, no unfinished record becomes
progress; already accepted earlier windows remain. Preserve original errors/cancellation
and existing `_retain_cancelled_prefix` policy. No wire/hash/receipt changes.
### Output
Same batch format with optional parallel bytes and correct ordered interruption prefix.
### Safe in nature
False
### Peripheral concepts
Window/date scans, raw records, blob publication, pool captures, batch limits.
### Hardness Lvl
4

## Step 3 — legacy attachment preparation without changing default behavior
### Proposed changes
Keep the current fetch implementation as the inline default. Add a wrapper/optional
private owner argument so above-one media reads retain ownership across any existing
outer flood retries. Preserve the same iteration/date/min_id/safety-limit rules.
Use an optional prepared-message iterator: obtain metadata/profile enrichment in the
parent, preserving skipped/date-excluded rows, then perform only attachment work in
finite windows. The outer reader still owns counters, callbacks, resume cursor and
DataFrame formatting. Bound a window by the remaining callback batch capacity, so
no next-batch download outlives its callback or designed pause. Stop at the existing
window boundary without downloading excluded messages. No parallel get_sender or
profile-photo work.

Refactor message metadata and attachment completion only as needed to reuse the
current shape; do not copy the entire fetch algorithm into a second engine. Above-one
attachment errors propagate with the prepared DataFrame prefix, including budget and
source errors; default best-effort behavior is unchanged. Preserve original exception
and cancellation. A completed later file cannot become a row past an earlier gap.

For opted-in disk downloads, use native temporary files and existing local-I/O/owned-
stream principles, publishing the final deterministic message filename only after
SDK completion/flush. Do not expose a partial final file on error/stop. Existing-file
reuse stays compatible; do not claim to validate historical files that the legacy
cache never hashed. Collisions must not overwrite another file; retain or verify the
winner as required by the existing deterministic filename contract. In-memory bytes
remain bounded byN in-flight preparations; returned DataFrame still holds requested
media and its existing memory warning. If both disk and bytes requested, retain both
outputs without raising concurrent per-message request count beyond the worker bound.
### Output
Optional bounded legacy downloads, same columns/ordering/callback semantics, explicit
strict media errors above one and complete new named-file publication.
### Safe in nature
False
### Peripheral concepts
Legacy filters/retries/batch pacing, enrichment, file reuse, DataFrame partial results.
### Hardness Lvl
4

## Step 4 — forward runtime tuning through existing consumers
### Proposed changes
Add the option to ProgressFacade.sync_group/prepare_backfill, SyncEngine.prepare,
BackfillEngine.prepare and AccountPool.read/get_message_batch/_read/_read_batch/
sync_group/prepare_backfill. Validate before source/store/capture work as appropriate,
then forward only nondefault keywords to injected readers. Scope is the selected
source ConnectionEngine; the pool retains its exclusive attempts and no-wait clients.
Pending replay verifies/returns saved blobs without source requests even if the valid
option changes. No persisted scheduling knob, backfill context/receipt schema, worker
job grammar or pool routing changes. Ordinary replay/metadata calls need no scheduler.
### Output
All requested public read paths can opt in while stored delivery stays identical.
### Safe in nature
False
### Peripheral concepts
Injected readers, state-only replay, exact attempts, capture lifecycle, budget admission.
### Hardness Lvl
3

## Step 5 — actual composition tests and documentation
### Proposed changes
Add `tgdata/smoke_tests/test_49_media_concurrency.py` using real Telethon1.45 iterators,
download methods, generated RPC requests, native temp files and existing synthetic
sender fixtures (network forbidden). Fixtures control replies/timing only, never
supply successful cleanup, ordering or budget behavior. Cover actual overlapping N3
with out-of-order completion;N1 parity/keyword omission; bounds on long history;
invalidN before anyI/O; early file failure after later success; repeated callerstop
while resourcecleanup is held; sender/data-centre borrow return; CDN creation policy
and cancellation; cached/SDK-handled/propagated waits and no independent retries;
reference-refresh budget; local I/O and cleanup error precedence; identical blobs and
legacy filename collision; callback stop/pause; foreign/background task attribution;
slow versus stalled heartbeat; default legacy best-effort versus opted-in failure;
real daily/backfill/pool propagation/replay/capture. Test references-only no scheduler.

README and new docs/media_downloads.md describe signatures/default1, small example3,
local coordination extent, strict opted-in failure, policy-preserving backoff, completed
prefix/extra files, supported surfaces and resource limits. Update smoke README.
Provide a bounded read-only benchmark procedure, cold-cache comparison1/3 with counts,
bytes/time/waits/peak concurrency and stop-on-wait instruction; no automatic live run
or asserted multiplier. Do not change SDK dependency or package version.
### Output
Meaningful regression suite and clear caller documentation, including known limits.
### Safe in nature
False
### Peripheral concepts
Actual SDK transport seams, user contracts, reproducible validation, live-test scope.
### Hardness Lvl
4

## Step 6 — verify and commit separately
### Proposed changes
Compile/3.7 grammar check (not native3.7 claim), run new suite plus affected14/16/18/19/
22–31/39–44 and full supported12–19/22–46/48/49 plus seven demos on Python3.11.10,
Telethon1.45. Preserve three optional live skips. Use isolated git-free prebuild first;
after PASS/fold adopt exact candidate bytes in steps1–5 and verify affected/full suites
without changing expectations to hide failures. Small local fixes only; structural
failure stops per task-impl and is recorded. Commit product/tests/docs separately
from this work folder. Update issue60 with committed artifacts and actual results.
No merge/release automatically in this implementation run; next merge-check/PR/fresh
critic stages remain visible. Preserve existing branches and unrelated user changes.
### Output
Completed tested implementation with traceable commits and explicit remaining review.
### Safe in nature
False
### Peripheral concepts
Candidate provenance, offline/live distinction, review gates, archive-only work notes.
### Hardness Lvl
3
