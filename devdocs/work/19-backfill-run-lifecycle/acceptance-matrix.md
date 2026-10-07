---
model: gpt-6-astra
effort: max
status: stage-8-and-gate-d-PASS
---
# Backfill acceptance and failure matrix

This is the test specification for [contract.md](contract.md). Stage 2 has scoped
local evidence at `1425fd7`; Stage 3 adds actual internal delivery checks at `3140dcd`,
recorded in [its verification](stage-3-delivery/verification.md).
A case still marked UNRUN has not completed its full listed composition; that does
not discard its partial observations. Gate A's foundation scope has now passed; later
operation/composition requirements remain scoped below. Stage 4 and Gate B evidence
now supplement those historical records; they do not credit unbuilt later operations.

C01–C22 preserve the final inquiry's 22 histories in their original order. C23–C44 add operation, storage, live-oracle and selected-critique boundaries. Gate A foundation tests can use the existing reader with the Stage 2 record; they do not claim that Stage 3 preparation already exists. Cases spanning multiple stages are repeated at their first full composition.

LIVE means actual Telegram via Telethon 1.45.0; INJECTED means an identified local interruption/order/fault around real source/store/receiver paths; LOCAL means no server behavior is inferred. No Telegram source writes are allowed.

## Stage 8 and Gate D — current completion record

**PASS at `405218e`: 357 actual supported offline checks, three explicit legacy live
skips, 19 instrument checks and both examples.** [Verification](stage-8-validation/verification.md).
[Gate D PASS](validation/gate-d.md) adds the complete public/real-source/SQLite/receiver
composition, exact 250-message history plus two daily records, controls, source and
commit exits, 100-record interrupted prefix, verified photo custody and real pacing.
Every C01–C44 status below now names its scoped actual evidence; no blanket range
claim replaces missing cases. [Whole-feature readiness audit](stage-8-validation/review-readiness.md).
Formal merge-check/PR/fresh PR critique and operational adoption remain separate.
The earlier stage sections below are historical checkpoints, not outstanding gate status.

## Stage 7 public composition evidence — 2026-10-07

Product `17fccbc`: 23 new public/example groups, 342 actual supported offline passes,
three explicit legacy live skips. [Verification](stage-7-public-api/verification.md).
Six public methods preserve typed context, engine lifetime/clock minima, source-health
ownership and backend scope. Local status/logs exclude payload/credential sentinels.
Actual SQLite example namespaces/receiver snapshots and an owned process restart pass;
source observations remain synthetic. Existing A/B/C live evidence is not relabeled.

C33/C34 now have scoped public LOCAL evidence, with their LIVE portions still required
at Gate D. Public tests cover creation/recognition, exact delivery, terminal order,
source overlap, recovery, clock retention, failure provenance and namespace boundaries.
They do not replace every combined history in this matrix; prior internal suites retain
their invariant coverage, and the complete public composition remains Stage 8/Gate D.
**Next: Stage 8 and mandatory Gate D; no new live gate has passed in Stage 7.**

## Stage 6 and Gate C evidence — 2026-10-07

Product `0d6bb26`: 32 new control groups and 319 total supported offline passes;
three legacy live skips. [Verification](stage-6-controls/verification.md).
[Gate C PASS](validation/gate-c.md) combines the core cases, exact matrix supplement
and independent saved-record audit. Earlier tables below are historical checkpoints.

| Cases / boundary | New scoped evidence | Still required |
|---|---|---|
| C03/04/06–11/16/21/22/27/28/32/36 | Actual commands, produced terminal histories, lost replies, late result/receipt orderings, quiescence, retirement and equal-hash successors; live-origin data and actual receiver/store | Public facade/selected deployment checks at D |
| C17–20/24/26/38/39 | Live allowance exhaustion/prefixes, measured waits/restart, owned-worker source/recovery exits and stable deadline; deterministic time/expiry edge cases separately local | Arbitrary deployment clocks/ownership remain caller assumptions |
| C25/33/34/35/37/43/44 | Full supported regressions and no local-operation RPC in Gate C traces; strict namespace/context/validation preserved | C33/C34 public/integrated daily flow at D |

No required Gate C case was skipped. Existing raw reader/window/media semantics and
state schema were unchanged, so A/B remain valid. At the Stage 6 checkpoint Stage 7 was next; the Stage 7 section above records its
later offline completion. Gate D remains pending.

## Stage 5 local pacing/recovery evidence — 2026-10-07

Product `a180151`: 32 new temporal/fault groups and 287 actual supported offline passes,
three explicit legacy live skips. [Verification](stage-5-pacing-recovery/verification.md).
The tests execute actual engine/SQLite/SDK/budget code with synthetic transport, plus
real local elapsed time and actual recovery commit/process exits. Two copied Gate B
records recover/retry correctly; their originals and the real ledger remain unchanged.

| Cases / boundary | Stage 5 local observation | Still required |
|---|---|---|
| C05, C18–C21, C26, C28, C38, C39 | Exact stopped-attempt recovery; caller assertion/local active refusal; deadline retention; clock faults; actual before/after recovery commits; retry recognition | Live elapsed/budget/recovery/control composition at C |
| C14, C17, C22, C38 | Actual budget prefixes/no-prefix stops, indefinite/expired hints, actual account change and retained cancelled charges; no source send during local pacing | Specific live allowance/expiry/control integration at C |
| C25, C33 | Original errors and direct typed wait hints; no cached identity/cause-derived hints or local health recovery | Public operations at D; controls at C |
| C35–C37, C43, C44 | Existing context/refusal/codec regressions plus new recovery input, changed-ID/control and newer-attempt protection | Future controls/facade and equivalent deployment backend |

Seeded control snapshots do not implement control operations. Clock observations and
LIVE-origin file copies are LOCAL evidence. At this historical Stage 5 checkpoint,
Gate C was pending; the Stage 6/Gate C section above records its later completion.

## Stage 4 and Gate B evidence — 2026-10-07

Product `b1f6495`: 16 new completion groups, 255 actual supported offline passes,
three explicit legacy live skips. [Verification](stage-4-completion/verification.md).
[Gate B PASS](validation/gate-b.md) adds actual source/state/receiver composition.

| Cases / boundary | New evidence | Still unverified |
|---|---|---|
| C01–C05, C21, C25, C26, C43 | Exact-candidate read-back, old/missing/newer/corrupt/unreadable states, cancellation and source provenance; actual final SQLite boundaries | Unbuilt control/recovery/public operations and other backends |
| C12, C14, C23, C24 | Live imported completion, actual full-then-empty, full-then-refused, empty/final commit crashes and complete reopen | Other account views; deployed/public composition |
| C15–C17, C29–C31, C35 | Live-data replay, actual receiver dedup, media custody/removal, equal hashes/wrong scope, duplicate/stale refusal, useful interrupted prefix | C16 later pruning/control composition; C17 actual live quota/wait integration at C |
| C18, C26 (B portions) | Actual post-answer and pre-empty-commit exits preserve unknown attempts; offline reopening refuses another reader | Explicit recovery, conservative waits and controls at C |
| C41, C42 | New engine accepts 350 exact independently expected records with real second SDK pages; photo hash and fresh/imported boundaries agree | Public facade at D |
| C40 | Independent qualification before scans, small-source post-check, unchanged expected sets | Future source drift remains a new qualification requirement |

Gate B deliberately used the staged plan's permitted **controlled-failure** alternative
for the useful prefix; no live quota exhaustion/expiry or policy reset is claimed.
C09–C11/C27/C32/C36 controls remain unrun; local seeded preservation is not those APIs.

## Stage 3 local delivery evidence — 2026-10-07

The actual new engine passed 41 delivery groups using real SQLite, SDK/batch/artifact
code, controlled storage faults and a real local receiver. Transport was synthetic;
Gate B still must run the new composition with real data after Stage 4.

| Cases / boundary | Observed locally in Stage 3 | Still unverified |
|---|---|---|
| C03, C04, C30, C31, C37 | Real successor/retained-receipt behavior, equal-hash run isolation, stale/unknown context refusal | Live new-engine/retirement composition |
| C12–C14, C23 | Original fresh/relative query, imported cursor, empty/final minimal closure and full-batch follow-up | Dedicated Stage 4 completion/final-commit matrix and Gate B |
| C15–C17, C29 | Exact pending replay, real receiver commit/lost reply, media relocation/corruption/removal, ack independent of local media | Operational receiver/media custody and actual Gate B payloads |
| C21, C25, C26 | Actual publication/ack process exits, uncertain real commit cleanup, errors kept separate from source failure | Stage 4 expanded empty/final/uncertain-outcome matrix |
| C27, C28, C35, C36 | Confirmed admission, overlap/unknown-attempt refusal, real cancellation, stale cursor/control checks, compatible late-result preservation | Control/recovery operations and live race composition |
| C33, C34, C43, C44 | No local health recovery/verdict, legacy regressions, strict loaded bounds and exact receipt/context validation | Public facade and later full integration |

Seeded control/recovery snapshots only test preservation. Stage 3's positive timing
guard refuses further source admission where Stage 5 machinery is needed; it is not
implemented pacing/recovery. Case statuses below still refer to their full specified
composition; no unrun live or later-stage portion is credited from these local checks.

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
is covered by a seeded snapshot. These initial local receipts did not pass a live gate.
The later Gate A evidence below is a separate execution and aggregate review.

## Gate A live foundation evidence — 2026-10-07

[Gate A PASS](validation/gate-a.md) records seven independently expected real-source
comparisons, actual SDK pages, an independent photo hash and two controlled local
interruptions around actual reads. test_24 also passed 23/23 again. Each individual
scan still reports INCONCLUSIVE; the documented aggregate review closes the gate.

| Cases | Observed at A | Still outside this evidence |
|---|---|---|
| C01–C05, C37 | Real creation/reopen/retry/refusal tests paired with real saved-query reuse | C03 terminal transitions and C05 recovery are later operations |
| C12, C13 | Imported tail and fresh historical origins drive the declared real query | Lifecycle completion and integrated daily scheduling |
| C14 | A real full batch followed by a refused send remains interrupted, not end | New lifecycle completion and actual quota-expiry/wait integration |
| C18, C24–C28 (characterization only) | Cancellation after a real answered response retains charges and leaves state unchanged | Durable attempt admission/settlement and unknown-outcome recovery |
| C40 | Existing-source qualification, refusal of a non-group and replacement of an undersized page fixture | Future source drift must be requalified, not assumed absent |
| C41 | 350 expected records, six real SDK requests, three caller batches, actual second pages | Repeat through the new preparation/public APIs at B/D |
| C42 | Date boundaries, ties/gaps, empty/full, fresh/imported scope and selected photo hash match | Later pending-media custody/replay |
| C43, C44 | Repeated strict-state/input tests plus valid real query use | Later operation validation and public integration |

Case-level UNRUN below retains the full stated composition for multi-stage cases;
it does not negate the scoped foundation observations above. No later stage is credited
from seeded state, an individual MATCH or raw-reader tests.

## C01 — Start reply lost

**Setup and ordered stimulus:** A valid new start committed, but its response was lost; retry the same request tomorrow.
**Required observation:** Return the original run, dates and attributable status without reading a new clock.
**Forbidden outcome:** Creating another generation or moving the window.
**Operations:** OP-START OP-STATUS. **Requirements:** INV-01 INV-05 INV-09.
**Evidence / earliest check:** LOCAL/INJECTED; saved query also used LIVE at A; Stage 2 / Gate A.
**Status:** PASS (scoped): D main-local original creation retry; test24 relative-window forbidden-clock retry. Named LOCAL regression: test_30 `test_creation_real_commit_exit_pair`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C02 — Changed input reuses creation identity

**Setup and ordered stimulus:** Submit a retained creation identity with different window, origin, destination or policy.
**Required observation:** Conflict; old state unchanged and no source request.
**Forbidden outcome:** Reinterpreting the earlier command.
**Operations:** OP-START. **Requirements:** INV-01 INV-05.
**Evidence / earliest check:** LOCAL; Stage 2 / Gate A.
**Status:** PASS (scoped): LOCAL immutable-intent refusal; common engine revalidated through public retries. Named LOCAL regression: test_24 `test_changed_input_and_active_successor_conflict`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C03 — Deliberate identical new job

**Setup and ordered stimulus:** After a terminal quiescent settled predecessor, submit new intent with identical settings and matching predecessor.
**Required observation:** A distinct generation/ref; independent new progress and no inherited acceptance.
**Forbidden outcome:** Collapsing jobs solely because parameters match.
**Operations:** OP-START. **Requirements:** INV-01 INV-03 INV-05.
**Evidence / earliest check:** LOCAL/INJECTED; repeat with real history; Stage 2 / Gate A; composition C.
**Status:** PASS (scoped): D controls: four real equal-hash generations. Named LOCAL regression: test_30 `test_successor_real_commit_exit_pair_keeps_old_receipt_read_only`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C04 — Forgotten old start

**Setup and ordered stimulus:** An old creation request is outside retained history; submit it as retry or with a stale predecessor.
**Required observation:** Unknown/conflict without mutation or new intent.
**Forbidden outcome:** Treating nonrecognition as evidence of first use.
**Operations:** OP-START OP-STATUS. **Requirements:** INV-01 INV-05 INV-10.
**Evidence / earliest check:** LOCAL; Stage 2 / Gate A.
**Status:** PASS (scoped): D controls: first generation pruned, old receipt refused. Named LOCAL regression: test_28 `test_retained_accepted_receipt_and_previous_cancel_are_read_only_then_pruned`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C05 — Known state unavailable

**Setup and ordered stimulus:** Request a known RunRef after row/file loss, malformed state or backend outage.
**Required observation:** Report unknown/corrupt/storage uncertainty separately; no bootstrap or Telegram call.
**Forbidden outcome:** Resetting progress or calculating another window.
**Operations:** OP-STATUS OP-START OP-RECOVER. **Requirements:** INV-01 INV-09 INV-11.
**Evidence / earliest check:** LOCAL/INJECTED on real backend; Stage 2 / Gate A; recovery rechecked C.
**Status:** PASS (scoped): LOCAL public missing/malformed/file-loss and cleanup boundaries. Named LOCAL regression: test_30 `test_missing_malformed_known_state_and_cleanup_preserve_uncertainty`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C06 — Old resume response arrives last

**Setup and ordered stimulus:** Resume accepted, then pause accepted; deliver the old resume response after the pause response.
**Required observation:** Pause remains authoritative; older response is attributable to its revision.
**Forbidden outcome:** Displaying/using arrival order as new permission.
**Operations:** OP-CONTROL OP-STATUS. **Requirements:** INV-05 INV-08.
**Evidence / earliest check:** LOCAL/INJECTED around actual storage; Stage 6 / Gate C.
**Status:** PASS (scoped): D controls: delayed accepted resume arrives after newer pause. Named LOCAL regression: test_30 `test_opposing_controls_and_delayed_resume_are_revision_ordered`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C07 — Unaccepted stale resume

**Setup and ordered stimulus:** A resume request still names an older control revision after a newer pause.
**Required observation:** Conflict, no new read permission and no automatic rebase.
**Forbidden outcome:** Changing the request to the current revision for the caller.
**Operations:** OP-CONTROL. **Requirements:** INV-05 INV-06 INV-08.
**Evidence / earliest check:** LOCAL/INJECTED; Stage 6 / Gate C.
**Status:** PASS (scoped): D controls: stale resume refuses; original context retained. Named LOCAL regression: test_28 `test_stale_resume_prepare_and_forgotten_command_refuse`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C08 — Two conflicting controls

**Setup and ordered stimulus:** Two new commands address the same control revision and try pause/resume/cancel in controlled order.
**Required observation:** One accepted order or explicit conflict; no two contradictory authoritative effects.
**Forbidden outcome:** Choosing a winner from client clocks.
**Operations:** OP-CONTROL OP-STATUS. **Requirements:** INV-08 INV-09.
**Evidence / earliest check:** INJECTED with real storage/await barriers; Stage 6 / Gate C.
**Status:** PASS (scoped): D controls: actual shared-load/CAS barrier accepts exactly one decision. Named LOCAL regression: test_30 `test_opposing_controls_and_delayed_resume_are_revision_ordered`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C09 — Completion before cancellation

**Setup and ordered stimulus:** Final ack commits completion before a cancel command is accepted.
**Required observation:** Remain completed; later cancel cannot rewrite terminal history.
**Forbidden outcome:** Relabeling an accepted completion.
**Operations:** OP-ACK OP-CONTROL. **Requirements:** INV-03 INV-04 INV-08.
**Evidence / earliest check:** INJECTED using actual receiver/store; live payload; Stage 6 / Gate C.
**Status:** PASS (scoped): D controls: completion-first then cancellation reports terminal. Named LOCAL regression: test_30 `test_ack_real_commit_exit_pair_follows_receiver`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C10 — Cancellation before final receipt

**Setup and ordered stimulus:** Cancel commits while a final batch is owed; then its valid receipt arrives.
**Required observation:** Record accepted delivery/cursor for that run, while terminal outcome remains cancelled.
**Forbidden outcome:** Resurrection or relabeling cancellation as completed.
**Operations:** OP-CONTROL OP-ACK. **Requirements:** INV-03 INV-04 INV-08.
**Evidence / earliest check:** INJECTED using actual receiver/store; live payload; Stage 6 / Gate C.
**Status:** PASS (scoped): D controls: cancellation-first then final receiver/ack remains cancelled. Named LOCAL regression: test_30 `test_late_final_result_cancel_order_and_equal_hash_successor`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C11 — Final receipt while paused

**Setup and ordered stimulus:** Source is exhausted and final output owed; pause, then acknowledge it.
**Required observation:** Complete without a source read or resume.
**Forbidden outcome:** Making acknowledgment depend on permission to fetch.
**Operations:** OP-CONTROL OP-ACK. **Requirements:** INV-03 INV-04 INV-06 INV-08.
**Evidence / earliest check:** LIVE plus controlled local receipt order; Stage 6 / Gate C; basic completion B.
**Status:** PASS (scoped): D prebuild and controls: exact final ack completes while paused. Named LOCAL regression: test_30 `test_control_real_commit_exit_pair_preserves_delivery`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C12 — Imported midpoint

**Setup and ordered stimulus:** A September scope is explicitly initialized from a caller-supplied September 20 position and reaches its end.
**Required observation:** Report completion only for the declared tail; imported prefix stays caller-asserted.
**Forbidden outcome:** Claiming this run collected the skipped prefix.
**Operations:** OP-START OP-PREPARE OP-STATUS. **Requirements:** INV-01 INV-04.
**Evidence / earliest check:** LIVE bounded oracle plus LOCAL origin checks; Gate A foundation; Stage 4 / Gate B completion.
**Status:** PASS (scoped): D prebuild/unknown/photo: imported after13 completes declared photo tail only. Named LOCAL regression: test_24 `test_imported_origin_is_not_acceptance_or_exhaustion`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C13 — Daily progress cannot seed fresh backfill silently

**Setup and ordered stimulus:** Daily progress exists for a group; create a fresh historical run covering older existing history.
**Required observation:** Fresh origin is zero and dates remain historical; daily state is independent.
**Forbidden outcome:** Borrowing the newer daily cursor without explicit import.
**Operations:** OP-START OP-PREPARE. **Requirements:** INV-01 INV-03 INV-04.
**Evidence / earliest check:** LIVE from independent scopes; LOCAL state comparison; Gate A foundation; B/D composition.
**Status:** PASS (scoped): D main: fresh history after0; daily starts at independent recent origin; rows isolated. Named LOCAL regression: test_29 `test_daily_and_backfill_progress_are_separate_and_no_auto_namespace_exists`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C14 — Full last batch followed by refusal

**Setup and ordered stimulus:** Receive a limit-sized batch, acknowledge it, then encounter quota/transport refusal when checking for more.
**Required observation:** Remain incomplete without end evidence; retain the real stop reason.
**Forbidden outcome:** Treating full size or latest known ID as proof of end.
**Operations:** OP-PREPARE OP-ACK. **Requirements:** INV-04 INV-11.
**Evidence / earliest check:** LIVE plus local budget/failure injection; Stage 4 / Gate B.
**Status:** PASS (scoped): D photo: full one-record batch then local refusal remains incomplete; later real end. Named LOCAL regression: test_25 `test_exact_full_batch_needs_real_end_not_length`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C15 — Missing local artifact after receiver acceptance

**Setup and ordered stimulus:** Receiver has committed exact batch/artifacts; remove a disposable local copy before replay/ack.
**Required observation:** Replay fails integrity; a matching receipt can still record prior durable acceptance.
**Forbidden outcome:** Replacement download, or refusing acceptance solely because local replay is unavailable.
**Operations:** OP-PREPARE OP-ACK. **Requirements:** INV-02 INV-03 INV-11.
**Evidence / earliest check:** LIVE media and real receiver; INJECTED local removal; Stage 3 / Gate B.
**Status:** PASS (scoped): D photo: durable receiver bytes precede source removal and actual ack-commit exit. Named LOCAL regression: test_30 `test_media_receipt_custody_ack_without_source_bytes_and_health`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C16 — Live pending receipt outlives history policy

**Setup and ordered stimulus:** Keep one batch owed longer than the historical recognition policy; prune only eligible historical metadata.
**Required observation:** Its data/context remain replayable and acknowledgeable.
**Forbidden outcome:** Expiring the live obligation or its ability to settle.
**Operations:** OP-PREPARE OP-ACK. **Requirements:** INV-02 INV-05 INV-10.
**Evidence / earliest check:** LOCAL/INJECTED with actual storage and saved bytes; Stage 3 / Gate B; pruning rechecked C.
**Status:** PASS (scoped): C retention matrix and D controls: prior histories retire/prune without expiring current pending. Named LOCAL regression: test_28 `test_retired_equal_hash_receipt_never_accepts_successor`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C17 — Budget ends after usable prefix

**Setup and ordered stimulus:** Actual bounded reads consume the small test allowance after complete records were prepared.
**Required observation:** Save/deliver the complete prefix; retain budget failure and incomplete source state.
**Forbidden outcome:** Advancing without ack or treating a short interrupted prefix as end.
**Operations:** OP-PREPARE OP-ACK. **Requirements:** INV-02 INV-03 INV-04 INV-06 INV-11.
**Evidence / earliest check:** LIVE with real budget/store/receiver; Stage 3 / Gate B; timing C.
**Status:** PASS (scoped): C actual bounded budget exhaustion; D 100-record locally interrupted prefix with retained charges. Named LOCAL regression: test_29 `test_public_budget_prefix_and_failed_prefix_save_keep_provenance`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C18 — Crash after possible send

**Setup and ordered stimulus:** Kill the reader after source activity is possible but before durable settlement; wait for worker exit.
**Required observation:** Unresolved attempt blocks another read; recovery preserves facts and applies the declared conservative wait.
**Forbidden outcome:** Inferring no send, worker death or accepted output from missing response.
**Operations:** OP-PREPARE OP-RECOVER. **Requirements:** INV-06 INV-07 INV-09 INV-12.
**Evidence / earliest check:** LIVE plus INJECTED subprocess interruption; Stage 5 / Gate C.
**Status:** PASS (scoped): D unknown-source: actual raw return/exit81, confirmed child death then recovery. Named LOCAL regression: test_30 `test_admission_real_commit_exit_pair_never_sends`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C19 — Restart during known wait

**Setup and ordered stimulus:** Persist a known post-attempt deadline; restart and repeatedly inspect/replay.
**Required observation:** Same deadline; no premature source request and no timer extension from observation.
**Forbidden outcome:** Resetting or continually restarting the pause.
**Operations:** OP-PREPARE OP-STATUS. **Requirements:** INV-06 INV-07.
**Evidence / earliest check:** LIVE elapsed timing plus LOCAL injected-clock edges; Stage 5 / Gate C.
**Status:** PASS (scoped): D main-local: restart preserves deadline, decreasing early wait; later real reads >=12s. Named LOCAL regression: test_29 `test_clock_minimum_survives_public_calls_and_close`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C20 — Untrustworthy time evidence

**Setup and ordered stimulus:** Present conflicting/backward time evidence or lack the evidence needed to establish elapsed wait.
**Required observation:** Report uncertain eligibility and no newly authorized read.
**Forbidden outcome:** Inventing readiness or claiming protection against all undetectable clock jumps.
**Operations:** OP-PREPARE OP-RECOVER OP-STATUS. **Requirements:** INV-06 INV-07.
**Evidence / earliest check:** LOCAL; separate from LIVE timing evidence; Stage 5 / Gate C.
**Status:** PASS (scoped): LOCAL UTC/monotonic fault boundaries; trusted UTC after restart remains deployment assumption. Named LOCAL regression: test_27 `test_clock_regression_and_invalid_ns_refuse_without_admission`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C21 — Commit succeeded but response failed

**Setup and ordered stimulus:** Inject failure/exit immediately after actual create/publish/ack/end/control/recovery commit.
**Required observation:** Reload committed outcome; retry without duplicate effect or assumed rollback.
**Forbidden outcome:** Reverting accepted progress or issuing compensating new source work blindly.
**Operations:** OP-START OP-PREPARE OP-ACK OP-CONTROL OP-RECOVER OP-STATUS. **Requirements:** INV-03 INV-05 INV-09.
**Evidence / earliest check:** INJECTED at actual store commits; A create; B publish/ack/end; C controls/recovery.
**Status:** PASS (scoped): All nine test30 commit exit pairs; D actual receiver/source/recovery/ack exits; no power-loss claim. Named LOCAL regression: test_30 `test_cancelled_publication_and_ack_reply_reopen_actual_effect`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C22 — Paused, pending and rate-limited together

**Setup and ordered stimulus:** A saved batch coexists with operator pause and source wait; replay and acknowledge using the correct context.
**Required observation:** Expose all facts; allow local settlement, deny new source admission.
**Forbidden outcome:** Letting one display label erase another restriction or obligation.
**Operations:** OP-PREPARE OP-ACK OP-STATUS OP-CONTROL. **Requirements:** INV-02 INV-03 INV-06 INV-08 INV-11.
**Evidence / earliest check:** LIVE payload plus INJECTED conditions; Stage 6 / Gate C.
**Status:** PASS (scoped): C actual combined paused budget prefix; D independently repeats public pause/delivery/failure boundaries. Named LOCAL regression: test_28 `test_paused_failed_budget_prefix_replays_and_ack_preserves_wait_and_failure`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C23 — Empty and nonempty exhausted scope

**Setup and ordered stimulus:** Use independently known empty scope and nonempty end result; restart before/after final settlement.
**Required observation:** Empty end commits completion without fake upload; nonempty end waits for ack; reopening is local.
**Forbidden outcome:** Equating arbitrary None/error with end, or reading again after completed status.
**Operations:** OP-PREPARE OP-ACK OP-STATUS. **Requirements:** INV-03 INV-04 INV-09.
**Evidence / earliest check:** LIVE oracle with actual storage and crash boundaries; Stage 4 / Gate B.
**Status:** PASS (scoped): D main final partial/ack and photo actual empty end without fake receipt. Named LOCAL regression: test_30 `test_empty_end_real_commit_exit_pair`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C24 — Failure before a usable prefix

**Setup and ordered stimulus:** Refuse or interrupt a source read before any complete record is available.
**Required observation:** No pending/accepted/end evidence invented; preserve failure and known/uncertain attempt state.
**Forbidden outcome:** Returning successful empty completion.
**Operations:** OP-PREPARE OP-STATUS. **Requirements:** INV-03 INV-04 INV-11.
**Evidence / earliest check:** LIVE read with INJECTED local failure; LOCAL source categories; Stage 3 / Gate B; recovery C.
**Status:** PASS (scoped): D photo local pre-send failure: no pending/end/cursor advance; no natural server denial claimed. Named LOCAL regression: test_25 `test_no_prefix_failure_settles_without_end_or_cursor_advance`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C25 — Prefix save also fails

**Setup and ordered stimulus:** A read has a complete prefix and source error; actual persistence then fails.
**Required observation:** Local persistence error keeps original read error separately; no promise of durable prefix; no false Telegram health.
**Forbidden outcome:** Cleanup/storage replacing the original context silently or signaling fake source recovery.
**Operations:** OP-PREPARE. **Requirements:** INV-02 INV-09 INV-11.
**Evidence / earliest check:** INJECTED with real backend; existing local health checks; Stage 3 / Gate B.
**Status:** PASS (scoped): LOCAL public SDK error plus failed real publication, unchanged health during recovery/wait. Named LOCAL regression: test_30 `test_failed_prefix_and_publication_keep_source_provenance_then_recover`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C26 — Admission write failed or uncertain

**Setup and ordered stimulus:** Fail/cancel the attempt-admission write before its success is established, including commit-then-error.
**Required observation:** No source send unless the intended admission is authoritatively reconciled; otherwise recover/stop.
**Forbidden outcome:** Sending because the write probably worked or probably rolled back.
**Operations:** OP-PREPARE OP-RECOVER. **Requirements:** INV-06 INV-09 INV-12.
**Evidence / earliest check:** INJECTED actual backend; count real send boundary; Stage 3 / Gate B.
**Status:** PASS (scoped): D unknown attempt refuses new prepare; LOCAL before/after admission exits send zero. Named LOCAL regression: test_30 `test_admission_real_commit_exit_pair_never_sends`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C27 — Late source result after control mutation

**Setup and ordered stimulus:** Hold an admitted real read result before settlement; commit pause/cancel; then release the result.
**Required observation:** Settle only the same attempt/run/cursor, retain usable output and preserve the newer control.
**Forbidden outcome:** Whole-record stale overwrite, new fetch to repair CAS, or silent discard solely because control changed.
**Operations:** OP-PREPARE OP-CONTROL. **Requirements:** INV-02 INV-05 INV-08 INV-09.
**Evidence / earliest check:** LIVE plus INJECTED await barrier; Stage 6 / Gate C.
**Status:** PASS (scoped): D controls: real result held before publication preserves newer pause; LOCAL late cancellation. Named LOCAL regression: test_30 `test_late_final_result_cancel_order_and_equal_hash_successor`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C28 — Recovery while old reader lives

**Setup and ordered stimulus:** Keep a local read active; request recovery, including a false or wrongly asserted quiescence flag.
**Required observation:** Reject the live local attempt regardless; caller must actually stop/wait for worker before sequential recovery.
**Forbidden outcome:** Treating a timeout or boolean alone as a distributed ownership proof.
**Operations:** OP-RECOVER OP-PREPARE. **Requirements:** INV-06 INV-12.
**Evidence / earliest check:** INJECTED subprocess/local-task control; Stage 5 / Gate C.
**Status:** PASS (scoped): D controls: busy recover/abandon refuse; parent confirms each owned worker exit. Named LOCAL regression: test_29 `test_one_cached_engine_preserves_busy_source_and_late_control`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C29 — Corrupt pending artifact

**Setup and ordered stimulus:** Modify only a disposable saved test blob, then request pending replay.
**Required observation:** Integrity failure with same pending identity/cursor; no source refetch.
**Forbidden outcome:** Accepting changed bytes because filename/path matches.
**Operations:** OP-PREPARE. **Requirements:** INV-02 INV-11.
**Evidence / earliest check:** LIVE media plus INJECTED filesystem fault; Stage 3 / Gate B.
**Status:** PASS (scoped): D photo: corrupt disposable copy refuses unchanged, no refetch or health recovery. Named LOCAL regression: test_30 `test_media_receipt_custody_ack_without_source_bytes_and_health`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C30 — Wrong collection, destination or run receipt

**Setup and ordered stimulus:** Prepare equal payload bytes in different contexts; submit the other context or destination receipt.
**Required observation:** Refuse without clearing current pending or advancing its cursor.
**Forbidden outcome:** Treating a payload hash as collection/destination authority.
**Operations:** OP-ACK. **Requirements:** INV-03 INV-05.
**Evidence / earliest check:** LOCAL/INJECTED with real stored observations; LIVE where equal observations exist; Stage 3 / Gate B.
**Status:** PASS (scoped): B wrong destination/run/collection; D controls same-hash full-scoped receipts; test29 receiver scope. Named LOCAL regression: test_25 `test_wrong_and_unknown_receipts_preserve_pending`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C31 — Duplicate latest ack with newer pending

**Setup and ordered stimulus:** Ack batch one, prepare batch two, then repeat batch one ack; also send an older unrecognized receipt.
**Required observation:** Recognized latest ack is harmless and batch two remains; unknown older receipt refuses.
**Forbidden outcome:** Clearing another pending batch or advancing twice.
**Operations:** OP-ACK OP-STATUS. **Requirements:** INV-02 INV-03 INV-05 INV-10.
**Evidence / earliest check:** Real storage and receiver; LIVE payload; Stage 3 / Gate B.
**Status:** PASS (scoped): B latest same-run duplicate preserves newer pending; D prior-run duplicate preserves successor pending. Named LOCAL regression: test_25 `test_scoped_ack_duplicate_and_zero_pause_continuation`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C32 — Explicit abandonment and successor

**Setup and ordered stimulus:** Cancel with pending data; first attempt abandon while source unresolved, then after quiescence; start a successor.
**Required observation:** Unresolved attempt prevents abandonment/replacement; later explicit abandonment preserves cancelled outcome and cursor, records withdrawal, and permits a scoped successor.
**Forbidden outcome:** Pretending abandoned data was accepted, or letting a late retired receipt affect the successor.
**Operations:** OP-CONTROL OP-START OP-ACK. **Requirements:** INV-03 INV-05 INV-08 INV-10 INV-12.
**Evidence / earliest check:** LOCAL/INJECTED with actual storage; Stage 6 / Gate C.
**Status:** PASS (scoped): D controls: cancel/abandon after quiescence; unchanged cursor, distinct successor. Named LOCAL regression: test_30 `test_abandon_real_commit_exit_pair_retires_receipt`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C33 — Local public operations and health

**Setup and ordered stimulus:** After recorded source health failure, invoke status/control/ack/replay or cause local storage failure.
**Required observation:** No Telegram calls attributable to those local operations; no fabricated health verdict or recovery.
**Forbidden outcome:** Treating local success/failure as fresh Telegram evidence.
**Operations:** OP-STATUS OP-CONTROL OP-ACK OP-PREPARE OP-RECOVER OP-START. **Requirements:** INV-11.
**Evidence / earliest check:** LOCAL call counters; LIVE attributed trace at D; Stage 7 / Gate D; affected local checks earlier.
**Status:** PASS (scoped): D all socket/config-blocked local workers and operation-tagged live RPC traces; injected fixture labeled. Named LOCAL regression: test_29 `test_local_operations_preserve_prior_health_and_make_no_calls`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C34 — Legacy compatibility and separate collections

**Setup and ordered stimulus:** Run existing daily/window APIs/state and batch v1 alongside lifecycle code; schedule readers sequentially.
**Required observation:** Unchanged legacy behavior and independent progress; wrong record kinds refuse.
**Forbidden outcome:** Silently migrating daily data or advancing another collection.
**Operations:** OP-START OP-PREPARE OP-ACK OP-STATUS. **Requirements:** INV-01 INV-03 INV-09.
**Evidence / earliest check:** LOCAL regressions plus LIVE sequential integration; On any shared edit; Stage 7 / Gate D.
**Status:** PASS (scoped): 357 actual supported offline passes; D main daily/history state and receiver integration. Named LOCAL regression: test_29 `test_daily_and_backfill_progress_are_separate_and_no_auto_namespace_exists`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C35 — Delayed prepare after acknowledgment

**Setup and ordered stimulus:** Save an old PrepareContext, acknowledge its earlier batch, then deliver that old prepare call again.
**Required observation:** Stale accepted-position conflict before a source send; current state unchanged.
**Forbidden outcome:** Turning the old call into fetch-next at the new cursor.
**Operations:** OP-PREPARE OP-ACK. **Requirements:** INV-05 INV-06.
**Evidence / earliest check:** LOCAL/INJECTED actual lifecycle state; LIVE request attribution; Stage 3 / Gate B.
**Status:** PASS (scoped): D main-local explicitly refuses original pre-ack prepare context without source. Named LOCAL regression: test_25 `test_scoped_ack_duplicate_and_zero_pause_continuation`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C36 — Delayed prepare after pause/resume

**Setup and ordered stimulus:** Save a PrepareContext, change control revision through pause/resume, then submit the old context.
**Required observation:** Stale control conflict before source admission; caller must obtain current context deliberately.
**Forbidden outcome:** Automatically using the newer operator permission.
**Operations:** OP-PREPARE OP-CONTROL. **Requirements:** INV-05 INV-06 INV-08.
**Evidence / earliest check:** INJECTED barriers with actual state; LIVE turns; Stage 6 / Gate C.
**Status:** PASS (scoped): D controls stale prepare after accepted controls refuses with unchanged pending. Named LOCAL regression: test_30 `test_opposing_controls_and_delayed_resume_are_revision_ordered`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C37 — Absent slot is not unknown retry permission

**Setup and ordered stimulus:** Compare an affirmative new first-use submission with the same request submitted as retry when absent; also test missing known state.
**Required observation:** Only explicit new first use may create under its preconditions; unknown retry and failed known-run restore refuse.
**Forbidden outcome:** Inferring new intent from absence or hiding total-history loss.
**Operations:** OP-START OP-STATUS. **Requirements:** INV-01 INV-05 INV-09.
**Evidence / earliest check:** LOCAL real backend; Stage 2 / Gate A.
**Status:** PASS (scoped): LOCAL public absent slot: retry/status refuse; test30 before-creation exit retains absence. Named LOCAL regression: test_29 `test_unknown_start_and_run_never_bootstrap`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C38 — Intentional retry after settled failure

**Setup and ordered stimulus:** A source attempt failed and settled with unchanged accepted position/no pending; call prepare with current context before and after eligibility.
**Required observation:** Before deadline no send; after eligibility one new admitted attempt is allowed. Unresolved work still refuses.
**Forbidden outcome:** Promising indefinite old-prepare replay or treating every repeated call as free source work.
**Operations:** OP-PREPARE OP-RECOVER. **Requirements:** INV-06 INV-07 INV-12.
**Evidence / earliest check:** LIVE failure injection plus LOCAL timing cases; Stage 5 / Gate C.
**Status:** PASS (scoped): C real allowance recheck; D photo explicit later retry after failed follow-up and actual >=12s wait. Named LOCAL regression: test_30 `test_failed_prefix_and_publication_keep_source_provenance_then_recover`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C39 — Recovery reply lost

**Setup and ordered stimulus:** Recover a quiescent unknown attempt; lose the committed recovery reply; repeat the same command after restart.
**Required observation:** Recognize/reconcile the same effect and deadline without another quiet interval or source read.
**Forbidden outcome:** Resetting the wait each time or recovering a different current attempt.
**Operations:** OP-RECOVER OP-STATUS. **Requirements:** INV-05 INV-07 INV-09 INV-12.
**Evidence / earliest check:** INJECTED actual store/process boundary; Stage 5 / Gate C.
**Status:** PASS (scoped): D recovery commit exit82 then exact retry/deadline; next real read >=12s. Named LOCAL regression: test_30 `test_recovery_real_commit_exit_pair_preserves_original_command`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C40 — Missing independent oracle or source drift

**Setup and ordered stimulus:** Fixture contains only sampled IDs, is derived from the tested reader, lacks a critical case, or changes during measurement.
**Required observation:** Gate is BLOCKED/INCONCLUSIVE or FAIL as appropriate; preserve differences and stop dependent work.
**Forbidden outcome:** Retrospectively changing expected results, seeding Telegram messages, or passing synthetic-only live coverage.
**Operations:** VALIDATION. **Requirements:** INV-04 INV-11.
**Evidence / earliest check:** LIVE independent existing-history evidence; Fixture qualification / Gate A; recheck every gate.
**Status:** PASS (scoped): A rejected non-group/undersized fixture; D direct qualified sets frozen before reads, unchanged counts; drift guard retained. Named LOCAL regression: test_24 `test_window_and_clock_failures_are_local`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C41 — Real SDK and caller pagination

**Setup and ordered stimulus:** Use existing history with an independently complete interval crossing an actual SDK history page and multiple caller batches, including available ties/gaps.
**Required observation:** Recorded request/page trace and accepted union match expected visible IDs exactly within scope.
**Forbidden outcome:** Counting repeated small first pages as an SDK boundary test or using the same reader as the sole oracle.
**Operations:** OP-START OP-PREPARE. **Requirements:** INV-01 INV-04 INV-11.
**Evidence / earliest check:** LIVE, existing group, read-only; Gate A foundation; Gate B/D new API.
**Status:** PASS (scoped): D 250 exact records in120/120/10; actual second SDK pages; source differs from independent descending oracle. Named LOCAL regression: test_25 `test_short_slice_is_not_itself_source_exhaustion`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C42 — Exact date selection and media mode

**Setup and ordered stimulus:** Select existing boundary messages and media independently; read fresh/imported windows and reference/download modes.
**Required observation:** Start-inclusive/end-exclusive selection; media only for included messages; required hashes verified. Missing critical live media/boundary cases remain unverified.
**Forbidden outcome:** Claiming unseen cases passed, downloading excluded media, or creating fixture messages.
**Operations:** OP-START OP-PREPARE. **Requirements:** INV-01 INV-02 INV-04 INV-11.
**Evidence / earliest check:** LIVE plus separate LOCAL malformed/bounds cases; Gate A foundation; B/D composition.
**Status:** PASS (scoped): A/B full boundary matrix; D fresh/imported closed scopes and independent real photo digest. Named LOCAL regression: test_25 `test_fresh_relative_query_uses_original_window_after_clock_moves`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C43 — Invalid or incompatible saved state

**Setup and ordered stimulus:** Load wrong kind/version, duplicate/missing fields, contradictory cursor/receipt state or malformed dates.
**Required observation:** Local validation/storage refusal without repair, source traffic or new enrollment.
**Forbidden outcome:** Interpreting lifecycle as daily state or guessing unknown fields.
**Operations:** OP-START OP-PREPARE OP-STATUS OP-ACK OP-CONTROL OP-RECOVER. **Requirements:** INV-01 INV-09 INV-11.
**Evidence / earliest check:** LOCAL real backend with injected corrupt records; Stage 2 / Gate A; public regression D.
**Status:** PASS (scoped): Strict codec suites plus test30 public malformed/missing state; no bootstrap or repair. Named LOCAL regression: test_24 `test_malformed_outer_and_request_refused`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

## C44 — Input, scope and identity normalization

**Setup and ordered stimulus:** Exercise accepted timezone normalization/ID bounds and reject booleans, invalid tokens, naive/mixed dates, future end, invalid origin/media/pacing and counter wrap.
**Required observation:** Valid equivalent normalized inputs retain identity; invalid/conflicting inputs produce no lifecycle/source effect.
**Forbidden outcome:** Using a different input form to reset an accepted intent or losing precision in identifiers.
**Operations:** OP-START OP-PREPARE OP-ACK OP-CONTROL OP-RECOVER OP-STATUS. **Requirements:** INV-01 INV-05 INV-09.
**Evidence / earliest check:** LOCAL; valid saved query also checked LIVE at A; Stage 2 / Gate A; later operations as implemented.
**Status:** PASS (scoped): Strict input/counter/codec suites plus test29 typed public exports/required args/bad address refusal. Named LOCAL regression: test_24 `test_input_and_portable_identity`; see [Stage 8 case map](stage-8-validation/coverage-map.md).

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
