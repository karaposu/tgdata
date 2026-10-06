---
model: gpt-6-astra
effort: max
---

**PR verdict: REJECTED — 2 Medium findings, 1 Low finding.**

**critic-d disposition: IMPLEMENT AFTER FOLDING THESE IN.** The feature's overall
shape remains viable. At this implemented-code gate, CONTRIBUTING §7.4 requires
revision3 re-planning, a new plan critic/fold and implementation, not direct
post-review patches. The proposals below are input to that re-plan.

Falsifier: the real SDK exhausting temporary RPC failures must not make a valid
cached group look like bad input; a public health summary must not attach a fresh
account's observation to a different cached account ID.
Affordable now: yes — real SDK/public-facade probes with supplied transport, under
one second without network. Both falsifiers were run and reproduced the failures
below before this verdict. No future experiment is substituted for their result.

# High-level summary

Reviewed PR16's implemented product diff and plan.md together, at head
`7e3408a3691e48f4677efabadc8d41307e08ebd7` against dev
`45bab7172621f576fa5e4b3265f87ec20da04fd5`. Runtime remains implementation8e245f8.
The merge-check's fidelity pass was not treated as a soundness verdict.

- Medium: SDK retry exhaustion loses the final RPC error, and numeric resolution
  additionally converts it into GroupReferenceError. A valid group can look invalid
  during a temporary Telegram failure.
- Medium: fresh account identity is used on the new events but not on the health
  ledger's public snapshot. One denial is emitted for account222 and then appears
  inside a health summary labeled account111.
- Low: the committed concurrent-identity test's immediate replies allow its two
  operations to complete sequentially. A separate probe forcing overlap passes,
  but that stronger check is not in the product regression suite.

The25 new regression groups and prior151-group offline receipt remain valid
observations; they do not cover these missing cases. No runtime file was changed
while conducting this review. No live Telegram request or group mutation occurred.
Model/effort is verified as Astra/max from active turn metadata, including the
post-restart continuation; see model-verification.md. No lower-model review or
subagent handoff was used.

## Premise Inventory — ranked by waste if false

1. **Premise:** failure translation preserves the distinction between local
   reference problems and temporary remote failures throughout the SDK call.
   **First dependent step:** plan4; **waste if false:** resolver/facade failure
   contract and downstream retry decisions.
   **Test scheduled:** step5 local-error/ordinary-error/retry groups.
   **Cheapest earlier test:** let actual UserMethods._call exhaust ServerError
   on a known numeric peer, then on join; <1s with sleep elided.
   **Coverage:** prior suite tests a retry that succeeds or hits quota, not retry
   exhaustion. Fresh probe reproduces six sends followed by GroupReferenceError
   for lookup and generic ValueError for join. Supplied replies determine which
   error arrives, while the real SDK and new resolver determine the wrong result.
2. **Premise:** a per-call fresh account override can coexist with an unchanged
   aggregate identity without misattributing new health observations.
   **First dependent step:** plan4; **waste if false:** health integration and
   consumers of health_check()['health'].
   **Test scheduled:** step5 event-identity/recovery tests; snapshot explicitly
   kept on the old fallback in the plan.
   **Cheapest earlier test:** actual public check_group_access then health_check,
   with both transports authenticated as222 but primary cache111; <1s.
   **Coverage:** event tests pass, but the new probe shows an event for222 and
   the same group's no-access entry in a public summary labeled111. This challenges
   a plan decision, not just a missing line in implementation.
3. **Premise:** actual-send accounting and durable SQLite claims survive retries,
   cancellation, restart and concurrent processes.
   **First dependent steps:**2–3; **waste if false:** allowance architecture.
   **Test scheduled:** pre-plan SDK probe plus test20 process/retry/cancellation
   groups. **Cheapest earlier test:** those real SDK/SQLite checks, already run.
   **Coverage:** covering for local admission/SDK behavior; the new exhaustion
   probe additionally retains all six admitted charges. No quota bypass reproduced.
4. **Premise:** task-local identity remains isolated under overlapping calls.
   **First dependent step:**4; **waste if false:** concurrent event attribution.
   **Test scheduled:** step5 concurrency/reentry group.
   **Cheapest earlier test:** keep both requests pending and complete in reverse
   order. **Coverage:** original immediate-future fixture executes A-start,A-end,
   B-start,B-end. Fresh forced-overlap probe passes with correct222/333 event IDs.
   Runtime premise holds on this evidence; original regression coverage is weak.
5. **Premise:** vendor success/approval/interaction and history results have the
   documented meaning for live Telegram accounts.
   **First dependent step:**4; **waste if false:** public outcome interpretation.
   **Test scheduled:** no live test in this authorized scope.
   **Cheapest earlier test:** designated account/group with live mutation approval,
   unavailable here. **Coverage:** installed1.45 schema and documented semantics;
   scripted replies are NON-COVERING for live acceptance. This known limitation is
   not newly rated as a risk or treated as proof of server behavior.

No OPEN planning/execution blocker was inherited from the current plan. The model
metadata uncertainty is closed by evidence. The first two observations are bounded
implementation/integration failures; they do not show the whole feature belongs
at the wrong layer or require a human to redefine the requested group operations.

## Restart Check and inherited lessons

The earlier #6 failures were local errors mistaken for Telegram health and cleanup
replacing a primary failure. This diff carries local provenance boundaries and
post-ack cache/warning containment; the existing targeted tests cover those paths.

The #7 initial critic's three findings are implemented as selected: auxiliary
post-ack errors cannot erase acknowledgment; native local errors suppress incidental
RPC context; emitted events use fresh per-call identity. This fresh review finds
two incomplete assumptions around those fixes: the SDK can turn a remote failure
into the same native type being translated, and the public aggregate still uses
an unrelated cached identity. Implementing selected mitigations did not establish
those stronger end-to-end claims.

Other retained lessons hold on reviewed code/evidence: metadata is not read proof;
one helper invocation need not equal one send; uncertainty stays charged; unknown
preview IDs and incomplete joins are explicit; no mandatory post-ack RPC is added.

## Risk1 — temporary Telegram failures become invalid-reference errors

**Risk**

A group that the account already knows can be reported as an invalid reference
when Telegram temporarily fails to answer. The SDK retries, then throws away the
specific server error in favor of a generic error. The new lookup code interprets
that generic error as a reference problem. A caller that retries temporary server
errors but rejects invalid targets can stop a valid job instead of retrying it.
Joining also loses the specific remote error after its retries are exhausted.

`GroupEngine._resolve` in `tgdata/group_operations.py:247` calls get_entity for
an already-validated cached peer and catches ValueError/TypeError/KeyError as
GroupReferenceError. Factory clients retain Telethon's raise_last_call_error=False.
In1.45, `telethon/client/users.py:137` raises generic ValueError after retry
exhaustion. The fresh probe gives GetChannels six ServerError replies for known
peer-1000000000007: the facade raises GroupReferenceError with the SDK ValueError
suppressed. Six failed ImportChatInvite attempts likewise end in ValueError,
with six charges correctly retained. This is remote failure mislabeled/lost,
not a missing cache row or an invalid target.

**Severity:** Medium
**Category:** Error contract / retry classification
**Impact:** callers cannot reliably distinguish retryable server failure from bad
input; group readiness work can be rejected incorrectly; remote failure diagnostics
lose their original type despite the stated contract.
**NoobEng:** get_entity uses the same ValueError class for several paths. Validating
the local cache first does not make every later ValueError a cache/input failure.
The SDK's final retry behavior is a separate source of that type.
**Affected areas:** group_operations._resolve, new facade/client policy, lookup,
access and join failure paths; future worker retry classification.

### Mitigation — Quick

Change the reference-error text to mention possible temporary server failure.
This improves a message but leaves the wrong exception category and lost cause.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Give the new owned ephemeral operations an explicit final-RPC-error policy before
requests can run, including identity/authorization. Keep SDK retries and admission
accounting. Restrict reference-error conversion to demonstrated local input/cache
or missing-entity conditions, not every native exception escaping a network helper.
Add exhaustion regressions for numeric/handle resolution, history, identity/auth
and join, checking original final RPC type/object and retained charges.
**Why this is robust:** fixes the distinction at both origins: the SDK retains
remote failure, and the resolver stops inferring origin solely from ValueError.
The policy can be scoped to new group operations without changing all legacy calls.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The same native-error ambiguity exists in message_engine._entity_after_dialog_sync and batch_engine.fetch_batch, so a wider class is real. Changing all legacy error contracts would expand this feature substantially. The scoped robust boundary closes the new API problem and remains useful in a later common resolver migration.
*For future:* —

### Mitigation — Long-term

Unify typed request-resolution/retry outcomes across the entire shared factory and
all engines, migrating old entity lookup wrappers and their public error contracts.
**Why this is long term effective:** the same SDK ValueError ambiguity also exists
in message_engine._entity_after_dialog_sync and batch_engine.fetch_batch; one
consistent transport/error policy could prevent repeated misclassification.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit a common resolution/error policy through a separate issue covering the old message and batch contracts; do not let a global migration ride inside the #7 re-plan.

## Risk2 — the public health summary names a different account from its event

**Risk**

A caller can receive a group-denial event for the freshly authenticated account,
then ask for the account's health summary and see that same denial labeled with
an older account ID. The new event path is accurate, but the stored summary uses
a different source of identity. Applications reading the summary can therefore
attach the denial to the wrong account. Preserving the old summary behavior does
not preserve a coherent account-health contract once fresh-identity events feed it.

`HealthMonitor._event` in `tgdata/health.py:396` applies the new `_Call.account_id`
override. `_record` still stores observations in unqualified per-instance state,
and `snapshot` at539 calls `_who`, which uses TgData._health_identity's cached
primary `_self_id`. A public-path probe gives both clients authenticated ID222
while their restored cache is111. check_group_access emits user_id222; the subsequent
public health_check()['health'] has user_id111 and contains that operation's
synthetic_room denial. No two real authenticated accounts are required: one stale
cache is sufficient. Plan4 explicitly retained snapshot fallback, so this is a
plan decision that the fresh soundness check rejects.

**Severity:** Medium
**Category:** Account attribution / public API coherence
**Impact:** health-summary consumers can record or act on a denial under the wrong
Telegram account; events and summaries disagree about whose condition is stored.
**NoobEng:** changing the identity printed on an event does not change the identity
owned by the ledger behind the summary. Reading a cached client ID later can
relabel an observation that was recorded under a freshly verified identity.
**Affected areas:** HealthMonitor event/record/snapshot identity, TgData.health_check,
and the new ephemeral methods' interaction with existing health consumers.

### Mitigation — Quick

Omit account.user_id from summaries after ephemeral operations, leaving all state
otherwise untouched. This hides a wrong label without defining ownership/mixing.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Make verified identity part of the health observation's stored ownership and derive
both event and summary attribution from that ownership. Retain cached fallback
only for genuinely unverified legacy observations. Define account-change/conflict
behavior in the revised plan: a summary must not silently merge or relabel different
verified accounts, and one account's successful request cannot clear another's
condition. Cover the public summary after stale-cache, no-primary, sequential
identity-change and genuinely overlapping-call cases, with explicit legacy behavior.
**Why this is robust:** closes the reported event-to-summary mismatch at the shared
ledger boundary and makes the ambiguous-identity case an explicit contract instead
of using a last-writer assignment that races between calls.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Event delivery and public snapshot are two actual consumers of the same local health ledger. Stored ownership closes their mismatch together. A cross-instance registry adds an unrequested aggregation contract; the per-instance ownership fix has greater verified reach per change and survives such a future registry.
*For future:* —

### Mitigation — Long-term

Introduce a canonical per-account health registry shared across TgData instances,
with an explicit aggregate query API and migration of all old event/snapshot paths.
**Why this is long term effective:** would provide one identity/ownership model for
all clients and consumers, including multi-instance aggregation and session changes.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit cross-instance health aggregation when a concrete consumer requires it. Preserve explicit ownership semantics from the robust fix rather than introducing a last-writer identity fallback.

## Risk3 — the concurrent-identity regression does not force overlap

**Risk**

The test named for concurrent calls can pass even if the two calls run one after
another. Its replies are ready immediately, so neither operation has to yield to
the other. That leaves a gap in the regression protection for identity separation,
even though a separate review probe shows the present implementation handles real
overlap correctly.

`test_concurrent_identity_and_callback_reentry` in test_20_group_operations.py:632
uses gather with senders whose futures are completed in send. Tracing that fixture
produces A:start,A:end,B:start,B:end. The fresh probe holds both resolution futures
pending, verifies both tasks are live, then completes them in reverse order;
222/333 stay correctly paired with their events. That stronger probe currently
lives in work-folder review evidence rather than the product smoke suite.

**Severity:** Low
**Category:** Regression coverage
**Impact:** a future shared-identity race could pass the existing test; no current
runtime attribution failure was found under forced overlap.
**NoobEng:** awaiting an already-completed Future need not hand execution to another
task. gather creates tasks but does not guarantee their operations interleave.
**Affected areas:** test20 concurrency regression coverage.
**Disposition:** record and carry the forced-overlap case into the required re-plan's
regression work. No code/test patch is applied during this critic run.

## Coverage and validation

- Real SDK/public-facade retry exhaustion: two failing outcome-classification cases
  reproduced; join admission remains conservative and counts six attempts.
- Event-to-public-summary stale identity: reproduced with both transports describing
  the same authenticated account222 and a stale cached111.
- True overlap: two pending requests, reversed completion order, correct per-call
  identities. Original fixture's sequential execution independently traced.
- Read/lookup/join shapes, quota persistence/contention/cancellation, local post-ack
  cache/logging containment, privacy, wrapper/batch guards, factory defaults and
  dependency changes were checked against the actual diff and existing evidence.
- Installed Telethon declares Python>=3.5; project runtime syntax was already
  checked for3.7 and executed on3.11.10. No new old-SDK work was introduced.
- Original model/effort uncertainty is resolved from active metadata, not config
  defaults. The interrupted continuation was checked again as Astra/max.
- Existing151 offline passes/3 live skips are retained as historical validation;
  unchanged broad suites were not repeated for this review. These new cases expose
  what that evidence did not cover. No live acceptance or safe-rate claim is added.

Command: `.venv/bin/python devdocs/work/7-group-operations/pr-critic-probes.py`.
All probe assertions completed. “REPRO” lines intentionally demonstrate defects;
the script's successful exit means reproduction succeeded, not that the PR passed.

## Required next state

Keep PR16 draft and issue7 open. Commit/post this review. Under CONTRIBUTING §7.4,
return to task-plan revision3 using this review plus desc.md, then new critic/fold,
implementation, verification, merge check and fresh PR critique on the same PR.
Preserve the earlier plan critic as history. No direct fixes or merge are authorized
by this review verdict; the user's separate merge go-ahead remains required.

## Phase3 selection audit

Two robust/elegant proposals selected as revision3 planning input; no quick fix,
last_resort or forced tradeoff. Risk1 has a real wider class in the existing
message/batch resolvers, but its global API migration exceeds this feature. Risk2
has two current sinks sharing one local ledger; global cross-instance aggregation
is a larger unrequested surface. Both selected fixes survive later generalization.
No risks, severities or proposals were rewritten during selection, and no selected
proposal was applied to runtime code in this review turn.
