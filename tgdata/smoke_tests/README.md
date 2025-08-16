# Smoke Tests for TgData

This directory contains smoke tests for the TgData Telegram message extraction library.

## Test Coverage

### 1. **test_00_connection.py**
Tests basic connection functionality:
- Connection initialization
- Connecting to Telegram
- Authentication validation
- Session persistence

### 2. **test_01_list_group_chats.py**
Tests group listing functionality:
- Listing all accessible groups/channels
- Group metadata retrieval
- Group filtering and sorting

### 3. **test_02_get_message_count.py**
Tests message counting:
- Get total message count without fetching all messages
- Efficient count retrieval using Telethon's API

### 4. **test_03_get_all_messages.py**
Tests basic message retrieval:
- Fetching all messages from a group
- Message data structure validation
- Basic filtering and limits

### 5. **test_04_get_all_messages_in_batches.py**
Tests batch processing:
- Fetching messages in configurable batches
- CSV export with incremental writes
- Progress tracking
- Using `after_id` for incremental fetching

### 6. **test_06_advanced_features.py**
Tests advanced features:
- Connection pooling
- Progress tracking callbacks
- Date-based filtering
- Message caching behavior
- Metrics and logging
- Health checks and validation

### 7. **test_10_polling.py**
Tests polling and real-time features:
- Polling for new messages at intervals
- Real-time event handlers
- Error handling in polling
- Multiple handler registration

## Running Tests

### Run Individual Test:
```bash
# Basic tests
python -m tgdata.smoke_tests.test_00_connection
python -m tgdata.smoke_tests.test_01_list_group_chats
python -m tgdata.smoke_tests.test_02_get_message_count
python -m tgdata.smoke_tests.test_03_get_all_messages
python -m tgdata.smoke_tests.test_04_get_all_messages_in_batches

# Advanced tests
python -m tgdata.smoke_tests.test_06_advanced_features
python -m tgdata.smoke_tests.test_10_polling
```

### Custom Test Scripts:
- **my_test.py** - Custom test script for specific scenarios

## Important Notes

1. **Authentication Required**: All tests require valid Telegram credentials in `config.ini`

2. **Non-Destructive**: Tests only read data, they don't send messages or modify groups

3. **Rate Limits**: Tests respect Telegram's rate limits with appropriate delays

4. **Real Data**: Tests work with your actual Telegram groups, so results vary based on your account

## Configuration

Create a `config.ini` file in the project root:

```ini
[Telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
session_file = YOUR_USERNAME
phone = YOUR_PHONE_NUMBER
```

## Expected Results

Each test will show:
- ✓ for passed tests
- ✗ for failed tests
- Test-specific output (message counts, group names, etc.)

Tests are designed to be informative, showing real data from your Telegram account while validating the library's functionality.