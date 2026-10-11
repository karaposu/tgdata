# Joining groups

`await tg.join_group(target, *, account_id)` attempts to join through one expected
authenticated Telegram account. It uses a temporary client with the configured
session, proxy and device identity. It never requests a login code, chooses another
account, pays for entry or runs a bot interaction.

## Configure the allowance

```python
from tgdata import TgData, JoinBudget

# Provision once. Choose policy for this account; no Telegram-safe rate is implied.
budget = JoinBudget("allowances.sqlite3", create=True)
budget.configure(account_id=123456789, daily_limit=0)  # Initially paused.
# When ready, configure the cap your application has chosen.

# Subsequent jobs reopen existing state; missing state must not reset usage.
budget = JoinBudget("allowances.sqlite3")
tg = TgData("config.ini", join_budget=budget)

async def join_and_check(target, expected_account_id):
    result = await tg.join_group(target, account_id=expected_account_id)
    print(result.to_dict())
    if result.member is True:
        # Optional separate operation, subject to any configured ReadBudget.
        access = await tg.check_group_access(target, account_id=expected_account_id)
        print(access.readable)
    return result
```

The numeric `account_id` is required and independent of the session filename or
cached identity. A mismatch refuses before group work. Fresh proof immediately
before mutation admission must still identify the same account. Missing or revoked
authentication raises; `interactive_login=True` does not permit a login here.

A configured `JoinBudget` and an explicit policy for the verified account are
required, including for nonmutating outcomes. No default cap or database is created
by `join_group`. Zero or exhausted allowance permits observing an existing membership
or known payment requirement; it refuses an actual mutation. Query the ledger directly
with `budget.status(account_id)`; that snapshot never reserves a slot.

## Targets and preflight

The operation uses the same bounded [reference grammar](group_operations.md) as
lookup/access: bare or `@` handles, supported Telegram URLs, invite links, and
qualified numeric IDs. Invite tokens are case-sensitive. Numeric resolution requires
an unambiguous peer in that account's session cache; it never scans dialogs or guesses
an access hash.

A handle or numeric channel/supergroup uses the concrete peer resolved during
preflight, including its exact access hash. It does not resolve the handle a second
time for mutation. A basic group or community without a supported direct join peer
needs an invite link. Supported invites use Telegram's import operation.

Preflight already-member and known-payment observations return without sending a join.
Missing or minimal metadata does not prove membership or permission. Source resolution
errors propagate rather than becoming a join outcome.

## Results

`GroupJoin` is frozen and contains `account_id`, normalized `target`, preflight
`group: GroupMetadata`, `status`, and optional `bot_id`/`query_id`. `to_dict()` returns
fresh plain data, including derived `member`. IDs remain Python integers, including
large values; query IDs may be zero or negative. No client, raw entity, access hash,
invite token or web-view user vector is exposed in the result.

| Status | Evidence | `member` |
|---|---|---|
| `joined` | Valid Telegram join acknowledgment containing a supported Updates result | `True` |
| `already_joined` | Preflight membership, or this mutation's `USER_ALREADY_PARTICIPANT` reply | `True` |
| `requested` | This mutation's `INVITE_REQUEST_SENT`; approval is still pending | `None` |
| `payment_required` | Preflight payment requirement or this mutation's `STARS_PAYMENT_REQUIRED` | `None` |
| `interaction_required` | Valid web-view result; `bot_id` and `query_id` identify the separate interaction | `None` |

The three named RPC outcomes are mapped only when the error belongs to the exact
join/import request. A similarly named failure from identity proof, metadata lookup
or another request remains an exception. There is no automatic payment, URL request,
bot interaction, approval polling or post-join metadata fetch.

`group` describes the preflight observation. It can be incomplete or stale after
the mutation. In particular an invite preview may have `id=None` and `peer_id=None`
even when status is `joined`. Nested acknowledgment entities are not explicitly
cached to enrich it. Call `lookup_group` separately when fresh metadata is needed.

Membership is separate from reading permission. A result does not prove accessible
history or clear an earlier read denial. Use `check_group_access` for its separate
one-message read probe. Existing source request/account health recovery rules still
apply, and health records belong to the verified account, not the cached identity.

## Admission and failures

One synchronous durable claim precedes each new SDK join/import enqueue, with fresh
account proof and no intervening await. There is no refund. The production temporary
client has zero request retries and exposes FloodWait instead of automatically
sleeping. Cached waits before enqueue consume no join allowance. Each extra SDK
application retry would need another claim; MTProto repairs that requeue the same
pending request belong to its existing attempt.

Both metadata and joins leave `ReadBudget` unspent. The separate optional history
check in the example uses normal read accounting.

- `JoinBudgetConfigError`: missing/invalid ledger or account policy, invalid clock,
  or a provider that does not complete its policy/claim synchronously.
- `JoinBudgetExceeded`: no capacity; carries a status snapshot and retry hints.
- `JoinBudgetStorageError`: missing, incompatible or failed ledger state. No send
  is authorized, even when an uncertain write might already have spent allowance.
- `UnsupportedJoinRequest`: unsupported batching, wrapping or request family inside
  the bounded joining operation. It inherits `JoinBudgetError` and grants no send.
- `GroupReferenceError`: unsupported or unusable group reference/direct peer.
- `GroupResponseError`: an unusable source reply. After admission, allowance remains
  spent and the remote mutation may already have happened.

Other source failures preserve their original exception, including auth, server,
transport and wait errors. Caller cancellation remains cancellation. Failure or
cancellation after admission, including between commit and enqueue, keeps the charge;
an exception does not prove that Telegram did not join the account. SDK processing
can also fail before a decoded reply reaches the outcome helper. Retrying is a new
operation subject to fresh resolution and admission, not an exactly-once promise.

The operation waits for one SDK disconnect attempt to settle. Cleanup failures log
their type and preserve the primary outcome. Cancellation during cleanup is delivered
after that attempt settles; no shutdown deadline is promised. Health callbacks run
after cleanup and may finish after the API returns.

Invite result/health targets use `invite:` plus the full SHA256 of the token. Original
SDK exceptions still have normal request attributes, and arbitrary SDK/debug logging
is not sanitized by this contract.

## Scope and verification

The guard is active only inside `join_group` on its owned temporary client. Ordinary
raw clients, other APIs and direct SDK use are outside it. This is not automatic
account routing or an account-wide interception layer. See the [allowance contract](join_budget.md)
for same-host shared-file storage, contention, clock and durability limits.

`python -m tgdata.smoke_tests.test_36_group_join` exercises the public composition
on Telethon 1.45.0 with real dispatch, TL decoding, RPC error construction, session
backends and SQLite. Its transport replies are synthetic and sockets/login are blocked.
It verifies local behavior; it does not demonstrate live membership, Telegram policy
or that a chosen allowance prevents restrictions.
