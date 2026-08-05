# Trace 8 — Client Acquisition Routing (Pool vs Primary + Health-Check Gate)

**Category:** Decision / routing
**One-liner:** How `get_client()` decides which connection to hand back — pooled vs primary — and how a time-gated health check is smuggled into that accessor.

---

## Entry Point

`ConnectionEngine.get_client()` (`connection_engine.py:133`). Every Telegram operation routes through here. Terminal state is a returned `TelegramClient` (pooled or primary).

## Execution Path

1. **Health-check gate (side effect).** Compute `now - self._last_health_check`; if it exceeds `self._health_check_interval` (300s), run `await self.health_check()` and reset the timestamp (`connection_engine.py:138-142`). This happens *before* returning a client, on whatever call trips the interval.
2. **Route: pool vs primary.** `if self.pool_size > 1 and self._pool:` → `return await self._pool.get_connection()` (round-robin, rate-limit-aware) (`connection_engine.py:145-146`). Otherwise fall through to the primary path.
3. **Primary path.** Lazily `_init_primary_client()` on first call; if the cached client isn't connected, `_connect_with_retry()` (`connection_engine.py:149-153`).
4. **Return.** Hand back the chosen client.

`ConnectionPool.get_connection()` (`connection_engine.py:29`) itself routes: round-robin skipping connections whose `flood_wait_until` is in the future, falling back to the least-rate-limited one if all are limited.

## Resource Management

- Primary client cached in `self._primary_client`; pool clients in `self._pool.connections`.
- The health check calls `get_me()` on each live connection — a network round-trip charged to whichever unlucky operation trips the 5-minute gate.

## Error Path

- `health_check()` is internally wrapped in try/except and records errors into a status dict rather than raising (`connection_engine.py:238-278`) — so a failed health check won't break `get_client`.
- If `health_check` itself hit a `FloodWaitError` via `get_me`, it's caught as a generic `Exception` and logged, not specially handled.

## Performance Characteristics

- Steady state (`pool_size==1`): one branch + occasional 300s health round-trip.
- The health check adds latency spikes to random user operations (whichever one crosses the interval), rather than running on a background timer.
- The pool route is essentially never taken in practice (`pool_size` defaults to 1, and per-call teardown undermines pooling — trace 1).

## Observable Effects

- Periodic "Performing connection health check..." logs (`connection_engine.py:229`).
- A `get_me()` round-trip roughly every 5 minutes of activity.

## Why This Design

Centralizing client acquisition is good — one place decides connection strategy. The pool-vs-primary branch cleanly supports an optional scaling mode. Piggy-backing the health check on `get_client` avoids needing a background task/event loop just for liveness, which is a pragmatic choice for a library that can't assume it owns the loop.

---

## What feels incomplete

**The issue.** The pool route is aspirational: `pool_size` defaults to 1, most call sites wrap the client in `async with` (which would disconnect pooled connections too — trace 1), and no public API encourages pooling. The routing branch exists but the branch it guards is effectively dead.

**ELI15.** There's a fast lane built for when you have many connections, but the car is hard-wired to only ever have one connection, and the way trips are taken would wreck the fast lane anyway. So the fast lane is painted on but unused.

**Impact.** Maintenance weight and reader confusion (a whole `ConnectionPool` class + rate-limit bookkeeping) for zero realized benefit; a false impression that scaling is supported.

**Robust Fixes / Best Practices.** Either make pooling real (fix trace 1's teardown so pooled connections persist, and expose/ document `connection_pool_size`) or delete the pool and its routing until it's needed (YAGNI).

**Architectural Fix.** If pooling is wanted: a persistent-connection manager (trace 1 fix) that the pool sits on top of. *Currently overkill* — a single persistent connection covers the real workload; pooling matters only at extraction scale that isn't in evidence.

**Speculative defence.** Pooling was likely built proactively for an imagined high-throughput ETL future (the `deprecated/` ETL docs hint at bigger ambitions), then never exercised because the actual workload was one account pulling modest groups.

**Is this worth fixing?** Low priority — decide "commit or delete" during the trace-1 cleanup.

## What feels vulnerable

**The issue.** The health check is a hidden side effect of an accessor and runs *inline* on a user operation. It also calls `get_me()` (a network call) which can itself hit rate limits or fail — turning a routine "get me a client" into a latency spike or an error surface at an unpredictable time.

**ELI15.** Every so often, when you ask for the keys, the valet secretly takes the car for a lap around the block first — so one random errand takes much longer than expected, and if the lap goes wrong, your errand inherits the problem.

**Impact.** Unpredictable latency spikes; a health probe that can consume rate-limit budget or fail at the worst moment; harder-to-reason-about accessor semantics (a getter that does I/O).

**Robust Fixes / Best Practices.** Make liveness lazy and reactive instead of proactive: rely on the existing `is_connected()`/reconnect path and only probe on actual failure. If a periodic check is truly wanted, run it as an opt-in background task, not inside `get_client`.

**Architectural Fix.** A background heartbeat task owned by `ConnectionEngine`, started on connect and cancelled on close. *Mild overkill for a single connection* that already reconnects on demand — reactive recovery is simpler and sufficient here.

**Speculative defence.** Without owning the event loop, a library can't easily run background timers, so hanging the check off the most-called method was the pragmatic way to get *some* periodic liveness. Given the per-op reconnect already revalidates the connection, the check rarely does anything, so its cost went unnoticed.

**Is this worth fixing?** Medium — the inline network side effect is a real smell; making it reactive is both simpler and safer.

## What feels like bad design

**The issue.** `get_client()` violates command/query separation: it looks like a pure accessor but can perform network I/O, mutate `_last_health_check`, lazily construct clients, and reconnect. One method with four responsibilities and hidden effects.

**ELI15.** A button labeled "show me the client" also secretly builds the client, phones home, reconnects, and updates a clock. Buttons should do the one thing they say.

**Impact.** Hard to test and reason about; every caller inherits unpredictable behavior. It's the structural reason traces 1 and 8's issues are entangled.

**Robust Fixes / Best Practices.** Separate concerns: `connect()` (explicit, idempotent, does I/O once) vs `client` (pure accessor returning the connected client). Move liveness out of the accessor.

**Architectural Fix.** The persistent-`session()` context manager from trace 1 subsumes this: connect once, hand out the live client, no per-access side effects. Not overkill — it's the same high-leverage change.

**Speculative defence.** Lazy-everything-in-the-getter is a common convenience pattern ("callers don't have to remember to connect"), and it genuinely makes the call sites terse. The hidden costs only bite under load or in tests, neither of which pressured this code.

**Is this worth fixing?** Medium — bundle it with the trace-1 connection-lifecycle fix rather than as a standalone change.
