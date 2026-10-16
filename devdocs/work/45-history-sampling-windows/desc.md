---
model: gpt-6-astra
effort: xhigh
---
# #45 — History sampling across days

**Session warmth:** same session as #43/#44 implementation, review and merge; current base dev77f2f53eba8bdc6922127a3b9118bf17de4efabf. Full batch/value, activity, album/trail and downstream consumer files refreshed; complete owned-operation/budget/heartbeat context retained with current interfaces. triage.md and traverse/surfacing record the bounded inventory. No fresh whole-tree archaeology claimed. PROJECT_SPECIFICS.md/AGENTS.md absent. Current-thread metadata2026-10-16T06:48:39.161Z verifies gpt-6-astra/xhigh.

## Problem Statement
Applications need reading material distributed across a requested period. The downstream stride selects only the newest300 of599 candidates. Correcting stride alone cannot recover older days excluded by a newest-only source cap. Existing batch values provide content but not day-distributed acquisition; #44's coverage-bearing activity values deliberately omit text.

## User Value Proposition
Capture bounded original content across UTC days, then choose a reproducible local sample. Callers can change topic eligibility or sample size without another Telegram read when they retain the capture. Both source gaps and deliberate omissions remain visible; no source progress is advanced by sampling.

## Success Criteria
1. `TgData.capture_group_history` uses an explicit supported group, expected numeric account and fixed aware half-open publication window ending no later than invocation. Reads are distributed across intersecting UTC days rather than exhausted on one newest day.
2. Separate finite message and logical history-request limits bound source work, including empty responses. Under insufficient capacity, a deterministic spread of days gets a turn and all unvisited/incomplete buckets remain reported. Normal allowance/wait policies remain authoritative.
3. An immutable versioned `HistoryCapture` retains original reference-mode raw message records, group/account/window identity, per-day source evidence and observation times. Strict local JSON reload supports exact retained-input replay, refuses malformed/inconsistent state and never creates fresh empty input on failure. A content hash is an observation identity, not proof of source authenticity.
4. Pure `capture.sample(size=300, eligible_ids=None)` returns a separate immutable `HistorySample`. It allocates equally across nonempty eligible UTC days, redistributes sparse-day capacity and uses deterministic evenly spaced ranks with explicit tie/order rules. Same captured content and normalized decisions reproduce selected IDs and sample identity. No fresh-query determinism or statistical representativeness is claimed.
5. Eligibility is an explicit set of existing ordinary captured IDs. None means all ordinary messages; empty means none. Caller predicates run outside the library over retained content. Their failure leaves the capture intact and holds no live client. Services are retained as source observations but not sampled.
6. Selected output is bounded by raw message count, retains original IDs/dates/text/grouping and declares raw-message units. Selected-album metadata reports captured versus selected members and known omissions; global membership stays unconfirmed. No photo-trail inference runs on sparse samples.
7. Source end/boundary evidence and unknown slots determine each bucket's coverage independently from sample omissions. Short pages, caps, failures, unavailable rows or unvisited days cannot become a complete period. Contradictory cross-day repeated IDs refuse atomically.
8. Reuse current verified ownership, budget, heartbeat, health and cleanup. Share only structural raw-page validation with activity, keeping independent projections and preserving #44 behavior. No shared-client policy changes, joins, media downloads, batch schema/cursor/ack changes or durable source state.
9. Original source failures/cancellation propagate with accepted capture evidence attached best effort after resolution. Invalid pages do not contaminate earlier captured content. Local selection/reload errors do not manufacture Telegram health events.
10. A combined real SDK/codec/SQLite prebuild precedes product edits. Tests cover599/300, uneven traffic, sparse/empty days, small work caps, timestamp ties, raw albums/services, explicit eligibility, reload/tamper/duplicate inputs, partial failures, repeated selection, ownership/admission/liveness/cleanup and unchanged activity behavior. Supported full offline baseline and demos pass; conditional live evidence is reported honestly.

## Scope Boundaries
No permanent archive, scheduler, discovery resumption, distributed leases/workers, automatic joining, classifiers/LLM/prompt/report logic, probabilistic confidence claims, local-calendar/alternate strategy registry, atomic whole-post sampling, photo-trail inference, media download or new progress lifecycle. No release/version change, PR or merge in this task-impl run.

## Priority Level
Medium (P2): the next reusable consumer feature after #44; useful for bounded human/LLM review without blocking existing readers.

## Decisions and assumptions
The full inquiry's selected contract is in traverse/finding.md. `[ASSUMPTION]` initial defaults300 selected messages,3000 source messages and100 logical history requests are bounded caller-overridable policy, not validated universal traffic recommendations. Detailed limits/schema/tie rules belong in the plan. Raw-message units and separate capture/selection are deliberate initial scope choices.

## Known Blockers
No planning blocker or required offline execution blocker. Live validation requires a qualified exclusive session and authoritative allowance; neither is established, so it remains conditional supplemental evidence rather than an invented prerequisite.
