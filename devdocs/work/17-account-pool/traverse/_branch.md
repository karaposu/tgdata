# Branch: account-pool-contract

## Source Input

```text
The other big proposal you’re remembering is #17—the account pool that handles routing and failures automatically.
$task-impl lets do this then

Routing and failover for groups accounts can already read; keep #7 paused (recommended).
```

## Articulation Reference

File: articulate_simple.md. Itemize count: 1; identifiers: A; verdict: HIGH-PROCEED; flagged conditions: none.

## Question

Source: MultiDepth literal-statement and MQ1/MQ3 of Item A.

Literal-statement: “The other big proposal you’re remembering is #17—the account
pool that handles routing and failures automatically. $task-impl lets do this
then. Routing and failover for groups accounts can already read; keep #7 paused
(recommended).”



MQ1:
Identified-ambiguities-list: bounded batch-reader pool versus a pool facade for
daily/backfill; inventory of owned TgData clients versus inventory of immutable
account configurations; transient routing observations versus durable routing
state. Each is a possible shape of the requested implementation.

MQ3:
Identified-ambiguities-list: obtain one usable bounded batch automatically versus
continue a long-lived group reader across account failures; caller-declared
readable groups versus learned access; reuse one account until unavailable versus
distribute calls; retry within the call versus return a deferred outcome.

## Goal

Source: Deconstruct, WHY, MQ2 and MQ4 of Item A.

Tuple: (deliverable: working first delivery; kinds: runtime API, tests, usage
contract and required pipeline records; bounds: routing/recovery over existing
access with existing quota and delivery invariants). This is one coherent tuple;
no late split. The inquiry's answer establishes the contract feeding implementation,
not permission to stop at a design-only deliverable.

Purpose-motivation-ambiguities (WHY): reduce application orchestration burden;
make account failures routine operational events; preserve trustworthy daily
coverage/delivery despite source changes. These motivations can coexist, but
their relative priority is unstated.

MQ2:
Identified-ambiguities-list:
- Verdict: whether actual authentication and SDK retries support bounded,
  attributable failover; whether accepted progress contracts permit changing
  source account without additional visibility rules.
- Kinds: account identity, group identity, budget/warm-up, pending prefix,
  cooldown, cancellation, restart, credential replacement, concurrent calls.
- Stance: one owning process versus multiple independent callers; offline
  correctness versus live two-account qualification; minimal first delivery
  versus general scheduling policy.

MQ4:
Identified-ambiguities-list (negative specification): automatic joining and
resuming #7 are explicitly excluded. Existing session context also excludes
message edit/deletion reconciliation, competing machines for the same progress,
business/UI workflows and implicitly merging this feature. No openness exists
about those exclusions; the ambiguity is the boundary of permitted source
selection within them.

## Considered Articulations

Item A; copied from Rephrase without selection:

1. Implement an owned inventory that selects an eligible account for one bounded
   group batch, with explicit deferred outcomes and caller-managed scheduling.
2. Implement a pool reader used by the existing daily/backfill engines, retaining
   source-independent pending delivery and conservative source visibility rules.
3. Implement a durable routing controller that remembers eligibility, group
   affinity and cooldowns across restarts while callers retain business policy.
4. Implement a process-scoped pool that learns access during reads and distributes
   eligible attempts, with explicit requalification after restart.

All four preserve implementation shape, span identified axes, respect the
negative specification, and use the loaded substrate. They are alternatives to
evaluate downstream, not approved designs.

## Scope Check

Question covers goal. IN: routing/recovery over existing access with existing quota and delivery invariants. OUT: automatic joining, resumed #7, edit/deletion reconciliation, competing progress readers, UI/business workflows and merging. Broader ownership/failure pattern, not merely the two historic #7 reproductions. MQA shared axes remain delivery integration, durability and authority of evidence.

## Synthesis Trigger

This inquiry uses prior results as constraints to re-test, not accepted implementation designs:
- ../source-input.md and main-worktree devdocs/work/7-group-operations/HANDOFF.md: paused review identifies actual/cached identity and SDK error gaps. Reproduce on current dev; do not adopt rejected code.
- docs/backfill_runs.md and docs/daily_continuation.md at dev95ed4c7: pending delivery/ack ownership, visibility-qualified history, caller-confirmed quiescence. Re-test source injection against the current real engines. No claim that prior live gates establish multi-account equivalence.
