---
model: gpt-6-astra
effort: max
status: OFFLINE_PASS
---
# #17 whole-operation restart — implementation verification

**Product:** a63099e. **Integrated dev:**2ddb852 via ceda2bf.
**Plan:** revision5, folded1 robust mitigation after full P0 PASS at3f535d1.
**Result:**725 executed offline test groups passed,3 explicit legacy live skips,
3 offline examples passed, compilation and86 Python3.7 grammar checks passed.
Python3.11.10 / Telethon1.45.0. No native3.7 or live two-account qualification claim.

## Implementation against the plan

1. Integrated the exact tested dev commit. All76 baseline runtime Python files
   matched the isolated union before implementation. Only batch_engine conflicted;
   resolution preserves worker resolver and pool opt-in cancellation-prefix behavior.
2. Added the private owned-component capture/wait and expiring provider scope. The
   existing retained cleanup mechanism moved unchanged in behavior; physical cleanup
   is never cancelled by the waiter's repeated stop requests.
3. Source body outcome survives every secondary finalization path. Unexpected source
   interruption is local/unresolved. Passive bounded observations replace pool
   callbacks, drain in every state and execute no application consumer. Native SDK
   retirement/quarantine remains. Sync session-load interruption is local configuration.
4. Pool and configured daily/backfill provider operations use that same child-outcome
   boundary. Caller stop joins actual I/O; provider-owned cancellation becomes local
   storage error. Admission and uncertain-write authority rules remain unchanged.
   Selected Risk1 refuses all exclusive same-pool controls before ownership/mutation.
5. Existing interrupted-prefix logic is shared. Pool settlement and shared progress
   publication errors/cancellation retain known complete data without creating a
   receipt or history-end evidence. Existing exact backfill reconciliation remains.
6. Promoted the48-group real-component composition to test39/pool_storage_cases;
   adapted test31's callback cases to the explicitly planned passive API. Public
   README/docs/example describe provider/caller distinction, data versus receipt,
   bounded diagnostics and state-only use after close.
7. Full offline suite, examples, compilation, grammar, export imports, diff check
   and exact P0/runtime parity passed. Product and work evidence are separate commits.
8. **E1 pending.** User selected one-account/offline-first. Two approved logged-in
   accounts/shared readable group/existing bounded allowance are still required.

## Verification commands and results

Existing project environment:

```bash
python -m compileall -q tgdata examples
python devdocs/work/17-account-pool/probes/restart/verify.py
python devdocs/work/17-account-pool/probes/restart/verify.py test_34 test_35 test_36
```

The first command set runs all26 supported offline suites12–19 and22–39, including
worker source/process and both pool suites, plus account_pool/daily_continuation/
backfill_runs demos. Proxy/device runners receive an explicitly nonexistent config;
their3 live cases are skipped and excluded from725 executed checks. Local proxy
refusal tests run; no Telegram traffic or real account allowance is used. Older
live scripts are not part of this offline qualification.

[Combined report](evidence/restart/final-summary.json) records all29 suite/example
outcomes,728 runner-reported groups minus3 explicit skips, exact commands and parity.
[Complete initial logs](evidence/restart/final-attempt-1/) and
[three collector reruns](evidence/restart/final-attempt-2/) remain available.
All8 changed production modules match the passing P0 candidate byte for byte;
permanent tests only reorganize probe imports/names and update the planned callback
API expectations. No runtime correction after P0. Package exports/imports pass.

The pool demo selected account222 after a wait on111, delivered4 records, replayed
without source traffic, acknowledged through104 and retained charges111:2/222:4.
It drained1 health observation and0 drops. These are synthetic fixture accounts.

## Corrections and deviations

No architecture or runtime deviation from the folded plan. Two local verification
corrections are explicit:

- P0 matrix audit added two missing coverage groups. The new backfill-recovery
  fixture originally supplied only a pending first SDK page while expecting charge200.
  Added a real100-record first page before the pending second page. Assertions stayed
  unchanged. [Exact old fixture and explanation](evidence/restart/fixture-correction.md).
- Full suite collector recognized only `Passed: N/N`, mislabelling test34/35/36 despite
  exit0 and all PASS/OK output. Added their actual formats and reran just those three.
  No production or test assertion change. [Collector correction](evidence/restart/verification-correction.md).

No failing semantic expectation was weakened. No new PR critique was run during
implementation. Original rejected PR and failed r3 plan/prebuild remain evidence;
one PR rejection and one failed design prebuild, not three rejected revisions.

## Remaining gates and operational limits

Renewed merge check and a fresh in-session PR critique of a63099e against current dev
are next. PR26 remains draft and #17 open. Work/inquiry artifacts stay on the feature
branch during any later code-only merge. No merge authorized here.

Two-account E1 still needs the user-provided access/allowance. Task-impl's gate says
“Step gated by an OPEN execution blocker → stop there.” Steps1–7 are complete;
step8 is that execution gate, not an implementation failure or a request to repeat
already-authorized offline work. Stored unknown writes still require inspection/
existing exact recovery; provider I/O must terminate cooperatively. Native disconnect
failure still quarantines a client. Diagnostic data remains best-effort.

Main checkout/untracked HANDOFF/todo, duncan and unrelated work are untouched.
