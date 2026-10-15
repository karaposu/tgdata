# Album assembly across batches

`assemble_albums` combines Telegram-marked album members from existing
`MessageBatch` values. It returns immutable **observed posts**, with one stable ID
per album and a new revision when its observed content grows. It performs no
network, storage, scheduling or acknowledgment operations.

Telegram identifies album members with
[`grouped_id`](https://core.telegram.org/constructor/message). Each media member
can carry [its own caption](https://core.telegram.org/constructor/inputSingleMedia).
tgdata preserves all those original records. It does not infer albums from the
sender or timestamps; optional photo-trail inference is separate work.

## Use the pure operation

```python
from tgdata import TelegramPost, album_post_ids, assemble_albums

# `batch` is an existing MessageBatch. Perform these lookups in your receiver's
# transaction, against its current authoritative data.
keys = album_post_ids(batch)
previous = {key: destination.load_post(key) for key in keys}
posts = assemble_albums(batch, previous=previous)
```

`destination.load_post` above is your application function. It returns a
`TelegramPost` or `None` for an absent individual key. Storage failure must raise;
it must never be converted to `None`. A known missing database or collection is
an error, even though a missing individual post can be normal.

`previous` is required and must contain **exactly** the affected keys. Missing or
extra keys, wrong post identities and incompatible media modes are refused.
The helper cannot independently verify whether your application's lookup was
authoritative or whether someone deleted historical data outside its contract.

`album_post_ids` returns a tuple in the order keys first occur in the input.
`assemble_albums` returns a tuple of the updated affected posts, ordered by each
post's first member ID and then its post ID. An empty raw batch requires an empty
mapping and produces an empty tuple.

Each post exposes:

| Property or method | Meaning |
|---|---|
| `post_id` | Stable string identifying an album or singleton in its chat |
| `revision` | SHA-256 of this observed post's canonical content |
| `chat_id` | Canonical negative chat ID as an integer |
| `grouped_id` | Telegram grouping ID as an integer, or `None` |
| `membership` | `unconfirmed` for an album, `single` for an ungrouped message |
| `media_mode` | Original `references` or `download` mode |
| `member_ids` | Tuple of original integer message IDs, ascending |
| `members` | Independent copy of all original raw member records, ascending by ID |
| `to_dict()` / `to_json()` | Copy of the versioned document / canonical JSON text |
| `TelegramPost.from_json(text_or_bytes, ...)` | Validate and reload a saved post locally |

Caption text stays in each member's `text`, including empty/null values and
multiple nonempty captions. Sender, reply, forward, service and media fields stay
unchanged. A caption arriving in a later batch does not change `post_id`.

## Updates, replay and conflicts

Members can arrive in different batches, nonadjacent positions or reverse batch
order. Combining the same records produces identical post JSON and revision,
regardless of how they were partitioned. Raw member records remain ordered by
message ID.

When the operation is admitted under its bounds, exact duplicate records produce
the same content and revision. The function returns unchanged affected
posts too; it is a projection operation, not an event emitter. A downstream
consumer can upsert by `post_id` and compare `revision` to avoid processing an
identical observation twice. An additional member creates an update to that same
post. The API does not promise one irreversible final emission or exactly-once
external processing. This bounded computation is separate from confirming a
delivery that a durable receiver has already accepted.

A repeated member whose raw record differs raises `AlbumAssemblyError`. That
includes changed captions, sender metadata or media observations. Mixing reference
and download mode for a saved post also refuses. There is no implicit edit
reconciliation or “last value wins” policy. Retrying the original saved batch is
different from fetching overlapping history again, which may produce new records.
Use separate collections for independent observation policies when appropriate.

`AlbumAssemblyError` is a local format, conflict or resource refusal. It neither
logs message content nor reports a Telegram health event. It preserves the input
and prior post values unchanged; no subset of an operation is returned on refusal.
Application lookup/storage exceptions remain the application's responsibility.

## Membership remains unconfirmed

The raw format has a grouping ID but no expected member count or authoritative
album-complete marker. All album observations therefore carry
`membership="unconfirmed"`, including after:

- a bounded batch reaches its limit;
- the history iterator reports an end;
- a fixed historical window excludes earlier or later members;
- a budget, source failure or cancellation interrupts reading;
- the receiver commits, restarts or replays an input.

The helper does not read ahead, widen a window, spend extra allowance, or infer
completion from adjacent IDs, a timeout or Telegram's send-size limit. It groups
only supplied observed records. This is compatible with daily and historical
readers without changing their source contracts.

## Bounds for combination and post values

Both constructors/loaders and assembly accept positive plain-integer
`max_members` and `max_bytes` options. Defaults are **10,000 members** and
**16 MiB**. `album_post_ids` accepts `max_bytes`.

For assembly, `max_members` bounds the total members in all returned posts;
identical duplicate records count once in that output. `max_bytes` bounds this
sum, using UTF-8 serialized sizes:

```
input MessageBatch JSON
+ every supplied non-None prior TelegramPost JSON
+ every returned TelegramPost JSON
```

The loader's byte bound applies to its single saved input. Encoded values are
checked before decoding, and output totals are checked while accumulating.
These are serialized-work limits, not a strict process-memory guarantee. JSON
decoding and canonical encoding also allocate memory.

Limits refuse the whole operation; there is no eviction, truncation or hidden
history cache. You may deliberately raise them. Apply the same adequate policy
when loading saved posts and reopening the receiver, as well as when assembling.
A cumulative observation can exceed one raw batch's limit. Reopening with a
stricter policy can refuse otherwise valid stored data; restore an adequate
policy instead of resetting the database. These aggregate bounds govern a new
combination; they must not be reapplied as a condition for recognizing an already
committed delivery. The receiver below separates those operations.

## Durable receiver and source acknowledgment

The application owns permanent data and accepted-input recognition. The example
stores each original member record once, keyed by collection, chat and message ID,
with its post key and content digest. A current `TelegramPost` is reconstructed
from those records when requested. No second post snapshot or per-batch content
archive is stored.

For a **new input**, perform these steps in one receiver transaction or equivalent
conditional-write protocol:

1. Open and validate the intended existing collection. Provision a new collection
   only through an explicit creation operation.
2. Refuse any existing chat/message record with different content or post identity,
   then load the **current** prior post view for every affected key.
3. Run bounded assembly and persist the new immutable member records together
   with a marker that this raw batch was accepted in this particular collection.
4. Commit, then acknowledge the original source delivery outside the transaction.

For an **exact accepted input**, verify its original records against their stored
canonical content, digest and post key. Do not reassemble, load expanded post
views, write rows or return grown post content. Missing or changed accepted data
raises; the marker alone is insufficient. With intact available storage, unchanged
input limits and the same exact batch, confirmation remains valid after restart
and later album growth.

`AlbumReceiver.accept(batch)` returns **None on success**, both for a new commit
and an accepted-input confirmation. `load(post_id)` is a separate bounded read
that returns the current `TelegramPost`, or None for an absent post key.

Scope input markers by logical destination; equal batch hashes in separate
collections do not establish acceptance in each other. Load current views inside
the new-input transaction so another accepted batch cannot make the prior stale.

The repository's [SQLite receiver example](../examples/album_assembly.py) provides
this composition. It is example code to copy or adapt into your application, not
a mandatory tgdata storage backend. Its default reopening uses SQLite `mode=rw`
and validates schema/version/collection. `create=True` explicitly creates a new
file/schema or registers a new collection in an existing valid example database;
it refuses an already registered collection or a damaged/foreign schema. Parent
directories must already exist. Each operation opens and closes its connection.

The example uses **local schema version2**, with immutable member rows and an index
for post reads. It refuses version1 databases from the rejected, unmerged example
unchanged, including when create=True. There is no automatic migration or reset.
Retain any such known state and use an explicitly validated import/restore before
switching that collection. Public MessageBatch v1 and TelegramPost v1 are unchanged.

```python
from examples.album_assembly import AlbumReceiver  # repository example

# Provision once, before collecting a new destination:
receiver = AlbumReceiver("posts.sqlite3", "daily", create=True)

# On subsequent runs, reopen; never provision as a fallback on failure:
receiver = AlbumReceiver("posts.sqlite3", "daily")
batch = await tg.sync_group(chat_id, limit=200)
if batch is not None:
    receiver.accept(batch)  # records + marker committed, or prior acceptance confirmed
    await tg.acknowledge_sync(chat_id, batch.batch_id)
```

For a backfill delivery, preserve its **full original delivery reference**:

```python
turn = await tg.prepare_backfill(context)
if turn.batch is not None:
    history_receiver.accept(turn.batch)  # preselected intended destination
    await tg.acknowledge_backfill(turn.delivery)
```

The application must bind the selected receiver to the intended source collection
and backfill destination. A receiver's content marker is not a source receipt.
Neither `post_id`, `revision`, nor the largest assembled member ID is a raw
acknowledgment or continuation cursor. A post may retain members from outside the
current raw batch; source progress still advances from the original raw delivery.

If receiver commit fails, do not acknowledge. A process loss before commit rolls
back the input; after commit, reopening retains it. If the acceptance reply or
source acknowledgment is lost, replay the saved source delivery. Confirmation
checks its original immutable records, so an older retry neither replaces later
members nor pays to assemble them again. Missing or inconsistent accepted records
refuse rather than being silently reconstructed from a fragment.

The example applies three distinct resource policies:

| Operation | What is bounded |
|---|---|
| New acceptance | Original input plus the existing aggregate assembly member/byte bounds |
| Accepted-input confirmation | Original input size/count and one indexed comparison per original record; no post-wide load or size scan |
| `load(post_id)` | Current view's member count and serialized bytes, independently of receipt confirmation |

View reads and new-work prior loading check count/byte metadata before fetching
payloads. New-work loading also accounts for actual reconstructed prior JSON
incrementally. A consistent SQLite read transaction keeps view metadata and records
in the same snapshot. Invalid canonical records, digests or row identities refuse.

A later writer using a larger view/admission policy can grow the current album
beyond a smaller reader's view limit. That reader can still confirm its old input;
its separate `load` can refuse. Deliberately lowering the original input limit,
storage failure or contention can still refuse confirmation. Reading or processing
the latest post content is application work, separate from acknowledging data
already accepted durably.

The example uses short synchronous local transactions with no await/network work
under the lock. Contention raises so the caller can retry the whole acceptance
from current state. It does not provide leases, distributed source ownership or
an atomic commit spanning source and destination. External deletion/rollback of
destination history requires backup/archive recovery, not invented empty state.

## Failures, captures and media

An exception's `partial_result`, or an account pool's `PoolReadCapture`, can hold
useful completed raw records even when source publication failed. Available data
does **not** by itself prove a durable delivery is pending. The example's `collect`
helper only accepts normal confirmed daily returns and propagates exceptions and
cancellation. Use existing source status/recovery/pending replay operations to
obtain the actual delivery before acknowledging; never manufacture a receipt from
captured data. Retain captures as required by the pool's own contract.

The core supports both raw media modes and preserves blob references. Saving a
post JSON does not copy or retain downloaded bytes, refresh expiring media
references or verify a blob on disk. Keep downloaded files durably before source
acknowledgment. The SQLite example deliberately accepts reference-only batches.

## Run the offline demonstration and tests

```bash
python examples/album_assembly.py --demo
python -m tgdata.smoke_tests.test_42_album_assembly
```

The tests use Telethon1.45.0, real SDK serialization/iteration/cached-photo download,
SQLite transactions/process exits and existing daily/backfill/budget components.
Source responses are synthetic; sockets are blocked. They qualify the observed
data contract, not live Telegram completeness or a deployed receiver's durability.

## Post wire format, version1

Exact top-level fields:

| Field | Rule |
|---|---|
| `schema` | `"tgdata.telegram-post"` |
| `version` | Integer1 |
| `post_id` | `tg:<chat_id>:album:<grouped_id>` or `tg:<chat_id>:message:<message_id>` |
| `revision` | Lowercase SHA-256 of canonical JSON excluding this field |
| `chat_id` | Canonical negative signed64-bit decimal string |
| `grouped_id` | Canonical nonzero signed64-bit decimal string, or null |
| `media_mode` | `"references"` or `"download"` |
| `membership` | `"unconfirmed"` for albums, `"single"` for ungrouped messages |
| `members` | Nonempty array of exact [raw v1 records](message_batch_v1.md), strictly ascending IDs |

An ungrouped post contains exactly one member. Every album member's grouping ID
must match the envelope. Canonical JSON uses sorted keys, compact separators,
unescaped UTF-8 text and no nonfinite numbers. Unknown/missing fields, duplicate
JSON keys, invalid types/identifiers, inconsistent members or a wrong revision
raise. There are no raw batch hashes or collection names in this value: post
content identity is independent of transport partitioning and destination choice.
Raw MessageBatch v1 and existing progress-store schemas remain unchanged.
