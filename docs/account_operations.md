# Internal account operations

`ConnectionEngine._account_operation(expected_account_id)` is the private
foundation for account-owned, short-lived tgdata operations. It is not a public
TgData group API. Group lookup, access checking, joining and health ownership are
separate work.

Internal callers use it in the task that opens the context:

```python
async with engine._account_operation(expected_account_id) as operation:
    account_id = operation.account_id
    client = operation.client
    # Implement the bounded operation here, using this verified account_id.
    # Later admission checks call await operation.verify_account().
```

The expected ID must be a positive Python integer, excluding booleans. The context
constructs a fresh client through the normal session/proxy/device factory; it does
not use or replace the persistent client or connection pool. File sessions and
pluggable session stores keep their existing behavior.

Before connecting, the client is configured with zero automatic flood sleeps,
zero request/connection retries, zero connection retry delay, no automatic
reconnection, preserved final RPC errors and disabled incoming updates. Telethon's
own server-error path can still request its final two-second backoff. The tested
SDK is **Telethon 1.45.0**.

The context connects without `start()` and verifies authentication and the actual
self response before yielding. An old cached account ID does not authorize work:
expected B, cached A, actual B succeeds as B; expected A, actual B raises
`tgdata.account_operation.AccountIdentityError` before the body runs.

Missing or revoked authentication raises `AuthRequiredError`, with the original
Telegram reason/cause when available. This path never logs in, even when the
engine was created with `interactive_login=True`; authenticate separately.
Transport failures and Telegram waits/server failures remain their original errors.

The handle's `account_id` and `client` properties cannot be reassigned. Later read
budget admission asks the handle to verify the same account before reserving quota
or sending. Identity mismatch, unavailable/malformed identity or authentication
loss permanently closes the handle. Catching that refusal cannot make it usable
again; begin a new operation after resolving the cause.

Keep all SDK work inside the opening task and context. Do not retain the raw client,
detach work, call login methods or replace its credentials/session. Handle access
and verification reject a foreign task or closed lifetime. This is an internal
usage contract, not a sandbox around every arbitrary SDK method.

Every constructed operation client gets one disconnect attempt. The handle closes
before teardown begins; the context waits for the SDK's attempt to settle, even if
the caller is cancelled again while closing. Its outcome rules are:

| Work / caller state | Cleanup state | Outcome |
|---|---|---|
| Success | Success or failure | Original successful result |
| Work failed | Success or failure | Original exception |
| Caller cancelled, including during cleanup | Success or failure | `CancelledError` after cleanup settles |

Disconnect's own cancellation counts as a cleanup failure, not caller cancellation.
Cleanup failures are logged at ERROR with their type only; their text and traceback
are omitted. Failure of that diagnostic cannot replace the work outcome.

One completed attempt does not guarantee successful closure if the SDK fails, and
there is no bounded shutdown duration if SDK disconnect hangs. Existing ordinary
client defaults and lifecycle methods are unchanged.

Run the offline contract suite with:

```bash
python -m tgdata.smoke_tests.test_32_account_operation
```

It uses actual SDK connect/dispatch/disconnect, synthetic replies, temporary
sessions and real SQLite budgets. Socket connections are forbidden. This proves
local ownership/lifecycle behavior; it does not validate a live account or fix
the existing health summary's account ownership.
