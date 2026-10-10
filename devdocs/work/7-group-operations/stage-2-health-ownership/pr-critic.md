---
model: gpt-6-astra
effort: max
---
# IMPLEMENT AS WRITTEN

**Gate: ACCEPTED — 0 High, 0 Medium, 0 Low.** This is the fresh second-round
PR22 soundness review under CONTRIBUTING §7.2–7.3, not permission to merge.

**Falsifier:** actual SDK/asyncio composition supplies evidence for an unsent or
wrong-owner request, loses the original failure's provenance, or lets notification
lifetime change the source outcome such that the selected boundary cannot separate
those facts. **Affordable now:** yes — local probes, seconds, no live account.
**Status:** the targeted falsifiers were executed before this verdict; none produced
a disqualifying observation. No affordable unexecuted behavioral blocker is deferred
behind approval. Existing regression results support, but do not replace, this review.

## High-level summary

Revision4 closes the three first-round findings and the subsequent mutable-input
finding. Failure and success keys now describe the same namespaced action. A fresh
self proof cannot stand in for a refused history read. Attribution neutrality follows
the original failure across tasks, while a new legacy RPC remains observable.
The fixed-owner monitor remains a bounded prerequisite for later group operations.

The additional probes challenge composition beyond the earlier regressions: equal
short names under different namespaces, supported and invalid batch containers,
SDK-internal username resolution, successful requests followed by local failure,
forced cross-account cleanup reordering, cancellation before recovery, and forwarded
pre-proof failure followed by a real legacy wait. All seven groups passed.

**Subject:** full product diff `53306df...c6451bb`, with plan.md revision4 at
`aee7211`; implementation evidence `cc5050b`; renewed merge fidelity `fd655a5`;
fresh prompt `da777fe`. Remote PR22 base/head were checked against local Git before
review; later checkpoints contain work-folder documents only. Review ran fresh
in the same warmed session, without delegation or runtime fixes.

Read the affected health/owned-health implementations, facade and factory boundaries,
Stage1 handle and teardown, read-budget hooks, session implementation, suite33 and
its real-SDK fixture, product contracts, triage, description, plan critics, first PR
critique and re-plan evidence. Inspected installed Telethon1.45.0 UserMethods._call,
MTProtoSender.send/_handle_rpc_result and RequestState, including request resolution,
wrapping, batch collection and error construction. Original PR review/prompt/probes
remain byte-for-byte under archive/round-1; root critic.md remains the plan review.

## Premise Inventory

### 1. Request evidence matches the actual action — supported

**First dependent steps:** 2–3. **Waste if false:** wait and restriction records
claim an action succeeded when another action or only metadata did.
**Test scheduled at:** prebuild findings, step1 red cases, steps2/3/5 acceptance.
**Cheapest earlier test/cost:** actual SDK sender error and nested-resolution calls,
seconds offline; first-round probes established the original defect, and this review
extends the combinations. **Coverage:** suite33 observes actual sender-built errors,
mutable-list input and MultiError, rather than supplying convenient error names.
Probes1–3 below independently establish namespace restriction separation, tuple
success/invalid-container refusal and a nested resolver wait distinct from its outer
history request. Known envelopes are bounded; unknown/lazy input supplies no invented
success. Stable individual request objects remain an explicit private caller contract.

The original probe draft attempted a set of generated requests and failed before
entering product code: SDK TLRequests are unhashable. The final probe records that
fact, exercises real tuple success, and tests invalid set/dict input conservatively.
No hashable test-only request subclasses or weakened product expectations were added.

### 2. Origin metadata preserves attribution without changing diagnostics — supported

**First dependent step:** 4. **Waste if false:** unknown-account failures become
cached-parent facts, or unrelated legacy failures disappear.
**Test scheduled at:** required carrier experiment before step1, then step4 and
integrated step5 cases. **Cheapest earlier test/cost:** actual Stage1 failure through
an awaited task and wrapper, seconds; passed at d2dd499 before implementation.
**Coverage:** the carrier experiment did not supply the later emission predicate.
Suite33 separately tests actual predicate composition, original explicit-cause
rethrow, prior implicit context, new RPC precedence, MultiError members and harmless
metadata failure. Probe7 combines child-task forwarding, diagnostic classification,
handled-error reporting and a subsequent real legacy wait in the same handler.
The pre-proof account remains unobserved; the new wait belongs to legacy owner111.
General classify/polling diagnostics still see the original logout verdict.

### 3. Recovery and delivery respect operation lifetime — supported within scope

**First dependent steps:** retained owned observation/notification composition,
then steps3–5. **Waste if false:** late work or observers can corrupt account state
or replace outcomes before later group APIs adopt this prerequisite.
**Test scheduled at:** initial prebuild composition, original suite33, rework step5.
**Cheapest additional test/cost:** force source overlap, local failure and cancellation
with asyncio barriers; seconds. **Coverage:** probes4–6 execute real SDK calls and
real disconnect/task behavior. Successful request evidence is insufficient when the
body subsequently fails or is cancelled. Two proven owners stay distinct while
cleanup completes in reverse order and the legacy cache changes to a third ID.
Notifications follow completed source teardown; timestamps retain observation order.
Existing suite33 covers caught handle invalidation, older/same-call refusal, callback
failure/cancellation, re-entry and cooperative/self close. No durable/FIFO or arbitrary
noncooperative-shutdown premise is inherited.

### 4. Live Telegram access semantics — outside this delivery

**First dependent step:** later group lookup/access/join stages, not Stage2.
**Waste if false:** later interpretation of group-specific results must change.
**Test scheduled at:** those future operations, not claimed by these offline tests.
**Cheapest observation/cost:** an authorized live account/group test; unnecessary to
validate this stage's local ownership and provenance contract.
**Coverage:** synthetic server replies are deliberately non-covering for actual
server permissions, frozen-account behavior and network policy. The private group
assertion requires the future operation to interpret an actual access result; this
review does not turn a request name into permission proof or claim live validation.

## Restart Check

| Observed prior failure | Established mechanism | Current answer / evidence |
|---|---|---|
| Verified B event later summarized as cached A | Mutable legacy identity owned the summary | Fixed per-account monitor and explicit local query; suite33 owner tests, probe5 |
| Wrapped errors alias waits / cannot recover | Error used outer wrapper; success used caller type | Same namespaced logical key at both boundaries; sender-built suite33, probes1/3 |
| Repeated identity clears action restriction | Any nonempty request set counted | Stored refused key plus method and temporal guards; suite33 negative/positive budget cases, probe1 |
| New legacy RPC disappears inside old handler | Any excluded ancestor suppressed the whole chain | Ordered marker/RPC decision at emission only; suite33 and probe7 |
| Child pre-proof failure becomes parent logout | Exclusion list remained in parent task | Origin metadata survives forwarding; prebuild experiment, suite33 and probe7 |
| Caller list changes the recorded successful action | Input reread after await | Immutable bound keys captured before await; actual SDK mutation regression |

## Inherited Lessons

| Lesson | Sequence / actual validation |
|---|---|
| Running SDK dispatch does not establish its error representation | Real sender/result construction was added before corrective runtime edits; retained by review probes |
| Account proof is not proof of another action | Refused-key predicate tested with self-only and budget-refused work before acceptance |
| Context is not necessarily the same failure | Explicit marking and ordered incoming traversal tested before approval, including task hops |
| Passing suites are not PR soundness evidence alone | Seven additional composition probes executed after fidelity check and fresh prompt |
| Keep the prerequisite smaller than the whole group feature | Existing ledger/wrapper/Stage1 reused; no registry, sender receipt layer, permission engine or migration |

## Executed additional probes

Command, from this worktree:

```bash
/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python devdocs/work/7-group-operations/stage-2-health-ownership/pr_probes.py
```

Python3.11.10 / Telethon1.45.0. Final process exit0. Seven probe groups; sockets are
forbidden, credentials/session data synthetic, SQLite/session/SDK/asyncio composition
real. Error responses enter actual RequestState/result handling via the inspected
suite33 adapter. Local log: `/private/tmp/tgdata7-r4-fresh-pr-probes.log`.
The following output is the durable evidence; temporary logs are not archival storage.

```json
{"probe":"namespace_restriction","observed":{"other_namespace":"restricted","same_namespace":"ok"}}
{"probe":"concrete_batches","observed":{"tuple":["messages.GetHistoryRequest","updates.GetStateRequest"],"set":"invalid SDK input; no recovery evidence","dict":"invalid SDK input; no recovery evidence"}}
{"probe":"nested_resolution","observed":{"failure_key":["contacts.ResolveUsernameRequest"],"initial_events":1,"history_success_clears_resolver_wait":false,"resolver_success_clears":true}}
{"probe":"unsuccessful_body","observed":{"account":"restricted","wait":["messages.GetHistoryRequest"],"group":["7"],"events":3}}
{"probe":"account_overlap","observed":{"arrival_owners":[333,222],"observation_order":[222,333],"cached_owner":999,"cached_owner_has_ledger":false}}
{"probe":"cancellation_recovery","observed":{"cancelled_body_keeps_wait":true,"source_closed":true,"later_success_recovers":true}}
{"probe":"forwarding_then_fresh","observed":{"isolated_diagnostic":"logged out","owned_ledger":null,"legacy_owner":111,"legacy_events":1,"legacy_request":"GetHistoryRequest"}}
```

The first probe draft stopped on its unhashable-request construction as described
above; the product was not implicated or modified. The completed run contains all
seven groups. Probe compilation/Python3.7 grammar and diff whitespace also passed.
The recorded **445 actual offline suite passes, 3 live skips, 3 demos and 63-file
syntax checks** from c6451bb remain applicable: no product files changed in either
gate. They were not needlessly rerun wholesale during documentation-only review.

## Findings and mitigation selection

**No new High, Medium or Low finding.** No mitigation proposals or selections are
needed in critic-d Phase3. The affordable probes ruled out the suspected composition
failures above; no unsupported risk is added merely to populate the review.

Consciously retained contracts, not newly discovered defects:

- Only verified private operations populate the explicit account view. Existing
  public methods and health_check retain legacy behavior, including its known limits.
- A logical request key describes a request type, not arguments, session generation
  or a full permission domain. The current single account condition is intentional.
- Internal callers keep the raw client, request objects and opening-task lifetime
  stable. Arbitrary detached/forged use is not an authorization sandbox.
- Group access needs explicit interpretation of a real result by later group code.
- Notification arrival may reorder; there is no durable/FIFO or bounded shutdown
  promise. Ongoing producers finish before cooperative close.
- The previously accepted Stage1 Low about malformed bootstrap self replies remains
  unchanged: it still refuses/closes. It is not a new Stage2 finding.

## Gate consequence and provenance

Both renewed gates pass for product c6451bb. Commit/push this critique and probes,
post the full verdict on PR22, update issue7's step6/7 with those artifacts, and mark
the PR ready for review. The first rejection stays visible as history; it is answered,
not erased. There is no second rejection and no §7.4 upstream restart is triggered.

Merge still requires the user's go-ahead. Exclude devdocs/work and any archaeology
refresh from dev, preserve dev archaeology and retain the archive branch. Whole #7
remains open for stages3–5. No runtime fix, live Telegram action or merge occurred.
Frontmatter uses retained same-session Astra/max provenance and the previously
recorded timestamp discussed in merge-check.md, not an invented current selector read.
