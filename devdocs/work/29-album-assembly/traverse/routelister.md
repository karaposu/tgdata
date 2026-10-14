# Route map — album assembly concepts

## User Input
Territory: _branch.md and the six saved discipline outputs in this folder. Goal received from _branch.md: Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.

## Map Header
Mode: root/project-space; entry:index-extending. Identities:18; high-priority:11; essential/core:13. Routes are attributable directions, not a selected sequence.

## Route Index

| # | Direction | Engagement | Priority | Essentiality | ✓ |
|---|---|---|---|---|---|
| 1 | Stable Telegram post identity | DEVELOP | HIGH | core | |
| 2 | Lossless captions and media members | DEVELOP | HIGH | core | |
| 3 | Album membership uncertainty | TEST | HIGH | core | |
| 4 | Authoritative prior-observation lookup | REFINE | HIGH | core | |
| 5 | Known receiver state reopening | REFINE | HIGH | core | |
| 6 | Durable receiver acceptance | DEVELOP | HIGH | core | |
| 7 | Idempotent input replay | TEST | HIGH | core | |
| 8 | Receiver collection identity | REFINE | HIGH | core | |
| 9 | Assembly work and retention bounds | TEST | MED | core | |
| 10 | Conflicting member observations | REFINE | HIGH | core | |
| 11 | Downloaded media custody | TEST | MED | core | |
| 12 | Real-component album qualification | TEST | HIGH | core | |
| 13 | Usable receiver integration example | DEVELOP | MED | supporting | |
| 14 | Album-aware source delivery | INVESTIGATE-FRONTIER | LOW | peripheral | |
| 15 | Finite-scope album exports | DEEPEN | LOW | peripheral | |
| 16 | Reconstruction from accepted raw archives | DEEPEN | MED | supporting | |
| 17 | ScrapeOps adapter parity | TEST | LOW | peripheral | |

| 18 | Original source delivery authority | TEST | HIGH | core | |

## R01 — Stable Telegram post identity
Identity:post_identity. Type:project-space × teleological × DEVELOP.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Define immutable album and singleton identities independent of caption location.
Lands:One source entity keeps its key as observed members grow.
Touches:docarchive/sensemaking.md#R3; docarchive/innovation.md#Q1 (the concept's own evidence/manifestations).
WHY:The goal gains one coherent post instead of phantom per-photo records.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Preserve canonical chat/group/message IDs because those identify the source entity.
Meaning-gaps: Exact public field names — low — plan-time naming does not alter the identity rule.
Depth-link:none; depth-signal:formed contract requiring implementation evidence.

## R02 — Lossless captions and media members
Identity:member_preservation. Type:project-space × teleological × DEVELOP.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Preserve every original record and derive convenience views from it.
Lands:Secondary captions and media provenance remain available.
Touches:docarchive/sensemaking.md#R3; reference-probe.json (the concept's own evidence/manifestations).
WHY:The goal gains complete observed content for downstream processing.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Compare multi-caption members because the current consumer returns only the first caption.
Meaning-gaps: Display convenience fields — low — originals remain authoritative.
Depth-link:none; depth-signal:formed contract requiring implementation evidence.

## R03 — Album membership uncertainty
Identity:membership_evidence. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Test what each proposed completion signal actually establishes.
Lands:Observation closure cannot be mistaken for full membership.
Touches:docarchive/sensemaking.md#R4; docarchive/critique.md#D4 (the concept's own evidence/manifestations).
WHY:The goal remains accurate when windows, failures or history visibility omit members.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Use the actual schema and scoped reads because timing alone supplies no count proof.
Depth-link:none; depth-signal:formed contract requiring implementation evidence.

## R04 — Authoritative prior-observation lookup
Identity:prior_lookup. Type:project-space × epistemic × REFINE.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Distinguish required prior values, observed absence and lookup failure.
Lands:A missing argument or failed backend cannot silently become a fresh post.
Touches:docarchive/innovation.md#Q2F; docarchive/critique.md#Q2F (the concept's own evidence/manifestations).
WHY:The goal preserves earlier members across batches and restarts.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Require every affected key because omitted history would otherwise be invisible.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R05 — Known receiver state reopening
Identity:reopen. Type:project-space × epistemic × REFINE.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Separate explicit creation from reopening existing state.
Lands:Lost or corrupt known state refuses rather than resetting.
Touches:docarchive/critique.md#Q3F; docarchive/critique.md#Assembly (the concept's own evidence/manifestations).
WHY:The goal avoids losing accepted album members after a restart.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Exercise missing files and schemas because auto-bootstrap hides prior data loss.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R06 — Durable receiver acceptance
Identity:acceptance. Type:project-space × teleological × DEVELOP.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Define and demonstrate the commit that retains posts and input recognition before raw ack.
Lands:Acknowledged input remains recoverable after process loss.
Touches:docarchive/sensemaking.md#R5; docarchive/decomposition.md#Q3 (the concept's own evidence/manifestations).
WHY:The goal can continue daily without dropping earlier album members.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Use an actual transaction because a success-shaped callback is not durability.
Meaning-gaps: Concrete receiver schema/default details — low — the explicit create/reopen and collection contract is settled; candidate runtime remains to be tested.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R07 — Idempotent input replay
Identity:replay. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Replay accepted input after a lost acknowledgment and after restart.
Lands:Repeated batches do not duplicate members or erase newer accepted membership.
Touches:docarchive/innovation.md#Q3F; docarchive/critique.md#D2 (the concept's own evidence/manifestations).
WHY:The goal survives ordinary delivery retries.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Compare saved bytes and final membership because a repeated call count is not enough.
Depth-link:none; depth-signal:formed contract requiring implementation evidence.

## R08 — Receiver collection identity
Identity:namespace. Type:project-space × epistemic × REFINE.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Make the selected logical destination part of accepted-input lookup.
Lands:Equal batch hashes in distinct collections cannot settle each other.
Touches:docarchive/critique.md#Q3F; docarchive/critique.md#Assembly (the concept's own evidence/manifestations).
WHY:The goal keeps independent collection deliveries correct.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Use two collections with equal input because content identity is not destination identity.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R09 — Assembly work and retention bounds
Identity:bounds. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Measure count/byte refusal and verify prior values remain unchanged.
Lands:Limits stop work explicitly without trimming or partial mutation.
Touches:docarchive/innovation.md#Q2A; docarchive/decomposition.md#Q2 (the concept's own evidence/manifestations).
WHY:The goal remains usable on large histories without silent loss.
Priority:MED. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Test multibyte content and large IDs because scalar counts alone miss byte cost.
Depth-link:none; depth-signal:formed contract requiring implementation evidence.

## R10 — Conflicting member observations
Identity:conflicts. Type:project-space × epistemic × REFINE.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Define exact duplicate and conflicting-record behavior.
Lands:Repeated observations are idempotent while incompatible content requires an explicit response.
Touches:docarchive/innovation.md#Q2F; docarchive/sensemaking.md#R6 (the concept's own evidence/manifestations).
WHY:The goal avoids silently choosing an edit policy or replacing data.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Check immutable-record equality because arrival order must not silently choose content.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R11 — Downloaded media custody
Identity:media_custody. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Check preserved blob references and the caller retention obligation.
Lands:JSON persistence is not advertised as retention of deleted media bytes.
Touches:docarchive/decomposition.md#Interface; docarchive/sensemaking.md#Frame-exit (the concept's own evidence/manifestations).
WHY:The goal keeps the post usable with its media after raw acknowledgment.
Priority:MED. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Keep references and blob lifetimes distinct because they are stored separately.
Depth-link:none; depth-signal:formed contract requiring implementation evidence.

## R12 — Real-component album qualification
Identity:qualification. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Exercise actual value/SDK/storage composition at failure boundaries.
Lands:The contract has observable evidence before production adoption.
Touches:docarchive/innovation.md#Q4F; docarchive/critique.md#Q4F (the concept's own evidence/manifestations).
WHY:The goal avoids building on a false restart or representation premise.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Use real SDK serialization and SQLite because faked providers cannot establish those seams.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R13 — Usable receiver integration example
Identity:receiver_example. Type:project-space × teleological × DEVELOP.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Show the existing raw receipt APIs composed with stored post snapshots.
Lands:Callers have an executable reference for correct acknowledgment ordering.
Touches:docarchive/decomposition.md#Q3; docarchive/innovation.md#Q3F (the concept's own evidence/manifestations).
WHY:The goal becomes easier to adopt without rewriting grouping logic.
Priority:MED. Confidence:MED. Essentiality:supporting.
Guidance Mode:compact. Pointer:Keep the example explicit about ownership because the helper cannot verify another application's storage.
Meaning-gaps: Example API names — low — representation choices can be fixed without changing transactional ownership.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R14 — Album-aware source delivery
Identity:source_wrapper. Type:project-space × teleological × INVESTIGATE-FRONTIER.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Examine what additional readiness contract a source wrapper would provide.
Lands:A future reader API has a concrete purpose beyond grouping existing observations.
Touches:docarchive/innovation_iter1.md#Q1C; docarchive/critique_iter1.md#Q1C (the concept's own evidence/manifestations).
WHY:Indirect: the goal could gain a specialized delivery surface if a caller needs it.
Priority:LOW. Confidence:LOW. Essentiality:peripheral.
Guidance Mode:compact. Pointer:Test the requested extra guarantee because another wrapper does not create source evidence.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R15 — Finite-scope album exports
Identity:finite_export. Type:project-space × teleological × DEEPEN.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Explore explicit bounded-scope closure with qualified output limits.
Lands:A finite export can state what its assembled observations cover.
Touches:docarchive/innovation_iter1.md#Q2G; docarchive/critique_iter1.md#Q2G (the concept's own evidence/manifestations).
WHY:Indirect: the goal gains a specialized closed-input use case.
Priority:LOW. Confidence:MED. Essentiality:peripheral.
Guidance Mode:compact. Pointer:Retain explicit limits because a large history is not a small page.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R16 — Reconstruction from accepted raw archives
Identity:raw_rebuild. Type:project-space × teleological × DEEPEN.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Establish which actual retained raw artifacts can reconstruct prior posts.
Lands:An archive-backed caller can reuse its existing data custody.
Touches:docarchive/innovation.md#Q1C; docarchive/critique.md#Q1C (the concept's own evidence/manifestations).
WHY:The goal can support storage arrangements beyond saved post snapshots.
Priority:MED. Confidence:MED. Essentiality:supporting.
Guidance Mode:compact. Pointer:Identify the archive/index because individual rows are not necessarily full saved batches.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R17 — ScrapeOps adapter parity
Identity:consumer_adapter. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Compare a later adapter with the current consumer fixtures and count semantics.
Lands:Adoption has a known caption/member/count mapping.
Touches:source-input.md; reference-probe.json (the concept's own evidence/manifestations).
WHY:Indirect: the motivating consumer can use the generic capability safely.
Priority:LOW. Confidence:MED. Essentiality:peripheral.
Guidance Mode:compact. Pointer:Keep deployment separate because the running consumer currently uses its own data shapes.
Depth-link:none; depth-signal:contract formed; runtime qualification or the stated alternative applicability remains explicit.

## R18 — Original source delivery authority
Identity:source_receipt. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Distinguish available captured data from a confirmed pending source delivery.
Lands:Only the original daily batch ID or full backfill delivery reference authorizes the corresponding acknowledgment.
Touches:docarchive/decomposition.md#Q3; docarchive/critique.md#Substance (data-versus-receipt distinction).
WHY:The goal gains reliable restart behavior without advancing a source on an unconfirmed delivery.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Exercise failed publication followed by pending replay because a useful partial_result may lack acknowledgment authority.
Depth-link:none; depth-signal:actual source-engine behavior supplies the distinction; candidate composition remains to be tested.

## Excluded
Photo-trail inference, distributed leases, account routing/auth and business classification are separate capabilities and add no required movement toward this album contract. Process instructions such as closing a pipeline gate are not concept routes. Rich duplicated display caches have no additional demonstrated goal contribution beyond the retained-member concept.

## Telemetry
Mode:root/project-space; entry:index-extending. Loaded all17 prior identities; reconfirmed17, split out1 previously implicit source-receipt identity;18 live routes, no stale entries. A second sweep found no further identity. Kinds:teleological7/epistemic11. Priority:HIGH11. Essentiality:core13/supporting2/peripheral3. Namespaces/opening confidence enriched from actual probes; no manifestation dump. Original source receipt is separated from durable receiver acceptance because available data and owed delivery can differ. No priority selection, process control or inter-concept edge recorded. Checked all6 operational and4 identity failure modes. **PROCEED**.
