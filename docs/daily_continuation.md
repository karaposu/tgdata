# Daily continuation with explicit acknowledgment

Daily continuation is the first delivery of #18. It keeps one acknowledged
message position and at most one pending `MessageBatch` per group in a progress
store. The caller schedules runs and saves/uploads the data. Each library call
prepares or replays one bounded batch; there is no background loop.

```python
from tgdata import TgData, SQLiteSyncStore

chat_id = -1001234567890  # canonical marked ID, as returned by MessageBatch.chat_id
tg = TgData("config.ini", interactive_login=False,
            sync_store=SQLiteSyncStore("daily-progress.sqlite3"))

# Enrollment: do this once with your archive's last accepted message ID.
# Matching repeated enrollment is harmless and does not reset later progress.
await tg.initialize_sync(chat_id, after_id=48213)

try:
    for _ in range(10):  # caller-selected amount of work for this invocation
        batch = await tg.sync_group(chat_id, limit=200)
        if batch is None:
            break
        await destination.accept(batch)  # YOUR durable, repeat-safe destination
        await tg.acknowledge_sync(chat_id, batch.batch_id)
        if batch.stop_reason == "end":
            break
finally:
    await tg.close()
```

`destination.accept` above is an application function, not a tgdata API. A runnable
SQLite destination example, including an offline demonstration, is in
[`examples/daily_continuation.py`](../examples/daily_continuation.py):

```bash
python examples/daily_continuation.py --demo
```

The demo uses synthetic batches and forbids sockets. It saves a batch, simulates
a lost acknowledgment, restarts, replays without fetching, and stores four messages
once. Normal example mode requires an explicit directory/group and an already
logged-in account; see the script's `--help`. The example stores references only
and uses one SQLite file for destination records and progress.

## Enrollment and group identity

All four methods require `TgData(..., sync_store=store)`. Without it they raise
`SyncConfigurationError`; existing TgData methods keep their behavior.

Use a negative canonical marked group ID, the integer `MessageBatch.chat_id`.
Positive IDs from other interfaces, numeric strings and usernames are rejected
here because they can be ambiguous or change their referent. If you only have a
username, a one-time existing `get_message_batch(username, after_id=known_position,
limit=1)` gives its canonical `chat_id`. That setup read spends the normal read
allowance and does not enroll or advance progress; reuse an existing batch's ID
when available.

`initialize_sync(chat_id, *, after_id, media_mode="references")` requires an
explicit integer position in `0..2147483647`. Zero deliberately begins at the
oldest currently visible history. Import the last *accepted* ID from an existing
archive to continue it. No implicit current-head or last-24-hours policy exists.

The initial ID and media mode are retained. Calling initialize again with those
same values returns current status; changing either raises `SyncConflictError`.
There is no reset/delete API. Use separate stores for independent destinations or
collections. One store's position must not be reused for a destination that never
received the earlier data.

Progress belongs to the canonical group, independently of the account that reads
it. Another account must still resolve/read that group through the existing batch
API. Different accounts may see different history; a stored cursor is not proof
of complete Telegram history. Basic-group/channel migrations are not automatically
treated as the same source.

## Prepare, replay and acknowledge

`sync_group(chat_id, *, limit=200, download_media_to=None)` returns a nonempty
`MessageBatch` after persisting it as pending. `limit` is an integer in `1..10000`.
If pending work already exists, it returns that exact observation first, even if
the new limit is smaller. Replay opens no client and spends no read allowance.

Preparing does not advance `after_id`. A fresh read starts strictly after the
last acknowledged position and uses `get_message_batch`, including its configured
proxy, session, read budget and health reporting. `current_group` is unchanged.
Missed days accumulate work after that bookmark; they do not change the query to
“the last day.”

`None` means the current read found no new visible messages. It creates no pending
batch and advances no position. Call again on the next scheduled run. A nonempty
batch with `stop_reason="end"` also needs acknowledgment; “end” describes current
visible history, not a permanent completion state.

`acknowledge_sync(chat_id, batch_id)` asserts that the destination durably accepted
the entire batch and its requested artifacts. It derives the next position from
the saved batch, then atomically advances progress and clears pending work.
The caller never supplies a replacement cursor.

Repeating the latest acknowledged ID is harmless, including when a newer batch
is pending. An older, wrong or nonexistent batch ID raises `SyncConflictError`
without changing state. Only the latest acknowledgment ID is retained; the reader
is not an unlimited receipt archive. Status/reload resolves an uncertain response
after a storage write; a raised error or cancellation does not prove rollback.

## Destination acceptance and duplicates

Commit the destination's effects and duplicate markers in the same transaction
before acknowledging. A destination that accepted a batch but lost its response
must safely recognize the resent `batch_id`. Different batches can overlap, so
message storage also needs a key such as `(chat_id, message.id)`.

The example uses both keys and ignores already stored messages, consistent with
the user's exclusion of edit reconciliation. Tgdata supplies no upload service
or exactly-once downstream-effect guarantee. Its acknowledgment is the caller's
assertion; the library cannot verify a remote database commit.

## Partial reads, errors and cancellation

A read error can carry a nonempty completed `MessageBatch` in `partial_result`.
`sync_group` saves that prefix as pending, then re-raises the same error. This
matters when the read budget ends before the requested batch size is reached:
the completed prefix can still be delivered and acknowledged.

```python
from tgdata import MessageBatch, ReadBudgetExceeded

try:
    batch = await tg.sync_group(chat_id, limit=200)
except ReadBudgetExceeded as error:
    partial = error.partial_result
    if isinstance(partial, MessageBatch) and partial.messages:
        await destination.accept(partial)
        await tg.acknowledge_sync(chat_id, partial.batch_id)
    raise  # let your scheduler apply the budget's stopping/retry policy
```

If validating or saving a prefix fails, a local `SyncError` is raised instead,
with the original read exception in `read_error`. Do not assume that exception's
prefix is durably pending; retry `sync_group` to reload authoritative state.
The accepted position has not been advanced by preparation. A backend may have
committed pending output before its response failed, so the next call can replay it.

An error before any complete record leaves no new pending batch. Cancellation
propagates, never acknowledges, and does not promise a saved partial prefix.
Already committed pending state survives and can be replayed.

`SyncConfigurationError` covers invalid input/backend configuration;
`SyncNotInitializedError` covers an unenrolled group; `SyncConflictError` covers
state conflicts or overlapping preparation; `SyncStorageError` covers unavailable,
unsupported or invalid stored state/backend failures. These inherit `SyncError`.
They suppress incidental exception context so an old Telegram error is not mistaken
for the cause of a local storage failure. Existing batch/media failures retain their
documented types. Secondary SQLite cleanup failures log only operation/type and
preserve the active primary error; a cleanup-only error remains visible.

## Optional downloaded media

Enroll with `media_mode="download"`, then supply `download_media_to` on every sync
call. The existing batch downloader writes complete hash-named blobs. Pending
replay checks each distinct blob's regular-file status, size and digest under that
directory before returning the saved batch.

Missing, corrupt or symlink blobs raise while leaving the pending record intact.
Tgdata never downgrades it to references or downloads replacement observations.
Reference-only enrollment rejects a media directory; changing modes requires a
separate collection.

For a sequential machine move, make the same progress state and pending blobs
available on the new machine; the local directory name may differ. Acknowledge
only after the destination has accepted both manifest and requested blobs. No
automatic media transfer or deletion occurs. The application owns retention and
cleanup, including possible unreferenced complete blobs after interrupted reads.

## Status and storage contract

`get_sync_status(chat_id)` returns immutable `SyncStatus`, or None only when no
record exists. Its fields are `chat_id`, `initial_after_id`, `after_id`, `media_mode`,
`pending_batch_id`, `pending_message_count`, `pending_next_after_id` and
`last_acked_batch_id`. `to_dict()` returns an independent JSON-ready dictionary
with IDs encoded as strings. Status contains no message contents.

A custom backend implements exactly these two asynchronous methods:

```python
class ProgressStore:
    async def load(self, chat_id):
        # Return opaque saved text or None if absent. Raise on storage failure.
        ...

    async def compare_and_swap(self, chat_id, expected, data):
        # Atomically compare saved text with expected (None means absent).
        # On a match durably write data and return True.
        # Otherwise leave the record untouched and return False.
        ...
```

Store text without parsing it; schema/version checks and domain transitions belong
to tgdata. A successful replacement must be durable before returning. Do not turn
an outage into None, use write-behind, or implement comparison and writing as two
unprotected requests. The interface is asynchronous so remote implementations can
await their database, but no remote backend is bundled in this delivery.

`SQLiteSyncStore(path)` uses two namespaced tables and short transactions, without
holding a connection across an await. Its async methods currently perform synchronous
local SQLite I/O and can wait up to five seconds on contention. The parent directory
must exist; in-memory databases and URI connection strings are refused. Normal
operations refuse a deleted database or missing/unsupported schema rather than
silently creating fresh progress. Pending records contain message content; storage
access control and encryption are the application's responsibility.

The supported operating condition is one active reader per group/store. Same-instance
overlapping preparation is rejected. Conditional updates prevent stale overwrite,
but do not implement leases, failover or coordinated reading across machines.

The internal state format is versioned and opaque. It stores the canonical source,
initial and accepted positions, media mode, pending batch and latest acknowledgment
together. Batch v1 itself is unchanged. Backfill and its independent progress remain
for #18's later delivery; old edits and deletions are excluded permanently.
