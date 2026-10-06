---
model: gpt-6-astra
effort: max
---

# #7 — implementation plan, revision 3

**Status:** re-planned after PR16 round1 rejection; awaiting a new critic-d pass
and fold to revision4. This document has no carried-forward critic-fold marker.
No runtime correction is implemented by writing it.

Inputs: desc.md; pr-critic.md at87d15b4 (Medium1, Medium2, Low3); the original
traverse finding; current code at35aead1; replan-context.md; replan-r3-probes.py.
The rejected blueprint and first plan critic are preserved in archive/round-1/.
The warm context/probe checkpoint is4daf873,2026-10-06. Model: Astra/max, verified
again from current turn metadata. PR16 remains the single draft PR for this work.

### What is the task

Deliver the three ephemeral group operations with truthful results, original
remote failure categories, durable account join admission and coherent account
health. The first implementation got the request/result and allowance boundaries
largely right, but inferred local failure from an SDK exception type and attached
fresh identity only to event presentation. Revision3 makes request failure origin
and observation ownership explicit across the complete paths, including summaries,
recovery, nested requests and concurrent calls. It also makes overlap a condition
of the regression test rather than an assumption about gather.

### Huge Hard Blockers

#### Planning Blockers

None identified. The two Medium mechanisms are reproduced, not unexplained.
The selected-version constructor policy is tested in the actual SDK/factory MRO,
and the account-ownership cases have concrete behavior specified below. No human-only
product decision or unavailable premise prevents this plan. New ledger/scope code
will need implementation tests; it is not represented as already implemented.

#### Execution Blockers

None for the planned offline implementation. A new plan critic and selected fold
must precede runtime edits under CONTRIBUTING; this is the next pipeline gate.
Live acceptance still requires designated accounts/groups and authorization and is
outside these steps. Merging remains separately user-authorized after both reviews.
The previously unavailable model/effort metadata has been verified, not waived.

### How this implementation moves toward desired state

Keep the working group-result, reference, session and allowance contracts. Replace
one ambiguous resolution boundary with explicit RPC/result handling, and choose
final-RPC-error propagation at client construction. Replace the health ledger's
implicit single identity with an owner key carried from request evidence into
storage and recovery. Derive event and summary identity from the same owner.
Expose selection explicitly when this instance has evidence for several accounts.
Verify the complete public paths, then update the same PR and repeat both gates.

### Evidence settled before planning

- pr-critic-probes.py reproduces six ServerError responses becoming
  GroupReferenceError for a known numeric group and ValueError for joining.
- replan-r3-probes.py changes only the real SDK constructor input
  raise_last_call_error=True. Authorization, self identity, numeric resolution,
  handle resolution, history and joining all propagate the identical final
  ServerError object after six actual SDK attempts. Six failed history/join
  attempts retain six respective charges. No desired exception was fabricated
  by replacing the SDK loop or the facade.
- The public health-check success path already sends GetUsers(InputUserSelf)
  through get_me. The fresh reply contains222 while cached/snapshot ID remains111.
  The fix can consume existing evidence without adding a successful-path RPC.
- Genuine overlap with two pending requests and reversed completions preserves
  event identity today. The original immediate-future fixture runs sequentially.

### Scope and retained contracts

Retain lookup_group, check_group_access, join_group and get_join_budget; their
portable values and statuses; strict handles/invites/known numeric peers; token-free
labels; one owned ephemeral client; no prompts/current_group mutation; explicit
paid/webview/pending outcomes; no mandatory post-ack network work; local enrichment
and warning containment. GroupInfo, message-batch schema and discovery non-joining
behavior remain unchanged.

Keep both durable budget schemas and existing units/atomicity. Every join send
still has fresh account verification and a committed claim, with no uncertainty
refund. Health identity bindings are diagnostic evidence only: they never replace
the fresh lookup required for budget admission. No cross-instance health registry,
new backend, login workflow, worker or live group test is introduced.

Additional traverse is not needed for these corrections within the already-traversed
client/health/admission design: the reproduced errors refine an existing request
policy and ownership relation. A cross-instance registry or different product
workflow would exceed this decision and require reassessing §5.

### High-Level Summary

| Step | Description | Expected Output |
|---|---|---|
| 1 | Preserve remote failure origin through owned requests | Explicit SDK error policy and typed numeric resolution |
| 2 | Give stored health state an immutable owner | Per-instance owner-keyed ledgers and owner-local recovery |
| 3 | Carry verified identity through actual request scopes | Client binding, request evidence and exception provenance |
| 4 | Select public health summaries without cached relabeling | Compatible single-account view plus explicit multi-account views |
| 5 | Make error and concurrency regressions exercise real failures | Expanded test20 and focused health-ownership suite |
| 6 | Document the complete result/error/health contract | Updated README and test inventory |
| 7 | Verify, commit and prepare renewed gates | Supported offline checks and traceable commits on PR16 |

## Design commitments for the implementation

### A — Failure origin is established at its source [PR Medium1]

An absent local cache row is a reference error. An expected RPC reply that does
not contain the requested entity is checked explicitly. An RPC exception remains
an RPC exception, including after retries. A generic ValueError escaping a network
helper is not sufficient evidence of bad input. Local diagnostic failures keep
the existing implicit-context isolation; real explicit RPC causes remain intact.

### B — One health owner means one state/recovery namespace [PR Medium2]

HealthMonitor stays local to one TgData. Introduce a frozen internal Owner key:
`verified(account_id)`, `legacy(captured_id_or_none)`, or `unverified`.
Verified IDs are positive integers from a real self lookup. Legacy IDs are only
captured display hints for existing unverified call paths; their kind prevents
them from becoming the verified account with the same number. Explicit unknown
identity on a new group call is unverified and never falls back to the primary cache.

Move account verdict/ticks, restricted-method marker, waits/expiry/generations,
group denials/ticks, event/wait counters and last-unclassified value into one
Ledger per Owner. Capture the account envelope with its owner; snapshot rendering
must not replace that user ID by a later _who lookup. Label/session decoration
can fill previously unavailable configured metadata, never reassign the person.
No migration of an old ledger to a newly discovered account is permitted.

A call may observe several owners. Its answer ticks, handled waits and reported
scopes are keyed by Owner, not a single global answered/account_id pair. Recovery
requires the matching owner's later evidence and existing method/group rules.
One owner's success cannot clear another's condition. Ancestor suppression uses
(owner, scope) and only active ancestors belonging to the same monitor. Foreign
or expired inherited task contexts cannot mutate the originating call's evidence.

For waits, retain the generation of the actual handled/slept wait. Completion
can clear that generation only, not a later wait another call recorded for the
same request type. Expiry still filters waiting snapshots without inventing an
account-recovery event. Unverified account/group conditions are not assigned to
or recovered by a newly verified different namespace. They stay visibly unverified.
Legacy-only behavior remains within its own ledger; it never clears verified state.
An initially unverified self-lookup wait can end when that exact request frame
succeeds under the same credential/DC binding: clear its recorded wait generation
and emit its recovery under the original unverified owner. This narrow request
completion is not evidence for clearing an unverified account/group condition.
A changed credential or different verified owner cannot clear the earlier wait.

### C — A request's identity is distinct from the last identity seen [PR Medium2]

Introduce a task-owned request-evidence scope around the existing _AnswerEvidence
client wrapper. A frame belongs to the current active public call, records its
client identity evidence and has its own owner. Initialize it from that client’s
valid verified binding;
otherwise use the call’s captured legacy hint only for a legacy-mode call, or
unverified ownership for an explicitly unknown/new-group call. Never seed a new
client’s frame from the last verified owner used by another client.
Nested frames restore their parent; frames from a different client do not
overwrite the parent's owner. Concurrent
calls never use one mutable facade-wide current account.

A client may retain a verified diagnostic binding `(dc_id, auth_key.key_id,
account_id)` derived from its actual self reply. Compare the current session/DC/key
before using it; absent/changed key or DC means no verified binding. Never use
_self_id as authority. This binding is in-memory per client, not a new session-store
field or a cross-client registry. A genuine self reply can update this binding
even outside a public health call; that creates no event or ledger observation.
Never expose key IDs or client objects in events,
exceptions, snapshots or logs. Budget verification remains fresh on every attempt.

Recognize the exact GetUsers(InputUserSelf) request and a single valid User reply
at the shared wrapper, including supported invocation wrappers. Bind the fresh
account before recording that reply's answer. An invalid/ambiguous self reply must
not credit the previous account with recovery evidence. Do not derive identity
from ordinary user lookups, arbitrary metadata or cached get_me(input_peer=True).
Compound requests without an unambiguous identity observation remain conservative.

Fresh join/read identity helpers also pass the client when noting an account,
so an enclosing history/join request gets the owner verified immediately before
admission. A response/failure is attributed to its request frame, not whatever
another task most recently stored on that client. If credential/DC state changed
without matching verification within the frame, ownership becomes unverified.

When an RPC error escapes, retain private owner provenance tied to this monitor
and public-call token. Preserve a matching inner RPC origin through wrapper errors;
an unrelated old error tag cannot bind a later call. The tag contains only immutable
owner/call identifiers, not a client/session/credential object. Attribute writes
are best effort; use a bounded current-call fallback or unverified ownership if
provenance cannot be retained. Never guess another verified owner on failure.
Close/clear request-frame client references and reset ContextVar tokens in finally.
All new observation hooks are nonthrowing and leave the operation's return/error intact.

### D — Summary selection is explicit and deterministic [PR Medium2]

Add keyword-only `account_id=None` to TgData.health_check and selection arguments
to HealthMonitor.snapshot. This argument selects stored observations; it is not
identity proof and never causes a connection to a different account. Validate an
explicit positive integer before network work, with local context-free ValueError.

TgData.health_check opens its health call with explicitly unknown ownership
before inspecting clients, so a primary-cache hint cannot label an unverified
pool/client failure. A valid per-client verified binding may still supply identity.
ConnectionEngine.health_check already calls _confirm_logged_in/get_me for live
clients. Return the verified ID from that existing successful self read and expose
it as primary_account_id and per-pool account_id metadata. _confirm_logged_in
retains the returned self object long enough to validate/note its ID with that
client; an identity note alone is not a synthetic answer tick. Preserve connection
healthy/error semantics and the existing auth-reason fallback when get_me returns
None; inability to establish an ID remains None, never cached _self_id. The shared
request scope attributes each client's evidence independently in that loop.

Health snapshots add `identity_source`, `accounts`, `unverified` and `totals`:

- accounts maps stringified verified account IDs to nonrecursive snapshots with
  the existing account/verdict/wait/group/counter fields for exactly that owner.
- unverified is an ordered list of nonrecursive legacy/unverified snapshots with
  captured ownership hints and explicit source labels; none is silently promoted.
- totals contains instance-wide event/wait counts. A selected flat view's existing
  counters belong only to its owner, not a mixture of different accounts.

The existing flat fields are a compatibility view selected in this order:

1. Explicit account_id selects its verified ledger. If unseen, return that ID with
   identity_source=unobserved and no verdict/observation claims; do not create a
   verified ledger merely because the caller requested it.
2. Otherwise prefer the primary account freshly verified during this health_check.
3. Otherwise select the sole verified account only if no active unverified condition
   makes automatic selection ambiguous. Active here means a terminal account
   verdict, a group denial or a nonexpired wait; historical counters and a last
   unclassified error alone do not create an active condition.
4. With no verified owners, a sole legacy/unverified ledger retains its flat view.
   With no observations, retain the empty legacy view and mark its source honestly.
5. Multiple verified owners, conflicting unverified conditions, or multiple possible
   fallback owners yield identity_source=ambiguous and no selected user ID/verdict.
   Flat observation fields/counters are None in this new case; the complete details
   remain under accounts/unverified/totals. Do not return fabricated empty healthy
   state or pick the last writer. The caller can select a verified account explicitly.

The account envelope's existing label/session/user_id keys remain. Events add an
identity_source marker but retain the existing verdict vocabulary and fields.
Known single-account snapshots keep their existing flat values. Ambiguous/unobserved
views are new explicit cases, documented rather than hidden behind a stale ID.

## Step 1 — Define the owned request error boundary

[answers: PR Medium1]

### Proposed changes

In connection_engine.py, add optional keyword-only raise_last_call_error=False
through _new_client and ephemeral_client. When True, pass the documented SDK
constructor argument before connect/auth; when False, omit it to retain existing
factory/stub/default behavior. Do not mutate a shared standing client's retry policy.
TgData._group_operation and get_join_budget request True. Retain their zero flood
threshold after authorization and all current admission/retry behavior.

In group_operations.py, replace get_entity inside numeric _resolve with a helper
that accepts the already-validated InputPeerChat/InputPeerChannel and calls the
corresponding GetChats/GetChannels request directly. Await outside any blanket
ValueError/TypeError conversion. Verify Chats/ChatsSlice and exact marked peer match:
empty expected entity list is a clear unresolved-reference result; nonempty mismatched
or ambiguous/malformed replies raise GroupResponseError. Only local cache/input
conversions and explicit unavailable/deactivated/migrated-target decisions become
GroupReferenceError. All RPC/transport errors retain their object and category.
Keep handle/invite validation, proof and post-ack outcome mapping intact.

### Output

Every new group/status operation preserves the final retry RPC; numeric resolution
cannot reinterpret an arbitrary SDK failure as bad input.

### Safe in nature

False — changes new operation error contracts and a shared factory signature; defaults stay compatible.

### Peripheral concepts

SDK constructor/retry loop, auth-reason handling, reference cache, request admission, explicit causes.

### Hardness Lvl

4

## Step 2 — Refactor health storage and recovery around ownership

[answers: PR Medium2]

### Proposed changes

In health.py, implement Owner/Ledger and the owner-keyed call evidence described
in B. Keep classification/register/normalise_group vocabulary and callback/logging
behavior. Route _record, _event, _sleep, _recover and counters through the chosen
owner, with immutable captured account identity. Keep independent group-recovery
control. Do not relabel old state or use unverified evidence to recover verified
state. Add wait-generation matching and owner-scoped parent reporting.

Keep state growth proportional to distinct account/hint owners and conditions,
not one persistent ledger per request. Transient request/call evidence is released
at scope end. Observation failures must not mask a business error or successful
join; new hooks contain their own diagnostics failures as well.

### Output

Events, conditions and recoveries share one explicit ownership model inside each
TgData, with no cross-account clearing or mutable snapshot relabeling.

### Safe in nature

False — shared health state is used by old and new features; legacy tests and new ownership cases are required.

### Peripheral concepts

ContextVar ownership, temporal recovery ticks, wait generations, nested callbacks, unverified legacy evidence.

### Hardness Lvl

5

## Step 3 — Bind request evidence to real self identity

[answers: PR Medium2]

### Proposed changes

Extend _AnswerEvidence in connection_engine.py to enter/leave the request frame
from C, recognize genuine self replies before generic answer credit, maintain the
per-client diagnostic binding and tag escaping RPC origins. Use a bounded supported
wrapper inspection; never infer fresh identity from a batch with ambiguous results.

Update join_client.py and budget_client.py fresh identity notes to include the
client. They still make their existing fresh self query and validate its result;
no diagnostic cache is consulted for quota authority. Preserve no-await claim-to-send.

Connect frame ownership to handled errors and the silent-sleep filter. Unowned
background tasks produce unverified observations without mutating a parent call's
answer/reported sets. Errors handled after the SDK frame exits retain their captured
origin; explicit wrapper causes work without following unrelated implicit context.

### Output

The owner that generated a reply/failure remains its owner through nested requests,
retries, callback reentry and delayed handling. Stale primary caches are irrelevant
to verified account attribution.

### Safe in nature

False — changes the shared observation wrapper; observer failure and credential-lifetime tests are required.

### Peripheral concepts

GetUsers(InputUserSelf), auth-key/DC lifetime, nested SDK calls, per-task frames, exception provenance, budget helpers.

### Hardness Lvl

5

## Step 4 — Expose coherent health summaries

[answers: PR Medium2]

### Proposed changes

Implement D in health.py, ConnectionEngine.health_check/_confirm_logged_in and
TgData.health_check. Consume the existing self read's verified ID, record primary/
pool evidence independently and choose the flat snapshot by explicit/fresh primary/
sole owner rules. Do not add an extra success-path get_me request.

Add deterministic accounts/unverified/totals views and ambiguous/unobserved cases.
Selection does not mutate state, fabricate authority or suppress the existing
connection errors. Keep the old single-owner envelope and other public group
results unchanged. Keep health observation non-enforcing: identity uncertainty
changes diagnostic attribution/selection, not permission to read or join.

### Output

check_group_access followed by public health_check reports the same account's
condition; multiple/unknown owners are inspectable without false attribution.

### Safe in nature

False — public diagnostic data gains fields and explicit ambiguity cases; callers and docs need an exact contract.

### Peripheral concepts

Connection/pool health, self identity, flat snapshot compatibility, account selection, JSON-ready output.

### Hardness Lvl

4

## Step 5 — Put the rejected cases and true overlap in regression suites

[answers: PR Medium1, Medium2, Low3]

### Proposed changes

Expand test_20_group_operations.py and add test_21_health_ownership.py. Keep real
SDK dispatch, factory mixins, real sessions/SQLite and socket blocking. Supply
transport replies/faults only; do not replace error selection, ownership or snapshots
with stand-ins returning the expected behavior. Use explicit pending futures/barriers
and assert both tasks are live before reversed completion.

Required outcome matrix:
1. Exhaust temporary errors through authorization, identity, numeric/handle/invite
   resolution, history, join and budget status. Preserve the final RPC object/type;
   no GroupReferenceError for remote failure. Verify charge counts and cleanup.
2. Real missing cache/empty entity/nonempty mismatch/malformed reply cases remain
   distinct. A native error from a network-side hook is not automatically bad input.
3. Strict SDK policy reaches the ephemeral client before authorization. Legacy
   defaults, factory proxy/device/session options and budget independence remain.
4. Reproduce cached111/fresh222 through check_group_access and public health_check;
   event and selected snapshot agree and the existing self request is used once.
5. No-primary/sole-account, explicit selector, unseen selector, invalid selector,
   multiple accounts and active unverified conditions follow D exactly.
6. Two different accounts access the same group/request type with real overlap.
   Success forB cannot clearA's account restriction, group denial or wait. Also
   test reversed order, same-account recovery and a newer wait generation.
7. One call changes observed identity between preflight and admission. Its replies,
   charges and errors stay with their actual verified owners; old-owner state is
   not relabeled or cleared by new-owner answers.
8. Primary/pool checks for different verified accounts remain isolated. Self lookup
   credits the new owner before recovery. Cached input_peer=True and ordinary
   user lookups provide no new identity evidence.
9. Nested identity lookup during a guarded request, handled RPC after frame exit,
   wrapper causes, callback reentry and unowned/expired inherited tasks preserve
   ownership. Error tags from another monitor/call cannot redirect this call.
10. Credential/DC changes invalidate the diagnostic binding; no authentication
    material or client object appears in public metadata or exception tags.
11. Legacy-only event/snapshot behavior remains in the legacy namespace; old
    unverified facts never become a verified account's conditions. Unknown events
    stay marked unverified and are not hidden or assigned a guessed identity.
12. Snapshot views are JSON-ready, deterministic and independent copies. Counts
    belong to their owner; totals are instance-wide. Selector reads do not create
    authority or conditions. State is not allocated persistently per request.
13. Hook/attribute/logging failures do not replace the original operation outcome;
    post-ack cache/warning containment, privacy, session persistence and cancellation
    remain covered by the existing meaningful tests.

Adapt test16's internal-state setup only where the deliberate owner/summary model
requires it; preserve its classification, delivery, temporal-recovery and public
single-owner assertions. Do not weaken a failed expectation to conceal a defect.
The first PR's standalone probes remain historical reproductions; equivalent
correct-behavior cases become product tests rather than only archive evidence.

### Output

Regression protection includes both reproduced Mediums and enforced concurrency,
with a concrete compatibility matrix for the new health ownership contract.

### Safe in nature

True — offline synthetic tests only; no account login or live group mutation.

### Peripheral concepts

Real SDK retry semantics, scheduling barriers, exception identity, per-owner ledger histories, public health API.

### Hardness Lvl

5

## Step 6 — Document the resulting public contract

### Proposed changes

Update README group/error and account-health sections with original final RPC
propagation, the explicit health_check(account_id=...) selector, identity_source,
accounts/unverified/totals, flat-view selection order and ambiguity examples.
Explain that legacy hints are unverified and that a diagnostic identity cache
never replaces budget admission's fresh identity query. Document retained unknown
observations without claiming they belong to the selected account.

Update smoke_tests/README.md for test21 and the stronger test20 cases. Keep the
Telethon1.45 target and existing dependency bounds. No schema change to batches,
sessions or either budget is required. Note added primary/pool identity fields.

### Output

Callers can tell a remote retry failure from invalid input and select the health
observations belonging to their account without relying on cached labels.

### Safe in nature

True — documentation only; this step does not change dependencies.

### Peripheral concepts

Public health consumers, result portability, legacy compatibility, offline/live evidence limits.

### Hardness Lvl

2

## Step 7 — Verify and commit the coherent revision

### Proposed changes

Compile, run targeted test20/test21/test16, then the supported offline suites12–21
on .venv Python/Telethon1.45.0. Use the confirmed nonexistent config for12/13 to
skip the three live checks. Check Python3.7 grammar for changed runtime files and
public import/API compatibility. Check diffs and staging, excluding duncan and
unrelated guide edits. Report any small corrections transparently; a structural
failure returns to the plan instead of receiving a hidden patch.

Commit runtime/tests/public docs together and work records separately; keep warming/
work-folder artifacts on the archive branch. Update PR16 and issue7 with exact
results and the revised contract. Repeat merge-check and a fresh diff-plus-plan
PR critique on the final revision. A second rejected PR gate invokes §7.4's stop
and return to description/traverse, rather than another local re-plan loop.
Merge remains pending the user's go-ahead; this plan authorizes no live joins.

### Output

An implemented, verified revision with current blueprints and review evidence,
ready for the renewed two-gate merge process on the existing PR.

### Safe in nature

False — validation publishes code/records; final merge is separately gated.

### Peripheral concepts

Commit isolation, PR review rounds, archive-only documents, target SDK, supported offline suite.

### Hardness Lvl

3

## Why this replaces revision2

Revision2 translated native exceptions after a network helper and added fresh
identity at event formatting time. Both repairs stopped too late in their data
flow. Revision3 chooses the request's failure policy before any request and keeps
identity attached to stored facts and recovery evidence. The same owner then
serves event delivery and summary selection. Its tests force the concurrency
condition the contract claims to handle. These are one coherent boundary design,
not independent patches applied after the rejected review.

This revision is complete as a plan. Next: critic-d on this plan plus desc.md and
the first PR review, then selected fold to revision4 before implementation.
