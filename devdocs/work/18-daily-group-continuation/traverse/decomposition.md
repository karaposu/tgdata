---
model: gpt-6-astra
effort: max
---

# Decomposition — daily continuation

## User Input
_branch.md plus the saved SV6 in sensemaking.md: durable prepared output and an
accepted position, canonical source identity, explicit enrollment/acknowledgment,
one reader, existing batch/SDK contracts, optional media and interrupted prefixes.

## 1. Coupling Map

Strong cluster A: source binding, initial position, pending batch identity and
cursor validation. Changing the bound group changes which cursor/batch is valid.

Strong cluster B: persistent accepted position, pending payload and last accepted
delivery identity. Removing pending output and changing progress are one commit;
splitting them produces a crash gap.

Strong cluster C: fetch outcome, completed partial prefix and artifact availability.
A prefix cannot be called replayable until its exact bytes and required blobs are
retained; a failure can coexist with deliverable data.

Moderate connections: A's validated state feeds B; the existing MessageBatch value
crosses C→B; prepared/acknowledged results cross the library/caller boundary. The
consumer's business transaction is external and connected only by acknowledgment.

Weak connections: scheduler clock, UI plan, account inventory and later backfill.
None must be pulled into A/B/C to make one-reader daily progress coherent.

## 2. Top-down Boundaries

Keep source/state invariants together as Q1. Keep all durable transition operations
and backend validation together as Q2. Keep the read/partial/artifact composition
together as Q3. Isolate caller API and delivery obligation in Q4.

The important cut is between prepared output and caller acceptance. The store owns
their atomic transition but cannot own the caller's external destination. The
network is outside every store transaction. Tests cross each interface rather than
becoming a fifth owner of runtime decisions.

## 3. Bottom-up Validation

Atoms: canonical marked peer ID; exclusive initial/current message ID; immutable
MessageBatch JSON; pending batch ID; acknowledgment identity; complete file digest;
one local database commit; original read exception/cancellation.

Identity and cursor validation group under Q1. The inseparable pending removal and
cursor advance group under Q2. Complete prefix plus original read error group under
Q3; preserving both is a defined interface obligation. Receiver acceptance remains
an external assertion exposed through Q4. Top-down/bottom-up agreement: HIGH for
all four boundaries. No atom is split across two independent commit owners.

## 4. Question Tree

### Q1 — What identifies one continuation and a valid state?
Verification criteria:
- [ ] A group/collection has an immutable canonical source binding and explicit
  initial position; reopening cannot reset or silently rebind it.
- [ ] A state distinguishes ready/pending, validates pending group/start/end and
  preserves the existing MessageBatch format.
- [ ] Unknown, corrupt and missing records have explicit meanings; source changes
  are detectable rather than relabeled.
- [ ] Media policy and any replay location are inspectable and stable while pending.

### Q2 — How does a backend make preparation and acceptance durable?
Verification criteria:
- [ ] Store operations have exact atomicity, failure and persistence obligations;
  another backend can implement them without reimplementing Telegram behavior.
- [ ] Preparation retains exact bytes without advancing; acknowledgment matches
  pending identity, advances atomically and handles a repeated acknowledgment.
- [ ] Store failures never look like absent/new state; old acknowledgments never
  clear newer pending work. Crash/reopen probes verify the real backend.
- [ ] No transaction/lock spans a Telegram or receiver await. One-reader scope is
  explicit; distributed leases/ownership takeover are not smuggled in.

### Q3 — How are existing reads composed into restartable work?
Verification criteria:
- [ ] Pending work replays without opening a Telegram client or spending read budget.
- [ ] Ready work invokes the existing bounded batch path from its accepted cursor.
- [ ] Valid nonempty interrupted prefixes are retained while the read failure stays
  visible. Failure to persist a prefix has an explicit non-acknowledgeable outcome.
- [ ] Empty results, cancellation, unavailable files and returned-source mismatch
  cannot advance or overwrite progress; media checks preserve saved bytes.

### Q4 — How does a caller operate the feature correctly?
Verification criteria:
- [ ] Enrollment, one-batch preparation/replay, acknowledgment and status are usable
  through a small API with accurate examples.
- [ ] The destination deduplicates accepted batch IDs and overlapping message IDs;
  its durable acceptance occurs before acknowledgment.
- [ ] Daily scheduling/pacing remain caller-owned; missed runs catch up from the
  checkpoint, with no date cutoff or automatic joining.
- [ ] Public tests exercise the actual SDK/SQLite composition, failure windows,
  process restarts and existing compatibility. Backfill remains visibly pending.

## 5. Interface Map

| Source → Target | What flows | Assumptions checked |
|---|---|---|
| Caller → Q1 | collection/group reference and initial position | explicit enrollment; trusted position only because caller chooses it |
| Q1 → Q2 | validated state and transition preconditions | scalar IDs are exact; missing differs from corrupt |
| Q2 → Q3 | current source/cursor or retained pending observation | load does not swallow failures; no network needed for replay |
| Existing batch API → Q3 | complete batch or original error with partial batch | after_id is exclusive; prefix is fully prepared, not necessarily whole request |
| Q3 → Q2 | candidate observation and expected prior state | never commit a different group's records; persisted before exposure |
| Q3 → Caller | durable pending value or visible failure | requested media remains available; failure does not auto-ack |
| Caller → Q2 via Q4 | exact acknowledgment identity | receiver already committed effects/dedup; repeated acknowledgment is harmless |
| Q2 → Q4 | accepted/pending status | derived from one consistent state, not independently updated flags |
| Scheduler → Q4 | invocation time and batch limit | no concurrent owner; respecting waits/budgets is caller policy |

The assumed single reader is documented as an operational precondition, not proof
that individual updates can be non-atomic. Sequential machine changes require the
same state and pending artifacts; this phase does not build a transfer service.

## 6. Dependency Order

Define Q1's identity/state interface first. Q2 and Q3 can be reasoned about against
that interface, but Q3's persistence promises must wait for Q2's verified commit
behavior. Q4 exposes those established contracts and supplies the integration tests.
No circular ownership: the store never calls Telegram, and the reader never decides
whether external data was accepted. Documentation/verification span all four pieces.

## 7. Self-Evaluation

Independence PASS: each question is answerable through named interfaces.
Completeness PASS: enrollment, persistence, replay, errors, artifacts, acceptance,
compatibility and exclusions all have an owner.
Reassembly PASS: ready → prepare → pending → deliver → acknowledge → ready covers
daily resumption; Q1/Q2 explicitly determine state validity and pending existence.
Tractability PASS: four focused questions, no full scheduler or health redesign.
Interface clarity PASS: data and assumptions both enumerated.
Balance PASS: state/storage/read composition carry the work; caller surface is
smaller but independently necessary. No one opaque piece hides all complexity.
Confidence PASS: both boundary passes agree. All seven failure modes checked.

Telemetry: four pieces, nine interfaces, one dependency order, seven evaluation
dimensions passed. Stop decomposition: each piece is directly verifiable and
further splitting would divide atomic transition obligations.
