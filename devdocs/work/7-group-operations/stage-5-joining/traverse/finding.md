---
status: active
model: gpt-6-astra
effort: max
---
# Finding: A bounded joining operation over the merged foundations

## Question

The user asked to implement Stage5 of #7 after merging Stage4. The first four
stages now provide verified temporary accounts, account-owned health, group lookup
and access checks, and persistent join allowance. What should the final joining
operation promise, and how can it use those parts without another broad redesign?

## Finding Summary

- Add one public joining operation with an explicitly expected account and a
  configured JoinBudget. Keep its admission guard inside that owned operation.
- Reuse the existing group-reference rules, including qualified numeric IDs.
  Refuse unsupported direct mutation peers instead of guessing a route or hash.
- Re-verify the owner and commit one claim immediately before each new SDK join
  enqueue. Do not refund failure, cancellation or an uncertain reply.
- Return distinct acknowledged, already-member, pending, payment-required and
  interaction-required outcomes. An error name alone is not enough to identify
  which operation produced it.
- Validate the actual selected SDK's join reply, including the nested payload
  family. Its type annotations do not enforce that automatically.
- Keep metadata as the preflight observation; unknown invite IDs stay unknown.
  Add no mandatory network/cache enrichment after acknowledgment.
- Preserve the existing cleanup, original-error and owned-health rules. A join
  acknowledgment does not by itself prove history is readable.

## Finding

### 1. Build a small public consumer of the existing parts

tgdata already knows how to open a temporary client, apply the account's proxy,
device and session settings, verify the expected account, and close the client.
It also has the durable allowance primitive. Stage5 should connect those contracts
to the two ordinary SDK join requests rather than introduce another account or
storage system.

The selected public shape is a `join_budget` option on TgData and a `join_group`
method requiring `account_id`, just like the other verified group operations.
The caller supplies the already provisioned/configured JoinBudget; the operation
does not choose a “safe” default rate or recreate lost state.

The guard is active for this owned operation. Configuring the facade does not
claim protection for arbitrary raw client calls, external clients or private
transport use. A wider guard would need a separate ownership contract for callers
that do not provide the verified temporary handle.

### 2. Reuse reference resolution, while keeping mutation eligibility explicit

The current resolver accepts handles, invite links and qualified numeric IDs.
Its numeric path already checks peer namespace and this session's cache instead
of guessing an access hash. A new actual-SDK probe confirmed that a resolved
numeric channel with a legitimate zero hash can be joined through the same
input-peer path. A joining-only rejection of all numeric IDs adds a limitation
without simplifying the underlying resolution.

For a direct channel join, use the concrete peer returned by resolution. Do not
send the original handle back through a generic SDK resolver, where it might
refer to something different later. An invite import uses the validated, unchanged
invite token. Result and health labels continue to use the existing normalized
reference, including the hashed invite label.

Preflight can find that the account is already a member or that payment is required.
Those observations need no join request and spend no join attempt. Policy must
still exist; a zero allowance may return an already-member observation but cannot
admit a mutation. A basic group or community without a qualified direct join route
requires an invite rather than a new guessed mutation method.

### 3. Put admission at the request boundary

The actual SDK resolves inputs and handles cached waits before calling its sender.
Its retry loop also calls that sender again for a new request attempt. The
existing read-budget integration demonstrates the correct kind of insertion
point: wrap the sender argument for the relevant SDK call, without replacing the
client's lifecycle sender.

At that point, the joining consumer uses the existing operation handle to verify
the same expected account again. It then calls the synchronous ledger claim and
enqueues only after that call completed successfully. No await belongs between
the committed claim and the sender's synchronous enqueue.

The qualified ledger contract returns None after a successful claim. An incomplete
or asynchronous substitute must not be mistaken for that completed permission.
The formal plan must make the accepted ledger/context and request-shape predicates
explicit rather than accepting any object that happens to have a method name.

This counts new SDK request admissions, not individual transport packets. The
SDK may correct a bad server salt by requeuing the same pending request. The
inquiry exercised that actual handler and observed the same RequestState/future.
Such protocol repair is part of the existing attempt; this feature is not a
packet-rate limiter. Application and SDK-level retries obtain new claims.

The temporary operation retains its merged policy of zero automatic request
retries, flood sleeps and reconnects. Testing the admission seam with an extra
retry enabled is useful qualification; it does not change that production policy.

### 4. Report what the source actually answered

The installed Telethon1.45.0 uses a join-result wrapper with an Ok branch and a
WebView branch. The opened public method pages described an older layer, so they
cannot substitute for the selected SDK's wire shapes.

A frozen `GroupJoin` should contain the verified account, normalized target,
preflight GroupMetadata and a status. The status vocabulary is `joined`,
`already_joined`, `requested`, `payment_required` and `interaction_required`.
Only the first two establish the corresponding positive membership observation.
The other statuses do not establish membership; use an unknown value rather than
a false negative. A WebView result can expose validated bot/query IDs as data;
the library does not open it or run a bot.

Two concrete checks are essential. First, recognized outcome errors must belong
to the exact mutation request. An extra probe made the SDK construct
InviteRequestSentError for an intentionally unexpected GetUsers proof response.
No join ran and no quota was spent. Mapping the exception class alone would have
invented a pending join. The error's request must unwrap to the actual join request;
otherwise preserve the original exception.

Second, validate the Ok wrapper's nested Updates family and the WebView fields
that the result uses. Actual TL decoding accepted an Ok wrapper containing a User
object in the field annotated as Updates. A class name or annotation is not enough
to support a valid success observation.

Ordinary Telegram errors, waits, transport errors and local failures keep their
existing types and meaning. A failed or cancelled call after admission can have
an uncertain remote outcome. That is a reason to retain the charge, not a reason
to automatically retry or return “not joined”.

### 5. Keep acknowledgment separate from later information

The actual SDK does not automatically cache the chats nested inside its new Ok
wrapper. Explicitly processing the nested Updates does populate that cache, as
the probe showed. That proves an optional capability exists; it does not prove
that Stage5 needs to perform it after every join.

The smaller contract performs no added post-ack cache or network enrichment.
The returned group metadata is the observation made before attempting the join.
For an invite preview, its ID may still be unknown after an acknowledged result.
A caller that needs refreshed metadata or read access can explicitly call the
existing lookup/access API afterward.

This avoids making a later lookup failure look like a failed mutation, avoids
guessing the target from a multi-chat updates vector, and adds no result journal.
Normal SDK processing and the existing owned cleanup still apply. The contract
does not promise that arbitrary SDK/local failures before a result reaches the
operation will be converted into success.

### 6. Preserve health and lifetime meaning

The operation's existing owned-health context records actual source failures for
the verified account. Request/account recovery keeps its current source-evidence
rules. Joining must not call the group's read-access recovery assertion merely
because membership was observed or a join was acknowledged: neither contains a
validated history reply.

Use the existing temporary-client teardown unchanged. Original errors survive
secondary cleanup errors, and caller cancellation remains cancellation. Notifications
remain separate and occur after cleanup settles. No new shared identity override,
health registry or shutdown policy is needed for this consumer.

### 7. Carry the evidence into implementation tests

The inquiry ran six initial and three additional probe groups using the actual
factory, account operation, read budget, SQLite join ledger, SDK request dispatch,
TL decoding and RPC error construction. Only the transport replies were synthetic;
sockets, login and code requests were blocked.

Those probes established a viable candidate seam, including stale identity,
changed identity before admission, retry counting, cached waits, preserved final
RPC errors, numeric resolution, response/cache behavior and the two new validation
requirements. They do not qualify an unimplemented public method, live Telegram
acceptance or a restriction-safe rate.

The delivered feature therefore needs its own public-facade tests and all existing
offline regressions. Retain forced overlaps and actual lifecycle behavior; do not
replace them with immediately completed helpers or reuse an old test count as proof.

## Next Actions

### MUST

- **What:** write the Stage5 description and explicit plan, then run fresh critic-d
  and fold its selected mitigations. **Who:** task-impl in this branch. **Gate:** this
  completed inquiry. **Why:** make exact API, request-origin/payload/ledger predicates
  and test cases reviewable before runtime changes.
- **What:** implement and verify the bounded public operation. **Who:** task-impl
  after the plan gate. **Gate:** an implementable critiqued plan and any required
  prebuild experiment pass. **Why:** provide the actual feature rather than leave
  a prototype or contract document as the claimed delivery.

### COULD

- **What:** show a caller example that joins and then explicitly checks access.
  **Who:** docs author. **Gate:** the public result/signature is finalized.
  **Why:** show the difference between joining and read readiness.
  **Depends-on:** MUST “implement and verify the bounded public operation”. This
  COULD is GATED until that delivery exists.

### DEFERRED

- **What:** add optional nested cache/metadata enrichment. **Gate:** a concrete
  consumer requires it and target-correlation/secondary-error behavior is qualified.
  **Why if revived:** improve convenience without making acknowledgment conditional.
- **What:** guard ordinary raw clients or add per-call ledger selection. **Gate:**
  an explicit consumer need and an ownership/accounting-domain contract.
  **Why if revived:** cover additional callers without guessing authority.
- **What:** integrate pool-driven joining or durable reconciliation. **Gate:** a
  separately scoped routing/workflow requirement. **Why if revived:** automate that
  consumer's policy rather than silently embedding it in a primitive operation.
- **What:** qualify live joins. **Gate:** explicit account/group mutation permission
  and an agreed live test plan. **Why if revived:** establish server behavior beyond
  local protocol and failure tests. Earlier read-only group permission is insufficient.

## Reasoning

The chosen assembly combines a facade-configured allowance, the existing resolver,
a guard confined to the verified operation, portable outcomes and no added post-ack
enrichment. It meets the user's concern about a fundamental design mistake by
keeping authority, admission and source evidence explicit instead of patching labels
after the fact.

Every generated alternative is accounted for:

| Alternative | Result and reason |
|---|---|
| Factory-wide join guard | Not selected: ordinary raw callers require a separately defined expected-owner policy |
| Facade-configured owned join | Selected: fits existing caller shape and limits integration extent |
| Per-call ledger argument | Coherent alternative, lower priority without a caller needing multiple accounting domains |
| Generic read/join quota framework | Not selected: different settlement lifecycles and wider accepted-code changes lack a present need |
| Small operation-local sender adapter | Selected with completed-claim/context/request predicates; actual composition was probed |
| Lower packet-level allowance | Rejected: changes admitted-attempt policy into transport shaping |
| Mandatory post-join lookup | Rejected as success condition: later failure cannot erase prior acknowledgment |
| Portable qualified result | Selected with exact RPC-origin and payload validation, not type/name-only inference |
| Raw SDK result as public contract | Not selected: callers would reconstruct the operation's interpretation; original operational errors still remain original |
| Optional nested cache processing | Feasible, but no concrete consumer requires its extra failure/correlation path now |
| No added post-ack enrichment | Selected: metadata origin/unknowns are explicit and follow-up lookup already exists |
| Durable recovery journal | Rejected here: recorded acknowledgment cannot prove current membership or justify reusable mutation permission |
| Old test suite as new acceptance | Rejected: historical observations do not establish the new composition |
| New actual-SDK public-path tests | Selected: qualify the delivered code and preserve evidence limits |
| Live-only acceptance replacing offline tests | Rejected: live and local tests answer different questions; a later authorized live test remains useful |
| Handles/invites only | Coherent narrower alternative, but qualified numeric resolver reuse avoids a new inconsistency |
| Later pool consumer | Retained as a future interface use, not new routing scope |

The critique refined source interpretation rather than expanding architecture.
Its extra probes show why an apparently helpful catch or a familiar constructor
name can still be wrong. Those exact distinctions belong in the plan and tests.

## Open Questions

### Monitoring

During implementation, measure whether guard composition preserves existing
read-budget/owned-health behavior and ordinary client defaults. Unexpected changes
reopen the relevant predicate rather than justify a global rewrite.

### Research Frontiers

Live joining acceptance, raw-client ownership policy and future routing/reconciliation
need their own concrete requirements or permissions. None is a hidden blocker to
this bounded offline implementation.

### Refinement Triggers

Revisit no-enrichment if a real caller cannot use the explicit follow-up lookup and
requires a canonical joined-room ID from one operation. Revisit target breadth if
the current namespace/cache rules fail a real numeric joining case. Revisit the
sender boundary when upgrading the selected SDK, using actual dispatch probes.

## Source Input

```text
after this start $task-impl stage 5
```
