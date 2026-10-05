---
model: unknown
effort: unknown
---

# Sensemaking — what the batch contract promises

## User Input

`../_branch.md`: derive a stable interpretation of I1's four raw-batch/replay
readings from `surfacing.md`, before choosing implementation parts. The full
original request is retained in `../source-input.md`.

## SV1 — Baseline understanding

At first glance #6 looks like adding a version, next-message number and hashes
to the current fetch result. That leaves “raw”, “batch”, “continue” and
“repeated upload” carrying several different meanings.

## Phase 1 — Cognitive anchors

- **Constraints C1–C3:** the requested producer is tgdata, not the later #10
  worker; output must include messages/continuation/media references; #9's
  shared guard applies to actual pulls, including re-fetches during downloads.
- **Insights K1–K3:** current presentation rows can omit an SDK message when
  its sender cannot be resolved (`MessageEngine._process_message`); the existing
  JSON exporter substitutes binary data and has no version/schema; existing
  media paths identify a message, not its downloaded contents.
- **Structural points S1–S3:** SDK pages, application rows and file writes
  complete at different times; continuation belongs to a particular chat;
  transport delivery/acknowledgment will be managed outside this library.
- **Foundational principles P1–P3:** a cursor must not silently skip unfinished
  requested output; identities need enough namespace to avoid group collisions;
  naming bytes by their digest supports reuse but does not execute a receiver's
  deduplication transaction.
- **Meaning nodes M1–M3:** observed message snapshot; prepared batch artifact;
  acknowledged continuation. These name distinct states of the same work, not
  additional subsystems to build.

## SV2 — Anchor-informed understanding

The missing object is a producer-owned snapshot contract. A rendered table is
not the authoritative scan record, and a read cursor is not evidence that a
receiver stored the output. Hashing and continuation must refer to what was
actually prepared for delivery.

H4/H5 check: “snapshot” is a bounded set of observed messages, not a frozen
Telegram database. The example of 200 messages is an instance of any bounded
batch; missing senders, service messages and interrupted media are the broader
pattern that a row-only wrapper would conceal.

## Phase 2 — Perspective checking

**Technical/logical:** a generated SDK object contains vendor-specific nested
types, dates and byte references. TLObject's generic JSON fallback can use repr.
A stable cross-version envelope cannot let that serializer silently define its
public fields. This adds the anchor of explicit field ownership.

**User:** someone storing the supplied next cursor expects no requested message
to disappear. A media error after several successful messages needs a recoverable
prefix and a cursor before the failed message. This adds the anchor of preparation
progress, distinct from network-page consumption.

**Strategic:** #10 needs a payload contract now, but its receiving storage and
job acknowledgment do not exist here. A replayable artifact plus stable identity
is useful without claiming exactly-once processing. This adds a delivery-boundary
anchor that the initial “add fields to a DataFrame” picture lacked.

**Risk/failure:** fetching the same range later can observe an edit, deletion,
different metadata or changed media. A saved batch can be replayed; a new server
observation cannot be forced to match an old one without retaining that old
observation. IDs and file paths alone do not prove equal bytes.

**Resource/feasibility:** the unit should stay bounded. Large media should pass
through temporary files and hashing rather than requiring all bytes in memory.
An extra read to determine whether more history exists also spends quota; the
format can honestly distinguish reaching the requested bound from observing end.

**Ethical/systemic:** sender IDs/text are requested data, but transport credentials,
access hashes, transient file-reference bytes and local absolute paths do not
belong in an interchange artifact. Missing metadata should remain missing,
without fabricated author identities or unnecessary enrichment calls.

**Definitional/internal:** “raw” can mean the requested unprocessed message
fields; it need not mean every Telegram implementation detail. The strongest
counter is full archival preservation. That remains a distinct depth choice,
but generic SDK dumps do not meet the independent-evolution purpose without
another explicitly versioned contract around their contents.

**Frame-exit completeness:** the inherited term “batch” has four referents here:
an SDK page, a DataFrame callback group, the proposed artifact, and a future
worker delivery. The first two affect production, the third is the owned
contract, and the fourth is an external acknowledgment boundary. Ignoring the
last would make an exactly-once claim false; relocating it to a caller obligation
preserves coherence. An album is another grouping in the message stream, not
proof that a requested batch boundary contains the entire album. Preserve its
group ID so a consumer can associate parts across batches. The strongest counter
asks for a full receiver/album-completion protocol now; that would require new
storage/transport behavior and extra reads beyond the requested bounded unit.
Residual concerns reduce to these ownership/counting boundaries.

**Phase/calibration:** no existing public raw schema or deployed receiver is
present in this repository. The first version can establish explicit rules,
but tests must become fixtures for those rules rather than assuming downstream
requirements were already agreed elsewhere. Numeric read quotas remain unrelated
application policy, not a rate-safety claim by this task.

## SV3 — Multi-perspective understanding

The contract separates observation, preparation and acknowledgment. It owns an
explicit record representation, a chat-scoped continuation and content identities.
It must not inherit presentation filtering, claim that refetch equals replay,
or imply that receiver-side exactly-once storage already exists.

H1/H2/H3/H7 check: the four initial readings are still evaluated, not silently
reduced to the familiar export path. The frame includes failure/receiver obligations
without importing a new worker. The question's “stable” does not assume a static
server. V1 is a new producer contract, not a migration of an existing raw format.

## Phase 3 — Ambiguity collapse

### A1 — Raw record versus current presentation row or full vendor dump

**Strongest counter-interpretation:** wrapping the current DataFrame is small;
dumping every SDK field would preserve the most information.
**Why the counter fails structurally:** presentation can already discard a
message, so its last row cannot represent all fetched work. Generic SDK dumps
change with vendor constructors and encode transport-only details, leaving the
“fixed format” owned by another layer. Neither alone supplies the requested
producer contract.
**Confidence:** HIGH that tgdata must own an explicit representation; LOW on
the exact optional-field depth until design/critique chooses it.
**Resolution:** preserve the requested unprocessed fields and message identity
without depending on sender enrichment or the DataFrame conversion.
**Fixed:** producer-owned schema; no silent message loss for absent metadata.
**No longer allowed:** treating an arbitrary SDK dump or current row set as
sufficient proof of raw-contract completeness.
**Depends on this:** record projection, schema fixtures and public documentation.
**Model change:** raw batch production is a distinct contract from presentation.

### A2 — Repeat upload versus repeat fetch

**Strongest counter-interpretation:** a deterministic query plus a fixed cursor
should recreate the same bytes, avoiding local artifact retention.
**Why the counter fails structurally:** the request does not address a historical
immutable revision; a later read is a new observation. Reconstructing an old
observation after its contents change requires preserving it somewhere.
**Confidence:** HIGH; the issue explicitly describes repeating an upload.
**Resolution:** identity/replay guarantees apply to prepared snapshot bytes.
**Fixed:** persist and resend the same artifact for delivery retries.
**No longer allowed:** promising equal batches for arbitrarily changed server
state or conflating a new read with replay.
**Depends on this:** batch identity, local export and receiver instructions.
**Model change:** immutable artifact identity and mutable observation are separate.

### A3 — Continuation after inspection versus after complete representation

**Strongest counter-interpretation:** advance to the newest inspected ID and
describe errors separately so the reader never stalls.
**Why the counter fails structurally:** an append-only caller then omits failed
messages/media permanently unless a second retry queue is invented. No such
queue is requested or present. A complete prefix needs no hidden recovery queue.
**Confidence:** HIGH for a mode that promises downloaded media; references-only
mode has no byte-completion obligation.
**Resolution:** continuation advances only past fully prepared message records
under the selected mode. An interrupted prefix is recoverable and the failure
retains its type/cause.
**Fixed:** chat-scoped, exclusive continuation after a represented prefix.
**No longer allowed:** moving past a failed requested asset or a dropped row.
**Depends on this:** partial results, media publication and resume tests.
**Model change:** quota consumption and application continuation can differ
legitimately; retrying a failed message may spend quota again.

### A4 — Content identity versus naming a message's file

**Strongest counter-interpretation:** existing message-based filenames already
prevent duplicate files and can simply be put in the batch.
**Why the counter fails structurally:** equal bytes from different messages
produce different names, and changed bytes under the same message ID reuse an
old path. A path or Telegram file ID is not a digest of downloaded content.
**Confidence:** HIGH.
**Resolution:** file identity is derived from completed bytes; output references
must not depend on the producing machine's absolute path.
**Fixed:** digest-to-bytes relationship and portable relative references.
**No longer allowed:** labeling a partial download or reused message filename
as a verified content hash.
**Depends on this:** storage publication and integrity/concurrency tests.
**Model change:** existing media APIs can remain compatible while the new
contract uses a separate publication policy.

### A5 — Batch identity versus exactly-once receiving

**Strongest counter-interpretation:** “nothing is duplicated” requires building
receiver transactions as part of #6.
**Why the counter fails structurally:** this repository is the reader library;
#10 explicitly introduces the job/worker boundary later. Stable keys can be
supplied now, but a receiver must check them and acknowledge its own durable
write. A hash cannot perform that write for it.
**Confidence:** HIGH.
**Resolution:** define reusable batch/blob identities and document deduplication
and cursor-commit obligations for callers.
**Fixed:** the producer's guarantee and the receiver's responsibility.
**No longer allowed:** claiming end-to-end exactly-once delivery without a
receiver or advancing durable caller progress before acknowledgment.
**Depends on this:** upload example, batch save/load and future #10 integration.
**Model change:** #6 is useful independently while retaining an honest boundary.

### A6 — Batch boundary versus end-of-history or complete album

**Strongest counter-interpretation:** a full requested batch proves more messages
exist, or it should extend automatically to finish a grouped album.
**Why the counter fails structurally:** reaching a count supplies no observation
of the next message. Extra reads consume #9 quota, and album sizes are not the
requested count. Preserving grouping identity is enough to avoid inventing a
guarantee about where server history ends.
**Confidence:** HIGH.
**Resolution:** report what was observed: bound reached, history ended, or
interrupted; preserve grouping IDs without promising album-atomic batches.
**Fixed:** truthful completion semantics and bounded requested work.
**No longer allowed:** unobserved `has_more` claims or automatic extra pulls
solely to make a batch look complete.
**Depends on this:** envelope status and pagination tests.
**Model change:** completion is evidence about this read, not future history.

## SV4 — Clarified understanding

The viable meaning is an additive, explicitly versioned snapshot contract with
portable content identities and a safe continuation. The current DataFrame
wrapper alone, an unqualified full-SDK JSON dump, and a promise of identical
fresh reads do not meet that meaning. The deeper archival field set and exact
API/file shape remain bounded design choices, not hidden assumptions.

## Phase 4 — Degrees of freedom

Fixed: producer-owned schema; bounded ascending reads after a chat-scoped ID;
represent missing metadata; cursor after complete prefix; content hashes for
completed media; saved-snapshot replay; no worker/receiver transaction here.
Existing successful DataFrame/media behavior remains a compatibility constraint,
because callers still use it and an additive contract does not require migrating
them. Eliminated: implicit row filtering as raw completeness, path-as-hash,
refetch-as-replay, unobserved end/album claims.

Open for decomposition/innovation: exact public value/API shapes and v1 fields;
optional versus required media-download mode; canonical encoding/publication
mechanism and partial-result carrier. These can be resolved by local design and
probes before planning; no inaccessible human-owned premise was established.

## SV5 — Constrained understanding

One operation produces a finite prefix of message snapshots. Each prepared
record carries enough identity and references for a processor; any requested
bytes exist under their content identities before the record advances progress.
The resulting artifact can be stored and replayed. The caller decides when its
receiver has acknowledged enough work to commit the continuation.

## Phase 5 / SV6 — Stabilized model

#6 is an additive producer contract around a prepared message snapshot, not a
formatting change to a DataFrame and not a delivery service. The three states
observed → prepared → acknowledged explain cursor ownership, partial failures
and replay without requiring a new worker or hiding additional reads.

SV1 treated the work as extra export fields; SV6 ties identity and continuation
to completed preparation and gives the future receiver explicit obligations.
The last perspectives confirm those relationships instead of forcing exception
patches; the accommodation trigger does not fire.

## Telemetry and checks

Six ambiguity groups resolved/narrowed; two implementation-depth choices remain
explicitly open for downstream design. All five anchor types and eight
perspectives used; technical, failure, user and delivery perspectives added
different anchors. Frame-exit and phase checks were applied. H4/H5/H9 meanings
were tested in A1–A6; no inherited earlier sensemaking concept escaped a counter.
Status-quo, premature stabilization, anchor dominance, perspective blindness,
clean-resolution and self-reference checks raised no remaining process flag.
Six Sense Versions and every required resolution field are present. Manual
structure: 8/8. **PROCEED** to decomposition.
