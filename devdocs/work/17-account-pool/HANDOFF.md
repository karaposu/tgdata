---
model: gpt-6-astra
effort: max
status: PR_REJECTED_REVISION_3_REQUIRED
---
# #17 account pool — current handoff

**PR #26 is rejected: two Medium observer/ownership defects; revision-3 re-planning
is required.** Product commit `4854464` combines dev `68f6bbd` (all five #7 stages)
with the retained #17 router and the focused cancellation/retirement repair.
The working branch is `feat/17-account-pool` at
`/private/tmp/tgdata-17-account-pool`. [PR #26](https://github.com/karaposu/tgdata/pull/26)
is open as a draft after review; no merge into dev has happened.

The [merge check](merge-check.md) passed at `cdcfd63` and was posted on the PR.
The [fresh PR critique](pr-critic.md), initially committed at `4464021`, reproduced:

- A callback awaiting its own cancelled future makes completed source work look
  like caller cancellation: prefix100 and FloodWait7200 miss normal settlement.
- Callback-created/awaited close bypasses exact-task reentry checks and forms a
  retained wait cycle, hanging the read/close before SDK disconnect begins.

Eight fresh probe groups ran; six boundaries held and these two defects reproduced.
No runtime patch followed the rejection. The selected robust directions are inputs
to re-planning, not approval to patch the existing blueprint. The user queued #10
after this review; preserve #17 here while that separate task begins.

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

1. Revision-3 re-plan taking `pr-critic.md` and both original/scoped plans as input,
   required by CONTRIBUTING §7.4. Preserve this first rejected round's evidence.
2. Fresh plan critic, fold into revision 4, run the required candidate experiment,
   implement, verify and renew both review gates on the same PR. If a second PR
   round is rejected, return upstream to description/traverse under §7.4.
3. Merge only after accepted gates and the user's go-ahead, excluding work documents
   and preserving the feature branch as the archive.
4. Parent Step 9/E1 live qualification remains pending: two distinct approved,
   logged-in accounts with shared readable-group access and a bounded allowance.
   The user supplied one account and selected offline-first implementation.
   Do not claim live failover evidence or infer permission for live login/join.

No work on automatic joining was added merely because #7 is now available.
The original checkout, its untracked #7 handoff/todo, duncan and unrelated work
remain untouched. No dev branch update is part of this handoff.
