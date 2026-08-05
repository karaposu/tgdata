# Trace 2 — Real-Time Event Handler Lifecycle

**Category:** Lifecycle
**One-liner:** How a `@tg.on_new_message` handler is registered, deferred, bound to the live client, and invoked when Telegram pushes a new message.

---

## Entry Point

The `@tg.on_new_message(group_id=...)` decorator (`tgdata.py:405`). Applying it to an `async def` handler is the birth event. The terminal state is `client.run_until_disconnected()` returning (disconnect) inside `run_with_event_loop()` (`tgdata.py:545`).

## Execution Path

1. **Decoration (deferred registration).** `on_new_message` returns a decorator that does *not* wire anything into Telethon yet. It appends `(func, group_id)` to `self._pending_handlers`, lazily creating that list (`tgdata.py:420-428`), and returns `func` unchanged. This is a queue-now, bind-later pattern.
2. **Activation.** The user calls `await tg.run_with_event_loop()` (`tgdata.py:545`), which first calls `_register_pending_handlers()`.
3. **Binding.** `_register_pending_handlers()` (`tgdata.py:432`) gets the live client, then for each queued handler builds a wrapper via a nested `make_handler(f, gid)` closure that re-checks `event.chat_id != gid` before delegating (`tgdata.py:441-447`), and registers it with `client.add_event_handler(handler, events.NewMessage(chats=group_id))` (or unfiltered if no group). The queue is then cleared (`tgdata.py:458`).
4. **Running.** `run_until_disconnected()` blocks; Telethon's update loop invokes the wrappers as messages arrive.
5. **Firing.** On each new message Telethon calls the wrapper → optional group filter → the user's `func(event)`.

## Resource Management

- `_pending_handlers` is created lazily and cleared after binding — no leak across a single `run_with_event_loop`.
- Handlers are owned by the Telethon client; they live as long as the client does. There is **no `remove_event_handler` path** — handlers cannot be unregistered except by tearing down the client.
- This path deliberately does **not** use the `async with client:` teardown pattern (trace 1); it holds the connection open via `run_until_disconnected`, which is the one place the connection is genuinely long-lived.

## Error Path

- There is no try/except around `await f(event)` in the wrapper (`tgdata.py:446`). An exception in a user handler propagates into Telethon's update loop; behavior then depends on Telethon (typically logged and swallowed per-update, but not guaranteed).
- If `run_with_event_loop` is never called, decorated handlers sit in `_pending_handlers` forever and never fire — a silent no-op.

## Performance Characteristics

- Push-based: near-zero idle cost, latency bounded by Telegram's push, not by a poll interval. This is strictly better than `poll_for_messages` (trace 10) for latency and for not missing messages.
- The redundant `event.chat_id != gid` check inside the wrapper duplicates the filtering already done by `events.NewMessage(chats=group_id)` — negligible cost but dead belt-and-suspenders logic.

## Observable Effects

- Log lines "Queued handler..." at decoration and "Registered handler..." at binding (`tgdata.py:426,456`).
- The process blocks in `run_until_disconnected` until Ctrl-C / disconnect.
- User side effects (prints, DB writes) fire per incoming message.

## Why This Design

Deferring registration lets users declare handlers at module load time (decorator syntax) before any event loop or connection exists — a clean ergonomic. Binding is postponed to `run_with_event_loop` when a live client is guaranteed. This is the idiomatic way to bridge "declarative decorator at import" with "imperative registration needs a connected client."

---

## What feels incomplete

**The issue.** The lifecycle is one-directional: handlers can be added but never removed, and there's no lifecycle hook for "handler errored" or "reconnected." The nested-closure indirection in `make_handler` (an `async def` that just returns another function, awaited for no reason — `tgdata.py:441-449`) suggests the code was iterated on without being finished/cleaned.

**ELI15.** You can sign people up to react to new messages, but you can never un-sign them, and if one of them trips and falls, nobody catches them. Also the sign-up code takes a weirdly long, roundabout path to do something simple.

**Impact.** Fine for a run-once script; limiting for any app that adds/removes subscriptions dynamically or needs resilience. The awaited-closure is harmless but confusing to maintainers.

**Robust Fixes / Best Practices.** Keep handles returned by `add_event_handler` so they can be removed; wrap `await f(event)` in try/except with logging so one bad handler doesn't destabilize the loop; simplify `make_handler` to a plain (non-async) factory or a `functools.partial`.

**Architectural Fix.** A small subscription registry object that tracks `{handler_id: (func, filter, telethon_handle)}` with `subscribe`/`unsubscribe`. *Mild overkill* for the current single-script usage, but the try/except and the closure simplification are clearly worth doing regardless.

**Speculative defence.** The feature was likely built to satisfy the "real-time" smoke test and the README's example, both of which register a handler and run forever. Removal and error isolation were never needed by those flows, so they were never built. The awaited closure is a classic "it worked, moved on" artifact.

**Is this worth fixing?** The try/except is worth doing (low effort, real resilience). Removal support is only worth it if dynamic subscription becomes a requirement.

## What feels vulnerable

**The issue.** An unhandled exception in a user handler is not contained (`tgdata.py:446`). Depending on Telethon's version, a raising handler can disrupt update processing or simply vanish without the user knowing their handler failed.

**ELI15.** If your "what to do on a new message" code crashes, the crash isn't caught here — it either quietly disappears or can knock the listener off balance, and you may never find out a message wasn't processed.

**Impact.** Silent processing failures in the exact place users put their important logic (writing to a DB, forwarding, alerting). Hard to diagnose.

**Robust Fixes / Best Practices.** Wrap each invocation: `try: await f(event) except Exception: logger.exception(...)`. Optionally surface an error callback so the app can react.

**Architectural Fix.** Same subscription-registry as above, with per-handler error policy. Overkill unless the app needs it; the try/except alone is the 90% fix.

**Speculative defence.** In the author's tests, handlers just `print()` — they don't fail — so there was never a crash to contain. The risk only appears with real, side-effecting handlers the author never ran.

**Is this worth fixing?** Yes, low effort / good return — wrap the call.

## What feels like bad design

**The issue.** The redundant in-wrapper `event.chat_id != gid` filter (`tgdata.py:444`) duplicates the server-side/Telethon filter `events.NewMessage(chats=group_id)` (`tgdata.py:452`). Two filters for one job, and they can disagree (e.g. `chat_id` sign/format vs the resolved `chats` entity), which could cause a handler to silently never fire.

**ELI15.** The bouncer checks your ID at the door, and then a second bouncer inside checks it again using a slightly different rulebook. If the two rulebooks disagree, you get thrown out even though you were let in — for no reason there should be two checks at all.

**Impact.** Mostly redundant work, but the subtle risk is a format mismatch between `event.chat_id` (often the `-100…` form for channels) and the `group_id` the user passed (which may be a raw id or `@username`), causing the manual check to reject valid events.

**Robust Fixes / Best Practices.** Trust Telethon's `events.NewMessage(chats=...)` for filtering and delete the manual check; or, if manual filtering is intended for the unfiltered-registration case, apply it only there. Normalize the id form before comparing.

**Architectural Fix.** None needed — this is a deletion, not an addition.

**Speculative defence.** Likely written defensively ("filter just in case") while the author was unsure whether `events.NewMessage(chats=...)` reliably filtered — a belt-and-suspenders reflex left in after it turned out to work.

**Is this worth fixing?** Low priority, but delete-the-redundant-check is a clean, safe simplification.
