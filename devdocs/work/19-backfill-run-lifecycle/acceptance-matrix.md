---
model: gpt-6-astra
effort: max
status: stage-2-partial-local-evidence
---
# Backfill acceptance and failure matrix

This is the test specification for [contract.md](contract.md). Stage 2 now has scoped
local evidence at `1425fd7`, listed below and in [verification](stage-2-state/verification.md).
A case still marked UNRUN has not completed its full listed composition; that does
not discard its partial local observations. No live case or gate has passed.

C01–C22 preserve the final inquiry's 22 histories in their original order. C23–C44 add operation, storage, live-oracle and selected-critique boundaries. Gate A foundation tests can use the existing reader with the Stage 2 record; they do not claim that Stage 3 preparation already exists. Cases spanning multiple stages are repeated at their first full composition.

LIVE means actual Telegram via Telethon 1.45.0; INJECTED means an identified local interruption/order/fault around real source/store/receiver paths; LOCAL means no server behavior is inferred. No Telegram source writes are allowed.

## Stage 2 evidence scope — 2026-10-07

| Cases | Actual observation | Still unverified |
|---|---|---|
| C01 | Real SQLite commit/cleanup failure and process exits before/after commit; exact retry and forbidden-clock date preservation | Saved query against live source at A |
| C02, C04, C37 | Changed-input conflict, pruned/unknown retry refusal and affirmative first-use creation | No live claim; C04 history is seeded valid terminal state |
| C03 | Successor/predecessor generation and bounded retention from valid seeded terminal snapshots | Actual completion/control transitions; live composition |
| C05 | Missing file/row, schema-less/corrupt state and backend errors refuse; existing-only open cannot bootstrap | Recovery operation and later public integration |
| C12 | Imported origin, including maximum supported ID, creates no acceptance or exhaustion | Live tail/end/completion semantics |
| C33, C34 | Internal start/status remain local; sanitization, namespace isolation and existing offline regressions pass | Later operations, public facade and live attribution/integration |
| C40–C42 | Probe preflight refuses unqualified input; real SDK page/send guards and comparison exercised with synthetic transport | Independent existing-history oracle and every actual source observation |
| C43, C44 | Strict nested codec/input/counter checks and unchanged-state refusal through internal start/status | Later transition operations and valid saved query's live use |

No prepare, acknowledgment, completion, pacing admission, control or recovery operation
is covered by a seeded snapshot. All other cases remain unrun. [Gate A](validation/gate-a.md)
is BLOCKED on actual inputs. The probe's individual MATCH cannot automatically pass it.

## C01 — Start reply lost

**Setup and ordered stimulus:** A valid new start committed, but its response was lost; retry the same request tomorrow.
**Required observation:** Return the original run, dates and attributable status without reading a new clock.
**Forbidden outcome:** Creating another generation or moving the window.
**Operations:** OP-START OP-STATUS. **Requirements:** INV-01 INV-05 INV-09.
**Evidence / earliest check:** LOCAL/INJECTED; saved query also used LIVE at A; Stage 2 / Gate A.
**Status:** UNRUN.

## C02 — Changed input reuses creation identity

**Setup and ordered stimulus:** Submit a retained creation identity with different window, origin, destination or policy.
**Required observation:** Conflict; old state unchanged and no source request.
**Forbidden outcome:** Reinterpreting the earlier command.
**Operations:** OP-START. **Requirements:** INV-01 INV-05.
**Evidence / earliest check:** LOCAL; Stage 2 / Gate A.
**Status:** LOCAL PASS at `1425fd7` for internal OP-START; no gate PASS implied.

## C03 — Deliberate identical new job

**Setup and ordered stimulus:** After a terminal quiescent settled predecessor, submit new intent with identical settings and matching predecessor.
**Required observation:** A distinct generation/ref; independent new progress and no inherited acceptance.
**Forbidden outcome:** Collapsing jobs solely because parameters match.
**Operations:** OP-START. **Requirements:** INV-01 INV-03 INV-05.
**Evidence / earliest check:** LOCAL/INJECTED; repeat with real history; Stage 2 / Gate A; composition C.
**Status:** UNRUN.

## C04 — Forgotten old start

**Setup and ordered stimulus:** An old creation request is outside retained history; submit it as retry or with a stale predecessor.
**Required observation:** Unknown/conflict without mutation or new intent.
**Forbidden outcome:** Treating nonrecognition as evidence of first use.
**Operations:** OP-START OP-STATUS. **Requirements:** INV-01 INV-05 INV-10.
**Evidence / earliest check:** LOCAL; Stage 2 / Gate A.
**Status:** LOCAL PASS at `1425fd7` from seeded terminal history; producing that history via later operations remains unrun.

## C05 — Known state unavailable

**Setup and ordered stimulus:** Request a known RunRef after row/file loss, malformed state or backend outage.
**Required observation:** Report unknown/corrupt/storage uncertainty separately; no bootstrap or Telegram call.
**Forbidden outcome:** Resetting progress or calculating another window.
**Operations:** OP-STATUS OP-START OP-RECOVER. **Requirements:** INV-01 INV-09 INV-11.
**Evidence / earliest check:** LOCAL/INJECTED on real backend; Stage 2 / Gate A; recovery rechecked C.
**Status:** UNRUN.

## C06 — Old resume response arrives last

**Setup and ordered stimulus:** Resume accepted, then pause accepted; deliver the old resume response after the pause response.
**Required observation:** Pause remains authoritative; older response is attributable to its revision.
**Forbidden outcome:** Displaying/using arrival order as new permission.
**Operations:** OP-CONTROL OP-STATUS. **Requirements:** INV-05 INV-08.
**Evidence / earliest check:** LOCAL/INJECTED around actual storage; Stage 6 / Gate C.
**Status:** UNRUN.

## C07 — Unaccepted stale resume

**Setup and ordered stimulus:** A resume request still names an older control revision after a newer pause.
**Required observation:** Conflict, no new read permission and no automatic rebase.
**Forbidden outcome:** Changing the request to the current revision for the caller.
**Operations:** OP-CONTROL. **Requirements:** INV-05 INV-06 INV-08.
**Evidence / earliest check:** LOCAL/INJECTED; Stage 6 / Gate C.
**Status:** UNRUN.

## C08 — Two conflicting controls

**Setup and ordered stimulus:** Two new commands address the same control revision and try pause/resume/cancel in controlled order.
**Required observation:** One accepted order or explicit conflict; no two contradictory authoritative effects.
**Forbidden outcome:** Choosing a winner from client clocks.
**Operations:** OP-CONTROL OP-STATUS. **Requirements:** INV-08 INV-09.
**Evidence / earliest check:** INJECTED with real storage/await barriers; Stage 6 / Gate C.
**Status:** UNRUN.

## C09 — Completion before cancellation

**Setup and ordered stimulus:** Final ack commits completion before a cancel command is accepted.
**Required observation:** Remain completed; later cancel cannot rewrite terminal history.
**Forbidden outcome:** Relabeling an accepted completion.
**Operations:** OP-ACK OP-CONTROL. **Requirements:** INV-03 INV-04 INV-08.
**Evidence / earliest check:** INJECTED using actual receiver/store; live payload; Stage 6 / Gate C.
**Status:** UNRUN.

## C10 — Cancellation before final receipt

**Setup and ordered stimulus:** Cancel commits while a final batch is owed; then its valid receipt arrives.
**Required observation:** Record accepted delivery/cursor for that run, while terminal outcome remains cancelled.
**Forbidden outcome:** Resurrection or relabeling cancellation as completed.
**Operations:** OP-CONTROL OP-ACK. **Requirements:** INV-03 INV-04 INV-08.
**Evidence / earliest check:** INJECTED using actual receiver/store; live payload; Stage 6 / Gate C.
**Status:** UNRUN.

## C11 — Final receipt while paused

**Setup and ordered stimulus:** Source is exhausted and final output owed; pause, then acknowledge it.
**Required observation:** Complete without a source read or resume.
**Forbidden outcome:** Making acknowledgment depend on permission to fetch.
**Operations:** OP-CONTROL OP-ACK. **Requirements:** INV-03 INV-04 INV-06 INV-08.
**Evidence / earliest check:** LIVE plus controlled local receipt order; Stage 6 / Gate C; basic completion B.
**Status:** UNRUN.

## C12 — Imported midpoint

**Setup and ordered stimulus:** A September scope is explicitly initialized from a caller-supplied September 20 position and reaches its end.
**Required observation:** Report completion only for the declared tail; imported prefix stays caller-asserted.
**Forbidden outcome:** Claiming this run collected the skipped prefix.
**Operations:** OP-START OP-PREPARE OP-STATUS. **Requirements:** INV-01 INV-04.
**Evidence / earliest check:** LIVE bounded oracle plus LOCAL origin checks; Gate A foundation; Stage 4 / Gate B completion.
**Status:** UNRUN.

## C13 — Daily progress cannot seed fresh backfill silently

**Setup and ordered stimulus:** Daily progress exists for a group; create a fresh historical run covering older existing history.
**Required observation:** Fresh origin is zero and dates remain historical; daily state is independent.
**Forbidden outcome:** Borrowing the newer daily cursor without explicit import.
**Operations:** OP-START OP-PREPARE. **Requirements:** INV-01 INV-03 INV-04.
**Evidence / earliest check:** LIVE from independent scopes; LOCAL state comparison; Gate A foundation; B/D composition.
**Status:** UNRUN.

## C14 — Full last batch followed by refusal

**Setup and ordered stimulus:** Receive a limit-sized batch, acknowledge it, then encounter quota/transport refusal when checking for more.
**Required observation:** Remain incomplete without end evidence; retain the real stop reason.
**Forbidden outcome:** Treating full size or latest known ID as proof of end.
**Operations:** OP-PREPARE OP-ACK. **Requirements:** INV-04 INV-11.
**Evidence / earliest check:** LIVE plus local budget/failure injection; Stage 4 / Gate B.
**Status:** UNRUN.

## C15 — Missing local artifact after receiver acceptance

**Setup and ordered stimulus:** Receiver has committed exact batch/artifacts; remove a disposable local copy before replay/ack.
**Required observation:** Replay fails integrity; a matching receipt can still record prior durable acceptance.
**Forbidden outcome:** Replacement download, or refusing acceptance solely because local replay is unavailable.
**Operations:** OP-PREPARE OP-ACK. **Requirements:** INV-02 INV-03 INV-11.
**Evidence / earliest check:** LIVE media and real receiver; INJECTED local removal; Stage 3 / Gate B.
**Status:** UNRUN.

## C16 — Live pending receipt outlives history policy

**Setup and ordered stimulus:** Keep one batch owed longer than the historical recognition policy; prune only eligible historical metadata.
**Required observation:** Its data/context remain replayable and acknowledgeable.
**Forbidden outcome:** Expiring the live obligation or its ability to settle.
**Operations:** OP-PREPARE OP-ACK. **Requirements:** INV-02 INV-05 INV-10.
**Evidence / earliest check:** LOCAL/INJECTED with actual storage and saved bytes; Stage 3 / Gate B; pruning rechecked C.
**Status:** UNRUN.

## C17 — Budget ends after usable prefix

**Setup and ordered stimulus:** Actual bounded reads consume the small test allowance after complete records were prepared.
**Required observation:** Save/deliver the complete prefix; retain budget failure and incomplete source state.
**Forbidden outcome:** Advancing without ack or treating a short interrupted prefix as end.
**Operations:** OP-PREPARE OP-ACK. **Requirements:** INV-02 INV-03 INV-04 INV-06 INV-11.
**Evidence / earliest check:** LIVE with real budget/store/receiver; Stage 3 / Gate B; timing C.
**Status:** UNRUN.

## C18 — Crash after possible send

**Setup and ordered stimulus:** Kill the reader after source activity is possible but before durable settlement; wait for worker exit.
**Required observation:** Unresolved attempt blocks another read; recovery preserves facts and applies the declared conservative wait.
**Forbidden outcome:** Inferring no send, worker death or accepted output from missing response.
**Operations:** OP-PREPARE OP-RECOVER. **Requirements:** INV-06 INV-07 INV-09 INV-12.
**Evidence / earliest check:** LIVE plus INJECTED subprocess interruption; Stage 5 / Gate C.
**Status:** UNRUN.

## C19 — Restart during known wait

**Setup and ordered stimulus:** Persist a known post-attempt deadline; restart and repeatedly inspect/replay.
**Required observation:** Same deadline; no premature source request and no timer extension from observation.
**Forbidden outcome:** Resetting or continually restarting the pause.
**Operations:** OP-PREPARE OP-STATUS. **Requirements:** INV-06 INV-07.
**Evidence / earliest check:** LIVE elapsed timing plus LOCAL injected-clock edges; Stage 5 / Gate C.
**Status:** UNRUN.

## C20 — Untrustworthy time evidence

**Setup and ordered stimulus:** Present conflicting/backward time evidence or lack the evidence needed to establish elapsed wait.
**Required observation:** Report uncertain eligibility and no newly authorized read.
**Forbidden outcome:** Inventing readiness or claiming protection against all undetectable clock jumps.
**Operations:** OP-PREPARE OP-RECOVER OP-STATUS. **Requirements:** INV-06 INV-07.
**Evidence / earliest check:** LOCAL; separate from LIVE timing evidence; Stage 5 / Gate C.
**Status:** UNRUN.

## C21 — Commit succeeded but response failed

**Setup and ordered stimulus:** Inject failure/exit immediately after actual create/publish/ack/end/control/recovery commit.
**Required observation:** Reload committed outcome; retry without duplicate effect or assumed rollback.
**Forbidden outcome:** Reverting accepted progress or issuing compensating new source work blindly.
**Operations:** OP-START OP-PREPARE OP-ACK OP-CONTROL OP-RECOVER OP-STATUS. **Requirements:** INV-03 INV-05 INV-09.
**Evidence / earliest check:** INJECTED at actual store commits; A create; B publish/ack/end; C controls/recovery.
**Status:** UNRUN.

## C22 — Paused, pending and rate-limited together

**Setup and ordered stimulus:** A saved batch coexists with operator pause and source wait; replay and acknowledge using the correct context.
**Required observation:** Expose all facts; allow local settlement, deny new source admission.
**Forbidden outcome:** Letting one display label erase another restriction or obligation.
**Operations:** OP-PREPARE OP-ACK OP-STATUS OP-CONTROL. **Requirements:** INV-02 INV-03 INV-06 INV-08 INV-11.
**Evidence / earliest check:** LIVE payload plus INJECTED conditions; Stage 6 / Gate C.
**Status:** UNRUN.

## C23 — Empty and nonempty exhausted scope

**Setup and ordered stimulus:** Use independently known empty scope and nonempty end result; restart before/after final settlement.
**Required observation:** Empty end commits completion without fake upload; nonempty end waits for ack; reopening is local.
**Forbidden outcome:** Equating arbitrary None/error with end, or reading again after completed status.
**Operations:** OP-PREPARE OP-ACK OP-STATUS. **Requirements:** INV-03 INV-04 INV-09.
**Evidence / earliest check:** LIVE oracle with actual storage and crash boundaries; Stage 4 / Gate B.
**Status:** UNRUN.

## C24 — Failure before a usable prefix

**Setup and ordered stimulus:** Refuse or interrupt a source read before any complete record is available.
**Required observation:** No pending/accepted/end evidence invented; preserve failure and known/uncertain attempt state.
**Forbidden outcome:** Returning successful empty completion.
**Operations:** OP-PREPARE OP-STATUS. **Requirements:** INV-03 INV-04 INV-11.
**Evidence / earliest check:** LIVE read with INJECTED local failure; LOCAL source categories; Stage 3 / Gate B; recovery C.
**Status:** UNRUN.

## C25 — Prefix save also fails

**Setup and ordered stimulus:** A read has a complete prefix and source error; actual persistence then fails.
**Required observation:** Local persistence error keeps original read error separately; no promise of durable prefix; no false Telegram health.
**Forbidden outcome:** Cleanup/storage replacing the original context silently or signaling fake source recovery.
**Operations:** OP-PREPARE. **Requirements:** INV-02 INV-09 INV-11.
**Evidence / earliest check:** INJECTED with real backend; existing local health checks; Stage 3 / Gate B.
**Status:** UNRUN.

## C26 — Admission write failed or uncertain

**Setup and ordered stimulus:** Fail/cancel the attempt-admission write before its success is established, including commit-then-error.
**Required observation:** No source send unless the intended admission is authoritatively reconciled; otherwise recover/stop.
**Forbidden outcome:** Sending because the write probably worked or probably rolled back.
**Operations:** OP-PREPARE OP-RECOVER. **Requirements:** INV-06 INV-09 INV-12.
**Evidence / earliest check:** INJECTED actual backend; count real send boundary; Stage 3 / Gate B.
**Status:** UNRUN.

## C27 — Late source result after control mutation

**Setup and ordered stimulus:** Hold an admitted real read result before settlement; commit pause/cancel; then release the result.
**Required observation:** Settle only the same attempt/run/cursor, retain usable output and preserve the newer control.
**Forbidden outcome:** Whole-record stale overwrite, new fetch to repair CAS, or silent discard solely because control changed.
**Operations:** OP-PREPARE OP-CONTROL. **Requirements:** INV-02 INV-05 INV-08 INV-09.
**Evidence / earliest check:** LIVE plus INJECTED await barrier; Stage 6 / Gate C.
**Status:** UNRUN.

## C28 — Recovery while old reader lives

**Setup and ordered stimulus:** Keep a local read active; request recovery, including a false or wrongly asserted quiescence flag.
**Required observation:** Reject the live local attempt regardless; caller must actually stop/wait for worker before sequential recovery.
**Forbidden outcome:** Treating a timeout or boolean alone as a distributed ownership proof.
**Operations:** OP-RECOVER OP-PREPARE. **Requirements:** INV-06 INV-12.
**Evidence / earliest check:** INJECTED subprocess/local-task control; Stage 5 / Gate C.
**Status:** UNRUN.

## C29 — Corrupt pending artifact

**Setup and ordered stimulus:** Modify only a disposable saved test blob, then request pending replay.
**Required observation:** Integrity failure with same pending identity/cursor; no source refetch.
**Forbidden outcome:** Accepting changed bytes because filename/path matches.
**Operations:** OP-PREPARE. **Requirements:** INV-02 INV-11.
**Evidence / earliest check:** LIVE media plus INJECTED filesystem fault; Stage 3 / Gate B.
**Status:** UNRUN.

## C30 — Wrong collection, destination or run receipt

**Setup and ordered stimulus:** Prepare equal payload bytes in different contexts; submit the other context or destination receipt.
**Required observation:** Refuse without clearing current pending or advancing its cursor.
**Forbidden outcome:** Treating a payload hash as collection/destination authority.
**Operations:** OP-ACK. **Requirements:** INV-03 INV-05.
**Evidence / earliest check:** LOCAL/INJECTED with real stored observations; LIVE where equal observations exist; Stage 3 / Gate B.
**Status:** UNRUN.

## C31 — Duplicate latest ack with newer pending

**Setup and ordered stimulus:** Ack batch one, prepare batch two, then repeat batch one ack; also send an older unrecognized receipt.
**Required observation:** Recognized latest ack is harmless and batch two remains; unknown older receipt refuses.
**Forbidden outcome:** Clearing another pending batch or advancing twice.
**Operations:** OP-ACK OP-STATUS. **Requirements:** INV-02 INV-03 INV-05 INV-10.
**Evidence / earliest check:** Real storage and receiver; LIVE payload; Stage 3 / Gate B.
**Status:** UNRUN.

## C32 — Explicit abandonment and successor

**Setup and ordered stimulus:** Cancel with pending data; first attempt abandon while source unresolved, then after quiescence; start a successor.
**Required observation:** Unresolved attempt prevents abandonment/replacement; later explicit abandonment preserves cancelled outcome and cursor, records withdrawal, and permits a scoped successor.
**Forbidden outcome:** Pretending abandoned data was accepted, or letting a late retired receipt affect the successor.
**Operations:** OP-CONTROL OP-START OP-ACK. **Requirements:** INV-03 INV-05 INV-08 INV-10 INV-12.
**Evidence / earliest check:** LOCAL/INJECTED with actual storage; Stage 6 / Gate C.
**Status:** UNRUN.

## C33 — Local public operations and health

**Setup and ordered stimulus:** After recorded source health failure, invoke status/control/ack/replay or cause local storage failure.
**Required observation:** No Telegram calls attributable to those local operations; no fabricated health verdict or recovery.
**Forbidden outcome:** Treating local success/failure as fresh Telegram evidence.
**Operations:** OP-STATUS OP-CONTROL OP-ACK OP-PREPARE OP-RECOVER OP-START. **Requirements:** INV-11.
**Evidence / earliest check:** LOCAL call counters; LIVE attributed trace at D; Stage 7 / Gate D; affected local checks earlier.
**Status:** UNRUN.

## C34 — Legacy compatibility and separate collections

**Setup and ordered stimulus:** Run existing daily/window APIs/state and batch v1 alongside lifecycle code; schedule readers sequentially.
**Required observation:** Unchanged legacy behavior and independent progress; wrong record kinds refuse.
**Forbidden outcome:** Silently migrating daily data or advancing another collection.
**Operations:** OP-START OP-PREPARE OP-ACK OP-STATUS. **Requirements:** INV-01 INV-03 INV-09.
**Evidence / earliest check:** LOCAL regressions plus LIVE sequential integration; On any shared edit; Stage 7 / Gate D.
**Status:** UNRUN.

## C35 — Delayed prepare after acknowledgment

**Setup and ordered stimulus:** Save an old PrepareContext, acknowledge its earlier batch, then deliver that old prepare call again.
**Required observation:** Stale accepted-position conflict before a source send; current state unchanged.
**Forbidden outcome:** Turning the old call into fetch-next at the new cursor.
**Operations:** OP-PREPARE OP-ACK. **Requirements:** INV-05 INV-06.
**Evidence / earliest check:** LOCAL/INJECTED actual lifecycle state; LIVE request attribution; Stage 3 / Gate B.
**Status:** UNRUN.

## C36 — Delayed prepare after pause/resume

**Setup and ordered stimulus:** Save a PrepareContext, change control revision through pause/resume, then submit the old context.
**Required observation:** Stale control conflict before source admission; caller must obtain current context deliberately.
**Forbidden outcome:** Automatically using the newer operator permission.
**Operations:** OP-PREPARE OP-CONTROL. **Requirements:** INV-05 INV-06 INV-08.
**Evidence / earliest check:** INJECTED barriers with actual state; LIVE turns; Stage 6 / Gate C.
**Status:** UNRUN.

## C37 — Absent slot is not unknown retry permission

**Setup and ordered stimulus:** Compare an affirmative new first-use submission with the same request submitted as retry when absent; also test missing known state.
**Required observation:** Only explicit new first use may create under its preconditions; unknown retry and failed known-run restore refuse.
**Forbidden outcome:** Inferring new intent from absence or hiding total-history loss.
**Operations:** OP-START OP-STATUS. **Requirements:** INV-01 INV-05 INV-09.
**Evidence / earliest check:** LOCAL real backend; Stage 2 / Gate A.
**Status:** LOCAL PASS at `1425fd7` for internal start/status and real SQLite; no gate PASS implied.

## C38 — Intentional retry after settled failure

**Setup and ordered stimulus:** A source attempt failed and settled with unchanged accepted position/no pending; call prepare with current context before and after eligibility.
**Required observation:** Before deadline no send; after eligibility one new admitted attempt is allowed. Unresolved work still refuses.
**Forbidden outcome:** Promising indefinite old-prepare replay or treating every repeated call as free source work.
**Operations:** OP-PREPARE OP-RECOVER. **Requirements:** INV-06 INV-07 INV-12.
**Evidence / earliest check:** LIVE failure injection plus LOCAL timing cases; Stage 5 / Gate C.
**Status:** UNRUN.

## C39 — Recovery reply lost

**Setup and ordered stimulus:** Recover a quiescent unknown attempt; lose the committed recovery reply; repeat the same command after restart.
**Required observation:** Recognize/reconcile the same effect and deadline without another quiet interval or source read.
**Forbidden outcome:** Resetting the wait each time or recovering a different current attempt.
**Operations:** OP-RECOVER OP-STATUS. **Requirements:** INV-05 INV-07 INV-09 INV-12.
**Evidence / earliest check:** INJECTED actual store/process boundary; Stage 5 / Gate C.
**Status:** UNRUN.

## C40 — Missing independent oracle or source drift

**Setup and ordered stimulus:** Fixture contains only sampled IDs, is derived from the tested reader, lacks a critical case, or changes during measurement.
**Required observation:** Gate is BLOCKED/INCONCLUSIVE or FAIL as appropriate; preserve differences and stop dependent work.
**Forbidden outcome:** Retrospectively changing expected results, seeding Telegram messages, or passing synthetic-only live coverage.
**Operations:** VALIDATION. **Requirements:** INV-04 INV-11.
**Evidence / earliest check:** LIVE independent existing-history evidence; Fixture qualification / Gate A; recheck every gate.
**Status:** UNRUN.

## C41 — Real SDK and caller pagination

**Setup and ordered stimulus:** Use existing history with an independently complete interval crossing an actual SDK history page and multiple caller batches, including available ties/gaps.
**Required observation:** Recorded request/page trace and accepted union match expected visible IDs exactly within scope.
**Forbidden outcome:** Counting repeated small first pages as an SDK boundary test or using the same reader as the sole oracle.
**Operations:** OP-START OP-PREPARE. **Requirements:** INV-01 INV-04 INV-11.
**Evidence / earliest check:** LIVE, existing group, read-only; Gate A foundation; Gate B/D new API.
**Status:** UNRUN.

## C42 — Exact date selection and media mode

**Setup and ordered stimulus:** Select existing boundary messages and media independently; read fresh/imported windows and reference/download modes.
**Required observation:** Start-inclusive/end-exclusive selection; media only for included messages; required hashes verified. Missing critical live media/boundary cases remain unverified.
**Forbidden outcome:** Claiming unseen cases passed, downloading excluded media, or creating fixture messages.
**Operations:** OP-START OP-PREPARE. **Requirements:** INV-01 INV-02 INV-04 INV-11.
**Evidence / earliest check:** LIVE plus separate LOCAL malformed/bounds cases; Gate A foundation; B/D composition.
**Status:** UNRUN.

## C43 — Invalid or incompatible saved state

**Setup and ordered stimulus:** Load wrong kind/version, duplicate/missing fields, contradictory cursor/receipt state or malformed dates.
**Required observation:** Local validation/storage refusal without repair, source traffic or new enrollment.
**Forbidden outcome:** Interpreting lifecycle as daily state or guessing unknown fields.
**Operations:** OP-START OP-PREPARE OP-STATUS OP-ACK OP-CONTROL OP-RECOVER. **Requirements:** INV-01 INV-09 INV-11.
**Evidence / earliest check:** LOCAL real backend with injected corrupt records; Stage 2 / Gate A; public regression D.
**Status:** UNRUN.

## C44 — Input, scope and identity normalization

**Setup and ordered stimulus:** Exercise accepted timezone normalization/ID bounds and reject booleans, invalid tokens, naive/mixed dates, future end, invalid origin/media/pacing and counter wrap.
**Required observation:** Valid equivalent normalized inputs retain identity; invalid/conflicting inputs produce no lifecycle/source effect.
**Forbidden outcome:** Using a different input form to reset an accepted intent or losing precision in identifiers.
**Operations:** OP-START OP-PREPARE OP-ACK OP-CONTROL OP-RECOVER OP-STATUS. **Requirements:** INV-01 INV-05 INV-09.
**Evidence / earliest check:** LOCAL; valid saved query also checked LIVE at A; Stage 2 / Gate A; later operations as implemented.
**Status:** UNRUN.

## Operation coverage

| Operation | Cases |
|---|---|
| OP-START | C01, C02, C03, C04, C05, C12, C13, C21, C32, C33, C34, C37, C41, C42, C43, C44 |
| OP-STATUS | C01, C04, C05, C06, C08, C12, C19, C20, C21, C22, C23, C24, C31, C33, C34, C37, C39, C43, C44 |
| OP-PREPARE | C12, C13, C14, C15, C16, C17, C18, C19, C20, C21, C22, C23, C24, C25, C26, C27, C28, C29, C33, C34, C35, C36, C38, C41, C42, C43, C44 |
| OP-ACK | C09, C10, C11, C14, C15, C16, C17, C21, C22, C23, C30, C31, C32, C33, C34, C35, C43, C44 |
| OP-CONTROL | C06, C07, C08, C09, C10, C11, C21, C22, C27, C32, C33, C36, C43, C44 |
| OP-RECOVER | C05, C18, C20, C21, C26, C28, C33, C38, C39, C43, C44 |

## Invariant coverage

| Invariant | Cases |
|---|---|
| INV-01 | C01, C02, C03, C04, C05, C12, C13, C34, C37, C41, C42, C43, C44 |
| INV-02 | C15, C16, C17, C22, C25, C27, C29, C31, C42 |
| INV-03 | C03, C09, C10, C11, C13, C15, C17, C21, C22, C23, C24, C30, C31, C32, C34 |
| INV-04 | C09, C10, C11, C12, C13, C14, C17, C23, C24, C40, C41, C42 |
| INV-05 | C01, C02, C03, C04, C06, C07, C16, C21, C27, C30, C31, C32, C35, C36, C37, C39, C44 |
| INV-06 | C07, C11, C17, C18, C19, C20, C22, C26, C28, C35, C36, C38 |
| INV-07 | C18, C19, C20, C38, C39 |
| INV-08 | C06, C07, C08, C09, C10, C11, C22, C27, C32, C36 |
| INV-09 | C01, C05, C08, C18, C21, C23, C25, C26, C27, C34, C37, C39, C43, C44 |
| INV-10 | C04, C16, C31, C32 |
| INV-11 | C05, C14, C15, C17, C22, C24, C25, C29, C33, C40, C41, C42, C43 |
| INV-12 | C18, C26, C28, C32, C38, C39 |

## Reading the result

A case passes only when its actual expected and forbidden outcomes have been checked at the named composition. A matching heading, policy choice or simulated future engine is not that evidence. Each gate report links to these IDs and records revision, environment, oracle, observations and limitations. No required case may be silently skipped to advance.
