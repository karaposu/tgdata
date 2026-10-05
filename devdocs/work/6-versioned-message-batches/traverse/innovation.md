---
model: unknown
effort: unknown
---

# Innovation — candidates for the v1 batch producer

## User Input and seed

`_branch.md`, `sensemaking.md` SV6 and `decomposition.md` P1–P4. Seed: the
missing library contract between observed messages and safely replayable output.
Direction comes from the user's concrete messages/cursor/content-hash request
and #10's future dependency; novelty is measured within this repository.

Production-task mode with four meta-decision pieces: P1 owns representation,
P2 completion/publication, P3 progress semantics, P4 public adoption. Each
commits framing/evaluation criteria and an intervention shape, so each gets
generic, focused and contrarian variations plus shape-axis Inversion.

Inherited methodology: **Standard default**, full seven mechanisms. Alternative:
**Contrarian-rethink (Framer-weighted)** would devote more work to eliminating
the new API or moving persistence to the future worker. Run Standard default:
all four pieces still need concrete implementation choices, while the explicit
contrarian alternatives below test the inherited direction without reducing
generator coverage. No coverage reduction was requested.

## Phase 2 — Generated variations, before selection

### P1 — Representation and identity

- **P1-G, generic / Combination:** ADD-CONTENT: put the SDK's complete JSON
  message representation inside a versioned envelope with a cursor and digest.
  Combine vendor serialization with a library wrapper, maximizing immediate fields.
- **P1-F, focused / Combination + Constraint Manipulation ADD:** ADD-CONTENT:
  define a bounded, explicit JSON v1 projection and a value object that keeps
  canonical bytes. Use decimal strings for identifiers, normalized UTC dates,
  explicit nulls and content-derived batch identity. Dict access returns copies;
  reload validates schema/version/hash instead of trusting a supplied ID.
- **P1-C, contrarian / Inversion:** reverse ADD-CONTENT into
  REORGANIZE-WITHOUT-ADDING: no new value model; standardize the existing
  DataFrame export and derive the cursor from its rows. At system level the
  claim becomes “presentation already is the interchange contract”. This also
  tests the existence-axis: zero new producer representation.

### P2 — File completion and publication

- **P2-G, generic / Domain Transfer:** ADD-CONTENT: transfer an object-store
  pattern to local files, download entire assets into memory, hash them and
  publish by digest with overwrite-by-rename. Native source: content-addressed
  computing storage; different-domain analogy: a sealed parcel identified by
  its manifest. The analogy generates the completion idea, not filesystem proof.
- **P2-F, focused / Domain Transfer + Lens Shifting:** ADD-CONTENT: treat local
  output as a cache of complete immutable blobs. Stream to a private temporary
  file, hash completed bytes, publish atomically without replacing an existing
  blob, and verify any existing digest-named file before reuse. Clean temporary
  files on every exit. Return only digest/size/portable filename, no absolute root.
- **P2-C, contrarian / Inversion:** reverse ADD-CONTENT into DO-NOTHING for
  publication: retain existing `<chat>_<message>` reuse and require the future
  receiver to hash/rename it. System-level reversal: the consumer, not the
  producer, owns content identity. Identity-axis check: a file name is an origin
  pointer rather than evidence about its bytes.

### P3 — Reading and continuation

- **P3-G, generic / Extrapolation:** REPAIR the existing fetch pipeline into a
  universal scanner with pluggable DataFrame/raw sinks, anticipating many future
  formats and streaming workers. This makes one cursor implementation serve all.
- **P3-F, focused / Absence Recognition + Constraint Manipulation REMOVE:**
  ADD-CONTENT: a new bounded oldest-first reader uses the existing shared client,
  not the presentation converter. Remove the assumed obligation to download all
  media on every call: references-only is usable, and an explicit directory
  requests content files. In that mode append/advance only after publication.
  On failure attach a valid complete prefix and propagate the original exception.
- **P3-C, contrarian / Inversion:** reverse ADD-CONTENT into REPAIR of the
  existing scanner alone: change its successful output to preserve every raw
  record and return a cursor, then adapt current callers. System-level claim:
  there should be one new universal contract replacing the old one, not two APIs.
  This directly challenges the additive-compatibility constraint.

### P4 — Adoption, replay and evolution

- **P4-G, generic / Absence Recognition (patch):** ADD-CONTENT: add a version
  field/cursor to existing JSON export and explain receiver-side deduplication.
  The patch fills obvious missing fields but leaves the producing record set.
- **P4-F, focused / Lens Shifting + Absence Recognition (redesign):**
  ADD-CONTENT: expose one bounded `get_message_batch` call plus a `MessageBatch`
  value with JSON save/load. Evaluate success as reproducible *saved output*,
  not a repeat query. Document field/version rules, references versus downloaded
  media, exact-message continuation, and the caller's acknowledgment obligation.
- **P4-C, contrarian / Inversion + Extrapolation:** reverse ADD-CONTENT of a
  one-shot API into CONTRARIAN-RETHINK: make the contract an async stream with
  acknowledgments and backpressure, not a returned value. System-level inversion:
  reading and delivery progress become one protocol. The existence-axis asks
  whether an explicit batch value can disappear into the stream interface.

## Mechanism-specific coverage and additional checks

All seven mechanisms produced tested candidates above. Constraint Manipulation
has both directions: ADD strict portable scalar encoding (P1-F), REMOVE mandatory
downloads (P3-F). Absence Recognition covers the patch-level missing version/
cursor (P4-G), the redesign-level missing durable snapshot (P4-F), and what is
already present in another form: SDK iteration, after-ID reads, media downloads,
quota admission and health reporting. Those existing capabilities are reused,
not reimplemented as new transport/account features.

Inversion reached system-level statements for all pieces, with existence/identity
axes explicitly checked. P2's native computing object-store source and unrelated
parcel analogy are both present; only the former's mechanisms are implementation
candidates. Extrapolation tested multi-sink and acknowledgment-stream futures,
without assuming #10's eventual runtime must be built in #6.

## Inherited Frame Audit

The seed's central inherited commitments are “new producer value”, “complete
prefix”, “producer-owned content identity” and “additive library boundary”.
P1-C challenges existence of a new representation; P4-C challenges the one-shot
prefix/delivery separation; P2-C reverses content-identity ownership; P3-C
reverses additive compatibility. Each piece's ADD/REPAIR shape has a named
alternative. No commitment lacks an explicit challenge; audit does not fire,
no override is used. The strongest alternative, a universal scanner, stays in
the test set instead of being dismissed for touching familiar code.

## Phase 3 — Five-test log

N = novelty in this repository; S = scrutiny survival; F = fertility;
A = actionability; I = independent-mechanism support. Every variation entered
the cycle. Failures stop at their decisive test; unrun later tests are named.

| Candidate | N | S / strongest objection | F | A | I and disposition |
|---|---|---|---|---|---|
| P1-G | new envelope | FAIL: SDK field drift, byte references and repr fallback become the consumer contract | not reached | not reached | not reached; reject |
| P1-F | new explicit stable value | survives: narrower than a full archive, but covers requested fields and states omissions; validated bytes prevent mutation/ID drift | future processors can validate v1 | stdlib JSON/digests; exact fields still need plan fixtures | independent request-format requirement + actual SDK/export drift; ACTIONABLE |
| P1-C | existing representation reused | FAIL: a lost sender/row cannot be reconstructed from the export; row maximum is not scan completeness | not reached | not reached | not reached; reject |
| P2-G | new content namespace | FAIL as default: whole large files in memory and silent overwrite do not supply bounded resource use or integrity reuse | not reached | not reached | not reached; refine to P2-F |
| P2-F | new verified blob publication | survives: no cross-filesystem rename assumption when temp is in target directory; failed writes expose no final object | same bytes deduplicate across posts and batches | local primitive probe below passes; publisher implementation tests still required | byte-identity requirement + filesystem completion semantics, not analogy alone; ACTIONABLE |
| P2-C | changes ownership boundary | FAIL: #6 no longer returns the requested content-named files; old message paths do not prove current bytes | not reached | not reached | not reached; reject |
| P3-G | generalizes all readers | survives as a broader refactor, but must retest dates/callbacks/flood resumption for no required change in those APIs | supports future multiple sinks | larger than necessary for this contract | different long-term demand not yet established; DEFERRED until at least another reader needs the same scan state machine |
| P3-F | new bounded raw operation | survives: small intentional scan duplication avoids inheriting lossy presentation; shared factory still enforces quota | direct primitive for #10 | existing iterator/media primitives; prefix algorithm is bounded | raw-record need + preparation-failure boundary + existing client guard; ACTIONABLE |
| P3-C | one universal contract | FAIL for this run: existing documented DataFrame consumers would require migration unrelated to obtaining a new raw contract | not reached | not reached | not reached; reject |
| P4-G | minimal export versioning | FAIL: framing an existing incomplete row set does not answer the raw completeness and partial-cursor problem | not reached | not reached | not reached; reject |
| P4-F | new replayable API/value pair | survives: receiver must still perform dedup/ack, which is documented rather than claimed implemented | independent producer/consumer evolution | library API, local files and offline fixtures suffice | issue's repeated-upload example + separate #10 receiver scope; ACTIONABLE |
| P4-C | new acknowledgment stream | survives as future worker design; it combines backpressure with persistence | useful to #10 orchestration | requires a receiver/ack lifecycle beyond this task | worker need is real but protocol unchosen; RESEARCH FRONTIER for #10 |

### Grounding and real primitive observation

Categorical project claims were checked against `MessageEngine`, `utils`,
`TgData`, the SDK iterator/download/serialization code and #10. There is no
existing stable raw batch hidden behind the callback API; there is existing
read/resume/download machinery that the focused design consumes.

A temporary-file probe used real `fsync` plus non-replacing `os.link` publication,
with all temporary files on the destination filesystem. Exact output:

```text
Filesystem publication: 24 competing writers, one complete digest-named object, no temporary leftovers
This probes real local filesystem semantics, not a new tgdata publisher or live Telegram.
```

This establishes the local primitive, not arbitrary filesystem portability,
power-loss durability, server bytes, or correctness of unwritten publisher code.
Unsupported storage behavior must raise instead of silently downgrading atomicity.

## Assembly and axis coverage

Assemble P1-F + P2-F + P3-F + P4-F. A caller receives a producer-owned immutable
snapshot value; selected files are fully published before records advance its
cursor; serialization and reload preserve identity; the caller can persist and
resend the same output before acknowledging progress. This composition supplies
the replay/resume property that none of the separate pieces supplies alone.

Proposed concrete shape for subsequent critique: additive `get_message_batch`
with a positive bounded limit, an exclusive after-ID, and optional media directory;
`MessageBatch` provides canonical JSON, validated reload and a digest-derived
identity. Standard JSON strings carry large identifiers, while typed status
distinguishes bound reached, observed end and interruption. No wall-clock export
timestamp or absolute root enters the identity. Detailed field/type/limit choices
remain for the description/plan; every choice must have a fixture.

Axes varied: schema depth, representation mutability, publication/completion,
media mode, reader reuse versus new operation, API replacement versus addition,
and artifact replay versus acknowledgment streaming. Every committed assembly
element has a focused variation in the test log; default references-only mode
was actively generated by REMOVE, not inherited without a test. Shared-input
convergence was challenged by P1-C/P2-C/P3-C/P4-C; independent evidence includes
the issue's delivery wording, actual row omission, SDK encoding, local filesystem
probe and existing downstream scope. No surviving candidate contradicts an
assembly claim without being retested; no RE-TEST TRIGGER remains open.

## Telemetry and handoff

Generators 4/4; framers 3/3. Four meta-decision pieces, three variations each;
all 12 entered testing. Four ACTIONABLE, one DEFERRED with trigger, one RESEARCH
FRONTIER; six rejected/refined into stronger alternatives. All six survivors
completed N/S/F/A/I with their limits stated.

Per-piece logs: P1 [Combination:content, Constraint-ADD:scope,
Inversion:intervention-shape]; P2 [Domain Transfer:content, Lens Shifting:frame,
Inversion:intervention-shape]; P3 [Extrapolation:direction,
Absence Recognition:scope, Constraint-REMOVE:scope, Inversion:intervention-shape];
P4 [Absence Recognition:content, Lens Shifting:criterion,
Inversion:intervention-shape, Extrapolation:direction]. Property-(v) Inversion
compliance: satisfied for P1/P2/P3/P4. No overrides.

At least Combination, Absence Recognition, Constraint Manipulation and Domain
Transfer converge on explicit snapshot preparation, with distinct grounds.
All six failure modes checked; no remaining coverage or untested-survivor flag.
Manual required structure/coverage: 9/9. **PROCEED** to structural critique.
