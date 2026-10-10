---
model: gpt-6-astra
effort: max
---
# #7 Stage3 implementation plan — revision1

### What is the task

Add public read-only group lookup and history-access checks for an explicitly expected
account. Consume the merged verified temporary operation and account-owned health
instead of rebuilding them. Return useful metadata even when no read can be attempted,
and preserve operational errors so callers never mistake a failed check for a denial.
Inputs: desc.md (`382c911`), the completed traverse/finding.md (`f174e90`), current
Telethon1.45.0 and the four executed contract-probe groups.

### Huge Hard Blockers

#### Planning Blockers

None identified. The expected account/lifetime and health interfaces are merged at
30ba706. Schema, cache, budget and error-composition questions have been inspected
and probed. Exact input/result/error decisions below resolve remaining local choices;
no external assumption is being substituted for a missing architectural decision.

The known hashless CommunityForbidden/file-cache failure is not assumed fixed. It is
an explicit source error that this API preserves and documents; no universal backend
success is promised. Live server behavior is not claimed from synthetic replies.

#### Execution Blockers

None external for the six offline steps. The fresh plan critic and any experiment it
requires must run before implementation. The project venv has Python3.11.10 and
Telethon1.45.0; source fixtures and temporary SQLite sessions/budgets are available.
No live account, login code, joining permission, unmerged #17 or another machine is
needed. PR/merge gates are later work, and merge still requires separate authorization.

### How this implementation moves toward desired state

The new layer adds only group-reference interpretation, matching/projecting actual
replies and deciding whether a history result establishes read access. The facade
supplies the existing verified handle and performs the existing semantic health
assertion after the complete positive result has been built. Current session, budget,
request policy, source evidence and cleanup code remain unchanged.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Establish real-source test fixtures | Offline group replies/errors through actual SDK and the merged ownership path |
| 2 | Build reference/value/resolution domain | Explicit group identity, qualified portable lookup and bounded source queries |
| 3 | Build the access observation | One admitted history probe, precise outcomes/errors and validated positive evidence |
| 4 | Wire the public surface and SDK requirement | Two facade methods, exports and consistent dependency metadata |
| 5 | Complete public-path coverage and documentation | Acceptance cases and exact user-facing contract |
| 6 | Verify and checkpoint | Measured tests, separate product/work commits and truthful issue status |

## Binding public contract

### Signatures and values

Public methods:

```python
await tg.lookup_group(target, *, account_id=expected_id)
await tg.check_group_access(target, *, account_id=expected_id)
```

The keyword-only account_id has no default. It is the expected positive Python
integer, excluding bool, checked by the existing owned-operation boundary before
client construction. Do not duplicate that validation outside its isolation scope.
Syntax validation for the target is pure and can precede the boundary; its local
GroupReferenceError suppresses incidental exception context.

New frozen dataclasses in tgdata/group_operations.py:

| Value | Fields |
|---|---|
| GroupMetadata | id: Optional[int], peer_id: Optional[int], title: str, username: Optional[str], kind: str, participants_count: Optional[int] |
| GroupLookup | account_id: int, target: str/int safe label, group: GroupMetadata, member: Optional[bool], request_needed: Optional[bool]=None, requires_payment: Optional[bool]=None, preview_expires_at: Optional[datetime]=None |
| GroupAccess | account_id: int, target: str/int safe label, status: str, lookup: Optional[GroupLookup]=None, reason: Optional[str]=None |

GroupAccess derives group and member from lookup (or None), and readable from status:
readable=True, denied=False, unprobed=None. It does not duplicate independent mutable
metadata. Its to_dict contains its dataclass fields plus readable; group/member live
inside the nested lookup in that dictionary. All values have to_dict producing fresh
plain dictionaries; nested expiry is UTC ISO8601 text, unknowns are None, IDs remain
Python integers. This is not a new versioned message-batch wire format. No raw SDK
object/client/access hash is a public result field.

Export GroupMetadata, GroupLookup, GroupAccess, GroupReferenceError and
GroupResponseError. The two errors are respectively ValueError and RuntimeError
subclasses with generic text and suppressed incidental context. Do not register them
as health failures. Existing GroupAccessError/GroupInfo retain their old meanings.

### Reference rules

Use a small private frozen target value: kind(handle/invite/id), raw value hidden from
repr, and safe label. Inputs are Python int (not bool) or str only; no raw SDK objects.
Strip outer whitespace. Signed decimal strings become ints. Numeric references must
be nonzero and within signed64-bit bounds; reject conversion/range failures locally.

Username candidates use 1–32 ASCII letters/digits/underscores starting with a letter.
This is syntax, not proof of a valid or existing Telegram username; the server validates
it. Accept bare names, @names and http/https or scheme-less t.me/telegram.me username
links, with optional www and one trailing slash. Support /+hash and /joinchat/hash
invites on those hosts. Invite hashes are case-sensitive ASCII letters/digits/_/-,
1–256 characters. Reject credentials, ports, queries, fragments, posts/deep-link paths,
other schemes/hosts and empty components. Keep the grammar explicit; do not invoke
the SDK's general string resolver. Bare me/self are literal username candidates, never
SDK self aliases; a server-resolved user is rejected as a non-group.

Handle labels are lowercase names; numeric labels are ints. Invite labels are
`invite:` plus the full SHA256 of the hash. Original SDK exceptions retain their
normal request attributes; the guarantee here is no raw invite token in the result
or health target label, not rewriting the SDK exception object.

Numeric routing is local and bounded:
- Marked basic-group ID: derive its positive ID and issue GetChats directly.
- Marked channel ID: require an exact session row with a valid signed64 integer hash
  (zero allowed); no hash guess or dialogs fallback.
- Bare positive ID: inspect exact basic-group and channel rows only. Exactly one
  usable group namespace is required. Ignore user rows as non-group candidates;
  reject zero/multiple group candidates or unusable channel hash. Do not query SQLite
  with a computed marked value outside signed64; an out-of-range candidate is absent.

Validate row identity/shape before constructing input peers; do not catch arbitrary
storage exceptions as “missing”. Source exceptions must propagate unchanged. Never
call get_entity/get_input_entity on a user-supplied string or enumerate dialogs.

### Resolution and metadata

All source calls use operation.client inside the original task/lifetime and retain
its constructor policy. No method retry, login, join or sleep layer is added.

- Handle: ResolveUsernameRequest, require ResolvedPeer with PeerChat/PeerChannel;
  PeerUser is a GroupReferenceError. Select exactly one matching marked group entity
  from its chats vector. Missing/duplicate/mismatched replies are GroupResponseError.
- Numeric: direct GetChatsRequest([id]) or GetChannelsRequest([InputChannel(id,hash)]).
  Accept Chats/ChatsSlice with exactly one matching typed target entity. Do not use
  generic get_entity or translate native exceptions escaping a network helper.
- Invite: CheckChatInviteRequest only. Plain ChatInvite produces metadata with absent
  IDs/username and member=False; request_needed is its actual flag and requires_payment
  is whether subscription_pricing is present. No peer, no history from this form.
  ChatInviteAlready projects its chat and member=True. ChatInvitePeek projects its
  chat and member=False and retains its optional UTC expiry. No implicit import/join.

Known entity families: Chat, ChatForbidden, Channel, ChannelForbidden, Community,
CommunityForbidden. ChatEmpty and inactive/migrated basic Chat are explicit unavailable
reference errors; no silent migration. Unrecognized/malformed result shapes are response
errors. Validate positive IDs and representable canonical signed64 peer IDs before
projection; title must be a string, username absent/string, optional counts nonnegative
integers. Do not mutate the source entity. Match typed peers, not bare numeric IDs.

Kinds: group for basic chats; megagroup/channel from explicit Channel flags; community
for Community; unknown when a channel-family subtype is not established. Plain invite
flags supply group/megagroup/channel or unknown for an unspecified channel-family subtype.
For ordinary full Chat/Channel/Community, member is not left. For forbidden/min forms,
member is None unless the invite wrapper explicitly establishes Already/Peek semantics.
A full non-min Channel's join_request can supply request_needed; absent/partial or
inapplicable hints stay None. Payment is unknown outside a source form that supplies
pricing evidence; never default an unobserved payment requirement to False.

Private peer construction is explicit: basic-group input uses its validated ID;
channel-family input requires a signed64 integer hash and non-min metadata. Missing
hash/min means no usable peer, not a fabricated zero. A provided zero hash remains
zero. Use these guarded concrete input peers, avoiding implicit resolution RPCs.

The source SDK still performs its ordinary entity caching before returning a reply.
For hashless CommunityForbidden, file-session IntegrityError propagates; stored-memory
mode may return a valid no-peer observation. Do not patch session classes, disable
entity saving or mask that current SDK limitation in this feature.

### Access and health rules

A private resolver returns the complete GroupLookup plus an optional private input
peer. lookup_group exposes only the lookup. check_group_access uses both without a
second metadata lookup. The private helpers consume the existing operation handle;
they never construct or retain a client independently.

No peer after a recognized successful resolution → GroupAccess(unprobed, reason=NO_PEER,
lookup=the complete lookup). Otherwise issue exactly one logical GetHistoryRequest:
peer=the concrete peer, offset_id=0, offset_date=None, add_offset=0, limit=1, max_id=0,
min_id=0, hash=0. Existing budget admission/re-verification/settlement remains authoritative.

Require Messages, MessagesSlice or ChannelMessages with a finite messages vector
of at most one recognized Message/MessageService/MessageEmpty. Validate any supplied
message peer against the requested group; a missing peer is allowed only for the
optional MessageEmpty representation. A valid empty vector is readable. A different
result type, malformed vector, contradictory peer or MessagesNotModified is a local
GroupResponseError, unless the SDK/budget already raised its own error first.

Catch only actual RPCError around the group resolution/history work. Classify with
include_reported=True because the source hook may already have recorded it. Convert
only NO_ACCESS/group findings into GroupAccess(denied, reason=finding.error), keeping
lookup when it exists. Re-raise all other RPCs unchanged; do not catch local/native
errors or cancellation as a result. No manual ambient health.report call is needed.

The facade builds the complete GroupAccess before calling observation.confirm_group_access
for readable only. The existing boundary decides whether recovery is allowed. Metadata,
unprobed and denied results never assert access. Cancellation/failure before a valid
complete result cannot recover. A later cancellation during cleanup does not undo
already-established source evidence; primary cancellation and notification timing still
follow Stage1/Stage2. No canonical alias migration or extra derived-denial event path.

## Step1 — Establish the real-source test fixture

### Proposed changes

Create tgdata/smoke_tests/test_34_group_access.py. Reuse test32's actual factory/client/
session/budget setup and test33's inspected sender/error adapter where appropriate.
Extend synthetic group replies through real TL serialization/deserialization and SDK
result handling; keep requests/error association from the actual configured sender.
Block sockets, login-code methods, join/import requests and dialog enumeration.

Keep file and store session configurations, inspect actual outgoing group requests,
and expose deterministic barriers for overlap, pending reads and delayed cleanup.
This is test scaffolding, not a simulated GroupAccess-returning engine. Add test cases
alongside each following domain change; full public execution waits for step4.

### Output

A transport-faithful offline fixture and staged acceptance functions for the new API.
### Safe in nature

True — test-only additions; no existing behavior or external account is changed.
### Peripheral concepts

TL serialization, actual RequestState/RPC errors, socket forbidding, Stage1/Stage2,
SQLite/session stores, real asyncio scheduling.
### Hardness Lvl

3/5 — the fixture must observe the boundary, not supply its conclusions.

## Step2 — Implement reference, value and resolution behavior

### Proposed changes

Add tgdata/group_operations.py with the private target, pure parser, frozen result
values, local errors, recursive plain conversion and bounded resolver described above.
Use ordinary functions receiving the verified operation; do not create GroupEngine.
Group facts come from matching reply entities, with explicit handling for invite forms,
forbidden/min/Community shapes, unavailable basic groups and source errors.

Keep the parser's known conversion catches local; avoid catches around awaited source
work that infer invalid input from ValueError/TypeError/KeyError. Reuse SDK constructors
and canonical peer utilities only with validated, concrete inputs. Do not change the
existing models.py, session/cache implementation or factory policy.

### Output

Qualified immutable lookup values and bounded reference routes on an existing handle.
### Safe in nature

False — defines a new public contract and its source/query interpretation.
### Peripheral concepts

Reference namespaces, safe labels, optional facts, UTC expiry, source entity matching,
SDK cache behavior, GroupInfo compatibility and signed integer bounds.
### Hardness Lvl

4/5 — incomplete evidence and malformed evidence must remain distinguishable.

## Step3 — Implement the bounded access observation

### Proposed changes

In the same domain module, reuse one resolution, make the single concrete history
request when possible, validate its actual reply and build the complete access value.
Apply the narrow RPC conversion rule; preserve other exceptions/cancellation exactly.
Return no message content. Keep full lookup qualifications in every result that has
completed lookup, and return lookup=None when resolution itself produced a group denial.

The helper returns its decision; it does not call private monitor record methods or
create a health event. The facade will provide the explicit semantic confirmation.

### Output

Readable/denied/unprobed behavior with bounded read cost and original failure meaning.
### Safe in nature

False — sends a budgeted request and establishes the evidence consumed by health.
### Peripheral concepts

ReadBudget, response validation, source error identity, partial metadata, same-call
failure scope, entity-cache errors and caller cancellation.
### Hardness Lvl

4/5 — the positive evidence boundary must precede every success claim.

## Step4 — Wire the public API and declared SDK requirement

### Proposed changes

Add the two methods to tgdata/tgdata.py, directly using _account_health_operation with
method names lookup_group/check_group_access and the parsed safe label. Do not decorate
with legacy _reported or instantiate an extra engine. Do not mutate current_group,
primary client/pool or shared configuration. Confirm group access only after receiving
the complete validated readable result; return through the existing cleanup boundary.

Export the values/errors from tgdata/__init__.py. Set Telethon>=1.45,<2.0 consistently
in setup.py and requirements.txt and replace the stale minimum-version comments. The
verification target remains exactly1.45.0; no compatibility shim for1.33 or version bump
of tgdata is required. Keep Python3.7-compatible syntax/APIs.

### Output

Callable public methods, documented import names and consistent installation metadata.
### Safe in nature

False — changes package exports, facade methods and dependency requirements.
### Peripheral concepts

Import graph, owned versus legacy health, configured source policy, packaging,
keyword-only expected account and method-specific restriction recovery.
### Hardness Lvl

2/5 — narrow wiring through the already-merged foundation.

## Step5 — Complete public-path acceptance and product docs

### Proposed changes

Complete suite34 against the public methods. Required case families:

1. Accepted reference forms/normalization and invalid syntax/types/ranges before
   configuration/source I/O; literal names do not activate SDK self aliases.
2. ExpectedB/cachedA/actualB result/event/snapshot ownership; expectedA/actualB refusal
   before group work; invalid/missing authentication without login codes.
3. Fresh handle replies for basic, mega, broadcast and Community; user rejection,
   wrong/missing/duplicate typed matches and unavailable/migrated/empty groups.
4. Marked basic ID without cache; marked channel with exact large/zero hash; unique
   bare IDs, user-only rows, two group namespaces, absent/unusable rows, extreme
   integer bounds and real local cache failures. No dialog fallback.
5. Plain/Already/Peek invites: unknown IDs, wrapper membership, UTC expiry and nullable
   request/payment hints; token retained only for the request, never as the output
   or health target label; no join/import request under any response.
6. Full/forbidden/min/missing-hash source forms, including legitimate empty history,
   no-peer unprobed and the measured file/store hashless-community difference.
7. Exact one history request with limit1/hash0, retained lookup qualifications,
   no history for plain preview/no peer, no duplicate metadata query.
8. Actual sender-built group refusal during metadata/history, correct incomplete
   lookup, same owner/source health; other auth/wait/server/network/local errors
   propagate. Numeric server failure remains the original RPC under the constructor
   policy, never a reference error.
9. Real budget cost/refund/refusal and later identity re-verification; a refused or
   malformed read never masquerades as readable. SDK/budget errors precede domain
   projection where those existing components detect a fault first.
10. Prior denial persists on lookup/unprobed/failed/cancelled work; validated history
    can confirm recovery while same-call/older-operation/invalid-handle guards remain.
    Force overlap rather than trusting immediate-future concurrency.
11. Callback errors/cancellation, delayed/failed disconnect and caller cancellation
    preserve the public outcome; notifications start after the source attempt settles.
    Check persistent client/pool/current_group are unchanged.
12. Immutable values, fresh JSON-ready dictionaries, complete nested lookup, stable
    derived views and exports; old public health/GroupInfo/discovery behavior unchanged.

Use explicit real-component assertions, not a numeric test-count target. Pure parser/
projection tests may complement the public-path cases, with their limits stated.

Add docs/group_operations.md and a README section with usage and exact input, outcome,
error, budget, privacy-label, health-reference, source-cache and timing qualifications.
Explain that access checking already includes lookup. Update docs/account_operations.md
to point from the private foundation to the new public APIs, and add the measured
suite34 entry to tgdata/smoke_tests/README.md. No SDK backend repair or live-test claim.

### Output

Public contract coverage and documentation that describes what the implementation
actually does, including the specific known source limitation.
### Safe in nature

True — tests/docs only; no extra production behavior or external actions.
### Peripheral concepts

Actual error construction, forced overlap, conditional metadata, consumer ergonomics,
legacy compatibility, offline versus live evidence, SDK support limits.
### Hardness Lvl

4/5 — the intersections matter more than isolated helper coverage.

## Step6 — Verify and checkpoint

### Proposed changes

Run suite34 first, then all supported offline suites12–19,22–30,32–33 on the final
product (no duplicate unchanged already-passed suite34 run). Use the project venv from
this worktree and normal `python -m` entry points, especially test18's multiprocessing
case. Confirm imports come from this worktree. Tests12/13 receive a verified missing
config, keeping their three known live checks skipped; test12 may need normal local
socket escalation. No blanket pytest, old live suites or unmerged #17 suite31.

Compile all tgdata/examples Python and check Python3.7 grammar; run the daily demo and
fresh/restarted backfill demos in temporary directories. Report actual passes separately
from skips. Follow task-impl's correction limit: only small local nonarchitectural
corrections, recorded and retested; an architectural failure stops for the required
reconsideration. Never change an expectation to hide a failure.

Review the diff against this plan and run whitespace checks. Commit code/tests/product
docs/dependency metadata together, then work-folder verification/handoff separately.
Push the existing linked branch and tick only completed committed artifacts on #7.
Leave Stage3 merge-check/PR/fresh PR critique and any merge pending later authorization.
Preserve all earlier branch archives, original untracked files, duncan and the stray guide.

### Output

Measured implementation verification and a reviewable, committed/pushed checkpoint.
### Safe in nature

True — offline verification and isolated feature-branch checkpoints.
### Peripheral concepts

Actual test counts, package imports, SDK1.45, compatibility grammar, separate process
notes, CONTRIBUTING stage status and later review/merge boundaries.
### Hardness Lvl

2/5 — established verification tools, with a larger new domain suite.
