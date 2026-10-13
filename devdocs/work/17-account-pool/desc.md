---
model: gpt-6-astra
effort: max
revision: 5
status: MERGED_LIVE_E1_PENDING
---
# Account routing with explicit invocation and data ownership

> Session warm by other means at ancestor09e0277 (2026-10-13): complete foundation
> traverse and module reads carried forward; source, controller, store and progress
> paths refreshed. This revision additionally consumes the full failure history,
> current code, Python task behavior and real-component inquiry probes. No new
> architecture warming skill run claimed. GPT-6 Astra/max verified in turn metadata.

**Issue:** #17, feature-heavy; branch `feat/17-account-pool`, PR26 merged into dev
at c4e6eac after explicit user approval. Live E1 remains pending.
**Authority:** [public outcome ownership finding](../../inquiries/2026-10-13_11-46__17-public-outcome-ownership/finding.md).
This description replaces revision4, preserved in desc_r4.md. It does not replace
or rehabilitate the rejected revision5 implementation plan. The replacement is now
implemented in `007c2e4` under folded plan7; verification_outcomes.md records its
passing offline checks. Renewed merge check and round3 PR critique now PASS for the
offline scope (pr-critic.md); two-account live qualification remains pending.

## Problem Statement

Applications need bounded group reads without choosing and repairing an account for
every request. Existing pool routing covers much of that need, but its ownership
contract was incomplete. Earlier observer/provider cancellation could obscure a real
source result. The replacement then preserved messages on CancelledError, while an
internal close waiter or ordinary asyncio wrapper could consume/replace that signal
before the application received the messages.

There is a second independent mistake: the containing application Task can continue
after the tgdata call ends. Waiting for that whole Task makes pool shutdown wait for
unrelated application work even after owned source/provider work has stopped.

The missing contract distinguishes the owned invocation, the caller's stop signal,
the destination for completed data, and the durable facts permitting a retry or ack.
Changing one await or adding another exception handler does not establish that contract.

## User Value Proposition

Applications supply already-authorized accounts and groups and retain their existing
quota/progress stores. tgdata selects an eligible account and fails over only when
safe. Actual completed messages remain accessible to the caller through cancellation
and later local failure, without depending on exception-object identity.

The application owns scheduling, login/repair, receiver storage and health reactions.
It also owns the lifetime of a per-call result recipient: a local destination retained
before the call, independent of the Task used to await it. The pool closes its own work
and clients without acquiring ownership of arbitrary application continuation.

## Success Criteria

1. Preserve verified numeric account identity at admission/send, deterministic
   drain/spread, actual ReadBudget reservations, warm-up and saved restrictions.
   Fail over only on eligible, safe no-prefix outcomes. No duplicate credentials,
   login requests, hidden retry sleeps, quota refunds/resets or shortened known waits.
2. Distinguish actual source value/error, component-internal interruption, pool
   timeout, true caller cancellation and cleanup completion. True stop remains
   cancellation; a provider's cancelled I/O with no caller stop is a local failure.
   Completed source data cannot be replaced by later reporting or storage status.
3. Give every accepted source/control invocation an exact completion fact independent
   of its containing application Task. Publish completion only after its owned work
   actually ends and exclusive ownership is released. Close may stop that invocation
   and wait for this fact without consuming its public result or waiting for the
   application's post-call cleanup. A stale stop cannot affect a successor or later
   application work. Exact private representation is a later design choice.
4. The canonical data-producing pool calling form requires an explicit caller-retained,
   single-use result recipient before execution. Bind it to that invocation before
   I/O; invalid or already-bound reuse refuses before I/O. A coroutine cancelled before
   entry performs no I/O and leaves no started invocation/data. No hidden private
   holder, exception attribute or optional weaker form claims the same guarantee.
5. Record actual complete validated data in that recipient locally before later awaits
   can obscure it. Distinguish unbound/no data, running with available data, and ended
   success/failure/cancellation. Provisional or interrupted data never invents final
   success, end-of-history or a delivery receipt. Final content is stable, read-only
   and retrievable without re-awaiting the Task; later close/calls/drains cannot consume
   it. Normal return/error/cancellation remains observable through the awaited call.
6. Retain at most one current batch under existing batch limits per recipient, not an
   unbounded operation history. Store safe diagnostic facts rather than live Tasks,
   clients, credentials or exception traceback graphs. Keep the original read error
   distinguishable from a later local error. Caller-held snapshots/disposal are caller
   owned. No new universal byte-size or process-crash durability promise is implied.
7. Apply cancellation provenance/retained ownership to every configured async pool,
   sync and backfill store method. Invoke each provider once per engine call and retain
   the actual task until it ends. Providers settle their own I/O before returning;
   detached writes are outside their contract. Caller stop cannot release its owned
   write early, including when the actual commit completes during cancellation.
8. Only definite successful account admission authorizes source work. Failed/cancelled/
   malformed replies imply neither rollback nor permission. Preserve exact existing
   non-admission backfill reconciliation; no generic CAS retry or inferred receipt.
   Account permission, quota and group ack keep their distinct authority and schemas.
9. Completed error/cancellation data is available data, not proof of durable delivery.
   Reload/replay the authoritative progress store before using its existing ack contract.
   True caller stop begins no new persistence just to save a prefix. Source-internal
   interruption retains actual data but leaves admission unresolved, without automatic
   failover or normal settlement. A completed success is not downgraded by later close.
10. Retain native SDK cleanup through repeated cancellation. Disconnect must finish
    before reuse. Failed cleanup quarantines the client until explicit successful
    retry; secondary cleanup must not replace the primary body result/error.
11. Keep bounded passive health observations, synchronously drainable in every state.
    No pool observer callback/task; loss is visible and cannot alter permission or
    erase recipient data. Existing ordinary TgData/#7/#10 behavior remains as merged.
12. Refuse detectable same-pool operation/provider lifecycle reentry before mutation.
    Scope expires and is pool-specific. Providers perform I/O only, without depending
    on control of their own pool through any task. No arbitrary wait-graph guarantee.
13. Preserve the distinction between the pool source/control span and public progress
    calls. Daily/backfill publication may continue under its caller after source work
    and pool closure; its recipient finalizes when that public call ends. State-only
    replay/ack/status remains usable after close without credentials, pool state or
    quota reads. Close does not become a global manager of progress-store calls.
14. Qualify the complete proposed contract in a fresh combined real-component prebuild
    before production edits, then run complete relevant offline/current-dev checks
    with Telethon1.45.0. Cover raw/daily/backfill, actual store commit phases, native
    cleanup, recipient lifecycle, early data retention, wrapper/observer order,
    post-call application work and existing worker compatibility. Small concept
    experiments do not replace that gate or the later fresh PR critique.

Key observable acceptance cases:

| History | Required observation |
|---|---|
| One or100 complete records, then true cancellation; close receives stop first | Caller-retained records remain accessible; Task remains cancelled; actual charge persists |
| shield/gather replaces the cancellation exception | Recipient still carries actual data independently of the signal |
| tgdata returns/raises, application continues unrelated cleanup | Pool close finishes its clients without waiting for that continuation |
| Provider cancellation before/after actual CAS | Local failure versus caller stop is accurate; durable uncertainty and completed data stay separate |
| Daily/backfill publication held after source completion | Close may finish; recipient remains unfinished until its public call ends; no invented receipt |
| Recipient reused, cancelled before entry, or read after finalization | No overwrite or unintended I/O; unstarted and finalized states are distinguishable |

## Scope Boundaries

Existing-access first delivery, one owning process/event loop, exclusive sessions,
trustworthy UTC, one source reader per group across progress stores [ASSUMPTION:
unchanged deployment contract]. Retain tested routing, quota, restrictions, recovery,
progress and retirement mechanisms where they satisfy this contract.

No automatic joining, scheduler, background-job supervisor, global result registry,
new durable raw-result store, distributed leases, login flow, affinity or union-history
guarantee. Do not impose pool lifetime policy on temporary #7 operations or #10 workers.
Shared progress changes must preserve existing cursor/receipt semantics.

**Current authorized endpoint (implementation follow-up):** implementation under
folded revision7 after the passed prebuild, with permanent tests, public docs and full
offline verification. This is complete at007c2e4. The later authorized review completed renewed merge/PR
gates; the subsequent explicit merge approval landed c4e6eac. Two-account live
qualification remains separate and pending; see merge-result.md.

## Priority Level

**High correctness priority within P2 feature #17.** An application can otherwise lose
already-observed data or have shutdown depend on work the library does not own.

## Known Blockers and Evidence Limits

**Upstream ownership question — answered at description level.** The completed traverse
reproduced public wrapper loss without close and application lifetime extending beyond
the owned call. Its concept experiments support separate completion and data ownership.
The finding records the limits, including one full traverse iteration and no claim of
repeated-cycle architectural convergence. No further factual/vendor question blocks
writing a new plan from this description.

**Production implementation — OFFLINE PASS; renewed PR review PASS.** Product007c2e4
implements folded plan7. All750 executed offline groups and3 demos pass on the actual
branch, with3 live skips excluded. Its runtime matches the passing prebuild's executable
code; new public method docstrings and permanent test organization are recorded in
verification_outcomes.md. The subsequent round3 PR critique passes with0 High/Medium/Low
and26 fresh histories; see pr-critic.md. The two previous rejected reviews remain
historical. User subsequently authorized the merge: c4e6eac, with750 merged-code
checks+3 demos passing. E1 remains pending.

**Earlier storage-cancellation false premise — preserved history.** prebuild_r3.md
records the failed provider-boundary experiment; the later implementation fixed that
measured path but did not establish public outcome delivery. Keep both lessons.

**E1 — two-account live qualification — OPEN, execution only.** User chose one account
and offline-first. Requires two approved logged-in accounts, a shared readable group
and their existing bounded allowance. No live calls, joining, login or budget reset.
Only Python3.11.10/Telethon1.45.0 ran in this inquiry; native3.7 is not newly qualified.
