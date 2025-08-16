# Limitations

## Technical Limitations

### 1. User Account Based
- **Not a Bot API**: Uses MTProto user API, not Bot API
- **Requires Phone Number**: Must authenticate with a real phone number
- **Session Management**: Requires persistent session files
- **Single Account**: Each instance uses one user account

### 2. Rate Limits
- **Telegram Enforced**: Subject to Telegram's rate limiting
- **FloodWaitError**: Must wait when hitting limits (typically 30-300 seconds)
- **Daily Limits**: Approximate limits:
  - ~30 requests per second per connection
  - ~1000 channel joins per day
  - ~50 username resolves per day

### 3. Message Retrieval Constraints
- **Historical Limit**: Can only access messages while being a member
- **Deleted Messages**: Cannot retrieve deleted messages
- **Edited Messages**: Gets latest version only
- **Message Order**: Retrieved in reverse chronological order by default

### 4. Media Handling
- **Profile Photos Only**: Currently downloads profile photos, not message media
- **No Video/Audio**: Does not handle video or audio messages
- **No Stickers/GIFs**: Special media types not processed
- **File Size**: Large media can slow down operations

## API Limitations

### 1. Data Access
- **Member Only**: Must be a member of the group/channel
- **Private Groups**: Cannot access without invitation
- **Restricted Content**: Some channels restrict message history
- **Admin Actions**: Cannot perform admin operations

### 2. Search Limitations
- **Basic Search**: Only text-based search supported
- **No Regex**: Search uses Telegram's built-in search
- **Limited Operators**: No complex search queries
- **Performance**: Search in large groups can be slow

### 3. Real-time Constraints
- **Not Real-time**: Designed for batch processing
- **No Push Updates**: Doesn't receive live updates
- **Polling Required**: Must poll for new messages
- **Latency**: Several seconds delay for "real-time" monitoring

## Performance Limitations

### 1. Memory Usage
- **In-Memory Processing**: All messages loaded into memory
- **DataFrame Storage**: Pandas DataFrames can be memory-intensive
- **Photo Storage**: Profile photos increase memory usage
- **Scaling Issues**: 1M+ messages require significant RAM

### 2. Processing Speed
- **Sequential by Default**: Messages fetched sequentially
- **Network Bound**: Limited by network latency
- **API Throttling**: Automatic throttling reduces speed
- **Large Groups**: Fetching all messages from large groups is slow

### 3. Concurrency Limits
- **Connection Pool**: Limited to 3-5 concurrent connections
- **Shared State**: Single group state per instance
- **No Parallel Groups**: Cannot process multiple groups simultaneously in one instance

## Feature Limitations

### 1. Message Types
- **Text Focus**: Optimized for text messages
- **Limited Media**: Basic media support only
- **No Polls**: Doesn't handle polls
- **No Reactions**: Doesn't capture message reactions
- **No Threads**: Doesn't handle threaded conversations

### 2. Metadata Gaps
- **Limited User Info**: Basic user information only
- **No Online Status**: Doesn't track user presence
- **No Read Receipts**: Cannot see who read messages
- **No Typing Indicators**: No real-time activity data

### 3. Export Formats
- **Basic Formats**: Only CSV and JSON
- **No Pagination**: Exports entire dataset
- **Limited Customization**: Fixed column structure
- **No Streaming**: Must load all data before export

## Operational Limitations

### 1. Authentication
- **Manual First Time**: Requires manual code entry initially
- **Phone Verification**: SMS/call verification needed
- **2FA Support**: Manual password entry for 2FA
- **Session Expiry**: Sessions can expire requiring re-auth

### 2. Error Recovery
- **Limited Retry**: Basic exponential backoff only
- **Connection Loss**: Requires manual reconnection
- **Partial Failures**: No automatic resume for partial exports
- **State Loss**: In-memory state lost on crash

### 3. Monitoring
- **Basic Metrics**: Limited built-in monitoring
- **No Dashboards**: No built-in visualization
- **Manual Tracking**: Progress tracking requires custom code
- **Limited Alerts**: No built-in alerting system

## Scalability Limitations

### 1. Vertical Scaling
- **Single Process**: Runs in a single Python process
- **GIL Bound**: Subject to Python's Global Interpreter Lock
- **Memory Bound**: Limited by available RAM
- **CPU Limited**: Cannot utilize multiple CPUs effectively

### 2. Horizontal Scaling
- **Session Conflicts**: Cannot share sessions between instances
- **No Coordination**: No built-in distributed coordination
- **Manual Sharding**: Must manually partition work
- **State Synchronization**: No shared state between instances

## Data Limitations

### 1. Historical Data
- **Join Date Limit**: Cannot access messages before joining
- **No Backfill**: Cannot retrieve pre-membership messages
- **Deletion Permanent**: Deleted messages are gone forever
- **Edit History**: No access to message edit history

### 2. Group Information
- **Basic Metadata**: Limited group information available
- **No Member Lists**: Cannot enumerate all members
- **No Permissions**: Cannot see detailed permissions
- **No Settings**: Cannot access group settings

## Workarounds and Mitigations

### For Rate Limits
```python
# Use connection pooling
tg = TgData(connection_pool_size=3)

# Implement backoff
async def fetch_with_backoff(tg, group_id):
    while True:
        try:
            return await tg.get_messages(group_id=group_id)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
```

### For Memory Limitations
```python
# Process in chunks
async def process_large_group(tg, group_id):
    last_id = 0
    while True:
        messages = await tg.get_messages(group_id=group_id, after_id=last_id)
        if messages.empty:
            break
        
        # Process chunk
        process_chunk(messages)
        
        # Update last_id
        last_id = messages['MessageId'].max()
```

### For Performance
```python
# Use date filters
messages = await tg.get_messages(
    group_id=12345,
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now()
)

# Enable caching
messages = await tg.get_messages(
    group_id=12345,
    limit=1000,
    use_cache=True  # Second call will be faster
)
```

## Future Considerations

These limitations are based on the current implementation. Future versions may address:
- Media message support
- Streaming exports
- Better distributed processing
- Real-time update handling
- Advanced search capabilities

Always check the latest documentation for updates on these limitations.