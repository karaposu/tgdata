---
model: gpt-6-astra
effort: max
status: REJECTED
---
**Verdict: REORDER — TEST BEFORE BUILD**

Falsifier: the source/observer composition cannot distinguish cancellation of an
observer's own awaited work from cancellation of the source caller, or cannot
refuse callback-descendant shutdown before entering a circular owned wait.
Affordable now: yes — seconds offline with actual pool/Telethon/SQLite and explicit
callback tasks. Current-code falsifiers ran and exposed both gaps below. A candidate
of the revised boundary must pass the experiment before replacement implementation.

Experiment: retain a source FloodWait7200 with 100 completed records while the
observer awaits an independently cancelled future; preserve the original outcome,
stored wait and daily pending prefix when the caller has zero cancellation requests.
Separately let an observer create/await a shutdown task; require an immediate local
reentry refusal without setting the pool closed or waiting on the caller. Combine
both with external repeated cancellation and ordinary external close/recheck.
Cost: local synthetic sessions/SQLite, no Telegram traffic, seconds.
Must precede: lifecycle/observer implementation in the revision-3 re-plan (then
its freshly critiqued/folded revision 4), rather than testing the premise afterward.
Disqualifying result: the candidate needs to discard an owned live child or ignore
caller cancellation to avoid the cycle, or cannot retain the completed source result.
Passing result: original source outcomes settle normally; true caller cancellation
still waits for owned work then propagates; callback descendants cannot enter close.

**PR decision: REJECTED — zero High, two Medium, zero Low.** CONTRIBUTING §7.3
rejects even one Medium. Section 7.4 requires revision-3 re-planning, fresh plan
critique/fold, implementation and renewed gates; no runtime patch was made here.

## High-level summary and subject

The full existing-access feature was reviewed in this warmed session, not a
subagent: product `4854464`, original implementation/plan and scoped lifecycle
plan, against dev `68f6bbd`. PR #26 opened at `cdcfd63`; prompt `2643eb7` changes
work documentation only. The 14-file product diff is unchanged throughout review.

The targeted implementation fixes hold, and fresh checks also preserve changed
identity after a completed page, pre-proof neutral health, remote-CAS cancellation,
known waits, simultaneous close/recheck, local-I/O provenance and source-free
daily/backfill replay. However, the observer remains inside the owned child without
a complete observer-versus-caller cancellation rule, and close tests only exact task
identity when deciding whether it was called from its own operation. Both omissions
are reproduced, not inferred from a hypothetical vendor behavior.

The 619 implementation passes/three live skips and merge-check fidelity PASS remain
valid evidence of their coverage. They do not answer these new histories. The
two-account live E1 remains an execution precondition, not a new review finding.

## Premise Inventory

### P1 — Cancellation of a completed observer is source-caller cancellation

**First dependent step:** original owned source Step 2 and scoped lifetime Step 2.
**Waste if false:** cleanup, routing and progress qualification built around an
incomplete outcome boundary. **Test scheduled at:** original Step 6/scoped Step 3
test external cancellation and internal observer timeout, not observer-owned
cancellation. **Cheapest earlier test:** an actual callback awaits its own cancelled
future after a real batch error; seconds, no access requirement. **Coverage:** fresh
probe ran both raw and daily calls: actual source prefix100/FloodWait7200, caller
cancel requests0, returned CancelledError, no returned/pending prefix and no stored
wait. Current behavior fails; a candidate must be tested before rebuilding.

### P2 — Exact task checks cover callback-initiated shutdown

**First dependent step:** original administration Step 4/scoped shutdown Step 2.
**Waste if false:** shutdown safety and subsequent lifetime claims. **Test scheduled
at:** direct same-task callback close is covered, descendant-task close is not.
**Cheapest earlier test:** actual callback creates/awaits `pool.close()` as a task;
seconds in an owned offline subprocess. **Coverage:** current callback child waits
for close, close's retained cleanup waits for the reader, and the reader waits for
that source child. Both automatic cancellation requests occur, yet none can end.
The probe records the actual task links and terminates only its owned subprocess.

### P3 — Identity, quota, persistence and delivery separation

**First dependent steps:** original Steps 1–5. **Waste if false:** the reusable
core would need revision. **Tests scheduled at:** prebuild primitives and Step 6,
then full integrated verification. **Cheapest earlier tests:** actual SDK/SQLite
composition already available and executed. **Coverage:** six new probe groups
held these boundaries, including identity switching after the first 100 records,
cancelled admission replies before/after commit, known wait committed before a
cancelled reply, and replay with credentials removed/pool backend unavailable/
budget access forbidden. No replacement router is justified by these findings.

### P4 — Deployment and live two-account behavior

**First dependent step:** parent Step 9/live deployment qualification. **Waste if
false:** a real deployment claim, not the authorized offline development.
**Test scheduled at:** Step 9/E1 after resources are supplied. **Cheapest earlier
test:** two approved logged-in distinct accounts/shared readable group/bounded
allowance, unavailable under the one-account offline-first choice. **Coverage:**
synthetic wire is non-covering for real account/proxy/visibility behavior. E1 stays
pending exactly as declared; no live access or quota reset occurred.

## Restart Check

| Observed failure | Established mechanism | Design element/result |
|---|---|---|
| Old client usable while cancelled retirement still runs | SDK disconnect shield outlives the old public await | Retained retirement and reuse block; current checks hold |
| Repeated read cancellation releases live source child | Interruptible wait_for cancellation waiter | Retained cancel-and-join; current checks hold |
| Observer timeout hides completed wait/prefix | Reporting awaits after source outcome | Outcome holder handles timeout, but not independent observer cancellation: Risk 1 |
| Repaired login ignored/overwritten | Cached client outlives external session repair | Explicit settled retirement/reload; original mitigation holds |
| Callback shutdown creates a wait cycle | Reentry check covers only exact parent/source tasks | Descendant closure bypasses it: Risk 2 |

## Inherited Lessons

Waiting is not quiescence: native disconnect and source-child checks remain, but
wait graphs must also be acyclic before entering retained cleanup. Completed source
work is distinct from observers: hold that result on every observer completion,
not only timer expiry. Cached identity is not ownership: fresh second-page admission
refuses before wrong-owner traffic/charge. Pool state is not delivery state: removal
of source resources leaves both replay/ack protocols operational. More passing
tests do not close an untested composition: these callback histories must precede
replacement lifecycle work. No generic framework is justified solely by these two
local boundaries.

## Risk 1 — An observer's cancelled future discards a completed source result

**Risk**

A health notification callback can await a task or future that was independently
cancelled. The pool then reports that the read itself was cancelled, even though
the application never cancelled it and Telegram already returned messages and a
two-hour wait. Those completed messages do not reach the normal return/error path
or the saved daily delivery, and the known wait is not recorded. The account is
left with an unresolved attempt that needs manual recovery.

`tgdata/pool_source.py:203–209` calls `child.result()` whenever the observed child
ends before timeout. If `HealthMonitor._deliver` (`health.py:532–546`) receives
CancelledError from its callback's awaited future, it propagates through the child.
`run` treats that as caller cancellation without examining the already-complete
`outcome` stored at lines178–186; that holder is only used on the timeout fallthrough
at214–217. `AccountPool.read` then skips `_settle`, and `SyncEngine.prepare` skips
prefix publication because it sees cancellation. The actual probe recorded zero
caller cancellation requests, original FloodWaitError/prefix100, but returned
CancelledError/prefix0, daily pending=False, stored wait0 and unresolved=True.

**Severity:** Medium
**Category:** Outcome ownership / cancellation / delivery
**Impact:** completed observations and known retry facts are withheld, source calls
appear cancelled for the wrong reason, and avoidable operator recovery is required.
The unresolved token prevents automatic unsafe retry, so this is not rated High.
**NoobEng:** the source read and the reporting callback share a child task, but a
cancelled resource awaited by that callback is not cancellation of the parent call.
**Affected areas:** `_OwnedSource.run`, pool settlement, daily/backfill error delivery.
The underlying legacy HealthMonitor propagation is inherited; the new pool's result
holder/settlement composition introduces the reviewed contract failure. A global
HealthMonitor redesign is not required to repair this instance.

### Mitigation — Quick

Require callbacks never to await cancellable work or disable callback use.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Define source result, observer completion and external caller cancellation as
separate outcomes. Once the source body completed, preserve that exact result/error
when only observer work is cancelled, including child completion before timeout.
External caller cancellation must still settle the child then propagate. Prove raw,
daily, successful-source recovery callback, and simultaneous caller cancellation
cases on the actual composition before implementation.
**Why this is robust:** uses the existing source outcome holder at the missing
boundary; it neither changes routing nor suppresses genuine caller cancellation.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The pool's existing holder closes this instance with local outcome rules. TgData reporting and scheduled HealthMonitor callbacks are real adjacent instances, but their different lifetime policies do not justify a shared dispatch redesign inside this repair; the local remedy survives such later work.
*For future:* —

### Mitigation — Long-term

Decouple health delivery from source execution across TgData, listeners and pools
using a shared outcome/event lifetime protocol.
**Why this is long term effective:** other asynchronous observers could share
explicit delivery outcomes independent of source completion.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit shared observer delivery only with separately specified caller/observer cancellation policies for TgData, listeners and the pool. It would touch unchanged consumers and add coupling beyond this instance.

## Risk 2 — Callback shutdown in a child task deadlocks the pool

**Risk**

If a health callback creates and awaits a task that closes its pool, shutdown is
allowed to begin instead of refusing the callback's reentrant request. Closing
cancels the read and waits for it; the read waits for the callback to finish; the
callback waits for closing. Cleanup retains all those waits despite cancellation,
so the pool remains stuck without starting client disconnects.

`tgdata/account_pool.py:572–574` detects only exact identity with `_active_task` or
`source.task`. A callback-created task (including the task created by `wait_for`)
is neither. It sets `_closed/_closing` at577–578, then the retained worker at580–602
cancels and awaits `_active_task`. `_OwnedSource.run` waits for the source child
under `_await_cleanup`; that child awaits the callback's close task, which retains
the worker waiting for the reader. The probe uses unmodified source/close/SDK code,
records the actual waiter links, one cancellation request each on read and close,
all three tasks pending, and zero SDK disconnects started.

**Severity:** Medium
**Category:** Reentrancy / asynchronous ownership / deadlock
**Impact:** a documented refused callback-close pattern instead hangs reads and
shutdown permanently; ordinary cancellation does not break the dependency cycle.
**NoobEng:** checking a task's identity does not identify work that it starts and
awaits. Retaining cleanup safely assumes its wait graph does not point back to itself.
**Affected areas:** `AccountPool.close`, callback-descendant operation ownership,
source-child settlement and shutdown tests. Direct same-task callback close remains
correctly refused; the missing descendant case is not a failure of SDK disconnect.

### Mitigation — Quick

Document that callbacks may never create tasks which call close.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Carry pool-specific active-operation provenance into descendants and refuse close
from that operation's observer/child context before mutating shutdown state or
waiting. Keep external close functional and invalidate stale context when the
operation ends. Test direct/create_task/wait_for callback calls, another pool's
callback, stale descendant context and repeated external cancellation.
**Why this is robust:** prevents the cycle at shutdown admission while retaining
the actual source/SDK settlement guarantees; it does not release live children.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Operation provenance at this pool's admission boundary closes the demonstrated descendant case while preserving settled cleanup. The proposed generic supervisor has no second consumer with the same ownership/close policy: temporary account operations do not expose this callback-to-pool close cycle, so the wider class is unestablished.
*For future:* —

### Mitigation — Long-term

Introduce an operation supervisor shared by temporary account operations, persistent
pools and observer dispatch, with explicit dependency/reentrancy policies.
**Why this is long term effective:** could standardize task provenance for several
owners if a common policy is established by separate design work.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Consider a shared supervisor only after another concrete owner needs the same reentrancy and lifetime policy. Do not turn these two local findings into a cross-library cleanup framework.

## Executed evidence and limits

`pr-critic-probes.py` ran with Python3.11.10/Telethon1.45.0, actual SDK/SQLite and
synthetic wire; both socket connection entry points were forbidden. Eight fresh
groups completed: six boundaries held and two defects reproduced. Exact output is
`pr-critic-probes.txt`; the two strongest observations are:

```text
observer_cancel_masks_source (raw and daily): caller_cancel_requests=0,
actual_source_error=FloodWaitError, completed_prefix=100, returned_error=CancelledError,
returned_prefix=0, daily_pending=false, actual_wait=7200, stored_wait=0, unresolved=true
callback_close_wait_cycle: child_waits_for_close=true, cleanup_waits_for_reader=true,
reader_done=false, source_child_done=false, close_done=false, sdk_disconnects_started=0
```

The intentional deadlock was isolated in an owned subprocess and exited42 after
recording the waiter graph; its parent enforced a ten-second outer bound. This is
not a Telegram outage or a test that merely sleeps and calls it deadlock.

An initial media probe incorrectly replaced `_publish`, bypassing the local-I/O
provenance wrapper being examined. Its failed assertion is retained in
`pr-critic-probes-fixture.txt`. The corrected injection fails `os.link` inside the
real wrapper, without changing expectations or product code, and passes. It is
fixture evidence, not a third finding or a silently repaired implementation.

No finding is assigned to known live E1, cooperative timeout/no cleanup deadline,
exclusive ownership, account-visible history or deferred automatic joining. Those
are explicit accepted boundaries. No runtime file changed during this critique.

**Next for #17:** draft PR; revision-3 re-plan required before further implementation.
The user has queued #10 after this review, so save this result and handoff rather
than beginning #17 re-planning or merging either branch implicitly.
