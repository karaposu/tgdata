# Articulation — account routing and recovery

## User Input

```text
The other big proposal you’re remembering is #17—the account pool that handles routing and failures automatically.
$task-impl lets do this then

Routing and failover for groups accounts can already read; keep #7 paused (recommended).
```

## Itemize

Count: 1. Item A: implement the selected first delivery of #17. Routing and
recovery share one account/source contract; they are not independent requests.
Warm substrate: merged daily/backfill contracts, existing quota enforcement,
issue17, paused issue7 and triage at dev95ed4c7.

## Item A — MQ and MQA

**MQ1 — What is the user asking for?**
Identified-ambiguities-list: bounded batch-reader pool versus a pool facade for
daily/backfill; inventory of owned TgData clients versus inventory of immutable
account configurations; transient routing observations versus durable routing
state. Each is a possible shape of the requested implementation.

**MQ2 — What context does this response need?**
Identified-ambiguities-list:
- Verdict: whether actual authentication and SDK retries support bounded,
  attributable failover; whether accepted progress contracts permit changing
  source account without additional visibility rules.
- Kinds: account identity, group identity, budget/warm-up, pending prefix,
  cooldown, cancellation, restart, credential replacement, concurrent calls.
- Stance: one owning process versus multiple independent callers; offline
  correctness versus live two-account qualification; minimal first delivery
  versus general scheduling policy.

**MQ3 — What is the user trying to accomplish (WHAT)?**
Identified-ambiguities-list: obtain one usable bounded batch automatically versus
continue a long-lived group reader across account failures; caller-declared
readable groups versus learned access; reuse one account until unavailable versus
distribute calls; retry within the call versus return a deferred outcome.

**MQ4 — What is explicitly excluded?**
Identified-ambiguities-list (negative specification): automatic joining and
resuming #7 are explicitly excluded. Existing session context also excludes
message edit/deletion reconciliation, competing machines for the same progress,
business/UI workflows and implicitly merging this feature. No openness exists
about those exclusions; the ambiguity is the boundary of permitted source
selection within them.

**MQA — reconcile.** MQ1's pool facade and MQ3's continued group reader share the
delivery-integration axis; MQ1 durable state and MQ2 restart share durability.
MQ2 ownership and MQ3 declared/learned access share authority of evidence. These
joint axes preserve all listed alternatives rather than selecting one.

## Deconstruct

Tuple: (deliverable: working first delivery; kinds: runtime API, tests, usage
contract and required pipeline records; bounds: routing/recovery over existing
access with existing quota and delivery invariants). This is one coherent tuple;
no late split. The inquiry's answer establishes the contract feeding implementation,
not permission to stop at a design-only deliverable.

## MultiDepth

Literal-statement: “The other big proposal you’re remembering is #17—the account
pool that handles routing and failures automatically. $task-impl lets do this
then. Routing and failover for groups accounts can already read; keep #7 paused
(recommended).”

Purpose-motivation-ambiguities (WHY): reduce application orchestration burden;
make account failures routine operational events; preserve trustworthy daily
coverage/delivery despite source changes. These motivations can coexist, but
their relative priority is unstated.

## Considered articulations

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

## Self-check

Modes 1–9: not-fire (no split conflict, late split, extended MQ, missing operation,
missing MQ2 axis, 2-shape commitment, WHAT/WHY conflation or variant drift).
All required bundle fields present. Low procedural friction; semantic questions
are intentionally retained rather than resolved by articulation.

**Verdict: HIGH-PROCEED**
