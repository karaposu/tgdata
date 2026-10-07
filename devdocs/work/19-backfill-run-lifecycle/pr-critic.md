---
model: gpt-6-astra
effort: max
---
**PR Gate: PASS — 0 High, 0 Medium, 0 Low findings.**

**Critic-d verdict: IMPLEMENT AS WRITTEN** — for this already implemented product
diff and its adopted plans. No mitigation or runtime patch is selected. This is
CONTRIBUTING §7.2 review, performed after opening PR #20 in the same warmed session.

Falsifier: a real public/SQLite sequence with a lost reply lets older state replace
newer accepted/pending work, a scoped receipt lacks its promised observation, a local
operation fabricates source health, or the packaged public API needs development files.
Affordable now: yes — six fresh actual-component probes were executed before this
verdict, and passed. No affordable unrun prerequisite is deferred until after merge.
Actual vendor selection remains covered by the already passed, unchanged-runtime
Gates A–D; synthetic source replies below are not relabeled as Telegram evidence.

## High-level summary and exact subject

Reviewed [PR #20](https://github.com/karaposu/tgdata/pull/20), base
`45bab7172621f576fa5e4b3265f87ec20da04fd5`, head
`719f2a9fad2dcd419d1d3aaaa9b68f79ae083080`. Its actual published diff contains 27
product files and no work/archaeology delta. Product contents exactly match archive
`30c9c24`; normative plans/merge-check are archived at `47b2936`. The generated
[review prompt](dynamic_pr_critic_prompt.md) was committed separately in `441f50d`.
[Subject manifest](pr-critic-evidence/subject.json) preserves the published diff hash.

The subject includes the unmerged #18 daily/fixed-window foundations and all eight
#19 stages, not only the final test additions. It was read against both prerequisite
plans, all scoped lifecycle plans/critics and the final contract. The full relevant
facade, source/window, store/codec, lifecycle, health/budget/media and receiver paths
were read in this session; current exact product equality was checked rather than
assuming branch names identify the same code. No subagent supplied the review.

No supported-path defect was established. New probes specifically crossed real
commit boundaries where a later actor changes state before an earlier reply fails.
The earlier operation correctly reports local uncertainty and never undoes the newer
facts. Exact receipt retries preserve newer pending work. Cross-kind namespaces and
malformed state refuse without source/health side effects. The full-snapshot receiver
retains distinct observations, including after a lost committed reply. The actual
source distribution builds and its public local operations run without repository
tests, examples, work files or credentials.

## Premise inventory — ranked by waste if false

### 1. Whole-record authority survives real asynchronous reply loss

**Premise:** conditional durable state, original contexts and authoritative reload
prevent rollback/refetch when the response to an earlier operation is stale or lost.
**First dependent steps:** #18 store/prepare/ack and #19 Stages 2–6; failure would
invalidate delivery, recovery, controls and the facade. **Waste if false:** nearly
the entire lifecycle, not merely an error message. **Test scheduled:** component
probes before those builds, their actual SQLite/process suites, then Gates B–D and
fresh review before merge. **Cheapest earlier real test:** actual SQLite commit,
hold its reply, perform a later public operation, then fail the earlier reply.
**Coverage:** fresh probes 1/2 below execute exactly those histories through the
public facade, real SQLite and actual SDK. Replies alone are synthetic; storage
success and later state are not manufactured. Both passed. Power-loss behavior of
another filesystem/backend is not covered or claimed.

### 2. Exact observation, qualified end and external acceptance stay distinct

**Premise:** saved output can replay exactly; a receipt only advances its own owed
work; source exhaustion cannot complete a nonempty undelivered final batch.
**First dependent steps:** #19 Stages 3–4 and public receiver example Stage 7.
**Waste if false:** silent loss or false completion even with apparently healthy
state transitions. **Test scheduled:** prebuild source/receiver probes, delivery/
completion tests, real Gates B/D and receiver checks before the final verdict.
**Cheapest earlier real test:** committed receiver snapshot/bytes plus restart and
lost acknowledgment, checking actual stored data. **Coverage:** Gate D's independent
SQL/file/trace audit and 250-message/photo comparisons; fresh probe 5 adds two differing
observations under complete scoped receipts and an actual post-commit close failure.
All snapshots survived and duplicate reception changed nothing. The user's deployed
receiver remains a separate obligation; a test receiver cannot certify its commit.

### 3. Actual SDK/source selection and pacing fit the declared scope

**Premise:** the selected account's visible history supplies the bounded chronological
ID/date scan and real end observations, and saved/local timing enforces the chosen
post-attempt interval. **First dependent steps:** #18 window reader and #19 source
Stages 3/5. **Waste if false:** misplaced cursors or false exhaustion under the new
lifecycle. **Test scheduled:** SDK component probes, Gate A before new delivery,
Gates B/C/D before review. **Cheapest real test:** independent descending enumeration
versus the real ascending SDK reader and measured later turns. **Coverage:** Gates
A/B/C/D on identical relevant runtime, real second pages, independent photo digest,
four Gate D intervals >=12 seconds and actual account-budget claims. SDK-only mocks
do not cover server visibility, and no such claim is made. Other source views,
future mutations and reliable UTC after restart remain stated boundaries. No changed
runtime premise justified another live read during this review.

### 4. Public composition keeps namespace, health and package boundaries

**Premise:** the added facade preserves backend identity and local/source attribution;
the distributable contains the needed modules without depending on development trees.
**First dependent steps:** #18 facade/state versioning and #19 Stage 7. **Waste if
false:** otherwise correct internals fail or corrupt progress when called normally.
**Test scheduled:** public suites/package checks, Gate D and this exact-tree review.
**Cheapest real test:** use actual public methods with real mismatched SQLite records,
an unrelated RPC exception context and a built distribution outside the checkout.
**Coverage:** fresh probes 3/4/6 plus the repeated product-only regression. All passed;
there was no source request or repository test import in the packaged API probe.

### 5. The caller can establish the operational preconditions

**Premise:** one source reader per group, durable receiver acceptance, equivalent CAS
semantics and trustworthy restart time are supplied by the integrator. **First
dependent step:** operational adoption, not another library implementation step.
**Waste if false:** concurrent reads or misleading acceptance regardless of library
state. **Test scheduled:** selected local receiver/owned workers at D; each different
deployment must establish its own guarantees before adoption. **Cheapest earlier
test:** the actual chosen worker/receiver composition, not a fake lease or success
callback. **Coverage:** D confirms its owned process exits and receiver custody;
arbitrary competing-machine or production receiver behavior remains non-covering.
Those capabilities are explicitly outside scope, not hidden implementation promises.

## Restart check

- **Local file/storage errors producing Telegram health events:** established through
  the earlier #6 incident. New local operations avoid the raw reader's reporting
  wrapper and suppress incidental RPC context. Fresh probe 4 preserves a prior denial
  while malformed-state errors occur inside an authentication-error handler.
- **Cleanup replacing the primary failure:** actual rollback/close errors previously
  reproduced it. SQLite cleanup preserves active errors; receiver close-only failure
  remains visible as uncertainty. Test30's cleanup case and fresh receiver probe 5
  execute these boundaries instead of relying on exception names alone.
- **Commit success followed by failed reply:** real process/SQLite histories establish
  the mechanism. One exact-candidate read-back never replaces later state; probes 1/2
  deliberately make that candidate obsolete before its reply fails. Both retain the
  later durable facts and perform no repair read from Telegram.
- **An old receipt or response affecting a new run/control:** equal batch bytes and
  reply arrival order lack authority. Scoped refs, generations and expected revisions
  are validated. Gate D forced equal-hash generations/opposing controls; probe 2 adds
  a failed old ack followed by its retry with a newer pending batch.
- **Moving historical windows:** resolving relative input on every restart changes
  the job. Initialization/start recognize stored intent before clock observation.
  The original forbidden-clock tests and saved-query live comparisons still execute
  against this exact product; no new date resolution was introduced by the facade.
- **Marker-only storage losing an accepted observation:** Stage 7's probe established
  the failure in that proposed exact-receiver pattern. The backfill receiver now stores
  full scoped snapshots separately from its index; probe 5 confirms both observations
  survive. The older daily sample explicitly documents first-observation storage
  (`docs/daily_continuation.md`, Destination acceptance), so it is not silently used
  as the backfill exact-snapshot receiver. No edit-reconciliation requirement is added.
- **Per-worker counters missing total gate cost:** Stage 6 established this instrument
  gap. Gates C/D use durable nonrefundable launch allocations and independent actual
  sends/returned/uncertain-claim accounting. Review probes use no real account.

Every cited failure has an established mechanism and an addressing boundary. The
paused #7 account-health ownership redesign is not claimed to be solved or imported.

## Inherited lessons and ordering

Real source behavior was tested at Gate A before new source delivery, then at the
required B/C/D boundaries. Each Stage3–8 required prebuild actually ran before its
implementation. Internal/synthetic success never replaced the public/live gate.
External acceptance was tested at the chosen receiver before claiming completion;
new exact snapshots preceded the receiver demonstration. Generation/control identity
preceded successor/late-reply tests. Owned workers were explicitly waited for before
recovery. Receiver markers, cursor progress, source end and source health stayed
separate in both code and evidence. This sequence addresses the inherited lessons;
merely documenting them would not have done so.

## Fresh probe observations

[pr_critic_probes.py](pr_critic_probes.py) ran against `/private/tmp/tgdata-19-pr-review`
at exact head `719f2a9`. Its actual outputs are preserved in
[public-probe-results.txt](pr-critic-evidence/public-probe-results.txt):

```text
publication_reply_after_receiver_and_ack: PASS; completed at 101, one source read
ack_reply_after_newer_pending: PASS; accepted 101, pending 102 survives old receipt
namespace_isolation_both_directions: PASS; three refusals, zero mutation/config loads
malformed_state_inside_unrelated_rpc_context: PASS; three local refusals, health unchanged
receiver_contracts_and_failed_reply: PASS; two scoped snapshots, one message index row
Passed: 5/5 fresh public/SQLite/SDK/receiver probes; LOCAL, sockets forbidden
```

The five lines above are labeled summaries; the linked JSON output is the verbatim
observation record. No expected result was changed and no initial probe failed.

[pr_package_probe.py](pr_package_probe.py) used installed setuptools to build the
actual source distribution and its package in a disposable git-archive checkout.
Wheel/build frontends were unavailable; no dependency was fetched to run the check.
The built package, outside the repository and with sockets/config blocked, performed
public create/retry/status/pause/prepare/close. Verbatim final line:

```text
Passed: 1/1 actual sdist/build/import/public-local-API probe; no network or repository work files
```

[Package result](pr-critic-evidence/package-result.txt) and
[build log](pr-critic-evidence/package-build-log.txt) retain the evidence (only the
disposable directory prefix is normalized). Package version remains 0.0.8; no release
or version bump is part of this PR. No smoke-test module was imported by the built API.

The exact product-only candidate also reran **357 actual supported checks and both
examples**, with three legacy live skips separately counted; it parsed as Python 3.7
and executed on Python 3.11.10/Telethon 1.45.0. That runtime/syntax distinction remains
explicit. No performance/security/compatibility defect on a supported path was
established by full source review or these observations; no speculative risk is padded
into the finding count.

## Findings and Phase 3 disposition

No High, Medium or Low finding was established. Phase 3 has no mitigation proposals
to select; no boxes, architectural generalization or product patch are invented.
The completed plan may stand. The seven earlier selected Medium findings retain
their implemented answers documented by the separate merge check.

§9: active-session metadata verifies gpt-6-astra/max in this warmed session, matching
the required model family at higher effort than xhigh. No cheaper model, subagent or
unsupported claim of literal xhigh was used. This verdict is tied to the exact PR
base/head above; a changed runtime, target or deployment assumption requires review
of affected evidence. **Merge remains awaiting the maintainer's explicit go-ahead.**

Administrative follow-through: stale Stage 7 status text in the archive contract/live
specification was refreshed to the observed Stage 8/Gate D completion. No normative
contract, product file or probe expectation changed. These work notes remain outside
the PR diff.
