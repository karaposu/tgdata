# Architecture Introduction — `tgdata`

*Onboarding notes for a new engineer. This is about **how the code is put together**, not what features it has. Read `small_summary.md` first if you want the "what/why."*

---

## 1. The 30-second mental model

There is **one class you talk to — `TgData`** — and it delegates almost all real work to **two engines** sitting behind it:

```
                 ┌─────────────────────────────────────────┐
   your script → │                 TgData                  │   ← the facade (public API)
                 │  state: current_group, connection/msg   │
                 │         engines, (unused) _metrics       │
                 └───────────────┬─────────────┬───────────┘
                                 │ delegates    │ delegates
                    ┌────────────▼───────┐  ┌───▼───────────────────┐
                    │  ConnectionEngine  │  │     MessageEngine      │
                    │  (transport layer) │◄─┤  (message domain layer)│
                    │  owns Telethon     │  │  depends on ConnEngine │
                    │  client + pool     │  │  via constructor       │
                    └─────────┬──────────┘  └───────────┬───────────┘
                              │                          │
                              ▼                          ▼
                         Telethon  ──────────────►  Telegram servers

   Everything a fetch produces becomes a pandas DataFrame, and from that
   point on the flat, stateless helpers in utils.py + progress.py do the rest.
```

So three tiers, loosely: a **facade** (`TgData`), a **service/engine layer** (`ConnectionEngine`, `MessageEngine`), and a set of **stateless functions + dataclasses** (`utils.py`, `models.py`, `progress.py`). It's small — ~1,700 lines across 7 files — and the skeleton is clean. The messiness is in the seams, which we'll get to honestly in §7.

---

## 2. The main abstractions

Learn these six things and you know the codebase:

- **`TgData` (`tgdata.py`)** — the facade and the only class users are meant to touch. It holds a tiny bit of state (`current_group`, the two engines) and is mostly thin pass-through methods: it picks the target group, wires up an optional default progress printer, and forwards to an engine. It also owns the two *stateful* long-running flows (polling and real-time event registration) because those don't belong to a single fetch.

- **`ConnectionEngine` (`connection_engine.py`)** — the transport layer. It owns the Telethon client's whole lifecycle: reading `config.ini`, authenticating, reconnecting, health checks, and rate-limit handling. Think of it as "everything about *having a live pipe to Telegram*." It's engine #1 and has no idea what a message is.

- **`MessageEngine` (`message_engine.py`)** — the domain layer for messages. Fetching, per-message processing, search, and count all live here. It **depends on `ConnectionEngine`** (passed into its constructor — a light dependency-injection move) and asks it for a client whenever it needs one. Engine #2 knows nothing about connections beyond "give me a client."

- **`ConnectionPool` (inside `connection_engine.py`)** — a helper object implementing the object-pool pattern: a list of clients handed out round-robin, each tagged with `RateLimitInfo` so flood-limited connections get skipped. It's only instantiated when `pool_size > 1`. (In practice it's largely dead — see §7.)

- **The data models (`models.py`)** — four plain `@dataclass`es: `MessageData`, `GroupInfo`, `ConnectionConfig`, `RateLimitInfo`. These are dumb records. The important one is **`MessageData.to_dict()`**, which is the bridge from typed object to pandas row (it renames fields to PascalCase: `MessageId`, `SenderId`, `Message`, `Date`, …). Keep an eye on that method — it defines a schema the whole downstream depends on.

- **The stateless toolbox (`utils.py` + `progress.py`)** — free functions that operate on a DataFrame and return a DataFrame or a dict: export to CSV/JSON, filter by sender/keyword/date, compute statistics, save photos. `ProgressTracker` is a small stateful helper for rate/ETA math. None of these know anything about Telegram — they're pure post-processing over the table.

The organizing concept, then, is **"connection vs. message, wrapped in a facade, producing a table."**

---

## 3. The central data flow — trace `get_messages()` end to end

This is the spine of the system. Follow it once and everything else rhymes:

1. **Entry** — caller invokes `TgData.get_messages(group_id=..., limit=..., after_id=...)`.
2. **Facade bookkeeping** — `TgData` resolves the target group (argument or `current_group`), optionally installs a default console progress callback, and translates `after_id` into a Telethon `min_id` (`after_id + 1`, to make it exclusive). Then it forwards to the engine.
3. **Get a client** — `MessageEngine.fetch_messages()` calls `self.connection_engine.get_client()`. The connection engine ensures the primary client exists, is connected (reconnecting with retry if not), and — as a side effect — runs a health check if 5 minutes have elapsed.
4. **Stream from Telegram** — inside `async with client:` it resolves the entity (`get_entity`, so a numeric ID *or* an `@username` both work) and iterates `client.iter_messages(...)` with kwargs assembled from the filters. Date filters and `min_id` deduplication are applied in the loop.
5. **Per-message transform** — each raw Telethon message goes through `_process_message()`, which pulls sender info, builds a **`MessageData`** dataclass, optionally downloads a profile photo, and returns it. Failures return `None` and are skipped.
6. **The DataFrame pivot** — each `MessageData` is immediately turned into a dict via `.to_dict()` and appended to a list. At the end, that list becomes a **`pandas.DataFrame`**. *This is the architectural keystone (see §4).*
7. **Optional batching** — if `batch_size` + `batch_callback` were given, the loop flushes chunks to the callback as it goes (with an optional inter-batch delay), rather than only returning at the end. This is the streaming/generator-ish escape hatch for large groups.
8. **Return** — the DataFrame flows back up through the facade to the caller.
9. **Output/storage** — there is **no database**. "Storage" is entirely the caller's choice via the `utils` exporters (`export_to_csv` / `export_to_json`) or raw pandas. The *only* persisted state the library itself keeps is the Telethon **`.session` file** (a SQLite auth cache) so you don't re-login every run.

Rate limiting wraps the whole loop: a `FloodWaitError` is caught, handed to `ConnectionEngine.handle_rate_limit()` (which sleeps, with a `wait` or `exponential`+jitter strategy), and then `fetch_messages` **recursively retries itself**.

---

## 4. The DataFrame is the spine — understand this or nothing makes sense

The single most important design decision: **a message is a strongly-typed `MessageData` for about one line of its life, and a loosely-typed pandas row for the rest.**

Once `to_dict()` runs, everything downstream — filtering, statistics, export, printing, and even the polling deduplication — operates on DataFrames addressed by **hardcoded string column names** (`MessageId`, `SenderId`, `Message`, `Date`, `ReplyToId`, `ForwardedFrom`, `PhotoData`). `utils.py` reaches straight into `df['SenderId']`, `df['Message']`, etc.

Consequences you should internalize:
- The DataFrame is the **universal interface** between layers. It's why the `utils` functions can be dumb and Telegram-agnostic, and it's genuinely convenient for analysts (the whole point of the library).
- But the schema contract is **implicit and duplicated**. `MessageData.to_dict()` is the only definition of those column names, and half a dozen call sites depend on it with no shared constant. Rename a key there and things break *silently* three files away. There is no schema validation layer.
- Two of the models are used very unevenly: `MessageData` earns its keep; `GroupInfo` is mostly bypassed (see §7).

---

## 5. The secondary flows

Three other flows branch off the same skeleton:

- **`list_groups()`** — doesn't go through `MessageEngine` at all; `TgData` iterates `client.iter_dialogs()` directly and builds a DataFrame of group/channel metadata **as raw dicts** (not `GroupInfo` objects). It's the discovery entry point — run it to find the IDs/usernames you'll feed to `get_messages`.

- **Polling (`poll_for_messages`)** — a stateful loop living in `TgData`. Each iteration calls `get_messages(after_id=...)`, advances `after_id` to the max ID seen, and — importantly — maintains its own `seen_message_ids` **set** to filter duplicates on top of what `min_id` already does. This belt-and-suspenders dedup exists because of a real, documented message-skipping bug (`issue_1.md`); the defensive layering is a scar from fighting Telegram's `min_id` semantics.

- **Real-time events (`on_new_message` / `run_with_event_loop`)** — a **decorator-based, event-driven** path that leans directly on Telethon's own event system. Handlers registered via the decorator are queued on `self._pending_handlers`, then bound to the live client when the event loop starts. This is a different concurrency model from the request/response fetch flow — push, not pull — bolted onto the same class.

---

## 6. Design patterns in play

The codebase mixes several patterns, mostly coherently:

- **Facade** — `TgData` is a textbook facade over the engines + utils. This is the dominant, load-bearing pattern.
- **Layered architecture** — API → engines → models/utils, with a clean dependency direction (message layer depends on connection layer, never the reverse).
- **Composition + light dependency injection** — `MessageEngine` receives its `ConnectionEngine`; engines are composed into `TgData`. No global singletons.
- **Object pool** — `ConnectionPool` (round-robin + rate-limit-aware).
- **Callback / hook extensibility** — `progress_callback`, `batch_callback`, and the polling `callback` are all inversion-of-control seams so callers can stream-process without the library knowing their intent.
- **Event-driven** — the real-time handler path, delegated to Telethon.
- **Async context manager** — `TgData` supports `async with` (`__aenter__`/`__aexit__` → `close()`), and individual operations use `async with client:` internally.

The consistent thread is **async/await everywhere I/O touches Telegram**, with a clean sync boundary for the pure DataFrame post-processing (`print_messages`, `filter_messages`, `export_messages`, `get_statistics` are all synchronous — they never touch the network).

---

## 7. Where it's inconsistent or in transition — read this before you trust the design

This code was **recently refactored** from a heavier multi-class "ETL framework" (see the `deprecated/` notes and the module docstring "Single class with all features, delegating to specialized engines"). The new facade+engines skeleton is clean, but the refactor left seams and vestigial parts that haven't been reconciled. Be aware:

1. **The connection lifecycle contradicts itself — this is the big one.** `ConnectionEngine` is built for a *persistent, pooled* client: `get_client()` caches `_primary_client`, checks `is_connected()`, reconnects, and runs periodic health checks. But **every actual operation wraps the client in `async with client:`** (`list_groups`, `fetch_messages`, `search_messages`, `get_message_count`), and Telethon's context manager **disconnects on exit**. So the "persistent" connection is torn down and re-established on essentially every call. The persistence machinery and the usage pattern are working against each other.

2. **Connection pooling is effectively dead code.** `pool_size` defaults to 1, and even if you raise it, the `async with client:` teardown at every call site undermines the pool's whole premise. `ConnectionPool` is well-written but, as wired today, load-bearing for nothing. Treat it as aspirational.

3. **Rate-limit handling is spread across three places.** `_connect_with_retry` handles floods during *connect*; `handle_rate_limit` (with strategy + jitter) handles them during *fetch*; and `ConnectionPool.mark_rate_limited` + `RateLimitInfo` track them for the (dead) pool. Overlapping responsibility, no single owner. Also note the fetch retry path recurses via `fetch_messages(...)` but **drops `batch_delay` and `rate_limit_strategy`** on the recursive call — the retry isn't a faithful replay of the original.

4. **`min_id` / polling logic is the least clean area.** `after_id + 1` is computed in `tgdata.py`, then partially *un-computed* in `message_engine.py` (`original_min_id = min_id - 1`), with manual skip-filtering, forced `reverse=True`, `offset_date` popping, and verbose per-message logging — then a *second* dedup set in `poll_for_messages`. This is defensive complexity that accreted around the Telegram skipping bug, not a designed abstraction. Tread carefully when editing it.

5. **Vestigial / unevenly-used state.** `TgData._metrics` is initialized and **never read** (`get_metrics` builds a fresh local dict). `create_metrics_report` is exported and imported but not called by any `TgData` method. `TgData.current_group` is a `GroupInfo` created with empty `title`/`username` that never gets populated. And `GroupInfo` as a type is largely bypassed — `list_groups` emits plain dicts instead. The `MessageData` model is used well; the others are half-wired.

6. **A compatibility hack in session naming.** `_init_primary_client` uses `config.username` as the Telethon session name "for compatibility with original code," falling back to `session_file`. That's a bridge to the pre-refactor world, not an intentional design choice — expect more small artifacts like it.

7. **The schema contract is implicit** (covered in §4): no shared column-name constants, no validation. It works, but it's fragile to change.

**Net:** the *shape* is a clean facade-over-layered-engines with async I/O and a DataFrame spine — a good design to build on. But the connection/pooling/rate-limit corner is mid-transition and partly contradictory, and there's dead/vestigial state to ignore or clean up. When something surprises you, assume "refactor in progress" before assuming intent.
