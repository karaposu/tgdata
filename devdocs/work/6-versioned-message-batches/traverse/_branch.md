# Branch: versioned-message-batches

## Source Input

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


## Articulation Reference

- File: `articulate_simple.md`
- Itemize count: 1; item identifier: I1
- Verdict: HIGH-PROCEED; flagged conditions: none
- Output location follows CONTRIBUTING §5's task-local `traverse/` convention.

## Question

Item I1 literal statement: “Read group X from message N” returns a versioned batch:
messages with ids, text, sender, dates and media references; an explicit
“continue from message M”; media files named by a content hash.

Open verdict-axis readings:

**MQ1 — What is being asked for?** Identified-ambiguities-list: an additive raw
batch API versus changing existing DataFrame output; a producer contract with
supporting file export versus a format specification alone.

Open action-endpoint readings:

**MQ3 — What action endpoint does the user intend?**
Identified-ambiguities-list: replay the same saved snapshot versus recreate an
identical batch by reading again; references-only versus attached-media batches;
continue after the last represented message versus advance past every inspected
item; include all visible message kinds versus only processed DataFrame rows.

## Goal

Deliverable shape from Deconstruct:
Deliverable: implemented versioned reader/processor contract. Kinds: public
library behavior, documented data format, continuation/media representations,
serialization/files and tests. Bounds: Telegram reading and produced artifacts;
the later receiving worker/orchestration remains separate. Existing-call
compatibility and media mode are open design readings, not settled here.
No late split: the tuple still describes one contract with coupled outputs.

Context still needed:

**MQ2 — What preparation/context does the response need?**
Identified-ambiguities-list:
- Verdict axis: current read/cursor behavior versus downstream consumer
  requirements that are not yet a schema; which existing behavior is a constraint.
- Kinds axis: message projection, envelope/version, cursor, media references,
  local artifacts and interruption results; their exact representations are open.
- Stance axis: a small explicit v1 contract for a later worker versus a broad
  archival format preserving every vendor-specific field.

WHY-axis openness: independent evolution of
reader/processor deployments; recovery from repeated uploads; archival fidelity
when Telegram messages or media change. The wording supports all three,
without ranking them.

Boundary axis:

**MQ4 — What is explicitly excluded?** Explicit-empty for additional exclusions
in the raw issue. Session constraints remain part of the substrate: this task
is #6, #10's worker is separate, unrelated edits are preserved, and implementation
does not authorize merge/deployment.

## Considered Articulations

Item I1:
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

## Scope Check

Question covers goal. Consider the general producer-contract problem illustrated
by the example 200-message batch; no restriction to that count or group exists.
The inquiry addresses how records, continuation, files and repeat delivery fit
in tgdata, while the future worker/receiver service remains a separate task.
No additional live operation, merge or deployment is authorized by this design
pass. Preserve the unrelated guide edit. No widening is needed.

## Derivation Check

I1 appears in Question and Considered Articulations. MQ1/MQ3 readings are copied
into Question; Deconstruct, MQ2, MQ4 and WHY are copied into Goal; all four
variants are preserved. Five preservation checks pass; no reading selected here.

## User Steering

After the pre-build probes, the user specified:
“we will be using 1.45.0 , no need for 1.33.1”.
Target subsequent implementation and verification at Telethon 1.45.0. The earlier
1.33.1 observation is historical evidence, not a requirement to continue that
compatibility work. The producer-contract question and four original readings
remain unchanged.
