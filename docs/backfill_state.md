# Backfill state — Stage 2

This staged interface implements durable **start and status only**. It does not yet
prepare/acknowledge lifecycle batches, complete a run, enforce pacing, pause/cancel or
recover source attempts. Those later stages require the live validation gates. No new
`TgData` facade methods or package-root exports are introduced here.

The internal modules below can be used for Stage 2 verification. The existing daily
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
to be terminal, quiescent and free of owed output. This stage can validate such snapshots;
it does not provide the later operations that produce terminal runs.

Only the current and immediate prior run are retained. Prior status is marked
`history_limited`; older references/requests refuse. Generations and revisions cannot
wrap. A backend failure after commit may still have committed: reload/retry the same
context. Cancellation propagates; it does not prove rollback. Backend errors expose
operation and exception type, never raw error text or saved payloads.

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

Run `python -m tgdata.smoke_tests.test_24_backfill_state`. It uses real SQLite, actual
process exits around commit, custom-backend faults and blocked network access. Future
pending/control/terminal fixtures test their codec and successor restrictions, not
unimplemented lifecycle transitions.

The issue branch retains the opt-in `devdocs/work/19-backfill-run-lifecycle/live_probe.py`
instrument and its input specification. This is staged development tooling, not an
installed public API. Default preflight is offline; live mode requires an existing
read-only group, chosen account/config, independently complete frozen oracle, request
caps and an already configured authoritative budget. A matching diagnostic raw scan
never automatically passes Gate A and never advances lifecycle progress.
