# Routelister — terminal login
## User Input
Territory: this inquiry's _branch.md and six discipline outputs. Goal: deliver deliberate terminal onboarding/re-login with compatible persisted sessions, tests and guidance while preserving existing auth/session ownership and old usable state.

## Map Header
Root/project-space breadth; fresh index.10 identities,5 HIGH-priority,7 core (one activates at live qualification). Attribution only; no selection or execution. A second sweep found no new identities. Native representations and publication effects remain separate identities because one can be correct while the other fails.

## 1. Terminal login conversation
Identity: terminal-conversation
Type: project-space × teleological × DEVELOP
Goal: the received terminal onboarding/re-login outcome.
Move: Drive eligible LoginFlow steps with one retained event loop and terminal input between settled calls.
Lands: A deliberate login or clear stop, with completed credentials available for local save retry.
WHY: The onboarding goal gains predictable control without changing the existing authentication API.
Priority:HIGH; Confidence:MED; Essentiality:core.
Guidance Mode:compact. Test first and repeated Ctrl-C on a real PTY (bc a stubbed input cannot establish interrupt behavior).
Meaning-gaps: SIGINT/action draining composition — high — wrong ownership can leave source work running.
Pointers: innovation.md Q2-F; critique.md Q2-F (bc these manifestations carry this identity's constraints/evidence).
Depth-link:none; depth-signal:targeted composition proof remains.

## 2. Native SQLite credential compatibility
Identity: native-credential
Type: project-space × teleological × DEVELOP
Goal: the received terminal onboarding/re-login outcome.
Move: Construct and reopen a private native candidate from a completed flow.
Lands: The ordinary configured reader restores the observed account.
WHY: The saved-session goal only lands when the existing reader consumes the output unchanged.
Priority:HIGH; Confidence:HIGH; Essentiality:core.
Guidance Mode:compact. Use the existing codec and SDK session APIs (bc opaque text and SQLite are distinct representations).
Meaning-gaps: Exact transfer/read-back assertions — mid — native compatibility was probed but needs permanent coverage.
Pointers: sensemaking.md compatibility probe; critique.md Q3-F (bc these manifestations carry this identity's constraints/evidence).
Depth-link:none; depth-signal:targeted composition proof remains.

## 3. Local session publication outcomes
Identity: publication
Type: project-space × teleological × DEVELOP
Goal: the received terminal onboarding/re-login outcome.
Move: Implement a publication lifetime that retains old state and distinguishes known from uncertain effects.
Lands: A saved session or an honest, actionable publication outcome.
WHY: The user can recover a local failure without losing a working credential or causing another code request.
Priority:HIGH; Confidence:MED; Essentiality:core.
Guidance Mode:compact. Exercise failures before and after namespace mutation (bc the same exception can occur on different effect sides).
Meaning-gaps: Post-publication interruption/durability classification — high — incorrect assumptions can misreport changed credentials.
Pointers: decomposition.md Q1; critique.md Q1-F/AR-R/DT-R (bc these manifestations carry this identity's constraints/evidence).
Depth-link:none; depth-signal:targeted composition proof remains.

## 4. Reader quiescence and destination preconditions
Identity: reader-quiescence
Type: project-space × epistemic × REFINE
Goal: the received terminal onboarding/re-login outcome.
Move: Make the operator-owned inactivity condition and observable conflict checks precise.
Lands: A bounded replacement promise with no implied global lock.
WHY: Safe re-login depends on acknowledging existing readers rather than pretending their cached state disappears.
Priority:HIGH; Confidence:HIGH; Essentiality:core.
Guidance Mode:compact. Compare current reader/session behavior with the stated precondition (bc a CLI-only marker cannot coordinate unaware clients).
Pointers: sensemaking.md A3; critique.md CM-R (bc these manifestations carry this identity's constraints/evidence).
Depth-link:none; depth-signal:bounded concept grounded in current artifacts.

## 5. Credential-safe operator outcomes
Identity: safe-observation
Type: project-space × teleological × DEVELOP
Goal: the received terminal onboarding/re-login outcome.
Move: Expose account/destination and safe failure kinds without input or credential disclosure.
Lands: Useful messages and exit outcomes that preserve secret boundaries.
WHY: The terminal becomes usable without turning its diagnostics into credential exports.
Priority:HIGH; Confidence:HIGH; Essentiality:core.
Guidance Mode:compact. Promote getpass echo warnings to refusal (bc non-echo input otherwise has a documented fallback).
Meaning-gaps: Exact exit/status wording — low — semantics are known and wording can be refined locally.
Pointers: sensemaking.md A2/A5; innovation.md AR-R (bc these manifestations carry this identity's constraints/evidence).
Depth-link:none; depth-signal:targeted composition proof remains.

## 6. Installed terminal command delivery
Identity: command-delivery
Type: project-space × teleological × DEVELOP
Goal: the received terminal onboarding/re-login outcome.
Move: Provide a shared installed and module command path with reader-compatible configuration rules.
Lands: Operators can invoke the documented behavior from the installed package.
WHY: The feature reaches the user's terminal rather than remaining an internal helper.
Priority:MED; Confidence:HIGH; Essentiality:core.
Guidance Mode:compact. Probe installation/help and pre-I/O refusal (bc direct Python calls do not prove the entry point).
Meaning-gaps: Concrete spelling and parser flags — low — a routine bounded interface choice.
Pointers: decomposition.md Q4; critique.md Q4-F (bc these manifestations carry this identity's constraints/evidence).
Depth-link:none; depth-signal:targeted composition proof remains.

## 7. Concrete application-store publication
Identity: store-adapter
Type: project-space × teleological × PURSUE-SEED
Goal: the received terminal onboarding/re-login outcome.
Move: Explore a named store adapter when a consumer supplies its publication semantics.
Lands: A justified terminal destination beyond native files.
WHY: Indirect: future users could reuse the command where a file destination is unsuitable.
Priority:LOW; Confidence:MED; Essentiality:peripheral.
Guidance Mode:compact. Require a concrete backend receipt/conflict contract (bc arbitrary save callables do not define publication evidence).
Pointers: innovation.md Q1-G; critique.md Q1-G (bc these manifestations carry this identity's constraints/evidence).
Depth-link:none; depth-signal:bounded concept grounded in current artifacts.

## 8. Persistent terminal login recovery
Identity: durable-recovery
Type: project-space × teleological × INVESTIGATE-FRONTIER
Goal: the received terminal onboarding/re-login outcome.
Move: Explore settled checkpoint ownership and retention for cross-process CLI resume.
Lands: An explicit recovery contract for interrupted command lifetimes.
WHY: The goal can gain convenience for long interruptions without conflating resumed auth with a local save retry.
Priority:LOW; Confidence:MED; Essentiality:supporting.
Guidance Mode:compact. Study stale-copy and uncertain-request outcomes (bc export_state does not guarantee exactly-once source recovery).
Pointers: innovation.md Q2-G/EX-R; critique.md Q2-G (bc these manifestations carry this identity's constraints/evidence).
Depth-link:none; depth-signal:bounded concept grounded in current artifacts.

## 9. Immutable session destinations
Identity: immutable-generation
Type: project-space × teleological × PURSUE-SEED
Goal: the received terminal onboarding/re-login outcome.
Move: Develop a new-destination-only workflow with explicit reader configuration selection.
Lands: Re-login without overwriting an existing session path.
WHY: The goal gains an alternative where replacement preconditions cannot be met, at the cost of a config handoff.
Priority:MED; Confidence:HIGH; Essentiality:supporting.
Guidance Mode:compact. Keep no-clobber publication and explicit reader switch (bc immutable files alone do not select the new credential).
Pointers: innovation.md Q1-C; critique.md Q1-C (bc these manifestations carry this identity's constraints/evidence).
Depth-link:none; depth-signal:bounded concept grounded in current artifacts.

## 10. Real Telegram login qualification
Identity: live-qualification
Type: project-space × epistemic × TEST
Goal: the received terminal onboarding/re-login outcome.
Move: Observe the finished command with an authorized isolated real account and allowance/setup.
Lands: Evidence of actual code delivery and optional 2FA acceptance.
WHY: Production use gains source-level confidence beyond controlled local component behavior.
Priority:MED; Confidence:MED; Essentiality:core · @live.
Guidance Mode:compact. Establish exclusive session/operator ownership first (bc local fixtures do not authorize or prove live login).
Pointers: sensemaking.md evidence limits; critique.md Q4-F (bc these manifestations carry this identity's constraints/evidence).
Depth-link:none; depth-signal:bounded concept grounded in current artifacts.

## Excluded
Auth-engine rewrite, background automatic login, signup/QR/web flows, exit-IP measurement and ScrapeOps deployment: excluded by the received task boundary, not unexplored hidden routes. Merge/release/process-gate moves are control flow, not concept directions. No candidate was omitted merely because it is deferred in the critique.

## Telemetry
10 identities;8 teleological/2 epistemic;5 HIGH priority;7 core/2 supporting/1 peripheral. All10 fresh,0 stale,0 uncertain merges; two sweeps, fixpoint reached. All6 operational and4 identity modes checked; no route ranking, dependency edges or process state in the index. Manual5/5: header, records/typing/guidance, exclusions, telemetry, paired index. **PROCEED**.
