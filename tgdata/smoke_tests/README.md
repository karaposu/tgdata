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

### 8. **test_11_discover_groups.py**
Tests group discovery (`python -m tgdata.smoke_tests.test_11_discover_groups [config.ini]`):
- `build_search_queries` and the empty/unresolved frame shapes (no network)
- `search_groups`, `similar_groups`, `linked_groups` (unresolved, then resolved with a budget of 3)
- `discover_groups` with `found_callback`, `heartbeat` and the link-source cap
- a `get_messages` round-trip on a discovered room

Cost: about a dozen requests and three username resolutions on the live account. Do not scale it up.

### 9. **test_12_proxy.py**
Tests proxy support (`python -m tgdata.smoke_tests.test_12_proxy [config.ini]`):
- proxy URL parsing, masking, and the forms that are refused (no network)
- config loading: no key = direct, `require_proxy` refusal, inline comments, password kept out of `repr` (no network)
- every client (main and pool) is built with the proxy (no network)
- a dead proxy and a proxy that refuses the tunnel both FAIL; nothing falls back to a direct line (loopback only)
- a local SOCKS5 relay with a user name and password carries a full round trip to Telegram for a throwaway, never-logged-in session
- a real proxy from the config, when the config has a `proxy` key (pending a real proxy)

Items 3–6 need `pip install 'tgdata[proxy]'`. Item 6 reads only `api_id`/`api_hash` from the config; the account's own session is never opened.

### 10. **test_13_device_identity.py**
Tests the fixed device identity (`python -m tgdata.smoke_tests.test_13_device_identity [config.ini]`):
- no keys: Telethon's machine defaults, unchanged (no network)
- pinned keys presented as written: spaces kept, quotes and inline comments stripped, `lang_code` alone sets `system_lang_code` (no network)
- the use-and-close, persistent and pool clients all carry it — driven through the real code paths with a stand-in client that refuses to connect (no network)
- `device_identity()`: pasting its `config_lines` back pins exactly the same identity (no network)
- `health_check()` reports the presented identity (no network)
- Telegram accepts a connection presenting a pinned identity (throwaway session, no login)

Whether Telegram's active-sessions list *shows* the pinned values needs a logged-in account and is not checked here.

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