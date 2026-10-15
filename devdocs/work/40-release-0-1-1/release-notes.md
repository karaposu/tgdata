## New in 0.1.1

- **Album assembly across batches:** `TelegramPost` and `assemble_albums()` retain original messages, captions and media references, with caller-owned persistence and replay support.
- **Optional photo trails:** `PhotoTrailPolicy` and `fold_photo_trails()` associate following photos in a provisional view. Disabled by default; later observations can withdraw an association without losing originals.
- **Batch heartbeats:** optional synchronous `heartbeat(phase)` on direct batch reads, daily continuation, backfill preparation and account-pool reads. Real media-chunk/message/request progress lets caller watchdogs distinguish slow downloads from silent reads. Callback errors are isolated; source receipts, budgets and retry policy remain unchanged.

Heartbeat does not change Telegram's allowed SDK waits. Configure the watchdog above a single allowed wait plus ordinary latency; [the guide](https://github.com/karaposu/tgdata/blob/v0.1.1/docs/batch_heartbeat.md) explains the contract.

Validated on Python 3.11.10 / Telethon 1.45.0: 914 offline checks across 31 suites and seven demos passed; three live checks skipped. Wheel/sdist contents and isolated installation were checked against the reviewed source. Tests used synthetic Telegram responses.

Source: reviewed main commit [2e6edf2](https://github.com/karaposu/tgdata/commit/2e6edf2a3b2c016f9fea4a43b5edffd25fc9cf8e), following PRs #35, #36 and #38, and release-version PRs #41 and #42.

```bash
pip install tgdata==0.1.1
```

[Full changes since 0.1](https://github.com/karaposu/tgdata/compare/v0.1...v0.1.1)
