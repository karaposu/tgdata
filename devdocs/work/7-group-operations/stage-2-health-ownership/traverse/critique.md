---
model: gpt-6-astra
effort: max
---
# Critique: Stage 2 ownership design

## User Input

_branch.md, sensemaking.md and innovation.md: evaluate the complete candidate set
against the actual ownership failures and the user's small-stage constraint.
The td-critique reference was loaded in full earlier in this same conversation;
its dimension, adversarial, assembly and convergence requirements apply unchanged.

## Phase 0 — dimensions and inherited-premise prosecution

| Dimension | Weight | Required evidence |
|---|---|---|
| Stored ownership | critical | event/state/query cannot relabel or mix verified accounts |
| Source and recovery truth | critical | actual bound client/task; self metadata cannot imply group access; newer conditions survive older work |
| Work/lifetime integrity | critical | callbacks cannot replace results/errors/cancellation or prevent source close |
| Legacy compatibility | high | existing APIs remain usable; no silent migration of uncertain state |
| Scope/complexity | high | small local composition; no global registry or general tracing system |
| Feasibility/evidence | high | real current SDK/monitor paths and reproducible offline probes |

Premise prosecution: fixed monitors are only useful if they do not share recovery
context; the actual _Call parent behavior therefore needs a monitor/task boundary.
Deferring classification is only useful if caught failures cannot disappear; test
that rather than assuming exceptions always escape. Initial proof is evidence of
identity, but its request may have started before a newer concurrent condition.
None of these premises is protected merely because Sensemaking selected it.

## Phases 1–3 — candidate collisions

| Candidate | Strongest prosecution | Strongest defense | Verdict / constructive output |
|---|---|---|---|
| C1 owner-indexed rewrite | changes every ledger field and requires ambiguous default selection | uniform aggregate storage | KILL on scope; keep explicit account query, revisit aggregation with a consumer |
| C2 fixed complete ledgers | separately stored state could become invisible through the old query | explicit owned query removes guessing and reuses current state machinery | SURVIVE with documented legacy/owned query distinction |
| C3 mandatory whole-instance binding | breaks all existing constructors/call paths | single principal is easy to reason about | KILL on compatibility/extent; opt in at the verified operation boundary |
| C4 persistent request tracing | adds credential/error history not needed for one active client | can explain arbitrary cross-client behavior | KILL on extent; use the existing wrapper's actual client at observation time |
| C5 call-local source evidence | a caught raw RPC failure might never be classified, leaving only earlier success evidence | short-lived actual-client evidence avoids guessed exception ownership | REFINE into C5r below: record actual owned RPC health at the source, not only when an exception escapes |
| C6 ambient cache and any answer | reproduces all ownership/self-recovery failures | smallest textual patch | KILL on correctness; counterexamples are executable, not stylistic |
| C7 await isolated post-close callback | observer still delays caller and needs extra cancellation semantics | provides completion guarantee to a demanding consumer | REFINE/defer; require a real consumer for that stronger delivery contract |
| C8 independent post-close notifications | consumers cannot assume callback completed when work returned | preserves source/work lifecycle; snapshot already contains facts | SURVIVE with explicit timing and task-retirement contract |
| C9 application-driven queue drain | every consumer must orchestrate notifications | maximum delivery control | KILL on unnecessary API/burden; automatic best-effort notifications suffice |
| C10 enclosing-call isolation | global error tags could outgrow the stage | scoped suppression prevents a legacy outer owner claiming a foreign/pre-proof error | SURVIVE as call-local suppression only |

## Behavioral attacks and refinements

Two additional baseline probes ran with the real current HealthMonitor; the second
also used Stage1's actual client and SDK with synthetic transport/sockets blocked:

```text
older_call_clears_newer_wait: before GetHistoryRequest.seconds=120; after={}
caught_rpc_can_leave_only_success_evidence: verdict=ok, events=2
```

The older handled-wait call completed after a newer 120-second wait and erased it.
The second probe began with a known logout, then a call obtained fresh self evidence
and caught a later actual AuthKeyUnregistered reply without reporting it; the monitor
recovered to ok. These expose two relevant failure planes missing from a label-only
ownership model.

**C5r — observe owned RPC health at the source.** The client wrapper already knows
the actual client and raw RPC exception. For an active owned call, record classified
raw RPC failures immediately in its fixed-owner ledger and queue their notifications.
Use an explicit owned-event source such as `rpc`: it means the request failed,
not necessarily that the overall operation eventually failed. Deduplicate through
the existing reported-error mechanism. Automatic owned reporting does not infer
health from an arbitrary local exception's cause chain. This removes the need for
a deferred exception-origin registry and prevents caught failures from disappearing.
Explicit derived domain findings remain separate deliberate assertions, not a
reason to classify arbitrary local errors as Telegram failures.

**Conservative recovery ordering.** Capture the owned operation's start order before
authentication and retain condition order. A condition recorded after that start
cannot be recovered by this operation, even if an old request's response arrives
late. A later operation with actual matching successful evidence can recover it.
This conservative rule plus request-specific evidence/current wait generation
prevents stale clearing without a universal per-request trace framework. A call
cannot recover its own recorded failure. Authentication proof may supply account
evidence but never group proof; group access confirmation remains explicit after
real owned work, and metadata/self-only work cannot supply it automatically.

**Delivery refinement.** Queue log/callback notifications after state recording,
then dispatch them after the source's close attempt. Invoke both sync and async
callbacks in the delivery task, never directly in the work task. Track/retrieve
delivery outcomes; cooperative TgData.close can cancel pending owned notifications
without awaiting its own current callback. No durable delivery guarantee is added.

## Phase 3.5 — assembly re-test

Assembly A1 = C2+C5r+C8+C10 with conservative recovery ordering. Prosecution: a
setup failure escaping after observation isolation could be re-labelled by an
outer legacy wrapper; or an inner legacy report could set the parent's recovery
flags. Defense: scoped enclosing-call suppression for escaped owned-boundary
errors, monitor/task-limited parent reporting, and client-bound request hooks.
Collision: SURVIVE with those mechanisms explicitly required.

Further prosecution: source `rpc` and asynchronous delivery differ from the old
event contract. Defense: this is a new opt-in owned path; document both differences,
leave legacy delivery/query unchanged, and expose immediate local owned snapshots.
Collision: SURVIVE. Do not silently advertise the old before-exception callback
completion guarantee for new owned observations.

## Phase 4 — coverage and convergence

Round1 reviewed all ten candidates and exposed C5's missing caught-failure case.
Round2 applied source-time recording and conservative ordering to wait/account/group
conditions and pre-proof failures; the local composition remained viable. Round3
tested the same assembly against callback cancellation, nested legacy calls and
unknown-account query behavior; no new architecture was needed. The last two rounds
stay in the same viable region. The five current-component probes provide external
grounding; hypothetical examples alone did not establish the verdict.

Coverage: all ten candidates and the refined assembly, six dimensions, all three
original articulations explicitly evaluated. Viable: fixed-ledger/explicit-query
composition. Dead: cached/last-owner authority, broad mandatory migration and global
tracing. Deferred boundary: callback-completion guarantees. Unexplored live server
behavior is not claimed established or required for this local foundation.

Accumulator: C1/C3/C4/C6/C9 killed with seeds; C5 refined successfully; C7 deferred
with consumer trigger; C2/C8/C10 and A1 survive. Mechanism independence validated
by code and executed probes. Adversarial strength STRONG; landscape STABLE in the
last two review rounds; no critical caveat on A1's defined scope.

**Signal: TERMINATE — A1, then its component survivors.**
**Telemetry: PROCEED.** No silent weight drift, decorative risk, cross-instance
dependency or false claim that the old legacy health implementation is migrated.
