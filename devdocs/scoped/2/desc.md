# Issue 2 — "Give me everything new since last time" quietly loses messages — twice

**Status:** Leak 2 ✅ IMPLEMENTED (2026-07-19, design amended in review): the silent 100-cap is gone; no-limit fetches now get an **explicit 750-message safety bound** (`DEFAULT_FETCH_LIMIT`) that **logs a warning when hit**, lifted by any explicit `limit=` or `allow_full_fetch=True`; uniform across normal and polling mode. This deliberately keeps a bound (huge-group protection while Issue 8's retry is unfixed) but never a *silent* one — honoring this doc's "if a cap is ever applied, say so" principle. Live-verified (cap + warning fire; explicit limits honored silently). **Leak 1 (the `after_id + 1` off-by-one) ✅ also implemented — see `scoped/5` for the fix + live boundary verification. Both leaks are now closed.**
**Where it bites:** every incremental pull — `get_messages(after_id=cursor)` — which is the exact §5 "cursor" pattern propertybot's recurring scrapes are built on, and what the library's own polling uses internally
**Severity:** high — no errors, no warnings; the results simply have holes. For a supply-seeding scraper, silent gaps are the worst possible failure mode: the map just quietly misses listings.

---

## What you'd expect

You keep a bookmark (the "cursor"): the ID of the last message you've already processed. A few times a day you ask:

```python
new = await tg.get_messages(group_id, after_id=cursor)   # "everything since my bookmark"
cursor = new['MessageId'].max()                           # move the bookmark forward
```

You'd expect: *every* message that arrived since the bookmark, however many there are.

## What actually happens — two separate leaks

### Leak 1: the first new message after the bookmark is always skipped (off-by-one)

In a Telegram group, message IDs count up one by one: 501, 502, 503… When you say "give me everything after 500," the library translates that for Telegram — but it adds 1 where Telegram has already done the "after" part itself. The result is a request for "everything after **501**" — so **message 501, the first genuinely new message, is never fetched.**

Plain-language picture: you tell the librarian *"I've read up to page 500 — start me at the next page."* The librarian, being helpful, *also* turns one page forward before handing you the book. You resume at 502. Page 501 is never read — and because you then move your bookmark to wherever you finished, you never go back for it. **Every single visit loses the first new page.**

Because group IDs are consecutive, this isn't a rare edge case — it's *every non-empty incremental pull, deterministically*. This is the real cause of the project's long-standing "polling skips messages" mystery (`issue_1.md`): the rapid-fire test there lost exactly messages **6** (first after cursor 5) and **13** (first after cursor 12) — the first-after-the-bookmark message, both times. It was blamed on Telegram being flaky; it's actually our own arithmetic. Verified against the Telegram library's documentation and source: its "after this ID" filter is already exclusive — adding 1 double-excludes.

### Leak 2: "everything" secretly means "at most 100" (hidden cap)

When you don't specify a maximum, the library silently substitutes **100**. So "give me everything since my bookmark" actually means "give me at most 100 messages since my bookmark" — and nothing tells you there were more.

Post-office picture: you ask for *"all my mail since Tuesday."* The clerk has a hidden house rule — *never hand over more than 100 envelopes* — and doesn't mention the rest sitting in the back room.

This hidden cap hurts in two different ways depending on how you ask:

- **With a bookmark (`after_id=cursor`):** you get the *oldest* 100 new messages and your bookmark advances only that far. Nothing is destroyed — but you *believe you're caught up when you aren't*. A busy RU/TR real-estate group easily produces more than 100 messages (listings + chatter) in the ~12-hour overnight gap between passes. At 3 pulls/day your ceiling is ~300 messages/group/day; a busier group builds a permanent, growing backlog — fresh listings surface hours, then days, late, and the whole point ("rentals show up within hours") quietly dies. If anyone ever resets or re-derives the bookmark, the backlog is skipped for good.
- **Without a bookmark (first run / plain fetch):** you get the *newest* 100 and — if you then set your bookmark to the newest ID, as any cursor loop does — everything older than those 100 is **permanently leapfrogged**. This is also why the "get ALL messages" test would today produce 100 rows, not the 2,000+ it once did.

## Why nobody noticed

- Both failures are **invisible**: the calls succeed and return plausible-looking data. You'd have to already know what you were owed to see the hole.
- The off-by-one only *shows* under rapid traffic (the author saw it, documented it in `issue_1.md`, but diagnosed it as platform unreliability and added duplicate-filters — which cure repeats, not drops).
- The 100 cap was added as a safety default for the *infinite polling loop* (the code comment says so) and unintentionally leaked onto every caller. The tests and demos always pass explicit small limits, so it never surfaced.

## Who cares / impact

- **propertybot incremental scrapes (§4/§5):** with 6 groups × 3 pulls/day, Leak 1 alone silently discards up to ~18 messages/day — some of them listings. Leak 2 caps intake at ~300 messages/group/day and lies about being caught up. Together: a map with quiet holes and growing staleness, defeating the spec's core promise.
- **Anyone** using the documented cursor pattern (the ETL guide's own examples) inherits both leaks.

---

## Solution approaches (high level)

### Approach A — Stop double-counting the bookmark *(recommended, fixes Leak 1)*

Hand Telegram the bookmark **itself** and let Telegram do the "strictly after" part — it already does this correctly. Remove our extra "+1." A one-line change. The existing duplicate-filters can stay on as harmless seatbelts (they were built to fight this bug's symptoms and cost little).

- **Pros:** one line; deterministic loss ends; finally closes `issue_1.md` at the root.
- **Cons:** none. Needs the rapid-fire test re-run to prove it (see verification).

### Approach B — No hidden caps: "everything" must mean everything *(recommended, fixes Leak 2)*

Keep a safety cap **only** where it belongs — inside the library's own repeating poll loop, which re-asks every few seconds anyway. Everywhere else, when the caller says "no limit," pass "no limit" through (the underlying library fully supports fetching until done). And as a principle: **if a cap is ever applied, say so** — a log line or a "there's more" flag — so a caller can never be silently short-changed.

- **Pros:** small change; "since my bookmark" becomes trustworthy; backfills and full pulls work at any size.
- **Cons:** an unbounded ask on a huge group now really fetches everything — which is correct, but callers should pace it (that's Issue 3's territory: flood-wait handling).

### Approach C — Caller-side workaround: page manually in a loop *(not recommended as the fix)*

Callers can loop — "fetch up to 100 after my bookmark; repeat until a short page comes back" — which is how one of the smoke tests already works around the cap.

- **Pros:** no library change; bounds memory per page.
- **Cons:** every caller must know the secret handshake; and it does **nothing** about Leak 1 — worse, a paging loop crosses *many* bookmark boundaries, so it loses one message per page. The only outside cure for Leak 1 is overlapping windows plus de-duplication — exactly the fragile scaffolding that already grew around this bug once.

### Recommendation

**A + B together** — they're each roughly a one-line correction to the same function's inputs, and they turn the cursor pattern from "quietly lossy twice" into the reliable primitive the propertybot spec assumes. Then delete or demote the workaround scaffolding at leisure. Skip C.

## How we'll verify the fix

1. **Re-run the `issue_1.md` scenario as a test:** send ~14 rapid numbered messages to a test group, pull incrementally with a moving cursor, and **assert all 14 arrive, each exactly once** (today: 6 and 13 vanish).
2. **Cap test:** place >100 messages beyond the cursor (or use a busy group), do one no-limit pull, assert the count exceeds 100 and matches the group's actual new-message count.
3. **First-run test:** a no-cursor "get all" on a known group must return the full history count, not 100.
4. Keep these as asserting regression tests — the current smoke tests print results but assert nothing, which is exactly how both leaks survived.

---

## Appendix — exact pointers (for the developer)

- **Leak 1 (+1):** `tgdata/tgdata.py:184` — `min_id=after_id + 1 if after_id > 0 else None` → should pass `after_id` directly. The justifying comment ("min_id includes the ID itself (>= behavior)") at `tgdata/message_engine.py:105` is wrong for Telethon 1.40: docstring says *"messages with a lower ID **or equal to this** will be excluded"* (`.venv/.../telethon/client/messages.py:413-415`); reverse-mode offset logic confirms (`messages.py:38-58`).
- **Leak 1 scaffolding (symptom patches, keep-or-simplify after fix):** manual skip filter `tgdata/message_engine.py:114,119`; `seen_message_ids` dedup set `tgdata/tgdata.py:490,504`.
- **Leak 2 (cap):** `tgdata/message_engine.py:98` — `'limit': limit if limit else 100  # Default limit for polling` → default only when `min_id is not None` (polling), else pass `None` through (Telethon: `limit=None` ⇒ whole history, `messages.py:398-399`).
- **History:** `issue_1.md` (the misdiagnosis); `all_messages_merged_batches.csv` (30 rows, only 10 unique IDs — an older era of the same incremental path misbehaving); commit `abbd077` introduced both current defects.
- **Related:** Issue 1 (`devdocs/scoped/1/desc.md`) breaks the *backfill* path; this issue breaks the *incremental* path. Fixing both makes the two §4 cadence modes trustworthy.
