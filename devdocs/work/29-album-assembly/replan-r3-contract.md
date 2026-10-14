---
model: gpt-6-astra
effort: xhigh
---
# Revision 3 contract — accepted records and post views

## The decision

The receiver's durable fact is **this collection accepted these exact original message records in this raw batch**. The current album is a view assembled from those records. Confirming the durable fact must not require rebuilding or returning today's larger view.

Keep the public TelegramPost format and pure assemble_albums API. Change the repository's optional SQLite receiver example to store each original member record once, under a collection/chat/message key, with its derived post key and content digest. The example returns `None` on successful acceptance, both first time and replay. `load(post_id)` separately constructs the current validated TelegramPost view. No new public receipt class, source API, progress store or library-owned archive service is introduced.

This is a revised acceptance contract, not a higher numeric limit. It supersedes the earlier inquiry's receiver-specific assertion that every retry merges against the current post. The inquiry's stable identity, lossless records, caller ownership, unconfirmed membership and unchanged source receipt conclusions remain.

## Why records are the authoritative stored data

The original receiver already stores every raw record inside mutable post JSON. Normalizing those same records does not require storing an additional raw-batch archive or retaining duplicate post snapshots. It allows an exact retry to inspect only its original immutable members. Later added members cannot change the number or size of records that retry needs to confirm.

This follows the existing `examples/daily_continuation.py::Destination` pattern of atomic message rows plus batch recognition. Its bootstrap behavior and generic partial_result exception handling are not copied: strict reopening, local integrity checks and confirmed source delivery remain required here.

The smaller alternative—load each grown post sequentially and check its subset—would bound the number of simultaneously loaded posts but still make replay work depend on future growth. A marker-only shortcut would skip the required missing/changed-data checks. Persisting a separate snapshot for every accepted batch would duplicate content and introduce another retention concern. Normalized authoritative records keep confirmation tied to the input while retaining integrity checks.

## Operations and invariants

**New input:** validate the original MessageBatch, selected collection and input limits. In one receiver transaction, reject any existing same chat/message record with different content or post identity; load the affected prior post views; run the existing bounded assembler; insert only new immutable member rows and the collection-scoped raw batch marker; commit. No accepted row is replaced or edited. Source acknowledgment remains outside the transaction, using the original raw receipt.

**Exact accepted input:** validate the same input/collection, find its marker, then compare each original record against the corresponding stored member row. Check canonical content bytes, digest and post key. Missing or inconsistent data refuses; there is no repair or new acceptance write. Do not invoke assemble_albums, load complete current post views, aggregate later members or return post content. Successful confirmation returns `None`.

**Post view:** load one post's member rows under a consistent read transaction, validate their metadata, canonical encoding and digests, and construct the ordinary TelegramPost with current member ordering/revision. Apply its selected per-view limits. A view may legitimately exceed a smaller reader's policy after a larger-policy writer adds members; that does not invalidate confirmation of an old accepted input whose own bounds still fit.

**Closure under retry:** after a successful acceptance, an exact retry with unchanged input limits stays confirmable after restart and permitted later additions. This assumes available, intact storage and no deletion/edit of accepted records. An explicitly lowered input policy, missing/corrupt state, a real backend failure or lock contention can still refuse. Receipt recognition alone never overrides data integrity.

**Fixed source authority:** successful receiver acceptance/confirmation establishes local data custody only. Daily uses its original batch ID; backfill uses its full original delivery reference. Available captured data is not automatically a pending source receipt. The receiver never advances source progress or certifies album completeness.

## Bounds

New work retains the existing aggregate assembler rule: raw input JSON + prior post JSON + produced post JSON must fit max_bytes, and total produced members must fit max_members. These are admission limits for a new projection, not the definition of already committed acceptance.

Confirmation checks the bounded original input: at most its message count (also bounded by max_members and raw MessageBatch's10000 limit), with one indexed member lookup per record. SQL returns equality results rather than complete grown posts. The expected canonical member data is bounded by the input. Do not call decoding properties on MessageBatch inside the member loop: extract batch metadata once, so the whole raw batch is not repeatedly decoded.

Post loading is separately bounded per view. Before fetching/decoding member payloads, use count and UTF-8 byte-size metadata to refuse obviously oversized views. For new-work prior loading, accumulate those metadata lower bounds across affected keys before materializing them, then account for actual constructed post JSON before loading further prior values. The existing assembler remains the final exact aggregate check. No count/byte limit is removed, and no silent trim or eviction is introduced. SQL storage/cache and Python object overhead are not a strict RSS guarantee.

## Persistence compatibility

The example's local schema becomes version2 because the authoritative representation changes. It contains metadata, named collections, immutable member rows, a post lookup index and scoped batch markers. Public TelegramPost v1 and MessageBatch v1 remain unchanged.

Strict reopening refuses a known version1 example database unchanged. `create=True` must not reset, migrate or repair it. This feature and example schema have not merged or shipped; this work does not add automatic migration tooling. If state from the rejected example has been used, retain it and use an explicit separately qualified import/restore path before switching that collection. Never reset the source cursor to conceal missing destination state.

## Planning evidence and limits

`replan-r3-probe.py` implements only the proposed acceptance shape in a temporary SQLite receiver. It uses actual MessageBatch/TelegramPost/assemble_albums, actual SDK-derived records and actual SyncEngine/SQLiteSyncStore. The six final histories pass:

1. The exact4640-byte acceptance/lost-ack case replays under4640, with one source read and acknowledgment advancing to2.
2. The1300-record input replays under the unchanged default16MiB cap.
3. The cap3 old input confirms after album growth; it also confirms after an explicitly larger writer makes the current view too large for that smaller reader. The separate view read still refuses.
4. Missing records, altered content, wrong digests and wrong post keys refuse without repair.
5. A real SQLite receipt-write failure rolls member inserts and marker back together.
6. New oversized work still refuses; changed content or reassociation of an existing chat/message record refuses.

Replays are instrumented to fail if they call the assembler or post-view loader, and they cause zero SQL changes. Final local probe execution took0.492 seconds on Python3.11.10; this is a measurement of these fixtures, not a performance guarantee. Product files remain hash-identical to the rejected implementation.

Prototype corrections: an initial normal-message fixture used None where Telethon's wire string requires text; changed to an empty string. The first prototype also repeatedly accessed MessageBatch.chat_id inside a member loop, causing repeated whole-batch JSON decoding; the final probe extracts metadata before iterating. Initial partial output is retained in replan-r3-probe-attempt1.txt. Neither correction touched production code.

This evidence closes the **planning** question: the receiver can confirm immutable accepted records independently of growing post views with existing source APIs. It does not qualify a complete implementation. Full schema validation, bounded load preflights, cleanup/crash cases, both progress engines, compatibility tests and the complete revised candidate must pass the later critic-directed combined prebuild before production adoption.

**Provenance verified retrospectively, 2026-10-14:** local active-thread turn records and matching commit outputs establish GPT 6 Astra / xhigh for this artifact. Earlier unknown/pending wording records what was known at the time; see [§9 verification](model-effort-verification.md).
