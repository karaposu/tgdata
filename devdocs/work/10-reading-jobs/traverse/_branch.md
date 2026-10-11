# Branch: #10 worker contract

## Source Input

```text
What should #10's small worker that holds configured accounts, accepts read/lookup/access/join jobs and emits raw batches/health events promise about job admission, account ownership, reply loss and shutdown, while orchestration and processing stay with the caller?
```

Original user/issue input: `../source-input.md`. This issue-local inquiry path
follows CONTRIBUTING §5 rather than the generic timestamped inquiry directory.

## Articulation Reference

File: `articulate_simple.md`; Itemize count1; identifierW1; verdictHIGH-PROCEED;
flagged structural conditions:none. All sections below derive from its W1 bundle.

## Question

Literal (MultiDepth): What should #10's small worker that holds configured accounts,
accepts read/lookup/access/join jobs and emits raw batches/health events promise
about job admission, account ownership, reply loss and shutdown, while orchestration
and processing stay with the caller?

MQ1 preserves two possible answers: an externally observable process/job contract
versus a first-delivery deployment shape; library/caller responsibility decisions
versus concrete transport selection.

MQ3 preserves endpoint choices: bounded request/reply versus durable acceptance and
later retrieval; caller-selected account versus automatic selection; sequential
execution versus account-scoped concurrency; external reassignment/login versus
worker-managed relocation. The issue keeps orchestration/processing external and
distinguishes many accounts from many sessions of one account.

## Goal

From Deconstruct: actionable worker-boundary decision; externally visible rules,
account/job ownership, failure semantics and empirical premises; bounded to the
four requested job types, accounts/proxies/sessions/budgets, batch/health outputs
and laptop/server use on current dev.

WHY alternatives (MultiDepth): consumer simplicity/reuse versus operational
isolation/restartability; identical laptop/server behavior versus centralized
service convenience; predictable failure meaning versus maximal throughput.

Context required (MQ2): verdict—reusable current-dev ownership/cleanup guarantees
versus missing process guarantees; kinds—job envelopes, account configuration,
result/error/health serialization, budgets, OS pipe/termination behavior and
consumer expectations; stance—caller subprocess versus network service versus
durable runner. The pending preference question and stated stdin/stdout working
default are inputs, not proof of a user-selected protocol.

Boundaries (MQ4): do not change ordinary connection-pool semantics, take over
orchestration/processing, rely on unmerged/rejected #17, or infer live activity,
merge or deployment permission. Replay/durable acceptance, queueing, network
authentication and automatic account assignment remain responsibility choices.

## Considered Articulations

W1 variants copied from Rephrase:

1. V1: define a small caller-managed subprocess with a bounded sequential stream
   of explicit-account jobs and replies; make uncertain reply receipt a caller
   responsibility while preserving the existing library outcomes.
2. V2: define a network-addressable worker with explicit-account jobs and bounded
   execution, including the authentication and shutdown duties a service adds;
   keep scheduling/processing external.
3. V3: define a worker that durably accepts jobs and exposes later outcomes/retries;
   decide exactly which acceptance/replay duties remain in the orchestrating caller
   before adding any worker queue or automatic selection.

MQA reconciles overlapping process-contract axes without selecting a variant.

## Scope Check

Question covers goal. IN: process, account/job ownership, all four job types,
batch/error/health outcomes and failure meaning. OUT: changing ordinary session
pooling; application orchestration/processing; #17 dependency; unauthorized live
work/merge/deployment. Pending replay/queue/transport/selection choices remain open,
not silently added to that OUT list. Address the broader process/source boundary;
#17's two reproduced failures are relevant examples, not this inquiry's entire task.

No cognitive-protocol redefinition or synthesis of multiple prior inquiry outputs
is requested; Layer Commitment and Synthesis Trigger do not apply. Existing library
contracts and prior failure evidence are source inputs rather than a rolled-up spec.

## Articulation-preservation check

W1 appears in Question and Considered Articulations; MQ1/3 in Question; MQ2/4 and
WHY alternatives in Goal/Scope; all three Rephrase variants retained. Exclusions
stay distinct from undecided boundaries. Five of five derivation checks pass.
