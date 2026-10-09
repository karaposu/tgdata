---
model: gpt-6-astra
effort: max
---
# Stage 2 verification — 2026-10-09

**Result: PASS.** Product commit `3d59455`, base dev `53306df`, branch
`feat/7-account-health-ownership`. No live Telegram action, login or membership
change. No PR/merge gate is claimed by this implementation verification.

## Implementation against the folded plan

1. Fixed monitor reuses HealthMonitor's state/event/snapshot shape; new private
   owned observation binds exact client/task and generation ordering. Notifications
   receive plain data separately. Product module `tgdata/owned_health.py`: 182 lines.
2. Actual factory wrapper passes client/request successes and RPC/MultiError
   failures. Scoped exclusions prevent pre-proof/owned errors from being attributed
   to an enclosing legacy owner. Parent report flags stay in one monitor/task.
3. Private facade composes the unchanged Stage 1 handle; public
   `get_account_health(id)` is a synchronous local copy or None. Cooperative close
   retires pending owned notifications and avoids callback self-await.
4. Suite33 exercises real facade, SDK, budget and cleanup with synthetic transport;
   README and smoke README describe the separate query/timing contract.
5. Targeted and full supported offline regression runs passed, as did examples,
   compilation, compatibility grammar and diff whitespace checks.

Both selected mitigations are implemented: current handle validity vetoes recovery
after caught identity/auth loss; actual SDK MultiError leaves are observed without
using partial successes as recovery evidence. Prebuild experiment PASS is separately
recorded in `critic.md` and committed in `46866c3`, before any runtime edit.

## Tests

Python 3.11.10, installed Telethon 1.45.0. Commands use
`/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python` from the isolated
Stage 2 worktree. Suites12/13 receive
`/private/tmp/tgdata-stage2-deliberately-missing.ini`; their live cases skip without
reading credentials. Suite12 uses normal escalation to bind a local test proxy;
its dead/refusing proxy diagnostics are expected successes, not live Telegram tests.

| Suite | Actual passes | Live skips |
|---|---:|---:|
| 12 proxy | 5 | 2 |
| 13 device identity | 5 | 1 |
| 14 flood threshold | 11 | 0 |
| 15 login | 11 | 0 |
| 16 legacy health | 21 | 0 |
| 17 sessions | 12 | 0 |
| 18 read budget | 28 | 0 |
| 19 message batches | 33 | 0 |
| 22 daily continuation | 25 | 0 |
| 23 fixed windows | 22 | 0 |
| 24 backfill state | 23 | 0 |
| 25 backfill delivery | 41 | 0 |
| 26 backfill completion | 16 | 0 |
| 27 pacing | 32 | 0 |
| 28 controls | 32 | 0 |
| 29 public backfill | 23 | 0 |
| 30 backfill integration | 15 | 0 |
| 32 Stage 1 operation | 28 | 0 |
| 33 owned health (new) | 41 | 0 |
| **Total** | **424** | **3** |

Suite12 prints 7/7 and suite13 prints 6/6 because those runners count skips as
successful results. The actual-pass total above subtracts their three skips.
No blanket pytest or older live-oriented smoke suite was run. Suite31 belongs to
unmerged #17 and is not part of this base.

New tests cover stale cached owner versus verified event/snapshot, independent
accounts/instances, snapshot copy/no-I/O, pre-proof and local-error exclusions,
source failures caught by the body, real MultiError, nested budget verification,
foreign clients and inherited/inactive tasks, self-only versus explicit group
recovery, caught handle invalidation, matching method/request recovery and forced
older/newer overlap for all three scopes. An additional forced overlap starts the
older operation before authentication completes. Callback cases cover sync/async
errors, cancellation, post-disconnect invocation, repeated caller cancellation,
failed cleanup, re-entry, cooperative retirement and callback self-close.

All 41 new tests passed on their first run. Test16 and test32 also passed first;
the remaining offline suites passed once. Expected injected diagnostic tracebacks
are not test failures. Full-suite and demo output is locally retained under
`/private/tmp/tgdata7-stage2-verification/`; targeted test output was captured in
the tool transcript. This document records the durable verification evidence.

## Other checks

- `compile()` plus `ast.parse(..., feature_version=(3, 7))`: all 63 Python files
  under tgdata/ and examples/ pass. This checks syntax compatibility, not execution
  on a Python3.7 runtime. Final syntax was rechecked after a comment/import-format
  cleanup; behavioral code had not changed after the passing suites.
- Daily continuation `--demo`: destination retry/replay passed without Telegram.
- Backfill `--demo --directory <temporary> --new`: completed with an accepted batch
  replay after an owned process exit. Re-running the same directory: completed with
  zero source reads. Three offline demo executions total, all exit0.
- `git diff --cached --check`: clean. Product checkpoint contains eight intended
  files only; work docs remain in separate commits.

## Corrections and deviations

No runtime correction or architectural deviation was needed after testing. No test
expectation was changed. Fixed one accidentally duplicated smoke-README heading
before commit, wrapped a long import and clarified an existing monitor comment.
The existing `docs/account_operations.md` also needed its Stage 1-only wording
updated and the private composition contract documented. This small documentation
extension beyond the named READMEs is recorded in the product commit message.

Original checkout remains on `feat/7-group-operations` with its two pre-existing
untracked files (HANDOFF.md and todo.md). No duncan, stray guide change, old revision3,
unmerged #17 or archive worktree was staged or changed.

## Limits and next gate

This is Stage 2 foundation. Existing public reads still use legacy health; lookup,
access and join operations are later stages. The internal access assertion trusts
the concrete operation's interpretation of actual results, not generic RPC names.
Callbacks are asynchronous notifications, with no durable completion guarantee;
close assumes ongoing producers have finished. Tests prove local SDK/asyncio/SQLite
composition, not Telegram server permission or frozen-account policy.

Next: merge check against the full diff and pipeline, PR into dev, then a fresh
same-session PR critic. §9 model/effort evidence must be considered at that gate;
this artifact retains the previously observed same-session Astra/max provenance,
not an invented fresh model-selector reading. Merge requires the user's go-ahead.
