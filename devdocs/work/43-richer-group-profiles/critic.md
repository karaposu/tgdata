---
model: gpt-6-astra
effort: xhigh
---
# REORDER — TEST BEFORE BUILD

Falsifier: the actual Telethon full-profile/pin-search requests, through the
existing verified client and budget/heartbeat mixins, cannot preserve scoped
identity, bounded admission, source-error origin or cleanup cancellation as planned.
Affordable now: yes — local SDK1.45.0, existing real TL/wire harness, temporary
sessions/SQLite; minutes, no real login, network or money.

Experiment: prebuild.py executes full basic/channel metadata and pinned Search
through the existing verified/owned-health facade boundary and actual factory
mixins, with TL packets decoded by MTProtoSender. Exercise both session backends,
zero/absent fields, budget reserve/refund/refusal, changed identity before send,
wrapped source denial, heartbeat exception isolation and repeated cancellation
while SDK disconnect is held. Run foundational suites32/33/34/18/44 too.
Cost: local runtime and temporary files only; no credentials or live Telegram.
Must precede: step1 and all product changes.
Disqualifying result: a listed invariant fails in the unmodified composition;
or satisfying it needs a factory, ownership, health or budget design change.
Passing result: every listed composition probe and all five foundational suites
pass on1.45.0, the baseline product is unchanged and observed limitations match
the plan. Then fold the selected clarification and implement.

Result: PASS — six combined real-component probe groups passed, covering both
session backends and basic/channel replies; all198 checks in suites32/33/34/18/44
passed. Source hashes and git diff confirm no product edits preceded this gate.
2026-10-15. Evidence: evidence/prebuild/result.json and prebuild.txt. One fixture
constructor setup correction is recorded in prebuild-setup.md.

## High-level summary
The design is a bounded consumer of the settled #7 operation; no new persistence
or lifecycle is needed. One Medium contract ambiguity needs folding. A combined
prebuild is required before implementation. This review does not establish live
Telegram field availability or permission. No declared external execution blocker.

## Premise Inventory
### P1 — existing composition supports these request families
First dependent step1; waste if false: profile module/facade/test assumptions in
steps1–4. Scheduled at prebuild before product work. Cheapest test: actual SDK
TL decode and dispatch using existing account/health/budget/heartbeat code,
temporary actual SQLite and both session forms. Source inspection covers request
classes, schemas and Search admission; existing suites qualify individual seams,
not this combined request path. Synthetic server values do not prove live results.
### P2 — an observed count and its precision are distinct
First dependent step1 (value shape); waste if false: consumers/tests/docs in1–4.
Cheapest test: examine actual MessagesSlice/ChannelMessages.inexact alongside
count and unavailable rows. Documented constructors and SDK decoding cover the
representation; Risk1 addresses a missing public distinction.
### P3 — profile and filtered pins do not prove general history access
First dependent step3; waste if false: misleading health API. Covered by existing
owned-health semantic assertion contract and plan's explicit refusal to call it.
Prebuild observes existing denial retention after metadata/Search without a
confirm call. Server permissions may vary; no stronger inference is required.
### P4 — cancellation and observers remain outcome-neutral
First dependent step2/3; waste if false: all error/partial contracts.
Cheapest test: held actual disconnect and repeated cancellation with the existing
SDK/context, actual heartbeat sender and a raising callback. Scheduled in prebuild;
existing suites32/44 also cover individual mechanisms. No success-shaped stand-in
may replace SDK disconnect or budget admission.

## Restart Check
| Observed reference failure | Established mechanism | Planned response |
|---|---|---|
| Failed pin reads appear empty | reference measure.py catches Exception and leaves [] | step2 re-raises original error with completed profile partial_result |
Other downstream activity/sampling defects belong to #44/#45. The old broad #7
failures are covered by retained verified operations, not reopened in this plan.

## Inherited Lessons
| Lesson | Step/ordering that satisfies it |
|---|---|
| Cached identity is not billing/operation authority | existing verified context + prebuild before1; integration3/tests4 |
| Local failure is not a Telegram verdict | owned context unchanged3; error/health probes before1 and4 |
| Successful metadata is not history access recovery | no confirm_group_access in3; regression4 |
| No error means rollback is an unsafe storage assumption | no new storage; retain existing budget charges2 and prebuild |
| Fake source values do not establish live permissions | boundary declared before1 and in4/5 reporting |

## Risk 1 — the result loses whether the reported total is approximate
The caller can receive a number of pinned messages without knowing whether that
number was exact. An incomplete collection can mean either an approximate source
count or unavailable message contents. Using the same status for both leaves a
consumer unable to label its total honestly.

Step1's GroupProfile contains pins_total and pins_status, while step2 retains
MessagesSlice/ChannelMessages.count when inexact=True and labels both that case
and MessageEmpty rows incomplete. No result field preserves the source's precision
flag. For example count=10 with inexact=True is indistinguishable from exact
count=10 plus unavailable content using only that total/status pair.

**Severity:** Medium
**Category:** API contract / information loss
**Impact:** downstream reports may present an approximate number as an exact total.
**NoobEng:** Telegram marks some search totals inexact. Content completeness and
count precision are independent; one combined status cannot represent both.
**Affected areas:** new profile value/projection, public serialization, tests/docs.

### Mitigation — Quick
Add a documentation warning that every incomplete result's total may be approximate.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust
Add nullable pins_total_exact: None without a successful pin response, True for
an exact count/full vector, False for an inexact count. Preserve status independently.
**Why this is robust:** carries the source evidence through this new value and
keeps unavailable content distinct without changing existing APIs.
- [x] selected   - [x] elegant   - [ ] last_resort
**Note**
*Why chosen:* No second implemented precision-aware count API is in scope. This
is the smallest permanent correction; a general wrapper would impose coupling
on existing basic metadata and hypothetical #44 output.
*For future:* —

### Mitigation — Long-term
Introduce shared evidence/precision wrappers for all counts throughout tgdata.
**Why this is long term effective:** future measurements could share a vocabulary
for approximate, absent and exact observations instead of adding field-specific flags.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* Revisit only if #44 establishes multiple actual consumers needing
one common mechanism. The proposed wrapper fails the current class/extent gate;
it is neither a prerequisite nor work to fold into #43.

## Other review conclusions
One filtered response is consistent with the requested bounded first delivery;
full pin pagination is not a hidden requirement. Reusing heartbeat_scope avoids a
new background task/wait policy. Basic online counts stay unknown. Full metadata
and pin evidence are separate observations; source changes between them are
documented. No source-success recovery is asserted merely for profile data.
Existing lookup/access and batch v1 serialization remain untouched.
