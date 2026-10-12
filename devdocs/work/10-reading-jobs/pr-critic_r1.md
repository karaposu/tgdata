---
model: gpt-6-astra
effort: max
---
**Verdict: REORDER — TEST BEFORE BUILD**

Falsifier: a worker-owned stop/diagnostic boundary cannot preserve immediate loop
wake-up, retained cleanup and type-only unknown authentication errors without
changing the selected serial-process architecture.
Affordable now: yes — a small candidate composition and actual subprocess/SDK
controls, seconds offline, before the corrective implementation is built.

Experiment: qualify the revised process stop handoff with a quiescent selector,
no periodic test helper, SIGINT/SIGTERM, held disconnect, repeated signals, idle
input and blocked raw output; qualify canonical authentication diagnostics with
SDK-decoded unknown401/406, ordinary403 and known authentication-error controls.
Cost: owned temporary sessions/SQLite, OS pipes and synthetic RPC answers; no network.
Must precede: revision3's replacements for source/protocol Step1 and process Step3,
before the next implementation cycle; the review does not patch those steps here.
Disqualifying result: progress still depends on an unrelated timer/I/O event,
cleanup is abandoned, output regains a final flush, raw diagnostic text escapes,
or solving these requires a different job/source ownership architecture.
Passing result: wake-up occurs through the owned stop path, existing outcome/cleanup
rules hold in all states, unknown auth text is absent, and canonical known reasons
remain useful. The experiments below reproduce the current failures and controls;
they are not a passing implementation of the proposed remedies.

**PR gate: REJECTED — 0 High, 2 Medium, 0 Low.**

## High-level summary

Fresh review of PR27's actual13-file product diff plus revision2 plan, against
current dev68f6bbd, in the same warmed session under GPT-6 Astra/max. Product remains
6ee146c; merge-check85c0455 established fidelity, not soundness. No subagent.

Two integration boundaries escaped the earlier qualification. The process requests
cancellation but does not wake a sleeping event loop; the existing active-signal
test supplies a10 ms helper timer that hides this. Separately, authentication
wrapping turns arbitrary SDK error text into a field the worker treats as safe.
Unknown401/406 text reaches JSON even though ordinary403 text is correctly omitted.

Nine fresh probe histories cover four signal runs, four SDK-decoded error runs and
one protocol-control group. Two failure mechanisms reproduce with matched controls.
The existing25 core and14 process groups still pass. Their pass is valid coverage of
their cases and does not override these observations. No credential, account or live
Telegram resource was used; the text sentinel is synthetic.

The explicit-account serial worker remains a reasonable layer. These findings do
not justify HTTP, a queue, a router or a generic supervisor. A corrected plan and
small prebuild are required by CONTRIBUTING7.4 before further implementation.

## Premise Inventory

### P1 — Asking an active task to cancel makes process shutdown run

First dependent Step3; waste if false: process/tests/docs/qualification3–6. Scheduled
test4 and full test6. Cheapest earlier test: same process with actual selector/SDK
and a pending network future, without a helper timer, under a second per adverse
history. Existing active-signal tests are **non-covering for quiescent wake-up**:
their release watcher schedules asyncio.sleep(.01), periodically waking the loop.
Fresh quiet runs leave cleanup unstarted after SIGINT/SIGTERM and a repeat. An
explicit self-pipe wake lets the already-cancelled source clean up and exit130/143.
The polling control exits normally. Requesting cancellation and waking its executor
are separate facts. A revised mechanism needs real qualification before building.

### P2 — An authentication reason is trusted metadata rather than error text

First dependent Step1; waste if false: protocol/source/privacy documentation/tests1–6.
Scheduled test4 covers unknown generic RPC text but not authentication rewrapping.
Cheapest earlier test: SDK-decode unknown401/406 RPC errors and execute real worker
jobs, milliseconds. Fresh runs show raw sentinel text in error.reason. The underlying
library intentionally preserves unknown Telegram names in AuthRequiredError.reason;
the process cannot infer that a name-shaped string came from a known SDK mapping.
403 and AUTH_KEY_UNREGISTERED controls retain the intended distinction.

### P3 — Temporary verified operations preserve ownership and primary outcomes

First dependent Step2; prior prebuild plus tests32–38 cover actual SDK/context/ledger
behavior with synthetic Telegram data. Current read/source foundations are byte-
identical to dev except the documented resolver and cleanup receipt seams. Fresh
diagnostic runs prove zero group traffic/charge on failed identity authentication,
real cleanup, and no borrowed account. No contrary result found. A fabricated Worker
return would not cover these properties; the probes execute the real Worker.

### P4 — Serial framing and output preserve delivered versus unknown completion

First dependent Steps1/3; original prebuild actual pipes and fresh test38 cover EOF,
broken output, raw backpressure, partial batches and exact consumer IDs. Fresh local
protocol controls reject six malformed IDs without consuming the counter, consume
a recognized refused job and reject its repeat. Existing size/serialization faults
remain explicit delivery failure. This does not prove arbitrary crash exactly-once
delivery, and the contract correctly promises none.

### P5 — A live deployment can use assigned sessions and target groups

External precondition, not a hidden offline success premise. Live Telegram, proxy
availability, permission, safe rates, exclusive cross-process assignment and native
Windows/older Python remain unqualified. No cheap local stand-in closes those facts.
They are disclosed deployment boundaries and are not new findings in this review.

## Restart Check

| Observed failure | Established mechanism | Addressing design / remaining gap |
|---|---|---|
| #17 observer cancellation replaces source; descendant close forms a cycle | Inline callback coupled to source lifetime | Accepted post-cleanup monitor and fixed worker collector; overlap/observer controls pass |
| Failed SDK disconnect returns while transport/tasks remain | Existing result-preserving helper hides cleanup failure from caller | Private receipt stops admission; loop tasks are settled; process control passes |
| Missing cached read peer scans dialogs | Legacy BatchEngine fallback | Worker bounded resolver; default path remains unchanged |
| Buffered stdout flush outlives stop | Interpreter-owned pending output buffer | Raw writer and no teardown flush; real pipe tests pass |
| Active stop waits while no cleanup has begun | No wake-up accompanies task cancellation | **Gap: Risk1; polling fixture masked this composition** |
| Unknown auth diagnostic appears in portable result | Raw SDK message rewrapped as reason, then syntax-checked | **Gap: Risk2; trust origin was lost across wrapper boundary** |

Most established prior failures have concrete addressing mechanisms; this is not
a wrong-layer verdict. The two fresh gaps need a renewed plan, not symptom patches.

## Inherited Lessons

- Account filenames/caches are not identity: Step2 uses the accepted fresh proof;
  tests37/38 and these failed-auth controls preserve that ordering.
- Observer failure must not replace source completion: fixed bounded collector and
  post-cleanup delivery are covered by actual operation tests, not just a mock.
- Cleanup return is not proof of disconnection: the receipt is set before cancellation
  escapes and admission stops. **Requesting cancellation is likewise not proof that
  cleanup started**; Risk1 shows the additional process boundary must be tested first.
- Raw stdout is needed for stop under backpressure: tested before implementation and
  retained. Do not replace it with an event-loop-only signal handler that cannot
  interrupt the synchronous idle/write paths.
- Exact IDs do not imply safe diagnostics: string projection is correct, but error
  field origin also matters. Risk2 needs a known-name rule across auth wrapping.

## Risk 1 — Stop signals do not wake a waiting source job

**Risk**

When a Telegram request is waiting and nothing else is happening, asking the worker
to stop can leave it asleep instead of beginning client cleanup. Sending the stop
signal again does not help. It resumes when an unrelated event wakes it, so a caller
may wait unnecessarily or force-kill the process while its connection is still open.
This is a delay before cleanup starts, distinct from the documented possibility
that native cleanup itself takes a long time.

`tgdata/worker.py:132–146` installs a synchronous signal.signal handler that calls
active.cancel() and returns; it neither registers an asyncio wakeup fd nor posts via
a wake-capable loop path. During `loop.run_until_complete(active)` at169 the actual
KqueueSelector can remain in its approximately60-second SDK timer wait after the
signal. `test_38_worker_process.py:40–50` starts a10 ms release watcher, hiding the
problem. `probes/pr_lifetime.py` uses actual Worker/Telethon and selector calls:
without the watcher, SIGINT and SIGTERM leave cleanup unstarted after0.7 s and a
repeat; SIGUSR1's diagnostic call_soon_threadsafe wake then permits native cleanup
and exit130/143. The polling control succeeds. No Worker execution was replaced.

**Severity:** Medium
**Category:** Process lifecycle / cancellation scheduling / test coverage
**Impact:** graceful stop depends on unrelated traffic/timers; supervision may
escalate to hard termination even though cleanup has not had a chance to run.
**NoobEng:** Task.cancel queues work for the event loop. A signal handler returning
from an interrupted OS wait does not necessarily make that queue run; the selector
needs its own wake-up. A helper timer can make a defective stop path look correct.
**Affected areas:** worker process signal/loop ownership, active-stop tests and docs.

### Mitigation — Quick

Add a periodic worker heartbeat solely to make pending cancellations run.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Define the owned signal handoff for each process phase. For an active job, enqueue
its single cancellation through a wake-capable owned-loop operation; keep immediate
interruption for synchronous idle input/output, preserve repeated-signal cleanup
protection, and restore owned handler state. Qualify quiet-selector and held-cleanup
histories without polling assistance alongside the existing raw-output controls.
**Why this is robust:** supplies the missing executor wake-up at the stop boundary
without another task, transport, deadline policy or change to source ownership.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* One actual process owner exists in worker.serve; the CLI and Python bootstrap share it. Existing examples use their own established asyncio runners, not a second implementation of this hybrid signal contract. A wake-capable handoff closes this instance without a framework or polling dependency. The candidate still needs the named prebuild before corrective implementation.
*For future:* —

### Mitigation — Long-term

Introduce a reusable process lifecycle/transport controller for pipe, HTTP and
future worker front ends, with explicit phase and signal ownership.
**Why this is long term effective:** could make wake-up, blocking-I/O interruption
and restoration policies reusable across genuine future process implementations.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit only when a second concrete worker transport needs the same blocking-I/O and active-loop lifecycle. #17's pool is an in-process client owner and is not such an instance. The narrow stop boundary would survive a later transport controller.

## Risk 2 — Authentication wrapping forwards raw diagnostic text

**Risk**

The worker promises portable errors that omit arbitrary exception text. An unknown
authentication error bypasses that protection: its text is copied into a field
called “reason” and returned to the caller if it resembles a short identifier.
Such text can contain private diagnostic material. Consumers cannot rely on the
documented sanitization rule, even though other unknown Telegram errors are filtered.

`tgdata/health.py:114–117` intentionally returns unknown SDK .message text;
`ConnectionEngine._auth_required` at873 stores it in AuthRequiredError.reason.
`worker_protocol.py:227–231` copies any reason matching `_NAME`, unlike its known-
class RPC allowlist at252–258. `probes/pr_diagnostics.py` serializes/decodes real
TL RpcError replies and uses Telethon's rpc_message_to_error, then executes actual
lookup jobs. Unknown401/UnauthorizedError and406/AuthKeyError both publish
`RAW_AUTH_DIAGNOSTIC_7D93C1` verbatim as reason; ordinary403 omits it. The known
AUTH_KEY_UNREGISTERED control preserves its canonical reason. Cleanup succeeds,
with zero group requests or charges in all four histories.

**Severity:** Medium
**Category:** Diagnostic privacy / trust provenance / protocol contract
**Impact:** unknown authentication text crosses a boundary documented as type/known-
metadata only. This proves an output path, not a observed leak of a real credential.
**NoobEng:** the library intentionally keeps a raw reason for Python callers.
Renaming it and checking its spelling does not make it trusted metadata for a
serialized worker reply. The worker must decide which names it recognizes.
**Affected areas:** worker authentication projection and privacy tests; ordinary
library AuthRequiredError behavior need not change.

### Mitigation — Quick

Remove every authentication reason, including useful recognized Telegram reasons.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

At the worker projection boundary, publish only explicitly recognized canonical
authentication reasons; omit or use a fixed unknown value for all other text.
Retain type/category/first_login/banned and the existing known-reason behavior.
Test decoded unknown401/406 and known authentication failures through real worker
operations, in addition to the ordinary generic-RPC control.
**Why this is robust:** closes the demonstrated privacy boundary while preserving
the library's intentional raw diagnostics and the worker's useful fixed metadata.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The two actual neighboring projections, generic RPC errors and health events in worker_protocol, already reject unknown text. This authentication branch is the uncovered instance. A canonical-name rule at the existing worker boundary gives the required reach without migrating ordinary library error fields or changing their diagnostic contract.
*For future:* —

### Mitigation — Long-term

Give library errors separate typed canonical and raw diagnostic fields and require
future public transports to project only the canonical representation.
**Why this is long term effective:** could carry trust provenance across multiple
wrappers/transports instead of each consumer deciding which strings are publishable.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* A typed diagnostic representation is useful if another actual public transport needs it. It would touch existing library error construction/consumers beyond this worker boundary; the robust projection would remain necessary and can survive that later change. No present blocker forces a lesser remedy.

## Probe evidence and limits

```text
SIGINT quiet: stalled=true; cleanup_started_before_wake=false; repeat_still_waiting=true; exit130 after explicit wake
SIGINT polling: stalled=false; cleanup_started=true; exit130
SIGTERM quiet: stalled=true; cleanup_started_before_wake=false; repeat_still_waiting=true; exit143 after explicit wake
SIGTERM polling: stalled=false; cleanup_started=true; exit143
unknown401: UnauthorizedError -> AuthRequiredError.reason=raw sentinel
unknown406: AuthKeyError -> AuthRequiredError.reason=raw sentinel
unknown403: ForbiddenError -> no raw sentinel
known401: AuthKeyUnregisteredError -> canonical AUTH_KEY_UNREGISTERED
protocol: six malformed IDs refused; recognized invalid job consumes ID; repeat refused
```

Exact timings/selector deadlines, retained charges and cleanup observations are in
`probes/pr_lifetime.txt`; exact JSON projections are in `probes/pr_diagnostics.txt`.
The selector wrapper observes calls without supplying a timer. The separate SIGUSR1
wake is a diagnostic control, not production behavior or a claimed implemented fix.
The0.7-second observation bounds the probe; the finding is missing wake-up and delayed
cleanup entry, not an invented subsecond shutdown SLA. The source's normal SDK timer
or future network event can eventually wake the unchanged worker.

No product edits, live requests or real secrets. Existing39 worker groups passed
again; prior612 actual passes/3 live skips remain recorded for their covered cases.
Neither count qualifies these newly found mechanisms. Constructor positional
optionality recorded by merge-check is benign API breadth, not a padded Low risk.

**Disposition:** CONTRIBUTING7.3 rejects on either Medium. Keep PR27 draft and #10
open. Under7.4, next is revision3 re-planning using this critique, then plan critique,
fold and implementation before both PR gates repeat. No findings are patched here.
