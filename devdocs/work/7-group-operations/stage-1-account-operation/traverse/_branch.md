# Branch: Stage 1 account operation

## Source Input

Implement only Stage 1: declare an expected numeric Telegram account ID independent
of filenames/cache; construct a temporary client with proxy/device/session settings
preserved and waits/retries configured before authentication; verify its actual
authenticated identity without requesting login codes; pass the verified identity
into the operation and require later admission checks to agree; close reliably,
preserving the original result/failure and cancellation. Expected B/cached A/actual B
must proceed as B. Expected A/actual B must refuse before group requests or joins.


## Articulation Reference

File: articulate_simple.md. Itemize count: 1; identifier I1; HIGH-PROCEED; no flags.

## Question

Implement only Stage 1: declare an expected numeric Telegram account ID independent
of filenames/cache; construct a temporary client with proxy/device/session settings
preserved and waits/retries configured before authentication; verify its actual
authenticated identity without requesting login codes; pass the verified identity
into the operation and require later admission checks to agree; close reliably,
preserving the original result/failure and cancellation. Expected B/cached A/actual B
must proceed as B. Expected A/actual B must refuse before group requests or joins.


- **MQ1 — What is being asked?** Identified ambiguities: an internal reusable
  operation boundary versus a new public facade for third-party operations;
  proving initial ownership versus policing every subsequent arbitrary SDK call.
- **MQ2 — What context does the response need?** Identified ambiguities:
  **verdict** — whether the SDK's real authentication and disconnect composition
  supports the proposed guarantees; **kinds** — factory policy, fresh self lookup,
  read-budget admission and session persistence behavior; **stance** — a narrowly
  scoped library foundation versus a general-purpose client supervision framework.
- **MQ3 — What endpoint is intended?** Identified ambiguities: a verified handle
  consumed by later tgdata operations versus a caller-controlled raw-client context;
  cleanup completion versus bounded cleanup latency when the SDK cannot finish.
- **MQ4 — What is excluded?** Identified ambiguities: none within the exclusions;
  the explicit NOT-list is health ownership redesign (Stage 2), lookup/access
  (Stage 3), join allowance (Stage 4), joining (Stage 5), routing, another database,
  login UX and live account tests in this run.

**MQA — reconcile.** MQ1's API surface and MQ3's handle/raw-client endpoints form
one surface/lifetime axis. MQ2's narrow/framework stance controls how far that axis
may extend, without selecting an answer. Cleanup completion/latency is a separate
axis; it must not be hidden inside the ownership choice. No WHY claim is made here.


## Goal

Tuple: (deliverable: implemented, tested Stage 1; kinds: code, offline composition
tests, API/lifetime documentation and workflow evidence; bounds: single-operation
ownership, constructor policy, explicit auth failures and cleanup, based on dev).
No late split: all artifacts support this one lifecycle contract.

### MultiDepth

Literal statement: Implement only Stage 1's expected-account declaration, configured
temporary client, authentication proof, admission agreement and reliable cleanup.

Identified purpose/motivation ambiguities (WHY): making subsequent #7 features
small and trustworthy; preventing requests being attributed to the wrong account;
avoiding another growing patch series. These motivations can coexist, but their
relative priority could affect how much machinery is justified.


MQ2 and MQ4 above are preserved as context/exclusion inputs to this goal.

## Considered Articulations

1. Implement an internal operation context with a verified numeric owner, fresh
   admission agreement, and completed cleanup; later tgdata stages consume it.
2. Implement a public context exposing the SDK client and verified owner, with
   documented caller obligations and explicit lifecycle closure.
3. Implement a per-request supervisor proving ownership for every SDK dispatch,
   with bounded shutdown and a wider lifetime contract, while leaving health,
   group operations, joining, routing and persistence schemas out.

All three preserve the requested implementation shape and exclusions. They span
surface, proof scope and cleanup tradeoffs; none is selected by articulation.


## Scope Check

Question covers goal. Address the ownership/lifecycle pattern illustrated by both
acceptance examples, not just two hardcoded IDs. IN: the Deconstruct bounds above.
OUT: the full MQ4 NOT-list above. This is an ordinary software boundary inquiry,
not a cognitive protocol rewrite or synthesis of prior inquiry outputs.
