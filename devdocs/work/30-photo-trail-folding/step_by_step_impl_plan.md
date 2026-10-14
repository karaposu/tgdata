---
model: gpt-6-astra
effort: xhigh
---
# Implementation plan — optional photo-trail views (#30), revision1

Explicit input: desc.md at570cc7d, triage.md, traverse/finding.md and its preserved two-pass evidence. Baseline dev35c4362. No previous plan or rejected PR critique exists for #30. Product code has not started.

### What is the task
Offer an optional conservative relation between a user's original text/album and following photo-only posts. Preserve every original TelegramPost and raw member, expose a replaceable provisional view, and demonstrate restartable use with the existing caller-owned receiver. The selected scope and original-message timeline must not hide known activity or change source acknowledgment semantics.

### Huge Hard Blockers

#### Planning Blockers
None OPEN. The inherited scope/ordering question is CLOSED: selected stored intervals must contain each selected post's entire known observation, otherwise refuse; original member events determine interruptions. Confirmed by traverse's actual selection counterexample, nine contract histories and two fresh backfill/WAL histories. These establish the contract, not complete implementation correctness. Source: desc.md and traverse/finding.md. Resolved locally through full code reads and actual component probes; no human-only answer remains.

#### Execution Blockers
None identified. #29 is merged. Local Python3.11.10/Telethon1.45.0 and SQLite are available. No live Telegram, additional account, deployment or external store is required to implement this provisional observed-data contract. Full candidate qualification is a required ordering gate, not an unavailable external dependency.

### How this implementation moves toward desired state
Add one pure module with a validated policy and versioned current-view value. The rule consumes existing original posts; it does not extend their wire format or own source progress. Add an optional example that reads a bounded coherent snapshot from #29's existing immutable-record receiver, then calls the pure helper after closing the read transaction. The old receiver's schema and acceptance path remain byte-identical. Tests and documentation cover both the pure inference and actual storage/source composition.

### High-Level Summary

| Step | Description | Expected Output |
|---|---|---|
| 1 | Define policy and immutable view contract | Validated public values and strict serialization |
| 2 | Implement deterministic member-event inference | Opt-in pure fold with explicit conservative barriers |
| 3 | Compose bounded receiver reads and demo | Strict current-scope view; unchanged original acceptance |
| 4 | Add behavioral tests and public documentation | Complete offline suite43, guide and example usage |
| 5 | Verify and commit product/evidence separately | Full regression evidence; ready for later merge check |

## Mandatory complete prebuild before production Step1

After fresh critic-d and its selected fold, build the **entire** proposed module, exports, example and suite43 in an isolated temporary package based on dev35c4362. Run the complete new suite and relevant existing raw/album/daily/window/backfill/pool suites, plus the new demo, before adopting any candidate file into product paths. The inquiry's contract_probe.py is deliberately incomplete and cannot satisfy this gate.

Use real Telethon1.45 values/serialization, existing TelegramPost, actual candidate public constructors/loaders/fold, actual SQLite schema/open/read/preflight/cleanup and real daily/backfill engines. Include all critical histories below together: late caption withdrawal; unknown late album member; same-user overlap; exact gap/span/count limits; list/arrival/partition invariance; malformed forged view; raised10001-member reload and getters; closed-scope counterexample; aggregate/key/byte preflight; foreign-collation exact namespace; missing/corrupt known data; consistent WAL snapshot; original acceptance independently replayable after scope/view refusal; actual source receipts, lost ack/reply, cancellation and child-process loss.

Passing result: complete actual candidate satisfies the stated behavior, preserves every original record and existing receipt authority, enforces bounds without partial output/hidden context, and passes all retained regressions. Record hashes for every candidate product source and exact run output. Disqualifying result: the selected current-view/closed-scope/member-event contract itself cannot satisfy these guarantees without another ownership, scope or ordering rule. Stop and return to the contract; do not silently change semantics or weaken assertions. Local prototype/fixture wiring corrections may be recorded, but do not call targeted probes a complete gate.

## Public Contract Fixed for This Plan

### Policy
`PhotoTrailPolicy(enabled=False, gap_seconds=30, max_span_seconds=120, max_photos=20)` is frozen. enabled is a plain bool. All three integer fields are plain positive ints at most MAX_MESSAGE_ID; bool, float, strings, zero and negatives refuse. The gap and span use exact timedelta comparisons, including microsecond boundaries. Span is measured from the anchor's last original member to the last attached photo; max_photos counts attached raw photo messages, excluding the anchor's own media. `to_dict()` returns a copy; `from_dict()` validates exactly these four fields. Defaults are explicit conservative policy assumptions, not calibrated intent guarantees.

### Pure operation
`fold_photo_trails(posts, *, policy=None, max_members=10000, max_bytes=16777216)` accepts a concrete list/tuple of TelegramPost values. None policy means the disabled default. No generator/hidden input stream is consumed. Validate the selected policy and positive plain-int resource limits before work. Reject wrong element types and invalid values; revalidate original post wire data with the selected limits.

Identical duplicate post observations may deduplicate; differing current observations of one post ID refuse. A raw(chat,message) identity cannot appear in two different posts. Different original posts may retain different media modes. Canonical original order is `(numeric chat_id, first member ID, post_id)`, independent of argument order. No source fetch, storage, clock, acknowledgment or callback is performed.

`max_members` bounds inspected input member occurrences, including duplicated supplied observations, and the retained unique output members. `max_bytes` bounds the sum of every supplied post's canonical UTF-8 JSON plus the resulting view's canonical UTF-8 JSON. Check encoded input amounts before decode, input-list length before walking, aggregate member counts during validation and output size before return. Limits refuse the whole operation; they do not imply a process-RSS bound. This computation is not durable receipt confirmation.

### Immutable view, version1
`PhotoTrailView(document, *, max_members=..., max_bytes=...)`, `from_json(text_or_bytes, ...)`, `to_dict()` and `to_json()` follow the existing immutable-value style. The exact top-level fields are:

`schema`, `version`, `revision`, `algorithm`, `policy`, `status`, `posts`, `groups`, `folded_posts`, `folded_photos`.

Values: schema=`tgdata.photo-trail-view`; version=plain integer1; algorithm=`same-user-photo-trail/v1`; status=`provisional`; policy=the four exact fields above; posts=unique canonical ordered original TelegramPost v1 documents, each retained once; groups=ordered objects with exactly `anchor_post_id` and `post_ids`, where post_ids begins with its original anchor. Every original post occurs in exactly one group. Groups are ordered by their anchor's canonical source order. folded_posts counts nonanchor original posts; folded_photos counts their original photo messages. Both counters are plain nonnegative ints. A disabled policy yields one original post per group and zero counters.

revision is lowercase SHA256 of canonical JSON excluding revision, covering policy, original observations and relations. A loader checks exact keys/types/schema/algorithm/status, all nested originals, uniqueness/order, policy, counters and revision. Recompute the expected relation under the saved policy and require it to match groups/counters: a rehashed forged link is still invalid. Reject duplicate JSON keys, nonfinite values, bad UTF-8 and unsupported revisions.

Expose `posts` as a tuple of immutable TelegramPost values, `groups` as tuples of original post-ID tuples, frozen `policy`, revision/status and both counts. Cache only immutable tuples/frozen values/strings, never return a mutable internal document. Store validated post objects with the view so getters do not reload them under default10000 limits after a deliberately raised-limit load. repr must not expose message contents. Equality/hash may use canonical encoded content; mutable decode copies are never authoritative.

The single-view constructor/JSON loader bounds its encoded view size and total retained members; the fold's separate input+output work formula is not reapplied as a loader cost. All error paths use `PhotoTrailError`, a local ValueError with suppressed incidental exception context; no content logging or Telegram health event.

### Inference rule
Precompute each post's complete metadata from its original members. An eligible owner exists only if every member names the same positive user ID. A usable post consists of ordinary messages, has dates for every member and has nondecreasing dates in original-ID order. Text means nonempty after whitespace stripping. An anchor has text or an actual non-null Telegram grouped_id. A follower consists solely of ordinary textless photo-kind records; whole photo-only albums qualify atomically.

For each known user/chat, mark every post in a connected overlap of original-post ID intervals as unsafe. Separately inspect original events for that known user; any post containing a date earlier than the maximum previously observed known timestamp is unsafe. Missing dates are unsafe. These determinations happen before inference so later evidence can invalidate an earlier guess.

Traverse all original members by(chat, numeric message ID). Unknown/mixed/nonpositive owners clear all active anchors in that chat at each of their member events. Unsafe known-user posts clear that user's anchor at each event. A valid non-follower clears the user's previous anchor at its first member. Other positively identified users remain independent.

At a valid post's last observed member, consider it for atomic attachment. A follower needs an active prior anchor with all chain member IDs earlier than it. Every follower member's reply is absent or targets an already known earlier chain/candidate member. Check each nonnegative gap, total span and all candidate photo messages against remaining count; no partial post attaches. Success extends the original anchor's group and chain. Failure clears the old chain; the original post stays separate. A separate eligible text post or Telegram album may become a new anchor at its last member. An uncaptioned singleton does not start an anchor. Recompute from scratch for each full current view; no persisted inference state or finality timer.

## Step1 — Policy and immutable view

### Proposed changes
Create `tgdata/photo_trails.py` with PhotoTrailError, frozen PhotoTrailPolicy and frozen PhotoTrailView. Reuse existing canonical JSON/identifier/digest/date/post validation helpers where their error contracts are translated correctly; do not modify MessageBatch or TelegramPost. Implement strict serialization, limits, immutable caches and canonical original/group ordering described above. Define the private relation interface for Step2 so the loader can validate computed groups without circular imports. Add four exports (the three values/error plus fold_photo_trails) at the end of `tgdata/__init__.py`; leave version0.1 and existing signatures unchanged.

### Output
Versioned immutable policy/view values with safe reload under explicitly selected bounds, ready for the pure relation algorithm.
### Safe in nature
False — a new public format and import surface require exact validation and compatibility checks.
### Peripheral concepts
TelegramPost v1, canonical JSON, raw peer identifiers/dates, resource limits, immutable getters, local health-neutral errors, package import/discovery.
### Hardness Lvl
4

## Step2 — Pure event-based folding

### Proposed changes
In the same module, implement bounded input validation/deduplication, metadata/overlap/chronology passes, original-member event traversal and canonical group/counter construction. One private deterministic rule supplies both fold output and loader relation validation. Build only bounded per-call structures; no history cache, callbacks or I/O. Preserve byte-identical originals. Keep construction and inference code separate enough to avoid repeated whole-value getter decoding inside member loops; caches remain immutable outside the call.

### Output
The exact opted-in rule and disabled behavior, with deterministic complete-view results, reversible late-observation changes and no source/persistence side effect.
### Safe in nature
False — incorrect attachment can misrepresent a caller's posts despite immutable originals; chronology and bounds need adversarial cases.
### Peripheral concepts
Original member chronology, per-user source intervals, unknown-author barriers, photo/reply evidence, multiple captions, late albums, bounded current views, policy revisions.
### Hardness Lvl
4

## Step3 — Bounded SQLite composition and runnable example

### Proposed changes
Add `examples/photo_trails.py`, importing the existing AlbumReceiver without modifying its file/schema/acceptance. Expose example helper `load_photo_trails(receiver, chat_id, *, after_id, through_id, policy=None)`. Validate plain integer canonical negative chat ID and `0 <= after_id <= through_id <= MAX_MESSAGE_ID`, policy, and receiver limits before opening. Use the selected receiver's max_members/max_bytes throughout loading and fold; callers can reopen a separate reader under an adequate policy, as in #29.

One read transaction validates existing schema/collection, counts selected rows and encoded post-key bytes/type validity before materializing keys, and finds distinct post keys using explicit BINARY collation. For each selected key, obtain count/record-byte preflight and original ID extents, reject cross-chat/type inconsistencies, and refuse if any known member lies outside `(after_id, through_id]`. Accumulate all selected member/byte lower bounds before any payload read. Confirm selected counts agree; do not let a collation alias or malformed key silently omit a selected row. Load through the existing validated `_load` path with incrementally remaining byte capacity and actual post-JSON accounting. A missing post after selection is inconsistent state, not None. Close the read transaction before pure folding to avoid holding a database lock during computation.

Return PhotoTrailView only after successful loading/close and fold. No DML, inferred marker, schema migration or data repair. Exact collection/key comparisons must not inherit foreign NOCASE columns. Existing `_open` cleanup precedence is reused. A storage, scope or view-limit failure leaves the saved original facts/receipts unchanged.

The `--demo` path blocks sockets, creates explicit temporary receiver/progress stores, uses the actual SyncEngine, loses an acknowledgment, reopens/replays, accepts later photos and shows current groups. Demonstrate a later follower-album caption withdrawing an association. Source acknowledgment uses only the original delivery; a view failure does not invalidate durable data. The example is callable repository code, not a mandatory installed backend, deployment or migration.

### Output
A concrete portable use of retained originals across calls/restarts, with strict closed-scope and consistency behavior.
### Safe in nature
False — the example teaches durable integration; selection or acknowledgment mistakes could mislead consumers.
### Peripheral concepts
AlbumReceiver schema2/validation, SQLite snapshots and BINARY comparisons, metadata preflight, raw receipt identity, daily/backfill replay, failed cleanup, caller scope and media custody.
### Hardness Lvl
4

## Step4 — Behavioral tests and documentation

### Proposed changes
Add `tgdata/smoke_tests/test_43_photo_trails.py`, socket-blocked and runnable directly/module-wise without work-folder files or Git metadata. Use actual Telethon1.45 serialization/_record fixtures and real TelegramPost/receiver/source classes. New fixture messages use unique IDs; preserve the old consumer discrepancy as explanation, not as an expected library duplicate.

Cover these behavioral groups with explicit expected outcomes rather than source-text assertions:

- Exports/default-disabled behavior; policy validation/frozen copies; text→photos; album→photos with multiple captions; whole photo-only follower albums and distinct count units; two interleaved users/chats; anonymous/channel/mixed users; unknown late album-member barrier; same-user overlap; null/backward dates; new text/nonphoto/reply barriers; replies to known earlier chain/candidate members versus unknown/future targets; exact microsecond gap/span and atomic count limits; no reverse photos→text.
- Late caption/identity/extent updates withdraw links without changing prior values; fixed observation-set order/partition/arrival invariance; exact duplicate inputs versus conflicting revisions/raw identities; concrete input type and bounded duplicate visits; immutable view getters/repr; strict/canonical JSON, large IDs and both original media modes; rehashed forged associations/policy/counters/order refuse; exact UTF-8 work/value bounds;10001 accumulated members with deliberately raised limits survive serialization/getters/reopen while stricter bounds refuse.
- Closed interval success/empty/invalid/split cases; the exact hidden-text counterexample; known missing/corrupt state and malformed selected key/digest/row metadata; separate collections and foreign NOCASE declarations with BINARY indexes; count/key/record lower bounds before payload and actual prior JSON accounting; consistent WAL reads during growth; zero DML on view generation; contention and primary/cleanup error precedence; old raw confirmation remains valid after view refusal.
- Actual daily and backfill receipt replay/restart, late observation updates, source publication/read failure/cancellation without invented receipts, and process loss after receiver commit before ack/view. Keep source call counts, exact batch bytes, source cursor/pending, original rows and current view observations separate in assertions. Exercise the new executable demo and isolated package import.

Add `docs/photo_trails.md` specifying the exact policy, value fields/properties, provisional full-view replacement, observed-scope limitation, closed interval refusal, atomic follower/chain versus whole-operation caps, caller media/data custody and source ack order. Include pure/default/enabled examples and the optional receiver composition. Update README and smoke README with the new opt-in capability/commands and actual case count. Explain the intentional old-helper differences and that consumer adoption is later work. Preserve #29 docs except a needed additive link, if used; no existing semantics change.

### Output
Complete suite43 and clear public contract/demo documentation tied to actual behavior and declared limitations.
### Safe in nature
True — tests/docs only in this step; no independent production behavior change or live calls.
### Peripheral concepts
SDK fixtures, original observation identity, deterministic relation oracle, SQLite/process faults, source recovery, reference/download custody, documentation accuracy.
### Hardness Lvl
4

## Step5 — Verify, commit and report

### Proposed changes
After the complete candidate passes, adopt the exact qualified product files, record hashes and any local nonarchitectural fixture/wiring corrections, then run focused suite43/demo and relevant integrations. Run all29 existing supported offline suites12–19/22–42 plus suite43 and all seven demos. Use missing config for optional live proxy/device checks, report actual executed counts separately from skips, and bound each subprocess with a watchdog. Use Python3.11.10/Telethon1.45.0. Compile all package/examples and parse Python3.7 grammar; do not claim native3.7 execution.

Verify every old runtime module except additive __init__ exports is byte-identical to dev35c4362, including album.py and examples/album_assembly.py. Run a clean temporary package/archive-shaped check without Git/work notes for the new module/example/tests. Once exact tested bytes are adopted, avoid redundant full-suite reruns without a change/failure.

Commit code/tests/public docs separately from work evidence on feat/30-photo-trail-folding, push the authorized feature branch, and update #30 through step5 only with committed evidence. Keep plan.md as a pointer to this canonical plan; preserve all inquiry/history. No merge, PR publication, release, branch deletion or ScrapeOps migration in this task-impl run. Next separate workflow: merge check→product-only PR→fresh PR critique.

### Output
A verified implementation with reproducible full evidence and honest issue status, ready for the later review gates.
### Safe in nature
True — isolated verification and reversible feature-branch publication; no live/deployed mutation.
### Peripheral concepts
Full regressions, source hash parity, Python compatibility, watchdogs, isolated imports, archive branch/process separation, issue provenance.
### Hardness Lvl
3
