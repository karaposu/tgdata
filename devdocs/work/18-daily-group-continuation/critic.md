---
model: gpt-6-astra
effort: max
---

**Verdict: IMPLEMENT AS WRITTEN.**

Falsifier: actual SQLite process-exit/conditional-write behavior or existing batch
replay must invalidate the proposed pending/ack boundary; a pending downloaded
observation must not require re-fetching merely because its local root changed.
Affordable now: yes — offline component probes, executed before this verdict;
the observations passed. No affordable unrun prerequisite is scheduled after
dependent implementation. New-runtime tests still belong to implementation.

## High-level summary

Reviewed plan.md revision1 at b403ffd, desc.md and the actual merged facade,
batch/value/files, storage/budget/lifecycle and test interfaces. The design is an
additive continuation layer with an explicit receiver boundary; it neither rebuilds
the reader nor imports the paused #7 health changes. No High, Medium or Low finding
was established against the plan. No runtime code was written during this review.

The six steps specify the critical transition invariants, exact store semantics,
source/cursor validation, prefix/error precedence, optional artifact replay and
compatibility coverage. The single-reader limit removes scheduling coordination,
while conditional replacement still rejects stale writes.

## Premise Inventory — ranked by waste if false

1. **Premise:** atomic whole-state persistence can leave either old pending state
   or fully acknowledged state after process termination. **First dependent step:**1.
   **Waste if false:** backend/state/ack design and downstream engine/tests.
   **Test scheduled:** pre-plan probe, then new suite step4.
   **Cheapest earlier test:** actual SQLite transaction followed by subprocess exit
   before/after commit; milliseconds. **Coverage:** probe_components.py passed both
   cases and a failed exact-value replacement. This is real SQLite/filesystem
   behavior, not a fake backend supplying the desired outcome. Power-loss/storage
   hardware guarantees remain those of SQLite and the deployment filesystem.
2. **Premise:** an existing prepared observation can replay exactly from persisted
   JSON, including downloaded blobs relocated to another root. **First dependent
   step:**1/2. **Waste if false:** pending format and retry architecture.
   **Test scheduled:** prior tests19, component probe, plan_probes.py, step4.
   **Cheapest earlier test:** prepare a real SDK batch, round-trip its nested JSON,
   copy its blob, run the real verifier; under a second. **Coverage:** exact bytes
   and digest survive; same-size corruption is refused without another request.
3. **Premise:** quota/read failures expose a complete prefix through existing batch
   semantics. **First dependent step:**2. **Waste if false:** partial publication
   and caller recovery contract. **Test scheduled:** pre-plan actual SDK/budget
   probe and step4. **Cheapest earlier test:** existing public budget-prefix test.
   **Coverage:** real iterator/guard/SQLite budget exercised with scripted Telegram
   replies. NON-COVERING for live Telegram visibility, covering for local composition.
4. **Premise:** cancellation or a failed response from an async store can follow a
   committed write. **First dependent step:**2. **Waste if false/ignored:** error
   recovery might discard committed state or retry unsafely.
   **Test scheduled:** plan_probes.py before implementation, step4 after build.
   **Cheapest earlier test:** real SQLite commit in an async operation then cancel
   before it returns. **Coverage:** new value remains; cancellation propagates.
   Plan2 never assumes rollback and always reloads authoritative state on retry.
5. **Premise:** the caller acknowledges only durable destination acceptance and
   deduplicates repeated effects. **First dependent step:** public integration,
   not internal store construction. **Waste if false:** consumer delivery semantics.
   **Test scheduled:** local receiver example/test at steps4–5.
   **Cheapest earlier test:** existing lost-ack receiver stand-in demonstrates the
   protocol; actual deployed destination is not available. **Coverage:** NON-COVERING
   for the user's deployment, explicitly an application obligation. No automatic
   exactly-once promise is made and deployment is outside this delivery.

No inherited planning/execution blocker was open. The active model/effort evidence
is recorded in triage.md, with Astra/max kept exact rather than called xhigh.

## Restart Check and inherited lessons

This is not a re-plan after rejected #18 implementation. Relevant lessons from
earlier work were tested against the new boundary:

- Local failures inheriting old RPC context: SyncError and backend conversion
  explicitly suppress unrelated context; replay/store work is outside _reported.
  Existing batch_files local-I/O helpers are reused, not replaced.
- Cleanup replacing a chosen error: step1 specifies rollback/close precedence;
  no artifact deletion occurs at ack. Saving a partial batch is integral preparation,
  so a failed save is separately reported while read_error preserves the original.
- Fresh event identity disagreeing with health summary in #7: this feature neither
  owns fresh account labels nor changes health storage. Canonical group identity
  is checked directly against the batch. Account routing remains excluded.
- Concurrency fixtures that do not overlap: step4 explicitly holds the actual SDK
  request pending while the duplicate operation is attempted.

## Boundary audit

Enrollment refuses implicit current-head/24h policies and resets. Exact source,
cursor and mode checks precede pending publication. State's strictly advancing
acknowledged cursor, retained last ack and absent reset operation prevent a supported
ready→pending→ready cycle from recreating an old expected state with different
meaning. Duplicate latest ack is a no-op even when newer pending exists; older IDs
raise, which is harmless to stored progress rather than universal acknowledgment
history retention.

Pending replay loads validated bytes before network use. Requested media has an
independent regular-file/hash/size check. A missing file cannot be repaired by a
new fetch because that would replace the observation; the plan correctly raises.

The reference store's normal operations open existing DB mode=rw and check schema.
Initialization distinguishes fresh tables from partial schema. A compare-and-swap
failure has no successful pending receipt; commit-then-error is recovered by load,
not by a compensating delete. Database transactions never hold across awaits.

No-store construction and existing public signatures retain their defaults. Adding
sync_store at the end is backward-compatible; new methods delegate actual reads
to get_message_batch. Python3.7 syntax and package export/import checks are explicit.

The existing SDK's broader retry/error-classification limitations are not claimed
fixed. This layer preserves the exception exposed by the current batch reader and
does not turn a failure into an acknowledgment. A common resolver/health migration
would be separate work; it is not a hidden requirement for this progress contract.

## Probe output

```text
PASS cancellation after commit does not imply rollback
PASS real downloaded batch replays from relocated verified blob
PASS same-size corrupt blob refused without Telegram
```

These extend the seven pre-plan component observations. New implementation tests
must still establish the engine/backend contract through real code; passing these
probes does not substitute for step4 or the later fresh PR critique.

## Phase3 selection audit

No findings require mitigation tiers or selection. No selected proposal exists to
fold. Under task-impl, proceed directly to implementation of revision1. The first
delivery leaves #18 open for backfill and leaves #7, duncan and dev unchanged.
