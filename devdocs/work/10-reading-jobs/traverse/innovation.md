# Innovation — #10 worker design candidates

## User Input and seed

Generate worker-contract candidates for decomposition Q1–Q4, grounded in SV6 and
the source/process probes. Value: a small usable reader process whose simple
interface does not hide account ownership or uncertain completion.

Seed type: gap plus constraint. Inherited methodology mode: Standard default,
production-task question list. Alternative: Contrarian-rethink, which would start
by removing the persistent worker or its inventory entirely. Decision: retain the
balanced mode and explicitly test those reversals. All seven mechanisms fire;
every Q1–Q4 piece is meta-decision (frame/criterion) and receives generic, focused
and contrarian candidates before testing. No coverage reduction was requested.

## Generation — core variation sets

**Q1 contract (frame):** G1 generic authenticated HTTP request service; F1 focused
versioned JSON-line stream with explicit account and bounded increasing request
IDs within one process; C1 contrarian durable acceptance/receipt queue inside the
worker. Inversion: the worker could own zero durable job state rather than a new
queue; then missing replies stay the caller's uncertainty and retransmission is
explicit new intent. This reaches system responsibility, not only a JSON field.

**Q2 ownership (criterion):** G2 generic wrapper around ordinary TgData reads and
public group methods; F2 focused verified temporary operation for every job, with
BatchEngine composed inside the existing account/health context for raw reads,
and explicit feedback when cleanup fails; C2 contrarian one OS child process per
job, making process exit the client-lifetime boundary. Inversion: remove client
reuse entirely, then invert again—remove the whole persistent execution process,
leaving a parent only for protocol coordination. Existence/identity axes tested.

**Q3 process (frame):** G3 generic async loop with executor stdin, a queue and
concurrent account tasks; F3 focused serial main-thread binary input/output around
one owned asynchronous job at a time, signals cancelling active work and a stopping
state preventing further admission; C3 contrarian no long-lived loop, one command
invocation per job. Inversion challenges both “async source requires async stdin”
and “worker must keep every Telegram socket open while idle.”

**Q4 results (criterion):** G4 generic exception strings plus callback writes to
stdout; F4 focused unchanged portable results/partial batches, type/code-only errors
and a fixed bounded job-local event collector, with one protocol writer after
source cleanup; C4 contrarian store every result durably and send only a receipt.
Inversion: no worker-owned message archive at all; keep the existing caller receipt
boundary instead of creating another place where messages must be acknowledged.

## Seven mechanisms — additional variations

1. **Lens shifting (L1):** evaluate the worker as a trusted child of the orchestration
   app, not a public network service. Process startup and pipe ownership replace
   network authentication duties; this does not remove validation or secret-safe
   failures. L2 shifts the success criterion from throughput to bounded completion
   meaning; then serial execution is useful rather than an accidental bottleneck.
2. **Combination (M1):** combine merged verified group operations, the real raw-batch
   engine and a transport-neutral outcome projection. The source-composition probe
   already demonstrates the crucial account/budget join; no #17 runtime is needed.
3. **Inversion (I1):** keep no live account clients between jobs, and consider no
   persistent worker (C3) or per-job process (C2). These alternatives challenge the
   inventory-as-live-socket assumption instead of patching its cleanup machinery.
4. **Constraint manipulation:** ADD A1: one admitted source job globally and no
   next job while writing its outcome; this bounds concurrency and backpressure.
   REMOVE R1: remove the assumption that every failure needs transparent recovery;
   a cleanup failure can stop the worker after preserving the known source result.
   REMOVE R2: remove exclusive account ownership; this would require distributed
   coordination and credential lifetime rules, so it tests and loses that boundary.
5. **Absence recognition:** patch-level N1: cleanup failure is logged but not
   available as an explicit admission fact; add a private outcome path without
   changing existing caller results. Redesign-level N2: distinguish outcome known
   from worker safe-to-continue and from caller receipt in the protocol. Reverse
   absence check N3: batch IDs, partial results, read/join claims and group outcomes
   already exist—do not reinvent them as worker features.
6. **Domain transfer:** native computing D1: request correlation is not transaction
   idempotency; use bounded process-local sequencing without claiming replay after
   restart. Different domain D2: custody handoff requires the receiver's own receipt;
   a sender's completed dispatch is not proof of acceptance. Transfer only the
   distinction, not warehouse/broker machinery.
7. **Extrapolation (E1):** at 20 accounts/daily scraping, abandoned SDK work and an
   ever-growing “seen job ID” set accumulate. Bound process state using monotonic
   IDs and deliberate worker lifetimes; scale by caller-managed workers with
   exclusive inventories later. Do not prebuild a distributed scheduler today.

## Inherited frame audit

Central assumptions challenged: persistent worker (C3/I1); caller-selected account
(C1 tests adding selection/acceptance state); preserving existing source routines
(C2); simple stdin default (G1); cleanup must be observed in-process (C2); no worker
archive (C4); exclusive sessions (R2); throughput priority (L2). No assumption lacks
an explicit alternative; no audit override. Q1–Q4 each include inversion. No piece
commits a cognitive-spec intervention shape, so property-(v) shape-axis inversion
is inapplicable; these are software boundary candidates, not spec repair proposals.

## Five-test results

N = novelty in this worker's current design space; S = strongest-objection survival;
F = fertility; A = actionability; I = independent mechanism/evidence. A passing
design test is not a claim that an unbuilt implementation already passed runtime tests.

| Candidate | N | S | F | A | I | Disposition |
|---|---|---|---|---|---|---|
| G1 HTTP | New consumer shape | Viable only with network/auth contract | Supports remote clients | Larger unsupplied surface | Lens/service context | DEFERRED: user selects HTTP and its consumer/security boundary |
| F1 JSON stream | New bounded protocol | Fits trusted child, makes loss explicit | Reusable transport adapter | Standard library only | L1 + real pipes | ACTIONABLE with strict framing/receipt limits |
| C1 durable queue | Adds new owner | Duplicates caller orchestration and cannot transact joins with receipts | Useful for a broker product | Requires independent durable job design | D1 rejects false atomicity | RESEARCH FRONTIER, not first delivery |
| G2 ordinary wrappers | Little new mechanism | Fails explicit-account read and cleanup-knowledge tests | Weak ownership foundation | Superficially small | Actual source probe disproves | KILLED |
| F2 verified operations | New worker consumer of existing primitive | Needs cleanup fact even on cancellation/setup failure | Preserves source APIs | Small private integration seam | M1 + N1 + source probe | ACTIONABLE subject to candidate experiment |
| C2 per-job OS child | Strong lifetime alternative | Requires extra IPC/result drain/spawn supervision | Useful for hostile/uncooperative plugins | Material extra process machinery | Inversion + OS resource ownership | DEFERRED if the small cleanup seam cannot preserve required outcomes |
| G3 executor/queue | Familiar transport approach | Cancelled reader thread outlives await in real probe; queue adds admission complexity | Concurrency possible | More shutdown machinery | Real stdin probe rejects naive form | KILLED for first delivery |
| F3 serial driver | Distinguishes source from idle I/O | Must handle signals in idle, active and output phases | Small caller-managed service | No idle executor; file/pipe friendly | A1 + actual pipe evidence | ACTIONABLE with process tests |
| C3 per-command worker | Removes entire lifecycle | Contradicts start-once inventory/idle behavior | Useful standalone command | Simple but different requested product | Existence-axis inversion | KILLED for this issue |
| G4 string/callback output | Little new structure | Leaks diagnostics and mixes source/observer/output lifetimes | Poor extension boundary | Easy but unsafe | Prior evidence + owned callback API | KILLED |
| F4 portable outcome | Reuses rather than redefines data | Needs bounded collection before next job | Stable consumer contract | Existing to_dict/batch format | M1 + D2 + notification probe | ACTIONABLE |
| C4 durable output archive | New receipt owner | Takes processing/storage duties from caller | Useful optional receiver | New retention/ack lifecycle | D2 distinguishes needed caller duty | DEFERRED to an explicitly requested receiver adapter |

Additional mechanism outputs all entered the same tests: L1/L2 survive as deployment
and evaluation frames; M1 survives with unchanged engine contracts; I1 refines F2,
while its C2/C3 variants receive the dispositions above. A1/R1 survive; R2 is killed
by the absent shared-ownership authority. N1/N2 survive pending the cleanup candidate
probe; N3 rejects redundant engines. D1/D2 survive as explicit receipt limits;
E1 survives as bounded state/explicit future scaling, not a performance claim.
Each is new in the assembled worker frame, survives its named scope objection,
has a concrete next design use and is checked against code or a different mechanism.

## Assembly and axis checks

Survivor assembly S1 = F1 + F2 + F3 + F4 + A1/R1 + N1/N2/N3 + D1/D2. Trusted startup
inventory and existing ledgers; explicit-account serial jobs; verified owned source
work; a private cleanup failure fact that preserves existing operation outcomes;
bounded job-local health collection; one JSON writer; stop rather than reuse after
uncertain cleanup; no retry/receipt illusion. The worker stays resident but does not
keep a live account client between jobs. This is a concrete shape for Q1–Q4.

Mechanism to qualify next: expose cleanup failure before any caller cancellation
escapes and keep it visible to worker admission, including failure before an operation
yields. Existing non-worker callers retain their current success/error precedence.
Do not infer this from a disconnect log or a transport snapshot. A candidate probe
must establish it before the final plan relies on it.

Axes varied: transport (HTTP/stdio); durability (caller/worker); source lifetime
(temporary/persistent/process-per-job); concurrency (serial/queued); observer/output
coupling (collector/direct); cleanup response (stop/recover); state growth (counter/
receipt archive); ownership (exclusive/shared). No one-axis candidate set.
Every committed Q row has mechanism/test trace. Convergence is not solely the
inherited “small worker” premise: actual source ownership, actual pipe lifetime
and independent receipt/irreversibility constraints provide separate grounds.

## Telemetry

4/4 generators and3/3 framers; four meta-decision pieces, each generic/focused/
contrarian and inversion-tested. Per-piece logs: Q1 L/combination/inversion/D/E; Q2 combination/
inversion/absence; Q3 inversion/constraint/lens; Q4 absence/domain/inversion. Both
constraint directions and both absence levels exercised; native and different-domain
transfer recorded. All survivors passed five design tests, with empirical limits
explicit. Artifact grounding names existing batch/health/ledger facilities and the
observed cleanup gap; no nonexistent API is treated as ready.

No premature evaluation, single-mechanism trap, early frame lock, ungrounded novelty,
exhaustion or hidden contrarian kill. Assembly S1 is the selected candidate for
Critique; HTTP, per-job process and archive alternatives retain revival conditions.
**Overall: PROCEED to Critique; candidate cleanup composition must still be probed.**
