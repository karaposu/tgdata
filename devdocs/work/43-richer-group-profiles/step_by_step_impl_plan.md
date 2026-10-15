---
model: gpt-6-astra
effort: xhigh
---
# Richer group profiles — implementation plan, revision 1

## What is the task
Expose a portable profile observation under the existing verified-account
operation, with description, optional counts and an optional bounded pin search.
Keep source errors, unknown values and incomplete results explicit, while
preserving current public group APIs and their ownership/cleanup contracts.

### Huge Hard Blockers
#### Planning Blockers
None identified. Source contracts and Telethon 1.45.0 constructors establish the
available metadata/pin representations. Real SDK composition remains a prebuild
gate, not a premise silently supplied by a mocked public profile method.
#### Execution Blockers
None for offline implementation and verification. Live Telegram permission and
field availability are not established by this run; a real account is unnecessary
for the bounded local projection contract. No live PASS will be claimed.

## How this implementation moves toward desired state
Add one module beside group_operations, reusing its target resolver, canonical
identity and metadata projection. Keep the existing owned operation, budget
adapter and heartbeat sender unchanged. A full reply is projected before optional
pin work. The caller gets either one immutable result or the original failure,
with completed profile evidence attached when optional pin work fails.

## High-Level Summary
| Step | Description | Expected Output |
|---|---|---|
| 1 | Portable values and full-profile projection | group_profile.py values and validated metadata |
| 2 | Optional bounded pin observation and partial failures | One filtered search, explicit coverage |
| 3 | Public verified composition and exports | TgData.get_group_profile and root imports |
| 4 | Public-path tests and usage contract | test_45_group_profile.py and docs/group_profiles.md |
| 5 | Relevant/full verification and checkpoints | Product commit plus separate work evidence |

## Prebuild before any product step
Critic must define a combined experiment using actual Telethon 1.45.0 dispatch,
TL serialization/decoding, existing verified operation, owned health, StoredSession/
SQLiteSession, ReadBudget and heartbeat. Synthetic server packets may exercise
those real local components but do not qualify Telegram's live permissions.
At minimum observe full basic/channel responses, zero/absent counts, filtered
SearchRequest admission/refunds, original errors/health keys, owner changes before
admission and actual cleanup cancellation. No prototype implementation can supply
the behavior whose existing composition is being qualified.

## Step 1 — Profile values and full metadata
### Proposed changes
Add tgdata/group_profile.py importing existing private group-operation helpers.
Define frozen GroupPinnedMessage(id, kind, date, text) and GroupProfile(account_id,
target, group, about, online_count, observed_at, pinned_messages, pins_status,
pins_total, pins_observed_at). Pins are a tuple; output dictionaries are detached,
JSON-ready, with UTC ISO8601 dates and integer IDs. Exclude SDK objects, access
hashes, user/contact rows, clients and credentials. Use repr=False for free text.
Properties are unnecessary beyond the existing group metadata object.

Validate pinned_limit as a Python integer excluding bool, range 0..100. Zero
means not_requested, no search, empty pin tuple, unknown total/time. Resolve using
_resolve(operation, target). Supported lookup kinds are group, megagroup, channel;
a plain invite/minimal hashless result without a peer, Community or unknown kind
raises GroupReferenceError and performs no full/pin request.

Use messages.GetFullChatRequest for InputPeerChat and
channels.GetFullChannelRequest(InputChannel(id, hash)) for InputPeerChannel.
Require types.messages.ChatFull, the appropriate full_chat constructor and exact
raw ID/namespace. Match exactly one chats entry using _matching; project it using
_project and require a supported kind/expected canonical peer. Full response
description must be str. For channels, participants_count comes only from
ChannelFull (absent stays None), replacing GroupMetadata's possibly older count.
For basic groups it comes from the matching Chat metadata; do not count returned
participant/user vectors or infer online presence. online_count is ChannelFull's
optional field; basic groups report None. Counts must be None or non-bool integers
0..2**31-1. Do not constrain online <= participants: these are observations, not
one atomic census.

Capture datetime.now(timezone.utc) after successful validated metadata. Source/cache
errors propagate untouched; invalid shape is GroupResponseError. Full metadata
failure produces no fabricated partial GroupProfile.
### Output
Portable immutable values and a full-profile helper within the existing model.
### Safe in nature
True — a new unexported module; existing runtime is unchanged.
### Peripheral concepts
GroupMetadata, target resolution, namespace-qualified peers, optional source facts,
UTC times, JSON conversion, retained SDK session cache behavior.
### Hardness Lvl
3

## Step 2 — Bounded pinned-message observation
### Proposed changes
On explicit pinned_limit>0, use the already resolved input peer for exactly one
messages.SearchRequest(q='', filter=InputMessagesFilterPinned(), min_date=None,
max_date=None, offset_id=0, add_offset=0, limit=pinned_limit, max_id=0, min_id=0,
hash=0). No iter_messages, hidden lookahead, pagination, media downloads or retries.
Existing budget reserves the full requested limit and refunds unused response
slots. Refusal remains the existing error; do not silently lower the requested
limit or provision policy. Metadata itself costs no message allowance.

Accept Messages, MessagesSlice or ChannelMessages, with a vector no larger than
the requested limit. Cache-only MessagesNotModified and wrong/malformed responses
raise GroupResponseError (budget may refuse first). Validate each row's distinct
positive signed32 ID and matching group peer; an Empty row may omit peer, with its
identity attributed only to this scoped source request. Message dates must be
aware and normalize to UTC. Message text stays complete (including empty media
captions). Service rows retain date and kind with text=None; Empty rows retain
ID and kind=unavailable with date/text=None. No content/author enrichment.
Return source order. Record source-filter provenance; do not infer pin time or
promise that the message is still pinned after the observation.

Messages is a full vector with total=len(rows). Slice/channel total is its
nonnegative signed32 count; inexact is bool/None. Exact count < returned rows is
malformed. Pin status:
- complete: no unavailable rows, exact result and total == returned rows;
- limited: exact total > returned rows and returned rows == requested limit,
  with no unavailable rows;
- incomplete: inexact results, unavailable rows, or a shorter-than-limit slice
  whose count reports more. Never use short-page length alone as completion.
Successful empty exact response is complete with total=0. Preserve approximate
total as supplied but never infer completion from it. Record pins_observed_at
after projection.

If optional pin send/projection fails, catch Exception or CancelledError only,
attach a frozen completed-profile partial_result with pins_status='failed',
unknown pin total/time and no accepted pins, then re-raise the same exception.
Exception annotation is best effort and must never replace the primary error.
Partial pin rows from an invalid response are not accepted. Metadata remains the
prior successful observation; pin denial does not erase it or become empty.
### Output
One bounded source observation, explicit pin coverage and retained profile evidence.
### Safe in nature
True — still internal until the facade is exposed.
### Peripheral concepts
Budget sender, filtered searches, optional counters, response validity, cancellation,
failure metadata and partial-result custody.
### Hardness Lvl
4

## Step 3 — Public operation and heartbeat
### Proposed changes
Add TgData.get_group_profile(target, *, account_id, pinned_limit=0, heartbeat=None).
Validate reference/limit/heartbeat before client construction. Use existing
heartbeat_kwargs/heartbeat_scope and _account_health_operation(account_id,
'get_group_profile', reference.label); invoke the profile helper and return.
Emit profile/pins completion phases through the scoped observer. Actual SDK
send/answer phases come from the existing factory mixin, including identity and
budget checks. No periodic beats during an unanswered call and no new wait policy.
Use existing heartbeat invalid-callback error (BatchFormatError, a ValueError).

Never call confirm_group_access: a profile/filtered-pin observation is not the
existing history-access probe. Do not add a legacy _reported wrapper. Exceptions
escape the owned context, retaining original request evidence and preventing
success recovery after failed pin work. Existing request/account recovery rules
and post-cleanup notification behavior stay intact. Cancellation during teardown
keeps the existing cancellation outcome; no result-delivery guarantee is added
for a caller that cancels after the helper completed.
Export GroupProfile and GroupPinnedMessage from package root, preserving version
and every existing import/signature. No engine/factory/budget/health changes.
### Output
One additive public method and two public immutable types.
### Safe in nature
False — facade/package import integration touches shared entry points.
### Peripheral concepts
Import graph, account-owned health boundary, task-scoped heartbeat, cleanup and
public export compatibility.
### Hardness Lvl
3

## Step 4 — Contract tests and documentation
### Proposed changes
Add test_45_group_profile.py using the real SDK wire harness from test_34/test_33/
test_32, actual TL replies/errors and SQLite budget/session backends. Socket and
login calls remain forbidden. Do not stub get_group_profile, ownership or budget.
Exercise:
- required account/input validation before I/O; correct B despite cached A;
  wrong expected account and absent auth before any group request;
- supported basic/broadcast/megagroup routes, exact qualified IDs/hash extremes,
  invite already/peek and refusal of preview/no-peer/community;
- empty/Unicode description, missing/zero counts, malformed full types/IDs/
  namespaces/vectors/fields; field counts do not borrow unrelated chat/user rows;
- default pins off and one exact filtered request; zero, limit, short/inexact,
  service/unavailable and invalid/duplicate/wrong-peer pin rows; JSON independence;
- zero budget metadata, pre-send pin refusal, actual charge/refund, owner change
  before claim; original RPC/wait/local errors and complete-profile partial_result;
- source-only owned events, no metadata/pin group recovery, cancellation before
  and during cleanup, cleanup failure precedence, heartbeat callback failures,
  no periodic liveness while held, persistent-client/current_group isolation.
Use per-test/process watchdogs. SDK fixture traffic is synthetic; state clearly
that passing tests do not establish live Telegram permissions.

Add docs/group_profiles.md covering exact fields/status/errors, one-response cap,
source timing, immutable serialization, no general access guarantee, allowance,
zero waits/retries, cleanup limits and usage. Link from README, group_operations
and smoke-test README. Keep #44/#45/#46 out of the product.
### Output
Meaningful public contract suite and caller documentation.
### Safe in nature
True — tests/docs are additive, no production policy changes.
### Peripheral concepts
Real TL/SDK/session fixtures, budget SQL, owned health, packaging test discovery.
### Hardness Lvl
4

## Step 5 — Verify, commit and hand off
### Proposed changes
Compile affected sources and check declared Python3.7 grammar (runtime is3.11).
Run new45 then32/33/34/18/44; then the complete supported31 existing offline
suites plus45 and all7 demos, with explicit live skips and process watchdogs.
Check public exports, clean diff, docs, and source-identical execution; no live
login/join, PyPI release, consumer environment change or branch merge.
Only small nonarchitectural test/setup/reference corrections may be fixed; record
them and rerun affected checks. A design contradiction stops this run.
Commit product code/tests/public docs together, work verification/HANDOFF separately.
Push the linked branch and update #43 honestly through step5; merge check, PR and
fresh PR critique remain unchecked. Preserve original checkout edit, duncan and
unrelated guide edits.
### Output
Verified committed branch and a review-ready status, with evidence limits stated.
### Safe in nature
True — no main/dev mutation or external deployment.
### Peripheral concepts
Supported-suite inventory, package imports, process isolation, commit separation.
### Hardness Lvl
3
