# Sensemaking — receiver recovery refinement

## User Input

Same I1/V1–V4 goal in _branch.md; focused concern from critique_iter1.md: known destination state must not silently become an empty new collection. Inputs are surfacing.md and the actual receiver-probe.json observations.

## SV1 — Baseline

The first pass chose an explicit receiver boundary but had not distinguished first provisioning from reopening. The remaining question is whether that distinction can be concrete and small, while keeping the pure post assembler and raw source authority intact.

## Phase 1 — Anchors

Constraints: acknowledged raw members may no longer be pending; known state loss must not be treated as successful creation. Insight: absence has two levels—an absent post in an authoritative opened collection, and an absent collection/database. Structural point: lookup and write belong in one receiver transaction or equivalent conditional-write contract. Principle: successful acceptance means recoverable data, not merely a marker. Meaning nodes: explicit creation, authoritative reopen, scoped acceptance.

Evidence: eight existing-component checks pass in receiver-probe.json. SQLiteSyncStore(create=False) refuses a missing file without creating it; a partial known schema is not repaired; stale CAS is false; data/receipt rollback together; committed rows survive reopen; collection keys separate equal input IDs; a write transaction excludes a stale competing writer, whose retry sees current state.

## SV2 — Anchor-informed

An explicit opening contract can resolve the gap without adding any source lifecycle. Post absence becomes meaningful only after the selected receiver collection has been opened and validated. H4/H5: these terms identify actual different observable states, not names invented to make the three-photo fixture pass.

## Phase 2 — Perspectives

- Technical: use a require-existing open for resume, validate all required schema/collection metadata, and allow None only for an absent individual key after successful lookup.
- User: a misspelled path or collection must produce an actionable local error rather than losing the caption already scraped yesterday.
- Failure: a response lost after commit must replay from actual stored state; it must not trigger a compensating reset. A failed load is not an empty prior mapping.
- Resource: short local transactions can load only affected post keys; neither source history nor every post in the destination must be loaded into memory.
- Strategic: portable immutable post values can be stored by other backends, provided the same acceptance guarantees hold. No mandatory SQLite runtime store is implied for the library API.
- Privacy/systemic: failures need type/field context, not dumped message text or credentials. No Telegram calls are required to recover the local receiver state.
- Internal consistency: a post is observed data, not an acknowledgment or a stream cursor. Destination namespace belongs to acceptance; source chat/group identity belongs to the post.
- Calibration: the actual local probes qualify SQLite behavior and an existing store pattern, not another database deployment or power-loss assumptions. The combined future assembler still needs its own prebuild.

Frame-exit check: “absence” includes missing file, missing schema, unregistered collection, absent individual key and failed lookup. Only the last-but-one can be an ordinary new post after authoritative opening. “Receipt” includes raw content identity and destination-scoped acceptance; equal batch IDs are safe only within the intended namespace. The strongest contrary boundary—automatically restoring a store from raw source progress—fails because that progress does not retain all acknowledged members. A retained raw archive could supply recovery, but that is a separate explicit input, not inferred emptiness. No additional frame exit changes the source/receiver split.

## SV3 — Multi-perspective

The recovery gap is a concrete API and example contract, not a missing storage engine. Later perspectives confirm the same distinction rather than producing new anchor types: evidence is converging on authoritative state opening plus atomic acceptance.

## Phase 3 — Counter-tests and fixed meanings

### R1 — Absence and initialization

Counter: opening a missing file and creating tables is harmless convenience. Structural result: if a separate source cursor has advanced, new empty prior data cannot reconstruct old accepted album members. Actual mode=rw/create=False refuses this case. Confidence HIGH. Fixed: explicit create versus require-existing reopen; per-key None only after validated open. Disallowed: silently provisioning on resume or load failure. Depends: receiver example and restart tests. Model change: creation is declared intent, not a fallback.

### R2 — Namespace and concurrent acceptance

Counter: one content hash proves every caller already received the batch; cached prior snapshots can be upserted blindly. Structural result: the same hash can be delivered into two collections; stale writes can lose members. The real probe separates composite keys and shows transaction/CAS behavior. Confidence HIGH. Fixed: scope acceptance by caller-selected logical collection and load current prior state inside the transaction or use equivalent conditional writes. Disallowed: global duplicate markers and blind stale replacement. Depends: acceptance example. Model change: content identity is separated from acceptance ownership.

### R3 — Membership and identity, inherited concepts re-tested

Counter: grouping by sender or caption-carrier ID is enough. Structural result: the request uses Telegram's group marker, caption location can change, and the mixed-chat reference probe aliases unrelated inputs without chat scope. Confidence HIGH. Fixed: chat/group identity; ungrouped messages use their own IDs. Disallowed: sender/time inference and carrier identity. Depends: value/combiner. Model change: none; prior meaning survives independently of receiver refinement.

### R4 — Completeness, inherited concept re-tested

Counter: validated durable storage makes an album complete. Structural result: a perfectly durable store can contain a clipped raw observation; commit proves custody, not undiscovered membership. Confidence HIGH. Fixed: explicit unconfirmed global album membership. Disallowed: deriving completeness from persistence, iterator end or receipt. Depends: serialization/docs. Model change: none.

### R5 — Custody and storage ownership, inherited concepts re-tested

Counter: the pure helper must therefore own a permanent database and perform source ack. Structural result: the real receiver transaction already supports data/marker acceptance, and existing source APIs accept the caller's assertion afterward. Confidence HIGH. Fixed: core operation owns values/combination; caller owns persistence, media custody and existing source receipt. Disallowed: hidden I/O/ack or treating a post revision as a raw cursor. Depends: example and contract. Model change: receiver recovery is made precise without moving ownership.

### R6 — Bounds, inherited concept re-tested

Counter: keeping every historical post in one in-memory checkpoint avoids lookup complexity. Structural result: that binds memory to whole history rather than the affected keys of a bounded input. Confidence HIGH. Fixed: explicit per-operation/member/byte bounds and authoritative prior input for affected identities. Disallowed: silent eviction or partial mutation. Depends: local refusal behavior. Model change: none; scale stays local to supplied observations.

All inherited load-bearing concepts have been re-tested. These are broader restart/identity patterns; the synthetic album and SQLite examples demonstrate mechanisms without being treated as all possible cases.

## SV4 — Clarified

The selected receiver declares creation explicitly, reopens known state strictly, distinguishes key absence from backend failure, and accepts each raw input in its named collection after preserving the derived observations. It never substitutes a post ID for a source receipt.

## Phase 4 / SV5 — Degrees of freedom reduced

Fixed: the six meanings above, atomic/conditional current-prior acceptance, immutable original records and no global completeness claim. Eliminated: auto-bootstrap on resume, empty-on-error lookup, unscoped duplicate markers and source-managed post storage. Viable: the pure assembler plus a small concrete caller-owned SQLite example; other backends remain possible by contract. Open details are field/function names and policy defaults for the later plan, not missing ownership decisions.

## Phase 5 / SV6 — Stable model

The first-pass architecture survives with one concrete refinement: recoverable destination state has an explicit creation/opening lifecycle. Eight real component observations support that boundary. The planned combined prebuild must still demonstrate the new immutable values and combiner through the source/receiver composition; no runtime implementation success is claimed yet.

Delta from SV1: absence is now a specific checked fact, not a generic empty value. Perspective saturation is reached; no new architectural region emerged. Six counter-tests preserve all load-bearing prior meanings. No status-quo protection, false global-completeness proxy, or unsupported “checkpoint means durable” claim remains. **PROCEED** to Decomposition.
