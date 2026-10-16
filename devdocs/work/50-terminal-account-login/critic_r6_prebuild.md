---
model: unknown
effort: unknown
---
**DO NOT IMPLEMENT — MEANING GAP**

Falsifier: —

Experiment: the full revision6 candidate composition requested by the revision5
critic. The initial review and selected R1 are preserved in critic_r5.md.
Result: FAIL — second full attempt passed23 retained groups/25 retained PTY
scenarios and36 new terminal cases, then canonical kernel-overflow input timed out.
Candidate and product hashes were unchanged;2026-10-16. Exact results and the
independent native diagnosis are in prebuild-r6/.

## High-level summary

The plan assumed that a128-byte check after a canonical read could reliably refuse
oversized input. That premise is false on the tested host:5,000 bytes plus newline
were accepted by the PTY writer but never produced a readable line before the
12-second child deadline. Killing that child is a failed test, not successful stop.

The complete gate therefore failed. No product promotion or local candidate patch
is permitted. Revision6 is renamed DEPRECATED_step_by_step_impl_plan.md. The false
premise is recorded as CLOSED with its observation under desc.md's Known Blockers.
The new input-framing contract must be established before a replacement plan.

## Meaning gap and evidence

Canonical terminal processing holds input until a line boundary is available.
The application does not observe each byte as it arrives. An application-level
limit smaller than the kernel limit consequently does not make a huge pasted line
observable: the kernel can reach its own limit first and fail to deliver the
newline to the application. The command then keeps waiting for input it cannot
validate. Its finite select timeout lets Ctrl-C be checked, but does not make the
oversized line readable or produce the planned input-limit refusal.

Revision6 step1 chose canonical line editing and validation after os.read, while
step2 explicitly required a larger-than-kernel input case. That case failed in the
actual complete CLI with real PTY, existing LoginFlow/native publisher and controlled
source transport. The ordinary128/129-byte boundary tests had passed immediately
before it. This is not another version of the already repaired SIGINT/getpass bug.

Independent canonical_overflow_probe.py removes the candidate and whole-command
harness. On the same native terminal, PC_MAX_CANON=1024;129 and130 total bytes
(including newline) were readable and exact. All5,001 bytes were accepted by os.write
but select found no readable line after250ms. The full CLI independently waited
12seconds without producing an outcome. The test harness terminated only its owned
synthetic child and counted that as FAIL.

Steps1 and3 must change their input mechanism or accepted input/timeout contract;
step4's public support and regression expectations depend on that choice. These
are not missing exception branches in a proven input protocol. Do not quietly
shorten the overflow test, omit it, accept timeout termination or promote only the
passing fixes. Existing auth/session/publication semantics need no change from
this observation.

## First attempt — separately identified harness error

The first full run passed the retained suite and23 new cases, then the test driver
sent a synthetic phone number after an injected wait failure had already restored
terminal echo. harness-diagnostic.txt shows the fixed error report before the
synthetic input echo, with zero code requests and restored settings. The driver now
sends no input for the two deliberately immediate wait-exit cases. No assertion or
candidate code changed; the failed harness source/log/manifests are retained.

The second run repeated the ENTIRE suite and passed those cases. Its later kernel-
overflow failure is a product-candidate premise failure, not treated as another
harness correction. No additional candidate edits or narrowed rerun followed it.

## What passed and what remains unqualified

The retained23 groups include25 actual PTY scenarios,17 source/file histories,
8 stop transitions and14 publication-stop combinations. The first Ctrl-C after
normal/EOF input passed at all five prompt types. Acquisition, snapshot, mode-apply,
read/wait/flush/restore/readback/close/output failures and normal Unicode/editing/
128/129-byte cases passed up to the failed37th new case. Deliberately failed
restorations correctly returned no value and reported failure; those two terminals
were repaired only by the harness after recording dirty modes.

Remaining new cases after kernel_overflow were not executed: invalid encoding,
partial EOF, typeahead, two terminals, absent/background/unsupported contexts and
mode changes. In particular, R1's native diagnosis is established and its validation
is in the candidate, but the full candidate's later ISTRIP cases did not run. Neither
that mitigation nor the overall product is declared fully qualified.

## Procedure and limits

The fresh review itself ran in-session, without subagents. It selected one robust
Medium mitigation, preserved in critic_r5.md and folded in ba00375. This experiment
failure is not a third rejected PR review; PR51 remains on unchanged34907d4 with
the two existing rejected reviews. Current-turn §9 metadata confirmation remains
pending. No real account/login, native3.7 runtime claim, merge, release or deployment.

No further mitigation tiers or implementation plan are written around this failed
premise. A subsequent description/contract pass must choose and demonstrate how
input becomes observable under overflow before task-plan is run again.
