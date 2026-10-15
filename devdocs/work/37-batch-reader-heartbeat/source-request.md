# Request to tgdata: a heartbeat on the batch reader

**From:** flatmir-scrapeops issue #21 (reading positions on tgdata's daily continuation), 2026-10-14.
**For:** NS, as tgdata's maintainer. Carry it into tgdata's own pipeline as you see fit. Nothing has been filed or pushed.

## Why

ScrapeOps' collector cancels a read that stays silent for 120 seconds (`FETCH_STALL_TIMEOUT_S`). Silence, not duration, is its hang signal. tgdata's row reader supports this today: `get_messages(heartbeat=...)` beats on every message, every media chunk (Telethon's `progress_callback` inside `_download_or_reuse`), sliced sleeps and dialog sync.

The batch reader behind daily continuation has no such signal.
- `batch_engine.fetch_batch` downloads each blob through `download_blob(media_directory, writer, ...)`, where `writer` is `client.download_media(message, file=output)` with no progress callback.
- `get_message_batch` and `sync_group` take no heartbeat parameter. On 0.1, `sync_group(..., heartbeat=...)` raises `TypeError: ProgressFacade.sync_group() got an unexpected keyword argument 'heartbeat'` (probed 2026-10-14).

In download mode, a batch holding a large video is silent for the whole download. ScrapeOps' watchdog cancels it. A cancelled read saves nothing ("Cancellation propagates, never acknowledges, and does not promise a saved partial prefix"), so the same batch is read again and cancelled again on every try. The group never moves.

NS chose download-mode continuation for #21 (design β), so #21's media steps depend on this change.

## The request

1. **A parameter.** `heartbeat: Optional[Callable[[str], None]] = None` on:
   - `BatchEngine.fetch_batch`;
   - `TgData.get_message_batch`;
   - `TgData.sync_group`, with `SyncEngine.prepare` forwarding it to its `read_batch`.

   AccountPool's `sync_group` should mirror it.
2. **Beat phases,** matching the row reader's names where they mean the same thing:
   - `"messages"`, once per record prepared;
   - `"media"`, per downloaded chunk, via Telethon's `download_media(..., progress_callback=...)` inside `download_blob`'s writer;
   - one beat around entity resolution, including the dialog-sync fallback (`"dialog-sync"` / `"dialog-sync done"` as in `message_engine`).
3. **Waits.** tgdata's primary client keeps Telethon's default `flood_sleep_threshold` of 60 seconds, so waits up to 60 s are slept silently inside Telethon. Two such waits in one batch could exceed a 120-second silence watchdog. Please beat around waits as well, for example by slicing them like the row reader's "sliced designed sleeps". The mechanism is tgdata's choice.
4. **Callback errors.** An exception raised by the heartbeat callback is logged and ignored. It must not change the batch, the pending state, or the partial-result and error contract.
5. **Replay.** Replaying a pending batch opens no client and reads nothing, so it needs no beats. (It may beat once; ScrapeOps does not depend on it.)
6. **Tests:**
   - beats observed during a scripted slow download, chunk by chunk;
   - no read and no beat requirement on replay;
   - a raising callback leaves the batch and pending state unchanged.

## Optional: author and chat metadata in batches

Not needed for #21, but it would simplify every batch consumer.

**Today's gap:** MessageBatch v1 records the wire `from_id` only, so the two readers disagree on authors:
- broadcast-channel posts get `sender.id = None`;
- posts sent as a channel get a marked id (`-100…`);
- usernames carry no `@`.

The row reader uses `msg.get_sender()`, which returns the channel for broadcast posts.

**The request** (a format version, so consumers stop re-deriving `get_sender` semantics):
- a resolved author for broadcast posts;
- the chat's username and type in batch metadata.

#21 maps these itself in the meantime (critic Risks 1 and 5).

## What ScrapeOps will do once it is released

1. Bump `requirements.txt` to the release.
2. Pass `heartbeat=` into `sync_group` from the collector's watchdog.
3. Add an integration test where a scripted batch's download outlasts the watchdog tick but beats per chunk and completes (#21 plan, Step 13).
4. Deploy only after the release (#21 plan, Step 17).
