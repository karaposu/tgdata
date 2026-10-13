---
model: gpt-6-astra
effort: max
revision: 6
status: PROPOSED_PREBUILD_REQUIRED
---
# #17 — owned invocation completion and caller-retained data

**Source:** desc.md revision5 and the completed public-outcome ownership inquiry.
**Subject:** product a63099e on feature head f1cae2c; dev2ddb852 is already integrated
and was verified unchanged on GitHub in this turn. This is a new plan, not a patch to
rejected plan revision5 (preserved as step_by_step_impl_plan_r5.md).
**Current authorization:** new plan, fresh in-session critic-d, selected mitigation
fold, and full combined prebuild. Production implementation and live work are later.
Exactly two PR reviews are rejected; the task is not PARKED. No subagent delegation.

### What is the task

Complete the existing-access account pool without treating the caller's Task as the
library's lifetime or its cancellation exception as the only data carrier. The caller
must keep actual complete records through normal async cancellation composition,
while pool shutdown waits only for owned work, preserves native cleanup, and leaves
quota, permission and progress receipts governed by their existing records.

### Huge Hard Blockers

#### Planning Blockers

None OPEN. Inherited public-ownership question is **CLOSED at contract level** by the
new finding: a task-wide non-consuming join still waits for application continuation,
and exception attributes still lose data under shield/gather without close. Independent
completion and a caller-retained data destination are required. Actual candidate
composition remains a behavioural premise for P0, not an assumption marked confirmed.

The data destination and progress transport can be specified from the actual code:
BatchEngine owns a list containing only validated complete records; AccountPool owns
source/account settlement; SyncEngine/BackfillEngine own caller-scoped publication.
No inaccessible service fact or human-only design choice prevents writing the steps.
Native Python3.7 behaviour is not inferred from grammar checks. The proposed runtime
uses 3.7-era asyncio/contextmanager/dataclass APIs; only installed3.11.10 is executable
here, so native3.7 qualification remains an explicitly unclaimed compatibility limit.

#### Execution Blockers

**E1 — OPEN, inherited from desc.md:** two-account live qualification needs two approved
logged-in accounts, a shared readable group and their existing bounded allowance.
**Who:** maintainer supplies/approves resources. **Blocks:** step7 only. The user chose
one-account/offline-first; no login, join or allowance reset in P0 or this task.

### How this implementation moves toward desired state

Use two small owners for two different spans. A private invocation record tracks when
exclusive pool source/control work ends; its caller Task is only a stop address. A
public PoolReadCapture holds one caller-owned read observation through the longer
public call, including daily/backfill publication. It does not own Tasks or perform
I/O. Keep existing component outcome capture, provider boundaries and retirement.

Transport the data writer explicitly through private parameters. Do not add a global
ContextVar result registry, use health diagnostics for payloads, or retain a callback.
The four data-producing AccountPool entry points require `capture=`. Ordinary TgData
APIs and state-only pool operations keep their signatures. The pool's injected internal
batch reader receives the already-bound private writer; it never allocates/rebinds a
public capture for the inner read. Shared engines receive an opt-in private parameter
whose absence preserves existing ordinary-client behavior.

### High-Level Summary

| Step | Description | Expected Output |
|---|---|---|
| P0 | Full isolated candidate composition before any production step | One qualifying report, hashes, raw logs and negative controls |
| 1 | Define caller-owned data capture and immutable snapshots | Explicit one-shot public data destination with bounded retention |
| 2 | Separate exclusive invocation completion from caller Task lifetime | Close joins only owned completion, with retained native retirement |
| 3 | Retain complete records at the source boundary | Running capture sees actual prefix before subsequent source/store awaits |
| 4 | Wire canonical raw and progress public calls | One capture per public call, local replay and independent publication lifetime |
| 5 | Migrate docs/examples and permanent adversarial tests | Public calling pattern and preserved historical regression expectations |
| 6 | Verify final implementation and commit separately | Full offline evidence and exact comparison with the qualified candidate |
| 7 | Run live two-account gate when E1 is satisfied | Real account/access/proxy/failover evidence, without overstating offline proof |

## Decisions the implementation must preserve

### Public data shape and use

New `tgdata/pool_result.py`, exported from tgdata.__init__:

```python
capture = PoolReadCapture()             # no I/O, no task
try:
    result = await pool.read(chat_id, capture=capture, after_id=cursor, limit=200)
finally:
    observation = capture.snapshot()    # synchronous, nondestructive, no I/O
```

`PoolReadSnapshot` is an immutable value with `state`, `batch`, `account_id`,
`error_type`, `read_error_type`. States: `unbound`, `running`, `succeeded`, `failed`,
`cancelled`. `batch` is None or an immutable MessageBatch. `account_id` denotes the
verified source that produced retained records, not a guessed identity from session
names; replay has no newly verified account, so it is None. Error fields are validated
ASCII type names up to128 characters or a fixed fallback; never exception messages,
instances, traceback chains, Tasks or credentials. `read_error_type` records the source
failure separately from a later public error. Existing exception return semantics are
kept as convenience; the capture is authoritative for in-memory data availability.

The public object exposes only constructor/snapshot. Use private state plus a private
writer; callers cannot assign public state/batch fields. Require exact PoolReadCapture
rather than an arbitrary callback/duck-typed object. A local binding context manager
marks it running once on accepted coroutine entry, before argument-dependent I/O.
Invalid/missing/reused captures refuse before I/O; reuse leaves the original untouched.
Concurrent attempts to bind the same capture have one winner, never two writers.
A Task cancelled before coroutine entry leaves it unbound. Cancellation queued at entry
may bind and then cancel at the existing pre-I/O checkpoint; neither starts store/source
I/O. A bound capture is never reset/reused, including after validation failure.

`snapshot()` during execution exposes only complete validated records, always with
`stop_reason='interrupted'`; zero available records means batch=None. Successful final
return preserves its actual full/end/limit batch (including a real empty batch). Empty
sync/wait/control returns do not invent a batch; a known source empty-end observation
may remain a real source fact, but provides no receipt. Failure/cancellation freezes
only the interrupted complete prefix. No final snapshot is later downgraded by close.
Snapshots are copies in meaning: later capture changes cannot mutate an earlier one.

Avoid rebuilding/copying the entire prefix for each message. The private writer can
retain BatchEngine's internal complete-record list plus its validated chat/cursor/mode
while that one source runs. This list contains only validated plain records, no SDK
objects, and is not exposed publicly. `snapshot()` materializes an immutable batch on
demand, with no await; finalization seals a single MessageBatch and releases the list.
The shared source list may grow only after validation/media completion. A later
no-prefix failover may install a new empty record list; once nonempty data exists,
no further account is eligible for this call. Never lose a nonempty prefix because a
later error carries None/empty data. Existing10,000-message bounds apply; no new universal
byte limit or lossless process-crash guarantee. Caller-retained older snapshots remain
caller-owned memory. No public discard protocol: release references to release data.

### Private invocation lifetime

An `_Invocation` in pool_lifecycle.py contains caller stop address and a private
normal-result completion Future. AccountPool has one `_active_invocation` reference.
Keep `_active_task` as a derived private read-only compatibility property for existing
invariant probes; it is not a second mutable source of truth.

`_operation()` establishes the invocation only after scope/closed/busy refusal. Its
finally exits the live scope, clears the exact active slot, clears the record's caller
reference and signals completion, without an intervening await. All retained source
and provider tasks already settle before this finally under the existing ownership
helpers. Never turn a source/control invocation into the whole public progress call.

`close()` sets closed/closing as before and retains its cleanup worker. That worker
stops only an invocation still equal to the active record and not completed; perform
the identity check and cancel synchronously. Await the record's completion Future,
never the caller Task. Then retire all native clients with existing quarantine/error
rules. Multiple close/reentry behavior remains unchanged. A completed/stale invocation
is harmless and cannot cancel later application code. No waiter consumes public data.

### Explicit transport, including source-free progress

Public AccountPool.read/get_message_batch/sync_group/prepare_backfill require capture.
Use one binding context at the outer public boundary. Move raw routing body into a
private `_read(..., _capture)`; its existing admission, selection, classification,
settlement and failover rules remain. Public get_message_batch calls that private
body directly, not public read. Provide a private bounded-reader adapter for engines.

AccountPool's SyncEngine and `_new_backfill_engine` bind to the private adapter.
Add opt-in `_capture=None` to shared SyncEngine.prepare and BackfillEngine.prepare;
forward it to the configured reader only when supplied. Ordinary TgData creates no
capture and passes no extra reader keyword. State-only methods retain their signatures.
No shared ProgressFacade signature change is necessary: override only the two
pool-specific public preparation methods and its engine factory.

`_OwnedSource.run(..., _capture=None)` forwards the private writer to BatchEngine.
BatchEngine.fetch_batch's private parameter attaches the local complete-record list
after actual identity/entity resolution, before awaiting more source work. Capture only
records appended after complete media preparation and validation. Record source
completion/error in the writer before monitor finalization; later secondary failures
cannot obscure known data. No capturing from an invented batch or reread.

For daily/backfill replay, offer the actual validated pending batch after media checks
and before returning. For newly obtained batches, preserve running interrupted data
through account settlement and group publication. Only outer public-call exit marks the
capture terminal; inner source completion does not. Publication may remain active after
pool close retires clients. Do not send a synthetic ack or clear an uncertain token from
capture state. Native helper/store/receipt schemas and reconciliation stay unchanged.

## Mandatory combined prebuild P0 — before step1

**Location:** new `probes/outcome/` and `evidence/outcome/` in this work folder. Preserve
all older inquiry/restart/review scripts and exact failed outputs. Export tracked code,
docs and examples at f1cae2c to a fresh owned /private/tmp directory with no .git. It
already contains dev2ddb852. Record source-tree/SDK/Python/hash manifests. Apply the
candidate only in that export; do not change the branch's production files.

The candidate must implement the complete interaction in steps1–4, including early
record retention and required capture arguments, not the inquiry's exit-only adapter.
Use actual Telethon1.45.0 client/iterator/native disconnect, ReadBudget, SQLite account
and progress stores, batch serialization, sync and backfill engines. Synthetic wire
controls replies and fault wrappers control timing but delegate actual writes. No
helper supplies a manufactured result, receipt, allowance or client-completion flag.

Migrate existing pool fixture calls in the export to pass fresh captures without
changing existing assertions. New qualification cases retain and inspect those captures
explicitly. Compare/assert the old test oracles remain intact. No default capture is
silently added to the actual API. Run the whole combined command on one candidate/hash
set; targeted passes or concatenated results from different candidates cannot pass P0.

Coverage groups (individual histories parameterize each group):

- Binding/state: all four APIs, missing/wrong type, same/different-pool reuse, concurrent
  same-capture calls, prestart/queued stop, validation errors, source-free empty/wait,
  successful and failing finalization, immutable old/final snapshots, bounded diagnostics,
  capture retention after GC/close and no retained Task/client/traceback graph.
- Early visibility: actual first page100 then blocked second RPC; complete prior media
  records then blocked/failing next download; completed source held in monitor cleanup;
  pool settlement held before/after actual commit; progress publication held; snapshot
  before release must show all and only actual complete records as interrupted data.
- Public composition: raw/daily/backfill plus batch-only adapter; direct Task wait,
  wait-for timeout, shield, gather return_exceptions, first/late/repeated observers;
  read-first/close-first plus repeated reader/closer cancellation. Prefix1 or100 must
  persist in the explicit recipient while the actual public Task remains cancelled.
- Lifetime: application catches tgdata cancellation then waits for close/unrelated
  cleanup; close must retire without waiting for that continuation. Internal source/
  store/native cleanup remains held until actual completion. Stale completion/stop
  cannot cancel unrelated work or a subsequent operation. Positive no-close cases remain.
- Authoritative effects: genuine and provider-owned cancellation at account/progress
  load/admission/settlement/publication/ack/recovery, before/after actual commit; paired
  account+progress faults; exact receipts versus interrupted hashes; no rollback,
  synthetic receipt, refunded charge, shortened wait or second source after a prefix.
- Source-free daily/backfill replay and ack after close with removed credentials and
  poisoned pool-state/quota access; capture finalization follows the public prepare,
  not pool source closure. Receipt/cursor assertions remain independently observed.
- All48 existing lifecycle groups, full test31 pool suite, worker37+38, and complete
  supported offline12–19/22–39 suites plus the three offline demos. This wider combined
  run protects the shared optional parameter seams and ordinary TgData/#7/#10 behavior.
  Explicit legacy live skips are excluded from executed counts, never marked as tests.

Each process has a parent watchdog and per-case bounds where meaningful. If forced
termination is needed, report FAIL; never equate a timeout/cancelled waiter with actual
quiescence. Record exact SDK requests, available records, signal/Task state, source/
provider termination, native retirement, quota and stored token/wait/pending/cursor
separately. Compile and check new runtime modules against3.7 grammar, not a native3.7
claim. Assert candidate hashes unchanged during execution and branch runtime unchanged.

**PASS:** every required group, regression suite and demo on that single candidate
passes with the expected real observations and no watchdog. **FAIL:** any unresolved
semantic mismatch in data, lifetime, authority or compatibility. Preserve evidence;
stop before implementation and apply task-impl's failed-experiment procedure. A local
syntax/import/fixture wiring error may be corrected only if it changes no design or
expected semantic outcome; record it and rerun the full combined gate. Do not replace
expected data or silently alter the design to make a test pass.

## Step 1 — caller-retained data destination

### Proposed changes
Implement PoolReadCapture/PoolReadSnapshot and the private writer/binding context in
`tgdata/pool_result.py`; export only the two public values in `tgdata/__init__.py`.
Implement the state, snapshot, bounded-error, exact-type, one-shot and reference-release
rules above. Keep the writer separate from the public value, with no user callback.
### Output
One explicit destination survives wrapper cancellation and has a documented lifecycle.
### Safe in nature
False — introduces a required public calling contract on the unmerged pool.
### Peripheral concepts
MessageBatch immutability and validation, error provenance, caller-owned memory.
### Hardness Lvl
4/5.

## Step 2 — library invocation completion

### Proposed changes
Add private _Invocation to pool_lifecycle.py; replace the mutable task slot in
account_pool.py with the exact invocation record and derived task property. Change
_operation and close only as specified. Preserve retained cleanup/reentry/quarantine.
### Output
Shutdown stops/joins actual library work without awaiting the caller's whole Task.
### Safe in nature
False — changes cancellation and lifetime coordination.
### Peripheral concepts
Provider scopes, repeated cancellation, persistent clients, application continuation.
### Hardness Lvl
4/5.

## Step 3 — complete source records available before later awaits

### Proposed changes
Add the opt-in private writer argument in batch_engine.py and pool_source.py. Attach
the real complete-record buffer after identity/entity resolution; never expose its
mutable list or an incomplete media record. Record body value/error before monitor
exit. Use the existing source outcome and cancellation helpers unchanged otherwise.
### Output
Actual running data is retrievable through later source, monitor and account-store work.
### Safe in nature
False — shared batch code changes, with opt-in behavior absent for ordinary callers.
### Peripheral concepts
Media completion, MessageBatch hashing, SDK pagination, source error precedence.
### Hardness Lvl
4/5.

## Step 4 — outer public calls and progress transport

### Proposed changes
Bind captures at all four public AccountPool data entry points; move routing into the
private raw reader and route engine adapters directly to it. Pass the existing private
writer through SyncEngine/BackfillEngine.prepare and pool-only engine construction.
Capture validated replay results without source access. Terminal state is set only on
the outer call's exit; existing store/provider/receipt semantics remain authoritative.
### Output
One capture spans exactly one public read/prepare, including local replay and publication.
### Safe in nature
False — changes pool public signatures and shared optional engine transport.
### Peripheral concepts
ProgressFacade, scope expiry, pending replay, durable acknowledgment, local media checks.
### Hardness Lvl
5/5.

## Step 5 — permanent qualification and user-facing contract

### Proposed changes
Promote P0 public-ownership cases to `tgdata/smoke_tests/test_40_pool_outcomes.py` and
migrate pool callers in test31/test39/pool_storage_cases and examples/account_pool.py.
Retain previous oracles; add assertions through the explicit recipient. Update README,
docs/account_pool.md and smoke-test README with capture use, wrapper-safe retrieval,
early/final snapshot meanings, required one-shot binding, normal cancellation, memory
limits and data-versus-receipt rules. Inspect actual doc filenames before editing.
### Output
A canonical working example and permanent tests protect all ownership boundaries.
### Safe in nature
False — fixtures/examples/public call sites migrate with the new pool contract.
### Peripheral concepts
Documentation migration, package exports, raw/daily/backfill user workflows.
### Hardness Lvl
4/5.

## Step 6 — verify and commit the implementation

### Proposed changes
Run compile/grammar, complete supported offline suites and demos on the integrated
branch; compare runtime with the passing P0 candidate, accounting for only deliberate
packaging/test/doc organization differences. Commit production/tests/public docs apart
from work/inquiry evidence. Update #17 honestly, keep PR26 draft until renewed merge
check and fresh PR critique pass. Any eventual merge needs user's go-ahead and excludes
work/inquiry/archaeology docs while preserving the feature branch as archive.
### Output
Auditable implementation verification; no accidental merge or claimed live readiness.
### Safe in nature
True — verification/recording after functional changes; it does not deploy or merge.
### Peripheral concepts
Current dev, worker compatibility, source hashes, PR soundness gates.
### Hardness Lvl
3/5.

## Step 7 — live qualification [E1 OPEN]

### Proposed changes
With confirmed resources/authorization, run bounded read-only failover observations
using two approved accounts and one shared group, sharing their real read allowances.
Verify expected identity/proxy/access/history assumptions; do not manufacture bans or
resets. Preserve differences in visible history and make no union-history guarantee.
### Output
Separate actual service qualification with explicit resource/visibility limits.
### Safe in nature
False — contacts real Telegram and consumes approved allowance.
### Peripheral concepts
Account inventory, proxy identity, live read budget and visibility.
### Hardness Lvl
3/5.
