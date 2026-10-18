# Optional concurrent media downloads

Downloads remain sequential by default. Pass `download_concurrency=3` to overlap
up to three message-attachment preparations:

```python
batch = await tg.get_message_batch(
    chat_id, after_id=last_id, limit=100,
    download_media_to="media", download_concurrency=3,
    heartbeat=heartbeat,
)

rows = await tg.get_messages(
    chat_id, limit=100, download_media_to="media",
    download_concurrency=3,
)
```

The option accepts integers from **1 through 16**, excluding booleans. Invalid
values raise `ValueError` before source or progress-store work. One follows the
existing inline path. Values above one are opt-in; three is an example to measure,
not a guaranteed safe account rate or promised speed multiplier.

The same keyword is available on `sync_group` and `prepare_backfill`, and on
`AccountPool.read`, `get_message_batch`, `sync_group` and `prepare_backfill`. Pool
calls still require their usual `capture`. Internal injected batch readers receive
no new keyword for the default value; to opt in, a custom reader must support it.

## What overlaps

Only message-attachment preparation overlaps. History pagination and sender/profile
photo enrichment remain sequential. Disk downloads and the legacy reader's
`include_media=True` mode support the option. If both disk and bytes are requested,
each worker prepares them sequentially, preserving both existing outputs.

The reader processes finite windows of at most N records. It settles the window
before starting another. This bounds active workers and results waiting behind a
slow earlier message. Windows also stop at legacy batch-callback boundaries: a
callback can stop the read or pause it without later downloads continuing behind it.

`download_media_by_id`, profile-photo parallelism and the worker job protocol are
unchanged. Reference-only reads validate the option but create no media workers.
The option does not speed up the chunks of one large file or promise a total memory
cap: the final DataFrame still holds all requested in-memory attachments.

## Ordering, failures and saved progress

Results retain source order even when files finish in another order. If the first
message fails while the third file succeeds, that third file does not authorize
advancing past the first message. A batch error retains only the fully prepared
ordered prefix in `partial_result`, following the existing cancellation/capture
rules of that reader. Message IDs may contain gaps; order refers to the observed
messages, not consecutive integers.

The default legacy reader keeps its existing best-effort media behavior. Above one,
media errors propagate instead of being swallowed, and `error.partial_result` holds
the prepared DataFrame prefix. Callback errors also propagate. Existing outer
legacy flood retries still apply; the batch/pool paths retain their current policy.

New opted-in disk files are written to temporary files and published under their
final name only after completion. Batch blobs remain content-addressed. Legacy
filenames remain based on chat/message IDs; known-extension cache entries retain
the existing reuse behavior. Old legacy cache entries are not newly authenticated
or hashed merely because concurrency is enabled. A simultaneous conflicting writer
cannot be silently overwritten by the opt-in publisher.

Some completed later files may remain after an earlier message fails. They are
artifacts, not delivery acknowledgments. Upload and acknowledge the original batch
using the existing daily/backfill contract. Changing this runtime option does not
change stored receipts, batch identity or a pending replay. Replay downloads nothing.

## Waits, cancellation and ownership

Owned requests share observed rate-limit deadlines. New affected requests and retries
check admission before being sent; requests already sent may finish. Telethon remains
the retry authority. Its configured wait threshold and retry bound remain in effect,
and pool clients still return wait errors rather than sleeping through them. There
is no independent retry loop per worker and no mutation of a shared client's policy.
SDK-created CDN helpers inherit the source's request policy for the opt-in span.

One ConnectionEngine admits one opted-in media operation at a time, including its
managed clients. A second one raises `RuntimeError` before source work. Wait for the
first operation to finish before starting another. Ordinary sequential calls and
independently configured engines are outside that local bound; applications must
coordinate simultaneous use of the same Telegram account. This is not a distributed
or account-wide rate limiter.

Cancellation stops owned workers once and awaits their cleanup, including borrowed
exported download iterators and SDK-created CDN clients. Repeated cancellation does
not detach cleanup. The original failure or caller cancellation is preserved. A
cleanup failure alone is a local `RuntimeError`; it does not become an account-health
verdict. A client whose media-resource cleanup failed refuses further opted-in reads
until it is closed and replaced. Cleanup has no hard time guarantee if the underlying
SDK cleanup cannot finish.

Only explicitly owned tasks share health and heartbeat observations. Nested reads
start with their own media context; inherited SDK background tasks are not enrolled.
Real download progress and deliberate gate waits emit heartbeats. With a finite
window, completed later downloads cannot continually refill work to hide a stalled
first download. Callers still own their watchdog and must cancel **and await** the
read. No synthetic progress is emitted for an unanswered request.

The native integration is qualified with **Telethon 1.45.0**. Re-run its tests when
upgrading Telethon, especially request waits and exported/CDN cleanup.

## Measure before enabling in an application

Use a separately authorized read-only benchmark on an existing accessible group,
with the account's existing allowance and no overlapping scraper. Do not join,
send messages, change configuration or induce flooding for the measurement.

1. Choose an explicit small message range and a maximum message/media-byte allowance.
   Record the account, SDK version, group, boundaries and time; keep credentials out
   of the report. A dry reference-only read can identify the candidate media set, but
   it still spends the normal read allowance.
2. Compare the same bounded media set at one and three, using different empty output
   folders so local cache hits cannot make one run appear faster. Record any history
   changes or mismatched file counts instead of comparing unlike runs.
3. Record total elapsed time, completed file count/bytes, files per minute, bytes per
   second, errors and observed rate waits. The offline suite checks the configured
   concurrency bound; add transport-level instrumentation if measuring actual peak
   active transfers live rather than inferring it from heartbeat counts.
4. Stop on a rate-limit answer or unexpected health event, retain its mandated wait,
   and do not retry immediately or rotate accounts. Use the existing cancel-and-await
   watchdog so a stalled read does not leave downloads running.
5. Report the observed difference and conditions. Do not infer a universal speedup
   or safeN from one account/network. Leave the application at one until its operator
   chooses to enable the option.

No live benchmark is run automatically by the offline smoke test.
