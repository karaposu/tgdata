---
status: draft
revision: 5
model: gpt-6-astra
effort: max
---
# Planned backfill lifecycle — staged implementation plan

Imported overall draft for #19, prepared from the completed
[lifecycle source record](stage-1-contract/source-input.md#behavioral-basis).
It does not mark a formal pipeline step complete or authorize implementation,
publication or merge. It leaves the existing daily-continuation and fixed-window
implementation records intact.

Planning baseline: branch `feat/18-daily-group-continuation` at `d1f37f7`;
product code at `e9b5154`. Session metadata confirmed GPT 6 Astra / max for this
planning turn. Target SDK: **Telethon 1.45.0 only**.

## Revision 2 — validate assumptions before building on them

User direction: after every two stages, use a real Telegram connection and extensive
testing to check the assumptions on which later work depends. This revision adds
blocking gates after Stages 2, 4, 6 and 8, brings the live test harness and assumption
record into Stage 1, and makes real-source evidence a prerequisite for advancing.
It supersedes the draft's offline-only progression. This is a user-directed draft
revision, not the formal critic/fold revision or a claim that any gate has passed.

**Published issue:** [#19 — Add durable backfill runs with staged live Telegram validation](https://github.com/karaposu/tgdata/issues/19).
The issue carries this staged plan and its four gates as a focused follow-up within
#18. The original revision 2 source in #18 remains an uncommitted draft; this #19
working copy is checkpointed with its Stage 1 records. Publication alone completes
no formal implementation checkpoint. Task-specific artifacts now belong in this
#19 work folder, with the original #18 draft retained as their source.

## Stage 1 contract handoff — revision 3

The user selected Stage 1 only via task-impl, then selected an existing group with
read-only tests. The [contract](contract.md), [assumptions](assumptions.md),
[acceptance matrix](acceptance-matrix.md) and [live specification](live-validation.md)
are the Stage 1 deliverables. Their local pipeline is recorded in
[stage-1-contract/](stage-1-contract/step_by_step_impl_plan.md).
No later implementation or gate is marked complete by this handoff.

Two selected critic mitigations refine the future operation contract:
- Explicit new submission versus retry for starting a run. Unknown retry cannot
  create, and fresh/successor intent requires affirmative predecessor context.
- Preparation carries expected accepted position and control revision. A stale call
  cannot silently become permission for another read after ack or pause/resume.

Read-only existing history replaces the earlier dedicated/seedable-fixture preference.
Independent complete enumeration is required for a bounded source-selection oracle;
missing critical cases or source drift remain blocked/inconclusive. No source writes,
group joins or membership changes are part of this test scope.

At the Stage 1 checkpoint this dev-based branch did not contain #18's runtime.
The Stage 2 handoff below records its later feature-only integration. Preserve the
mandatory A/B/C/D gate order below.

## Stage 2 implementation handoff — revision 4

The user selected Stage 2 via task-impl. Its [folded plan](stage-2-state/step_by_step_impl_plan.md),
[implementation](stage-2-state/implementation.md) and [verification](stage-2-state/verification.md)
record the build. #18 prerequisites through `e9b5154` were merged only into this feature
branch by `5d0789e`; product code/tests/public docs are committed in `1425fd7`.

Steps 2.1–2.4 and the opt-in instrument are built and verified offline. Start/status
are internal direct-module operations; later transitions remain unimplemented. Two
selected Stage 2 critique remedies add existing-only SQLite reopening and upward
microsecond rounding of minimum durations, without changing the chosen policy.
Gate A was initially blocked on resources. The user supplied the account, two existing
sources and exclusive test-budget context; [live validation passed](validation/gate-a.md)
on 2026-10-07. This revision 5 handoff unblocks Stage 3. Stages 3–8 and Gates B–D remain
pending; the live receipts are separate from the original offline passes.

## What is the task

Add a durable lifecycle around one group's planned historical read, so the caller
can fetch in small turns, deliver and acknowledge data, stop, restart, pause or
cancel without losing progress or inventing completion. A saved run retains its
fixed window, declared starting point, pacing and outstanding work. tgdata owns
these rules through a caller-selected state store; the caller owns the permanent
archive, destination acceptance, account selection and scheduling.

## Huge Hard Blockers

### Planning Blockers

**None identified for this plan.** The request to plan from the finding supplies
the behavioral basis: closed historical windows, post-attempt spacing, pause of
new reads, terminal cancellation and explicit receipt ownership. These remain
visible planning decisions below; drafting the plan does not claim approval to
ship them.

The required atomic storage primitive already exists: async opaque-text `load`
and `compare_and_swap`. The raw batch API already returns a real end observation,
including an empty one, and preserves completed prefixes on ordinary failure.
No distributed ownership service, new account pool or #7 health redesign is needed.

Rejection guard: no `pr-critic*.md` rejection records exist for this lifecycle
slice or its parent #18 work folder. The paused #7 task is unrelated to this plan.

### Execution Blockers

No external account is needed to prepare Stages 1–2 or run their local tests once
implementation is requested. Advancement beyond Stage 2 now requires live evidence.
The following conditions attach to their named gates:

- **What must happen:** identify the test account/session, accessible test group,
  independent fixture manifest, bounded request allowance and test pacing. Reuse
  these choices at later gates while the scope remains the same. **Who:** application
  owner and implementing session. **Blocks:** Gate A after Stage 2, therefore Stage 3
  and subsequent dependent work. **Status:** CLOSED for A on 2026-10-07; qualified in
  its report. Later gates requalify their own conditions; no offline pass substitutes.
- **What must happen:** execute and record each required validation gate successfully.
  **Who:** implementing session, with the maintainer reviewing changed assumptions.
  **Blocks:** Gate A → Stage 3; Gate B → Stage 5; Gate C → Stage 7; Gate D → feature
  review/release readiness. **Status:** A passed; B–D remain OPEN/unrun.

- **What must happen:** the integration names its durable destination acceptance
  point and supplies its chosen pacing and retry policy. **Who:** application owner.
  **Blocks:** Stage 8, step 8.3, operational adoption only. **Status:** OPEN.
  A local durable receiver can exercise the library contract before this.
- **What must happen:** implementation is requested and the repository's preparation,
  plan critique and fold checkpoints are completed. **Who:** maintainer and implementing
  session. **Blocks:** production-code execution of each selected stage. **Status:** DONE
  for Stage 2; OPEN for later stages, subject first to the mandatory live gates.
- **What must happen:** merge check, fresh PR critique and explicit merge go-ahead.
  **Who:** implementing/reviewing session and maintainer. **Blocks:** merging after
  Stage 8. **Status:** OPEN. Nothing in this plan performs those actions now.

## How this implementation moves toward desired state

The existing daily/fixed-window engine stores a cursor and one pending batch. It
has no durable job completion, accepted pause/cancel history or pacing lifecycle.
Its `sync_group` result also collapses an empty successful scan to `None`.

Add a separate backfill engine over the existing **raw** `get_message_batch` API.
Reuse the batch format, date selection, media verification, budget adapter and
opaque-text storage protocol. Keep the new run's pending data, accepted position,
end evidence and controls in **one atomic state record**. This avoids an old sync
acknowledgment and a separate job update committing independently.

Build and test the internal layers first, exercising the real source after each pair
of stages. Before the new public facade exists, an opt-in harness calls the existing
raw batch API and then the new internal engine. It does not simulate the eventual
lifecycle merely to make the first gate pass. Public `TgData` methods are wired in
Stage 7. Every stage includes its own tests; the final stage checks the combined
behavior through the public API against both controlled failures and real Telegram.

## High-Level Summary

| Stage | Steps | Description | Expected output |
|---|---|---|---|
| 1 | 1.1–1.3 | Fix the public contract and failure expectations | Reviewed scope, operations, state invariants and acceptance matrix |
| 2 | 2.1–2.4 | Save run identity and state atomically | Durable create/reopen/status; Gate A validates the foundations |
| 3 | 3.1–3.4 | Prepare, replay and acknowledge one batch | Exact pending delivery with run-scoped acknowledgments |
| 4 | 4.1–4.3 | Establish truthful completion and recover uncertain writes | Durable completion; Gate B validates delivery and restart |
| 5 | 5.1–5.4 | Enforce pacing, budget stops and interrupted-attempt recovery | Persistent read eligibility without an internal scheduler |
| 6 | 6.1–6.4 | Add pause, resume, cancel and retirement | Accepted intent survives races; Gate C validates timing and controls |
| 7 | 7.1–7.3 | Expose the API and document the caller's part | Public facade, honest status and an offline receiver example |
| 8 | 8.1–8.3 | Verify combined failures and prepare review | Regression evidence plus Gate D through the complete public flow |

Order: **1 → 2 → Gate A → 3 → 4 → Gate B → 5 → 6 → Gate C → 7 → 8 → Gate D**.
The gates are mandatory, not optional final-stage reassurance. No dependent stage
begins after a failed, blocked or inconclusive gate. Partially implemented stages
are not independently ready for production.

## How the validation gates work

**Write the assumption and expected observation before the test.** Stage 1 creates
`assumptions.md`: each critical premise names its dependent stages, earliest gate,
test method, expected outcome, evidence and current status. Assertions about Telegram,
local persistence and receiver acceptance have different evidence requirements.
Listing an assumption or running a successful connection is not confirmation.
Probe a later-stage premise in Gate A whenever the current reader/storage can already
falsify it; the two-stage cadence is the latest scheduled checkpoint, not a reason
to postpone an earlier useful experiment. Keep the critical expected outcomes fixed
before observing results, and trace a failed premise to every dependent stage.

| Critical premise | Earliest evidence | Consequence if contradicted |
|---|---|---|
| Telegram ID continuation and date/end behavior match the declared scan | Gate A, live fixture and actual SDK pagination | Revisit the reader/window contract before building the lifecycle around it |
| One conditional record can preserve intent and survive uncertain writes | Gate A, real SQLite process/commit checks | Revisit the state/storage boundary before adding delivery |
| A saved observation and scoped receipt are sufficient for safe replay | Gate B, real data and interrupted delivery | Revisit pending custody, artifact handling or acknowledgment identity |
| The destination's acceptance is durable and repeat-safe | Gate B for the test receiver; Gate D for the selected integration | Correct the receiver contract/flow before claiming accepted progress |
| End evidence plus accepted delivery supports the declared completion claim | Gate B, empty/full/final/failed reads | Revise completion semantics before pacing and controls depend on them |
| The source-attempt boundary fits actual SDK activity | Characterize at Gate A; validate pacing/recovery at Gate C | Revisit attempt admission/settlement rather than merely changing a timer |
| Accepted controls survive delayed results and terminal races | Gate C, forced orderings around real reads/storage | Revisit transitions and their atomic scope before exposing the API |

Use three complementary forms of evidence at each gate:

- **Live-source checks:** actual authenticated Telegram reads through Telethon 1.45.0,
  using the intended session/proxy/budget path and a known fixture set. Compare with
  an independently recorded list of expected message IDs, dates and selected media,
  not a second invocation of the same fetch function as the sole oracle.
- **Controlled failure checks:** real reads and real durable storage, with test-only
  barriers, process termination and delayed/lost local responses at named boundaries.
  Label injected failures precisely. A local disconnect is not evidence of how a real
  Telegram ban or server flood restriction behaves.
- **Deterministic local checks:** exhaust the timing/order/state cases that cannot be
  reliably reproduced from the live service, including clock faults and malformed
  state. Synthetic transport remains useful but is identified as synthetic.

Use the user-selected existing group with read-only tests. Establish its independent
existing-history oracle and read limits before the first gate. Do not set up messages/
media in Telegram, join groups or change membership to manufacture a fixture. Do not generate high request volume to provoke server
restrictions: a small locally configured read allowance exercises budget exhaustion.
Before built-in run pacing exists, the harness enforces spacing externally. Extensive
testing means coverage of distinct assumptions and failure boundaries, not large pulls.

Each gate saves `validation/gate-a.md`, `gate-b.md`, `gate-c.md` or `gate-d.md` with
the exact code revision, SDK/configuration metadata without credentials, fixture,
expected and actual outcomes, request counts/timing, receiver/store evidence, failures,
remaining limits and the next-stage decision. Summaries omit message contents and
credentials. Per-case results distinguish LIVE, INJECTED and LOCAL evidence.

Gate verdicts are **PASS**, **FAIL**, **BLOCKED** or **INCONCLUSIVE**. PASS requires
all critical assertions assigned to the gate and the relevant regressions to pass;
skipped required cases cannot count as PASS. Evidence supports the tested account,
group, backend and operating conditions, not universal Telegram behavior.

If a critical premise is contradicted, preserve the failing case, mark its dependents,
and revise the affected contract/earlier stages and plan before continuing. Do not
weaken the expectation simply to keep the existing design. Re-critique a changed
premise and rerun its gate. An ordinary implementation bug can be fixed within the
accepted contract, with the failed case and affected checks rerun. Later changes that
invalidate earlier evidence reopen the relevant earlier gate. While live access is
blocked, only work independent of the unvalidated premise may proceed.

## Decisions this plan carries forward

1. **One saved intent per run.** A run has a collection/group context and a stable
   identity distinct from its batch hashes. Reopening and retrying creation are
   different operations from deliberately starting a new run.
2. **Closed windows and declared origin.** Resolve relative dates once. A fresh
   whole-window run starts at `after_id=0`. An imported nonzero position is explicit
   and is reported as caller-supplied progress, not verified earlier collection.
3. **One pending batch per run.** No further source batch is prepared while it is
   owed. Retain exact data/artifacts until acceptance or explicit abandonment.
4. **One atomic lifecycle record.** It contains all facts needed to settle an
   attempt or acknowledgment. No split write to an independent cursor and job flag.
5. **Completion has evidence.** Source exhaustion, no unresolved attempt, and no
   outstanding delivery are required. Cancellation/abandonment remain distinct outcomes.
6. **Pacing belongs to source attempts.** Apply the selected quiet interval after
   each admitted bounded attempt settles. Conservatively count attempts that might
   have contacted Telegram; a validation or local eligibility refusal before an
   attempt is admitted does not create another pause. A turn can contain several
   SDK requests; this is not a new per-RPC rate limiter.
7. **Numeric settings are explicit.** Keep the existing batch-size range; use 200
   as the proposed default. Require the caller to choose the pacing interval,
   including an explicit zero if spacing is intentionally disabled. The ScrapeOps
   example of 240 seconds is an example, not a Telegram-safe-rate guarantee.
8. **Controls have accepted order.** Pause prohibits new reads while settlement
   remains possible. Cancellation is terminal for that intent. Stale commands
   cannot silently rebase onto newer control state.
9. **Bound historical recognition, not live obligations.** Keep the active creation
   identity, current pending receipt, latest applied acknowledgment and latest
   control receipt. Retain a bounded prior-run terminal summary. Older unrecognized
   requests may refuse without mutation; a pending receipt never expires while owed.
   Do not promise an arbitrary time-based retry horizon from a count-based record.
10. **Explicit recovery.** After an unknown attempt, require the single-reader
    precondition to be re-established, then record one conservative recovery wait.
    A timeout alone is not proof that an earlier reader stopped.

### Proposed module boundary

| File or interface | Responsibility |
|---|---|
| `tgdata/backfill_state.py` — new | Versioned run record, strict validation, invariants and transition helpers |
| `tgdata/backfill_engine.py` — new | Creation, preparation, acknowledgment, controls, recovery and read admission |
| `tgdata/backfill.py` — new | Public immutable run reference, status/result types and local error types |
| `tgdata/sync_store.py` — existing | Reuse the opaque-text backend contract and `SQLiteSyncStore`; no new SQL transaction protocol |
| `tgdata/history_window.py`, `message_batch.py`, `batch_files.py` — existing | Reuse date/batch/artifact semantics; extract a shared helper only if necessary and regression-covered |
| `tgdata/tgdata.py`, `tgdata/__init__.py` | Additive facade wiring and exports in Stage 7 |
| `tgdata/smoke_tests/test_24_backfill_state.py` — proposed | Storage, identity, command and terminal-state invariants |
| `tgdata/smoke_tests/test_25_backfill_delivery.py` — proposed | Real batch/SDK, pending data, acknowledgment and media behavior |
| `tgdata/smoke_tests/test_26_backfill_lifecycle.py` — proposed | Pacing, crash recovery, control races and combined histories |
| `docs/backfill_runs.md`, `examples/backfill_runs.py` — new | Public contract and runnable offline delivery/restart example |
| `devdocs/work/19-backfill-run-lifecycle/live_probe.py` — planned | Explicit opt-in harness for early live-source checks and controlled local failures |
| `devdocs/work/19-backfill-run-lifecycle/assumptions.md` — planned | Critical assumptions, earliest falsification tests and dependent stages |
| `devdocs/work/19-backfill-run-lifecycle/validation/gate-*.md` — planned | Actual gate evidence and advance/revise decision; never prefilled as passed |

Use a dedicated logical backfill store, for example
`SQLiteSyncStore("backfill-progress.sqlite3")`, supplied separately from `sync_store`.
The backend already treats its text as opaque. The new engine validates its own
explicit record kind/version and refuses daily/window records. Conversely, old
sync code must reject lifecycle records. A custom database can provide separate
namespaces instead of separate physical files. Do not repurpose an existing daily
store or silently convert its progress into a backfill run.

The aggregate is keyed by the canonical group ID within that collection. It keeps
one current run and bounded recognition metadata, so starting its successor does
not require an atomic transaction across two independent backend keys. New run
creation names the expected predecessor/generation; it cannot overwrite unresolved
work. This does not provide leases or support competing readers.

## Stage 1 — Fix the contract and acceptance matrix

### Proposed changes

**1.1 — Record the lifecycle task's scope and public operations.** Prepare the formal
`run-lifecycle/desc.md` and contract when implementation is authorized, drawing from
the finding rather than copying the old daily-only description. Define explicit
operations to create a run, prepare one turn, acknowledge a delivery, read status,
apply a control and recover an interrupted attempt. Proposed facade names are
`start_backfill`, `prepare_backfill`, `acknowledge_backfill`, `get_backfill_status`,
`control_backfill` and `recover_backfill`; exact parameter names may be refined in
review without changing the semantics.

Creation carries a stable caller-retained request identity, expected collection/run
context and immutable intent. Controls carry a request identity and expected control
revision. Delivery acknowledgments carry their collection/group/run/batch context.
Callers retain request identity before the first submission if they need safe retry
after losing the response. Equal parameters alone are not a retry key.

**1.2 — Define observable results and transitions.** Write the transition table and
content-free status contract: declared scope, accepted cursor, pending delivery,
source exhaustion, active/uncertain attempt, operator intent, terminal outcome,
applicable waits and last observed failure. A turn returns a status plus an optional
batch and scoped delivery reference; do not make all non-batch outcomes `None`.
Ordinary source errors still raise after any usable prefix has been saved. Status
exposes the stop reason without claiming it is a fresh global account-health check.

**1.3 — Turn the finding into acceptance cases and review the plan.** Map the 22
adverse histories to expected observable outcomes. Add the implementation-specific
boundaries below: a control update during a read, a failed attempt-state save before
network admission, incompatible stored versions, and a repeated recovery command.
Complete the applicable description/plan critique/fold checkpoints before production
code. If review exposes a missing fundamental premise, revise the plan before coding.

Prepare the assumption record and opt-in live-probe specification here. Identify the
test account/group and expected fixture independently of the implementation. During
Stage 2, build the small executable harness specified in live-validation.md for Gate A; do not wait for the
Stage 7 public backfill facade. Plan assertions for frozen dates, canonical identity,
timestamp boundaries, ID pagination, source exhaustion, media and visible-history
limits, alongside the local atomicity tests. Connect every critical assumption to
the first gate that can falsify it.

### Output

A lifecycle-specific contract, typed operation sketches and a traceable acceptance
matrix. Retrying, replacing, pausing, cancelling and acknowledging each have one
meaning. No claim that the existing implementation already provides them.

### Exit check

Every public operation names its authority, durable success point, retry behavior,
possible conflict and effect on pending data. Every completion path names its evidence.
The first live gate has an executable test specification, fixture requirements and
an explicit list of critical assumptions; later-stage guarantees are not credited early.

### Safe in nature

True — documents and test scenarios only.

### Peripheral concepts

Canonical chat identity, collection scope, caller-owned acceptance, contribution gates.

### Hardness Lvl

3/5. The behavioral inquiry is finished; this step makes its API consequences explicit.

## Stage 2 — Persist identity and run state together

### Proposed changes

Implementation entry required the #18 daily/window prerequisites. They are available
on this feature branch through merge `5d0789e`; their separate dev review/merge remains
outside this stage. The changes below are built at `1425fd7` with scoped local evidence.

**2.1 — Add the strict lifecycle record and codec.** Store immutable intent and frozen
dates, declared origin, run/generation identity, acknowledged progress, pending
observation, exhaustion evidence, active attempt, pacing evidence, control revision,
terminal disposition and bounded command/receipt recognition. Define invariants
before serializers. Reject missing/duplicate/unknown fields, unsupported versions,
invalid IDs/times, contradictory states and pending data outside the declared scope.
Do not repair or infer corrupt records during load.

**2.2 — Reuse atomic storage as one aggregate.** Use the existing async load/CAS
protocol and real SQLite backend. Pending publication, receipt acceptance, end evidence
and controls must commit with their corresponding state transitions. Never hold a
SQLite transaction across a network await. A store returning failure or throwing after
commit leaves an uncertain outcome to reconcile; it does not prove rollback.

**2.3 — Implement creation, reopening and status without Telegram.** Distinguish
explicit new submission from retry; unknown retry never creates, and fresh/successor
creation requires affirmative predecessor context [folded: Stage 1 critic Risk 1,
robust]. Matching retried
creation returns its existing intent and original dates. Reusing its identity with
changed settings conflicts. A new identical job needs new intent and the expected
predecessor context. Reopening a known run requires it to exist; absence, corruption
or backend failure cannot call the create path. Fresh first use is explicit. Keep
schema/store creation separate from pretending a missing known run never existed.

**2.4 — Test identity and storage failure windows.** Exercise real SQLite reopen,
CAS conflict, committed-but-unanswered creation, duplicate creation, changed-input
conflict, missing file/row, custom async backend failures and malformed state. Verify
that legacy daily v1/window v2 records retain their exact formats and cannot be read
as lifecycle records. Test old creation requests against later generations before
and after historical recognition metadata has been retired.

Build the opt-in Gate A harness alongside these tests. It loads dates/origin from
the actual newly saved run record and supplies them to the existing raw batch API.
It does not implement Stage 3's pending/acknowledgment behavior in a throwaway clone.

### Output

New state/types modules and a storage-backed internal engine supporting safe
creation/reopen/status. Tests in the state suite exercise actual persistence.

### Exit check

Create a relative-window run, lose the reply, reopen in another process and retry:
the same run and dates return. Wrong/stale context and missing known state cannot
create another run or alter existing progress.

### Safe in nature

False — this introduces durable state and retry authority, though old APIs remain
unwired to the new engine. Mistakes here can lose or misattribute later progress.

### Peripheral concepts

SQLiteSyncStore, opaque custom backends, schema versions, history-window validation.

### Hardness Lvl

5/5. This is the prerequisite on which all later guarantees depend.

## Gate A — Validate the foundations before Stage 3

**Premises under test:** saved intent can drive the existing real source reader;
canonical identity, dates, ID continuation and end signals mean what the new engine
will rely on; creation and reopening are durable.

1. Use the selected real account/group and independently recorded fixture. Read a
   bounded explicit window with enough known messages to cross a real SDK history-page
   boundary and at least two caller-batch boundaries across the planned cases. Compare
   IDs and dates against the expected set, checking both
   included and excluded boundary messages and any available timestamp ties/gaps.
   Required edge cases absent from the fixture remain unverified until supplied;
   deterministic coverage is recorded separately.
2. Create a relative-window run, restart the process, reopen and retry creation.
   Use its saved dates for real reads. Confirm the run and dates remain identical
   and the selected visible fixture remains consistent with those boundaries.
3. Check empty-window and exact-full-batch follow-up behavior against a known fixture,
   plus the selected media mode. Preserve evidence of account-dependent visibility;
   do not infer a complete archive from a server result alone.
4. Pair those reads with actual SQLite commit/reopen/uncertain-create tests from
   Stage 2. Keep live source compatibility and local atomicity results separate.
   Record actual request/turn boundaries and characterize cancellation of a raw read
   with a controlled local interruption. Identify any SDK behavior that contradicts
   the proposed attempt boundary before later stages assume it away.

**Pass condition:** every foundational assumption has evidence, the expected fixture
is recovered without unexplained omissions, and retry/restart preserves intent.
**Not yet claimed:** new pending delivery, completion, pacing or control correctness.
**Output:** `validation/gate-a.md` and updated `assumptions.md`.
**Failure action:** stop before Stage 3; repair or revise the foundation and repeat Gate A.

## Stage 3 — Prepare, retain and acknowledge one batch

### Proposed changes

**3.1 — Admit and record one source attempt.** Require the run plus expected accepted
position and control revision; stale contexts refuse before source work [folded:
Stage 1 critic Risk 2, robust]. Before invoking Telegram, durably
record the attempt identity, run, cursor and policy used. Refuse overlapping
preparation and unresolved attempts. A failed/uncertain admission write must not
send a source request. Call `get_message_batch` directly with the frozen query;
do not wrap `sync_group`, whose `None` result loses empty end evidence. A successful
attempt records its result against that same run and attempt.

**3.2 — Publish exact pending data before returning it.** Validate source, cursor,
media mode and dates using existing batch semantics. Publish the complete pending
batch together with the attempt outcome. Repeated preparation loads that batch
without Telegram, budget consumption or a new pacing interval. Verify pending media
from its configured local root; missing/corrupt artifacts block replay rather than
causing a replacement download. Keep receipt context outside MessageBatch v1 so its
canonical payload/hash remains compatible.

**3.3 — Settle an acknowledgment atomically.** Match the complete delivery context;
advance only to the saved batch's next cursor and clear pending in one conditional
write. Repeat recognized acknowledgments without a second effect. Wrong-run, wrong-
collection, stale and unknown receipts refuse without mutation, even if two runs
produced the same batch hash. A valid receiver acceptance can settle an exact pending
obligation even if its already-delivered local files subsequently disappeared.
Acknowledgment is the caller's durability assertion, not a file-presence check.

**3.4 — Preserve prefixes and original errors.** Save an ordinary failure's completely
prepared prefix before re-raising the source error. If saving it fails, expose a
local persistence error with the original read failure separately available, following
the existing `read_error` pattern. Interrupted prefixes never establish exhaustion.
Cancellation is propagated explicitly across the project's supported Python behavior;
it does not acknowledge or invent a successfully saved prefix. If settlement cannot
be confirmed, leave the attempt requiring reconciliation rather than reading again.

### Output

Internal prepare/replay/acknowledge behavior and delivery tests using the actual
batch engine, Telethon 1.45.0 iterator, SQLite and artifact verification.

### Exit check

Prepare, restart, replay and acknowledge the exact batch. A lost destination reply
can cause repeated delivery but not a skipped cursor. Failed media replay and wrong
receipts preserve pending state. Local failures do not emit Telegram health verdicts.

### Safe in nature

False — this handles source reads, delivery custody and accepted progress.

### Peripheral concepts

MessageBatch v1, media blobs, partial_result, error provenance, existing health wrapper.

### Hardness Lvl

5/5. Persisted observation, external delivery and acknowledgment are separate failure points.

## Stage 4 — Make completion and uncertain storage outcomes truthful

### Proposed changes

**4.1 — Save source exhaustion independently of pending data.** Use the validated raw
batch's `stop_reason`. An empty successful `end` records end evidence without a fake
pending batch. A nonempty `end` records the pending batch and exhaustion together.
A `limit` result does not establish exhaustion; another admitted read may be needed.
No exception, short interrupted prefix, absent account or missing state means `end`.

**4.2 — Complete in the same transition that satisfies the last obligation.** Empty
exhaustion can complete on attempt settlement. A final pending batch completes only
when its acknowledgment commits. Require no unresolved source attempt and no prior
cancellation/abandonment. Record the declared origin in the completion view; imported
progress never becomes evidence that this run read the skipped prefix. Reopening a
completed run returns the saved result without spending another Telegram read.

**4.3 — Reconcile uncertain writes from authoritative state.** Re-load after an
ambiguous create, publish, ack, completion or control result. Verify whether the
addressed effect committed before retrying. Handle backend outage as unknown state.
Use subprocess exits around actual SQLite commit boundaries, including final ack
and empty completion, rather than only an in-memory mock. If the record still names
an unfinished source attempt, prohibit another read; Stage 5 supplies explicit recovery.

### Output

Durable completion transitions, qualified coverage in status, and real commit-boundary
recovery tests. Completed jobs stop permanently unless the caller creates new intent.

### Exit check

Both empty and nonempty final runs remain completed after restart. A failed next
read following a full batch remains incomplete. An ack committed before process
exit is applied once; one that did not commit leaves the same pending obligation.

### Safe in nature

False — an incorrect terminal transition could permanently skip owed work.

### Peripheral concepts

End/limit/interrupted semantics, imported progress, CAS recovery, receiver acknowledgment.

### Hardness Lvl

4/5. Small transition surface, strict consequences.

## Gate B — Validate delivery, completion and restart before Stage 5

**Premises under test:** real prepared observations survive delivery uncertainty;
acknowledgments advance only their own run; completion represents exhausted scope
plus accepted output.

1. Read the known fixture through the new internal backfill engine into a real local
   durable receiver. Compare the final accepted message set and selected media hashes
   with the fixture. Use sequential reads from independent test collections with
   overlapping windows to check receiver deduplication; do not require the Stage 6
   successor/abandonment controls at this gate.
2. Terminate/restart after pending publication, after receiver commit but before ack,
   and immediately before/after the actual ack commit. Verify exact pending replay,
   no source read during replay, no skipped cursor and no repeated destination effect.
   Use real data and storage with explicitly injected local interruption boundaries.
3. Exercise empty completion, nonempty final delivery, an exact full final batch,
   imported progress, wrong-run receipts and completed-run reopen. Completion must
   remain false while final delivery is owed and must persist once established.
4. Interrupt or refuse a read using a controlled failure or small local budget,
   including a saved prefix. It must not become end-of-history. Where an unfinished
   source attempt remains, assert the recovery-required state; recovery is tested at
   Gate C once Stage 5 exists. Do not reset state to make this gate finish.

**Pass condition:** source/store/receiver evidence agrees on the expected data and
accepted cursor, with correct completion and harmless repeated/wrong acknowledgments.
**Not yet claimed:** durable run pacing or pause/cancel race handling. The harness
continues to space live reads externally.
**Output:** `validation/gate-b.md` and updated `assumptions.md`.
**Failure action:** stop before Stage 5; reopen Gate A too if source assumptions changed.

## Stage 5 — Persist pacing and recover interrupted attempts

### Proposed changes

**5.1 — Save attempt-based pacing and expose readiness.** Store the selected policy
and known post-attempt deadline with settlement, including failures/cancellation
that may have reached Telegram. Keep state operations, pending replay and receipts
independent of that deadline. A call made too early reports the wait without sleeping
through it or making a source call. Return control between bounded turns so the caller
can prioritize daily work. A bounded message count is not a fixed network-duration
limit; existing SDK retry/flood behavior remains inside a turn.

**5.2 — Combine local timing with existing source restrictions.** Preserve budget
refusals, returned retry hints and actionable source failures. Keep account-specific
observations tied to the actual failure's context and describe them as observations,
not current global health. The existing guarded client remains the authority for
fresh account identity and budget admission at send time. Never reserve allowance
by trusting a status snapshot, reset the budget ledger, or infer an account from the
stale health cache. Unknown/indefinite restrictions are not zero-second waits.
Expiry of a hint permits re-evaluation; it does not guarantee a successful read.

**5.3 — Add explicit recovery of unknown attempts.** First reload and reconcile any
committed outcome. When an attempt remains uncertain, require evidence from the caller's
single-reader ownership that the earlier worker has stopped. Refuse recovery while
the same engine still has that attempt running. Record one conservative full pacing
interval from accepted recovery when its end is unknown. Retry of that recovery
command preserves the saved wait. Do not infer worker death from elapsed time or add
a distributed lease mechanism. This is sequential recovery, not competing-worker safety.

**5.4 — Test clocks and every pacing anchor.** Inject UTC and monotonic clocks for
tests; do not persist a process-relative monotonic timestamp as portable time.
Preserve known deadlines over restart, detect inconsistent/backward evidence and
report uncertain eligibility where it cannot be established. Document the trusted
UTC assumption across process lifetimes: arbitrary undetectable clock jumps cannot
be solved by this library. Test early/late acknowledgment, failed attempt, zero
explicit interval, budget prefix, budget recovery, unknown attempt and repeated recovery.

### Output

A restart-safe read-admission layer, explicit recovery operation and deterministic
clock/budget tests. No internal standing loop or automatic wake-up promise.

### Exit check

An attempt ending at 10:00 with a chosen four-minute interval cannot begin another
before 10:04. Ack at 10:01 or 10:10 does not move that deadline. Restart preserves it.
Unknown attempts remain blocked until recovery establishes one new wait; repeated
status or recovery does not continually extend it. Receipts can settle throughout.

### Safe in nature

False — this changes when network activity is admitted and what recovery permits.

### Peripheral concepts

ReadBudget, BudgetClientMixin, SDK retries/waits, trustworthy time, source ownership.

### Hardness Lvl

5/5. Timing must survive uncertainty without claiming account-wide rest or perfect clocks.

## Stage 6 — Preserve operator intent through concurrent settlement

### Proposed changes

**6.1 — Implement pause/resume as accepted control commands.** Persist command identity
and expected control revision. Known duplicates report their recorded effect and
current attributable state; stale unaccepted commands conflict. Pause denies new
source attempts while allowing an already-admitted attempt, replay and acknowledgments
to settle. Resume grants only operator permission; pacing, pending work and source
restrictions still apply. Mutable controls have their own revision so an ordinary ack
need not invalidate a legitimate control solely because delivery progressed.

**6.2 — Implement cancellation and terminal ordering.** Cancellation prevents future
reads for that intent. Preserve outstanding activity and delivery facts. If completion
committed first, cancellation reports the completed outcome. If cancellation committed
first, a final acknowledgment records delivery without relabeling it completed.
Do not use client clocks or callback response arrival to select the winner.

**6.3 — Reconcile a late attempt result with newer controls.** A prepare call may await
Telegram while pause/cancel updates the same record. Reload and validate the same
run, attempt, cursor and pending obligation before publishing its result; preserve
the newer control decision. Do not blindly retry an old whole-record write, drop a
usable result merely because control changed, or start another fetch to resolve CAS
failure. Keep result settlement narrowly scoped and leave irreconcilable outcomes
visible. No lock spans the network wait and prevents control commands from recording.

**6.4 — Add explicit abandonment and successor creation.** Permit retirement of owed
work only as an explicit operation that ends its delivery guarantee; record an
incomplete/abandoned delivery outcome and never advance the accepted cursor as if
delivered. Preserve an already accepted terminal cancellation while marking its
remaining delivery abandoned; do not rewrite it as a different terminal outcome.
A successor waits for old activity to stop and owed work to settle or be explicitly
abandoned. Bounded historical receipts can later become unknown and harmlessly refuse;
active pending identity cannot expire. Blob garbage collection and automatic timeout
cleanup are outside this delivery.

### Output

Control operations and tests for delayed commands, in-flight reads, terminal races,
abandonment, new generations and historical receipt retirement.

### Exit check

Use barriers around actual awaits to exercise pause-before-result, cancel-before-ack,
ack-before-cancel, two conflicting controls, stale resume and old receipt/new run with
identical bytes. Each history preserves the accepted terminal/control outcome and
never mutates another run's progress.

### Safe in nature

False — even one source reader can have simultaneous controls and delayed receipts.

### Peripheral concepts

CAS reconciliation, control revisions, terminal outcomes, artifact custody, command retention.

### Hardness Lvl

5/5. This is the main temporal-race stage, not a cosmetic status feature.

## Gate C — Validate pacing, recovery and controls before Stage 7

**Premises under test:** saved timing limits source activity; actual SDK behavior
fits the attempt boundary; controls and delayed results preserve accepted intent.

1. Use real reads and measured request times to check attempt spacing across process
   restart, early/late acknowledgments and failed attempts. Distinguish source turns
   from SDK requests/retries; record observed SDK waits and cancellation behavior.
   Run fake-clock edge cases separately without changing the host clock.
2. Exhaust a small test allowance through ordinary bounded reads using the actual
   budget adapter. Verify no disallowed message request is sent, a completed prefix
   remains deliverable, and source eligibility is rechecked after an explicit increase
   to the dedicated test allowance while preserving its charges and keeping any
   existing authoritative account ledger in force. A test cap may only restrict
   further, never bypass a shared account's budget. Test rolling-expiry
   boundaries deterministically; label a policy increase separately from natural expiry.
   Do not provoke Telegram flood limits or bans to manufacture a test result.
3. Kill the test worker after possible source activity but before durable settlement.
   Confirm it has exited, then recover through the real recovery operation. Verify
   the conservative wait, preserved obligations and stable deadline after a lost
   recovery response. An unresolved earlier worker must not be treated as stopped.
4. Use test-only barriers around real read/settlement and receiver operations to
   force pause-before-result, cancel-before-ack, ack-before-cancel, stale resume and
   two conflicting controls. Test late receipts after a successor has been created.
   Report exactly which local ordering was forced; do not attribute it to Telegram.

**Pass condition:** recorded source activity respects the applicable gates, receipts
still settle while reading is blocked, and every forced ordering retains the correct
control/terminal outcome. Unknown outcomes remain visible instead of silently retrying.
**Output:** `validation/gate-c.md` and updated `assumptions.md`.
**Failure action:** stop before Stage 7 and revise the affected state/timing assumptions;
reopen Gate B if delivery or completion semantics changed.

## Stage 7 — Expose the lifecycle through a small public API

### Proposed changes

**7.1 — Wire additive facade operations and exports.** Add optional `backfill_store`
and the reviewed methods to `TgData`. Keep existing daily/window calls and batch v1
unchanged. Only actual `get_message_batch` work enters the existing Telegram health
context. Create/status/control/ack/replay and local storage failures must neither
report Telegram failures nor clear prior Telegram health problems.

**7.2 — Publish honest, content-free status.** Expose scope/origin, run identity,
control revision, accepted progress, pending metadata, source exhaustion, unresolved
activity, terminal outcome, waits and failure categories together. Include timestamps
as evidence/estimates, not guaranteed execution times or invented percentages. Status
is storage-only and does not connect to Telegram to refresh account identity.

**7.3 — Document and demonstrate the caller boundary.** Add `docs/backfill_runs.md`,
README/smoke-test README entries and an offline `examples/backfill_runs.py`. Show fresh
creation, saved run references, restart, replay, durable receiver acceptance, ack,
pause/cancel and completion. Use a real local durable receiver in the demo and simulate
a lost acknowledgment. Show daily and backfill stores separately, with the caller
choosing one eligible turn at a time. Explain that the application can reuse a
logical database namespace rather than a dedicated file. State bounded historical
retry recognition and explicit abandonment without recommending auto-expiry.

### Output

Publicly usable lifecycle API, documented storage/receiver contract and a repeatable
offline example that survives a restart and repeated delivery.

### Exit check

The example delivers the expected unique records, survives the chosen failure and
finishes only after durable acceptance. Public status/ack/control/replay tests forbid
network access and contain no message content or credentials in status/logs.

### Safe in nature

False — the new API becomes reachable through the existing public class.

### Peripheral concepts

TgData compatibility, exports, public error/status contracts, receiver deduplication.

### Hardness Lvl

3/5 once the internal guarantees pass. Avoid moving unresolved semantics into examples.

## Stage 8 — Verify the complete behavior and prepare review

### Proposed changes

**8.1 — Run the combined failure matrix.** Combine the three new suites with real
SQLite subprocess exits and Telethon 1.45.0's iterator/budget adapter using synthetic
transport and blocked external sockets. Cover before/after durable attempt admission,
pending publication, acknowledgment, exhaustion, controls, cancellation, recovery and
successor creation. Include commit-then-error, commit-then-cancellation, cleanup failure,
missing/corrupt artifacts, missing known state, and expired historical recognition.
Validate observable data/requests/store effects rather than tests that mirror helpers.

**8.2 — Run regressions and record their limits.** Compile changed files; retain the
package's declared Python syntax compatibility without claiming an untested interpreter
runtime. Run tests 23, 22, 19, 18, 17, 16, 15, 14, 13 and 12 in their documented offline
forms, plus the two explicitly awaited offline test 11 helpers and both offline examples.
Use the existing [fixed-window verification commands](https://github.com/karaposu/tgdata/blob/e9b5154/devdocs/work/18-daily-group-continuation/fixed-window/verification.md#reproduction)
as the starting point. Do not run mixed/live legacy module entry points incidentally;
execute the explicit opt-in live gates with their selected fixtures and scope.
Record passes and skips separately, exact versions and remaining deployment assumptions.

**8.3 — Make one reviewable feature delivery.** Inspect the final diff against the
finding, description, plan and critique. When formal implementation is authorized,
commit product code/tests/public docs together and work-folder evidence separately,
following CONTRIBUTING. Then perform the requested merge-check/PR/fresh-critic gates;
merge still needs explicit go-ahead. Application adoption separately requires its
chosen pacing and durable receiver acceptance point. Offline results alone do not
finish this delivery: Gate D and all preceding live gates are required before it
is ready for feature review. The gate uses the actual state backend chosen for this
delivery; a different custom deployment backend needs its own equivalent acceptance.

### Output

Verification report, complete source/contract traceability, a clean scoped diff and
the appropriate implementation checkpoints. PR publication or merge is not claimed
by writing this plan.

### Exit check

No unexplained High/Medium finding, failing required check, false completion, cross-run
mutation or omitted fault boundary remains. Gate D and any reopened earlier gates
have passed. Any remaining limitation is a named scope or deployment assumption,
not a passing-test claim about an untested system.

### Safe in nature

False — live validation performs bounded reads through a real account as well as
local failure tests. Publication and merge remain separate actions under their gates.

### Peripheral concepts

Regression evidence, fault injection, repository review process, deployment acceptance.

### Hardness Lvl

4/5. Integration failures can occur between individually passing stages.

## Gate D — Validate the complete public flow before review readiness

**Premises under test:** the public API preserves the verified internal guarantees
and the caller can use them across separate sessions with its chosen durable receiver.

1. Run a complete bounded backfill through the public API and selected real Telegram
   account/group, state backend and durable receiver. Reopen in another process after
   an actual pacing wait and saved progress; include delayed delivery and a restart.
   Compare accepted IDs/media and the final scope-qualified result with the fixture.
2. Exercise daily continuation alongside historical work with independent state,
   sequentially scheduling the reader. Confirm that the caller can give daily work a
   turn, and neither collection advances the other's progress. No competing readers
   or automatic failover are introduced by this test.
3. Verify public status/control/ack/replay cause no Telegram requests and no false
   health recovery. Attribute requests to the operation under test so unrelated SDK
   housekeeping is not misclassified. Re-run representative Gate B/C fault histories through the facade
   and all affected regressions. Inspect the combined request/store/receiver trace.
4. Review the assumption record: every critical premise has evidence for the released
   code, any earlier gate invalidated by subsequent changes has been rerun, and no
   required case is skipped, blocked or silently replaced by synthetic evidence.

**Pass condition:** the complete caller flow, critical assumptions and regressions
pass on the recorded revision. Preserve limits of the fixture/account/backend; do
not claim that a bounded live run proves all Telegram accounts or future conditions.
**Output:** `validation/gate-d.md`, the final assumption record and verification report.
**Failure action:** stop release/review readiness, return to the affected stage and
repeat the invalidated gates before merge-check/PR delivery.

## Failure coverage that must remain visible

| Required history | Main stage(s) | Observable proof |
|---|---|---|
| Creation committed; reply lost; retry tomorrow | 2, 8 | Same run and original dates; no new intent |
| Old creation command after a successor exists | 2, 6 | Existing generation unchanged; recognized old result or conflict |
| Same bytes prepared for different windows | 3, 6 | Old run's receipt cannot acknowledge current pending data |
| Destination committed; acknowledgment lost | 3, 7 | Exact batch replay; receiver produces no duplicate effect |
| Ack committed; store then raised or process exited | 4, 8 | Reload shows one accepted advancement |
| Successful empty scan | 4 | Completion evidence survives restart; no fake upload |
| Full batch followed by quota failure | 4, 5 | Incomplete with source stop, not inferred end |
| Failure after a usable prefix | 3, 5 | Saved prefix remains deliverable; original failure remains visible |
| Pause while an attempt is awaiting Telegram | 6 | Result saved; pause retained; no second attempt |
| Cancel versus final acknowledgment, both orders | 6 | First accepted terminal outcome preserved |
| Stale or repeated resume after a newer pause | 6 | No reapplication or silent overwrite |
| Restart during a known wait | 5 | Same deadline, no premature request |
| Crash after possible send but before settlement | 5 | Explicit recovery and one conservative wait |
| Recovery committed but its response was lost | 5 | Retried recovery does not restart the timer |
| Pending data outlives historical receipt retention | 6 | Live receipt still settles its original obligation |
| Missing blob after receiver already accepted it | 3 | Replay fails; valid scoped receipt can still settle |
| Missing/corrupt known-run state | 2, 4 | No reset, bootstrap, changed window or Telegram call |
| Imported midpoint of the date window | 2, 4 | Completion qualifies the imported prefix |
| Local file/storage error or offline status/ack | 3, 7 | No false Telegram health event or recovery |
| Daily continuation used alongside historical runs | 7, 8 | Independent progress; existing daily behavior unchanged |

## Scope that stays outside these stages

No competing machines/readers, old-edit/deletion reconciliation, automatic account
routing/joining, account-wide rest scheduler, dashboard, worker daemon, archive-folder
scanning, ScrapeOps code changes, #7 resumption or `duncan` changes. Reuse ScrapeOps's
operator vocabulary and pacing example; do not copy its whole-loop blocking or
normal-return-means-done behavior.

## Plan completion and next handoff

This overall document remains a staged runtime plan. Stage 1 established the contract;
Stage 2 built and locally verified the persistence foundation and live instrument.
Their separate implementation/verification reports preserve each checkpoint's evidence.
The later [Gate A](validation/gate-a.md) passed real-source validation. Next is Stage 3.
Stages 3–8 and Gates B–D remain pending. No protected-branch merge is implied here.
