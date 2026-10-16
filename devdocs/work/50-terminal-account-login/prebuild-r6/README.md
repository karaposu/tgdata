# Revision6 combined prebuild — FAIL; product unchanged

The requested new plan and fresh critic ran; the robust input-transformation refusal
was folded before this experiment. The complete prebuild FAILED. Do not promote the
candidate. See ../critic.md and ../DEPRECATED_step_by_step_impl_plan.md.

Candidate modules substitute only the CLI and private terminal reader. LoginFlow,
Telethon1.45/native SRP, StoredSession, native SQLite, LoginDestination and ordinary
configured reader are real. Controlled wire replies are the only source transport;
network connect/connect_ex are forbidden. Actual PTYs/process signals qualify input.
Input-mocked source/file cases are not claimed as terminal evidence.

Run1:23 retained groups passed, with25 PTYs/17 histories/8 stop transitions/14 file
crossings. The new matrix passed23 cases before the driver wrote synthetic input
after an intentionally immediate wait failure had restored the terminal. The
retained diagnostic shows the error report before the synthetic input echo. The
only harness correction skips sending input to the two immediate wait-exit cases;
all assertions and both candidate modules remained byte-identical.

Run2:the complete retained suite passed again;36 new terminal cases passed. Case37,
kernel_overflow, failed by timeout. The harness wrote5,000 bytes plus newline, but
canonical input never became readable before its12-second deadline. An independent
native probe accepted all5,001 written bytes while delivering no line; short128/129-
byte lines worked. PC_MAX_CANON was1,024. No timeout kill counts as successful stop.
The remaining13 new cases were not executed after this disqualifying failure.

result-attempt-1.json and result-attempt-2.json record source manifests and observed
counts; attempt logs and terminal_matrix_attempt1.py preserve failed evidence.
result.json records the final FAIL, not a selectively passing subset. Candidate
hashes match between both runs and product source matches throughout. Native input
policy is unqualified; do not copy the candidate merely because the prior two
review regressions now pass. The terminal matrix is diagnostic evidence, not a
production test suite ready to promote (later unexecuted harness cases are unqualified).

canonical_overflow_probe.py is a diagnosis of the failed premise, not a candidate
patch or a third full run. It resets its synthetic terminals and uses no account.
Current environment: Python3.11.10/Telethon1.45.0; no native3.7/live Telegram claim.
