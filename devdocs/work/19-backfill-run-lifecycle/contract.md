---
model: gpt-6-astra
effort: max
status: stage-1-specification
contract_version: 1
---
# Planned backfill run contract

This specifies future behavior for [issue #19](https://github.com/karaposu/tgdata/issues/19).
The lifecycle API is **not implemented**. Stage 1 produces this contract; later stages
implement it and must pass the prescribed gates. Method/type sketches below are not
imports or runnable examples for the current package.

The [source record](stage-1-contract/source-input.md), [assumptions](assumptions.md),
[acceptance matrix](acceptance-matrix.md) and [live-validation specification](live-validation.md)
state the evidence and limits. dev baseline is `45bab71`; daily/fixed-window
prerequisites are separately on #18 at `e9b5154`. Telethon 1.45.0 is the only target.

## 1. Ownership and scope

The caller chooses accounts, schedules turns and durably stores/uploads accepted
messages. tgdata owns the saved historical intent, preparation/replay, acknowledged
progress, read admission and lifecycle transitions through the selected state store.
Temporary pending payload/media supports exact replay; it is not a permanent archive.

Support one active **source reader per group**, including separately scheduled daily
and historical collections. Status, controls and acknowledgments can overlap that
read. This contract supplies no lease, competing-worker recovery, account selection,
joining, edits/deletions, dashboard or background scheduler.

A run scans the declared visible scope under the account/access conditions in use.
It cannot certify an immutable or universally complete Telegram archive. Changing
accounts may change visibility; reading/account policy remains the caller's concern.
Live evidence must be gathered from an **existing group using read-only tests**.

## 2. Identities and immutable intent

**Collection:** a caller-named logical output collection and its state namespace.
Its stable `collection_id` is independent of a file path, machine or account. Configure
an isolated backend namespace for it; copying a store for a sequential move preserves
identity. Reusing a daily namespace for lifecycle records is an error, not a migration.

**Run:** one accepted historical intention. `run_id` is the caller-retained creation
request identity. The caller generates a fresh identity for a deliberately new job,
even if all query settings match, and retains it before the first submission.
A monotonically increasing `generation` scopes succession within a group/collection.
The identity used everywhere is the complete `RunRef`, not just a bare run label:

```text
RunRef = {collection_id, chat_id, generation, run_id}
```

**Command:** a control or recovery request with a caller-retained `command_id`, its
addressed run and expected context. Recognition binds an ID to its original action,
input and context. A changed payload using the same recognized identity conflicts.
The caller uses a fresh command ID for a new decision and reuses one only for an
unchanged retry. Detection of arbitrary ID misuse after historical retention is
not promised; expected context still prevents an unchanged stale request from applying.
IDs are not authorization secrets; the caller controls access to its backend/API.

**Attempt:** one durably admitted bounded call to the existing raw batch reader.
It has an internal `attempt_id` and exact run, input cursor and policy. It may contain
multiple SDK requests and retries. One attempt is not one RPC or a bounded duration.

**Delivery:** one saved observation owned by one run and destination:

```text
DeliveryRef = {run: RunRef, destination_id, batch_id}
PrepareContext = {run: RunRef, expected_after_id, expected_control_revision}
```

Python-facing identity/context integers remain exact integers. In portable JSON,
encode chat/message IDs, generations and revisions as canonical decimal strings;
small counts remain JSON integers. Datetime output uses canonical UTC text with
microseconds and `Z`. No floating-point conversion of an identifier is allowed.

`batch_id` retains MessageBatch v1's payload identity. It does not become a run or
query ID. Two different runs can contain the same batch hash. A delivery reference
must be presented in the original collection/backend context and match every field.

**Immutable intent** contains collection/group/destination, declared read origin,
initial exclusive message ID, media mode, original window request, resolved fixed UTC
bounds, batch size and pacing interval. Relative windows resolve once, on first accepted
creation; recognition checks the original input form before considering a clock.
Changing intent requires a fresh run; pause/resume do not alter it. Caller defaults
changing on restart cannot rewrite it. Relocating a verified media directory is not
an intent change; its bytes/hashes must remain the saved ones.

### Input validation and sketches

- Canonical group ID: non-boolean integer in signed 64-bit negative range. No group
  discovery, username resolution or Telegram call is performed by creation/status.
- Initial/expected message ID: non-boolean integer in `0..2**31-1`; batch size in
  `1..10000`, default 200. Generations/revisions are in `0..2**63-1` and never wrap;
  run generations start at 1 and overflow refuses rather than recycling old context.
- Identity text: case-sensitive, nonempty UTF-8, at most 256 bytes, no whitespace or
  control characters. Caller-generated UUID text is suitable. Do not use credentials.
- Dates: aware datetimes normalized to UTC, start inclusive/end exclusive, start < end,
  within the existing history-window wire range. Explicit end must be at/before the
  accepted creation time. `last_days` is an alternative positive integral duration of
  N × 24 hours, resolved once. Reject mixed/incomplete input, overflow and naive dates.
- Origin: `fresh` requires initial `after_id=0`; `imported` explicitly records caller-
  supplied progress and its qualified coverage, including a zero import if deliberately
  supplied. A nonzero ID never silently becomes evidence about its preceding archive.
- `pause_seconds`: required, finite nonnegative number, excluding booleans. Explicit
  zero disables this run's extra spacing; it never disables budget/server restrictions.
- Media: `references` or `download`. Download preparation needs a usable local directory;
  reference preparation rejects a supplied media directory. Receiver acceptance in
  download mode includes every required artifact in that prepared batch.

These are operation constraints. Stage 2 must define a strict versioned wire codec;
this document does not prescribe a SQL schema or silently change existing state v1/v2.

## 3. Independent saved facts and invariants

Status reports these together: immutable scope/origin, accepted cursor, pending
metadata, source-exhaustion evidence, active/uncertain attempt, operator intent,
terminal outcome, pacing/recovery evidence and observed source blockers.

`state_revision` changes on each durable aggregate mutation. `control_revision`
changes on accepted operator-control decisions; an ordinary ack need not change it.
Every result carries its addressed run and observed state revision. Response arrival
order is not state order. A stale response cannot be used to overwrite newer status.

Terminal outcome is absent, `completed`, `cancelled` or `abandoned`. Delivery facts
remain independent: owed/accepted/explicitly abandoned. A cancelled run can later
have all data accepted, or have its remaining obligation abandoned; it remains cancelled.

- **INV-01 — Fixed intent:** the same accepted run keeps its query, origin, destination
  and policy. Known-run absence is a recovery problem, not fresh enrollment.
- **INV-02 — Exact custody:** at most one nonempty pending batch per run; no new source
  attempt while it remains owed. Preserve payload and required artifact identity.
- **INV-03 — Accepted progress:** only a matching acknowledgment advances the cursor,
  only to the saved batch's next ID, atomically with settling pending. Abandonment
  never advances it as if data were delivered.
- **INV-04 — Qualified completion:** valid durable exhaustion of the declared scope,
  no active/uncertain source attempt, no owed batch/artifact, and no prior terminal
  cancellation/abandonment. Imported origin remains a caller assertion.
- **INV-05 — Scoped authority:** commands, source results and receipts affect only
  their addressed context. Equal parameters/hashes do not supply that authority.
- **INV-06 — Current read permission:** source admission requires matching prepare
  context, active operator intent, no terminal outcome/pending/unresolved attempt,
  and satisfied local timing gates. Actual budget/server admission is also required.
- **INV-07 — Persistent spacing:** failed or uncertain admitted work does not gain a
  free retry by restart. Local replay, status and acknowledgment do not restart a timer.
- **INV-08 — Control order:** current control comes from accepted transitions; the
  first accepted terminal disposition wins. Late results settle facts, not intent.
- **INV-09 — Atomic fact changes:** use one conditional aggregate transition for each
  lifecycle effect. No success before durable commit; an error can mean outcome unknown.
- **INV-10 — Live obligations survive retention:** keep their data/context until
  accepted or explicitly abandoned. Historical recognition may be bounded.
- **INV-11 — Evidence boundaries:** local activity never supplies Telegram health or
  receiver-durability proof; source failures are not empty/end success.
- **INV-12 — Single-reader recovery:** no overlapping source readers or inferred death
  from timeout. Recovery requires quiescence and authoritative state reconciliation.

The store offers async `load(chat_id)` and atomic exact-text `compare_and_swap` in
an isolated collection namespace. One record includes current run plus bounded
recognition metadata so a successor does not need a split pointer/run transaction.
The application still owns backend durability and access. No transaction spans
Telegram and the destination, or holds a database lock across network I/O.

## 4. Operation contracts

Returned names are sketches. `Status` is immutable/content-free; `CommandOutcome`
contains addressed identity, whether an effect was applied/recognized/refused and
attributable current status; `Turn` contains status plus optional batch/delivery ref.
Exact exception class names may be selected during coding; refusal categories below
and their no-mutation semantics are normative.

### OP-START — Create or recover the result of starting a run

```text
start_backfill(start_request, *, submission) -> CommandOutcome
StartRequest = {collection_id, chat_id, run_id, expected_predecessor,
                destination_id, origin, after_id, window_input,
                media_mode, batch_size, pause_seconds}
```

`submission` is required and is either `new` or `retry`: it has no implicit default. `expected_predecessor` is null
only for affirmative fresh first use, otherwise the full previous RunRef. The caller
must not declare fresh first use while it is actually recovering a known run.

**Preconditions:** valid intent and existing configured backend. A fresh successor
must match the current predecessor, which is terminal, quiescent and has no owed
work. Starting while an older run remains active or unresolved conflicts. Validate
the stored state and namespace; a backend failure is not an absent slot.

**Recognition first:** a retained matching creation identity with the same original
input returns its recorded creation effect and current addressed-run status without
reading the clock or creating again. Changed input conflicts. The request identity
must not be reused for a deliberately new intent.

**Unknown request:** `retry` returns `UnknownCommand` without creation, even if no
row exists. `new` may create only with its affirmative first-use/successor preconditions;
it is not a recovery fallback. An old predecessor context never becomes current
because its old request was pruned. Losing all authoritative history cannot be solved
by equal parameters; recovery stops, and recreating a collection is a separate explicit
operator decision outside automatic recovery.

**Success/effects:** atomically record new generation, frozen dates, origin/policy and
creation recognition. Initial accepted cursor equals declared origin; no accepted-
delivery evidence or exhaustion is invented. No Telegram or receiver operation.
A retry after uncertain write must use `retry` or inspect the known context; no blind
new submission. An uncommitted unknown start may require a deliberately new intent,
rather than promising that every retry can always make progress.

### OP-STATUS — Read a known run's facts

```text
get_backfill_status(run: RunRef) -> Status
```

**Preconditions:** complete valid RunRef and readable correct namespace.
**Result:** consistent current facts for the addressed run, or retained terminal
summary if available; include observed revision and whether history is limited.
A missing/pruned known context is `UnknownRun`, malformed state is `InvalidState`,
and backend outage is `StorageUnknown`. None creates a run or returns ready/complete.
**Durability/retry:** no transition; safe to repeat, but later snapshots may differ.
No Telegram, credential access, receiver action, timer refresh or health recovery.
There is no whole-store list/discovery/reset API in this delivery.

### OP-PREPARE — Prepare or replay the next delivery

```text
prepare_backfill(context: PrepareContext, *, download_media_to=None) -> Turn
```

**Preconditions:** exact run, expected accepted cursor and expected control revision.
Check against authoritative state before source admission. A stale context conflicts;
do not replace it automatically with current values. Validate directory/mode locally.

**If pending exists:** explicitly requested replay returns the exact stored batch and
its original DeliveryRef, after verifying required local artifacts. This is allowed
while paused or cancelled; it is not a source attempt. Missing/corrupt files refuse
replay without replacing its observation. Use a fresh control context after a pause.

**If no pending:** terminal/paused/timing/unknown-attempt conditions return attributable
status (or the specified recovery refusal) with no source send. Another active prepare
conflicts. When eligible, durably admit an attempt for this context before invoking
the raw reader. A failed or ambiguous admission write does not authorize a send.

**Source success:** validate the batch against the exact run, window, cursor and
media policy. In one durable transition settle that attempt, save pending if nonempty,
record end evidence if actually supplied, and save known pacing evidence. Return
only after that commit. Empty exhausted scope needs no fake delivery; apply INV-04.
Do not hide an empty observation by using the old `sync_group` wrapper.

**Source failure:** retain a fully prepared valid prefix when possible, then re-raise
the source error. It is not exhaustion. A prefix-persistence failure reports a local
storage error with the read failure separately available, not inherited as Telegram
health classification. Cancellation propagates; it does not acknowledge. If outcome
settlement is unknown, do not claim a prefix durable or clear the unresolved attempt.

**Late result:** reload after a concurrent control mutation. It may settle only its
same attempt/run/cursor with no incompatible pending work, preserving newer controls.
Do not overwrite a whole stale record, discard a usable result just because pause
changed, or issue another source request to repair a failed conditional write.

**Retry:** while its batch remains pending and context matches, replay is exact.
After acknowledgment changes progress, the old context refuses before another source
read. After pause/resume changes control, the old context also refuses. At unchanged
progress after a known failed/settled attempt, an eligible call can initiate a new
attempt; this is not indefinite replay of an old preparation command. An unresolved
attempt needs OP-RECOVER. A fresh intentional turn obtains current context from status.

### OP-ACK — Record destination acceptance

```text
acknowledge_backfill(delivery: DeliveryRef) -> Status
```

**Preconditions:** caller asserts that the named destination durably accepted the
exact batch and every required artifact. Match full context and the pending batch.
No cursor supplied by the caller can replace the saved next ID. tgdata cannot verify
this external assertion or make non-repeat-safe receiver processing exactly-once.

**Success:** atomically advance accepted position, settle pending, retain latest
receipt recognition and, if INV-04 becomes true, record completion. A paused or
budget-blocked run can complete this way. A cancelled run records accepted progress
while remaining cancelled. No source request, pacing reset or operator resume.

**Retry/conflict:** the latest recognized matching receipt has no second effect,
even if a newer batch is pending. Another run/collection/destination or unrecognized
old receipt refuses without touching current work. An explicitly abandoned receipt
refuses as retired; it cannot repair or advance a successor. Missing local files do
not prevent a valid acceptance already made by the destination from being recorded.
On an ambiguous write, reload or repeat this same receipt; never invent a rollback.

### OP-CONTROL — Pause, resume, cancel or abandon

```text
control_backfill(run: RunRef, *, command_id, expected_control_revision,
                 action) -> CommandOutcome
```

`action` is required: `pause`, `resume`, `cancel` or `abandon`.

**Common:** recognized identical commands report the prior effect/current addressed
status without reapplying. Reused ID with different input conflicts. A previously
unaccepted stale control revision refuses; do not auto-rebase it. Unknown forgotten
requests cannot acquire a fresh expected revision automatically. New explicit
commands may conflict even if the caller sent them later; acceptance order is authority.

**Pause:** atomically prohibit new source admission and advance control revision.
An already admitted bounded attempt may still make its remaining SDK calls and settle.
Pause is not a promise to stop all traffic instantly or revoke a batch already handed
out. Replay and valid ack remain possible. If already paused at the matching revision,
record the command's accepted no-change decision; do not turn it into a resume.

**Resume:** grant operator permission only. Preserve pending, waits, source blockers
and unresolved activity. It cannot revive any terminal run. Each accepted control,
including a matching no-change decision, has an attributable new control revision;
ordinary status/ack does not. Creation retries do not reset it.

**Cancel:** atomically record terminal cancellation and prohibit future admission,
while retaining in-flight work and owed delivery. It does not undo source/destination
effects. If completion is already durable, report already completed without rewriting
it. If cancellation commits first, late final acceptance stays cancelled. Do not
cancel by deleting the row or clearing pending data.

**Abandon:** require source quiescence (no active/uncertain attempt) and an explicit
withdrawal of outstanding delivery. Record which obligation was abandoned without
advancing accepted progress. An active nonterminal run becomes terminal abandoned;
an already cancelled run remains cancelled with delivery marked abandoned. An already
completed run remains completed. This is not automatic timeout cleanup, and physical
blob garbage collection is outside this API. It creates no new run.

**Durable point/retry:** the accepted control/recognition and relevant intent/terminal
change commit together. Refusal changes no facts. A lost response is reconciled through
same-command recognition or current status; an expired command can refuse harmlessly.

### OP-RECOVER — Resolve an interrupted source attempt

```text
recover_backfill(run: RunRef, *, attempt_id, command_id,
                 expected_control_revision, previous_reader_stopped) -> CommandOutcome
```

`previous_reader_stopped` is required with no default, and is an explicit caller assertion, not a lease or a timeout
heuristic; False refuses. The caller must actually stop/wait for the old worker.
If the same engine still has that attempt active, refuse regardless of the assertion.

**Reconcile first:** load authoritative facts. If its outcome/pending/completion already
committed, report those facts; do not fabricate another effect. A recognized identical
recovery returns its recorded outcome. A stale attempt/control/unknown run or backend
failure never enables source work. Refuse an unrecognized recovery of an already-
replaced attempt; it must not recover whichever attempt happens to be current.

**Uncertain attempt, quiescence established:** atomically settle the uncertainty with
no invented messages/ack/end. Preserve pending and accepted progress. If an end time
cannot be established, record one full configured quiet interval from accepted recovery,
while preserving stronger known restrictions. Its recovery identity and deadline survive
a lost reply/restart; repeating it does not start another wait. Preserve pause/cancel.
A subsequent source turn starts only through OP-PREPARE with current context.

**Known end time:** preserve its existing deadline rather than adding another interval.
Missing/untrustworthy time evidence remains an explicit eligibility blocker. Recovery
makes no Telegram or receiver call and never refunds read-budget charges itself.

## 5. Completion, timing and retention rules

Successful completion means exhausted **declared visible scan** plus accepted output,
not the biggest seen message ID or “the function returned.” A full batch (`limit`)
needs further evidence; a budget/transport failure on that follow-up leaves the run
incomplete. Empty legitimate exhaustion completes locally after durable settlement.
A final nonempty batch remains owed until ack. Completed-run status/reopen spends no
source requests; deliberately rescanning is new intent.

Fresh origin claims this run scanned the complete declared window. Imported origin
claims only its declared tail, with the earlier position explicitly caller-supplied.
Neither certifies other accounts' history or future edits/deletions.

Pacing begins at the **local end of an admitted source attempt**, including failed
work that may have contacted Telegram. A local refusal before admission creates no
pause. Replay/status/ack neither shorten nor extend it. A 10:00 end with 240 seconds
chosen makes another attempt locally eligible no earlier than 10:04, regardless of
whether ack arrives at 10:01 or 10:10. Other restrictions can still prevent reading.
Persist the policy and known deadline; use monotonic evidence within a process and
explicit trusted-UTC assumptions across processes. Never persist a process-relative
clock as universal time. Arbitrary undetectable clock jumps cannot be solved here.

Current budget admission belongs to the existing adapter using verified account
identity at the actual send. A saved refusal/retry estimate is a scoped observation,
not reserved capacity or fresh global account health. A future attempt rechecks it;
indefinite blockers are not zero waits. Per-run pacing does not promise account-wide
rest, ban prevention, automatic wake-up, scheduling fairness or a completion ETA.

Minimum recognition: active creation input; the active pending DeliveryRef; latest
accepted acknowledgment; latest accepted control; current attempt/recovery context;
and a bounded immediately prior terminal-run summary with its retained receipt/creation
metadata. Later unknown historical requests may refuse without mutation. No arbitrary
number-of-days retry promise is derived from this bounded-count policy. Never prune
context/data while it is an active delivery obligation. Revision/generation counters
must not reset or wrap to make old commands appear current.

## 6. Observable transition examples

| Initial facts / event | Required resulting facts | Forbidden inference |
|---|---|---|
| New valid fresh intent accepted | Fixed window/origin; no delivery/end proof | Creation means data already read |
| Pending exists; prepare with current context | Exact replay; no new attempt | Fetch a newer observation |
| Pending accepted | Cursor advances and pending settles atomically | Advance from caller-supplied ID |
| Empty successful exhausted scan | Durable end and completed if quiescent | Empty exception equals end |
| Nonempty end batch | Exhausted + pending, incomplete | Fetch completion equals delivery completion |
| Final ack while paused | Completed without source admission | Ack resumes reading |
| Cancel before final ack | Cancelled + accepted delivery facts | Late ack relabels success |
| Complete before cancel | Remains completed | Later control rewrites terminal history |
| Pause during admitted read | Paused + eventual result/pending | Result overwrites pause |
| Lost commit reply | Reload exact effect or report unknown | Every error implies rollback |
| Uncertain attempt | Recovery required; no second reader | Timeout proves the old reader stopped |
| Missing known run | Recovery fault | Automatically create a new window |
| Explicit abandon after cancellation | Cancelled; delivery abandoned; cursor unchanged | Abandonment is a successful ack |

## 7. Status and failure reporting

Status contains no message contents, credentials or raw backend error text. It names
scope/origin, run/generation, observed state/control revisions, accepted cursor, pending
ID/count/next cursor, source exhaustion, active/uncertain attempt, operator/terminal
facts, explicit abandonment and wait/last-failure metadata with observation times.
Multiple reasons may coexist. A display label is derived; it cannot erase those facts.

Distinguish invalid input, incompatible/corrupt state, unknown run/command/receipt,
stale/conflicting context, recovery required, media integrity failure, storage outcome
unknown, source error and normal waiting/terminal results. Refusals make no lifecycle
mutation or new source request. Preserve original source failures and cancellation;
never reinterpret a local validation/storage error as a Telegram verdict. Only the
actual raw source operation supplies Telegram health success/failure evidence.

## 8. Compatibility and validation boundary

Existing daily `initialize_sync/sync_group/acknowledge_sync/get_sync_status`, state
v1/v2, raw batch v1, session storage, budgets and legacy DataFrame behavior remain
unchanged. New records use an explicit incompatible kind/version; either engine
rejects another kind rather than guessing. Do not alter old APIs to acquire the new
command/retry contract by accident.

The stage sequence is 1–2 → Gate A → 3–4 → Gate B → 5–6 → Gate C → 7–8 → Gate D.
Only recorded PASS evidence permits dependent work. Stages have their own checks;
none of these API guarantees is considered implemented merely because this document
or a reasoning case exists. Changes that invalidate earlier evidence reopen its gate.
