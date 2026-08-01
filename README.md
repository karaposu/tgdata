# tgdata

A production-grade Python library for extracting and processing Telegram group and channel messages. Designed for ETL pipelines, data analysis, and archival purposes.

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
