# Issue #1: Message Skipping During Polling

## Problem Description

When polling for new messages in Telegram groups, some messages are being completely skipped and never delivered to the callback function. This results in data loss where certain messages are permanently missed.

### Example Scenario

When sending messages numbered 1-14 rapidly to a Telegram group:
- Messages sent: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
- Messages received by polling:
  - Poll 1: 1, 2, 3, 4, 5 (missed 6)
  - Poll 2: 7, 8, 9, 10, 11, 12 (missed 13)
  - Poll 3: 14

Messages 6 and 13 were completely lost and never delivered to the callback.

## Root Cause Analysis

### 1. Telegram API Behavior with `min_id`

The Telegram API's `iter_messages()` method with `min_id` parameter doesn't guarantee returning ALL messages with ID >= min_id. Instead, it appears to:
- Return a subset of available messages
- Use internal pagination or buffering
- Have eventual consistency issues when messages arrive rapidly

### 2. Naive Polling Logic

The original polling implementation had a critical flaw:
```python
# Original problematic logic
if not new_messages.empty:
    max_id = new_messages['MessageId'].max()
    current_after_id = max_id  # PROBLEM: Assumes all messages between old and new were returned
```

This assumes that if we get messages [1, 2, 3, 5, 7], all messages between 1 and 7 were returned. But message 4 and 6 might exist and simply weren't included in this particular API response.

### 3. Caching Issues

The message engine had a caching mechanism that would return stale data:
```python
# Problematic caching
if use_cache and min_id is None and cache_key in self._message_cache:
    return self._message_cache[cache_key]  # Returns old data!
```

This caused the polling to sometimes get cached results instead of fresh data from Telegram.

## Why Messages Get Skipped

The skipping occurs due to a combination of factors:

1. **Race Condition**: When messages arrive while a query is being processed, Telegram's API might not include them in the response
2. **Non-contiguous Returns**: The API might return messages [204083, 204084, 204085, 204087, 204089] skipping 204086 and 204088
3. **Aggressive after_id Updates**: Updating to the max ID seen (204089) means we'll never query for 204086 and 204088 again

## Solutions Implemented

### 1. Removed Caching
- Eliminated the entire caching mechanism as it doesn't make sense for real-time message data
- Messages are immutable once created, and new ones arrive constantly
- Users can implement their own caching if needed

### 2. Contiguous ID Tracking
- Only advance `current_after_id` to the highest contiguous message ID
- If we receive [1, 2, 3, 5, 7], only advance to 3, not 7
- This ensures we'll re-query for message 4 in the next poll

### 3. Duplicate Filtering
- Track all seen message IDs in a set
- Filter out duplicates before calling the user's callback
- Ensures callbacks only receive truly new messages

### 4. Updated Polling Logic
```python
# New robust logic
seen_message_ids = set()  # Track what we've processed

# In each poll:
new_message_ids = [id for id in all_ids if id not in seen_message_ids]
truly_new_messages = messages[messages['MessageId'].isin(new_message_ids)]
seen_message_ids.update(new_message_ids)

# Only advance after_id to highest contiguous ID
for msg_id in sorted(all_message_ids):
    if msg_id == expected_id:
        highest_contiguous = msg_id
        expected_id = msg_id + 1
    elif msg_id > expected_id:
        # Gap detected - will re-poll
        break

current_after_id = highest_contiguous
```

## Current Status

With the implemented fixes:
- ✅ Callbacks don't receive duplicates (duplicate filtering works)
- ✅ Polling advances correctly (no longer stuck on old IDs)
- ❌ **Messages are still being missed** due to Telegram API limitations
- ⚠️ Telegram's `iter_messages` with `min_id` doesn't guarantee returning all messages
- ⚠️ This appears to be an inherent Telegram API issue, not fixable client-side

## Recommendations for Users

1. **Use real-time events instead of polling** - The `on_new_message()` decorator is more reliable for real-time updates
2. **For polling, expect some message loss** - Especially when messages arrive rapidly
3. **Implement periodic full fetches** - Periodically fetch all recent messages to catch any missed ones
4. **Message IDs are your source of truth** - Always use the `MessageId` field to identify unique messages
5. **Consider longer polling intervals** - Give Telegram's API time to stabilize before querying

## Future Improvements

1. Consider implementing a sliding window approach for more efficient gap detection
2. Add configurable strategies for handling gaps (aggressive vs conservative)
3. Implement exponential backoff when gaps are detected repeatedly
4. Add metrics/monitoring for gap detection frequency

## Test Command

To reproduce and test the issue:
```bash
python -m tgdata.smoke_tests.test_06_polling_simple
```

Then rapidly send numbered messages to the test group during polling.