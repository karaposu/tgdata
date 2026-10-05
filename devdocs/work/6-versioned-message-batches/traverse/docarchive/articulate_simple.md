---
model: unknown
effort: unknown
---

# Articulation — issue #6 batch contract

## User Input

User invocation: $task-impl on #6 — stable, versioned message batches.

Original issue request:
Filed 2026-10-03 from a draft proposal written for a downstream consumer of tgdata (the proposal itself is not public). The request below keeps its own wording, trimmed to what tgdata itself would do.

**Request.** "Read group X from message N" returns a **versioned batch**:
- the messages, with ids, text, sender, dates and media references;
- an explicit "continue from message M" for next time;
- media files named by a content hash.

The format is the contract between the side that reads and the side that processes. If it's fixed and versioned, either side can change without breaking the other, and a repeated upload is harmless.

**Today.**
- **Reading is resumable, but the output isn't a contract.** `fetch_messages` already continues from a given message id, works in batches and resumes after slow-downs, but it returns a DataFrame.
- `MessageData.to_dict` exists, but no format is fixed or versioned.
- The result doesn't say where to continue next time.
- Downloaded media is named `<chat_id>_<message_id>.<ext>`, not by a content hash, so a repeat upload can't be recognised as a duplicate.

**When it works.** A reader takes 200 new messages, uploads one batch file plus its media, and records "next: from 48213". If the upload is repeated after a network drop, the receiving side sees the same batch and the same media hashes, and nothing is duplicated.


## Itemize

Count: **1**. Item **I1**: “Read group X from message N” returns a versioned
batch of messages, a continuation point and content-hashed media, with
recognizable repeat delivery. These are coupled parts of one producer contract,
not independent feature requests.

## I1 — Meta-questions and alignment

**MQ1 — What is being asked for?** Identified-ambiguities-list: an additive raw
batch API versus changing existing DataFrame output; a producer contract with
supporting file export versus a format specification alone.

**MQ2 — What preparation/context does the response need?**
Identified-ambiguities-list:
- Verdict axis: current read/cursor behavior versus downstream consumer
  requirements that are not yet a schema; which existing behavior is a constraint.
- Kinds axis: message projection, envelope/version, cursor, media references,
  local artifacts and interruption results; their exact representations are open.
- Stance axis: a small explicit v1 contract for a later worker versus a broad
  archival format preserving every vendor-specific field.

**MQ3 — What action endpoint does the user intend?**
Identified-ambiguities-list: replay the same saved snapshot versus recreate an
identical batch by reading again; references-only versus attached-media batches;
continue after the last represented message versus advance past every inspected
item; include all visible message kinds versus only processed DataFrame rows.

**MQ4 — What is explicitly excluded?** Explicit-empty for additional exclusions
in the raw issue. Session constraints remain part of the substrate: this task
is #6, #10's worker is separate, unrelated edits are preserved, and implementation
does not authorize merge/deployment.

**MQA — Reconcile.** The common axis joining MQ1/MQ2 is the ownership and depth
of the new producer contract. The common axis joining MQ2/MQ3 is what a stable
snapshot promises across retries and failures. Preserve both dimensions; neither
alignment selects a schema, an API migration, or a replay guarantee.

## I1 — Deconstruct

Deliverable: implemented versioned reader/processor contract. Kinds: public
library behavior, documented data format, continuation/media representations,
serialization/files and tests. Bounds: Telegram reading and produced artifacts;
the later receiving worker/orchestration remains separate. Existing-call
compatibility and media mode are open design readings, not settled here.
No late split: the tuple still describes one contract with coupled outputs.

## I1 — MultiDepth

Literal-statement: “Read group X from message N” returns a versioned batch:
messages with ids, text, sender, dates and media references; an explicit
“continue from message M”; media files named by a content hash.

Identified-purpose-motivation-ambiguities (WHY): independent evolution of
reader/processor deployments; recovery from repeated uploads; archival fidelity
when Telegram messages or media change. The wording supports all three,
without ranking them.

## I1 — Considered articulations

1. Add a fixed, vendor-independent batch API with an explicit continuation
   point and optional hashed media; replay its saved output after upload failure.
2. Version the current DataFrame export, returning a cursor and hashed media
   alongside the processed rows, while retaining their existing selection rules.
3. Preserve the full Telegram message representation inside a versioned envelope,
   with continuation and hashed media for an archive-oriented consumer.
4. Make repeated calls for the same requested interval reproduce one stable
   batch and media identity despite retries, rather than relying on saved output.

Each variant keeps the requested implemented producer contract and spans a
named ambiguity. They are candidates, not selected designs; the last variant's
feasibility remains for downstream investigation.

## Telemetry and self-assessment

One item, four MQs, one reconciliation, one deliverable tuple, separate WHAT/WHY
axes and four bounded variants. Warm context supplied by the source/triage reads.
Single-pass checks: premature split=no; late split=no; MQ extension=no; missing
operation=no; MQ2 preparation omission=no; missing kinds/stance=no; 2-shape
violation=no; WHAT/WHY conflation=no; variant drift=no. No new external source
was consulted by this articulation. **HIGH-PROCEED**.
