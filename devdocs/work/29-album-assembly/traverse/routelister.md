# Route map — album assembly concepts

## User Input
Territory: _branch.md and the six saved discipline outputs in this folder. Goal received from _branch.md: Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.

## Map Header
Mode: root/project-space; entry:fresh. Identities:17; high-priority:10; essential/core:12. Routes are attributable directions, not a selected sequence.

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

## R01 — Stable Telegram post identity
Identity:post_identity. Type:project-space × teleological × DEVELOP.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Define immutable album and singleton identities independent of caption location.
Lands:One source entity keeps its key as observed members grow.
Touches:sensemaking.md#A2; innovation.md#Q1 (the concept's own evidence/manifestations).
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
Touches:sensemaking.md#A4; reference-probe.json (the concept's own evidence/manifestations).
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
Touches:sensemaking.md#A1; critique.md#D4 (the concept's own evidence/manifestations).
WHY:The goal remains accurate when windows, failures or history visibility omit members.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Use the actual schema and scoped reads because timing alone supplies no count proof.
Depth-link:none; depth-signal:formed contract requiring implementation evidence.

## R04 — Authoritative prior-observation lookup
Identity:prior_lookup. Type:project-space × epistemic × REFINE.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Distinguish required prior values, observed absence and lookup failure.
Lands:A missing argument or failed backend cannot silently become a fresh post.
Touches:innovation.md#Q2F; critique.md#Q2F (the concept's own evidence/manifestations).
WHY:The goal preserves earlier members across batches and restarts.
Priority:HIGH. Confidence:MED. Essentiality:core.
Guidance Mode:compact. Pointer:Require every affected key because omitted history would otherwise be invisible.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## R05 — Known receiver state reopening
Identity:reopen. Type:project-space × epistemic × REFINE.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Separate explicit creation from reopening existing state.
Lands:Lost or corrupt known state refuses rather than resetting.
Touches:critique.md#Q3F; critique.md#Assembly (the concept's own evidence/manifestations).
WHY:The goal avoids losing accepted album members after a restart.
Priority:HIGH. Confidence:MED. Essentiality:core.
Guidance Mode:compact. Pointer:Exercise missing files and schemas because auto-bootstrap hides prior data loss.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## R06 — Durable receiver acceptance
Identity:acceptance. Type:project-space × teleological × DEVELOP.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Define and demonstrate the commit that retains posts and input recognition before raw ack.
Lands:Acknowledged input remains recoverable after process loss.
Touches:sensemaking.md#A3; decomposition.md#Q3 (the concept's own evidence/manifestations).
WHY:The goal can continue daily without dropping earlier album members.
Priority:HIGH. Confidence:MED. Essentiality:core.
Guidance Mode:compact. Pointer:Use an actual transaction because a success-shaped callback is not durability.
Meaning-gaps: Exact new/reopen and collection contract — high — a wrong default can reset retained membership.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## R07 — Idempotent input replay
Identity:replay. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Replay accepted input after a lost acknowledgment and after restart.
Lands:Repeated batches do not duplicate members or erase newer accepted membership.
Touches:innovation.md#Q3F; critique.md#D2 (the concept's own evidence/manifestations).
WHY:The goal survives ordinary delivery retries.
Priority:HIGH. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Compare saved bytes and final membership because a repeated call count is not enough.
Depth-link:none; depth-signal:formed contract requiring implementation evidence.

## R08 — Receiver collection identity
Identity:namespace. Type:project-space × epistemic × REFINE.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Make the selected logical destination part of accepted-input lookup.
Lands:Equal batch hashes in distinct collections cannot settle each other.
Touches:critique.md#Q3F; critique.md#Assembly (the concept's own evidence/manifestations).
WHY:The goal keeps independent collection deliveries correct.
Priority:HIGH. Confidence:MED. Essentiality:core.
Guidance Mode:compact. Pointer:Use two collections with equal input because content identity is not destination identity.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## R09 — Assembly work and retention bounds
Identity:bounds. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Measure count/byte refusal and verify prior values remain unchanged.
Lands:Limits stop work explicitly without trimming or partial mutation.
Touches:innovation.md#Q2A; decomposition.md#Q2 (the concept's own evidence/manifestations).
WHY:The goal remains usable on large histories without silent loss.
Priority:MED. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Test multibyte content and large IDs because scalar counts alone miss byte cost.
Depth-link:none; depth-signal:formed contract requiring implementation evidence.

## R10 — Conflicting member observations
Identity:conflicts. Type:project-space × epistemic × REFINE.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Define exact duplicate and conflicting-record behavior.
Lands:Repeated observations are idempotent while incompatible content requires an explicit response.
Touches:innovation.md#Q2F; sensemaking.md#A5 (the concept's own evidence/manifestations).
WHY:The goal avoids silently choosing an edit policy or replacing data.
Priority:HIGH. Confidence:MED. Essentiality:core.
Guidance Mode:compact. Pointer:Check immutable-record equality because arrival order must not silently choose content.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## R11 — Downloaded media custody
Identity:media_custody. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Check preserved blob references and the caller retention obligation.
Lands:JSON persistence is not advertised as retention of deleted media bytes.
Touches:decomposition.md#Interface; sensemaking.md#Frame-exit (the concept's own evidence/manifestations).
WHY:The goal keeps the post usable with its media after raw acknowledgment.
Priority:MED. Confidence:HIGH. Essentiality:core.
Guidance Mode:compact. Pointer:Keep references and blob lifetimes distinct because they are stored separately.
Depth-link:none; depth-signal:formed contract requiring implementation evidence.

## R12 — Real-component album qualification
Identity:qualification. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Exercise actual value/SDK/storage composition at failure boundaries.
Lands:The contract has observable evidence before production adoption.
Touches:innovation.md#Q4F; critique.md#Q4F (the concept's own evidence/manifestations).
WHY:The goal avoids building on a false restart or representation premise.
Priority:HIGH. Confidence:MED. Essentiality:core.
Guidance Mode:compact. Pointer:Use real SDK serialization and SQLite because faked providers cannot establish those seams.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## R13 — Usable receiver integration example
Identity:receiver_example. Type:project-space × teleological × DEVELOP.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Show the existing raw receipt APIs composed with stored post snapshots.
Lands:Callers have an executable reference for correct acknowledgment ordering.
Touches:decomposition.md#Q3; innovation.md#Q3F (the concept's own evidence/manifestations).
WHY:The goal becomes easier to adopt without rewriting grouping logic.
Priority:MED. Confidence:MED. Essentiality:supporting.
Guidance Mode:compact. Pointer:Keep the example explicit about ownership because the helper cannot verify another application's storage.
Meaning-gaps: Minimal schema and recovery demonstration — mid — must reflect the actual acceptance contract.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## R14 — Album-aware source delivery
Identity:source_wrapper. Type:project-space × teleological × INVESTIGATE-FRONTIER.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Examine what additional readiness contract a source wrapper would provide.
Lands:A future reader API has a concrete purpose beyond grouping existing observations.
Touches:innovation.md#Q1C; critique.md#Q1C (the concept's own evidence/manifestations).
WHY:Indirect: the goal could gain a specialized delivery surface if a caller needs it.
Priority:LOW. Confidence:LOW. Essentiality:peripheral.
Guidance Mode:compact. Pointer:Test the requested extra guarantee because another wrapper does not create source evidence.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## R15 — Finite-scope album exports
Identity:finite_export. Type:project-space × teleological × DEEPEN.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Explore explicit bounded-scope closure with qualified output limits.
Lands:A finite export can state what its assembled observations cover.
Touches:innovation.md#Q2G; critique.md#Q2G (the concept's own evidence/manifestations).
WHY:Indirect: the goal gains a specialized closed-input use case.
Priority:LOW. Confidence:MED. Essentiality:peripheral.
Guidance Mode:compact. Pointer:Retain explicit limits because a large history is not a small page.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## R16 — Reconstruction from accepted raw archives
Identity:raw_rebuild. Type:project-space × teleological × DEEPEN.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Establish which actual retained raw artifacts can reconstruct prior posts.
Lands:An archive-backed caller can reuse its existing data custody.
Touches:innovation.md#Q3C; critique.md#Q3C (the concept's own evidence/manifestations).
WHY:The goal can support storage arrangements beyond saved post snapshots.
Priority:MED. Confidence:MED. Essentiality:supporting.
Guidance Mode:compact. Pointer:Identify the archive/index because individual rows are not necessarily full saved batches.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## R17 — ScrapeOps adapter parity
Identity:consumer_adapter. Type:project-space × epistemic × TEST.
Goal:Implement reusable cross-batch album assembly with preserved raw members, honest observation limits and recoverable acceptance.
Move:Compare a later adapter with the current consumer fixtures and count semantics.
Lands:Adoption has a known caption/member/count mapping.
Touches:source-input.md; reference-probe.json (the concept's own evidence/manifestations).
WHY:Indirect: the motivating consumer can use the generic capability safely.
Priority:LOW. Confidence:MED. Essentiality:peripheral.
Guidance Mode:compact. Pointer:Keep deployment separate because the running consumer currently uses its own data shapes.
Depth-link:none; depth-signal:concept has the named unresolved facet or conditional applicability.

## Excluded
Photo-trail inference, distributed leases, account routing/auth and business classification are separate capabilities and add no required movement toward this album contract. Process instructions such as closing a pipeline gate are not concept routes. Rich duplicated display caches have no additional demonstrated goal contribution beyond the retained-member concept.

## Telemetry
17 identities after a second sweep found no additional goal-relevant identity; kinds:{'teleological': 7, 'epistemic': 10}. Essentiality:core12, supporting2, peripheral3. No uncertain identity suppressed; no stale entries in this fresh index. Checked over-merge, under-coverage, wrong grain, goal loss, type assignment, index drift, selection creep, process coupling, description collapse and manifestation dumping. No selection or inter-concept dependency edge is recorded. **PROCEED**.
