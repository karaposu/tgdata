---
model: gpt-6-astra
effort: max
---
# #7 Stage 4 — Join allowance, revision 2

**Critic folded:** 2026-10-10 — 1 mitigation (3 steps changed, 0 added). Risk1 robust selected; required shared-file experiment PASS before any implementation step.

### What is the task

Provide a standalone durable rolling-day allowance for admitted join attempts,
so the separately reviewed Stage 5 can consume one local claim before each
source attempt. Keep the implementation small: one ledger module, exports,
contract documentation and real storage tests. No client/health integration.

### Huge Hard Blockers

#### Planning Blockers

None identified. `desc.md` inherits no open blocker. `traverse/finding.md` settles
the counting and custody contract. Actual SQLite/process experiments in
`contract_probe.py` and `evidence/critique-probe.txt` precede this plan: concurrent
admission serializes, process exits preserve committed charges, existing-file
opens refuse absence, and an error after a real commit leaves a charge. These
are component observations, not a claim that unbuilt methods already pass.

#### Execution Blockers

None identified for this stage. All work and verification are local/offline.
Stage 5 integration and live joining are outside this plan, following review
and merge at the user's chosen boundary.

### How this implementation moves toward desired state

Stage 4 adds durable local policy and accounting without changing the verified
account operation or its health ownership. Explicit creation avoids accidental
reset on normal reopen. A short writer transaction binds observation, expiry,
capacity and charge. An uncertain outcome spends allowance but grants no return
permission. No receipts, refunds, backend abstraction or generic quota framework
are needed. Existing ReadBudget's different lifecycle remains untouched.

### High-Level Summary

| Step | Description | Expected Output |
|---|---|---|
| 1 | Define local values and errors | JoinBudgetStatus and error surface |
| 2 | Implement persistent custody and transactions | Explicit provisioning, validated schema, conservative failures |
| 3 | Implement configuration, status and atomic claim | Rolling accounting keyed by account ID |
| 4 | Qualify storage and failure boundaries offline | test_35 with actual SQLite/process evidence |
| 5 | Export and document the delivered boundary | Public exports, README, join contract and suite entry |
| 6 | Verify and record delivery | Product commit, separate work record, accurate #7 state |

## Step 1 — Local values and errors

### Proposed changes

Create `tgdata/join_budget.py`, standard-library imports only, Python 3.7 syntax.
Add `JoinBudgetError(RuntimeError)` suppressing incidental exception context,
with `JoinBudgetConfigError`, `JoinBudgetStorageError`, `JoinBudgetExceeded`.
None is registered as a health verdict. Exceeded carries `status`, `account_id`,
`retry_after` and `next_available_at`; no partial-result/refund semantics.

Frozen `JoinBudgetStatus` has account_id, limit, used, remaining, observed_at,
next_available_at. `retry_after` is 0 when capacity exists, None when limit=0,
otherwise ceil(next_available_at-observed_at), bounded below by0. `to_dict()`
returns a fresh JSON-compatible dict including retry_after and window_seconds=86400;
observed/next times are UTC ISO text, absent next time is None. When remaining>0,
next_available_at is None, matching the existing read status convention.

Validation: use `operator.index` for account ID [1,2**63-1] and daily_limit
[0,2**63-1], reject booleans. Clock results accept int/float except bool, must be
finite and in [0,253402214399] (one day of ISO expiry headroom). Values are copied
to built-in int/float. A clock must be callable; callback Exception becomes a
sanitized ConfigError naming only its type. BaseException, including cancellation,
propagates. Bad argument conversion raises ConfigError from None. [folded: Risk 1, robust]
Explicitly re-raise asyncio.CancelledError before generic argument/clock conversion
catches; its Python3.7 Exception inheritance must not change the cancellation result. Stored values
use strict SQLite result types and become StorageError, not caller errors.

### Output

Small frozen status/error API and deterministic pure validation/format helpers.

### Safe in nature

True — new, not yet exported; no existing runtime path changes.

### Peripheral concepts

ReadBudgetStatus naming, health exception-chain classification, UTC serialization.

### Hardness Lvl

2

## Step 2 — Explicit state custody and transaction lifetime

### Proposed changes

Add `JoinBudget(path, *, create=False, clock=time.time)`. Accept filesystem string
or PathLike, resolve/expand once, reject empty, bool, None, bytes, `:memory:` and
`file:` URIs; parent directories must already exist. `create` must be bool.
Connection URI is Path.as_uri plus mode=rwc only for explicit constructor creation;
constructor reopen and all methods use mode=rw. Missing state never silently
reappears during ordinary operations. Path/connection errors expose sanitized
types, not paths or underlying exception text.

Use three independently named tables, schema version1:

```sql
CREATE TABLE tgdata_join_meta (
    id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL);
CREATE TABLE tgdata_join_accounts (
    account_id INTEGER PRIMARY KEY,
    daily_limit INTEGER NOT NULL CHECK(daily_limit>=0), last_clock REAL NOT NULL);
CREATE TABLE tgdata_join_attempts (
    id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL, admitted_at REAL NOT NULL,
    FOREIGN KEY(account_id) REFERENCES tgdata_join_accounts(account_id));
CREATE INDEX tgdata_join_attempts_time ON tgdata_join_attempts(account_id, admitted_at);
```

No automatic migration or repair. Check sqlite_master for all four owned names;
only an entirely absent namespace plus create=True initializes it. All other
partial/wrong-object states refuse. Validate exact columns, declared types,
not-null flags and PK positions with table_info; validate the attempt FK and
account/time index (nonunique, not partial). Metadata must contain exactly (1,1),
both integers. No need to compare textual SQL/check-expression spelling; runtime
value validation covers relevant data constraints. Constructor validates schema;
account operations validate the affected account's values. Refuse orphan or
noninteger attempt owners before configuring/observing any account, so a missing
policy cannot be recreated around surviving charges. Do not touch other namespaces.

Every transaction opens a short connection (timeout5, isolation_level=None),
enables foreign_keys and synchronous=FULL, begins IMMEDIATE, checks schema,
performs work, commits, then closes. No transaction spans an await. Catch
BaseException so primary cancellation/errors survive cleanup. SQLite errors map
to type-only StorageError from None. On primary failure, attempt rollback and
close independently, catching secondary BaseExceptions and logging only operation
and error type; logging itself cannot replace the primary. On a sole close
Exception raise StorageError; sole close cancellation propagates. [folded: Risk 1, robust]
Check asyncio.CancelledError explicitly before generic close-error conversion, including
its Python3.7 hierarchy. Secondary cleanup cancellation still preserves the primary. Commit or close
errors grant no claim even if a durable charge already exists. No retries/refunds.

### Output

Existing-state reopen and explicit provisioning with conservative transaction
errors and separate schema, reusable by the three local operations.

### Safe in nature

False — explicit creation can add tables to a caller-selected existing file.

### Peripheral concepts

SQLite URI opening, locking/fsync, shared ReadBudget file, cancellation, sanitized logging.

### Hardness Lvl

4

## Step 3 — Policy, observation and one-unit consumption

### Proposed changes

`configure(account_id,daily_limit)` returns the resulting status. `status(account_id)`
returns a status snapshot; `_claim(account_id)` returns None only on successful
one-unit admission. Missing policy is ConfigError (except configure); a missing
policy with surviving attempts is damaged storage and refused.

Shared observation sequence under the writer lock:

1. Load affected policy; validate stored limit as a nonnegative SQLite int and
   prior last_clock as finite in the accepted epoch range.
2. Validate all affected attempts BEFORE advancing time or deleting anything:
   id and owner are positive SQLite ints; admitted_at is numeric/finite/in-range
   and <= the PRIOR last_clock. Null, text, blob, out-of-range and future values
   refuse with StorageError. Use bounded invalid-row queries, not materializing
   an unbounded history in Python. Constructor schema-only validation does not
   claim every untouched account's values have been scanned.
3. Invoke the clock under the lock; effective_now=max(clock,prior last_clock).
   Insert new policy only for configure; otherwise UPDATE the existing row
   (never REPLACE). A configure changes the limit after validating prior data.
4. Persist effective_now and delete only affected attempts with
   admitted_at<=effective_now-86400. A clock failure rolls back everything.
5. Count affected rows, remaining=max(0,limit-used). If exhausted and limit>0,
   next_available_at is the ordered timestamp at zero-based offset used-limit
   plus86400: enough expirations to yield a slot after a cap reduction. Zero cap
   has no future admission time. Different account policies/clocks are isolated.

For claim, observe, then insert a single attempt only when remaining>0. If denied,
save the Exceeded object, exit the transaction successfully to persist observation/
expiry, then raise it from None. Do not throw a denial inside the transaction and
roll back its clock. A status snapshot never reserves a future claim. Every new
claim is another charge; there is no success settlement, cancel hook or delete API.

### Output

Durable atomic admitted-attempt counter, policy/status semantics and retry hints.

### Safe in nature

False — deliberate mutation of the new persistent accounting namespace.

### Peripheral concepts

Rolling time, backward clock clamp, account IDs, uncertainty, future verified send boundary.

### Hardness Lvl

4

## Step 4 — Behavioral qualification

### Proposed changes

Add `tgdata/smoke_tests/test_35_join_budget.py`, runnable by python -m, using
unittest/temporary directories and actual SQLite. No git/history dependence or
network. Tests use synthetic positive IDs and no credentials. Test groups cover:

- Explicit create/reopen/missing-file/missing-namespace, same-file ReadBudget
  coexistence, refused partial/version/column/PK/FK/index/metadata damage, wrong
  object types, and loss after a live object was opened. Refusal never repairs.
- [folded: Risk 1, robust] Native current-runtime cancellation plus a clearly labeled
  Exception-derived compatibility fixture at conversion and sole-close boundaries.
  No native Python3.7 execution claim.
- Input types/ranges, clock callback failures/cancellation, max ISO headroom,
  policy absence/zero, frozen status/fresh JSON dict and public exports.
- Exact rolling boundary, fractional retry rounding, same-time claims, reduced
  cap's sufficient expiry, raised caps, policy preservation, per-account
  isolation, backward clock across restart and denied-claim clock persistence.
- Invalid stored policy/clock/id/owner/timestamps, including the inquiry's
  negative and future-vs-old-clock cases, with before/after rows proving no prune.
- Forced overlap: spawned workers open first then wait at a barrier; competing
  claims against a cap yield exactly cap successes, persisted usage agrees.
  Different-account workers also get independent allowance.
- Real subprocess exits bracketing commit with a delegating connection wrapper;
  before commit leaves0, after real commit but before return leaves1. This tests
  process failure, not physical disk power loss. An injected exception after
  real commit raises StorageError and retains usage; no permit is returned.
- Delegating wrappers inject begin/insert/commit/rollback/close failures on real
  connections; verify rollback of uncommitted work, no leaked writer locks,
  primary identity/cancellation preservation, cleanup-only errors and type-only
  logs even when logging fails. Test local errors raised inside Telegram-error
  handlers with actual health.classify; no invented health registration.

The contract probe is prior evidence, not the new suite. Fault stand-ins inject
failures around real storage; they do not supply the storage's durability result.

### Output

Measured qualification of public ledger operations and the private consumption seam.

### Safe in nature

True — synthetic/offline tests in temporary files only.

### Peripheral concepts

Process spawning, SQLite connection faults, real health classifier, archive-run tests.

### Hardness Lvl

4

## Step 5 — Exports and consumer documentation

### Proposed changes

Export JoinBudget, JoinBudgetStatus and the four errors from `tgdata/__init__.py`.
Add a brief README section and `docs/join_budget.md` covering explicit one-time
provisioning vs reopen; account policy/status example; counted attempts/no refunds;
rolling-day/zero/missing-policy/changed-cap rules; status fields; local failures;
clock, same-host file custody and busy timeout. No guessed Telegram-safe limit.
The sample can use zero to demonstrate a paused configured account.

State clearly that this is the standalone Stage4 allowance. No TgData option or
automatic join guarding exists. Document Stage5 obligations: freshly verified ID,
one successful claim per actual attempt/retry, claim immediately before enqueue
without awaiting or caching permits, uncertainty remains charged. No ledger is
held over network I/O. Add test35 entry to `tgdata/smoke_tests/README.md` with actual
measured count and limitations after the run.

### Output

Discoverable public local API and an accurate future-integration boundary.

### Safe in nature

False — new public package imports/exports; verify import compatibility.

### Peripheral concepts

Public package surface, documentation examples, future joining stage.

### Hardness Lvl

2

## Step 6 — Verify, commit and update status

### Proposed changes

Run new test35, then supported offline suites12–19,22–30,32–34 under the project's
Python3.11.10/Telethon1.45.0. Use normal python -m for process suites; absent config
for12/13 so their3 live checks skip. No old live-only tests or unmerged test31.
Run daily-continuation demo and backfill new/restart demos; compile tgdata/examples
and AST-check Python3.7 syntax. Baseline is494 actual groups plus3 live skips;
report the actual new count, not assertions as tests. Check git diff --check and
scope; run suite35 from an exported tree without .git to prove self-containment.

Commit product code/tests/docs together, then verification.md/HANDOFF.md separately.
Record all deviations/local verification fixes honestly. Push the feature branch,
update committed pipeline steps on #7. Leave merge check, PR critique and merge
pending. Keep parent #7 open and Stage5 untouched, and leave unrelated original
worktree files, duncan and the stray guide alone.

### Output

Tested Stage4 delivery on its archive-capable branch, ready for separately requested review.

### Safe in nature

False — commits/push and issue publication, within the authorized implementation workflow.

### Peripheral concepts

Repository pipeline, offline regression scope, Python support and work-doc exclusion on later merge.

### Hardness Lvl

2
