---
model: gpt-6-astra
effort: max
revision: 2
---
# Stage 2 — durable run state and Gate A instrument

**Critic folded:** 2026-10-07 — 2 mitigations (4 steps changed, 0 added).

Inputs: [desc.md](desc.md), Stage 1 [contract](../contract.md),
[staged plan](../staged-plan.md), [live-validation specification](../live-validation.md).
Product base: feature-only prerequisite merge `5d0789e`; target Telethon 1.45.0.
No PARKED description or rejected PR-critic history exists for this stage.

### What is the task

Implement immutable start/reference/status values, strict lifecycle state persistence
and storage-only creation/reopening. Reuse the existing opaque CAS backend. Build an
opt-in live-source instrument for Gate A, verify the stage locally, and run the gate
only when the actual selected existing-group/read-only inputs are available.

### Huge Hard Blockers

#### Planning Blockers

None identified. Stage 1 fixes the relevant meanings and the real backend/batch/SDK
interfaces are available. The record/validation choices below are implementation
choices inside that contract. The instrument must expose incomplete evidence rather
than presume a real fixture or silently choose an account.

#### Execution Blockers

- **What must happen:** selected account/config label, existing canonical group,
  independently complete closed-interval oracle, source request/slot/elapsed limits,
  pacing and authoritative budget context must be supplied/qualified.
  **Who:** maintainer identifies resources; implementer validates the fixture.
  **Blocks:** Step 6 actual Gate A execution and any subsequent Stage 3.
  **Status:** OPEN; asynchronously requested. Steps 1–5 remain executable.
- #18 runtime prerequisite is **DONE on this feature branch**, merge `5d0789e` only.
  Its separate review/merge into dev is not claimed or performed by this stage.

### How this implementation moves toward desired state

Build a separate lifecycle record over the same exact-text CAS protocol, with no
legacy migration. The only new state-mutating operation is start. Future pending,
end, attempt, control and pacing facts are validated snapshots; their transition
operations do not exist yet. The Gate A instrument reads frozen query values from
that actual record and calls the existing raw reader, keeping its diagnostic scan
cursor separate from acknowledged lifecycle progress.

### High-Level Summary

| Step | Description | Output |
|---|---|---|
| 1 | Types, strict record and nested invariants | backfill.py, backfill_state.py |
| 2 | Storage-only start/status engine | backfill_engine.py |
| 3 | Real persistence and refusal tests | test_24_backfill_state.py |
| 4 | Opt-in bounded read-only Gate A tool | live_probe.py plus offline tool checks |
| 5 | Docs, full offline verification and checkpoints | docs/backfill_state.md, reports, code/docs commits |
| 6 | Execute/review Gate A when inputs exist | validation/gate-a.md; PASS or explicit blocked/inconclusive/fail |

## Wire record and interface decisions

New modules are imported directly for this staged delivery; no new TgData constructor,
facade methods or root exports before Stage 7. Keep Python 3.7-compatible syntax.

`backfill.py` defines immutable `BackfillRunRef`, `BackfillStartRequest`,
`BackfillStatus`, `BackfillStartResult` and local error categories: configuration,
conflict, unknown run/command, invalid state and backend/storage uncertainty.
IDs use canonical decimal strings in portable dictionaries; object attributes use
exact integers. Identity strings obey the Stage 1 UTF-8/length/whitespace/control rule.
Requests normalize integers, UTC dates and finite nonnegative pacing seconds; require
explicit expected_predecessor (None for affirmative first use). Exactly one fixed
explicit window or positive last_days is required. Origin/media/limit rules stay fixed.
A pacing duration must fit a supported timedelta and a UTC deadline at initial creation;
recognized retry does not consult a new clock to revalidate an accepted intent.

`BackfillEngine(store, collection_id, *, clock=UTC-now)` has only async
`start(request, *, submission)` and `status(run_ref)` in Stage 2. No read callable,
Telegram/config/session object, source preparation, acknowledgment or control operation
is accepted by this engine yet. The local clock is injectable for tests.

The versioned opaque aggregate has exact keys:
`schema="tgdata.backfill-state"`, `version=1`, `collection_id`, `chat_id`,
`state_revision`, `current`, `previous` (null or the immediate predecessor record).
One CAS replaces the entire aggregate. Retained previous records must be terminal,
quiescent and have no pending obligation; no payload history grows unboundedly.

Each run record has exact keys:
`ref`, `request`, `created_at`, `window`, `after_id`, `control_revision`,
`operator_intent`, `terminal_outcome`, `pending`, `last_ack`, `exhaustion`, `attempt`,
`pacing`, `last_control`, `last_recovery`, `last_failure`, `abandoned`.

- `ref` is the full RunRef. `request` is the canonical original StartRequest including
  input window form and expected predecessor; `window` is resolved fixed dates.
- `pending` is null or a validated nonempty MessageBatch v1 from this group's window,
  input cursor and media mode. Its payload remains unchanged.
- `last_ack`: batch_id, next_after_id, observed_at; or null.
- `exhaustion`: attempt_id, after_id, next_after_id, observed_at; or null.
- `attempt`: attempt_id, after_id, control_revision, admitted_at; or null.
- `pacing`: attempt_id, ended_at (nullable), not_before (nullable), clock_uncertain;
  or null. Known timing has a representable deadline; unknown timing remains explicit.
- `last_control`: command_id, action, expected_revision, accepted_revision,
  state_revision; or null. Actions map consistently to operator/terminal intent.
- `last_recovery`: command_id, attempt_id, expected_control_revision, state_revision,
  recovered_at; or null. It must match the saved recovered-attempt/pacing context.
- `last_failure`: category, error_type, observed_at, retry_at (nullable), account_id
  (nullable); or null. No exception text, credentials or message content.
- `abandoned`: batch_id (nullable if no batch was owed), next_after_id, observed_at;
  or null. It cannot advance accepted position or rewrite an earlier cancellation.

Nested dictionaries use exact keys/types. Encode dates canonically in UTC; integer
IDs/revisions stay canonical decimal strings. No duplicate/unknown JSON keys, nonfinite
numbers or invalid UTF-8. Load does not repair/normalize invalid state into validity.
The constructor owns its data through canonical encoding, not caller-mutable dicts.

Cross-field checks include request/ref/key namespace agreement, successive generation/
predecessor identity, original-input/window consistency, accepted-position/latest-ack
agreement, pending cursor/window/hash/mode, end evidence versus pending stop reason,
unresolved attempt exclusivity, terminal/control/abandonment compatibility, bounded
recognition and pacing/recovery context. Timestamps are evidence, not command order;
do not reject acknowledgment merely because an observed wall clock moved backwards.
A saved-state validator cannot authenticate a fabricated history; the backend remains
trusted to accept transitions only from its authorized writers.

## Step 1 — Implement values and the strict codec

[folded: Risk 2, robust]

Preserve canonical requested pacing seconds, but round its canonical decimal value
up to whole microseconds when deriving a minimum UTC duration. Reuse this helper in
creation representability and known pacing validation. Refuse overflow; sanitize clock
provider failures as local errors and propagate cancellation.

### Proposed changes

Create `tgdata/backfill.py` and `tgdata/backfill_state.py`. Reuse history-window and
MessageBatch validation, with local sanitized error boundaries. Public inputs fail as
configuration errors; corrupt saved state fails as invalid state. Preserve cancellation
separately from ordinary exceptions. Never log saved JSON or backend exception text.

Use immutable references/requests/results and a content-free immutable status snapshot.
Status includes actual scope, cursor/pending metadata, state/control revisions, terminal/
operator facts, unresolved attempt ID, pacing uncertainty/deadline, receipt and observed
failure metadata. It does not advertise ready-to-read, enforce timers or claim a source
outcome in this stage. Prior status is marked history-limited and addressed to its own ref.

Implement canonical request dictionary conversion and strict reverse conversion for
fixtures/tooling. Scalar precision and canonical serialization must round-trip. The
state validates both current and retained previous records and maps them to status.
New creation initializes all delivery/source/control/timing facts without invented
acceptance or exhaustion. Future snapshot fixtures are validation tests, not implementations
of those later operations; no generic arbitrary mutation API is exposed.

### Output

Strict versioned state and reusable typed values with no new network-facing behavior.

### Safe in nature

False — durable identity and corrupt-state refusal govern future progress.

### Peripheral concepts

HistoryWindow, MessageBatch v1, local error provenance, JSON precision, Python syntax floor.

### Hardness Lvl

5/5.

## Step 2 — Implement atomic start and known-run status

[folded: Risk 1, robust] [folded: Risk 2, robust]

Add keyword-only `create=True` to SQLiteSyncStore. The default keeps its existing
behavior. With `create=False`, the constructor uses the current mode=rw/schema-check
path without creating a file or schema, including when a file disappears before open.
Subsequent load/CAS already use mode=rw. No SQL schema or backend protocol change.
Use the upward-rounded duration helper for initial deadline representability.

### Proposed changes

Create `tgdata/backfill_engine.py`. Validate the configured namespace and async load/CAS
interface; sanitize backend failures by operation/error type, suppress unrelated RPC
exception context and propagate asyncio cancellation even after an uncertain commit.
Validate all loaded rows before returning status or trying a write. CAS compares the
exact loaded text, not a re-encoded approximation.

Start validates request/submission and namespace, then loads before reading time.
Search current and retained predecessor creation identities. A recognized identical
request returns BackfillStartResult(applied=False, status=addressed snapshot), with no
clock/read/write; changed input conflicts. Unknown retry raises UnknownCommand even
when absent. New first use requires absence plus expected_predecessor=None. New successor
requires exact current predecessor, terminal/quiescent/no owed output, and safe generation/
state-revision increments. Reject active, stale, corrupt or exhausted counters before write.

For accepted new intent, observe UTC once, resolve relative dates once or check explicit
end <= creation time, validate pacing representability, construct initial record, and
commit a single CAS. Keep the prior terminal record as bounded recognition. Successful
result has applied=True; false CAS conflicts; ambiguous failure remains visible. Caller
can retry/reload the exact identity, not silently create another run. No automatic loop
that rebases a stale start onto a newer predecessor.

Status accepts only a complete matching RunRef, returns current or retained prior
status, and raises UnknownRun for missing/pruned context. It is storage-only and never
creates a row or reads the clock. Preserve the existing daily engine/store behavior.

### Output

Real start/reopen/retry/status behavior through SQLite or the same custom async protocol.

### Safe in nature

False — this is the stage's actual durable mutation boundary.

### Peripheral concepts

Atomic replacement, uncertain commits, bounded retention, state namespace isolation.

### Hardness Lvl

5/5.

## Step 3 — Test persistence, identity and malformed state

[folded: Risk 1, robust] [folded: Risk 2, robust]

Add tests for existing-only open of missing/deleted/schema-less stores and unchanged
default provisioning. Cover positive sub-/fractional-microsecond duration ceilings,
zero, overflow, and sanitized clock-provider failures.

### Proposed changes

Add `tgdata/smoke_tests/test_24_backfill_state.py`, using temporary SQLite and sockets
forbidden. Test public input/serialization, explicit/relative creation, changed-input
conflicts, known retry with forbidden clock, unknown retry/known absence, prior/current
recognition, stale successors, counter bounds and incompatible daily/window state.

Exercise actual process exits immediately before and after SQLite commit, plus an actual
commit whose response/cleanup raises. After restart assert exact stored state and retry
outcome. Add custom async backend concurrency/return-type/failure/cancellation cases;
fakes demonstrate the backend contract, not durability. Use deliberately well-formed
terminal/future records as codec/successor fixtures and label those limits.

Cover nested pending/outside-window/wrong-source values, contradictory progress/end/
attempt/control/abandonment/pacing, unknown keys/versions, duplicate JSON keys, nonfinite
values and mutable input/status aliasing. Verify local errors never inherit Telegram
health verdicts or expose a sentinel secret from backend exception text. Ensure no
new public facade/source/ack/control method exists by accident.

### Output

An offline suite that runs the actual new engine/codec and real persistent storage.

### Safe in nature

True — tests use disposable data and forbid external network.

### Peripheral concepts

Subprocess crash boundaries, SQLite durability, custom async store contracts, privacy.

### Hardness Lvl

4/5.

## Step 4 — Build the opt-in Gate A probe

[folded: Risk 1, robust]

Open known state using SQLiteSyncStore(create=False), not a separate path-exists check
followed by its default constructor. An absent store is a non-mutating preflight failure.

### Proposed changes

Create `devdocs/work/19-backfill-run-lifecycle/live_probe.py` and a documented manifest
example/schema. Its default preflight/help path is offline. Live mode must be explicit
and requires selected config/group, existing known run/reference, independent expected
IDs/dates with provenance/completeness, selected media expectations and bounded request/
slot/elapsed limits plus external spacing. Require a pre-existing authoritative budget
ledger/account identity; never configure/reset a production policy implicitly.

Load the existing state file without creating a missing one, use BackfillEngine.status
and recognized start retry with a forbidden clock, and compare the saved query/origin
with the frozen oracle. Do not auto-create or rewrite the oracle/state during live reads.
The caller can prepare a run locally first, then independently enumerate that exact scope.

Actual source reads use TgData/get_message_batch with interactive_login=False, one
connection, the selected budget and stored bounds. A diagnostic scan cursor advances
only inside the probe; the lifecycle cursor stays unchanged (Stage 3/ack do not exist).
Measure SDK sends/pages/retries via an instance-scoped sender wrapper, preserving the
actual client/budget path. Enforce selected-group history reads, bounded requested slots,
read-only RPC allowlist and media allowance; unknown/unrelated requests refuse before
sending. Source reads/metadata limits are recorded separately from MTProto housekeeping.
Do not bypass a configured proxy, budget, access failure or cached-entity requirement.

Compare IDs/dates and selected artifact hashes with the independent manifest, inspect
actual SDK page crossings and empty/end/limit observations, and produce sanitized JSON
observations. Persist no message bodies/credentials in reports. A successful individual
scan is not an automatic Gate A PASS; emit remaining coverage and require the complete
manual gate report with local persistence evidence. Test help/preflight/no-network,
wrong target/budget/version, write-RPC refusal, limits and oracle comparison offline
through real request types. Synthetic tests remain explicitly non-covering for live behavior.

### Output

A usable Gate A instrument with safe offline defaults and auditable bounded live mode.

### Safe in nature

False — explicitly opted-in execution can contact the selected real account/group.

### Peripheral concepts

Installed Telethon send/iterator seams, existing budget/proxy/auth, independent oracle.

### Hardness Lvl

5/5.

## Step 5 — Verify locally, document and checkpoint Stage 2

### Proposed changes

Add `docs/backfill_state.md` with internal staged usage and exact supported/deferred
operations, plus a smoke-test README entry. Update task README/assumptions/case evidence
only for observed Stage 2 behavior, preserving live requirements and UNRUN later stages.
Run compilation/Python 3.7 AST syntax check for changed Python files, new tests and tool
preflight checks, then the full supported offline suite including prerequisite tests22/23,
19 through12 and two awaited test11 helpers; run the existing offline daily example.
No 1.33.1 or live legacy entry point. Keep actual passes and explicit skips separate.

Record corrections/deviations and actual evidence. Commit product code/tests/public docs
separately from work-folder notes/tooling, then push only the #19 feature branch and
record the scoped Stage 2 status on #19. A live gate is not marked passed from local
checks. If Step 6 remains gated, leave an explicit gate record and resumable command/
input requirements; all executable local work is completed before stopping there.

### Output

Verified Stage 2 build with code, tests, docs, scoped commits and accurate evidence.

### Safe in nature

False — new persistent code ships on the feature branch; local tests remain isolated.

### Peripheral concepts

Supported offline suites, package imports, documentation, branch/issue checkpoints.

### Hardness Lvl

3/5.

## Step 6 — Execute and review Gate A when its inputs are ready

### Proposed changes

This step is gated by the declared live-resource condition. Reuse the user's existing-
group/read-only choice. Qualify the specific fixture/config and declared read allowance;
run the live probe plus required independent source cases and actual storage checks.
Record revision, input provenance, actual expected/observed outcomes and limitations in
`validation/gate-a.md`. Missing critical coverage is BLOCKED/INCONCLUSIVE, not PASS.

A contradicted premise stops and routes to the affected contract/plan; do not build
Stage 3 around it. No Stage 3 work in this run merely because the gate eventually passes.
If inputs remain unavailable, report completed Stage 2 work and exactly what is needed
for Gate A, preserving the pending user question and the unpassed gate.

### Output

Honest Gate A evidence/decision, or an explicit execution-blocked handoff.

### Safe in nature

False — real source reads are bounded but externally observable.

### Peripheral concepts

Live visibility, independent history, actual requests, prerequisite evidence, stop rule.

### Hardness Lvl

4/5.
