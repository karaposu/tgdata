# Structural critique — terminal login publication
## User Input
Evaluate saved innovation candidates against _branch.md and sensemaking SV6. This is the inquiry's structural critique, not the later plan critic or PR gate.

## Phase 0 — dimensions and burden
D1 reader compatibility (critical): native reader reopens the published file and proves the same account without prompting.
D2 preservation/observable publication (critical): old usable state survives before publication; after an uncertain mutation the command does not lie about whether a session was saved.
D3 source/secret ownership (critical, project-specific): no save-driven SendCode, no secret diagnostics/echo, no cleanup-induced replacement of the intended outcome.
D4 operator fitness (critical): deliberate first login/re-login at the intended configured slot, clear refusals and interruption behavior.
D5 feasibility/coherence (high): existing LoginFlow/SDK/factory preserved; local components testable before product work.
D6 extent (medium): no generalized store/coordination/recovery system without a concrete consumer.
D7 evidence/frame challenge (critical): external code/doc/probe evidence supports claims; constructor mocks or a fake success return are insufficient.

Purpose-fitness: D1–D4/D7 failures would prevent the requested command from doing its job, so cannot be waived for brevity. D6 may choose among viable designs but cannot kill a necessary safety boundary.
Axis check: source ownership, destination integrity, publication visibility/durability, human input and downstream reopen all represented. Broad “failed save” includes after-syscall uncertainty, not just inability to open a file. No check requires writing a real credential or mutating a production destination.

Frame-premise prosecution:
1. What if native files are the wrong target? Existing unmodified readers open native SQLite; arbitrary stores require an application-supplied object. File-first is a concrete first consumer, not a universal claim.
2. What if replacement is unnecessary? Immutable new files are viable, but force config switching for re-login. Preserve create-only default and explicit replacement rather than hiding replacement in first-login behavior.
3. What if “small wrapper” permits ignoring publication uncertainty? The returned credential exists before any write; namespace change precedes directory sync. A single success boolean cannot represent those observed phases.

## Phase 1 — fitness landscape
Viable: native file create/explicit replace with settled credentials, strict operator preconditions, protected candidate/backup and truthful local outcomes; in-process save retry; installed command with actual-component tests.
Boundary: create-only generations (safe but less convenient), concrete store adapters, durable checkpoints, broad conversion API.
Dead: plaintext credential stdout as the ordinary command outcome, active-reader replacement without a rotation contract, rollout-only storage/TTY testing.
Unexplored intentionally: new remote stores and distributed reader ownership; no concrete requirement suggests they beat the bounded native-file survivor for this delivery.

## Phases 2–3 — prosecution, defense, collision and accumulator
### Q1-G — general provider publication
Prosecution: a generic save method cannot establish each backend's compare/commit/durability semantics; it would claim an outcome it cannot observe. Defense: shared UX would help real heterogeneous stores. Collision: REFINE, boundary D5/D6; revive with a named backend and its explicit receipt/conflict contract. Seed: common UI can consume concrete outcomes later without a provider framework now.

### Q1-F — native file publication
Prosecution: an active reader, sidecar or destination changed during code entry can invalidate the preflight; a rename followed by fsync failure can already expose the new credential. Defense: a completed closed candidate, stopped-reader precondition, rechecked identity, private old backup and explicit uncertain outcome address those exact phases without touching auth.
Collision: SURVIVE as refined in Innovation, across D1–D7. The actual code must determine nonsymlink/type/sidecars/change; it cannot rely on the word “safe.” Atomic rename is visibility, not universal durability. Native primitive evidence below supports feasibility; the full composition still must pass its prebuild before implementation.

### Q1-C — immutable new destinations
Prosecution: the user must now edit reader configuration, and a new-path collision still needs atomic refusal. Defense: removes overwrite risk entirely and keeps old readers' credentials intact.
Collision: SURVIVE as fallback/explicit alternative, but ranks below Q1-F for same-slot re-login. No forced config edit in the initial command; default creation already inherits its no-clobber benefit.

### Q2-G — durable checkpoint command
Prosecution: old checkpoint copies and a killed process cannot establish whether Telegram acted; a new persistent credential lifecycle grows the task. Defense: LoginFlow already exports settled state.
Collision: REFINE, boundary D5/D6. Add only after cross-process CLI resume is requested with a retention/ownership/recovery contract. Seed: preserve auth/publication separation now so later resume is additive.

### Q2-F — single-process conversation
Prosecution: one loop per prompt breaks LoginFlow's event-loop binding, while blocking input inside an async runner can delay Ctrl-C and background stdin threads can outlive cancellation. Defense: one retained event loop with synchronous terminal input between settled async actions preserves current ownership; interrupted async actions are cancelled and drained before exiting.
Collision: SURVIVE as refined, D1–D7. Test actual PTY/SIGINT and real LoginFlow together in prebuild; don't infer this from an input stub. The save retry consumes the same completed credential. A stop never becomes an implicit source retry.

### Q2-C — credential emitter
Prosecution: “saves a reusable account session” is not fulfilled by exposing a secret and requiring another program to publish it. Defense: an advanced application already can save session_data safely.
Collision: KILL for this command on D3/D4. Seed: retain the Python API for custom stores; avoid a new stdout-secret convention.

### Q3-F — private native bridge
Prosecution: key-only copying could lose DC/own identity needed by the reader; manual SQLite schema assumptions would drift. Defense: existing StoredSession plus native SQLiteSession properties/entity APIs restore that state; the real ordinary-reader probe passed.
Collision: SURVIVE, with actual bridge/read-back verification as D1's acceptance. It is a completed-login bridge, not a promise to convert arbitrary stored histories.

### Q3-G — general public export/import
Prosecution: arbitrary caches/backends introduce unrequested lifecycle and compatibility commitments. Defense: reusable infrastructure could help future consumers.
Collision: REFINE to research frontier on D6; require an actual second conversion consumer. Seed: keep the first bridge private so its contract can be learned without freezing a universal API.

### Q4-G — operator suite
Prosecution: profiles/inventory/plugins introduce multiple new consumers and state systems. Defense: future repeated onboarding may benefit.
Collision: REFINE to deferred D6; revive when concrete workflows require shared orchestration. Seed: one entry point now can be embedded by ScrapeOps later.

### Q4-F — installed command and actual composition tests
Prosecution: synthetic source replies do not prove live code delivery, and a script calling the API directly misses TTY/packaging. Defense: SDK/storage/TTY components can be real while source responses are controlled; installation and no-network subprocess probes cover the command boundary.
Collision: SURVIVE. State live limits explicitly; perform combined prebuild, permanent suite and installed-entry checks. No public “qualified live” claim.

### Q4-C — prove at rollout
Prosecution: the first real publication failure would be paid for by a production account's credential. Defense: least upfront work.
Collision: KILL on D2/D7. Seed: a small local combined experiment is cheaper than recovering the wrong assumption after rollout.

### CM-R — active-reader replacement
Prosecution: ordinary clients cache credentials and do not share a rotation lock. Defense: a SQLite transaction can coordinate database writes.
Collision: KILL on D2/D3; transaction locks do not invalidate in-memory auth ownership. Seed: a future shared rotation protocol would be prerequisite for this different promise.

### AR-R — separate publication result
Prosecution: a public durable-receipt framework could exceed scope. Defense: the command needs only safe known/not-published/uncertain outcome evidence.
Collision: SURVIVE in the constrained private form. Reports classify actual effect phases, not broad exceptions.

### DT-R — retain prior bytes during replacement
Prosecution: backup adds another credential-bearing file and shares old inode state if made by link. Defense: private per-attempt directory, stopped-reader precondition and bounded retention protect it; it supplies recovery evidence when publication's durability is unknown.
Collision: SURVIVE as refined. Confirm/retain backup before replacing; preserve it on uncertainty; remove it only after confirmed publication or proven no publication, and report cleanup failure without reversing the known outcome.

### EX-R — later resume seam
Prosecution: a speculative recovery schema now would freeze too much. Defense: conceptual effect separation already enables later work.
Collision: REFINE to deferred; no new schema now, revive on an explicit cross-process resume requirement. Seed: don't couple auth input to save attempts.

## External anchors and targeted probes
User anchor: “asks for the phone and code and saves the session.” Q2-C is tested against the final save obligation, not just the first prompts.
Current login.py says “never prompts and never writes the configured account's session”; the adapter preserves that API contract and owns the new terminal/publication layer.

Sensemaking's real-component probe passed LoginFlow→StoredSession→native SQLite→ordinary verified reader, same account/key, no extra code request, private file mode and no-clobber link behavior. It used synthetic Telegram replies but actual SDK/session/reader components.

A second isolated native-file/input probe observed:
```
PASS native SQLite candidate replacement; collision refuses; private old backup survives visibility change
PASS warning-to-error refuses getpass echo fallback before reading secret
```
The first created/closed actual SQLiteSession candidates, checked no-clobber, hardlinked the prior file inside a0700 directory, atomically replaced the destination and reopened its new key. It did not claim active-reader safety or power-loss proof.
The second made actual getpass fallback raise GetPassWarning before its input reader ran; no secret was read with echo.

Primary references: [Python replace/fsync](https://docs.python.org/3.11/library/os.html#os.replace), [getpass fallback](https://docs.python.org/3.11/library/getpass.html), [SQLite WAL](https://sqlite.org/wal.html). These constrain the claim; they do not replace the later combined fault/TTY experiment.

## Phase 3.5 — assembly
A=Q1-F+Q2-F+Q3-F+Q4-F+AR-R+DT-R, with create-only default and explicit replacement.
Prosecution: independent pieces may all work while their composition mishandles a Ctrl-C between rename and reporting, erases retained backup, or restarts source authentication on save failure.
Defense: one conversation owner and one synchronous publication lifetime can preserve explicit outcome evidence; their interface contains no hidden automatic source action. Current native compatibility and filesystem primitive probes support the mechanism; a mandatory combined prebuild must test the exact interrupt/failure ordering before product work.
Collision: SURVIVE as the contract to plan, with no unsupported critical guarantee. Its promise is bounded local POSIX publication under reader quiescence, not cross-process coordination or arbitrary-store durability. Full implementation feasibility remains an enforced prebuild question, not a claimed product PASS.

Ranked:1 assembled file-first command;2 create-only generation fallback;3 named-store/checkpoint extensions when their revival conditions exist. Variants2/4 from articulation are explicitly deferred, not silently forgotten.

## Phase 4 — coverage, convergence and telemetry
Accumulator above evaluates all15 variations and the assembly. Seven dimensions cover representation, ownership, filesystem phases, input, integration, extent and evidence. Mechanism-independence status: validated by current code, native-consumer observation and filesystem/input probes; no purely rhetorical convergence is claimed.

After initial landscape placement, two adversarial re-sweeps kept dimensions fixed:
- Sweep2 replayed failed auth/failed staging, changed target/sidecars and source/cleanup interruption. These map to already-defined refusal, retained credential and stopped-reader boundaries.
- Sweep3 replayed post-replace sync failure, output failure and future-store claims. These map to already-defined uncertain publication/cleanup evidence and deferred backend contract. No new region appeared.
These are critique re-evaluations, not invented additional traverse iterations or claims of a completed full prebuild.

No likely unexplored adjacent region changes the first-delivery choice; the unbuilt store/coordinator families have explicit revival conditions. Eight source concepts checked at their failure plane; no evaluation drift or relaxed safety weight. Adversarial strength STRONG for contract choice, behavioral confidence limited to the probes actually run. Landscape STABLE after the two re-sweeps; a clean bounded contract survivor exists. Nine failure modes considered; no missing critical axis identified.
**TERMINATE — ranked survivor A. PROCEED** to route exhaust and CONCLUDE; then plan and enforce the combined actual-component prebuild.
