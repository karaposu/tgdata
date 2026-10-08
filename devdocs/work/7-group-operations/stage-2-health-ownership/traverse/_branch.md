---
model: gpt-6-astra
effort: max
---
# Branch: Stage 2 health ownership

## Source Input

`$task-impl stage 2`

Warm context: Stage2 is health ownership after merged Stage1; source-input.md
preserves the staged scope, prior rejection and the user's concern about growth.


## Articulation Reference

articulate_simple.md; Itemize count1, I1; HIGH-PROCEED; no operational flags.

## Question

Literal statement: `$task-impl stage 2` — in the established health-ownership scope.

- **MQ1 — What is the user asking for?** Identified ambiguities: a fixed owner for
  each health monitor versus owner-indexed state inside the existing monitor;
  opt-in health for Stage1 operations versus migration of every legacy observation.
- **MQ2 — What context does the response need?** Identified ambiguities:
  **verdict** — whether actual SDK evidence and callback lifetimes support the
  boundary; **kinds** — verified identity, legacy snapshots, request/recovery
  evidence, task nesting and delivery semantics; **stance** — minimal prerequisite
  versus broad health-system replacement. The earlier rejected design is evidence
  to challenge, not a selected starting point.
- **MQ3 — What endpoint is intended?** Identified ambiguities: owner-specific local
  snapshot versus changing the existing network health_check summary; unverified
  setup failures as diagnostics versus account conditions; automatic versus
  explicitly authorized recovery for an operation's successful requests.
- **MQ4 — What is explicitly excluded?** Explicit-empty for ambiguity. NOT-list
  from warm context: group lookup/access, join allowance, joining, account routing,
  cross-instance aggregation, new persistence, live account tests and resuming the
  broad old revision3 implementation. Preserve Stage1's cancellation/cleanup rules.

**MQA — reconcile.** MQ1's migration choice and MQ3's query choice share a legacy
compatibility axis. MQ2's evidence/delivery questions remain separate from choosing
a storage surface. No alternative is selected here.


## Goal

Tuple: (deliverable: implemented and verified Stage2; kinds: code, offline probes/
tests, maintainer contract and workflow evidence; bounds: health ownership and its
Stage1 integration). No late split: all outputs support the same safety boundary.

## MultiDepth

Literal statement: `$task-impl stage 2`.
Purpose/motivation ambiguities: explicit-empty. The warm context explicitly names
the goal of avoiding a flawed foundation and keeping later #7 stages manageable.


MQ2's verdict/kinds/stance and MQ4's exclusions above remain goal inputs, preserved
without selection. The requested implementation must make ownership coherent
across events, stored health and recovery while honoring the staged scope.

## Considered Articulations

1. Give each observed account a fixed-owner health monitor for Stage1 operations,
   with an explicit local snapshot and compatible legacy behavior; distinguish
   unverified setup from owned work and control recovery evidence.
2. Partition the existing health monitor's state by account, extend health_check
   to choose a ledger, and integrate the owned operation with the current callback
   and recovery machinery.
3. Bind an entire TgData instance permanently to one expected account and migrate
   its existing health-producing paths to require verified source identity.

These are readings, not selected plans. Each preserves the implementation shape
and health-only scope; they vary storage ownership, legacy migration and query
surface. Pre-proof diagnostics, evidence and delivery must be resolved in each.


## Scope Check

Question covers goal. IN: the Deconstruct bounds. OUT: the complete MQ4 NOT-list.
Address the broader ownership pattern illustrated by the old event222/snapshot111
case, including later reads and overlapping calls; not just two hardcoded IDs.
This is ordinary software design, not a rewrite of a cognitive protocol or a
synthesis of multiple prior inquiry findings; no Layer/Synthesis trigger applies.
