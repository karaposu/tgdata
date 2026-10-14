---
model: gpt-6-astra
effort: xhigh
---
# Implementation plan — observed album assembly (#29), revision 2

**Critic folded:** 2026-10-14 — 1 selected robust mitigation (3 steps changed, 0 added). Combined prebuild PASS37/37 before step1; see critic.md and prebuild/report.md.

Canonical task-plan artifact. `plan.md` points here to preserve the repository's conventional entry point without maintaining duplicate plans. Input explicitly supplied: `devdocs/work/29-album-assembly/desc.md`. No prior PR rejection or deprecated plan exists.

### What is the task

Provide an opt-in pure operation that combines Telegram-marked album members across immutable raw batches into stable, lossless post observations. The caller retains prior posts and accepts each raw input durably before its existing source acknowledgment. The feature must work across restart/replay without pretending bounded observations prove complete albums or changing raw delivery, windows, budgets or pool behavior.

### Huge Hard Blockers

#### Planning Blockers

None identified. The two-iteration inquiry resolves ownership, uncertainty and recovery. The optional API preference is an explicit working assumption in desc.md; the independent assembler satisfies the qualified request. Current schema/SDK/source-engine and actual SQLite probes establish the available interfaces, not the new runtime. Unknown §9 model/effort metadata remains recorded for later review; no model certification is claimed.

#### Execution Blockers

None identified for this implementation. No live login, second account, external deployment or release is required by the observed-data promise. A combined real-component prebuild must qualify the candidate before production adoption; this is executable work, not an external blocker. Any future source-completeness promise needs separately qualified real Telegram evidence.

### How this implementation moves toward desired state

Keep source data and its receipts intact. Add one immutable versioned post value and two pure helper functions in a new module. Keep persistent acceptance in a small runnable SQLite example, where strict reopening and current-prior transaction semantics can be tested concretely. Export the public helpers, document their exact limits, and verify with actual SDK/value/storage/source-engine composition plus every existing offline suite.

### High-Level Summary

| Step | Description | Expected Output |
|---|---|---|
| 1 | Implement immutable post values and pure assembly | New `tgdata/album.py` and public exports |
| 2 | Demonstrate strict durable receiver acceptance | Runnable `examples/album_assembly.py` with offline restart demo |
| 3 | Add focused composition and refusal tests | `test_42_album_assembly.py` covering real SDK/value/SQLite/source engines |
| 4 | Document the observed-post and caller-storage contract | `docs/album_assembly.md`, README and smoke-test entry |
| 5 | Verify, commit and record status | Full offline regression evidence; separate product/work commits |

## Concrete contract shared by all steps

- Public names: `TelegramPost`, `AlbumAssemblyError`, `album_post_ids(batch, *, max_bytes=...)`, `assemble_albums(batch, *, previous, max_members=10000, max_bytes=16777216)`.
- `previous` is a Mapping with exactly the affected post IDs, each mapped to a TelegramPost or explicit None. No default mapping. Key selection returns a tuple in first occurrence order. Assembly returns a tuple of updated affected posts sorted by their first member ID, then post ID; it returns unchanged observations too so it is a predictable projection, not an emission/dedup service.
- Post schema `tgdata.telegram-post`, integer version1; exact fields `schema`, `version`, `post_id`, `revision`, `chat_id`, `grouped_id`, `media_mode`, `membership`, `members`. All source IDs remain canonical decimal strings. Identity text is `tg:<chat_id>:album:<grouped_id>` or `tg:<chat_id>:message:<message_id>`. Revision is lowercase SHA256 of canonical JSON excluding `revision`. It contains no batch IDs, cursors or collection identifiers, so equivalent observed members yield identical bytes regardless of delivery partition.
- Album membership=`unconfirmed`; singleton membership=`single`. Grouped members all agree with the envelope; an ungrouped post has exactly one member. Members strictly increase by ID and reuse existing raw-record validation. No caption synthesis or guessed finality.
- Frozen encoded value, copy-returning `to_dict()`/`members`, properties for identity/revision/chat/group/mode/membership and tuple member IDs; `to_json()` and `from_json()` with strict duplicate-field/nonfinite/UTF-8/schema/type/hash/identity checks. Constructors/loaders take the same adjustable member/byte limits. Error messages name the local problem without dumping content; no health event or log is emitted.
- Default10000 combined member records per operation and16MiB UTF-8 serialized payload budget. Byte accounting covers source batch + supplied non-None prior post JSON + output post JSON; check before decoding supplied values and incrementally before accumulating outputs. Loader bounds apply to its single serialized value. Member bounds cover total output union; duplicates count once in the output. Both limits must be positive plain integers; no arbitrary cap preventing a caller deliberately raising them. Refusal is all-or-nothing and never mutates prior/input. These are bounded work policies, not a hard process-RSS guarantee.
- A duplicate member must match the complete raw record exactly. Conflicting content or media mode refuses; no silent edit reconciliation. The helper sees only supplied prior identities and cannot detect an application's omitted or externally deleted historical data. Callers must treat authoritative storage as part of acceptance.
- Receiver example: explicit `create=True` registers a new named collection; default `create=False` requires an existing validated database and collection. New file creation is explicit and never a fallback on failed open/load. Existing partial/foreign schema refuses even in create mode. Collection selection scopes both posts and accepted-input markers. Repeated creation of an existing collection refuses.
- Receiver transaction: `BEGIN IMMEDIATE`, validate schema/version/collection, load current post JSON for all affected keys, assemble, save posts and marker, commit; then source acknowledgment outside the transaction. Accepted-input replay must find all incoming members already in current stored observations; missing/different accepted data raises rather than repairing it from the retried fragment. A fresh input can add members; an old retry cannot shrink a later union. Short synchronous local database operations only; no await or network under lock.
- Example accepts reference-only batches. Downloaded post values preserve blob references, but users must keep bytes durably themselves before source ack. No built-in blob deletion/copying policy.
- `collect` demonstrates only normal confirmed daily delivery: prepare → receiver.accept → acknowledge original batch ID. Exceptions/cancellation propagate without inferring receipt authority from partial_result. Backfill composition uses the original BackfillDeliveryRef in tests/docs. A failed delivery can be recovered through existing source APIs and then offered normally.

## Step 1 — Immutable observed posts and assembly

[folded: Risk 1, robust] Apply caller-selected limits to saved-value revalidation as well as output construction. Safe=False remains appropriate for public exports.

### Proposed changes

Add `tgdata/album.py`; reuse raw-record and canonical identifier/JSON validators without changing MessageBatch or its format. Normalize only record ordering, never member content. Reject wrong prior key/value/identity, duplicate conflicting IDs, mixed mode and malformed serialization using local AlbumAssemblyError. Revalidate public saved values, reject unsupported fields/types, hide message contents from repr/errors. Implement key selection and pure bounded union; empty batch requires an empty mapping and returns an empty tuple. Export four names from `tgdata/__init__.py`, preserving version0.1 and every existing export. If the required prebuild has produced the qualified candidate, adopt those exact module bytes.

### Output

Portable validated post observations and a deterministic core with no I/O, source callbacks, cursor, acknowledgment or internal cache.

### Safe in nature

False — new module is additive, but exports touch package import behavior and strict reuse of raw validators must remain compatible.

### Peripheral concepts

MessageBatch v1, canonical identifiers/JSON, raw media validation, package exports, immutable observations, source receipt distinction.

### Hardness Lvl

4

## Step 2 — Durable receiver example

[folded: Risk 1, robust] AlbumReceiver takes explicit max_members/max_bytes and passes them to every saved post load, assembly operation and readback. Reopening under a lower policy may refuse; restore an adequate policy, never reset data. Safe=True remains: only a new opt-in example changes.

### Proposed changes

Add `examples/album_assembly.py` with `AlbumReceiver`, isolated versioned schema, named collections, post JSON and input markers. Reopen through SQLite mode=rw, validate schema column types/nullability/primary keys and version/collection before lookup or writes. Explicit provisioning creates only a genuinely new schema; known partial schema refuses. Each accept opens/closes its connection, uses current prior state under one write transaction and commits data/marker together. Rollback/close must preserve the original error; a post-commit failure must not reset committed data. Provide readback for the offline demo and tests. Add a bounded daily collect helper using confirmed normal delivery only. The no-network CLI demo stores a split album, loses its raw ack, reopens both stores, replays and continues, then prints member/caption counts. No live CLI/login is required. Adopt qualified prebuild bytes if available.

### Output

A runnable example of caller-owned durable membership across restart and acknowledgment loss, with explicit open/create and source-data authority.

### Safe in nature

True — new opt-in example; touches no existing running destination or source code.

### Peripheral concepts

SQLite transactions/schema, SyncEngine receipts, BackfillDeliveryRef, post serialization, collection namespaces, content retention, cleanup precedence.

### Hardness Lvl

4

## Step 3 — Focused tests and combined evidence

[folded: Risk 1, robust] Include10001 members accumulated from valid bounded raw batches, accept→reopen→replay under a raised policy, then lower-policy refusal without a write; exact multibyte byte accounting also crosses the boundary. Safe=True remains: temporary offline data only.

### Proposed changes

Add `tgdata/smoke_tests/test_42_album_assembly.py`, independent of credentials and with socket connections forbidden. Use real Telethon1.45 TL serialization/deserialization and the actual raw `_record` serializer, actual MessageBatch/post candidate, actual SQLite receiver/SQLiteSyncStore, and actual SyncEngine/BackfillEngine. Scripted bounded source replies are fixtures; tests do not claim real server pagination/completeness.

Cover: split and nonadjacent albums; caption arriving last; all captions preserved; mixed singleton/service/media; exact large IDs and cross-chat separation; reverse arrival/partition-invariant bytes; immutable round-trip; duplicate/unknown/type/hash/schema/identity corruption; required mapping; conflict refusal; refs/download compatibility and preserved actual cached-photo blob bytes; byte/count boundaries including multibyte text; input/prior unchanged after every refusal; no raw hash/cursor mutation or extra reads.

Exercise durable histories: explicit new/reopen, missing file/schema/collection, corrupt post and failed lookup, whole-transaction rollback, real commit then lost response/reopen, stale competing writer retry, equal raw hash in separate collections, lost ack replay, replay after newer album growth, accepted marker with missing member refusal. Integrate daily pending replay and backfill pending delivery/ack including an album split by a fixed window. For cancellation/budget/source failure, preserve raw source behavior and unconfirmed observed membership; never manufacture a receipt from available partial data. Keep existing health callbacks uncalled on local refusal. Run the actual demo.

### Output

A bounded offline suite with observable results, no invented vendor guarantees, and failure/recovery checks of the actual new components.

### Safe in nature

True — additive offline tests and temporary databases.

### Peripheral concepts

SDK TL values, raw serialization, reference/download modes, daily/backfill receipt ownership, SQLite crash boundaries, cancellation, budgets, local health isolation.

### Hardness Lvl

4

## Step 4 — Public documentation

### Proposed changes

Add `docs/album_assembly.md` defining the post schema, keys, revision, required prior lookup, conflict/limits behavior and update semantics. Document transaction/current lookup/strict reopen, source receipt distinction, ref-only example and blob custody. Show an in-memory opt-in example and safe daily/backfill acceptance snippets. Explain that an exhausted bounded read does not finalize album membership; interrupted/captured data lacks automatic ack authority. Add a short README entry near raw batches/daily continuation and the suite42 entry to the smoke README. Link primary Telegram grouping/caption documentation and the executable demo; no extra dependencies or version change.

### Output

Usable public contract and discoverable tests/example.

### Safe in nature

True — documentation only.

### Peripheral concepts

Raw v1 schema, source receipts, caller persistence, media custody, stable observation revision, future optional photo trails.

### Hardness Lvl

2

## Step 5 — Verify and commit

### Proposed changes

Compile changed sources and check Python3.7 grammar (current runtime3.11.10, no native3.7 claim). Run suite42 plus raw19/daily22/fixed23/backfill24–30/pool31,39–40 focused checks, then every28 existing offline suite (12–19,22–41) and all five existing demos plus the new demo. Use missing config for12/13 live skips; loopback proxy checks need sandbox escalation, not Telegram access. Each subprocess has a watchdog; record counts/skips and source SHA256. Fix only local nonarchitectural errors per task-impl; structural failure halts. Confirm diff scope/version/original checkout unchanged. Commit product code/tests/docs separately from work-folder evidence, push the feature branch and update #29 through step5 only. Leave merge check, PR and fresh PR critique pending.

### Output

Verified feature commits and honest issue/evidence status, ready for the separately requested review gates.

### Safe in nature

True — verification uses temporary data, commits are isolated and reversible; no deployment or merge.

### Peripheral concepts

Regression suite, Python compatibility, offline sockets, baseline parity, Git worktrees, issue status, model metadata.

### Hardness Lvl

3

**Provenance verified retrospectively, 2026-10-14:** local active-thread turn records and matching commit outputs establish GPT 6 Astra / xhigh for this artifact. Earlier unknown/pending wording records what was known at the time; see [§9 verification](model-effort-verification.md).
