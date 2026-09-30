# Issue 9 — The fetch that cannot say where it is: the heartbeat's two blind spots, and a count with no denominator

**Status:** 📋 PROPOSED (2026-08-23). Nothing here is a correctness bug — every fetch returns the right rows today. This is about a long fetch being **unable to describe itself** to the program that called it.
**Where it bites:** any fetch long enough that a human is watching and wondering — a first-contact pull, a paced backfill, a resume over a large backlog. Exactly the runs that take minutes, and exactly the ones where "still working" and "hung" are indistinguishable from outside.
**Severity:** medium — no data loss, no wrong answers; purely observability. But it turns every long run into a leap of faith, and it pushes callers toward the worst possible workaround: killing a healthy fetch because it *looked* dead.
**Relationship to other docs:** builds directly on the liveness `heartbeat` added in 0.0.6 (`fetch_messages(heartbeat=...)`) — that callback solved the *hang detection* problem and this issue is the part it did not reach. `scoped/8` is the reason it matters more now: with the connection kept alive, single fetches are legitimately long-running, so a long silence is normal rather than suspicious.

---

## The symptom, from the caller's side

A consumer runs a fetch. It prints something like `fetch…` and then nothing happens for several minutes. There is no way, from outside the library, to distinguish:

- working normally, walking a big backlog;
- sleeping through a configured batch pause;
- waiting out a flood-wait;
- hung on a dead connection or a locked session file.

The `heartbeat` callback answered the *last* of those — a caller can now run a watchdog and cancel on true silence. What it cannot do is tell the caller **how the work is going**, and it happens to go quiet during two specific windows that are precisely the ones a watching human distrusts.

---

## Part (a) — the heartbeat is silent exactly when a fetch looks most dead

### What the design intends

The comment above `_beat` states the intent plainly: called with a phase label on **every sign of life**. Consumers are meant to treat any silence as pathological, which is only safe if a healthy fetch is never silent.

### What actually happens

`_beat` is currently reached from five places — `"messages"`, `"pause"`, `"flood-wait Ns"`, `"dialog-sync"`, `"media"`. Four of those are healthy and correct. The problem is where the first one sits.

In `fetch_messages`, the first `_beat("messages")` fires **inside the message loop, after the skip filter**. That leaves two windows with no sign of life at all:

**Window 1 — everything before the first in-window message.** Connecting, authenticating, resolving the group entity, and the first Telegram round-trip all happen before any message is processed. On a cold connection against a large group this is the longest single pause in the whole run, and it produces zero beats. It is also the window in which a genuinely broken setup (no session, wrong entity, dead network) actually hangs — so the one moment a caller most wants a tick is the one moment there is none.

**Window 2 — the already-seen skip scan.** When resuming with `min_id`, messages at or below the cursor take an early `continue`:

```python
if original_min_id is not None and msg.id <= original_min_id:
    ...
    iterated_count += 1
    continue          # <-- returns to the top of the loop; _beat is never reached

_beat("messages")
```

So a resume that iterates thousands of already-seen messages before reaching new ones is **completely silent to the heartbeat**, while being perfectly healthy and doing real work. A caller with a strict stall threshold will cancel it.

### What the fix looks like

Beat in both windows, with phase labels that say which one is happening:

- before/around connection and entity resolution — e.g. `"connecting"`, `"resolving"`, `"fetching"` — so the startup interval is covered and *named*;
- on the skip path, so the scan reports life — either by moving `_beat` above the skip filter, or by beating on the skip branch with a distinct label such as `"skipping"`.

The label matters as much as the tick. `"skipping"` and `"messages"` are both healthy, but a caller that can tell them apart can say *"walking past 12,000 already-seen messages"* instead of *"working…"* — and that sentence is the entire difference between a user waiting calmly and a user reaching for Ctrl-C.

---

## Part (b) — `total_processed` rises forever with nothing to divide it by

### What the design intends

`batch_callback` receives a `batch_info` dict that already carries real progress data:

```python
{'batch_num': …, 'batch_size': …, 'total_processed': …, 'group_id': …, 'is_final': …}
```

A caller can show a rising count, which is genuinely useful and better than nothing.

### What actually happens

Every field describes **what has already happened**. Nothing describes the size of the job. There is no total, no remaining, no position in the id range, no date reached. So a consumer can render:

```
fetch  1,400 messages…
```

but never:

```
fetch  1,400 of ~5,200 (27%) · now at 2026-03-14 · ~4 min left
```

No percentage, no bar, no estimate — not because the consumer lacks the data, but because the number that would make it meaningful never crosses the boundary. This is the difference between a spinner and a progress bar, and for multi-minute fetches it is the difference between a caller trusting the run and babysitting it.

### What the fix looks like

Two candidates, either useful alone, and both cheap because the library already holds the values internally:

1. **Position, in `batch_info`.** The oldest/newest message id and date in the batch just handed over — the caller can then say *"now at 2026-03-14"*, which conveys real progress on a date-bounded walk without needing any total at all. Cheapest of the two, and it composes with the existing `total_processed`.
2. **A denominator, once known.** Whatever bound the fetch is actually working against — the effective limit, the id span between the cursor and the group's newest message, or an estimate — emitted once at the start (or on every `batch_info`). This is what unlocks a real percentage and an ETA.

Worth noting for whoever builds this: a caller cannot compute either of these itself. `total_processed` alone cannot be turned into progress, and the caller has no view of the id range being walked.

---

## How this will be used

The consumer pattern is already in production and only the inputs are missing. A caller today wires both hooks:

```python
await tg.get_messages(
    group_id=…,
    batch_size=200, batch_callback=on_batch,   # per-chunk reports
    heartbeat=on_beat,                          # liveness ticks
)
```

`on_beat` drives a **watchdog** — a fetch that goes silent past a threshold is cancelled and retried — and with part (a) it can additionally drive a live status line, because ticks would arrive during startup and skip scans rather than only once messages flow.

`on_batch` drives the **display**. With part (b) that display upgrades from a rising number to a real position:

```
fetch  connecting…                          <- part (a), window 1
fetch  skipping 12,000 already-seen…        <- part (a), window 2
fetch  1,400 of ~5,200 (27%) · at 2026-03-14   <- part (b)
```

The same values feed a dashboard progress bar rather than a pulse, and let a paced backfill show an honest estimate of when it will finish.

---

## Explicitly out of scope

- **The heartbeat mechanism itself** — it exists and works; this only extends where it fires and what it is called with.
- **Any change to what a fetch returns.** Rows, ordering, filtering and the batching contract stay exactly as they are; every addition here is a new key in `batch_info` or a new phase label, so existing consumers are unaffected.
- **Rate-limit and connection behaviour** — `scoped/8`'s territory.
