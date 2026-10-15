# Batch-reader heartbeat

A large media download may take longer than a caller's stall timeout while still
making progress. Pass a quick synchronous `heartbeat(phase)` callback to observe
activity during a bounded read:

```python
import time

last_progress = time.monotonic()

def heartbeat(phase):
    global last_progress
    last_progress = time.monotonic()

batch = await tg.sync_group(
    chat_id, limit=200, download_media_to="media", heartbeat=heartbeat,
)
# Deliver the original batch durably before acknowledging it as usual.
```

A separate application watchdog compares the monotonic time since the last
callback with its silence limit. It must cancel and await the reading task when
that limit expires; tgdata does not create a watchdog or change acknowledgment.
Total read duration is not the silence duration.

The optional keyword defaults to `None` on `get_message_batch`, `sync_group` and
`prepare_backfill`, and on the corresponding `AccountPool` operations (including
`read`). Pool calls still require their normal caller-retained `capture`.
`SyncEngine.prepare`, `BackfillEngine.prepare` and `BatchEngine.fetch_batch`
forward it through the same source path. None is omitted from injected-reader
options, so existing custom readers without a heartbeat keyword still work.
A custom reader must accept and implement the callback when you explicitly use it.

## Signals and waits

Phases are diagnostic strings, not delivery receipts or reliable message/byte
counts. They include:

- `connect` / `connected`, `resolve` / `resolved`;
- `dialog-sync` / `dialog-sync done` on the entity-cache fallback;
- `message scanned` for observations, including those outside a fixed window;
- `messages` after a complete record has been prepared;
- `media` from Telethon's download progress callback after each chunk;
- `request`, `request done`, `request-error` and `flood-wait` from actual SDK
  request activity. An error phase reports activity, not success or recovery.

The SDK request observer preserves existing retry counts, flood thresholds and
budget charges. Consecutive flood-wait responses produce separate signals, so
several waits are not one uninterrupted silence. A cached wait has a request-start
signal before the SDK processes it. The pool continues to raise flood waits for
its existing routing policy; enabling heartbeat does not make it sleep/retry.

**Set the watchdog above the longest single allowed SDK sleep plus normal
latency.** Ordinary clients default to a 60-second flood threshold; a 120-second
watchdog allows that default. Telethon's own sleeps are unchanged. Heartbeat is
not a guaranteed periodic tick while a request is unanswered or the SDK is
sleeping. If you raise the SDK threshold, adjust the watchdog accordingly.

For waits that tgdata itself already owns during connection/authentication or
rate-limit handling, it emits `flood-wait` in slices of at most ten seconds and
`flood-wait done` afterward. No periodic task sends false progress while an RPC
is stuck. Local synchronous file verification, hashing/publication and custom
storage callbacks are not made asynchronous by this option.

## Observer and delivery contracts

Use a quick, nonblocking synchronous observer. Async functions/async-generator
callbacks and noncallables refuse before source/storage work. Unexpected
awaitable callback results are not awaited; returned coroutines are closed.
Callback exceptions are logged at WARNING with their type only, without message
contents or traceback, and ignored. They do not become Telegram health failures,
change a batch hash, replace a read error or affect completed-prefix publication.
Cancellation of the reading task still cancels the operation; a callback must not
perform application side effects such as cancelling tasks unless that is intended.

Callbacks are scoped to this read and its actual request results. Background or
unrelated concurrent tasks do not inherit them, and queued notifications stop
when the read exits. Callback execution is on the event-loop thread, including
request completion callbacks; do not assume `asyncio.current_task()` is always
available. No callback is persisted in progress/pool/session storage.

Pending daily/backfill replay uses saved data, performs no Telegram read and
requires no heartbeat. Download-mode replay still verifies local blobs. Enabling
heartbeat does not acknowledge a batch, advance a cursor, alter replay bytes,
refund budget or change the pool capture/cleanup contract.

## Verification

`python -m tgdata.smoke_tests.test_44_batch_heartbeat` uses real Telethon1.45.0
request/download loops and SQLite with synthetic wire replies and blocked sockets.
It covers a chunked download that outlasts the watchdog, a genuinely stalled
chunk, request waits, callback isolation, cancellation, replay and all pool APIs.
No live-account or deployed consumer validation is claimed. ScrapeOps must update
its dependency to a release containing this feature and forward `heartbeat=`
from its continuation watchdog; that adoption is a separate consumer change.
