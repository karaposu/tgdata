---
model: gpt-6-astra
effort: xhigh
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the real SDK and public readers cannot satisfy bounded ownership, unchanged
policy and ordered prefixes together without changing the proposed contract.
Affordable now: yes — local candidate, installed Telethon1.45 and native files; no
live account or publication needed.

Experiment: build the complete planned candidate in a git-free copy of devd8232d1,
including the selected nested-scope mitigation below. Run the new native SDK/public
reader suite, all affected suites and the complete supported offline suite plus seven
demos. Include real file/document/download iterators, sender migration/CDN creation,
SDK retry/cached-wait paths, budgeted refreshes, child task attribution, window-prefix
failures, repeated stop while cleanup is held, both reader callbacks and all durable
consumer/replay paths. Controlled source responses may provide bytes/errors/timing;
they may not implement ordering, cleanup, admission or success on the product's behalf.
Cost: bounded local implementation prototype and offline tests. Must precede step1
product adoption (therefore every plan step). Preserve first outcomes and source hashes.
Passing result: all declared cases and regressions pass with bounded tasks/results,
exact default behavior, original error/cancellation, no unowned resource/late activity,
correct source policy and unchanged batch/receipt identity; no structural correction
or relaxed assertions needed. Small naming/import/fixture wiring mistakes may be
recorded and corrected before the affected check reruns.
Disqualifying result: the actual composition requires a new ownership/policy contract,
source fork beyond the planned private seam, weaker prefix/cleanup semantics or changed
regression expectations. Record FAIL, deprecate plan and stop; do not patch architecture
under the same plan. Live throughput is not part of the pass claim.

## High-level summary
Zero High, one Medium, zero Low findings. Shape survives with explicit client-bound
contexts and masking at public nested read boundaries. Full native prebuild remains
required; native lifetime and nested-context observations alone do not replace it.
Same warmed session, current-thread GPT6 Astra/xhigh verified; no subagent. Plan a4db484,
desc4821a7b, triage and complete traverse read together with real SDK/source consumers.

## Premise Inventory (ranked by waste if false)
### P1 — task/resource ownership can be complete in the actual SDK composition
First dependent step1 and all later integrations. False wastes the whole scheduler.
Current coverage: real successful exported download returns1 borrow; cancelled download
returns0 despite its Task stopping (sdk_lifetimes.json). That establishes the gap,
not the proposed closure. Existing iterator.close and helper creation seams are real.
Cheapest earlier covering test: complete opt-in candidate with cancellation during
iterators/CDN creation/release and repeated parent stops, before adoption. Nativefiles
and real private SDK paths must execute; mocked successful release is non-covering.

### P2 — backoff remains coordinated without replacing the SDK retry authority
First dependent step1, batch/legacy steps2–3. False demands changing the source contract.
Current coverage: actual1.45 _call code and heartbeat/budget tests establish seams,
not new combined gate timing. Test scheduled in mandatory prebuild. Cheapest covering
experiment includes inside-threshold retry, cached wait, above-threshold propagation,
zero-second normalization, exported/CDN policy and refresh budget admission. Gate must
precede reservation/enqueue, not put committed budget claims behind a new sleep.

### P3 — ordered acceptance and default compatibility survive integration
First dependent steps2–4. False changes reader/receipt semantics. Existing batch and
sync/backfill/capture contracts provide actual oracles. New window/callback behavior
is unproven until public paths run. Complete native prebuild checks101 failure after
102 success, metadata/page failure, cancellation and callback exit; unchanged defaults
run in the complete regression suite. Smaller semaphore-only tests are non-covering.

### P4 — inherited task context does not become ownership of nested work
First dependent step1/reader wrappers. Native public legacy callback probe confirms a
nested call can use another client on the same Task while inheriting outer context.
This is not hypothetical background-task inheritance; task equality alone cannot
exclude it. Risk1 below supplies the missing boundary. Test exact cases in prebuild.

### P5 — throughput improves and a chosenN is appropriate for a real account
First dependent deployment choice, outside these adoption steps. Reported timing is
not newly verified; real live workload/network varies. No universal safeN or multiplier
is promised. Native timing can prove actual overlap, not real network speedup. A
bounded separately authorized benchmark remains the external validation route.

## Restart Check / inherited lessons
SDK cancellation: actual borrow survives cancellation; explicit iterator/helper
accounting and joined finalization address the mechanism before adoption.
Prior account ownership: cached identities do not authorize account-wide coordination;
this design deliberately scopes to one engine and does not loosen verified handles.
Prior false health/local errors: owned-stream/local-I/O boundaries and source/context
separation remain; native error-precedence probes must cover them together.
Progress is not received bytes: existing validated prefix and durable acknowledgment
stay authoritative. These lessons are tested before product adoption, not just listed.

## Risk 1 — nested reads can inherit another operation's source gate
**Risk — plain:** An application may start another read from a batch callback. That
read runs in the same asynchronous task as the outer read, but it can use a different
client or explicitly request ordinary sequential behavior. If the new concurrency
state follows the task alone, the nested read may unexpectedly inherit the outer
read's wait policy, resource owner or progress attribution.

**Risk — precise:** Step1 proposes task-owned context for the parent and child media
requests, but does not explicitly bind source hooks to the authorized client set or
mask inherited media context on N1 public read entry. MessageEngine.fetch_messages
awaits batch_callback directly. The actual public-path probe nested_context.py records
two nested SDK sends with same_task=true, inherited_outer_context=true and
different_client=true. A mixin using only current-task identity would intercept those
sends despite the described scope. This is a plan gap, not an existing product bug.

**Severity:** Medium
**Category:** ownership/compatibility
**Impact:** unrelated source calls acquire unintended backoff/resource behavior; the
promised unchanged default can fail only when nested under an opted-in call.
**NoobEng:** Context variables follow call chains automatically. The same Task can
perform several logical operations, so owning the Task does not own every client or
nested read it happens to call.
**Affected areas:** media owner/mixin, batch and legacy read entry boundaries, callback
integration, health/heartbeat membership tests.

### Quick mitigation
Document nested reads as unsupported while concurrent media is active.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

### Robust mitigation
Bind each media context to its root client and explicitly registered owned CDN
helpers. Hooks require both active task membership and client membership. Mask any
inherited media context at every fresh batch/legacy read boundary; N1 stays masked
throughout, N>1 installs its own owner after same-engine admission. Nested opted-in
same-engine calls reject before source work; another engine installs an independent
context. Add real nested callback cases for same/different client, N1/N3 and background
inheritance. Do not broaden verified account-operation or owned-health authority.
**Why this is robust:** closes the concrete same-task leak at the public operation
boundary while retaining explicit source ownership; covers both affected readers.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

### Long-term mitigation
Introduce a general invocation-capability system for every source-facing API, including
existing group operations, progress, worker and login paths.
**Why this is long term effective:** if a repeated cross-API ownership class emerges,
a shared capability might enforce all task/client/resource boundaries uniformly.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

## Preconditions retained
Complete real prebuild before adoption. No externally blocked implementation step;
separate live benchmark requires explicit account/group/allowance authority. No new
branch, schema, package version, dependency, release or deployment in this run.
