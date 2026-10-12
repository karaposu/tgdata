---
model: gpt-6-astra
effort: max
---
# Implementation plan — #10 reading-job worker

**Critic folded:** 2026-10-11 — 2 robust mitigations (5 steps changed,0 added).
Mandatory prebuild PASS before product edits:7 actual source histories,6 cleanup
cases and4 real pipe controls; see `critic.md` and `probes/prebuild.txt`.

Revision2. Input: `desc.md` at `faa2f18`; design finding at `e8bf7f0`.
Base: dev `68f6bbd`. #17 is neither merged nor a runtime dependency.

### What is the task

Expose the accepted library operations through a small resident caller-managed
process. Explicit-account jobs perform bounded reading, lookup, access checks or
joining and return exact results/health observations. Keep scheduling, account
assignment, receiver acceptance and uncertain-result recovery with the caller.

### Huge Hard Blockers

#### Planning Blockers

None identified. The actual owned operation + BatchEngine + health composition,
cleanup-failure receipt under cancellation, OS pipe pitfalls and Node identifier
round trips were probed before this plan. The stated initial transport is JSON
lines over stdin/stdout; no answer to the optional preference question has arrived.
This is an explicit selectable first-delivery design, not a claim about an unknown
consumer contract. A later explicit HTTP request would change the transport scope.

#### Execution Blockers

None for these seven offline implementation steps. Live deployment qualification
requires separately approved logged-in account/group access, exclusive sessions
and bounded existing allowance; it is outside this delivery, not a hidden final
step or permission to reuse earlier live tests.

### How this implementation moves toward desired state

Define a small strict wire contract, adapt existing verified source operations,
then give a serial process ownership of admission and output. A private cleanup
receipt prevents unsafe continuation without changing existing library results.
Actual subprocess/SDK tests qualify the composition before packaging/documentation
are declared complete. No queue, router, login or new quota engine is introduced.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Strict values, request decoding and result projection | Versioned finite protocol with exact IDs and safe errors |
| 2 | Owned job execution and cleanup-failure feedback | Four jobs using accepted account/group/batch/ledger mechanisms |
| 3 | Serial process, inventory loader and CLI | Resident stdin/stdout worker with explicit stop/EOF behavior |
| 4 | Actual SDK and subprocess qualification | New worker suites covering source and process failure histories |
| 5 | Public contract and caller example | Usable configuration, job, retry and shutdown documentation |
| 6 | Full offline/package verification | Measured supported regressions, compile/grammar and isolated invocation |
| 7 | Commit and publish implementation evidence | Separate product/work commits and honest issue status |

## Fixed first-delivery contract

### Source and configuration

Require Telethon exactly1.45.0 for this opt-in worker; ordinary library requirements
stay unchanged. Add `WorkerAccount(account_id, config_path, *, session_store=None,
label=None)` as a frozen trusted-Python inventory value in `worker_engine.py`.
IDs are positive signed64 integers excluding bool; paths/labels validated and
credentials/config paths excluded from repr/errors. File sessions are the CLI
default; Python bootstrap may supply a session-store object without any import or
credential selection in job data.

`Worker(accounts, *, worker_id, read_budget, join_budget=None)` owns its TgData
instances, constructs them with `connection_pool_size=1`, `interactive_login=False`
and a fixed event collector, and never initializes a persistent connection/pool.
Required ReadBudget is the caller's existing object; optional JoinBudget enables
join jobs but its per-account policy still applies at the accepted send boundary.
No configure/reset call belongs in worker execution.

CLI: `python -m tgdata.worker --config worker.json` and installed `tgdata-worker`.
Manifest exact fields: `version:1`, `worker_id`, `read_budget`, `accounts`; optional
`join_budget`. Accounts are objects with `account_id` as canonical decimal string,
`config_path`, optional `label`; unknown keys refuse. Maximum manifest1MiB,
inventory1000 accounts; zero accounts allowed for a local protocol-only demonstration.
Paths in the manifest resolve relative to its directory. INI session naming retains
existing library behavior (relative names resolve from worker cwd); document absolute
session paths for relocation. Pin that resolved file path once for file-backed
worker clients; custom store names remain opaque. Reject duplicate IDs, config
paths and known file/store session addresses locally. Do not read credentials or
open SDK clients merely to report ready.

CLI read-budget path must exist, and every configured account must have an existing
read policy. Opening may perform the ledger's existing schema/clock/expiry bookkeeping;
it never creates an account policy or erases usage. JoinBudget reopens with create=False;
join policy is checked only by a join job. Config/session/proxy failures are type-only
local diagnostics. No live account resource is needed for tests or examples.

### Requests and replies

UTF-8 JSON objects, one complete LF-terminated line per request. Maximum request
16KiB including LF; CRLF accepted. Reject duplicate keys, nonfinite numbers, invalid
UTF-8 and unknown fields. Maximum nesting is bounded by the frame and the fixed
schema; parser recursion/value errors become local protocol failures.

Request fields exactly `version`, `request_id`, `account_id`, `operation`, `params`.
Version is integer1 excluding bool. request_id is integer1..2^53-1, strictly greater
than the last accepted envelope ID in this process; gaps are allowed, no wrap or
reset. A recognized fresh ID is consumed before argument/source processing, including
a subsequent invalid operation/argument outcome. Malformed envelopes without a valid
version/ID consume none. Reused/old IDs refuse without work. IDs are correlation and
process-local duplicate protection, not durable idempotency across process restart.

account_id is a canonical positive decimal string identifying inventory. Operations:

- `read_batch`: params `group_id` (nonempty reference string or canonical integer),
  optional `after_id` (canonical decimal string0..MAX_MESSAGE_ID, default"0"),
  `limit` (integer1..1000, default200), and paired aware ISO `start_date`/`end_date`.
  Validate the existing date-window/batch argument rules before a source context.
  Use the accepted group reference parser for the target and the bounded worker
  resolver below; no arbitrary SDK string/phone resolver or dialog/contact scan.
  This first worker protocol returns reference-mode media; file downloads remain
  available through the library and are not an extra worker verb or arbitrary path.
- `lookup_group`, `check_group_access`, `join_group`: params exactly `target` as a
  supported string or canonical integer; validate with existing group reference
  rules before client creation. Join without configured JoinBudget is locally
  disabled before authentication. No hidden retries, joins or dialog warm-up jobs.

Ready frame: `version`, `kind:"ready"`, `worker_id`, `instance_id` (new opaque process
identity), `state:"idle"`, account IDs/count and documented protocol limits. Ready
means configured/idle, not authenticated or Telegram-healthy.

Health frames: `version`, `kind:"health"`, worker/instance/request/account IDs and
the plain event. Terminal frame: same correlation, `kind:"result"`, `operation`,
`ok`, `data` or `error`, `partial_result` (batch dict or null), `health_dropped`,
`worker_stopping`. Preserve all GroupAccess/GroupJoin status meanings. Identifier
fields become decimal strings in group/health/error projections; counts/booleans
keep their types. Raw MessageBatch.to_dict and batch_id are unchanged.

Errors include fixed category, exception type, and bounded safe fields when known:
auth reason/first_login/banned, identity expected/actual IDs, allowance retry/status,
and Telegram error name/wait seconds/code. Never use raw exception strings, repr,
traceback, raw request payload or credential/config contents. Unknown exceptions
remain explicit `operation_error` with type only; no guessed health or retry.

Health collection cap256 per job, dropping excess with an explicit count; notification
collection must never fail the source. Serialize a complete frame before writing,
with a64MiB encoded-frame ceiling and no silent truncation. If a source outcome cannot
fit or serialize, emit a small explicit delivery-error terminal frame with safe source
outcome/error metadata and `partial_omitted:true`, then stop. Never present an empty
batch/success or acknowledge omitted data. Closed/failed output may prevent even that
frame; exit with unknown caller receipt. This is a transport limitation, not a source
retry or quota refund. Build bounded bytes incrementally and check size before write.

### Lifetime and stopping

One job at a time, no internal pending-job queue. Do not read/admit the next frame
while a source job or its output is active. Keep one worker-owned event loop for
async source work; synchronous binary input/output runs only outside active source
work. No executor stdin thread and no user callback performing protocol writes.

No new automatic job timeout. Accepted owned clients already disable retries/long
flood sleeps; caller-controlled process cancellation handles an unresponsive job.
SIGINT/SIGTERM set a stopping flag. During active work cancel its task once and
wait for the existing owned cleanup; repeated signals do not break that wait or
start another job. During idle input/output interrupt the blocking operation and
exit. A hanging cleanup has no hard deadline; supervisor hard termination leaves
completion unknown. EOF after a completed request permits its result before exit;
an incomplete final line is not executed. Fatal oversized/truncated frames stop,
while a complete malformed JSON/envelope can produce an uncorrelated local error
and continue. No input/result receipt is called durable acceptance.

Exit0: normal EOF. Exit2: startup/fatal protocol error. Exit3: cleanup/serialization/
output failure requiring stop. Signal exit128+signal. Per-job source errors do not
exit the worker unless cleanup/transport is unsafe. Restore signal handlers and
close the owned loop; bootstrap callers must exit the dedicated process with the
returned code. Never imply failed SDK cleanup guarantees successful connection close.

## Step 1 — Protocol and trusted values [folded: Risk1, robust]

### Proposed changes

Add `tgdata/worker_protocol.py` for constants, safe WorkerError taxonomy, duplicate-key
decoding, exact request parsing, canonical identifier conversion and JSON-ready
frame projection. Use a small immutable parsed-job value; no global registry or
mutable raw payload retained across admission. Explicit operation allowlist and
parameter schema; no getattr dispatch from untrusted names. Validate all local
arguments before a source task. Read targets use the same accepted `_parse_target`
rules as group jobs, rather than arbitrary nonempty SDK strings. Preserve errors' real categories without exposing
their text; recursively project only known identifier fields and leave batch dicts
as their existing schema. Bound diagnostics and serialization; optional error metadata
must not replace an original source outcome if inspection itself fails.

### Output

An explicit protocol contract implemented as local pure validation/projection.
### Safe in nature
True — additive module; no existing path changed.
### Peripheral concepts
MessageBatch v1, GroupAccess/GroupJoin values, auth/budget errors, JSON integer precision.
### Hardness Lvl
4

## Step 2 — Owned source execution and cleanup evidence [folded: Risk1, robust]

### Proposed changes

Add `tgdata/worker_engine.py` with WorkerAccount, Worker and a private bound-session
adapter whose async session yields the current verified operation.client in its
opening task. Build a BatchEngine over that adapter inside `_account_health_operation`
for read jobs. Add an optional private `_resolve_entity` hook to BatchEngine's
constructor; when absent, retain the exact current get_entity/dialog-sync fallback.
The worker hook calls the merged group `_resolve` on its parsed target and verified
operation, refuses missing peers/unsupported community reads, retrieves the resulting
InputPeer entity with the SDK and verifies its canonical ID equals the lookup's.
Never enumerate dialogs/contacts or join to resolve a worker read. A private channel
ID needs its account-specific cache or a usable public/invite reference; uncertainty
is an explicit GroupReferenceError. The prebuild exercises this actual composition,
including the unchanged default branch. Successful actual history answers may confirm group access; do not
claim access recovery for the MAX_MESSAGE_ID shortcut or metadata-only work.
Dispatch the three group jobs to existing public methods with the configured account.

Implement the tested private cleanup-feedback seam: `_disconnect_owned(client,
failures=None)` appends the failure type to the trusted optional receipt BEFORE
diagnostics/caller cancellation. `ConnectionEngine` starts with no cleanup failure;
its `_account_operation` uses a local receipt and records a sticky
`_account_cleanup_failure` in finally even when cancellation or setup failure escapes.
Do not alter existing return/error/logging precedence or ordinary connection policy.
No public failure callback, new supervisor or credential-generation protocol.

Worker validates read policies/config addresses locally, keeps one fresh-source
TgData per configured account and uses no primary client/pool. A ContextVar carries
the immutable job collector into owned notification tasks. Callback appends bounded
plain events only; no application/network/output callbacks. After the operation
ends, drain its owned notification tasks under the same bounded trusted collector,
then construct health and terminal frames. Retain a completed value/error before
notification/projection work. Actual caller cancellation stops the worker; it is
never recast as a retryable source error. Any cleanup failure makes worker stopping
sticky before a terminal result is handed to the process; future execute calls refuse.

### Output

All four operations use verified existing mechanisms and produce correlated outcomes.
### Safe in nature
False — shared owned cleanup gains a private observation path; correctness is delicate.
### Peripheral concepts
AccountOperation lifetime, same-owner quota claims, deferred health, partial batches, join guard.
### Hardness Lvl
5

## Step 3 — Process driver and package entry point [folded: Risk2, robust]

### Proposed changes

Add `tgdata/worker.py` with strict bounded manifest loader, `serve(...)` for trusted
Python bootstrap with session-store objects, and CLI main/argparse. Export worker
types from the worker module, not the package root (avoid eager new import cycles).
Add the console script in setup.py; `python -m tgdata.worker` shares the exact path.

Own one loop and signal state on the main thread; reject running inside another
active event loop. Ready before request input; binary bounded readline, single job
task and one complete-frame writer. Write-all handles short writes; failed/closed
output stops immediately and never admits another job. The CLI uses unbuffered
output (raw descriptor/raw binary stream), leaving no worker bytes in Python's
stdout buffer for interpreter-finalization retries. Normalize a standard buffered
bootstrap stream to its raw stream or require a genuinely unbuffered supplied one;
do not flush/retry protocol output during teardown after a failed/interrupted write.
Retain pre-encoding, size bounds and write-all semantics. Real pipe controls showed
buffered exit120 and a final-flush wait, versus raw exit3/143 without drain.
CLI disables library/SDK
diagnostic logging to avoid contaminating stdout or exposing failure text; own
startup/fatal diagnostics contain types/codes only. Restore the embedding process's
logging/signal state before returning its exit code. The documented bootstrap is a
dedicated process entry point and exits with that code.

On EOF/normal completion close source-free facade state and notifications. On unsafe
cleanup, do not try another source or claim recovery; finish the bounded known reply
when possible and terminate the process. Source clients are temporary; the SDK
cleanup attempt has already settled, and final process exit ends remaining resources.
Do not add multiprocessing children, executor readers, HTTP listeners, polling or
automatic rerun. Keep request counters and collectors bounded for an unlimited
number of sequential jobs.

### Output

A resident worker command with deterministic request/exit behavior and no live defaults.
### Safe in nature
False — process I/O, signal and packaging behavior is new; must test actual processes.
### Peripheral concepts
Binary pipes/files, event-loop ownership, signal cancellation, backpressure, config/ledger paths.
### Hardness Lvl
5

## Step 4 — Source and process tests [folded: Risk1, robust; Risk2, robust]

### Proposed changes

Add test_37_worker.py for protocol/engine composition and test_38_worker_process.py
for real subprocess CLI histories. Use actual factory/SDK/SQLite with synthetic wire;
test child bootstrap may replace only transport fixtures, never Worker execution or
the behavior being qualified. Block sockets. Keep fixture hooks out of production
arguments/protocol. Include process watchdogs and explicit cleanup for test resources.

Cover: all four verbs; two configured expected accounts and stale cache; wrong actual
identity before any group/join/charged read; no login code; proxy/device/settings;
read and join denial/retained charges; qualified join/access statuses; original
RPC/local error and complete partial batch; large IDs through JSON/Node-style consumer;
malformed/unknown/duplicate fields, IDs and operations; argument validation without
source; missing/bad manifest/config/ledger and known session alias; custom session
store bootstrap; exact MessageBatch hash round trip; source-free ready/empty inventory;
fixed-window read and maximum-cursor no false recovery; bounded health/drop disclosure.
Include valid handle/cached ID, uncached private ID and invite-preview read refusal;
assert no GetDialogs/GetContacts/Join/Import requests in worker resolution, and
retain a control proving ordinary BatchEngine default fallback remains unchanged.

Lifetime histories: successful/body-failed/setup-failed operation plus native cleanup
failure; SDK-internal cancellation; repeated caller cancellation; broken diagnostics;
sticky refusal of the next job; observer/source separation and stable job correlation;
actual EOF after a job, truncated/oversized line, multiple requests and old IDs;
SIGINT/SIGTERM idle and active with a held native disconnect; repeated signals;
broken/slow stdout after a source result; no second source while output is blocked;
raw-output broken-reader exit3 with no shutdown warning; SIGINT/SIGTERM under
backpressure exits without first draining the still-open pipe, with no final flush;
response size/encoding failure with explicit omission and no false empty success;
unrelated ordinary library semantics. Prove actual charges, requests, outcomes and
task/client settlement, not just a mocked method call count.

### Output

Measured offline worker suites and retained failure histories without Telegram use.
### Safe in nature
True — tests own temporary files, processes and synthetic data.
### Peripheral concepts
Existing tests19/32–36 fixtures, real pipes, lost replies, SQLite policies, SDK tasks.
### Hardness Lvl
5

## Step 5 — Public docs and example [folded: Risk1, robust; Risk2, robust]

### Proposed changes

Add docs/worker.md with the complete manifest/request/frame/exit contract and examples
for four operations, allowance provisioning outside startup, absolute session paths,
trusted Python bootstrap/session stores, output draining, partial results, exact IDs,
lost reply/uncertain join handling, cleanup-stop policy, platform/runtime qualification
and no live claims. README and smoke-test README link it and record measured suites.
Explain bounded read resolution and the cached-ID/reference requirement; an uncached
private group does not trigger global discovery. Document raw/unbuffered bootstrap
output and the rule that interrupted output is not retried during teardown.
Add examples/reading_worker.py as a caller that reads ready/health/result correctly;
provide an explicitly offline demo and normal supplied-config mode. Example defaults
never read project credentials, request login, join or reset an existing allowance.
No work-folder dependency in runtime or examples.

### Output

A usable documented process interface and runnable caller demonstration.
### Safe in nature
True — docs/example additions.
### Peripheral concepts
Consumer persistence, exclusive assignment, job correlation, process supervision, partial delivery.
### Hardness Lvl
3

## Step 6 — Verify integrated behavior and packaging

### Proposed changes

Run new37/38 first, then supported offline12–19,22–30,32–36 (22 existing suites;
573 actual prior passes and3 explicit live skips) plus new suites. No test31 because
#17 is absent from dev. Pass an intentionally missing config to legacy12/13 to keep
their live checks skipped, and count skips separately. No live join/login/read.

Compile all product/examples/setup and check Python3.7 grammar under actual3.11.10.
Run the offline caller demo and existing daily/new/restarted-backfill examples.
Build/install a package or equivalent isolated export without Git/devdocs and verify
the module/console entrypoints and worker protocol from there. Review signatures,
scoped diff/whitespace, no dependency on work docs or unmerged #17, and unchanged
library behavior. Required process fault cases must be actual subprocess runs.

Small nonarchitectural slips may be corrected and recorded, with failed checks rerun.
An architectural verification failure stops task-impl for re-planning; never weaken
expectations to claim success.

### Output

Measured final verification with exact environments, actual passes and limits.
### Safe in nature
False — integration and process verification can expose real design failure.
### Peripheral concepts
Current-dev regression baseline, package imports/entrypoints, synthetic/live evidence boundary.
### Hardness Lvl
4

## Step 7 — Commit implementation and evidence

### Proposed changes

Commit code/tests/public docs/example/setup in one product commit, then verification,
implementation record and handoff/evidence separately. Preserve all other worktrees,
original untracked files and duncan. Push the issue-linked branch and update #10's
status from committed evidence, with live qualification and merge-check/PR/fresh
critique still later. Do not publish a PR or merge/deploy in this task-impl run.

### Output

Completed offline worker delivery ready for its separately requested review gates.
### Safe in nature
False — deliberate commits/push and issue updates.
### Peripheral concepts
Pipeline status, archive-only work documents, product review boundary.
### Hardness Lvl
2
