# Branch: Stage4 allowance contract

## Source Input

```text
$task-impl Next: Stage 4 — join allowance, followed by Stage 5 — joining.

Scope clarification:
Stage 4 only; review and merge before Stage 5 (Recommended)
```

## Articulation Reference

- File: docarchive/articulate_simple.md, read before this derivative was written.
- Itemize count:1; identifiers:I1; verdict:HIGH-PROCEED; flagged conditions:none.
- Inquiry path is this task's traverse/ folder under CONTRIBUTING §5; it is not a
  new independent issue or an implementation of the historical broad branch.

## Question

I1 literal: “Stage 4 only; review and merge before Stage 5 (Recommended)”.
What should the Stage4 join allowance promise to its caller and future Stage5 consumer?
From MQ1: is the needed surface policy plus observed usage, an admission decision, or
both; does “allowance” concern attempts or successful memberships?
From MQ3: preserve the open choices of admitted attempts/confirmed memberships,
rolling/calendar window, policy/status/private atomic admission, explicit provisioning/
auto-initialization, repeated-call/new-claim versus named retry recovery, policy history
preservation/reset, and retained/refunded uncertain commits. These are inquiry questions,
not design selections. The task-impl implementation and Stage4-only scope are settled.

## Goal

From Deconstruct: a coherent implemented library allowance, with contract, local/public
values and operations, persistent representation as needed, offline verification and
docs; bounded to account allowance for later joining and existing repository conventions.
The inquiry supplies its contract to description/planning; it does not replace that chain.

From MultiDepth WHY: preserve the possibilities of account-activity restraint/predictable
planning, crash/retry protection/avoiding unnecessary denial, reusable library/centralized
consumer safeguards, and reliable staged progress/easy eventual joining. An answer must
serve these practical motivations without assuming one cancels the others.

From MQ2: evaluate which old allowance parts survive independently of the rejected broad
feature, using current policy/claim/storage/clock/account/error/API/consumer facts. Context
kinds include identifiers, claim records, schema lifecycle, atomicity and offline evidence.
The stance choice remains minimal caller-controlled primitive versus broader workflow,
and conservative refusal versus convenience repair where persistence is uncertain.

From MQ4: Stage5 joining/send integration, live login/join, general routing, legacy-health
redesign, read-budget behavior changes, other-client system-wide enforcement, safe-rate
promises and unrelated original-file commits are outside this inquiry's deliverable.

## Considered Articulations

I1 — Implement Stage4 join allowance only:

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

## Scope Check

Question covers goal. The user chose Stage4 only; this framing cannot authorize Stage5.
The inquiry covers the broader account-allowance behavior, with old failures as evidence,
not merely a patch to their examples. Existing verified ownership is a dependency already
merged; investigate an integration seam without reopening that model gratuitously.
No protocol/framework redefinition or multi-inquiry roll-up is requested, so no Layer
Commitment/Synthesis Trigger applies. Prior artifacts are contextual evidence to retest,
not findings being consolidated into a new canonical protocol.

## Derivation audit

All1 items,4 MQ axes (including MQ2 verdict/kinds/stance), MQA's two shared axes,
Deconstruct tuple, literal and4 WHY pairs, exclusion list and6 variants survive.
No option was selected during derivation; no Stage5 work item was reintroduced.
