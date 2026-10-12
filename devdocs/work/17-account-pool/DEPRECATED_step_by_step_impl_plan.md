---
model: gpt-6-astra
effort: max
revision: 3
status: DEPRECATED_PREBUILD_FAILED
---
# DEPRECATED — #17 operation ownership, revision 3

**Do not implement.** The combined P0 experiment failed; see `prebuild.md`.
The failed source/storage cancellation premise requires a replacement plan.

Regenerated under CONTRIBUTING §7.4. Inputs: revised `desc.md` at79ecce7;
`pr-critic.md` (first rejected round, both Medium findings); archived original
`step_by_step_impl_plan_r2.md`/`critic_r1.md`; `retirement-rework/plan.md` and critic;
[foundation finding](../../inquiries/2026-10-12_19-42__17-account-pool-foundations/finding.md)
at ebbaaac. Product baseline71502e5/4854464; current dev2ddb852. This is a replacement
plan, not separate patches attached to the old blueprint. Fresh critic/fold pending.

### What is the task

Complete the existing-access account pool by making its source result, caller stop,
lifecycle authority, physical cleanup and health observations distinct. Preserve
the useful router, durable account state, existing budgets and delivery engines.
Remove arbitrary application observation work from the pool's source lifetime, and
prove the smaller contract before committing runtime changes.

### Huge Hard Blockers

#### Planning Blockers

None identified. The traverse closes the semantic choices; current code and reachable
probes establish the relevant SDK/state mechanisms. The combined candidate remains
to be measured by mandatory Gate P0 below; it is not claimed proven by separate
inquiry demonstrations. No unanswered human preference is substituted with a guess.

#### Execution Blockers

**E1 — OPEN, inherited.** The maintainer must supply/confirm two approved logged-in
accounts, shared readable group and bounded existing ledger allowance. Blocks Step7
only. User chose one account/offline first. No credential search, login or allowance
reset is authorized to manufacture this gate.

**Run boundary:** the present request authorizes re-plan/critic/fold and Gate P0.
Steps1–7 describe subsequent implementation/qualification; they do not run in this
preparation turn. This is a requested endpoint, not an unclosed planning blocker.

### How this implementation moves toward desired state

Keep selection, admission and settlement authority where they are. A small pool-only
collector captures safe plain health data; callers retrieve it locally and own its
processing. The source wrapper consistently uses its actual body completion, while
true caller cancellation remains an outer control signal. Pool-specific live scopes
reject detectable control reentry and expire after use. Persistent retirement retains
its existing cancellation/quarantine guarantees. The prebuild composes all of this
with real SDK/SQLite/progress behavior and the current-dev batch seam.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| P0, before all runtime steps | Freshly critique and exercise the complete candidate in an isolated current-dev integration | Evidence that the boundary holds, or a disqualifying result |
| 1 | Integrate current dev with both batch options | Worker functionality and pool prefix support coexist |
| 2 | Add passive bounded observations | Local drain API; application callbacks refused on AccountPool |
| 3 | Make source completion authoritative | All terminal paths preserve source facts and distinguish cancellation roles |
| 4 | Enforce permitted lifecycle dependencies | Detectable reentry refuses; external close and expired scopes work |
| 5 | Update product tests, docs and example | Explicit migration and a contract-level regression matrix |
| 6 | Verify and commit offline implementation | Full supported suites/demos/export checks and separate work notes |
| 7 | Qualify two actual accounts | Bounded approved live evidence, gated by E1 |

## Contract fixed by this plan

### Source outcome and stopping rules

Keep one private source-completion holder populated around the actual read/identity
body, before health finalization. Resolve it on every child terminal path. Observe
and retrieve the child's terminal exception to avoid orphan errors, but do not use
that exception as the source outcome when the body completed.

| Observation | Public consequence / account permission |
|---|---|
| Body completed with a batch | Return that exact batch through existing result APIs; ordinary settlement |
| Body completed with an error/prefix | Re-raise that same source error/prefix; normal exact-token settlement preserves its real wait/restriction |
| Outer caller cancelled while awaiting owned work | Retain stop/cleanup until finished; propagate caller cancellation; leave account attempt unresolved, no failover |
| Internal attempt timer expires before body completes | Retain child stop; PoolTimeoutError with complete interrupted prefix; existing timeout restriction and no-prefix-only failover |
| Internal timer expires after body completed | Preserve the completed source fact, not a fabricated transport timeout |
| Source child internally cancels without caller stop/timer and no completed body | Local private `_SourceInterrupted` (PoolStateError subtype), safe type-only message, optional completed prefix; leave exact account attempt unresolved and do not fail over |
| Secondary health finalization fails/cancels after body completed | Preserve the body completion; report capture failure is secondary |

Do not infer caller cancellation from `child.result()` raising CancelledError. Catch
caller cancellation only around the awaited ownership boundary/retained stop. Do not
require Task.cancelling(), uncancel() or other Python3.11-only runtime APIs. Keep the
current Python3.7 grammar/API compatibility claim separate from runtime3.11 testing.

Unexpected source cancellation is uncertainty, not a freshly granted cooldown. Add
only the private subtype needed to carry that distinction; no public result envelope.
At the beginning of `_settle`, before row mutation, refuse settlement for this subtype
by re-raising it. Existing ordinary-error prefix handling in daily/backfill can publish
its complete prefix while account permission stays unresolved. Caller cancellation
retains its existing no-prefix-promise contract.

### Passive observation API and limits

`AccountPool.drain_health_events()` is synchronous and returns a detached plain dict:
`{'events': [event, ...], 'dropped': int}`. Events retain the existing health fields
and safe account/group attribution. Return the captured-so-far events in capture
order, then reset events/byte count/drop count in the same non-awaiting call. No
client, store, active-operation or `_closing` predicate; usable before any read,
during work and close, and after closure or failed cleanup. It is not a completion
barrier, eligibility certificate, durable receipt or acknowledgment.

Keep the constructor keyword `health_callback=None` temporarily for harmless None
call sites; reject every non-None value with PoolConfigurationError naming the drain
migration before any client/storage work. Never accept and silently ignore a callback.
Ordinary TgData/#7/#10 callback contracts are unchanged.

A private `tgdata/pool_observation.py` owns a bounded collector and a pool-only
HealthMonitor adapter. Fixed limits:128 events,4096 encoded bytes per event,65536
encoded bytes total; dropped count saturates at2**63-1 and this is documented.
Drop incoming events on overflow, oversize, malformed input or failed capture; retain
already-buffered events. No retries, backpressure, persistent storage or consumer task.

Capture accepts only the known11 top-level health keys and3 account keys. Copy into
new exact-built-in dicts; only exact str/int/None scalar values are allowed, with
signed64 integer limits and per-string character prechecks at4096 before encoding.
Use compact sorted JSON with ensure_ascii=True/allow_nan=False for size accounting;
this bounds transient serialization too. Store owned detached plain values, not
exception objects, arbitrary repr/default hooks or live client references. Draining
transfers that list; later producer/caller mutation cannot change the other side.
Container overhead is bounded by event count and known schema; byte limits describe
encoded payloads, not a claim of exact process RSS.

The pool monitor reuses health classification/recovery but overrides delivery with
synchronous internal capture (async `_deliver` has no suspension) and overrides
`_deliver_now` similarly. It never calls the user callback, creates observer tasks
or invokes the legacy health-log mirror. Pool health-reporting failures increment
capture loss without logging arbitrary exception data. Bypass the ambient callback
recursion flag for this internal data path; it must not suppress a pool report merely
because an enclosing legacy callback is active. Normal SDK logging remains SDK logging.

### Control and provider roles

In `account_pool.py`, a private context scope records the pool and whether that
scope is still active. Wrap `_operation` and `_backend` invocation so direct/task-
descendant calls made while serving source/admin work or pool-store I/O inherit it.
`close()` checks for an active scope belonging to itself before mutating `_closed`
or `_closing`. Existing busy/closed guards continue to serialize source/admin work.

Expire scopes in finally and release their pool reference; restore ContextVar tokens.
Ignore inactive scopes and other pools. Keep the original retained close/retire work:
external close cancels/awaits the active reader, then attempts all client retirements;
repeated cancellation cannot release live work or certify successful retirement.

No guard claims to discover arbitrary pre-existing-task dependency graphs. Custom
pool/session providers must not call or await the same pool's lifecycle while serving
it, including through another task. Independent external controllers may close it;
applications may process drained reports and close it outside source work. No callback
program remains inside the supported pool source path to create the rejected cycle.

### Preserved responsibilities

No schema/version change to pool state, sessions, quota or MessageBatch/progress
receipts. Keep expected identity and actual ledger admission, state CAS uncertainty,
no-prefix failover, existing group/account restriction policy, credential reload,
retirement quarantine, source-free replay/ack/control and existing-access scope.
Read-only pool status remains source-free; its backend call still has a storage-only
role, without acquiring exclusive source-operation ownership.

## Gate P0 — Combined real-component prebuild before Step1

Fresh critic specifies the final pass/fail obligations. Build only a reversible
candidate under this work folder's `probes/`, importing actual runtime components
from an isolated export. Do not edit working-branch tgdata/docs/examples to make it
pass. Candidate code contains only the proposed source/observation/scope changes;
selection, budgets, CAS transitions and progress engines remain actual code.

Create the integration export from product71502e5 and dev2ddb852. Merge preview has
one conflict in batch_engine.py. Its union is the existing pool version of that file:
it already includes the worker's resolver and adds only the opt-in cancellation-prefix
behavior compared with dev. Record hashes/resolution; keep worker's connection/
account-operation cleanup receipts. No protected ref or real runtime checkout changes.

Use actual Telethon1.45.0 client request/pagination and native disconnect, synthetic
wire replies, real ReadBudget and real SQLite stores. Fault-only wrappers may delay
or fail an actual I/O/cleanup boundary; they cannot return a fabricated pool result,
charge, permission, prefix or receipt. Socket connect/connect_ex must be blocked.
All configs/keys/database files are synthetic in owned temporary directories.

Required combined histories:
1. Raw successful read and successful recovery observation; exact batch/identity/
   charge survive subsequent application observer cancellation and close.
2. Raw/daily/backfill100-record prefix plus FloodWait7200; same original source error,
   saved wait7200, actual charge200, no second source; progress publishes/replays/acks
   its prefix after close with no account/store/budget source dependency.
3. Ordinary completion and internal timeout after an actual source result with
   explicitly injected secondary finalization failure/cancellation; outcome retained.
4. Actual caller stop and repeated cancellation while the real child/finalizer or
   SDK disconnect is held; no replacement/read/release before that work finishes.
5. Internal source future cancellation with no caller requests; explicit local error,
   no failover, unresolved account token and retained complete prefix if present.
6. Direct/create_task/wait_for same-pool close from load/CAS provider; refusal before
   flags mutate. Positive controls: foreign pool, expired inherited scope and ordinary
   external close. Include read-only status backend to test scope coverage.
7. A pre-existing external closer triggered by application processing of drained
   reports after the read; no cycle and all clients retired.
8. Observation retrieval while active/closing, in caller finally, and after close/
   backend failure; no busy error, no source/store access, detached values, reset and
   later captures. Capacity/bytes/oversize/bad scalar and capture-failure cases; losses
   do not affect source/state/charges. Ambient legacy delivery flag cannot suppress data.
9. Actual failed-disconnect refusal/retry and repaired StoredSession reload. Admission
   before/after commit cancellation and settlement lost response retain conservative
   permissions/prefixes; no event becomes a state-write receipt.
10. Shared BatchEngine default/pool options and current worker compatibility through
    actual existing worker tests; all runtime source hashes match the recorded export.

A parent process enforces a finite watchdog; a hang or forced kill is FAIL, never
proof of cleanup. Record every case, versions, source/candidate hashes and counts.
**Disqualifying result:** any lost source fact, false caller cancellation, observer/
provider dependency cycle within the supported contract, premature reuse/release,
wrong permission/charge/receipt, or inability to implement passive reporting without
fabricating authoritative behavior. Stop and return upstream on an architectural
failure; do not change the test expectation to claim a pass.
**Passing result:** every required history passes in the same candidate composition,
with explicit evidence of actual SDK/SQLite behavior and zero network. Separate
inquiry probes and targeted subsets do not substitute for this full gate.

## Step 1 — Integrate current dev at the shared batch seam

### Proposed changes
Merge current dev2ddb852 (or reassess if it moves) into the issue branch. Resolve
batch_engine.py by retaining `_resolve_entity` and `_retain_cancelled_prefix=False`
and their existing behaviors. Preserve the worker cleanup-failure receipt changes
in connection_engine/account_operation and all worker modules/entry point. No manual
copy of an older connection implementation. Use the P0 integration resolution.
### Output
A current-dev source tree retaining both pool and worker requirements.
### Safe in nature
False — shared imports and SDK reader behavior cross consumers.
### Peripheral concepts
Worker protocol, actual client factory, default cancellation behavior, packaging.
### Hardness Lvl
3

## Step 2 — Make pool observations bounded passive data

### Proposed changes
Add the private collector/monitor in pool_observation.py and initialize one collector
per AccountPool. Connect all owned sources to its internal capture adapter. Add the
drain method and reject non-None health_callback before source construction. Preserve
None compatibility and all other constructor parameters. Implement exactly the field,
copy, byte/count/drop and no-user-delivery rules above; change no global health module.
### Output
Usable bounded diagnostic data without a pool-owned observer program or task.
### Safe in nature
False — explicit unmerged pool API/reporting change.
### Peripheral concepts
HealthMonitor classification/recovery, identity attribution, event serialization, logs.
### Hardness Lvl
4

## Step 3 — Preserve actual source completion on every terminal path

### Proposed changes
Refactor `_OwnedSource.run` so the completed body holder supplies the outcome on both
normal and timed paths. Separate the outer awaited caller-cancellation handler from
reading child termination. Keep `_await_cleanup`, cooperative timeout and prefix
capture. Add private `_SourceInterrupted` in pool_state.py for unexpected internal
source cancellation; preserve its prefix and refuse token settlement before mutation
in AccountPool._settle. Do not alter known wait classification, source error identity,
quota charges or no-prefix failover. Use the P0 candidate rather than a second design.
### Output
One complete outcome rule, conservative unexpected cancellation and preserved data.
### Safe in nature
False — error and permission semantics affect all pool consumers.
### Peripheral concepts
asyncio cancellation, original exception context, durable token, progress publication.
### Hardness Lvl
5

## Step 4 — Guard live lifecycle reentry without changing cleanup ownership

### Proposed changes
Add private expiring pool scopes around `_operation` and `_backend`. Check scopes at
close before setting flags; retain existing guards and external-close cleanup flow.
Provider call scope does not serialize get_pool_status as source work. Scope objects
release the pool reference on exit; old descendants and other pools are unaffected.
No global task registry, arbitrary graph inspection, background task or deadline.
Keep failed-retirement quarantine/retry and client/config clearing on actual success.
### Output
Supported reentry refuses deterministically while legitimate external close works.
### Safe in nature
False — task lineage and shutdown admission change.
### Peripheral concepts
ContextVar inheritance/expiry, backend I/O, persistent source retirement, recovery.
### Hardness Lvl
4

## Step 5 — Publish the changed contract and preserve behavioral tests

### Proposed changes
Update docs/account_pool.md, README, smoke README and examples/account_pool.py with
passive drain usage, finite/loss semantics, callback migration, internal interruption
and provider restrictions. Show error-safe application ownership of event processing;
no claim that drain acknowledges progress or proves source completion.

Expand test_31_account_pool.py with the P0 contract cases. Replace callback-based
expectations only where this plan explicitly changes the API: test callback refusal
and equivalent actual event capture/data/owner assertions. Keep original SDK/budget/
CAS/progress checks. Add secondary-finalizer fault controls and ordinary TgData/worker
callback preservation checks. Synthetic wire is a transport seam, never a fake reader.
Tests must include physical task/SDK completion and persisted outputs, not string
assertions over implementation. Private collector imports remain test-only.
### Output
An adoptable public contract and regression tests that protect behavior rather than helpers.
### Safe in nature
False — examples/API expectations change; unrelated assertions must remain intact.
### Peripheral concepts
Application receiver, error handling, legacy health behavior, live/offline distinction.
### Hardness Lvl
4

## Step 6 — Verify and commit offline implementation

### Proposed changes
Compile changed modules; run pool31 then supported offline suites12–19 and22–38,
respecting existing explicit live-skip rules. Run pool/daily/backfill/worker offline
examples, package/export checks and declared Python3.7 grammar checks. Report actual
counts and skips, not an assumed total. Inspect runtime diff for the planned scope.
Only local nonarchitectural slips may be repaired under task-impl; record each fix.

Commit code/tests/public docs separately from work notes. Update #17 honestly;
renew merge-check and fresh PR critique later on the same draft PR26. Keep work docs
on the branch, preserve duncan/main-worktree untracked files, and do not merge dev.
### Output
Verified implementation and reviewable evidence; later merge gates still explicit.
### Safe in nature
False — full integration/regression and commits require scope verification.
### Peripheral concepts
Packaging/export, current-dev worker, review status, separate archival docs.
### Hardness Lvl
4

## Step 7 — Qualify real two-account behavior

### Proposed changes
Gated by E1. Prepare a concrete bounded read-only gate for approved accounts/group
and existing allowances. Verify real identity/proxy/visibility and controlled eligible-
account switching without provoking bans/waits. Keep no-equal-history claim; no joins,
login prompts or budget resets. Preserve the original parent live gate's purpose.
### Output
Actual two-account qualification, or an explicitly pending external gate.
### Safe in nature
False — live reads consume real allowance and account resources.
### Peripheral concepts
Shared-group access, exclusive sessions, existing quota, real Telegram visibility.
### Hardness Lvl
4
