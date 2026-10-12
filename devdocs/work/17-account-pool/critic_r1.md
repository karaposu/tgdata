---
model: gpt-6-astra
effort: max
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the actual SDK/budget/health composition cannot retain the real source
owner and already-completed source outcome when an observer is cancelled by the
pool timer; a proposed wrapper only works by fabricating the desired result.
Affordable now: yes — offline, synthetic wire, actual SDK/ledger/HealthMonitor;
under a minute, no credentials or network.

Experiment: run the retained plan-critic probe against current source. Confirm a
wrong fresh ID is rejected before history/charge, then complete100 records and
raise FloodWait7200 while the actual HealthMonitor awaits a blocked callback.
Compare naive timer handling with a wrapper retaining the source body's completed
outcome before observer work. Use actual BatchEngine with only the proposed
cancellation exception seam, actual SDK requests and actual health context.
Cost: local temporary SQLite/session data and <1 minute; no Telegram traffic.
Must precede: step2, and task-impl requires it before step1.
Disqualifying result: fresh mismatch sends history/charges an account, or retention
cannot recover the original FloodWait and100-record prefix after observer cancellation.
Passing result: zero wrong-owner history/charge; original FloodWait7200 and exact
100-record interrupted prefix survive with the source child ended.

Result: PASS — zero wrong-owner history/charges; retaining the actual source outcome preserved FloodWaitError7200 and100 interrupted records after observer cancellation. Ran the real composed probe before plan step1 on 2026-10-08. Evidence: `probes/plan_premises.py`. No Telegram connection.

## High-level summary

The owned account design survives. Two implementation boundaries need precision:
retain source outcomes before health observers can suspend/cancel them, and reload
stored credentials during deliberate repair. The first is demonstrated by a
reconnaissance probe and receives the formal pre-build experiment above.
One High and one Medium risk; no global #7 rewrite required.

## Premise Inventory

### 1. Actual guarded source can preserve identity and completed outcomes

**First dependent step:**2. **Waste if false:** steps2–8 would build on an unusable
owned-reader seam. **Test scheduled at:**6, with narrower existing traverse probes.
**Cheapest earlier test:** the formal experiment above, affordable now. **Coverage:**
traverse proved stale identity, actual admission and raw cancellation-prefix transfer;
it did not test a timer firing during HealthMonitor's awaited callback. Reconnaissance
now shows the naive wrapper loses prefix/wait while retaining the actual source
outcome preserves them. Run the exact retained composition before implementation.
Fake readers returning a prefix are non-covering; these probes execute the reader.

### 2. Actual SQLite supports token admission and stale-settlement refusal

**First dependent step:**1. **Waste if false:** state/router work. **Test scheduled
at:**6. **Cheapest earlier test:** actual CAS/reconstructed backend, already run.
**Coverage:** current traverse probe PASS; product tests still need the whole pool
codec/transition composition. This documentary/primitive premise is closed, not a
reason to infer the unbuilt state machine is already verified.

### 3. Actual progress engines accept reader substitution without source replay

**First dependent step:**5. **Waste if false:** facade integration/docs/tests.
**Test scheduled at:**6. **Cheapest earlier test:** real current daily/backfill
engines and SQLite, already run. **Coverage:** both replay probes PASS with a changed
source account and zero new reads. Facade extraction parity remains implementation
verification, not an assumed SDK behavior.

### 4. Deployment ownership, time and live resources

**First dependent step:**9 for live deployment qualification; steps1–8 implement
an explicit single-owner/UTC contract. **Waste if false:** a deployment outside the
contract requires another ownership/time design. **Test scheduled at:**9.
**Cheapest earlier test:** operator/deployment evidence, unavailable here; cannot
be replaced by a fake clock or invented second account. **Coverage:** offline fault
tests cover enforcement, not real deployment. User has explicitly replied one
account for now; build/test offline first. E1 remains an execution precondition.

## Restart Check

| Observed failure | Established mechanism | Design element |
|---|---|---|
| Actual222 charged while health111 | SDK get_me leaves nonempty cached self ID | Step2 owned fresh identity and bound ledger |
| Authentication requests7200-second sleep | Ordinary _authenticate catches FloodWait and sleeps | Step2 private direct authorization path |
| Exhausted ServerError becomes ValueError | SDK default raise_last_call_error=False | Step2 preserved original SDK failure |
| Post-result fact may not commit before crash | No pre-source restriction-state marker in first proposal | Steps1/3 durable attempt token |
| Cancellation drops completed raw records | BatchEngine only catches Exception | Step2 opt-in prefix seam |
| Observer cancellation masks actual source failure/prefix | HealthMonitor.call awaits _on_error after body raised | Risk1 retention before observers |

## Inherited Lessons

Cached identity is not actual owner: probe precedes step1 and binding is step2.
More retry/health machinery does not prove correct delivery: real SDK/prefix probe
precedes router step3; actual progress composition tested in step6. Known state
does not mean settled source: token admission precedes network in step3. No added
source layer may duplicate acknowledgment: facade reuse step5; replay tests step6.
Existing one-account live proof does not establish multi-account operation: E1/step9
explicitly pending, never represented by synthetic account fixtures.

## Risk 1 — A timeout during reporting can replace the real source outcome

**Risk**

A read may already have collected messages and received a long Telegram wait,
while its optional health callback is still running. If the pool's timer then
expires, it can see only a generic timeout. It would lose the completed messages
and remember a short transport cooldown instead of the actual long wait.

`tgdata/health.py:HealthMonitor.call` awaits `_on_error` after the batch body raises.
The step2 wait_for wrapper can cancel that await after `BatchEngine.fetch_batch`
has attached its prefix to the original FloodWaitError. The resulting CancelledError
comes from callback delivery, not the batch exception seam, so inspecting only
TimeoutError.__cause__.partial_result is insufficient. Reconnaissance reproduced
zero prefix/unknown wait for naive handling, versus100 records/FloodWait7200 with
source-body outcome retention.

**Severity:** High
**Category:** Data preservation / error provenance
**Impact:** lost completed observations and early reuse of a rate-limited account.
**NoobEng:** health reporting is an awaited stage after the source has already
finished; timing out the combined coroutine does not imply the source timed out.
**Affected areas:** step2 pool_source timer, step3 outcome classification, daily/
backfill prefix delivery, optional health callback.

### Mitigation — Quick

Document that callbacks must never block and keep the simple timeout-cause lookup.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Retain the source body's batch or original error in an owned outcome holder before
HealthMonitor performs observer work. On an internal timer, await child termination;
if source already finished, return/re-raise that exact outcome. Otherwise transfer
the cancelled reader's completed prefix into PoolTimeoutError. External cancellation
always propagates. Test both successful and failing source bodies with blocked
callbacks, including long-wait retention and no extra source attempt.
**Why this is robust:** covers the actual two-stage completion boundary without
changing global health delivery or weakening the callback contract for other callers.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Selected robust/elegant: this pool is the only new timed observer composition. Existing _reported and listener paths form a possible broader class, but changing them expands scope and is unnecessary for the owned outcome holder. The local fix survives a future shared mechanism.
*For future:* —

### Mitigation — Long-term

Separate source outcome capture from observation delivery throughout the existing
TgData health decorator, listeners and pool contexts.
**Why this is long term effective:** provides a shared outcome/observer boundary
for every asynchronous reporting path.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit shared source/observer outcome capture when another timed public operation needs it; existing TgData decorators/listeners would then be concrete additional consumers.

## Risk 2 — Rechecking an old client may ignore a repaired stored login

**Risk**

An operator can repair a login in its store, then ask the pool to recheck it. If
the pool keeps using the previously opened client, that client still holds the old
login key. The recheck would repeatedly fail even though the replacement login is
valid, forcing callers to reconstruct the entire pool to recover.

Step4 `recheck_account` promises authentication/identity repair but does not state
that the owned client is retired and its session reloaded. Telethon's live session
and `tgdata/session_store.py:StoredSession` cache the loaded credential; calling
fresh `get_me` refreshes server identity for that credential, not the store record.
The repair path must explicitly close/reload before its guarded authorization call.

**Severity:** Medium
**Category:** Stale credential / lifecycle detail
**Impact:** repaired accounts remain unusable; unsafe ad-hoc client replacement by callers.
**NoobEng:** a fresh request and fresh credential load are different operations.
**Affected areas:** steps2/4 pool_source ownership, session storage and recheck.

### Mitigation — Quick

Require users to close/reconstruct the whole pool after every login repair.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Recheck only after quiescence/known waits: await retirement of that slot's client,
reload its configured session and repeat alias preflight, then durably admit the
identity-only check. Refuse if retirement cannot establish safe ownership. Preserve
all stored restrictions until the new identity is verified and settlement commits;
test an actual StoredSession credential replacement with no overwritten new key.
**Why this is robust:** repairs the precise stale object while preserving the
pool's durable restrictions and session-store conflict behavior.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Selected robust/elegant: retire/reload the exclusive slot and retain durable facts. Persistent TgData sessions are another rotation instance, but a global generation protocol changes their ownership contract and the pluggable store interface. This narrow reload remains useful if such a protocol is added.
*For future:* —

### Mitigation — Long-term

Introduce credential generations and rotation coordination shared by all TgData
clients and backends.
**Why this is long term effective:** would support explicit live rotation across
arbitrary callers, beyond this pool's exclusive-owner contract.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit credential generations only when live rotation across multiple independent client owners is requested; #7 remains paused and no new prerequisite is introduced.

## Execution preconditions

E1 unchanged: two approved distinct authenticated accounts/shared group and bounded
allowance gate step9. User confirmed one account for now and offline-first delivery.
No live work required or authorized for the current implementation run.
