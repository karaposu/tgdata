---
model: gpt-6-astra
effort: max
status: verified
date: 2026-10-07
---
# Stage 3 verification

**PASS for the implemented Stage 3 scope.** Product code/tests/public docs are committed
in `3140dcda296d6c16b54bcbde124641bab9efeb7e`. No real account/config or Telegram
connection was used in this stage. Gate A remains the earlier live foundation receipt;
Stage 4 and Gate B are not completed by these checks.

## Environment and results

Python 3.11.10 and Telethon **1.45.0**, imported from the #19 worktree. Changed Python
compiled and passed Python 3.7 AST grammar checks; no Python 3.7 runtime or 1.33.1 claim.
New tests forbid sockets. Existing proxy checks use a localhost fixture; live config
is absent from this checkout and the three pre-existing live branches explicitly skip.

| Suite | Actual passing groups | Explicit live skips |
|---|---:|---:|
| test_25_backfill_delivery | 41 | 0 |
| test_24_backfill_state | 23 | 0 |
| test_23_fixed_windows | 22 | 0 |
| test_22_daily_continuation | 25 | 0 |
| test_19_message_batches | 33 | 0 |
| test_18_read_budget | 28 | 0 |
| test_17_session_store | 12 | 0 |
| test_16_health_events | 21 | 0 |
| test_15_login_checks | 11 | 0 |
| test_14_flood_threshold | 11 | 0 |
| test_13_device_identity | 5 | 1 |
| test_12_proxy | 5 | 2 |
| test11_helpers | 2 | 0 |
| **Total** | **239** | **3** |

The two test_11 helpers were explicitly awaited with connections forbidden; its live
module main was not run. Legacy test_12/test_13 summaries include their skipped branches
in the printed totals; the table counts only actual executed groups.

The Gate A instrument's **10/10** offline checks and the existing daily demo also passed
(four receiver messages, acknowledgment through 104). The separate prebuild experiment
passed five real-primitive checks before implementation. No synthetic check is counted
as a new live result. The full supported offline sweep ran once after the final test
addition; checks were not repeated merely to inflate totals.

Receipts: [machine-readable totals](verification-results.json),
[delivery output](delivery-test-results.txt), [instrument output](instrument-results.txt),
and [prebuild output](prebuild-results.txt). Other per-suite local logs are retained at
`/private/tmp/tgdata19-stage3-<suite-name>.log`.

## What the new 41 groups establish

- Confirmed admission and exact saved query precede the actual SDK-backed callback;
  no SQLite transaction remains held over it. Stale scopes, counters and invalid local
  inputs refuse, while source overlap and unconfirmed attempts cannot start another read.
- Real SQLite reopen/replay preserves canonical payload/hash/full receipt without a
  reader or clock. Fresh relative enrollment still uses its original dates after the
  supplied clock moves. MessageBatch v1 and existing namespaces/APIs remain compatible.
- Complete run/destination/generation authority, equal hashes across runs, retained
  prior receipts, duplicates with newer pending and concurrent ack/control conflicts
  are handled without foreign effects or repeated accepted progress.
- Ordinary source errors retain the actual valid prefix and original exception. Failed
  persistence exposes it separately in read_error; cancellation at source/commit/error
  handling boundaries remains local and does not claim rollback or false Telegram health.
- Real downloaded artifact handling is exercised with actual SDK/file code and synthetic
  transport: exact replay/relocation, corruption/missing/symlink refusal, prefix retention
  on media failure, and valid acceptance after both local copies are removed.
- Actual subprocess exits occur immediately before/after pending publication and ack
  commits. A real receiver commits data, loses its local reply, receives exact replay
  and retains one receipt/two message rows before the cursor advances. These are process-
  crash/transaction observations, not power-loss or remote-backend certification.
- Minimal end/terminal closure satisfies the existing codec. Full batches are not
  exhaustion; an explicit finite response or subsequent empty response establishes it.
  Future paused/cancelled/recovery snapshots only test preservation, not those APIs.

## Corrections and deviations

1. A newly inserted test block initially landed after the module entrypoint, causing
   an await-outside-function syntax error. It was moved into its intended test before
   execution; compilation then passed. This was a local test-writing correction.
2. The first execution passed 36/39 groups. Three end/late-control/successor fixtures
   supplied a short MessagesSlice that advertised more history and then fell back to
   the synthetic sender's continuing stream. The SDK correctly kept reading. Those
   fixtures now use the actual finite Messages response type. Original pending/end/
   receipt assertions were retained; no production behavior or expected guarantee was
   weakened. A separate short-slice-plus-empty-reply test explicitly requires the extra
   SDK request. All 40 groups then passed.
3. An additional fresh-relative-query test exercised zero origin and a moved clock;
   it passed individually and in the final **41/41** delivery suite/full regression sweep.
4. The pre-existing test_24 assertion that prepare/ack methods were absent changed as
   explicitly planned for Stage 3. Its no-public-facade/control/recovery boundary remains.

No runtime correction or architectural plan deviation was required after implementation.
The minimal completion closure and fail-closed positive timing boundary were explicit
in the description/plan before coding. No additional mitigation was invented after the
critic; its required primitive experiment passed before any implementation step.

## Remaining limits

Further source admission after a positive-pause/uncertain timing record remains gated
until Stage 5; replay/ack stay local. Unsettled attempts require future explicit recovery.
Stage 4 must audit/refine completion and uncertain outcomes with its dedicated fault
matrix, then Gate B must exercise the new delivery/receiver composition with real data.
No new live proof, public facade, control/recovery API, PR or protected merge is claimed.
