---
model: gpt-6-astra
effort: max
---
# Stage 1 source and scope

## Original request

```text
|  |  |  |
|---|---|---|
| **1\. Define the contract** | Specify operations, run identity, state rules and failure scenarios; critique the plan. | Every operation has clear retry, conflict and durability semantics |\
\
lets start by implementing this via $task-impl ,
```

The user supplied `/Users/ns/.agents/skills/task-impl/SKILL.md` and selected only
Stage 1 of issue #19. Execute desc → plan → critic-d → selected fold → implement
this document delivery → verify. Do not enter Stage 2 or run live Gate A.

## Published plan

[Issue #19](https://github.com/karaposu/tgdata/issues/19) is the published full staged
plan, revision 2: eight stages, 28 steps and mandatory real-Telegram gates after
Stages 2, 4, 6 and 8. Its original body is preserved on GitHub. Imported working
copy: [staged-plan.md](../staged-plan.md); relative source links have been adapted
for this new branch. No implementation checkbox is completed by copying the plan.

Issue body SHA-256 at intake: `30e464730a4a110d47635fda14b7247335e74faeec4e96a3722e2a3bc8a84e84`.

## Behavioral basis

The completed two-pass lifecycle inquiry is retained at git commit `d1f37f7` in
`devdocs/inquiries/2026-10-06_17-56__backfill-run-lifecycle/` on the local #18 branch.
Its finding and both critiques were consumed in this same session. Its 22 final
histories were reasoning checks, not an implemented lifecycle passing tests.
The source branch's inquiry commits remain unpublished; do not manufacture a GitHub
permalink to them. Issue #19 embeds the derived recommendations and complete plan.

Inherited behavior: durable intent distinct from process/attempt; independent pending,
accepted and exhausted facts; exact replay and run-scoped ack; qualified origin;
post-attempt pacing; pause-reading; terminal cancellation; accepted control order;
bounded historical recognition without expiring live obligations; known-run recovery
never bootstraps silently; caller-owned archive/scheduler/receiver acceptance.

The user subsequently required live validation between stage pairs. Expected results
must precede tests; failures/inconclusive evidence stop dependent work. This is part
of the contract, not an optional future check. Actual account/group/fixture selection
is still a later execution input; a text preference was requested asynchronously.

## Baselines and preservation

Stage 1 branch: `feat/19-backfill-run-lifecycle`, created from remote dev
`45bab7172621f576fa5e4b3265f87ec20da04fd5` with `gh issue develop 19`.
Daily/fixed-window source inspected separately: #18 at `e9b5154` (runtime commit
`e87754e`), not yet merged into dev. Stage 1 imports no prerequisite runtime code.
Before Stage 2 implementation, use an integrated/authorized base containing it.
Existing #7 and #18 worktrees and uncommitted files remain untouched.

No account credentials, personal config, production destination or live Telegram
operation is needed for this document delivery. No duncan edits, PR or merge.
