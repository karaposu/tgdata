# Reading worker, protocol v1

`tgdata-worker --config worker.json` (also `python -m tgdata.worker`) runs a
resident, serial worker on stdin/stdout. Each job explicitly selects one account.
The worker returns raw message batches, group observations and account health.
Your application schedules jobs, stores results, manages progress and decides
when to retry. This first interface targets trusted, caller-managed processes on
a laptop or server; it has no HTTP listener or automatic account routing.

The worker requires **Telethon 1.45.0**. Install that version explicitly alongside
tgdata; ordinary library compatibility is unchanged. Offline qualification uses
Python 3.11.10 and POSIX processes on macOS. Python 3.7 grammar is checked, but
native Python 3.7, Windows signal behavior and live Telegram operation have not
been qualified by these worker tests.

## Prepare an inventory

Log accounts in separately, and assign each session exclusively to this worker
until it stops. Account IDs are the numeric Telegram user IDs, independent of
session filenames and cached identity. Each account uses its existing INI file,
proxy, device identity and session. Prefer absolute `session_file` paths in INIs.
No job may supply credentials, a proxy, a file path or a replacement allowance.

Provision read policies outside the worker using [ReadBudget](../README.md#per-account-read-budgets).
Provision [JoinBudget](join_budget.md) separately when joins are needed:

```python
from tgdata import ReadBudget, JoinBudget

# Explicit operator setup. Choose allowances appropriate to these accounts;
# the numbers below are illustrative, not a Telegram-safe rate recommendation.
ReadBudget('/srv/reader/read.sqlite3').configure(123456789, 100)
JoinBudget('/srv/reader/join.sqlite3', create=True).configure(123456789, 1)
```

Do not repeat policy setup inside job submission or worker startup. Existing
policies, warm-up rules, reservations and charges remain authoritative. Reuse
the shared ledger if another authorized component has already provisioned it.

`worker.json`:

```json
{
  "version": 1,
  "worker_id": "laptop-reader",
  "read_budget": "read.sqlite3",
  "join_budget": "join.sqlite3",
  "accounts": [
    {"account_id": "123456789", "config_path": "account.ini", "label": "reader-one"}
  ]
}
```

The manifest accepts these keys and the optional `media_directory` described below;
`join_budget` and account `label` are optional. `worker_id` is 1–64 ASCII letters/digits/`_`/`.`/`-`, starting with a
letter or digit. Labels are at most 128 characters. Account IDs are canonical
positive decimal strings up to signed 64-bit maximum. Duplicate IDs, config
paths and known shared session addresses are refused. This is local validation,
not a cross-process lock: the caller must prevent two owners using one session.

Paths in the manifest are relative to the manifest directory. INI session paths
keep ordinary tgdata semantics: a relative file session is relative to the
worker's starting directory, and the worker pins that resolved path at startup.
Store session keys are opaque names and are not resolved as paths. There is no
`<session>_1` pool: each job uses one temporary client for its selected account,
with authentication/retry policy configured before connecting and a fresh check
that its authenticated ID matches the declared account. No login code is requested.

The read ledger file and a read policy for every account must already exist.
An optional join ledger must already exist; its account policy is checked by the
join operation when needed. The worker never configures or resets either budget.
An absent join ledger disables join jobs before opening a client. Startup reads
local configuration only; it does not connect or establish that accounts are healthy.

Limits: manifest 1 MiB, 1,000 accounts (an empty inventory is allowed), input line
16 KiB including newline, 1,000 messages per read, output frame 64 MiB including
newline, 256 health events per job and 8 KiB per collected health event. These are
resource bounds, not Telegram pacing recommendations.

## Submit jobs

Use one UTF-8 JSON object per LF-terminated line. CRLF is also accepted. Duplicate
keys, non-finite constants, unknown fields and invalid types are refused. Drain
stdout while the process runs; stdout contains protocol frames only.

```json
{"version":1,"request_id":1,"account_id":"123456789","operation":"read_batch","params":{"group_id":"@example_group","after_id":"100","limit":20}}
{"version":1,"request_id":2,"account_id":"123456789","operation":"lookup_group","params":{"target":"@example_group"}}
{"version":1,"request_id":3,"account_id":"123456789","operation":"check_group_access","params":{"target":"@example_group"}}
{"version":1,"request_id":4,"account_id":"123456789","operation":"join_group","params":{"target":"https://t.me/+EXAMPLE_INVITE"}}
```

These illustrate separate explicit jobs. Sending the fourth performs a real join
attempt when the account and allowance permit it. Reading and looking up never join.

`request_id` is a JSON integer from 1 through 9007199254740991, strictly increasing
within one process. A recognized version plus fresh valid request ID consumes that
ID even if the rest of the job is refused. Earlier or duplicate IDs are rejected.
This bounded high-water mark is **not durable idempotency**. IDs may restart in a
new process, which has a new `instance_id`; the application must not replay an
uncertain job merely because the new process accepts the same number.

| Operation | Parameters | Result |
|---|---|---|
| `read_batch` | `group_id`; optional `after_id` (default `"0"`), `limit` (default 200), paired `start_date`/`end_date`, `download_media` (default `false`) | Unchanged MessageBatch v1; references by default, downloaded file descriptors when enabled |
| `lookup_group` | `target` | Qualified group details, including invite previews |
| `check_group_access` | `target` | `readable`, `denied` or `unprobed`; a real history probe costs read allowance |
| `join_group` | `target` | `joined`, `already_joined`, `requested`, `payment_required` or `interaction_required` |

`after_id` is a canonical decimal string in 0..2147483647. Date boundaries must
both be supplied as timezone-aware ISO timestamps (for example
`2026-10-01T00:00:00Z` and `2026-10-02T00:00:00Z`); the existing batch contract
uses a start-inclusive, end-exclusive window. The worker does not resolve or
persist relative windows such as “last 30 days”.

Group targets use the [existing strict reference grammar](group_operations.md):
usernames, supported Telegram group links and canonical negative peer IDs. Use
decimal strings for IDs in JSON. Read resolution is bounded: an uncached private
channel ID without its access hash is refused, and an invite preview alone cannot
be read. The worker does not scan all dialogs/contacts to resolve an ID. A usable
public handle or a group already cached in that account's session supplies the
required reference. Ordinary library batch resolution keeps its previous behavior.

Membership and readability are different facts. A join request awaiting approval
is not membership; successful membership is not proof that history can be read.
See [group joining](group_joining.md) for qualified results, conservative claim
accounting and interactive/payment outcomes that the worker does not complete.

## Download attachments on the worker machine

Add a trusted output directory to `worker.json`:

```json
"media_directory": "media"
```

This is a local configuration field, never a job parameter. Relative paths resolve
against the manifest's directory and are pinned at startup. Omission or `null`
disables media downloads. A nonempty path string is required when enabled; an
existing non-directory or malformed path produces `invalid_config` with field
`media_directory`. A missing directory is permitted. The existing batch reader
creates it and its parents on the first media-enabled read; startup and
references-only reads do not create it. Directory permissions and later filesystem
changes can still cause local operation errors when a read uses it.

Then submit a read with the strict boolean `download_media` option:

```json
{"version":1,"request_id":1,"account_id":"123456789","operation":"read_batch","params":{"group_id":"@example_group","after_id":"100","limit":20,"download_media":true}}
```

Omitting the flag or using `false` preserves references-only behavior. Strings,
numbers and `null` are not booleans and are refused. A media-enabled read without a
configured directory returns `media_disabled` before opening a client or spending
read allowance. All three other operations remain target-only. Job paths, including
`media_directory` or `download_media_to`, are rejected as unknown parameters.

The worker uses the existing **sequential** batch downloader. Successful `data`
has `media_mode: "download"`; each supported downloadable photo/document/video
contains a `media.blob` with `sha256`, `size` and `path`. The path is the hash
basename under the configured directory. No media bytes or absolute output root
are embedded in the reply. Non-downloadable messages retain their normal records.

On download failure, `ok` remains false and `partial_result`, when available,
contains only completely prepared messages before the failure. Its `next_after_id`
never advances past the failed attachment. Validate the payload using
`MessageBatch.from_json(json.dumps(frame["data"]))` (or `partial_result`); this
checks the batch representation, not the files. Verify local file sizes and hashes
separately when receiving/uploading them. Local filesystem failures are not Telegram
health events; the existing source, budget and cleanup policies remain in force.

Completed files stay on disk after success, partial failure, result-delivery
failure and worker exit. Your relay owns upload and eventual deletion. A hash may
be referenced by several messages or jobs: delete it only after every dependent
delivery no longer needs it. The worker has no upload acknowledgment, durable file
inventory or automatic garbage collector. Temporary incomplete artifacts follow
the reader's existing cleanup behavior. Cancellation keeps the existing worker
contract; it does not promise a terminal partial-result reply.

Batch identity includes media mode and blob descriptors. The same messages read
with media off and on therefore have different `batch_id` values. Keep the relay's
chosen media mode consistent and use the returned identity. Files on disk do not
prove that a result reached the relay or that the destination accepted an upload.

For a trusted Python bootstrap, pass `media_directory` to `serve` (or `Worker`)
as a text path or `Path`; a relative path resolves against the startup working
directory. It is still configuration, never part of a submitted job.

## Read replies

Startup emits one `ready` frame with `version`, `worker_id`, a fresh `instance_id`,
`state: "idle"`, account IDs/count and protocol limits. Thereafter a job emits zero
or more `health` frames followed by one `result` frame, if output remains usable.
Each includes `version`, `worker_id`, `instance_id`, `request_id`, `account_id` and
`operation`. Invalid input can leave unrecognized correlation fields null.

A result contains:

```json
{
  "version": 1,
  "kind": "result",
  "worker_id": "laptop-reader",
  "instance_id": "a-fresh-process-identifier",
  "request_id": 1,
  "account_id": "123456789",
  "operation": "read_batch",
  "ok": false,
  "data": null,
  "error": {"category":"telegram_error","type":"FloodWaitError","code":420,"wait_seconds":7200},
  "partial_result": null,
  "health_dropped": 0,
  "worker_stopping": false
}
```

On success, `data` contains the operation result and `error` is null. A read that
fails after collecting a prefix returns its complete valid MessageBatch in
`partial_result`. It still has `ok: false`; honor the failure and do not conceal
the wait by continuing immediately. Validate batches using `MessageBatch(data)`
or `MessageBatch(partial_result)`. Batch IDs, message IDs, dates and hashes are
unchanged by the worker envelope. This interface does not acknowledge or advance
daily/backfill progress for the caller.

Group, health and error identifier fields are decimal strings, including large
bot/query IDs. Counts, booleans and request IDs retain their normal JSON types.
Do not cast identifiers to a JavaScript `Number`. Health frames put the plain
event in `event`; delivery is bounded, and `health_dropped` counts collected events
that could not be delivered. Health is observation, not the source result. The
worker uses its own collector, with no caller callback able to replace a result.

Errors contain a category and exception type, plus selected fixed metadata such
as budget status, expected/actual account IDs or wait seconds. They never include
raw exception messages, reprs or tracebacks. Categories include `worker_error`,
`operation_error`, `authentication_required`, `identity_mismatch`, `allowance_error`,
`group_error`, `configuration_error` and `telegram_error`. Local refusal codes
include `unknown_account`, `unknown_operation`, `stale_request_id`,
`invalid_parameters`, `join_disabled` and `media_disabled`. Treat unknown categories/types as errors.
Authentication errors retain boolean `first_login` and `banned` flags. A `reason`
appears only for a recognized SDK authentication code, such as `SESSION_REVOKED`
or `AUTH_KEY_UNREGISTERED`, or an existing banned-account code. Unknown Telegram
text is omitted even when it looks like a code. The same rule applies to terminal
errors, `delivery_failed.source_error` and fatal diagnostics. Ordinary library
`AuthRequiredError.reason` values are unchanged.

Successful message/group data and intended health labels still contain application
data: this sanitization does not make protocol output public or suitable for logs.

All job frames are encoded before any are published. A result exceeding the frame
limit or failing serialization yields a small `delivery_failed` error with
`source_outcome`, safe `source_error` or `source_result_type`, `partial_omitted: true`,
and `worker_stopping: true`. Qualified group `source_status` is retained when
available. No prefix is silently truncated or turned into an empty success.
Already-spent read/join allowance is retained. Such a reply is not a delivered batch.

## Process lifetime and uncertainty

The worker runs one job at a time and finishes its native client cleanup before
publishing the reply or admitting another job. It configures temporary clients
with no hidden SDK retry/wait policy. It has no internal queue, job timeout,
automatic rerun or durable “accepted” frame. Pipe buffering is not job acceptance.

A native cleanup failure preserves the known source result/error but makes
`worker_stopping` sticky. The worker then settles remaining loop tasks and exits;
it never starts the next submitted job. A failed cleanup is not reported as a
successful disconnect, nor does it overwrite a completed read or join outcome.

| Condition | Behavior / exit code |
|---|---|
| EOF between complete jobs | Finish an active job/reply, close, exit 0 |
| Malformed complete line | Local error, continue when the frame is recoverable |
| Truncated final line or oversized input | Do not execute that line; stop, exit 2 |
| Invalid startup | Safe `fatal` frame when possible; exit 2 |
| Cleanup failure or result serialization/size failure | Preserve known outcome when possible, stop, exit 3 |
| Broken/failed stdout | Stop immediately, no second output channel/retry, exit 3 |
| SIGINT / SIGTERM | Freeze admission, cancel active work once, await owned cleanup, exit 130 / 143 for the first signal |

The first stop signal wakes an idle event loop even while a Telegram request is
waiting without network activity. A stop received before a submitted job starts
prevents that job from opening a client. Repeated signals preserve the first exit
reason and do not abandon client cleanup or final process cleanup. Idle input or
blocked output can be interrupted without waiting for stdin EOF or stdout drain.
Output uses the raw binary stream, leaving no protocol bytes for Python to retry
flushing during interpreter exit. There is no graceful-shutdown time limit:
supervisors decide when to force-kill and must then treat completion as uncertain.

A missing, partial or unparseable terminal reply means **unknown completion**. A
source operation or join may have happened and its allowance may have been spent.
Do not infer rollback from an exit code or resubmit a join automatically. Check the
account/group state through a later explicitly chosen operation. Even a complete
reply is not proof that your destination stored the messages; commit those and
manage continuation/acknowledgments in the application.

## Caller and session-store examples

Run the provided caller from an installed package environment:

```bash
python examples/reading_worker.py --demo
python examples/reading_worker.py --config worker.json --account 123456789 \
  --target @example_group --after-id 100 --limit 20
python examples/reading_worker.py --config worker.json --account 123456789 \
  --target @example_group --after-id 100 --limit 20 --download-media
```

The offline demo uses an empty inventory and a new temporary ledger. It demonstrates
ready, a local unknown-account refusal and EOF; it does not simulate an SDK read.
Normal mode drains correlated health frames before the result and prints it.
It neither saves messages nor retries. `--operation` can explicitly select another
verb; selecting `join_group` authorizes that real operation for the supplied target.
`--download-media` is valid only with `read_batch` and uses the worker-configured
directory; the example does not upload or delete the downloaded files.

For store-backed sessions, use trusted Python setup in a **dedicated process's
main thread**, outside any running event loop:

```python
from tgdata import ReadBudget, JoinBudget
from tgdata.worker import WorkerAccount, serve

# store is your existing synchronous load(name)/save(name, opaque_text) store.
# Set up access control/encryption there; keep its methods quick.
account = WorkerAccount(123456789, '/srv/reader/account.ini', session_store=store)
raise SystemExit(serve([account], worker_id='database-reader',
    read_budget=ReadBudget('/srv/reader/read.sqlite3'),
    join_budget=JoinBudget('/srv/reader/join.sqlite3', create=False),
    media_directory='/srv/reader/media')))
```

`serve` owns an event loop, returns the exit code, and restores logging/signal state.
The bootstrap must exit with that code. Its optional `input_stream`/`output_stream`
are binary; output must be unbuffered. A standard buffered binary output is unwrapped
to its `.raw` stream. Do not add another buffering writer or print to protocol stdout.
Worker CLI logging is disabled; sanitized protocol diagnostics are authoritative.

Offline suites37/38 use actual Telethon, SQLite, native disconnect tasks and real
process pipes with synthetic transport and blocked sockets. Their 33 and 25 test
groups cover all verbs, ownership, charges, partial results, exact IDs, SDK-decoded
authentication errors, quiet request cancellation, stops around job creation,
retained cleanup and process failures. Held cleanup is released explicitly by the
test parent; no child polling timer supplies progress. This is not live qualification
or evidence that two machines may share a session safely.

`python -m tgdata.smoke_tests.test_49_worker_media` covers opt-in media with actual
worker/SDK reads, local files and SQLite, plus CLI subprocess configuration and
JSON replies. Wire responses are synthetic and external sockets are forbidden.
A live check requires separate authorization for an existing account/group and a
bounded read. These tests do not qualify new concurrency or repair the separate
auxiliary connection-lifecycle issues.
