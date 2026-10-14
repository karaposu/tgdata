# Innovation — bounded album observations

## User Input / Seed

`_branch.md` I1/V1–V4 and decomposition.md Q1–Q4. Seed: make cross-batch grouping reusable without inventing complete membership or a second source-progress authority. Direction comes from the user's daily scraping need and the observed failure of treating album photos as unrelated posts.

Production-task mode over four contract pieces. Inherited methodology: Standard default. Alternative considered: Contrarian-rethink, which would start by removing the proposed helper/persistence layer and look for reuse in already accepted raw records. Decision: retain Standard default with all seven mechanisms, and explicitly test that alternative at Q2/Q3. No user-requested coverage reduction exists.

## Generate — three variations per meta-decision piece

All four pieces are meta-decision pieces: Q1 defines representation/meaning, Q2 chooses how retained state enters, Q3 assigns acceptance ownership, and Q4 sets the proof standard. Each receives generic, focused and contrarian variants before testing. Named shapes are analysis labels, not product API terminology.

### Q1 — Representation

- **Q1G, generic — Combination / ADD-CONTENT:** introduce a rich logical-post format that caches display text, sender summaries, media summaries, counts, source records and readiness fields.
- **Q1F, focused — Lens Shifting + Domain Transfer / ADD-CONTENT:** introduce a small immutable TelegramPost observation. Stable identity names the album `(chat, grouped_id)` or standalone message; revision names exact retained content. Full members remain the source of captions/media. Album membership is explicitly unconfirmed. A catalogue analogy distinguishes an object's identity from revisions of what has been recorded about it; the computing-native analogue is a keyed immutable document revision.
- **Q1C, contrarian — Inversion / REPAIR:** reverse the assumption that a separate representation is needed; extend the raw batch surface into an optional album-batch format. This changes the intervention from adding a derived value to changing the transport representation while retaining v1 as a compatibility path.

### Q2 — Combination and retention

- **Q2G, generic — Lens Shifting:** under a finite export job, buffer the entire declared scope, then group and emit one result per album. Retention bounds can refuse a job too large for the selected buffer.
- **Q2F, focused — Constraint Manipulation REMOVE + Domain Transfer:** remove the assumption that the assembler must own an ever-growing history. A pure operation consumes one raw batch plus caller-loaded prior post observations for the affected keys. Require an explicit entry for every key, including None for an observed absence; omission is not silently interpreted as a new post. Merge identical members by message ID; reject conflicting observations rather than choosing an edit policy. This is a small receiver-side projection operation, not a source engine.
- **Q2C, contrarian — Inversion:** reverse retained state altogether: emit independent per-batch album fragments and ask the consumer to concatenate them. Existence-axis inversion: zero remembered membership. Identity-axis check: fragments would be transport observations rather than the complete accumulated post the consumer needs.
- **Q2A, additional — Constraint Manipulation ADD:** impose zero source I/O and explicit member/byte work bounds on the combining operation. Failure produces no mutated prior value. This tightens the operation enough to make budget/window noninterference structural, rather than a retry convention.

### Q3 — Durable acceptance

- **Q3G, generic — Combination / ADD-CONTENT:** add a new library-owned album store/engine with its own pending output and source acknowledgment orchestration, combining progress and derived membership.
- **Q3F, focused — Domain Transfer + Absence Recognition:** use the caller's existing receiver transaction: load the affected prior posts, combine, write updated post snapshots and record raw input acceptance, commit, then acknowledge using the unchanged raw receipt. The patch-level absence is a reusable post value/combiner; the redesign-level absence is an explicit receiver assembly contract. What is already present in another form is the daily example's atomic record/duplicate-marker transaction. No new generic library persistence engine is needed for this option.
- **Q3C, contrarian — Inversion / REORGANIZE-WITHOUT-ADDING:** reverse the need to persist derived checkpoints. Retain raw input durably first, then rebuild affected posts from the archive when needed. At the system level, the destination's recoverable source data supplies state, rather than a mandatory new post database. This preserves source acceptance but may require indexed archive access.

### Q4 — Qualification

- **Q4G, generic — Extrapolation:** anticipate additional media kinds, #30 and more readers; create a broad general grouping framework and a vendor-wide qualification suite before any first delivery.
- **Q4F, focused — Absence Recognition + Combination / ADD-TEST:** qualify the actual value/receiver composition with SDK1.45 serialization, immutable snapshots, real SQLite, lost acknowledgment, replay, stale/missing prior state, bounds and daily/backfill integration. Explicitly test that end/limit/interrupted batches never certify full album membership. Real source evidence gates any future stronger vendor-dependent closure claim.
- **Q4C, contrarian — Inversion / DO-NOTHING:** reverse the need for new qualification and rely on the existing773 passing checks because raw readers are unchanged. This explicitly challenges the new-test shape rather than merely varying test data.

## Inherited Frame Audit

Central assumptions challenged: a separate representation (Q1C); retained state owned by the assembler (Q2F/Q2C); a new derived persistence layer (Q3C); mandatory new evidence (Q4C). The source-side framing itself is inverted twice: first the reader need not hold a tail; then the receiver can combine already owned observations with zero new source calls. Independent existence and identity axes were both exercised. Constraint ADD and REMOVE both produced candidates. Absence recognition covered patch, redesign-missing, and already-present-in-another-form directions. No audit override or forced additional cycle is needed.

## Five-test cycle

These are conceptual survival checks, not claims that new runtime code has passed. N=novel within this codebase, S=survives the strongest objection, F=fertile, A=actionable, M=mechanism-independent grounds. Every variation entered the cycle; killed candidates are retained here.

| Candidate | N | S: objection and result | F | A | M / disposition |
|---|---|---|---|---|---|
| Q1G | New post contract | Redundant display caches can disagree with preserved records; no current need justifies them | More UI fields possible | Extra validators/fields required | Weaker than Q1F; DEFERRED until a concrete consumer needs a derived field |
| Q1F | New reusable observation | Cannot promise finality; explicit unknown membership and stable identity answer that limitation without losing data | Basis for #30 without heuristic merging | One value module can express it | Caption evidence plus schema/identity facts independently support it; ACTIONABLE |
| Q1C | New transport shape | A format change does not supply a membership oracle and introduces new receipt/capture/worker integration | Future reader API possible | Broad new transport work | DEFERRED until explicitly requested album-aware fetching; it is not needed for the current separate surface |
| Q2G | New finite-scope mode | Long daily/backfill jobs exceed whole-scope retention; explicit bounds make it honest but narrow | Export helper possible | Tractable for finite caller-owned inputs | DEFERRED until a finite export consumer needs one-time emission |
| Q2F | New cross-batch operation | Missing/stale prior state could overwrite membership; required exact key map plus receiver transaction/conditional-write contract exposes the responsibility | Same operation serves daily/backfill and restores from JSON | No source owner changes | Schema limits and real receiver architecture are distinct grounds; ACTIONABLE with that persistence contract |
| Q2C | Repackages fragments | Fails cross-batch assembly itself; consumer still implements the missing merge | Not evaluated after failure | Not evaluated after failure | KILLED at scrutiny |
| Q2A | New bounded pure seam | Large valid observations may exceed policy; explicit refusal and configurable limits preserve data and permit deliberate retry | Predictable local behavior | Measurable without vendor calls | Budget/window boundaries and functional immutability independently support it; ACTIONABLE |
| Q3G | New orchestration | Duplicates lifecycle responsibilities and introduces cross-store settlement while neither store supplies completeness | Larger subsystem could serve a different product | Cost exceeds the established need | DEFERRED until a separately qualified source-aware post-delivery API is requested |
| Q3F | New use of existing acceptance seam | Crash between commit and source ack causes replay; exact raw receipt plus durable post snapshot makes retry harmless | Any backend with the required transaction/conditional-write guarantee can use the pure API | Concrete SQLite receiver/example | Existing destination transaction and source pending-replay code independently support it; ACTIONABLE |
| Q3C | New archive reuse route | Rebuild costs require an index or bounded relevant input; it works if the caller already retains that data | Supports other backends without another library store | Conditional on caller archive facilities | DEFERRED implementation variant; interface permits this later without changing source APIs |
| Q4G | Broad framework | Future scenarios do not establish today's boundary and widen scope before evidence | Potential future research | Not a bounded #29 delivery | RESEARCH FRONTIER, not production scope |
| Q4F | New composition evidence | Offline replies cannot prove vendor completeness; the proposed output does not claim it, and tests must enforce that limit | Protects #30's input foundation | Real SDK/SQLite composition is available now | Independent value, storage and progress components; ACTIONABLE; real-source claims remain separately gated |
| Q4C | Reuses baseline | Existing suites never exercise a new grouping operation or its acceptance path | Not evaluated after failure | Not evaluated after failure | KILLED at scrutiny |

## Assembly check

Q1F + Q2F + Q2A + Q3F + Q4F produce a compact opt-in assembler: immutable observed posts, a pure key-selection/combination operation, and a concrete receiver acceptance example. The caller loads prior values for each affected key, explicitly distinguishes absence from failed/missing lookup, and stores the result before raw acknowledgment. Source APIs, source state schemas, budgets and health attribution stay independent. A post can gain members across many raw batches without requiring an indefinitely growing in-memory stream tail or claiming a final album count.

Tentative public shape for the later description: a lossless TelegramPost value with stable post identity/content revision and to_json/from_json; a function identifying required post keys; an assembly function whose prior-state mapping is required. Exact names/fields/bounds belong to the plan after critique. The receiver example must demonstrate a duplicate raw-batch receipt, both halves of an album, crash/restart and a lost ack. Source receipts remain existing values, never derived from post IDs.

This assembly combines V1's opt-in surface with V3's receiver ownership. V2 and V4 remain deliberately deferred rather than silently forgotten. Full-global membership is always unconfirmed for an album in this first contract; caller processing readiness is not advertised as a Telegram fact. Different nonempty captions remain individual members. No extra RPC, file download or join is needed for the operation itself.

## Axis and artifact grounding checks

Axes covered: API placement (Q1/Q3), output identity/finality (Q1/Q2), retention ownership (Q2/Q3), resource policy (Q2A), acceptance/replay (Q3), evidence (Q4). Every assembly element traces to a tested variation. Grounded against actual artifacts: strict MessageBatch validation; daily/backfill exact pending/ack; real receiver transaction; caption documentation; no album-count field in the observed schema. No field of the source state is invented as already available.

Shared-input check: several mechanisms inherit the desire for raw compatibility, so agreement alone is not proof. Q1C/Q3G explicitly test changing the raw/ownership layer. Their extra machinery still cannot manufacture absent membership evidence. The smaller option is supported separately by the existing receiver transaction and immutable-value seam, not only by the inherited frame. No stronger source-finality rule is promoted from sample data.

## Telemetry / disposition

Generators4/4; Framers3/3. Thirteen variations entered testing; two killed, five ACTIONABLE, five DEFERRED, one RESEARCH FRONTIER. Five actionable survivors completed all five tests; deferred conditional candidates and the frontier have explicit revival conditions above. No untested survivor is selected.

Per-piece logs: Q1 Combination/Lens/DomainTransfer/Inversion; Q2 Lens/ConstraintRemove/DomainTransfer/Inversion/ConstraintAdd; Q3 Combination/DomainTransfer/Absence/Inversion; Q4 Extrapolation/Absence/Combination/Inversion. All are meta-decision pieces; each has generic/focused/contrarian variants. Shape-axis inversion satisfied at Q1 ADD-CONTENT→REPAIR, Q3 ADD-CONTENT→REORGANIZE-WITHOUT-ADDING, Q4 ADD-TEST→DO-NOTHING; Q2's inversion addresses retained-state existence and identity, with no named shape commitment requiring a different axis. No override.

Convergence: value semantics, acceptance transaction and zero-source-call constraint converge from different grounds. No premature evaluation, one-mechanism selection, inherited-frame lock or untethered future framework survived. API preference is still pending; separate assembly remains the best-judgment proposed scope, not a claimed user answer. **PROCEED** to Critique.
