---
model: gpt-6-astra
effort: max
---
# REORDER — TEST BEFORE BUILD

Falsifier: the real Stage 1/factory/budget/SDK composition hides a caught raw RPC
failure's client/object, or isolated callback cancellation can replace the primary
outcome despite scheduling only after the real disconnect attempt settles.
Affordable now: yes — local Python/Telethon, minutes, no credentials or network.

Experiment: run `prebuild_probe.py` with real Telethon 1.45.0, Stage 1, factory MRO,
budget admission and SDK disconnect. Instrument the request wrapper to observe
outcomes; only replace the network sender. Exercise caught single RPC, nested
identity verification, mixed batch failure, scoped ContextVar isolation, delayed
disconnect, separate callback cancellation and primary-error preservation.
Cost: minutes, local CPU and temporary SQLite/session state, no live service.
Must precede: step 1 — no production edit before this experiment.
Disqualifying result: a health RPC is transformed/lost before the client boundary
or real cleanup/callback composition prevents preserving the primary result.
Passing result: source client and raw error identity are observable, the SDK's
batch container retains its raw failures, contexts reset correctly, and disconnect
settles before isolated notification cancellation with the original outcome intact.

Result: PASS — `prebuild_probe.py` observed the same raw RPC object at its exact
client, nested real budget verification and a retained charge, caught identity
invalidation, actual SDK MultiError leaves, delayed real disconnect completing
before the callback, callback cancellation containment, primary exception identity
and ContextVar reset; 2026-10-09. Telethon1.45.0; network sockets forbidden.
The probe observes local SDK/asyncio composition with synthetic transport, not
Telegram permission policy or the not-yet-written Stage 2 implementation.

## High-level summary

The selected small boundary addresses the reproduced mechanisms and avoids the
old owner-indexed global rewrite. Two Medium risks need folding: caught handle
invalidation must veto recovery, and SDK partial batch failures need leaf observation.
The plan already requires a prebuild check, but its premise is not closed until
that check actually runs. No open planning or execution blocker; no architecture
replacement is proposed. Same-session review, no subagent or live Telegram work.

## Premise Inventory

### 1. Actual request/lifetime composition exposes usable evidence

**Premise:** the client wrapper can observe raw errors even when callers catch
them, and source cleanup can precede notification without joining its outcome.
**First dependent step:** 1. **Waste if false:** steps 1–3 require a different
boundary; the corresponding suite is built around the wrong seam.
**Test scheduled at:** plan prebuild check, not executed at this verdict.
**Cheapest earlier test:** the experiment above, before any implementation.
**Coverage:** five baseline probes and test32 exercise real SDK and asyncio with
synthetic transport. They cover the old failures, not the full proposed composition.
The new probe must observe that composition; a fake client returning the desired
health events is non-covering. Telegram server policy remains outside this stage.

### 2. Handle invalidation and batch exceptions have the read code's behavior

**Premise:** caught verification loss invalidates the handle, and mixed request
failures reach callers as MultiError rather than RPCError.
**First dependent steps:** 1 and 2. **Waste if false:** recovery/source tests would
target the wrong case. **Test scheduled at:** step 4; add both to the earlier probe.
**Cheapest earlier test:** actual Stage 1 verification and SDK list request with
transport-injected responses, minutes. **Coverage:** account_operation.py closes
before raising on auth/identity loss; test32 covers invalidation. Installed SDK
UserMethods._call builds MultiError from per-request RPCError objects; new probe
must run that branch, not manually instantiate a MultiError as its only evidence.

## Restart Check

| Observed failure | Established mechanism | Design element that addresses it |
|---|---|---|
| Event B, later snapshot A | Both sinks ask the mutable primary identity supplier at different times | Step 1 fixed monitor plus step 3 explicit account query |
| Self proof clears group denial | Generic answer tick satisfies legacy group recovery | Step 1 explicit group assertion and step 4 self-only regression |
| Callback cancellation replaces original error | Callback is awaited in the error-reporting path; CancelledError escapes Exception catch | Separate post-cleanup tasks in steps 1/3 |
| Old call clears newer wait | Waiting entries have no checked condition generation | Step 1 start-order and matching-request checks |
| Caught RPC leaves only successful proof | Exit-only classification misses a failure consumed by the body | Step 2 raw source observation and no self-recovery |

## Inherited Lessons

| Lesson | Ordering that satisfies it |
|---|---|
| Relabeling an event does not establish ledger ownership | Fixed complete ledger precedes facade wiring |
| More agreeing fake responses do not prove SDK composition | Required real-code probe precedes step 1; synthetic transport only |
| Group-operation scope must not grow into routing/global health | Steps 1–3 local/private; public group APIs explicitly deferred |
| A successful self lookup is not proof of group access | Recovery predicate precedes future group work; step 4 negative case |
| An observer is not part of the operation outcome | Cleanup/dispatch ordering is built before callbacks are exposed |

## Risk 1 — A caught identity failure can leave old recovery evidence

**Risk:** An operation can discover that its login no longer belongs to the
expected account, catch that error, and finish normally. If the health observer
checks only that the body returned, its earlier proof can incorrectly announce
that a previous ban or logout has ended. The caller sees an apparently recovered
account even though the handle has been permanently disabled.

Technically, `_AccountOperation.verify_account()` closes its handle before raising
AccountIdentityError/AuthRequiredError. The planned `_OwnedCall` starts with proof
evidence, but revision 1 does not explicitly recheck handle validity at successful
observation exit. Catching that exception bypasses the context's failed flag.

**Severity:** Medium. **Category:** evidence/lifetime ordering.
**Impact:** false account or group recovery after a caught invalidation.
**NoobEng:** this handle has stronger lifetime rules than an ordinary client;
successful body completion is not the same as a still-valid verified operation.
**Affected areas:** owned_health recovery, Stage 1 handle consumption, suite33.

### Mitigation — Quick

Treat only escaping identity exceptions as failure.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Require the existing handle's active opening-task check immediately before recovery,
as well as on evidence/assertion hooks. An invalid handle silently vetoes recovery;
the caller's original result/error is preserved. Test caught identity and auth loss.
**Why this is robust:** the source already owns invalidation; reading its existing
validity avoids another state machine and closes this instance permanently.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* No other current consumer needs invalidation subscriptions. The
existing handle check closes this instance with one predicate; the proposed class
does not yet exist, so the size/delicacy gates favor this robust fix.
*For future:* —

### Mitigation — Long-term

Add a reusable invalidation subscription protocol to account-operation handles.
**Why this is long term effective:** multiple future consumers could immediately
discard their cached evidence on source invalidation.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit only if another concrete consumer needs push invalidation;
the current validity guard survives that change and is not throwaway work.

## Risk 2 — A mixed request batch bypasses the raw-RPC catch

**Risk:** The Telegram client can send several requests together and return one
container describing their individual failures. Catching only a single-request
error misses those failures. A caller that handles the container can then leave
health appearing successful even though Telegram rejected one of its requests.

Telethon 1.45.0 `UserMethods._call` raises `errors.MultiError`, an Exception rather
than RPCError, when its list of sender futures contains RPC failures. Revision 1's
`_AnswerEvidence.__call__` hook catches RPCError only. The existing budget wrapper
can forward list requests; the private handle does not forbid them.

**Severity:** Medium. **Category:** SDK error composition/API completeness.
**Impact:** lost conditions and potential inappropriate recovery on caught batches.
**NoobEng:** this is SDK transport batching, not tgdata's versioned message-batch
feature. The container retains the original per-request errors; no guessing from
error text or general exception-chain registry is needed.
**Affected areas:** connection_engine source hook, owned_health, suite33 transport fixture.

### Mitigation — Quick

Document list requests as unsupported without enforcing that restriction.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Observe raw RPCError leaves of the actual SDK MultiError at the same bound-client
hook, deduplicate existing markers and re-raise the same container. Do not infer
recovery from partial successful results. On fully successful lists, retain the
successful request names. Add a real SDK mixed-list regression with a caught error.
**Why this is robust:** it handles the vendor's explicit second error shape in the
existing source seam, preserving identity, lifetime and primary outcome rules.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Single and list requests genuinely share the same client seam, so
one small leaf adapter covers both. A generic trace layer adds unneeded extent
and would broaden this prerequisite into the rejected redesign.
*For future:* —

### Mitigation — Long-term

Introduce a generic per-request trace/outcome layer beneath all SDK calls.
**Why this is long term effective:** a future transport-independent observer could
consume all request results, retries and failures uniformly.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Only a concrete transport-level auditing requirement would justify
that layer; no named additional consumer requires it now.

## Other reviewed boundaries

No schema or persistence change. Imports can remain one-way (owned_health imports
health; facade imports both; engines import only health). Fixed monitor memory is
per observed account within one TgData, without global references. Credentials are
not introduced into events or logs. The planned query copies the existing snapshot.
The callback and group-assertion contracts are intentionally narrow and documented;
they do not promise durable delivery or infer Telegram permissions.
