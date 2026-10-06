# tgdata

A production-grade Python library for extracting and processing Telegram group and channel messages. Designed for ETL pipelines, data analysis, and archival purposes.

> **New in 0.0.8 — group discovery.** tgdata can now *find* groups and channels, not only read
> them: Telegram's name search, its "similar channels" recommendations, and links mined from
> posts, on the same persistent session, paced, flood-safe and budgeted. Four calls —
> `search_groups`, `similar_groups`, `linked_groups`, `discover_groups` — return candidate rooms
> in the `list_groups` row shape, already usable by `get_messages`. Quick start below under
> [Group discovery](#group-discovery--finding-groups-you-are-not-in); the full guide to using it
> properly is [`devdocs/guides/group_discovery.md`](devdocs/guides/group_discovery.md).

## Features

- 🚀 **Production-Ready**: Built for reliability and scale in ETL pipelines
- 🆔 **Flexible Identification**: Use numeric IDs or usernames (@channelname) for all operations
- 📊 **Efficient Data Extraction**: Fetch messages with automatic rate limit handling
- 🔄 **Incremental Updates**: Fetch only new messages with `after_id` parameter
- 📈 **Progress Tracking**: Monitor long-running operations with real-time progress
- 🔌 **Clean Architecture**: Focused on data extraction with minimal dependencies
- 🛡️ **Robust Error Handling**: Automatic retries with exponential backoff
- 📁 **Multiple Export Formats**: Export to CSV, JSON, or integrate with your data pipeline
- 🔔 **Real-time Updates**: Listen for new messages with event handlers
- ⏱️ **Polling Support**: Poll for new messages at configurable intervals
- 🎯 **Batch Processing**: Handle large groups with configurable batch sizes and delays
- 🖼️ **Media Detection & Download**: Flag photos/videos per message (no download needed) and pull the files on demand or during the fetch
- 🔎 **Group Discovery**: Find rooms you are not in — Telegram's name search, its "similar channels", and links mined from posts — paced, flood-safe, budgeted
- 🛡️ **Proxy Support**: An optional per-account SOCKS5/SOCKS4/HTTP proxy for every connection, with `require_proxy` and no silent fallback to a direct line
- 🪪 **Fixed Device Identity**: Optionally pin the device model, system and app version an account presents, so it looks the same from every machine and after Telethon upgrades
- 🩺 **Account Health Events**: Every wait, logout, ban, restriction or lost group is reported as a plain-data event — through one callback, a log line and a per-account summary — and "ok" when it ends
- **Per-account read budgets**: An optional shared SQLite ledger limits message pulls over a rolling 24 hours, with persistent warm-up steps and recoverable partial results
- **Versioned message batches**: Read bounded raw snapshots with canonical JSON, replayable batch IDs, safe continuation cursors and optional content-addressed media
- **Durable daily continuation**: Keep per-group progress and pending batches in a pluggable store, replay after restart, and advance only after explicit acknowledgment

## Installation

```bash
pip install tgdata
```


## Authentication

tgdata supports 1 authentication at the moment. 

(2 other are being implemented)

1. get telegram development credentials in telegram API Development Tools from [https://my.telegram.org/apps](https://my.telegram.org/apps)

2. Create a `config.ini` file with your Telegram API credentials like this:

```ini
[Telegram]

# you can get telegram development credentials in telegram API Development Tools
api_id = 1234566
api_hash = a24adjfakjdfakjshdflkajsbdflk
phone = +905064004949 # use full phone number including + and country code

# Where the Telethon session lives (".session" is appended automatically).
# Use an ABSOLUTE path — a bare name creates the file in whatever directory
# the process happens to run from. Do not quote values: INI values are raw
# text, so quotes become part of the value (tgdata strips them defensively
# since 0.0.4, but don't rely on it).
session_file = /absolute/path/to/my_session
```

**Session naming precedence** (since 0.0.4): an explicit `session_file`
always wins. A legacy `username` key is used as the session name only when
no `session_file` is set — configs that relied on username-named sessions
keep working, but new configs should set `session_file` and omit `username`
(it plays no part in authentication).

### Logging in

The first run of a new session, started by hand in a terminal, asks for the
code Telegram sends you. After that, tgdata never asks Telegram for a login
code on its own: before connecting it checks with Telegram whether the session
is logged in, and if it is not, it raises `AuthRequiredError` instead of
prompting.

- `.reason` is Telegram's own name for the problem — `AUTH_KEY_UNREGISTERED`
  or `SESSION_REVOKED` when Telegram logged the account out,
  `USER_DEACTIVATED_BAN` when it is banned. `.banned` is true when logging in
  again cannot help.
- To log back in after Telegram logged the account out, run once by hand in a
  terminal with `TgData("config.ini", interactive_login=True)`.
  `interactive_login=False` forbids even the first-run prompt.
- A background job should stop and alert someone on `AuthRequiredError`.
  Retrying cannot log it back in — and, unlike before, it no longer sends the
  owner a fresh login code on every retry.

### Keeping sessions out of files

Pass a store once to keep each account's session in your application's storage:

```python
import sqlite3
from tgdata import TgData

class SessionStore:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        with self.db:
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS sessions "
                "(name TEXT PRIMARY KEY, data TEXT NOT NULL)"
            )

    def load(self, name):
        row = self.db.execute(
            "SELECT data FROM sessions WHERE name = ?", (name,)
        ).fetchone()
        return row[0] if row else None

    def save(self, name, data):
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO sessions (name, data) VALUES (?, ?)",
                (name, data),
            )

    def delete(self, name):            # optional; used on Telegram log-out
        with self.db:
            self.db.execute("DELETE FROM sessions WHERE name = ?", (name,))

store = SessionStore("accounts.sqlite3")
tg = TgData("config.ini", session_store=store)
# Use tg as usual. When finished, await tg.close(), then store.db.close().
```

This example keeps sessions in a small SQLite table across restarts. Supply
your own store to use another database or storage service. The methods are
synchronous, not `async def`, and run on the
event loop: keep them quick, for example with a local database or an in-memory
cache that writes behind. tgdata ships no storage backend.

- **Names:** `session_file` is the store key, used as configured; no `.session`
  suffix is added. The existing fallback to `username`, then `telegram_session`,
  still applies. Persistent and short-lived clients share that name; pool
  connections use `<name>_1`, `<name>_2`, and so on.
- **Contents:** one opaque, versioned string containing the login key, data
  centre, update states, groups and channels with their access hashes, and the
  account's own identity rows. Message senders are excluded from this session
  cache. The temporary key and sent-file cache are not persisted.
- **Keep the string as text.** It is not Telethon's `StringSession` format or a
  JSON document for the store to interpret. Its encoding is not encryption;
  access control and any encryption belong to your store.
- **Save points:** whenever Telethon saves (connect, data-centre changes, new
  login keys, and periodically while connected), plus disconnect/`close()`.
  Unchanged state causes no write. Always close the client when finished.
- **Failures:** a store load error or unreadable saved string raises before a
  connection opens. A failed save is logged at ERROR and retried at the next
  save point; failed deletes are logged too. Save/delete logs contain the
  session name and error type, never the error text or traceback, which could
  contain the login key.
- **Two clients:** with the same login, the later save wins for the cache.
  Before a changed save or deletion, a client re-reads the stored key. If it
  changed or was removed, the client skips the mutation and warns once. Logging
  out an older client therefore preserves a newer login saved by another client.
  This check and save are separate operations, not an atomic guarantee across
  processes. Telethon's session copies for side connections stay in memory and
  never write to the store.
- **Login rules stay the same:** `None` from `load` means a new session; an
  existing session that Telegram logged out still raises `AuthRequiredError`.
  If `delete` is provided, Telegram log-out removes the stored record only when
  it still holds the login that client last loaded or saved.

Without `session_store`, existing `.session` files work exactly as before.
There is no automatic migration from files to a store. This option is designed
and tested against Telethon 1.45.0.

### Connecting through a proxy (optional)

With no `proxy` key, tgdata connects directly, exactly as before. Add one, and
**every** connection to Telegram goes through it — the persistent client, each
pool connection, and every short lookup. All of them are built by one function
in the connection engine, so there is no second way in.

```ini
[Telegram]
api_id = 1234566
api_hash = a24adjfakjdfakjshdflkajsbdflk
session_file = /absolute/path/to/my_session
proxy = socks5://user:password@203.0.113.7:1080
require_proxy = true
```

- **Forms:** `socks5://host:port`, `socks5://user:pass@host:port`,
  `socks4://…`, `http://…` (an HTTP CONNECT proxy). Percent-encode special
  characters in the user name or password (`@` as `%40`, `:` as `%3A`).
- **`require_proxy = true`** refuses to connect when no proxy is configured.
  Use it on accounts that must never touch Telegram from the machine's own
  IP.
- **No fallback, ever.** A malformed URL, a missing proxy library, or
  `require_proxy` without a proxy raises `tgdata.ProxyConfigError` before any
  connection opens. A proxy that is down or refuses the tunnel makes the
  connection fail with `ConnectionError`. Nothing retries without the proxy.
- **Install the extra:** `pip install 'tgdata[proxy]'`, which pulls in
  `python-socks[asyncio]`.
- **Logs and health checks show the proxy masked**
  (`socks5://user:***@203.0.113.7:1080`); the password never appears in a
  log line or a repr. The engine logs once whether connections are direct or
  via a proxy.
- **Not supported:** MTProto proxies (`tg://proxy?…`, `t.me/proxy?…`); they
  are refused with a clear error.
- One `proxy` per config file, and the account pool has one config per
  account, so each account gets its own proxy.
- An existing session keeps working through a proxy; a session file is not
  tied to an IP.

### A fixed device identity (optional)

Every connection tells Telegram what device it is running on — a device
model, a system version, an app version and language codes. Telegram shows
them in the account's active-sessions list. Unless you pin them, Telethon
derives them from the machine and from its own version, so the same account
presents a different device on another machine, after an OS update, and after
every Telethon upgrade. On a Mac today that is `arm64`, `25.6.0`, `1.40.0`.

Pin them in the account's config, and every connection presents exactly
that, from any machine:

```ini
[Telegram]
device_model = PC 64bit
system_version = Windows 11
app_version = 4.16.8 x64
lang_code = en
system_lang_code = en
```

- **All five keys are optional.** No keys means Telethon's defaults, exactly
  as before; a key you leave out keeps its default. `lang_code` alone also
  sets `system_lang_code`. Values may contain spaces; quotes and an inline
  `; comment` are stripped.
- **You can add it later.** The identity is sent on every connection, not
  only at login, so an existing session picks it up on its next connection —
  no new login.
- **To keep what an account shows today**, pin its current values instead of
  inventing new ones (switching identity is itself a visible change). Run
  this on the machine the account normally runs on and paste the output into
  its config:

```python
print(TgData("config.ini").device_identity()['config_lines'])
```

  `device_identity()` needs no network and no session; it also returns the
  presented values and which ones are pinned. `health_check()` reports the
  presented identity too.
- Whether Telegram cares about a changing identity has not been measured;
  pinning is a precaution for accounts that move between machines.


## Per-account read budgets

Pass a `ReadBudget` to limit explicit message pulls across jobs for the same
Telegram account. Every persistent, pooled and short-lived client built by
that `TgData` uses it. Without `read_budget`, existing behavior is unchanged.

```python
import asyncio
from tgdata import TgData, ReadBudget, ReadBudgetExceeded

async def main():
    budget = ReadBudget("/absolute/path/read-budgets.sqlite3")
    tg = TgData("config.ini", read_budget=budget)
    try:
        # Policy setup: get the authenticated account ID using metadata only.
        client = await tg.connection_engine.get_client()
        me = await client.get_me()
        budget.configure(
            account_id=me.id,
            daily_limit=2000,
            warmup=[(0, 100), (2, 300), (7, 2000)],
        )

        try:
            messages = await tg.get_messages("@channelname", limit=2000)
        except ReadBudgetExceeded as error:
            messages = error.partial_result
            print(error.status.to_dict())
            print("Retry after seconds:", error.retry_after)

        if messages is not None:
            print(messages)
        print((await tg.get_read_budget()).to_dict())
    finally:
        await tg.close()

asyncio.run(main())
```

The numbers above illustrate configuration; they are **not Telegram-safe rate
recommendations**. Warm-up days are completed 24-hour periods since enrollment,
not calendar days. The example starts at 100, rises to 300 after two days, and
to 2,000 after seven. Without `warmup`, the full `daily_limit` applies immediately.
A zero cap pauses reads. A curve starts at day zero, has unique nonnegative
integer days and nondecreasing caps, and never exceeds `daily_limit`.

`configure()` deliberately replaces the limit and curve, while retaining usage
and the original start time. Omit it in later jobs to keep the stored policy.
Pass `started_at` explicitly to set a known enrollment time: a timezone-aware
datetime or UTC timestamp, no later than now. The last curve cap continues
until the policy changes; it does not automatically rise to `daily_limit`.

- **Shared identity and storage:** use the same SQLite file on the same host
  for every reader that should share an allowance. Keys are authenticated
  Telegram account IDs, not session names or pool suffixes. Different accounts
  have separate policies. A missing policy stops message reads. The parent
  directory must exist; `:memory:` is not supported. The ledger stores account
  IDs, policies and counters, never login keys or message content.
- **What spends the allowance:** history, message search, replies, explicit
  message-ID lookups, discovery post reading, and message re-fetches during
  media operations. Repeated reads, service/empty message slots and messages
  later filtered out still count. A count operation that fetches a message
  counts too. User/group/dialog metadata and incidental dialog previews,
  passive updates and update recovery, and downloading file bytes are excluded.
- **When it counts:** before each actual send, tgdata reserves the request's
  maximum number of messages. Successful replies settle to the returned slot
  count and release unused capacity. Failed, cancelled or crashed attempts
  retain their full claim; each retry needs another reservation. Cached flood
  waits do not spend capacity before a send. An oversized reply is charged at
  its actual count and raises a local error.
- **Rolling expiry:** each claim expires 24 hours after its send admission,
  regardless of when the reply arrives. There is no midnight reset. A persisted
  clock high-water mark prevents backward clock changes from restoring spent
  capacity. Keep the host clock accurate; forward jumps advance expiry and
  warm-up. No SQLite transaction stays open while awaiting Telegram. Operations
  are synchronous and normally short, but contention can block the event loop
  for up to the five-second SQLite busy timeout before raising.
- **Status and stopping:** `budget.status(account_id)` is local;
  `await tg.get_read_budget()` verifies the active account and returns its
  status, or `None` without connecting when disabled. `used` includes outstanding
  `reserved` capacity; `remaining` is the available allowance. `to_dict()` adds
  ISO timestamps and `retry_after` for one message. An exhaustion exception
  also has `requested`, `account_id`, `next_available_at` and `retry_after` for
  that request. Retry times are estimates assuming no new claims or policy
  changes; `None` means a smaller request or policy change is needed.
- **Partial results:** fetch/search/discovery errors carry the processed
  DataFrame in `partial_result`; media-by-ID errors carry completed entries
  in a dictionary. Batch callbacks may already have seen some of those rows.
  Polling delivers and deduplicates its partial frame, then raises exhaustion
  instead of automatically retrying. Other `ReadBudgetError` subclasses also
  stop polling. These are local policy/storage errors, not Telegram health
  verdicts; actual Telegram errors keep their existing health reporting.
- **Request boundaries:** history/search pages shrink to the available
  allowance while preserving their cursors. ID chunks and raw request bounds
  are not silently truncated, so a chunk larger than the remaining allowance
  is refused. Use smaller ID lists when needed. Unbounded or unsupported raw
  message-returning calls and message-bearing batches raise
  `UnsupportedBudgetRequest`; metadata-only batches still work. Supported
  invoke wrappers retain the inner message bound.
- **Identity verification:** each message send uses a fresh Telegram self
  lookup, including retries; page sizing and status can add another lookup.
  Cached session identities are not billing authority. Storage/configuration
  errors fail closed before further message sends; failed settlement retains
  the prior full claim. Clients created separately, other ledger files and
  direct use of private transport internals are outside this guard.

The budget suite exercises real Telethon request/iterator code with scripted
replies on 1.45.0 and 1.33.1. It does not test live Telegram response bounds or
whether any chosen limit prevents account restrictions.

## Quick Start

### List All Group Chats 

This is required for finding chat id for the chat of interest. 

```python
from tgdata import TgData
import asyncio

async def main():
    # Initialize the client
    tg = TgData("config.ini")
    
    # List available groups and channels
    groups = await tg.list_groups()

    print(groups)

```

Outputs:

```
Python Devs 10012312313
```

### Group discovery — finding groups you are not in

`list_groups` shows what the account already follows. To find *new* rooms there are three
routes, all returning the same columns as `list_groups` plus `FoundVia` and `FoundBy`.
This is the quick start; the rules for running discovery on a real account without earning
a block — pacing, budgets, resumable runs, reading the output — are in
[`devdocs/guides/group_discovery.md`](devdocs/guides/group_discovery.md).

```python
from tgdata import TgData, build_search_queries

tg = TgData("config.ini")

# 1. Telegram's global search — matches room NAMES and @usernames only, never post text
df = await tg.search_groups("Анталия аренда")

# 2. Telegram's "similar channels" — rooms whose subscribers overlap the seeds', no keyword needed
df = await tg.similar_groups(["@antalyadaa", "@sprout_antalya"], rounds=2)

# 3. t.me links found in a room's recent posts — usernames only (free), or resolved
df = await tg.linked_groups(group_id, posts=100, resolve=False)

# All three on one session, deduplicated by id, in cost order
df = await tg.discover_groups(
    seeds=["@antalyadaa"],
    queries=build_search_queries(["Анталия", "Antalya"], topics=["чат", "аренда", "новости"],
                                 prefixes=["Турция"]),
    mine_links=True,
    heartbeat=lambda phase: print(phase),      # liveness ticks: search / similar / links / pause / flood-wait Ns
    found_callback=lambda row: rows.append(row),  # each room as it is found — persist as you go
)
```

**The name-only rule.** Telegram's search matches names and @usernames, never what a room
posts. A perfect room under an unrelated name is invisible to every query — that is what
`similar_groups` and `linked_groups` are for. Rooms name themselves "place + topic", so
`build_search_queries` combines your place spellings with topic words, in both word orders.

| Column | Meaning |
|---|---|
| `GroupID` … `ParticipantsCount` | the `list_groups` columns; `ParticipantsCount` is present on search and similar-channel results, absent (`NA`) on rooms resolved from links — Telegram's lookup reply does not carry it |
| `FoundVia` | `search` · `similar` · `link` — the cheapest route that found the room |
| `FoundBy` | the query, the seed's `@name`, or the source room |

Unresolved link rows carry only `Username`/`Identifier`; `GroupID` and the flags are `NA`
(the columns are nullable, so dtypes never drift). Every row with an id is already usable
by `get_messages(row['GroupID'])` — Telegram results land in the session cache with their
access hash, no dialog sync needed.

**Pacing and waits.** Every request is followed by `pace` seconds (default 2, the proven
pace for a personal account). A rate-limit wait up to `max_flood_wait` is obeyed exactly,
with heartbeat ticks so a watchdog sees life; a longer one raises `DiscoveryInterrupted`,
which carries `.found` (everything collected so far) and `.retry_after`. Two steps keep
Telethon's own handling: reading a room's posts for links, and the dialog sync for a numeric
id — a wait of up to a minute there is slept without ticks. A dropped connection
is waited out up to `max_offline` and the same request retried. Nothing found is ever lost.

**The budget.** Resolving a username to a room is the request Telegram punishes hardest —
a production account lost 8 and 21 hours of lookups to it. So every call has `max_resolve`
(default 100), `discover_groups` mines links from the first `link_sources` rooms only
(default 50), `resolve_links` is off by default (mined names come back as text, which costs
nothing), and a wait on a lookup is skipped or stopped, never waited out — for a
`linked_groups` source it ends the call with `DiscoveryInterrupted`. A truncating cap
logs a warning telling you which parameter lifts it.

**Similar channels** work on channels and megagroups, not basic groups; two rounds by
default (a third drifts off topic); the seeds themselves are never returned. Yield depends
on the account — a Premium account got 64 recommendations from one seed, a normal account
reportedly about 10.

**Links** are read from the visible text, from hyperlinked text (where channels put nearly
all of them) and from URL buttons. Accepted: `t.me/name`, `t.me/name/123`, `t.me/s/name`,
`t.me/boost/name`, `telegram.me/name`. Skipped: invite links (`t.me/+…`), `t.me/c/…`,
reserved paths, and bots (`…bot`). Discovery reads; it never joins.


### Get all messages of a chat 

You can use either the numeric chat ID or the username (if the chat has one).

**Note:** For large groups (2500+ messages), use batch processing with rate limit protection. 


```python
from tgdata import TgData
import asyncio

async def main():
    # Initialize the client
    tg = TgData("config.ini")

    # Fetch messages using numeric ID
    messages = await tg.get_messages(
        group_id=-1001234567890,  # Numeric ID
        limit=1000,
        with_progress=True
    )
    
    # OR using username (if the chat has one)
    messages = await tg.get_messages(
        group_id="@channelname",  # Username with @
        limit=1000,
        with_progress=True
    )
    
    # Export to CSV
    tg.export_messages(messages, "messages.csv")

asyncio.run(main())
```

### Get message count of a chat 



```python
from tgdata import TgData
import asyncio

async def main():
    # Initialize the client
    tg = TgData("config.ini")

    # Get count using numeric ID or username
    message_count = await tg.get_message_count(
        group_id=-1001234567890,  # Numeric ID
        # OR: group_id="@channelname"  # Username
    )

    print(message_count)

asyncio.run(main())
```




## Advanced Usage

### Using Usernames vs Numeric IDs

```python
# Both approaches work identically:

# Option 1: Using username (recommended if available)
messages = await tg.get_messages(
    group_id="@channelname",
    limit=100
)

# Option 2: Using numeric ID
messages = await tg.get_messages(
    group_id=-1001234567890,
    limit=100
)
```

A numeric id resolves only if the session can actually see the group. On a
cache miss tgdata syncs the account's chat list once and retries — so fresh
sessions work for groups the account belongs to. If the group still can't be
found it raises `tgdata.GroupAccessError` (the account is not a member, or
the id is wrong) instead of Telethon's generic "Could not find the input
entity" ValueError.

### get_messages with start_date parameter

```python
    tg = TgData("config.ini")
    # Fetch recent messages for ETL processing
    yesterday = datetime.now() - timedelta(days=1)
    messages = await tg.get_messages(
        group_id="@channelname",  # Can use username
        start_date=yesterday,
        with_progress=True
    )
    

```

### Incremental Message Fetching

```python
from tgdata import TgData

async def incremental_fetch():
    tg = TgData("config.ini")
    
    # Get the latest message ID from your storage, or db
    last_processed_id = load_checkpoint()  # Your implementation
    
    # Fetch only messages after that ID
    new_messages = await tg.get_messages(
        group_id="@channelname",  # Can use username or numeric ID
        after_id=last_processed_id
    )

    save_checkpoint(new_messages['MessageId'].max())   # Your implementation


asyncio.run(incremental_fetch())
```

### Stable message batches for storage and delivery

Use `get_message_batch` for a versioned raw snapshot that can be saved and
replayed. It keeps senderless and service messages, reads oldest first after an
exclusive cursor, and uses the same client and optional read budget. Designed
and tested with Telethon **1.45.0**.

```python
from tgdata import TgData, MessageBatch

async def prepare_batch():
    tg = TgData("config.ini")
    try:
        batch = await tg.get_message_batch(
            "@channelname", after_id=100, limit=200,
            download_media_to="out/media",  # omit for references only
        )
        manifest = batch.save("out/batches")
        replay = MessageBatch.from_json(manifest.read_bytes())
        assert replay.batch_id == batch.batch_id
        return manifest, batch.next_after_id
    finally:
        await tg.close()
```

Send the saved batch using `batch_id` for receiver deduplication, and advance
your stored cursor only after acknowledgment. If acknowledgment is lost, replay
that file: a fresh Telegram fetch can produce a different observation. Requested
photo/document files are named by their content hash; saving the manifest does
not copy its media. Blob paths are relative to `out/media` in this example.

Ordinary failures after group resolution carry the completed prefix as a
`MessageBatch` in `error.partial_result` and still raise. `next_after_id` never
passes an unfinished record/file. Local file errors keep their type without
inventing a Telegram health verdict. A secondary cleanup failure is logged by
operation/type and preserves the original error or cancellation; storage that
refuses cleanup may leave a private temporary file. The exact schema, limits,
interruption rules
and delivery protocol are in [Message batch v1](docs/message_batch_v1.md).

### Daily continuation across restarts

Use a progress store when tgdata should remember unfinished delivery and the last
accepted message for each group:

```python
from tgdata import TgData, SQLiteSyncStore

tg = TgData("config.ini", interactive_login=False,
            sync_store=SQLiteSyncStore("daily-progress.sqlite3"))
chat_id = -1001234567890  # canonical MessageBatch.chat_id

# Initial setup: your existing archive's last accepted ID, or explicit 0.
await tg.initialize_sync(chat_id, after_id=48213)
try:
    batch = await tg.sync_group(chat_id, limit=200)
    if batch is not None:
        await destination.accept(batch)  # your durable, duplicate-safe destination
        await tg.acknowledge_sync(chat_id, batch.batch_id)
finally:
    await tg.close()
```

The next run replays a pending batch without contacting Telegram, or reads after
the acknowledged position. Preparing a batch never advances progress. Matching
repeated initialization does not reset it. `destination.accept` is your application
function; acknowledge only after its effects and duplicate markers are committed.

This first delivery supports one reader per group. Scheduling remains with the
caller; backfill is separate and edits/deletions are not reconciled. Optional media,
partial budget failures, custom storage and exact acknowledgment rules are covered
in [Daily continuation](docs/daily_continuation.md). Run the local example without
Telegram using `python examples/daily_continuation.py --demo`.

### Fixed historical windows

Give a historical collection its own progress store, then freeze its window at
first enrollment:

```python
from tgdata import TgData, SQLiteSyncStore

tg = TgData("config.ini", sync_store=SQLiteSyncStore("historical-progress.sqlite3"))
try:
    await tg.initialize_sync(chat_id, after_id=0, last_days=30)
    batch = await tg.sync_group(chat_id, limit=200)
    if batch is not None:
        await destination.accept(batch)
        await tg.acknowledge_sync(chat_id, batch.batch_id)
finally:
    await tg.close()
```

Repeated matching initialization reuses the saved dates. You can instead enroll
with timezone-aware `start_date` and `end_date`; the start is included and end
excluded. Daily and historical collections use separate stores, so their bookmarks
stay independent. See [Fixed historical windows](docs/fixed_windows.md) for date
limits, restart rules and direct batch reads. Scheduling and pacing remain with
the caller.

### Detecting & Downloading Media (photos / videos)

Every fetched message carries media-reference columns, so you can tell whether a
message has a photo **without downloading anything**:

| Column | Meaning |
|---|---|
| `MediaType` | `'photo'`, `'video'`, `'document'`, `'webpage'`, … or `None` (text-only) |
| `GroupedId` | album tag — rows sharing the same value are one multi-photo post (else `None`) |
| `MessageLink` | `t.me` deep link to the original message |
| `MediaPath` | local file path once media is downloaded (else `None`) |

> ⚠️ **`'webpage'` is NOT a real photo.** It is a link-preview thumbnail, not an
> attached image. Filter on the actual attachment type (`'photo'` / `'video'`) —
> **never** on "`MediaType` is not null" — or you will count URL previews as media.

```python
messages = await tg.get_messages(group_id="@channelname", limit=100)

# ✅ correct — real attached photos only
photos = messages[messages['MediaType'] == 'photo']

# ❌ wrong — also catches 'webpage' link previews, which are NOT real images
# media = messages[messages['MediaType'].notna()]

# how many photos each album/listing has
photos.groupby('GroupedId').size()
```

Get the actual media in one of three ways:

```python
# A) On demand — fetch references cheaply, then download only what you keep.
#    Pass every MessageId sharing a GroupedId to grab a whole album.
paths = await tg.download_media_by_id("@channelname", [12345, 12346], output_dir="media")
# -> {12345: "media/photo_....jpg", 12346: None}   (None = nothing downloadable, e.g. a webpage)

# B) During the fetch, to disk — one call returns the data AND writes the files.
messages = await tg.get_messages(
    group_id="@channelname",
    limit=100,
    download_media_to="media",   # each file's path is recorded in the MediaPath column
)

# C) During the fetch, in memory — bytes land in the DataFrame itself (MediaData column).
#    Great for small scrapes; holds every file in RAM, so scope it.
messages = await tg.get_messages(
    group_id="@channelname",
    limit=100,
    include_media=True,          # MediaData = raw bytes per row (None for text/webpage)
)
# Note: CSV export drops MediaData; JSON stores a "[Binary data]" placeholder.
```

Downloaded files (modes A and B) are named `<ChatId>_<MessageId>.<ext>` — e.g.
`1707717812_183019.jpg` — so every file is traceable to its exact message and
group from the filename alone (and won't collide across groups sharing a folder).
The precise path is also recorded per row in the `MediaPath` column.

**Re-scraping is idempotent:** if a message's file is already on disk, it is
reused, not re-downloaded — so pulling the same (or an overlapping) range again
never duplicates files or re-fetches bytes. Each message maps to exactly one file.

### Progress Monitoring

```python
async def monitor_extraction():
    tg = TgData()
    
    def progress_callback(current, total, rate):
        percent = (current / total * 100) if total else 0
        print(f"Progress: {current}/{total} ({percent:.1f}%) - {rate:.1f} msg/s")
    
    messages = await tg.get_messages(
        group_id=-1001234567890,
        limit=10000,
        progress_callback=progress_callback
    )
```

### Batch Processing for Large Groups

```python
# For groups with 100k+ messages, use batch processing with rate limit protection
async def process_large_group():
    tg = TgData("config.ini")
    
    async def save_batch(batch_df, batch_info):
        # Process each batch (e.g., save to database)
        print(f"Batch {batch_info['batch_num']}: {len(batch_df)} messages")
        batch_df.to_csv(f"batch_{batch_info['batch_num']}.csv")
    
    await tg.get_messages(
        group_id="@largechannel",  # Works with username
        batch_size=500,  # Process 500 messages at a time
        batch_callback=save_batch,
        batch_delay=2.0,  # Wait 2 seconds between batches
        rate_limit_strategy='exponential'  # Handle rate limits gracefully
    )
```

### Custom callback 




### Polling for New Messages

```python
async def poll_messages():
    tg = TgData()
    
    # Define callback for new messages
    async def process_batch(messages_df):
        print(f"Got {len(messages_df)} new messages")
        # Process messages here
    
    # Poll every 30 seconds
    await tg.poll_for_messages(
        group_id="@channelname",  # Works with username
        interval=30,
        callback=process_batch,
        max_iterations=10  # Stop after 10 polls
    )
```

Polling stops, raising the error, when polling again cannot help:
- the account is logged out, banned or restricted;
- it cannot read the group (`CHANNEL_PRIVATE`, `GroupAccessError`, ...);
- the session is not logged in (`AuthRequiredError`);
- the proxy setting is unusable (`ProxyConfigError`).

Network errors, rate-limit waits and server errors are logged and retried at
the next interval, as before. An exception raised by your callback now reaches
you; it used to be logged, and those messages were skipped.


### Real-time Message Events

```python
# Monitor messages in real-time
tg = TgData("config.ini")

@tg.on_new_message(group_id="@channelname")  # Works with username
async def handle_message(event):
    print(f"New message: {event.message.text}")

await tg.run_with_event_loop()
```


### Account health events

Every time Telegram says no to an account, tgdata tells you:
- which verdict;
- about what — the account, one kind of request, or one group;
- from which call;
- for how long;
- when it ended.

It reports and never acts. No exception changes, and nothing is paused or
retried because of a verdict.

```python
def on_health(event):                # or an async function
    print(event['verdict'], event['scope'], event['error'], event['call'])

tg = TgData("config.ini", health_callback=on_health, account_label="reader-7")
```

| Verdict | About | Telegram's names |
|---|---|---|
| `waiting` | one request type | `FLOOD_WAIT_X`, `FLOOD_PREMIUM_WAIT_X`, `SLOWMODE_WAIT_X`, `FLOOD_TEST_PHONE_WAIT_X` — with the seconds |
| `logged out` | the account | `AUTH_KEY_UNREGISTERED`, `SESSION_REVOKED`, `SESSION_EXPIRED`, `AUTH_KEY_INVALID`, `AUTH_KEY_DUPLICATED` |
| `banned` | the account | `USER_DEACTIVATED_BAN`, `USER_DEACTIVATED`, `PHONE_NUMBER_BANNED` |
| `restricted` | the account | `FROZEN_METHOD_INVALID`, `FROZEN_PARTICIPANT_MISSING`, `USER_RESTRICTED`, `PEER_FLOOD` |
| `no access` | one group | `CHANNEL_PRIVATE`, `CHAT_FORBIDDEN`, `CHANNEL_INVALID`, `USER_BANNED_IN_CHANNEL`, `CHANNEL_PUBLIC_GROUP_NA`, `CHANNEL_BANNED`, and tgdata's `GroupAccessError` |
| `unclassified` | — | any other Telegram error in the 401, 403, 406 or 420 categories, with its name (file-reference errors excepted) |
| `ok` | what recovered | — |

Nothing else is an event: bad requests (400), server errors, network and proxy
errors, a lookup that found nothing, or a session that was never logged in.

An event is a plain dict that survives `json.dumps`:

```python
{'kind': 'health', 'time': '2026-10-03T14:02:11.418523+00:00',
 'account': {'label': 'reader-7', 'session': 'reader7', 'user_id': 123456789},
 'verdict': 'no access', 'scope': 'group', 'group': 'somegroup',
 'call': 'get_messages', 'request': 'GetHistoryRequest',
 'wait_seconds': None, 'error': 'CHANNEL_PRIVATE', 'source': 'error'}
```

- **`group`** is the group as you named it: an int stays an int; `@Name` and
  t.me links become `name`.
- **`call`** is the `TgData` method; **`request`** is Telegram's request type.
- **`source`** says where it came from:
  - `error` — it ended the call, and you also get the exception;
  - `sleep` — Telethon slept through a wait of up to a minute, silently;
  - `handled` — tgdata waited it out itself;
  - `swallowed` — tgdata skipped the item and carried on, such as a
    discovery seed or link;
  - `recovery` — an `ok`.

**"ok" only when Telegram shows a condition ended:**
- **a wait** — the call that waited completes successfully;
- **logged out or banned** — a call completes that Telegram answered after
  the problem was recorded;
- **restricted** — the same, from the method that was refused;
- **no access** — the same, from a call naming that group.

A call that merely completes proves nothing. A call Telegram answered before
the problem was seen, or one that sent no request at all, never sends `ok`.

**Delivery.** The event that ends a call is delivered before its exception
reaches you. The callback may be a function or a coroutine function. If it
raises, the error is logged — first at WARNING with its traceback, then at
DEBUG — and nothing else changes. A wait Telethon sleeps through is delivered
from inside the request: a function runs there, a coroutine is scheduled.
The callback may call tgdata itself. Events caused by those calls are logged
and counted, but not delivered back to it, so it never calls itself.

**Summary.** `(await tg.health_check())['health']` holds, for this `TgData`,
in memory:
- the account's verdict, and since when;
- the open waits per request type;
- the groups without access;
- the wait count and total seconds;
- the event count;
- the last unclassified name.

**Log lines.** Each event is also logged on `tgdata.tgdata.health`, so
`log_file=` receives it: WARNING for logged out, banned, restricted and
unclassified; INFO for waiting, no access and ok. Your own logging output is
otherwise unchanged. The INFO lines in which Telethon logs its silent sleeps
stay hidden unless you asked for them.

**`validate_connection()` and `health_check()` ask Telegram directly.**
Telethon's `get_me()` answers a logout or a ban with `None` instead of an
error, so both now confirm with Telegram whether the session is logged in.
- `validate_connection()` still returns `True` or `False`. On `False` it says
  why: at WARNING with Telegram's name when it is a verdict, and as an event.
- `health_check()` marks such a connection unhealthy and names the verdict in
  `errors`, e.g. `logged out (AUTH_KEY_UNREGISTERED)`. It reports it as an
  event, and the same result's `['health']` already includes it.

**Not covered yet.**
- Signals that Telethon's background update loop only logs: an account banned
  in one channel, and waits while catching up.
- `restricted` follows Telegram's documentation; how a frozen account behaves
  when it only reads has not been observed.
- Capturing Telethon's silent sleeps relies on Telethon creating its INFO
  record: `logging.disable(logging.INFO)` or higher turns the capture off, and
  a level set on `telethon.client.users` during a call applies from the next
  call.

### Performance Tips

- The client authenticates once and keeps a single **persistent connection**,
  reused across all calls; release it with `await tg.close()` or use
  `async with TgData("config.ini") as tg:`
- Implement checkpoint logic for incremental processing
- Implement progress callbacks for visibility
- Export data incrementally for large datasets

## Requirements

- Python 3.7+
- Telegram API credentials (not bot tokens)
- Group/channel membership

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
