---
model: gpt-6-astra
effort: xhigh
---
# Articulation — #44 measurement contract

## User Input
What should #44 activity and engagement measurement mean in tgdata: its bounded
time-window observations, raw facts and aggregates, coverage/completion, unknown
values and failure semantics, while preserving existing reader/progress contracts?

Source task: `$task-impl #44 — Activity and engagement measurement (P2)`.
Issue44 is the requested scope; this inquiry precedes its implementation plan.

## Itemize
Count:1. Item I1: the measurement contract as a whole. Source coverage and numbers
are coupled; splitting them into independent features would lose the ask.

## I1 — bounded activity/engagement measurement
### MQ1 — verdict axis
Question: What kind of answer is requested at this inquiry stage?
Answer: explicit-empty — the inquiry asks for a defensible feature contract before
the already-authorized implementation, not another backlog recommendation.

### MQ2 — context-need axis
Question: What context is needed to resolve the measurement contract?
Answer: identified-ambiguities-list:
- Verdict: whether existing read/progress abstractions expose sufficient evidence
  or a separate bounded source observation is required.
- Kinds: what the SDK/server report about paging, dates, missing rows, author peers,
  views/reactions/forwards/replies and count precision.
- Stance: which guarantees are established locally, which are conditional on live
  visibility, and which need a real-component prebuild or live qualification.

### MQ3 — intent/WHAT axis
Question: Which concrete measurement endpoints could satisfy the request?
Answer: identified-ambiguities-list:
- One collecting-and-summarizing operation versus separate capture and pure analysis.
- A self-contained versioned observation versus a compatible raw-batch extension.
- Bounded observed-prefix statistics versus a completed window census, and what
  evidence each label requires.
- Per-message counting versus assembled-post counting; interval exposure versus
  calendar-day averages; latest seen versus latest in the entire visible window.

### MQ4 — boundary axis
Question: What exclusions constrain the plausible contracts?
Answer: explicit-empty — issue44 explicitly keeps business classification,
advertising scores, background monitoring, permanent archives and edit/deletion
reconciliation out. #45 sampling and #46 discovery resume are separate. Existing
MessageBatch v1/cursor/acknowledgment behavior must be preserved.

### MQA
Reconcile MQ2's reusable-reader question with MQ3's observation-format/coverage
axis: both describe where the evidence boundary belongs. This names the joint
axis without choosing either reader integration. MQ2's validation stance remains
separate from MQ3's requested endpoint.

### Deconstruct
Deliverable: a resolved contract and evidence for the subsequent feature plan.
Kinds: source-grounded findings, falsifiable invariants, boundaries and qualification
frontiers; no product implementation in this inquiry.
Bounds: explicit-window group activity/counters under verified account/read allowance,
existing library compatibility, no business-specific labels or other issue delivery.
No late split: all parts support one trustworthy measurement.

### MultiDepth
Literal statement: What should #44 activity and engagement measurement mean in
tgdata: its bounded time-window observations, raw facts and aggregates,
coverage/completion, unknown values and failure semantics, while preserving
existing reader/progress contracts?
WHY-axis identified-ambiguities-list: trustworthy downstream room comparison;
avoiding duplicated SDK collection; preventing another implementation built on
a false completeness assumption; preserving reusable evidence for future analysis.

### Considered articulations
1. Deliver one bounded verified measurement operation that captures window evidence
   and returns both raw counter observations and explicitly qualified statistics
   in a separate portable value.
2. Deliver reusable bounded observation capture and a pure statistics operation,
   separating source work from interpretation while keeping one #44 contract.
3. Reuse existing batch collection and add a compatible engagement-observation
   extension, then derive window statistics only from explicitly retained coverage.

These are readings, not selections. Each preserves the requested deliverable,
known exclusions and context; none promises accrued views or a business verdict.

## Self-check and telemetry
One item; MQ1–4 all present with explicit 2-shape answers; MQ2 has verdict/kinds/
stance; WHAT and WHY are distinct; three variants span the surfaced axes.
Single light check of all nine Layer1 modes: no firing. No external inquiry or
implementation plan was substituted for framing. Four structural checks
(bundle completeness, axis discipline, 2-shape compliance, composition fidelity)
pass manually; tools/structural_check.sh is absent in this repository.
Verdict: HIGH-PROCEED.
