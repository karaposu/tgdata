---
model: gpt-6-astra
effort: max
---
# #7 Stage5 — Joining, revision 1

### What is the task

Add a public owned-account joining operation using the merged temporary lifetime,
group resolver, owned health and JoinBudget. A configured caller gets a truthful
portable outcome while each new SDK mutation attempt is admitted for the verified
owner. Keep existing reads/raw-client behavior intact and add no post-ack workflow.

### Huge Hard Blockers

#### Planning Blockers

None identified. Description inherits none. The completed inquiry established the
bounded consumer contract. Actual SDK/SQLite probes precede this plan: wrapped
results/cache behavior, stale/changed identity, send order, cached waits/retries,
final error identity, protocol requeue, numeric peer reuse, misleading proof RPC
names and malformed nested payloads. A further planning probe confirms that the
SDK error's InvokeWithoutUpdates wrapper retains the exact original mutation
request object. Evidence is in contract_probe.py and evidence/*.txt; none is
claimed to qualify the still-unimplemented facade.

#### Execution Blockers

None for local implementation/verification. Live joining needs separate account/
group mutation authorization and is outside this delivery, not a delayed required
implementation step. Stages1–4 are already merged at devf15f1a8.

### How this implementation moves toward desired state

The new facade captures one configured ledger and enters the existing expected-owner
context. It validates policy, resolves the target, and may return a nonmutating
observation. For a needed mutation, a small SDK _call adapter verifies again and
claims at sender enqueue. A domain helper interprets only qualified source results.
This avoids the old broad branch's identity fallback and error relabeling, and avoids
new caches, journals, refunds or automatic follow-up RPCs.

### High-Level Summary

| Step | Description | Output |
|---|---|---|
| 1 | Add portable outcome and reply interpretation | Frozen GroupJoin and exact source-outcome predicates |
| 2 | Add bounded per-operation join admission | Small join_client adapter, inactive on ordinary clients |
| 3 | Connect the facade and factory | join_budget option and join_group through existing owned lifetime |
| 4 | Qualify the actual public composition | New test36 with real SDK/SQLite and forced fault/overlap cases |
| 5 | Export and document the contract | Package exports, README and accurate group/budget docs |
| 6 | Run verification and record delivery | Product and separate work commits, pushed branch, truthful #7 status |

## Step 1 — Portable outcome and bounded interpretation

### Proposed changes

Extend `tgdata/group_operations.py` without changing existing lookup/access behavior.
Add frozen GroupJoin(account_id, target, group, status, bot_id=None, query_id=None).
`group` is the existing GroupMetadata from preflight, including None IDs on previews.
`member` returns True for joined/already_joined and None otherwise. `to_dict()` returns
fresh plain data with nested group.to_dict(), all fields and member; no raw entity,
access hash, invite token or client. Large IDs/query IDs remain exact Python integers.

Add `_join_group(operation,target)`:

1. `lookup,peer = await _resolve(operation,target)` using the current parser/resolver.
   Do not add generic get_entity calls, rewrite numeric grammar or catch its source
   failures as reference errors.
2. If lookup.member is True, return already_joined with no mutation. If
   lookup.requires_payment is True, return payment_required with no mutation.
3. For invite targets construct ImportChatInviteRequest(target.value). Otherwise
   require InputPeerChannel and group.kind != community; reject an absent/basic/
   unsupported direct peer with GroupReferenceError suggesting an invite. Build
   JoinChannelRequest(InputChannel(peer.channel_id,peer.access_hash)), preserving
   the already observed peer/hash (including0). No second handle resolution.
4. Await this one logical request. Catch RPCError only around this await. Translate
   USER_ALREADY_PARTICIPANT → already_joined, INVITE_REQUEST_SENT → requested, and
   STARS_PAYMENT_REQUIRED → payment_required ONLY when error.request unwraps to
   this exact request object. Use the Telegram name helper for the generic1.45
   payment error. Otherwise re-raise the original exception object.
5. ChatInviteJoinResultOk is joined only if its updates is one of the installed
   Updates-family classes: UpdateShort, UpdateShortChatMessage, UpdateShortMessage,
   UpdateShortSentMessage, Updates, UpdatesCombined, UpdatesTooLong. Do not inspect
   nested chat vectors for target metadata or explicitly cache them.
6. ChatInviteJoinResultWebView → interaction_required with bot_id a non-bool signed64
   positive integer and query_id a non-bool signed64 integer (zero/negative allowed).
   Copy only those fields; do not run the bot, request a URL or expose users.
7. Other responses or invalid used fields → GroupResponseError. Original waits,
   auth, transport, budget/local errors and cancellation still propagate. A
   post-admission failure/invalid reply does not refund usage or prove no mutation.

Use the request-leaf predicate from step2 for exact error origin; if origin cannot
be interpreted safely, preserve the original RPC rather than map it. No extra
RPC/cache work follows a validated acknowledgment. Source values returned by
Telethon before this helper's interpretation still undergo normal SDK processing;
this is not a promise to override SDK failures before a result reaches the helper.

### Output

One portable result type and one operation helper with explicit outcome semantics.

### Safe in nature

False — extends the shared group domain module; existing helper behavior must remain unchanged.

### Peripheral concepts

GroupMetadata, normalized target labels, selected TL schema, original error provenance.

### Hardness Lvl

4

## Step 2 — Admission at the actual SDK enqueue

### Proposed changes

Create `tgdata/join_client.py` with `JoinClientMixin`, a private `_JoinSender`,
request-origin helpers, and local `UnsupportedJoinRequest(JoinBudgetError)`.
The new module depends on the standard library, Telethon and existing join budget,
not on the facade/group domain/connection engine or health storage.

Define a bounded join-leaf classifier:
- Accept the exact supported JoinChannelRequest/ImportChatInviteRequest families.
- Unwrap only InvokeWithoutUpdatesRequest, including the wrapper the selected SDK
  adds automatically for these owned clients. Bound nesting at8 and refuse cycles/
  over-depth with UnsupportedJoinRequest.
- Unknown wrappers containing a recognizable join, or an unknown request advertising
  the join-result family, refuse. Ordinary scalar metadata is not a join.
- While the operation's join marker is active, SDK root batches/list-like requests
  refuse without consuming them. The public operation uses only scalar requests;
  ordinary unmarked clients retain their existing batch behavior.

JoinClientMixin._call returns directly through super when `_tgdata_join_budget`
is None. When active, classify the scalar request. For a join, require the client's
existing `_tgdata_account_operation` and verify that operation.client is this client
(which also enforces current-task/live-handle ownership), then wrap only the sender
argument passed to super()._call. Never replace client._sender.

_JoinSender captures sender/client/operation/budget/original join leaf. Each send:
1. Confirm its actual SDK request unwraps to the captured join object.
2. Await operation.verify_account(); check operation.client still identifies the
   guarded client and the request still has the captured leaf.
3. Call budget._claim(verified_id) synchronously. Only None return is completed
   permission. Unexpected/awaitable returns raise JoinBudgetConfigError before send;
   close an unstarted native coroutine when possible to avoid a warning, preserving
   the local refusal if that hygiene fails. Do not await/cancel arbitrary tasks.
4. Immediately call underlying sender.send with the same request/ordered flag,
   then await its future. No await between claim and enqueue. No refund/settlement.

The origin helper compares the bounded unwrapped error request by object identity,
not class/name or equal parameters. Unsupported/unreadable origin returns false,
preserving the original RPC; caller cancellation is explicitly re-raised before
generic metadata catches for Python3.7 compatibility.

Add a small synchronous preflight-policy check for a configured JoinBudget instance:
status(account_id) must return JoinBudgetStatus for that exact owner. Reject invalid/
awaitable results locally (same coroutine hygiene); do not use remaining as reserved
permission. Qualified real ledger behavior remains unchanged. Other backend protocols
are not introduced. All adapter errors inherit the context-suppressed local budget base.

### Output

A small opt-in internal guard, tied to the verified handle and actual request identity.

### Safe in nature

True before wiring — new internal module; no existing execution path uses it yet.

### Peripheral concepts

Telethon _call/sender.send, same-task ownership, synchronous claims, cancellation, SDK envelopes.

### Hardness Lvl

4

## Step 3 — Facade and factory composition

### Proposed changes

In `tgdata/connection_engine.py`, add JoinClientMixin to _client_class between
_AnswerEvidence and BudgetClientMixin. Initialize each constructed client's
`_tgdata_join_budget = None`. Do not add an engine-wide ledger option or change
ordinary client settings, _account_operation policies, auth or disconnect.

Append optional `join_budget=None` after current TgData constructor arguments in
`tgdata/tgdata.py`; keep the ledger on the facade. Add:

```python
async def join_group(self, target: Union[str, int], *, account_id: int) -> GroupJoin:
    ...
```

Parse target, validate expected account using the existing helper, and capture/
validate the configured JoinBudget before any client is opened. Enter
_account_health_operation(account_id, 'join_group', reference.label). Check policy
for the freshly verified owner before group requests, activate that client's join
marker, invoke the helper and clear the marker in finally using the saved client
reference. No call to observation.confirm_group_access: membership is not read proof.

No get_join_budget convenience method is needed; the caller already owns the local
ledger. No public _reported decorator: the existing owned context handles isolation,
source health, notifications and lifetime. Do not register local join errors as
health verdicts. A caught closed/foreign operation cannot grant a new send.

### Output

The public join operation executes on exactly one verified temporary client.

### Safe in nature

False — constructor/public API and shared dynamic client MRO change; legacy regressions required.

### Peripheral concepts

Factory/session/proxy/device policy, owned-health observation, public signatures, read-budget mixin.

### Hardness Lvl

4

## Step 4 — Public behavior and failure tests

### Proposed changes

Add `tgdata/smoke_tests/test_36_group_join.py`, ordinary python -m entry point.
Reuse test32/33 fixture machinery and test34 TL Reply decoding, not its send function
that intentionally forbids joins. Replace only the network boundary; real connect,
dispatch, request serialization, RPC error construction, session backends, owned
health and SQLite JoinBudget/ReadBudget run. Block sockets, start and code requests.
No git/history/work-folder dependency. Use unique temporary files/synthetic accounts.

Cover these acceptance groups, with actual count measured after implementation:
- Public signature/exports; immutable result/fresh JSON dict; large IDs and signed
  query IDs; normalized handles/invite privacy/numeric peers.
- Missing/invalid budget, invalid target/owner before client creation; missing policy
  and invalid synchronous policy/claim returns; zero cap with no-op membership and
  required-mutation refusal; no implicit provisioning or guessed default.
- Expected222/cached111/actual222 bills222; expected111/actual222 refuses before group
  work; identity changes after preflight but before admission refuse before claim/
  send. Missing/revoked authentication never prompts, including interactive_login=True.
- Lookup membership/payment no-op; fresh handle and known numeric pinned peer/hash0;
  ambiguous/missing numeric cache, basic/community unsupported direct join; supported
  invite import for preview/peek forms. Invalid lookup/source response fails closed.
- Both valid Ok request paths, all allowed Updates roots, malformed outer/nested
  response, WebView IDs and all three recognized RPC outcomes. Assert exact mutation
  request origin; same-shaped foreign request, proof/metadata RPC or unreadable
  origin never becomes a join result. Other server/flood/auth/transport/local errors
  keep their type/object, including final SDK error after zero retry policy.
- Trace fresh self → committed claim → real enqueue, no intervening await; cached
  waits cost0; controlled probe-only extra SDK retry costs per actual new enqueue.
  Batches/unknown wrappers/family/depth errors refuse while active; unmarked clients
  and scalar metadata keep prior behavior. Closed/foreign client/task cannot claim.
- Actual ledger missing/corrupt/zero/exhausted state, failed and cancelled source
  attempts, and failure after committed claim retain conservative usage. Read budget
  remains unspent by metadata/joins; file/store sessions and proxy/device settings
  survive. Raw clients remain outside the public-operation guard.
- No post-ack lookup or nested cache processing. Returned metadata is preflight;
  missing invite ID stays None. Do not claim live membership from the fake transport.
- Success/failure/cancellation with delayed/failed disconnect and callback errors;
  original outcome preserved. Forced overlapping joins across owners plus same-owner
  shared-cap competition. Source health names the fixed account; join results never
  clear prior read denial; actual source request/account recovery keeps current rules.

Native Python3.7 is not available here; check grammar and use clearly labeled
Exception-derived cancellation compatibility fixtures only where new conversion
catches require them. Do not claim a native old-runtime run. Keep Stage3/4 accepted
Lows unchanged; malformed inherited lookup cases need only fail closed before join.

### Output

Actual delivered-composition coverage, distinct from the exploratory candidate probes.

### Safe in nature

True — offline synthetic source and temporary databases only.

### Peripheral concepts

Real SDK fixtures, serialization/correlation, process-local concurrency, storage, owned callbacks.

### Hardness Lvl

4

## Step 5 — Exports and public documentation

### Proposed changes

Export GroupJoin and UnsupportedJoinRequest from `tgdata/__init__.py`.
Update README's standalone-foundation text to describe the actual bounded integration.
Add `docs/group_joining.md` with configuration and expected-account example; input
eligibility, policy/no-op rules, all statuses/fields, source-origin/error behavior,
preflight metadata, no automatic payment/interaction, cancellation/uncertainty,
no refunds, per-SDK-attempt versus transport repair, and raw-client scope.

Update `docs/join_budget.md` to link its new consumer without changing ledger semantics;
`docs/group_operations.md` and `docs/account_operations.md` link the new method and
retain their existing lookup/read/lifetime claims. Add test36's measured count and
offline limits to the smoke-test README. Examples use a caller-supplied chosen cap,
not a purported Telegram-safe recommendation. Optional explicit check_group_access
after joining demonstrates that membership and read readiness are separate.

### Output

Discoverable API whose documented guard and result boundaries match implementation.

### Safe in nature

False — public imports and behavioral documentation are compatibility surfaces.

### Peripheral concepts

Package exports, examples, account/group/budget contracts, privacy labels.

### Hardness Lvl

2

## Step 6 — Verify and record

### Proposed changes

Run new36 first; run all supported offline suites12–19,22–30,32–35 plus36 with
normal module entry points. Explicitly absent config for12/13 keeps their3 live
checks skipped; no old live suites or unmerged31. Current baseline529 actual groups
includes35; report measured new total. Run daily-continuation and backfill new/
restart demos. Compile tgdata/examples and AST-check Python3.7 grammar. Export the
product tree without .git/work documents and run36 to prove tests are self-contained.
Check whitespace and scoped diff. No live Telegram actions.

Commit code/tests/public docs together; commit verification.md/HANDOFF.md and work
evidence separately. Record deviations and any small nonarchitectural verification
fixes; never weaken expectations. Push branch and tick committed steps on #7.
Leave PR/merge gates pending later requests. The original checkout, duncan, guide,
old broad branch, Stage4 ledger and health storage remain outside this change.

### Output

Verified Stage5 implementation on its own branch, ready for separate review.

### Safe in nature

False — prescribed commits/push and issue updates in the authorized workflow.

### Peripheral concepts

Regression baseline, SDK/runtime support, archive-only work records, staged issue status.

### Hardness Lvl

2
