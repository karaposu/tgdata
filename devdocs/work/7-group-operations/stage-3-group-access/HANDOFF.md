---
model: gpt-6-astra
effort: max
---
# #7 Stage 3 handoff

Implementation is complete on **feat/7-group-lookup-access**, product **a2afc05**.
Base dev30ba706 already contains Stages1/2. Active task folder is this directory.
The old broad feat/7-group-operations worktree is historical, not the branch to resume.

- Public lookup_group and check_group_access require an expected numeric account ID.
- Immutable qualified lookup/access values, bounded explicit reference resolution,
  one budgeted history probe and conservative account-owned health confirmation.
- Telethon1.45.0 target; dependency minimum1.45. No join/allowance/pool routing change.
- Revision2 plan d15b5d5 incorporates critic48a662b M1 (typed numeric round trip).
- Verification:494 actual offline groups passed,3 live skips;3 demos;65 Python files
  compiled/3.7 grammar checked. See verification.md and its durable evidence.
- Known SDK cache errors preserve their original meaning; offline evidence is not live
  permission qualification. No foundation runtime or legacy selection changes.

**Next:** merge check → publish a partial-stage PR into dev (Refs #7) → fresh PR critic.
Then merge only with the user's go-ahead, retaining work docs on this archive branch.
Stage4 join allowance and Stage5 joining remain later work; keep parent issue7 open.

Preserve original checkout untracked HANDOFF.md/todo.md, duncan and the stray guide.
Do not fold in unmerged #17 or resume historical PR16. This Stage3 task has one plan
critique with a selected Medium and no PR review/rejection yet.
