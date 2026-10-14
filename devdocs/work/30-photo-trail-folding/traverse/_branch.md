---
model: gpt-6-astra
effort: xhigh
---
# Branch: photo-trail contract

## Source Input
```text
$task-impl |  |  |
|---|---|
| #30 — Optional photo-trail folding | Not started. Now unblocked by #29’s merge; its checklist still lists the old blocker. |
```

## Articulation Reference
File: articulate_simple.md. Itemize count:1; item I1; verdict HIGH-PROCEED; no operational flags. Source issue/context: ../source-input.md. All sections below are derived from the saved articulation; no variant is selected here.

## Question
### I1 — #30 — Optional photo-trail folding
Literal-statement: “#30 — Optional photo-trail folding”.

MQ1 verdict-axis openness:
Question: What kind of result is the user asking this implementation to provide?

Identified-ambiguities-list: a pure helper over supplied post observations versus a restartable incremental helper; a replacement view of currently observed posts versus finalized outputs; copying useful consumer semantics versus matching every existing consumer behavior. The task-impl invocation itself is explicit implementation authorization; that is not an ambiguity.

MQ3 WHAT-axis openness:
Question: What observable endpoint could “folding” mean here?

Identified-ambiguities-list: attached photos appear under the earlier logical post while original messages remain inspectable; repeated snapshots revise earlier associations versus irreversible stream emission; sorted observations from overlapping/backfill calls versus strictly forward delivery; caller-managed retention/recomputation versus library-managed serialized tail; unresolved replies or later album content leave observations separate versus refuse the whole operation. These are endpoint shapes, not chosen designs.

## Goal
Deconstruct's deliverable tuple:
Tuple: (deliverable: qualified reusable optional library capability followed by the authorized implementation chain; kinds: contract, code, tests, docs and runnable integration evidence; bounds: original observations and explicit caller state, with source progress/account behavior unchanged). The inquiry answers what can safely be built; it does not replace the task's later planning/critique gates. One coherent task remains.

MultiDepth literal/WHY openness:
Literal-statement: “#30 — Optional photo-trail folding”.

Identified-purpose-motivation-ambiguities (WHY): reduce phantom media-only posts in downstream processing; reuse generic grouping rather than repeat it in each app; preserve recoverability and inspectability when an intent heuristic is wrong. These motivations may trade latency/convenience against conservative nonattachment, but do not authorize losing original messages.

MQ2 context-need openness:
Question: What context does the response need beyond the short task statement?

Identified-ambiguities-list: **verdict** — whether #29's immutable posts and caller-owned receiver suffice, or another persisted tail/revision contract is required; **kinds** — growing album observations, sender peer identities, actual photo types, source ordering versus arrival ordering, timestamps/replies, current source receipts and retained consumer fixtures; **stance** — conservative false-fold avoidance versus exact parity with the old list helper, bounded lifetime state versus caller-selected retained observation windows. Existing source code and actual component probes can inform these alternatives; source-completeness or human-intent certainty cannot be supplied by a fake success fixture.

MQ4 exclusion and open-boundary field:
Question: What is explicitly excluded or constrained by the request and loaded context?

Identified-ambiguities-list (exclusions): opt-in, never enabled on existing calls by default; no text-to-text or photos-before-text inference in this first delivery; no anonymous/unknown/channel-identity folding; no nonphoto attachment; no inferred reply-author lookup over Telegram; no raw-record/hash/receipt mutation or extra source reads; no business classification, seeker merging, contact extraction, leases, source scheduler, edit/deletion reconciliation or ScrapeOps migration. Open boundaries: exact handling of separate all-photo albums as followers, finite retention versus eviction, and output finality must be qualified without relaxing those exclusions.

## Considered Articulations
### I1
1. **A — explicit observation projection:** implement a pure bounded fold over the caller's retained current post observations, returning a replaceable, fully traceable heuristic view; demonstrate carrying the requisite observations across batches/restarts.
2. **B — incremental retained tail:** implement a pure transition with explicit serialized prior tail/state, returning updated inferred posts and the next state for caller-atomic persistence, while qualifying late albums and ordering.
3. **C — receiver-side derived view:** reuse original-record acceptance, then reconstruct and fold a bounded destination view separately from raw acknowledgment, so restart/replay preserves facts and recomputation revises inference.
4. **D — explicitly closed stream segments:** implement forward processing with a caller-declared segment/closure policy and retained unfinished tail, refusing observations inconsistent with that policy rather than silently revising finalized output; no claim of Telegram completeness.

Each is a reading of the same authorized generic feature, not a separate project. All preserve opt-in operation, original records, explicit provenance and the negative scope; none is selected by articulation. A/C may compose but differ in whether persistence composition is part of the capability being qualified.

## Scope Check
Question covers goal: YES. In scope: qualifying the optional generic capability, its inputs/retention/output semantics, conservative association, provenance and original-source obligations. The proposed readings preserve the Deconstruct bounds; none adds deployment or consumer migration. MQ4's exclusions above remain binding. Address the broader cross-batch/restart pattern, using ScrapeOps fixtures as evidence rather than limiting the inquiry to those fixtures. The user explicitly requests a reusable tgdata feature; no scope widening is needed.

## Derivation Check
Item coverage, MQ1–MQ4 coverage, WHY coverage, all four variants and exclusions preserved:5/5. The common observation-view/incremental-final-output axis is retained without adjudication. No cognitive-framework rewrite or multi-inquiry synthesis is requested, so Layer Commitment and Synthesis Trigger do not apply.

## Iteration2 Focus (original articulation preserved)
Resolve the bounded observation-scope and precise temporal-barrier gaps from critique_iter1.md. Compare closed interval refusal, safe context closure and partial-observation approaches using the actual scope_probe counterexample. Keep A/B/C/D and the original exclusions visible; no new feature scope or re-articulation.
