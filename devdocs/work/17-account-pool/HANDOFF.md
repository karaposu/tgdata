---
model: gpt-6-astra
effort: max
status: PREBUILD_FAILED_REPLAN_REQUIRED
---
# #17 account pool — current handoff

**Revision3's combined prebuild failed. Do not implement the deprecated plan.**
The user requested re-planning around the foundation finding followed by a small
real-component prebuild. Those preparation steps ran; runtime implementation did not.
Current worktree: `/private/tmp/tgdata-17-replan`, existing issue-linked branch
`feat/17-account-pool`. Original partial worktree and main checkout were preserved.

## Current result

[Prebuild report](prebuild.md):36/37 pool case groups passed; worker33/33 and25/25
passed on an isolated #17+current-dev export. One group disproved the complete
outcome guarantee: an asynchronous state provider's own cancelled future during
settlement returned CancelledError with caller cancellation requests0. A real100-
record prefix was absent from the public error and daily pending state. This occurred
before and after the actual SQLite commit. Charge200 remained; before commit the
account attempt stayed unresolved, after commit the known7200-second wait was saved.

The provider performed storage only; it did not reenter pool lifecycle. The tested
role contract therefore does not exclude the failure. Caller cancellation and
provider completion need distinct handling at this additional awaited boundary.
No runtime patch, folded revision4 or verification claim followed the failure.

## Read next

- [Revised description](desc.md), including the CLOSED measured false premise.
- [Deprecated revision3](DEPRECATED_step_by_step_impl_plan.md); retain as evidence,
  never execute it. The canonical step_by_step_impl_plan.md is intentionally absent.
- [Fresh plan critic](critic.md), result FAIL under its mandatory experiment.
- [Prebuild report/scripts/results](prebuild.md), including exact candidate/source hashes.
- [Foundation finding](../../inquiries/2026-10-12_19-42__17-account-pool-foundations/finding.md),
  now carrying the later prebuild evidence pointer.
- [First rejected PR review](pr-critic.md) and [its handoff](HANDOFF_pr_round1.md).
  Original plan/critic/description are preserved as *_r2.md / critic_r1.md; the
  scoped retirement work remains in retirement-rework/.

## Next work

Clarify outcome/cancellation ownership for awaited state-provider work, including
actual caller stop, provider-internal cancellation and uncertain commits. Preserve
completed source data through local storage interruption without detaching a live
write or treating cancellation as proof of rollback. Then write a replacement plan,
freshly critique it and rerun the complete combined gate before runtime changes.
Do not blanket-convert CancelledError, retry CAS into permission or weaken the test.

The rest of the candidate remains useful evidence: passive reports, source completion,
scope/refusal controls, native cleanup, budgets and source-free daily/backfill all
passed their listed cases. This does not qualify the full plan or PR.

## Status and limits

This is **one failed prebuild**, not a second rejected PR review. There is still only
one rejected PR critic (two Mediums); PR26 remains draft/unmerged. The new fresh plan
critic found0 additional content risks but required this experiment, which then
falsified an untested composition. Keep both facts visible.

Working-branch runtime remains product4854464 at71502e5. Current dev2ddb852 was used
only in an isolated export; its batch conflict resolution is recorded, not merged
onto the runtime branch. Two-account live E1, production implementation, full suite,
renewed merge check/PR critique and user-authorized merge remain pending.

No live login/read/join or real allowance reset; all probe credentials/state are
synthetic. Main checkout's untracked HANDOFF/todo, duncan and unrelated work remain
untouched. Preserve all work/inquiry docs on the feature branch archive; exclude them
from any later dev merge. No protected branch or PR merge was performed.
