---
model: gpt-6-astra
effort: max
---
**Verdict: REORDER — TEST BEFORE BUILD**

Falsifier: retained cleanup plus source-child settlement cannot preserve caller
cancellation and the original completed source error/prefix on the actual pool/
SDK/health composition; or the proposed lifecycle fix still releases ownership
before the actual child/disconnect settles.
Affordable now: yes — seconds offline with the real pool/SDK/SQLite, blocked
sockets and controlled cleanup/finalizer delays. No account or money is needed.

Experiment: exercise a candidate of the proposed wait/retirement/shutdown behavior,
including Risk1's source-child mitigation, on the actual existing pool. Check
repeated recheck cancellation with held SDK disconnect; failed/internal-cancelled
retirement and refusal/retry; repeated read cancellation with a held cooperative
finalizer; close cancellation while the reader is ending; and original completed
FloodWait/prefix survival when the observer times out.
Cost: a short local probe; synthetic network only.
Must precede: step2's lifetime implementation; task-impl runs it before step1.
Disqualifying result: ownership escapes while a child/SDK cleanup still runs,
caller cancellation becomes success, failed cleanup grants reuse, or original
completed wait/prefix is lost. This would require replacing the lifetime premise.
Passing result: guards remain held until settlement; cancellation/failure and
reuse rules hold; source outcome/prefix remain identical; no extra read or charge.

## High-level summary

The focused repair fits the existing pool structure and current-dev integration.
One Medium boundary is missing from revision1: the source child can also outlive
its caller under repeated cancellation. Fixing only retirement and close leaves
that escape reachable from ordinary read cancellation. The plan shape survives;
extend its source lifetime handling, then test the candidate before building.
No High or Low finding. The parent live E1 remains a later execution precondition.

## Premise Inventory

### P1 — A caller's end establishes the source child's end

**First dependent step:**2. **Waste if false:** cleanup/controller tests and final
integration would qualify an incomplete ownership boundary.
**Test scheduled at:**3 covers close while a read ends, but repeated independent
read cancellation is absent. **Cheapest earlier test:** actual asyncio/pool/batch
with a delayed cooperative finalizer, seconds offline.
**Coverage:** fresh reconnaissance disproved the premise on the current branch:
the reader ended, source child remained alive, its reference was cleared and
another account read successfully. This is Risk1, not a reason to rebuild routing.

### P2 — The proposed retained-task composition preserves all existing outcomes

**First dependent step:**2. **Waste if false:** implementation/tests/docs2–5.
**Scheduled test:**3, after building. **Cheapest earlier test:** experiment above,
seconds locally. #7's temporary-client helper alone is non-covering for the pool's
failure-block/repair/source-timer combination. The baseline failure proves the bug,
not the proposed solution. This premise sets REORDER until the experiment passes.

### P3 — Current-dev integration can preserve existing public behavior

**First dependent step:**1. **Waste if false:** planned factory adaptation and
combined verification. **Scheduled test:** disposable assessment before planning,
then step5 final product. **Coverage:** a diagnostic combination passed608 checks,
with one known obsolete constructor assertion and3 live skips. Both conflicting
factory variants were read; dev already provides explicit options. That establishes
a concrete integration path, not the unbuilt final tree's verification.

### P4 — Live multi-account qualification

**First dependent step:** parent step9, outside this scoped repair. **Waste if false:**
any claim of live proxy/account behavior. **Scheduled test:** after resources and
authorization arrive. **Cheapest earlier test:** two approved logged-in accounts,
shared group and bounded allowance, unavailable under the one-account/offline-first
choice. Synthetic replies are non-covering for that premise. Scope and docs keep
it pending; it does not block the local lifetime repair.

## Restart Check

| Observation | Established mechanism | Design response |
|---|---|---|
| Read begins during cancelled recheck's old disconnect | SDK shields child but public retirement returns/release guard | Retained retirement task and source block, step2 |
| Completed prefix/wait replaced by observer timeout in old#17 design | Health reporting awaits after source finished | Keep existing outcome holder; test it before changing source wait |
| Repaired credential ignored by old client | Session retains loaded key | Successful retirement clears old client/config before reload; preserve selected repair mitigation |
| Repeated read cancellation hides live source child | wait_for's cancellation waiter is itself cancelled, then run finally clears task | Risk1 mitigation needed in step2/3 |

## Inherited Lessons

- One wait returning is not ownership settlement: examine SDK task, source child
  and public operation separately; the required experiment precedes implementation.
- Keep completed observations and source provenance: original holder remains before
  observer work; the candidate must pass the actual FloodWait100-record scenario.
- Fresh identity is not fresh credential load: retain explicit successful retirement
  and reload ordering; failed cleanup must not permit either reuse or replacement.
- Existing tests do not prove the new composition: the diagnostic608 passes and
  original36 groups are context; new source/cleanup histories are mandatory.
- No broader framework without a real class: pool retirement, shutdown and source
  child settlement share cancellation-safe waiting, but #7's cleanup failure policy
  differs. Do not change its public semantics to make a helper appear universal.

## Risk 1 — The source child can escape repeated read cancellation

**Risk**

A pool read runs its Telegram work in a separate task. If the caller is cancelled
twice while that task is finishing, the caller can exit and free the pool before
the work has actually stopped. The pool then forgets the running child and can
start another account or report shutdown complete while old work is still active.

`_OwnedSource.run` in pool_source.py awaits `asyncio.wait_for(self.task, timeout)`
and unconditionally clears `self.task` in finally. A second cancellation can
interrupt wait_for's own `_cancel_and_wait` waiter, leaving its child pending.
`AccountPool._operation` then releases `_active_task`; existing close additionally
swallows cancellation when the parent task is done. Reconnaissance ran the real
pool/reader and injected only a cooperative finalizer after the actual read exits:
`reader_ended:true,source_child_ended:false,source_reference_cleared:true`; the
next read used222 before that child ended. Close returned without cancellation
while the child remained pending. Revision1 changes close but leaves this run path.

**Severity:** Medium
**Category:** Ownership / cancellation / shutdown
**Impact:** premature new source work and unsafe cleanup/repair after a supposedly
ended operation; durable unknown-attempt state alone does not establish task quiescence.
**NoobEng:** cancelling a task that is waiting for another task's cancellation is
a separate event; the second wait can be interrupted even though the child continues.
**Affected areas:** pool_source.run, AccountPool read/close/recovery assumptions,
step2 lifetime implementation and step3 regression histories.

### Mitigation — Quick

Document that callers must never cancel a read twice.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Have run retain its local source Task until actual settlement. Use a non-cancelling
timeout observation (`asyncio.wait`) and a separately retained cancel-and-join
cleanup action. The latter cancels a pending child once, awaits its end and retrieves
its exception while repeated caller cancellation cannot interrupt the join. Keep
the current outcome holder: on internal timeout, return/re-raise completed source
outcomes before observers; otherwise attach the cancelled body's prefix to
PoolTimeoutError. External cancellation remains cancellation after the child ends.
Clear self.task only afterward. Reuse the planned private wait helper; add direct
repeated-read and cancelled-close-with-held-child tests.
**Why this is robust:** closes the additional escape at its actual task owner and
retains existing timer/outcome contracts without touching routing or stored formats.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Long-term

Introduce one lifecycle supervisor for pool sources and temporary#7 operations,
including credential generations and all observer tasks.
**Why this is long term effective:** could provide a common ownership model if
independent owners/credential rotation later require one.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Reconnaissance evidence and limits

`probes/cancellation_edges.py` ran on the actual old pool, BatchEngine, SDK and
SQLite. Its cooperative finalizer is explicit fault injection; it establishes
asyncio ownership behavior, not a claim that a live Telegram callback hangs.

```json
{"case": "repeated_read_cancel", "reader_ended": true, "source_child_ended": false, "source_reference_cleared": true, "next_read_account": 222, "child_pending_after_next_read": true}
{"case": "close_cancel", "reader_ended": true, "source_child_ended": false, "source_reference_cleared": true, "close_cancelled": false, "child_pending_after_close": true}
```

The task's existing baseline probe separately proves native SDK disconnect escaping
recheck cancellation. No runtime fix or new live action has been made.
