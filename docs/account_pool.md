# Reading through an account pool

`AccountPool` chooses among distinct, already logged-in accounts. It supports raw
batches and the same daily/backfill operations as `TgData`. Accounts must already
be able to read the groups: the pool never joins, sends login codes or prompts.
Plain `TgData` and its same-account `connection_pool_size` keep their behavior.

The source adapter requires **Telethon 1.45.0**. Its SDK, storage and failure
composition has offline tests with synthetic replies and real SQLite transactions.
Two-account live qualification remains pending. Offline tests do not prove equal
history visibility or that a particular real proxy works.

## Configure accounts, groups and storage

```python
from tgdata import (
    AccountPool, PoolAccount, PoolGroup, PoolPolicy,
    ReadBudget, SQLiteAccountPoolStore, SQLiteSyncStore,
)

# Reuse deliberately configured account policies. Never reset allowances on startup.
budget = ReadBudget("read-budgets.sqlite3")
pool = AccountPool(
    [PoolAccount(111111, "account-a.ini"),
     PoolAccount(222222, "account-b.ini")],
    [PoolGroup(-1001234567890, "@my_existing_group")],
    read_budget=budget,
    state_store=SQLiteAccountPoolStore("pool.sqlite3", create=False),
    policy=PoolPolicy(strategy="drain", attempt_timeout=30, max_attempts=3),
    sync_store=SQLiteSyncStore("daily.sqlite3", create=False),
    backfill_store=SQLiteSyncStore("history.sqlite3", create=False),
)
```

Use your own authenticated numeric account IDs and canonical negative group IDs.
Each config uses existing Telegram/proxy/device settings. Optional `session_store=`
and `label=` belong to `PoolAccount`; the session-store contract is unchanged. Do
not put credentials in labels. The pool owns its clients and sessions exclusively;
do not use them in another scraper or rotate credentials during a read.

Configure each `ReadBudget` policy deliberately using the existing
[budget contract](../README.md#per-account-read-budgets). Missing policy is an error,
never unlimited access. Failed/cancelled sends retain their reservations. The pool
never configures, resets or refunds the ledger.

`PoolGroup(chat_id, reference=None)` resolves the canonical ID by default. An optional
public username/link helps when an account lacks a cached access hash. The resolved
entity must match the registered ID; a reassigned username cannot redirect progress.
Private groups need account-specific cached resolution. No dialog sweep or invite
join is hidden in resolution.

## Provision once, then reopen

For deliberate first provisioning, use `SQLiteAccountPoolStore("pool.sqlite3")`
and `await pool.initialize()`. Its parent directory must exist. Create new daily/
history stores separately when those collections are new.

For ordinary restarts, use `create=False` and omit `initialize()`. Missing files or
state, corruption and backend outages are errors; do not replace known state to
handle them. After adding an account to inventory, explicit `initialize()` enrolls
that ID without resetting existing restrictions or unresolved attempts. Removing
an account from inventory does not delete its stored facts.

One logical pool owns a dedicated store. Do not share its file with progress stores.
A custom backend implements async `load() -> str or None` and
`compare_and_swap(expected, data) -> bool`. CAS must compare/write atomically against
authoritative state. A failed response or cancellation does not prove rollback.

Store the versioned opaque string unchanged. It contains account IDs, attempt tokens,
timestamps and restrictions, never credentials, messages, quotas or accepted message
positions. SQLite does short synchronous I/O on the event loop; remote methods may
await their own I/O. Status and initialization do not open Telegram clients.

Pool, daily and backfill providers run in owned child tasks. They must complete or
settle their subordinate I/O before returning; they must not detach writes. They
serve storage only and must not call, or depend on another task controlling, the
same pool. Detected calls to read/initialize/recheck/recover/close from their live
scope raise `PoolBusyError` before source or administrative mutation. This guard
is not a general detector of dependencies through pre-existing external tasks.

Cancellation of a provider's own awaited I/O becomes a local storage error with
only its type in the message. Cancelling the public caller instead cancels its
provider once, waits for it to finish (including finalization), then propagates
cancellation. A provider may commit during that finalization. Neither outcome proves
rollback or grants new source permission. Set appropriate I/O timeouts in your
provider; the pool cannot turn a deadline into proof a write has stopped.

## Read and select accounts

```python
from tgdata import PoolReadCapture, PoolUnavailable

capture = PoolReadCapture()
try:
    result = await pool.read(-1001234567890, capture=capture, after_id=500, limit=100)
    print(result.account_id, result.attempts)
    await destination_accepts_durably(result.batch)  # your application's receiver
except PoolUnavailable as error:
    for account in error.accounts:
        print(account.account_id, account.reasons, account.retry_at)
    print(error.retry_after)  # None: no finite automatic retry is known
finally:
    snapshot = capture.snapshot()
    await pool.close()
```

`read` returns immutable `PoolReadResult(batch, account_id, attempts)`. The batch
retains MessageBatch v1 and its hash. `get_message_batch` returns only that batch.
Both require `capture=` and accept fixed date boundaries and an optional media
directory. The pool's own progress methods use an internal reader that shares the
outer call's capture; it does not bind that capture a second time.

`drain` selects the first eligible account in inventory order. `spread` selects the
largest remaining allowance, breaking ties by inventory order. There is no hidden
affinity policy. Each account is attempted at most once per call, within `max_attempts`.
One source/administrative operation may be active; overlap raises `PoolBusyError`.

Eligibility includes saved waits, unresolved attempts, account repair flags, group
denials, budget and optional `min_warmup_days`. That minimum defaults to zero; the
ledger's reduced warm-up caps still apply. No finish date is inferred from its curve.

Defaults permit another transport probe after 30 seconds and a denied/unresolved
group probe after 300 seconds. Configure `transient_retry_seconds` and
`access_retry_seconds` to change those policies. Telegram waits are preserved and
conservatively block that account's pool source operations. Ban/logout/restriction
or identity repair requires deliberate rechecking. Group denial affects only that group.

`PoolUnavailable` supplies per-account reasons and conditional retry hints. Reasons
include `waiting`, `budget`, `warmup`, `unresolved_attempt`, repair conditions and group
denials. An attempt cap can leave an eligible untried candidate, yielding retry_after
zero. Another call may spend allowance before retry. Unavailable never means empty history.

## Retain data through cancellation

Create a `PoolReadCapture` before starting a pool read and keep a reference where
your application can inspect it after the awaited operation stops. Pass it as the
required `capture=` argument to `read`, `get_message_batch`, `sync_group` or
`prepare_backfill`. Allocate a new capture for every call, including replay. Existing
pool call sites must add this argument; ordinary `TgData` APIs are unchanged.

```python
import asyncio

capture = PoolReadCapture()
reader = asyncio.create_task(
    pool.read(chat_id, capture=capture, after_id=500, limit=100)
)
try:
    result = await asyncio.wait_for(reader, timeout=30)
finally:
    snapshot = capture.snapshot()
    # snapshot.batch holds any available complete records. Keep it for your receiver.
    # Do not acknowledge a daily/backfill delivery from this snapshot alone.
```

`snapshot()` is synchronous, performs no I/O and returns an immutable
`PoolReadSnapshot`. Reading it does not consume the data. Earlier snapshots remain
unchanged when more messages arrive, and a final snapshot remains unchanged after
pool closure or another read. Keeping the capture outside the reader Task makes
its data accessible even when a timeout, `shield`, `gather` or another waiter
replaces the cancellation exception.

| State | Meaning | `batch` |
|---|---|---|
| `unbound` | The public coroutine has not entered | `None` |
| `running` | The call is still running, including owned cleanup or progress publication | Complete available records with `stop_reason="interrupted"`, or `None` |
| `succeeded` | The public call returned normally | Its actual batch, if any, preserving its stop reason |
| `failed` | The public call raised an ordinary error | Complete interrupted prefix, or `None` |
| `cancelled` | Cancellation propagated from the public call after its owned work ended | Complete interrupted prefix, or `None` |

A successful raw empty read retains its actual empty batch. A successful daily or
backfill call can retain a known empty source observation even when no delivery is
owed. Local wait/paused results have no batch. Available data never proves that a
progress write committed or that the receiver accepted a delivery.

`account_id` identifies the verified source for a retained observation. It is `None`
for stored replay or when no batch is available. `error_type` names the public
failure/interruption; `read_error_type` separately names the latest actual source
failure/interruption. They contain bounded type names, never exception messages or
tracebacks. Changing accounts after an empty attempt clears the previous source
metadata. These fields are observations, not health, retry or acknowledgment authority.

A capture binds once at coroutine entry, before argument-dependent I/O. Missing or
invalid captures refuse before I/O; attempting to bind an already-used capture also
refuses without altering its original data. A bound capture remains used after a
validation failure. Cancellation before the coroutine starts leaves it `unbound`.
If a shielded outer waiter is cancelled, the inner read may still be `running`;
the waiter's cancellation does not prove that the read has ended.

Only fully validated records are available, including completed downloads when media
is requested. An unfinished next message or download is excluded. Snapshot creation
copies the available batch on access; avoid repeatedly copying a large batch in a
tight loop. Retention is one current batch per capture under the existing
10,000-message limit, without a separate universal byte limit. Keeping older snapshots
is the application's memory responsibility. Drop references to release them. Captures
are in memory and do not add persistence across process death; durable progress stores
keep their existing replay guarantees.

## Preserve partial data and uncertainty

The first nonempty completed prefix ends failover. Ordinary source errors retain
their type/object and `partial_result`, plus safe `pool_account_id`/`pool_attempts`
metadata. Use the retained capture to obtain records independently of exception
identity, and handle those records before deciding to read again.

An internal timeout cancels and awaits its task. `PoolTimeoutError` carries any
complete interrupted prefix. If only internal health finalization was delayed after
the source finished, the actual result/error survives instead. A long flood wait
cannot become a short transport cooldown. The pool runs no application health callbacks.

Timeout is cooperative, not hard preemption of blocking code. No next account starts
while its predecessor's source task runs. Caller cancellation, including repeated
cancellation, waits for that task to end before propagating. If it interrupts an
admitted source, the account attempt remains unresolved. If it interrupts later
settlement, inspect the store: the write may already have committed. Already-known
complete records remain in the caller's capture. An exception's `partial_result` is
a convenience, not the cancellation-safe delivery channel. Cancellation starts no
new publication just to save a prefix. Uncertain quota charges remain. Local input/configuration/
media/format and unknown errors stop without failover.

An unexpected source-internal cancellation with no completed result raises a local
`PoolStateError` subtype, keeps any complete prefix and leaves account admission
unresolved. It does not silently cancel the caller or authorize another account.

Permission is saved before source work. Token-specific settlement records the outcome
and retires that permission. An uncertain admission starts no source; an unresolved
token never expires into fresh permission.

A failed pool-state settlement raises a local `PoolStateError` subtype. It may carry
complete records as an interrupted `partial_result`, and a source error separately as
`read_error`. It is not Telegram health evidence. Never treat a lost write response
as proof of rollback or automatically recreate pool state.

Daily/backfill publication failures retain validated complete records in the capture
and on the local error's `partial_result`; `read_error` retains an earlier source
failure when there was one. This interrupted batch is available data, **not a durable pending
receipt**. Its hash can differ from a successfully committed full batch because its
stop reason is interrupted. Reload/replay saved pending data and use its actual
receipt before acknowledgment. Backfill may confirm a non-admission write by reading
back the exact candidate state; an uncertain admission never uses that to start a read.

## Passive health observations

`AccountPool` rejects non-None `health_callback=`. Migrate application reactions to
`pool.drain_health_events()`, a synchronous local call returning
`{"events": [...], "dropped": N}`. Ordinary `TgData` health callbacks keep their behavior.

```python
capture = PoolReadCapture()
try:
    result = await pool.read(chat_id, capture=capture, after_id=500, limit=100)
finally:
    observations = pool.drain_health_events()
    snapshot = capture.snapshot()
# Your application owns handling health observations and the separately retained data.
```

Draining works while reading, while closing, in a caller's finally block and after
close. It returns detached plain event values captured so far and resets the buffer
and loss count. Later captures belong to a later drain. It does no source, store or
quota I/O. The pool neither awaits a consumer nor creates observer tasks or mirrors
these observations to the application health logger.

The health buffer retains at most 128 events, 4,096 encoded bytes per event and 65,536 total encoded
bytes (compact ASCII JSON). New events are dropped on overflow; malformed/capture
failures count as losses. `dropped` saturates at 2**63-1. Existing health event fields
include account/session identifiers, verdict/scope/request and wait/error type, never
credentials or message bodies. Keep labels free of secrets. These best-effort,
non-durable observations are not a complete audit, account permission or group ack.

## Use daily and backfill delivery

```python
await pool.initialize_sync(-1001234567890, after_id=500)  # deliberate enrollment
capture = PoolReadCapture()
batch = await pool.sync_group(-1001234567890, capture=capture, limit=100)
if batch is not None:
    await destination_accepts_durably(batch)
    await pool.acknowledge_sync(-1001234567890, batch.batch_id)
```

The [daily](daily_continuation.md) and [backfill](backfill_runs.md) contracts apply
unchanged to stored progress and acknowledgment. The pool's `sync_group` and
`prepare_backfill` additionally require a new capture on every call. For example:

```python
capture = PoolReadCapture()
turn = await pool.prepare_backfill(context, capture=capture)
if turn.batch is not None:
    await destination_accepts_durably(turn.batch)
    await pool.acknowledge_backfill(turn.delivery)
```

All state-only methods keep their signatures. Pending replay, valid
acknowledgment, control and status bypass account selection/state/credentials and
remain local after `pool.close()`. A source-error prefix is saved by the progress
engine before re-raising when publication succeeds. For backfill, replay to obtain
the complete scoped delivery reference; a bare batch hash is not sufficient.

Source/account work can finish before the public preparation finishes saving group
progress. Pool closure may therefore finish while publication remains active under
its caller. That call's capture stays `running` until the public call ends. Pool
closure, a final capture, a saved pending delivery and acknowledgment are different
facts; none substitutes for the others.

Account recovery cannot acknowledge or recover a group run. If both attempts remain
unresolved, each needs its own exact recovery after the old reader has stopped.
The caller still schedules one source reader per group across raw, daily, historical
reads and pool instances. Receiver acceptance and scheduling remain application duties.

Different accounts may see different history. Empty/end means history visible to
the selected account for this read. It proves neither a union of account histories
nor equal visibility. Old edits/deletions are not reconciled.

## Inspect, repair and recover

`get_pool_status(chat_id=None)` returns immutable stored facts and ledger eligibility
without authenticating. Supply a group to include its denials. `verified_at` is a
settled past identity observation, not a live certificate. Ledger status retains its
existing expiry/clock bookkeeping.

After repairing a stored login outside active pool work, call
`await pool.recheck_account(account_id)`. Known waits or unresolved attempts refuse.
It retires the old client, reloads credentials, repeats duplicate checks, durably
admits an identity-only check and verifies the expected account. Successful settlement
clears account repair flags, never group denials or quota. Failed retirement refuses reuse.

Recheck keeps the operation busy until the actual SDK disconnect attempt settles,
even if the caller is cancelled repeatedly. Successful retirement clears the old
client before cancellation reaches the caller, so a later operation loads a fresh
one. Ordinary disconnect failure or SDK-internal cancellation raises a local
`PoolStateError` with the failure type; it does not masquerade as caller cancellation.
That client remains unavailable until an explicit `recheck_account` or `close`
successfully retries cleanup. No read, authentication or replacement client is
allowed through the failed retirement. Pool status describes stored restrictions
and allowance; it does not certify the state of local client cleanup.

For an unknown attempt, actually stop and await the prior reader, then retain and submit:

```python
await pool.recover_account(
    account_id,
    attempt_id=saved_attempt_id,
    previous_reader_stopped=True,
    retry_not_before=explicit_aware_utc_datetime,
)
```

Choose the retry bound from the incident and your recovery policy. Quiescence cannot
reveal a wait whose response was lost. This bound is an operator assertion, not proof
of Telegram readiness. Recovery preserves longer known waits and repair flags. The
latest exact recovery is harmless to retry even with newer work; changed arguments
or unrelated tokens refuse. Only the latest recovery recognition is retained.

Use one owning process/event loop and trustworthy UTC. Clock regression refuses new
permission; same-process monotonic timing also protects known account waits. The store
is not a distributed lease. A process disappearing does not establish another worker's
quiescence automatically.

`close()` blocks new pool source/control work, stops the active owned invocation,
waits for its completion and retires every client. It does not await the containing
application Task or consume its result. Application cleanup after the library call
ends can continue independently, including waiting for that close to finish.
Calling it from a live same-pool operation/provider scope refuses before changing
flags, including inherited child-task calls. Expired and foreign-pool scopes do not
block ordinary application control.
Cancellation of close waits for the owned invocation and cleanup attempts to settle, then
propagates; another close while this is pending refuses busy. A failed or cancelled
close is not proof every retirement succeeded; retry cleanup as needed. The pool
stays closed to new source work. There is no shutdown deadline for SDK work that
does not finish. Async context exit preserves an existing body exception when
ordinary cleanup fails; caller cancellation during cleanup takes precedence after
settlement. State-only progress methods
remain usable; their own callers retain any outstanding storage work. Close owns
source/account activity, not every independent progress/status task in the application.
Source reads on a closed pool refuse.

## Offline demonstration

```bash
python examples/account_pool.py --demo
python -m tgdata.smoke_tests.test_31_account_pool
python -m tgdata.smoke_tests.test_39_pool_lifecycle
python -m tgdata.smoke_tests.test_40_pool_outcomes
```

The demo opens no Telegram sockets and reads no real config. Test 31 exercises routing,
identity, real overlapping tasks, native teardown, uncertain writes and process exits.
Test 39 adds 48 lifecycle groups, including cancellation before/after actual commits,
held provider finalization, available data versus pending delivery, exact recovery,
provider control refusal and bounded passive observations. Test 40 adds 25 groups
for early and final captures, one-shot binding, wrappers and late observers,
post-call application cleanup, progress publication after close, exact receipts,
paired store failures, attempt metadata and completed media retention. Delayed finalizers and
wire replies are explicit test instrumentation. Tests run on Python 3.11/Telethon 1.45;
Python 3.7 grammar checks are not a native 3.7 run. These are not disk power-loss or
live-account tests.
