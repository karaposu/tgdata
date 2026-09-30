---
model: claude-fable-5-1
effort: max
---

# Issue 10 — group discovery in tgdata: implementation plan

Source: `devdocs/scoped/10/desc.md` (PROPOSED 2026-09-30).
Critique: `critic.md` (2026-09-30) — verdict REORDER; the experiment `probe_discovery.py` was run the same day and PASSED. The selected mitigations are folded in below, each marked **⟵ critic R1 / R2 / R3 / R5 / Low** where it lands: mining and resolution caps (R1), reconnect-and-retry with a per-room callback (R2), a mutation-free resolution guard (R3), the six step-4 specifics (R5), and the marked-id dedup key, boost links and export placement (Low).

## What is the task

Give tgdata the ability to **find** groups and channels, not only read them. Today a consumer that has to decide which rooms to scrape runs its own Telethon client, its own pacing and its own flood-wait handling (the flatmir-growth finder does exactly this, ~120 lines of collection code plus scaffolding). The generic core of that search is three Telegram calls — global name search, "similar channels" recommendations, and t.me links in a room's recent posts — plus dedup by id, a pace, and two hard-won flood rules (never re-resolve a username you already hold as an object; never sleep on a resolution). This task moves that core into tgdata as a `DiscoveryEngine` with four facade methods and one pure query helper, returning rows in the shape `list_groups` already uses, so a consumer keeps only its own business rules. Measurement, labelling and every Flatmir-specific rule stay outside.

## Huge Hard Blockers

### Planning Blockers

All of the following were **discovered during planning** and **closed by probe** before any step was written. None is open.

On 2026-09-30 the live probe (`probe_discovery.py`, account @karaposu — a Premium account — via the flatmir-scrapeops session, run beside its live loop without a lock error) also *observed* every vendor premise the critique listed: 64 recommendations for one seed, 17 search hits for «Анталия» including megagroups, 81 of 81 objects non-`min` with an access hash and a `participants_count`, one `Forbidden` object, and a non-member room fetched by bare id with no dialog sync. Nothing disqualifying. The non-Premium recommendation yield remains unobserved; no step depends on it.

- **Question:** Is `channels.GetChannelRecommendationsRequest` available in the Telethon range tgdata allows (`>=1.24,<2.0`), and from which version?
  **Why the steps can't survive it:** if the call were newer than the installed line, step 4 would need a fallback path or the feature would be gated; if the floor were wrong, `setup.py` would promise something the library cannot do.
  **Status:** `CLOSED — present in Telethon 1.33.1 (layer 167) and 1.40.0 (layer 201) (confirmed by downloading the 1.33.1 and 1.34.0 sdists and grepping the generated tl/functions/channels.py; live import in the repo's .venv on 1.40.0)`
  **Source:** discovered during planning
  **Who can close it:** closed

- **Question:** Do rooms returned by a raw search or recommendations request land in the session's entity cache, so a later `get_messages(group_id)` on them works without a dialog sync?
  **Why the steps can't survive it:** if not, every discovered id would need the dialog-sync fallback or an explicit access-hash column, changing the row shape (step 2) and the engine (step 4).
  **Status:** `CLOSED — yes: telethon/client/users.py _call runs session.process_entities(result) on every raw result (confirmed by reading the installed 1.40.0 source, lines 83 and 93)`
  **Source:** found in vendor code
  **Who can close it:** closed

- **Question:** Can the flood-sleep threshold be controlled per request, so search waits surface to a heartbeat while the persistent client's default stays untouched?
  **Why the steps can't survive it:** without it, step 4 would have to mutate the shared client's threshold around every call, which races with any concurrent fetch on the same client.
  **Status:** `CLOSED — TelegramClient.__call__(request, ordered=False, flood_sleep_threshold=None) accepts it per call; waits above the threshold are re-raised, at or below it Telethon sleeps and retries (confirmed by inspect.signature and reading _call)`
  **Source:** found in vendor code
  **Who can close it:** closed

- **Question:** Is `get_input_entity("@name")` cache-first, so the resolution guard only pays for names the session has never seen?
  **Why the steps can't survive it:** the guard in step 4 is designed around cache-first lookup; if every call resolved over the network, similar-channel rounds would need a different carry mechanism.
  **Status:** `CLOSED — get_input_entity returns session.get_input_entity(peer) before falling to _get_entity_from_string, which is where ResolveUsernameRequest is sent (confirmed by reading users.py lines 438–562)`
  **Source:** found in vendor code
  **Who can close it:** closed

### Execution Blockers

- **What must happen:** the live smoke test sends global-search and recommendation requests from a personal account; a burst can earn that account a flood wait. The user runs it, or approves it being run, with the query count kept to a handful. The probe was approved and run on 2026-09-30 against `/Users/ns/Desktop/projects/flatmir-scrapeops/scrapeOps/sessions/config.ini` (session `propertybot_scrape`, beside the live scrapeOps loop); step 6 takes the config path as an argument so it can use the same one.
  **Who:** the user
  **Blocks:** step 6 (running it; writing it is not blocked)
  **Status:** `OPEN` — the smoke test is a larger burst than the probe (about a dozen requests and three username resolutions); approve it separately.

- **What must happen:** publishing 0.0.8 to PyPI is a GitHub release the user creates; the workflow `.github/workflows/python-publish.yml` builds and uploads on `release: published`.
  **Who:** the user
  **Blocks:** no step in this plan — listed so the version bump in step 5 is not mistaken for a release
  **Status:** `OPEN`

## How this implementation moves toward desired state

Current state: `TgData` can list the account's own dialogs and read any room it can see, but has no way to find rooms it is not in. Desired state: one call returns a deduplicated table of candidate rooms found by name search, by Telegram's own recommendations, and by following links, paced and flood-safe, in the same row shape `list_groups` returns, with every discovered room already usable by `get_messages`.

The steps get there additively. The dependency floor is raised first so the new request is guaranteed to exist (1). The row shape is made reusable by giving `GroupInfo` a way to build itself from an entity and to emit the `list_groups` columns (2). The pure query combinatorics land in `utils` with no network (3). The engine is written as a new module that uses the existing persistent session, the existing dialog-sync helper and the existing heartbeat convention, adds the two flood rules as code, bounds what it will spend the way the fetch path bounds a walk, survives a dropped connection, and streams rows to a callback so a two-hour run is neither a runaway nor all-or-nothing (4). The facade, exports and version tie it into the public surface (5). A smoke test in the repo's own style exercises each method against a real account with tiny limits (6). The README tells consumers what the search can and cannot see (7). Nothing existing changes behaviour: `list_groups`, `fetch_messages` and the connection engine are untouched.

## High-Level Summary

| Step | Description | Expected Output |
|------|-------------|-----------------|
| 1 | Raise the Telethon floor to the first version that ships the recommendations request | `setup.py` requires `Telethon>=1.33,<2.0` with the reason recorded |
| 2 | Teach `GroupInfo` to build from an entity and emit the `list_groups` row | `GroupInfo.from_entity()` and `GroupInfo.to_dict()` in `models.py` |
| 3 | Pure query builder in `utils` | `build_search_queries(terms, topics, prefixes, both_orders)` returning ordered unique queries |
| 4 | The discovery engine: search, similar, links, discover; flood discipline; mutation-free resolution guard; mining and resolution caps; reconnect-and-retry; per-room callback | `tgdata/discovery_engine.py` with `DiscoveryEngine`, `DiscoveryInterrupted` and the shared `_State` |
| 5 | Facade methods carrying the cap, recovery and callback parameters; exports; version 0.0.8 | `TgData.search_groups / similar_groups / linked_groups / discover_groups`; `__init__` exports; version bumped |
| 6 | Smoke test in the repo's style, config path as an argument, empty-case, unresolved-row and cap assertions | `tgdata/smoke_tests/test_11_discover_groups.py` + README entry; run once the execution blocker clears |
| 7 | User-facing documentation | README section "Finding groups" with the name-only search caveat and the flood rules |

---

## Step 1 — Raise the Telethon floor

### Proposed changes

`setup.py` allows `Telethon>=1.24,<2.0`. The recommendations request first appears in 1.33 (verified on 1.33.1, layer 167). Raise the floor and record why beside the existing `min_id` note:

```python
install_requires=[
    # min_id is exclusive in Telethon 1.x (the off-by-one fix relies on it);
    # 2.0 is a breaking API rewrite, so cap below it. Verified on 1.40.
    # 1.33 is the first release carrying channels.GetChannelRecommendationsRequest
    # (group discovery, scoped/10) — verified against the 1.33.1 sdist.
    'Telethon>=1.33,<2.0',
    'pandas>=1.0',
],
```

`requirements.txt` stays as it is (unpinned names).

### Output

`setup.py` with the new floor and the comment. Installed 1.40.0 already satisfies it; nothing to reinstall.

### Safe in nature

True — a tighter dependency floor; the installed version and every code path are unchanged.

### Peripheral concepts

setup.py install_requires, the "verified on 1.40" convention in this repo's comments

### Hardness Lvl

1

---

## Step 2 — `GroupInfo` builds from an entity and emits the `list_groups` row

### Proposed changes

`models.GroupInfo` already has the right fields (`id`, `title`, `username`, `is_channel`, `is_megagroup`, `participants_count`) but nothing constructs it from a Telethon object or turns it into the column dict that `list_groups` writes by hand. Add both, so the engine and any future caller share one definition of the row:

```python
from telethon.tl import types as tl_types

@dataclass
class GroupInfo:
    ...  # fields unchanged

    @classmethod
    def from_entity(cls, entity) -> "GroupInfo":
        """Build from a Telethon Channel or Chat (what search, recommendations
        and dialogs hand back). IsChannel mirrors Dialog.is_channel: True for
        every Channel, megagroups included."""
        return cls(
            id=entity.id,
            title=getattr(entity, 'title', '') or '',
            username=getattr(entity, 'username', None),
            is_channel=isinstance(entity, tl_types.Channel),
            is_megagroup=bool(getattr(entity, 'megagroup', False)),
            participants_count=getattr(entity, 'participants_count', None),
        )

    def to_dict(self) -> Dict[str, Any]:
        """The list_groups row: same keys, same values."""
        handle = f"@{self.username}" if self.username else None
        return {
            'GroupID': self.id,
            'Title': self.title,
            'Username': handle,
            'Identifier': handle or str(self.id),
            'IsChannel': self.is_channel,
            'IsMegagroup': self.is_megagroup,
            'ParticipantsCount': self.participants_count,
        }
```

`list_groups` in `tgdata.py` is **not** rewritten to use this (out of scope by the desc); the parity is by construction — the keys and expressions are copied from `tgdata.py` lines 88–96.

### Output

`models.py` gains `GroupInfo.from_entity` and `GroupInfo.to_dict`; a telethon types import at the top of the module. Existing dataclass fields and `MessageData` untouched.

### Safe in nature

True — additive methods on a dataclass; no caller changes.

### Peripheral concepts

GroupInfo dataclass, the list_groups column contract (GroupID/Title/Username/Identifier/IsChannel/IsMegagroup/ParticipantsCount), Dialog.is_channel semantics

### Hardness Lvl

1

---

## Step 3 — Pure query builder in `utils`

### Proposed changes

The finder builds queries from place spellings × topic words × country prefixes, in one or both word orders, deduplicated case-insensitively with order kept. The word lists are the consumer's; the combinatorics are generic. Add to `utils.py`:

```python
def build_search_queries(terms: Iterable[str],
                         topics: Iterable[str] = (),
                         prefixes: Iterable[str] = (),
                         both_orders: bool = True) -> List[str]:
    """
    Search queries for Telegram's global search, which matches room NAMES
    and @usernames only — rooms name themselves "place + topic", so the
    queries are those combinations.

    For every term: the term alone; each prefix + term ("Турция Анталия");
    term + topic for every topic ("Анталия аренда"), and with both_orders
    also topic + term ("Аренда Анталия" — Telegram is not guaranteed to
    treat the two alike). Deduplicated case-insensitively, order kept.

    Example:
        build_search_queries(["Анталия", "Antalya"], topics=["чат", "аренда"],
                             prefixes=["Турция"])
        -> ['Анталия', 'Турция Анталия', 'Анталия чат', 'Анталия аренда',
            'чат Анталия', 'аренда Анталия', 'Antalya', 'Турция Antalya', ...]
    """
    out: List[str] = []
    for t in terms:
        t = t.strip()
        if not t:
            continue
        out.append(t)
        out += [f"{p.strip()} {t}" for p in prefixes if p.strip()]
        out += [f"{t} {w.strip()}" for w in topics if w.strip()]
        if both_orders:
            out += [f"{w.strip()} {t}" for w in topics if w.strip()]
    seen, uniq = set(), []
    for q in out:
        k = q.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(q)
    return uniq
```

This is a faithful lift of the finder's `build_queries` with the town/district split removed — a caller that wants a shorter topic list for districts calls the helper twice.

### Output

`utils.py` gains `build_search_queries`; `Iterable`/`List` added to its typing imports. No network, no state.

### Safe in nature

True — a new pure function.

### Peripheral concepts

utils module (pandas helpers live here already), `__all__` export list in `__init__` (wired in step 5)

### Hardness Lvl

1

---

## Step 4 — The discovery engine

### Proposed changes

New module `tgdata/discovery_engine.py`, the same shape as `message_engine.py`: a class holding the `ConnectionEngine`, every network call inside `async with self.connection_engine.session() as client`, DataFrames out. Components, top to bottom:

**Constants and the exception.**

```python
DEFAULT_PACE_S = 2.0            # after every network request — the proven personal-account pace
DEFAULT_MAX_FLOOD_WAIT_S = 3600 # a longer mandated wait raises DiscoveryInterrupted
DEFAULT_MAX_OFFLINE_S = 3600    # ⟵ critic R2: how long to wait for the network before giving up
DEFAULT_LINK_SOURCES = 50       # ⟵ critic R1: rooms mined for links per discover_groups call
DEFAULT_MAX_RESOLVE = 100       # ⟵ critic R1: username resolutions per call — the punished request
SEARCH_LIMIT = 100              # Telegram caps lower; ask for the most
LINK_POSTS = 100
SIMILAR_ROUNDS = 2              # a third round drifts out of the topic (finder's experience)
NET_ERRORS = (ConnectionError, OSError, asyncio.TimeoutError, asyncio.IncompleteReadError)  # ⟵ critic R2
COLUMNS = ['GroupID', 'Title', 'Username', 'Identifier', 'IsChannel', 'IsMegagroup',
           'ParticipantsCount', 'FoundVia', 'FoundBy']

# `s/` is the web preview, `boost/` names its channel in the second segment (⟵ critic Low)
TME_LINK = re.compile(
    r"(?:t\.me|telegram\.me)/(?:s/|boost/)?([A-Za-z][A-Za-z0-9_]{4,31})(?![A-Za-z0-9_])", re.I)
RESERVED_PATHS = {"joinchat", "addstickers", "addemoji", "addtheme", "share", "proxy",
                  "socks", "setlanguage", "confirmphone", "login", "invoice", "boost",
                  "giftcode", "addlist", "iv", "bg"}

class DiscoveryInterrupted(RuntimeError):
    """The run could not continue: Telegram demanded a wait longer than
    max_flood_wait, or the network stayed down past max_offline (⟵ critic R2).
    Nothing found so far is lost: .found is the DataFrame collected up to the
    interruption, .retry_after the seconds Telegram asked for (0 for a
    network give-up)."""
    def __init__(self, message: str, found: pd.DataFrame, retry_after: int):
        super().__init__(message)
        self.found, self.retry_after = found, retry_after


@dataclass
class _State:
    """Bookkeeping shared by the four operations when discover_groups chains
    them on one session (⟵ critic R5). One instance per public call."""
    seen: set                          # dedup keys: marked peer id, or '@name' while unresolved
    rows: list                         # row dicts in discovery order
    entities: dict                     # key -> entity, so link mining iterates objects, not ids
    beat: Callable[[str], None]        # the exception-safe heartbeat closure
    pace: float
    max_flood_wait: int
    max_offline: int
    max_resolve: int                   # ⟵ critic R1: resolutions allowed in this call
    resolved: int = 0                  # resolutions spent so far
    found_callback: Optional[Callable] = None   # ⟵ critic R2: per new room, sync or async
```

The link regex accepts `t.me/name`, `t.me/s/name`, `t.me/boost/name`, `telegram.me/name`, with or without a trailing `/<message id>` (the finder's regex rejected message deep links — a real gap, since channels link to specific posts constantly). Usernames are 5–32 characters starting with a letter; `t.me/+invite` and `t.me/c/…` never match; reserved paths are filtered after matching. The room's own username is excluded by the caller.

**Two internal helpers carry the flood rules.**

```python
async def _request(self, client, request, st: _State, phase: str):
    """One raw request with EVERY wait surfaced (per-call threshold 0, so
    Telethon never sleeps silently): a FloodWait within max_flood_wait is
    waited out in beating slices, then the SAME request is retried; a
    longer one raises DiscoveryInterrupted with everything found so far.
    A transport failure (⟵ critic R2) waits for the network to come back,
    beating, then retries the same request — every request here is
    idempotent — and gives up past max_offline the same way."""
    while True:
        try:
            st.beat(phase)
            return await client(request, flood_sleep_threshold=0)
        except FloodWaitError as e:
            if e.seconds > st.max_flood_wait:
                raise DiscoveryInterrupted(
                    f"Telegram wants a {e.seconds}s wait on {type(request).__name__} "
                    f"(max_flood_wait={st.max_flood_wait}); {len(st.rows)} rooms found so far",
                    self._frame(st.rows), e.seconds) from e
            logger.warning(f"FloodWait {e.seconds}s on {type(request).__name__} — waiting, then retrying")
            await self._sleep_beating(e.seconds, st.beat, "flood-wait")
        except NET_ERRORS as e:
            logger.warning(f"connection lost during {type(request).__name__} ({type(e).__name__}) — "
                           f"waiting for the network")
            await self._wait_for_network(client, st)     # raises DiscoveryInterrupted past max_offline

async def _wait_for_network(self, client, st: _State):
    """The finder's wait_for_network (the fix that ended its 487-room loss):
    every 30 s reconnect if needed and ask get_me(); beat 'reconnecting <n>min'
    so a watchdog sees life; past max_offline raise DiscoveryInterrupted with
    .found and retry_after=0. Mirrors ConnectionEngine._ensure_connected but
    keeps trying instead of raising ConnectionError on the first failure."""
    waited = 0
    while True:
        try:
            if not client.is_connected():
                await client.connect()
            await client.get_me()
            logger.info(f"connection is back after {waited // 60} min — continuing")
            return
        except Exception:  # noqa: BLE001 — still down
            if waited >= st.max_offline:
                raise DiscoveryInterrupted(
                    f"no connection to Telegram for {waited // 60} min (max_offline={st.max_offline}); "
                    f"{len(st.rows)} rooms found so far", self._frame(st.rows), 0)
            st.beat(f"reconnecting {waited // 60}min")
            await asyncio.sleep(30)
            waited += 30

async def _resolve(self, client, ref, st: _State):
    """A seed or a mined name → a full entity, WITHOUT ever sleeping on
    ResolveUsername (the request Telegram punishes hardest: 8 h and 21 h
    blocks on the finder's account) and WITHOUT touching the shared client's
    flood_sleep_threshold (⟵ critic R3: a real-time handler or a concurrent
    fetch on the same client keeps its own sleeping behaviour).

    Entities pass through untouched — round two of similar_groups hands back
    the objects round one returned. Otherwise: the session cache first (pure,
    no network); on a miss, a STRING sends ResolveUsername through the
    per-call path with threshold 0 — never through _request — so a
    FloodWaitError propagates unslept for the caller to skip or stop on, and
    counts against st.max_resolve (callers check the budget before calling);
    an INT uses the message engine's dialog-sync fallback, so GroupAccessError
    keeps its meaning. A cached peer becomes the full object by id + access
    hash (GetChannels / GetChats via _request), which beats and carries none
    of the resolution risk."""
    if isinstance(ref, (tl_types.Channel, tl_types.Chat)):
        return ref
    st.beat("resolve")
    try:
        peer = client.session.get_input_entity(ref)          # cache only; ValueError = never seen
    except ValueError:
        if isinstance(ref, int):
            # called across engines on purpose until the shared resolver of the
            # follow-up issue exists (critic R3, long-term)
            return await MessageEngine._entity_after_dialog_sync(client, ref, st.beat)
        name = str(ref).lstrip('@')
        st.resolved += 1
        r = await client(functions.contacts.ResolveUsernameRequest(username=name),
                         flood_sleep_threshold=0)             # NOT _request: a wait here is never slept
        ent = next((c for c in r.chats if isinstance(c, (tl_types.Channel, tl_types.Chat))), None)
        if ent is None:
            raise ValueError(f"{ref!r} is not a group or channel")
        return ent
    if isinstance(peer, tl_types.InputPeerChannel):
        r = await self._request(client, functions.channels.GetChannelsRequest(
            id=[utils.get_input_channel(peer)]), st, "resolve")
    else:
        r = await self._request(client, functions.messages.GetChatsRequest(id=[peer.chat_id]), st, "resolve")
    return r.chats[0]
```

`_sleep_beating(seconds, beat, phase)` is the ten-second sliced sleep already used twice in `message_engine.py`, with the label carrying the remaining seconds. `_beat` is the same exception-safe closure as `fetch_messages`. `_frame(rows)` (⟵ critic R5) always builds on the fixed columns — `pd.DataFrame(rows, columns=COLUMNS)`, so an empty result still has every column — then casts `GroupID` to nullable `Int64` and `IsChannel`/`IsMegagroup` to nullable `boolean`, so a frame that mixes resolved and unresolved link rows keeps one dtype per column. `iter_messages` in link mining cannot take a per-call threshold; it keeps Telethon's default (a silent sleep of at most 60 s, rare) and the docstring says so.

**Row and dedup.**

```python
async def _add(self, st: _State, entity, via: str, by: str) -> bool:
    """Append a row for a Channel/Chat whose key is new; first discovery wins,
    so FoundVia records the cheapest route. Forbidden objects and anything
    else are skipped — the probe saw one Forbidden among 82 results."""
    if not isinstance(entity, (tl_types.Channel, tl_types.Chat)):
        return False
    key = self._key(entity)
    if key in st.seen:
        return False
    st.seen.add(key)
    st.entities[key] = entity
    row = GroupInfo.from_entity(entity).to_dict()
    row.update({'FoundVia': via, 'FoundBy': by})
    st.rows.append(row)
    await self._notify(st, row)          # ⟵ critic R2: found_callback(row), sync or async; errors propagate
    return True

@staticmethod
def _key(e) -> str:
    """Dedup key: Telethon's MARKED peer id (utils.get_peer_id — a basic group
    and a channel can never collide, ⟵ critic Low) for an entity, else the
    lowercased @username. GroupID in the row stays the bare id, as in list_groups."""
    return str(utils.get_peer_id(e)) if hasattr(e, 'id') else f"@{str(e).lstrip('@').lower()}"

@staticmethod
def _unresolved_row(username: str, by: str) -> dict:
    """A link whose name was not resolved (⟵ critic R5): GroupID, IsChannel,
    IsMegagroup, ParticipantsCount = pd.NA; Username and Identifier = '@name';
    Title = None; FoundVia = 'link'."""
    return {'GroupID': pd.NA, 'Title': None, 'Username': f"@{username}", 'Identifier': f"@{username}",
            'IsChannel': pd.NA, 'IsMegagroup': pd.NA, 'ParticipantsCount': pd.NA,
            'FoundVia': 'link', 'FoundBy': by}
```

One `_State` per public call travels through every operation (⟵ critic R5); `discover_groups` builds it once and hands the same instance to all three. Seeds are added to `st.seen` (and `st.entities`) as they resolve, so a seed recommended by another seed never comes back as a find. `found_callback` fires from `_add` for every new row, resolved or not, in discovery order; like `batch_callback` in `fetch_messages`, an exception in it propagates and ends the run.

**The four operations** (⟵ critic R5: signatures fixed here). Each is an internal coroutine on one session; the public methods build a `_State`, open `session()`, call one operation, and return `_frame(st.rows)`. `discover_groups` calls all three on the same `_State`.

```python
async def _search(self, client, st, query: str, limit: int) -> None
async def _similar(self, client, st, seeds: list, rounds: int) -> None
async def _links(self, client, st, sources: list, posts: int, resolve: bool) -> None
```

*`_search`:* `r = await self._request(client, functions.contacts.SearchRequest(q=query, limit=limit), st, "search")`; `for c in r.chats: await self._add(st, c, 'search', query)`; then the pace sleep (`st.beat("pause")` first). `r.users` is ignored.

*`_similar`:* round 1 resolves each seed through `_resolve` — a string seed is skipped with a warning when `st.resolved >= st.max_resolve`; a `FloodWaitError` skips that seed with a warning; a `ValueError`/`GroupAccessError` logs and skips; an entity that is not a `Channel` is skipped with a log line (the call needs a channel; a basic group cannot be asked). Every resolved seed goes into `st.seen`/`st.entities` without a row. For each entity in the layer: `r = await self._request(client, functions.channels.GetChannelRecommendationsRequest(channel=ent), st, "similar")` — `r` is `messages.Chats` or `messages.ChatsSlice`, both expose `.chats`; each new one (`_add` returned True) joins `next_layer` **as an object**; rounds 2..N iterate `next_layer` with no resolution at all. `FoundBy` is the seed's token (`@name` when it has one, else `id:N`).

*`_links`:* `sources` is a list of entities (from `st.entities` in `discover_groups`, or resolved from the caller's refs in `linked_groups`). Per source, `_mine_room(client, ent, posts, st)` runs `async for m in client.iter_messages(ent, limit=posts)` inside the same retry shape as `_request`: on `NET_ERRORS`, `_wait_for_network` then restart that room; on a `FloodWaitError` within `max_flood_wait`, sleep beating then restart that room; beyond it, `DiscoveryInterrupted`. **Where the links are** (found during implementation, 2026-09-30): channels put nearly all their links behind hyperlinked text — `MessageEntityTextUrl.url` — and some in URL buttons (`reply_markup` rows, `KeyboardButtonUrl.url`); the visible `m.message` held none in 200 posts of two news channels. `_mine_room` therefore scans the visible text, every entity URL and every button URL. Collected `TME_LINK` matches are lowercase-deduplicated, minus reserved paths, minus usernames ending in `bot` (never a room; would waste a resolution), minus the room's own username, minus anything already in `st.seen`. With `resolve=False` every new name becomes `_unresolved_row(name, source_token)`, keyed `@name`. With `resolve=True` each name goes through `_resolve` while `st.resolved < st.max_resolve`; the cap, or the first `FloodWaitError`, stops resolution with one WARNING in the voice of the 750-message warning ("stopped resolving at the N-username bound; M links returned unresolved — pass max_resolve=… to resolve more") and the rest are returned unresolved. This is the finder's "abandon the mined tail" rule as a return value instead of a lost list (⟵ critic R1).

*`discover_groups`:* on one session, in cost order — `_similar` (rounds), then `_search` per query, then, if `mine_links`, `_links` over the first `link_sources` entities of `st.entities` in discovery order (similar first, so the seeds' neighbourhood is mined before search noise) with `resolve=resolve_links`, **default False** (⟵ critic R1: usernames come back as text; the caller resolves the ones it keeps, or opts in knowingly). When the source cap truncates, one WARNING in the same voice ("mined links from the first 50 of 312 rooms; pass link_sources=… to mine more"). `st.max_resolve` is shared across the whole call, seeds included. A `DiscoveryInterrupted` raised inside carries the partial frame; nothing is caught and swallowed.

**Per-item exceptions** (⟵ critic R5) — swallowed with a log line: `FloodWaitError` on a seed or a mined name (skip / stop resolving), `ValueError` on an unknown or non-group name, `TypeError` on a basic-group seed, `GroupAccessError` on an int seed the account cannot see. Propagate: `DiscoveryInterrupted`, any exception from `found_callback`, and everything else.

**Logging** mirrors the message engine: one INFO line per phase with counts, WARNING on every flood wait and every skipped seed.

### Output

`tgdata/discovery_engine.py` (~400 lines) exporting `DiscoveryEngine` and `DiscoveryInterrupted`, with the private `_State`. Importable on its own; no change to any existing module (it imports `ConnectionEngine`, `MessageEngine._entity_after_dialog_sync` — a private cross-engine call accepted with a comment until the shared resolver of the follow-up issue exists — `GroupInfo`, and `telethon.utils`).

### Safe in nature

True — a new module nothing existing imports yet. It never mutates the shared client's state (⟵ critic R3): every wait it controls goes through a per-call threshold, and resolution reads the session cache directly.

### Peripheral concepts

ConnectionEngine.session() persistent client, MessageEngine._entity_after_dialog_sync and GroupAccessError, the heartbeat closure and sliced-sleep convention, the DEFAULT_FETCH_LIMIT warning convention, the batch_callback streaming convention, GroupInfo row contract, Telethon session entity cache (session.get_input_entity, process_entities), per-call flood_sleep_threshold, ResolveUsername vs GetChannels cost, utils.get_peer_id marked ids, NET_ERRORS transport failures

### Hardness Lvl

4

---

## Step 5 — Facade methods, exports, version 0.0.8

### Proposed changes

`tgdata.py`: construct the engine in `__init__` beside the message engine, and add a **Group Discovery** section with four thin delegating coroutines whose docstrings carry the caveats a caller must know:

```python
self.discovery_engine = DiscoveryEngine(connection_engine=self.connection_engine)

# ==================== Group Discovery ====================

async def search_groups(self, query: str, limit: int = 100, pace: float = 2.0,
                        max_flood_wait: int = 3600, max_offline: int = 3600,
                        heartbeat: Optional[Callable] = None,
                        found_callback: Optional[Callable] = None) -> pd.DataFrame:
    """
    Telegram's global search for groups and channels.

    Matches room NAMES and @usernames only — never post content. A room
    about your topic under an unrelated name is invisible to every query;
    use similar_groups and linked_groups to reach those.

    Returns the list_groups columns plus FoundVia ('search') and FoundBy
    (the query). Rows returned here are already in the session cache, so
    get_messages(row['GroupID']) works without a dialog sync.
    """

async def similar_groups(self, seeds, rounds: int = 2, max_resolve: int = 100, ...common...)
async def linked_groups(self, group_id, posts: int = 100, resolve: bool = False,
                        max_resolve: int = 100, ...common...)
async def discover_groups(self, seeds=(), queries=(), similar_rounds: int = 2,
                          mine_links: bool = False, link_posts: int = 100,
                          link_sources: int = 50,          # ⟵ critic R1
                          resolve_links: bool = False,     # ⟵ critic R1: opt in knowingly
                          max_resolve: int = 100,          # ⟵ critic R1: seeds + links, whole call
                          ...common...) -> pd.DataFrame
# ...common... = pace: float = 2.0, max_flood_wait: int = 3600, max_offline: int = 3600,
#                heartbeat: Optional[Callable] = None, found_callback: Optional[Callable] = None
```

`seeds` accepts one value or a list of `@username`, `username`, numeric id, or entity. `group_id` for `linked_groups` accepts the same, plus a list, so a caller can mine the rooms a previous call found. Every docstring states the four rules a caller must know: name-only search; the resolution budget and why (`max_resolve`, `resolve_links=False`); what `DiscoveryInterrupted.found` holds; that `found_callback` receives each row as it is found and that an exception in it ends the run.

`__init__.py`: export `DiscoveryInterrupted` (from the engine) and `build_search_queries` (from utils) in the **main** import block and `__all__`, and fold the trailing post-`__all__` import of `AuthRequiredError` up into that block while there (⟵ critic Low); bump `__version__ = "0.0.8"`. `setup.py` reads the version from there, so nothing else changes.

### Output

Four public coroutines on `TgData`; `tgdata.DiscoveryInterrupted` and `tgdata.build_search_queries` importable; version 0.0.8.

### Safe in nature

True — additive methods and exports; `__init__` gains one engine attribute; no existing signature changes.

### Peripheral concepts

TgData facade and its section comments, `__all__` in `__init__`, single-source version in setup.py, `heartbeat` parameter convention shared with get_messages

### Hardness Lvl

2

---

## Step 6 — Smoke test

### Proposed changes

`tgdata/smoke_tests/test_11_discover_groups.py`, in the repo's style (run with `python -m tgdata.smoke_tests.test_11_discover_groups [config.ini]`, prints ✓/✗, exit code). The optional config path argument defaults to `config.ini` and lets the run use the flatmir-scrapeops config the probe was approved for. The banner states the cost up front: about a dozen requests and **three username resolutions** (the punished request) — do not scale it up. The request count is deliberately tiny:

1. **query builder (no network):** `build_search_queries(["Анталия", "Antalya"], topics=["чат", "аренда"], prefixes=["Турция"])` → 12 unique queries, first is `'Анталия'`, contains both `'Анталия аренда'` and `'аренда Анталия'`, none duplicated case-insensitively; `both_orders=False` → 8.
2. **empty frame (no network, ⟵ critic R5):** `DiscoveryEngine._frame([])` has every `COLUMNS` entry and zero rows, with `GroupID` dtype `Int64` and `IsChannel` dtype `boolean`; `_frame([_unresolved_row("abcde", "id:1")])` keeps those dtypes with `pd.NA` in them.
3. **search_groups:** one query (`"Анталия"`, `limit=20`, `pace=1.0`); assert every `COLUMNS` entry present, `FoundVia == 'search'`, `FoundBy == 'Анталия'`, ids unique. Print the head. Then one nonsense query (`"zzqqxx_no_such_room_123"`) returns zero rows with every column present.
4. **similar_groups:** seed = the first row of `list_groups()` that is a broadcast channel with a username; `rounds=1`; assert the shape and that the seed's own id is **not** among the rows; a megagroup seed may legitimately return zero rows (the probe's Premium account got 64 from a broadcast seed).
5. **linked_groups:** the same seed, `posts=50`, `resolve=False`; assert every row has `Username` and `GroupID` is `NA`, dtype still `Int64`; then `resolve=True, max_resolve=3` on the whole list and assert at most 3 rows gained ids and the cap warning was logged (a `logging` handler attached to `tgdata.discovery_engine` collects WARNING records).
6. **discover_groups:** `seeds=[seed]`, `queries=["Анталия чат"]`, `similar_rounds=1`, `mine_links=True`, `link_sources=2`, `resolve_links=False`; assert `df['GroupID'].dropna().is_unique`, `FoundVia` ⊆ {`similar`, `search`, `link`}, and the source-cap warning was logged if more than two rooms were found.
7. **found_callback (⟵ critic R2):** a list-appending callback passed to item 6; assert `len(received) == len(df)` and that the rows arrived in the frame's order.
8. **round-trip:** `get_messages(group_id=int(df.iloc[0]['GroupID']), limit=3)` on the first discovered room — proves the cache side-effect the design relies on (no `GroupAccessError`, no dialog sync in the log), as the probe already did once.
9. **heartbeat:** a collector list passed as `heartbeat` to item 6; assert it received at least one `"search"`, one `"similar"` and one `"pause"` phase.

Reconnect-and-retry (`_wait_for_network`) cannot be exercised without cutting the network; it is covered by reading, and the smoke test's banner says so.

Add the file to `tgdata/smoke_tests/README.md` under a new "8. test_11_discover_groups.py" entry.

**Execution blocker:** running it sends live requests from the user's account — see Huge Hard Blockers. The file is written regardless; running waits for the user.

### Output

`tgdata/smoke_tests/test_11_discover_groups.py`; README entry. After the user's go-ahead: a run with all checks ✓, or a concrete failure to fix.

### Safe in nature

True — a new script; read-only against Telegram (search, recommendations, reading posts; never join, never send).

### Peripheral concepts

smoke_tests conventions (sys.path insert, ✓/✗ printing, exit codes), list_groups as the seed source, get_messages round-trip, GroupAccessError

### Hardness Lvl

2

---

## Step 7 — Documentation

### Proposed changes

`README.md`: a **Finding groups** section after "List All Group Chats", carrying the facts a consumer must know before relying on it:

- the four calls with one-line examples and the `build_search_queries` helper;
- **the name-only rule** in bold: Telegram's search matches names and @usernames, never post text — a perfect room under an unrelated name needs `similar_groups` or `linked_groups`;
- the column table (`list_groups` columns + `FoundVia` + `FoundBy`; `GroupID` nullable for unresolved links; `ParticipantsCount` present on search and recommendation results — 81 of 81 in the probe — but `NA` on rooms resolved from links, since the resolution reply does not carry it, observed live 2026-09-30);
- pacing and flood behaviour: `pace` default 2 s on a personal account; waits up to `max_flood_wait` are obeyed exactly with heartbeat ticks; longer ones raise `DiscoveryInterrupted` with `.found`; a dropped connection is waited out up to `max_offline` and the same request retried (⟵ critic R2);
- **the budget** (⟵ critic R1): `discover_groups` mines links from the first `link_sources` rooms (default 50) and resolves at most `max_resolve` usernames per call (default 100), warning when a cap truncates — and why: resolving a name is the request Telegram punishes hardest (the finder's account lost 8 and 21 hours to it); `resolve_links` is off by default and `resolve=False` costs nothing;
- `found_callback`: each room as it is found, so a long run can be persisted incrementally, like `batch_callback` on `get_messages`;
- "similar": two rounds by default; a basic-group seed cannot be asked; yield depends on the account — the probe's Premium account got 64 recommendations from one seed, a non-Premium account reportedly gets about 10 (unverified);
- link forms accepted (`t.me/name`, `t.me/name/123`, `t.me/s/name`, `t.me/boost/name`, `telegram.me/name`) and skipped (`t.me/+invite`, `t.me/c/…`, reserved paths);
- discovered rooms are already usable by `get_messages`, confirmed live on 2026-09-30.

Add "Group discovery (search, similar channels, link mining)" to the Features list. Refresh the `smoke_tests/README.md` entry from step 6.

### Output

README with the new section and feature bullet.

### Safe in nature

True — documentation only.

### Peripheral concepts

README structure (Quick Start → Advanced Usage), Features list, smoke_tests README

### Hardness Lvl

1
