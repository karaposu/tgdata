# Durable historical backfill runs

Use a backfill run when you need a fixed historical window, bounded turns, durable
replay, explicit acceptance, pacing and operator controls. The caller chooses accounts,
owns the receiver and schedules **one source reader per group**, including daily and
historical jobs. Plain `TgData` does not run a scheduler or choose another account.
The optional [AccountPool](account_pool.md) supplies existing-access account routing
through the same progress engines; it does not change acknowledgment or recovery.

The public API is available through `TgData(backfill_store=...)`. Existing daily
continuation, fixed-window calls and MessageBatch v1 keep their behavior. This interface
is verified with Telethon **1.45.0**. The complete public flow passed read-only live
Gate D on 2026-10-07 with SQLite and a selected durable test receiver, including real
pagination, daily/history separation, recovery, controls and photo custody. This
evidence does not certify a different receiver, backend, clock or worker deployment.

| Operation | Returns | Source behavior |
|---|---|---|
| `start_backfill(start_request, *, submission)` | `BackfillStartResult` | State only |
| `get_backfill_status(run)` | `BackfillStatus` | State only |
| `prepare_backfill(context, *, download_media_to=None)` | `BackfillTurn` | Reads only for a newly admitted eligible attempt; pending replay is local |
| `acknowledge_backfill(delivery)` | `BackfillStatus` | State only, asserting prior receiver acceptance |
| `control_backfill(run, *, command_id, expected_control_revision, action)` | `BackfillControlResult` | State only |
| `recover_backfill(run, *, attempt_id, command_id, expected_control_revision, previous_reader_stopped)` | `BackfillRecoveryResult` | State only after caller-established quiescence |

## Start explicit new intent

```python
from uuid import uuid4
from tgdata import TgData, SQLiteSyncStore, BackfillStartRequest

tg = TgData(
    "config.ini", interactive_login=False,
    sync_store=SQLiteSyncStore("daily-progress.sqlite3"),
    backfill_store=SQLiteSyncStore("history-progress.sqlite3"),
)
request = BackfillStartRequest(
    collection_id="archive-history", chat_id=-1001234567890,
    run_id=uuid4().hex, destination_id="my-durable-archive",
    pause_seconds=240, expected_predecessor=None, last_days=30,
    batch_size=200,
)
# Your application durably retains request.to_dict() BEFORE submitting it.
started = await tg.start_backfill(request, submission="new")
run = started.status.run
# Retain run.to_dict() for subsequent calls and process restarts.
```

`submission` is required. `new` declares deliberate new intent; `retry` only recognizes
the retained original request. A retry that is missing or no longer retained raises
`BackfillUnknownCommand`; it does not create a replacement. Do not switch an uncertain
retry to new automatically. A retained ID with changed inputs conflicts.

`last_days=30` freezes thirty 24-hour periods ending at accepted creation. Matching
retries reuse the saved boundaries tomorrow. Alternatively provide both timezone-aware
`start_date` and `end_date` for a closed `[start, end)` interval. Future-ended windows
refuse. `origin="fresh"` starts at zero; `origin="imported", after_id=N` explicitly
declares an exclusive starting cursor without claiming to verify earlier history.

A later deliberate run needs a new `run_id` and the exact current RunRef as
`expected_predecessor`. The predecessor must be terminal, quiescent and free of owed
delivery. Equal query settings do not make two jobs the same run. Names and IDs are
caller-controlled identifiers; do not put credentials in them.

## Reopen known state

```python
from tgdata import BackfillRunRef, BackfillStartRequest

tg = TgData("config.ini", interactive_login=False,
            backfill_store=SQLiteSyncStore("history-progress.sqlite3", create=False))
run = BackfillRunRef.from_dict(saved_run_dict)
status = await tg.get_backfill_status(run)

# If creation's response was lost, reuse its saved request:
request = BackfillStartRequest.from_dict(saved_request_dict)
recognized = await tg.start_backfill(request, submission="retry")
```

`create=False` refuses a missing database/schema instead of provisioning new progress.
The default SQLite constructor can create the file/schema; its parent directory must
exist. Missing known run/namespace, unreadable state and backend outage are errors,
never proof of an empty archive or permission to start again. Only current and immediate
previous run history is retained; older references may refuse harmlessly.

These calls touch the configured backend, not Telegram, config credentials or session
identity. A custom remote backend may perform its own database I/O.

## Prepare one turn, deliver, then acknowledge

Here `deliver_and_commit` is an application function. It must durably accept the exact
batch and all required artifacts at the named destination before returning.

```python
from tgdata import BackfillPrepareContext

async def one_history_turn(tg, run, deliver_and_commit):
    status = await tg.get_backfill_status(run)
    context = BackfillPrepareContext.from_status(status)
    turn = await tg.prepare_backfill(context)
    if turn.batch is not None:
        await deliver_and_commit(turn.batch, turn.delivery)
        status = await tg.acknowledge_backfill(turn.delivery)
        return status, None
    return turn.status, turn.wait_seconds
```

The caller schedules another turn after a returned wait and may give daily work a turn
meanwhile. `wait_seconds` is this run's **local spacing**, not guaranteed account
readiness. A missing wait is not a readiness promise: pause, terminal work and other
facts remain in status. The library does not sleep for its lifecycle pacing or maintain
your scheduling loop. SDK retries/waits may still occur inside an admitted source turn.

Until acceptance, matching preparation replays the exact saved batch and complete
`BackfillDeliveryRef`, with `replayed=True`, without source traffic, quota use or timer
reset. In download mode pass `download_media_to` for both preparation and replay;
replay verifies saved hash/size under that root. Missing/corrupt artifacts refuse
instead of refetching. Reference mode rejects a download directory argument.

Retain the complete delivery reference with the destination receipt. A batch hash alone
is insufficient: another run can produce identical bytes. Acknowledgment advances only
to the saved pending cursor, never to a supplied new cursor. It does not inspect the
receiver or remove files; it is your assertion that durable acceptance occurred. A valid
receipt can be acknowledged after already-delivered local files disappear.

The latest recognized ack is harmless to retry, including when newer data is pending.
Wrong, retired or unrecognized receipts refuse. Historical recognition is bounded;
active pending data does not expire with historical metadata. Make destination effects
repeat-safe yourself—there is no transaction spanning Telegram, tgdata state and your
receiver, and no exactly-once external processing guarantee.

An actual empty end can complete without a fake batch. A nonempty final end stays owed
until ack. A limit-sized batch or error prefix does not prove end. Completion certifies
the declared visible scope under the account/access conditions used, not an immutable
or universally complete Telegram archive.

## Pause, resume, cancel or abandon

```python
status = await tg.get_backfill_status(run)
pause_args = dict(command_id=uuid4().hex,
                  expected_control_revision=status.control_revision,
                  action="pause")
# Retain these exact arguments before submission.
outcome = await tg.control_backfill(run, **pause_args)
```

Create a fresh command for each deliberate decision. Retained retries reuse their
original ID, action and expected revision. Never refresh an old command's expected
revision automatically. Accepted order controls state; an old response arriving later
can describe an older revision. Query current status rather than treating arrival order
as fresh permission.

- **Pause** denies new admissions. An already admitted bounded read can finish its
  remaining SDK calls and publish data. Pause is not instant transport cancellation.
- **Resume** grants operator permission while retaining pending work, waits, source
  restrictions and unknown attempts. It cannot revive a terminal run.
- **Cancel** is terminal and preserves admitted work and owed delivery. Final ack
  after cancel remains cancelled; cancel after completion reports completed.
- **Abandon** explicitly withdraws the delivery guarantee after source quiescence.
  It records the abandoned obligation without advancing accepted progress or deleting
  blobs. A nonterminal run becomes abandoned; a cancelled run remains cancelled.

Replay and valid ack remain available while paused/cancelled; obtain current prepare
context after a control changes its revision. An accepted matching no-change pause or
resume still advances control revision once. A recognized retry does not.

Control results have `outcome="accepted"` for a new decision (`applied=True`) or its
retained retry (`False`). `outcome="terminal"` reports an existing terminal result
without a new accepted command or write. The explicit exception is a first abandonment
of current cancelled work. Retained previous runs are read-only.

## Source failure, uncertain writes and recovery

An ordinary source exception is re-raised unchanged after a valid completed prefix is
saved when possible. Inspect status and, **only if pending exists**, call prepare with
its current context to replay that owed batch and obtain its scoped delivery reference.
Do not acknowledge a bare `error.partial_result.batch_id`, and do not call prepare
indiscriminately after every error: with no pending it may become a new intentional read.

If prefix validation/storage/media prevents settlement, the local `BackfillError`
retains the actual source failure separately in `read_error`, not as a health-classified
exception cause. Stored failure facts retain category, error type and optional retry
evidence; they do not contain raw error text or grant quota. Only the actual raw reader
uses the existing Telegram health context. Local successes/failures do not create
Telegram verdicts or clear previous health problems.

An error/cancellation after a write does not prove rollback. The engine can confirm
ordinary uncertain writes with one exact authoritative readback. A changed/unavailable
snapshot leaves uncertainty; it is never permission for a compensating write or fetch.
An ambiguous admission reply specifically does not authorize source traffic.

If `status.attempt_id` remains unresolved, another read refuses. First actually stop
and await the previous worker across all instances/processes that may read that group.
Closing a connection alone does not establish task quiescence. Then deliberately retain
and submit one exact recovery command:

```python
status = await tg.get_backfill_status(run)
recovery_args = dict(
    attempt_id=status.attempt_id,
    command_id=uuid4().hex,
    expected_control_revision=status.control_revision,
    previous_reader_stopped=True,  # only after your worker really stopped
)
# Retain recovery_args before submission; reuse them unchanged after a lost reply.
outcome = await tg.recover_backfill(run, **recovery_args)
```

The required assertion is not a lease or worker termination API. Active local preparation
still refuses. Recovery reconciles committed outcomes first, or clears only its exact
stopped uncertain attempt. It preserves known end evidence or records one conservative
quiet interval; repeated recovery does not restart it. It never accepts data, invents
end, resumes intent, reads Telegram or refunds/configures allowance.

Recovery results use `outcome="recovered"` for a new recovery/retained retry, and
`"settled"` when the addressed source attempt is already settled without accepting a
new recovery command. Neither means that the whole run is completed. Missing/replaced
context or uncertain clock evidence requires inspection, not automatic zero waiting.

## Stored status and public values

`BackfillStatus` is immutable and contains no batch/message bodies or sender metadata.
Its independent fields deliberately avoid a single misleading "ready" label.

| Facts | Fields and meaning |
|---|---|
| Identity/scope | Full `run`, `destination_id`, `origin`, initial cursor, fixed dates, creation time and immutable batch/media/pacing policy |
| Accepted progress | `after_id`, `last_acked_batch_id`; a saved pending batch has not advanced this cursor |
| Owed output | `pending_batch_id`, count and pending next cursor; full data is returned in a Turn, not status |
| Activity | `attempt_id` means an admitted unresolved attempt; status alone cannot tell whether its worker still lives |
| Operator/terminal | `operator_intent` and `terminal_outcome` remain separate; a cancelled run can still owe data |
| Source end | `source_exhausted` is saved end evidence, independent of destination acceptance |
| Timing | Saved pacing attempt/end/not-before and `clock_uncertain`; a Turn's optional wait is local, not account readiness |
| Failure | Historical category/type/time, optional retry hint and verified budget-account ID when supplied by that error; no account lookup |
| Recognition | Control revision, last command/action/original expected/accepted state revision and recovery identity/observation |
| Retirement/history | Abandoned batch/next cursor/time and `history_limited`; previous history is bounded |

Root imports include `BackfillRunRef`, `BackfillStartRequest`, `BackfillPrepareContext`,
`BackfillDeliveryRef`, `BackfillStatus`, `BackfillStartResult`, `BackfillTurn`,
`BackfillControlResult` and `BackfillRecoveryResult`. Identity/request/context/receipt
objects provide `to_dict()` and `from_dict()`; result/status values provide `to_dict()`.
Portable identity/cursor/revision integers are exact decimal strings; counts/policy
values remain numeric and dates are canonical UTC. Results do not expose internal engines.

| Error | Meaning |
|---|---|
| `BackfillConfigurationError` | Invalid input or missing backend configuration |
| `BackfillClockError` | Invalid/contradictory clock evidence; a configuration-error subtype |
| `BackfillConflictError` | Stale/incompatible context, active preparation or insufficient transition capacity |
| `BackfillUnknownRun` | Known run missing or no longer retained |
| `BackfillUnknownCommand` | Creation retry is not retained and cannot create |
| `BackfillUnknownReceipt` | Receipt is not owed/recognized, including explicit retirement |
| `BackfillStateError` | Invalid/wrong-kind/wrong-scope state or incompatible reader observation |
| `BackfillStorageError` | Backend operation failed; a write may already have committed |
| `BackfillRecoveryRequired` | Preparation needs explicit investigation/recovery; carries stored status |
| `BackfillMediaError` | Local artifact root/integrity failure |

These derive from `BackfillError`; source exceptions remain their original classes.

## Backend, time and caller ownership

`backfill_store` implements `await load(chat_id) -> str | None` and
`await compare_and_swap(chat_id, expected, data) -> bool`. CAS must compare exact text
and commit durably/atomically; a queued write is not success. The payload is opaque
versioned state owned by tgdata and includes the temporary pending batch needed for
replay. Protect it and required media according to your application's data policy.

Configure **one isolated collection namespace** for the backend. `collection_id` is
identity, not a database routing key; changing it does not select another namespace.
Wrong daily/backfill or stored collection records refuse without migration. SQLiteSyncStore
is a convenient separate-file backend. A custom backend can isolate `(namespace, chat_id)`
rows in one database; the example below does this. Do not reuse one progress namespace
for daily and historical collections of the same group.

The facade retains engines, local activity and monotonic minima for its lifetime,
including close/reconnect. Cache memory follows caller-used collection IDs; it is not
a backend registry. Do not mutate private store/cache fields to route a request.
Across processes or sequential moves, share the known namespace, original identity and
required pending media, and ensure the previous source worker has stopped.

Pacing saves UTC evidence and uses a local monotonic minimum while known. After local
context loss, trusted UTC remains an application precondition; arbitrary undetectable
clock jumps are not solved. `pause_seconds=0` disables only this run's extra spacing,
not actual account budgets or SDK/server restrictions. Local SQLite and artifact hashing
are synchronous bounded work; remote backends may await their own I/O. No database lock
should span source calls. Account choice, warm-up policy, workers and the permanent
archive remain application responsibilities.

## Offline receiver/restart example

```bash
python examples/backfill_runs.py --demo
# Retain its files, with an explicit first-use decision:
python examples/backfill_runs.py --demo --directory ./backfill-demo --new
python examples/backfill_runs.py --demo --directory ./backfill-demo
```

[The example](../examples/backfill_runs.py) blocks sockets and uses synthetic public
batch values. It does execute real SQLite transactions and an owned process exit after
receiver commit, before library ack. A fresh process replays without a source read,
accepts the same receipt once, acknowledges while paused, resumes and interleaves one
daily turn with bounded historical turns. It produces five unique records, history
completed at 104, daily progress at 105 and a separately cancelled successor. A completed
repeat reads no new source data. Missing known state or repeated `--new` refuses.

The example receiver retains the full canonical batch with each scoped receipt, plus
a deduplicated first-observation message index. Different observations for one message
ID remain in their respective receipt snapshots; the index is not the entire archive.
It demonstrates reference mode only; real download receivers must also durably retain
and verify artifact bytes before acknowledging. It does not perform edit reconciliation.

This is one chosen lost-ack demonstration, not an automatic arbitrary-crash recovery
service or proof about Telegram/deployment durability. Other interruptions can require
explicit inspection; retained command contexts are never silently rewritten to finish.
Close TgData connections when done and retain your chosen state/artifact storage.

Run `python -m tgdata.smoke_tests.test_29_backfill_public` for the offline public/example
checks, and `python -m tgdata.smoke_tests.test_30_backfill_integration` for combined
public failures and actual process exits around nine SQLite commit boundaries.
Earlier internal checks remain in tests 24–28. Gate D separately exercised the real
public source/backend/receiver composition; synthetic tests alone do not establish
Telegram behavior or operational receiver durability.
