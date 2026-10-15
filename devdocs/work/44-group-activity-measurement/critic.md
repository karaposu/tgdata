---
model: gpt-6-astra
effort: xhigh
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the actual verified-client/SDK/SQLite composition loses raw page evidence, mischarges owner/slots, or replaces cancellation/original failure during raw history collection.
Affordable now: yes — local Python/SDK probes, minutes, no Telegram or credentials.

Experiment: `prebuild.py` in this work folder, actual TelegramClient dispatch, TL codec, MTProtoSender result handler, StoredSession, SQLite ReadBudget, `_account_health_operation`, heartbeat and SDK disconnect. Synthetic server packets only; no fake client/allowance/lifecycle supplying the premise.
Cost: local development and under two minutes runtime, no remote account access.
Must precede: step1 and every product edit. The plan already names this ordering; this verdict makes the outstanding experiment a hard execution gate rather than treating its planned existence as evidence.
Disqualifying result: after correcting only probe-setup mistakes, raw SDK calls cannot retain source row/response evidence under existing owner/admission/cleanup contracts, or decoded request precision cannot support the planned conservative seek. That changes the collector composition and invalidates the plan.
Passing result: one combined run passes raw paging/codec/date/optional-counter preservation, actual owner and allowance, error and heartbeat/cancellation/cleanup histories; all observations match declared outcomes. Fixture source packets do not qualify live Telegram order/visibility.

Result: PASS — seven combined groups passed with real Telethon1.45.0 dispatch/codec, stored sessions, SQLite budget, owned health, heartbeat and cleanup; 2026-10-15T20:17:11Z. No live source evidence.

## High-level summary
The plan's shape fits the inquiry and existing lifecycle. One Medium performance detail should be folded; no High or Low finding. The unexecuted combined prebuild must run before any product step. Live verification remains optional and unqualified, not an invented hard blocker. No PR review is implied by this plan critique.

## Premise Inventory — ranked by waste
### P1: raw history composition
Premise: raw GetHistory retains rows/page types and traverses existing verified-owner, budget, heartbeat and cleanup seams correctly. First dependent step1 (value evidence), then2–4; waste if false: most implementation/tests. Test scheduled before step1, currently unrun. Cheapest earlier test: combined prebuild described above. Coverage: existing32–34/45 suites cover components and isolated calls but not this measurement paging composition; non-covering for the full premise until run. A fake result provider bypassing actual SDK/admission would not close it.
### P2: vendor paging and visibility
Premise: GetHistory follows its documented descending date/offset contract; source may hide/delete rows and is not a snapshot. First dependent step2; waste if stronger assumptions false: collector and summaries. Test scheduled: offline boundary/codec probes now, live comparison only when available. Cheapest earlier live check requires qualified account ownership/allowance not presently established; no accessible synthetic substitute proves server semantics. Coverage: official GetHistory/offsets documentation plus source iterator corroboration, not empirical universal proof. The plan makes conditional visible-history claims and validates observed order, with explicit live limitation. No premise of universal visibility is accepted.
### P3: budget request granularity
Premise: raw reads reserve the requested page size before send; a smaller remaining allowance can refuse despite a sparse response. First dependent step2; waste: public cap/allowance semantics if misunderstood. Test: prebuild beforestep1; cost one SQLite fixture. Coverage: `_BudgetSender` source directly confirms requested-limit reservation; iterator-only page shrinking does not apply to raw calls. Docs must say callers may lower max_messages or enlarge their configured allowance; no silent quota resize.
### P4: default/source version
Premise: cap3000 is useful as a default, not source proof; SDK1.45.0 is the supported qualification runtime. First dependent step3; waste low. Default is explicit configurable policy, not a claim to test against a vendor. Codec/runtime asserted by prebuild and suites; actual Python3.7 runtime not available, grammar only.

## Restart Check
The motivating consumer's cap hides partial coverage → bounded loops lack a completion flag → step2 source evidence and step1 qualified rates.
Zero views excluded → truthy `if p.views` filter → step1 known-value populations include0.
Unknown sender becomes one user → fallback `sender_id or 'anon'` → step1 distinct known IDs and separate unknown-message count.
No failed earlier #44 implementation exists. The plan addresses the observed layer rather than rebuilding unrelated orchestration.

## Inherited Lessons
Iterator exhaustion is not transparent coverage → raw page/placeholder probes beforestep1, validationstep2.
More rows do not prove a snapshot → fixed visible-history claim in description and source contract, no snapshot promise.
Cached identity is not ownership → real wrong/cached-owner probes beforestep1, unchanged verified operationstep3.
Partial source failure is not completion → original-error/accepted-prefix probes beforestep1, collectorstep2.
Existing v1/progress compatibility → separate value step1 and unchanged-path full regressionstep5.

## Risk 1 — aggregation cost can escape the source bound
**Risk**

A caller can request many years of history while allowing only a small number of messages to be read. If every daily result rescans every retained message, producing the statistics can take much longer than the bounded source read suggests. Repeating the same work for each metric and each day can stall other event-loop tasks after network work has finished.

Step1's `GroupActivity.statistics` in planned `tgdata/group_activity.py` specifies all intersected UTC dates and per-day author sets but does not bound arithmetic complexity. A straightforward days×messages filtering implementation rescans up to roughly25,000 daily buckets across the supported wire-date range; max_messages can be large. The statistics property and to_dict may repeat it.

**Severity:** Medium
**Category:** Performance / specification detail
**Impact:** avoidable event-loop stalls and CPU cost despite finite source requests.
**NoobEng:** source bounds constrain Telegram traffic; local aggregation needs its own efficient traversal. Group rows once and sort only counter populations for exact medians.
**Affected areas:** new measurement statistics, JSON export, step4 performance-sensitive boundary tests.

### Mitigation — Quick
Add a warning that wide windows may be slow.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust
Group ordinary rows into UTC-day accumulators in one pass, with global/daily author sets and four counter vectors. Emit daily buckets in one pass over dates; compute exact counter medians with at most four sorts. O(messages log messages + days), O(messages + days) space; do not rescan all messages per date. Add a wide sparse-window test with known output and one-pass structure checked in review.
**Why this is robust:** permanently removes the cross-product at its only new source without altering public semantics.
- [x] selected   - [x] elegant   - [ ] last_resort
**Note**
*Why chosen:* Phase3: no genuine shared class exists. utils.get_message_statistics uses a supplied DataFrame and different populations; progress/backfill track cursors, not daily analytics. A common mechanism would need per-case branches. One-pass local aggregation closes this instance with minimal extent; robust is selected/elegant, not last_resort.
*For future:* —

### Mitigation — Long-term
Create a shared incremental analytics accumulator for all statistical APIs.
**Why this is long term effective:** could centralize complexity guarantees if several APIs later share identical row/availability semantics; no such common class is established today.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

## Other review evidence and limits
No database schema change, dependency change or library version bump. Counter observations omit credentials/text/media; arbitrary metric/ratio language and future sampling machinery remain out. Existing profile partial-result pattern and verified cleanup are reused rather than replaced. Frozen primitive rows and detached dictionaries prevent mutable SDK object leakage. Mandatory protocol checks and page-atomic acceptance are already explicit, so not duplicated as invented risks. Full SDK runtime/owner proof remains the experiment above; no live result claimed.
