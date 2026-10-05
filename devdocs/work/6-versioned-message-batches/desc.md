---
model: unknown
effort: unknown
---

# Stable, versioned message batches — issue #6

> Warmth: this session read the full codebase during #5/#9, then reviewed and
> verified the merged runtime at `d39a4df`. For #6 it refreshed record/export,
> iterator, download and identity code and completed the task-local traverse
> (`traverse/finding.md`, `c7f7e1e`). Triage is feature-heavy. The historical
> `devdocs/scoped/6` date-range fix is unrelated.

Source: GitHub #6 and the user's task-impl request. **Target SDK: Telethon
1.45.0**, per the user's explicit correction; no further 1.33.1 work.

## Problem Statement

Incremental reads currently return a presentation DataFrame with no fixed wire
schema, batch identity or explicit next cursor. Presentation can omit a message
whose sender is unresolved, so wrapping that result does not create a faithful
raw batch. Existing downloaded filenames identify a chat/message rather than
the bytes, preventing straightforward content deduplication across deliveries.

## User Value Proposition

A caller asks for a bounded sequence after a message ID, receives a versioned
snapshot with an explicit continuation, and can persist and resend that exact
snapshot after an upload failure. Requested media files have verifiable content
names. A later processor or #10 worker can consume the documented format without
depending on DataFrame internals or Telethon's changing generated object schema.

## Success Criteria

1. **Additive API.** A new `TgData.get_message_batch(...)` returns a public
   `MessageBatch` value. Existing DataFrame/callback/media APIs keep their
   current successful behavior and filenames.
2. **Explicit v1 contract.** Document exact JSON fields, types, nullable values,
   identity and version acceptance. Preserve message IDs/text/dates, available
   sender data, reply/forward/grouping references and media references. Keep
   normal and service messages even when sender metadata is missing. Do not
   serialize arbitrary SDK objects, credentials or access/file-reference tokens.
3. **Safe continuation.** Read one resolved group/channel oldest-first after an
   exclusive ID. The next cursor advances only after a message and its requested
   media are fully prepared. Empty output retains the input cursor. Reaching a
   count is distinct from observing end-of-history; neither requires a speculative
   extra read or completing an album beyond the requested bound.
4. **Replay identity.** The same finalized payload has the same identity and
   canonical JSON across output directories. Save/load preserves it; unsupported
   versions, malformed values and identity mismatches are rejected. Mutating a
   dictionary returned to the caller does not mutate the original batch value.
5. **Content-addressed media.** Optional downloads of supported photo/document
   attachments stream to temporary files, publish only after completion under
   SHA-256 names, and verify existing objects before reuse. Equal bytes from
   different messages share a file; changed bytes get a different name. Failed
   or cancelled preparation leaves no partial object under a final digest name.
6. **Recoverable interruptions.** Budget, Telegram, network, serialization and
   file failures remain errors. Once the source is resolved, ordinary exceptions
   carry the completely prepared prefix as `partial_result`, with a safe cursor.
   Cancellation cleans temporary files and never advances an external cursor.
   No Telegram health verdict is invented for a local format/media error.
7. **Existing account controls.** All message reads and implicit re-fetches use
   the shared client factory and #9 budget guard. A batch does not introduce a
   second transport/account lifecycle or spend unmetered message quota.
8. **Offline evidence.** Verify normative schema examples, exact large IDs,
   saved-output replay, cursor/failure cases, media integrity/concurrency and
   integration using real Telethon 1.45.0 control flow with synthetic transport.
   Run the supported offline regressions with live checks disabled.

## Scope Boundaries

- [ASSUMPTION] “Raw” means an explicit unprocessed projection of the requested
  fields, not a complete Telegram protocol archive. Missing sender metadata
  remains nullable; no per-message enrichment lookup is required. Deleted/
  inaccessible messages and SDK-filtered empty placeholders are not reconstructed.
- [ASSUMPTION] Default mode supplies references. Passing a media directory
  requests content files for supported attachments. Other attachment kinds
  retain metadata; the exact supported set is part of the v1 specification.
- [ASSUMPTION] One call is a finite oldest-first unit after an ID, without the
  legacy reader's date/search/callback options. The caller owns its persistent
  cursor, upload and acknowledgment. No worker, receiver, queue or exactly-once
  database transaction is implemented here.
- Saved-output replay is guaranteed by identity/serialization. A fresh Telegram
  read may observe edits/deletions or changed metadata; equal query arguments
  do not guarantee identical newly fetched bytes.
- No edits/deletion event stream, full-history snapshot isolation, automatic
  album completion, media garbage collector, remote object-store backend,
  new proxy/login behavior or session-store changes.
- The target is the user's Telethon 1.45.0 environment. Live Telegram behavior,
  deployment-volume durability and the future receiver are not established by
  offline probes. Merge/deployment remain separate review/authorization stages.

## Priority Level

**Medium — P2.** #10's future worker needs this reader/processor boundary. #9
budgets, #5 sessions and #4 health reporting are already integrated; #7 group
operations and #8 login are related but do not block this contract.

## Known Blockers

None open for local planning/implementation. Real pre-build probes confirmed
SDK raw-message preservation and writing to supplied file objects, plus the
local filesystem publication primitive. Exact fields and limits are local
design decisions to make explicit in the plan and attack with critic-d.
Exact model/effort metadata remain unavailable and are recorded as unknown;
no claim of CONTRIBUTING §9 model compliance is made.
