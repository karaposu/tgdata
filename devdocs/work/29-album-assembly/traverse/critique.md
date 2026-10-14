# Critique — album contract, iteration 1

## User Input

`_branch.md`, sensemaking.md, decomposition.md and all thirteen variations in innovation.md. Judge the proposed assembler against the user's cross-batch/restart requirement, not merely whether grouping a list is possible. This is an inquiry critique, not a PR rejection or the later critic-d plan gate.

## Phase 0 — Dimensions and weights

| Dimension | Weight | Substance-level success and anchor |
|---|---|---|
| D1 Membership/identity correctness | Critical | A caption in batch1 and photos in batch2 become one stable post with every member preserved; same group ID in another chat remains separate |
| D2 Acceptance/custody | Critical, project-specific | After accepted input and a lost ack/restart, prior members survive; source receipt/cursor remains the existing engine's authority |
| D3 Raw compatibility/source bounds | Critical | No raw hash/schema change and no extra source I/O to assemble; prior members do not become an invented source cursor |
| D4 Evidence/truthfulness | Critical | No page/timeout/end-based global membership claim; actual schema/vendor/consumer evidence must support externally grounded statements |
| D5 Resource/failure behavior | High | Bounded work/retention policy, no silent trim, no partial input/prior mutation on refusal |
| D6 Useful minimum scope | Medium | Reusable cross-batch operation and a usable persistence example, without a second archive/scheduler/reader lifecycle |
| D7 Inherited-frame fitness | Critical | The selected meaning of “one post” must satisfy the user's grouping goal, not merely rename fragments |

Risk axes cover missing/corrupt state and receipt scope, not only normal grouping. “Preserve raw compatibility” is read broadly to include pending replay, media custody and account-pool captures. No criterion requires performing the failure it is checking. Dimensions remain fixed for the next iteration.

### Frame-premise prosecution

1. If “one post” actually meant one irreversible downstream event, revisable observations would be insufficient. The request calls for one logical post and preserves uncertainty at boundaries; it does not establish a final-emission oracle. The current design must clearly advertise observations/updates, not silently promise event finality.
2. If a source marker proved complete membership, a reader-bound tail might be simpler. The examined MessageBatch/SDK interfaces lack that marker, and scoped reads can omit members independently of adjacency. No source-side completeness claim is available to transfer.
3. If caller persistence could not retain prior values safely, the pure helper would not fulfill restart behavior. The actual daily Destination.accept transaction is a usable acceptance boundary, but its first-use/open policy needs separate scrutiny before copying it.

## Phase 1 — Fitness landscape

Viable: immutable observed post values plus explicit prior data and durable receiver acceptance. Dead: independent fragments as the entire solution, guessed completeness, source ack ahead of recoverable data, and qualification that never runs new behavior. Boundary: whole-scope buffering, source-owned post delivery, rich display metadata and archive reconstruction without an indexed accepted input. Unexplored: the concrete reopen/absence behavior of the proposed receiver and its missing-state recovery response; this is adjacent to the viable region and is load-bearing.

## Phases 2–3 — Prosecution, defense, collision and verdicts

| Candidate | Strongest prosecution | Strongest defense | Collision / constructive verdict |
|---|---|---|---|
| Q1G | Cached caption/sender/media summaries can diverge from full members and repeat the first-caption loss | Rich consumers may benefit from convenience fields | REFINE to Q1F now; add a convenience field only when derived without discarding member data |
| Q1F | Unknown membership may be mistaken for a finished album; carrier ID can change when a caption arrives later | Explicit uncertainty and stable chat/group identity prevent that ambiguity; full members remain inspectable | SURVIVE conceptually across D1–D7; names/status must visibly preserve this contract |
| Q1C | A new transport format adds receipt/capture integration yet still has no full-membership oracle | A future source-aware API could coordinate caller-selected closure policy | REFINE/defer to an explicitly requested reader API; use existing derived-layer candidate for current delivery |
| Q2G | A thirty-day stream can exceed whole-scope memory, even though individual raw batches are small | An explicitly finite export can refuse before data loss | REFINE to a scoped export mode if needed; it is not the default solution for daily continuation |
| Q2F | An omitted or stale prior post can overwrite earlier photos | Exact required lookup entries plus transaction/conditional-write ownership make prior state explicit | SURVIVE as a pure operation with mandatory prior-state input and the acceptance precondition; do not make omission mean absence |
| Q2C | Splitting an album into independent fragments leaves the consumer implementing cross-batch assembly | Fragments preserve raw data and require little code | KILL on D1/D7. Seed: retain one stable entity and combine observations instead of treating delivery chunks as posts |
| Q2A | A limit could quietly discard members or leave a half-mutated state | Immutable inputs/results and explicit refusal make resource limits safe | SURVIVE with whole-operation refusal and adjustable, documented bounds |
| Q3G | Another lifecycle increases coupling and can mistake derived completion for raw source acceptance | An integrated delivery service could offer stronger orchestration under its own contract | REFINE/defer; remove unnecessary ownership by using Q3F unless a separately qualified reader-service requirement appears |
| Q3F | A restart can recreate a lost receiver database as empty, return None for every prior key, and accept only later photos after the raw cursor advanced | The receiver transaction is exactly the right layer to preserve membership and input acceptance | REFINE: distinguish explicit creation from reopening; missing/corrupt known state or failed lookup must raise before accepting/acking. Use a caller-selected logical collection namespace for receipts/posts |
| Q3C | Existing receiver rows are not necessarily a saved full-batch archive, and an unindexed rebuild can be unbounded | Recoverable accepted raw input can legitimately supply prior membership | REFINE to a named actual archive/index contract before claiming it as the ready implementation; preserve as an alternative compatible with the pure API |
| Q4G | General future-framework testing delays the concrete feature and cannot prove every future source behavior | Extension-aware tests can protect #30's inputs | REFINE to current obligations; future framework work stays outside this delivery |
| Q4F | Fake replies could be presented as proof of complete Telegram albums | Actual SDK/value/storage composition can qualify a pure operation that explicitly refuses that claim | SURVIVE as a mandatory real-component prebuild and focused regression requirement; stronger vendor claims require their own actual source evidence |
| Q4C | The baseline has never invoked the new operation or its receiver contract | Baseline reuse gives compatibility evidence | KILL on D2/D4. Seed: preserve baseline evidence and add targeted composition/restart tests |

## External-anchor and user-level checks

- User-level edge: one album's caption is accepted today, a crash happens, and tomorrow's remaining photos must not replace it. Q3F's storage reopening policy, not a grouping-key algorithm alone, determines that outcome.
- Canonical source: Telegram documents a per-file caption in inputSingleMedia (`message` is “A caption for the media”). This directly defeats the first-caption-only storage assumption.
- Empirical reference: reference-probe.json runs the actual ScrapeOps helper on synthetic inputs. Two captions produce one returned caption field; equal grouped IDs in two supplied chats produce one post. The current consumer normally processes one chat; this is a generic-library boundary observation, not a claim about a live ScrapeOps defect.
- Actual source code: SyncEngine.acknowledge clears pending and advances after_id; BackfillEngine.acknowledge advances only from its saved pending batch. TelegramPost data cannot replace either receipt. SQLiteSyncStore already has create=False with a mode=rw open, demonstrating that creation/recovery distinction is an existing project pattern rather than a new storage subsystem.

## Phase 3.5 — Assembly candidate A1

Q1F + Q2F + Q2A + Q3F + Q4F is the strongest assembly. Prosecution: the API can be locally correct while the example silently destroys retained membership by bootstrapping after state loss, or mixes accepted-batch markers between destinations. Defense: current components already expose the needed receipt/transaction boundary, and a scoped explicit reopen path can satisfy it without changing any source engine.

**REFINE A1** on D2: carry explicit new/reopen, strict known-schema/load failure, scoped duplicate markers and authoritative prior lookup into the receiver contract. This is one refinement of the existing candidate, not a new architecture. The small pure assembler remains intact. These obligations need concrete real-component evidence before the production plan is adopted.

## Phase 4 — Coverage / accumulator

All13 variations were screened against the critical dimensions; five focused components received full D1–D7 testing. Log: four SURVIVE components (Q1F/Q2F/Q2A/Q4F), seven REFINE candidates including Q3F, two KILLs. Kill seeds and refinement directions are recorded above. External anchors include actual code, direct consumer behavior and primary caption documentation, so mechanism-independence is validated at the concept-evidence level; runtime implementation is still unbuilt.

Landscape changed at the concrete receiver-reopen boundary. A complete clean assembly does not yet survive D2. The first iteration cannot claim two-iteration stability or full convergence. **ITERATE**, narrowly: close the receiver bootstrap/reopen and prior-observation acceptance contract using actual existing SDK/SQLite/value seams; keep dimensions fixed. No new source-reader or archive engine is presumed.

Telemetry: dimension coverage7/7; adversarial strengthSTRONG; landscapeCHANGED; clean complete assembly:none yet; partial survivors:4. No rubber-stamp or qualification-by-label pass. The remaining boundary is explicit, rather than hidden as a small implementation detail. **FLAG — focused second iteration required.**
