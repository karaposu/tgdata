---
model: gpt-6-astra
effort: max
---
# #7 Stage 2 implementation plan — revision 4

**Critic folded:** 2026-10-10 — 1 selected robust mitigation (3 steps changed, 0 added).
**Status:** plan critique and required prebuild experiment passed; implementation
follows this folded revision. Product3d59455 remains the rejected baseline on draft
PR22 until the new implementation is verified. This is not PR approval.
**Inputs:** `desc.md`, rejecting `pr-critic.md` atb9a8a5d (Medium1–3), its executed
probes, `replan-evidence.md` and the additional planning probes. Original revision2,
original plan critic/prompt and merge check are preserved under `archive/round-1/`.
The archive/evidence checkpoint is2509a1f; the extended task-hop probe accompanies
this revision. Only one distinct Stage2 PR review has rejected this branch.

### What is the task

Complete the Stage 2 prerequisite that makes health observations and recovery
belong to a verified account. Keep the fixed-owner ledger and Stage1 lifetime,
but define evidence precisely enough that SDK wrapping, repeated identity checks
and Python exception context cannot change which condition an observation affects.
Later group operations must be able to consume this boundary without rebuilding
identity, recovery or notification handling.

### Huge Hard Blockers

#### Planning Blockers

None identified. The description has none open. The PR review established the
three mechanisms; planning executed additional SDK request/namespace and Python
exception/task probes. The necessary identity and failure information is available
locally. The concrete rules below are decisions for the next critic to challenge,
not unresolved questions disguised as assumptions.

#### Execution Blockers

None external. Stage1 is merged at53306df; Python3.11.10 / Telethon1.45.0 and offline
fixtures are available. No account, login, live Telegram group, second machine or
unmerged #17 dependency is required. The fresh critic, prebuild carrier experiment
and selected fold are complete; `critic.md` records the PASS before any plan step.

### How this implementation moves toward desired state

The retained architecture has one fixed monitor per verified account, the existing
factory source hooks, the private facade and notifications after source cleanup.
Re-plan the evidence feeding that architecture around two concrete identities:

- **Logical request identity:** a known SDK envelope is not the action it carries.
  Failure and success use one namespaced leaf-request key. Restrictions remember
  which action was refused and require evidence for that action.
- **Failure identity:** a forwarded exception is not every error that subsequently
  occurs while handling it. Attribution neutrality travels on the originating
  failure, while an independently produced RPC error retains its own observation.

This replaces the broad nonempty-success test and the ambient call's exclusion
list. It does not add global ownership storage, a request history, a permission
engine, new credentials/persistence, account routing or legacy health migration.
The runtime changes are confined to `owned_health.py`, `health.py` and the existing
`_AnswerEvidence` wrapper in `connection_engine.py`. The wrapper snapshots request
evidence before awaiting [folded: Risk 1, robust]. Stage1, budget admission and facade
interfaces remain in place; no new sender layer is introduced.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Establish transport-faithful contract regressions | Real sender-built errors and a recorded red baseline for the known gaps |
| 2 | Define one owned request key | Matching failure/success keys without wrapper or namespace collisions |
| 3 | Recover only the condition actually disproved | Restrictions require the refused action; existing owner/time guards remain |
| 4 | Carry neutral attribution with the failure | New RPCs report; forwarded unverified errors stay neutral across tasks |
| 5 | Exercise the composition and document the contract | Integrated tests and clear public/private naming, recovery and delivery docs |
| 6 | Verify and checkpoint the rework | Product/evidence commits and truthful PR22/#7 status; renewed gates pending |

## Decisions that bind the implementation

### A. What stays

Preserve numeric owner proof before observation; expectedB/cachedA/actualB proceeds
asB, expectedA/actualB refuses. A caught invalidation remains terminal. Preserve
proxy/device/session policy, zero automatic retries/waits, budget admission and
cleanup/cancellation behavior. Keep `get_account_health(id)` local, copied and
explicit, with None for an unknown owner; keep legacy health separate.

Keep condition start ordering captured before authentication, no recovery of a
condition reported by the same call, exact client/opening-task evidence, and the
explicit group-access assertion. Keep source-time RPC/MultiError observation and
post-cleanup callback tasks. Existing successful coverage remains mandatory.

### B. One key for an owned request

For a single concrete TLRequest, unwrap a bounded chain of explicitly recognized
SDK envelopes, then use the leaf's generated namespace and class name:
`messages.GetHistoryRequest`, `messages.GetMessagesRequest`,
`channels.GetMessagesRequest`, `users.GetUsersRequest`, `updates.GetStateRequest`.
Root-namespace requests retain their root class name. The namespace disambiguates
different TL constructors with the same short class name, confirmed by the probe.

Initial transparent-envelope set, taken from the inspected1.45.0 SDK:
InvokeAfterMsgRequest, InvokeAfterMsgsRequest, InitConnectionRequest,
InvokeWithLayerRequest, InvokeWithoutUpdatesRequest, InvokeWithMessagesRangeRequest,
InvokeWithTakeoutRequest. Refer to the generated classes explicitly; do not depend
on Telethon's private `_NESTS_QUERY` variable at runtime. An unknown query-bearing
TLRequest stays its own namespaced type, not automatically its `.query` child.
Malformed/cyclic/over-depth chains yield no usable key, never a guessed leaf or an
exception into the caller. Bound envelope traversal at eight and detect cycles.

Only the **new owned** event `request` and snapshot `waiting` keys adopt this
namespaced spelling. They are a correction to this unmerged stage's contract.
Legacy event/request strings and `health._request_name()` stay as before. No query
arguments, peer hashes, credentials or serialized requests enter the key.

Capture immutable keys before the wrapper's first await, for a scalar TLRequest
or concrete built-in list/tuple/set/dict batch. Bind that snapshot to the current
owned observation and client, then consume it only on full success in the same
active task/lifetime. Never reread mutable caller containers after success or
treat their Python type as an RPC. Do not consume lazy/custom iterators for health
evidence or transform SDK input to repair iterable behavior; unknown input supplies
no request evidence. Partial MultiError successes supply none, as in revision2.
Internal callers keep individual TLRequest/envelope objects unchanged during the
call; this is a trusted private source contract, with no deep request cloning.
[folded: Risk 1, robust]

### C. Evidence by condition

All recovery additionally requires a successful body, a still-valid handle, the
same monitor/owner, a condition older than the operation's start, and no same-call
report for that condition. These are guards, not evidence that an action succeeded.

| Condition | Additional evidence required |
|---|---|
| Logged out / banned | Stage1's fresh account proof, as already specified |
| Request wait | A successful answer with the same logical request key |
| Restricted | The same outer method **and** a successful answer for the recorded refused logical request |
| Group no access | Explicit internal assertion after an actual result establishing access to that group |

A later GetUsers identity check may resolve a GetUsers-specific refusal, but cannot
resolve a GetHistory restriction or prove group access. Initial proof occurs before
owned observation and does not create a synthetic request success. Missing request
identity means no automatic request/restriction recovery based on a guess.

Maintain the existing single current account condition and request-type wait model;
this is not a redesign of Telegram's permission or rate-limit domains. Do not add
capability graphs or change budgets/join policy. Domain-specific group-result
interpretation remains the later operation's explicit responsibility.

### D. Isolation belongs to the failure, not every descendant context

Keep the ContextVar boundary that clears ambient health during setup/cleanup and
the existing conservative guard on active same-task enclosing calls. Replace
`_Call.excluded_errors` and its any-ancestor search with a private boolean marker
on the failure that escapes the isolated operation: **do not emit this failure
under a legacy account**. It is not "reported": an unverified failure emitted
nothing. It carries no owner, client, session, task or credential reference.

Mark the exact escaping object and its **explicit cause lineage**; known SDK
MultiError RPC leaves are explicit failure members too. Bound traversal, handle
cycles, and make metadata failure harmless to the original outcome. Do not adopt
arbitrary implicit context as part of the isolated source: that context can be
an independent legacy failure that existed before entry. This also preserves
neutrality when the original explicit cause is unwrapped and rethrown.

For legacy emission, inspect the incoming exception in the existing bounded
cause/context order. At each node, check the neutrality marker first. Reaching it
means this is the isolated failure or its wrapper: do not emit. Reaching an
unmarked raw RPCError first means a new RPC signal: allow existing classification,
even if an older neutral failure is farther down its context. The same rule serves
both `_on_error` and `report`; it does not turn local wrappers into new RPC evidence.

Use that check only at legacy **emission** sites. Leave general diagnostic
`classify`, `include_reported=True`, error descriptions and polling decisions able
to inspect the real verdict. Keep existing reported-error deduplication separate.
Forwarding through an awaited child task, another wrapper or another caller must
not reassign a pre-proof failure to a cached parent account.

This deliberately revises the selected Medium3 proposal's call-local storage form:
the additional probe shows that form loses provenance across task hops. A marker
on the actual failure removes the per-call retained exception list and follows
the error automatically. There is no global registry or persistent provenance log.

## Step 1 — Establish realistic contract regressions

[folded: Risk 1, robust]

### Proposed changes

Extend `tgdata/smoke_tests/test_33_owned_health.py` with a small sender-reply adapter
based on the executed review/planning probes. Synthetic decoded RpcError replies
must enter real MTProtoSender.send/RequestState/_handle_rpc_result, using the
actual request produced by the factory's policy. Preserve the real factory,
Stage1 handle, budget hooks, SDK dispatch, ledger and disconnect. Block sockets.

Convert the three review failures into acceptance tests; also cover same-short-name
namespaces, nested known envelopes, rethrown explicit source and awaited-child
pre-proof failure. Capture the known red baseline against3d59455 before production
edits; this intentional pre-change run is not final verification. Do not weaken
the required outcomes to match the defects or hand the SDK convenient prebuilt
error request names. Preserve the original review/probe files as historical evidence.
Add a real SDK case that sends GetState from a list, changes the caller's list to
GetHistory while awaiting its result, and checks that no GetHistory success/wait
recovery is manufactured. The critic's executed probe establishes this baseline.

### Output

Tests exercise actual error construction and fail for the known wrong behavior,
ready to validate the revised predicates in steps2–4.

### Safe in nature

True — offline test infrastructure and assertions only.

### Peripheral concepts

Telethon request envelopes, decoded RPC replies, synthetic transport, Stage1 fixture,
ContextVar/task propagation, red baseline versus final acceptance.

### Hardness Lvl

3/5 — the injection seam must observe, rather than supply, request identity.

## Step 2 — Normalize owned request evidence at both source hooks

[folded: Risk 1, robust]

Addresses **PR Medium1** and establishes the key consumed by Medium2's solution.

### Proposed changes

Add the bounded logical-key helper in `owned_health.py`. Use it for each successful
concrete request and for each actual raw RPCError's `.request`, including MultiError
leaves. Create the owned Finding with the canonical request value (e.g. a dataclass
copy); never rewrite the SDK error's request, arguments, cause/context or container.
Continue re-raising the same exception object. Keep actual client/task/validity
checks ahead of recording, and retain source-time recording of caught failures.

The owned ledger, event, waiting tick, reported-scope key and successful-request
set all use the same canonical string. No parallel alias map or request argument
history. Add a small safe capture hook at entry to `_AnswerEvidence.__call__`,
before awaiting the SDK. Capture only immutable keys and their observation/client
binding, not request objects/arguments. Pass the captured evidence to the answer
hook on full success and recheck the binding/task/handle there. Legacy calls keep
their old answer path. Unsupported lazy/custom inputs provide no owned success
evidence. The request/error source hook and budget admission otherwise remain as-is.

Test: matching success clears only the matching older wait; GetState cannot replace
or clear GetHistory's wait; namespaces do not collide; known nested envelopes match
their leaf; unknown/malformed evidence cannot create a false recovery; list success
and MultiError failures preserve their agreed behavior. Legacy strings stay unchanged.

### Output

Owned failure and success evidence agree on the same logical request. The new
namespaced keys are explicit and isolated from legacy API behavior.

### Safe in nature

False — changes the unmerged owned event/snapshot values and recovery keys.

### Peripheral concepts

Finding copy, generated TL classes, batch outcomes, wait generations, legacy naming,
exception identity, source deduplication, mutable caller input and in-flight evidence lifetime.

### Hardness Lvl

4/5 — normalization and capture timing must both describe the actual request.

## Step 3 — Record the refused action and narrow restriction recovery

Addresses **PR Medium2**, using step2's key rather than a second identity scheme.

### Proposed changes

Keep one private refused-request key with the owned monitor's current restriction.
Set/replace it from the actual restricted Finding. Clear it when that condition
recovers or is replaced by a non-restricted account condition; do not let a stale
key authorize recovery of a newer condition. Unknown key stays unknown.

Replace `call.requests` being merely nonempty with membership of this refused key,
plus the existing matching method, owner/start order, successful-body, valid-handle
and no-self-report guards. Keep account-proof and explicit group-assertion behavior
as defined above. No new generic success callback or capability engine is needed.
The inherited legacy answer tick remains for legacy calls; remove redundant owned
writes to that tick if it no longer serves an owned predicate, rather than inventing
another proof counter.

Tests must include repeated self checks, GetState/other metadata, wrong request,
wrong method, nested budget identity checks, missing key, caught auth/identity
invalidation, same-call report/retry and forced old/new overlap. A successfully
retried refused action under the matching method is the positive case. If the
refused action was GetUsers itself, a later owned GetUsers success is meaningful;
do not globally discard identity-request evidence.

### Output

A restriction clears only when the refused action has suitable later evidence;
merely proving the account again cannot clear another action's restriction.

### Safe in nature

False — changes owned account-condition recovery behavior.

### Peripheral concepts

Restriction replacement, logical request keys, method identity, budget re-verification,
account proof versus action proof, conservative generation ordering.

### Hardness Lvl

3/5 — one additional condition key with explicit lifetime and replacement rules.

## Step 4 — Replace ambient exclusion lists with origin-bound neutrality

Addresses **PR Medium3**, including the additional task-hop/prior-context cases.

### Proposed changes

In `health.py`, implement decisionD with small helpers for marking the exact failure
cohort and deciding legacy emission. Remove `_Call.excluded_errors` and the old
any-ancestor `excludes` implementation. Keep the existing ContextVar reset and
same-task enclosing-call recovery guard in `isolate_call`. When a failure escapes,
attach neutral-attribution metadata before propagating the same object.

Recognize explicit cause objects and actual RPC leaves of SDK MultiError without
walking arbitrary implicit context while marking. In the incoming ordered walk,
neutrality on the current node wins; a fresh raw RPC encountered first wins over
neutrality on an older ancestor. Apply exactly the same emission decision to
escaping and explicitly handled errors. Preserve existing classification and
reported-error behavior for calls with no neutral failure involved.

No source marker may change the meaning of `classify(..., include_reported=True)`
or the retry/polling stop decision. Marker writes must not replace primary exceptions
or cancellation. Do not mutate exception text/cause/context or add global maps.

Acceptance includes direct and wrapped pre-proof AuthRequiredError, its original
explicit RPC cause re-raised alone, implicit and explicit ordinary wrappers, new
actual RPC failures inside the handler (direct and wrapped), handled `report`,
an unrelated legacy RPC predating a local setup failure, and an awaited child task
returning an unverified failure. Add bounded/cyclic-chain and metadata-write-failure
checks without inventing a general exception framework.

### Output

Forwarded failures keep neutral attribution across task hops; independent fresh
RPCs still report under the correct legacy context. No ambient retained-error list.

### Safe in nature

False — shared legacy emission paths must preserve their established behavior.

### Peripheral concepts

Explicit cause versus implicit context, SDK MultiError, reported-error deduplication,
task propagation, diagnostic classification, cancellation and failure containment.

### Hardness Lvl

4/5 — the ordering and distinction between diagnostics and attribution are essential.

## Step 5 — Validate the combined boundary and document it

[folded: Risk 1, robust]

### Proposed changes

Exercise the real facade with combinations, not only helpers: namespace-separated
waits plus later success; refusal plus repeated proof and nested budget admission;
pre-proof errors forwarded across tasks and then a distinct legacy RPC; all while
checking fixed event/snapshot owner and source cleanup. Retain the original Stage2
and Stage1 acceptance cases, callback error/cancellation isolation, re-entry,
cooperative close and forced account/group/request overlaps.

Update README, `docs/account_operations.md` and smoke README with owned namespaced
request keys, refused-action recovery and neutral error forwarding. Show that
legacy health remains separate. Clarify the already-observed notification contract:
arrival can differ from observation order when cleanup durations differ; event
time and the local snapshot describe the observations. Add no FIFO worker or
durable delivery promise. Group assertions still require semantic access results.
Document stable individual request objects during a private call, immutable key
capture, and conservative lack of evidence for unsupported lazy/custom inputs.

### Output

Integrated regressions for the whole revised contract and product docs that match
it. Old expectations change only where this plan explicitly changes owned keys
or fixes a proved false recovery/omission; legacy expectations are not weakened.

### Safe in nature

True — tests/documentation, with real local components and synthetic transport.

### Peripheral concepts

Public snapshot copying, callback timing, original failure history, scope limits,
transport-faithful fixtures and consumer-visible request names.

### Hardness Lvl

3/5 — cover interactions and negative evidence, not just the three happy fixes.

## Step 6 — Verify, checkpoint and prepare renewed review

### Proposed changes

Run the revised suite33, legacy health16 and Stage1 suite32 first. Then all supported
offline suites12–19 and22–30 (avoid duplicate runs of unchanged already-passed suites
within the same final product state). Suites12/13 use missing config to skip their
three known live checks; suite12 may require normal local-bind escalation. No live
Telegram work, older live-oriented tests or unmerged #17 suite31.

Compile all tgdata/examples Python and check Python3.7 grammar; run daily continuation
demo and fresh/restarted backfill demos in temporary directories. Report actual
passes separately from skips. Re-run failures after only corrections permitted by
task-impl; an architectural departure goes back through planning, never a silent
patch or weakened assertion. Verify product scope and diff whitespace.

Commit code/tests/product docs together and current work-folder verification/handoff
separately, preserving round1 evidence. Push the existing issue branch and update
PR22/#7 with the actual new product/evidence commits. The old 424 passes are a
baseline, not acceptance of the rework. Then require renewed merge check and a fresh
in-session PR critic under §7; any Medium/High rejects. A second rejecting Stage2
round returns to the description/traverse under §7.4, not another routine patch loop.

### Output

Measured rework verification, separate archive notes, and the same PR ready for
its renewed gates. Merge still needs the user's go-ahead; exclude devdocs and
preserve the branch archive. This plan itself does not pass any of those later gates.

### Safe in nature

True — offline verification and isolated feature-branch checkpoints.

### Peripheral concepts

CONTRIBUTING stages, selective staging, unchanged duncan/guide/original-checkout files,
Telethon1.45.0, original archived evidence and explicit review scope.

### Hardness Lvl

2/5 — established suites, precise counts and honest publication state.

## Re-plan check

| Input | How this revision answers it |
|---|---|
| PR Medium1 | Steps1–2 observe real sender errors and unify namespaced request keys |
| PR Medium2 | Step3 retains the refused key and requires matching action evidence |
| PR Medium3 | Step4 distinguishes a marked originating failure from a new raw RPC, including task hops |
| Original critic1/2 | Validity veto and MultiError source observation retained and re-tested |
| No overengineering | Reuse the fixed ledger and existing wrapper; three runtime targets, one key rule with immutable capture, one refusal key and one failure marker; remove the ambient error list |
| Test assumptions before relying on them | Existing failures and additional source facts already executed; step1 uses the real error-construction seam before corrective code |

The fresh revision3 critic selected one robust mitigation and its required carrier
experiment passed before implementation. Execute this revision4 without re-critiquing
the fold. Renewed merge check and fresh PR critique remain required after verification.
