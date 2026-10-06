---
model: gpt-6-astra
effort: max
status: gate-a-blocked
---
# Read-only live validation specification

This specifies Gates A–D for the [contract](contract.md) and
[case matrix](acceptance-matrix.md). **All gates are UNRUN; Gate A is BLOCKED on actual
inputs.** Stage 1 wrote the procedure. Stage 2 now supplies [live_probe.py](live_probe.py)
and [usage](stage-2-state/probe-usage.md), exercised only with offline/synthetic transport.
No real account/config has been accessed and no source traffic has occurred. The
[Gate A report](validation/gate-a.md) records the missing inputs and scoped local evidence.

The user chose **an existing group, using read-only tests**. Every live source action
must be a bounded read of that selected group's already-visible history. No messages,
media uploads, edits, deletions, invitations, joins, membership changes, account setting
changes or intentional server flood/ban generation belong to these tests. Local test
stores, saved media copies, receiver records and process interruptions are expected.

## 1. Inputs to establish before the first live request

Record these in the gate report before running. `UNSET` is not a default or approval.

| Input | Required meaning | Current value |
|---|---|---|
| Code revision / package import path | Exact tested code, including #18 foundations for Gate A | Stage 2 product `1425fd7`; record actual checkout and tool commit on live execution |
| SDK | Actual installed Telethon version | Required: 1.45.0 |
| Account/session/config label | Caller-selected already-authenticated test context; never publish secrets | UNSET |
| Canonical group ID | Specific existing group accessible to that account | UNSET |
| Source visibility | Account/access/view used for the independent baseline | UNSET |
| Closed interval | UTC start/end and declared exclusive origin | UNSET |
| Oracle provenance | Independent client/export/manual enumeration, capture time, interval completeness | UNSET |
| Expected ID/date set | All visible messages within that bounded interval, plus boundary witnesses | UNSET |
| Page-crossing fixture | Enough existing records to cross a real SDK history page and multiple caller batches | UNSET |
| Existing media fixture | Expected eligible record IDs, original bytes/hash/size where download mode is advertised | UNSET |
| Source allowance and pacing | Total requests/messages/elapsed limit; external spacing before Stage 5 exists | UNSET |
| State/artifact paths | Disposable isolated collection data, no existing progress overwritten | UNSET |
| Budget policy/ledger | Chosen authoritative account allowance plus any stricter test cap | UNSET |
| Receiver acceptance point | Actual commit/durability boundary before acknowledgment | Gate B/D: UNSET |
| Reader ownership | How the caller excludes another source worker and confirms process exit | Gate C/D: UNSET |

Keep an existing authoritative account budget in force. A separate test cap may
restrict it further; it must not grant extra allowance or bypass charges on an account
also used elsewhere. If a dedicated ledger is used, the caller must establish that it
is authoritative for the isolated test account/session. Increasing a temporary test
cap preserves all incurred charges and does not change a production account policy
implicitly. If that setup cannot be established, the budget case stays blocked.

## 2. Establish an independent oracle from existing history

1. Choose an already-existing, closed, manageable interval from the selected group.
   Record why it fits the request cap and covers the critical cases. Do not pick an
   expected count after seeing the result from tgdata.
2. Enumerate the whole visible interval through a separate client/export or manual
   inspection with recorded message links/IDs, timestamps and view/account context.
   Record excluded boundary witnesses where they exist. A few familiar messages or
   a Telegram aggregate message count are not a complete interval oracle.
3. Freeze a minimal local manifest before the tested read. It can contain group ID,
   interval, source/view/capture metadata, ordered expected IDs/dates and selected
   media hash/size references. Do not place credentials or unnecessary message content
   in committed reports. Document how completeness was established independently.
4. Choose caller batch sizes and an existing history span that force a real SDK page
   boundary as well as caller-batch boundaries. Observe actual request/page behavior;
   do not infer a server page boundary from repeated small caller requests. The fixture
   qualification must state the exact bound/count and planned cases before traffic.
5. Use existing equal-time messages, gaps, boundary records and media where required.
   If a critical case cannot be found within the selected read-only scope, mark it
   BLOCKED/INCONCLUSIVE. A different already-existing interval can be selected and its
   oracle frozen before rerun; do not create records or silently demote the assertion.
6. Check whether the independent view changed during measurement. Preserve both
   observations. If edits/deletions/visibility drift explain a mismatch only as a
   hypothesis, mark the result INCONCLUSIVE and re-establish the oracle before rerun.
   Do not alter the expected set simply to match the tested function.

The oracle for **source selection** is the independent expected set above. The oracle
for **exact replay** is the canonical payload and artifact hashes actually prepared
and durably retained on the first call. Comparing replay with that observation proves
preservation of it; it does not independently prove the source selection was complete.

## 3. Harness boundaries and observations

Stage 2 supplies the opt-in `live_probe.py` in this issue's work folder. It requires
explicit live mode and the selected account/group/fixture;
importing it or running default offline checks must not connect. It must use the actual
library/Telethon paths, not a fake provider presenting the desired Telegram behavior.

**Gate A composition:** Stage 2's real saved run provides intent, resolved dates and
origin. The existing #18 `get_message_batch` path performs bounded reads from those
values. The driver keeps its oracle comparison separately. It does not reimplement
pending/acknowledgment or pretend the Stage 7 backfill facade exists. Creation/status
must remain offline even when the same driver can separately perform real reads.

**Gate B/C composition:** the new internal backfill engine, actual guarded raw reader,
real durable store and local durable receiver. Use disposable local artifacts and
state. Drive only the behavior that has reached its implementation stage.

**Gate D composition:** the real public API, selected state backend and actual intended
receiver flow. Re-run representative cases through that facade; success of an internal
component alone does not establish the public composition.

Record at least:
- source operation/attempt identities and actual history-request counts, parameters
  needed for boundary verification, admission/start/end times and observed SDK retries;
- store revision/cursor, pending hash, end evidence and control/terminal facts at each
  named interruption boundary, using sanitized views rather than message dumps;
- receiver commit evidence, accepted unique ID set and media hash/size checks, with
  duplicate batch and overlapping-collection outcomes;
- process IDs/exit confirmation for controlled recovery, command/receipt contexts and
  actual results when responses are deliberately delayed or dropped;
- expected versus actual outcome, evidence class and the reason a case is conclusive.

Attribute activity to the operation under test. Unrelated SDK housekeeping must not
be misreported as a local status/ack creating a history request; equally, a hidden
history retry must not escape the recorded source count.

No run-loop is added to tgdata. The harness schedules bounded turns and applies external
spacing until Stage 5 exists. It yields control between turns and stops at its declared
request/time allowance. SDK retries/flood waits remain observable; a batch-size cap is
not a wall-time guarantee. Never weaken actual budget admission to finish a case.

## 4. Controlled failure methods

Use named test-only barriers at actual boundaries: after durable attempt admission,
after a real source return but before result publication, after pending publication,
after receiver commit, before/after actual state commit, and before delivering the
command/ack response. State which side of the durable boundary was reached.

For a process crash, terminate only the owned test worker. Recovery waits for its
actual exit. Do not assume that a delayed response or elapsed timeout proves quiescence.
A deliberately still-running worker is a separate negative case that must refuse recovery.

For lost acknowledgment, commit to the real receiver first, then withhold/drop only
the local response or tgdata acknowledgment. Replay the exact batch and inspect actual
receiver data and effects. A fake “receiver accepted” callback is non-covering.

For a storage uncertainty case, interrupt or fail around the real backend commit,
then reopen that backend in a fresh process. A memory object claiming a write succeeded
is not durability evidence. For media corruption, alter only a disposable local copy;
never edit source messages/media in Telegram.

For pause/cancel races, hold the real result before settlement and apply the control
against the actual store, then release the result. Force both terminal orders. These
are **INJECTED local orderings around real components**, not naturally observed Telegram
server failures. Simulate unsupported server error categories only in separately marked
LOCAL tests; do not induce Telegram bans or floods to create them.

For time, keep host time unchanged. Use independently controlled clocks for local
edge cases and measured elapsed time plus real process restart for live timing. An
explicit test-cap increase is not evidence that a rolling 24-hour charge expired.

## 5. Gate A — source and saved-intent foundations

**Entry:** Stages 1–2, chosen existing read-only fixture/inputs, actual #18 source base,
actual Stage 2 start/status record and external harness spacing. No Stage 3/7 dependency.

Required evidence:
1. LIVE independent ID/date/boundary/pagination/selected-media comparison (C12/C13
   foundation portions, C14 source behavior, C41/C42). Record actual SDK pages.
2. Real create/reopen/retry and saved-window reuse, with same intent tomorrow/restart,
   changed/unknown/absent requests and corrupt state (C01–C05, C37, C43/C44).
3. Actual SQLite before/after-commit boundaries and correct no-send behavior of local
   create/status; paired live reads use the saved query, not freshly calculated dates.
4. Characterize current raw read attempt/retry/cancellation boundaries with controlled
   interruption where affordable; record limitations and do not claim Stage 5 recovery.

**Pass:** the foundation-critical assertions pass with their required evidence. No
new lifecycle delivery, completion, pacing or control guarantee is credited yet.
**Advance:** permits Stage 3. Otherwise preserve evidence and fix/re-plan foundations.

## 6. Gate B — delivery, acknowledgment and completion

**Entry:** Gate A PASS and Stages 3–4; actual new internal engine and real receiver.
Harness still enforces external pacing. Source oracle is requalified for drift.

Required evidence:
1. Exact live-data pending replay and actual destination acceptance/deduplication,
   including sequential overlapping-window collections (C15–C17, C29–C31).
2. Pending/receiver/ack commit interruptions, restart and stale prepare after progress
   advanced; no unexpected source reads or cursor effects (C21, C25/C26, C35).
3. Empty/final/full/imported coverage with durable completion and failed read cases
   (C12–C14, C23/C24). No-account/budget/transport failure cannot become successful end.
4. Unknown source outcomes remain recovery-required. Do not reset a stuck test record
   or require recovery/control machinery scheduled for Stages 5–6 to pass this gate.

**Pass:** required source/store/receiver evidence agrees; only fully accepted exhausted
scope completes. **Advance:** permits Stage 5. Reopen A if source interpretation changes.

## 7. Gate C — timing, recovery and operator intent

**Entry:** Gate B PASS and Stages 5–6; actual pacing/recovery/controls, exclusive test reader.

Required evidence:
1. Real elapsed pacing across failure, restart and early/late ack; separately marked
   injected clock cases (C19/C20, C22, C38/C39). No status/retry-created timer drift.
2. Actual budget adapter refuses traffic under the agreed test cap, retains useful
   prefixes and re-evaluates capacity when a permitted test-policy change allows it.
   Existing authoritative account charges stay in force (C14/C17/C22/C38).
3. Possible-send crash, confirmed worker exit, conservative recovery and lost recovery
   reply. Still-active or replaced attempts refuse (C18, C26–C28, C39).
4. Forced control/terminal orderings, late results, stale preparation/control and
   abandonment/succession/receipt-retention cases (C03/C04, C06–C11, C16/C21/C22,
   C27/C28, C32, C36). Completion-first and cancellation-first must both be exercised.

**Pass:** timing and all required orderings preserve their invariants, receipts settle
without new source permission, and uncertainty stays visible. **Advance:** permits Stage 7.
Reopen B if delivery/completion/authority changes invalidate its evidence.

## 8. Gate D — complete public flow

**Entry:** Gate C PASS and Stages 7–8; the chosen public API/backend/receiver composition.

Required evidence:
1. Bounded complete backfill over separate real process sessions and an actual wait;
   delayed delivery/restart with expected final IDs/media and qualified completion.
2. Daily and historical work scheduled sequentially with isolated progress; each can
   receive a turn without advancing the other (C13/C34).
3. Local public operations create no attributed source request or false health event;
   representative B/C fault cases repeated through facade (C21/C27/C33–C39).
4. Full relevant regressions, all critical assumptions with evidence for the released
   revision, and rerun of any earlier gate invalidated by changes. No required skip.

**Pass:** review readiness for this feature delivery; not automatic PR/merge/deployment.
A different deployment backend/receiver needs its own equivalent acceptance evidence.

## 9. Gate report template and decision rule

A report records actual results; do not prefill one as passed during Stage 1.

```text
Gate: A | B | C | D
Code revision and import path:
Date / SDK / Python:
Selected account/config label, group and visibility (no credentials):
Fixture provenance, frozen interval, expected-set hash, completeness method:
Backend / receiver and acceptance boundary:
Request allowance, pacing, budget and worker ownership:
Per case: ID; expectation recorded before test; LIVE/INJECTED/LOCAL;
          actual observation; request/store/receiver evidence; result; limits
Changes since earlier gate and which prior evidence was rerun:
Unresolved or skipped critical cases:
Verdict: PASS | FAIL | BLOCKED | INCONCLUSIVE
Decision: advance to named stage | stop and named repair/re-plan
Evidence artifact locations (sanitized):
```

- **PASS:** every required critical assertion has the specified evidence and relevant
  regressions pass. LOCAL success alone cannot satisfy a LIVE requirement.
- **FAIL:** conclusive evidence violates an expected invariant/premise. Preserve the
  failing case, trace dependencies and fix implementation or revise the premise/plan.
- **BLOCKED:** a required input/capability is unavailable. Do not substitute a weaker
  test and relabel it as the original evidence.
- **INCONCLUSIVE:** source drift, insufficient observation or uncertain fault placement
  prevents deciding. Improve the measurement and rerun before advancing.

If a premise is wrong, re-critique the revised contract/ordering. Do not change expected
outcomes merely to preserve existing code. If a local implementation typo is wrong,
fix it and rerun the failed and affected checks. Later invalidating changes reopen
earlier gates. Only independent work may proceed while a gate is blocked.

## 10. Stage 1 handoff

The executable harness is Stage 2 work. Current actual resource values are in
[assumptions.md](assumptions.md) and remain UNSET. These document procedures and local
existing-component probes do not fulfill any live gate. Stage 2 remains a separately
selected implementation step on a base containing its #18 prerequisites.
