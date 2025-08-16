"""
Example: Using polling and real-time features in TgData
"""

import asyncio
from datetime import datetime
from tgdata import TgData


async def example_basic_polling():
    """Example: Basic polling for new messages"""
    print("=== Basic Polling Example ===\n")
    
    # Initialize TgData
    tg = TgData("config.ini")
    
    # Get groups
    groups = await tg.list_groups()
    if groups.empty:
        print("No groups available")
        return
        
    # Select first group
    group_id = int(groups.iloc[0]['GroupID'])
    group_name = groups.iloc[0]['Title']
    print(f"Polling messages from: {group_name}\n")
    
    # Define callback for new messages
    async def process_new_messages(messages_df):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Got {len(messages_df)} new messages:")
        for _, msg in messages_df.head(3).iterrows():
            print(f"  - {msg.get('SenderName', 'Unknown')}: {msg.get('Message', '')[:50]}...")
        print()
    
    # Start polling (runs for 5 iterations, checking every 30 seconds)
    await tg.poll_for_messages(
        group_id=group_id,
        interval=30,
        callback=process_new_messages,
        max_iterations=5
    )
    
    await tg.close()


async def example_real_time_events():
    """Example: Real-time event handling"""
    print("\n=== Real-time Event Handling Example ===\n")
    
    # Initialize TgData
    tg = TgData("config.ini")
    
    # Get groups for filtering
    groups = await tg.list_groups()
    if not groups.empty:
        group_id = int(groups.iloc[0]['GroupID'])
        group_name = groups.iloc[0]['Title']
        print(f"Listening for messages from: {group_name}\n")
    else:
        group_id = None
        print("Listening for messages from all groups\n")
    
    # Register event handler for new messages
    @tg.on_new_message(group_id=group_id)
    async def handle_new_message(event):
        # Get sender info
        sender = await event.get_sender()
        sender_name = getattr(sender, 'first_name', 'Unknown')
        
        # Get message text
        text = event.message.text or "[Media/File]"
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {sender_name}: {text[:100]}")
        
        # React to specific commands
        if text.lower() == "!ping":
            await event.reply("Pong! 🏓")
    
    # Register handler for all groups (logging)
    @tg.on_new_message()
    async def log_all_messages(event):
        print(f"[LOG] Message in chat {event.chat_id}")
    
    print("Listening for messages... Press Ctrl+C to stop\n")
    
    try:
        # Run the event loop
        await tg.run_with_event_loop()
    except KeyboardInterrupt:
        print("\nStopping...")
        await tg.close()


async def example_checkpoint_polling():
    """Example: Polling with checkpoint management"""
    print("\n=== Checkpoint-based Polling Example ===\n")
    
    import json
    import os
    
    # Initialize TgData
    tg = TgData("config.ini")
    
    # Checkpoint file
    checkpoint_file = "polling_checkpoint.json"
    
    # Load checkpoint if exists
    checkpoint = {}
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
    
    # Get groups
    groups = await tg.list_groups()
    if groups.empty:
        print("No groups available")
        return
        
    group_id = int(groups.iloc[0]['GroupID'])
    group_name = groups.iloc[0]['Title']
    
    # Get last processed message ID from checkpoint
    after_id = checkpoint.get(str(group_id), 0)
    print(f"Resuming from message ID: {after_id}")
    print(f"Polling messages from: {group_name}\n")
    
    # Callback that updates checkpoint
    async def process_and_checkpoint(messages_df):
        if messages_df.empty:
            return
            
        # Process messages
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing {len(messages_df)} messages")
        
        # Update checkpoint with latest message ID
        latest_id = messages_df['MessageId'].max()
        checkpoint[str(group_id)] = int(latest_id)
        
        # Save checkpoint
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f)
        
        print(f"  Checkpoint updated: {latest_id}")
    
    # Poll with checkpoint
    await tg.poll_for_messages(
        group_id=group_id,
        interval=20,
        after_id=after_id,
        callback=process_and_checkpoint,
        max_iterations=3
    )
    
    print(f"\nFinal checkpoint saved to {checkpoint_file}")
    await tg.close()


async def example_multi_group_monitoring():
    """Example: Monitor multiple groups simultaneously"""
    print("\n=== Multi-group Monitoring Example ===\n")
    
    # Initialize TgData
    tg = TgData("config.ini")
    
    # Get all groups
    groups = await tg.list_groups()
    if len(groups) < 2:
        print("Need at least 2 groups for this example")
        return
    
    # Select first 3 groups (or less)
    monitor_groups = groups.head(3)
    
    print("Monitoring groups:")
    for _, group in monitor_groups.iterrows():
        print(f"  - {group['Title']} (ID: {group['GroupID']})")
    print()
    
    # Create polling tasks for each group
    async def poll_group(group_id, group_name):
        async def callback(messages_df):
            if not messages_df.empty:
                print(f"[{group_name}] {len(messages_df)} new messages")
        
        await tg.poll_for_messages(
            group_id=int(group_id),
            interval=15,
            callback=callback,
            max_iterations=4
        )
    
    # Start polling all groups concurrently
    tasks = []
    for _, group in monitor_groups.iterrows():
        task = asyncio.create_task(
            poll_group(group['GroupID'], group['Title'])
        )
        tasks.append(task)
    
    # Wait for all polling to complete
    await asyncio.gather(*tasks)
    
    await tg.close()


async def main():
    """Run examples"""
    examples = [
        ("Basic Polling", example_basic_polling),
        ("Real-time Events", example_real_time_events),
        ("Checkpoint Polling", example_checkpoint_polling),
        ("Multi-group Monitoring", example_multi_group_monitoring)
    ]
    
    print("TgData Polling Examples")
    print("=" * 50)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    try:
        choice = input("\nSelect example (1-4) or 'all' to run all: ").strip()
        
        if choice.lower() == 'all':
            for name, func in examples:
                print(f"\n{'='*50}")
                await func()
                await asyncio.sleep(1)
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                await examples[idx][1]()
            else:
                print("Invalid choice")
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()