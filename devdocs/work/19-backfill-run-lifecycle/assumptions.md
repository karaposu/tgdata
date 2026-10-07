---
model: gpt-6-astra
effort: max
status: stage-6-gate-c-evidence
---
# Backfill assumptions and evidence register

This register belongs to [the contract](contract.md). A selected policy is not an
empirically proved property, and an existing component receipt is not evidence that
the new lifecycle works. Stage 1 supplied the specifications. Stage 2 now has scoped
local evidence at `1425fd7`, recorded in [verification](stage-2-state/verification.md).
[Gate A passed](validation/gate-a.md) with scoped live evidence on 2026-10-07.
[Case IDs](acceptance-matrix.md) retain unverified portions of every later composite case.
Stage 3 adds [local delivery evidence](stage-3-delivery/verification.md) at `3140dcd`;
it did not replace the mandatory live Gate B. Stage 4 adds [completion verification](stage-4-completion/verification.md)
at `b1f6495`, and [Gate B passed](validation/gate-b.md) with the actual new engine,
selected real source and local durable receiver. Later/deployment claims remain scoped below.

Stage 5 adds [local timing/recovery evidence](stage-5-pacing-recovery/verification.md)
at `a180151`: 32 new groups and 287 actual supported offline passes. Actual recovery
of copied LIVE-origin records remains LOCAL. Stage 6 adds 32 actual control groups
(319 total supported offline passes), and [Gate C passed](validation/gate-c.md) with
real elapsed/source/control evidence at `0d6bb26`. Earlier local evidence is not
relabeled as live. Public/deployment integration remains for Stage 7–8/Gate D.

## Status vocabulary

- `SELECTED`: a normative scope/policy decision, not an observed implementation.
- `OBSERVED-COMPONENT`: a specific existing component was exercised at a named revision;
  it says nothing about an untested composition or deployment.
- `OBSERVED-LOCAL`: actual scoped runtime code was exercised offline within the stated scope;
  it is not live-source, future-operation or deployment evidence.
- `OBSERVED-LIVE`: actual Telegram/SDK behavior in the named account/view/window and
  composition; it is not evidence for unimplemented operations or arbitrary deployments.
- `SOURCE-CONFIRMED`: source/format fact checked against the named code.
- `UNVERIFIED`: behavioral premise awaiting the specified evidence.
- `UNSET`: a required external input has not been supplied/verified.
- `CONTRADICTED`: a recorded observation violates the premise; stop dependent work.

Each status below applies only to its stated evidence scope. Gate reports must state
the actual test revision. Later changes to the source, backend, receiver, fixture,
identity context or timing policy can invalidate earlier evidence and reopen its gate.

## Selected policies

| ID | Policy and authority | Contract | What would reopen it |
|---|---|---|---|
| POL-01 | Single active source reader; caller schedules/accounts/uploads — user scope and adopted finding | INV-06, INV-12 | Explicit request for competing readers or orchestration |
| POL-02 | Closed historical windows and explicit imported origin — adopted finding/plan | INV-01, INV-04 | Explicit future-ended-query scope change |
| POL-03 | Post-attempt quiet interval; caller supplies the number — adopted finding/plan | INV-07 | Explicit different pacing policy, not a default change on restart |
| POL-04 | Pause reading, terminal cancellation, explicit abandonment — adopted finding | INV-03, INV-08 | Explicit contract change with all affected traces reviewed |
| POL-05 | Existing group, read-only live tests — direct user answer | INV-11 and validation scope | New explicit user instruction; absence of a fixture is not one |
| POL-06 | Bounded historical recognition, live obligations retained — finding and selected critique fixes | INV-05, INV-10 | Need for a longer declared retry horizon or generalized service |

All six are SELECTED for this specification. None is a runtime PASS. Edits/deletions
remain excluded, as previously directed; this is not a deferred implementation step.

## A01 — Real history selection and canonical group identity

**Premise:** the selected account/group supports the declared ID/date scan, including
canonical identity, ordering, real SDK pagination, boundary inclusion and end signals.
**Kind/status:** OBSERVED-LIVE within Gate A's two selected existing groups/intervals:
350-record real SDK pagination, dates, ties/gaps, empty/full/end and imported scope.
Other account/view/SDK conditions require equivalent evidence.
**Evidence now:** BatchEngine/_HistoryWindow at #18 e9b5154 and prior fixed-window
verification; replies there are synthetic. Batch v1's explicit identity is source-confirmed.
The later [Gate A report](validation/gate-a.md) adds actual independently expected
source comparisons, real SDK page traces and the selected photo hash.
**Falsifier:** independently recorded visible IDs within the frozen scope are omitted,
extra records appear, the source identity changes, or exhaustion contradicts the oracle.
**Cheapest earlier check:** existing raw reader on a selected, independently enumerated
bounded interval; actual SDK and caller page boundaries. No lifecycle facade needed.
**First dependent stage / earliest gate:** Stage 3 new source/delivery behavior; Gate A
immediately after Stage 2, with basic characterization sooner if resources exist.
**Owner:** implementer runs; caller identifies account/group and independent oracle.
**Coverage:** C12, C13, C14, C23, C41, C42; INV-01, INV-04, INV-05, INV-11.
**Waste if false:** reconsider the reader/window contract before runtime Stages 3–8.

## A02 — Conditional durable storage is sufficient for a lifecycle aggregate

**Premise:** a selected backend's exact conditional replacement commits the whole
record durably, and lost/failed replies can be reconciled by loading it.
**Kind/status:** OBSERVED-LOCAL through Stage 4's exact read-back/final-boundary matrix
at `b1f6495`; Gate B adds actual live-data publication, empty completion and final-ack
process exits/reopen. Power-loss behavior and other deployment backends remain UNVERIFIED.
**Evidence now:** test_24 at `1425fd7` exercises exact CAS, actual process exits before/
after commit, successful commit followed by cleanup error, reopen and unchanged retry.
It also refuses missing/schema-less existing-only stores. The earlier #18 component
receipts remain in [critic.md](stage-1-contract/critic.md).
**Falsifier:** mismatched expected text writes, partial state appears after restart,
or a acknowledged durable transition disappears under the stated storage guarantees.
**Cheapest earlier check:** real SQLite process exits before/after actual commit and
stale CAS; test the chosen deployment adapter equivalently rather than a memory stand-in.
**First dependent stage / earliest gate:** Stage 2 record implementation; component
probe already precedes it, new-record persistence must pass Stage 2/Gate A.
**Owner:** implementer/backend provider. **Coverage:** C01, C05, C21, C26, C43;
INV-01, INV-09. **Waste if false:** revise storage boundary before delivery/control code.

## A03 — Frozen enrollment does not recalculate its intent on retry

**Premise:** immutable input recognition and saved boundaries preserve one run;
absence/pruning cannot turn an unknown retry into new intent.
**Kind/status:** OBSERVED-LOCAL for internal Stage 2 start/retry/status and OBSERVED-LIVE
for saved-query reuse after process restart at Gate A. Gate C adds actual produced
successors, retained/pruned creation recognition and equal-hash receipt isolation.
**Evidence now:** test_24 at `1425fd7` preserves dates and identity across reopen, lost
reply and a forbidden retry clock; changed requests conflict and unknown retries refuse.
Earlier successor/pruned checks used seeded terminal snapshots. Stage 6/Gate C now
produce those histories through actual controls, receiver acceptance and succession.
**Falsifier:** retry observes a new clock, accepts changed settings, silently resets
missing known state or creates from an unrecognized recovery request.
**Cheapest earlier check:** Stage 2 start/reopen with actual storage and forbidden clock
on recognized retry; before/after-commit failure injection, then live query reuse at A.
**First dependent stage / earliest gate:** Stage 2; Gate A before Stage 3.
**Owner:** implementer. **Coverage:** C01–C05, C37, C44; INV-01, INV-05, INV-09.
**Waste if false:** revise creation/recognition before later commands inherit its meaning.

## A04 — Exact observation and media custody support replay

**Premise:** the complete pending value and required bytes stay available until accepted
or explicitly abandoned; replay never silently substitutes a fresh observation.
**Kind/status:** OBSERVED-LOCAL and OBSERVED-LIVE at Gate B for exact pending/media
custody, real receiver commitment, process restart, relocation/corruption/removal and
ack without local source copies. Production deployment durability remains UNVERIFIED.
**Stage 3 evidence:** OBSERVED-LOCAL exact pending replay, relocation, missing/corrupt/
symlink refusal and valid acknowledgment after media removal; actual new-engine live
payload custody is now observed at B; deployment durability remains for D/adoption.
**Falsifier:** replay changes data/ref, re-contacts Telegram, loses pending after an
error, or treats a missing/corrupt artifact as permission to read on.
**Cheapest earlier check:** retain an actual prepared batch, restart and verify payload/
artifact hashes; remove/corrupt only disposable test copies and inspect unchanged state.
**First dependent stage / earliest gate:** Stage 3; Gate B.
**Owner:** implementer; caller supplies durable/relocatable artifact storage.
**Coverage:** C15, C16, C17, C22, C25, C29, C30, C31; INV-02, INV-03, INV-10, INV-11.
**Waste if false:** revise custody before completion, pacing and retirement rely on it.

## A05 — The destination's acceptance is durable and repeat-safe

**Premise:** acknowledgment attests committed receiver data/artifacts; repeated batches
and overlapping collections do not repeat the caller's irreversible processing effects.
**Kind/status:** OBSERVED-LIVE with INJECTED local boundaries for the Gate B test
receiver: durable SQLite receipt/message transaction after verified/fsynced media custody.
Duplicate delivery and overlapping collections produced no repeated record effect.
Production receiver remains UNSET/UNVERIFIED; a library receipt cannot verify the caller's
assertion or establish a distributed transaction.
**Evidence now:** prior local example/test exists; it is not the selected receiver.
Stage 3 additionally exercised an actual SQLite receiver transaction and lost local
reply against the new delivery references. This proves that test composition only.
**Falsifier:** acknowledged data is absent after receiver restart, or lost replies/
overlap produce duplicate destination effects.
**Cheapest earlier check:** actual local durable receiver at Gate B; actual selected
integration/backend before Gate D/adoption. Inspect commit point before choosing ack.
**First dependent stage / earliest gate:** Stage 3 delivery semantics; Gate B and D.
**Owner:** application integrator, with implementer observing the chosen test receiver.
**Coverage:** C09–C11, C15–C17, C21–C23, C30–C32; INV-03, INV-04, INV-05, INV-11.
**Waste if false:** fix receiver contract before calling progress accepted or complete.

## A06 — The composed source attempt has an observable local outcome

**Premise:** raw reads/SDK retries, disconnect and cancellation can be distinguished
from admission and durable result settlement sufficiently to enforce this contract.
**Kind/status:** OBSERVED-LIVE with local injection for the raw read at Gate A;
OBSERVED-LOCAL for the new durable admission/settlement and cancellation boundaries
in Stage 3, plus actual live new-engine attempts/settlement at Gate B, including a
100-record interrupted prefix and preserved unresolved post-answer crash. Explicit
recovery and timing have Stage 5 LOCAL evidence and Gate C OBSERVED-LIVE composition
with controlled local result barriers and owned source/recovery process exits.
**Falsifier:** source activity occurs before durable admission, another read overlaps
unresolved activity, or a late result cannot be attributed to its original attempt.
**Cheapest earlier check:** characterize actual existing raw read at Gate A, including
controlled local interruption; new attempt/order injection in Stages 3/5/Gate C.
**First dependent stage / earliest gate:** Stage 3, then Stage 5; Gate A characterization,
B delivery boundaries and C full recovery. No claim a bounded batch bounds wall time.
**Owner:** implementer. **Coverage:** C18, C24–C28, C38, C39; INV-06, INV-09, INV-12.
**Waste if false:** change admission/settlement model rather than merely adjusting a timer.

## A07 — Clock evidence can support the chosen wait

**Premise:** supported deployment time is trustworthy enough for known deadlines;
within-process monotonic evidence and persistent UTC are not confused.
**Kind/status:** OBSERVED-LOCAL through Stage 5 for independent UTC/monotonic clocks,
positive/zero/sub-microsecond pacing, early/late ack, reopen, clock faults, actual
measured local elapsed time and recovery commit boundaries. Gate C adds OBSERVED-LIVE
5/8-second pacing across failure/restart/early/late ack and recovery. Trusted UTC after
local context loss and deployment time qualification remain required.
**Falsifier:** known wait shortens/restarts after observation-only calls, or contradictory
clock evidence is converted to ready. Arbitrary unobservable jumps remain outside proof.
**Cheapest earlier check:** injected independent clock readings locally, plus real elapsed
wait and process restart at Gate C. Do not change the host clock or fake a live timing pass.
**First dependent stage / earliest gate:** Stage 5; Gate C.
**Owner:** implementer/deployment owner. **Coverage:** C19, C20, C22, C38, C39;
INV-06, INV-07. **Waste if false:** revise time/recovery assumptions before API rollout.

## A08 — Budget admission remains authoritative at send time

**Premise:** actual requests use verified account identity and durable budget claims;
a saved retry hint cannot grant or reserve capacity.
**Kind/status:** OBSERVED-LIVE for fresh account verification and preserved real charges
at Gates A/B, including cancellation/refused-send charges. Gate B reused the unchanged
ledger and retained charges under controlled local failures; usage ended at 2202/5000.
Stage 5 adds LOCAL actual-adapter prefixes, indefinite/expired hints, fresh account
switch and preserved cancelled charges. Gate C OBSERVED-LIVE test-cap exhaustion,
usable/empty prefixes and timing/control integration passed. Test cap 3 → 6 preserved
charges and the authoritative 5,000 policy; current usage is 2,334. Natural expiry/
warm-up remain deterministic offline evidence, not an induced live server restriction.
**Falsifier:** refused message traffic is sent, retries bypass charging, cached health
identity bills the wrong account, or local lifecycle code refunds old charges.
**Cheapest earlier check:** small local test allowance with actual bounded source reads,
then an explicit test-policy increase preserving charges; expiry edges tested separately.
**First dependent stage / earliest gate:** reuse in Stage 3; local budget regressions
before then, actual accounting observed at Gate A/B and full lifecycle wait at Gate C.
**Owner:** implementer. **Coverage:** C14, C17, C22, C24, C38; INV-06, INV-07, INV-11.
**Waste if false:** repair actual send boundary before asserting safe source eligibility.

## A09 — Scoped revisions and recognition prevent temporal reapplication

**Premise:** creation mode, expected predecessor, prepare cursor/control context and
accepted command/receipt scope prevent old calls from acquiring new effects.
**Kind/status:** OBSERVED-LOCAL for creation plus Stage 3 context/receipt scoping,
stale rejection, latest/prior recognition and compatible settlement. Stage 6/Gate C
add actual control/recovery/terminal/retention orderings with live-origin data, including
old resume after newer pause and equal-hash successors. Stage 5 proves LOCAL recovery
identity, retained retries, changed-input/control conflict and replacement-attempt
isolation. Gate B observed actual live-data wrong-scope/equal-hash
receipt refusal, duplicate latest ack with newer pending, old receipt refusal and stale
prepare after progress. The Stage 1 counterexamples
motivated the mechanism; tests 24–28 and Gates A/B/C supply scoped implementation evidence.
**Falsifier:** delayed prepare reads after an already-accepted cursor/control change;
old resume overrides pause; unknown start creates; wrong-run receipt advances progress.
**Cheapest earlier check:** current/future-state operation-order cases with actual
conditional state, including simultaneous await barriers. No extra command service needed.
**First dependent stage / earliest gate:** start Stage 2/A, prepare/ack Stage 3/B,
controls Stage 6/C. The contract and matrix precede all implementations.
**Owner:** implementer. **Coverage:** C01–C11, C27, C30–C32, C35–C39;
INV-05, INV-08, INV-09, INV-10. **Waste if false:** revise state/authority before exposing API.

## A10 — Recovery can re-establish the single-reader precondition

**Premise:** the caller can confirm the previous worker has stopped before recovering
an uncertain attempt; the library can reject a still-active local attempt.
**Kind/status:** caller ownership policy selected; Stage 5 OBSERVED-LOCAL exact recovery,
required true assertion, active local-read/admission/publication refusal and owned
subprocess exit/commit boundaries. Copied actual Gate B unknown records also recover
without mutating originals. Gate C OBSERVED-LIVE/INJECTED source exit, parent wait,
recovery commit/reply loss and stable conservative deadline passed; active local
preparation refused recovery. Deployment ownership remains the caller's precondition.
No leases are provided.
**Falsifier:** recovery is admitted while an earlier source worker remains active, or
elapsed time alone is used as proof of death.
**Cheapest earlier check:** controlled subprocess kill + wait-for-exit and recovery;
also attempt recovery while the local reader is intentionally still running.
**First dependent stage / earliest gate:** Stage 5; Gate C.
**Owner:** caller owns worker lifecycle; implementer enforces declared checks.
**Coverage:** C18, C27, C28, C39; INV-06, INV-12.
**Waste if false:** deployment must enforce exclusive ownership or select a different scope.

## A11 — Existing-group evidence can supply an independent bounded oracle

**Premise:** the selected existing group has a manageable stable visible interval,
and a separate client/export/manual enumeration can establish the expected IDs/dates
and selected media before the reader under test runs.
**Kind/status:** OBSERVED-LIVE for Gate A's independently enumerated ID/date intervals
and selected photo hash; Gate B requalified the 350-record interval, independently
checked the same photo, and confirmed the 46-record source again after measurement.
The first source was too small for an SDK page; a second
user-selected existing source supplied that missing case. Gate C independently
requalified the 46-record view/photo before measured lifecycle reads; exact prefixes
and media matched. Read-only scope was retained.
**Falsifier:** expected results come only from the tested function, enumerate only a
sample while claiming completeness, omit required page/boundary cases, or drift during
measurement without an independent explanation.
**Cheapest earlier check:** fixture qualification before Gate A traffic. Choose another
already-existing interval within authorized scope if necessary, never send seed messages.
**First dependent stage / earliest gate:** Stage 2 harness/Gate A; cannot enter Stage 3
without the required evidence. Live behavior was not needed to write this specification.
**Owner:** caller supplies/identifies existing group and independent view; implementer
records completeness and drift. **Coverage:** C40–C42; INV-01, INV-04, INV-11.
**Waste if false:** reopen Gate A as BLOCKED/INCONCLUSIVE; stop dependent work.

## A12 — Existing contracts and health remain isolated

**Premise:** new runtime APIs keep daily/window state and batch v1 unchanged, and local
status/control/replay/ack do not become Telegram health observations.
**Kind/status:** OBSERVED-LOCAL for namespace refusal, Stage 3 local prepare/replay/ack
health isolation and supported regressions through `0d6bb26` (319 actual passes),
including actual controls and local waits/recovery without invented health/account
identity. Gate C traced no RPC attributable to intervening local operations.
Gate B local restart workers blocked sockets while settling live-data receipts;
public facade/integration remains UNVERIFIED for D.
**Falsifier:** legacy inputs/state change behavior, wrong-kind state is accepted, local
error emits a Telegram verdict, or offline operation clears a source health failure.
**Cheapest earlier check:** supported dev offline regression suite now; repeat affected
checks with each runtime change and public/live attribution at Gate D.
**First dependent stage / earliest gate:** any future shared-helper edit, otherwise
Stage 7; local checks as changed, integration Gate D.
**Owner:** implementer. **Coverage:** C25, C33, C34, C43, C44; INV-01, INV-09, INV-11.
**Waste if false:** separate the new contract from old APIs before rollout.

## External input register

| Input | Current status | Owner | Required by |
|---|---|---|---|
| Existing group and read-only test approach | SELECTED by user | Maintainer | All gates |
| Specific canonical group ID and approved account/session/config label | DONE for A/B/C; two user-selected existing sources and verified project login; credentials omitted | Maintainer | Gate A |
| Existing closed interval, independent complete ID/date oracle and source/view metadata | DONE for A/B/C; frozen before tested reads, archived in gate evidence | Maintainer + implementer | Gate A |
| Existing media fixture and independent hashes for advertised download mode | DONE for A/B/C; independent hash and actual receiver copy agree | Maintainer + implementer | A/B |
| Source request allowance, external harness spacing and test budget path | DONE for A/B/C; 5,000 cap, 2,334 charged after C, no reset; paths retained privately | Maintainer + implementer | Gate A |
| Actual state backend/integration base containing #18 foundations | DONE: real SQLite, feature-only merge `5d0789e`, isolated live-case stores | Maintainer + implementer | Stage 2/Gate A |
| Durable test receiver and declared commit/ack point | DONE for B/C: actual SQLite transaction after verified durable blob custody; Gates B/C PASS | Implementer/integrator | Gate B |
| Operational receiver, worker ownership and clock assumptions | UNSET | Integrator | Gate D/adoption |

Gate reports transition evidence states only after running the named checks. A blocked
resource is never converted to evidence by a policy choice or a documentation audit.
