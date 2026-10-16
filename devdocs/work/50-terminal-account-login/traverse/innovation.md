# Innovation — terminal login publication
## User Input
`_branch.md`, saved SV6 and decomposition Q1–Q4. Generate publication/operator alternatives without replacing the existing authentication API.

## Seed and methodology
Seed: a usable terminal login needs a reliable handoff from isolated authorization to an existing reader's session destination. Valuation: operator convenience must not discard a working credential or silently request more codes.
Inherited mode: Standard default, production-task piece-list Q1–Q4. Alternative: Contrarian-rethink would emphasize zero replacement, zero persisted recovery and zero new publication API; it might reduce failure surfaces but leave the ordinary re-login outcome indirect. Decision: retain Standard default with all seven mechanisms, and explicitly test those contrarian choices. No user request narrows coverage.

Meta-decision classification before generation: Q1 (destination/publication success criteria), Q2 (retry/interrupt frame), Q4 (qualification criteria) are meta-decision. Q3 is content-production within the established native-compatibility boundary. Q1/Q2/Q4 each receive generic/focused/contrarian candidates. No named intervention-shape is inherited; for Q1's new command surface ADD-CONTENT is explicitly challenged by DO-NOTHING/REORGANIZE alternatives below.

## Generate — full candidate set before testing
### Q1 — publication
**Q1-G, generic:** a destination-provider interface supports files and arbitrary application stores with a common durable publication receipt. Lens Shifting: useful when the operator already provisions heterogeneous stores, instead of assuming a laptop file. The interface requires per-backend publication evidence.

**Q1-F, focused:** file-first terminal command builds a closed native SQLite candidate from the completed flow. New destination publication refuses collisions; explicit replacement requires stopped readers, rejects sidecars/changed paths and preserves a private old-file backup before switching. Publication is separately reported from confirmed persistence. Combination joins the already-existing session codec, native SQLite writer and staged local publication pattern.

**Q1-C, contrarian:** invert “a re-login replaces the configured file” to zero overwrites: always create a new destination, then the operator changes reader configuration. At system depth, account credentials become immutable generations selected by configuration, not mutable slots. Existence-axis: no replacement operation at all. Identity-axis: the command publishes a new credential, not an account slot. This also tests ADD-CONTENT publication against DO-NOTHING at the old slot and REORGANIZE-WITHOUT-ADDING to the operator procedure.

### Q2 — operator conversation and recovery
**Q2-G, generic:** persist every settled LoginFlow checkpoint and a publication receipt so a new process can resume phone/code/password/save. Combination with existing export_state, but a durable CLI recovery-state owner is new.

**Q2-F, focused:** one command owns one LoginFlow and event loop. Human input occurs only when its prior async step has settled. Keep the completed credential/candidate for explicit local save retries in that process. Ctrl-C/EOF stops, and unsupported/wait/uncertain source states are reported without automatic restart. Constraint ADD: terminal-only, no secret argv, no durable checkpoint machinery, publication supported only where local filesystem guarantees can be tested.

**Q2-C, contrarian:** remove the persistence constraint entirely: finish authentication and emit the credential for another program to save. Inversion at system depth turns tgdata into a credential emitter and downstream tooling into the publisher; no save retry state inside the command. It removes local lifecycle work but changes the requested user outcome and exposes secret transport surfaces.

### Q3 — native representation
**Q3-F, patch-level absence:** add a narrow private completed-login-to-SQLite bridge, using StoredSession decoding and native setters/process_entities. The missing item is a compatible publisher, not an auth algorithm.

**Q3-G, redesign-level absence:** make session export/import/publication a general public capability of all session backends. Bidirectional absence check: the supposedly missing capability is partly present already—session_data, StoredSession and SQLiteSession provide the pieces. A generic facade would add new promises about arbitrary existing caches/credentials, beyond this isolated login flow.

### Q4 — delivery and qualification
**Q4-G, generic:** extrapolate many operators/backends into a full onboarding utility with profiles, persisted resume, store plugins and session inventory. Future scale may make this useful, but it is not today's concrete consumer.

**Q4-F, focused:** publish one installed command plus module entry, docs and an actual-component prebuild, followed by permanent fault/TTY/reader integration tests. Domain Transfer: native computing's staged file commit/read-back pattern plus a physical handover checklist—possession and usable delivery are different checkpoints. Do not equate a checklist with a runtime lock.

**Q4-C, contrarian:** invert “real-component prebuild is needed” into a help/prompt smoke test plus live trial at rollout. At system depth, defer publication-contract verification to the operator environment rather than verify library composition beforehand. This tests the inherited criterion, not merely a different test count.

### Cross-piece mechanism variations
- **Constraint REMOVE, CM-R:** allow active readers during replacement and rely on SQLite locking. This could avoid operational downtime if all readers adopted a shared rotation protocol; existing readers do not.
- **Absence redesign, AR-R:** if designed from scratch, publication would expose separate remote-authorized/local-published outcomes. Existing LoginStatus deliberately stops before persistence; adding its missing result to the command does not require changing that status.
- **Domain Transfer, DT-R:** retain old credential bytes as a rollback asset before replacement, analogous to a deployment's prior release; make the backup private and its retention explicit rather than automatic credential history forever.
- **Extrapolation, EX-R:** if asynchronous checkpoint recovery becomes a requirement, add it later as a separate command contract. The current in-process save retry should survive that addition without being thrown away.

## Inherited Frame Audit
Central assumptions challenged: native-file publication is needed(Q1-G/Q1-C/Q2-C); mutation is appropriate(Q1-C); completed credentials need CLI ownership(Q2-C); early real-component evidence is worthwhile(Q4-C).
Q1's frame/success criterion is inverted by immutable generations. Q2's in-process recovery frame is inverted by an external publisher. Q4's evidence criterion is inverted by rollout-only testing. Q3's private-bridge boundary is challenged by a public export/import redesign.
No unchallenged load-bearing assumption remains; no audit override or return cycle required. Stronger alternatives were generated before testing.

## Test — five criteria for every variation
N=novelty in this repo; S=scrutiny survival; F=fertility; A=actionability; I=independence of grounding. Novelty alone is not a shipping criterion.

| Candidate | N | S — strongest objection and result | F | A | I | Disposition |
|---|---|---|---|---|---|---|
| Q1-G | new provider contract | each store's durability/conflict rules differ; no concrete CLI store config exists | high future | low now | store semantics, not just file analogy | DEFERRED until a named backend/consumer needs terminal provisioning |
| Q1-F | new command handoff | rename alone cannot prove inactivity/persistence; refine with explicit stopped-reader precondition, sidecar/change refusal, private backup and uncertain outcome | supports reader reuse | high with probes | native SDK compatibility + filesystem semantics + operator intent | survivor, refined |
| Q1-C | new immutable-generation workflow | preserves old bytes but forces config migration and still needs a protected publication path | useful alternate mode | feasible | source ownership + absence of overwrite | viable fallback, not primary; retained if replacement proves too costly |
| Q2-G | durable CLI flow owner | stale checkpoints and interrupted source requests are not exactly-once; recovery/security retention expands scope | high later | medium/large | existing export API supports settled state only | DEFERRED until cross-process CLI resume is requested |
| Q2-F | thin in-process orchestration | blocking terminal input inside a running async task can delay first Ctrl-C; refine to one persistent loop with input between settled async actions and explicit interruption draining | compatible save retry | high with real TTY probes | flow's loop binding + terminal behavior, not only convenience | survivor, refined |
| Q2-C | emitter pipeline | stdout/pipe credential transport plus downstream save fails the requested reusable-session command | useful advanced integration | technically possible | existing Python API already supports this | killed as initial delivery; no second credential-output interface |
| Q3-F | private compatibility bridge | must retain DC/key/own rows and reopen the ordinary reader; isolated probe passes, combined proof still required | enables file-first command | high | actual native reader evidence | survivor |
| Q3-G | broad public capability | would promise conversion of arbitrary session caches/backends; no such consumer identified | high speculative | large | current APIs already provide primitives | RESEARCH FRONTIER, not a prerequisite |
| Q4-G | operator suite | many unrequested concepts/profiles/store plugins obscure the small command | high future | low now | extrapolation alone | DEFERRED when multiple concrete operator workflows exist |
| Q4-F | native composition proof | synthetic source cannot validate live delivery; keep that limit explicit and use actual storage/TTY/SDK for local claims | reusable regression | high | native APIs + fault outcomes + user handoff | survivor |
| Q4-C | rollout-only proof | would place a delicate credential publication premise after implementation/production use | low | easy but unsafe evidence order | no independent support | killed |
| CM-R | no reader downtime | SQLite lock is not a credential-rotation protocol; old clients can retain and save old auth state | possible future | not now | current factory/session lifetime | killed for this scope |
| AR-R | explicit publication result | could become oversized public receipt machinery; keep a private command outcome with known/uncertain distinction | useful now | high | LoginStatus scope + filesystem failure phases | survivor, constrained |
| DT-R | private prior-file retention | extra secret copy needs protection/retention policy; keep only a bounded per-attempt backup through uncertainty and clean it after confirmed success | recovery safety | high with tests | deployment handoff analogy tested against actual file semantics | survivor, refined |
| EX-R | future resume seam | must not force a checkpoint schema now; retain conceptual auth/publish separation only | later additive | no current code beyond seam | existing LoginFlow checkpoint contract | DEFERRED with explicit request trigger |

Artifact-grounding: current setup exposes only worker; flow never writes destination; batch_files already stages non-replacing artifacts; SQLiteSession supplies native schema; ordinary readers consult no CLI lock. These concrete artifacts support the scope verdicts. No diagram or invented public type is treated as implementation evidence.

Mechanism independence: Combination and Absence alone would merely repeat SV6. Independent grounds are the successful native-reader conversion probe, SQLite sidecar persistence, getpass fallback code and the existing reader's lack of a rotation gate. Their objections refined Q1-F/Q2-F; convergence is not claimed solely from shared upstream text.

## Assembly and re-test
Assembly candidate A: Q1-F + Q2-F + Q3-F + Q4-F + AR-R + DT-R. File-first, deliberate create/replace, existing LoginFlow, narrow native bridge, retained in-process retry and honest publication result. Emergent value: no custom reader/store bootstrap is needed, and a failed save can be repaired without another code request.

Re-test trigger from Q1-C: is replacement itself necessary? It is not needed for first login, but an explicit opt-in replacement serves the requested re-login at the existing configured slot without silently editing config. Keep create-only as default; allow replacement only under the stricter stated preconditions. If real combined probes cannot preserve the old file and classify outcomes with a small protocol, kill replacement rather than grow a universal coordinator.

Re-test trigger from Q2-F: one asyncio.run per input would violate LoginFlow's loop binding. The command must own one loop across inputs. No background stdin thread is assumed cancellable.

Re-test trigger from DT-R: a hardlink backup preserves old bytes but also shares an inode with active readers. It is recovery evidence only under the stopped-reader precondition; it is not a lock. Cleanup failure must not turn known publication into failure or erase the original outcome.

Axis coverage: destination backend(Q1-G/F), overwrite policy(Q1-C/F), recovery persistence(Q2-G/F/C), auth trigger(Q2), publication success evidence(AR-R), coordination(CM-R), qualification timing(Q4-F/C). Every assembled element has a generated/tested source above. No silent default row.

## Mechanism and piece telemetry
All4 generators and3 framers fired: Lens(Q1-G), Combination(Q1-F/Q2-G), Inversion(Q1-C/Q2-C/Q4-C), Constraint ADD(Q2-F)/REMOVE(CM-R), Absence patch(Q3-F)/redesign(Q3-G/AR-R with already-present check), Domain Transfer(Q4-F/DT-R, native and cross-domain), Extrapolation(Q4-G/EX-R).
Q1 meta: Lens/Combination/Inversion(scope,intervention-shape); generic/focused/contrarian3/3; inversion satisfied.
Q2 meta: Combination/Constraint/Inversion(recovery/ownership);3/3; inversion satisfied.
Q3 content: Absence/Combination; private bridge versus redesign tested.
Q4 meta: Domain Transfer/Extrapolation/Inversion(evidence timing);3/3; inversion satisfied.
15 variations entered all five tests;7 refined/actionable survivors assembled;4 deferred,1 frontier,3 killed. No absent mechanism, untested survivor or shape-axis violation. Six failure modes checked; no override required.
**PROCEED** to structural critique. Assembly is a candidate, not yet the final chosen contract.
