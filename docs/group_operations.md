# Group lookup and access checks

These two async methods make short-lived, read-only observations under an explicitly
expected Telegram account. Authenticate separately first. They never request a login
code, join a group, select `current_group` or use the persistent client/pool.

```python
from tgdata import TgData

async def inspect_group(config_path, expected_account_id):
    async with TgData(config_path, interactive_login=False) as tg:
        details = await tg.lookup_group("@example_group", account_id=expected_account_id)
        print(details.group.title, details.member)

        access = await tg.check_group_access("@example_group", account_id=expected_account_id)
        print(access.status, access.reason)
        return access.to_dict()
```

Use `check_group_access` alone when you need both metadata and access: it includes the
completed lookup in `access.lookup`, avoiding the example's two independent lookups.
`account_id` is required and must be a positive Python integer, excluding booleans.
It is the expected Telegram account ID, independent of the session filename. A fresh
self request must confirm it before any group request. Expected B/cached A/actual B
proceeds as B; expected A/actual B raises `AccountIdentityError` before group work.

## References

| Input | Resolution |
|---|---|
| `example_group`, `@example_group` | Fresh username resolution; no generic SDK string aliases |
| `https://t.me/example_group`, `telegram.me/example_group/` | Same username route; HTTP/HTTPS and optional `www` accepted |
| `t.me/+case_sensitive_token`, `t.me/joinchat/case_sensitive_token` | Invite inspection only; never import/join |
| Marked basic-group ID, e.g. `-123` | Direct basic-group lookup without a cache row |
| Marked channel ID, e.g. `-1000000000123` | Requires that exact session's cached access hash |
| Bare positive ID, e.g. `123` | Requires exactly one basic-group/channel namespace in this session cache |

Numeric strings follow numeric rules. Outer whitespace is removed. Numeric inputs
must be nonzero signed64 integers; booleans, floats and raw SDK objects are rejected.
Typed IDs must survive the SDK's marked-ID round trip: a large number cannot borrow a
row from another peer namespace. No dialog enumeration, user-row fallback or access-hash
guess is performed. Zero is a valid *observed access hash*, not a substitute for one.
A username or invite is usually more convenient than an uncached numeric channel ID.

Username candidates contain 1–32 ASCII letters, digits or underscores, starting with
a letter; the server decides existence/validity. `me` and `self` are literal username
candidates, not the SDK's self aliases, and a resolved user is rejected. Invite tokens
contain 1–256 ASCII letters, digits, underscores or hyphens. One trailing URL slash is
allowed. Credentials, ports, queries, fragments, message links/deeper paths, other
hosts/schemes and empty invite tokens are unsupported. `/joinchat` is reserved for the
invite route and requires a token.

## Returned observations

The exported `GroupMetadata`, `GroupLookup` and `GroupAccess` are frozen dataclasses.
They contain no client, SDK entity or transport access hash. `to_dict()` creates fresh
plain dictionaries; timestamps become UTC ISO8601 text and IDs remain Python integers.

`GroupMetadata` contains `id`, canonical marked `peer_id`, `title`, optional `username`,
`kind` (`group`, `megagroup`, `channel`, `community` or `unknown`) and optional
`participants_count`. Counts describe what the source supplied, not an exhaustive count.

`GroupLookup` contains the verified `account_id`, normalized `target`, `group`, nullable
`member`, `request_needed`, `requires_payment` and `preview_expires_at`. Unknown facts
are `None`. In particular:

- A plain invite preview has no group IDs/username or usable input peer. It says the
  account is not a member and supplies its request/pricing flags.
- An already-member invite establishes membership; a peek invite establishes temporary
  preview access without membership and retains its expiry when supplied.
- Full ordinary groups use their membership flags. Forbidden/minimal entities leave
  membership unknown unless the invite wrapper establishes it. A minimal entity or a
  channel-family entity without an access hash cannot support this history probe.
- Payment requirements remain unknown outside an invite form containing pricing
  evidence. Missing ordinary metadata is not evidence that joining is free.

`GroupAccess` contains the owner/target, `status`, optional complete `lookup`, and optional
`reason`. Its `group` and `member` properties derive from that lookup. `readable` is a
three-valued convenience property, also included in `to_dict()`:

| Status | `readable` | Meaning |
|---|---|---|
| `readable` | `True` | One valid uncached history reply was received for this group, even if empty |
| `denied` | `False` | Telegram returned a classified group-access refusal; `reason` is its error name |
| `unprobed` | `None` | Lookup succeeded without a usable input peer; `reason` is `NO_PEER` |

A denied result retains lookup details only if resolution completed before the refusal.
It does not invent metadata from a failed resolution. Readability describes an observation
at that instant. It is not membership, permission to join, complete historical visibility,
or a guarantee of future access. No message content is returned.

## Requests, budgets and errors

Each call uses one verified temporary client with the configured proxy, device and
session store. Group resolution uses one explicit source request once local numeric
requirements are met. Access checking adds one logical `GetHistory(limit=1, hash=0)`
request if a peer is available. Authentication and budget identity checks are separate
requests; “one probe” does not mean one total network request.

Metadata costs no message allowance. The optional existing `ReadBudget` reserves one
message before sending history and re-verifies the same account. A valid empty reply
refunds that reservation; failure/cancellation keeps the charge. Exhausted allowance
raises before history is sent. A budgeted malformed/oversized response may raise the
existing budget error before domain validation. No separate quota is introduced.

`lookup_group` raises original Telegram errors, including access refusals.
`check_group_access` converts only classified group-access RPC refusals into `denied`.
Authentication/identity loss, flood waits, server and network failures, budget refusal,
and local cache/storage errors still raise. Do not treat any arbitrary exception as
“the account cannot access this group.”

`GroupReferenceError` identifies unsupported/ambiguous/non-group references, absent
numeric cache requirements, or unavailable/migrated basic groups. There is no implicit
migration redirect. `GroupResponseError` identifies replies that cannot support a
consistent observation, including mismatched peers, malformed vectors or a cache-only
history response. Neither creates a Telegram health failure. Source errors raised
before projection keep their original type/object instead of becoming reference errors.

Telethon **1.45.0** is the tested SDK; installation metadata requires `>=1.45,<2.0`.
Its ordinary entity-cache behavior still applies. A known 1.45 edge is a
`CommunityForbidden` without an access hash: the file session raises SQLite
`IntegrityError` before returning the reply, whereas the store-backed session can
produce an unprobed observation. This API preserves the source error. It does not
repair SDK caches or promise that every backend can return every metadata form.

## Health, labels and cleanup

`get_account_health(account_id)` observes this instance's verified-account ledger.
Actual source RPC failures remain recorded even when access checking converts a group
refusal into a result. Only a completely validated readable result confirms group
recovery. Metadata, unprobed results, malformed replies and interrupted reads cannot
clear group denial. An older overlapping operation cannot clear a newer condition.

Correlation uses the caller's normalized reference: lowercase username, numeric ID, or
`invite:` plus the full SHA256 of the case-sensitive invite token. These labels keep raw
invite tokens out of result and health target fields. Different handles/IDs/invites are
not merged into a shared alias registry. Original SDK exceptions retain their normal
request attributes; this is not a promise to sanitize arbitrary SDK debug output or
tracebacks. Protect session storage and exception logging appropriately.

The operation waits for one SDK disconnect attempt to settle. Cleanup failure preserves
the primary result/error; caller cancellation remains cancellation. Cancellation during
cleanup after a completed valid read does not undo the already-observed health evidence.
Notifications run separately after cleanup settles and may arrive after the API returns.
There is no shutdown timeout or notification ordering guarantee. Existing persistent
reads and legacy `health_check()` retain their separate behavior.

See [the internal lifetime/health contract](account_operations.md) for detailed guarantees.
Run `python -m tgdata.smoke_tests.test_34_group_access` for the offline public contract
suite. It uses actual SDK dispatch/TL decoding/error construction, session backends and
SQLite budgets with synthetic source replies and blocked sockets. It does not qualify
live Telegram permissions. Joining and join limits are later work.
