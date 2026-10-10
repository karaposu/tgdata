---
model: gpt-6-astra
effort: max
---
# Stage 3 implementation verification

Recorded UTC: 2026-10-10T15:02:38.430776+00:00.
Product commit: **a2afc05**, branch `feat/7-group-lookup-access`, based on dev30ba706.
Plan: revision2 `d15b5d5`; selected critic M1 `48a662b`.

## Outcome

**494 actual offline test groups passed; 3 live checks skipped.** All20 selected suites
exited0. The skipped checks are test12's2 live proxy/Telegram checks and test13's1 live
identity check. Their scripts count skips in their printed denominator; this record
subtracts them. No Telegram account, network login or joining was exercised.

New public methods lookup_group/check_group_access, exported qualified result/error
values, one stateless domain module, facade wiring, SDK minimum and product docs are
implemented. Existing account-operation, factory, health, budget and session runtime
files are unchanged. No persistent schema, join behavior or alias registry was added.

## Measured regression matrix

| Suite | Actual passed | Skipped |
|---|---:|---:|
| test_12_proxy | 5 | 2 |
| test_13_device_identity | 5 | 1 |
| test_14_flood_threshold | 11 | 0 |
| test_15_login_checks | 11 | 0 |
| test_16_health_events | 21 | 0 |
| test_17_session_store | 12 | 0 |
| test_18_read_budget | 28 | 0 |
| test_19_message_batches | 33 | 0 |
| test_22_daily_continuation | 25 | 0 |
| test_23_fixed_windows | 22 | 0 |
| test_24_backfill_state | 23 | 0 |
| test_25_backfill_delivery | 41 | 0 |
| test_26_backfill_completion | 16 | 0 |
| test_27_backfill_pacing | 32 | 0 |
| test_28_backfill_controls | 32 | 0 |
| test_29_backfill_public | 23 | 0 |
| test_30_backfill_integration | 15 | 0 |
| test_32_account_operation | 28 | 0 |
| test_33_owned_health | 62 | 0 |
| test_34_group_access | 49 | 0 |

Machine-readable counts/exit codes and original log SHA256 values are in
verification/results.json. The complete final new-suite output is verification/suite34.txt.
Original baseline logs remain in /private/tmp/tgdata7-stage3-verification; the durable
matrix above distinguishes observed counts from those scripts' skip-inclusive totals.

## Reproduction and boundaries

From this worktree, using /Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python:

```
python -m tgdata.smoke_tests.test_34_group_access
python -m tgdata.smoke_tests.test_12_proxy /private/tmp/tgdata7-stage3-verification/intentionally-missing-config.ini
python -m tgdata.smoke_tests.test_13_device_identity /private/tmp/tgdata7-stage3-verification/intentionally-missing-config.ini
python -m tgdata.smoke_tests.<each other suite in the matrix>
```

The config path was verified absent; test12 uses loopback for its two local proxy checks.
Other selected suites are their supported offline modes. Old live suites, unmerged
#17/test31 and absent20/21 were not run. Normal module execution was used, including
multiprocessing in test18; no runpy wrapper. Four independent regression processes ran
at a time in isolated test temporary directories. Every exit code and summary was read.

Python3.11.10, Telethon1.45.0; tgdata imported from this exact worktree, not the original
checkout. **65 Python files** under tgdata/examples compiled with py_compile and parsed
with ast.parse(feature_version=(3,7)). This is grammar compatibility, not execution on
Python3.7. Whitespace checks passed.

## Demo verification

Three subprocess executions exited0. Durable outputs are in verification/*.txt.

- Daily continuation --demo: lost acknowledgment replayed the same batch without another
  source read;4 stored messages, acknowledged through104.
- Backfill --demo --directory <temporary directory> --new: completed;3 source reads,
  0 replay source reads,3 receipts,5 unique messages; daily105/history104 kept separate.
- Same backfill directory without --new: completed again with **0 source reads**,0 replay
  reads, same receipts/messages/cursors.

## New suite evidence

49 named test groups exercise public methods over the actual SDK/factory/ownership/
health/budget composition. Group success replies go through real TL bytes and actual
MTProtoSender RequestState/result handling; RPC errors are constructed by the SDK.
Auth fixtures and network transport are synthetic; socket connect/connect_ex, login-code,
start, join/import and dialog requests are forbidden. Malformed source/native faults
are labeled injections. No test supplies a GroupAccess result or semantic confirmation.

Coverage includes all12 plan families: grammar/no-I/O refusal; expected versus cached
identity; known group/reference/invite shapes; exact numeric/hash/collision rules;
no-peer and known source-cache failures; qualified immutable/JSON values; one bounded
history reply and invalid replies; source RPC versus local errors; real budget cost,
refund, refusal and re-verification; health recovery; actual overlaps; cancellation,
callbacks and delayed/failed cleanup; unchanged persistent selection and legacy health.
The M1 boundary/collision tests use actual session caches and SDK peer encoding.

## Corrections during implementation

No architectural failure or structural plan deviation arose. Final regression verification
needed no product correction. While building the new suite, the following were recorded:

1. The first scaffold-only source fixture passed before domain implementation.
2. The first23-group run:19passed/4failed. One product parser issue accepted an empty
   /joinchat/ URL as a username after removing its trailing slash. A small local correction
   reserves the empty joinchat route; the original no-I/O refusal expectation remains.
3. The other initial failures were fixture/test assumptions: a missing required argument
   fails at call construction, so use the synchronous assertion; inject a cache failure
   only at its intended exact group lookup instead of SDK connect's self lookup; and
   separate the valid basic-ID boundary route from the SDK's pre-connect self sentinel
   collision. The latter remains its own preserved-error regression, not a hidden pass.
4. The next38-group run:34passed/4failed. Test construction needed explicit peer_id=None
   for patched MessageEmpty and action= for MessageService. Health snapshot's account
   verdict is separate from waits/unclassified fields; assertions now check those actual
   baseline fields as well as unchanged original error identity.
5. The next49-group run:48passed/1failed; last_unclassified is an error-name string, not
   a nested dictionary. Corrected that test access, keeping exact error equality.
6. Final49-group run:49passed/0failed. No expectation was weakened to accept a production
   defect. Baseline suites then passed unchanged; callbacks/cleanup intentionally emit
   their expected fault diagnostics in the new-suite log.

The existing hashless CommunityForbidden/SQLite IntegrityError remains explicitly
preserved and documented. A synthetic Chat(10**12) cache row additionally exposes the
SDK's self-row0 lookup collision before proof; that original AttributeError is preserved,
without group requests or invented owned health. Neither issue was expanded into a cache
repair. Live Telegram permission behavior remains unqualified by these offline tests.

## Review handoff

Product a2afc05 is ready for later fidelity merge-check → PR → fresh in-session PR critic.
Those gates are not claimed complete. Partial-stage PR should use Refs #7; parent #7
remains open for join allowance/joining. No PR or merge was performed by this task-impl.
§9 model/effort provenance is retained session evidence; this run does not claim a fresh
selector check. Work-folder evidence stays archive-only under the later merge recipe.
