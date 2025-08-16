# Polling and Real-time Features

TgData supports both polling and real-time message monitoring, allowing you to build responsive applications that react to new messages as they arrive.

## Overview

TgData provides three main approaches for monitoring new messages:

1. **Real-time Event Handlers** - Listen for messages as they arrive using Telethon's event system
2. **Interval Polling** - Check for new messages at regular intervals
3. **Hybrid Approach** - Combine both methods for maximum reliability

## Real-time Event Handling

### Basic Event Handler

```python
from tgdata import TgData
import asyncio

async def main():
    tg = TgData()
    
    # Register a handler for all new messages
    @tg.on_new_message()
    async def handle_any_message(event):
        print(f"New message: {event.message.text}")
    
    # Run the event loop
    await tg.run_with_event_loop()

asyncio.run(main())
```

### Group-Specific Handler

```python
# Listen to messages from a specific group only
@tg.on_new_message(group_id=-1001234567890)
async def handle_group_message(event):
    sender = await event.get_sender()
    print(f"{sender.first_name}: {event.message.text}")
    
    # React to specific messages
    if event.message.text.lower() == "hello":
        await event.reply("Hi there! 👋")
```

### Multiple Handlers

You can register multiple handlers for different purposes:

```python
tg = TgData()

# Log all messages
@tg.on_new_message()
async def logger(event):
    print(f"[LOG] Message in {event.chat_id}")

# Handle commands in specific group
@tg.on_new_message(group_id=-1001234567890)
async def command_handler(event):
    if event.message.text.startswith("!"):
        command = event.message.text[1:].split()[0]
        await process_command(command, event)

# Monitor keywords
@tg.on_new_message()
async def keyword_monitor(event):
    keywords = ["urgent", "important", "alert"]
    if any(kw in event.message.text.lower() for kw in keywords):
        await notify_admin(event)
```

## Polling for Messages

### Basic Polling

```python
async def poll_example():
    tg = TgData()
    
    # Define callback for new messages
    async def process_messages(messages_df):
        print(f"Received {len(messages_df)} new messages")
        # Process the DataFrame of messages
        for _, msg in messages_df.iterrows():
            print(f"- {msg['SenderName']}: {msg['Message'][:50]}...")
    
    # Poll every 30 seconds for 10 iterations
    await tg.poll_for_messages(
        group_id=-1001234567890,
        interval=30,
        callback=process_messages,
        max_iterations=10
    )
```

### Continuous Polling with Checkpoint

```python
import json

async def poll_with_checkpoint():
    tg = TgData()
    
    # Load last checkpoint
    try:
        with open("checkpoint.json", "r") as f:
            checkpoint = json.load(f)
            after_id = checkpoint.get("last_message_id", 0)
    except:
        after_id = 0
    
    async def save_checkpoint(messages_df):
        if not messages_df.empty:
            # Save latest message ID
            last_id = messages_df['MessageId'].max()
            with open("checkpoint.json", "w") as f:
                json.dump({"last_message_id": int(last_id)}, f)
            
            # Process messages
            await process_messages(messages_df)
    
    # Poll indefinitely
    await tg.poll_for_messages(
        group_id=-1001234567890,
        interval=60,
        after_id=after_id,
        callback=save_checkpoint
    )
```

### Multi-Group Polling

```python
async def monitor_multiple_groups():
    tg = TgData()
    
    groups_to_monitor = [
        (-1001234567890, "Group 1"),
        (-1009876543210, "Group 2"),
        (-1005555555555, "Group 3")
    ]
    
    async def create_callback(group_name):
        async def callback(messages_df):
            if not messages_df.empty:
                print(f"[{group_name}] {len(messages_df)} new messages")
        return callback
    
    # Create polling tasks for each group
    tasks = []
    for group_id, group_name in groups_to_monitor:
        task = tg.poll_for_messages(
            group_id=group_id,
            interval=45,
            callback=await create_callback(group_name),
            max_iterations=20
        )
        tasks.append(task)
    
    # Run all polling tasks concurrently
    await asyncio.gather(*tasks)
```

## Combining Real-time and Polling

For maximum reliability, you can combine both approaches:

```python
async def hybrid_monitoring():
    tg = TgData()
    
    # Track received messages to avoid duplicates
    processed_ids = set()
    
    # Real-time handler for immediate response
    @tg.on_new_message(group_id=-1001234567890)
    async def realtime_handler(event):
        if event.message.id not in processed_ids:
            processed_ids.add(event.message.id)
            print(f"[REALTIME] {event.message.text}")
    
    # Polling as backup to catch any missed messages
    async def polling_backup():
        async def callback(messages_df):
            for _, msg in messages_df.iterrows():
                if msg['MessageId'] not in processed_ids:
                    processed_ids.add(msg['MessageId'])
                    print(f"[POLLING] Caught missed message: {msg['Message']}")
        
        await tg.poll_for_messages(
            group_id=-1001234567890,
            interval=300,  # Check every 5 minutes
            callback=callback
        )
    
    # Run both concurrently
    await asyncio.gather(
        tg.run_with_event_loop(),
        polling_backup()
    )
```

## Best Practices

### 1. Error Handling

```python
@tg.on_new_message()
async def safe_handler(event):
    try:
        await process_message(event)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Don't let one error stop the handler
```

### 2. Rate Limiting

```python
from asyncio import Semaphore

# Limit concurrent processing
semaphore = Semaphore(5)

@tg.on_new_message()
async def rate_limited_handler(event):
    async with semaphore:
        await process_message(event)
```

### 3. Message Filtering

```python
@tg.on_new_message()
async def filtered_handler(event):
    # Skip messages from bots
    if event.sender.bot:
        return
    
    # Only process text messages
    if not event.message.text:
        return
    
    # Skip old messages (e.g., when joining a group)
    if (datetime.now() - event.message.date).seconds > 60:
        return
    
    await process_message(event)
```

### 4. Graceful Shutdown

```python
import signal

async def main():
    tg = TgData()
    
    # Setup handlers
    @tg.on_new_message()
    async def handler(event):
        await process_message(event)
    
    # Handle shutdown
    def signal_handler(sig, frame):
        print("Shutting down gracefully...")
        asyncio.create_task(tg.close())
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await tg.run_with_event_loop()
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await tg.close()
```

## Use Cases

### 1. Alert System

Monitor groups for urgent messages and send notifications:

```python
@tg.on_new_message()
async def alert_monitor(event):
    urgent_keywords = ["urgent", "emergency", "critical", "alert"]
    
    if any(keyword in event.message.text.lower() for keyword in urgent_keywords):
        await send_alert_notification(
            group=event.chat.title,
            message=event.message.text,
            sender=event.sender.first_name
        )
```

### 2. Auto-Responder Bot

```python
@tg.on_new_message()
async def auto_responder(event):
    # FAQ responses
    faqs = {
        "price": "Our pricing starts at $99/month. Visit example.com/pricing",
        "hours": "We're open Monday-Friday, 9 AM - 5 PM EST",
        "support": "Contact support at support@example.com"
    }
    
    message_lower = event.message.text.lower()
    for keyword, response in faqs.items():
        if keyword in message_lower:
            await event.reply(response)
            break
```

### 3. Data Collection Pipeline

```python
async def data_pipeline():
    tg = TgData()
    
    async def process_batch(messages_df):
        # Clean and transform data
        processed = transform_messages(messages_df)
        
        # Save to database
        await save_to_database(processed)
        
        # Update metrics
        update_metrics(len(processed))
    
    # Poll every minute for continuous data collection
    await tg.poll_for_messages(
        group_id=-1001234567890,
        interval=60,
        callback=process_batch
    )
```

### 4. Content Moderation

```python
@tg.on_new_message(group_id=-1001234567890)
async def content_moderator(event):
    # Check for prohibited content
    if contains_prohibited_content(event.message.text):
        # Delete the message
        await event.delete()
        
        # Warn the user
        await event.respond(
            f"@{event.sender.username}, your message was removed for violating group rules."
        )
        
        # Log the incident
        await log_moderation_action(event)
```

## Performance Considerations

1. **Event Handlers** are more efficient for real-time response but require a persistent connection
2. **Polling** is more reliable for batch processing but has higher latency
3. For high-volume groups, consider:
   - Using Redis or MongoDB trackers to handle deduplication
   - Implementing message queues for processing
   - Running multiple instances with different group assignments

## Troubleshooting

### Common Issues

1. **Handler not triggering**
   - Ensure the client is authenticated
   - Check group_id is correct (negative for groups/channels)
   - Verify you have permission to read messages

2. **Duplicate messages**
   - Implement deduplication using message IDs
   - Use a tracker backend for persistence

3. **Rate limiting**
   - Implement exponential backoff
   - Use connection pooling
   - Respect Telegram's rate limits

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Create TgData with logging
tg = TgData(log_file="telegram_debug.log")
```

## Examples

Complete examples are available in the `examples/` directory:
- `polling_example.py` - Comprehensive polling examples
- `realtime_example.py` - Event handler examples
- `hybrid_example.py` - Combined approach example