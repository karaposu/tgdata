# Example Usage

## Basic Examples

### 1. Simple Message Retrieval
```python
import asyncio
from tgdata import TgData

async def get_recent_messages():
    # Initialize with defaults
    tg = TgData()
    
    # List available groups
    groups = await tg.list_groups()
    print(f"Found {len(groups)} groups")
    
    # Get messages from first group
    if not groups.empty:
        group_id = groups.iloc[0]['GroupID']
        messages = await tg.get_messages(group_id=group_id, limit=100)
        
        # Display results
        print(f"Retrieved {len(messages)} messages")
        tg.print_messages(messages, limit=10)

# Run
asyncio.run(get_recent_messages())
```

### 2. Message Filtering and Export
```python
async def filter_and_export():
    tg = TgData()
    
    # Get messages from specific date range
    messages = await tg.get_messages(
        group_id=12345,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        limit=1000
    )
    
    # Filter by keyword
    important = tg.filter_messages(messages, keyword="important")
    
    # Export to CSV
    tg.export_messages(important, "important_messages.csv", format="csv")
    
    # Export to JSON
    tg.export_messages(important, "important_messages.json", format="json")

asyncio.run(filter_and_export())
```

## Advanced Examples

### 3. Progress Tracking with Custom Callback
```python
async def download_with_progress():
    tg = TgData()
    
    # Custom progress callback
    def show_progress(current, total, rate):
        if total:
            percent = (current / total) * 100
            bar_length = 40
            filled = int(bar_length * current / total)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f'\r[{bar}] {percent:.1f}% - {rate:.1f} msg/s', end='')
        else:
            print(f'\rProcessed {current} messages at {rate:.1f} msg/s', end='')
    
    # Download with progress
    messages = await tg.get_messages(
        group_id=12345,
        limit=5000,
        progress_callback=show_progress
    )
    print("\nDownload complete!")

asyncio.run(download_with_progress())
```

### 4. Using Connection Pooling
```python
async def high_performance_crawl():
    # Enable connection pooling for better performance
    tg = TgData(
        connection_pool_size=3,  # Use 3 connections
        enable_deduplication=True,
        log_file="crawler.log"
    )
    
    # Process multiple groups efficiently
    group_ids = [12345, 67890, 11111]
    all_messages = pd.DataFrame()
    
    for group_id in group_ids:
        try:
            messages = await tg.get_messages(
                group_id=group_id,
                limit=1000,
                with_progress=True
            )
            all_messages = pd.concat([all_messages, messages])
            
        except FloodWaitError as e:
            print(f"Rate limited, waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
    
    print(f"Total messages collected: {len(all_messages)}")

asyncio.run(high_performance_crawl())
```

## Integration Examples

### 5. Custom Message Tracker (Redis)
```python
import redis
from tgdata import MessageTrackerInterface, MessageInfo, TgData

class RedisTracker(MessageTrackerInterface):
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        
    async def is_processed(self, message_id: int, group_id: int) -> bool:
        key = f"telegram:processed:{group_id}:{message_id}"
        return bool(self.redis.exists(key))
    
    async def mark_processed(self, message_info: MessageInfo) -> None:
        key = f"telegram:processed:{message_info.group_id}:{message_info.message_id}"
        self.redis.setex(key, 86400 * 30, "1")  # 30 days TTL
    
    async def mark_batch_processed(self, messages: List[MessageInfo]) -> None:
        pipe = self.redis.pipeline()
        for msg in messages:
            key = f"telegram:processed:{msg.group_id}:{msg.message_id}"
            pipe.setex(key, 86400 * 30, "1")
        pipe.execute()
    
    async def get_unprocessed(self, messages: List[Dict], group_id: int) -> List[Dict]:
        unprocessed = []
        for msg in messages:
            if not await self.is_processed(msg['MessageId'], group_id):
                unprocessed.append(msg)
        return unprocessed

# Use custom tracker
async def crawl_with_redis():
    tg = TgData(
        tracker=RedisTracker(),
        enable_deduplication=True
    )
    
    # Messages will be deduplicated using Redis
    messages = await tg.get_messages(group_id=12345)

asyncio.run(crawl_with_redis())
```

### 6. Incremental Updates
```python
async def incremental_sync():
    tg = TgData(
        tracker=SQLiteTracker("messages.db")
    )
    
    group_id = 12345
    
    # First run - get initial messages
    print("Initial sync...")
    messages = await tg.get_messages(
        group_id=group_id,
        limit=1000,
        with_progress=True
    )
    
    if not messages.empty:
        last_message_id = messages['MessageId'].max()
        
        # Save last ID for next run
        with open('last_sync.txt', 'w') as f:
            f.write(str(last_message_id))
        
        # Later runs - get only new messages
        print("\nIncremental sync...")
        new_messages = await tg.get_messages(
            group_id=group_id,
            after_id=last_message_id
        )
        
        print(f"Found {len(new_messages)} new messages")

asyncio.run(incremental_sync())
```

## Real-World Scenarios

### 7. Monitoring Keywords
```python
async def keyword_monitor():
    tg = TgData()
    
    keywords = ["urgent", "alert", "important", "breaking"]
    monitored_groups = [12345, 67890]
    
    while True:
        for group_id in monitored_groups:
            try:
                # Get messages from last hour
                messages = await tg.get_messages(
                    group_id=group_id,
                    start_date=datetime.now() - timedelta(hours=1)
                )
                
                # Check each keyword
                for keyword in keywords:
                    alerts = tg.filter_messages(messages, keyword=keyword)
                    
                    if not alerts.empty:
                        print(f"\n🚨 Found {len(alerts)} messages with '{keyword}' in group {group_id}")
                        tg.print_messages(alerts)
                        
                        # Send notification (implement your notification logic)
                        # send_email_alert(alerts, keyword)
                        
            except Exception as e:
                print(f"Error monitoring group {group_id}: {e}")
        
        # Wait before next check
        await asyncio.sleep(300)  # 5 minutes

# Run as background task
# asyncio.run(keyword_monitor())
```

### 8. Daily Report Generation
```python
async def generate_daily_report():
    tg = TgData()
    
    # Configuration
    report_groups = {
        12345: "Customer Support",
        67890: "Sales Team",
        11111: "Development"
    }
    
    # Collect data
    report_data = {}
    
    for group_id, group_name in report_groups.items():
        try:
            # Get yesterday's messages
            yesterday = datetime.now() - timedelta(days=1)
            messages = await tg.get_messages(
                group_id=group_id,
                start_date=yesterday.replace(hour=0, minute=0),
                end_date=yesterday.replace(hour=23, minute=59)
            )
            
            # Calculate statistics
            stats = tg.get_statistics(messages)
            
            report_data[group_name] = {
                'total_messages': stats['total_messages'],
                'unique_senders': stats['unique_senders'],
                'top_contributors': stats['top_senders'][:3],
                'busiest_hour': messages.groupby(messages['Date'].dt.hour).size().idxmax()
            }
            
        except Exception as e:
            report_data[group_name] = {'error': str(e)}
    
    # Generate report
    report = f"Daily Telegram Report - {yesterday.date()}\n"
    report += "=" * 50 + "\n\n"
    
    for group_name, data in report_data.items():
        report += f"{group_name}:\n"
        if 'error' in data:
            report += f"  Error: {data['error']}\n"
        else:
            report += f"  Total Messages: {data['total_messages']}\n"
            report += f"  Active Users: {data['unique_senders']}\n"
            report += f"  Busiest Hour: {data['busiest_hour']}:00\n"
            report += f"  Top Contributors:\n"
            for contributor in data['top_contributors']:
                report += f"    - {contributor['name']}: {contributor['message_count']} messages\n"
        report += "\n"
    
    # Save report
    with open(f"daily_report_{yesterday.date()}.txt", 'w') as f:
        f.write(report)
    
    print("Daily report generated!")
    
    # Optionally email the report
    # send_email(report, recipients=['team@example.com'])

asyncio.run(generate_daily_report())
```

### 9. Archive with Compression
```python
import gzip
import json

async def archive_with_compression():
    tg = TgData()
    
    # Get all messages from a group
    messages = await tg.get_messages(
        group_id=12345,
        with_progress=True
    )
    
    # Convert to JSON and compress
    json_data = messages.to_json(orient='records', date_format='iso')
    compressed = gzip.compress(json_data.encode('utf-8'))
    
    # Save compressed archive
    archive_name = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.gz"
    with open(archive_name, 'wb') as f:
        f.write(compressed)
    
    # Stats
    original_size = len(json_data.encode('utf-8'))
    compressed_size = len(compressed)
    compression_ratio = (1 - compressed_size / original_size) * 100
    
    print(f"Archive created: {archive_name}")
    print(f"Original size: {original_size / 1024 / 1024:.2f} MB")
    print(f"Compressed size: {compressed_size / 1024 / 1024:.2f} MB")
    print(f"Compression ratio: {compression_ratio:.1f}%")

asyncio.run(archive_with_compression())
```

### 10. Error Handling and Resilience
```python
async def resilient_crawler():
    tg = TgData(
        connection_pool_size=2,
        tracker=InMemoryTracker(max_size=10000)
    )
    
    groups_to_process = [12345, 67890, 11111, 22222]
    results = {}
    
    for group_id in groups_to_process:
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"Processing group {group_id}...")
                
                # Set timeout for the operation
                messages = await asyncio.wait_for(
                    tg.get_messages(
                        group_id=group_id,
                        limit=1000,
                        with_progress=True
                    ),
                    timeout=300  # 5 minutes timeout
                )
                
                results[group_id] = {
                    'status': 'success',
                    'count': len(messages),
                    'data': messages
                }
                break  # Success, exit retry loop
                
            except asyncio.TimeoutError:
                print(f"Timeout processing group {group_id}")
                results[group_id] = {'status': 'timeout', 'retry': retry_count}
                
            except FloodWaitError as e:
                print(f"Rate limited for {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                retry_count += 1
                
            except Exception as e:
                print(f"Error processing group {group_id}: {e}")
                results[group_id] = {'status': 'error', 'error': str(e)}
                retry_count += 1
                
                if retry_count < max_retries:
                    await asyncio.sleep(5 * retry_count)  # Exponential backoff
    
    # Summary
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    print(f"\nProcessed {successful}/{len(groups_to_process)} groups successfully")
    
    # Save results
    summary_df = pd.DataFrame([
        {
            'group_id': gid,
            'status': data['status'],
            'message_count': data.get('count', 0)
        }
        for gid, data in results.items()
    ])
    summary_df.to_csv('processing_summary.csv', index=False)

asyncio.run(resilient_crawler())
```

## Testing and Development

### 11. Unit Test Example
```python
import pytest
from unittest.mock import Mock, AsyncMock

async def test_message_filtering():
    # Create test data
    test_messages = pd.DataFrame({
        'MessageId': [1, 2, 3],
        'SenderId': [100, 200, 100],
        'Message': ['Hello world', 'Important message', 'Another message'],
        'Date': [datetime.now() for _ in range(3)]
    })
    
    # Initialize TgData
    tg = TgData()
    
    # Test filtering
    filtered = tg.filter_messages(test_messages, keyword='Important')
    assert len(filtered) == 1
    assert filtered.iloc[0]['MessageId'] == 2
    
    # Test sender filtering
    sender_filtered = tg.filter_messages(test_messages, sender_id=100)
    assert len(sender_filtered) == 2

# Run with pytest
# pytest -v test_tgdata.py
```

## Best Practices

1. **Always use async context managers for cleanup**
```python
async with TgData() as tg:
    messages = await tg.get_messages(group_id=12345)
```

2. **Handle rate limits gracefully**
```python
try:
    messages = await tg.get_messages(group_id=12345)
except FloodWaitError as e:
    await asyncio.sleep(e.seconds)
```

3. **Use appropriate limits for large groups**
```python
# Don't try to fetch millions at once
messages = await tg.get_messages(group_id=large_group, limit=10000)
```

4. **Implement proper logging**
```python
tg = TgData(log_file="telegram_crawler.log")
```

5. **Use deduplication for repeated crawls**
```python
tg = TgData(
    tracker=SQLiteTracker("messages.db"),
    enable_deduplication=True
)
```