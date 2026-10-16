# History sampling across days

Capture bounded visible history, then select raw messages locally. This is useful
for reviewing content or supplying examples to an application classifier. It
does not estimate a statistically representative population, save reading
progress, or acknowledge delivery.

## Capture, select, retain and replay

```python
from datetime import datetime, timezone
from pathlib import Path
from tgdata import TgData, HistoryCapture

async def review(expected_account_id):
    tg = TgData("config.ini")
    try:
        capture = await tg.capture_group_history(
            "@example_group", account_id=expected_account_id,
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 2, 1, tzinfo=timezone.utc),
            max_messages=3000, max_requests=100,
        )
    finally:
        await tg.close()

    # The caller owns storage and any topic rules. No Telegram requests follow.
    Path("capture.json").write_text(capture.to_json(), encoding="utf-8")
    eligible = [r["id"] for r in capture.messages
                if r["kind"] == "message" and r["text"]]
    sample = capture.sample(size=300, eligible_ids=eligible)
    Path("sample.json").write_text(sample.to_json(), encoding="utf-8")

    restored = HistoryCapture.from_json(
        Path("capture.json").read_text(encoding="utf-8"))
    assert restored.sample(size=300, eligible_ids=eligible).to_json() == sample.to_json()
    return sample
```

Capture includes text, IDs, publication/edit dates, available sender fields,
reply/forward references, album IDs and reference-mode media metadata. It does
not download media or request sender enrichment. Text is not silently shortened.
Treat these files as your application's retained message content.

Values own canonical JSON and expose detached dictionaries/lists. Mutating a
getter's result cannot change the value. `HistoryCapture.from_json` validates the
schema, supported algorithm, exact fields, canonical dates, records, count and
coverage consistency, and content digest. Duplicate keys and nonfinite values
are rejected. Its default `max_bytes` is 64 MiB, checked before parsing; explicitly
raise it for a larger legitimate capture. Native count limits do not promise a
byte or memory ceiling, and a native capture may exceed the default reload policy.
Load failure raises `HistorySampleError`; it never creates replacement state.

## Bounds and day coverage

Both dates are required, timezone-aware, and normalized to UTC. The window is
half-open: `start_date <= publication_date < end_date`. It must fit between
1970-01-01 UTC and 2038-01-19 03:14:07 UTC, and its end must not exceed invocation
time. Each bucket is the intersection of that window with a UTC calendar day;
partial first/last days remain explicit.

`max_messages` (default 3000) and `max_requests` (default 100) are plain integers
from 1 through 10000. The first counts all raw slots in accepted pages, including
services, unavailable placeholders and rows outside the bucket used as boundary
evidence. The second counts logical `GetHistory` attempts, including a refused or
failed current attempt. It excludes authentication and identity/metadata RPCs;
it is not a network packet limit. These limits are independent of `ReadBudget`.

The capture algorithm is `utc-day-round-robin/v1`:

1. Visit unresolved days chronologically in rounds. If remaining slots or calls
   cannot cover a round, choose evenly spaced days (one opportunity chooses the
   middle day, rounding down).
2. Give each chosen day one page, at most 100 slots. Divide remaining slots fairly
   among the visits left in that round. On a day's first visit, request just one
   slot when spare calls remain for a depth pass. This avoids spending large
   pages merely proving empty days empty.
3. Start each day immediately before its end, rounded upward to a wire second;
   filter exact boundaries locally. Continue by exclusive descending message ID.
   Validate a whole page before accepting any of it.
4. A dated row before the bucket's start, an empty response, or the SDK's complete
   `Messages` response ends that bucket. A short slice alone does not prove end.
   Continue unfinished days until all have end evidence or a limit is reached.

Every day remains in `capture.buckets`, including unvisited days. Its fields are
`start_date`, `end_date`, `requests`, `pages`, `scanned_messages`,
`unavailable_messages`, `end_reason` and chronological `records`. Requests count
attempts; pages and slots count only fully accepted responses. Invalid or failed
pages add no records, although the underlying allowance may have charged work.

`capture.coverage` gives aggregate counts, limits, collection timestamps,
`stop_reason`, and `coverage_complete`. Normal stops are `finished`,
`message_limit` or `request_limit` (message limit takes precedence if both stop an
unfinished capture). Finished means every bucket has end evidence; unknown slots
can still make coverage incomplete. A bucket is complete only with end evidence
and no unknown slots. An error elsewhere does not erase an earlier day's evidence.

Even complete coverage describes messages visible to this account during this
observation. It does not recover deleted/inaccessible messages or create an atomic
snapshot. Capped busy days contain a descending captured prefix, and selection
cannot recover uncaptured rows. Inspect coverage before drawing conclusions.

## Deterministic selection

`capture.sample(size=300, eligible_ids=None)` performs no I/O and returns a
`HistorySample`. `size` is a plain integer 0..10000. `eligible_ids` is `None` (all
ordinary captured messages) or a list, tuple, set or frozenset with at most 10000
input occurrences. IDs are plain positive int32 integers or canonical decimal
strings. Order and duplicates are normalized; empty means select nothing.
Unknown or service IDs are errors. Generators and predicate callbacks are not
accepted. Evaluate topic rules on retained content and supply their resulting IDs;
a caller's predicate failure cannot alter the capture or source health.

Selection uses `utc-day-even-rank/v1` with no random seed:

- Sort each day's eligible messages by date, then numeric message ID.
- Allocate equal day quotas up to each day's capacity, redistributing spare
  capacity from sparse days. Allocate residual single slots to evenly spaced
  remaining days. Zero and full selection terminate directly.
- For `k` of `n` messages, choose no ranks if `k=0`, rank `floor((n-1)/2)` if `k=1`,
  otherwise ranks `floor(j*(n-1)/(k-1))` for `j=0..k-1`. The same rank rule selects
  residual days. Return messages chronologically.

For 599 eligible captured messages on one day and size 300, this includes the
first and last, rather than keeping only the newest 300. Days with more messages
do not automatically receive a proportionately larger quota. This is descriptive
sampling with an explicit bias, not random or statistically representative sampling.

Identical retained capture and normalized policy produce identical JSON and
`sample_id`. A new Telegram query may see different content, visibility or
observation times, so it has no replay guarantee. `capture_id` identifies retained
input, including observation times and source evidence. Digests detect content
changes; they do not authenticate Telegram provenance.

The sample contains selected raw records, policy, capture/account/group identity,
window, source summary and day metadata. Each day reports ordinary/service counts,
eligible/selected counts, eligibility exclusions and intentionally omitted eligible
messages separately from incomplete source coverage. Unselected message bodies
are not duplicated in the sample. Save its JSON as output; replay uses the capture
and policy, so no separate sample loader is provided.

## Services, albums and photo trails

The sampling unit is explicitly `raw_message`. Services remain in the capture but
are excluded from selection. Album members may be selected separately. For each
selected album, metadata reports `grouped_id`, all captured ordinary member IDs,
selected IDs and omitted captured IDs. Membership is `unconfirmed`: even selecting
all observed members cannot prove no other member exists outside captured data.
No photo-trail inference runs on sparse selected input. This API neither changes
the existing album/trail helpers nor promises their batch envelopes.

Neither capture nor sample is a `MessageBatch` or a delivery receipt. Selected IDs,
including the largest ID, must never advance daily continuation/backfill cursors or
acknowledge skipped messages. No progress storage, leases, joins or scheduler are
introduced here.

## Account ownership, errors and liveness

The operation uses one temporary client under a freshly verified expected numeric
account ID, with existing proxy/device/session settings. It never prompts for a
login code or joins a group. Existing admission checks, read allowances and cleanup
remain in effect. A different actual identity refuses before group work; a later
identity change refuses subsequent requests.

Source allowance reserves each requested page's slots before dispatch and settles
under the existing policy. A one-slot day probe does not grant more allowance, and
a later larger request may refuse even if a smaller request could have fit. There
are no added retries or flood-wait policies. Success does not clear a previously
recorded history-access restriction. Local validation/storage failures do not
become Telegram health events.

After valid metadata resolution, failures and cancellation preserve their original
type and attach accepted pages as `error.partial_result` when possible. Its stop
is `error` or `cancelled`, and global coverage is false. Errors before valid metadata
have no capture. Annotation is best effort, not a durable receipt; repeated
cancellation during cleanup can prevent delivery of that metadata. Cleanup retains
the existing result/error precedence and waits for disconnect. No exception is
converted into a successful sample.

Optional synchronous `heartbeat(phase)` receives existing request progress and
`history page done` after each accepted page. Callback failures are isolated. An
unanswered request emits no fake timer beats, so a caller can detect a stall and
cancel it.

Offline tests use Telethon 1.45.0's actual dispatch/TL decoding, verified-account
lifecycle, StoredSession and SQLite allowance with synthetic replies. They do not
qualify live Telegram visibility or pagination behavior for a particular group.
