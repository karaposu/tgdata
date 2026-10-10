---
model: gpt-6-astra
effort: max
---
# Stage 3 merged-code verification — PASS

Recorded UTC: 2026-10-10T16:53:12.416445+00:00.

[PR23](https://github.com/karaposu/tgdata/pull/23) is **MERGED** into dev at
**1ce39d5c90df399d57b4935cef353762c77cc537**, recorded by GitHub at
**2026-10-10T16:50:52Z**. The user explicitly authorized the merge with “go”.
The reviewed head was8dfa10d2ab9ead27a0215939780c0c2641f5795c; producta2afc05.
Fidelity PASS1348028 and fresh critic ACCEPT8dfa10d (0High/0Medium/1Low) preceded it.
The malformed nested-invite error-typing Low remains consciously retained; no patch.

## Merge content and archive

The merge was prepared in isolated /private/tmp/tgdata-23-merge-verification at remote
dev30ba706. It has two parents:30ba706 and reviewed feature head8dfa10d. Before commit,
restore-from-HEAD excluded devdocs/work and preserved dev's archaeology. Exactly the10
reviewed product files changed. There was no merge conflict or implementation change.

Both before/after commit, diff checks confirmed:

- devdocs/work and devdocs/archaeology match dev30ba706 exactly; no work notes entered dev.
- All paths outside those directories match the reviewed feature head exactly.
- No whitespace errors or untracked/dirty files in the merge verification worktree.

The merged commit was tested **before push**. Remote heads were checked again immediately
before a normal fast-forward push of that merge to dev. GitHub then reported PR23 MERGED,
mergeCommit1ce39d5. Local dev was fast-forwarded from its ancestor95ed4c7; origin/dev was
refreshed to1ce39d5. The original checkout stays on its historical branch, untouched.

feat/7-group-lookup-access is retained as the archive, including this post-merge record.
This record and its evidence are committed only there. No branch was deleted. Parent
#7 stays open because Stage4 join allowance and Stage5 joining remain to implement.

## Verification on the merged checkout

**494 actual offline test groups passed;3 live checks skipped; all20 suites exited0.**

| Suite | Actual passes | Live skips |
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
| test_34_group_access | 49 | 0 |

Commands used the project venv Python in normal module mode (`python -m
tgdata.smoke_tests.<suite>`), with four independent processes in separate fixture
directories. Tests12/13 received a verified absent config path under
/private/tmp/tgdata23-merged-verification; their3 live checks stayed skipped. Test12's
loopback-only cases ran. Old live suites and unmerged #17/test31 were not invoked.
The totals subtract skips that tests12/13 include in their printed pass denominators.

Python3.11.10 and Telethon1.45.0 were verified; the imported module path was
/private/tmp/tgdata-23-merge-verification/tgdata/__init__.py. All65 Python files under
tgdata/examples passed py_compile and ast.parse(feature_version=(3,7)). This checks
Python3.7 grammar, not execution on3.7. No merged-code test failure or correction occurred.

All3 demo subprocesses exited0:

- Daily continuation: lost acknowledgment replayed without reading the source again;
  4 messages persisted, acknowledged through104.
- Fresh backfill: completed,3 source reads/0 replay reads,3 receipts,5 unique messages;
  daily105/history104 remained independent; successor cancellation preserved.
- Restarted same backfill directory: completed with **0 source reads**, same receipts,
  unique messages and cursors.

Durable counts, exit codes, log hashes and import/runtime evidence are in
merge-verification/results.json. The final merged suite34 output and demo outputs
are adjacent .txt files. Full baseline logs remain in /private/tmp/tgdata23-merged-verification.
No live Telegram permission qualification is claimed by these checks.

## Process verification

The current session's matching turn_context at2026-10-10T16:46:58.498Z reports
**gpt-6-astra/max**, meeting the recorded §9 model/effort requirement. Merge work
retained the warmed implementation and review context. The completed PR state and merge
OID were read back from GitHub, rather than inferred from the local git command.

Original checkout's untracked devdocs/work/7-group-operations/HANDOFF.md and todo.md,
duncan, stray guide and other worktree branches were not staged or changed. Existing
Stage1/2 archives remain. Next feature work is Stage4, not a continuation of historical
PR16 or a restart of the broad rejected implementation.
