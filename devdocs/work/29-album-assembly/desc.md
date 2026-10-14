---
model: unknown
effort: unknown
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
10. Receiver acceptance loads current prior observations inside its transaction and commits all posts with a collection-scoped input marker before source ack. Rollback, commit-response loss, lost ack, duplicate input after later growth, and equal inputs in different collections are tested.
11. Daily and backfill integration retains original raw batch/delivery receipts and cursors. Available partial data alone is never represented as a pending source receipt. Existing pool captures, budget charging, raw hashes and progress schemas are unchanged.
12. Documentation explains observed updates, conflict refusal, caller retention/atomicity, media-byte custody, limits and correct acknowledgment order. The library version remains0.1; consumer migration and release are separate work.
13. The real candidate passes a combined SDK/value/SQLite/daily/backfill prebuild, then targeted tests and the full offline regression suite on Python3.11 and Telethon1.45.0. Scripted source replies are disclosed; they do not prove vendor completeness.

## Scope Boundaries

No photo-trail inference (#30), leases (#31), joins/auth/routing changes, classification/contact extraction, scheduler, uploads, edit/deletion reconciliation, automatic reconstruction of lost receiver data, or running ScrapeOps changes. No new source progress store or raw MessageBatch version. The caller owns permanent data and downloaded bytes. The example's SQLite transaction does not promise distributed source ownership or atomicity across two independent systems. No merge, PR publication or release in this task-impl run.

## Priority Level

**Medium / P2.** Cross-batch fragmentation affects recurring scraping and provides the foundation for optional photo trails, but does not invalidate the existing raw-message contract. Feature-heavy describes implementation risk, not urgency.
