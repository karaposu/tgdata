---
model: unknown
effort: unknown
---

# Plan — per-account read budgets (issue #9)

**Revision 1.** Input: `desc.md` (`eeb86a7`), triage and pre-plan probes.

### What is the task

Add an opt-in, durable allowance for explicit message pulls by Telegram account
ID. Every supported reader using a budget-enabled tgdata client must acquire
capacity before dispatch. A rolling 24-hour ledger and persisted warm-up policy
coordinate clients and processes, while preserving ordinary behavior without
a budget and preserving partial results when a reader stops at its allowance.

### Huge Hard Blockers

#### Planning Blockers

None open. The dispatch and paging seams are established by full source reads
of Telethon 1.45.0 and the local probe:
- a 37-message oldest-first page uses limit 37 / add_offset -37;
- restoring the iterator's temporary state lets it later resume with 100 /
  -100 from the next ID, without a gap;
- 40 competing SQLite claims in four processes admit exactly 98 of a 100-unit
  allowance, with usage retained after reopening the database.

These observe real iterator and SQLite behavior; scripted message replies do
not verify live Telegram. Telegram documents history/search limits as result
bounds and message-ID lookup as an explicit ID vector:
[history](https://core.telegram.org/method/messages.getHistory),
[search](https://core.telegram.org/method/messages.search),
[IDs](https://core.telegram.org/method/channels.getMessages).
Actual live response-bound conformance remains unverified. If a response
exceeds its bound, record the actual count and stop with a protocol error.

The description's explicit scope assumptions are the working contract:
message-pull RPCs are metered; metadata/previews and passive updates are not;
SQLite coordinates callers that share its path; rolling 24-hour time and
warm-up enrollment are distinct. No new worker or remote quota backend is built.

#### Execution Blockers

None for local implementation and offline verification. Live Telegram checks
require an authenticated account and are outside this run. Merge/deployment
are not steps in this task-impl plan and still need their separate review and
authorization. Exact model/effort metadata are unavailable and recorded as
unknown; no claim of §9 model compliance is made.

### How this implementation moves toward desired state

Use a small SQLite ledger for policy and charged reservations. A reservation
is committed before each actual sender.send, including Telethon's hidden
retries; successful replies settle to their returned message-slot count.
Failed/cancelled/crashed attempts remain charged until their dispatch timestamp
ages out. This is admission-time accounting, not response-arrival accounting.

The shared client factory adds a request adapter when a budget is supplied.
The adapter sits inside Telethon's request loop at its sender boundary, after
entity resolution and flood waits. Per-iterator wrapping reduces page size
before Telethon computes offsets; the final atomic claim still catches races.
The engines attach processed partial results to budget-stop exceptions, while
polling treats the stop as terminal for the current run.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Durable ledger, policy, status and errors | Atomic per-account reservations and rolling/warm-up accounting |
| 2 | Guard the client dispatch and pagination seams | Every supported request is admitted before each send |
| 3 | Wire public configuration and preserve interruptions | Budget-aware engines, partial results and polling stop |
| 4 | Add offline behavioral tests | Ledger/concurrency and real SDK-flow regression coverage |
| 5 | Document configuration and boundaries | Usable examples and explicit accounting semantics |
| 6 | Verify and commit | Passing supported offline suites, recorded limits and separate commits |

## Step 1 — Ledger and policy

### Proposed changes

Add `tgdata/read_budget.py`, using only standard-library SQLite, dataclasses,
time, datetime, uuid and validation helpers. Public objects:
- `ReadBudget(path, *, clock=time.time)`; a durable SQLite path is required,
  not a per-connection `:memory:` database.
- `configure(account_id, daily_limit, warmup=None, started_at=None)` registers
  or deliberately updates policy, retaining usage and the existing start when
  omitted. Warm-up is a sequence of increasing whole-day thresholds and
  nondecreasing caps no greater than daily_limit, starting at day zero.
- `status(account_id)` returns a `ReadBudgetStatus` with effective cap, charged
  usage, outstanding reservations, remaining allowance, warm-up day and next
  time a unit can be admitted. `.to_dict()` is JSON-ready.
- `ReadBudgetError` and subclasses for configuration/storage, unsupported
  requests and exhaustion. `ReadBudgetExceeded` carries requested units,
  status, retry timing and `partial_result=None`. Suppress unrelated exception
  context so local policy stops never masquerade as Telegram health findings.

Tables use a tgdata-specific prefix: schema metadata, per-account policy
(account ID, daily maximum, warm-up JSON, start, clock high-water mark), and
reservations (unique token, account ID, dispatch timestamp, charged amount,
settled flag). Index account/time. Store no session keys or message content.
Reject unknown schema versions and invalid/corrupt policy rather than resetting.

Use a short-lived connection per operation, with BEGIN IMMEDIATE for every
read-modify-write transaction; no transaction crosses an await. Within a
transaction, clamp observed time to the account's persisted high-water mark,
prune charges at or before now minus 86400 seconds, compute the effective cap
and sum current charges. Claims are all-or-nothing. Commit a reservation before
returning its token. Refusal includes the earliest expiry/warm-up boundary at
which the requested amount fits, or None when a policy change/smaller request
is required. Status uses the same calculation for one unit.

Settlement updates only its reservation token, once. Refund unused capacity
on a valid successful reply; remove zero-count records. A late settlement of
an already expired/pruned token cannot reduce a newer window's usage. On any
failed, cancelled or crashed request, retain the reservation; it ages out from
its original dispatch timestamp. An oversized reply is charged at its actual
count and reported as a protocol error. SQLite failures raise a local budget
error and prevent dispatch; settlement failure leaves the prior full charge.

### Output

A persistent, process-safe quota component independent of Telegram sockets.

### Safe in nature

True — a new component not wired to existing callers yet.

### Peripheral concepts

SQLite transactions, account identity, admission time, rolling expiry, warm-up,
clock rollback, conservative failed-attempt accounting, status serialization

### Hardness Lvl

3

## Step 2 — Request and iterator adapter

### Proposed changes

Add `tgdata/budget_client.py` with a client mixin and a per-call sender proxy.
The mixin overrides `_call`, preserving Telethon's signature and forwarding
unchanged when no budget is configured. Resolve the authenticated account ID
from `_self_id`, asking get_me only if necessary; metadata calls do not recurse
into budget claims. Unknown identity or missing policy stops reads locally.

Pass a proxy for the sender argument into Telethon's real `_call`. It acquires
the reservation synchronously immediately before each send, including retries,
then wraps the returned awaitable to settle successful replies. It never
changes the client's actual sender or changes connection/reconnection behavior.
Each retry is separately charged; waiting on a cached flood wait charges nothing
until an attempt actually sends. Exceptions/cancellation keep the charge.

Support positive-limit history, search, global search and replies requests,
and explicit ID vectors for messages/channels getMessages and scheduled-ID
lookup where available. Recognize known invoke wrappers recursively without
modifying them. Reject message-bearing batches, unbounded/unsupported requests
returning messages.Messages or DiscussionMessage, invalid/nonpositive bounds,
and unknown bounded-result shapes before dispatch or before handing a reply to
callers. Metadata-only batches remain unchanged. Request parameters themselves
are not silently rewritten.

Wrap each `_MessagesIter` instance's `_load_next_chunk`: temporarily reduce
its `left` to the latest available allowance, call Telethon's real method, then
restore `left` and the original add_offset. This lets Telethon compute reverse
paging correctly and restores its assumption that a later full page uses its
full negative offset. A final atomic claim may still refuse a raced request.
For `_IDsIter`, do not truncate ID vectors; restore its pre-call `_offset` if a
budget error stops a chunk, so resuming that iterator cannot skip denied IDs.

Extend `_client_class` to include the mixin. Append `read_budget=None` to
ConnectionEngine's constructor and attach the reference in `_new_client` so
primary, pool and ephemeral clients share the guard. Device-identity's local
probe remains unmetered. Default clients preserve current behavior.

### Output

Budgeted clients cannot dispatch supported message pulls without an atomic
claim, and budget-limited pagination retains its cursor semantics.

### Safe in nature

False — affects the shared client factory and vendor request path.

### Peripheral concepts

UserMethods._call, sender.send, _MessagesIter, _IDsIter, _PerCallFloodThreshold,
_AnswerEvidence, wrappers, authentication identity, shared factory

### Hardness Lvl

4

## Step 3 — Public wiring and interrupted results

### Proposed changes

Append `read_budget=None` to TgData and pass it through; export the budget
component/status/error types from tgdata/__init__. Add async
`get_read_budget()` returning the active account's status, or None without a
budget. It must not connect when no budget is configured.

In message_engine, propagate ReadBudgetError through sender/media conversion
catch-all handlers. On exhaustion in fetch/search, attach the processed
DataFrame to `partial_result` before re-raising. Successful returns stay
unchanged. Already-delivered callback rows may also be in that partial frame;
pending batches need not be redelivered during an exception path.

Stream ID lookup results during download_media_by_id so completed downloads
can be attached as a partial dictionary if the budget interrupts later work.
Keep positional ID association and None values for genuinely missing messages.

For discovery, retain text from posts read before exhaustion in _mine_room,
extract/resolve the links already seen, then propagate the budget stop with
all found group rows in partial_result. Stop before reading another room.
Keep non-budget network/flood behavior unchanged.

Polling delivers/deduplicates a partial message frame, if present, then
propagates exhaustion instead of sleeping and retrying. Other budget errors
also stop the run. Budget errors remain local and do not register new Telegram
health verdicts. Caller callback errors retain their normal propagation.

### Output

One public budget option covers every supported reader and reports a useful
stop without silently discarding processed output.

### Safe in nature

False — modifies exception paths and media iteration in existing engines.

### Peripheral concepts

DataFrame conversion, batch callbacks, media result dictionaries, discovery
partial rows, polling deduplication, health classification, public exports

### Hardness Lvl

3

## Step 4 — Behavioral regression suite

### Proposed changes

Add `test_18_read_budget.py`, offline with synthetic credentials and blocked
Telegram sockets. Use an injected clock and temporary SQLite files; use real
Telethon request/iterator code with scripted senders rather than replacing
the budget adapter. Include:
- validation/defaults, missing policy, persistence and account isolation;
- warm-up steps, zero allowance, policy updates retaining usage/start;
- rolling expiries, exact boundary, rollback, earliest sufficient retry time;
- settlement/refund/idempotence/late settlement and failed/cancelled charges;
- concurrent tasks/independent managers and four-process atomic claims;
- actual send-time charging through cached waits, retry and request resolution;
- forward/reverse paging with a small remainder, resumed larger page and ID
  cursor restoration after a refused chunk;
- all bounded request families, wrapper/batch/unsupported guards, oversized
  replies and fail-closed storage;
- persistent/pool/ephemeral factory wiring, actual account ID sharing;
- partial fetch/search/media/discovery results, polling delivery/stop, and
  absence of invented Telegram health verdicts;
- no-budget behavior remains unchanged.

Use the pre-plan probe as evidence for the seams, not as a substitute for tests
of the implemented ledger/adapter. Exercise compatibility on installed Telethon
1.45.0 and, if obtainable in an isolated temporary location, the declared 1.33.1
floor for the new request/iterator adapter; no project environment downgrade.

### Output

A standalone test report with meaningful assertions on both quota state and
which requests actually reached the scripted transport.

### Safe in nature

True — synthetic offline tests only.

### Peripheral concepts

controlled clock, multiprocessing, real SDK flow, cancellation, fault injection,
regression isolation, optional compatibility environment

### Hardness Lvl

3

## Step 5 — User documentation

### Proposed changes

Add a README section with ReadBudget configuration, an illustrative warm-up
curve, obtaining/using the Telegram account ID, sharing the SQLite path, status
and exception/partial-result handling. Explain rolling admission-time
accounting, conservative failed reservations, metadata/passive-update
exclusions, unsupported raw message calls, synchronous short transactions,
clock assumptions, and unchanged defaults. Do not describe examples as safe
Telegram limits. Add the new smoke-suite entry.

### Output

A runnable configuration example and a precise accounting contract.

### Safe in nature

True.

### Peripheral concepts

README, account setup, quota observability, offline-versus-live verification

### Hardness Lvl

1

## Step 6 — Verify and commit

### Proposed changes

Compile touched modules, run test_18, then the full supported offline suites
12–17 plus no-network helper checks from discovery. Disable live 12/13 cases
with an explicit nonexistent config path; localhost proxy checks may need
sandbox permission. Historical interactive/live smoke demos are not run against
the account. Report that boundary and any pre-existing unavailable checks.

Follow task-impl's verification gate: fix only small, non-architectural local
errors; record each fix and rerun failures. Architectural failure stops the run.
Commit runtime/tests/user docs separately from this work folder, exclude the
unrelated guide edit, and record exact results. Update issue checkpoints only
when backed by committed artifacts. Do not merge or deploy in this run.

### Output

Verified implementation commits and a truthful implementation record, ready
for the later merge gate and PR critique.

### Safe in nature

True.

### Peripheral concepts

offline suites, compatibility evidence, task-impl failure gate, separate commits,
issue status, archived branch documents

### Hardness Lvl

2
