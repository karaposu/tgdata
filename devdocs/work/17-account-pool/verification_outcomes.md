---
model: gpt-6-astra
effort: max
status: OFFLINE_PASS_LIVE_E1_PENDING
plan_revision: 7
product: 007c2e4
---
# #17 public outcome ownership — implementation verified

**Product:**007c2e4. **Plan:**revision7, folded after the full P0 pass.
**Result:**750 executed offline groups and3 offline demos pass on the actual feature
branch. Three explicit legacy live skips are excluded from the750. Compilation and
88 Python3.7 grammar checks pass; runtime is Python3.11.10/Telethon1.45.0.
No native3.7 or two-account live qualification is claimed.

Current dev2ddb852d917998d003f9db863fce09a92e9c5712 was already integrated and was
verified unchanged before and after implementation. The tested working-tree hashes
match the committed product. Main checkout, duncan and unrelated work are untouched.

## Plan execution

1. Added PoolReadCapture/PoolReadSnapshot and package exports. The caller retains a
   single-use data destination before a public call; snapshot reads are local and
   immutable, with bounded error-type facts and no retained exception/task graph.
2. Added private invocation completion. `_active_task` is a derived compatibility
   property, not the owner. Close stops the exact live invocation and joins its
   normal completion Future, then retires native clients. It does not consume the
   public Task's signal or wait for unrelated application continuation.
3. Wired early retention of the actual validated source-record buffer through
   BatchEngine/_OwnedSource before later source/media/monitor/store awaits. Incomplete
   media records are excluded. Completed source outcome remains authoritative.
4. Required capture= on the pool's read/get_message_batch/sync_group/prepare_backfill.
   Private reader transport shares one outer writer, without rebinding or global
   context storage. Progress publication retains its caller's lifetime. Selected
   Risk1 resets empty attempt metadata and publishes source identity only after
   verification; no new source is allowed after a complete prefix.
5. Promoted all17 new ownership groups and8 previous PR-review groups into permanent
   test40, keeping35 test/helper function bodies exactly unchanged. Migrated the
   existing pool fixtures, updated the demo to retain named captures, and documented
   required arguments, states, disposal, cancellation wrappers and receipt limits.
6. Verified the actual branch and committed code/tests/public docs separately from
   this report/work evidence. No runtime correction or failed test during this run.
7. **E1 pending:** two approved logged-in accounts/shared readable group/existing
   bounded allowances remain unavailable. User selected one-account/offline-first.

## Verification on the implemented branch

Commands:

```bash
python -m compileall -q tgdata examples
python devdocs/work/17-account-pool/probes/outcome/verify.py
```

The existing Telethon1.45 virtual environment was used. The full runner starts the
three directly changed pool suites first, then all other supported offline suites,
without rerunning the focused suites. It supplies a nonexistent config to the proxy/
device live cases and allows only the existing local refusing proxy test to use
127.0.0.1. Telegram/source tests block sockets and use synthetic wire with real SDK,
SQLite, ReadBudget, batch and progress implementations. No live account or allowance
was used/reset. Parent watchdogs bounded each process; none fired.

| Verification | Result |
|---|---|
| All27 supported offline suites12–19 and22–40 | 750 executed groups PASS;3 live skips excluded |
| Permanent public outcome suite40 | 25/25 PASS |
| Pool feature suite31 | 46/46 PASS |
| Source/provider lifecycle suite39 | 48/48 PASS |
| Worker source/process suites37/38 | 33/33 and25/25 PASS |
| Pool/daily/backfill demos | 3/3 PASS |
| Compile plus Python3.7 grammar | 88 files PASS |
| Runtime/test/example hashes stable during full run | PASS |
| Executable AST equality with P0, eight runtime modules | PASS |
| Promoted qualification test/helper bodies | 35/35 identical to P0 |

The count is the same750 as P0: the former17+8 probe groups now live together in
permanent suite40. P0's original-product negative controls remain historical evidence;
they are not rerun against a product they expect to fail. Their positive replacement
histories are in suite40. This is not a new PR critique or merge approval.

The updated demo selects account222 after account111's wait, delivers4 records,
replays with zero source reads, acknowledges through104, and retains charges111:2 /
222:4. Its original two-record read remains in the caller's capture after close;
local replay has no invented source account. Health diagnostics remain separate.

## Exact parity and deliberate organization changes

Six of the eight runtime files are byte-identical to P0. In account_pool.py, added
public method docstrings describe the required capture and publication/receipt
boundary. In pool_result.py, added the immutable snapshot docstring and removed the
work-document label “Risk1” from a comment. Removing docstrings/comments gives exact
AST equality for all eight files; no runtime control/data decision changed.

Permanent test40 changes only its module harness/imports and combines the two already
qualified case lists; every35 substantive helper/test function body is AST-identical
to the source probes. Existing fixture imports now follow their local package-path
setup so direct script execution does not depend on an installed package. Existing
assertions remain. The demo now retains named captures and asserts their source/replay
metadata, rather than allocating unreachable inline captures as P0's mechanical
signature migration did.

Public README/account-pool/smoke-test docs were updated. Two short cross-reference
paragraphs in daily_continuation.md and backfill_runs.md clarify that their documented
ordinary TgData signatures stay unchanged while the pool requires capture=. Those
small guide edits were discovered during documentation migration; they introduce no
additional product scope or design step. The new test filename was already planned.

No semantic assertion was weakened. No product behavior was changed to repair a
verification failure. Test counts, skips and per-process exit status are recorded in
one complete passing attempt; there was no stitching of targeted results.

## Evidence and remaining gates

- [Complete implementation report](evidence/outcome-implementation/attempt-1/summary.json)
- [Permanent outcome suite output](evidence/outcome-implementation/attempt-1/test_40_pool_outcomes.txt)
- [Pool demo](evidence/outcome-implementation/attempt-1/example_account_pool.txt)
- [P0 report](prebuild.md), [candidate manifest](evidence/outcome/candidate-manifest.json)
- [Current plan](step_by_step_impl_plan.md), [selected plan critique](critic.md)

Steps1–6 are complete. Task-impl's execution gate says “Step gated by an OPEN execution
blocker → stop there.” Step7 needs the maintainer's two approved accounts, shared group
and bounded allowances; no live action was taken. This resource gate is separate from
the completed offline implementation and from the next review work.

**Next:** renewed merge-check → PR update → fresh in-session PR critique of007c2e4
and plan7. PR26 stays draft; the prior rejected critiques remain historical evidence.
No new PR verdict, merge or deployment is claimed. Any later merge needs user go-ahead,
excludes work/inquiry/archaeology docs and retains the feature branch as the archive.
