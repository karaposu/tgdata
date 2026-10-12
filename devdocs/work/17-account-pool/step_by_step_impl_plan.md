---
model: gpt-6-astra
effort: max
revision: 5
---
# #17 — explicit ownership across source and storage

**Critic folded:** 2026-10-13 — 1 mitigation (1 step changed, 0 added).
P0 completed before step1; prebuild.md records48/48 plus both worker suites.
**Implementation:** steps1–7 complete at producta63099e; verification_restart.md.
Step8 remains gated by E1; renewed PR gates are separate.

### What is the task

Complete existing-access account routing from the new desc.md requirements, using
all rejected/failed history as evidence. Rebuild completion ownership across source
and async storage, retain actual messages through local failure, and remove arbitrary
health observers from the pool's source lifetime. Keep proven routing/quota/progress
rules and persistent clients. This is a fresh plan, not amendments to deprecated r3.

### Huge Hard Blockers

#### Planning Blockers

None identified. The inherited storage premise is CLOSED: it was false, measured
in prebuild_r3.md. Full source/store/progress implementations show where both outcomes
and data must be retained; no human product decision is missing. Behavioral confidence
in the proposed replacement is not inferred from those reads: P0 below must run
before step1, and a disqualifying result kills this plan.

#### Execution Blockers

**E1 — OPEN.** Two approved logged-in accounts that can already read the same group,
plus their existing bounded ledger allowance. **Who:** user supplies access/approval.
**Blocks:** step8 only. User selected one-account/offline-first; steps1–7 are authorized.
No reset, new joins or login codes in chat. PR review and merge remain separate gates.

### How this implementation moves toward desired state

Use one private ownership primitive for interruptible async source/provider work:
the child's value/error is data returned to its waiter, while cancellation delivered
to the waiter is a stop request. Stop the child once, retain its actual completion,
then propagate caller cancellation. Cleanup retains its different policy: do not
cancel native disconnect. Both use the existing retained-join technique; neither
uses Task.cancelling/uncancel or a global supervisor.

Source body outcome remains separate from the health context's finalization.
Synchronous passive capture replaces pool callbacks. Scoped provider calls extend
ownership through every async store; local internal cancellation takes existing
storage-error paths, leaving authoritative write/recovery rules intact. Shared
progress publication errors carry known data without claiming durable publication.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Integrate current dev | Worker/source union identical to P0 baseline |
| 2 | Own interruptible work and provider scopes | Private lifecycle primitives |
| 3 | Separate source outcome and passive observations | Source result survives secondary failure |
| 4 | Apply ownership to pool and progress stores | Provider cancellation has local meaning |
| 5 | Retain completed data through persistence failure | Error prefix without invented receipt |
| 6 | Add regression cases and public contract | Tests/docs/examples match behavior |
| 7 | Full offline verification and scoped commits | Reproducible evidence and pushed branch |
| 8 | Two-account live qualification | E1 report; blocked pending access |

## Required prebuild P0 — before step1

Create a fresh isolated export of product71502e5 + dev2ddb852 (one batch_engine
conflict, explicit union). Prototype steps2–5 only in that export/private probe
material. Use real Telethon1.45 methods, native disconnect, ReadBudget, SQLite pool/
sync/backfill state, actual progress engines and event-loop task scheduling. Synthetic
wire may supply replies; fault adapters must execute actual SQLite CAS when a commit
is claimed. Never manufacture batches, charges, tokens, waits or receipts as outcomes.
Block socket connect; parent subprocess watchdog prevents an actual deadlock hanging
the agent. Watchdog termination is failure, not cleanup success.

Retain all37 r3 groups and their exact semantic expectations (including the failed
storage group), current-dev worker37/38, then add the following complete matrix:

- Pool state load and admission: provider-owned cancellation, before/after actual
  commit; no caller stop, no source request/charge, unresolved token only if stored.
- Pool settlement: raw/daily/backfill × successful batch / prefix+FloodWait ×
  before/after commit; local storage error, available data retained, wait/token agree
  with actual state, no failover. Daily/backfill retain pending if their store works.
- Daily/backfill stores: load, admission where applicable, publication/settlement,
  ack and local controls; provider-owned cancellation before/after commit. Admission
  never reconciles into source permission; non-admission backfill exact-state
  reconciliation remains allowed. Errors retain data; replay/ack reload actual state.
- True caller stop during source or provider work, including repeated cancellation
  while the provider's finalizer performs a held actual SQLite CAS. Caller/busy owner
  remains until I/O finishes, no new source admission, no false rollback assumption.
  Pre-start cancellation starts no provider or source. Cancellation after a known
  batch retains that prefix but starts no new saving just for cancellation.
- Provider reentry through direct call, child task and wait_for after the new task
  boundary; pool/sync/backfill scopes, external/foreign/expired positive controls.
- Source-internal cancellation stays local/unresolved, native failed cleanup stays
  quarantined, source-free progress after close, bounded detached observation/drain,
  no application callback or observer task, ordinary health callbacks unchanged.
- Synchronous session load cancellation is a local configuration failure, not caller
  stop (no await point there); session save/disconnect interruption remains inside
  the owned source/retirement boundary. Secrets stay out of public errors/events.

PASS requires every matrix assertion, all37 retained groups and both worker suites
in one combined run. A wrong ownership/data/permission result or watchdog is FAIL;
record/deprecate/stop under task-impl. Minor fixture/name/import errors may be corrected
and recorded; semantic expectations cannot be weakened. Passing targeted probes alone
is not P0. Record exact candidate/source hashes and commands. Prototype is evidence,
not product completion; runtime remains unchanged until P0 passes.

## Step 1 — integrate current dev

### Proposed changes

Merge current dev2ddb852 into this issue branch after P0. Preserve all worker cleanup
receipts and merged #7 behavior. Resolve only the known batch_engine constructor seam:
keep `_resolve_entity` and `_retain_cancelled_prefix=False`; pool opts in. Use the
P0 tree as the comparison, not guessed resolution. If dev moved, inspect and repeat
combined P0 for its changed composition before implementation. Keep work docs on the
feature branch and unrelated main-checkout changes untouched.
### Output

Feature branch contains current dev with the same runtime union used in P0.
### Safe in nature

False — shared source seam.
### Peripheral concepts

BatchEngine, temporary owner, worker receipts, historical work docs.
### Hardness Lvl

2

## Step 2 — explicit interruptible ownership and scoped providers

### Proposed changes

New private `tgdata/pool_lifecycle.py` holds: (a) retained cleanup join moved unchanged
from pool_source (re-export privately there for current users); (b) child capture and
wait primitives; (c) expiring per-pool ContextVar scope; (d) pool-only async store
adapter. No public supervisor/task registry.

For each interruptible call, checkpoint caller cancellation before creating the child.
Invoke the component inside that child, capture Exception/CancelledError as value/error,
observe child completion via asyncio.wait, catch caller cancellation only around the
wait/retained stop, cancel child once and retain completion through further stop
requests. Child.cancelled before capture starts is internal terminal data, not an
uncaught caller exception. Return completion plus timeout indication; consumers
interpret it. Process-control BaseExceptions are not normalized into ordinary errors.

No storage timeout is invented. Providers own their timeout and must finish subordinate
I/O before returning. Python3.7-compatible syntax/APIs; no cancellation-count heuristic.
Scope direct and descendant same-pool close before mutation, expire it in finally and
remove pool references so inherited stale context is harmless. Guards supplement the
I/O-only provider role; they do not detect arbitrary outside-task dependencies.

The store adapter invokes exactly once, awaits the real provider through the same
primitive and maps only provider-internal CancelledError to the supplied local error
class with type-only text and suppressed context. Actual caller cancellation passes
through after joining. Ordinary engine/provider error translation remains in its
existing engine. Optional stores retain None semantics; reject malformed configured
pool progress adapters locally. Do not mutate adapters used by other consumers.
### Output

One small private outcome mechanism shared by source and three storage paths;
cleanup remains a separate retained policy.
### Safe in nature

False — lifetime semantics.
### Peripheral concepts

asyncio cancellation, contextvars, async store protocols, Python3.7.
### Hardness Lvl

5

## Step 3 — source outcome and passive observations

### Proposed changes

New `pool_observation.py`: private bounded buffer and HealthMonitor subclass. Capture
only the existing eleven event keys/three account keys, exact plain dict/scalar types,
signed64 ints/None/strings with pre-encoding length bound; detached values. Limits:
128 events,4096 encoded bytes/event,65536 total bytes, drop incoming on overflow and
saturate dropped at2**63-1. Catch capture Exception/CancelledError locally as one loss.
No health log mirror, user callback, consumer await, background task or dependence
on the legacy callback-delivery ContextVar. Ordinary HealthMonitor unchanged.

Pool rejects non-None health_callback with migration guidance. `drain_health_events()`
synchronously returns `{events: [...], dropped: N}`, resets capture, works in every
pool state and performs no source/state/quota I/O. It is best-effort diagnostics.

Source.run uses step2 owned child while retaining a separate source body holder.
Always prefer a completed body result/error over secondary monitor failure, internal
cancellation or timeout. Genuine caller stop takes precedence after joining and carries
any already-known complete prefix. Source-internal cancellation without completed body
becomes private `_SourceInterrupted(PoolStateError)` with prefix and no normal account
settlement/failover. Owned timeout uses existing PoolTimeoutError rules after quiescence.
Keep self.task accurate until child finishes. Preflight sync session/config CancelledError
is local configuration failure; native retirement/quarantine/retry stays unchanged.
### Output

Source outcome survives secondary termination; passive bounded health API.
### Safe in nature

False — unmerged pool callback API changes.
### Peripheral concepts

HealthMonitor attribution/recovery, credential loading, native SDK disconnect.
### Hardness Lvl

4

## Step 4 — controller and every configured async store [folded: Risk1, robust]

### Proposed changes

AccountPool._operation first refuses a live same-pool scope before changing ownership,
then enters the expiring scope while retaining its existing exclusive caller task.
This covers initialize/read/recheck/recover invoked from state-only providers, even
when no source is active. P0 covers all five exclusive controls (including close)
from pool/daily/backfill providers through direct/task/wait_for paths; state, clients
and quota stay unchanged. Foreign/expired scopes and local progress remain usable. _backend uses owned provider invocation for load/CAS and preserves existing
PoolError translation. SyncEngine receives an owned wrapper of sync_store; backfill_store
uses its own wrapper/namespace. State-only methods are scoped during provider work but
do not acquire exclusive source ownership; they remain usable after close.

close refuses a live same-pool scope before changing flags. Ordinary external close
keeps existing cancel/await-active/retire-all behavior; it does not track independent
state-only progress calls. Those calls' own waiters retain their I/O. Keep pool admission
strictly definite True, recovery exact-token and conservative waits. No CAS retries or
schema changes. SourceInterrupted skips settlement and retains actual durable token.
Normal local settlement failure and true cancellation attach already-known interrupted
prefix; read_error retains original source failure where one exists. No failover on
local storage failure; no persistence started merely to service a cancelled caller.
### Output

Independent provider interruption cannot look like caller stop, at any store seam.
### Safe in nature

False — async provider execution changes task, documented as an extension contract.
### Peripheral concepts

Admission, CAS, status, recovery, progress lifetime, observer reentry.
### Hardness Lvl

5

## Step 5 — retain available data when progress publication fails

### Proposed changes

Extract the existing AccountPool._prefix logic as private `_interrupted_prefix` in
message_batch.py and reuse it without changing serialization/hashes. None/empty stays
None; known nonempty records become interrupted (never history-end proof).

SyncEngine._publish validates first, then on SyncError/CancelledError from persistence
attaches that batch as interrupted partial_result before rethrowing. Existing read_error
assignment stays. BackfillEngine settlement similarly retains its already validated
batch on BackfillError/CancelledError; no reader fabrication, new write/retry or receipt.
A successful backfill exact-state reconciliation still returns confirmed original data.
Neither shared engine converts its direct caller's cancellation; only the pool adapter
classifies provider-owned cancellation. Failed validation must not advertise untrusted
data. Ordinary direct TgData gains only error data retention, not new lifetime policy.
### Output

Known records remain inspectable across publication failure, without implying durability.
### Safe in nature

False — shared progress error payload adds information.
### Peripheral concepts

MessageBatch hashes, interrupted semantics, SyncError.read_error, backfill reconcile.
### Hardness Lvl

3

## Step 6 — regression coverage and public contract

### Proposed changes

Promote P0 assertions to a standalone pool lifecycle smoke suite reusing actual test31
SDK/SQLite fixtures. Update test31 callback-specific expectations only for the planned
passive API, keeping all existing source/permission/retirement expectations. Avoid
using tests that simply mirror the helper; assert observable source traffic, SQLite
snapshots, charges, data/receipts and task termination. Cover full P0 matrix and ordinary
source success/SDK errors/current worker composition. Network blocked.

Update docs/account_pool.md, examples/account_pool.py, README and smoke README:
passive drain in app-owned finally, no background consumer promise; provider task/lifetime
contract; source/caller/provider cancellation distinctions; prefix is data not receipt;
ambiguous writes require inspection/existing exact retries; state-only use after close;
limits and dropped counts; offline qualification versus pending E1. Preserve scope.
### Output

Permanent regression runner and accurate app-facing docs/example.
### Safe in nature

True — tests/docs; intentional old expectations change only where plan changes API.
### Peripheral concepts

Examples, offline suite inventory, user-facing recovery workflow.
### Hardness Lvl

3

## Step 7 — verify, record and commit

### Proposed changes

Compile all runtime/examples, check Python3.7 grammar, run new suite and full supported
offline suites12–19 and22–38, plus offline examples and package exports using existing
Telethon1.45 environment. Tests20/21 and E1 live cases stay gated; record any actual
skip. Use the real runners; PROJECT_SPECIFICS absent is not a reason to invent commands.
Compare final runtime with P0 candidate and explain deliberate test/docs deltas.

Small local slips may be fixed with recorded reason/retest; architecture failures stop
under task-impl. Run diff whitespace/status checks. Commit product/tests/docs separately
from work notes; push the existing feature branch and update #17 pipeline with exact
committed evidence. Keep PR26 draft: renewed merge check/fresh PR critique remain next.
Preserve unrelated files/history; never stage duncan or user main-checkout changes.
### Output

Full offline verification record, scoped commits and accurate issue/handoff.
### Safe in nature

True — verification and feature-branch records.
### Peripheral concepts

CONTRIBUTING gates, model stamp, issue status, E1 qualification.
### Hardness Lvl

2

## Step 8 — live qualification [execution gate E1 OPEN]

### Proposed changes

Only after the user supplies the two-account/shared-group/allowance preconditions,
run bounded read-only live routing/failover as originally scoped, record real identity,
visibility, proxy and quota observations. No joining/reset or invented equivalence
between offline synthetic wire and live Telegram. Renewed merge/PR review gates remain
necessary regardless of this result; merge requires user go-ahead.
### Output

Live evidence or explicit pending status. This run stops here if E1 remains open.
### Safe in nature

False — actual Telegram reads spend allowance.
### Peripheral concepts

Real accounts, network/proxy, visibility, read quota.
### Hardness Lvl

3
