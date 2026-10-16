---
model: gpt-6-astra
effort: xhigh
---
# #50 implementation plan — revision 4

**Critic folded:** 2026-10-16T12:11:17.879086+00:00 —0 mitigations (0 implementation steps changed,0 added).
Fresh critique: REORDER — TEST BEFORE BUILD; no new rated risks. Phase3 has no
mitigation selection. Full combined prebuild **PASS** is recorded in prebuild-r4/result.json:23 groups,
25 actual PTY scenarios,17 retained histories,8 stop transitions and14 publication
combinations, before product changes. The textual fold followed the user's explicit
sequence; the fold alone was not implementation clearance. The complete gate
subsequently passed in e0d764f before product da890a1. Revision3 is preserved in
step_by_step_impl_plan_r3.md and revision2 in step_by_step_impl_plan_r2.md.

Inputs: desc.md, triage77c1e85, traverse15de8c2, selected robust R1 in
pr-critic_r1.md (93ba179 / d10104b), and the actual code/probes. Archive productdf79728
is identical to PR51 product69c2407. Fetched dev remains77f2f53. Same warmed session;
no subagent. Current-thread2026-10-16T12:07:55.242Z verifies gpt-6-astra/xhigh.
Feature-heavy still applies. One rejected PR critique exists; neither the skill's
three-rejection guard nor CONTRIBUTING's second-rejection return-to-description
rule has been reached. This is a regenerated lifecycle plan, not a list of patches.

### What is the task

Provide deliberate terminal phone/code/optional-password login using the existing
LoginFlow, and publish a reusable native session with truthful failure outcomes.
The rejected driver treated Ctrl-C as a task exception to retry through an event
loop. This revision makes stop intent belong to the entire command, while source
cancellation, terminal input and file publication retain distinct effect rules.
A stop must prevent the next operation, settle owned work and preserve what is
already known about authentication and saving.

### Huge Hard Blockers

#### Planning Blockers

None identified. The failure mechanism is established by actual process signals,
real terminal/native SRP and Python's completion callback: re-entering
run_until_complete on a task done with KeyboardInterrupt can hang. A bounded
six-case probe in replan-r3/ observes that cooperative cancellation plus terminal
result consumption works with actual LoginFlow/SDK cleanup. This resolves the
local feasibility question without changing authentication or file representation.

At revision3 planning time, the complete command owner and its phase boundaries
were unqualified. Step2 subsequently passed the full combined prebuild at e0d764f
within the declared offline/local scope. This was reachable experimental work,
not an inaccessible planning blocker; step2
puts the full combined prebuild before every product change. If the composition
fails the stated design falsifier, stop and return to the description rather than
implementing around an unproved lifetime.

#### Execution Blockers

None for required offline work. Carry desc.md's limits unchanged: live Telegram
code delivery/real-account2FA needs an explicitly authorized exclusive setup and
is supplemental, unperformed qualification; native Python3.7 execution is also
unavailable. Neither is used to claim the supported Python3.11.10/Telethon1.45.0
or syntax-only evidence covers a different runtime or live behavior. No live login,
release, deployment or merge is included in this plan's implementation stages.

### How this implementation moves toward desired state

Retain the established LoginFlow, StoredSession, native SQLite conversion and
LoginDestination publication contract. Rebuild the private terminal lifetime in
login_cli.py around one persistent stop request and explicit admission/retirement
boundaries. Test the whole revised candidate before promoting it. Carry the file
barriers and optional own-cache decisions forward; the fresh review found no reason
to alter those layers. No public supervisor, new persistence framework, reader lock,
background input thread or worker refactor is justified.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Specify one command's stop and effect ownership | Phase, admission, completion and final-exit contract |
| 2 | Critique/fold, then prove the complete candidate | Revision4 plus passing combined prebuild before product edits |
| 3 | Promote the terminal lifetime and preserve publication | Revised private driver integrated with existing auth/file semantics |
| 4 | Make phase coverage permanent and explain stopping | Expanded smoke48 and accurate terminal guide |
| 5 | Verify, commit and return to the same PR's review gates | Supported regression/install evidence and honest revision status |

## What changed after rejection

Observed failure: Ctrl-C during executing login code can leave a completed task
carrying KeyboardInterrupt. The old _drive loops into run_until_complete again;
the Python callback does not stop the loop for that completed exceptional task.
Tests that signal while a Future is suspended miss this execution phase.

Missing distinction: **command stop intent is persistent; a task's cancellation or
completion is only one part of responding to it.** A completed task must be consumed
once, a pending action must be asked to stop, and retirement must still run. Merely
adding a done-task early return does not prove that other owned work has settled.

R1 mapping: step1 defines the owner and admission boundaries; step2 tests actual
running-code signals, transitions and retirement in the full composition; step3
implements that selected local mechanism; step4 preserves it as regression coverage.
Revision1 plan findings remain answered: parent/backup persistence barriers and
optional own-account cache data are retained in the publication contract below.

## Step 1 — command ownership, admission and outcome contract

### Proposed changes

Define one small private command-lifetime owner inside tgdata/login_cli.py. It
holds the retained private event loop, original SIGINT handler, a sticky requested-
stop flag, current phase and at most one active action registration. An action
registration binds its future and cancellation-request state; an old callback may
never cancel a later action or a cleanup future. This is private to this CLI, with
no generic framework/public API or duplicated LoginFlow state machine.

Install a command-owned SIGINT policy before constructing the flow/destination;
restore the previous handler exactly once after owned finalization. Refuse a
non-main thread, nonterminal stdin or an already-running loop before source work.
Do not temporarily restore the default exception-raising handler between ordinary
command phases. The policy depends on the active phase:

| Phase | Response to SIGINT | Boundary before continuing |
|---|---|---|
| Preflight / between operations | Record stop only | Check before the next prompt/action/publication |
| Terminal input / confirmation | Record stop and unwind that input | Let getpass restore terminal state; start no action |
| Active async auth / authorization check | Record stop; schedule one cancellation of the registered action | Wait for its terminal state and owned cleanup |
| Explicit retirement / loop shutdown | Record stop only; never repeatedly cancel retirement | Finish its owned attempt, preserving failure evidence |
| Native file preparation/publication | Record stop; pass it to the publisher's existing stop predicate | Respect pre-mutation checks and post-mutation outcome |
| Reporting / final cleanup | Record stop without interrupting effect bookkeeping | Choose exit status after finalization |

During async work, the SIGINT handler must not throw KeyboardInterrupt into arbitrary
authentication/SDK bytecode. It records intent and schedules at most one cancellation
callback with loop.call_soon_threadsafe while its registered loop is open. Do not
manipulate the returned handle inside the signal handler. The callback captures
and verifies the exact action registration, then cancels only if that action is
still pending. Repeated signals do not create another cancellation or skip cleanup.
A queued signal before task registration is retained and handled before source
admission. Clear registrations before closing the loop, so signals cannot enqueue
work against a closed loop. The six planning probes support these primitives;
the full phase/registration design was qualified by the step2 combined prebuild
recorded at e0d764f, before product promotion.

For synchronous terminal input, preserve getpass' exception-based unwind so echo
restoration executes. Scope that behavior to the input operation; clear the input
phase in finally before async work or cleanup begins. Subsequent signals during
unwind must not repeatedly inject exceptions into terminal restoration: switch to
the stop-only retirement policy before raising the first input interruption.
The full PTY tests must observe terminal settings, not merely absence of echoes.

Source admission checks stop before constructing/scheduling a new action; use an
awaitable factory or explicitly close an unstarted coroutine on refusal. Recheck
any stop arriving during registration before running the loop. Check again before
another prompt, authorization-only check, retry confirmation or file save. A
pending stop is never reset by successful completion or a different phase.

An in-flight authentication request may already have a remote effect before it
observes cooperative cancellation. The SRP planning probe actually recorded one
password request and an uncertain outcome. Preserve existing LoginFlow truth and
settle it; do not claim a stop prevents every in-flight RPC. No NEW top-level login
action or publication is admitted after stop, even if the previous action completed
authentication. No auth-only check is run automatically to resolve a stopped flow.

Drive a pending future until it becomes terminal, then consume its result once.
Never call run_until_complete again for a future already done with KeyboardInterrupt
or another terminal result. Keep a defensive path for an actual task-raised
KeyboardInterrupt: record stop, consume it without re-entering a finished future,
then follow owned retirement. Ordinary LoginError/status semantics stay intact;
component CancelledError must not create a second source action. Normal async
SIGINT must follow the cancellation-request path, not rely on this defensive path.

Retirement is admitted even after stop. Retry flow.cleanup_pending once as the
existing command does; do not invent endless reconnect/close retries. Settle the
command's private-loop tasks and async generators without allowing repeated SIGINT
to cancel the draining future. A completed failure is reported safely; the command
must not claim a failed disconnect succeeded. No bounded disconnect/syscall latency
or safe escape from SIGKILL is promised. Tests use bounded synthetic subprocesses
as failure detectors, not product timeouts.

Compute the final exit after retirement/reporting, rather than evaluating an early
return before finally can observe a later stop. A recorded operator stop yields130;
otherwise preserve0 saved,2 preflight,3 source/cleanup,4 known-unpublished save
failure,5 uncertain publication. Publication state remains independently authoritative:
saved plus stop is reported saved with130; uncertainty plus stop remains uncertainty
with retained recovery files and130. Cleanup or broken output cannot turn a known
published result into an unpublished one. Safe errors show kind/type only.

### Output
An explicit local lifetime contract covering admission, task completion, retirement,
input and publication effects; each transition has a stop rule.
### Safe in nature
False — this design changes how terminal interruption reaches existing async work.
### Peripheral concepts
Main-thread signals, asyncio task state, getpass terminal restoration, LoginFlow
cleanup ownership, synchronous file effects, final exit precedence.
### Hardness Lvl
5

## Step 2 — fresh plan critique, fold and full combined prebuild

### Proposed changes

Fresh in-session critic-d on revision3 with desc.md and the rejected PR critique
is complete (critic.md): no rated findings; full combined prebuild required. Preserve the earlier planning critic/prompt and PR critique;
use revision-specific copies before replacing canonical planning artifacts. Fold
selected mitigations into revision4 before promoting any product code. A meaning
gap returns to the description. The zero-mitigation fold and full-prebuild PASS are recorded above.

Build the complete revised command candidate only under the work folder, composing
its actual lifetime owner/terminal driver with the existing real LoginFlow,
StoredSession, native SQLiteSession, LoginDestination and ordinary configured
reader. Source transport may use test41's controlled wire; native SRP, cleanup,
file operations, hidden input and signals must remain real. Use exact candidate
hashes and no live socket. Probe helpers returning complete/login/save success
are non-covering for those behaviors.

Run one combined prebuild with all revision2 scenarios, the17 fresh functional
histories from pr-probes/probe_matrix.py, and the following phase matrix. This
matrix is required acceptance coverage, not a collection of optional targeted
checks; a collection of earlier isolated passes does not replace a full run.

1. **Running source code:** real SIGINT inside phone validation and during actual
   native SRP computation. Include real PTY/getpass, prove the signal occurred
   during compute, assert exit130 without external kill, no publication and all
   releasable synthetic wires/tasks settled. Preserve source-call counts and the
   resulting known/uncertain auth state; do not require impossible zero in-flight
   effects after a stop.
2. **Suspended work and native cleanup:** first/repeated signals during connect,
   source await and disconnect; complete authorization followed by interrupted
   cleanup; cleanup failure followed by its permitted retirement attempt. Hold
   synthetic cleanup with an explicit gate, prove the command waits, then release
   and prove it exits. Also test signals during the separate final retirement path.
3. **Terminal state:** EOF and first/repeated Ctrl-C at phone/code/password and
   replacement/save-retry confirmation. Observe the PTY's echo/canonical settings
   after input unwind. No prompt/action is admitted after stop and no secrets echo.
4. **Admission/completion transitions:** stop before action creation, after task
   registration but before execution, at task completion before the next prompt,
   and during the transition to finalization. An already-done future containing
   KeyboardInterrupt is consumed without a second event-loop run. Delayed callbacks
   for an old action cannot target a new action or a retirement future.
5. **Publication boundaries:** stop before preparation, after preparation but before
   namespace mutation, during actual link/replace, after mutation before parent
   sync, after confirmed save and during cleanup/reporting. Check actual old/new
   bytes, recorded outcome, recovery retention and exit precedence for create and
   replacement. Include stop plus post-mutation sync failure and broken output.
6. **No-stop compatibility:** phone/code, actual2FA, invalid/expired/wait/unsupported/
   password-setup and explicit uncertain checks; migration, optional hash/native
   state, unchanged proxy/device settings; noTTY and redacted args; local retry
   with no extra auth; sidecars/stale targets/collisions and native constructor/
   commit/close/sync failures. Run the existing real-terminal scenarios too.

Passing result: the complete candidate observes these outcomes in one full run,
with private files, no leaked source ownership and no changed acceptance assertions.
The successful six planning probes alone do not close this gate. If the local
owner cannot meet the contract without changing LoginFlow or the publisher's
established meaning, record that disqualifying result and return to desc/traverse.
If candidate mechanics fail the stated contract, stop for plan/critic reassessment;
do not silently promote a locally patched candidate. Fixture-only corrections
must retain failed evidence, preserve assertions and rerun the entire prebuild.

### Output
Fresh critique/folded revision4 and a separately recorded full combined candidate
PASS, with source hashes and observed phase histories before product edits.
### Safe in nature
True — work-folder experiment and synthetic owned processes only; product untouched.
### Peripheral concepts
Critic-d premise inventory, same-session review, controlled TL transport, real SRP,
PTY/signals, candidate hashes, phase coverage, failed-evidence retention.
### Hardness Lvl
5

## Step 3 — integrate the qualified lifetime with the retained feature

### Proposed changes

Promote the passing command owner/driver into tgdata/login_cli.py without divergence
from its candidate. Wire _login, _settle_flow, confirmations, _publish and finalization
through that one lifetime. Remove the old per-call KeyboardInterrupt rerun loop and
separate resettable publication stop flag; feed the persistent flag to the existing
publisher's stop predicate. Keep exactly one event loop across the conversation.
No worker, ordinary reader or public LoginFlow API change is planned.

Retain the complete feature contract, rather than treating revision3 as a one-line
bug fix. Installed/module interface remains tgdata-login --config CONFIG [--replace]
and python -m tgdata.login_cli; config defaults to config.ini. Cached factory policy
continues to choose explicit session_file, legacy username, then telegram_session;
append .session as the native reader does, use invoking CWD and literal tilde,
require an existing parent and show the escaped absolute destination before auth.
No phone/code/password/credential CLI option; hide all three inputs and refuse
getpass echo fallback. Prompt only at a settled eligible step. Preserve invalid-
input correction, explicit one-time auth-only checking, waits, restart/unsupported/
password-setup refusal and completed-auth-plus-error handling. A local retry uses
the retained credential without a new source action.

Retain tgdata/login_file.py unless the fresh plan critique establishes a necessary
contract change, which must be folded/tested before this step. Its final contract:

- Native conversion decodes through StoredSession, validates256-byte key/DC/own-ID0,
  copies optional own-account cache only if present, and preserves available native
  update/takeout state. No generic public converter or invented hash. Prepare a
  closed0600 SQLite candidate in a0700 private directory; read back and fsync.
  Native construction/save/close failures retire the real connection or retain
  cleanup-required evidence; never publish a partial candidate.
- Default existing-file refusal precedes auth. Replacement requires --replace and
  explicit target/account/stopped-reader confirmation. Snapshot regular files with
  no-follow reading and identity/content checks; reject symlinks, all SQLite
  sidecars and changed parent/target. An initially absent target remains no-clobber
  even with --replace. These checks do not establish global reader exclusion.
- Sync staging's parent before auth. For replacement, verify and sync old bytes
  through previous.session, then its private directory, before replacing. Preserve
  the post-publication parent-sync success barrier. New creation uses no-clobber
  link; existing replacement uses the backed-up native candidate. Failure before
  mutation leaves old bytes intact; an effect-uncertain failure retains recovery
  files and refuses blind retry/rollback. Cleanup failure does not erase success.

Version, exports, dependencies and session naming remain unchanged. Trusted local
POSIX/stopped-reader preconditions remain; no lease, auto-resend, durable login
checkpoint, signup/QR flow or ScrapeOps change is added. Stop semantics apply to
the command's deliberate lifetime and do not change the library's background auth.

### Output
A terminal command whose qualified lifetime governs the existing login/publication
feature, without a second source of authentication or storage truth.
### Safe in nature
False — terminal control flow, signal policy and credential publication integration.
### Peripheral concepts
Factory config caching, LoginFlow status, native session conversion, local retry,
file effect/durability ordering, signal restoration and saved/uncertain outcomes.
### Hardness Lvl
5

## Step 4 — permanent phase tests and operator documentation

### Proposed changes

Extend tgdata/smoke_tests/test_48_terminal_login.py with the prebuild's regression
histories, especially actual native-SRP SIGINT, completed exceptional tasks and
phase transitions. Preserve original tests and the rejected probe evidence.
Timeout-killing a synthetic child must fail acceptance, never count as a successful
stop. A real signal marker and phase/source effects must be asserted; a timer that
fires after computation has ended is non-covering and must not silently pass.

Keep real LoginFlow/SDK/SRP/SQLite/reader usage. Observe old/new bytes, stop status,
retained files, terminal modes, source counts, all task/wire retirement and signal
handler restoration. Do not test only internal booleans/callback call order. A
component that deliberately refuses disconnect produces safe refusal rather than
a fabricated successful retirement. Tests may clean their own fixture after
observing that outcome. No real credentials or network login is used.

Update docs/terminal_login.md and smoke README for the clarified stop behavior:
Ctrl-C requests cooperative stop during authentication, native computation/cleanup
may need to settle, repeated Ctrl-C does not bypass that settlement, and already
in-flight auth may have effects. Stop prevents a later prompt/auth action/save;
publication already observed remains saved or uncertain even with exit130.
Keep the documented exit codes and file-first guarantees. Do not advertise bounded
shutdown or live Telegram validation. README's command example and setup.py's
entry point stay correct; update only if the qualified integration requires it.

### Output
Permanent regression coverage for executing, suspended, completed and retiring
work, plus public guidance consistent with observed command outcomes.
### Safe in nature
True — tests/docs only; no real login, release or active environment change.
### Peripheral concepts
Real terminal state, secret-free diagnostics, deterministic phase markers,
synthetic bounded processes, public cooperative-stop semantics.
### Hardness Lvl
4

## Step 5 — supported verification, commits and renewed review handoff

### Proposed changes

Compile and check Python3.7 grammar; run new smoke48 then15/17/32/41; run the full
supported12–19/22–46 plus48 and all seven demos. Current baseline is1,005 actual
offline checks in34 suites before added cases, with3 deliberately skipped live
checks excluded. If dev advances, reconcile actual suite inventory and counts;
#45/test47 is currently separate and must not be silently imported or excluded
after a later merge. Use Python3.11.10/Telethon1.45.0 and missing configuration for
live cases. Record per-suite counts, failures and exact before/after source hashes.

Re-run isolated installed-command verification using the existing offline tools:
actual console and module entry, isolated import/source match, help and headless
refusal; include the new native-SRP stop behavior through an installed-command
synthetic harness. Do not install dependencies into the active environment. New
phase tests and the full prebuild must pass; prior revision2 PASS is historical.

Review the resulting whole feature diff against this plan and desc. Commit product,
tests and public docs together and work evidence separately. Preserve archive
feat/50-terminal-account-login and product-only feat/50-terminal-account-login-pr;
update the same PR51 after qualified implementation with only product commits.
Refresh issue50's revision-specific checklist from committed evidence, without
claiming the rejected review has been answered merely by a new plan. Preserve the
original checkout's version edit, duncan, unrelated guides and separate PR49.

Next review cycle remains mandatory: renewed merge-check against the actual new
diff and folded plan, then fresh in-session PR critique, both committed/posted.
Any Medium/High rejects again. A second rejected PR gate requires a return to the
description/traverse under CONTRIBUTING §7.4, not automatic revision5 patching.
User go-ahead remains necessary for merge; no version bump, release or deployment.

### Output
Verified revision4 implementation, traceable product/work commits, updated draft
PR and honest handoff to the renewed two-part merge gate.
### Safe in nature
False — publishes code/evidence and updates externally visible workflow status.
### Peripheral concepts
Full regression baseline, installed command isolation, product/archive separation,
GitHub checklist honesty, repeated-rejection rule, model/effort verification.
### Hardness Lvl
3
