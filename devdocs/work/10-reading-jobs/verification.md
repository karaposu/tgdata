---
model: gpt-6-astra
effort: max
---
# Verification — product `6ee146c`

**Result: PASS**, 2026-10-11. Python3.11.10, Telethon1.45.0, SQLite3.45.3,
macOS/POSIX subprocesses. Node was available and the real JavaScript ID consumer
check ran. These are offline synthetic-source tests, not live Telegram qualification.

`verification/results-final.json` records the final24-suite result. Its original
`results.json` preserves the sandbox-blocked initial test12 run. The loopback rerun
is separately logged, not substituted invisibly. Individual logs are in
`verification/suites/`; initial new-suite failures and packaging attempts are retained.

| Suite | Actual passes | Live skipped |
|---|---:|---:|
| 12 proxy | 5 | 2 |
| 13 device identity | 5 | 1 |
| 14 flood threshold | 11 | 0 |
| 15 login | 11 | 0 |
| 16 health | 21 | 0 |
| 17 session store | 12 | 0 |
| 18 read budget | 28 | 0 |
| 19 message batches | 33 | 0 |
| 22 daily continuation | 25 | 0 |
| 23 fixed windows | 22 | 0 |
| 24 backfill state | 23 | 0 |
| 25 backfill delivery | 41 | 0 |
| 26 backfill completion | 16 | 0 |
| 27 backfill pacing | 32 | 0 |
| 28 backfill controls | 32 | 0 |
| 29 public backfill | 23 | 0 |
| 30 backfill integration | 15 | 0 |
| 32 owned account operation | 28 | 0 |
| 33 owned health | 62 | 0 |
| 34 group access | 49 | 0 |
| 35 join allowance | 35 | 0 |
| 36 group joining | 44 | 0 |
| 37 worker source/protocol | 25 | 0 |
| 38 worker processes | 14 | 0 |
| **Total** | **612** | **3** |

The legacy12/13 harness prints skipped cases as passed; the table subtracts them.
No test31 was run or imported: that suite belongs to unmerged #17. Current-dev
baseline573 actual cases plus39 new worker groups equals612. Groups contain more
than one scenario where stated; they are not612 live account observations.

## Real composition evidence

Worker source tests use the actual factory, verified operation, SDK iterator/group
dispatch, health machinery, raw batches and SQLite ledgers. Only synthetic transport
replies/faults replace Telegram. Request objects are serialized; socket connections
are forbidden. Fake stale identity999 must yield verified111/222 ownership, and
changed identity at admission stops the source/claim. Counted read/join charges and
partial batches are checked, including a100-record prefix before FloodWait7200.

Worker process tests run the actual CLI or serve bootstrap in subprocesses, with
the test-only synthetic wire at the same boundary. They verify all four verbs,
unknown/malformed frames and startup, exact query ID1152921504606847099 through
Node JSON/BigInt, session-store bootstrap without .session files, completed-source
cleanup failure with no successor job, broken stdout exit3, idle SIGINT/SIGTERM,
output-pressure exit130/143 without draining stdout, and repeated active signals
while native disconnect is held until explicitly released. Cleanup failure must
leave stderr empty and charges retained. Tests own watchdogs/child processes.

Core lifetime tests additionally cover success/body-error/setup-error/internal
disconnect cancellation, repeated caller cancellation, callback-owned cancellation,
overlap refusal, and a callback child attempting close without a dependency cycle.
Explicit serializer and oversized-notification faults test secondary-observation
isolation; they are not described as natural SDK replies.

## Package and examples

`verification/tgdata10-package-verify-third.txt` is the final passing run:

- 76 Python files compile and parse with Python3.7 grammar. Native older-runtime
  behavior is not claimed; `cancelling()` test checks run under3.11.
- Build a wheel from an export containing no `.git` or `devdocs`.
- Install without dependencies into an isolated target; `tgdata.__file__` points
  there. Run both `python -m tgdata.worker` and generated `tgdata-worker` from an
  independent directory. Each emits source-free ready and exits0 on EOF.
- Run the copied caller example against the installed package: local refusal/EOF.
- Daily demo accepts/replays/acknowledges through104.
- New backfill demo completes with3 source reads,3 receipts,5 unique messages;
  completed restart keeps all state and uses0 source reads.

The runtime dependency environment is unchanged. Existing wheel0.44.0 tooling
from the base environment was used to build, not downloaded. Verification export
is retained at `/private/tmp/tgdata10_package_hgbgykwn` for inspection. The script
records absolute environment paths and is an evidence runner, not a public package
dependency. Initial tooling/invocation corrections are explained in implementation.md.

`git diff --cached --check` passed for all13 product paths. No production/example
import depends on work docs or the unmerged account pool. Ordinary library regressions
retain their prior behavior. No live login/read/join, real policy reset or dev merge.

## Limits / next gates

Synthetic wire tests cannot establish permission, safe rates, a proxy's real exit
IP or Telegram availability. Windows/native Python3.7 and live worker deployment
remain unqualified. Exclusive assignment of sessions is a caller requirement,
not a distributed lock. Lost output/force-kill can leave source completion unknown;
the worker's request IDs are process-local and are not durable idempotency.

Implementation verification is complete. Merge-check, PR publication and a fresh
PR critique have not run for #10. #17's two-account live test is separate and pending.
