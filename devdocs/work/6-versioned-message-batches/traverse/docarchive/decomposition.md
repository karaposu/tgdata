---
model: unknown
effort: unknown
---

# Decomposition — batch contract and its boundaries

## User Input

`../_branch.md` and saved `sensemaking.md` SV6: partition the producer snapshot
contract without separating the cursor from completed preparation. DV1.

## 1. Coupling Map

| Cluster | Strongly coupled elements | Boundary to other clusters |
|---|---|---|
| P1 — representation | normalized message fields, ID/date types, envelope/version, canonical identity, validated reload | accepts prepared records and portable blob references; supplies a stable value |
| P2 — artifact publication | temporary output, complete bytes, digest/size, atomic publication, existing-file verification | accepts a byte/file producer; returns a verified portable reference or raises |
| P3 — bounded reading | group resolution, SDK iteration, selected media mode, completed prefix, cursor, interrupted result | consumes P1/P2 contracts plus existing guarded client; returns a batch or original failure with prefix |
| P4 — library/consumer integration | public method/options, unchanged legacy APIs, exports/docs, caller replay/acknowledgment rules | exposes P3/P1 to callers; supplies configuration and existing health context |

Changing canonical fields changes batch identity: those stay together in P1.
Publishing a hash before bytes are complete would break its meaning: those stay
together in P2. Advancing a cursor before record/media completion loses work:
that state machine stays together in P3. Neither file publication nor record
encoding owns Telegram authentication or the later receiver.

## 2. Boundaries detected top-down

P1 can be exercised from plain values and synthetic SDK messages without a
network or filesystem. P2 can be exercised with a file writer without knowing
Telegram message fields. P3 is deliberately the composition point; its dependencies
are explicit completion/error interfaces, not shared global counters. P4 is a
small boundary around existing APIs and documentation, not a second reader.

The producer/receiver boundary is outside these four pieces: receiver storage
and cursor acknowledgment belong to the calling application/#10. Its obligations
must be documented by P4 so that exclusion does not become a hidden guarantee.

## 3. Bottom-up boundary validation

- An exact peer ID, nullable sender and UTC timestamp are record atoms: P1.
- A digest is meaningful only with the completed file it names: P2, not P1's
  serializer guessing a hash from a Telegram file ID.
- An awaited media operation and the append/cursor update around it are one
  state transition: P3. They cannot be cut into unrelated callbacks.
- A budget error's type/cause and the already prepared prefix cross P3/P4;
  they must not be replaced by a success-shaped partial return.
- Replayable manifest bytes link P1 to P2, but do not require either piece to
  know the receiver's database or acknowledgment protocol.

Top-down and bottom-up agree on all four boundaries: HIGH confidence. No
residual atom is unowned. The reader is the largest piece, but its mutable
prefix/progress state is one tractable algorithm, not a separate framework.

## 4. Question Tree

**Root:** how does one bounded read produce a portable, versioned, replayable
artifact with a continuation that never skips unfinished requested output?

### P1 — What exactly is a valid snapshot, and how is its identity stable?

Verification criteria: explicit version/field/type/absence rules; namespaced
source and sender identities; strict continuation consistency; no vendor objects,
credential fields or absolute paths; deterministic identity and save/load bytes;
unknown version or malformed/tampered content rejected; required message kinds
remain representable even without resolved sender metadata.

### P2 — When may completed bytes be referenced by their content hash?

Verification criteria: streaming or file-based production; hash/size computed
from complete bytes; no partial public filename; cleanup on cancellation/error;
safe reuse with integrity checking and concurrent writers; portable references;
publication failure returned to the caller rather than hidden. The determination
of “already exists and is correct” belongs here, with an actual byte/digest check.

### P3 — How does reading maintain a complete, resumable prefix?

Verification criteria: validate bounded input before I/O; resolve one canonical
chat; read ascending after an exclusive ID through the existing quota guard;
prepare each record and requested media before advancing; distinguish reaching
a bound from observed end; preserve a useful prefix on quota/network/media/
encoding failure; propagate original error/health semantics; empty first-page
failure does not invent progress. Determine downloadable media from explicit
SDK type/mode rules, not from a truthy generic attachment flag.

### P4 — How do callers adopt and deliver the contract safely?

Verification criteria: additive public API and exports; existing DataFrame,
callbacks and filename semantics unchanged; documented v1 schema and examples;
caller can persist/reload/replay without Telegram; receiver deduplicates by
supplied identities and commits continuation only after its durable acknowledgment;
all supported offline regressions run with live checks disabled.

## 5. Interface Map

| Source → target | Flow | Assumptions carried with it |
|---|---|---|
| P1 → P3 | record/envelope contract and construction/validation | record validation must succeed before prefix append; identity never depends on local roots or wall-clock export time |
| P2 → P3 | completed blob reference or exception | a returned reference names complete bytes; None/missing bytes cannot masquerade as success in a mode requiring a file |
| guarded client → P3 | entities, ordered messages and original errors | actual sends remain metered; SDK buffering is not caller acknowledgment; no additional quota bypass client is created |
| P3 → P1 | ordered complete records, source, input/next cursor, observed stop | next cursor covers only this complete prefix, even if more network slots were charged |
| P1 → P2 | finalized manifest bytes/digest for local publication | publish the same bytes whose identity was computed; reject unsupported/tampered input before trusting it |
| P4 → P3 | normalized caller request and health context | one group, explicit bounded limit, selected media policy; errors remain errors |
| P3/P1 → P4/caller | immutable or defensively copied batch plus resumable partial on failure | mutation of a returned dict cannot silently alter the saved identity |
| caller → receiver (external) | artifact/blobs and acknowledgment | upload replay means reusing saved output; only the receiver can enforce its write/dedup transaction |

The apparent P1/P3 cycle is a contract dependency, not a runtime ownership cycle:
define P1's value schema first; P3 supplies data to construct that value. P1 does
not call the reader. P1/P2 share a byte-publication contract; P2 is otherwise
unaware of the envelope schema.

## 6. Dependency Order

First settle P1's semantic value/reference interfaces and P2's publication
completion interface. Then P1 encoding and P2 filesystem behavior can be proved
independently. P3 composes them with the existing client. P4 exposes the result
and verifies compatibility/consumer instructions. Tests for each contract precede
or accompany composition; the complete offline suite follows implementation.
This is a dependency topology, not yet an implementation plan or assignment to
parallel agents. The traverse disciplines continue sequentially in-session.

## 7. Self-Evaluation and telemetry

Independence PASS: each question is answerable against its stated interface.
Completeness PASS: all requested messages/cursor/media/replay and failure cases
are owned. Reassembly PASS: P3 composes valid records with completed blobs into
P1 output, exposed by P4; the external acknowledgment obligation is explicit.
Determination mechanisms are covered: schema/version/identity in P1, existing
blob correctness in P2, message/media eligibility and stop reason in P3.
Tractability PASS: four bounded questions; no piece needs a new worker.
Interface clarity PASS: timing, mutability and acknowledgment assumptions are
stated, not merely the data types. Balance PASS: P1/P2/P3 carry separate real
complexity; P4 is intentionally the smaller integration boundary. Confidence
PASS: bottom-up atoms agree with the top-down partition.

Four pieces, eight interfaces, no unresolved runtime dependency cycle. Seven
process steps and seven quality dimensions complete. Checked premature/wrong
decomposition, hidden coupling, missing pieces, over-decomposition, dependency
ordering and imbalance; no remaining flags. Manual structure 7/7. **PROCEED**
to innovation with the exact value/API/media-mode choices still open.
