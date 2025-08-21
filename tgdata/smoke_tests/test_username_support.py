"""
Test if Telethon supports using usernames instead of numeric IDs
"""
# To run: python -m tgdata.smoke_tests.test_username_support

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tgdata import TgData

async def test_username_support():
    """Test various ways to identify a group/channel"""
    print("Testing Username Support in Telethon")
    print("=" * 50)
    
    tg = TgData("config.ini")
    client = await tg.connection_engine.get_client()
    
    # Test cases - you'll need to use real usernames from your groups
    test_cases = [
        # (description, identifier)
        ("Numeric ID", 4611400320),  # BudgetyAIDev
        ("Username with @", "@Bitcoinsensus"),  # From your group list
        ("Username without @", "Bitcoinsensus"),
        ("Username lowercase", "bitcoinsensus"),
        # You can add more test cases with groups you have access to
    ]
    
    async with client:
        for description, identifier in test_cases:
            print(f"\nTest: {description}")
            print(f"  Identifier: {identifier}")
            
            try:
                # Try to get the entity
                entity = await client.get_entity(identifier)
                
                print(f"  ✓ Success!")
                print(f"    - Title: {entity.title}")
                print(f"    - ID: {entity.id}")
                print(f"    - Username: @{entity.username if hasattr(entity, 'username') and entity.username else 'None'}")
                
                # Try to fetch a few messages to confirm it works
                messages = []
                async for msg in client.iter_messages(entity, limit=3):
                    if msg.text:
                        messages.append(msg.text[:30])
                
                if messages:
                    print(f"    - Sample messages retrieved: {len(messages)}")
                
            except ValueError as e:
                print(f"  ✗ Failed (ValueError): {e}")
                print(f"    This usually means the entity wasn't found or you don't have access")
            except Exception as e:
                print(f"  ✗ Failed ({type(e).__name__}): {e}")
    
    # Now test with tgdata's get_messages directly
    print("\n" + "=" * 50)
    print("Testing with tgdata.get_messages()")
    print("=" * 50)
    
    test_with_tgdata = [
        ("Numeric ID", 4611400320),
        ("Username with @", "@Bitcoinsensus"),
    ]
    
    for description, identifier in test_with_tgdata:
        print(f"\nTest: {description} ({identifier})")
        try:
            # This will fail for usernames since get_messages expects int
            # but let's see what error we get
            messages = await tg.get_messages(
                group_id=identifier,
                limit=2
            )
            print(f"  ✓ Retrieved {len(messages)} messages")
        except TypeError as e:
            print(f"  ✗ Type Error (expected): {e}")
            print(f"    This is because tgdata currently only accepts int for group_id")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    await tg.close()
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("- Telethon DOES support usernames (with or without @)")
    print("- Telethon DOES support numeric IDs")
    print("- tgdata currently only accepts numeric IDs")
    print("- We can update tgdata to accept both!")

if __name__ == "__main__":
    asyncio.run(test_username_support())