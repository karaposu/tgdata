---
model: gpt-6-astra
effort: max
revision: 2
---
# Stage 7 — public lifecycle and durable caller example

**Critic folded:** 2026-10-07 — 1 robust mitigation, 2 steps changed, 0 added.
The required real SQLite/receiver experiment ran before Step 1 and PASSED all seven
checks on unchanged production code. See [critic](critic.md) and [probe](prebuild-results.json).

Baseline `5b51cc3`, product `0d6bb26`; description `2379017`. Gate C PASS is the
entry requirement. No PARKED marker/rejected PR critic exists. Model/effort verified
gpt-6-astra/max; same-session warmth and completed lifecycle inquiry retained.

### What is the task

Make the reviewed lifecycle usable through TgData while preserving its exact
authority, timing, storage and health boundaries. Publish the existing typed contract
and demonstrate the caller's real durable acceptance, request retention and sequential
daily/history scheduling. Do not move scheduling or receiver ownership into the library.

### Huge Hard Blockers

#### Planning Blockers

None identified. The operation names, typed inputs, outcomes and state semantics are
settled by the contract and Gate C. The facade can delegate to persistent existing
engines without another state machine. The example's namespaced SQLite composition
is an executable local premise, not a missing human decision or vendor capability.

#### Execution Blockers

None. This stage needs only local temporary SQLite, synthetic source observations and
the supported offline tests. Existing live resources/ledger remain untouched; mandatory
public/live Gate D belongs after Stage 8, not to this scoped Stage 7 implementation.

### How this implementation moves toward desired state

Keep all lifecycle transitions in BackfillEngine and all source health reporting in
the existing get_message_batch boundary. Add a small facade that retains engine
instances for the TgData lifetime, and public exports of the already validated values.
An application-owned example uses real atomic storage and receiver commits, while
synthetic source values remain explicitly synthetic. Tests verify public composition
and prevent incidental local operations from pretending to contact Telegram.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Add configuration, stable delegation and exports | Six public methods; existing engine/value semantics |
| 2 | Test the public boundary and legacy compatibility | test_29 plus intentional staged-availability updates |
| 3 | Build a durable offline caller/receiver example | Separate logical namespaces, owned restart and exact replay |
| 4 | Publish public contract and usage | docs/backfill_runs.md, README and smoke-test discovery |
| 5 | Verify scoped and full supported behavior | Compile/grammar, new suite/example, full regression results |
| 6 | Commit and publish the scoped handoff | Separate product/work commits, branch push, #19 Stage 7 status |

## Public API and lifetime decisions

Append `backfill_store=None` to TgData.__init__, after existing sync_store, preserving
every existing positional/default argument. Keep constructor/config/client behavior
unchanged. Store the backend privately and initialize an empty private engine cache;
do not open the backend, config, session or source from this addition.

Expose exactly:

```python
await tg.start_backfill(start_request, *, submission)
await tg.get_backfill_status(run)
await tg.prepare_backfill(context, *, download_media_to=None)
await tg.acknowledge_backfill(delivery)
await tg.control_backfill(run, *, command_id, expected_control_revision, action)
await tg.recover_backfill(run, *, attempt_id, command_id,
                          expected_control_revision, previous_reader_stopped)
```

Method signatures carry typed immutable objects, not bare hashes or unvalidated dicts.
The arguments retain the internal required/optional distinctions. No request context
is fetched or rebased for the caller. No exception is swallowed/reclassified. Results
are the existing owned StartResult/Status/Turn/ControlResult/RecoveryResult.

A private synchronous helper validates/reconstructs the expected address type using
its existing from_dict/to_dict contract, obtains collection_id from that owned value,
requires a configured backfill_store, and returns `(engine, owned_address)`. It creates
one BackfillEngine per collection only once, using the configured backend and the
existing bound `self.get_message_batch` callback. All six methods use it, so prepare,
control and recover share the same local activity/end/wait evidence. No await occurs
between cache lookup/creation. The cache is retained through close/reconnect; the
existing close method still only closes connections. No eviction discards live timing.
Cache memory is proportional to collection IDs explicitly used by the application.

Collection IDs **do not automatically partition the backend**. backfill_store is the
same configured isolated namespace for that facade, not a resolver/factory. Wrong
stored collection/kind refuses through the existing strict codec; passing another
collection ID does not move its row or select a different database. Use independently
configured namespaces/facades for simultaneous collections. A custom application may
put those namespaces in one physical database. The cache is only engine lifetime
management, not storage routing. No new constructor collection parameter or production
namespace framework is needed. No fallback to sync_store.

None of these six facade methods uses `_reported` or opens another health context.
The captured actual get_message_batch callback already owns the source context. Local
success/error/cancellation/replay cannot clear an existing Telegram failure; local
prefix-persistence failures keep the actual read error separately as today. New facade
validation errors name expected types/configuration, never supplied credentials/data.

Export the nine existing public values from package root: BackfillRunRef,
BackfillStartRequest, BackfillPrepareContext, BackfillDeliveryRef, BackfillStatus,
BackfillStartResult, BackfillTurn, BackfillControlResult, BackfillRecoveryResult.
Export the eleven local errors: BackfillError, BackfillConfigurationError,
BackfillConflictError, BackfillUnknownRun, BackfillUnknownCommand, BackfillStateError,
BackfillStorageError, BackfillUnknownReceipt, BackfillRecoveryRequired,
BackfillMediaError, BackfillClockError. Keep BackfillEngine, _BackfillState and helper
functions internal. Do not change package version, dependency range or runtime support
claims in this stage; the verified SDK is 1.45.0 and actual runtime is 3.11.10.

## Example decisions: application storage, not another library service

Add a bounded **offline-only** `examples/backfill_runs.py`. Default help performs no
work. `--demo` uses a fresh temporary directory. For retained files, require explicit
`--demo --directory PATH --new` for first provisioning; without --new reopen known
state and refuse missing/incomplete data. Never decide that missing known history is
permission to start over. Refuse --new if its known database already exists.

Use one application SQLite database with separate fixed application tables:

- progress keyed by `(namespace, chat_id)`, storing opaque text. A small example-owned
  NamespaceStore implements async load/compare_and_swap through short real transactions;
- retained application request/reference/command records, committed before submission;
- accepted receipts keyed by complete backfill DeliveryRef (canonical JSON), each
  retaining the full canonical batch snapshot in the same transaction, and
  deduplicated messages keyed by group/message ID. Daily receipt keys include a distinct
  daily namespace, source and batch hash so they cannot alias a backfill receipt.

Validate destination, chat and hash before receiver acceptance. Duplicate receipt
keys must match the complete stored batch exactly or refuse. The unique message table
is a first-observation index; each receipt retains its exact observation even when
an overlapping delivery differs. This does not implement edit reconciliation.

Application database setup is explicit, operations reopen with SQLite `mode=rw`, and
transactions use synchronous=FULL plus BEGIN IMMEDIATE for compare/write. No connection
or database lock spans an await/source call. Use exact parameterized text comparison
under one write transaction for CAS. Rollback/close must preserve a primary error;
do not turn a committed-then-close-error into assumed rollback. Example schema/identity
records are application-owned and never part of the library's opaque state format.
The example is not a schema migration system, remote database adapter or power-loss
certification. Test actual SQLite behavior rather than an in-memory dictionary.

The synthetic reader is a TgData subclass overriding only get_message_batch and
returning valid public MessageBatch objects for a fixed small known dataset. Honor
cursor/window/limit and return limit versus actual end distinctly. It does not claim
SDK/network qualification. All example worker sockets are blocked and no real config,
login, budget or session is read. Choose explicit pause_seconds=0 for the quick demo;
documentation separately demonstrates caller-scheduled waits with a real nonzero policy.

Keep four historical records in a closed window and one newer daily record. Enroll daily
at the explicit known origin preceding that newer record. The parent launches an owned
first worker; it persists intent before start and the complete returned RunRef, prepares
one historical batch, commits actual receiver receipt/data, then deliberately exits
before library acknowledgment. Parent waits for the exact expected exit and reopens in
a fresh worker. Pending replay must produce the same canonical bytes/full receipt with
zero synthetic source calls. Duplicate receiver acceptance has no repeated row effect.

The resumed caller records a pause command, replays/delivers/acknowledges while paused,
then records resume and deliberately obtains current contexts for new turns. Between
historical turns it may execute one daily turn; every source read is sequential and
each collection's cursor stays independent. Stop/return a wait instead of sleeping in
the library. Finish history only after an actual empty/final end and durable acceptance.
After completion, create a deliberate separate successor that is cancelled without
source work, illustrating terminal cancellation without rewriting completed history.

Persist any example control request before submission, with its original expected
revision. Retried saved commands keep that context; conflict/unknown stops instead of
rewriting it. Unknown attempts also stop; the example never asserts worker death and
automatically recovers arbitrary work. It demonstrates only its specified receiver-
before-ack interruption. On a repeated completed demo, verify the saved outcomes and
unique receiver set with zero new source reads; do not repeat forgotten old commands.
Print small status/count summaries, no message bodies, credentials or raw source errors.

## Step 1 — Additive public facade and exports

### Proposed changes

Modify `tgdata/tgdata.py` and `tgdata/__init__.py` according to the signatures/cache/
exports above. Validate and own addresses before cache selection. Delegate each call
once to the existing method; preserve required submission/action/recovery parameters.
No new state transition, backend selection policy, health wrapper or current_group
mutation. Missing backfill_store raises BackfillConfigurationError on use, locally.
Update stale internal staged-availability docstrings where they would now be false.

### Output

Public typed operations over stable internal engine instances, disabled by default.

### Safe in nature

False — changes the existing public class and package import surface.

### Peripheral concepts

Constructor compatibility, exact addresses, engine lifetime, callback capture, health.

### Hardness Lvl

3/5.

## Step 2 — Public composition tests

### Proposed changes

Add `tgdata/smoke_tests/test_29_backfill_public.py` using real SQLite and existing actual
Telethon 1.45.0 transport fixtures, with sockets forbidden. Exercise:

1. Root exports, immutable/portable values, unchanged old constructor positions and
   default raw/daily behavior; absent/malformed backend/address refuses before config.
2. Public fresh/retry start, missing/pruned context, explicit scope, exact receipt,
   pending replay/final ack, both terminal orders, control/recovery required arguments.
3. Same engine across every facade operation: overlapping prepare refuses, controls
   preserve late actual SDK result; busy recovery/abandonment refuses; clock minimums
   survive status/ack/control/close calls. Independent deterministic clocks are test
   injections into the existing engine, not a new public clock-setting API.
4. Source errors are reported once through get_message_batch; local create/status/
   replay/ack/control/recovery and store/media failures emit no events and preserve a
   prior no-access/wait snapshot. A saved typed source error remains historical evidence.
5. Status/result/log serialization excludes message text/sender metadata/credential
   sentinels, while retaining documented identifiers and independent state dimensions.
6. Real budget prefix and store-failure provenance, cancellation, no-send ambiguous
   admission, committed lost reply and exactly scoped restart recognition through facade.
7. Separate daily/backfill stores preserve independent progress; deliberately reusing
   one namespace or addressing another collection refuses without state replacement.

Update only deliberately staged public-absence assertions in tests 24/25/28 to the
planned public availability. Keep any assertions that internal engines/codecs/helpers
are not package-root APIs. Do not weaken old state/receipt/health expectations.

### Output

Focused public-boundary evidence; the existing internal suites continue to cover the
full state-machine matrix without mechanically duplicating every internal assertion.

### Safe in nature

True — isolated tests and intentional stage-availability changes only.

### Peripheral concepts

Actual SDK fixtures, local health isolation, source guards, status redaction, namespace.

### Hardness Lvl

4/5.

## Step 3 — Durable offline application example [folded: Risk 1, robust]

### Proposed changes

Implement the example design above. Qualify its real SQLite namespace/CAS/receiver
primitive before depending on it if the critic requires a prebuild experiment; carry
the tested design into the example rather than replacing it with a fake after proof.
Add example tests (in test29 or a focused example section) for the actual two-process
lost-ack run, exact replay/receipt dedup, independent progress, completed repeat with
no source work, and refusal of missing known database/intent or duplicate --new.
Use explicit fixed expected IDs/statuses/counts independent of implementation counters.
Carry the qualified prebuild_store.py database/namespace/receiver design into this
example, adapting public imports only. Test complete snapshots for differing valid
observations of the same message ID, exact duplicate acceptance and wrong receiver
chat/destination/hash refusal. No marker may stand in for the accepted batch snapshot.

### Output

Runnable help/offline demo, optional retained directory, real durable acceptance and
caller identity records, no Telegram calls and no automatic arbitrary recovery.

### Safe in nature

True — new isolated opt-in offline example; explicitly selected new files only.

### Peripheral concepts

SQLite durability/CAS, full receipt keys, app manifest, process exit, daily/history scope.

### Hardness Lvl

4/5.

## Step 4 — Public documentation and discovery [folded: Risk 1, robust]

### Proposed changes

Add `docs/backfill_runs.md` with one practical public flow, the six-method/result/error
reference, explicit first use versus restart, receiver commit/receipt requirements,
partial-failure replay via saved delivery (not a bare partial hash), source end versus
acceptance, pause/cancel/abandonment, exact recovery and worker lifetime, timing/account
restrictions, portable identity and bounded historical recognition. Explain the example receiver's full snapshot-per-receipt storage separately from its
first-observation message index; neither implies edit reconciliation. Define stored status
fields without percentages, ready flags or fresh account/health claims. Explain that
IDs/labels are caller supplied and must not contain secrets; status excludes message
content, while pending storage intentionally contains the batch needed for replay.

Document backfill_store as one caller-isolated load/CAS namespace, no automatic routing
by collection_id, SQLiteSyncStore's separate-file convenience and the example's custom
same-database namespaces. State synchronous local SQLite/hash work must remain bounded.
Keep the application responsible for scheduling, accounts, worker quiescence, receiver
durability and sequential movement. No exactly-once external processing claim.

Add a README section after fixed historical windows, link the demo/smoke suite, and
update `docs/backfill_state.md` to direct public users to the new contract while retaining
internal evidence details. Update work-folder contract/status/assumptions/matrix only
for scoped Stage 7 evidence. Gate D stays pending; A/B/C retain their exact revisions.

### Output

Discoverable public API with a clear caller boundary and reproducible offline example.

### Safe in nature

True — documentation reflects tested behavior; no package release or live action.

### Peripheral concepts

User-facing status semantics, source versus receiver evidence, namespace ownership.

### Hardness Lvl

3/5.

## Step 5 — Scoped and full verification

### Proposed changes

Compile; run test29 and the example fresh/reopen modes, then the existing supported
suite 28 through 11 (explicitly await test11's two offline helpers), daily demo and
ten live-guard instrument checks. Preserve three legacy live skips rather than count
them as executed. Run Python 3.7 grammar checks separately from actual 3.11.10 runtime.
Check public imports, signatures, changed-document links, diff scope and credentials.

No new Telegram connection or live budget mutation. Gate D follows Stage 8. Record
every initial failure and small nonarchitectural correction; stop for structural
failure, never change behavior expectations to make the result pass.

### Output

Reproducible verification/results and explicit remaining public/live validation limits.

### Safe in nature

True — offline fixtures; loopback-only proxy tests may need sandbox permission.

### Peripheral concepts

Supported SDK/runtime, package imports, legacy callers, actual durable primitives.

### Hardness Lvl

3/5.

## Step 6 — Commit, push and scoped status

### Proposed changes

Record implementation and verification. Commit product code/tests/public docs/example
together, work-folder evidence separately; keep duncan/#7 and other worktrees untouched.
Push the existing feature branch and update #19 only after checkpoints exist remotely.
Preserve its original user request and near-limit issue body. Link detailed results in
a completion comment. Mark Stage 7/7.1–7.3 complete; leave Stage 8/Gate D and whole-feature
review/PR/merge pending. No package version bump, PR or merge in this scoped run.

### Output

Reviewable published Stage 7 checkpoint with Stage 8/Gate D as the next work.

### Safe in nature

True — feature-branch/evidence publication already authorized by task-impl.

### Peripheral concepts

Pipeline checkpoints, honest gate provenance, source privacy, branch archive.

### Hardness Lvl

2/5.
