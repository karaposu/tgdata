---
model: gpt-6-astra
effort: max
---
# PR21 merge verification

**Result: merged and pushed to dev.**

- User authorization: “go”, following the accepted Stage1 review and explicit merge-go-ahead request.
- PR: https://github.com/karaposu/tgdata/pull/21
- Merge commit: `53306df2c3d87b558be0b7ed4419a42d3229c5f9`.
- First parent / prior dev: `95ed4c76c4d2aba7800d8793b16eb5d54cfba4ec`.
- Second parent / reviewed PR head: `a0d83cd0a1ababecc91e326bdeb5742e0ff463d1`.
- GitHub confirmed state MERGED at `2026-10-08T12:35:16Z`, with that merge commit.
- Archive branch retained: `feat/7-account-operation-foundation`.

## Integration

Prepared a no-fast-forward merge in an isolated checkout at
`/private/tmp/tgdata-21-merge-verification`. Restored devdocs/work and
devdocs/archaeology from the pre-merge dev tree before committing. The resulting
merge changes exactly six product files, byte-for-byte equal to product `2fe9aeb`:
account_operation.py, connection_engine.py, budget_client.py, test32, its README
entry and docs/account_operations.md. No tracked devdocs/work remains on dev;
dev's archaeology is unchanged. Whitespace checks passed.

The approved branch/base were rechecked before push. Both were unchanged; the
merge was pushed normally (no force) only after all tests below passed. The
merge/check/critic workflow documents remain exclusively on the archive branch.

## Tests on the actual merged code

Python3.11.10, Telethon1.45.0. Each runner asserted tgdata imports from the merge
checkout, not the archive or original checkout. Commands used the existing project
venv and `python -m tgdata.smoke_tests.<module>` from the merge checkout.

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
| **Total** | **383** | **3** |

All 18 supported offline modules exited0. The legacy test12/test13 runners count
skips as passes; this table separates them. A nonexistent config path kept the
three Telegram checks skipped. Test12 used narrow localhost socket permission for
its dead/refusing-proxy cases. No live Telegram operation, login or join occurred.

Three offline examples also exited0: daily_continuation --demo, backfill_runs
--demo --directory <temporary> --new, then the same backfill directory without
--new. Compile and Python3.7 grammar checks passed for all 61 Python files in
tgdata/ and examples/. This does not claim Python3.7 runtime execution.

The original eight PR-critic probe groups remain evidence on the identical product;
they are not represented as rerun after this merge. The Low-only review result
remains: unexpected empty self replies during SDK bootstrap can yield Python
errors before normalization, but refusal and cleanup hold.

## Workflow correction and remaining work

One pre-commit verification helper unnecessarily tried `git write-tree` under the
read-only sandbox and was blocked from taking an index lock. It was replaced by
read-only staged-file comparisons and a cached-diff check. No tree content changed
because of that helper, and no product test failed.

#7 remains OPEN because only Stage1 is merged. Next scope is Stage2 health ownership;
group lookup/access, join allowance and joining remain later stages. Old draft
PR16 and its paused broad implementation are historical; this merge did not use
them. The original checkout's untracked HANDOFF.md/todo.md are preserved, and no
duncan or stray guide edit entered dev.
