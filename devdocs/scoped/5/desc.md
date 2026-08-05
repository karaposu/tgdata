# Issue 5 — The off-by-one: the first message after every cursor is silently dropped

**Status:** ✅ IMPLEMENTED (2026-07-19) — Approach A: the `+1` removed at `tgdata.py` (now `min_id=after_id`), the false ">= behavior" comment corrected, engine seatbelt re-pointed at the cursor itself (`skip id <= min_id`), poll seen-set kept as seatbelt per plan. Live boundary check passed: `after_id=182981` now returns `[182982, …]` — the previously-lost cursor+1 message present, cursor absent, ascending. `issue_1.md` is closed at the root.
**Where it bites:** every "give me what's new since message #X" call (`after_id=…`) — the heartbeat of polling, incremental ETL pulls, and propertybot's §5 cursor scrapes
**Severity:** high — deterministic, invisible, permanent loss of exactly one message per pull. This is the true root cause of the project's oldest open mystery, `issue_1.md` ("messages skipped during polling").
**Relationship to other docs:** `scoped/2` covers the incremental path's *two* leaks together; this doc is the standalone deep-dive on the first of them, with the full evidence trail. `scoped/3`'s resume-based retry depends on this fix landing first.


---

## What you'd expect

"I've processed everything up to message **500**. Give me what came after." → You get 501, 502, 503, …

## What actually happens

You get 502, 503, … — **501 is missing.** No error. And since your bookmark then jumps to the newest message you received, nothing ever goes back for 501. It's not delayed; it's gone.

Because Telegram numbers a group's messages consecutively (501, 502, 503…), the "first message after the bookmark" is almost always a real message — so this isn't a rare fluke. **Every non-empty pull loses its first message.**

## Why it happens (plain language)

Think of a bakery ticket counter. You say: *"I've been served through ticket 500 — start me at the next one."* The clerk, wanting to be helpful, *also* adds one — and calls out **502**. Ticket 501's owner never gets served.

Concretely: Telegram's fetch API already interprets the number you give it as *"strictly after this one."* Our code **adds 1 on top** before handing the number over. Two "afters" get applied where one was needed — so the boundary message falls through the gap.

## The evidence trail (why we're sure)

1. **The library's own manual says so.** The installed Telethon's documentation for this parameter reads: *"All the messages with a lower (older) ID **or equal to this** will be excluded"* — i.e., it already excludes the number itself. Its internal code confirms it (it even adds its own +1 internally when reading forward). Our extra +1 is the double-count.
2. **It reproduces `issue_1.md` exactly.** That investigation sent messages 1–14 rapidly and observed: got 1–5, *missed 6*; got 7–12, *missed 13*; got 14. Look at the pattern: the lost messages are precisely `cursor + 1` each time (after 5 → lost 6; after 12 → lost 13). Not random flakiness — arithmetic.
3. **The in-code comment asserts the opposite** ("min_id includes the ID itself (>= behavior)") — an honest but incorrect belief, likely from a misread debugging session (`test_debug_min_id.py` shows the author probing exactly this). The +1 was built on that belief.
4. **The scar tissue fits.** Two layers of defensive code exist *specifically* to fight this bug's symptoms: a manual "skip already-seen messages" filter in the engine, and a "seen message IDs" memory in the polling loop. Both cure **duplicates** (which the author could see) — neither can cure **drops** (which are invisible: you don't notice a message you never received). The visible symptom got fixed; the silent one survived.
5. **Bonus artifact:** the committed `all_messages_merged_batches.csv` holds 30 rows but only **10 unique message IDs** — three "incremental" batches that fetched the same 10 messages three times. That file predates the current code (the dupes era); the +1 "fix" then swung the behavior from *duplicates* to *drops*. The incremental path has never yet been correct in both directions at once.

## Why nobody noticed

A dropped message leaves no trace — the pull succeeds and returns plausible data. It only *shows* when someone numbers their messages and counts (which is exactly what `issue_1.md` did — and then the platform, not the arithmetic, got the blame). The dedup layers made the visible problem disappear, which felt like "fixed."

## Who cares / impact

- **propertybot (§5 cursors):** 6 groups × 3 pulls/day → up to ~18 silently discarded messages per day, some of them listings or seeker posts. A map with quiet holes.
- **The polling feature** and every ETL example built on `after_id` — all lossy at every boundary, forever, invisibly.

---

## Solution approaches (high level)

### Approach A — Stop double-counting: hand over the bookmark itself *(recommended)*

Pass the cursor number **as-is** and let Telegram do the "after" — it already does it correctly. Delete our +1 (and the now-false comment). A one-line change at the single place the number is translated.

- **Pros:** one line; removes the loss deterministically; finally closes `issue_1.md` at the root rather than at the symptom.
- **Cons:** none. (The one thing to respect: fix it *at the translation point only* — the rest of the pipeline already assumes "strictly after" semantics.)

### Approach B — Formalize the overlap: ask one earlier on purpose, de-duplicate after *(defensive variant)*

Deliberately request from one message *before* the cursor and rely on the existing de-duplication layers to discard the repeat. This makes the code robust even if the underlying library ever changed its convention.

- **Pros:** immune to either convention; the seatbelts already exist.
- **Cons:** codifies scar tissue as architecture — permanent extra moving parts to paper over a one-character arithmetic question that the library documents plainly. Better used as a temporary seatbelt than a design.

### Approach C — Leave the library; make every caller compensate *(rejected)*

Callers overlap their own windows and de-dup downstream (propertybot's `dedup_hash` would partially mask it).

- **Cons:** every consumer must know the secret; polling and the ETL examples stay broken for everyone else; masking an upstream defect downstream is how this bug survived a year already.

### Recommendation

**A** — remove the +1, correct the comment. **Keep the existing skip-filter and seen-set as seatbelts** through one release (they're cheap and now merely redundant), then simplify them away once the regression test below has been green in real use. Skip B-as-design, skip C.

## How we'll verify

1. **The issue_1 scenario, as an asserting test:** send ~14 rapid numbered messages to a test group; pull incrementally with a moving cursor; **assert all 14 arrive, each exactly once.** (Today, two of them vanish — this exact test was run by hand in `issue_1.md` and documented the loss.)
2. **Boundary check:** for a known message ID `M` with an existing `M+1`: `after_id=M` must include `M+1` and must not include `M`.
3. Keep both as permanent regression tests — the smoke tests' assert-nothing style is how this survived.

---

## Appendix — exact pointers (for the developer)

- **The one line:** `tgdata/tgdata.py:184` — `min_id=after_id + 1 if after_id > 0 else None` → `min_id=after_id if after_id > 0 else None`.
- **The false comment to correct:** `tgdata/message_engine.py:105` ("Since min_id includes the ID itself (>= behavior)…").
- **The seatbelts (keep short-term, then simplify):** engine skip filter `tgdata/message_engine.py:114,119` (`original_min_id` bookkeeping); polling dedup set `tgdata/tgdata.py:490,504-527` (`seen_message_ids`).
- **Telethon 1.40 verification:** exclusivity docstring `.venv/…/telethon/client/messages.py:413-415`; forward-reading offset arithmetic (`offset_id = max(offset_id, min_id)` then `offset_id += 1`) `messages.py:38-58`; "skip the one we already have" `messages.py:260-263`.
- **History:** `issue_1.md` (the observed 6/13 losses + the eventual-consistency misdiagnosis); `test_debug_min_id.py` (the probing session the wrong comment likely came from); commit `abbd077` (introduced the +1); `all_messages_merged_batches.csv` (the earlier dupes era, 30 rows / 10 unique IDs).
- **Dependents:** `scoped/3` (flood-retry resume) must land *after* this — its resume point uses this cursor and would otherwise skip one message per resume.
