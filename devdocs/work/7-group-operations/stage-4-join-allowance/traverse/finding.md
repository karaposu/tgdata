---
status: active
model: gpt-6-astra
effort: max
---
# Finding: A small durable join allowance

## Question

What should #7 Stage4's join allowance promise, so the later joining operation can use
it without another redesign? The user explicitly chose Stage4 only, with review and
merge before Stage5. The goal is a reusable library primitive with clear counting,
persistence and failure rules—not a new account-health or routing system.

## Finding Summary

- Build a small standalone `JoinBudget` backed by a local SQLite file.
- Count admitted join attempts. A failed or interrupted attempt does not earn a refund.
- Require explicit creation of new state; ordinary reopening must refuse missing or
  damaged known state rather than silently resetting usage.
- Make the capacity decision and one-unit charge in the same transaction. A status
  snapshot is useful information, but never permission to make a later request.
- Keep the existing account ownership, health, read-budget and client code unchanged.
  Stage5 will provide verified identity and place each claim immediately before sending.
- Test real storage, concurrency and process exits. The inquiry has tested the underlying
  components; the new public ledger still needs implementation and its own tests.

## Finding

### 1. Define a unit that the library can actually control

The eventual joining API must limit activity even when Telegram's reply is lost. Counting
only confirmed memberships cannot do that: a failed response does not prove that no
request was sent or no membership change happened.

The allowance therefore counts one unit whenever it admits an attempt. A successful
local claim means that unit has already been recorded. The later caller may use it for
one source attempt. A new retry needs a new claim.

Charges remain for a rolling24-hour interval. This follows the current admission model
and avoids calendar-boundary bursts. It is an explicit library policy choice, not a
claim that Telegram publishes a safe daily rate.

There is no refund or reusable claim-token API in this stage. A crash after commit but
before return can waste a unit of allowance. That conservative outcome is preferable to
issuing free retry permission based on a source outcome the library cannot establish.

### 2. Keep policy changes distinct from consumption

The proposed standalone surface is `JoinBudget(path, *, create=False, clock=time.time)`,
with public `configure(account_id, daily_limit)` and `status(account_id)`. A private
synchronous `_claim(account_id)` supplies the later internal send consumer.

Each account must have an explicit nonnegative limit. Zero prevents new admissions;
a missing policy raises an error. Changing a policy preserves already recorded claims.
A reduced limit may leave usage above the cap, and no new admission is available until
enough old claims expire or the caller deliberately increases the policy.

A frozen status value describes the supplied account key, limit, unexpired usage,
remaining capacity, observed time and optional next availability. Its retry delay is
advisory: another caller or policy change can affect the next decision. It does not
reserve a slot. Plain dictionary conversion provides UTC timestamp text for consumers.

### 3. Make creation an explicit decision

Creating fresh state and reopening known state have different meanings. The default
open must use existing state and refuse a missing file or namespace. `create=True` is
explicit permission to provision a new file or an absent join namespace in a shared file.
It must still refuse an existing partial or unsupported join schema.

This distinction closes a reproduced flaw in the old unmerged allowance implementation.
After its attempts table was removed, calling its constructor recreated that table and
reported zero usage while keeping the account's policy. It then admitted another claim.
The old implementation is useful evidence, but copying it unchanged would copy this reset.

The new module needs only separate join-policy and attempt records plus a schema marker.
It may coexist with `ReadBudget` in one SQLite file, using distinct table names. It must
not change message allowance, refund rules or existing read-budget schema.

Detectable invalid stored values must be rejected before ordinary maintenance can hide
them. In particular, validate attempt timestamps against their permitted range and the
account's prior recorded clock before advancing that clock or pruning expired rows.
The old implementation silently pruned a negative timestamp into free allowance and
accepted a timestamp later than its stored observation horizon as plausible usage.

This is not a promise to detect arbitrary valid-looking external edits or replacement
with an older backup. Cooperating callers must preserve the file and use the same ledger
for the same account. Separate files define separate accounting domains.

### 4. Let one transaction own the decision

Read the account policy, observe time, validate/prune usage and insert the admitted unit
under one writer transaction. A separate “check remaining” followed by a later decrement
cannot coordinate concurrent callers correctly.

The local operation must finish successfully before its consumer may proceed. If commit
or cleanup reports an error, it grants no permission; usage may still have been committed.
Do not infer a refund from that error. If work already failed, a later rollback/close
failure must preserve the original failure or cancellation and use sanitized diagnostics.

Status and refused claims may persist clock observations or prune genuinely expired
records without consuming a new unit. That maintenance belongs to the same transaction
contract, not a background worker or a second cached counter.

Use finite UTC wall-clock values and preserve a nondecreasing observation per account.
This makes rollback conservative. Correct forward time remains an operating assumption;
a local counter cannot distinguish a bad forward clock jump from time elapsed while it
was shut down. Retry hints must not be presented as guaranteed future permission.

### 5. Keep the Stage4/Stage5 boundary visible

The ledger accepts a numeric account key; it does not authenticate a Telegram account.
Stage5 must obtain that key from the merged verified account operation, re-verify as
required for admission, and consume each successful claim once before enqueueing a join.
Every actual retry must be separately admitted. No database transaction spans source I/O.

Stage4 adds no join method, client mixin, `TgData(join_budget=...)` option or health event.
An option without a qualified guard would suggest protection that this stage has not
built. The standalone budget is useful for explicit policy/status setup and provides
the tested local contract the later source integration needs.

### 6. Qualify what runs

The inquiry used actual SQLite and spawned processes, not a simulated successful ledger.
Six competing workers admitted exactly three claims under a cap of three. Exiting an
owned process before commit left zero records; exiting after commit left one. An injected
error after an actual commit left usage in storage, and opening a missing path with
existing-file mode did not create it. The historical ledger's clock and policy behavior
was measured separately from its reset and invalid-time weaknesses.

These results support the component choices. They do not prove the unimplemented new
ledger or disk power-loss behavior. The implementation needs public-method tests for
its exact schema, policies, boundary times, storage failures, races and process exits.
The existing offline regression suites and demos must also pass unchanged.

The [transaction rules](https://www.sqlite.org/lang_transaction.html),
[existing-file URI behavior](https://docs.python.org/3.11/library/sqlite3.html#how-to-work-with-sqlite-uris)
and [storage assumptions](https://www.sqlite.org/atomiccommit.html) are documented by
SQLite/Python. Actual inquiry evidence is in `../contract_probe.py`,
`../evidence/contract-probe.txt` and `../evidence/critique-probe.txt`.

## Next Actions

### MUST

- **What:** write the Stage4 description and explicit implementation plan, then run its
  fresh critic-d and selected fold. **Who:** task-impl in this branch. **Gate:** completed
  inquiry contract. **Why:** settle concrete schema/API/error predicates before code.
- **What:** implement and verify the small allowance module, exports, docs and actual
  SQLite/process tests. **Who:** task-impl after its plan gate. **Gate:** an implementable
  critiqued plan and any required experiment pass. **Why:** turn this contract into a
  measured component without relying on the historical implementation's verdict.

### COULD

- **What:** provide additional examples of policy changes for consumers. **Who:** docs
  author. **Gate:** public status fields are finalized. **Why:** improve usability without
  new runtime semantics. **Depends-on:** MUST “implement and verify the small allowance”.
  This COULD is GATED until that contract is implemented and verified.

### DEFERRED

- **What:** implement verified per-send join integration. **Gate:** Stage4 reviewed/merged
  and a separate Stage5 request. **Why if revived:** enforce this local allowance on source
  requests, with actual join outcomes handled in their proper scope.
- **What:** qualify another persistent backend or extract shared quota infrastructure.
  **Gate:** a concrete additional consumer/backend with matching atomic/error needs.
  **Why if revived:** justified portability/reuse rather than a speculative framework.

## Reasoning

The selected assembly combines the small status/error surface, explicit state custody,
nonrefundable atomic consumption, a documented future consumer seam and real storage
qualification. Those parts satisfy the user’s staged goal without sharing mutable account
health state or introducing remote-outcome recovery.

Every alternative generated and evaluated is accounted for here:

| Alternative | Result and reason |
|---|---|
| Generic multi-resource quota facade | Excluded now: read refunds/warmup and join claims require different transitions; no present consumer justifies widening accepted code |
| Small standalone values and ledger | Kept: clear local unit and compact public surface |
| ReadBudget wrapper | Rejected: initialization/custody and reservation semantics do not match; a safe wrapper would bypass or change its implementation |
| Auto-init with partial-table check | Refined: missing whole state still looks like first-use; require explicit creation intent |
| Explicit provisioning/existing-state open | Kept with validation before clock advance/pruning, closing both schema and timestamp counterexamples |
| External backend contract only | Excluded now: it would defer the actual local delivery and require a new backend qualification surface |
| Reservation receipts, settlement and recovery | Rejected: grant replay cannot safely stand in for another source attempt without a larger source lifecycle |
| One synchronous nonrefundable claim | Kept: actual atomicity is available and uncertainty remains conservative |
| Charge confirmed memberships after acting | Rejected as allowance: missing source outcomes can leave unlimited uncertain attempts uncounted |
| Factory guard in Stage4 | Deferred to Stage5 by the user's explicit scope decision |
| Documented verified consumer obligations | Kept: makes future identity/retry/dispatch duties explicit without implementing them now |
| Omit all future consumption meaning | Rejected: that would carry hidden assumptions into Stage5 |
| Fake storage plus existing regressions | Refined into pure helper supplements; cannot establish new storage behavior |
| Real storage/process/fault tests | Kept, with evidence limits stated |
| Repackage prior tests as new qualification | Rejected: historical passes cannot establish methods that do not exist yet |
| Consumed physical ticket analogy | Not an implementation component; it adds explanation rather than a new mechanism |
| Process-memory-only counter | Rejected: restart and independent processes restore separate capacity |

The apparent tension between reuse and a dedicated module is resolved by reusing proven
patterns, not inheriting an incompatible lifecycle. The tension between availability and
uncertain failures is resolved by retaining charges and refusing permission; no extra
settlement state is necessary. The concrete API/schema/error details remain planning work,
not an unanswered architectural choice or missing human decision.

## Open Questions

### Monitoring

Measure actual transaction latency when Stage5 is exercised. Local synchronous calls can
wait for SQLite's busy timeout; this is not a nonblocking service. A measured unacceptable
latency would justify a separately designed execution model rather than an untested thread
wrapper that changes cancellation semantics.

### Research Frontiers

Cross-host coordination and alternative backends need a concrete deployment requirement.
Live joining behavior and any chosen allowance's effect on restrictions remain outside
what a local accounting test can establish.

### Refinement Triggers

Revisit reusable/idempotent admission only if a consumer requires recovery of stranded
allowance and supplies a verifiable source-attempt lifecycle; losing a local return alone
is not sufficient. Revisit the rolling interval if the user explicitly requires calendar
policy. Neither condition blocks the current Stage4 contract.

## Source Input

```text
$task-impl Next: Stage 4 — join allowance, followed by Stage 5 — joining.
Stage 4 only; review and merge before Stage 5 (Recommended)
```
