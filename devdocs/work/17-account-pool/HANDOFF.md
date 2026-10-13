---
model: gpt-6-astra
effort: max
status: OFFLINE_PR_REVIEW_PASS_LIVE_E1_PENDING
---
# #17 — renewed PR review passed; live qualification remains

User authorized renewed merge check → PR update → fresh PR critique. All three are
complete for product007c2e4/folded plan7 on feat/17-account-pool. **Round3 PR decision:
PASS offline,0 High/Medium/Low.** The5 fresh groups cover26 histories and pass in one
complete attempt. No product changes, re-plan or deprecation were needed.

**PR26 remains draft and unmerged.** Two-account live E1 is pending; any later merge
still needs user go-ahead. Exactly two historical PR reviews were rejected; this third
round passed. Preserve those reviews and all earlier failed/prebuild evidence.

## Authoritative records

- [Fresh PR critique](pr-critic.md) and [prompt](pr-dynamic-critic-prompt.md), prompt
  commit3f890cd. Full23-file product diff and plan7 reviewed in the same warmed session.
- [Renewed fidelity check](merge-check.md), initially committed001d920 and posted at
  https://github.com/karaposu/tgdata/pull/26#issuecomment-6153199803.
- [Fresh probe run](evidence/review3/pr-attempt-1.json) and
  [observations](evidence/review3/pr-attempt-1.txt), exact probe/source hashes preserved.
- [Implementation verification](verification_outcomes.md) and
  [750-group complete run](evidence/outcome-implementation/attempt-1/summary.json).
- [Folded plan7](step_by_step_impl_plan.md), [description5](desc.md), [plan critic](critic.md),
  [P0](prebuild.md), and the
  [public ownership finding](../../inquiries/2026-10-13_11-46__17-public-outcome-ownership/finding.md).
- Prior reviews: pr-critic_r1.md/pr-critic_r2.md and merge-check_r1.md/merge-check_r2.md.
  Plan critic remains distinct from PR critique; no prior evidence was overwritten.

## What was established

Pool read/get_message_batch/sync_group/prepare_backfill require a caller-retained,
single-use PoolReadCapture. Actual complete records remain available through source,
account and public-progress work. Only outer public-call exit finalizes the capture.
Available data is independent of Task cancellation payloads and does not grant a receipt.

Private invocation completion lets close stop/join source/account work and native
retirement without joining the containing application Task. Progress publication can
continue under its own caller. Routing, quotas, durable uncertainty, recovery, passive
health and quarantine remain separate authorities/mechanisms.

The fresh probes observe:
- cancelled shield waiter, surviving inner read:100 early records→101 final, charge101;
- two different groups/accounts during shutdown:1 record/account111 and100/account222
  stay separate; publication can succeed, fail or commit during cancellation after close;
- one application Task continuing into another pool survives closing the first;
- post-source clock/media failures retain records without pending/false health;
- second admission/identity failures preserve accurate provenance and charge no history
  to the unstarted/refused second source.

The full implementation run still applies:88 Python hashes unchanged,750 executed
checks+3 demos,3 live skips excluded;15 adjacent modules identical to dev;8 runtime AST
matches to P0;35 promoted functions unchanged;10 facade methods equal to dev. Fresh
review made no runtime or assertion correction. Python3.11.10/Telethon1.45.0 executed;
native3.7 is unqualified. Dev2ddb852 verified unchanged at review start and verdict.

## Remaining work and boundaries

**E1:** obtain two approved logged-in accounts, a shared readable group and their
existing bounded read allowances, then run plan7's read-only live step7. The user
selected one-account/offline-first; no second account, login, join or allowance reset
was inferred. Offline review is complete but cannot qualify actual service visibility
or proxies. No extra redesign is prescribed by this passing review.

Before any merge, obtain the user's explicit go-ahead, recheck current dev, and follow
§7.6/§7.7: exclude work/inquiry/archaeology artifacts while preserving dev's existing
docs and keeping this feature branch as archive. Test the merged product as required.
Do not close issue17 or treat the draft PR as merged.

Main checkout remains feat/7-group-operations with its untracked HANDOFF.md and todo.md
unchanged. Duncan and unrelated work were not staged. The review/work artifacts are
committed separately from product007c2e4; their GitHub links/status are recorded on PR26
and issue17.
