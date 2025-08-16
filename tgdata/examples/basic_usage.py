"""
Basic usage examples for TgData
"""

import asyncio
from datetime import datetime, timedelta
from tgdata import TgData


async def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Usage Example ===\n")
    
    # Initialize TgData
    tg = TgData("config.ini")
    
    # List available groups
    groups = await tg.list_groups()
    print(f"Found {len(groups)} groups/channels")
    
    if not groups.empty:
        # Select first group
        group_id = groups.iloc[0]['GroupID']
        group_name = groups.iloc[0]['Title']
        print(f"\nUsing group: {group_name}")
        
        # Get recent messages
        messages = await tg.get_messages(
            group_id=group_id,
            limit=10
        )
        print(f"Retrieved {len(messages)} messages")
        
        # Display messages
        tg.print_messages(messages, limit=5)
        
        # Get statistics
        stats = tg.get_statistics(messages)
        print(f"\nStatistics: {stats}")
        
    await tg.close()


async def example_search_and_filter():
    """Example of searching and filtering messages"""
    print("\n=== Search and Filter Example ===\n")
    
    tg = TgData("config.ini")
    
    groups = await tg.list_groups()
    if not groups.empty:
        group_id = groups.iloc[0]['GroupID']
        
        # Search for messages containing specific text
        results = await tg.search_messages(
            query="hello",
            group_id=group_id,
            limit=5
        )
        print(f"Found {len(results)} messages containing 'hello'")
        
        # Get messages from last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        recent_messages = await tg.get_messages(
            group_id=group_id,
            start_date=week_ago,
            limit=100
        )
        print(f"\nMessages from last 7 days: {len(recent_messages)}")
        
        # Filter by sender
        if not recent_messages.empty and 'SenderId' in recent_messages.columns:
            sender_id = recent_messages.iloc[0]['SenderId']
            filtered = tg.filter_messages(recent_messages, sender_id=sender_id)
            print(f"Messages from sender {sender_id}: {len(filtered)}")
    
    await tg.close()


async def example_export():
    """Example of exporting messages"""
    print("\n=== Export Example ===\n")
    
    tg = TgData("config.ini")
    
    groups = await tg.list_groups()
    if not groups.empty:
        group_id = groups.iloc[0]['GroupID']
        
        # Get messages
        messages = await tg.get_messages(
            group_id=group_id,
            limit=50
        )
        
        if not messages.empty:
            # Export to CSV
            tg.export_messages(messages, "messages.csv", format="csv")
            print("✓ Exported to messages.csv")
            
            # Export to JSON
            tg.export_messages(messages, "messages.json", format="json")
            print("✓ Exported to messages.json")
            
            # Get and export metrics
            await tg.export_metrics("session_metrics.json")
            print("✓ Exported metrics to session_metrics.json")
    
    await tg.close()


async def example_progress_tracking():
    """Example with progress tracking"""
    print("\n=== Progress Tracking Example ===\n")
    
    tg = TgData("config.ini")
    
    groups = await tg.list_groups()
    if not groups.empty:
        group_id = groups.iloc[0]['GroupID']
        
        # Define progress callback
        def progress_callback(current, total, rate):
            percent = (current / total * 100) if total else 0
            print(f"Progress: {current}/{total} ({percent:.1f}%) - {rate:.1f} msg/s", end='\r')
        
        # Get messages with progress tracking
        messages = await tg.get_messages(
            group_id=group_id,
            limit=500,
            with_progress=True,
            progress_callback=progress_callback
        )
        print(f"\nCompleted! Total messages: {len(messages)}")
    
    await tg.close()


async def example_incremental_fetch():
    """Example of incremental message fetching"""
    print("\n=== Incremental Fetch Example ===\n")
    
    tg = TgData("config.ini")
    
    groups = await tg.list_groups()
    if not groups.empty:
        group_id = groups.iloc[0]['GroupID']
        
        # First fetch - get initial messages
        print("Initial fetch...")
        messages = await tg.get_messages(group_id=group_id, limit=10)
        
        if not messages.empty:
            # Remember the latest message ID
            last_message_id = messages['MessageId'].max()
            print(f"Latest message ID: {last_message_id}")
            
            # Wait a bit (in real usage, this would be your next scheduled run)
            await asyncio.sleep(2)
            
            # Fetch only new messages since last_message_id
            print(f"\nFetching new messages after ID {last_message_id}...")
            new_messages = await tg.get_messages(
                group_id=group_id,
                after_id=last_message_id
            )
            
            if not new_messages.empty:
                print(f"Found {len(new_messages)} new messages")
            else:
                print("No new messages")
    
    await tg.close()


async def main():
    """Run all examples"""
    examples = [
        example_basic_usage,
        example_search_and_filter,
        example_export,
        example_progress_tracking,
        example_incremental_fetch
    ]
    
    for example in examples:
        try:
            await example()
            print("\n" + "="*50 + "\n")
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())