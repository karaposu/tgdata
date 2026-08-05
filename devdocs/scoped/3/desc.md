# Issue 3 — When Telegram says "slow down," the retry starts over — faster

**Status:** ✅ IMPLEMENTED (2026-07-19) — Approaches A+B landed (after the scoped/5 prerequisite): the recursive restart is replaced by a retry loop that **resumes from the last handled message** (`min_id`/`max_id` per direction), physically cannot drop settings (no re-copied call), caps at `MAX_FLOOD_RETRIES = 3` then raises a clear `RuntimeError` with the resume cursor, and logs each wait. Live-verified with injected FloodWaits: exact row count after resume (20/20, no dupes), batches delivered exactly once, bounded give-up fires with the hint.
**Where it bites:** any long fetch that trips Telegram's rate limit — which in practice means the **backfill** (30 days × 6 groups is exactly the heavy pass where limits fire). Telegram's history API is known to throttle after bursts of requests.
**Severity:** medium-high — results usually still arrive eventually, but the retry behavior wastes work, can re-deliver the same messages to downstream processing (duplicates), amplifies the very rate-limiting it's reacting to, and can loop forever. For propertybot this touches the **ban-safety guardrail (§6)**: the disposable account's safety depends on backing off gracefully, and this code backs off — then charges again.

---

## The good part first

When Telegram says *"too fast — wait N seconds,"* the library **does** wait the full N seconds. That part is correct and non-negotiable (Telegram dictates the wait). The problem is everything that happens **after** the wait.

## What actually happens after the wait — three defects in one move

Picture photocopying a 1,000-page book. At page 700 the machine overheats: *"wait 2 minutes."* The clerk dutifully waits two minutes… and then **starts again from page 1.**

1. **It restarts from scratch.** All progress is thrown away. The 700 pages already copied get copied again. On a big backfill, one hiccup near the end means re-fetching almost the entire month — and all those repeat requests are new pressure on the very limit that just tripped. Slow down → start over → get told to slow down again. A vicious circle.

2. **It forgets the "go gently" instructions.** The retry re-issues the original order by hand-copying it — and misses two lines: the **pause between batches** (`batch_delay`) and the **back-off style** (`rate_limit_strategy`). So the caller who carefully said "pace this politely, and if refused, ease off harder" gets a retry that runs at **full speed with default settings** — precisely at the moment gentleness matters most.

3. **It can hand out the same pages twice.** If the caller is processing results batch-by-batch as they stream in (the recommended pattern for feeding a database), the batches delivered *before* the interruption get delivered **again** after the restart. Unless the receiving side de-duplicates, the same listings enter the pipeline twice.

And there's no limit on attempts: if the account is being persistently throttled, the cycle repeats indefinitely — wait, restart, re-trip, wait… — with nobody ever deciding "this isn't working, stop and report."

## Why nobody noticed

At hobby scale (small groups, short fetches), rate limits are rare and brief; when one fired, the restart re-did only a minute of work and succeeded on the second pass — invisible. The dropped settings never mattered because the tests barely use them. The duplicate-batch case needs a flood to land *mid-batch-stream*, which short test runs never produced.

## Who cares / impact (propertybot specifically)

- The **backfill queue** (§4/§6): six 30-day walks back-to-back is exactly the burst profile that trips Telegram's history limits. With this bug, the first flood mid-group means: re-fetch the group from the top, at an *unpaced* rate, with duplicate batches flowing into ingest. Worst realistic case: a slow-motion loop that hammers the account — the opposite of "keep the disposable account safe."
- **Duplicate listings** reaching the map pipeline unless propertybot's dedup catches them (its `dedup_hash` likely would — but relying on downstream cleanup for an upstream defect is backwards).

---

## Solution approaches (high level)

### Approach A — Resume where it stopped, don't restart *(recommended)*

Remember the ID of the last message successfully processed. After the mandated wait, continue **from that bookmark** instead of from the beginning — the library already has exactly this "fetch after an ID" capability (it's the cursor primitive from Issue 2). No wasted work, no duplicate batches, and the retry issues only a fraction of the requests — which is itself the best way to avoid re-tripping the limit.

- **Pros:** eliminates all three defects' worst effects at once; dramatically fewer repeat requests (ban-safety win).
- **Cons:** depends on the cursor primitive being trustworthy — i.e., **fix Issue 2 first** (its off-by-one would make every resume silently skip one message).

### Approach B — Make the retry faithful and bounded *(recommended, alongside A)*

Two disciplines:
- **Faithful:** the retry must reuse *exactly* the original instructions — restructure it so the settings physically can't be forgotten (one shared retry loop instead of a hand-copied second call). Hand-copied retries drift; this one already has, twice.
- **Bounded:** cap the attempts (say, 3) and, past the cap, stop with a clear message ("rate-limited N times, waited M minutes total, giving up at message #X"). A scraper that's being persistently throttled should *stop and tell you* — not grind on. Log every wait so the operator can see throttling happen.

- **Pros:** small, mechanical change; ends the infinite-loop and settings-drift failure modes; makes throttling *visible*.
- **Cons:** none of substance.

### Approach C — Just pace harder from the outside *(complement, not a fix)*

The caller can lower the odds of ever flooding: bigger pauses between batches, one group's backfill at a time (queued, not parallel), off-peak scheduling. propertybot should do all of this **anyway** (§6 says so), and the library's pacing knobs support it.

- **Pros:** reduces how often the bug is even reached; good operational hygiene regardless.
- **Cons:** does nothing about the damage when a flood *does* happen — and on a 30-day × 6-group backfill, one eventually will. Prevention without a working recovery is a plan that works until it doesn't.

### Recommendation

**A + B together, after Issue 2's fix** (A's resume stands on Issue 2's cursor): replace the restart-from-scratch with a small loop that remembers the bookmark, reuses the exact original settings, counts attempts, and reports. Roughly 10–15 lines in one function. Keep C as standing operational practice in propertybot's scraper config.

## How we'll verify the fix

Real floods can't be summoned on demand, so simulate one:

1. In a test, inject a fake "wait 1 second" rate-limit error partway through a fetch (after, say, message 50 of 120).
2. Assert: the final result contains **all 120 messages exactly once** (no gap at the interruption point, no duplicates); each streamed batch was delivered **once**; the pacing settings were identical before and after the interruption; attempts were counted.
3. Inject persistent floods and assert the attempt cap triggers a clear, informative error instead of looping.
4. Soak test: one real 30-day backfill on a large public group, watching the logs for wait events and confirming a single clean pass.

---

## Appendix — exact pointers (for the developer)

- **The restart-and-drop retry:** `tgdata/message_engine.py:193-206` — `except FloodWaitError` → `handle_rate_limit(...)` → recursive `self.fetch_messages(...)` whose argument list **omits `batch_delay` and `rate_limit_strategy`** (they revert to `0.0` / `'wait'`). No attempt counter. Replace recursion with a resume loop (cursor = last processed `MessageId` → `min_id`), forwarding all params.
- **The wait logic (correct, keep):** `tgdata/connection_engine.py:297-321` — `handle_rate_limit`, honors `e.seconds`, supports `'wait'`/`'exponential'`+jitter.
- **Duplicate-batch mechanism:** batches flush inside the loop (`message_engine.py:145-168`); on restart, `batch_count`/buffers reset and early batches re-fire to `batch_callback`.
- **Latent edge:** the handler references `client` (`message_engine.py:194`), which is unbound if the flood escaped `get_client()` itself — bind before the `try` while in there.
- **Sibling handler to consolidate (nice-to-have):** connect-time flood handling duplicated more simply at `connection_engine.py:207-216`.
- **Telethon's own warning** about history-request flood limits: `.venv/.../telethon/client/messages.py:376-378`.
- **Dependency:** Issue 2 (`devdocs/scoped/2/desc.md`) must land first — resume uses the `after_id`/`min_id` cursor, and its off-by-one would silently skip one message at every resume point.
