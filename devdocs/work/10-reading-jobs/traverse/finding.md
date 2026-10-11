---
status: active
model: gpt-6-astra
effort: max
---
# Finding: a small worker with explicit job and account ownership

## Question

How should tgdata run as a resident process that holds configured accounts, accepts
read, lookup, access-check and join jobs, and returns batches and health events?
What must it promise when work finishes, a reply is lost or shutdown interrupts it,
while the caller continues to own orchestration and processing?

## Finding Summary

- Use a serial caller-managed process with versioned JSON lines over stdin/stdout.
  This is the stated engineering default; the optional transport preference has
  not received a user answer.
- Every job names a configured expected account. Verify that account before group
  work, and use the existing read/join ledgers. Automatic routing is separate #17.
- Keep the worker resident but use one temporary verified client per job. Do not
  keep account sockets alive merely because their configurations are in inventory.
- A cleanup failure must be visible to the worker. Preserve the known source result,
  then stop accepting source jobs instead of reusing an uncertain client/session.
- Preserve raw MessageBatch v1 and partial results. Project identifier fields as
  decimal strings so JSON consumers retain large Telegram IDs exactly.
- Collect health notifications with their originating job; one writer owns output.
  A lost reply never means a join failed, and the worker never retries jobs itself.

## Finding

### 1. Keep the existing library responsibilities

Issue10 asks for a different way to call tgdata, not a second implementation of
Telegram reading. Current dev already contains the account proof, group operations,
budgets and batch format needed for those calls. The worker should use them directly.

The source probe combined the existing BatchEngine with the verified temporary
account context. With cached account111 and actual account222, it returned two
records and charged222 only. This establishes a concrete path for raw reading
without importing #17's unmerged account pool.

The caller supplies trusted account configuration, existing sessions and deliberately
configured allowances. A job selects an account from that inventory; it cannot
supply credentials, an arbitrary module or an alternative configuration path.
Moving an account remains an external reassignment after the previous owner stops
and any required login is completed separately.

### 2. Define a job as one bounded attempt

The worker accepts one source job at a time. It validates the complete request
before source work and returns a correlated terminal outcome. Versioned envelopes,
bounded input and process-local increasing request IDs provide a small explicit
protocol without an ever-growing duplicate-ID registry.

The worker does not durably accept jobs or promise exactly-once execution across
restart. If a response disappears, the caller must treat completion as unknown.
The worker must not replay a join on the theory that no reply means no membership
change. A repeated read also remains an explicit new attempt that consumes allowance.

No worker cursor or acknowledgment store is needed for these raw jobs. The existing
caller-side processing and delivery contracts continue to own accepted progress.

### 3. Make cleanup knowledge part of admission

The accepted account-operation helper preserves a successful result when disconnect
fails. That is useful for a short-lived library call, but its normal return does
not certify that the old transport closed. An actual fault probe returned a completed
body while the transport remained connected.

A small private feedback path can report that failure without changing existing
library outcomes. The candidate captures the failure before caller cancellation
escapes and retains a sticky engine fact in a finally block. Six real SDK composition
cases passed, including failed setup, source failure, SDK-internal cancellation,
repeated caller cancellation and failed diagnostic logging.

The worker must consume that fact: once cleanup is uncertain, no more source jobs
are admitted in that process. A known source result remains a result; it is accompanied
by the worker's stopping state. Process restart is a caller decision after the old
process has actually ended. The worker does not add automatic account repair.

### 4. Separate source work from process I/O and notifications

Synchronous binary stdin/stdout around one owned asynchronous job is sufficient for
this first delivery. A real probe showed why a naive executor reader is unsuitable:
cancelling its asyncio await left the process waiting for the blocking stdin thread.
Another probe demonstrated actual pipe backpressure. The process must stop admitting
work while it writes the prior outcome, rather than accumulating source jobs.

Signals need phase-specific behavior. During source work they request cancellation
and prevent later admission while owned cleanup settles. During idle input or output
they stop the loop. There is no hard deadline for an SDK cleanup that never finishes;
a caller that forcibly terminates the process has an uncertain job outcome.

The merged owned-health implementation already dispatches plain notifications after
cleanup. Use a fixed bounded job-local collector and drain its defined work before
reusing job state. Do not run arbitrary application callbacks inside source execution
or let notification code write directly to stdout. Those patterns would recreate
the observer/cancellation problems just reproduced in #17.

### 5. Preserve the data meaning across JSON

MessageBatch v1 already uses exact string identifiers; keep that format and hash.
An ordinary source failure's complete partial batch must remain present in the
worker error reply. Do not replace it with a generic worker error or silently retry.

Group and health projections need explicit identifier conversion. A real Node
JSON.parse probe rounded the numeric query ID9223372036854775807 to9223372036854776000;
the decimal-string form survived exactly. Counts and booleans retain their own types.
The Python group API stays unchanged; this is the worker's wire representation.

Preserve qualified source statuses: readable, denied and unprobed differ, as do
joined, already_joined, requested, payment_required and interaction_required.
Errors expose stable categories/types and safe metadata, never raw exception text,
credential values or tracebacks. “Idle” reports process activity, not authenticated
health of accounts that have not yet been checked.

## Next Actions

### MUST

- **What:** qualify the issue and create a precise request/config/outcome contract.
  **Who:** task-desc/task-plan. **Gate:** this completed inquiry.
  **Why:** the implementation needs explicit framing, limits and retry meaning.
- **What:** preserve the tested cleanup feedback and verify its worker admission use.
  **Who:** implementation and critic-d. **Gate:** before production source integration.
  **Why:** a private fact is useful only if unsafe continuation is prevented.
- **What:** exercise actual subprocess framing, signals, output pressure, source
  ownership, partial data and all four operations, then run current-dev regressions.
  **Who:** implementation verification. **Gate:** the folded plan's completion.
  **Why:** in-process tests alone cannot qualify a worker boundary.

### COULD

- **What:** provide a small caller helper/example that drains events until a terminal
  reply. **Who:** docs/example implementation. **Gate:** request contract fixed.
  **Why:** make correct integration easy. **Depends-on:** MUST “precise request/config/
  outcome contract”; GATED until that contract exists.

### DEFERRED

- **What:** authenticated HTTP transport. **Gate:** an explicit network consumer and
  authentication contract are selected. **Why if revived:** remote application access.
- **What:** per-job OS isolation. **Gate:** uncooperative work defeats the tested
  cooperative ownership boundary. **Why if revived:** stronger resource isolation.
- **What:** durable worker job/output receipts. **Gate:** a consumer explicitly needs
  a worker-owned acceptance/retention protocol. **Why if revived:** restart delivery.
- **What:** live account qualification. **Gate:** approved accounts/group, exclusive
  session ownership and bounded existing allowance are provided for this worker.
  **Why if revived:** qualify real deployment separately from offline tests.

## Reasoning

Ordinary method wrappers were rejected because raw reads would lack explicit expected
identity and cleanup success would be guessed from return. Direct callback output and
raw exception strings were rejected because they entangle observers with replies and
can disclose configuration. The verified-operation composition and bounded outcome
collector address those specific failures with existing primitives.

An executor stdin reader with an internal job queue was rejected in its naive form:
the real thread outlived cancellation, and queueing would add admission/shutdown
responsibility. A command that exits after every job was also rejected because it
does not satisfy the requested start-once resident worker.

Worker-owned durable queues and message archives were rejected for this delivery
because they duplicate the caller's orchestration/storage duties without making a
Telegram join transactional with reply receipt. Shared session ownership was rejected
because no coordination authority exists. Existing ledgers and raw batches already
supply the reusable accounting/data pieces; replacing them adds no needed capability.

HTTP and per-job subprocesses remain legitimate alternatives under different stated
requirements. They add network policy or a second process/IPC lifecycle. The smaller
stdio design has a proven source/cleanup path and fits the supplied caller boundary,
so those extra layers are not necessary now.

## Open Questions

### Monitoring

The exact final wire limits, exit codes and event ordering will be fixed in the
implementation plan and tested. The process/SDK prototypes establish feasibility;
they are not claims that worker implementation or integration tests already exist.

### Refinement Triggers

An explicit HTTP preference revisits transport, not account/receipt ownership. A
failed candidate experiment that cannot expose cleanup failure without changing
source outcomes would revisit lifetime design before implementation. A requested
durable job broker would require its own acceptance/retry design rather than adding
automatic retries to this protocol.

Evidence is retained in `../probes/`: source composition, real process pipes,
cleanup candidate and Node identifier round trips. All Telegram data was synthetic;
no network login/read/join or existing account budget was used.
