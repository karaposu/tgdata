---
model: gpt-6-astra
effort: max
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the existing internal prepare/ack path cannot preserve a real selected
observation and its media through SQLite reopen and durable receiver acceptance,
or actual post-commit read-back cannot recover identical candidate state.
Affordable now: yes — one small authorized live fixture and local SQLite/files,
under five minutes, charged to the existing ledger and Stage 4 request cap.

Experiment: before Step 1, run a scoped prebuild probe on the unchanged Stage 3
engine. Independently enumerate the approved small group's current visible history
with direct descending RPCs and hash the selected photo via direct SDK bytes; freeze
the fixture. Prepare that one-photo historical window with the actual engine/raw
reader and isolated SQLite store, reopen offline, commit its exact batch/artifact to
a real SQLite receiver, acknowledge, and reopen completed status. Separately force
actual SQLite close errors after empty completion and final acknowledgment, then
reopen and compare committed snapshots/receipts. The existing engine is expected to
raise its current storage error; this tests persistence, not the unbuilt confirmer.
Cost: <=250 requested history slots, <=4MiB requested media, one source session,
external spacing >=5 seconds, existing 5,000-read account policy unchanged.
Must precede: step 1 — write confirmation and its new claims.
Disqualifying result: source fixture contradicts saved query/end assumptions; real
pending/artifact/receiver custody is lost; accepted output is not durably complete;
or actual committed state cannot be loaded identically. Preserve evidence, stop and
revisit the premise. Auth/budget outage is an execution block, not a contrary result.
Passing result: independent IDs/date/photo hash match the prepared observation;
exact replay is local; actual durable receiver acceptance precedes ack; completion
survives reopen; real post-commit failures leave the expected state readable.

## High-Level Summary

The plan stays within the established contract and uses a conservative confirmation
rule. No additional High/Medium/Low content finding remains unhandled. Its current
ordering postpones an affordable check of the existing live delivery composition and
final SQLite boundary until after the change. Test that first. Full Gate B still runs
on the final product; this one-case probe is not a substitute or a premature gate PASS.

Review ran in the warmed primary session. No OPEN planning blocker or currently open
execution blocker is inherited. The authorized live inputs must be rechecked, without
resetting their account allowance. Controls and positive recovery/timing remain later work.

## Premise Inventory — ranked by waste if false

### P1 — Actual prepared source data can cross these custody boundaries

- Premise: the current internal engine's frozen query, pending observation, media and
  scoped acknowledgment compose with an actual durable receiver on the approved source.
- First dependent step: 1; confirmation presupposes those existing transitions.
- Waste if false: Steps 1–3 would certify local changes atop a faulty composition.
- Test scheduled at: Steps 4–5 / Gate B.
- Cheapest earlier test: the one-photo experiment above, using current runnable engine.
- Coverage: Gate A proved raw selection/media foundations; Stage 3's actual SQLite/SDK
  tests used synthetic transport. Those do not cover real-source delivery composition.
  Receiver fixtures that merely return accepted are non-covering; real transactions are required.

### P2 — Lost/error replies can be resolved by identical authoritative state

- Premise: actual durable SQLite commits can survive subsequent close/reply errors,
  and reading back the full aggregate observes those facts without another write.
- First dependent step: 1.
- Waste if false: the new confirmer would need a different backend contract.
- Test scheduled at: Step 2.
- Cheapest earlier test: force real post-commit close failure for empty completion and
  final ack using existing engine, reopen through actual SQLiteSyncStore; seconds offline.
- Coverage: Stage 2 creation and Stage 3 publication already reproduced this mechanism.
  The new final-effect cases are cheap enough to include before building. Mocked return
  values alone would not establish durability. No power-loss guarantee is inferred.

### P3 — The proposed implementation preserves each deliberate refusal

- Premise: bounded confirmation leaves false CAS, ambiguous admission, cancellation,
  incompatible/newer snapshots, errors and receipt scope fail-closed.
- First dependent step: 1; this is the behavior being built, not an external premise.
- Waste if false: implementation must be corrected/replanned before Gate B.
- Test scheduled at: Step 2, before later work.
- Cheapest earlier test: no probe can execute the not-yet-existing helper; full reading
  confirms that `_load`, `_BackfillState`, `_backend` and operation-specific paths can
  implement it without a schema change. A hand-coded substitute would supply behavior.
- Coverage: existing cancellation/identity/fault tests; intentionally changed post-commit
  return behavior needs new assertions, while negatives remain intact.

### P4 — Current source view and account capacity are sufficient for Gate B

- Premise: the two already approved existing groups and selected session/ledger still
  support the required bounded fixture, including a useful interrupted prefix.
- First dependent step: 4 (the small critical composition is brought before 1 by P1).
- Waste if false: Gate B cannot pass; no Stage 5 implementation may proceed.
- Test scheduled at: qualification in Step 4, before tested full scans.
- Cheapest earlier test: include small-source visibility and budget status in prebuild;
  larger interval qualification belongs before its specific case. No synthetic substitute.
- Coverage: historical Gate A, not an immutable claim about today's Telegram view.

## Restart Check

| Observed prior failure | Established mechanism | Design element that addresses it |
|---|---|---|
| SQLite operation errored after a real commit | close failure after transaction commit, reproduced by prior suites | Exact candidate read-back, prebuild and Step 2 real boundaries |
| Local failures/cancellation inherited Telegram health | implicit exception context under an RPC failure | Explicit from-None boundaries, preserved read_error, Step 2 classifier checks |
| Short synthetic slice incorrectly treated as a finite fixture | actual Telethon requires further reply; fixture was corrected, runtime stayed intact | Only validated stop_reason, full-follow-up and interrupted-prefix checks |
| Live SDK connect exceeded the scoped source guard | account-wide GetDifference despite receive_updates=False | Retain the tested startup hook/guard; do not widen permission |

## Inherited Lessons and ordering

| Lesson | Satisfied by |
|---|---|
| Error is not rollback | Prebuild actual commit failure; Step 1 never blindly rewrites |
| Source end is not receiver acceptance | Existing atomic closure retained; Step 2 final pending/ack matrix |
| Hash is not run authority | Full aggregate equality and existing scoped receipt checks in Steps 1–2 |
| Local work is not Telegram health evidence | Step 1 keeps error boundaries; Step 2 source-prefix causality assertions |
| More synthetic testing does not establish source behavior | Real one-case probe before Step 1; full Gate B after product verification |
| Unknown attempts cannot be reset to complete a gate | Admission stays conservative; Gate B keeps stuck records for Stage 5 recovery |

## Risk Review

No additional severity item is warranted. Exact snapshot equality is deliberately
stronger than semantic partial-effect recognition: moved-on state can leave an
exception even where a retained receipt later proves the effect. The plan explicitly
states this limitation and provides existing status/retry paths. It never labels a
nonmatch uncommitted or returns the stale candidate as current. One extra bounded
load/validation on ordinary ambiguity is proportional to the existing pending state;
there is no retry loop or widened backend protocol.

Completion has one shared predicate and the codec cross-checks all required facts.
The dedicated tests target actual final transitions and process exits. Controls are
seeded preservation fixtures only; full controls/recovery remain gated. The existing
receiver assertion remains external and the test receiver actually owns bytes before
commit. No unsupported exactly-once, distributed or power-loss claim is introduced.

## Phase 3 — Proposal Selection

No High/Medium proposal requires selection, so no boxes are fabricated. The common
create/publication/ack CAS-reply seam is already one genuine class served by the small
helper; the plan excludes admission by explicit policy and does not couple unrelated
daily APIs. Larger journals/operation logs have no justification here. The only required
fold is sequencing the affordable experiment before Step 1; no content mitigation added.
