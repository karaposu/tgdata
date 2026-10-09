---
model: gpt-6-astra
effort: max
---
# Fresh PR critique — #7 Stage 2 / PR22

**Gate: REJECTED — 0 High, 3 Medium, 0 Low.**
**Design verdict: IMPLEMENT AFTER FOLDING THESE IN**, through a revision3 re-plan
under CONTRIBUTING §7.4, not patches during this review. The fixed-owner ledger
and private composition remain a suitable boundary; the request/evidence/exclusion
rules need correction before it can be approved.

**Falsifier for approval as written:** run actual SDK error construction using the
request that reaches its sender, then compare failure keys with later success keys;
also try proof-only recovery and a new RPC failure inside an isolated-error handler.
**Affordable now:** yes; all executed below, and all three disprove the implemented
acceptance claims. This is an implemented-diff review: the gate rejects, rather than
deferring an affordable experiment or calling the existing passing suite sufficient.

## High-level summary

The immutable numeric owner works, and the original critic's two selected safeguards
are present. However, actual SDK wrappers make unrelated waits share a key and prevent
matching success from clearing it; a repeated self lookup can erase a restriction;
and implicit Python exception context can hide a separate later legacy RPC failure.
These are three distinct, reproduced Medium findings. They change neither the
verified account boundary nor the reason to split #7 into stages, but the current
evidence predicates are not ready for later group operations.

**Subject:** product `3d59455`, diff against dev `53306df`, PR22 opened at `1625e09`
and review prompt checkpoint `7711e56` (documentation only). This critique ran
fresh in the same warmed session, with no subagent. Original `critic.md` is preserved.
No runtime file or test expectation was changed during review.

Read the folded plan, description, triage, inquiry findings, original critic and
verification with the full affected implementations: owned_health, health, facade,
connection factory, Stage1 handle, budget client, session store and relevant health/
operation tests. Read installed Telethon1.45.0 RPCError, error conversion, RequestState,
MTProtoSender.send/_handle_rpc_result and UserMethods._call. The published PR's
head/base/files were verified against local Git before probing.

## Premise Inventory

### 1. Failure and success use the same request identity — falsified

**First dependent steps:** 1–2, request-scoped storage and recovery.
**Waste if false:** waiting-state assertions and tests claim correctness for a
request representation that the configured SDK does not use on errors.
**Test scheduled at:** prebuild composition plus step4, but those fixtures hand the
SDK a prebuilt error referring to an unwrapped request.
**Cheapest earlier test:** actual sender error conversion after the factory's
`receive_updates=False` policy wraps a request; seconds, offline. Executed now.
**Coverage:** suite33 does run SDK dispatch, but its `fail()` creates
`FloodWaitError(history_request)` and test32's wire strips wrappers before choosing
that response. It therefore supplies this premise instead of observing it. Probe1
uses actual MTProtoSender.send, RequestState and _handle_rpc_result and falsifies it.

### 2. Any post-proof answer means the refused operation succeeded — falsified

**First dependent step:** 1, restriction recovery.
**Waste if false:** a stored restriction can disappear under an unchanged semantic
condition, defeating a future caller's account-health decision.
**Test scheduled at:** step4 checks a bare body, a different method and successful
history; it never repeats self verification in the same named method.
**Cheapest earlier test:** actual Stage1 `verify_account()` after storing a
restriction, with no retry of the refused request; seconds, offline. Executed now.
**Coverage:** Probe2 observes a real GetUsers request admitted to the generic answer
set and the actual recovery predicate clearing the condition. It does not make a
claim about which live operations Telegram currently freezes or restricts.

### 3. An excluded ancestor means the new error is the same failure — falsified

**First dependent step:** 2, scoped enclosing-call exclusions.
**Waste if false:** compatibility isolation suppresses genuine later observations.
**Test scheduled at:** step4 checks wrappers and an independent error raised after
the handler finishes; it does not test a new RPC during that handler.
**Cheapest earlier test:** real Stage1 mismatch followed by a separate real-SDK RPC
failure in its except block, inside an active legacy call; seconds, offline.
**Coverage:** Probe3 executes exactly that sequence. The raw RPC is new, but Python
sets the mismatch as implicit context, and the whole error gets excluded.

### 4. Cleanup and observer-task separation — supported within stated scope

**First dependent steps:** 1 and3. **Waste if false:** lifecycle composition would
need replacement. **Test scheduled at:** prebuild and step4; both executed before
this review. **Cheapest additional test:** two simultaneously entered callbacks
both close TgData; executed as Probe5 with real tasks.
**Coverage:** no deadlock or retained task in that probe. Probe4 additionally shows
that differing cleanup durations can reverse notification arrival order, while
observation timestamps and local state retain the actual order. No FIFO/durable
delivery promise is made; this is a limitation, not another blocking finding.

## Restart Check

| Original observed failure | Established mechanism | Current design / evidence |
|---|---|---|
| Event B, summary A | Mutable identity supplier at both sinks | Fixed owned monitor and explicit query address it; suite33 owner/copy cases |
| Self proof clears group denial | Generic answer treated as group proof | Explicit group assertion addresses that scope; Medium2 finds the related restriction gap |
| Callback cancellation replaces primary error | Awaited observer participates in outcome | Separate delivery after cleanup; suite33 and Probe5 support it |
| Older work clears newer wait | Missing condition generation/order | Start-order guard is present; Medium1 finds incompatible request keys instead |
| Caught RPC leaves only success evidence | Classification only at operation exit | Source-time recording and MultiError leaves address it; sender identity still needs Medium1 |

## Inherited Lessons

| Lesson | Actual ordering / remaining gap |
|---|---|
| Relabeling events is not stored ownership | Fixed ledger precedes facade; satisfied |
| Real SDK composition must precede building on it | Prebuild ran first, but bypassed actual error/request association; Medium1 exposes the non-covering seam |
| Identity proof is not action/access proof | Group semantics are explicit; restriction recovery still conflates them, Medium2 |
| Keep scope small rather than rewriting global health | Four runtime files; proposed corrections remain in the same boundary |
| Observer outcome is independent of operation outcome | Post-cleanup tasks are retained and tested; no new scheduler is justified |

## Medium1 — SDK wrappers corrupt request-scoped waits

**Risk:** A temporary client records a rate-limit wait under the name of a generic
SDK wrapper rather than the action Telegram refused. Successfully repeating the
original action then leaves the wait visible. A shorter wait on a different action
can overwrite the first wait because both now appear to be the same request type.
The health snapshot gives callers incorrect waiting information.

Stage1 sets `receive_updates=False` in connection_engine.py:643–646. Telethon1.45.0
UserMethods._call wraps each outgoing request in InvokeWithoutUpdatesRequest, and
MTProtoSender._handle_rpc_result builds the RPCError with that wrapped RequestState.
`health._request_name` at170–172 takes its outer type, while
`_OwnedCall.note_answer` at owned_health.py:39–44 takes the original caller request's
type. `_recover` at105–111 consequently compares incompatible keys. The second
wrapped wait also replaces the same `_waiting`/`_waiting_tick` entry.

**Severity:** Medium. **Category:** SDK composition / request identity.
**Impact:** stale waits after successful requests and collisions between unrelated waits.
**NoobEng:** the same request has an outer transport representation and an inner
action. The current observer reads the outer one on errors and the inner one on
successes. Its tests construct the error before this wrapping occurs.
**Affected areas:** health request naming, owned call evidence/recovery, suite33 fixture.

**Reproduction:** Probe1 output:

```json
{"error_request":"InvokeWithoutUpdatesRequest","inner_request":"GetHistoryRequest","success_names":["GetHistoryRequest"],"initial_wait_keys":["InvokeWithoutUpdatesRequest"],"wait_keys_after_matching_success":["InvokeWithoutUpdatesRequest"],"wait_seconds_after_other_request":15}
```

The first wait was120 seconds on GetHistory; the other15-second wait was GetState.

### Mitigation — Quick

Ignore wrapped waits or clear every wait on any successful request.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Define one logical-request key for owned failures and successes, unwrapping known
SDK envelopes consistently without mutating the original error. Test actual sender
construction, distinct request waits and matching/nonmatching recovery, including
batched/wrapped forms. Preserve original error/container propagation.
**Why this is robust:** one narrow key rule serves the two concrete observation
paths; it removes the representation mismatch without a request-history registry.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Error keys and successful-request keys are two genuine instances
served by one normalization rule. This closes that class inside the existing owned
boundary; broad transport instrumentation adds extent without needed reach.
*For future:* —

### Mitigation — Long-term

Introduce a transport-wide canonical request/outcome layer for all legacy and owned
calls, retries, envelopes and batching.
**Why this is long term effective:** every observer could consume the same semantic
request record instead of reading vendor representations independently.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit only for a concrete all-client request-auditing requirement;
the logical-key contract can survive that expansion.

## Medium2 — A second self lookup clears an action restriction

**Risk:** After Telegram restricts an operation, the next attempt can merely check
who is logged in and announce that the restriction is gone. It never retries the
refused action. Knowing the account's identity does not establish that the account
can perform an operation Telegram previously restricted.

`_OwnedCall.note_answer` at owned_health.py:39–44 adds GetUsersRequest from a later
`operation.verify_account()` to `call.requests`. `_recover` at112–119 considers
any nonempty request set sufficient when the outer `call.method` matches. It does
not identify whether the refused action succeeded. Initial self proof is excluded
by context timing, but identical proof repeated after the context opens is admitted.
The negative case in test33 at349–358 only covers a body with no request at all.

**Severity:** Medium. **Category:** recovery evidence / semantic contract.
**Impact:** false `ok` event and premature removal of a restriction from the owned snapshot.
**NoobEng:** the outer method label describes what the caller intended to do.
An internal identity check is another request inside it, not evidence that the
intended action actually worked.
**Affected areas:** owned restriction recording/recovery and later admission consumers.

**Reproduction:** Probe2 output:

```json
{"before":"restricted","after":"ok","post_proof_evidence":["GetUsersRequest"],"refused_request_retried":false,"events":2}
```

### Mitigation — Quick

Disable all automatic restriction recovery permanently.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Retain the refused logical request as restriction evidence and require a suitable
successful action to clear it, alongside the existing owner/method/generation rules.
An unrelated identity check must not satisfy that rule; if identity verification
itself was refused, distinguish that concrete case. Specify/test this evidence
contract before implementation, including nested budget verification and handled
failures. Do not infer action success from an arbitrary nonempty request set.
**Why this is robust:** the source already provides the refused request; the owned
monitor needs a bounded evidence predicate, not a generic Telegram permission engine.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* This instance has concrete refused-request evidence already. A wider
capability model has no additional implemented consumer here and would expand a
prerequisite into the redesign the staged approach was meant to avoid.
*For future:* —

### Mitigation — Long-term

Create a semantic capability/evidence model shared by every public and private
operation, expressing what each successful response proves.
**Why this is long term effective:** multi-request domain operations could recover
conditions from explicit capabilities instead of incidental transport activity.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* A later operation with a real multi-request semantic result may need
an explicit evidence assertion; require that concrete case and its tests first.

## Medium3 — An excluded error hides an independent later RPC failure

**Risk:** An enclosing operation handles a refused temporary-account attempt and
then makes a separate request with its own client. If that request fails while the
first error is still being handled, the new health event disappears. The caller
still receives the exception, but its health summary omits a genuine group denial.

`_Call.excludes` at health.py:283–284 searches every ancestor from `_chain`, including
implicit `__context__`. The pre-proof AccountIdentityError is retained by
`isolate_call`; Python attaches it as context to a different ChannelPrivateError
raised by a later legacy-client RPC inside the handler. `_on_error` at377–379 and
`report` at628–630 exclude the new error before classification can recognize its
own fresh signal. The existing independent-error test raises after leaving the
except block and misses this context shape.

**Severity:** Medium. **Category:** exception provenance / compatibility.
**Impact:** silent loss of a separate valid legacy health observation.
**NoobEng:** Python's implicit exception context means "this happened while handling
that", not necessarily "this is a wrapper for that". The exclusion treats those
two relationships as identical.
**Affected areas:** scoped exclusions and both escaping/handled legacy report paths.

**Reproduction:** Probe3 used an ordinary client for account111 and a separate
temporary client verified as222, refused against expected111. The new account111
RPC really returned CHANNEL_PRIVATE. Output:

```json
{"new_rpc":"ChannelPrivateError","implicit_context":"AccountIdentityError","account":111,"events":0,"no_access":{}}
```

### Mitigation — Quick

Disable all enclosing legacy health after an isolated operation, or remove all
exclusions and accept false attribution of pre-proof errors.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Make exclusion/classification distinguish the originating isolated failure and its
wrappers from a fresh RPC signal encountered before that excluded ancestor. Keep
the decision scoped to the enclosing call, with explicit tests for implicit/explicit
wrappers, source-error unwrapping and a separate actual RPC raised inside the handler.
Do not let mere membership anywhere in the context chain suppress the new signal.
**Why this is robust:** it closes the concrete ambiguity at the existing bounded
exclusion seam while preserving both pre-proof isolation and independent reporting.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Both escaping `_on_error` and handled `report` share the same exclusion
decision, so one bounded correction serves both. A whole legacy migration exceeds
this stage and is not required to keep a fresh RPC distinguishable from a wrapper.
*For future:* —

### Mitigation — Long-term

Migrate all legacy health reporting to explicit source-owned observations and stop
using broad exception-chain inference for health provenance.
**Why this is long term effective:** message/discovery/connection wrappers could
report their own source and derived domain findings instead of inheriting incidental
exception context. It needs its own compatibility and migration contract.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit only when legacy migration is explicitly requested. It must
account for actual domain-error translation sites, not assume every exception is RPC.

## Additional executed probes and limits

Probe4 output:

```json
{"callback_order":["ok","banned"],"snapshot":"ok","event_times_retain_observation_order":true}
```

The earlier ban's disconnect was deliberately delayed. The later recovery's
notification arrived first; the earlier event still carried its earlier observation
timestamp. The snapshot remained correct. This matches separate post-cleanup delivery;
consumers must not assume arrival order is state order. It is not a request to add
a FIFO worker or make callbacks participate in source cleanup.

Probe5 output:

```json
{"entered":2,"close_completed":1,"pending_tasks":0}
```

Both callbacks entered before close; one close cancelled the other notification,
both tasks retired, and no self-await/cross-await deadlock occurred. The expected
callback cancellation diagnostic was contained.

Run: `.venv/bin/python devdocs/work/7-group-operations/stage-2-health-ownership/pr_probes.py`
using the workspace's Python3.11.10 and Telethon1.45.0. Five probes completed with
sockets forbidden. The script's assertions deliberately characterize the observed
defects; its exit0 does **not** mean the acceptance contract passes. No live server
permission or frozen-account policy was tested. Existing 424 offline passes remain
accurate for that suite, but do not close the three newly reproduced gaps. No full
suite rerun was needed because product3d59455 was unchanged.

## Gate consequence

PR22 remains draft and unmerged. Under CONTRIBUTING §7.3 any Medium rejects. §7.4
requires a revision3 plan taking these findings as input, then a fresh plan critic,
fold, implementation and both merge gates again. Do not fix findings one by one
in this review or count the archived old PR16 rejection as another Stage2 rejection.
This is the first rejecting PR critique in this Stage2 folder.

No current evidence requires discarding fixed-owner monitors or resuming the old
broad revision3 design. The next plan should correct and test these bounded
evidence rules first. Original plan/critic remain the implementation's blueprint
until that formal re-plan archives/replaces them. Available §9 provenance is the
retained Astra/max session record described in merge-check.md, not a new selector read.
