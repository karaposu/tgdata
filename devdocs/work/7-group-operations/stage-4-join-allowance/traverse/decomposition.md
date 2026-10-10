---
model: gpt-6-astra
effort: max
---
# Decomposition — Stage4 allowance contract

## User Input / understood whole

_branch.md I1, all6 articulations, committed sensemaking.md SV6 and its real component
probes. Stage4 is a local durable admission ledger with explicit policy/custody; Stage5
will later prove identity and consume one admission immediately before a join attempt.
The partition below describes reasoning boundaries, not a demand for separate modules.

## 1 — Coupling map

| Elements | Coupling | Why changes propagate |
|---|---|---|
| Policy, unexpired claims, effective time, admission decision | Strong | One changed limit/time/count changes whether the same transaction may admit |
| Commit result, returned permission, rollback/close handling | Strong | A failure cannot be allowed to produce permission or lose the primary error |
| Schema marker, required tables, provisioning/open mode | Strong | Treating missing pieces as fresh state resets usage |
| Account key, status fields, domain errors | Moderate | Shared value contract; no shared client or mutable health identity |
| Public configuration/status and transactional core | Moderate | Values/errors cross a fixed boundary; no separate cached counter |
| Ledger and future source sender | Moderate timing, narrow data | Verified numeric ID and successful one-unit claim; no source result flows back |
| Join ledger and ReadBudget | Weak | May share a file, but units, tables and refund policy stay independent |
| Ledger and legacy/owned health | Weak | Local errors must remain local; no events, registry or recovery ownership inside ledger |
| Product behavior and fault evidence/docs | Moderate | Tests/docs must describe the same claims, error/custody and timing contract |

The stateful cluster cannot be split into a policy service, count cache and decision
service without rebuilding atomic coordination. A separate source sender is a real
boundary: it needs only admission's outcome and is excluded by the user's staging.

## 2 — Top-down boundaries

B1: value/policy/error meaning ↔ transactional state implementation.
B2: initialization/schema custody ↔ ordinary existing-state transactions.
B3: transaction body ↔ commit/cleanup result boundary (an internal sequencing boundary,
not a separate asynchronous component).
B4: local ledger ↔ future verified source-send integration.
B5: implementation ↔ independent behavior evidence and consumer documentation.
Read-budget/health implementations are references and compatibility checks, not pieces
to rewrite. No SQL connection or stored “remaining” field crosses B1/B4.

## 3 — Bottom-up validation

Atoms: numeric account ID, configured nonnegative cap, one attempt timestamp, versioned
schema identity, clock observation, SQLite commit, one return/exception, portable status.
Policy/time/claims form the decision atom; splitting read-count from insert is invalid.
A commit and the permission return cannot be reordered. File existence alone cannot be
split from schema validation when determining known state. Raw credentials, target group
and Telegram replies are absent atoms here; they do not justify fields or new tables.

Top-down and bottom-up agree on all5 boundaries: HIGH confidence. B3 stays inside the
transaction helper; it does not become a component abstraction or an acknowledgment API.

## 4 — Question tree and verification criteria

**Root:** What bounded allowance can Stage4 provide for later per-account join attempts?

### Q1 — What do callers configure and observe?

- [ ] Numeric account key and limit validation are explicit, with zero/absent policy distinct.
- [ ] Status is an immutable local observation with unexpired used/remaining and honest retry hints.
- [ ] Errors distinguish configuration, storage and exhaustion without Telegram-health meaning.
- [ ] A successful claim, not status, conveys one consumed admission; no refund/replay token.

Independent through the public value/error contract; needs no live account or source result.

### Q2 — How is legitimate persistent state distinguished from missing/damaged state?

- [ ] Provisioning intent and reopening known state are distinguishable in the API.
- [ ] Ordinary opens cannot create missing files; partial/unsupported schema is refused.
- [ ] Expected policy/claim values are validated before mutation/pruning can conceal invalid state.
- [ ] Namespaced tables can coexist with ReadBudget without altering its schema or records.
- [ ] Storage assumptions bound what can be detected: arbitrary valid-looking external edits/
  backup replacement are a custody violation, not magically detectable by a local counter.

This is the determination-mechanism piece: it supplies HOW “known valid ledger” is decided,
not an assumption that another layer already made the determination.

### Q3 — How does one transaction decide, charge and finish?

- [ ] Policy, effective clock, expiry and usage are observed under a writer transaction.
- [ ] At most one claim is inserted for one successful call; concurrency cannot oversubscribe.
- [ ] Configure preserves usage; lower caps compute the expiry that actually restores a slot.
- [ ] Clock rollback cannot move observed time backwards; zero cap has no timed availability.
- [ ] Refused admission can persist clock/pruning without creating a claim.
- [ ] Permission returns only after persistence succeeds; unknown commit/close outcome grants none.
- [ ] Work's original failure/cancellation survives cleanup failure, and no cleanup masks quota facts.

The tightly coupled math/write/commit sequence stays one tractable transaction contract.
It consumes Q1 and Q2; it does not need a Telegram client or settlement state machine.

### Q4 — What may Stage5 assume, and what must it still supply?

- [ ] Stage4 receives an ID; Stage5 must obtain it from the freshly verified operation.
- [ ] Every attempted source send/retry needs its own successful claim, with no intervening await.
- [ ] A failed claim or status read is never permission; lost return may still mean usage consumed.
- [ ] Source success/failure/cancellation does not call a refund path.
- [ ] Stage4 exports only its usable standalone allowance API; no constructor option suggests
  existing clients are already guarded and no joining API is added in this run.

This piece is a documented consumption contract, not Stage5 implementation. Its existence
keeps the excluded integration responsibility visible without expanding scope.

### Q5 — What evidence demonstrates the whole instead of supplying desired outcomes?

- [ ] Public ledger methods exercise real temporary SQLite data and schema faults.
- [ ] Process barriers force competition; owned-process exits bracket actual commits.
- [ ] Reopen, policy reductions, exact expiry, rollback, corruption and coexistence use real state.
- [ ] Faulted commits/cleanup preserve outcome and local health neutrality with original errors.
- [ ] Existing suites and demos remain unchanged and pass; no live join/login is exercised.
- [ ] Docs distinguish claims, actual joins, observable refusals, custody and advisory retry times.

Q5 consumes contracts Q1–4; it does not mock successful claim decisions or infer live safety.

## 5 — Interface map, including assumptions

| Source → consumer | What crosses | Assumption made explicit |
|---|---|---|
| Q1 → Q2/Q3 | Validated numeric key, cap, typed errors/status | No username/session filename is identity; no implicit default cap |
| Q2 → Q3 | Existing validated schema and a transactional connection | Connection stays local; no silent creation/repair during use |
| Q3 → Q1 | Completed status or successful claim return / local exception | No returned grant before commit; unknown outcomes may retain usage |
| Q3 → future Q4 consumer | One successful admission for its supplied account | Single-use before one source attempt; all callers coordinate on same local file |
| Current verified operation → future Q4 consumer | Actual expected account identity | Ledger alone does not authenticate or recover health |
| Q1–4 → Q5 | Invariants, boundaries and error/return semantics | Observe actual implementations and persistence; don't supply their conclusions |
| Q5 → docs/reviewer | Measured outcomes and coverage limits | Process-crash evidence is not a disk power-loss or live Telegram guarantee |

Configuration cannot revoke an admission already returned. Status cannot reserve capacity.
A changed file path or another independent ledger creates a separate accounting domain.
The injected clock is trusted UTC; forward clock correctness is not supplied by SQLite.
These assumptions cross B4 even though no extra data field carries them.

## 6 — Dependency order

Q1 contract and Q2 custody interface first; their implementations may be considered
independently once names are agreed. Q3 follows those interfaces. Q4's documented future
obligations follow the claim meaning; actual Stage5 waits for Stage4 review/merge per user.
Q5 probes begin with Q1–3 invariants and complete against the assembled implementation.
No dependency cycle requires a new service or a source callback. Actual cognition remains
sequential as required by traverse; this is a dependency map, not agent delegation.

## 7 — Self-evaluation / stopping

| Dimension | Verdict | Evidence |
|---|---|---|
| Independence | PASS | Each question has explicit inputs/outputs; source implementation deferred |
| Completeness | PASS | Policy, custody, clock/claim, failure, consumer and evidence all covered |
| Reassembly | PASS | Q1+Q2+Q3 deliver admission; Q4 bounds its use; Q5 tests the composed promise |
| Tractability | PASS | Five focused questions; internal sequencing stays together |
| Interface clarity | PASS | Data and timing/custody assumptions separately named |
| Balance | PASS | Q2 and Q3 carry most risk; neither is hidden behind trivial wrappers |
| Confidence | PASS | Five top-down boundaries agree with the indivisible bottom-up atoms |

Determination mechanism present in Q2/Q3 for schema validity, current policy/usage and
available capacity. No extra decomposition needed: further splitting would break the
transaction atom or produce one-line pieces. All7 failure modes checked; no DV2 trigger.
Coverage: all9 sensemaking resolutions and all6 articulation readings are mapped, with
rejected/limited readings still recorded rather than silently omitted.
