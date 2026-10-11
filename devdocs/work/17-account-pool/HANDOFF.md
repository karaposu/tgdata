---
model: gpt-6-astra
effort: max
status: OFFLINE_PASS_REVIEW_AND_LIVE_PENDING
---
# #17 account pool — current handoff

**The existing-access delivery is integrated with current dev and ready for its
merge check.** Product commit `4854464` combines dev `68f6bbd` (all five #7 stages)
with the retained #17 router and the focused cancellation/retirement repair.
The working branch is `feat/17-account-pool` at
`/private/tmp/tgdata-17-account-pool`. No #17 PR or merge into dev has happened.

Current evidence: [retirement-rework/verification.md](retirement-rework/verification.md).
There are 619 actual offline passes across 23 suites, with three live skips
excluded; the pool suite is 46/46. Four demo runs, 76 compile/grammar checks
and a separate export's pool suite/demo passed. No live Telegram operation ran.

## What changed

Client retirement now waits for the actual SDK disconnect despite repeated caller
cancellation. A failed retirement blocks reuse until an explicit recheck/close
successfully retries cleanup. Read cancellation keeps the real source child and
pool guard until that child ends. Close waits for active work and all cleanup
attempts; context exit preserves ordinary body errors and caller cancellation.

The current-dev factory seam replaces the obsolete pool base hook. All merged
#7 APIs remain intact. Routing, budgets, persisted restrictions, restart recovery
and the daily/backfill facade were retained and checked for preservation. This
delivery still routes only among groups the configured accounts can already read;
it does not automatically join, add accounts or run a scheduler.

## Read next

The parent [implementation plan](step_by_step_impl_plan.md), [desc.md](desc.md)
and [critic.md](critic.md) explain
the original feature. They are historical records, so references there to #7 being
paused describe the original delivery. The scoped continuation is documented in
[retirement-rework/triage.md](retirement-rework/triage.md),
[desc.md](retirement-rework/desc.md), [plan.md](retirement-rework/plan.md) revision 2,
and [critic.md](retirement-rework/critic.md). The fresh critic's one Medium required
a source-child settlement fix; its mandatory actual-composition experiment passed
before implementation and its selected robust mitigation was folded into the plan.

The public contract is [docs/account_pool.md](../../../docs/account_pool.md).
GitHub [#17](https://github.com/karaposu/tgdata/issues/17) owns current pipeline
status; its original offline-delivery block is retained as history.

## Remaining work

1. Formal merge check of the full diff against dev, the original and scoped plans,
   both selected critiques, #17 status and CONTRIBUTING's model requirement.
2. PR into dev and a fresh in-session PR critique with probes. Neither the plan
   critic nor this implementation verification substitutes for that gate.
3. Merge only after those gates and the user's go-ahead, excluding work documents
   and preserving the feature branch as the archive.
4. Parent Step 9/E1 live qualification remains pending: two distinct approved,
   logged-in accounts with shared readable-group access and a bounded allowance.
   The user supplied one account and selected offline-first implementation.
   Do not claim live failover evidence or infer permission for live login/join.

No work on automatic joining was added merely because #7 is now available.
The original checkout, its untracked #7 handoff/todo, duncan and unrelated work
remain untouched. No dev branch update is part of this handoff.
