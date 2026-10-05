---
model: unknown
effort: unknown
---

**IMPLEMENT AFTER FOLDING THESE IN**

Falsifier: authorized live Telegram evidence that a supported join acknowledgment
or successful bounded history response does not establish the documented operation
outcome, invalidating the result contract rather than one implementation detail.
Affordable now: no — no designated live accounts/groups or mutation authorization.
The affordable SDK/session/health falsifiers were run before this verdict; their
observations support the architecture and expose the three in-shape risks below.

# High-level summary

Three Medium findings, no Highs. Preserve the seven-step architecture. Fold:
post-ack cache/projection failure containment; local numeric/parser error isolation;
and task-local authenticated identity for ephemeral health events. Existing
read-budget suite passes (28 groups), as do both real SDK/session probes. These
are supporting evidence, not proof of the not-yet-written join implementation.

## Premise Inventory — ranked by waste if false

1. **Premise:** actual SDK join dispatch revisits sender.send on retry, and fresh
   self lookup provides authoritative identity independently of cached self.
   **First dependent step:**3. **Waste if false:**3–5, sender/facade/test design.
   **Test scheduled at:** pre-plan probe, then regression step5.
   **Cheapest earlier test:** real UserMethods._call with recording sender and
   supplied transport, <1s, no account required. **Coverage:** RUN in
   probe_group_seams.py: two real retry sends; fresh222 vs cached111. Supplied
   error/reply does not prove server behavior, but SDK retry control is observed.
2. **Premise:** Telethon1.45.0 consumes wrapped join results/cache differently
   from older method-page descriptions. **First dependent step:**1/4.
   **Waste if false:** result projection and engine work. **Test scheduled at:**
   pre-plan probe plus step5. **Cheapest earlier test:** actual TL roundtrip and
   MemorySession processing, already run. **Coverage:** actual types/bytes and
   nested-cache observation; cache write failure also reproduced with real
   SQLiteSession after removing its temporary parent directory.
3. **Premise:** separate SQLite transactions can serialize account claims across
   processes. **First dependent step:**2. **Waste if false:**2/3/5.
   **Test scheduled at:** existing test18 process_claims before implementation,
   new join-specific contention step5. **Cheapest earlier test:** actual existing
   SQLite admission concurrency (~seconds), RUN. **Coverage:** real processes/
   file locking; this does not test a future JoinBudget's SQL or claim count.
4. **Premise:** metadata answers are insufficient group-read proof and existing
   health identity can reflect the wrong cached account. **First dependent step:**4.
   **Waste if false:** narrow health extension. **Test scheduled at:** pre-plan/
   critic probes. **Cheapest earlier test:** actual HealthMonitor plus factory
   client, RUN. **Coverage:** metadata clears prior denial; fresh222 still emits
   cached111; real missing session-cache ID inherits outer ChannelPrivateError.
5. **Premise:** Telegram's documented acknowledgment, approval-request and history
   outcomes retain their semantic meaning. **First dependent step:**4.
   **Waste if false:** public outcome contract. **Test scheduled at:** no live
   test in authorized scope. **Cheapest earlier test:** live designated group
   and account, not available/authorized. **Coverage:** installed schema and
   official method semantics; scripted replies are explicitly NON-COVERING for
   live server behavior. Preserve this evidence limit; do not claim live success.

No affordable earlier test remains scheduled after its first dependent step.
Rolling24h is a chosen API policy, not a stochastic assertion. No OPEN planning
or execution blocker is inherited. Exact model/effort availability and later
merge go-ahead remain the known process constraints, not risk items.

## Restart Check

This is a feature, not a restart of a failed #7 implementation. Relevant observed
prior mechanisms are nevertheless carried: #6 local filesystem errors inherited
RPC context → local error isolation; #6 cleanup masked primary download failure →
acknowledged outcome/primary failure precedence. The plan handles the same local
error principle in ledger code but misses two new manifestations below.

## Inherited Lessons

- Wrapper truthiness is not membership: pre-plan actual TL probe, step1 statuses
  and step4 mapping before any final implementation claim.
- A helper call is not one send: pre-plan retry probe, step3 admission before
  step4 mutations; no uncertainty refund.
- Metadata is not readability: pre-plan health probe, step4 history proof and
  separate recovery control, then public composition tests.
- Local errors are not Telegram verdicts: step1/2 local errors are explicit;
  Risk2 closes the remaining native-resolution gap at step4.
- No fallible enrichment should erase acknowledged work: step4 prohibits
  post-ack network work; Risk1 extends this to fallible local cache work.

## Risk 1 — local enrichment can turn acknowledged joining into an error

**Risk**

After Telegram has accepted a join, the library tries to remember returned group
details. That local write can fail even though the account has already joined.
If the write's error escapes, a caller sees failed joining and may retry a change
that already happened. Avoiding a second network request does not prevent this.

Step4 of plan.md calls session.process_entities(reply.updates) after a
ChatInviteJoinResultOk. Telethon's ordinary process_entities(reply) sees no direct
chats on that wrapper. The added nested pass can open/write SQLiteSession storage.
probe_plan_edges.py reproduces OperationalError there after wrapper processing
succeeds. Projection of optional returned chats is similarly auxiliary to the ack.
The plan does not specify containment at this boundary.

**Severity:** Medium
**Category:** Outcome integrity / local storage
**Impact:** acknowledged join appears failed; duplicate retry and unnecessary charge.
**NoobEng:** Telethon automatically caches direct entities, but the new wrapper
requires an explicit nested pass. That pass occurs after the irreversible remote
result and cannot decide whether the join succeeded.
**Affected areas:** group_operations.py join projection; stored/file sessions.

### Mitigation — Quick

Skip caching and returned metadata entirely.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Construct acknowledged status from the reply first. Make nested cache/projection
best effort under a narrow Exception handler; on failure log type only and keep
preflight metadata. Do not report that auxiliary local failure as Telegram health.
Cancellation remains cancellation; the attempt stays charged. Test real local
cache failure after an Ok response and empty/ambiguous updates.
**Why this is robust:** preserves the remote outcome for every local enrichment
failure in this path without weakening pre-send validation or swallowing RPC errors.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* No other implemented membership-mutation receipt path exists; the class claim has no second instance. Robust closes this acknowledged-result boundary in one module with no new subsystem.
*For future:* —

### Mitigation — Long-term

Create a general remote-operation receipt and deferred-enrichment subsystem.
**Why this is long term effective:** could separate confirmed effects from optional
local projections for multiple mutation APIs with resumable enrichment.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit a receipt/enrichment framework only when another mutation API needs durable resumable enrichment.

## Risk 2 — native lookup errors can become false group health events

**Risk**

A caller may ask for a locally unknown group while handling a previous Telegram
error. The native lookup exception remembers that older error as its context.
The library's health observer follows the context and can blame Telegram for the
new local lookup failure, even though no request for that group was sent.

Step4 says numeric resolution errors remain explicit, but does not translate
ValueError from session.get_input_entity/get_entity. health.classify follows
__context__ unless suppressed. probe_plan_edges.py reproduces a missing numeric
cache row's ValueError classified as NO_ACCESS from an unrelated outer
ChannelPrivateError. urlsplit and local input-peer conversion have the same native
error-provenance surface; GroupReferenceError suppresses it only if actually used.

**Severity:** Medium
**Category:** Diagnostic provenance
**Impact:** false denial events, misleading retry/account decisions, misleading logs.
**NoobEng:** Python attaches the active handled exception automatically. Tgdata
intentionally follows wrapped Telegram errors, so local failures need an explicit
boundary rather than blindly retaining that automatic context.
**Affected areas:** group_operations.py parser/numeric resolution/input-peer conversion;
health consumers of new operations.

### Mitigation — Quick

Disable health reporting for numeric group operations.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Resolve numeric references through client.session.get_input_entity first, translate
missing/ambiguous/cache native failures into sanitized GroupReferenceError (or
GroupOperationError for storage), then fetch the resolved peer entity. Translate
native parser/conversion validation errors at their local boundary; preserve real
RPC/network exceptions. Catch health denials only if the actual outer exception
is a Telegram RPC error. Test calls inside unrelated RPC handlers.
**Why this is robust:** each local decision establishes its own provenance; an
incidental context cannot create a denied value or event, while real server errors
remain unchanged and observable.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* batch_files.py is another local-versus-RPC provenance instance, but file operations and entity validation need different origin boundaries. A universal rewrite would widen scope; explicit local translation closes this path and survives a later provenance redesign.
*For future:* —

### Mitigation — Long-term

Replace health exception-chain inference with explicit origin tagging throughout
all engines and SDK call boundaries.
**Why this is long term effective:** would require every diagnostic source to
identify remote versus local origin consistently across old and new methods.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Explicit origin tagging across old engines is a separate improvement if further concrete false-health incidents justify its migration cost.

## Risk 3 — ephemeral health can name a stale primary account

**Risk**

The new operations open a short-lived client, but account health currently reads
the remembered identity of the persistent client. An event can therefore name an
old account or no account even after the short-lived client has authenticated a
different identity. Correct allowance charging alone does not fix that report.

TgData._health_identity reads connection_engine._primary_client._self_id, not the
client owned by step4's ephemeral operation. The SDK does not replace a nonempty
cached self ID on get_me. probe_plan_edges.py observes fresh account222 with event
user_id111. Mutating a global facade identity for the operation would race across
concurrent ephemeral calls and callback reentry.

**Severity:** Medium
**Category:** Account attribution / concurrency
**Impact:** health consumers may act on the wrong account's denial or restriction.
**NoobEng:** per-send billing and event identity are separate paths. The event
needs identity attached to its own asynchronous operation, not the last client
that happened to update a shared object.
**Affected areas:** health.py _Call/_event, facade new group methods, fresh-ID helpers.

### Mitigation — Quick

Always omit user_id from the new operation events.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Add an opt-in task-local account override to HealthMonitor.call/_Call, initially
unknown for new ephemeral operations. Acquire fresh self identity on the opened
client before group resolution; update that call's override. A nonthrowing
health.note_account helper updates only an opted-in current owned call. Invoke
it from fresh read/join identity helpers too so later sends stay accurate. Events
use attributed call override; old callers/snapshots keep existing default identity.
Test auth failure before identity, stale primary, concurrent calls and reentry.
**Why this is robust:** identity travels with the same context/task as the event
and never relies on or mutates cached primary state.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Existing persistent methods also use primary identity, but migrating their context contracts changes established behavior. The opt-in call override has the best reach/extent for concurrent ephemeral calls and remains useful in a later general migration.
*For future:* —

### Mitigation — Long-term

Migrate every engine to operation-owned identity contexts, removing fallback
primary identity entirely.
**Why this is long term effective:** would unify attribution for every current
and future operation, including old persistent-client helpers.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Migrate old engines only with an explicit identity-attribution task and regression contract; the new override can be reused.

## Verification evidence

probe_group_seams.py: SDK wrapper/cache/retry/fresh-self/no-retry/health observations
pass; probe_plan_edges.py: all three counterexamples reproduced with actual SDK,
SQLiteSession and health classifier, sockets blocked. Initial missing-ID probe
used a permissive transport fixture that returned a user for every request; it did
not reproduce the intended local boundary. Corrected to call the actual session
cache (the proposed numeric precondition), then reproduced the native-context issue.
This is probe correction, not changed runtime code or changed test expectations.
Existing test18 passes 28 offline groups; new feature code remains unwritten.

## Selection audit

Phase3 selected three robust/elegant proposals, no last_resort. No external
blocker forced a lesser tier. Risk1 has no second genuine mutation receipt
instance; Risk2 has file/validation provenance instances but no single small
mechanism that fits both without origin-specific boundaries; Risk3 broad
identity migration would exceed the current operation contract. The selected
fixes survive any future class-wide work. Only selections/notes changed in this
pass; evidence count corrected to the actual 28/28 test18 result.
