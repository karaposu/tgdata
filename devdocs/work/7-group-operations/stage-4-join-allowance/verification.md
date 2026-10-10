---
model: gpt-6-astra
effort: max
---
# Stage 4 implementation verification

**Product:** `de1f758`, based on merged dev `1ce39d5`.
**Plan:** revision2 `8d5a256`; fresh critic `34508a7`, required prebuild experiment
PASS `3e40528`. Same-session implementation; no delegated reviewer or PR acceptance
is claimed. User scope: Stage4 only, review and merge before Stage5.

## Delivered behavior

`tgdata/join_budget.py` supplies explicit provisioning/existing-state reopen,
per-account policy, immutable status and one atomic private claim. Each claim
consumes a nonrefundable attempt for a rolling24-hour window. Reconfiguration
preserves usage; zero blocks. Persisted clock observations prevent backward clock
movement; reduced caps wait for enough expirations to restore a slot.

Schema is checked on every transaction. Partial namespaces, unsupported metadata,
wrong columns/PK/FK/index and orphan owners refuse. Affected account records are
validated against their prior clock before any pruning. SQLite/cleanup uncertainty
grants no permission even when usage committed. Cleanup preserves primary errors
and cancellation; local exceptions suppress incidental Telegram-error context.

Public exports, README, docs/join_budget.md and the smoke-test index describe the
standalone boundary. No TgData option, sender guard, joining API, group operation,
account-health change or ReadBudget change is part of this delivery.

## Verification results

Environment: Python3.11.10, Telethon1.45.0, SQLite3.45.3.

| Check | Result |
|---|---|
| New test35 | 35/35 test groups passed |
| All supported offline suites12–19,22–30,32–35 | **529 actual passes; 3 live checks skipped; 0 failures** |
| Exported tree, no .git, imports verified inside exported tree | test35 repeated:35/35 |
| Daily-continuation offline demo |4 stored messages, acknowledged through104; replay without source read |
| Backfill demo, new and restart |Both completed; restart0 source reads,5 unique messages,3 receipts |
| Compile + ast.parse(feature_version=(3,7)) |67 Python files under tgdata/examples passed |
| git diff --check |Passed |

Counts are test groups as reported by the suites, not individual assertions or
subTest parameter cases. Suites12/13 count skipped checks in their displayed totals;
the529 figure subtracts those3 skips. The repeated export run is not added to529.
Detailed counts are `evidence/regression-results.json`; new suite, exported suite
and demo output are saved alongside it.

Commands used the existing project venv, not an installed replacement package:

```sh
/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python -m tgdata.smoke_tests.test_35_join_budget
```

Each supported suite was run with its normal python -m module entry point, four
independent processes at a time. Suites12/13 received an explicitly absent config
path (`/private/tmp/tgdata7-stage4-verification/intentionally-missing-config.ini`).
The regression launcher lives at `/private/tmp/tgdata7-stage4-regressions.py`; full
transient suite logs are in `/private/tmp/tgdata7-stage4-verification/`. Loopback
networking for test12 was enabled; no live Telegram credential was supplied.

```sh
python examples/daily_continuation.py --demo
python examples/backfill_runs.py --demo --directory /private/tmp/tgdata7-stage4-backfill-demo --new
python examples/backfill_runs.py --demo --directory /private/tmp/tgdata7-stage4-backfill-demo
```

The export check used git archive of the preparation HEAD plus the exact six
pending product files, without .git. It asserted tgdata.__file__ belonged to that
export before running test35. Those exact product files were then committed in
de1f758. The suite has no dependence on inquiry scripts or historical git objects.

## What the new tests establish

- Six synchronized competing processes admit exactly three claims under cap3;
  another race isolates two account policies. Status alone confers no reservation.
- Actual process exits before commit leave0, after real commit/before return leave1.
  An exception injected after actual commit retains usage and returns no permit.
- Explicit creation/reopening, missing state after object construction, damaged
  schema/owners/records, invalid timestamps and policies all refuse without repair.
  Negative timestamps and future-vs-prior-clock values cannot disappear via pruning.
- Real SQLite read-budget reservation/settlement coexists with join claims.
  Exact/fractional expiry, changed caps, zero/missing policies, maximum bounds and
  backward clock observations behave as specified. Clock calls run under writer lock.
- Real connection wrappers inject failures before/after operations, including
  claim cancellation at commit. Secondary rollback/close/logger failures preserve
  primary identity and release underlying connections. Cleanup-only errors retain
  committed charges. Actual health.classify ignores local failure context.
- Native current-runtime cancellation plus an explicitly labeled Exception-derived
  fixture exercise the selected compatibility fold. This is not a native Python3.7
  run; syntax checks and fixtures are not advertised as one.

## Deviations and verification fixes

**No runtime deviation from the folded plan; no failed verification run or runtime
correction.** After the initial35/35 pass, the cancellation test was strengthened
to interrupt an actual claim at commit and the conversion case added a throwing
float subclass. The full regression/export runs cover that final version. Test
expectations were not weakened. Documentation and exports were completed before
the final full run, as required for their public-surface tests.

## Evidence limits and next gate

These are local accounting tests, not live Telegram join or safe-rate evidence.
Process exits do not prove physical power-loss durability. Accurate forward clock,
cooperative same-host file custody and SQLite/filesystem behavior remain stated
operating assumptions. Valid-looking arbitrary edits or backup rollback are outside
the detectable-corruption contract. No account/session or production database was
used. Original untracked files, duncan and the stray guide remain untouched.

Next: merge check, PR into dev with Refs #7 (partial staged delivery), then a fresh
in-session PR critique. Stage4 is not merged, and parent #7 stays open. Stage5 begins
only after this stage's review and authorized merge.
