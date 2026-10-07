---
model: gpt-6-astra
effort: max
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the actual local namespace/CAS/receiver composition cannot preserve the
same pending observation and independent daily/history state across real commit and
process boundaries without changing the production store/state contract.
Affordable now: yes — temporary SQLite, existing engines and local owned processes;
seconds of execution, no Telegram/account access or live allowance.

Experiment: before product edits, build the bounded example-store/receiver primitive
as a work-folder probe. Use real SQLite FULL transactions and the existing engines,
with synthetic public batch values as inputs (not fake persistence). Verify separate
namespace CAS, one winner between actual competing conditional writes, independent
daily/history rows, retained request/ref and receiver snapshot before acknowledgment.
Exit an owned child immediately after the actual receiver commit, wait for exit and
reopen. Replay must match exact canonical batch/full receipt without reader calls;
duplicate acceptance must preserve one effect and the complete observation, then ack
may advance/complete. Check missing known database refusal and post-commit close-error
reconciliation with the same primitive. Include Risk 1's selected receiver safeguard.
Cost: local temporary files/processes only; a few seconds, no credentials or network.
Must precede: step 1 under task-impl; first directly dependent example step is 3,
whose caller contract/doc claims otherwise rely on unqualified composition.
Disqualifying result: namespace interference, multiple successful conflicting claims,
missing acknowledged observation after actual commit/reopen, automatic missing-state
creation, or a required production schema/health redesign. Deprecate and stop.
Passing result: actual SQLite/process evidence preserves exact pending/receipts and
independent namespaces, refuses missing known state, reconciles committed outcomes,
and needs no change to the production lifecycle/store contract.

Result: PASS — 2026-10-07. All seven actual SQLite/namespace/receiver/process checks
passed on unchanged production code `0d6bb26`. Exact observations survive receiver
commit/reopen; one competing CAS wins; known missing state refuses; committed close
errors reconcile and cleanup preserves primary errors. No Telegram calls or product
edits. See [prebuild-results.json](prebuild-results.json).

## High-level summary

The facade design fits the tested lifecycle: persistent cached engines, typed ownership,
no outer health context and unchanged backend protocol. One Medium finding concerns
the new example receiver's exact-data promise. No High finding or meaning gap found.
The affordable real SQLite composition test belongs before implementation rather than
after the example is built. Gate C qualifies unchanged source/state internals; it does
not qualify an unbuilt facade or this new application adapter. Gate D remains later.

## Premise Inventory — ranked by waste if false

### 1. Example-owned namespace/receiver storage realizes the claimed contract

**Premise:** one physical SQLite database can host separate opaque progress namespaces,
retained application identity and full scoped receiver acceptance through the stated
crash/reopen boundary. **First dependent step:** 3 (task-impl moves its probe before 1).
**Waste if false:** example, example-specific tests and docs in steps 3–4, plus misleading
public guidance; hours rather than a new vendor capability. **Test scheduled at:**
step 3/5, with an earlier critic probe anticipated but unexecuted.
**Cheapest earlier test:** the real primitive/process experiment above, seconds.
**Coverage:** Gates B/C prove actual SQLiteSyncStore plus their selected receiver;
the old daily example proves its separate chosen receiver. Neither proves this new
namespace implementation or full-observation contract. A dict-based CAS or simulated
"receiver accepted" flag would be non-covering. Synthetic source values are valid
inputs when actual persistence is the tested component; no live-source claim follows.

### 2. Public delegation retains local engine authority and health boundaries

**Premise:** the new public methods call persistent engines with the exact owned input,
without adding a health wrapper or recreating timing/activity evidence.
**First dependent step:** public consumption/example after step 1.
**Waste if false:** facade/example tests fail before a release; no later stage may claim
public-live readiness. **Test scheduled at:** step 2, before dependent example/docs.
**Cheapest earlier test:** no actual unbuilt facade exists. Source review establishes
the existing bound callback/decorator and engine-lifetime surfaces; tests 22/25–28
and Gates A/B/C exercise those actual components. A mock facade would not cover the
new method's correctness. Existing ordering is appropriate; no extra live probe needed.

### 3. Package and backend interfaces are compatible with the additive surface

**Premise:** modules have no cycle through TgData, all reviewed input classes support
owned portable reconstruction, new constructor argument can append after sync_store,
and namespace validation remains in the codec. **First dependent step:** 1.
**Waste if false:** local import/configuration shape changes, resolved before writing.
**Test scheduled at:** source review now, import/signature tests in step 2.
**Cheapest earlier test/coverage:** direct inspection of actual module imports, value
converters, current signature and load/CAS contract confirms documentary premises.
No `collection_id` routing exists in SQLiteSyncStore; the plan correctly documents
that a cache key does not allocate a backend namespace.

## Restart Check

This continues a planned delivery, not a repair of paused #7. Established inherited
mechanisms have specific owners:

| Observed failure | Established mechanism | Design element |
|---|---|---|
| Local calls can incorrectly appear to recover source health when broadly wrapped | Existing reported decorator creates success evidence; daily tests forbid local recovery | Plain public delegates; only actual get_message_batch context, steps 1–2 |
| A reply can be lost after durable write | Actual SQLite/process evidence in B/C | Preserve existing recognition; exact receiver/restart probe before example |
| A stopped process can leave unresolved source work | Gate C owned source exit and recovery | Same engine guards, no automatic demo recovery, steps 1–3 |
| A per-message dedup index can omit a later accepted snapshot | Actual old example receiver probe in this critique | Risk 1 robust snapshot-per-receipt before demo dependence |

## Inherited Lessons

| Lesson | Step/order that satisfies it |
|---|---|
| Local work is not Telegram evidence | No outer decorator in step 1; prior-health tests in 2 before example |
| Wrapper cannot discard activity/monotonic evidence | Persistent engine cache and cross-method tests, steps 1–2 |
| Collection identity is not database namespace | Explicit configured backend; real namespace experiment before build; docs in 4 |
| Source end is not receiver acceptance | Existing engine preserved; actual receiver commit/replay probe before example |
| Hash is not run authority | Full DeliveryRef receiver key and input validation, steps 1/3 before docs |
| Error is not rollback | Actual commit/reopen probe and no automatic state reset before example |
| Retain requests before submission | Explicit application identity table and no missing-known bootstrap, step 3 |
| Examples must execute their durability claim | Experiment observes actual SQLite/process boundary, not a supplied success flag |

## Risk 1 — A receipt marker can outlive data that was never retained

**Risk**

The new example could record that it accepted a complete delivered batch while its
message table silently keeps only an earlier observation of one message. Daily and
historical deliveries can overlap. Deduplicating the visible message index is useful,
but it does not by itself preserve everything the new receipt says was accepted.
Applications copying the example could discard data and still advance their bookmark.

Step 3 specifies receipt keys plus group/message dedup but does not specify retention
of the complete canonical MessageBatch or a conflicting-observation policy. The real
`examples/daily_continuation.py::Destination.accept` uses INSERT OR IGNORE for both
markers and message rows. A local probe supplied two valid batches for the same ID
with different observations: two markers committed, one earlier message row survived,
and the later observation was absent. Copying that storage pattern alone is insufficient
for Stage 7's exact-delivery demonstration. This does not ask for edit reconciliation.

**Severity:** Medium. **Category:** Receiver contract / missing implementation detail.
**Impact:** a misleading durability example and potentially acknowledged data loss
in a caller that adopts its persistence pattern.
**NoobEng:** a unique message key suppresses repeated processing; a receipt asserts
acceptance of a particular scoped observation. Those are different keys and promises.
**Affected areas:** new offline example's receiver/schema, its tests and public guidance.

### Mitigation — Quick

Limit the prose to the synthetic fixture and assume every overlapping observation
is identical; leave the receiver as only receipt markers plus message-ID dedup.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Store each full canonical MessageBatch alongside its full scoped receipt in the same
receiver transaction as the deduplicated message index. Validate receiver destination,
chat and batch hash before acceptance. A duplicate receipt must match its stored batch
exactly; otherwise refuse. Treat the unique message table as a first-observation index,
not the sole archive. Test differing observations for the same ID and wrong scope.
**Why this is robust:** acceptance retains the precise delivered observation without
adding edits/deletions, replacing old records or a production archive abstraction.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The new exact-delivery example is the affected instance. The daily example and frozen Gate B helper have different historical receipt contracts; moving them into one framework adds extent and migration decisions outside Stage 7. This local receiver change closes the instance completely and survives later extraction.
*For future:* —

### Mitigation — Long-term

Factor a shared exact-observation receiver framework across the daily example and
backfill example, with pluggable receipt-key policies and schema migrations.
**Why this is long term effective:** one persistence implementation could serve future
examples that adopt the same complete-observation contract, preventing divergence.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Reconsider a shared helper if multiple public examples deliberately adopt the same exact-snapshot contract. Keep the present snapshot schema/transactions; historical gate instruments remain frozen. This is optional future work, not a prerequisite.

## Preconditions and scope audit

No planning/execution blocker is open. Source/account behavior is unchanged and has
prior scoped live evidence; new public/live integration remains Gate D after Stage 8.
No new schema in tgdata_sync_state, raw reader, budget, health ownership, package
release or distributed orchestration is needed. One cached engine per caller-used
collection consumes memory proportional to those IDs; no automatic eviction may
erase temporal evidence. The private helper's typed reconstruction must precede
cache access so malformed addresses do not become arbitrary attribute/key failures.
