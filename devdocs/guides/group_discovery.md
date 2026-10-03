# Group discovery — how to use it properly

*The usage guide for `search_groups`, `similar_groups`, `linked_groups` and
`discover_groups` (tgdata 0.0.8, 2026-09-30). The README has the quick start;
this document is the part that keeps your account out of trouble and your runs
resumable. Design history and the critique that shaped it: `devdocs/scoped/10/`.*

Everything here was verified live on 2026-09-30 against a real personal account
(Telethon 1.40, Premium) unless marked otherwise.

---

## 1. What it is, and what it is not

Discovery finds rooms the account is **not** in. It reads; it never joins, never
sends, never messages anyone. Three routes, one row shape:

| Route | Telegram call behind it | What it can see | Cost per call |
|---|---|---|---|
| `search_groups(query)` | global search | room **names and @usernames** only — never post text | 1 request |
| `similar_groups(seeds)` | "similar channels" recommendations | channels whose subscribers overlap the seed's | 1 request per seed per round |
| `linked_groups(room)` | read the room's recent posts | rooms it links to (text, hyperlinks, buttons) | 1–2 requests per room, plus lookups if you resolve |
| `discover_groups(...)` | all three on one session, deduplicated by id | | the sum |

What it deliberately does **not** do: judge rooms. No language check, no
category, no "is this alive", no member-count bars. tgdata returns candidates
with the numbers Telegram hands back for free; the rules that decide which
candidates matter are yours, and belong in your code, not in the library.
Measurement (views, writers per day) is a separate, planned feature.

## 2. Before the first run

**The session must already be authorized.** `TgData(...)` opens the persistent
client with Telethon's `start()`, which *prompts on stdin* for a phone and a
code when the session is not logged in. In a background job there is nobody to
answer, and the process hangs. For unattended runs, check first with the client
that can never prompt:

```python
from tgdata import TgData, AuthRequiredError

tg = TgData("config.ini")
try:
    async with tg.connection_engine.ephemeral_client() as probe:
        me = await probe.get_me()
except AuthRequiredError:
    raise SystemExit("session not logged in — run an interactive login once, by hand")
```

**One live client per session file.** Two processes on the same `.session`
contend for its SQLite file and can hit lock errors that look like hangs. Short
overlaps work (the live tests ran beside a running loop on the same session
without incident), but do not leave two long runs sharing one session.
Discovery runs for minutes to hours; give it the session to itself when you can.

**Telethon 1.33 or newer.** The recommendations call does not exist before that;
`setup.py` requires it, so installing tgdata 0.0.8 pulls the right floor.

**Know your account's tier.** A Premium account gets far more recommendations
per seed (64 observed from one seed) than a normal one (reportedly about 10;
not observed). It changes how big round two of `similar_groups` gets — see §5.

## 3. The recommended workflow

Discovery is cheapest to most expensive: recommendations, then search, then
link mining, then username resolution. Run it in that order and stop when you
have enough.

**Step 1 — seeds from rooms you already trust.** The best seeds are rooms whose
audience you already know is right. Usernames from `list_groups()` cost nothing
to resolve (they are in the session cache).

```python
groups = await tg.list_groups()
seeds = groups[groups['IsChannel'] & groups['Username'].notna()]['Username'].head(4).tolist()
```

Keep seeds mixed by type: "similar" works through shared subscribers, so seeds of
one kind only ever find more of that kind.

**Step 2 — queries from how rooms name themselves.** Rooms in a market name
themselves "place + topic" («Анталия чат», «Аланья аренда», «Side Rent»). The
helper combines every spelling with every topic word, in both word orders,
because Telegram's search is not guaranteed to treat «Стамбул аренда» and
«Аренда Стамбул» alike. Spellings matter: a room calls itself Аланья *or*
Алания, ё and е are different letters to the search, and Latin spellings are
separate rooms.

```python
from tgdata import build_search_queries

queries = build_search_queries(
    ["Анталия", "Анталья", "Antalya", "Аланья", "Алания", "Alanya"],
    topics=["чат", "новости", "аренда", "недвижимость", "жильё", "жилье", "квартиры", "русские"],
    prefixes=["Турция", "Turkey"],
)
# 6 terms × (1 + 2 + 8 + 8) = 114 queries, deduplicated case-insensitively
```

Districts usually need only a short topic list in one order; call the helper
twice with `both_orders=False` for those rather than multiplying a long list
by thirty district names.

**Step 3 — run discovery in the background, persisting as you go.**

```python
import json, time

rows_file = open("found.jsonl", "a")
last_beat = {"t": time.time(), "phase": ""}

def on_found(row):                       # every room, as it is found
    rows_file.write(json.dumps(row, default=str, ensure_ascii=False) + "\n")
    rows_file.flush()

def on_beat(phase):                      # every sign of life
    last_beat.update(t=time.time(), phase=phase)

df = await tg.discover_groups(
    seeds=seeds,
    queries=queries,
    similar_rounds=2,
    mine_links=True,          # from the first 50 rooms found, seeds first
    resolve_links=False,      # linked names come back as text — free
    pace=2.0,
    heartbeat=on_beat,
    found_callback=on_found,
)
```

A run of 114 queries plus two rounds of recommendations takes roughly
`requests × (pace + ~0.5 s)`; budget ten to forty minutes and let it run
unattended. The callback means a crash costs nothing already written.

**Step 4 — filter with your rules, then fetch.** Every row with a `GroupID` is
already usable by `get_messages`; Telegram wrote it into the session cache with
its access hash when the result arrived (verified live: a room the account had
never seen was fetched by bare id with no dialog sync).

```python
keep = df[df['GroupID'].notna() & df['Title'].str.contains("Антал|Alanya", case=False, na=False)]
for gid in keep['GroupID'].astype(int):
    sample = await tg.get_messages(group_id=gid, limit=50)
    ...   # your language check, your activity check, your ledger
```

**Step 5 — resolve links only for what you keep.** Link mining returns names.
Resolving a name to a room is the one request Telegram punishes hardest (§4).
Resolve the handful you actually want, not everything. Two ways: rerun link
mining on the few source rooms whose links you want, with a small budget; or
fetch a chosen name directly — `get_messages` resolves it (one lookup each, so
keep it to a handful) and the row is then in the session cache for good:

```python
unresolved = df[df['GroupID'].isna()]
wanted = unresolved[unresolved['Username'].str.contains("antalya", case=False, na=False)]
for name in wanted['Username'].head(5):
    sample = await tg.get_messages(group_id=name, limit=20)   # one lookup per name

# or: resolve everything the two best sources link to, capped
resolved = await tg.linked_groups(seeds[:2], posts=100, resolve=True, max_resolve=20)
```

## 4. The rules that keep the account safe

**Pace.** `pace` seconds after every request; the default 2.0 is the pace a
production account has run at for weeks without a search block. Lower it only
on an account with headroom to lose.

**Waits are obeyed exactly, and you see them.** When Telegram answers "wait N
seconds", discovery sleeps N seconds in ten-second slices, each one a heartbeat
tick (`"flood-wait 50s"`, `"flood-wait 40s"`, …), then retries the *same*
request. It never retries early and never works around a limit. A wait longer
than `max_flood_wait` (default one hour) ends the run with `DiscoveryInterrupted`.
Two steps keep Telethon's own handling instead: reading a room's posts for
links, and the dialog sync for a numeric id — a wait of up to a minute there is
slept without ticks.

**Username resolution is the dangerous request.** Turning `@name` into a room
(`ResolveUsername`) is rate-limited far more harshly than search: the reference
account that this design was lifted from was blocked from lookups for 8 hours
one day and 21 hours the next, after a few hundred. So:

- every call has `max_resolve` (default 100), counted across the whole call;
- `discover_groups` defaults to `resolve_links=False` — mined names come back as
  text, which costs nothing;
- a wait on a lookup is **never slept through**: a seed that would wait is
  skipped with a warning, and link resolution stops at the first wait, returning
  the rest unresolved;
- names the session already knows (your own dialogs, rooms found earlier in the
  same session) resolve from the cache for free and do not count.

Watch the log line at the end of a run: `discover_groups: N rooms (K username
resolutions spent of M)`.

**Link mining is bounded.** `link_sources` (default 50) is how many rooms are
read for links, taken in discovery order — seeds first, then their
recommendations, then search hits — so the most relevant rooms are mined before
any cap cuts. A truncating cap logs a warning that names the parameter to lift.

**"Similar" rounds compound.** Round one asks about your seeds; round two asks
about everything round one returned, *as objects*, so it costs no lookups — but
it does cost one request per room. On a Premium account four seeds can mean
250+ requests in round two (about ten minutes at the default pace). Three
rounds drift off topic; the default is two for a reason.

**Nothing found is ever lost.** `DiscoveryInterrupted` carries `.found`, the
DataFrame collected up to the interruption, and `.retry_after`, the seconds
Telegram asked for (0 when the network stayed down past `max_offline`).

```python
from tgdata import DiscoveryInterrupted

try:
    df = await tg.discover_groups(seeds=seeds, queries=queries)
except DiscoveryInterrupted as e:
    df = e.found
    print(f"kept {len(df)} rooms; retry after {e.retry_after}s")
```

Do not retry inside that window: Telegram remembers the pending wait per
request type and a premature call is refused before it is even sent.

**A dropped connection is waited out.** A sleeping laptop or a changed Wi-Fi
network drops the socket; discovery waits for it to come back (beating
`"reconnecting 3min"`) up to `max_offline` (default one hour), then retries the
same request. Past that it gives up with everything found so far.

## 5. Reading the output

Every method returns a DataFrame with the same columns, in this order:

| Column | dtype | Meaning |
|---|---|---|
| `GroupID` | `Int64` (nullable) | bare Telegram id, as in `list_groups`; `NA` for an unresolved link |
| `Title` | object | room title; `None` for an unresolved link |
| `Username` | object | `@name` or `None` |
| `Identifier` | object | `@name` when it has one, else the id as text — a display key, the same as in `list_groups`. To fetch, pass `Username` or `int(GroupID)`; Telethon reads a numeric *string* as a phone number |
| `IsChannel` | `boolean` (nullable) | `True` for every channel **including megagroups**, as `list_groups` does |
| `IsMegagroup` | `boolean` (nullable) | `True` for a supergroup chat; `False` for a broadcast channel or a basic group |
| `ParticipantsCount` | `Int64` (nullable) | present on search and recommendation results; `NA` on rooms resolved from links |
| `FoundVia` | object | `search` · `similar` · `link` — the cheapest route that found the room; first discovery wins |
| `FoundBy` | object | the query, the seed (`@name` or `id:N`), or the source room |

Practical consequences:

- A "chat" in everyday terms is `IsChannel == True & IsMegagroup == True`. A
  broadcast channel is `IsChannel == True & IsMegagroup == False`. A basic
  (legacy) group is `IsChannel == False`.
- The nullable dtypes mean `df['GroupID'].astype(int)` fails while any row is
  unresolved; filter with `df['GroupID'].notna()` first. Indexing with a mask
  that contains `NA` treats `NA` as `False` in both directions (pandas 2.3
  verified), so an unresolved row is excluded by `df[df['IsMegagroup']]` *and*
  by `df[~df['IsMegagroup']]` alike; select them explicitly with `.isna()`.
- Deduplication is **per call**, by id. Across runs, keep your own ledger of
  ids and lowercased usernames and drop what you already know.
- Seeds and the rooms you mine from are never returned as finds.
- An empty result still has every column, so downstream code needs no special
  case.

## 6. Heartbeat and a watchdog

The `heartbeat` callback receives a phase label on every sign of life:
`"search"`, `"similar"`, `"links"`, `"resolve"`, `"pause"`, `"flood-wait 40s"`,
`"reconnecting 2min"`. Treat **silence** as the hang signal, not duration — a
healthy run beats at least every `pace` seconds and every ten seconds inside a
wait:

```python
import asyncio, time

last = {"t": time.time()}
task = asyncio.create_task(tg.discover_groups(seeds=seeds, queries=queries,
                                              heartbeat=lambda p: last.update(t=time.time())))
while not task.done():
    await asyncio.sleep(15)
    if time.time() - last["t"] > 120:          # two silent minutes is a hang, at any run length
        task.cancel()
        break
```

Discovery never mutates the shared client's flood setting, so it is safe to run
while real-time handlers or a poll loop use the same `TgData`; they keep their
own behaviour. Running two discoveries at once on one client only halves the
pace of each — run them one after the other.

## 7. Links: where they are and what is skipped

Channels put nearly all their links behind hyperlinked text, not in the visible
message (87 of 100 posts in one news channel carried links; none in the text
itself). The miner therefore reads three places per post: the text, the URL
behind every hyperlinked span, and URL buttons.

Accepted: `t.me/name`, `t.me/name/123` (a post link still names its room),
`t.me/s/name`, `t.me/boost/name`, `telegram.me/name`.
Skipped: invite links (`t.me/+…`, `joinchat`) — following one would mean
joining; `t.me/c/…` (private ids, not resolvable); reserved paths
(`addstickers`, `proxy`, `share`, …); bots (`…bot`, never a room); the room's
own username.

## 8. Troubleshooting

| Symptom | Cause | What to do |
|---|---|---|
| `DiscoveryInterrupted` with `retry_after > 0` | Telegram demanded a wait above `max_flood_wait`, or a wait on looking up a `linked_groups` source (lookups are never slept through) | keep `.found`, wait the full `retry_after`, rerun with the queries not yet done |
| `DiscoveryInterrupted` with `retry_after == 0` | offline longer than `max_offline` | keep `.found`, rerun when connected |
| log: `Seed @x skipped — Telegram wants Ns on username lookups` | the account is under a lookup block | do not resolve anything until it passes; seeds from `list_groups` avoid lookups entirely |
| log: `Stopped resolving links at the N-username bound` | `max_resolve` hit | intended; raise it knowingly, or resolve only what you keep |
| `similar_groups` returns nothing | a megagroup or basic-group seed, or a non-Premium account | seed with broadcast channels; expect ~10 per seed without Premium |
| `GroupAccessError` for an int seed | the account cannot see that id | use the `@username`, or a room the account is in |
| `ValueError: '@x' is not a group or channel` | the name is a user or a bot | drop it |
| the process hangs at start with no output | `start()` waiting for a login code on stdin | authorize interactively once; use the `ephemeral_client` check from §2 |
| `sqlite3.OperationalError: database is locked` | another process holds the same session file | one live client per session; wait for the other to finish |
| `ParticipantsCount` is `NA` | the row was resolved from a link | counts come with search and recommendation results only; fetch the full channel yourself if you need it |

## 9. A complete example

```python
import asyncio, json
from tgdata import TgData, DiscoveryInterrupted, build_search_queries

async def main():
    tg = TgData("config.ini")
    try:
        groups = await tg.list_groups()
        seeds = groups[groups['IsChannel'] & ~groups['IsMegagroup'].astype(bool)
                       & groups['Username'].notna()]['Username'].head(3).tolist()
        queries = build_search_queries(["Анталия", "Antalya", "Аланья", "Alanya"],
                                       topics=["чат", "аренда", "недвижимость", "новости"],
                                       prefixes=["Турция"])
        found = []
        try:
            df = await tg.discover_groups(seeds=seeds, queries=queries, similar_rounds=2,
                                          mine_links=True, resolve_links=False,
                                          heartbeat=lambda p: None,
                                          found_callback=found.append)
        except DiscoveryInterrupted as e:
            df = e.found
            print(f"interrupted; kept {len(df)}, retry after {e.retry_after}s")

        df.to_csv("candidates.csv", index=False)
        print(df['FoundVia'].value_counts())

        # your rules go here — this is the part tgdata leaves to you
        rooms = df[df['GroupID'].notna()]
        for gid in rooms['GroupID'].astype(int).head(5):
            sample = await tg.get_messages(group_id=gid, limit=30)
            print(gid, len(sample), "messages")
    finally:
        await tg.close()

asyncio.run(main())
```

## 10. What the live runs showed (2026-09-30)

- One recommendations call on a Premium account: 64 channels for one seed;
  74 for another. Every object non-`min`, with an access hash and a member count.
- A search for «Анталия»: 16–17 rooms, broadcast channels and megagroups alike,
  all with member counts.
- `discover_groups` with one seed, one query, one round and link mining from
  two rooms: 85 rooms, the callback received all 85 in order, the source-cap
  warning fired as designed.
- A room the account had never seen, fetched by bare id straight after
  discovery: one message returned, no dialog sync.
- Link resolution with `max_resolve=1` on a channel linking to three rooms: the
  name already in the session cache resolved free, one lookup was paid, the cap
  stopped the third with its warning and returned it unresolved.
- The whole set ran beside a live loop sharing the same session file, without a
  lock error — short overlaps are fine.

Non-Premium recommendation yield, and a real flood wait during discovery, have
not been observed. Both paths are covered by code reading only.
