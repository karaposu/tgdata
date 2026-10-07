---
model: gpt-6-astra
effort: max
status: PASS
---
# Stage 4 verification

**PASS** on product `b1f6495099f72fb9a49d56d3cc5acef62e8ae82e`, Python 3.11.10,
Telethon 1.45.0. [Machine-readable offline receipt](verification-results.json),
[new suite output](completion-test-results.txt), [instrument output](instrument-results.txt),
[real Gate B report](../validation/gate-b.md). No source/behavior changes followed testing.

## Offline results

| Suite | Actual passing groups | Explicit live skips |
|---|---:|---:|
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
| 11 explicitly awaited offline helpers | 2 | 0 |
| **Total** | **255** | **3** |

The suites' reported totals for 12/13 include skips; the table subtracts them.
Those legacy live tests are outside the authorized fixture-specific gate and are not
counted as passes. The worktree has no real account config. Source transport is synthetic
in SDK/budget/media suites; completion tests block sockets. Proxy refusal checks use
local loopback only. Existing Gate A instrument: **10/10**; daily demo: four stored
messages, acknowledged through 104. Compile and Python-3.7 grammar parsing passed for
all four changed/new Python product/test files; no actual Python 3.7 runtime claim.

Run the new suite with `python -m tgdata.smoke_tests.test_26_backfill_completion`.
Modules 25/24 ran alongside it; the remaining full supported sweep ran after those
passed, without repeating them unnecessarily. Test 11's `test_query_builder` and
`test_empty_frame` were explicitly awaited and their True returns asserted. Log hashes
and reported/actual/skip counts are retained in verification-results.json.

The 16 completion groups include 16 pre/post/error/nonbool combinations, 20 unreadable/
old/missing/corrupt/foreign read-back combinations, cancellation during four operations,
six origin/final shapes, and eight real before/after-commit subprocess exits. They also
check newer controls/receipts, original source-error provenance, actual post-commit
SQLite close errors, full-follow-up auth/budget failure and seeded terminal precedence.
These matrices execute behavior; they do not assert source-code string patterns.

No product test failed and no runtime fix was needed. The deliberately updated old
post-commit assertions follow Step 2 of the reviewed plan. The only documentation
correction was the issue-priority transcription described in implementation.md.

## Real evidence

The critic's prebuild probe passed four checks before the product change; that was not
a Gate B PASS. After product verification, Gate B ran 20 sequential worker actions
with actual Telegram, real SQLite, a durable receiver and actual process exits.
A separate audit read the final state/receiver files, not just the harness result.
All assertions passed. See the gate report for scopes, hashes, request/budget counts,
independence limits and explicitly preserved unknown attempts.

Gate B passes only this selected account/view/SDK/backend/test-receiver composition.
Actual quota expiry/warm-up/pacing/recovery/control and public integration remain at
Gates C/D. Power loss, an arbitrary remote backend or a production receiver was not tested.
