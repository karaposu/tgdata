---
model: unknown
effort: unknown
---
# Combined prebuild — PASS

Executed `run.py` using Python3.11.10 and Telethon1.45.0 before any production edit. It copied the current library/examples to a fresh temporary package, installed the exact candidate module/example/test and four planned public exports, and ran37 offline tests. Candidate paths/hashes are in result.json; all test names/results are in combined.txt.

Actual components: Telethon TL serialization/deserialization, native history iterator, raw BatchEngine and record serializer, MessageBatch, candidate TelegramPost/assembler, candidate AlbumReceiver, SQLite, SQLiteSyncStore, SyncEngine, BackfillEngine and ReadBudget. Cached photo bytes also passed through the SDK's real download implementation. The SDK transport response and bounded source replies are synthetic input fixtures; no Telegram completeness, live account or server pagination result is claimed.

Passing histories include every partition/reverse order of a four-member album; multiple captions and nonadjacent members; exact large IDs/cross-chat keys; strict serialization/conflict/limits; original raw identity/cursor preservation; actual fixed-window clipping without assembly lookahead; explicit create/reopen and missing schema/file/collection refusal; rollback of both posts and marker; process exit before and after actual SQLite commit; receipt replay after later membership growth; separate collections; competing writer refusal and retry from current prior; failed publication/cancellation/budget refusal without source ack; daily pending replay and backfill full receipt replay/ack; preserved cached-photo blob references/bytes; raised10001-member receiver policy through reopen/replay. The full candidate ran together; the earlier eight storage probes were not used as a substitute.

First attempt:33/34 passed; the backfill fixture's end date was later than its injected creation clock, and the real engine correctly refused a future window. The fixture clock was changed to two hours after the observed message time, leaving the intended closed window unchanged. No production or candidate algorithm changed. Native SDK clipping, cleanup and actual exhausted-budget histories were then added to complete coverage; final37/37 passed. attempt-1.txt/json preserve the failed fixture evidence.

The architecture falsifier did not occur: no raw mutation, receipt substitution, guessed completeness, extra source lifecycle or lost observed member was required. Result PASS permits the selected mitigation fold and adoption of the candidate. Tests do not certify arbitrary external storage corruption, hardware power-loss behavior or distributed source ownership.
