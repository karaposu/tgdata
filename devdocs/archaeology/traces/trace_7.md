# Trace 7 — Fetch Iteration-Parameter Routing

**Category:** Decision / routing
**One-liner:** How `fetch_messages` chooses between historical, date-ranged, and polling iteration modes by branching on `min_id`, `start_date`, `end_date`, and `limit` — and the consequences each branch carries.

---

## Entry Point

The kwargs-assembly block in `fetch_messages` (`message_engine.py:91-115`). The branch condition is really four inputs (`limit`, `start_date`, `end_date`, `min_id`) collapsed into one `iter_kwargs` dict. Terminal state is the `iter_messages(**iter_kwargs)` call whose behavior is fully determined here.

## Execution Path — the decision table

| Inputs | `reverse` | `offset_date` | `limit` | `min_id` | Effective mode |
|---|---|---|---|---|---|
| none | `False` | `now()` | **100** | absent | "recent" (newest-first, capped 100) |
| `limit=N` | `False` | `now()` | N | absent | recent N |
| `start_date` set | `True` | `end_date or now()` | limit-or-100 | absent | historical forward from start |
| `end_date` set | `False` | `end_date` | limit-or-100 | absent | up to end_date |
| `min_id` set (polling) | **forced `True`** | **removed** | limit-or-100 | `min_id` | incremental since id |

Key routing lines:
- `reverse = bool(start_date)` (`message_engine.py:100`).
- `limit = limit if limit else 100` (`message_engine.py:98`) — applies to **every** branch (see trace 6).
- `if min_id is not None:` forces `reverse=True`, pops `offset_date`, sets `original_min_id = min_id - 1` (`message_engine.py:104-114`).

The `min_id` branch is the highest-priority route: it overrides `reverse` and `offset_date` regardless of what the date logic decided.

## Resource Management

- Pure parameter selection; no resources acquired here. The chosen route determines pagination direction and volume downstream.

## Error Path

- No error handling in the routing itself. A contradictory combination (e.g. `start_date` **and** `min_id`) doesn't error — `min_id` silently wins and `start_date` is only applied as a post-filter in the loop (`message_engine.py:128`), which can produce surprising empty results.

## Performance Characteristics

- `reverse=True` (oldest-first) can be markedly slower/heavier on large channels than newest-first, because Telegram paginates from the far end. The polling route always pays this.
- The 100-cap makes the "recent" and "get all" routes indistinguishable in cost — which is the bug hiding in plain sight (trace 6).

## Observable Effects

- Different message ordering per route (newest-first vs oldest-first), later normalized only in polling by an explicit sort (`message_engine.py:216`).
- In polling mode, verbose per-message log lines.

## Why This Design

The branches map onto real Telegram semantics: `offset_date` + direction is how you page history, and `min_id` is how you ask "what's new since." Forcing chronological order for polling (`reverse=True` + sort) is correct — consumers of "new messages" want them in order. Consolidating into one `iter_kwargs` dict keeps the single `iter_messages` call site.

---

## What feels incomplete

**The issue.** The routing doesn't cover or reject invalid combinations, and the `limit` default isn't route-aware. "Get everything" (`limit=None`) has no route of its own — it collapses into the capped "recent" route (trace 6). There's no explicit "unbounded historical" path even though it's the primary advertised use.

**ELI15.** There are labeled lanes for "recent," "by date," and "what's new," but no lane for "give me literally all of it" — that request quietly gets shoved into the "recent 100" lane. And if you pick two lanes at once, nobody stops you; one just silently wins.

**Impact.** The headline extraction use case has no correct route; conflicting inputs produce silent surprises rather than errors.

**Robust Fixes / Best Practices.** Make `limit` default route-aware (only cap when `min_id is not None`); validate mutually-exclusive inputs and raise on contradictions; add an explicit unbounded path.

**Architectural Fix.** Split into per-intent methods (same as trace 6's fix) so each route is named and its parameters can't collide. Proportionate, not overkill.

**Speculative defence.** Each route was added when a feature needed it (dates, then polling), and the shared `limit` default was a polling-era addition never revisited for the historical route. Invalid combos never arose in the author's own linear usage.

**Is this worth fixing?** Yes — it's the same root cause as the trace-6 data-loss bug.

## What feels vulnerable

**The issue.** The `min_id` branch silently discards `offset_date` and overrides `reverse` (`message_engine.py:108-110`). A caller who sets both a date range and `after_id` gets neither the date semantics they asked for (dates degrade to post-filters) nor a warning.

**ELI15.** You ask for "new messages since #500, but only from July." The program hears "since #500" and throws away the "only from July" part of your instruction without telling you — then filters July out afterward in a way that can leave you with nothing.

**Impact.** Confusing empty/partial results when combining incremental and date filtering; the interaction is undocumented and non-obvious.

**Robust Fixes / Best Practices.** Either honor both (pass `min_id` *and* keep date bounds as first-class), or reject the combination with a clear error. At minimum, log when one input overrides another.

**Architectural Fix.** Per-intent methods again remove the overlap. No extra machinery.

**Speculative defence.** Polling and date-range fetching were never used together by the author, so the override was a convenient simplification ("in polling I don't care about offset_date") that happens to be lossy for the general case.

**Is this worth fixing?** Low-medium — real but narrow; fix it when splitting the method.

## What feels like bad design

**The issue.** The routing decision is expressed by *mutating a shared dict* (`iter_kwargs.pop('offset_date', None)`, reassigning `reverse`) rather than by choosing a clear path. Reading the code, you must mentally execute the mutations in order to know the final kwargs — control flow encoded as dict edits.

**ELI15.** Instead of picking a recipe, the cook starts with one recipe and then crosses out and rewrites ingredients as they go. To know what's actually being cooked, you have to follow every edit in order.

**Impact.** Low runtime impact, high cognitive load; it's the structural reason the cross-mode bugs (limit cap, offset_date discard) are easy to miss.

**Robust Fixes / Best Practices.** Build the final kwargs per branch explicitly (`if polling: kwargs = {...} else: kwargs = {...}`) instead of mutating a shared base. Intent becomes readable in one pass.

**Architectural Fix.** Folds into the per-intent method split. Not overkill.

**Speculative defence.** Starting from one kwargs dict and tweaking it is the natural way code grows when you add one mode at a time — each new mode "just needs to adjust a couple of keys," so mutation felt cheaper than restructuring.

**Is this worth fixing?** Low priority on its own; do it opportunistically when addressing traces 6/10.
