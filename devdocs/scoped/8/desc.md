# Issue 8 — Transport discipline: the line that hangs up after every sentence, and the retry that starts the call over

**Status:** ✅ FULLY IMPLEMENTED. Part (b) (resumable/faithful/bounded retry) landed via `scoped/3`. Part (a) (2026-07-21): authenticate/connect split (`_authenticate` = one-time `start()`; `_ensure_connected` = runtime `client.connect()`, non-interactive) + a non-disconnecting `session()` context manager replacing all 5 `async with client:` sites + health-check side effect removed from `get_client`. Proven: 4 sequential operations now trigger **1** connect (was 4) with `is_connected=True` between every op; retry/off-by-one/media suites all still pass. The pool remains inert (single persistent connection is the real path) — now *honestly* dead code, safe to delete or make real later.
**Where it bites:** **(a)** every single operation (list groups, fetch, count, search) pays a full disconnect + double re-login; **(b)** any long fetch that trips Telegram's rate limit — i.e., precisely the heavy backfill passes
**Severity:** (a) medium — no data corruption, but constant waste, log spam, and it quietly disables two of the library's own subsystems; (b) medium-high — duplicate deliveries downstream, amplified rate-limiting, possible endless loop. Together they make the library's Telegram conversation *fragile exactly when it's busiest.*
**Relationship to other docs:** part (b) is the standalone treatment of what `scoped/3` describes from propertybot's ban-safety angle. Part (a) has no earlier scoped doc — it's the "connection contradiction" from the architecture review, now scoped as a fix.

---

## Part (a) — Every operation hangs up the phone, then redials twice

### What the design intends

The library is visibly built around a **long-lived phone line** to Telegram: it keeps the connection object around, checks "are we still connected?", has reconnect logic, a connection *pool* for scaling, and a five-minute health check. Dial once, talk all day, hang up when you close.

### What actually happens

Every operation wraps its work in a construct that — per the underlying library's rules — **hangs up when the work ends**. And on the way in, the connection is established via a helper that logs in… followed by that same construct logging in *again*. So the real conversation looks like:

> dial + verify identity → dial + verify identity **again** → do one task → **hang up** → (next task) dial + verify… → hang up → …

An office with a dedicated line, where the clerk hangs up after every sentence and redials — with the full "hello, verifying who I am" handshake, twice — for the next one.

### The quiet collateral damage

- **The connection pool is dead weight.** Pooling assumes lines stay open; here every line gets hung up after one use. The whole pool subsystem (and its rate-limit bookkeeping) protects nothing.
- **Telegram's "who is this group?" cache loses value.** Lookups re-resolve more than they should because the line keeps dropping.
- **The health check pings a phone that's usually already hung up** — it mostly measures the hang-up habit, not health.
- **Log spam:** "Successfully connected and authenticated!" once per operation — which is itself the bug announcing itself.
- A polling loop redials forever, paying login round-trips every few seconds for nothing.

### Why it's like this

The hang-up-when-done construct is the single most-copied snippet from the underlying library's tutorials — correct for a script that opens, does one thing, and exits. It was carried into a *library* whose engine was separately (and correctly) built for persistence. Each idiom is fine alone; combined, one keeps preparing a long conversation the other keeps ending. And since everything still *works* — just wastefully — nothing ever failed loudly enough to expose it.

---

## Part (b) — When Telegram says "slow down," the retry starts over, faster, and forgets its manners

When a long fetch trips Telegram's rate limit, the library correctly **waits the full mandated time** (that part must stay). Then, in one move, four things go wrong:

1. **It restarts from the beginning.** All progress is discarded; a month-long backfill interrupted at 90% refetches ~everything — and that burst of repeat requests is fresh pressure on the very limit that just tripped. Slow down → start over → trip again.
2. **It forgets the "go gently" settings.** The retry re-issues the request by hand-copying the original order — and the copy omits two lines: the *pause between batches* and the *back-off style*. The retry runs at full speed with defaults, precisely when gentleness matters most.
3. **It can deliver the same messages twice.** Batches already streamed to the caller before the interruption stream again after the restart — duplicates flowing into whatever database sits downstream.
4. **It never gives up.** No attempt limit: a persistently throttled account loops wait→restart→trip indefinitely, with no one deciding "stop and report."

---

## Why these two are one repair

Both are failures of *transport discipline* — who owns the connection, and what a polite retry looks like. And the fixes stack:

- A **persistent line** (fix a) means a retry doesn't also pay reconnect churn mid-recovery, and the "who is this group?" cache stays warm across the resume.
- A **resuming retry** (fix b) needs a reliable "continue after message #X" primitive — which is Issue 5's off-by-one territory. **Sequence: Issue 5's one-liner → part (a) → part (b).**

---

## Solution approaches (high level)

### Part (a): who owns the phone line?

**A1 — The engine owns it; operations just talk** *(recommended).* Connect once (first use), keep the line open, and hang up **only** in the explicit close. Operations stop wrapping the client in the hang-up-when-done construct — four call sites simply drop their wrapper. Optionally dress this as a small "borrow the line" helper so future code can't reintroduce the habit. Then either make the pool real or delete it (it's currently unreachable weight either way).
- **Pros:** matches the engine's existing design; one handshake per session instead of two per task; pool/health-check/cache all become meaningful (or removable) honestly.
- **Cons:** none of substance; long-idle connections rely on the existing reconnect check, which finally gets a real job.

**A2 — Go fully disposable: open-use-close every time, officially** *(rejected).* Honest about what currently happens, but blesses the waste — and polling would still redial every few seconds.

### Part (b): what does a polite retry look like?

**B1 — Resume, faithfully, with a limit** *(recommended — same as `scoped/3`).* Remember the last message successfully handled; after the mandated wait, **continue from there** with the **exact same settings** (restructure so the retry *cannot* drift from the original — one shared loop, not a hand-copied second call), counting attempts and stopping with a clear report after a few failures.
- **Pros:** kills all four defects at once; the retry becomes *lighter* than the original instead of heavier.
- **Cons:** depends on the "after #X" primitive being exact → land Issue 5's fix first.

**B2 — Only pace harder from outside** *(complement, not a fix).* Bigger pauses, one backfill at a time — worth doing operationally regardless, but prevention without working recovery fails eventually on a 30-day × 6-group pass.

### Recommendation

**A1 + B1, in that order, after Issue 5's one-liner.** Net effect: one login per session, no hang-ups between tasks, and an interruption near the end of a backfill costs seconds instead of a full restart with duplicates.

## How we'll verify

**Part (a):** count handshakes. Run five consecutive operations; the logs must show **one** "connected and authenticated," not ten. Assert the connection object reports connected *between* operations, and that only the explicit close disconnects. A short polling run must show zero re-login lines.

**Part (b):** inject a fake "wait 1 second" rate-limit error mid-fetch (e.g. after 50 of 120 messages). Assert: all 120 arrive **exactly once**; every streamed batch delivered once; pacing settings identical before/after; attempts counted; persistent-flood injection trips the cap with a clear error instead of looping. Finish with one real 30-day backfill on a large public group as a soak test.

---

## Appendix — exact pointers (for the developer)

**Part (a):**
- The four hang-up wrappers: `tgdata/tgdata.py:84`, `tgdata/message_engine.py:86, 279, 314` (`async with client:`).
- Why it hangs up / double-dials: Telethon's context manager is `__aenter__ → start()`, `__aexit__ → disconnect()` (`.venv/…/telethon/client/auth.py:668-672`); meanwhile `get_client()` has already run `start()` via `_connect_with_retry` (`tgdata/connection_engine.py:133-155, 198-220`).
- The subsystems this decision revives-or-retires: pool (`connection_engine.py:20-66, 175-196`), health-check gate (`connection_engine.py:138-142`).
- Teardown stays only in `close()` (`connection_engine.py:323-332`) / `TgData.__aexit__`.

**Part (b):**
- The restart-and-forget retry: `tgdata/message_engine.py:193-206` — recursive `fetch_messages(…)` call whose argument list omits `batch_delay` and `rate_limit_strategy`; no attempt counter; batch buffers reset so early batches re-fire.
- The wait logic to keep: `connection_engine.py:297-321` (`handle_rate_limit`, `'wait'`/`'exponential'`+jitter).
- Latent edge to close in the same touch: `message_engine.py:194` references `client`, unbound if the flood escaped `get_client()` — bind before the `try`.
- Resume primitive: last processed `MessageId` → `min_id` — **requires Issue 5's off-by-one fix first** (`devdocs/scoped/5/desc.md`), else every resume skips one message.
- Sibling doc: `devdocs/scoped/3/desc.md` (same retry defect, propertybot ban-safety framing).
