# Routes: Stage 1 account operation

## User Input

Territory: _branch.md and six discipline outputs in this inquiry. Goal: implemented, tested Stage 1 with explicit ownership, constructor policy, admission agreement and cleanup; preserve all exclusions and considered API/lifetime alternatives.

## Map Header

Seven identities; five high-priority; six core. Root/project-space, fresh index. Attributes do not select or order routes.

## R1 — Expected and verified account

Type: project-space × teleological × DEVELOP. Goal: the Stage 1 contract above.

Move: Carry a positive expected ID and compare the actual self RPC result.

Lands: An operation has one immutable verified owner.

WHY: Stage 1 gains truthful ownership independent of cached identity.

Priority: HIGH; Confidence: HIGH; Essentiality: core.

Guidance Mode: compact — critique.md C5r (because the lifetime refinement bounds private use).

Depth-link: none; current definition is bounded by the cited contract.

Meaning-gaps: none perceived at this framing depth; implementation evidence remains to be produced.

## R2 — Client construction policy

Type: project-space × teleological × DEVELOP. Goal: the Stage 1 contract above.

Move: Supply fixed policy before constructing and connecting the temporary client.

Lands: Authentication obeys the same policy as the body.

WHY: The stage avoids hidden sleeps and preserves configured routing/device/session behavior.

Priority: HIGH; Confidence: HIGH; Essentiality: core.

Guidance Mode: compact — sensemaking.md K2 (because connect itself makes authenticated calls).

Depth-link: none; current definition is bounded by the cited contract.

Meaning-gaps: none perceived at this framing depth; implementation evidence remains to be produced.

## R3 — Admission identity agreement

Type: project-space × teleological × DEVELOP. Goal: the Stage 1 contract above.

Move: Reuse the handle verification at quota admission.

Lands: Disagreement refuses before quota reservation and message send.

WHY: Stage 1 prevents a later admission from silently changing owners.

Priority: HIGH; Confidence: HIGH; Essentiality: core.

Guidance Mode: compact — decomposition.md interface map (because billing and proof use the same client).

Depth-link: none; current definition is bounded by the cited contract.

Meaning-gaps: none perceived at this framing depth; implementation evidence remains to be produced.

## R4 — Disconnect completion and outcome

Type: project-space × teleological × DEVELOP. Goal: the Stage 1 contract above.

Move: Retain one close completion while preserving the primary outcome.

Lands: Cancellation propagates after the cleanup attempt settles.

WHY: The stage can safely support later operations with remote side effects.

Priority: HIGH; Confidence: HIGH; Essentiality: core.

Guidance Mode: compact — sensemaking.md actual probe (because the SDK shields disconnect internally).

Depth-link: none; current definition is bounded by the cited contract.

Meaning-gaps: none perceived at this framing depth; implementation evidence remains to be produced.

## R5 — Authentication failure clarity

Type: project-space × epistemic × TEST. Goal: the Stage 1 contract above.

Move: Exercise empty/revoked sessions and auth RPC failures.

Lands: No login code is requested and absence is distinct from waits/server errors.

WHY: The stage can refuse unauthenticated work without hiding the cause.

Priority: HIGH; Confidence: HIGH; Essentiality: core.

Guidance Mode: compact — critique.md A1 (because connect can fail before explicit proof).

Depth-link: none; current definition is bounded by the cited contract.

## R6 — Compatibility with ordinary clients

Type: project-space × epistemic × TEST. Goal: the Stage 1 contract above.

Move: Compare existing factory defaults and existing offline suites.

Lands: Opt-in ownership leaves ordinary paths behaviorally compatible.

WHY: The foundation lands without changing established scraping behavior.

Priority: MED; Confidence: HIGH; Essentiality: core.

Guidance Mode: compact — surfacing.md factory and budget seams (because these are shared).

Depth-link: none; current definition is bounded by the cited contract.

## R7 — Health consumer ownership

Type: project-space × epistemic × REFINE. Goal: the Stage 1 contract above.

Move: Clarify how a later health consumer receives the explicit account identity.

Lands: The later consumer has a precise ownership input.

WHY: Indirect: helps the later health stage; Stage 1 can land without its implementation.

Priority: LOW; Confidence: MED; Essentiality: peripheral.

Guidance Mode: compact — source-input.md stage boundary (because health is explicitly separate).

Depth-link: none; current definition is bounded by the cited contract.

## Excluded

Account routing, new storage and joining: present as exclusions, not routes toward the current bounded goal. Public arbitrary SDK supervision: no current consumer; its alternative was explicitly evaluated in the territory. Git workflow actions: process control, not concept routes.

## Telemetry

Two sweeps; second added no identity. Seven individuations; 4 teleological/3 epistemic; priority HIGH5/MED1/LOW1; essential core6/peripheral1. No stale/uncertain identity, no uncovered frontier. Checked all six operational and four identity failure modes. No route selection, dependency graph or process state in index. **Verdict: PROCEED.**
