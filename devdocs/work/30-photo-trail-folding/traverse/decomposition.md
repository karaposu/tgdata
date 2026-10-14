---
model: gpt-6-astra
effort: xhigh
---
# Decomposition — remaining scope and ordering decisions

## User Input
_branch.md Iteration2 Focus and sensemaking.md SV6. The original four-piece decomposition remains in decomposition_iter1.md; this pass refines its two unresolved determination mechanisms.

## Coupling Map
Strong cluster K1: requested original-ID interval, selected post extents, known intervening records, consistent read snapshot and preflight limits. These must be decided together: changing boundary semantics changes which rows must be checked before materialization. Strong cluster K2: per-member event order, positive shared owner, overlapping post intervals, text/nonphoto/unknown barriers, chained gap/reply/count/span and anchor activation. A late barrier changes the next eligible attachment, so “eligibility” and “state transitions” cannot be separate contracts.

Moderate interface: K1 supplies a finite coherent observed domain; K2 computes deterministic links within it. Weak existing interface: original-record acceptance/confirmation supplies durable facts and remains independent of both. Result serialization consumes K1/K2 and retains the earlier Q3 contract; no new result-lifecycle decision is introduced.

## Top-Down Boundaries and Bottom-Up Validation
Cut at validated original observations and deterministic relation output, as before. Atoms are a stored row/post key, an explicit interval, an original event, and an association edge. No atom is split: “whole post” cannot hide an individual interrupting event. K1 and K2 each have internally cohesive rules and one directional interface. Both boundaries agree top-down/bottom-up: HIGH confidence. The former scope/barrier work was under-specified, not a reason to create another service.

## Question Tree

**K1 — How can an explicitly bounded stored view preserve all known context it claims to analyze?** Verification: compare split-album refusal, bounded transitive closure and partial observations; reproduce the1,2,4 omission; define exact empty/range cases and closure discovery; refuse before payload when key/member/byte caps fail; keep one read snapshot; preserve strict known-state errors and original confirmation. This question can be answered without a folding algorithm.

**K2 — How are anchor activation, attachment and interruption determined at original event positions?** Verification: every raw member has one event; positively identified per-post user is deterministic; same-user overlapping intervals and invalid chronology are flagged before inference; unknown-author late members interrupt at their own IDs; other known users remain independent; whole photo-only followers attach only after all their relevant evidence is accounted for; exact reply/gap/span/count rules and replacement on late captions are testable. This question can be answered on explicit finite post fixtures without a database.

**Reassembly qualification:** compose the K1 choice and K2 choice with actual #29 storage/SDK values and the existing source receipt boundary. Verify late observation/restart/replay, scope/resource refusal, preserved originals and changed current relations. This is a cross-boundary verification obligation, not a third independent subsystem.

## Interfaces and Assumptions
K1→K2: current original TelegramPosts, with the declared observed domain. No claim that unseen Telegram messages are absent. K2→existing result design: relation edges, exact policy and counts; no mutation/receipt. Source acceptance→caller ack: original raw delivery; neither K1 nor K2 adds authority. K1↔caller scope selection: explicit boundaries and a refusal outcome when they cannot be honored; no silent widening, reset or clipping. Assumptions are named rather than left as caller folklore: current snapshot consistency, intended observation namespace, and full-view replacement belong in executable examples/docs.

## Dependency Order
Resolve K1's scope semantics and K2's event semantics before choosing the final adapter/core API. Their finite interface permits separate probes, followed by the combined qualification. Preserve original Q3 value invariants and Q4 original-acceptance isolation. Do not build production before the later full task-plan/critic-d candidate gate.

## Self-Evaluation
Independence PASS (separate data-selection and inference questions). Completeness PASS (both critique gaps and their runtime determination mechanisms included). Reassembly PASS (actual selected originals→events→relation, independent raw ack). Tractability PASS (two bounded mechanisms). Interface clarity PASS (scope, assumptions and refusal explicit). Balance PASS (both are substantial; no leftover omnibus integration piece). Confidence PASS (two matching top-down/bottom-up cuts). All seven failure modes checked; no additional decomposition needed. Manual7/7 structure.
