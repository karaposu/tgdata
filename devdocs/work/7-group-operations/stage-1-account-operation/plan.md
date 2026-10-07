---
model: gpt-6-astra
effort: max
---
# Stage 1 implementation plan — revision 2

**Critic folded:** 2026-10-08 — 1 mitigation (2 steps changed, 0 added). Prebuild REORDER experiment PASS; see critic.md and prebuild_probe.py.

Repository convention uses `plan.md` for task-plan's output. Input: this folder's
`desc.md` and completed `traverse/finding.md`. No parent revision 3 steps are resumed.

### What is the task

Create a private, account-owned temporary operation for future #7 features. It
must refuse the wrong or unauthenticated account before the body runs, preserve
configuration and later admission ownership, and complete one close attempt
without replacing the work outcome. No group/health feature is added yet.

### Huge Hard Blockers

#### Planning Blockers

None identified. Installed SDK1.45 source plus same-session auth-policy and actual
disconnect/cancellation probes establish the required seams. The context's private
scope and cleanup limitation are explicit in the description, not assumptions.

#### Execution Blockers

None for offline Stage 1. Live Telegram, another account and merged #17 are not
dependencies. Merge approval and fresh PR review remain separate later workflow.

### How this implementation moves toward desired state

The shared factory remains the source of session/proxy/device configuration. A
private context supplies a fixed constructor policy, connects without login,
proves self, and yields a small handle. The existing budget provider delegates to
that handle when present. A separate close helper handles cancellation independently
of proof and work, so no global owner/task/request registry is needed.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Define owner proof and lifetime | private handle and identity error |
| 2 | Construct/connect/close the owned operation | optional factory policy and private context |
| 3 | Make quota admission agree | optional owner-aware budget identity provider |
| 4 | Prove behavior offline | real SDK, lifecycle and budget regression suite |
| 5 | Document scope and run regressions | maintainer contract and verification evidence |
| 6 | Commit and update stage status | product commit separate from workflow notes |

## Step 1 — owner proof and lifetime

### Proposed changes

Add `tgdata/account_operation.py`, internal module (no top-level exports or new
TgData method). Validate expected account ID as int, not bool, and >0; invalid
expectation raises ValueError before constructing a client. Define
`AccountIdentityError(RuntimeError)` with expected_account_id and actual_account_id
(None if identity cannot be verified), using sanitized numeric diagnostics.

`_AccountOperation` stores one client, expected/verified numeric ID, opening task,
active flag and an auth-error factory supplied by ConnectionEngine. Read-only
`account_id` exposes the verified owner; read-only `client` checks task/lifetime.
`verify_account()` checks active/task, calls real
`functions.users.GetUsersRequest([types.InputUserSelf()])`, validates the single
user's positive ID, checks active/task again and compares with expectation. It
returns the same verified ID or raises; never rebinds. UnauthorizedError/AuthKeyError
become the existing AuthRequiredError via the factory, preserving cause/reason.
Empty/UserEmpty self results mean explicit missing authentication; malformed
response/ID means unverifiable identity error. Do not use cached `_self_id` or
`get_me(input_peer=True)`. `_close()` permanently ends handle admission.

[folded: Risk 1, robust] Identity mismatch, absent/malformed self or authentication
loss marks the handle inactive before raising, even when caught inside the body.
A later proof or client access on that handle refuses; an account becoming valid
again requires a new operation. Transient wait/server/transport errors retain their
original type without rebinding ownership. No additional state machine is added.

### Output

One local ownership/lifetime contract; no new storage/schema, ContextVar, credentials
fingerprint, general client dispatch proxy or health mutation.

### Safe in nature
True — new internal definitions only; not yet called.
### Peripheral concepts
SDK self RPC, authentication errors, asyncio task identity, Python 3.7 compatibility.
### Hardness Lvl
3

## Step 2 — construct, authenticate and close

### Proposed changes

Extend `_new_client(session_file=None, **client_options)` in
`tgdata/connection_engine.py`; pass options alongside existing identity/proxy/session
arguments. Ordinary call sites provide none, preserving defaults. The private
`_account_operation(expected_account_id)` context uses fixed kwargs:
`flood_sleep_threshold=0`, `request_retries=0`, `connection_retries=0`,
`retry_delay=0`, `auto_reconnect=False`, `raise_last_call_error=True`,
`receive_updates=False`. Preserve the factory's optional read budget. These settings
go into the constructor, not onto a client after connect. SDK-internal server-error
backoff is not claimed eliminated; flood waits propagate and SDK retries are zero.

Validate expectation, read config, create client/handle and capture first-login
status. In a try/finally, connect, ask `_authorization_problem`, then verify self.
Catch UnauthorizedError/AuthKeyError from connect/proof as AuthRequiredError with
original cause and flags. The auth-error factory also handles absent self without
inventing a Telegram error reason. Restrict conversion to setup/proof; do not
reinterpret the operation body's exceptions. Bind `_tgdata_account_operation` to
the verified handle and yield it. Never call persistent authentication/get_client,
start, sign_in or code-request methods. No primary/pool client is set or reused.

Finally mark the handle closed and await `_disconnect_owned(client)`. Its inner
task calls and awaits disconnect exactly once, recording cleanup exceptions
(including internal CancelledError) as type-only status. Its caller awaits fresh
shields of that retained task, remembers any caller CancelledError, and keeps waiting
through repeated cancellation. On settlement, best-effort ERROR logging names only
the cleanup error type, with no exception text, repr or traceback. Re-raise captured
caller cancellation after cleanup; otherwise preserve the body's automatic return
or exception. SDK shutdown hangs have no time guarantee. Unrelated existing
ephemeral/session/close methods are unchanged.

### Output

An internal lexical context usable by subsequent tgdata stages, with configured
policy before the first authentication request and one settled close attempt.
### Safe in nature
False — shared client construction changes; optional behavior must stay isolated.
### Peripheral concepts
proxy routing, device identity, StoredSession, SDK connect/disconnect, cancellation,
authentication, diagnostic logging, persistent/pool defaults.
### Hardness Lvl
4

## Step 3 — preserve admission ownership

### Proposed changes

At the start of `BudgetClientMixin._read_budget_account`, if the client carries
`_tgdata_account_operation`, await and return its `verify_account()`. Leave the
unowned path and all reservation/cost/settlement logic unchanged. This covers page
preparation and the actual `_BudgetSender.send` admission, including real SDK retry
entry. Self RPC is metadata so it does not recursively enter read admission. Keep
the closed binding on the client to refuse retained budgeted reads after exit.

### Output

An owned message read cannot charge/send as a newly observed different account;
ordinary budget users retain current behavior.
### Safe in nature
False — shared budget provider gets a conditional branch.
### Peripheral concepts
per-account quota, sender retry loop, iterator page admission, auth errors.
### Hardness Lvl
3

## Step 4 — offline contract tests

### Proposed changes

Add `tgdata/smoke_tests/test_32_account_operation.py` (31 belongs to the unmerged
#17 branch). Follow the repository's standalone suite pattern. Block sockets; use
temporary config/session stores and synthetic account IDs/credentials only.

Use real Telethon dispatch, connect and disconnect on a scripted transport where
practicable. At least one cancellation test must run actual SDK disconnect and its
internal coroutine. Do not replace the behavior being proved with an agreeing fake.
Use real SQLite read budgets; force pending futures/events for overlapping tasks.

Cover both acceptance cases; invalid IDs; malformed/absent self; empty/revoked/banned
auth; no code/prompt even with interactive_login=True; policy observed during
connect/auth; original wait/server/transport failures; inherited session/proxy/device
settings; budget mismatch and logout before claim/send; closed/foreign task refusal;
two genuinely overlapping operations; close on connect/proof/body/success exits;
body error plus failing close; caller cancellation during work and close, including
repeat; disconnect's own cancellation; logger failure; no credential in diagnostic.
Use bounded event waits so a broken test fails instead of hanging indefinitely.

[folded: Risk 1, robust] Catch each identity-invalidating refusal inside the body,
then change the reply back to the expected account and assert handle/client and
real budget admission remain closed. Cleanup still runs once.

### Output

Reproducible offline acceptance and failure-path evidence, with no live side effects.
### Safe in nature
True — tests only, synthetic fixtures.
### Peripheral concepts
real SDK transport contract, asyncio scheduling, temporary SQLite, test runner.
### Hardness Lvl
4

## Step 5 — documentation and verification

### Proposed changes

Add a smoke-test README entry and a concise maintainer contract in
`docs/account_operations.md`: private usage, policy, identity/admission, outcome
precedence, task/lifetime obligations and Stage 2 health boundary. Avoid advertising
new public group functionality in README. Compile changed modules and parse them
with the supported Python3.7 grammar. Run new suite first, then every supported
offline module 12–19 and 22–30; 12/13 live portions stay skipped with a nonexistent
config path. Run shipped continuation/backfill examples with temporary outputs if
the existing regression workflow includes them. No old live smoke tests are run.

### Output

Clear internal contract and recorded meaningful regression results on SDK1.45.0.
### Safe in nature
True — docs/tests; no live account work.
### Peripheral concepts
package support baseline, standalone suite conventions, legacy live skips.
### Hardness Lvl
2

## Step 6 — commits and issue status

### Proposed changes

Commit product code/tests/docs separately from verification/work-folder notes.
Keep unrelated todo.md, guide edits and duncan out. Update #7 with Stage 1 branch,
scope and actual T/0–5 progress; preserve original request and prior PR16/revision3
history. Push the feature branch. Do not claim #7 complete, close it, publish a PR
or merge. Those remain later explicitly requested workflow steps.

### Output

Reviewable Stage 1 implementation and durable resume record.
### Safe in nature
True — scoped archival/workflow updates, no integration branch changes.
### Peripheral concepts
GitHub native issue branch, historical PR16, staged task status, separate devdocs.
### Hardness Lvl
1
