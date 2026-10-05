---
model: unknown
effort: unknown
---

# Structural critique — the batch producer design

## User Input

Evaluate `innovation.md` P1–P4 against `sensemaking.md` and `../_branch.md`.
The user's latest steering targets Telethon **1.45.0**; no further 1.33.1 work
is required. This is the architecture selection, not the later critic-d pass
over the implementation plan.

## Phase 0 — Dimensions and weights

| Dimension | Weight | Substance-level pass condition and source |
|---|---|---|
| D1 — requested record fidelity | critical | actual yielded messages retain requested fields, including missing sender/service cases; test against SDK objects, not just a schema label |
| D2 — continuation safety | critical | failed preparation cannot move the next cursor beyond the complete represented prefix; use a failure on the second message as the counterexample |
| D3 — replay/content identity | critical | same saved bytes have the same identity and referenced files match their digest; a changed observation is not called the same artifact |
| D4 — tgdata integration risk | critical | new sends use the existing #9 guard and health context; old DataFrame/callback/media contracts remain usable |
| D5 — publication and data exposure | critical | no partial public blob, no reliance on untrusted media names, no transport secrets/absolute paths in the wire format |
| D6 — feasibility and extent | important | available SDK/stdlib behavior can produce the contract without inventing a worker or broadly rewriting working readers |
| D7 — external grounding/frame premises | critical | user wording, real code and observable primitives must support claims; an analogy or agreement among our own documents is insufficient |

These weights follow purpose: a failure on D1–D5/D7 defeats this producer's
guarantees; D6 distinguishes a sufficient implementation from a larger viable
future refactor. The dimensions span schema, state-transition and filesystem
failure planes, including the project-specific quota/health boundary. They do
not require deploying a receiver merely to test the claim that the receiver is
external.

Frame premises independently prosecuted:
1. **A new representation is needed.** If wrong, the current table/export could
   satisfy #6. The real probe below shows it omitting senderless message 101;
   that refutes using the table as the complete raw record source.
2. **Replay concerns saved output.** If wrong, query identity would have to
   freeze server history. The request says “If the upload is repeated after a
   network drop”; SDK reads have no historical-snapshot token. Persisted output
   is the available boundary for that promise.
3. **File identity belongs to this producer.** If wrong, the caller/receiver
   could rename files later. The requested output includes “media files named
   by a content hash”; moving all hashing downstream leaves that output absent.

## Phase 1 — Fitness landscape

Viable: an explicit producer-owned value, completed content publication and a
bounded guarded reader, exposed additively. Dead: row-only completeness,
vendor-dump-as-fixed-schema, origin-filename-as-content-identity, or replacing
existing returns without a migration requirement. Boundary: a universal scanner
and an acknowledgment stream are plausible larger work but not required here.
Unexplored: the eventual receiver's storage/ack protocol and exhaustive archival
fields beyond this issue's requested record surface; neither must be invented
to supply the present contract.

## Phases 2–3 — Prosecution, defense, collision and verdicts

### P1-G — Full SDK JSON in a versioned envelope: KILL

Prosecution: the outer version does not freeze a nested schema whose constructors,
fields and byte/date encodings are chosen by the SDK. Defense: it preserves
maximum information with little extraction code. Collision: completeness of
vendor fields is not independent evolution of a defined consumer contract; D1,
D3 and D7 fail as proposed. Seed: explicitly own the required field projection,
or later version a vendor archive separately if a consumer actually needs it.

### P1-F — Explicit canonical snapshot value: SURVIVE

Prosecution: mutable nested dicts can disagree with a saved digest; exact integer
and timestamp rules can be lost between Python and another consumer. Defense:
canonical bytes are the value, dicts are copies, IDs have exact string encoding,
and reload validates version/shape/hash. Collision: those are determination
mechanisms, not labels; D1/D3/D5 pass at the design level. It is fertile for
versioned fixtures and independent consumers without depending on an SDK dump.
All D1–D7 checked; exact schema examples are a required planning output before
implementation, not a claim that code already exists.

### P1-C — Standardize the existing DataFrame export: KILL

Prosecution: an omitted message has neither a row to serialize nor a safe cursor
derived from that row set. Defense: existing users already understand the table.
Collision: the probe provides an actual counterexample; D1/D2 fail. Seed: retain
the table as a presentation API while reading raw records from the guarded SDK.

### P2-G — Whole-file memory buffer with overwriting publication: REFINE

Prosecution: a large asset expands memory with no need, and replacement hides
an existing corrupt destination instead of checking it. Defense: a digest over
complete bytes is correct and simple. Collision: retain byte-derived identity,
but improve D5/D6 toward a temporary file and verified non-replacing publication.
That refinement is already present as independently evaluated P2-F.

### P2-F — Stream, verify and publish complete blobs: SURVIVE

Prosecution: a crash/cancellation could leave a partial digest filename, two
writers could race, or the SDK could choose a path from untrusted media metadata.
Defense: a private temporary file is the write target, publication occurs after
completion, `os.link` does not replace another writer's result, and existing
bytes are verified before reuse. The SDK file-object probe confirms it uses the
supplied output rather than the media filename. Collision: actual local primitive
and SDK evidence support the boundary; D3/D5/D6/D7 pass. Unsupported filesystem
operations must fail; the design does not claim arbitrary filesystem or
power-loss guarantees. All D1–D7 checked; no critical caveat remains for the
scoped local publication contract.

### P2-C — Let the future receiver hash existing filenames: KILL

Prosecution: the producer returns origin-named files rather than the explicitly
requested content-named artifacts. Defense: the receiver might already have an
object store. Collision: no receiver is supplied and D3 is missing from this
task's result. Seed: make content identity portable so a later receiver can reuse
it instead of requiring one particular storage service now.

### P3-G — Universal scanner and pluggable sinks: REFINE / DEFER

Prosecution: dates, retries, callbacks, default limits and existing output all
move together, though #6 only needs one bounded raw path. Defense: one scanner
could avoid future duplicate scan logic. Collision: the future benefit is real
but does not improve today's requested contract enough to justify D4/D6 risk.
Refinement target: prove a second consumer needs the same generalized state
machine before undertaking that refactor; preserve current public behavior.

### P3-F — Separate bounded reader on the existing guarded client: SURVIVE

Prosecution: a quota stop during media refresh or an encoding error after a
page was fetched could skip a message or become a misleading success. Defense:
only completed records enter the prefix; the cursor follows the prefix, not SDK
page consumption, and the original failure carries the partial value. The same
client factory meters hidden re-fetches. Collision: D1/D2/D4 are satisfied by
the explicit state transition; the new operation has one count/order/mode rather
than duplicating every legacy fetch option. All D1–D7 checked. Include tests for
both an empty prefix and a failure after a completed record.

### P3-C — Replace the legacy scanner's return contract: KILL

Prosecution: current callers expect DataFrames and callbacks; the requested new
batch does not require breaking them. Defense: one public format is cleaner.
Collision: aesthetic uniformity does not meet D4; a library migration would be
new work. Seed: expose the new value alongside existing calls, then evaluate
shared internals only when there is evidence for the larger refactor.

### P4-G — Add version/cursor fields only to JSON export: KILL

Prosecution: the export cannot recover omitted records or determine failed-media
progress. Defense: it is easy to ship and document. Collision: D1/D2 remain
unsatisfied; low effort is not a substitute for the requested behavior. Seed:
export a prepared batch value rather than treat formatting as preparation.

### P4-F — Additive API plus persisted replay: SURVIVE

Prosecution: a hash alone does not prevent a receiver processing a duplicate,
and callers could persist the cursor before uploading. Defense: explicit
save/load and documented acknowledge-then-advance obligations supply the
producer guarantee without inventing receiver behavior. Collision: apply the
user's repeated-*upload* example literally: upload the same saved artifact,
deduplicate by its identity, then commit its continuation. D2/D3/D7 pass;
full transaction orchestration remains outside #6. All dimensions checked.

### P4-C — Acknowledgment-aware async stream: REFINE / FUTURE

Prosecution: receiving acknowledgments, durable queue state and backpressure
are not current tgdata contracts. Defense: those controls can fit #10's worker.
Collision: viable future direction but unclear receiver ownership prevents a
present completeness verdict. Refinement target: #10 must define job ownership,
acknowledgment and persistence first; use the #6 value as its payload.

## Phase 3.5 — Assembly A1

**A1 = P1-F + P2-F + P3-F + P4-F: SURVIVE, ranked first.**

Prosecution: a valid record containing an uncompleted file, or a changed value
whose identity was computed earlier, would break the whole despite individually
plausible pieces. Defense: P2's returned reference is a completed-file boundary;
P3 appends only after it; P1 freezes canonical payload bytes; P4 replays those
bytes and leaves acknowledgment outside the producer. Collision: the interfaces
join on completion and immutable values rather than ambient mutable state.
This directly supplies the requested message/cursor/hash/replay combination.

All critical dimensions pass for the design. Success still requires the later
plan to specify field types, validation, failure results and fixtures, and the
implementation to pass those tests. This verdict does not substitute for either.

## External evidence

`../../probe_batch_seams.py` runs real installed SDK iteration/download behavior
and real local files with synthetic replies and sockets forbidden. On 1.45.0:

```text
Batch seam probes — Telethon 1.45.0
Publication: 24 competing writers, one complete digest-named file, no temporary leftovers
Raw iteration: IDs 101/102 and service action survive; presentation conversion omits senderless 101
SDK dictionary: ordinary JSON encoding rejects its datetime; an explicit wire projection is needed
SDK download: writes complete bytes to the supplied file object and returns it; media filename is unused
All pre-build seam probes passed; no live server behavior is claimed
```

Before the user's version steering, the same probe also ran on 1.33.1. That
historical observation creates no further compatibility requirement. All
subsequent work targets 1.45.0 as requested. No live Telegram read or receiver
transaction is claimed. Mechanism-independence status is **validated** for the
scoped design claims by source text and empirical artifacts; server behavior
remains explicitly unobserved.

## Phase 4 — Accumulator, coverage and convergence

The candidate evaluations above are the accumulator: five KILLs, three REFINEs
(one already embodied by P2-F, two future directions), four component SURVIVEs
and one assembly SURVIVE. Kill seeds/refinement directions are retained beside
each verdict rather than silently discarded.

Critical screening mapped the landscape. Two subsequent within-pass adversarial
iterations checked (1) prefix failure/mutation and (2) SDK/file publication
composition against the same dimensions. Both retained the same viable region;
the empirical probe narrowed uncertainty rather than adding a new architecture.
This is one outer traverse iteration, not two separate implementations. New
information decreased from architecture elimination to confirmation of mechanisms.

Coverage: all 12 generated candidates faced prosecution/defense/collision;
all four survivors and their assembly faced all seven dimensions. The alternative
regions include raw SDK export, table wrapping, API replacement, generalized
scanning and streaming acknowledgment. Remaining worker/archival regions are
outside the bounded question, not unexamined prerequisites for its answer.

**Signal: TERMINATE with A1, then its four component survivors.** The architecture
question is answered; no critical weakness requires another generation round.
Prosecution strength STRONG; landscape CHANGED during screening, then STABLE in
both follow-up iterations; clean SURVIVE exists. All nine failure modes checked,
including frame preservation and external grounding; no unresolved process flag.
Manual structural/coverage check: 8/8. **PROCEED** to Routelister.
