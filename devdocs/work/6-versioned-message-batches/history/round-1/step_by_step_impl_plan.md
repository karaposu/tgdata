---
model: unknown
effort: unknown
---

# Plan — stable, versioned message batches (issue #6)

**Revision 1.** Inputs: `desc.md` (`9928658`), completed traverse (`c7f7e1e`),
the real SDK/filesystem probes, and the user's Telethon **1.45.0-only** target.

### What is the task

Add a producer-owned message-batch value and an additive bounded reader. The
value has an exact JSON v1 contract, a content-derived identity, a safe next
cursor and optional content-hashed files. Callers can persist and resend the
same value independently of Telegram and a future worker, while existing
DataFrame/media behavior remains compatible.

### Huge Hard Blockers

#### Planning Blockers

None open. The proposed transport/filesystem seams were read and observed
before building: the actual 1.45.0 iterator preserves senderless/service messages;
the presentation converter can omit one; the SDK writes to and returns a supplied
file object; 24 concurrent local publishers produce one complete hash-named
object without temporary leftovers. `probe_batch_seams.py` records these probes.
Scripted replies cover client control flow, not live Telegram behavior.

The schema and limits below are explicit local design choices derived from
the request and traverse. There is no existing raw schema or receiver in this
repository requiring a migration or outside approval. A schema fixture will
make those choices reviewable before integration.

#### Execution Blockers

None for local implementation and offline tests. Live Telegram and deployment
volume/receiver validation are outside this run. No further 1.33.1 work is
required. Merge/deployment remain separate stages. Model/effort metadata are
unavailable and recorded as unknown, not certified under CONTRIBUTING §9.

### How this implementation moves toward desired state

A standard-library value/codec owns the wire contract. A small file module owns
temporary files, byte hashing and non-replacing publication. A new batch engine
iterates through the existing guarded client and completes one record at a time;
only then does it append the record and advance its cursor. TgData exposes the
engine through a new method with the existing health-reporting boundary.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Define and implement the v1 value/codec | Validated deterministic MessageBatch with exact fields |
| 2 | Publish complete content-addressed artifacts | Media and manifest files with integrity-checked reuse |
| 3 | Implement bounded raw reading | Complete-prefix batches through the existing client guard |
| 4 | Expose the additive public API | New method/exports without changing old successful calls |
| 5 | Specify the contract and test behavior | Normative docs, example and offline test_19 |
| 6 | Verify and commit | Passing supported offline checks, separate code/work-note commits |

## Step 1 — Value, schema and canonical encoding

### Proposed changes

Add `tgdata/message_batch.py`, standard-library only except its eventual local
file-publisher import in step 2. Public types: immutable `MessageBatch` and
`BatchFormatError` (a ValueError-compatible local exception suppressing incidental
context). Use frozen state containing canonical JSON text; `to_dict()` returns
a fresh decoded copy. No user mutation of that copy alters the value.

V1 envelope has **exactly** these keys:
- `schema`: literal `"tgdata.message-batch"`; `version`: integer `1` (not bool).
- `batch_id`: lowercase 64-character SHA-256 hex string.
- `chat_id`: canonical negative decimal string for the resolved marked Telegram
  group/channel ID, within signed 64-bit range, nonzero.
- `after_id`, `next_after_id`: canonical decimal strings in `0..2**31-1`.
- `media_mode`: `"references"` or `"download"`.
- `stop_reason`: `"limit"`, `"end"` or `"interrupted"`.
- `messages`: ordered list, at most 10,000 records.

Each record has exactly:
- `id`: positive canonical decimal string, at most `2**31-1`.
- `kind`: `"message"` or `"service"`.
- `date`, `edit_date`: UTC ISO strings with six fractional digits and `Z`, or
  null when metadata is unavailable.
- `text`, `post_author`: strings or null.
- `sender`: exactly `id`, `name`, `username`; ID is a nonzero signed 64-bit
  decimal string or null, other fields strings or null. Username is bare, without
  adding `@`. No missing-value sentinel or network enrichment.
- `reply_to_id`: positive message-ID string or null.
- `forward_from_id`, `grouped_id`: nonzero signed 64-bit decimal strings or null.
- `service_action`: opaque SDK action type name for a service record, otherwise
  null; v1 does not preserve every action-specific field.
- `media`: null or the media object below.

Media has exactly `kind`, `id`, `mime_type`, `file_name`, `size`, `downloadable`,
`blob`. Kind uses the existing detector's vocabulary: photo, video, video_note,
gif, audio, voice, document, sticker, webpage, contact, geo, poll, other. ID is a
nonzero signed 64-bit decimal string or null; MIME/name are strings or null;
size is a nonnegative integer up to `2**63-1` or null. `downloadable` is bool.
Full Photo and Document attachments are supported for download, including the
semantic document kinds above. Other kinds/empty assets remain references only.
Photo MIME/size are not invented when the SDK supplies neither.

Blob is null or exactly `sha256`, `size`, `path`: lowercase SHA-256 hex,
nonnegative integer size, and a basename equal to that digest (no extension or
directory components). In reference mode every blob is null. In download mode
each downloadable media record must have a blob; unsupported media must not.
When source size is known, require blob size to match it. A blob requires a
non-null media ID and a supported media kind. Original file_name is metadata
only, never a filesystem destination.

All record IDs must be strictly increasing and greater than after_id. The next
cursor equals the final record ID, or the input cursor for an empty list. A
`limit` batch must be nonempty. Null media has no hidden file requirement.
All text must be valid UTF-8; reject invalid surrogate strings. Do not accept
unknown/missing keys, arbitrary objects, bool-as-number, noncanonical IDs,
nonfinite values, duplicate JSON keys or unsupported versions.

Canonical payload: `json.dumps(payload, ensure_ascii=False, sort_keys=True,
separators=(',', ':'), allow_nan=False)` encoded as UTF-8. `batch_id` is SHA-256
of that encoding **with batch_id omitted**. Serialize the final envelope by the
same rule with batch_id included. No export timestamp, account credential,
absolute path or transient access/file-reference token enters it.

Provide internal construction from validated complete records; public
`MessageBatch.from_json(text_or_bytes)` validates and verifies identity.
`to_json()` returns canonical text; `to_dict()` returns a defensive copy.
Expose convenient `batch_id`, `chat_id`, `after_id`, `next_after_id`, `messages`,
`stop_reason` and `media_mode` accessors; ID/cursor accessors return Python ints,
while the wire format retains strings. The byte format/version is independent
of the package version.

### Output

A deterministic, validated batch value independent of Telegram sockets.

### Safe in nature
True — new component, not wired into existing imports/calls yet.

### Peripheral concepts
canonical JSON, SHA-256, exact integer identity, UTC dates, optional metadata,
immutability, strict version validation, service messages, schema fixtures

### Hardness Lvl
3

## Step 2 — Complete file publication

### Proposed changes

Add `tgdata/batch_files.py`, a standard-library leaf module, with public local
`BatchStorageError` and private file helpers. Format/storage local errors suppress
incidental exception context; ordinary filesystem and Telegram errors keep their
original classes. No dependency on the value/engine modules, avoiding cycles.

An async download helper receives a media directory and an awaitable writer
that accepts an already-open binary file object. Create a private temporary
file inside that directory; await the writer; reject None or an unexpected output
object instead of publishing an empty success. The SDK probe establishes that
download_media returns the supplied file object. Flush/fsync, hash in bounded
chunks, check a declared source size when available, then close and publish.
Temporary paths are removed on success, exception and cancellation.

Use non-replacing `os.link` to publish the fully written temporary file under
its SHA-256 basename. On FileExistsError verify the existing destination is a
regular nonsymlink file with the expected size and content digest. Reject a
corrupt/directory/symlink destination; never silently overwrite it. Unsupported
filesystem operations raise. File hashing and publication are synchronous local
I/O with bounded memory; no claim of arbitrary storage latency or power-loss
durability. Cancellation may leave an already completed immutable blob, but
never a partially written public object or an advanced external cursor.

Add `MessageBatch.save(directory)` using the same publication principle for
canonical UTF-8 manifest bytes, named `<batch_id>.json`; return its Path. Verify
existing manifest bytes against the full serialized file digest before reuse.
The manifest filename is its payload identity, not a claim that the file's own
SHA equals batch_id (the file also contains that ID). Save publishes only the
manifest; callers retain/upload referenced media separately. Output-directory
choices never change the wire value. Validate/create local directories explicitly.

### Output

Verified digest-named media and safely replayable manifest files.

### Safe in nature
True — new opt-in file operations, no legacy filename changes.

### Peripheral concepts
temporary files, streaming SDK output, fsync, bounded hashing, hard-link publish,
concurrency, cancellation cleanup, corrupt-cache detection, portable references

### Hardness Lvl
3

## Step 3 — Bounded raw batch engine

### Proposed changes

Add `tgdata/batch_engine.py` with `BatchEngine(connection_engine)` and
`fetch_batch(group_id, *, after_id=0, limit=200, download_media_to=None)`.
Accept an explicit group ID/name, integer after_id in `0..2**31-1`, and integer
limit in `1..10000`; reject bool/nonintegral values and missing/invalid group
or media-directory arguments before connecting. No current_group fallback or
silent limit truncation. References is the default; a provided directory
selects download mode.

Use `connection_engine.session()` and client.get_entity. Reuse the existing
dialog-sync fallback on ValueError. Require a Chat/Channel; report forbidden
group objects as GroupAccessError rather than misclassifying them as formats.
Resolve the canonical marked ID with Telethon's peer utility. No independent
client, session or account state is created.

Iterate `client.iter_messages(entity, min_id=after_id, reverse=True, limit=limit)`.
For each yielded normal/service message:
1. Check its peer matches the resolved chat and ID advances monotonically.
2. Project the specified raw fields using the message and cached sender only.
   Preserve missing values and full text; use `action is not None` to identify
   service records on 1.45.0. Convert peer references to marked IDs. Reuse the
   existing media-type detector, but never `_process_message` or `get_sender`.
3. Determine supported full Photo/Document media explicitly. In download mode,
   pass `client.download_media(message, file=output)` to step 2's helper and
   attach the verified blob; no web-preview/contact/other downloads are added.
4. Validate/encode the complete record before appending it and advancing the
   local continuation. A bad record or asset leaves that message uncompleted.

After iteration, return a MessageBatch with `limit` when exactly the requested
number completed, otherwise `end` (SDK iteration ended). Do not issue another
request to infer has_more. On any ordinary exception after group resolution,
attach a MessageBatch for the complete prefix to `error.partial_result`, with
`interrupted`, then re-raise the same object. Failures before source resolution
have no fabricated batch. Cancellation propagates and cleans temporary files;
no durable caller cursor is stored by this API.

Do not add engine-level retries beyond the existing client/SDK policy. A caller
can persist a partial batch and resume from its cursor; every repeated network
read is still charged by #9. Existing ReadBudgetExceeded/Telegram errors and
health classifications stay intact. Unsupported-media references are explicit
records, not disguised file-download successes.

### Output

A raw reader that produces complete-prefix values through the shared guard.

### Safe in nature
True — new engine, not yet invoked by existing public APIs.

### Peripheral concepts
Telethon 1.45.0 iteration, marked peers, group resolution, cached sender data,
media projection, budget re-fetches, partial_result, cancellation, error identity

### Hardness Lvl
4

## Step 4 — Public integration

### Proposed changes

In `tgdata/tgdata.py`, construct BatchEngine using the same ConnectionEngine.
Add `get_message_batch(group_id, *, after_id=0, limit=200, download_media_to=None)`
under the existing `_reported('group_id')` wrapper, returning the engine's value.
It does not change current_group or existing delegates. Export MessageBatch,
BatchFormatError and BatchStorageError from `tgdata/__init__.py`.

Update the stale setup.py dependency comment that says every API returns a
DataFrame: legacy APIs still require pandas. No package version bump, dependency
installation or release is part of this task. Test the requested SDK 1.45.0.

### Output

One documented additive public entry point and importable value/errors.

### Safe in nature
False — shared façade/package imports change and must retain old behavior.

### Peripheral concepts
public imports, shared engine lifetime, health boundaries, package discovery,
existing API compatibility, pandas dependency

### Hardness Lvl
2

## Step 5 — Normative docs and behavioral suite

### Proposed changes

Add `docs/message_batch_v1.md` with the exact schema, ID/date/null rules,
canonical hash algorithm, mode/stop semantics, examples, save/reload and receiver
deduplication/acknowledgment order. Distinguish replay from a fresh fetch and
message identity from batch identity. Describe unsupported media and metadata
omissions; no full-archive, complete-album or exactly-once service claim.
Add a README example and smoke-test README entry.

Add `tgdata/smoke_tests/test_19_message_batches.py`, offline on Telethon 1.45.0,
synthetic credentials and blocked sockets. Use real SDK request/iterator/download
paths with scripted transport plus real temporary files. Include:
- a fixed golden v1 JSON/hash fixture, Unicode/large signed IDs, dates/nulls,
  service/senderless messages and no enrichment calls;
- immutable value/defensive-copy behavior; save/load identity and directories;
- malformed/duplicate-key/nonfinite/unsupported-version/hash-mismatch inputs,
  strict ID/cursor/order/mode/blob constraints;
- bounded chronological reads, after-ID behavior, empty/end versus bound,
  invalid input before connection and group/peer validation;
- real budget exhaustion with a nonempty/empty raw partial and safe resume;
- original network/RPC/local errors with complete prefix, correct health
  reporting and no invented Telegram verdict;
- exact media bytes/hashes, equal-content dedup across messages/directories,
  changed content, missing/truncated output, unsafe metadata filenames,
  corrupt/symlink destinations, concurrent writers and cancellation cleanup;
- an implicit media-reference refresh stopped by the real budget guard;
- saved manifest replay through a tiny in-memory receiver stand-in, with one
  accepted batch ID and cursor advancement only after acknowledgment;
- existing DataFrame/media calls still use their original contracts.

Keep golden expectations explicit; do not weaken assertions to bless the code.
The publication probe is evidence for a primitive, not a replacement for tests
of the implemented publisher/reader composition.

### Output

A usable v1 contract and executable offline regression evidence.

### Safe in nature
True — docs and synthetic tests only.

### Peripheral concepts
schema fixtures, SDK transport scripts, filesystem fault injection, concurrency,
receiver stand-in boundaries, README and compatibility documentation

### Hardness Lvl
3

## Step 6 — Verify and commit

### Proposed changes

Compile, run test_19, then the full supported offline suites 12–18 and the two
no-network discovery helpers. Disable live 12/13 cases with an explicit nonexistent
config; localhost proxy cases may need sandbox permission. No 1.33.1 run. Do not
run historical live/manual smoke demonstrations against an account.

Under task-impl's Verify gate, correct only small local failures without changing
plan decisions; record every correction and rerun what failed. Larger/architectural
failures stop the run. Record exact counts, skipped checks, limitations and plan
deviations in `implementation.md`. Commit code/tests/public docs separately from
work notes, preserve/exclude the unrelated group-discovery guide edit, publish
the feature branch checkpoints and update #6 only from committed evidence.

### Output

Verified implementation ready for the later merge check and PR critique.

### Safe in nature
True.

### Peripheral concepts
offline suite boundaries, version target, separate commits, truthful issue status,
unchanged user work, task-impl verification gate

### Hardness Lvl
2
