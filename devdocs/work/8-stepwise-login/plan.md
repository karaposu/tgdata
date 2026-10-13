---
model: gpt-6-astra
effort: max
---
# #8 implementation plan — revision 2

**Critic folded:** 2026-10-14 — 1 robust mitigation (steps1/3 changed,0 added).
Full prebuild: PASS23/23, prebuild/REPORT.md; production work can begin.

## What is the task
Provide an explicit existing-account LoginFlow for independent phone, code and 2FA
password inputs. Retain actual progress privately, preserve connection policy and
return a usable #5 session without changing unattended reading behavior.

## Huge Hard Blockers
### Planning Blockers
None identified. Source, vendor docs and five actual installed-SDK boundary probes
resolve the contract questions in traverse/finding.md. Full composition remains a
mandatory behavioral qualification before production, not an assumed PASS.
### Execution Blockers
None for this offline implementation. Live code delivery/password acceptance is a
separate qualification requiring authorized setup; no production login is scheduled.

## How this implementation moves toward desired state
One new public LoginFlow owns state; native transport belongs to one invocation;
the application owns persistence. Reuse the configured factory and StoredSession
codec through an isolated memory store. A narrow auth-only SDK subclass records
native connect's authorization without the ordinary update initialization. No new
coordinator, health storage model, session backend or pool login behavior.

## High-Level Summary
| Step | Description | Output |
|---|---|---|
| 1 | State, configuration binding and invocation ownership | Private restorable flow and common factory seam |
| 2 | Explicit auth transitions and public exports | Start/code/password/check APIs and safe observations |
| 3 | Real SDK regression suite | test_41_stepwise_login.py covering complete composition |
| 4 | Caller integration docs and offline example | README/guide/example and smoke index |
| 5 | Full verification and separate commits | Qualified offline implementation and issue evidence |

## Prebuild gate — before step 1
Build an isolated candidate in this work folder, using the actual common factory
(only the planned private base-class seam), actual TL requests/serialization, native
connect/migration/disconnect, real password.compute_check and real StoredSession.
Only network replies/transport are controlled; do not replace auth helpers, state
retention, invocation ownership, SRP computation or session codec with passing stubs.
Socket attempts are blocked. Run the entire combined candidate including restart
between steps, no-2FA/2FA, actual migration, fault/cancellation and consumer loading.
Synthetic wire proves local SDK composition, not live server delivery/acceptance.
Record source hashes/results and explicit pass/fail before copying candidate into
runtime. Targeted probes from the inquiry alone do not satisfy this gate.

## Public contract fixed by this plan
`LoginFlow(config_path='config.ini', *, state=None)`; methods `start(phone)`,
`submit_code(code)`, `submit_password(password)`, `check_authorization()`, `close()`.
All are async; none prompts. Synchronous `status`, `export_state()` and `session_data`
expose safe observation, explicitly secret checkpoint, and explicitly secret final
credential respectively. Export/credential access refuse while busy or cleanup is
pending; known progress remains visible and retained while close is retried.

`LoginStatus` is a frozen safe value: step, account_id, delivery, code_length,
retry_after, action_required, cleanup_pending. Steps: phone, code, password, complete,
uncertain, restart_required, unsupported. A complete authorization with Telegram's
password-setup flag carries action_required='password_setup'; it is not silently
fulfilled. `LoginError` exposes a bounded kind and optional wait duration, not the
raw RPC object or its message. Current status remains available after exceptions.

Checkpoint version1 stores phone/hash, actual StoredSession dump, status facts,
uncertain action, absolute cooldown, effective device identity and a configuration
fingerprint (API/proxy/require-proxy/explicit identity). It excludes OTP/password and
API/proxy secrets themselves. Secret text is not encryption or tamper-proof input;
accept it only from private trusted server storage, maximum64KiB. Validate exact
schema/types/phase consistency before any network or file-session load.

One owner uses only the latest checkpoint. Local overlap raises busy; no queue or
distributed lease. Calls are bound to one event loop. Between-step restoration is
supported; killed-process mid-call replay safety is not. New code delivery requires
a fresh, deliberate flow after restart_required/unsupported; no resend API in scope.

## Step 1 — State and owned lifetime
[folded: Risk1, robust]
### Proposed changes
Add `tgdata/login.py` with public safe values/errors and private codec/memory sink.
Use the actual StoredSession for isolated state, never the configured session row.
Load config through ConnectionEngine; redact config failures outside their exception
handler. Suppress the new auth engine's route/device diagnostic payloads; use a private
disabled SDK logger so raw native errors cannot leak secrets through normal handlers.
Add only `_client_base=None` as a private keyword to `_new_client`, with unchanged
TelegramClient default. Its existing proxy/device/mixin construction remains shared.
Freeze actual constructor device values at initial creation and apply those on every
later client and restoration. Reject a changed config fingerprint before connecting.

Own each invocation in a retained child task. Yield before admitting source work so
queued caller cancellation starts no action. Catch body exceptions and component
CancelledError into an outcome value; genuine caller cancellation cancels that child
once, shields/joins it through repeated cancellation and is re-raised only after
retirement. The child records phase changes synchronously at observations. Run under
health.isolate_call. Always call existing `_disconnect_owned` with its failure receipt;
on failure retain the client and block admission/export until `close()` retries it.
No task-wide caller join, detached task, timeout-as-retirement or global registry.
Copy actual session state after all exits, including native migration and cleanup.
Retain the auth subclass's actual private `_disconnect` transport completion as well
as public disconnect's flush completion; new connection resets settled handles.
Native `_switch_dc` uses the private method (corrected by the full prebuild trace).
Explicit failed-close retry resets those settled failed handles. Keep native SDK
child loggers on the same private disabled logger instance. These are the qualified
candidate's concrete call sites for the already selected ownership/privacy rules.
### Output
One validated private state owner and one authoritative configured construction path.
### Safe in nature
False — narrow shared factory signature change must preserve all existing callers.
### Peripheral concepts
ConnectionEngine, StoredSession, health context, native SDK defaults, owned disconnect.
### Hardness Lvl
5

## Step 2 — Authentication and results
### Proposed changes
Implement a private auth-only TelegramClient subclass overriding `_on_login` to
record fresh self identity and SDK self-cache without GetState/GetDifference. Native
connect can otherwise hide remote success behind update setup. Validate actual User
ID/type and, when Telegram supplies it, its phone against the requested phone. Reject
identity mismatch before an explicit auth mutation; never use filename/cached owner.
Construct before connect with receive_updates=False, request_retries=0,
connection_retries=0, retry_delay=0, auto_reconnect=False, flood_sleep_threshold=0,
raise_last_call_error=True. SDK server-error handling may still incur its native2s
delay; do not promise zero latency or a bounded cleanup time.

Use raw auth.SendCode, auth.SignIn, account.GetPassword and auth.CheckPassword with
Telethon.password.compute_check. Do not use start/send_code_request/sign_in helpers.
Start is eligible only at phone; only explicit positive phone digits accepted, never
config default. Reject empty/malformed code/password locally. Support app/SMS/voice
code delivery; other constructors return unsupported, without signup/payment/resend.
SentCodeSuccess and Authorization go through the same actual-authorization recorder.
Set uncertain + action immediately before each auth mutation. Record SentCode/required
password/Authorization before another await. Save actual key/DC in every exit path.

Known wrong code/password retains its eligible step; expired hash/AuthRestart requires
a deliberate new flow. Waits preserve the previous eligible step and persist an
absolute retry deadline; admission enforces it. Generic RPC/transport/interruption
after a mutation remains uncertain and never silently retries. On actual migration,
permit one explicit retry only for SendCode after a proven Phone/NetworkMigrate
rejection and verified changed DC; SDK's native switch handles the route. Other
redirects require explicit restart/check, rather than replay code/password with a
changed credential. More than one redirect exits honestly; no loop of requests.

`check_authorization()` sends no code: fresh self observation can complete a prior
uncertain login; a confirmed unauthenticated code/password attempt restores that
eligible step for an explicit retry, while an uncertain send without a hash becomes
restart_required. An invalidated completed key becomes restart_required. A pre-RPC
connect failure preserves the previously known phase. Local store methods are never
invoked except the internal memory sink. Final session_data is a #5-compatible dump.
Export LoginFlow, LoginStatus, LoginError through the package without changing TgData.
### Output
Deliberate no-console existing-account login usable over separate calls.
### Safe in nature
False — public exports and SDK auth integration require compatibility verification.
### Peripheral concepts
Native connect, SRP, DC migration, account ownership, headless auth policy, final session.
### Hardness Lvl
5

## Step 3 — Focused regression suite
[folded: Risk1, robust]
### Proposed changes
Add test_41_stepwise_login.py using the complete prebuild's cases against production.
Exercise native SDK client, wire serialization and disconnection, not three fake auth
methods. Include: completed-step reload; no-2FA and real SRP proof generation; incorrect
input; required password/unsupported constructors; migration with proxy unchanged;
silent store failure cannot overwrite live slot; actual final credential consumer
reload; config/device binding; prequeued/repeated cancellation during connect/request/
disconnect; known auth/challenge retained when cleanup fails; close retry and local
overlap; component interruption; uncertain check without SendCode; waits with restart;
secrets excluded from status/repr/errors/logs; malformed state local refusal; health
neutrality; unchanged test15 headless behavior. All sockets blocked in this new suite.
### Output
Executable, bounded offline evidence for both success paths and ownership boundaries.
### Safe in nature
True — additive tests; existing expectations preserved.
### Peripheral concepts
Actual Telethon1.45 and existing suites12–40; Python3.7 grammar.
### Hardness Lvl
4

## Step 4 — Integration documentation
### Proposed changes
README Authentication link and short example; a focused stepwise-login guide explains
safe status versus private checkpoint versus final credential. Show explicit
store.save(configured_name, flow.session_data), persistence failure retry without
re-login, finally-save latest settled state, caller cancellation, exclusive ownership,
unsupported/restart/uncertain action and cleanup refusal. Provide an executable
offline example using the actual API/test wire; do not add HTTP/database services or
read real secrets. Add the smoke README entry and qualification limitations.
### Output
The feature can be integrated without guessing who saves or which input is next.
### Safe in nature
True.
### Peripheral concepts
Application-owned session store and private web-server state.
### Hardness Lvl
2

## Step 5 — Verify and commit
### Proposed changes
Compile/grammar-check changed production, run focused41 and auth/factory/store/health
regressions, then the full supported27 existing offline suites12–19,22–40 plus41.
Run the new offline example, existing3 demos and package import. Legacy live suites
stay skipped with exact reasons; no credential/request values in evidence. Inspect
diff/check for unrelated changes; product code/tests/docs one commit, task work notes
another. Push linked branch and update #8's status truthfully. No PR/merge in this run.
### Output
Passing supported offline evidence and reviewable committed implementation.
### Safe in nature
True — verification/commit only; no live account mutation.
### Peripheral concepts
CONTRIBUTING checkpoints, no duncan/unrelated guide/main checkout changes.
### Hardness Lvl
3
