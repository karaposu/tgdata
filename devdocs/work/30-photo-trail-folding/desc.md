---
model: gpt-6-astra
effort: xhigh
---
# Description — optional photo-trail folding (#30)

Session warmed at dev `35c4362d4e6a8fc92e695def67bffcac192dc073` (2026-10-15): same session as #29's complete implementation/review/merge, with fresh raw/album/reader and consumer helper/caller/fixture reads. warm.md and surfacing.md record actual coverage. Current turn records verify GPT 6 Astra/xhigh. The required issue-linked branch is feat/30-photo-trail-folding.

Input: source-input.md preserves the original issue. The two-pass inquiry in traverse/finding.md qualifies its interpretation; eleven actual SDK/SQLite/source-engine contract histories passed. Those sketches are not production implementation or the later complete candidate prebuild.

## Problem Statement

A person may publish a text post or Telegram album and then send additional photos as separate posts. Album assembly preserves Telegram's explicit grouping, but it does not infer this extra relationship. Consumers can therefore process a trailing photo as an unrelated empty-text post.

ScrapeOps already guesses these relationships over one supplied list, but its helper mutates anchors, accepts nonphoto media and does not retain cross-call context. Copying it unchanged would also inherit backward-time/channel-identity cases and a duplicate-ID fixture. The generic capability needs explicit inference and durable original evidence, not compatibility with those incidental behaviors.

## User Value Proposition

An application can explicitly enable conservative photo-trail grouping and obtain one current view of related original posts. Every caption, original identity and media reference remains inspectable. Recomputing the view after another batch or a restart updates or withdraws associations without losing the underlying posts.

The application keeps control of storage, selected history scope and downstream processing. The library adds no extra Telegram reads, inferred-delivery acknowledgment or mandatory storage service.

## Success Criteria

1. An opt-in pure operation consumes a finite current set of existing TelegramPost values and a validated policy. Existing library calls remain unchanged; default policy is disabled.
2. Original posts/members/IDs/captions/media remain unchanged and occur exactly once in a full immutable versioned result. The result exposes original values, association links, policy/version, canonical revision and separate counts for absorbed original posts and attached photo messages. It is a provisional current view, never a final source receipt.
3. Same-chat, positively identified same-user eligibility, actual textless photo-only followers, known earlier reply targets, nonnegative chained gaps, total-span and attached-photo limits are enforced. Text-bearing posts and incompatible activity end prior trails. Photo-only albums may attach atomically; photos-before-text and text-to-text merging are excluded.
4. Inference accounts for every original member's event position. Unknown/unsafe late members cannot be hidden by album display order. Other known users may interleave independently; same-user overlapping post intervals, missing dates and backward chronology remain conservative barriers.
5. Canonical results are independent of supplied post-list order. Identical observations are idempotent when admitted; incompatible revisions or conflicting raw identity refuse. Later original observations can withdraw an older attachment in a replacement view. No hidden tail timer or completeness assumption is used.
6. Explicit positive member/serialized-byte bounds refuse the whole operation without truncation, mutation or eviction. Saved values validate strict schema/content/relationships and propagate deliberately raised limits through reload.
7. A runnable optional SQLite composition reuses #29's original-record receiver. It loads all stored observations in an explicit chat/message-ID interval and refuses if that interval splits a known current post. Selection/extent/preflight/load share one consistent read snapshot; missing known state and corrupt data raise.
8. Original-record acceptance/confirmation stays independent of current inference size and policy. Daily/backfill integration uses the exact original source receipt after durable acceptance. Lost reply, restart, cancellation, resource/scope refusal and late observations preserve accepted data and source authority.
9. Documentation teaches full-view replacement in a caller-selected scope, provisional inference, explicit policy assumptions, conservative nonattachment, range refusal, retained original data and downloaded-media custody. ScrapeOps remains a reference consumer, not an automatic migration target.
10. The complete candidate passes real SDK/value/SQLite/daily/backfill qualification before production adoption, then focused tests and the full supported offline suite on Python3.11.10/Telethon1.45.0. Synthetic source responses and live-validation limits are stated accurately; no universal human-intent accuracy is claimed.

## Scope Boundaries

No edits to TelegramPost v1 or MessageBatch v1 semantics, source receipts/progress schemas, account health/routing/budgets, joins or worker behavior. No automatic source fetching, window widening, state reset, archive eviction, distributed leases, classifier, contact extraction, seeker-text merging, old edit/deletion reconciliation or final-stream delivery protocol.

Caller-owned original retention and view replacement remain explicit. The example accepts reference batches as #29 does; the pure view preserves both original media modes without claiming to copy downloaded bytes. No release, merge, PR publication or running ScrapeOps migration is part of this task-impl delivery.

## Priority Level

Low/P3, selected by the maintainer for implementation now. This is optional consumer convenience and reusable inference, not a correction to the already valid raw/album contracts. Feature-heavy describes the semantic and recovery risk, not urgency.

## Known Blockers

No OPEN planning or external execution blocker. The source-completeness and human-intent questions are intentionally not claimed by this provisional heuristic. The inquiry closed the scope/ordering gap using a retained counterexample and actual component probes. A reviewed complete candidate prebuild remains mandatory before adoption; a structural failure there must stop the run under task-impl.

[ASSUMPTION] Initial configurable heuristic defaults: disabled,30-second per-member gap,120-second total span from the anchor's last original member,20 attached photo messages. The30-second value comes from the reference consumer; the two additional limits are conservative work/policy choices, not calibrated Telegram facts. The plan must make their exact units and validation explicit.
