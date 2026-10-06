---
model: gpt-6-astra
effort: max
---

# Innovation — group-operation implementation candidates

## User Input and seed

Produce viable candidates for Q1–Q7 in the committed decomposition, preserving
the G1/A1–A4 framing and SV6. The gap is three useful ephemeral operations with
truthful outcomes and enforceable join admission, not a new worker or transport.
Context is the existing client/health/read-budget structure; value is reduced
caller glue and accountable membership changes; motivation is the user's #7 task.

Inherited methodology: **Standard default**, applied in Production-task mode
to Q1–Q7. Alternative: **Contrarian-rethink**, which would primarily challenge
whether joins/limits belong inside tgdata and whether the existing SDK should
be bypassed. Decision: keep the inherited mode, but explicitly generate those
alternatives. All seven mechanisms fire; every meta-decision piece gets generic,
focused and contrarian variants before testing. No reduced-coverage mode is used.

## Phase 2 — Candidate generation (before testing)

### Q1 — Reference/result contract (meta-decision: frame/criteria)

- **Q1-G, generic — Combination:** one extensible universal operation-result
  envelope for group, account and future worker actions, with plugin-specific
  detail dictionaries and a generic reference abstraction.
- **Q1-F, focused — Absence Recognition + Combination:** a small immutable group
  metadata value and explicit lookup/access/join result values with to_dict.
  IDs remain nullable when unavailable; proof/outcome fields are separate from
  descriptive metadata. One strict parser supplies the SDK operand and a safe
  diagnostic label; legacy GroupInfo keeps its existing shape.
- **Q1-C, contrarian — Inversion:** invert “the library owns a result contract”:
  return SDK entities/replies unchanged and let callers decide truth/serialization.
  At system level this makes the SDK protocol, rather than tgdata, the public
  interface; at the existence axis the number of new value types becomes zero.

### Q2 — Durable allowance (meta-decision: unit/evaluation criteria)

- **Q2-G, generic — Domain Transfer (native resource accounting):** generalize
  ReadBudget into one multi-resource policy engine with join/read units,
  configurable windows, storage adapters and shared schema migration.
- **Q2-F, focused — Domain Transfer + Constraint Manipulation ADD:** a distinct
  JoinBudget with explicit per-account configuration and a rolling 24-hour
  SQLite ledger, matching the existing operational pattern without sharing its
  message units/tables. Each admitted join attempt costs one and is never
  refunded merely because the reply failed. No unconfigured default quota.
- **Q2-C, contrarian — Inversion:** invert “the library must hold durable attempt
  state”: count confirmed successes in a caller/process-local counter. The
  system-level alternative delegates restart/concurrency correctness to the caller.
  Identity-axis inversion asks whether “join budget” is actually a convenience
  statistic rather than admission authority.

### Q3 — Admission point (meta-decision: timing/authority criteria)

- **Q3-G, generic — Extrapolation:** a universal request-policy interceptor
  mediating every Telegram mutation family and allocating all account resources.
- **Q3-F, focused — Combination + Domain Transfer:** a small JoinClientMixin
  around the actual SDK sender seam, alongside the existing read guard. For
  supported join requests, fresh self identity precedes an atomic claim, then
  enqueue follows without another await. Each SDK retry is separately admitted;
  metadata/read requests keep their own behavior. Public joining requires a
  configured join budget before mutation; legacy non-join paths remain intact.
- **Q3-C, contrarian — Inversion + Constraint Manipulation ADD:** invert “retries
  need a send guard”: disable SDK retries for the join and make a single claim
  at the helper boundary. The system becomes a caller-retry protocol, with one
  underlying attempt per admitted call, rather than transparent retry admission.

### Q4 — Read observation (meta-decision: proof criterion)

- **Q4-G, generic — Lens Shifting:** treat access as a comprehensive capability
  report: query participants, rights, full chat info and message history to
  characterize all possible operations for the account.
- **Q4-F, focused — Constraint Manipulation ADD + Combination:** lookup resolves
  known metadata or an invite preview/peek; access adds one bounded history
  request when a peer is available. It returns readable/denied/unprobed evidence,
  never a membership-derived Boolean. The history request obeys ReadBudget.
- **Q4-C, contrarian — Inversion:** invert “access needs a read”: use membership
  flags alone. At system level this redefines readiness as subscription state;
  the existence-axis variant removes all message reads from checking access.

### Q5 — Join outcome (meta-decision: completion criterion)

- **Q5-G, generic — Extrapolation + Absence Recognition redesign:** create a
  durable workflow that follows approval, web-view and payment steps to eventual
  membership, resuming across process restarts and coordinating callers.
- **Q5-F, focused — Absence Recognition + Combination:** preflight on the same
  client; skip an observed already-member mutation; send the appropriate join
  request through admission; map Ok, already-member, request-sent and WebView
  outcomes explicitly. Project available nested-update metadata/cache locally;
  no mandatory network enrichment after an acknowledgment. Paid/interactive
  completion is surfaced as unsupported/required interaction, never automated.
- **Q5-C, contrarian — Inversion:** invert “unfinished outcomes are values”:
  return a value only for acknowledged/already membership and use dedicated
  pending/interaction exceptions carrying typed detail for every incomplete case.
  At system level the caller's exception protocol becomes the workflow protocol.

### Q6 — Public lifecycle and health (meta-decision: observation criteria)

- **Q6-G, generic — Absence Recognition redesign:** replace health recovery
  with a general proof/evidence taxonomy for all old/new public methods and
  merge entity/account/request recovery into one extensible evidence engine.
- **Q6-F, focused — Lens Shifting + Combination:** keep one ephemeral client
  per public operation and a safe target label. Add a narrow default-preserving
  control over group recovery to the existing health call, so metadata/join
  outcomes can still recover account/wait evidence without declaring history
  access. An actual successful access probe can recover the group. Keep local
  validation/admission errors and genuine Telegram errors distinct.
- **Q6-C, contrarian — Inversion:** invert “new calls participate in health”:
  return/raise directly and leave all observation to callers. The system-level
  alternative makes these operations a second, unobserved client interface.

### Q7 — Evidence (meta-decision: evaluation criteria)

- **Q7-G, generic — Extrapolation:** provision live multi-account group fixtures,
  cross-host workers and exhaustive state-model testing as prerequisites to ship.
- **Q7-F, focused — Domain Transfer (native protocol contract tests) + Combination:**
  observe real SDK dispatch/serialization/retries with supplied transport,
  real local database concurrency and complete public operation paths. Add
  targeted fault/cancellation/health checks and run the supported offline suites;
  state the live-server and multi-host limits without claiming they were tested.
- **Q7-C, contrarian — Inversion:** invert “offline fixtures can be useful”:
  ship only a live happy-path smoke check. At system level vendor acceptance
  becomes the sole evidence, with no deterministic failure-path regression.

### Required mechanism extensions

- **M8 — Constraint Manipulation REMOVE / caller backend:** remove the built-in
  storage constraint: accept only a caller-supplied atomic admission provider,
  shipping no default backend. This expands multi-host integration but moves
  enforcement implementation outside the library's delivered feature.
- **M9 — Absence Recognition patch level:** a typed incomplete-result field is
  missing between Telegram's reply and a caller's “ready” state (Q1-F/Q5-F).
- **M10 — Absence Recognition redesign, already-present direction:** admission
  at the retry seam and durable accounting already exist in another form in
  BudgetClientMixin/ReadBudget. Preserve the proven placement, not its message
  unit or schema; do not claim this capability is absent everywhere.
- **M11 — Domain Transfer, deliberately different field:** an inventory gate
  allocates scarce entry capacity before handing out permission, not only after
  receiving a receipt. Unknown receipt delivery cannot safely restore capacity.
  Adapt to join attempts; do not import payment/refund machinery.

## Inherited-frame audit (before testing)

Central assumptions challenged: library-owned truth contract (Q1-C), durable
attempt accounting (Q2-C/M8), actual-send integration (Q3-C), read evidence
(Q4-C), explicit incomplete outcomes (Q5-C), health participation (Q6-C), and
offline evidence (Q7-C). Each Q1–Q7 is meta-decision by frame/criteria property;
each has a full generic/focused/contrarian set and a system-level inversion.
No piece commits a named intervention-shape-vocabulary operation, so the extra
property-(v) shape-axis requirement does not fire. No generic override was used.
The audit has a concrete challenge for every inherited load-bearing choice.

## Phase 3 — Tests and assembly

### Observed seams

Ran `../probe_group_seams.py` using .venv Telethon 1.45.0, layer 229, sockets
forbidden. Real TL serialization round-trips Ok/WebView; WebView has no URL.
MemorySession ignores the wrapper's nested entities but caches `reply.updates`.
Real UserMethods._call retries a synthetic ServerError at sender.send: two
sends and two fresh self reads return account 222 while cached self remains 111.
The retry=0 alternative really does send once and preserve the original error
with raise_last_call_error; it is technically viable, not dismissed as impossible.
The actual health context plus metadata request clears a prior group denial.
The last observation is a counterexample motivating an explicit recovery control.
The transport supplies replies; these probes prove SDK behavior, not Telegram
acceptance, a yet-unwritten ledger, or live ephemeral lifecycle correctness.

### Five-test log

N = novelty in this project, S = strongest scrutiny, F = fertility, A =
actionability, M = independent mechanism/evidence. Lack of novelty alone is
not a defect for a useful reused primitive; the new composition must add value.

| Candidate | N | S | F | A | M | Disposition |
|---|---|---|---|---|---|---|
| Q1-G | New broad schema | No second consumer defines its extension rules | Broad but speculative | Requires invented cases | Only extrapolated reuse | Failed; seed: wait for another operation family |
| Q1-F | New portable group proof contract | Nullable identity prevents invented preview IDs; separate proof avoids stale membership in metadata | Usable by #10 | Small dataclasses/parser | Invite type evidence + worker serialization need | ACTIONABLE |
| Q1-C | Existing SDK surface | Breaks stable caller distinction between preview, acknowledgment and pending | Vendor-specific callers only | Easy to return | Simplicity supports it; wire changes oppose | Failed for the requested caller boundary |
| Q2-G | New generic policy engine | Refactors working #9 with no second common unit contract | Many resources | Too much migration for #7 | Analogy only | RESEARCH FRONTIER: only after another measured shared accounting need |
| Q2-F | New resource, known durable primitive | Multiple clients/restarts handled; shared-file boundary explicit; no claim of Telegram-safe limit | Worker can query remaining allowance | SQLite/stdlib available | #9 admission evidence + concurrent-restart counterexample | ACTIONABLE |
| Q2-C | Familiar counter | Restart, retry and ambiguous delivery defeat success-only total | Useful display statistic | Very easy | Convenience, not enforcement, supports it | Failed; retain successful-count as possible analytics only |
| Q3-G | New universal authority | Cannot enumerate or test all mutations in this issue | Platform policy | Undefined scope and rules | Extrapolation only | RESEARCH FRONTIER, not a #7 prerequisite |
| Q3-F | Existing seam with new resource | Actual SDK retry observed; fresh identity avoids stale session cache | Shared across client factory | Two known request families | Real SDK probe + existing read guard | ACTIONABLE |
| Q3-C | Narrow alternative | Probe proves single send; changing shared client retry state races, and a dedicated no-retry client no longer uses the common factory behavior | Useful explicit no-retry mode | Possible with isolated client construction | Probe supports feasibility, factory constraint opposes fit | DEFERRED: revive if common sender seam stops working in a supported SDK |
| Q4-G | New capability census | More RPCs still cannot prove every future permission | Rich diagnostic tooling | Oversized/unbounded | Lens shift only | RESEARCH FRONTIER if detailed permissions requested |
| Q4-F | Bounded direct proof | A peerless invite remains unprobed; quota/network failures raise, not denied | Consumer can decide readiness | One history request, existing read budget | Public nonmember readability + history response evidence | ACTIONABLE |
| Q4-C | Existing flags | Public nonmember history and forbidden member both refute equivalence | Cheap membership display | Easy | Membership semantics conflict with read goal | Failed; seed retained as lookup evidence only |
| Q5-G | New workflow | Cannot complete approval/payment/webview within requested short-lived lookup | Worker orchestrator | Needs durable jobs, auth/payment/UI | Future #10 analogy only | RESEARCH FRONTIER outside #7 |
| Q5-F | New truthful outcome mapping | No extra network step after ack; unknown detail stays unknown; interaction never implies membership | Fits caller orchestration | 1.45 constructors observed | SDK wrapper probe + issue's readiness purpose | ACTIONABLE |
| Q5-C | New exception protocol | Technically sound, but successful request submission is an expected outcome; callers would parse exception families for normal progress | Works for exception-oriented API | Straightforward | Transport/error convention supports; operation-status convention opposes | DEFERRED: revive if consumers require exception-only completion protocol |
| Q6-G | General health redesign | Would change every existing recovery contract | Better general evidence model | Exceeds issue and tests | Conceptual purity only | RESEARCH FRONTIER if multiple new proof types recur |
| Q6-F | Narrow opt-out with old defaults | Probe reproduces false recovery; retain account/wait recovery independently | Other metadata callers could adopt later | One optional context control | Real counterexample + #4 health contract | ACTIONABLE |
| Q6-C | No integration | Loses waits/auth/access observations the rest of facade reports | Simpler separate API | Easy | Convenience supports, project observation contract refutes | Failed |
| Q7-G | Broad evidence | Live membership mutations unavailable/unauthorized; no deterministic timing | Future staging confidence | Cannot run now | Production realism supports only a later supplement | DEFERRED: explicit live test account/group approval |
| Q7-F | Focused composition evidence | Does not prove Telegram acceptance; tests real SDK/ledger behavior and states that limit | Regressions support future SDK changes | Existing harness available | Independent SDK, SQLite and public-path observations | ACTIONABLE |
| Q7-C | Existing smoke style | Cannot reproduce cancellation, identity drift, races or quota exhaustion reliably | Narrow live confidence | Needs credentials/live joins | Server acceptance alone | Failed as sole evidence; seed becomes optional later smoke |
| M8 | New adapter-only contract | Requires every consumer to implement atomic storage before feature works | Distributed backend useful | No evidenced consumer now | Multi-host model supports, installed local use doesn't | DEFERRED: actual multi-host consumer with shared atomic provider |
| M9 | Missing outcome filled | Wrapped WebView/request-sent cannot be Boolean membership | Future orchestration | Included Q1-F/Q5-F | SDK + readiness lens | ACTIONABLE, merged into those candidates |
| M10 | Reuse of existing placement | Read units/schema must not be reused blindly | Consistent guards | Included Q2-F/Q3-F | Code inspection + retry observation | ACTIONABLE, merged |
| M11 | New explanatory transfer | Admission cannot guarantee delivery or server membership | Clarifies uncertainty boundary | Implemented by Q2-F claim before send | Inventory analogy alone is weak; real retry observation independently supports timing | ACTIONABLE only as explanation of Q2-F, no extra subsystem |

### Shared-input and artifact-grounding tests

All candidates inherit the request and SV6. That common input is not independent
confirmation. Q2-C challenged its durable-attempt premise with success-only
counting: restart plus ambiguous send loses the very upper bound requested.
Q3-C challenged sender integration and passed a real feasibility probe; it loses
on shared factory/retry preservation, not on assumed impossibility. Q1-C/Q4-C
challenge library-owned/read-proof truth using observed preview shape and the
different semantics of metadata and history. Q5-C survives as a protocol option,
so value results are a documented ergonomic selection, not uniquely provable.

Grounding inventory: `read_budget.py`/`budget_client.py` already provide durable
read admission (M10 does not claim absence); `connection_engine.py` supplies
ephemeral factory/auth/finally-disconnect; `health.py` has one recovery switch,
and the probe shows its group implication; installed `tl/types/messages.py`
provides wrapped results; `session_store.py`/MemorySession require nested cache
projection; `models.py`'s GroupInfo requires an ID. These artifacts support the
selected roles. Existing auth GetState uses default flood handling; no claim of
zero-wait authorization is retained. No contradictory project-state claim remains.

### Axis coverage and assembly

Axes varied: result ownership (Q1), accounting unit/lifetime/backend (Q2/M8),
send timing/retry policy (Q3), proof depth (Q4), incomplete-operation protocol
(Q5), recovery evidence (Q6), and evidence environment (Q7). Each has generated
and tested variants. Every selected element has its own mechanism trace above;
there are no silently inherited default rows. Property-(v) shape commitment did
not fire; scope/frame alternatives are nevertheless explicit.

Assembly: Q1-F + Q2-F + Q3-F + Q4-F + Q5-F + Q6-F + Q7-F. A caller receives a
portable answer whose membership/read evidence matches the operation performed,
while the same short-lived factory enforces a durable account admission bound.
The emergent value is that “ready” and “attempt permitted” can be automated
without either being inferred from an SDK object's presence. Strict input
parsing and safe labels occur before the health context; fresh account identity
and admission occur before mutation; no follow-up request can turn an acknowledged
join into an apparent failure. Local result projection must tolerate missing
metadata. Auth/transport/storage failures remain distinguishable from denial.

Surviving alternatives do not contradict this bounded assembly: Q3-C/Q5-C/M8
are preserved with revival triggers; Q7-G is additional evidence only. No
RE-TEST TRIGGER remains open. The implementation layout/API particulars are
for the plan after critique, not implicitly finalized by this assembly.

## Mechanism coverage telemetry

Generators 4/4; framers 3/3. Convergence: YES, Combination, Absence Recognition
and Domain Transfer converge on the admission/proof composition, independently
grounded by SDK/SQLite/project-call contracts after shared-input challenge.
Survivors tested: 19/19 (7 selected, 3 merged, 4 deferred, 5 research-frontier);
6 failures also received every test. All Q1–Q7: meta-decision; piece-level
Inversion satisfied, no overrides. Per-piece mechanism log: Q1 Combination,
Absence Recognition, Inversion; Q2 Domain Transfer, Constraint Manipulation,
Inversion; Q3 Extrapolation, Combination, Domain Transfer, Inversion, Constraint
Manipulation; Q4 Lens Shifting, Constraint Manipulation, Combination, Inversion;
Q5 Extrapolation, Absence Recognition, Combination, Inversion; Q6 Absence
Recognition, Lens Shifting, Combination, Inversion; Q7 Extrapolation, Domain
Transfer, Combination, Inversion. Failure modes: none remaining; retry=0 was
tested to avoid comfort-driven rejection. Audit firings 0 after explicit
challenges; no override, no post-run user correction, cross-run calibration not
measured. **Overall: PROCEED** to critique of the assembled candidates.
