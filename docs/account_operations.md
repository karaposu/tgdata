# Internal account operations

`ConnectionEngine._account_operation(expected_account_id)` is the private
foundation for account-owned, short-lived tgdata operations. Public consumers use
[`lookup_group` and `check_group_access`](group_operations.md); joining is later work.
The facade's owned-health composition is described below.

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

## Owned health composition (Stage 2)

Group operations use the private facade boundary:

```python
async with tg._account_health_operation(account_id, "operation_name", group) as (op, observation):
    result = await op.client(request)
    # Only if this actual result establishes access to the named group:
    observation.confirm_group_access()
```

The source handle, policies and cleanup rules above still apply. Keep those
policies unchanged and all SDK work in the opening task. The observation is fixed
to that handle's verified account and client. Self proof is account evidence only.
`confirm_group_access()` is a trusted internal semantic assertion, not an SDK
permission classifier: never call it merely because a self or metadata query
succeeded. It checks active lifetime/task and post-proof source evidence; the
concrete operation must check the result's access meaning.

The local public `get_account_health(account_id)` returns this owned ledger or
None when unobserved. Legacy public reads and `health_check()` remain separate.
Raw RPC failures, including SDK MultiError leaves, record immediately even if
caught. Partial batch successes provide no recovery evidence. Local exception
causes and ambient reports do not create owned facts. A caught invalidated handle
cannot recover state; an older operation cannot clear a newer condition.

Owned event `request` and snapshot `waiting` keys use the logical SDK request's
namespace and class, such as `messages.GetHistoryRequest`. Known transport envelopes
are unwrapped; `messages.GetMessagesRequest` and `channels.GetMessagesRequest` stay
distinct. Legacy health names are unchanged. Missing or malformed request identity
provides no evidence for automatic recovery.

A wait needs a successful answer for its request key. A restriction remembers
the refused key and needs that request to succeed in a later operation with the
same outer method. A successful identity check cannot clear a history-read
restriction. Initial account proof occurs before observation and adds no request
success; fresh proof still provides the existing logged-out/banned recovery evidence.
All recovery retains the owner, valid-handle, operation-start and no-self-recovery
guards. Group access still needs the semantic assertion described above.

The factory captures immutable request keys before awaiting the SDK and binds them
to the current observation and client. Changing a caller's batch container while
awaiting cannot invent a different successful request. Internal callers must keep
individual TLRequest objects and their envelope chains unchanged during the call;
the hook does not clone requests. It recognizes scalar requests and concrete
built-in list/tuple/set/dict batches. Unsupported lazy/custom inputs are not consumed
for health evidence and supply no recovery evidence.

Failures escaping isolated setup or work carry private attribution-neutral metadata
on the original exception, its explicit causes and SDK MultiError RPC members.
Forwarding one through another task, wrapping it, or rethrowing an explicit cause
does not assign it to an enclosing legacy account. Arbitrary implicit context is
not adopted as part of that source. A fresh RPC error encountered before a neutral
ancestor still emits its own legacy observation. This controls emission only:
diagnostic classification and polling decisions retain the original verdict.

Notifications receive plain data in separate tasks after the disconnect attempt
settles. They may run after the primary outcome reaches the caller, and unequal
cleanup durations can reorder their arrival. Event times and the local snapshot
describe the observations; there is no FIFO delivery promise. Close after ongoing
operations finish to cooperatively retire pending notifications; this is not a
durable delivery or concurrent-producer shutdown contract.

Run `python -m tgdata.smoke_tests.test_33_owned_health` for the offline composition
regressions, alongside suites16 and32.
