---
model: gpt-6-astra
effort: max
status: OFFLINE_PASS_LIVE_PENDING
---
# Verification — #17 existing-access account pool

**Offline implementation PASS at product commit `964d082`.** The current user
selected “One account for now; build and test offline first.” No #17 Telegram
connection/login/join was made. Step 9 live qualification remains pending; this
report is not a merge-check or a fresh PR critique.

## Results

**393 actual supported offline checks passed.** Three explicit legacy live skips
are excluded from that number. The new account-pool suite passed 36/36, including
four owned process exits immediately before/after actual admission/settlement
writes. Existing supported checks passed 357/357. Python 3.11.10; Telethon 1.45.0.

| Suite | Actual passes |
|---|---:|
| 31 account pool | 36 |
| 30 backfill integration | 15 |
| 29 public backfill | 23 |
| 28 controls | 32 |
| 27 pacing/recovery | 32 |
| 26 completion | 16 |
| 25 delivery | 41 |
| 24 backfill state | 23 |
| 23 fixed windows | 22 |
| 22 daily continuation | 25 |
| 19 message batches | 33 |
| 18 read budgets | 28 |
| 17 stored sessions | 12 |
| 16 health events | 21 |
| 15 login checks | 11 |
| 14 flood threshold | 11 |
| 13 device identity | 5; one live skip |
| 12 proxy | 5; two live skips |
| 11 explicitly awaited offline helpers | 2 |

All three offline examples passed. The new example selected account 222 after a
synthetic wait on 111, stored four messages, acknowledged through 104, and replayed
pending data with zero source reads. Charges remained 111:2 and 222:4.

All 66 Python files under tgdata/examples plus setup.py compiled and parsed with
Python 3.7 grammar using Python 3.11.10. This is not a Python 3.7 runtime claim.
An isolated built package, with smoke tests and all work documents removed, imported
the public pool API and ran the same offline example successfully.

Evidence: `verification/summary.json`, `offline-results.json`, per-suite logs,
`compile.json`, `package-build.txt`, and `isolated-package.txt`. The retained runner
is `verification/run_offline.py`; at most three independent subprocesses and a
180-second bound per job. Legacy12/13 received an explicitly nonexistent config,
so only their loopback/offline portions ran. No prior account ledger was touched.

## Corrections during implementation and verification

1. The first test31 run passed 31/32. Its backfill fixture supplied history in
   ascending wire order, whereas the actual SDK reverses Telegram's descending
   reply. Corrected that synthetic reply to 102,101 and retained the two-message
   assertion. The complete suite then passed 36/36, including four additional
   recovery/cleanup/process groups, and passed again in the supported sweep.
2. The staged diff check found one extra blank line at the extracted facade's EOF.
   Removed it; no behavior changed. Staged diff check then passed.

No runtime test failure required a fix. No architectural deviation, expectation
weakening or bypass of a task-impl gate occurred. Shared factory and BatchEngine
hooks retain default behavior; the supported legacy suites substantiate that claim.

## Plan execution

Steps 1–8 complete: strict values/store, owned source, router, administration/cleanup,
shared progress facade, actual-composition tests, docs/example, verification/product
commit. Product changes are one 15-file commit, separate from all work records.

Step 9/E1 remains OPEN: two approved distinct logged-in accounts, a shared readable
group and bounded allowance. The user explicitly chose offline-first work. Do not
infer permission to reuse earlier live gates, reset budgets or log in automatically.

## Material limits

One owning process/event loop, exclusive session ownership, caller-controlled
single reader per group and trustworthy UTC are required. Timeout is cooperative.
Results remain account-visible history; no union-coverage proof. Unknown source
attempts require exact explicit recovery. Live Telegram/proxy behavior for this
two-account composition is unqualified. Automatic joining stays deferred and #7
stays paused. Formal merge-check, PR publication, fresh PR critique and merge have
not run for #17.
