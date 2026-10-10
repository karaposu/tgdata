# #7 Stage 4 handoff

**State:** merged into dev via PR24 at `f15f1a8` after the user's go-ahead and
merged-code verification. `feat/7-account-join-allowance` is the retained archive.
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
- Merge fidelity **PASS `9861573`**, current session Astra/max verified for §9.
  [PR24](https://github.com/karaposu/tgdata/pull/24) targets dev and uses Refs #7;
  [merge check posted](https://github.com/karaposu/tgdata/pull/24#issuecomment-6101488254).
- Fresh in-session critic-d **ACCEPTED `d7709ef`:0 High/0 Medium/1 Low**, with seven
  additional real SQLite/process probe groups (one reproduces the Low).
  [Critique posted](https://github.com/karaposu/tgdata/pull/24#issuecomment-6101530562).
  The product is unchanged. No Stage4 rejection or re-plan is triggered.

## Merge complete — next is Stage5

PR24 merged at `f15f1a864f07905aee1c8d679f6039fb5c898ae6`, confirmed by GitHub
2026-10-10T19:56:31Z. Only the six reviewed product paths landed; this folder was
excluded and dev archaeology preserved. Actual merged code passed529 offline groups,
3 live skips,3 demos and67-file compile/grammar checks before push. See
merge-verification.md and its retained count evidence.

The user subsequently requested `$task-impl stage 5`. Start that stage from devf15f1a8
on its own natively linked issue branch. Keep #7 open, and keep this branch as archive.

## Consciously retained Low

At an accepted nonbinary fractional clock boundary (1000.2 →87400.2), the expiry
hint can say retry_after0 while pruning still retains the claim for one representable
float step (about14ps in the probe). This is a conservative refusal, not lost usage
or excess admission. §7.3 permits this Low; see pr-critic.md for exact evidence and
limits. Do not silently patch it during merge or inherit a claim of perfect numerical
deadline identity. No Medium/High findings remain.

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
