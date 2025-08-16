# Integration Points

## Overview

The Telegram Group Message Crawler is designed with multiple integration points to fit into various architectures and workflows. This document outlines where and how you can integrate the library with your systems.

## 1. Message Tracker Integration

### Custom Storage Backends

The `MessageTrackerInterface` allows you to integrate any storage system:

```python
from tgdata import MessageTrackerInterface, MessageInfo

class RedisTracker(MessageTrackerInterface):
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def is_processed(self, message_id: int, group_id: int) -> bool:
        key = f"msg:{group_id}:{message_id}"
        return await self.redis.exists(key)
    
    async def mark_processed(self, message_info: MessageInfo) -> None:
        key = f"msg:{message_info.group_id}:{message_info.message_id}"
        await self.redis.set(key, "1", ex=86400 * 30)  # 30 days TTL
```

**Integration Options:**
- Redis/Memcached for distributed caching
- PostgreSQL/MySQL for persistent storage
- MongoDB for document-based tracking
- DynamoDB for serverless architectures
- Custom APIs for enterprise systems

## 2. Configuration Integration

### Custom Configuration Sources

```python
# Default: INI file
tg = TgData(config_path="config.ini")

# Custom: Environment variables
import os
class EnvConnectionEngine(ConnectionEngine):
    def _load_config(self):
        return ConnectionConfig(
            api_id=os.getenv('TELEGRAM_API_ID'),
            api_hash=os.getenv('TELEGRAM_API_HASH'),
            session_file=os.getenv('TELEGRAM_SESSION_FILE')
        )
```

**Integration Options:**
- Environment variables for containerized deployments
- Kubernetes ConfigMaps/Secrets
- AWS Parameter Store / Secrets Manager
- HashiCorp Vault
- Database configuration tables

## 3. Progress Monitoring Integration

### Custom Progress Handlers

```python
# Integration with monitoring systems
def prometheus_progress_callback(current, total, rate):
    # Push metrics to Prometheus
    progress_gauge.set(current / total if total else 0)
    rate_gauge.set(rate)

# Integration with task queues
def celery_progress_callback(current, total, rate):
    # Update Celery task state
    current_task.update_state(
        state='PROGRESS',
        meta={'current': current, 'total': total, 'rate': rate}
    )

tg = TgData()
messages = await tg.get_messages(
    limit=10000,
    progress_callback=prometheus_progress_callback
)
```

## 4. Data Pipeline Integration

### Stream Processing

```python
# Integration with Apache Kafka
async def kafka_message_processor(messages_df):
    for _, msg in messages_df.iterrows():
        await kafka_producer.send('telegram-messages', {
            'id': msg['MessageId'],
            'text': msg['Message'],
            'sender': msg['SenderId'],
            'timestamp': msg['Date'].isoformat()
        })

# Batch processing
messages = await tg.get_messages(limit=1000)
await kafka_message_processor(messages)
```

### ETL Pipelines

```python
# Integration with Apache Airflow
from airflow.decorators import task

@task
async def extract_telegram_messages(group_id: int):
    tg = TgData()
    return await tg.get_messages(group_id=group_id, limit=5000)

@task
def transform_messages(messages_df):
    # Apply transformations
    return messages_df

@task
def load_to_warehouse(transformed_df):
    # Load to data warehouse
    transformed_df.to_sql('telegram_messages', warehouse_conn)
```

## 5. Analytics Integration

### Data Science Workflows

```python
# Integration with Jupyter notebooks
import pandas as pd
from tgdata import TgData

async def load_telegram_data():
    tg = TgData()
    messages = await tg.get_messages(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31)
    )
    return messages

# In Jupyter
df = await load_telegram_data()
# Continue with pandas, matplotlib, etc.
```

### ML Pipeline Integration

```python
# Integration with MLflow
import mlflow

async def prepare_training_data(group_id):
    tg = TgData()
    messages = await tg.get_messages(group_id=group_id)
    
    # Log dataset with MLflow
    mlflow.log_param("group_id", group_id)
    mlflow.log_metric("message_count", len(messages))
    
    return messages
```

## 6. API Integration

### REST API Wrapper

```python
from fastapi import FastAPI, BackgroundTasks
from tgdata import TgData

app = FastAPI()
tg = TgData()

@app.post("/api/groups/{group_id}/messages")
async def fetch_messages(group_id: int, background_tasks: BackgroundTasks):
    # Start async task
    background_tasks.add_task(process_group_messages, group_id)
    return {"status": "processing", "group_id": group_id}

async def process_group_messages(group_id: int):
    messages = await tg.get_messages(group_id=group_id)
    # Store in database or send to queue
```

### GraphQL Integration

```python
import strawberry
from tgdata import TgData

@strawberry.type
class Message:
    id: int
    text: str
    sender_id: int
    date: str

@strawberry.type
class Query:
    @strawberry.field
    async def telegram_messages(self, group_id: int, limit: int = 100) -> List[Message]:
        tg = TgData()
        df = await tg.get_messages(group_id=group_id, limit=limit)
        return [Message(...) for _, row in df.iterrows()]
```

## 7. Monitoring & Observability

### OpenTelemetry Integration

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class TracedTgData(TgData):
    async def get_messages(self, **kwargs):
        with tracer.start_as_current_span("telegram.get_messages") as span:
            span.set_attribute("group_id", kwargs.get('group_id'))
            span.set_attribute("limit", kwargs.get('limit'))
            
            result = await super().get_messages(**kwargs)
            
            span.set_attribute("message_count", len(result))
            return result
```

### Logging Integration

```python
import structlog

logger = structlog.get_logger()

# Custom log handler
class StructLogHandler(logging.Handler):
    def emit(self, record):
        logger.info(
            record.getMessage(),
            level=record.levelname,
            module=record.module
        )

# Configure library logging
tg = TgData(log_file=None)  # Disable file logging
logging.getLogger('src2').addHandler(StructLogHandler())
```

## 8. Storage Integration

### Object Storage

```python
# S3 Integration
import boto3

async def archive_messages_to_s3(group_id: int):
    tg = TgData()
    messages = await tg.get_messages(group_id=group_id)
    
    # Export to S3
    s3 = boto3.client('s3')
    csv_buffer = messages.to_csv(index=False)
    
    s3.put_object(
        Bucket='telegram-archives',
        Key=f'groups/{group_id}/messages_{datetime.now().isoformat()}.csv',
        Body=csv_buffer.encode('utf-8')
    )
```

## 9. Event-Driven Integration

### Event Streaming

```python
# Integration with event systems
from tgdata import TgData
import asyncio

class TelegramEventEmitter:
    def __init__(self, event_bus):
        self.tg = TgData()
        self.event_bus = event_bus
        
    async def monitor_new_messages(self, group_id: int):
        last_message_id = 0
        
        while True:
            messages = await self.tg.get_messages(
                group_id=group_id,
                after_id=last_message_id
            )
            
            for _, msg in messages.iterrows():
                await self.event_bus.emit('telegram.new_message', {
                    'group_id': group_id,
                    'message': msg.to_dict()
                })
                last_message_id = max(last_message_id, msg['MessageId'])
            
            await asyncio.sleep(60)  # Check every minute
```

## Best Practices

1. **Use connection pooling** for high-throughput scenarios
2. **Implement custom trackers** for production deployments
3. **Add monitoring** at integration points
4. **Handle errors gracefully** with retry logic
5. **Respect rate limits** in automated systems
6. **Cache results** when appropriate
7. **Use async/await** for better performance