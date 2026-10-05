---
model: unknown
effort: unknown
---

# Implementation and verification — issue #9

Implemented folded plan revision 2 (`c88ac47`) on
`feat/9-account-read-budget`, based on `dev` at `af593fc`.
Runtime, tests and user documentation are committed in **`07d983a`**.
This report belongs to a separate work-folder commit.

## Result

All six implementation-plan steps are complete. The public opt-in is
`TgData(..., read_budget=ReadBudget(path))`. SQLite holds policies and
admission-time charges by authenticated Telegram account ID. Atomic claims
coordinate independent instances/processes sharing that file. Warm-up and
usage persist across restarts; policy updates preserve usage and, unless
explicitly replaced, enrollment time.

The client adapter obtains fresh self identity and commits a reservation
immediately before each actual sender enqueue. Hidden retries claim again;
cached flood waits do not claim before sending. Valid replies settle to the
returned message-slot count; failures/cancellation retain the full reservation.
Request bounds, supported wrappers, paging and ID cursors are guarded without
changing no-budget behavior. Local storage/configuration failures stop reads.

Message/search/discovery operations attach processed frames to budget errors;
media-by-ID attaches completed entries. Polling delivers/deduplicates partial
output then propagates exhaustion. Local budget errors do not create Telegram
health verdicts. The README covers setup, identity, status, boundaries, clock
and SQLite assumptions, and conservative accounting.

## Plan and critic accounting

- Steps 1–3: ledger, request/iterator adapter and public/engine wiring complete.
- Step 4: `test_18_read_budget.py` contains 28 behavioral groups using real
  SQLite and Telethon request/iterator code with scripted transport replies.
- Step 5: README example and contract, plus smoke-suite documentation complete.
- Step 6: compile, supported offline regressions, compatibility and example
  checks complete; code and work-folder commits remain separate.
- Critic Risk 1 (Medium), selected robust mitigation: implemented. Tests use
  cached self ID 111 with authenticated account 222, change identity between
  page sizing and send, and preserve actual GetState logout errors. Cached
  `_self_id` remains untouched and is never quota authority.

No architectural or accounting deviation from revision 2 was necessary.
The plan file retains the task-impl-mandated name
`step_by_step_impl_plan.md`; it is the authoritative plan for later review.

## Verification on 2026-10-05

Python 3.11.10 from the project `.venv`; normal Telethon remains 1.45.0.
All Telegram replies and credentials in the budget suite are synthetic.
The suite blocks socket connect/connect_ex. SQLite contention uses four real
worker processes, admitting exactly 98 units from 40 competing seven-unit
claims under a 100-unit cap.

| Check | Result |
|---|---|
| `python -m compileall -q tgdata` | Pass |
| `git diff --cached --check` before code commit | Pass |
| `test_18_read_budget`, Telethon 1.45.0 | 28/28 pass |
| `test_18_read_budget`, Telethon 1.33.1 | 28/28 pass |
| `test_17_session_store` | 12/12 pass |
| `test_16_health_events` | 21/21 pass |
| `test_15_login_checks` | 11/11 pass |
| `test_14_flood_threshold` | 11/11 pass |
| `test_13_device_identity` | 5 offline pass, 1 live check skipped |
| `test_12_proxy` | 5 offline/loopback pass, 2 live checks skipped |
| `test_11_discover_groups` query-builder/frame helpers | 2/2 pass, sockets blocked |
| README's exact budget code block | Pass with temporary ledger/config and scripted client |

The main environment therefore passed **95 offline groups**, with **three
live checks explicitly skipped**. Compatibility reran the 28 budget groups
on 1.33.1. The older proxy/device runners count a skip as success in their
printed totals; the table separates those skips rather than claiming live
coverage. Explicit nonexistent config paths disabled the live checks. The
proxy suite was given localhost socket access; no Telegram account was used.

Telethon 1.33.1 was installed with `--no-deps --target` in
`/private/tmp/tgdata-issue9-telethon-1.33.1` and selected with `PYTHONPATH` only
for that subprocess. The project environment was not downgraded. The README
check executed the extracted code block, substituting only its filesystem
paths/client factory for temporary test fixtures: the actual ledger, adapter
and SDK handled the 100-message warm-up stop, partial frame, status and close.

Temporary logs are under `/private/tmp/tgdata_issue9_*`; durable results and
commands are recorded here because temporary logs are not branch artifacts.

## Small verification fixes

Task-impl's Verify gate allowed only small, non-architectural corrections:

1. First 1.45.0 run: 25/26 groups passed; the new MessageEmpty fixture omitted
   the `peer_id` required by that version. Added a synthetic channel peer.
   Additional resolution-delay/metadata coverage brought the suite to 28
   groups, all passing.
2. First 1.33.1 run: 27/28 groups passed. The filtered-message fixture used IDs
   1–3, which that SDK treats as end-of-history even for a reverse page.
   Supplied IDs 1001–1003 so the test isolates date filtering and budget
   exhaustion. Accounting and partial-result assertions were unchanged.
   Reran the full budget suite on both versions: 28/28 each.

Neither correction changed production behavior, architecture or the plan.

## Limits and next gate

No live Telegram response-bound conformance or safe numeric rate was verified.
Historical interactive/live smoke demos were not run. Metadata/previews,
passive updates, update recovery and file bytes remain outside the selected
message allowance. Separate ledger files/hosts and clients/private transports
constructed outside the guarded factory are not coordinated. SQLite operations
are synchronous, may wait up to five seconds on contention, and rely on a
reasonably accurate host clock; backward jumps are clamped, forward jumps are
not hidden.

The unrelated `devdocs/guides/group_discovery.md` edit was left untouched and
excluded. Its SHA-256 remained
`28daa77cd0a94e787f211f05405858327721fcdd275549e64b64f9e48389cedf`.

CONTRIBUTING's merge check/PR (step 6) and PR critic (step 7) are still pending;
do not confuse those process numbers with this plan's six implementation steps.
Exact model/effort metadata remain unavailable, so §9 compliance is not
certified and must be flagged at the merge gate. This implementation run does
not authorize merging or deployment. Issue #9 stays open pending review and
integration.
