# Sensemaking — #10 worker contract

## User Input

`_branch.md` W1 and all three considered articulations, consuming the saved
`surfacing.md` and same-session source workspace. Establish the boundary before
choosing an implementation.

## SV1 — Baseline

The worker appears to be a command loop around four existing library methods,
holding account configuration and returning their results. The immediate temptation
is to serialize calls and consider a returned coroutine sufficient completion.

## Anchors and SV2 — Anchor-informed

Constraints: four source operations; configured accounts/proxies/sessions/budgets;
many accounts, one session per account; orchestration and processing stay external;
only merged dev is available, not #17's rejected pool. Structural points: verified
temporary account operations, raw batch engine, owned health notifications, existing
read/join ledgers, process stdin/stdout and supervisor. Principles: actual identity
owns quota; a lost response does not establish rollback; a read result is distinct
from receiver acknowledgment. Meaning nodes: job, outcome, account owner, reply,
cleanup, worker lifetime. Insight: ordinary `get_message_batch` is not itself an
explicit expected-account boundary, but the existing BatchEngine can execute inside
the merged verified-operation context without adopting #17.

SV2: this is a process consumer of distinct existing contracts, not a replacement
account router or a new raw-batch format. The source operation, result publication
and process lifetime have different completion conditions. H4/H5: these names map
to actual code and observed task boundaries; #17 is supporting failure evidence,
not the definition of every possible worker fault.

## Perspectives and SV3 — Expanded understanding

- Technical: the actual owned operation plus BatchEngine probe verifies expected222
  despite cached111, reads two records, charges222 only, and settles SDK disconnect.
  This closes the source-composition premise before further worker design.
- User: one startup command and explicit jobs can hide SDK mechanics. A forced new
  transport/server deployment would add a consumer obligation the issue did not
  supply. The asynchronous transport preference remains open; stdin/stdout is a
  stated engineering default, not a fabricated user answer.
- Failure: actual disconnect failure can leave the transport connected while the
  context returns the original successful body. The existing contract deliberately
  preserves that outcome. A worker must not silently interpret it as permission
  to reuse the same account/session for another job.
- Operational: actual owned health callbacks are scheduled after cleanup; the probe
  observes one notification task and correct owner222/FloodWait7200. A worker needs
  explicit job correlation/drain behavior, not a mutable global current-job label.
- Resource: an executor-backed stdin read remains alive after its asyncio waiter
  is cancelled; closing stdin permits exit. A real pipe writer blocks until the
  parent drains output. Unbounded input queues and detached blocking threads are
  not incidental transport choices.
- Strategic: a durable worker queue would own acceptance/retry state that already
  belongs to the orchestrating caller. Reads can be replayed deliberately, consuming
  allowance; joins cannot be retried merely because a reply disappeared.
- Systemic: credentials/config paths and source messages have different disclosure
  purposes. Protocol errors must not echo secret configuration/exception text;
  returned message content is the requested product, not a diagnostic.
- Definition/frame exit: “pool” has existing same-account sessions, distinct-account
  routing in #17, and this worker's inventory. Only the last belongs to #10. “Done”
  includes source completion, cleanup attempt, reply write and caller receipt:
  none can stand in for another. Caller durable storage remains an external
  prerequisite for reliable orchestration, not an omitted worker responsibility.
- Phase/calibration: no consumer network API or second live account was supplied.
  An offline implementation can be complete without claiming live deployment or
  a durable distributed worker protocol.

SV3: the central difficulty is preserving the meaning of completion across source
and process boundaries. Three perspectives produced additional anchors: failed
cleanup visibility, deferred notifications and blocking transport lifetime.

## Ambiguity collapse and SV4

### A1 — Does holding accounts imply automatic selection?

Counter: “takes jobs” could mean the caller names only a group and the worker routes.
Structural test: accepted routing/recovery needs account/group persistent facts,
which are in unmerged #17; the merged job primitives already take explicit expected
account IDs. Resolution: explicit account per job for this delivery. ConfidenceHIGH
for independence from #17; automatic routing is a separate future integration.
Fixed: account ownership is declared and verified. Disallowed: silently routing
through rejected code. Dependent: job schema/admission. Model change: inventory is
not a selection engine.

### A2 — Does a reply establish durable delivery or safe retry?

Counter: adding job IDs could make every retry harmless. Structural test: a join
may succeed remotely before the pipe loses its reply; no shared transaction covers
Telegram mutation and caller receipt. Resolution: explicit request/response
correlation, no exactly-once or automatic retry promise. ConfidenceHIGH. Fixed:
unknown receipt remains unknown completion. Disallowed: automatic join replay,
cursor advancement or inferred receipt from local write. Dependent: error/exit
contract and examples. Model change: caller acceptance is outside this worker.

### A3 — Is returning from cleanup permission for another job?

Counter: the verified-operation helper already handles cleanup, so no further rule
is needed. Structural test: actual SDK fault probe returns the body while its
transport remains connected. Resolution: the worker needs explicit failed-cleanup
knowledge or a stronger process-lifetime boundary, and must stop new source work
when ownership is uncertain. ConfidenceHIGH. Fixed: no reuse based only on normal
method return. Disallowed: hiding a cleanup failure and opening a successor client.
Dependent: execution/termination design. Model change: an attempt and successful
closure are separate facts; choose the mechanism later, not a generic framework now.

### A4 — Are notification tasks part of source execution?

Counter: await arbitrary health callbacks inside the source so replies always
follow notifications. Structural test: the merged owned monitor deliberately
queues plain events after source cleanup; #17 demonstrated cyclic/independent
observer cancellation when coupled differently. Resolution: preserve the existing
separation and make the worker's own notification collector bounded/correlated.
ConfidenceHIGH. Fixed: health must not replace source outcome or own account
admission. Disallowed: a network/UI callback controlling source lifetime. Dependent:
protocol event ordering/drain. Model change: event delivery is an observation.

### A5 — Is HTTP or durable queueing necessary for “worker”?

Counter: servers commonly expose network APIs or consume durable queues. Structural
test: no authentication, broker or consumer API is supplied; a caller can start the
same subprocess on laptop or server and own job scheduling/storage. This establishes
V1 feasibility, not that V2/V3 are invalid in every deployment. Resolution: V1 is
the initial working delivery; V2/V3 remain alternatives to compare explicitly in
Innovation/Critique. ConfidenceLOW about human transport preference, not an unknown
mechanism or permission gate. Fixed: no unsolicited network deployment. Disallowed:
claiming a preference response. Dependent: concrete process interface.

### A6 — Are the two recent #17 failures the whole ownership problem?

Counter: copying its fixes would cover the worker. Structural test: actual process
stdin executor cancellation, pipe pressure and cleanup-return observations add
different failure boundaries. Resolution: inspect all source/process/caller ends,
using #17 only as examples. ConfidenceHIGH. Fixed: actual composition qualification.
Disallowed: inherited test counts as proof of a new process contract. Dependent:
prebuild and final tests. Model change: broader lifetime pattern, no pool rewrite.

SV4: explicit-account jobs and honest uncertain completion are stable. Cleanup
failure visibility and process I/O require concrete mechanisms; these are resolvable
design work, not human-only blockers. Transport preference remains replaceable.

## Degrees of freedom and SV5

Fixed: current-dev ownership and ledgers, original raw-batch format, all four job
types, no hidden login/routing or automatic retry, caller-owned scheduling/results,
exclusive sessions, no live actions in this run. Eliminated: direct unverified raw
read wrapper, new quota ledger, treating a pipe write as a durable acknowledgment,
ignoring uncertain cleanup, indefinite unowned executor readers.

Viable: serial caller subprocess with explicit lifetime/error semantics; a larger
service/queue adapter only if its added duties are actually selected. Mechanism
choices remain for transport framing, request IDs, notification collection,
cleanup-failure feedback and fatal shutdown. None requires replacing batch/budget/
group implementations.

## SV6 — Stabilized model

Build an execution boundary for caller-selected bounded jobs. Its contract says
what was validated, what source operation ran, what outcome is known and whether
the process can safely accept another job. It preserves the caller's responsibility
for receipts, uncertain joins, scheduling and exclusive account assignment.
The initial transport can be small; the completion semantics cannot be implicit.

Compared with SV1, source methods are reused but their return is no longer treated
as universal completion. The model separates job admission, verified work, cleanup,
notification collection and reply receipt without inventing new product engines.
H6 accommodation: dropping the “simple returned coroutine means safe next job”
assumption stabilized the model; no series of exceptions was used to protect it.

## Evidence and telemetry

Current-dev probes in `../probes/source_boundaries.py` and `process_boundaries.py`
ran on actual Python3.11.10/Telethon1.45/SQLite and owned subprocess pipes. Three
source observations and three process observations passed; exact outputs retained.
Synthetic Telegram replies are labeled; network sockets were forbidden. Process
probe was strengthened with a writer-start handshake before its final run; no
expectation or product behavior changed.

Official reference context: [async subprocess pipes](https://docs.python.org/3.11/library/asyncio-subprocess.html),
[loop/executor lifetime](https://docs.python.org/3.11/library/asyncio-eventloop.html),
[runner signal handling](https://docs.python.org/3.11/library/asyncio-runner.html).
The runtime observations above, rather than the online patch-version docs, establish
what this installed interpreter did. No live Telegram or power-loss proof is claimed.

Six SVs; five anchor types; nine perspectives; five high-confidence boundary
resolutions plus one explicitly low-confidence transport preference. H1–H9 checked;
self-reference concerns do not apply to this ordinary software question. Last
definition/phase perspectives constrain rather than add implementation layers.
Status-quo bias challenged with failed cleanup; clean-resolution trap tested by
actual pipes; no prematurely fixed transport preference. Ready for decomposition.
