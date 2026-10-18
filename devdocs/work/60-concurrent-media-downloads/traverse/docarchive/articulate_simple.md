# Articulation — concurrent media contract
## User Input
What ownership, ordered-completion and wait contract lets optional parallel media downloads coexist with tgdata readers, durable progress and existing SDK policy without a general scheduler?
Agent-framed inquiry for the user's `$task-impl` on issue60; original request is
../request.md. Default1/opt-in parameter and rate-aware backoff were explicitly
confirmed by the user. Same-session code context is substrate, not another request.
## Itemize
Count1; item I1: What ownership, ordered-completion and wait contract lets optional parallel media downloads coexist with tgdata readers, durable progress and existing SDK policy without a general scheduler?
Kept together: ownership/order/wait are constraints on one feature, not independent
projects. Deconstruct reveals no late split.
## I1 — MQ and alignment
MQ1 question: what kind of answer is requested?
Identified ambiguities: minimal in-reader scheduling contract versus reusable media
ownership primitive; research conclusion versus directly implementable boundary.
MQ2 question: what context must the answer prepare?
Identified ambiguities: verdict-axis requires actual SDK wait/resource behavior;
kinds-axis requires legacy rows versus validated batch/receipts; stance-axis requires
compatibility at1 versus stricter opted-in failure handling and local versus account-
wide coordination. Real live throughput versus controlled local overlap evidence.
MQ3 question: what action endpoint is intended?
Identified ambiguities: per-read overlap only, shared-engine overlap bound, or
in-process per-account bound across clients; message attachments only versus all
media surfaces; automatic retry versus honoring the existing caller's wait policy.
MQ4 question: what is excluded?
Identified ambiguities/exclusion bounds from session: no default concurrency increase,
new branch, unbounded task-per-message creation, parallel history pagination,
per-file chunk acceleration, automatic account rotation, distributed coordinator,
new durable progress schema or promised speed multiplier. No new live test authority.
MQA: reconcile scope overlaps into coordination extent and compatibility extent;
retain unknown SDK behavior and measurement evidence as separate axes. None selected.
## I1 — Deconstruct
Tuple: deliverable=feature contract; kinds=ownership/state invariants, options and
falsifiers; bounds=issue60 readers/media/progress/source-policy integration. A later
plan supplies steps; this inquiry does not implement them.
## I1 — MultiDepth
Literal statement: What ownership, ordered-completion and wait contract lets optional parallel media downloads coexist with tgdata readers, durable progress and existing SDK policy without a general scheduler?
WHY ambiguities: lower daily collection latency versus predictable account pressure
versus reusable library behavior with trustworthy saved progress.
## I1 — Considered articulations
1. Establish per-invocation media overlap with caller-managed cross-call ownership,
   keeping current reader result/wait contracts and proving ordered completion.
2. Establish bounded shared-engine download ownership, preserving independent clients
   and defining how opted-in calls queue, wait, settle and deliver prefixes.
3. Establish per-account in-process ownership across distinct configured clients,
   requiring verified identity and explicit policy for different requested limits.
4. Establish an attachments-first contract with explicit dispositions for profile,
   in-memory and selected-ID downloads; separate local overlap from live speed proof.
## Self-assessment
All nine LAYER1 modes checked: no fires. One item, four MQs (MQ2 all three subaxes),
MQA, tuple, literal/WHY and four bounded variants present; no adjudication/plan.
HIGH-PROCEED
