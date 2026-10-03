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


### Real-time Message Events

```python
# Monitor messages in real-time
tg = TgData("config.ini")

@tg.on_new_message(group_id="@channelname")  # Works with username
async def handle_message(event):
    print(f"New message: {event.message.text}")

await tg.run_with_event_loop()
```


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
