---
model: gpt-6-astra
effort: xhigh
---
# #45 implementation plan — revision 2

**Critic folded:** 2026-10-16T08:12:16Z —2 robust mitigations,3 steps changed(2,3,5),0 added. Combined prebuild PASS before every product step.

### What is the task
Provide bounded history content distributed across UTC days and reproducible local raw-message selection. The caller retains a portable capture, chooses explicit eligible IDs and obtains a smaller sample with honest source/omission evidence. Preserve existing activity/batch/progress/account contracts. Basis: desc.md and concluded traverse/finding.md, dev77f2f53, Telethon1.45.0.

### Huge Hard Blockers
#### Planning Blockers
None identified. Source projection, day seeking and shared-validation composition are locally testable; no external premise prevents planning. No parked/rejected earlier #45 plan exists. Required behavioral prebuild remains before productstep1, not waived by code inspection.
#### Execution Blockers
None for required implementation/offline verification. Optional live comparison needs established exclusive session and authoritative allowance; not currently established. It does not gate required steps and will be reported not run if unavailable.

### How this implementation moves toward desired state
Extract the small structural page validator from activity, add an independent capture/sample value and one bounded day collector, then expose a verified-account capture method. Local selection is independent of source work. No progress engine, strategy registry, archive or callback runtime is introduced. Shared validation preserves #44's behavior and keeps content/counter projection separate.

### High-Level Summary
| Step | Description | Expected output |
|---|---|---|
| 1 | Share structural history-page validation | Small private validator; unchanged activity behavior |
| 2 | Define portable capture and deterministic sample values | Strict replayable input and bounded selected output |
| 3 | Collect across days under two source bounds | Native source capture with bucket evidence and partial outcomes |
| 4 | Wire facade and exports | Expected-account public capture method |
| 5 | Test public behavior and document use | Sampling suite47 and public guide/examples |
| 6 | Verify baseline and publish implementation record | Separate product/work commits, pushed branch and honest issue state |

### Mandatory prebuild before product step1
Use work-folder-only prototype/probes over real Telethon1.45 dispatch/TL decoding, existing _account_health_operation, StoredSession, SQLite ReadBudget and SDK cleanup. Source packets may be synthetic; clients, admission and cleanup must be real. Prove per-day exclusive date/ID seeking with equal timestamps; rounds across a busy day and quiet days; empty-day request bound; actual _record projection on decoded ordinary/service/photo/document rows; common page validation parity with #44; deterministic quota/rank arithmetic and canonical reload feasibility; failure/cancellation after prior valid work. Do not treat an arithmetic-only probe or mocked public client as the combined experiment. No product edit until the critic's combined passing conditions hold.

## Step 1 — shared page structure, independent projections
### Proposed changes
New `tgdata/history_observation.py` contains the current activity `_page` structural checks and UTC source-date normalization, parameterized by an internal projection callable(row,date,observed_at) and diagnostic label. Keep response families, positive int32 IDs, peer matching, strict descending IDs/nonincreasing dates, MessageEmpty counting, complete-page validation, local half-open selection and end/start evidence exactly as today. Return the same tuple shape as current activity _page. A row is projected/validated even outside the interval, preserving current whole-page validation semantics.

In `tgdata/group_activity.py`, retain `_page` as a thin delegate with `_message` projection and label preserving existing activity error text. Leave the collector, result fields, counters, timing, source cap, heartbeat and public signature unchanged. Shared validator imports group_operations/history_window primitives, not a facade or collector; avoid cycles. This is reuse by two concrete consumers, not a generalized source engine.
### Output
One private page validator; activity public behavior and serialization unchanged.
### Safe in nature
False — existing activity behavior is touched and needs parity tests.
### Peripheral concepts
GroupResponseError, TL page families, fixed windows, MessageEmpty, source order, activity projection.
### Hardness Lvl
3

## Step 2 — capture value and deterministic local selection
### Proposed changes
New `tgdata/history_sample.py` defines HistorySampleError (local ValueError), immutable HistoryCapture and HistorySample. Follow the existing canonical JSON value pattern: own canonical encoded content, detached getters, supported schema/version, exact keys, duplicate-key/nonfinite rejection and content digest. Use reference-mode raw v1 record validation without adopting MessageBatch envelope/cursor fields. No media bytes, live SDK objects or implicit sender enrichment.

Capture envelope exact fields: schema=`tgdata.history-capture`, version1, capture_id; algorithm=`utc-day-round-robin/v1`; account_id, normalized target, group metadata; start_date/end_date; collection_started_at/collection_finished_at; limits {max_messages,max_requests}; stop_reason; buckets. Dates use canonical UTC microsecond Z strings. Each bucket has start_date/end_date, requests, pages, scanned_messages, unavailable_messages, end_reason (null/window_start/history_end), records (in-window raw v1 records, ascending date then numeric ID). Keep every requested UTC intersection, including unvisited buckets. Services remain records but cannot be sampled. Capture ID hashes the canonical envelope excluding capture_id, including observation times and actual evidence; identical selection input means this retained value, not a new query.

Constructor/reload validates: aware fixed bounds and canonical day partition; positive verified account/int64 group identity/namespace and supported kind; safe normalized target (including hashed invite label); valid text metadata; count types/ranges;0<=pages<=requests and unavailable<=scanned; records<=scanned-unavailable; no records/evidence in unvisited buckets; terminal end evidence requires an accepted page; record dates inside their bucket; globally unique IDs; canonical ordering; no downloaded blobs; exact digest. Recompute aggregate counts/coverage instead of storing contradictory duplicate flags. Normal results have every logical call accepted; on error/cancellation at most the current call may lack an accepted page. Finished means every bucket has end evidence, not that every slot was readable. Message/request-limit stop requires the respective bound and some unresolved bucket. Error/cancelled never implies global completeness. Per-bucket completeness requires terminal evidence and zero unavailable slots.

Source max_messages: integer1..10000, default3000. max_requests: integer1..10000, default100, counts logical GetHistory attempts (not authentication/identity metadata calls or a network-packet count). Limits are independent of ReadBudget. The finite supported wire-date interval bounds bucket metadata; no additional arbitrary max-days setting. These are count/work bounds, not byte/RSS promises. `HistoryCapture.from_json(data, max_bytes=64*1024*1024)` checks input bytes before JSON parsing and exact count/schema consistency; callers may explicitly raise the reload byte policy for a retained larger capture. Reload failure never initializes new state. Native capture/selection does not silently truncate text to fit this loader policy.

Expose capture_id, account_id/group/window, messages (detached flattened raw records), buckets (detached), stop_reason, derived coverage_complete/source counts, to_dict/to_json/from_json, and `.sample(size=300, eligible_ids=None)`. A saved sample is output, not valid capture input. HistorySample is created by sample(), exposes immutable canonical output/to_dict/to_json, messages and selected_ids; no independent sample loader is required because replay uses the capture plus policy. No implicit storage helper.

Selection accepts plain integer size0..10000; eligible_ids is None or a concrete list/tuple/set/frozenset of canonical decimal-string or plain positive int32 message IDs, bounded by10000 input occurrences. Normalize duplicates/order into a numeric-sorted set; reject unknown/service IDs. None means every ordinary captured message; empty means none. No predicate callback parameter. Caller predicate failures occur before sample() and cannot alter capture or source health.

[folded: Risk 2, robust] Handle target0 and full selection directly. For partial selection restrict the integer search level to [0,max(day_capacity)] and use terminating integer binary search; there is no unbounded largest-level search.

Build eligible per-day lists in ascending date/id order. Target=min(size,total eligible). Allocate equally via water filling: find the largest integer level L with sum(min(day_capacity,L))<=target, then add one to an evenly spaced subset of days with remaining capacity for the residual. This redistributes sparse-day capacity without a days×messages loop. Even-index helper: k0 empty; k1 floor((n-1)/2); k>=2 indices floor(j*(n-1)/(k-1)), j0..k-1. Use the same helper to choose remainder days and within-day message ranks. Output chronological date/id order. Algorithm=`utc-day-even-rank/v1`, sampling_unit=`raw_message`; no randomness/seed or representativeness claim.

Sample envelope retains schema/version/sample_id, algorithm/unit, capture_id, account/target/group/window, source summary and per-day source/selection metadata, policy {size,eligible_ids}, selected raw records and selected-album metadata. Metadata includes captured ordinary/service counts, eligibility exclusions, eligible/selected/omitted counts and unvisited/incomplete source facts. For each selected grouped_id report all captured ordinary member IDs, selected IDs and omitted captured IDs; membership remains unconfirmed. No photo-trail inference or whole-album promise. Hash the entire canonical sample excluding sample_id; no selection-time clock in the payload, so identical retained input/policy gives identical bytes/hash. Avoid duplicating unselected bodies in sample output.
### Output
Portable replayable capture and deterministic, bounded, traceable selected output.
### Safe in nature
True — additive pure value/selection module before public integration.
### Peripheral concepts
canonical JSON/digests, raw v1 records, UTC partitions, raw/album unit semantics, caller eligibility, immutable data.
### Hardness Lvl
4

## Step 3 — bounded day-distributed capture
### Proposed changes
New `tgdata/history_capture.py` uses shared page validation, `_HistoryWindow`, `_resolve` and batch_engine._record/_validate_record. After resolution refuse unsupported/minimal/invite-only peers; validate capture metadata before the first history call. Create every UTC day intersection. Mutable internal bucket state also tracks last ID/date for pagination; these live continuation details are not resumable receipts in the saved value.

[folded: Risk 1, robust] On a bucket's first visit, request1 slot when remaining_requests exceeds remaining planned visits in that round, preserving room for a depth pass. With no spare request opportunity, retain the fair bounded page size. All later visits use the fair rule. Empty buckets then consume one boundary witness where another pass is affordable.

Each round takes unresolved buckets in chronological order. Let k=min(number active,remaining message slots,remaining logical requests); choose evenly spaced k active bucket indices when a whole round cannot fit. Give each chosen bucket one page. Request limit=min(100,max(1,remaining_slots//remaining_visits_in_this_round)). Recalculate remaining slots after each accepted page; quiet/empty days free capacity for later visits/rounds. Before each call increment that bucket's logical attempt count; never exceed max_requests. Source slots count all rows in accepted pages, including services, placeholders and out-of-day boundary rows. A refused/failed/invalid current page stops the operation; its attempted work may be charged but does not join accepted observation counts.

First request for each bucket uses ceil(end to wire second), offset_id0, add_offset0,min_id0,max_id0,hash0. Later requests use last raw ID and offset_dateNone. Shared validator supplies strict order/peer checks and end_reason. The content projector calls existing _record(row,client), validates the reference-mode record and returns it. Only in-bucket records are retained; record IDs already retained in another bucket raise GroupResponseError. Validate all prospective page content before changing accepted bucket data/offsets. Unknown slots prevent that bucket's completeness but do not prevent finite continuation; terminal evidence ends it even if incomplete.

Stop normal capture with finished when all buckets have terminal evidence, otherwise message_limit before request_limit when both bounds are reached. Unvisited buckets keep zero evidence/end_reasonNone, and unfinished visited buckets remain distinguishable by requests/pages. On original source/local failure or CancelledError, create a capture of accepted pages only with stop_reasonerror/cancelled and attach best-effort error.partial_result, then bare raise. No source retry, new error wrapper, fabricated complete selection or recovery reset. Preserve the original error even if annotation is refused. Errors before a valid resolved metadata observation have no partial capture.

Emit `history page done` after accepted pages through existing guarded heartbeat; no fake timer through an unanswered call. No user callback executes as a selection predicate. Global capture result is constructed before existing cleanup; cleanup/cancellation semantics remain the current verified-operation contract, not a durable capture receipt guarantee.
### Output
Finite native capture spanning requested days with explicit source evidence and original failure outcomes.
### Safe in nature
False — new actual source/admission/liveness composition.
### Peripheral concepts
SDK date/ID pagination, per-day rounds, logical-call bound, source allowance, page atomicity, partial evidence, cancellation.
### Hardness Lvl
4

## Step 4 — facade and exports
### Proposed changes
Add `TgData.capture_group_history(target, *, account_id, start_date, end_date, max_messages=3000, max_requests=100, heartbeat=None) -> HistoryCapture`. Parse/normalize target and validate expected account, both aware bounds (1970..wire maximum and end<=invocation time), limits and heartbeat before config/client I/O. Enter heartbeat_scope then `_account_health_operation(account_id,'capture_group_history',reference.label)` and call the private capture collector. Do not confirm_group_access or mutate persistent selection/pool. Export HistoryCapture/HistorySample/HistorySampleError; no package version bump or new dependency. Existing sample-unrelated signatures unchanged.
### Output
One expected-account capture method and pure replay/selection values.
### Safe in nature
False — facade/package integration.
### Peripheral concepts
expected owner, existing health attribution, proxy/device/session policy, temporary lifecycle, public imports.
### Hardness Lvl
3

## Step 5 — tests and public documentation
### Proposed changes
[folded: Risk 1 and Risk 2, robust] Add the60-day sparse-history case (59 empty requested days plus599 messages on one day), requiring599 captured/300 selected within100 calls and fewer than1000 returned slots; cover no-spare-request and tiny-cap branches. Exercise empty/all-zero/full/partial quota populations with conservation/capacity/deterministic remainder assertions.

Add `tgdata/smoke_tests/test_47_history_sampling.py` on real SDK/TL/SQLite fixtures34/46, with sockets/login forbidden. Include source-side offset models with per-day datasets and separate expected selections, not only supplied desired outputs. Cover599/300 endpoints, one busy day among quiet days, sparse quota redistribution, sample size0/less-than-days, exact/fractional/UTC-offset bounds/ties, empty requests, explicit caps, MessageEmpty, malformed/duplicate/wrong-day data, metadata refusal, raw services/albums and omission reports, full text preservation and detached immutability.

Replay: capture JSON round trip; repeated/reordered/duplicate eligibility yields identical sample; no source request during selection/load; reject duplicate JSON keys/nonfinite/unknown keys/wrong hash/rehash of inconsistent evidence, changed window partition, impossible counts, conflicting IDs, unknown/service eligibility and oversized input. Source budget refusal/storage failure/auth change and source/local failures preserve prior captured days; cancellation while a later day waits and repeated cleanup cancellation remain cancellation. Callback failure stays isolated. Activity's existing tests46 and full public value outputs stay compatible after shared extraction.

Add docs/history_sampling.md and README/smoke README entries with a two-action example, explicit topic-ID filtering, serialization/replay, defaults/bounds/day and rank algorithms, source coverage versus sample omissions, raw/album/trail limits and failure/health semantics. State loader byte policy versus native count bounds, bias/nonrepresentativeness, no fresh-query replay or acknowledgment authority. No new live demo or downstream consumer edit required; meaningful suite exercises the full public path.
### Output
Permanent public-path tests and precise caller guide.
### Safe in nature
True — tests/docs additive; existing fixture behavior remains unchanged unless a small recorded helper correction is necessary.
### Peripheral concepts
SDK codec fixtures, deterministic arithmetic, strict value reload, source evidence, existing assembly and progress compatibility.
### Hardness Lvl
4

## Step 6 — verify and commit
### Proposed changes
Compile/check Python3.7 grammar, run new47 then relevant23/32/33/34/42/43/44/46 suites, then all supported12–19/22–47 (34 suites) and seven offline demos. Use Python3.11.10/Telethon1.45.0. Live12/13 cases receive deliberately missing config; local loopback fixture may need escalation. Adapt prior44 verifier with suite47 and source hashes; no native3.7 or live claim from grammar/synthetic packets. Record every verification correction without weakening expectations; architectural failures stop this task-impl run.

Review diff/check actual unchanged batch/progress/assembly/policy files and #44 parity. Commit code/tests/public docs together; work records separately. Push branch and update issue45 committed steps through5 with evidence and qualification comment. Keep mergecheck/PR/freshPRcritic for a later explicit request. No release/tag/deployment. Preserve original checkout, duncan and unrelated guide/version edits.
### Output
Verified committed/pushed implementation with honest evidence and next review handoff.
### Safe in nature
False — publishes commits/status; limited to authorized task workflow after verification.
### Peripheral concepts
987-check baseline plus new tests,34 suites/seven demos, GitHub pipeline records, separate archival development docs.
### Hardness Lvl
3
