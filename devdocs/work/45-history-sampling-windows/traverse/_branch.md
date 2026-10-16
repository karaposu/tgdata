# Branch: history sampling across days

## Source Input
```text
$task-impl |  |  |  |
|---|---|---|
| #45 — History sampling across days | P2 | Not started; next in our sequence |
```

## Articulation Reference
articulate_simple.md; count1, itemI1, HIGH-PROCEED, no flags. This directory follows CONTRIBUTING §5/§6.4's issue work-folder convention, overriding the general root-inquiry destination. No discipline/framework rewrite or synthesis of multiple prior inquiry outputs is requested.

## Question
From I1 literal statement: implement #45 — history sampling across days. The inquiry asks what bounded, reproducible period-distributed sampling must mean before that implementation is planned.
MQ1 has no verdict ambiguity. MQ3 retains: live sample versus capture/reselection; equal-day versus traffic-weighted allocation; even rank versus deterministic randomized selection; complete-period capture versus bounded partial-day observations; raw messages versus observed albums/posts; predicates versus supplied eligibility decisions.

## Goal
From Deconstruct: qualify a native sampling contract, then implement code/tests/public docs through task-impl; this inquiry supplies contract findings, not product edits. Bounds: fixed-period content and traceable identities/coverage, preserving existing readers and progress.
From WHY: useful human/LLM reading, avoidance of newest-only bias, controlled source/output cost, auditable repeat analysis and reduced application duplication. Preserve the tradeoffs between acquisition breadth, retained input and output size.
From MQ2: determine existing source/value fit and capped distribution meaning; raw/assembled, per-window/per-day, captured/query-only alternatives; deterministic descriptive material versus statistical inference; local eligibility versus live callbacks; local tests versus conditional live evidence.
From MQ4: no embedded classifiers/scoring/LLMs, scheduler/workers/new backfill lifecycle, unsupported representativeness claim, batch/identity/cursor/ack change or progress from omissions. No merge/release in this implementation request.

## Considered Articulations
I1:
1. Bounded source sampling explicitly distributes reads and selected raw messages across UTC days, returning incomplete-day evidence.
2. Bounded content capture plus reproducible local selection allows same-input/eligibility replay without Telegram.
3. Sample observed assembled posts/albums while preserving original members and qualifying membership.
4. Use immutable MessageBatch capture with pure temporal selection and a bounded source wrapper, preserving schemas/progress.

## Scope Check
Question covers goal. IN: acquisition distribution, units, replay, selection/omission evidence, failure and policy composition. OUT: the explicit Goal exclusions. Address the broader bounded temporal sampling problem illustrated by599/300, not only its stride arithmetic. Item, all MQ axes, WHY motivations and all four variants preserved; no selection during derivation. No Layer Commitment or Synthesis Trigger applies.
