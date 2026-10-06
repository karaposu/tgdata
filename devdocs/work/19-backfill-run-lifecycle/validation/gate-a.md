---
model: gpt-6-astra
effort: max
gate: A
verdict: BLOCKED
date: 2026-10-07
---
# Gate A — frozen scope, source compatibility and real persistence

**BLOCKED — no live attempt made.** Stage 2 product is `1425fd7`, based on feature-only
prerequisite merge `5d0789e` through #18 `e9b5154`. Its executable instrument is
[live_probe.py](../live_probe.py), committed with this report. Record the exact product
and instrument revisions again on actual live execution.

The user selected an existing group and read-only tests. No particular account/config,
group or independent complete interval was supplied. No real config/account has been
read, no Telegram connection has been attempted, and no source request budget consumed
by this validation run. Offline checks used disposable local inputs and synthetic transport.

## Required inputs still open

| Input | Owner / action |
|---|---|
| Already-authenticated account/config label and existing canonical group | Maintainer identifies; implementer verifies selected account matches before history reads |
| Closed bounded interval, independent complete IDs/dates, view/provenance/capture time | Maintainer identifies independent view; implementer qualifies and freezes manifest before tested reads |
| SDK and caller page crossings, boundary/tie/gap/end cases | Qualify existing visible history; missing critical cases stay blocked/inconclusive |
| Eligible media and independent expected hashes/sizes for download mode | Qualify existing read-only artifacts; no fixture creation |
| Authoritative budget ledger/account policy, stricter test caps, spacing and elapsed allowance | Maintainer/integrator establishes; instrument must not create/reset allowance |
| Disposable state/output/artifact paths and retained request/RunRef | Prepare locally, with no existing progress overwritten |

An async request for the account/config label, group and independent view was issued
during this run and remains unanswered. Credentials should remain in local configuration,
not in issue comments or evidence. The example manifest is deliberately unqualified and
its numeric caps are illustrative; it is not authorization to send those requests.

## Evidence available, and its limits

| Area | Evidence | Gate status |
|---|---|---|
| New run identity/frozen dates/reopen | Real Stage 2 engine + SQLite, forbidden-clock retry, conflicts/absence/refusals | LOCAL observed |
| Durability and uncertain replies | Actual process exits immediately before/after commit, committed cleanup error, exact CAS | LOCAL/INJECTED observed; no power-loss claim |
| SDK/page/retry guard and budget instrumentation | Real Telethon 1.45.0 iterator/request types and budget code with synthetic transport | LOCAL/INJECTED only |
| Real source selection, date/order/end and page behavior | No selected independent live fixture | UNRUN |
| Real source failure/interruption and budget trace | No live attempt | UNRUN |
| Real media/date boundary behavior | No independently qualified live artifacts | UNRUN |

[Verification](../stage-2-state/verification.md) records 198 actual offline test groups,
3 explicit live skips, 9 additional instrument checks, compilation and the existing
offline daily example. None is counted as a live pass. Later lifecycle source/delivery,
completion, controls, pacing/recovery and facade behavior are unimplemented.

## Resume

1. Resolve the inputs above and qualify every required case in the
   [live-validation specification](../live-validation.md). Preserve the existing-group,
   read-only scope and the independently recorded oracle.
2. Prepare an isolated run locally and complete the actual manifest. Run the offline
   preflight in [probe usage](../stage-2-state/probe-usage.md), with an existing state
   store. Preflight success authorizes no extra traffic by itself.
3. Execute explicitly bounded live scans with the selected config, existing authoritative
   budget and disposable outputs. Retain sanitized reports; compare against the frozen
   oracle and investigate mismatches without rewriting expectations to match the reader.
4. Assemble all required local/live observations, exact revisions, source/view metadata,
   limits, budget charges, page/send trace, interruptions and uncovered cases here.
   A matching scan remains INCONCLUSIVE until the whole gate's evidence is reviewed.
5. Record PASS only when all required Gate A assertions hold. BLOCKED, INCONCLUSIVE
   or FAIL continues to block Stage 3. Later gates B–D remain unrun.

This is the folded Stage 2 plan's OPEN execution blocker before Step 6, not a rejected
plan or an implementation abort. The caller supplies the missing context; the implementer
qualifies and runs the gate. Do not start Stage 3 while it remains open.
