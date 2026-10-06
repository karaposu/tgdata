---
model: gpt-6-astra
effort: max
---

# Verification — #18 daily continuation

Runtime commit: `d096442cb1b0a2e482d42f1a8f18ed5c023d7b33`.
Python 3.11.10, Telethon 1.45.0. Import path was explicitly confirmed as
`/private/tmp/tgdata-18-daily-group-continuation/tgdata/__init__.py`.
Interpreter: `/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python`.

## Results

| Suite | Offline groups passed | Live checks skipped |
|---|---:|---:|
| test_22_daily_continuation | 25 | 0 |
| test_19_message_batches | 33 | 0 |
| test_18_read_budget | 28 | 0 |
| test_17_session_store | 12 | 0 |
| test_16_health_events | 21 | 0 |
| test_15_login_checks | 11 | 0 |
| test_14_flood_threshold | 11 | 0 |
| test_13_device_identity | 5 | 1 |
| test_12_proxy | 5 | 2 |
| test_11 query-builder and empty-frame helpers only | 2 | 0 |
| **Total** | **153** | **3** |

Every executed suite/process exited 0. Tests 12/13 print 7/7 and 6/6 because their
runners count explicit skips as successful outcomes; the table above excludes those
three skips from the offline pass count. A verified nonexistent config path,
`/private/tmp/tgdata18-no-live-config.ini`, was supplied to both. Proxy checks used
localhost only. Legacy live suites and test 11's live function were not invoked.

The final new-suite result is 25/25 after the fixture correction and malformed-NULL
row regression documented in implementation.md. Existing suites passed before the
last isolated new-backend validation correction; the new suite and grammar/compile
checks were repeated after it. No existing runtime path was changed by that correction.

Compilation and Python 3.7 grammar parsing passed for all six changed/new Python
files. Runtime execution was Python 3.11 only; this is not a Python 3.7 runtime receipt.
git diff --check and staged-diff whitespace checks passed. Only the nine intended
product/test/doc/example paths were staged in the runtime commit.

## Runnable example

Executed the documented command with no supplied directory:

```text
python examples/daily_continuation.py --demo
Destination accepted the batch; acknowledgment was lost.
Replay used the same batch without reading Telegram.
Stored messages: 4
Acknowledged through: 104
```

The new suite also runs the demo in an explicit temporary directory. The demo uses
synthetic batch input and actual sync/receiver SQLite code, with sockets forbidden.
SDK behavior is tested separately through real Telethon request/iterator code with
scripted transport, not inferred from that demo.

## Durable failure evidence

The new suite terminates subprocesses inside the actual acknowledgment transaction
before and after commit. Reopening observes respectively the old pending batch or
the fully advanced cursor, never a half-transition. A separate real SQLite receiver
accepts a batch, loses its response, then accepts the identical replay without a
second record effect. Cancellation after a committed store write leaves pending
state discoverable. These tests exercise actual persistence rather than a fake
store returning expected values.

The pre-build component probes recorded seven observations; the plan critic added
three observations on uncertain commit and relocated/corrupt media. Those are
separate design evidence, not added again to the 153 regression-group total.

## Reproduction

From this branch, with Telethon 1.45.0 installed:

```bash
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

For test 11, invoke only test_query_builder and test_empty_frame, with socket
connect/connect_ex patched to raise. Its main runner includes a live test and is
not the offline command. Logs from this run are in `/private/tmp/tgdata18_*.log`;
the committed tests and this receipt are the durable record, not those temp logs.

No 1.33.1 test, live Telegram account, deployed receiver or hardware power-loss
acceptance is claimed. SQLite/filesystem durability and the custom backend's
contract remain deployment obligations. No merge or deployment occurred.
