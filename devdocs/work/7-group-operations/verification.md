---
model: gpt-6-astra
effort: max
---

# #7 — verification, 2026-10-05

Code commit: `8e245f8f1d001c30ecd561e173e8742302cc313d`.
Environment: `.venv/bin/python`, Python3.11.10, Telethon1.45.0 (TL layer229).

**Result: 151 offline test groups passed, 3 live checks skipped, 0 failures.**
The two mixed proxy/device runners count skips as passes in their printed totals;
the table below separates them. No Telegram credentials or live joins were used.

| Suite | Offline passed | Live skipped | Runner result |
|---|---:|---:|---|
| test_20_group_operations |25|0|25/25, exit0|
| test_19_message_batches |33|0|33/33, exit0|
| test_18_read_budget |28|0|28/28, exit0|
| test_17_session_store |12|0|12/12, exit0|
| test_16_health_events |21|0|21/21, exit0|
| test_15_login_checks |11|0|11/11, exit0|
| test_14_flood_threshold |11|0|11/11, exit0|
| test_13_device_identity |5|1|6/6 including skip, exit0|
| test_12_proxy |5|2|7/7 including skips, exit0|

All suites ran as `.venv/bin/python -m tgdata.smoke_tests.<module>`.
For tests12/13, supply a confirmed nonexistent config path:
`/private/tmp/tgdata7-no-live-config-20261005.ini`. This skips live relay/proxy
and Telegram identity acceptance while preserving proxy parse/factory/loopback
refusal checks. Local-only test12 used the permission needed for loopback sockets.
Raw outputs from this run are `/private/tmp/tgdata7_suite_<number>_<name>.log`;
they are temporary receipts, not a committed artifact dependency.

## Other checks

- `.venv/bin/python -m compileall -q tgdata`: pass.
- Python3.7 grammar parse on the seven changed runtime modules: pass. This is
  syntax compatibility evidence, not execution on a Python3.7 interpreter.
- Dependency declarations in setup.py and requirements.txt agree; exported new
  public types are importable and listed in __all__: pass.
- `git diff --check`: pass.
- Staging review: exactly13 code/test/public-doc files, no work artifacts or duncan.
- No repository-wide offline aggregate was found. Suites12–20 are the complete
  supported offline set; credential-dependent tests00–11 and ad-hoc live scripts
  were not run, consistent with the task's offline scope.

## What the new suite proves

Real SDK dispatch and TL result decoding are used with supplied transport replies.
The facade opens/connects/authenticates/disconnects real factory-composed clients
with only transport lifecycle hooks replaced. Real sessions and SQLite transactions
exercise persistence, concurrent process claims, expiry, uncertainty and local cache
failure. Tests inspect request count/type, independent read/join usage, actual
health events and cancellation cleanup. The 25 groups cover the21 planned behavior
areas; several larger areas have separate focused groups.

The first run's failures and every local correction are recorded in implementation.md.
The final full regression run happened after all functional changes. Only a
factory docstring and status-method docstring were clarified afterward; no test
expectation or runtime behavior was changed after the passing run.

## Evidence limits

Scripted replies do not establish live Telegram acceptance, future approval timing,
or a restriction-preventing quota. The ledger coordinates processes sharing one
SQLite file; no multi-host backend was tested or promised. Other clients/files and
private transport bypasses are outside this library allowance. SDK upgrades need
these composition tests again. PR/merge verification is a separate later stage.

## Merge-check supplement

The merge check re-read the committed runtime diff without changing it. Three
targeted probe groups in merge-check-probes.py pass: SDK history retries and
per-send read admission; account/authorization-wait recovery with group recovery
disabled; primary-versus-cleanup failure and real read-only SQLite refusal.
These supplement, rather than replace or inflate, the151-group regression receipt.
The whole-branch whitespace check exposed one trailing blank line in a committed
source-input artifact; it was corrected. See merge-check.md for the exact reviewed
revisions, wording/record repairs and remaining process qualifications.

## Fresh PR review result

The additional PR probes reproduce2 Medium soundness failures not covered by the
151-group run: temporary RPC retry exhaustion is misclassified/lost, and a public
health snapshot can use a stale account ID for a fresh event’s observation. A
forced-overlap identity probe passes and exposes1 Low coverage gap in the original
immediate-response concurrency test. See pr-critic.md and pr-critic-probes.py.
The prior green receipt is unchanged historical evidence; PR16 is rejected/draft
and must follow CONTRIBUTING §7.4 re-planning before renewed acceptance.
