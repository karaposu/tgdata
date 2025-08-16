# tgdata

A production-grade Python library for extracting and processing Telegram group and channel messages. Designed for ETL pipelines, data analysis, and archival purposes.

## Features

- 🚀 **Production-Ready**: Built for reliability and scale in ETL pipelines
- 📊 **Efficient Data Extraction**: Fetch messages from groups and channels with rate limit handling
- 🔄 **Smart Deduplication**: Avoid reprocessing messages with pluggable tracker backends
- 📈 **Progress Tracking**: Monitor long-running operations with real-time progress
- 🔌 **Extensible Architecture**: Support for Redis, MongoDB, SQLite, and custom storage backends
- 🛡️ **Robust Error Handling**: Automatic retries with exponential backoff
- 📁 **Multiple Export Formats**: Export to CSV, JSON, or integrate with your data pipeline
- 🔔 **Real-time Updates**: Listen for new messages with event handlers
- ⏱️ **Polling Support**: Poll for new messages at configurable intervals

## Installation

```bash
pip install tgdata
```

## Quick Start

```python
from tgdata import TgData
import asyncio

async def main():
    # Initialize the client
    tg = TgData()
    
    # List available groups and channels
    groups = await tg.list_groups()
    print(f"Found {len(groups)} groups/channels")
    
    # Fetch messages from a specific group
    messages = await tg.get_messages(
        group_id=-1001234567890,  # Your group ID
        limit=1000,
        with_progress=True
    )
    
    # Export to CSV
    tg.export_messages(messages, "messages.csv")
    
    # Get message statistics
    stats = tg.get_statistics(messages)
    print(f"Total messages: {stats['total_messages']}")
    print(f"Date range: {stats['date_range']['first']} to {stats['date_range']['last']}")

asyncio.run(main())
```

## Configuration

Create a `config.ini` file with your Telegram API credentials:

```ini
[telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
session_file = telegram_session
```

Get your API credentials from [https://my.telegram.org/apps](https://my.telegram.org/apps)

## Advanced Usage

### ETL Pipeline Integration

```python
from tgdata import TgData
from datetime import datetime, timedelta
import asyncio

async def etl_pipeline():
    tg = TgData()
    
    # Fetch recent messages for ETL processing
    yesterday = datetime.now() - timedelta(days=1)
    messages = await tg.get_messages(
        group_id=-1001234567890,
        start_date=yesterday,
        with_progress=True
    )
    
    # Filter messages
    filtered = tg.filter_messages(
        messages,
        keyword="important",
        start_date=yesterday
    )
    
    # Export for data pipeline
    tg.export_messages(filtered, "daily_extract.json", format="json")
    
    # Get metrics
    metrics = await tg.get_metrics()
    print(f"Processed {len(filtered)} messages")

asyncio.run(etl_pipeline())
```

### Message Deduplication with Redis

```python
from tgdata import TgData
from tgdata.trackers import RedisTracker

async def deduplicated_extraction():
    # Use Redis to track processed messages
    tracker = RedisTracker(host="localhost", port=6379)
    tg = TgData(tracker=tracker)
    
    # Only fetch new messages since last run
    messages = await tg.get_messages(
        group_id=-1001234567890,
        limit=100
    )
    
    print(f"New messages: {len(messages)}")

asyncio.run(deduplicated_extraction())
```

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

### Real-time Message Monitoring

```python
async def monitor_real_time():
    tg = TgData()
    
    # Register handler for new messages
    @tg.on_new_message(group_id=-1001234567890)
    async def handle_message(event):
        print(f"New message from {event.sender_id}: {event.message.text}")
        
        # React to commands
        if event.message.text == "!ping":
            await event.reply("Pong!")
    
    # Run event loop
    await tg.run_with_event_loop()
```

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
        group_id=-1001234567890,
        interval=30,
        callback=process_batch,
        max_iterations=10  # Stop after 10 polls
    )
```

## API Reference

### TgData

Main class for interacting with Telegram groups and channels.

#### Methods

**Core Methods:**
- `list_groups()` - List all accessible groups and channels
- `get_messages()` - Fetch messages with various filters
- `search_messages()` - Search for specific content
- `filter_messages()` - Filter messages by criteria
- `export_messages()` - Export to CSV or JSON
- `get_statistics()` - Get message statistics
- `get_metrics()` - Get session metrics
- `get_message_count()` - Get total message count without fetching all

**Real-time & Polling:**
- `on_new_message()` - Decorator to register real-time message handlers
- `poll_for_messages()` - Poll for new messages at intervals
- `run_with_event_loop()` - Run client with event loop for real-time events

### Message Trackers

Prevent duplicate processing across runs:

- `InMemoryTracker` - Default, resets on restart
- `RedisTracker` - Persistent Redis storage
- `SQLiteTracker` - Local SQLite database
- `MongoTracker` - MongoDB backend

## Production Deployment

### Best Practices

1. **Use environment variables for credentials**:
   ```python
   import os
   config_path = os.getenv("TELEGRAM_CONFIG", "config.ini")
   tg = TgData(config_path=config_path)
   ```

2. **Implement error handling**:
   ```python
   try:
       messages = await tg.get_messages(group_id=group_id)
   except Exception as e:
       logger.error(f"Failed to fetch messages: {e}")
       # Implement retry logic or alerting
   ```

3. **Monitor rate limits**:
   ```python
   health = await tg.health_check()
   if not health['primary_connection']:
       # Handle connection issues
   ```

### Performance Tips

- Use connection pooling for parallel operations
- Enable message deduplication to avoid reprocessing
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

## Support

- Documentation: [Full documentation](https://github.com/yourusername/tgdata)
- Issues: [GitHub Issues](https://github.com/yourusername/tgdata/issues)
- Examples: See the [examples/](examples/) directory

## Disclaimer

This tool is for legitimate data collection and analysis only. Users must comply with Telegram's Terms of Service and applicable laws. Always respect user privacy and platform rate limits.