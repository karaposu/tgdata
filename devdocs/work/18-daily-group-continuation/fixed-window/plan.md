---
model: gpt-6-astra
effort: max
---
# Fixed historical windows — plan, revision 1

### What is the task
Extend the existing batch/continuation APIs with a fixed UTC interval, supplied as
explicit dates or resolved once from last_days. Reuse the existing progress store,
immutable pending batch and acknowledgment path. The caller continues to own its
archive and scheduling; daily and historical collections use separate stores.

### Huge Hard Blockers
#### Planning Blockers
None identified. Date positioning, exclusive ID continuation and quota resizing
were probed against actual Telethon1.45.0/guard code before this plan. The first
query uses the SDK's documented chronological date offset; scripted transport is
not evidence of live server behavior. No live operation is required or authorized.
#### Execution Blockers
None for these steps. The implementation is based on the completed daily feature
on this same linked branch. Combined merge review remains a later gate; no merge
or publication of a PR is part of this run.

### How this implementation moves toward desired state
Add one immutable date constraint to the existing collection, not a new scheduler
or delivery state machine. Save the resolved dates with the initial record; all
later prepare/ack transitions preserve them. Select messages in that interval
before preparing media. Existing batch v1 identifies returned observations, not
queries, and needs no new fields. Strict state decoding validates window membership.

### High-Level Summary
| Step | Description | Expected output |
|---|---|---|
| 1 | UTC window validation/value | one internal shared date contract |
| 2 | Bounded batch reading | date positioning, exact interval filtering, ID resume |
| 3 | Durable window enrollment/continuation | saved dates reused through the existing store/ack path |
| 4 | Offline behavioral suite | boundary, restart, budget, compatibility and failure coverage |
| 5 | Public contracts and examples | explicit usage and scope, test inventory |
| 6 | Verify and commit | supported offline regression receipt, separate code/docs checkpoints |

## Step 1 — shared window value
### Proposed changes
Create tgdata/history_window.py with a private immutable _HistoryWindow containing
start_date and end_date. Accept timezone-aware datetime objects only; convert to UTC,
require start < end, and constrain both to the nonnegative signed32 Unix date range
used by the SDK (epoch through 2038-01-19T03:14:07Z). Retain microsecond precision;
range-check the actual instant. Raise BatchFormatError locally with suppressed
incidental exception context. No package export or public class is needed.

A from_dates helper returns None only when both inputs are absent; a single bound
raises. Canonical state dates use UTC ISO strings with six fractional digits and Z,
with strict canonical decoding. A seek_date property floors start to a second and
subtracts one second for the SDK's exclusive offset; return None when that would
be epoch or earlier, selecting the oldest visible history instead. This ensures
messages exactly at start can be checked by the inclusive predicate.

A positive last_days integer is an enrollment convenience, not part of the raw
batch query. Resolve it in step3, using one UTC clock observation and timedelta;
invalid/overflowing durations raise SyncConfigurationError before writes/network.
### Output
An internal validated value shared by the reader and saved-state decoder.
### Safe in nature
True — new private module only; no existing call path changes yet.
### Peripheral concepts
UTC normalization, second-resolution SDK offsets, immutable dates, local errors.
### Hardness Lvl
2

## Step 2 — date-bounded batches
### Proposed changes
Extend TgData.get_message_batch and BatchEngine.fetch_batch with optional keyword
start_date=None, end_date=None. Construct the window before entering a client or
creating media directories. Omitted dates preserve existing requests and output.

Retain the existing guarded connection, entity resolution, group/peer validation,
record conversion, file preparation and partial-result exception handling. Use a
bounded oldest-first SDK iterator with limit equal to the remaining *included*
record capacity. For a zero scan cursor and a window, set offset_date=seek_date;
otherwise use min_id=scan_cursor. An ID takes precedence over the date in Telethon,
so after a cursor exists use IDs and retain explicit date checks on every message.
The declared after_id is still the batch envelope's starting position.

Track the last scanned ID separately from the last fully prepared record. Validate
peer and monotonically increasing legal IDs before filtering. Require a usable SDK
datetime for window selection (naive SDK dates retain the existing UTC convention).
Skip dates before start; stop before the first date >= end in the SDK's chronological
history order. Never download media for filtered messages. Null/invalid dates raise
with the existing complete prefix rather than guessing membership.

A full SDK iterator containing excluded lower-bound records is not exhausted
history: continue from its last scanned ID with the remaining output capacity.
Only a genuinely exhausted iterator, upper-bound crossing or maximum ID yields end.
If the requested number of records is prepared, return limit without a lookahead.
This can require additional requests for excluded records; those spend normal budget.
No whole-history DataFrame or unbounded-memory fetch is introduced. An arbitrary
nonzero initial cursor below the window can cost extra scans; the zero-cursor initial
window uses date positioning. Budget exhaustion is never converted to end.

Keep MessageBatch v1 unchanged. Its end reason additionally describes reaching the
explicit query's end boundary. Nonempty end results still require acknowledgment.
### Output
Direct bounded history reads with exact half-open UTC selection and safe prefixes.
### Safe in nature
False — existing reader loop and public signature are extended.
### Peripheral concepts
Telethon1.45 _MessagesIter, BudgetClientMixin, record/media preparation, health.
### Hardness Lvl
3

## Step 3 — persist the window in continuation
### Proposed changes
Extend initialize_sync and SyncEngine.initialize with start_date=None,
end_date=None, last_days=None, retaining required after_id and existing media_mode.
Allow either both explicit dates, a positive integer last_days, or neither. Reject
mixed/incomplete/naive/invalid input. These are local SyncConfigurationError failures.
Use the existing integer validation for days (1..2147483647), then catch timedelta,
datetime and date-range overflow as configuration errors.

Validate request shape, then load existing state before reading the clock. Matching
relative initialization compares the stored last_days, initial cursor and media
mode, returning existing dates/state even tomorrow or after clock rollback. Matching
explicit initialization compares normalized dates plus the same seed/mode. Switching
input form, changing any constraint, adding/removing a window, or changing the initial
cursor/mode raises SyncConflictError. No reset/re-arm behavior. New relative enrollment
observes datetime.now(timezone.utc) once, resolves both bounds, and atomically saves.

Add optional window and window_days to internal _State. Daily records remain exact
version1 bytes; window records use version2 with exactly one additional window
object: {start_date, end_date, last_days}. last_days is nullable and, when present,
must equal the stored duration. Decode each version with strict keys/types and
retain all existing source/cursor/ack invariants. v2 without a valid window refuses;
v1 containing a window refuses; no migration or rewrite on load. SQLite table/schema
version and custom backend's opaque-text load/CAS interface do not change. Old code
refuses v2 rows rather than silently using them without dates.

Append optional start_date, end_date and last_days fields to SyncStatus. They are
immutable UTC datetimes/int/None. to_dict retains exactly the old daily keys and
adds canonical start_date/end_date/last_days only for window records.

prepare passes the saved dates to get_message_batch only for window records, leaving
the default call signature unchanged for existing injected readers. Validate all
pending message dates against the window both before publication and on decode,
including complete interrupted prefixes. Missing/out-of-window dates are local
SyncStorageError failures. Existing acknowledgment replace operations preserve window
fields without clock reads; offline replay uses exactly the stored batch bytes.

No persistent done field: end/None describes exhaustion visible to that call under
the fixed query. Planned-job completion/pacing/re-arm belongs to a later slice.
### Output
Durable fixed queries through the existing enrollment/prepare/replay/ack contract.
### Safe in nature
False — extends strict state decoding and initialization/prepare behavior.
### Peripheral concepts
conditional persistence, query identity, status compatibility, pending integrity.
### Hardness Lvl
3

## Step 4 — offline regressions
### Proposed changes
Create tgdata/smoke_tests/test_23_fixed_windows.py using the existing SDK transport
fixtures and real SQLite backend, with sockets forbidden and no real account config.
Exercise at least these behavioral groups:
1. Explicit UTC/offset normalization, half-open bounds, invalid inputs before I/O.
2. First date seek and repeated timestamps across SDK pages and caller batches.
3. All-excluded full pages do not produce false empty/end, including fractional starts.
4. Upper bound excluded before media download; empty/exact-limit/end/max-ID behavior.
5. Nonzero cursors intersect the window; ID gaps do not lose progress.
6. Relative enrollment stores one clock observation, restart/repeated setup never rolls it.
7. Conflicting/mixed/naive/overflowing initialization preserves prior state.
8. Actual SQLite reload, offline exact replay, duplicate/wrong ack and date preservation.
9. Real budget exhaustion after included and excluded slots; prefix publication/resume.
10. Original read errors and failed prefix persistence retain both failure meanings.
11. v1 byte-for-byte unchanged; unsupported/malformed window and pending rows refuse.
12. Daily/historical separate stores keep independent bookmarks and query identities.
13. Media prefix/replay and omitted-date behavior retain existing contracts.
14. Store commit-then-error/cancellation at enrollment reloads the original frozen dates.
15. Missing dates/out-of-window reader output cannot enter pending state or report recovery.

Use actual SDK iterator/request construction, not a fake iter_messages. Synthetic
server replies establish local composition only. Reuse test22 fault wrappers and
actual process-exit ack test with window state where possible; preserve expected
behavior of previous tests. No 1.33.1 or live Telegram run.
### Output
A standalone offline suite and reproducible boundary/restart evidence.
### Safe in nature
True — isolated tests/temporary artifacts; no production behavior change.
### Peripheral concepts
fault injection, SQLite transactions, request boundary counts, receiver assertions.
### Hardness Lvl
3

## Step 5 — public docs
### Proposed changes
Add docs/fixed_windows.md with explicit/last_days enrollment, restart usage through
sync_group, caller acceptance before ack, frozen dates in status and independent
stores for daily/history. Show the backend creates its SQLite file in an existing
parent directory. Explain input-form idempotence/conflicts, wire date limits,
no permanent completion/scheduler, and visibility/failure boundaries.

Update README with a compact linked example, docs/daily_continuation.md to describe
the optional window extension, docs/message_batch_v1.md to document the optional
query and end meaning (wire unchanged), and smoke_tests/README.md with test23.
Keep legacy DataFrame date semantics unchanged; point specifically to the batch API.
### Output
Reviewable usage and exact API/storage compatibility contract.
### Safe in nature
True — documentation only.
### Peripheral concepts
caller archive ownership, public status, repeat-safe delivery, future backfill.
### Hardness Lvl
2

## Step 6 — verification and checkpoint
### Proposed changes
Compile changed Python and check Python3.7 grammar; run test23, then the complete
supported offline suite: test22,19,18,17,16,15,14, test13 and12 with an explicitly
nonexistent config (live checks skipped), and only test11's pure helper cases.
Run the existing offline daily example. Verify imports come from this worktree and
Telethon is1.45.0. Examine failures; only local nonarchitectural corrections permitted
under task-impl, each recorded. Never change expected outcomes to hide a failure.

Commit runtime/tests/public docs together, work-folder verification/implementation
notes separately. Stage named paths only; duncan and original #7 stay untouched.
Push the feature branch and update only #18's fixed-window status after committed
checkpoints. Preserve the daily-delivery checklist and original request. Leave
merge-check, PR and fresh PR critique pending; no merge and no close of #18.
### Output
Recorded verification, committed implementation, accurate #18 status.
### Safe in nature
True — verification and explicit feature-branch checkpoint; no merge/deployment.
### Peripheral concepts
supported offline suite, archival branch, contribution gates.
### Hardness Lvl
2
