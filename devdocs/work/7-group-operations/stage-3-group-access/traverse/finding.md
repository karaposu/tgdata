---
status: active
model: gpt-6-astra
effort: max
---
# Finding: read-only group lookup and access for Stage3

## Question

How should tgdata resolve a group's details and check whether a specified account
can read it, using the account-identity and health foundations already merged in
Stages1 and2? The answer must feed the requested implementation while keeping join
allowance and joining for their later stages.

This is the completed contract inquiry. It selects what Stage3 should build; the
feature description, plan, plan critique, code and final verification still follow.

## Finding Summary

- Expose two asynchronous methods: lookup_group and check_group_access. Both require
  the expected numeric account ID and use the existing temporary owned operation.
- Lookup returns available metadata and membership qualifications. It does not claim
  that resolving a name or being a member proves readable history.
- Access checking makes one bounded history request when a usable peer exists. It
  reports readable, denied or unprobed; unrelated operational failures remain errors.
- Access results retain the complete lookup observation, so a temporary preview's
  expiry and other qualifications do not disappear after checking history.
- Implement the domain logic in one stateless module with thin facade methods.
  No new connection manager, budget store, engine instance or health ledger is needed.
- Validate the public path with actual Telethon1.45.0, existing ownership/health and
  real budgets. Synthetic server replies establish local behavior, not live permission.
- Preserve and document a measured SDK cache limitation: a hashless CommunityForbidden
  can fail in Telethon's file session before a result reaches tgdata. That error must
  not be converted to a group-access result.

## Finding

### 1. Treat lookup, membership and history as different observations

The library's consumers scrape groups, so the useful access question is whether this
account can obtain a history response. A group name and title answer a different
question. An account can see an invitation's description without obtaining a peer
that can be used for a read request.

Membership is another useful fact, but it is not the read verdict. Telegram's
[temporary invite preview](https://core.telegram.org/constructor/chatInvitePeek)
can permit reading without joining. Conversely, a separate history request can fail
after metadata was obtained. The new API must keep these facts distinct.

A successful empty history response counts as a read observation. It says nothing
about whether the group has ever had messages, whether all history is visible, or
whether the account will retain access later. This is a point-in-time observation.

### 2. Preserve the expected account throughout each call

Both methods take an explicit account_id keyword argument. It means the expected
Telegram account, not a session filename or a cached identity. The existing verified
operation checks the authenticated identity before the group work begins.

Every returned value includes that verified account. The existing owned-health
boundary records failures and recovery for the same owner. A mismatched account,
missing authentication or failed setup produces an error, not a group-access result.
The methods do not request login codes.

All SDK work remains inside the opening task and temporary-client lifetime. Existing
proxy, device, session storage, read-budget and cleanup policy applies unchanged.
The result is plain data that remains usable after disconnect; it holds no client.

### 3. Keep reference resolution explicit and bounded

Support group handles, documented Telegram username/invite links and deterministic
numeric group references. Specify the exact string grammar and integer bounds in the
plan. Do not inherit the SDK's entire entity vocabulary, including phone/self aliases,
or add an implicit dialog scan to make an unknown number work.

A marked basic-group ID already identifies its peer type and needs no access hash,
so one direct metadata request can resolve it. A marked channel ID needs an exact
cached hash. A bare positive ID is accepted only when one cached group namespace is
identified; a user cache row is never selected as a group. Ambiguity and missing local
reference information raise an explicit local reference error.

Match the returned group against the requested typed peer. The same numeric ID in
another peer namespace must not silently become a different group. A username that
resolves to a user is also an explicit non-group reference error.

The method keeps an invite's raw token only as a request input. Public results and
health grouping use a safe correlation label, with a canonical peer ID separately
available when Telegram supplied one. These labels are observations about the supplied
reference; this stage adds no registry that merges every username, ID and invite alias.

### 4. Return qualified values without changing GroupInfo

The existing GroupInfo type supports discovery rows and assumes a known group ID.
It should remain unchanged. A valid invitation preview can lack an ID entirely,
so filling that existing shape with invented defaults would mislead its consumers.

Use small immutable GroupMetadata and GroupLookup values. Group metadata records
available IDs, title, username, group kind and participant count. Lookup records the
verified account, safe target label, that metadata, optional membership and source-
derived preview/request/payment qualifications. Missing qualifications remain None.

The pinned SDK exposes basic Chat, Channel and Community forms, with incomplete and
forbidden variants. The projection must distinguish those actual forms and validate
what it uses. A min entity (an incomplete SDK entity) or a missing hash does not
provide a general-purpose channel peer. Zero and missing hashes are not interchangeable.
Unknown/malformed source shapes must not manufacture metadata or readiness.

GroupAccess records the verified account, safe target, status and reason, and retains
an optional complete GroupLookup. When resolution itself is denied there may be no
lookup value. Convenience views such as group, member and readable are derived from
that single observation. They must not become independently mutable facts.

### 5. Define the access result at the actual read boundary

After successful resolution, issue one GetHistory request with limit1 and no cached
result hash when a suitable peer exists. Use the existing client, so normal account
verification and read-budget admission still occur. Do not add a separate quota.

Return readable only for a valid history response. Validate the response shape and
any supplied message peer against the requested group before asserting access. A
recognized empty history result remains valid; a malformed or cache-only reply does
not establish the required observation.

Return denied only for an actual group-access RPC failure classified by the existing
health vocabulary. Preserve Telegram's reason. This may occur during resolution, so
metadata can be absent. It is a refusal of the attempted access, not a permanent
permission prediction or proof of why the account was refused.

Return unprobed when a recognized reply supplies useful metadata but no safely
constructible peer. A plain invite preview is one example. It does not mean denied.

Authentication/identity, flood waits, temporary server failure, network errors,
read-budget refusal, malformed responses and local storage/cache errors remain
exceptions. Do not catch all failures as denied or unprobed. The old combined
implementation's native-exception translation must not be copied into this stage.

Only a validated positive history result calls the existing explicit group-access
assertion. Lookup and unprobed results cannot clear a prior denial. The merged
owner, operation ordering, handle validity and no-self-recovery guards still apply.

### 6. Keep the SDK cache limitation visible

A probe used actual1.45 TL serialization, factory dispatch, sessions and cleanup.
For a CommunityForbidden reply without an access hash, the default SQLite session
raised IntegrityError while caching the reply. The store-backed memory session
returned the same reply. Both source clients closed without creating false health.

This is an existing SDK boundary: its entities table requires a non-null hash, while
this current entity form can omit one. The domain adapter has not received a normal
result when that caching step fails. It must preserve the original error rather than
invent an access outcome or silently change session behavior.

Document this specific limit and cover it through the new public methods. The selected
contract does not promise that every legal SDK reply succeeds through every backend.
A vendor/session compatibility fix would be separate work, triggered by a concrete
need for that unsupported path; it is not required to build the classic-group feature
or the error-preserving observation boundary.

### 7. Use the merged structures directly

One cohesive group_operations module can contain reference interpretation, result
projection and read-only operations that consume the verified handle. The facade
provides two thin methods through its existing owned-health context. A new stateful
engine object supplies no needed state here.

Keep the implementation on the selected Telethon1.45.0 surface and align dependency
metadata with the constructors used. New exports and documentation must describe the
same return/error contract. No join method, allowance store, account pool, scheduler
or broad legacy-health migration belongs in this delivery.

## Next Actions

### MUST

- **What:** produce the lightweight feature description and a concrete plan with
  exact input/result/error rules, including the SDK limitation.
  **Who:** the current task-impl agent, using task-desc and task-plan.
  **Gate:** before any Stage3 runtime edit.
  **Why:** implementation and review need one explicit contract rather than guesses
  hidden inside parser or exception-handling code.
- **What:** run critic-d on that plan, execute any required prebuild experiment,
  then fold selected mitigations before implementation.
  **Who:** the current agent in this same session.
  **Gate:** after the plan is committed, before dependent implementation.
  **Why:** source composition and domain validation must survive an adversarial check.
- **What:** implement the small adapter, public methods, values, docs and real-path
  regressions; verify supported offline suites and demos.
  **Who:** the current task-impl agent.
  **Gate:** after critic requirements are met and the fold is committed.
  **Why:** the requested feature is working code, not just this design document.

### COULD

- **What:** qualify a few real group/invite examples with bounded read-only tests.
  **Who:** a maintainer/agent with a designated account, group and shared allowance.
  **Gate:** after public-path implementation verification and explicit live setup.
  **Why:** actual server examples complement local SDK evidence.
  **Depends-on:** MUST “implement the small adapter”; this live qualification is GATED
  until those methods and deterministic checks exist.

### DEFERRED

- **What:** repair or upgrade the SDK cache path for hashless CommunityForbidden.
  **Gate:** a concrete supported consumer needs that path, or a candidate SDK update
  changes its behavior and can be verified.
  **Why (if revived):** make the source reply available consistently across backends.
- **What:** joining, join allowance and any legacy-health migration.
  **Gate:** their explicitly scoped follow-up stage or a demonstrated consumer need.
  **Why (if revived):** deliver those capabilities without expanding this read-only stage.

## Reasoning

Broad SDK entity resolution was rejected as the complete policy because it accepts
more than explicit group references and can lose plain preview metadata or trigger
unrelated discovery. Requiring callers to supply only resolved peers was also rejected:
it would shift the requested lookup work back to the consumer. Explicit bounded
routes preserve useful inputs while making missing identity visible.

Reusing GroupInfo with placeholder IDs or returning raw SDK objects would leave the
meaning problem unresolved. The former changes an existing discovery contract; the
latter leaves consumers to interpret all source variants. Separate portable values
retain unknowns and qualifications without those costs.

A permission matrix inferred from metadata/membership cannot prove a history read.
An exception-only Boolean also erases the useful unprobed case. The chosen three-state
observation retains error identity and lets callers distinguish lack of evidence from
an actual refusal.

A global ownership/resolution migration would be a much larger change. Actual probes
show that the merged lifetime, budget and health hooks already supply the needed
boundary. A thin GroupEngine could also work, but an extra instance owns no new state;
the stateless arrangement has less machinery for the same public contract.

Tests with canned engine verdicts would supply the behavior they claim to verify.
Live-only tests cannot reliably exercise wrong peers, local cache failure or precise
concurrency/cancellation. Real SDK composition with synthetic remote replies is the
appropriate deterministic test layer, with its live-permission limits stated clearly.

The inquiry ran four component probe groups: schema/cache shapes, budget/health
composition, preserved final numeric RPC failure, and the file/store optional-hash
edge. The last prevents a blanket SDK-support claim; it does not justify masking
source errors or introducing another session system. See ../contract_probe.py and
the executed output in docarchive/sensemaking.md and docarchive/critique.md.

## Open Questions

### Monitoring

The exact new public-path regression matrix must show that wrong/missing response
identity cannot produce readable or a recovery event. This is an implementation
acceptance obligation, not a missing external decision.

### Refinement Triggers

Revisit the SDK cache qualification when the hashless reply succeeds through the
ordinary file session on the selected SDK, or when a separately reviewed compatibility
change removes the specific non-null-hash failure. Revisit reference aliases only if
a consumer explicitly needs canonical health rekeying; current reference grouping
must not silently grow into an alias registry.

No open planning blocker was identified. Live account permissions remain unmeasured
in this run and are not claimed as established by synthetic replies.
