# Edge Cases Covered

## Connection and Authentication Edge Cases

### 1. Session Expiration
**Scenario**: Telegram session expires after long inactivity  
**Handling**: Automatic reconnection with retry logic
```python
# Built-in handling in ConnectionEngine
async def _connect_with_retry(self, client: TelegramClient):
    for attempt in range(config.max_retries):
        try:
            await client.connect()
            if not await client.is_user_authorized():
                # Handle re-authentication
                raise Exception("Manual authentication required")
        except Exception as e:
            if attempt < config.max_retries - 1:
                await asyncio.sleep(delay)
```

### 2. Network Interruptions
**Scenario**: Connection drops during message retrieval  
**Handling**: Graceful failure with ability to resume
```python
# Resume from last message ID
last_id = 12345  # Stored from previous run
messages = await tg.get_messages(group_id=group_id, after_id=last_id)
```

### 3. Rate Limit Flooding
**Scenario**: Hit Telegram's rate limits (FloodWaitError)  
**Handling**: Automatic wait and retry with connection pooling
```python
# Connection pool rotates connections
pool.mark_rate_limited(conn, wait_seconds=flood_error.seconds)
next_conn = await pool.get_connection()  # Gets non-rate-limited connection
```

## Message Retrieval Edge Cases

### 4. Empty Groups
**Scenario**: Group has no messages  
**Handling**: Returns empty DataFrame without errors
```python
messages = await tg.get_messages(group_id=empty_group_id)
assert messages.empty  # True, but no errors
```

### 5. Deleted Messages
**Scenario**: Messages deleted between retrieval attempts  
**Handling**: Silently skips deleted messages
```python
# MessageEngine handles missing messages gracefully
if not sender:  # Message might be deleted
    continue
```

### 6. Very Large Groups
**Scenario**: Group with millions of messages  
**Handling**: Limit-based retrieval with progress tracking
```python
# Fetch in manageable chunks
messages = await tg.get_messages(
    group_id=large_group_id,
    limit=10000,  # Reasonable chunk size
    with_progress=True
)
```

### 7. Date Range Edge Cases
**Scenario**: Invalid date ranges (start > end)  
**Handling**: Proper date filtering logic
```python
# End date before start date - returns empty
messages = await tg.get_messages(
    start_date=datetime(2024, 12, 31),
    end_date=datetime(2024, 1, 1)
)  # Returns empty DataFrame
```

## Data Processing Edge Cases

### 8. Unicode and Emoji Handling
**Scenario**: Messages with complex Unicode/emojis  
**Handling**: Proper UTF-8 encoding throughout
```python
# Handles emojis and special characters
message_with_emoji = "Hello 👋 мир 世界"
df.to_csv('output.csv', encoding='utf-8')
```

### 9. Null/Missing Values
**Scenario**: Messages without text (media only)  
**Handling**: Null-safe operations
```python
# Statistics handle None values
stats = tg.get_statistics(df)  # Won't crash on None messages
messages_with_text = df['Message'].notna().sum()
```

### 10. Malformed Messages
**Scenario**: Corrupted or malformed message data  
**Handling**: Skips problematic messages with logging
```python
try:
    message_data = await self._process_message(msg, client, include_photos)
    if message_data:
        messages_data.append(message_data.to_dict())
except Exception as e:
    logger.error(f"Error processing message {msg.id}: {e}")
    # Continue with next message
```

## Memory and Performance Edge Cases

### 11. Memory Pressure
**Scenario**: System running low on memory  
**Handling**: LRU cache eviction in trackers
```python
# InMemoryTracker with size limit
tracker = InMemoryTracker(max_size=10000)
# Automatically evicts oldest entries when full
```

### 12. Concurrent Access
**Scenario**: Multiple operations on same TgData instance  
**Handling**: Not thread-safe by design, but handles async properly
```python
# Safe concurrent operations with separate instances
async def process_groups(group_ids):
    tasks = []
    for gid in group_ids:
        tg = TgData()  # Separate instance per group
        tasks.append(tg.get_messages(group_id=gid))
    return await asyncio.gather(*tasks)
```

### 13. Cache Invalidation
**Scenario**: Switching between groups rapidly  
**Handling**: Automatic cache clearing on group change
```python
tg.set_group(12345)  # Clears cache for previous group
# Fresh data for new group
```

## Export and Storage Edge Cases

### 14. File System Errors
**Scenario**: No write permissions or disk full  
**Handling**: Proper error propagation
```python
try:
    tg.export_messages(df, '/read_only/path.csv')
except PermissionError:
    # Handle gracefully
    logger.error("Cannot write to destination")
```

### 15. Large Exports
**Scenario**: Exporting millions of messages  
**Handling**: Chunked processing (user implementation)
```python
# Process in chunks to avoid memory issues
for chunk in pd.read_csv('large_export.csv', chunksize=10000):
    process_chunk(chunk)
```

### 16. Special Characters in Export
**Scenario**: Messages with quotes, commas in CSV  
**Handling**: Proper CSV escaping via pandas
```python
# Pandas handles CSV escaping automatically
message = 'He said, "Hello, world!"'
df.to_csv('output.csv')  # Properly escaped
```

## Tracker Edge Cases

### 17. Tracker Failures
**Scenario**: Custom tracker throws exception  
**Handling**: Continues operation but logs errors
```python
# Deduplication continues even if tracker fails
try:
    if await self.tracker.is_processed(msg.id, group_id):
        continue
except Exception as e:
    logger.error(f"Tracker error: {e}")
    # Process message anyway
```

### 18. Clock Skew
**Scenario**: System time changes during operation  
**Handling**: Uses monotonic time for progress tracking
```python
# Progress tracker uses relative time
elapsed = (datetime.now() - self.start_time).total_seconds()
rate = self.current / elapsed if elapsed > 0 else 0
```

## Group and Channel Edge Cases

### 19. Private Channels
**Scenario**: Accessing invite-only channels  
**Handling**: Proper error messages
```python
try:
    messages = await tg.get_messages(group_id=private_channel_id)
except ChannelPrivateError:
    logger.error("Cannot access private channel without invitation")
```

### 20. Renamed Groups
**Scenario**: Group ID remains same but title changes  
**Handling**: Group identified by ID, not title
```python
# Always use group_id, not group title
tg.set_group(12345)  # Works even if group renamed
```

## Progress Tracking Edge Cases

### 21. Unknown Total Count
**Scenario**: Don't know total messages in advance  
**Handling**: Progress works without total
```python
def progress_callback(current, total, rate):
    if total:
        percent = (current / total) * 100
    else:
        # Just show count and rate
        print(f"Processed {current} messages at {rate:.1f} msg/s")
```

### 22. Zero Messages
**Scenario**: Progress tracking with no messages  
**Handling**: Handles gracefully without division by zero
```python
# No crash on empty results
messages = await tg.get_messages(
    group_id=12345,
    with_progress=True  # Won't crash even if no messages
)
```

## Configuration Edge Cases

### 23. Missing Configuration
**Scenario**: config.ini file missing or incomplete  
**Handling**: Clear error messages
```python
try:
    config = self._load_config()
except KeyError as e:
    raise ValueError(f"Missing configuration: {e}")
```

### 24. Invalid Credentials
**Scenario**: Wrong API ID/hash  
**Handling**: Proper authentication errors
```python
except AuthKeyUnregisteredError:
    logger.error("Invalid API credentials or session expired")
```

## Best Practices for Edge Cases

1. **Always Check Return Values**
```python
messages = await tg.get_messages(group_id=12345)
if not messages.empty:
    # Process messages
```

2. **Handle Exceptions Appropriately**
```python
try:
    await tg.get_messages(group_id=12345)
except FloodWaitError as e:
    await asyncio.sleep(e.seconds)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

3. **Validate Input Data**
```python
if start_date > end_date:
    logger.warning("Invalid date range")
    return pd.DataFrame()  # Empty result
```

4. **Test Edge Cases**
```python
# Test with empty groups
# Test with very large groups
# Test with network interruptions
# Test with invalid inputs
```