---
model: gpt-6-astra
effort: max
---
# Revision 4 implementation verification — #10

2026-10-12. **PASS: 24 supported offline suites, 631 actual passing test groups,
3 explicit live skips.** Product commit `d32abcd`, current dev `68f6bbd`.
Python 3.11.10, Telethon 1.45.0, SQLite 3.45.3, macOS/POSIX; Node 20.17.0
was available and the exact JavaScript identifier check ran.

This is implementation verification under the folded revision 4 plan, after the
complete combined prebuild passed at `95acfc3`. It does not replace the renewed
merge check or fresh PR critique. The first PR critique remains rejected and PR27
remains draft until those gates pass.

## Integrated worker checks

- `test_37_worker`: **33/33 groups**, including all original 25. Six SDK-decoded
  errors (unknown 401/406, generic 403, unregistered, revoked and banned) run
  through each of the four actual worker operations. Each verifies category,
  reason/flags, zero group/login requests and allowance, and completed native
  cleanup. Ordinary library reasons remain available. Additional controls cover
  hostile metadata, delivery-failure source errors and the shared fatal encoder.
- `test_38_worker_process`: **25/25 groups**, retaining all original 14, with
  **67 controlled worker subprocesses**. It also runs three direct module checks
  (empty inventory/EOF, help and invalid CLI arguments), plus Node JSON decoding.
  Coverage includes quiet selectors, held native cleanup, repeated owner
  cancellation, stops before task creation/publication, retained finalization,
  broken/undrained stdout, every cleanup fault from the prebuild, all four verbs
  and all six SDK errors, delivery diagnostics and four fatal encoder controls.
- The process fixture has no polling task. The parent uses SIGUSR1 to release a
  held Event only after observing retained cleanup; test-only SIGUSR2 cancels
  the actual owning job task. Named task/finalization boundary instrumentation
  delegates to the real driver and SDK. Worker SIGINT/SIGTERM and actual loop
  settlement/logging restoration are observed, not supplied by a stand-in.
- Source activity and lifecycle observations remain in separate traces. Failed
  native cleanup is recorded as failed, not as a successful disconnect. The
  process must settle remaining tasks, keep the known outcome and refuse a
  successor. Authentication source failures incur no read/join charge.
- Fatal authentication cases inject SDK-translated errors into the actual shared
  fatal encoder; they do not claim that startup performs authentication.

The two new permanent regressions were also run against an **isolated export of
rejected runtime `6ee146c`**, preserving current tests. Its authentication projector
failed the SDK regression and its quiet stop handler exceeded the five-second
parent watchdog. Both were expected sensitivity failures, with owned children
cleaned up by the test fixture. No current product file was replaced.
See [sensitivity log](verification_r4/regression-sensitivity.txt).

## Full supported suite

Commands: project venv Python `-m tgdata.smoke_tests.<suite>`, for 12–19,
22–30 and 32–38. Suites12/13 receive an intentionally missing config, preserving
all three live skips. Test12 uses only its owned loopback proxy controls; execution
permission was granted for that local socket test. No live Telegram was contacted.
The legacy summaries count skipped checks as passing; the table subtracts them.

| Suite | Actual passes | Live skips |
|---|---:|---:|
| `test_12_proxy` | 5 | 2 |
| `test_13_device_identity` | 5 | 1 |
| `test_14_flood_threshold` | 11 | 0 |
| `test_15_login_checks` | 11 | 0 |
| `test_16_health_events` | 21 | 0 |
| `test_17_session_store` | 12 | 0 |
| `test_18_read_budget` | 28 | 0 |
| `test_19_message_batches` | 33 | 0 |
| `test_22_daily_continuation` | 25 | 0 |
| `test_23_fixed_windows` | 22 | 0 |
| `test_24_backfill_state` | 23 | 0 |
| `test_25_backfill_delivery` | 41 | 0 |
| `test_26_backfill_completion` | 16 | 0 |
| `test_27_backfill_pacing` | 32 | 0 |
| `test_28_backfill_controls` | 32 | 0 |
| `test_29_backfill_public` | 23 | 0 |
| `test_30_backfill_integration` | 15 | 0 |
| `test_32_account_operation` | 28 | 0 |
| `test_33_owned_health` | 62 | 0 |
| `test_34_group_access` | 49 | 0 |
| `test_35_join_budget` | 35 | 0 |
| `test_36_group_join` | 44 | 0 |
| `test_37_worker` | 33 | 0 |
| `test_38_worker_process` | 25 | 0 |
| **Total** | **631** | **3** |

[Counted machine results](verification_r4/counted-results.json) and individual logs
are retained alongside the [runner](verification_r4/regressions.py). The original
first-cycle 612-pass record is untouched in `verification.md` / `verification/`.

## Package and examples

[Package log](verification_r4/package.txt),
[reproduction script](verification_r4/package-verify.py):

- Compiled all 76 product/test/example/setup Python files and parsed Python 3.7
  grammar under Python 3.11.10. This is not execution on Python 3.7.
- Copied a clean source export with no `.git` or `devdocs`, built a wheel without
  downloads/dependencies, installed to a separate target and verified the import
  came from that target. Existing local wheel tooling was used; no dependency or
  development environment was changed.
- Installed `python -m tgdata.worker` and `tgdata-worker` each emitted ready for
  an empty inventory, consumed EOF and exited 0 with empty stderr.
- Worker and daily-continuation offline examples passed from the installed copy.
- New backfill example (`--new`) completed with three source reads. Restarting
  the same retained state completed with zero source reads, preserving receipts.

Export/install retained at `/private/tmp/tgdata10_r4_package_4awdyfgb`.
Targeted worker checks passed before the full suite; no failing current-code check
or implementation correction was needed. Earlier prebuild harness history remains
in `prebuild-result.md`; it has not been erased or counted as a product pass.

## Integration and limits

[Integration audit](verification_r4/integration-audit.json) records exact product
hashes and verified model metadata (`gpt-6-astra`, `max`, turn timestamp
2026-10-12T11:18:36.654Z). `serve` and `describe_error` match the passing frozen
candidates structurally; the frozen 20-name authentication set also matches.
Nine other fingerprinted runtime files remain byte-identical to `6ee146c`:
worker executor, connection/account-operation foundation, owned health, batch
engine, both budgets, group operations and TgData. No new shared-source behavior.

The revision changes six files; the whole branch still has the same 13 product
files against unchanged dev. Product/tests do not import work-folder code or
reconstruct source functions. README and caller example were inspected and remain
consistent without edits. `git diff --check` passed. Existing untracked files,
duncan and other worktrees were not edited or staged.

This proves the specified offline process/SDK behavior on this runtime. Live
Telegram, Windows/native Python 3.7, deployment and cross-process session sharing
remain unqualified. Caller-owned exclusive sessions and provisioned budgets remain
required. No merge, live login/read/join or allowance reset occurred.
