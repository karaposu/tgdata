# Backfill state and delivery — Stages 2–3

This internal staged interface implements **start, status, prepare/replay and
acknowledge**. Preparation retains one exact batch before returning it; acknowledgment
records the caller's durable acceptance. Minimal end/completion transitions preserve
saved-state invariants, while Stage 4's dedicated completion/uncertain-write audit
remains pending. Positive timing/recovery, controls and the public facade retain
their later stages. No new `TgData` methods or package-root exports are introduced.

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
    pause_seconds=0, expected_predecessor=None,
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
can produce completed runs. Cancel/abandon operations remain later-stage work.

Only the current and immediate prior run are retained. Prior status is marked
`history_limited`; older references/requests refuse. Generations and revisions cannot
wrap. A backend failure after commit may still have committed: reload/retry the same
context. Cancellation propagates; it does not prove rollback. Backend errors expose
operation and exception type, never raw error text or saved payloads.

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
if turn.batch is not None:
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
Stage 4 still supplies the dedicated completion/reconciliation audit and full fault matrix.

## Failures, timing and staged limits

An ordinary source exception is re-raised unchanged after its valid complete prefix
is stored. Re-run preparation with the current context to obtain that owed prefix's
delivery reference. If validation, media or persistence prevents settlement, a local
`BackfillError` exposes the original separately in `read_error`; it is not an exception
cause used for Telegram health classification. Source error text is not stored.

Cancellation or an unconfirmed write can leave `status.attempt_id` unresolved. Another
prepare raises `BackfillRecoveryRequired`, with content-free status, instead of reading
again. If publication actually committed before its reply failed, reopening/retry
replays the persisted batch. If acknowledgment committed, retrying that same complete
receipt recognizes it. No automatic rollback/reset is inferred. Explicit recovery is
Stage 5; do not clear an attempt or create a replacement run to bypass it.

The example chooses `pause_seconds=0` to exercise repeated Stage 3 source turns. This
disables only the run's extra spacing, never the configured budget/server restrictions.
A first positive-pause turn records its real end/deadline, but another source admission
requiring positive timing fails closed with a staged configuration error until Stage 5.
Uncertain timing also refuses; replay and valid acknowledgment remain available. No
stored policy is rewritten, and waiting longer does not bypass this capability boundary.

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
and attributable to a run/state revision. It is not a grant to read, proof of source
availability, or a claimed implemented pacing/control state machine.

Pacing seconds are finite/nonnegative and must be representable. The requested normalized
value remains part of intent. Minimum datetime durations round **up** to whole microseconds,
independently of an application's Decimal context; zero remains zero. This stage validates
representation and saved timing facts; actual wait enforcement is Stage 5.

## Verification and live gate

Run `python -m tgdata.smoke_tests.test_24_backfill_state` and
`python -m tgdata.smoke_tests.test_25_backfill_delivery`. They exercise actual SQLite,
process exits around commit, receiver transactions, custom-backend faults and blocked
network access. Delivery tests use actual SDK/batch/media code with synthetic transport.
Seeded control/recovery fixtures test preservation, not unimplemented operations.

Gate A already passed real-source foundation validation on the issue branch. Gate B
must exercise the new delivery/completion composition after Stage 4; offline passes do
not substitute for it. No later-stage/public-API readiness follows from these checks.

The issue branch retains the opt-in `devdocs/work/19-backfill-run-lifecycle/live_probe.py`
instrument and its input specification. This is staged development tooling, not an
installed public API. Default preflight is offline; live mode requires an existing
read-only group, chosen account/config, independently complete frozen oracle, request
caps and an already configured authoritative budget. A matching diagnostic raw scan
never automatically passes Gate A and never advances lifecycle progress.
