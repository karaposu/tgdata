# Revision8 full combined prebuild — PASS

This experiment loads clean candidate_terminal_input.py and candidate_login_cli.py;
product files are unchanged. The input code has no inquiry observer hooks. All SDK,
auth/session/publisher/ordinary-reader components are real; source transport is
controlled and network connections are forbidden. No real credentials are used.

The fixed full runner requires:
-23 retained groups,25 PTY scenarios,17 source/file histories,8 stop transitions and
 14 publication crossings from the complete earlier suite;
-all50 r6 terminal cases, including its previously unrun cases;
-20 additional profile/physical-control checks (native unsupported contexts plus
 explicitly injected malformed/unknown profile observations);
-all46 input-framing histories, observed on the actual candidate with native syscall
 wrappers and read-only tracing of its bounded buffer/framing state;
-all7 selected real consumer handoffs;
-offline isolated installation of both candidate modules, generated console/module
 entry points and actual installed native-SRP interruption.

No input/result/restoration receipt is supplied by observe_candidate.py. It delegates
to the clean candidate and observes its actual syscalls, local buffer and transitions.
It may emit real signals/faults at those observed boundaries. Large discarded inputs
stop per-byte tracing after invalidity; native reads keep measuring buffer/chunk size.
This is test instrumentation, not code that fixes the candidate's terminal state.

Explicit test adaptation from the failed canonical candidate:
-Each producer honors and records partial writes. Native mode classification now
 distinguishes initial noncanonical mode, protected canonical settling and final
 original-state restoration.
-small_canon now proves canonical capacity is irrelevant to the streaming framer;
 it returns a small PC_MAX_CANON only, preserves real PC_VDISABLE and expects a valid
 native session. This is the new documented input policy, not dropping overflow.
-Persistent flush failure can leave the native PENDIN transition unsettled. It must
 report restoration/flush failure and release no value, not assert successful physical
 restoration. The fixture repairs its own terminal only after recording the outcome.
-Background fixtures never write terminal settings from the background child; the
 candidate must refuse without mode writes or source work.
-Installed source overlays exist only in a temporary build tree and must hash-match
 both candidate modules. Test helpers import those installed modules, not the checkout.

The inquiry46+7 result is not this gate. Candidate contract failure stops under the
skill. Proven fixture corrections retain failed sources/logs and require a complete
rerun with unchanged acceptance meaning. Timeout-killing a child is always failure.

## Observed result

First complete run PASS,96.644seconds, Python3.11.10/Telethon1.45.0. All five runner
components returned0 and exact declared counts matched:23 retained groups;25 retained
PTY scenarios;17 source/file histories;8 stop transitions;14 publication crossings;
50 terminal cases;20 profile/control checks;46 framing cases;7 handoffs. Isolated
offline installation, console/module entry, headless refusal and installed native-SRP
interruption passed; installed module hashes equal the candidate hashes.

No candidate or harness correction was needed after execution began. result.json
and attempt-1.txt retain the complete run, with all candidate/harness/product source
hashes unchanged. No product source was promoted. Deliberately injected persistent
cleanup faults correctly report no-value failure; fixture repair is not successful
product restoration. Native/protocol fault observations are distinguished above.

The positive native profile is explicit in the candidate: canonical foreground8-bit
entry, ISIG with VINTR3, CR→LF mapping, permitted local flags only, no byte stripping/
case mapping/parity markers/unsupported CR-LF processing, usable distinct controls and
VDISABLE. Unknown local flags are refused even if the Python termios build has no
named constant for them. This is tested scope, not a universal POSIX/terminal claim.

No real Telegram delivery/real-account2FA, native Python3.7 execution, release, version
change or downstream environment update occurred. The full1,010-check product baseline
and demos belong to verification after promotion; they were not redundantly rerun here.
