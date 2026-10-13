---
model: gpt-6-astra
effort: max
status: IMPLEMENTED_OFFLINE_REVIEW_PENDING
---
# #17 — plan7 implemented and verified; renewed review is next

The user authorized implementation under revision7 after the full combined P0 pass.
**Product commit:**007c2e4. Steps1–6 complete; step7's live E1 remains gated.
The code, permanent tests, example and public docs are in a separate product commit;
work evidence is committed separately. PR26 remains draft/unmerged, awaiting renewed
merge-check and fresh PR critique of this new product. No merge authorization inferred.

## Read before continuing

- [Verification report](verification_outcomes.md) and
  [complete passing run](evidence/outcome-implementation/attempt-1/summary.json).
- [Folded plan7](step_by_step_impl_plan.md), [description5](desc.md),
  [plan critic](critic.md) with its full-prebuild PASS.
- [P0 report](prebuild.md), qualified before implementation in9772541.
- [Public outcome finding](../../inquiries/2026-10-13_11-46__17-public-outcome-ownership/finding.md).
- Existing pr-critic.md/pr-critic_r1.md describe the two prior rejected products;
  merge-check.md also remains historical. Neither is approval of007c2e4.

## What shipped on the feature branch

The pool requires caller-retained PoolReadCapture at read/get_message_batch/sync_group/
prepare_backfill. One explicit private writer carries actual complete records through
source, account and progress work. Running snapshots are interrupted data; only outer
public-call exit finalizes. They do not imply a durable receipt or accepted progress.

A private invocation completion Future replaces the containing application Task as
close's completion target. Close retains owned work/native retirement while allowing
unrelated application continuation to outlive the library call. Source/account closure
and caller-owned progress publication retain different lifetimes.

The selected critic correction resets source metadata on no-prefix failover, attaches
verified identity to actual observations and forbids another attempt after complete
data. Routing, quota, uncertain-write refusal, receipts, reentry guards, passive health
and quarantine semantics remain the existing mechanisms. No supervisor/result database.

## Verification and parity

750 executed offline groups+3 demos pass;3 explicit live skips excluded. Pool31:46/46,
lifecycle39:48/48, new outcome40:25/25, worker37:33/33 and worker38:25/25. All27 supported
offline suites ran in one complete attempt. No watchdog or failed test. Compilation
and88 Python3.7 grammar checks pass on Python3.11.10/Telethon1.45.0; no native3.7 claim.

All eight runtime modules match the qualified candidate's executable AST. Only public
API docstrings and a work-label comment differ in two files; six files are byte-identical.
The17 new and8 previous-review P0 groups are combined in permanent suite40;35 function
bodies remain identical. Fixtures were migrated, their import placement made suitable
for direct invocation, and the demo now retains named captures. README/pool/smoke docs
and two small daily/backfill cross-references explain the intentional pool API change.
No runtime repair or weakened assertion was needed during implementation verification.

Current dev2ddb852 was already integrated and was verified unchanged before/after this
run. Recheck it before the later merge-check. All tested source hashes are recorded;
main checkout/untracked HANDOFF/todo, duncan and unrelated work were untouched.

## Next work

Run renewed merge-check against current dev and actual product007c2e4, update the same
PR26 and run fresh critic-d against the implemented diff plus plan7. Preserve old
review documents before creating the new canonical artifacts. This is still the same
branch/history: two rejected PR rounds and one earlier failed design prebuild. Do not
mistake P0 or the750 implementation checks for a fresh PR soundness verdict.

E1 remains separate: two approved logged-in accounts/shared readable group/existing
bounded allowances after offline verification. The user selected one-account/offline-
first; no login, join, quota reset or real Telegram call was made. Task-impl requires
stopping at that OPEN execution gate. Any later merge still needs user go-ahead and
excludes work/inquiry/archaeology artifacts while keeping the feature branch archive.
