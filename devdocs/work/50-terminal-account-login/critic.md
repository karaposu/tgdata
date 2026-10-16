---
model: unknown
effort: unknown
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the complete command cannot satisfy terminal settlement, stop admission
and retained source/file semantics with the private input owner and existing real
components, or the candidate violates a specified acceptance history.
Affordable now: yes — local candidate and bounded real-PTY/SDK/filesystem runs;
no account, network login or deployment required.

Experiment: revision5 step2's FULL combined suite using both candidate modules,
actual LoginFlow/Telethon1.45/native SRP/session/publisher/reader, controlled wire
replies, real PTYs and real signals. Include all retained23 groups/25 terminal
scenarios/17 source-file histories/8 stop phases/14 publication crossings plus
new terminal lifetime, support/refusal and Enter/EOF first-signal histories. Add
R1's actual ISTRIP refusal before source work and per-prompt mode-change refusal.
Cost: bounded candidate/harness development and local subprocess execution.
Must precede: every product edit/promotion (step3); step1 candidate work is the
experiment itself. Fold selected R1 into revision6 before candidate qualification.
Disqualifying result: any candidate contract failure in the complete composition;
record FAIL and return under task-impl's meaning-gap procedure. Do not tune an
architectural candidate failure into a pass. Proven harness-only corrections must
preserve assertions, failed evidence and require a complete rerun.
Passing result: one full run observes every required terminal/source/file outcome,
including safe failure on deliberately irreparable restoration, with unchanged
product hashes and no timeout kill counted as a successful stop. Input mocks are
non-covering for terminal claims; live source delivery is not claimed.

## High-level summary

One Medium, zero High/Low. The input mode checks omit a real byte transformation:
ISTRIP changes valid UTF-8 input into different valid text before decoding. The
private owner is the correct place to refuse it. No broader auth/file redesign is
needed. The full candidate experiment remains unrun, so the behavioral gate is
REORDER even though the plan already places it before product promotion.

Subject: revision5 e065575, desc dbe9d97, traverse47d3c99, both rejected reviews,
actual product34907d4-equivalent archive and dev77f2f53. Fresh in the same warmed
session, no subagent. Current CLI, complete retained combined harness and native
terminal experiment read; LoginFlow/SDK/SRP/native publisher/reader contracts remain
in the inherited full warmed context. New behavior was measured below. Current-turn
model/effort cannot be verified from available metadata; unknown is not §9 clearance.

## Premise Inventory — ranked by waste if false

### P1 — the explicit input lifetime composes with the whole command

First dependent product step3 (candidate cost step1); false ownership would waste
integration/tests/docs through step5. Test scheduled step2 before promotion. Cheapest
covering earlier test is that full local candidate experiment, affordable now.
The inquiry22cases establish local feasibility but do not cover LoginFlow, native
publication or full command transitions. Old r4 input mocks and its getpass matrix
are non-covering for the replacement input module. Existing actual source/file
histories are retained and rerun with the candidate; no fake success receipt counts.

### P2 — supported canonical terminal modes preserve the submitted value

First dependent step1 input decoding/validation and product step3. Wrong policy can
submit altered credentials. Test scheduled step2 support matrix; cheapest earlier
native observation is a few-line PTY probe, now run in replan-r5/istrip_probe.py.
Observed UTF-8 bytes[195,169,10] became[67,41,10], decoding successfully to C) newline.
The plan's strict decode does not establish original byte fidelity. R1 below closes
this within the selected input boundary. Full candidate refusal still needs step2.

### P3 — stop/wait/cleanup are separate effects

First dependent step1/3; false behavior invalidates terminal integration and final
reporting. Scheduled full step2. Native inquiry proved nonthrowing flag alone does
not wake ordinary read, fd close does not restore modes and getpass may use a
controlling terminal different from stdin. Finite wait/nonblocking owned fd directly
address these observations. Full first/repeated signal placement and restoration-
failure matrix remains required; scalar stop/result mocks cannot supply it.

### P4 — native auth/publication contracts can remain unchanged

First dependent step3, already supported by prior real LoginFlow/SDK/SRP/SQLite/
reader evidence. Step2 reruns the complete composition before integration. Cheapest
earlier covering check is the retained suite with candidate input substituted.
The two reviewed failures occurred in local lifetime handling, including one before
any code request. No evidence calls for an auth, database schema or publisher change.
Live delivery/real-account2FA and native3.7 remain explicitly unqualified execution
limits, not claimed by controlled wire responses or grammar checks.

## Restart Check

| Observed failure | Established mechanism | Addressing design |
|---|---|---|
| Native-SRP Ctrl-C hangs | Completed task with KeyboardInterrupt is driven again | Retained completed-result consumption and one action registration; step2 real native-SRP regression |
| First signal after Enter/EOF leaves echo off | Outer input flag injects exception into getpass restoration | Step1 removes exception input policy and owns exact fd/modes through checked restoration; step2 independent first-signal histories |
| Isolated input success overstated composition | Earlier tested history differed in first-signal timing | Full step2 matrix crosses exit reason, timing and concrete resource effects before promotion |

## Inherited Lessons

- Wrapper state is not resource settlement: step1 requires observed modes and no
  returned value until retirement; step2 observes actual selected terminal.
- A nonthrowing stop flag alone does not wake input: step1 requires finite wait and
  nonblocking read; step2 stops actual waiting without more input.
- Two TTYs can differ: both preflight and reader bind /dev/tty, with step2 two-terminal
  observation. A stdin-only cleanup fixture cannot qualify that case.
- Source/file outcomes survive later stop: retained actual publication/native-reader
  histories in step2 precede integration; no newly invented rollback semantics.
- More passing tests do not imply missing-history coverage: step2 names explicit
  new normal/EOF/first-signal and failed-restoration outcomes before product work.
- Avoid a shared framework without a second matching consumer: private CLI module
  only; no worker/frontend/public API changes.

## Risk R1 — input can be silently changed before UTF-8 decoding

**Risk**
An operator can type the correct password, but a supported-looking terminal can
change its bytes before the command reads them. The changed text may still be valid
UTF-8, so decoding succeeds and the command submits a different password. That can
cause a failed login attempt without explaining the real cause.

Revision5 step1 checks canonical/ISIG and CR/LF mappings but omits termios.ISTRIP
(and IUCLC on hosts exposing it). In the planned tgdata/_terminal_input.py preflight
and per-prompt validation, ISTRIP can convert bytes0xc3,0xa9 for é into ASCII C).
replan-r5/istrip-result.json reproduces this with real termios and PTY input. Strict
decode at the future reader does not detect the alteration. No product patch made.

**Severity:** Medium.
**Category:** input compatibility / authentication correctness.
**Impact:** incorrect credential submission and avoidable remote login failures.
**NoobEng:** canonical editing and terminal byte transformations happen in the OS
before os.read. LoginFlow sees only the resulting string and cannot reconstruct
what the operator typed; the private input owner must admit only supported modes.
**Affected areas:** candidate/private terminal preflight and per-prompt validation,
CLI support docs, real-terminal tests; no auth or session schema change.

### Mitigation — Quick
Reject all non-ASCII decoded strings.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust
Reject ISTRIP and available IUCLC flags in preflight and every prompt before mode
mutation/source work. Retain explicit canonical editing semantics; test actual
ISTRIP initially and changing between prompts, with no subsequent source request.
**Why this is robust:** prevents the observed transformation at the owner that
can inspect it, without changing the user's terminal policy or authentication.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Long-term
Normalize supported input transformations within the private owner, restoring all
original settings, and qualify a broader line-input policy across supported hosts.
**Why this is long term effective:** could accept additional terminal configurations
by controlling the transformation rules rather than refusing them.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

## Other checked concerns

No public API/database/dependency change. Private module needs safe import/help on
non-POSIX, covered in the plan.128-byte policy is explicit, not silent truncation;
canonical kernel overflow and partial EOF remain required real measurements. Flushing
failure must not skip restoration, restore readback must not fabricate success,
and close uncertainty blocks value release. Prompt output errors must settle modes.

The full test adaptation must load both candidate modules in every child/entry
path; an old-product module invocation is non-covering for the new candidate.
Input-mocked source/file tests stay useful but cannot qualify terminal preflight.
Two-terminal and refusal histories must use actual terminal state. The plan's
acceptance statements already require these; they are experiment checks, not extra
rated findings. SIGINT and cooperative foreground contexts are the declared scope;
process kill, external terminal mutation and universal job-control recovery are not
proved. No new guaranteed SDK/filesystem/disconnect time bound is introduced.

## Execution limits carried unchanged

Live account setup, native3.7 runtime and current-turn §9 verification remain OPEN
as declared. No dependency installation, real login, product promotion, PR approval,
merge/release or downstream deployment is part of this review/prebuild turn.

## Phase 3

Pending selection; Phase2 proposals above are intentionally unticked.
