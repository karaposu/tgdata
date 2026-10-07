---
model: gpt-6-astra
effort: max
revision: 1
---
# Stage 3 — prepare, retain, replay and acknowledge

Inputs: [desc.md](desc.md), [contract](../contract.md), [Gate A PASS](../validation/gate-a.md).
Baseline: `8023adf`, product `1425fd7`; Telethon 1.45.0 only. No rejected PR-critic or
PARKED state exists for this scoped task. Public facade work remains Stage 7.

### What is the task

Add internal durable delivery operations to the existing backfill aggregate. Admit
one source attempt before reading, publish its exact observation before returning,
replay it locally and settle only its full run/destination receipt. Keep uncertain
outcomes visible, preserve valid source prefixes and do not invent Telegram health
or receiver acceptance from local work.

### Huge Hard Blockers

#### Planning Blockers

None identified. The state/identity/CAS contracts already exist. Gate A observed the
real source and artifact fundamentals before this dependent stage. The local atomic
store/media primitives can be probed again cheaply before implementation; synthetic
transport tests of the new code remain explicitly non-covering for live source behavior.

#### Execution Blockers

None for Stage 3 implementation and offline verification. Gate A is DONE. The actual
new-engine live composition belongs to Gate B after Stage 4; it is not claimed here.
Positive timing/recovery/control operations retain their named later stages and do
not authorize silently weaker behavior during this staged delivery.

### How this implementation moves toward desired state

Keep a single exact-text CAS aggregate and MessageBatch v1. Extend the internal engine
with a reader callback, prepare(context) and acknowledge(delivery). Source admission,
settlement and receipt acceptance are distinct conditional writes. Local replay/ack
never call the reader. Retain same-attempt uncertainty on cancellation or unconfirmed
settlement. Existing local-error provenance and owned payload/artifact checks are reused.

### High-Level Summary

| Step | Description | Output |
|---|---|---|
| 1 | Values, local errors and stored batch bounds | backfill.py / backfill_state.py |
| 2 | Local guards and confirmed source admission | backfill_engine.py helpers / admission |
| 3 | Publication, replay and source-failure handling | prepare and same-attempt settlement |
| 4 | Scoped atomic acknowledgment | acknowledge and retained-receipt recognition |
| 5 | Real persistence, SDK/media and receiver tests | test_25_backfill_delivery.py |
| 6 | Staged usage and boundary documentation | docs/backfill_state.md and task records |
| 7 | Full offline verification and checkpoints | product/evidence commits, feature push, #19 update |

## Interface and stage decisions

`BackfillEngine(store, collection_id, *, read_batch=None, clock=UTC_now)` preserves
existing calls. `read_batch`, when supplied, is an async callable compatible with
`TgData.get_message_batch`; None supports storage-only/replay/ack operations. No new
session, configuration or client constructor is introduced.

- `BackfillPrepareContext(run, expected_after_id, expected_control_revision)` is immutable,
  validates complete RunRef and exact integers, has portable conversion and `from_status`.
- `BackfillDeliveryRef(run, destination_id, batch_id)` is immutable, validates every
  scope field and a lowercase SHA-256 identifier, and round-trips without float IDs.
- `BackfillTurn(status, batch=None, delivery=None, replayed=False)` has an owned immutable
  batch and a full receipt when data is owed. No-data turns carry attributable status.
  `to_dict()` copies payloads; the batch itself retains its original v1 bytes/hash.
- Add local `BackfillUnknownReceipt`, `BackfillRecoveryRequired`, `BackfillMediaError`
  and `BackfillClockError` categories. RecoveryRequired may carry content-free status.
  Local errors suppress implicit RPC context; `read_error` remains explicit data.

The wire schema remains version 1 with the existing fields. Strengthen loaded pending
validation to require no more messages than the immutable run's batch size. Do not
infer end from length or require a short limit marker to mean exhausted.

**Stage boundary:** successful `end` necessarily records exhaustion. Fulfilled exhaustion
must close as completed unless prior cancellation/abandonment wins, because the existing
codec and contract prohibit an unqualified intermediate state. Include that minimal
closure, but leave Stage 4's completion/uncertain-write audit and full crash matrix open.
Store known post-attempt UTC timing, with minimum duration rounded up by `_pause_delta`.
Do not implement Stage 5 timers/recovery: another source read after a settled positive
pause or unresolved timing refuses as an explicit staged limitation. First source turns,
zero-pause continuation and all valid local replay/ack remain usable. No implicit policy
override or automatic sleeping. Source attempts with an invalid/regressed ending clock
remain unresolved rather than inventing a trusted settlement time.

## Step 1 — Add delivery values and invariant checks

### Proposed changes

Extend `tgdata/backfill.py` with the three values and local errors above. Normalize
inputs through owned portable snapshots at engine entry. Validate Turn agreement among
status/pending metadata, batch and DeliveryRef. Extend `_record` in `backfill_state.py`
with the immutable batch-size upper bound; preserve all existing end/control/cursor
checks and record keys. No root exports or facade methods.

### Output

Exact scoped request/receipt/result types and a codec that refuses oversized pending data.

### Safe in nature

False — these values carry authority to advance durable progress.

### Peripheral concepts

RunRef, canonical decimal IDs, MessageBatch ownership, state version 1, content-free status.

### Hardness Lvl

4/5.

## Step 2 — Add local selection, guards and durable admission

### Proposed changes

Extend `backfill_engine.py`, keeping lifecycle transitions together. Add helpers for
validated current/retained run selection, strict boolean CAS, UTC observation, directory
mode/type checks and artifact verification. Preserve exact loaded text as CAS expectation.
Clock/provider/media/backend errors are local and sanitized. Cancellation is raised
explicitly with suppressed implicit context, including cancellation inside a source-error
handler. Do not change the original ordinary source exception/cause chain.

Track preparation per group on this engine before the first await. Another local
prepare conflicts; another instance sees the persisted attempt and requires reconciliation.
Caller still excludes source readers in other collections/daily jobs; this is not a lease.

`prepare` validates complete context and namespace, loads strict state and matches the
accepted cursor/control revision. Check pending first for replay. With no pending,
return terminal/paused status without source work; refuse an unresolved attempt. Refuse
unimplemented repeated positive-pause/uncertain timing admission. For an eligible read,
validate the callback and local media root, observe UTC and build a fresh attempt ID,
cursor/control/admission timestamp. Reserve revision headroom for admission, settlement
and possible acknowledgment; refuse near the counter limit before reading. Commit the
attempt with one CAS. False, nonboolean, failed or cancelled admission never invokes the
reader; an uncertain committed marker remains visible. No transaction spans a source await.

### Output

No new read without a confirmed, attributable attempt and satisfied implemented guards.

### Safe in nature

False — this is the budget-spending/source boundary.

### Peripheral concepts

Opaque async backends, CAS uncertainty, single-reader precondition, revision bounds, clocks.

### Hardness Lvl

5/5.

## Step 3 — Settle one observation, replay exactly and preserve failures

### Proposed changes

Call the injected raw reader once with the saved canonical group, accepted cursor,
batch size, fixed dates and selected media root. Never call sync_group or refetch to
repair a CAS conflict. Reconstruct an owned MessageBatch and validate group, cursor,
mode, dates and size. Normal success requires end/limit; exception prefixes require
interrupted. Invalid results are local errors and leave the admitted attempt unresolved.

After the source await, observe a valid non-regressed UTC end and derive the saved
pacing deadline. Validate download artifacts before publication. Reload authoritative
state and match the entire admitted attempt, run, accepted cursor and immutable intent.
Retain newer compatible control/terminal facts. Publish nonempty pending data, clear
only this attempt, replace its timing facts and record actual end evidence atomically.
Clear superseded recovery recognition when replacing its attempt context. Retain safe
last-failure metadata as a historical observation, not an admission grant or health verdict.
Use bounded CAS-conflict reloading (at most four publication attempts), never another
source call. Nonempty publication reserves room for its later ack. Return a Turn only
after confirmed commit, with status from that committed revision. No hidden auto-retry
after an exceptional/ambiguous write; status/retry can observe a committed pending batch.

Replay validates the current context, verifies every unique required hash/size through
the existing non-symlink file verifier, then returns the same v1 bytes/ref locally.
Directory relocation is allowed. No callback/clock/pacing update or file cleanup. A
missing/corrupt artifact does not become permission to download another observation.

On ordinary read failure, validate its optional partial_result. Publish a valid nonempty
interrupted prefix before re-raising the same error; settle a known failure with no prefix
without inventing pending/end. Store only failure category/class/time and authoritative
budget fields if supplied by the budget exception, never cached account identity/error
text. Failed prefix validation/media/storage settlement raises a local error with the
original in `read_error`, not its causal chain. Cancellation propagates and leaves any
unconfirmed attempt/result for reconciliation; it never claims rollback or publishes an
invented prefix. Always release the local preparation guard while preserving durable facts.

### Output

Durable prepared/replayed Turns, exact prefix preservation and attributable uncertainty.

### Safe in nature

False — incorrect settlement could overwrite an owed batch or newer authority.

### Peripheral concepts

Source stop reasons, partial_result, media custody, health causality, future control compatibility.

### Hardness Lvl

5/5.

## Step 4 — Apply complete delivery receipts atomically

### Proposed changes

`acknowledge(delivery)` selects only its exact current/retained run and destination.
Recognize that run's latest accepted hash first, even if newer pending work exists,
without clock, file or reader access. Unknown/abandoned/wrong-context receipts refuse.
For a current matching pending obligation, observe UTC, advance only to its saved next
ID, clear pending and record latest acknowledgment in one CAS; derive the minimal
required completion fact while preserving earlier cancellation and operator intent.
Never verify/remove media, call the receiver, change pacing or infer an acceptance.
Reload after a false CAS to recognize an already-applied receipt or preserve newer
compatible controls, at most four attempts. An exceptional write remains explicitly
uncertain and must be inspected/retried with the same receipt. Retained previous receipt
recognition must not mutate the current successor.

### Output

Run/destination-scoped progress with harmless latest receipt retries and no source effects.

### Safe in nature

False — this is the only transition that declares output accepted.

### Peripheral concepts

External durability assertion, bounded recognition, control order, aggregate revision, no media dependency.

### Hardness Lvl

5/5.

## Step 5 — Exercise real persistence and the actual source/media composition

### Proposed changes

Add `test_25_backfill_delivery.py`. Use disposable real SQLite and sockets forbidden.
Use the existing actual TgData/Telethon iterator/budget/artifact fixtures with synthetic
transport for source composition; distinguish this from Gate A's live evidence.

Cover value precision/ownership; before-source confirmed admission/no held transaction;
explicit/frozen query reuse; restart/replay with a forbidden reader/clock; stale contexts;
same-engine overlap and two-instance CAS; zero-pause continuation; positive timing staged
refusal; empty/final invariant closure; original failures with/without partials; invalid
source output; failed prefix storage and real cleanup errors; cancellation at load,
admission, source and committed publication; required recovery and released local guards.

Exercise full receipt/destination/run/generation isolation, equal batch hashes in different
runs, duplicate latest ack with newer pending, prior-run recognition and expiry, false CAS
control races and wrong/incompatible settlement. Seeded paused/cancelled/recovery snapshots
are explicitly future-state fixtures, not tests of unimplemented control/recovery APIs.
Test media relocation, corruption, missing files, symlinks, valid ack after media removal,
and absence of false health events/recovery or secret error text. Include revision/clock
edges and bounded conflict retries.

Use actual subprocess exits before/after pending publication and ack commits plus a real
SQLite receiver transaction followed by a lost local reply. Confirm exact replay,
deduplicated receiver records and no skipped accepted cursor. No claim of power-loss or
remote-backend certification. Adjust test_24's explicit Stage-2-only absence assertion to
the newly planned internal methods, retaining no-facade/control/recovery assertions.

### Output

Delivery/state/failure receipts for the new implementation, not only input-mirroring tests.

### Safe in nature

True — disposable state and blocked external network.

### Peripheral concepts

Real commit boundaries, receiver idempotence, actual SDK internals, legacy fixtures, offline health observation.

### Hardness Lvl

5/5.

## Step 6 — Document available behavior and remaining stages

### Proposed changes

Update `docs/backfill_state.md` and smoke-test README with exact direct-module usage,
full receipt acknowledgment, error/replay handling and artifact ownership. State the
positive-pause/uncertain-attempt limitation explicitly. Update task availability and
scoped case evidence, preserving the accepted full contract and unrun Stage 4/Gate B.
Record deviations/corrections and provenance; do not call seeded transitions live.

### Output

Reviewable staged usage and a precise handoff to Stage 4.

### Safe in nature

True — documentation only.

### Peripheral concepts

Caller acceptance, staged API availability, source/live evidence boundaries.

### Hardness Lvl

3/5.

## Step 7 — Verify and checkpoint

### Proposed changes

Compile changed Python and check Python 3.7 AST syntax, then run test_25 and the full
supported offline suite: test_24, 23, 22, 19 through 12 and two explicitly awaited
offline test_11 helpers. Run the existing offline daily example and the ten Gate A
instrument checks after the new value/engine changes. Telethon 1.45.0 only. Separate
actual passes from the three existing explicit live skips; no legacy live entry point.

Fix only local nonarchitectural failures in this run and rerun affected checks. Record
every correction, actual tested environment and limitations. Commit product code/tests/
public docs separately from work-folder evidence; push only this feature branch and
update #19's scoped Stage 3 status while preserving its original request. Gate B remains
after Stage 4, and no PR/merge is performed.

### Output

Verified Stage 3 implementation, committed/pushed evidence and accurate issue handoff.

### Safe in nature

False — publishes new persistent behavior on the feature branch.

### Peripheral concepts

Supported regressions, legacy compatibility, branch/issue workflow and evidence privacy.

### Hardness Lvl

4/5.
