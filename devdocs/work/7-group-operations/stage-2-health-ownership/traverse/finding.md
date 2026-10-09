---
status: active
model: gpt-6-astra
effort: max
---
# Finding: account-owned health for Stage 2

## Question

How should Stage2 make health events, stored conditions and recovery belong to
Stage1's verified account, while keeping this a small prerequisite for later group
operations rather than restarting the rejected broad health rewrite?

## Finding Summary

- Reuse a complete health monitor for each verified account within one TgData.
  Its numeric owner stays fixed for both events and snapshots.
- Add an explicit local `get_account_health(account_id)` query. It returns None
  for an account not observed by this instance, and never opens a connection.
- Begin owned observation only after Stage1 verifies the account. Setup failures
  remain caller errors; they do not become conditions of an unverified account.
- Observe genuine health-related RPC failures at the bound client's request
  boundary, even when the operation later catches the exception.
- Recovery needs later evidence from the same owner. Identity/metadata alone
  cannot establish group access; older work cannot erase newer conditions.
- Record state before returning, then close the source and deliver notifications
  in separate tasks. Observer failure or cancellation cannot replace the work.
- Keep legacy health reporting separate. This stage does not migrate every old
  public call or introduce global aggregation, routing or new persistence.

## Finding

### 1. Give the existing ledger a fixed owner

The previous #7 event fix supplied a fresh ID while its retained summary still
consulted an old cache. That cannot be repaired by another display override.
The health state itself must have the same fixed owner as the event it produces.

HealthMonitor already contains the account, request-wait and group-condition state.
Reuse that complete unit with a fixed verified ID, instead of adding an owner key
to every field. TgData keeps its owned monitors locally, alongside its existing
legacy monitor. State from one account never moves to another, and legacy facts
are never promoted to verified facts by changing their label.

The local query `get_account_health(account_id)` selects that owner explicitly and
returns an independent snapshot. It does no authentication, storage lookup, recovery
or default selection. The old network `health_check()` remains the legacy view;
documentation must make the two views and their source of authority explicit.

### 2. Observe the verified source, not an ambient label

The new internal facade composes Stage1 with an owned health observation. It opens
the health observation only after Stage1 yields its verified handle. The observation
is bound to that exact client and opening task.

Setup and teardown must be isolated from surrounding health contexts. A failed
attempt before proof must not become a ban/logout for either the expected account
or an older enclosing cached account. The exception still reaches the caller.

The factory's request wrapper sees the actual client and a raw Telegram RPC error.
For an active owned observation, record health-related RPC errors there. This is
more reliable and smaller than keeping a general exception-origin registry and
trying to infer provenance from whatever exception eventually escapes.

Owned events use a distinct source such as `rpc`, meaning a request received a
Telegram failure. The enclosing operation may subsequently handle that failure;
it is still a real observation. This differs intentionally from legacy `error`,
which describes the public call ending in error. Arbitrary local errors and their
incidental exception context never manufacture owned Telegram conditions.

### 3. Make recovery conservative and explicit

Capture the operation's order before authentication. It cannot recover a condition
recorded after it started. This prevents a late reply from older work clearing a
newer ban, denial or wait. A later operation can clear the condition with suitable
successful evidence from the same verified owner.

Request waits require matching request evidence and the current condition's
generation/order. A call cannot clear a condition it reported itself. Independent
owners and tasks must not share parent-reported flags.

Group recovery requires an explicit assertion by the internal group operation
after it proves access using the owned client. Self verification is not group
proof. Stage3 remains responsible for interpreting actual group results; Stage2
must not invent a general Telegram permission engine or automatically treat every
metadata response as access.

### 4. Separate notification from the source lifetime

The health state is updated before the operation's outcome is returned. Its queued
notification data is then independent of the source client. Stage1 completes its
disconnect attempt before callback invocation begins.

Both synchronous and asynchronous owned callbacks run in isolated delivery tasks.
Failures and cancellation inside those tasks are contained and their task outcomes
retrieved. Observer re-entry remains suppressed. Cooperative cleanup of outstanding
notification tasks must avoid a callback awaiting itself when it closes TgData.

This means an owned callback may run after the caller receives the operation's
result or exception. The local snapshot is already ready at that point. Keep the
old legacy callback timing unchanged and document this new owned-path timing.
No durable delivery promise, queue worker or background account scheduler is added.

## Next Actions

### MUST

- **What:** plan and implement the fixed monitor/query and owned observation
  composition. **Who:** task-impl in this stage folder. **Gate:** task-desc, plan
  and dynamic critic complete. **Why:** make ownership structural across both sinks.
- **What:** exercise actual SDK, health and callback composition before relying on
  it, then run regressions. **Who:** plan critic/implementation verification.
  **Gate:** before dependent code and at final verification. **Why:** test the
  assumptions that the earlier feature's agreeing fixtures failed to expose.

### DEFERRED

- **What:** migrate legacy health or add aggregation across TgData instances.
  **Gate:** a concrete consumer requests that contract. **Why if revived:** support
  that broader query without pretending uncertain legacy data is verified.
- **What:** guarantee owned callback completion before returning.
  **Gate:** a consumer needs that stronger delivery guarantee. **Why if revived:**
  design its cancellation/backpressure contract as a separate requirement.
- **What:** group lookup/access/join semantics. **Gate:** the user starts later
  stages. **Why if revived:** consume this foundation without merging all of #7 now.

## Reasoning

Five current-component probes exposed relabelling, self-only group recovery,
observer cancellation replacing a primary error, older work clearing a newer wait,
and a caught RPC failure leaving only earlier success evidence. These are why the
design includes source/time/lifetime boundaries rather than only fixed labels.

Rewriting the whole monitor into owner-indexed fields and mandatory instance-wide
account binding were rejected because they expand migration and default-selection
semantics unnecessarily. A fixed complete ledger plus an explicit query covers
the requested new ownership without those problems.

Persistent request traces and credential-generation tags were rejected because
the live wrapper already identifies the client. Source-time RPC recording preserves
caught failures without a historical provenance framework. Cached/ambient ownership
was rejected by the reproduced failures themselves.

Awaited observer completion was deferred because it adds work-outcome and latency
obligations that are not required here. Application-driven manual event draining
was rejected because it would make every consumer rebuild delivery orchestration.
Scoped outer-error isolation survived because merely opening the owned context
after proof does not stop an enclosing legacy wrapper from claiming an exception.

## Open Questions

### Monitoring

The prebuild composition check must confirm isolated notification cleanup and
source-time recording with real SDK code. These are local behavioral checks, not
reasons to request live accounts or invent an external blocker.

### Refinement Triggers

If Stage3 needs an additional explicit derived-domain health assertion, add it
only with the concrete result interpretation and source-evidence tests. This
stage's ownership contract must not be weakened to classify arbitrary local errors.
