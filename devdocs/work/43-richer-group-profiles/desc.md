---
model: gpt-6-astra
effort: xhigh
---
# Richer group profiles

> Warm at dev `abd1f577c928cc22c08cdbd9580c2d916e98c64b` on 2026-10-15:
> retained same-session architecture understanding, refreshed complete group,
> connection, ownership, health, budget, heartbeat and facade implementations.
> See triage.md and surfacing.md. No archaeology refresh claimed.

## Problem Statement
Group lookup returns basic identity and membership observations, but callers
still use raw Telegram calls for descriptions, member/online counts and pins.
The downstream audit reader also swallows pin failures, making failed retrieval
indistinguishable from an empty room. Applications need bounded, attributable
profile evidence without duplicating #7's verified ownership and cleanup.

## User Value Proposition
A caller names a group and expected authenticated account, requests an optional
small number of pins, and receives portable profile evidence with timestamps
and honest coverage. The operation preserves the existing route, session, read
allowance and error behavior. Applications retain interpretation and storage.

## Success Criteria
1. An additive public operation returns a frozen group profile for supported
   basic groups, supergroups and broadcast channels. Canonical peer/account
   identities are verified; malformed or mismatched source payloads refuse.
2. Description is preserved in full, empty text remains empty, optional counts
   remain unknown when absent and zero when supplied as zero. Observation times
   describe received metadata/pins, not an atomic Telegram-wide snapshot.
3. Pins are off by default. An explicit bounded limit returns original message
   IDs/dates/text with unavailable/service messages identified. Exact complete
   empty, omitted, limited and incomplete observations are distinguishable.
4. Unsupported community/unknown channel types and references lacking a usable
   profile peer refuse explicitly. Existing lookup handles invite-only previews;
   this feature never joins, logs in or manufactures a full profile from one.
5. Failed optional pin retrieval raises the same source/local exception and
   retains the completed profile as partial_result when the exception supports
   metadata. Cancellation remains cancellation, including during cleanup.
6. Use existing verified operation, source health attribution and request policy.
   Pin reads use the existing message budget and identity recheck; metadata costs
   no message allowance. Success makes no group-access recovery claim.
7. Optional synchronous heartbeat reports actual SDK activity and profile/pin
   completion without timers that make a hung request look healthy.
8. Real SDK/codec/session/SQLite composition checks and the public regression suite
   cover owner mismatch/stale caches, missing auth, field availability, bounds,
   malformed replies, denied pins, waits, cancellation and cleanup. The full
   supported offline suite and demos pass on Telethon 1.45.0.

## Scope Boundaries
One read-only consumer of established #7 contracts. No changes to lookup/access/
join results, MessageBatch v1, sync/backfill cursors, pool routing or worker jobs.
No media downloads, topic/reply traversal, pin mutations, saved snapshots, profile
cache, recurring monitoring, statistics (#44), sampling (#45), discovery resume
(#46), marketing classifications, contact extraction or reports.
The first delivery observes at most one pin-search response, with a maximum
caller limit of 100. It does not promise full enumeration beyond that bound or
an atomic snapshot across metadata and pins. Existing SDK cache behavior applies.
No real account or credentials are needed for offline implementation. Live server
permissions/results remain unqualified unless a separately recorded read-only
check actually runs; synthetic replies prove local composition only.
This task-impl ends after verification and commits. Review/PR/merge remain later.

## Priority Level
**Medium (P2).** Removes duplicated Telegram collection and enables downstream
measurement without importing its business rules.

## Known Blockers
None identified. SDK composition must pass the critic's combined prebuild before
product edits; source availability remains an explicit runtime outcome, not a
reason to assume a successful live observation.
