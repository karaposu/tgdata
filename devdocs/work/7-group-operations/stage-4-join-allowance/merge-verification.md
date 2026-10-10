---
model: gpt-6-astra
effort: max
---
# Stage4 merged-code verification

**Merged:** [PR24](https://github.com/karaposu/tgdata/pull/24) into dev at
`f15f1a864f07905aee1c8d679f6039fb5c898ae6`, GitHub confirmed MERGED at
`2026-10-10T19:56:31Z`. The user gave the merge go-ahead, then requested Stage5
through task-impl after this merge. Parent #7 remains open for that final stage.

The merge was prepared in `/private/tmp/tgdata-24-merge-verification` from
dev1ce39d5 and reviewed branch head6ab540d. Both review gates had passed:
merge-check9861573 and fresh critic-d7709ef (0High/0Medium/1Low), committed and posted.
Current matching session metadata at2026-10-10T19:54:04.992Z confirms Astra/max.

## Exact merged tree

Only the six reviewed product paths differ from the first parent: README.md,
docs/join_budget.md, tgdata/__init__.py, tgdata/join_budget.py,
tgdata/smoke_tests/README.md and test_35_join_budget.py. Their bytes equal the
accepted productde1f758. `devdocs/work` and `devdocs/archaeology` were restored from
dev before the merge commit; no Stage4 work folder appears in the merged tree.
The feature branch is retained as the archive. Original-checkout untracked files,
duncan and the stray guide were not touched.

## Checks on actual merge f15f1a8, before pushing

- **529 actual offline groups passed,3 live checks skipped,0 failures**, across
  suites12–19,22–30,32–35. New suite35 passed35/35.
- Three offline demo executions passed: daily continuation, new backfill, restarted
  backfill. Restart read0 source messages;5 unique messages and3 receipts persisted.
- 67 Python files under tgdata/examples compiled and passed Python3.7 grammar checks.
- Full merge diff passed whitespace checking. The worktree remained clean.

Environment: Python3.11.10, Telethon1.45.0, SQLite3.45.3. The suite launcher
`/private/tmp/tgdata24-merged-regressions.py` ran ordinary python -m entry points
from the merge worktree, with four independent suite processes. Suites12/13 used
an explicitly nonexistent config to skip their3 live checks; only test12's local
loopback networking was enabled. No live Telegram, login or join occurred.

Machine counts are retained in evidence/merged-regression-results.json. Full
temporary logs remain at `/private/tmp/tgdata24-merged-verification/`. The3 demo
logs are `/private/tmp/tgdata24-merged-daily-demo.log`,
`/private/tmp/tgdata24-merged-backfill-new.log` and
`/private/tmp/tgdata24-merged-backfill-restart.log`.

No runtime correction, merge conflict or verification failure occurred. The accepted
fractional-expiry Low remains as documented in pr-critic.md; it was not patched during
merge. Physical power loss, native Python3.7 execution and live joining are not claimed.

After these checks, f15f1a8 was pushed to dev as the two-parent PR merge. GitHub
recognized PR24 as merged, and the feature branch remained present. Next: Stage5
joining, as newly requested by the user; its implementation/review is separate.
