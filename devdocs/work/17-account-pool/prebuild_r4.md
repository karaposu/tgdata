---
model: gpt-6-astra
effort: max
status: PASS
plan_revision: 4
---
# Whole-operation prebuild — passed before production changes

**P0 PASS, 2026-10-13.** Final combined run:48/48 pool groups, worker37:33/33,
worker38:25/25. No watchdog fired, no runtime candidate correction was needed.

Baseline: product71502e5 plus current dev2ddb852; combined Git tree
7d2dc2393c473cf6cdf9642c60f7c40618b21404. Dev was rechecked unchanged afterward.
Fresh isolated export, with the known batch constructor union; source, ledger,
SQLite and progress engines are real. Telethon1.45.0/Python3.11.10. Synthetic wire
supplies server replies; actual SDK/SQLite creates records, quotas, tokens and receipts.
No network or real accounts used. Runtime branch stayed unchanged throughout P0.

Candidate implements steps2–5 and selected Risk1 in the export, not the branch.
The78 runtime Python files stayed byte-identical during tests; manifests record all
hashes and changed files. New files pass Python3.7 grammar; no native3.7 claim.

## What was established

The previous37 groups all pass unchanged in meaning. Its failing storage case now
returns PoolStorageError with prefix100 and daily pending=true, caller requests0,
charge200, no second source. Before actual settlement the token stays unresolved;
after actual commit the saved wait7200 remains and token is cleared. No rollback
or fresh permission is inferred from a failed response.

Eleven added groups cover pool load/admission, twelve raw/daily/backfill settlement
histories, daily/backfill load/start/admission, eight publication histories, ack and
controls, pool and backfill exact recovery, repeated caller stop during held real
provider commits, raw completed-result cancellation, pre-start stop, sync session
interruption, and45 provider-driven control refusals. Data, durable rows, actual
budget, SDK requests and child termination are asserted separately.

Before/after-write provider interruption maps to local errors. Backfill admission
never reconciles into permission; non-admission exact read-back can confirm the
existing candidate. Error prefixes are interrupted data, not invented end evidence
or receipts. Actual caller cancellation remains cancellation and retains complete
known data while joining I/O. State-only replay/ack survives pool close. All source/
retirement/observation positive controls and both current worker suites hold.

## Attempts and one local fixture correction

Attempt1:46/46+33/33+25/25, initial matrix. Final coverage audit added backfill recovery
and raw completed-settlement cancellation. Attempt2:47/48+33/33+25/25. Its new recovery
fixture expected two pages charged but supplied only one pending first page. Corrected
input supplies a real100-record first page then pending second page; original expected
charge200/state/retry/cursor assertions are unchanged. Candidate runtime unchanged.
This is a local fixture correction, not a failed design premise or another PR rejection.
Exact failed fixture and hash are preserved; see evidence/restart/fixture-correction.md.
Attempt3:48/48+33/33+25/25 in one full combined run. No weakened assertion or silent fix.

## Reproduce

```bash
python devdocs/work/17-account-pool/probes/restart/export.py
python devdocs/work/17-account-pool/probes/restart/build_candidate.py
python devdocs/work/17-account-pool/probes/restart/run.py
```

Use the existing Telethon1.45 environment. Export uses an isolated Git index, not a
branch mutation. The parent runner bounds each child process and records numbered
attempts. The48-group runner consumes the real candidate export; it does not fake
reader results or install the deprecated candidate.

Evidence: [final gate](evidence/restart/attempt-3-summary.json),
[pool cases](evidence/restart/attempt-3-combined.txt),
[worker source](evidence/restart/attempt-3-worker37.txt),
[worker process](evidence/restart/attempt-3-worker38.txt),
[candidate hashes](evidence/restart/candidate-manifest.json),
[baseline export](evidence/restart/export-manifest.json).

Passing P0 authorizes fold and implementation under task-impl, not merge or live
qualification. E1 is still pending; full offline regression follows runtime integration.
