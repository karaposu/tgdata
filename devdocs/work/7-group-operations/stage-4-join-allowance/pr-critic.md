---
model: gpt-6-astra
effort: max
---
**Verdict: IMPLEMENT AS WRITTEN — accept the implemented Stage4 diff with the Low below consciously retained.**

**Gate: ACCEPTED — 0 High, 0 Medium, 1 Low.** CONTRIBUTING §7.3 permits the
recorded Low; this is not permission to merge without the user's go-ahead.

Falsifier: a real competing admission exceeds the cap, an uncertain return allows
another caller to reuse its charge, or a supported ledger transition disagrees
materially with the stated accounting contract.
Affordable now: yes — additional real SQLite/process probes, performed before this
verdict. Result: six assurance groups passed, including600 model transitions;
the seventh probe reproduced a fractional-deadline discrepancy rated Low below.
No unrun affordable experiment remains between this verdict and its premises.

## High-level summary

Reviewed [PR24](https://github.com/karaposu/tgdata/pull/24)'s implemented diff at
head9861573, productde1f758, against dev1ce39d5 and the revision2 plan8d5a256.
This is a **fresh in-session** critic-d review, not delegated and not the earlier
plan critique or merge-check relabeled. Full changed runtime/tests/docs were read;
actual ReadBudget, SQLiteSyncStore custody/cleanup, health classification and
packaging/export behavior were refreshed. Review model/effort is the current
session's verified gpt-6-astra/max (see merge-check §9 provenance).

The dedicated ledger is proportionate:311 new runtime lines, no new dependency,
no backend framework, no refunds/receipt lifecycle, no client/health changes. Its
unit is admitted attempts, which it can establish locally. It does not pretend
to know a remote membership result or to guard requests before Stage5 exists.
Explicit provisioning and validation-before-pruning answer the old ledger's
reproduced reset/data defects. A verified-account consumer remains the next
stage's responsibility rather than being silently assumed implemented here.

No High or Medium defect was established. The one Low is an exact-boundary rounding
mismatch between pruning and the advertised retry time for certain fractional
clocks. It refuses conservatively; the observed delay is one representable float
step, not a lost charge or excess admission. No runtime/test patch was made during
this review. The accepted product remains de1f758.

## Premise Inventory

### P1 — Concurrent provisioning and claims preserve one allowance

**First dependent step:** plan2/3. **Waste if false:** storage/operations/tests/docs2–5.
**Scheduled test:** inquiry before implementation, plus suite35 and this review.
**Cheapest earlier test/cost:** actual SQLite writers, seconds, no external access.
**Coverage:** prior probe six writers/cap3, suite35 admissions on an existing ledger;
fresh `provision_race` adds a barrier BEFORE constructing a missing shared file,
then real configure+claim in each process. Six workers admitted3 and persisted3.
This observes the real constructor/transactions; no stand-in grants capacity.

### P2 — Persistence and uncertainty do not grant a free retry

**First dependent step:** plan2/3. **Waste if false:** fundamental claim contract2–5.
**Scheduled test:** prebuild/implementation process exits, additional review probes.
**Cheapest earlier test/cost:** real SQLite busy commit and competing uncertain
return, about5s for the configured lock timeout. **Coverage:** actual native commit
failed behind a held reader, raised local storage error, persisted0, and allowed
a later retry after rollback. A separate writer really committed/closed, then a
hook delayed and failed its return while another caller attempted: the competitor
was denied and the charge remained1. The close error was injected; storage and
the competing decision were real. Physical power failure is not qualified.

### P3 — Policy/time transitions and retry estimates match the contract

**First dependent step:** plan3. **Waste if false:** operation/status consumers3–5.
**Scheduled test:** suite35, plus fresh reference-model/deadline probes here.
**Cheapest earlier test/cost:** deterministic model checked against actual API and
SQLite, seconds. **Coverage:**600 seeded transitions across3 accounts, including
196 configurations,191 observations,49 admitted/164 denied claims, backward/forward
clock movement and reopenings matched independent state/expiry simulation. The
model is an oracle for transitions, not a substitute for actual storage durability.
The separate nonbinary fractional deadline probe found Low1; it does not invalidate
capacity safety. Existing quarter-second tests missed this numerical case.

### P4 — Same-file coexistence, local errors and public integration

**First dependent step:** plan2/5. **Waste if false:** storage/export design and docs.
**Scheduled test:** prebuild actual ReadBudget composition, suite35, fresh review.
**Cheapest earlier test/cost:** actual package imports/read settlement/SQLite file
operations, seconds. **Coverage:** fresh test retained read usage2, join usage3,
and an unrelated customer table. A genuinely non-SQLite file was refused with
sanitized DatabaseError while raised inside an actual Telethon-error handler;
health.classify returnedNone and file bytes were unchanged. Existing exported-tree
test35 and package discovery cover the new module's public import path.

### P5 — Operating assumptions, not unqualified guarantees

**First dependent step:**2/3 and futureStage5. **Waste if false:** clock/storage or
future-consumer behavior outside this stage. **Scheduled test:** bounded local
behavior here; future sender qualification belongs to Stage5. **Cheapest earlier
test:** none can prove future host-clock accuracy, file custody or remote retry
integration for code not in this delivery. **Coverage:** explicit limitations in
desc/plan/public docs. No new vendor behavior is claimed. Arbitrary external edits,
old-backup substitution, cross-host filesystems and live safe-rate efficacy are
not silently promoted from offline tests. These are not execution blockers for
the standalone local primitive.

## Restart Check

| Observed prior failure | Established mechanism | Delivered response |
|---|---|---|
| Dropped attempt table reset usage | Old constructor silently recreated it | Full owned namespace/schema required; create=True only initializes wholly absent namespace; suite35 tests refusal without repair |
| Invalid negative/future timestamps hidden or accepted | Old observation pruned/advanced without prior-horizon validation | _observe checks type/range/prior clock before either mutation; suite35 asserts rows unchanged |
| Broad #7 stale account summary | Cached owner differed from fresh authenticated source | Stages1/2 already merged; Stage4 has no health/client authority and docs require a verified Stage5 owner |
| Broad #7 operational source errors relabeled | Group wrapper translated RPC failures as reference errors | Stage3 already merged; this stage changes no group/source wrappers, local errors suppress ambient health context |

The first two are fixed in this diff. The latter two are closed prerequisites,
not claimed newly fixed by the allowance module. No historical failure was used
to justify rebuilding an unrelated layer.

## Inherited Lessons

| Lesson | Actual ordering or structural boundary |
|---|---|
| Old review acceptance is not new correctness evidence | Dedicated inquiry/prebuild probes before product; fresh probes here against actual new API |
| Unknown remote result cannot justify a refund | Atomic admitted-attempt unit has no settlement/refund API; actual lost-return competitor cannot reuse charge |
| Status is advisory, not permission | _claim checks/inserts under one writer lock; model and process probes exercise this |
| Check damage before maintenance conceals it | Prior clock and rows validated before UPDATE/DELETE; no automatic schema repair |
| Ownership must precede mutation | Account/health foundations merged first; Stage4 accepts a supplied key and makes no authenticated-owner claim |
| Keep scope small and qualify real components | Separate ledger, no generic quota framework; native SQLite busy commit and actual processes, not only mocks |

## Low 1 — Fractional expiry can report zero delay while still refusing

**Risk**

A caller using a fractional test clock can retry at the exact time the allowance
reported and still be refused, even though the new error says to wait zero seconds.
Advancing the clock by the next representable instant releases the slot. This can
surprise deterministic-clock consumers or tests. The reproduced delay is about
14 picoseconds, so it does not represent a practical extra wait with a moving wall
clock, and it cannot allow an extra attempt.

`tgdata/join_budget.py:272` prunes using `admitted_at <= now - WINDOW_SECONDS`,
while `:280` returns `admitted_at + WINDOW_SECONDS` and `JoinBudgetStatus.retry_after`
at`:87–93` subtracts that hint from observed_at. These are not inverse floating-point
operations for every accepted epoch. With admission1000.2, next_available_at87400.2,
and clock set to that hint, subtraction yields1000.1999999999971: the claim remains,
_claim raises JoinBudgetExceeded, and retry_after is0. `math.nextafter` of the hint
advances by1.4551915228366852e-11s and status then reports remaining1. Existing
test35 uses exactly representable .25 fractions for the boundary case.

**Severity:** Low
**Category:** Numerical precision / retry hint
**Impact:** deterministic clocks can produce a zero-delay refusal at the exact
returned deadline; real-time admission remains conservative. No excess usage,
credential exposure, source mutation or durable-state reset was found.
**NoobEng:** the same mathematical deadline is computed by addition for the hint
and subtraction for deletion. Binary float rounding can leave the stored value
just above the computed cutoff even when now equals the advertised hint.
**Affected areas:** local JoinBudget status, exhaustion hints and synthetic clocks;
the structural pattern also exists in ReadBudget, which this stage does not modify.
**Recommendation:** when addressing exact numerical boundaries, derive expiry
comparison and retry hints from the same rounded representation, and test a
nonbinary fraction. Do not add a quota framework or patch unrelated budgets here.
**Disposition:** consciously retained under §7.3; no required mitigation tiers for
a Low and no runtime edits during review.

## Probe record and verification limits

Saved `pr-critic-probes.py` and `evidence/pr-critic-probes.txt`, run with the project
Python3.11.10/Telethon1.45.0/SQLite3.45.3. All seven groups completed (six assurance
checks, one finding reproduction). Selected actual output:

```json
{"probe":"provision_race","workers":6,"admitted":3,"persisted":3}
{"probe":"reference_model","transitions":600,"accounts":3,"admitted":49,"denied":164}
{"probe":"native_busy_commit","error":"JoinBudgetStorageError","native_wait_seconds":5.215,"after_failure":0,"after_retry":1}
{"probe":"lost_return_competitor","first":"storage_error","competitor":"denied","persisted":1}
{"probe":"fractional_deadline","hint":87400.2,"remaining_at_hint":0,"retry_after":0,"outcome_at_hint":"denied","remaining_after_tick":1}
```

The record above selects fields for readability; the evidence file retains full
machine output. No real account, login, group join or message read was performed.
The earlier529 offline passes/3 live skips,3 demos and exported-tree run remain
applicable to the unchanged product, not newly rerun counts. Native Python3.7,
physical power loss and cross-host coordination were not tested or claimed.

## Selection pass and gate action

No Medium/High proposal selection is required. Low1 is retained as stated; no
speculative class-wide redesign is smuggled in. Both merge gates now pass for the
reviewed product once this critique is committed and posted. Keep #7 open for
Stage5, retain the archive branch, and wait for the user's merge instruction.
