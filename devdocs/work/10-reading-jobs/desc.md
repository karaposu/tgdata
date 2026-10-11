---
model: gpt-6-astra
effort: max
---
# A resident worker for explicit reading and group jobs — #10

**Session warmth:** same session as #7 implementation/merge and #17 review. Current
base `68f6bbda33aeb1963b96b3c719d8f23938fa4449` is an ancestor of this branch.
Verified operation/factory, batch, group, health, ledger and process-I/O boundaries
were read/probed; no redundant archaeology refresh is claimed. Feature-heavy triage
is `a61f4a4`; completed design inquiry is `e8bf7f0` (`traverse/finding.md`).

## Problem Statement

Applications currently import tgdata and directly manage its account objects and
async calls. They cannot start a standard tgdata reader process, submit a bounded
read or group operation and receive portable results and account health events.
Each application must invent that process boundary and its failure meaning.

The accepted library primitives exist, but simply serializing their return values
would miss expected-account proof on raw reads, exact large identifiers, deferred
health delivery and the difference between a disconnect attempt and successful
cleanup. A lost worker reply also cannot establish whether a Telegram join happened.

## User Value Proposition

Start one worker on a laptop or server with a named account inventory, existing
proxy/session configuration and read/join allowances. Send explicit-account jobs
for reading a bounded batch, looking up a group, checking access or joining, and
receive versioned results and correlated health events. The application keeps its
scheduling, result storage, receiver acknowledgments and account assignment.

The first delivery uses a trusted caller-managed subprocess with JSON lines over
stdin/stdout. This is the stated working default after an optional transport
preference question; no answer was received and no HTTP deployment was assumed.
It is an engineering scope choice, not an inference that the user approved a service.

## Success Criteria

1. A packaged worker command/module loads an explicit trusted inventory and reports
   its worker identity, account count/IDs and idle state. Startup does not log in or
   claim unobserved account health. One account is never silently expanded into
   several session files; ordinary TgData connection pooling stays unchanged.
2. A strict bounded versioned protocol admits one source job at a time. Each job
   names a configured account and one of the four operations. Invalid frames,
   unknown accounts/operations and invalid arguments are local source-free failures.
   Process-local request identity/repetition semantics are explicit and bounded.
3. Every source job uses a freshly verified expected account with existing proxy,
   device, session and quota policy. Raw batch execution composes the accepted
   BatchEngine with the accepted owned account/health context. Group methods retain
   their current meaning. No login prompt/code, hidden join, routing or quota reset.
4. Join jobs require explicit configured JoinBudget policy; missing/denied allowance
   cannot perform a mutation. Successful transport replies preserve the difference
   between joined, already_joined, requested, payment_required and interaction_required.
5. Raw MessageBatch v1 and ordinary-error partial batches survive serialization.
   Identifier fields in group/health/error envelopes remain exact for JSON consumers.
   Denied/unprobed access is not reported as readable. No raw exception text,
   credential/config content or traceback enters protocol diagnostics.
6. The worker collects bounded plain health events against their originating job
   and publishes through one writer, preserving source/observer separation. Read
   and join ledger authority remains the existing library, not worker counters.
7. Known source outcomes survive secondary cleanup/diagnostic errors. Cleanup
   failure is explicitly observable even during setup or cancellation and prevents
   the worker accepting another source job. No successful cleanup is inferred from
   a normal method return. The worker can terminate conservatively after reporting
   what it actually knows; it does not repair accounts automatically.
8. EOF, malformed/oversized input, slow/broken output and stop signals have defined
   behavior under real process pipes. Active cancellation settles owned work before
   normal shutdown; forcibly terminated or reply-lost work remains uncertain. No
   detached blocking reader/hidden job queue prevents shutdown or grants extra work.
9. A runnable caller/example and protocol/config documentation explain restarts,
   unknown joins, output draining and external exclusive account ownership. The
   worker does not imply durable job acceptance, exactly-once delivery or automatic
   retry. Account relocation/re-login remains an external operation.
10. Offline actual-SDK/SQLite and real-subprocess tests cover the whole composition,
    including all four jobs and lifecycle faults; supported current-dev regressions,
    compile/grammar, packaging and isolated invocation pass on Telethon1.45.0.
    Synthetic wire evidence is never called live account qualification.

## Scope Boundaries

- Caller-managed local process protocol, explicit account selection and serial
  source execution. No HTTP server, broker, background schedule, distributed lease,
  worker-owned message archive/cursor/ack store or transparent job replay.
- Reuse current dev; #17's rejected/unmerged account pool is not a dependency.
  Automatic routing/failover remains #17. No #17 runtime repair in this task.
- Existing file sessions remain usable. Trusted Python setup may supply existing
  pluggable session stores; jobs never choose/import a backend or carry login keys.
  No new encryption system or interactive/stepwise login flow.
- [ASSUMPTION] The caller owns the process pipes and exclusively assigns the worker's
  sessions/accounts while it runs. Transfer requires the old owner to stop. This
  is not a claim that several machines may concurrently use a session safely.
- The first delivery is qualified on the available Python3.11.10/Telethon1.45.0
  environment, with repository Python3.7 syntax constraints retained. Do not claim
  native testing of unavailable Python/platform combinations.
- This run covers offline implementation and required commits/issue updates.
  No live Telegram login/read/join, existing budget reset, PR, deployment or dev merge.

## Priority Level

**Low / P3**, selected now by the maintainer. The worker removes repeated process
integration work for consumers; its source prerequisites are already merged.
Importance is separate from its feature-heavy ownership/transport complexity.

## Known Blockers

No open planning blocker identified. The inquiry tested source/health composition,
cleanup-failure feedback, process I/O pitfalls and exact consumer ID projection.
The transport default is a declared engineering choice that can be steered, not
an unanswered behavioral premise. Exact wire/config/exit contracts belong in the plan.

Live deployment qualification requires separately approved account/group access,
exclusive ownership and bounded existing allowances. It is outside this offline
delivery and does not block its code, tests or documentation.
