# Fixed historical windows

A historical collection uses the same progress store, `sync_group` and explicit
acknowledgment as [daily continuation](daily_continuation.md). Its dates are saved
once. Restarting tomorrow continues the same interval.

## Last N days

```python
from tgdata import TgData, SQLiteSyncStore

tg = TgData("config.ini", interactive_login=False,
            sync_store=SQLiteSyncStore("historical-progress.sqlite3"))
chat_id = -1001234567890
try:
    # First enrollment resolves the dates. Matching repeated setup reuses them.
    status = await tg.initialize_sync(chat_id, after_id=0, last_days=30)
    print(status.start_date, status.end_date)
    batch = await tg.sync_group(chat_id, limit=200)
    if batch is not None:
        await destination.accept(batch)  # your durable, repeat-safe destination
        await tg.acknowledge_sync(chat_id, batch.batch_id)
finally:
    await tg.close()
```

`last_days` is a positive integer, each day exactly 24 hours. At first enrollment,
tgdata observes the UTC clock once, sets `end_date` to that instant and subtracts
the duration for `start_date`. It saves both with the initial progress record.
Repeating the same request loads the saved dates without reading the clock, even
if no message has yet been fetched. Retry after an uncertain committed enrollment
therefore reuses the original dates.

`SQLiteSyncStore` creates its file and tables on initial setup; the parent directory
must already exist. Reopen the same file on later invocations. Custom stores use the
existing opaque-text `load`/`compare_and_swap` contract. The application chooses the
storage and retains its permanent archive; tgdata keeps progress and one pending
observation per group/store.

## Explicit dates

For calendar-day boundaries or a specific historical interval, supply both dates:

```python
from datetime import datetime, timezone

await tg.initialize_sync(
    chat_id, after_id=0,
    start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
    end_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
)
```

This is an alternative initial enrollment, not a replacement for the preceding
30-day collection. Dates must be timezone-aware `datetime` values. Other offsets
normalize to UTC. Naive dates, strings, equal/reversed bounds and a single bound
are rejected. Bounds must be within `1970-01-01T00:00:00Z` through
`2038-01-19T03:14:07Z`, the nonnegative signed-32-bit Unix date range used here for
SDK offsets. A relative duration that cannot form such a window is rejected too.
Microseconds are retained in the predicate and saved state.

The range is **start inclusive, end exclusive**: `start_date <= message.date < end_date`.
`after_id` remains required. Zero starts at the window's first visible message;
a nonzero ID intersects the range with `message.id > after_id`. Continuation uses
IDs, so messages sharing a timestamp can span batches without losing the remaining
messages at that time.

## Restart and query identity

After enrollment, call `sync_group(chat_id)` without dates. It loads the saved
window and position. Pending batches replay exactly without Telegram or budget use.
Acknowledgment preserves the dates and advances only to the pending batch's last
completely prepared message.

Repeated initialization must use the original input form and settings:

- Relative: the same `last_days`, initial `after_id` and `media_mode`.
- Explicit: the same normalized dates, initial `after_id` and `media_mode`.

Changing the query, switching input forms, omitting a configured window, or adding
one to an existing daily collection raises `SyncConflictError`. Mixing `last_days`
with dates is invalid. No call resets or rolls a collection forward. Another
interval needs another collection/store; no reset/re-arm or named-job API is added.

For a group with both daily and historical reads, use separate stores, for example
`daily-progress.sqlite3` and `historical-progress.sqlite3`, with their corresponding
`TgData` instances. Their bookmarks advance independently. Receivers should deduplicate
by `(chat_id, message.id)` as well as batch ID because collections can overlap.
One active reader per group/store is supported.

`get_sync_status` exposes immutable `start_date`, `end_date` and `last_days`
attributes, all None for a daily collection. `to_dict()` adds these fields only for
window collections, using canonical UTC strings for dates; existing daily dictionaries
retain their keys. Status includes no message contents.

## Limits, end and failures

Each call returns at most `limit` included records. The initial zero-cursor read
uses a date offset; subsequent reads use the saved ID. The SDK offset is exclusive
and second-precision, so tgdata seeks slightly earlier and applies the exact predicate.
A full page of excluded records is followed by another bounded page, rather than
reported as empty history. An arbitrary nonzero initial ID below the window can
require extra scans before reaching its start.

Filtered slots spend normal read budget. A page can contain slots beyond the end
although they are not delivered. Excluded messages do not trigger media downloads.
In-window media retains the existing download and verified pending-replay contract.

`None` means no included messages were found after the accepted cursor. A nonempty
batch with `stop_reason="end"` means the reader reached the end bound or exhausted
currently visible history before filling the batch; it still needs acknowledgment.
An exact full batch has `stop_reason="limit"`; another call may be needed to discover
the end. There is no permanent completed-job marker, background loop or pacing.

Budget exhaustion and read failures raise, even if every returned slot was filtered
out. A nonempty completed in-window prefix is saved before the original error is
re-raised. Failed prefix persistence follows the existing `SyncError.read_error`
contract. Missing message dates fail rather than being guessed. Cancellation never
acknowledges; store failure never means an empty/new collection.

The dates freeze a query, not Telegram's contents or visibility. Existing exclusions
for edits/deletions and account-dependent history remain. Planned backfill scheduling,
pacing and run completion are later #18 work.

## Direct reads and compatibility

Callers managing their own progress can use the same selection on raw batches:

```python
batch = await tg.get_message_batch(
    chat_id, after_id=last_accepted_id, limit=200,
    start_date=start, end_date=end,
)
```

`last_days` is an enrollment convenience, not a raw-batch argument. Batch v1 contains
observation fields, not query dates; retain the query separately for direct reads.
`sync_group` does that in its store.

Omitting date options retains existing batch/daily behavior. Legacy DataFrame date
semantics are unchanged. Daily progress stays in state v1; window progress uses
state v2 with validated dates and optional relative input. SQL schema and custom-store
protocol do not change. Older code rejects window records rather than reading them
as unbounded daily progress. Pending records are checked against their window before
publication and on reload.

Verification targets Telethon **1.45.0**, with its actual iterator, budget adapter and
real SQLite. Synthetic transport and blocked sockets do not establish live server
selection, account visibility or deployed receiver guarantees.
