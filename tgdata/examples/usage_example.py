"""
Example showing how to use the telegram-group-message-crawler with custom message tracking.
"""

import asyncio
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tgdata import TgData, InMemoryTracker, NoOpTracker
from tgdata.examples.sqlite_tracker import SQLiteTracker


async def example_basic_usage():
    """Basic usage with in-memory tracking"""
    print("=== Basic Usage Example ===\n")
    
    # Create group handler with default in-memory tracking
    tg = TgData(enable_deduplication=True)
    
    # List available groups
    groups = await tg.list_groups()
    print(f"Found {len(groups)} groups/channels")
    
    if not groups.empty:
        # Select first group
        group_id = groups.iloc[0]['GroupID']
        tg.set_group(group_id)
        
        # Get recent messages
        messages = await tg.get_messages_async(limit=10)
        print(f"\nRetrieved {len(messages)} messages")
        
        # Print them
        tg.print_messages(messages)


async def example_no_tracking():
    """Example without any message tracking"""
    print("\n=== No Tracking Example ===\n")
    
    # Use NoOpTracker to disable deduplication
    tg = TgData(
        tracker=NoOpTracker(),
        enable_deduplication=True  # Still enabled but NoOpTracker does nothing
    )
    
    # This will always fetch all messages, no deduplication
    messages = await tg.get_messages_with_date_filter(
        group_id=1001199012765,
        start_date=datetime.now() - timedelta(days=1),
        limit=50
    )
    
    print(f"Retrieved {len(messages)} messages (no deduplication)")


async def example_sqlite_tracking():
    """Example with SQLite persistent tracking"""
    print("\n=== SQLite Tracking Example ===\n")
    
    # Create SQLite tracker for persistent storage
    tracker = SQLiteTracker("my_telegram_messages.db")
    
    # Use it with TgData
    tg = TgData(
        tracker=tracker,
        enable_deduplication=True
    )
    
    group_id = 1001199012765
    
    # First run - fetch messages
    print("First run - fetching messages...")
    messages1 = await tg.get_messages_with_date_filter(
        group_id=group_id,
        start_date=datetime.now() - timedelta(days=7),
        limit=100
    )
    print(f"Retrieved {len(messages1)} messages")
    
    # Get stats from SQLite
    stats = await tracker.get_stats(group_id)
    print(f"Total tracked: {stats['total_processed']}")
    
    # Second run - only new messages
    print("\nSecond run - only new messages...")
    messages2 = await tg.get_messages_with_date_filter(
        group_id=group_id,
        start_date=datetime.now() - timedelta(days=7),
        limit=100
    )
    # Due to deduplication, this should return fewer or no messages
    print(f"Retrieved {len(messages2)} new messages")


async def example_progress_tracking():
    """Example with progress tracking"""
    print("\n=== Progress Tracking Example ===\n")
    
    tg = TgData()
    
    # Progress callback
    def show_progress(current, total, rate):
        if total:
            percent = (current / total) * 100
            print(f"\rProgress: {current}/{total} ({percent:.1f}%) - {rate:.1f} msg/s", end="")
        else:
            print(f"\rProgress: {current} messages - {rate:.1f} msg/s", end="")
    
    # Fetch with progress
    messages = await tg.fetch_messages_with_progress(
        group_id=1001199012765,
        limit=500,
        progress_callback=show_progress
    )
    
    print(f"\n\nCompleted! Retrieved {len(messages)} messages")


async def example_resumable_with_sqlite():
    """Example of resumable operations using SQLite tracker"""
    print("\n=== Resumable Operations Example ===\n")
    
    # SQLite tracker supports checkpointing
    tracker = SQLiteTracker("resumable_messages.db")
    tg = TgData(tracker=tracker)
    
    operation_id = "weekly_export_2024_01"
    group_id = 1001199012765
    
    # Check for existing checkpoint
    checkpoint = tracker.load_checkpoint(operation_id)
    min_id = None
    
    if checkpoint:
        print(f"Resuming from checkpoint: {checkpoint['total_processed']} messages processed")
        min_id = checkpoint['last_message_id']
    else:
        print("Starting fresh operation")
    
    # Fetch messages (will resume from min_id if set)
    try:
        messages = await tg.fetch_messages_with_progress(
            group_id=group_id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            min_id=min_id,
            limit=1000
        )
        
        print(f"\nOperation completed! Retrieved {len(messages)} messages")
        
    except Exception as e:
        print(f"\nOperation interrupted: {e}")
        # On interruption, save checkpoint
        if len(messages) > 0:
            last_msg = messages.iloc[-1]
            tracker.save_checkpoint(
                operation_id=operation_id,
                group_id=group_id,
                last_message_id=last_msg['MessageId'],
                last_message_date=last_msg['Date'],
                total_processed=len(messages)
            )
            print("Checkpoint saved for resume")


async def main():
    """Run examples"""
    print("Telegram Group Message Crawler - Usage Examples")
    print("=" * 50)
    
    # Note: These examples require valid Telegram credentials in config.ini
    
    try:
        # Basic usage
        await example_basic_usage()
        
        # Without tracking
        await example_no_tracking()
        
        # With SQLite
        await example_sqlite_tracking()
        
        # Progress tracking
        await example_progress_tracking()
        
        # Resumable operations
        await example_resumable_with_sqlite()
        
    except Exception as e:
        print(f"\nError in examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())