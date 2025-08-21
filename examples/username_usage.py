"""
Example: Using usernames instead of numeric IDs
"""

import asyncio
from tgdata import TgData

async def main():
    # Initialize the client
    tg = TgData("config.ini")
    
    # List all groups to see available usernames
    groups = await tg.list_groups()
    print("Available groups:")
    for _, group in groups.head(5).iterrows():
        print(f"  {group['Title']}: {group['Identifier']}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 1: Using username with @ symbol
    messages = await tg.get_messages(
        group_id="@Bitcoinsensus",  # Username with @
        limit=5
    )
    print(f"Got {len(messages)} messages from @Bitcoinsensus")
    
    # Example 2: Using username without @ symbol
    messages = await tg.get_messages(
        group_id="Bitcoinsensus",  # Username without @ also works
        limit=5
    )
    print(f"Got {len(messages)} messages from Bitcoinsensus (no @)")
    
    # Example 3: Using numeric ID (still works)
    messages = await tg.get_messages(
        group_id=1670178185,  # Numeric ID
        limit=5
    )
    print(f"Got {len(messages)} messages using numeric ID")
    
    # Example 4: Get message count using username
    count = await tg.get_message_count(group_id="@Bitcoinsensus")
    print(f"\nTotal messages in @Bitcoinsensus: {count}")
    
    # Example 5: Search messages using username
    results = await tg.search_messages(
        query="bitcoin",
        group_id="@Bitcoinsensus",
        limit=3
    )
    print(f"Found {len(results)} messages containing 'bitcoin'")
    
    # Example 6: Polling with username
    print("\nStarting polling for @Bitcoinsensus (will run for 10 seconds)...")
    
    async def on_new_message(messages_df):
        print(f"  New messages: {len(messages_df)}")
    
    # Poll for 10 seconds
    await asyncio.wait_for(
        tg.poll_for_messages(
            group_id="@Bitcoinsensus",
            interval=5,
            callback=on_new_message,
            max_iterations=2
        ),
        timeout=15
    )
    
    await tg.close()

if __name__ == "__main__":
    asyncio.run(main())