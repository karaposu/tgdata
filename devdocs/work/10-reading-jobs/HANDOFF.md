---
model: gpt-6-astra
effort: max
---
# #10 handoff — revision4 folded; combined prebuild next

2026-10-12. Branch `feat/10-reading-jobs`, worktree
`/private/tmp/tgdata-10-reading-jobs`, unchanged current dev `68f6bbd`.
**Product remains `6ee146c`; no product edits during review.**

Revision3 at9ce9ae3 has received a fresh in-session critic-d review and is folded
into revision4 in `step_by_step_impl_plan.md`. Prompt1d6cac7, Phase2 08ee0f2,
then a separate completed selection pass d49f8a0. No additional High/Medium/Low plan risks
were found; zero new remedies were folded. The two original robust PR remedies
were already present in revision3. Exact revision3 is archived in
`step_by_step_impl_plan_r3.md`.

**Next: the complete combined Step1 prebuild**, as required by critic.md's REORDER
verdict. It has NOT passed yet. Only after it passes may implementation begin.
The fold marker must not bypass the pending experiment in a task-impl resume.
No runtime changes, live actions, PR approval or merge occurred in this review/fold.

Fresh review evidence: `probes/revision3_critic.py/.txt`,8 actual process histories
(quiet, held disconnect, creation/publication and held finalization, both signals)
and14 diagnostic histories (all four verbs, delivery-error and fatal projections).
All22 passed with real Worker/SDK/SQLite and OS signals, candidates compiled in
memory, no child polling helper and no live network. These targeted observations
do not replace the full startup/EOF/raw-pipe/cleanup-fault composition in Step1.

The plan has six steps: qualify the complete boundary; implement one process stop
policy; restrict authentication diagnostic vocabulary; add permanent regressions;
document/verify; commit and update the same draft PR for renewed gates. It covers
task creation, synchronous I/O, active work and final settlement together, rather
than treating a cancellation call as proof of shutdown progress.

Planning-only feasibility evidence in `probes/revision3_feasibility.py/.txt` passed
two quiet worker subprocesses, two native asyncio ordering controls and six actual
SDK/Worker authentication cases. Candidates were compiled in memory only. Immediate
cancellation marking plus loop wake works; merely queuing cancellation can let a
ready Task step first. Known authentication metadata survives without raw text.
The full creation/held-cleanup/finalization/pipe matrix remains Step1's mandatory
prebuild, not a claimed PASS from these narrower experiments.

Archived without altering their contents: plans r2/r3, `critic_r1.md`,
`dynamic_critic_prompt_r1.md`. The live `critic.md` now holds the new revision3
review; read its pending experiment before resuming implementation. `pr-critic.md`
remains the first rejected PR review and has not been overwritten.

The user-requested merge check → PR → fresh critique is complete:

- Fidelity check **PASS**, commit `85c0455`, posted at
  https://github.com/karaposu/tgdata/pull/27#issuecomment-6118444113.
- PR https://github.com/karaposu/tgdata/pull/27 targets dev with Closes #10.
- Fresh critic-d prompt `d6d3e7d`; Phase2 critique/probes `837d06f`.
- **Gate REJECTED: 0 High, 2 Medium, 0 Low.** PR is draft. Read `pr-critic.md`;
  Phase3 selects both robust remedies, without editing the Phase2 findings.

The findings are reproducible, not hypothetical:

1. Active SIGINT/SIGTERM calls Task.cancel without waking the selector. Without
   the test's10 ms polling helper, native cleanup has not begun until unrelated
   loop activity occurs. Both signals/repeats fail; an explicit self-pipe wake
   permits real SDK cleanup and exit130/143. The long native-cleanup allowance
   does not explain a failure to start cleanup.
2. Unknown SDK401/406 raw text passes through AuthRequiredError.reason into JSON.
   The regex checks spelling, not trusted origin. SDK-decoded403 and canonical
   AUTH_KEY_UNREGISTERED controls show the intended neighboring behavior.

Probes: `probes/pr_lifetime.py/.txt`, `probes/pr_diagnostics.py/.txt` (9 histories).
All25 existing core and14 process groups passed again. Prior24-suite612-pass/3-live-
skip and packaging records remain accurate for their coverage; neither is evidence
that these new findings are safe. No live Telegram or real credential was used.

**Next under CONTRIBUTING7.4:** required combined prebuild; implementation; renew
merge check and fresh PR critique on the same PR. Do not re-critique the folded
plan just because it is revision4. Old plans are archived as history, not marked
as meaning-gap deprecations. This is the first rejected PR round; a second PR
rejection goes back to description/traverse under7.4. Do not merge or close #10.

The worker remains explicit-account, serial JSON lines over caller-owned pipes,
with temporary verified clients and existing budgets. These findings do not justify
a queue, HTTP service or pool redesign. Live deployment remains separately pending.

Formal first-cycle history: feature-heavy triage, traverse, desc, plan, planning
critic/prebuild, folded revision2, product6ee146c, verification6c60832. The transport
default was a declared engineering choice after an unanswered optional question.
Current §9 metadata confirms GPT-6 Astra/max; both review gates ran in-session.

**Prior #17:** PR26 remains draft/rejected, revision3 re-plan next, at `71502e5` in
`/private/tmp/tgdata-17-account-pool`. It is independent and no runtime was copied.
Original checkout at `8a43d23`, untracked HANDOFF/todo, duncan and other worktrees
remain untouched. No dev merge, live action, existing allowance reset or deployment.
