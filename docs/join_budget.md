# Join allowance

`JoinBudget` stores a per-account rolling 24-hour allowance in local SQLite.
It counts **admitted attempts**, including attempts whose later outcome is unknown.
Pass it as `TgData(..., join_budget=budget)` to guard the public
[`join_group(target, account_id=...)` operation](group_joining.md). It does not
guard ordinary raw clients or authenticate account IDs by itself.

## Provision and reopen

```python
from tgdata import JoinBudget

# Explicit first-time setup. The parent directory must already exist.
budget = JoinBudget("allowances.sqlite3", create=True)
budget.configure(account_id=123456789, daily_limit=0)  # Paused until configured otherwise.
print(budget.status(123456789).to_dict())

# Subsequent jobs open existing state without permission to recreate it.
budget = JoinBudget("allowances.sqlite3")
```

Use your account's numeric Telegram ID. The ledger accepts a key; it does not
authenticate it. Session filenames and cached user identities are not ownership
proof. There is no recommended Telegram-safe rate in this example.

`create=True` may create a fresh file or add an entirely absent join namespace to
an existing file. It never repairs a partial or unsupported join schema. Default
reopening, and all later operations, refuse a missing file or namespace. Provision
deliberately: explicitly creating a new file after losing the old one also loses
its history. Keep the existing file and its policies between runs.

The ledger stores account IDs, limits, clock observations and attempt timestamps,
not credentials, group membership or message content. It can share a file with
`ReadBudget` using separate tables. It does not change read accounting or refunds.
SQLite URI strings, in-memory databases and automatic parent-directory creation
are not supported. No connection is retained, so no close method is needed.

## Policy and status

`configure(account_id, daily_limit)` creates or updates explicit policy and returns
the resulting `JoinBudgetStatus`. A missing policy is an error; zero blocks all
new admissions. The ID is a positive integer and the limit a nonnegative integer,
both at most 2**63-1. Booleans, fractional values and numeric strings are rejected.
Changing the limit preserves usage, including when usage exceeds the new limit.

`status(account_id)` is a local observation. It can persist clock observations and
prune expired records; it never reserves capacity. The frozen result contains:

| Field | Meaning |
|---|---|
| `account_id` | Supplied numeric account key |
| `limit` | Configured rolling-day cap |
| `used` | Unexpired admitted attempts |
| `remaining` | max(0, limit - used) |
| `observed_at` | Effective UTC epoch timestamp of this observation |
| `next_available_at` | Estimated epoch time when one slot opens if exhausted; otherwise None |
| `retry_after` | Rounded-up seconds until that slot, 0 if available, None for a zero cap |

`to_dict()` returns a fresh plain dictionary with UTC ISO timestamp strings,
`retry_after` and `window_seconds=86400`. Retry hints assume no competing claims or
policy changes. After lowering a cap, the hint waits for enough claims to expire,
not just the oldest one. A status result is never permission for a later send.

Each attempt expires exactly 24 hours after admission; there is no midnight reset.
Backward clock changes use the account's persisted last observation. Keep the
forward clock accurate: a local ledger cannot distinguish a bad forward jump from
real elapsed time. The optional `clock` callable, mainly useful in tests, must
return finite numeric UTC seconds in [0,253402214399], leaving ISO expiry headroom.

## Failures and storage boundary

- `JoinBudgetConfigError`: invalid input/clock or an unconfigured account.
- `JoinBudgetExceeded`: no capacity; carries `status`, `account_id`, `retry_after`
  and `next_available_at`.
- `JoinBudgetStorageError`: missing, incompatible or detectably invalid state,
  or a storage/cleanup failure. It grants no permission even if a commit succeeded.

All inherit `JoinBudgetError`. They are local failures, not Telegram health
verdicts. Error conversion and cleanup diagnostics omit underlying exception text;
secondary cleanup errors preserve the original failure or cancellation.

Schema is checked on each transaction. Operations validate the affected account's
stored policy and timestamps before advancing its clock or pruning records;
orphan attempt owners are refused globally. These checks detect malformed state,
not arbitrary valid-looking external edits or restoring an old database backup.

Use the same file on the same host for all cooperating callers that should share
an account's allowance. Other files and cross-host storage are outside this contract.
Calls perform synchronous local I/O and may block the event loop for SQLite's
five-second busy timeout under contention. Durability relies on SQLite and its
underlying filesystem/hardware. Offline process-exit tests are not power-loss tests.

## Internal consumption contract

`_claim(account_id)` is an internal synchronous one-unit admission operation.
The capacity check and charge share one writer transaction. Only successful return
permits its consumer to use that claim for one actual attempt. No transaction is
held over network I/O.

The public joining operation supplies freshly verified identity and claims
immediately before enqueueing, without an intervening await or caching permission.
Each new application-level SDK retry needs another claim. MTProto protocol repair
that requeues the same pending request is part of that attempt. Exhaustion, a failed commit, failed cleanup
or cancellation does not authorize a send. A committed charge can survive any of
those failures, or a crash before returning; this can waste allowance but cannot
create a free retry. No refund, settlement or reusable claim-token API exists.
Successful remote replies do not release allowance either.

An explicit account policy is required even when joining returns an observation
without a mutation. A zero cap permits those observations, but refuses a needed join.
See [joining](group_joining.md) for exact outcome and uncertainty semantics.
