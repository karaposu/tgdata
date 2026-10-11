---
model: gpt-6-astra
effort: max
---
# Articulation — #10 worker contract

## User Input

```text
What should #10's small worker that holds configured accounts, accepts read/lookup/access/join jobs and emits raw batches/health events promise about job admission, account ownership, reply loss and shutdown, while orchestration and processing stay with the caller?
```

This is the triage's question derived from the user-authorized #10 request;
the literal user message and original issue body are preserved in `../source-input.md`.
Save output in this issue's `traverse/` folder under CONTRIBUTING §5.

## Itemize

Count: 1. Item W1: the worker's contract across source, process and caller boundaries.
Keep together: these clauses constrain one delivered process boundary; splitting
them into independent jobs would conceal their shared ownership/reply semantics.
Warm substrate: current dev's owned account/group operations, batch/health/budget
contracts, the issue's caller-orchestration boundary and the prior #17 review.

## W1 — Meta-questions and alignment

**MQ1 — What kind of answer is requested?** Identified-ambiguities-list:
an externally observable process/job contract versus a first-delivery deployment
shape; deciding library/caller responsibilities versus choosing concrete transport.

**MQ2 — What context does that answer require?** Identified-ambiguities-list:
verdict: reusable current-dev ownership/cleanup guarantees versus missing process
guarantees; kinds: job envelopes, account configuration, live result/error/health
serialization, budgets, OS pipe/termination behavior and consuming-app expectations;
stance: small caller-managed subprocess versus network service versus durable
job runner. The transport preference question remains unanswered; a stated working
default is context, not an identified user selection.

**MQ3 — What action endpoint is intended?** Identified-ambiguities-list:
bounded request/response jobs through a persistent process versus job acceptance
with later durable retrieval; caller-selected account versus automatic selection;
sequential job execution versus account-scoped concurrency; account reassignment
as external configuration/login versus worker-managed relocation. The issue keeps
orchestration/processing external and distinguishes many accounts from many sessions
of one account, which constrains all candidate endpoints.

**MQ4 — What boundaries are explicit or still ambiguous?** Identified-ambiguities-list:
explicit exclusions inherited from the request/session are changing ordinary
connection-pool semantics, moving orchestration/processing into tgdata, relying on
unmerged/rejected #17, and treating this task as permission for live account activity
or merging/deploying. The exact boundary of replay/durable acceptance, queueing,
transport authentication and automatic account assignment remains to be decided.

**MQA — reconcile:** MQ1's deployment shape, MQ2's stance and MQ3's endpoint share
the process-contract axis. Preserve all three readings rather than choosing a
transport from their overlap. MQ4 separates explicit exclusions from still-open
responsibility boundaries; do not turn a possible non-goal into a user instruction.

## W1 — Deconstruct and MultiDepth

**Deconstruct:** (deliverable: an actionable worker-boundary decision;
kinds: externally visible rules, account/job ownership, failure semantics and
empirical premises; bounds: #10's four job types, accounts/proxies/sessions/budgets,
raw batches/health and laptop/server use on current dev). No late item split.

**Literal statement:** What should #10's small worker that holds configured accounts,
accepts read/lookup/access/join jobs and emits raw batches/health events promise
about job admission, account ownership, reply loss and shutdown, while orchestration
and processing stay with the caller?

**WHY-axis identified-ambiguities-list:** consumer simplicity and code reuse versus
operational isolation/restartability; identical laptop/server behavior versus
centralized service convenience; predictable failure meaning versus maximal
throughput. These are motivations, not implementation endpoints.

## W1 — Considered articulations

1. V1: define a small caller-managed subprocess with a bounded sequential stream
   of explicit-account jobs and replies; make uncertain reply receipt a caller
   responsibility while preserving the existing library outcomes.
2. V2: define a network-addressable worker with explicit-account jobs and bounded
   execution, including the authentication and shutdown duties a service adds;
   keep scheduling/processing external.
3. V3: define a worker that durably accepts jobs and exposes later outcomes/retries;
   decide exactly which acceptance/replay duties remain in the orchestrating caller
   before adding any worker queue or automatic selection.

All three retain the requested job types and account/session distinction. They span
identified transport/acceptance boundaries and motivations without selecting one.

## Self-assessment

One light pass: modes 1–9 not fired (no premature/late split, extra MQ axis, missing
operation/preparation/kinds/stance, commitment at a 2-shape position, WHAT/WHY
conflation or out-of-bounds variant). Layer2 behavior is not assessed from one run.
Bundle complete; four MQs, MQA, tuple, literal/WHY and three bounded variants.

**Verdict: HIGH-PROCEED.**
