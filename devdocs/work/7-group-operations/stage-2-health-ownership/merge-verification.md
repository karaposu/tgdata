---
model: gpt-6-astra
effort: max
---
# PR22 merge verification — 2026-10-10

**Result: merged, verified and pushed to dev.**

- User authorization: “go”, after both renewed gates passed and the explicit
  merge-go-ahead request.
- PR: https://github.com/karaposu/tgdata/pull/22
- Merge commit: `30ba7062b0d7254b5695c4a0d727a4c8242e3f25`.
- First parent / prior dev: `53306df2c3d87b558be0b7ed4419a42d3229c5f9`.
- Second parent / approved PR head: `b74e9b369c7607037da7f3b84fa02e170e6569d2`.
- GitHub confirmed merged at `2026-10-10T12:23:14Z`, with that exact merge commit.
- Feature/archive branch retained: `feat/7-account-health-ownership`.

## Integration

Prepared a no-fast-forward merge in an isolated checkout at
`/private/tmp/tgdata-22-merge-verification`. Before committing, restored devdocs/work
and devdocs/archaeology from the prior dev tree. The staged and committed merge
changes exactly eight product files, byte-for-byte equal to approved product c6451bb:
README, docs/account_operations.md, connection_engine.py, health.py, owned_health.py,
tgdata.py, test33 and the smoke README.

All devdocs match prior dev; no tracked work-folder files entered dev and archaeology
is unchanged. No duncan, unrelated guide edit, original untracked file, old broad
PR16 work or unmerged #17 code was included. Whitespace checks passed. The original
checkout remains on feat/7-group-operations with its two pre-existing untracked files.

Renewed merge fidelity PASS fd655a5 and fresh PR critic ACCEPTED9e0b4e5 (0 High,
0 Medium, 0 Low) were posted before authorization. Source refs were refreshed and
rechecked before push: dev53306df and featureb74e9b3 were unchanged. The merge was
pushed normally, without force, only after the final verification below passed.
GitHub recognized PR22 as merged before advancing the retained branch with this
post-merge evidence. No extra review or implementation was substituted for the merge.

## Tests on the actual merged code

Python3.11.10 / Telethon1.45.0. The existing project venv was used from the isolated
merge checkout. Import checks confirmed tgdata came from this merged tree, not the
original checkout or archive. The corrected budget-suite invocation was the normal
`python -m tgdata.smoke_tests.test_18_read_budget` from the same directory/interpreter.

| Module | Actual passes | Live skips |
|---|---:|---:|
| test_12_proxy | 5 | 2 |
| test_13_device_identity | 5 | 1 |
| test_14_flood_threshold | 11 | 0 |
| test_15_login_checks | 11 | 0 |
| test_16_health_events | 21 | 0 |
| test_17_session_store | 12 | 0 |
| test_18_read_budget | 28 | 0 |
| test_19_message_batches | 33 | 0 |
| test_22_daily_continuation | 25 | 0 |
| test_23_fixed_windows | 22 | 0 |
| test_24_backfill_state | 23 | 0 |
| test_25_backfill_delivery | 41 | 0 |
| test_26_backfill_completion | 16 | 0 |
| test_27_backfill_pacing | 32 | 0 |
| test_28_backfill_controls | 32 | 0 |
| test_29_backfill_public | 23 | 0 |
| test_30_backfill_integration | 15 | 0 |
| test_32_account_operation | 28 | 0 |
| test_33_owned_health | 62 | 0 |
| **Total** | **445** | **3** |

All 19 supported offline modules finished with exit0 after the launcher correction
below. Test12/test13 count live skips in their printed 7/7 and6/6 totals; the table
subtracts those skips. A verified nonexistent config path
`/private/tmp/tgdata22-no-live-config.ini` kept their three Telegram checks skipped.
Test12 had narrow permission to bind its local dead/refusing-proxy sockets. No live
Telegram action, login or membership change occurred.

Three offline demo executions also exited0:

- Daily continuation: lost-acknowledgment replay reused its stored batch, with4
  messages retained and progress acknowledged through104.
- Fresh backfill: simulated process exit/replay completed, 5 unique messages,
  3 source reads and0 replay reads.
- Restarting that same backfill: completed with0 source reads.

Compile and Python3.7 grammar checks passed for **63 Python files** under tgdata/
and examples/. This does not claim Python3.7 runtime execution. The seven fresh
PR probe groups remain evidence for the identical product; they are not presented
as rerun from this document-excluding merge.

Initial/final suite manifests, individual logs, demo output and syntax results are
locally retained at `/private/tmp/tgdata22-merge-verification/`. This committed
report is the durable evidence; temporary log storage is not an archive guarantee.

## Verification launcher correction

The initial runner used runpy.run_module with a temporary `__main__` namespace to
check imports before each suite. That broke test18's ProcessPoolExecutor pickling:
`attribute lookup process_claim on __main__ failed`. Its first result was27/28;
this was a launcher failure before the child worker ran, not a product assertion.
Rerunning with the suite's normal `python -m` entry point passed28/28, including
process_claims. No source file or test expectation changed, and no other passing
suite was repeated unnecessarily.

A result-counting helper also initially assumed the test label and pass line were
adjacent. An expected SDK diagnostic interleaved those lines. The helper instead
checked the actual 28/28 summary, 28 pass markers and absence of failure markers.
This changed only log parsing, not a test outcome. Both original and corrected-run
logs are preserved locally, and the final445 total counts each test once.

## Remaining scope

#7 remains OPEN: Stage1 and Stage2 are merged, while Stage3 group lookup/access,
Stage4 join allowance and Stage5 joining remain. The next work has not started.
Old broad PR16 is historical and unchanged. Keep all reasoning and review artifacts
on the retained archive branch; do not delete it or add them to dev.
