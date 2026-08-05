# Issue 7 — Real-time handlers with a group filter never fire

**Status:** ✅ IMPLEMENTED (2026-07-19) — Approach A: the `event.chat_id != gid` kill-switch deleted; filtering fully delegated to Telethon's `events.NewMessage(chats=group_id)`; the awaited-factory `make_handler` collapsed into a plain `make_safe_handler` that wraps the user handler in try/except + `logger.exception`. Proven deterministically: 2 handlers register carrying `chats=4611400320` (the positive id the old guard rejected), 1 carries `chats=None`; direct-invoke shows call-through works and a crashing handler is contained + logged with traceback. Corroborated live: the unfiltered handler fired on a real incoming message this session.
**Where it bites:** the real-time listening feature — `@tg.on_new_message(group_id=…)`. Any handler registered **with a group filter** silently receives nothing, ever. (Handlers registered with *no* filter work fine.)
**Severity:** high for anyone using per-group real-time monitoring — the feature is dead on arrival for the common ways of naming a group. Silent: no error, the handler simply never runs.

---

## What you'd expect

```python
@tg.on_new_message(group_id=4611400320)   # "call me for new messages in THIS group"
async def handler(event):
    ...
```

New message arrives in that group → your handler runs.

## What actually happens

Your handler never runs. Not once. No error, no log — indistinguishable from "the group was quiet." Meanwhile the *unfiltered* form (`@tg.on_new_message()`, all groups) works normally, which makes the broken case even more confusing.

## Why it happens (plain language)

The message passes through **two bouncers**, and the second one turns everyone away.

- **Bouncer #1 — Telegram's own doorman (works correctly).** When the handler is registered, the group filter is handed to the underlying library, which properly understands every way of naming a group — the plain number, the `@username`, all of it — and only lets through events from that group. This bouncer alone does the whole job.
- **Bouncer #2 — our own re-check inside the door (broken).** After the doorman has already admitted the right guests, our code checks the guest again: *"does the event's chat number equal the number the caller gave me?"* — comparing two things written in **different formats**.

The format mismatch: internally, Telegram reports a group's identity with a **minus-sign prefix** (large groups get an extra `-100…` on the front). So the event says something like `-1004611400320`, while the caller wrote `4611400320` (the plain positive number you see in group lists — including in this project's own tests) or `'@groupname'` (text). A negative internal number never equals a positive one, and never equals a piece of text. **The re-check fails for every message, and the wrapper returns before your handler is called.**

Two checks for one job — and the second, redundant one rejects everyone the first correctly admitted.

## The tell-tale evidence

The project's own test files record the pain:

- The tests pass exactly the doomed formats (`group_id=4611400320` — a plain positive number).
- `test_07_on_new_message_simple.py` contains a **second** test that abandons the decorator entirely and registers the handler *directly on the underlying client* — bypassing bouncer #2. That's the classic shape of a workaround written after the official path mysteriously produced silence.
- The tests that "pass" for this feature either use the unfiltered form (which works) or only check that registration didn't crash — never that a filtered handler actually *fired*.

(An earlier internal review flagged this double-check as merely "redundant, low priority." That was wrong — it isn't just redundant, it's the kill switch.)

## Why the second bouncer existed at all (git archaeology)

It wasn't written as a double-check — **it used to be the only check.** The previous version (`9a98c0e`) registered every handler for **all** chats with no platform filter at all (bare `events.NewMessage()`), and the manual `event.chat_id != group_id` line inside the wrapper was the *entire* filtering mechanism. Load-bearing, not defensive.

Commit `abbd077` ("fix") then rewrote registration — deferring it to fix a real decoration-time race (`asyncio.create_task` with possibly no loop), adding the closure-safe `make_handler` factory (the standard cure for Python's loop-variable capture gotcha — which is why that odd construct exists), and introducing the correct platform filter `events.NewMessage(chats=group_id)`. The old manual line was carried along rather than retired — "add the new mechanism, keep the old one for safety." That's the moment it became a second bouncer.

Two ironies the history shows:
1. **The format mismatch is original** — `event.chat_id` (marked, negative) vs the caller's positive id was wrong in the *old* design too, so the group-filtered path never worked in any era. The rewrite preserved the breakage seamlessly by keeping the one line that caused it.
2. **"Keep it for safety" was the unsafe choice** — redundancy is only harmless when both layers speak the same id dialect; here the kept layer vetoes everything the correct layer admits.

## Who cares / impact

- Anyone using per-group real-time monitoring — the README-advertised pattern.
- **propertybot:** real-time is the natural upgrade path from 3×/day polling (fresher listings, no cursor gymnastics), and the planned in-group auto-ingest would sit on exactly this feature. As-is, the per-group form yields silence.

---

## Solution approaches (high level)

### Approach A — Fire the second bouncer *(recommended)*

Delete the inner re-check. Trust the platform's own filter — it's correct, complete (numbers, `-100…` forms, usernames), and already scoped the events before our code sees them. The fix is *removing* ~4 lines, not adding any. While in that function, one adjacent courtesy: wrap the call to the user's handler so an exception inside it gets logged instead of disappearing into the event loop (a separate small weakness noted in the earlier review).

- **Pros:** minimal; deletes the failure instead of managing it; usernames and every id form start working uniformly.
- **Cons:** none. The re-check protects against nothing the doorman doesn't already handle.

### Approach B — Keep the re-check but teach it the formats *(rejected)*

Normalize both sides to Telegram's internal form before comparing (add the minus, handle the `-100…` prefix, resolve usernames to numbers).

- **Cons:** re-implements, imperfectly and forever, what the platform filter already does perfectly; username resolution would even need network calls. Complexity with zero protective value.

### Approach C — Document "only pass the internal negative form" *(rejected)*

Make callers write `-1004611400320`.

- **Cons:** pushes a platform quirk onto every user; `@username` stays broken; the project's own tests show nobody naturally writes the internal form.

### Recommendation

**A.** Delete the check; add the try/except courtesy around handler invocation; done.

## How we'll verify

1. Register three filtered handlers for the same test group — one with the plain positive id, one with the internal `-100…` form, one with `@username` — plus one unfiltered handler.
2. Send one message to the test group and one to a *different* group.
3. Assert: all three filtered handlers fired exactly once (for the right group only); the unfiltered one fired for both; nothing crashed.
4. Keep it as an asserting regression test — today's tests never verify a filtered handler actually fires, which is how this shipped.

---

## Appendix — exact pointers (for the developer)

- **The kill switch:** `tgdata/tgdata.py:441-447` — `wrapped_handler` does `if gid and event.chat_id != gid: return` before `await f(event)`. `event.chat_id` is Telethon's *marked* id (negative; `-100…` for channels/supergroups) while `gid` is whatever the caller passed (positive int or `'@…'` string). Delete the check (and the now-pointless `make_handler` indirection can collapse too).
- **The correct filter already in place:** `tgdata/tgdata.py:451-454` — `client.add_event_handler(handler, events.NewMessage(chats=group_id))`; Telethon resolves `chats=` through its entity machinery (any id form, usernames).
- **The workaround smell:** `tgdata/smoke_tests/test_07_on_new_message_simple.py:97-123` — second test registers via `@client.on(events.NewMessage(chats=…))` directly, bypassing the decorator.
- **Doomed formats in the project's own usage:** `test_07_on_new_message_simple.py:28` (`4611400320`), `test_08_polling.py:97,182` (positive ids).
- **Adjacent hardening (do in the same touch):** wrap `await f(event)` in try/except + `logger.exception` — an unrelated crash in a user handler currently vanishes into Telethon's loop.
- **Earlier misjudgment to supersede:** `devdocs/archaeology/traces/trace_2.md` called this double-check "redundant … low priority" — it is in fact a functional break of the filtered path.
