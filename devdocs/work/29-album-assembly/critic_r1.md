---
model: unknown
effort: unknown
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the actual candidate cannot preserve a split album through SDK raw serialization, receiver commit/reopen and existing daily/backfill replay/ack without altering raw identity, guessing completeness or introducing another source lifecycle.
Affordable now: yes — local prototype and temporary SQLite databases, approximately one implementation/testing session; no login, network, spending or deployment.

Experiment: build the exact candidate value/combiner and receiver under the work folder, load them into a temporary package composition with current dev, and run one combined script using actual Telethon1.45 TL serialization/deserialization, actual raw serializer/MessageBatch, actual candidate, real SQLite receiver/SQLiteSyncStore and actual SyncEngine/BackfillEngine. Exercise split/nonadjacent/reverse-arrival albums, all captions/large IDs, duplicate/conflicting prior input, strict reopen and schema failure, atomic rollback/committed-reply-loss/reopen, lost source ack, replay after later growth, separate collections, current-prior transactions, limits/media references and confirmed receipt ownership. Scripted bounded source replies are input data only; they cannot establish vendor completeness.
Cost: local coding and offline tests; temporary files only.
Must precede: step1 and every production edit. The plan declares this prebuild but has no candidate result yet; this verdict makes the required ordering executable.
Disqualifying result: an actual representation, SQLite acceptance or existing receipt rule makes the qualified ownership contract impossible without changing source semantics or redesigning the selected value/receiver split. A missing member, false acknowledgment authority or raw identity change caused by that architecture fails the experiment. Ordinary local prototype typos do not establish a false premise; record and correct them before comparing results.
Passing result: all named combined histories run on actual candidate/components, retain exact observed members/captions and canonical revision, retain original raw bytes/receipts/cursors, refuse invalid/uncertain state, preserve committed data through retries, and make zero network calls. Record candidate hashes and exact cases. Targeted existing-component probes alone cannot pass.

Result: PASS — 37 combined actual-candidate tests passed on Python3.11.10/Telethon1.45.0, 2026-10-14. See prebuild/result.json and prebuild/combined.txt for candidate hashes and histories; prebuild/report.md records the one corrected test-clock fixture. No source semantics or production code changed during the experiment.

## High-level summary

The plan's small derived layer fits the existing library. The new post represents observed membership, while raw batch IDs and full backfill delivery references remain source acknowledgment authority. A strict caller-owned receiver can retain members without a new progress engine. The full combined candidate has not run; qualify it first.

One Medium implementation-detail risk needs folding: adjustable assembly limits must propagate through every saved-value load in the receiver. Otherwise a post deliberately accepted under a raised limit can become unreadable after restart. No High finding or meaning gap was found in the selected architecture. No model/effort certification is available; §9 remains visible for later merge review.

## Premise Inventory

### P1 — Actual representation and receiver/source composition

**Premise:** immutable observed posts and caller-owned acceptance can retain all members across real raw serialization, commit/reopen and source replay without a second source lifecycle.
**First dependent step:**1.
**Waste if false:** core, receiver, tests and docs (steps1–4) require redesign.
**Test scheduled at:** the plan says a prebuild precedes production adoption, but no combined candidate/result exists; step3 also repeats qualification after adoption.
**Cheapest earlier test:** the combined experiment above, before step1; local and available now.
**Coverage:** eight real SQLite/SQLiteSyncStore probes cover existing open/transaction behavior, not new post serialization or integration. Real MessageBatch/source code reads confirm interfaces. A fake receiver reporting success would be non-covering. A scripted source returning raw input is valid only for testing receiver/source-engine integration, not Telegram membership completeness.

### P2 — Limits remain usable across persistence and restart

**Premise:** callers can deliberately raise operation limits without the receiver later imposing hidden default loader limits.
**First dependent step:**1, then2.
**Waste if false:** saved-value API and receiver load path need local correction; no source redesign.
**Test scheduled at:** step3 general bound/restart tests; the exact raised-limit round trip is not named.
**Cheapest earlier test:** accept and reopen the actual receiver with a caller-selected bound above the loader default, then exercise a lower bound that refuses without writes; part of the combined experiment.
**Coverage:** no current album code exists. Existing batch maximum10000 is an individual source input limit, not a guaranteed maximum cumulative observed-post size. Do not infer one from the other.

### P3 — Observation API is an acceptable qualified endpoint

**Premise:** stable entity updates with explicitly unconfirmed membership satisfy the request rather than a final-emission promise.
**First dependent step:**1.
**Waste if false:** delivery API changes.
**Test scheduled at:** inquiry before planning.
**Cheapest earlier test:** documentary comparison with source-input.md and the user's scope; performed. The issue explicitly requests incomplete/unconfirmed membership and asks qualification to select assembler versus fetching API. Separate assembler remains the stated optional preference assumption, not a user answer.
**Coverage:** source request + inquiry address this. No stochastic vendor-completeness premise is inherited: `grouped_id` is the supplied membership key, not a promise to find all unseen records. A live sample cannot replace the missing global completeness oracle, and none is required by this API.

## Restart Check

| Observed failure | Established mechanism | Design element that addresses it |
|---|---|---|
| Actual reference helper returns only one caption for multiple captioned members | reference-probe.json executes the consumer helper; first selected caption is the summary field | Step1 preserves every raw member instead of storing a lossy synthesized caption |
| Actual reference helper merges equal group IDs across supplied chats | reference-probe.json shows grouping without a chat key; consumer normally supplies one chat | Step1 includes canonical chat in stable identity |

Lost receiver state, stale writes and lost acknowledgments are designed fault histories, not claimed observed live incidents. The eight SQLite probes establish available mechanisms. Their combined use with new values remains the experiment, not an already reproduced feature result.

## Inherited Lessons

| Lesson | Ordering that satisfies it |
|---|---|
| Source data availability is not receipt authority | Concrete contract before step1; source-engine composition in prebuild; step2 collect only normal deliveries |
| More source reads do not prove global album completeness | No source calls in core; no completion promise to test by overfetch; explicit schema property in step1 |
| Durable data requires a known owner before source acknowledgment | Receiver open/transaction order fixed before implementation and tested in prebuild |
| Existing component probes do not qualify new composition | Full candidate experiment before step1, then regression in step3/5 |
| Failed approaches should not grow another progress engine | Pure supplied-value interface and receiver example; source modules remain untouched |

## Risk1 — Raised limits can be lost on the reload path

**Risk**

A caller may increase the allowed album size so that a large set of observed members can be saved. If reopening that saved post uses the library's smaller default limit, a successful collection becomes unreadable on its next run. This is a delayed failure: the first write succeeds, then the restart that should continue it refuses the caller's own accepted data.

The plan's `tgdata/album.py` loaders and `assemble_albums(..., max_members, max_bytes)` expose adjustable limits, but step2's `examples/album_assembly.py::AlbumReceiver` does not explicitly propagate one configured policy into every `TelegramPost.from_json` load, assembly call and readback. A cumulative post can exceed `MessageBatch.MAX_BATCH_MESSAGES` even though each incoming raw batch remains valid. This triggers when acceptance uses larger bounds and reload silently falls back to10000 members or16MiB.

**Severity:** Medium.
**Category:** API contract / persistence compatibility.
**Impact:** inability to resume accepted data, pressure to discard or reinitialize a healthy receiver.
**NoobEng:** a raw batch's size bound applies to one delivery; an album observation accumulates multiple deliveries. Treat saved-value loading and operation limits as one explicit receiver configuration, not independent defaults.
**Affected areas:** new album value/combiner, new receiver example and restart tests; no existing source store changes.

### Mitigation — Quick

Document that the example only accepts values within library defaults, despite core configurability.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Give the receiver explicit positive max_members/max_bytes configuration, use it for every loaded post and assembly/readback, and refuse a deliberately lowered bound without writes. Add a real raised-member-limit accept→close→reopen→replay case (for example10001 members across individually valid batches) plus exact UTF-8 byte-bound refusal. Explain that reopening under stricter policy may refuse and requires restoring an adequate limit, never resetting data.
**Why this is robust:** the one receiver path carries its declared policy consistently; saved data remains portable, and the test crosses the default boundary rather than mirroring parameter plumbing.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* One explicit receiver policy closes this instance permanently in the planned files. The other serialized types have different fixed source/state invariants, so a generic mechanism would need special cases and adds extent without the same reach.
*For future:* —

### Mitigation — Long-term

Introduce a shared generic serialized-value policy framework across raw batches, source state, backfill state and derived posts.
**Why this is long term effective:** a uniform framework could standardize resource-policy propagation across serialized types if they shared a common limit contract.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Compatibility and scope assessment

No mandatory dependency, database migration, raw hash/schema change, new account operation, source request, budget override or worker protocol change is planned. The new receiver schema is isolated and user-selected; package exports need import verification. Private raw validators are reused within the same library, with local errors translated and suppressed context to avoid false health attribution/content leaks. Download values preserve references without claiming blob retention. Existing daily example's generic partial-result exception branch is not copied; source publication failure can expose available data without a normal pending receipt. Fixing that separate example is not silently added here.

The proposed format and operation ordering are detailed enough to implement. The prebuild must still test exact byte accounting, saved-value validation and real rollback/retry behavior. No future photo-trail heuristic or distributed lease is needed to satisfy #29. Global edited-message reconciliation is explicitly outside the conflict-refusing observation contract.

## Phase3 selection

Completed after saving Phase2. Risk1 Robust is selected and elegant; no last-resort or quick choice. Named comparison instances: message_batch.py (fixed raw-delivery bound), sync_store.py (opaque source state), backfill_state.py (lifecycle state). Their policies are not interchangeable with cumulative observed members, so the proposed class-wide framework fails the one-mechanism test. No future mechanism is selected or prerequisite added. Phase3 changed only boxes/notes and this selection record; no severity/proposal was rewritten. No execution blockers were declared or added.
