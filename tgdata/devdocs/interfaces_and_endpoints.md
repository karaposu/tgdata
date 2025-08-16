# Interfaces and Endpoints

## Core Interfaces

### 1. TgData (Main API)

The primary interface for all operations. This is the only class most users need to interact with.

```python
class TgData:
    def __init__(self,
                 config_path: str = "config.ini",
                 connection_pool_size: int = 1,
                 log_file: Optional[str] = None)
```

## Primary Endpoints

### Group Management

#### `list_groups() -> pd.DataFrame`
- **Purpose**: List all accessible Telegram groups/channels
- **Returns**: DataFrame with columns: GroupID, Title, Username, IsChannel, IsMegagroup, ParticipantsCount
- **Async**: Yes

#### `set_group(group_id: int) -> None`
- **Purpose**: Set the current group for subsequent operations
- **Side Effects**: Clears message cache for previous group
- **Async**: No

### Message Operations

#### `get_messages(...) -> pd.DataFrame`
```python
async def get_messages(
    group_id: Optional[int] = None,
    limit: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    after_id: int = 0,
    include_profile_photos: bool = False,
    with_progress: bool = False,
    progress_callback: Optional[Callable] = None
) -> pd.DataFrame
```
- **Purpose**: Retrieve messages from a group
- **Features**: Date filtering, progress tracking, photo retrieval, incremental extraction
- **Use Cases**: 
  - Get recent messages: `get_messages(limit=100)`
  - Get all messages: `get_messages(after_id=0)`
  - Incremental updates: `get_messages(after_id=last_id)`
- **Returns**: DataFrame with message data

#### `search_messages(query: str, group_id: Optional[int] = None, limit: Optional[int] = None) -> pd.DataFrame`
- **Purpose**: Search for messages containing specific text
- **Returns**: Filtered DataFrame
- **Async**: Yes

### Data Processing

#### `filter_messages(...) -> pd.DataFrame`
```python
def filter_messages(
    df: pd.DataFrame,
    sender_id: Optional[int] = None,
    username: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> pd.DataFrame
```
- **Purpose**: Filter messages by various criteria
- **Operates On**: Existing DataFrame
- **Async**: No

#### `get_statistics(df: pd.DataFrame) -> Dict[str, Any]`
- **Purpose**: Calculate statistics from messages
- **Returns**: Dict with total_messages, unique_senders, date_range, top_senders, etc.
- **Async**: No

### Export Operations

#### `export_messages(df: pd.DataFrame, filepath: str, format: str = 'csv') -> None`
- **Purpose**: Export messages to file
- **Formats**: 'csv', 'json'
- **Async**: No

#### `save_photos(df: pd.DataFrame, output_dir: str) -> None`
- **Purpose**: Save profile photos from messages
- **Requires**: PhotoData column in DataFrame
- **Async**: No

### System Operations

#### `health_check() -> Dict[str, Any]`
- **Purpose**: Check connection and system health
- **Returns**: Health status dictionary
- **Async**: Yes

#### `validate_connection() -> bool`
- **Purpose**: Validate Telegram connection
- **Returns**: True if connected
- **Async**: Yes

#### `get_metrics() -> Dict[str, Any]`
- **Purpose**: Get current session metrics
- **Includes**: Cache size, connection health
- **Async**: Yes

#### `export_metrics(filepath: str = "telegram_metrics.json") -> None`
- **Purpose**: Export metrics to JSON file
- **Async**: Yes

## Context Manager Support

```python
async with TgData() as tg:
    # Automatic cleanup on exit
    messages = await tg.get_messages(limit=100)
```

## Progress Callbacks

Progress callbacks receive three parameters:
```python
def progress_callback(current: int, total: Optional[int], rate: float):
    # current: Messages processed so far
    # total: Expected total (if known)
    # rate: Messages per second
```

## DataFrame Schema

Messages are returned as pandas DataFrames with these columns:
- `MessageId`: Unique message identifier
- `SenderId`: Sender's user ID
- `Name`: Sender's display name
- `Username`: Sender's @username
- `Message`: Message text content
- `Date`: Message timestamp
- `ReplyToId`: ID of replied message (if any)
- `ForwardedFrom`: Original sender ID (if forwarded)
- `PhotoData`: Profile photo bytes (if requested)

## Error Handling

All async methods may raise:
- `ValueError`: Invalid parameters or missing configuration
- `ConnectionError`: Telegram connection issues
- `FloodWaitError`: Rate limit exceeded
- `Exception`: Other Telegram API errors

## Thread Safety

- The library is designed for async/await usage
- Not thread-safe for concurrent operations on same instance
- Use separate instances for parallel processing