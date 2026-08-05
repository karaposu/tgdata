# Issue 1 — "Give me the last 30 days" comes back (almost) empty

**Status:** ✅ IMPLEMENTED (2026-07-19) — Approach A (offset = start_date when walking forward, 1s exclusivity pad) + Approach B (direction-aware stop-at-cutoff in the loop) + a latent-crash guard (naive datetimes normalized to UTC, Telethon's own convention). Live-verified on a real group: start-only (25 rows, ascending, in-window — previously ~empty), closed 24h range (in-window only — previously empty), end-only regression (still correct, incl. naive input).
**Where it bites:** any fetch that uses a start date — most importantly the propertybot **backfill** ("walk the last 30 days of each group once, so the map isn't empty on day one")
**Severity:** high — the feature doesn't error, it just quietly returns nothing, which looks like "the group has no messages"

---

## What you'd expect

You ask the library: *"get me the messages from this group since 30 days ago."*

```python
messages = await tg.get_messages(group_id, start_date=thirty_days_ago)
```

You'd expect a table with a month's worth of messages.

## What actually happens

You get back an empty (or nearly empty) result — no error, no warning. It looks exactly like a dead group. In reality the group may have thousands of messages in that window.

## Why it happens (plain language)

Think of a group's history as a very long bookshelf, arranged oldest → newest, with a bookmark you can place anywhere to say "start reading here."

When you ask for "everything since June 19," the library correctly decides to read the shelf **left-to-right** (oldest-to-newest) — that part is right. But then it places the bookmark at **today** instead of at June 19.

So the instruction Telegram receives is: *"start at today, and read forward in time."* There is nothing after today — so Telegram hands back nothing. The month of messages you wanted sits entirely *behind* the bookmark and is never read.

(The subtle cause: the same "bookmark" setting is shared between two different kinds of requests — "up to a date" and "since a date" — and it's always set the way the *first* kind needs it. Asking "up to a date" works fine; asking "since a date" gets the bookmark on the wrong side.)

## Why nobody noticed until now

- The project's own test for this feature prints *"Found N messages from last 30 days"* but **never checks that N is bigger than zero** — a run that finds 0 still counts as a pass.
- All the other, more-used fetch styles (newest-N messages, "everything after message #X") don't go through this code path, so daily usage never touched it.

## Who cares / impact

- **propertybot backfill (§4 of scrape_needs.md)** is built entirely on this call. As things stand, day-one seeding of the map would silently produce zero listings.
- Anyone using the documented "date range extraction" pattern from the ETL guide gets empty results and may wrongly conclude the group, their account, or their access is the problem.
- The failure is **silent** — the most dangerous kind, because the output looks like a legitimate "nothing there."

---

## Solution approaches (high level)

### Approach A — Put the bookmark on the correct side *(recommended)*

When the request is "since date X," place the starting bookmark at **X** (not at today), and keep reading forward until the end date (or the present). This is the smallest possible correction — a couple of lines — and it makes the library do exactly what its own documentation already promises. Everything else stays as-is.

- **Pros:** tiny change; fixes the feature at the source; backfill becomes one natural call per group.
- **Cons:** none of substance. Needs one live test against a real group to confirm (see "How we'll verify").

### Approach B — Read backwards from today and stop at the cutoff

Alternative framing: for "last 30 days" specifically, you can read the shelf **right-to-left** (newest first, which is Telegram's most natural direction) and simply **stop as soon as you reach a message older than the cutoff**. Today the code *skips* older messages one by one instead of stopping — so if you tried this route it would pointlessly walk the entire multi-year history. Adding a proper "stop here" makes it efficient.

- **Pros:** newest-first is Telegram's cheapest, most reliable read direction; you get the freshest listings first (nice for seeding a map); a natural fit for "last N days" jobs.
- **Cons:** slightly more logic than A; results arrive newest-first so they need one sort at the end.

### Approach C — Don't touch the library; work around it from the caller *(not recommended)*

The caller fetches a huge number of messages with an explicit big limit and throws away the ones older than 30 days.

- **Pros:** zero library changes.
- **Cons:** wasteful (downloads far more than needed), slow, and it pounds Telegram's servers — raising exactly the rate-limit/ban risk the propertybot spec explicitly says to avoid for the disposable account. Also every future caller must know the secret workaround. This is a stopgap, not a fix.

### Recommendation

Do **A** (the two-line bookmark fix), and add **B's "stop at the cutoff"** improvement while in there — they're complementary: A fixes "since date X" requests generally; B makes "last N days" jobs efficient and adds a second safety net. Skip C.

Whichever approach: also make the test **assert** it got a non-zero, in-range result, so this can't silently regress again.

## How we'll verify the fix

1. Pick one real, active group.
2. Ask for "last 30 days" and check: result is non-empty, every message's date is inside the window, and the count roughly matches what the Telegram app shows for that period.
3. Ask for a closed range (e.g. exactly one past week) and check both edges behave: nothing before the start, nothing after the end.
4. Lock it in with a test that fails on an empty result.

---

## Appendix — exact pointers (for the developer)

- The wrong-side bookmark: `tgdata/message_engine.py:92-100` — `offset_date` is set to `end_date or now()` even when `reverse=True` (i.e. when `start_date` is the boundary that matters). Fix: when `start_date` is set, use it as the `offset_date`.
- The "skips instead of stopping" walk (Approach B's cost today): `tgdata/message_engine.py:128` — `continue` on too-old messages; in newest-first mode this should `break`.
- Behavior verified against the installed Telethon 1.40 source (`.venv/.../telethon/client/messages.py`, reverse/offset handling at lines 38–58): with `reverse=True`, the offset is the *ascending start point* — messages **after** it are returned.
- The assert-nothing test that let this slip: `tgdata/smoke_tests/test_05_with_progress_feature.py` (`test_progress_with_date_filter`).
