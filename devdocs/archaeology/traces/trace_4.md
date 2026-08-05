# Trace 4 — Statistics & Metrics Derivation

**Category:** Data transformation
**One-liner:** How a messages DataFrame is reduced to summary statistics and a metrics report — a pure, synchronous fold over the table.

---

## Entry Point

`TgData.get_statistics(df)` (`tgdata.py:325`) → `get_message_statistics(df)` (`utils.py:137`); and the standalone `create_metrics_report(df, group_info)` (`utils.py:214`). Also `TgData.get_metrics()` / `export_metrics()` (`tgdata.py:337,354`), which report *connection* health rather than message stats. Terminal state is a returned dict (and optionally a JSON file from `export_metrics`).

## Execution Path

1. **Empty guard.** `get_message_statistics` returns a zeroed skeleton if `df.empty` (`utils.py:147-153`).
2. **Aggregates.** Otherwise it computes counts via vectorized pandas: `len(df)`, `df['SenderId'].nunique()`, min/max `Date`, and `.notna().sum()` on `Message`/`ReplyToId`/`ForwardedFrom` (`utils.py:155-165`).
3. **Top senders.** `df.groupby(['SenderId','Name']).size().sort_values(...).head(10)` produces the leaderboard, reshaped into a list of dicts (`utils.py:168-179`).
4. **Metrics report (separate path).** `create_metrics_report` calls `get_message_statistics`, adds `memory_usage_mb`, and — if non-empty — derives `Hour` and `DayOfWeek` columns via `pd.to_datetime(df['Date']).dt` and builds `messages_by_hour` / `messages_by_day` value-counts (`utils.py:238-245`).
5. **Session metrics (unrelated).** `get_metrics` builds a fresh dict with a timestamp, `current_group.id`, and the result of a connection `health_check()` — it does **not** touch `self._metrics` (which stays `{}` forever, `tgdata.py:67`).

## Resource Management

- Pure in-memory transforms; no I/O except `export_metrics` writing JSON.
- `create_metrics_report` **mutates the caller's DataFrame in place** by assigning `df['Hour']` and `df['DayOfWeek']` (`utils.py:239-240`) — a side effect on an argument the caller likely considers read-only.

## Error Path

- No try/except. Any schema surprise (missing column, non-datetime `Date`) raises straight to the caller.
- `pd.to_datetime` will raise on unparseable dates; the empty-frame skeleton avoids the empty case but not the malformed case.

## Performance Characteristics

- Vectorized and cheap; `groupby` is the dominant cost, trivial for typical group sizes.
- `memory_usage(deep=True)` (`utils.py:233`) walks every object cell — comparatively expensive on large frames, and only used for a report field.

## Observable Effects

- Returned dicts; a `telegram_metrics.json` file from `export_metrics`.
- **Hidden effect:** two new columns (`Hour`, `DayOfWeek`) silently appended to the caller's frame by `create_metrics_report`.

## Why This Design

Keeping stats as free functions over a DataFrame (rather than methods on a stateful object) is a clean, testable choice that fits the "DataFrame is the interface" philosophy. Analysts can call them on any frame, including ones they filtered themselves. The empty-frame skeleton gives a stable shape for callers to rely on.

---

## What feels incomplete

**The issue.** There are *two unrelated notions of "metrics"* that were never reconciled: message-content stats (`get_message_statistics`/`create_metrics_report`) and connection/session metrics (`get_metrics`/`export_metrics`). `self._metrics` is initialized and never used; `create_metrics_report` is exported and imported into `tgdata.py` but **never called** by any method. The feature is half-built.

**ELI15.** There are two different dashboards labeled "metrics" that don't talk to each other, plus an empty box also labeled "metrics" that nobody ever puts anything in, plus a fully-built dashboard that isn't plugged into anything.

**Impact.** Confusing surface area; dead exports; a vestigial `_metrics` field. No runtime harm, but it misleads maintainers about what's wired.

**Robust Fixes / Best Practices.** Delete `self._metrics` if unused; either wire `create_metrics_report` into a public `TgData.get_report(df, group_info)` or drop it; rename the connection-health method to `connection_health()` to stop overloading "metrics."

**Architectural Fix.** Consolidate under one `reporting` module with clearly named `message_report` vs `connection_report`. *Overkill for the size* — the right move is deletion/renaming, not new structure.

**Speculative defence.** `create_metrics_report` was likely built speculatively ("we'll want a full report") and the simpler `get_statistics` won out in practice, leaving the richer function stranded but not deleted. `_metrics` was a placeholder for a caching idea that never landed.

**Is this worth fixing?** Low priority, but a satisfying dead-code cleanup (see the dead-code inventory command).

## What feels vulnerable

**The issue.** `create_metrics_report` mutates the caller's DataFrame in place (`utils.py:239-240`). A function named "create report" unexpectedly adds columns to the input, which can corrupt subsequent operations (e.g. an export that now includes `Hour`/`DayOfWeek`, or a re-run that finds the columns already present).

**ELI15.** You hand someone your spreadsheet to *summarize*, and they quietly scribble two extra columns onto your original copy. Next time you print it, there are columns you didn't put there.

**Impact.** Silent data contamination of a shared object; hard-to-trace bugs where an exported CSV suddenly has extra columns depending on whether a report was generated first.

**Robust Fixes / Best Practices.** Operate on a copy: `d = df.copy()` before deriving columns, or compute the hour/day series without assigning them back (`pd.to_datetime(df['Date']).dt.hour.value_counts()`), which needs no new columns at all.

**Architectural Fix.** None — a one-line discipline fix (don't mutate inputs).

**Speculative defence.** Since `create_metrics_report` is never actually called (see above), the mutation never manifested, so it was never noticed. It's a latent bug in unused code.

**Is this worth fixing?** Only if the function gets wired in — then yes, immediately. As dead code, it's moot until revived.

## What feels like bad design

**The issue.** `get_metrics`/`export_metrics` live on the message-oriented `TgData` but report only connection health, and their name collides with the message-statistics "metrics." Naming carries no information about which metrics you get.

**ELI15.** Two buttons both say "Stats." One shows how your internet connection is doing; the other shows who talks the most in the chat. Same label, totally different things.

**Impact.** API confusion; a user calling `export_metrics` expecting message analytics gets a connection-health blob instead.

**Robust Fixes / Best Practices.** Rename to intent: `connection_health()` / `export_connection_health()` vs `message_statistics()` / `export_report()`. Names should disambiguate the two metric families.

**Architectural Fix.** None beyond renaming.

**Speculative defence.** "Metrics" was probably a catch-all bucket early on, and both the connection and message summaries landed under it before the two concepts diverged. The overload is an accretion, not a decision.

**Is this worth fixing?** Low priority — a rename during the next API pass.
