"""
Smoke tests for unified TgData class with real Telegram API
"""
# To run: python -m tgdata.smoke_tests.test_03_tgdata

import asyncio
import sys
import os
import tempfile
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tgdata import TgData, NoOpTracker
import pandas as pd


async def test_initialization():
    """Test TgData initialization with real config"""
    print("TEST: TgData initialization with real config...")
    try:
        # Check config exists
        if not os.path.exists("config.ini"):
            print("✗ config.ini not found")
            return False
            
        # Default initialization with real config
        tg = TgData("config.ini")
        assert tg is not None
        assert hasattr(tg, 'connection_engine')
        assert hasattr(tg, 'message_engine')
        print("✓ Default initialization successful")
        
        # Test connection is ready
        client = await tg.connection_engine.get_client()
        assert await client.is_user_authorized()
        me = await client.get_me()
        print(f"✓ Connected as: {me.first_name} (ID: {me.id})")
        await tg.close()
        
        # With custom tracker
        tg2 = TgData("config.ini", tracker=NoOpTracker())
        assert tg2.message_engine.tracker is not None
        assert isinstance(tg2.message_engine.tracker, NoOpTracker)
        print("✓ Custom tracker initialization successful")
        await tg2.close()
        
        # With connection pooling (pool_size=1 for testing)
        tg3 = TgData("config.ini", connection_pool_size=1)
        assert tg3.connection_engine.pool_size == 1
        print("✓ Connection pool initialization successful")
        await tg3.close()
        
        # With logging
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp:
            tg4 = TgData("config.ini", log_file=tmp.name)
            await tg4.close()
            os.unlink(tmp.name)
        print("✓ Logging initialization successful")
        
        return True
    except Exception as e:
        print(f"✗ Initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_group_operations():
    """Test group-related operations with real API"""
    print("\nTEST: Group operations with real data...")
    tg = None
    try:
        tg = TgData("config.ini")
        
        # Test list_groups with real API
        print("Fetching real groups...")
        groups_df = await tg.list_groups()
        assert isinstance(groups_df, pd.DataFrame)
        assert len(groups_df) > 0
        print(f"✓ Listed {len(groups_df)} real groups")
        
        # Show first few groups
        print("\nFirst 3 groups:")
        for idx, group in groups_df.head(3).iterrows():
            print(f"  - {group['Title']} (ID: {group['GroupID']})")
        
        # Test set_group with a real group ID
        first_group_id = int(groups_df.iloc[0]['GroupID'])  # Convert numpy int64 to Python int
        tg.set_group(first_group_id)
        assert tg.current_group is not None
        assert tg.current_group.id == first_group_id
        print(f"\n✓ set_group works with real group ID: {first_group_id}")
        
        return True
    except Exception as e:
        print(f"✗ Group operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if tg:
            await tg.close()


async def test_message_methods():
    """Test message-related methods with real data"""
    print("\nTEST: Message methods with real data...")
    tg = None
    try:
        tg = TgData("config.ini")
        
        # Check all methods exist
        methods = [
            'get_messages',
            'search_messages',
            'print_messages',
            'filter_messages',
            'export_messages',
            'get_statistics'
        ]
        
        for method in methods:
            assert hasattr(tg, method), f"Missing method: {method}"
            
        print("✓ All message methods exist")
        
        # Get real groups and select one with messages
        groups_df = await tg.list_groups()
        
        # Find a group with reasonable message count (prefer smaller groups for testing)
        test_group = None
        for _, group in groups_df.iterrows():
            if group['ParticipantsCount'] and 10 < group['ParticipantsCount'] < 1000:
                test_group = group
                break
        
        if test_group is None:
            # Use first group as fallback
            test_group = groups_df.iloc[0]
        
        print(f"\nTesting with group: {test_group['Title']} (ID: {test_group['GroupID']})")
        tg.set_group(int(test_group['GroupID']))  # Convert numpy int64 to Python int
        
        # Test get_messages with real data (limit to 10 for speed)
        print("Fetching real messages...")
        messages_df = await tg.get_messages(limit=10)
        
        if len(messages_df) > 0:
            print(f"✓ Retrieved {len(messages_df)} real messages")
            
            # Test filter_messages with real data
            if 'SenderId' in messages_df.columns and len(messages_df) > 1:
                # Filter by first sender
                first_sender = messages_df.iloc[0]['SenderId']
                filtered = tg.filter_messages(messages_df, sender_id=first_sender)
                print(f"✓ Filtered {len(filtered)} messages from sender {first_sender}")
            
            # Test search with real data
            if 'Message' in messages_df.columns:
                # Search for a common word
                search_results = await tg.search_messages(query="the", limit=5)
                print(f"✓ Search found {len(search_results)} messages containing 'the'")
        else:
            print("⚠ No messages in test group, skipping message tests")
        
        return True
    except Exception as e:
        print(f"✗ Message methods test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if tg:
            await tg.close()


async def test_statistics():
    """Test statistics functionality with real data"""
    print("\nTEST: Statistics with real data...")
    tg = None
    try:
        tg = TgData("config.ini")
        
        # Get a real group with messages
        groups_df = await tg.list_groups()
        
        # Find a group with good activity
        test_group = None
        for _, group in groups_df.iterrows():
            if group['ParticipantsCount'] and 50 < group['ParticipantsCount'] < 5000:
                test_group = group
                break
        
        if test_group is None:
            test_group = groups_df.iloc[0]
            
        print(f"\nGetting statistics for: {test_group['Title']}")
        tg.set_group(int(test_group['GroupID']))  # Convert numpy int64 to Python int
        
        # Get real messages (more messages for better statistics)
        messages_df = await tg.get_messages(limit=50)
        
        if len(messages_df) > 0:
            stats = tg.get_statistics(messages_df)
            
            print("\nReal statistics:")
            print(f"  - Total messages: {stats['total_messages']}")
            print(f"  - Unique senders: {stats['unique_senders']}")
            print(f"  - Messages with text: {stats['messages_with_text']}")
            print(f"  - Replies: {stats['replies']}")
            print(f"  - Forwards: {stats['forwards']}")
            
            if stats['top_senders']:
                print("\n  Top 3 senders:")
                # Handle different possible formats of top_senders
                top_senders = stats['top_senders'][:3]
                for item in top_senders:
                    if isinstance(item, tuple) and len(item) == 2:
                        sender, count = item
                        print(f"    - {sender}: {count} messages")
                    else:
                        print(f"    - {item}")
            
            # Verify stats make sense
            assert stats['total_messages'] == len(messages_df)
            assert stats['unique_senders'] <= stats['total_messages']
            assert stats['messages_with_text'] <= stats['total_messages']
            print("\n✓ Statistics calculation works with real data")
        else:
            print("⚠ No messages in test group, skipping statistics")
        
        return True
    except Exception as e:
        print(f"✗ Statistics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if tg:
            await tg.close()


async def test_export():
    """Test export functionality with real data"""
    print("\nTEST: Export functionality...")
    tg = None
    try:
        tg = TgData("config.ini")
        
        # Get real messages for export
        groups_df = await tg.list_groups()
        test_group = groups_df.iloc[0]
        tg.set_group(int(test_group['GroupID']))  # Convert numpy int64 to Python int
        
        print(f"Getting messages from: {test_group['Title']}")
        messages_df = await tg.get_messages(limit=5)
        
        if len(messages_df) > 0:
            # Test CSV export
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
                tg.export_messages(messages_df, tmp.name, format='csv')
                assert os.path.exists(tmp.name)
                file_size = os.path.getsize(tmp.name)
                print(f"✓ CSV export works (size: {file_size} bytes)")
                os.unlink(tmp.name)
            
            # Test JSON export
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
                tg.export_messages(messages_df, tmp.name, format='json')
                assert os.path.exists(tmp.name)
                file_size = os.path.getsize(tmp.name)
                print(f"✓ JSON export works (size: {file_size} bytes)")
                os.unlink(tmp.name)
        else:
            print("⚠ No messages to export, skipping export tests")
        
        return True
    except Exception as e:
        print(f"✗ Export test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if tg:
            await tg.close()


async def test_health_and_metrics():
    """Test health check and metrics with real connection"""
    print("\nTEST: Health and metrics with real connection...")
    tg = None
    try:
        tg = TgData("config.ini")
        
        # Ensure connection is established
        await tg.connection_engine.get_client()
        
        # Test health check
        health = await tg.health_check()
        assert isinstance(health, dict)
        assert 'timestamp' in health
        assert 'primary_connection' in health  # Fixed key name
        assert health['primary_connection'] == True
        print("✓ Health check shows healthy connection")
        
        # Test metrics with real data
        metrics = await tg.get_metrics()
        assert isinstance(metrics, dict)
        assert 'timestamp' in metrics
        print("✓ Metrics retrieval works")
        
        # Print actual metrics structure
        if 'connection_health' in metrics:
            print(f"  - Connection health: {metrics['connection_health']}")
        if 'performance' in metrics:
            print(f"  - Messages processed: {metrics['performance'].get('messages_processed', 0)}")
            print(f"  - Errors: {metrics['performance'].get('errors', 0)}")
        
        # Test metrics export
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            await tg.export_metrics(tmp.name)
            assert os.path.exists(tmp.name)
            # Verify file has content
            assert os.path.getsize(tmp.name) > 0
            os.unlink(tmp.name)
        print("✓ Metrics export works")
        
        return True
    except Exception as e:
        print(f"✗ Health and metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if tg:
            await tg.close()


async def test_context_manager():
    """Test context manager support with real connection"""
    print("\nTEST: Context manager with real connection...")
    try:
        async with TgData("config.ini") as tg:
            assert tg is not None
            assert hasattr(tg, 'connection_engine')
            
            # Verify connection works inside context
            client = await tg.connection_engine.get_client()
            assert await client.is_user_authorized()
            
            # Do a simple operation
            groups = await tg.list_groups()
            assert len(groups) > 0
            
        print("✓ Context manager works with real connection")
        print("✓ Connection properly closed after context")
        
        return True
    except Exception as e:
        print(f"✗ Context manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all telegram group tests with real API"""
    print("Unified TgData Tests (Real API)")
    print("=" * 50)
    print("\nNOTE: These tests require:")
    print("  1. Valid config.ini with Telegram API credentials")
    print("  2. Authenticated session file ('karaposu'.session)")
    print("  3. Access to at least one group/channel with messages")
    print("=" * 50)
    
    tests = [
        test_initialization,
        test_group_operations,
        test_message_methods,
        test_statistics,
        test_export,
        test_health_and_metrics,
        test_context_manager
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
            # Small delay to ensure SQLite connection is properly closed
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
        print("✓ All telegram group tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)