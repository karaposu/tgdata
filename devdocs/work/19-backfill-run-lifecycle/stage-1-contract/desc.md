---
model: gpt-6-astra
effort: max
---
# #19 Stage 1 — define the backfill lifecycle contract

> Session warm at dev ancestor `45bab7172621f576fa5e4b3265f87ec20da04fd5` by
> retained same-session code/inquiry work and refreshed full batch, media, progress,
> window, store and budget reads. Prerequisite #18 sources separately at `e9b5154`.
> Scope/source/warmth evidence: triage checkpoint `cc23590`. No archaeology refresh
> or merge of #18 is claimed. Active model/effort: gpt-6-astra/max.

## Problem Statement

The eight-stage backfill plan states the required behavior, but an implementer still
needs one explicit contract for the operations and their failure boundaries. Without
it, two implementations can interpret a retry, pause, unknown storage result or late
receipt differently while each appears to follow the plan. A polished implementation
built on one such disagreement is the failure the user wants to avoid.

The new run lifecycle is not implemented. dev has stable raw batches and budgets;
#18's branch adds daily progress and fixed windows. Current progress APIs do not
provide named-run command authority, permanent completion or saved pacing. Their
passing offline tests do not establish those future guarantees or live Telegram
selection. Stage 1 produces the contract and the means to test these premises early.

## User Value Proposition

The maintainer and later implementing sessions receive a self-contained reference
for what each operation accepts, changes, returns and refuses. A connected assumption
register and failure matrix identify the evidence required before later work proceeds.
Live validation has explicit expected results and stop conditions at Gates A–D.
This delivery leaves a concrete, reviewable foundation before runtime code is built.

## Success Criteria

1. `contract.md` defines run, attempt, collection/destination, command and delivery
   identity. It states how a new intention differs from retrying one; how stale or
   forgotten commands refuse; and what restoring a known run may infer from absence.
2. Every public operation has inputs/preconditions, observable result, durable success
   point, retry/conflict behavior and effects on source access, pending data, accepted
   progress and terminal/control state. Method sketches are explicitly future APIs.
3. The contract states independent state facts and invariants, valid transitions,
   full versus imported-origin completion, pacing/recovery, pause-reading, cancellation,
   abandonment, historical recognition and simultaneous local settlement/control.
4. `assumptions.md` separates selected policies, verified documentary/component facts
   and untested behavioral premises. Each critical premise has a falsifier, earliest
   test, dependent stages, owner and evidence state. No live gate is marked passed.
5. `acceptance-matrix.md` covers the inquiry's 22 adverse histories plus relevant
   implementation boundaries. Cases name initial facts, event order, required and
   forbidden outcomes, evidence method and earliest gate. Coverage maps operations
   and invariants to cases rather than relying on a prose assertion of completeness.
6. `live-validation.md` specifies the opt-in harness, independently established fixture,
   source/store/receiver observations, account/resource inputs, bounded reads, controlled
   interruptions and PASS/FAIL/BLOCKED/INCONCLUSIVE rules. Gate A works with the existing
   reader and Stage 2 run record; it cannot depend on Stages 3–7 being implemented.
7. Critique and selected mitigations are recorded through the complete task-impl chain.
   The overall staged plan is reconciled with the contract where needed; changes and
   later execution dependencies remain visible. No runtime work is smuggled into Stage 1.
8. Document coverage/link/consistency checks and the supported offline baseline suites
   complete with accurately scoped evidence. Verification does not present a document
   audit or existing component test as a new lifecycle passing runtime or live tests.
9. Completed artifacts are checkpointed on the issue-linked branch and #19 records
   only Stage 1 completion. Stages 2–8 and Gates A–D remain pending; no PR or merge.

## Scope Boundaries

Deliver documents/specification and existing-component verification only. No code
under `tgdata/`, no public export or constructor change, no store/schema implementation,
no executable live harness, no test group creation/messages/membership changes and no
live Telegram calls during Stage 1. Do not run the next stage just because its spec
is now ready. The full eight-stage runtime plan remains a separate scope of #19.

Retain one active source reader per group, including caller-scheduled daily/backfill
turns; no competing-machine leases or account routing. Controls and acknowledgments
may overlap with that one source read. Archive/upload ownership and scheduling stay
with the caller. Edits/deletions, worker/UI, ScrapeOps changes and #7 remain excluded.
Do not commit duncan or modify the #7/#18 worktrees. Target Telethon 1.45.0 only.

## Priority Level

**Medium (P2).** Daily scraping needs reliable historical continuation. The user
selected contract definition as the immediate prerequisite to runtime implementation.
The formal Stage 1 path is feature-heavy despite the document-only change.

## Known Blockers

None for writing, critiquing and verifying this Stage 1 contract delivery.

Later execution conditions, preserved rather than treated as planning uncertainty:
- #18's daily/fixed-window implementation is not merged into dev. Later runtime work
  needs an integrated or explicitly authorized base containing it; Stage 1 reads its
  sources separately and does not import code or merge it.
- Live account/session, accessible group, independent expected-message fixture, read
  limits and receiver acceptance must be established before their corresponding gates.
  The requested fixture preference may arrive asynchronously. Unanswered details are
  `UNSET` in the specification, not fabricated approvals or a reason to stop Stage 1.
- Gates A/B/C/D must actually pass before their dependent stages. No synthetic-only
  result or unavailable live environment waives that requirement.

## Inherited Lessons

- More implementation does not establish a source premise. Gate A follows Stage 2
  and precedes the first new source/delivery implementation; cheaper earlier probes
  should run sooner. Later invalidating changes reopen the relevant earlier gate.
- A normal return, empty result or full-sized batch does not by itself certify a job
  complete. Completion needs scoped source exhaustion and all prepared output accepted.
- A stable payload hash is not a run/receipt authority. Scope and accepted command
  context survive reordered responses and repeated operations.
- A nonzero cursor is an imported assertion, not proof that its preceding archive
  exists. Missing known state is a recovery fault, not automatic first use.
- Local storage, validation and replay are not Telegram health observations. Preserve
  original read errors separately when local persistence also fails.
- A budget snapshot is not a reservation, a timer is not a scheduler, and a lost reply
  is not proof that its write rolled back. State these boundaries where operations use them.
