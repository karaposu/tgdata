---
status: active
model: gpt-6-astra
effort: xhigh
refines: devdocs/work/50-terminal-account-login/traverse/finding.md
---
# Finding: terminal login must own terminal restoration, not infer it from control flow

## Question

After two rejected reviews of #50, the terminal login command, what assumption
must change before another plan? The goal is a usable phone/code/password command
that saves a reader session and stops safely, without rebuilding unrelated parts
of tgdata.

## Finding Summary

- The missing responsibility is ownership of terminal input through restoration.
  An outer “input is active” flag cannot establish what the input helper has done.
- A stop request, a settled authentication action, restored terminal settings and
  a published session file are separate facts. None proves the others.
- Give one private input component the selected terminal and its original settings.
  It releases a value only after restoring the terminal, or reports a safe failure.
- During command-owned work, record SIGINT as stop intent without raising an
  exception through unknown cleanup code. Waiting for input must still wake and
  stop without requiring another keystroke.
- Keep the existing LoginFlow authentication API and native session publisher.
  Neither reproduced defect supplies a reason to replace them.
- A small native experiment passed 22 boundary cases. This establishes feasibility
  of the input boundary, not readiness of the complete command.
- Revise the description now. A later plan and full combined prebuild must qualify
  the complete command before another implementation attempt.

## Changes from Prior

This finding REFINES
`devdocs/work/50-terminal-account-login/traverse/finding.md`, the original
file-first command inquiry. Its native session format, explicit replacement,
local save retry and truthful publication outcomes remain the intended contract.
The triggers are the first and second rejected PR reviews, preserved in
[pr-critic_r1.md](../../work/50-terminal-account-login/pr-critic_r1.md) and
[pr-critic.md](../../work/50-terminal-account-login/pr-critic.md).

What changed is the meaning of “terminal interaction between settled actions.”
That ordering remains useful, but an opaque input helper plus exception handling
does not establish terminal settlement. The description must name the resource,
its owner, the release condition and what happens when restoration itself fails.
Revision 4's plan remains historical evidence; it must not resume unchanged.

The original action commitments change as follows:

- MUST drift: prior text “qualify and plan the file-first command and publication
  outcomes.” New text “revise #50's description around explicit terminal ownership
  and independent stop, authentication and publication outcomes.” Rationale: two
  review failures require correcting the upstream contract before planning again.
- MUST drift: prior text “run one combined experiment using real LoginFlow, native
  SQLite, filesystem publication, ordinary reader reopen and terminal interruption.”
  New text “qualify the complete candidate with real LoginFlow, native SQLite,
  filesystem publication, ordinary reader reopen and owned terminal interaction.”
  Rationale: the terminal's identity and restoration must be observed explicitly;
  the old composition passed while a first signal during normal/EOF cleanup failed.
- MUST drift: prior text “test failures before and after publication, explicit save
  retry, repeated interruption, secret-output refusal and cleanup precedence.”
  New text “retain publication, retry and secrecy tests, and cross input exit
  reasons with first/repeated stops and resource acquisition/restoration failures.”
  Rationale: replaying only a read-time interruption missed an independent history.
- COULD: live Telegram delivery and optional 2FA remain gated by exclusive setup,
  explicit authorization and successful local composition. No scope change.

## Finding

### 1. Both failures confused a control-flow event with a resource outcome

The first implementation could finish an authentication task with
KeyboardInterrupt, then ask the event loop to drive that completed task again.
The command hung. Revision 4 corrected that particular task-driving failure.

The second failure happened before any Telegram code request. The command marked
an entire getpass call as “input.” After normal Enter or EOF, getpass was restoring
the terminal, but that outer flag still allowed the first SIGINT to raise
KeyboardInterrupt. Restoration was interrupted and echo remained disabled after
the command returned. The passing repeated-signal test had first signaled during
the read, changing the flag; it did not cover this history.

The new inquiry reproduced both normal-input and EOF restoration failures, with
exit 130, echo off and zero code requests. A read-time stop control restored echo.
The observations are recorded in [input-restore-result.json](evidence/input-restore-result.json).
The first review's native-SRP correction remains supported by its later review
record; this inquiry did not rerun the complete authentication suite.

A task being done establishes a task result. A stop being requested establishes
intent. Neither establishes that terminal settings were restored or that a file
was never published. The command needs separate observations for those effects.

### 2. Terminal input needs one complete, private lifetime

The input component must know which terminal it changed and retain access to it
until it has restored the captured settings. Its lifetime includes acquisition,
mode changes, waiting, normal input, EOF, errors, stopping, restoration and release.
A caller must not receive an input value and begin a login action before this
lifetime is settled.

Three native observations constrain the design. Terminal settings survive closure
of the descriptor that changed them. getpass can select a controlling terminal
different from stdin. A nonthrowing signal handler can record a stop while an
ordinary blocking read continues waiting for input. These facts rule out “close
the descriptor,” “restore stdin,” and “set a flag” as complete solutions.
See [semantics-result.json](evidence/semantics-result.json).

The preferred direction is a private owner with an interruptible wait and a
nonthrowing stop request. This avoids raising an exception through hidden helper
cleanup. Python explicitly cautions that exceptions from signal handlers can
appear at arbitrary execution points; a nonraising handler can also allow a
system read to restart. [Python signal documentation](https://docs.python.org/3.11/library/signal.html#note-on-signal-handlers-and-exceptions),
[Python os.read documentation](https://docs.python.org/3.11/library/os.html#os.read).

This does not promise that a broken terminal device or failed operating-system
call can always be repaired. If restoration cannot be established, input is not
released, later login/save admission stops, and diagnostics report the failure
without secrets. An ordinary SIGINT must not itself abandon otherwise possible
restoration. The distinction is between avoidable interruption and actual I/O
failure, not between success and a concealed cleanup error.

### 3. Preserve the working authentication and publication boundaries

LoginFlow is tgdata's existing noninteractive phone/code/optional-password API.
It owns Telegram authentication and returns an opaque credential without writing
the configured reader session. The command should keep using it and its existing
proxy, device, wait, unsupported-response and cleanup rules.

A stop prevents new prompts, authentication actions and save attempts. An already
started source action may nevertheless have reached Telegram. The command must
settle that action and preserve its known or uncertain outcome, rather than claim
that stopping reversed it. Cancellation remains directed at the owned action;
repeated stop requests must not create competing cleanup owners.

The existing private bridge converts a completed credential into a native
Telethon SQLite session. The publisher separately distinguishes pre-publication
failure, confirmed publication and uncertain publication. Those outcomes remain
true even if the process later exits because of a stop. Recovery material must
survive uncertainty, and an explicitly retried local save must not request a new
Telegram code.

This division is small enough for one deliberate CLI. A shared worker supervisor,
a public terminal framework or a new authentication implementation is not justified
by either observed failure.

### 4. Native experiments establish a direction, not a finished command

An inquiry-only prototype owns a terminal descriptor, captures its settings,
uses a controlled wait, records stop intent and checks restoration before
returning a value. It passed 22 cases covering ordinary input, Unicode, kernel
editing, EOF, rejected input, first and repeated stops at lifetime boundaries,
and failures while reading or changing/restoring terminal modes.

Two cases deliberately made restoration fail. Their correct result was an explicit
failure with no released value; they did not restore the terminal successfully.
The test harness then repaired its own synthetic terminal. The evidence therefore
supports truthful failure handling, not a claim that restoration is infallible.
See [owned-terminal-result.json](evidence/owned-terminal-result.json).

The prototype uses a small canonical UTF-8 input sample with a 128-byte limit.
It does not determine production encoding, line limits, all terminal contexts or
complete LoginFlow/file integration. It must not be copied into the product merely
because this experiment passed.

The first experimental harness misclassified an exiting child's early terminal
EOF as a timeout before reaping it. The harness was corrected within the same
deadline; terminal logic and acceptance assertions were unchanged. Earlier sources
and logs remain under `evidence/`. Some controlling-terminal probes also required
execution outside the sandbox to exercise the intended terminal topology.

## Inherited Commitments Re-test

- **Commitment:** reuse LoginFlow rather than duplicate authentication.
  **Source:** original finding, Finding and Reasoning.
  **Re-test status:** RE-TESTED — commitment confirmed.
  **Evidence:** source/interface analysis in [Sensemaking](docarchive/sensemaking.md)
  and [Critique](docarchive/critique.md); the freshly reproduced terminal failure
  makes zero code requests. No new authentication semantics are required.
- **Commitment:** publish native session files through the private bridge; keep
  explicit replacement, preserved prior bytes and uncertain-write outcomes.
  **Source:** original finding, Finding.
  **Re-test status:** INHERITED-WITHOUT-RE-TEST.
  **Reason:** the earlier native conversion/publication and reader-reopen evidence
  is retained. This upstream inquiry changed no product code and did not rerun that
  full suite. The future combined candidate must requalify the composition.
- **Commitment:** retry local saving with the completed credential, without remote
  replay; keep custom-store CLI, durable resume and active-reader rotation deferred.
  **Source:** original finding, Finding and Next Actions.
  **Re-test status:** RE-TESTED — commitment confirmed.
  **Evidence:** alternatives compared in [Innovation](docarchive/innovation.md) and
  [Critique](docarchive/critique.md); none addresses the actual terminal failures
  by broadening storage, replay or reader coordination. Runtime retry evidence is
  inherited, not newly executed.
- **Commitment:** synchronous input between settled actions is a sufficient boundary
  when combined with helper cleanup and interruption handling.
  **Source:** original finding, Finding; revision 4's interpretation of that boundary.
  **Re-test status:** RE-TESTED — commitment found INVALID.
  **Evidence:** normal/EOF first-stop failures and native descriptor observations.
  Ordering survives, but the input owner must establish restoration independently.
- **Commitment:** one command owner should settle the current action before exit.
  **Source:** first PR critique and its selected mitigation.
  **Re-test status:** RE-TESTED — commitment confirmed but frame revised.
  **Evidence:** the terminal observations show that task completion alone is not
  settlement of every resource. Apply explicit terminal ownership alongside source
  cleanup. The native-SRP fix's execution evidence is inherited from review 2.
- **Commitment:** the exact selected terminal and original modes need an owner
  through restoration, regardless of input exit or first-stop timing.
  **Source:** second PR critique and review-r2-handoff.md.
  **Re-test status:** RE-TESTED — commitment confirmed.
  **Evidence:** fresh failing native reproduction, three semantics observations and
  22 bounded ownership cases cited above.
- **Commitment:** combined prebuild and permanent failure tests precede readiness.
  **Source:** original finding, MUST actions.
  **Re-test status:** RE-TESTED — commitment confirmed but frame revised.
  **Evidence:** prior passing totals omitted the now-reproduced first-stop history.
  Qualification must cross exit reason, signal timing and resource effects.
- **Commitment:** live delivery/2FA remains supplemental and requires an authorized
  exclusive account setup after local composition passes.
  **Source:** original finding, COULD action.
  **Re-test status:** INHERITED-WITHOUT-RE-TEST.
  **Reason:** no live source work was requested or performed in this inquiry.

## Next Actions

### MUST

- **What:** revise #50's description around explicit terminal ownership and independent
  stop, authentication and publication outcomes.
  **Who:** task-desc in the existing #50 work folder.
  **Gate:** now, before another plan or product change.
  **Why:** replace the invalid upstream input assumption while retaining useful scope.
- **What:** qualify the complete candidate with real LoginFlow, native SQLite,
  filesystem publication, ordinary reader reopen and owned terminal interaction.
  **Who:** a later task-plan/critic/prebuild pass, using controlled source replies.
  **Gate:** after a new plan and fresh critique, before product edits.
  **Why:** establish actual composition and supported input contexts; this prototype
  is only boundary feasibility evidence.
- **What:** retain publication, retry and secrecy tests, and cross input exit
  reasons with first/repeated stops and resource acquisition/restoration failures.
  **Who:** the later prebuild and permanent offline qualification.
  **Gate:** full combined prebuild before implementation; permanent tests before
  renewed merge check and PR critique.
  **Why:** test independent failure histories instead of only the latest reproducer.

### COULD

- **What:** qualify live Telegram delivery and optional 2FA with an isolated account.
  **Who:** maintainer and implementation agent.
  **Gate:** explicit authorization and an agreed exclusive session setup.
  **Why:** add source-level evidence beyond controlled component tests.
  **Depends-on:** MUST “qualify the complete candidate.” GATED until local composition passes.

### DEFERRED

- **What:** guarded getpass reuse or a parent-owned helper process.
  **Gate:** demonstrate a required context that the local owner cannot support, or
  prove guarded reuse has smaller total responsibility with the same guarantees.
  **Why (if revived):** meet a concrete input requirement without unverified cleanup.
- **What:** create-only delivery without replacement.
  **Gate:** replacement itself fails qualification, or the user narrows re-login scope.
  **Why (if revived):** simplify publication while preserving honest user expectations.
- **What:** custom-store CLI, durable resume, a generic session/operator framework
  or active-reader rotation.
  **Gate:** a named consumer needs the feature and its backend/ownership contract.
  **Why (if revived):** serve an actual additional workflow, rather than absorb it into #50.
- **What:** broad platform and terminal-mode support.
  **Gate:** a named required runtime or terminal context falls outside initial qualification.
  **Why (if revived):** expand evidence and support deliberately.

## Reasoning

The explicit local input owner survives because it addresses the observed failure
and the native resource facts. Nonthrowing stop intent also survives, paired with
a wait that can stop; a flag alone fails that requirement. Retaining LoginFlow and
the publisher preserves separately justified source and file semantics. Testing
resource outcomes survives because it would expose both reviewed failures without
assuming a wrapper's phase label was accurate.

Guarded getpass remains a reserve, not a selected shortcut. It must prove that the
guard owns exactly the terminal selected by getpass and covers acquisition and
all exit paths. Restoring stdin or adding a catch around the known restore site
does not establish that. A parent-owned helper is also a reserve: child death does
not restore terminal settings, so process isolation adds IPC and secret lifetimes
without removing terminal ownership. Local feasibility gives no current reason
for that extra extent.

Default exception unwinding or immediate exit was rejected: it can interrupt
restoration or misstate file effects. Caller repair was rejected as an acceptance
criterion: tgdata must establish its own resource outcome, and report genuine
failure rather than borrow a caller's later cleanup as evidence of success.

An external frontend alone and a credential-installer-only command were rejected
for this delivery because they remove the requested terminal login conversation.
The existing Python API remains available to such consumers independently.

A direct authentication/session rewrite was rejected because neither failure is
in those components, and it would reopen configured-session safety and source
uncertainty rules. A universal transaction or lease was rejected because terminal
settings, remote authentication and file publication do not share rollback rules.
They need distinct outcomes even when one command coordinates them.

A shared supervisor and a universal qualification framework were rejected for
this delivery because no second matching consumer or required universal platform
contract exists. Test counts were rejected as a readiness argument: the previous
large suite passed while an independently specified resource postcondition failed.

Create-only publication remains a legitimate fallback, but it does not fix either
observed defect. There is no causal basis for dropping qualified replacement solely
because two reviews rejected terminal handling.

The inquiry completed one full sequential traverse. Repeated challenges within
its critique tested the alternatives; this is not a claim that multiple complete
traverses or a fresh product PR review passed. Full comparisons are preserved in
[Critique](docarchive/critique.md). The onward directions remain in
[routelister.md](routelister.md) and [_route.md](_route.md).

## Open Questions

### Monitoring

The later combined prebuild must choose and test production input encoding, line
length, supported foreground/main-thread terminal contexts, restored-mode
observation and final reporting alongside source/file failures. Check that the
private input owner remains small rather than becoming a general terminal framework.

### Blocked

Real Telegram delivery and real-account 2FA remain unqualified without an authorized
exclusive account setup. Native Python 3.7 runtime qualification is unavailable;
Python 3.11/Telethon 1.45 evidence and syntax compatibility are distinct claims.

### Research Frontiers

Full POSIX primary pages could not be retrieved in this pass. Python API text,
local standard-library code and native macOS observations ground the current
conclusion; search excerpts are not full or universal standards verification.

### Refinement Triggers

Reopen guarded-helper reuse only with proof of exact terminal binding and complete
restoration coverage. Reopen process isolation if a required input context defeats
the local owner. Reopen the auth or publisher boundaries if complete-candidate
experiments demonstrate a failure inside those contracts. Any new Medium/High
review finding must be handled under CONTRIBUTING, not silently patched into this
inquiry's conclusion.

## Source Input

<details>
<summary>Raw user input for this finding</summary>

```text
: return to the description/traverse before another plan\
\
do it
```

</details>
