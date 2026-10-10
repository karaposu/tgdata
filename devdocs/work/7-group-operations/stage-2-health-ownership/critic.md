---
model: gpt-6-astra
effort: max
---
# REORDER — TEST BEFORE BUILD

Falsifier: actual SDK/Stage1 authentication errors cannot carry neutral-attribution
metadata through an awaited child and ordinary wrapping without changing their
identity, diagnostic verdict or source cleanup outcome.
Affordable now: yes — a local real-SDK/asyncio composition probe, seconds, no network.

Experiment: run `critic_r3_probes.py premise`, which gets an actual sender-built
authentication error through Stage1, annotates the actual escaping object/cause,
forwards it through an awaited child and wrapper, then checks identity, text/cause,
diagnostic classification and completed source cleanup. It does not substitute
a fake health predicate for the not-yet-written emission rule.
Cost: seconds, temporary synthetic sessions, no credentials or live Telegram.
Must precede: step1 — before any plan implementation, including new product tests.
Disqualifying result: metadata is lost/rejected for the actual SDK/tgdata errors,
the original outcome is replaced, diagnostic classification changes, or source
cleanup no longer completes before propagation.
Passing result: exact error/cause metadata survives task/wrapper forwarding, the
same original failure and diagnostic verdict remain, and source cleanup completes.

Result: PASS — 2026-10-10. The actual error and explicit SDK cause kept metadata
through the awaited child and wrapper; the original object/text/cause and diagnostic
`logged out` verdict were preserved, and the source was closed before delivery.

```json
{"same_error":true,"root_and_cause_metadata_survive":true,"explicit_wrapper_retains_marker":true,"diagnostic_verdict":"logged out","source_closed_before_delivery":true}
```

This proves the carrier composition, not the new attribution predicate. The
predicate's acceptance cases remain required during implementation.

## High-level summary

The six-step plan addresses the three rejected PR findings and the new task-hop
case without a global health rewrite. Its central source/data prerequisites have
been inspected and probed. One Medium remains: successful request identity is
collected too late from mutable caller input. Capture immutable names at entry to
the existing client wrapper instead. That adds one narrow change to the already
surfaced factory wrapper; no new request registry or sender architecture is needed.

No open planning/execution blocker. The marker's actual propagation composition
still needs the cheap experiment above before implementation; the planning probe
only annotated the error after its parent had received it. Review ran in-session,
without delegation, against revision3 at530ea36 and unchanged product3d59455.

## Premise Inventory

### 1. Error metadata survives the required composition

**First dependent step:** 4, with step1's new tests depending on the same boundary.
**Waste if false:** attribution steps/tests need a different carrier.
**Test scheduled at:** step4 acceptance; planning observed writable attributes after
delivery, not the full annotated-child forwarding path.
**Cheapest earlier test:** the specified experiment before step1.
**Coverage:** real sender/Stage1/task tests establish error shape and cleanup;
the experiment must establish metadata retention in that actual composition.
It cannot prove the future marker predicate by merely supplying its expected result.

### 2. Caller input still describes the successful RPC after awaiting — falsified

**First dependent step:** 2, then step3 consumes that evidence.
**Waste if false:** both request wait and restriction recovery use the wrong action.
**Test scheduled at:** no mutable-input case in revision3.
**Cheapest earlier test:** mutate a caller list after the real SDK submits a copied
request list and before its future completes; executed in this critique.
**Coverage / output:** `critic_r3_probes.py finding`, using actual SDK and factory:

```json
{"entry":["GetStateRequest"],"wire":"GetStateRequest","recorded_success":["GetHistoryRequest"]}
```

The wrapper-entry snapshot matched the actual sent request; current post-await
observation read the changed list. Normalizing that changed list's names would not
correct the provenance error. No production function was edited in this probe.

### 3. Logical names and cause/context shapes are available — established

**First dependent steps:** 2–4. **Waste if false:** evidence rules need replacement.
**Test scheduled at:** original review and re-plan, both already executed.
**Cheapest earlier test:** already performed real SDK sender/error probes plus
actual Python chains, including namespaced GetMessages constructors and child tasks.
**Coverage:** replan-evidence.md and pr-critic.md give actual outputs. Their
synthetic transport does not prove Telegram's live permission/frozen-account policy;
the plan correctly makes no such claim. Group-result semantics remain explicit.

## Restart Check

| Observed failure | Established mechanism | Revision3 element / required fold |
|---|---|---|
| Wrapped waits alias and fail recovery | Error sees outer wrapper, success sees caller type | Common namespaced leaf key in step2 |
| Identity-only success clears restriction | Nonempty request set stands in for refused action | Stored refused key and matching evidence in step3 |
| New RPC suppressed by old context | Any-ancestor exclusion before classification | Ordered source/marker decision in step4 |
| Child pre-proof failure relabelled as parent logout | Exclusion references stay only in same-task calls | Neutrality travels with exact failure in step4; prebuild propagation probe |
| Caller list mutation supplies a different success | Wrapper rereads original input after awaiting | Medium1 fold: immutable pre-await evidence |

## Inherited Lessons

| Lesson | Ordering / assessment |
|---|---|
| Real SDK dispatch alone does not prove error association | Step1 uses actual sender/error construction before corrective code |
| Identity proof is not action proof | Step2 key precedes step3 matching predicate; negative self/budget cases required |
| Context is not necessarily a cause | Step4 marks explicit causes only and orders incoming traversal |
| Same failure can cross a task boundary | Required experiment before step1, then actual marker tests at step4 |
| Keep the ownership prerequisite bounded | One complete ledger, one request-key scheme, one refusal key, one error marker |

## Medium1 — Mutable caller input can invent successful action evidence

**Risk:** A request list can be changed while the Telegram client waits for a reply.
If health reads that list afterward, it can record a different action as successful.
A wait or restriction on that other action may then be cleared despite no successful
retry of it. Merely making the names more precise does not stop this false recovery.

Revision3 decisionB and step2 collect keys after success. `_AnswerEvidence.__call__`
in connection_engine.py passes the original request object to `health.note_answer`
after its await. Real Telethon `_call` copies a request list before awaiting its
results, while the caller retains and can mutate the original. The executed probe
sent GetState, replaced the caller list with GetHistory while the future was pending,
and observed `_OwnedCall.requests == {'GetHistoryRequest'}` at owned_health.py:39–44.

**Severity:** Medium. **Category:** evidence lifetime / mutable input.
**Impact:** false request or restriction recovery under the right owner but wrong action.
**NoobEng:** the SDK and health observer look at different versions of the same
list. The original list reference is not a receipt for what the SDK sent.
**Affected areas:** client wrapper, health evidence hook, owned request keys,
wait/restriction recovery and source-composition tests.

### Mitigation — Quick

Disable recovery for every batched request, including ordinary safe list calls.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Snapshot immutable logical request keys at wrapper entry, before the first await,
for a scalar request or concrete built-in batch container. Bind the snapshot to
the current owned observation and client; only consume it on full success when
that observation, client and task are still valid. Do not reread caller containers
or consume lazy/custom iterators for recovery evidence. Legacy calls keep their
existing path. Document that internal callers keep individual TLRequest/envelope
objects unchanged during a call, as they already must keep the raw client/session
unchanged. Add the real mutable-list regression. No deep request copying.
**Why this is robust:** captures the concrete data before its lifetime becomes
ambiguous, using the existing wrapper; only names and an in-flight call binding
are retained, with no persistent request trace or new sender layer.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Wait and restriction recovery are two real consumers of the same
success evidence, and one snapshot serves both. Adding a small hook at the existing
wrapper closes the instance with far less extent than instrumenting sender receipts.
*For future:* —

### Mitigation — Long-term

Build source receipts around every actual sender enqueue/completion and correlate
them with higher-level operations, retries, nested verification and partial batches.
**Why this is long term effective:** the logical observation could follow serialized
requests independently of mutable application objects and SDK helper boundaries.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Only a concrete audit requirement beyond the trusted internal source
contract would justify it. It would need its own plan for partial results and retries;
the current immutable-key contract can survive that expansion.

## Other boundaries checked

Restriction replacement must replace/clear its private refused key with the current
account condition; missing keys cannot recover by guess. The plan already states
these requirements, as well as valid-handle, method, owner, generation and no-self
guards. Marker logic remains at emission sites so diagnostic/polling classification
is not disabled. Explicit causes and SDK MultiError members are separate from prior
implicit context. Callback timing/order limits are documented, not extended into
a FIFO/durable queue. Public owned request spelling changes only this unmerged
stage; legacy strings and timing remain regression constraints. No schema change,
new credential data, global registry or extra Telegram request is justified.
