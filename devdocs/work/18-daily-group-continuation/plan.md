---
model: gpt-6-astra
effort: max
---

# #18 — daily continuation implementation plan, revision 1

Inputs: desc.md; traverse/finding.md; triage.md; probe_components.py; merged base
45bab7172621f576fa5e4b3265f87ec20da04fd5. This is the daily first delivery only.

### What is the task

Let a daily caller reopen per-group progress, prepare or replay one stable batch,
and acknowledge durable destination acceptance. Keep accepted progress separate
from unfinished output, use existing Telegram reads, and survive process restarts
without taking over scheduling, accounts or downstream storage.

### Huge Hard Blockers

#### Planning Blockers
None identified. The user fixed single-reader scope and permanent edit/deletion
exclusion; explicit caller acknowledgment needs no knowledge of a deployed receiver.
Canonical numeric enrollment and explicit initial position remove an implicit
identity/start-policy decision. Real SQLite process-exit/CAS and actual SDK/batch
probes passed before this plan. A custom store is a documented contract; its future
implementation is not claimed to be covered by the SQLite tests.

#### Execution Blockers
None for implementation/offline verification. Live Telegram and a deployed receiver
are outside this run. Merging requires a later user go-ahead. #7 stays paused.

### How this implementation moves toward desired state

Define one validated continuation state and an atomic storage protocol. Compose it
with get_message_batch in a separate internal engine, then expose four additive
facade methods. Exercise the real public path, SQLite and failure windows, and
document caller acceptance with a runnable local example. Existing batch v1 and
legacy methods are unchanged.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Validated state and SQLite store | sync_store.py, errors/status, async backend protocol |
| 2 | Preparation/replay/acknowledgment engine | sync_engine.py around the current batch API |
| 3 | Additive public API | optional sync_store and four TgData methods; exports |
| 4 | Offline contract and failure coverage | test_22_daily_continuation.py using real SDK/SQLite |
| 5 | Public contract and receiver example | README, daily-continuation docs, runnable example |
| 6 | Verify and commit | complete offline receipt and separate code/work commits |

## Contract fixed before implementation

Public async methods:

```python
await tg.initialize_sync(chat_id, *, after_id, media_mode="references")
await tg.sync_group(chat_id, *, limit=200, download_media_to=None)
await tg.acknowledge_sync(chat_id, batch_id)
await tg.get_sync_status(chat_id)
```

The first, third and fourth perform only storage work. initialize and acknowledge
return SyncStatus; status returns SyncStatus or None when unenrolled. sync_group
returns a nonempty MessageBatch or None. All require a configured sync_store.
chat_id is a non-boolean integer, negative and within signed64 range, using the
canonical marked ID from MessageBatch. Strings/handles and positive IDs are
refused. after_id is an integer0..2**31-1; limit is integer1..10000. Normal integer
protocol values such as numpy integers can be normalized with operator.index.

State fields are exactly version=1, chat_id, initial_after_id, after_id, media_mode,
pending and last_acked_batch_id. IDs use canonical decimal strings in serialized
state, as in batch v1. pending is null or the complete nested batch document.
Unknown/missing/duplicate keys, nonfinite values, malformed types, unsupported
versions and invalid UTF-8 are rejected. State is opaque text to the backend.

State invariants: after_id >= initial_after_id; both within message-ID bounds;
mode is references or download; pending is nonempty, matches chat_id/mode and
starts at exactly after_id; its validated next_after_id advances; last ack is null
or a lowercase64hex batch ID. An advanced position must have an acknowledgment;
an initial position must not claim a past acknowledgment. Pending ID cannot equal
the last acknowledged ID. Loading never repairs corrupt state.

SyncStatus is immutable and contains chat_id, initial_after_id, after_id, media_mode,
pending_batch_id, pending_message_count, pending_next_after_id and last_acked_batch_id.
to_dict is JSON-ready, using string IDs and ordinary counts. It contains no pending
message content or credentials.

Exceptions: SyncError base; SyncConfigurationError; SyncNotInitializedError
(configuration subtype); SyncConflictError; SyncStorageError. Local bases suppress
incidental RPC context. Each can carry read_error=None by default; only failure
persisting an interrupted prefix attaches the original read error there. No logging
of stored JSON, file paths, credentials or exception text is introduced.

## Step 1 — Implement state validation and storage

### Proposed changes

Create tgdata/sync_store.py. It owns the error/status types and internal state
encoding/validation helpers. Reuse MessageBatch validation for nested pending data;
do not change the batch envelope or duplicate its complete record validator.

The duck-typed backend protocol has two asynchronous methods:

```python
async def load(chat_id) -> str_or_none: ...
async def compare_and_swap(chat_id, expected_text_or_none, new_text) -> bool: ...
```

load returns None only for an absent key and raises on failure. compare_and_swap
atomically compares the exact current text (None means absent) and durably writes
new_text if equal, returning True; mismatch returns False without mutation. There
is no delete/reset operation. The engine checks returned value types and wraps
backend failures as local SyncStorageError with error type only. asyncio cancellation
propagates rather than becoming a storage error, including Python3.7's hierarchy.

SQLiteSyncStore(path) requires a persistent filesystem path, not :memory: or a
URI connection string. Resolve/expand it; parent directory must already exist.
Use namespaced tgdata_sync_meta(id=1, version=1) and
tgdata_sync_state(chat_id INTEGER PRIMARY KEY, data TEXT NOT NULL) tables. Existing
unrelated tables remain untouched. Initialization refuses partially missing or
unsupported sync schema instead of stamping an old table as new. Non-initialization
operations open with SQLite URI mode=rw, so a deleted DB cannot silently reappear.

Use short-lived connections and synchronous transactions inside async methods;
document the five-second SQLite busy timeout and local-I/O behavior. For conditional
writes use BEGIN IMMEDIATE, exact SELECT comparison, INSERT or UPDATE, then commit.
No database transaction crosses an await. Enable normal durable synchronous mode;
do not rely on a write-behind task. Loads verify schema each time. Convert SQLite
failures to sanitized SyncStorageError, preserving an active failure if rollback
or close also fails. A close-only failure remains visible; its preceding commit
may have succeeded, so retry/reload remains necessary.

### Output
An importable backend and shared state validator with no Telegram dependency beyond
the existing batch value's validation/import chain.

### Safe in nature
True — new module and namespaced tables; no existing runtime path invokes it yet.

### Peripheral concepts
MessageBatch format, exact integer IDs, SQLite transactions/durability, local error
provenance, pending content privacy, custom async storage.

### Hardness Lvl
4

## Step 2 — Compose bounded preparation with durable state

### Proposed changes

Create tgdata/sync_engine.py with an internal SyncEngine holding a callable for
the facade's existing get_message_batch and the selected store. It owns all state
transitions; the store never calls Telegram or interprets acknowledgment.

Enrollment: validate input before mutation, load current state. If present, matching
initial_after_id and media_mode returns its current status; mismatch raises
SyncConflictError. If absent, conditionally create ready state at the explicit seed.
A lost create acknowledgment can be retried idempotently; a real CAS mismatch
raises visibly and can be retried by the single caller.

Preparation: validate canonical chat, limit and any requested media path before
network work. Refuse an uninitialized chat. For reference mode, a download directory
is a conflicting option; for download mode require an explicit usable directory.
Use a per-engine in-flight set to reject overlapping sync_group calls for the same
chat, releasing it in finally. Different groups are not serialized together.

If pending exists, reconstruct its immutable MessageBatch. For download mode,
verify each distinct referenced blob under the current directory with the existing
regular-file/hash/size verifier; use the stored blob basename, never original file
metadata as a path. Return the same canonical batch without invoking the reader.
Pending existence is determined by validated persisted state, not a memory cache.

If ready, call get_message_batch(chat_id, after_id=accepted, limit=limit,
download_media_to=validated_directory_or_none). Validate the returned batch against
the selected source, cursor and mode. Empty/end output returns None, leaving state
ready and the cursor unchanged. Nonempty output is installed as pending with exact
expected-state replacement before returning. A conflict never overwrites another
pending observation. No automatic next read, sleep or cursor advancement occurs.

For an ordinary read exception, inspect its partial_result. If it is a nonempty
MessageBatch, validate and persist it using the same path. On success, re-raise the
identical original exception with its existing partial_result; the caller may now
deliver/ack that prefix or replay it later. Empty/absent prefix re-raises unchanged.
If validation or persistence fails, raise the local SyncError and attach the original
exception as read_error, with suppressed implicit context. Do not claim durable
pending output. Cancellation bypasses prefix publication and acknowledgment;
already committed state is never rolled back based on cancellation guesses.

Acknowledgment: validate ID syntax and load state. If ID equals last_acked_batch_id,
return current status without changing even a newer pending batch. Otherwise require
that exact pending ID, advance to its validated next_after_id, clear pending, set
last ack, and conditionally replace the whole state. Wrong/stale/absent IDs raise
SyncConflictError without mutation. Read-back/status exposes uncertain commit
outcomes. No caller-supplied cursor is accepted here.

Status: load and validate one state snapshot, return immutable public metadata;
None means no enrollment, never failed storage. None of these local paths emits
health events or changes TgData.current_group.

### Output
The ready/pending/acknowledged transitions are owned by one module and compose with
both complete and interrupted batch results.

### Safe in nature
True — new engine; existing batch semantics remain unchanged.

### Peripheral concepts
Async cancellation, exact batch identity, file verification, read budgets,
conditional updates, duplicate acknowledgment and exception precedence.

### Hardness Lvl
5

## Step 3 — Expose the additive public API

### Proposed changes

Append sync_store=None to TgData.__init__, instantiate the internal SyncEngine with
the bound public batch method, and add the four async methods listed above. Do not
decorate store/replay operations with _reported: actual fetch delegates to the
already-decorated get_message_batch, retaining truthful network evidence and current
health call naming. An omitted store leaves existing methods unchanged and new
sync methods raise SyncConfigurationError.

Export SQLiteSyncStore, SyncStatus and the five error classes from tgdata/__init__.py.
Keep public signatures/docstrings precise about canonical IDs, initialization,
no automatic acceptance and the single-reader condition. No connection-engine,
health-ledger, budget/session schema or dependency change is required.

### Output
Daily callers can use the feature through TgData with a local or custom backend.

### Safe in nature
False — modifies the common facade and exports; compatibility suites required.

### Peripheral concepts
Constructor compatibility, package imports/cycles, public health decoration,
existing engine delegation and Python3.7 syntax.

### Hardness Lvl
3

## Step 4 — Add meaningful offline regressions

### Proposed changes

Add tgdata/smoke_tests/test_22_daily_continuation.py. Number22 avoids the unmerged
#7 test20 and its proposed test21. Reuse synthetic transport helpers from tests18/19
while running the actual public facade, Telethon iterator, budget guard, state
validator and SQLite backend. Block sockets. Use temporary files and synthetic IDs.

Required behavioral groups:
- omitted-store compatibility; explicit enrollment; invalid types/ranges/modes;
  idempotent enrollment versus forbidden reset; missing state versus store failure;
- successive daily batches, gaps in IDs, empty results and maximum cursor;
  several missed days represented by continued IDs, not host-date filtering;
- prepare leaves accepted cursor unchanged; reconstructed instance replays identical
  bytes without any client creation or budget request;
- exact acknowledgment, latest repeated ack, older/wrong/malformed ack, latest ack
  during newer pending state; atomic source/cursor/mode checks;
- real SQLite reopen/rollback, unsupported/missing/partial schema, missing DB,
  corrupt JSON/hash/types, large signed IDs, conditional write conflict;
- process exit before state commit and after commit; receiver acceptance followed
  by lost acknowledgment, restart and one destination effect;
- actual budget-exhausted prefix is durably replayable; original RPC/network object
  retained after successful prefix save; no-prefix failures leave no pending;
  a failed prefix save exposes both the local failure and original read_error;
- cancellation during actual pending SDK request and during custom async store
  access; no fabricated progress or held in-flight guard;
- real overlap barrier for duplicate same-instance preparation (second is rejected);
  returned different group/wrong start/mode cannot publish;
- custom asynchronous backend contract, boolean CAS return validation, backend
  failures inside incidental Telegram error context never becoming health verdicts;
- real optional media preparation, offline replay at another root with copied blobs,
  missing/corrupt/symlink blob refusal, stable media policy and no automatic cleanup;
- snapshot immutability/JSON form, independent groups, no current_group change,
  no repeated health event or false recovery from local replay/ack/status;
- SQLite rollback/close failure precedence and bounded type-only diagnostics.

Include a backend contract exercise reusable for SQLite and an independent in-memory
async implementation, without treating the latter as persistence evidence.

### Output
Behavior-based regressions cover public composition and durable failure boundaries.

### Safe in nature
True — offline tests only, no real account or network mutation.

### Peripheral concepts
Real SDK fixtures, SQLite process exits, persisted receiver deduplication, scheduling
barriers, immutable JSON and existing local-I/O helpers.

### Hardness Lvl
5

## Step 5 — Document and demonstrate daily use

### Proposed changes

Add docs/daily_continuation.md with store protocol, exact state/ack semantics,
canonical-ID acquisition, initial checkpoint import, pending-first retry, partial
errors, media retention, one-reader boundary and sequential relocation obligations.
Explain that receiver acceptance/effects and dedup markers must commit together,
and that batch IDs alone do not deduplicate overlapping messages.

Add a README feature/usage section beside stable batches, plus a smoke-test entry.
Add examples/daily_continuation.py with a small SQLite destination keyed by batch ID
and (chat_id,message_id), committing acceptance before acknowledge_sync. Provide an
offline --demo that uses explicitly synthetic MessageBatch inputs, demonstrates a
lost acknowledgment and restart, and writes only to an explicit or temporary demo
directory. Normal use receives the user's config/group/initial checkpoint and
bounded batch count; no cron loop, UI, upload service or live test runs here.

Document reference-only first use and optional media separately. Do not imply the
sample receiver proves a deployed receiver's guarantees. #18 backfill remains
pending, and no edit/deletion reconciliation is suggested as future scope.

### Output
A caller can run a correct daily collection loop and understand its failure limits.

### Safe in nature
True — docs/example additions; the example only contacts Telegram when explicitly
invoked in normal mode by its user.

### Peripheral concepts
SQLite destination transactions, receiver idempotency, existing batch docs,
daily invocation and initial checkpoint migration.

### Hardness Lvl
3

## Step 6 — Verify, commit and update the first-delivery record

### Proposed changes

Compile changed modules and check Python3.7 grammar. Run the new suite and example
demo, then supported offline tests12–19 and the two pure discovery helpers on
Telethon1.45.0 using the existing .venv Python3.11.10 from the isolated checkout.
Use a nonexistent config for12/13 to skip their three live checks. Do not run the
live legacy smoke scripts or 1.33.1. Verify imports resolve to this worktree.

Small local corrections are recorded; architectural failure returns to the plan
under the task-impl gate. Check whitespace/diff/staging. Commit source/tests/public
docs/example together, work-folder verification notes separately. Push the feature
branch and update #18's first-delivery checklist without closing its backfill scope.
Merge check/PR/fresh PR critic remain subsequent gates; merging is not authorized.
Keep all #7 state and duncan untouched in the original checkout.

### Output
Implemented daily continuation with a reproducible verification receipt and reviewable
commits, ready for the later merge gates.

### Safe in nature
False — publishes feature code and records; no deployment or merge occurs.

### Peripheral concepts
Worktree isolation, offline/live distinction, commit separation, issue scope and
archive-only work documents.

### Hardness Lvl
3
