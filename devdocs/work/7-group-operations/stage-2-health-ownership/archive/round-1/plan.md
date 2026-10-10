---
model: gpt-6-astra
effort: max
---
# #7 Stage 2 implementation plan — revision 2

**Critic folded:** 2026-10-09 — 2 mitigations (3 steps changed, 0 added).
Prebuild experiment PASS in `46866c3`, before any runtime implementation.

### What is the task

Make the health state observed during Stage 1's verified temporary operations
belong permanently to that numeric account. Give callers an explicit local query,
prevent inappropriate recovery, and keep notification behavior outside the
operation's result and source lifetime. Preserve the legacy public path.

### Huge Hard Blockers

#### Planning Blockers

None open. `desc.md` and `traverse/finding.md` settle ownership, compatibility,
pre-proof behavior, evidence and notification timing. The five baseline probes
establish the failure mechanisms; no server behavior is newly assumed. The local
composition premise below must be executed before implementation.

#### Execution Blockers

None identified. Stage 1 is merged; Python 3.11.10 / Telethon 1.45.0 and synthetic
transport fixtures are available. No network/login or second live account needed.

### How this implementation moves toward desired state

Keep each existing HealthMonitor ledger complete, fixed to one verified account
for the new path. Put owned observation/recovery/delivery in a small private module
that reuses the ledger, classification, event shape and snapshot. Add only the
context and source hooks needed in existing health/client code. Compose those with
the unchanged Stage 1 handle in TgData; do not route legacy calls through them.

An observation lives only in its task and exact client. A raw SDK RPC failure is
recorded there, even if later caught. Start order is captured before authentication,
so concurrent older operations cannot clear newer facts. Delivery tasks only start
after source cleanup and never participate in the operation's exception handling.

### High-Level Summary

| Step | Description | Expected Output |
|---|---|---|
| 1 | Fixed ledger and owned observation | Private monitor/call with conservative recovery and queued notifications |
| 2 | Source hooks and scoped isolation | Actual RPC failures and successes bound to the client; enclosing legacy calls isolated |
| 3 | Facade composition and query | Private owned boundary, local public snapshot and cooperative notification close |
| 4 | Contract regressions and docs | Real-SDK offline suite and README contract |
| 5 | Verify and checkpoint | Product commit, separate work notes, pushed branch and truthful #7 status |

## Prebuild composition check

Before any runtime edit, run a saved offline probe using the real factory, Stage 1
handle, budget admission, Telethon 1.45.0 request/exception code and disconnect.
Observe client identity and raw exception object at the existing outer request
wrapper; inject only transport responses. Verify a caught RPC remains observable,
budget verification re-enters the wrapper, and disconnect settles before a separate
callback task runs. Also exercise ContextVar isolation and callback cancellation
using actual asyncio tasks. Do not replace Telethon's request or disconnect logic.
Record the boundaries this does not cover: Telegram permissions/server behavior,
future group semantics and the not-yet-written Stage 2 wiring.

## Step 1 — Reuse fixed ledgers with owned calls

[folded: Risk 1, robust]

### Proposed changes

Add `tgdata/owned_health.py`. `_OwnedHealthMonitor(HealthMonitor)` holds a fixed
`(session, account_id)` and reuses record/event/snapshot/classification. It has a
private `observe(operation, method, group, started)` context yielding `_OwnedCall`.
The call holds the verified handle, exact client, task, start tick, successful
request names, explicit group-access confirmation and a per-operation event list.
Initial account proof counts as account evidence, never request/group evidence.

Add narrow `_Call` hooks for successful answers and raw RPC errors in `health.py`;
legacy defaults keep existing behavior. An owned call disables ambient `report`
and sleep-log attribution: only the client's source hook can record its failures.
No raw RPC inference from local exception causes. Ordinary errors or cancellation
mark the observation unsuccessful and propagate unchanged; no error classification
at owned context exit. Health hook failures are contained.

Immediately before recovery, require the handle's existing active opening-task
check again. Caught verification failures permanently invalidate Stage 1's handle;
that invalidity vetoes recovery even when the body returned normally. Do not add a
second invalidation protocol or replace the caller's outcome when vetoing recovery.

Recovery requires a successful operation, same owner, a condition tick older than
the operation's start, and no same-call report for that scope. Logged-out/banned
conditions may recover from fresh proof. Restrictions also require a post-proof
successful request and matching operation method. Waits gain private generation
ticks and require a successful matching request. A current call cannot clear the
wait it reported, even if it catches the exception and then succeeds.

`confirm_group_access()` is an internal semantic assertion by later group code;
it requires the active owner task and at least one successful owned request after
proof. Stage 3 must call it only after a result actually establishes access, never
after self verification or metadata alone. Stage 2 never infers access automatically
and does not build a request-to-permission classifier. Parent reported flags may
propagate only across the same monitor and task, while both calls remain active.

Queue plain event dictionaries per observation. `dispatch` starts a tracked task
after the facade finishes cleanup. Both sync invocation and awaiting async callbacks
occur in that task; ordinary errors and callback cancellation cannot reach the
operation. Preserve the recursion guard even for callback-originated operations.
Retain/retrieve task outcomes, contain logging failures, and offer cooperative
retirement of pending delivery tasks, excluding the current callback task.

### Output

One fixed-owner ledger per account can record, snapshot and recover conservatively;
callbacks have no path into the primary outcome. No global identity/trace registry.

### Safe in nature

False — shared health context seams require legacy regression coverage.

### Peripheral concepts

HealthMonitor ledger, ContextVar inheritance, asyncio cancellation, callback re-entry,
plain event data, per-account/per-group/per-request condition scopes.

### Hardness Lvl

4/5 — lifecycle and concurrent evidence must agree; keep source/time predicates explicit.

## Step 2 — Attach source evidence and isolate the boundary

[folded: Risk 2, robust]

### Proposed changes

In `_AnswerEvidence.__call__`, catch a raw `RPCError`, call the safe owned error
hook with `self`, then re-raise the same object. Catch the SDK's `MultiError` too
and observe each raw RPCError leaf at that same bound-client hook; preserve the
container and existing deduplication. Partial successes do not count as recovery
evidence. On fully successful lists retain each successful request name, without
request traces or a new generic outcome layer. On success, pass `self` and the
request to `health.note_answer`; legacy no-argument use remains valid. Nested
budget identity verification deduplicates the same exception with the existing
reported marker. An owned hook accepts only its exact client, active opening task
and still-valid handle. No group/account state from a foreign client or child task.

Add a scoped context manager in health that sets `_CURRENT` to None around setup,
cleanup and the owned scope. Mark active enclosing calls in the same task unable
to recover from the nested operation. If an error escapes, remember that object
only in those enclosing calls; their error/report paths skip that error and its
wrappers. This is short-lived per-call exclusion, not a global provenance registry.
Other independent errors in the same enclosing call still report normally.

### Output

Caught owned RPC failures are retained at source; unverified errors cannot be
relabeled by enclosing legacy health. No Stage 1 policy/budget/session changes.

### Safe in nature

False — changes the shared client wrapper and legacy context's exclusion check.

### Peripheral concepts

Actual SDK error objects, `_AnswerEvidence` MRO, BudgetClientMixin re-entry,
exception cause chains, connection setup/disconnect, task ownership.

### Hardness Lvl

4/5 — source attribution must survive nested calls without claiming foreign evidence.

## Step 3 — Compose at the facade

### Proposed changes

Keep `_health` unchanged and add an initially empty per-instance map of owned
monitors. `get_account_health(account_id)` validates a positive non-bool numeric ID
using Stage 1's helper and returns `snapshot()` or None, synchronously, without I/O.

Add private `_account_health_operation(expected_account_id, method, group=None)`.
Capture start order before authentication, enter isolation, open Stage 1's existing
`connection_engine._account_operation`, then obtain/create the fixed monitor from
the verified ID and configured session label. Enter owned observation and yield
`(operation, observation)`. Finally dispatch that observation's queued events only
after Stage 1's disconnect attempt finishes, including failure/cancellation paths.
No owned monitor is created on failed verification. Source handles become invalid
through Stage 1 exactly as before.

`TgData.close()` also retires pending owned notification tasks cooperatively in a
finally block. Exclude its own delivery task if invoked from the callback. This
retires existing tasks, not concurrent operation producers; callers finish their
operations before closing, as with the existing facade. No scheduler/shutdown barrier.

### Output

A single internal entry point for future group operations and a public explicit
local health query. Legacy `health_check()` continues to select its own ledger.

### Safe in nature

False — the close path gains notification cleanup; other changes are additive.

### Peripheral concepts

Configuration session label, expected/verified identity, Stage 1 close guarantees,
local snapshots, existing facade close semantics.

### Hardness Lvl

3/5 — ordering the two contexts and dispatch is the important part.

## Step 4 — Tests and user contract

[folded: Risk 1, robust; Risk 2, robust]

### Proposed changes

Add `tgdata/smoke_tests/test_33_owned_health.py`, using test32's real-SDK fixture
with socket connections forbidden. Extend synthetic response scripts only at the
transport. Exercise the facade, real wrapper, monitor and cleanup together.

Cover both required identity cases; post-event cache changes; independent accounts
and instances; local query validation/copy/no-I/O; pre-proof auth and mismatch inside
legacy calls; local wrapped errors; caught RPCs and nested budget deduplication;
foreign clients/tasks and stale contexts; explicit group recovery versus self-only
success; same-call recovery refusal; forced older/newer overlaps for account, group
and request waits; matching request/method evidence; callbacks starting only after
disconnect; sync/async failures and callback cancellation; re-entry, pending task
retirement/self-close; operation cancellation and broken cleanup preservation.
Retain the original five failure cases as end-to-end regressions where applicable.
Add caught post-proof identity/auth loss followed by normal body completion and
verify that prior conditions remain. Exercise a real SDK mixed request list and
its actual MultiError container; record its failure leaves and preserve the same
container, including when the body catches it. Successful list request evidence
is covered separately. Only the transport fixture supplies list sender futures.

README explains the two views, unknown=None, fixed owner, source `rpc`, conservative
recovery, callback timing and lifetime. Clarify that Stage 2 is foundation only:
existing public reads still use legacy health until explicitly migrated later.
Add the new offline suite to the smoke-test README, with no live test instruction.

### Output

Behavioral contract coverage and docs that do not advertise unbuilt group APIs.

### Safe in nature

True — tests/docs only; test transport has no network capability.

### Peripheral concepts

Test16 compatibility, test32 fixture, synthetic session store, real read-budget SQLite,
stable event/snapshot dictionaries and future Stage 3 access assertions.

### Hardness Lvl

4/5 — force ordering with events/futures, not tests that merely agree with helpers.

## Step 5 — Verification and commits

### Proposed changes

Compile runtime/tests/examples and check Python 3.7 grammar compatibility. Run new
suite33, health16, Stage1 suite32, then supported offline suites12–19 and22–30.
Use missing config for suites12/13's known live skips; no older live-oriented suite.
Run daily continuation demo and both first/restart backfill demo paths in temporary
directories. Local bind in suite12 may need normal sandbox escalation.

Only small local corrections are permitted by task-impl; record all of them.
Architectural plan failure stops the run. Never change an expectation to hide it.
Review diff/whitespace, commit code/tests/README together and work-folder verification
and handoff separately. Stage only these files; preserve original checkout, duncan,
all archive worktrees and unmerged #17. Push this branch, post the qualified description
and update #7's Stage 2 pipeline boxes only for committed artifacts. #7 remains open;
merge check, PR and fresh PR critic are later work.

### Output

Verified implementation, separate archive documentation, explicit remaining gates.

### Safe in nature

True — validation and isolated feature-branch checkpoints, no live service changes.

### Peripheral concepts

CONTRIBUTING checkpoints, Telethon1.45.0, offline suite boundaries, user exclusions.

### Hardness Lvl

2/5 — run known checks once, repeat only when a change/failure warrants it.
