# Trace 10 — Polling Message-Skipping & Dedup Workaround

**Category:** Error / recovery
**One-liner:** How `poll_for_messages` repeatedly asks "what's new since id X," why Telegram's `min_id` can skip messages under rapid arrival, and the layered `seen_message_ids` + max-id bookkeeping built to compensate.

---

## Entry Point

`TgData.poll_for_messages(group_id, interval, after_id, callback, max_iterations)` (`tgdata.py:460`). Entry is the start of the polling loop; terminal state is loop exit (after `max_iterations`, or never for `None`). The underlying failure this trace centers on is documented in `issue_1.md`: messages with `id >= min_id` are sometimes not returned by `iter_messages`.

## Execution Path

1. **State init.** `current_after_id = after_id`, `iterations = 0`, and a `seen_message_ids` **set** (`tgdata.py:488-490`).
2. **Fetch new.** Each iteration calls `get_messages(group_id, after_id=current_after_id)` (`tgdata.py:496`) → `fetch_messages` with `min_id = after_id + 1` (`tgdata.py:184`), which in the engine becomes the polling route (trace 7): `reverse=True`, `original_min_id = min_id - 1`, per-message skip of `id <= original_min_id`.
3. **Two-layer dedup** (`tgdata.py:501-527`):
   - Pull `all_message_ids` from the frame; compute `new_message_ids` = those not in `seen_message_ids`.
   - If any are new: filter the frame to truly-new rows, add them to `seen_message_ids`, advance `current_after_id = max(all_message_ids)`, and invoke `callback(truly_new_messages)`.
   - If all were duplicates: still advance `current_after_id` to the max id seen.
4. **Advance.** `current_after_id` only ever moves to the **max id observed this iteration** — not `max+1` — meaning next iteration's `min_id = max+1` (via the `after_id+1` step), which is correct for exclusivity.
5. **Sleep.** `await asyncio.sleep(interval)` unless it's the last iteration.

The core recovery move is the `seen_message_ids` set: because the author observed `min_id` returning overlapping/partial pages, they dedup client-side so the callback never sees a message twice.

## Resource Management

- `seen_message_ids` grows **unbounded** for the lifetime of the poll — one int per message ever seen. An infinite poll on a busy group is a slow memory leak.
- No persistence: `current_after_id` and the seen-set live only in memory, so a restart re-polls from the passed `after_id` and re-delivers.

## Error Path

- The whole iteration body is wrapped in try/except (`tgdata.py:493,537`): on any error it logs, increments `iterations`, sleeps, and continues — a resilient but silent "keep going" (see below).
- `max(all_message_ids)` assumes the frame has a `MessageId` column; on an empty frame the `if not new_messages.empty` guard avoids it, but a column-less empty frame (trace 3) would still be caught by `.empty`.

## Performance Characteristics

- One fetch per interval; each fetch pays the per-op reconnect (trace 1) and the `reverse=True` cost (trace 7).
- Dedup is O(new) set membership — cheap. Memory, not CPU, is the scaling concern.
- Latency is bounded by `interval`, strictly worse than the push-based event handler (trace 2).

## Observable Effects

- Verbose logs: "Poll iteration N: Checking for messages after ID...", "Found K new messages, IDs: [...]", "Updating after_id from A to B" (`tgdata.py:495-527`), plus the engine's per-message "Processing/Skipping" lines.
- `callback` fires once per iteration with only genuinely-new messages.

## Why This Design

The dedup set and max-id tracking are a *direct, honest response to an observed platform bug* — `issue_1.md` documents the investigation. Given `min_id` can return overlapping pages, deduping client-side and advancing to the max seen is a reasonable way to guarantee "no message delivered twice" without trusting the server's paging. The try/except-continue keeps a long-running poller alive through transient errors.

---

## What feels incomplete

**The issue.** The workaround guarantees *no duplicates* but **not** *no skips*. `issue_1.md` itself shows messages (6, 13) being lost entirely: if `iter_messages` never returns a message id, `seen_message_ids` can't recover it, and advancing `current_after_id` to `max(all_message_ids)` **permanently skips past** the missing lower id. The dedup layer treats the symptom (repeats) while the real disease (drops) remains — and advancing to max actively *cements* the drop.

**ELI15.** The mail carrier sometimes skips a house. This code is very good at making sure you never get the *same* letter twice — but it does nothing to get back the letter that was skipped, and worse, once it sees letter #10 it stops looking for the missing #6 forever.

**Impact.** Silent, permanent message loss in the real-time path — the exact failure the issue describes, only half-mitigated. For a "scraper," losing messages is a core-mission failure.

**Robust Fixes / Best Practices.** Don't jump `current_after_id` to `max`; advance conservatively (e.g. to the min of the *contiguous* run from the previous cursor, re-fetching the tail next round), or fetch a small overlapping window each iteration and rely on dedup to drop repeats. Better: prefer the push-based event handler (trace 2), which doesn't page by `min_id` at all, for latency-sensitive/no-loss needs.

**Architectural Fix.** Replace `min_id` polling with Telethon's update/event stream as the primary real-time mechanism; keep polling only as a periodic "catch-up backfill" that pages by contiguous id ranges. *Proportionate* — the event path already exists, so this is mostly wiring, not new machinery.

**Speculative defence.** The author clearly hit the bug, investigated it (the issue doc is thorough), and shipped the dedup because it *demonstrably* stopped the duplicates they could see in tests. Skips are harder to observe (you don't notice a message you never received), so the partial fix felt complete. Advancing to `max` is the intuitive "don't re-ask for old stuff" move whose downside (skipping the gap) isn't obvious.

**Is this worth fixing?** Yes — high priority for a tool whose name is "scraper"; at minimum, document that polling can drop messages and steer users to the event handler.

## What feels vulnerable

**The issue.** `seen_message_ids` grows without bound and nothing is persisted. A long-lived poller leaks memory proportional to total messages seen, and any restart loses the cursor and re-delivers from the initial `after_id`.

**ELI15.** The program keeps a list of every letter it's ever received, forever, and never throws any away — so the list just keeps growing. And if the program restarts, it forgets where it was and starts re-reading old mail.

**Impact.** Slow memory growth on busy groups (eventually OOM for a truly long run); duplicate delivery across restarts; no durable "resume point."

**Robust Fixes / Best Practices.** Bound the set (only keep ids near the frontier — you never need to remember ids far below `current_after_id`), or drop the set entirely once the cursor logic is contiguous. Persist `current_after_id` (and optionally the frontier) so restarts resume cleanly.

**Architectural Fix.** A small durable cursor store (file/SQLite) keyed by group. *Mild overkill for ephemeral polling* but essential if polling underpins an ETL pipeline (which the docs claim). Bounding the set is the cheap must-do.

**Speculative defence.** Polls in testing ran for seconds/minutes with `max_iterations`, never long enough to leak meaningfully, and were never restarted mid-stream — so neither the growth nor the missing persistence bit.

**Is this worth fixing?** Medium — bound the set now; add persistence only if long-running/production polling is real.

## What feels like bad design

**The issue.** The recovery logic is spread between two layers doing overlapping dedup: the engine skips `id <= original_min_id` per message (`message_engine.py:119`) *and* `poll_for_messages` maintains its own set (`tgdata.py:504`). Two dedup mechanisms for one guarantee, plus heavy `logger.info` on the hot path leaking internal ids.

**ELI15.** Two different workers both cross names off the guest list independently, using slightly different lists — and they announce every name over a loudspeaker as they go. It's redundant, and it's noisy.

**Impact.** Redundant logic that can drift; log spam at INFO level (including message ids, a mild privacy leak); harder to reason about where "new" is actually decided.

**Robust Fixes / Best Practices.** Decide dedup in exactly one place; demote the per-message polling logs to DEBUG; stop logging raw message ids at INFO.

**Architectural Fix.** Fold cursor+dedup into a single `PollCursor` object owned by one layer. Proportionate; also the natural home for persistence and set-bounding.

**Speculative defence.** The engine-level skip was the first attempt; when it didn't fully work (the platform bug), the author added the set at the polling layer *on top* rather than replacing, because the engine skip was shared with non-polling paths and felt risky to remove. Verbose logging is debugging scaffolding from the `issue_1` investigation, left in.

**Is this worth fixing?** Low-medium — consolidate and quiet the logs during the polling rework.
