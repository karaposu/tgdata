---
status: active
model: gpt-6-astra
effort: max
refines: devdocs/inquiries/2026-10-12_19-42__17-account-pool-foundations/finding.md
---
# Finding: #17 must separate who stops a read, who finishes it, and who keeps its data

## Changes from Prior

**Prior path:** `devdocs/inquiries/2026-10-12_19-42__17-account-pool-foundations/finding.md`, the earlier account-pool ownership inquiry.

**Revision trigger:** a failed storage-cancellation prebuild, then a second rejected PR review after the replacement implementation. The user asked to return to the description and traverse before another plan.

**Preserved:** existing-access routing, verified numeric account identity, actual read-budget charges, durable account restrictions and uncertain-attempt recovery, separate group receipts, retained native cleanup, and passive health observations.

**Changed:** the ownership boundary must reach the public caller. Keeping data inside a source wrapper or on a cancellation exception does not guarantee the application can retrieve it. The caller's Task also cannot stand for the lifetime of work owned by tgdata.

**New:** a private completion fact for each owned invocation, plus an explicit caller-owned destination for that invocation's data. The destination is local memory, not another database or a global result registry.

**Migration:** revise #17's description before producing a new plan. The unmerged pool's data-producing calling form may change explicitly; ordinary TgData, group-operation and worker APIs do not acquire a new lifetime policy. Production remains at `a63099e`, and PR #26 stays draft/rejected.

Changes to inherited action commitments:

- MUST/COULD drift: prior text “Re-plan the existing pool around the explicit operation and observation contract before implementing more pool changes.” New text: “Revise #17's description around invocation lifetime and caller-owned data before another plan.” Rationale: the second PR rejection requires a return upstream, and the public receiver was missing from the earlier contract.
- MUST/COULD drift: prior text “Prove the revised operation boundary with actual source, store and progress components before accepting its implementation.” New text: “Qualify the entire proposed public ownership contract with a combined real-component prebuild before production edits.” Rationale: include application continuation, wrapper replacement, late observers, recipient lifecycle and progress publication; selected examples alone already missed a defect.
- Current-dev integration, full offline verification, fresh PR critique, two-account live qualification and the optional workload-driven ranking improvement keep their prior acceptance conditions. This inquiry satisfies none of those future implementation/merge gates.

## Question

After two rejected reviews of the automatic account pool, what assumption is still wrong? Is this a local shutdown bug, a missing ownership concept, or evidence that the feature needs a larger prerequisite? What must the description say before another implementation plan is credible?

The selected feature lets an application ask tgdata to read a group using accounts that already have access. The pool chooses an eligible account while respecting identity, waits and budgets. The user wants completed reads preserved without turning tgdata into a scheduler or another application.

## Finding Summary

- The fundamental mistake is treating an application's asynchronous Task as both the lifetime of a tgdata operation and the container for its result.
- A Task can keep running after the library call has ended. Waiting for that whole Task makes pool shutdown depend on unrelated application cleanup.
- A cancellation exception is a control signal. Ordinary wrappers can replace it, so attached messages are not a dependable delivery channel.
- Give each owned invocation its own completion fact. Give its completed data a caller-retained destination that exists before execution.
- Keep data availability, call completion, account permission and durable acknowledgment distinct.
- Preserve the tested routing, quota, state, progress and retirement mechanisms. No separate scheduler, result database or library-wide rewrite is justified.
- Offline concept tests support this contract. They do not implement it, qualify all its behavior, or make the rejected PR mergeable.

## Finding

### 1. The failures share a missing distinction

The first rejected PR allowed a health observer to replace the result of a completed read. It also allowed a shutdown dependency cycle: the read waited for a callback, the callback waited for close, and close waited for the read.

The next design removed callbacks from source work. Its prebuild then found the same result-loss pattern in storage: a provider could await its own cancelled I/O even though the application never requested cancellation. The real source had produced 100 messages and a 7,200-second Telegram wait, but the caller received no messages.

The replacement implementation retained source and provider outcomes separately. Its later PR review found the remaining public boundary: close awaited the cancelled caller Task first and consumed the cancellation exception carrying the messages. A later application waiter received a different exception with no data.

There have been **two rejected PR reviews and one failed intermediate prebuild**. Revision numbers are not counts of rejected PRs. The current product has not been repaired by this inquiry.

### 2. Changing one await does not establish the correct lifetime

This inquiry ran a caller that caught tgdata's cancellation, then performed unrelated application cleanup. At that point the pool's operation slot was free and all owned source/provider tasks had ended. Yet close still waited because the containing application Task had not ended.

Changing close to a non-consuming wait on that same Task avoided reading its exception but retained the wrong lifetime. The three real raw, daily and backfill contrast cases reproduced that wait.

The corrected contract needs a completion fact tied to **the library-owned invocation**, meaning the particular accepted operation and its owned source/account-state work. It ends only after that work has actually settled and its exclusive ownership has been released. The containing Task can be an address to which a stop is sent; its entire lifetime is not work owned by the pool.

A stop must target the same invocation that was observed as active. A late stop cannot cancel a successor invocation or arbitrary application work after the library returned. Actual native disconnect remains retained through cancellation, with failed retirement quarantined as before.

### 3. Completed data needs an owner outside the cancellation signal

The current code loses cancellation-attached data even when close never runs. With one real completed message and a real late SQLite settlement, direct waiting retained the payload. `asyncio.shield()` and `asyncio.gather(..., return_exceptions=True)` exposed a cancellation signal without that payload. The Task was genuinely cancelled in every case.

This behavior was measured on Python3.11.10. The versioned [Python asyncio documentation](https://docs.python.org/3.11/library/asyncio-task.html) describes Task cancellation and wrapper behavior; it does not promise to preserve arbitrary attributes on one exception object. A portable library contract should not depend on that undocumented carrier.

The canonical pool calling form therefore needs a **caller-owned, single-use result recipient**: a local object the caller retains before execution, to which the library records actual completed data. Its exact public name belongs to later design. Its ownership cannot remain implicit or optional while the API promises unconditional cancellation-safe delivery.

The caller can await the operation normally. Success returns, ordinary failures raise, and genuine cancellation remains cancellation. After any of those outcomes, the caller can inspect its retained recipient without re-awaiting the Task or relying on which observer saw an exception first.

The recipient is neither a callback nor a pool-wide registry. Capturing known data is local and invokes no application code. Each recipient owns at most one current batch under existing batch limits, with bounded diagnostic facts rather than live exception tracebacks, Tasks, clients or credentials. This is a bound on retained objects and lifetime; the present batch schema does not establish a universal byte-size limit.

The caller owns keeping or discarding the recipient. Process death may lose data that was only in memory. Existing durable pending deliveries retain their own replay guarantees. Adding durable raw-read delivery would be a different requirement.

### 4. The recipient must distinguish availability from completion

A recipient that has never been bound is not a completed empty read. If an application creates a Task and cancels it before the coroutine starts, tgdata performs no I/O and has no produced data. Reusing an already-bound recipient for another invocation must be rejected before I/O; it cannot overwrite an earlier result.

While the invocation runs, complete validated records may already be known even though settlement remains unfinished. Retain them before later awaited work can obscure them. A provisional snapshot must be conservative: it cannot claim final success, end-of-history or a durable receipt.

When the public call ends, its final recipient state becomes stable. Retrieval is nondestructive and read-only. A later close or another call cannot consume or replace that invocation's data. A completed success is not retroactively downgraded because close happens afterward.

The small adapter used in this inquiry captured at public-call exit. It proves independent retrieval for the tested cancelled/error outcomes, but it does **not** implement early availability, input validation or the complete public recipient lifecycle. Those requirements must appear in the later combined prebuild.

### 5. Pool shutdown, progress publication and acknowledgment remain separate

A daily or backfill call contains more than a source read. After the source/account operation ends, the caller may still be saving group progress. Fresh real-component tests held that publication in SQLite: pool close retired all clients and returned, while the public progress call was still waiting. Releasing the write then produced a real pending delivery.

This is a valid ownership boundary. Close governs the pool's source/control work and clients; it does not become the owner of every state-only progress operation. The public call's recipient becomes final when that call ends, not merely when the pool's source slot is released.

The existing authorities remain separate:

| Fact | What establishes it |
|---|---|
| Permission to contact Telegram | Definite durable account admission plus current eligibility checks |
| Allowance spent | The existing ReadBudget ledger |
| Data available to the caller | Actual validated records in that invocation's recipient |
| Durable pending delivery | The real daily/backfill store and its existing reconciliation rules |
| Progress accepted by the receiver | The existing explicit acknowledgment contract |

A captured batch cannot refund a charge, shorten a wait, clear an unknown account attempt or invent an acknowledgment receipt. A cancelled or failed admission reply cannot be interpreted as rollback or permission. True caller cancellation starts no new persistence merely to save an error prefix; already-owned writes must still finish their own cleanup.

### 6. The evidence supports a focused boundary change

The experiment comparing whole-Task waits with invocation completion used actual Telethon disconnects and actual SQLite/account/budget paths. The candidate completion witness let close finish while unrelated application cleanup remained pending.

Across 24 true-cancellation concept histories, a caller-retained recipient preserved either one completed message or the actual 100-message prefix. Wrapper signals could still contain zero messages; the independent recipient retained the records. Real charges stayed 1 or 200, and no second-account read substituted for the missing data.

Another sixteen concept histories exercised provider cancellation before and after actual account/progress commits. Data, unknown account attempts, known waits and pending receipts retained their separate meanings. Six existing regression controls also passed, including identity checks, uncertain admission, daily replay and failed-retirement recovery.

These results support two small responsibilities: the library certifies when its own operation ends, and the caller owns where its data is kept. They do not establish a need for a global supervisor, a new result database or rebuilding drain/spread selection.

## Inherited Commitments Re-test

| Commitment and source | Re-test status | Evidence / reason |
|---|---|---|
| Numeric identity at actual send; original account-pool traverse finding | RE-TESTED — commitment confirmed | Changed-identity real send control passes in [sense probe](evidence/sense-probe.txt). |
| Definite admission and unknown-attempt refusal; original finding and failed prebuild | RE-TESTED — commitment confirmed | Before/after actual account CAS outcomes and restart control preserve refusal and charges. [Concept log](evidence/concept-probe.txt), sense probe. |
| Preserve complete source data; foundation finding and prebuild_r3.md | RE-TESTED — commitment confirmed but frame revised | Preservation must reach a separately addressable public recipient, not stop at an internal holder or exception. Actual 100-record/FloodWait histories retain records. |
| Caller Task represents operation completion; reviewed product underlying latest pr-critic.md | RE-TESTED — commitment found INVALID | Source/provider work ends while application cleanup continues. Non-consuming caller join still waits. [Lifetime contrast](evidence/concept-probe.txt). |
| Cancellation exception can be the sole public data carrier; reviewed revision4 description | RE-TESTED — commitment found INVALID | Shield/gather lose the payload without close. [Public wrapper observations](evidence/sense-probe.txt). |
| Source and provider cancellation need provenance; foundation finding plus prebuild_r3.md | RE-TESTED — commitment confirmed | Real caller stop and provider-owned cancellation yield different signals and preserved actual data; concept account/progress cases. |
| Retained native cleanup, quarantine and explicit retry; foundation finding / retirement work | RE-TESTED — commitment confirmed | Actual SDK cancellation and failed-cleanup regression controls re-run in sense probe; concept close waits for native retirement. |
| Quota and group receipt separate from account recovery; original/foundation findings | RE-TESTED — commitment confirmed | Charge1/200 remains; data can exist without pending receipt. Real publication-before/after faults have distinct persisted outcomes. |
| State-only progress retains caller ownership; revision4 description | RE-TESTED — commitment confirmed | [Critique probe](evidence/critique-probe.txt) holds daily/backfill publication past close. |
| Passive bounded health data and provider I/O-only role; foundation finding | INHERITED-WITHOUT-RE-TEST in full | Existing implementation/contract inspected, but this inquiry did not rerun every overflow, external-actor/reentry or capture-failure case. Keep full regression obligations. |
| Complete configuration/recovery, all routing policies, worker compatibility; original plan and verification_restart.md | INHERITED-WITHOUT-RE-TEST in full | Six relevant controls were re-run; the earlier entire offline suite was not repeated for a docs-only inquiry. Future implementation must requalify it. |
| Two-account live behavior; original and foundation findings | INHERITED-WITHOUT-RE-TEST | No two-account resources or live traffic used; the execution gate remains pending. |

## Next Actions

### MUST

- **What:** Revise #17's description around invocation lifetime and caller-owned data before another plan. **Who:** this upstream documentation task. **Gate:** this saved finding and its acceptance boundaries. **Why:** remove the two false ownership assumptions from the next plan's inputs.
- **What:** Qualify the entire proposed public ownership contract with a combined real-component prebuild before production edits. **Who:** a later #17 task-impl run after a new plan and fresh plan critique. **Gate:** raw/daily/backfill composition, early and final recipient state, cancellation provenance, all store phases, observer order, application continuation, native cleanup and unchanged durable facts. **Why:** a small concept adapter is not a finished design.
- **What:** Retain current-dev integration, full offline suites and a fresh PR critique. **Who:** later implementation/review work. **Gate:** accepted new design implemented and verified. **Why:** PR #26 is still rejected.
- **What:** Qualify failover using two approved existing accounts and a shared group. **Who:** maintainer and authorized live-test runner. **Gate:** offline verification passes and account/group/shared-budget resources are confirmed. **Why:** establish actual operational behavior.

### COULD

- **What:** Extend ranking beyond drain/spread. **Who:** later pool work. **Gate:** real workload evidence shows unfairness. **Why:** improve utilization. **Depends-on:** MUST implementation/verification; GATED until it passes. This is inherited optional work, not a remedy for result loss.

### DEFERRED

- **What:** Add a durable raw-result journal or background job control. **Gate:** a named consumer requires process-crash delivery or independent job lifetime beyond existing progress stores. **Why if revived:** those are stronger delivery responsibilities.
- **What:** Extract a shared lifecycle helper. **Gate:** a second consumer demonstrates the same completion and failure policy. **Why if revived:** remove proven duplication.
- **What:** Add automatic joining, distributed ownership or lossless telemetry. **Gate:** explicit scope selection or a named consumer requiring the stronger guarantee. **Why if revived:** meet a different access, deployment or reporting need.

## Reasoning

A non-consuming wait is useful but insufficient: it still waits for the wrong owner if its target is the whole caller Task. A library-specific completion fact survives that objection because its end is defined by actual owned work, not by arbitrary code after the library call.

Attaching more fields to cancellation exceptions cannot control ordinary wrapper behavior. An explicit caller-held destination survives that objection without changing true cancellation into success. The older foundation finding rejected a universal result envelope as an unnecessary broad API rewrite; the new evidence requires an explicit destination only for #17's canonical data-producing calls. It does not justify replacing every TgData error API.

Dropping the preservation promise and refetching would violate the user's requirement. Refetch can also be prohibited by an unknown attempt, a wait or depleted allowance. Refusing every close while busy would avoid one dependency by removing required shutdown behavior, while leaving wrapper data loss unresolved.

A combined transaction for permission, quota and group delivery is incompatible with the existing independent stores. Deriving permission from a delivered batch would forget uncertain attempts. Keeping those authorities separate preserves their real recovery rules.

A pool-global result registry would need identifiers, eviction and abandonment policies. A durable journal would add another uncertain-write protocol. Replacing calls with cooperative background jobs would still leave real Task cancellation to handle. These alternatives serve broader products, not the measured missing boundary.

A larger example suite or a live-only test is insufficient evidence. The selected qualification approach observes the actual receiver, owned children, native clients, ledger and store outcomes separately, including negative controls. Two-account live testing remains useful for different assumptions.

## Open Questions

### Monitoring

The next design must demonstrate one-shot recipient validation, local retention before later awaits, provisional-versus-final snapshots, safe disposal and absence of retained Task/client/exception graphs. The inquiry adapters do not implement those rules. Any failure in their combined prebuild returns to the affected contract; it must not be repaired by reducing the expected data.

Only one full traverse iteration ran here. The critique found a complete answer to the upstream question, but explicitly flagged that repeated full-cycle stability has not been established. This finding claims an evidence-backed ownership contract, not exhaustive proof of an optimal architecture.

### Blocked

Two-account live qualification remains pending. Native Python3.7 execution also remains unmeasured; source compatibility and Python3.11 observations do not replace it if that runtime remains supported.

### Research Frontiers

Raw reads surviving process death would need an explicitly chosen durable delivery owner. No such new guarantee is established by preserving data across in-process cancellation.

### Refinement Triggers

Revisit the explicit-recipient calling contract if a required application cannot retain a reference before execution. Revisit the source/progress ownership split if a required provider needs pool-controlled shutdown to finish its own I/O. Revisit a shared supervisor only when another concrete consumer demonstrates the same ownership policy.

## Evidence and scope

Subject: production `a63099e`, integrated dev `2ddb852d917998d003f9db863fce09a92e9c5712`, initial review/handoff `28fd4c2`. Python3.11.10 and Telethon1.45.0 executed with real local components, synthetic Telegram replies and blocked sockets. No live login, account, budget reset or product patch was used.

The [evidence directory](evidence/) contains the scripts and outputs. The first concept run's too-short completion observation is preserved in `concept-probe-initial.txt`; the corrected run waits for actual native retirement and passes 46 histories without changing production or weakening expected data. Three later critique observations pass. Parent watchdogs bound all experiments; no killed process is counted as completion.

The [archived critique](docarchive/critique.md) records the detailed candidate decisions. The [route-map](routelister.md) and [concept index](_route.md) remain at the inquiry root. A complete implementation prebuild and renewed PR review are still required.

## Source Input

<details>
<summary>Raw user request</summary>

```text
return to the description/traverse before another plan. , do it
```

</details>
