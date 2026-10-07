---
status: active
model: gpt-6-astra
effort: max
---
# Finding: routing group reads across owned accounts

## Question

How should tgdata implement #17 so an application can request a group read and
let the library choose another account when one becomes unavailable? The user
selected a first delivery covering groups accounts can already read. Automatic
joining is excluded and #7 remains paused.

The design must work with the existing read budgets, raw message batches and
daily/backfill acknowledgment APIs. It must not move permanent message storage or
application scheduling into tgdata.

## Finding Summary

- Add a separate AccountPool that owns its account clients. Existing connection
  pool settings continue to mean multiple sessions of one account.
- Verify the authenticated numeric account ID before history reads and again at
  budget admission. Cached identity and legacy health summaries cannot authorize reads.
- Save an account attempt before starting source work. An unresolved attempt
  remains blocked across restart until explicitly recovered.
- Fail over only after the previous attempt ends and has no completed messages
  to deliver. Preserve completed prefixes on errors and pool-owned timeouts.
- Keep quotas and acknowledged group progress in their existing components.
- Results describe history visible to the selected account. They do not prove
  that different accounts see identical history.

## Finding

### 1. Own each account at the source boundary

The new pool accepts account configurations with expected numeric Telegram IDs,
their config files and optional existing session stores. It owns the resulting
clients exclusively. Duplicate expected identities and known duplicate session
credentials are refused. A fresh identity answer must match the configured ID
before a history request is admitted.

This is necessary even with one account. An offline probe of the current real
Telethon path returned account222 while restored cache, health event and health
summary still named111. The existing budget correctly charged222. Copying those
health summaries into a pool would make routing decisions about the wrong owner.

Pool-owned reporting uses the source operation's verified identity. Before that
verification, user_id is unknown; a configured label is not proof of authentication.
Wrong identity is a repair/configuration failure, not a claim that Telegram banned
the account. The paused global health redesign from #7 is not adopted.

### 2. Make every account attempt explicit

Use a persistent opaque pool-state document with account rows. Before source work,
write a unique attempt ID, account, group or diagnostic kind, and admission time
through compare-and-swap: the write succeeds only if the stored document is still
the version that was read. A definite successful response permits the source call.
An uncertain response never does.

After the source task ends, settle only that exact attempt. Clear the active token
and record any resulting restriction in one state transition. A stale response
cannot clear a newer attempt. An unconfirmed transition remains visible as a local
state error; it is never treated as proof of rollback.

The first design stored only failures. Critique rejected that gap: a process could
receive a two-hour wait and die before saving it, leaving an apparently clear
account on restart. Recording permission beforehand makes that account unresolved
even when the later failure fact is lost.

Explicit recovery names the attempt, asserts that its previous reader is stopped,
and provides an explicit retry-not-before time for the unknown outcome. Recovery
cannot shorten a saved wait, erase a repair flag or grant budget. The operator's
chosen time is policy under uncertainty, not evidence that Telegram is ready.

Initialization is explicit. Ordinary reads refuse missing or corrupt state; they
cannot silently provision a replacement. Adding an account preserves all previously
stored restrictions, including records for accounts temporarily removed from inventory.

### 3. Bound attempts and preserve completed data

Use a private connection policy through the existing client factory, retaining
proxy, device identity and session storage. Pool clients do not prompt for login.
They expose flood waits and exhausted SDK errors, use finite retry settings and
a cooperative attempt timeout. The ordinary TgData connection policy stays unchanged.

A probe showed that setting only a zero flood threshold is insufficient: the
current authentication method still requested a7200-second sleep. Another probe
showed default SDK exhaustion replacing ServerError with ValueError. The pool's
policy must cover both authentication and SDK request behavior.

An ordinary failure can advance to another candidate only after its task has
ended and it has no complete records. A completed prefix ends the routing call;
the caller or existing progress engine must handle that observation first.

For an internal timeout, the pool awaits cancellation and preserves any complete
records through an opt-in BatchEngine exception seam. The real-component prototype
retained100 messages after the next page stalled. The actual daily engine saved
and replayed them without another read. The ledger retained200 units:100 returned
and100 reserved for the unanswered request. External caller cancellation still
propagates and leaves the account attempt unresolved.

A pool-store failure after data arrives raises a local exception carrying those
records as an interrupted prefix. The original source error is retained separately,
not as a health-classified exception cause. This preserves useful data while exposing
the unsettled account state. No new account is tried inside that failed call.

### 4. Keep eligibility separate from quota and delivery

The pool records account-wide repair conditions, account cooldowns and per-group
denials with explicit retry deadlines. Known waits survive restart. Ordinary
transport/group failures become eligible for a later bounded probe; ban/logout or
identity repair requires deliberate rechecking after repair. Unrelated success
does not clear a group's denial.

ReadBudget remains the only allowance authority. Failed or cancelled sends retain
their charges. Its warm-up caps remain active; an optional minimum age is an
additional eligibility rule, not an inferred completion date for the warm-up curve.

Initial selection policies are deterministic inventory-order drain and
remaining-allowance spread with inventory-order ties. Each candidate is attempted
at most once in a call. One active pool operation makes ownership explicit; overlap
returns a busy outcome. When no candidate can proceed, return structured reasons
and conditional retry information rather than an empty batch.

Groups are registered by canonical numeric ID with optional bounded resolution
hints. Every resolved hint must match that ID before history is read. Existing
private groups need account-specific cached resolution; no unbounded dialog scan
or joining is hidden in the pool.

Daily/backfill methods share the existing progress facade and inject the pool's
batch reader. Pending replay and acknowledgment bypass account selection, account
state and budget access. Account-attempt recovery and group-delivery recovery remain
separate because they protect different obligations.

## Inherited Commitments Re-test

| Commitment and source | Re-test status | Evidence |
|---|---|---|
| #7 HANDOFF: cached identity can disagree with actual operation owner | RE-TESTED — confirmed | Current dev probe fresh222/cache111/health111; recorded in docarchive/sensemaking_iter1.md. |
| #7 HANDOFF: SDK exhaustion can hide real errors | RE-TESTED — confirmed | Real SDK default ValueError versus preserved ServerError; same artifact. |
| docs/daily_continuation.md and docs/backfill_runs.md: pending observation belongs to progress, not account | RE-TESTED — confirmed | Actual SQLite/SDK replay after source identity changed made0 additional reads. |
| Existing backfill source admission pattern protects uncertainty | RE-TESTED — confirmed but frame revised | Actual CAS reconstruction/stale-settlement probe; now applied to account-wide source permission, not copied group receipts. |
| Account-visible history does not prove equal coverage | INHERITED-WITHOUT-RE-TEST | No live two-account visibility comparison performed; the design promises no equality and does not depend on it. |

## Next Actions

### MUST

- **What:** describe, plan, critique, implement and verify the owned pool and exact
  failure contracts. **Who:** this task-impl run. **Gate:** traverse conclusion
  committed; then the normal plan/critic gates. **Why:** deliver the selected capability.
- **What:** test actual source/store/timeout and existing progress composition,
  including concurrent calls and uncertain writes. **Who:** implementation tests.
  **Gate:** before marking implementation verified. **Why:** primitives alone do
  not prove the assembled pool.
- **What:** qualify real failover on two named existing accounts and an approved
  shared group, with a bounded shared budget. **Who:** maintainer supplies resources;
  agent prepares/runs the gate when authorized. **Gate:** offline verification passes
  and resources are confirmed. **Why:** distinguish implementation proof from live qualification.

### COULD

- **What:** extend ranking beyond drain/spread. **Who:** later pool work.
  **Gate:** real workload evidence shows unfairness. **Why:** improve utilization.
  **Depends-on:** MUST implementation/verification; GATED until that passes.

### DEFERRED

- **What:** automatic joining. **Gate:** #7 accepted and explicitly resumed for
  this purpose. **Why if revived:** expand accessible group inventory.
- **What:** distributed ownership and union-history coverage. **Gate:** user requests
  competing readers or a stronger coverage guarantee. **Why if revived:** different
  requirements need their own ownership and visibility design.

## Reasoning

The retained approach combines owned clients, durable attempt permissions and the
existing progress engines. Alternatives using separate account documents also
survived, but add coordination work to an intentionally serial pool. Treating every
timeout as caller cancellation survived as a conservative option but gives up useful
failover when no prefix exists. Both are less suitable for this first delivery.

Rejected alternatives and their useful lessons:

| Alternative | Why rejected |
|---|---|
| Arbitrary shared TgData objects and health snapshots | Real identity mismatch makes their ownership unsafe. |
| Global health repair first | Expands into paused #7 and does not itself bound source waits. |
| Process-local breakers or asking Telegram on every call | Restart/next call forgets known prohibitions. |
| Expiring source leases | Time passing does not prove an old task stopped. |
| Parallel hedged reads | Multiple paid observations and loser cleanup need an additional delivery contract. |
| Selector-only API | Leaves the requested automatic failover in application code. |
| Duplicate pool cursor and acknowledgment state | Creates competing authorities after uncertain writes. |
| Raw-only integration fallback | Useful smaller option, but silently choosing it would leave daily users needing private-engine wrappers. |
| Fake-only or live-only qualification | Neither establishes both actual SDK behavior and deterministic failure histories. |
| Account identity in MessageBatch v2 | Changes hashes/receipts to solve separate routing provenance. |
| Discarding timeout prefixes | Another account may not reproduce those visible records. |
| Returning success after pool settlement fails | Conceals unresolved source permission. |
| Distributed scheduler in this delivery | Solves an excluded ownership problem and expands the state model. |

## Open Questions

### Blocked

Two-account live resources are not confirmed. An optional question is pending;
offline implementation proceeds independently. No login, join or Telegram request
has been made for #17, and no existing live budget has been reset.

### Refinement Triggers

Revisit serialization only when measured pool contention prevents the intended
workload. Revisit the private SDK policy when Telethon changes from the verified
1.45.0 behavior. Revisit restart assumptions if multiple processes must own one pool
or the deployment cannot provide trustworthy UTC and source quiescence.

## Source Input

The user selected “#17—the account pool that handles routing and failures
automatically” with task-impl, then chose “Routing and failover for groups accounts
can already read; keep #7 paused (recommended).” Full transcription: `_branch.md`.
