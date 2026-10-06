---
model: gpt-6-astra
effort: max
---
# Fixed-window verification — 2026-10-06

Runtime: e87754e1717dc06f2b5232f3cb4d776bf0932d81.
Python3.11.10; Telethon1.45.0 only. Imports confirmed from the isolated #18 worktree.
Interpreter: /Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python.

## Results

| Suite | Offline groups passed | Live checks skipped |
|---|---:|---:|
| test23 fixed windows | 22 | 0 |
| test22 daily continuation | 25 | 0 |
| test19 message batches | 33 | 0 |
| test18 read budget | 28 | 0 |
| test17 session store | 12 | 0 |
| test16 health events | 21 | 0 |
| test15 login checks | 11 | 0 |
| test14 flood threshold | 11 | 0 |
| test13 device identity | 5 | 1 |
| test12 proxy | 5 | 2 |
| test11 explicitly awaited pure helpers | 2 | 0 |
| **Total** | **175** | **3** |

All final invocations exited0. Tests12/13 include skips in their printed7/7 and6/6;
the table excludes those3 checks from the175 passes. Other live suites and test11's
live discovery function were not invoked. The proxy's actual network use was localhost
only, with its refusing relay never forwarding to Telegram. No real config/account
was read. No 1.33.1 run or deployed receiver/live server acceptance is claimed.

Final compilation and Python3.7 AST grammar checks passed for six changed/new Python
files. Execution was on Python3.11 only, not a Python3.7 runtime receipt. Working and
staged diffs passed whitespace checks. All11 staged product paths were inspected;
work-folder notes were kept out of the runtime commit.

The existing offline daily example passed and reported four stored messages,
acknowledged through104, with the same batch replayed after a lost acknowledgment.

## New evidence

The new suite exercises real SDK request construction/iteration and guarded budget
resizing; replies are synthetic. It covers exact/fractional boundaries, timezone
normalization, inclusive ties over SDK and caller batch boundaries, excluded full
pages, sparse IDs, wire-date endpoints, empty/end/limit, and filtering before media.

Actual SQLite reload and subprocess exits before/after the real ack commit preserve
both dates and the appropriate pending/accepted state. Repeated relative enrollment
and ack do not read the clock. Commit-then-error and committed-then-cancelled setup
recover the original interval. Invalid v2 state/pending dates refuse without mutation
or network. Existing v1 serialization and default reader behavior remain covered.

Budget tests count excluded slots, distinguish failure from end, replay valid prefixes
without another read, and preserve the original failure when prefix storage succeeds.
A failed prefix save retains the read error through the existing read_error field.

## Corrections and limitations

The initial proxy attempt was blocked by sandbox localhost restrictions; the unchanged
suite passed with the required local-socket permission. The temporary test driver
also initially called two async discovery helpers without awaiting them. That output
is invalid evidence and excluded; the corrected awaited run below passed on the
committed code. No runtime fixes, architecture changes or expectation changes were
needed. A second test23 run followed added planned identity/after-ack assertions.

Logs: /private/tmp/tgdata18_fixed_windows_test23.log (initial22/22),
/private/tmp/tgdata18_fixed_window_*.log (existing suites; proxy initial attempt),
and test_11_helpers_corrected.log under that prefix (valid awaited helper result).
The final proxy/test23 receipts were tool output; these committed tests and this
record are the durable evidence. Temporary logs are not the archive.

## Reproduction

From this worktree with Telethon1.45.0:

```bash
python -m tgdata.smoke_tests.test_23_fixed_windows
python -m tgdata.smoke_tests.test_22_daily_continuation
python -m tgdata.smoke_tests.test_19_message_batches
python -m tgdata.smoke_tests.test_18_read_budget
python -m tgdata.smoke_tests.test_17_session_store
python -m tgdata.smoke_tests.test_16_health_events
python -m tgdata.smoke_tests.test_15_login_checks
python -m tgdata.smoke_tests.test_14_flood_threshold
python -m tgdata.smoke_tests.test_13_device_identity /path/that/does/not/exist.ini
python -m tgdata.smoke_tests.test_12_proxy /path/that/does/not/exist.ini
python examples/daily_continuation.py --demo
```

Run ONLY the two offline discovery helpers; their enclosing module main also runs
live discovery:

```python
import asyncio, socket
from unittest.mock import patch
from tgdata.smoke_tests.test_11_discover_groups import test_query_builder, test_empty_frame

async def main():
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        assert await test_query_builder() is True
        assert await test_empty_frame() is True

asyncio.run(main())
```

Merge-check and fresh PR critique are not replaced by this verification. No PR,
merge, release or issue closure was performed by this implementation run.
