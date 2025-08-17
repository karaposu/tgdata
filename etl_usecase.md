# ETL Use Case: Using tgdata for Data Extraction

## Overview

`tgdata` is designed specifically for the **Extract** phase of ETL pipelines, enabling reliable extraction of Telegram group/channel messages for data warehousing, analytics, and archival purposes.

## Core ETL Patterns

### 1. Initial Historical Load (One-time Backfill)

When first setting up your data pipeline, you need to extract all historical messages:

```python
import asyncio
from tgdata import TgData
from datetime import datetime, timedelta

async def initial_historical_load():
    """One-time extraction of all historical messages"""
    tg = TgData("config.ini")
    
    # Option 1: Get ALL messages
    all_messages = await tg.get_messages(
        group_id=YOUR_GROUP_ID,
        limit=None  # No limit, get everything
    )
    
    # Option 2: Get messages from specific date range
    historical_messages = await tg.get_messages(
        group_id=YOUR_GROUP_ID,
        start_date=datetime(2023, 1, 1),  # From Jan 1, 2023
        end_date=datetime.now()  # Until now
    )
    
    # Option 3: Batch processing for very large groups with rate limit protection
    total_messages = await tg.get_message_count(group_id=YOUR_GROUP_ID)
    
    async def process_batch(batch_df, batch_info):
        # Process each batch (e.g., write to data lake)
        print(f"Processing batch {batch_info['batch_num']}: {len(batch_df)} messages")
        write_to_data_lake(batch_df)
    
    await tg.get_messages(
        group_id=YOUR_GROUP_ID,
        batch_size=500,  # Process in chunks of 500
        batch_callback=process_batch,
        batch_delay=1.5,  # Wait 1.5 seconds between batches to avoid rate limits
        rate_limit_strategy='exponential'  # Use exponential backoff with jitter if rate limited
    )
    
    await tg.close()

# Run the historical load
asyncio.run(initial_historical_load())
```

### 2. Incremental Updates (Regular ETL)

After the initial load, you need regular incremental updates. **The polling/scheduling should be handled by your orchestration tool** (Airflow, cron, Prefect, etc.), NOT by the library:

```python
async def incremental_extract():
    """Regular incremental extraction - run hourly/daily via scheduler"""
    tg = TgData("config.ini")
    
    # Load checkpoint from your metadata store
    last_processed_id = load_from_metadata_store("telegram_last_message_id")
    
    # Extract only new messages since last run
    new_messages = await tg.get_messages(
        group_id=YOUR_GROUP_ID,
        after_id=last_processed_id  # Only messages after this ID
    )
    
    if not new_messages.empty:
        # Transform and load to your data warehouse
        transformed_data = transform_messages(new_messages)
        load_to_warehouse(transformed_data)
        
        # Update checkpoint for next run
        max_id = new_messages['MessageId'].max()
        save_to_metadata_store("telegram_last_message_id", max_id)
        
        print(f"Processed {len(new_messages)} new messages")
    else:
        print("No new messages")
    
    await tg.close()
```

## Integration with ETL Orchestrators

### Apache Airflow Example

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import asyncio

def extract_telegram_messages():
    """Wrapper for async extraction"""
    asyncio.run(incremental_extract())

dag = DAG(
    'telegram_etl',
    default_args={'retries': 2},
    schedule_interval='@hourly',  # Run every hour
    start_date=datetime(2024, 1, 1)
)

extract_task = PythonOperator(
    task_id='extract_telegram_messages',
    python_callable=extract_telegram_messages,
    dag=dag
)

transform_task = PythonOperator(
    task_id='transform_messages',
    python_callable=transform_data,
    dag=dag
)

load_task = PythonOperator(
    task_id='load_to_warehouse',
    python_callable=load_to_warehouse,
    dag=dag
)

extract_task >> transform_task >> load_task
```

### Cron Job Example

```bash
# Run every hour at minute 5
5 * * * * /usr/bin/python3 /path/to/telegram_etl.py >> /var/log/telegram_etl.log 2>&1

# Run daily at 2 AM
0 2 * * * /usr/bin/python3 /path/to/telegram_daily_extract.py
```

## Key Differences: Historical vs Incremental

### Historical Data Extraction
- **Purpose**: One-time backfill or recovery
- **Method**: `get_messages()` without `after_id`
- **Characteristics**:
  - Large volume (thousands/millions of messages)
  - Can use date ranges for filtering
  - May need batch processing for memory efficiency
  - Typically run once or rarely
  - Very reliable - gets all messages

### Incremental Data Extraction  
- **Purpose**: Regular updates (hourly/daily)
- **Method**: `get_messages()` with `after_id`
- **Characteristics**:
  - Smaller volume (dozens to hundreds of messages)
  - Uses message ID checkpoint
  - Stateless - each run is independent
  - Run frequently via scheduler
  - Reliable for ETL intervals (hourly/daily)

## Why Polling Should Be External

The library intentionally does NOT handle scheduling/polling internally for ETL because:

1. **Separation of Concerns**
   - Data extraction is the library's job
   - Scheduling is the orchestrator's job

2. **Flexibility**
   - Different teams use different schedulers (Airflow, cron, Prefect, Dagster)
   - Custom retry logic and error handling
   - Integration with existing data pipelines

3. **Reliability**
   - Orchestrators provide monitoring, alerting, retries
   - Centralized scheduling and dependency management
   - Better resource management

4. **Stateless Design**
   - Each extraction run is independent
   - No long-running processes
   - Easy to debug and restart

## Rate Limiting and Large-Scale Extraction

When extracting large volumes of messages, Telegram's rate limits become a critical consideration. The library provides several mechanisms to handle this:

### Rate Limit Protection Parameters

| Parameter | Description | Recommended Value | Use Case |
|-----------|-------------|-------------------|----------|
| `batch_size` | Messages per batch | 200-500 | Large historical extracts |
| `batch_delay` | Seconds between batches | 1.0-3.0 | Prevent hitting rate limits |
| `rate_limit_strategy` | How to handle rate limits | 'exponential' | Production ETL |

### Example: Production-Safe Historical Extract

```python
async def safe_historical_extract():
    """Extract large message history with rate limit protection"""
    tg = TgData("config.ini")
    
    # For groups with 100k+ messages
    messages_processed = 0
    
    async def process_and_save_batch(batch_df, batch_info):
        """Process each batch with progress tracking"""
        nonlocal messages_processed
        
        # Save to staging table first
        batch_df.to_sql(
            f"telegram_staging_{batch_info['batch_num']}",
            staging_connection,
            if_exists='replace'
        )
        
        messages_processed += len(batch_df)
        
        # Log progress
        logger.info(f"Batch {batch_info['batch_num']}: {messages_processed} total messages processed")
        
        # If this is the final batch, merge all staging tables
        if batch_info.get('is_final'):
            merge_staging_tables()
    
    try:
        await tg.get_messages(
            group_id=LARGE_GROUP_ID,
            batch_size=300,  # Smaller batches for large groups
            batch_delay=2.0,  # 2 second delay between batches
            rate_limit_strategy='exponential',  # Exponential backoff with jitter
            batch_callback=process_and_save_batch,
            with_progress=True  # Show progress
        )
    except Exception as e:
        logger.error(f"Extract failed after {messages_processed} messages: {e}")
        # Can resume from messages_processed using after_id
    finally:
        await tg.close()
```

### Handling Rate Limit Errors

The library automatically handles `FloodWaitError` from Telegram:

1. **'wait' strategy** (default): Waits exactly the time Telegram specifies
2. **'exponential' strategy**: Adds 0-30% random jitter to prevent thundering herd

```python
# Conservative approach for critical ETL
await tg.get_messages(
    group_id=GROUP_ID,
    batch_size=200,  # Small batches
    batch_delay=3.0,  # Long delay
    rate_limit_strategy='exponential'
)

# Aggressive approach for time-sensitive extraction
await tg.get_messages(
    group_id=GROUP_ID,
    batch_size=1000,  # Large batches
    batch_delay=0.5,  # Short delay
    rate_limit_strategy='wait'  # Exact wait times
)
```

## Best Practices for ETL

### 1. Checkpoint Management

```python
class TelegramETL:
    def __init__(self, metadata_db):
        self.metadata_db = metadata_db
        self.tg = TgData("config.ini")
    
    def get_checkpoint(self, group_id):
        """Get last processed message ID from metadata"""
        return self.metadata_db.query(
            "SELECT last_message_id FROM etl_checkpoints WHERE group_id = ?",
            group_id
        )
    
    def save_checkpoint(self, group_id, message_id):
        """Save checkpoint for next run"""
        self.metadata_db.execute(
            "UPDATE etl_checkpoints SET last_message_id = ?, updated_at = NOW() WHERE group_id = ?",
            message_id, group_id
        )
```

### 2. Error Handling

```python
async def robust_extract():
    """ETL with proper error handling"""
    max_retries = 3
    retry_delay = 60  # seconds
    
    for attempt in range(max_retries):
        try:
            tg = TgData("config.ini")
            messages = await tg.get_messages(
                group_id=GROUP_ID,
                after_id=last_checkpoint
            )
            await tg.close()
            return messages
            
        except Exception as e:
            logger.error(f"Extraction failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                raise
```

### 3. Data Quality Checks

```python
async def extract_with_validation():
    """Extract with data quality checks"""
    new_messages = await tg.get_messages(
        group_id=GROUP_ID,
        after_id=last_checkpoint
    )
    
    if not new_messages.empty:
        # Check for gaps in message IDs
        message_ids = sorted(new_messages['MessageId'].tolist())
        expected_count = message_ids[-1] - message_ids[0] + 1
        
        if len(message_ids) < expected_count * 0.95:  # Allow 5% gap
            logger.warning(f"Potential data loss: expected ~{expected_count}, got {len(message_ids)}")
        
        # Check for duplicate IDs
        if len(message_ids) != len(set(message_ids)):
            logger.error("Duplicate message IDs detected")
```

## Complete ETL Pipeline Example

```python
"""
telegram_etl.py - Complete ETL pipeline for Telegram messages
Run via cron or orchestrator
"""

import asyncio
import logging
from datetime import datetime
from tgdata import TgData
import pandas as pd
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

class TelegramETLPipeline:
    def __init__(self, config_path, warehouse_conn_string):
        self.config_path = config_path
        self.warehouse = create_engine(warehouse_conn_string)
        
    async def extract(self, group_id, after_id=0):
        """Extract phase"""
        tg = TgData(self.config_path)
        try:
            messages = await tg.get_messages(
                group_id=group_id,
                after_id=after_id
            )
            return messages
        finally:
            await tg.close()
    
    def transform(self, messages_df):
        """Transform phase"""
        if messages_df.empty:
            return messages_df
            
        # Add derived columns
        messages_df['MessageLength'] = messages_df['Message'].str.len()
        messages_df['HasMedia'] = messages_df['MediaType'].notna()
        messages_df['ExtractedAt'] = datetime.now()
        
        # Clean text
        messages_df['MessageCleaned'] = messages_df['Message'].str.replace(r'[^\w\s]', '', regex=True)
        
        return messages_df
    
    def load(self, messages_df, table_name='telegram_messages'):
        """Load phase"""
        if messages_df.empty:
            return
            
        # Upsert to warehouse (handles duplicates)
        messages_df.to_sql(
            table_name,
            self.warehouse,
            if_exists='append',
            index=False,
            method='multi'
        )
        
        logger.info(f"Loaded {len(messages_df)} messages to {table_name}")
    
    def get_checkpoint(self, group_id):
        """Get last processed message ID"""
        query = f"""
            SELECT MAX(MessageId) as last_id 
            FROM telegram_messages 
            WHERE GroupId = {group_id}
        """
        result = pd.read_sql(query, self.warehouse)
        return result['last_id'].iloc[0] if not result.empty else 0
    
    async def run(self, group_id):
        """Run complete ETL pipeline"""
        logger.info(f"Starting ETL for group {group_id}")
        
        # Get checkpoint
        last_id = self.get_checkpoint(group_id)
        logger.info(f"Last processed message ID: {last_id}")
        
        # Extract
        messages = await self.extract(group_id, after_id=last_id)
        logger.info(f"Extracted {len(messages)} new messages")
        
        if not messages.empty:
            # Transform
            transformed = self.transform(messages)
            
            # Load
            self.load(transformed)
            
            logger.info(f"ETL completed. New checkpoint: {messages['MessageId'].max()}")
        else:
            logger.info("No new messages to process")

# Main execution
async def main():
    pipeline = TelegramETLPipeline(
        config_path="config.ini",
        warehouse_conn_string="postgresql://user:pass@localhost/warehouse"
    )
    
    # Process multiple groups
    group_ids = [123456789, 987654321, 456789123]
    
    for group_id in group_ids:
        try:
            await pipeline.run(group_id)
        except Exception as e:
            logger.error(f"Failed to process group {group_id}: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

## Scheduling and Batch Size Recommendations

### By Group Size and Activity

| Group Type | Message Volume | Batch Size | Batch Delay | Schedule | Rate Strategy |
|------------|---------------|------------|-------------|----------|---------------|
| Very Large | 10k+ msgs/day | 200-300 | 2-3s | Every 15 min | exponential |
| Large | 1k-10k msgs/day | 500 | 1.5s | Hourly | exponential |
| Medium | 100-1k msgs/day | 1000 | 1s | Every 4 hours | wait |
| Small | <100 msgs/day | No batching | 0s | Daily | wait |

### By Use Case

| Use Case | Frequency | Method | Batch Config | Notes |
|----------|-----------|---------|--------------|-------|
| High-volume ETL | Every 15 min | `after_id` | size=300, delay=2s | Prevent rate limits |
| Normal ETL | Hourly | `after_id` | size=500, delay=1s | Good balance |
| Low-volume ETL | Daily | `after_id` | No batching needed | Simple extraction |
| Historical backfill | One-time | Date range | size=200, delay=3s | Conservative approach |
| Archival | Weekly/Monthly | Date range | size=1000, delay=0.5s | Can be aggressive |

## Limitations and Considerations

1. **Message Order**: Telegram message IDs are globally unique, not sequential per group
2. **Rate Limits**: 
   - Telegram enforces API rate limits (`FloodWaitError`)
   - Use `batch_delay` to proactively avoid limits
   - Use `rate_limit_strategy='exponential'` for production
3. **Message Edits**: Edited messages maintain same ID - consider tracking edit timestamps
4. **Deleted Messages**: Won't be captured - consider soft deletes in warehouse
5. **Media Files**: Large media files should be stored separately (S3, blob storage)
6. **Memory Usage**: Large batches consume more memory - balance batch size with available RAM
7. **Resume Capability**: Always track last processed message ID for resumable extracts

## Conclusion

`tgdata` provides the extraction capabilities needed for production ETL pipelines. By keeping scheduling external and focusing on reliable data extraction, it integrates seamlessly with existing data infrastructure while maintaining simplicity and reliability.

The key insight: **Let the library do extraction, let your orchestrator do scheduling.**