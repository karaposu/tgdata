---
model: gpt-6-astra
effort: max
---
# #17 retirement rework — revision 2

**Critic folded:** 2026-10-11 — 1 robust mitigation (steps2/3 changed,0 added).
Required six-group real-component prebuild experiment PASS at6bb40f2 before
implementation. The original pool structure and five-step shape remain.

### What is the task

Bring the unmerged existing-access pool onto dev68f6bbd and restore its promised
exclusive lifetime during retirement/repair/shutdown. Keep the implemented router,
durable facts and progress APIs. This plan supplements the parent revision2, which
continues to describe the original feature; it does not revive paused old#7 code.

### Huge Hard Blockers

#### Planning Blockers

None identified. The baseline probe established that native Telethon disconnect
survives cancellation of its awaiting pool call. Current#7 demonstrates waiting
for a retained cleanup task. Pool cleanup must additionally retain failure as a
reuse prohibition, so its outcome policy cannot simply be replaced by #7's
log-and-preserve helper. Existing source/credential/permission contracts settle
the required outcome rules; the fresh critic will test the assembled change.

#### Execution Blockers

None for steps1–5 below. Parent E1 remains OPEN for a later live qualification:
two approved distinct logged-in accounts, shared readable group and existing
bounded allowance. It gates no step in this offline rework and authorizes no live
action. A concurrent dev update must be reassessed before integration; target at
planning is68f6bbd and current feature base is8d3db76 plus work-document commits.

### How this implementation moves toward desired state

Integrate the new factory/public APIs, then let each cleanup action finish inside
an explicitly retained task before its caller releases ownership. Keep a local
retirement block on the source until successful completion clears the old client.
Use the same bounded wait mechanism for pool shutdown so caller cancellation
cannot interrupt waiting for the active reader or suppress its own cancellation.
No new stored protocol, timeout, quota or routing policy is introduced.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Integrate current dev and adapt the factory | Existing-access pool alongside all merged#7 APIs |
| 2 | Correct retirement and shutdown ownership | Settled cleanup, failure refusal and cancellation precedence |
| 3 | Add real-composition regression histories | Public recheck/close cases with actual SDK cleanup |
| 4 | Update contract and current handoff | Accurate lifetime/retry behavior and pending live boundary |
| 5 | Verify, commit and publish the scoped result | Product merge/fix commit, separate work evidence, honest#17 status |

## Step 1 — Current-dev integration

### Proposed changes

On the existing feat/17-account-pool branch, merge the verified dev68f6bbd with
`--no-ff --no-commit`, after the plan/critic gates. Keep all committed#17 work notes
on this feature branch; no merge into dev occurs in this task. Resolve README by
retaining both the account-pool section and current joining/allowance section.

Resolve connection_engine.py to dev's implementation of the factory, including
`_new_client(session_file=None, **client_options)`, the owned account operation,
health evidence and inactive join guard. Remove#17's superseded base-class
`_client_options()` hook. Adapt `_OwnedSource` in pool_source.py to override
`_new_client(session_file=None, **client_options)` and call the existing factory.
Apply the owned pool policy (zero request/connection retries and retry delay,
zero flood threshold, no auto reconnect/incoming updates, last error preserved)
on every source client. Preserve other passed options while pool policy takes
precedence for its controlled keys; combine dictionaries before the call so
duplicate keyword expansion cannot fail. Preserve session name/proxy/device/store.

Accept automatic merges only after inspecting exports and TgData: retain #7's
new methods/constructor argument and #17's ProgressFacade extraction with its
module-local backfill factory seam. Update test31's exact constructor assertion
to include trailing join_budget=None. No legacy argument moves or source-policy
default changes on ordinary clients. Keep all integration/fix product edits in
the same eventual merge commit after tests; do not commit a temporarily broken merge.

### Output

The combined source tree builds against current dev without a second base factory hook.
### Safe in nature
False — combines shared factory, public facade/imports and documentation.
### Peripheral concepts
Current#7 temporary operations, long-lived pool sources, ProgressFacade, constructor compatibility.
### Hardness Lvl
3

## Step 2 — Settle cleanup before releasing ownership [folded: Risk1, robust]

### Proposed changes

Add private `_await_cleanup(awaitable)` in pool_source.py, used only by the pool's
retirement/shutdown paths. It creates and retains one task whose wrapper returns
the work's value or captured ordinary exception/CancelledError as data. Await it
under shield in a loop, recording caller CancelledError and continuing through
repeated cancellation. Once finished, retrieve its outcome; caller cancellation
takes precedence, otherwise return the value or raise the work exception. Do not
add a deadline or swallow process-level BaseExceptions. Capturing internal
CancelledError as data distinguishes it from cancellation of the caller on Python3.7.

`_OwnedSource` gains a private local retirement-block flag, initially False.
`retire()` with a client sets it before starting cleanup. Its retained cleanup
body awaits the actual SDK disconnect; ordinary failure or SDK-internal cancellation
becomes a sanitized PoolStateError containing only its type. Failure retains the
old client/config and the block. Success clears `_primary_client`, `verified_id`,
`_config` and the block inside the cleanup body, before outer caller cancellation
can escape. No-client retirement remains harmless. A later explicit retire attempt
may retry the retained client only after the preceding attempt has actually settled.

Preflight and verification refuse a blocked source before client reuse, replacement,
authentication or reads. This is a local PoolStateError, not health or durable repair
state; pool status remains the existing stored-facts/budget snapshot. Process restart
has no old client to quarantine, consistent with exclusive ownership. Public calls
already serialize source mutations; retain that guard rather than introducing a
new distributed lease or per-client framework.

In AccountPool.close, retain current deadlock/busy/closed checks. Put the existing
cancel-and-await-active-reader plus all-source retirement sequence inside one cleanup
body and await it with `_await_cleanup`. Set `_closed`/`_closing` before the body;
clear `_closing` only after it settles. The worker handles cancellation of the active
reader as expected shutdown, records the first ordinary retirement error while
attempting other sources, then raises it. Caller cancellation must not propagate
into this worker or its await of the reader. Existing source errors still belong
to their original caller. A failed/cancelled close never reopens the pool.

In AccountPool.__aexit__, explicitly re-raise caller CancelledError from close.
Retain the original body exception when ordinary cleanup fails, with the existing
type-only warning. SDK-internal disconnect cancellation is converted by retire and
does not pretend the caller cancelled. No change to read selection, budget accounting,
CAS settlement, recovery or progress delegation.

In `_OwnedSource.run`, retain a local reference to the actual source child until it
ends. Replace wait_for's interruptible cancellation-wait sequence with a non-cancelling
`asyncio.wait((child,), timeout=...)` observation. A separately retained stop-and-join
action cancels a pending child once, waits for it and retrieves its outcome; await
that action with `_await_cleanup` on internal timeout or caller cancellation. Clear
`self.task` only after settlement. An external cancellation remains cancellation even
when repeated; no next source starts while the child remains active. Preserve the
existing body outcome holder before health observers: completed original errors/
prefixes or batches survive an internal observer timeout; unfinished body cancellation
still becomes PoolTimeoutError with its existing partial_result. Keep error raising
outside incidental timeout-handler context as before. Do not let the stop action's
exception retrieval replace the captured source result. The prebuild candidate proves
this composition with real SDK/SQLite/health and a labeled cooperative finalizer fault.

### Output

Pending cleanup retains the public operation guard; failed cleanup refuses reuse;
successful retirement permits a fresh client, and caller cancellation is preserved.
### Safe in nature
False — changes delicate asynchronous teardown and exception precedence.
### Peripheral concepts
Telethon shielded disconnect, repeated cancellation, retained tasks, credentials, pool exclusion.
### Hardness Lvl
4

## Step 3 — Qualification on actual SDK cleanup [folded: Risk1, robust]

### Proposed changes

Extend test31 using its real pool/SQLite/Telethon fixtures. Delay/fail only the
transport/session-close boundary; do not replace retire/close or the owned reader
to supply the expected outcome. Use events to force overlap; always release gates
and retrieve cleanup tasks in test finalizers. Preserve existing assertions/tests.

Cover at least:
- Public recheck cancelled while native SDK disconnect is held: caller stays pending,
  read/recheck refuse busy, no history/charge/client replacement. Repeat cancellation;
  release → one completed disconnect, original cancellation, old source cleared.
- Successful ordinary recheck and post-cancel fresh load: replacement StoredSession
  credential survives; no old client writes after the new one is used.
- Native disconnect/close failure and SDK-internal cancellation: local sanitized
  failure, retained client blocked from reuse, no new health/charge/source work;
  explicit retry can complete retirement/recheck. Include caller cancellation together
  with failed cleanup and require cancellation plus retained refusal.
- Pool.close during delayed retirement: repeated cancellation waits; new work stays
  closed, concurrent close refuses busy, all source cleanup settles before return.
- Close while a real source read is suspended, including delayed cooperative source
  finalization: outer close cancellation must not cause premature reader release.
  Label any fault-only finalizer injection; do not call it live SDK behavior.
- Independently repeat cancellation of a pool read during a held cooperative source
  finalizer: the public call and operation guard stay pending, self.task retains the
  live child, no next account starts, and cancellation escapes only after that child
  ends. Re-run existing timeout-prefix and completed outcome/observer tests unchanged.
- Async context exit: original body error survives ordinary cleanup failure, caller
  cancellation during cleanup survives after settlement, and SDK-internal cancellation
  remains a local failure rather than caller cancellation.
- Repeated cleanup does not open clients or reset quota/restrictions; pending replay/
  acknowledgment remain local and callable after close, as existing tests require.

Exercise policy precedence through actual _new_client construction and pin settings.
Test helper cancellation under an Exception-derived compatibility fixture only when
needed; do not claim a native Python3.7 runtime. Measure the new group count.

### Output

Meaningful regression histories for the reproduced race and its cleanup boundaries.
### Safe in nature
True — synthetic transport, blocked sockets and temporary data only.
### Peripheral concepts
Actual disconnect tasks, pool state, stored credentials, callbacks, timeout/prefix tests.
### Hardness Lvl
4

## Step 4 — Contract and handoff

### Proposed changes

Update docs/account_pool.md with settled cleanup, delayed caller cancellation,
failed-source reuse refusal and explicit retry; distinguish local source refusal
from the existing persisted eligibility snapshot. State that an indefinitely hung
SDK cleanup can delay cancellation; never promise successful closure after a failed
attempt. Update README/smoke README for current dev and the measured new test count.
Remove stale current-tense statements that#7 is paused from public/current handoff
text, without rewriting original historical plan/critic evidence. New HANDOFF.md
links the parent implementation plan and this scoped rework/verification.

Keep automatic joining and the two-account live qualification visibly deferred;
new#7 APIs coexist but do not silently grant the pool new behavior.

### Output

The current public contract and navigation record describe the final composition.
### Safe in nature
True — documentation of the selected behavior.
### Peripheral concepts
Operator cleanup/retry, offline versus live qualification, historical evidence.
### Hardness Lvl
2

## Step 5 — Verify and record

### Proposed changes

Run new/extended31 first, then all supported offline12–19,22–36 (23 suites; the new
merged#7 suites32–36 included). Existing baseline is573 +36 pool groups =609 before
added cases; count actual passes separately from3 live skips. Run account-pool,
daily-continuation and fresh/restarted backfill demos. Compile/AST-check Python3.7
grammar under actual Python3.11.10/Telethon1.45.0. Export the integrated product tree
without Git/work artifacts and run the pool suite/demo there. No live accounts.

Compare unchanged router/state/progress/budget modules against the starting product
and current dev as appropriate. Check scoped diff/whitespace, preserve both branches'
public features and all original user files. Complete the in-progress feature-branch
merge with product code/tests/public docs as one commit; work artifacts remain separate.
Record failures and any small nonarchitectural fixes rather than weakening tests.
Architectural verification failure stops for re-planning under task-impl.

Commit verification/HANDOFF/evidence separately, push the feature branch and update
#17 to show this offline continuation complete, live E1 and review/PR/merge pending.
No merge into dev is authorized by this implementation request.

### Output

An integrated and verified#17 branch with explicit evidence and honest remaining gates.
### Safe in nature
False — branch merge/commits/push and issue updates are prescribed mutations.
### Peripheral concepts
Current-dev regression baseline, release-like export, archive-only notes, live prerequisites.
### Hardness Lvl
3
