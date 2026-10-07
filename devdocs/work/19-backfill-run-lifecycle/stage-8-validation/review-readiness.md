---
model: gpt-6-astra
effort: max
status: ready-for-formal-review
---
# Whole-feature traceability and review readiness

**Ready for the separately requested formal review gates.** Stages 1–8 and Gates A–D
are complete in the selected composition. This audit is not CONTRIBUTING's formal
merge-check or fresh implemented-diff PR critic; no PR/merge approval is implied.

The source is the two-pass lifecycle finding at local `d1f37f7`,
`devdocs/inquiries/2026-10-06_17-56__backfill-run-lifecycle/finding.md`, adopted by
[Stage 1 source/description](../stage-1-contract/source-input.md). It asks for a durable
historical obligation, exact pending custody, acknowledgment-owned progress, qualified
completion, attempt pacing, accepted control order and explicit stopped-worker recovery.
It excludes scheduling, account routing, competing readers and edit/deletion reconciliation.

## Full diff scope

Reviewed base `45bab7172621f576fa5e4b3265f87ec20da04fd5` through product `405218e`:
27 product files, 9,591 insertions/24 deletions before the final documentation refresh.
The feature includes intentionally integrated #18 daily/fixed-window prerequisites
through `e9b5154` (feature-only merge `5d0789e`). It is larger than Stage 8's own diff;
the review must include both foundations and lifecycle behavior.

| Product area | Reason and correspondence |
|---|---|
| `sync_store.py`, `sync_engine.py`, daily example/docs | Existing #18 durable pending/acknowledged cursor and real opaque-text SQLite load/CAS foundation. Explicit provisioning and namespace separation remain. |
| `history_window.py`, `batch_engine.py`, fixed-window/batch docs | Existing #18 fixed UTC half-open windows; actual SDK seeks, lower-bound filtering, bounded ascending records and explicit end/limit/interrupted semantics. Unwindowed legacy calls retain their signatures/behavior. |
| `backfill.py`, `backfill_state.py` | Typed immutable identities/contexts/results and strict version1 aggregate. Canonical integer strings, exact scope and bounded current/previous recognition. No state migration added in later stages. |
| `backfill_engine.py` | One aggregate owns creation, durable admission, exact publication, acceptance, exhaustion, pacing, controls and recovery. Source reads occur only after confirmed admission; no uncertain-write repair refetch. |
| `tgdata.py`, `__init__.py` | Additive `sync_store`/`backfill_store` and six backfill operations. Cached engine lifetime preserves busy guards and monotonic minima. Local calls do not acquire the raw reader's health context. Collection names validate identity; they do not route backends. |
| `examples/backfill_runs.py`, README/public docs | Actual SQLite namespace/receiver example, full snapshots per scoped receipt, explicit durability/clock/worker responsibility, source-free restart. Example remains reference-only; Gate D separately proves download byte custody. |
| tests22–30 and smoke documentation | Exact component and public histories with real SQLite/SDK plus synthetic transport. All relevant legacy suites rerun. Actual Telegram proof is separately gated, not inferred from mocks. |

No changes to the account-health storage architecture, connection/account-routing code,
ScrapeOps, duncan, package version or release configuration. The unrelated paused #7
and #18 original worktree files stay untouched. Stage 8 changed no runtime behavior.

## Invariant and finding disposition

| Contract invariant / original finding | Implementation boundary | Named evidence |
|---|---|---|
| INV-01 fixed obligation, origin, query and policy | `start`, exact request recognition, closed `_HistoryWindow`, codec | C01–C05/C12–C13/C37; test24 relative forbidden-clock retry; D original-request reopen and independent daily/history origins |
| INV-02 exact pending custody | confirmed admission then `_settle`; local replay/media verification | C15–C17/C22/C25/C29; D exact receiver/restart/photo/prefix |
| INV-03 only acceptance advances | scoped `acknowledge` atomically records saved next cursor | C09–C11/C15/C21/C30–C32; test30 actual receiver before both ack commit exits; D photo ack without source bytes |
| INV-04 truthful finite completion | separate exhaustion; `_complete_if_fulfilled`; first terminal outcome | C09–C14/C23–C24; D full photo then refused follow-up remains incomplete; actual later empty end |
| INV-05 exact authority | RunRef/generation/destination/hash plus original control/prepare context | C03–C08/C16/C30–C32/C35–C39; D equal-hash generations, pruned/retired refusal and delayed controls |
| INV-06 current read permission | durable `_admit`, busy guard, stale context refusal and actual SDK budget | C17–C18/C22/C26–C28/C35–C38; test30 admission exits send zero; D explicit refused overlap and unknown recovery |
| INV-07 persistent attempt spacing | `_ended`, saved UTC with local monotonic minima; exact recovery | C18–C22/C38–C39; test27 clock edges; D four measured waits >=12s without host-clock changes |
| INV-08 accepted control order | revision-checked CAS and result attribution | C06–C11/C27/C32/C36; D opposing actual CAS, newer pause survives late source/resume |
| INV-09 atomic durable facts | strict aggregate/exact load-CAS; one bounded exact-candidate readback | C01/C05/C21/C25–C26/C43; test30 nine real before/after commit pairs; selected SQLite process evidence only |
| INV-10 retain owed work while history is bounded | current pending cannot be pruned/replaced; explicit quiescent abandonment | C03–C04/C16/C31–C32; D current pending survives old-history pruning; abandon keeps cancellation and cursor |
| INV-11 evidence boundaries | local errors/content-free status; raw reader owns health; external acceptance assertion | C15/C20/C24–C25/C29/C33–C34/C40–C44; D injected health clearly labeled, no local RPC/recovery, actual selected oracle |
| INV-12 single-reader recovery | active local guard plus required external stopped-reader assertion | C18/C27–C28/C39; D parent-confirmed exits and busy refusal; no distributed lease claimed |

All 44 cases have individual named evidence in [coverage-map.md](coverage-map.md) and
the reconciled [acceptance matrix](../acceptance-matrix.md). Case ranges above only map
invariants; they do not replace those per-case results. Twelve assumptions have explicit
observed/tested versus external dispositions in [assumptions.md](../assumptions.md).

## Every selected critic remedy

| Stage | Selected remedy / experiment | Final disposition |
|---|---|---|
| 1 | Unknown creation retries must not become new intent; stale prepare must not become another read | Explicit `submission`/predecessor and expected cursor/control; C01–C04/C35–C37 pass. |
| 2 | Missing known store must not bootstrap; positive minimum duration must not round down | Existing-only SQLite `mode=rw`; upward microsecond rounding; test24 and missing-state/process public tests pass. |
| 3 | No content mitigation; real primitive experiment first | Required actual store/SDK/codec probe PASS before build; delivery suite and Gates B/D add composition. |
| 4 | No content mitigation; real delivery prebuild first | Actual source/store/receiver premise PASS before completion changes; exact readback/final-boundary suite and Gates B/D pass. |
| 5 | No content mitigation; real clock/recovery primitives first | Probe PASS; independent clocks, original-command recovery and copied-state checks; Gates C/D add actual elapsed/owned exits. |
| 6 | Restrictive test-budget adapter must implement actual interface; whole gate needs durable allocations | Adapter prebuild PASS with both real ledgers, Gate C quota exhaustion; D retains nonrefundable per-launch allocation and shared policy. No product-budget redesign. |
| 7 | Receipt marker must retain every accepted observation | Full canonical snapshot per scoped receipt plus separate message index; actual receiver fault/restart probe PASS; D adds verified download bytes before that transaction. |
| 8 | No content mitigation; actual public byte/snapshot receiver composition first | Real 250-slot prebuild allocation passed before Step 1; no product change needed. Complete Gate D and independent audit PASS. |

The eight scoped desc/plan/critic/fold/implementation/verification chains are the
authoritative preparation record. Stages3–8 each ran their required prebuild experiment
before implementation; Stage 1/2 had no affordable live prerequisite then, and Gate A
blocked advancement until the user-selected fixture actually qualified. No aggregate
checkbox implies that a separate monolithic `plan.md` or critic was produced.

## Deviations, corrections and remaining review

- Stage 3 needed minimal completion closure to produce states the existing codec could
  accept; Stage 4 then owned its dedicated exact-write/final-boundary implementation and
  validation. This is documented in those stage handoffs, not an unexamined later patch.
- Every checkpoint distinguishes LOCAL synthetic-source results from actual LIVE
  composition. Earlier Gate B's allowed controlled-failure alternative did not claim
  actual quota exhaustion; Gate C subsequently ran it with real ledgers/source.
- Stage 8 added 15 public groups instead of mirroring every prior unit case; all 44 cases
  still have named existing/new evidence and all seven mandatory D compositions ran.
- One new audit filter mistakenly treated normal file-DC migration as a history error.
  Its local call-scope correction and exact retained evidence are recorded; no runtime,
  expected message set, policy or lifecycle behavior changed.
- Timing-sensitive public docs are refreshed only after Gate D actually passed, in
  documentation-only commit `1d0f7a9` after tested `405218e`. This does
  not invalidate its runtime receipt; tests/docs and work evidence remain separate.

No unexplained substantive finding remains in this readiness audit. The model/effort
record is gpt-6-astra/max in the same warmed session; CONTRIBUTING §9 verification
must still be explicitly recorded at the formal merge gate. Do not equate this document
with that gate or the fresh PR critic. Keep the branch/archive; no protected branch merge,
issue closure or release is part of Stage 8.

For operational adoption, the integrator still chooses durable destination acceptance,
appropriate CAS/backend guarantees, reliable UTC across restart and actual worker
exclusion. Completion is the selected visible fixed scope, not the full historical
Telegram archive. Account-wide rest, distributed competition, automatic routing and
edit/deletion reconciliation stay outside the contract.
