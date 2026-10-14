# Decomposition — album contract

## User Input

`_branch.md` I1/V1–V4, with the actual saved SV6 in sensemaking.md. Whole: combine observed Telegram-marked members across batches under stable post identity, with honest observation limits and recoverable acceptance before raw acknowledgment.

## 1. Coupling Map

- **Identity/representation cluster:** canonical chat/message/group keys, member validation, captions/media, immutable serialization and completeness wording are strongly coupled. Changing the key or losing a member changes the meaning of the stored post.
- **Combination cluster:** prior observation, new records, duplicate/conflict behavior, resource bounds and failure atomicity are strongly coupled. A bound is not safe if it mutates half the retained membership before refusing.
- **Acceptance cluster:** receiver persistence, input recognition, lost replies/restart and the source acknowledgment order are strongly coupled. Splitting the duplicate marker from the data creates an actual loss window.
- **Qualification cluster:** each advertised behavior needs direct evidence at its relevant component boundary; the complete composition needs adversarial restart/boundary coverage.

Moderate coupling connects representation → combination and combination → receiver acceptance through explicit value contracts. Weak coupling connects pure grouping to source authentication, routing, scheduling and source quota implementations: it consumes their already-prepared raw values. Raw delivery is an existing external authority, not a piece to redesign.

## 2. Top-down Boundaries

B1 separates “what an observation is” from “how observations combine”. B2 separates a deterministic data operation from the caller's durable transaction/acknowledgment. B3 separates contract construction from behavioral evidence. Completeness/closure wording stays with representation; replay/conflict/bounds stay with the combining operation. These boundaries hold for V1, V3 and V4; V2 additionally crosses the existing reader boundary and must justify that extra connection.

## 3. Bottom-up Validation

Atoms: one canonical source ID; one complete raw record; one group identity; one prior immutable observation; one input batch identity; one durable commit; one existing source receipt. A caption and its member cannot be separated. A receipt marker and recoverable accepted data cannot be committed independently without another explicit recovery mechanism. An SDK/session is not an atom of local grouping. Top-down and bottom-up agree on B1–B3 with high confidence. No storage implementation or public function name is selected here.

## 4. Question Tree

### Q1 — What does one observed logical post mean?

Verification criteria: canonical album and ungrouped-message identities; every raw member/caption/media reference preserved; immutable round-trip representation; clear known/unknown membership statement; no account/sender identity invented; no alias between equal group IDs in different chats. The runtime determination is explicit: a non-null validated grouped_id selects platform membership; absent grouped_id selects the single-message case. Completeness is not determined from timing or a page boundary.

### Q2 — How can new raw input combine with prior observations safely and within bounds?

Verification criteria: specified prior-state input and lookup responsibility; same-key accumulation across arbitrary batch splits; repeat delivery without added duplicates; explicit conflicting-member/stale-input behavior; byte/count bounds and refusal without partial mutation; no hidden network call; no change to the raw input hash/cursor. The decision of whether prior data exists must come from a named caller/state interface, not an implicit memory cache.

### Q3 — How does a caller durably accept this result before source acknowledgment?

Verification criteria: an explicit acceptance unit; output and required retained data remain recoverable before raw ack; duplicate input recognition is tied to the same accepted data; rollback and lost-commit-reply behavior; reload/replay after process loss; a concrete daily/backfill receiver example using the unchanged source receipt APIs. Media JSON versus blob custody must be stated. Permanent archive ownership remains with the caller.

### Q4 — What evidence qualifies the composition and its limits?

Verification criteria: actual MessageBatch/Telethon serialization; real SQLite/process or transaction failure behavior; complete combination with daily/backfill replay; existing full-suite regression; realistic multi-caption/media/big-ID/nonadjacent/cross-chat cases; direct source evidence before relying on any vendor completeness rule. A scripted server reply cannot prove a Telegram completeness guarantee. An API that promises only observed membership must still demonstrate its real-component data path and explain the remaining limit.

## 5. Interface Map

| From → To | What crosses | Direction and assumptions |
|---|---|---|
| Existing reader → Q1/Q2 | Validated immutable MessageBatch, complete prepared records and its input identity | One-way data; no expected album count or contiguity certificate is supplied |
| Q1 → Q2 | Key and immutable post/member representation | One-way contract; caption selection never replaces member data |
| Caller-held state → Q2 | Prior observation or an explicitly observed absence | Data inward; lookup completeness/failure and collection scope must be named |
| Q2 → Q3 | Derived observations/changes and input recognition context | Data outward; exact accepted representation is stable; local grouping is not a source receipt |
| Q3 → Q2 | Reloaded accepted observations on retry/restart | Recovery data; saving a cursor alone is insufficient |
| Q3 → source acknowledgment | Existing batch ID or full BackfillDeliveryRef | Acceptance assertion only after custody; no fabricated receipt or album-derived cursor |
| Q1–Q3 → Q4 → task description | Obligations, actual behavior and unresolved limits | Evidence/constraints; tests cannot replace definitions by assuming desired outcomes |

Assumptions-not-data check: caller persistence is atomic or provides an explicit recovery contract; loss of a reply is not proof of rollback; input re-query is not exact replay; prior observations are not proof of source completeness; media references require independent blob retention when needed. These are exposed interfaces, not invisible coupling.

## 6. Dependency Order

Q1's contract precedes Q2's combining rule. Q2's input/output contract precedes Q3's concrete receiver. Q4 can inspect existing real source/value facts early, but combined behavioral qualification needs all three interfaces and must precede production adoption. No piece requires a new account/session/health implementation. Independent evidence reads may run together; the inquiry disciplines remain sequential.

## 7. Self-Evaluation

Independence: PASS through the named interfaces. Completeness: PASS against identity, captions/media, batches, bounds, restart, ack and qualification requirements. Reassembly: PASS provided Q3 explicitly supplies prior-state determination and durable acceptance; an in-memory-only helper with no usable persistence contract would fail it. Tractability: four focused questions. Interface clarity: data and assumptions named. Balance: combination and acceptance hold the difficulty, without hiding it in a generic “integration” remainder. Confidence: top-down/bottom-up agree; emission/retention mechanism remains for Innovation rather than being smuggled into a boundary.

Checked all seven decomposition failure modes: no premature cut, high-coupling split, hidden lookup/commit assumption, missing runtime determination, excessive sub-pieces, circular dependency or single unbounded implementation piece. Stop at four questions; further decomposition would split tractable contracts. **PROCEED** to Innovation.
