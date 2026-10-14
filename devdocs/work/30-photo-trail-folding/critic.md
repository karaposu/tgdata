---
model: gpt-6-astra
effort: xhigh
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the complete public value/inference/receiver candidate cannot preserve original data, enforce its chronology and bounded closed-scope contracts, and independently settle original daily/backfill receipts through restart, faults and late observations.
Affordable now: yes — one local isolated candidate build with actual SDK/SQLite/source engines; no account, network, spending or deployment required.

Experiment: build the complete candidate for plan revision1 plus the selected R1 clarification in a temporary package based on dev35c4362. Run all suite43 behavioral groups, the new demo and the existing raw/album/daily/window/backfill/pool regression suites together. Exercise actual public constructors/loaders/getters/serialization, original-member rule, complete SQLite selection/preflight/read/cleanup, original receipts, schema/corruption/collation cases, deliberately raised10001-member limits, process-loss and cancellation histories. Include the mixed-post/per-member chronology counterexample below as a required nonattachment case. Record exact candidate hashes and full results; the inquiry sketches do not satisfy this gate.
Cost: local candidate implementation and bounded offline test run; no external access dependency.
Must precede: production Step1 and every production adoption. The plan already requires a complete candidate; its actual result is still absent.
Disqualifying result: the selected original-facts/current-view/closed-scope/member-event architecture cannot meet these requirements without replacing its ownership, scope or ordering contract, relaxing original-data integrity, hiding a source read/receipt, or changing test expectations to bless a failure.
Passing result: the full actual candidate passes every named behavior with the R1 semantics, strict limits and unchanged source/receiver acceptance. Exact candidate files can then be adopted, followed by full verification. Local nonarchitectural wiring corrections are recorded; a structural failure stops task-impl.

Result: PASS — complete candidate53/53 new tests,14 related suites and2 demos (491 offline checks) passed; isolated no-Git/no-work-doc suite/demo also pass with exact matching hashes. R1 semantics included; no runtime correction or weakened assertion.2026-10-15. See prebuild/report.md and result.json.

## High-Level Summary

The selected architecture addresses the request without another state engine: immutable original posts feed a provisional replaceable view, and the existing receiver continues to own original acceptance. Closed interval refusal removes the inquiry's hidden-context counterexample. Original-member event evaluation handles interruptions that a post-level order misses.

One Medium detail must be made explicit before adopting the algorithm: a post that has no single eligible owner can still contain individual messages with known positive senders. Those known timestamps must contribute to each sender's chronology checks. The current inquiry sketch drops them, and an actual probe reproduces a backward-dated text becoming a new anchor. The ownership model and step sequence survive this clarification; no meaning-gap deprecation is warranted.

The complete public module/format/example is not built. Eleven successful contract histories do not qualify its serialization, raised-limit getters and full failure matrix. Execute the complete experiment before production, using the user's task-impl order Experiment→Fold→Implement→Verify. The draft plan's “after fold” experiment wording is superseded by that explicit orchestration and will be corrected during the later fold, without a second critique.

## Premise Inventory

### P1 — Complete public composition
Premise: the public values, deterministic rule, bounded loader and real source protocols jointly preserve the qualified contract. First dependent step:1. Waste if false: steps1–4 would need structural changes. Test scheduled: complete isolated prebuild before production1, then regression. Cheapest earlier test: the experiment above. Coverage: actual contract sketches establish the ownership/scope mechanism, but omit the complete public schema/options/corruption/cleanup matrix; they are non-covering for full implementation qualification. A fake receiver or supplied success result cannot close this premise.

### P2 — Chronology is tracked for original known senders
Premise: per-user backward-time refusal includes every individual raw member with that positive sender, even if the enclosing post is mixed/unknown and cannot itself anchor. First dependent step:2; step1's relation loader must use the same rule. Waste if false: misleading links, wire validation blessing them, and tests/docs repeating the omission. Test scheduled: general chronology/mixed-user cases in Step4; their combination was not explicit. Cheapest earlier test: actual SDK-derived mixed post followed by a regressed text and photo. Coverage: plan-critic-chronology-probe.py reproduces the omission in the existing inquiry sketch; R1 specifies the needed clarification. Existing single-owner backward-time test is a control, not coverage of this combination.

### P3 — View limits do not become receipt limits
Premise: new bounded projection remains separate from confirming fixed accepted input. First dependent step:3. Waste if false: receiver integration/recovery guide changes. Test scheduled: complete prebuild and actual daily/backfill cases. Cheapest earlier test: actual schema2 receiver confirmation while projection is forbidden or refuses aggregate scope. Coverage: inquiry probes already pass this seam on real receiver/source classes; complete adapter qualification still required. No new Telegram completeness or human-intent accuracy premise is used.

### P4 — Selected current scope is complete relative to known stored context
Premise: strict interval/post-extent checks plus one read snapshot prevent the adapter from silently excluding known intervening activity. First dependent step:3. Waste if false: selection and recovery interface changes. Test scheduled: prebuild. Cheapest earlier test: actual1,2,4 omission control, closed refusal and concurrent WAL growth. Coverage: counterexample retained, refined contract and fresh snapshot probes pass; complete type/key/collation/resource implementation still needs execution. This is not a claim about unseen Telegram history.

## Restart Check

| Observed failure | Established mechanism | Planned response |
|---|---|---|
| Consumer accepts video, backward time and channel identities | Actual helper uses media count, one-sided gap and non-null identity | Typed photo/positive-user evidence, exact chronology and conservative barriers |
| Consumer mutates originals and representative fixture repeats an ID | Actual helper mutates anchors; fixture11 members/10 distinct IDs | Immutable original posts, unique-ID fixtures and separate relation |
| Expanded selected album hides known intervening text | Actual seed1–2 query returns1,2,4 but omits3 | Explicit closed interval refusal with complete current posts |
| Post-level position hides a later unknown-author interruption | Album1,5 cannot be represented by one event at1 | Every original member event, decision at last current member |
| #29 old replay failed as current views grew | Recognition formerly depended on new projection costs | Byte-identical original acceptance; optional view read is separate |
| Mixed post hides a known user's previous timestamp | Inquiry chronology pass uses aggregate post owner | R1: raw member sender drives chronology independently of post eligibility |

## Inherited Lessons

Original facts and guessed associations remain separate; full value validation precedes adoption. Closed scope is tested with the retained failing query before product code. Source receipt authority is exercised through real daily/backfill engines, not inferred from a partial result. Raised limits must survive getters/reload, explicitly including10001 members. Complete prebuild precedes adoption; targeted inquiry probes cannot substitute for it. Unseen album membership and human intent remain unclaimed, with default opt-out and reversible views.

## R1 — A mixed post can erase known timestamp evidence

**Risk**

An album may be unsuitable for photo-trail inference because its records do not all identify one author. That does not make every individual author's timestamp unknown. If the algorithm ignores all timestamps in such an album, it can accept a later text whose timestamp goes backward for a known author, then attach another photo to that text. This violates the promised backward-time protection even though every original record remains valid and saved.

In traverse/contract_probe.py, infer's chronology loop uses `info['owner']`, the aggregate eligible owner. For an album containing member1 by user88 at10s and member2 by user99 at11s, that owner is None. Member3 by user88 at2s therefore sees no prior user88 timestamp and becomes an anchor; member4 at3s attaches. plan-critic-chronology-probe.py reproduces groups `((1,2),(3,4))` through actual Telethon-derived values and AlbumReceiver. The plan's “known user” phrasing needs to distinguish raw member sender from eligible whole-post owner so Step2 and Step1's loader cannot inherit this sketch behavior.

**Severity:** Medium.
**Category:** inference contract / chronology / plan precision.
**Impact:** a valid input combination bypasses a stated safety predicate and produces an unjustified link; source data remains intact and the view is replaceable, so no source data-loss claim is made.
**NoobEng:** whether a whole post can anchor a trail and whether one of its messages identifies a sender are different questions. The former can be unknown while the latter is known. Chronology should retain the individual known evidence even when the whole post is treated as an inference barrier.
**Affected areas:** proposed photo_trails.py chronology/validation, suite43 mixed-author chronology coverage; no existing source or receiver module needs changing.

### Mitigation — Quick
After any unknown/mixed post, disable all subsequent folding in that chat for the current view.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust
Track chronology using each raw member's own positive sender ID and timestamp, independently of the enclosing post's eligible owner. Preserve the existing whole-post eligibility/barrier rules. Add the reproduced mixed-user case and a partly missing-user variant; both must keep regressed text/photo separate. Keep ordinary subsequent monotone new anchors working as a positive control. State this distinction explicitly in Steps2/4 and the shared relation validator.
**Why this is robust:** closes the information-loss point before eligibility filters can discard it; one local pass and directly targeted tests cover the actual mechanism without changing ownership or scope.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The raw member already carries the needed positive sender; retaining that evidence in one local pass closes the reproduced case. No other current feature shares this exact per-user inference chronology policy, so a shared framework adds extent without established reach.
*For future:* —

### Mitigation — Long-term
Extract a shared raw-message chronology/evidence abstraction for multiple future inference features, separating individual evidence from aggregate eligibility.
**Why this is long term effective:** if several real features later need the same per-sender chronology semantics, one proven implementation could prevent repeated omissions. No second current runtime consumer of this exact policy is established.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit only when a second implemented inference consumer needs identical chronology/barrier semantics. MessageBatch format validation, album membership and history-window filtering are not interchangeable consumers of this policy.

## Compatibility, Complexity and Qualification Limits
The plan is specific about new wire fields, relation recomputation, conservative barriers, exact count units, immutable caches and selected-policy propagation. Existing raw/album/source files and schema2 acceptance remain byte-identical. No framework, client lifecycle, new persistence authority or deployment is necessary. Python3.7 grammar checks are correctly distinguished from native execution. Strict view failure can inconvenience callers but cannot silently change their requested scope; that is an intentional contract, not an extra finding.

One Medium, zero High, zero Low. Phase2 complete. Phase3 selection follows separately. No planning blocker or plan deprecation is added; the full candidate experiment remains pending.

## Phase3 Selection
R1 Robust selected and elegant; no quick or last-resort choice. Compared actual neighboring modules: message_batch.py validates format/within-batch IDs, album.py groups explicit membership, history_window.py constrains dates. None needs the same per-user heuristic chronology, so a shared class is not established. The local correction remains useful if future reuse appears. One mitigation affects Step2 and Step4; the same relation function validates Step1 values. No new architectural step or execution blocker.

Next under the user-provided task-impl sequence: complete isolated candidate experiment using revision1 plus selected R1 → record actual result → formal Fold → adopt exact candidate → Verify. Do not re-critique after folding.

**Implementation outcome:** selected R1 included in product6eff7c7; complete candidate PASS at1daf215, fold0691364, then exact adoption and full883-check/7-demo verification. See implementation.md. The original critique/experiment/selection above remains the preimplementation record.
