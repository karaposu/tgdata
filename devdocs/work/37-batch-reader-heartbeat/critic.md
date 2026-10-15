---
model: gpt-6-astra
effort: xhigh
---
**REORDER — TEST BEFORE BUILD**

Falsifier: observing the actual SDK sender changes enqueue/admission/cancellation or cannot report repeated waits and multi-chunk progress without inventing liveness or changing retry policy.
Affordable now: yes — complete local candidate with Telethon1.45, synthetic wire, SQLite and pool tasks; no network/account/release required.

Experiment: build the complete proposed helper/factory/forwarding/milestones/docs/suite44 in a temporary source copy. Run the complete new suite and existing14/16/18/19/22–31/39/40 suites. Exercise actual SDK download/request loops and actual source/pool stores; include Future lists, budget coroutine sends, concurrent/background contexts, callbacks raising RPC/cancellation/errors, pending replay, cached/repeated waits, deliberately scaled watchdog and actual cancellation cleanup. Record all commands, results and exact product hashes.
Cost: bounded local development/test run.
Must precede: adoption of production Step1, including all later production steps.
Disqualifying result: the contract requires a new retry/ownership model, SDK-global interception or false timer liveness to satisfy the cases, or tests must weaken data/cancellation expectations.
Passing result: complete candidate meets the stated notification and compatibility behavior; underlying sends, waits, charges, raw/pending values and cancellation remain authoritative. Then fold the recorded qualification and adopt exact tested bytes.

## High-level summary

The plan adds a notification to existing work without making that notification a new authority over retries, messages or acknowledgment. Chunk progress is the correct signal for the reported large-download stall. Request observation addresses consecutive SDK waits; known library sleeps can be sliced. The explicit single-SDK-wait limitation prevents overstating what this observer provides.

No unsupported architectural premise or actionable code-level defect is established by reading. The exact behavior of the proposed sender observer still needs a real-component run. That is an experiment gate, not a reason to add a generalized retry system or guess that a mock callback proves compatibility. No Medium/High/Low findings; the full candidate qualification remains mandatory.

## Premise Inventory

### P1 — Sender observation preserves source authority
First dependent step1; wasted if false: helper, API plumbing, source tests and docs. Test scheduled before adoption. Cheapest earlier test: actual Telethon1.45 `_call` with actual factory mixins and a controlled sender, covering Future/list and budget-coroutine variants. Coverage now: full relevant SDK request loop and budget wrapper reads show one send followed by await, but no candidate execution exists. A fake reader supplying heartbeat is non-covering for enqueue/cancellation/charging. This premise requires the experiment.

### P2 — Progress is evidence, not timer activity
First dependent step1/2; wasted if false: watchdog contract and client observer. Test scheduled before adoption. Cheapest test: actual slow chunked download under a shorter silence watchdog, then a never-completing chunk; repeated/cached SDK waits with preserved sleep/send counts. Code inspection confirms SDK calls download progress after each write and has independent internal wait handling. It does not prove the candidate scope/wrapper. The plan correctly refuses a universal maximum-silence guarantee and preserves the SDK threshold. No new Telegram accuracy premise is asserted.

### P3 — Scope isolation survives owned source tasks
First dependent step1/2; wasted if false: public/pool surface and lifecycle qualification. Test scheduled before adoption. Cheapest test: concurrent calls on one real client plus inherited background work, followed by real pool source child/capture calls. Scope must bind inside each batch invocation, and deferred Future callbacks must consult the original observer's active flag. Explicit callback forwarding crosses the pool child boundary; the plan does not assume ContextVar ownership transfers to a child. No unqualified inherited lifetime is accepted.

### P4 — Optional callbacks do not change replay or data
First dependent step2; wasted if false: forwarders/source behavior. Test scheduled before adoption. Cheapest test: actual daily/backfill stores with failing callbacks, errors with completed prefix and pending replay, plus legacy injected readers without the keyword. Existing prepare functions distinguish pending replay before reader call; no schema changes are proposed. Actual candidate qualification must check both happy and failed publication paths and pool captures. Existing unmodified engine tests alone do not qualify the new plumbing.

## Restart Check

| Observed failure | Established mechanism | Planned response |
|---|---|---|
| Consumer cancels healthy long batch media reads | Actual writer calls download_media without progress callback; continuation has no heartbeat argument | Public forwarding and actual per-chunk `media` notification, scaled watchdog qualification |
| Multiple short SDK waits can accumulate into one silent read | SDK sleeps/retries inside one call without batch-level visibility | Per-request-start/response/flood observation, preserving existing SDK sleeps and threshold; no fake background timer |

## Inherited Lessons

The earlier #6 review established that local failures must not inherit Telegram health context and cleanup must preserve the original exception. Callback exceptions are consumed locally, logged by type and never propagated into batch/health classification; existing blob ownership/cleanup stays unchanged. #17 established capture and task lifetime boundaries: callbacks remain transient inside actual source work, no extra owned task is introduced, and pool settlement/acknowledgment keeps its original authority. Qualification uses real components before adoption; prior tests or a stand-in that invokes heartbeat do not close that gate.

## Compatibility and complexity

The proposed helper has one purpose. It neither intercepts all sleeps nor replaces the SDK retry loop. None follows the unchanged call shape; supplied heartbeat is forwarded explicitly. Counter/receipt schemas and old row-reader semantics stay unchanged. Adding the same option to existing backfill/pool routes is compatible plumbing, not a new lifecycle. Callbacks are documented quick synchronous observers; async callbacks are not silently awaited. No shared public observer framework or prerequisite issue is warranted.

## Findings and Phase3

Zero High, zero Medium, zero Low. Phase3 has no mitigation tiers to select. REORDER retains the plan and requires the experiment above. No deprecation, OPEN blocker or product patch follows from this review. Full experiment → record result → fold qualification → adopt → full verify, in that order.
