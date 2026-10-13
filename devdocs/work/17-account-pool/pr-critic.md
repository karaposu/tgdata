---
model: gpt-6-astra
effort: max
status: PASS_OFFLINE_LIVE_E1_PENDING
round: 3
plan_revision: 7
---
**Verdict: REORDER — TEST BEFORE BUILD**

Falsifier: ordinary application concurrency leaves a capture with the wrong data or
owner, makes shutdown wait for unrelated application/progress work, or changes actual
permission/charge/receipt facts when keeping data available.
Affordable now: yes — fresh actual SDK/SQLite/ReadBudget composition, local seconds,
no live account, network or money. The experiment below was executed before acceptance.

Experiment: run the implemented four public read/prepare paths under outer-shield
cancellation, overlapping groups' publication/source/close, application continuation
inside a foreign pool, post-source local failures and second-account admission/identity
failures. Record data, signal, lifetime and authoritative stores separately.
Cost:1.316s for the complete bounded probe process, plus local probe preparation.
Must precede: PR acceptance. In this implemented-diff review this is a soundness gate,
not a direction to rebuild the already-qualified implementation or authorization to patch.
Disqualifying result: lost/misattributed complete data, incorrect capture finality,
unrelated application work joined/stopped, early cleanup release, invented receipt,
unsafe source retry, lost wait or refunded charge.
Passing result: the exact owned span ends before close returns, independent public
publication keeps its own lifetime, caller data survives, and actual writes/charges
continue to govern permission and acknowledgment.
Result: **PASS —5/5 fresh groups,26 distinct histories, one complete attempt.** No
watchdog, failed assertion, probe correction or product edit. This affordable gate is
satisfied; no plan reorder or implementation change remains from this review.

**PR decision: PASS for the selected offline scope —0 High,0 Medium,0 Low.** Under
CONTRIBUTING §7.3 the fresh review does not reject this product. This is round3, but
there remain exactly **two historical rejected PR rounds**. No third rejection,
re-plan or deprecation is triggered. Live E1 remains pending; no merge authorization.

## High-level summary and subject

Reviewed the entire23-file product diff dev2ddb852...007c2e4 together with folded plan7,
description5, current plan critic/P0, prior failure history and current-dev consumers.
Review head3f890cd differs from the product only in work evidence. The same warmed
session read full relevant implementations, tests, docs and example, without delegation.
Prompt3f890cd follows merge check001d920. Current dev is unchanged; Astra/max meets §9.
The old round2 critique and prompt are preserved with _r2 suffixes; critic.md is untouched.

The new design addresses the demonstrated ownership problem. A caller retains one
explicit data destination before invoking the library. A separate private record
represents completion of the source/account span. Neither relies on the identity of
a cancellation exception or the lifetime of the caller's entire Task. Public progress
preparation owns its later publication and finalizes its own capture when it ends.

The fresh probes challenge those boundaries rather than just rerunning the qualified
examples. They passed with actual Telethon1.45 pagination/native disconnect, real SQLite
transactions/ReadBudget and the real batch/progress engines. Synthetic replies replace
only Telegram traffic; fault wrappers delay/fail real boundaries. No helper supplies a
batch, receipt, permission or completion result to make the ownership behavior pass.

Existing750 executed offline groups+3 demos remain applicable: all88 tested Python
hashes match, compilation/grammar pass, and product hashes remain unchanged during
fresh probes. Three explicit live skips are excluded. Python3.11.10 executed;3.7 grammar
is not native3.7 qualification. Offline tests do not establish actual two-account access,
proxy behavior or equal visible history.

## Premise Inventory — ranked by waste if false

### P1 — One explicit recipient survives normal application async composition

**First dependent step:**1, then3/4. **Waste if false:** capture/transport/API migration
and the central data-availability claim. **Test scheduled:** full P0 before production,
then permanent40 and this fresh PR gate. **Cheapest earlier test:** actual first page,
held next wire response and cancelled shield waiter; four public modes, seconds.
**Coverage:** fresh probe observes100 records while running and101 on successful final
return after the outer waiter is cancelled. Inner cancellation requests remain0; old
snapshot stays100/interrupted; final source owner111 and charge101. P0/permanent40 also
cover genuine reader cancellation, late waiters, gather/wait_for and single-use binding.
Mock result handles or returning a prepared batch would be non-covering; neither is used.

### P2 — Owned invocation completion differs from public/application lifetime

**First dependent step:**2. **Waste if false:** shutdown coordination and guarantees
claimed by1/4. **Test scheduled:** P0 before production and application-continuation
permanent40; fresh foreign-pool/overlapping-group histories before PR acceptance.
**Cheapest earlier test:** let the same application Task enter a second real pool
while closing the first; separately hold one group's progress CAS while reading another.
**Coverage:** both normal and cancelled first reads allow foreign-pool work to finish
without another cancellation. Six overlap histories close actual clients while groupA
publication remains running and groupB's source is cancelled with100 records retained.
The stale private completion address is harmless. Whole-Task joins are non-covering;
the probe observes actual task/client state and later independent completion.

### P3 — Data retention does not acquire durable permission or receipt authority

**First dependent steps:**3/4. **Waste if false:** safe failover and daily/backfill
integration despite correct in-memory data. **Test scheduled:** combined P0, preserved
before/after-write controls in39/40, and fresh independent publication outcomes.
**Cheapest earlier test:** actual CAS success/failure/commit during cancellation while
another real source is stopped; seconds. **Coverage:** groupA/account111 keeps1 record,
charge1 and settled account permission. GroupB/account222 keeps100, charge200 and an
unresolved attempt. Publication success/late commit has real pending; failed publication
has none. Only stored replay is acknowledged, locally after close. The media-loss/clock
cases retain a record without inventing pending or advancing the historical cursor.
Storage-cancellation fixtures delegate actual SQLite; manufactured receipts would be
non-covering. No distributed or process-crash durability is inferred from these tests.

### P4 — Attempt metadata belongs to actual observed source work

**First dependent step:**1, then3/4; current plan critic's selected robust correction.
**Waste if false:** consumers see a different attempt's error or account beside data.
**Test scheduled:** P0/permanent40 before implementation; fresh12 refusal histories.
**Cheapest earlier test:** first account returns a real FloodWait, second admission
fails before/after actual commit or real identity verification refuses. **Coverage:**
no retained batch means no public account_id. A failed second admission preserves the
latest actual source failure (FloodWait) separately from public PoolStorageError; that
source never started. Definite admission followed by wrong identity records PoolIdentityError
as the new source failure. The second account sends0 history reads and consumes0 quota.
The first account's7200-second wait persists. Existing success/held-prefix controls
also cover metadata after second-account data actually attaches.

### P5 — Shared consumers and bounded retention keep their prior contracts

**First dependent steps:**3–5. **Waste if false:** ordinary TgData/worker or persistent
progress behavior, and unbounded library retention. **Test scheduled:** full P0 and
actual-branch27-suite verification before renewed review. **Cheapest earlier tests:**
shared optional-argument absence and worker/process suites, already executed with actual
components. **Coverage:** fifteen adjacent modules unchanged, ten facade method bodies/
signatures equal to dev,88 tested hashes match; no new shared schema. Final capture
contains one immutable batch and bounded type facts, not exception/task graphs.
Existing10000-message limits do not establish a universal byte bound; docs say so.
Repeated snapshots retain caller-owned copies, with cost paid on access/finalization,
not one whole-prefix copy per appended record. No new measured performance failure.

### P6 — Real service and native runtime qualification

**First dependent step:**7/E1 for real two-account deployment evidence; native3.7
compatibility is explicitly unclaimed. **Waste if false:** operational readiness claims,
not the local ownership mechanism. **Test scheduled:** bounded live step7 once approved
resources exist. **Cheapest earlier test:** two approved authenticated accounts with
shared readable group/proxies and existing allowance; those resources remain unavailable.
**Coverage:** none for those live facts. Synthetic replies and grammar checks are
**non-covering** for real service visibility/proxies/native3.7. Carry the execution
precondition unchanged; do not manufacture an equivalent offline pass.

## Restart Check

| Observed failure | Established mechanism | Current design and evidence |
|---|---|---|
| Reuse during cancelled native retirement | SDK disconnect outlived its public waiter | Retained native retirement/quarantine; permanent31/39 and fresh actual close |
| Repeated stop released source work | Interruptible join ended before child | Owned child outcome/retained join; permanent31/39/40, fresh source close |
| Observer interruption hid source outcome | Composite task status replaced body outcome | Explicit body holder before monitor exit; retained source capture; permanent controls |
| Observer shutdown formed dependency cycle | Application callback depended on own read/close | Callbacks removed; passive observations; no application execution in source reporting |
| Draining during close masked cancellation | Busy gate on local observation | Synchronous all-state drain unchanged; permanent39 |
| Provider-owned cancellation hid100 records | Component interruption treated as caller stop | Owned provider boundary and retained data; before/after actual writes in39/40 |
| Status provider performed account control | Busy check covered source only | Expiring pool-specific scope checked before mutation;45 permanent refusal cases |
| Close consumed cancellation payload | Internal await retrieved public Task exception | Close awaits private normal completion at account_pool.py:653; capture is separate |
| Wrappers lost payload without close | Runtime replaced cancellation exception | Required public capture; permanent wrapper/late-waiter cases plus fresh outer-stop control |
| Close waited for application continuation | Caller Task lifetime exceeded invocation | _operation releases slot/completes record at239–241; fresh foreign-pool continuation passes |
| Progress publication outlived source closure | Separate public/source ownership spans | Outer prepare finalizes capture; six fresh overlapping-group histories preserve both owners |

No cited failure is left without an addressing mechanism. The upstream return corrected
the earlier recommendation to rely only on a non-consuming whole-Task wait: independent
data ownership and invocation completion were both necessary. The resulting two owners
serve different observed spans; no global supervisor/result registry was added.

## Inherited Lessons

- Task status is not source outcome: early source recording is implemented; full P0
  precedes step3, and permanent monitor/store cases observe actual completed data.
- Task lifetime is not library lifetime: P0 application continuation preceded step2;
  fresh normal/cancelled foreign-pool continuation confirms the narrower completion.
- Cancellation is not rollback: P0 real pre/post CAS preceded step4; fresh cancellation
  finalization commits pending while the public call still ends cancelled.
- Available data is not a receipt: P0/40 reject interrupted hashes as acknowledgments;
  fresh local replay/ack and post-source failures keep progress authoritative.
- More passing internal examples do not prove public delivery: full public capture
  composition was tested before production, and26 new consumer histories ran before
  accepting this PR. No inference from test count alone.
- Context ancestry cannot detect arbitrary external dependency graphs: callback removal,
  I/O-only provider contract and bounded same-pool refusal remain explicit, not a claim
  of general cycle detection. No global abstraction is justified by these results.

## Fresh behavioral observations

Command: `python devdocs/work/17-account-pool/probes/review3/run.py`.
One process,90-second parent watchdog; per-group25-second bounds; no watchdog fired.
Product hashes before/after match the merge audit. Exact probe and runner hashes are in
[attempt1](evidence/review3/pr-attempt-1.json); [raw output](evidence/review3/pr-attempt-1.txt).
The exact tested probe is also preserved beside the output.

Selected observations, condensed from that output:

```text
shield/raw: outer_cancelled=true, inner_cancel_requests=0, early_records=100, final_records=101, charge=101
publication/backfill/cancel_late_commit: first_owner=111, second_owner=222, charges=[1,200], pending_committed=true, first_final=cancelled
foreign continuation: first_cancelled=true, caller_requests=1, foreign_read_survived=true, first_records=100, second_records=1
post-source clock: error=BackfillClockError, retained=1, charge=1, group_attempt_unresolved=true, no_false_health=true
summary: passed=5, total=5, histories=26
```

Counts are5 new groups/26 histories, not26 additional full regression suites. Source
captures are observed while calls are running and after finalization; old values remain
unchanged. Native retirement and SQLite writes actually run. Intentional later media
loss is detected as local; retaining its message/metadata does not restore a missing
artifact or turn the capture into blob storage.

## Findings and Phase3

**No High, Medium or Low finding established.** The complete diff, docs and reachable
consumer paths do not reveal another actionable defect within the declared contract,
and the new affordable falsifiers passed. No speculative/private-state-mutation finding
or cosmetic noise is added to force another revision. Phase3 has no mitigation boxes
to select; plan7 and the plan critic remain unchanged. This is bounded evidence, not a
claim of universal safety or live readiness.

## Preconditions and procedural result

E1 remains OPEN: two approved logged-in accounts, shared readable group, existing
bounded allowance. No live call/login/join/reset or merge occurred. PR26 remains draft
while this live qualification is pending. Any later merge needs the user's go-ahead,
excludes work/inquiry/archaeology and preserves the feature branch archive.

Commit/post this critique on PR26; mark issue pipeline6/7 complete with the offline
scope and E1 explicit. The two rejected historical rounds and earlier failed design
prebuild remain evidence; this passing round does not erase them. No product code was
changed by this review. Main checkout, duncan and unrelated work remain untouched.
