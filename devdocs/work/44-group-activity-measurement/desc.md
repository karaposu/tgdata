---
model: gpt-6-astra
effort: xhigh
---
# #44 — Activity and engagement measurement

## Problem Statement
Applications currently repeat raw Telethon history collection and arithmetic. The audit consumer silently caps history, excludes zero views and conflates unknown senders. Existing `get_statistics(df)` cannot establish source coverage; MessageBatch v1 omits engagement counters and must retain its strict schema.

## User Value Proposition
One `measure_group_activity` call measures a fixed publication period for an explicitly verified account. Callers get useful counts and counter distributions, their raw observations and honest coverage, without owning source pagination or changing their existing batch/progress integrations.

## Success Criteria
1. Expected account, supported group target, aware UTC-normalized `[start_date,end_date)` and finite raw-source cap are explicit; invalid inputs fail before connection. End must not be in the future. Service messages are separate from ordinary raw messages; albums remain separate rows with their album IDs.
2. Result v1 records requested bounds, actual collection times, source slots/pages, unavailable slots, oldest/newest observed dated rows, termination reason and coverage completeness. Cap/short page/error/budget/cancellation never masquerade as complete. Completeness requires a below-start or genuine source-end witness without unknown slots and means visible history during collection, not an atomic snapshot.
3. Raw in-window observations retain IDs, dates, source observation times, author kind/ID, album ID and optional views, reactions, forwards and replies. No text/media payload or access hashes are needed. Values are immutable; `to_dict()` is detached JSON-compatible data.
4. Statistics count ordinary/service messages, distinct known users and channel identities, unknown authors, latest observed ordinary activity and per-UTC-day activity with exact window overlap. Known zero counters survive; each distribution names known/missing populations, sum/mean/median/min/max. Only complete-window message rates use the full requested duration; no average daily unique-user or engagement score is implied.
5. Counters describe observations at collection time on publications in the window, not engagement accrued during it. Unknown is distinct from zero, users from channel identities, and forward counts from forwarding origin.
6. Existing expected-owner verification, actual-send allowance, wait policies, heartbeat, cancellation/cleanup and health attribution remain authoritative. No shared-policy mutations, joins, media downloads or new durable state. History success does not automatically clear group restrictions; only the existing access-check API owns that recovery action.
7. Later failures preserve their original type and best-effort validated partial observations. Malformed pages are rejected atomically; no invalid partial page contributes statistics. Cleanup/cancellation retain existing semantics.
8. A combined real SDK/codec/SQLite prebuild precedes implementation. Public-path tests cover dense/capped, sparse/empty, boundary ties, zeros/missing fields, sender categories, service/album rows, changing counters, malformed pages, partial failure and operational composition. Existing offline suites/demos pass. Bounded live validation is conditional on a qualified exclusive session/allowance; absence is reported, never a synthetic live PASS.

## Scope Boundaries
No business categories/scores, audience-growth claims, admin-only analytics, configurable statistics language, local-calendar modes, assembled-post metrics, archive, background monitoring, edit/delete reconciliation, synchronization/cursor/ack changes, sampling (#45), discovery lifecycle (#46) or PyPI release. Preserve MessageBatch v1 and package version0.1.1.

## Priority Level
Medium (P2): high reusable value, but no existing production path must change to deliver it.

## Decisions and evidence
`traverse/finding.md` resolves the requested contract after the full sequential inquiry. Source: dev490cf5f; Telethon1.45.0 and current verified-operation/budget/heartbeat contracts. `[ASSUMPTION]` public default cap3000 raw source slots follows the existing chat audit's bound; the caller can supply a different finite cap. UTC-only/raw-message-only is an explicit first-delivery boundary.

## Known Blockers
No planning or required offline-implementation blocker. Conditional live qualification has no established exclusive session and authoritative allowance yet; it is optional verification, not a hidden prerequisite for the code path.
