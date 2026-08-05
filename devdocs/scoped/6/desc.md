# Issue 6 — Date-range fetching is inverted: 2 of its 3 forms return (almost) nothing

**Status:** ✅ IMPLEMENTED (2026-07-19) — see `scoped/1/desc.md` for the matching status; Approach A + B landed in `message_engine.py` (forward walks start at `start_date - 1s`; direction-aware break/continue for both bounds; naive datetimes normalized to UTC). All three truth-table rows now behave as expected, live-verified.
**Where it bites:** any fetch that specifies dates — `get_messages(start_date=…)`, `get_messages(start_date=…, end_date=…)`. This is the documented "date range extraction" pattern in the project's own ETL guide.
**Severity:** high — silent: no error, just an empty result that looks like an empty group.
**Relationship to other docs:** `scoped/1` describes this same defect through the lens of one caller (propertybot's 30-day backfill). This is the standalone, general write-up of the fix itself. One repair closes both.

---

## The three ways to ask by date — and what each actually returns

| You ask for | What you expect | What you get today |
|---|---|---|
| "everything **since** June 1" (`start_date` only) | June 1 → today | **~nothing** |
| "everything **between** June 1 and June 30" (both) | that month | **nothing** |
| "everything **up to** June 30" (`end_date` only) | history up to June 30 | ✅ works |

Two of the three forms are broken — including the most natural one ("since date X") and the one the ETL guide showcases (a range).

## Why (plain language)

Fetching by date needs two decisions: **which direction** to walk the history (forward or backward in time), and **where to start walking**.

The code gets the *direction* right: when you give a "since" date, it correctly switches to walking **forward** (oldest → newest). But the *starting point* is always computed the way the "up to" form needs it — at the **end** date, or today if there is none. So:

- **"Since June 1"** → walk forward… starting from **today**. There's nothing after today, so the walk ends before it begins. Empty.
- **"June 1–30"** → walk forward… starting from **June 30**. The first messages encountered are *after* June 30 — and the code (correctly!) stops the moment it sees a message past the end date. It stops on the very first message. Empty.
- **"Up to June 30"** → walk *backward* from June 30. Start point and direction agree. Works.

One line chooses the start point; it just never accounts for the forward-walking case. Direction and starting point come from two different requests' logic, and nobody introduced them to each other.

(Verified, not guessed: the underlying library's manual and source confirm that in forward mode the given date is the **ascending start point** — messages *after* it are returned. Details in the appendix.)

## Why nobody noticed

- The project's own smoke test for date filtering fetches "last 30 days," prints *"Found N messages"* — and **never checks that N > 0**. A run finding zero still passes.
- Everyday usage went through the other fetch styles (newest-N, "after message #X"), which don't touch this code path.
- And the failure is indistinguishable from a quiet group — an empty table, no error.

## Who cares / impact

- Anyone following the ETL guide's date-range recipe gets empty output and will suspect their access, their group, or Telegram — anything but the library.
- propertybot's **day-one backfill** ("last 30 days per group") is built on the "since" form: as-is it would seed **zero** listings while appearing to succeed (the `scoped/1` story).
- Combined with the (now-fixed) hidden 100-cap, date-based work had no working escape hatch: the "since" form returned nothing and the workaround (fetch-everything-then-filter) used to cap at 100.

---

## Solution approaches (high level)

### Approach A — Give the forward walk the right starting point *(recommended)*

When the request includes a "since" date (forward mode), start the walk **at that date**. Keep the end date's job as-is (the stop line). A ~one-line correction at the single place the starting point is chosen; it makes all three forms of the table above behave as expected.

- **Pros:** minimal, at the root, fixes both broken forms at once; the "since" form becomes the efficient one-call backfill primitive.
- **Cons:** none of substance. Needs one live confirmation on a real group (see verification).

### Approach B — Never walk forward: read backward from the end and stop at the start *(complement or alternative)*

Date windows can also be served in the library's cheapest direction — newest → oldest, starting at the end date (or today) — **stopping** as soon as a message older than the "since" date appears. Today the code merely *skips* such messages one by one, which in backward mode would pointlessly walk the entire multi-year history; turning that skip into a stop makes this route efficient.

- **Pros:** backward is Telegram's native, most reliable direction; freshest messages arrive first (pleasant for seeding maps/feeds).
- **Cons:** slightly more logic than A; results need one final sort if the caller expects oldest-first.

### Approach C — Do nothing; callers fetch everything and filter locally *(rejected)*

Now that the 100-cap is fixed, a caller *could* pull the entire history and keep the window they wanted.

- **Cons:** downloads potentially years of messages to keep a month; slow; burns exactly the rate-limit budget that the flood-safety guardrails (and Issue 3) try to protect. A stopgap that punishes the biggest groups the most.

### Recommendation

**A**, and while in that function, add **B's skip→stop** improvement — they're complementary (A fixes forward mode's start point; B makes backward-mode windows efficient and doubles as a safety net). Then upgrade the smoke test to **assert** a non-empty, in-window result so this can never silently regress.

## How we'll verify

1. On a real, active group: "since 30 days ago" → non-empty; every returned date inside the window; count sanity-checked against the Telegram app.
2. A closed range (one specific past week) → non-empty; **both edges respected** (nothing before the start, nothing after the end).
3. "Up to date" form → still works (regression guard for the one case that was already correct).
4. Convert the print-only smoke test into an asserting test.

---

## Appendix — exact pointers (for the developer)

- **The wrong start point:** `tgdata/message_engine.py:92-100` — `offset_date = end_date if end_date else datetime.now()` combined with `reverse = bool(start_date)`. Fix: when `reverse` (i.e. `start_date` is set), pass `offset_date = start_date`.
- **The skip that should be a stop (Approach B):** `tgdata/message_engine.py:128-129` — `if start_date and msg.date < start_date: continue` → in newest-first mode this should `break`.
- **Library semantics (verified in Telethon 1.40):** `offset_date` docstring — *"messages previous to this date will be retrieved… Exclusive"* — with the note that `reverse` **flips the meaning of the offsets** (`.venv/…/telethon/client/messages.py:368-369, 401-403`); forward-mode offset handling at `messages.py:38-58`.
- **The assert-nothing test that let it slip:** `tgdata/smoke_tests/test_05_with_progress_feature.py` (`test_progress_with_date_filter` — prints the count, asserts nothing).
- **Related:** `scoped/1` (same defect, propertybot-backfill framing — retire/merge that doc when this fix lands); the now-fixed hidden cap (Issue 5's sibling, `message_engine.py:98`) which used to break even the crude workaround.
