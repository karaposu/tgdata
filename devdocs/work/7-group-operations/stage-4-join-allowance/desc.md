---
model: gpt-6-astra
effort: max
---
# #7 Stage 4 — Per-account join allowance

**Session warmth:** already warm from the staged #7 work, at merged `dev`
`1ce39d5c90df399d57b4935cef353762c77cc537`. Refreshed the account operation,
fixed-owner health, read budget, SQLite sync storage, group API, historical join
ledger and review evidence. No archaeology refresh claimed. See `triage.md` and
`traverse/finding.md` for the evidence and contract decisions.

## Problem Statement

The next stage will let a verified account join a group. Before allowing that
mutation, tgdata needs durable local admission: one process or restart must not
forget attempts another process already admitted. The existing read budget counts
messages and refunds unused reservations; that lifecycle does not fit joins whose
remote outcome may be unknown. The old, unmerged join ledger also silently repaired
a missing attempts table and pruned invalid timestamps into free capacity, reproduced
by this stage's inquiry. Reusing it unchanged would preserve those failures.

This qualifies one prerequisite of the original broad #7 request. The user explicitly
chose **Stage 4 only, with review and merge before Stage 5**. Joining itself is not
part of this delivery.

## User Value Proposition

Callers can explicitly provision, configure and inspect an account's rolling
24-hour join allowance in local SQLite. Cooperative processes using the same file
share the accounting. Later joining code receives a tested atomic claim primitive
instead of reconstructing quota behavior alongside Telegram error handling.

## Success Criteria

1. A small standalone `JoinBudget` provides explicit creation, configuration and
   immutable status. Account policy is required; a zero cap prevents admission.
2. A successful private claim atomically records one admitted attempt before it
   returns. Usage survives reopening and process exit; concurrent claims never
   exceed a configured cap. There are no refunds or reusable claim tokens.
3. Policy changes preserve claims; rolling expiry, lowered caps and backward clock
   observations yield accurate status and conservative admission. Retry hints
   never constitute reserved permission.
4. Normal opens refuse missing state. Explicit creation may initialize fresh state
   but refuses a partial/unsupported join schema. Detectably invalid policy, clock
   or attempt records are rejected before maintenance can hide them.
5. Storage errors grant no permission, even if commit may already have succeeded.
   Secondary cleanup errors preserve the primary failure/cancellation. Diagnostics
   are sanitized and local errors cannot become Telegram health observations.
6. Separate join tables coexist with ReadBudget without changing its behavior.
   Existing clients, verified-account operations, health and group lookups remain
   unchanged. Actual SQLite/process/fault tests and supported offline regressions
   establish the delivered contract.

## Scope Boundaries

- No joining API, raw request guard, `TgData` option, automatic retries, join-result
  cache, account router, warm-up policy, settlement or refund mechanism.
- No cross-host storage, database backend abstraction, generic quota framework,
  read-budget refactor, prior-stage cleanup or unrelated files.
- No live joins, login prompts or Telegram requests in this stage's verification.
- The numeric key is supplied, not authenticated by the ledger. Stage 5 must use
  fresh verified identity and consume a new claim immediately before each actual
  source attempt/retry. Stage 4 does not protect raw client calls.
- SQLite and a caller-controlled forward wall clock are operating assumptions.
  Cooperative same-host callers must retain and share the file. Arbitrary valid
  external edits, backup rollback, separate files and broken storage hardware are
  not detected. Local synchronous calls can wait for SQLite's bounded busy timeout.
- A commit/return ambiguity can waste capacity. Counting confirmed memberships or
  reclaiming an uncertain attempt would require a different source lifecycle.

## Priority Level

**Medium (P2).** Required before Stage 5 can safely enforce the user-configured
allowance, but the completed read-only stages remain usable independently.

## Known Blockers

None identified. The inquiry tested actual SQLite serialization, process exits,
existing-file opening and ambiguous commit behavior before implementation planning.
Concrete API/schema predicates and their tests are planning work, not missing human
decisions. Stage 5 waits for this stage's later review and merge; it does not gate
this local implementation.
