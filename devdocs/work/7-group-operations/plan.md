---
model: unknown
effort: unknown
---

# #7 — implementation plan, revision 1

### What is the task

Add ephemeral group lookup, actual read-access checking and explicitly admitted
joining to TgData. Callers receive portable observations instead of interpreting
SDK entities. A separate durable account allowance bounds actual join attempts,
while existing connection/session/proxy/read-budget controls remain authoritative.

### Huge Hard Blockers

#### Planning Blockers

None identified. The real 1.45.0 probe at `probe_group_seams.py` resolves the
wrapped-reply, retry seam, fresh identity and health-recovery premises. There is
no inherited OPEN blocker in desc.md. Caller-set limits and a rolling 24-hour
shared-file ledger are the documented working design, not an inferred safe rate.

#### Execution Blockers

None for these implementation steps. Live acceptance requires designated accounts,
groups and authorization and is excluded. PR/merge remains a later requested
stage. Model/effort unavailable is a recorded §9 process limitation, not a runtime
premise silently treated as verified.

### How this implementation moves toward desired state

Define values and parsing first, then durable admission and its client-factory
seam. Build resolution/read/join behavior on that foundation. Wire it to the
facade and health with explicit evidence control. Test the public composition
against real SDK dispatch and SQLite before documenting and committing delivery.

### High-Level Summary

| Step | Description | Expected Output |
|---|---|---|
| 1 | Group references, errors and portable values | `group_operations.py` contract and strict parser |
| 2 | Durable join attempt allowance | `join_budget.py`, explicit policies and atomic claims |
| 3 | Actual-send admission and factory wiring | `join_client.py`, optional `join_budget` on every factory client |
| 4 | Group engine and health-aware facade | lookup/check/join/status methods, one ephemeral client each |
| 5 | Offline behavioral coverage | `test_20_group_operations.py` on real SDK/SQLite |
| 6 | Public documentation | README contracts/examples and smoke-test index |
| 7 | Verify and commit | supported offline suites, code/docs and work-note commits |

## Step 1 — Define references and observations

### Proposed changes

Create `tgdata/group_operations.py`, initially values/parsing. Runtime Python3.7
compatible dataclasses/typing; no new dependency. Export through `tgdata/__init__.py`
after wiring. Keep existing `GroupInfo` untouched.

- Local `GroupOperationError` base with `__suppress_context__=True` and subclasses
  `GroupReferenceError` and `GroupResponseError`. No user input or vendor payload
  in their message. Ordinary RPC/auth/transport errors retain identity/traceback.
- Internal frozen `_Target(kind, value, label)`; invite value excluded from repr.
  Handles: bare or @ handle and optional http(s) Telegram short link; validate
  4–32 ASCII letter/number/underscore characters, starting with a letter. Hosts
  exactly t.me or telegram.me (optional www). Invite forms `/+HASH` and
  `/joinchat/HASH`, hash ASCII letters/numbers/underscore/hyphen, 1–256 chars.
  Preserve hash case; lower handles. Reject URL userinfo/ports/query/fragment,
  unrelated/deep paths, phone strings, empty/bool/other object values. Allow
  nonzero signed integer IDs (including numeric strings) for lookup/access;
  positive IDs need existing unambiguous group cache resolution. Join accepts
  handles/invites only. Never interpolate original input in local errors.
  Label is handle, int ID or `invite:` plus first16 hex SHA256(hash); no raw hash.
- Frozen `GroupMetadata`: id and peer_id optional int, title optional str,
  username optional str (without @), kind `group|megagroup|channel|unknown`,
  participants_count optional int. peer_id uses Telethon's marked peer convention.
- Frozen `GroupLookup`: target safe label, group GroupMetadata, member optional
  bool, request_needed optional bool, requires_payment bool, preview_expires_at
  optional datetime. `to_dict()` emits only JSON-ready values/UTC ISO timestamps.
- Frozen `GroupAccess`: target, group optional GroupMetadata, member optional
  bool, status `readable|denied|unprobed`, reason optional safe error name;
  `readable` convenience property returns True/False/None respectively.
- Frozen `GroupJoin`: target, group optional GroupMetadata, status
  `joined|already_joined|requested|interaction_required|payment_required`,
  bot_id/query_id optional ints. `member` property True only for joined/already,
  otherwise None (request pending does not prove nonmembership forever).
  to_dict for all results; no raw TL objects, access hashes, invite links or users.

### Output

Documented importable value shapes and deterministic parser; legacy model unchanged.

### Safe in nature

True — isolated new contract, no existing call behavior changed.

### Peripheral concepts

GroupInfo, marked peer IDs, datetime serialization, private invite diagnostics.

### Hardness Lvl

3

## Step 2 — Persist the join allowance

### Proposed changes

Create `tgdata/join_budget.py`. Public `JoinBudget(path, *, clock=time.time)`,
`configure(account_id, daily_limit)` and `status(account_id)`. Require persistent
file, positive integer account_id and nonnegative integer daily_limit, bools
rejected, SQLite signed63-bit range. No warmup, refund, credentials or targets.
All policy updates preserve claims. No policy is an explicit configuration error.

Use separate `tgdata_join_meta` (version1), `tgdata_join_accounts` (account ID,
limit,last_clock), `tgdata_join_attempts` (integer primary key, account, admitted_at)
and indexed account/time. Can coexist with ReadBudget in the same file without
schema/unit interference. Short-lived connections, BEGIN IMMEDIATE, 5s busy timeout,
no transaction crosses an await. Last observed clock per account never decreases;
prune attempts at `admitted_at <= now-86400`. Validate finite UTC clock values.

Private `_claim(account_id)` atomically reads current policy/usage and inserts
exactly one charge only if remaining>0. Refusal commits clock/pruning before
raising. Return no refund token. Cancellation/error after claim leaves it charged.
Status contains account_id, limit, used, remaining, observed_at, next_available_at,
retry_after, and window_seconds in to_dict. For reduced policy below usage,
next_available_at is the expiry needed to get below the cap, not simply oldest.
Zero limit has no timed availability. Claim counts use SQL COUNT, not message sums.

Errors `JoinBudgetError`, `JoinBudgetConfigError`, `JoinBudgetStorageError`,
`JoinBudgetExceeded` (status/account_id/retry_after), `UnsupportedJoinRequest`.
Local bases suppress unrelated implicit RPC context. Sanitize native path/SQLite
failures to local errors naming error type only. Cleanup cannot replace a primary
failure; no DB close/rollback error may become a Telegram verdict.

### Output

A restart-safe, concurrent local join allowance with portable status and failure types.

### Safe in nature

True — separate tables and code; no changes to existing read-budget schema.

### Peripheral concepts

SQLite locking, clock rollback, policy replacement, local error provenance.

### Hardness Lvl

4

## Step 3 — Guard actual join sends

### Proposed changes

Create `tgdata/join_client.py` with JoinClientMixin and a sender adapter. Supported
mutations are exactly channels.JoinChannelRequest and messages.ImportChatInviteRequest.
Recognize the existing budget client's known invocation-wrapper set explicitly;
recursively unwrap at most8 levels. Unknown wrappers containing join-bearing query,
unknown request families returning ChatInviteJoinResult and any batch containing
a join fail before send. Non-join requests pass unchanged. No read-policy refactor.

When `_tgdata_join_budget` is set, wrap sender in `_call`, before actual SDK retry
loop execution. The adapter's `send` returns a coroutine. For each call, fresh
`get_me(input_peer=False)` yields account ID; if None, GetState surfaces actual
auth verdict then local error if still no identity. Validate ID. Synchronously
claim, then underlying sender.send with no intervening await. Each retry pays;
no catch/refund on transport error, cancellation, already-member or pending reply.
Forward sender attributes and ordered unchanged. Resolving a request costs no join.

Add `join_budget=None` at end of both `TgData.__init__` and
`ConnectionEngine.__init__`. Keep/store/pass it and assign on every `_new_client`.
MRO: answer evidence, JoinClientMixin, BudgetClientMixin, per-call flood threshold,
base client. With no join budget, existing raw-client behavior remains unchanged;
new public join_group still requires policy. This is a library admission boundary,
not a security sandbox around arbitrary external Telegram clients.

### Output

Every configured factory client, including ephemeral/pool clients, guards SDK join
retries under fresh account authority, independently of message-read admission.

### Safe in nature

False — changes shared client composition; old suites and guard interaction required.

### Peripheral concepts

SDK _call retries/cached waits/resolution, invoke wrappers, fresh self cache, read guard.

### Hardness Lvl

5

## Step 4 — Resolve, check and join through one ephemeral client

### Proposed changes

Finish `GroupEngine(connection_engine)` in group_operations.py and expose
`TgData.lookup_group(target)`, `check_group_access(target)`, `join_group(target)`.
Each facade parses/validates before health context, then opens exactly one existing
`ephemeral_client()`; no session(), no pool/current_group change, no start/login.
Private helpers take the opened client; one public operation never calls another.
Add `get_join_budget()` returning None with no policy and otherwise status from
one ephemeral client and fresh account ID, analogous to get_read_budget semantics
but use-and-close. Export values/ledger/errors from package __init__.

Resolver:
- Handle: ResolveUsernameRequest, require peer chat/channel and matching chats
  entity; reject User/empty/deactivated/migrated basic-chat entities with local
  reference error rather than silently selecting another group. No phone lookup.
- Numeric: get_entity through known session cache; require group/chat kind;
  ambiguous/missing ID errors remain explicit, never walk all dialogs implicitly.
- Invite: CheckChatInviteRequest; Already projects chat/memberTrue, Peek projects
  chat/memberFalse/expiry, plain ChatInvite projects missing-ID metadata/memberFalse,
  request_needed and subscription_pricing. Never import while resolving.
- Full Chat/Channel membership is not left when complete/active; min or forbidden
  entity membership remains None. Derive group type using megagroup/broadcast.
  Banned/forbidden peer can still carry metadata but must not manufacture a read.

Access: resolve then build input peer when possible, issue raw GetHistoryRequest
limit1 with existing client (read budget applies). Return readable only for a
normal expected messages result. No peer yields unprobed with safe reason
`NO_PEER`. Catch only actual errors classified NO_ACCESS/group from resolver or
history; health.report the original then return denied with optional metadata.
All other errors propagate; preview already-member status does not skip read proof.
For missing access_hash, return unprobed rather than falsely denied/readable.

Join: require a JoinBudget before client creation; fresh ID plus budget.status
requires policy even for existing membership. Resolve same client. Existing
member returns already_joined without claim. Paid preview returns payment_required
without send. Otherwise JoinChannelRequest for resolved Channel or
ImportChatInviteRequest for invite. Explicit flood_sleep_threshold=0 for these
new operation RPCs (authorization context itself retains existing default).
Return joined for ChatInviteJoinResultOk; process available reply.updates entities
locally and choose matching chat metadata if available (for invite use first
valid chat only when unambiguous). Preserve preflight metadata when absent.
No follow-up network request after acknowledgment. Catch UserAlreadyParticipant
as already_joined and InviteRequestSent as requested; these admitted attempts
remain charged. Map raw RPC message STARS_PAYMENT_REQUIRED to payment_required
(the installed SDK has no generated error class). WebView becomes
interaction_required with bot_id/query_id; no URL invention or user records.
Unknown reply yields GroupResponseError, retained charge and no false success.

Health: extend HealthMonitor.call with optional `recover_group=True`, captured on
_Call. _recover's group branch alone honors it; default old behavior unchanged.
New contexts use False; only after actual successful expected history response
set that call's recover_group True. Health still reports original failures and
waits/auth evidence. Safe parser label only, never raw invite. No logging raw
result or request. Ephemeral cleanup behavior stays owned by existing context.

### Output

Usable public group methods and portable status, with truthful evidence and limits.

### Safe in nature

False — facade and shared health context change; defaults preserve existing methods.

### Peripheral concepts

GroupInfo, stored group cache, read budget, auth errors, health.report, cleanup/cancellation.

### Hardness Lvl

5

## Step 5 — Exercise real offline behavior

### Proposed changes

Add `tgdata/smoke_tests/test_20_group_operations.py`, ordinary executable suite in
the existing style. Block socket connects; temp config/session-store/SQLite only.
Use real factory class + real SDK _call, scripted sender replies and stand-in
connect/disconnect hooks; never replace the admission/projection behavior tested.
Use real TL byte roundtrips where wrapper shape matters and spawned processes for
ledger contention. Tests must cover these independent behavioral groups:

1. Default factory compatibility and unchanged GroupInfo; no primary client used.
2. Parser accepted handles/IDs/invite forms, case preservation and invalid inputs;
   invalid input causes zero clients/network and sanitized exceptions.
3. Handle/group/basic-chat/forbidden projections; reject user/missing peer results.
4. Invite Preview/Already/Peek and expiry; lookup sends no join/history requests.
5. Public readable nonmember and empty history; one limit1 read, budget settlement.
6. Group denial during resolve/read returns denied and reports health once;
   auth/wait/network/local quota failures remain errors.
7. Peerless preview returns unprobed; unknown or absent access hash never fakes read.
8. Handle/invite joins, preflight already member no send/charge, actual already
   error still charged; approval request, wrapped Ok, WebView and payment outcomes.
9. No post-ack enrichment; nested group cache processed; unknown reply stays charged.
10. Missing policy/zero cap refuse before mutation; lowered cap preserves usage;
    account isolation, expiry, clock rollback and correct next_available_at.
11. Persistence/restart, same-file ReadBudget coexistence, corruption/read-only or
    missing storage failure before send, sanitization and cleanup provenance.
12. Concurrent processes compete for fixed number of attempts with no overspend.
13. SDK retry consumes each send, exhaustion stops next send, cancellation/failed
    reply stays charged, no transaction lock while awaiting remote response.
14. Fresh self identity vs stale cache and changing fresh IDs; no charge on failed
    identity or request resolution; wrappers and batches fail closed as specified.
15. Factory controls inherited by every client and read/join budgets independent.
16. Exact ephemeral create/connect/auth/disconnect on success, denied, error and
    cancellation; no terminal prompt or persistent/current_group mutation.
17. Health metadata/join do not recover group denial; read success does, waits and
    account recovery retained; local errors inside RPC handlers do not fake events.
18. JSON-ready value dictionaries/immutability; private tokens absent from result,
    log and health fields; no saved message-sender rows caused by helper projection.

### Output

Reproducible offline evidence for public contract and dangerous composition seams.

### Safe in nature

True — test-only synthetic data, no Telegram mutation.

### Peripheral concepts

Real SDK scripted sender, multiprocessing SQLite, cancellation, health capture.

### Hardness Lvl

4

## Step 6 — Document the caller contract

### Proposed changes

Add README section with the three awaitable methods, result status examples,
accepted references/ID-cache limits, optional fields, read-budget charge on access,
JoinBudget configuration (caller-chosen example limit, not safety advice), status
and quota exceptions. Explain 24-hour attempt unit, retries/failure retained,
already-observed no-op, shared-file coordination, sync quick local storage,
explicit external interaction requirements and offline verification bounds.
Add test20 invocation and coverage in smoke_tests/README.md. No live test execution.

### Output

A caller can configure and interpret the feature without reading SDK source.

### Safe in nature

True — documentation only.

### Peripheral concepts

Authentication, existing read-budget usage, health events, smoke test commands.

### Hardness Lvl

2

## Step 7 — Verify and commit

### Proposed changes

Compile package/tests; run new test20 and supported offline suites19,18,17,16,15,
14,13,12 with .venv/bin/python on Telethon1.45.0. Run repository-wide offline
checks if an aggregate exists; account-dependent tests00–11 remain explicitly
skipped rather than attempting login/network. Inspect diff/check and no duncan.
Only local nonarchitectural corrections during verification, enumerate each.

Commit code/tests/public docs together; commit task-folder implementation and
verification notes separately. Push branch and update issue #7 step5 honestly;
keep steps6/7 unchecked. No merge/PR in this invocation. Record remaining live
bounds and §9 model metadata limitation.

### Output

Tested committed implementation and honest issue/task records, ready for merge check.

### Safe in nature

False — publishes branch commits/issue progress; restricted to authorized feature.

### Peripheral concepts

Git staging isolation, CONTRIBUTING status, archive-only work notes.

### Hardness Lvl

2
