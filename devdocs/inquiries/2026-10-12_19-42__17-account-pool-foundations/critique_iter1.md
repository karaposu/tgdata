---
model: gpt-6-astra
effort: max
---
# Critique — #17 foundation alternatives, iteration 1

## User Input

Evaluate Innovation's18 candidates/assemblies against `_branch.md`, Sensemaking
SV6 and the actual-code evidence. The user asks whether a missing concept explains
rework and what would make implementation easier. This is not PR approval.

## Phase 0 — Dimensions and frame prosecution

| Dimension | Weight | Substance-level success criterion / anchor |
|---|---|---|
| D1 Causal explanation | Critical | Explains original and neighboring failures without turning revision3 into three rejected rewrites; Git/artifacts and current reproductions decide |
| D2 Source-result authority | Critical | Exact success/error/prefix and known wait survive observer faults with caller cancel requests0; true caller cancellation remains distinct |
| D3 Valid control and lifetime | Critical | No source/observer/control wait cycle; no live-child release; normal external close and stale/foreign scopes retain explicit meaning |
| D4 Independent state obligations | Critical | CAS permission, actual quota and group acknowledgment keep their owners; ambiguous admission/restart/prefix cases remain safe |
| D5 Scope and parsimony | High | Reduces causal edges or ambiguity; does not add a global framework to preserve an avoidable dependency |
| D6 Usable contract | Critical for a proposed delivery design | Caller can obtain observations on errors and know timing, loss and shutdown meaning; no unspecified behavior is called “simpler” |
| D7 Evidence/phase honesty | Critical | Actual SDK/SQLite/task observations versus analogies/mocks; no live or production implementation claim from an in-memory candidate |
| D8 Retained capability | High | Existing-access failover, persistent-client choice and source-free daily/backfill remain, or an explicit alternative states what it gives up |

Purpose-fitness: D1–D4/D7 are essential to the causal answer; D6 is essential before
recommending a concrete first-delivery boundary, but arbitrary field names are not.
D5/D8 tradeoffs do not kill an otherwise coherent alternative; silently changing
those requirements would. User objection tested directly: a new abstraction that
merely moves complexity would not “make things a lot easier to implement.”

Frame-premise prosecutions, independent of candidate preference:
1. What if the router/state core is also wrong? Current controls exercise actual
   identity switching, CAS ambiguity, saved waits and source-free replay; no contrary
   observation. This supports retention, not proof of every possible state history.
2. What if a live operation scope is unnecessary? Busy-only close removes one edge
   but changes external close semantics; passive observations remove another edge.
   A scope is a candidate mechanism, not the fundamental answer by itself.
3. What if passive notifications only rename the await? If source/progress still
   waits for the observer, or close drains an observer that awaits close, the cycle
   remains. The boundary must remove that dependency, not just enqueue it elsewhere.

Axis-absence audit includes pre-existing tasks, providers before source start,
ordinary success as well as partial errors, storage settlement, callback/metadata
failure, cancellation during cleanup and caller-visible event access. The broad
reading of “observer cannot replace source” is used; timeout-only testing is rejected.

## Phase 1 — Landscape

**Viable:** authoritative source facts; separately scoped live/durable ownership;
retained persistent retirement; original budgets/progress; plain observations outside
source settlement. **Dead:** task-status-as-result, task-ID-as-operation, arbitrary
awaited-observer closure, forgotten restart tokens, unified cursor/quota authority.
**Boundary:** backward-compatible callback timing versus passive observation API;
strict busy-close versus automatic active-close convenience; temporary versus retained
clients. **Unexplored within the answer:** the smallest complete notification/control
role contract, including error access and backend limitations. **Outside this task:**
actual two-account qualification and a future shared supervisor with another equal
policy consumer.

## Phases 2–3 — Candidate adversarial accumulator

| Candidate | Prosecution | Defense | Collision / verdict / constructive output |
|---|---|---|---|
| 1G | Global child tracking cannot discover arbitrary user wait dependencies and policies differ by owner | One lifecycle vocabulary could aid future consumers | REFINE D5/D8: only revisit with a second owner sharing an explicit policy; seed is contract reuse, not one universal controller |
| 1F | Context inheritance misses a pre-existing external actor awaited by a callback | Actual descendants, backend, stale and foreign controls pass | SURVIVE as bounded guard component, not graph oracle; D3 requires structural callback/provider roles too |
| 1C | Active external close currently works and is required by public docs | Rejecting all busy closes removes dependency inference | REFINE D6/D8: an explicit alternate stop-then-close API could work; not a silent substitute |
| 2G | Changes all source/error APIs without fixing who decides the outcome | Explicit values discourage exception conflation | KILL D5/D8 for this delivery; seed: keep the completion fact private and preserve public errors |
| 2F | A captured success must not override a genuine caller stop | Separates body truth from secondary completion and supports every terminal path | SURVIVE D1–D8 as an authoritative contract, represented without a required new hierarchy |
| 2C | Reusing dicts can leave the same asymmetric branches | Actual local prototype preserves success/error/prefix while retaining caller cancellation | SURVIVE D1–D8 as the smallest representation candidate; contract/tests, not class naming, are the deliverable |
| 3G | Temporary/persistent/process owners disagree about reuse after cleanup failure | Shared retention mechanics are real | REFINE D5/D8: share only a proven mechanism later; do not unify owner policies now |
| 3F | Retaining a circular wait makes a deadlock permanent | Native retirement/retry/cancellation safety is already established | SURVIVE when combined with valid control admission; seed already incorporated: retention cannot authorize its own wait |
| 3C | Reconnect per attempt does not eliminate observer outcome or control cycles | Fewer persistent credential/retirement states | REFINE D8: separately price the changed client contract; not the prerequisite cure |
| 4G | New journal merges obligations whose recovery and replay differ | Atomic combined facts sound attractive | KILL D4; seed: connect authorities by exact result/token interfaces, not one state store |
| 4F | If source result or cancellation is misidentified, settlement still records the wrong fact | Existing CAS/ledger/receipt mechanisms survived real probes | SURVIVE with Q2 source-fact input; original uncertainty rules stay |
| 4C | Restart forgets permission/wait uncertainty | Fewer state fields and recovery calls | KILL D4; seed: conservative permission survives missing outcome, not fresh health guessing |
| 5G | Another observer queue/supervisor can recreate shutdown cycles and adds delivery guarantees | Useful with real multiple subscriber needs | REFINE D5/D7: defer until those requirements exist; no durable telemetry dependency in this delivery |
| 5F | “Passive” is incomplete without timing, bounds and error-path retrieval; a background drain joined by close can recreate the cycle | Removes arbitrary observers from the active source dependency graph; actual raw/daily/backfill checks preserve facts | REFINE D6: finish the smallest explicit data-delivery/control contract, without designing a bus |
| 5C | A callback awaits an actor created before operation context; close waits for the source still awaiting that actor | Preserves signature and fixes the reported direct cases | KILL D3 as an unrestricted contract; seed: remove/narrow the dependency rather than enumerate task creation forms |
| 6G | Unlimited callback programs imply an unbounded test space | Generated failure combinations can expose blind spots | KILL exhaustive-proof claim D7; seed: role/phase matrix with independent falsifiers |
| 6F | Could mirror a chosen helper instead of challenge its assumptions | Original reproductions, provider and outside-actor controls expose meaningful differences | SURVIVE D1–D8; require assembly checks before implementation, not after bulk router work |
| 6C | Live successful reads will not exercise local cancelled futures/wait graphs | Live account composition is necessary eventually | KILL as a substitute D2/D3/D7; seed: keep live E1 as a distinct downstream gate |

No survivor is merely grounded by the words of this inquiry. Anchors include
canonical public contract (“Calling it from a source callback refuses”), current
source/close code, saved old probes and new actual consumer behavior.

## Phase 3.5 — Assembly prosecution

### A — Owned attempts plus passive observations

**Prosecution:** this could be a pleasant diagram whose missing event retrieval,
provider role or close/drain behavior recreates the same bug. It changes callback
semantics and must not be sold as an internal refactor. If the application must
process an event before source settlement or pool.close waits for that observer,
the dependency has only moved. Arbitrary storage providers still can await foreign
control tasks; a ContextVar cannot prove a global dependency graph.

**Defense:** six new observations on the original runtime, not a fabricated source,
show a useful boundary. For raw/daily/backfill operations the actual100-message
prefix and7200 wait settle with200 charged slots. Application observation then
awaits an outside-created closer or cancels its own future; source facts remain,
clients retire, and daily/backfill replay/ack uses no source. This separates behavior
without replacing routing/state/progress. A direct storage/notification role contract
can bound what the library promises rather than claim arbitrary graph detection.

**Collision: REFINE, D6 only.** Preserve the conceptual architecture; establish the
minimal observable contract before recommending a specific shape: when data becomes
available, how errors expose it, finite retention/drop semantics, who owns application
observers, and that storage backends perform storage rather than await pool lifecycle.
Do not add a durable queue or a broad supervisor to answer those questions.

### B — Unrestricted awaited callbacks plus scope guard

**Prosecution:** the outside-created actor still forms the exact wait cycle despite
all12 narrow prototype controls passing. **Defense:** small code delta and visible
original fixes. **Collision: KILL D3.** The assumption that lineage tagging determines
all await dependencies is false. Seed: notifications may be data rather than programs
executed inside a source-owned lifetime. No broad source rewrite is implied.

### C — Caller stops before close

**Prosecution:** removes a documented convenience and needs a clear outside owner for
stop/await. **Defense:** a coherent simpler lifecycle contract may be desirable for
an unmerged API. **Collision: REFINE D6/D8**, retain as explicit alternative. It does
not by itself establish outcome separation and cannot silently replace A.

### D — Temporary source clients

**Prosecution:** client allocation policy changes without removing the demonstrated
observer/control dependency. **Defense:** could reuse more accepted #7 setup/cleanup.
**Collision: REFINE D8**, defer performance/API choice. No evidence requires restarting
the pool around this policy to fix the established causes.

## Additional empirical evidence

`evidence/critique_observations.py/.txt` ran six histories on unmodified pool/source
methods: raw/daily/backfill × observer-owned cancellation/awaited external close,
with a plain internal capture sink. All preserve prefix100, stored wait7200 and
charge200. The four daily/backfill cases replay/ack after close without source;
raw cases only verify preserved data/close/no further source, not a replay API.
The log's shared replay_source_free field is vacuously true for raw; it is not a
claim that a raw replay method was invoked. A complete public event interface was
not implemented or qualified by this experiment.

The strongest rejected design was tested beyond its intended favorable scope:
`innovation-probe.txt` shows an unmarked pre-existing actor and real wait cycle.
No product code changed, no test expectation was weakened, and no real Telegram
account or ledger was used. Old deadlock subprocesses exit42 only after recording
actual pending dependencies; no task is abandoned in production as a “fix.”

## Phase 4 — Coverage and convergence

All18 variants faced critical-dimension prosecution/defense; survivor components
were checked across all8 dimensions. The original frame's retention assumption was
challenged by1C/3C/4C, and new scope sufficiency was falsified by an independent task.
Mechanism independence is **validated** for the causal diagnosis and retained core,
with literal code/public-contract and empirical anchors. Shared-supervisor ambitions
remain research/frontier, not quietly promoted by analogy.

The causal answer has a clean survivor: incomplete source/observer/control contracts,
not a failed account selector or proof that every component needs rewriting. The
preferred implementation-shape answer still has a D6 refinement. The landscape
changed within the observer/control boundary, and this inquiry has only one critique
iteration. Do not claim the two-iteration convergence criterion is met.

**Signal: ITERATE.** Narrow focus: what is the smallest complete observation/control
contract that removes the demonstrated dependency, preserves useful health reporting
and ordinary external close, and avoids turning the pool into an event framework?
Retain the tested routing/state/progress and original cause findings. No need to
re-articulate the user's input or reopen the whole account-selection design.

Telemetry: dimensions8/8; adversarial strength STRONG; landscape CHANGED at boundary;
clean component/diagnosis survivors yes, complete preferred assembly needs D6.
No wrong dimensions, rubber stamp, nitpicking, silent drift, false convergence,
self-reference collapse, actual-plane blindness or external-grounding absence.
Manual structural10/10 PASS (checker unavailable). **Overall: FLAG — focused iteration.**
