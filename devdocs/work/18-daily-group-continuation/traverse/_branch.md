# Branch: daily group continuation

## Source Input

```text
I would implement daily continuation first

okay do it
```

## Articulation Reference

File: articulate_simple.md. Itemize count: 1. Identifier: DC.
Verdict: HIGH-PROCEED. Flagged conditions: none.

## Question

DC literal statement: “Implement daily continuation first.”
MQ1 has no verdict-axis ambiguity: implementation is authorized.
MQ3 preserves these possible endpoints: facade prepare/acknowledge/status;
independent helper composed over existing batches; integrated consumer callback.
Initial enrollment may take a supplied checkpoint or an explicit starting policy.
What durable continuation contract fits these readings and the current library?

## Goal

From Deconstruct: implemented library capability, public contract/example, offline
tests and pipeline records, within merged batch/lifecycle interfaces and a single
reader per group. From MultiDepth WHY: prevent coverage loss after interruption,
reduce repeated consumer checkpoint code, and permit sequential movement between
machines/accounts. These motivations remain represented without making them new
features.

MQ2 context needed: batch replay and partial-result compatibility (verdict);
starting position, group/source identity, references/downloads and local/custom
durable stores (kinds); local versus remote acceptance and explicit acknowledgment
versus callback (stance). MQA ties acceptance locus to endpoint and starting policy
to enrollment, without selecting either.

MQ4 leaves the precise library/delivery integration boundary open. Its fixed
exclusions remain binding in Scope Check below.

## Considered Articulations

Item DC — Implement daily continuation first:
1. Explicit preparation, acknowledgment and status over a durable store, starting
   from a caller checkpoint and replaying pending snapshots.
2. A continuation helper over get_message_batch, with caller storage/delivery and
   library-owned transition rules.
3. An integrated callback that advances durable progress after successful delivery
   and retains pending snapshots after callback failure.
4. Explicit beginning/current-head initialization, optionally retaining downloaded
   artifacts alongside pending batches.

## Scope Check

Question covers goal. In scope: daily continuation, durable prepared output,
acknowledged progress, restarts, partial failures and a pluggable storage contract.
Out of scope: backfill in this delivery; competing readers; edits/deletions
permanently; account routing/joining; ScrapeOps UI/center scheduler; live Telegram
actions; merging without separate user instruction.

Specific-versus-pattern: solve the daily continuation failure boundary across
the supported batch paths, not only one example cursor file. Do not generalize
into a distributed worker system or the paused health redesign.

## Articulation-preservation check

One item preserved; every MQ2/MQ3 dimension, MQ4 exclusion, WHY motivation and all
four variants are present. No framework redefinition or multi-inquiry synthesis
is requested, so Layer Commitment/Synthesis Trigger do not apply.
