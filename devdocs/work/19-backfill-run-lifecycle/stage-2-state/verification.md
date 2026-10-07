---
model: gpt-6-astra
effort: max
status: historical-stage-2-offline-checkpoint
date: 2026-10-07
---
# Stage 2 verification

**PASS for the original Stage 2 offline scope.** At this checkpoint Gate A was blocked
and no real config/account or Telegram connection was used. The later
[Gate A PASS](../validation/gate-a.md) is a separate live execution, not a reinterpretation
of these receipts. Stages 3–8 remain unimplemented.

## Revision and environment

- Feature branch: `feat/19-backfill-run-lifecycle`.
- Existing #18 product prerequisites through `e9b5154`, integrated by feature-only
  merge `5d0789e`. The new product code/tests/public docs are committed at `1425fd7`.
- Checkout/import: `/private/tmp/tgdata-19-backfill-run-lifecycle`.
- Interpreter: `/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python`;
  Python **3.11.10**, Telethon **1.45.0**.
- Runtime support below means that actual interpreter. Python 3.7 syntax was checked
  with the AST grammar; no Python 3.7 runtime test was performed. No 1.33.1 test.
- New state tests and instrument checks block network sockets. The existing proxy
  suite used its disposable localhost refusing relay; external/live cases skipped.

## Results

| Check | Actual passing groups | Explicit live skips |
|---|---:|---:|
| test_24_backfill_state.py | 23 | 0 |
| test_23_fixed_windows.py | 22 | 0 |
| test_22_daily_continuation.py | 25 | 0 |
| test_19_message_batches.py | 33 | 0 |
| test_18_read_budget.py | 28 | 0 |
| test_17_session_store.py | 12 | 0 |
| test_16_health_events.py | 21 | 0 |
| test_15_login_checks.py | 11 | 0 |
| test_14_flood_threshold.py | 11 | 0 |
| test_13_device_identity.py | 5 | 1 |
| test_12_proxy.py | 5 | 2 |
| test_11: explicitly awaited query-builder and empty-frame helpers | 2 | 0 |
| **Supported offline suite** | **198** | **3** |
| Stage 2 probe_checks.py (additional tool checks) | **9** | **0** |

The test_12/test_13 legacy summaries count skipped branches in their printed totals;
the table separates actual execution. Live legacy entrypoints and the test_11 module
main were not run. test_11's two offline helpers were explicitly awaited with socket
connections prohibited.

The first full sweep had 197 passing groups; a meaningful imported-origin test was
then added to test_24, which was rerun in full at 23/23. No product code changed after
the full sweep. The total above counts the latest successful coverage, not repeated
executions as additional tests.

The existing daily-sync offline example also passed: lost acknowledgment response
reconciled, four messages retained, acknowledged position 104. Changed Python files
passed compilation and Python 3.7 AST grammar checks; the final test-only addition was
compiled/checked again. `git diff --check` and the staged product diff check passed.

Local execution logs are `/private/tmp/tgdata19_stage2_test24.log`, the corresponding
test-number logs, `/private/tmp/tgdata19_stage2_probe_checks.log` and
`/private/tmp/tgdata19_stage2_daily_demo.log`. They are temporary receipts; this report
and the committed tests preserve the assertions and qualified results.

## What the new tests actually establish

1. New/retry submission, immutable request recognition, fixed dates, content-free
   status, exact IDs, conflicts and unknown/missing state behavior use the real new
   engine and codec. A forbidden clock proves recognized retry does not recalculate.
2. Actual SQLite commits are interrupted by `os._exit` immediately before/after
   commit in subprocesses. Another test commits and then raises during connection
   cleanup. Reload/retry distinguishes committed state from absent state. These are
   process-crash observations, not filesystem/power-loss certification.
3. Exact old text is the CAS expectation even if its JSON layout was noncanonical.
   Simultaneous submissions produce one accepted effect. Backend type errors, lost
   replies and cancellation retain uncertainty without exposing sentinel secrets.
4. Existing-only SQLite open refuses missing/deleted/schema-less files without
   creating replacement state. Default provisioning remains compatible.
5. Nested pending/end/attempt/control/recovery/failure/abandonment snapshots must
   satisfy the strict schema and cross-field constraints. Valid future snapshots
   are explicitly seeded fixtures: their transition operations are not implemented.
6. Imported origin is not accepted delivery or observed exhaustion, including the
   maximum message ID. Accepted positions and IDs preserve exact integer precision.
7. Minimum durations round upward to representable microseconds, handle overflow,
   and are independent of the caller's Decimal precision/exponent context.

## Instrument verification limits

The nine tool checks exercise existing-only preflight, refusal of unqualified oracle
and limit inputs, real write/join/wrong-target RPC refusal, send caps, actual SDK
iterator page tracking, SDK retries, comparisons, full driver composition and CLI
offline defaults/report exclusivity. They use actual SQLite, Telethon request/iterator
types and budget code with **synthetic transport**. The injected ServerError message
in the log is the intended retry test; it is not a live Telegram failure.

The driver never advances lifecycle state or calls unimplemented prepare/ack. A
matching diagnostic scan still reports the whole gate INCONCLUSIVE, with remaining
coverage listed. Live oracle completeness, visibility, SDK/server pagination, dates,
end signals and real downloaded media have not been verified.

## Local corrections and deviations

- Duration conversion was isolated from ambient Decimal settings and covered by
  low-precision/exponent tests. This implements the folded conservative-rounding remedy.
- Probe reporting preserves an earlier failure when cleanup/evidence collection also
  fails, does not call uncertain requested-live activity “no connection,” and compares
  every expected artifact strictly. These were local implementation refinements.
- No test expectation was weakened to force a pass. No architectural deviation or
  new plan step was introduced. No product-test failure remains.
- Product code/tests/public docs and work-folder notes/tooling are separate commits.
  No PR, protected-branch merge, #7 change or `duncan` change belongs to this run.

## Gate handoff from this checkpoint

At this checkpoint the actual source/oracle/allowance inputs were still unset, so
Stage 3 remained gated. The later [Gate A report](../validation/gate-a.md) records
their qualification and the actual live PASS. These offline receipts alone did not close it.
