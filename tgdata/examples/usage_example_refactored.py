"""
Example showing how to use the refactored telegram-group-message-crawler.
"""

import asyncio
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tgdata import TgData, InMemoryTracker, NoOpTracker
from tgdata.examples.sqlite_tracker import SQLiteTracker


async def example_basic_usage():
    """Basic usage with default settings"""
    print("=== Basic Usage Example ===\n")
    
    # Create TgData with default settings (in-memory tracking)
    tg = TgData()
    
    # List available groups
    groups = await tg.list_groups()
    print(f"Found {len(groups)} groups/channels")
    
    if not groups.empty:
        # Select first group
        group_id = groups.iloc[0]['GroupID']
        tg.set_group(group_id)
        
        # Get recent messages
        messages = await tg.get_messages(limit=10)
        print(f"\nRetrieved {len(messages)} messages")
        
        # Print them
        tg.print_messages(messages)
        
        # Get statistics
        stats = tg.get_statistics(messages)
        print(f"\nStatistics: {stats}")


async def example_no_tracking():
    """Example without any message tracking"""
    print("\n=== No Tracking Example ===\n")
    
    # Use NoOpTracker to disable deduplication
    tg = TgData(
        tracker=NoOpTracker(),
        enable_deduplication=True  # Still enabled but NoOpTracker does nothing
    )
    
    # Get messages - no deduplication will occur
    messages = await tg.get_messages(
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
    messages1 = await tg.get_messages(
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
    messages2 = await tg.get_messages(
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
    
    # Fetch with progress tracking
    messages = await tg.get_messages(
        group_id=1001199012765,
        limit=500,
        with_progress=True  # Enables default progress display
    )
    
    print(f"\n\nCompleted! Retrieved {len(messages)} messages")
    
    # Custom progress callback
    print("\nWith custom progress callback:")
    
    def custom_progress(current, total, rate):
        bar_length = 40
        if total:
            progress = current / total
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r[{bar}] {current}/{total} - {rate:.1f} msg/s", end="")
        else:
            print(f"\rProcessing: {current} messages - {rate:.1f} msg/s", end="")
    
    messages = await tg.get_messages(
        group_id=1001199012765,
        limit=200,
        progress_callback=custom_progress
    )
    print("\nDone!")


async def example_connection_pooling():
    """Example with connection pooling for better performance"""
    print("\n=== Connection Pooling Example ===\n")
    
    # Enable connection pooling with 3 connections
    tg = TgData(
        connection_pool_size=3,
        log_file="telegram_debug.log"
    )
    
    # Perform health check
    health = await tg.health_check()
    print(f"Health check: {health}")
    
    # Fetch messages (will use pool for better rate limit handling)
    messages = await tg.get_messages(
        group_id=1001199012765,
        limit=1000
    )
    
    print(f"Retrieved {len(messages)} messages using connection pool")
    
    # Export metrics
    tg.export_metrics("session_metrics.json")


async def example_advanced_filtering():
    """Example of advanced message filtering and export"""
    print("\n=== Advanced Filtering Example ===\n")
    
    tg = TgData()
    
    # Get messages from last week
    messages = await tg.get_messages(
        group_id=1001199012765,
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        limit=1000
    )
    
    # Filter messages
    filtered = tg.filter_messages(
        messages,
        keyword="important",
        start_date=datetime.now() - timedelta(days=3)
    )
    
    print(f"Found {len(filtered)} messages containing 'important' from last 3 days")
    
    # Export to different formats
    if not filtered.empty:
        tg.export_messages(filtered, "important_messages.csv", format='csv')
        tg.export_messages(filtered, "important_messages.json", format='json')
        print("Exported filtered messages")
    
    # Get new messages since last check
    if not messages.empty:
        last_id = messages['MessageId'].max()
        new_messages = await tg.get_messages(group_id=group_id, after_id=last_id)
        print(f"\nFound {len(new_messages)} new messages since last check")


async def example_search():
    """Example of searching messages"""
    print("\n=== Search Example ===\n")
    
    tg = TgData()
    
    # Search for specific content
    results = await tg.search_messages(
        query="meeting",
        group_id=1001199012765,
        limit=50
    )
    
    print(f"Found {len(results)} messages containing 'meeting'")
    
    # Display search results
    if not results.empty:
        tg.print_messages(results, limit=5)


async def example_profile_photos():
    """Example of handling profile photos"""
    print("\n=== Profile Photos Example ===\n")
    
    tg = TgData()
    
    # Get messages with profile photos
    messages = await tg.get_messages(
        group_id=1001199012765,
        limit=50,
        include_profile_photos=True
    )
    
    print(f"Retrieved {len(messages)} messages with profile photos")
    
    # Save profile photos to directory
    if not messages.empty and 'PhotoData' in messages.columns:
        tg.save_photos(messages, "profile_photos")
        print("Saved profile photos to 'profile_photos' directory")


async def main():
    """Run examples"""
    print("Telegram Group Message Crawler - Refactored Usage Examples")
    print("=" * 60)
    
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
        
        # Connection pooling
        await example_connection_pooling()
        
        # Advanced filtering
        await example_advanced_filtering()
        
        # Search
        await example_search()
        
        # Profile photos
        await example_profile_photos()
        
    except Exception as e:
        print(f"\nError in examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())