# Trace 6 — Message Fetch Boundary (Entity Resolution + `iter_messages`)

**Category:** Integration boundary
**One-liner:** How a group id/username is resolved to a Telegram entity and how messages are streamed back across the MTProto boundary — including the silent `limit=None → 100` cap.

---

## Entry Point

`MessageEngine.fetch_messages(...)` (`message_engine.py:35`), reached from `TgData.get_messages`. The outbound crossings are `client.get_entity(group_id)` (`message_engine.py:88`) and the `async for msg in client.iter_messages(**iter_kwargs)` stream (`message_engine.py:117`). Terminal state is the assembled DataFrame.

## Execution Path

1. **Acquire client** (trace 8) and open `async with client:` (trace 1 teardown applies).
2. **Resolve entity.** `get_entity(group_id)` accepts a numeric id **or** an `@username` string (`message_engine.py:88`) — Telethon does a lookup, possibly a network round-trip, possibly cache. `channel.title` is logged.
3. **Assemble iteration kwargs** (`message_engine.py:96-101`):
   - `limit = limit if limit else 100` ← **the cap**: a `None` ("get everything") becomes 100.
   - `offset_date = end_date or datetime.now()`.
   - `reverse = bool(start_date)`.
4. **Polling override.** If `min_id` is set, force `reverse=True`, drop `offset_date`, and record `original_min_id = min_id - 1` (trace 7).
5. **Stream + filter.** For each message: skip if `<= original_min_id`; apply `start_date`/`end_date` bounds; hand to `_process_message` (trace 3/11); accumulate; optionally flush batches (trace 13-adjacent).
6. **Assemble.** Build the DataFrame, sort by `MessageId` if polling, return.

## Resource Management

- Connection opened/closed per call (trace 1).
- `get_entity` may populate Telethon's entity cache in the `.session` file.
- Full result buffered in memory (trace 3).

## Error Path

- `FloodWaitError` → `handle_rate_limit` + recursive retry (trace 9).
- Any other exception → logged and re-raised (`message_engine.py:208-210`).
- **Unbound-variable risk:** the `except FloodWaitError` handler references `client` (`message_engine.py:194`); if the error were raised before `client` is assigned (e.g. inside `get_client`'s health check), the handler would `NameError`. In practice `get_client` absorbs floods, so this is latent.
- A bad `@username`/invalid id → Telethon raises (e.g. `UsernameNotOccupiedError`), surfaced as a generic re-raise.

## Performance Characteristics

- One entity resolution per call (cacheable), then a streamed cursor — Telethon paginates under the hood.
- The `limit=100` default means "get all" is accidentally *fast* (it stops at 100), which masks the bug: it looks performant because it silently under-fetches.
- `reverse=True` (oldest-first) changes Telegram's pagination direction; combined with `min_id` it's the polling path.

## Observable Effects

- Log "Fetching messages from: {title}" (`message_engine.py:89`) and, in polling mode, verbose per-message "Processing/Skipping" lines (trace 10).
- Network: entity lookup + paged message pulls.
- Return: up to `limit` (or 100) messages as a frame.

## Why This Design

Accepting id-or-username at the boundary (`get_entity` handles both) is a genuinely nice ergonomic — it's why `examples/username_usage.py` works. Streaming via `iter_messages` with `offset_date`/`reverse` maps directly onto Telegram's cursor model. The default limit exists to keep the polling path (which passes no explicit limit) from accidentally pulling an entire channel each interval.

---

## What feels incomplete

**The issue.** `limit=None` is silently coerced to 100 (`message_engine.py:98`). But `None` is the *documented* way to "get everything" — `etl_usecase.md` literally shows `limit=None  # No limit, get everything`, and `get_message_count` exists precisely to size a full pull. The base fetch therefore contradicts its own documented contract and caps full extraction at 100 messages with no error or warning.

**ELI15.** You ask for "all the messages," and the program quietly hands you the first 100 and acts like that's all of them. It doesn't warn you. If the group has 50,000 messages, you just lost 49,900 and think you're done.

**Impact.** **Silent, severe data loss** on the headline use case (full extraction). The bug is invisible because the result *looks* like a successful fetch — it's the most dangerous kind of defect. It also makes the `all_messages.csv` / batch examples work only because they pass explicit small limits or use `after_id` looping.

**Robust Fixes / Best Practices.** Separate the two intents: only default to a limit when in *polling* mode (`min_id is not None`), and pass `limit=None` straight through to Telethon otherwise (Telethon treats `None` as unbounded). If a bounded default is wanted for safety, make it explicit and log a warning when it truncates.

**Architectural Fix.** Make `fetch_messages` an async generator (trace 3's fix) so "all" means "stream until exhausted" and there's no place for a magic 100 to hide. *Not overkill* — it fixes memory and this cap together.

**Speculative defence.** The comment `# Default limit for polling` reveals the intent: the default was added for the polling path (which calls with no limit) and then left applying to *all* callers because both paths share one function. The author's own extraction used explicit limits or `after_id` batching (as the smoke tests do), so they never exercised `limit=None` and never saw the truncation.

**Is this worth fixing?** Yes — highest-priority correctness bug in the codebase. One-line guard (`limit if limit else (100 if min_id is not None else None)`).

## What feels vulnerable

**The issue.** `get_entity` is called on every fetch with no caching guard at this layer and no handling for resolution failures (invalid username, not-a-member, private channel). Any failure becomes a generic re-raise, and because the connection is torn down per call (trace 1), the entity cache benefit is reduced.

**ELI15.** Every time you want messages, the program re-looks-up "which group is this?" from scratch, and if the name is wrong it just crashes with a vague error instead of "I couldn't find that group."

**Impact.** Extra round-trips in loops; unfriendly errors on the most common user mistake (typo'd username or a group they haven't joined).

**Robust Fixes / Best Practices.** Catch resolution errors and raise a clear domain error ("Cannot access group '@X' — check the id/username and that you're a member"). Resolve the entity once per `TgData` group session and reuse it. Persisting one long-lived connection (trace 1 fix) restores Telethon's entity cache效果.

**Architectural Fix.** A resolved-entity cache keyed by id/username on `MessageEngine`. *Mild overkill alone*, but falls out naturally from the persistent-connection fix.

**Speculative defence.** Telethon caches entities in the session file, so even with reconnects the lookup is usually cheap — the author likely saw fast repeats and didn't consider it a problem. Error messaging wasn't a focus for a personal tool.

**Is this worth fixing?** Medium — the error-message improvement is worth it; the caching is a nice-to-have that comes free with the trace-1 fix.

## What feels like bad design

**The issue.** One function multiplexes three quite different behaviors (historical fetch, date-ranged fetch, polling) via interacting flags (`limit`, `start_date`, `end_date`, `min_id`), and their interactions are non-obvious — e.g. setting `min_id` silently discards `offset_date` and flips `reverse`. The overloading is what let the `limit` default leak across intents (trace 7).

**ELI15.** It's one big machine with lots of switches, and flipping one switch secretly changes what the others do. It's hard to know what you'll get, and the switches quietly override each other.

**Impact.** Hard to reason about, easy to introduce cross-mode bugs (the `limit` cap is exactly this). High cognitive load for maintainers.

**Robust Fixes / Best Practices.** Split into intention-revealing methods: `fetch_history(limit=None)`, `fetch_since(min_id)`, `fetch_range(start, end)` — each with only the parameters it needs, sharing a small private streamer. This removes cross-mode flag interference by construction.

**Architectural Fix.** The split above *is* the architectural fix; it's proportionate and would prevent a whole class of bugs. Not overkill.

**Speculative defence.** The single-function shape grew incrementally: a fetch method got a date filter, then a polling `min_id`, each bolted on rather than refactored, because each addition "just needed one more parameter." Classic organic accretion under time pressure.

**Is this worth fixing?** Medium — worth it as part of addressing the `limit` and polling bugs, which share this root cause.
