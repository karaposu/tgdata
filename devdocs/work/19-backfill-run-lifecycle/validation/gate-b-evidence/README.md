# Gate B evidence

[Gate report](../gate-b.md) is the aggregate PASS decision. `observations.json` records:

- product revision and SHA-256 of the engine, unchanged Gate A guard and execution scripts;
- all 20 worker actions with expected/actual exit codes;
- independent source ID/date oracles and frozen case inputs;
- actual RPC/SDK page traces and conservative budget counters;
- content-free observed/candidate status, exact pending-payload fingerprints,
  receiver unique ID/date sets and selected media hash/size.

A before-commit **candidate** status is deliberately distinguished from a reopened
observed status: the candidate may say completed while the actual precommit-exit record
still holds an unresolved attempt. Inspect the paired `recovery_check`/`complete_check`
reports and gate text, not a candidate in isolation.

The summary's 1400 requested slots includes 202 from the separate unchanged-Stage-3
prebuild experiment. Actual final-product Gate B used 1198 slots across 29 history
requests. Each control failure is labeled INJECTED; real Telegram supplied all history
and media. Synthetic transport supplied only the separate offline suites.

No credentials, account identifier, session/budget database, raw message payload,
sender details or media bytes are included. A nonnull account field would be redacted;
this published evidence is an audit artifact, not runnable account configuration.
Private databases/media remain outside Git under the paths documented in the handoff.
The executable audit drivers live in stage-4-completion on this branch and assume the
explicit selected test setup; they are not installed library APIs.
