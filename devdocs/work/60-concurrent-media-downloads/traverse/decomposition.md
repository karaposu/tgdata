# Decomposition — bounded media preparation
## User Input
_branch.md and committed sensemaking.md SV6; all four extent/surface articulations.
## Coupling map
Strong: task start/stop/join with worker resource ownership and outcome selection.
Strong: record order with accepted prefix, callback boundary and durable next_after_id.
Strong: raw request admission with SDK waits/retries and budget admission ordering.
Moderate: explicit task observations with health/heartbeat scopes; source results and
local artifact errors must retain provenance. Moderate: public option forwarding with
reader runtime configuration. Weak: delivery schema/replay with the option (opaque
existing MessageBatch remains the boundary). No dependency on account-routing redesign.

Top-down boundaries: P1 activation/coordination extent, P2 bounded owned media work,
P3 source admission/observations, P4 reader-specific acceptance, P5 public propagation/
validation. Bottom-up atoms: one requestedN; one Task; one SDK borrow; one send attempt;
one completed blob; one row; one durable receipt. Task and borrow must stay together;
row/receipt stay with readers/delivery, not scheduler. P2↔P3 timing is an explicit
contract, not independent implementations. All five boundaries HIGH confidence at
contract granularity. Do not split errors from outcomes or cancellation from ownership.
## Question tree and verification criteria
Q0: How can optional media overlap preserve ordered source and delivery semantics?
P1: Who may activate it and whose work shares its bound/backoff?
- DetermineN validation/default and local extent; state independent-engine/account
  responsibility. Verify concurrent calls cannot silently multiply the promised scope.
- Determine activation from explicitN, not metadata size or guessed network latency.
P2: How does an invocation own a bounded set of media preparations until quiescence?
- Bound both active and unaccepted work; no detached tasks; repeated cancel sends one
  stop per child and joins physical settlement. Track native exports/CDN resource use.
- First gap prevents later acceptance; already-published files never imply progress.
P3: How do these owned tasks honor source policy and observation ownership?
- Gate sends before enqueue; observe real source waits including SDK-handled waits;
  do not change shared policy or create worker retries. Keep budget admission charged.
- Explicitly enroll owned tasks only; inherited SDK/background tasks cannot borrow
  attribution. Exported/CDN/source-refresh behavior must be accounted for.
P4: How does each reader consume results without changing its default contract?
- N1 same path/order/errors; opted-in errors declared. Batch complete records in
  source order and valid interrupted prefix. Legacy callbacks/batch pacing must
  finish their promised batch with no later writes before callback decisions.
- Files use existing naming/cache expectations but incomplete opted-in files cannot
  masquerade as reusable complete results. Local failure remains local.
P5: How do callers select it and know what was validated?
- Forward only nondefault option through daily/backfill/pool; do not persist it in
  receipt identity. Replay has no source work. Define scope of profile/bytes/by-ID.
- Meaningful real SDK/public-route probes, default regressions and opt-in benchmark
  path; distinguish local qualification from live gains and production deployment.
## Interface map — flows and assumptions
P1→P2/P3: validatedN, coordinator scope/lease; no accidental global account promise.
P2↔P3: active task/resource ownership and raw-send stop/wait facts; registration is
explicit and revoked only after child settlement. Background context inheritance is
not admission. File operation boundaries do not classify RPC errors as local.
P2→P4: ordered success or preserved error after settled children, bounded completed
artifacts. P4 owns cursor/callback acceptance; it must not treat speculative bytes as
records or acknowledge anything. P4→P2: batch/callback window boundary and early exit.
P3→P4: same wait/error policy and real observations; earlier source failure wins over
cleanup failure, while actual caller cancellation remains cancellation.
P4→P5: unchanged MessageBatch/DataFrame contracts plus optional control. P5→P1:
validated nondefault forwarding; default omitted for injected readers. P5→delivery:
existing batch only; receipt/store schemas and CAS semantics unchanged.
## Dependency order
P1 extent/activation contract first. P2/P3 interfaces next and tested together before
reader integration (not declared independent). P4 legacy and batch acceptance then
P5 consumers/proofs. Full combined real-component prebuild before product adoption;
small isolated helper tests alone cannot establish the interfaces. Documentation can
follow settled contract; no subagents or parallel cognitive discipline work.
## Self-evaluation
Independence PASS at contract boundaries, not permission to mock away P2/P3 coupling.
Completeness PASS across activation/tasks/source/records/public consumers and SDK
resources. Reassembly PASS with runtime determination provided byP1 and task membership
byP2/P3. Tractability PASS: five purposeful questions; no generic scheduler framework.
Interface clarity PASS incl. assumptions above. Balance PASS: P2/P3 most delicate but
separated by raw-send interface; P4 two existing consumers needs explicit tests.
Confidence PASS: top-down/bottom-up atoms agree. All seven failure modes checked;
no missing receipt authority, hidden callback boundary or unbounded task backlog.
Manual structural5/5 output sections and7/7 quality dimensions PASS; script absent.
