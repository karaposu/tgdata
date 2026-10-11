# Critique — #10 worker assembly

## User Input

Evaluate Innovation's S1 assembly and its G/F/C alternatives against the saved
Sensemaking and Decomposition. Same warmed session; actual source/process evidence,
no live Telegram. This is design critique, not the later task-plan critic-d gate.

## Dimensions and weights

| Dimension | Weight | Substance-level passing condition |
|---|---|---|
| D1 actual account/allowance | Critical5 | Fresh proof and send admission agree; no cached-ID authority or new quota ledger |
| D2 client/process ownership | Critical5 | No successor work after uncertain cleanup; failure knowledge survives setup/body/cancellation/logging paths |
| D3 completion/irreversible retry | Critical5 | A missing reply never implies no join; no automatic retry/receipt fiction |
| D4 wire fidelity and disclosure | Critical4 | Exact IDs/batches/partial data and qualified group statuses; bounded frames and type-only local errors |
| D5 scope/feasibility | Critical4 | Four requested verbs and resident worker on merged dev, no #17 dependency or unsupplied network/queue platform |
| D6 compatibility/parsimony | Important3 | Existing library behavior retained; smallest sufficient source/driver integration |
| D7 external evidence | Critical5 | Source and lifetime premises tested with actual SDK/SQLite/OS, not desired fake outcomes |

These cover all Sensemaking perspectives. D2 uses the broad ownership meaning
(actual native work, not only public method return). D3/D4 distinguish source
completion, pipe publication and receiver receipt literally. No criterion requires
performing a live join to prove that live joining was not authorized.

Frame premises prosecuted independently: (a) “a persistent worker requires live
clients between jobs”—counterexample is inventory plus temporary verified clients;
(b) “return means cleanup succeeded”—actual probe disproves it;
(c) “JSON-ready means identifiers survive a consumer”—actual Node probe disproves
numeric 64-bit query-ID preservation and verifies decimal-string projection.

## Fitness landscape

Viable: a caller-managed serial protocol over the accepted verified primitives,
with explicit cleanup-failure knowledge, exact wire projection and uncertain-reply
rules. Dead: unverified raw wrappers, callback-written output, ignored cleanup,
automatic uncertain join replay, and cancellable-await-as-thread-termination.
Boundary: HTTP/authenticated service, durable job/output receipt store, per-job OS
children, and throughput-driven concurrency. Those can be useful with a different
selected scope; their added duties are not currently supplied. Unexplored: actual
deployment/proxy behavior and future distributed routing, explicitly outside this
offline first delivery.

## Adversarial candidate verdicts

**G1 HTTP — REFINE/defer.** Prosecution: network reachability adds authentication,
request ownership and deployment policy not present in the issue or consumer input.
Defense: natural for a remote web caller. Collision: technically viable, but fails
D5 for this first delivery. Revival: actual network consumer/transport selection,
with those duties specified. Seed: a transport adapter later, not a second source engine.

**F1 JSON stream — SURVIVE.** Prosecution: naive lines permit unbounded input,
ambiguous duplicate IDs, invalid JSON values and output backpressure. Defense: a
trusted caller process already owns pipes and scheduling. Collision: strict bounded
frames, versioned envelopes and bounded process-local request sequencing fit that
existing relationship without durable queueing. Source cannot start on bad input;
the caller drains output and decides what missing/truncated replies mean. D1–D7
hold at this contract level; implementation must test actual framing, not only dicts.

**C1 durable job queue — KILL for this delivery.** Prosecution: a new acceptance/
retry owner exceeds caller-orchestration scope and still cannot transact a Telegram
join with receipt. Defense: restart convenience. Collision: D3/D5 win. Seed: let
the orchestrator durably record its own intent and handle uncertainty explicitly.

**G2 ordinary source wrappers — KILL.** Prosecution: ordinary batch reads do not
declare expected identity, and source return hides cleanup failure. Defense:
minimal wrapper code. Collision: actual probes defeat D1/D2; fewer lines cannot
replace those guarantees. Seed: reuse verified contexts, not ordinary call defaults.

**F2 verified operations plus cleanup fact — SURVIVE.** Prosecution: a failure
record returned only after normal await would disappear on caller cancellation or
setup failure; logging is not a reliable channel. Defense: one owned helper already
waits for actual disconnect and preserves the primary outcome. Collision: the
candidate records failure before cancellation can escape, and an outer finally
retains a sticky engine fact. Six actual SDK cases pass, including failed setup,
internal SDK cancellation, repeated caller cancellation and broken logging. The
worker must consume that fact to stop; the prototype proves the fact channel, not
an unbuilt worker's admission check. No new global health/lifecycle framework.

**C2 one OS child per job — REFINE/defer.** Prosecution: needs a second IPC protocol,
result custody and child shutdown; adds startup/resource costs without a requested
isolation requirement. Defense: process exit strongly closes resources. Collision:
it remains a legitimate fallback if F2 cannot preserve its guarantees, but the
actual small seam passed. D6 favors F2. Seed: revisit process isolation for genuinely
uncooperative third-party work, not as an unexplained worker default.

**G3 executor stdin/queued async driver — KILL in its proposed form.** Prosecution:
real cancelled await leaves the executor reader/process alive until stdin closes;
queues make admission/EOF harder. Defense: familiar async integration. Collision:
D2/D7 fail for the naive shape. Seed: the source may be async while idle stdin is
ordinary synchronous I/O; avoid a hidden thread that owns termination.

**F3 serial main-thread driver — SURVIVE.** Prosecution: blocking output or idle
input can obscure signals, while a signal during actual source work needs cleanup
to settle. Defense: no source is live during idle I/O; one admitted job naturally
bounds overlap and output pressure. Collision: specify separate idle/active/output
phases. Active signals request cancellation and stop future admission; idle/output
signals terminate the loop. Repeated stop signals must not create new work. No
hard cleanup deadline is promised; the caller may forcibly terminate with an
unknown result. Real process tests must cover these phases before completion.

**C3 per-command-only executable — KILL.** Prosecution: misses “start once” and
resident idle inventory. Defense: very small lifecycle. Collision: D5 wins. Seed:
keep the process, remove persistent account sockets instead.

**G4 exception strings/direct callback stdout — KILL.** Prosecution: secret-bearing
errors and interleaved/observer-controlled replies violate D4/D2. Defense: fewer
projection functions. Collision: unsafe even for a local caller. Seed: one writer
consumes known outcome data; health collection is fixed and job-correlated.

**F4 portable outcomes/collector — SURVIVE with explicit projection.** Prosecution:
existing Python group-result dictionaries contain 64-bit numeric query IDs, unlike
MessageBatch v1's string identifiers; JSON.parse rounds them. Defense: reuse the
source meaning, not necessarily its Python scalar representation. Collision:
decimal-string wire identifiers preserve the group result, and raw MessageBatch
stays unchanged. Actual Node positive/negative signed-64 probes pass after string
projection. Keep counts/booleans as their own types; preserve all join/access
statuses. Drain the fixed bounded notification collector for the current job
before reuse; never let an arbitrary callback own source completion.

**C4 worker archive/receipts — KILL for this delivery.** Prosecution: adds storage,
retention and acknowledgment responsibility the caller already owns. Defense:
helps interrupted delivery. Collision: D5/D6 reject it here without denying that
future receiver adapters could help. Seed: existing batch IDs let the caller store
received data; missing replies remain unknown, not a worker recovery guarantee.

Supporting L/M/I/A/R/N/D/E variations were checked at their corresponding candidate
boundaries: explicit caller custody, serial admission, cleanup-stop policy and
reuse of existing ledgers survive; shared ownership and implicit durable receipts
do not. No supporting variation is silently promoted without its parent verdict.

## Empirical collision

`../probes/source_boundaries.txt`: expected222/cached111 returns2 records and charges
222 only; health is queued after cleanup with owner222/wait7200; a failed disconnect
can leave a connected transport after normal context return. All are actual SDK
composition observations, with synthetic wire explicitly labeled.

`../probes/cleanup_candidate.py` compiles the existing helper/context with only an
optional failure receipt and a sticky engine fact; it does not edit product files.
Six cases preserve their original outcome and expose failure when present. A later
successful legacy operation does not erase that fact. The output field
`candidate_admission_predicate` is a proposed worker predicate, not a claim that
worker code already exists. Its essential property is available before successor
admission, including when cancellation escapes.

`../probes/process_boundaries.txt`: cancelled executor stdin still needs EOF; a real
2MiB pipe write waits for a draining parent after a writer-start handshake; a regular
file cannot simply be passed to this interpreter's read-pipe transport. These
support the chosen simple I/O frame, not a universal OS certification.

`../probes/wire_ids.txt`: native Node JSON.parse changes `9223372036854775807` to
`9223372036854776000` as a number; a decimal string preserves it exactly. The negative
case behaves similarly. This is a worker projection rule, not an unsolicited change
to the merged Python group API.

## Assembly check

S1 combines F1/F2/F3/F4: startup trusted inventory; explicit-account serial jobs;
real verified operations and existing budgets; failure feedback blocking successor
work; portable results/partial batches and collected health; one writer and honest
uncertain completion. Prosecution: the handoff between cleanup fact, active signals
and publication could still allow a next job or lose the known primary outcome.
Defense: failure fact is recorded within owned cleanup, process stop is sticky,
and publishing occurs only after source ownership settles. Collision: these are
explicit plan/test obligations with a proven primitive, not guessed SDK behavior.

**S1 SURVIVES as the first-delivery design.** No durable worker queue, HTTP service,
automatic routing, new budget engine or persistent client pool is needed. The
conceptual question is answered; final code still needs its own plan/critic/tests.

## Accumulator, coverage and convergence

Evaluation round1 screened all twelve core candidates against the fixed dimensions;
round2 challenged the surviving assembly at actual cleanup/cancellation/consumer
boundaries. No new architecture region emerged; the second round constrained the
existing cleanup and wire-projection interfaces. Kill/refinement seeds and revival
conditions are retained above. This is two adversarial evaluation rounds within
one traversal iteration, not a claim of two full traversal runs.

Coverage: all transport/durability/lifetime/concurrency/observer/ownership axes in
Innovation evaluated; unqualified live behavior remains an execution boundary.
Mechanism independence validated by source/OS/consumer observations, not quarantined
structural agreement. Candidate experiments establish primitives, not implementation
success. Dimensional coverage7/7; adversarial strengthSTRONG; landscapeSTABLE after
the named refinements; one clean assembly survivor. No silent dimension drift,
rubber stamp, nitpicking, label-only test or false live claim.

**Signal: TERMINATE with S1 ranked first. Overall: PROCEED to Routelister/CONCLUDE.**
