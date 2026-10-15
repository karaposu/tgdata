# Group activity and engagement

`measure_group_activity` reads a bounded portion of visible history and returns
raw observations, descriptive statistics and explicit coverage. It requires an
already authenticated account; it never logs in, joins, downloads media or changes
your saved reading position.

```python
from datetime import datetime, timedelta, timezone
from tgdata import TgData, GroupActivity

async def measure(config_path, expected_account_id, shared_read_budget):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    # Reuse your account's existing allowance; do not create/reset it for each run.
    tg = TgData(config_path, interactive_login=False, read_budget=shared_read_budget)
    try:
        result = await tg.measure_group_activity(
            "@example_group", account_id=expected_account_id,
            start_date=start, end_date=end, max_messages=3000,
            heartbeat=lambda phase: print(phase),
        )
        print(result.coverage_complete, result.stop_reason)
        print(result.statistics["message_count"])
        print(result.statistics["counters"]["views"])
        return result.to_dict()  # Save or analyze this in your application.
    finally:
        await tg.close()
```

## Inputs and source work

The expected `account_id` is a positive integer, excluding bool. The temporary
client verifies the actual login before group work. Cached account identity is
not authority. Supported references and numeric-channel access-hash requirements
match [group lookup](group_operations.md). Basic groups, supergroups and broadcast
channels need a usable peer; plain invite previews and unsupported group types
raise `GroupReferenceError` without a history request.

Both dates are required timezone-aware datetimes, normalized to UTC. The interval
is **half-open**: `start_date <= message.date < end_date`. It must satisfy
1970-01-01 UTC <= start < end <= the signed 32-bit wire-date maximum, and end must
not be later than invocation time. Local-calendar day bucketing is not provided.
Dates select publication time, not edit time or reaction time.

`max_messages` defaults to 3000 and accepts an integer from 1 through 2147483647, excluding bool.
It bounds **all returned source slots**, including service messages, unavailable
placeholders and dated rows outside the window. It is not a requested number of
ordinary posts. Each history request asks for at most 100 slots and never exceeds
the remaining cap. There is no hidden lookahead after the cap. Allocation grows
with actual returned observations, not with the configured maximum.

History is read newest first, seeking conservatively before the end and filtering
exact bounds locally. Following pages continue by message ID so equal timestamps
can span pages. Short pages can be followed by more pages. No count-only query,
full-profile request, topic traversal or retry loop is added.

With a [ReadBudget](../README.md#per-account-read-budgets) configured, the actual
source call re-verifies the owner and reserves its entire requested limit before
sending. Successful replies settle to their actual returned slot count. For
example, a first request for 100 slots is refused if only 20 remain, even when the
group might contain fewer than 20 messages. Set a smaller `max_messages` explicitly
when appropriate; the method does not resize or reset your allowance. Failed or
cancelled requests retain the existing conservative reservation. No budget is
created implicitly when TgData has none configured.

## Coverage and failures

| stop_reason | Meaning |
|---|---|
| `window_start` | A validated page contains a dated row strictly older than start |
| `history_end` | A validated empty response or nonsliced full history response supplies source-end evidence |
| `message_limit` | The source-slot cap was reached without either witness |
| `error` | Only on an exception's partial result; collection failed |
| `cancelled` | Only on a cancellation's partial result; collection was cancelled |

`coverage_complete` is true only for `window_start` or `history_end` with no
unavailable slots in accepted pages. An unavailable placeholder has an ID but no
usable date, so it cannot be assumed outside the requested window. Even if traversal
reaches the boundary, that observation remains incomplete. A reported source total
or a short sliced response never establishes completion. If the last allowed page
supplies a genuine boundary/end witness, completion is possible without another
request; filling the cap by itself is insufficient.

Completeness means **account-visible history observed during collection**. It does
not mean deleted/hidden history, every message ever written, an atomic snapshot,
or identical results for another account. Edits, deletions and visibility can
change between requests. Oldest/newest dated source rows describe observations;
they do not claim every intervening ID exists. Counter availability is independent:
complete message coverage can still have missing view/reaction counts.

Source, budget and authentication failures raise their original exceptions.
Malformed/wrong-peer/non-progressing pages raise `GroupResponseError`. Every page
is validated before any of its rows are accepted. After target resolution, errors
that allow attributes get `error.partial_result`, containing only accepted pages,
with `coverage_complete=False` and the appropriate failure reason. Errors before resolution
have no fabricated observation. Exception annotation is best effort and cannot
replace the original error.

```python
try:
    result = await tg.measure_group_activity(
        target, account_id=expected_account_id,
        start_date=start, end_date=end, max_messages=500)
except Exception as error:
    partial = getattr(error, "partial_result", None)
    if isinstance(partial, GroupActivity):
        save_observation(partial.to_dict())  # Your storage function.
    raise
```

The result's `scanned_messages` and `pages` count **validated, accepted pages**.
They are not the billing ledger: an invalid page, failed request or cancelled
request may have consumed allowance without entering the result. Use ReadBudget
for charged/reserved amounts.

## Portable result and raw observations

`GroupActivity` and `ActivityMessage` are frozen dataclasses. `messages` is an
immutable tuple in descending source order, containing only in-window dated
ordinary/service rows. `to_dict()` creates detached JSON-compatible dictionaries
and lists. Timestamps are UTC ISO8601 strings; absent values are JSON null.
Album IDs serialize as decimal strings to retain signed 64-bit precision. No
message text, contact enrichment, SDK entities, access hashes or clients are stored.

| GroupActivity field | Meaning |
|---|---|
| schema_version | 1; independent of MessageBatch v1 |
| account_id, target, group | Verified account, normalized safe reference and existing GroupMetadata |
| start_date, end_date | Exact normalized requested publication window |
| collection_started_at, collection_finished_at | Local UTC invocation and result-construction times; cleanup can finish later |
| max_messages | Configured source-slot cap |
| scanned_messages, pages | Accepted raw slots and accepted responses, including an accepted empty terminal page |
| unavailable_messages | Accepted placeholders with no usable dated observation |
| stop_reason, coverage_complete | Termination evidence and coverage qualification above |
| oldest_observed_message_date, newest_observed_message_date | Extrema of dated rows in all accepted source pages, including boundary rows outside the window; None if none |
| messages | In-window raw observations |
| statistics | Freshly derived descriptive dictionary; changing it cannot change the value |

Each `ActivityMessage` has `id`, `kind` (`message` or `service`), `date`,
`observed_at`, `sender_kind`, `sender_id`, `grouped_id`, `views`, `reactions`,
`forwards`, `replies` and `replies_are_comments`.

The sender is taken from the returned raw sender field. `user` identifies a visible
user ID; `channel` identifies a channel ID; absent or chat-level sender information
is `unknown` with no claimed sender ID. Unknown authors are never collapsed into
one person. Channel identities and user identities stay separate even if their
numeric IDs coincide. Distinct IDs do not establish distinct people or readers.

Service messages have `kind="service"` and no engagement counters. Albums are counted
as separate ordinary messages retaining the shared `grouped_id`; no album or
photo-trail assembly runs here.

For ordinary messages, views/forwards/replies are the supplied nonnegative counts,
or None if absent. `forwards` is a count, not evidence that a message itself was
forwarded. `reactions` sums the supplied reaction-type counts; a present empty list
is 0, an absent reaction object is None. This is not a unique-reactor count. The
source's reaction `min` flag concerns personal details and does not discard the
supplied aggregate counts. `replies_are_comments` preserves whether a supplied
reply count describes comments; it is None without reply metadata.

## Statistics and denominators

Every statistic refers to the **observed ordinary in-window messages**, except
the separately named service count. Service and unavailable slots do not enter
ordinary message, author or counter populations.

| Statistic | Definition |
|---|---|
| message_count | Number of observed ordinary raw messages |
| service_message_count | Number of observed in-window service rows |
| known_user_count | Distinct observed user sender IDs |
| channel_sender_count | Distinct observed channel sender IDs, not people |
| unknown_author_messages | Ordinary rows without a known user/channel sender |
| latest_observed_message_date | Latest observed ordinary publication date, or None |
| window_seconds | Exact requested interval duration |
| messages_per_24h | message_count ×86400/window_seconds when coverage is complete; None otherwise |
| daily | Every intersected UTC calendar date, with exact start/end overlap, window_seconds and the four ordinary message/author counts |
| counters | Separate distributions for views, reactions, forwards and replies |

Each counter distribution contains `known_count`, `missing_count`, `sum`, `mean`,
`median`, `min` and `max`. Only supplied values enter its denominator; zeros count.
With `[0, None, 10]`, known_count=2, missing_count=1, sum=10, mean=5 and median=5. With no known
values all five numeric aggregates areNone, not a claim of zero engagement. Exact
median averages the middle two values for an even population.

A rolling seven-day window can intersect eight UTC dates. Daily rows report each
intersection's exposure rather than inventing eight whole days. They contain
observed counts even when coverage is incomplete; a zero then is **not proof of a
quiet day**. Distinct daily user counts must not be summed into a period's unique
user count. No average daily unique-user scalar or engagement score is implied.

Counters are observed now on messages **published** in the requested period. They
are not views/reactions earned during that period. No minimum-age or cohort filter
is applied. Fresh and older publications have different time to accumulate counts;
comparison alone does not establish growth, loyalty or fraud. Retained dates and
counters allow applications to choose explicit cohorts themselves.

## Liveness, health and compatibility

The synchronous heartbeat follows [the existing contract](batch_heartbeat.md),
with actual SDK request/answer/error events and `activity page done` after each
accepted page. There is no timer beating through an unanswered request. Callback
errors are isolated; invalid asynchronous/non-callable callbacks fail before I/O.

The verified temporary client's automatic wait/retry policies remain unchanged.
Telegram waits propagate; the SDK's existing final server-error backoff can still
occur. Actual source RPC failures populate `get_account_health(account_id)`.
Local validation/transport/callback failures do not invent Telegram health events.
Measurement success does not clear an earlier group-access restriction; use the
explicit access-check operation for that recovery evidence.

Cleanup preserves the original result or failure. Caller cancellation remains
cancellation and waits for disconnect, including repeated cancellation during
cleanup. Partial-result attachment during a source cancellation is best effort;
later cleanup cancellation can supersede the exception carrying it. There is no
durable delivery guarantee or automatic retry/resume token.

`get_statistics(df)` still summarizes supplied application rows. MessageBatch v1,
album/trail assembly, daily continuation, backfill cursors/acknowledgments and pool
reads keep their existing contracts. This call creates no store and changes no
persistent selection. Rich group descriptions/counts remain in
[get_group_profile](group_profiles.md).

## Qualification

`python -m tgdata.smoke_tests.test_46_group_activity` exercises the public operation
using real Telethon 1.45.0 dispatch/TL decoding and SQLite allowances, with sockets
and login forbidden. Synthetic source replies test local behavior; they do not
qualify live Telegram visibility. Live comparisons require a separately qualified
exclusive session and authoritative allowance.
