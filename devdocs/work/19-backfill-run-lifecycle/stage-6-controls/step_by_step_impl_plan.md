---
model: gpt-6-astra
effort: max
revision: 1
---
# Stage 6 — controls, late settlement and retirement

Baseline `1896820`; description `8c0060d`. Same-session warmed context and the
completed lifecycle traverse are retained. Telethon 1.45.0 only. No rejected PR
critic or PARKED marker exists in this stage folder.

### What is the task

Implement explicit operator decisions without losing already admitted work or
delivered data, then validate Stages 5–6 with real Gate C. The application owns
source-worker lifetime, scheduling and durable receipt generation; tgdata owns
attributable state transitions, pacing and safe recognition after uncertain replies.

### Huge Hard Blockers

#### Planning Blockers

None identified. The strict aggregate already models every control/abandonment
field. Existing settlement revalidates its own attempt and preserves newer intent.
The test-only composition of two real budgets is an executable premise, not a
human decision. Its early falsifier belongs in the critic experiment if required.

#### Execution Blockers

None currently open. Step 6 requires the previously approved session, read-only
group view and remaining allowance to requalify. If any disappears, stop at that
live case with its exact condition recorded; do not claim Gate C or enter Stage 7.
The user already approved the account/groups, read-only mode and staged live gates.

### How this implementation moves toward desired state

Add one bounded exact-context command transition to the current engine and reuse
the current codec, CAS confirmation, attempt settlement and receipt acceptance.
Commands change permission/terminal facts, never message acceptance. Retain the
first committed terminal outcome and expose enough command/abandonment evidence
for a caller to understand a late reply. Prove races locally and at real source,
storage, process and receiver boundaries before exposing the public API.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Internal command result and status evidence | Immutable values; unchanged v1 persisted schema |
| 2 | Exact pause/resume/cancel/abandon transition | Recognized commands and preserved owed work |
| 3 | Settlement and successor integration | Late results/receipts cannot replace intent or another run |
| 4 | Offline transition and durability tests | Actual SQLite, SDK boundaries and fault orderings |
| 5 | Document and verify the scoped product | Supported suite passes; separate product commit |
| 6 | Execute mandatory live Gate C | Timing, allowance, worker recovery and race evidence |
| 7 | Publish evidence and stage status | Work-only commit/push; issue #19 updated; Stage 7 pending |

## Decisions shared by the steps

### Command identity and outcomes

Internal API: `control(run, *, command_id, expected_control_revision, action)`.
Every input is required. Validate full RunRef/collection, token ID, exact bounded
non-boolean revision and action in pause/resume/cancel/abandon before storage.
Add frozen `BackfillControlResult(command_id, action, applied, outcome, status)`.
Outcomes are `accepted` and `terminal`:

- New accepted decisions have applied=True, including matching already-paused or
  already-active decisions. Increment control revision once and retain recognition.
- Exact retained command/action/original expected revision returns accepted/False
  with current addressed status, even after ordinary progress or a newer recovery.
  Same retained ID with changed input conflicts. Latest recovery ID cannot be reused
  as a control, symmetric with recover's existing collision refusal.
- An unrecognized stale expected revision conflicts. Never refresh it automatically.
- A fresh matching command on terminal work reports terminal/False with no write,
  command recognition or revision consumption. Exception: a current cancelled run
  with no abandonment may accept explicit abandonment. Retained previous terminal
  runs are read-only, including fresh abandonment requests.

Accepted result validation requires matching retained ID/action. Terminal results
require an existing terminal outcome and applied=False. This does not promise an
unbounded command history. Forgotten commands can refuse; a caller cannot relabel
an old request as fresh by replacing its expected revision automatically.

### One bounded mutation

For up to four ordinary CAS conflicts, load exact run, check recognition and original
expected control revision, decide terminal handling, validate quiescence/capacity,
build one candidate and use `_write`/exact readback confirmation. A storage error
is not CAS false; it never triggers blind reapplication. Compatible data changes
may reload without invalidating the command, but changed control revision refuses.

Pause/resume update only intent. Cancel sets intent/outcome cancelled and preserves
attempt, pending, accepted cursor, last receipt, exhaustion, pacing and failure.
Abandon requires no saved attempt and no local `_preparing` activity; record
pending hash/next cursor or null hash/current cursor, with `_now()` solely for its
observation timestamp. Clear pending without advancing accepted position. Set
abandoned terminal/intent only when nonterminal; cancelled remains cancelled.
Never read media, delete blobs, call source, classify health, sleep or alter quota.
Pause/resume/cancel/recognition/terminal reporting do not sample either clock.

Command and intent commit atomically: last_control stores ID/action/original expected,
accepted control revision and the candidate's global state revision. Before a write
reserve global revision capacity for this command plus still owed work: 3 with an
attempt (command + publication + ack), 2 with pending (command + ack), otherwise 1.
Abandon retires the obligation so needs 1. Overflow refuses without losing settlement
capacity. Do not change wire v1 fields/invariants to make an invalid candidate pass.

### Succession and concurrent settlement

Keep `_settle`'s same attempt/run/cursor/request/window validation and full reload.
It already preserves newer controls and uses shared completion closure; add no second
transition path or refetch. A cancel followed by final ack/end stays cancelled. A
completed run followed by cancel stays completed. Accepted commit order is authority.

`start` retains its identical-request recognition path before new-run checks. For a
genuinely new successor require exact current predecessor, terminal, no pending/no
attempt, and no local `_preparing` activity before clock/CAS. This conservatively
refuses while local replay/publication remains active. Other engines/processes remain
subject to the durable facts and caller's one-source-reader/quiescence contract.
Latest accepted old receipts may recognize a retained predecessor; retired pending
receipts refuse. Full run identity protects an equal-hash successor. Pruned runs refuse.

## Step 1 — Internal values and projection

### Proposed changes

In `tgdata/backfill.py`, add the result above and optional status fields
`last_control_action`, `last_control_expected_revision`, `last_control_state_revision`,
`abandoned_batch_id`, `abandoned_next_after_id`, `abandoned_at`. Serialize revisions/
cursors as decimal strings and dates as canonical UTC. Project existing record facts
in `_BackfillState.status`; leave codec/wire keys unchanged. No package exports or
TgData facade yet. Keep source error suppression and `.read_error` unchanged.

### Output

Content-free attributable command and retirement results.

### Safe in nature

False — additive internal result shape; default new status fields preserve construction.

### Peripheral concepts

Run identity, portable integer/date encoding, stored status versus batch schema.

### Hardness Lvl

2/5.

## Step 2 — Atomic controls and abandonment

### Proposed changes

Implement the shared decision algorithm in `tgdata/backfill_engine.py`. Reuse `_known`,
`_revision`, `_write` and canonical codec; retain four-attempt conflict bound. Use
latest-command recognition before expected-revision/terminal/clock/capacity checks.
Reject retained recovery ID collisions. Guard abandonment after awaited load as well
as immediately before mutation. Recognized identical abandonment remains read-only.
Terminal reports have no new control identity and cannot revive or relabel a run.
No clock on operator permission/cancellation and no implicit recovery on abandon.

### Output

One exact-context method implementing all four actions and lost-reply recognition.

### Safe in nature

False — permission and terminal decisions race with existing delivery settlement.

### Peripheral concepts

CAS ambiguity, bounded command history, first terminal outcome, revision headroom.

### Hardness Lvl

5/5.

## Step 3 — Preserve settlement and succession boundaries

### Proposed changes

Audit `_settle`, `acknowledge`, `recover` and `start` against the decisions above.
Reuse their current data-preserving transitions rather than replacing them. Add the
new-successor local busy guard after known-start recognition/terminal checks and before
clock/CAS. Update comments that say controls are absent. Confirm new controls can
commit during admission/publication awaits and actual bounded source activity;
no engine lock may span the source call. Only abandon/succession require quiescence.

### Output

Existing source and receipt paths cooperate with actual operator commands.

### Safe in nature

False — successor eligibility becomes conservatively stricter during local activity.

### Peripheral concepts

One-reader ownership, exhaustion versus acceptance, retired receipts, pending media.

### Hardness Lvl

4/5.

## Step 4 — Offline behavior, races and real durability

### Proposed changes

Add `tgdata/smoke_tests/test_28_backfill_controls.py` using actual SQLite and existing
real Telethon 1.45.0 stand-in transport. Block sockets. Group cases by invariants:

- Input/result validation, exact portable status, no facade; pause/resume accepted
  no-change decisions; immutable policy, wait, failure and accepted progress.
- Exact retries with forbidden clock/reader; changed action/expected input, command
  collision with recovery, stale resume/prepare, previous recognition and pruning.
- Two opposing controls with one expected revision; ordered delayed replies;
  compatible ordinary data CAS changes versus new control revision conflicts.
- Actual source held before/after admission/publication: pause/cancel preserve its
  result; no second attempt. Failed/budget-limited prefixes remain deliverable.
- Both final-ack/cancel orders and empty-end/cancel orders preserve first terminal.
- Abandon refuses unknown/busy workers; no-data versus pending retirement; cursor
  unchanged, cancelled preserved, blobs untouched, old receipts refused. Timestamp
  failure leaves obligation intact. Allowed successor/equal-hash isolation.
- Near-MAX revision reserve for pending and in-flight work; acknowledgement/publication
  still fit after accepted controls. Exhausted capacity refuses atomically.
- Real post-commit SQLite close errors, before/after commit process exits, cancellation,
  CAS false, malformed readback and lost command reply. Recognition never extends waits.

Update only tests 24/25's intentional staged assertions that control is absent.
Keep public-facade absence assertions. Reuse invariant helpers, not production logic
as an oracle. Record initial failures and only fix small nonarchitectural mistakes.

### Output

Reproducible offline evidence for transitions, authority and actual durable points.

### Safe in nature

True — isolated test databases/SDK transport; no live credentials or production writes.

### Peripheral concepts

Async barriers, fault injection, canonical state, SQLite WAL/FULL, process exit.

### Hardness Lvl

5/5.

## Step 5 — Product documentation, verification and commit

### Proposed changes

Add the test to the smoke README and update scoped lifecycle status/contract notes,
distinguishing implemented internal controls from pending facade and live validation.
Compile and check Python 3.7 grammar (runtime remains 3.11.10), run test28 then the
supported offline suite 27 through 11 using prior explicit helper invocation for 11,
guard instrument checks and daily demo. Report legacy live skips honestly. Review
the diff for scope, secrets and unchanged state schema. Commit product code/tests/
smoke documentation separately from work-folder evidence, preserving duncan/#7.

### Output

Verified product checkpoint to identify exactly what Gate C executes.

### Safe in nature

True — verification/feature-branch commit only; no protected merge or deployment.

### Peripheral concepts

Supported SDK/runtime, staged interface availability, auditable artifact separation.

### Hardness Lvl

3/5.

## Step 6 — Mandatory real Gate C

### Proposed changes

Add reproducible work-folder drivers and instrument checks. Reuse the audited
read-only actual-send guard and durable receiver helper; do not weaken allowlists.
Read only the selected session/config and approved existing groups. Requalify small
group with independent descending history to explicit EOF and independently verify
the chosen photo's digest if used. Preserve any source drift as evidence. Use new
private SQLite/media/receiver state. Never alter Gate A/B originals or unresolved rows.

Test-only allowance composition: two actual ReadBudget ledgers. Existing 5,000/day
account policy remains authoritative. A separate cap (initially 3, then 6) may only
restrict it. `.status` returns the actual status with the smaller remaining allowance;
`._reserve` claims primary then test ledger and returns both real reservation objects;
`._settle` settles both. If the second reservation/settlement fails, retain any first
charge conservatively, never reset/refund unknown source outcomes. Existing actual-send
adapter receives the composition; reconfiguration applies only to the test ledger and
preserves its start/charges. Validate both stricter-ledger orders and partial failure
locally, then actual exhaustion/prefix/re-admission live. Never label cap increase as
natural rolling expiry. Test natural expiry separately with deterministic clocks.

Bound Stage 6 live traffic, including a prebuild experiment, to at most 1,000 requested
history slots and 4 MiB downloaded media per selected case, with a 180-second case
deadline, sequential source workers and guard limits. Stop on unexpected view/account,
FloodWait, logout, malformed data or exhausted authoritative allowance. Source pacing
uses a small explicit 5–8 second run policy; this validates the same rule as offline
240-second tests. Independent cases/qualification have at least five seconds between
source calls. No extra case sleep may hide whether an early lifecycle call was refused.

Record actual SDK sends/replies separately from bounded lifecycle entry/return,
persisted end/deadline, receiver commits and command/control revisions. UTC is portable;
diagnostic monotonic comparisons across same-host workers require a parent/child bracket
probe first. Never save monotonic ticks into production run state or change host time.

Required cases, each with assertions and explicit live/injected-local labels:

1. Measured waits after real result/failure across process reopen, early ack, late ack
   and repeated early calls. Reopened work neither resets nor bypasses its deadline.
2. Real restrictive allowance exhaustion with usable prefix and no disallowed send;
   replay/receiver/ack while paused and exhausted; explicit test-cap increase preserving
   charges; resume preserves wait; next actual source admission rechecks both ledgers.
3. Owned worker performs real source activity and exits before publication. Parent
   confirms process exit, recovers exact attempt, loses the committed recovery reply,
   retries without resetting the conservative wait, then measures a later real read.
   A still-running local prepare refuses recovery/abandonment.
4. Force pause-before-result, cancel-before-final-ack, final-ack-before-cancel, stale
   resume, opposing controls and delayed responses around actual source/store/receiver
   boundaries. Already admitted work settles with preserved intent; local commands
   produce no additional Telegram traffic. Label barriers as injected ordering.
5. Explicitly abandon owed live-origin data, create a successor, verify equal payload
   hashes carry different full receipts, reject the retired receipt, and recognize
   a retained accepted old receipt without changing current work. No blob cleanup.

Only all required observations yield PASS. Otherwise record FAIL/BLOCKED/INCONCLUSIVE,
stop before Stage 7, and reopen Gate B if delivery/completion assumptions changed.

### Output

`validation/gate-c.md`, sanitized evidence and exact runnable drivers. Private raw data,
account IDs/credentials/session strings and receiver message content stay uncommitted.

### Safe in nature

False — consumes real account allowance and exercises crash/recovery of owned workers.

### Peripheral concepts

Telegram history/media, actual-send quotas, worker death, durable receiver, clock trust.

### Hardness Lvl

5/5.

## Step 7 — Record and publish scoped completion

### Proposed changes

Record implementation, every small correction, full-suite results and Gate C evidence.
Update assumptions, matrix, contract/staged-plan/README to the observed result. Commit
work evidence separately, push this feature branch, post a concise issue comment and
update #19's status/checklist only after commits. Preserve its raw request and body
size limit. Keep parent-feature implementation/PR/merge and Stages 7–8/Gate D pending.
Do not touch duncan, paused #7, other worktrees or protected branches.

### Output

Reviewable Stage 6 checkpoint with an honest next stage or concrete gate blocker.

### Safe in nature

True — scoped evidence and issue status; no library release, PR or merge.

### Peripheral concepts

Pipeline discipline, bounded evidence, source privacy, branch archive.

### Hardness Lvl

2/5.
