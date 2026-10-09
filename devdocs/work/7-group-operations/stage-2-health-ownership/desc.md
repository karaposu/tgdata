---
model: gpt-6-astra
effort: max
---
# #7 Stage 2 — Account-owned health

**Session warmth:** carried from the Stage 1 implementation, review and merge in
this session; base `53306df` is this branch's ancestor. Health, facade, connection,
budget and Stage 1 code/tests were refreshed for this stage. No new architecture
skill run or archaeology refresh is claimed. See `triage.md` for model provenance.

## Problem Statement

Stage 1 verifies a temporary client's numeric account and closes it reliably, but
the health ledger still labels events and summaries using a mutable primary-client
cache. A reproduced group denial was emitted for account B and later summarized
as account A. The same health machinery can treat self verification as group
recovery, let older work clear a newer wait, and let callback cancellation replace
the operation's original exception. A caught RPC failure can also leave only an
earlier successful answer as recovery evidence.

The prerequisite for later group operations is consistent ownership across the
observation, retained condition, recovery and local query. The completed bounded
inquiry in `traverse/finding.md` chooses fixed-owner monitors and source-time RPC
observation, rather than resuming the old broad #7 revision 3 rewrite.

## User Value Proposition

Callers can inspect what this TgData instance observed about an explicitly named
account without silently changing the owner when a session cache changes. Later
group operations can consume this boundary without rebuilding health attribution,
and a health notification cannot alter the work's result or delay source cleanup.

## Success Criteria

1. A verified operation for B with cached A records and returns B in both event
   and `get_account_health(B)`; A's state stays independent. Session is a fixed
   descriptive label, never ownership authority.
2. `get_account_health(account_id)` is a synchronous local, independent snapshot,
   or None for an unobserved account. It never connects or migrates legacy facts.
3. Ownership begins only after Stage 1 proof. Mismatch, missing authentication and
   setup/cleanup errors cannot create a health condition for an unverified or
   enclosing cached account. Original errors and cancellation survive.
4. Genuine health-related raw RPC failures on the bound client/opening task are
   recorded immediately with source `rpc`, including failures the operation
   catches. Local errors, their incidental causes, foreign clients and inherited
   child-task contexts do not create owned observations.
5. Recovery belongs to the same owner and only to conditions older than the
   operation's start. A call cannot clear its own failure. Group recovery needs
   an explicit access assertion after successful owned work; self verification
   alone never recovers a group. Wait recovery needs the matching request.
6. State is ready before returning. Notifications start only after Stage 1's
   disconnect attempt settles, run separately, contain ordinary callback errors
   and cancellation, and prevent callback re-entry. Cooperative close retires
   outstanding notification tasks without a callback awaiting itself.
7. Real Telethon 1.45.0 composition is exercised offline before implementation
   depends on it, then regressions cover owner/task isolation, request outcomes,
   overlap, cleanup, notifications and legacy health behavior.

## Scope Boundaries

Stage 2 builds a private composition boundary and the explicit local account
snapshot. It adds no lookup/access/join operation, automatic join, account pool,
new persistence, global registry, credential-generation tracking or migration of
legacy public methods. `health_check()` and existing public read methods retain
their legacy view and timing. Public methods do not populate the new owned view
until later stages adopt the private boundary.

Access interpretation remains the later group operation's responsibility; no
generic RPC-to-permission engine. Notification completion is not a work-result
guarantee; no durable queue or worker. No live Telegram testing, other account,
login, unmerged #17 dependency, PR publication or merge in this implementation run.

## Priority Level

**High (P2 within issue #7):** this ownership prerequisite must be correct before
building group lookup/access. Wrong attribution can mislead later account routing
even when the underlying Telegram request was correctly executed.

## Known Blockers

None open. The inquiry resolved the scope/design questions with five executed
current-component probes. The plan/critic must test the new composition premise
before dependent implementation; this is locally executable work, not an external
blocker. Stage 1 is already merged at `53306df`.
