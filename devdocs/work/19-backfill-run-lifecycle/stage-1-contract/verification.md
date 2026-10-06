---
model: gpt-6-astra
effort: max
status: stage-1-verified
---
# Stage 1 verification

Stage 1 delivered specifications only. Product baseline on this branch:
`45bab7172621f576fa5e4b3265f87ec20da04fd5`. The #18 prerequisite component probes ran
separately at product baseline `e9b5154`. No new lifecycle runtime or live gate was
executed or passed. The 44 new lifecycle cases remain UNRUN.

## Document verification

Structural/reference checks passed for:
- six operation contracts, twelve invariant definitions and twelve critical assumptions;
- 44 individually specified cases with setup/order, required and forbidden outcome,
  operation/invariant coverage, evidence method, earliest stage/gate and UNRUN status;
- coverage index for every operation/invariant, resolved case references and local links;
- both selected Medium mitigations folded into steps 1/3 and implemented in the contract;
- source/future evidence separation, existing-group/read-only choice, and unchanged
  A/B/C/D gate dependency order; no synthetic-only claim of a live PASS.

Literal semantic audit checked creation new/retry/absence, prepared-context staleness,
known versus unknown outcomes, batch/cursor/terminal coupling, final ack versus cancel
in both orders, explicit abandonment after cancellation, recovery quiescence, durable
waits, scoped historical recognition and local-versus-Telegram evidence. Gate A can
use the current raw reader with Stage 2 saved state; it needs no Stage 3 or Stage 7 code.

These are specification/coverage checks and adversarial readings, not an executed
model of the new state machine. No toy lifecycle model was used as verification.
No runtime files, tests, schema or SDK dependency changed.

## Full supported offline baseline suite

Python 3.11.10, Telethon 1.45.0. Package import confirmed inside
`/private/tmp/tgdata-19-backfill-run-lifecycle/tgdata/`.

| Suite | Actual offline groups passed | Explicit live skips |
|---|---:|---:|
| test19 message batches | 33 | 0 |
| test18 read budget | 28 | 0 |
| test17 session store | 12 | 0 |
| test16 health events | 21 | 0 |
| test15 login checks | 11 | 0 |
| test14 flood threshold | 11 | 0 |
| test13 device identity | 5 | 1 |
| test12 proxy | 5 | 2 |
| test11 explicitly awaited pure helpers | 2 | 0 |
| **Total** | **128** | **3** |

All invoked modules/helpers completed successfully. Tests12/13 print 7/7 and 6/6
because their skipped live checks return success; those three are excluded from the
128 passes here. Skip counts use explicit skip markers, not the word “skipped” in
a successful test's description. No real config/account was read. Proxy networking
was its localhost refusing relay and never forwarded to Telegram; it ran with local
socket permission. Other legacy live entry points were deliberately not invoked.
No Telethon 1.33.1 run or unsupported Python-runtime receipt is claimed.

Reproduce from this #19 branch with the named SDK:

```bash
python -m tgdata.smoke_tests.test_19_message_batches
python -m tgdata.smoke_tests.test_18_read_budget
python -m tgdata.smoke_tests.test_17_session_store
python -m tgdata.smoke_tests.test_16_health_events
python -m tgdata.smoke_tests.test_15_login_checks
python -m tgdata.smoke_tests.test_14_flood_threshold
python -m tgdata.smoke_tests.test_13_device_identity /path/that/does/not/exist.ini
python -m tgdata.smoke_tests.test_12_proxy /path/that/does/not/exist.ini
```

For test11, import and explicitly await only `test_query_builder` and `test_empty_frame`
with socket connect/connect_ex forbidden. Its module main includes a live test and
was not run. Temporary logs: `/private/tmp/tgdata19_test12.log` through the invoked
suite numbers. Durable evidence is this receipt plus existing committed test sources.
No new Python files were shipped, so no changed-code compilation claim is applicable.

## Prerequisite component probes during critique

Four existing #18 tests passed with actual SQLite, real library/SDK code, synthetic
replies, temporary fixtures and both socket connect functions forbidden:
`test_store_protocol_and_no_store`,
`test_backend_failures_conflicts_and_uncertain_ack`,
`test_relative_enrollment_freezes_once`,
`test_initialization_conflicts_and_bad_durations`.

These four are separate from the 128 dev-baseline groups. They validate only the
named existing mechanisms; source code at e9b5154 is not merged into this branch.
The new lifecycle, live Telegram behavior and deployed receiver remain unverified.

## Corrections and limits

The first temporary component-probe driver omitted the shared temporary-directory
fixture (`f.TMP`), so it failed before constructing its first store. The corrected
driver used the suites' actual fixture setup and client cleanup and passed all four.
No source/test change or weakened expectation was needed. The failed initial driver
is not included in passing evidence; this is recorded in the critic too.

The read-only existing-group approach is selected. Actual account/session, group,
independent complete interval oracle, request limits and receiver acceptance point
remain UNSET. Their absence does not block this document delivery but prevents a
future gate from being treated as passed. Stage 2 requires the #18 runtime prerequisite
on an integrated/authorized base. No PR, merge or Gate A operation occurred here.
