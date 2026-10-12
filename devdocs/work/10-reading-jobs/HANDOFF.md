---
model: gpt-6-astra
effort: max
---
# #10 handoff — PR27 rejected; revision3 re-planning next

2026-10-12. Branch `feat/10-reading-jobs`, worktree
`/private/tmp/tgdata-10-reading-jobs`, unchanged current dev `68f6bbd`.
**Product remains `6ee146c`; no product edits during review.**

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

**Next under CONTRIBUTING7.4:** revision3 re-plan using the whole critique and
desc; fresh plan critic; fold into revision4; required prebuild; implementation;
renew merge check and fresh PR critique on the same PR. Do not apply isolated
findings as patches in this review run. The skill verdict REORDER preserves the
existing plan as history and requires a candidate experiment before rebuilding;
no meaning-gap deprecation was triggered. Do not merge or close #10.

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
