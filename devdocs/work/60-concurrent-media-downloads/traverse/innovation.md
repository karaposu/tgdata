# Innovation — small owned windows
## User Input / seed
_branch.md and decompositionP1–P5: optional bounded media overlap with truthful ordered
completion, existing waits and physical cleanup. Production-task seed; value is lower
daily latency without new progress/account orchestration. Inherited mode Standard
default. Alternative Contrarian-rethink would concentrate on whether any parallel
scheduler is justified before live measurement. Retain Standard with all seven
mechanisms and explicit contrarian candidates; no below-full override.
## Generation — generic / focused / contrarian per meta-decision piece
P1 (framing/evaluation meta-decision; scope axis): G global account registry keyed by
verified self ID; F per-ConnectionEngine opt-in ownership, one concurrent media read
at a time, with caller coordinating other engines/ordinary reads; C no shared scope,
N means independent per-call permission. Invert F: eliminate local coordination and
make application responsible for every overlap. This is a real scope alternative.
P2 (intervention-shape meta-decision): G ADD-CONTENT reusable rolling scheduler and
reorder buffer; F ADD-CONTENT bounded windows with retained children and explicit SDK
resource ownership; C DO-NOTHING about native borrows, trusting SDK Task completion.
Invert twice: no helper → caller composes gather → library no longer owns reader
completion, contradicting its current public scope. Existence-axis: zero child tasks
cannot overlap files; identity-axis: only media preparation, not whole message reads.
P3 (intervention-shape meta-decision): G REPAIR SDK retry policy into central scheduler;
F ADD-CONTENT task-scoped raw-send gate/observer with existing retries/thresholds;
C DO-NOTHING centrally, each download catches final FloodWait independently. Explicit
shape inversion reverses added gate into worker-only handling; no shared policy writes.
P4 (evaluation meta-decision): G new unified result/error schema for both readers;
F retain inline1 and reader-specific ordered acceptance, explicit strict errors only
when opted in; C accept out-of-order completion as cursor progress. Invert fixedprefix
criterion: use maximum completed ID and assume gaps recover later; challenge receipts.
P5 (framing meta-decision): G expose config/persisted scheduling everywhere including
worker jobs/by-ID/profile; F runtime nondefault keyword on two readers and existing
daily/backfill/pool paths, preserve replay identities; C no library feature, benchmark
or downstream semaphore only. Invert integration commitment: external app owns media.

## Seven-mechanism variations (generated before evaluation)
M1 Lens shifting: throughput target becomes bounded added work and unchanged receipts;
a small opt-in window is useful without promising a multiplier. CandidateL.
M2 Combination: bounded window + existing blob publication + existing prefix acceptance
forms owned preparation, leaving schemas untouched. CandidateW.
M3 Inversion: later success is not progress; invert worker-centric execution into
reader-authorized speculative preparation. CandidateO; opposite max-ID candidateX.
M4 Constraint manipulation ADD: no refill across a full window/callback boundary makes
finite task/result bounds and final stalled-tail silence explicit. CandidateB.
REMOVE: remove ordered-prefix constraint to deliver any completed rows. CandidateU.
M5 Absence recognition patch: explicit registered child ownership is missing from
health/heartbeat; candidateD. Redesign: a resource-complete download span would own
exported borrows/CDN helpers; candidateR. Already present differently: #17 cleanup
retains tasks and batch_files owns output; reuse principles, not a second general pool.
M6 Domain transfer: ordered retirement of speculative work (processor reorder-buffer
analogy) suggests positions, not message-ID adjacency, define a complete prefix.
CandidateQ: bounded rolling retire queue; adapt to deletions/gaps without contiguousIDs.
M7 Extrapolation: many independent engines for one account eventually need shared
account-wide admission; candidateA. Current single-operator flow does not establish
that registry now; expose scope so later work can extend deliberately.

## Inherited frame audit
Central assumptions challenged: library-owned concurrency (P5C), bounded work (P2G
versus finite windows), ordered-prefix (P4C/U), local extent (P1G/C), SDK policy remains
(P3G). Every meta-piece has generic/focused/contrarian and explicit inversion. No
unchallenged inherited success criterion; no override. Shape-axis inversion applies
toP2/P3 and is satisfied. Default1 challenged by replacing all paths with pool1 under
P4G; evaluated against user confirmation below.

## Five-test log (N novelty; S scrutiny; F fertility; A actionability; I independent support)
P1G/A: N adds global authority; S identity verification and mixedN1 policy cannot be
inferred from config/cache, needs broader contract; F yes for future fleet; A costly
now; I only scaling premise. DEFERRED: revive with explicit same-account multi-engine
requirement. P1F: N scopes optional work; S ordinaryN1/other engines explicitly outside
bound (no global safety claim); F both readers; A existing engine lifetime; I user
opt-in plus pool exclusive attempts independently support. SURVIVE. P1C: N per-call
only; S multiple opted-in calls multiply load in sameengine; F limited; A easy; I
weaker than source-policy ownership. REFINE intoF local coordination.
P2G/Q: N rolling ordered window; S can remain bounded but refill can keep unrelated
progress masking stalled first item, needs individual stall policy; F yes; A more
state; I queue analogy only. DEFERRED until measured underutilization justifies it.
P2F/W/B/R: N complete owned finite window; S borrowed-SDK and repeated-stop cleanup
need explicit receipts before return, not gather assumption; F both readers; A private
context plus real-client seams; I actual SDK cancellation observation + durable prefix
independently require ownership. SURVIVE conditional real-composition prebuild.
P2C: N none; S fails borrowed1/returned0 observed; F/A/I not pursued after failed test.
KILL. No child-resource leak can be waved away as an unchanged SDK detail.
P3G: N centralized new retry policy; S changes unrelated shared retry behavior; F wide;
A rewrite; I not required by source evidence. KILL for this task. P3F/D: N scoped
admission observes sends even through SDK-handled waits; S cover cached/exported/CDN
paths and explicit task membership; F limits ownedscope; A common clientMRO seam;
I actual _call plus task-scope tests independent. SURVIVE conditional prebuild.
P3C: N none; S SDK consumes waits internally so misses coordination; F/A/I failbound.
KILL. P4G: N unified schema; S N1 compatibility and receipt/hash changes unjustified;
F broad; A highcost; I no demand. KILL. P4F/O/L: N control without schema mutation;
S both current error policies preserved at1, opt-in strict behavior explicit; F yes;
A shared helper plus reader adapters; I raw batch validation+legacycallbacks. SURVIVE.
P4C/X/U: N max-ID shortcut; S acknowledged gaps are irrecoverably skipped; KILL.
P5G: N persisted tuneables; S replay identity shouldn't depend on scheduling; F later
worker option possible; A unnecessaryscope; I no cross-source need. DEFERRED explicit
worker/by-ID/profile feature request. P5F: N runtime propagation; S default omission
preserves injected-reader signatures; F all requestedconsumers; A existing seams;
I heartbeatprecedent plus replaycode. SURVIVE. P5C: N downstream alternative;
S cannot own batch file/preparation boundary; F no; A would duplicate reads/account
logic; I poor. KILL as fulfillment, benchmark retained as validation.

## Assembly and axis coverage
CandidateS: P1F+P2F+P3F+P4F+P5F. One opt-in read owns bounded windows; source gates
and explicitly registered observations stay within its lifetime, and reader alone
accepts ordered output. One ConnectionEngine rejects/serializes overlapping opt-in
operations (exact policy next critique); N1 and independent engines retain existing
caller coordination. No global per-account promise. N1 stays inline. Optional path
can fail strictly on media errors to preserve meaningful prefixes, while default
legacy best-effort behavior remains. Profile photos/by-ID not implicitly parallelized.

Assembly novelty is the explicit ownership join, not a generic executor. Combined
native prebuild must test SDK waits, borrowed-resource cleanup, registered observations,
ordered errors, callback boundaries and replay before adoption. No implementation
proof claimed. Axes covered: scope, scheduling/refill, retry authority, default/failure
semantics, forwarding/persistence; no emptyaxis. Shared-input detection: prefixneed
comes from batchvalidation, cleanup fromactualSDKprobe, default fromuser—independent
sources, not seven restatements of one inherited assumption. Artifact-grounding: all
claims checked against code/probe; global coordinator remains proposal, not existing.
Telemetry:4G/3F, five meta-pieces each three variants and inversion satisfied; six
failure modes checked; all survivors five-tested. Convergent finite ownership across
M2/M3/M4/M5, with M6/M7 alternatives preserved. PROCEED to adversarial critique.
