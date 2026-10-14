# Critique — iteration 2

## User Input

Evaluate current innovation.md's twelve candidates and A2 against `_branch.md`, current sensemaking.md and the first-pass accumulator in critique_iter1.md. This is design qualification, not a PR critique or a claim that unbuilt runtime code passed.

## Phase 0 — fixed dimensions and premise prosecution

Retain D1 membership/identity (Critical), D2 acceptance/custody (Critical, project-specific), D3 raw compatibility/source bounds (Critical), D4 evidence/truthfulness (Critical), D5 resource/failure behavior (High), D6 useful minimum scope (Medium), D7 inherited-frame fitness (Critical), with the same substance criteria as iteration1. Concretely: retain captions and large IDs across splits; preserve committed members through a lost ack; never derive a raw cursor from an assembled post; refuse known-state loss; never turn persistence into completeness; bound/refuse without trimming; supply a usable small composition.

Premise1: perhaps “post” means one final irreversible emission. Then an observation API fails. Original source-input explicitly allows a partial/uncertain result when completeness cannot be guaranteed; no source oracle establishes irreversible finality. Public naming/docs must say observed membership and revision updates.

Premise2: perhaps durable observation state belongs in source progress. Actual source ack clears pending, and arbitrary consumers own different delivery destinations. Moving content custody there creates a new lifecycle; it is not required to merge two observations.

Premise3: perhaps missing receiver state can safely be regenerated. With an advanced source cursor and no retained raw archive, earlier members are unavailable. Real receiver-probe cases1/3 show missing/partial known stores can be refused using existing conventions. Regeneration must require a separately supplied authoritative archive, not guessed None.

These dimensions span the concrete failure plane: opening, individual lookup, transaction, acceptance namespace and original source receipt. No requirement asks the evaluator to simulate finality or acknowledge uncertain data in order to check it. External evidence is required on D1–D4; D5's new bounds remain a future implementation check, not empirically certified here.

## Phase 1 — landscape

Viable: immutable observed posts plus pure required-prior combination and strict receiver acceptance. Dead: independent fragments as the whole solution, blind overwrite, implicit creation on resume, baseline-only qualification. Boundary: rich receipt envelopes, permanent mutable library caches, archive-query-only APIs, source-owned delivery services and global completeness claims. The previously unexplored receiver-opening seam is now concretely specified and independently probed. No additional candidate region emerged in iteration2; it refined a boundary within the same receiver projection.

## Phases 2–3 — adversarial candidates

| Candidate | Strongest prosecution | Strongest defense | Collision / verdict |
|---|---|---|---|
| Q1G | Receipt ownership differs by collection while the same observed album can be shared; cached caption summary loses secondary captions | One envelope is convenient | REFINE on D1/D2 to Q1F: keep data portable and source acceptance separate |
| Q1F | A later member can change a consumer's interpretation of a post already processed | Stable entity ID plus revision and full members expresses that update honestly | SURVIVE D1–D7 as an observed-post contract. No final-emission promise |
| Q1C | Caller may only have projected rows, not a complete indexed raw archive | Query views avoid another saved representation | REFINE on D2/D6: require an actual archive/index input before offering this alternative; not the ready implementation |
| Q2G | Crash loses cache; eviction loses old caption after raw ack | Explicit checkpoint could make it durable | REFINE on D2/D6 to receiver-owned prior observations rather than another mutable engine |
| Q2F | Explicit None can be dishonest and stale prior can discard members | Exact key coverage prevents accidental omission; receiver transaction determines actual current prior | SURVIVE D1–D7 within its explicit caller contract. Pure function cannot certify an arbitrary external database |
| Q2C | Album crossing batches remains multiple independent posts | Fragments retain raw data cheaply | KILL D1/D7; seed: preserve one logical identity and combine prior observed members |
| Q3G | Automatic bootstrap after a lost file falsely authorizes source ack | A comprehensive managed service could be easier to consume | REFINE D2/D6: explicit creation/reopen and separately qualify service ownership; use Q3F now |
| Q3F | Commit succeeds but reply is lost; retry arrives after another batch added members, or same hash reaches another collection | Reopen selected collection, load current prior inside transaction, preserve union, scope receipt, commit then ack original delivery | SURVIVE D1–D7. No filesystem-loss repair or cross-system atomicity is promised |
| Q3C | Removing the receiver example hides the precise failure that motivated iteration2 | Leaves a tiny library API | KILL D2/D7 for this delivery; seed: demonstrate the minimal concrete safe receiver boundary |
| Q4G | Finite live samples cannot certify universally complete historical albums | Live tests could expose additional SDK behavior | REFINE D4/D6: reserve live completeness study for a stronger source-aware contract; do not block pure observed-data composition on it |
| Q4F | A fake provider could conceal failure in real source/ack behavior | New candidate, SDK serialization, SQLite and real source engines must be combined, while scripted bounded source data is disclosed | SURVIVE D1–D7 as the required experiment; a test plan is not a test result |
| Q4C | All old suites pass even if assembler always drops the second photo | Baseline detects regressions | KILL D1/D4; seed: retain baseline and add actual new-operation composition |

## Substance and external-anchor probes

User case: accepted caption today + resumed photo tomorrow. Q3F requires authoritative reopen; individual-key None is legal only after that succeeds. Missing file/schema/collection fails rather than accepting a new partial album. Required-prior mapping prevents omission from implicitly becoming absence.

Literal retry case: batchX stored and source ack lost; batchY subsequently grows album; replayX must union with current persisted Y, not replace it with X's old projection. SQLite receiver-probe cases7/8 demonstrate exclusion of a competing writer and authoritative current lookup; the combined candidate must additionally test this exact membership history.

Literal namespace case: equal raw batch hashes in collectionsA/B require two acceptance records. receiver-probe case6 actually stored both composite keys. Core identity remains `(chat_id, grouped_id)`, because collection is acceptance context rather than Telegram membership.

Literal partial-data case: a PoolReadCapture or failed-publication partial_result may be useful observed data without being an owed durable delivery. Existing source engines, not a post hash, determine whether ack is valid. Example flow must use normal prepare or confirmed pending replay, then unchanged original receipt.

External anchors checked: receiver-probe.json has8/8 passing actual SQLite/SQLiteSyncStore cases; reference-probe.json retains multiple source member IDs but the old consumer helper returns only the first caption; actual message schema has grouped_id but no member-count/complete field. Telegram's [inputSingleMedia](https://core.telegram.org/constructor/inputSingleMedia) describes the message field as “A caption for the media”. Real immutable MessageBatch validation preserves these individual records and strict source ordering. These facts support observation identity/custody; none proves new runtime performance or universal vendor history completeness.

## Phase 3.5 — A2 assembly

Prosecution: data can be correctly combined but lost between acceptance and ack, or marked accepted in a different logical destination. Defense: strict open + collection selection + transaction/current prior + observations/receipt commit precedes unchanged source ack. Crash before commit leaves no accepted input; crash after commit leaves recoverable observations; lost ack replays immutable raw delivery into the current union. Unknown write outcome is resolved by reopening/reading, never by compensation or cursor synthesis.

Collision: the refinement directly answers C1's failure without adding source ownership. A2 **SURVIVE** all7 dimensions. Ranked1 A2; its four independently useful components Q1F/Q2F/Q3F/Q4F rank below the composed contract because no one component satisfies restart integration alone. No unresolved critical design caveat; implementation feasibility must still be demonstrated by the later mandatory experiment.

## Phase 4 — accumulator, coverage and signal

Accumulator references C1's13 candidates and this pass's12 candidates. Current:4 SURVIVE components + A2;5 REFINE alternatives;3 KILLs with seeds. C1 receiver refinement is closed by explicit opening/namespace semantics and8 actual component probes. Former kills (fragment-only, baseline-only) remain dead; no relaxed weights or resurrection. mechanism_independence_status=validated at the contract level using empirical artifacts, actual source/consumer behavior and canonical schema; new implementation status=unbuilt.

Across both iterations the candidates occupy the same observed-value, source-owned-service, archive-query and fragment regions. C1 changed confidence and exposed a receiver boundary inside that existing region; C2 closes it rather than generating another architecture. No adjacent unexamined region is needed for this bounded observation promise. New information decreased from ownership/closure alternatives to one concrete opening contract; repeated inversion finds the same boundaries. Two candidate-generation iterations have now mapped the same regions, with a clean assembled survivor. **TERMINATE**, after required Routelister, with A2.

Telemetry: dimension coverage7/7; late-stage survivors tested on all7; adversarial strengthSTRONG (lost state, lost commit reply, stale retry, wrong namespace, uncertain source publication); landscapeSTABLE in candidate regions; cleanSURVIVE=A2. No rubber stamp, nitpicking, silent drift, self-reference collapse or unanchored convergence. **PROCEED** to Routelister, then qualified task description. Runtime and live claims remain explicitly unmade.
