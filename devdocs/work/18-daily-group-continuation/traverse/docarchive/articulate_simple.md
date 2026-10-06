---
model: gpt-6-astra
effort: max
---

# Articulation — daily continuation

## User Input

```text
I would implement daily continuation first

okay do it
```

Warm substrate: ../source-input.md and ../triage.md, including the user's daily
scraping purpose, one-reader boundary, permanent exclusion of edits/deletions,
later backfill and the existing merged MessageBatch contract.

## Itemize

Count: 1. Item DC: “Implement daily continuation first.” Documentation and tests
are parts of that one implementation outcome; later backfill is not another
authorized work item in this invocation.

## Item DC

### MQ1 — verdict axis
Question: What kind of outcome is requested?
Answer: explicit-empty. The current message authorizes implementation after the
preceding assessment; no discussion-only versus implementation ambiguity remains.

### MQ2 — context need
Question: What context could change how a durable continuation is delivered?
Answer: identified-ambiguities-list:
- Verdict: whether existing batch serialization and partial-error behavior can
  be composed with durable pending state without changing their contracts.
- Kinds: starting position (supplied checkpoint, oldest available, or current
  head); group/source identity; references-only versus downloaded media; a local
  SQLite backend versus an application-supplied durable backend.
- Stance: where acceptance occurs (local destination or remote receiver), and
  whether the library exposes an explicit acknowledgment or executes a consumer
  callback. The requirement for restart-safe progress itself is already fixed.

### MQ3 — intent / WHAT axis
Question: Which implementation endpoints can satisfy daily continuation?
Answer: identified-ambiguities-list: a facade prepare/acknowledge/status API;
an independently composed continuation helper over the existing batch API;
an integrated read-and-deliver callback API. Initial enrollment might require
an explicit checkpoint or infer a starting point. These are readings, not choices.

### MQ4 — boundary axis
Question: What is explicitly excluded, and where is the remaining boundary open?
Answer: identified-ambiguities-list: the precise split between library checkpoint
operations and caller delivery integration still needs definition. Fixed exclusions
from the warm substrate: backfill in this delivery; competing readers; edit/deletion
reconciliation permanently; automatic joining/account routing; ScrapeOps UI and
center scheduling; live Telegram actions; merging without separate go-ahead.

### MQA
Reconcile: MQ2's acceptance locus and MQ3's callback/explicit-ack endpoints share
one delivery-boundary axis. MQ2 starting position and MQ3 enrollment share one
initialization axis. MQ4 bounds both without selecting a variant. Media retention
and identity remain distinct axes.

### Deconstruct
Deliverable: implemented daily-continuation capability.
Kinds: library code, public contract/example, offline regression tests and required
pipeline artifacts.
Bounds: current merged tgdata batch/lifecycle interfaces; one reader per group;
durable acknowledgment-driven progress. No late multi-item split detected.

### MultiDepth
Literal-statement: “Implement daily continuation first.”
Purpose-motivation ambiguities (WHY): identified-ambiguities-list — avoiding lost
daily coverage after interruptions; reducing repeated consumer checkpoint code;
making sequential machine changes possible without tying progress to one account.

### Considered articulations
1. Add explicit preparation, acknowledgment and status over a durable store,
   beginning at a caller-supplied checkpoint and replaying pending snapshots.
2. Add a continuation helper around get_message_batch, allowing callers to own
   storage and delivery while tgdata owns the transition rules.
3. Add an integrated delivery callback whose successful completion advances
   durable progress, retaining a pending snapshot for callback failures.
4. Add first-use initialization from an explicitly chosen beginning/current-head
   policy, with optional downloaded artifacts retained alongside pending batches.

## Self-check and telemetry

One item, four mandatory MQs, one reconciliation, one deliverable tuple, both
MultiDepth outputs and four bounded variants. All nine Layer 1 modes: not fired.
The variants stay inside the authorized delivery and preserve the unsettled
initialization, identity, storage and acceptance choices. No selection or plan
is made by this articulation. Composition fidelity and axis separation pass.

**Verdict: HIGH-PROCEED.**
