# Sensemaking — terminal login publication
## User Input
`_branch.md`: understand #50's terminal login/session-publication contract across four preserved articulations.

## SV1 — baseline
The request initially looks like adding prompts around phone/code/password and writing a returned value. That understates the meaning of “saved”: the current flow intentionally owns an isolated in-memory credential, while a normal configured reader opens a native SQLite file.

## Phase 1 — anchors
- C1 constraint: use the existing LoginFlow; no automatic login in readers, resend, signup or downstream deployment.
- C2 constraint: keep an existing usable destination intact through pre-publication failure; never report success just because Telegram authenticated.
- I1 insight: secret text, native SQLite bytes and a safe status are different representations/authorities. A filename suffix cannot convert them.
- I2 insight: local save retry must reuse observed authentication; a second code request cannot repair a disk error.
- S1 structural point: config naming/factory is shared with the reader; LoginFlow's state machine/cleanup is shared with its existing application consumer.
- S2 structural point: file publication has a before/after visibility point and an additional persistence-confirmation step.
- F1 principle: operator control of readers is a precondition; no existing repo-wide filesystem lease makes replacement safe against arbitrary active writers.
- F2 principle: a source outcome and local publication outcome must each remain honest after interruption.
- M1 meaning-node: reusable session = the intended ordinary reader can restore identity/key/DC from the published representation.
- M2 meaning-node: deliberate replacement = named destination, explicit operator intent and an unchanged old destination until a completed candidate is ready.

H4/H5 check: “reusable” is tested by reader consumption, not a self-reported saved flag. ScrapeOps is one motivating consumer of the general reader-format boundary.

## SV2 — anchor-informed
This is a terminal operator adapter plus a narrow publication boundary. Authentication stays in LoginFlow. Saving is an explicit transition with its own ownership, failure and success evidence.

## Phase 2 — perspectives and new anchors
**Technical:** actual Telethon SQLiteSession setters can create a fresh database without hand-authoring its schema. Copy the completed credential via StoredSession, not by parsing opaque text in application code. Native own-ID/entity rows matter to reader bootstrap, beyond the key alone.

**Human:** the command should name its resolved destination before sending a code. Existing-file replacement must be deliberate. EOF/Ctrl-C should stop, not begin another login. A message saying “not saved” after a rename may be false.

**Strategic:** a generic arbitrary-store plugin loader is not a prerequisite. Python applications already own store.save through #5; a CLI store backend would need a concrete config/publication contract rather than inventing one for all stores.

**Risk:** SQLite sidecars can contain committed state. Renaming one database file while another process writes it is unsafe; a marker understood only by the CLI cannot prove readers are idle. A post-publication fsync/notification failure cannot be represented as an ordinary untouched-destination failure.

**Resource:** a closed native candidate and same-filesystem publication are locally testable. No live credential or immediate production fix is needed to establish conversion/lifecycle behavior.

**Ethical/systemic:** a terminal password helper can fall back to echoing input; treating its warning as an error is necessary for a no-echo promise. Secret-bearing recovery files/backups need deliberate retention and private permissions, not routine diagnostic dumps.

**Definitional/internal:** “LoginFlow complete” is authorization evidence, not disk publication. “Atomic” must distinguish namespace visibility from power-loss persistence. “Existing” means the intended nonsymlink file and associated SQLite state, not only path.exists.

**Frame-exit completeness:** “session” spans the in-memory flow, opaque store string and native file. Enumeration retains all three; application-store publication remains a legitimate adjacent consumer, but it cannot dictate this CLI's file format. Counterclaim “support all stores now” fails as a necessary condition: no installed store configuration/adapter exists and ordinary file readers need none. Residual active readers belong to the operator's precondition, not an omitted lock implementation.

**Phase/calibration:** the system has no established cross-process reader lease or authorized live login setup. Early delivery must refuse unsupported publication situations and state evidence limits, rather than promise universal coordination or live qualification.

H1/H2/H3/H7 check: four variants remain considered; “small wrapper” is not a proof of small persistence semantics. A full durable login workflow is not assumed merely because interrupted auth exists.

## SV3 — multi-perspective
There are two independent effects: remote authentication and local session publication. The UI must expose both and must not hide their uncertainty. Native file compatibility is the first concrete consumer; replacement/recovery policy remains to be selected against the failure contract.

## Phase 3 — ambiguity collapse
### A1: reusable output versus opaque bytes
Strongest counter: writing session_data to the configured .session path is the smallest faithful wrapper.
Structural test: SQLiteSession opens SQL tables, while session_data begins with the StoredSession codec prefix. The two readers are not interchangeable.
Confidence HIGH. Resolution: publish a reader-compatible representation, with a narrow adapter or explicit supported store. Fixed: end-to-end reader reopen evidence. Excluded: text disguised as a SQLite file. Depends: publication and tests. Model change: serialization is part of the task.

### A2: “saved” versus authenticated
Counter: complete status means the useful work is done; filesystem errors can be treated as cleanup.
Structural test: session_data exists before store.save; no reader can consume an unpublished credential. Conversely, rename can succeed before directory sync or success output fails.
Confidence HIGH. Resolution: distinguish pre-publication failure, publication observed/persistence confirmed, and publication uncertainty. Fixed: success requires publication evidence. Excluded: converting disk failure into another login or claiming old unchanged after a possible replacement. Depends: command outcomes and retry UX.

### A3: reader ownership versus an automatic safety lock
Counter: create a lockfile and claim replacement safe.
Structural test: ordinary reader clients never consult that marker; an open SQLite connection can write after the CLI checks it. WAL is independent persistent state.
Confidence HIGH. Resolution: stopped/coordinated readers and trusted local directory are explicit preconditions; observable conflicts/sidecars must refuse. Fixed: no distributed safety claim. Excluded: using CLI-only locking as proof of global inactivity. Depends: replacement scope and documentation.

### A4: one failed save versus another authentication
Counter: rerun the whole command after every failure; simpler than retained state.
Structural test: completed LoginFlow still holds session_data; another SendCode mutates a remote service and cannot fix local storage.
Confidence HIGH. Resolution: local retry while the completed credential is retained must avoid authentication. Fixed: no implicit resend. Excluded: discarding a completed credential merely to implement an automatic save retry. Depends: in-process retry and interruption policy. Cross-process checkpoint recovery is not thereby required.

### A5: “terminal” versus unattended secret input
Counter: permit piped input or getpass fallback to make automation convenient.
Structural test: issue asks for an explicit terminal workflow; getpass fallback may echo a password. Existing LoginFlow already supplies nonterminal integrations.
Confidence HIGH. Resolution: deliberate terminal interaction and no-echo input are observable preconditions. Fixed: refuse inability to protect input; headless readers unchanged. Depends: input tests and exit outcomes.

### A6: native-file focus versus all-store framework
Counter: tgdata supports pluggable stores, so a native-file-only CLI is incomplete.
Structural test: issue requires qualifying file publication and any supported store path, not inventing a universal loader. Store objects/transactions vary and the current command packaging has no store plugin contract. Existing API already lets applications save directly.
Confidence HIGH for “generic store support is not a prerequisite”; LOW for choosing the final initial destination surface before Innovation. Fixed: avoid an invented universal abstraction. Still viable: file-first or a genuinely concrete store adapter. Depends: scope selection.

### A7: these examples versus the broader failure pattern
Counter: SQLite conversion is the whole problem; once a file reopens, the task is solved.
Structural test: failed publication, cancellation and live-reader races can occur even with correct bytes. The compatibility probe covers only one axis.
Confidence HIGH. Resolution: the broader effect/publication boundary is load-bearing. Fixed: combined behavioral evidence before implementation. Excluded: declaring the isolated conversion test a complete prebuild.

## SV4 — clarified
The output must be compatible, but compatibility alone is insufficient. A precise publication point, preserved old state before it, explicit uncertainty afterward and separate save retries constrain all viable variants.

## Phase 4 — degrees of freedom
Fixed: existing LoginFlow, explicit terminal inputs, current proxy/device policy, compatible reader output, secret-safe observations, no hidden login retry, honest publication phases, operator-owned reader coordination.
Eliminated: writing opaque text as SQLite; opening/truncating the destination during unfinished auth; CLI-only lock claiming reader safety; global plugin framework as a prerequisite; echoing secret input; “success” based only on remote auth.
Still viable for later selection: native file create/explicit replace; new-file-only publication; a concrete supported store if justified; same-process save retry with optional separately justified checkpoint recovery.
Unresolved implementation mechanics: replacement backup/publication durability, interruption handling, exact CLI names/flags and how much recovery to expose. These remain design variables, not hidden decisions.

## SV5 — constrained
The shape is an operator conversation consuming the settled LoginFlow state machine and a publication boundary consuming only complete credentials. Neither may silently restart the other.

## Phase 5 and SV6 — stabilized model
Build a deliberate way to authenticate and publish a reusable credential, where “logged in”, “candidate prepared”, “published” and “durability uncertain” do not collapse into one boolean. Constrain the first supported destination to a concrete reader contract; choose mechanisms in Innovation, then test the actual composition before implementation.

Compared with SV1, prompting is now the thin layer and publication semantics are the critical contract. The model holds without adding an auth engine, distributed coordinator or permanent credential archive. No accommodation-trigger cycle was needed: destabilizing anchors refined effect boundaries rather than requiring exceptions to an unsupported architecture.

## Behavioral evidence and limits
One isolated feasibility probe used real LoginFlow/SRP-independent code path, StoredSession codec, native SQLiteSession, local link/fsync and ordinary ConnectionEngine._account_operation with the existing controlled wire. Result:
```
PASS actual LoginFlow -> StoredSession -> native SQLite -> ordinary verified reader; no extra code; mode0600; link collision refuses; directory fsync supported
```
Sockets were forbidden; no live auth or production path touched. It transferred the auth key/DC, own rows and update states through native APIs, closed and synced the candidate, then reopened under expected4242. This is not the later combined prebuild and does not establish replacement/crash/TTY guarantees.

Primary references: [Python os](https://docs.python.org/3.11/library/os.html#os.replace), [getpass](https://docs.python.org/3.11/library/getpass.html), [SQLite WAL](https://sqlite.org/wal.html). Rename atomicity is not a blanket power-loss guarantee; WAL belongs with its database; getpass's fallback can echo. Actual local capability was probed where stated.

## Telemetry / structural check
SV1–SV6 present. Ten initial anchors across all five types; nine perspectives, three produced material new constraints (human publication message, WAL ownership, getpass fallback). Seven ambiguities tested against explicit counters; six stable resolutions and one destination-selection choice deliberately left open. Six failure modes checked; no self-referential framework is evaluated. Manual8/8: input, six versions, typed anchors, perspectives/hooks, ambiguity pairs, degrees of freedom, evidence/limits, delta/telemetry. Checker absent as attempted at A.
