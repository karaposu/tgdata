# Backfill lifecycle — internal state and engine reference

This internal staged interface implements **start, status, prepare/replay,
acknowledge, explicit recovery and operator controls**, with durable per-run pacing. Preparation retains
one exact batch before returning it; acknowledgment
records the caller's durable acceptance. Completion and uncertain-write handling
are covered through Stage 4; Stage 5 adds positive timing and recovery.
Stage 6 adds pause/resume/cancel/abandon and safe succession. Stage 7 exposes these
operations and their typed values through TgData and package-root imports. Use
[Backfill runs](backfill_runs.md) for the public contract, configuration and example;
the internal engine paths below remain implementation/evidence reference.

The internal modules below support this staged delivery. The existing daily
and fixed-window APIs and MessageBatch v1 remain unchanged. Tests target Telethon 1.45.0.

## Create explicit intent locally

```python
from datetime import datetime, timezone
from tgdata import SQLiteSyncStore
from tgdata.backfill import BackfillStartRequest
from tgdata.backfill_engine import BackfillEngine

request = BackfillStartRequest(
    collection_id="archive-history", chat_id=-1001234567890,
    run_id="september-2026-first-run", destination_id="raw-archive",
    pause_seconds=240, expected_predecessor=None,
    start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
    end_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
)
store = SQLiteSyncStore("backfill-progress.sqlite3")
engine = BackfillEngine(store, "archive-history")
result = await engine.start(request, submission="new")
reference = result.status.run
print(reference.to_dict(), result.status.start_date, result.status.end_date)
```

These operations use only the chosen state backend. No account/config/session is
needed. The SQLite parent directory must already exist; the default constructor
creates its file/schema as before. Use a separate logical namespace from daily
progress. A custom async backend implements the same opaque-text `load(chat_id)` and
atomic exact-text `compare_and_swap(chat_id, expected, data)` protocol.

Retain the request identity **before submitting it** if its response might be lost.
Retain the returned reference for status/reopening. Equal settings are not a new-run
identity: a deliberately new run needs a fresh `run_id` and matching predecessor.
Do not store secrets in collection, destination or request identity strings.

Use `last_days=30` instead of both explicit dates to freeze N × 24 hours ending at
accepted creation. Matching retained retries reuse the original dates without reading
the clock. Explicit windows must be closed, start-inclusive/end-exclusive, timezone-
aware and within the existing fixed-window wire range. `origin="fresh"` requires
`after_id=0`; `origin="imported"` labels the caller-supplied starting position without
claiming to verify the preceding archive.

## Reopen without creating missing state

```python
from tgdata.backfill import BackfillRunRef, BackfillStartRequest

reference = BackfillRunRef.from_dict(saved_reference_dict)
request = BackfillStartRequest.from_dict(saved_request_dict)
store = SQLiteSyncStore("backfill-progress.sqlite3", create=False)
engine = BackfillEngine(store, reference.collection_id)
status = await engine.status(reference)
result = await engine.start(request, submission="retry")
assert result.applied is False
```

`create=False` refuses a missing file or schema at SQLite's actual open, including
when it disappears during reopening. It does not provision an empty replacement.
The default `create=True` preserves existing behavior; this option changes neither
the database schema nor the backend protocol. Load/CAS also refuse a disappeared file.

`submission` is required. A recognized identical request returns its addressed current
or retained-prior status without writing; changed input conflicts. An unknown `retry`
never creates, including when the row is absent. Missing known references raise rather
than becoming fresh enrollment. A new successor requires the exact current predecessor
to be terminal, quiescent and free of owed output. Preparation/final acknowledgment
can produce completed runs. Cancel/abandon can also make a run terminal, but a successor
still waits for admitted work and owed delivery to settle or be explicitly retired.
The same engine refuses succession while local preparation/replay remains active.

Only the current and immediate prior run are retained. Prior status is marked
`history_limited`; older references/requests refuse. Generations and revisions cannot
wrap. A backend failure after commit may still have committed. After an ordinary
ambiguous create, publication or acknowledgment reply, the engine makes **one**
authoritative read-back. A validated snapshot identical to the full attempted state
confirms success, including empty completion or final acceptance. It makes no second
write or source call. A start confirmed this way returns `applied=True`; a later
retained request retry returns `applied=False`.

An absent, changed or unreadable snapshot leaves the write unconfirmed; corrupt state
raises its validation error. A changed snapshot may contain a later valid transition,
so a failure is never proof of rollback. Inspect status or retry the same retained
request/receipt deliberately. The engine does not partially match fields or overwrite
newer state to recover a reply. Backend errors expose operation and exception type,
never raw error text or saved payloads. Cancellation propagates without reconciliation
I/O. Neither cancellation nor an ambiguous admission reply grants permission to read.

## Prepare, deliver and acknowledge

Here `tg` is an existing configured `TgData`, including the caller's session, proxy and
read-budget policy. `deliver_and_commit` is supplied by the caller and must durably
accept the batch and every required artifact before returning.

```python
from tgdata.backfill import BackfillPrepareContext

engine = BackfillEngine(store, reference.collection_id,
                        read_batch=tg.get_message_batch)
current = await engine.status(reference)
turn = await engine.prepare(BackfillPrepareContext.from_status(current))
if turn.wait_seconds is not None:
    print("Try another turn in", turn.wait_seconds, "seconds")
elif turn.batch is not None:
    await deliver_and_commit(turn.batch, turn.delivery)
    current = await engine.acknowledge(turn.delivery)
else:
    current = turn.status
```

For a download-mode run, pass `download_media_to=your_artifact_directory` to `prepare`.
Reference mode rejects that argument. Only `prepare` can invoke the reader; admission
is durably recorded first. The saved group, dates, exclusive cursor and batch size are
passed directly to the raw reader. A stale accepted cursor or control revision refuses
before another read. Obtain a new context deliberately after acknowledgment/control;
do not silently replace a failed request's context with newer values.

The result contains immutable status, an optional owned MessageBatch and its
`BackfillDeliveryRef(run, destination_id, batch_id)`. A bare batch hash is insufficient:
different runs can produce the same hash. Portable contexts/receipts have `to_dict()`
and `from_dict()` conversions; all identity/cursor/revision integers remain exact.
Persist the whole delivery reference with the destination's acceptance record.

Until acknowledged, another matching preparation returns the exact saved batch and
reference with `turn.replayed=True`, without Telegram, budget use or a new clock/timer.
An engine with no reader callback can replay, acknowledge and query status. Download
replay verifies hash/size under the supplied root; intact files may be relocated.
Missing/corrupt/symlink-substituted artifacts refuse rather than trigger refetch.

Acknowledgment is the caller's assertion of durable external acceptance. It advances
only to the saved next ID and clears pending atomically. It never invokes a receiver,
checks local media or deletes files: valid acceptance can be recorded after already-
delivered local files disappeared. Latest matching retries are harmless even with
newer pending work. Retained previous-run receipts cannot acknowledge a successor;
unknown, wrong-destination or retired references refuse without changing current work.
The caller still makes receiver processing repeat-safe, commonly by group/message ID
and delivery identity; library acknowledgment is not an exactly-once external transaction.

Actual `end` evidence is retained independently of delivery. Empty exhaustion needs
no fake batch. A final nonempty batch stays pending until acknowledged; only then can
the run be completed. A `limit` batch, failed read or interrupted prefix never proves
completion. Existing cancellation takes precedence over a later final acceptance.
Completion preserves the declared origin and frozen window. An imported run certifies
only its declared tail, without verifying the caller's skipped archive. A completed
run reopens without another source read; rescanning requires deliberate new intent.

## Pause, resume, cancel and abandon

Retain a command identity and its original expected control revision before submission:

```python
from uuid import uuid4

status = await engine.status(reference)
pause_args = dict(command_id=uuid4().hex,
                  expected_control_revision=status.control_revision,
                  action="pause")
result = await engine.control(reference, **pause_args)
```

Use `action="resume"`, `"cancel"` or `"abandon"` for a new deliberate decision, with
its own retained ID/context. An accepted command advances control revision once,
including a pause on an already paused run or resume on an already active run.
Ordinary delivery progress does not change that control revision. Exact recognized
retries return the addressed current status without applying the decision again.
Changed inputs with a retained ID and unaccepted stale contexts conflict; never
automatically replace a retry's expected revision. Only the latest command is retained.

Pause denies new source admission. It lets an already admitted bounded turn finish
its SDK calls and publish its result; it does not promise instant traffic termination.
Resume grants operator permission while preserving pending data, wait deadlines,
unresolved activity and actual account restrictions. Replay and valid acknowledgment
remain possible while paused or cancelled, using current preparation context.

Cancel is terminal and preserves all admitted activity and owed delivery. If it commits
before final acknowledgment, that acknowledgment records delivery while the run stays
cancelled. If completion commits first, cancellation reports completed. Commit order
decides; a delayed command response may describe an older revision, so its arrival
does not replace newer stored status. No control can resume terminal work.

Abandon explicitly withdraws the remaining delivery guarantee. It requires no uncertain
attempt and no active local preparation; stop the worker and recover its exact attempt
first when necessary. It records `abandoned_batch_id`, `abandoned_next_after_id` and
`abandoned_at`, clears pending and leaves the accepted cursor unchanged. With no owed
batch the hash is None and recorded next cursor equals accepted progress. An active
run becomes abandoned; a cancelled run stays cancelled. It neither deletes files nor
creates a successor. A retired receipt cannot accept a later run with identical bytes.

`BackfillControlResult` exposes command ID/action, `applied`, `outcome` and status.
`outcome="accepted"` is a new decision (`applied=True`) or retained exact retry
(`False`). `outcome="terminal"` reports an existing terminal outcome without accepting
another command, writing or consuming a revision. The exception is an explicit first
abandonment of a current cancelled run. Retained previous terminal runs remain read-only.
Status also exposes the last control action, original expected revision and accepted
state revision. These are facts, not a grant for a new command or source read.

Controls do no Telegram, budget or health work. Only a new abandonment reads UTC for
its observation timestamp; other control decisions need neither clock. They preserve
revision capacity for still-owed source publication/acknowledgment. Exact write
confirmation and cancellation behavior are the same as for other local transitions.

## Failures, timing and staged limits

An ordinary source exception is re-raised unchanged after its valid complete prefix
is stored. Re-run preparation with the current context to obtain that owed prefix's
delivery reference. If validation, media or persistence prevents settlement, a local
`BackfillError` exposes the original separately in `read_error`; it is not an exception
cause used for Telegram health classification. Source error text is not stored.

Cancellation or an unconfirmed write can leave `status.attempt_id` unresolved. Another
prepare raises `BackfillRecoveryRequired`, with content-free status, instead of reading
again. If publication actually committed but exact read-back could not confirm it,
reopening/retry replays the persisted batch. If acknowledgment committed, retrying that same complete
receipt recognizes it. No automatic rollback/reset is inferred. Use explicit recovery
below for an unresolved attempt; do not clear the record or
create a replacement run to bypass it.

### Pacing and source restrictions

The example chooses a four-minute pause. A source attempt ending at 10:00 is not
locally eligible again before 10:04, whether its acknowledgment arrives at 10:01 or
10:10. Failures also establish their attempt-end deadline. A cancellation leaves
uncertainty until explicit recovery. `pause_seconds=0` explicitly disables only this
run's extra spacing; configured account budgets and SDK/server restrictions still apply.

An early `prepare` returns a no-data turn with positive `wait_seconds`. It does not
sleep, write state, call the source or create a media directory. The caller schedules
another turn and may do daily work meanwhile. Pending replay, status and receipt
settlement remain available; they never restart or extend the pacing deadline.
`status` returns stored facts without consulting a clock or the account's budget.
A first acknowledgment records its own UTC timestamp, independent of pacing eligibility.

The wait describes **local pacing only**. `last_failure_*` fields retain an observed
source failure, its time, optional retry hint and any account identity supplied by the
actual budget exception. Direct known SDK wait errors may supply a duration hint;
local error causes and cached health identities do not. A missing/indefinite hint
stays `None`, not zero. Historical hints neither grant quota nor gate another account:
an intentional locally eligible turn still passes through the reader's fresh account/
budget check and SDK restrictions. An expired estimate is not reserved capacity or
proof that the next read will succeed. Ordinary source errors still propagate.

### Recover a stopped attempt

Retain one recovery request for a deliberate decision. **Actually stop and wait for
the previous reader before submitting it**, across every engine/process that might
own that group's read. The assertion below does not terminate a worker or acquire a
lease. The same engine also refuses recovery while any preparation for that group is
still active, including admission/publication waits.

```python
from uuid import uuid4

status = await engine.status(reference)
# Create and retain these arguments once; unchanged retries reuse them.
recovery_args = dict(
    attempt_id=status.attempt_id,
    command_id=uuid4().hex,
    expected_control_revision=status.control_revision,
    previous_reader_stopped=True,  # assert only after your worker really stopped
)
result = await engine.recover(reference, **recovery_args)
status = result.status
```

Use the exact retained run/attempt/control context. Do not replace an old request's
attempt ID or expected revision with current values automatically. False/missing
quiescence, wrong/stale context, local active preparation, unavailable state or an
unconfirmed write never permits another read. Reusing a recognized command ID with
changed input conflicts; older forgotten attempts may refuse harmlessly.

A new recovery clears only its matching unresolved attempt, preserving accepted
position, delivery/end/terminal facts and source-failure observations. If this engine
still knows the actual local end after an unconfirmed save/cancellation, it preserves
that end/deadline. Otherwise it saves one full quiet interval from the trusted recovery
observation after quiescence, preserving stronger known restrictions. The observation
is accepted atomically with recovery; it is not the backend's physical commit timestamp.
Time awaiting the write counts as quiet time; a lost reply does not restart it.

`BackfillRecoveryResult` returns the command/attempt, `applied`, `outcome` and status.
`outcome="recovered"` with `applied=True` confirms a new recovery; its retained duplicate
returns `applied=False` without a clock or another write. `outcome="settled"` means the
addressed attempt was already resolved by source settlement or another recovery; it
reports the facts without accepting a new command. It does **not** mean the backfill
is completed. Pending/completed outcomes reconcile without local artifact access.
Recovery never reads Telegram, delivers/acknowledges output, resumes operator intent,
creates exhaustion, or refunds/configures account allowance.

### Clock evidence and limits

Saved pacing uses UTC. Within an engine's lifetime, an independent monotonic minimum
also protects elapsed time, so a forward wall-clock step cannot shorten a locally
anchored wait. Reopening establishes a local anchor once from the remaining saved UTC
interval; repeated checks do not restart it. Backward or invalid clock evidence refuses
new admission/recovery. Persisted uncertain timing is an explicit blocker.

The engine accepts `clock` (aware UTC datetime) and `monotonic_ns` (nonnegative integer
nanoseconds, up to signed-64-bit maximum) for independent testing. Monotonic ticks never
enter the portable record. After process/engine recreation, reboot or moving machines,
local evidence is gone and the application must trust UTC. Arbitrary undetectable jumps
cannot be solved here. This is per-run spacing, not account-wide rest or a bound on a
raw turn's elapsed duration: the SDK can still retry/wait inside that turn.

Status exposes saved `pacing_attempt_id`, `pacing_ended_at`, `pacing_not_before`, and
`last_recovery_id`, `last_recovered_attempt_id`, `last_recovery_at`. The record remains
opaque v1; these additive internal result fields do not change MessageBatch v1.

One source reader per group remains a caller precondition across collections and daily
work. The engine prevents overlapping local preparation and uses durable admission for
its own aggregate; it does not provide leases or distributed ownership. Local SQLite,
payload validation and media hashing are synchronous work proportional to retained data;
local replay is not a constant-time/no-I/O promise. No background scheduler is introduced.

## Validation and representation

`tgdata.backfill-state` version 1 is an opaque single-record aggregate with strict
nested fields and cross-field checks. Wrong-kind daily/window records, unknown versions,
duplicate/missing/extra fields, invalid dates/IDs, nonfinite values and contradictory
pending/cursor/end/control/attempt facts refuse without repair. The old daily engine
likewise rejects lifecycle records. The backend remains trusted; structural validation
cannot authenticate a fabricated event history.

References and requests are immutable. Portable IDs/generations/revisions are canonical
decimal strings; object attributes remain integers. Status is immutable, content-free
and attributable to a run/state revision. It is not a grant to read or proof of source
availability.

Pacing seconds are finite/nonnegative and must be representable. The requested normalized
value remains part of intent. Minimum datetime durations round **up** to whole microseconds,
independently of an application's Decimal context; zero remains zero. Stage 5 enforces
these intervals with independent UTC/monotonic evidence.

## Verification and live gate

Run `python -m tgdata.smoke_tests.test_24_backfill_state` and
`python -m tgdata.smoke_tests.test_25_backfill_delivery`, followed by
`python -m tgdata.smoke_tests.test_26_backfill_completion` and
`python -m tgdata.smoke_tests.test_27_backfill_pacing` and
`python -m tgdata.smoke_tests.test_28_backfill_controls`. They exercise actual SQLite,
process exits around commit, receiver transactions, custom-backend faults and blocked
network access. Delivery tests use actual SDK/batch/media code with synthetic transport.
Completion tests include exact read-back versus unavailable/moved-on state, original
source-error provenance, and actual process exits around empty completion/final ack.
Stage 5 tests execute actual recovery with independent clocks, real budget admission,
and process exits at recovery commits. Stage 6 tests execute actual controls, concurrent
settlement, terminal ordering, abandonment, receipt isolation and control commit exits;
older seeded fixtures remain preservation tests only.

Gates A/B passed the selected real-source foundation and delivery/completion composition
on the issue branch. Gate C subsequently passed actual pacing/budget/recovery/control
composition at Stage 6. Stages 7–8 add public facade and combined failure tests.
The separate public/live Gate D passed on 2026-10-07 with actual Telegram, SQLite
and the selected byte/snapshot receiver. These offline checks alone do not establish
live behavior or another deployment's guarantees.

The issue branch retains the opt-in `devdocs/work/19-backfill-run-lifecycle/live_probe.py`
instrument and its input specification. This is staged development tooling, not an
installed public API. Default preflight is offline; live mode requires an existing
read-only group, chosen account/config, independently complete frozen oracle, request
caps and an already configured authoritative budget. A matching diagnostic raw scan
never automatically passes Gate A and never advances lifecycle progress.
