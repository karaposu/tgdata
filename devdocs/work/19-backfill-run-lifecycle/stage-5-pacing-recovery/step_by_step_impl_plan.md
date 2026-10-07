---
model: gpt-6-astra
effort: max
revision: 1
---
# Stage 5 — pacing and exact-attempt recovery

Baseline `246a187`, product `b1f6495`; [description](desc.md), [contract](../contract.md),
[Gate B PASS](../validation/gate-b.md). No PARKED or rejected PR-critic artifact exists.
SDK: Telethon 1.45.0 only. Stage 6/Gate C are outside this scoped implementation.

### What is the task

Replace the temporary positive-pause refusal with real bounded-turn pacing, and add
explicit recovery of one stopped source attempt. Preserve accepted data/intent and
make waiting/uncertainty observable without building a scheduler, another budget
system or a health/account ownership redesign.

### Huge Hard Blockers

#### Planning Blockers

None identified. Existing aggregate v1 already contains attempt, pacing and recovery
recognition fields. Gate B proved delivery/storage composition; installed SDK and
actual budget source identify the live admission owner. The clock/record composition
can be falsified cheaply with actual local primitives before building. Unimplemented
behavior still needs the dedicated tests, not just a handwritten state fixture.

#### Execution Blockers

None for this stage. No Telegram/account input is required. Mandatory Gate C requires
Stage 6 controls and its later live execution; this stage neither passes nor bypasses
it. Existing live ledger and unresolved Gate B records remain unchanged.

### How this implementation moves toward desired state

Use the same engine and strict aggregate. UTC records survive reopening; local
monotonic nanoseconds prevent a forward wall-clock step from shortening a wait after
its local anchor is known. A locally eligible intentional turn still goes through the
actual budget/SDK admission path. Recovery is another exact-context CAS transition:
recognize/reconcile first, otherwise require quiescence and settle just that attempt.
It never fetches, acknowledges, invents exhaustion or overwrites a replacement attempt.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Internal wait/recovery values and status evidence | backfill.py / state status projection |
| 2 | Dual-clock pacing and observed attempt ends | engine clock helpers and eligible prepare |
| 3 | Exact, idempotent recovery transition | recover method using existing CAS/recognition |
| 4 | Preserve typed retry observations at source boundary | safe SDK/budget hints, unchanged actual-send authority |
| 5 | Timing/recovery and real commit-boundary tests | test_27 plus intentional staged-assertion updates |
| 6 | Documentation, full verification and handoff | separate product/work commits, push/#19 status; Stage 6 next |

## Interface and meaning decisions

### Local waiting, not global account readiness

Add optional `wait_seconds` to internal immutable `BackfillTurn`, default None and
included in to_dict. A waiting turn has no batch/delivery, positive finite remaining
local interval, active nonterminal state, no unresolved attempt and no persisted clock
uncertainty. Normal pending/replay/terminal results keep None. The saved UTC not-before
is already in status; remaining seconds can be longer if a local monotonic anchor is
stronger. None is not a claim that the account is ready. No new public facade/export.

Status remains a stored-fact query: no clock, reader or budget I/O. Add content-free
`pacing_attempt_id`, `pacing_ended_at`, `last_recovery_id`, `last_recovered_attempt_id`
and `last_recovery_at` from the existing record, with defaults on the dataclass for
internal construction compatibility. Serialize dates canonically. No wire-state
version/field changes; new status/turn fields are not changes to MessageBatch v1.

`BackfillEngine(..., clock=UTC_now, monotonic_ns=time.monotonic_ns)` permits independent
injection. The monotonic function must return a non-boolean nonnegative integer in
signed-64-bit range. It is never called by start/status/replay/ack/recognized recovery.
Clocks are sampled lazily for source eligibility/end or a genuinely new recovery.

`recover(run, *, attempt_id, command_id, expected_control_revision,
previous_reader_stopped)` requires all keyword arguments. The true boolean is a
caller assertion, not a timeout/lease. Return immutable `BackfillRecoveryResult` with
`command_id`, `attempt_id`, `applied`, `outcome` (`recovered` or `settled`) and attributable
status. Exact retained command retry returns recovered/applied=False. A matching
already-settled source observation returns settled/applied=False with no new command
record. A newly committed recovery returns recovered/applied=True. No error is a
permission to rebase the request automatically.

### Clock evidence and portable deadlines

- Add a separate source/recovery clock-pair helper. UTC must be valid; monotonic ticks
  must be valid. Detect either clock going backward relative to the engine's last
  successful pair. Also compare UTC against saved creation/admission/end anchors.
  Raise sanitized BackfillClockError with no new permission on contradiction.
- Keep `_now` for acknowledgment's observation timestamp: recording valid external
  acceptance must not be blocked by source-pacing regression detection. Existing ack
  semantics remain; timing metadata is not acceptance authority.
- Store only UTC `ended_at/not_before` and existing recovery time. Compute durations
  as exact integer nanoseconds from `_pause_delta`'s upward-rounded microseconds.
  No floating-point arithmetic determines the earliest monotonic tick.
- Maintain at most one local wait anchor and one latest observed end per group,
  keyed by full RunRef/attempt and saved pacing fields. They cannot apply to another
  generation, collection or pacing record. Memory is proportional to groups touched.
- At actual attempt end, capture UTC and monotonic together. Remember its fixed UTC
  end/deadline and monotonic deadline **before awaiting publication**. A failed save
  does not erase a locally known end. An ordinary source failure uses the same anchor.
- On a read cancellation, do only best-effort synchronous end observation and preserve
  the original cancellation even if clock observation fails. Do not await persistence
  or acknowledge. Durable attempt uncertainty remains until explicit recovery.
- On reopening without matching local evidence, initialize a monotonic anchor once
  from the remaining saved UTC interval. Repeated checks do not restart it. Require
  both known UTC and local monotonic minimums before another admission.
- UTC can jump forward while monotonic still shows too little elapsed time: return
  the remaining monotonic wait. Backward UTC/monotonic or an unrepresentable deadline
  refuses; it never shortens a restriction. Unknown persisted timing remains an
  explicit recovery/eligibility refusal rather than a fabricated zero wait.
- Across process/engine recreation, reboot or move, local evidence is gone; trusted
  UTC is required. Arbitrary undetectable jumps cannot be solved. This is per-run
  spacing, not an account-wide rest guarantee or a bound on SDK request duration.

### Existing source restrictions remain authoritative where observed

Preserve `last_failure` as historical evidence with its observation time. Existing
ReadBudgetExceeded supplies verified account ID and optional absolute retry timestamp.
For a direct recognized SDK wait error (the existing health.WAIT_ERRORS type tuple),
record a valid nonnegative integer seconds hint as end-observed UTC plus that duration,
with overflow/invalid hint yielding None. Do not call health.classify or traverse a
local error's context to manufacture a hint; do not infer account identity for SDK
errors from the stale health cache. Unknown/account-less provenance remains None.

These observations do **not** become a second cached account admission gate. The
reader may use a different account later; only BudgetClientMixin/SDK can recheck that
current context. `wait_seconds` describes local pacing; last_failure/retry_at describes
what happened previously. An expired hint does not guarantee allowance, and an unknown
hint is not converted to zero. Source failures still raise; no automatic retry loop.
Recovery preserves these fields and never refunds/configures budget state.

## Step 1 — Values and stored evidence projection

### Proposed changes

Extend `tgdata/backfill.py` with the wait field, validation and recovery result above.
Extend `_BackfillState.status` in `tgdata/backfill_state.py` to expose existing pacing/
recovery evidence. Keep the wire codec and all v1 record keys/invariants unchanged.
Local errors retain suppression/read_error behavior. Document additive internal fields.

### Output

Waiting and recovery outcomes have explicit immutable values and portable dictionaries.

### Safe in nature

False — internal result shape changes, although defaults preserve existing construction.

### Peripheral concepts

Typed context/receipt values, exact IDs, content-free status, state-vs-result schema.

### Hardness Lvl

2/5.

## Step 2 — Pacing admission and known ends

### Proposed changes

Implement the clock/anchor design in `tgdata/backfill_engine.py` with small private
helpers. Remove only the temporary Stage 5 configuration refusal. Pending, terminal/
paused and unresolved-attempt checks keep their existing precedence and clock-free
paths. After context validation, a known early pacing condition returns BackfillTurn
with wait_seconds, no state write, reader callback, directory creation or sleeping.
An early wait does not require a configured source callback or usable media directory.
Invalid supplied media-mode/path types still fail normal local validation.

For an eligible read, reuse the same sampled clock pair for admission; do not read the
clock a second time merely because pacing exists. Keep revision headroom, actual root/
reader checks and strict confirmed admission before source invocation. A fresh run
with no pacing still validates reader/root before sampling for admission. Known UTC
anchors cannot be in the future relative to the eligibility observation.

Use exact nanosecond arithmetic for all elapsed decisions; only convert remaining
wait to a finite positive seconds result. `_ended` retains its end/deadline return
shape for existing settlement while recording volatile matching end evidence. Preserve
cancellation/no-send, strict result validation, original exceptions and CAS behavior.

### Output

Repeated positive-pause turns work when eligible; early turns return immediately.
Acknowledgment/replay/status cannot change a deadline or establish new read permission.

### Safe in nature

False — replaces a capability refusal with real source-admission timing.

### Peripheral concepts

UTC/monotonic clocks, source cancellation, directory side effects, revision headroom.

### Hardness Lvl

5/5.

## Step 3 — Exact-attempt recovery

### Proposed changes

Validate the run snapshot, scope, tokens, integer control revision and required true
boolean before mutation. Conservatively refuse recovery while this engine has any
prepare active for the group; the caller can wait for that operation to finish. This
also covers admission/publication awaits, not only the raw callback. Caller assertion
still governs other engines/processes; no cross-process lease is implied.

For at most four normal CAS-conflict iterations, load authoritative state:

1. Reject a command ID known as the latest control identity (different action). If
   latest recovery has that command ID, require the original attempt/control inputs;
   return its recognized result before clock/revision-capacity checks. Never update
   its recovery time/deadline on retry. This retained recognition may survive a newer
   attempt's admission; the new attempt is never cleared.
2. For an unrecognized command require current control revision exactly. Do not rebase
   to a concurrent pause/resume. If an attempt exists, its ID must match the addressed
   one and it must belong to the current row; otherwise conflict.
3. With no attempt, only a matching retained pacing attempt can reconcile a settled
   source outcome. Return its actual pending/terminal/recovery facts with no mutation,
   clock, media verification or reader call. Unknown/replaced attempt IDs conflict;
   missing/pruned runs remain UnknownRun. This does not accept/remember a new recovery
   command merely to answer a read-only reconciliation.
4. For the exact unresolved current attempt, require revision capacity, recheck local
   preparation quiescence, sample valid clock evidence and compare it to saved admission/
   creation. Prefer a matching trustworthy locally observed end/deadline when present.
   Otherwise establish one full configured interval from accepted recovery time.
   Preserve any later known saved not-before and stronger matching local wait anchor.
   A valid fresh interval can conservatively replace missing old end evidence; a
   currently invalid clock cannot. Do not reuse another attempt's end.
5. In one candidate: clear only that attempt; keep after_id/pending/end/operator/
   terminal/failure facts; set pacing for this attempt (ended_at known or None,
   not_before chosen conservatively, clock_uncertain=False), and last_recovery with
   exact command/attempt/expected control, new state revision and recovered_at.
   Remember matching local timing before awaiting CAS so lost replies cannot remove
   the elapsed guard. The candidate must pass the existing strict codec.
6. Commit with Stage 4's existing exact read-back helper. A false CAS reloads and
   checks these same conditions; it cannot overwrite changed control or a new attempt.
   An exceptional unresolved result propagates, with no blind second write. The same
   retained command can later recognize a committed recovery. Bounded unresolved
   conflicts report an error; none initiate a source call.

Preserve known pacing after already-committed source settlement, including pending/
completed/cancelled records. Recovery does not inspect/delete media, deliver anything,
advance cursor, create exhaustion, resume operator intent or touch account budgets.
Known clock uncertainty on an already settled record remains explicit; this API is
not an unrestricted clock/state repair command.

### Output

A scoped recovery operation with durable retry recognition and conservative pacing.

### Safe in nature

False — a recovery mistake could clear live/newer activity and authorize duplicate reads.

### Peripheral concepts

CAS, command identity, quiescence, bounded retention, future controls, source-end evidence.

### Hardness Lvl

5/5.

## Step 4 — Typed source retry observations

### Proposed changes

Extend `_failure` only at the actual reader-error boundary as specified above. Retain
budget class/type/account/retry information; add direct known SDK wait seconds without
following causes or consulting cached identity. Invalid/overflow hints stay None.
No edits to ReadBudget, BudgetClientMixin or HealthMonitor. Future attempts still
recheck actual account policy and SDK restrictions even if an earlier hint expired.
Historical failures remain observations after success/recovery, not a global block.

### Output

Status retains actionable safe hints while local timing and source admission remain distinct.

### Safe in nature

False — persisted observation metadata changes for recognized SDK wait errors.

### Peripheral concepts

SDK error types, actual account verification, error provenance, budget expiry/warm-up.

### Hardness Lvl

3/5.

## Step 5 — Timing, budget, recovery and real persistence tests

### Proposed changes

Add `tgdata/smoke_tests/test_27_backfill_pacing.py`, reusing actual SQLite, SDK/batch/
budget fixtures from existing suites and blocking sockets. Inject UTC and integer
monotonic clocks independently. Execute actual methods, not source-string assertions.

Cover:
- 10:00 end/240-second interval, early and late ack, repeated status/replay/waits,
  no clock on stored-fact paths, no early directory creation/reader callback, zero
  and sub-microsecond pause; unknown/terminal/paused precedence remains intact.
- Reopened remaining interval, forward UTC cannot beat retained monotonic minimum,
  backward clocks, invalid/raising clocks, overflow and namespace/generation anchor
  isolation. No portable monotonic field is written. Add a small measured elapsed
  wait with real monotonic time; do not fake a live Telegram gate from it.
- Actual budget exhaustion with valid prefix, no-prefix refusal, preserved verified
  account metadata despite stale cache, known/indefinite retry hints, expired hint
  but still-denied actual allowance, account switch and a permitted **disposable
  offline** policy change preserving charges. No real ledger change/network.
- Direct SDK wait hint, unknown/auth/local error without invented hints/health;
  original source exceptions and local persistence/cancellation precedence.
- Required true quiescence, live same-engine prepare/refused recovery (including
  a held committed publication/admission), wrong run/attempt/command/control,
  known control-ID collision, missing/corrupt backend and counter limits.
- Unknown stopped attempt recovered once; known local end preserved after failed
  publication or cancellation; lost local end gets full interval; stronger saved
  deadline preserved; restart/identical retry has no clock/write/deadline refresh.
- Already committed pending/completed/known-failure outcome reconciles without
  mutation/artifact access. Changed recognized recovery input conflicts; old
  recognized retry cannot clear newer admission, and forgotten attempts refuse.
- Concurrent recoveries/compatible settlement versus stale control/new attempt,
  false CAS bounds, commit-then-error/nonbool exact confirmation, unreadable result,
  cancellation and original read-error provenance.
- Owned subprocess exits immediately before/after actual recovery commit. Reopen
  existing-only: uncommitted marker remains; committed recovery retains one identity/
  deadline and no fabricated ack/end. Include real prepare→crash→confirmed child exit
  →recovery and explicit live-local-reader negative cases.

Optionally validate offline copies of Gate B's two actual unresolved SQLite records
through the new method, with recorded prior worker exits. Preserve originals and the
account ledger. Label this LOCAL using LIVE-origin state, not a Gate C result.

Update only planned staging assertions in tests 24/25: recover now exists internally;
positive pacing produces wait/eligible behavior. Retain control/public-facade absence
and every unrelated failure/identity/delivery assertion. Any small test correction is
recorded; never weaken a failing expectation to accommodate a design change.

### Output

Executable temporal/fault matrix and actual durability receipts for the new behavior.

### Safe in nature

True — disposable offline files/clocks/processes, no Telegram or original evidence mutation.

### Peripheral concepts

Real SQLite/process boundaries, SDK/budget semantics, clock independence, concurrency.

### Hardness Lvl

5/5.

## Step 6 — Documentation, verification and publication

### Proposed changes

Update docs/backfill_state.md and smoke-test README with actual wait/recovery use,
quiescence assertion, retry scope, clock/trusted-UTC limitations and source-observation
meaning. Reflect availability in the issue handoff/contract/assumptions/staged plan/
acceptance matrix without altering historical Gate A/B receipts or claiming Gate C.

Run compile/AST Python-3.7 grammar checks, new suite, then all supported offline suites
26/25/24/23/22/19/18/17/16/15/14/13/12 and two explicitly awaited test_11 helpers;
run the unchanged Gate A instrument and daily example. Preserve explicit legacy live
skips, actual Python 3.11.10/Telethon 1.45.0 scope and exact pass counts. No actual
Python 3.7 runtime or real-source pacing claim from syntax/synthetic tests.

Commit product code/tests/public docs separately from work evidence. Publish the #19
feature branch and update its scoped checklist/comment after commits. Its issue body
is at ~65,459 bytes: shorten current status/link fields as needed, use a completion
comment, and preserve the original request/history. No unrelated worktree/duncan,
PR/protected merge or Stage 6 implementation. Final handoff names Stage 6 then Gate C.

### Output

Verified Stage 5 checkpoint, accurate GitHub status and a clear Stage 6 handoff.

### Safe in nature

True — verification/docs/publication of this feature branch, no deployment or source writes.

### Peripheral concepts

Compatibility, stage gates, private evidence preservation, contribution checkpoints.

### Hardness Lvl

2/5.
