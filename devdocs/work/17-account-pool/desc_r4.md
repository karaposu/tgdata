---
model: gpt-6-astra
effort: max
revision: 4
---
# Account routing with explicit operation outcomes

> Session warm by other means at ancestor09e0277 (2026-10-13): complete foundation
> traverse and module reads carried forward, with full source/controller/store/
> daily/backfill implementations refreshed. See triage.md. No new architecture
> skill run claimed. Model/effort verified from current turn metadata.

**Issue:** #17, feature-heavy; same draft PR26 and feature branch.
**Restart:** this description replaces the prior design. It is derived from the
original routing goal, the rejected PR, completed traverse and failed real-component
prebuild. Earlier descriptions/plans/critics and exact probes remain preserved.

## Problem Statement

A caller needs bounded group reads without selecting and repairing the account for
every request. Existing routing can do that, but its completion boundary is wrong:
an exception named CancelledError is treated as a caller stop even when it came
from a health observer or storage provider. A completed Telegram batch can therefore
vanish from the public error and durable pending delivery. Callback-driven shutdown
can also make the reader wait for shutdown while shutdown waits for that reader.

The last prebuild removed callbacks from source execution but missed storage. It
observed a real 100-message prefix and FloodWait7200, followed by provider-owned
cancellation before/after an actual SQLite commit. The caller had no cancellation
requests; both cases returned cancellation with no data. The right boundary covers
all awaited work, including pool state and daily/backfill state, while preserving
uncertain-write refusal and actual caller cancellation.

## User Value Proposition

Applications register already-authorized accounts/groups, keep their existing
account quota and progress stores, and request a bounded read. The pool selects an
eligible account and fails over only when safe. Completed messages remain available
when later local persistence fails. A stopped request finishes its owned work before
returning, so another read cannot reuse something still being retired or written.

Applications own scheduling, login/repair, receiver storage and health reactions.
The pool provides bounded passive health observations, explicit uncertain-attempt
recovery and existing daily/backfill acknowledgment contracts.

## Success Criteria

1. Preserve numeric expected-account verification, deterministic drain/spread,
   actual ledger reservations, warm-up, stored restrictions and safe no-prefix
   failover. No duplicate credentials, login requests, hidden retry sleeps or quota
   reset. Known waits are never cleared by local failure or diagnostic data.
2. Distinguish completed source value/error, component-internal interruption,
   pool timeout, caller cancellation and cleanup completion. Component cancellation
   is a local error; actual caller cancellation remains cancellation, including
   repeated stop requests and cancellation concurrent with component completion.
3. Apply that distinction to source work and every configured async pool/sync/
   backfill store method. A provider is invoked/awaited once per engine call, and
   its actual task is retained until it ends. Caller stop cannot leave a write
   running after that caller's ownership is released. Providers must settle their
   own I/O before returning; detaching subordinate I/O is outside their contract.
4. Only a definite successful admission reply authorizes a source call. Failed,
   cancelled or malformed replies never imply rollback or permission. Preserve
   existing exact-state backfill reconciliation for non-admission writes; no new
   generic CAS retries or inferred receipts. Pool permission, quota and group ack
   remain distinct authorities and retain their schemas.
5. Once complete messages exist, preserve them as an interrupted MessageBatch on
   later local persistence failure (and cancellation after that known result).
   Retain an original read error separately. This is available data, not a promise
   of durable pending delivery or a receipt. Reload/replay the authoritative store
   before acknowledgment. Never invent history-end evidence from an error prefix.
6. Preserve source body outcome on every secondary reporting termination path.
   Unexpected source-internal cancellation retains complete prefix but leaves
   account admission unresolved; no automatic failover or normal settlement.
   True caller stop starts no new persistence just to save an error prefix.
7. Cleanup is retained through repeated cancellation; actual SDK disconnect must
   finish before client reuse. Failed cleanup quarantines the client until explicit
   successful retry and does not replace the primary body result/error.
8. Pool health reporting runs no application callback and creates no observer task.
   Bounded, detached plain data is drained synchronously in all states, including
   during reads/close and after close. Overflow/loss is visible and never changes
   account permission. Ordinary TgData/#7/#10 health behavior stays as merged.
9. Detectable lifecycle reentry from live same-pool operations/providers refuses
   before close mutation. Scope ownership expires and is pool-specific. Providers
   do I/O only: no dependency on controlling their own pool, including via existing
   outside tasks. No claim of complete arbitrary wait-graph detection.
10. Daily/backfill state-only operations and replay/ack remain independent of pool
    source lifetime. They work after close without credentials, pool state or quota
    reads. Their caller owns their I/O; close does not become a global task manager.
11. Pass a fresh combined real-component prebuild before runtime edits, then the
    applicable complete offline suite on Telethon1.45.0/current dev. Exercise raw,
    daily and backfill results, actual SQLite commits, native SDK cleanup, retained
    caller/provider cancellation and current worker compatibility.

## Scope Boundaries

Existing-access first delivery, one owning process/event loop, exclusive sessions,
trustworthy UTC, one source reader per group across progress stores [ASSUMPTION:
unchanged deployment contract]. No automatic joining, scheduler, distributed leases,
new login flow, affinity, union-history guarantee or general health-system redesign.

Restart the design around these requirements; retain proven router, quota, state
and progress mechanisms where they satisfy them. A new private cancellation owner
may serve the actual repeated source/provider instances; do not impose pool lifetime
policy on temporary #7 operations or the worker. Shared progress changes are limited
to retaining already-validated data on errors, not new cursor/receipt semantics.

**Authorized endpoint:** fresh plan/critic/prebuild/fold, implementation and complete
offline verification. Two-account live E1 remains a later execution gate. Renewed
merge check/PR critique and merge remain subsequent work; no automatic merge.

## Priority Level

**High correctness priority within P2 feature #17.** Misclassified cancellation can
lose an already-observed batch from delivery even while account safety checks hold.

## Known Blockers

### PR round2 — public outcome consumption — OPEN for description requalification

The fresh PR review reproduced a new boundary omitted from the ownership contract:
close needs to observe task termination, but directly awaiting the cancelled public
reader can consume its saved CancelledError. A later application waiter receives a
fresh exception without the completed-message payload. This holds for raw, daily and
backfill: six cases lose the payload; six caller-first controls retain it. Actual
storage settlement, charges and client retirement still hold. This behavior is measured,
not an unanswered vendor question; see pr-critic.md and evidence/review2/cancel-payload.txt.

The description/foundation inquiry must establish who owns consuming the public result,
separately from who may stop or await quiescence, and which caller-delivery guarantee is
required. The current requirement to preserve known data stands; do not weaken it to
make the review pass. The selected review guidance is to make internal shutdown observe
completion without taking the application's cancellation payload. No extra public
result store or global supervisor is established as a prerequisite by this evidence.

CONTRIBUTING §7.4 requires this upstream return after the second rejected PR round.
Do not resume the folded revision5 implementation or immediately write another plan.
Qualification must include late application waiters and external close, before any
replacement implementation. No human access is needed for this offline design work;
E1 remains a separate later live gate. Production is unchanged at a63099e.


### Prior storage-cancellation premise — CLOSED, measured false

Revision3 P0 failed36/37 pool groups; worker33/33+25/25 held. Before/after settlement
commit, independently cancelled provider I/O yielded caller requests0, prefix0 and
no daily pending despite actual prefix100/charge200. See prebuild_r3.md and exact
replan-r3 evidence. DEPRECATED_step_by_step_impl_plan.md must not be resumed.
The missing requirement is now explicit across source and all state-provider work.
The replacement passed its mandatory fresh experiment at3f535d1 and was implemented
in a63099e with full offline verification (verification_restart.md). This preserves
the historical false premise without marking the replacement live-qualified.

### E1 — two-account live qualification — OPEN, execution only

User has one account and selected offline-first. Requires two approved logged-in
accounts, a shared readable group and their existing bounded allowance. Gates only
the later live step. No live traffic, budget reset or joining is authorized here.

## Inherited lessons

Task termination is not source outcome. Cancellation is not rollback. Completed data
is not durable acknowledgment. Retained cleanup needs acyclic ownership. Context
ancestry is a guard, not a global dependency graph. Passing isolated cases does not
qualify their composition. Use the whole prebuild before the first production step.
