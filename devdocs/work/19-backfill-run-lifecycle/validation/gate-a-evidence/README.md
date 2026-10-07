# Gate A execution evidence — 2026-10-07

See the [gate report](../gate-a.md) for PASS scope and limitations.

- `observations.json`: seven frozen comparison manifests and their real reports,
  two independent fixture captures, selected-media hash, controlled interruptions
  and setup-attempt receipts. Per-scan INCONCLUSIVE verdicts remain intact; the
  aggregate review is separately PASS.
- `state-checks.txt`: 23 actual offline state test groups passed on the tested product.
- `instrument-checks.txt`: 10 checks passed, including real SDK startup with synthetic
  transport and missing/zero/populated state. Its injected ServerError is an offline
  retry test, not a real Telegram failure.
- `run-scripts/`: exact auxiliary sources used for qualification, enrollment,
  sequential comparisons, independent media hashing and controlled interruptions.
  Paths/case IDs are execution-specific; these are archive receipts, not package
  APIs or commands to run against a different account unchanged.

Published manifests replace the numeric account ID with `REDACTED_SELECTED_ACCOUNT`
and deliberately cannot run directly. Credentials, codes/passwords, session/budget/state
databases, message text, sender identities and media bytes are not published. Private
inputs, state, ledger and outputs remain under `/private/tmp/tgdata19-gate-a-live-20261007`
on this machine; the restored login remains in the project's configured session file.

The qualification recipe's username constant changed only when the user selected a
different source; the archived version names the final larger fixture. Six small
cases were enrolled before the smaller group's final snapshot. The pagination case
used dates from records 360 and 10 of the descending 500-record capture, batch size
120 and fresh origin. Its full original request is in the observations. Runs used
isolated SQLite state, the same unreset 5,000-read ledger and exclusive output files.

To repeat, requalify account, source visibility, allowance and the independent
existing-history oracle; instantiate the saved request in an isolated store and
follow [probe usage](../../stage-2-state/probe-usage.md). Supply actual account identity
locally and new output paths. Do not copy an old PASS onto changed conditions.
