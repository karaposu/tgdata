# Trace 12 — Rate Limiting as a Cross-Cutting Mechanism

**Category:** Cross-cutting mechanism
**One-liner:** How flood/rate-limit awareness is (partially) wired across connect, fetch, and pool layers — three uncoordinated implementations of one concern.

---

## Entry Point

There is no single entry point — that's the point. The mechanism surfaces in three places:
1. **Connect-time:** `_connect_with_retry` catches `FloodWaitError` around `client.start()` (`connection_engine.py:207-216`).
2. **Fetch-time:** `fetch_messages` catches `FloodWaitError` and delegates to `handle_rate_limit` (`message_engine.py:193-194`; policy at `connection_engine.py:297-321`).
3. **Pool-level:** `ConnectionPool.mark_rate_limited` + `RateLimitInfo.flood_wait_until` track per-connection cool-down for round-robin skipping (`connection_engine.py:51-56`, consulted in `get_connection` `connection_engine.py:40-49`).

Terminal state of the mechanism is "the system waited the mandated time and resumed" (or, for the pool, "routed around the limited connection").

## Execution Path

- The **policy** (`handle_rate_limit`) is the most complete: it computes a wait (`wait` = exact `e.seconds`; `exponential` = `e.seconds * (1 + jitter)`, jitter 0–30%), optionally marks the pool connection, and `asyncio.sleep`s.
- The **connect-time** handler duplicates a simpler version inline (sleep `e.seconds`, retry `start()` once) and does *not* use the strategy or jitter.
- The **pool bookkeeping** exists to skip limited connections, but since pooling is effectively inert (trace 8), this branch rarely runs.
- `RateLimitInfo` also carries `requests_made`, `window_start`, `last_request` fields that are **never read or written** anywhere — a stub for proactive (pre-emptive) rate limiting that was never implemented.

## Resource Management

- The only managed resource is *time* (sleeps) and the `flood_wait_until` timestamps on pool connections.
- No global rate budget is tracked; the system is purely reactive (wait when told), never proactive (throttle before hitting the limit) — despite `RateLimitInfo`'s unused fields implying proactive intent.

## Error Path

- The mechanism *is* the error path for `FloodWaitError`. Non-flood errors bypass it entirely (generic re-raise).
- `batch_delay` (`fetch_messages`) is a *separate*, manual throttle knob (sleep between batches) that overlaps conceptually with rate limiting but isn't integrated with it — and is dropped on retry (trace 9).

## Performance Characteristics

- Correctly cooperative (waits the server-mandated time) but reactive-only: the system will happily sprint into a flood, then stall, rather than pacing to avoid it.
- `exponential` + jitter mitigates thundering-herd across multiple clients — but with `pool_size==1` there's only one client, so jitter buys little in practice.

## Observable Effects

- Warning logs at each flood ("Rate limit hit! Waiting...", "Connection ... rate-limited for Ns").
- Pauses in throughput; with pooling, traffic shifting off a limited connection.

## Why This Design

Reactive `FloodWaitError` handling is the *correct baseline* for Telegram — the server dictates the wait, so honoring it is mandatory and sufficient for correctness. The strategy/jitter option and the pool cool-down show the author thinking ahead about multi-connection scaling. Keeping `batch_delay` as a caller-controlled knob gives users a crude proactive lever without a full rate-budget system.

---

## What feels incomplete

**The issue.** The mechanism is three partial implementations plus a stub: a full policy (`handle_rate_limit`) that only the fetch path uses, a simpler duplicate at connect time, dead pool bookkeeping, and `RateLimitInfo`'s unused proactive fields (`requests_made`, `window_start`, `last_request`). Proactive rate limiting was scaffolded but never built.

**ELI15.** There are three different "don't go too fast" systems that don't talk to each other, plus an empty dashboard with gauges (requests-per-minute) that nothing ever fills in. The car only brakes *after* the speed camera flashes — it never watches its own speedometer.

**Impact.** Inconsistent behavior by location; a false impression (from `RateLimitInfo`) that request-rate tracking exists; missed opportunity to avoid floods entirely by self-pacing. No correctness bug, but real dead weight and divergence.

**Robust Fixes / Best Practices.** One rate-limit component used everywhere. Either implement the proactive side (token bucket over `requests_made`/`window_start`) or delete those fields. Fold `batch_delay` into the same component as the user-facing pacing knob.

**Architectural Fix.** A single `RateLimiter` (reactive flood handling + optional token-bucket pacing) injected into the connection engine and consulted by all outbound calls. *Right-sized if scaling is real*; *overkill if the tool stays single-account small* — in that case, just delete the unused fields and the duplicate connect-time handler, keeping the one policy.

**Speculative defence.** The proactive fields are a "we'll add real rate limiting later" placeholder; reactive handling proved sufficient for the author's volume, so the proactive half was never needed and never finished. The duplicate connect-time handler predates the richer policy and wasn't retro-fitted.

**Is this worth fixing?** Medium — consolidation + dead-field deletion is a clean win; proactive limiting only if volume demands it.

## What feels vulnerable

**The issue.** No cap on cumulative waiting and no coordination between the layers means pathological flood conditions compound: a fetch-time flood restarts the fetch (trace 9), which reconnects (possibly connect-time flood), each waiting independently, with no global "give up / alert" and no shared view of how limited the account currently is.

**ELI15.** Each part of the program waits out the speed camera on its own, and none of them compares notes. If the road is covered in cameras, the trip can stall over and over with nobody deciding "this isn't working, stop."

**Impact.** Potential very long unbounded stalls under sustained limiting; hard to observe total time lost; the account can stay near its limit with no backpressure to the caller.

**Robust Fixes / Best Practices.** A shared limiter with a cumulative-wait budget and a terminal error when exceeded; expose current limit state via `health_check`/metrics so callers can back off.

**Architectural Fix.** The single `RateLimiter` above, holding shared state. Proportionate if scaling; otherwise a simple max-total-wait cap suffices.

**Speculative defence.** Sustained flooding just doesn't happen at hobby volume — a single account pulling modest groups hits at most the occasional short flood, so unbounded compounding was never observed.

**Is this worth fixing?** Low-medium — a total-wait cap is cheap insurance; full coordination only at scale.

## What feels like bad design

**The issue.** Rate limiting is scattered rather than cross-cut: the concern lives in `_connect_with_retry`, `handle_rate_limit`, `ConnectionPool`, `RateLimitInfo`, and (informally) `batch_delay`. A cross-cutting concern implemented in five spots with two behaviors and one dead stub is the definition of tangled.

**ELI15.** The rule "don't go too fast" is written on five different sticky notes in five different rooms, and two of them say slightly different things while one is blank. There's no single rulebook.

**Impact.** Changing the rate-limit policy means touching several files and risking divergence; readers can't find "the" rate-limit logic. It's the structural cause of trace 9's inconsistencies.

**Robust Fixes / Best Practices.** Make it a true cross-cutting mechanism: one component (or a `@rate_limited` decorator) wrapping every outbound Telegram call, so connect, fetch, count, search, and list all share identical behavior.

**Architectural Fix.** Decorator/middleware around the client's outbound methods. *Proportionate* — this is exactly the kind of concern decorators exist for, and it deletes duplication.

**Speculative defence.** The pieces accreted as features arrived (connect handling first, fetch policy later, pool tracking for a scaling mode that didn't materialize), and no pass ever unified them because each worked well enough in isolation for the author's use.

**Is this worth fixing?** Medium — high readability/consistency payoff, pairs naturally with the trace-9 retry rework.
