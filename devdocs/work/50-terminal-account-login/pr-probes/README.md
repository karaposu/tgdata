# Fresh PR51 probes

All scripts import the exact published product tree at
/private/tmp/tgdata-50-terminal-login-pr (69c2407), not the archive candidate.
Run using the repository's Python3.11.10/Telethon1.45.0 interpreter. Network
connect/connect_ex are forbidden; temporary credentials are synthetic.

- probe_matrix.py:17 fresh cases passed. Six source histories cover expiration,
  lost phone reply, explicit code retry after an authorization-only check, second
  uncertain reply, wrong/correct real-SRP password and native DC migration plus
  ordinary-reader reopen. Three late dangling sidecars refuse with old bytes intact.
  Four link/replace faults before/after their actual effects retain uncertainty
  and recovery material. Changed-target retry refuses; failed native constructor
  retires its real connection; available message-box state/takeout/optional hash
  survive; repeatedly failed source retirement prevents publication.
- signal_inside_action.py: real process SIGINT at actual flow action boundaries.
  Both phone validation and password proof processing hung beyond5 seconds.
  signal_runner.py repeats them with bounded child execution and owned temporary
  directories. Its diagnostic variants observe re-entry into run_until_complete
  with a task already done with KeyboardInterrupt. The uninstrumented cases also
  hang; instrumentation does not create the defect.
- pty_native_srp.py: actual getpass and PTY input, actual native SRP compute_check,
  timer delivers SIGINT while that computation remains active. The driver hangs;
  another SIGINT does not end it. Parent kills only its owned synthetic child
  after7 seconds, with no command result. Secret echo is absent. This confirms
  the failure without replacing native password computation or terminal input.

The first matrix run failed its new available-state fixture after15 passes:
Telethon's real disconnect overwrote a directly edited session state with the
message box state. Corrected the fixture to load the actual message box before
native export, preserving the same expected values. Entire17-case matrix then
passed. Both attempt logs and first result are retained. No product edit or
acceptance weakening occurred. Repeated retirement failures are explicitly cleaned
up by the probe after observing the command's refusal; they do not claim the command
successfully retired a deliberately failing source.

Published/local diffs match after stripping only GitHub's different hunk-heading
context (`setup(` versus `def read_version():`). Source hashes in matrix-result.json
match the product/prebuild hashes. The preceding exact-tree verification is kept
separately in ../pr-verification/. These probes do not qualify live Telegram,
physical power loss, hostile concurrent writers or native Python3.7 execution.
