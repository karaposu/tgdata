# Sensemaking — album membership and acceptance

## User Input

`_branch.md`, I1 and V1–V4; prior actual output: surfacing.md. Establish a contract for the requested implementation, preserving the raw delivery and library boundaries. API preference is pending; no user choice is invented.

## SV1 — Baseline

The tempting starting picture is to group records by album ID, keep the last group when a batch ends, and emit it when the next group starts. That picture handles the familiar caption-plus-photos example, but has not established finality, restart ownership or the validity of its ordering assumptions.

## Phase 1 — Cognitive anchors

- **Constraints C1–C3:** MessageBatch hashes cover exact records/envelope; source acknowledgment advances a saved raw cursor; batch/window/budget bounds are enforced independently of grouping. Sources: message_batch, batch_engine, sync_engine and backfill_engine.
- **Insights I1–I3:** a grouping ID identifies association without carrying expected member count; a received batch may end before an album; a durable receiver can accept records before the logical post stops changing. Sources: actual SDK constructor, raw schema and receiver example.
- **Structural points S1–S3:** message identity is `(chat_id, message.id)`; album identity is `(chat_id, grouped_id)`; source receipt, retained member data and downstream processing are distinct responsibilities. Missing grouped_id leaves an independent message.
- **Foundational principles P1–P3:** preserve all original records/captions/media references; do not advance source acceptance ahead of recoverable destination custody; represent observation limits honestly instead of manufacturing global completeness.
- **Meaning nodes M1–M3:** album membership, observed logical post, durable acceptance. These use the request/consumer vocabulary, not new names for a new scheduler or archive service.

## SV2 — Anchor-informed

This is grouping plus custody of observed membership across delivery boundaries. It does not become correct merely by delaying the final list element. H4/H5 inspection: “complete” currently names several different facts; the three-photo fixture is one case of an arbitrary bounded observation, not a complete specification.

## Phase 2 — Perspective checking

- **Technical/logical:** MessageBatch guarantees increasing message IDs, not album contiguity. It can represent nonadjacent same-group members, interrupted prefixes and subsets cut by dates. New anchor: any stronger ordering precondition needs its own established evidence.
- **Human/user:** users want one coherent post and its media, not phantom empty-text photos. Yet a later caption can change which member best represents the post. New anchor: caption-carrier ID cannot be the durable identity of an album.
- **Strategic:** #30 needs original member IDs, dates, media kinds and reply references. Losing those now would make the next helper reconstruct unavailable facts. Raw records are the reusable foundation.
- **Risk/failure:** a crash after source acknowledgment cannot be repaired by asking the source store for an earlier pending batch. New anchor: any retained member needed later must already be in recoverable caller-owned state or accepted input. A capture of available data is not itself a source receipt.
- **Resource/feasibility:** unrestricted album recurrence, finite memory and one irreversible emission cannot all be promised from a stream with no closure evidence. Persistent caller-held observations or explicit bounded scopes change that equation; silent eviction does not.
- **Privacy/systemic:** grouping should not invent a sender or rely on usernames, signature text or temporal proximity. Telegram-marked membership also applies when sender identity is absent; photo-trail identity rules belong to #30.
- **Definitional/internal consistency:** “one post” can mean one stable entity with increasing observed membership, without requiring one irrevocable delivery event. “Finished backfill” means its declared scope was delivered/accepted, not that every album in that scope has all historical members.
- **Phase/calibration:** a delay or “next ID belongs elsewhere” may match familiar traffic, but no calibrated guarantee for those rules exists here. The early default must expose uncertainty and must not depend on a future live sample proving a universal property.

### Frame-exit completeness

This perspective fires because “complete”, “state” and “acknowledged” have distinct inherited meanings. Existence enumeration: complete prepared record, published media file, end of one source observation, fulfilled backfill run, full album membership and destination processing completion. State includes credentials, account quota, source pending delivery, derived post membership and permanent destination storage. Acknowledgment includes source progress and independent receiver acceptance.

Role assessment: credentials/quota remain source-layer preconditions; source progress remains existing engine authority; derived membership belongs to its explicit assembly/receiver contract; permanent archive and application processing remain caller-owned. Ignoring receiver custody would make restart claims incoherent, so it is included as an integration contract/example rather than silently moved into source progress.

Strongest clean-boundary counter: embedding assembly directly in a progress engine could make persistence easy. Structural response: those engines serialize and validate exact raw batches, enforce their bounds and receipts, and are consumed by pool/worker code. Replacing pending raw delivery with a derived post would change those interfaces. Reuse is viable through composition, but not a consequence of adding one field. Residual: media bytes have separate custody from JSON references; a checkpoint alone cannot keep a deleted blob available. No further referent forces a larger project scope.

## SV3 — Multi-perspective

The difficult boundary is between accepting raw input and deciding when an observed post is ready for downstream processing. Group identity is stable; the observations and their delivery can grow. The resource and failure perspectives independently destabilize the initial “hold the tail and forget everything else” model. The frame has room for a separate assembler, receiver projection or explicitly bounded collection; a fetching wrapper alone does not manufacture stronger evidence.

## Phase 3 — Ambiguity collapse

### A1 — “Complete album”

**Strongest counter-interpretation:** the next nonmatching group or an exhausted history iterator proves the album is complete.
**Structural counter test:** dates/after_id can omit earlier members; interrupted or budgeted reads can stop early; current wire and batch schemas expose no expected membership. Even a contiguous-history premise would not eliminate clipping by the requested scope. A live sample cannot prove every future observation has no omitted member.
**Confidence:** HIGH for refusing unqualified global completeness; no claim that source contiguity is false is required.
**Resolution / fixed:** membership comes from observed grouping IDs; global completeness stays unconfirmed unless separately established. **No longer allowed:** treating page/timeout/end as unconditional album completeness. **Depends on:** output status and documentation. **Model change:** observation closure is separated from membership completeness.

### A2 — “One post”

**Strongest counter-interpretation:** users require exactly one output event and cannot accept later observations of the same post.
**Structural counter test:** the request requires one logical post and cross-batch assembly, but does not supply a source-membership oracle or a bound on when all members become visible. Stable entity identity can satisfy grouping while output scheduling remains a caller/closure policy. The counter still has user-experience merit.
**Confidence:** HIGH for stable identity; LOW for choosing a final emission policy before evaluating options.
**Resolution / fixed:** `(chat_id, grouped_id)` identifies an album regardless of caption location; ungrouped records retain message identity. **No longer allowed:** using the changing caption carrier as the album key. **Depends on:** output/projection API. **Open:** whether results are revisions or explicit closed-scope outputs. **Model change:** identity and emission are distinct.

### A3 — “Saved checkpoint”

**Strongest counter-interpretation:** saving a cursor or accepted-batch marker is enough because the source can replay.
**Structural counter test:** source ack removes pending data and advances the cursor; a marker without retained members/output or durably retained raw input cannot reconstruct them after a crash. The existing receiver commits its marker with records before ack.
**Confidence:** HIGH.
**Resolution / fixed:** accepted input must remain recoverable together with derived progress/output before source ack. **No longer allowed:** acknowledging a batch while its needed membership exists only in process memory. **Depends on:** persistence contract and restart tests. **Model change:** custody is an explicit acceptance precondition, not an incidental cache.

### A4 — “The caption”

**Strongest counter-interpretation:** albums always have one caption, so the first nonempty string is sufficient.
**Structural counter test:** [Telegram's album guidance](https://core.telegram.org/api/files#albums-grouped-media) permits per-file captions; inputSingleMedia carries a caption per item. The consumer's first-caption helper is narrower than that platform contract.
**Confidence:** HIGH.
**Resolution / fixed:** retain every member and caption; a convenience display caption must not erase others. **No longer allowed:** conflating caption selection with record preservation. **Depends on:** logical-post representation and #30. **Model change:** one post can contain several caption-bearing members.

### A5 — “Bounded tail”

**Strongest counter-interpretation:** retaining only the last contiguous album always suffices.
**Structural counter test:** the accepted raw value admits increasing IDs with nonadjacent repeated grouped IDs; it does not carry a contiguity certificate. Forgetting an earlier group cannot later merge it without caller-held prior observations. Merely retaining all group IDs forever also violates bounded-state intent.
**Confidence:** HIGH for the limitation; OPEN for the particular retention policy.
**Resolution / fixed:** the chosen contract must name what prior data is retained and by whom, and how bounds fail. **No longer allowed:** silent eviction coupled with an exact cross-batch promise. **Depends on:** bounded assembly/projection design. **Model change:** resource ownership is part of correctness, not just an optimization.

### A6 — “tgdata saves everything”

**Strongest counter-interpretation:** a new library-managed permanent post database is needed to make assembly reliable.
**Structural counter test:** the existing caller already accepts raw data durably and can retain typed derived values. A library can own validation/grouping transitions while the caller owns persistence; no evidence yet requires a second archive engine.
**Confidence:** HIGH for the possibility; the exact API remains to be compared.
**Resolution / fixed:** permanent storage stays caller-owned; generic library state/value support is allowed. **No longer allowed:** silently expanding #29 into a destination service. **Depends on:** decomposition and examples. **Model change:** ownership can be explicit without a new scheduler/store framework.

The load-bearing concepts membership, identity, completeness, custody, bounds and storage ownership each have a counter-test above. Specific-versus-pattern check: captions in ScrapeOps's three/ten-photo examples do not exhaust the broader pattern; mixed media, multiple captions, gaps and clipped observations must survive the chosen contract.

## SV4 — Clarified

The library must assemble observed Telegram-marked membership without altering raw receipt authority. A stable post identity, complete retained raw members and explicit uncertainty survive. Universal finality and automatic bounded-tail correctness are not established. The final API/retention choice remains for option evaluation.

## Phase 4 — Degrees of freedom

Fixed: canonical identity; complete original member preservation; caller-owned durable acceptance; no extra source requests required merely by grouping; no silent loss on bounds; raw v1 unchanged; no photo trails. Eliminated: sender/time inference for albums, first-caption-only storage, blind whole-album promises and implicit source acknowledgment. Viable: separate pure assembly over caller-supplied prior observations; bounded explicitly closed collection; a fetching wrapper only if it carries the same honest limitations. Open: exact output/update surface and the minimum integration example.

## SV5 — Constrained

The candidate space is organized around one receiver-side data operation and its observable limits. Any solution must account for prior membership, repeat delivery and the durability boundary. The source reader need not change to supply those properties; a new reader wrapper adds cost without resolving missing completeness evidence by itself.

## Phase 5 / SV6 — Stabilized model

Album assembly is preservation and combination of observed members under a stable Telegram identity. A bounded delivery and a logical post are different units. The library can provide immutable, inspectable derived observations and a transition contract; the caller must durably accept enough data before acknowledging the raw source. Final emission remains an explicit observation/processing policy, not a hidden guess about Telegram history.

Compared with SV1, the model no longer assumes a contiguous tail proves completeness. It is supported separately by schema, source bounds, receiver transaction and vendor caption evidence. Seven major perspectives added distinct constraints; three of them changed the model. Five of six ambiguity entries fix strong constraints; finality/output/retention choice is deliberately open for the next stages. H1–H9 check: no protected status-quo design, no untested global-completeness proxy, no fixture-only generalization, no self-referential methodological claim. Accommodation was needed once at the tail model; the revised identity/custody model fits the surfaced facts without accumulating exceptions. **PROCEED** to Decomposition.
