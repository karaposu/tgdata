## New in 0.1.2

- **Richer group profiles:** `get_group_profile()` returns descriptions, available member/online-count observations and bounded readable pinned messages with their IDs, tied to a verified account.
- **Activity and engagement measurement:** `measure_group_activity()` measures a bounded time window, including messages, distinct observed authors, daily activity and available views, reactions, forwards and replies. Results retain coverage and missing-data information.
- **Terminal account login:** `tgdata-login --config config.ini` drives the existing phone → code → optional 2FA flow and saves a reusable native session. Existing files are protected by default; `--replace` requires explicit confirmation. Hidden input is bounded to 128 UTF-8 bytes per value, with supported-terminal checks and cancellation-safe retirement on the qualified POSIX path. Local save retry does not request another login code.

```bash
pip install tgdata==0.1.2
```

The reader, account pool, continuation/backfill, albums, photo trails and batch heartbeats remain available. Telethon requirement remains `>=1.45,<2.0`; qualification used 1.45.0.

Validation: 1,013 offline checks across 34 suites and seven demos passed on Python 3.11.10; three live checks were skipped. Both wheel and source distribution were compared with the qualified source, and isolated installation checked both generated commands and the native-SRP interruption path. Native Python 3.7, additional terminal hosts and live Telegram delivery/real-account 2FA are not newly qualified by this release.

Includes reviewed PRs #47, #48 and #51. Release source is the verified `main` commit named by this tag; publication and downloaded-artifact verification are tracked in #52.

[Full changes since 0.1.1](https://github.com/karaposu/tgdata/compare/v0.1.1...v0.1.2)

Verified source: [main eaa2f2b](https://github.com/karaposu/tgdata/commit/eaa2f2b659d83e249325f76fcb83857389ded020), following version PR #53 and promotion PR #54.
