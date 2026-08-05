# Trace 13 — Progress Tracking Mechanism

**Category:** Cross-cutting mechanism
**One-liner:** How progress/rate/ETA is computed during a fetch and pushed to a caller-supplied callback via inversion of control — a clean, self-contained mechanism with a few loose ends.

---

## Entry Point

Two ways in: `TgData.get_messages(with_progress=True)` (which installs a default console printer, `tgdata.py:168-176`) or a caller-supplied `progress_callback`. The mechanism proper begins when `fetch_messages` constructs a `ProgressTracker` (`message_engine.py:67-73`). Terminal state is the final callback invocation as the fetch completes.

## Execution Path

1. **Install callback.** If `with_progress` and no explicit callback, `TgData` builds `default_progress(current, total, rate)` that prints a carriage-return-updated line (`tgdata.py:169-176`).
2. **Construct tracker.** `fetch_messages` makes `ProgressTracker(total_expected=limit, callback=...)` and calls `.start()` (records `start_time`, zeroes `current`) (`message_engine.py:67-73`; `progress.py:33-37`).
3. **Tick per message.** After each successfully processed message, `progress_tracker.update()` (`message_engine.py:173-174`) increments `current`, computes `rate = current / elapsed`, and invokes the callback with `(current, total_expected, rate)` (`progress.py:39-60`).
4. **Callback renders.** The default printer shows `current/total (pct) - rate msg/s`, or just `current` if `total` is unknown (`tgdata.py:170-174`).
5. **Finish.** `get_messages` prints a trailing newline after the progress line (`tgdata.py:193-194`).

`ProgressTracker` also exposes richer read models never used by the fetch path: `get_eta`, `get_elapsed`, `get_progress_percentage`, `get_summary` (`progress.py:70-105`).

## Resource Management

- Purely in-memory counters and a `start_time`; no external resources.
- The tracker is created per fetch and discarded — no lifecycle concerns.

## Error Path

- `update()` wraps the callback in try/except and logs on failure (`progress.py:56-60`) — a bad user callback can't break the fetch. Good.
- Division-by-zero is guarded (`elapsed > 0`, `progress.py:50`).

## Performance Characteristics

- One callback per message: for the default printer that's a `print()` per message — cheap but not free; on a fast fetch of thousands of messages, terminal I/O can become a visible cost.
- `total_expected` is set to `limit`, so the percentage is against the *requested* count, not the group's true size (which would require the separate `get_message_count`).

## Observable Effects

- A live-updating console line (carriage-return overwrite) during fetch.
- Nothing persisted; progress is ephemeral.

## Why This Design

Inversion of control via a callback is the right pattern: the library reports raw numbers `(current, total, rate)` and lets the caller decide how to render (console, GUI, log, no-op). The default console printer is a nice batteries-included touch for the common CLI case. Keeping `ProgressTracker` free of I/O (it only computes) makes it testable and reusable.

---

## What feels incomplete

**The issue.** `ProgressTracker` is over-built relative to how it's used: `get_eta`, `get_summary`, `get_progress_percentage`, `get_elapsed`, and the `count` parameter of `update()` are implemented but never called by the fetch path. The rich progress model exists; the wiring to expose it doesn't.

**ELI15.** The progress bar has a fully-built "estimated time remaining," "percent done," and "elapsed time" display — but the program only ever shows the basic counter. The fancy readouts are installed behind the wall, unplugged.

**Impact.** Dead-but-tested code; a maintenance surface with no users. Harmless, but it signals unfinished ambition (an ETA/summary UI that never got surfaced).

**Robust Fixes / Best Practices.** Either surface the extras (pass `get_summary()` to a richer callback signature, or let `with_progress` show ETA) or trim to what's used. If keeping them, cover with a quick unit test since they're pure functions (easy wins).

**Architectural Fix.** None needed — it's already cleanly separated; the question is only expose-vs-trim.

**Speculative defence.** `ProgressTracker` was clearly written as a general-purpose utility ("this doesn't need persistence as it's for real-time progress only," its docstring notes), anticipating multiple front-ends. Only the simplest console front-end was ever built, leaving the richer methods ready but unused.

**Is this worth fixing?** Low priority — surface ETA if desired, else leave as a benign, well-factored utility.

## What feels vulnerable

**The issue.** Progress percentage is computed against `total_expected = limit`, and `update()` only fires on *successfully processed* messages (dropped messages — trace 11 — don't tick). So the bar can under-count relative to messages actually streamed, and against a `limit=None` fetch (which is secretly capped at 100, trace 6) `total_expected` is `None`, so no percentage shows even though a real bound exists.

**ELI15.** The "percent done" is measured against how many you *asked for*, not how many exist — and messages the program quietly threw away don't move the bar. So the bar can lie a little, and when you ask for "everything," it can't show a percentage at all.

**Impact.** Mildly misleading progress UX; edge inconsistency with the `limit` bug. No functional harm.

**Robust Fixes / Best Practices.** Base the total on the group's real count (`get_message_count`) when a true percentage is wanted; tick progress on every message *considered* (including drops) if the bar should reflect stream position; align with the `limit` fix so "all" has a knowable total.

**Architectural Fix.** None — parameter/threading adjustment only.

**Speculative defence.** For bounded fetches (`limit=N`) the percentage is correct and useful, which is the case the author actually ran; the unbounded/drop edge cases weren't exercised because the demos used explicit limits.

**Is this worth fixing?** Low priority — cosmetic; fold into the `limit` fix if touching that area.

## What feels like bad design

**The issue.** The default progress renderer lives *inside* `TgData.get_messages` as a nested function that hard-codes `print()` to stdout (`tgdata.py:169-176`), mixing presentation into the data-access method. A library writing to stdout by default is a questionable coupling (it assumes a terminal and pollutes output in non-interactive use).

**ELI15.** The part of the code whose job is "go get data" also secretly contains a little screen-printer that scribbles to the console. A library grabbing data shouldn't assume there's a screen to draw on.

**Impact.** Low, but: stdout noise in headless/piped contexts; presentation logic embedded in the API layer; can't easily swap the renderer without editing the method.

**Robust Fixes / Best Practices.** Ship the default printer as a small named, importable helper (e.g. `console_progress`) that callers opt into, rather than auto-injecting a stdout writer. Keep `get_messages` free of rendering.

**Architectural Fix.** None — move the nested function to a module-level utility. Trivial.

**Speculative defence.** Auto-installing a printer makes `with_progress=True` delightfully zero-effort for the CLI/notebook user the author is, which is a real ergonomic win; the headless-pollution downside doesn't matter in interactive use where this was built and tested.

**Is this worth fixing?** Low priority — a small refactor for cleanliness; the ergonomic default is defensible.
