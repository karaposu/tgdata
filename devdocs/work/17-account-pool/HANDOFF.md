---
model: gpt-6-astra
effort: max
status: OFFLINE_IMPLEMENTED
---
# #17 — next: renewed merge check and fresh PR critique

The user requested a from-scratch task-impl restart with cancellation ownership
covering storage too. That chain is complete through offline implementation/verification.
Do not resume the deprecated revision3 plan or the old rejected PR implementation.

- Worktree: `/private/tmp/tgdata-17-replan`, branch `feat/17-account-pool`.
- Product:a63099e; dev2ddb852 integrated atceda2bf using the exact P0 union.
- Active plan:step_by_step_impl_plan.md revision5; description revision4.
- Fresh plan critic:6c81299; one Medium, robust selected52f31c9; folded after P0 at3f535d1.
- P0:48/48 pool +33/33 worker +25/25 process tests, no watchdog or runtime candidate fix.
- Full regression:725 executed offline checks passed;3 explicit legacy live skips;
  all3 examples, compilation,86 Python3.7 grammar checks and package imports passed.
- All8 changed runtime modules exactly match the passed candidate. See
  verification_restart.md and evidence/restart/final-summary.json.

The pool now distinguishes component interruption from actual caller cancellation
across source and pool/daily/backfill storage. It joins actual work before releasing
its caller, preserves known batches without inventing receipts, retains uncertain
admission safeguards and replaces application callbacks with bounded passive health
observations. Same-pool provider control refuses at both operation entry and close.
Routing, budgets, durable account permissions and progress engines are reused.

One local P0 fixture correction and one collector-format correction are recorded;
neither changes a runtime premise or weakens an expected outcome. Original failed
r3 probes/artifacts and the one rejected PR review are preserved. The first foundation
inquiry points to the archived failed report so its historical note is not misleading.

**Next authorized workflow when requested:** renewed merge-check against triage/
desc/plan/critic plus current dev, then refresh draft PR26 and run a fresh in-session
PR critique. Keep PR26 draft until gates pass. No new PR is needed. Do not mistake
this plan critique or full regression for the required fresh PR critique.

**E1 pending:** two approved logged-in accounts, a shared group and their existing
bounded allowance. User chose one account/offline-first; no live calls, login, joining
or budget reset occurred. Plan step8 is stopped at task-impl's execution gate.
#7 being merged does not add automatic joining to this selected delivery.

Merge still needs user go-ahead and must exclude work/inquiry/archaeology documents
from dev, preserve this branch as archive, and keep #17's broader automatic-joining
scope explicit. Main checkout, duncan and unrelated work remain untouched.
