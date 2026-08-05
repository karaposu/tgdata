# Trace 9 — FloodWait Rate-Limit Recovery

**Category:** Error / recovery
**One-liner:** What happens when Telegram returns `FloodWaitError` mid-fetch: sleep for the mandated time, then recursively retry the whole fetch — dropping some parameters and risking duplicate batch delivery.

---

## Entry Point

The `except FloodWaitError as e:` block in `fetch_messages` (`message_engine.py:193`). Entry is the failure event (Telegram signalling "you're going too fast, wait N seconds"). Terminal state is either a successful retried fetch or propagation of a non-flood exception.

## Execution Path

1. **Catch.** A `FloodWaitError` raised anywhere in the fetch loop unwinds out of the `async with client:` block (disconnecting the client) into the handler.
2. **Delegate to strategy.** `await self.connection_engine.handle_rate_limit(e, client, strategy=rate_limit_strategy)` (`message_engine.py:194`) → sleeps `e.seconds` (`wait`) or `e.seconds * (1 + jitter)` with 0–30% random jitter (`exponential`) (`connection_engine.py:297-321`), and marks the pool connection rate-limited if a pool exists.
3. **Recursive retry.** The handler returns; `fetch_messages` **calls itself** with the original args (`message_engine.py:196-206`) — re-acquiring a client (reconnect), re-resolving the entity, and re-streaming from the top.
4. **Terminal.** The retry either succeeds or, if it floods again, recurses again (unbounded), or a different exception propagates via the generic `except` (`message_engine.py:208`).

There's a second, independent flood handler at connect time in `_connect_with_retry` (`connection_engine.py:207-216`): sleep then retry `start()` once.

## Resource Management

- During the sleep, the connection is already torn down (the `async with` exited on the exception) — so we correctly hold no socket while waiting.
- Recursion grows the Python call stack by one frame per flood event (practically bounded by how many floods occur, but unbounded in principle).
- Any `batch_messages` accumulated before the flood are discarded when the frame unwinds; the retry starts a fresh buffer.

## Error Path

- `handle_rate_limit` has no failure path of its own (just sleeps).
- The recursive call re-enters the same try/except, so repeated floods loop indefinitely with no cap and no backoff *escalation* across attempts (the `wait` strategy waits the same server-mandated time each time; jitter doesn't compound).
- **Latent bug:** the handler references `client` (`message_engine.py:194`); if `get_client()` raised before `client` was bound, this is a `NameError`. Mitigated only because `get_client` absorbs floods internally.

## Performance Characteristics

- Correctly respects Telegram's mandated wait — the safe, cooperative behavior.
- But a mid-large-fetch flood throws away *all* progress and restarts from message #1, re-doing every already-processed message. For a big pull that floods near the end, this is potentially catastrophic re-work (and can re-trigger floods).

## Observable Effects

- Log "Rate limit hit! Waiting Ns..." or the exponential variant (`connection_engine.py:313,316`).
- A pause, then a full re-fetch. If batching, the batch callback may fire on the *same* early messages again (duplicate batches).

## Why This Design

Sleeping the server-mandated `FloodWaitError.seconds` is exactly right — you must wait, and Telegram tells you how long. The `wait`/`exponential` strategy toggle with jitter shows awareness of thundering-herd concerns. Recursion is a terse way to "try again after waiting."

---

## What feels incomplete

**The issue.** The retry is not idempotent and not resumable: it restarts the entire fetch instead of continuing from the last processed message. It also **drops `batch_delay` and `rate_limit_strategy`** on the recursive call (`message_engine.py:196-206` omits them), so a retried fetch silently loses its batch pacing and reverts to the default `wait` strategy — the opposite of what a rate-limited caller wants.

**ELI15.** After being told "wait a minute," the program starts the whole job over from the beginning instead of resuming where it stopped — and it forgets the very settings you chose to *avoid* getting rate-limited, going back to the default pace. So the retry is more likely to get throttled again.

**Impact.** Wasted work and re-triggered floods on large fetches; duplicate batch deliveries; the caller's anti-throttling settings evaporate exactly when they matter most. On a big channel this can turn one flood into an endless restart loop.

**Robust Fixes / Best Practices.** Resume from the last successful `MessageId` (track it, set `min_id` on retry) instead of restarting. Forward *all* parameters on retry (or better, factor the retry into a decorator/loop so it can't drift from the call signature). Add a max-attempts cap.

**Architectural Fix.** Replace recursion with an internal `while` loop around a *resumable* streamer that remembers its cursor, wrapped by a generic `@retry_on_floodwait(max_attempts, strategy)` decorator applied once. *Proportionate* — it removes three problems (non-resumption, arg-drift, unbounded recursion) at once.

**Speculative defence.** The author's fetches were small enough that a flood rarely hit, and when it did, restarting 100-ish messages was cheap and invisible. The dropped args are a copy-paste omission — the recursive call was written by hand rather than delegating, so it drifted from the signature as parameters were added later (`batch_delay`, `rate_limit_strategy` were newer).

**Is this worth fixing?** Yes — medium-high. The arg-drop is a clear bug; non-resumption is a real scalability hazard.

## What feels vulnerable

**The issue.** Unbounded recursion with no attempt cap. Persistent rate-limiting (or a pathological group) yields indefinite retries and ever-growing stack depth, with the batch callback potentially re-firing on duplicates each cycle.

**ELI15.** If Telegram keeps saying "slow down," the program keeps restarting forever, stacking one attempt on top of another with no give-up point — and may keep re-handing your processor the same early messages.

**Impact.** Potential infinite loop / eventual stack pressure; duplicate downstream side effects in batch consumers (double DB inserts, etc.).

**Robust Fixes / Best Practices.** Cap attempts and surface a clear terminal error after the cap; make batch delivery idempotent or only deliver batches that weren't delivered pre-flood (resumption solves this too).

**Architectural Fix.** Same retry-loop + resumable-cursor as above. Not overkill.

**Speculative defence.** In normal use, `FloodWaitError.seconds` is short and the next attempt succeeds, so the loop terminates in one or two hops — the infinite case never showed up. Duplicate batches went unnoticed because the smoke tests use tiny batch counts and don't assert uniqueness.

**Is this worth fixing?** Medium — the attempt cap is cheap insurance; batch idempotency matters if anyone uses `batch_callback` for writes.

## What feels like bad design

**The issue.** Rate-limit handling is split across two places with different logic (connect-time single retry in `_connect_with_retry`; fetch-time strategied retry in `handle_rate_limit`), and the fetch handler reaches back into the connection engine while also depending on a possibly-unbound `client`. Responsibility for "what to do on a flood" is smeared across layers (see trace 12).

**ELI15.** Two different departments each have their own rulebook for "what to do when told to slow down," and they don't match; one of them also grabs a tool it might not have picked up yet.

**Impact.** Inconsistent behavior depending on *where* the flood happens; the `NameError` latent risk; harder to change the policy in one place.

**Robust Fixes / Best Practices.** One rate-limit policy object/decorator used by *both* connect and fetch paths; never reference a client that may be unbound (bind it before the try, or don't pass it).

**Architectural Fix.** Centralize in the cross-cutting mechanism described in trace 12. Proportionate; it deduplicates real logic.

**Speculative defence.** The connect-time handler came first (you need *some* flood handling just to log in), and the richer fetch-time handler was added later for the data path, without folding the earlier one in. Two handlers is the residue of incremental growth.

**Is this worth fixing?** Medium — consolidation is worthwhile and pairs naturally with trace 12.
