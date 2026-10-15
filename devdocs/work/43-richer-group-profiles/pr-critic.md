---
model: gpt-6-astra
effort: xhigh
---
# IMPLEMENT AS WRITTEN

**Gate: ACCEPTED** — 0 High / 0 Medium / 0 Low.
Subject: actual PR47 product diff `72f51313214a318d59eb9fc43e652ae64bf67159`
against dev `abd1f577c928cc22c08cdbd9580c2d916e98c64b`, together with folded
revision2 step_by_step_impl_plan.md. This verdict retains the implemented plan;
it does not authorize merge or publication of a release.

Falsifier: a public-path counterexample in which typed metadata/pin evidence
produces false completeness/precision, a foreign owner, false health recovery,
lost primary error outside the declared cancellation rule, or unbounded reads.
Affordable now: yes — the identified local falsifiers were executed before this
verdict in pr-probes.py against the actual PR checkout; all passed. No unrun
affordable local premise remains as a release-readiness claim. Live Telegram
permissions and optional-field availability remain expressly unqualified.

## High-level summary
Fresh critic-d ran in the same warmed session, not a subagent. Prompt:
pr-dynamic-critic-prompt.md; exact downloaded diff: pr-47.diff.
Current turn metadata verifies gpt-6-astra/xhigh (§9).
Read all eight changed product/public-documentation files, folded plan, description,
triage and existing verified-operation/health/budget/heartbeat/group contracts.

**13 fresh probe groups /29 executed cases PASS** on Python3.11.10/Telethon1.45.0.
Actual SDK dispatch, TL decoding, session behavior, native SQLite and cleanup
were exercised. Server replies are synthetic; sockets and login are forbidden.
No product change or changed expectation occurred during this review.

Existing qualification of952 offline checks/32 suites and7 demos (three live
skips excluded) is retained through exact100-file SHA256 parity. All eight changed
paths, including public docs, match the tested product byte-for-byte. This is
reuse of verified identical source, not a claim that the whole suite ran again.

## Premise Inventory
### P1 — account and source attribution remain fixed
First dependent step1/3; waste if false: all profile evidence and integrations.
Originally tested before implementation in the combined prebuild and suite32/33.
Cheapest fresh test: actual overlapping owned operations with stale cached identity,
different authenticated users, one held success and one decoded source denial.
Covered by probe_overlapping_accounts_keep_evidence_separate: owner222 succeeds,
owner333 keeps denial/partial profile and its own charge; cache111 owns nothing.
Source SDK errors, local cache/SQLite failures and callback metadata stay distinct.
No live account-identity or permission claim is inferred from fixture accounts.

### P2 — returned source facts support count/coverage claims
First dependent step1/2; waste if false: public values and consumer decisions.
Original tests observe actual TL representation and selected precision flag.
Fresh matrix: ten exact/inexact/full/sliced/channel/placeholder cases, plus four
nullable/zero/signed32-maximum counter cases with mixed companion entities.
Expected statuses and exactness are declared independently of the implementation.
The source-filter result has one bounded request; unknown and approximate
observations remain distinct. No short slice is treated complete by length alone.
Telegram documents the [full-vector constructor](https://core.telegram.org/constructor/messages.messages)
and [slice/inexact fields](https://core.telegram.org/constructor/messages.messagesSlice);
actual1.45 codec tests qualify local interpretation, not a live exhaustive census.

### P3 — message allowance and completed profile evidence coexist
First dependent step2; waste if false: quota and partial-error contract.
Prebuild used actual SQLite admission/refunds. Fresh probes check oversized,
cache-only and wrong-shape source replies under the real budget adapter.
A native temporary SQLite metadata-table loss after durable admission makes
settlement fail: ReadBudgetStorageError stays local, the reservation remains
charged and the already completed profile is retained with pins_status=failed.
A received but rejected pin packet is not represented as accepted pin content.
This matches the explicitly scoped prior-metadata custody promise, not a new
durable pin-batch delivery mechanism.

### P4 — success/health and cancellation ordering remain conservative
First dependent step3; waste if false: misleading health and cleanup outcomes.
Fresh histories establish that metadata-only and invalid pin results cannot clear
a Search wait, an older held success cannot clear a newer wait, and no profile/
pin path asserts group-access recovery. Actual request evidence and monotonic
observation ordering remain in the unchanged owned-health layer.
Cancelling at both completion phases and repeatedly during held native cleanup
preserves cancellation priority and waits for the attempt to settle. Callbacks
stop after scope exit. The API does not promise delivery or a durable receipt to
a caller that cancels; cancellation can supersede the prior operation outcome
under the existing account-operation contract.

### P5 — candidate transport does not change behavior or packaging
First dependent step3/5; waste if false: verification would describe another tree.
Fresh probe verifies import origin, all100 Python hashes and exact AST equality of
every pre-existing TgData method. Only get_group_profile is added; version remains
0.1.1. review-parity.json binds the eight-file product-only candidate and dev base.
No work-folder artifact, private runtime dependency or packaging rule was added.

## Restart Check
| Observed issue | Established mechanism | Reviewed response |
|---|---|---|
| Downstream pin failure looked like an empty list | catch-all around pin iteration left [] | original exception propagates with completed profile when attributes permit |
| Prior #7 failures mixed owners/source evidence | cached/ambient ownership and incomplete attribution boundaries | existing verified context and source-owned health are reused unchanged; overlap/SQLite/error probes pass |
The broad #7 task is not being restarted; its lessons are checked at the interfaces
this new operation actually consumes. #44/#45 measurement/sampling defects remain
outside this PR.

## Inherited Lessons
| Lesson | Review evidence |
|---|---|
| A cached user ID does not prove owner | real verified context, distinct owners/cached111 probe |
| Local storage failure is not a Telegram verdict | native SQLite settlement failure and cache failure probes, zero invented events |
| Metadata/filter success is not general access recovery | no confirm_group_access in diff; existing group-denial tests and fresh wait histories |
| Count precision differs from content completeness | explicit pins_total_exact and ten fresh response cases |
| Source completion is not automatically accepted output | malformed/budget-settlement failures retain prior profile, not fabricated successful pins |
| Caller cancellation takes priority over cleanup/result delivery | completion-boundary and repeated-cancellation probes |
| A supplied server packet is not live Telegram evidence | fixtures and final qualification limits explicitly label it synthetic |

## Findings
None. No High, Medium or Low finding is supported by the reviewed code or fresh
observations. This is not an assertion that all future platform behavior is known.

## Phase 3 — mitigation selection
No findings require mitigation selection or a fold. No runtime patch, source
contract weakening, prerequisite framework or re-plan is justified by this review.
The existing narrow observation fits #43; adding a paginator, profile store,
measurement schema, distributed owner or new health mechanism would broaden scope.

## Probe output and scope
Exact output and per-case accounting are committed in pr-probes.txt and
pr-probe-results.json. Terminal output:

```text
RESULT PASS groups 13 cases 29
```

The suite covers native count accuracy/coverage, malformed budgeted replies,
actual SQLite settlement failure, existing-wait recovery, overlapping owner and
operation histories, completion-boundary cancellation, repeated cleanup
cancellation, annotation failures, pre-projection local cache errors, source
denial with failed cleanup and product/import/ABI parity. The single cleanup-error
log is deliberate fault injection. No failed probe or fixture correction occurred.

## Limits and decision
Accepted under CONTRIBUTING §7.3. Existing SDK cache and disconnect limits, nullable
optional fields, one-response pin cap and separate observation times remain.
The public method is not a membership/history-access proof, a live-field
qualification, an atomic snapshot or a durable output-delivery service.
Work docs stay on the archive branch; PR47 contains only product/tests/public docs.
No live Telegram action, merge, version bump, release or deployment was performed.
