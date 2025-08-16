# Smoke Tests for Telegram Group Message Crawler

This directory contains smoke tests for the new implementation of the Telegram Group Message Crawler.

## Test Coverage

### 1. **test_01_connection.py**
Tests the `TelegramConnection` class:
- Connection initialization
- Connecting to Telegram
- Retry logic
- Connection validation
- Ensure connected functionality

### 2. **test_02_tgdata.py**
Tests the base `TgData` class:
- Group initialization
- Listing groups (requires authentication)
- Setting group ID
- Message filtering
- Export functionality (CSV/JSON)

### 3. **test_03_message_tracker.py**
Tests the `MessageTracker` class:
- Database initialization
- Message tracking and deduplication
- Batch processing
- Checkpointing system
- Progress tracking
- Statistics calculation

### 4. **test_04_advanced_features.py**
Tests advanced TgData features:
- Enhanced initialization with all features
- Health check functionality
- Date-based filtering
- Metrics export
- Resumable operations
- Connection validation
- Inheritance verification

## Running Tests

### Run All Tests:
```bash
python -m tgdata.smoke_tests.run_all_tests
```

### Run Individual Test Suite:
```bash
python -m tgdata.smoke_tests.test_01_connection
python -m tgdata.smoke_tests.test_02_tgdata
python -m tgdata.smoke_tests.test_03_message_tracker
python -m tgdata.smoke_tests.test_04_advanced_features
```

## Important Notes

1. **Authentication Required**: Some tests (like listing groups) require valid Telegram credentials in `config.ini`

2. **Non-Destructive**: All tests use temporary files and don't affect your actual data

3. **Smoke Tests**: These are basic functionality tests, not comprehensive unit tests

4. **Expected Failures**: Some tests may skip if authentication is not available

## Test Results

Each test will show:
- ✓ for passed tests
- ✗ for failed tests
- ! for skipped tests (usually due to authentication)

The test runner will exit with:
- 0 if all tests pass
- 1 if any test fails