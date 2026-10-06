# Message batch wire format, version 1

`await tg.get_message_batch(group_id, *, after_id=0, limit=200,
download_media_to=None, start_date=None, end_date=None)` returns an immutable `tgdata.MessageBatch`. It reads
visible group/channel messages oldest first, strictly after `after_id`. This
additive API produces a portable snapshot for storage and delivery. Existing
DataFrame, CSV, JSON export and media-by-ID methods keep their contracts.

Optional timezone-aware `start_date` and `end_date` constrain message dates to
`start_date <= date < end_date`, intersecting the ID cursor. Supply both or neither.
See [Fixed historical windows](fixed_windows.md) for accepted inputs and efficient
initial positioning. The query dates are not fields in the batch v1 wire format.

The implementation and offline suite target **Telethon 1.45.0**. The wire
version is independent of the tgdata package version.

## Reading and saving

```python
import asyncio
from tgdata import TgData, MessageBatch

async def prepare():
    tg = TgData("config.ini")
    try:
        batch = await tg.get_message_batch(
            "@channelname", after_id=100, limit=200,
            download_media_to="out/media",   # omit for references only
        )
        manifest = batch.save("out/batches")
        replay = MessageBatch.from_json(manifest.read_bytes())
        assert replay.batch_id == batch.batch_id
        print(manifest, batch.next_after_id, batch.stop_reason)
    finally:
        await tg.close()

asyncio.run(prepare())
```

`group_id` is required: a numeric ID, username or supported Telegram group
link. It must resolve to a group/channel. There is no `current_group` fallback,
and this call does not change `current_group`. `after_id` is an integer in
`0..2147483647`; `limit` is an integer in `1..10000`. Booleans and fractional
values are rejected. A missing/empty media path is not a download destination.

The existing connection, proxy, session, health reporting and optional
`ReadBudget` apply, including implicit message re-fetches during media download.
There is no second client or batch-specific retry loop. Repeated network reads
still consume the configured allowance.

`to_json()` returns canonical JSON text. `to_dict()` and `messages` return
independent copies; changing them does not change the batch. `chat_id`,
`after_id` and `next_after_id` properties return Python integers, while all
identifier fields inside JSON/dictionaries are strings. The other properties
are `batch_id`, `media_mode` and `stop_reason`.

## Exact envelope

Every listed key is required. There are no additional keys in v1.

| Key | Type and meaning |
|---|---|
| `schema` | Literal string `"tgdata.message-batch"`. |
| `version` | Integer `1`; boolean/float equivalents are invalid. |
| `batch_id` | Lowercase, 64-character hexadecimal SHA-256, computed below. |
| `chat_id` | Canonical negative decimal string for the resolved, marked Telegram peer ID, within signed 64-bit range. A basic group uses `-id`; a channel/supergroup uses `-(1000000000000 + id)`. |
| `after_id` | Exclusive input cursor as a decimal string in `0..2147483647`. |
| `next_after_id` | Last completely prepared message ID, or `after_id` when empty, using the same string range. |
| `media_mode` | `"references"` or `"download"`. |
| `stop_reason` | `"limit"`, `"end"` or `"interrupted"`. |
| `messages` | Array of at most 10,000 records, in strictly increasing ID order, all greater than `after_id`. |

Canonical decimal strings have no leading `+`, leading zeros or negative zero.
Signed 64-bit means `-9223372036854775808..9223372036854775807`. Identifier
strings preserve large values in systems whose default JSON numbers lose
integer precision.

- `limit`: exactly the requested number of records completed. It does not
  assert that another message exists; no extra history request is made to find
  out. A batch with this reason cannot be empty.
- `end`: the SDK iterator ended or the explicit date window's end was reached
  before the requested count. This describes
  the account's current visible history, not completeness of Telegram's archive.
  The maximum representable input cursor also returns an empty `end` batch
  without making a history request.
- `interrupted`: an exception stopped preparation. Only the complete prefix
  is included, and the exception is still raised.

An album can cross a batch boundary. IDs need not be consecutive. Deleted or
inaccessible messages and SDK-filtered empty placeholders are not fabricated
into records. This API does not discover later edits/deletions to IDs already
passed by the caller's cursor.

## Exact message record

| Key | Type and meaning |
|---|---|
| `id` | Positive canonical decimal string in `1..2147483647`. |
| `kind` | `"message"` or `"service"`. |
| `date`, `edit_date` | UTC timestamp string with exactly six fractional digits and `Z`, for example `"2023-11-14T22:13:20.000000Z"`; null when unavailable. SDK naive datetimes are treated as UTC. |
| `text` | Full message text/caption as a string, or null. Empty text remains an empty string. |
| `sender` | Object with exactly `id`, `name`, `username`. `id` is a nonzero signed 64-bit decimal string or null; name/username are strings or null. The username is copied without adding `@`. |
| `post_author` | Signature string or null. |
| `reply_to_id` | Positive message-ID string or null. |
| `forward_from_id` | Marked original peer ID as a nonzero signed 64-bit decimal string, or null when unavailable. |
| `grouped_id` | Album grouping ID as a nonzero signed 64-bit decimal string or null. This does not promise a complete album. |
| `service_action` | Nonempty SDK action type name for a service record, otherwise null. Treat the name as opaque; action-specific fields are not included. |
| `media` | Null, or the object specified below. |

Sender ID comes from the message's explicit author peer. Names/usernames come
only from matching sender metadata already available to the SDK. No sender
lookup is added. A senderless message remains a record with null sender fields;
an SDK-inferred self ID is not a substitute for an absent author peer. Cached
names can change between observations.

V1 is a specified projection of raw messages, not an SDK object dump. It omits
formatting entities, buttons, complete forward headers, full service-action data,
account/session credentials, access hashes and expiring file-reference tokens.
Null means unavailable or inapplicable; it is not replaced with a display label.
All strings must be valid UTF-8; no Unicode normalization is performed.

## Exact media and blob records

Media has exactly these keys:

| Key | Type and meaning |
|---|---|
| `kind` | One of `photo`, `video`, `video_note`, `gif`, `audio`, `voice`, `document`, `sticker`, `webpage`, `contact`, `geo`, `poll`, `other`. |
| `id` | Asset ID as a nonzero signed 64-bit decimal string, or null. |
| `mime_type` | SDK-supplied MIME string or null. Photo MIME is not invented. |
| `file_name` | Original filename metadata or null. It is never used as a filesystem path. |
| `size` | Known source byte size as an integer in `0..9223372036854775807`, or null. Readers must preserve its integer precision. |
| `downloadable` | Boolean: this observation has a supported full Photo or Document attachment. Empty assets and other attachment kinds are false. |
| `blob` | Null, or exactly `sha256`, `size`, `path` as below. |

The document kinds include video/audio/voice/sticker and other document
variants. Unsupported media, such as link previews, contacts or polls, remains
a reference even in download mode. A photo uses the representation selected by
Telethon's default downloader, including cached/progressive sizes or a video
variant when selected. `kind` describes the attachment, not a promise of a
particular blob encoding.

In `references` mode every `blob` is null and no media file is downloaded. In
`download` mode each `downloadable` attachment must have a complete blob;
unsupported attachments must still have null blobs. A blob requires a nonnull
asset ID and a supported media kind.

| Blob key | Type and meaning |
|---|---|
| `sha256` | Lowercase, 64-character SHA-256 hex of the downloaded bytes. |
| `size` | Nonnegative integer byte count, at most `9223372036854775807`. Must equal media `size` when that source size is known. |
| `path` | Exactly the digest basename, with no extension or directory components. |

`blob.path` is relative to the **media directory** passed to the fetch, which
may differ from the directory passed to `batch.save()`. Saving a manifest does
not copy or upload its media. Retain/deliver both; the manifest contains no
absolute storage root. References alone are not offline download credentials.

Media streams to a private temporary file. After successful SDK completion,
tgdata flushes/fsyncs, hashes in bounded chunks and checks any known source
size, closes the file, then publishes under the digest using a non-replacing
hard link. Equal bytes share one file even across different messages; changed bytes get a new
name. An existing digest path must be a regular nonsymlink file with matching
size and hash. Corrupt entries raise rather than being silently replaced.
Fresh fetches still download bytes to establish identity; only saved-batch
replay avoids fetching them again.

Manifest publication uses the same complete-file rule under
`<batch_id>.json`. Reusing that path verifies the complete serialized bytes.
The filesystem must support hard links; unsupported operations raise. Hashing,
fsync and publication use synchronous local I/O on the event loop, with bounded
hashing memory. This does not promise arbitrary-storage latency or durability
through power loss.

## Canonical encoding and identity

V1 uses JSON encoded as UTF-8, without a BOM or trailing newline. For Python:

```python
import hashlib
import json

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

payload = {key: value for key, value in envelope.items() if key != "batch_id"}
expected_id = hashlib.sha256(canonical(payload)).hexdigest()
assert envelope["batch_id"] == expected_id
wire_bytes = canonical(envelope)
```

All fields except `batch_id` participate, including mode, stop reason, nullable
metadata and record order. No export timestamp or storage root is included.
The manifest file itself also contains `batch_id`, so its whole-file SHA-256
is **different** from the payload identity used as its filename.

`MessageBatch.from_json(str_or_utf8_bytes)` accepts ordinary JSON whitespace
and key order, validates v1, verifies its payload identity and re-encodes
canonically. It rejects unknown/missing fields, duplicate keys, unsupported
versions, invalid identifiers/timestamps/types, booleans in numeric fields,
nonfinite values, invalid Unicode, inconsistent cursors/modes/blobs and hash
mismatches. It does not open media files to verify their contents. A digest
checks content consistency; it is not authentication or a signature.

## Failures, replay and acknowledgment

Once the canonical chat is resolved, an ordinary preparation failure is
re-raised as the **same exception object**, with `error.partial_result` set to
a `MessageBatch` for the completed prefix. Its reason is `interrupted`, and
its cursor does not pass the failed record or an unfinished requested file.
Before source resolution, no batch is fabricated. `BatchFormatError` and
`BatchStorageError` represent local failures; ordinary filesystem errors,
Telegram errors and `ReadBudgetExceeded` retain their classes and existing
health meaning.

Owned local filesystem operations retain their original exception object/type
and suppress unrelated exception context, including when the SDK invokes the
supplied file's write/flush methods. A real SDK/transport failure keeps its own
cause and health meaning. If close or temporary-file removal also fails during
an active failure or cancellation, the original outcome takes precedence.
Secondary cleanup failures produce a WARNING containing only the operation
and exception type, never the error text, path or traceback; diagnostic delivery
cannot replace the chosen outcome. If cleanup is the only failure, its first
error is raised and later cleanup is still attempted.

```python
from tgdata import MessageBatch, ReadBudgetExceeded

try:
    batch = await tg.get_message_batch(group_id, after_id=cursor, limit=200)
except ReadBudgetExceeded as error:
    partial = error.partial_result
    if isinstance(partial, MessageBatch) and partial.messages:
        pending_manifest = partial.save("pending")
        # Deliver this saved prefix through the same acknowledgment protocol.
    raise
```

Cancellation propagates and attempts to close/remove temporary files. Cleanup
is best-effort when the filesystem refuses it, so a private `.tgdata-...` file
may remain; a completed immutable blob may remain too. No partially written
object is published under a final digest name. There is no durable cursor owned
or advanced by this API,
and cancellation does not promise a returned partial batch.

For delivery, the caller should:

1. Save the prepared batch and retain its referenced media before sending.
2. Send the saved bytes with `batch_id` as the receiver's deduplication key.
3. Have the receiver durably commit acceptance/effects and deduplication
   together before acknowledging. Acknowledging an already accepted ID must
   also be safe.
4. Advance the durable cursor to `next_after_id` only after that acknowledgment.
5. If acknowledgment is lost, reload and resend the saved manifest and blobs,
   using the same ID. Do not replace it with a new Telegram fetch.

A saved observation always replays with the same ID. A fresh read can differ
because messages, visible history, metadata, selected files, boundaries or stop
reason changed. Different batches may contain the same message, so receivers
that need message-level upserts must also use `(chat_id, message.id)`. tgdata
does not supply the receiver, cursor database, upload transport or an
exactly-once processing guarantee.

The offline suite exercises the actual 1.45.0 SDK with scripted transport and
real local files. Its receiver stand-in demonstrates the ordering above; it
does not verify a deployed receiver, live Telegram selection or a deployment
filesystem.
