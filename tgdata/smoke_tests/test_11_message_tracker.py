"""
Smoke tests for MessageTracker class
"""
# To run: python -m tgdata2.smoke_tests.test_03_message_tracker

import asyncio
import sys
import os
import tempfile
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tgdata.message_tracker_interface import InMemoryTracker, MessageInfo, NoOpTracker
from tgdata.progress import ProgressTracker


async def test_tracker_initialization():
    """Test InMemoryTracker initialization"""
    print("TEST: InMemoryTracker initialization...")
    try:
        # Test default initialization
        tracker = InMemoryTracker()
        assert tracker is not None
        print("✓ InMemoryTracker created successfully")
        
        # Test with max_size
        tracker_limited = InMemoryTracker(max_size=100)
        assert tracker_limited._max_size == 100
        print("✓ InMemoryTracker with size limit created")
        
        # Test NoOpTracker
        noop = NoOpTracker()
        assert noop is not None
        print("✓ NoOpTracker created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Initialization test failed: {e}")
        return False


async def test_message_tracking():
    """Test message tracking functionality"""
    print("\nTEST: Message tracking...")
    try:
        tracker = InMemoryTracker()
        
        # Track a message
        msg_id = 12345
        group_id = 1001
        sender_id = 9999
        date = datetime.now()
        
        # Should not be processed initially
        assert not await tracker.is_processed(msg_id, group_id)
        print("✓ New message not marked as processed")
        
        # Mark as processed
        msg_info = MessageInfo(
            message_id=msg_id,
            group_id=group_id,
            sender_id=sender_id,
            date=date
        )
        await tracker.mark_processed(msg_info)
        
        # Should now be processed
        assert await tracker.is_processed(msg_id, group_id)
        print("✓ Message marked as processed")
        
        # Test batch processing
        messages = [
            MessageInfo(message_id=100, group_id=group_id, sender_id=1, date=date),
            MessageInfo(message_id=101, group_id=group_id, sender_id=2, date=date),
            MessageInfo(message_id=102, group_id=group_id, sender_id=3, date=date),
        ]
        
        await tracker.mark_batch_processed(messages)
        
        # All should be processed
        for msg in messages:
            assert await tracker.is_processed(msg.message_id, group_id)
        print("✓ Batch processing works")
        
        return True
    except Exception as e:
        print(f"✗ Message tracking test failed: {e}")
        return False


async def test_deduplication():
    """Test message deduplication"""
    print("\nTEST: Message deduplication...")
    try:
        tracker = InMemoryTracker()
        
        group_id = 1001
        messages = [
            {'MessageId': 1, 'SenderId': 100, 'Date': datetime.now()},
            {'MessageId': 2, 'SenderId': 101, 'Date': datetime.now()},
            {'MessageId': 3, 'SenderId': 102, 'Date': datetime.now()},
        ]
        
        # Mark first two as processed
        await tracker.mark_processed(MessageInfo(1, group_id, 100, datetime.now()))
        await tracker.mark_processed(MessageInfo(2, group_id, 101, datetime.now()))
        
        # Get unprocessed messages
        unprocessed = await tracker.get_unprocessed(messages, group_id)
        
        assert len(unprocessed) == 1
        assert unprocessed[0]['MessageId'] == 3
        print("✓ Deduplication filters correctly")
        
        # Test NoOpTracker (should not filter anything)
        noop = NoOpTracker()
        unprocessed_noop = await noop.get_unprocessed(messages, group_id)
        assert len(unprocessed_noop) == 3
        print("✓ NoOpTracker returns all messages")
        
        return True
    except Exception as e:
        print(f"✗ Deduplication test failed: {e}")
        return False


async def test_memory_limit():
    """Test memory limit functionality"""
    print("\nTEST: Memory limit...")
    try:
        # Create tracker with small limit
        tracker = InMemoryTracker(max_size=3)
        
        # Add 5 messages (should evict oldest 2)
        for i in range(5):
            await tracker.mark_processed(
                MessageInfo(i, 1001, 100, datetime.now())
            )
        
        # Check oldest are evicted
        assert not await tracker.is_processed(0, 1001)  # Evicted
        assert not await tracker.is_processed(1, 1001)  # Evicted
        assert await tracker.is_processed(2, 1001)      # Still there
        assert await tracker.is_processed(3, 1001)      # Still there
        assert await tracker.is_processed(4, 1001)      # Still there
        
        print("✓ LRU eviction works correctly")
        
        # Test stats
        stats = await tracker.get_stats()
        assert stats['current_size'] == 3
        assert stats['max_size'] == 3
        print("✓ Stats reflect size limits")
        
        return True
    except Exception as e:
        print(f"✗ Memory limit test failed: {e}")
        return False


async def test_progress_tracker():
    """Test progress tracking"""
    print("\nTEST: Progress tracking...")
    try:
        # Test with known total
        progress = ProgressTracker(
            total_expected=100
        )
        
        progress.start()
        
        # Update progress
        progress.update(10)
        assert progress.current == 10
        
        progress.update(15)  # Total 25
        assert progress.current == 25
        print("✓ Progress tracking works")
        
        # Test ETA calculation
        import time
        time.sleep(0.1)  # Let some time pass
        progress.update(25)  # Total 50
        
        eta = progress.get_eta()
        assert eta is not None
        print("✓ ETA calculation works")
        
        # Test with callback
        callback_called = False
        def test_callback(current, total, rate):
            nonlocal callback_called
            callback_called = True
            assert current > 0
            assert total == 100
            assert rate > 0
        
        progress2 = ProgressTracker(
            total_expected=100,
            callback=test_callback
        )
        progress2.start()
        progress2.update(1)
        
        assert callback_called
        print("✓ Progress callback works")
        
        return True
    except Exception as e:
        print(f"✗ Progress tracking test failed: {e}")
        return False


async def test_statistics():
    """Test statistics functionality"""
    print("\nTEST: Statistics...")
    try:
        tracker = InMemoryTracker()
        
        group_id = 1001
        base_date = datetime.now()
        
        # Add some test messages
        for i in range(10):
            await tracker.mark_processed(
                MessageInfo(
                    message_id=i,
                    group_id=group_id,
                    sender_id=i % 3,  # 3 unique senders
                    date=base_date - timedelta(days=i)
                )
            )
        
        # Get stats
        stats = await tracker.get_stats(group_id)
        
        assert stats['total_processed'] == 10
        assert stats['implementation'] == 'InMemoryTracker'
        print("✓ Statistics calculation works")
        
        # Test clear functionality
        tracker.clear()
        stats = await tracker.get_stats()
        assert stats['total_processed'] == 0
        print("✓ Clear functionality works")
        
        return True
    except Exception as e:
        print(f"✗ Statistics test failed: {e}")
        return False


async def main():
    """Run all message tracker tests"""
    print("Message Tracker Tests")
    print("=" * 50)
    
    tests = [
        test_tracker_initialization,
        test_message_tracking,
        test_deduplication,
        test_memory_limit,
        test_progress_tracker,
        test_statistics
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
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
        print("✓ All message tracker tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)