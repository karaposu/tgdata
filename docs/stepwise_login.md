# Step-by-step login

`LoginFlow` authenticates an existing Telegram account using inputs supplied by
your application. It never reads stdin, requests a password from a terminal,
creates an account or changes the login rules of ordinary `TgData` readers.

## Configure the account route

Use the same configuration as the eventual reader:

```ini
[Telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
session_file = account-primary
# Optional; every login connection and data-centre change uses this proxy.
proxy = socks5://user:password@proxy.example:1080
require_proxy = true
device_model = My account service
system_version = 1
app_version = 1
lang_code = en
system_lang_code = en
```

The phone is an explicit argument, independent of any `phone` value in this file.
The API uses an isolated in-memory session; it does not open `account-primary.session`
or load a live credential from your session store. Configuration failures raise a
redacted `LoginError(kind="invalid_configuration")` before connecting.

## Supply each input deliberately

These snippets belong inside your application's async handlers. Input variables
come from your own UI; the library supplies no HTTP server or console prompt.

```python
from tgdata import LoginFlow, LoginError

flow = LoginFlow("config.ini")
status = await flow.start(phone)       # For example, a full +country-code number.
# Return status to your UI; keep flow itself private on the server.

status = await flow.submit_code(code)
if status.step == "password":
    status = await flow.submit_password(password)
```

Every input call returns `LoginStatus` on an observed response, or raises
`LoginError` for an error. `flow.status` always exposes the retained observation.
Check the step after **each** call; not every account follows the common path.

| `status.step` | Meaning and next action |
|---|---|
| `phone` | A deliberate `start(phone)` is eligible, subject to any wait. |
| `code` | Call `submit_code(code)` with the numeric code. |
| `password` | Call `submit_password(password)` for this account's 2FA password. |
| `complete` | Authorization was observed; save the finished session explicitly. |
| `uncertain` | A request may have acted without a usable reply. Check authorization before deciding whether to submit an input again. |
| `restart_required` | This flow cannot continue. A new flow and code request require a deliberate application/user action. |
| `unsupported` | Telegram needs interaction outside this API, or the observed identity disagrees. Inspect `action_required`; do not retry automatically. |

Status contains only step, numeric `account_id` when authorized, delivery kind,
code length, remaining `retry_after` seconds, `action_required` and
`cleanup_pending`. It contains no phone, password, code, hash or session key.
Supported delivery kinds are app, SMS and voice call. Other delivery types,
signup and payment are explicit unsupported responses; no fallback performs them.
If authorization also requires password setup, status is `complete` with
`action_required="password_setup"`. The credential exists, but this API does not
perform that additional step or promise its continued validity.

## Retain progress between requests

Keeping the object in memory is sufficient for one process. To hand a settled flow
to another worker, save its opaque private checkpoint:

```python
private_state = flow.export_state()
# Your application saves private_state in trusted server storage.

flow = LoginFlow("config.ini", state=private_state)
status = await flow.submit_code(code)  # When the restored status says "code".
```

Both the checkpoint and `session_data` contain credentials. Store them as secret
text, never send them to the browser, log them, parse them as application data or
accept an arbitrary browser-supplied checkpoint. Encoding is not encryption.
Protection, expiry and deletion of these values belong to the application.
The checkpoint excludes the code and password inputs themselves.

Restoration checks the API, proxy, proxy requirement and explicitly configured
device settings. Effective device defaults are frozen in the checkpoint so another
worker uses the same values. A changed binding or malformed/unsupported state raises
`invalid_state`. Changing the config file does not mutate an already-created flow;
construct it again when loading a checkpoint. Pin device settings for subsequent
ordinary reader clients too.

Serialize access to each flow and store only its latest checkpoint. Local overlapping
calls are refused with `busy`; exported copies have no distributed lock or version
claim. Each instance belongs to the event loop that first uses it. Restoration
between settled calls is supported. If a process is killed during a request, its
last saved checkpoint cannot tell you whether Telegram acted or whether the
transport key changed; do not transparently replay the interrupted input.

## Publish the finished session

Use the existing [session-store contract](../README.md#keeping-sessions-out-of-files).
The store below is supplied by your application, not by the login flow:

```python
from tgdata import TgData

if flow.status.step == "complete" and not flow.status.cleanup_pending:
    credential = flow.session_data
    store.save("account-primary", credential)  # Exact configured session_file key.
    tg = TgData("config.ini", session_store=store, interactive_login=False)
    # Use tg normally, then await tg.close().
```

The credential is the opaque `StoredSession` format, not Telethon's `StringSession`.
It includes the actual authorization key, data centre and own-account rows.
A returned credential is not a storage commit receipt. If your explicit save fails,
retain the flow/credential and retry that **save**; do not request another login code.
Choose the intended account slot yourself and coordinate any old readers before
replacing its credential. Successful login does not promise future authorization,
group access or available read budget.

## Handle errors, interruption and cleanup

`LoginError.kind` is safe to display or log. The original SDK/configuration error
text is not exposed. Native login-client diagnostics are suppressed because they
can include request or credential details; ordinary reader logging is unchanged.

| Error kind | Handling |
|---|---|
| `invalid_phone`, `invalid_code`, `invalid_password` | Correct the input; inspect status for the eligible step. |
| `wait` | Respect `retry_after`; the deadline is retained in the checkpoint. Creating new flows is not a way to bypass Telegram's limits. |
| `wrong_step`, `busy`, `wrong_event_loop` | Correct the application call order/ownership. |
| `transport_error`, `telegram_error`, `interrupted`, `operation_failed` | Inspect retained status. If uncertain, check authorization rather than repeating the input. |
| `restart_required`, `identity_mismatch`, `invalid_response` | Do not retry automatically; inspect status and resolve the account/flow problem. |
| `cleanup_required` | Retain this object and retry `await flow.close()`; new steps and secret export remain blocked. |
| `invalid_configuration`, `invalid_state`, `no_credential`, `not_complete` | Correct local configuration/state or use the operation at its permitted phase. |

```python
try:
    status = await flow.submit_code(code)
except LoginError as error:
    status = flow.status
    safe_error_kind = error.kind
    # Apply the table above; never log the private state or input.
```

`await flow.check_authorization()` never sends a code. It checks the retained key
against Telegram: a completed but unobserved login can become `complete`; an
unauthorized uncertain code/password attempt can return to that input step for a
deliberate retry. An uncertain code request with no retained hash requires restart.
A state with no key cannot be checked. This method does not recover a lost key or
make stale checkpoint copies safe.

Caller cancellation remains `asyncio.CancelledError`. A cancelled waiter does not
mean the remote request was rolled back. The call waits for its owned cleanup;
after catching cancellation, inspect the same flow and persist the latest settled
checkpoint under your application's own cancellation-safe storage policy. If cleanup
failed, retain the object for `close()` first. Do not let a secondary persistence
error replace the original cancellation or operation error.

Every step retires its temporary connection before returning. Known progress survives
cleanup failure, but `cleanup_pending=True` prevents a new step or secret export until
`close()` succeeds. `close()` neither logs out nor discards known progress. It may be
cancelled repeatedly while still waiting for the owned native close; no bounded close
timeout is promised. No socket is held while waiting for the next human input.

There is no implicit resend or broad auth retry. A proven SendCode data-centre redirect
can be followed once through the same proxy; other failures remain explicit. Native
SDK server-error handling can still take its own two-second delay at zero retries.

## Qualification

The full offline suite uses Telethon **1.45.0**, actual SRP, native client lifecycle,
the real session codec and controlled network replies. It blocks sockets and inputs.
This does **not** qualify live code delivery or real-account password acceptance.
No production account was logged in by these tests. Python3.11 execution and Python3.7
grammar were checked; native Python3.7 execution was not.

```bash
python -m tgdata.smoke_tests.test_41_stepwise_login
python examples/stepwise_login.py --demo
```
