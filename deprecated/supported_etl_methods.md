# Supported ETL Methods

This document outlines different ETL approaches for extracting Telegram data, from the simplest CSV-based method to more sophisticated checkpoint strategies.

## Method 1: CSV as Checkpoint (Simplest)

The CSV file itself serves as both the data store and checkpoint. No separate checkpoint file needed.

### Interface

```python
from tgdata import TgData
import pandas as pd
import os

async def extract_to_csv(group_id: int, csv_file: str = "messages.csv"):
    tg = TgData()
    
    # Read last message ID from existing CSV
    last_message_id = 0
    if os.path.exists(csv_file):
        # Read just the last row efficiently
        last_row = pd.read_csv(csv_file).tail(1)
        if not last_row.empty:
            last_message_id = last_row.iloc[0]['id']
            print(f"Resuming from message ID: {last_message_id}")
    
    # Extract messages in batches
    async for batch in tg.get_all_messages(
        group_id=group_id,
        after_id=last_message_id,
        batch_size=1000,
        delay=1.0
    ):
        # Append to CSV (creates file if doesn't exist)
        batch.to_csv(
            csv_file, 
            mode='a', 
            header=not os.path.exists(csv_file),
            index=False
        )
        print(f"Appended {len(batch)} messages to {csv_file}")
```

### Usage

```python
# First run - creates messages.csv
await extract_to_csv(group_id=12345)

# Subsequent runs - automatically resume from last message
await extract_to_csv(group_id=12345)

# Different file for different group
await extract_to_csv(group_id=67890, csv_file="group_67890.csv")
```

### Pros
- Single file contains both data and checkpoint
- Easy to inspect progress (just open CSV)
- Natural resume capability
- No checkpoint synchronization issues

### Cons
- Reading last row from large CSV can be slow
- No metadata (extraction time, errors, etc.)
- Risk of corruption if process dies during write
- Limited to single output format

---

## Method 2: Database Table as Checkpoint

When writing to a database, the table itself tracks progress. No checkpoint.json needed.

### Interface with PostgreSQL

```python
import asyncpg
from tgdata import TgData

class DatabaseETL:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.tg = TgData()
    
    async def extract_to_postgres(self, group_id: int, table_name: str = "messages"):
        async with asyncpg.create_pool(self.db_url) as pool:
            # Ensure table exists
            await pool.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id BIGINT PRIMARY KEY,
                    group_id BIGINT,
                    date TIMESTAMP,
                    sender_id BIGINT,
                    sender_name TEXT,
                    text TEXT,
                    extracted_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Get last message ID from table
            last_id = await pool.fetchval(
                f"SELECT COALESCE(MAX(id), 0) FROM {table_name} WHERE group_id = $1",
                group_id
            )
            print(f"Resuming from message ID: {last_id}")
            
            # Extract messages
            async for batch in self.tg.get_all_messages(
                group_id=group_id,
                after_id=last_id,
                batch_size=1000
            ):
                # Bulk insert
                await pool.copy_records_to_table(
                    table_name,
                    records=[
                        (msg['id'], group_id, msg['date'], msg['sender_id'], 
                         msg['sender_name'], msg['text'])
                        for msg in batch.to_dict('records')
                    ],
                    columns=['id', 'group_id', 'date', 'sender_id', 'sender_name', 'text']
                )
                print(f"Inserted {len(batch)} messages")

# Usage
etl = DatabaseETL("postgresql://user:pass@localhost/telegram")
await etl.extract_to_postgres(group_id=12345)
```

### Interface with MongoDB

```python
from motor.motor_asyncio import AsyncIOMotorClient
from tgdata import TgData

class MongoETL:
    def __init__(self, mongo_url: str, db_name: str):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
        self.tg = TgData()
    
    async def extract_to_mongo(self, group_id: int, collection_name: str = "messages"):
        collection = self.db[collection_name]
        
        # Get last message ID from collection
        last_doc = await collection.find_one(
            {"group_id": group_id},
            sort=[("id", -1)]
        )
        last_id = last_doc['id'] if last_doc else 0
        print(f"Resuming from message ID: {last_id}")
        
        # Extract messages
        async for batch in self.tg.get_all_messages(
            group_id=group_id,
            after_id=last_id,
            batch_size=1000
        ):
            # Prepare documents
            docs = batch.to_dict('records')
            for doc in docs:
                doc['group_id'] = group_id
                doc['_id'] = f"{group_id}_{doc['id']}"  # Composite key
            
            # Bulk insert
            if docs:
                await collection.insert_many(docs, ordered=False)
                print(f"Inserted {len(docs)} messages")

# Usage
etl = MongoETL("mongodb://localhost:27017/", "telegram_data")
await etl.extract_to_mongo(group_id=12345)
```

### Pros
- Natural checkpoint from data itself
- Atomic operations (transactions)
- Can query progress easily
- Built-in deduplication (primary keys)
- Concurrent-safe

### Cons
- Requires database setup
- More complex error handling
- Need indexes for performance
- Tied to specific database schema

---

## Method 3: Using checkpoint.json

Separate checkpoint file provides flexibility and additional metadata.

### When checkpoint.json Makes Sense

1. **Multiple Output Formats**
```python
async def extract_to_multiple_formats(group_id: int):
    tg = TgData()
    
    # Single checkpoint for multiple outputs
    async for batch in tg.get_all_messages(
        group_id=group_id,
        checkpoint_file="checkpoint.json"  # Tracks progress
    ):
        # Write to multiple destinations
        batch.to_csv("messages.csv", mode='a')
        batch.to_parquet(f"messages_{batch.iloc[0]['id']}.parquet")
        await upload_to_s3(batch)
        await insert_to_database(batch)
```

2. **Complex State Tracking**
```json
{
    "last_message_id": 12345,
    "total_processed": 50000,
    "last_run": "2024-01-15T10:30:00Z",
    "extraction_phase": "historical",
    "error_count": 3,
    "rate_limit_hits": 12,
    "groups_completed": [12345, 67890],
    "groups_pending": [11111, 22222]
}
```

3. **Error Recovery**
```python
async def extract_with_error_tracking(group_id: int):
    tg = TgData()
    
    async for batch in tg.get_all_messages(
        group_id=group_id,
        checkpoint_file="checkpoint.json"
    ):
        try:
            process_batch(batch)
        except Exception as e:
            # Checkpoint already saved, can investigate error
            # without losing progress
            log_error(f"Failed at message {batch.iloc[-1]['id']}: {e}")
            raise
```

4. **Metadata and Monitoring**
```python
# Checkpoint can include performance metrics
{
    "last_message_id": 12345,
    "messages_per_second": 145.2,
    "avg_batch_time": 0.89,
    "total_duration_seconds": 3421,
    "api_calls_made": 234
}
```

### Advantages of checkpoint.json

1. **Flexibility**
   - Independent of output format
   - Can change output destination without losing progress
   - Easy to manipulate/reset

2. **Portability**
   - Can move checkpoint between systems
   - Human-readable and editable
   - Version control friendly

3. **Metadata Storage**
   - Track more than just position
   - Performance metrics
   - Error information
   - Multiple group states

4. **Atomic Updates**
   - Write to temp file and rename
   - Less risk of corruption
   - Clear separation of concerns

5. **Development Friendly**
   - Easy to debug
   - Can manually edit to replay
   - Clear checkpoint lifecycle

## Choosing the Right Method

| Scenario | Recommended Method | Why |
|----------|-------------------|-----|
| Simple CSV export | CSV as checkpoint | Simplest, single file |
| Database ETL | DB table as checkpoint | Natural fit, atomic |
| Multiple outputs | checkpoint.json | Flexibility needed |
| Complex workflows | checkpoint.json | Rich state tracking |
| Distributed processing | checkpoint.json + Redis | Coordination required |
| Development/Testing | checkpoint.json | Easy to inspect/modify |

## Best Practices

1. **Start Simple**: Use CSV/DB as checkpoint for basic cases
2. **Add checkpoint.json When**:
   - You need metadata beyond last ID
   - Multiple output destinations
   - Complex error recovery
   - Monitoring/metrics tracking
3. **Consider Hybrid**: Use checkpoint.json for state, but verify against destination
4. **Always Make Resumable**: Any method should support restart

## Example: Migration Path

```python
# Level 1: CSV as checkpoint
await extract_to_csv(group_id)

# Level 2: Need metadata - add checkpoint.json
await tg.get_all_messages(
    group_id=group_id,
    checkpoint_file="checkpoint.json"
)

# Level 3: Multiple outputs - checkpoint.json essential
async for batch in tg.get_all_messages(checkpoint_file="checkpoint.json"):
    await write_to_csv(batch)
    await write_to_database(batch) 
    await publish_to_kafka(batch)
```

The key is choosing the simplest method that meets your needs!