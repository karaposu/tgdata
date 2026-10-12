---
model: gpt-6-astra
effort: max
---
**Verdict: IMPLEMENT AS WRITTEN**

Falsifier: the integrated worker loses source/cleanup ownership at a stop transition,
executes a successor after unsafe shutdown, or forwards unknown diagnostic text through
an actual SDK wrapper/health path despite the declared process contract.
Affordable now: yes — executed during this review on the actual product, SDK, SQLite
and OS processes. The candidate prebuild had already passed before integration.
**Result: PASS.** The new observations below close this review's affordable falsifiers;
no unrun local experiment is being deferred past approval. Live/platform qualification
still requires its separately declared resources and authorization.

**PR gate: PASS — 0 High, 0 Medium, 0 Low.**

## High-level summary

Fresh in-session soundness review of the entire13-file product diff plus revision4
plan, landing on unchanged dev68f6bbd. Product remains **d32abcd**, with implementation
records0c0144d and renewed fidelity checkbbdc846. Promptc36c0a1 was committed before
these probes. Same warmed session, no subagent; current metadata at
2026-10-12T12:22:23.561Z verifies GPT-6 Astra/max.

The two original Medium findings are addressed at their actual boundaries. Stopping
owns both cancellation and loop progress, without a polling task or new supervisor.
Recognized authentication vocabulary is enforced at the serialized worker boundary,
while ordinary library reasons and existing error/health classification remain intact.
The design remains an explicit-account serial process; no new routing, persistence,
transport or global error framework is warranted by this review.

Fresh probes passed **13 actual subprocess histories** (10 ordered lifecycle histories
and3 pending-signal controls), **48 actual SDK/Worker error histories**, and one protocol
control group. Later proof failures keep zero unspent charge; failed reads retain real
charges and partial batches; a successful accountB job neither inherits nor clears
accountA's state. Unknown text is absent from terminal and correlated health frames.
Cleanup/output and process-state restoration hold through the tested transitions.

The committed24-suite631-pass/3-live-skip record covers this identical product and dev.
It was inspected and hash-checked, not represented as a new full-suite run. New probes
are fresh evidence beyond those tests. The earlier rejected PR review is preserved
exactly in `pr-critic_r1.md`; planning critic.md remains untouched.

## Premise Inventory

### P1 — Process stopping owns admission, progress and settlement together

**Premise:** one process owner can stop synchronous I/O, wake a quiet active task and
retain native/final cleanup without running another queued job.
**First dependent step:**2; **waste if false:** process integration, permanent tests,
docs and qualification2–5 need a different ownership design.
**Test scheduled at:** complete combined prebuild1, before integration; permanent4/5.
**Cheapest earlier test:** real process/selector with actual SDK work, seconds per
history; already executed before integration and extended in this review.
**Coverage:** frozen prebuild82/67 and permanent process25/25 already cover idle input,
quiet waits, creation/publication, held finalization, caller cancellation and broken/
undrained raw output. Fresh `pr_r4_lifetime.py` adds mixed signal types during quiet
work, a first stop during successful-source cleanup and failed cleanup, a stop at
completed-result publication, and a stop after the actual loop closes, for both
SIGINT/SIGTERM. All preserve the selected first reason, one disconnect attempt,
charges, no successor, restored handlers/logging and zero pending loop tasks.

A periodic child release watcher would be **non-covering** for quiet wake-up. None
runs. Parent-side polling and explicit Event release do not advance the child's loop
before its stop. The handler wrapper observes the real stop owner without changing
its action. Native cleanup failure is explicitly observed as disconnected=false;
process exit/task settlement is not claimed as successful transport cleanup.

### P2 — Diagnostic publication remains bounded across source phases

**Premise:** worker-local projection can omit unknown text after real SDK decoding,
wrapping and health attribution, preserving known fields and original failure types.
**First dependent step:**3; **waste if false:** diagnostics/public contract/tests3–5.
**Test scheduled at:**1, then4/5; **cheapest earlier test:** actual SDK-decoded errors
through Worker and its accepted account operation, milliseconds per history.
**Coverage:** the full prebuild and permanent tests cover unknown401/406, generic403,
known auth codes, flags, faulty metadata and terminal/delivery/fatal paths. Fresh
`pr_r4_diagnostics.py` tests GetState setup, later budget proof, group resolution,
history and a100-message prefix followed by failure. Every applicable verb is
exercised with unknown401/406/403; six later-proof controls preserve SESSION_REVOKED
and USER_DEACTIVATED_BAN.48 histories passed with actual SDK request construction,
SQLite charges and native cleanup. Raw authentication wrappers retain their original
Python reason; their portable projections omit it. Generic errors retain their
SDK type/code instead of being falsely turned into authentication wrappers.

Fake error dictionaries or pre-sanitized return values would be **non-covering**.
Probes decode TL error bytes using the SDK, bind them at actual request transport,
and execute the real Worker; no source outcome or projector is replaced.

### P3 — Fresh proof, accounting, health and source results keep one owner

**Premise:** wrapping accepted library operations in a resident process preserves
expected-account checks, later admission, partial batches and source/observer isolation.
**First dependent step:** original source integration, retained by revision4 steps2–5.
**Waste if false:** the source/process boundary must be rebuilt rather than documented.
**Test scheduled at:** original/combined prebuild and permanent tests before delivery.
**Cheapest earlier test:** actual account-operation/SDK/SQLite composition, available
and executed at those stages and again for the fresh error histories.
**Coverage:** all current source foundations remain unchanged except the original
narrow cleanup receipt and worker resolver seams. Fresh later proof failures emit no
history/join and consume no allowance. Errors after send retain1/2 or200 charges as
appropriate; the100-message partial batch keeps its actual batch ID. All48 cases
then execute a real successful accountB read: no inherited event and no change to
accountA's health state. Existing stale-cache/mismatch tests cover numeric identity.
A stand-in returning a selected account/result would not prove this premise.

### P4 — Framing and output preserve receipt uncertainty without added ownership

**Premise:** bounded JSON/request identity, one writer and raw output can carry exact
results without implying durable acceptance, storage or safe replay.
**First dependent steps:** original protocol/process integration, retained in2–5.
**Waste if false:** caller contract, process behavior and examples become misleading.
**Test scheduled at:** original/combined prebuild and permanent suites; **cheapest
earlier test:** real pipes plus decoder/encoder controls, already run.
**Coverage:** retained tests cover framing, malformed/duplicate requests, full limits,
exact Node query IDs, all four verbs, partial output and lost replies. Fresh controls
reject exponent infinity, excessive nesting and5000-digit integers without consuming
an ID. Exact encoded-frame size succeeds; one byte less refuses. Three-byte writes
reassemble exactly. Fresh completed-result stop histories leave no terminal reply,
keep the read charge and run no successor. No durable or exactly-once claim is made.
The short-writer control alone is **non-covering** for OS backpressure; the real pipe
qualification supplies that evidence separately.

### P5 — Live/platform deployment meets external preconditions

**Premise:** real accounts, proxies, readable groups, assigned sessions and provisioned
allowances exist on the chosen deployment platform.
**First dependent work:** later live deployment, outside this offline delivery.
**Waste if false:** deployment must wait; it does not change the selected local API.
**Test scheduled at:** separately authorized live/platform qualification.
**Cheapest earlier test:** requires those actual resources/permission; none in the
owned synthetic test environment can establish it.
**Coverage:** none claimed. Offline SDK data does not establish real access/proxy
behavior or safe rates. Python3.7 grammar is not native execution; Windows is not
POSIX. These declared preconditions are carried unchanged, not padded as new risks.

## Restart Check

| Observed failure | Established mechanism | Addressing design and evidence |
|---|---|---|
| Inherited #17 observer failures replace outcomes or create close cycles | Observer/source ownership coupled | Accepted post-cleanup monitor, fixed collector and overlap rules; existing source tests retained |
| Disconnect helper returns despite native failure | Primary result preservation hid failure from process admission | Private receipt recorded before cancellation escapes; sticky stop and remaining-task settlement; fresh held-failure signal controls |
| Uncached worker read scans all dialogs | Legacy BatchEngine fallback | Worker-only bounded resolver; unchanged library fallback confirmed structurally |
| Buffered output survives stop/error at interpreter exit | Hidden final flush retries pending bytes | Raw writer, no teardown flush; actual broken/undrained pipe tests retained |
| Quiet stop does not begin cleanup | Task cancellation did not wake the selector; test timer hid it | Immediate cancel plus public loop wake; timer-free permanent and fresh quiet mixed-signal controls |
| Raw auth text reaches JSON reason | Wrapper preserved raw text; spelling was treated as trust | Frozen canonical-name set in worker projector; all source phases and secondary paths covered |

Every established failure has a corresponding mechanism and actual covering evidence.
No empty restart row, wrong-layer conclusion or missing architectural premise found.

## Inherited Lessons

- Requested cancellation is not started cleanup: timer-free real-loop prebuild1
  preceded Step2; permanent tests and new quiet controls observe actual cleanup entry.
- Returned cleanup is not disconnection: receipt/transport state are checked, and
  fresh failed cleanup remains disconnected=false while task settlement succeeds.
- Name-shaped text is not recognized metadata: canonical vocabulary is fixed before
  Step3; decoded SDK tests prove omission after later wrappers/health observation.
- Passing neighboring tests is not the new composition: full combined prebuild
  preceded integration; fresh review extends edges rather than repeating its totals.
- Cache/session labels are not identity; membership is not readability: existing
  expected-account and qualified group APIs remain authoritative, before claims.
- More abstraction is not more safety: two small private process phases and one
  publication set address real boundaries. There is no second concrete worker
  transport requiring a controller, nor another broken canonical-error consumer
  justifying a library-wide migration.

## Risks

No new reportable High, Medium or Low findings. No mitigation tiers are invented
for unsupported hypothetical deployments or for a benign trusted constructor form
already acknowledged by revision4. No product change is requested by this review.

## Probe results, fixture corrections and limits

`probes/pr_r4_lifetime.py/.txt`:

```text
10 ordered histories: quiet mixed signals; successful/failed native cleanup;
  completed-result publication; closed loop — each under SIGINT/SIGTERM.
Exits130/143; charge2; one client/disconnect attempt; no successor; handlers/logging
  restored; pending tasks0. Failed cleanup remains disconnected=false.
3 back-to-back controls: sent [SIGTERM,SIGINT], observed owner can be INT or TERM;
  exit always128+the real stop owner. No child timer supplies progress.
```

The initial probe sent two different signals without a dispatch handshake and
incorrectly assumed send order was handler order; its failure is retained in
`pr_r4_lifetime-fixture.txt`. A first instrumentation attempt incorrectly used
handler **completion** order as ownership; nested handlers can finish out of order,
and that failed control is retained in `pr_r4_lifetime-fixture2.txt`. The final probe
observes the real handler's already-set stop-reason closure. Ordered histories wait
for the first completed handler before sending the other signal; their original
first-signal assertions remain. Separate back-to-back controls demonstrate that
both130 and143 are possible for that send sequence, depending on actual ownership.
No production signal action, cleanup behavior or accepted result was changed.

`probes/pr_r4_diagnostics.py/.txt`:

```text
42 unknown401/406/403 source histories +6 canonical later-proof controls =48 PASS.
Setup/admission/resolution: no read/join charge. History: correct1/2 charge.
After100-message prefix: original batch ID preserved, charge200, error still raised.
All48: no raw sentinel in replies/health; actual cleanup; B succeeds without
  inheriting/clearing A's state. Protocol/short-write/library-reason controls PASS.
```

No diagnostic fixture correction was required. Socket connect/connect_ex are blocked;
all configs, sessions, ledgers and processes are synthetic and owned. Named signal,
write and loop-close hooks observe/inject a specific boundary and delegate to the
real implementation; they are not claims of arbitrary production timing coverage.
No source functions, SDK cleanup, budget decisions or output encoders were fabricated.

The prior631-pass/3-live-skip and package/example artifacts remain valid for the
identical product. This review adds evidence; it does not claim an exhaustive proof,
live Telegram qualification, unbounded graceful-shutdown deadline or concurrent
session safety. No product edits, real policy changes or merge occurred.

## Disposition

Phase2 complete. The renewed fidelity check passed and this fresh soundness gate
passes with no findings. Phase3 still records its independent selection pass before
publication is finalized. PR27 may then leave draft status; merge still requires
the maintainer's explicit go-ahead and must exclude the work documents while keeping
the feature branch as the archive.
