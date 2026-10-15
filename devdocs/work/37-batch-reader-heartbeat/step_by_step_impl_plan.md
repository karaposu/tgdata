---
model: gpt-6-astra
effort: xhigh
---
# Batch heartbeat implementation — revision2

**Critic folded:**2026-10-15 — zero mitigations selected; qualification ordering retained. Complete candidate PASS recorded before this fold.

**Status:** implemented atb789846; full914-check/7-demo verification passed. Review/publication/merge remain separate.

**Qualification:**31 new tests,16 related existing suites and3 demos;472 offline checks passed. Exact product/source hashes are recorded in prebuild/result.json. No design change was required. The initial fixture and local authoring corrections are recorded in prebuild/report.md.

### What is the task
Carry the established synchronous phase heartbeat into bounded batch/daily/pool reads so a caller distinguishes real download/request progress from silence, preserving data, retry, budget and cancellation contracts. Inputs: desc.md9cde140, triage8ee0a73 and source-request.md. Existing branch only, as instructed.

### Huge Hard Blockers
#### Planning Blockers
None OPEN. Installed Telethon1.45 uses client._call for normal/exported-sender requests and sender.send returns awaitables; its retry loop sleeps internally. The strategy observes existing request outcomes without replacing that loop. A complete candidate experiment must confirm this behavior before adoption.
#### Execution Blockers
None for implementation/offline tests. Release and ScrapeOps deployment are outside this task and require later actions.

### How this implementation moves toward desired state
One private task-scoped observer supplies safe phase calls and a transparent SDK sender observation seam. Public options forward only when supplied. Reader milestones/media progress use that observer; existing source state and immutable values are unchanged. Known tgdata-owned sleeps use its sliced sleep helper; SDK-owned sleeps remain unchanged with progress before/after request work and between repeated flood responses.

### High-Level Summary
| Step | Change | Output |
|---|---|---|
| 1 | Add private callback scope and SDK request observation | Isolated, safe progress without retry policy changes |
| 2 | Wire batch milestones and public forwarding | Direct/daily/backfill/pool heartbeat support |
| 3 | Qualify real components and document contract | Offline suite44 and consumer guidance |
| 4 | Adopt tested candidate, run regressions and commit | Verified existing-branch implementation |

## Qualification before product adoption
Build the complete candidate in a temporary copy of this branch (no Git branch). Test its actual public APIs, Telethon request/download loops, budgets and SQLite engines together. No production file is adopted before the candidate passes the full new suite plus related14/16/18/19/22–30/31/39/40 tests. A stub that simply calls the wanted heartbeat does not qualify the SDK seam. Preserve results and hashes. A structural failure requires returning to the contract; do not weaken expectations.

## Step1 — Task-scoped callback and transparent request observation
### Proposed changes
Create private `tgdata/batch_heartbeat.py`. Validate None or a synchronous callable; reject async functions/callable objects and noncallables before I/O with a health-neutral BatchFormatError. A contextmanager binds an observer to its owning asyncio Task, masks an enclosing scope even when heartbeat=None, and deactivates/resets on every exit. Callback exceptions (including directly raised CancelledError) are ignored and logged by error type only, with logging failures isolated. Unexpected awaitable return is not awaited; close a coroutine to avoid leaking it and report the callback contract error. Callback-requested Task.cancel still takes effect at the next await; real cancellation is never swallowed by the reader.

Add a small mixin into the existing client factory after BudgetClientMixin and before _PerCallFloodThreshold. Its `_call` fast path delegates unchanged without an active owner scope. Otherwise emit a request-start milestone and wrap only the sender argument, never the client-wide sender or SDK globals. Underlying send executes synchronously at the original point. For Future results, attach a bounded observer callback and return the same Future; preserve lists. For a coroutine result (the existing budget sender), return a coroutine awaiting it directly, without spawning another Task. Observe results/errors, distinguish actual flood response, preserve identity/traceback/cancellation. Future completion callbacks may use the captured active observer outside its owner task because they correspond to that exact request; unrelated/background task calls cannot acquire it. No health evidence or retries are created by observation.

Add a helper for existing tgdata-owned connection/auth/rate-limit sleeps: without a scope call asyncio.sleep once exactly as before; with one, sleep in at-most10-second slices using a monotonic deadline and emit `flood-wait` while deliberately waiting. Replace only those existing sleep calls. Do not intercept Telethon's sleep implementation or log messages, change thresholds, implement its retry loop, add a perpetual heartbeat Task or signal arbitrary time passing as progress.
### Output
One private observation mechanism, inactive unless batch code binds it; existing SDK policy and physical send/budget boundaries unchanged.
### Safe in nature
False — SDK request/async callback lifetime and cancellation need real-component qualification.
### Peripheral concepts
ContextVars/task inheritance, future versus coroutine ownership, budget sender admission, exported media DCs, health error context, factory mixin order, known waits.
### Hardness Lvl
4

## Step2 — Reader milestones and optional API forwarding
### Proposed changes
BatchEngine.fetch_batch gains heartbeat=None and enters the private scope before session acquisition, then delegates its existing implementation to a private helper with the safe beat. Emit connect/connected, resolve/resolved, existing dialog-sync labels, a scanned-message phase before window filtering and `messages` after a complete record. Pass a synchronous `progress_callback` to download_media only when heartbeat is supplied, emitting `media`; preserve the current no-callback call shape otherwise. Local blob publication/validation and completed-prefix logic stay untouched.

Forward heartbeat=None through TgData.get_message_batch, ProgressFacade.sync_group, SyncEngine.prepare; extend prepare_backfill and BackfillEngine.prepare consistently. Validate at entry before state/storage/admission. Add keyword to AccountPool read/get_message_batch/sync_group/prepare_backfill and their private forwarding methods; the existing owned source child receives the callback explicitly and binds its own batch scope. No callback at pool settlement/store boundaries. Only include heartbeat in an injected reader's options when non-None, preserving old reader signatures and exact None-call tests. Replay remains before fresh read and emits no required beat. Backfill pacing returns remain local and immediate. No schema or __init__ constructor changes.
### Output
One consistent optional callback from public APIs to genuine source work, with no callback stored in state or included in hashes.
### Safe in nature
False — several read façades and capture ownership paths need compatible forwarding.
### Peripheral concepts
Daily pending replay, backfill delivery identity, pool child tasks/captures, custom batch readers, window scanning, immutable batch values.
### Hardness Lvl
3

## Step3 — Behavioral suite and public guidance
### Proposed changes
Add suite44 using the existing real SDK/wire fixtures, actual file downloads and stores with sockets forbidden. Include: real multi-chunk download taking longer than a scaled watchdog timeout; truly stalled chunk cancels/cleans temporary file; all message/window/resolution phases; repeated and cached SDK flood waits with exact send/sleep counts; no auto-wait on pool sources; normal/no-heartbeat byte/budget equality; callback ValueError/RPCError/CancelledError and bad logger isolation; invalid async/noncallable callback before I/O; returned coroutine closed; task cancellation remains cancellation; no callbacks after scope; concurrent same-client isolation/background task exclusion; future lists and direct/exported sender `_call`; tgdata-owned sliced wait and default unsliced sleep. Exercise direct, daily and backfill including pending replay/no read, callback failure with pending-prefix persistence, all four pool APIs with caller capture, and legacy injected reader compatibility when None.

Document heartbeat in message-batch/daily/backfill/pool guides or their existing API sections and smoke README. Include quick sync callback contract, phases are diagnostic not counts/receipts, no fixed interval guarantee during an unanswered RPC/SDK sleep, watchdog threshold above a single allowed SDK wait, callback error type-only logging, default/no callback and replay semantics. Explain no author metadata, version bump or deployment. Keep old reader behavior untouched.
### Output
New suite44, focused existing-suite qualification and accurate consumer instructions.
### Safe in nature
True — tests and additive docs, no additional runtime change.
### Peripheral concepts
Real Telethon send/download/retry seams, watchdog time scales, cancellation/cleanup, source publication, pool budgets and existing integrations.
### Hardness Lvl
4

## Step4 — Adopt, regress and commit separately
### Proposed changes
After candidate PASS and any selected critic fold, adopt exact qualified product bytes. Run suite44 on actual branch and all existing offline suites12–19/22–43 plus seven demos; preserve optional live skips and watchdogs. Compile package/examples and Python3.7 grammar-check; native3.7 is not claimed. Record hashes, source/callback invariants and every local authoring correction. Commit code/tests/public docs separately from work evidence. Push the existing archive branch and update#37 through implementation only. Do not create a new branch, modify PR36, merge, release, deploy or touch original checkout/version edit.
### Output
Verified implementation with a precise later review/release handoff.
### Safe in nature
True — verification and authorized existing-branch checkpoints.
### Peripheral concepts
Full regression, source hash identity, archive/product commits, no-new-branch constraint.
### Hardness Lvl
3
