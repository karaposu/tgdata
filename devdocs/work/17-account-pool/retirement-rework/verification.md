---
model: gpt-6-astra
effort: max
status: OFFLINE_PASS_LIVE_PENDING
---
# Verification — #17 retirement and current-dev integration

**PASS at product commit `485446419122a13f871bd07fb145bbf072465543`.**
This feature-branch merge incorporates dev `68f6bbd` and the scoped lifecycle
repair. No merge into dev, PR publication or fresh PR critique occurred here.
The two-account live qualification (parent plan Step 9/E1) remains pending.

## Result and scope

The pool retains ownership until its actual source child and native SDK cleanup
have settled, including repeated caller cancellation. Failed retirement retains
the old client behind a local reuse prohibition until explicit cleanup succeeds.
Shutdown waits for the active reader and each retirement attempt; caller
cancellation stays cancellation. Original completed source results/errors and
partial-result handling retain their existing precedence over observer timeouts.

The factory now uses current dev's `_new_client(..., **client_options)` seam.
README retains both the merged group-joining API and the existing-access pool.
All merged #7 exports and constructor arguments coexist with the pool facade.
Automatic joining is still outside this pool delivery.

## Runtime verification

**619 actual checks passed across 23 supported offline suites; three explicit
live skips are excluded.** All suites exited zero on the first final integrated
run. The focused pool suite passed 46/46 before the full run and again within it.
The ten additional groups cover native disconnect, repeated cancellation,
failed/internal-cancelled retirement, explicit cleanup retry, repaired credentials,
source-child settlement, shutdown/context-exit precedence and factory policy.

| Suite | Actual passes | Live skips |
|---|---:|---:|
| 12 proxy | 5 | 2 |
| 13 device identity | 5 | 1 |
| 14 flood threshold | 11 | 0 |
| 15 login checks | 11 | 0 |
| 16 health events | 21 | 0 |
| 17 session store | 12 | 0 |
| 18 read budgets | 28 | 0 |
| 19 message batches | 33 | 0 |
| 22 daily continuation | 25 | 0 |
| 23 fixed windows | 22 | 0 |
| 24 backfill state | 23 | 0 |
| 25 delivery | 41 | 0 |
| 26 completion | 16 | 0 |
| 27 pacing | 32 | 0 |
| 28 controls | 32 | 0 |
| 29 public backfill | 23 | 0 |
| 30 backfill integration | 15 | 0 |
| 31 account pool | 46 | 0 |
| 32 account operation | 28 | 0 |
| 33 owned health | 62 | 0 |
| 34 group access | 49 | 0 |
| 35 join budget | 35 | 0 |
| 36 group joining | 44 | 0 |

Python 3.11.10, Telethon 1.45.0, SQLite 3.45.3. Suites 12/13 received an
explicitly nonexistent config; their live skips are not passes. These checks
used synthetic Telegram replies, real SDK/SQLite composition, local loopback
and owned subprocess exits. No Telegram login/read/join or existing ledger use.
The delayed cooperative reader finalizer is a labeled fault injection, not a
claim that an unmodified SDK currently performs that delay.

Additional checks passed:

- All 76 Python files under `tgdata/`, `examples/` and `setup.py` compiled and
  parsed using Python 3.7 grammar. This is not a native Python 3.7 runtime claim.
- Four demo runs: account pool, daily continuation, new backfill and restarted
  backfill. The pool selected 222 after 111's wait, charged 111:2 / 222:4,
  stored four messages, acknowledged through 104 and replayed without a source
  read. Restarted backfill made zero source reads.
- A separate export excluding `.git` and all `devdocs` imported its own package,
  passed the 46/46 pool suite and ran the pool demo. The export was copied from
  the final tested product tree before the product commit; no product edits
  followed these checks.
- Staged/unstaged whitespace checks, conflict checks and the expected 14-file
  product diff against dev passed before committing. The merge parents are the
  folded-plan head `15f0b8a` and dev `68f6bbd`.

The exact suite runner is retained at `probes/run_verification.py`. It ran four
independent subprocesses at most, with a 300-second bound per suite. The runner
retains the original local paths. Its commands are `python -m
tgdata.smoke_tests.<module>`; only 12/13 take the absent-config argument.
Use the project virtualenv, whose interpreter was
`/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python`.
Durable results, all suite/demo/export logs and preservation evidence are in
`evidence/verification.json` and `evidence/final-logs/`.

## Preservation and selected critique

Byte comparisons against starting #17 `8d3db76` confirmed unchanged
`pool_state.py`, `progress_facade.py` and `batch_engine.py`. AST comparisons
confirmed all 21 router/state/admission/recovery methods listed in the JSON
evidence unchanged, including `read`, `get_message_batch`, `recover_account`
and `recheck_account`. Only pool cleanup orchestration changed in the controller.

The current dev foundation files are byte-identical to `68f6bbd`:
`connection_engine.py`, `account_operation.py`, `owned_health.py`,
`group_operations.py`, `join_budget.py`, `join_client.py`, `health.py`,
`read_budget.py`, `sync_engine.py` and `backfill_engine.py`.

The fresh plan critic (`c251ca4`) found one Medium: repeated cancellation could
release the pool while its actual source child remained active. Selected robust
mitigation and mandatory six-group prebuild evidence were committed at `6bb40f2`;
the folded revision-2 plan is `15f0b8a`. Actual-composition prebuild passed before
runtime edits. A prototype fixture finalizer was corrected to restore the old
sender after client replacement; all six groups were rerun successfully. This
was test-fixture cleanup, not a runtime redesign or weakened assertion.

The earlier disposable compatibility assessment (608 passes, one obsolete
constructor assertion, three live skips) preceded implementation and is retained
in `evidence/prior-compatibility.json`. The final test31 signature now includes
dev's trailing `join_budget=None`. It is not a remaining verification failure.
No final runtime verification failed and no post-test runtime correction was
needed. No architectural deviation from the folded plan occurred.

## Completion and remaining gates

All five scoped rework steps are implemented and verified. Product integration,
tests and public docs are in `4854464`; this verification, logs and parent handoff
are a separate work-only checkpoint. Original parent plans/critic/verification
remain historical evidence, including their then-current statement that #7 was
paused. #7 is now merged; the current pool still covers existing access only.

Next: merge check against the complete integrated feature and both plans, PR
into dev, then a fresh PR critique. Merge itself still needs the user's go-ahead.
E1 requires two approved distinct authenticated accounts, a shared readable group
and a bounded allowance; only one account was offered, and live testing remains
pending. Offline qualification is not live two-account qualification.

Cleanup has no deadline: an SDK task that never settles can delay cancellation
indefinitely. Exclusive session ownership and one pool process/event loop remain
required. Failed cleanup and a cancelled close are not proof every client closed.

Section 9 provenance was checked again from this session's latest turn metadata
at `2026-10-11T08:17:10.885Z`: `gpt-6-astra`, effort `max`, satisfying the feature
path minimum. This is a metadata check, not an assertion of a model switch.
