"""
Smoke tests for polling and real-time message features
"""
# To run: python -m tgdata.smoke_tests.test_10_polling

import asyncio
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tgdata import TgData
import pandas as pd


async def test_polling_basic():
    """Test basic polling functionality"""
    print("TEST: Basic polling functionality...")
    
    try:
        # Initialize TgData
        tg = TgData("config.ini")
        
        # Get a test group
        groups = await tg.list_groups()
        if groups.empty:
            print("✗ No groups available for testing")
            return False
            
        test_group = groups.iloc[0]
        test_group_id = int(test_group['GroupID'])
        print(f"Testing with group: {test_group['Title']} (ID: {test_group_id})")
        
        # Define a callback to handle new messages
        messages_received = []
        
        async def message_callback(messages_df):
            count = len(messages_df)
            messages_received.append(count)
            print(f"  Received {count} new messages")
            if not messages_df.empty:
                # Show first message
                first_msg = messages_df.iloc[0]
                msg_text = first_msg.get('Message', 'No text')[:50]
                print(f"  First message: {msg_text}...")
        
        # Get the latest message ID to start polling after
        initial_messages = await tg.get_messages(group_id=test_group_id, limit=1)
        start_after_id = 0
        if not initial_messages.empty:
            start_after_id = initial_messages['MessageId'].max()
            print(f"Starting polling after message ID: {start_after_id}")
        
        # Test polling with 3 iterations
        print("\nPolling for 3 iterations (5 seconds each)...")
        await tg.poll_for_messages(
            group_id=test_group_id,
            interval=5,
            after_id=start_after_id,
            callback=message_callback,
            max_iterations=3
        )
        
        print(f"✓ Polling completed. Total polls that found messages: {len(messages_received)}")
        await tg.close()
        return True
        
    except Exception as e:
        print(f"✗ Polling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_event_handler():
    """Test real-time event handler"""
    print("\nTEST: Real-time event handler...")
    
    try:
        # Initialize TgData
        tg = TgData("config.ini")
        
        # Get a test group
        groups = await tg.list_groups()
        if groups.empty:
            print("✗ No groups available for testing")
            return False
            
        test_group = groups.iloc[0]
        test_group_id = int(test_group['GroupID'])
        print(f"Testing with group: {test_group['Title']} (ID: {test_group_id})")
        
        # Track received messages
        received_events = []
        
        # Register event handler
        @tg.on_new_message(group_id=test_group_id)
        async def message_handler(event):
            received_events.append(event)
            print(f"  Real-time message from {event.sender_id}: {event.message.text[:50]}...")
        
        # Give time for handler to register
        await asyncio.sleep(1)
        
        print("✓ Event handler registered successfully")
        print("Note: To fully test real-time events, you would need to:")
        print("  1. Call await tg.run_with_event_loop() to start listening")
        print("  2. Send messages to the group from another account")
        print("  3. See the messages appear in real-time")
        
        await tg.close()
        return True
        
    except Exception as e:
        print(f"✗ Event handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_polling_error_handling():
    """Test polling error recovery"""
    print("\nTEST: Polling error recovery...")
    
    try:
        tg = TgData("config.ini")
        
        # Test with invalid group ID
        error_count = []
        
        async def error_callback(messages_df):
            # This shouldn't be called for invalid group
            error_count.append(1)
        
        print("Testing polling with invalid group ID...")
        
        # Create a task for polling (it will fail but should handle errors gracefully)
        poll_task = asyncio.create_task(
            tg.poll_for_messages(
                group_id=999999999,  # Invalid group ID
                interval=2,
                callback=error_callback,
                max_iterations=2
            )
        )
        
        # Wait for polling to complete
        await poll_task
        
        print("✓ Polling handled errors gracefully")
        await tg.close()
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_handlers():
    """Test multiple event handlers"""
    print("\nTEST: Multiple event handlers...")
    
    try:
        tg = TgData("config.ini")
        
        # Get test groups
        groups = await tg.list_groups()
        if len(groups) < 2:
            print("! Need at least 2 groups for this test, skipping")
            await tg.close()
            return True
            
        group1_id = int(groups.iloc[0]['GroupID'])
        group2_id = int(groups.iloc[1]['GroupID'])
        
        # Register handler for specific group
        @tg.on_new_message(group_id=group1_id)
        async def group1_handler(event):
            print(f"  Group 1 message: {event.message.text[:30]}...")
        
        # Register handler for all groups
        @tg.on_new_message()
        async def all_groups_handler(event):
            print(f"  Any group message from {event.chat_id}: {event.message.text[:30]}...")
        
        await asyncio.sleep(1)
        
        print(f"✓ Registered handler for group {group1_id}")
        print("✓ Registered handler for all groups")
        
        await tg.close()
        return True
        
    except Exception as e:
        print(f"✗ Multiple handlers test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all polling tests"""
    print("Polling and Real-time Features Tests")
    print("=" * 50)
    
    tests = [
        test_polling_basic,
        test_event_handler,
        test_polling_error_handling,
        test_multiple_handlers
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\nSummary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All polling tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)