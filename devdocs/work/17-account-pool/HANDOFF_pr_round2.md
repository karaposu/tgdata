---
model: gpt-6-astra
effort: max
status: PR_ROUND_2_REJECTED
---
# #17 — return to description/foundation inquiry before another plan

The requested renewed merge check and fresh PR critique are complete. Merge check
1c04cf4 passes fidelity for the selected offline scope. Fresh PR review7d3172e,
selectionfb4623d, **rejects with one Medium**. PR26 remains draft; nothing merged.

This is the second rejected PR round on this branch. CONTRIBUTING §7.4 says:
“If the second round is rejected too, stop re-planning.” Return to desc.md and the
foundation/traverse work before another plan. The skill's separate three-rejection
PARKED threshold is not reached; do not claim three PR rejections or invent a pause.

## Measured missing distinction

**Observing task completion is different from consuming its public outcome.**

The rebuilt source/store boundary preserves data on CancelledError. External close
then directly awaits the cancelled public reader and can receive that object first.
Python's actual Task gives a later application waiter a fresh cancellation exception
with no attached data. No daily/backfill pending delivery was published during genuine
cancellation. The user gets no already-complete records even though account settlement,
quota and physical retirement succeeded.

Eight fresh groups:7 pass,1 fails, reproduced twice with unchanged runtime/expectations.
A separate actual-pool diagnostic spans raw/daily/backfill, caller-first versus close-
first waiting, and ordinary versus repeatedly cancelled close:6 lost-prefix cases and
6 positive controls. It observes prefix1 inside the reader before Task termination,
then prefix0 for close-first callers. All retain charge1 and complete actual SQLite
settlement/native retirement. The `_asyncio.Task` control reproduces saved cancellation
exception consumption directly. See pr-critic.md and evidence/review2/.

Selected guidance: the internal shutdown coordinator should observe quiescence without
taking the application's cancellation payload. This is not a qualified fix or license
to patch. A new public result store/global supervisor is not justified by the evidence.
Keep completed-data retention; do not redefine success to allow the lost payload.

## Branch and preserved work

Worktree `/private/tmp/tgdata-17-replan`, branch `feat/17-account-pool`.
Product remainsa63099e; current dev2ddb852 integrated atceda2bf. No runtime, public doc,
test-suite or example patch followed review. Source and all candidate comparisons remain
unchanged. Original725 checks/3 demos and48-group prebuild still describe their coverage,
not merge approval. Current plan revision5 is marked rejected and kept as the reviewed
blueprint; do not resume its folded steps. Original PR critique is pr-critic_r1.md;
critic.md still records the plan critique. Exactly2 rejected PR artifacts,1 failed
design prebuild. Historical failed r3 evidence remains preserved.

Description Known Blockers and foundation finding's impact note now record this newer
boundary. No new plan or full traverse is claimed in this review-only run. The next
work must requalify outcome consumption at the description/foundation level, then run
the appropriate plan/critic/prebuild/implementation and renewed PR gates.

E1 remains separate: two approved logged-in accounts/shared readable group/existing
bounded allowance. User chose offline-first; no live traffic, joining, login or quota
reset. Main checkout, duncan and unrelated files are untouched. Any eventual merge
needs user go-ahead, excludes work/inquiry/archaeology documents and retains this branch.
