---
model: gpt-6-astra
effort: xhigh
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the real SDK/verified-operation composition cannot produce day-distributed valid raw records under the proposed source bounds, preserve #44 page semantics, or retain original failure/cancellation with earlier captured work.
Affordable now: yes — local real-component prebuild, minutes of development and bounded execution; no Telegram credentials/network required.

Experiment: work-folder prebuild.py combining actual Telethon1.45 request dispatch/MTProtoSender/TL decoding, StoredSession, SQLite ReadBudget, owned health, heartbeat/cleanup and current raw-record projection; source-side date/ID reply model plus explicit adversarial packets. Include proposed narrow validator with activity parity and content projection, the selected first-visit policy, bounded quota/rank arithmetic, canonical capture/replay feasibility and source/settlement/cancellation failure histories.
Cost: local development; under two minutes runtime target, no live access.
Must precede: step1 and all product edits. The plan already places the experiment there; this verdict enforces the still-unrun gate, rather than treating its planned existence as proof.
Disqualifying result: after correcting probe setup only, the actual SDK/projection/owner/allowance/lifetime composition cannot support the specified capture or shared validator without replacing the plan's source/value/lifecycle split.
Passing result: one combined run passes activity structural parity, decoded ordinary/service/photo/document projection, day seeks/ties/busy-empty allocation and finite calls, raw/selection/replay math, owner/quota/heartbeat and partial failure/cancellation outcomes. Source packets alone and arithmetic-only models are non-covering for SDK composition and never establish live visibility.

Result: PASS — eight combined real-component groups passed on the first run, including66 calls/660 slots/599 captured/300 selected and6875 quota cases; 2026-10-16T08:12:16Z. Synthetic source packets, no live Telegram.

## High-level summary
The contract and implementation shape survive. Two Medium details need focused correction: avoid wasting the first page on empty-day history when another request round is affordable; bound the exact water-filling level domain. No High or Low finding. No external planning blocker. Optional live qualification remains unavailable and is not mislabeled as passed.

## Premise Inventory — ranked by waste if false
### P1: shared source structure and raw projection
First dependent step1, then2–5; false premise wastes the core implementation. Scheduled beforestep1 but unrun. Cheapest test: proposed common validator against current activity _page, then real decoded source records through batch_engine._record/_validate_record and actual owned client. Existing suites34/46 cover the current components but not this new multi-day composition. Fake clients or helpers returning already-prepared records are non-covering.
### P2: day allocation under actual source cost
First dependent step3; false premise changes scheduler policy and its evidence. Scheduled combined prebuild and public suite47. Cheapest test beforestep1: source-side offset model delivered through real SDK/SQLite, including59 empty requested days with older history and one599-message day. Current plan arithmetic demonstrates wasted cost; real component execution must validate the selected correction, not merely restate it.
### P3: deterministic allocation/replay
First dependent step2; false formula/normalization changes pure selection and hashes. Cheapest test: exact arithmetic over empty/full/uneven capacities plus raw-record canonical reload, then public47 after implementation. Rank-spacing3160 combinations already pass, but that does not prove quota-level termination or capture validation. The new bounded level domain must be exercised before product code.
### P4: live server and runtime qualification
First dependent step3. Vendor date/offset contract and SDK1.45 are inspected; actual live visibility is not tested. A bounded live comparison requires qualified session ownership/allowance not available now. Native Python3.7 execution is also unqualified; grammar checks are not a substitute. These are declared evidence limits, not new findings or reasons to invent a fake PASS.

## Restart Check
Consumer599/300 newest-prefix defect: integer stride1 plus truncation → step2 even ranks and day allocation.
Missing earlier days under a source cap: newest-only acquisition cannot create unseen candidates → step3 independent day opportunities.
No prior #45 failed implementation exists. The two findings below refine this layer, not a restart of unrelated source infrastructure.

## Inherited Lessons
Returned rows do not bound empty requests → separate max_requests in step3, proved beforestep1.
Same query is not same captured input → strict retained value and no selection-time clock in step2.
Raw omissions are not source progress or whole posts → separate envelopes/unit/album metadata in step2, no progress calls in steps3–4.
Account ownership/cleanup must survive failure → actual component probes beforestep1, same operation in step4.
Shared validation must not import counters into content selection → independent projection and parity beforestep1, unchanged activity regression atsteps5–6.

## Risk 1 — first pages can spend the allowance on empty days
**Risk**

A requested day with no messages can still return a full page of older history. Giving each such day a large first page spends the finite reading allowance on material that cannot enter the sample. A period with many quiet days can therefore return only a small fragment of its one busy day even though the allowance was large enough to capture all useful messages.

Step3's first-request limit `min(100, remaining_slots//remaining_visits)` in planned history_capture.py does not distinguish an unvisited bucket from continuing a known populated day. A plan-arithmetic probe with max_messages3000/max_requests100,59 empty requested days with abundant older history and one599-message day uses3000 slots in60 calls and retains only50 in-window messages. This is a source-policy cost problem, not a false-completeness claim.

**Severity:** Medium
**Category:** Source work efficiency / useful coverage
**Impact:** avoidable quota consumption and preventable sample underfill on sparse periods.
**NoobEng:** GetHistory's date offset seeks before the day's end, but it does not stop at the day's start; one older message already proves that an empty day has been passed.
**Affected areas:** planstep3 acquisition policy and step5 sparse/busy source tests.

### Mitigation — Quick
Document that quiet days may waste the allowance and recommend increasing max_messages.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust
On a bucket's first visit request one slot when remaining_requests is greater than the remaining planned visits in the round, leaving capacity for a later depth pass. Otherwise use the existing fair page size so a caller permitting no further round can use its last allowed page. Subsequent visits use the fair bounded page rule. Prove the60-day sparse case retains599 useful messages with less than1000 raw slots and at most100 logical calls; also test no-spare-request and tiny-cap cases.
**Why this is robust:** one older row can close an empty bucket cheaply, while the explicit no-spare-request branch avoids imposing a one-message sample on a one-call policy. It fixes the new collector's scheduling policy without changing shared validation or existing readers.
- [x] selected   - [x] elegant   - [ ] last_resort
**Note**
*Why chosen:* Phase3: no genuine shared class exists. group_activity.py is a single-window census observation, while BatchEngine has forward cursor semantics; one scheduling mechanism would need policy-specific branches. The one-slot probe belongs only in the new day collector and has the best reach/extent. No external blocker forces this choice.
*For future:* —

### Mitigation — Long-term
Build an adaptive acquisition planner using historical density estimates and per-bucket cost predictions.
**Why this is long term effective:** could optimize many selection policies if concrete consumers later share those predictions; no such common planner or stable density evidence exists today.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

## Risk 2 — the quota-level domain is undefined for a full selection
**Risk**

When the caller requests every eligible message, increasing the allocation level never exceeds the target. A rule that searches for the largest permitted level therefore has no finite answer unless its domain is explicitly bounded. An implementation could loop forever or choose an arbitrary stopping convention for a normal input.

Step2 defines the largest integer L with sum(min(day_capacity,L))<=target, without an upper bound. For capacities[1,2] and target3, levels2,3,100 and1000000 all satisfy it. The rank-spacing probe did not test this separate allocation condition. The new quota helper in history_sample.py needs an exact finite domain and empty/full cases before implementation.

**Severity:** Medium
**Category:** Algorithm definition / termination
**Impact:** ambiguous or nonterminating full-population selection; inconsistent behavior across implementations.
**NoobEng:** water filling caps each bucket at its available count; once every bucket is full, raising the hypothetical level changes nothing.
**Affected areas:** planstep2 quota helper and step5 deterministic selection tests.

### Mitigation — Quick
Special-case the common default sample size and rely on an arbitrary loop ceiling.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust
Handle target0 and target==sum(capacities) directly. Otherwise search L only in [0,max(capacities)] using integer binary search; construct quotas and evenly spaced residual allocations exactly as planned. Test empty, all-zero, full and partial populations with conservation, per-day capacity and deterministic remainder properties.
**Why this is robust:** makes the existing algorithm total and finite without changing the chosen sampling policy.
- [x] selected   - [x] elegant   - [ ] last_resort
**Note**
*Why chosen:* Phase3: no other equal-day allocator exists. Source page fairness and existing progress budgets do not solve this quota problem, so a generic library would manufacture coupling. A finite-domain local helper permanently closes this instance with minimal extent; selected/elegant, not last_resort.
*For future:* —

### Mitigation — Long-term
Introduce a generic allocation library with formal policy interfaces for every reader.
**Why this is long term effective:** could centralize multiple true allocation consumers, but none exists beyond this new selector and source page fairness uses a different mechanism.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

## Scope and limits checked
No schema migration, new dependency or existing receipt format change. Capture/sample values expose original content deliberately, with no logging of it. Canonical hashes identify observations rather than authenticate Telegram origin. Native limits are counts/calls, not strict byte/RSS guarantees; reload has its own explicit byte bound. Literal repeated IDs and contradictory saved evidence already refuse. Sharing the small validator preserves activity projection/error behavior; a full engine rewrite is unnecessary. No speculative Low findings added.
