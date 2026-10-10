# Articulation — Stage4 join allowance

## User Input

```text
$task-impl Next: Stage 4 — join allowance, followed by Stage 5 — joining.

Scope clarification:
Stage 4 only; review and merge before Stage 5 (Recommended)
```

Input substrate: this warm session's merged Stages1–3, parent issue7, current read-budget
and SQLite storage code, old unmerged allowance reference and the user's concern about
fundamental design and overengineering. No external lookup during this articulation.

## Itemize

**Count:**1. **I1:** Implement Stage4 join allowance only, with review and merge before
Stage5 joining. The clarification makes Stage5 a boundary/dependency, not a second work
item in this run. Contract, implementation and tests are coupled facets of I1.

## I1 — Meta-questions and alignment

**MQ1 — What is being requested?**
Identified-ambiguities-list: allowance as configured policy plus observed usage versus
an admission decision that later code can rely on; amount-limiting versus success-counting.
The implementation request and Stage4-only scope are explicit, not ambiguities.

**MQ2 — What context is needed beyond the statement?**
Identified-ambiguities-list:
- Verdict: which parts of the unmerged old allowance survive independently of the old
  rejected health/resolver design; whether current storage primitives cover the new unit.
- Kinds: policy/account identifiers, persistent claim records, clock source/window,
  lifecycle/schema state, atomicity/error evidence, public API and future consumer seam.
- Stance: simple caller-controlled library primitive versus comprehensive mutation
  workflow; conservative refusal under uncertain persistence versus convenience repair.

**MQ3 — What action endpoint is intended?**
Identified-ambiguities-list: count admitted attempts versus confirmed new memberships;
rolling interval versus calendar-day reset; local policy/status only versus private
atomic admission too; explicit provisioning/reopen versus automatic initialization;
repeat a call as another claim versus named idempotent claim recovery; policy changes
preserve history versus reset usage; uncertain commits retained versus refunded.

**MQ4 — What is explicitly excluded?**
Identified-ambiguities-list of exclusions and boundary distinctions: Stage5 joining
and its send integration are deferred by the user's answer; no live login/join, general
account router, legacy health redesign, read-budget behavior change, arbitrary system-wide
control of other clients, vendor safe-rate promise, or committing unrelated original files.
The boundary between standalone Stage4 accounting and future verified send admission
needs to be explicit; the exclusion of Stage5 itself is already decided by the user.

**MQA:** reconcile MQ1's policy-versus-admission distinction with MQ3's endpoint choices
as one surface-contract axis. Reconcile MQ2's conservative-versus-convenience stance with
MQ3's creation/recovery choices as a durability-responsibility axis. Keep counted unit,
window and integration scope separate; these are readings, not selected designs.

## I1 — Deconstruct

Tuple: **deliverable**=implemented Stage4 library allowance; **kinds**=behavioral contract,
public/local values and operations, persistent representation where needed, offline
verification and user docs; **bounds**=account allowance for the later joining stage,
using merged ownership foundations and existing repository conventions. Review/PR/merge
are subsequent authorized gates, not automatically included in this implementation run.
No late-split signal: those outputs serve one allowance contract.

## I1 — MultiDepth

**Literal-statement:** “Stage 4 only; review and merge before Stage 5 (Recommended)”.

**Identified-purpose-motivation-ambiguities (WHY):** avoid excessive account mutation
activity versus predictable caller planning; prevent crash/retry loopholes versus avoid
unnecessary denial; keep tgdata a reusable library versus centralize consumer safeguards;
reduce repeated broad-review failures versus make the eventual joining API easy to use.
These motivations can coexist; articulation does not choose a dominant one.

## I1 — Considered articulations

1. Implement a per-account persistent attempt allowance with a rolling interval and
   atomic consumption, leaving source-send integration to Stage5.
2. Implement a durable daily membership-success counter with explicit policy and status,
   leaving outcome reporting and interaction with joining for Stage5 to consume.
3. Implement a small reservation/settlement allowance contract whose ambiguous outcomes
   remain visible until a later consumer reconciles them.
4. Implement a dedicated allowance surface reusing existing local read-budget/storage
   patterns, keeping the counted units and records separate.
5. Implement a provision-once/reopen allowance contract that refuses missing or damaged
   known state, with explicit consumption semantics for later joining.
6. Implement a convenient automatically initialized persistent allowance, requiring
   explicit account policy and clearly stating its storage-custody limitations.

All6 retain an implemented library allowance as deliverable and exclude actual joining,
health/routing rewrites and live actions. They span the named unit, durability, lifecycle
and reuse choices without deciding among them.

## Self-check and telemetry

One light pass: all9 LAYER1 modes not fired (no premature/late item split, extra MQ,
missing operation, missing MQ2 axis, 2-shape commitment, WHAT/WHY conflation or variant drift).
One item;4 MQ questions with identified-ambiguities answers;1 MQA reconciliation;
1 complete tuple; literal plus WHY list;6 bounded variants. All four composition bounds
checked for each variant. The user's scope clarification is preserved rather than
reopened as an ambiguity. No external-anchor phase or execution plan was introduced.

**Verdict: HIGH-PROCEED.**
