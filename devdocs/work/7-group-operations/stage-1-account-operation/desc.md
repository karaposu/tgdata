---
model: gpt-6-astra
effort: max
---
# #7 Stage 1 — account-owned temporary operations

**Session warmth:** same session as the #18/#19/#17 implementation and #7 restart
assessment; current dev95 factory, budget, session and health seams plus installed
Telethon1.45 authentication/disconnect sources refreshed. See `triage.md` and
`surfacing.md`. Same-session rollout metadata last observed at
2026-10-07T05:34:50.039Z records gpt-6-astra/max; no fresh timestamp is claimed.
The contribution guide's feature row names Astra/xhigh; max is the recorded higher
effort setting. Model verification remains reviewable at the merge gate.

## Problem Statement

A session name or cached SDK identity does not establish which account owns a
temporary operation. The rejected #7 code exposed this ambiguity. It also applied
its no-wait policy after authentication and could return from cancellation while
SDK disconnect was still running. Later group features need one small, reliable
account boundary before their behavior is implemented.

## User Value Proposition

Later tgdata operations can declare an expected account and safely receive that
account's verified client. Wrong or missing authentication refuses before group
work. Failure and cancellation retain their meaning through cleanup. This first
stage is an internal foundation; it does not yet add group lookup or joining.

## Success Criteria

1. Expectation is a positive integer Telegram account ID, never inferred from a
   session filename or cached identity; booleans/nonintegers/nonpositive IDs fail
   before client construction.
2. The fresh client preserves configured proxy, device identity, session storage
   and optional budget. Request/wait/reconnect policy is set before connect/auth.
   Ordinary client construction and lifecycle defaults remain unchanged.
3. A fresh self RPC proves the owner. Expected B/cached A/actual B proceeds as B.
   Expected A/actual B refuses before yielding control to group work.
4. Empty, logged-out or revoked sessions raise explicit authentication errors
   without prompting or requesting codes. Wait/server/transport errors remain
   their own errors; final RPC failures are not generic retry-exhaustion errors.
5. The private handle passes a read-only verified ID and client to its owning task.
   Fresh later admission must agree; mismatch or missing authentication precedes
   reservation/send. Closed or foreign-task handles cannot admit work.
6. Every constructed client gets one disconnect attempt on success, connect/auth
   failure, body failure and cancellation. The attempt settles before exit, even
   under repeated cancellation. Cleanup error text is never logged; its type may
   be logged without replacing the primary work result/error. Caller cancellation
   remains cancellation; internal disconnect cancellation is only a cleanup failure.
7. Offline tests use actual Telethon1.45 dispatch/disconnect plus synthetic replies,
   real read-budget storage and forced overlap. No network/login/group changes.

## Scope Boundaries

Private lexical context only; no public TgData group API, arbitrary SDK extension
API, login wizard, new database, join allowance, routing or health redesign.
Health attribution is Stage 2; lookup/access Stage 3; joining belongs to later
stages. No import of the rejected implementation or unmerged #17 pool.

The handle is for trusted internal code: no credential/session rebinding, login,
detached child work or retained raw-client use. Cleanup guarantees one completed
attempt, not a bounded duration or successful closure if the SDK itself fails.

## Priority Level

High within #7 (issue priority remains P2): this foundation prevents later work
from inheriting ambiguous ownership. It does not elevate the whole backlog issue.

## Known Blockers

None. Source inspection and a real SDK cancellation probe resolved the local
behavioral questions. `traverse/finding.md` records the selected contract.
