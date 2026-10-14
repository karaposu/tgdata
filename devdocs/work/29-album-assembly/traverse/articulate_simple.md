# Articulation — issue #29

## User Input

```text
$task-impl |  |  |  |
|---|---|---|
| #29 — Album assembly across batches | P2 | Not started; ready for qualification |

continue
```

The referenced issue's original body is preserved verbatim in ../source-input.md. This invocation frames the contract question required by triage; it does not replace the requested implementation with a research-only deliverable.

## Itemize

Count: 1. **I1 — Album assembly across batches.** Grouping, retention, restart, documentation and verification are coupled requirements of this one capability, not independently requested features.

## I1: MQ1 — verdict axis

**Question:** What is being requested?

**Explicit-empty:** the requested work kind is explicit: execute task-impl for issue29, whose initial status was not started. The inquiry prepares that implementation. No ambiguity about permission to start the pipeline is perceived.

## I1: MQ2 — context-need axis

**Question:** What context must qualify the response?

**Identified-ambiguities-list:**

- **Verdict:** which source facts identify an album, and which facts justify closing an observation or declaring complete membership? The existing grouping ID and history-end signal may support different claims.
- **Kinds:** raw MessageBatch, logical post, retained assembly state, source delivery receipt, destination acceptance and live observation may need distinct contracts. Which are existing reusable artifacts, and which are new public values?
- **Stance:** should the first API favor strict scope-qualified observations or a best-effort complete-post promise? What real-component and live evidence can qualify the chosen claim, and what remains explicitly unverified?
- **Preparation:** inspect raw-reader bounds, progress/ack semantics, failure prefixes, immutable serialization, consumer fixtures and actual SDK/vendor behavior; establish live resources without resetting account allowance.

## I1: MQ3 — intent axis (WHAT)

**Question:** What concrete endpoint could satisfy album assembly across batches?

**Identified-ambiguities-list:**

- A separate opt-in assembler over existing batches versus a new album-aware fetching surface.
- One finalized post per observed album versus revision/fragment observations with a stable album identity.
- A retained tail versus a bounded collection or caller-backed accumulation that can join nonadjacent members.
- A reusable state value with caller persistence versus integration with a source progress store. The API preference question is pending; a separate assembler is only the agent's provisional direction.

## I1: MQ4 — boundary axis

**Question:** What exclusions constrain every viable reading?

**Identified-ambiguities-list (explicit exclusions inherited from the issue/session):** raw MessageBatch v1 hashes/cursors/acknowledgments stay valid; no budget overrun or out-of-window fetch to complete an album; no discarded member captions/media/provenance; no silent assumption of global completeness; no photo-trail inference (#30), distributed ownership (#31), application classification/contact extraction, permanent edit/deletion reconciliation, or running ScrapeOps migration. Whether the helper stores only retained state or acts as an archive must remain explicit; the earlier library boundary leaves permanent application storage with the caller.

## I1: MQA

**Reconcile:** MQ2's source-evidence axis and MQ3's finalized-versus-revisable endpoint share a closure-contract axis: stronger output finality may require stronger evidence. MQ2's artifact kinds and MQ3's persistence choices share an ownership axis: retaining membership is distinct from accepting a source delivery. These overlaps are exposed without choosing an API, closure rule or storage owner. MQ4 constrains every variant.

## I1: Deconstruct

Tuple: **deliverable** = implemented and verified reusable album capability after qualification; **kinds** = library values/operations, tests, documentation/examples and pipeline evidence; **bounds** = Telegram-marked membership across batches, finite resources, retained original records and compatible raw delivery. No late split is indicated: these pieces support one requested outcome.

## I1: MultiDepth

**Literal statement:** “#29 — Album assembly across batches”.

**Identified-purpose-motivation-ambiguities (WHY):** prevent downstream phantom posts and repeated processing; reduce duplicated consumer-specific grouping; make daily/backfill restarts reliable; provide the stable foundation for later optional photo trails. These motivations may coexist; none selects the delivery shape by itself.

## I1: Considered articulations

1. **V1 — Separate stream assembler.** Implement an opt-in derived post API over raw batches, with explicit retained state and honest completion boundaries, so existing reading/ack APIs remain reusable.
2. **V2 — Album-aware reading.** Implement a separate fetching surface that coordinates bounded reads and group assembly, preserving existing raw APIs and respecting allowance/window limits when complete membership cannot be obtained.
3. **V3 — Receiver projection.** Implement reusable grouping into stable logical-post observations backed by caller-owned accepted records/checkpoints, allowing updates across input batches while making membership uncertainty explicit.
4. **V4 — Bounded observation assembly.** Implement grouping for a caller-declared bounded read scope, retain members across raw batches, and close or export observations explicitly with any scope/partial limits visible.

All variants preserve the implementation deliverable and stated exclusions. They span the API, finality, retention and ownership ambiguities; they do not add a scheduler, permanent content archive owned by tgdata or new business processing. No variant is selected by articulation.

## Self-check

Single lightweight pass: nine LAYER1 modes did not fire. One coupled item; all four MQs and required MQ2 axes present; WHAT/WHY separated; all ambiguity positions use identified lists or explicit-empty; four bounded variants preserve the task shape. Layer2 drift is not claimed evaluated by a single invocation. No independent verifier or new external source was used inside articulation.

**HIGH-PROCEED**
