---
model: gpt-6-astra
effort: max
---
**Verdict: IMPLEMENT AFTER FOLDING THESE IN**

**Falsifier:** a selected independent real-group oracle contradicts the ID/date/end
interpretation required by the proposed saved-run contract, so its source-facing
meaning must change before later lifecycle work.
**Affordable now:** no — specific existing-group/account/oracle inputs remain unset.
Gate A stays a mandatory execution condition. Affordable local storage/time premises
were probed before this verdict; their two bounded defects below do not invalidate
the plan's shape or require a different lifecycle architecture.

## High-level summary

Two Medium findings: reopen must fail at the actual SQLite open boundary rather than
merely check that a file exists, and timestamp-resolution conversion must not round a
minimum pause down. Select focused remedies; preserve the existing default store API
and the Stage 2-only boundary. No High/Low findings or new planning blocker.
In-session critic-d, plan revision 1 at 1abbe65, product base 5d0789e.

## Premise Inventory

### Atomic opaque storage can hold one lifecycle aggregate

First dependent step: 1/2; waste if false: record/engine design and later source
lifecycle built on it. Test scheduled: existing receipts, current component probes,
new-state tests in Step 3. Cheapest earlier actual SQLite uncertainty/process-exit
checks were run now and passed. The backend really stores opaque text with exact CAS;
a memory adapter is not used as durability evidence. Current results do not certify
new snapshot validation or a different remote backend.

### Saved-query/source behavior matches real visible history

First dependent step: Step 4 instrument and Step 6 live execution; runtime Stage 3
cannot proceed before Gate A. Waste if false: revise source-facing query assumptions
before later lifecycle stages. Cheapest real test requires the selected account/group
and independent complete interval; unavailable now. Existing SDK and source tests
use synthetic replies and are non-covering for actual Telegram visibility. The plan
keeps that distinction and no-gate-pass barrier.

### Timestamp values preserve a requested minimum pause

First dependent step: Step 1 numeric/schema validation, then future Stage 5 scheduling.
Waste if false: a stored policy and accepted deadline disagree. Cheapest test is actual
Python timedelta conversion, run now: 0.4 microseconds rounds to zero; 1.4 to one.
This is an implementation representation defect, not a reason to change the selected
post-attempt policy. Risk 2 closes it before encoding/validating the record.

### Known-state open never means fresh bootstrap

First dependent step: Step 2 usage and Step 4 preflight. Waste if false: missing known
state is obscured by a newly created empty file, including a check/open race.
Cheapest actual store test ran now: create real state, delete the disposable database,
construct SQLiteSyncStore again; it creates a new database and load returns None.
Its current default is intentional for new stores; the new resume use needs a strict
open mode. Risk 1 closes the specific reuse mismatch.

### Instrument observes real SDK sends without changing the source contract

First dependent step: Step 4. The pinned installed UserMethods._call retry loop calls
sender.send on each attempt; the actual BudgetClientMixin wraps that seam. Source
inspection supports placement, not proof of the new wrapper. Step 4 requires actual
SDK/request-type tests with injected transport, then the real Gate A trace. A fake
reply is not source evidence. Unknown RPCs/group context must refuse before send.
If the wrapper fails its offline seam tests, it cannot run live; do not bypass it.

## Component observations

On the integrated branch, Telethon 1.45.0, disposable SQLite and sockets forbidden:
- Store recreation and sub-microsecond rounding observations above reproduced.
- `test_backend_failures_conflicts_and_uncertain_ack` passed.
- `test_process_exit_at_actual_ack_commit` passed using its real SQLite subprocess boundaries.
- `test_relative_enrollment_freezes_once` passed.
No new lifecycle state, live account or Gate A was tested by those receipts.

## Restart Check

- Known missing state versus bootstrap: current constructor recreates absent file;
  selected strict-open remedy belongs before Step 4, not a warning after it.
- Committed write versus lost reply: actual existing store/continuation tests retain
  committed outcome; Step 2 returns uncertainty and Step 3 reopens actual storage.
- Frozen versus recalculated relative dates: existing code loads before clock; Step 2
  adopts recognition-first and Step 3 forbids the clock on recognized retry.
- Unknown creation retry versus new intention: Stage 1's explicit submission/context
  rule is retained in Steps 1/2 and tested in Step 3; no empty-store shortcut.

## Inherited Lessons

Each is enforced by sequence: strict state/identity before new source work (Steps 1–3);
actual persistence before reporting durable success (2/3); source oracle before accepting
Gate A and before Stage 3 (4/6); no codec-fixture claim of implemented transition (1/3);
legacy APIs retained with full regressions (5). Synthetic checks remain non-covering
for LIVE cases. Open fixture inputs stay execution conditions, not waived tests.

## Risk 1 — Reopening a lost store can create an empty replacement

**Risk**

A process expects a saved job, but its progress file disappeared. The existing storage
constructor is designed to create new files. Using it to reopen that job can create
an empty replacement, hiding the difference between first use and lost data. Checking
for the file first still leaves a gap in which it can disappear before opening.

`SQLiteSyncStore.__init__` calls `_transaction(initialize=True, write=True)`, which
uses SQLite `mode=rwc`. Step 4 of the plan requires an existing-only probe open but
does not supply a backend operation that guarantees it. A Path.exists check followed
by this constructor is racy. Engine status would still refuse a missing run, but the
filesystem has already been changed, contradicting the promised preflight behavior.

**Severity:** Medium. **Category:** storage/recovery/API reuse.
**Impact:** misleading empty database and unwanted bootstrap side effect during recovery.
**NoobEng:** choosing “open my saved work” must fail if it is gone, even if it disappears
between checking and opening. That needs the database open itself to refuse creation.
**Affected areas:** tgdata/sync_store.py constructor, Gate A tool and reopen documentation.

### Mitigation — Quick

Check Path.exists immediately before constructing the current store.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Add keyword-only `create=True` to SQLiteSyncStore. Preserve default behavior; `create=False`
opens with the existing mode=rw/schema-validation path, creates neither file nor schema,
and rejects missing/incomplete state. Use it for known-store Gate A/preflight/reopen.
Test missing file, missing schema, deletion after construction and unchanged default.
**Why this is robust:** closes the open-time race in the actual backend with one compatible
option, without changing the opaque load/CAS protocol or database schema.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The actual other consumers are SyncEngine and the new probe, both using SQLiteSyncStore; the compatible open flag closes this resource-opening instance. Budget/session storage have different provisioning rules, so a universal factory is not one proved class. Robust wins on reach/extent with no schema migration.
*For future:* —

### Mitigation — Long-term

Split provisioning and reopening into a general storage factory across sync, budget
and session persistence.
**Why this is long term effective:** a common lifecycle could distinguish bootstrap
from recovery at every persistent resource, if their different ownership rules were unified.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Consider a wider provisioning contract only in a separately selected storage task. This flag would survive that extension and is not throwaway work.

## Risk 2 — Datetime rounding can shorten a positive saved pause

**Risk**

The caller selects a small but positive quiet interval. Ordinary timestamp conversion
can round it down, including to zero. A stored deadline can then appear valid even
though it permits another request earlier than the requested minimum interval.

The contract accepts finite nonnegative pause_seconds, while Step 1/2 plan validation
uses UTC datetime/timedelta representability without specifying its rounding direction.
Actual timedelta(seconds=0.0000004) is zero, and timedelta(seconds=0.0000014) is one
microsecond. The future `pacing.not_before` validator must compare against a rounded-up
minimum, not the rounded-down expression it would otherwise accept.

**Severity:** Medium. **Category:** time representation / validation.
**Impact:** saved policy and minimum deadline can disagree before Stage 5 scheduling exists.
**NoobEng:** this timestamp format measures whole microseconds. A minimum duration must
round toward more waiting, not toward less, when the requested value is between ticks.
**Affected areas:** backfill value helper, record pacing checks, creation representability,
new tests/docs; future scheduling must reuse the same minimum-duration conversion.

### Mitigation — Quick

Document that very small pauses may round down and recommend larger values.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Keep the canonical requested numeric value for identity, but derive the minimum UTC
interval by rounding its canonical decimal value up to whole microseconds. Reuse that
helper for representability and known pacing validation, with overflow refused locally.
Test sub-microsecond, fractional-microsecond, zero and overflow cases. Clock/provider
failures remain local sanitized errors, not Telegram verdicts.
**Why this is robust:** one backfill-local conversion enforces the minimum at both
construction and reload, without changing unrelated legacy timing semantics.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The two genuine instances are new-run deadline representability and saved pacing validation within backfill. One local ceiling conversion serves both. Legacy budget accounting and SDK sleeping use different clock contracts; a global type grows scope for unproved reach. Robust is the smallest complete remedy.
*For future:* —

### Mitigation — Long-term

Introduce a project-wide exact-duration type and convert budget, retry and lifecycle clocks.
**Why this is long term effective:** a genuinely shared representation could standardize
precision throughout future timing code, but existing ledgers and SDK timers have different contracts.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit shared duration types only if another concrete module needs the same minimum-deadline semantics. The local helper remains valid in that future.

## Carried execution condition

Step 6 remains OPEN until actual existing-group/read-only account/fixture/oracle,
request bounds and authoritative budget inputs are qualified. No severity assigned.
It does not block Steps 1–5 and cannot be converted to a live PASS from local results.
