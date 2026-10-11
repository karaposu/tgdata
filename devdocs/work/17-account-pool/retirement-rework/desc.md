---
model: gpt-6-astra
effort: max
---
# #17 — retirement safety and current-dev integration

**Session warmth:** same-session #7 implementation/review/merge and full #17
assessment at branch8d3db76, targeting dev68f6bbd. Pool source/controller/state,
progress facade, real SDK disconnect, current factory and #7 owned cleanup were
read at complete relevant implementations. No archaeology refresh is claimed.
This is the scoped continuation of the existing unmerged feature, with original
description/plan/critique retained in the parent folder.

## Problem Statement

AccountPool promises one owned source/administrative operation at a time and no
reuse before an old client has retired. Cancelling `recheck_account` currently
breaks that promise: Telethon shields its own disconnect task, while the awaiting
pool call returns cancellation and releases the operation slot. The old client
remains stored and a new read can finish while that disconnect is still running.
This was reproduced on the untouched branch with the real SDK and synthetic wire.

The branch also predates #7's merged factory/identity/group APIs. Its core pool
already works, but its private factory hook and constructor assertion need alignment
with current dev. These are scoped integration/lifecycle changes, not evidence
that selection, durable restrictions or acknowledgment mechanisms must be rebuilt.

## User Value Proposition

A cancelled account repair or shutdown cannot leave cleanup racing later work.
Applications can retry an interrupted repair after actual retirement settles,
and receive an explicit local refusal when failed cleanup still prevents safe reuse.
The pool retains its long-lived per-account clients and reusable routing/progress
behavior while coexisting with current TgData/group APIs.

## Success Criteria

1. Pending retirement retains exclusive ownership until one actual SDK disconnect
   attempt settles, including repeated caller cancellation. No read/recheck or
   replacement client begins on that source before the boundary is established.
2. Successful retirement clears the old client/config/verified identity before
   cancellation is delivered. A later explicit operation can load a fresh client.
   Ordinary retirement failure or SDK-internal cancellation refuses source reuse
   until an explicit retry succeeds; neither is treated as successful closure.
3. Caller cancellation remains cancellation after cleanup. Repair/shutdown preserve
   completed source outcome and credential-reload guarantees; ordinary cleanup
   failures do not replace an existing body/source exception. No shutdown deadline
   is invented for a hanging SDK cleanup.
4. Current dev68f6bbd is incorporated without removing #7 APIs or changing its
   source/health/allowance contracts. Pool client policy uses the existing factory
   option API; duplicate factory mechanisms are not retained merely to resolve Git.
5. Router strategies, shared ReadBudget accounting, saved restrictions/unknown
   attempts, partial-message handling and daily/backfill acknowledgment stay intact.
   No durable-state format or public pool constructor/method signature changes.
6. Real SDK cleanup with controlled transport delays/failures verifies busy-state,
   cancellation, failure/refusal/retry, safe credential reload and context-manager
   behavior. New tests plus every supported offline suite, demos and export checks
   pass on Telethon1.45.0. Evidence distinguishes assessment from final verification.

## Scope Boundaries

Existing-access AccountPool only. Keep its exclusive persistent clients; consume
#7's proven cleanup guarantees without forcing temporary clients into the router
or changing the merged #7 helper's error policy. No new login flow, automatic joining,
account affinity, distributed ownership, scheduler, quota engine or progress format.
Local retirement refusal is not a Telegram health verdict or refundable read.

Original #17's two-account live qualification remains pending under the confirmed
offline-first choice. No real login/read/join or allowance reset is authorized by
this scoped repair. The current run ends at tested implementation and prescribed
commits/issue updates; formal merge check, PR critique and merge remain later gates.
Preserve the original checkout, its untracked files, duncan and unrelated worktrees.

## Priority Level

**High for this continuation:** the reproduced ownership violation blocks calling
the existing pool ready for review. Parent#17 retains its P2 feature priority.

## Known Blockers

No open planning or execution blocker for the offline rework. The real SDK's
shielded disconnect mechanism and current-dev compatibility issues are established
by source/probes, not assumptions. The parent's live E1 requires two approved
logged-in accounts, a shared readable group and bounded allowance; it gates the
later live test, not any step of this scoped offline repair.
