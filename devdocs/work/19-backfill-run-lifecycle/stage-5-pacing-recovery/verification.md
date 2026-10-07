---
model: gpt-6-astra
effort: max
status: PASS-offline
---
# Stage 5 verification

**PASS offline** on product `a180151`, Python 3.11.10 and Telethon 1.45.0. No production
runtime edit followed the passing tests. [Machine-readable receipt](verification-results.json),
[final new-suite output](pacing-test-results.txt), [initial output](pacing-test-initial.txt),
[guard checks](instrument-results.txt), [Gate B copy check](gate-b-copies-results.json).

## Supported offline sweep

| Suite | Actual passing groups | Explicit live skips |
|---|---:|---:|
| 27 pacing/recovery | 32 | 0 |
| 26 completion | 16 | 0 |
| 25 delivery | 41 | 0 |
| 24 lifecycle state | 23 | 0 |
| 23 fixed windows | 22 | 0 |
| 22 daily continuation | 25 | 0 |
| 19 message batches | 33 | 0 |
| 18 read budget | 28 | 0 |
| 17 sessions | 12 | 0 |
| 16 health | 21 | 0 |
| 15 login | 11 | 0 |
| 14 flood threshold | 11 | 0 |
| 13 device identity | 5 | 1 |
| 12 proxy | 5 | 2 |
| 11 explicitly awaited helpers | 2 | 0 |
| **Total** | **287** | **3** |

Reported suite totals for 12/13 include skips; actual counts above subtract them.
The worktree has no real config. Source transport is synthetic through actual SDK/
budget/batch code; socket connections are blocked in lifecycle tests. Proxy refusal
uses local loopback only. The two test_11 coroutine helpers were explicitly awaited
and their True returns asserted. Legacy live tests are not counted as passed.

The unchanged Gate A guard passed 10/10 checks. Daily demo stored four messages and
acknowledged through 104. Compile and Python-3.7 grammar parsing passed for the six
changed/new Python product/test files; Python 3.7 itself was not executed.

## New behavior and failure boundaries

Run `python -m tgdata.smoke_tests.test_27_backfill_pacing`. Its 32 groups include
multiple input/fault/clock matrices, actual SDK/budget prefixes and account changes,
one short measured local elapsed interval, actual source-callback process exit and
before/after actual recovery commit exits. It tests the built methods, not a model
of them or source-code string matching.

The initial result was 31/32 solely because the missing-keyword test used an async
exception helper for a synchronous signature error. The invocation was corrected;
expected refusal stayed TypeError. Final result 32/32, then all supported regressions
passed. No runtime correction or expectation relaxation occurred.

Five prebuild primitive checks preceded implementation; they established clock/record/
SQLite capacity, not the future algorithm. After implementation, two LIVE-origin Gate B
records passed actual recover/reopen/retry on disposable copies. Original state/budget
hashes were unchanged; there were zero source calls. This extra check belongs to the
work folder because release tests must not depend on private Gate B files.

## Evidence boundary

This stage made no Telegram calls and did not change the real account budget. Gates
A/B remain historical passed foundations, not new pacing/control evidence. Mandatory
**Gate C remains pending after Stage 6**. Unknown/indefinite source hints are not zero
waits; source admission still uses fresh account/allowance. Quiescence across engines
is the caller's assertion, not a distributed lock. UTC trust after context loss and
unimplemented controls/public facade remain explicit limits.
