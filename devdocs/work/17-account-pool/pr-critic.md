---
model: gpt-6-astra
effort: max
status: REJECTED
round: 2
---
**Verdict: REORDER — TEST BEFORE BUILD**

Falsifier: an internal shutdown waiter consumes a cancelled public read's completed
data before its actual caller receives the cancellation. Affordable now: yes — actual
SDK/SQLite/task composition, no network/access cost; executed below.

Experiment: complete an actual source batch, hold its pool-store settlement, initiate
external close, and release an actual SQLite commit from provider finalization. Compare
a caller already waiting on the read with a caller awaiting it after close's waiter
registered. Repeat for raw/daily/backfill and with/without repeated close cancellation.
Cost: seconds offline with actual Telethon1.45, native disconnect, ReadBudget and SQLite.
Must precede: PR acceptance and any replacement implementation; in this implemented-diff
review this is a soundness gate, not authorization to patch the product.
Disqualifying result: data exists on cancellation before the public task ends, but is
missing from the caller's exception, while no pending delivery can supply it.
Passing result: shutdown only observes quiescence and the public caller retains the
promised completed records independently of internal-waiter ordering; genuine caller
cancellation, physical cleanup, charges and uncertain writes remain conservative.
Result: **FAIL on the reviewed implementation**,2026-10-13. Two full probe runs pass7/8
groups. Twelve isolation histories reproduce6 lost-payload cases and6 positive controls.
No candidate fix was implemented or qualified; the next design must pass this history.

**PR decision: REJECTED — zero High, one Medium, zero Low.** Any Medium rejects under
CONTRIBUTING §7.3. This is the **second rejected PR round** on this branch, so §7.4
requires returning to desc/traverse before another plan. Do not apply a piecemeal
patch or mark the earlier fidelity PASS as merge approval. PR26 stays draft.

## High-level summary and subject

Reviewed the entire21-file product diff dev2ddb852...a63099e with folded plan revision5,
desc revision4, original feature/retirement artifacts and the failed r3 evidence.
Same warmed session; no delegated review. Prompt9cc5909 follows renewed merge check
1c04cf4. These heads change work documents only; product remainsa63099e throughout.
Current dev and model/effort were verified; GPT-6 Astra/max meets §9.

The source/store interruption solution holds in the new races and double-store faults.
The failure is at the next boundary: **observing a public task's completion is not the
same as consuming its cancellation outcome**. The implementation preserves data on a
CancelledError inside the reader, but close awaits and discards that object. Python's
actual Task can deliver a fresh cancellation exception to a later waiter. The caller
then receives no completed data. No unsafe source retry or quota release was observed;
this is an outcome-delivery defect, rated Medium.

The725 implementation checks and48-group prebuild remain valid for their tested cases.
They did not combine external shutdown, completed data and public-waiter ordering.
This finding does not justify replacing routing, budget storage or the progress engines.

## Premise Inventory

### P1 — Joining a cancelled public task leaves its attached data available

**First dependent step:** plan3/4, source/caller result retention and close's retained
`await active`. **Waste if false:** the public cancelled-result guarantee and its
shutdown qualification. **Test scheduled:** P0/steps6–7 retained repeated cancellation
and shutdown, but did not vary which waiter consumes the public task first.
**Cheapest earlier observation:** actual public read plus external close during actual
store finalization; executed here. **Coverage:** baselineFAIL; first-waiter controls
prove the difference. Tests that await a cancelled read only once without close are
non-covering for this combination. Python3.11's installed pure-Python Task/Future source
explains the mechanism; the `_asyncio.Task` probe confirms the runtime actually used.

### P2 — Component interruption stays local while genuine caller stop wins

**First dependent step:**2. **Waste if false:** source/provider ownership abstraction.
**Test scheduled:** P0 before runtime; permanent suite39; fresh PR probes now add
commit-then-parent-cancel with/without a simultaneous provider-internal cancellation.
**Cheapest earlier test:** actual CAS/SDK with independently scheduled cancellation;
seconds, executed. **Coverage:** holds at admission and settlement. Cancelled admission
sends0 source reads/charges; cancelled settlement retains data until the separate P1
consumer boundary. Source-internal interruption before identity stays local/unresolved.

### P3 — Data, permission, receipt and cleanup remain separate in composition

**First dependent steps:**4–5. **Waste if false:** account and group recovery semantics.
**Test scheduled:** full P0 and regressions; fresh paired-store failures/receipt probes.
**Coverage:** eight actual double-store combinations retain100 messages and the original
FloodWait through read_error chains, charge200, no second account. Stored token/wait
matches real commit history. Two receipt probes refuse the interrupted-error hash and
accept only the actual pending full/end batch receipt, source-free after close.
Actual late commits and native retirement finish even under repeated close cancellation.
The quiescence guarantee holds; P1 shows its implementation consumes something else too.

### P4 — Passive observations, compatibility and live service qualification

**First dependent steps:**3/6; actual live qualification8. **Waste if false:** reporting
or deployment claims, not a new reason to redesign the router. **Test scheduled:**
P0/39 and full existing suite, then E1. **Coverage:** fresh full-buffer loss still leaves
actual wait7200/data100/charge200 unchanged. Existing malformed/alias/legacy callback
controls remain;15 adjacent modules are byte-identical to dev and86 Python hashes match
verification. E1 is still unavailable under one-account/offline-first; synthetic wire
is explicitly non-covering for live two-account/proxy/visibility claims.

## Restart Check

| Observed failure | Established mechanism | Design element and review result |
|---|---|---|
| Reuse during cancelled native retirement | SDK shield outlived public await | Retained physical retirement/quarantine; still holds |
| Repeated cancellation released source work | Interruptible cancellation waiter | Private captured child and retained join; still holds |
| Observer cancellation/timeout hid source result | Composite task status substituted for body outcome | Body holder and passive observations; still holds |
| Callback shutdown formed a cycle | Reader/observer/close dependencies | Arbitrary observer execution removed; provider scopes/role remain |
| Drain during shutdown hid cancellation | Busy gate on local data | Synchronous all-state drain; retained tests hold |
| Provider cancellation hid completed data | Inline storage CancelledError looked like caller stop | Owned provider boundary; fresh paired-store failures hold |
| Status provider performed account control | Source-only busy check | Same-pool scope checked at operation entry/close;45 retained controls |
| Caller loses cancellation payload during close | Close consumes public Task's saved CancelledError | **Not addressed**: Risk1; task completion and outcome consumption conflated |

## Inherited Lessons

The plan correctly moved from task-status-as-source-outcome to captured component
outcomes and tested storage before building. It preserved no-rollback/no-receipt rules,
kept retained cleanup and removed observer cycles. The latest evidence extends the
same ownership lesson to **who is entitled to consume the public task's outcome**.
The next upstream description must express that distinction; its counterexample must
precede any replacement implementation. More passing internal-boundary tests cannot
establish a caller-delivery property they never observe.

## Risk1 — Shutdown consumes the read's completed-data cancellation payload

**Risk**

An application can stop the pool after Telegram has returned messages but while the
account's status is still being saved. The read correctly attaches those complete
messages to its cancellation exception. Shutdown also waits for that read, however,
and can receive the exception first. A caller that awaits the read afterward receives
a different cancellation exception with no messages. Daily and backfill calls have
not saved a pending delivery on this genuine cancellation path, so replay cannot supply
the already-observed data either. Availability depends on which waiter happens to run
first, despite the new promise to preserve known records through cancellation.

`AccountPool.close.finish` at `tgdata/account_pool.py:594–600` cancels then directly
awaits `_active_task`, discarding CancelledError. `_settle` at446–451 and `_OwnedSource.run`
at `tgdata/pool_source.py:164–167` attach `partial_result` to that cancellation instance.
On actual Python3.11 `_asyncio.Task`, the saved cancellation exception is consumed by
the first waiter; a later waiter gets a fresh instance without attributes. The library's
own close task becomes that first consumer when the app has not yet awaited its read.
`SyncEngine.prepare:149–150` and the corresponding backfill cancellation branch correctly
avoid fresh publication, leaving no durable pending fallback. This is not a bad provider:
the provider performs and settles actual storage only; external application code closes.

**Severity:** Medium
**Category:** Outcome ownership / cancellation / delivery
**Impact:** completed records are withheld from the public caller during normal shutdown;
re-fetch may be necessary and need not see identical history. Stored permission, quota,
cleanup and unadvanced group progress remain conservative, so this is not rated High.
**NoobEng:** CancelledError is both a control signal and, here, a temporary data carrier.
Python does not promise that every await of a cancelled Task raises the same object.
An internal component waiting only for termination must not consume the payload whose
owner is the application. The private child helper already avoids that ambiguity, but
the public reader task remains a separate boundary.
**Affected areas:** AccountPool.close, raw reads, daily/backfill prepares, documented
completed-data retention and the cancellation/shutdown acceptance matrix.

### Reproduction and evidence

Fresh full probes: `probes/review2/run.py` →7/8; twice, no watchdog. The failed group
had real source_reads1, charge1, settled account state and public_prefix0. No runtime
patch or changed assertion. The second run only added observation fields; the first
exact probe is preserved with its SHA256.

`probes/review2/cancel_payload.py` further records:

```text
_asyncio.Task: first waiter has payload; second waiter does not; different objects.
raw/daily/backfill, close waiter first: inner prefix1, caller prefix0, no pending.
raw/daily/backfill, caller waiter first: inner prefix1, caller prefix1, same exception.
```

Each mode runs with and without cancelling close repeatedly:6 failures and6 positive
controls. In all12, real SQLite settlement completes, charge1 remains and both native
clients retire. An instrumented caller wrapper sees the actual prefix before Task
termination; it supplies no batch or receipt. Installed asyncio source corroborates
its saved cancellation exception being cleared on retrieval; no Python3.7 behavior
is inferred from a grammar check.

- [Fresh complete probe output](evidence/review2/pr-attempt-2.txt)
- [Exact source/probe hash and failed group](evidence/review2/pr-attempt-2.json)
- [First probe before added logging](evidence/review2/pr-probes-attempt1.py)
- [Twelve isolating histories and actual Task control](evidence/review2/cancel-payload.txt)

### Mitigation — Quick

Require callers to wrap every pool read, capture cancellation data inside that wrapper,
and register the public receiver before another task can close the pool.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Make the internal close coordinator observe reader termination without consuming its
cancelled public outcome. Define which component owns result consumption independently
of who may stop/join work. Handle ordinary unobserved failures without retrieving and
swallowing the saved cancellation payload. Qualify late public waiters in raw/daily/
backfill, source and storage phases, both commit outcomes and repeated cancellation;
keep exact source/ledger/cleanup and caller cancellation behavior. This is an input
to the required upstream requalification, not permission for a patch in this review.
**Why this is robust:** addresses the actual shared close entry for all three affected
public readers, with no additional result store or global task supervisor.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Long-term

Introduce a stable public operation/outcome handle with separately retrievable data,
independent of Task exception consumption, across queued/raw/progress operations.
**Why this is long term effective:** supports multiple independent consumers and later
retrieval if those become explicit product requirements, rather than transporting data
through cancellation exceptions. It expands the public lifecycle/delivery contract.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Preconditions and procedural result

E1 remains pending exactly as before: two approved logged-in accounts, shared group,
existing bounded allowance. No live access or quota reset occurred. Main checkout,
duncan and unrelated files are untouched; product remainsa63099e.

Per CONTRIBUTING §7.4 this second rejection returns to the description/foundation
inquiry before another plan. The first plan critique, this PR review and their evidence
stay distinct. No new implementation, re-plan or production patch is performed here.
