# Branch: group-activity-measurement

## Source Input
```text
What should #44 activity and engagement measurement mean in tgdata: its bounded
time-window observations, raw facts and aggregates, coverage/completion, unknown
values and failure semantics, while preserving existing reader/progress contracts?
```

Source task: `$task-impl #44 — Activity and engagement measurement (P2)`.
Issue44 is the requested scope; this inquiry precedes its implementation plan.

## Articulation Reference
File: articulate_simple.md. Itemize count:1. Item:I1. Verdict:HIGH-PROCEED.
Flagged conditions:none. Inquiry is placed here under CONTRIBUTING §5/§6.4's
issue work-folder convention; this takes precedence over the general root-inquiry
directory default. No discipline/framework redefinition or synthesis of multiple
prior inquiry findings is being requested.

## Question
From I1's literal statement: What should #44 activity and engagement measurement
mean in tgdata: its bounded time-window observations, raw facts and aggregates,
coverage/completion, unknown values and failure semantics, while preserving
existing reader/progress contracts?

MQ1: explicit-empty at verdict axis; the inquiry seeks the contract before
implementation. MQ3 preserves these alternatives:
- integrated collection/summary versus capture plus pure analysis;
- independent versioned observation versus compatible batch extension;
- bounded-prefix statistics versus a completed window census, with supporting
  evidence named for either;
- raw-message versus assembled-post unit, interval versus calendar-day
  denominator, latest observed versus latest in the full visible window.

## Goal
From I1 Deconstruct: a resolved contract and evidence for the feature plan;
source-grounded findings, falsifiable invariants, boundaries and qualification
frontiers, with no product implementation inside this inquiry.
From WHY: support trustworthy comparison, reduce duplicated SDK work, avoid false
completion assumptions and retain useful evidence for future analysis.
From MQ2: determine which existing abstraction exposes enough evidence; inspect
actual paging/dates/placeholders/authors/counters; distinguish local composition,
conditional live visibility and required prebuild/live validation.
From MQ4: preserve v1/cursors/acknowledgments; no business classifiers, advertising
scores, background monitoring, archive, edit/deletion reconciliation, #45 sampling
or #46 discovery lifecycle in this issue.

## Considered Articulations
I1:
1. One bounded verified measurement operation captures window evidence and returns
   raw counter observations plus qualified statistics in a separate portable value.
2. Reusable bounded capture plus pure statistics separates source work from
   interpretation while keeping one #44 contract.
3. Existing batch collection plus a compatible engagement-observation extension
   supplies statistics only from explicitly retained coverage.

## Scope Check
Question covers goal. Address the broader trustworthy-measurement pattern behind
the audit script's cap/zero/anonymous-author defects, not only those code lines.
IN: explicit-window group observations under verified ownership and read allowance,
representation, aggregation, coverage and failures.
OUT: the exclusions in Goal. Three variants remain open until downstream reasoning.
Articulation-preservation check: I1, all MQ2/3 axes, MQ4 exclusions, four WHY aims
and all three variants are represented; no commitment-by-derivation.
