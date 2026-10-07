---
model: gpt-6-astra
effort: max
---
# Implementation plan — #17 existing-access account pool

**Critic folded:** 2026-10-08 — 2 selected robust mitigations (4 steps changed,0 added). Formal pre-build experiment PASS; see critic.md.

Revision2. Input: `desc.md` at1254253; design: `traverse/finding.md` atd1daa84.
Base: dev95ed4c7. No rejected PR critic exists for this task.

### What is the task

Implement a distinct-account reader that chooses eligible existing accounts and
fails over after bounded, quiescent source failures. Preserve actual identity,
admission-time allowance, completed observations and existing acknowledged progress.
Joining remains excluded and #7 stays paused.

### Huge Hard Blockers

#### Planning Blockers

None identified. Identity, SDK exception behavior, timeout-prefix transfer and CAS
admission primitives were read/probed in traverse. Design assumes one owning
process/event loop and trustworthy UTC; these are explicit deployment constraints,
not substituted evidence of multi-process safety.

#### Execution Blockers

**E1 — OPEN; inherited from desc.md.** Two distinct already-authenticated accounts,
their approved local configurations, a shared readable group and a bounded shared
allowance must be supplied/confirmed by the maintainer. **Blocks step9 only.**
User confirmed one account for now and offline-first work; do not inspect arbitrary credentials or
reset prior test allowances to manufacture the gate. Code/tests/docs proceed.

### How this implementation moves toward desired state

An owned source adapter binds the actual client to an expected account. A durable
pool document grants source-attempt permission and remembers restrictions. A small
router applies selection and stopping rules. Existing raw batches and progress
engines carry data and acknowledgments unchanged. Actual SDK/SQLite tests verify
their composition, then a separate live gate qualifies real configured accounts.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Define values, errors and durable pool state | Strict public inputs and opaque CAS state/store |
| 2 | Build the owned account source | Fresh identity, controlled requests, bounded resolution and timeout-prefix seam |
| 3 | Route and settle bounded reads | Drain/spread, explicit refusal, durable attempts and prefix preservation |
| 4 | Expose status, repair/recovery and shutdown | Safe administrative lifecycle without hidden login |
| 5 | Share existing daily/backfill facade | AccountPool progress methods with source-free replay/ack |
| 6 | Exercise actual composed failures | Offline test31 covering ownership, persistence, routing and delivery |
| 7 | Document and demonstrate use | README/docs and a bounded offline example |
| 8 | Verify and commit | Product commit, separate work notes, truthful issue status |
| 9 | Qualify live two-account operation | Bounded real gate, conditional on E1 |

## Contract fixed by this plan

`PoolAccount(account_id, config_path, *, session_store=None, label=None)` and
`PoolGroup(chat_id, reference=None)` are immutable validated inventory values.
Credentials/config paths are excluded from repr/status/error messages. Account IDs
positive; group IDs canonical negative; bools/duplicates/ref redirects refuse.
PoolGroup reference is an optional username/link or canonical integer resolution
hint; returned entity must match chat_id. No invite join or unbounded dialog fallback.

`PoolPolicy(strategy='drain', attempt_timeout=30, max_attempts=3,
transient_retry_seconds=30, access_retry_seconds=300, min_warmup_days=0)` is immutable.
Positive finite timeout/retry delays; positive attempt cap; nonnegative integer
warm-up days. Drain uses inventory order; spread greatest current remaining budget,
then inventory order. No hidden affinity or special zero-budget meaning.

`AccountPool(accounts, groups, *, read_budget, state_store, policy=None,
health_callback=None, sync_store=None, backfill_store=None)` is side-effect-free
with respect to credentials/network. ReadBudget and durable state backend required.
Only Telethon1.45.0 is qualified for this opt-in adapter; other versions refuse the
pool path explicitly, leaving ordinary TgData compatibility unchanged.

Source API: `read(chat_id, *, after_id=0, limit=200, download_media_to=None,
start_date=None, end_date=None)` returns immutable PoolReadResult containing the
MessageBatch, verified account ID and safe attempt metadata. `get_message_batch`
has the existing reader signature and returns only its batch for engine composition.
Ordinary source errors remain the same object/type; attach safe pool attribution
without replacing partial_result. PoolTimeoutError is local and carries a prefix.

Public local errors derive PoolError, carry partial_result=None initially and
suppress incidental exception context. Include configuration, state/storage,
conflict/busy, closed, identity, timeout and unavailable variants as needed by the
named behaviors. PoolUnavailable exposes per-account reasons, attempt metadata and
conditional retry_after, never a fabricated empty batch. Do not persist raw messages
or source exception text. Pool storage failures may expose read_error separately.

### Persistent state and source order

One opaque versioned document, discriminator `tgdata-account-pool`, contains
observed_at and account rows: account ID, active attempt{id,chat_id/kind,admitted_at},
repair reason, account not_before, per-group denial deadlines/reasons, latest error
type, latest recovery recognition. Strict decoder rejects unknown versions/shapes,
invalid IDs/times and contradictory tokens. No quota, credential, message or cursor.
Use canonical JSON, string IDs and finite bounded UTC values. Known rows survive
inventory changes; initialize adds but never resets them.

Backend: async load()->str|None and compare_and_swap(expected,data)->bool.
SQLiteAccountPoolStore composes SQLiteSyncStore using one private reserved slot in
a dedicated file. Pool document discrimination refuses accidental schema sharing.
`create=False` opens known files without provisioning; backend errors become local
PoolStorageError with safe type-only text. Custom backends need authoritative CAS.

`initialize()` is explicit first provisioning/account enrollment; ordinary read,
status and recovery refuse absence. One active source/mutation operation at a time;
overlap fails busy instead of queueing. Read-only pool status may observe an active
token. Pending progress replay/ack do not enter the pool operation guard.

Order for each attempted account: validate inputs/state → check eligibility and
ledger status → source preflight with no network → CAS fresh attempt token → require
definite True → run controlled source child → await its end → CAS exact-token outcome.
No source after ambiguous admission, no write retry that grants new permission.
CAS conflicts/state outages stop the call. Settling a failure updates its scoped
restriction and clears active atomically. Settlement cannot silently erase stronger
known prohibitions. If settlement fails, carry a completed interrupted prefix into
the local error and keep the source error separately; never fail over in that call.

| Outcome | Stored effect | Router behavior |
|---|---|---|
| Success | Retire token; no invented health recovery for other groups | Return observation, including genuine account-visible empty/end |
| Flood wait | Account deadline at least observed wait; preserve any longer existing bound | Try another candidate only with no prefix |
| Ban/logout/restriction | Account repair flag | Same no-prefix rule |
| Actual group denial or unresolved account-local entity | Group-specific retry deadline | Same no-prefix rule; resolution failure is not a fake Telegram event |
| Transport/server error or owned timeout | Account transient deadline | Same no-prefix rule |
| ReadBudgetExceeded | Retire token; quota authority remains ledger | Try another only with no prefix |
| Identity mismatch | Account repair flag | Local configuration/repair stop; no history for wrong ID |
| Local input/media/store/unknown failure | Retire when possible; no Telegram restriction invented | Re-raise; never try another account |
| Caller cancellation | Leave token unresolved | Re-raise; no next account |

HealthMonitor is private per owned slot, with verified user_id or None, and observes
only the source child. Durable eligibility never trusts legacy snapshots or general
health recovery. Local state/replay errors sit outside health contexts. Request
waits are conservatively account-wide for this delivery. No raw credential logging.

## Step 1 — Public values and durable state

### Proposed changes

Add `tgdata/account_pool.py` public immutable values/errors and
`tgdata/pool_state.py` strict codec/async storage adapter. Keep routing absent until
its source contract exists. Validate detached snapshots; reject bool-as-ID and
nonfinite times. Add explicit initial/enrollment state creation without overwriting
known rows. Budget stays the exact existing ReadBudget object, never configured by
the pool. UTC regression refuses; same-process monotonic lower bounds supplement
persisted wait deadlines. No network/config read in value or state-only operations.

### Output

Importable validated values and durable-state primitives, with safe error taxonomy.
### Safe in nature
True — additive modules; no existing call path changed.
### Peripheral concepts
SQLiteSyncStore CAS, canonical JSON, ReadBudget, UTC and monotonic timing.
### Hardness Lvl
4

## Step 2 — Owned source and exact client behavior [folded: Risk1, robust]

### Proposed changes

Add private `tgdata/pool_source.py`. Reuse ConnectionEngine._new_client via a private
`_client_options()` hook defaulting to {}, preserving all ordinary callers. Owned
policy supplies request_retries=0, raise_last_call_error=True, flood_sleep_threshold=0,
connection_retries=0, auto_reconnect=False and receive_updates=False. Its session
path connects directly, verifies GetState and fresh get_me, never invokes the
ordinary sleep/login path. Client ownership exclusive; one client per account.

Bind a ledger adapter that rejects a different fresh account at status/reservation
and reapplies minimum warm-up eligibility at send; all actual accounting delegates
to the existing ledger. Do not bill metadata or alter failed-reservation retention.
Preflight validates inventory config/session keys and known auth-key fingerprints
without logging them; fresh identity still detects distinct keys for the same user.

BatchEngine receives private optional resolver and retain-cancelled-prefix hooks,
defaulting to unchanged legacy behavior. Pool resolver calls bounded get_entity on
the registered hint, checks canonical group before iteration, and never enumerates
dialogs. Enable cancellation prefix only for pool-owned readers. Timer wrapper uses
wait_for and transfers the completed prefix from the cancelled child's cause; plain
external cancellation is never converted. Retain the body's completed batch or original
error before HealthMonitor can await observers. If the internal timer expires during
observer work, await child termination then preserve that already-complete outcome
(including the real wait), rather than replacing it with PoolTimeoutError. Only an
unfinished source body becomes a timeout with its retained cancellation prefix.
Document cooperative timing and the SDK's
bounded final server-error sleep, not a false hard-wall-clock guarantee.

### Output

Actual SDK reader bound to expected account and canonical group, without long hidden
waits/prompts or lost complete records on internal timeout.
### Safe in nature
False — touches the shared client factory and raw-batch exception boundary.
### Peripheral concepts
Proxy/pinned identity/session store, health task context, SDK1.45, budget sender,
entity/access hashes, media, asyncio cancellation.
### Hardness Lvl
5

## Step 3 — Router, admission and settlement [folded: Risk1, robust]

### Proposed changes

Implement AccountPool.read/get_message_batch using the fixed order and outcome table.
Reject duplicate configured IDs/groups at construction; validate source inputs before
network/state admission. Enforce serial ownership and per-call max_attempts with no
repeat candidate. Skip active/repair/deadline/age/budget-unavailable accounts. Persist
fresh UUID admission, require definite write success, then run the owned child.
Keep safe immutable attempt records. Classify the retained source-body outcome,
never an observer-only timeout, so an actual flood wait cannot become a shorter
transport cooldown. Classify actual source errors narrowly using
the existing health taxonomy plus explicit SDK/transport types; catch local errors
first. Retire only the exact token, never retry CAS into a different permission.
If any nonempty prefix exists, stop with that error after settlement. Source-free
unavailability includes all candidate reasons and a conditional earliest retry bound.

### Output

Working automatic selection/failover with durable permission and preserved observations.
### Safe in nature
True — new opt-in router; legacy TgData paths unchanged.
### Peripheral concepts
ReadBudget status versus actual reservation, account/group fact scopes, safe error
provenance, original exception identity, MessageBatch interrupted prefixes.
### Hardness Lvl
5

## Step 4 — Status, explicit repair/recovery and cleanup [folded: Risk2, robust]

### Proposed changes

Expose get_pool_status(chat_id=None), initialize(), recheck_account(account_id),
recover_account(account_id, *, attempt_id, previous_reader_stopped,
retry_not_before), close() and async context management. Status reads stored facts
and ledger eligibility, never authenticates. Recovery requires exact token, literal
True quiescence assertion and explicit aware UTC time; keep stronger deadlines/repair
flags and latest exact recovery retry recognition, including when newer work exists.
Recheck after known waits first awaits retirement of that slot's owned client,
reloads its configured session and repeats alias preflight. If retirement fails,
refuse replacement/source use. A durably admitted identity-only source attempt then may
clear repaired authentication/identity flags on fresh proof but never group denials
or budget. Close blocks new work, cancels/awaits owned activity, disconnects every
client; cleanup cannot replace a primary error. Context exit preserves its original
exception. Completed source-free progress operations remain usable after close.

### Output

Actionable state and conservative restart/repair/shutdown operations.
### Safe in nature
False — repair deliberately reloads owned credential state; preserve replacement
credentials during old-client cleanup and verify StoredSession conflict handling.
### Peripheral concepts
Exact retry recognition, task quiescence, session persistence, callback reentrancy.
### Hardness Lvl
5

## Step 5 — Existing progress facade reuse

### Proposed changes

Extract the current initialize_sync/sync_group/acknowledge_sync/get_sync_status and
backfill delegators into `tgdata/progress_facade.py`, with existing signatures and
behavior. Both TgData and AccountPool use it. Keep a TgData module-local backfill
factory hook so existing test clock injection remains valid. Preserve constructor
signature and engine cache fields. Do not decorate local methods as source health.
AccountPool supplies its reader only at actual new-source admission; local replay,
ack/control/status use only their respective progress stores. Export public pool
types in `tgdata/__init__.py`, not its private source/state internals.

### Output

Daily and backfill account routing through unchanged progress engines and receipt formats.
### Safe in nature
False — behavior-preserving extraction affects the existing public facade.
### Peripheral concepts
BackfillEngine factory seam, SyncEngine, local health exclusion, persisted replay.
### Hardness Lvl
4

## Step 6 — Actual-composition offline tests [folded: Risk1, robust; Risk2, robust]

### Proposed changes

Add `tgdata/smoke_tests/test_31_account_pool.py`, blocking sockets and using synthetic
credentials/replies with the actual factory/SDK, real SQLite and public pool APIs.
Cover constructor validation, config/proxy/pinned identity, duplicate IDs/keys,
stale cached identity, changed identity before send, no prompts, preserved server/
flood errors, actual pagination and quota charges, both strategies, warm-up, all
unavailable reasons, group-only denial, canonical alias redirect, no dialog sweep,
prefix/no-failover, timer prefix and external cancellation, overlapping tasks,
durable admission and ambiguous/failed writes, restart/missing/corrupt/schema-crossed
state, stale recovery/late settlement, stronger wait preservation, repair/recheck,
source-free daily/backfill replay/ack/control, media/local-error provenance and close.
Also block health callbacks after both successful and failing source bodies and prove
original data/wait preservation under internal timeout; replace actual stored login
credentials and prove deliberate recheck reloads them without stale-key overwrite.

Use controlled transport futures and commit-boundary backend wrappers to create
real overlap/uncertain responses; do not substitute the reader's key behavior.
Existing helper imports may serve fixtures only, never production code. Assertions
must include source call counts, exact account charges, saved state and original
exception/prefix identity. Add child-process crash coverage at admission/settlement
if ordinary backend reconstruction does not establish the intended ownership claim.

### Output

Reproducible failures that validate the public composition rather than mirroring implementation.
### Safe in nature
True — offline tests with synthetic state only.
### Peripheral concepts
SDK wire seams, actual SQLite commits, process/task lifetime, existing test18–30 helpers.
### Hardness Lvl
5

## Step 7 — Documentation and runnable example

### Proposed changes

Add docs/account_pool.md and README/smoke README entries. Show explicit pool-state
creation versus reopening, account/group inventory, existing budget configuration,
read/failover/unavailable results, daily/backfill use, prefix delivery and recovery.
State one owner, cooperative timeout, trusted UTC, account-visible history, repair
requirements and no joining. Clarify prior docs' caller-selection statements for
optional pool use while preserving plain TgData behavior. Add an offline runnable
example or demo with synthetic replies that demonstrates failover and replay without
private work-folder dependencies. No config secrets or login in example defaults.

### Output

A usable public contract and safe demonstration of automatic routing plus existing delivery.
### Safe in nature
True — docs/example additions.
### Peripheral concepts
SQLite stores, receiver acceptance, deployment ownership, library boundary.
### Hardness Lvl
3

## Step 8 — Verify and commit the offline delivery

### Proposed changes

Compile changed code and run test31, then the supported offline test12–30 sections
plus the repository's existing other offline checks. Use the already-established
offline runner/skip rules for legacy live suites; never connect simply because an
old script defaults to live config. Validate Python3.7 grammar where declared,
actual runtime3.11.10/Telethon1.45.0, example and isolated package imports. Review
diff and status for unrelated files/credentials. Do not include main-worktree todo,
paused #7 HANDOFF, stray guide edits or duncan.

Fix only small nonarchitectural slips under task-impl rules; record every fix.
An architectural verification failure stops for re-planning, not a patched contract.
Commit code/tests/public docs in one product commit and verification/work notes
separately. Update #17 status with E1 still open if applicable. No PR or merge is
implied by this step; merge-check and fresh PR critique remain later requests.

### Output

Verified and committed offline delivery plus precise live qualification status.
### Safe in nature
False — tests may reveal integration changes; deliberate commits require scope review.
### Peripheral concepts
Packaging, full regressions, issue status, archived process documents.
### Hardness Lvl
4

## Step 9 — Bounded live qualification

### Proposed changes

**Gated by E1.** Prepare a concrete read-only script/report after offline success.
Use two explicitly approved logged-in configs, fixed expected IDs, a canonical
shared existing group and the accounts' actual configured ledgers. Confirm no other
reader owns those sessions/progress. Bound each account to a few small batches and
name total upper charge before running. Exercise real identity/group resolution,
pagination if budget permits, policy-driven failover by locally making one candidate
ineligible, restart of saved waits, and source-free pending replay. Do not manufacture
ban/logout/flood through harmful traffic; deterministic offline probes cover those.
Stop on unexpected identity, access, policy or storage failures. Record exact versions,
before/after charges, outputs and limits. If resources unavailable, leave this step
pending and report its concrete prerequisite after finishing step8.

### Output

Real two-account composition evidence, or an explicit pending gate without false claims.
### Safe in nature
False — live reads consume allowance and expose real account/session resources.
### Peripheral concepts
Approved accounts/group, existing budget, one-reader ownership, Telegram visibility.
### Hardness Lvl
4
