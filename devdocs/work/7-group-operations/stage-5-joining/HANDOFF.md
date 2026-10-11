# #7 Stage 5 — merged into dev

Updated2026-10-11. User authorized Stage4 merge, `$task-impl stage 5`, its two review
gates, and finally Stage5 merge. **All five stages are now on dev.**

Stage5 branch: `feat/7-account-group-joining`, native issue-linked from that dev base.
Worktree: `/private/tmp/tgdata-7-stage5-joining`.
Product commit: **`4b4ae21`**. Work artifacts are separate commits.
PR: [#25](https://github.com/karaposu/tgdata/pull/25), into dev, `Closes #7`.
Stage5 merged at **`68f6bbd`**; GitHub confirmed2026-10-11T04:58:02Z.
See [merged-code verification](merge-verification.md). Keep this branch as the archive.

The full preparation → task-desc → task-plan → fresh critic-d → required experiment
→ fold → implementation/verification chain is complete. Plan revision2 is `aee1a70`.
Critic `752b8bf` found0 High/Medium/Low and required the cancellation probe; it passed
before runtime edits in `ab26367`. No mitigation or design change was selected.

The public API is `await tg.join_group(target, account_id=...)` with explicit
`TgData(..., join_budget=...)`. It uses merged Stages1–4, maps qualified source outcomes,
and claims immediately before each new SDK mutation send. No raw-client guard, automatic
payment/bot flow, routing or post-ack enrichment. See [verification](verification.md),
[plan](plan.md) and [public contract](../../../../docs/group_joining.md).

Verification: **573 actual offline groups pass,3 live skips**,44 new groups,3 demos
(restart0 source reads),69-file compilation/Python3.7 grammar, and exported-tree44/44.
The first full run's single failure was test29's old exact constructor signature;
adding the planned trailing join_budget parameter/default assertion fixes it,23/23.
No runtime correction or architectural deviation. No live Telegram operation.

**Review completed on2026-10-11 at the user's request:** merge-check.md PASS`5d76839`,
[posted onPR25](https://github.com/karaposu/tgdata/pull/25#issuecomment-6104402488).
Fresh in-session critic-d is ACCEPTED:0 High/0 Medium/0 new Low, with the two inherited
Stage3/4 Lows consciously unchanged. See pr-critic.md and evidence/pr-review-probes.txt:
eight new probe groups passed, including actual process exits, native commit refusal,
policy revocation during proof, shared-cap competition and protocol repair. No runtime
change or failed fresh probe. Model/effort verified Astra/max for both review gates.

**Merge completed on the user's go-ahead:** isolated merge with work documents
excluded and dev archaeology preserved; all13 product blobs match the reviewed code.
The actual merge passed573 offline groups/3 live skips,3 demos (restart0 source reads),
69-file compile/Python3.7 grammar and exported-tree44/44 before push. No conflict,
failed test or runtime correction. The final GitHub bookkeeping updates/closes#7 and
posts the separate archive evidence; no feature work remains in this stage.

Keep the archive work docs off dev and retain the feature branch.
Do not resume old broad PR16 or combine its old rejections with this fresh stage. Leave
the original checkout's untracked HANDOFF.md/todo.md, duncan, the stray guide and the
unmerged#17 branch alone. The original checkout stays at8a43d23 on feat/7-group-operations.
