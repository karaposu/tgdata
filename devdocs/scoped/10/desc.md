# Issue 10 — tgdata can read any room but cannot find one: group discovery as a library feature

**Status:** ✅ IMPLEMENTED AND LIVE-TESTED (2026-09-30, version 0.0.8) — all seven plan steps landed (`discovery_engine.py`, `GroupInfo.from_entity/to_dict`, `build_search_queries`, four facade methods, exports, README, `test_11_discover_groups.py`). The smoke test passed 3/3 on the @karaposu account via the flatmir-scrapeops session (16 search hits, 74 similar channels from one seed, 85 rooms from `discover_groups` with the callback in order and the source-cap warning, a `get_messages` round-trip on a discovered room). Two findings during implementation: channels put nearly all their links in hyperlink entities and buttons, not visible text (the miner now reads all three; bots are skipped); and rooms resolved from links carry no `participants_count` (documented). The resolution path was exercised separately: one paid lookup, a cached name free, the budget stop with its warning, the unresolved tail. Critique `critic.md`: REORDER, experiment passed, selected mitigations folded in. A feature, not a bug — nothing in the fetch path changes. This adds the *search* step that today lives outside the library, in a consumer script.
**Where it bites:** every consumer that has to decide *which* groups to scrape before scraping them. Today that means a separate script holding its own Telethon client, its own pacing, its own flood-wait handling and its own entity bookkeeping — duplicating what `ConnectionEngine` and `MessageEngine` already do well.
**Severity:** medium — no data loss, no wrong answers; a missing capability. Without it, tgdata is a reader whose input list must be produced by hand or by another tool.
**Relationship to other docs:** builds on `scoped/8` (the persistent connection — discovery runs hundreds of requests on one session), `scoped/3` (bounded, resumable flood-wait handling — the same discipline applies to search requests) and the 0.0.6 heartbeat (`fetch_messages(heartbeat=...)` — discovery beats the same way). `scoped/9` (heartbeat coverage gaps) is independent and stays open.

---

## Where the logic comes from

A consumer, the flatmir-growth finder (`work/tg/tg_groups_audit/find_rooms.py`, ~1,500 lines, in production since 2026-09), has run Telegram group discovery for weeks and paid for the lessons. Stripped of its business rules, its discovery core is **three Telegram calls plus bookkeeping**:

| Method | Telegram call | What it returns | Cap |
|---|---|---|---|
| **Similar channels** | `channels.GetChannelRecommendationsRequest(channel=…)` | channels whose subscribers overlap the seed's | ~10 per seed on a normal account, ~100 with Premium |
| **Keyword search** | `contacts.SearchRequest(q=…, limit=100)` | rooms whose **name or @username** matches — never post content | Telegram caps below 100 |
| **Link mining** | `iter_messages(room, limit=100)` + a `t.me/<name>` regex | rooms a room links to | one level, never recursive |

plus **dedup by Telegram id** (never by name) and a **pace** of about two seconds between requests on a personal account.

The lessons that matter, all from real blocks on a real account:

1. **Username resolution is the request Telegram punishes hardest** — 8 h 19 min on 2026-09-07, 20 h 55 min on 2026-09-08. `get_entity("@name")` always sends `ResolveUsername`; `get_input_entity("@name")` reads the session cache first and only then resolves. Round two of "similar" must reuse the `Channel` objects round one returned, never look them up again by name.
2. **Never sleep on a resolution.** A search wait of 50 minutes is worth sitting through; a resolution wait of a day is not. The finder drops the flood threshold to zero around resolution so Telethon raises instead of sleeping, and abandons the mined tail on the first wait.
3. **Obey a wait exactly, never retry early**, and make the wait *visible* — a 20-minute silent sleep looked like a hang until someone checked.
4. **Results seed the session cache.** Every room a search returns arrives with its access hash, so a later fetch by id needs no dialog sync.

## What belongs in tgdata, what stays out

| Into tgdata (generic) | Stays with the consumer (Flatmir's business) |
|---|---|
| the three discovery calls, rounds, dedup, pacing | the markdown-parsed inputs, markets, place spellings, topic words |
| flood-wait discipline and the resolution guard | language, category, district and "wide" labelling |
| a pure query-builder helper (terms × topics × prefixes) | the entry bars, the ledgers, the HTML list, the PDF, the sender |
| the `list_groups` row shape, plus how each room was found | measurement (7-day views, writers per day) — a later issue |

## The design

Four facade methods on `TgData`, one new engine beside `MessageEngine`, one pure helper in `utils`:

```python
tg = TgData("config.ini")

# Telegram's global search — matches room names and @usernames only, never post text
df = await tg.search_groups("Анталия аренда", limit=100)

# Telegram's "similar channels", N rounds out from the seeds (objects carried between rounds)
df = await tg.similar_groups(["@antalyadaa", "@sprout_antalya"], rounds=2)

# t.me links in a room's recent posts — usernames only, or resolved with the no-sleep guard
df = await tg.linked_groups(group_id, posts=100, resolve=False)

# the whole pipeline: similar → search → links, deduplicated by id, in cost order
df = await tg.discover_groups(
    seeds=[...], queries=[...], similar_rounds=2,
    mine_links=True, pace=2.0, max_flood_wait=3600, heartbeat=on_beat,
)

# a pure helper for the query combinatorics (the word lists are the caller's)
queries = build_search_queries(["Анталия", "Antalya"], topics=[...], prefixes=["Турция"], both_orders=True)
```

**Rows.** Every method returns a DataFrame in the `list_groups` shape — `GroupID`, `Title`, `Username`, `Identifier`, `IsChannel`, `IsMegagroup`, `ParticipantsCount` — plus `FoundVia` (`search` | `similar` | `link`) and `FoundBy` (the query, the seed's token, or the source room's token). `GroupID` is nullable `Int64` so an unresolved link row (username known, id not) never forces the column to float. An empty result still has every column.

**Entities kept.** `Channel` (broadcast channels and megagroups) and `Chat` (basic groups), matching `list_groups`. `ChannelForbidden` / `ChatForbidden` are skipped — nothing can be read from them.

**Dedup.** By id; when only a username is known, by lowercased `@username`. First discovery wins, so `FoundVia` records the cheapest route that found the room.

**Pacing.** `pace` seconds after every network request, default 2.0 (the proven personal-account pace; a caller with headroom lowers it).

**Flood waits.** Every raw request is sent with `flood_sleep_threshold=0` so *every* wait surfaces (Telethon would otherwise silently sleep waits under 60 s with no heartbeat). A wait of at most `max_flood_wait` seconds is slept in ten-second slices that beat (`"flood-wait Ns"`), then the same request is retried. A longer wait raises `DiscoveryInterrupted`, which carries `.found` (everything collected so far, as a DataFrame) and `.retry_after` seconds — nothing already found is lost. No exponential jitter: Telegram's number is a mandate, not a hint.

**The resolution guard.** Seeds and mined usernames are resolved through one helper: `get_input_entity` (cache first) with the client's flood threshold temporarily at zero, then the full entity by id and access hash (a `GetChannels` call, not a resolution). A `FloodWaitError` here is never slept: for a seed it skips that seed with a warning; in link mining it stops resolving and returns the remaining links unresolved. Numeric ids that the session has never met fall back to the existing dialog-sync helper from `MessageEngine`, so `GroupAccessError` keeps its meaning.

**Similar-channel rounds.** Round one resolves the seeds; every later round asks about the `Channel` objects the previous round returned, so rounds two and up cost no lookups. Default two rounds — the finder's experience is that a third drifts out of the market. A seed that is a basic group cannot be asked (the call needs a channel) and is skipped with a log line.

**Link mining.** The last `posts` messages of a room; links of the forms `t.me/<name>`, `t.me/s/<name>`, `telegram.me/<name>`, with or without a trailing `/<message id>`; usernames 5–32 characters starting with a letter; reserved paths (`joinchat`, `addstickers`, `proxy`, `c`, …) and invite links (`t.me/+…`) skipped — joining is out of scope. The room's own username is excluded.

**Heartbeat.** The same exception-safe callback as `fetch_messages`: phases `"similar"`, `"search"`, `"links"`, `"resolve"`, `"pause"`, `"flood-wait Ns"`.

## How it will be used

The finder's `collect()` and `link_mine()` (about 120 lines with their retry scaffolding) become:

```python
found = await tg.discover_groups(seeds=inputs["seeds"], queries=build_queries(inputs),
                                 similar_rounds=2, mine_links=False, pace=2.0, heartbeat=on_beat)
# … measure, label and judge as before …
mined = await tg.linked_groups(passed_ids, posts=100, resolve=True)
```

Its own client options (`connection_retries=None`, a 24-hour flood-sleep threshold) are a separate small change to `ConnectionEngine` — see *out of scope*.

## Verified facts (2026-09-30, against the repo's own `.venv`)

- Telethon **1.40.0, layer 201**: `GetChannelRecommendationsRequest(channel: Optional[InputChannel])`, `SearchRequest(q: str, limit: int)`; both `Channel` and `Chat` carry `participants_count`.
- **Raw-request results are cached**: `telethon/client/users.py` `_call` runs `self.session.process_entities(result)` on every result — search hits land in the session with their access hashes.
- **Per-call flood threshold exists**: `TelegramClient.__call__(request, ordered=False, flood_sleep_threshold=None)`; a server `FloodWaitError` above the threshold is re-raised, at or below it Telethon sleeps and retries.
- **`get_input_entity` is cache-first**: it returns `session.get_input_entity(peer)` before `_get_entity_from_string`, which is where `ResolveUsernameRequest` is sent.
- **Dependency floor**: `GetChannelRecommendationsRequest` is already present in Telethon **1.33.1 (layer 167)** — confirmed by downloading the 1.33.1 and 1.34.0 sdists and grepping the generated `tl/functions/channels.py`. `setup.py` currently allows `>=1.24`; the floor moves to `>=1.33`.
- **Live probe (2026-09-30, `devdocs/scoped/10/probe_discovery.py`, account @karaposu, Premium, via the flatmir-scrapeops session, run beside its live loop without a lock error):** one recommendations call returned **64** channels for one seed (a Premium yield; the ~10 non-Premium figure remains unobserved); a search for «Анталия» returned **17** chats, broadcast channels and megagroups alike; **81 of 81** returned objects were non-`min`, carried an access hash **and a `participants_count`**; one `Forbidden` object appeared (the skip rule is needed); and `get_messages(limit=1)` by bare id on a room the account is **not** in returned a row with **no dialog sync** — discovered rooms are usable by id exactly as this design assumes.

## Explicitly out of scope

- **Measurement** — 7-day average views, trend, writers per day, housing counts. Mostly generic, but a separate feature (`get_group_stats`) for a later issue.
- **Every Flatmir rule** — language check, categories, districts, bars, ledgers, list HTML/PDF, sending to Saved Messages.
- **Client options on `ConnectionEngine`** (`connection_retries`, `retry_delay`, `flood_sleep_threshold`, `auto_reconnect`) — needed before the finder can switch over; a small separate issue.
- **Changing `list_groups`** — it keeps its code; the new engine only adopts its row shape.
- **Joining rooms, invite links, `@mention` mining** — discovery reads, never joins.

## Known Blockers

**Planning:** none open. The four technical premises above were confirmed by probe before any step was written.

**Execution:**
- **Live smoke test on a real account.** `search_groups` and `similar_groups` send global-search and recommendation requests from the configured personal account; a burst of them can earn a flood wait on that account. The user runs the smoke test, or approves it being run, with a query count kept small. Blocks the smoke-test step only.
- **Releasing 0.0.8 to PyPI** is a GitHub release the user publishes (`.github/workflows/python-publish.yml`); no step in this plan depends on it.
