---
model: unknown
effort: unknown
---

# Route map — message-batch concepts

## User Input

Territory: `_branch.md` and the six saved discipline artifacts in this folder.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Received Goal from `_branch.md` (verbatim; the short label above is used in route records):

Deliverable shape from Deconstruct:
Deliverable: implemented versioned reader/processor contract. Kinds: public
library behavior, documented data format, continuation/media representations,
serialization/files and tests. Bounds: Telegram reading and produced artifacts;
the later receiving worker/orchestration remains separate. Existing-call
compatibility and media mode are open design readings, not settled here.
No late split: the tuple still describes one contract with coupled outputs.

Context still needed:

**MQ2 — What preparation/context does the response need?**
Identified-ambiguities-list:
- Verdict axis: current read/cursor behavior versus downstream consumer
  requirements that are not yet a schema; which existing behavior is a constraint.
- Kinds axis: message projection, envelope/version, cursor, media references,
  local artifacts and interruption results; their exact representations are open.
- Stance axis: a small explicit v1 contract for a later worker versus a broad
  archival format preserving every vendor-specific field.

WHY-axis openness: independent evolution of
reader/processor deployments; recovery from repeated uploads; archival fidelity
when Telegram messages or media change. The wording supports all three,
without ranking them.

Boundary axis:

**MQ4 — What is explicitly excluded?** Explicit-empty for additional exclusions
in the raw issue. Session constraints remain part of the substrate: this task
is #6, #10's worker is separate, unrelated edits are preserved, and implementation
does not authorize merge/deployment.

## Map Header

Mode: root / project-space; entry: fresh. Thirteen identities, seven HIGH-priority
routes, eleven core routes. Attributes describe goal relations, not a selection
or execution order. The index's done column is intentionally empty.

## Route Index

| # | Direction | Engagement | Priority | Essentiality | ✓ |
|---|---|---|---|---|---|
| 1 | Versioned message representation | DEVELOP | HIGH | core | |
| 2 | Stable snapshot identity | DEVELOP | HIGH | core | |
| 3 | Completed-prefix continuation | DEVELOP | HIGH | core | |
| 4 | Verified content-addressed media | DEVELOP | HIGH | core | |
| 5 | Media eligibility and download mode | REFINE | HIGH | core | |
| 6 | Shared quota and health behavior | TEST | HIGH | core | |
| 7 | Existing API compatibility | TEST | MED | core | |
| 8 | Replay and acknowledgment obligations | REFINE | MED | core | |
| 9 | Telethon 1.45.0 contract evidence | TEST | HIGH | core | |
| 10 | Version acceptance and evolution rules | REFINE | MED | core | |
| 11 | Bounded read and file-processing work | DEVELOP | MED | core | |
| 12 | Generalized scanner for multiple formats | INVESTIGATE-FRONTIER | LOW | peripheral | |
| 13 | Acknowledgment-aware worker streaming | INVESTIGATE-FRONTIER | LOW | peripheral | |

## R01 — Versioned message representation

Identity: `wire-record`. Type: project-space × teleological × DEVELOP.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Define exact record/envelope fields, scalar types and absence rules.
Lands: A documented v1 value that preserves the requested raw fields.
WHY: The goal gains an interchange contract independent of presentation and SDK field drift.

Priority: HIGH; Confidence: MED; Essentiality: core.
Guidance Mode: compact.
- Specify missing-sender/service records (bc they expose lossy presentation assumptions).
Meaning-gaps:
- Exact optional field depth — [mid] — the implementation must have a concrete schema.
Touches: `sensemaking.md#A1` (this concept’s recorded evidence), `decomposition.md#P1` (this concept’s recorded evidence), `critique.md#P1-F` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R02 — Stable snapshot identity

Identity: `snapshot-identity`. Type: project-space × teleological × DEVELOP.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Bind identity to canonical saved payload bytes and validate reload.
Lands: Replayed output retains its identity and mutation/tampering is detectable.
WHY: The goal gains recognizable repeat delivery without assuming unchanged server history.

Priority: HIGH; Confidence: HIGH; Essentiality: core.
Guidance Mode: compact.
- Exclude local roots and export time from identity (bc neither describes the snapshot).
Meaning-gaps:
- Canonical byte grammar — [mid] — digest reproducibility needs an explicit encoding.
Touches: `sensemaking.md#A2` (this concept’s recorded evidence), `innovation.md#P1-F` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R03 — Completed-prefix continuation

Identity: `continuation`. Type: project-space × teleological × DEVELOP.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Tie chat-scoped continuation to completely prepared records.
Lands: Interruption exposes a prefix and retries begin before unfinished work.
WHY: The goal gains resumability without silently skipping requested data.

Priority: HIGH; Confidence: HIGH; Essentiality: core.
Guidance Mode: compact.
- Probe failure on the second message (bc a nonempty prefix reveals cursor errors).
Touches: `sensemaking.md#A3` (this concept’s recorded evidence), `decomposition.md#P3` (this concept’s recorded evidence), `critique.md#P3-F` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R04 — Verified content-addressed media

Identity: `blob-publication`. Type: project-space × teleological × DEVELOP.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Publish only complete bytes under their content digest.
Lands: Concurrent producers can reuse a verified complete file.
WHY: The goal gains portable media identities that make repeated uploads recognizable.

Priority: HIGH; Confidence: HIGH; Essentiality: core.
Guidance Mode: compact.
- Use a private temporary file and verify existing digest paths (bc names alone do not prove contents).
Touches: `innovation.md#P2-F` (this concept’s recorded evidence), `critique.md#P2-F` (this concept’s recorded evidence), `../probe_batch_seams.py` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R05 — Media eligibility and download mode

Identity: `media-mode`. Type: project-space × epistemic × REFINE.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Make references-only and requested file preparation unambiguous.
Lands: Callers know which assets a complete record promises.
WHY: The goal gains honest media references and predictable network/storage work.

Priority: HIGH; Confidence: MED; Essentiality: core.
Guidance Mode: compact.
- Specify supported SDK attachment kinds (bc a truthy attachment is not necessarily downloadable).
Touches: `sensemaking.md#A3` (this concept’s recorded evidence), `decomposition.md#P3` (this concept’s recorded evidence), `innovation.md#P3-F` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R06 — Shared quota and health behavior

Identity: `guarded-reads`. Type: project-space × epistemic × TEST.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Exercise the new reader and media refresh through the existing client guard.
Lands: Actual sends remain charged and original failures retain their meaning.
WHY: The goal gains a batch path that respects account safeguards.

Priority: HIGH; Confidence: HIGH; Essentiality: core.
Guidance Mode: compact.
- Include a quota stop during implicit media re-fetch (bc that read is easy to overlook).
Touches: `decomposition.md#P3` (this concept’s recorded evidence), `critique.md#D4` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R07 — Existing API compatibility

Identity: `legacy-compatibility`. Type: project-space × epistemic × TEST.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Compare existing DataFrame/callback/media behavior before and after integration.
Lands: Current callers retain their established return and filename contracts.
WHY: The goal gains adoptability without requiring unrelated migrations.

Priority: MED; Confidence: HIGH; Essentiality: core.
Guidance Mode: compact.
- Run the supported offline regressions (bc the shared façade still connects both APIs).
Touches: `sensemaking.md#Phase-4` (this concept’s recorded evidence), `critique.md#P3-C` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R08 — Replay and acknowledgment obligations

Identity: `delivery-obligation`. Type: project-space × epistemic × REFINE.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Specify save, resend, receiver deduplication and cursor-commit responsibilities.
Lands: A caller can distinguish prepared output from acknowledged delivery.
WHY: The goal gains a usable recovery procedure instead of an unsupported exactly-once claim.

Priority: MED; Confidence: HIGH; Essentiality: core.
Guidance Mode: compact.
- Use the repeated-upload example literally (bc refetch is a different server observation).
Touches: `sensemaking.md#A5` (this concept’s recorded evidence), `critique.md#P4-F` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R09 — Telethon 1.45.0 contract evidence

Identity: `sdk-grounding`. Type: project-space × epistemic × TEST.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Verify the relevant SDK iterator and file-output composition on 1.45.0.
Lands: Implementation assumptions have observed local SDK evidence.
WHY: The goal gains confidence at the actual chosen dependency boundary.

Priority: HIGH; Confidence: HIGH; Essentiality: core.
Guidance Mode: compact.
- Retain synthetic transport and forbidden sockets (bc local control flow is the intended verification scope).
Touches: `_branch.md#User-Steering` (this concept’s recorded evidence), `critique.md#External-evidence` (this concept’s recorded evidence), `../probe_batch_seams.py` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R10 — Version acceptance and evolution rules

Identity: `schema-evolution`. Type: project-space × epistemic × REFINE.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Define which schema versions and field changes readers accept.
Lands: Consumers can reject unsupported formats deliberately.
WHY: The goal gains independent evolution with explicit compatibility boundaries.

Priority: MED; Confidence: MED; Essentiality: core.
Guidance Mode: compact.
- Specify unknown-version handling (bc version labels are useful only when behavior follows them).
Touches: `decomposition.md#P1` (this concept’s recorded evidence), `innovation.md#P1-F` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R11 — Bounded read and file-processing work

Identity: `bounded-work`. Type: project-space × teleological × DEVELOP.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Bound message preparation and choose a memory-conscious file-processing policy.
Lands: Large reads/assets have an explicit resource contract.
WHY: The goal gains a practical worker-ready unit without accidental full-history work.

Priority: MED; Confidence: MED; Essentiality: core.
Guidance Mode: compact.
- Specify limit validation and chunked hashing (bc a finite record count alone does not bound file memory).
Meaning-gaps:
- Exact limit and I/O scheduling policy — [mid] — resource behavior must be concrete before implementation.
Touches: `sensemaking.md#Resource-feasibility` (this concept’s recorded evidence), `decomposition.md#P3` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R12 — Generalized scanner for multiple formats

Identity: `shared-scanner`. Type: project-space × teleological × INVESTIGATE-FRONTIER.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Examine whether multiple real consumers need one generalized scan state machine.
Lands: Evidence about the value and cost of consolidating read loops.
WHY: Indirect: the goal may gain lower future maintenance, but the current contract can stand alone.

Priority: LOW; Confidence: MED; Essentiality: peripheral.
Guidance Mode: compact.
- Compare actual consumers before generalizing (bc speculative sinks enlarge compatibility risk).
Touches: `innovation.md#P3-G` (this concept’s recorded evidence), `critique.md#P3-G` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## R13 — Acknowledgment-aware worker streaming

Identity: `ack-stream`. Type: project-space × teleological × INVESTIGATE-FRONTIER.
Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

Move: Explore an explicit delivery/backpressure protocol for a future worker.
Lands: A possible job/ack model grounded in a real receiver.
WHY: Indirect: later worker orchestration may use the batch contract more safely.

Priority: LOW; Confidence: LOW; Essentiality: peripheral.
Guidance Mode: compact.
- Ground ownership in #10 (bc the reader library does not contain a receiving service).
Touches: `innovation.md#P4-C` (this concept’s recorded evidence), `critique.md#P4-C` (this concept’s recorded evidence).
Depth-link: none; no separate depth run exists.

## Excluded

- Proxy reachability and stepwise login: adjacent issues, but engaging them does
  not define this message/cursor/media contract.
- Deployment and PR/merge mechanics: process-control actions, not concept routes.
- Renaming historical scoped documents: no direct bearing on the current goal.

## Telemetry and self-assessment

Two sweeps (records/files, then failure/delivery/evolution) plus a confirmation
sweep produced no new identity. Thirteen identities: seven teleological and six
epistemic; seven HIGH priority; essentialities eleven core, two peripheral.
No uncertain individuation, stale entry or uncovered frontier is hidden. The two
future concepts are listed as routes, not selected/deferred by this map. No
inter-concept dependency edges or process state occur in the concept index.
Checked over-merge, under-coverage, grain, goal, type and index drift; also
selection creep, process coupling, description collapse and manifestation dumps.
Both required files written. Manual structure/typing 7/7. **PROCEED**.
