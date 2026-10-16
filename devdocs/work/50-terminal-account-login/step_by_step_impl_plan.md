---
model: gpt-6-astra
effort: xhigh
---
# #50 implementation plan — revision 8

**Critic folded:** 2026-10-16T21:33:21.243305+03:00 — 1 robust mitigation (2 implementation steps changed, 0 added).
**Status:** fresh critique REORDER; full combined prebuild PASS (prebuild-r8/result.json).
The experimental gate is satisfied; product promotion and verification are complete.
See implementation.md/verification.md. Renewed merge check and fresh PR critique remain pending.
First complete run:23 retained groups plus all50 terminal/20 profile-control/46 framing/
7 handoff cases and isolated installed entry/native-SRP checks; source hashes unchanged. Revision6 remains deprecated;
its failed critique is critic_r6_prebuild.md. The prior selected plan critique is
critic_r5.md. The new critic.md reviews revision7 at15e922d; revision7 is preserved in step_by_step_impl_plan_r7.md.

Inputs: desc.md79c7327, bounded-input finding e2f5ab6 and native evidence ffa0887,
terminal-ownership finding47d3c99, both rejected PR reviews, actual code and failed
prebuild-r6. Two PR gate rejections exist; the later failed plan experiment is not
a third PR review. The required upstream returns are complete; no PARKED description.
Same warmed session, no subagent; dev77f2f53 and product-only PR51 head34907d4 remain
unchanged. Current-thread2026-10-16T18:27:16.814Z verifies gpt-6-astra/xhigh; see model-verification-r8.md.

### What is the task

Deliver deliberate phone/code/optional-password terminal login using existing
LoginFlow and native session publication. Input must be observed and framed while
arriving, so oversized pastes are refused without truncated credentials or a lost
line delimiter. One private owner keeps the terminal hidden through invalid-line
disposal and restores exact settings before any value reaches authentication.
The initial pass reviewed/folded and completed the prebuild. The user then said
“continue”; product promotion and verification are now complete under this plan.

### Huge Hard Blockers

#### Planning Blockers

None open.

**Question:** can a small private input boundary observe oversized input, retain
bounded state and preserve terminal/source/file ownership?
**Why steps depended on it:** the canonical post-read limit in revision6 could not
observe its failed input; frontend behavior and its tests would otherwise be guesses.
**Status:** CLOSED — canonical premise false; bounded streaming with invalid-line
discard and staged restoration established on native macOS.46 input cases and7
real-component handoffs passed expected outcomes, including500,000 bytes plus newline.
**Source:** inherited desc.md Known Blockers; native inquiry evidence.
**Who closed it:** this warmed inquiry using actual PTYs/signals/SDK/native files.
This establishes the contract, not the complete next candidate or all platforms.

#### Execution Blockers

- **What must happen:** complete candidate qualification from step2. **Who:** the
  implementation agent after fresh plan critique/fold. **Blocks:** step3 and all
  product edits. **Status:** DONE — first full prebuild passed before product edits; result.json records exact coverage and hashes.
- **What must happen:** current-turn §9 model/effort verification. **Who:** session
  UI/metadata owner. **Blocks:** final review/merge clearance in step5. **Status:** DONE for this turn;
  matching active-thread metadata is recorded in model-verification-r8.md.
- **What must happen:** explicitly authorized exclusive account for supplemental
  live delivery/real-account2FA. **Who:** maintainer. **Blocks:** optional live part
  of step5 only. **Status:** OPEN; no live login is authorized here.
- **What must happen:** available native3.7 or another claimed host/runtime.
  **Who:** environment owner. **Blocks:** optional additional-runtime claims in
  step5. **Status:** OPEN; grammar checks are not native runtime proof.

### How this implementation moves toward desired state

Keep the authentication and native publisher. Replace the command's getpass/input
helpers and exception-injecting input phase with a private byte-observable reader.
Framing holds at most128 value bytes; invalid input is discarded through completion
without storing its remainder. Terminal restoration remains separate from value
acceptance, source settlement and file publication. Qualify the complete composition
before moving any candidate into product files.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Fresh plan critique and fold | Reviewed revision8 and explicit experiment criteria |
| 2 | Build and run the complete experimental composition | Full combined PASS or a recorded stop before product edits |
| 3 | Promote the qualified private input and command integration | Product code matching the tested candidate |
| 4 | Preserve regressions and document supported input | Permanent native tests and operator guidance |
| 5 | Verify and return to the same PR's review gates | Supported suite/install evidence and traceable commits |

## Step 1 — fresh critique and fold

### Proposed changes

Completed: fresh critic81598e2, robust R1 selection and fold70d32cf. The full experiment
then passed as recorded at the top; the procedural description below is preserved.

Run critic-d on this revision with desc.md, both PR rejections, the failed revision6
experiment and the new inquiry evidence. Write a new dynamic_critic_prompt.md and
critic.md; canonical files are intentionally absent so historical DO NOT IMPLEMENT
cannot be mistaken for a verdict on revision7. Preserve revision7 before a revision8
fold. Select mitigations through the skill's three passes; fold selected proposals
only. Do not re-critique the fold.

The critic must test the new premise, not merely verify the old two regressions.
Examine delimiter completion, partial writes/backpressure, invalid-state permanence,
Unicode editing, pre-prompt queue disposal, mode/control support, mutation-before-
restore ownership and terminal/source/file handoffs. An affordable behavioral
falsifier requires the real full experiment. A meaning gap follows the deprecation/
stop procedure; do not patch around an unestablished input contract.

### Output
Fresh review, selected mitigations, folded revision8 and prebuild pass/fail criteria.
### Safe in nature
True — planning/review records only.
### Peripheral concepts
Premise inventory, repeated rejection guard, native evidence versus composition,
private input scope, same-session criticism and model provenance.
### Hardness Lvl
5

## Step 2 — complete candidate prebuild before product edits

### Proposed changes

Build the complete candidate under a new work-folder prebuild-r8 directory, following
step3's design plus selected mitigations. Candidate modules are future
`tgdata/_terminal_input.py` and `tgdata/login_cli.py`; do not edit those product paths
yet. Remove inquiry instrumentation from the candidate. Load both candidate modules
in every child and installed/module test path; old-product invocation is non-covering.

Use real LoginFlow, Telethon1.45.0/native SRP, StoredSession, SQLiteSession,
LoginDestination and ordinary configured reader. test41 supplies controlled wire
responses only. Forbid socket connect/connect_ex; use synthetic credentials and
owned temporary files/terminals. Input-mocked source/file tests remain useful but
are explicitly non-covering for terminal behavior.

One full runner must cover all of the following, not just isolated successes:

1. Retained r4/r6 behavior:23 groups,25 actual PTY scenarios,17 source/file histories,
   8 command stop transitions and14 publication-stop combinations. Preserve completed
   exceptional-task consumption, exact cancellation registration, real native-SRP
   interruption, held source cleanup, saved/uncertain outcomes, file barriers and
   local retry without extra authentication.
2. All50 declared r6 terminal cases, including the13 previously unrun cases after
   its failed kernel_overflow test. The original5000-byte-plus-newline case must now
   finish with explicit oversized-input refusal, no publication and exact restoration.
   Keep normal/EOF first-SIGINT at phone/code/password/replacement/retry; all source,
   terminal and file assertions remain, with new documented input-policy expectations.
3. All46 new framing histories: prequeued bytes; plain/Unicode/split encoding; scalar
   erase/clear; empty/exact128-byte/Unicode128-byte values;129/5000/500000-byte and
   paced5000-byte rejection; overflow followed by erase/clear and valid-looking tail;
   malformed encoding; unsupported literal-next, flow-stop, quit, suspend and arrow
   controls; trailing lines; empty/partial EOF; waiting/discard cancellation;
   first/repeated and acquisition/read/framing/decoding/staged-restore/close signals;
   actual two terminals, ISTRIP and absent controlling terminal; persistent cleanup
   faults truthfully returning no value. Three injected persistent faults must not
   be described as successful physical restoration.
4. All7 real handoffs from the inquiry, plus the full prompt/source/publication matrix:
   actual plain/2FA native-reader reopen, oversized phone/password/retry confirmation,
   stop while discarding, first restoration stop. Add actual terminal VINTR byte
   (`\x03`) during normal and invalid input, not only os.kill(SIGINT).
5. Supported-profile checks: foreground/main thread/no existing event loop; canonical
   entry state/8-bit mode; forbidden transformations; configured controls and VINTR3;
   unavailable termios, unsupported/read-only external-processing states; malformed
   or disabled/overlapping bindings. Refuse before source work and before the first
   mode mutation. Background test cleanup belongs to its foreground fixture owner;
   the harness must not trigger job-control suspension by restoring from background.
6. [folded: R1, robust] Use actual quit/suspend/interrupt bytes at the protected
   intermediate canonical stage, before final original-mode restoration. No quit/
   suspend signal is re-enabled while the owner still owes hidden-mode settlement.
   Input retirement failures and admission races: apply failure before/after effect;
   stop before mutation; pre-prompt flush; invalid-line discard; both canonical/echo
   restoration stages; all flush/readback/close/output failures. Final restoration
   is attempted even if earlier cleanup fails. No unsupported-profile refusal should
   write terminal modes. Observe actual modes and descriptor release, not flags alone.

Every producer honors partial writes and records requested/accepted/consumed counts.
Do not mistake a nonblocking partial write for a fully delivered paste. No simulated
complete value, save-success receipt or timeout kill establishes behavior. Use explicit
markers for phase placement. Retain failed source/logs; a proven harness correction
may rerun the entire suite without weakening assertions. Candidate contract failure
is a failed experiment and invokes the skill's stop/deprecation procedure.

Record candidate, harness and all product source hashes before/after; a PASS requires
one complete run, every required history accounted for and no product source drift.
The inquiry46+7 PASS is a premise result, not this gate's result.

### Output
Full candidate composition result, manifests, observed outcomes and failure records;
only a complete PASS permits step3.
### Safe in nature
True — experimental files and owned synthetic resources only.
### Peripheral concepts
Real SDK/native filesystem/terminal composition, support determination, finite
producer contracts, secret-safe diagnostics, immutable evidence and test isolation.
### Hardness Lvl
5

## Step 3 — promote the qualified private input boundary

### Proposed changes

Promote only the fully qualified candidate bytes to `tgdata/_terminal_input.py` and
`tgdata/login_cli.py`. The following design is the candidate's blueprint, not work
to improvise after the experiment. No new public export or dependency.

**Acquisition and supported context.** Open an independent nonblocking `/dev/tty`
fd using NOCTTY. Keep stdin-terminal/main-thread/no-running-loop checks. Preflight
before LoginFlow/destination work and validate at every prompt. Require foreground
process ownership, canonical entry state, ISIG, CS8 and expected CR→LF mapping.
Reject ISTRIP, available IUCLC, PARMRK, IGNCR/INLCR and unsupported external-processing/
pending-output contexts rather than silently transforming credentials. Require usable,
distinct ASCII erase/clear/EOF/interrupt bindings, excluding newline/CR; require
VINTR=3 so the documented Ctrl-C actually produces SIGINT. Native prebuild determines
the exact supported constants and refusal cases; do not infer broad OS support from
function availability. Import/help remain safe when termios is unavailable.

Capture original settings before any mutation. A refusal or stop before mutation
closes the owned fd without flush or termios writes. Mark mutation as attempted
BEFORE the first tcsetattr call, so failure after an actual effect still restores.
This local bookkeeping records a possible mutation, never claims restoration succeeded.
Do not copy the inquiry prototype's instrumentation or unconditional restoration on
pre-validation failure into product; the native profile tests must cover this boundary.

**Input mode and invitation.** Copy the complete original mode including its control
array. Disable ICANON, ECHO, ECHONL, IEXTEN and software-flow processing (IXON/IXOFF/
available IXANY). Keep ISIG and its admitted VINTR. Disable VQUIT/VSUSP with the
native VDISABLE value; those input bytes are unsupported controls, not process exits.
Use VMIN1/VTIME0 and TCSANOW. Verify applied modes, flush queued input while hidden,
then display the prompt. This ensures prequeued bytes cannot answer a new invitation.

**Framing.** Use a finite50ms select wait and nonblocking reads of at most256 bytes.
Check persistent stop before/after waiting, after reading and during chunk processing.
Do not assume one read is one line. Collect at most128 UTF-8 bytes. Before overflow,
configured erase removes one scalar (strict decoding, no replacement characters),
clear-line removes the current candidate, newline completes and configured EOF stops
without a partial value. A completed empty string goes to existing LoginFlow validation.
Malformed UTF-8 or unsupported controls never become a credential. No normalization,
truncation, cursor/history/literal-next support or extra input framework.

**Invalid input.** On byte129 or an unsupported control, clear the candidate, latch a
fixed safe error kind and display a secret-free rejection indication. Consume/discard
until newline/EOF/stop without retaining the invalid payload. Erase/clear cannot undo
invalidity. Newline returns refusal after retirement; EOF/stop ends the interaction.
Input without a delimiter may wait but remains visibly invalid, memory-bounded and
cancellable. No new overall human prompt timeout is introduced. Discard bytes already
read after the first delimiter; queued typeahead is discarded during retirement.

**Retirement and errors.** On every potentially mutated path, discard queued input
while hidden; [folded: R1, robust] derive the intermediate state from the ACTIVE
protected profile, changing only ICANON to its original setting. Keep echo off,
VQUIT/VSUSP disabled, IEXTEN off and software-flow processing off. Flush the canonical
transition, then attempt the full original settings regardless of earlier cleanup
error. Only that final write restores original control bindings and echo together.
This settles the observed Darwin PENDIN transition without ignoring the bit or waiting
for output drain. Read back exact original attributes. Attempt owned-fd close once;
an uncertain close is not retried against a potentially reused descriptor. Flush,
restore/readback or close failure releases no value and reports a fixed safe kind.
Keep both primary operation and cleanup facts in diagnostics where needed; never print
underlying exceptions or input. Stop may select130 while restoration failure still
gets reported. A genuine OS failure is not promised repairable. Release a string only
after all required settlement succeeded and stop is checked again.

**Command handoff.** `_TerminalRun` keeps one sticky stop and at most one registered
source action. Remove `_input` and the SIGINT branch that raises KeyboardInterrupt.
All command-owned phases record stop; active source work receives at most one cancellation
bound to its exact registration. Preserve completed-task consumption without re-entering
the loop, stale-callback checks, explicit retirement and handler restoration. `_hidden`
and `_confirm` use the private reader with the run's stop predicate. `prompt` checks
admission before and after; it does not own another copy of terminal cleanup.

Keep LoginFlow's supported/uncertain/wait/retry semantics and one event loop. No new
auth/save after stop, and no remote rollback claim. Retain the native publisher/bridge:
actual key/DC/own identity/optional native state; private candidate/readback/sync;
create-only default; opt-in target/account/stopped-reader replacement; regular-file,
symlink/sidecar/changed-target checks; prior bytes/backups before replacement; confirmed,
failed-before-publication and uncertain effects; explicit local save retry without
reauthentication; cleanup cannot erase an observed saved/uncertain result. Session-name
precedence, invoking CWD/literal tilde, dependencies and version remain unchanged.

### Output
Private input/CLI code matching the qualified candidate, integrated with unchanged
source/session/publication contracts.
### Safe in nature
False — installed command input, signal, source-admission and cleanup behavior changes.
### Peripheral concepts
Terminal mode transitions, private resource ownership, Unicode/control framing,
LoginFlow outcomes, native session compatibility, publisher durability and retry.
### Hardness Lvl
5

## Step 4 — permanent regression coverage and public guidance

### Proposed changes

Move qualified cases into smoke48 using test-only PTY helpers that honor partial
writes and keep fixture cleanup separate from candidate success. Preserve both PR
rejection witnesses and the canonical overflow witness. Remove obsolete getpass-only
unit seams only when equivalent observable refusal/hidden-input coverage replaces them.
No changing an expected outcome merely to get a pass; explicitly trace the new input
policy to this plan/description.

Update docs/terminal_login.md and smoke README:128 UTF-8 bytes per input; hidden
confirmations; basic configured erase/clear/EOF and Ctrl-C; no cursor/history;
invalid line remains rejected until Enter/EOF/stop; queued input is discarded and
one prompted value should be supplied at a time. Explain scalar erase and Python API
availability for other input needs. No live validation, universal platform guarantee,
control over future writes after exit or bounded SDK/filesystem shutdown claim.
Keep existing command/config/re-login/recovery and exit-code documentation consistent.

### Output
Permanent native/integration regressions and operator-facing supported-input contract.
### Safe in nature
True — tests/docs, no real account or active environment change.
### Peripheral concepts
Input usability, source/file secrecy, deterministic phase markers, test producer
behavior, entry points and declared runtime/platform support.
### Hardness Lvl
4

## Step 5 — verify, commit and return to review

### Proposed changes

After implementation compile and check3.7 grammar, run smoke48 plus affected15/17/32/41,
then the full supported offline suites and seven demos. Reconcile the suite inventory
with fetched dev; #45/test47/PR49 is currently separate. The unchanged prior baseline
was1,010 checks across34 suites with3 live skips, not the new result to pre-fill.
Use Python3.11.10/Telethon1.45.0; report unavailable live/native3.7/other-host evidence.

Verify isolated installed and module entry paths, help/headless refusal and native-
SRP stop without changing the active environment. Record exact source hashes and
candidate/product equality. Failure beyond a small nonarchitectural correction stops
under the skill; retain evidence and never reclassify killed test processes as success.

Commit product/tests/public docs together and work evidence separately. Preserve
archive feat/50-terminal-account-login and product-only feat/50-terminal-account-login-pr;
update the same PR51 after verified implementation with product commits only. Keep the
original checkout's version edit, duncan, unrelated guides and PR49 separate.

Renewed merge check and fresh in-session PR critique remain required. Any Medium/High
rejects; three actual rejected PR critiques trigger task-impl decomposition. Current
plan-premise failure does not increment that count. Resolve §9 verification before
review/merge clearance. Merge needs go-ahead; no release/deployment/version bump here.

### Output
Verified implementation evidence and honest handoff to the same PR's renewed review
gates; no implicit merge approval.
### Safe in nature
False — later code publication and external issue/PR status updates.
### Peripheral concepts
Full regression/install evidence, archive/product separation, model provenance,
repeated-rejection rules and protected unrelated user edits.
### Hardness Lvl
3
