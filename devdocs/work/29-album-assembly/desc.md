---
model: gpt-6-astra
effort: xhigh
---
# Description — album assembly across batches (#29)

**Session warmth:** retained context plus fresh full reads at dev ancestor `e5cdad77ff6af41f21503fc43fe3180d5213a41e`: raw batch/value/files, daily and backfill engines/stores, TgData/progress facade, pool capture values, budget client, receiver example, and ScrapeOps's collapse helper/fixtures. Actual Telethon1.45.0 grouping interfaces and primary Telegram schema were inspected. See warm.md for scope; no all-code archaeology refresh is claimed. §9 model/effort metadata remains unknown, with the factual question pending.

**Qualified input:** source-input.md preserves the original issue. traverse/finding.md qualifies the ownership and completeness contract. [ASSUMPTION] Use a separate opt-in assembler; the optional API preference has not received a reply. This is the working design, not a claimed user choice.

## Problem Statement

MessageBatch v1 returns bounded individual Telegram messages. An album caption and its photos can therefore arrive in different calls, and consumers can accidentally process them as unrelated posts. Grouping only the current batch cannot restore members accepted before a restart. Increasing source reads to finish an album would risk changing budgets, fixed windows and saved delivery identities.

The qualified solution groups observed members into stable post observations and combines them with explicit caller-retained prior values. It does not promise a final, globally complete album. The request's incomplete/unconfirmed boundary makes that distinction essential.

## User Value Proposition

Consumers can store one logical Telegram post and update its revision as more members arrive. They retain every caption, original message and media reference without rebuilding album logic in each application. A concrete receiver example demonstrates restart/replay and acknowledgment ordering with caller-owned storage.

## Success Criteria

1. An opt-in operation accepts existing immutable MessageBatch values and explicit prior observations, returns immutable post observations, and performs no Telegram, filesystem or acknowledgment operations.
2. Album identity uses canonical chat ID plus grouping ID. Ungrouped messages remain distinct by chat/message ID. Large identifiers survive exact serialization; equal grouping IDs in different chats cannot merge.
3. Members retain the complete original raw records in ascending message-ID order, including multiple captions, sender/reply provenance, service records and media/blob references. Caption location cannot change post identity.
4. Splits, nonadjacent members and reversed batch arrival produce the same canonical post bytes for the same observed records. Exact duplicates do not change the revision. Conflicting records or incompatible modes raise without choosing an edit policy.
5. Every affected key requires an explicit prior lookup result, including None for authoritative individual-key absence. Missing/extra/wrong-key prior entries and invalid saved values refuse without mutating input or prior observations.
6. A versioned derived-post format validates schema, identity, record consistency and content revision. Returned dictionaries are copies; malformed JSON cannot silently become new state.
7. Explicit adjustable count/UTF-8 byte bounds refuse the whole operation; no hidden lookahead, trimming, eviction or internal history cache occurs.
8. Global album membership stays explicitly unconfirmed at limit/end/interrupted batches, fixed-window edges, exhausted allowance, cancellation and restart. No new source-completeness assumption is used; no live completeness claim is made.
9. A runnable SQLite receiver example requires explicit new collection creation or strict reopening. Missing/corrupt known file/schema/collection and failed loads raise, while a genuinely absent individual key can yield None.
10. The receiver commits immutable original member records and a collection-scoped input marker before source ack. New inputs load current post views and pass bounded assembly admission. Exact accepted inputs confirm their original stored records without reassembling or returning a current post view. Acceptance returns None on success; load(post_id) separately returns the current TelegramPost. Rollback, commit-response loss, lost ack, unchanged-limit replay, later growth and collection separation are tested.
11. Daily and backfill integration retains original raw batch/delivery receipts and cursors. Available partial data alone is never represented as a pending source receipt. Existing pool captures, budget charging, raw hashes and progress schemas are unchanged.
12. Documentation explains observed updates, conflict refusal, caller retention/atomicity, media-byte custody, limits and correct acknowledgment order. The library version remains0.1; consumer migration and release are separate work.
13. The real candidate passes a combined SDK/value/SQLite/daily/backfill prebuild, then targeted tests and the full offline regression suite on Python3.11 and Telethon1.45.0. Scripted source replies are disclosed; they do not prove vendor completeness.

## Scope Boundaries

No photo-trail inference (#30), leases (#31), joins/auth/routing changes, classification/contact extraction, scheduler, uploads, edit/deletion reconciliation, automatic reconstruction of lost receiver data, or running ScrapeOps changes. No new source progress store or raw MessageBatch version. The caller owns permanent data and downloaded bytes. The example's SQLite transaction does not promise distributed source ownership or atomicity across two independent systems. No merge, PR publication or release in this task-impl run.

## Priority Level

**Medium / P2.** Cross-batch fragmentation affects recurring scraping and provides the foundation for optional photo trails, but does not invalidate the existing raw-message contract. Feature-heavy describes implementation risk, not urgency.

## Known Blockers

### Accepted-input replay under unchanged bounds — CLOSED (planning contract)

**What must be known:** define which bounds admit new assembly versus confirm already accepted input, and what replay returns after post growth. Any successfully accepted input must remain confirmable under unchanged policy after restart/permitted later updates, while retaining integrity checks and original source receipt authority.

**Why it blocks planning:** the current receiver calls fresh assembly before recognizing accepted input; its costs grow on immediate retry or after later membership growth. Fresh PR35 probes reproduce refusal after successful commit with unchanged byte/member settings, including the default16MiB limit. Steps2–4 need a settled replay/return contract; propagating the same limits to loaders is not sufficient. The immutable post representation and source APIs are not disproved.

**Found by:** same-session critic-d on PR35 diff + revision2 plan,2026-10-14. Evidence: pr-critic.md and pr-probes.py/.json/.txt. This is the first PR rejection. Revision2 is retained as DEPRECATED_step_by_step_impl_plan.md. The re-planning agent can resolve this design contract from the recorded counterexamples; no external account or live access is required.

**Resolution,2026-10-14:** replan-r3-contract.md separates new projection admission, confirmation of immutable accepted member records, and bounded post-view reads. The SQLite example stores one canonical copy per collection/chat/message ID plus a digest/post key and the existing scoped input marker. Confirmation validates only the original records, returns no post payload, performs no write and never invokes assembly. Public post/batch formats and source APIs remain unchanged; the unmerged example database changes to schema2 with strict refusal of old known state, not automatic migration/reset.

**Evidence:** all six actual-component planning histories in replan-r3-probe.json passed, including the three rejected cases with unchanged limits, integrity refusals and actual SQLite rollback. This closes the design premise for revision3; it does not mark R1 fixed in production. The complete revised candidate, schema/load guards and both progress-engine compositions still require fresh plan critique and full combined prebuild before implementation.

**Implementation follow-through:** revision4 is implemented at `8c92cf5` / PR head `7a49bd9`, with the complete57-case candidate and830-check full offline run passing; see implementation-r4.md. This is implementation evidence addressing the first PR finding, not a renewed PR approval.

**Provenance verified retrospectively, 2026-10-14:** local active-thread turn records and matching commit outputs establish GPT 6 Astra / xhigh for this artifact. Earlier unknown/pending wording records what was known at the time; see [§9 verification](model-effort-verification.md).
