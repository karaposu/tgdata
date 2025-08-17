# ETL Batch Processing Guide

## Overview

This guide shows how to use `TgData` methods for ETL scenarios, from simple file-based checkpointing to custom database implementations. The library provides a clean API that stays focused on Telegram operations while allowing flexible checkpoint strategies.

## Core ETL Methods

### get_all_messages()
```python
async def get_all_messages(
    group_id: int,
    checkpoint_file: Optional[str] = None,
    after_id: int = 0,
    batch_size: int = 1000,
    delay: float = 0,
    rate_limit_aware: bool = False,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    progress_callback: Optional[Callable] = None
) -> AsyncIterator[pd.DataFrame]
```

### get_messages() with after_id
```python
# Updated: Use get_messages with after_id for incremental extraction
async def get_messages(
    group_id: int,
    after_id: int = 0,  # For incremental extraction
    limit: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    include_profile_photos: bool = False,
    with_progress: bool = False,
    progress_callback: Optional[Callable] = None
) -> pd.DataFrame
```

## Checkpoint File Format

When using `checkpoint_file`, the library uses this JSON format:
```json
{
    "last_message_id": 12345,
    "total_processed": 5000,
    "last_updated": "2024-01-15T10:30:00Z",
    "group_id": 12345
}
```

## Implementation Levels

### Level 1: Simple File-Based Checkpointing

**Use Case**: Small to medium datasets, single-server setups

#### Historical Data Extraction
```python
from tgdata import TgData
import asyncio

async def simple_backfill():
    tg = TgData()
    
    # Extract with automatic file checkpointing
    async for batch in tg.get_all_messages(
        group_id=12345,
        checkpoint_file="checkpoint.json",
        batch_size=500,
        delay=2.0,  # Fixed 2-second delay
        start_date=datetime(2024, 1, 1),
        progress_callback=lambda cur, tot, rate: print(f"{cur} messages at {rate:.1f} msg/s")
    ):
        # Process each batch
        save_to_csv(batch, "messages.csv", append=True)
```

#### Incremental Data Extraction
```python
async def simple_incremental():
    tg = TgData()
    
    # Get new messages since last checkpoint
    new_messages = await tg.get_messages(
        group_id=12345,
        checkpoint_file="checkpoint.json"
    )
    
    if not new_messages.empty:
        print(f"Found {len(new_messages)} new messages")
        process_messages(new_messages)
```

**Cron Setup**:
```bash
# Historical: Run every 5 minutes until complete
*/5 * * * * flock -n /tmp/backfill.lock python3 backfill.py

# Incremental: Daily at 2 AM
0 2 * * * python3 incremental.py
```

---

### Level 2: Custom Database Checkpointing

**Use Case**: Multi-server environments, better tracking and recovery

#### Historical Data Extraction with Database
```python
class DatabaseETL:
    def __init__(self):
        self.tg = TgData()
        self.db = PostgresPool()
    
    async def backfill_with_db_checkpoint(self, group_id: int):
        # Load checkpoint from database
        checkpoint = await self.db.fetchone(
            "SELECT last_message_id, total_processed FROM etl_checkpoints WHERE group_id = $1",
            group_id
        )
        start_id = checkpoint['last_message_id'] if checkpoint else 0
        total_processed = checkpoint['total_processed'] if checkpoint else 0
        
        # Use TgData with custom checkpoint
        async for batch in self.tg.get_all_messages(
            group_id=group_id,
            after_id=start_id,  # Use database checkpoint
            batch_size=1000,
            delay=1.0,
            rate_limit_aware=True,  # Auto-adjust delays
            progress_callback=self.report_progress
        ):
            # Process batch
            transformed = await self.transform(batch)
            await self.load_to_warehouse(transformed)
            
            # Update checkpoint in database (transaction-safe)
            async with self.db.transaction():
                await self.db.execute("""
                    INSERT INTO etl_checkpoints 
                    (group_id, last_message_id, total_processed, last_updated)
                    VALUES ($1, $2, $3, NOW())
                    ON CONFLICT (group_id) DO UPDATE SET
                        last_message_id = $2,
                        total_processed = etl_checkpoints.total_processed + $3,
                        last_updated = NOW()
                """, group_id, batch.iloc[-1]['id'], len(batch))
```

#### Incremental with Database
```python
async def incremental_with_db(self, group_id: int):
    # Get last position from database
    last_id = await self.db.fetchval(
        "SELECT last_message_id FROM etl_checkpoints WHERE group_id = $1",
        group_id
    ) or 0
    
    # Fetch new messages
    new_messages = await self.tg.get_messages(
        group_id=group_id,
        after_id=last_id,  # Use database checkpoint
        batch_mode=False   # Get all at once for incremental
    )
    
    if not new_messages.empty:
        # Process and update checkpoint
        await self.process_messages(new_messages)
        await self.db.execute(
            "UPDATE etl_checkpoints SET last_message_id = $1 WHERE group_id = $2",
            new_messages.iloc[-1]['id'],
            group_id
        )
```

**Database Schema**:
```sql
CREATE TABLE etl_checkpoints (
    group_id BIGINT PRIMARY KEY,
    last_message_id BIGINT NOT NULL,
    total_processed BIGINT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_checkpoints_updated ON etl_checkpoints(last_updated);
```

---

### Level 3: Distributed Processing with Redis

**Use Case**: High-scale, multiple workers, rate limit coordination

#### Distributed Historical Extraction
```python
class DistributedETL:
    def __init__(self):
        self.tg = TgData()
        self.redis = Redis()
        self.worker_id = os.environ.get('WORKER_ID', '1')
    
    async def distributed_backfill(self, group_id: int):
        # Distributed locking to prevent duplicate work
        lock_key = f"etl:lock:{group_id}"
        checkpoint_key = f"etl:checkpoint:{group_id}"
        
        async with self.redis.lock(lock_key, timeout=3600):
            # Get checkpoint from Redis
            checkpoint = await self.redis.hgetall(checkpoint_key)
            start_id = int(checkpoint.get('last_id', 0))
            
            # Extract with rate limit coordination
            async for batch in self.tg.get_all_messages(
                group_id=group_id,
                after_id=start_id,
                batch_size=2000,
                rate_limit_aware=True,
                progress_callback=lambda c, t, r: self.publish_progress(group_id, c, t, r)
            ):
                # Check global rate limit
                if await self.is_rate_limited():
                    await asyncio.sleep(await self.get_backoff_time())
                
                # Process batch
                await self.process_batch(batch)
                
                # Update checkpoint in Redis
                await self.redis.hset(checkpoint_key, mapping={
                    'last_id': batch.iloc[-1]['id'],
                    'worker': self.worker_id,
                    'timestamp': time.time()
                })
    
    async def is_rate_limited(self):
        tokens = await self.redis.get("rate_limit:tokens")
        return int(tokens or 0) < 5
```

---

### Level 4: Advanced Patterns

#### Pattern 1: Adaptive Rate Limiting
```python
async def adaptive_extraction(group_id: int):
    tg = TgData()
    current_delay = 1.0
    
    async for batch in tg.get_all_messages(
        group_id=group_id,
        checkpoint_file="checkpoint.json",
        batch_size=1000,
        delay=current_delay,
        rate_limit_aware=True
    ):
        # Adjust delay based on response time
        if batch.metadata.get('rate_limit_remaining', 100) < 10:
            current_delay = min(current_delay * 2, 30)  # Exponential backoff
        else:
            current_delay = max(current_delay * 0.9, 1)  # Gradual speedup
        
        process_batch(batch)
```

#### Pattern 2: Batch Mode for Incremental
```python
async def incremental_large_volume(group_id: int):
    tg = TgData()
    
    # Use batch mode for high-volume incremental
    async for batch in await tg.get_messages(
        group_id=group_id,
        checkpoint_file="checkpoint.json",
        batch_mode=True,  # Return iterator
        batch_size=5000,
        use_adaptive_sizing=True  # Learn from patterns
    ):
        # Stream processing
        await stream_to_kafka(batch)
```

#### Pattern 3: Progress Monitoring
```python
class ProgressMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.last_update = 0
    
    def progress_callback(self, current: int, total: Optional[int], rate: float):
        now = time.time()
        if now - self.last_update > 10:  # Update every 10 seconds
            elapsed = now - self.start_time
            if total:
                eta = (total - current) / rate if rate > 0 else 0
                print(f"Progress: {current:,}/{total:,} ({current/total*100:.1f}%) "
                      f"Rate: {rate:.1f} msg/s, ETA: {eta/60:.1f} min")
            else:
                print(f"Progress: {current:,} messages, Rate: {rate:.1f} msg/s")
            self.last_update = now

# Use with extraction
monitor = ProgressMonitor()
async for batch in tg.get_all_messages(
    group_id=12345,
    checkpoint_file="checkpoint.json",
    progress_callback=monitor.progress_callback
):
    process_batch(batch)
```

## Best Practices

### 1. Start Simple
```python
# Begin with file checkpointing
messages = await tg.get_messages(
    group_id=12345,
    checkpoint_file="checkpoint.json"
)
```

### 2. Add Complexity Gradually
```python
# Move to custom checkpointing when needed
checkpoint = get_checkpoint_from_db()
after_id = checkpoint['last_message_id'] if checkpoint else 0

messages = await tg.get_messages(
    group_id=12345,
    after_id=after_id
)

if not messages.empty:
    update_checkpoint_in_db(messages.iloc[-1]['id'])
```

### 3. Handle Failures
```python
try:
    async for batch in tg.get_all_messages(group_id=12345):
        process_batch(batch)
except Exception as e:
    logger.error(f"Extraction failed: {e}")
    # Can resume from checkpoint
```

### 4. Monitor Everything
```python
def detailed_progress(current, total, rate):
    metrics.gauge('etl.progress', current)
    metrics.gauge('etl.rate', rate)
    if total:
        metrics.gauge('etl.completion', current / total * 100)

async for batch in tg.get_all_messages(
    group_id=12345,
    progress_callback=detailed_progress
):
    process_batch(batch)
```

## Choosing the Right Approach

| Scenario | Data Volume | Infrastructure | Approach |
|----------|------------|----------------|----------|
| POC/Testing | <100K | Single server | File checkpoint |
| Small production | 100K-1M | Database available | Custom DB checkpoint |
| Large scale | 1M-10M | Redis/distributed | Distributed checkpoint |
| Incremental daily | <10K/day | Any | Simple file checkpoint |
| Incremental real-time | >10K/day | Redis | Streaming with Redis |

## Migration Path

```python
# Start with simple file checkpoint
tg.get_all_messages(group_id=12345, checkpoint_file="checkpoint.json")
    ↓
# Add custom database checkpoint
checkpoint = get_checkpoint_from_db()
after_id = checkpoint['last_message_id'] if checkpoint else 0
tg.get_all_messages(group_id=12345, after_id=after_id)
    ↓
# Scale to distributed
checkpoint = get_checkpoint_from_redis()
after_id = checkpoint['last_message_id'] if checkpoint else 0
tg.get_all_messages(group_id=12345, after_id=after_id)
```

The key is keeping the TgData API simple while allowing flexible checkpoint strategies!