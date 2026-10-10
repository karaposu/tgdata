# #7 Stage 4 handoff

**State:** implemented and verified on `feat/7-account-join-allowance`.
**Product commit:** `de1f758`. **Base dev:** `1ce39d5` (Stage3 merged via PR23).
**User scope:** Stage4 only; review and merge before Stage5. This is not permission
to resume the old broad PR16 implementation or include unmerged #17.

## Completed pipeline

- Triage `11dbde1`, full sequential traverse concluded `a5305f6`.
- Description `e27879b`, posted as qualification comment6101314461 on #7.
- Plan revision1 `a136033`.
- Fresh in-session critic-d `34508a7`: REORDER, one Medium cancellation compatibility
  finding. Required real ReadBudget/shared-SQLite experiment PASS `3e40528`.
- Selected robust fold, revision2 `8d5a256`; no re-critique of the folded plan.
- Product `de1f758`: standalone join ledger, exports,35 offline test groups and docs.
- Full verification: **529 actual offline passes,3 live skips**,3 demo executions,
  67-file compile/Python3.7 grammar checks. New suite also passed without .git.
  Read verification.md for actual coverage, provenance, commands and limitations.

## Next, after requested review work

1. Run CONTRIBUTING §7.1 merge check against triage, description, revision2 plan,
   selected critic finding, whole product diff and current issue status. Verify §9
   model/effort provenance again; this run's session metadata was gpt-6-astra/max.
2. Publish a Stage4 PR into dev using **Refs #7**, then post the merge check.
3. Run a genuinely fresh in-session critic-d of diff+plan with probes; commit and
   post pr-critic.md. High/Medium rejects under §7.3; apply §7.4 if rejected.
4. Merge only with the user's go-ahead, exclude work docs, verify merged code,
   preserve the branch as archive and leave #7 open for Stage5.

No Stage4 PR, merge check, PR critique or merge has been performed yet.

## Boundary to preserve

JoinBudget is a small local allowance, not a Telegram guard. Numeric account keys
are supplied; Stage5 must consume freshly verified identity and one new claim per
actual attempt/retry immediately before enqueue, with no intervening await. Claims
are never refunded. A failed commit/close can retain usage but grants no permission.
No TgData constructor option, client mixin, joins, read-budget redesign or health
changes should be inferred from this delivery.

Normal opens use existing state; explicit creation is for deliberate provisioning.
Validate malformed state before pruning. Do not copy the historical ledger's
automatic partial-table repair. No receipt/token recovery machinery is needed.

Worktree: `/private/tmp/tgdata-7-stage4-join-allowance`. The user's original checkout
is still on historical `feat/7-group-operations` with unrelated untracked HANDOFF.md
and todo.md; do not stage them, duncan or the stray guide. All stage documents stay
on the feature branch at merge, not on dev.
