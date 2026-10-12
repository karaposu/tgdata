---
model: gpt-6-astra
effort: max
---
# Implementation plan — #10 reading worker, revision 4

**Critic folded:** 2026-10-12 — 0 additional mitigations (0 implementation steps
changed, 0 added). The two robust PR remedies already encoded in revision3 remain.
**Review state: critique/fold complete; combined Step1 prebuild PASSED;
revision4 implementation and verification complete at product `d32abcd`.** The REORDER experiment in critic.md passed
82 groups across67 controlled subprocesses on2026-10-12. See `prebuild-result.md`.
Its frozen candidate at2cc9995, not the fold marker, supplies the qualification.
Steps2–5 are implemented and verified:631 actual passes /3 live skips across24
suites, plus packaging/examples. Step6 records separate product/work commits and
same-branch publication. See `implementation_r4.md` and `verification_r4.md`; renewed
merge check and fresh PR critique remain pending.

Revision3 at9ce9ae3 was reviewed under the new dynamic prompt at1d6cac7, with
Phase2 at08ee0f2 and Phase3 selection atd49f8a0 in critic.md. No additional
High/Medium/Low plan risks were found. The22 targeted review histories passed,
but are explicitly narrower than the full combined matrix required by Step1.
The six implementation steps and their contracts below are unchanged by this fold.

Revision3 is retained exactly in `step_by_step_impl_plan_r3.md`; revision2 in
`step_by_step_impl_plan_r2.md`. The first planning critic/prompt are `critic_r1.md`
and `dynamic_critic_prompt_r1.md`. `pr-critic.md` remains the rejected first PR
review (837d06f, selections8322827), whose two robust remedies drove the re-plan.
The current critic.md belongs to revision3, not to the first planning cycle.

Base dev remains68f6bbd. Original product6ee146c is revised by `d32abcd`; PR27
remains draft pending renewed gates. The first PR critique remains rejected.
This is the first rejected PR round, so re-planning is permitted. A second rejected
round requires returning to description/traverse under7.4, not another patch cycle.
Current review/fold metadata at2026-10-12T07:38:03.247Z verifies GPT-6 Astra/max.
Same warmed session; no delegation. The original feature-heavy scope remains appropriate.

### What is the task

Complete a small caller-managed process that performs explicitly assigned Telegram
read/lookup/access/join jobs, preserves their results and account ownership, and
can be stopped without depending on unrelated activity. Its serialized diagnostics
must carry only recognized safe metadata. The application retains scheduling,
account assignment, message storage, acknowledgment and uncertain-result recovery.
The first implementation stands; this cycle redefines and qualifies the process
boundary that its earlier tests failed to establish.

### Huge Hard Blockers

#### Planning Blockers

None identified. The two rejected premises are understood and have reachable
mechanisms, rather than human decisions disguised as blockers:

- Cancellation marks a Task but need not wake its selector. Python3.11 Runner's
  native SIGINT handling marks cancellation then uses call_soon_threadsafe to wake
  the loop. A planning-only candidate using that sequence passed both real quiet
  worker subprocesses with their60-second selector waits and no polling helper.
- AuthRequiredError.reason intentionally retains unknown SDK text for Python
  callers. A worker-local frozen set of recognized names, derived from the pinned
  SDK authentication classes plus existing banned names, removed unknown401/406
  text while preserving known authentication metadata in six actual SDK/Worker runs.

Evidence: `probes/revision3_feasibility.py/.txt`, compiled candidates in memory only.
The script also showed that queuing task.cancel can let an already-ready Task step
first; marking cancellation immediately and waking separately did not. These two
ordering controls are actual asyncio scheduling observations, not SDK source tests.
The first probe bootstrap overmatched an indented source line and exited before
ready; `revision3_feasibility-bootstrap.txt` retains it. Exact-line matching fixed
the experiment, without changing product code or expectations.

These observations establish feasibility of the mechanisms. They do **not** claim
the combined bootstrap/job/output/finalization contract has passed. The complete
candidate prebuild is Step1, before any runtime edit. Its failure stops this plan;
no assumption converts a failing experiment into permission to implement.

Inherited desc boundaries remain: caller-owned pipes and exclusive sessions;
serial JSON lines is the stated engineering choice after the unanswered optional
transport question. There is no new transport or account-ownership decision to ask.

#### Execution Blockers

None for these six offline steps. Fresh plan critique/fold and Step1 qualification
are local workflow gates, not out-of-reach external blockers. Live account/group
permission, exclusive sessions and bounded existing allowances are external
preconditions for later deployment qualification; that work is outside this plan.
No live login/read/join, existing policy reset, merge or deployment is authorized.

### How this implementation moves toward desired state

Treat process stopping and public diagnostics as two complete boundary contracts,
then qualify their composition before integrating it. Reuse the accepted source
ownership, cleanup helper, budgets, resolver and raw writer. The stop owner must
both prevent new work and make existing work progress toward cleanup; the projector
must distinguish recognized metadata from name-shaped text. Permanent tests remove
the incidental timer that concealed the failure and exercise every entry/exit phase.
This cycle does not reconstruct routing, SDK operations or a generic supervisor.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Qualify the complete candidate boundary before product edits | Actual-process/SDK prebuild with explicit pass/fail evidence |
| 2 | Give the process one stop and finalization policy | No new admission, immediate cancellation marking, loop wake-up and retained cleanup |
| 3 | Project recognized authentication diagnostics | Unknown text omitted; known reasons and flags preserved |
| 4 | Install permanent boundary regressions | Timer-free stop tests and decoded authentication-error controls |
| 5 | Update public contract and verify the integrated product | Full offline/package/example evidence with honest limits |
| 6 | Commit and publish the revised implementation record | Separate product/work commits, same draft PR ready for renewed gates |

## Re-planning decisions and findings answered

**R1 — stop signals:** the missing concept was progress ownership, not another
timeout. Marking cancellation, waking its loop and retaining cleanup are three
obligations of the same process owner. Step1 qualifies them across all phases;
Step2 implements that policy; Step4 removes masking test assistance. Merely adding
a periodic timer, adopting asyncio.run as a new incompatible driver, or handling
signals only while the loop runs does not satisfy the contract.

**R2 — raw authentication reason:** a field name or identifier-shaped string is
not evidence of safe origin. Step1 qualifies the allowed diagnostic vocabulary;
Step3 makes projection explicit at the worker boundary; Step4 covers SDK wrapping.
The library's existing raw AuthRequiredError semantics remain available to its
Python callers. No new public error hierarchy or global diagnostic framework.

**Coupling / simplicity:** the process driver is the only owner of signal state,
the loop and protocol I/O. Worker.execute remains the only job executor. Keep a
small amount of private phase state in worker.py; a general state-machine class,
thread, polling task, transport abstraction and job queue are unnecessary. The
projection remains in worker_protocol.py. The two rejected boundaries are tested
together without moving source behavior into either one.

## Complete retained product contract

### Inventory, ownership and source

Keep Telethon exactly1.45.0 for the opt-in worker. WorkerAccount is the existing
frozen trusted value `(account_id, config_path, session_store=None, label=None)`;
optional positional arguments remain accepted, matching actual product rather
than silently reintroducing revision2's unused keyword-only sketch. Account IDs
are positive signed64 integers excluding bool. Paths exist and labels are bounded;
credentials/config paths are excluded from repr/diagnostics.

`Worker(accounts, *, worker_id, read_budget, join_budget=None)` holds existing
TgData facades configured for one session each, no interactive login, fixed health
collector and no persistent client/pool. Every operation uses the merged expected-
account proof, including later budget admission. Stale cached identity is not
authority. No hidden login, join, retry, routing or allowance setup.

Keep the CLI/module and trusted `serve` bootstrap in a dedicated main-thread
process. The manifest has version, worker_id, existing read_budget and accounts;
optional join_budget. Each account names its decimal-string ID, config_path and
optional label. Existing limits remain:1 MiB manifest,1000 accounts, empty inventory
allowed. Manifest paths are relative to its directory; file sessions retain the
documented pinned cwd-relative names, and stores retain opaque keys. Duplicate
IDs/config paths/known session addresses refuse locally. Exclusive cross-process
ownership remains the caller's duty. Ready is local configuration, not health proof.

All accounts require existing ReadBudget policies. JoinBudget is optional, reopened
with create=False; missing join configuration refuses before authentication, and
the existing per-account policy controls actual mutations. No worker configure/reset.
Normal clock/schema/expiry bookkeeping remains ledger-owned.

Read jobs retain bounded group parsing/resolution, actual owned health and
BatchEngine composition. Never scan dialogs/contacts to resolve a missing private
channel hash, nor join an invite preview. Other library BatchEngine consumers keep
their unchanged default resolution. Existing lookup/access/join statuses remain
qualified; membership is not readability. Ordinary source failures retain valid
partial MessageBatch documents and real charges. MAX_MESSAGE_ID shortcuts do not
invent successful group-access evidence. The private cleanup receipt remains
sticky and result-preserving; failed cleanup prevents another source job.

### Wire and delivery

Retain version1 strict UTF-8 JSON lines, LF/CRLF,16 KiB requests, duplicate/unknown-
key/type validation and one job at a time. Envelope fields remain version,
request_id, account_id, operation, params. IDs1..2^53-1 strictly increase per process;
a recognized fresh ID is consumed before later argument refusal. They are not
durable idempotency tokens. Malformed input must not open a client.

The four verbs remain read_batch, lookup_group, check_group_access and join_group.
Reads accept supported group_id, decimal after_id0..MAX_MESSAGE_ID (default0),
integer limit1..1000 (default200) and paired aware start/end dates under the existing
fixed-window contract. Other verbs accept target only. Media stays reference-only;
jobs carry no arbitrary output path or backend/credential choice.

Ready, correlated health and terminal result frames keep their existing shape,
including worker/instance/request/account identities, ok, data/error, partial_result,
health_dropped and worker_stopping. Preserve exact decimal identifiers and unchanged
MessageBatch hashes; counts/booleans retain types. Collection stays256 events per
job and8 KiB per event, with explicit drops; frame encoding stays64 MiB and precedes
all publication. Serialization/size failure produces bounded delivery_failed,
safe source metadata and partial_omitted:true, then stops. Unknown/partial output
never implies a source rollback, unspent budget or safe automatic join retry.

### One process stop policy [answers PR-R1]

The first SIGINT/SIGTERM owns the stop reason. It monotonically prevents new job
admission and any later SDK operation from a queued-but-unstarted job. A repeated
signal must not send another cancellation into retained cleanup. Use the existing
Worker.stopping admission predicate as appropriate; do not add a competing job flag.

| Phase at first signal | Required behavior |
|---|---|
| Synchronous startup / ready / waiting for input / publishing output | Interrupt the blocking operation through the private stop path; freeze admission |
| Job has been scheduled but not started | Freeze admission, cancel it before its body can step, settle it without a source call |
| Active job, including its owned native disconnect | Mark its Task cancelled once in the owning main thread, then wake the loop; retain the existing cleanup waiter |
| Completed job before/during reply | Permit loss/truncation under existing unknown-receipt semantics; no successor job or output retry |
| Final process settlement | Record exit reason and wake a live loop if needed; do not inject a stop exception or extra cancellation that abandons settlement |
| Closed loop / restored handlers | No scheduling on a closed loop; the worker's handler ownership has ended |

For active cancellation prefer the proven sequence `active.cancel()` followed by
`loop.call_soon_threadsafe(noop)`, with actual live-loop/phase guards. Do not merely
queue active.cancel behind already-ready job work: the planning control observed
that work stepping first. This is main-thread signal ownership, not an invitation
to call Task.cancel from arbitrary threads. Keep signal.signal's blocking-I/O
interruption behavior; a loop-only add_signal_handler would leave idle read/write
outside the loop unhandled. No private self-pipe API or takeover of a foreign
signal wakeup fd is needed when the public wake-capable loop call suffices.

Task publication and cleanup are part of this policy: a signal may arrive between
Task creation and storing its reference. Freeze worker admission before any final
event-loop turn; find/cancel/settle any created unstarted job before running other
shutdown coroutines. Never start a job merely as a side effect of draining the loop.
Use the dedicated loop's ownership to account for tasks; do not cancel another
application's loop. Test the transition deterministically at the real creation
boundary. This is a contract to qualify in Step1, not a claim that the narrow
planning candidate already handles every such interleaving.

After the owned job has settled, retire notifications/facades and remaining SDK
tasks, shut down async generators and close the loop. Signal behavior during this
phase must preserve that work. Keep the original source result/failure and cleanup
receipt; teardown diagnostics do not overwrite them. Always restore owned signal
handlers and logging state. No new final output attempt, buffered flush, source
retry, forced cleanup deadline or generic supervisor. A supervisor's hard kill
still means uncertain completion; waiting for native cleanup is still permitted.

Exit meanings remain0 normal EOF,2 startup/fatal input,3 unsafe cleanup/delivery/
output, or128+the first stop signal. Per-job source refusal alone is not process
failure. A signal must make cancellation progress independently of SDK timers;
this is not a promise of a subsecond end-to-end cleanup deadline.

### Diagnostic vocabulary [answers PR-R2]

Classify by existing exception types and keep category/type plus recognized bounded
metadata. For authentication, emit reason only when it belongs to a frozen set of
canonical names from Telethon1.45.0 classes accepted by the existing authentication
translation (UnauthorizedError/AuthKeyError), plus the library's existing banned
names. Reuse the SDK name table; no arbitrary .message, str/repr, custom registration
or regex match expands the set. The planning candidate measured this20-name set.

Unknown reasons, absent values and malformed metadata omit the optional reason;
do not replace the whole failure or erase valid first_login/banned flags. Known
AUTH_KEY_UNREGISTERED, SESSION_REVOKED and USER_DEACTIVATED_BAN retain their meaning.
An unknown code401/406 string identical to a known canonical name is safe as that
fixed vocabulary value; this does not claim stronger source provenance or create
new recovery/authentication actions. The contract is bounded publication, not a
new classification engine. A future SDK version requires explicit qualification.

Generic RPC type/code/known-name/wait projection and health-event sanitization keep
their existing policies; neither is relaxed to match the auth branch. Metadata
access faults remain secondary and must not replace the primary source outcome.
Apply this same projector to terminal errors, source_error in delivery failures and
safe fatal/startup diagnostics. Message bodies/group data/intended labels are still
application data; do not claim all protocol content is safe to publish publicly.

## Step 1 — Qualify the combined boundary before product edits [PR-R1, PR-R2]

**Completed:** full combined prebuild PASS on2026-10-12,82 groups/67 subprocesses.
The two candidate snapshots and source fingerprints were frozen at2cc9995; product
files remain unchanged. `prebuild-result.md` maps every requirement below to evidence.

### Proposed changes

After the fresh plan critique and fold, create `probes/revision3_prebuild.py` (or
the next reviewed revision name) using temporary/in-memory candidate code derived
from the exact current product. No runtime file is edited to make the experiment
pass. Use actual Worker, Telethon1.45.0, SQLite, OS pipes and the real selector.
Synthetic transport may supply RPC replies, but must not supply stop, cleanup,
budget, ownership or serialization behavior. Retain normal and adverse controls.

Mandatory matrix before Step2/3:

- Quiet active request under SIGINT and SIGTERM: selector parked with a long SDK
  timer; no child polling/helper timer; cancellation reaches actual native cleanup
  without unrelated wake-up. Queued next job performs no source work.
- Held native disconnect for both signals, repeated signals and caller cancellation:
  use a parent-driven pipe/event to release it after observing cleanup entry, not
  a periodic file watcher. The child remains alive until release; charges remain.
- Signal at job creation/publication and before the task's first step: no client,
  lookup/history/join request or claim; created tasks are settled without warnings.
- First/repeated signal while finalization is deliberately held: preserve settlement
  and handler/logging restoration; no closed-loop scheduling or pending-task stderr.
- Idle input, startup refusal, completed reply/EOF, broken stdout and output
  backpressure: preserve exits0/2/3/130/143, no drain requirement/final flush or second
  source. SDK cleanup failure keeps its known result and sticky stop.
- Decode unknown401/406, ordinary403 and the three known auth controls through the
  actual SDK and real worker operations. Unknown sentinel absent from serialized
  errors and stderr; known fields retained, zero group traffic/charges on auth failure.
  Exercise the shared projection at bounded delivery-error/fatal call sites as well.

Use parent watchdogs, trace actual requests/cleanup and inspect remaining tasks;
do not infer cleanup from process exit alone. The parent may poll trace files;
the child must not receive progress assistance before the stop it is qualifying.

**Gate:** all required observations pass before any product edits. A candidate
failure is not patched around in the implementation. Resolve the mechanism and
revise this plan/experiment as needed; if its architecture cannot meet the contract,
stop for description/traverse work. The earlier10 feasibility observations are
evidence inputs, not a substitute or a pre-ticked PASS for this combined matrix.

### Output

Committed candidate/source fingerprint, complete execution log and explicit
PASS/FAIL comparison with this matrix, before runtime implementation.

### Safe in nature
True — owned offline experiments and work artifacts only.
### Peripheral concepts
OS signals, asyncio task/selector scheduling, SDK shielded cleanup, wrapper metadata, pipe uncertainty.
### Hardness Lvl
5

## Step 2 — Implement the single process stop owner [PR-R1]

### Proposed changes

Rework the signal/job/teardown region of `tgdata/worker.py` around the proven phase
contract. Keep state private and small: first stop reason, actual job task/loop,
and explicit settlement phase. First stop freezes admission, immediately marks an
active job cancelled and wakes its loop. Synchronous input/output still interrupts.
Publish and retire task ownership deliberately, checking the creation boundary;
settle any interrupted unstarted task before shutdown can run it. During final
settlement, signals record/wake without abandoning cleanup. Restore handlers/logging
and avoid scheduling on a closed loop on every exit path.

Keep raw output/write-all, pre-encoded frames, the existing one-job executor,
sanitized diagnostics and no teardown flush. Preserve original exceptions/results
and cancellation semantics; do not weaken `_disconnect_owned`, invent a timeout,
or modify SDK retry settings. `worker_engine.py` already has the stopping predicate;
reuse it, with no new source API or ownership logic. Any necessary behavioral change
outside these stated worker surfaces requires revisiting the plan rather than
quietly expanding this step.

### Output

Worker process with the qualified stop, task publication and final settlement policy.

### Safe in nature
False — process-wide signals and source lifetime are delicate existing behavior.
### Peripheral concepts
Task publication, event-loop wake-up, admission, notification retirement, raw stdout, exception precedence.
### Hardness Lvl
5

## Step 3 — Enforce recognized diagnostic publication [PR-R2]

### Proposed changes

In `tgdata/worker_protocol.py`, build the small immutable canonical-auth name set
from the pinned SDK metadata and existing banned names, and use it in describe_error.
Omit unknown reason text; retain type/category and validated flags. Keep safe metadata
inspection and the generic RPC/health policies. No changes to ConnectionEngine's
AuthRequiredError construction, health.telegram_error_name or other library callers.
Verify that terminal, delivery-failure source_error and fatal diagnostics share the
same rule. Do not add a public typed-error migration or sanitize ordinary message data.

### Output

Known authentication metadata survives every worker diagnostic path; unknown text
cannot be promoted to a public reason merely because its spelling looks valid.

### Safe in nature
False — changes serialized worker errors, although ordinary library errors remain intact.
### Peripheral concepts
SDK class tables, AuthRequiredError wrapping, optional metadata, health and delivery-error projections.
### Hardness Lvl
3

## Step 4 — Install permanent source/process regressions [PR-R1, PR-R2]

### Proposed changes

Extend `test_37_worker.py` with SDK-decoded unknown/known authentication cases and
secondary projection paths; check byte absence of the sentinel, semantic flags,
original error category, actual cleanup and zero unauthorized source/claims.
Keep ordinary raw library reason available in a control; do not alter shared tests
to hide its intentional behavior. Exercise all four worker verbs at the auth boundary.

Extend `test_38_worker_process.py` with the qualified quiet-selector, creation,
finalization and repeated-signal cases. Replace its10 ms file-watcher assistance
with explicit pipe/event release for held cleanup. Retain and distinguish quiet
source versus held cleanup: one proves cancellation begins, the other proves it
is not abandoned. Use actual subprocesses and native SDK work; patch only transport
data or a named boundary pause/instrumentation. No test-only production flags.

Carry every important Step1 history into tests that have no dependency on devdocs,
Git or candidate source rewriting. Preserve existing39 worker groups and their
ordinary source/budget/batch/pipe coverage; count actual cases and skips accurately.

### Output

Portable permanent regressions that fail the rejected code and verify the rebuilt
product's process and diagnostic contracts without incidental progress helpers.

### Safe in nature
True — tests use synthetic data and own their processes/files.
### Peripheral concepts
Regression sensitivity, instrumentation versus supplied behavior, real TL errors, sockets forbidden, watchdogs.
### Hardness Lvl
5

## Step 5 — Document and verify the integrated worker

### Proposed changes

Update `docs/worker.md` and smoke-test README with first-stop/wake/cleanup semantics,
known versus omitted auth reasons, measured case counts and exact limitations.
Keep the public request/reply shapes, budget ownership and lost-reply rules. Inspect
README and `examples/reading_worker.py` against this contract; change only any actual
inconsistency. No new transport, destination storage or automatic job retry.

Run the new tests first, then all24 supported offline suites:12–19,22–30,32–38.
Use an intentionally missing config for12/13; permit test12's local loopback only
as needed, with its two live checks skipped. Keep live skips separate from passes.
Baseline was612 actual passes/3 live skips; new counts must be measured, not assumed.

Compile product/examples/setup and check Python3.7 grammar under Python3.11.10 /
Telethon1.45.0. Build/install from an export without Git/devdocs and test both module
and console entry points. Run worker/daily and new/restarted-backfill offline examples
(explicit --new for new retained backfill state). Recheck the complete product diff,
no work-folder imports, unchanged source foundations and no unrelated edits.

Record every failed check and correction. Small implementation slips may be fixed
and rerun; an architectural failure returns to planning. Do not weaken acceptance,
replace native behavior with a fake, or call synthetic evidence live qualification.

### Output

Updated public contract, exact integrated test totals and isolated package/example
evidence for the rebuilt product, with all limitations and corrections recorded.

### Safe in nature
False — integrated verification can reveal a broken design or compatibility change.
### Peripheral concepts
Process/SDK version qualification, legacy semantics, packaging, decoder precision, live/offline evidence.
### Hardness Lvl
4

## Step 6 — Commit and hand off the revised PR cycle

### Proposed changes

Commit code/tests/public docs separately from work notes/evidence. Preserve archived
revision2, planning critic r1 and rejected PR critique; record which current findings
were answered and the real prebuild/verification results. Push the same branch and
update #10/PR27 from committed artifacts. Keep the PR draft until the renewed checks
have actually passed; implemented remedies are not a fresh PR approval.

Next review remains merge check → fresh PR critique on the same PR, each committed
and posted. Archive the old gate records when writing new ones. If the second PR
round rejects, follow CONTRIBUTING7.4 back to desc/traverse. Merge requires the
maintainer's separate go-ahead, excludes work docs and keeps the branch as archive.
Preserve duncan, the original checkout/untracked files and other issues/worktrees.

### Output

One reviewable revised implementation, honest current-cycle issue/PR status and a
saved handoff for renewed gates; no merge or live deployment implied.

### Safe in nature
False — deliberate version-control and remote issue/PR publication.
### Peripheral concepts
Review provenance, rejection thresholds, archive paths, publication, merge authority.
### Hardness Lvl
2
