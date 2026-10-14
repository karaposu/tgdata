---
model: unknown
effort: unknown
---
# Implementation plan — album acceptance and post views (#29), revision 4

**Critic folded:** 2026-10-14 — 0 additional mitigations (0 implementation steps changed, 0 added). Fresh critique confirms the revised contract and requires the complete candidate prebuild before production step1.

**Status:** reviewed revision4; full combined prebuild pending. The user authorized fold → prebuild → implementation; no production adoption until the prebuild passes. The previous folded plan remains in DEPRECATED_step_by_step_impl_plan.md.

**Explicit inputs:** desc.md, pr-critic.md R1, its three counterexamples, replan-r3-contract.md and six planning-probe histories. The prior implementation remains on the draft PR; this plan changes the receiver contract, not merely its numeric limits. Current source base is dev e5cdad7, product head19d421f / equivalent archive product e35392c. One rejected PR critique exists; the rejection guard does not require another traverse.

### What is the task

Finish #29's lossless observed album capability with a receiver whose successful acceptance remains confirmable after restart and later post growth. The source of durable content will be immutable original member records. Post views can grow and have their own read limits; confirming an already accepted raw delivery must not rebuild those views or depend on their current size. Keep the established pure assembler, post format and source receipt APIs intact.

### Huge Hard Blockers

#### Planning Blockers

**Question:** what is admitted as new work, what confirms accepted input, and what does confirmation return after posts grow?

**Why the old steps cannot survive unchanged:** revision2 always reassembled and returned current post projections before checking its stored acceptance marker. Exact replay therefore gained prior bytes or later members and could fail the unchanged policy that permitted the original commit.

**Status:** CLOSED — canonical member rows plus a scoped batch marker are authoritative receiver content. New input passes bounded assembly and commits immutable rows/marker. An accepted input confirms only its original rows, performs no assembly/write and returns None. A separate bounded load constructs a current TelegramPost. This contract is established in replan-r3-contract.md and the actual SQLite/value/SyncEngine planning probe; all three counterexamples succeed unchanged and integrity/fresh-admission controls still refuse correctly. Closing the planning premise does not claim the product fix is complete.

**Source:** inherited from desc.md and pr-critic.md R1.

**Who closed it:** this same-session task-plan pass through full code reads, contract analysis and six real-component feasibility histories. No unavailable information or human-only decision remains necessary for the plan.

#### Execution Blockers

None identified for the proposed local implementation. Fresh critic-d review, its selected fold and the complete candidate prebuild are workflow prerequisites before production adoption, not external blockers. Live Telegram, a second account, deployment and a new release are unnecessary for this observed-data contract. §9 model/effort remains unknown and must be surfaced at the later merge gate; this plan makes no certification.

### How this implementation moves toward desired state

The immutable TelegramPost/assemble_albums layer stays as implemented. The SQLite example will normalize the same member content it currently embeds in mutable post JSON, rather than store duplicate batch archives or mutable authoritative projections. Receipt confirmation then depends on unchanged original records; current post reconstruction becomes a separate read. Strict creation/reopen, transaction ownership, conflicts, resource refusal, cleanup and original source acknowledgments remain required. Tests become explicit about the two operations and jointly exercise admission, commit, growth and retry.

### High-Level Summary

| Step | Description | Expected Output |
|---|---|---|
| 1 | Define authoritative member storage and bounded post views | Schema2 receiver storage/load path |
| 2 | Separate new acceptance from exact confirmation | One atomic accept operation returning None on either successful path |
| 3 | Update example consumers and recovery tests | Preserved behavioral coverage plus all rejection histories and integrity controls |
| 4 | Document the revised persistence and return contracts | Accurate guide/README/example instructions |
| 5 | Verify and publish the product-only revision | Full offline evidence and updated draft PR, ready for renewed review |

## Mandatory qualification before production step 1

After fresh critic-d and its fold, build the **complete revised receiver/example/test candidate in an isolated temporary package**. This is the prebuild experiment, not adoption of production code. Use the actual current library, actual candidate schema/open/load/accept/cleanup paths, SQLite, SDK-derived raw values and both SyncEngine and BackfillEngine. The six-case planning probe is not a substitute: its schema validation, bounded prior-load preflight and cleanup matrix are intentionally incomplete.

Run the complete revised suite42 and a combined set of the following histories before copying any candidate into product paths: all three R1 counterexamples under unchanged limits; ordinary and boundary commit-before/after process exits; same-input replay with changed/later post views; wrong/missing/corrupt member and digest; known v1/partial v2 schema refusal; distinct collection/same batch; concurrent first accept and duplicate confirmation; failed lookup/write/commit/close; actual original daily/backfill receipt settlement; cancellation and uncertain publication preserving source authority; and resource-limit refusal on new work and separate view reads. Assert source calls, raw bytes, cursor/pending state, member rows and marker writes separately. For accepted-input confirmation, forbid the assembler, post-view loader and post-level count/size scans and observe zero DML.

Passing result: every named history preserves original records/receipt authority and accepted-input confirmation is independent of later view growth, without raising policy, dropping integrity checks, widening source reads or introducing another source lifecycle. Any missing immutable member, wrong confirmation or source advancement caused by the new design is a failure. Record exact candidate hashes and retain failed observations; structural failure requires re-planning, not an inline patch. Targeted or behavior-supplying stand-ins cannot pass this gate.

## Contract fixed for this revision

- **Public core stays unchanged:** TelegramPost v1, its identity/revision/member semantics, four exports, assemble_albums required previous mapping and its exact aggregate member/byte admission policy. Album membership stays unconfirmed. No core runtime edit is planned.
- **One authoritative copy:** replace example-only album_posts with album_members. Columns: collection TEXT, chat_id INTEGER, message_id INTEGER, post_id TEXT, record TEXT, record_sha256 TEXT; all NOT NULL. Primary key(collection,chat_id,message_id); index album_members_by_post(collection,post_id,message_id). The value is canonical original raw-record JSON plus its SHA256. The collection is reference-only as before. Keep album_meta, album_collections and scoped album_receipts, with meta version2.
- **No silent reassociation:** an existing collection/chat/message record may repeat identically but cannot acquire different content, digest or post key. New acceptance must check this even if a changed grouping ID points to a different prior-post key. Member rows are insert-only through this example.
- **accept(batch) returns None:** after a successful new commit or successful recognized-input confirmation. It never returns a post tuple or a source receipt. Callers needing content use load(post_id) separately. No new public acknowledgment class or schema is added.
- **Common validation:** require a valid reference-mode MessageBatch and a known selected receiver collection; check its UTF-8 input size and member count against the chosen positive limits before work. Extract the decoded batch metadata outside the member loop; avoid repeated whole-batch getter decoding.
- **New input:** current prior views are loaded under the receiver transaction; real assemble_albums is the final exact new-work admission check. Store only the canonical member rows and scoped input marker in one commit, with no post snapshot table. Conflicts, bounds or storage failures leave no partial acceptance.
- **Recognized input:** compare each original member's canonical bytes, SHA256 and post key against its indexed stored row. SQL can return equality flags using byte-exact comparison, without transferring grown post content into Python. Missing/different accepted data raises; do not restore it from the replay, trust the marker alone or invoke new-work assembly. Confirmation writes no row. Its work is bounded by original input records, not future view size.
- **load(post_id):** one consistent read transaction validates schema/collection, preflights member count/encoded-byte totals, then reads/validates records and constructs the existing TelegramPost. Verify row chat/message/post metadata, canonical record JSON, digest and raw-record validity; compute the ordinary post revision from the reconstructed full view. Return None only when a successful query finds no members for that post.
- **Policy effects:** unchanged input limits suffice for exact confirmation. A deliberately lower input bound can refuse the original batch. A larger-policy writer may make today's view too large for an older reader's view bound; old input confirmation still works because its immutable records did not grow. State corruption, unavailable storage or contention still raise. This is no distributed lease or physical-RSS guarantee.
- **Schema compatibility:** no automatic migration/reset of known version1 receiver databases. Strictly refuse them unchanged, including with create=True. The example schema is unmerged/unreleased; callers who used the rejected example must retain that state and explicitly import/restore it under separately qualified handling. Public raw/post/source-store formats and package version0.1 stay unchanged.

## Step 1 — Authoritative member storage and bounded post reads

### Proposed changes

Change examples/album_assembly.py's private schema to the exact version2 structure above. Preserve explicit creation versus strict reopening and named collections. Validate required columns/types/nullability/primary keys, version and the required nonpartial post index before operations. Known v1, missing/partial schema or missing collection must fail without repair or creation fallback. Preserve connection close/rollback precedence.

Replace stored-post-JSON loading with a private bounded member reader and view constructor. A read transaction covers schema validation, count/byte preflight and row reads, so a concurrent writer cannot make metadata and payload snapshots disagree. Before materializing rows, refuse counts beyond the selected per-view member cap or record-byte lower bounds beyond its byte cap. Validate each row's key/content/digest; construct the same TelegramPost document and revision using existing canonical/identity/revision validation helpers. Do not introduce another public value or batch-format factory, and do not route a10001-member post through MessageBatch's10000-record input bound.

For new-work prior loading, accumulate count/record-byte lower bounds across affected keys and raw input before materialization; then account for the actual prior-post JSON incrementally before loading subsequent views. These are early necessary checks; assemble_albums still enforces the exact full aggregate formula including produced JSON. No silent eviction or limit relaxation.

### Output

A strict example-only version2 receiver that stores immutable member content once and reconstructs bounded validated current post views.

### Safe in nature

False — the unmerged example's persistence format/read semantics change; tests must prove strict refusal of known old data and consistent reads.

### Peripheral concepts

SQLite schema/index/snapshots, canonical records and digests, TelegramPost validation, collection identity, explicit creation, prior lookup, read bounds, cleanup precedence.

### Hardness Lvl

4

## Step 2 — New-work admission and accepted-input confirmation

### Proposed changes

Keep one BEGIN IMMEDIATE transaction for validation, marker lookup and the selected path. For absent marker, check any existing input member for exact content/post identity, load current affected views through step1's bounded preflight, run actual assemble_albums, insert only absent immutable members and write the marker, then commit. The resulting post values validate admission but are not saved as a second authoritative copy.

For present marker, issue indexed member comparisons only. Use canonical expected content/digest from the already validated input, enforce byte-exact comparisons and include the selected collection/chat/message/post identity. A missing row, wrong digest/content/key or backend error raises. No post load, post-level stats scan, assembly, record rewrite or marker rewrite is allowed. Commit/close preserves the existing uncertainty semantics. Return None after successful completion of either path.

The original raw input size and count are common bounds. Confirmation has one fixed lookup per input member; it does not receive an unbounded exemption to validation. Cache raw envelope metadata before looping, so accessors cannot create quadratic whole-batch decoding. Source acknowledgment stays in the caller and uses its original receipt.

### Output

An acceptance operation whose successful input remains confirmable after restart and later view growth without increasing limits or skipping integrity checks.

### Safe in nature

False — changes example acceptance/return behavior and the recovery guarantee that caused the rejection.

### Peripheral concepts

Raw input identity, immutable accepted records, duplicate recognition, source receipt authority, atomic commit, resource admission, current-view growth, local failures.

### Hardness Lvl

4

## Step 3 — Example callers and regression histories

### Proposed changes

Update the demo and suite42 call sites that unpack accept() results: assert/ignore successful None as appropriate, then load a post explicitly when content is needed. The collect helper already ignores the return and must continue accepting only confirmed normal source deliveries before ack. Keep its cancellation/error propagation and no-partial-receipt inference. The demo retains its observable lost-ack/caption/member results.

Adapt SQL inspection/fault fixtures from mutable post rows to immutable member rows without weakening their intended acceptance/integrity assertions. Retain the37 existing behavioral cases, with the deliberately changed schema/return expectations explained. Add permanent versions of the three PR counterexamples; same-policy retry must pass, not expect a resource exception. Include a later larger-policy post growth case in which old confirmation succeeds while a too-small separate view read refuses.

Add guards forbidding assembler/view-loader/post-stat calls during recognized input, and observe zero row writes. Test missing/changed/malformed member records, digest and metadata mismatches, canonical/duplicate-field JSON validation, cross-chat/post reassociation, per-collection equal hashes, old-v1/partial-v2/schema/index refusal, input caps, bounded fresh-prior/view loading, rollback and actual process exits around fresh commits. Check both daily and backfill settlement using original receipts, publication failure/cancellation, lost acceptance replies/close errors, and competing first/duplicate calls. Compare source reads, pending/cursor state, raw hashes and durable rows separately.

### Output

Updated executable example and expanded offline suite that jointly tests admission, acceptance, growth and confirmation, including the previously missed boundaries.

### Safe in nature

False — the example's consumers change with its contract; test changes must correspond to the declared schema/return changes, never merely bless a regression.

### Peripheral concepts

Daily/backfill source engines, SDK raw fixtures, exact receipts, cancellation, SQLite fault/process boundaries, immutable views, content integrity, retry policy.

### Hardness Lvl

4

## Step 4 — Documentation and compatibility guidance

### Proposed changes

Revise docs/album_assembly.md and the README/smoke example descriptions to distinguish pure bounded combination, durable acceptance/confirmation and current post reading. Explain None returns, immutable canonical member storage, view reconstruction, no duplicate post/batch archives and the three separate resource scopes. Preserve the pure API's aggregate formula and qualified idempotence: if admitted, identical observations yield identical bytes; that computation is not itself a durable receiver receipt.

Show correct acknowledgment immediately after receiver success using the original daily batch ID/full backfill delivery reference. A later view read is application processing with its own policy, not a prerequisite for confirming already committed data. Document schema2 and strict refusal of known v1 without reset/migration. Keep unconfirmed membership, blob custody, reference-only example and no-live-completeness statements. Do not change the legacy daily example or deploy/migrate ScrapeOps.

### Output

A public contract that accurately states what is stored, what each operation returns, which limits apply and why replay remains valid after view growth.

### Safe in nature

True — documentation only; no runtime/default behavior changes in this step.

### Peripheral concepts

Data custody, projection versus acceptance, source acknowledgments, bounds, schema compatibility, unconfirmed membership, application processing.

### Hardness Lvl

2

## Step 5 — Verify, commit and update the same draft PR

### Proposed changes

After the complete candidate prebuild passes, adopt its exact qualified implementation and run the updated suite42/demo plus relevant raw/daily/window/backfill/pool integration checks. Run all28 existing offline suites (12–19,22–41), the expanded suite42 and six demos; report actual counts, missing-config live skips, source hashes and watchdog outcomes. Compile package/examples and check Python3.7 grammar using Python3.11/Telethon1.45.0; do not claim native3.7 execution. Preserve all old source behavior and the pure album core bytes/exports/version.

Retain original critic.md as critic_r1.md and its prompt as dynamic_critic_prompt_r1.md before a fresh plan critique writes the canonical filenames. Keep pr-critic.md and its probes as the first rejection; archive them with an r1 suffix before a later fresh PR critique so rejection history is not overwritten. The deprecated revision2 plan stays intact.

Commit product changes separately from work notes on feat/29-album-assembly. Apply only the product commit to feat/29-album-assembly-pr, verify tree parity and update PR35's description with actual validation. Preserve draft status until renewed merge check, fresh PR critique and §9 verification are satisfied. The original checkout/version edit and running ScrapeOps remain untouched. No merge/release or branch deletion is part of implementation.

### Output

A tested product-only revision of PR35 and separate durable evidence, ready for renewed fidelity and soundness gates.

### Safe in nature

True — isolated verification and reversible feature-branch publication; no production deployment or merge.

### Peripheral concepts

Regression evidence, source parity, Python compatibility, Git worktrees, artifact history, issue status, PR review gates, model metadata.

### Hardness Lvl

3

## Rejection response and current handoff

R1 is answered at the design level by a different durable fact, a distinct confirmation path and a None-return acceptance API—not by extra allowance. The three old counterexamples become required passing histories in prebuild and permanent tests. The original pure representation/assembly remains reusable.

Revision3 planning and its six feasibility histories remain the design record. The fresh critique and empty mitigation selection produce revision4 without adding scope. Next: full combined candidate prebuild → implementation. Planning-probe success must not be mistaken for that implementation gate or a passed PR review.
