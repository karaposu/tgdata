---
model: gpt-6-astra
effort: max
revision: 4
---
**Verdict: REORDER — TEST BEFORE BUILD**

Falsifier: the combined actual source/SQLite/progress composition either treats
provider interruption as caller stop, releases a live write, loses completed data,
infers permission from an uncertain admission, or allows same-pool provider control.
Affordable now: yes — local synthetic sessions/SQLite/blocked sockets, minutes of
execution plus bounded candidate construction; no live credentials required.

Experiment: execute the plan's full P0 using a fresh dev2ddb852/product71502e5 export,
prototype steps2–5 and selected Risk1. Retain all37 earlier groups, add the complete
source/pool/progress storage matrix, and run worker37/38 in the same parent-controlled
attempt. Actual SDK pagination/native cleanup, ledger and SQLite create the outcomes;
fault adapters may cancel their own awaited I/O before/after real CAS, not fabricate
permission, data or receipt state. Include caller cancellation while a real provider
finalizer waits to commit, and synchronous session load interruption.
Cost: offline; no service spend; bounded parent watchdog per process.
Must precede: step1 (the plan already lists P0 there; execute it, do not waive it).
Disqualifying result: any semantic assertion fails or watchdog fires. A released
live child, changed expected data loss, invented rollback or stand-in outcome is not
an acceptable repair. Minor fixture slips are recorded separately.
Passing result: every retained/new case and both workers pass in one combined run,
with hashes/commands recorded and working-branch runtime unchanged. Then fold/implement.

Result: PASS — combined48/48, worker33/33 and25/25; all actual ownership/data/
permission assertions held, no watchdog, 2026-10-13. See prebuild.md. A local added
fixture input correction is recorded; no runtime candidate change or weakened
expectation. Branch runtime remained identical to71502e5 throughout P0.

## High-level summary

Reviewed plan7872998 against actual current implementations and accumulated history,
in this warmed session. One Medium content risk; no High/Low padding. The proposed
ownership mechanism serves real repeated source/provider instances. Cleanup retains
a deliberately different policy. No replacement router, cursor engine or global
supervisor is justified. The passive observation design has prior positive evidence,
but source/store ownership and data preservation require the full fresh composition.
This is a plan review, not another rejected PR review.

## Premise Inventory

### P1 — One interruptible owner can distinguish all cancellation origins

First dependent step2; if false, steps2–6 lifetime/data work needs redesign.
Test scheduled P0 before1, repeated6/7. Cheapest earlier test is P0: actual SDK plus
SQLite provider I/O before/after commit, caller interruption while finalizing, all
three progress modes. Prior source-only success is non-covering for store ownership;
r3's failed37th group proves that. Task counts and documentation are non-covering.
No use of Python3.11-only cancellation counters in runtime may supply the answer.

### P2 — Data retention does not become permission or a receipt

First dependent steps4–5; false would invalidate admission/ack claims. P0 precedes
build,6/7 regress. Cheapest test: actual CAS and lost reply at admission, settlement,
publication and acknowledgment, inspect stored bytes and source traffic; minutes.
Existing pool prefix/error behavior and backfill exact reconciliation provide reuse
points, not coverage of new CancelledError paths. Success/end batch and failed-read
prefix both needed. Check same saved payload/hash on replay; error data alone is not
acknowledgeable and cannot prove end-of-history.

### P3 — Source-free storage calls still reject provider-driven source control

First dependent step4; false permits I/O role reversal or recursive ownership during
status calls. Cheap real-component probe ran in probes/restart/reentry_recon.py:
get_pool_status's provider awaited recheck_account, actual verification and SQLite
verified_at update succeeded. P0 must test refusal for all exclusive operation entry
points after the proposed task/scope hop. Risk1 below is a local content amendment,
not a new abstraction or premise requiring different steps.

### P4 — Combined compatibility and actual live service behavior

First dependent step1 for current-dev union; P0 workers plus step7 full suite close
that local composition. Previous workers pass on union, not new helper. Ordinary
TgData health/cancellation must keep existing behavior except added error data.
For real account/proxy/visibility behavior first dependent step8, E1 OPEN; user must
supply two approved accounts/group/allowance. Synthetic wire is non-covering for live
service behavior. Earlier real live test is not affordable with one account.

## Restart Check

| Observed failure | Established mechanism | Addressing design |
|---|---|---|
| Client reused during cancelled native disconnect | SDK shield outlived waiter | Steps2/3 retain existing physical retirement, P0 native controls |
| Repeated cancellation released source child | Interruptible cancellation waiter | Step2 owned cancel-and-join, P0 held finalizer |
| Callback cancellation hid completed prefix/wait | Child status substituted for source outcome | Step3 body holder all paths + passive capture |
| Callback child/outside actor deadlocked shutdown | Reader/observer/close wait cycle; ancestry incomplete | Step3 removes observer dependency, step2 scopes/provider role |
| Drain during closing replaced reader cancellation | Busy policy applied to local observation | Step3 drain synchronous in every state |
| Store cancellation hid real source data | Inline _backend CancelledError bypassed settlement/error publication | Steps2/4 owned provider, step5 known data retention |
| Status provider can reenter administrative control | No _active_task during state-only load | Risk1 guard at step4 _operation as well as close |

## Inherited Lessons

Task termination/source outcome: steps2/3 and P0 beforebuild. Cancellation/rollback:
step4 definite admission and exact existing reconciliation, P0 both commit sides.
Data/durability/ack: step5 interrupted errors, P0 actual pending/replay. Acyclic retained
cleanup: steps2–4 provider role plus guarded control, P0 external/foreign/expired
controls. Ancestry is not a wait graph: callback dependency removed, no general claim.
Composition precedes bulk implementation: full P0 mandatory before step1; neither
recon nor the earlier36 successes substitute. Existing mechanisms retained only where
their authority contract is unchanged; no schema/protocol redesign hidden in helper.

## Risk1 — Status providers can enter account administration

**Risk**

An application-supplied storage method can run while the pool is only reporting
status. If that method tries to repair or initialize the same pool, there may be no
active reader for the usual busy check to detect. The supposedly storage-only call
can then verify an account or change its permission record, and a provider that
repeats the dependency can recurse or wait on its own work. Rejecting shutdown alone
does not enforce the promised separation between providers and lifecycle control.

`AccountPool.get_pool_status` awaits `_backend` outside `_operation`. Step4 adds a
scope but only specifies a refusal at `close`; `_operation` still checks closed and
`_active_task`. A provider can invoke `initialize`, `recheck_account`, `recover_account`
or `read` while `_active_task is None`. The actual baseline probe made a status-load
provider call recheck_account and observed a real verified_at SQLite update. The same
scope predicate must also be checked before entering `_operation`, not only recorded
inside it. P0 must cover status-originated pool/sync/backfill provider calls.

**Severity:** Medium
**Category:** Lifecycle reentry / extension contract
**Impact:** hidden source/admin mutation and possible recursive provider dependency.
**NoobEng:** state reports deliberately remain usable without claiming a source slot;
that is why the existing one-active-reader check is insufficient for their providers.
**Affected areas:** account_pool._operation, pool_lifecycle scope, provider reentry tests.

### Mitigation — Quick

Document the provider prohibition and rely on applications to honor it.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Check the existing live same-pool scope predicate before _operation changes ownership,
as well as before close changes flags. Preserve state-only status/replay/ack and foreign/
expired scope behavior. P0 uses actual pool/daily/backfill load providers to try each
exclusive administrative/source entry and asserts local refusal with unchanged state,
clients and quota; direct/task/wait_for paths must agree.
**Why this is robust:** closes all existing exclusive controls at their shared entry,
using the scope already needed by the plan. No new owner or task registry.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Existing read/initialize/recheck/recover share one actual entry point,
so one scope check covers the class. Temporary #7 operations and worker/standalone
progress have different ownership policies; a common cross-library mechanism is not
established. Robust has the best reach/extent and survives later capability work.
*For future:* —

### Mitigation — Long-term

A repository-wide provider capability layer for pool, temporary account operations,
worker and standalone progress stores.
**Why this is long term effective:** explicit capabilities could prevent provider
control inversion across public components if a common ownership contract is established.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Execution preconditions

E1 unchanged: step8 needs two approved accounts/shared group/existing allowance.
No live access/joins/budget reset were used in this review. PROJECT_SPECIFICS absent;
commands must come from existing runners. PR26 stays draft until renewed later gates.
