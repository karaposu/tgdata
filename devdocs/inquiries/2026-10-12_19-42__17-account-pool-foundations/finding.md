---
status: active
model: gpt-6-astra
effort: max
refines: devdocs/work/17-account-pool/traverse/finding.md
impacted_by: devdocs/work/17-account-pool/prebuild_r3.md
---
# Finding: #17 needs a clearer operation boundary before further implementation

> **Later evidence, 2026-10-12:** the subsequent combined prebuild passed the
> proposed observer/source/control cases but found the same cancellation-origin
> mistake during awaited state settlement. The provider contract needs completion
> semantics as well as control restrictions. [Read the failed prebuild](../../work/17-account-pool/prebuild_r3.md)
> before using this finding for implementation; revision3 was deprecated. The
> original inquiry below is preserved as the record that produced that candidate.

## Changes from Prior

**Prior path:** `devdocs/work/17-account-pool/traverse/finding.md`, the original
account-pool design inquiry. **Revision trigger:** implementation and PR-review
counterexamples, followed by the user's request to examine the foundations.

**Preserved:** account identity verification, persistent owned clients, durable
permission to start an attempt, existing quotas, and group-owned delivery progress.

**Changed:** source completion, caller cancellation, reporting and shutdown need
separate operational rules. Preserving a result only when an observer times out is
insufficient. Checking the current task alone cannot establish safe shutdown ownership.

**New:** actual probes show the same problem on successful reads and before any
source request, and disprove a scope-tag-only fix for arbitrary awaited observers.
The recommended simplification makes health reports passive data owned by the caller
once retrieved. This deliberately changes the unmerged pool's callback contract.

**Migration:** apply these conclusions to revision-3 re-planning of PR #26. This
inquiry changes no runtime files and does not approve the rejected PR.

Changes to the prior action commitments are explicit:

- MUST/COULD drift: prior text “describe, plan, critique, implement and verify the
  owned pool and exact failure contracts.” New text: “Re-plan the existing pool
  around the explicit operation and observation contract before implementing more
  pool changes.” Rationale: most capability already exists; the next step must
  correct its ownership assumptions rather than repeat the initial build.
- MUST/COULD drift: prior text “test actual source/store/timeout and existing progress
  composition, including concurrent calls and uncertain writes.” New text: “Prove
  the revised operation boundary with actual source, store and progress components
  before accepting its implementation.” Rationale: add cancellation origin and
  callback/provider/control dependencies to the existing composition requirement.
- The prior two-account live requirement and optional ranking improvement remain
  conditional on their original resources/workload evidence. Neither is replaced
  by this inquiry's offline probes.

## Question

Does #17's need for revision 3 indicate a fundamental design mistake? Which missing
concept or abstraction would prevent more rework and make the account pool simpler
to implement? Which existing work should be retained?

The account pool lets an application request a group read while tgdata chooses an
eligible account and tries another when appropriate. This inquiry examines the
selected first delivery: accounts reading groups they can already access. It does
not add automatic joining, scheduling or distributed ownership.

## Finding Summary

- There is an upstream contract problem, but the evidence does not justify restarting
  the entire account pool.
- Revision 3 is the next plan version after one rejected PR review. It does not mean
  three separate pool designs were rejected.
- The code sometimes treats the end of a task containing both a read and reporting
  as the result of the read itself. Those are different facts.
- Shutdown sometimes treats a task's identity as proof that its caller is independent
  of the operation being stopped. Child tasks and pre-existing tasks break that assumption.
- Make source outcome, caller stop, permitted control and actual cleanup explicit.
  Keep arbitrary application reporting work outside the pool's source lifetime.
- Prefer bounded health-report data that the caller can retrieve locally, including
  during errors or close. The caller owns any processing of that data.
- Retain routing, account restrictions, quotas, restart recovery, progress and the
  persistent-client retirement safeguards. Rework the boundary around operations.
- Prove that boundary before rebuilding the surrounding feature. Two-account live
  qualification remains a separate pending gate.

## Finding

### 1. What the revision history actually shows

The original plan was revised after its plan critique. A later scoped retirement
repair was also revised after critique. PR #26 then received one rejected fresh
review with two Medium findings. Revision 3 is required next; it has not already
failed. The [saved PR critique](../../work/17-account-pool/pr-critic.md) records the
rejection and its reason.

Nevertheless, the repeated repairs concern a real shared boundary. Earlier work
preserved a source result when reporting timed out. Retirement work stopped caller
cancellation from releasing a client while its actual disconnect was still running.
The rejected PR exposed two other paths through those same ownership decisions.

The problem was partial semantics: a rule worked for one termination path but was
not established for all the roles using the operation. Adding another exception
handler without clarifying those roles could repeat that pattern.

### 2. A completed read and completed reporting are different facts

The source wrapper records the real read result before delivering health callbacks.
It uses that saved result on the timeout path. On the ordinary completed-task path,
it instead returns the enclosing task's result.

A callback can await a cancelled future even when the caller never requested
cancellation. In the reproduced failure, Telegram had already produced 100 complete
messages followed by a 7,200-second wait. The public call returned CancelledError,
lost the prefix, and left the account attempt unresolved without saving the known
wait. The caller had zero cancellation requests.

A separate probe produced the same outcome after a successful read. That matters:
the cause is not a peculiar FloodWait handler. The enclosing task contains more work
than the source operation, so its terminal state is an unreliable source-result proxy.
See the [original reproductions](evidence/sensemaking-reproductions.txt) and
[success/control counterchecks](evidence/sensemaking-boundaries.txt).

The corrected contract must keep the original source success, error and complete
prefix authoritative on every terminal path. It must still preserve real caller
cancellation and wait for owned source work to stop. Cancellation from another role
cannot be identified merely by the exception's type.

### 3. Waiting for cleanup is safe only when the wait dependencies are valid

The second rejection has this dependency chain:

```text
read waits for health callback
health callback waits for close
close waits for read
```

The existing guard rejects close from the exact reader/source task. It misses a
callback-created task that calls close. A new inquiry probe found the same cycle
inside an asynchronous storage adapter, before any Telegram source work began.

Tracking the live operation through task context improves detectable reentry. A
prototype passed the direct/descendant cases and legitimate external-close controls.
It still failed when the callback awaited an actor task created before the operation.
That actor had no inherited context but closed the same pool. The real wait cycle
remained. The [candidate evidence](evidence/innovation-probe.txt) records this limit.

This is why another broad “ownership helper” is not yet the answer. Task ancestry
cannot reveal every dependency an arbitrary application program can construct.
Retained cleanup is still required, but it cannot make a circular wait valid.

### 4. The missing foundation is an explicit operation contract

The next design should distinguish these facts without requiring a public framework:

| Fact | What establishes it | What it must not be confused with |
|---|---|---|
| Source outcome | The actual read or identity check returns/raises | Later observer success, failure or cancellation |
| Caller stop | Cancellation directed at the owning caller | A callback's cancelled future or SDK cleanup cancellation |
| Permitted control | Independent external control, with detectable reentry refused | A different task object automatically being an independent controller |
| Physical completion | Owned source work and the actual disconnect attempt have settled | A timeout, cancelled waiter or expired stored token |
| Permission for a new attempt | Exact durable account-state transition plus existing eligibility/allowance | A health report, cleared local task reference or elapsed timeout |
| Accepted group progress | The existing receiver acknowledgment contract | Account recovery or successful event delivery |

A small private representation may help carry these facts. Their semantics matter
more than whether they are implemented with an object, a context manager or existing
holders. The inquiry does not establish a need for a shared supervisor across tgdata.

Custom storage adapters also need a role boundary: they may await their storage I/O,
but must not call or await the same pool's lifecycle while serving its operation,
directly or through another task. Detectable reentry should refuse before mutation.
The library must not claim to detect arbitrary external wait graphs.

### 5. The simplest useful reporting boundary is passive data

For this pool, capture plain health observations internally. Do not execute or await
an application's arbitrary health callback within source work or retirement. The
application retrieves the data and decides how to log, display or react to it.

Use finite in-memory retention with explicit event-count and payload-size limits.
When an incoming event exceeds a limit, drop it and expose a loss indication. Do not
block source work, retry event delivery or introduce durable telemetry storage.
A failed report capture must remain secondary to the actual source outcome.

A local synchronous drain can return independent values plus the loss count and
clear the retained data. It must work in idle, active, closing and closed states.
It performs no I/O, invokes no application code and grants no permission to read.
It returns what has been captured so far; later observations appear in a later drain.

The inquiry tested an initially proposed busy-refusal rule and rejected it. During
external close, a reader's cleanup retrieved reports while close was still active.
A hypothetical busy accessor replaced CancelledError with PoolBusyError. A plain
local accessor preserved cancellation, returned reports and let all clients retire.
The [two-case comparison](evidence/passive-retrieval.txt) uses unchanged actual pool
source/close code, with only the proposed accessor supplied by the inquiry.

Health reports remain diagnostic. Overflow or process death may lose them. Losing a
report must not erase a saved wait, refund allowance or advance group progress.
Likewise, observing a source wait does not prove that a subsequent state write committed.

This approach changes the unmerged AccountPool callback API deliberately. It does
not silently change ordinary TgData callbacks. Exact method names, finite constants
and byte representation belong in the next plan and its implementation tests.

### 6. What to retain and what to rework

| Retain | Rework before further pool implementation |
|---|---|
| Deterministic drain/spread selection | Source-result precedence across every terminal path |
| Numeric identity and budget admission | Distinction between real caller stop and subordinate cancellation |
| Durable attempt admission and saved restrictions | Permitted control dependencies and detectable reentry guards |
| Conservative restart recovery | Pool reporting as passive data with explicit access/loss semantics |
| Existing ReadBudget accounting | Full composition tests around that boundary |
| Daily/backfill publication, replay and acknowledgment | Explicit callback migration and provider documentation |
| Retained disconnect, failed-retirement quarantine and retry | Current-dev integration review after the contract is settled |

The evidence supports retaining these responsibilities and their tested mechanisms.
It does not certify every existing line or replace the full future regression suite.
In particular, #10 has since merged into dev and needs normal integration review.

The prerequisite work is therefore a narrow ownership/reporting contract followed
by a real-component proof of that contract. More selection strategies, a general
lifecycle framework, a new progress store or rebuilding the whole pool would not
address the measured causes first.

## Inherited Commitments Re-test

The sources below are the original account-pool finding, original plan/critic,
retirement plan/critic and rejected PR critique named in this inquiry's framing.

| Commitment / source | Re-test status | Evidence or reason |
|---|---|---|
| Fresh numeric identity before reads/budget; original finding §1 and plan source boundary | RE-TESTED — commitment confirmed | Original PR probes re-run; changed identity retains first prefix and never reads under the mismatched second identity. [Log](evidence/sensemaking-reproductions.txt). |
| Durable permission before source and exact settlement; original finding §2 / original critique | RE-TESTED — commitment confirmed | Admission cancellation before/after commit starts no source; lost settlement reply preserves committed wait. Same log. |
| Preserve source prefixes despite reporting; original plan Step2 / original critic Risk1 | RE-TESTED — commitment confirmed but frame revised | The guarantee must cover every termination path, not only observer timeout. Original and success probes disprove the current implementation's completeness. |
| Await source completion and retain cleanup; retirement plan Step2 / retirement critic | RE-TESTED — commitment confirmed but frame revised | Repeated-cancellation controls preserve cleanup; descendant/outside-actor cycles show valid control dependencies are also required. [Prototype controls](evidence/innovation-probe.txt). |
| Exact-task close guard is sufficient; current product behind PR review | RE-TESTED — commitment found INVALID | Callback descendant and storage descendant bypass it; pre-existing actor defeats ancestry-only replacement. [Counterchecks](evidence/sensemaking-boundaries.txt), prototype controls. |
| Quota and group receipts remain independent; original finding §4 | RE-TESTED — commitment confirmed | Six raw/daily/backfill histories retain prefix100/wait7200/charge200; four progress cases replay/ack after close without source. [Log](evidence/critique-observations.txt). |
| Failed-retirement quarantine and explicit retry; retirement plan Step2 | INHERITED-WITHOUT-RE-TEST in full | The current block-before-disconnect/clear-after-success code and previous qualification were inspected. This inquiry exercised cancellation/retirement but did not repeat every failed-disconnect/retry injection. Preserve this policy and require its regression before merge. |
| Two Medium PR defects are real; rejected PR critique | RE-TESTED — commitment confirmed | Both re-run on the exact original branch subject, with additional success/provider controls. |
| SDK1.45.0 policy, duplicate-credential preflight and complete recovery/initialization surface; original plan | INHERITED-WITHOUT-RE-TEST in full | Relevant SDK/state paths were exercised, but this inquiry did not rerun the entire smoke suite or every configuration/recovery case. No runtime changes are proposed to these contracts. Future regression remains required. |
| Real accounts may have different history; original finding / PR qualification limit | INHERITED-WITHOUT-RE-TEST | No two-account live resources used. The recommendation makes no equal-visibility or live-readiness claim. |

## Next Actions

### MUST

- **What:** Re-plan the existing pool around the explicit operation and observation
  contract before implementing more pool changes. **Who:** the next #17 task-impl
  revision, including description/plan and fresh critique. **Gate:** use this saved
  finding as input before changing runtime code. **Why:** make source, observer,
  cancellation and control semantics reviewable before another implementation cycle.
- **What:** Prove the revised operation boundary with actual source, store and
  progress components before accepting its implementation. **Who:** the next #17
  prebuild and regression work. **Gate:** the combined candidate must cover successful
  and partial reads, real versus subordinate cancellation, repeated cancellation,
  storage reentry, descendant/outside control, normal external close, failed cleanup,
  report loss and local access during close. **Why:** catch false ownership assumptions
  before integrating the revised boundary into the pool.
- **What:** Retain current-dev integration, full offline suites and a fresh PR critique.
  **Who:** the #17 implementation/review run. **Gate:** after the accepted revised
  plan is implemented. **Why:** this inquiry has not made PR #26 mergeable.
- **What:** Qualify failover using two approved existing accounts and a shared group.
  **Who:** maintainer supplies resources; authorized live-gate runner executes it.
  **Gate:** revised offline verification passes and account/group/shared-budget
  resources are confirmed. **Why:** establish actual identity/proxy/history behavior.

### COULD

- **What:** Extend ranking beyond drain/spread. **Who:** later pool work.
  **Gate:** real workload evidence shows unfairness. **Why:** improve utilization.
  **Depends-on:** MUST implementation/verification. GATED until that passes; this
  remains the prior optional improvement, not an answer to the present defects.

### DEFERRED

- **What:** Extract a shared lifecycle helper. **Gate:** a second consumer demonstrates
  the same completion and failure policy. **Why if revived:** remove proven duplication.
- **What:** Introduce durable telemetry/subscribers. **Gate:** an actual consumer needs
  lossless event delivery. **Why if revived:** that new guarantee needs its own design.
- **What:** Add automatic joining or distributed ownership. **Gate:** explicit user
  selection of that expanded pool scope. **Why if revived:** serve different access
  or deployment requirements; #7's availability alone does not expand this task.

## Reasoning

The preferred design survived because it removes a demonstrated dependency: source
work no longer waits for arbitrary application reactions. It keeps physical cleanup
and durable uncertainty explicit, so simplification does not discard the safeguards
that already work. A report buffer adds bounded data, not another executable lifetime.

The significant rejected alternatives and their lessons are:

| Alternative considered | Decision and reason |
|---|---|
| Catch another callback exception and retain arbitrary awaited callbacks | Rejected as a sufficient design. Cancellation provenance and indirect close dependencies remain; patches need the wider contract. |
| Context/lineage guard alone | Rejected for unrestricted callbacks. A pre-existing actor bypasses it and reproduces the cycle. Retain it only as a bounded guard. |
| Global task/lifecycle supervisor | Not required here. It still needs authority over external dependencies and adds policies beyond this serial pool. |
| Universal source-result envelope | Rejected as the focused remedy; it changes raw/progress error APIs unnecessarily. It remains coherent for a separately chosen application protocol. |
| One journal for quota, account permission, progress and reports | Rejected. These facts have different ownership and recovery obligations; source-free replay must not depend on live account work. |
| Remove persisted account attempts | Rejected. Restart would forget uncertain permission and potentially lost waits. |
| Temporary clients for every attempt | Coherent alternative, but does not remove observer/control cycles and changes the chosen persistent-client policy. |
| Refuse every close while busy | Coherent alternative only with an explicit caller-stop-then-await contract; it gives up currently valid outside-close behavior. |
| Busy-sensitive or await-until-idle report access | Rejected. Refusal can mask the original cancellation; waiting can recreate the close/read cycle. |
| Latest-operation-only report snapshot | Coherent alternative with explicit overwrite/loss semantics. A drain is preferred because it need not attach data to every source/progress return or error. |
| Remove health reporting entirely | Survives as a smaller product choice; loses transient diagnostics. Passive data preserves useful reporting with no observer lifetime. |
| Exhaustive tests of arbitrary callbacks | Rejected as a proof claim. First bound permitted roles, then use adversarial phase/role tests. |
| Live-only validation | Rejected as a substitute. Successful real reads do not exercise cancelled callback futures or local task dependency cycles. |

The first inquiry iteration exposed the ancestry-only counterexample and completed
the causal diagnosis. The second specified useful reporting and found an unnecessary
busy predicate. The third tested and removed that predicate. The final two passes
stayed within the same design region; no broader rewrite or new prerequisite system
emerged. All seven traverse disciplines ran, with repeated full mechanism coverage.

## Open Questions

### Monitoring

The next plan must choose the exact public retrieval shape, finite limits and safe
plain-data encoding, then verify overflow/oversize/capture-failure behavior. These
are implementation choices within the settled role boundary.

### Blocked

Two-account live qualification remains pending. The completed local experiments do
not establish real account availability, proxies or equal history visibility.

### Refinement Triggers

Revisit passive lossy reporting if a named consumer requires guaranteed durable event
delivery. Revisit provider/control restrictions if a required adapter cannot finish
without coordinating the same pool's shutdown. Revisit shared lifecycle extraction
when another concrete owner needs the same policy, rather than merely similar names.

## Evidence and scope

Subject: #17 branch `71502e5993315354ca3d97afe607d5f4be776af3`, runtime product
`485446419122a13f871bd07fb145bbf072465543`. Current-dev comparison:
`2ddb852d917998d003f9db863fce09a92e9c5712` (includes merged #10).
Python3.11.10, Telethon1.45.0, SQLite3.45.3 on this host. Probes used actual SDK/
SQLite paths with synthetic replies and blocked sockets. Concept experiments changed
only inquiry-owned in-memory seams. No live account/config/budget was used or reset.

The [evidence folder](evidence/) preserves scripts, outputs and runtime source hashes.
The [final critique](docarchive/critique.md) records the full disposition; earlier
iterations are in [the archive](docarchive/). The [route map](routelister.md) preserves
fourteen concept directions. All runtime/product files remain unchanged by this inquiry.

## Source Input

<details>
<summary>Raw user input</summary>

```text
|  |  |  |
|---|---|---|
| #17 | Automatic account routing and failover | Draft PR #26 rejected with two Medium findings. Needs revision-3 re-planning; two-account live testing remains pending. |\
\
usually after revision 3 it measn sth fundementally was wrong or not well established, so maybe lets run full traverse with that focus and understand what missing abstraction or concept was cause of 3 revisions , or would make things a lot easier to implement etc
```

</details>
