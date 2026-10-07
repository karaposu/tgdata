---
model: gpt-6-astra
effort: max
---
# Stage 1 implementation and verification

Product commit: **2fe9aeb585dc8ae9ee8b0b1da5fc9b70867ade88**.
Base: dev **95ed4c76c4d2aba7800d8793b16eb5d54cfba4ec**.
Branch: `feat/7-account-operation-foundation`.
Environment: Python3.11.10, Telethon1.45.0. No live Telegram work.

## Delivered

The private `ConnectionEngine._account_operation(expected_account_id)` context
validates the numeric expectation before construction; supplies policy before
connect; proves actual self independently of cached IDs; yields a read-only owner
and scoped client; and settles one disconnect attempt on every exit.

Read-budget admission delegates to the same handle's fresh proof before claim/send.
Identity/authentication failure permanently invalidates the handle. Caller
cancellation remains cancellation after cleanup; cleanup failures retain only
their type for best-effort diagnostics and do not replace work outcomes.

Production scope: new internal module (133 lines), 54-line factory/context diff,
three-line opt-in budget branch. No new schema, global owner registry, public TgData
method or health redesign. Documentation lives in `docs/account_operations.md`.

## Plan completion

- [x] Step 1 — handle, strict expectation and fresh proof.
- [x] Step 2 — constructor policy, noninteractive context and retained cleanup.
- [x] Step 3 — owned quota admission.
- [x] Step 4 — 28 offline contract tests.
- [x] Step 5 — maintainer/smoke docs, compile/grammar, full supported offline suites and examples.
- [x] Step 6 — separate product commit; this report is in the subsequent work-notes commit. Branch push and issue status are recorded in the final handoff.

The critic's prebuild real-SDK experiment passed before Step 1 (`542c68e`). One
selected Medium mitigation was folded (`ad66e32`); no architecture substitution
or post-fold re-critique. No new implementation blocker occurred.

## New acceptance evidence

`python -m tgdata.smoke_tests.test_32_account_operation`: **28/28 passed**.

The suite runs actual SDK connect/dispatch/disconnect over a synthetic transport,
with socket.connect/connect_ex forbidden. It uses temporary file/store sessions,
synthetic keys/IDs and real SQLite read budgets. Its strongest assertions include:

- Expected222/cache111/actual222 proceeds with account222 while the cache remains111.
- Expected111/actual222 never enters the body; no group/history/join request occurs.
- Constructor policy and proxy/device/session/budget settings are observed at connect.
- Empty/revoked/banned auth and auth errors inside connect preserve explicit reasons;
  start, code requests and prompts are forbidden even with interactive_login=True.
- Later mismatch/auth loss/unverifiable identity closes the handle before quota
  claim/send; a caught refusal cannot reopen it when replies become valid again.
- Page admission and actual sender admission both refuse owner disagreement.
- Two tasks hold separate live operations simultaneously, then each bills its
  own account; closed and foreign-task handles refuse work.
- Actual SDK disconnect completes before repeated caller cancellation is delivered;
  cancellation during authentication, body or successful cleanup is preserved.
- Cleanup error, internal cleanup cancellation and broken logging cannot replace
  primary success/error; cleanup logs carry type only, not synthetic secret text.

## Existing suites

Commands use `/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python`
with `-m tgdata.smoke_tests.<module>`. Tests12/13 receive the deliberately nonexistent
`/private/tmp/tgdata7-stage1-verification/no-live-config.ini` as their only argument.
Their old runners count skips as passes; this table separates actual passes.

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
| **Existing total** | **355** | **3** |
| **Including new Stage 1 suite** | **383** | **3** |

All 18 supported offline modules pass. Old live suites were not run. The unmerged
#17 branch's tests are not part of this dev-based stage or counted here.

Three offline example runs passed: `daily_continuation.py --demo`,
`backfill_runs.py --demo --directory <temporary> --new`, and the second invocation
on that same directory without `--new`. No user data/config was used.

Compilation and Python3.7 grammar parsing passed for all **61 Python files** in
tgdata/ and examples/. Grammar checks do not claim Python3.7 runtime execution.
`git diff --check` and staged whitespace checks passed.

## Corrections and environment issues

Only local test-fixture corrections were made after test failures; no runtime
design changed and no expected outcome was weakened:

1. The fixture assigned a synthetic SQLite auth key without committing it, leaving
   a lock when the ordinary-client comparison opened the same file. Save the
   fixture's synthetic session immediately after assigning the key.
2. The synthetic MessageEmpty omitted Telethon1.45's required peer_id. Supply it.
3. The synthetic messages.Messages reply omitted the SDK1.45 topics field. Supply
   explicit messages/topics/chats/users keyword arguments.

The first proxy regression run hit the sandbox's localhost bind/connect restriction.
Re-running only that suite with narrowly granted local-socket permission passed;
both Telegram portions remained skipped. This was an environment restriction,
not a product test failure or an automatic-review rejection.

One workflow file was initially created at the worktree root and immediately moved
to its intended stage folder before staging; no misplaced file was committed.

## Limits and remaining workflow

This is an internal foundation. Raw SDK clients are not sandboxed against arbitrary
credential mutation or detached use. Cleanup has no duration bound and reports a
failed attempt without promising transport closure. SDK server failures may still
perform their final two-second backoff. The health ownership defect remains Stage2.

Stage 1 merge check, PR publication, fresh PR critique and merge are pending.
The whole #7 remains open; no merge is authorized by this implementation request.
The original checkout's untracked HANDOFF.md/todo.md were preserved. No duncan or
stray guide changes were staged. Product and workflow notes are separate commits.
