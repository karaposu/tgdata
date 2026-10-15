---
model: gpt-6-astra
effort: xhigh
---
# #44 implementation plan — revision 1

### What is the task
Provide one bounded expected-account operation measuring visible raw messages published in a fixed period. Return raw facts, deterministic descriptive statistics and explicit coverage so an application's capped/failed read cannot look like complete weekly or monthly activity. Basis: desc.md and traverse/finding.md at dev490cf5f, Telethon1.45.0, Python3.7 grammar floor.

### Huge Hard Blockers
#### Planning Blockers
None identified. SDK pages and lifecycle code are available to probe; uncertainty about their combined behavior is executable homework, not an external blocker. No prior rejected #44 plans or parked description exist.
#### Execution Blockers
None for required implementation/offline verification. Live validation is conditional and supplemental: no exclusive session and authoritative allowance currently established. If unavailable, report not run; do not tick a live PASS or open a login prompt.

### How this implementation moves toward desired state
Add a narrow measurement value and collector next to group_profile.py, then expose one facade method using the same verified temporary operation. Keep arithmetic pure over immutable observations. Existing Batch v1, read paths, progress stores and policies are unchanged. Before product step1, exercise the actual composed SDK/codec/SQLite owner/budget/heartbeat path with raw history pages; a failing core premise stops implementation.

### High-Level Summary
| Step | Description | Expected Output |
|---|---|---|
| 1 | Define observation values and deterministic statistics | group_activity.py values and math |
| 2 | Collect bounded raw pages with explicit evidence | private collector and validation |
| 3 | Expose expected-account public operation | facade, exports and cleanup composition |
| 4 | Verify public semantics and document use | test46, public docs and README entry |
| 5 | Run supported regression suites and record delivery | product commit, separate notes, issue status |

### Prebuild before product work
Work-folder script only; no product imports that do not exist yet. Use test34's wire response delivery and real TelegramClient._call/MTProtoSender/TL decoding, StoredSession, SQLite ReadBudget, owner verification, heartbeat_scope and disconnect handling. Socket access forbidden. Inputs are synthetic server packets, never stand-in client/admission/cleanup behavior. Exercise 100+ rows, short pages, MessageEmpty, fractional/equal-second bounds, source cap, wrong owner, budget refusal, second-page source error and repeated cancellation while an SDK operation is pending. Record exact evidence and limits; this proves local composition, not server order or live visibility. Official GetHistory/offsets documentation supplies the server contract; don't label fixture output as live proof.

## Step 1 — immutable observations and statistics
### Proposed changes
New `tgdata/group_activity.py` contains frozen `ActivityMessage` and `GroupActivity`, no external dependencies. `ActivityMessage`: id, kind (`message`/`service`), UTC date, observed_at, sender_kind (`user`/`channel`/`unknown`), sender_id orNone, grouped_id orNone, optional views/reactions/forwards/replies, optional replies_are_comments. Service rows have no engagement population. Grouped IDs serialize as decimal text to preserve signed64-bit values.

`GroupActivity`: schema_version1; account_id/target/group metadata; start_date/end_date; collection_started_at/collection_finished_at; max_messages; scanned_messages, unavailable_messages, pages; stop_reason (`window_start`, `history_end`, `message_limit`, `error`, `cancelled`); coverage_complete; oldest_observed_message_date/newest_observed_message_date among all validated dated source rows; tuple messages containing only in-window observations. No credentials/text/media/SDK entities. `to_dict()` produces detached JSON primitives and ISOUTC dates. Group metadata uses its existing value; target uses normalized safe label.

Pure statistics property derives a fresh dictionary each time; it cannot mutate observations. Ordinary counts and distinct sender-ID sets exclude service rows. Unknown-author messages separate. Latest observed ordinary message date isNone on empty population. All UTC dates intersecting the window appear, even observed-zero dates; daily entries expose their intersection start/end/duration, ordinary count, known-user count, channel-sender count, unknown-author messages. They are observed counts; incomplete coverage never makes them guaranteed zero-activity days.

For each of views/reactions/forwards/replies: known_count, missing_count, sum (None if no known values), mean, median, min, max (None if empty). Zero participates. No arbitrary percentiles, engagement ratio, member ratio, age filter or daily-user scalar. Include window_seconds and messages_per_24h = ordinary_count*86400/window_seconds only if coverage_complete, elseNone. Counter populations cover ordinary in-window messages, with dates allowing caller cohort filtering.
### Output
Portable versioned immutable result and deterministic inspectable arithmetic.
### Safe in nature
True — new isolated module, not yet on an existing call path.
### Peripheral concepts
GroupMetadata, UTC bounds, message identity, counter optionality, JSON portability.
### Hardness Lvl
3

## Step 2 — bounded page collection
### Proposed changes
In group_activity.py, validate window with `_HistoryWindow` semantics (aware dates,1970..wire maximum), require both bounds and end<=invocation time. Validate max_messages as a non-bool integer1..2**31-1. Do not allocate a cap-sized buffer. Source requests always limit=min(100,remaining).

Resolve supported group/chat/channel once with `_resolve`. Reject unusable/invite-only preview with GroupReferenceError before history. Initial GetHistory offset_date is ceil(end to whole second), offset_id0, add_offset0, max_id0,min_id0,hash0. If end exact-second use it directly; filter `[start,end)` locally. Continue offset_id=last raw ID and offset_date=None. Do not use min/max filters, since the vendor applies them after slicing.

Accept only messages.Messages/MessagesSlice/ChannelMessages; validate vector length<=requestlimit and every returned row before accepting page. Rows must be Message/MessageService/MessageEmpty with positive int32 IDs, strictly descending across pages; dated rows must have aware UTC dates, nonincreasing across all observed dated rows, valid peer matching requested canonical peer ID, valid author ID when present and nonnegative int32 counters. MessageEmpty may lack peer/date; count unavailable and use its raw ID for progress. Reject MessageNotModified, foreign peers, duplicates/repeats, invalid primitives/order with GroupResponseError. Do not trust reported `count` for completion.

For ordinary messages, reactions absent→None; present MessageReactions with valid ReactionCount nonnegative counts→sum (empty results→0); `min` does not downgrade aggregate counts because it describes personal reaction details. Replies absent→None; present MessageReplies.replies valid→count and comments flag preserved as bool. Views/forwards absent→None; present0 preserved. Known PeerUser/PeerChannel IDs stay distinct; absent or PeerChat sender is unknown, never invented self-ID. grouped_id accepts signed64-bit and serializes text.

Commit page observations atomically into the accumulator: source count includes the whole returned page, even rows below start; remember all dated extrema, unavailable count, pages. Only in-window ordinary/service rows enter messages. Stop `window_start` if accepted page has a dated row<start; stop `history_end` on empty vector or nonsliced messages.Messages (full response). Both give coverage_complete only if unavailable_messages==0. Otherwise continue even on a short page. Stop `message_limit` when cap used without boundary/end proof. Source counts/zero do not infer end. Ordering makes the below-start witness meaningful; docs qualify visibility, no snapshot.

Wrap post-resolution capture in try/except(Exception,CancelledError). On failure build GroupActivity from accepted pages only, stop error/cancelled and coveragefalse; attach as error.partial_result inside a defensive guard, then bare raise. No completed page yet still permits an empty partial observation once target is resolved. Errors before resolution have no partial result. No new exception wrapper, catch-and-return success, recovery reset or retry. Explicit beat after accepted page; request/answer beats already come from existing mixin; no timer while blocked.
### Output
Bounded raw history collector with page-atomic evidence and failure preservation.
### Safe in nature
False — source/budget/liveness behavior must compose correctly despite being a new entry point.
### Peripheral concepts
GetHistory pagination, MessageEmpty, GroupResponseError, verified handles, read budgets, original errors, heartbeat, date precision.
### Hardness Lvl
4

## Step 3 — public verified-account entry point
### Proposed changes
Add `TgData.measure_group_activity(target, *, account_id, start_date, end_date, max_messages=3000, heartbeat=None) -> GroupActivity`. Parse target, validate date/cap/callback and expectedaccount before connection. Enter heartbeat_scope then `_account_health_operation(account_id,'measure_group_activity',reference.label)`. Call private collector on operation.client. Do not call confirm_group_access: measurement does not own restriction recovery. Existing lifecycle handles disconnect, cleanup failure and repeated cancellation. Export ActivityMessage/GroupActivity from __init__; no version bump or existing signature changes.
### Output
One public call over existing owner/admission/cleanup policies.
### Safe in nature
False — facade imports/export/operation composition affect package integration.
### Peripheral concepts
expected_account_id, group reference parsing, owned health, lifecycle cancellation, heartbeat callback isolation.
### Hardness Lvl
3

## Step 4 — public tests and documentation
### Proposed changes
New `tgdata/smoke_tests/test_46_group_activity.py` on actual SDK/TL/SQLite fixture34 with sockets forbidden. Test explicit expected values, not mirrored algorithm: fractions/equal timestamps/endexclusive, complete empty/sparse/dense>100, short page needing another call, exact cap false, empty placeholders, service/album unit, users/channel/unknown, zero/missing counters and changing observations, JSON/frozen/detached behavior, malformed whole-page rejection and preserved prefix, all response types and wrong peers/nonprogress, wrong owner/cached owner/headless auth, budget accounting including raw slots and refusal before send, source failures/health ownership/no recovery reset, heartbeat actual work/callback exceptions/stalled cancellation, cleanup errors and repeated cancellation, invalid inputs before I/O.

Add `docs/group_activity.md` with example, fields/definitions, cap and coverage, error.partial_result usage, observation-time limitations, budget requirement/configuration, read-only guarantees, differences from get_statistics/batches/profiles and no snapshot promise. README group section links it; smoke-test README lists46. No unsolicited demo unless it adds verification beyond suite46.
### Output
Meaningful public-path suite and caller-facing contract documentation.
### Safe in nature
True — tests/docs additive; fixture modifications only if strictly needed and noted.
### Peripheral concepts
real codec fixtures, telemetry, JSON, UTC arithmetic, public API documentation.
### Hardness Lvl
4

## Step 5 — verification and delivery
### Proposed changes
Compile sources and check Python3.7 grammar; run test46 then relevant32/33/34/45/23/44 (heartbeat), then full supported suites12–19,22–46 and seven offline demos. Use current .venv Telethon1.45.0; full12/13 runs with deliberately missing live config to keep three live cases skipped. Local loopback test12 may require escalation; it is not a Telegram call. Adapt prior43 work-folder verification driver with current hashes and suite46 included. Targeted/full duplicate work is limited to required task-impl gates; don't invent implementation-mirroring tests.

Conditional live check only if session exclusivity and authoritative allowance established; otherwise explicitly reportnotrun. Record counts/source revision/runtime/evidence limits and every local verification fix in implementation.md. Verify diffcheck and unchanged v1/progress/policy files. Commit code/tests/publicdocs together; work notes separately. Push archive feature branch, update issue44 committed pipeline steps through5, post qualification description. Leave mergecheck/PR/critic unchecked; no main/dev merge, publish or release in this task.
### Output
Tested committed/pushed feature branch, honest issue state, separate development records.
### Safe in nature
False — commit/push/status changes publish project state; controlled by diff review and explicit workflow authorization.
### Peripheral concepts
full offline baseline952 checks/32 suites+7 demos, Python compatibility, package exports, GitHub pipeline evidence.
### Hardness Lvl
3
